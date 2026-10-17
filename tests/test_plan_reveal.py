"""Plan Reveal: the scroll-driven walkthrough published beside an export, and the two samples built with it."""
import hashlib
import json
import math
from pathlib import Path

import pytest
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from floorforge import plan_reveal
from floorforge.custom_plan import normalize
from floorforge.drawings import INK, plan_elements, primitives
from floorforge.model import DesignError

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / 'examples/gallery'
CATALOG = json.loads((GALLERY / 'catalog.json').read_text(encoding='utf-8'))
REVEALS = [s for s in CATALOG if s.get('hasPlanReveal')]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def packed(folder):
    text = (folder / 'reveal-data.js').read_text(encoding='utf-8')
    prefix = 'window.__PLAN_REVEAL__='
    assert text.startswith(prefix) and text.endswith(';\n')
    return json.loads(text[len(prefix):-2])


@pytest.fixture(scope='module', params=[s['id'] for s in REVEALS])
def sample(request):
    record = next(s for s in REVEALS if s['id'] == request.param)
    folder = ROOT / 'examples' / record['directory']
    data = packed(folder)
    return record, folder, data['scene'], data['reveal']


def test_two_walkthrough_samples_are_in_the_gallery():
    assert {s['id'] for s in REVEALS} == {'aangan-house', 'long-house'}
    assert {s['storeys'] for s in REVEALS} == {1, 2}
    assert all(s['featurePage'] == 'reveal.html' for s in REVEALS)
    assert all((GALLERY / 'thumbnails' / f"{s['id']}.png").stat().st_size > 10000 for s in REVEALS)


def test_page_is_offline_and_files_match_their_manifest(sample):
    record, folder, scene, data = sample
    page = (folder / 'reveal.html').read_text(encoding='utf-8')
    assert 'src="reveal-data.js"' in page and 'src="plan-reveal.js"' in page
    assert 'http://' not in page and 'https://' not in page and 'data:font/woff2;base64,' in page
    manifest = json.loads((folder / 'reveal-manifest.json').read_text(encoding='utf-8'))
    assert manifest['planHash'] == record['planHash'] == data['planHash'] == scene['planHash']
    for name, value in manifest['files'].items():
        assert digest(folder / name) == value, name
    # Digests, not raw bytes: a mismatch must fail fast rather than diff a megabyte bundle.
    assert digest(folder / 'plan-reveal.js') == digest(ROOT / 'web/plan-reveal.js')
    assert scene == json.loads((folder / 'scene.json').read_text(encoding='utf-8'))


def test_sheet_is_the_drawing_set_plan(sample):
    record, folder, scene, data = sample
    b = json.loads((folder / 'building.json').read_text(encoding='utf-8'))
    for sheet in data['sheets']:
        elems, _ = plan_elements(b, scene, sheet['floor'])
        poche = [e for e in primitives(elems) if e['type'] == 'poly' and e['layer'] == 'A-WALL' and e['fill'] == INK]
        assert len(sheet['poche']) == len(poche)
        names = {t[2] for t in sheet['texts']}
        assert {s['name'].upper() for s in b['spaces'] if s['floor'] == sheet['floor'] and s['kind'] not in ('void',)} <= names
        assert sheet['lines'] and sheet['cut'] == 1.2


def test_walk_visits_its_rooms_through_real_openings_with_clearance(sample):
    record, folder, scene, data = sample
    stops, legs = data['tour']['stops'], data['tour']['legs']
    assert stops[0]['kind'] == 'arrival' and len(stops) >= 7 and len(legs) == len(stops) - 1
    rooms = {r['id']: r for r in data['rooms']}
    walls = {}
    for c in scene['colliders']:
        walls.setdefault(c['floor'], []).append(Polygon(c['polygon']))
    for k, leg in enumerate(legs):
        to = stops[leg['to']]
        assert leg['to'] == k + 1 and to['room'] in {e['room'] for e in leg['enters']} | {to['room']}
        solid = unary_union(walls.get(leg['floor'], []))
        pts = [p[:2] for p in leg['points']]
        # The camera never passes closer than 20 cm to a wall or a piece of furniture.
        assert min(solid.distance(Point(*p)) for p in pts) >= .2, (record['id'], k)
        for a, b in zip(pts, pts[1:]):
            assert math.dist(a, b) < .45
        here = Polygon(rooms[to['room']]['polygon'])
        assert here.buffer(.05).contains(Point(*to['stand'][:2])) or math.dist(to['stand'][:2], pts[-1]) < .05
        floor_z = to['floor'] * data['floorHeight']
        assert abs(to['stand'][2] - floor_z - plan_reveal.EYE) < 1e-6


def test_every_presented_room_is_revealed_from_its_doorway(sample):
    record, folder, scene, data = sample
    entered = {e['room']: e for leg in data['tour']['legs'] for e in leg['enters']}
    for stop in data['tour']['stops'][1:]:
        e = entered.get(stop['room'])
        assert e, stop['room']
        room = Polygon(next(r for r in data['rooms'] if r['id'] == stop['room'])['polygon'])
        assert room.buffer(1.3).contains(Point(*e['origin']))
    shapes = {m['id'] for m in data['maskRooms']}
    assert {s['room'] for s in data['tour']['stops'][1:]} <= shapes
    assert len(data['maskOutside']['floors']) >= data['storeys']


def test_room_files_carry_the_measured_room(sample):
    record, folder, scene, data = sample
    for stop in data['tour']['stops'][1:]:
        f = data['files'][stop['room']]
        room = next(r for r in data['rooms'] if r['id'] == stop['room'])
        assert f['area'] == room['area'] > 3
        assert abs(f['sizeFt'][0] - f['size'][0] / .3048) < .06
        assert all(w['faces'] in plan_reveal.COMPASS + ['inner'] for w in f['windows'])


@pytest.mark.parametrize('slug', ['garden-pavilion', 'palm-terrace'])
def test_any_published_home_gets_a_walkthrough(slug, tmp_path):
    folder = GALLERY / slug
    for name in ('building.json', 'scene.json', 'review.json', 'report.json'):
        (tmp_path / name).write_bytes((folder / name).read_bytes())
    page = plan_reveal.publish(tmp_path)
    data = packed(tmp_path)['reveal']
    assert page.name == 'reveal.html' and len(data['tour']['stops']) >= 4
    assert {s['floor'] for s in data['tour']['stops']} == set(range(json.loads((folder / 'building.json').read_text())['storeys']))
    assert data['tour']['legs'][0]['kind'] == 'approach'


def test_reveal_refuses_a_folder_without_an_export(tmp_path):
    with pytest.raises(DesignError):
        plan_reveal.publish(tmp_path)


def test_specimen_tree_is_an_open_courtyard_option():
    room = lambda kind, **extra: dict(id='r', kind=kind, polygon=[[0, 0], [3000, 0], [3000, 3000], [0, 3000]], **extra)
    plan = lambda r: dict(schema='floorforge.custom-plan/1', units='mm', floors=[dict(id='f', rooms=[r], openings=[], walls=[])])
    assert normalize(plan(room('courtyard', centerTree=True)), 1)['floors'][0]['rooms'][0]['centerTree'] is True
    assert normalize(plan(room('courtyard', centerTree='ashoka')), 1)['floors'][0]['rooms'][0]['centerTree'] == 'ashoka'
    for bad in (room('living', centerTree=True), room('courtyard', centerTree=True, glassCover=True), room('courtyard', centerTree='yes'),
                room('courtyard', centerTree=1)):
        with pytest.raises(DesignError):
            normalize(plan(bad), 1)


def test_aangan_has_its_tree_and_the_long_house_its_open_court():
    aangan = json.loads((GALLERY / 'aangan-house/scene.json').read_text(encoding='utf-8'))
    assert any(v['species'] == 'mango' and v['floor'] == 0 for v in aangan['vegetation'])
    assert any(n['id'].endswith('/vrindavan') for n in aangan['nodes']) and any(v['species'] == 'tulsi' for v in aangan['vegetation'])
    long_scene = json.loads((GALLERY / 'long-house/scene.json').read_text(encoding='utf-8'))
    tree = next(v for v in long_scene['vegetation'] if v['species'] == 'ashoka')
    # A narrow court has room for its tree alone: no vrindavan cutting into the planter.
    assert not any(n['id'].endswith('/vrindavan') for n in long_scene['nodes'])
    long_house = json.loads((GALLERY / 'long-house/building.json').read_text(encoding='utf-8'))
    court = Polygon(next(s for s in long_house['spaces'] if s['id'] == 'l-court')['clear'])
    upper = unary_union([Polygon(s['clear']) for s in long_house['spaces'] if s['floor'] == 1])
    assert upper.intersection(court).area < 1 and court.area > 6e6
    assert court.contains(Point(tree['position'][0] * 1000, tree['position'][1] * 1000))
