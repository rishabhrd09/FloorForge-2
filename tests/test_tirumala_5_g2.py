"""Approved indoor G+2 stair, envelope and circulation regressions."""
from copy import deepcopy
import pytest
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.tirumala_5 import build_project
from floorforge.tirumala_luxury import upper_plan
from floorforge.tirumala_5_upper import (H, LEVEL, RISE, HALL, GUEST, FIRST_APPROACH,
    SECOND_SHAFT, HEADHOUSE_OUTER, BEDROOM_ROOF, compile_addition, validate_addition)

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
        if r['id']=='u-bedroom':assert after.equals(box(*GUEST))
        elif r['id']=='u-gallery':assert before.union(box(*FIRST_APPROACH)).equals(after)
        elif r['id']=='u-terrace':assert before.intersection(box(0,1524,9032,4800)).equals(after)
        else:assert before.symmetric_difference(after).area<1,r['id']
    assert now['u-bedroom']['bounds'][2]-now['u-bedroom']['bounds'][0]==pytest.approx(3082.4)
    assert now['u-bedroom']['bounds'][3]-now['u-bedroom']['bounds'][1]==5050


def test_indoor_approach_preserves_first_guest_and_main_terrace_routes(model):
    up=model['planning']['upperPlan'];gallery=shape(next(r for r in up['rooms'] if r['id']=='u-gallery')['regions'])
    for name,width in [('arrival_to_stair',1100),('arrival_to_guest',900),('arrival_to_main_terrace',900),('arrival_to_office',800)]:
        route=LineString(up['circulationPaths'][name]).buffer(width/2,cap_style=2,join_style=2)
        assert gallery.buffer(.01).covers(route),name
    ids={o['id'] for o in model['openings']}
    assert not ids.intersection({'s2-stair-entry','u-side-terrace-door','u-bedroom-terrace'})
    assert {'u-bedroom-door','u-terrace-door','u-bedroom-east-proposed'}<=ids


def test_first_slab_keeps_ground_stair_void_and_reduced_double_height_clear(model):
    up=model['planning']['upperPlan'];plate=shape(up['floorPlate'])
    assert plate.intersection(shape(up['stairVoid'])).area<1
    assert Polygon(up['void']).equals(box(1250,4875,6300,6600))
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
    assert shaft.equals(box(*SECOND_SHAFT))
    assert slab.intersection(shaft).area<1
    assert slab.intersection(Polygon(sp['lightwell']).buffer(-1)).area<1
    assert slab.covers(box(*sp['stairArrival']))
    assert slab.covers(box(*BEDROOM_ROOF))


def test_g2_stairs_height_spacing_and_lower_stair_headroom(model):
    sp=model['planning']['secondPlan'];steps=[s for s in sp['stairs'] if s['id']!='s2-turn-landing']
    assert len(steps)==20
    assert [steps[0]['top']-H]+[c['top']-a['top'] for a,c in zip(steps,steps[1:])]==pytest.approx([RISE]*20)
    assert steps[-1]['top']==LEVEL
    for st in steps:
        x0,y0,x1,y1=st['bounds']
        assert x1-x0==280
        assert y1-y0==1100
    assert steps[0]['bounds']==[3770,6600,4050,7700]
    assert steps[-1]['bounds']==[3770,7800,4050,8900]
    # Independent analytic check of underside over each retained ground tread.
    clearance=[]
    for i in range(9):
        old_leading_x=1250+i*2200/9
        old_top=1575+(i+1)*175
        new_underside=5262-180+(old_leading_x-1250)/2800*1754
        clearance.append(new_underside-old_top)
    assert min(clearance)==pytest.approx(3157.015873)
    assert sp['minimumAnalyticGroundStairHeadroomMm']==pytest.approx(min(clearance))
    assert all(c['status']=='pass' for c in validate_addition(model))


def test_second_stair_landing_is_enclosed_and_roofed_with_clear_arrival(model):
    sp=model['planning']['secondPlan'];rooms={r['id']:shape(r['regions']) for r in sp['rooms']}
    roof=shape(sp['hallRoof']);outer=box(*HEADHOUSE_OUTER)
    assert roof.covers(outer)
    assert rooms['s2-indoor-landing'].bounds==pytest.approx((4050,6600,5335.6,8900))
    entrance=next(o for o in model['openings'] if o['id']=='s2-hall-entry')
    assert entrance['connects']==['s2-indoor-landing','s2-hall']
    terrace=next(o for o in model['openings'] if o['id']=='s2-stair-terrace-proposed')
    assert terrace['width']==1000 and terrace['connects']==['s2-indoor-landing','s2-terrace']
    top_arrival=LineString([[3900,8350],[4600,8350]]).buffer(450,cap_style=2)
    for a,c in sp['landingGuards']:
        assert LineString([a,c]).buffer(12,cap_style=2).intersection(top_arrival).area<1
    wall=shape(sp['wallRegions'])
    for pts in sp['circulationPaths'].values():
        assert LineString(pts).buffer(400,cap_style=2,join_style=2).intersection(wall).area<1


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
