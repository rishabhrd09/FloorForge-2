#!/usr/bin/env python3
"""Build or finalize the two independent sample projects:
- 'tirumala-2' (based on finalized P12 / P12-A, version p12-open-porch-v33)
- 'tirumala-3' (based on finalized P11, version p11-veranda-return-trim-v32)

Preserves all existing sample projects (tirumala, my-desired-home, bungalow, etc.) untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.pipeline import deterministic_zip, run
from floorforge.review import validate
from floorforge.tirumala_context import (
    build_assumptions_register,
    build_photo_reference_manifest,
    build_tirumala_context,
)
from floorforge.tirumala_p11_p12 import (
    PROVISIONAL_PORCH_DROP_MM,
    build_p11_p12_project,
    load_authoritative_plan_data,
    render_dimensioned_2d_svg,
    render_material_overhead_2d_svg,
)

SAMPLES = {
    "tirumala-2": {
        "option_id": "P12-A",
        "source_version": "p12-open-porch-v33",
        "title": "Tirumala 2",
        "subtitle": "P12-A · Notched ICU, 10 × 14 ft 3¼ in Lower Open Porch, Front Veranda & Unfurnished Drawing Room",
        "style_label": "Large White/Cream Marble & Kota Porch (P12-A · Open Porch)",
        "description": (
            "East-facing 40 × 50 ft (2,000 sq ft) single-storey northeast corner home based on finalized P12 (P12-A, "
            "p12-open-porch-v33): notched Home ICU (136.2 sq ft) with South-to-North recliner bed and corner table, "
            "continuous 10 ft × 14 ft 3¼ in lower car porch / open lobby (-6 in provisional drop) in textured Kota stone "
            "with red-oxide border, 11 ft 7⅜ in × 6 ft front veranda beside the connected kitchen/living/dining hall, "
            "cleaned-up lobby entrance, unfurnished drawing room, 8 × 6 ft master bath, caregiver suite, and 24 × 48 in "
            "warm white/ivory marble flooring."
        ),
    },
    "tirumala-3": {
        "option_id": "P11",
        "source_version": "p11-veranda-return-trim-v32",
        "title": "Tirumala 3",
        "subtitle": "P11 · Rectangular ICU, Shortened Veranda Return, North Veranda & Lower Car Porch",
        "style_label": "Large White/Cream Marble & Kota Porch (P11 · Rectangular ICU)",
        "description": (
            "East-facing 40 × 50 ft (2,000 sq ft) single-storey northeast corner home based on finalized P11 "
            "(p11-veranda-return-trim-v32): rectangular Home ICU (11 ft 3 in × 11 ft 4⅞ in) with preserved bed/seating "
            "arrangement, 15 ft 7⅝ in × 6 ft 0⅞ in north veranda with shortened south return aligned to the ICU west wall, "
            "lower car porch (-6 in provisional drop) in textured Kota stone with red-oxide "
            "border, furnished drawing room, connected kitchen/living/dining hall, and 24 × 48 in warm white/ivory "
            "marble flooring."
        ),
    },
}

GALLERY_DIR = ROOT / "examples" / "gallery"
BRIEFS_DIR = GALLERY_DIR / "briefs"
CATALOG_PATH = GALLERY_DIR / "catalog.json"
COLONY_REF_DIR = ROOT / "evidence" / "tirumala" / "reference-assets"


def _design_guide(slug: str, spec: dict, site_context: dict, photo_manifest: dict, assumptions: dict) -> str:
    """Dimensional claims derive from the model rather than duplicated prose."""
    from floorforge.tirumala_p11_p12 import _mm_to_ft_in
    b = json.loads((GALLERY_DIR / slug / "building.json").read_text())
    plan = b["planning"]["canonicalPlan"]
    lines = [f"# {spec['title']} — {spec['option']} reference", "",
        f"Approved source: `{spec['sourceVersion']}`. Plot: **40 ft north–south × 50 ft east–west**. West is up and north is right in plan.", "",
        "Room, wall, opening, kitchen, stair and furniture footprints retain approved source coordinates. Sizes below are clear bounding spans; irregular rooms use polygon area.", "",
        "| Room | Clear bounding span (feet / inches) | Area (sq ft) |", "|---|---|---:|"]
    for room in b['spaces']:
        bounds = Polygon(room['clear']).bounds
        size = ' × '.join(_mm_to_ft_in(bounds[i+2]-bounds[i]) for i in range(2))
        lines.append(f"| {room['name']} | {size} | {room['area_m2'] / 0.09290304:.1f} |")
    lines += ["", "## Openings and kitchen", "",
        "Jambs reduce door aperture width by 110 mm. The bedroom entry recess is not the bedroom doorway.", "",
        "| Opening | Aperture | Clear between jambs |", "|---|---:|---:|"]
    for op in b['openings']:
        if op['sill'] == 0 and op['raw_kind'] != 'open-passage':
            lines.append(f"| {op['id']} | {_mm_to_ft_in(op['width'])} | {_mm_to_ft_in(op['width']-110)} |")
    serving=Polygon(plan['serving']).bounds; counter=Polygon(plan['counter']).bounds
    lines += ["", f"Serving worktop: {_mm_to_ft_in(serving[2]-serving[0])} × {_mm_to_ft_in(serving[3]-serving[1])}. L-counter remains along the store and east walls; east run: {_mm_to_ft_in(counter[2]-counter[0])}. No fridge or puja room.", "",
        "## Levels, stairs and finishes", "",
        f"House, veranda, forecourt and passages: 0 mm datum. Road: −300 mm. Car porch: −{spec['floorLevelsMm']['provisional_porch_drop_mm']} mm, an adjustable provisional 6-inch drop, independent of horizontal dimensions.", "",
        "Stairs retain 18 risers (2 south, 7 west, 9 north), each 175 mm, ending at 3150 mm. A raised glass rooflight over the upper flight and landing replaces the obstructing roof slab there; its top is 5250–5300 mm above the house datum, giving more than 2100 mm landing headroom. Main room ceiling height remains 3508 mm. This is an elevation repair, with the approved stair footprint unchanged. Ground-floor concept only; no upper-storey rooms are supplied.", "",
        "Large 24 × 48 in cream/ivory marble-look tiles: satin/polished indoors, coordinated matte exterior/wet finish on veranda and gullies. Lower porch: Kota-style pavers with red-oxide border. Charcoal framed glass, warm timber and a separate retractable insect screen.", "",
        "P12 keeps the drawing room empty and only its north-facing ICU recliner and corner table. P11 retains its approved furniture. ICU glass doors stack aside; store slider and hinged doors operate.", "",
        "The preview is real-time raster rendering, not a path-traced photograph. Room scale stays true; spaciousness comes from correct eye height, lighting and lens settings.", "",
        f"Plan hash: `{spec['planHash']}`. Geometry hash: `{spec['geometryHash']}`.", ""]
    return "\n".join(lines)


def build_single_sample(slug: str, finalize_only: bool = False) -> dict:
    """Build or finalize one sample project ('tirumala-2' or 'tirumala-3')."""
    meta = SAMPLES[slug]
    out_dir = GALLERY_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)

    # Preserve source-plan-data.json and reference-assets/ across rebuilds
    src_plan_data = load_authoritative_plan_data(slug)
    ref_dir = out_dir / "reference-assets"
    ref_dir.mkdir(parents=True, exist_ok=True)
    preserved_refs: dict[str, bytes] = {}
    for p_img in ref_dir.glob("*"):
        if p_img.is_file():
            preserved_refs[p_img.name] = p_img.read_bytes()

    p = build_p11_p12_project(slug)
    (BRIEFS_DIR / f"{slug}.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")

    if not finalize_only:
        b_check = generate_layout(fuse(p))
        review = validate(b_check)
        if review.get("errors") or review.get("warnings"):
            raise RuntimeError(f"{slug} validation failed: {json.dumps(review, indent=2)}")

        with tempfile.TemporaryDirectory(prefix=f"ff-{slug}-") as tmp:
            result = run(p, Path(tmp), use_cache=False)
            shutil.copytree(result["path"], out_dir, dirs_exist_ok=True)

        # Restore preserved source-plan-data.json and reference-assets
        (out_dir / "source-plan-data.json").write_text(json.dumps(src_plan_data, indent=2) + "\n", encoding="utf-8")
        ref_dir.mkdir(parents=True, exist_ok=True)
        for name, raw in preserved_refs.items():
            (ref_dir / name).write_bytes(raw)
        if COLONY_REF_DIR.exists():
            for img in sorted(COLONY_REF_DIR.glob("*.png")):
                shutil.copy2(img, ref_dir / img.name)

    b = json.loads((out_dir / "building.json").read_text(encoding="utf-8"))
    scene = json.loads((out_dir / "scene.json").read_text(encoding="utf-8"))
    site_context = build_tirumala_context(b, scene)
    site_context["project_id"] = slug
    photo_manifest = build_photo_reference_manifest()
    photo_manifest["project_id"] = slug
    assumptions = build_assumptions_register()
    assumptions["project_id"] = slug
    assumptions["title"] = f"{meta['title']} ({meta['option_id']}) — Evidence, Assumptions & Provisional Porch Drop Register"

    t_meta = b.get("planning", {}).get("tirumalaMeta") or {}
    spec = {
        "id": slug,
        "revision": 33 if meta["option_id"] == "P12-A" else 32,
        "option": meta["option_id"],
        "sourceVersion": meta["source_version"],
        "optionLabel": meta["style_label"],
        "optionTag": meta["subtitle"],
        "optionTrade": meta["description"],
        "title": meta["title"],
        "planHash": b["planHash"],
        "geometryHash": hashlib.sha256(json.dumps(b["planning"]["canonicalPlan"], sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "disclaimer": b["banner"],
        "orientation": "East road/front (40 ft = 12.192 m, y=0) · South left (x=0) · North 12 m road/right (50 ft = 15.240 m, x=12.192 m) · West rear (y=15.240 m). Overhead 2D plans show West at top and North on right.",
        "notes": p.get("notes") or p.get("brief", {}).get("notes") or meta["description"],
        "plotFt": [40, 50],
        "plotM": [12.192, 15.240],
        "plotAreaSqFt": 2000,
        "plotAreaM2": 185.806,
        "floorLevelsMm": {
            "road_ngl_mm": -300,
            "lower_car_porch_mm": -round(PROVISIONAL_PORCH_DROP_MM, 1),
            "provisional_porch_drop_mm": round(PROVISIONAL_PORCH_DROP_MM, 1),
            "provisional_porch_drop_in": 6.0,
            "provisional_porch_drop_status": "PROVISIONAL_ADJUSTABLE_SEPARATE_FROM_HORIZONTAL_DIMENSIONS",
            "house_veranda_forecourt_passages_mm": 0,
            "plinth_above_road_mm": 300,
            "floor_to_floor_mm": 3508,
            "clear_ceiling_mm": 3508,
        },
        "flooringSpecification": {
            "dominantInterior": {
                "material": "ivory-marble-polished",
                "moduleIn": [24, 48],
                "moduleMm": [609.6, 1219.2],
                "finish": "soft-satin / polished warm white-ivory vitrified marble with restrained natural veining",
                "appliesTo": ["g-living", "g-kitchen", "g-kitchen-store", "g-bedroom", "g-bath", "g-caregiver", "g-caregiver-bath", "g-access-lobby", "g-drawing", "g-care"],
            },
            "dominantExteriorAndWet": {
                "material": "ivory-marble-exterior-matte",
                "moduleIn": [24, 48],
                "moduleMm": [609.6, 1219.2],
                "finish": "coordinated non-slip exterior matte warm white-ivory vitrified marble",
                "appliesTo": ["g-veranda", "g-wash-gully", "raised-east-forecourt", "north-open-passage", "side-and-rear-walkways"],
            },
            "lowerCarPorch": {
                "material": "porch-kota-paver + porch-red-oxide-border",
                "finish": "traditional bungalow-inspired textured Kota stone / earthy geometric pavers with red-oxide border and inlay bands",
                "continuousAcrossNotchOrReturn": True,
                "appliesTo": ["g-porch"],
            },
        },
        "stairSpec": {
            "shape": "u-turn",
            "sequence": "Climb SOUTH -> WEST -> NORTH",
            "riserCount": 18,
            "flightWidthMm": 1100,
            "riserHeightMm": 175,
            "topLandingMm": 3150,
        },
        "coordinateSystem": site_context["coordinate_system"],
        "careRoomVerification": site_context["care_room_verification"],
        "referenceCameras": list(site_context["reference_cameras"].keys()),
        "sightlineCameras": list(site_context["sightline_cameras"].keys()),
        "rooms": [
            {
                "id": r["id"],
                "name": r["name"],
                "floor": r["floor"],
                "kind": r["kind"],
                "widthM": round((Polygon(r["clear"]).bounds[2] - Polygon(r["clear"]).bounds[0]) / 1000, 3),
                "depthM": round((Polygon(r["clear"]).bounds[3] - Polygon(r["clear"]).bounds[1]) / 1000, 3),
                "areaM2": r["area_m2"],
            }
            for r in b["spaces"]
        ],
    }

    (out_dir / "specifications.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    (out_dir / "site-context.json").write_text(json.dumps(site_context, indent=2) + "\n", encoding="utf-8")
    (out_dir / "photo-reference-manifest.json").write_text(json.dumps(photo_manifest, indent=2) + "\n", encoding="utf-8")
    (out_dir / "assumptions-register.json").write_text(json.dumps(assumptions, indent=2) + "\n", encoding="utf-8")
    (out_dir / "DESIGN_GUIDE.md").write_text(_design_guide(slug, spec, site_context, photo_manifest, assumptions), encoding="utf-8")

    # Generate high-resolution 2D SVG plans in renders/
    renders_dir = out_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    if not finalize_only:
        (renders_dir / "plan-2d-dimensioned.svg").write_text(render_dimensioned_2d_svg(b), encoding="utf-8")
        (renders_dir / "plan-2d-material-overhead.svg").write_text(render_material_overhead_2d_svg(b), encoding="utf-8")

    # Update manifest.json and FloorForge-export.zip to include all extra files and renders
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    extra_files = [
        "specifications.json",
        "DESIGN_GUIDE.md",
        "site-context.json",
        "photo-reference-manifest.json",
        "assumptions-register.json",
        "source-plan-data.json",
    ]
    if ref_dir.exists():
        for f in sorted(ref_dir.iterdir()):
            if f.is_file():
                extra_files.append(f"reference-assets/{f.name}")
    if renders_dir.exists():
        for f in sorted(renders_dir.iterdir()):
            if f.is_file():
                extra_files.append(f"renders/{f.name}")

    for name in extra_files:
        target = out_dir / name
        if target.exists():
            manifest["files"][name] = hashlib.sha256(target.read_bytes()).hexdigest()

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    files = {name: (out_dir / name).read_bytes() for name in manifest["files"] if (out_dir / name).exists()}
    files["manifest.json"] = (out_dir / "manifest.json").read_bytes()
    (out_dir / "FloorForge-export.zip").write_bytes(deterministic_zip(files))

    return {
        "slug": slug,
        "planHash": b["planHash"],
        "geometryHash": spec["geometryHash"],
        "outDir": str(out_dir),
    }


def update_catalog(built: dict[str, dict]) -> None:
    """Add or update tirumala-2 and tirumala-3 in examples/gallery/catalog.json while preserving all other entries."""
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    new_entries = {
        "tirumala-2": {
            "id": "tirumala-2",
            "title": "Tirumala 2",
            "description": SAMPLES["tirumala-2"]["description"],
            "style": SAMPLES["tirumala-2"]["style_label"],
            "directory": "gallery/tirumala-2",
            "bedrooms": 2,
            "storeys": 1,
            "widthFt": 40,
            "depthFt": 50,
            "roofAccess": False,
            "planHash": built["tirumala-2"]["planHash"],
            "hasSpecifications": True,
        },
        "tirumala-3": {
            "id": "tirumala-3",
            "title": "Tirumala 3",
            "description": SAMPLES["tirumala-3"]["description"],
            "style": SAMPLES["tirumala-3"]["style_label"],
            "directory": "gallery/tirumala-3",
            "bedrooms": 2,
            "storeys": 1,
            "widthFt": 40,
            "depthFt": 50,
            "roofAccess": False,
            "planHash": built["tirumala-3"]["planHash"],
            "hasSpecifications": True,
        },
    }

    updated: list[dict] = []
    seen: set[str] = set()
    for item in catalog:
        cid = item.get("id")
        if cid in new_entries:
            updated.append(new_entries[cid])
            seen.add(cid)
        else:
            updated.append(item)
    for cid in ("tirumala-2", "tirumala-3"):
        if cid not in seen:
            updated.append(new_entries[cid])

    CATALOG_PATH.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finalize-zip", action="store_true", help="Repackage manifest.json and FloorForge-export.zip after renders are captured.")
    args = parser.parse_args()

    # Clean up temporary smoke-test directories if present
    for tmp_p in (Path("/tmp/test_t2"), Path("/tmp/test_t3")):
        if tmp_p.exists():
            shutil.rmtree(tmp_p, ignore_errors=True)

    built = {}
    for slug in ("tirumala-2", "tirumala-3"):
        built[slug] = build_single_sample(slug, finalize_only=args.finalize_zip)
        print(f"Built {slug}: planHash={built[slug]['planHash']} -> {built[slug]['outDir']}")

    update_catalog(built)
    print("Updated examples/gallery/catalog.json with tirumala-2 and tirumala-3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
