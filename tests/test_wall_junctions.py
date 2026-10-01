"""Wall ownership at enclosed-room / outdoor-zone junctions, including the reported guide."""
import copy
import json
from pathlib import Path
import pytest
from shapely.geometry import Polygon, LineString, box
from floorforge.custom_plan import compile_plan, wall_runs
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from floorforge.plan_tools import convert_guide, guide_check, suggest_openings
from floorforge.review import validate


def screenshot_project(storeys=1):
    rows=[['outer-lobby']*4,['kitchen','dining','living','outer-lobby'],
          ['stair-landing','bedroom-2','veranda','outer-lobby'],
          ['master-bedroom','bedroom-2','courtyard','bedroom-1']]
    return {'brief':{'width_mm':12192,'depth_mm':18288,'front_mm':5500,'rear_mm':1200,
                     'left_mm':500,'right_mm':3000,'road_bearing_deg':90,'bedrooms':3,'storeys':storeys,'parking':True,'roof_access':False},
            'grid':{'mode':'spatial_hint','rows':4,'cols':4,'floorIds':['g','f','s'][:storeys],
                    'floors':[rows]+[[['']*4 for _ in range(4)] for _ in range(storeys-1)]}}


def adjoining_outdoors(junction=3150, offset=0):
    def room(id,kind,rect):return {'id':id,'name':id.title(),'kind':kind,'polygon':[list(c) for c in list(box(*rect).exterior.coords)[:-1]]}
    return {'brief':{'width_mm':9000,'depth_mm':10000,'front_mm':500,'rear_mm':500,'left_mm':500,'right_mm':500,
                     'storeys':1,'bedrooms':1,'parking':False,'pooja':False,'roof_access':False},
            'customPlan':{'schema':'floorforge.custom-plan/1','units':'mm','wallThickness':150,'stairs':[],
                'floors':[{'id':'ground','walls':[], 'rooms':[
                    room('living','living',(150,150,4150,6150)),
                    room('veranda','veranda',(4225+offset,75,6500,junction)),
                    room('courtyard','courtyard',(4225+offset,junction,6500,6225))],
                    'openings':[
                        {'id':'entrance','roomId':'living','side':'front','kind':'entry','offset':500,'width':1000},
                        {'id':'veranda-door','roomId':'living','side':'right','kind':'door','offset':500,'width':900},
                        {'id':'courtyard-window','roomId':'living','side':'right','kind':'window','offset':junction+100,'width':1700,'height':1500,'sill':750}]}]}}


def test_reported_cells_compile_with_individual_outdoor_connections():
    original=screenshot_project();plan=convert_guide(original)['customPlan']
    project={'brief':original['brief'],'customPlan':plan};before=copy.deepcopy(plan)
    b=compile_plan(fuse(project));assert plan==before
    assert {s['id']:s['clear'] for s in b['spaces']}=={r['id']:r['polygon'] for r in plan['floors'][0]['rooms']}
    right=[w for w in b['walls'] if 'guide-0-bedroom-2-0' in w['rooms'] and w['a'][0]==w['b'][0]==4346]
    assert [(w['a'][1],w['b'][1],w['rooms']) for w in right]==[
        (5794,8654,['guide-0-bedroom-2-0','guide-0-veranda-0']),
        (8654,11513,['guide-0-bedroom-2-0','guide-0-courtyard-0'])]
    assert all(len(w['rooms'])<=2 for w in b['walls'])
    proposed=suggest_openings(fuse(project))
    assert proposed['added']>0
    assert proposed['customPlan']['floors'][0]['rooms']==before['floors'][0]['rooms']
    compile_plan(fuse({**project,'customPlan':proposed['customPlan']}))
    # Fixing topology must not disable real room-size/access checks.
    with pytest.raises(DesignError) as err:validate(b)
    assert {'ROOM_MINIMUM','NO_ENTRY','UNREACHABLE'} <= {e['code'] for e in err.value.details['errors']}


def test_reported_g2_guide_and_custom_errors_are_separate_and_floor_specific():
    p=screenshot_project(3);issues=guide_check(fuse(p))['rooms']
    assert len(issues)==5
    assert {e['label'] for e in issues if e['floor']==0}=={'courtyard','outer-lobby','stair-landing'}
    assert {e['floor'] for e in issues if e['label']=='bedrooms'}=={1,2}
    p={'brief':p['brief'],'customPlan':convert_guide(p)['customPlan']}
    with pytest.raises(DesignError) as err:compile_plan(fuse(p))
    errors=err.value.details['errors']
    assert [(e['code'],e['floor']) for e in errors]==[('EMPTY_FLOOR',1),('EMPTY_FLOOR',2)]
    assert all('Stairs to roof' in e['message'] for e in errors)


@pytest.mark.parametrize('junction',[2400,3150,3900])
@pytest.mark.parametrize('offset',[0,75])
def test_doors_windows_and_access_follow_the_correct_side_of_a_junction(junction,offset):
    p=adjoining_outdoors(junction,offset);b=generate_layout(fuse(p));review=validate(b)
    by_id={o['id']:o for o in b['openings']}
    assert by_id['veranda-door']['connects']==['living','veranda']
    assert by_id['courtyard-window']['connects']==['courtyard','living']
    assert by_id['veranda-door']['wall_id']!=by_id['courtyard-window']['wall_id']
    assert 'veranda' in review['graph']['living'] and 'courtyard' in review['graph']['veranda']
    assert next(s for s in b['spaces'] if s['id']=='living')['area_m2']==24
    assert compile_plan(fuse(json.loads(json.dumps(p))))['walls']==b['walls']


def test_corner_touch_and_collinear_vertices_do_not_create_false_opening_hosts():
    line=LineString([(0,0),(0,4000)])
    corner=box(0,4000,2000,6000)
    assert list(wall_runs(line,{'corner':corner},75))==[((0,0),(0,4000),[])]
    outdoor=Polygon([(0,0),(2000,0),(2000,4000),(0,4000),(0,2000)])
    assert list(wall_runs(line,{'deck':outdoor},75))==[((0,0),(0,4000),['deck'])]


def test_opening_cannot_straddle_two_distinct_outdoor_spaces():
    p=adjoining_outdoors();p['customPlan']['floors'][0]['openings'][1]['offset']=2700
    with pytest.raises(DesignError) as err:compile_plan(fuse(p))
    issue=err.value.details['errors'][0]
    assert issue['code']=='OPENING_HOST' and issue['id']=='veranda-door'


def test_junction_reaches_drawings_scene_and_exports(tmp_path):
    from floorforge.pipeline import run
    p=adjoining_outdoors();result=run(p,tmp_path,use_cache=False);folder=Path(result['path']);h=fuse(p)['planHash']
    b=json.loads((folder/'building.json').read_text());scene=json.loads((folder/'scene.json').read_text())
    assert scene['planHash']==b['planHash']==h
    assert {s['id']:s['clear'] for s in b['spaces']}=={r['id']:r['polygon'] for r in p['customPlan']['floors'][0]['rooms']}
    for name in ['veranda-door','courtyard-window']:
        assert any(n.get('owner')==name for n in scene['nodes'])
    assert h in (folder/'model.ifc').read_text()
    assert h in (folder/'floorplans.dxf').read_text()
    assert all(h in f.read_text() for f in (folder/'sheets').glob('*.svg'))
