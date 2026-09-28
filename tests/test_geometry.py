import pytest,math,copy
from shapely.geometry import Polygon,box
from shapely.affinity import scale
from shapely.ops import unary_union
from floorforge.model import *
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate,reports
from floorforge.scene import extrude
from conftest import CASES

@pytest.mark.parametrize('style',list(STYLES))
@pytest.mark.parametrize('case',list(CASES))
def test_fixture_styles_screen(case,style):
    b=generate_layout(fuse({'brief':{**CASES[case],'style':style}}));r=validate(b)
    assert not r['errors'];assert b['storeys']==b['brief']['storeys']
    assert sum(s['kind']=='bedroom' for s in b['spaces'])==b['brief']['bedrooms']

@pytest.mark.parametrize('bearing',range(0,360,45))
def test_facing_does_not_rotate_geometry_or_promote_floors(bearing,model):
    # With Vastu off, facing never changes the plan.
    off=generate_layout(fuse({'brief':{'vastu':'off'}}))
    b=generate_layout(fuse({'brief':{'road_bearing_deg':bearing,'vastu':'off'}}))
    assert b['spaces']==off['spaces'] and b['footprint']==off['footprint']
    # With Vastu on, facing may only choose the hand: the same plan or its mirror, never a rotation or another floor.
    b=generate_layout(fuse({'brief':{'road_bearing_deg':bearing}}))
    validate(b)
    assert b['storeys']==model['storeys'] and b['footprint']==model['footprint']
    W=Polygon(model['footprint']).bounds[2]
    base={s['id']:Polygon(s['polygon']) for s in off['spaces']}
    same=all(Polygon(s['polygon']).symmetric_difference(base[s['id']]).area<1 for s in b['spaces'])
    flip=all(Polygon(s['polygon']).symmetric_difference(scale(base[s['id']],-1,1,origin=(W/2,0))).area<1 for s in b['spaces'])
    assert same or flip
    assert b['planning']['vastu_mirrored']==flip

@pytest.mark.parametrize('variant',[0,1,2])
def test_variants_are_valid_and_geometric(variant):
    b=generate_layout(fuse({'brief':{'variant':variant}}));validate(b)
    if variant:assert b['spaces']!=generate_layout(fuse({'brief':{}}))['spaces']

def test_determinism(model):assert model==generate_layout(fuse({'brief':{}}))

def test_complete_floor_partition(model):
    fp=Polygon(model['footprint'])
    for floor in range(model['storeys']):
        cells=[Polygon(s['polygon']) for s in model['spaces'] if s['floor']==floor]
        assert unary_union(cells).symmetric_difference(fp).area<1
        assert abs(sum(p.area for p in cells)-fp.area)<1

def test_clear_space_does_not_intersect_wall(model):
    for s in model['spaces']:
        wall=unary_union([Polygon(w['polygon']) for w in model['walls'] if w['floor']==s['floor']])
        assert Polygon(s['clear']).intersection(wall).area<1

def test_bedrooms_never_required_through_routes(model):
    graph=validate(model)['graph'];kinds={s['id']:s['kind'] for s in model['spaces']}
    for room in [s for s in model['spaces'] if s['kind']=='bedroom']:
        seen={'outside'};todo=['outside']
        while todo:
            for neighbor in graph[todo.pop()]:
                if neighbor!=room['id'] and neighbor not in seen:seen.add(neighbor);todo.append(neighbor)
        # Only the bedroom's own attached bath and dressing room lie beyond it.
        assert all(kinds[r] in ('bathroom','dress') for r in set(graph)-{room['id']}-seen)

@pytest.mark.parametrize('case',list(CASES))
def test_circulation_is_economical(case):
    b=generate_layout(fuse({'brief':CASES[case]}))
    for floor in range(b['storeys']):
        rooms=[s for s in b['spaces'] if s['floor']==floor]
        hall=sum(s['area_m2'] for s in rooms if s['kind']=='hall');total=sum(s['area_m2'] for s in rooms)
        # Circulation of 10-15% of a floor is normal for a house; corridors keep a 1.0 m clear width.
        assert hall<=.15*total
        for s in rooms:
            if s['kind']=='hall':
                x0,y0,x1,y1=Polygon(s["clear"]).bounds;assert min(x1-x0,y1-y0)>=1000

def test_stair_core_same_xy_and_real_rise(model):
    assert len(model['stairs'])==2
    first,second=model['stairs'];assert all(first[k]==second[k] for k in ['x','y','width','depth'])
    assert abs(first['riser_count']*first['riser_mm']-model['brief']['floor_height_mm'])<1e-6
    for st in model['stairs']:
        p=box(st['x'],st['y'],st['x']+st['width'],st['y']+st['depth'])
        walls=unary_union([Polygon(w['polygon']) for w in model['walls'] if w['floor']==st['floor']])
        assert p.intersection(walls).area<1

def test_upper_terrace_is_real_space(model):
    terrace=[s for s in model['spaces'] if s['kind']=='terrace']
    assert len(terrace)==1 and terrace[0]['floor']==1
    assert any(o['kind']=='glazed' and terrace[0]['id'] in o['connects'] for o in model['openings'])

def test_no_fake_approval(model):
    r=reports(model,validate(model));assert r['review']['construction_ready'] is False
    assert r['review']['regulatory']=='NOT EVALUATED';assert r['structure']['foundation_recommendation'] is None
    assert r['quantities']['reinforcement_kg'] is None

@pytest.mark.parametrize('brief',[{'width_mm':5000,'depth_mm':6500},{'storeys':1,'bedrooms':8},{'storeys':2,'bedrooms':1},{'parking':True,'front_mm':2000}])
def test_infeasible_programme_blocked(brief):
    with pytest.raises(DesignError):validate(generate_layout(fuse({'brief':brief})))

def grid_project(nonrect=False):
    rows=[]
    for y in range(12):
        if y<4:row=['living']*6+['dining']*3
        elif y<6:row=['kitchen']*4+['hall']+['bathroom']*4
        elif y<8:row=['kitchen']*4+['hall']+['utility']*4
        else:row=['bedroom-1']*4+['hall']+['bedroom-2']*4
        if nonrect and y>=10:row[0]=row[1]=''
        rows.append(row)
    return {'brief':{'storeys':1,'bedrooms':2,'width_mm':14000,'depth_mm':20000},'grid':{'cell_mm':1250,'floors':[rows]}}

@pytest.mark.parametrize('nonrect',[False,True])
def test_manual_grid_preserves_real_polygon(nonrect):
    b=generate_layout(fuse(grid_project(nonrect)));validate(b)
    expected=9*12*1250**2-(4*1250**2 if nonrect else 0)
    assert abs(Polygon(b['footprint']).area-expected)<1
    if nonrect:assert len(b['footprint'])>4

def test_grid_never_silently_resized():
    p=grid_project();p['brief']['width_mm']=8000
    with pytest.raises(DesignError) as e:generate_layout(fuse(p))
    assert e.value.code=='GRID_OUTSIDE'

def test_disconnected_grid_room_rejected():
    p=grid_project();p['grid']['floors'][0][0][0]='bedroom-1'
    with pytest.raises(DesignError) as e:generate_layout(fuse(p))
    assert e.value.code=='GRID_CONNECTED'

def test_mesh_hole_is_not_bounding_box():
    p=box(0,0,5,5).difference(box(1,1,4,4));m=extrude(p,0,2)
    assert m.is_watertight;assert abs(m.volume-p.area*2)<1e-6

@pytest.mark.parametrize('key,mutate',[('rooms',lambda b:b['spaces'].__setitem__(1,copy.deepcopy(b['spaces'][0]))),('opening',lambda b:b['openings'][0].__setitem__('width',999999))])
def test_adversarial_geometry_rejected(model,key,mutate):
    b=copy.deepcopy(model);mutate(b)
    with pytest.raises(DesignError):validate(b)


def test_report_does_not_mutate_validated_dag_stage():
    b=generate_layout(fuse({'brief':{'vastu':'strict'}}));v=validate(b);before=copy.deepcopy(v)
    r=reports(b,v)
    assert v==before
    assert r['areas']['open_terrace_m2']>0


def test_professional_screen_is_quiet_on_the_default(model):
    codes={w['code'] for w in validate(model)['warnings']}
    # Habitable rooms get a tenth of their floor in openings and every bath opens to the air.
    assert not codes&{'LOW_DAYLIGHT','BATH_VENTILATION','POOJA_BESIDE_BATH','DOOR_SWING_CLASH','WET_ABOVE_POOJA'}


def test_professional_screen_flags_what_a_reviewer_would(model):
    b=copy.deepcopy(model)
    bath=next(s for s in b['spaces'] if s['kind']=='bathroom')
    b['openings']=[o for o in b['openings'] if not (o['kind']=='window' and bath['id'] in o['connects'])]
    door=next(o for o in b['openings'] if o['kind']=='door' and o.get('swing'))
    twin={**copy.deepcopy(door),'id':door['id']+'-twin'}
    twin['offset']=door['offset']+100
    b['openings'].append(twin)
    codes=[(w['code'],w.get('id') or tuple(w.get('ids',()))) for w in validate(b)['warnings']]
    assert ('BATH_VENTILATION',bath['id']) in codes
    assert ('DOOR_SWING_CLASH',(door['id'],twin['id'])) in codes


def test_unresolved_requests_name_the_shortfall():
    b=generate_layout(fuse({'brief':{'width_mm':9144,'depth_mm':12192,'storeys':1,'bedrooms':2,'front_mm':1800,'rear_mm':900,'left_mm':750,'right_mm':750}}))
    r=reports(b,validate(b));got=b['planning']['attached_baths']
    assert got['provided']<got['requested']
    assert any(x.startswith(f'Attached baths: {got["provided"]} of {got["requested"]}') for x in r['unresolved_requests'])
    assert any(w['code']=='ENSUITE_SHORTFALL' for w in r['review']['warnings'])
    assert '' not in r['unresolved_requests']
