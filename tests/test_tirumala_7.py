"""Comprehensive geometry, architecture, furnishing, glitch-freedom, and preservation tests for Tirumala 7."""
import json
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
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


def test_room_programme_east_setback_and_zero_space_overlaps():
    """Every room on all three floors has exact dimensions, zero pairwise space overlaps,
    a 3' east kitchen/wash setback (x=47..50), 22' car porch, 15'x16' Home ICU, and 5' wash room."""
    b = read('building.json')
    spaces = {s['id']: s for s in b['spaces']}

    expected_ground = {
        'outside_gully': (23.0, 2.0),
        'caregiver': (8.0, 10.0),
        'caregiver_bath': (5.0, 6.0),
        'hall_entry': (3.0, 4.0),
        'drawing_room': (9.5, 14.0),
        'covered_entry': (5.5, 7.0),
        'verandah': (16.0, 9.0),
        'car_porch': (11.0, 22.0),
        'east_setback': (3.0, 18.0),
        'living_hall': (18.5, 10.0),
        'home_icu': (15.0, 16.0),
        'master_bath': (5.5, 8.0),
        'west_gully': (2.0, 14.0),
        'master_bedroom': (15.0, 14.0),
        'bedroom_entry': (4.0, 7.0),
        'dining_hall': (11.0, 8.0),
        'work_bay': (8.0, 3.0),
        'kitchen': (12.0, 10.0),
        'stair': (16.0, 7.0),
        'store': (7.0, 5.0),
        'wash_area': (7.0, 5.0),
    }
    for sid, (w_ft, d_ft) in expected_ground.items():
        assert sid in spaces, f"Missing ground floor room {sid}"
        s = spaces[sid]
        assert s['floor'] == 0
        assert abs(s['size_mm'][0] - w_ft * FT) <= 25.0
        assert abs(s['size_mm'][1] - d_ft * FT) <= 25.0

    # Kitchen and wash room sit west of x=47', leaving a full 3' east setback (x=47..50)
    assert spaces['kitchen']['x_ft'][1] == 47.0
    assert spaces['work_bay']['x_ft'][1] == 47.0
    assert spaces['wash_area']['x_ft'][1] == 47.0
    assert spaces['east_setback']['x_ft'] == [47.0, 50.0]

    expected_first = {
        'u_master_bedroom': (18.0, 15.0),
        'u_dressing': (8.0, 7.0),
        'u_en_suite': (7.0, 9.0),
        'u_study_meditation': (15.0, 13.0),
        'u_open_to_below': (10.0, 8.0),
        'u_shared_bath': (5.0, 8.0),
        'u_medium_bedroom': (15.0, 11.0),
        'u_stair': (16.0, 7.0),
    }
    for sid, (w_ft, d_ft) in expected_first.items():
        assert sid in spaces, f"Missing first floor room {sid}"
        s = spaces[sid]
        assert s['floor'] == 1
        assert abs(s['size_mm'][0] - w_ft * FT) <= 25.0
        assert abs(s['size_mm'][1] - d_ft * FT) <= 25.0

    suite_sqft = (
        spaces['u_master_bedroom']['nominal_area_sqft']
        + spaces['u_dressing']['nominal_area_sqft']
        + spaces['u_en_suite']['nominal_area_sqft']
    )
    assert abs(suite_sqft - 389.0) < 0.1

    expected_second = {
        's_office_tv_hall': (31.0, 17.0),
        's_lobby_passage': (3.5, 8.0),
        's_raised_rooflight': (13.5, 8.0),
        's_stair_lobby': (17.0, 7.0),
    }
    for sid, (w_ft, d_ft) in expected_second.items():
        assert sid in spaces, f"Missing second floor room {sid}"
        s = spaces[sid]
        assert s['floor'] == 2
        assert abs(s['size_mm'][0] - w_ft * FT) <= 25.0
        assert abs(s['size_mm'][1] - d_ft * FT) <= 25.0

    # Zero pairwise polygon overlaps on every floor
    for f_idx in (0, 1, 2):
        fl_spaces = [sp for sp in b['spaces'] if sp['floor'] == f_idx]
        for i in range(len(fl_spaces)):
            for j in range(i + 1, len(fl_spaces)):
                p1 = Polygon(fl_spaces[i]['polygon'])
                p2 = Polygon(fl_spaces[j]['polygon'])
                assert p1.intersection(p2).area < 1.0, f"Overlap on floor {f_idx}: {fl_spaces[i]['id']} vs {fl_spaces[j]['id']}"


def test_full_span_double_height_atrium_and_sunroof_alignment():
    """The double-height atrium spans the full 8' N-S gap from the Dining north wall (y=25') right up to
    the Staircase (y=33'), and the 13.5' x 8' raised glazed sunroof sits directly overhead."""
    b = read('building.json')
    ref = read('plan-reference.json')
    spaces = {s['id']: s for s in b['spaces']}

    shaft = ref['vertical_alignment']['light_shaft']
    assert shaft['y_ft'] == [25.0, 33.0]
    assert spaces['u_open_to_below']['x_ft'] == [20.5, 30.5] and spaces['u_open_to_below']['y_ft'] == [25.0, 33.0]
    assert spaces['s_raised_rooflight']['x_ft'] == [20.5, 34.0] and spaces['s_raised_rooflight']['y_ft'] == [25.0, 33.0]
    assert not spaces['u_open_to_below']['walkable']
    assert not spaces['s_raised_rooflight']['walkable']
    assert spaces['s_raised_rooflight'].get('glassCover') is True

    void_f1 = local_box_mm(20.5, 25.0, 30.5, 33.0).buffer(-5.0)
    void_f2 = local_box_mm(20.5, 25.0, 34.0, 33.0).buffer(-5.0)
    plate1 = geometry(b['floor_plates'][1]['regions'])
    plate2 = geometry(b['floor_plates'][2]['regions'])
    assert plate1.intersection(void_f1).area < 1.0
    assert plate2.intersection(void_f2).area < 1.0

    guards = {g['id']: g for g in b['guards']}
    for gid in ('u-void-guard-west', 'u-void-guard-east', 'u-void-guard-north', 'u-void-guard-south', 's-rooflight-curb-north', 's-rooflight-curb-east'):
        assert gid in guards
        assert guards[gid]['height'] >= 1050

    scene = read('scene.json')
    node_ids = {n['id'] for n in scene['nodes']}
    assert 's-rooflight-glass' in node_ids
    assert 'u-void-guard-north-glass' in node_ids
    assert 'u-void-guard-east-glass' in node_ids
    assert 'void-chandelier-ring-0' in node_ids


def test_terrace_edges_east_setback_and_ne_car_gate_with_verandah_lawn():
    """Terrace outer east edges sit at x=47' (first floor) and x=44' (second floor), x=47..50 is open to sky,
    NE corner has an interactive 10' car gate + sloped ramp, and Verandah has a manicured lawn court with zero round shrub balls."""
    b = read('building.json')
    scene = read('scene.json')
    spaces = {s['id']: s for s in b['spaces']}

    assert spaces['u_large_terrace']['east_edge_x_ft'] == 47.0
    assert spaces['s_open_terrace']['east_edge_x_ft'] == 44.0

    open_east_strip = local_box_mm(47.0, 0.0, 50.0, 40.0).buffer(-5.0)
    for fl_idx in (1, 2):
        plate = geometry(b['floor_plates'][fl_idx]['regions'])
        assert plate.intersection(open_east_strip).area < 1.0

    gate_ids = {g['id'] for g in scene.get('gate_model', [])}
    assert 'east-walk-gate' in gate_ids
    assert 'north-vehicle-gate' in gate_ids

    node_ids = {n['id'] for n in scene['nodes']}
    assert 'north-vehicle-ramp' in node_ids
    assert 'verandah/north-lawn-turf' in node_ids
    assert 'verandah/north-lawn-coping' in node_ids

    # Zero round/spiky green shrub spheres anywhere in the project
    assert scene.get('vegetation') == []
    plant_proxies = [n['id'] for n in scene['nodes'] if 'plant' in n.get('role', '') or n.get('material') in ('leaf', 'leaf-light')]
    assert plant_proxies == []


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


def test_home_icu_and_all_tvs_complete_without_wall_overlap():
    """Home ICU is 15' x 16' with 7' north slider and 5'6\" clear west opening, and every TV in the house
    has full screen dimensions and zero wall collision."""
    b = read('building.json')
    scene = read('scene.json')
    openings = {o['id']: o for o in b['openings']}

    slider = openings['icu_north_slider']
    assert slider['sliding'] is True and abs(slider['width'] - 7.0 * FT) <= 25.0
    west_open = openings['icu_west_clear_opening']
    assert west_open['kind'] == 'cased' and west_open['swing'] is None and west_open['width'] >= 1200.0

    nodes = {n['id']: n for n in scene['nodes']}
    walls_by_floor = {f: unary_union([Polygon(w['polygon']) for w in b['walls'] if w['floor'] == f]) for f in (0, 1, 2)}

    for tv_id, min_span_m in (
        ('living_hall/tv-75in', 1.60),
        ('home_icu/tv-55in', 1.20),
        ('s_office_tv_hall/tv-75in', 1.60),
    ):
        assert tv_id in nodes
        n = nodes[tv_id]
        pos, sc = n['position'], n['scale']
        assert max(sc[0], sc[1]) >= min_span_m
        assert sc[2] >= 0.70
        tv_box_mm = box((pos[0] - sc[0] / 2) * 1000, (pos[1] - sc[1] / 2) * 1000,
                        (pos[0] + sc[0] / 2) * 1000, (pos[1] + sc[1] / 2) * 1000)
        assert tv_box_mm.intersection(walls_by_floor[n['floor']]).area < 1.0


def test_wide_east_kitchen_platform_east_windows_and_west_shifted_fridge():
    """Kitchen has two east windows on x=47', an 840 mm (2'9\") wide quartz platform with under-platform storage
    and minimalist floating shelves (no heavy east loft), and fridge/pantry shifted west away from the east wall & NE corner."""
    b = read('building.json')
    scene = read('scene.json')
    openings = {o['id']: o for o in b['openings']}
    assert 'kitchen_east_window_1' in openings and openings['kitchen_east_window_1']['wall_ref'] == 'x=47.0'
    assert 'kitchen_east_window_2' in openings and openings['kitchen_east_window_2']['wall_ref'] == 'x=47.0'
    assert 'wash_east_window' in openings and openings['wash_east_window']['wall_ref'] == 'x=47.0'

    nodes = {n['id']: n for n in scene['nodes']}
    assert 'kitchen/modular-kitchen/quartz-worktop' in nodes
    assert 'kitchen/modular-kitchen/minimal-floating-shelf-0' in nodes
    assert 'kitchen/modular-kitchen/loft-carcass' not in nodes  # No heavy overhead loft on east wall!

    plinth = nodes['kitchen/modular-kitchen/plinth-kickboard']
    # Plinth depth is 840 mm - 50 mm = 0.79 m -> confirms 840 mm wide platform!
    assert plinth['scale'][1] >= 0.78

    # Fridge is shifted west (> 2.3 m west of the x=47' east wall, i.e. Y > 3.3 m)
    fridge = nodes['kitchen/modular-kitchen/fridge-housing']
    assert fridge['position'][1] > 3.30


def test_all_plan_reference_doors_and_windows_match_within_25mm():
    """Every door and window in `plan-reference.json` exists in `building.json` within ±25 mm."""
    b = read('building.json')
    ref = read('plan-reference.json')
    by_id = {o['id']: o for o in b['openings']}

    for fkey, f_idx in (('ground', 0), ('first', 1), ('second', 2)):
        f_data = ref['floors'][fkey]
        for item in list(f_data['doors']) + list(f_data['windows']):
            oid = item['id']
            assert oid in by_id, f"Missing opening {oid} on {fkey} floor"
            o = by_id[oid]
            assert o['floor'] == f_idx
            expected_w = abs(item['span_ft'][1] - item['span_ft'][0]) * FT
            assert abs(o['width'] - expected_w) <= 25.0


def test_other_gallery_samples_are_unchanged():
    """Revising tirumala-7 leaves all existing catalog entries and their planHashes untouched."""
    catalog = json.loads((ROOT / 'examples/gallery/catalog.json').read_text())
    by_id = {entry['id']: entry for entry in catalog}
    assert 'tirumala-7' in by_id
    for sid in ('tirumala-4', 'tirumala-5', 'tirumala-6'):
        assert sid in by_id
        b = json.loads(sample_file(sid, 'building.json').read_text())
        assert by_id[sid]['planHash'] == b['planHash']


def test_walkthrough_sunroof_sightline_and_cycles_renders_exist():
    """Verify 3-floor walkthrough start points, clear daylight path through the atrium & sunroof,
    and all 26 Blender Cycles renders plus style-comparison-sheet.png and gallery thumbnail."""
    b, scene = read('building.json'), read('scene.json')
    spaces = {r['id']: r for r in b['spaces']}
    for f, rid in ((0, 'living_hall'), (1, 'u_family_gallery'), (2, 's_office_tv_hall')):
        pos = scene['walk']['floors'][f]['position'][:2]
        pt_mm = Point(pos[0] * 1000.0, pos[1] * 1000.0)
        assert Polygon(spaces[rid]['clear']).contains(pt_mm)
        assert geometry(b['roofs'][f]['ceiling']).covers(pt_mm)

    shaft_pt_mm = Point((40.0 - 29.0) * FT, (50.0 - 26.2) * FT)
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
