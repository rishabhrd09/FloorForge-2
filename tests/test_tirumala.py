"""Automated verification tests for the Tirumala Revision 10 sample project (id: 'tirumala', Options A–E)."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon

from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.tirumala_context import (
    PLOT_AREA_M2,
    build_assumptions_register,
    build_photo_reference_manifest,
    build_tirumala_context,
    geo_bearing_to_walker_yaw,
    geo_to_local_mm,
    geo_to_scene_m,
    local_mm_to_geo_m,
    scene_to_geo_m,
)
from floorforge.tirumala_rev10 import OPTIONS, build_option_project, canonical_handoff_zones
from scripts.build_tirumala import check_tirumala, project

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "examples" / "gallery" / "tirumala"
EVIDENCE_DIR = ROOT / "evidence" / "tirumala"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_tirumala_site_dimensions_orientation_and_coordinate_transforms():
    p = project("A")
    b = generate_layout(fuse(p))
    v = b["brief"]
    # East frontage = 40 ft (12192 mm S-N), North/South boundaries = 50 ft (15240 mm E-W), East-facing (90 deg)
    assert v["width_mm"] == 12192
    assert v["depth_mm"] == 15240
    assert math.isclose(v["width_mm"] / 40.0, 304.8, abs_tol=1e-6)
    assert math.isclose(v["depth_mm"] / 50.0, 304.8, abs_tol=1e-6)
    assert v["road_bearing_deg"] == 90
    assert v["plinth_mm"] == 300
    assert v["floor_height_mm"] == 3658
    assert round((v["width_mm"] * v["depth_mm"]) / 1e6, 3) == round(PLOT_AREA_M2, 3) == 185.806

    # Plot corners in geographic coordinates: SW(0,0), SE(15.240,0), NW(0,12.192), NE(15.240,12.192)
    ctx = build_tirumala_context(b)
    corners = ctx["coordinate_system"]["plot_corners_geo_m"]
    assert corners["SW"] == [0.0, 0.0]
    assert corners["SE"] == [15.24, 0.0]
    assert corners["NW"] == [0.0, 12.192]
    assert corners["NE"] == [15.24, 12.192]

    # Round-trip geographic <-> plan mm and geographic <-> scene m transformations
    for x_geo, y_geo, z_geo in [
        (0.0, 0.0, 0.0),
        (15.24, 0.0, 0.0),
        (0.0, 12.192, 0.0),
        (15.24, 12.192, 0.30),
        (7.62, 6.096, 1.65),
    ]:
        xp, yp = geo_to_local_mm(x_geo, y_geo)
        xg2, yg2 = local_mm_to_geo_m(xp, yp)
        assert math.isclose(x_geo, xg2, abs_tol=1e-3)
        assert math.isclose(y_geo, yg2, abs_tol=1e-3)

        xs, ys, zs = geo_to_scene_m(x_geo, y_geo, z_geo)
        xg3, yg3, zg3 = scene_to_geo_m(xs, ys, zs)
        assert math.isclose(x_geo, xg3, abs_tol=1e-4)
        assert math.isclose(y_geo, yg3, abs_tol=1e-4)
        assert math.isclose(z_geo, zg3, abs_tol=1e-4)

    # Bearing to walker yaw check: North (0 deg) -> +x_scene (yaw = -pi/2), East (90 deg) -> -y_scene (yaw = +/-pi)
    assert math.isclose(geo_bearing_to_walker_yaw(0.0), -math.pi / 2, abs_tol=1e-5)
    assert math.isclose(abs(geo_bearing_to_walker_yaw(90.0)), math.pi, abs_tol=1e-5)


def test_tirumala_all_five_options_A_to_E_and_manifest():
    assert list(OPTIONS.keys()) == ["A", "B", "C", "D", "E"]
    manifest_path = SAMPLE_DIR / "options-manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["revision"] == 10
    assert manifest["defaultOption"] == "A"
    assert [o["code"] for o in manifest["options"]] == ["A", "B", "C", "D", "E"]

    expected_specs = {
        "A": (192.0, [11.0, 10.0], 51.0, 5.5),
        "B": (224.5, [11.0, 10.0], 51.0, 3.5),
        "C": (179.5, [11.0, 10.0], 51.0, 6.5),
        "D": (179.5, [11.0, 12.0], 51.0, 4.5),
        "E": (192.0, [11.0, 10.0], 52.0, 5.0),
    }
    plan_hashes = set()
    geom_hashes = set()
    for item in manifest["options"]:
        code = item["code"]
        assert (item["careSqFt"], item["drawingFt"], item["caregiverSqFt"], item["verandaDepthFt"]) == expected_specs[code]
        plan_hashes.add(item["planHash"])
        geom_hashes.add(item["geometryHash"])

        b = json.loads((SAMPLE_DIR / "variants" / code / "building.json").read_text(encoding="utf-8"))
        review = validate(b)
        assert review["status"] == "preliminary_geometry_pass"
        assert not review["errors"]
        assert not review["warnings"]

    assert len(plan_hashes) == 5
    assert len(geom_hashes) == 5


def test_compact_corner_stair_and_east_stair_window():
    for code in OPTIONS:
        b = json.loads((SAMPLE_DIR / "variants" / code / "building.json").read_text(encoding="utf-8"))
        cz = canonical_handoff_zones(code)
        st = b["stairs"][0]
        assert st["shape"] == "quarter-turn"
        assert st["rise_direction"] == "south-east"
        assert st["open_arrival"] is True
        assert st["riser_count"] == 20
        assert math.isclose(st["riser_mm"], 182.9, abs_tol=0.1)
        assert math.isclose(st["tread_mm"], 287.89, abs_tol=0.1)
        assert st["flight_width"] == 1067
        assert st["well"] == 0
        assert st["landing_mm"] == 1067
        assert math.isclose(st["width"], 3658.0, abs_tol=0.1)
        assert math.isclose(st["depth"], 3658.0, abs_tol=0.1)

        # Upper arrival must stay outside the double-height living void
        u_void = Polygon(next(s["polygon"] for s in b["spaces"] if s["id"] == "u-living-void"))
        upper_arrival = Polygon(cz["canonicalZones"]["upperStairArrival"])
        assert u_void.intersection(upper_arrival).area == 0.0

        # Tall East-facing stair window overlooking the 3.5 ft clear south lane
        stair_win = next(o for o in b["openings"] if o["id"] == "g-stair-east-window")
        assert stair_win["kind"] == "window"
        assert stair_win["width"] == 990
        assert stair_win["sill"] == 350
        assert stair_win["height"] == 2500
        assert set(stair_win["connects"]) == {"g-stair", "g-south-lane"}


def test_connected_ground_floor_double_height_void_and_porch():
    b = json.loads((SAMPLE_DIR / "variants" / "A" / "building.json").read_text(encoding="utf-8"))
    scene = json.loads((SAMPLE_DIR / "variants" / "A" / "scene.json").read_text(encoding="utf-8"))
    spaces = {s["id"]: s for s in b["spaces"]}

    # Shallow 11 x 3 ft open-to-sky porch
    porch = spaces["g-porch"]
    assert porch["openToSky"] is True
    assert porch["roofed"] is False

    # Screened East-wall puja alcove (worshipper facing East)
    puja = spaces["g-puja"]
    assert puja["altarWall"] == "front"

    # Open interfaces connecting kitchen, puja, stair and family hall
    open_ids = {o["id"] for o in b["openings"] if o["kind"] == "cased" and o.get("openSide")}
    assert {"g-kitchen-open-north", "g-puja-open", "g-stair-open-arrival", "g-stair-inner-west", "g-stair-inner-south"} <= open_ids

    # Double-height living void and rooflight + custom datum finishes
    u_void = spaces["u-living-void"]
    assert u_void["kind"] == "void"
    node_ids = {n["id"] for n in scene["nodes"]}
    for req_id in (
        "east-front-court/main-slab",
        "east-entrance-steps/step-1",
        "east-entrance-steps/step-2",
        "lower-parking-bay/slab",
        "north-clear-passage/walkway",
        "nw-open-garden/lawn",
        "living-void-rooflight/glass",
    ):
        assert req_id in node_ids


def test_spacious_revision_room_gains_and_furniture_clearances():
    """Area gains are real; neither tiny furniture nor a stretched plot earns a pass."""
    from shapely.geometry import box
    for code in OPTIONS:
        b = json.loads((SAMPLE_DIR / 'variants' / code / 'building.json').read_text())
        scene = json.loads((SAMPLE_DIR / 'variants' / code / 'scene.json').read_text())
        rooms = {r['id']: r for r in b['spaces']}
        assert b['planning']['tirumalaRevision'] == 10
        assert 120 < rooms['g-kitchen']['area_m2'] / .09290304 < 122
        lane=Polygon(rooms['g-south-lane']['clear']).bounds
        assert math.isclose(lane[2]-lane[0],1067,abs_tol=1)
        assert rooms['g-drawing']['area_m2'] / .09290304 > (131 if code == 'D' else 109)
        assert rooms['u-master']['area_m2'] / .09290304 > 176
        assert rooms['u-lobby']['area_m2'] / .09290304 > 370
        assert rooms['u-living-void']['area_m2'] / .09290304 > (43 if code == 'D' else 55)
        assert math.isclose(rooms['g-care']['area_m2'] / .09290304, OPTIONS[code]['careSqFt'], abs_tol=.4)
        for item in scene['furniture']:
            if item['kind']!='serving-counter' and item['room_id'] in ('g-kitchen', 'g-family', 'g-drawing', 'u-master', 'u-master-2', 'u-lobby', 'u-study'):
                footprint = Polygon(np.asarray(item['footprint']) * 1000)
                assert Polygon(rooms[item['room_id']]['clear']).buffer(10).covers(footprint), item['id']
        assert any(item['room_id'] == 'u-study' and item['kind'] == 'desk' for item in scene['furniture'])
        # Broad open kitchen work aisle, plus the unoccupied north stair approach.
        kitchen_aisle = box(7.2*.3048, 11.3*.3048, 13.8*.3048, 16.8*.3048)
        stair_approach = box(13.05*.3048, 28.7*.3048, 16*.3048, 31.7*.3048)
        for item in scene['furniture']:
            if rooms[item['room_id']]['floor']!=0:continue
            assert Polygon(item['footprint']).intersection(kitchen_aisle).area < .001
            assert Polygon(item['footprint']).intersection(stair_approach).area < .001
        openings = {o['id']: o for o in b['openings']}
        assert openings['g-drawing-door']['width'] >= 2590
        assert openings['g-care-hall-slider']['height'] == 3000
        assert (openings['u-lobby-terrace-door']['width']-100)/2-40 >= 670
        assert set(openings['u-lobby-terrace-door']['connects']) == {'u-lobby','u-terrace'}
        assert set(openings['u-master-terrace-door']['connects']) == {'u-master-2','u-terrace'}


def test_spacious_rooflight_is_an_actual_roof_and_ceiling_aperture():
    from floorforge.custom_plan import geometry
    from floorforge.scene import transformation
    for code in OPTIONS:
        b = json.loads((SAMPLE_DIR / 'variants' / code / 'building.json').read_text())
        scene = json.loads((SAMPLE_DIR / 'variants' / code / 'scene.json').read_text())
        roof = b['roofs'][-1]
        light = geometry(roof['rooflight'])
        void = Polygon(next(s['clear'] for s in b['spaces'] if s['id'] == 'u-living-void'))
        assert void.covers(light)
        assert geometry(roof['regions']).intersection(light).area < 1
        assert geometry(roof['ceiling']).intersection(light).area < 1
        # Check actual opaque triangles, so a metadata-only cut cannot pass.
        checked = 0
        for node in scene['nodes']:
            if node['floor'] != 1 or node['role'] not in ('roof', 'ceiling'):
                continue
            asset = scene['assets'][node['asset']]
            vertices = np.asarray(asset['vertices'])
            world = (np.c_[vertices, np.ones(len(vertices))] @ transformation(node).T)[:, :3] * 1000
            for face in asset['faces']:
                triangle = world[face]
                if triangle[:, 2].min() > 6900:
                    checked += 1
                    assert Polygon(triangle[:, :2]).intersection(light.buffer(-5)).area < 1
        assert checked > 0


def test_interior_presets_are_at_human_height_and_clear_of_furniture():
    from shapely.geometry import Point
    from shapely.ops import unary_union
    for code in OPTIONS:
        folder = SAMPLE_DIR / 'variants' / code
        b = json.loads((folder / 'building.json').read_text())
        scene = json.loads((folder / 'scene.json').read_text())
        room_floors = {r['id']: r['floor'] for r in b['spaces']}
        cameras = [c for c in scene['cameras'].values() if c.get('enter_walk')]
        assert len(cameras) == 12
        for camera in cameras:
            x, y, z = camera['walker']['position']
            floor = camera['floor']
            assert math.isclose(z - floor * 3.658, 1.60, abs_tol=.001)
            assert camera['fov'] == 62
            rooms = unary_union([Polygon(r['clear']) for r in b['spaces']
                                 if r['floor'] == floor and (r['enclosed'] or r['kind']=='terrace') and r['kind'] != 'void'])
            assert rooms.buffer(5).covers(Point(x * 1000, y * 1000)), camera['id']
            body = Point(x, y).buffer(.27)
            for item in scene['furniture']:
                if room_floors[item['room_id']] == floor:
                    assert Polygon(item['footprint']).intersection(body).area < .00001, (camera['id'], item['id'])


def test_care_suite_bed_sightlines_and_open_nw_garden_across_options():
    for code in OPTIONS:
        b = json.loads((SAMPLE_DIR / "variants" / code / "building.json").read_text(encoding="utf-8"))
        scene = json.loads((SAMPLE_DIR / "variants" / code / "scene.json").read_text(encoding="utf-8"))
        cz = canonical_handoff_zones(code)

        # Care bed: 7 x 3.5 ft (2134 x 1067 mm), head SOUTH (x=26.25 ft=8001 mm), feet NORTH (x=33.25 ft=10135 mm)
        care_beds = [f for f in scene["furniture"] if f["room_id"] == "g-care" and f["kind"] in ("reclining-bed", "bed")]
        assert len(care_beds) == 1
        bed_fp = np.asarray(care_beds[0]["footprint"], dtype=float) * 1000.0
        bx0, by0 = bed_fp.min(axis=0)
        bx1, by1 = bed_fp.max(axis=0)
        assert math.isclose(bx1 - bx0, 2134.0, abs_tol=5.0)
        assert math.isclose(by1 - by0, 1067.0, abs_tol=5.0)
        assert math.isclose(bx0, 8001.0, abs_tol=5.0)
        assert math.isclose(bx1, 10135.0, abs_tol=5.0)

        # Broad full-height North window and 6.5 ft East window in g-care
        care_openings = {o["id"]: o for o in b["openings"] if "g-care" in o["connects"]}
        assert "g-care-north-window" in care_openings
        assert care_openings["g-care-north-window"]["sill"] == 150
        assert care_openings["g-care-north-window"]["height"] == 3000
        assert "g-care-east-window" in care_openings
        assert care_openings["g-care-east-window"]["sill"] == 450
        assert care_openings["g-care-east-window"]["height"] == 2700
        assert "g-care-hall-slider" in care_openings
        assert "g-care-veranda-slider" in care_openings

        # Open NW garden must remain free of any enclosed ground-floor or first-floor rooms
        nw_garden = Polygon(cz["canonicalZones"]["garden"])
        assert nw_garden.area > 3_000_000  # > 3 m2 open NW corner garden pocket in every option
        for s in b["spaces"]:
            if s["enclosed"]:
                assert Polygon(s["polygon"]).intersection(nw_garden).area == 0.0, (
                    f"Option {code}: enclosed room {s['id']} encroaches into open NW garden"
                )


def test_six_reference_photographs_and_assumptions_register():
    manifest = build_photo_reference_manifest()
    assert len(manifest["photos"]) == 6
    expected_ids = {"N-01", "N-02", "N-03", "N-04", "NE-01", "E-01"}
    assert {item["id"] for item in manifest["photos"]} == expected_ids

    for item in manifest["photos"]:
        sample_ref = SAMPLE_DIR / item["reference_asset_path"]
        evidence_ref = ROOT / item["evidence_asset_path"]
        assert sample_ref.exists() and sample_ref.stat().st_size > 10000
        assert evidence_ref.exists() and evidence_ref.stat().st_size > 10000
        assert _sha256(sample_ref) == _sha256(evidence_ref)

    reg = build_assumptions_register()
    for section in (
        "owner_confirmed_facts",
        "directly_visible_photo_features",
        "estimated_dimensions_and_placements",
        "provisional_photo_assignments",
        "unknowns_requiring_site_measurement",
    ):
        assert section in reg and len(reg[section]) > 0


def test_generated_sample_bundle_and_colony_context_isolation():
    assert check_tirumala() == 0
    required_files = [
        "project.floorforge.json",
        "specifications.json",
        "DESIGN_GUIDE.md",
        "intent.json",
        "building.json",
        "scene.json",
        "report.json",
        "review.json",
        "sheets.json",
        "drawings.pdf",
        "floorplans.dxf",
        "model.glb",
        "model.ifc",
        "export-checks.json",
        "manifest.json",
        "preview.html",
        "REVIEW_BEFORE_USE.txt",
        "FloorForge-export.zip",
        "site-context.json",
        "photo-reference-manifest.json",
        "assumptions-register.json",
    ]
    for rel in required_files:
        assert (SAMPLE_DIR / rel).exists(), f"Missing required sample output: {rel}"
        for code in OPTIONS:
            assert (SAMPLE_DIR / "variants" / code / rel).exists(), f"Missing {rel} in variant {code}"

    scene = json.loads((SAMPLE_DIR / "scene.json").read_text(encoding="utf-8"))
    assert scene.get("context", {}).get("style") == "tirumala-colony"
    assert scene["context"]["roads"]["north_road_12m"]["total_row_m"] == 12.0
    assert scene["context"]["roads"]["east_road_9m"]["total_row_m"] == 9.0
    assert "smaller_east_cabinet" in scene["context"]["northwest_feeder_cabinets"]
    assert "taller_west_cabinet" in scene["context"]["northwest_feeder_cabinets"]
    assert "N-01" in scene["cameras"]
    assert "E-01" in scene["cameras"]
    assert "care_seated_north" in scene["cameras"]
    assert "care_east_court_glimpse" in scene["cameras"]

    # Colony context must NOT pollute building-only scene nodes, model.ifc, or report.json areas
    node_roles = {n.get("role") for n in scene["nodes"]}
    assert "colony-context" not in node_roles
    report = json.loads((SAMPLE_DIR / "report.json").read_text(encoding="utf-8"))
    assert report["areas"]["plot_m2"] == 185.806

    # Sheet A-001 must render the Tirumala site context overlay & required section sheets A-301 and A-302 must exist
    a001 = (SAMPLE_DIR / "sheets" / "A-001.svg").read_text(encoding="utf-8")
    for label in (
        "NORTH ROAD — 12.0 m ROW",
        "EAST ROAD — 9.0 m ROW",
        "BASKETBALL-COURT ENCLOSURE",
        "OPPOSITE NORTH COLONY GARDEN",
        "2x NW FEEDER CABINETS",
    ):
        assert label in a001, f"Missing '{label}' in sheets/A-001.svg"
    assert (SAMPLE_DIR / "sheets" / "A-301.svg").exists()
    assert (SAMPLE_DIR / "sheets" / "A-302.svg").exists()

    corr_path = EVIDENCE_DIR / "rev10-2d-3d-correspondence.json"
    assert corr_path.exists()
    corr = json.loads(corr_path.read_text(encoding="utf-8"))
    assert corr["allPassed"] is True
    assert len(corr["options"]) == 5


def test_existing_samples_and_baseline_files_preserved_unchanged():
    baseline_path = EVIDENCE_DIR / "baseline-manifest.json"
    assert baseline_path.exists()
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    # Every existing sample file and evidence file must match its exact pre-Tirumala SHA-256 hash
    for rel, expected_hash in baseline["files"].items():
        if rel == "examples/gallery/catalog.json":
            continue
        p = ROOT / rel
        assert p.exists(), f"Protected baseline file missing: {rel}"
        actual_hash = _sha256(p)
        assert actual_hash == expected_hash, f"Protected baseline file modified: {rel}"

    # Catalog must preserve all existing entries in exact order and content, adding 'tirumala' (and optional tirumala-2/tirumala-3)
    catalog_samples = json.loads((ROOT / "examples/gallery/catalog.json").read_text(encoding="utf-8"))
    if isinstance(catalog_samples, dict):
        catalog_samples = catalog_samples["samples"]
    baseline_entries = baseline.get("catalog_entries")
    if baseline_entries:
        assert len(catalog_samples) >= len(baseline_entries) + 1
        assert catalog_samples[: len(baseline_entries)] == baseline_entries
    tirumala_entry = next((e for e in catalog_samples if e["id"] == "tirumala"), None)
    assert tirumala_entry is not None
    assert tirumala_entry["title"] == "Tirumala"


def test_browser_evidence_captures_and_comparison_boards_present():
    current=EVIDENCE_DIR/'revision-10'
    for code in OPTIONS:
        for name in ('ground-plan','upper-plan','dollhouse','upper-dollhouse'):
            p=current/f'option-{code}-{name}.png'
            assert p.exists() and p.stat().st_size>1000
    pw=json.loads((current/'browser-checks.json').read_text())
    assert pw['revision']==10 and pw['errors']==[]
    assert all(c['pass'] for c in pw['checks'])
    assert len(pw['optionHashes'])==5


def test_l_stair_solids_are_the_plan_shape_with_continuous_rises():
    from floorforge.stair_geometry import footprint, quarter_parts, quarter_path
    from floorforge.plan_geometry import geometry
    from shapely.geometry import box
    from shapely.ops import unary_union
    for code in OPTIONS:
        b=generate_layout(fuse(build_option_project(code)));st=b['stairs'][0]
        stairs=footprint(st);parts=quarter_parts(st)
        actual=unary_union([box(a['bounds'][0],a['bounds'][1],a['bounds'][3],a['bounds'][4]) for a in parts])
        assert actual.symmetric_difference(stairs).area<1
        assert 71<stairs.area/92903.04<73
        assert math.isclose(Polygon(next(r['clear'] for r in b['spaces'] if r['id']=='g-stair')).area,stairs.area,abs_tol=1)
        assert geometry(b['floor_plates'][1]['regions']).intersection(stairs).area<1
        heights=sorted(a['bounds'][5] for a in parts)
        assert len(heights)==19
        for i,z in enumerate(heights,1):assert math.isclose(z,i*st['riser_mm'],abs_tol=.01)
        a,turn,c=quarter_path(st)
        assert a[0]>turn[0] and a[1]==turn[1] and c[0]==turn[0] and c[1]<turn[1]
        body=Polygon(next(r['clear'] for r in b['spaces'] if r['id']=='g-family'))
        assert body.contains(__import__('shapely').geometry.Point(10.5*304.8,25.1*304.8))


def test_upper_suites_shared_terrace_and_counter_have_real_connections():
    from floorforge.upper_floor import constraints
    from shapely.geometry import LineString
    for code in OPTIONS:
        p=build_option_project(code);b=generate_layout(fuse(p));rooms={r['id']:r for r in b['spaces']}
        assert constraints(p,1)['issues']==[]
        assert len([r for r in b['spaces'] if r['floor']==1 and r['kind']=='bedroom'])==2
        assert rooms['u-master-2']['area_m2']/.09290304>207
        assert 46<rooms['u-study']['area_m2']/.09290304<52
        assert 65<rooms['u-terrace']['area_m2']/.09290304<67
        links={frozenset(o['connects']) for o in b['openings'] if o['kind'] not in ('window',)}
        for a,c in [('u-lobby','u-master'),('u-lobby','u-master-2'),('u-lobby','u-study'),('u-master','u-bath'),('u-master-2','u-bath-2'),('u-lobby','u-terrace'),('u-master-2','u-terrace')]:
            assert frozenset([a,c]) in links
        counter=b['built_in_counters'][0]
        assert counter['height']==950
        assert set(counter['roomIds'])=={'g-kitchen','g-family'}
        assert max(y for x,y in rooms['g-kitchen']['clear'])<rooms['g-family']['diningPosition'][1]
        # Eye-level visibility has no opaque full wall along the kitchen-to-dining line.
        sight=LineString([(10.5*304.8,25.1*304.8),(10.5*304.8,18*304.8)])
        walls={w['id']:w for w in b['walls']}
        crossing=[w for w in b['walls'] if w['floor']==0 and LineString([w['a'],w['b']]).crosses(sight)]
        for wall in crossing:
            assert any(o['wall_id']==wall['id'] and o.get('openSide') for o in b['openings'])


def test_serving_platform_and_l_stair_export_use_actual_geometry():
    from shapely.geometry import box
    from shapely.ops import unary_union
    from floorforge.scene import transformation
    from floorforge.stair_geometry import footprint
    for code in OPTIONS:
        folder=SAMPLE_DIR/'variants'/code
        b=json.loads((folder/'building.json').read_text());scene=json.loads((folder/'scene.json').read_text())
        # Stair bounds must never overwrite the ground datum used by later site assets.
        car=next(n for n in scene['nodes'] if n['id']=='parked-car-body')
        assert math.isclose(car['position'][2],-.26,abs_tol=.001)
        assert scene['walk']['arrival']['position'][2] < .1
        furnishings={f['id']:f for f in scene['furniture']}
        counter=Polygon(furnishings['g-kitchen/serving-counter']['footprint'])
        dining=Polygon(furnishings['g-family/dining-set']['footprint'])
        assert counter.distance(dining)>=.60
        assert counter.intersection(Polygon(furnishings['g-kitchen/kitchen-fridge']['footprint'])).area<.00001
        assert counter.intersection(Polygon(furnishings['g-kitchen/kitchen-run']['footprint'])).area<.00001
        parts=[]
        for n in scene['nodes']:
            if n['role']!='stair' or n['floor']!=0:continue
            vertices=np.asarray(scene['assets'][n['asset']]['vertices'])
            world=(np.c_[vertices,np.ones(len(vertices))]@transformation(n).T)[:,:3]*1000
            parts.append(box(*world[:,:2].min(axis=0),*world[:,:2].max(axis=0)))
        assert len(parts)==19
        assert unary_union(parts).symmetric_difference(footprint(b['stairs'][0])).area<1
        ifc=(folder/'model.ifc').read_text()
        assert '.QUARTER_TURN_STAIR.' in ifc
        assert '.HALF_TURN_STAIR.' not in ifc


def test_l_stair_and_concave_opening_reject_inconsistent_inputs():
    import pytest
    from floorforge.model import DesignError
    p=build_option_project('A');p['customPlan']['stairs'][0]['landing']+=100
    with pytest.raises(DesignError) as exc:generate_layout(fuse(p))
    assert exc.value.details['errors'][0]['code']=='STAIR_LANDING'
    p=build_option_project('A')
    o=next(o for o in p['customPlan']['floors'][0]['openings'] if o['id']=='g-stair-inner-west')
    o['edgeIndex']=99
    with pytest.raises(DesignError) as exc:generate_layout(fuse(p))
    assert exc.value.details['errors'][0]['code']=='OPENING_EDGE'
