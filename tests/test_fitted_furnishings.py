"""Fitted furnishings (custom-plan furnishingStyle "fitted"): a closed quilt inside the mattress outline, and a default
kitchen run with an inset sink, a chimney hood over the hob and handled wall cupboards. Other plans keep their
published recipes, which tests/test_custom_plan.py and the published-sample tests pin."""
import copy
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from floorforge.custom_plan import normalize
from floorforge.exterior import apply_exterior_preferences
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError, read_json
from floorforge.review import reports, validate
from floorforge.scene import fitted_bedspread, make_scene, transformation
from floorforge.scene_kit import rounded_box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_plan_reveal_samples as reveal  # noqa: E402


def build(slug, style=None):
    make = {s: m for s, m, _ in reveal.SAMPLES}[slug]
    p = make()
    p['editorState'] = reveal.editor_state(p)
    p['customPlan'].pop('furnishingStyle', None)
    if style:
        p['customPlan']['furnishingStyle'] = style
    b = apply_exterior_preferences(generate_layout(fuse(p)))
    return b, make_scene(b, reports(b, validate(b)))


@pytest.fixture(scope='module', params=['long-house', 'aangan-house'])
def pair(request):
    return request.param, build(request.param), build(request.param, 'fitted')


def world(scene, node):
    v = np.asarray(scene['assets'][node['asset']]['vertices'])
    return (transformation(node) @ np.c_[v, np.ones(len(v))].T).T[:, :3]


def bounds(scene, node):
    w = world(scene, node)
    return w.min(0), w.max(0)


@pytest.mark.parametrize('width', [1.8, 1.6, 1.35, 1.0])
@pytest.mark.parametrize('frame', [((1, 0), (0, 1)), ((0, -1), (1, 0)), ((-1, 0), (0, -1)), ((1, 0), (0, -1))])
def test_spread_is_one_closed_quilt_clear_of_and_inside_the_mattress(width, frame):
    t, n = (np.array(a, float) for a in frame)
    c, length, v0, z = np.array([2., 3.]), 2.05, .1, 3.15
    spread = fitted_bedspread(lambda u, v: tuple(c + t * u + n * v), (width / 2 + .02, v0 + length / 2, length / 2 + .015, z + .515, .075), v0 + .68)
    assert spread.is_watertight and spread.is_winding_consistent and spread.volume > 0
    # Smooth normals point the way of the faces around them, so no triangle shades as if flipped.
    assert (np.einsum('ij,ij->i', spread.vertex_normals[spread.faces].mean(1), spread.face_normals) > 0).all()
    # The mattress as bed_set builds it (Kit.rb's rounded box). It is convex, so its face planes bound it.
    mattress = rounded_box((width + .04, length + .03, .25), .075)
    turn = np.array([[t[0], n[0], 0], [t[1], n[1], 0], [0, 0, 1]])
    mattress = trimesh.Trimesh(mattress.vertices @ turn.T + [*(c + n * (v0 + length / 2)), z + .39], mattress.faces)
    if mattress.volume < 0:
        mattress.invert()
    clearance = ((spread.vertices[:, None] - mattress.triangles[None, :, 0]) * mattress.face_normals[None]).sum(-1).max(1)
    assert clearance.min() > .002
    local = np.c_[(spread.vertices[:, :2] - c) @ t, (spread.vertices[:, :2] - c) @ n]
    assert abs(local[:, 0]).max() <= width / 2 + .02 - .015
    assert v0 + .6 <= local[:, 1].min() and local[:, 1].max() <= v0 + length + .015 - .015


def test_furnishing_style_is_a_validated_opt_in():
    room = dict(id='r', kind='bedroom', polygon=[[0, 0], [4000, 0], [4000, 4000], [0, 4000]])
    plan = lambda **extra: dict(schema='floorforge.custom-plan/1', units='mm', floors=[dict(id='f', rooms=[room], openings=[], walls=[])], **extra)
    assert 'furnishingStyle' not in normalize(plan(), 1)
    for style in ('standard', 'fitted'):
        assert normalize(plan(furnishingStyle=style), 1)['furnishingStyle'] == style
    for bad in ('Fitted', 'deluxe', True, None):
        with pytest.raises(DesignError):
            normalize(plan(furnishingStyle=bad), 1)
    b, _ = build('long-house', 'fitted')
    assert b['planning']['furnishingStyle'] == 'fitted'
    assert 'furnishingStyle' not in build('long-house')[0]['planning']


def test_fitted_only_changes_spreads_and_the_default_kitchen_run(pair):
    slug, (b, standard), (_, fitted) = pair
    kitchens = {s['id'] for s in b['spaces'] if s['kind'] == 'kitchen' and not s.get('kitchenLayout')}
    runs = [Polygon(f['footprint']) for f in fitted['furniture'] if f['kind'] == 'kitchen-run' and f['room_id'] in kitchens]
    beds = [Polygon(f['footprint']) for f in fitted['furniture'] if f['kind'] == 'bed']

    def keyed(scene):
        out = Counter()
        for node in scene['nodes']:
            lo, hi = bounds(scene, node)
            out[(node['material'], node['role'], node['floor'], *np.round(lo, 4), *np.round(hi, 4))] += 1
        return out
    a, f = keyed(standard), keyed(fitted)
    changed = list((a - f).elements()) + list((f - a).elements())
    spreads = 0
    for key in changed:
        material, role, floor = key[:3]
        plan = box(key[3], key[4], key[6], key[7])
        if material == 'fabric' and any(bed.buffer(.1).contains(plan) for bed in beds):
            spreads += 1
            continue
        assert any(run.buffer(.05).contains(plan) for run in runs), (slug, key)
    assert spreads == 2 * len(beds)
    assert bool(runs) == any(not any(bed.buffer(.1).contains(box(k[3], k[4], k[6], k[7])) for bed in beds) for k in changed)
    for key in ('materials', 'vegetation', 'lawns', 'cameras', 'colliders', 'furniture', 'rooms', 'walk', 'door_motion'):
        assert fitted[key] == standard[key], key
    moved = [(x, y) for x, y in zip(standard['lights'], fitted['lights']) if x != y]
    assert len(fitted['lights']) == len(standard['lights']) and all(x['kind'] == y['kind'] == 'undercabinet' for x, y in moved)


def near(a, b):
    return abs(a - b) < 2e-3


def kitchen(scene):
    """The default kitchen run's parts as (node, low corner, high corner), heights above its floor, and its fittings."""
    H = scene['floor_height']
    run = next(f for f in scene['furniture'] if f['kind'] == 'kitchen-run')
    z, zone = run['floor'] * H, Polygon(run['footprint']).buffer(.05)
    parts = []
    for node in scene['nodes']:
        if node['floor'] == run['floor']:
            lo, hi = bounds(scene, node)
            if zone.contains(box(lo[0], lo[1], hi[0], hi[1])):
                parts.append((node, lo - [0, 0, z], hi - [0, 0, z]))
    plan = lambda lo, hi: box(lo[0], lo[1], hi[0], hi[1])
    # The sink is let into the worktop: nothing stands on the worktop but the tap, the hob and the hood.
    assert not [n for n, lo, hi in parts if n['material'] == 'appliance' and .88 < hi[2] < 1.5]
    rim = next(plan(lo, hi) for n, lo, hi in parts if n['material'] == 'appliance' and near(lo[2], .866) and near(hi[2], .875))
    drain = next((lo + hi) / 2 for n, lo, hi in parts if n['material'] == 'frame' and near(lo[2], .6775) and near(hi[2], .6825))
    worktop = next(n for n, lo, hi in parts if n['material'] == 'counter' and near(lo[2], .83) and near(hi[2], .87))
    top, faces = world(scene, worktop), np.asarray(scene['assets'][worktop['asset']]['faces'])
    surface = unary_union([Polygon(top[f][:, :2]) for f in faces if np.allclose(top[f][:, 2], z + .87)])
    assert not surface.contains(Point(drain[:2])) and rim.contains(Point(drain[:2]))
    assert [n for n, lo, hi in parts if n['material'] == 'appliance' and near(lo[2], .665) and hi[2] < .7]
    # A chimney hood over the hob, clear of the sink, its duct reaching the ceiling.
    burners = [(lo + hi) / 2 for n, lo, hi in parts if n['material'] == 'frame' and near(lo[2], .872) and near(hi[2], .888)]
    assert len(burners) == 4
    hob = np.mean(burners, 0)
    plate = next(plan(lo, hi) for n, lo, hi in parts if n['material'] == 'blackglass' and near(lo[2], .87) and near(hi[2], .877))
    hood = next(plan(lo, hi) for n, lo, hi in parts if n['material'] == 'appliance' and near(lo[2], 1.58) and near(hi[2], 1.645))
    duct = next((lo, hi) for n, lo, hi in parts if n['material'] == 'appliance' and near(lo[2], 1.645))
    assert hood.buffer(-.1).contains(Point(hob[:2])) and plate.distance(rim) > .02
    assert near(duct[1][2], scene['floor_height'] - .157) and hood.contains(plan(*duct))
    doors = [plan(lo, hi) for n, lo, hi in parts if n['role'] == 'furniture' and near(lo[2], 1.53) and near(hi[2], 2.27)]
    handles = [Point(((lo + hi) / 2)[:2]) for n, lo, hi in parts if n['material'] == 'frame' and n['role'] == 'detail' and near(lo[2], 1.56) and near(hi[2], 1.76)]
    return dict(run=run, rim=rim, hood=hood, doors=doors, handles=handles)


def test_fitted_kitchen_has_an_inset_sink_a_chimney_hood_and_handled_wall_cupboards():
    k = kitchen(build('long-house', 'fitted')[1])
    # Wall cupboards beside (never over) the hood, and a bar handle on every door.
    assert len(k['doors']) >= 2 and len(k['handles']) == len(k['doors'])
    for door in k['doors']:
        assert not door.intersects(k['hood'])
        assert sum(door.distance(h) < .03 for h in k['handles']) == 1


def test_fitted_kitchen_under_a_window_keeps_its_hood_on_solid_wall():
    p = read_json(ROOT / 'examples/custom/g2-terrace.floorforge.json')
    p['customPlan']['furnishingStyle'] = 'fitted'
    window = next(o for o in p['customPlan']['floors'][0]['openings'] if o['id'] == 'custom-F0-service-window')
    window.update(sill=1050, height=1100)  # high enough for the worktop, a fridge at its end, to run beneath it
    b = apply_exterior_preferences(generate_layout(fuse(p)))
    k = kitchen(make_scene(b, reports(b, validate(b))))
    opening = next(o for o in b['openings'] if o['id'] == window['id'])
    wall = next(w for w in b['walls'] if w['id'] == opening['wall_id'])
    a, e = np.array(wall['a']) / 1000, np.array(wall['b']) / 1000
    along = (e - a) / np.linalg.norm(e - a)
    glazed = LineString([a + along * opening['offset'] / 1000, a + along * (opening['offset'] + opening['width']) / 1000]).buffer(1, cap_style='flat')
    # The sink sits under the window and the chimney goes up the solid wall; glazing takes no wall cupboards.
    assert glazed.contains(k['rim'].centroid) and not k['hood'].intersects(glazed) and not k['doors']


def test_a_short_fitted_run_keeps_the_sink_clear_of_the_hob():
    make = {s: m for s, m, _ in reveal.SAMPLES}['long-house']
    p = make()
    p['editorState'] = reveal.editor_state(p)
    p['customPlan']['furnishingStyle'] = 'fitted'
    openings = {o['id']: o for o in p['customPlan']['floors'][0]['openings']}
    # A wider garden door and a low window leave the kitchen only a 1.5 m stretch of wall for its run.
    openings['l-kitchen-garden'].update(offset=1900, width=2200)
    openings['l-kitchen-east'].update(sill=750)
    b = apply_exterior_preferences(generate_layout(fuse(p)))
    k = kitchen(make_scene(b, reports(b, validate(b))))
    footprint = Polygon(k['run']['footprint'])
    assert max(footprint.bounds[2] - footprint.bounds[0], footprint.bounds[3] - footprint.bounds[1]) < 1.6
