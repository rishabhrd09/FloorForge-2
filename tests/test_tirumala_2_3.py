"""Automated verification tests for the two independent sample projects:
- 'tirumala-2' (based on finalized P12 / P12-A, version p12-open-porch-v33)
- 'tirumala-3' (based on finalized P11, version p11-veranda-return-trim-v32)
"""
from __future__ import annotations

import json
import copy
import math
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.scene import make_scene
from floorforge.tirumala_p11_p12 import (
    PROVISIONAL_PORCH_DROP_MM,
    build_p11_p12_project,
    load_authoritative_plan_data,
)

ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = ROOT / "examples" / "gallery"


def test_requested_upper_floor_has_connected_rooms_and_real_open_voids():
    for slug in ('tirumala-2','tirumala-3'):
        b=_load_sample_json(slug,'building.json'); up=b['planning']['upperPlan']
        rooms={r['id']:Polygon(r['clear'],r.get('holes',[])) for r in b['spaces'] if r['floor']==1}
        assert set(rooms)=={'u-master','u-master-bath','u-study','u-bedroom','u-bath','u-gallery','u-terrace'}
        assert rooms['u-master'].symmetric_difference(Polygon(next(r for r in b['spaces'] if r['id']=='g-bedroom')['clear'])).area<1
        for a,p in rooms.items():
            assert p.is_valid and Polygon(b['plot']).covers(p)
            for c,q in rooms.items():
                if a<c:assert p.intersection(q).area<1,(a,c)
        plate=unary_union([Polygon(r['polygon'],r['holes']) for r in up['floorPlate']])
        assert plate.intersection(Polygon(up['void']).buffer(-1)).area<1
        assert plate.intersection(Polygon(up['lightwellClear']).buffer(-1)).area<1
        assert Polygon(up['void']).area/1e6>14
        assert rooms['u-terrace'].area/92903.04>330
        graph=validate(b)['graph'];seen={'g-living'};todo=['g-living']
        while todo:
            for x in graph[todo.pop()]:
                if x not in seen:seen.add(x);todo.append(x)
        assert set(rooms)<=seen
        bad=copy.deepcopy(b);next(r for r in bad['spaces'] if r['id']=='u-master')['clear'][0][0]+=100
        assert any(c['id']=='upper_floor_rooms_and_dimensions' for c in validate(bad)['errors'])


def test_icu_has_independent_glass_and_wood_without_resizing_the_opening():
    for slug in ('tirumala-2','tirumala-3'):
        scene=_load_sample_json(slug,'scene.json');b=_load_sample_json(slug,'building.json')
        motion=scene['door_motion']['icu-glass-living'];layers={l['id']:l for l in motion['layers']}
        assert motion['layerOrderFromHall']==['wood','glass']
        assert set(layers)=={'icu-glass-living','icu-glass-living-wood'}
        for layer in layers.values():
            assert len(layer['parts'])==4 and all(p['reverse'] and abs(p.get('angle',0))<.001 for p in layer['parts'])
        aperture=next(o for o in b['openings'] if o['id']=='icu-glass-living')
        assert abs(motion['clearWidth']*1000-(aperture['width']-110))<.1


def test_selected_picture_windows_are_tall_with_non_projecting_vents():
    from floorforge.tirumala_luxury import GROUND_PICTURE_WINDOWS
    for slug in ('tirumala-2','tirumala-3'):
        b=_load_sample_json(slug,'building.json');scene=_load_sample_json(slug,'scene.json')
        source={o['id']:o for o in b['planning']['canonicalPlan']['openings']}
        for o in b['openings']:
            if o['id'] in GROUND_PICTURE_WINDOWS:
                assert (o['sill'],o['height'])==GROUND_PICTURE_WINDOWS[o['id']]
                assert o['sill']+o['height']==2850
                assert o['a']==source[o['id']]['a'] and o['b']==source[o['id']]['b']
            if o.get('window_style')=='picture-with-sliding-vents':
                parts=scene['door_motion'][o['id']]['parts']
                assert len(parts)==2 and all(p.get('slide') and not p.get('angle') for p in parts)
                assert any(n['owner']==o['id'] and 'picture-glass' in n['id'] for n in scene['nodes'] if n.get('owner'))
        kitchen=next(o for o in b['openings'] if o['id']=='kitchen-east')
        assert kitchen['sill']==950
        assert b['planning']['finishSelection']=={'palette':'ivory-teak','status':'user-approved'}


def test_upper_walk_cameras_and_guard_geometry_match_levels():
    for slug in ('tirumala-2','tirumala-3'):
        scene=_load_sample_json(slug,'scene.json')
        for name in ('upper_gallery','upper_master','upper_office','upper_guest','upper_terrace'):
            cam=scene['cameras'][name]
            assert cam['floor']==1 and cam['enter_walk']
            assert abs(cam['position'][2]-(3.508+1.63))<.001
        assert scene['lawns'] and all(l['heightScale']<=.5 for l in scene['lawns'])
        names={n['id'] for n in scene['nodes']}
        assert 'atrium-window-permanent-guard' in names
        assert any(n.startswith('terrace-guard-') for n in names)
        assert 'stair-headroom-rooflight-top' not in names
        assert scene['storeys']==2 and scene['bounds'][3:5]==[12.192,15.24]


def test_validator_detects_wrong_dimensions_instead_of_returning_fixed_pass():
    b = _load_sample_json("tirumala-2", "building.json")
    assert "g-care" in validate(b)["graph"]["g-living"]
    wrong = copy.deepcopy(b)
    wrong["brief"]["width_mm"] = 15000
    report = validate(wrong)
    assert report["status"] == "geometry_fail"
    assert any(e["id"] == "plot_dimensions_40x50ft" for e in report["errors"])


def test_room_geometry_uses_positions_and_holes_not_only_equal_areas():
    for slug in ("tirumala-2", "tirumala-3"):
        b = _load_sample_json(slug, "building.json")
        for source in b["planning"]["canonicalPlan"]["rooms"]:
            room = next(r for r in b["spaces"] if r["id"] == source["id"])
            actual = Polygon(room["clear"], room.get("holes", []))
            expected = Polygon(source["regions"][0]["outer"], source["regions"][0].get("holes", []))
            assert actual.symmetric_difference(expected).area < 1
        changed = copy.deepcopy(b)
        care = next(r for r in changed["spaces"] if r["id"] == "g-care")
        care["clear"] = [[x+100, y] for x,y in care["clear"]]
        assert validate(changed)["errors"]


def test_new_variants_do_not_inherit_old_upper_floor_cameras_or_bed_orientation():
    for slug, orientation in (("tirumala-2", "Head South, feet North"), ("tirumala-3", "Head West, feet East")):
        scene = _load_sample_json(slug, "scene.json")
        assert "upper_master_one" not in scene["cameras"]
        assert "first_floor_terrace_outlook" not in scene["cameras"]
        assert scene["context"]["care_room_verification"]["bed_orientation"] == orientation
        for name in ("interior_kitchen_living_dining", "interior_icu_veranda_garden"):
            cam = scene["cameras"][name]
            assert cam["enter_walk"] and cam["floor"] == 0
            assert cam["eye_height_above_ffl_m"] == 1.63


def _load_sample_json(slug: str, filename: str) -> dict:
    path = GALLERY_DIR / slug / filename
    assert path.exists(), f"Missing {slug}/{filename}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_catalog_contains_tirumala_2_and_tirumala_3_and_preserves_existing_samples():
    catalog = json.loads((GALLERY_DIR / "catalog.json").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in catalog}
    for required_existing in ("my-desired-home", "bungalow", "tirumala"):
        assert required_existing in by_id

    for slug in ("tirumala-2", "tirumala-3"):
        assert slug in by_id
        entry = by_id[slug]
        assert entry["bedrooms"] == 4
        assert entry["storeys"] == 2
        assert entry["widthFt"] == 40
        assert entry["depthFt"] == 50
        assert entry["roofAccess"] is False
        assert entry["terraceAccess"] is True
        assert entry["hasSpecifications"] is True
        b = _load_sample_json(slug, "building.json")
        assert entry["planHash"] == b["planHash"]


def test_authoritative_coordinates_and_common_approved_planning():
    for slug, expected_opt, expected_ver in (
        ("tirumala-2", "P12-A", "p12-open-porch-v33"),
        ("tirumala-3", "P11", "p11-veranda-return-trim-v32"),
    ):
        raw = load_authoritative_plan_data(slug)
        src = raw["plans"][0]
        b = _load_sample_json(slug, "building.json")
        assert b["planning"]["tirumalaOption"] == expected_opt
        assert src["version"] == expected_ver

        review = _load_sample_json(slug, "review.json")
        assert review["status"] == "preliminary_geometry_pass"
        assert review["errors"] == []
        assert review["warnings"] == []

        # 40 ft N-S (12,192 mm) x 50 ft E-W (15,240 mm), East road approach (90 deg), single-storey ground floor
        assert b["brief"]["width_mm"] == 12192
        assert b["brief"]["depth_mm"] == 15240
        assert b["brief"]["road_bearing_deg"] == 90
        assert b["storeys"] == 2
        assert b.get("rooftop") in (None, [], {})

        # The current ICU revision is checked explicitly below; other room polygons
        # must still match the preserved original source, in position as well as area.
        spaces_by_id = {s["id"]: s for s in b["spaces"]}
        for src_room in src["rooms"]:
            if src_room['id'] == 'g-care': continue
            sp = spaces_by_id[src_room["id"]]
            assert sp["floor"] == 0
            p_src = Polygon(src_room["regions"][0]["outer"])
            p_bld = Polygon(sp["clear"])
            assert p_src.symmetric_difference(p_bld).area < 1

        # Verify 8 ft x 6 ft Master Bathroom (2438.4 x 1828.8 mm) and Caregiver's internally accessed attached WC
        mbath = spaces_by_id["g-bath"]
        mb_bounds = Polygon(mbath["clear"]).bounds
        assert math.isclose(mb_bounds[2] - mb_bounds[0], 2438.4, abs_tol=1.0)
        assert math.isclose(mb_bounds[3] - mb_bounds[1], 1828.8, abs_tol=1.0)

        cwc_door = next(o for o in b["openings"] if o["id"] == "wc-caregiver-only")
        assert set(cwc_door["connects"]) == {"g-caregiver", "g-caregiver-bath"}

        # Verify Lightwell (1500 x 1650 mm) and Master Bedroom doorway (800 mm leaf in 1000 mm throat)
        lw_bounds = Polygon(spaces_by_id["g-care-court"]["clear"]).bounds
        assert math.isclose(lw_bounds[2] - lw_bounds[0], 1500.0, abs_tol=1.0)
        assert math.isclose(lw_bounds[3] - lw_bounds[1], 1650.0, abs_tol=1.0)
        m_door = next(o for o in b["openings"] if o["id"] == "master-door")
        assert math.isclose(m_door["width"], 800.0, abs_tol=1.0)

        # Verify Staircase climbing South -> West -> North
        stair = b["stairs"][0]
        assert [fl.get("direction") for fl in stair["flights"] if fl.get("direction")] == ["South", "West", "North"]
        assert stair["riser_count"] == 18

        # Verify Kitchen L-counter along store wall and east wall + short serving worktop, no fridge, no puja room
        assert len(src["counter"]) >= 4
        assert len(src["serving"]) == 4
        f_kinds = {f["kind"] for f in src["furniture"]}
        assert not any("fridge" in k or "refrigerator" in k or "puja" in k for k in f_kinds)
        assert not any("puja" in s["id"].lower() or "puja" in s["name"].lower() for s in b["spaces"])


def test_tirumala_2_p12_specific_requirements():
    src = load_authoritative_plan_data("tirumala-2")["plans"][0]
    b = _load_sample_json("tirumala-2", "building.json")
    spaces_by_id = {s["id"]: s for s in b["spaces"]}

    # 1. Notched Home ICU with corner returned to the lower porch
    icu_poly = Polygon(spaces_by_id["g-care"]["clear"])
    assert len(spaces_by_id["g-care"]["clear"]) == 6  # L-shaped notched polygon
    assert math.isclose(icu_poly.area / 92903.04, 158.627947589, abs_tol=.001)
    assert math.isclose(spaces_by_id['g-care']['bounds'][0], 6817.8, abs_tol=.01)
    current=b['planning']['canonicalPlan']
    for key in ('counter','serving','stairs','lowerPorch','carBody','carEnvelope','gate'):
        assert current[key]==src[key],key
    assert math.isclose(next(o for o in b['openings'] if o['id']=='living-veranda')['width']-110,1057.8,abs_tol=.01)

    # 2. Lower porch footprint: 10 ft (3048 mm) across x 14 ft 3-1/4 in (4350 mm) main bay + ICU corner cut-out
    porch_poly = Polygon(src["lowerPorch"][0]["outer"])
    minx, miny, maxx, maxy = porch_poly.bounds
    assert math.isclose(maxx - minx, 3048.0, abs_tol=1.0)  # 10 ft across
    assert math.isclose(maxy, 4350.0, abs_tol=1.0)

    # 3. Veranda beside kitchen and in front of ICU: 11 ft 7-3/8 in (3541.6 mm) x 6 ft (1828.8 mm)
    ver_bounds = Polygon(spaces_by_id["g-veranda"]["clear"]).bounds
    assert math.isclose(ver_bounds[2] - ver_bounds[0], 3541.6, abs_tol=1.0)
    assert math.isclose(ver_bounds[3] - ver_bounds[1], 1828.8, abs_tol=1.0)

    # 4. Drawing room left completely unfurnished
    drawing_poly = Polygon(spaces_by_id["g-drawing"]["clear"])
    for item in src["furniture"]:
        f_box = box(*item["bounds"])
        assert drawing_poly.intersection(f_box).area == 0.0, f"Unexpected furniture {item['kind']} in P12 drawing room"

    # 5. Home ICU contains ONLY the recliner bed (head South, feet North) and corner table
    icu_furniture = [
        item for item in current["furniture"]
        if icu_poly.intersection(box(*item["bounds"])).area > 1000.0
    ]
    assert {item["kind"] for item in icu_furniture} == {"reclining-bed", "equipment-table"}
    icu_bed = next(item for item in icu_furniture if item["kind"] == "reclining-bed")
    bed_x0, bed_y0, bed_x1, bed_y1 = icu_bed["bounds"]
    assert math.isclose(bed_x1 - bed_x0, 2200.0, abs_tol=5.0)
    assert math.isclose(bed_y1 - bed_y0, 1100.0, abs_tol=5.0)


def test_tirumala_3_p13_extends_only_icu_into_forecourt():
    src = load_authoritative_plan_data("tirumala-3")["plans"][0]
    b = _load_sample_json("tirumala-3", "building.json")
    spaces_by_id = {s["id"]: s for s in b["spaces"]}

    # Rectangular ICU remains 11 ft 3 in N-S and extends 2 ft east, to 13 ft 4-7/8 in E-W.
    icu_poly = Polygon(spaces_by_id["g-care"]["clear"])
    icu_bounds = icu_poly.bounds
    assert math.isclose(icu_bounds[2] - icu_bounds[0], 3429.6, abs_tol=1.0)
    assert math.isclose(icu_bounds[3] - icu_bounds[1], 4085.6, abs_tol=1.0)
    assert math.isclose(icu_bounds[1]-150, 1524, abs_tol=.01)  # 5 ft forecourt
    current=b['planning']['canonicalPlan']
    assert b['planning']['tirumalaMeta']['displayOption']=='P13'
    for key in ('counter','serving','stairs','openFloor','lowerPorch','carBody','carEnvelope','gate','northGarden'):
        assert current[key]==src[key],key
    for op in current['openings']:
        old=copy.deepcopy(next(o for o in src['openings'] if o['id']==op['id']))
        if op['id']=='icu-east-window':
            old['a'][1]-=609.6;old['b'][1]-=609.6
        assert op==old,op['id']
    raised=unary_union([Polygon(r['outer']) for r in current['raisedForecourt']])
    assert raised.intersection(icu_poly).area<1
    assert icu_poly.intersection(Polygon(current['lowerPorch'][0]['outer'])).area<1
    assert math.isclose(icu_poly.area/92903.04,150.823630314,abs_tol=.01)

    # 2. Shortened small veranda return aligned to the ICU west exterior wall (y = 5760.0 mm)
    porch_gain = Polygon(src["porchGain"][0]["outer"]).bounds
    assert math.isclose(porch_gain[3] - porch_gain[1], 609.6, abs_tol=1.0)  # 2 ft shortened return

    # Drawing furniture and full-size recliner are preserved; two ICU chairs and
    # the tall cabinet are removed, with compact closed storage at the east corner.
    drawing_poly = Polygon(spaces_by_id["g-drawing"]["clear"])
    drawing_items = [item for item in src["furniture"] if drawing_poly.intersection(box(*item["bounds"])).area > 1000.0]
    assert len(drawing_items) >= 3
    assert [f for f in current['furniture'] if f['room_id']=='g-drawing']==[f for f in src['furniture'] if f['room_id']=='g-drawing']
    icu_items = [f for f in current['furniture'] if f['room_id']=='g-care']
    assert {f['kind'] for f in icu_items}=={'reclining-bed','care-chair-right','equipment-table','large-tv'}
    for f in icu_items: assert icu_poly.covers(Polygon(f['polygon']))
    bed=next(f for f in icu_items if f['kind']=='reclining-bed')['bounds']
    assert math.isclose(bed[2]-bed[0],1100,abs_tol=.01)
    assert math.isclose(bed[3]-bed[1],2200,abs_tol=.01)
    assert bed[1]-icu_bounds[1]>900 and icu_bounds[3]-bed[3]>900


def test_provisional_porch_drop_and_flooring_glazing_materials():
    for slug in ("tirumala-2", "tirumala-3"):
        scene = _load_sample_json(slug, "scene.json")
        spec = _load_sample_json(slug, "specifications.json")

        # 1. Provisional 6-inch (152.4 mm) porch drop
        assert math.isclose(spec["floorLevelsMm"]["provisional_porch_drop_mm"], PROVISIONAL_PORCH_DROP_MM, abs_tol=0.1)
        assert math.isclose(spec["floorLevelsMm"]["provisional_porch_drop_in"], 6.0, abs_tol=0.05)

        # Verify lower porch nodes sit at z_porch = -0.1524 m while raised house/veranda/forecourt nodes sit at z = 0.000 m
        nodes_by_id = {n["id"]: n for n in scene["nodes"] if "id" in n}
        assert "lower-porch-kota-paver" in nodes_by_id
        assert "lower-porch-red-oxide-border" in nodes_by_id
        assert "raised-forecourt-tile-0" in nodes_by_id

        # 2. Large-format 24x48 in (2.4384 x 1.2192 m 2x2 tile repeat) white/cream marble flooring & Kota/red-oxide porch
        mats = scene["materials"]
        assert "ivory-marble-polished" in mats
        assert "ivory-marble-exterior-matte" in mats
        assert "porch-kota-paver" in mats
        assert "porch-red-oxide-border" in mats
        assert mats["ivory-marble-polished"]["tile_m"] == [2.4384, 1.2192]
        assert mats["ivory-marble-exterior-matte"]["tile_m"] == [2.4384, 1.2192]

    # 3. Verify adjustable porch drop is strictly separate from horizontal dimensions
    p_default = build_p11_p12_project("tirumala-2", porch_drop_mm=152.4)
    p_custom = build_p11_p12_project("tirumala-2", porch_drop_mm=101.6)  # 4-inch test drop
    b_default = generate_layout(fuse(p_default))
    b_custom = generate_layout(fuse(p_custom))
    assert b_default["spaces"] == b_custom["spaces"]
    assert b_default["walls"] == b_custom["walls"]
    assert b_default["openings"] == b_custom["openings"]


def test_all_deliverable_renders_and_exports_exist():
    required_renders = [
        "renders/plan-2d-dimensioned.svg",
        "renders/plan-2d-dimensioned.png",
        "renders/plan-2d-material-overhead.svg",
        "renders/plan-2d-material-overhead.png",
        "renders/exterior-east.png",
        "renders/exterior-northeast.png",
        "renders/cutaway-3d-roof-off.png",
        "renders/interior-kitchen-living-dining.png",
        "renders/interior-icu-veranda-garden.png",
        "renders/closeup-flooring-glazing-lower-porch.png",
    ]
    for slug in ("tirumala-2", "tirumala-3", "tirumala-4"):
        sample_dir = GALLERY_DIR / slug
        for rel in required_renders:
            f = sample_dir / rel
            assert f.exists() and f.stat().st_size > 1000, f"Missing or empty render {slug}/{rel}"
        thumb = GALLERY_DIR / "thumbnails" / f"{slug}.png"
        assert thumb.exists() and thumb.stat().st_size > 1000, f"Missing thumbnail for {slug}"


def test_tirumala_4_site_calibrated_p13_and_evidence_hygiene():
    b3 = _load_sample_json("tirumala-3", "building.json")
    b4 = _load_sample_json("tirumala-4", "building.json")
    s3 = _load_sample_json("tirumala-3", "specifications.json")
    s4 = _load_sample_json("tirumala-4", "specifications.json")
    sc4 = _load_sample_json("tirumala-4", "scene.json")
    ctx4 = _load_sample_json("tirumala-4", "site-context.json")
    pm4 = _load_sample_json("tirumala-4", "photo-reference-manifest.json")
    ar4 = _load_sample_json("tirumala-4", "assumptions-register.json")

    # 1. Exact locked P13 house geometry preserved from Tirumala 3
    assert s4["basedOnSample"] == "tirumala-3"
    assert s4["sourcePlanHash"] == b3["planHash"]
    assert s4["geometryHash"] == s3["geometryHash"]
    assert b4["spaces"] == b3["spaces"]
    assert b4["walls"] == b3["walls"]
    assert b4["openings"] == b3["openings"]
    assert b4["stairs"] == b3["stairs"]
    assert b4["planning"]["canonicalPlan"] == b3["planning"]["canonicalPlan"]
    assert b4["planning"]["upperPlan"] == b3["planning"]["upperPlan"]

    # 2. Default car porch empty (defaultCarVisible=False) while retaining vehicle nodes for optional parking check
    assert s4["defaultCarVisible"] is False
    assert sc4["defaultCarVisible"] is False
    assert any(n.get("owner") == "parked-car" for n in sc4["nodes"])

    # 3. Evidence hygiene: R11 duplicate photo discrepancy, V06 camera-roll note, and Existing-vs-Proposed site modes
    assert pm4["duplicateAnnotationDiscrepancy"]["referenceId"] == "R11"
    assert pm4["duplicateAnnotationDiscrepancy"]["sourcePhoto"] == "1000145311.jpg"
    assert "rollCaution" in pm4["videoPanCaution"]
    assert ctx4["siteModes"]["default"] == "proposed"
    assert set(ctx4["siteModes"]["available"]) == {"proposed", "existing"}
    assert len(s4["clearanceAudit"]) >= 9
    assert len(ctx4["measuredClearanceAuditMm"]) >= 9
    assert any(f["id"] == "A-12" for f in ar4["items"])

    # 4. Tirumala 4 specific deliverables & reference comparisons exist
    t4_dir = GALLERY_DIR / "tirumala-4"
    for extra in (
        "renders/site-context-plan.svg",
        "renders/site-context-plan.png",
        "renders/veranda-north-garden-outlook.png",
        "renders/interior-icu-recliner-sightline.png",
        "renders/interior-living-sofa-sightline.png",
        "renders/ref-r07-east-northwest.png",
        "renders/ref-r07-existing-plot.png",
        "renders/ref-r11-ne-corner.png",
        "renders/ref-r08-north-garden.png",
        "renders/ref-v01-east-court-road.png",
        "renders/ref-r09-colony-junction.png",
        "renders/ref-r14-wall-pole-paving.png",
        "renders/reference-comparison-sheet.png",
        "renders/tirumala-3-vs-4-comparison.png",
    ):
        p = t4_dir / extra
        assert p.exists() and p.stat().st_size > 1000, f"Missing Tirumala 4 deliverable {extra}"
