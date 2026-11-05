#!/usr/bin/env python3
"""Build or verify the 'Tirumala' 40 x 50 ft (2,000 sq ft) Northeast corner sample project.

Preserves every existing sample project and only writes Tirumala's own brief, sample directory,
evidence assets, and single catalogue entry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from floorforge.custom_plan import SCHEMA
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.pipeline import deterministic_zip, run
from floorforge.review import validate
from floorforge.tirumala_context import (
    PLOT_EW_MIDPOINT_M,
    TIRUMALA_CONTEXT_STYLE,
    TIRUMALA_ID,
    build_assumptions_register,
    build_photo_reference_manifest,
    build_tirumala_context,
    local_mm_to_geo_m,
)

GALLERY_DIR = ROOT / "examples" / "gallery"
BRIEFS_DIR = GALLERY_DIR / "briefs"
OUT_DIR = GALLERY_DIR / TIRUMALA_ID
EVIDENCE_DIR = ROOT / "evidence" / TIRUMALA_ID
CATALOG_PATH = GALLERY_DIR / "catalog.json"


def rect(x0: int, y0: int, x1: int, y1: int) -> list[list[int]]:
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def op(ident: str, room_id: str, side: str, offset: int, width: int, kind: str = "cased", height: int = 2100, sill: int = 0, **extra) -> dict:
    return {
        "id": ident,
        "roomId": room_id,
        "side": side,
        "offset": offset,
        "width": width,
        "kind": kind,
        "height": height,
        "sill": sill,
        "hinge": extra.pop("hinge", "start"),
        **extra,
    }


def tirumala_project() -> dict:
    """Authoritative 40 ft (N-S East frontage = 12,192 mm) x 50 ft (E-W North boundary = 15,240 mm)
    project payload for Tirumala (2,000 sq ft NE corner plot, East-facing entrance)."""
    W_env, D_env = 9900, 12150
    plan = {
        "schema": SCHEMA,
        "units": "mm",
        "wallThickness": 150,
        "frontCourt": "planted",
        "facadeStyle": "warm-layered",
        "entranceStyle": "wall-supported",
        "interiorFloor": "ivory-vitrified",
        "colonyContext": TIRUMALA_CONTEXT_STYLE,
        "doorsClosed": False,
        "floors": [
            {
                "id": "floor-0",
                "rooms": [
                    {
                        "id": "g-living",
                        "name": "Entrance, Sitting, Living & Dining Hall",
                        "kind": "living",
                        "polygon": [
                            [2500, 150],
                            [4900, 150],
                            [4900, 5750],
                            [6350, 5750],
                            [6350, 7150],
                            [2500, 7150],
                        ],
                        "diningPosition": [3750, 1850],
                        "diningOrientation": 0,
                        "diningLength": 1500,
                        "diningCounterGap": 600,
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "g-care",
                        "name": "Residential Care Room (Home ICU)",
                        "kind": "care-room",
                        "polygon": rect(5050, 150, 8550, 5600),
                        "careLayout": "equipment-left",
                        "reclinerPosition": [6950, 2750],
                        "tvOffset": 1850,
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "g-veranda",
                        "name": "North L-Shaped Shaded Veranda",
                        "kind": "veranda",
                        "polygon": [
                            [8700, 0],
                            [9900, 0],
                            [9900, 9800],
                            [8700, 9800],
                            [8700, 7150],
                            [6500, 7150],
                            [6500, 5750],
                            [8700, 5750],
                        ],
                        "finishStyle": "warm-stone",
                        "clearAccess": True,
                        "drain": True,
                    },
                    {
                        "id": "g-kitchen",
                        "name": "Sociable Modular Kitchen",
                        "kind": "kitchen",
                        "polygon": rect(150, 150, 2350, 2750),
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "g-puja",
                        "name": "Open Puja Alcove",
                        "kind": "pooja",
                        "polygon": rect(150, 2900, 2350, 3800),
                        "altarWall": "left",
                    },
                    {
                        "id": "g-utility",
                        "name": "Pantry & Utility Room",
                        "kind": "utility",
                        "polygon": rect(150, 3950, 2350, 5600),
                        "drain": True,
                    },
                    {
                        "id": "g-stair",
                        "name": "Staircase",
                        "kind": "stair",
                        "polygon": rect(150, 5750, 2350, 9850),
                        "guardStyle": "white-timber",
                    },
                    {
                        "id": "g-bath",
                        "name": "Ground Family Bathroom",
                        "kind": "bathroom",
                        "polygon": rect(150, 10000, 2350, 12000),
                        "drain": True,
                    },
                    {
                        "id": "g-bedroom",
                        "name": "Ground Family Bedroom",
                        "kind": "bedroom",
                        "polygon": rect(2500, 7300, 5200, 12000),
                        "wardrobeWall": "left",
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "g-caregiver",
                        "name": "Caregiver Bedroom",
                        "kind": "bedroom",
                        "polygon": rect(5350, 7300, 8550, 9800),
                        "bedType": "single",
                        "wardrobeWall": "left",
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "g-caregiver-bath",
                        "name": "Caregiver Attached Toilet",
                        "kind": "bathroom",
                        "polygon": rect(6500, 9950, 8550, 11350),
                        "drain": True,
                    },
                ],
                "walls": [],
                "openings": [
                    op("o-entry", "g-living", "front", 600, 1200, "entry", 2350, 0, hinge="end", swingRoomId="g-living"),
                    op("o-kitch-serv", "g-kitchen", "right", 100, 2400, "cased", 2100, 0, servingCounter=True),
                    op("o-kitch-win-e", "g-kitchen", "front", 400, 1400, "window", 1250, 1000),
                    op("o-kitch-win-s", "g-kitchen", "left", 650, 1300, "window", 1250, 1000),
                    op("o-util-door", "g-utility", "right", 400, 800, "door", 2100, 0, hinge="start", swingRoomId="g-utility"),
                    op("o-util-win", "g-utility", "left", 400, 650, "window", 900, 1200),
                    op("o-puja", "g-puja", "right", 75, 750, "cased", 2100, 0),
                    op("o-stair-in", "g-stair", "right", 120, 1150, "cased", 2200, 0),
                    op("o-stair-win", "g-stair", "left", 1350, 1400, "window", 1500, 900),
                    op("o-living-ver", "g-living", "right", 5850, 1000, "glazed", 2250, 0, sliding=True),
                    op("o-care-in", "g-care", "left", 3550, 950, "door", 2150, 0, hinge="end", swingRoomId="g-care"),
                    op("o-care-ver-door", "g-care", "rear", 2500, 950, "glazed", 2250, 0, sliding=True, slidingPanels=2, stackingSliding=True),
                    op("o-care-n1", "g-care", "right", 300, 1650, "window", 1950, 450),
                    op("o-care-n2", "g-care", "right", 2100, 1550, "window", 1950, 450),
                    op("o-care-e", "g-care", "front", 850, 1800, "window", 1950, 450),
                    op("o-bed-in", "g-bedroom", "front", 850, 950, "door", 2100, 0, hinge="start", swingRoomId="g-bedroom"),
                    op("o-bed-win", "g-bedroom", "rear", 600, 1500, "window", 1300, 850),
                    op("o-bath-in", "g-bath", "right", 600, 750, "door", 2100, 0, hinge="start", swingRoomId="g-bath"),
                    op("o-bath-vent", "g-bath", "left", 650, 700, "window", 600, 1650),
                    op("o-cg-in", "g-caregiver", "front", 1450, 900, "door", 2100, 0, hinge="end", swingRoomId="g-veranda"),
                    op("o-cg-win-w", "g-caregiver", "rear", 200, 750, "window", 1300, 850),
                    op("o-cg-bath-in", "g-caregiver-bath", "front", 650, 750, "door", 2100, 0, hinge="start", swingRoomId="g-caregiver-bath"),
                    op("o-cg-bath-vent", "g-caregiver-bath", "right", 400, 600, "window", 600, 1650),
                ],
            },
            {
                "id": "floor-1",
                "rooms": [
                    {
                        "id": "u-balcony-east",
                        "name": "East Front Balcony",
                        "kind": "balcony",
                        "polygon": rect(0, 0, 8700, 1350),
                        "finishStyle": "honed-sandstone",
                        "guardStyle": "white-timber",
                        "clearAccess": True,
                    },
                    {
                        "id": "u-terrace-north",
                        "name": "North L-Shaped Terrace",
                        "kind": "terrace",
                        "polygon": [
                            [8700, 0],
                            [9900, 0],
                            [9900, 9800],
                            [8700, 9800],
                            [8700, 7150],
                            [6500, 7150],
                            [6500, 5750],
                            [8700, 5750],
                        ],
                        "finishStyle": "honed-sandstone",
                        "guardStyle": "white-timber",
                        "clearAccess": True,
                    },
                    {
                        "id": "u-lobby",
                        "name": "Upper Gallery & Family Lounge",
                        "kind": "hall",
                        "polygon": [
                            [2500, 1500],
                            [4900, 1500],
                            [4900, 5750],
                            [6350, 5750],
                            [6350, 7150],
                            [2500, 7150],
                        ],
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "u-bed-north",
                        "name": "First-Floor North-East Principal Bedroom",
                        "kind": "bedroom",
                        "polygon": rect(5050, 1500, 8550, 5600),
                        "wardrobeWall": "left",
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "u-store",
                        "name": "Upper Linen & Utility Store",
                        "kind": "store",
                        "polygon": rect(150, 1500, 2350, 3800),
                    },
                    {
                        "id": "u-bath-north",
                        "name": "First-Floor Principal Bathroom",
                        "kind": "bathroom",
                        "polygon": rect(150, 3950, 2350, 5600),
                        "drain": True,
                    },
                    {
                        "id": "u-stair",
                        "name": "Staircase",
                        "kind": "stair",
                        "polygon": rect(150, 5750, 2350, 9850),
                        "guardStyle": "white-timber",
                    },
                    {
                        "id": "u-bath-south",
                        "name": "First-Floor En-Suite Bathroom",
                        "kind": "bathroom",
                        "polygon": rect(150, 10000, 2350, 12000),
                        "drain": True,
                    },
                    {
                        "id": "u-bed-south",
                        "name": "First-Floor South-West Bedroom",
                        "kind": "bedroom",
                        "polygon": rect(2500, 7300, 5200, 12000),
                        "wardrobeWall": "left",
                        "ceilingStyle": "plain-downlights",
                    },
                    {
                        "id": "u-office",
                        "name": "Compact Office / Studio",
                        "kind": "study",
                        "polygon": rect(5350, 7300, 8550, 9800),
                        "ceilingStyle": "plain-downlights",
                    },
                ],
                "walls": [],
                "openings": [
                    op("o-ustair-in", "u-stair", "right", 120, 1150, "cased", 2200, 0),
                    op("o-ustair-win", "u-stair", "left", 1350, 1400, "window", 1500, 900),
                    op("o-ulobby-east", "u-lobby", "front", 550, 1300, "glazed", 2250, 0, sliding=True),
                    op("o-ulobby-north", "u-lobby", "right", 4500, 1000, "glazed", 2250, 0, sliding=True),
                    op("o-ubedn-in", "u-bed-north", "left", 2950, 950, "door", 2100, 0, hinge="end", swingRoomId="u-bed-north"),
                    op("o-ubedn-east", "u-bed-north", "front", 950, 1600, "glazed", 2250, 0, sliding=True),
                    op("o-ubedn-n1", "u-bed-north", "right", 300, 1650, "window", 1600, 650),
                    op("o-ubedn-n2", "u-bed-north", "right", 2100, 1550, "window", 1600, 650),
                    op("o-ustore-in", "u-store", "right", 550, 800, "door", 2100, 0, hinge="start", swingRoomId="u-store"),
                    op("o-ubathn-in", "u-bath-north", "right", 450, 750, "door", 2100, 0, hinge="start", swingRoomId="u-bath-north"),
                    op("o-ubathn-vent", "u-bath-north", "left", 475, 700, "window", 600, 1650),
                    op("o-ubeds-in", "u-bed-south", "front", 850, 950, "door", 2100, 0, hinge="start", swingRoomId="u-bed-south"),
                    op("o-ubeds-win", "u-bed-south", "rear", 600, 1500, "window", 1300, 850),
                    op("o-ubaths-in", "u-bath-south", "right", 600, 750, "door", 2100, 0, hinge="start", swingRoomId="u-bath-south"),
                    op("o-ubaths-vent", "u-bath-south", "left", 650, 700, "window", 600, 1650),
                    op("o-uoffice-in", "u-office", "front", 100, 800, "door", 2100, 0, hinge="start", swingRoomId="u-office"),
                    op("o-uoffice-terr", "u-office", "front", 1450, 1200, "glazed", 2250, 0, sliding=True),
                    op("o-uoffice-n", "u-office", "right", 550, 1400, "window", 1500, 750),
                    op("o-uoffice-w", "u-office", "rear", 850, 1500, "window", 1500, 750),
                ],
            },
        ],
        "stairs": [
            {
                "id": "south-stair-core",
                "roomIds": ["g-stair", "u-stair"],
                "flightWidth": 1000,
                "well": 200,
                "landing": 1050,
                "tread": 250,
                "rotation": 0,
            }
        ],
    }

    boards = []
    for fl in plan["floors"]:
        beds = [r for r in fl["rooms"] if r["kind"] == "bedroom"]
        labels = {r["id"]: ("bedroom-" + str(beds.index(r) + 1) if r["kind"] == "bedroom" else r["kind"]) for r in fl["rooms"]}
        rows = []
        for row in range(4):
            line = []
            for col in range(4):
                cell = box(col * W_env / 4, row * D_env / 4, (col + 1) * W_env / 4, (row + 1) * D_env / 4)
                matches = sorted([(Polygon(r["polygon"]).intersection(cell).area, r["id"]) for r in fl["rooms"]], reverse=True)
                line.append(labels[matches[0][1]] if matches[0][0] else "")
            rows.append(line)
        boards.append(rows)

    notes = (
        "East-facing 40 × 50 ft (12.192 × 15.240 m · 2,000 sq ft) northeast corner plot bounded by a 12.0 m North road "
        "(opposite a colony garden, pergola, palms and a white/grey house with a dark blue-grey vertical facade, N-01) "
        "and a 9.0 m East road (opposite a tall pale metal mesh basketball-court enclosure and screening planting, E-01). "
        "Two light-coloured electrical feeder cabinets stand outside the Northwest corner in the North road paver verge (N-02), "
        "and a streetlight pole stands along the North frontage between the NE and NW corners (N-03). "
        "The ground-floor Residential Care Room (g-care, 3.50 × 5.45 m = 19.08 m²) is positioned in the North/Northeast zone "
        "strictly east of the plot's East–West midpoint (X_geo in [7.65, 13.40] m >= 7.620 m), enjoying direct northward "
        "sightlines across the 12 m road to the colony garden at reclined (1.15 m), seated (1.20 m) and standing (1.63 m) eye heights, "
        "plus an oblique eastward glimpse to the court enclosure. A shaded L-shaped North Veranda with slender teak-collared columns, "
        "warm Jodhpuri sandstone paving and a woven-cane seating corner connects the living hall, care room and Northwest Caregiver Suite "
        "(3.20 × 2.50 m single bedroom + 2.05 × 1.40 m attached toilet), while preserving a landscaped Northwest open garden pocket "
        "and West boundary separation. Upstairs houses two family bedrooms with bathrooms, a compact office/studio, an upper store, "
        "east and north sandstone terraces, and continuous stair access to the roof terrace."
    )

    return {
        "schema": "floorforge.project/0.4",
        "brief": {
            "title": "Tirumala",
            "width_mm": 12192,      # 40 ft East frontage & West boundary (North-South)
            "depth_mm": 15240,      # 50 ft North boundary & South boundary (East-West)
            "front_mm": 1840,       # Provisional East arrival setback
            "rear_mm": 1250,        # Provisional West rear setback
            "left_mm": 1050,        # Provisional South side setback
            "right_mm": 1242,       # Provisional North garden setback
            "storeys": 2,
            "floor_height_mm": 3200,
            "plinth_mm": 450,
            "road_bearing_deg": 90,  # Principal entrance faces East
            "bedrooms": 4,
            "attached_baths": 0,
            "parking": False,
            "pooja": True,
            "roof_access": True,
            "eldercare": True,
            "open_kitchen": True,
            "vastu": "moderate",
            "style": "warm",
            "exterior_theme": "modern_tropical",
            "interior_theme": "bright_natural",
            "change_policy": "exterior_refinement",
            "interior_layout_locked": True,
        },
        "customPlan": plan,
        "notes": notes,
        "editorState": {
            "mode": "custom",
            "guideFloors": boards + [[[''] * 4 for _ in range(4)]],
            "guideEdited": False,
            "customPlan": copy.deepcopy(plan),
            "useRoomBoard": False,
        },
    }


def _design_guide(spec: dict, site_context: dict, photo_manifest: dict, assumptions: dict) -> str:
    """Comprehensive DESIGN_GUIDE.md for Tirumala."""
    care = site_context["care_room_verification"]
    lines = [
        "# Tirumala — Design Guide, Coordinate System & Colony Context Register",
        "",
        f"> **Preliminary Design Disclaimer:** {spec['disclaimer']}",
        "",
        "## 1. Site Overview & Confirmed Orientation",
        "",
        "- **Project Name:** Tirumala (`id: tirumala`)",
        "- **Plot Classification:** Northeast (NE) corner plot with an **EAST-facing principal entrance** (`road_bearing_deg: 90`).",
        "- **Confirmed Boundaries:**",
        "  - **EAST frontage (Front):** `40 ft 0 in = 12.192 m (12,192 mm)`, running North–South, adjoining the **9.0 m East colony road** and the **basketball-court enclosure & planting** beyond (`E-01`, `N-04`).",
        "  - **WEST boundary (Rear):** `40 ft 0 in = 12.192 m (12,192 mm)`, running North–South.",
        "  - **NORTH boundary (Right):** `50 ft 0 in = 15.240 m (15,240 mm)`, running East–West, adjoining the **12.0 m North colony road**, the **opposite colony garden** (lawn, raised planting kerb, pergola/seating, decorative pots, palms, slim lights), and the **two-storey white/grey house with dark blue-grey vertical facade** beyond (`N-01`, `N-02`, `N-03`).",
        "  - **SOUTH boundary (Left):** `50 ft 0 in = 15.240 m (15,240 mm)`, running East–West.",
        "- **Total Plot Area:** `2,000 sq ft = 185.806 m²`.",
        "- **Confirmed Roadside Utilities:**",
        "  - **Two Electrical Feeder Cabinets:** Outside the plot near its **Northwest (NW) corner** in the North road paver verge (`N-02`): a smaller pale-cream cabinet (`0.78 × 0.48 × 1.22 m`) on the left/east and a taller louvred cabinet (`1.05 × 0.55 × 1.62 m`) on the right/west when viewed from the North road looking Southwest.",
        "  - **Streetlight Pole:** Along the North frontage between the Northeast and Northwest corners (`N-02`, `N-03`).",
        "",
        "## 2. Explicit Geographic Coordinate System & FloorForge Transformation",
        "",
        "All site geometry, room polygons, road corridors, utility cabinets, and reference cameras are anchored to a single geographic coordinate system:",
        "",
        "- **Origin `(0.000, 0.000, 0.000)`:** Southwest (SW) plot corner at Natural Ground Level (`NGL ±0.000 m`).",
        "- **`+X_geo` (Eastward):** `0.000 m` at West boundary $\\to$ `15.240 m` (`50 ft`) at East frontage.",
        "- **`+Y_geo` (Northward):** `0.000 m` at South boundary $\\to$ `12.192 m` (`40 ft`) at North boundary.",
        "- **`+Z_geo` (Upward):** `0.000 m` at NGL $\\to$ `+0.450 m` at Ground Floor Finished Floor Level (`FFL`).",
        "",
        "| Plot Corner | Geographic `(X_geo, Y_geo)` (m) | FloorForge Scene `(x_scene, y_scene)` (m) | FloorForge Plan `(x_mm, y_mm)` (mm) |",
        "| :--- | :--- | :--- | :--- |",
        "| **SW Corner** | `(0.000, 0.000)` | `(-1.050, 13.400)` | `(-1050, 13400)` |",
        "| **SE Corner** | `(15.240, 0.000)` | `(-1.050, -1.840)` | `(-1050, -1840)` |",
        "| **NW Corner** | `(0.000, 12.192)` | `(11.142, 13.400)` | `(11142, 13400)` |",
        "| **NE Corner** | `(15.240, 12.192)` | `(11.142, -1.840)` | `(11142, -1840)` |",
        "",
        "**Exact Affine Transformation (`road_bearing_deg = 90`):**",
        "- `x_scene = Y_geo - 1.050`  $\\iff$  `Y_geo = x_scene + 1.050`",
        "- `y_scene = 13.400 - X_geo` $\\iff$  `X_geo = 13.400 - y_scene`",
        "- `z_scene = Z_geo - 0.450`  $\\iff$  `Z_geo = z_scene + 0.450`",
        "- Compass bearing $\\beta_{\\text{geo}}$ (`0°=N, 90°=E, 180°=S, 270°=W`) $\\to$ Walker `yaw_rad = atan2(-cos(β), -sin(β))`.",
        "",
        "## 3. Care Room Relocation & Northwest Open Pocket Verification",
        "",
        f"- **Plot East–West Midpoint:** `X_geo = {care['plot_ew_midpoint_x_geo_m']:.3f} m` (`25 ft`, corresponding to `y_local = 5,780 mm` / `y_scene = {care['midpoint_scene_y_m']:.3f} m`).",
        f"- **Residential Care Room (`g-care`) Clear Span:** `X_geo` from **`{care['care_clear_x_geo_min_m']:.3f} m` to `{care['care_clear_x_geo_max_m']:.3f} m`** (`Y_geo` from `6.100 m` to `9.600 m`, `19.08 m²`).",
        f"- **Residential Care Room (`g-care`) Outer Wall Span:** `X_geo` from **`{care['care_outer_x_geo_min_m']:.3f} m` to `{care['care_outer_x_geo_max_m']:.3f} m`** — **100% east of the `7.620 m` plot midpoint (`strictly_east_of_midpoint = {care['strictly_east_of_midpoint']}`)**.",
        "- **Dual-Aspect Sightlines from Care Room:**",
        "  - **Northward (`N-01`):** Two large windows (`1.65 m × 1.95 m` and `1.55 m × 1.95 m`) with `450 mm` low sills (`o-care-n1`, `o-care-n2`) and a `1.15 m` glazed door (`o-care-ver-door`) look across the shaded North veranda (`FFL +0.45 m`), over the low `0.90 m` North road boundary wall (`+0.45 m` above FFL), across the 12 m road into the opposite colony garden, pergola, palms, and house (`N-01`) from reclined (`+1.15 m`), seated (`+1.20 m`), and standing (`+1.63 m`) eye heights.",
        "  - **Eastward (`E-01`):** A `1.80 m × 1.95 m` low-sill East window (`o-care-e`) provides an oblique outlook across the 9 m East road toward the tall pale metal mesh basketball-court enclosure and screening palms/trees (`E-01`).",
        "- **Northwest Caregiver Suite & Open Garden Pocket:**",
        "  - The Caregiver Bedroom (`g-caregiver`, `8.00 m²`) and Attached Toilet (`g-caregiver-bath`, `2.87 m²`) sit in the West/Northwest zone (`X_geo in [2.05, 6.10] m`), directly connected to `g-care` via the sheltered L-shaped North Veranda (`g-veranda`).",
        "  - The Northwest corner of the plot (`x_local in [8700, 11142], y_local in [9800, 13400]` and `x_local in [5350, 8700], y_local in [11500, 13400]`) is preserved as a landscaped open garden pocket with lawn, stepping-stone service path, terracotta planters, and `1.90 m–3.60 m` separation from the West boundary.",
        "",
        "## 4. Six Reference Photographs & Camera Presets",
        "",
        "| ID | Original Suffix | Bearing | Confidence | Key Reproduced Features |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for p in photo_manifest["photos"]:
        feats = "; ".join(p["observed_features"][:2])
        lines.append(f"| **`{p['id']}`** | `{p['original_number_suffix']}` | `{p['bearing_deg']}°` | `{p['confidence']}` | {feats} |")
    lines.extend([
        "",
        "## 5. Room-by-Room Schedule",
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
        "## 6. Assumptions & Unknowns Requiring Survey Verification",
        "",
    ])
    for u in assumptions["unknowns_requiring_site_measurement"]:
        lines.append(f"- {u}")
    lines.extend(["", f"Plan hash: `{spec['planHash']}`", ""])
    return "\n".join(lines)


def write_tirumala(out_dir: Path = OUT_DIR) -> dict:
    """Compile Tirumala and write all FloorForge sample deliverables plus Tirumala context manifests."""
    p = tirumala_project()
    b = generate_layout(fuse(p))
    review = validate(b)
    if review.get("errors") or review.get("warnings"):
        raise RuntimeError(f"Tirumala validation issues: {json.dumps(review, indent=2)}")

    # Strict geometric check: care room must stay at or east of plot midpoint X_geo >= 7.620 m
    care = next(s for s in b["spaces"] if s["id"] == "g-care")
    for pt in care["polygon"] + care["clear"]:
        x_geo, _ = local_mm_to_geo_m(pt[0], pt[1])
        if x_geo < PLOT_EW_MIDPOINT_M - 1e-6:
            raise RuntimeError(f"Care room point {pt} has X_geo={x_geo}m < midpoint {PLOT_EW_MIDPOINT_M}m")

    out_dir.mkdir(parents=True, exist_ok=True)
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)
    (BRIEFS_DIR / f"{TIRUMALA_ID}.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="ff-tirumala-") as tmp:
        result = run(p, Path(tmp), use_cache=False)
        shutil.copytree(result["path"], out_dir, dirs_exist_ok=True)

    b = json.loads((out_dir / "building.json").read_text(encoding="utf-8"))
    scene = json.loads((out_dir / "scene.json").read_text(encoding="utf-8"))
    site_context = build_tirumala_context(b, scene)
    photo_manifest = build_photo_reference_manifest()
    assumptions = build_assumptions_register()

    spec = {
        "id": TIRUMALA_ID,
        "title": "Tirumala",
        "planHash": b["planHash"],
        "disclaimer": b["banner"],
        "orientation": "East road/front (40 ft = 12.192 m) · South left · North 12 m road/right (50 ft = 15.240 m) · West rear",
        "notes": p["notes"],
        "plotFt": [40, 50],
        "plotM": [12.192, 15.240],
        "plotAreaSqFt": 2000,
        "plotAreaM2": 185.806,
        "setbacksMm": {
            "east_front_mm": p["brief"]["front_mm"],
            "west_rear_mm": p["brief"]["rear_mm"],
            "south_left_mm": p["brief"]["left_mm"],
            "north_right_mm": p["brief"]["right_mm"],
            "status": "provisional_reversible_assumptions",
        },
        "buildableEnvelopeMm": [9900, 12150],
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

    guide_md = _design_guide(spec, site_context, photo_manifest, assumptions)
    (out_dir / "DESIGN_GUIDE.md").write_text(guide_md, encoding="utf-8")

    # Copy reference photographs into examples/gallery/tirumala/reference-assets/
    ref_src_dir = EVIDENCE_DIR / "reference-assets"
    ref_dst_dir = out_dir / "reference-assets"
    if ref_src_dir.exists():
        ref_dst_dir.mkdir(parents=True, exist_ok=True)
        for img in sorted(ref_src_dir.glob("*.png")):
            shutil.copy2(img, ref_dst_dir / img.name)

    # Update manifest.json and FloorForge-export.zip so all new Tirumala files are bundled
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    for name in ("specifications.json", "DESIGN_GUIDE.md", "site-context.json", "photo-reference-manifest.json", "assumptions-register.json"):
        manifest["files"][name] = hashlib.sha256((out_dir / name).read_bytes()).hexdigest()
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    files = {name: (out_dir / name).read_bytes() for name in manifest["files"]}
    files["manifest.json"] = (out_dir / "manifest.json").read_bytes()
    (out_dir / "FloorForge-export.zip").write_bytes(deterministic_zip(files))

    # Mirror registers into evidence/tirumala/
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    for fname in ("site-context.json", "photo-reference-manifest.json", "assumptions-register.json", "DESIGN_GUIDE.md", "specifications.json"):
        shutil.copy2(out_dir / fname, EVIDENCE_DIR / fname)

    update_catalog_entry(b)
    return {"building": b, "review": review, "scene": scene, "specifications": spec}


def update_catalog_entry(b: dict) -> None:
    """Append or update ONLY the 'tirumala' entry in examples/gallery/catalog.json without
    renaming, removing, reordering, or altering any existing entry."""
    items = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    entry = {
        "id": TIRUMALA_ID,
        "title": "Tirumala",
        "description": (
            "East-facing 40 × 50 ft (2,000 sq ft) northeast corner home bounded by a 12 m North road "
            "(opposite a colony garden and white/blue-grey house) and a 9 m East road (opposite a basketball-court enclosure): "
            "Northeast care room east of the plot midpoint, shaded L-shaped North veranda with cane seating, "
            "Northwest caregiver suite with open garden pocket, sociable kitchen, puja alcove, three bedrooms, study and roof terrace."
        ),
        "style": "White/Ivory & Colony Veranda",
        "directory": f"gallery/{TIRUMALA_ID}",
        "bedrooms": b["brief"]["bedrooms"],
        "storeys": 2,
        "widthFt": 40,
        "depthFt": 50,
        "roofAccess": True,
        "planHash": b["planHash"],
        "hasSpecifications": True,
    }
    existing_idx = next((i for i, s in enumerate(items) if s.get("id") == TIRUMALA_ID), None)
    if existing_idx is None:
        items.append(entry)
    else:
        items[existing_idx] = entry
    CATALOG_PATH.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")


project = tirumala_project


def check_tirumala() -> int:
    p = tirumala_project()
    b = generate_layout(fuse(p))
    review = validate(b)
    if review.get("errors") or review.get("warnings"):
        print(f"Validation failed: {review}", file=sys.stderr)
        return 1
    on_disk = json.loads((OUT_DIR / "building.json").read_text(encoding="utf-8"))
    if on_disk.get("planHash") != b.get("planHash"):
        print("planHash mismatch on disk", file=sys.stderr)
        return 1
    print(f"Tirumala check passed: planHash={b['planHash']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify Tirumala compiles and matches on-disk planHash.")
    args = parser.parse_args()

    if args.check:
        return check_tirumala()

    result = write_tirumala()
    print(json.dumps({
        "path": str(OUT_DIR),
        "planHash": result["building"]["planHash"],
        "spaces": len(result["building"]["spaces"]),
        "review": result["review"].get("status"),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
