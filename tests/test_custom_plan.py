"""End-to-end acceptance for exact geometry, revision identity and per-floor guides."""
import copy,json,gzip
from geometry_snapshot import assert_visual_snapshot
from pathlib import Path
import pytest
from shapely.geometry import Polygon,box
from floorforge.model import DesignError,sha,read_json
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate,reports
from floorforge.exterior import apply_exterior_preferences
from floorforge.scene import make_scene
from floorforge.plan_geometry import plate,roof,geometry
from floorforge.pipeline import run

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def project():return read_json(ROOT/'examples/custom/g2-terrace.floorforge.json')

def build(p):return generate_layout(fuse(p))

def codes(error):return {x['code'] for x in error.value.details['errors']}

def test_exact_g2_bypasses_planner_and_keeps_clear_dimensions(project,monkeypatch):
    monkeypatch.setattr('floorforge.layout.automatic_spaces',lambda *a,**k:pytest.fail('custom plan invoked automatic planner'))
    b=build(project);validate(b)
    room=next(s for s in b['spaces'] if s['id']=='custom-F1-bedroom')
    assert Polygon(room['clear']).bounds==(3850,4400,7850,8400)
    assert room['area_m2']==16
    assert [s['id'] for s in b['floors']]==['custom-floor-0','custom-floor-1','custom-floor-2']
    terrace=next(s for s in b['spaces'] if s['kind']=='terrace');p=Polygon(terrace['polygon'])
    assert plate(b,1).covers(p)
    assert plate(b,2).intersection(p).area<1
    assert all(roof(b,f).intersection(p).area<1 for f in (1,2))
    assert any(g['owner']==terrace['id'] for g in b['guards'])
    for st in b['stairs'][1:]:
        hole=box(st['x'],st['y']+st['landing_mm'],st['x']+st['width'],st['y']+st['depth'])
        assert plate(b,st['floor']).intersection(hole).area<1


def test_hash_survives_save_reopen_and_excludes_revision(project):
    a=fuse(project);reopened=json.loads(json.dumps(project));reopened['draftRevision']=42
    assert fuse(reopened)['planHash']==a['planHash']
    reopened['customPlan']['floors'][1]['rooms'][0]['polygon'][0][0]+=10
    assert fuse(reopened)['planHash']!=a['planHash']

@pytest.mark.parametrize('issue',['overlap','setback','stair','terrace','drain','window','access','opening'])
def test_invalid_edits_block_with_object_ids(project,issue):
    fl=project['customPlan']['floors'];expected=None
    if issue=='overlap':fl[0]['rooms'][2]['polygon']=fl[0]['rooms'][0]['polygon'];expected='SPACE_OVERLAP'
    if issue=='setback':fl[0]['rooms'][2]['polygon']=[[x-8000,y] for x,y in fl[0]['rooms'][2]['polygon']];expected='SETBACK'
    if issue=='stair':
        for room in fl[1]['rooms']:room['polygon']=[[x+50,y] for x,y in room['polygon']]
        expected='STAIR_ALIGNMENT'
    if issue=='terrace':fl[2]['rooms'].append({**copy.deepcopy(fl[1]['rooms'][-1]),'id':'covered-terrace','kind':'balcony'});expected='OPEN_SKY_BLOCKED'
    if issue=='drain':fl[1]['rooms'][3]['drain']=False;expected='DRYING_DRAIN'
    if issue=='window':fl[1]['openings']=[o for o in fl[1]['openings'] if o['id']!='custom-F1-bed-window'];expected='NO_EXTERNAL_WINDOW'
    if issue=='access':fl[1]['openings']=[o for o in fl[1]['openings'] if o['id']!='custom-F1-terrace-door'];expected='UNREACHABLE'
    if issue=='opening':fl[0]['openings'][0]['offset']=50000;expected='OPENING_HOST'
    with pytest.raises(DesignError) as e:validate(build(project))
    assert expected in codes(e)
    assert all('id' in x or 'ids' in x for x in e.value.details['errors'])


def test_openings_and_room_ids_survive_theme_refinement(project):
    b=build(project);after=apply_exterior_preferences(b)
    assert b['spaces']==after['spaces']
    assert b['openings']==after['openings']
    assert b['stairs']==after['stairs']
    assert after['planHash']==b['planHash']


def test_every_export_has_same_plan_hash_and_three_different_floors(project,tmp_path):
    result=run(project,tmp_path,use_cache=False);out=Path(result['path']);h=fuse(project)['planHash']
    for name in ('building','scene','report','manifest'):
        assert read_json(out/(name+'.json'))['planHash']==h
    scene=read_json(out/'scene.json');building=read_json(out/'building.json')
    assert sum(n['role']=='floor' for n in scene['nodes'])==3
    assert {r['floor'] for r in scene['rooms']}=={0,1,2}
    assert next(r for r in scene['rooms'] if r['id']=='custom-F1-bedroom')['polygon']==[[3.85,4.4],[7.85,4.4],[7.85,8.4],[3.85,8.4]]
    assert h in (out/'model.ifc').read_text(encoding='utf-8')
    assert 'IFCSTAIR(' in (out/'model.ifc').read_text(encoding='utf-8')
    assert h in (out/'floorplans.dxf').read_text(encoding='utf-8')
    assert all(h in p.read_text(encoding='utf-8') for p in (out/'sheets').glob('*.svg'))
    import struct
    glb=(out/'model.glb').read_bytes();length=struct.unpack_from('<I',glb,12)[0]
    assert json.loads(glb[20:20+length])['scenes'][0]['extras']['planHash']==h
    assert ('/Subject (planHash:'+h+')').encode() in (out/'drawings.pdf').read_bytes()
    report=read_json(out/'report.json')
    assert report['areas']['gross_floor_m2']==round(sum(plate(building,f).area for f in range(3))/1e6,3)


def test_a_kitchen_edit_changes_its_walls_opening_and_scene(project):
    p=copy.deepcopy(project);p['brief']['storeys']=1;p['brief']['bedrooms']=1;p['customPlan']['floors']=p['customPlan']['floors'][:1];p['customPlan']['stairs']=[]
    fl=p['customPlan']['floors'][0];fl['rooms'][0]['kind']='utility'
    a=apply_exterior_preferences(build(p));validate(a)
    kitchen=next(r for r in fl['rooms'] if r['kind']=='kitchen');kitchen['polygon']=[[x,y+300] for x,y in kitchen['polygon']]
    b=apply_exterior_preferences(build(p));validate(b)
    sid=kitchen['id'];assert a['planHash']!=b['planHash']
    assert next(s for s in a['spaces'] if s['id']==sid)['polygon']!=next(s for s in b['spaces'] if s['id']==sid)['polygon']
    assert [w for w in a['walls'] if sid in w['rooms']]!=[w for w in b['walls'] if sid in w['rooms']]
    for building in (a,b):
        opening=next(o for o in building['openings'] if o['id']=='custom-F0-service-window');w=next(w for w in building['walls'] if w['id']==opening['wall_id'])
        assert w['a'][1]+opening['offset']==(5300 if building is a else 5600)
    sa=make_scene(a,reports(a,validate(a)));sb=make_scene(b,reports(b,validate(b)))
    assert next(r for r in sa['rooms'] if r['id']==sid)!=next(r for r in sb['rooms'] if r['id']==sid)
    assert [n for n in sa['nodes'] if n.get('owner')==sid]!=[n for n in sb['nodes'] if n.get('owner')==sid]


def test_guides_keep_floor_assignments_and_fixed_dimensions():
    boards=[[['']*4 for _ in range(4)] for _ in range(3)]
    boards[0][2][0]='kitchen';boards[1][0][3]='terrace';boards[2][3][3]='bedroom-3'
    p={'brief':{'storeys':3,'bedrooms':3},'grid':{'mode':'spatial_hint','rows':4,'cols':4,'floorIds':['g','f','s'],'floors':boards}}
    intent=fuse(p)
    assert [(h['floor'],h['label']) for h in intent['placement_hints']]==[(0,'kitchen'),(1,'terrace'),(2,'bedroom-3')]
    p['grid']['floors'][2].append(['']*4)
    with pytest.raises(DesignError) as e:fuse(p)
    assert e.value.code=='GRID_SIZE'


def test_guide_unsupported_floor_room_returns_specific_conflict():
    p={'brief':{'storeys':2,'bedrooms':3},'grid':{'mode':'spatial_hint','rows':4,'cols':4,'floorIds':['g','f'],'floors':[[['']*4 for _ in range(4)] for _ in range(2)]}}
    p['grid']['floors'][1][0][0]='kitchen'
    with pytest.raises(DesignError) as e:build(p)
    assert e.value.code.startswith('PLACEMENT_')


def test_legacy_presets_keep_aesthetic_geometry():
    baseline=read_json(ROOT/'evidence/custom-plan/aesthetic-baseline.json')
    snapshots=json.loads(gzip.decompress((ROOT/'tests/fixtures/legacy_visual_geometry.json.gz').read_bytes()))
    for name,record in baseline['presets'].items():
        b=apply_exterior_preferences(build(record['input']));s=make_scene(b,reports(b,validate(b)))
        assert_visual_snapshot(s,snapshots[name])


def test_veranda_is_covered_and_two_terraces_share_an_open_edge(project):
    p=copy.deepcopy(project);outdoor=p['customPlan']['floors'][1]['rooms'][-1];outdoor['kind']='veranda'
    b=build(p);validate(b)
    assert roof(b,1).intersection(Polygon(outdoor['polygon'])).area==Polygon(outdoor['polygon']).area
    p=copy.deepcopy(project);fl=p['customPlan']['floors'][1];terrace=fl['rooms'][-1]
    terrace['polygon']=[[3850,0],[5925,0],[5925,4250],[3850,4250]]
    fl['rooms'].append({'id':'terrace-east','kind':'terrace','name':'East terrace','polygon':[[5925,0],[8000,0],[8000,4250],[5925,4250]]})
    b=build(p);review=validate(b)
    assert 'terrace-east' in review['graph'][terrace['id']]
    assert {g['owner'] for g in b['guards']}>={terrace['id'],'terrace-east'}


def test_void_cuts_floor_and_lower_ceiling_but_retains_upper_roof(project):
    fl=project['customPlan']['floors'][2];room=next(r for r in fl['rooms'] if r['kind']=='study');room['kind']='void'
    fl['openings']=[o for o in fl['openings'] if o['roomId']!=room['id']]
    b=build(project);validate(b);p=Polygon(room['polygon'])
    assert plate(b,2).intersection(p).area==0
    assert geometry(b['roofs'][1]['ceiling']).intersection(p).area==0
    assert roof(b,2).covers(p)
    # Every stair hole is absent in the ceiling underneath, not just in the slab above it.
    for plate_record in b['floor_plates'][1:]:
        for opening in plate_record['openings']:
            assert geometry(b['roofs'][plate_record['floor']-1]['ceiling']).intersection(geometry(opening['regions'])).area==0


def test_stable_opening_edit_changes_only_requested_width(project):
    p=copy.deepcopy(project);o=next(o for o in p['customPlan']['floors'][0]['openings'] if o['kind']=='window');o['width']=1800
    a=build(project);b=build(p);validate(b)
    old=next(x for x in a['openings'] if x['id']==o['id']);new=next(x for x in b['openings'] if x['id']==o['id'])
    assert new=={**old,'width':1800}
    assert a['spaces']==b['spaces'] and a['walls']==b['walls']


def test_g2_automatic_plan_has_three_aligned_stair_levels():
    b=generate_layout(fuse({'brief':{'storeys':3,'bedrooms':3}}));validate(b)
    assert [s['floor'] for s in b['stairs']]==[0,1,2]
    assert len({(s['x'],s['y'],s['width'],s['depth']) for s in b['stairs']})==1
    assert any(s['floor']==1 and s['kind']=='veranda' for s in b['spaces'])
    assert any(s['floor']==2 and s['kind']=='terrace' for s in b['spaces'])


def test_guide_programme_conflict_identifies_floor_and_cells():
    boards=[[['']*4 for _ in range(4)] for _ in range(3)];boards[2][1][3]='bedroom-8'
    with pytest.raises(DesignError) as e:fuse({'brief':{'storeys':3,'bedrooms':3},'grid':{'mode':'spatial_hint','rows':4,'cols':4,'floorIds':['g','f','s'],'floors':boards}})
    assert e.value.details['rooms'][0]['floor']==2
    assert e.value.details['rooms'][0]['cells']==[[3,1]]


def test_service_lightwell_cannot_bypass_occupied_room_or_door_access():
    from scripts.build_desired_home import project as desired_project
    p=desired_project()
    living=next(r for r in p['customPlan']['floors'][0]['rooms'] if r['id']=='g-living')
    living['serviceOnly']=True
    with pytest.raises(DesignError):build(p)
    p=desired_project()
    p['customPlan']['floors'][0]['openings'].append(dict(id='invalid-lightwell-door',roomId='g-living',side='rear',offset=1376,width=1100,height=2100,sill=0,kind='glazed'))
    with pytest.raises(DesignError) as e:validate(build(p))
    assert 'VOID_ACCESS' in codes(e)
