"""Room-first preparation must help without replacing authored rooms or weakening validation."""
import copy,json
from pathlib import Path
import pytest
from shapely.geometry import Polygon
from floorforge.intent import fuse
from floorforge.plan_assist import prepare_plan
from floorforge.layout import generate_layout
from floorforge.review import validate


def rough():
    rooms=[]
    for id,kind,x,y in [('living','living',150,150),('drawing','drawing-room',4150,150),('kitchen','kitchen',150,4150),('bed','bedroom',4150,4150)]:
        rooms.append({'id':id,'kind':kind,'name':kind.title(),'polygon':[[x,y],[x+4000,y],[x+4000,y+4000],[x,y+4000]]})
    return {'brief':{'storeys':1,'bedrooms':1,'width_mm':10000,'depth_mm':12000,'left_mm':500,'right_mm':500,'front_mm':1000,'rear_mm':1000,'roof_access':False},'customPlan':{'schema':'floorforge.custom-plan/1','units':'mm','wallThickness':150,'floors':[{'id':'floor-0','rooms':rooms,'walls':[],'openings':[]}],'stairs':[]}}


def test_touching_rough_rooms_prepare_into_a_valid_home_without_resizing():
    p=rough();before=copy.deepcopy(p);r=prepare_plan(p)
    assert p==before and r['valid'] and not r['errors']
    original={q['id']:q for q in p['customPlan']['floors'][0]['rooms']}
    for room in r['customPlan']['floors'][0]['rooms']:
        assert room['id'] in original
        old=Polygon(original[room['id']]['polygon']);new=Polygon(room['polygon'])
        assert new.area==old.area and new.bounds[2]-new.bounds[0]==4000 and new.bounds[3]-new.bounds[1]==4000
        assert new.centroid.distance(old.centroid)<=355
    assert any(c['kind']=='wall-spacing' for c in r['changes'])
    assert any(c['kind']=='openings' for c in r['changes'])
    p['customPlan']=r['customPlan'];intent=fuse(p);assert intent['planHash']==r['planHash']
    assert validate(generate_layout(intent))['status']=='preliminary_geometry_pass'
    again=prepare_plan(json.loads(json.dumps(p)))
    assert again['valid'] and again['changes']==[] and again['planHash']==r['planHash']


def test_empty_upper_floors_are_not_invented_or_silently_deleted():
    p=rough();p['brief']['storeys']=3
    p['customPlan']['floors'] += [{'id':f'floor-{f}','rooms':[],'walls':[],'openings':[]} for f in (1,2)]
    r=prepare_plan(p)
    assert not r['valid'] and len(r['customPlan']['floors'])==3
    assert {e['floor'] for e in r['errors'] if e['code']=='EMPTY_FLOOR'}=={1,2}
    assert any(c['kind']=='wall-spacing' for c in r['changes'])


def test_large_overlap_stays_blocked_and_dimensions_are_not_optimized_away():
    p=rough();p['customPlan']['floors'][0]['rooms'][1]['polygon']=copy.deepcopy(p['customPlan']['floors'][0]['rooms'][0]['polygon'])
    r=prepare_plan(p)
    assert not r['valid'] and any(e['code']=='SPACE_OVERLAP' for e in r['errors'])
    assert all(Polygon(q['polygon']).area==16000000 for q in r['customPlan']['floors'][0]['rooms'])


def test_aligned_existing_stairs_link_automatically_without_relocation():
    p=json.loads((Path(__file__).parents[1]/'examples/custom/g2-terrace.floorforge.json').read_text())
    p['brief']['roof_access']=True;p['customPlan']['stairs']=[]
    before={r['id']:r['polygon'] for f in p['customPlan']['floors'] for r in f['rooms'] if r['kind']=='stair'}
    result=prepare_plan(p)
    assert result['valid'] and any(c['kind']=='stair-link' for c in result['changes'])
    after={r['id']:r['polygon'] for f in result['customPlan']['floors'] for r in f['rooms'] if r['kind']=='stair'}
    assert before==after and len(result['customPlan']['floors'])==3
    assert len(result['customPlan']['stairs'][0]['roomIds'])==3


def test_existing_openings_and_authored_partitions_are_retained():
    p=rough();p['customPlan']=prepare_plan(p)['customPlan'];f=p['customPlan']['floors'][0]
    before=copy.deepcopy(f['openings']);result=prepare_plan(p)
    assert result['customPlan']['floors'][0]['openings']==before
    # An explicit partition prevents automatic room translations on that floor.
    p=rough();p['customPlan']['floors'][0]['walls']=[{'id':'partition','a':[8500,200],'b':[8500,3000]}]
    result=prepare_plan(p)
    assert not result['valid'] and not any(c['kind']=='wall-spacing' for c in result['changes'])
    assert result['customPlan']['floors'][0]['walls']==p['customPlan']['floors'][0]['walls']
