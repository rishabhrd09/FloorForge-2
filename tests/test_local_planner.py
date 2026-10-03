import base64,copy,io,json
import pytest
from PIL import Image
from floorforge import local_planner as lp
from floorforge.model import DesignError
from tests.test_plan_search import crowded


def response(action='rearrange',rooms=None,questions=None):
    return dict(action=action,rooms=rooms or [],questions=questions or [],rationale='Review the requested plan.')


def install_fake(monkeypatch,proposal,capabilities=('completion','vision')):
    calls=[]
    def fake(path,payload=None,timeout=10):
        calls.append((path,payload))
        if path=='/api/tags':return {'models':[{'name':'qwen3.5:9b'}]}
        if path=='/api/show':return {'capabilities':list(capabilities)}
        return {'message':{'content':json.dumps(proposal)},'total_duration':1e9}
    monkeypatch.setattr(lp,'call',fake);return calls


def test_no_model_contact_without_consent_or_scale(monkeypatch):
    monkeypatch.setattr(lp,'call',lambda *a,**k:pytest.fail('network'))
    with pytest.raises(DesignError):lp.propose(crowded(),'Help')
    result=lp.propose(crowded(),'Help',confirm=True)
    assert result['questions'] and not result['alternatives']


def test_local_rearrangement_validated_and_input_untouched(monkeypatch):
    calls=install_fake(monkeypatch,response());p=crowded();before=copy.deepcopy(p)
    r=lp.propose(p,'Find a connected layout',confirm=True,dimensions_confirmed=True)
    assert r['valid'] and len(r['alternatives'])==3 and p==before and not r['applied']
    assert calls[-1][1]['format']==lp.SCHEMA and calls[-1][1]['stream'] is False


def test_questions_never_apply_partial_edits(monkeypatch):
    r=lp.checked_proposal(crowded(),0,[],response('clarify',questions=['Which bedroom should move?']))
    assert r['questions'] and not r['alternatives']


def test_fixed_room_cannot_be_changed():
    room=dict(id='kitchen',name='kitchen',kind='kitchen',x=100,y=100,width=2500,depth=2500)
    with pytest.raises(DesignError,match='fixed room'):lp.checked_proposal(crowded(),0,['kitchen'],response('edit',[room]))


@pytest.mark.parametrize('edit',[{'action':'execute','rooms':[],'rationale':'','questions':[]},response('edit',[dict(id='x',name='X',kind='kitchen',x=0,y=0,width=True,depth=2000)]),response('edit',[dict(id='x',name='X',kind='invalid',x=0,y=0,width=2000,depth=2000)]),response('edit',[dict(id='x',name='X',kind='kitchen',x=0,y=0,width=2000,depth=2000,command='bad')])])
def test_model_output_is_untrusted(edit):
    with pytest.raises(DesignError):lp.parse(json.dumps(edit))


def test_invalid_geometry_rejected_without_resize_or_mutation():
    p=crowded();before=copy.deepcopy(p)
    r=lp.checked_proposal(p,0,[],response('edit',[dict(id='kitchen',name='kitchen',kind='kitchen',x=150,y=150,width=90000,depth=90000)]))
    assert not r['valid'] and not r['alternatives'] and p==before and r['errors']


def test_create_programme_uses_python_search():
    p=crowded();rooms=[]
    for r in p['customPlan']['floors'][0]['rooms']:
        (x,y),(x1,_),(_,y1),_=r['polygon'];rooms.append(dict(id=r['id'],name=r['name'],kind=r['kind'],x=x,y=y,width=x1-x,depth=y1-y))
    p['customPlan']['floors'][0]['rooms']=[]
    result=lp.checked_proposal(p,0,[],response('create',rooms))
    assert result['valid'] and len(result['alternatives'])==3


def test_images_are_bounded_and_checked_for_vision(monkeypatch):
    with pytest.raises(DesignError):lp.image_data(['https://example.com/image.png'])
    with pytest.raises(DesignError):lp.image_data([base64.b64encode(b'not an image').decode()])
    data=io.BytesIO();Image.new('RGB',(16,16)).save(data,format='PNG');b64=base64.b64encode(data.getvalue()).decode()
    install_fake(monkeypatch,response(),('completion',))
    with pytest.raises(DesignError,match='cannot read images'):lp.propose(crowded(),'Read this',images=[b64],dimensions_confirmed=True,confirm=True)
    calls=install_fake(monkeypatch,response('clarify',questions=['What is the annotated dimension?']))
    r=lp.propose(crowded(),'Read this',images=[b64],dimensions_confirmed=True,confirm=True)
    assert r['questions'] and calls[-1][1]['messages'][-1]['images']==[b64]


def test_remote_ollama_models_refused(monkeypatch):
    def fake(path,payload=None,timeout=10):
        return {'models':[{'name':'local-alias'}]} if path=='/api/tags' else {'remote_host':'https://ollama.com'}
    monkeypatch.setattr(lp,'call',fake)
    with pytest.raises(DesignError,match='Remote models'):lp.propose(crowded(),'Help',model='local-alias',dimensions_confirmed=True,confirm=True)


def test_positioned_room_details_are_protected():
    p=crowded();p['customPlan']['floors'][0]['rooms'][0]['wardrobeWall']='rear'
    result=lp.checked_proposal(p,0,[],response())
    assert not result['alternatives'] and not result['valid']


def test_valid_exact_edit_keeps_requested_dimensions_and_other_rooms():
    from floorforge.intent import fuse
    p=crowded();p['customPlan']=lp.alternatives(p)['alternatives'][0]['customPlan']
    original=fuse(p)['customPlan'];room=next(r for r in original['floors'][0]['rooms'] if r['kind']=='bedroom')
    (x,y),(x1,_),(_,y1),_=room['polygon']
    # Shorten only the exterior edge, preserving precise shared wall contacts.
    target=dict(id=room['id'],name=room['name'],kind=room['kind'],x=x+150,y=y,width=x1-x-150,depth=y1-y)
    result=lp.checked_proposal(p,0,[],response('edit',[target]))
    assert result['valid'],result
    out=result['alternatives'][0]['customPlan']['floors'][0]['rooms']
    assert {r['id']:r['polygon'] for r in out if r['id']!=room['id']}=={r['id']:r['polygon'] for r in original['floors'][0]['rooms'] if r['id']!=room['id']}


def test_local_request_timeout_does_not_poison_future_requests(monkeypatch):
    def down(*a,**k):raise DesignError('LOCAL_MODEL_UNAVAILABLE','stopped')
    monkeypatch.setattr(lp,'call',down)
    with pytest.raises(DesignError):lp.propose(crowded(),'Help',dimensions_confirmed=True,confirm=True)
    install_fake(monkeypatch,response('clarify',questions=['Which room?']))
    assert lp.propose(crowded(),'Help',dimensions_confirmed=True,confirm=True)['questions']


def test_live_plan_api_is_session_protected(http_server,monkeypatch):
    from tests.test_security_ai import request
    code,raw=request(http_server,'/api/session');headers={'X-FloorForge-Token':json.loads(raw)['token']}
    body={'project':crowded()}
    assert request(http_server,'/api/plan/alternatives',body)[0]==403
    code,raw=request(http_server,'/api/plan/alternatives',body,headers)
    assert code==200 and len(json.loads(raw)['alternatives'])==3
    install_fake(monkeypatch,response('clarify',questions=['Which bedroom?']))
    body.update(instruction='Move the bedroom',dimensionsConfirmed=True,confirm=True)
    code,raw=request(http_server,'/api/local-plan/propose',body,headers)
    assert code==200 and json.loads(raw)['questions']==['Which bedroom?']
    body['confirm']=False
    assert request(http_server,'/api/local-plan/propose',body,headers)[0]==400


from tests.test_security_ai import http_server


def test_vision_json_fence_is_data_but_embedded_extra_text_is_rejected():
    value=response('clarify',questions=['Which bedroom?'])
    assert lp.parse('```json\n'+json.dumps(value)+'\n```')==value
    with pytest.raises(DesignError):lp.parse('Here is a plan: '+json.dumps(value))
    with pytest.raises(DesignError):lp.parse(json.dumps(response('edit',[dict(id='x',kind='hall',name='Hall',x=0,y=0,width=float('nan'),depth=2000)])))


def test_rearrange_never_consumes_model_room_coordinates():
    p=crowded();extra=dict(id='unrequested',name='Extra',kind='bedroom',x=0,y=0,width=90000,depth=90000)
    r=lp.checked_proposal(p,0,[],response('rearrange',[extra]))
    assert r['valid'] and 'ignored' in r['rationale']
    expected={q['id'] for q in p['customPlan']['floors'][0]['rooms']}
    for option in r['alternatives']:assert {q['id'] for q in option['customPlan']['floors'][0]['rooms']}==expected
