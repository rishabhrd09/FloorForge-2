"""Realistic walkthrough contract: modern exterior, procedural planting, lawns, rooms and walk metadata."""
import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import LineString, Polygon, Point, box

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


@pytest.mark.parametrize('theme', [t for t in EXTERIOR_THEME_IDS if t != 'current'])
@pytest.mark.parametrize('case', ['villa', 'compact', 'small', 'parking'])
def test_frontage_has_separate_pedestrian_and_vehicle_gates(theme, case):
    # A real compound wall, not a centred gate with equal walls either side: a pedestrian gate on the path to
    # the door, a separate sliding vehicle gate over the parking pad (or the carport), a letterbox pier.
    brief = {'parking': True, 'front_mm': 6000, 'depth_mm': 21000} if case == 'parking' else CASES[case]
    building, _, scene = build({**brief, 'exterior_theme': theme})
    boundary = building['exterior']['landscape']['boundary']
    xmin, ymin, xmax, _ = Polygon(building['plot']).bounds
    gates = {g['kind']: g for g in boundary['gates']}
    ped, vehicle = gates['pedestrian'], gates.get('vehicle')
    assert ped['operation'] == 'swing' and 900 <= ped['x1_mm'] - ped['x0_mm'] <= 1300
    assert boundary['gate_center_mm'] == round((ped['x0_mm'] + ped['x1_mm']) / 2)
    pier = boundary['letterbox_pier']
    assert pier['x1_mm'] == ped['x0_mm'] or pier['x0_mm'] == ped['x1_mm']
    ex = scene['entry'][0] * 1000
    assemblies = {a['geometry'].get('kind'): a for a in building['exterior']['assemblies']}
    carport = next((a for a in building['exterior']['assemblies'] if a['geometry'].get('kind') == 'carport'), None)
    if not carport:
        assert ped['x0_mm'] <= ex <= ped['x1_mm'], 'the pedestrian gate lines up with the front door'
    # A vehicle gate wherever 2.4 m of frontage is clear of the entrance porch (a deep verandah across a small
    # plot leaves no pad for one).
    free = LineString([(xmin + 450, 0), (xmax - 450, 0)])
    for a, b2 in [(pier['x0_mm'], pier['x1_mm']), (ped['x0_mm'], ped['x1_mm'])] + \
            ([tuple(assemblies['porch']['geometry']['bounds_mm'][0::2])] if 'porch' in assemblies else []):
        free = free.difference(box(a - 150, -1, b2 + 150, 1))
    room = max((g.length for g in getattr(free, 'geoms', [free])), default=0)
    if room < 2400 and not carport:
        assert vehicle is None
        return
    assert vehicle, 'a vehicle gate beside the pedestrian gate'
    assert vehicle['operation'] == 'sliding' and vehicle['x1_mm'] - vehicle['x0_mm'] >= 2400
    spans = sorted([(ped['x0_mm'], ped['x1_mm']), (vehicle['x0_mm'], vehicle['x1_mm']), (pier['x0_mm'], pier['x1_mm'])])
    assert all(a[1] <= b[0] for a, b in zip(spans, spans[1:])), 'gates and pier do not overlap'
    assert xmin < spans[0][0] and spans[-1][1] < xmax
    if carport:
        c0, _, c1, _ = carport['geometry']['bounds_mm']
        assert vehicle['x0_mm'] <= (c0 + c1) / 2 <= vehicle['x1_mm'], 'the vehicle gate serves the carport'
    elif 'porch' in assemblies:
        p0, _, p1, _ = assemblies['porch']['geometry']['bounds_mm']
        assert vehicle['x1_mm'] <= p0 or vehicle['x0_mm'] >= p1, 'the drive keeps clear of the entrance steps'
    names = {n['id'] for n in scene['nodes']}
    assert {'exterior-letterbox-pier', 'house-number-plate', 'exterior-vehicle-gate', 'exterior-gate-sill'} <= names
    # The pedestrian leaf stands open (its parts are turned off the wall line); the vehicle leaf is closed.
    leaf = [n for n in scene['nodes'] if n.get('owner') == 'exterior-pedestrian-gate' and n['role'] == 'gate' and n['material'] == 'frame']
    assert leaf and all(abs(math.sin(n['rotation'][2])) > .95 for n in leaf)


def test_modern_entrance_is_an_l_shaped_porch_with_a_tall_pivot_door(modern):
    building, _, scene = modern
    porch = next(a for a in building['exterior']['assemblies'] if a['geometry'].get('kind') == 'porch')
    geo = porch['geometry']
    assert geo['flight_side'] in ('left', 'right') and geo['return_steps_mm'] >= 600 and geo['sitout_x_mm']
    nodes = {n['id']: n for n in scene['nodes']}
    aid = porch['id']
    # Steps across the door end of the landing that return down its side (an L in plan), a sit-out with a
    # stone-clad column, planter and bench at the other end.
    for part in ('-step-0', '-step-1', '-return-0', '-return-1', '-column', '-sitout-planter', '-bench-plinth'):
        assert aid + part in nodes, part
    assert nodes[aid + '-column']['material'] == 'cladding'
    front, ret = nodes[aid + '-step-0'], nodes[aid + '-return-0']
    x0, _, x1, _ = [q / 1000 for q in geo['bounds_mm']]
    rx = ret['position'][0]
    assert (rx < x0) if geo['flight_side'] == 'left' else (rx > x1)
    assert ret['scale'][1] > .5 and front['scale'][0] > 1.5
    # Every tread carries an LED strip under its nosing.
    strips = [n for n in scene['nodes'] if n.get('owner') == aid and n['material'] == 'lamp' and n['role'] == 'fixture']
    assert len(strips) >= 4
    # A tall pivot door in a black steel portal, its head in line with the full-height glazing.
    entry = next(o for o in building['openings'] if o['kind'] == 'entry')
    assert entry['height'] >= 2500
    portal = [n for n in scene['nodes'] if n.get('owner') == entry['id'] and n['role'] == 'door-portal']
    assert len(portal) == 3 and all(n['material'] == 'frame' for n in portal)
    leaf = [n for n in scene['nodes'] if n.get('owner') == entry['id'] and n['role'] == 'door' and n['material'] == 'walnut']
    heights = [np.ptp(np.array(scene['assets'][n['asset']]['vertices'])[:, 2]) * n['scale'][2] for n in leaf]
    assert leaf and max(heights) >= 2.4


@pytest.mark.parametrize('case', ['villa', 'compact'])
def test_modern_massing_has_a_deep_eave_and_a_finished_roof(case):
    building, _, scene = build(CASES[case])
    top = scene['storeys'] * scene['floor_height']
    nodes = scene['nodes']
    by_id = {n['id']: n for n in nodes}
    # A deep street-side eave with a timber-slat soffit and downlights.
    eave = by_id['roof-overhang']
    ys = np.array(scene['assets'][eave['asset']]['vertices'])[:, 1]
    assert ys.min() <= -.95
    def zmid(n):
        z = np.array(scene['assets'][n['asset']]['vertices'])[:, 2] * n['scale'][2] + n['position'][2]
        return (z.min() + z.max()) / 2
    assert sum(n['role'] == 'soffit' and n['material'] == 'timber' and zmid(n) > top - .3 for n in nodes) >= 20
    assert any(n['role'] == 'downlight' and zmid(n) > top - .3 for n in nodes)
    # Photovoltaic modules on a rack.
    assert sum(n['material'] == 'solar' for n in nodes) >= 4
    tower = next((a for a in building['exterior']['assemblies'] if a['geometry'].get('kind') == 'stair_tower'), None)
    if scene['storeys'] > 1:
        # The stair rises into a stone-clad tower beside an open roof terrace with a glass balustrade.
        assert tower
        body = by_id[tower['id'] + '-body']
        assert body['position'][2] + body['scale'][2] / 2 >= top + 2.4
        assert any(n['id'].startswith(tower['id'] + '-cladding') and n['material'] == 'cladding' for n in nodes)
        assert 'roof-terrace-pavers' in by_id
        assert sum(n['material'] == 'railglass' and zmid(n) > top for n in nodes) >= 1
        roof_items = [v for v in scene['vegetation'] if v['position'][2] > top]
        assert all(v['floor'] == scene['storeys'] for v in roof_items)
    else:
        assert tower is None and 'roof-gravel' in by_id


@pytest.mark.parametrize('theme', EXTERIOR_THEME_IDS)
def test_every_designed_theme_raises_a_stair_tower_and_solar_roof(theme):
    building, _, scene = build({'exterior_theme': theme})
    tower = [a for a in building['exterior']['assemblies'] if a['geometry'].get('kind') == 'stair_tower']
    solar = [n for n in scene['nodes'] if n['material'] == 'solar']
    if theme == 'current':
        # The preserved facade stays exactly as it was.
        assert not tower and not solar
        return
    assert len(tower) == 1 and len(solar) >= 4
    stair = next(s for s in building['spaces'] if s['floor'] == building['storeys'] - 1 and s['kind'] == 'stair')
    assert Polygon(stair['polygon']).equals(box(*tower[0]['geometry']['bounds_mm']))
    # Solar modules sit on the roof, inside the footprint.
    fp = Polygon(scene['footprint'])
    top = scene['storeys'] * scene['floor_height']
    assert all(fp.contains(Point(n['position'][:2])) and n['position'][2] > top for n in solar)


@pytest.mark.parametrize('case', list(CASES))
def test_side_passages_are_paved_and_the_boundary_is_clad_in_timber(case):
    building, _, scene = build(CASES[case])
    features = {f['id']: f for f in building['exterior']['landscape']['features']}
    v = building['brief']
    for side, gap in (('left', v['left_mm']), ('right', v['right_mm'])):
        if gap < 700:
            assert f'{side}-fence-cladding' not in features
            continue
        fence = features[f'{side}-fence-cladding']
        boards = [n for n in scene['nodes'] if n.get('owner') == fence['id'] and n['material'] == 'timber']
        assert len(boards) >= 8 and all(n['scale'][1] > 5 for n in boards), 'horizontal boards the length of the garden'
        if gap - 150 - 60 >= 820:
            paving = features[f'{side}-passage-paving']
            assert paving['kind'] == 'path' and paving['material_role'] == 'site.flagstone'
            assert features[f'{side}-passage-drip']['kind'] == 'pebble_bed'
    assert scene['materials']['flagstone']['params'][3] > 0, 'large slabs laid in two tones'


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


def test_studio_offers_focus_mode_fitted_views_and_a_wider_layout():
    html = (ROOT / 'web/index.html').read_text('utf8')
    app = (ROOT / 'web/app.js').read_text('utf8')
    bundle = (ROOT / 'web/viewer.js').read_text('utf8')
    page = (ROOT / 'floorforge/pipeline.py').read_text('utf8')
    for control in ('id="focus"', 'Focus', 'id="zoom-fit"', 'data-view="aerial"', 'data-view="top"', 'id="brief-toggle"'):
        assert control in html, control
    assert 'setFocus' in app and 'frameInsets' in app and 'setWide' in app
    assert 'focusBtn' in page and 'v.setFocus(' in page
    # The viewer frames the home itself (not the street) in every view and mode.
    for name in ('fitHouse', 'houseBox', 'setFocus', 'overheadTheta', 'acrossTheta'):
        assert name in bundle, name


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js unavailable')
def test_framing_fills_the_frame_exactly_from_any_direction():
    # The camera fit (web/viewer/src/framing.js) must put every corner of the home's box inside the usable window,
    # touch the fill line on the limiting axis and centre the other, for low, high and overhead views on wide and
    # tall screens, with toolbars overlaid.
    module = (ROOT / 'web/viewer/src/framing.js').as_uri()
    script = """
import { frameBox, project } from '%s';
const out = [];
const boxes = [[[-.4, -.5, -14.2], [10.4, 6.5, 2.2]], [[0, -.5, -9.5], [7.6, 3.9, 1.5]], [[-3, 0, -3], [3, 12, 3]]];
const dirs = [[-.54, -.18, .82], [0, -.2, 1], [-1, -.15, 0], [-.4, -.62, .67], [0, -1, .05], [.05, -1, 0]];
for (const [min, max] of boxes) for (const d of dirs) for (const [aspect, window] of [[16 / 9, [-1, 1, -1, 1]], [.46, [-.97, .97, -.45, .86]], [3.2, [-.99, .9, -.8, .98]]]) {
  const fill = .9, fov = 43;
  const { position, target } = frameBox(min, max, d, { fov, aspect, fill, window });
  let x0 = 9, x1 = -9, y0 = 9, y1 = -9, zmin = 1e9;
  for (let i = 0; i < 8; i++) {
    const p = [i & 1 ? max[0] : min[0], i & 2 ? max[1] : min[1], i & 4 ? max[2] : min[2]];
    const [x, y, z] = project(p, position, target, { fov, aspect });
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); zmin = Math.min(zmin, z);
  }
  out.push({ window, fill, ndc: [x0, x1, y0, y1], zmin });
}
console.log(JSON.stringify(out));
""" % module
    res = subprocess.run(['node', '--input-type=module', '-e', script], capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    cases = json.loads(res.stdout)
    assert len(cases) == 54
    for case in cases:
        (l, r, b, t), (x0, x1, y0, y1) = case['window'], case['ndc']
        assert case['zmin'] > 0
        # Inside the window (never under a toolbar)...
        assert l - 1e-6 <= x0 and x1 <= r + 1e-6 and b - 1e-6 <= y0 and y1 <= t + 1e-6, case
        # ...filling it on the limiting axis...
        sx, sy = (x1 - x0) / (r - l), (y1 - y0) / (t - b)
        assert case['fill'] - .01 < max(sx, sy) <= case['fill'] + .01, case
        # ...and centred on it.
        slack = (x0 - l, r - x1) if sx >= sy else (y0 - b, t - y1)
        assert abs(slack[0] - slack[1]) < .03, case


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

