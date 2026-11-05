#!/usr/bin/env python3
"""Build or finalize the independent 'tirumala-4' sample project:
- 'tirumala-4' (based on finalized Tirumala 3 / P13, version p13-icu-east-extension-2026-10-30,
  with calibrated Tirumala Colony surroundings from R07-R14 and V01-V06, empty default car porch,
  existing-vs-proposed site mode toggle, and refined interior lighting/material presentation).

Preserves all existing sample projects (tirumala-2, tirumala-3, tirumala, my-desired-home, bungalow, etc.) untouched.
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
from floorforge.tirumala_4 import (
    TIRUMALA_3_SOURCE_GEOMETRY_HASH,
    TIRUMALA_3_SOURCE_PLAN_HASH,
    TIRUMALA_3_SOURCE_VERSION,
    TIRUMALA_4_REVISION,
    build_tirumala_4_assumptions_register,
    build_tirumala_4_clearance_audit,
    build_tirumala_4_photo_reference_manifest,
    build_tirumala_4_site_context,
    generate_site_context_plan_svg,
)
from floorforge.tirumala_luxury import JOINERY_REVISION, PALETTES, REVISION, upper_svg
from floorforge.tirumala_p11_p12 import (
    PROVISIONAL_PORCH_DROP_MM,
    _mm_to_ft_in,
    build_p11_p12_project,
    load_authoritative_plan_data,
    render_dimensioned_2d_svg,
    render_material_overhead_2d_svg,
)

SLUG = "tirumala-4"
GALLERY_DIR = ROOT / "examples" / "gallery"
BRIEFS_DIR = GALLERY_DIR / "briefs"
CATALOG_PATH = GALLERY_DIR / "catalog.json"
COLONY_REF_DIR = ROOT / "evidence" / "tirumala" / "reference-assets"
PROMPT_PACK_DIR = ROOT / "output" / "tirumala-4-prompt-pack"


def _design_guide(b: dict, spec: dict, site_context: dict, photo_manifest: dict, assumptions: dict, clearance_audit: dict) -> str:
    """Generate comprehensive, model-derived DESIGN_GUIDE.md for Tirumala 4."""
    plan = b["planning"]["canonicalPlan"]
    lines = [
        f"# {spec['title']} — {spec['option']} Site-Calibrated Reference",
        "",
        f"Approved source: `tirumala-3` (`{spec['sourceVersion']}`, source `planHash`: `{spec['sourcePlanHash']}`, `geometryHash`: `{spec['geometryHash']}`).",
        "Plot: **40 ft north–south × 50 ft east–west** (`12.192 × 15.240 m`, `2,000 sq ft`). West is up and north is right in overhead 2D plans.",
        "",
        "Tirumala 4 preserves every room polygon, wall thickness, opening span, stair flight, ceiling height, and P13 Home ICU enlargement from Tirumala 3 (`geometryHash` identical), while calibrating the real Tirumala Colony surroundings (`R07`–`R14`, `V01`–`V06`), separating pre-construction plot vegetation into the `Existing plot` site mode toggle, keeping the private car porch empty by default (`defaultCarVisible: false`), and refining interior daylight/overcast material response.",
        "",
        "## Ground & First Floor Room Schedule",
        "",
        "| Room | Floor | Clear bounding span (feet / inches) | Net Area (sq ft) | Net Area (m²) |",
        "|---|---:|---|---:|---:|",
    ]
    for room in b["spaces"]:
        bounds = Polygon(room["clear"]).bounds
        size = " × ".join(_mm_to_ft_in(bounds[i + 2] - bounds[i]) for i in range(2))
        fl_label = "Ground" if room["floor"] == 0 else "First"
        lines.append(f"| {room['name']} | {fl_label} | {size} | {room['area_m2'] / 0.09290304:.1f} | {room['area_m2']:.2f} |")

    lines += [
        "",
        "## Door & Full-Height Opening Schedule",
        "",
        "Jambs reduce door aperture width by `110 mm` (`4⅜ in`). The ground-floor master bedroom entry recess is not the bedroom doorway.",
        "",
        "| Opening ID | Floor | Raw Kind | Structural Aperture | Clear Between Jambs |",
        "|---|---:|---|---:|---:|",
    ]
    for op in b["openings"]:
        if op["sill"] == 0 and op["raw_kind"] != "open-passage":
            fl_label = "Ground" if op["floor"] == 0 else "First"
            lines.append(
                f"| `{op['id']}` | {fl_label} | `{op['raw_kind']}` | {_mm_to_ft_in(op['width'])} (`{op['width']} mm`) | {_mm_to_ft_in(op['width'] - 110)} (`{op['width'] - 110} mm`) |"
            )

    serving = Polygon(plan["serving"]).bounds
    counter = Polygon(plan["counter"]).bounds
    lines += [
        "",
        "## Measured Circulation & Bottleneck Clearance Audit",
        "",
        "| Passage / Pinch Point | Clear Width (ft / in) | Clear Width (mm) | Notes |",
        "|---|---:|---:|---|",
    ]
    for item in clearance_audit:
        lines.append(
            f"| {item['zone']} | {item['measuredFtIn']} | `{item['measuredMm']}` | {item['note']} |"
        )

    lines += [
        "",
        "## Kitchen, Levels, Stairs & Finishes",
        "",
        f"- **Kitchen**: Serving worktop `{_mm_to_ft_in(serving[2] - serving[0])} × {_mm_to_ft_in(serving[3] - serving[1])}`. L-counter along the store and east walls; east run `{_mm_to_ft_in(counter[2] - counter[0])}`. No fridge or puja room.",
        f"- **Levels**: House, veranda, east forecourt, and side/rear passages sit at `0 mm` house datum (`+300 mm` above road NGL). Road NGL is `-300 mm`. Lower car porch sits at `-{spec['floorLevelsMm']['provisional_porch_drop_mm']} mm` (`-6 in` provisional adjustable drop, separate from horizontal plot/room dimensions). Default car visibility is `false` (empty porch); the accurately sized Škoda Kylaq (`4098 × 1975 × 1522 mm`) can be toggled on via `Show car` for a parking check.",
        "- **Stairs & Upper Floor**: 18 risers (`175 mm`) to `3150 mm` landing, plus 2 arrival connector risers (`179 mm`) to `3508 mm` first-floor slab. Ground-floor clear ceiling is `3315 mm`; double-height living void reaches `6991 mm` (`~23 ft`). First floor comprises the upper master suite (`276.7 sq ft`), master ensuite (`48.0 sq ft`), study/office (`92.2 sq ft`), guest bedroom (`106.2 sq ft`), shared bathroom (`37.6 sq ft`), gallery overlooking the double-height living hall, and open garden terrace reached directly from the gallery (no stair to the roof above the first floor).",
        "- **Material Palette**: Large `24 × 48 in` (`609.6 × 1219.2 mm`) warm white/ivory marble-look tiles (soft-satin indoors, coordinated non-slip matte on veranda and wet gullies), textured Kota stone with red-oxide border on the lower car porch, warm limestone exterior cladding, teak timber accents, charcoal aluminium glazing, and warm daylight (`day`) + neutral overcast (`overcast`) lighting grades.",
        "- **Layered Hall–ICU Entrance**: Wooden privacy doors sit on the hall side concealing an independent sliding glass door behind them (`icu-glass-living-wood` + `icu-glass-living`). Both layers operate independently (`Wood closed`, `Reveal glass`, `Both open`). The separate ICU–veranda glass opening (`icu-veranda-glass`) stacks neatly to the side.",
        "",
        "## Colony Site Calibration & Evidence Hygiene (`R07`–`R14`, `V01`–`V06`)",
        "",
        "- **Existing vs Proposed Site Layer Toggle**: Pre-construction trees, wild scrub, and footing blocks (`R07`, `R10`, `R12`, `V05`, `V06`) are isolated in the `Existing plot` site mode (`Site: Existing plot` button) so zero tree trunks or branches pass through rooms or block access in `Proposed` mode.",
        "- **Colony Road & Boundary Details**: Grooved concrete carriageways (`12 m` North road, `9 m` East road), interlocking dusty-rose/grey paver verges, precast concrete storm-drain cover slabs with paired circular holes (`V01`, `R09`, `R13`), muted mauve-taupe boundary walls (`#8e7e85`) with pale grey coping (`#c8c4bc`) and horizontally grooved square corner piers (`R11`, `R14`, `V02`, `V05`), mixed burgundy *Acalypha* and white-flowering green *Tabernaemontana* hedges (`R10`, `R12`, `V03`), slim dark-grey LED street luminaires (`R09`, `R13`, `R14`, `V04`), and round-hooded post-top park lamp + fenced basketball court with terracotta key and white markings (`V01`, `E-01`).",
        "- **R11 Duplicate Photo Discrepancy**: Two attachments in the reference set use the identical underlying photograph (`1000145311.jpg`) with different annotations (`R11-NE-corner-owner-labelled.png` vs `alternate-annotation/R11-wall-return-unconfirmed.png`). They are documented as a single photograph in `photo-reference-manifest.json` and `assumptions-register.json`; the owner-confirmed NE corner interpretation is used while preserving the locked `40 × 50 ft` boundary.",
        "- **V06 Video Roll Caution**: Near the end of the walk-around video (`V06`, `20.0 s`), the camera tilts/rolls while framing plot vegetation; compass bearings are derived from continuous pan landmarks (`V01`–`V05`), never from camera roll.",
        "- **Transient Exclusions**: All temporary parked cars, covered vehicles, scooters, and pedestrians visible in `R09`, `R10`, `R12`, and `R13` are excluded from the permanent 3D colony scene.",
        "",
        f"Plan hash: `{spec['planHash']}`. Geometry hash: `{spec['geometryHash']}` (matches Tirumala 3 / P13).",
        "",
    ]
    return "\n".join(lines)


def build_tirumala_4(finalize_only: bool = False) -> dict:
    """Build or finalize 'tirumala-4' in examples/gallery/tirumala-4/."""
    out_dir = GALLERY_DIR / SLUG
    out_dir.mkdir(parents=True, exist_ok=True)
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)

    src_plan_data = load_authoritative_plan_data(SLUG)
    ref_dir = out_dir / "reference-assets"
    ref_dir.mkdir(parents=True, exist_ok=True)

    p = build_p11_p12_project(SLUG)
    (BRIEFS_DIR / f"{SLUG}.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")

    if not finalize_only:
        b_check = generate_layout(fuse(p))
        review = validate(b_check)
        if review.get("errors") or review.get("warnings"):
            raise RuntimeError(f"{SLUG} validation failed: {json.dumps(review, indent=2)}")

        with tempfile.TemporaryDirectory(prefix=f"ff-{SLUG}-") as tmp:
            result = run(p, Path(tmp), use_cache=False)
            shutil.copytree(result["path"], out_dir, dirs_exist_ok=True)

        (out_dir / "source-plan-data.json").write_text(json.dumps(src_plan_data, indent=2) + "\n", encoding="utf-8")
        ref_dir.mkdir(parents=True, exist_ok=True)
        # Copy baseline reference assets from Tirumala 3 / colony reference dir
        t3_ref_dir = GALLERY_DIR / "tirumala-3" / "reference-assets"
        if t3_ref_dir.exists():
            for img in sorted(t3_ref_dir.glob("*")):
                if img.is_file():
                    shutil.copy2(img, ref_dir / img.name)
        elif COLONY_REF_DIR.exists():
            for img in sorted(COLONY_REF_DIR.glob("*.png")):
                shutil.copy2(img, ref_dir / img.name)

    b = json.loads((out_dir / "building.json").read_text(encoding="utf-8"))
    scene = json.loads((out_dir / "scene.json").read_text(encoding="utf-8"))

    ground_geom_hash = hashlib.sha256(
        json.dumps(b["planning"]["canonicalPlan"], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    geom_hash = hashlib.sha256(
        json.dumps(
            {"ground": b["planning"]["canonicalPlan"], "upper": b["planning"]["upperPlan"]},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    if geom_hash != TIRUMALA_3_SOURCE_GEOMETRY_HASH:
        raise RuntimeError(
            f"Tirumala 4 geometryHash ({geom_hash}) diverged from Tirumala 3 ({TIRUMALA_3_SOURCE_GEOMETRY_HASH})!"
        )

    care = next(r for r in b["spaces"] if r["id"] == "g-care")
    cx0, cy0, cx1, cy1 = care["bounds"]
    care_size = f"{_mm_to_ft_in(cx1 - cx0)} × {_mm_to_ft_in(cy1 - cy0)}"
    care_sqft = round(care["area_m2"] / 0.09290304, 1)

    title = "Tirumala 4"
    style_label = "Ivory · limestone · teak (P13 · calibrated colony & interior realism)"
    subtitle = f"P13 · Home ICU {care_size} · Calibrated colony context · Empty porch default · G+1"
    description = (
        f"40 × 50 ft east-facing G+1 northeast corner home built on locked Tirumala 3 (P13) geometry "
        f"(Home ICU {care_size}, {care_sqft} sq ft, 5 ft east forecourt, layered wood + sliding glass ICU entrance, "
        f"15 ft 7⅝ in × 7 ft 0¼ in north veranda, 23 ft double-height living void, upper master, study, guest room & open terrace). "
        "Calibrated Tirumala Colony surroundings from site photos R07–R14 and walk-around video V01–V06, "
        "empty private car porch by default (with optional parking check), Existing-vs-Proposed site toggle, "
        "and balanced warm-daylight & neutral-overcast ivory–limestone–teak interiors."
    )

    site_context = build_tirumala_4_site_context(b, scene)
    photo_manifest = build_tirumala_4_photo_reference_manifest()
    assumptions = build_tirumala_4_assumptions_register()
    clearance_audit = build_tirumala_4_clearance_audit()

    spec = {
        "id": SLUG,
        "basedOnSample": "tirumala-3",
        "sourcePlanHash": TIRUMALA_3_SOURCE_PLAN_HASH,
        "sourceGeometryHash": TIRUMALA_3_SOURCE_GEOMETRY_HASH,
        "revision": 34,
        "option": "P13",
        "sourceOption": "P11",
        "sourceVersion": TIRUMALA_3_SOURCE_VERSION,
        "currentVersion": b["planning"]["canonicalPlan"]["version"],
        "spaciousnessRevision": TIRUMALA_4_REVISION,
        "optionLabel": style_label,
        "optionTag": subtitle,
        "optionTrade": description,
        "title": title,
        "planHash": b["planHash"],
        "groundGeometryHash": ground_geom_hash,
        "geometryHash": geom_hash,
        "defaultCarVisible": False,
        "siteModes": ["proposed", "existing"],
        "disclaimer": b["banner"],
        "orientation": (
            "East road/front (40 ft = 12.192 m, y=0) · South left (x=0) · North 12 m road/right "
            "(50 ft = 15.240 m, x=12.192 m) · West rear (y=15.240 m). Overhead 2D plans show West at top and North on right."
        ),
        "notes": p.get("notes") or description,
        "plotFt": [40, 50],
        "plotM": [12.192, 15.240],
        "plotAreaSqFt": 2000,
        "plotAreaM2": 185.806,
        "luxuryRevision": REVISION,
        "joineryRevision": JOINERY_REVISION,
        "palette": "ivory-teak",
        "paletteStatus": "user-approved",
        "icuDoorLayersFromHall": ["wooden privacy door", "independent sliding glass door", "ICU"],
        "windowSchedule": [
            {
                "id": o["id"],
                "floor": o["floor"],
                "widthMm": o["width"],
                "heightMm": o["height"],
                "sillMm": o["sill"],
                "clearBetweenJambsMm": o["width"] - 110 if o["sill"] == 0 else o["width"],
                "style": o.get("window_style", "operable casement"),
            }
            for o in b["openings"]
            if o["kind"] == "window"
        ],
        "doorSchedule": [
            {
                "id": o["id"],
                "floor": o["floor"],
                "rawKind": o["raw_kind"],
                "apertureMm": o["width"],
                "apertureFtIn": _mm_to_ft_in(o["width"]),
                "clearBetweenJambsMm": o["width"] - 110,
                "clearBetweenJambsFtIn": _mm_to_ft_in(o["width"] - 110),
                "heightMm": o["height"],
            }
            for o in b["openings"]
            if o["sill"] == 0 and o["raw_kind"] != "open-passage"
        ],
        "clearanceAudit": clearance_audit,
        "paletteOptions": PALETTES,
        "upperFloor": b["planning"]["upperPlan"],
        "floorLevelsMm": {
            "road_ngl_mm": -300,
            "lower_car_porch_mm": -round(PROVISIONAL_PORCH_DROP_MM, 1),
            "provisional_porch_drop_mm": round(PROVISIONAL_PORCH_DROP_MM, 1),
            "provisional_porch_drop_in": 6.0,
            "provisional_porch_drop_status": "PROVISIONAL_ADJUSTABLE_SEPARATE_FROM_HORIZONTAL_DIMENSIONS",
            "house_veranda_forecourt_passages_mm": 0,
            "plinth_above_road_mm": 300,
            "floor_to_floor_mm": 3508,
            "clear_ceiling_mm": 3315,
            "double_height_ceiling_mm": 6991,
            "upper_terrace_mm": 3508,
        },
        "flooringSpecification": {
            "dominantInterior": {
                "material": "ivory-marble-polished",
                "moduleIn": [24, 48],
                "moduleMm": [609.6, 1219.2],
                "finish": "soft-satin / polished warm white-ivory vitrified marble with restrained natural veining",
                "appliesTo": [
                    "g-living",
                    "g-kitchen",
                    "g-kitchen-store",
                    "g-bedroom",
                    "g-bath",
                    "g-caregiver",
                    "g-caregiver-bath",
                    "g-access-lobby",
                    "g-drawing",
                    "g-care",
                ],
            },
            "dominantExteriorAndWet": {
                "material": "ivory-marble-exterior-matte",
                "moduleIn": [24, 48],
                "moduleMm": [609.6, 1219.2],
                "finish": "coordinated non-slip exterior matte warm white-ivory vitrified marble",
                "appliesTo": [
                    "g-veranda",
                    "g-wash-gully",
                    "raised-east-forecourt",
                    "north-open-passage",
                    "side-and-rear-walkways",
                ],
            },
            "lowerCarPorch": {
                "material": "porch-kota-paver + porch-red-oxide-border",
                "finish": "traditional bungalow-inspired textured Kota stone / earthy geometric pavers with red-oxide border and inlay bands",
                "continuousAcrossNotchOrReturn": True,
                "defaultCarVisible": False,
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
            "arrivalConnectorRisers": 2,
            "arrivalConnectorRiserMm": 179,
            "upperFloorMm": 3508,
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
                "widthFtIn": _mm_to_ft_in(Polygon(r["clear"]).bounds[2] - Polygon(r["clear"]).bounds[0]),
                "depthFtIn": _mm_to_ft_in(Polygon(r["clear"]).bounds[3] - Polygon(r["clear"]).bounds[1]),
                "areaM2": r["area_m2"],
                "areaSqFt": round(r["area_m2"] / 0.09290304, 1),
            }
            for r in b["spaces"]
        ],
    }

    (out_dir / "specifications.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    (out_dir / "site-context.json").write_text(json.dumps(site_context, indent=2) + "\n", encoding="utf-8")
    (out_dir / "photo-reference-manifest.json").write_text(json.dumps(photo_manifest, indent=2) + "\n", encoding="utf-8")
    (out_dir / "assumptions-register.json").write_text(json.dumps(assumptions, indent=2) + "\n", encoding="utf-8")
    (out_dir / "DESIGN_GUIDE.md").write_text(
        _design_guide(b, spec, site_context, photo_manifest, assumptions, clearance_audit),
        encoding="utf-8",
    )

    renders_dir = out_dir / "renders"
    renders_dir.mkdir(parents=True, exist_ok=True)
    if not finalize_only:
        (renders_dir / "plan-2d-dimensioned.svg").write_text(render_dimensioned_2d_svg(b), encoding="utf-8")
        (renders_dir / "plan-first-floor.svg").write_text(upper_svg(b), encoding="utf-8")
        (renders_dir / "plan-2d-material-overhead.svg").write_text(render_material_overhead_2d_svg(b), encoding="utf-8")
        (renders_dir / "site-context-plan.svg").write_text(generate_site_context_plan_svg(b), encoding="utf-8")

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

    # Update catalog.json with tirumala-4 while preserving all other entries untouched
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    t4_entry = {
        "id": SLUG,
        "title": title,
        "description": description,
        "style": style_label,
        "directory": f"gallery/{SLUG}",
        "basedOnSample": "tirumala-3",
        "sourcePlanHash": TIRUMALA_3_SOURCE_PLAN_HASH,
        "bedrooms": 4,
        "storeys": 2,
        "widthFt": 40,
        "depthFt": 50,
        "roofAccess": False,
        "terraceAccess": True,
        "planHash": b["planHash"],
        "hasSpecifications": True,
    }
    updated: list[dict] = []
    seen = False
    for item in catalog:
        if item.get("id") == SLUG:
            updated.append(t4_entry)
            seen = True
        else:
            updated.append(item)
    if not seen:
        updated.append(t4_entry)
    CATALOG_PATH.write_text(json.dumps(updated, indent=2) + "\n", encoding="utf-8")

    return {
        "slug": SLUG,
        "planHash": b["planHash"],
        "geometryHash": geom_hash,
        "outDir": str(out_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--finalize-zip",
        action="store_true",
        help="Repackage manifest.json and FloorForge-export.zip after renders are captured.",
    )
    args = parser.parse_args()
    res = build_tirumala_4(finalize_only=args.finalize_zip)
    print(f"Built {res['slug']}: planHash={res['planHash']} geometryHash={res['geometryHash']} -> {res['outDir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
