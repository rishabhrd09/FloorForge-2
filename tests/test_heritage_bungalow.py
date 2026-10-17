"""The Bungalow sample: an opt-in heritage facade style that leaves every other plan untouched."""
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest
from shapely.geometry import Point, Polygon

from floorforge.exterior import apply_exterior_preferences
from floorforge.heritage_bungalow import FLOOR_FINISHES, HERITAGE, WALL_PAINTS
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from floorforge.review import solar_position
from floorforge.scene import make_scene
from scripts.build_bungalow import TITLE, project

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def bungalow():
    p = project()
    b = apply_exterior_preferences(generate_layout(fuse(p)))
    return p, b, make_scene(b, {'solar': solar_position(b['brief'])})


def plan_error(mutate):
    p = project()
    mutate(p['customPlan'])
    with pytest.raises(DesignError) as err:
        generate_layout(fuse(p))
    return {e['code'] for e in (err.value.details or {}).get('errors', [])} or {err.value.code}


def test_plan_is_a_large_two_storey_bungalow_that_validates():
    from floorforge.review import validate
    p = project()
    b = generate_layout(fuse(p))
    review = validate(b)
    assert not review.get('errors')
    assert b['brief']['title'] == TITLE and b['storeys'] == 2 and b['rooftop']
    assert b['planning']['facadeStyle'] == HERITAGE
    rooms = {s['id']: s for s in b['spaces']}
    # Large rooms: a drawing hall over 45 m2, a dining hall over 35 m2 and four bedrooms with attached baths.
    assert rooms['g-drawing']['area_m2'] > 45 and rooms['g-dining']['area_m2'] > 35
    assert sum(s['kind'] == 'bedroom' for s in b['spaces']) == 4
    assert b['brief']['floor_height_mm'] == 3600
    # Distemper colours and period floor finishes travel from the plan to the building.
    assert rooms['g-drawing']['wallPaint'] == 'sky-blue' and rooms['g-drawing']['floorFinish'] == 'white-marble'
    assert all(s.get('wallPaint', 'ivory') in WALL_PAINTS and s.get('floorFinish', 'mosaic') in FLOOR_FINISHES for s in b['spaces'])
    assert {o['id'] for o in b['openings'] if o.get('grille')} >= {'g-entry', 'g-verandah-carport', 'g-verandah-front-west'}


@pytest.mark.parametrize('mutate,code', [
    (lambda c: c.update(facadeStyle='plain'), 'WALL_PAINT'),
    (lambda c: c.update(facadeStyle='heritage'), 'FACADE_STYLE'),
    (lambda c: c['floors'][0]['rooms'][0].update(wallPaint='neon'), 'WALL_PAINT'),
    (lambda c: c['floors'][0]['rooms'][0].update(floorFinish='carpet'), 'FLOOR_FINISH'),
    (lambda c: c['floors'][0]['openings'][0].update(grille='yes'), 'GRILLE'),
    (lambda c: c['floors'][0]['openings'][6].update(grille=True), 'GRILLE'),
])
def test_heritage_finishes_are_opt_in_and_validated(mutate, code):
    assert code in plan_error(mutate)


def test_exterior_proposal_keeps_to_the_plot_and_off_the_house(bungalow):
    _, b, _ = bungalow
    ex = b['exterior']
    assert not ex.get('rejections')
    kinds = Counter(a['geometry']['kind'] for a in ex['assemblies'])
    assert kinds == Counter({'sheet_carport': 1, 'sheet_canopy': 1, 'chick_pergola': 1, 'water_tank': 1, 'desert_cooler': 2})
    plot = Polygon(b['plot'])
    house = Polygon(b['footprint'])
    features = ex['landscape']['features']
    counts = Counter(f['kind'] for f in features)
    for kind in ('lawn', 'tree', 'pot', 'hedge', 'hex_paving', 'flower_bed', 'entry_steps', 'rose_fence', 'tulsi', 'jhoola', 'kitchen_garden'):
        assert counts[kind], kind
    for f in features:
        shape = Polygon(f['polygon']) if 'polygon' in f else Point(*f['position_mm']) if 'position_mm' in f else None
        if shape is None:
            continue
        assert plot.buffer(1).covers(shape), f['id']
        if f['kind'] != 'entry_steps':
            assert shape.intersection(house).area < 1 and not (shape.geom_type == 'Point' and house.contains(shape)), f['id']
    # Every outside door is reached by plinth steps; the main entry has cheek walls.
    steps = {f['opening_id']: f for f in features if f['kind'] == 'entry_steps'}
    assert steps['g-entry']['main'] and steps['g-entry']['cheeks']
    assert {'g-verandah-carport', 'g-rear-verandah-edge', 'g-wash-edge'} <= set(steps)
    gates = {g['kind'] for g in ex['landscape']['boundary']['gates']}
    assert gates == {'pedestrian', 'vehicle'}


def test_scene_furnishes_every_room_in_the_period(bungalow):
    _, b, scene = bungalow
    assert scene['context'] == {'style': 'colony'}
    items = {f['id'] for f in scene['furniture']}
    for expected in ('g-drawing/sofa', 'g-drawing/diwan', 'g-drawing/showcase', 'g-dining/dining-set', 'g-office/officer-desk',
                     'g-master/bed', 'g-guest/bed', 'f-bed3/bed', 'f-bed4/bed', 'g-master/almirah', 'f-lounge/carrom',
                     'g-rear-verandah/jhoola', 'f-front-terrace/pergola-seating', 'f-front-terrace/charpai', 'g-kitchen/kitchen-run'):
        assert expected in items, expected
    # Furniture stays inside its own room, and ids are unique.
    rooms = {s['id']: Polygon(s['clear']).buffer(30) for s in b['spaces']}
    assert len(items) == len(scene['furniture'])
    for f in scene['furniture']:
        assert rooms[f['room_id']].covers(Polygon([[x * 1000, y * 1000] for x, y in f['footprint']])), f['id']
    assert len({e['id'] for e in scene['editables']}) == len(scene['editables'])
    # Ceiling fans in the halls and bedrooms; painted rooms carry their own distemper.
    roles = Counter(n['material'] for n in scene['nodes'])
    assert roles['hb-fan'] >= 30 and roles['paint-sky-blue'] and roles['paint-peach'] and roles['floor-white-marble']
    species = {v['species'] for v in scene['vegetation']}
    assert {'neem', 'mango', 'ashoka', 'araucaria', 'areca', 'rose_bush', 'flower_clump', 'climber', 'tulsi', 'croton', 'bougainvillea'} <= species
    assert scene['gate_model'][0]['id'] == 'exterior-vehicle-gate'
    assert {'g-drawing-main', 'g-dining-verandah', 'f-lounge-terrace', 'f-stair-terrace'} <= set(scene['door_motion'])


def test_scene_wall_linings_never_cover_an_opening(bungalow):
    # Distemper linings are cut at every door, window and arch at their own heights.
    from shapely.affinity import scale
    from shapely.ops import unary_union
    from floorforge.scene import opening_polygon
    _, b, scene = bungalow
    H = scene['floor_height']
    linings = []
    for n in scene['nodes']:
        if n['role'] != 'wall-panel' or not n['material'].startswith('paint-') or n['scale'] != [1, 1, 1] or n['rotation'] != [0, 0, 0]:
            continue
        asset = scene['assets'][n['asset']]
        v = asset['vertices']
        top = max(p[2] for p in v)
        tris = [Polygon([v[i][:2] for i in face]) for face in asset['faces'] if all(abs(v[i][2] - top) < 1e-6 for i in face)]
        linings.append((n['floor'], min(p[2] for p in v), top, unary_union([t for t in tris if t.area > 0])))
    assert len(linings) > 100
    hosts = {w['id']: w for w in b['walls']}
    for o in b['openings']:
        aperture = scale(opening_polygon(hosts[o['wall_id']], o), .001, .001, origin=(0, 0))
        mid = o['floor'] * H + (o['sill'] + o['height'] / 2) / 1000
        for floor, z0, z1, shape in linings:
            if floor == o['floor'] and z0 < mid < z1:
                assert shape.intersection(aperture).area < 1e-4, o['id']


def test_other_plans_and_themes_are_untouched():
    p = project()
    p['customPlan']['facadeStyle'] = 'plain'
    for floor in p['customPlan']['floors']:
        for r in floor['rooms']:
            r.pop('wallPaint', None)
            r.pop('floorFinish', None)
        for o in floor['openings']:
            o.pop('grille', None)
    b = apply_exterior_preferences(generate_layout(fuse(p)))
    assert not any(a['geometry'].get('kind') in ('sheet_carport', 'chick_pergola', 'water_tank') for a in b['exterior']['assemblies'])
    scene = make_scene(b, {'solar': solar_position(b['brief'])})
    assert 'context' not in scene and not any(n['material'].startswith(('hb-', 'paint-')) for n in scene['nodes'])
    assert not any(v['species'] in ('neem', 'mango', 'ashoka') for v in scene['vegetation'])


def test_published_sample_is_catalogued():
    catalog = json.loads((ROOT / 'examples/gallery/catalog.json').read_text(encoding='utf-8'))
    entry = next(s for s in catalog if s['id'] == 'bungalow')
    assert entry['title'] == TITLE and entry['style'] == 'Heritage Bungalow' and entry['hasSpecifications']
    assert (entry['widthFt'], entry['depthFt'], entry['bedrooms'], entry['storeys']) == (100, 130, 4, 2)
    folder = ROOT / 'examples' / entry['directory']
    assert (ROOT / 'examples/gallery/thumbnails/bungalow.png').stat().st_size > 50_000
    scene = json.loads((folder / 'scene.json').read_text(encoding='utf-8'))
    assert scene['planHash'] == entry['planHash'] and scene['context'] == {'style': 'colony'}
    page = (folder / 'preview.html').read_text(encoding='utf-8')
    assert 'Heritage Bungalow' in page and 'gardenLeaves' in page
    guide = (folder / 'DESIGN_GUIDE.md').read_text(encoding='utf-8')
    assert guide.startswith('# ' + TITLE) and entry['planHash'] in guide


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js unavailable')
def test_viewer_grows_every_heritage_species():
    module = (ROOT / 'web/viewer/src/plant-builders.js').as_uri()
    script = """
import { buildSpecies } from '%s';
const out = {};
for (const [name, opts] of [['neem', {}], ['mango', {}], ['ashoka', {}], ['araucaria', {}], ['areca', {}], ['rose_bush', {color: 'pink'}],
    ['flower_clump', {color: 'marigold'}], ['amaryllis', {}], ['croton', {leaf: 'poinsettia'}], ['climber', {length: 2, height: 2, flowers: 'white'}],
    ['bougainvillea', {bracts: 'white'}], ['tulsi', {}], ['vegetable', {kind: 'leafy'}], ['vegetable', {kind: 'tomato'}], ['hedge', {size: [3, .5, .6], flowers: 'white'}]]) {
  const s = buildSpecies(name, 7, opts);
  let tris = 0;
  for (const g of Object.values(s.parts)) if (g) tris += g.index.count / 3;
  out[name + (opts.kind || '')] = { height: s.height, tris, leaf: s.leafAtlas, flower: s.flowerAtlas || null, parts: Object.keys(s.parts) };
}
console.log(JSON.stringify(out));
""" % module
    res = subprocess.run(['node', '--input-type=module', '-e', script], capture_output=True, text=True, timeout=120, cwd=ROOT / 'web/viewer')
    assert res.returncode == 0, res.stderr
    grown = json.loads(res.stdout)
    for name, s in grown.items():
        assert s['tris'] > 50 and 0 < s['height'] < 12, name
        assert s['tris'] < 40_000, name
    assert grown['neem']['height'] > 8 and grown['ashoka']['leaf'] == 'gardenLeaves'
    assert grown['hedge']['flower'] == 'gardenFlowers' and 'flowers' in grown['rose_bush']['parts']
