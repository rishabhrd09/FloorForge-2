"""Approved indoor G+2 stair, envelope and circulation regressions."""
import pytest
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.tirumala_5 import build_project
from floorforge.tirumala_luxury import upper_plan
from floorforge.tirumala_5_upper import (H, LEVEL, RISE, HALL, GUEST, FIRST_APPROACH,
    GUEST_EXTENSION, compile_addition, validate_addition)

@pytest.fixture(scope='module')
def model():
    b=generate_layout(fuse(build_project()))
    if not b['planning'].get('secondPlan'):compile_addition(b)
    return b

def shape(regions):return unary_union([Polygon(r['polygon'],r.get('holes',[])) for r in regions])

def test_only_authorized_first_rooms_change(model):
    original=upper_plan(model['planning']['canonicalPlan'])
    now={r['id']:r for r in model['planning']['upperPlan']['rooms']}
    for r in original['rooms']:
        before,after=shape(r['regions']),shape(now[r['id']]['regions'])
        if r['id']=='u-bedroom':assert after.equals(box(*GUEST).union(box(*GUEST_EXTENSION)))
        elif r['id']=='u-gallery':
            guest=box(*GUEST).union(box(*GUEST_EXTENSION))
            assert before.union(box(*FIRST_APPROACH)).difference(guest.buffer(150,join_style=2)).equals(after)
        elif r['id']=='u-terrace':assert before.intersection(box(0,1524,9032,4800)).equals(after)
        else:assert before.symmetric_difference(after).area<1,r['id']
    assert now['u-bedroom']['bounds'][2]-now['u-bedroom']['bounds'][0]==pytest.approx(3387.2)
    assert now['u-bedroom']['bounds'][3]-now['u-bedroom']['bounds'][1]==5050
    guest=shape(now['u-bedroom']['regions'])
    assert guest.intersection(box(0,6350,12192,9200)).bounds[0]==8045.2
    assert guest.intersection(box(0,9201,12192,11400)).bounds[0]==8350
    assert guest.area-box(*GUEST).area==pytest.approx(304.8*2850)


def test_indoor_approach_preserves_first_guest_and_main_terrace_routes(model):
    up=model['planning']['upperPlan'];gallery=shape(next(r for r in up['rooms'] if r['id']=='u-gallery')['regions'])
    for name,width in [('arrival_to_stair',1100),('arrival_to_guest',900),('arrival_to_main_terrace',900),('arrival_to_office',800)]:
        route=LineString(up['circulationPaths'][name]).buffer(width/2,cap_style=2,join_style=2)
        assert gallery.buffer(.01).covers(route),name
    # Retain a genuine 3 ft passage around the new bedroom's stepped return.
    # The existing office door itself is 900 mm, so test its final approach separately.
    corridor=LineString(up['circulationPaths']['arrival_to_office'][:-1]).buffer(914.4/2,cap_style=2,join_style=2)
    assert gallery.buffer(.01).covers(corridor)
    ids={o['id'] for o in model['openings']}
    assert not ids.intersection({'s2-stair-entry','u-side-terrace-door','u-bedroom-terrace'})
    assert {'u-bedroom-door','u-terrace-door','u-bedroom-east-proposed'}<=ids


def test_first_slab_keeps_ground_stair_void_and_double_height_area_clear(model):
    up=model['planning']['upperPlan'];plate=shape(up['floorPlate'])
    assert plate.intersection(shape(up['stairVoid'])).area<1
    assert Polygon(up['void']).equals(box(1250,6075,6300,7800))
    assert Polygon(up['void']).area==5050*1725
    assert plate.intersection(Polygon(up['void'])).area<1
    assert plate.covers(box(*FIRST_APPROACH))
    assert not plate.covers(box(8400,4900,9000,5900))  # old side link is removed
    assert Polygon(next(s for s in model['shafts'] if s['id']=='living-double-height')['polygon']).equals(Polygon(up['void']))


def test_g2_hall_dimensions_terrace_connectivity_and_slab_opening(model):
    sp=model['planning']['secondPlan'];rooms={r['id']:shape(r['regions']) for r in sp['rooms']}
    assert rooms['s2-hall'].symmetric_difference(box(*HALL)).area<1
    assert rooms['s2-terrace'].geom_type=='Polygon'
    assert rooms['s2-hall'].intersection(rooms['s2-terrace']).area<1
    assert rooms['s2-indoor-landing'].intersection(rooms['s2-terrace']).area<1
    slab=shape(sp['floorPlate']);shaft=shape(sp['stairVoid'])
    ground=model['planning']['canonicalPlan']
    lower_footprint=unary_union([Polygon(s['polygon']) for s in ground['stairs']]+
        [box(*s['bounds']) for s in upper_plan(ground)['connectorSteps']])
    assert shaft.symmetric_difference(lower_footprint).area<.01
    assert slab.intersection(shaft).area<1
    assert slab.intersection(Polygon(sp['lightwell']).buffer(-1)).area<1
    assert slab.covers(box(*sp['stairArrival']))
    assert slab.covers(shape(sp['newBedRoof']))


def test_g2_stairs_height_spacing_and_lower_stair_headroom(model):
    sp=model['planning']['secondPlan'];steps=[s for s in sp['stairs'] if not s.get('landing')]
    assert len(steps)==20
    assert len(sp['stairs'])==23
    assert [steps[0]['top']-H]+[c['top']-a['top'] for a,c in zip(steps,steps[1:])]==pytest.approx([175]*18+[179]*2)
    assert steps[-1]['top']==LEVEL
    # Independent expected tread schedule, derived from the retained lower flights.
    # All three flights and both short arrival steps must align in XY, not just fit a bbox.
    expected=[];rise_index=0
    for flight in model['planning']['canonicalPlan']['stairs']:
        x0,y0,x1,y1=Polygon(flight['polygon']).bounds
        if 'level' in flight:
            upper=next(s for s in sp['stairs'] if s['id']=='s2-'+flight['id'])
            assert upper['landing'] and upper['bounds']==[x0,y0,x1,y1]
            assert upper['top']==H+flight['level']
            continue
        n=flight['risers']
        for i in range(n):
            if flight['direction']=='South':
                bounds=[x1-(i+1)*(x1-x0)/n,y0,x1-i*(x1-x0)/n,y1]
            elif flight['direction']=='West':
                bounds=[x0,y0+i*(y1-y0)/n,x1,y0+(i+1)*(y1-y0)/n]
            else:
                bounds=[x0+i*(x1-x0)/n,y0,x0+(i+1)*(x1-x0)/n,y1]
            rise_index+=1;expected.append((bounds,H+175*rise_index))
    for connector in upper_plan(model['planning']['canonicalPlan'])['connectorSteps']:
        expected.append((connector['bounds'],H+connector['top']))
    for actual,(bounds,top) in zip(steps,expected):
        assert actual['bounds']==pytest.approx(bounds)
        assert actual['top']==top
    assert steps[0]['bounds']==[1387.5,5000,1525,6100]
    assert steps[-1]['bounds']==[4850,7800,5150,8900]
    # Same-plan sloping upper waist: at each lower tread's leading edge its
    # underside is one rise + 180 mm below the upper tread top.
    clearance=[]
    base=0
    for count in [2,7,9]:
        for i in range(count):
            old_top=base+(i+1)*175
            new_underside=H+base+i*175-180
            clearance.append(new_underside-old_top)
        base+=count*175
    assert min(clearance)==3153
    assert sp['minimumAnalyticGroundStairHeadroomMm']==pytest.approx(min(clearance))
    assert all(c['status']=='pass' for c in validate_addition(model))


def test_second_stair_landing_is_enclosed_and_roofed_with_clear_arrival(model):
    sp=model['planning']['secondPlan'];rooms={r['id']:shape(r['regions']) for r in sp['rooms']}
    roof=shape(sp['hallRoof']);outer=shape(sp['headhouseRegions'])
    assert roof.covers(outer.difference(Polygon(sp['atriumOpening'])))
    assert rooms['s2-indoor-landing'].covers(box(5150,7800,6600,8900))
    assert rooms['s2-indoor-landing'].covers(box(5485.6,8900,6600,10050))
    assert 6600-5485.6>=1100
    entrance=next(o for o in model['openings'] if o['id']=='s2-hall-entry')
    assert entrance['connects']==['s2-indoor-landing','s2-hall']
    assert entrance['width']==1000 and entrance['a']==[5410.6,9050]
    assert entrance['b']==[5410.6,10050]
    # 55 mm jambs leave 890 mm clear, not the prior narrow 690 mm opening.
    assert entrance['width']-2*55==890
    terrace=next(o for o in model['openings'] if o['id']=='s2-stair-terrace-proposed')
    assert terrace['width']==1000 and terrace['connects']==['s2-indoor-landing','s2-terrace']
    top_arrival=LineString([[4850,8350],[6050,8350]]).buffer(450,cap_style=2)
    for a,c in sp['landingGuards']:
        assert LineString([a,c]).buffer(12,cap_style=2).intersection(top_arrival).area<1
    wall=shape(sp['wallRegions'])
    for name,width in [('stairs_to_hall',850),('stairs_to_terrace',900)]:
        path=LineString(sp['circulationPaths'][name]).buffer(width/2,cap_style=2,join_style=2)
        assert path.intersection(wall).area<1,name
        assert shape(sp['floorPlate']).buffer(.01).covers(path),name


def test_landing_return_uses_existing_lightwell_wall_not_clear_air_shaft(model):
    sp=model['planning']['secondPlan'];up=model['planning']['upperPlan']
    wall=shape(sp['wallRegions']);clear=Polygon(up['lightwellClear'])
    assert wall.intersection(clear).area<.01
    assert shape(sp['hallRoof']).intersection(clear).area<.01
    new_wall_band=box(5485.6,10050,6600,10200)
    assert wall.covers(new_wall_band)
    # It bears on the original first-floor lightwell masonry, with the slab
    # opening left intact; no unsupported flooring projects over the shaft.
    assert shape(up['wallRegions']).covers(new_wall_band)
    assert shape(sp['floorPlate']).intersection(Polygon(up['lightwell'])).area<.01
    for room in sp['rooms']:
        assert room['enclosed']==(room['kind']!='terrace')
        assert room['roofed']==(room['kind']!='terrace')
    compiled=next(s for s in model['spaces'] if s['id']=='s2-indoor-landing')
    assert compiled['enclosed'] and compiled['roofed']


def test_g2_hall_furniture_does_not_block_glass_or_entrance(model):
    sp=model['planning']['secondPlan'];hall=box(*HALL)
    glass_route=box(4200,12400,5600,14100)
    entry_route=box(4300,9050,5300,10000)
    for f in sp['furniture']:
        if f['id'].startswith('s2-terrace'):continue
        item=box(*f['bounds'])
        assert hall.covers(item),f['id']
        assert item.intersection(glass_route).area<1,f['id']
        assert item.intersection(entry_route).area<1,f['id']


def test_g2_glass_door_opens_onto_supported_terrace_not_lightwell(model):
    sp=model['planning']['secondPlan'];op=next(o for o in model['openings'] if o['id']=='s2-hall-garden')
    door=LineString([op['a'],op['b']]).buffer(80,cap_style=2)
    assert door.intersection(Polygon(sp['lightwell'])).area<1
    assert shape(sp['floorPlate']).covers(door)
    approach=box(5485.6,12500,6400,13700)
    assert shape(next(r for r in sp['rooms'] if r['id']=='s2-terrace')['regions']).covers(approach)
    for f in sp['furniture']:
        if f['id'].startswith('s2-terrace'):assert approach.intersection(box(*f['bounds'])).area<1


def test_serialized_project_and_compiled_rooms_share_one_geometry(model):
    cp=build_project()['customPlan']
    for key in ['upperPlan','secondPlan']:
        compiled={r['id']:r for r in model['planning'][key]['rooms']}
        for r in cp[key]['rooms']:
            assert shape(r['regions']).symmetric_difference(shape(compiled[r['id']]['regions'])).area<1


def test_upper_opening_hosts_resolve_to_spaces(model):
    spaces={r['id'] for r in model['spaces']}|{'outside'}
    hosts={w['id']:w for w in model['walls']}
    for o in model['openings']:
        if o['floor']<1:continue
        assert set(o['connects'])<=spaces,o['id']
        assert o['wall_id'] in hosts
        if o['id'] in ('s2-hall-entry','u-bedroom-door'):
            assert not hosts[o['wall_id']]['external']
