"""The reviewed atrium is a real through-opening, with weather glazing above it.

These checks use authored geometry and the generated scene independently. A
skylight label or transparent panel on an uncut opaque slab must not pass.
"""
import numpy as np
import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import solar_position
from floorforge.scene import make_scene, transformation
from floorforge.tirumala_5 import build_project


APERTURE = box(1675, 6075, 5000, 7800)
GALLERY_TAIL = box(150, 4875, 1675, 7800)
FIRST_VOID = box(1250, 6075, 6300, 7800)
LEVEL = 7016
ROOM_HEIGHT = 3350
SQFT_MM2 = 92903.04
RETIRED_SOUTH_WINDOWS = {
    'u-master-south', 'u-atrium-south',
    's2-hall-south', 's2-stair-south-window-proposed',
}
EAST_GLAZING = {
    'u-stair-east': (1, [250, 4800], [1250, 4800]),
    's2-stair-east': (2, [250, 4800], [1250, 4800]),
    's2-gallery-east': (2, [1800, 4800], [5700, 4800]),
}


def shape(regions):
    return unary_union([Polygon(r['polygon'], r.get('holes', [])) for r in regions])


@pytest.fixture(scope='module')
def model():
    return generate_layout(fuse(build_project()))


@pytest.fixture(scope='module')
def scene(model):
    return make_scene(model, {'solar': solar_position(model['brief'])})


def world_vertices(scene, node):
    vertices = np.asarray(scene['assets'][node['asset']]['vertices'], dtype=float)
    matrix = transformation(node)
    return vertices @ matrix[:3, :3].T + matrix[:3, 3]


def mesh_footprint(scene, node):
    vertices = world_vertices(scene, node)
    triangles = []
    for face in scene['assets'][node['asset']]['faces']:
        triangle = Polygon(vertices[face, :2])
        if triangle.area > 1e-10:
            triangles.append(triangle)
    return unary_union(triangles)


def test_atrium_matches_reviewed_aperture_and_lower_void(model):
    up = model['planning']['upperPlan']
    sp = model['planning']['secondPlan']
    assert Polygon(sp['atriumOpening']).equals(APERTURE)
    assert Polygon(up['void']).equals(FIRST_VOID)
    assert FIRST_VOID.covers(APERTURE)
    assert shape(up['floorPlate']).intersection(APERTURE).area < .01
    assert APERTURE.area / SQFT_MM2 == pytest.approx(61.7377536838)
    assert sp.get('skylight'), 'Weather glazing must be explicitly described'


def test_second_slab_and_top_roof_both_clear_the_atrium(model):
    sp = model['planning']['secondPlan']
    assert shape(sp['floorPlate']).intersection(APERTURE).area < .01
    assert shape(sp['hallRoof']).intersection(APERTURE).area < .01
    second_plate = next(p for p in model['floor_plates'] if p['floor'] == 2)
    assert shape(second_plate['regions']).intersection(APERTURE).area < .01
    assert any(Polygon(p).equals(APERTURE) for p in second_plate['openings'])
    for roof in (r for r in model['roofs'] if r['floor'] in (1, 2)):
        assert shape(roof['regions']).intersection(APERTURE).area < .01, roof['id']
        assert shape(roof['ceiling']).intersection(APERTURE).area < .01, roof['id']


def test_atrium_and_enclosure_leave_stacked_stairs_and_arrival_clear(model):
    sp = model['planning']['secondPlan']
    steps = sp['stairs']
    assert len(steps) == 23
    assert len([s for s in steps if not s.get('landing')]) == 20
    assert steps[-1]['top'] == LEVEL
    assert shape(sp['stairVoid']).intersection(APERTURE).area < .01
    assert all(box(*step['bounds']).intersection(APERTURE).area < .01 for step in steps)
    assert shape(sp['floorPlate']).intersection(shape(sp['stairVoid'])).area < .01
    assert sp['minimumAnalyticGroundStairHeadroomMm'] == pytest.approx(3153)
    walls = shape(sp['wallRegions'])
    for name, clear_width in [('stairs_to_hall', 850), ('stairs_to_terrace', 900)]:
        route = LineString(sp['circulationPaths'][name]).buffer(clear_width / 2, cap_style=2, join_style=2)
        assert walls.intersection(route).area < 1, name
        assert shape(sp['floorPlate']).buffer(.01).covers(route), name


def test_expanded_enclosure_gains_usable_space_without_filling_atrium(model):
    sp = model['planning']['secondPlan']
    rooms = {r['id']: shape(r['regions']) for r in sp['rooms']}
    previous_clear_enclosure = unary_union([
        box(150, 6600, 5335.6, 8900), box(150, 4875, 1525, 6600),
        box(5150, 7800, 6600, 8900), box(5485.6, 8900, 6600, 10050),
    ])
    previous_landing = previous_clear_enclosure.difference(shape(sp['stairVoid']))
    expected_landing = previous_clear_enclosure.union(box(1525, 4875, 6600, 7800))
    expected_landing = expected_landing.difference(shape(sp['stairVoid'])).difference(APERTURE).difference(GALLERY_TAIL)
    landing = rooms['s2-indoor-landing']
    assert landing.symmetric_difference(expected_landing).area < 1
    assert (landing.area - previous_landing.area) / SQFT_MM2 == pytest.approx(37.2205796495)
    assert landing.intersection(APERTURE).area < .01
    assert rooms['s2-terrace'].area / SQFT_MM2 == pytest.approx(477, abs=1)
    assert rooms['s2-terrace'].geom_type == 'Polygon'
    assert rooms['s2-terrace'].intersection(landing).area < 1
    assert rooms['s2-hall'].equals(box(150, 9050, 5335.6, 14328))


def test_south_windows_are_closed_and_east_glazing_is_real_openings(model):
    openings = {o['id']: o for o in model['openings']}
    assert not RETIRED_SOUTH_WINDOWS.intersection(openings)
    schedules = {o['id'] for o in model['planning']['upperPlan']['openingSchedule']}
    assert not RETIRED_SOUTH_WINDOWS.intersection(schedules)
    for ident, (floor, a, b) in EAST_GLAZING.items():
        op = openings[ident]
        assert op['floor'] == floor and op['kind'] == 'window'
        assert op['a'] == a and op['b'] == b
        assert op['width'] == pytest.approx(b[0] - a[0])
        assert op['sill'] == 150 and op['height'] == 2900
        wall = next(w for w in model['walls'] if w['id'] == op['wall_id'])
        assert wall['hostOnly']
    # Removing a window must close the masonry cut, not only remove the glass.
    for floor, y0, y1 in [(1, 10100, 11800), (1, 5450, 7300),
                           (2, 10300, 12300), (2, 7000, 8300)]:
        plan = model['planning']['upperPlan' if floor == 1 else 'secondPlan']
        assert shape(plan['wallRegions']).covers(box(10, y0 + 10, 140, y1 - 10))


def test_atrium_guards_cover_free_edges_without_blocking_arrival(model):
    sp = model['planning']['secondPlan']
    guards = unary_union([LineString([a, b]).buffer(25, cap_style=3) for a, b in sp['landingGuards']])
    # The new south end closes against the east wall. The removed ledge and
    # atrium are one void, so their former internal dividing guard disappears.
    for a, b in [([1675, 4875], [1675, 6075]),
                 ([1675, 6075], [5000, 6075]),
                 ([5000, 6075], [5000, 7800]),
                 ([5000, 7800], [5150, 7800])]:
        assert guards.covers(LineString([a, b]))
    assert guards.intersection(box(1600, 6200, 1750, 7650)).area < 1
    arrival = LineString([[5150, 8350], [6050, 8350]]).buffer(425, cap_style=2)
    assert guards.intersection(arrival).area < 1


def test_unused_gallery_tail_is_open_only_at_second_floor(model, scene):
    sp = model['planning']['secondPlan']
    assert Polygon(sp['galleryEndCutout']).equals(GALLERY_TAIL)
    landing = shape(next(r for r in sp['rooms'] if r['id'] == 's2-indoor-landing')['regions'])
    assert landing.geom_type == 'Polygon', 'No disconnected usable-floor pockets'
    assert landing.intersection(GALLERY_TAIL).area < .01
    assert shape(sp['floorPlate']).intersection(GALLERY_TAIL).area < .01
    plate = next(p for p in model['floor_plates'] if p['floor'] == 2)
    assert shape(plate['regions']).intersection(GALLERY_TAIL).area < .01
    # A trim at second floor must not cut the approach serving the lower stair,
    # nor make the newly open volume exposed to the weather through its roof.
    retained_first_approach = box(1525, 4875, 1675, 6075)
    assert shape(model['planning']['upperPlan']['floorPlate']).covers(retained_first_approach)
    assert shape(sp['hallRoof']).covers(GALLERY_TAIL)
    # Preserve the existing usable gallery destination, with a real standing
    # area, and a supported route to it from the stair arrival.
    gallery_route = LineString(sp['circulationPaths']['stairs_to_east_gallery']).buffer(425, cap_style=1, join_style=2)
    assert shape(sp['floorPlate']).covers(gallery_route)
    cut_m = scale(GALLERY_TAIL, xfact=.001, yfact=.001, origin=(0, 0)).buffer(-.01)
    for node in scene['nodes']:
        if node.get('floor') != 2 or node.get('role') not in {'slab', 'floor'}:
            continue
        vertices = world_vertices(scene, node)
        if vertices[:, 2].min() > 7.04 or vertices[:, 2].max() < 6.8:
            continue
        assert mesh_footprint(scene, node).intersection(cut_m).area < 1e-8, node['id']


def test_second_gallery_guard_is_visible_closed_geometry_to_the_wall(model, scene):
    sp = model['planning']['secondPlan']
    assert sp['landingGuardStyle'] == 'metal-and-teak'
    guard_nodes = [n for n in scene['nodes'] if n.get('floor') == 2
                   and n['id'].startswith('s2-landing-guard-')]
    assert guard_nodes, 'Guard needs visible geometry, not only a plan annotation'
    for node in guard_nodes:
        material = scene['materials'][node['material']]
        assert material.get('alpha', 1) == 1, node['id']
        assert material.get('transmission', 0) == 0, node['id']
        assert scene['assets'][node['asset']].get('closed') is not False, node['id']
        assert node['role'] in {'railing', 'parapet'}, 'Guard must participate in collision'
    assert {'frame', 'teak-warm'}.issubset({n['material'] for n in guard_nodes})
    # A continuous top rail must turn across the new end and join the wall;
    # pickets alone, invisible panels or a floating short rail cannot pass.
    top_nodes = [n for n in guard_nodes if world_vertices(scene, n)[:, 2].min() >= 8.05]
    assert top_nodes
    top_footprint = unary_union([mesh_footprint(scene, n) for n in top_nodes]).buffer(.11)
    for a, b in sp['landingGuards']:
        edge = LineString([(a[0] / 1000, a[1] / 1000), (b[0] / 1000, b[1] / 1000)])
        assert top_footprint.covers(edge)
    assert min(world_vertices(scene, n)[:, 2].max() for n in top_nodes) >= 8.10
    # The low ivory base must sit on the retained slab rather than projecting
    # into the newly open volume; its height must not become a full wall.
    bases = [n for n in guard_nodes if n['id'].startswith('s2-landing-guard-base')]
    assert bases
    retained_plate = scale(shape(sp['floorPlate']), xfact=.001, yfact=.001, origin=(0, 0))
    base_footprint = unary_union([mesh_footprint(scene, n) for n in bases])
    assert retained_plate.buffer(1e-6).covers(base_footprint)
    for node in bases:
        vertices = world_vertices(scene, node)
        assert vertices[:, 2].min() == pytest.approx(LEVEL / 1000)
        assert np.ptp(vertices[:, 2]) == pytest.approx(.12)
    # Check actual vertical members, including the last short return, so a
    # visually continuous handrail cannot conceal a large opening below it.
    pickets = [n for n in guard_nodes if '-picket-' in n['id']]
    assert pickets
    centers = []
    for node in pickets:
        vertices = world_vertices(scene, node)
        center = (vertices[:, :2].min(axis=0) + vertices[:, :2].max(axis=0)) / 2
        centers.append(center)
        assert np.linalg.norm(vertices[:, :2] - center, axis=1).max() == pytest.approx(.012, abs=1e-6)
        assert vertices[:, 2].min() <= LEVEL / 1000 + .12
        assert vertices[:, 2].max() >= LEVEL / 1000 + 1.10 - 1e-6
    for a, b in sp['landingGuards']:
        aa, bb = np.asarray(a) / 1000, np.asarray(b) / 1000
        direction = (bb - aa) / np.linalg.norm(bb - aa)
        stations = sorted(float(np.dot(center - aa, direction)) for center in centers
                          if LineString([aa, bb]).distance(Point(center)) < 1e-6)
        assert stations[0] == pytest.approx(0, abs=1e-6)
        assert stations[-1] == pytest.approx(np.linalg.norm(bb - aa), abs=1e-6)
        assert max(np.diff(stations)) <= .110001


def test_terrace_door_opens_outward_without_obstructing_atrium_gallery(model, scene):
    ident = 's2-stair-terrace-proposed'
    opening = next(o for o in model['openings'] if o['id'] == ident)
    assert opening['hinge'] == 'a' and opening['swing_vec'] == [7675, 7900]
    leaf = next(n for n in scene['nodes'] if n['id'] == f'op-{ident}-leaf-0')
    leaf_shape = mesh_footprint(scene, leaf)
    gallery_route = LineString([(5.8, 8.35), (5.8, 5.475)]).buffer(.45, cap_style=2)
    assert leaf_shape.intersection(gallery_route).area < 1e-8
    assert leaf_shape.bounds[0] > 6.7, 'Open leaf must park outside the indoor landing'
    # Check the complete operating arc against actual terrace floor and solid
    # obstructions; ignore its own frame/jamb at the wall threshold.
    swing = unary_union([rotate(leaf_shape, angle, origin=(6.675, 7.9)) for angle in range(0, 91, 3)])
    outside_swing = swing.intersection(box(6.75, 7.8, 7.75, 8.95))
    terrace = next(r for r in model['planning']['secondPlan']['rooms'] if r['id'] == 's2-terrace')
    assert scale(shape(terrace['regions']), xfact=.001, yfact=.001, origin=(0, 0)).covers(outside_swing)
    for node in scene['nodes']:
        if node.get('owner') == ident or node.get('floor') != 2:
            continue
        vertices = world_vertices(scene, node)
        if vertices[:, 2].max() <= 7.05 or vertices[:, 2].min() >= 9.65:
            continue
        material = scene['materials'][node['material']]
        if material.get('alpha', 1) < 1 or material.get('transmission', 0) > 0:
            continue
        assert mesh_footprint(scene, node).intersection(outside_swing).area < 1e-8, node['id']


def test_scene_has_no_hidden_opaque_slab_or_soffit_over_light_path(scene):
    aperture_m = scale(APERTURE, xfact=.001, yfact=.001, origin=(0, 0)).buffer(-.12)
    for node in scene['nodes']:
        if node.get('floor', 0) < 1 or node.get('role') not in {'roof', 'slab', 'floor', 'ceiling', 'soffit', 'fascia'}:
            continue
        if any(token in node['id'] or token in str(node.get('owner', '')) for token in ('skylight', 'rooflight')):
            continue
        vertices = world_vertices(scene, node)
        if vertices[:, 2].max() < LEVEL / 1000 - .3:
            continue
        assert mesh_footprint(scene, node).intersection(aperture_m).area < 1e-6, node['id']


def test_scene_skylight_is_transparent_and_retired_windows_leave_no_meshes(scene):
    glazing = []
    for node in scene['nodes']:
        owner = node.get('owner', '')
        assert owner not in RETIRED_SOUTH_WINDOWS, node['id']
        assert not any(node['id'].startswith('op-' + ident + '-') for ident in RETIRED_SOUTH_WINDOWS)
        if not any(token in node['id'] or token in str(owner) for token in ('skylight', 'rooflight')):
            continue
        material = scene['materials'][node['material']]
        if material.get('alpha', 1) < 1 or material.get('transmission', 0) > 0:
            glazing.append(node)
    assert glazing, 'Skylight needs actual transparent weather glazing, not only an opening'
    aperture_m = scale(APERTURE, xfact=.001, yfact=.001, origin=(0, 0))
    projected = unary_union([mesh_footprint(scene, n) for n in glazing])
    assert projected.intersection(aperture_m).area > .9 * aperture_m.area
    assert all(world_vertices(scene, n)[:, 2].min() >= (LEVEL + ROOM_HEIGHT) / 1000 for n in glazing)


def test_no_downlight_or_pendant_floats_in_the_open_atrium(scene):
    aperture_m = scale(APERTURE, xfact=.001, yfact=.001, origin=(0, 0)).buffer(-.05)
    for node in scene['nodes']:
        if node.get('role') not in {'downlight', 'fixture', 'cove', 'lamp'}:
            continue
        vertices = world_vertices(scene, node)
        if vertices[:, 2].max() <= 3.3 or vertices[:, 2].min() >= 10.546:
            continue
        assert mesh_footprint(scene, node).intersection(aperture_m).area < 1e-8, node['id']


def test_rooflight_curbs_and_solar_are_supported_outside_the_aperture(scene):
    aperture_m = scale(APERTURE, xfact=.001, yfact=.001, origin=(0, 0))
    hall_roof = box(.15, 9.05, 5.3356, 14.328)
    panels = [n for n in scene['nodes'] if n['id'].startswith('t5-solar-module-') and n['id'].endswith('-backing')]
    assert len(panels) == 4, 'Four physical roof panels, rather than a metadata-only solar label'
    for panel in panels:
        footprint = mesh_footprint(scene, panel)
        assert hall_roof.covers(footprint)
        assert footprint.intersection(aperture_m).area == 0
        # This measures the actual inclined solid, independently of its metadata.
        vertices = world_vertices(scene, panel)
        south = vertices[np.isclose(vertices[:, 0], vertices[:, 0].min()), 2].max()
        north = vertices[np.isclose(vertices[:, 0], vertices[:, 0].max()), 2].max()
        assert north - south == pytest.approx(1.13 * np.tan(np.deg2rad(8)))
        pads = [n for n in scene['nodes'] if n.get('owner') == panel['owner'] and '-pad-' in n['id']]
        assert len(pads) == 4
        for pad in pads:
            assert footprint.covers(mesh_footprint(scene, pad))
            assert world_vertices(scene, pad)[:, 2].min() == pytest.approx(10.546)
    for node in scene['nodes']:
        if node['id'].startswith(('t5-rooflight-curb-', 't5-rooflight-drain-')):
            assert mesh_footprint(scene, node).intersection(aperture_m).area < 1e-8
    equipment = scene['roofEquipment']
    assert equipment['clearApertureMm'] == [1675, 6075, 5000, 7800]
    assert equipment['solarModules'] == 4 and equipment['solarFaces'] == 'South'
    assert min(equipment['solarMaintenanceClearancesMm'].values()) >= 700
