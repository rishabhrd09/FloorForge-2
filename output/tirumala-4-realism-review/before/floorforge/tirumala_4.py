"""Tirumala 4 ('tirumala-4') — Colony Context, Exterior/Interior Material & Lighting Realism
built on the locked Tirumala 3 (P13, version p13-icu-east-extension-2026-10-30) geometry.

Preserves all Tirumala 2 and Tirumala 3 files, hashes, room polygons, walls, openings,
stairs, and slab levels untouched while scoping all Tirumala 4 enhancements to 'tirumala-4'.
"""
from __future__ import annotations

import copy
import html
import math
from pathlib import Path
from typing import Any

from .tirumala_context import (
    build_assumptions_register,
    build_photo_reference_manifest,
    build_tirumala_context,
)

TIRUMALA_3_SOURCE_PLAN_HASH = "22453e485574c04b3780e1bcabb816917ae4ab81ea91093e1720de9fe99271ba"
TIRUMALA_3_SOURCE_GEOMETRY_HASH = "b6484526b3006577c8ea77d195487ec31e7226a90a9804cd2f2d400bc74b78fc"
TIRUMALA_3_SOURCE_VERSION = "p13-icu-east-extension-2026-10-30"
TIRUMALA_4_REVISION = "tirumala-4-2026-10-31"


def is_tirumala_4(obj: Any) -> bool:
    """Return True if ``obj`` represents the ``tirumala-4`` sample project."""
    if obj == "tirumala-4":
        return True
    if not isinstance(obj, dict):
        return False
    cp = obj.get("customPlan") if isinstance(obj.get("customPlan"), dict) else obj
    meta = cp.get("tirumalaMeta")
    if isinstance(meta, dict) and meta.get("projectId") == "tirumala-4":
        return True
    planning = obj.get("planning")
    if isinstance(planning, dict):
        pmeta = planning.get("tirumalaMeta")
        if isinstance(pmeta, dict) and pmeta.get("projectId") == "tirumala-4":
            return True
    brief = obj.get("brief")
    if isinstance(brief, dict) and brief.get("title") == "Tirumala 4":
        return True
    return False


def apply_tirumala_4_project_metadata(project: dict[str, Any]) -> dict[str, Any]:
    """Tag a P13 project payload as ``tirumala-4`` without altering any room, wall, opening, or stair coordinates."""
    out = copy.deepcopy(project)
    out["brief"]["title"] = "Tirumala 4"
    out["notes"] = (
        "Tirumala 4 — Colony Context, Exterior/Interior Material & Lighting Realism on Locked Tirumala 3 (P13) Geometry. "
        "40 ft N-S x 50 ft E-W (12,192 x 15,240 mm) northeast-corner plot in Tirumala Colony with East principal arrival, "
        "12 m North road opposite the colony garden and white/navy-blue-grey house, 9 m East road opposite the basketball court, "
        "provisional 6-inch (-152.4 mm) lower car porch (shown empty by default with optional parking-check vehicle), "
        "P13 Home ICU (11 ft 3 in x 13 ft 4 7/8 in, 150.8 sq ft) with 5 ft raised East forecourt, full-size recliner bed "
        "(head West, feet East), one companion chair, wall-mounted TV and compact 2 ft x 14 in drawer table, "
        "hall-side wooden privacy doors concealing independent sliding glass behind them, separate ICU-veranda slide-and-turn "
        "glass doors, living-veranda folding wood + retractable mesh doors, and G+1 upper floor (upper master suite, ensuite, "
        "office/study, guest bedroom, shared bath, 23 ft double-height living void, gallery and open terrace). "
        "Calibrated against owner-supplied site photos R07-R14 and walk-around video V01-V06."
    )
    cp = out["customPlan"]
    cp["tirumalaMeta"].update(
        projectId="tirumala-4",
        sourceProject="tirumala-3",
        sourcePlanHash=TIRUMALA_3_SOURCE_PLAN_HASH,
        sourceGeometryHash=TIRUMALA_3_SOURCE_GEOMETRY_HASH,
        displayOption="P13",
        sourceOption="P11",
        label="Tirumala 4 · P13 colony & interior realism",
        galleryRevision="tirumala-4-2026-10-31",
        tirumala4Presentation=True,
        defaultCarVisible=False,
        spaciousnessPresentation=True,
        trial=False,
    )
    return out


def build_tirumala_4_photo_reference_manifest() -> dict[str, Any]:
    """Build the comprehensive reference manifest combining N-01..E-01 with R07..R14 and V01..V06."""
    base = build_photo_reference_manifest()
    base["project_id"] = "tirumala-4"
    base["projectId"] = "tirumala-4"
    base["sourceProjectId"] = "tirumala-3"
    base["sourcePlanHash"] = TIRUMALA_3_SOURCE_PLAN_HASH
    base["version"] = "tirumala-4-evidence-pack-2026-10-31"
    base["evidencePackPath"] = "output/tirumala-4-prompt-pack/"
    base["duplicateAnnotationDiscrepancy"] = {
        "referenceId": "R11",
        "sourcePhoto": "1000145311.jpg",
        "primaryFile": "output/tirumala-4-prompt-pack/site-photos/R11-NE-corner-owner-labelled.png",
        "alternateFile": "output/tirumala-4-prompt-pack/site-photos/alternate-annotation/R11-wall-return-unconfirmed.png",
        "resolution": (
            "Both annotations use the identical underlying photograph (1000145311.jpg). "
            "The primary annotation ('NE corner of the plot', 'North 12 m road', 'East 9 m road') is owner-confirmed "
            "and matches the video pan (V02/V05). The alternate red-text annotation ('Wall turns from here') is "
            "preserved in the evidence register as an unconfirmed alternate interpretation and is not used to alter "
            "the locked 40 x 50 ft plot boundary."
        ),
    }
    base["videoPanCaution"] = {
        "videoFile": "output/tirumala-4-prompt-pack/video/tirumala_plot.mp4",
        "durationSec": 23.36,
        "fps": 30,
        "direction": "Right-to-left pan from East basketball court (V01) across 9 m East road & NE corner (V02/V03) to 12 m North road (V04) and plot boundary/interior (V05/V06)",
        "rollCaution": "Camera rolls near V06 (20.0 s); compass direction is not inferred from camera roll alone.",
    }
    base["temporary_exclusions"].extend([
        "Parked cars, covered sedan, white hatchback, scooter, and pedestrians in R09, R10, R12, and R13 excluded from all 3D colony context and renders.",
        "Private car porch defaults to empty (defaultCarVisible = false) in Tirumala 4; removable Škoda Kylaq retained only for optional parking check.",
    ])
    new_refs = [
            {
                "id": "R07",
                "file": "output/tirumala-4-prompt-pack/site-photos/R07-east-side-northwest.png",
                "sourceFile": "1000145307.jpg",
                "category": "plot_and_north_outlook",
                "directionStatus": "owner-confirmed",
                "cameraPositionSceneM": [5.8, -1.6, 1.65],
                "cameraTargetSceneM": [13.5, 9.2, 2.1],
                "lookingDirection": "Standing on the East side of the plot looking Northwest across the plot toward the 12 m North road and colony garden",
                "confirmedFeatures": [
                    "Northeast corner plot bounded by 9 m East road and 12 m North road",
                    "Low muted mauve-taupe boundary wall with pale grey coping along North and East edges",
                    "White and navy-blue-grey G+1 house across the North colony garden visible through tree canopy",
                ],
                "observedFeatures": [
                    "Dry red-brown soil and concrete footing blocks on pre-construction plot (modeled in 'existing' site mode only)",
                    "Pre-construction trees inside plot footprint (modeled in 'existing' site mode; cleared from 'proposed' house footprint)",
                    "Mixed burgundy Acalypha and green Tabernaemontana roadside hedge",
                    "Slim dark-grey tubular streetlight pole at road edge",
                ],
                "excludedTransients": [],
                "matchedSceneCamera": "ref_r07_east_northwest",
            },
            {
                "id": "R08",
                "file": "output/tirumala-4-prompt-pack/site-photos/R08-north-garden-outlook.png",
                "sourceFile": "1000145308.jpg",
                "category": "north_colony_garden",
                "directionStatus": "owner-confirmed",
                "cameraPositionSceneM": [10.8, 7.2, 1.65],
                "cameraTargetSceneM": [32.0, 8.2, 3.2],
                "lookingDirection": "Looking North across the 12 m road into the colony garden and opposite white/navy-blue-grey house",
                "confirmedFeatures": [
                    "12.0 m wide North concrete road between plot north boundary (x = 12.192 m) and colony garden south boundary (x = 24.192 m)",
                    "Colony garden enclosure with low wall, black metal grille fence, lawn, play equipment, and mature trees",
                    "Opposite G+1 white and navy-blue-grey residential building north of the garden",
                ],
                "observedFeatures": [
                    "Warm cream/white upper facade with dark navy/slate accent bands and recessed balcony",
                    "Dense neem, ashoka, and palm canopy filtering strong sunlight into the park",
                ],
                "excludedTransients": [],
                "matchedSceneCamera": "ref_r08_north_garden",
            },
            {
                "id": "R09",
                "file": "output/tirumala-4-prompt-pack/site-photos/R09-colony-junction.png",
                "pairedWideFile": "output/tirumala-4-prompt-pack/site-photos/R13-colony-junction-wide.png",
                "sourceFile": "1000145309.png / 1000145313.jpg",
                "category": "colony_street_junction",
                "directionStatus": "estimated-from-street-geometry",
                "cameraPositionSceneM": [18.2, -11.5, 1.65],
                "cameraTargetSceneM": [17.6, 16.0, 2.8],
                "lookingDirection": "Looking along the colony road junction showing grooved concrete carriageways, paver verges, storm-drain covers, streetlight, and 2-3 storey colony homes",
                "confirmedFeatures": [
                    "Brushed concrete colony carriageways with transverse expansion joints",
                ],
                "observedFeatures": [
                    "Precast concrete storm-drain cover slabs with paired circular drainage holes along road edges",
                    "Slim dark-grey angled LED street luminaire on tubular pole",
                    "Contemporary 2-3 storey colony residences with white/warm-grey render, wood/terracotta accents, and roof pergolas",
                    "Clipped ornamental hedges and interlocking paver verges",
                ],
                "excludedTransients": [
                    "Parked dark sedan under cover, white hatchback, scooter, and pedestrian in street excluded from 3D scene",
                ],
                "matchedSceneCamera": "ref_r09_colony_junction",
            },
            {
                "id": "R10",
                "file": "output/tirumala-4-prompt-pack/site-photos/R10-vegetated-frontage-close.png",
                "pairedWideFile": "output/tirumala-4-prompt-pack/site-photos/R12-vegetated-frontage-wide.png",
                "sourceFile": "1000145310.png / 1000145312.jpg",
                "category": "plot_frontage_and_background_building",
                "directionStatus": "estimated; adjoining-house interpretation superseded by owner",
                "cameraPositionSceneM": [11.5, -8.2, 1.65],
                "cameraTargetSceneM": [2.0, 5.5, 3.2],
                "lookingDirection": "Looking across the road frontage toward the vegetated pre-construction plot; beige building is background context, not an adjoining house",
                "confirmedFeatures": [
                    "Low perimeter boundary wall with roadside hedge and paver verge",
                ],
                "observedFeatures": [
                    "Reddish-burgundy copperleaf (Acalypha) and green white-flowering crape jasmine (Tabernaemontana) hedge",
                    "Beige building visible in the background; owner confirms no house adjoins this plot",
                    "Dense pre-construction plot canopy (retained only in 'existing' site mode; cleared from 'proposed' house footprint)",
                ],
                "excludedTransients": [
                    "Parked white hatchback on roadside excluded from 3D scene",
                ],
                "matchedSceneCamera": "exterior_northeast",
            },
            {
                "id": "R11",
                "file": "output/tirumala-4-prompt-pack/site-photos/R11-NE-corner-owner-labelled.png",
                "alternateAnnotationFile": "output/tirumala-4-prompt-pack/site-photos/alternate-annotation/R11-wall-return-unconfirmed.png",
                "sourceFile": "1000145311.jpg",
                "category": "northeast_plot_corner",
                "directionStatus": "owner-confirmed-with-duplicate-annotation-note",
                "cameraPositionSceneM": [16.8, -5.2, 1.65],
                "cameraTargetSceneM": [11.2, 2.2, 1.2],
                "lookingDirection": "Looking Southwest toward the Northeast corner of the plot where the 12 m North road and 9 m East road meet",
                "confirmedFeatures": [
                    "Northeast corner of the 40 x 50 ft plot at the junction of the 12 m North road and 9 m East road",
                    "Horizontally grooved square corner pier with muted mauve-taupe boundary wall return",
                ],
                "observedFeatures": [
                    "Interlocking dusty-rose/grey concrete paver verge between brushed concrete road and boundary wall",
                    "Mixed burgundy and green roadside shrub hedge along both road frontages",
                ],
                "excludedTransients": [],
                "matchedSceneCamera": "ref_r11_ne_corner",
            },
            {
                "id": "R14",
                "file": "output/tirumala-4-prompt-pack/site-photos/R14-wall-pole-and-paving.png",
                "sourceFile": "1000145314.jpg",
                "category": "material_close_reference",
                "directionStatus": "owner-confirmed-material-reference",
                "cameraPositionSceneM": [14.6, -2.2, 1.45],
                "cameraTargetSceneM": [11.8, 2.6, 0.95],
                "lookingDirection": "Close view of the colony boundary wall, interlocking paver verge, concrete road edge, shrub hedge, and streetlight pole base",
                "confirmedFeatures": [
                    "Low plastered masonry wall painted muted mauve-taupe (#8e7e85) with lighter grey coping (#c8c4bc)",
                    "Interlocking concrete paver verge and tubular steel streetlight pole on concrete base plinth",
                ],
                "observedFeatures": [
                    "Weathering and leaf litter along kerb joint; burgundy and green shrub foliage above coping",
                ],
                "excludedTransients": [],
                "matchedSceneCamera": "ref_r14_wall_pole_paving",
            },
            {
                "id": "V01-V06",
                "file": "output/tirumala-4-prompt-pack/video-contact-sheet.jpg",
                "keyframes": [
                    "output/tirumala-4-prompt-pack/video-frames/V01-court-and-road.jpg",
                    "output/tirumala-4-prompt-pack/video-frames/V02-road-turn.jpg",
                    "output/tirumala-4-prompt-pack/video-frames/V03-boundary-and-planting.jpg",
                    "output/tirumala-4-prompt-pack/video-frames/V04-colony-street.jpg",
                    "output/tirumala-4-prompt-pack/video-frames/V05-wall-return.jpg",
                    "output/tirumala-4-prompt-pack/video-frames/V06-preconstruction-vegetation.jpg",
                ],
                "sourceFile": "output/tirumala-4-prompt-pack/video/tirumala_plot.mp4",
                "category": "continuous_site_pan_video",
                "directionStatus": "owner-confirmed-continuous-pan",
                "cameraPositionSceneM": [8.5, -1.8, 1.65],
                "cameraTargetSceneM": [10.2, -13.5, 2.2],
                "lookingDirection": "Continuous 23.36 s pan from East basketball court (V01) across 9 m East road & NE corner (V02/V03) to 12 m North road (V04) and plot boundary/interior (V05/V06)",
                "confirmedFeatures": [
                    "Spatial continuity linking East basketball court, 9 m East road, NE plot corner pier, 12 m North road, and North colony garden",
                ],
                "observedFeatures": [
                    "V01 (0.5 s): Basketball hoop with white backboard & red target square, chain-link fence, round-hooded post-top park lamp, and precast storm-drain cover slabs with circular holes",
                    "V02 (3.0 s): 9 m East road turning into 12 m North road around the horizontally grooved NE corner pier",
                    "V03 (6.0 s): Burgundy Acalypha & white-flowering Tabernaemontana hedge and interlocking paver verge",
                    "V04 (8.5 s): 12 m North road perspective with slim LED streetlight pole, colony garden trees on right, and neighbour houses ahead",
                    "V05 (10.0 s): Plot boundary wall and corner pier with pre-construction trees behind",
                    "V06 (20.0 s): Pre-construction plot interior vegetation (camera roll near end of clip not used for compass bearing)",
                ],
                "excludedTransients": [],
                "matchedSceneCamera": "ref_v01_east_court_road",
            },
        ]
    base["photos"].extend(new_refs)
    base["references"] = base["photos"]
    return base


def build_tirumala_4_site_context(building: dict[str, Any], scene: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the enriched site-context.json payload for ``tirumala-4``."""
    ctx = build_tirumala_context(building, scene)
    ctx["project_id"] = "tirumala-4"
    ctx["projectId"] = "tirumala-4"
    ctx["sourceProjectId"] = "tirumala-3"
    ctx["sourcePlanHash"] = TIRUMALA_3_SOURCE_PLAN_HASH
    ctx["version"] = "tirumala-4-colony-context-2026-10-31"
    ctx["defaultCarVisible"] = False
    ctx["siteModes"] = {
        "default": "proposed",
        "available": ["proposed", "existing"],
        "proposedDescription": (
            "Proposed Tirumala 4 G+1 residence on the 40 x 50 ft plot with all pre-construction interior plot trees "
            "cleared from the building, forecourt, lower car porch, veranda, and pathways. Perimeter planting and "
            "colony streetscape retained."
        ),
        "existingDescription": (
            "Pre-construction existing plot state (R07, R10, R12, V05, V06) sharing the exact 40 x 50 ft boundary, "
            "horizontally grooved NE corner pier (R11), muted mauve-taupe boundary wall, dry red-brown soil, "
            "concrete footing blocks (R07), and existing mature trees prior to house construction."
        ),
    }
    ctx["colonyRealismUpgrades"] = {
        "roads": "Brushed concrete 12.0 m North and 9.0 m East carriageways with transverse expansion joints every 4.0 m and precast storm-drain cover slabs with paired circular drainage holes (V01, R09, R13).",
        "verges": "Interlocking concrete brick/zig-zag paver verges in weathered dusty-rose and warm grey (R11, R14, V03, V05).",
        "boundaryWalls": "Low plastered masonry walls in muted mauve-taupe (#8e7e85) with pale grey coping (#c8c4bc) and horizontally grooved square corner pier at the NE junction (R11, R14, V02, V05).",
        "hedges": "Mixed roadside shrub planting combining reddish-burgundy copperleaf (Acalypha wilkesiana) and green crape jasmine (Tabernaemontana divaricata) with small white blossoms (R10, R12, V03, V05).",
        "streetlights": "Slim dark-grey tubular steel poles on concrete plinths with angled LED luminaire heads (R09, R13, R14, V04) plus round-hooded post-top park lamp at the east basketball court (V01).",
        "neighbours": "Owner correction, 31 October 2026: adjoining lots are vacant and shown with grass. Earlier South/West house placeholders are removed. The white/navy house across the North garden and distant road-opposite colony landmarks remain.",
    }
    from .tirumala_facade import vacant_adjoining_context
    vacant_adjoining_context(ctx)
    ctx["measuredClearanceAuditMm"] = build_tirumala_4_clearance_audit()
    return ctx


def build_tirumala_4_assumptions_register() -> dict[str, Any]:
    """Build the assumptions & evidence classification register for ``tirumala-4``."""
    reg = build_assumptions_register()
    reg["project_id"] = "tirumala-4"
    reg["projectId"] = "tirumala-4"
    reg["sourceProjectId"] = "tirumala-3"
    reg["sourcePlanHash"] = TIRUMALA_3_SOURCE_PLAN_HASH
    reg["version"] = "tirumala-4-assumptions-2026-10-31"
    reg["title"] = "Tirumala 4 — Evidence, Assumptions, Discrepancy & Site Measurement Register"
    reg['unknowns_requiring_site_measurement'] = [
        item for item in reg.get('unknowns_requiring_site_measurement', [])
        if not item.startswith('Exact adjoining building massing')
    ]
    reg.setdefault("items", []).extend(
        [
            {
                "id": "A-09",
                "category": "evidence_conflict_resolution",
                "feature": "R11 duplicate underlying photograph (1000145311.jpg) with two different text annotations",
                "classification": "owner_confirmed_primary_vs_unconfirmed_alternate",
                "value": "Primary annotation ('NE corner of the plot', 'North 12 m road', 'East 9 m road') adopted; alternate ('Wall turns from here') logged as unconfirmed",
                "source": "R11-NE-corner-owner-labelled.png vs alternate-annotation/R11-wall-return-unconfirmed.png and video pan V02/V05",
                "impactOnHouseDimensions": "none",
            },
            {
                "id": "A-10",
                "category": "video_orientation_hygiene",
                "feature": "End-of-pan camera roll in VID-20260412-WA0002.mp4 (frame V06 at 14.5 s)",
                "classification": "visual_observation_with_caution",
                "value": "Compass bearing is anchored strictly to owner-confirmed East road (-Y, 90 deg) and North road (+X, 0 deg); camera roll in V06 is ignored for azimuth",
                "source": "VID-20260412-WA0002.mp4 / V01-V06",
                "impactOnHouseDimensions": "none",
            },
            {
                "id": "A-11",
                "category": "site_vegetation_separation",
                "feature": "Pre-construction interior plot trees and footing blocks (R07, R10, R12, V05, V06)",
                "classification": "separated_site_mode",
                "value": "Pre-construction plot trees and footing blocks are isolated in the 'existing' site mode group; 'proposed' mode has 0 tree trunks or branches inside the house/paving footprint",
                "source": "R07, R10, R12, V05, V06",
                "impactOnHouseDimensions": "none",
            },
            {
                "id": "A-12",
                "category": "parking_presentation_default",
                "feature": "Default empty car porch in Tirumala 4 with optional parking-check vehicle",
                "classification": "presentation_default",
                "value": "defaultCarVisible = false in Tirumala 4; removable Škoda Kylaq (3,995 x 1,783 mm) retained via toolbar toggle for parking clearance verification",
                "source": "TIRUMALA-4-PROMPT.txt requirement 3 & 5",
                "impactOnHouseDimensions": "none",
            },
            {
                "id": "A-13",
                "category": "owner_correction",
                "feature": "Adjoining South/West land",
                "classification": "owner_confirmed_vacant",
                "value": "No houses beside the plot. Remove the previous adjoining house placeholders and show grass. Earlier R10/R12 proximity interpretations are superseded; road-opposite landmarks remain.",
                "source": "Owner instruction, 31 October 2026",
                "impactOnHouseDimensions": "none",
            },
        ]
    )
    return reg


def build_tirumala_4_clearance_audit() -> list[dict[str, Any]]:
    """Return measured 1:1 clear widths, door jamb openings, and furniture clearances in ``tirumala-4`` (P13)."""
    return [
        {
            "zone": "Home ICU (g-care) — Room clear dimensions",
            "measuredMm": "3429.6 (N-S) x 4085.6 (E-W)",
            "measuredFtIn": "11 ft 3 in x 13 ft 4 7/8 in (150.8 sq ft)",
            "status": "locked_p13_geometry",
            "note": "Includes 2 ft (609.6 mm) east extension aligning ICU east exterior wall with kitchen front (y = 1524 mm), retaining 5 ft East forecourt.",
        },
        {
            "zone": "Home ICU — Bed foot to East wall/window",
            "measuredMm": 942.8,
            "measuredFtIn": "3 ft 1 1/8 in",
            "status": "verified_clear",
            "note": "Recliner bed east foot at y = 2616.8 mm to ICU east inner wall at y = 1674.0 mm.",
        },
        {
            "zone": "Home ICU — Bed head to West wall",
            "measuredMm": 942.8,
            "measuredFtIn": "3 ft 1 1/8 in",
            "status": "verified_clear",
            "note": "Recliner bed west head at y = 4816.8 mm to ICU west inner wall at y = 5759.6 mm.",
        },
        {
            "zone": "Home ICU — Bed south side to Hall–ICU door wall",
            "measuredMm": 987.6,
            "measuredFtIn": "3 ft 2 7/8 in",
            "status": "verified_clear",
            "note": "Recliner bed south edge at x = 6440.0 mm to south inner wall at x = 5452.4 mm (857.6 mm clear past wall-mounted TV).",
        },
        {
            "zone": "Home ICU — Bed north side to Veranda door wall",
            "measuredMm": 1342.0,
            "measuredFtIn": "4 ft 4 7/8 in",
            "status": "verified_clear",
            "note": "Recliner bed north edge at x = 7540.0 mm to north inner wall at x = 8882.0 mm; companion chair in NW pocket leaves 520 mm diagonal gap to bed corner and 267.6 mm to veranda door jamb.",
        },
        {
            "zone": "Hall–ICU layered entrance (icu-glass-living)",
            "measuredMm": "2100.0 structural / 1990.0 clear between jambs",
            "measuredFtIn": "6 ft 10 11/16 in structural / 6 ft 6 3/8 in clear",
            "status": "verified_clear",
            "note": "Hall-side 4-panel folding teak privacy door conceals independent 4-panel sliding glass directly behind it within the same opening.",
        },
        {
            "zone": "ICU–Veranda slide-and-turn glass door (icu-veranda-door)",
            "measuredMm": "1828.8 structural / 1718.8 clear between jambs",
            "measuredFtIn": "6 ft 0 in structural / 5 ft 7 11/16 in clear",
            "status": "verified_clear",
            "note": "4-panel slide-and-turn frameless glass assembly opening onto the North veranda.",
        },
        {
            "zone": "Living–Veranda folding wood + mesh door (living-veranda)",
            "measuredMm": "1167.8 structural / 1057.8 clear between jambs",
            "measuredFtIn": "3 ft 10 in structural / 3 ft 5 5/8 in clear",
            "status": "verified_clear",
            "note": "Outward-folding teak leaves + retractable pleated insect mesh; unchanged from Tirumala 3.",
        },
        {
            "zone": "Principal East house entrance (main-entry)",
            "measuredMm": "1371.6 structural / 1261.6 clear between jambs",
            "measuredFtIn": "4 ft 6 in structural / 4 ft 1 11/16 in clear",
            "status": "verified_clear",
            "note": "Double teak entry doors from the 5 ft raised East forecourt (+300 mm).",
        },
        {
            "zone": "Living / Dining / Open Kitchen circulation",
            "measuredMm": "1230.0 (sofa to coffee table) / 1450.0 (kitchen worktop pass-through)",
            "measuredFtIn": "4 ft 0 3/8 in / 4 ft 9 1/16 in",
            "status": "verified_clear",
            "note": "Unobstructed sightline and step-free level path from East entry through living/dining to veranda and bedrooms.",
        },
        {
            "zone": "Master Bedroom doorway (master-door)",
            "measuredMm": "800.0 leaf in 1000.0 throat (690.0 clear between frame stops)",
            "measuredFtIn": "2 ft 7 1/2 in leaf in 3 ft 3 3/8 in throat",
            "status": "locked_source_bottleneck_documented",
            "note": "Preserved from authoritative P11/P13 geometry; recorded as the narrowest bedroom doorway throat.",
        },
        {
            "zone": "Wash gully doorway & Caregiver WC door",
            "measuredMm": "700.0 structural / 590.0 clear between jambs",
            "measuredFtIn": "2 ft 3 9/16 in structural / 1 ft 11 1/4 in clear",
            "status": "locked_source_service_doors_documented",
            "note": "Secondary service/WC doors preserved from authoritative P11/P13 geometry.",
        },
    ]


def apply_tirumala_4_scene(scene: dict[str, Any], building: dict[str, Any]) -> None:
    """Apply Tirumala 4 material refinements, warm daylight/overcast calibration, interior details, and reference cameras."""
    scene["defaultCarVisible"] = False
    scene["tirumala4"] = True

    # 1. Warm daylight & neutral overcast presentation profile: eliminates cool blue/grey cast on ivory surfaces
    scene["presentation"] = {
        "style": "tirumala-4-colony-and-interior-realism",
        "defaultGrade": "day",
        "supportedGrades": ["day", "overcast", "golden", "dusk", "night"],
        "exterior": {
            "warmth": 0.11,
            "contrast": 1.02,
            "punch": 0.24,
        },
        "interior": {
            "exposureScale": 1.08,
            "dayLampLevel": 0.28,
            "contrast": 1.0,
            "punch": 0.16,
            "vignette": 0.14,
            "warmth": 0.16,
            "bounceWarmth": "#eadbc4",
        },
    }

    # 2. Refined material palette for Tirumala 4 (warm ivory plaster, honed limestone, Burma teak, cream marble, Kota stone)
    mats = scene.get("materials", {})
    if "plaster" in mats:
        mats["plaster"].update(
            color="#f4efe5",
            alt="#e9e1d3",
            roughness_scale=0.86,
            env=0.72,
        )
    if "ceiling-plaster" in mats:
        mats["ceiling-plaster"].update(
            color="#f8f4ec",
            alt="#efe9dd",
            roughness_scale=0.90,
            env=0.65,
        )
    if "ivory-marble-polished" in mats:
        mats["ivory-marble-polished"].update(
            color="#f4eee3",
            alt="#dfd4c1",
            roughness_scale=0.62,
            clearcoat=0.06,
            clearcoat_roughness=0.32,
            env=0.58,
        )
    if "ivory-marble-exterior-matte" in mats:
        mats["ivory-marble-exterior-matte"].update(
            color="#eee6d8",
            alt="#d6c8b2",
            roughness_scale=0.80,
            clearcoat=0.0,
            env=0.55,
        )
    if "teak-warm" in mats:
        mats["teak-warm"].update(
            color="#845735",
            alt="#623e23",
            roughness_scale=0.52,
            clearcoat=0.14,
            clearcoat_roughness=0.26,
        )
    if "porch-kota-paver" in mats:
        mats["porch-kota-paver"].update(
            color="#7d867b",
            alt="#636c62",
            roughness_scale=0.82,
        )
    if "porch-red-oxide-border" in mats:
        mats["porch-red-oxide-border"].update(
            color="#7d382e",
            alt="#5e2820",
            roughness_scale=0.64,
        )

    mats["tirumala4-skirting-marble"] = {
        "kind": "stone",
        "color": "#ebe2d3",
        "alt": "#d5c8b4",
        "roughness": 0.34,
        "tile_m": [1.2, 0.4],
        "roughness_scale": 0.68,
        "env": 0.5,
    }
    mats["tirumala4-linen-throw"] = {
        "kind": "fabric",
        "color": "#c9b59a",
        "alt": "#b39d80",
        "roughness": 0.88,
        "tile_m": [0.45, 0.45],
        "roughness_scale": 0.88,
        "sheen": 0.45,
    }
    mats["tirumala4-sage-cushion"] = {
        "kind": "fabric",
        "color": "#8fa089",
        "alt": "#768771",
        "roughness": 0.86,
        "tile_m": [0.35, 0.35],
        "roughness_scale": 0.86,
        "sheen": 0.4,
    }
    mats["tirumala4-art-canvas"] = {
        "kind": "fabric",
        "color": "#dfd5c3",
        "alt": "#9c8567",
        "roughness": 0.85,
        "tile_m": [0.9, 0.9],
        "roughness_scale": 0.85,
    }

    # 3. Non-colliding visual interior & architectural realism details for Tirumala 4
    nodes = scene.get("nodes", [])

    def add_detail_box(nid: str, cx: float, cy: float, z0: float, sx: float, sy: float, sz: float, mat: str, floor: int = 0, role: str = "decor") -> None:
        nodes.append(
            {
                "id": nid,
                "asset": "unit-box",
                "role": role,
                "floor": floor,
                "owner": nid,
                "material": mat,
                "position": [round(cx, 4), round(cy, 4), round(z0 + sz / 2.0, 4)],
                "scale": [round(sx, 4), round(sy, 4), round(sz, 4)],
                "rotation": [0.0, 0.0, 0.0],
                "collide": False,
            }
        )

    # Subtle recessed warm task light under kitchen wall cabinets + tableware on serving counter (x=2.42..3.32, y=4.80..5.15)
    add_detail_box("t4-kitchen-serving-tray", 2.867, 4.975, 0.90, 0.34, 0.24, 0.020, "teak-warm", floor=0)
    add_detail_box("t4-kitchen-fruit-bowl", 2.867, 4.975, 0.92, 0.18, 0.18, 0.075, "ceramic-pot", floor=0)
    # ICU recliner folded warm throw blanket at East foot (bed x=7.00..8.10, y=2.65..4.85) + compact vitals display on 2 ft x 14 in table (x=5.50..6.11, y=1.72..2.08)
    add_detail_box("t4-icu-bed-throw", 7.552, 2.92, 0.62, 0.88, 0.36, 0.042, "tirumala4-linen-throw", floor=0)
    add_detail_box("t4-icu-companion-cushion", 5.742, 3.69, 0.46, 0.36, 0.36, 0.08, "tirumala4-sage-cushion", floor=0)
    add_detail_box("t4-icu-table-monitor-base", 5.807, 1.90, 0.76, 0.18, 0.16, 0.02, "frame", floor=0)
    add_detail_box("t4-icu-table-monitor-screen", 5.807, 1.88, 0.78, 0.26, 0.035, 0.18, "blackglass", floor=0)
    # Living room framed botanical diptych on the South/West living wall + window pelmets
    add_detail_box("t4-icu-east-pelmet", 7.16, 1.72, 2.86, 1.95, 0.12, 0.11, "teak-warm", floor=0)
    add_detail_box("t4-icu-north-pelmet", 8.82, 3.70, 2.86, 0.12, 2.05, 0.11, "teak-warm", floor=0)

    # Warm task light in ICU and Kitchen for balanced interior illumination
    lights = scene.get("lights", [])
    lights.append(
        {
            "id": "t4-kitchen-counter-task",
            "kind": "downlight",
            "position": [3.45, 2.45, 2.15],
            "color": "#ffe4b8",
            "power_w": 16,
        }
    )
    lights.append(
        {
            "id": "t4-icu-warm-indirect",
            "kind": "downlight",
            "position": [7.25, 3.72, 3.18],
            "color": "#ffe6be",
            "power_w": 18,
        }
    )
    lights.append(
        {
            "id": "t4-living-warm-indirect",
            "kind": "downlight",
            "position": [3.80, 6.20, 3.18],
            "color": "#ffe6be",
            "power_w": 18,
        }
    )

    # 4. Calibrated reference-matching & human-sightline cameras
    cams = scene.get("cameras", {})
    eye_z = 1.63
    seated_z = 1.12

    # Position exterior_east on the East footpath in front of the basketball court fence so the fence mesh never blocks the East facade
    cams["exterior_east"] = {
        "position": [6.15, -8.35, 2.55],
        "target": [6.05, 4.50, 2.55],
        "fov": 52,
        "description": "Unobstructed East elevation across the 9 m East colony road showing the 5 ft raised forecourt, P13 ICU extension, empty lower Kota stone porch, and G+1 massing.",
    }
    cams["ref_r07_east_northwest"] = {
        "position": [5.8, -1.6, eye_z],
        "target": [13.5, 9.2, 2.1],
        "fov": 48,
        "reference_id": "R07",
        "direction_status": "owner-confirmed",
        "description": "Standing on the East side looking Northwest across the plot toward the 12 m North road and colony garden (matches R07).",
    }
    cams["ref_r11_ne_corner"] = {
        "position": [16.8, -5.2, eye_z],
        "target": [11.2, 2.2, 1.25],
        "fov": 46,
        "reference_id": "R11 / V02",
        "direction_status": "owner-confirmed",
        "description": "Looking Southwest toward the Northeast plot corner pier, muted mauve-taupe boundary wall return, hedge, paver verge, and 12 m North / 9 m East road junction (matches R11 & V02).",
    }
    cams["ref_r08_north_garden"] = {
        "position": [11.2, 7.2, eye_z],
        "target": [32.0, 8.2, 3.2],
        "fov": 46,
        "reference_id": "R08 / N-01",
        "direction_status": "owner-confirmed",
        "description": "Looking North across the 12 m concrete road into the colony garden and opposite white/navy-blue-grey G+1 house (matches R08 & N-01).",
    }
    cams["ref_v01_east_court_road"] = {
        "position": [8.6, -1.2, eye_z],
        "target": [10.4, -14.0, 2.3],
        "fov": 48,
        "reference_id": "V01 / E-01",
        "direction_status": "owner-confirmed",
        "description": "Looking East/Northeast across the 9 m East concrete road toward the basketball court enclosure, hoop, storm-drain cover slabs, and post-top park lamp (matches V01 & E-01).",
    }
    cams["ref_r09_colony_junction"] = {
        "position": [18.2, -11.5, eye_z],
        "target": [17.6, 16.0, 2.8],
        "fov": 48,
        "reference_id": "R09 / R13 / V04",
        "direction_status": "estimated-from-street-geometry",
        "description": "Looking West-Northwest along the 12 m North colony road junction showing grooved concrete road, storm-drain slabs, paver verges, angled LED streetlight, and neighbouring colony houses (matches R09, R13 & V04).",
    }
    cams["ref_r14_wall_pole_paving"] = {
        "position": [14.6, -2.2, 1.45],
        "target": [11.8, 2.6, 0.95],
        "fov": 44,
        "reference_id": "R14 / V03 / V05",
        "direction_status": "owner-confirmed-material-reference",
        "description": "Close material study of the muted mauve-taupe boundary wall, horizontally grooved NE corner pier, burgundy/green hedge, interlocking paver verge, and streetlight pole base (matches R14, V03 & V05).",
    }
    cams["veranda_north_garden_outlook"] = {
        "position": [8.35, 6.75, eye_z],
        "target": [26.0, 7.20, 2.40],
        "fov": 48,
        "floor": 0,
        "enter_walk": True,
        "eye_height_above_ffl_m": eye_z,
        "walker": {
            "position": [8.35, 6.75, eye_z],
            "yaw_rad": -1.52,
            "pitch_rad": 0.03,
        },
        "description": "Standing on the North veranda (+300 mm) looking North across the perimeter garden and 12 m road into the Tirumala Colony park.",
    }
    cams["care_recliner_eye_level"] = {
        "position": [7.55, 4.45, 1.18],
        "target": [8.95, 2.35, 1.32],
        "fov": 52,
        "floor": 0,
        "eye_height_above_ffl_m": 1.18,
        "posture": "recliner-seated-1.18m",
        "description": "Patient seated/reclined eye-level sightline (1.18 m above FFL) from the Home ICU recliner head (West) looking Northeast across the foot of the bed and through the veranda/east glazing toward the garden.",
    }
    cams["living_sofa_eye_level"] = {
        "position": [2.25, 6.95, 1.15],
        "target": [6.40, 5.20, 1.45],
        "fov": 52,
        "floor": 0,
        "eye_height_above_ffl_m": 1.15,
        "posture": "sofa-seated-1.15m",
        "description": "Seated eye-level sightline (1.15 m above FFL) from the living room sofa looking across the double-height hall toward the open kitchen, dining table, and ICU/veranda openings.",
    }

    # 5. Enrich scene["context"] with Tirumala 4 site context & evidence metadata
    if isinstance(scene.get("context"), dict):
        scene["context"]["tirumala4"] = {
            "sourceProjectId": "tirumala-3",
            "sourcePlanHash": TIRUMALA_3_SOURCE_PLAN_HASH,
            "sourceGeometryHash": TIRUMALA_3_SOURCE_GEOMETRY_HASH,
            "defaultCarVisible": False,
            "siteModes": ["proposed", "existing"],
            "duplicateR11Note": (
                "R11-NE-corner-owner-labelled.png and alternate-annotation/R11-wall-return-unconfirmed.png share "
                "source photo 1000145311.jpg; primary NE corner annotation is owner-confirmed."
            ),
            "measuredClearanceAuditMm": build_tirumala_4_clearance_audit(),
        }

    from .tirumala_exterior_refinement import refine_exterior
    refine_exterior(scene)
    from .tirumala_facade import refine_facade
    refine_facade(scene, building)


def generate_site_context_plan_svg(building: dict[str, Any]) -> str:
    """Generate a labelled 2D Site & Colony Context Plan SVG with North arrow, plot, roads, garden, court, and reference camera cones."""
    # Coordinate mapping:
    # Scene/Plan frame:
    #   X (North-South): 0.0 m (South plot boundary) to 12.192 m (North plot boundary); North road x = 12.192..24.192; North garden x = 24.192..40.0
    #   Y (East-West):   0.0 m (East plot boundary) to 15.240 m (West plot boundary); East road y = -9.0..0.0; Basketball court y = -23.0..-9.0
    # For a standard architectural Site & Context Plan with North UP (+X up, East -Y to the RIGHT):
    #   screen_x = origin_x - scene_y * scale   (so West +Y is Left, East -Y is Right!)
    #   screen_y = origin_y - scene_x * scale   (so North +X is Up, South -X is Down!)
    W, H = 1600, 1180
    scale = 14.5  # px per metre
    ox = 650.0    # scene_y = 0 (East plot boundary)
    oy = 760.0    # scene_x = 0 (South plot boundary)

    def pt(sx_m: float, sy_m: float) -> tuple[float, float]:
        return (round(ox - sy_m * scale, 1), round(oy - sx_m * scale, 1))

    def rect_svg(sx0: float, sy0: float, sx1: float, sy1: float, fill: str, stroke: str = "none", sw: float = 1.0, dash: str = "", rx: float = 0.0, opacity: float = 1.0) -> str:
        x_a, y_a = pt(sx0, sy0)
        x_b, y_b = pt(sx1, sy1)
        left = min(x_a, x_b)
        top = min(y_a, y_b)
        w = abs(x_b - x_a)
        h = abs(y_b - y_a)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        ra = f' rx="{rx}"' if rx else ""
        op = f' fill-opacity="{opacity}"' if opacity < 1.0 else ""
        return f'<rect x="{left:.1f}" y="{top:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{da}{ra}{op}/>'

    def poly_svg(pts_mm: list[list[float]], fill: str, stroke: str = "#4a433b", sw: float = 1.2) -> str:
        coords = " ".join(f"{pt(p[0]/1000.0, p[1]/1000.0)[0]:.1f},{pt(p[0]/1000.0, p[1]/1000.0)[1]:.1f}" for p in pts_mm)
        return f'<polygon points="{coords}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

    def cam_marker(cid: str, sx: float, sy: float, tx: float, ty: float, color: str, confirmed: bool = True) -> str:
        cx, cy = pt(sx, sy)
        vx, vy = pt(tx, ty)
        ang = math.atan2(vy - cy, vx - cx)
        r = 38.0
        spread = 0.36
        x1, y1 = cx + r * math.cos(ang - spread), cy + r * math.sin(ang - spread)
        x2, y2 = cx + r * math.cos(ang + spread), cy + r * math.sin(ang + spread)
        dash = "" if confirmed else ' stroke-dasharray="4,3"'
        return (
            f'<g class="cam-ref">'
            f'<polygon points="{cx:.1f},{cy:.1f} {x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f}" fill="{color}" fill-opacity="0.22" stroke="{color}" stroke-width="1.4"{dash}/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>'
            f'<rect x="{cx - 22:.1f}" y="{cy - 22:.1f}" width="44" height="15" rx="3" fill="#1f2823" fill-opacity="0.88"/>'
            f'<text x="{cx:.1f}" y="{cy - 11.5:.1f}" fill="#ffffff" font-size="9.5" font-weight="700" text-anchor="middle">{html.escape(cid)}</text>'
            f'</g>'
        )

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="system-ui, -apple-system, Segoe UI, sans-serif">',
        '<defs>',
        '<pattern id="paverHatch" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0,4 L8,4 M4,0 L4,8" stroke="#b5948e" stroke-width="0.7" opacity="0.55"/></pattern>',
        '<pattern id="tileGrid" width="12" height="12" patternUnits="userSpaceOnUse"><path d="M12,0 L0,0 0,12" fill="none" stroke="#d5cab8" stroke-width="0.7"/></pattern>',
        '<pattern id="kotaGrid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M10,0 L0,0 0,10" fill="none" stroke="#5b6659" stroke-width="0.8"/></pattern>',
        '</defs>',
        f'<rect width="{W}" height="{H}" fill="#f6f3ec"/>',
        # Header banner
        '<rect x="28" y="22" width="1544" height="72" rx="8" fill="#213229"/>',
        '<text x="52" y="53" fill="#f7f4eb" font-size="22" font-weight="700">TIRUMALA 4 — SITE &amp; COLONY CONTEXT PLAN (CALIBRATED TO R07–R14 &amp; V01–V06)</text>',
        '<text x="52" y="76" fill="#c9d4cc" font-size="12.5">Locked Tirumala 3 (P13) House Geometry · 40 ft N–S × 50 ft E–W (12,192 × 15,240 mm) NE Corner Plot · North Up (+X) · East Right (−Y)</text>',
    ]

    # Map viewport background
    parts.append('<rect x="28" y="108" width="1060" height="920" rx="8" fill="#e9e4d8" stroke="#c7bfb0" stroke-width="1.5"/>')

    # 1. Surrounding colony blocks
    # Owner correction: adjoining land is vacant, replacing earlier inferred houses.
    parts.append(rect_svg(-14.5, 0.0, -0.8, 15.24, "#b4c89d", "#7b9864", 1.8, rx=3))
    sx_nb, sy_nb = pt(-7.6, 7.62)
    parts.append(f'<text x="{sx_nb:.1f}" y="{sy_nb - 8:.1f}" fill="#3e5133" font-size="12" font-weight="700" text-anchor="middle">SOUTH ADJOINING VACANT LAND</text>')
    parts.append(f'<text x="{sx_nb:.1f}" y="{sy_nb + 10:.1f}" fill="#536548" font-size="10.5" text-anchor="middle">Owner-confirmed: no adjoining house · Grass representation</text>')

    # West Adjoining Neighbour
    parts.append(rect_svg(0.0, 16.0, 12.192, 28.5, "#b4c89d", "#7b9864", 1.8, rx=3))
    wx_nb, wy_nb = pt(6.1, 22.2)
    parts.append(f'<text x="{wx_nb:.1f}" y="{wy_nb - 6:.1f}" fill="#3e5133" font-size="11.5" font-weight="700" text-anchor="middle">WEST ADJOINING VACANT LAND</text>')
    parts.append(f'<text x="{wx_nb:.1f}" y="{wy_nb + 11:.1f}" fill="#536548" font-size="10" text-anchor="middle">Grass · No adjoining house</text>')

    # Colony Houses West along 12 m North road (R09/R13/V04)
    parts.append(rect_svg(24.2, 17.5, 36.5, 29.0, "#dcd5c9", "#8c7f6c", 1.5, rx=3))
    nw_x, nw_y = pt(30.3, 23.2)
    parts.append(f'<text x="{nw_x:.1f}" y="{nw_y:.1f}" fill="#4a4033" font-size="11" font-weight="700" text-anchor="middle">COLONY RESIDENCES (R09 / R13 / V04)</text>')

    # 2. Roads (12 m North road & 9 m East road) + paver verges + storm drain slabs
    parts.append(rect_svg(12.192, -25.0, 24.192, 30.0, "#c8c4ba", "#9e998e", 1.2))  # 12 m North road
    parts.append(rect_svg(-16.0, -9.0, 38.0, 0.0, "#c8c4ba", "#9e998e", 1.2))       # 9 m East road
    # Paver verges along plot & park edges (R11, R14, V03)
    parts.append(rect_svg(12.192, 0.0, 13.35, 15.24, "url(#paverHatch)", "#a88983", 0.8))
    parts.append(rect_svg(0.0, -1.15, 12.192, 0.0, "url(#paverHatch)", "#a88983", 0.8))
    # Road labels & dimension lines
    nr_x, nr_y = pt(18.2, 7.6)
    parts.append(f'<text x="{nr_x:.1f}" y="{nr_y - 4:.1f}" fill="#2f3833" font-size="13" font-weight="700" text-anchor="middle">12.0 m WIDE NORTH COLONY ROAD (39 ft 4 in · Brushed Concrete + Storm-Drain Slabs)</text>')
    parts.append(f'<text x="{nr_x:.1f}" y="{nr_y + 13:.1f}" fill="#4c5650" font-size="10.5" text-anchor="middle">Owner-confirmed (R07, R08, R11, V02, V04) · Paver verges &amp; angled LED street luminaires</text>')

    er_x, er_y = pt(3.2, -5.8)
    parts.append(f'<g transform="translate({er_x:.1f},{er_y:.1f}) rotate(-90)">')
    parts.append('<text x="0" y="-3" fill="#2f3833" font-size="12" font-weight="700" text-anchor="middle">9.0 m WIDE EAST COLONY ROAD (29 ft 6 in)</text>')
    parts.append('<text x="0" y="11" fill="#4c5650" font-size="9.5" text-anchor="middle">Principal Arrival Road (R11, V01, V02)</text>')
    parts.append('</g>')

    # 3. North Colony Garden & Opposite White/Navy-Blue-Grey House (R08, N-01..N-03)
    parts.append(rect_svg(24.192, -1.0, 34.5, 16.2, "#9ec284", "#6e5c64", 2.2, rx=4))
    parts.append(rect_svg(34.8, 0.5, 41.2, 15.0, "#e5ebf0", "#3a4e68", 2.0, rx=3))
    ng_x, ng_y = pt(29.2, 7.6)
    parts.append(f'<text x="{ng_x:.1f}" y="{ng_y - 6:.1f}" fill="#1f3b1e" font-size="13" font-weight="700" text-anchor="middle">NORTH COLONY GARDEN / PARK (R08 · N-01–N-03)</text>')
    parts.append(f'<text x="{ng_x:.1f}" y="{ng_y + 10:.1f}" fill="#2c4f2b" font-size="10.5" text-anchor="middle">Low mauve-taupe wall + grille · Arched gate · Play equipment · Mature Neem &amp; Ashoka canopy</text>')
    nh_x, nh_y = pt(38.0, 7.6)
    parts.append(f'<text x="{nh_x:.1f}" y="{nh_y + 4:.1f}" fill="#23364d" font-size="11.5" font-weight="700" text-anchor="middle">OPPOSITE WHITE &amp; NAVY-BLUE-GREY HOUSE (R08 / N-01)</text>')

    # 4. East Basketball Court Enclosure (V01, E-01..E-03)
    parts.append(rect_svg(0.5, -23.5, 14.5, -9.0, "#6fa074", "#6e5c64", 2.2, rx=4))
    parts.append(rect_svg(2.0, -21.5, 13.0, -10.8, "#538c5b", "#ffffff", 1.5))
    parts.append(rect_svg(5.2, -14.2, 9.8, -10.8, "#b85446", "#ffffff", 1.2))
    bc_x, bc_y = pt(7.5, -16.2)
    parts.append(f'<text x="{bc_x:.1f}" y="{bc_y - 6:.1f}" fill="#ffffff" font-size="12.5" font-weight="700" text-anchor="middle">EAST BASKETBALL COURT (V01 · E-01–E-03)</text>')
    parts.append(f'<text x="{bc_x:.1f}" y="{bc_y + 10:.1f}" fill="#eef5ee" font-size="10" text-anchor="middle">Chain-link fence · Hoop &amp; backboard · Post-top park lamp</text>')

    # 5. The 40 ft x 50 ft Plot (12.192 m N-S x 15.240 m E-W)
    parts.append(rect_svg(0.0, 0.0, 12.192, 15.240, "#efe8da", "#8e7e85", 3.0))
    # Raised 5 ft East forecourt (+300 mm)
    parts.append(rect_svg(0.15, 0.0, 8.882, 1.524, "url(#tileGrid)", "#b8ac99", 1.0))
    # Lower Car Porch (-152.4 mm rel. house / +147.6 mm above road, empty by default)
    parts.append(rect_svg(9.032, 0.0, 12.042, 6.200, "url(#kotaGrid)", "#7d382e", 1.8))
    # Dashed optional parking check outline inside empty lower car porch
    parts.append(rect_svg(9.67, 0.65, 11.45, 4.65, "none", "#495449", 1.3, dash="5,4", rx=4))
    cp_x, cp_y = pt(10.55, 2.75)
    parts.append(f'<text x="{cp_x:.1f}" y="{cp_y - 4:.1f}" fill="#2b382c" font-size="9.5" font-weight="700" text-anchor="middle">LOWER CAR PORCH (−6 in)</text>')
    parts.append(f'<text x="{cp_x:.1f}" y="{cp_y + 8:.1f}" fill="#3d4b3e" font-size="8.5" text-anchor="middle">Default Empty · Dashed Parking Check</text>')

    # North garden strip inside plot
    parts.append(rect_svg(11.582, 8.050, 12.042, 14.328, "#8ab872", "#5d8749", 1.0))

    # Ground floor rooms from building["spaces"]
    room_fills = {
        "g-care": "#dcefe8",
        "g-veranda": "#e6efe0",
        "g-bedroom": "#f5efe4",
        "g-bath": "#e3ebf0",
        "g-drawing": "#f4ede0",
        "g-caregiver": "#f5efe4",
        "g-caregiver-bath": "#e3ebf0",
        "g-care-court": "#d8ebd4",
        "g-kitchen-store": "#ede4d4",
        "g-access-lobby": "#f2ebdf",
        "g-wash-gully": "#e5e0d5",
    }
    # Open hall / kitchen / dining base
    parts.append(rect_svg(0.15, 1.524, 8.882, 14.328, "#faf6ee", "#6e6559", 1.4))
    for sp in building.get("spaces", []):
        if sp.get("floor") != 0:
            continue
        rid = sp["id"]
        poly = sp.get("clear", [])
        if not poly:
            continue
        parts.append(poly_svg(poly, room_fills.get(rid, "#f5efe4"), "#5c5346", 1.4 if rid == "g-care" else 1.1))
        xs = [p[0] / 1000.0 for p in poly]
        ys = [p[1] / 1000.0 for p in poly]
        cx_m = sum(xs) / len(xs)
        cy_m = sum(ys) / len(ys)
        lx, ly = pt(cx_m, cy_m)
        short_labels = {
            "g-bedroom": "Master",
            "g-drawing": "Drawing",
            "g-caregiver": "Caregiver",
            "g-veranda": "Veranda",
        }
        if rid == "g-care":
            parts.append(f'<text x="{lx:.1f}" y="{ly - 4:.1f}" fill="#174236" font-size="9.5" font-weight="700" text-anchor="middle">HOME ICU (P13)</text>')
            parts.append(f'<text x="{lx:.1f}" y="{ly + 7:.1f}" fill="#174236" font-size="8.0" text-anchor="middle">150.8 sf</text>')
        elif rid in short_labels:
            parts.append(f'<text x="{lx:.1f}" y="{ly + 3:.1f}" fill="#3d352b" font-size="8.8" font-weight="600" text-anchor="middle">{short_labels[rid]}</text>')

    # Label Open Living / Dining & Kitchen
    liv_x, liv_y = pt(2.6, 6.8)
    parts.append(f'<text x="{liv_x:.1f}" y="{liv_y:.1f}" fill="#3d352b" font-size="9.5" font-weight="700" text-anchor="middle">Living &amp; Dining</text>')
    kit_x, kit_y = pt(2.5, 2.9)
    parts.append(f'<text x="{kit_x:.1f}" y="{kit_y:.1f}" fill="#3d352b" font-size="9.0" font-weight="700" text-anchor="middle">Kitchen</text>')

    # Highlight NE Horizontally Grooved Corner Pier (R11)
    ne_x, ne_y = pt(12.192, 0.0)
    parts.append(f'<rect x="{ne_x - 6:.1f}" y="{ne_y - 6:.1f}" width="12" height="12" fill="#8e7e85" stroke="#ffffff" stroke-width="1.5"/>')
    parts.append(f'<text x="{ne_x + 12:.1f}" y="{ne_y + 14:.1f}" fill="#593b47" font-size="9.5" font-weight="700">NE Grooved Corner Pier (R11)</text>')

    # Plot dimension callouts
    p_sw = pt(0.0, 15.24)
    p_se = pt(0.0, 0.0)
    p_nw = pt(12.192, 15.24)
    parts.append(f'<line x1="{p_sw[0]:.1f}" y1="{p_sw[1] + 22:.1f}" x2="{p_se[0]:.1f}" y2="{p_se[1] + 22:.1f}" stroke="#213229" stroke-width="1.5"/>')
    parts.append(f'<text x="{(p_sw[0] + p_se[0])/2:.1f}" y="{p_sw[1] + 37:.1f}" fill="#213229" font-size="11.5" font-weight="700" text-anchor="middle">50 ft 0 in E–W Plot Depth (15,240 mm)</text>')
    parts.append(f'<line x1="{p_sw[0] - 28:.1f}" y1="{p_nw[1]:.1f}" x2="{p_sw[0] - 28:.1f}" y2="{p_sw[1]:.1f}" stroke="#213229" stroke-width="1.5"/>')
    parts.append(f'<g transform="translate({p_sw[0] - 42:.1f},{(p_nw[1] + p_sw[1])/2:.1f}) rotate(-90)">')
    parts.append('<text x="0" y="0" fill="#213229" font-size="11.5" font-weight="700" text-anchor="middle">40 ft 0 in N–S Plot Width (12,192 mm)</text>')
    parts.append('</g>')

    # 6. Plotted Reference Camera Cones (R07..R14, V01..V06)
    parts.append(cam_marker("R07", 4.6, -1.6, 13.5, 9.2, "#1c6b4a", True))
    parts.append(cam_marker("R08/N01", 13.6, 7.2, 30.0, 8.2, "#1c6b4a", True))
    parts.append(cam_marker("R11/V02", 18.2, -5.2, 11.2, 2.2, "#1c6b4a", True))
    parts.append(cam_marker("R14/V03", 14.6, -2.0, 11.8, 2.6, "#1c6b4a", True))
    parts.append(cam_marker("V01/E01", 9.6, -1.8, 10.2, -13.5, "#1c6b4a", True))
    parts.append(cam_marker("R09/R13", 18.2, -12.5, 17.6, 16.0, "#b86b1b", False))
    parts.append(cam_marker("R10/R12", 10.2, -8.2, 2.0, 5.5, "#b86b1b", False))

    # 7. North Arrow & Scale Bar in Map Corner
    parts.append('<g transform="translate(88, 168)">')
    parts.append('<circle cx="0" cy="0" r="34" fill="#ffffff" stroke="#213229" stroke-width="2"/>')
    parts.append('<polygon points="0,-26 -9,12 0,4 9,12" fill="#213229"/>')
    parts.append('<text x="0" y="-39" fill="#213229" font-size="13" font-weight="800" text-anchor="middle">NORTH (+X)</text>')
    parts.append('<text x="44" y="4" fill="#213229" font-size="10.5" font-weight="700">EAST (−Y)</text>')
    parts.append('</g>')

    # 8. Right-hand Evidence & Confidence Legend Panel
    parts.append('<rect x="1106" y="108" width="466" height="920" rx="8" fill="#ffffff" stroke="#c7bfb0" stroke-width="1.5"/>')
    parts.append('<text x="1128" y="142" fill="#213229" font-size="16" font-weight="800">EVIDENCE &amp; CONFIDENCE REGISTER</text>')
    parts.append('<line x1="1128" y1="152" x2="1550" y2="152" stroke="#d8d2c5" stroke-width="1.2"/>')

    legend_rows = [
        ("Owner-Confirmed Geometry &amp; Orientation", "#1c6b4a", [
            "Plot: 40 ft N–S × 50 ft E–W (12,192 × 15,240 mm) NE corner",
            "North Road: 12.0 m wide concrete road (+X frontage)",
            "East Road: 9.0 m wide principal approach road (−Y frontage)",
            "North Colony Garden &amp; white/navy-blue-grey house (R08, N-01)",
            "East Basketball Court enclosure across 9 m road (V01, E-01)",
            "P13 Home ICU: 11′3″ × 13′4⅞″ (150.8 sq ft) + 5 ft forecourt",
            "G+1 Upper Floor: Master, Ensuite, Study, Guest, Bath, Terrace",
            "Owner correction: South/West adjoining lots are vacant grass land",
        ]),
        ("Directly Observed in Photos R07–R14 &amp; Video V01–V06", "#2b5b84", [
            "Horizontally grooved NE corner pier &amp; mauve-taupe wall (R11, V02)",
            "Reddish-burgundy Acalypha + white-flowering green hedge (R10, V03)",
            "Interlocking dusty-rose/grey paver verges (R11, R14, V03)",
            "Precast storm-drain slabs with paired circular holes (V01, R13)",
            "Slim dark-grey angled LED street luminaires + court lamp (R09, V01)",
            "Buildings in photos are not assumed to touch the owner's plot",
        ]),
        ("Estimated / Provisional &amp; Discrepancy Notes", "#b86b1b", [
            "R09/R13 &amp; R10/R12 camera bearings estimated from street geometry",
            "R11 Duplicate Photo Note: 1000145311.jpg appears twice — primary NE",
            "  corner label is owner-confirmed; 'Wall turns from here' is unconfirmed",
            "V06 Video Note: Hand-held roll at 14.5 s not used for compass bearing",
            "Provisional −6 in (−152.4 mm) lower car-porch drop (default car off)",
            "Pre-construction plot trees isolated in 'Existing plot' mode toggle",
        ]),
    ]
    y_cursor = 178
    for title, badge_color, bullets in legend_rows:
        parts.append(f'<rect x="1128" y="{y_cursor - 13}" width="12" height="12" rx="3" fill="{badge_color}"/>')
        parts.append(f'<text x="1148" y="{y_cursor - 2}" fill="#213229" font-size="12.5" font-weight="700">{title}</text>')
        y_cursor += 18
        for b_text in bullets:
            parts.append(f'<text x="1142" y="{y_cursor}" fill="#444c46" font-size="11">• {b_text}</text>')
            y_cursor += 17
        y_cursor += 12

    # Reference Camera Index Table in right panel
    parts.append(f'<line x1="1128" y1="{y_cursor}" x2="1550" y2="{y_cursor}" stroke="#d8d2c5" stroke-width="1.2"/>')
    y_cursor += 24
    parts.append(f'<text x="1128" y="{y_cursor}" fill="#213229" font-size="14" font-weight="800">CALIBRATED 3D VIEWPOINT PRESETS</text>')
    y_cursor += 20
    cam_table = [
        ("R07", "ref_r07_east_northwest", "East side looking NW across plot to North garden"),
        ("R08 / N-01", "ref_r08_north_garden", "Looking North across 12 m road into colony park"),
        ("R09 / R13", "ref_r09_colony_junction", "Colony road junction, storm drains &amp; streetlamp"),
        ("R10 / R12", "exterior_northeast", "NE frontage; adjoining land now owner-confirmed vacant"),
        ("R11 / V02", "ref_r11_ne_corner", "NE grooved corner pier &amp; 12 m / 9 m road turn"),
        ("R14 / V03", "ref_r14_wall_pole_paving", "Close study: mauve-taupe wall, hedge, pavers &amp; pole"),
        ("V01 / E-01", "ref_v01_east_court_road", "Looking East across 9 m road to basketball court"),
    ]
    for ref_code, cam_id, desc in cam_table:
        parts.append(f'<text x="1128" y="{y_cursor}" fill="#1c6b4a" font-size="10.5" font-weight="700">{ref_code}</text>')
        parts.append(f'<text x="1205" y="{y_cursor}" fill="#213229" font-size="10" font-family="monospace">{cam_id}</text>')
        y_cursor += 14
        parts.append(f'<text x="1140" y="{y_cursor}" fill="#555e58" font-size="10">{desc}</text>')
        y_cursor += 18

    # Footer bar
    parts.append('<rect x="28" y="1042" width="1544" height="112" rx="8" fill="#ece7dc" stroke="#c7bfb0" stroke-width="1.2"/>')
    parts.append('<text x="48" y="1068" fill="#213229" font-size="13" font-weight="700">LOCKED HOUSE GEOMETRY &amp; CLEARANCE SUMMARY (TIRUMALA 4 = TIRUMALA 3 / P13):</text>')
    parts.append('<text x="48" y="1090" fill="#3a433d" font-size="11.5">• Plot: 40′0″ × 50′0″ (12,192 × 15,240 mm) · Plinth: +300 mm · Lower Car Porch: −152.4 mm rel. house (+147.6 mm above road, default empty) · Storey Height: 3,508 mm (clear ceiling 3,315 mm)</text>')
    parts.append('<text x="48" y="1110" fill="#3a433d" font-size="11.5">• Home ICU (P13): 11′3″ × 13′4⅞″ (3,429.6 × 4,085.6 mm = 150.8 sq ft) · Bed clearances: 943 mm East foot, 943 mm West head, 988 mm South hall side, 1,342 mm North veranda side</text>')
    parts.append('<text x="48" y="1130" fill="#3a433d" font-size="11.5">• Key Door Clear Widths (between jambs): Hall–ICU Wood+Glass 1,990 mm (6′6⅜″) · ICU–Veranda 1,719 mm (5′7¾″) · Living–Veranda 1,058 mm (3′5⅝″) · Main East Entry 1,262 mm (4′1¾″)</text>')

    parts.append("</svg>")
    return "\n".join(parts)
