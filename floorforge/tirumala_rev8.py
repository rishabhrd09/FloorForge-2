"""Authoritative Tirumala Revision 9 specification and compiler for Options A–E.

All coordinates originate from the Southeast (SE) plot corner (0, 0) in feet
and convert using 1 ft = 304.8 mm:
- x increases South-to-North: 0..40 ft (0..12,192 mm)
- y increases East-to-West: 0..50 ft (0..15,240 mm)
- East (9 m road) is at y = 0 (bottom of displayed 2D plan)
- North (12 m road) is at x = 40 ft (right of displayed 2D plan)

Shared wall centerlines sit at round(w_ft * 304.8) mm with 150 mm thickness
(±75 mm clear faces), so 2D drawings and 3D meshes share one exact model.
"""
from __future__ import annotations

from typing import Any
from .model import sha

FT_MM = 304.8
WALL_MM = 150
HALF_MM = WALL_MM // 2
PLOT_W_FT = 40.0
PLOT_D_FT = 50.0
PLOT_W_MM = 12192
PLOT_D_MM = 15240
FLOOR_H_MM = 3658   # 12.0 ft floor-to-floor
PLINTH_MM = 300     # +300 mm house/court/porch/veranda datum above ±0 mm road/car bay
REVISION = 9

OPTIONS: dict[str, dict[str, Any]] = {
    "A": {
        "code": "A",
        "label": "A — Original flow",
        "tag": "Balanced care room and a 5½′ rear veranda",
        "trade": "Closest overall flow; 5½′ veranda between care and the compact caregiver room.",
        "summary": "192 sq ft care suite, 11 × 10 ft drawing room, 51 sq ft caregiver room, and 5.5 ft deep main rear veranda.",
        "careSqFt": 192.0,
        "drawingFt": [11.0, 10.0],
        "caregiverSqFt": 51.0,
        "verandaDepthFt": 5.5,
        "drawEnd": 21.0,
        "careStart": 21.5,
        "careEnd": 34.5,
        "careNorth": 36.0,
        "courtStart": 35.0,
        "courtEnd": 40.5,
        "glassClear": 9.0,
        "careFront": 20.5,
        "cgRectFt": [16.0, 41.0, 8.5, 6.0],
        "wcRectFt": [25.0, 41.0, 5.0, 6.0],
        "gardenRectFt": [30.5, 41.0, 9.0, 6.0],
        "returnRectFt": None,
        "sceneSeed": "81a80a94c513426f90451a8d2e1b7c349012f8a4b6c7d8e9f0a1b2c3d4e5f601",
    },
    "B": {
        "code": "B",
        "label": "B — Larger care suite",
        "tag": "Largest care suite · 3½′ rear veranda",
        "trade": "Largest revised care suite (224.5 sq ft). The 3½′ rear veranda is a circulation strip; seating sits in the wider northwest pocket.",
        "summary": "224.5 sq ft extended care suite, 11 × 10 ft drawing room, 51 sq ft caregiver room, and 3.5 ft rear veranda.",
        "careSqFt": 224.5,
        "drawingFt": [11.0, 10.0],
        "caregiverSqFt": 51.0,
        "verandaDepthFt": 3.5,
        "drawEnd": 21.0,
        "careStart": 21.5,
        "careEnd": 36.5,
        "careNorth": 36.0,
        "courtStart": 37.0,
        "courtEnd": 40.5,
        "glassClear": 9.0,
        "careFront": 20.5,
        "cgRectFt": [16.0, 41.0, 8.5, 6.0],
        "wcRectFt": [25.0, 41.0, 5.0, 6.0],
        "gardenRectFt": [30.5, 41.0, 9.0, 6.0],
        "returnRectFt": None,
        "sceneSeed": "82b80a94c513426f90451a8d2e1b7c349012f8a4b6c7d8e9f0a1b2c3d4e5f602",
    },
    "C": {
        "code": "C",
        "label": "C — Garden first",
        "tag": "6½′ rear veranda · slim north passage",
        "trade": "Deepest main veranda bay: 6½′, with a 4½′ left return. The side passage is the same slim 3′ width as every option.",
        "summary": "179.5 sq ft care suite, 11 × 10 ft drawing room, 51 sq ft caregiver room, and 6.5 ft deep main rear veranda.",
        "careSqFt": 179.5,
        "drawingFt": [11.0, 10.0],
        "caregiverSqFt": 51.0,
        "verandaDepthFt": 6.5,
        "drawEnd": 21.0,
        "careStart": 21.5,
        "careEnd": 33.5,
        "careNorth": 36.0,
        "courtStart": 34.0,
        "courtEnd": 40.5,
        "glassClear": 9.0,
        "careFront": 20.5,
        "cgRectFt": [16.0, 41.0, 8.5, 6.0],
        "wcRectFt": [25.0, 41.0, 5.0, 6.0],
        "gardenRectFt": [30.5, 41.0, 9.0, 6.0],
        "returnRectFt": None,
        "sceneSeed": "83c80a94c513426f90451a8d2e1b7c349012f8a4b6c7d8e9f0a1b2c3d4e5f603",
    },
    "D": {
        "code": "D",
        "label": "D — Larger drawing room",
        "tag": "Rectangular drawing room · 11′ × 12′",
        "trade": "Drawing is a plain 11′ × 12′ rectangle. A, B, C and E use a shorter 11′ × 10′ rectangle. All share the same shallow front porch.",
        "summary": "179.5 sq ft care suite, 11 × 12 ft drawing room, 51 sq ft caregiver room, and 4.5 ft deep main rear veranda.",
        "careSqFt": 179.5,
        "drawingFt": [11.0, 12.0],
        "caregiverSqFt": 51.0,
        "verandaDepthFt": 4.5,
        "drawEnd": 23.0,
        "careStart": 23.5,
        "careEnd": 35.5,
        "careNorth": 36.0,
        "courtStart": 36.0,
        "courtEnd": 40.5,
        "glassClear": 7.0,
        "careFront": 22.5,
        "cgRectFt": [16.0, 41.0, 8.5, 6.0],
        "wcRectFt": [25.0, 41.0, 5.0, 6.0],
        "gardenRectFt": [30.5, 41.0, 9.0, 6.0],
        "returnRectFt": None,
        "sceneSeed": "84d80a94c513426f90451a8d2e1b7c349012f8a4b6c7d8e9f0a1b2c3d4e5f604",
    },
    "E": {
        "code": "E",
        "label": "E — Caregiver courtyard",
        "tag": "5′ shared veranda court · caregiver opposite care",
        "trade": "Care and caregiver face a shared 5′ veranda court. A west-side return connects the hall to the rear strip.",
        "summary": "192 sq ft care suite, 11 × 10 ft drawing room, 52 sq ft caregiver room, and 5 ft shared veranda court with 3.5 ft west return.",
        "careSqFt": 192.0,
        "drawingFt": [11.0, 10.0],
        "caregiverSqFt": 52.0,
        "verandaDepthFt": 5.0,
        "drawEnd": 21.0,
        "careStart": 21.5,
        "careEnd": 34.5,
        "careNorth": 36.0,
        "courtStart": 35.0,
        "courtEnd": 40.0,
        "glassClear": 9.0,
        "careFront": 20.5,
        "cgRectFt": [25.5, 40.5, 8.0, 6.5],
        "wcRectFt": [20.0, 40.5, 5.0, 6.5],
        "gardenRectFt": [34.0, 40.5, 5.5, 6.5],
        "returnRectFt": [16.0, 40.5, 3.5, 6.5],
        "sceneSeed": "85e80a94c513426f90451a8d2e1b7c349012f8a4b6c7d8e9f0a1b2c3d4e5f605",
    },
}


def ft(val: float) -> int:
    return round(val * FT_MM)


def fp(w_ft: float) -> int:
    """Clear room face on the positive (+x or +y) side of wall centerline w_ft."""
    return round(w_ft * FT_MM) + HALF_MM


def fn(w_ft: float) -> int:
    """Clear room face on the negative (-x or -y) side of wall centerline w_ft."""
    return round(w_ft * FT_MM) - HALF_MM


def rect_poly(x0: int, y0: int, x1: int, y1: int) -> list[list[int]]:
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _rect_ft(x: float, y: float, w: float, h: float) -> list[list[float]]:
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def canonical_handoff_zones(option_code: str = "A") -> dict[str, Any]:
    """Return the revision-9 concept zones, evolved from the saved revision-8 handoff."""
    o = OPTIONS[option_code]
    draw_end = o["drawEnd"]
    care_start = o["careStart"]
    care_end = o["careEnd"]
    care_north = o["careNorth"]
    care_front = o["careFront"]
    court_start = o["courtStart"]
    court_end = o["courtEnd"]
    tail_end = max(35.5, care_end)
    left_start = max(36.0, court_start)
    end_north = 40.5 if option_code == "E" else 41.0

    care_ft = [
        [23.5, care_start],
        [29.0, care_start],
        [29.0, care_front],
        [care_north, care_front],
        [care_north, care_end],
        [23.5, care_end],
        [23.5, tail_end],
        [16.0, tail_end],
        [16.0, 32.5],
        [23.5, 32.5],
    ]
    veranda_ft = [
        [16.0, left_start],
        [24.0, left_start],
        [24.0, court_start],
        [care_north, court_start],
        [care_north, court_end],
        [16.0, court_end],
    ]
    family_ft = [
        [4.5, 7.5],
        [17.0, 7.5],
        [17.0, draw_end + 0.5],
        [23.0, draw_end + 0.5],
        [23.0, 32.0],
        [0.5, 32.0],
        [0.5, 25.5],
        [12.5, 25.5],
        [12.5, 18.0],
        [4.5, 18.0],
    ]
    master_ft = [
        [0.5, 32.5],
        [15.5, 32.5],
        [15.5, 39.5],
        [10.0, 39.5],
        [10.0, 47.0],
        [0.5, 47.0],
    ]

    ground_ft = {
        "parking": _rect_ft(29.0, 0.5, 10.5, 19.0),
        "entry": _rect_ft(17.5, 7.5, 11.0, 3.0),
        "entrySteps": _rect_ft(18.5, 0.5, 10.0, 1.0),
        "frontCourt": [[0.5, 0.5], [18.5, 0.5], [18.5, 1.5], [28.5, 1.5], [28.5, 7.0], [0.5, 7.0]],
        "drawing": _rect_ft(17.5, 11.0, 11.0, draw_end - 11.0),
        "kitchen": [[4.5,7.5],[9,7.5],[9,11],[14.5,11],[14.5,17.5],[4.5,17.5]],
        "puja": _rect_ft(9.5, 7.5, 4.0, 3.0),
        "south": _rect_ft(0.5, 7.5, 3.5, 10.0),
        "stair": _rect_ft(0.5, 18.0, 12.0, 7.5),
        "groundStairArrival": _rect_ft(12.5, 18.0, 3.5, 3.5),
        "family": family_ft,
        "master": master_ft,
        "bath": _rect_ft(10.5, 40.0, 5.0, 7.0),
        "care": care_ft,
        "caregiver": _rect_ft(*o["cgRectFt"]),
        "wc": _rect_ft(*o["wcRectFt"]),
        "veranda": veranda_ft,
        "return": _rect_ft(*o["returnRectFt"]) if o["returnRectFt"] else None,
        "north": _rect_ft(36.5, care_front, 3.0, end_north - care_front),
        "garden": _rect_ft(*o["gardenRectFt"]),
        "rear": _rect_ft(0.5, 47.5, 39.0, 2.0),
    }
    first_ft = {
        "upperStairArrival": _rect_ft(12.5, 22.0, 3.5, 3.5),
        "livingVoid": [
            [16.25, draw_end + 1.0],
            [23.0, draw_end + 1.0],
            [23.0, 31.75],
            [9.5, 31.75],
            [9.5, 25.75],
            [16.25, 25.75],
        ],
        "uBath": _rect_ft(0.5, 7.5, 5.0, 10.0),
        "uMaster": [[0.5,26],[9,26],[9,32.25],[12.5,32.25],[12.5,39.5],[0.5,39.5]],
        "uStudy": _rect_ft(16.0, 11.0, 12.5, draw_end - 13.5),
        "rooflight": _rect_ft(18.5, draw_end + 2.0, 4.0, min(8.0, 29.0 - draw_end)),
    }
    furniture_ft = {
        "car": [31.0, 2.25, 6.5, 15.5],
        "diningTable": [4.75, 26.5, 3.0, 5.0],
        "careBed": [26.25, care_start + 3.95, 7.0, 3.5],
        "careBedside": [24.0, care_start + 8.2, 1.3, 1.8],
        "careVisitorChair": [34.0, care_end - 3.0, 1.5, 1.8],
        "pujaMandir": [9.8, 7.65, 3.4, 0.9],
    }

    def poly_mm(pts: list[list[float]]) -> list[list[int]]:
        return [[ft(p[0]), ft(p[1])] for p in pts]

    def box_mm(b_ft: list[float]) -> list[list[int]]:
        x, y, w, d = b_ft
        return rect_poly(ft(x), ft(y), ft(x + w), ft(y + d))

    canonical_zones_mm = {
        **{k: poly_mm(v) for k, v in ground_ft.items() if v is not None},
        **{k: poly_mm(v) for k, v in first_ft.items()},
        "car": box_mm(furniture_ft["car"]),
        "dining": box_mm(furniture_ft["diningTable"]),
        "bed": box_mm(furniture_ft["careBed"]),
    }
    geom_hash = sha({
        "revision": REVISION,
        "option": option_code,
        "ground_ft": {k: v for k, v in ground_ft.items() if v is not None},
        "first_ft": first_ft,
        "furniture_ft": furniture_ft,
    })
    def _norm_nums(val: Any) -> Any:
        if isinstance(val, float) and val.is_integer():
            return int(val)
        if isinstance(val, dict):
            return {k: _norm_nums(v) for k, v in val.items()}
        if isinstance(val, list):
            return [_norm_nums(v) for v in val]
        return val

    return _norm_nums({
        "option": option_code,
        "label": o["label"],
        "tag": o["tag"],
        "trade": o["trade"],
        "summary": o["summary"],
        "revision": REVISION,
        "careEndFt": max(care_end, tail_end),
        "geometryHash": geom_hash,
        "parameters": {
            "drawEnd": draw_end,
            "careStart": care_start,
            "careEnd": care_end,
            "careNorth": care_north,
            "careFront": care_front,
            "courtStart": court_start,
            "courtEnd": court_end,
            "glassClear": o["glassClear"],
            "verandaEnd": court_end,
        },
        "ground_ft": {k: v for k, v in ground_ft.items() if v is not None},
        "first_ft": first_ft,
        "furniture_ft": furniture_ft,
        "canonicalZones": canonical_zones_mm,
    })


def build_option_project(option_code: str = "A") -> dict[str, Any]:
    """Build the complete FloorForge project payload for Tirumala Revision 9 Option A–E."""
    if option_code not in OPTIONS:
        raise ValueError(f"Unsupported Tirumala option: {option_code}")
    o = OPTIONS[option_code]
    draw_end = o["drawEnd"]         # 21.0 (A/B/C/E) or 23.0 (D)
    care_start = o["careStart"]     # 21.5 (A/B/C/E) or 23.5 (D)
    care_end = o["careEnd"]         # 34.5 (A/E), 36.5 (B), 33.5 (C), 35.5 (D)
    care_front = o["careFront"]     # 20.5 (A/B/C/E) or 22.5 (D)
    court_start = o["courtStart"]   # 35.0 (A/E), 37.0 (B), 34.0 (C), 36.0 (D)
    court_end = o["courtEnd"]       # 40.5 (A/B/C/D) or 40.0 (E)
    tail_end = max(35.5, care_end)  # 35.5 (A/C/D/E) or 36.5 (B)

    # Exact stair core: 12.0 ft (3658 mm) S–N x 7.5 ft (2286 mm) E–W
    st_x0, st_y0 = fp(0.25), fp(17.75)           # 151, 5485
    st_x1, st_y1 = st_x0 + 3658, st_y0 + 2286    # 3809, 7771

    # Ground-floor rooms
    g_porch = {
        "id": "g-porch",
        "kind": "veranda",
        "name": "Shallow entry porch",
        "clearAccess": True,
        "openToSky": True,
        "finishStyle": "warm-stone",
        "polygon": rect_poly(fp(17.25), fp(7.25), fn(28.75), fn(10.75)),
    }
    g_drawing = {
        "id": "g-drawing",
        "kind": "drawing-room",
        "name": "Drawing room · guests",
        "ceilingStyle": "plain-downlights",
        "polygon": rect_poly(fp(17.25), fp(10.75), fn(28.75), fn(draw_end + 0.25)),
    }
    g_kitchen = {
        "id": "g-kitchen",
        "kind": "kitchen",
        "name": "Open kitchen · southeast",
        "ceilingStyle": "plain-downlights",
        "kitchenLayout": "open-south-return",
        "polygon": [[fp(4.25), fp(7.25)], [fn(9.25), fp(7.25)], [fn(9.25), fp(10.75)], [fn(14.75), fp(10.75)], [fn(14.75), fn(17.75)], [fp(4.25), fn(17.75)]],
    }
    g_puja = {
        "id": "g-puja",
        "kind": "pooja",
        "name": "Screened puja niche",
        "altarWall": "front",
        "polygon": rect_poly(fp(9.25), fp(7.25), fn(13.75), fn(10.75)),
    }
    g_south_lane = {
        "id": "g-south-lane",
        "kind": "veranda",
        "name": "South daylight lane",
        "clearAccess": True,
        "serviceOnly": True,
        "finishStyle": "warm-stone",
        "polygon": rect_poly(st_x0 - WALL_MM, fn(7.25), fn(4.25), fn(17.75)),
    }
    g_stair = {
        "id": "g-stair",
        "kind": "stair",
        "name": "Compact corner stair",
        "guardStyle": "white-timber",
        "polygon": rect_poly(st_x0, st_y0, st_x1, st_y1),
    }
    # Continuous family space including the released hall zone behind the compact stair (x = 0.5..12.5, y = 25.5..32)
    g_family = {
        "id": "g-family",
        "kind": "family",
        "name": "Living · dining · stair hall",
        "ceilingStyle": "plain-downlights",
        "diningPosition": [ft(6.25), ft(29.0)],
        "diningOrientation": 90,
        "diningLength": 1524,
        "diningCounterGap": 600,
        "polygon": [
            [fp(13.75), fp(7.25)],
            [fn(17.25), fp(7.25)],
            [fn(17.25), fp(draw_end + 0.25)],
            [fn(23.25), fp(draw_end + 0.25)],
            [fn(23.25), fn(32.25)],
            [st_x0, fn(32.25)],
            [st_x0, st_y1 + WALL_MM],
            [st_x1 + WALL_MM, st_y1 + WALL_MM],
            [st_x1 + WALL_MM, fp(17.75)],
            [fp(14.75), fp(17.75)],
            [fp(14.75), fn(10.75)],
            [fp(13.75), fn(10.75)],
        ],
    }
    # Southwest L-shaped master bedroom (176 sq ft) and attached 5 x 7 ft bath
    g_master = {
        "id": "g-master",
        "kind": "bedroom",
        "name": "Master bedroom · southwest",
        "wardrobeWall": "rear",
        "polygon": [
            [st_x0, fp(32.25)],
            [fn(15.75), fp(32.25)],
            [fn(15.75), fn(39.75)],
            [fn(10.25), fn(39.75)],
            [fn(10.25), fn(47.25)],
            [st_x0, fn(47.25)],
        ],
    }
    g_bath = {
        "id": "g-bath",
        "kind": "bathroom",
        "name": "Master attached bath",
        "polygon": rect_poly(fp(10.25), fp(39.75), fn(15.75), fn(47.25)),
    }

    # Home care suite: includes 1 ft East step-out at x = 29..36 (y = careFront..careStart)
    # and the L-return behind the family hall at x = 16..23.5 (y = 32.5..tailEnd)
    if abs(care_end - tail_end) < 1e-4:
        # Options B (careEnd = 36.5 = tailEnd) and D (careEnd = 35.5 = tailEnd)
        g_care_poly = [
            [fp(23.25), fp(draw_end + 0.25)],
            [fp(28.75), fp(draw_end + 0.25)],
            [fp(28.75), fp(care_front - 0.25)],
            [fn(36.25), fp(care_front - 0.25)],
            [fn(36.25), fn(care_end + 0.25)],
            [fp(15.75), fn(care_end + 0.25)],
            [fp(15.75), fp(32.25)],
            [fp(23.25), fp(32.25)],
        ]
    else:
        # Options A, C, E (careEnd < 35.5 = tailEnd)
        g_care_poly = [
            [fp(23.25), fp(draw_end + 0.25)],
            [fp(28.75), fp(draw_end + 0.25)],
            [fp(28.75), fp(care_front - 0.25)],
            [fn(36.25), fp(care_front - 0.25)],
            [fn(36.25), fn(care_end + 0.25)],
            [fp(23.25), fn(care_end + 0.25)],
            [fp(23.25), fn(tail_end + 0.25)],
            [fp(15.75), fn(tail_end + 0.25)],
            [fp(15.75), fp(32.25)],
            [fp(23.25), fp(32.25)],
        ]

    g_care = {
        "id": "g-care",
        "kind": "care-room",
        "name": "Home care suite · north",
        "careLayout": "equipment-left",
        "reclinerPosition": [ft(29.75), ft(care_start + 5.70)],
        "polygon": g_care_poly,
    }

    if option_code == "E":
        # Option E: Shared veranda court (y = 35..40) + West return (x = 16..19.5, y = 40..47),
        # with WC at x = 20..25, y = 40.5..47 and Caregiver at x = 25.5..33.5, y = 40.5..47
        g_veranda_poly = [
            [fp(15.75), fp(tail_end + 0.25)],
            [fp(23.25) + WALL_MM, fp(tail_end + 0.25)],
            [fp(23.25) + WALL_MM, fp(care_end + 0.25)],
            [fn(36.25), fp(care_end + 0.25)],
            [fn(36.25), fn(40.25)],
            [fn(19.75), fn(40.25)],
            [fn(19.75), fn(47.25)],
            [fp(15.75), fn(47.25)],
        ]
        g_wc = {
            "id": "g-wc",
            "kind": "bathroom",
            "name": "Caregiver WC",
            "polygon": rect_poly(fp(19.75), fp(40.25), fn(25.25), fn(47.25)),
        }
        g_caregiver = {
            "id": "g-caregiver",
            "kind": "bedroom",
            "name": "Caregiver room",
            "bedType": "single",
            "polygon": rect_poly(fp(25.25), fp(40.25), fn(33.75), fn(47.25)),
        }
    else:
        # Options A–D: Open rear veranda between care and caregiver/WC,
        # with Caregiver at x = 16..24.5, y = 41..47 and WC at x = 25..30, y = 41..47
        if abs(care_end - tail_end) < 1e-4:
            g_veranda_poly = rect_poly(fp(15.75), fp(care_end + 0.25), fn(36.25), fn(40.75))
        else:
            g_veranda_poly = [
                [fp(15.75), fp(tail_end + 0.25)],
                [fp(23.25) + WALL_MM, fp(tail_end + 0.25)],
                [fp(23.25) + WALL_MM, fp(care_end + 0.25)],
                [fn(36.25), fp(care_end + 0.25)],
                [fn(36.25), fn(40.75)],
                [fp(15.75), fn(40.75)],
            ]
        g_caregiver = {
            "id": "g-caregiver",
            "kind": "bedroom",
            "name": "Caregiver room",
            "bedType": "single",
            "polygon": rect_poly(fp(15.75), fp(40.75), fn(24.75), fn(47.25)),
        }
        g_wc = {
            "id": "g-wc",
            "kind": "bathroom",
            "name": "Caregiver WC",
            "polygon": rect_poly(fp(24.75), fp(40.75), fn(30.25), fn(47.25)),
        }

    g_veranda = {
        "id": "g-veranda",
        "kind": "veranda",
        "name": "Shared veranda courtyard" if option_code == "E" else "Open rear veranda",
        "clearAccess": True,
        "finishStyle": "warm-stone",
        "polygon": g_veranda_poly,
    }

    # Ground-floor openings
    WallH = FLOOR_H_MM - 150  # 3508 mm
    north_win_span = care_end - care_front - 1.0  # 13 ft (A/E), 15 ft (B), 12 ft (C/D)
    g_openings = [
        # Drawing room: front entry door (x=23 ft, y=10.75 ft, 3 ft), North window (5.5 ft on x=28.75), hall door
        {
            "id": "g-entry",
            "roomId": "g-drawing",
            "side": "front",
            "kind": "entry",
            "offset": ft(23.0 - 1.5) - fp(17.25),
            "width": ft(3.0),
            "height": 2400,
            "sill": 0,
            "hinge": "start",
        },
        {
            "id": "g-drawing-north-window",
            "roomId": "g-drawing",
            "side": "right",
            "kind": "window",
            "offset": ft(16.0 - 2.75) - fp(10.75),
            "width": ft(5.5),
            "height": 1800,
            "sill": 600,
            "hinge": "start",
        },
        {
            "id": "g-drawing-door",
            "roomId": "g-drawing",
            "side": "left",
            "kind": "glazed",
            "sliding": True,
            "slidingPanels": 3,
            "offset": ft(0.75),
            "width": ft(draw_end - 12.5),
            "height": 3000,
            "sill": 0,
            "hinge": "start",
        },
        # Shallow porch side sliding door into family hall (v at x=18.25, y=9.0, span 3 ft)
        {
            "id": "g-porch-family-slider",
            "roomId": "g-porch",
            "side": "left",
            "kind": "glazed",
            "sliding": True,
            "slidingPanels": 2,
            "offset": 80,
            "width": 750,
            "height": 2200,
            "sill": 0,
            "hinge": "start",
        },
        # Kitchen: East window (4.5 ft) and open North interface into family/dining
        {
            "id": "g-kitchen-east-window",
            "roomId": "g-kitchen",
            "side": "front",
            "kind": "window",
            "offset": 75,
            "width": ft(3.75),
            "height": 1350,
            "sill": 950,
            "hinge": "start",
        },
        {
            "id": "g-kitchen-open-north",
            "roomId": "g-kitchen",
            "side": "right",
            "kind": "cased",
            "openSide": True,
            "offset": fp(10.75) - fp(7.25),
            "width": fn(17.75) - fp(10.75),
            "height": WallH,
            "sill": 0,
            "hinge": "start",
        },
        # Puja alcove: West side open to family hall (leaving the two 2 ft side walls as screening returns)
        {
            "id": "g-puja-open",
            "roomId": "g-puja",
            "side": "rear",
            "kind": "cased",
            "openSide": True,
            "offset": 0,
            "width": fn(13.75) - fp(9.25),
            "height": WallH,
            "sill": 0,
            "hinge": "start",
        },
        # Compact corner stair: tall East-facing window (3.25 ft at x=2.25, y=17.75, sill 350, height 2500)
        # and open interfaces on North arrival, West hall release, and East hall side (x=9.75..12.5)
        {
            "id": "g-stair-east-window",
            "roomId": "g-stair",
            "side": "front",
            "kind": "window",
            "offset": 40,
            "width": 990,
            "height": 2500,
            "sill": 350,
            "hinge": "start",
        },
        {
            "id": "g-stair-open-arrival",
            "roomId": "g-stair",
            "side": "right",
            "kind": "cased",
            "openSide": True,
            "offset": 0,
            "width": st_y1 - st_y0,
            "height": WallH,
            "sill": 0,
            "hinge": "start",
        },
        {
            "id": "g-stair-open-west",
            "roomId": "g-stair",
            "side": "rear",
            "kind": "cased",
            "openSide": True,
            "offset": 0,
            "width": st_x1 - st_x0,
            "height": WallH,
            "sill": 0,
            "hinge": "start",
        },
        {
            "id": "g-stair-open-east",
            "roomId": "g-stair",
            "side": "front",
            "kind": "cased",
            "openSide": True,
            "offset": fp(9.75) - st_x0,
            "width": st_x1 - fp(9.75),
            "height": WallH,
            "sill": 0,
            "hinge": "start",
        },
        # Master bedroom (door at x=13.5, y=32.25, width 3 ft; West window at x=7, y=47.25, width 4.5 ft)
        # & attached bath (door at x=10.25, y=43, width 2.7 ft; West window)
        {
            "id": "g-master-door",
            "roomId": "g-master",
            "side": "front",
            "kind": "door",
            "offset": ft(13.5 - 1.5) - st_x0,
            "width": ft(3.0),
            "height": 2100,
            "sill": 0,
            "hinge": "start",
            "swingRoomId": "g-master",
        },
        {
            "id": "g-master-south-window",
            "roomId": "g-master",
            "side": "rear",
            "kind": "window",
            "offset": ft(7.0 - 2.25) - st_x0,
            "width": ft(4.5),
            "height": 1800,
            "sill": 600,
            "hinge": "start",
        },
        {
            "id": "g-bath-door",
            "roomId": "g-bath",
            "side": "left",
            "kind": "door",
            "offset": ft(43.0 - 1.35) - fp(39.75),
            "width": ft(2.7),
            "height": 2100,
            "sill": 0,
            "hinge": "start",
            "swingRoomId": "g-bath",
        },
        {
            "id": "g-bath-south-window",
            "roomId": "g-bath",
            "side": "rear",
            "kind": "window",
            "offset": ft(13.0 - 1.25) - fp(10.25),
            "width": ft(2.5),
            "height": 900,
            "sill": 1500,
            "hinge": "start",
        },
        # Care suite: hall slider (x=23.25), 3 ft L-return door (x=19.3, y=32.25),
        # 6.5 ft East car-porch window (x=32.5, y=careFront), 12–15 ft North garden window (x=36),
        # and 8 ft West veranda slider (x=29.75, y=careEnd)
        {
            "id": "g-care-hall-slider",
            "roomId": "g-family",
            "side": "right",
            "kind": "glazed",
            "sliding": True,
            "slidingPanels": 3,
            "offset": ft(draw_end + 0.25) + 450 - fp(7.25),
            "width": ft(o["glassClear"]),
            "height": 3000,
            "sill": 0,
            "hinge": "start",
        },
        {
            "id": "g-care-return-door",
            "roomId": "g-family",
            "side": "rear",
            "kind": "door",
            "offset": ft(19.3 - 1.5) - st_x0,
            "width": ft(3.0),
            "height": 2100,
            "sill": 0,
            "hinge": "start",
            "swingRoomId": "g-family",
        },
        {
            "id": "g-care-east-window",
            "roomId": "g-care",
            "side": "front",
            "kind": "window",
            "offset": ft(29.25) - fp(15.75),
            "width": ft(6.5),
            "height": 2700,
            "sill": 450,
            "hinge": "start",
        },
        {
            "id": "g-care-north-window",
            "roomId": "g-care",
            "side": "right",
            "kind": "window",
            "offset": ft(0.5),
            "width": ft(north_win_span),
            "height": 3000,
            "sill": 150,
            "hinge": "start",
        },
        {
            "id": "g-care-veranda-slider",
            "roomId": "g-veranda",
            "side": "front",
            "kind": "glazed",
            "sliding": True,
            "slidingPanels": 3,
            "offset": ft(29.75 - 4.0) - fp(15.75),
            "width": ft(8.0),
            "height": 3000,
            "sill": 0,
            "hinge": "start",
        },
    ]

    g_openings.append({"id": "g-kitchen-rear-open", "roomId": "g-kitchen", "side": "rear",
                       "kind": "cased", "openSide": True, "offset": st_x1 + WALL_MM - fp(4.25),
                       "width": fn(14.75) - (st_x1 + WALL_MM), "height": WallH, "sill": 0})

    if option_code == "E":
        # Option E caregiver & WC openings
        g_openings.extend([
            {
                "id": "g-caregiver-door",
                "roomId": "g-caregiver",
                "side": "front",
                "kind": "glazed",
                "sliding": True,
                "slidingPanels": 2,
                "offset": ft(25.5 + 2.4 - 1.5) - fp(25.25),
                "width": ft(3.0),
                "height": 2100,
                "sill": 0,
                "hinge": "start",
            },
            {
                "id": "g-wc-door",
                "roomId": "g-wc",
                "side": "right",
                "kind": "door",
                "offset": ft(44.0 - 1.25) - fp(40.25),
                "width": ft(2.5),
                "height": 2100,
                "sill": 0,
                "hinge": "start",
                "swingRoomId": "g-wc",
            },
            {
                "id": "g-caregiver-west-window",
                "roomId": "g-caregiver",
                "side": "rear",
                "kind": "window",
                "offset": ft(29.5 - 1.5) - fp(25.25),
                "width": ft(3.0),
                "height": 1800,
                "sill": 600,
                "hinge": "start",
            },
            {
                "id": "g-wc-window",
                "roomId": "g-wc",
                "side": "rear",
                "kind": "window",
                "offset": ft(22.5 - 1.0) - fp(19.75),
                "width": ft(2.0),
                "height": 900,
                "sill": 1500,
                "hinge": "start",
            },
        ])
    else:
        # Options A–D caregiver & WC openings
        g_openings.extend([
            {
                "id": "g-caregiver-door",
                "roomId": "g-caregiver",
                "side": "front",
                "kind": "glazed",
                "sliding": True,
                "slidingPanels": 2,
                "offset": ft(16.0 + 2.4 - 1.5) - fp(15.75),
                "width": ft(3.0),
                "height": 2100,
                "sill": 0,
                "hinge": "start",
            },
            {
                "id": "g-wc-door",
                "roomId": "g-wc",
                "side": "left",
                "kind": "door",
                "offset": ft(44.0 - 1.25) - fp(40.75),
                "width": ft(2.5),
                "height": 2100,
                "sill": 0,
                "hinge": "start",
                "swingRoomId": "g-wc",
            },
            {
                "id": "g-caregiver-west-window",
                "roomId": "g-caregiver",
                "side": "rear",
                "kind": "window",
                "offset": ft(20.0 - 1.5) - fp(15.75),
                "width": ft(3.0),
                "height": 1800,
                "sill": 600,
                "hinge": "start",
            },
            {
                "id": "g-wc-window",
                "roomId": "g-wc",
                "side": "rear",
                "kind": "window",
                "offset": ft(27.5 - 1.0) - fp(24.75),
                "width": ft(2.0),
                "height": 900,
                "sill": 1500,
                "hinge": "start",
            },
        ])

    # First-floor rooms
    # livingVoid exact coordinates from handoff:
    # [[16.25, drawEnd+1], [23, drawEnd+1], [23, 31.75], [12.75, 31.75], [12.75, 25.75], [16.25, 25.75]]
    void_front_w = draw_end + 0.75
    gal_e0 = fp(draw_end - 2.5)
    gal_e1 = fn(void_front_w)
    u_stair = {
        "id": "u-stair",
        "kind": "stair",
        "name": "Upper staircase core",
        "guardStyle": "white-timber",
        "polygon": rect_poly(st_x0, st_y0, st_x1, st_y1),
    }
    u_living_void = {
        "id": "u-living-void",
        "kind": "void",
        "name": "Double-height living void",
        "openToBelow": True,
        "polygon": [
            [fp(16.0), fp(void_front_w)],
            [fn(23.25), fp(void_front_w)],
            [fn(23.25), fn(32.0)],
            [fp(9.25), fn(32.0)],
            [fp(9.25), st_y1 + WALL_MM],
            [fp(16.0), st_y1 + WALL_MM],
        ],
    }
    # Guarded upper gallery & upperStairArrival (x=12.5..16, y=22..25.5) wrapping livingVoid
    u_lobby = {
        "id": "u-lobby",
        "kind": "hall",
        "name": "Upper stair arrival & gallery",
        "polygon": [
            [fp(5.75), fp(10.75)],
            [fn(16.0), fp(10.75)],
            [fn(16.0), gal_e0],
            [fn(26.5), gal_e0],
            [fn(26.5), fn(36.0)],
            [st_x1 + WALL_MM, fn(36.0)],
            [st_x1 + WALL_MM, fp(32.0)],
            [fp(23.25), fp(32.0)],
            [fp(23.25), gal_e1],
            [fn(16.0), gal_e1],
            [fn(16.0), st_y1],
            [st_x1 + WALL_MM, st_y1],
            [st_x1 + WALL_MM, fn(17.75)],
            [fp(5.75), fn(17.75)],
        ],
    }
    u_bath = {
        "id": "u-bath",
        "kind": "bathroom",
        "name": "Upper bathroom · southeast",
        "polygon": rect_poly(st_x0, fp(7.25), fn(5.75), fn(17.75)),
    }
    u_study = {
        "id": "u-study",
        "kind": "study",
        "name": "Upper lounge · study",
        "polygon": rect_poly(fp(16.0), fp(10.75), fn(28.75), fn(draw_end - 2.5)),
    }
    u_master = {
        "id": "u-master",
        "kind": "bedroom",
        "name": "Upper bedroom · southwest",
        "wardrobeWall": "left",
        "polygon": [[st_x0, st_y1 + WALL_MM], [fn(9.25), st_y1 + WALL_MM], [fn(9.25), fp(32.0)], [st_x1, fp(32.0)], [st_x1, fn(39.75)], [st_x0, fn(39.75)]],
    }
    u_terrace = {
        "id": "u-terrace",
        "kind": "terrace",
        "name": "East upper terrace",
        "clearAccess": True,
        "finishStyle": "honed-sandstone",
        "polygon": rect_poly(fp(5.75), fp(7.25), fn(17.25), fn(10.75)),
    }
    u_walls = [
        {
            "id": "u-master-void-wall",
            "a": [ft(9.25), st_y1 + HALF_MM],
            "b": [ft(9.25), ft(32.0)],
        },

    ]

    u_openings = [
        {
            "id": "u-stair-open-arrival",
            "roomId": "u-stair",
            "side": "right",
            "kind": "cased",
            "openSide": True,
            "offset": 0,
            "width": st_y1 - st_y0,
            "height": WallH,
            "sill": 0,
            "hinge": "start",
        },
        {
            "id": "u-bath-door",
            "roomId": "u-bath",
            "side": "right",
            "kind": "door",
            "offset": ft(13.5 - 1.3) - fp(7.25),
            "width": ft(2.6),
            "height": 2100,
            "sill": 0,
            "hinge": "start",
            "swingRoomId": "u-bath",
        },
        {
            "id": "u-bath-east-window",
            "roomId": "u-bath",
            "side": "front",
            "kind": "window",
            "offset": ft(4.5 - 1.25) - st_x0,
            "width": ft(2.5),
            "height": 900,
            "sill": 1500,
            "hinge": "start",
        },
        {
            "id": "u-study-door",
            "roomId": "u-study",
            "side": "left",
            "kind": "door",
            "offset": ft(14.0 - 1.4) - fp(10.75),
            "width": ft(2.8),
            "height": 2100,
            "sill": 0,
            "hinge": "start",
            "swingRoomId": "u-study",
        },
        {
            "id": "u-study-east-window",
            "roomId": "u-study",
            "side": "front",
            "kind": "window",
            "offset": ft(22.5 - 2.0) - fp(16.0),
            "width": ft(4.0),
            "height": 1800,
            "sill": 900,
            "hinge": "start",
        },
        {
            "id": "u-study-north-window",
            "roomId": "u-study",
            "side": "right",
            "kind": "window",
            "offset": ft(14.25 - 1.75) - fp(10.75),
            "width": ft(3.5),
            "height": 1800,
            "sill": 600,
            "hinge": "start",
        },
        {
            "id": "u-master-door",
            "roomId": "u-master",
            "side": "right",
            "kind": "door",
            "offset": fp(32.0) + 120 - (st_y1 + WALL_MM),
            "width": 750,
            "height": 2100,
            "sill": 0,
            "hinge": "end",
            "swingRoomId": "u-master",
        },
        {
            "id": "u-master-south-window",
            "roomId": "u-master",
            "side": "left",
            "kind": "window",
            "offset": ft(29.5 - 2.0) - (st_y1 + WALL_MM),
            "width": ft(4.0),
            "height": 1800,
            "sill": 600,
            "hinge": "start",
        },
        {
            "id": "u-master-west-window",
            "roomId": "u-master",
            "side": "rear",
            "kind": "window",
            "offset": ft(6.0 - 1.75) - st_x0,
            "width": ft(3.5),
            "height": 1800,
            "sill": 600,
            "hinge": "start",
        },
        {
            "id": "u-lobby-terrace-door",
            "roomId": "u-lobby",
            "side": "front",
            "kind": "glazed",
            "sliding": True,
            "slidingPanels": 2,
            "offset": ft(12.25 - 1.4) - fp(5.75),
            "width": ft(2.8),
            "height": 2400,
            "sill": 0,
            "hinge": "start",
        },
        {
            "id": "u-lobby-north-window",
            "roomId": "u-lobby",
            "side": "right",
            "kind": "window",
            "offset": ft(28.0 - 2.0) - fp(10.75),
            "width": ft(4.0),
            "height": 1800,
            "sill": 600,
            "hinge": "start",
        },
    ]

    u_openings.append({"id": "u-study-gallery-slider", "roomId": "u-study", "side": "rear",
                       "kind": "glazed", "sliding": True, "slidingPanels": 3, "offset": 150,
                       "width": ft(9.0), "height": 3000, "sill": 0})

    handoff_meta = canonical_handoff_zones(option_code)

    custom_plan = {
        "schema": "floorforge.custom-plan/1",
        "units": "mm",
        "wallThickness": WALL_MM,
        "facadeStyle": "warm-layered",
        "entranceStyle": "wall-supported",
        "frontCourt": "tiled",
        "interiorFloor": "ivory-vitrified",
        "doorsClosed": False,
        "colonyContext": "tirumala-colony",
        "tirumalaRevision": REVISION,
        "tirumalaOption": option_code,
        "tirumalaMeta": handoff_meta,
        "parkedCar": {"x": ft(34.25), "y": ft(10.0)},
        "sceneSeed": o["sceneSeed"],
        "floors": [
            {
                "id": "floor-0",
                "rooms": [
                    g_porch,
                    g_drawing,
                    g_kitchen,
                    g_puja,
                    g_south_lane,
                    g_stair,
                    g_family,
                    g_master,
                    g_bath,
                    g_care,
                    g_caregiver,
                    g_wc,
                    g_veranda,
                ],
                "walls": [],
                "openings": g_openings,
            },
            {
                "id": "floor-1",
                "rooms": [
                    u_stair,
                    u_living_void,
                    u_lobby,
                    u_bath,
                    u_study,
                    u_master,
                    u_terrace,
                ],
                "walls": u_walls,
                "openings": u_openings,
            },
        ],
        "stairs": [
            {
                "id": "south-corner-stair",
                "roomIds": ["g-stair", "u-stair"],
                "rotation": 90,
                "openArrival": True,
                "flightWidth": 1067,
                "well": 152,
                "landing": 1067,
                "tread": round((3658 - 1067) / 9, 4),
            }
        ],
    }

    brief = {
        "title": "Tirumala" if option_code == "A" else f"Tirumala ({o['label']})",
        "width_mm": PLOT_W_MM,
        "depth_mm": PLOT_D_MM,
        "front_mm": 0,
        "left_mm": 0,
        "right_mm": 0,
        "rear_mm": 0,
        "plinth_mm": PLINTH_MM,
        "storeys": 2,
        "floor_height_mm": FLOOR_H_MM,
        "bedrooms": 3,
        "attached_baths": 0,
        "eldercare": True,
        "open_kitchen": True,
        "vastu": "moderate",
        "parking": True,
        "pooja": True,
        "roof_access": False,
        "exterior_theme": "modern_tropical",
        "interior_theme": "bright_natural",
        "road_bearing_deg": 90,
    }
    notes = (
        f"Tirumala Revision 9 — {o['label']}: {o['summary']} "
        "40 ft East frontage (9 m road + basketball-court enclosure) x 50 ft North/South depth "
        "(12 m North road + opposite colony garden). Compact 12 x 7.5 ft South-wall corner stair "
        "(climb South, turn West, return North; 20 risers @ 182.9 mm, 9 treads @ 287.9 mm) with "
        "tall 3.25 ft East lane glazing and open North arrival. Continuous +300 mm house/court/porch/veranda "
        "datum with two 150 mm front entrance rises and ±0 mm 10.5 x 19 ft car bay. "
        "Revision 9 enlarges the kitchen to approximately 81 sq ft, widens drawing to 11 ft, "
        "relocates dining beside the rear of the stair, broadens the glass-linked upper gallery, "
        "and opens the rooflight through the slab. Care and ground master retain their floor areas."
    )
    guide_floors = [
        [
            ["bathroom", "bedroom-2", "veranda", "veranda"],
            ["bedroom-1", "family", "care-room", "care-room"],
            ["stair", "family", "drawing-room", "drawing-room"],
            ["veranda", "kitchen", "veranda", "veranda"],
        ],
        [
            ["", "", "", ""],
            ["bedroom-1", "hall", "void", ""],
            ["stair", "hall", "study", "study"],
            ["bathroom", "terrace", "terrace", ""],
        ],
        [
            ["", "", "", ""],
            ["", "", "", ""],
            ["", "", "", ""],
            ["", "", "", ""],
        ],
    ]

    return {
        "schema": "floorforge.project/0.4",
        "brief": brief,
        "customPlan": custom_plan,
        "editorState": {
            "customPlan": custom_plan,
            "guideEdited": False,
            "guideFloors": guide_floors,
            "mode": "custom",
            "useRoomBoard": False,
        },
        "notes": notes,
        "draftRevision": REVISION,
    }


def all_option_projects() -> dict[str, dict[str, Any]]:
    """Return all five Revision-9 option project payloads keyed by option code ('A'..'E')."""
    return {code: build_option_project(code) for code in OPTIONS}
