"""First-floor-only changes must preserve the occupied ground floor exactly."""
import hashlib
import json
from pathlib import Path
import pytest
from shapely.geometry import Polygon, LineString, box, shape
from shapely.ops import unary_union
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from scripts.build_desired_home import project
from test_desired_home import historic_interior_floor, historic_caregiver_nodes, historic_veranda_items

ROOT=Path(__file__).resolve().parents[1]


def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def test_upper_refinement_preserves_ground_model_finishes_lighting_and_collision():
    before=json.loads((ROOT/'tests/fixtures/desired_home_before_upper_refinement.json').read_text())
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    p=project();b=generate_layout(fuse(p))
    prior=json.loads((ROOT/'tests/fixtures/desired_home_before_caregiver_timber_door.json').read_text())
    ground=p['customPlan']['floors'][0]
    ground={**ground,'openings':[prior['plan_opening'] if o['id']=='g-caregiver-garden-door' else o for o in ground['openings']]}
    assert ground==before['ground_plan']
    b['openings']=[prior['opening'] if o['id']=='g-caregiver-garden-door' else o for o in b['openings']]
    # The later Option A approval removes only veranda overhead cover.
    b['roofs'][0]=json.loads((ROOT/'tests/fixtures/desired_home_before_open_veranda.json').read_text())['ground_roof']
    for key,value in before['ground_building'].items():
        assert digest([x for x in b[key] if x.get('floor')==0])==value
    nodes=[{k:v for k,v in historic_interior_floor(n).items() if k!='id' and not(k=='owner' and v.startswith('object-'))}
           for n in historic_caregiver_nodes(scene) if n['floor'] in (0,-1) and n['role']!='plinth']
    assert digest(sorted(nodes,key=lambda n:json.dumps(n,sort_keys=True)))==before['ground_nodes']
    for key in ('furniture','colliders','vegetation'):
        assert digest([n for n in (historic_veranda_items(scene,key) if key=='colliders' else scene[key]) if n.get('floor') in (0,-1)])==before['ground_'+key]
    restored=sorted([n for n in historic_veranda_items(scene,'lights') if n['position'][2]<3.15],key=lambda n:json.dumps(n,sort_keys=True))
    prior_lights=json.loads((ROOT/'tests/fixtures/desired_home_before_open_veranda.json').read_text())['ground_lights']
    assert restored==sorted(prior_lights,key=lambda n:json.dumps(n,sort_keys=True))
    assert digest(prior_lights)==before['ground_lights']
    assert all(scene['materials'][key]==value for key,value in before['materials'].items())
    # An extra collinear upper-boundary vertex may retriangulate the plinth;
    # compare its actual surface extent and height, not its asset checksum.
    for n,old in zip([n for n in scene['nodes'] if n['role']=='plinth'],before['plinth']):
        mesh=scene['assets'][n['asset']]
        triangles=[Polygon([mesh['vertices'][i][:2] for i in face]) for face in mesh['faces']]
        foot=unary_union([p for p in triangles if p.area>1e-9])
        assert foot.symmetric_difference(shape(old['footprint'])).area<1e-8
        assert [min(v[2] for v in mesh['vertices']),max(v[2] for v in mesh['vertices'])]==old['z']


def test_upper_gallery_guards_storage_and_deck_finishes():
    b=generate_layout(fuse(project()));scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    rooms={r['id']:r for r in b['spaces']}
    assert all(r['finishStyle']=='honed-sandstone' for r in rooms.values() if r['floor']==1 and r['kind'] in ('terrace','balcony'))
    assert not any(n['material']=='glass' for n in scene['nodes'] if n.get('owner')=='u-living-void' and n['role']=='railing')
    assert any(n['material']=='oak' for n in scene['nodes'] if n.get('owner')=='u-living-void' and n['role']=='railing')
    # Both west atrium corners have continuous railing, with no tall wall piers.
    for pt in ((6425,5375),(6425,7275)):
        assert not any(Polygon(w['polygon']).covers(box(pt[0]-1,pt[1]-1,pt[0]+1,pt[1]+1)) for w in b['walls'] if w['floor']==1)
    door=next(o for o in b['openings'] if o['id']=='u-bed-south-door')
    assert door['width']==950 and door['hinge']=='end'
    wardrobe=Polygon(next(f['footprint'] for f in scene['furniture'] if f['id']=='u-bed-south/wardrobe'))
    assert wardrobe.bounds[1]>=10.9
    assert not wardrobe.intersects(box(4.65,8.55,5.59,10.3))
    assert not any(w['id']=='u-balcony-privacy' for w in b['walls'])
    assert rooms['u-garden-daylight']['openToSky']
    assert Polygon(rooms['u-garden-daylight']['clear']).area==6688*2600


@pytest.mark.parametrize('field,value',[('guardStyle','unsupported'),('wardrobeWall','ceiling'),('finishStyle','glossy')])
def test_invalid_upper_finish_options_are_rejected(field,value):
    p=project();r=next(r for r in p['customPlan']['floors'][1]['rooms'] if r['id']=='u-bed-south')
    r[field]=value
    with pytest.raises(DesignError):generate_layout(fuse(p))
