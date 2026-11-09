"""Automated verification tests for the Tirumala Revision 8 sample project (id: 'tirumala', Options A–E)."""
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
from floorforge.tirumala_rev8 import OPTIONS, build_option_project, canonical_handoff_zones
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
    assert manifest["revision"] == 8
    assert manifest["defaultOption"] == "A"
    assert [o["code"] for o in manifest["options"]] == ["A", "B", "C", "D", "E"]

    expected_specs = {
        "A": (192.0, [10.0, 10.0], 51.0, 5.5),
        "B": (224.5, [10.0, 10.0], 51.0, 3.5),
        "C": (179.5, [10.0, 10.0], 51.0, 6.5),
        "D": (179.5, [10.0, 12.0], 51.0, 4.5),
        "E": (192.0, [10.0, 10.0], 52.0, 5.0),
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
        assert st["rotation"] == 90
        assert st["open_arrival"] is True
        assert st["riser_count"] == 20
        assert math.isclose(st["riser_mm"], 182.9, abs_tol=0.1)
        assert math.isclose(st["tread_mm"], 287.89, abs_tol=0.1)
        assert st["flight_width"] == 1067
        assert st["well"] == 152
        assert st["landing_mm"] == 1067
        assert math.isclose(st["width"], 2286.0, abs_tol=0.1)
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

    # Shallow 10 x 3 ft open-to-sky porch
    porch = spaces["g-porch"]
    assert porch["openToSky"] is True
    assert porch["roofed"] is False

    # Screened East-wall puja alcove (worshipper facing East)
    puja = spaces["g-puja"]
    assert puja["altarWall"] == "front"

    # Open interfaces connecting kitchen, puja, stair and family hall
    open_ids = {o["id"] for o in b["openings"] if o["kind"] == "cased" and o.get("openSide")}
    assert {"g-kitchen-open-north", "g-puja-open", "g-stair-open-arrival", "g-stair-open-west", "g-stair-open-east"} <= open_ids

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
        assert care_openings["g-care-north-window"]["height"] == 2400
        assert "g-care-east-window" in care_openings
        assert care_openings["g-care-east-window"]["sill"] == 450
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

    corr_path = EVIDENCE_DIR / "rev8-2d-3d-correspondence.json"
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

    # Catalog must preserve all existing entries in exact order and content, adding only 'tirumala'
    catalog_samples = json.loads((ROOT / "examples/gallery/catalog.json").read_text(encoding="utf-8"))
    if isinstance(catalog_samples, dict):
        catalog_samples = catalog_samples["samples"]
    baseline_entries = baseline.get("catalog_entries")
    if baseline_entries:
        assert len(catalog_samples) == len(baseline_entries) + 1
        assert catalog_samples[: len(baseline_entries)] == baseline_entries
    assert catalog_samples[-1]["id"] == "tirumala"
    assert catalog_samples[-1]["title"] == "Tirumala"


def test_browser_evidence_captures_and_comparison_boards_present():
    required_evidence = [
        "01-site-plan-north-up.png",
        "02-ground-floor-plan.png",
        "03-first-floor-plan.png",
        "03b-roof-terrace-plan.png",
        "03c-ground-3d-dollhouse.png",
        "03d-first-3d-dollhouse.png",
        "04-east-entrance-exterior.png",
        "05-ne-corner-both-roads.png",
        "06-care-room-interior.png",
        "07-care-room-north-seated-view.png",
        "07b-care-room-north-recliner-view.png",
        "07c-care-room-north-standing-view.png",
        "08-care-room-east-court-glimpse.png",
        "09-north-veranda-l-route.png",
        "10-kitchen-dining-connection.png",
        "11-caregiver-nw-open-pocket.png",
        "12-first-floor-terrace-outlook.png",
        "14-evening-exterior.png",
        "15-sample-gallery-with-tirumala.png",
        "option-A-2d-3d-overlay.png",
        "option-B-2d-3d-overlay.png",
        "option-C-2d-3d-overlay.png",
        "option-D-2d-3d-overlay.png",
        "option-E-2d-3d-overlay.png",
        "options-A-to-E-2d-3d-comparison.png",
        "ref-N-01-existing-site.png",
        "ref-N-01-proposed-home.png",
        "ref-N-01-comparison.png",
        "ref-N-02-existing-site.png",
        "ref-N-02-proposed-home.png",
        "ref-N-02-comparison.png",
        "ref-N-03-existing-site.png",
        "ref-N-03-proposed-home.png",
        "ref-N-03-comparison.png",
        "ref-N-04-existing-site.png",
        "ref-N-04-proposed-home.png",
        "ref-N-04-comparison.png",
        "ref-NE-01-existing-site.png",
        "ref-NE-01-proposed-home.png",
        "ref-NE-01-comparison.png",
        "ref-E-01-existing-site.png",
        "ref-E-01-proposed-home.png",
        "ref-E-01-comparison.png",
        "browser-checks.json",
    ]
    for name in required_evidence:
        p = EVIDENCE_DIR / name
        assert p.exists() and p.stat().st_size > 1000, f"Missing or empty evidence file: {name}"

    thumb = ROOT / "examples" / "gallery" / "thumbnails" / "tirumala.png"
    assert thumb.exists() and thumb.stat().st_size > 10000

    pw = json.loads((EVIDENCE_DIR / "browser-checks.json").read_text(encoding="utf-8"))
    assert pw["errors"] == []
    assert all(c["pass"] for c in pw["checks"])
