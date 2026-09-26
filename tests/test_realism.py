"""Realistic walkthrough contract: modern exterior, procedural planting, lawns, rooms and walk metadata."""
from pathlib import Path

import pytest
from shapely.geometry import Polygon, Point, box

from floorforge.exterior import EXTERIOR_THEME_IDS, apply_exterior_preferences
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import reports, validate
from floorforge.scene import make_scene
from floorforge.pipeline import preview_html
from floorforge.drawings import make_sheets, svg_sheet
from conftest import CASES

ROOT = Path(__file__).resolve().parents[1]


def build(brief=None, schema='floorforge.project/0.3'):
    building = apply_exterior_preferences(generate_layout(fuse({'schema': schema, 'brief': brief or {}})))
    report = reports(building, validate(building))
    return building, report, make_scene(building, report)


@pytest.fixture(scope='module')
def modern():
    return build()


def test_new_projects_default_to_modern_tropical(modern):
    building, _, scene = modern
    assert building['exterior']['theme'] == 'modern_tropical'
    assert scene['schema'] == 'floorforge.scene/0.4'
    assert scene['exterior_theme'] == 'modern_tropical' and scene['interior_theme'] == 'bright_natural'


def test_modern_glazing_is_full_height_in_living_rooms(modern):
    building, _, _ = modern
    kinds = {s['id']: s['kind'] for s in building['spaces']}
    living_windows = [o for o in building['openings'] if o['kind'] == 'window' and any(kinds.get(r) in ('living', 'family', 'dining') for r in o['connects'])]
    assert living_windows and any(o['sill'] == 0 and o['height'] >= 2500 for o in living_windows)
    walls = {w['id']: w for w in building['walls']}
    for o in building['openings']:
        assert o['sill'] + o['height'] <= walls[o['wall_id']]['height']


@pytest.mark.parametrize('case', list(CASES))
def test_modern_landscape_stays_in_plot_and_off_the_house(case):
    building, _, scene = build(CASES[case])
    plot = Polygon(building['plot'])
    house = Polygon(building['footprint'])
    features = building['exterior']['landscape']['features']
    assert features
    for f in features:
        if 'polygon' in f:
            p = Polygon(f['polygon'])
            assert plot.covers(p), f['id']
            assert p.intersection(house).area < 1, f['id']
        for stone in f.get('stones', []):
            assert plot.covers(Polygon(stone)) and Polygon(stone).intersection(house).area < 1, f['id']
        if 'position_mm' in f and f['kind'] != 'wall_light':
            assert plot.covers(Point(f['position_mm'])), f['id']
    kinds = {f['kind'] for f in features}
    assert 'court' in kinds and 'pebble_bed' in kinds


@pytest.mark.parametrize('case', list(CASES))
def test_procedural_planting_and_lawns_are_on_site(case):
    building, _, scene = build(CASES[case])
    plot = Polygon([[x / 1000, y / 1000] for x, y in building['plot']])
    house = Polygon(scene['footprint'])
    assert scene['vegetation']
    for item in scene['vegetation']:
        x, y, z = item['position']
        assert item['species'] and item['scale'] > 0
        assert plot.buffer(.01).covers(Point(x, y)), item['id']
        if item['floor'] == -1 and z < 0:
            assert not house.buffer(-.05).contains(Point(x, y)), item['id']
    for lawn in scene['lawns']:
        p = Polygon(lawn['polygon'])
        assert plot.buffer(.01).covers(p)
        assert p.intersection(house).area < .05
    # Every planted instance has a coordination proxy for GLB/drawings.
    assert sum(n['role'] == 'plant-proxy' for n in scene['nodes']) >= len(scene['vegetation'])


def test_rooms_and_walk_metadata_support_first_person_navigation(modern):
    building, _, scene = modern
    assert len(scene['rooms']) == len(building['spaces'])
    [x0, y0, _, x1, y1, _] = scene['bounds']
    ax, ay, _ = scene['walk']['arrival']['position']
    assert x0 <= ax <= x1 and y0 <= ay <= y1
    floors = {s['floor']: s for s in scene['walk']['floors']}
    assert set(floors) == set(range(building['storeys']))
    fp = Polygon(scene['footprint'])
    for spawn in floors.values():
        assert fp.contains(Point(spawn['position'][:2]))
    # The stair core is real geometry (treads) the walker can climb, not a teleport.
    assert sum(n['role'] == 'stair' for n in scene['nodes']) >= 17


def test_surfaces_declare_physically_based_kinds(modern):
    _, _, scene = modern
    used = {n['material'] for n in scene['nodes']}
    for name in used:
        m = scene['materials'][name]
        assert 'color' in m and 'roughness' in m
        if name in ('wall', 'floor', 'woodfloor', 'cobble', 'pebble', 'lawn', 'deck', 'counter', 'cladding'):
            assert m.get('kind'), name


def test_interior_upgrades_keep_furniture_inside_rooms(modern):
    building, _, scene = modern
    rooms = {s['id']: Polygon([[x / 1000, y / 1000] for x, y in s['clear']]) for s in building['spaces']}
    from shapely.ops import unary_union
    for space in building['spaces']:
        if space['kind'] in ('living', 'dining'):
            rooms[space['id']] = unary_union([Polygon([[x / 1000, y / 1000] for x, y in s['clear']]) for s in building['spaces'] if s['floor'] == space['floor'] and s['kind'] in ('living', 'dining')])
    for item in scene['furniture']:
        assert rooms[item['room_id']].buffer(.015).covers(Polygon(item['footprint'])), item['id']
    roles = {n['role'] for n in scene['nodes']}
    assert {'skirting', 'downlight', 'ceiling'} <= roles


@pytest.mark.parametrize('theme', EXTERIOR_THEME_IDS)
def test_every_theme_publishes_planting_for_the_viewer(theme):
    _, _, scene = build({'exterior_theme': theme})
    assert scene['vegetation'] or scene['lawns']


def test_preview_embeds_viewer_without_breaking_script_blocks(modern):
    building, report, scene = modern
    sheets = make_sheets(building, scene, report)
    page = preview_html(scene, building, svg_sheet(sheets[0], building))
    assert page.count('</script>') == 3
    assert 'FloorForgeViewer' in page and 'Walk in' in page


def test_bundled_viewer_is_present_and_attributed():
    bundle = (ROOT / 'web/viewer.js').read_text('utf8')
    assert len(bundle) > 400_000
    assert 'FloorForgeViewer' in bundle
    assert 'SPDX-License-Identifier: MIT' in bundle and '@license Zlib' in bundle
    for package in ('three', 'three-mesh-bvh', 'postprocessing', 'n8ao'):
        assert any((ROOT / 'licenses/viewer-js' / package).iterdir())
