"""User-facing regressions: boundary repair, semantic room types and guide hand-off."""
import copy
import pytest
from shapely.geometry import Polygon
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from floorforge.review import validate, reports
from floorforge.scene import make_scene
from floorforge.spaces import SPACE_REGISTRY
from floorforge.plan_tools import convert_guide, guide_check, suggest_openings


def guide(rows, storeys=1, bedrooms=1):
    return {'brief':{'storeys':storeys,'bedrooms':bedrooms,'width_mm':10000,'depth_mm':12000,'left_mm':1000,'right_mm':1000,'front_mm':1000,'rear_mm':1000,'parking':False,'pooja':False},'grid':{'mode':'spatial_hint','rows':4,'cols':4,'floorIds':[f'floor-{i}' for i in range(storeys)],'floors':rows}}


def test_guest_drawing_room_and_drying_room_are_distinct():
    assert not SPACE_REGISTRY['drawing-room']['wet']
    assert SPACE_REGISTRY['drying-room']['wet']
    for name,kind in [('drawing room','drawing-room'),('drying room','drying-room')]:
        assert fuse({'text':name+' at front left'})['placement_hints'][0]['label']==kind


def test_screenshot_guide_explains_unsupported_roles_and_empty_floor_only():
    rows=[[['']*4 for _ in range(4)] for _ in range(3)]
    rows[0][3]=['master-bedroom','courtyard','bedroom-1','bedroom-1']
    rows[0][0]=['outer-lobby']*4
    rows[0][1][0]='kitchen'
    p=guide(rows,3,3);check=guide_check(fuse(p))
    assert not check['valid']
    assert {i['label'] for i in check['rooms']}=={'bedrooms','courtyard','outer-lobby'}
    missing=next(i for i in check['rooms'] if i['label']=='bedrooms')
    assert missing['floor']==2 and missing['actual']==0 and missing['cells']==[]
    assert next(i for i in check['rooms'] if i['label']=='courtyard')['cells']==[[1,3]]
    with pytest.raises(DesignError) as err:generate_layout(fuse(p))
    assert err.value.code=='GUIDE_CONFLICT'
    assert not any(i['label']=='kitchen' for i in err.value.details['rooms'])


def test_cells_to_rooms_to_openings_to_valid_furnished_scene():
    rows=[['hall','hall','drawing-room','drawing-room']]*2+[['kitchen','kitchen','bedroom-1','bedroom-1']]*2
    original=guide([rows]);converted=convert_guide(original)
    project={'brief':original['brief'],'customPlan':converted['customPlan']}
    original_plan=copy.deepcopy(project['customPlan']);proposal=suggest_openings(fuse(project))
    assert proposal['added']>=7
    assert original_plan==project['customPlan']  # suggestions are a proposal, never a hidden mutation
    project['customPlan']=proposal['customPlan'];intent=fuse(project);b=generate_layout(intent);review=validate(b)
    assert review['status']=='preliminary_geometry_pass'
    assert [r['polygon'] for r in original_plan['floors'][0]['rooms']]==[r['polygon'] for r in proposal['customPlan']['floors'][0]['rooms']]
    assert suggest_openings(intent)['added']==0
    scene=make_scene(b,reports(b,review));drawing=next(s for s in b['spaces'] if s['kind']=='drawing-room')
    assert any(f['kind']=='sofa' and f['room_id']==drawing['id'] for f in scene['furniture'])
    assert not any(s['id']==drawing['id'] for s in b['spaces'] if s['wet'])
    assert scene['planHash']==intent['planHash']


def test_all_boundary_issues_have_names_distances_and_dimension_preserving_repairs():
    rows=[['hall','hall','drawing-room','drawing-room']]*2+[['kitchen','kitchen','bedroom-1','bedroom-1']]*2
    source=guide([rows]);p={'brief':source['brief'],'customPlan':convert_guide(source)['customPlan']}
    for r in p['customPlan']['floors'][0]['rooms']:r['polygon']=[[x+600,y+800] for x,y in r['polygon']]
    with pytest.raises(DesignError) as err:generate_layout(fuse(p))
    issues=err.value.details['errors'];assert len(issues)>=3
    for issue in issues:
        assert issue['name'] and issue['exceeds_mm'] and issue['fix']['action']=='move'
        room=next(r for r in p['customPlan']['floors'][0]['rooms'] if r['id']==issue['id']);before=Polygon(room['polygon']).area
        room['polygon']=[[x+issue['fix']['dx'],y+issue['fix']['dy']] for x,y in room['polygon']]
        assert Polygon(room['polygon']).area==before


def test_conversion_preserves_l_shaped_lobby_and_disconnected_repeated_rooms():
    rows=[['outer-lobby']*4,['kitchen','living','living','outer-lobby'],['stair-landing','living','veranda','outer-lobby'],['master-bedroom','courtyard','bedroom-1','bedroom-1']]
    p=guide([rows],1,2);result=convert_guide(p)['customPlan'];lobby=next(r for r in result['floors'][0]['rooms'] if r['kind']=='outer-lobby')
    assert len(lobby['polygon'])>4 and Polygon(lobby['polygon']).is_valid
    assert not result['stairs']  # a landing label is not a staircase
    from floorforge.custom_plan import normalize
    assert normalize(result,1)==result


def test_over_capacity_guide_is_a_structured_error_not_server_exception():
    rows=[[['']*4 for _ in range(4)]];rows[0][0][0]='kitchen'
    check=guide_check(fuse(guide(rows,1,8)))
    assert not check['valid'] and check['rooms'][0]['code']=='PROGRAMME_CAPACITY'


@pytest.mark.parametrize('floor',[0,1])
def test_quick_guide_builds_a_guest_drawing_room_on_the_painted_floor(floor):
    import json
    from floorforge.spaces import GUIDE_AUTOMATIC_KINDS
    boards=[[['']*4 for _ in range(4)] for _ in range(2)]
    boards[floor][0][3]='drawing-room'
    p={'brief':{'storeys':2,'roof_access':True},'grid':{'mode':'spatial_hint','rows':4,'cols':4,'floorIds':['ground','first'],'floors':boards}}
    intent=fuse(p)
    assert 'drawing-room' in GUIDE_AUTOMATIC_KINDS
    assert guide_check(intent)['valid']
    b=generate_layout(intent);review=validate(b);scene=make_scene(b,reports(b,review))
    guest=next(s for s in b['spaces'] if s['kind']=='drawing-room')
    assert guest['floor']==floor and guest['name']=='Drawing room' and not SPACE_REGISTRY[guest['kind']]['wet']
    assert any(s['kind']=='living' and s['id']!=guest['id'] for s in b['spaces'])
    assert all(any(f['kind']==kind and f['room_id']==guest['id'] for f in scene['furniture']) for kind in ('sofa','coffee-table'))
    assert any(o['kind']=='door' and guest['id'] in o['connects'] for o in b['openings'])
    assert any(o['kind']=='window' and guest['id'] in o['connects'] for o in b['openings'])
    assert len(b['floors'])==2 and scene['roof_level']==2
    assert scene['planHash']==b['planHash']==fuse(json.loads(json.dumps(p)))['planHash']


def test_guest_room_does_not_replace_a_requested_study():
    b=generate_layout(fuse({'text':'Drawing room at front right. Study at rear right.'}))
    validate(b)
    assert any(s['kind']=='drawing-room' and s['name']=='Drawing room' for s in b['spaces'])
    assert any(s['kind']=='study' for s in b['spaces'])


def test_guest_room_placement_conflict_is_not_silently_published():
    boards=[[['']*4 for _ in range(4)] for _ in range(2)];boards[1][3][3]='drawing-room'
    p={'grid':{'mode':'spatial_hint','rows':4,'cols':4,'floorIds':['ground','first'],'floors':boards}}
    with pytest.raises(DesignError) as err:generate_layout(fuse(p))
    assert err.value.code.startswith('PLACEMENT_')
    assert any(r['label']=='drawing-room' and r['floor']==1 for r in err.value.details['rooms'])
