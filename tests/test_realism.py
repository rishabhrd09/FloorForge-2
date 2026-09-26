"""Realistic walkthrough contract: modern exterior, procedural planting, lawns, rooms and walk metadata."""
from pathlib import Path

import numpy as np
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
    # The visitor arrives on the footpath outside the plot, lined up with the open gate.
    assert x0 <= ax <= x1 and y0 - 1.6 < ay < y0
    floors = {s['floor']: s for s in scene['walk']['floors']}
    assert set(floors) == set(range(building['storeys']))
    fp = Polygon(scene['footprint'])
    for spawn in floors.values():
        assert fp.contains(Point(spawn['position'][:2]))
    # The stair core is real geometry (treads) the walker can climb, not a teleport.
    assert sum(n['role'] == 'stair' for n in scene['nodes']) >= 17


# Roles the viewer's walking capsule passes through (web/viewer/src/scene-builder.js NO_COLLIDE).
NO_COLLIDE = {'curtain', 'rug', 'detail', 'fixture', 'plant-proxy', 'light-glow', 'downlight', 'cove', 'art', 'decor', 'blind', 'lamp'}


def _solids(scene):
    """World bounding boxes (lo, hi) of every solid that blocks or carries the walking capsule."""
    out = []
    for n in scene['nodes']:
        asset = scene['assets'][n['asset']]
        if n['role'] in NO_COLLIDE or asset.get('closed') is False:
            continue
        rx, ry, rz = n['rotation']
        cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
        R = np.array([[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx], [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx], [-sy, cy * sx, cy * cx]])
        v = (np.array(asset['vertices']) * n['scale']) @ R.T + n['position']
        out.append((n['id'] + ':' + n['role'], v.min(0), v.max(0)))
    return out


def _obstacles(solids, lo, hi):
    """Solids that reach into the axis-aligned box lo..hi (metres, Z up)."""
    return [name for name, a, b in solids if (a < hi).all() and (b > lo).all()]


def _tops(solids, ground, x, y):
    """Heights a foot can stand on at (x, y): the terrain and the top of every solid there."""
    return [ground] + [b[2] for _, a, b in solids if a[0] <= x <= b[0] and a[1] <= y <= b[1]]


@pytest.mark.parametrize('theme', EXTERIOR_THEME_IDS)
@pytest.mark.parametrize('case', ['villa', 'small', 'parking'])
def test_walk_arrival_leads_through_an_open_gateway(theme, case):
    brief = {'parking': True, 'front_mm': 6000, 'depth_mm': 21000} if case == 'parking' else CASES[case]
    _, _, scene = build({**brief, 'exterior_theme': theme})
    x0, y0, g = scene['bounds'][:3]
    ax, ay, _ = scene['walk']['arrival']['position']
    solids = _solids(scene)
    # Nothing above step height stands in the capsule's path from the footpath through the gate and up to
    # the front door, and each rise along the way is one the walker climbs in practice: its capsule
    # (web/viewer/src/walker.js, radius .27 m, raised by the .38 m step offset) is held back by an edge
    # much above .3 m before the ground probe reaches it.
    ex = scene['entry'][0]
    assert not _obstacles(solids, (ax - .3, ay - .3, g + .45), (ax + .3, y0 + .5, g + 1.85))
    assert not _obstacles(solids, (ex - .3, y0 + .5, .45), (ex + .3, -.4, 1.85))
    level = g
    for y in np.arange(ay, .3, .05):
        x = ex if y > y0 + .5 else ax
        if y < -.3:
            blocking = [name for name, a, b in solids if a[0] <= x <= b[0] and a[1] <= y <= b[1] and b[2] > level + .3 and a[2] < level + 1.7]
            assert not blocking, f'a {blocking[0]} edge too high to step onto at y={y:.2f}'
        level = max(t for t in _tops(solids, g, x, y) if t <= level + .3)
    assert level > -.02, 'the walk does not reach the ground floor through the front door'


@pytest.mark.parametrize('theme', EXTERIOR_THEME_IDS)
def test_windows_use_the_refined_system(theme):
    building, _, scene = build({'exterior_theme': theme})
    kinds = {s['id']: s['kind'] for s in building['spaces']}
    walls = {w['id']: w for w in building['walls']}
    windows = {o['id']: o for o in building['openings'] if o['kind'] == 'window'}
    parts = [n for n in scene['nodes'] if n.get('owner') in windows]
    # Slim frames and sills, no heavy projecting shades.
    assert not any(n['role'] == 'shade' for n in parts)
    assert all(n['scale'][1] <= .15 for n in parts if n['role'] == 'sill')
    # Wet rooms get obscured glass, habitable rooms clear glass.
    for oid, o in windows.items():
        wet = any(kinds.get(r) in ('bathroom', 'utility') for r in walls[o['wall_id']]['rooms'])
        panes = {n['material'] for n in parts if n['owner'] == oid and n['role'] == 'glass'}
        assert panes == ({'frosted'} if wet else {'glass'}), oid
    # Bedroom glazing on the facade sits in a slim projecting pod.
    pods = [n for n in parts if n['role'] == 'window-surround']
    assert pods and all(min(n['scale'][0], n['scale'][2]) <= .05 for n in pods)


@pytest.mark.parametrize('theme', [t for t in EXTERIOR_THEME_IDS if t != 'current'])
def test_terrace_sits_at_the_first_floor_with_rail_and_pergola(theme):
    _, _, scene = build({'exterior_theme': theme})
    H = scene['floor_height']
    deck = next(n for n in scene['nodes'] if n['id'] == 'exterior-balcony-01-deck')
    # Level with the first floor it opens from, never up on the roof.
    assert abs(deck['position'][2] + deck['scale'][2] / 2 - H) < .03
    terrace = [n for n in scene['nodes'] if n.get('owner') == 'exterior-balcony-01']
    assert any(n['material'] == 'railglass' for n in terrace)
    assert any(n['role'] == 'pergola' for n in terrace)
    top = H * scene['storeys']
    assert all(n['position'][2] + n['scale'][2] / 2 < top for n in terrace)


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
    assert 'Blender GLB' in page and 'exportPresentation' in page
    # Large view and zoom for exploring the home in big size, and a large still.
    assert 'Large view' in page and 'v.zoom(' in page and 'snapshot({width:3840})' in page


def test_studio_offers_large_view_zoom_and_large_stills():
    html = (ROOT / 'web/index.html').read_text('utf8')
    app = (ROOT / 'web/app.js').read_text('utf8')
    bundle = (ROOT / 'web/viewer.js').read_text('utf8')
    for control in ('id="fullscreen"', 'Large view', 'id="zoom-in"', 'id="zoom-out"', 'id="sheet-zoom-in"', 'id="sheet-large"'):
        assert control in html, control
    assert 'setLargeView' in app and 'snapshot({width:3840})' in app and 'zoomSheet' in app
    # The viewer glides the camera for zoom, zooms to a double-clicked spot and renders large stills.
    assert 'zoomToPoint' in bundle and 'stepZoom' in bundle


def test_bundled_viewer_is_present_and_attributed():
    bundle = (ROOT / 'web/viewer.js').read_text('utf8')
    assert len(bundle) > 400_000
    assert 'FloorForgeViewer' in bundle
    assert 'SPDX-License-Identifier: MIT' in bundle and '@license Zlib' in bundle
    for package in ('three', 'three-mesh-bvh', 'postprocessing', 'n8ao'):
        assert any((ROOT / 'licenses/viewer-js' / package).iterdir())


def test_walls_tile_each_storey_without_overlapping_solids(modern):
    # Overlapping wall solids leave coincident faces that path tracers shade black; walls must tile instead.
    from shapely.ops import unary_union
    _, _, scene = modern
    H = scene['floor_height']
    for f in range(scene['storeys']):
        z = f * H + .2
        pieces = []
        for n in scene['nodes']:
            if n['role'] != 'wall' or n['floor'] != f:
                continue
            asset = scene['assets'][n['asset']]
            v = asset['vertices']
            zs = [p[2] for p in v]
            if not (min(zs) <= z <= max(zs)):
                continue
            top = max(zs)
            tris = [Polygon([v[i][:2] for i in face]) for face in asset['faces'] if all(abs(v[i][2] - top) < 1e-6 for i in face)]
            pieces.append(unary_union([t for t in tris if t.area > 0]))
        assert pieces
        assert sum(q.area for q in pieces) == pytest.approx(unary_union(pieces).area, abs=1e-3)


def test_offline_render_path_is_present():
    bundle = (ROOT / 'web/viewer.js').read_text('utf8')
    assert 'exportPresentation' in bundle
    for script in ('scripts/render_cycles.py', 'scripts/blender_scene.py'):
        compile((ROOT / script).read_text('utf8'), script, 'exec')

