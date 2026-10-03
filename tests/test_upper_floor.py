import copy,json
from pathlib import Path
from shapely.geometry import Polygon
from floorforge.intent import fuse
from floorforge.upper_floor import constraints,starter,usable
from floorforge.smart_fit import smart_fit
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.model import DesignError
ROOT=Path(__file__).resolve().parents[1]
def sample():
    return json.loads((ROOT/'examples/custom/your-sketch-g1.floorforge.json').read_text(encoding='utf-8'))
def test_upper_starter_keeps_lower_floor_and_requires_explicit_application():
    p=sample();p['customPlan']['floors'][1].update(rooms=[],openings=[],walls=[])
    p['customPlan']['stairs'][0]['roomIds']=p['customPlan']['stairs'][0]['roomIds'][:1]
    before=copy.deepcopy(p);r=starter(p,1)
    assert r['valid'],r['errors']
    assert p==before
    assert r['customPlan']['floors'][0]==fuse(p)['customPlan']['floors'][0]
    assert len([r for r in r['customPlan']['floors'][1]['rooms'] if r['kind']=='stair'])==1
    assert validate(generate_layout(fuse({**p,'customPlan':r['customPlan']})))['status']=='preliminary_geometry_pass'
def test_guidance_names_unsupported_room_and_duplicate_stairs():
    p=sample();rooms=p['customPlan']['floors'][1]['rooms'];r=next(r for r in rooms if r['kind']=='bedroom');r['polygon']=[[x+8000,y] for x,y in r['polygon']]
    stair=next(r for r in rooms if r['kind']=='stair');rooms.append({**copy.deepcopy(stair),'id':'duplicate'})
    result=constraints(p,1)
    assert any(e['id']==r['id'] for e in result['issues'] if e['code']=='UPPER_FOOTPRINT')
    assert any(set(e['ids'])=={stair['id'],'duplicate'} for e in result['issues'] if e['code']=='DUPLICATE_STAIR')
    try:starter(p,1,True)
    except DesignError as error:assert error.code=='DUPLICATE_STAIR'
    else:assert False
def test_existing_upper_stair_is_aligned_without_adding_another():
    p=sample();stairs=[r for r in p['customPlan']['floors'][1]['rooms'] if r['kind']=='stair'];stairs[0]['polygon']=[[x+100,y] for x,y in stairs[0]['polygon']]
    r=starter(p,1,True)
    assert r['customPlan']['floors'][0]==fuse(p)['customPlan']['floors'][0]
    assert len([q for q in r['customPlan']['floors'][1]['rooms'] if q['kind']=='stair'])==1
def test_upper_fit_does_not_resize_or_reposition_lower_floor():
    p=sample();lower=copy.deepcopy(fuse(p)['customPlan']['floors'][0])
    room=next(r for r in p['customPlan']['floors'][1]['rooms'] if r['kind']=='bedroom')
    room['polygon']=[[x+50,y] for x,y in room['polygon']]
    r=smart_fit(p,floor=1)
    assert r['customPlan']['floors'][0]==lower
    assert r['valid'],r['errors']
    assert validate(generate_layout(fuse({**p,'customPlan':r['customPlan']})))['status']=='preliminary_geometry_pass'
def test_worked_example_has_matching_geometry_hashes_and_roof():
    p=sample();b=generate_layout(fuse(p));assert validate(b)['status']=='preliminary_geometry_pass'
    assert b['storeys']==2 and b['rooftop']
    assert len(p['editorState']['guideFloors'])==3
    assert all(len(row)==4 for board in p['editorState']['guideFloors'] for row in board)
    for name in ['building','scene','report','manifest']:
        data=json.loads((ROOT/f'examples/your-sketch/{name}.json').read_text(encoding='utf-8'))
        assert data['planHash']==b['planHash']

def test_original_and_fitted_sample_keep_bedroom_and_guest_dimensions():
    original=json.loads((ROOT/'examples/custom/your-sketch-original.floorforge.json').read_text(encoding='utf-8'))
    rooms={r['id']:r for r in sample()['customPlan']['floors'][0]['rooms']}
    for r in original['customPlan']['floors'][0]['rooms']:
        if r['kind'] in ('bedroom','drawing-room'):
            a=Polygon(r['polygon']).bounds;b=Polygon(rooms[r['id']]['polygon']).bounds
            assert (a[2]-a[0],a[3]-a[1])==(b[2]-b[0],b[3]-b[1])

def test_narrow_lower_stair_is_explained_before_building_upper_floor():
    p=sample();r=next(r for r in p['customPlan']['floors'][0]['rooms'] if r['kind']=='stair')
    x,y,x1,y1=Polygon(r['polygon']).bounds;r['polygon']=[[x,y],[x+900,y],[x+900,y+3600],[x,y+3600]]
    issue=next(e for e in constraints(p,1)['issues'] if e['code']=='STAIR_FIT')
    assert issue['floor']==0 and issue['id']==r['id'] and '2.2 × 4.1' in issue['message']

def test_missing_upper_request_is_a_structured_error():
    import pytest
    with pytest.raises(DesignError):starter({},None)
    with pytest.raises(DesignError):constraints({},None)
