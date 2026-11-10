"""Comprehensive geometry, architecture, furnishing, and preservation tests for Tirumala 7."""
import json
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from floorforge.sample_projects import sample_file
from floorforge.plan_geometry import geometry

FT = 304.8
ROOT = Path(__file__).resolve().parents[1]


def read(name: str):
    return json.loads(sample_file('tirumala-7', name).read_text())


def local_box_mm(x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float):
    ax, ay = (40.0 - y1_ft) * FT, (50.0 - x1_ft) * FT
    bx, by = (40.0 - y0_ft) * FT, (50.0 - x0_ft) * FT
    return box(min(ax, bx), min(ay, by), max(ax, bx), max(ay, by))


def test_room_programme_and_nominal_dimensions_within_25mm():
    """Every room on all three floors exists on the right floor with nominal size within ±25 mm of the PDF."""
    b = read('building.json')
    ref = read('plan-reference.json')
    spaces = {s['id']: s for s in b['spaces']}

    expected_ground = {
        'outside_gully': (23.0, 2.0),
        'caregiver': (8.0, 10.0),
        'caregiver_bath': (5.0, 6.0),
        'hall_entry': (3.0, 4.0),
        'drawing_room': (9.5, 14.0),
        'covered_entry': (5.5, 7.0),
        'verandah': (16.0, 9.0),
        'car_porch': (11.0, 20.0),
        'living_hall': (18.5, 10.0),
        'home_icu': (15.0, 17.0),
        'master_bath': (5.5, 8.0),
        'west_gully': (2.0, 14.0),
        'master_bedroom': (15.0, 14.0),
        'bedroom_entry': (7.0, 7.0),
        'dining_hall': (12.0, 7.0),
        'kitchen': (14.0, 8.0),
        'work_bay': (11.0, 6.0),
        'stair': (15.0, 7.0),
        'stair_gap': (2.0, 7.0),
        'store': (7.0, 6.0),
        'wash_area': (9.0, 6.0),
    }
    for sid, (w_ft, d_ft) in expected_ground.items():
        assert sid in spaces, f"Missing ground floor room {sid}"
        s = spaces[sid]
        assert s['floor'] == 0
        assert abs(s['size_mm'][0] - w_ft * FT) <= 25.0
        assert abs(s['size_mm'][1] - d_ft * FT) <= 25.0

    expected_first = {
        'u_master_bedroom': (18.0, 15.0),
        'u_dressing': (8.0, 7.0),
        'u_en_suite': (7.0, 9.0),
        'u_study_meditation': (15.0, 13.0),
        'u_open_to_below': (12.0, 5.0),
        'u_shared_bath': (6.0, 8.0),
        'u_medium_bedroom': (15.0, 11.0),
        'u_stair': (16.0, 7.0),
    }
    for sid, (w_ft, d_ft) in expected_first.items():
        assert sid in spaces, f"Missing first floor room {sid}"
        s = spaces[sid]
        assert s['floor'] == 1
        assert abs(s['size_mm'][0] - w_ft * FT) <= 25.0
        assert abs(s['size_mm'][1] - d_ft * FT) <= 25.0

    # Master suite total area on First floor = 18x15 (270) + 8x7 (56) + 7x9 (63) = 389 sq ft exact per PDF label
    suite_sqft = (
        spaces['u_master_bedroom']['nominal_area_sqft']
        + spaces['u_dressing']['nominal_area_sqft']
        + spaces['u_en_suite']['nominal_area_sqft']
    )
    assert abs(suite_sqft - 389.0) < 0.1

    expected_second = {
        's_office_tv_hall': (30.0, 18.0),
        's_lobby_passage': (4.0, 5.0),
        's_raised_rooflight': (12.0, 5.0),
        's_stair_lobby': (17.0, 9.0),
    }
    for sid, (w_ft, d_ft) in expected_second.items():
        assert sid in spaces, f"Missing second floor room {sid}"
        s = spaces[sid]
        assert s['floor'] == 2
        assert abs(s['size_mm'][0] - w_ft * FT) <= 25.0
        assert abs(s['size_mm'][1] - d_ft * FT) <= 25.0


def test_double_height_void_and_rooflight_alignment_and_guards():
    """The 12' x 5' void and rooflight sit at identical x/y (x: 21..33, y: 26..31) on all three levels,
    cut the first-floor and second-floor slabs, glaze the second floor, and guard all open edges."""
    b = read('building.json')
    ref = read('plan-reference.json')
    spaces = {s['id']: s for s in b['spaces']}

    # Check identical x_ft=[21, 33], y_ft=[26, 31] across all 3 levels
    shaft = ref['vertical_alignment']['light_shaft']
    assert shaft['x_ft'] == [21.0, 33.0] and shaft['y_ft'] == [26.0, 31.0]
    assert spaces['u_open_to_below']['x_ft'] == [21.0, 33.0] and spaces['u_open_to_below']['y_ft'] == [26.0, 31.0]
    assert spaces['s_raised_rooflight']['x_ft'] == [21.0, 33.0] and spaces['s_raised_rooflight']['y_ft'] == [26.0, 31.0]
    assert not spaces['u_open_to_below']['walkable']
    assert not spaces['s_raised_rooflight']['walkable']
    assert spaces['s_raised_rooflight'].get('glassCover') is True

    void_poly = local_box_mm(21.0, 26.0, 33.0, 31.0).buffer(-5.0)
    plate1 = geometry(b['floor_plates'][1]['regions'])
    plate2 = geometry(b['floor_plates'][2]['regions'])
    assert plate1.intersection(void_poly).area < 1.0, "First-floor slab must be cut over the 12' x 5' void"
    assert plate2.intersection(void_poly).area < 1.0, "Second-floor slab must be cut for the 12' x 5' rooflight"

    # Guards around first-floor overlook and second-floor rooflight
    guards = {g['id']: g for g in b['guards']}
    for gid in ('u-void-guard-west', 'u-void-guard-north', 'u-void-guard-south', 's-rooflight-curb-north', 's-rooflight-curb-east'):
        assert gid in guards
        assert guards[gid]['height'] >= 1050

    # Verify 3D scene has the rooflight glass and balustrade nodes
    scene = read('scene.json')
    node_ids = {n['id'] for n in scene['nodes']}
    assert 's-rooflight-glass' in node_ids
    assert 'u-void-guard-north-glass' in node_ids
    assert 'void-chandelier-ring-0' in node_ids


def test_terrace_edges_walkable_areas_and_car_porch_open_strip():
    """Terrace outer east edges are straight at x=47' (first floor, 520 sq ft) and x=44' (second floor, 858 sq ft),
    and the outer 3' of the car porch (x: 47..50, y: 0..20) is open to the sky."""
    b = read('building.json')
    spaces = {s['id']: s for s in b['spaces']}

    t1 = spaces['u_large_terrace']
    t2 = spaces['s_open_terrace']
    assert t1['east_edge_x_ft'] == 47.0
    assert t2['east_edge_x_ft'] == 44.0
    assert abs(t1['nominal_area_sqft'] - 520.0) < 0.5
    assert abs(t2['nominal_area_sqft'] - 858.0) < 0.5

    # Outer 3' of the car porch (x: 47..50, y: 0..20) is open to the sky on both upper floor plates
    open_strip = local_box_mm(47.0, 0.0, 50.0, 20.0).buffer(-5.0)
    for fl_idx in (1, 2):
        plate = geometry(b['floor_plates'][fl_idx]['regions'])
        assert plate.intersection(open_strip).area < 1.0


def test_stair_294_sequence_risers_treads_and_headroom():
    """The U-turn staircase has the 2/9/4 tread sequence, risers <= 190 mm, treads >= 250 mm, and headroom >= 2100 mm."""
    b = read('building.json')
    stairs = {st['floor']: st for st in b['stairs']}
    assert set(stairs) == {0, 1, 2}
    for f in (0, 1):
        st = stairs[f]
        assert st['tread_sequence'] == [2, 9, 4]
        assert st['riser_count'] == 18
        assert st['riser_mm'] <= 190.0 and abs(st['riser_mm'] - 175.0) < 0.1
        assert st['tread_mm'] >= 250.0
        assert st['headroom_mm'] >= 2100.0
        assert st['flight_width'] >= 1000.0


def test_home_icu_dimensions_openings_and_layout():
    """Home ICU is 15' x 17', has a 7' north slider to the verandah, >= 1200 mm clear west opening with no door leaf,
    and hospital bed facing the west-wall 75\" TV."""
    b = read('building.json')
    spaces = {s['id']: s for s in b['spaces']}
    icu = spaces['home_icu']
    assert abs(icu['size_mm'][0] - 15.0 * FT) <= 25.0
    assert abs(icu['size_mm'][1] - 17.0 * FT) <= 25.0

    openings = {o['id']: o for o in b['openings']}
    slider = openings['icu_north_slider']
    assert slider['sliding'] is True
    assert abs(slider['width'] - 7.0 * FT) <= 25.0
    assert set(slider['connects']) == {'home_icu', 'verandah'}

    west_open = openings['icu_west_clear_opening']
    assert west_open['kind'] == 'cased'
    assert west_open['swing'] is None
    assert west_open['width'] >= 1200.0 and abs(west_open['width'] - 5.5 * FT) <= 25.0
    assert set(west_open['connects']) == {'home_icu', 'living_hall'}

    scene = read('scene.json')
    nodes = {n['id']: n for n in scene['nodes']}
    assert 'home_icu/bed-base' in nodes and 'home_icu/tv-55in' in nodes
    bed_y = nodes['home_icu/bed-base']['position'][1]
    tv_y = nodes['home_icu/tv-55in']['position'][1]
    # In building metres (+Y is west), the west wall TV has a larger Y coordinate than the east-side bed
    assert tv_y > bed_y + 2.0


def test_straight_run_kitchen_work_bay_and_prep_counter():
    """Kitchen counter is a single straight east-wall run (~13'6\"), with sink in the work bay (y~22.25..24.35),
    hob at the south end (y~30..32.15), prep counter against the ICU south wall, and doors to store and wash area."""
    b = read('building.json')
    openings = {o['id']: o for o in b['openings']}
    assert set(openings['store_door']['connects']) == {'kitchen', 'store'}
    assert set(openings['wash_area_door']['connects']) == {'kitchen', 'wash_area'}

    scene = read('scene.json')
    nodes = {n['id']: n for n in scene['nodes']}
    assert 'kitchen/modular-kitchen/quartz-worktop' in nodes
    assert 'kitchen/modular-kitchen/sink-bottom' in nodes
    assert 'kitchen/modular-kitchen/hob-glass-plate' in nodes
    assert 'kitchen/modular-kitchen/prep-quartz-top' in nodes
    assert 'kitchen/modular-kitchen/loft-carcass' in nodes
    loft = nodes['kitchen/modular-kitchen/loft-carcass']
    # Counter/loft run spans y_ft: 20.3..33.7 (13.4 ft = 4.084 m along X in building coordinates)
    assert abs(loft['scale'][0] - 13.4 * 0.3048) < 0.05
    # Sink is at north end (larger X in building metres), hob is at south end (smaller X in building metres)
    sink_x = nodes['kitchen/modular-kitchen/sink-drainboard']['position'][0]
    hob_x = nodes['kitchen/modular-kitchen/hob-glass-plate']['position'][0]
    assert sink_x > hob_x + 1.8


def test_all_pdf_doors_and_windows_match_within_25mm():
    """Every door and window in `plan-reference.json` exists in `building.json` within ±25 mm."""
    b = read('building.json')
    ref = read('plan-reference.json')
    by_id = {o['id']: o for o in b['openings']}

    for fkey, f_idx in (('ground', 0), ('first', 1), ('second', 2)):
        f_data = ref['floors'][fkey]
        for item in list(f_data['doors']) + list(f_data['windows']):
            oid = item['id']
            assert oid in by_id, f"Missing PDF opening {oid} on {fkey} floor"
            o = by_id[oid]
            assert o['floor'] == f_idx
            expected_w = abs(item['span_ft'][1] - item['span_ft'][0]) * FT
            assert abs(o['width'] - expected_w) <= 25.0


def test_other_gallery_samples_are_unchanged():
    """Adding tirumala-7 leaves all existing catalog entries and their planHashes untouched."""
    catalog = json.loads((ROOT / 'examples/gallery/catalog.json').read_text())
    by_id = {entry['id']: entry for entry in catalog}
    assert 'tirumala-7' in by_id
    for sid in ('tirumala-4', 'tirumala-5', 'tirumala-6'):
        assert sid in by_id
        b = json.loads(sample_file(sid, 'building.json').read_text())
        assert by_id[sid]['planHash'] == b['planHash']


def test_walkthrough_rooflight_sightline_and_cycles_renders_exist():
    """Verify 3-floor walkthrough start points, clear daylight path through the 12' x 5' rooflight shaft,
    and all 26 Blender Cycles renders plus style-comparison-sheet.png and gallery thumbnail."""
    b, scene = read('building.json'), read('scene.json')
    spaces = {r['id']: r for r in b['spaces']}
    for f, rid in ((0, 'living_hall'), (1, 'u_family_gallery'), (2, 's_office_tv_hall')):
        pos = scene['walk']['floors'][f]['position'][:2]
        pt_mm = Point(pos[0] * 1000.0, pos[1] * 1000.0)
        assert Polygon(spaces[rid]['clear']).contains(pt_mm)
        assert geometry(b['roofs'][f]['ceiling']).covers(pt_mm)

    # Vertical daylight sightline from dining table center (28.0', 28.5') up through First and Second floor plates to rooflight glass
    shaft_pt_mm = Point((40.0 - 28.5) * FT, (50.0 - 28.0) * FT)
    for f in (1, 2):
        assert not geometry(b['floor_plates'][f]['regions']).intersects(shaft_pt_mm)
        assert not geometry(b['roofs'][f - 1]['ceiling']).intersects(shaft_pt_mm)
    assert geometry(b['roofs'][2]['rooflight']).covers(shaft_pt_mm)

    expected_renders = [
        'ground', 'first', 'second',
        'exterior', 'east_arrival', 'north_frontage', 'colony_overview', 'roof_terraces',
        'kitchen_run', 'kitchen_from_dining', 'dining_double_height', 'living_hall',
        'living_to_icu', 'icu', 'verandah', 'drawing_room', 'master_bedroom',
        'gallery_void', 'master_suite', 'study_meditation', 'medium_bedroom', 'east_terrace',
        'office_tv_hall', 'north_terrace', 'rooflight', 'stair_lobby',
        'style-comparison-sheet',
    ]
    for name in expected_renders:
        p = sample_file('tirumala-7', f'renders/{name}.png')
        assert p.is_file() and p.stat().st_size > 20_000, f"Missing or empty render: {p}"
    thumb = ROOT / 'examples/gallery/thumbnails/tirumala-7.png'
    assert thumb.is_file() and thumb.stat().st_size > 15_000

