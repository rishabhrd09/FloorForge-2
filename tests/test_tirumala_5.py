"""Regression checks for the selected Plan A: real geometry, not just labels."""
import json
import math
from pathlib import Path

import pytest
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.tirumala_5 import build_project, KITCHEN, ICU, UTILITY, PANTRY, PANTRY_AISLE

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def model():
    return generate_layout(fuse(build_project()))


def test_plan_a_actual_spaces_counter_and_plot(model):
    spaces={r['id']:r for r in model['spaces']}
    assert model['brief']['width_mm']==12192 and model['brief']['depth_mm']==15240
    for key,bounds in [('g-care',ICU),('g-kitchen',KITCHEN),('g-wash-gully',UTILITY)]:
        assert Polygon(spaces[key]['clear']).symmetric_difference(box(*bounds)).area<1
    assert 'g-kitchen-store' not in spaces
    counter=Polygon(model['planning']['canonicalPlan']['counter'])
    assert counter.bounds==(150,1674,4060,3900)
    assert box(*KITCHEN).covers(counter)
    assert not validate(model)['errors']


def test_plan_a_retains_all_unrequested_rooms_stairs_and_openings(model):
    old=json.loads((ROOT/'examples/gallery/tirumala-4/building.json').read_text())
    before={r['id']:r for r in old['spaces']};after={r['id']:r for r in model['spaces']}
    changed={'g-care','g-kitchen','g-living','g-wash-gully','g-kitchen-store','g-veranda','u-terrace','u-bedroom','u-gallery'}
    for key,r in before.items():
        if key not in changed:
            assert r['clear']==after[key]['clear'],key
    assert old['stairs']==model['stairs'][:len(old['stairs'])]
    p=model['planning']['canonicalPlan'];original=old['planning']['canonicalPlan']
    for key in ('gate','lowerPorch','porchGain','verandaGlass','carBody','carEnvelope'):
        assert p[key]==original[key],key
    ops={o['id']:o for o in p['openings']}
    for o in original['openings']:
        if o['id'] not in ('kitchen-east','store-door','stair-window','icu-east-window','living-veranda','icu-glass-living'): assert ops[o['id']]==o
    assert 'store-door' not in ops
    assert ops['stair-window']['connects']==['g-kitchen','g-stair']


def test_pantry_fits_below_upper_flight_and_aisle_is_clear(model):
    plan=model['planning']['canonicalPlan'];aisle=box(*PANTRY_AISLE)
    pantry=next(f for f in plan['furniture'] if f['kind']=='pantry-cabinet')
    # The added continuous150mm waist follows the unchanged north-flight slope.
    # Use its true underside, rather than the former isolated tread/riser blocks.
    underside=1575+(PANTRY[0]-1250)/2200*1575-150
    centre=1575+((PANTRY[0]+PANTRY[2])/2-1250)/2200*1575-150
    assert underside==pytest.approx(1961.931818)
    assert underside-pantry['heightMm']>160
    assert centre==pytest.approx(2452.902273)
    measured=model['planning']['secondPlan']['pantryClearance']
    assert measured['minimumUnderWaistMm']==pytest.approx(underside)
    assert measured['centreUnderWaistMm']==pytest.approx(centre)
    assert PANTRY_AISLE[3]-PANTRY_AISLE[1]==pytest.approx(914.4)
    for f in plan['furniture']:
        assert aisle.intersection(Polygon(f['polygon'])).area<1,f['id']
    floor=unary_union([Polygon(r['outer'],r.get('holes',[])) for r in plan['openFloor']])
    assert floor.covers(aisle)


def test_utility_fixtures_and_side_access_fit(model):
    p=model['planning']['canonicalPlan'];room=box(*UTILITY)
    fixtures=[Polygon(f['polygon']) for f in p['furniture'] if f['room_id']=='g-wash-gully']
    assert len(fixtures)==3 and all(room.covers(f) for f in fixtures)
    assert all(a.intersection(b).area<1 for i,a in enumerate(fixtures) for b in fixtures[i+1:])
    path=LineString([[2500,550],[600,550]]).buffer(270,cap_style=2)
    assert not any(path.intersection(f).area>1 for f in fixtures)
    walls=unary_union([box(*r) for r in p['wallRects']])
    assert path.intersection(walls).area<1


def test_compiled_scene_and_exports_share_geometry(model):
    scene=json.loads((ROOT/'examples/gallery/tirumala-5/scene.json').read_text())
    assert scene['planHash']==model['planHash']
    assert scene['planA']['icuMm']==ICU
    assert scene['defaultCarVisible'] is False
    assert scene['realismRefinement'] and scene['facadeRefinement']
    room=next(r for r in scene['rooms'] if r['id']=='g-care')
    assert Polygon(room['polygon']).area==pytest.approx(18.6793632)
    motion=scene['door_motion']['icu-glass-living']
    assert motion['layerOrderFromHall']==['wood','glass']
    hob=next(n for n in scene['nodes'] if n['id']=='kitchen-hob')
    assert .15<hob['position'][0]<.75
    assert not any('g-kitchen-store' in f['room_id'] for f in scene['furniture'])


def test_approved_junction_closure_and_door_offsets(model):
    p=model['planning']['canonicalPlan'];ops={o['id']:o for o in p['openings']}
    walls=unary_union([box(*r) for r in p['wallRects']])
    assert walls.covers(box(7375,8050,8200,8200))
    assert ops['living-veranda']['a']==[7300,6100]
    assert ops['living-veranda']['b']==[7300,7900]
    assert ops['icu-glass-living']['a']==[5452.4,5834.6]
    assert ops['icu-glass-living']['b']==[7050,5834.6]
    assert p['glass']['path']==[ops['icu-glass-living']['a'],ops['icu-glass-living']['b']]
    assert p['glass']['stackBounds']==[5312.4,5084.6,5552.4,5684.6]
    assert p['entrance']['woodStacks'][0]==[7380,6000,7830,6090]
    assert walls.intersection(LineString([ops['drawing-veranda-only']['a'],ops['drawing-veranda-only']['b']]).buffer(20,cap_style=2)).area<1
    assert walls.intersection(LineString([ops['lobby-open-entry']['a'],ops['lobby-open-entry']['b']]).buffer(20,cap_style=2)).area<1
    rear=LineString([[6200,7200],[6200,7800],[6450,8150],[6937.5,8550],[7500,9000],[7742.8,9400],[7742.8,10500],[7742.8,11950]]).buffer(300,cap_style=2)
    assert walls.intersection(rear).area<1
    floor=unary_union([Polygon(r['outer'],r.get('holes',[])) for r in p['openFloor']]+[Polygon(r['regions'][0]['outer']) for r in p['rooms']])
    assert rear.difference(floor).area<1


def test_south_head_recliner_and_clear_foot_aisle(model):
    p=model['planning']['canonicalPlan']
    bed=next(f for f in p['furniture'] if f['kind']=='reclining-bed')
    assert bed['bounds']==[5767.6,3204.8,7967.6,4304.8]
    assert bed['headDirection']=='South' and bed['feetDirection']=='North'
    foot=box(7967.6,3204.8,8882,4304.8)
    assert foot.bounds[2]-foot.bounds[0]==pytest.approx(914.4)
    for f in p['furniture']:
        if f['id']!=bed['id']: assert foot.intersection(Polygon(f['polygon'])).area<1
    assert p['utilityPrivacy']['southRectMm']==[0,150,148,1521.6]
    assert p['utilityPrivacy']['heightMm']==1800


def test_lounge_to_dining_and_stairs_has_clear_walking_route(model):
    p=model['planning']['canonicalPlan']
    route=LineString([[5700,7650],[3500,7650],[3500,7950],[1550,7950],[1550,5200]]).buffer(270,cap_style=2)
    for f in p['furniture']:
        assert route.intersection(Polygon(f['polygon'])).area<1,f['id']
    assert route.intersection(unary_union([box(*r) for r in p['wallRects']])).area<1
