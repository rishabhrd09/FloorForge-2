#!/usr/bin/env python3
"""Build or verify the 'Tirumala' Revision 10 (Options A–E) 40 x 50 ft (2,000 sq ft) Northeast corner sample project.

Preserves every existing sample project and only writes Tirumala's own brief(s), sample directory
(including variants/A..E), evidence assets, and single catalogue entry.
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
    TIRUMALA_ID,
    build_assumptions_register,
    build_photo_reference_manifest,
    build_tirumala_context,
)
from floorforge.tirumala_rev10 import (
    OPTIONS, REVISION,
    all_option_projects,
    build_option_project,
    canonical_handoff_zones,
)

GALLERY_DIR = ROOT / "examples" / "gallery"
BRIEFS_DIR = GALLERY_DIR / "briefs"
OUT_DIR = GALLERY_DIR / TIRUMALA_ID
EVIDENCE_DIR = ROOT / "evidence" / TIRUMALA_ID
CATALOG_PATH = GALLERY_DIR / "catalog.json"


def tirumala_project(option: str = "A") -> dict:
    """Authoritative Revision-10 project payload for Tirumala (Options A–E)."""
    return build_option_project(option)


project = tirumala_project


def _design_guide(spec: dict, site_context: dict, photo_manifest: dict, assumptions: dict, options_summary: list[dict]) -> str:
    """Comprehensive DESIGN_GUIDE.md for Tirumala Revision 10 (Options A–E)."""
    care = site_context["care_room_verification"]
    lines = [
        f"# Tirumala Revision 10 — Option {spec['option']} ({spec['optionLabel']}) Design Guide & Colony Context Register",
        "",
        f"> **Preliminary Design Disclaimer:** {spec['disclaimer']}",
        "",
        "## 1. Site Overview, Confirmed Orientation & Coordinate System",
        "",
        "- **Project Name:** Tirumala (`id: tirumala`, Revision 10, Options A–E)",
        "- **Plot Classification:** Northeast (NE) corner plot with an **EAST-facing principal entrance** (`road_bearing_deg: 90`).",
        "- **Authoritative Conversion:** `1 ft = 304.8 mm` from the Southeast (SE) plot corner `(0, 0)`: `x` runs South-to-North `0..40 ft` (`0..12,192 mm`); `y` runs East-to-West `0..50 ft` (`0..15,240 mm`).",
        "- **Confirmed Boundaries:**",
        "  - **EAST frontage (Front, `y = 0`):** `40 ft 0 in = 12.192 m (12,192 mm)`, adjoining the **9.0 m East colony road** and **basketball-court enclosure & planting** beyond (`E-01`, `N-04`).",
        "  - **WEST boundary (Rear, `y = 15,240 mm`):** `40 ft 0 in = 12.192 m (12,192 mm)`.",
        "  - **NORTH boundary (Right, `x = 12,192 mm`):** `50 ft 0 in = 15.240 m (15,240 mm)`, adjoining the **12.0 m North colony road**, the **opposite colony garden** (lawn, raised planting kerb, pergola/seating, palms, slim lights), and the **two-storey white/grey house with dark blue-grey vertical facade** beyond (`N-01`, `N-02`, `N-03`).",
        "  - **SOUTH boundary (Left, `x = 0`):** `50 ft 0 in = 15.240 m (15,240 mm)`.",
        "- **Total Plot Area:** `2,000 sq ft = 185.806 m²`.",
        "",
        "## 2. Five Revision-10 Coordinated Alternatives (A–E)",
        "",
        "| Option | Title | Care Area (sq ft) | Drawing Size (ft) | Caregiver Area (sq ft) | Main Rear Veranda Depth (ft) | Geometry Hash | Plan Hash |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for o in options_summary:
        lines.append(
            f"| **`{o['option']}`** | {o['label']} | `{o['careSqFt']}` | `{o['drawingFt'][0]} × {o['drawingFt'][1]}` | "
            f"`{o['caregiverSqFt']}` | `{o['verandaDepthFt']}` | `{o['geometryHash'][:12]}` | `{o['planHash'][:12]}` |"
        )
    lines.extend([
        "",
        "## 3. Corner L Stair, Double-Height Living & Floor Levels",
        "",
        "- **L stair:** two perpendicular 1,067 mm wide flights and a square landing, climbing SOUTH then EAST. The 12 × 12 ft bounding box includes the dining corner; actual stair footprint is approximately 71.8 sq ft, not 144 sq ft.",
        "- **Risers & treads:** 20 equal rises over 3,658 mm, 18 treads at 287.89 mm, with the upper floor cut only over the L-shaped stair. The east upper arrival is outside the living void.",
        "- **Kitchen & dining:** approximately 121 sq ft kitchen, opening north to the hall and west to dining through a low 950 mm serving counter plus a clear passage. The 3.5 ft south daylight lane ends at the tall stair window.",
        "- **First floor:** two master suites, a compact office, a furnished common lounge, and a small open terrace with separate doors from the lounge and suite 2. A smaller double-height opening preserves the height and rooflight while allowing the larger upstairs accommodation.",
        "- **Floor Levels:** Continuous `+300 mm` datum across all ground-floor rooms, West veranda, `3 ft` shallow open-to-sky porch (`11 × 3 ft`), and `28 × 6.5 ft` East front court (`5.5 ft` standing depth behind two `150 mm` entrance rises at `y = 0.5..1.5 ft`). The `10.5 × 19 ft` Northeast car bay (`x = 29..39.5 ft, y = 0.5..19.5 ft`) remains at ground datum `±0 mm` (`300 mm` lower) with a `6.5 × 15.5 ft` reference car (`2 ft` side gaps, `1.75 ft` end gaps).",
        "",
        "## 4. Care Suite, Bed Orientation & Northwest Open Garden Verification",
        "",
        f"- **Care Bed (`7 × 3.5 ft`):** Head SOUTH (`x = 26.25 ft`), feet NORTH (`x = 33.25 ft`), preserving north-facing sightlines through broad full-height North glazing (`x = 36 ft`) across the `3 ft` clear North garden passage (`x = 36.5..39.5 ft`) to the 12 m road and opposite colony garden (`N-01`), plus the `6.5 ft` East window (`y = careFront`) toward the car court and East basketball enclosure (`E-01`).",
        f"- **Farthest West Care Edge:** `{care['care_west_edge_ft']} ft` from East frontage; Northwest garden remains open (`nw_garden_open = {care['nw_garden_open']}`).",
        "",
        "## 5. Six Reference Photographs & Camera Presets",
        "",
        "| ID | Original Suffix | Bearing | Confidence | Key Reproduced Features |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ])
    for p in photo_manifest["photos"]:
        feats = "; ".join(p["observed_features"][:2])
        lines.append(f"| **`{p['id']}`** | `{p['original_number_suffix']}` | `{p['bearing_deg']}°` | `{p['confidence']}` | {feats} |")
    lines.extend([
        "",
        "## 6. Room-by-Room Schedule (Option " + spec["option"] + ")",
        "",
        "| Floor | ID | Room Name | Kind | Clear Bounding Size (m) | Clear Area (m²) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])
    for r in spec["rooms"]:
        fl_label = ("Ground", "First")[r["floor"]] if r["floor"] < 2 else "Roof"
        lines.append(
            f"| `{fl_label}` | `{r['id']}` | {r['name']} | `{r['kind']}` | "
            f"`{r['widthM']:.2f} × {r['depthM']:.2f}` | `{r['areaM2']:.2f}` |"
        )
    lines.extend([
        "",
        "## 7. Assumptions & Unknowns Requiring Survey Verification",
        "",
    ])
    for u in assumptions["unknowns_requiring_site_measurement"]:
        lines.append(f"- {u}")
    lines.extend(["", f"Plan hash: `{spec['planHash']}` | Geometry hash: `{spec['geometryHash']}`", ""])
    return "\n".join(lines)


def _build_single_option(opt_code: str, p: dict, variant_dir: Path, ref_src_dir: Path, photo_manifest: dict, assumptions: dict) -> dict:
    """Compile one Tirumala Revision-10 option and write its deliverables into `variant_dir`."""
    try:
        b_check = generate_layout(fuse(p))
        review = validate(b_check)
    except Exception as exc:
        details = getattr(exc, "details", None)
        raise RuntimeError(f"Tirumala Option {opt_code} failed: {exc} | details={json.dumps(details, indent=2)}") from exc
    if review.get("errors") or review.get("warnings"):
        raise RuntimeError(f"Tirumala Option {opt_code} validation issues: {json.dumps(review, indent=2)}")

    if variant_dir.exists():
        shutil.rmtree(variant_dir)
    variant_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"ff-tirumala-{opt_code}-") as tmp:
        result = run(p, Path(tmp), use_cache=False)
        shutil.copytree(result["path"], variant_dir, dirs_exist_ok=True)

    b = json.loads((variant_dir / "building.json").read_text(encoding="utf-8"))
    scene = json.loads((variant_dir / "scene.json").read_text(encoding="utf-8"))
    site_context = build_tirumala_context(b, scene)
    meta = OPTIONS[opt_code]
    rev8 = b.get("planning", {}).get("tirumalaMeta") or b.get("planning", {}).get("tirumalaRev8") or {}

    spec = {
        "id": TIRUMALA_ID,
        "revision": REVISION,
        "option": opt_code,
        "optionLabel": meta["label"],
        "optionTag": meta["tag"],
        "optionTrade": meta["trade"],
        "title": b["brief"]["title"],
        "planHash": b["planHash"],
        "geometryHash": rev8.get("geometryHash", ""),
        "disclaimer": b["banner"],
        "orientation": "East road/front (40 ft = 12.192 m, y=0) · South left (x=0) · North 12 m road/right (50 ft = 15.240 m, x=12.192 m) · West rear (y=15.240 m)",
        "notes": p["notes"],
        "plotFt": [40, 50],
        "plotM": [12.192, 15.240],
        "plotAreaSqFt": 2000,
        "plotAreaM2": 185.806,
        "floorLevelsMm": {
            "parking_bay_mm": 0,
            "entry_intermediate_step_mm": 150,
            "house_court_porch_veranda_mm": 300,
            "floor_to_floor_mm": 3658,
            "ordinary_clear_ceiling_mm": 3353,
            "double_height_living_clear_mm": 7010,
        },
        "stairSpec": {
            "shape": "quarter-turn",
            "boundingBoxFt": [12.0, 12.0],
            "coreAreaSqFt": round(next(r["area_m2"] for r in b["spaces"] if r["id"]=="g-stair")/.09290304,2),
            "flightWidthFt": 3.5,
            "wellFt": 0.0,
            "southLandingDepthFt": 3.5,
            "riserCount": 20,
            "riserMm": 182.88,
            "treadsPerFlight": 9,
            "treadMm": 287.87,
            "sequence": "Enter from north hall -> climb SOUTH -> quarter turn -> climb EAST to upper lounge outside living void",
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

    (variant_dir / "specifications.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    (variant_dir / "site-context.json").write_text(json.dumps(site_context, indent=2) + "\n", encoding="utf-8")
    (variant_dir / "photo-reference-manifest.json").write_text(json.dumps(photo_manifest, indent=2) + "\n", encoding="utf-8")
    (variant_dir / "assumptions-register.json").write_text(json.dumps(assumptions, indent=2) + "\n", encoding="utf-8")

    # Copy reference photographs into variant_dir/reference-assets/
    ref_dst_dir = variant_dir / "reference-assets"
    if ref_src_dir.exists():
        ref_dst_dir.mkdir(parents=True, exist_ok=True)
        for img in sorted(ref_src_dir.glob("*.png")):
            shutil.copy2(img, ref_dst_dir / img.name)

    return {
        "option": opt_code,
        "building": b,
        "review": review,
        "scene": scene,
        "specifications": spec,
        "site_context": site_context,
    }


def _finalize_option_package(variant_dir: Path, spec: dict, site_context: dict, photo_manifest: dict, assumptions: dict, options_summary: list[dict], options_manifest_bytes: bytes | None = None) -> None:
    """Write DESIGN_GUIDE.md, update manifest.json, and rebuild deterministic FloorForge-export.zip."""
    guide_md = _design_guide(spec, site_context, photo_manifest, assumptions, options_summary)
    (variant_dir / "DESIGN_GUIDE.md").write_text(guide_md, encoding="utf-8")
    if options_manifest_bytes is not None:
        (variant_dir / "options-manifest.json").write_bytes(options_manifest_bytes)

    manifest = json.loads((variant_dir / "manifest.json").read_text(encoding="utf-8"))
    extra_files = [
        "specifications.json",
        "DESIGN_GUIDE.md",
        "site-context.json",
        "photo-reference-manifest.json",
        "assumptions-register.json",
    ]
    if (variant_dir / "options-manifest.json").exists():
        extra_files.append("options-manifest.json")
    ref_dir = variant_dir / "reference-assets"
    if ref_dir.exists():
        for img in sorted(ref_dir.glob("*.png")):
            extra_files.append(f"reference-assets/{img.name}")

    for name in extra_files:
        manifest["files"][name] = hashlib.sha256((variant_dir / name).read_bytes()).hexdigest()
    (variant_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    files = {name: (variant_dir / name).read_bytes() for name in manifest["files"]}
    files["manifest.json"] = (variant_dir / "manifest.json").read_bytes()
    (variant_dir / "FloorForge-export.zip").write_bytes(deterministic_zip(files))


def write_tirumala(out_dir: Path = OUT_DIR) -> dict:
    """Compile all five Tirumala Revision-10 options (A–E), write variants/{A..E}, set Option A as root default,
    and update catalog.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    ref_src_dir = EVIDENCE_DIR / "reference-assets"
    photo_manifest = build_photo_reference_manifest()
    assumptions = build_assumptions_register()

    projects = all_option_projects()
    built_options: dict[str, dict] = {}
    variants_root = out_dir / "variants"
    variants_root.mkdir(parents=True, exist_ok=True)

    for code, p in projects.items():
        (BRIEFS_DIR / f"{TIRUMALA_ID}-{code}.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
        if code == "A":
            (BRIEFS_DIR / f"{TIRUMALA_ID}.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
        built_options[code] = _build_single_option(
            code, p, variants_root / code, ref_src_dir, photo_manifest, assumptions
        )

    options_summary = []
    for code, res in built_options.items():
        meta = OPTIONS[code]
        cz = canonical_handoff_zones(code)
        b = res["building"]
        options_summary.append({
            "option": code,
            "code": code,
            "label": meta["label"],
            "tag": meta["tag"],
            "trade": meta["trade"],
            "careSqFt": meta["careSqFt"],
            "drawingFt": meta["drawingFt"],
            "caregiverSqFt": meta["caregiverSqFt"],
            "verandaDepthFt": meta["verandaDepthFt"],
            "careWestEdgeFt": cz["careEndFt"],
            "planHash": b["planHash"],
            "geometryHash": res["specifications"]["geometryHash"],
            "baseUrl": f"/samples/{TIRUMALA_ID}/variants/{code}/",
        })

    options_manifest = {
        "id": TIRUMALA_ID,
        "revision": REVISION,
        "defaultOption": "A",
        "plotFt": [40, 50],
        "plotMm": [12192, 15240],
        "mmPerFt": 304.8,
        "options": options_summary,
    }
    options_manifest_bytes = (json.dumps(options_manifest, indent=2) + "\n").encode("utf-8")

    for code, res in built_options.items():
        _finalize_option_package(
            variants_root / code,
            res["specifications"],
            res["site_context"],
            photo_manifest,
            assumptions,
            options_summary,
            options_manifest_bytes,
        )

    # Copy Option A files into out_dir root as the default sample while keeping variants/A..E intact
    opt_a_dir = variants_root / "A"
    for item in opt_a_dir.iterdir():
        dst = out_dir / item.name
        if item.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
    (out_dir / "options-manifest.json").write_bytes(options_manifest_bytes)

    # Mirror registers into evidence/tirumala/
    for fname in (
        "site-context.json",
        "photo-reference-manifest.json",
        "assumptions-register.json",
        "DESIGN_GUIDE.md",
        "specifications.json",
        "options-manifest.json",
    ):
        shutil.copy2(out_dir / fname, EVIDENCE_DIR / fname)

    update_catalog_entry(built_options["A"]["building"], options_summary)
    return {
        "building": built_options["A"]["building"],
        "review": built_options["A"]["review"],
        "scene": built_options["A"]["scene"],
        "specifications": built_options["A"]["specifications"],
        "options": options_summary,
    }


def update_catalog_entry(b: dict, options_summary: list[dict]) -> None:
    """Append or update ONLY the 'tirumala' entry in examples/gallery/catalog.json without
    renaming, removing, reordering, or altering any existing entry."""
    items = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    entry = {
        "id": TIRUMALA_ID,
        "title": "Tirumala",
        "revision": REVISION,
        "defaultOption": "A",
        "options": options_summary,
        "description": (
            "East-facing 40 × 50 ft (2,000 sq ft) northeast corner home (Revision 10, Options A–E) bounded by a 12 m North road "
            "(opposite a colony garden and white/blue-grey house) and a 9 m East road (opposite a basketball-court enclosure): "
            "corner L staircase, enlarged kitchen and west dining, two upper master suites and a generous family lounge, with "
            "~23 ft double-height void and rooflight, shallow 11 × 3 ft open porch, +300 mm house/court/veranda datum above "
            "a ±0 mm 10.5 × 19 ft car bay, South-to-North care bed with broad North/East glazing, caregiver suite, and open NW garden."
        ),
        "style": "White/Ivory & Colony Veranda (Rev 10 · Options A–E)",
        "directory": f"gallery/{TIRUMALA_ID}",
        "bedrooms": b["brief"]["bedrooms"],
        "storeys": 2,
        "widthFt": 40,
        "depthFt": 50,
        "roofAccess": bool(b.get("rooftop")),
        "planHash": b["planHash"],
        "hasSpecifications": True,
    }
    existing_idx = next((i for i, s in enumerate(items) if s.get("id") == TIRUMALA_ID), None)
    if existing_idx is None:
        items.append(entry)
    else:
        items[existing_idx] = entry
    CATALOG_PATH.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


def check_tirumala() -> int:
    for code in OPTIONS:
        p = tirumala_project(code)
        b = generate_layout(fuse(p))
        review = validate(b)
        if review.get("errors") or review.get("warnings"):
            print(f"Validation failed for Option {code}: {review}", file=sys.stderr)
            return 1
        var_b_path = OUT_DIR / "variants" / code / "building.json"
        if not var_b_path.exists():
            print(f"Missing variant building.json for Option {code}", file=sys.stderr)
            return 1
        on_disk = json.loads(var_b_path.read_text(encoding="utf-8"))
        if on_disk.get("planHash") != b.get("planHash"):
            print(f"planHash mismatch on disk for Option {code}", file=sys.stderr)
            return 1
    root_disk = json.loads((OUT_DIR / "building.json").read_text(encoding="utf-8"))
    opt_a = json.loads((OUT_DIR / "variants" / "A" / "building.json").read_text(encoding="utf-8"))
    if root_disk.get("planHash") != opt_a.get("planHash"):
        print("Root building.json planHash does not match Option A", file=sys.stderr)
        return 1
    print(f"Tirumala Revision 10 check passed for all 5 options A–E (default A planHash={root_disk['planHash']})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify Tirumala Revision 10 Options A–E compile and match on-disk planHashes.")
    args = parser.parse_args()

    if args.check:
        return check_tirumala()

    result = write_tirumala()
    print(json.dumps({
        "path": str(OUT_DIR),
        "defaultPlanHash": result["building"]["planHash"],
        "options": [
            {"option": o["option"], "planHash": o["planHash"], "geometryHash": o["geometryHash"][:12]}
            for o in result["options"]
        ],
        "review": result["review"].get("status"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
