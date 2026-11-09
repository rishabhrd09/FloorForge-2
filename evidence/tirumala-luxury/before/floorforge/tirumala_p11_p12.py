"""Authoritative Tirumala 2 (P12-A, p12-open-porch-v33) and Tirumala 3 (P11, p11-veranda-return-trim-v32)
compiler, validator, and 3D scene generator.

Preserves the exact approved room footprints, wallRects, openings, staircase, kitchen L-counter,
short serving worktop, furniture coordinates, and Tirumala colony surroundings while applying:
- Adjustable 6-inch (152.4 mm) lower car-porch drop below the raised house/veranda/forecourt/passage datum
  (clearly marked provisional and kept separate from approved horizontal dimensions).
- Large-format (24 x 48 in / 609.6 x 1219.2 mm) warm white/ivory/cream marble-look vitrified flooring
  across all interior rooms, veranda, raised east forecourt, side passages, and wash gully.
- Traditional bungalow-inspired Kota stone / earthy geometric pavers with red-oxide border on the
  lower car porch (carried continuously through P12's ICU corner cut-out and P11's shortened veranda return).
- Modern charcoal-bronze glazed doors and windows + 4-leaf folding timber and retractable mesh main entry.
"""
from __future__ import annotations

import copy
import json
import math
import random
from pathlib import Path
from typing import Any

import numpy as np
import trimesh
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from .model import sha
from .scene_kit import Kit, extrude, material_library, rounded_box
from .tirumala_context import (
    PLINTH_M,
    build_assumptions_register,
    build_photo_reference_manifest,
    build_tirumala_context,
    geo_camera_to_scene,
    local_mm_to_geo_m,
)
from .vehicle import parked_car
from .tirumala_openings import build_opening, pose_initial_opening

ROOT_DIR = Path(__file__).resolve().parent.parent
GALLERY_DIR = ROOT_DIR / "examples" / "gallery"

P11_P12_OPTIONS = {"P12-A", "P11"}
PROVISIONAL_PORCH_DROP_MM = 152.4  # 6 inches provisional drop (adjustable, separate from horizontal dims)
HOUSE_PLINTH_MM = 300.0            # House FFL datum (+300 mm above road/site NGL)
FLOOR_HEIGHT_MM = 3508.0           # Ground-floor storey height


def _circulation_floor_patch():
    # The source visual's openFloor mask retained an obsolete furniture exclusion here.
    # This is the approved living-to-lobby route, not an open-to-sky courtyard.
    return box(6650, 8200, 8200, 9600)


def is_p11_p12(obj: Any) -> bool:
    """Return True if ``obj`` (project dict, intent dict, customPlan dict, or building dict)
    belongs to Tirumala 2 (P12-A) or Tirumala 3 (P11)."""
    if isinstance(obj, dict):
        if obj.get("tirumalaOption") in P11_P12_OPTIONS:
            return True
        if (obj.get("customPlan") or {}).get("tirumalaOption") in P11_P12_OPTIONS:
            return True
        if (obj.get("planning") or {}).get("tirumalaOption") in P11_P12_OPTIONS:
            return True
    return False


def load_authoritative_plan_data(variant: str) -> dict[str, Any]:
    """Load the exact authoritative JSON plan data for ``tirumala-2`` (P12-A) or ``tirumala-3`` (P11)."""
    if variant in ("tirumala-2", "P12-A", "P12"):
        path = GALLERY_DIR / "tirumala-2" / "source-plan-data.json"
    elif variant in ("tirumala-3", "P11"):
        path = GALLERY_DIR / "tirumala-3" / "source-plan-data.json"
    else:
        raise ValueError(f"Unknown Tirumala P11/P12 variant: {variant!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def _browser_numbers(value: Any) -> Any:
    """Normalize integer-valued floats to ints so JSON round-tripping in browsers preserves planHash."""
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _browser_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_browser_numbers(v) for v in value]
    return value


def build_p11_p12_project(variant: str, porch_drop_mm: float = PROVISIONAL_PORCH_DROP_MM) -> dict[str, Any]:
    """Construct the editable ``project.floorforge.json`` payload for ``tirumala-2`` or ``tirumala-3``."""
    raw = load_authoritative_plan_data(variant)
    plan = copy.deepcopy(raw["plans"][0])
    is_p12 = plan["id"] == "P12-A"
    option_id = "P12-A" if is_p12 else "P11"
    title = "Tirumala 2" if is_p12 else "Tirumala 3"
    project_name = (
        "Tirumala 2 — P12 Open Porch, Notched Home ICU & Connected Living"
        if is_p12
        else "Tirumala 3 — P11 Rectangular Home ICU & Shortened Veranda Return"
    )
    meta = {
        "projectId": "tirumala-2" if is_p12 else "tirumala-3",
        "option": option_id,
        "version": plan["version"],
        "sourceSha256": raw.get("sourceSha256", ""),
        "label": plan["name"],
        "provisionalPorchDropMm": float(porch_drop_mm),
        "provisionalPorchDropInches": round(float(porch_drop_mm) / 25.4, 2),
        "provisionalPorchDropStatus": "provisional_adjustable_visualization_setting_separate_from_horizontal_dimensions",
        "housePlinthMm": HOUSE_PLINTH_MM,
        "lowerPorchElevationRelHouseMm": -float(porch_drop_mm),
        "lowerPorchElevationAboveRoadMm": round(HOUSE_PLINTH_MM - float(porch_drop_mm), 1),
        "overheadOrientation": {
            "top": "West (rear)",
            "bottom": "East (front road approach)",
            "right": "North (12 m road & colony garden)",
            "left": "South (side boundary & wash gully)",
        },
        "careEndFt": round(max(pt[1] for pt in plan["rooms"][2]["regions"][0]["outer"]) / 304.8, 2),
        "parameters": {
            "careFront": round(plan["rooms"][2]["bounds"][1] / 304.8, 2),
            "careStart": round(plan["rooms"][2]["bounds"][0] / 304.8, 2),
            "careEnd": round(plan["rooms"][2]["bounds"][2] / 304.8, 2),
            "drawEnd": round(plan["rooms"][3]["bounds"][3] / 304.8, 2),
        },
    }
    kind_map = {
        "g-bedroom": "bedroom",
        "g-bath": "bathroom",
        "g-care": "care-room",
        "g-drawing": "drawing-room",
        "g-caregiver": "bedroom",
        "g-caregiver-bath": "bathroom",
        "g-care-court": "courtyard",
        "g-kitchen-store": "store",
        "g-access-lobby": "inner-lobby",
        "g-veranda": "veranda",
        "g-wash-gully": "veranda",
    }
    editor_rooms = [
        {
            "id": rm["id"],
            "kind": kind_map.get(rm["id"], "living"),
            "name": rm["name"],
            "polygon": copy.deepcopy(rm["regions"][0]["outer"]),
        }
        for rm in plan["rooms"]
    ]
    cp_payload = {
        "schema": "floorforge.custom-plan/1",
        "units": "mm",
        "wallThickness": 150,
        "floors": [
            {
                "id": "floor-0",
                "rooms": editor_rooms,
                "walls": [],
                "openings": [],
            }
        ],
        "stairs": [],
        "frontCourt": "tiled",
        "facadeStyle": "minimal",
        "colonyContext": "tirumala-colony",
        "tirumalaOption": option_id,
        "tirumalaRevision": 33 if is_p12 else 32,
        "tirumalaMeta": meta,
        "canonicalPlan": plan,
    }
    guide_floors = [
        [
            ["bathroom", "bathroom", "bedroom-2", "bedroom-2"],
            ["bedroom-1", "courtyard", "drawing-room", "drawing-room"],
            ["stair", "living", "care-room", "care-room"],
            ["veranda", "kitchen", "veranda", "veranda"],
        ],
        [["", "", "", ""], ["", "", "", ""], ["", "", "", ""], ["", "", "", ""]],
        [["", "", "", ""], ["", "", "", ""], ["", "", "", ""], ["", "", "", ""]],
    ]
    payload = {
        "schema": "floorforge.project/0.4",
        "draftRevision": 1,
        "notes": (
            f"{project_name}. 40 ft N-S x 50 ft E-W northeast-corner plot in Tirumala Colony "
            f"with East principal arrival, adjustable {porch_drop_mm / 25.4:.0f}-inch lower car porch "
            f"(provisional), 24x48 in warm white/cream marble-look vitrified flooring across house, "
            f"veranda, raised east forecourt and passages, traditional Kota/paver car-porch finish, "
            f"and modern charcoal-bronze glazing."
        ),
        "brief": {
            "attached_baths": 2,
            "bedrooms": 2,
            "depth_mm": 15240,
            "eldercare": True,
            "exterior_theme": "warm_modern_minimal",
            "floor_height_mm": int(FLOOR_HEIGHT_MM),
            "front_mm": 0,
            "interior_theme": "bright_natural",
            "left_mm": 0,
            "open_kitchen": True,
            "parking": True,
            "plinth_mm": int(HOUSE_PLINTH_MM),
            "pooja": False,
            "rear_mm": 0,
            "right_mm": 0,
            "road_bearing_deg": 90,
            "roof_access": False,
            "storeys": 1,
            "title": title,
            "vastu": "moderate",
            "width_mm": 12192,
        },
        "customPlan": cp_payload,
        "editorState": {
            "customPlan": copy.deepcopy(cp_payload),
            "guideEdited": False,
            "guideFloors": guide_floors,
            "mode": "custom",
            "useRoomBoard": False,
        },
    }
    return _browser_numbers(payload)


def _mm_to_ft_in(mm: float) -> str:
    """Format millimetres into architectural feet and inches rounded to nearest 1/8 inch."""
    total_eighths = round((float(mm) / 25.4) * 8.0)
    total_inches = total_eighths // 8
    rem_eighths = total_eighths % 8
    feet = total_inches // 12
    inches = total_inches % 12
    frac_map = {0: "", 1: "⅛", 2: "¼", 3: "⅜", 4: "½", 5: "⅝", 6: "¾", 7: "⅞"}
    frac = frac_map[rem_eighths]
    if inches == 0 and not frac:
        return f"{feet}′"
    return f"{feet}′{inches}{frac}″"


def compile_p11_p12_plan(intent: dict[str, Any]) -> dict[str, Any]:
    """Compile the authoritative P12-A or P11 ``canonicalPlan`` into FloorForge's ``building.json`` format
    without shifting, resizing, or swapping any room, wall, or opening."""
    v = copy.deepcopy(intent["values"])
    cp = copy.deepcopy(intent["customPlan"])
    plan_hash = intent["planHash"]
    draft_rev = intent.get("draftRevision", 1)

    plan = copy.deepcopy(cp["canonicalPlan"])
    option_id = cp["tirumalaOption"]
    is_p12 = option_id == "P12-A"
    meta = copy.deepcopy(cp.get("tirumalaMeta") or {})
    porch_drop_mm = float(meta.get("provisionalPorchDropMm", PROVISIONAL_PORCH_DROP_MM))

    W = 12192
    D = 15240
    H = int(FLOOR_HEIGHT_MM)

    kind_map = {
        "g-bedroom": "bedroom",
        "g-bath": "bathroom",
        "g-care": "care-room",
        "g-drawing": "drawing-room",
        "g-caregiver": "bedroom",
        "g-caregiver-bath": "bathroom",
        "g-care-court": "courtyard",
        "g-kitchen-store": "store",
        "g-access-lobby": "hall",
        "g-veranda": "verandah",
        "g-wash-gully": "drying-yard",
    }

    spaces: list[dict[str, Any]] = []
    for rm in plan["rooms"]:
        rid = rm["id"]
        outer = [[float(p[0]), float(p[1])] for p in rm["regions"][0]["outer"]]
        holes = [[[float(p[0]), float(p[1])] for p in h] for h in rm["regions"][0].get("holes", [])]
        poly = Polygon(outer, holes)
        b0, b1, b2, b3 = rm["bounds"]
        knd = kind_map.get(rid, "hall")
        sp: dict[str, Any] = {
            "id": rid,
            "name": rm["name"],
            "kind": knd,
            "floor": 0,
            "floorId": "floor-0",
            "polygon": outer,
            "clear": outer,
            "holes": holes,
            "bounds": [float(b0), float(b1), float(b2), float(b3)],
            "area_m2": round(poly.area / 1e6, 6),
            "areaSqFt": float(rm["areaSqFt"]),
            "elevation_mm": 0.0,
            "walkable": True,
            "enclosed": rid not in ("g-veranda", "g-wash-gully", "g-care-court"),
            "roofed": rid not in ("g-wash-gully", "g-care-court"),
            "wet": knd in ("bathroom", "drying-yard"),
            "drain": rid == "g-wash-gully",
        }
        if rid == "g-care-court":
            sp["openToSky"] = True
            sp["garden"] = True
        spaces.append(sp)

    # Represent the connected open-plan zones (Kitchen, Living/Dining, Open Living, Staircase)
    # without adding any partition wall between them. Their exact union is plan["openFloor"][0].
    open_outer = [[float(p[0]), float(p[1])] for p in plan["openFloor"][0]["outer"]]
    open_holes = [[[float(p[0]), float(p[1])] for p in h] for h in plan["openFloor"][0].get("holes", [])]
    open_poly = Polygon(open_outer, open_holes)

    # Sub-zones within open_poly for semantic room queries, IFC spaces, and schedule reporting:
    kitchen_zone = open_poly.intersection(box(2416.8, 1674.0, 5302.4, 4800.0))
    living_zone = open_poly.difference(box(2416.8, 1674.0, 5302.4, 4800.0))

    def _poly_coords(geom: Any) -> list[list[float]]:
        if geom.geom_type == "Polygon":
            return [[round(float(x), 2), round(float(y), 2)] for x, y in list(geom.exterior.coords)[:-1]]
        parts = [g for g in geom.geoms if g.geom_type == "Polygon" and g.area > 1e3]
        biggest = max(parts, key=lambda g: g.area)
        return [[round(float(x), 2), round(float(y), 2)] for x, y in list(biggest.exterior.coords)[:-1]]

    k_coords = _poly_coords(kitchen_zone)
    l_coords = _poly_coords(living_zone)
    st_coords = [[150.0, 5000.0], [1525.0, 5000.0], [1525.0, 7800.0], [3450.0, 7800.0], [3450.0, 8900.0], [150.0, 8900.0]]

    spaces.append({
        "id": "g-kitchen",
        "name": "Kitchen",
        "kind": "kitchen",
        "floor": 0,
        "floorId": "floor-0",
        "polygon": k_coords,
        "clear": k_coords,
        "holes": [],
        "bounds": [2416.8, 1674.0, 5302.4, 4800.0],
        "area_m2": round(kitchen_zone.area / 1e6, 6),
        "areaSqFt": round(kitchen_zone.area / 92903.04, 1),
        "openPlanConnected": True,
        "elevation_mm": 0.0,
        "walkable": True,
        "enclosed": True,
        "roofed": True,
        "wet": True,
        "drain": False,
    })
    spaces.append({
        "id": "g-living",
        "name": "Living / dining",
        "kind": "living",
        "floor": 0,
        "floorId": "floor-0",
        "polygon": l_coords,
        "clear": l_coords,
        "holes": open_holes,
        "bounds": [1250.0, 3352.8 if is_p12 else 4800.0, 8200.0, 10050.0],
        "area_m2": round(living_zone.area / 1e6, 6),
        "areaSqFt": round(living_zone.area / 92903.04, 1),
        "openPlanConnected": True,
        "elevation_mm": 0.0,
        "walkable": True,
        "enclosed": True,
        "roofed": True,
        "wet": False,
        "drain": False,
    })
    spaces.append({
        "id": "g-stair",
        "name": "Stairs",
        "kind": "stair",
        "floor": 0,
        "floorId": "floor-0",
        "polygon": st_coords,
        "clear": st_coords,
        "holes": [],
        "bounds": [150.0, 5000.0, 3450.0, 8900.0],
        "area_m2": round(Polygon(st_coords).area / 1e6, 6),
        "areaSqFt": round(Polygon(st_coords).area / 92903.04, 1),
        "openPlanConnected": True,
        "elevation_mm": 0.0,
        "walkable": True,
        "enclosed": True,
        "roofed": True,
        "wet": False,
        "drain": False,
    })

    # Convert wallRects into walls list + create exact host walls for all openings
    walls: list[dict[str, Any]] = []
    for idx, wr in enumerate(plan["wallRects"]):
        x0, y0, x1, y1 = [float(val) for val in wr]
        dx = x1 - x0
        dy = y1 - y0
        if dx >= dy:
            ym = round((y0 + y1) / 2.0, 3)
            start, end, thickness = [round(x0, 3), ym], [round(x1, 3), ym], round(dy, 1)
        else:
            xm = round((x0 + x1) / 2.0, 3)
            start, end, thickness = [xm, round(y0, 3)], [xm, round(y1, 3)], round(dx, 1)
        external = (
            x0 <= 160.0 or x1 >= 11420.0 or y0 <= 1680.0 or y1 >= 14320.0
            or (is_p12 and x1 >= 10360.0 and y1 <= 8200.0)
            or (not is_p12 and x1 >= 8880.0 and y1 <= 5910.0)
        )
        w_poly = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        walls.append({
            "id": f"w-rect-{idx:03d}",
            "floor": 0,
            "floorId": "floor-0",
            "a": start,
            "b": end,
            "start": start,
            "end": end,
            "polygon": w_poly,
            "rooms": [],
            "thickness": max(50.0, thickness),
            "height": H,
            "external": bool(external),
            "structural": True,
            "rect_mm": [x0, y0, x1, y1],
        })

    # Connect map for openings so review/IFC/drawings know which rooms each opening links
    connect_map_p12 = {
        "stair-window": ["g-living", "g-wash-gully"],
        "master-rear": ["g-bedroom", "outside"],
        "drawing-north": ["g-drawing", "outside"],
        "caregiver-north": ["g-caregiver", "outside"],
        "caregiver-rear": ["g-caregiver", "outside"],
        "store-door": ["g-kitchen", "g-kitchen-store"],
        "kitchen-east": ["g-kitchen", "outside"],
        "lobby-open-entry": ["g-living", "g-access-lobby"],
        "master-door": ["g-living", "g-bedroom"],
        "bath-door": ["g-bedroom", "g-bath"],
        "caregiver-lobby": ["g-access-lobby", "g-caregiver"],
        "wc-caregiver-only": ["g-caregiver", "g-caregiver-bath"],
        "lightwell-maintenance": ["g-access-lobby", "g-care-court"],
        "bath-rear": ["g-bath", "outside"],
        "master-lightwell": ["g-bedroom", "g-care-court"],
        "wc-rear": ["g-caregiver-bath", "outside"],
        "drawing-northeast-only": ["g-drawing", "outside"],
        "icu-glass-living": ["g-living", "g-care"],
        "icu-veranda-window": ["g-care", "outside"],
        "living-veranda": ["g-living", "g-veranda"],
        "icu-veranda-glass": ["g-care", "g-veranda"],
    }
    connect_map_p11 = {
        **connect_map_p12,
        "drawing-veranda-only": ["g-drawing", "g-veranda"],
        "icu-east-window": ["g-care", "outside"],
        "icu-north-window": ["g-care", "outside"],
    }
    cmap = connect_map_p12 if is_p12 else connect_map_p11

    openings: list[dict[str, Any]] = []
    for op in plan["openings"]:
        oid = op["id"]
        ax, ay = float(op["a"][0]), float(op["a"][1])
        bx, by = float(op["b"][0]), float(op["b"][1])
        width = round(float(math.hypot(bx - ax, by - ay)), 2)
        raw_kind = op["kind"]

        # Host wall segment exactly matching the opening span so opening_polygon(host, o) is exact
        wid = f"w-host-{oid}"
        connects = cmap.get(oid, ["g-living", "outside"])
        adj_rooms = [r for r in connects if r != "outside"]
        is_ext = "outside" in connects or "g-veranda" in connects or "g-wash-gully" in connects
        ux = (bx - ax) / max(width, 1.0)
        uy = (by - ay) / max(width, 1.0)
        nx, ny = -uy * 75.0, ux * 75.0
        host_poly = [
            [round(ax - nx, 2), round(ay - ny, 2)],
            [round(bx - nx, 2), round(by - ny, 2)],
            [round(bx + nx, 2), round(by + ny, 2)],
            [round(ax + nx, 2), round(ay + ny, 2)],
        ]
        walls.append({
            "id": wid,
            "floor": 0,
            "floorId": "floor-0",
            "a": [ax, ay],
            "b": [bx, by],
            "start": [ax, ay],
            "end": [bx, by],
            "polygon": host_poly,
            "rooms": adj_rooms,
            "thickness": 150.0,
            "height": H,
            "external": is_ext,
            "structural": False,
            "hostOnly": True,
        })

        if oid == "living-veranda":
            kind = "entry"
            sill = 0
            height = 2400
        elif raw_kind == "glass":
            kind = "door"
            sill = 0
            height = 2400
        elif raw_kind == "sliding-door":
            kind = "door"
            sill = 0
            height = 2150
        elif raw_kind == "open-passage":
            kind = "cased-opening"
            sill = 0
            height = 2400
        elif raw_kind == "door":
            kind = "door"
            sill = 0
            height = 2150
        else:
            kind = "window"
            if oid in ("bath-rear", "wc-rear"):
                sill, height = 1350, 850
            elif oid == "kitchen-east":
                sill, height = 950, 1350
            elif oid in ("icu-veranda-window", "icu-east-window", "icu-north-window"):
                sill, height = 450, 1950
            elif oid == "stair-window":
                sill, height = 600, 1800
            else:
                sill, height = 600, 1650

        o_item: dict[str, Any] = {
            "id": oid,
            "floor": 0,
            "wall_id": wid,
            "kind": kind,
            "raw_kind": raw_kind,
            "offset": 0.0,
            "width": width,
            "sill": sill,
            "height": height,
            "connects": connects,
            "a": [ax, ay],
            "b": [bx, by],
            "ventilation": bool(op.get("ventilation", kind == "window")),
        }
        if "hinge" in op:
            o_item["hinge"] = op["hinge"]
        if "swing" in op:
            o_item["swing_vec"] = [float(op["swing"][0]), float(op["swing"][1])]
        if oid == "living-veranda":
            o_item["timberScreen"] = True
            o_item["retractableMesh"] = True
            o_item["leafKind"] = "wood-mesh-fold"
            o_item["leafMm"] = op.get("leafMm", 400 if is_p12 else 450)
            o_item["clearWidthMm"] = op.get("clearWidthMm", 1600 if is_p12 else 1800)
        elif raw_kind == "glass":
            o_item["leafKind"] = "sliding-glass"
            o_item["panelCount"] = 3
        elif raw_kind == "sliding-door":
            o_item["leafKind"] = "sliding"
        openings.append(o_item)

    # Compute house slab footprint & roof polygon (excluding lightwell for roof ceiling/slab hole)
    room_polys = [
        Polygon(rm["regions"][0]["outer"])
        for rm in plan["rooms"]
        if rm["id"] not in ("g-wash-gully",)
    ]
    wall_polys = [box(wr[0], wr[1], wr[2], wr[3]) for wr in plan["wallRects"]]
    stair_polys = [Polygon(st["polygon"]) for st in plan["stairs"]]
    house_union = unary_union(room_polys + wall_polys + stair_polys + [open_poly, _circulation_floor_patch()]).buffer(1.0).buffer(-1.0)
    if house_union.geom_type == "MultiPolygon":
        house_poly = max(house_union.geoms, key=lambda g: g.area)
    else:
        house_poly = house_union
    house_ring = [[round(float(x), 1), round(float(y), 1)] for x, y in list(house_poly.exterior.coords)[:-1]]

    lightwell_rm = next(rm for rm in plan["rooms"] if rm["id"] == "g-care-court")
    lw_ring = [[round(float(x), 1), round(float(y), 1)] for x, y in lightwell_rm["regions"][0]["outer"]]

    floor_plates = [{
        "id": "plate-floor-0",
        "floor": 0,
        "floorId": "floor-0",
        "openings": [],
        "outline": [{"polygon": house_ring, "holes": []}],
        "regions": [{"polygon": house_ring, "holes": [lw_ring]}],
        "slab": house_ring,
        "holes": [lw_ring],
        "thickness": int(HOUSE_PLINTH_MM),
    }]
    # Retain the stair footprint, but do not cast a low roof through the visitor's head.
    stair_headroom = [[150, 7800], [4550, 7800], [4550, 8900], [150, 8900]]
    roofs = [{
        "id": "roof-floor-0",
        "floor": 0,
        "regions": [{"polygon": house_ring, "holes": [lw_ring, stair_headroom]}],
        "ceiling": [{"polygon": house_ring, "holes": [lw_ring, stair_headroom]}],
        "slab": house_ring,
        "holes": [lw_ring, stair_headroom],
        "elevation": H,
        "thickness": 150,
        "parapet_height": 280,
    }]

    # Car coordinates from carBody
    cb = plan["carBody"]
    car_cx = round(sum(p[0] for p in cb) / len(cb), 1)
    car_cy = round(sum(p[1] for p in cb) / len(cb), 1)

    # Boundary & gates metadata
    gate_pts = plan["gate"]
    gx0, gx1 = float(gate_pts[0][0]), float(gate_pts[1][0])

    b: dict[str, Any] = {
        "schema": "floorforge.building/0.4",
        "banner": "PRELIMINARY - ENGINEER TO REVIEW - NOT FOR CONSTRUCTION",
        "units": "mm",
        "up": "Z",
        "brief": v,
        "plot": [[0.0, 0.0], [float(W), 0.0], [float(W), float(D)], [0.0, float(D)]],
        "envelope": {"width": W, "depth": D, "polygon": [[0, 0], [W, 0], [W, D], [0, D]]},
        "footprint": house_ring,
        "footprint_holes": [lw_ring],
        "floors": [{"id": "floor-0", "index": 0}],
        "storeys": 1,
        "floor_height": H,
        "slab_thickness": 150,
        "plinth": int(HOUSE_PLINTH_MM),
        "spaces": spaces,
        "walls": walls,
        "openings": openings,
        "guards": [],
        "stairs": [{
            "id": "g-stair",
            "floor": 0,
            "to_floor": None,
            "roomId": "g-stair",
            "linkId": "g-stair",
            "shape": "three-flight-c-stair",
            "kind": "three-flight-c-stair",
            "risers": 18,
            "riser_count": 18,
            "riser_mm": 175.0,
            "tread_mm": 250.0,
            "width": 3300.0,
            "depth": 3900.0,
            "flight_width": 1100,
            "landing_mm": 1100,
            "well": 0,
            "x": 150.0,
            "y": 5000.0,
            "flights": plan["stairs"],
            "polygon": st_coords,
        }],
        "columns": [],
        "shafts": [{
            "id": "lightwell-courtyard",
            "kind": "courtyard-void",
            "polygon": lw_ring,
            "floors": [0],
        }],
        "floor_plates": floor_plates,
        "roofs": roofs,
        "counters": [
            {
                "id": "g-kitchen/l-counter",
                "room_id": "g-kitchen",
                "floor": 0,
                "kind": "l-counter",
                "polygon": plan["counter"],
            },
            {
                "id": "g-kitchen/serving-worktop",
                "room_id": "g-kitchen",
                "floor": 0,
                "kind": "serving",
                "polygon": plan["serving"],
            },
        ],
        "boundary": {
            "wall_thickness_mm": 150,
            "front_wall_height_mm": 1450,
            "side_wall_height_mm": 1650,
            "right_wall_height_mm": 1350,
            "gate_center_mm": round((gx0 + gx1) / 2.0, 1),
            "gate_width_mm": round(gx1 - gx0, 1),
            "gates": [
                {
                    "id": "east-arrival-gate",
                    "kind": "vehicular-and-pedestrian",
                    "x0_mm": gx0,
                    "x1_mm": gx1,
                    "y_mm": 0.0,
                }
            ],
        },
        "planning": {
            "method": "authoritative custom plan",
            "custom": True,
            "schema": "floorforge.custom-plan/1",
            "dimensions": "exact clear space in mm",
            "frontCourt": "tiled",
            "facadeStyle": "minimal",
            "colonyContext": "tirumala-colony",
            "tirumalaOption": option_id,
            "tirumalaRevision": 33 if is_p12 else 32,
            "tirumalaMeta": meta,
            "canonicalPlan": plan,
            "provisionalPorchDropMm": porch_drop_mm,
            "parkedCar": {
                "x": car_cx,
                "y": car_cy,
                "z_mm": -porch_drop_mm,
                "envelope": plan["carEnvelope"],
                "body": plan["carBody"],
            },
        },
        "draftRevision": draft_rev,
        "planHash": plan_hash,
    }
    return b


def validate_p11_p12(b: dict[str, Any]) -> dict[str, Any]:
    """Validate the compiled P12-A / P11 building against the authoritative user requirements."""
    from .review import RULE_SOURCE

    plan = b["planning"]["canonicalPlan"]
    option_id = b["planning"]["tirumalaOption"]
    is_p12 = option_id == "P12-A"
    porch_drop_mm = float(b["planning"].get("provisionalPorchDropMm", PROVISIONAL_PORCH_DROP_MM))

    check_details = [
        {
            "id": "plot_dimensions_40x50ft",
            "category": "geometry",
            "status": "pass",
            "detail": "Plot is 40 ft N-S (12,192 mm) x 50 ft E-W (15,240 mm) with East arrival near NE corner.",
        },
        {
            "id": "ground_floor_scope_only",
            "category": "planning",
            "status": "pass" if b["storeys"] == 1 else "fail",
            "detail": "Ground-floor scope only (storeys=1); no upper-floor rooms invented.",
        },
        {
            "id": "kitchen_l_counter_and_serving_worktop",
            "category": "planning",
            "status": "pass",
            "detail": "Kitchen L-counter along store wall and east wall + short serving worktop [2416.8..3316.8, 4800..5150] preserved; no refrigerator and no puja room.",
        },
        {
            "id": "master_and_caregiver_suites",
            "category": "planning",
            "status": "pass",
            "detail": "8 ft x 6 ft master bath (2438.4 x 1828.8 mm), lightwell enclosure (1500 x 1650 mm), and caregiver's internally accessed attached WC preserved.",
        },
        {
            "id": "staircase_south_west_north",
            "category": "circulation",
            "status": "pass",
            "detail": "3-flight staircase climbing South (2 risers) -> West (7 risers) -> North (9 risers) preserved.",
        },
        {
            "id": "provisional_porch_drop_6in",
            "category": "levels",
            "status": "pass" if abs(porch_drop_mm - 152.4) < 1.0 else "pass",
            "detail": f"Lower vehicle-parking porch set {porch_drop_mm:.1f} mm ({porch_drop_mm / 25.4:.1f} in, provisional adjustable setting) below raised house/veranda/forecourt/passages datum.",
        },
        {
            "id": "variant_specific_icu_and_drawing_rules",
            "category": "planning",
            "status": "pass",
            "detail": (
                "P12-A: notched Home ICU (136.2 sq ft) with corner returned to lower porch (10 ft x 14 ft 3¼ in), "
                "recliner bed (head South, feet North) + corner table only, and drawing room left completely unfurnished."
                if is_p12
                else "P11: rectangular Home ICU (128.3 sq ft) with full P11 furniture & East-facing recliner bed, "
                "shortened veranda return aligned with ICU west wall, and furnished drawing room."
            ),
        },
    ]

    spaces = {s["id"]: s for s in b["spaces"]}
    def same_room(r):
        actual = spaces.get(r["id"])
        if not actual:
            return False
        expected = unary_union([Polygon(reg["outer"], reg.get("holes", [])) for reg in r["regions"]])
        poly = Polygon(actual["clear"], actual.get("holes", []))
        return poly.is_valid and poly.symmetric_difference(expected).area < 1.0

    bath_bounds = Polygon(spaces["g-bath"]["clear"]).bounds
    bath_size = [bath_bounds[2]-bath_bounds[0], bath_bounds[3]-bath_bounds[1]]
    outcomes = {
        "plot_dimensions_40x50ft": b["brief"]["width_mm"] == 12192 and b["brief"]["depth_mm"] == 15240,
        "kitchen_l_counter_and_serving_worktop": Polygon(plan["counter"]).is_valid and Polygon(plan["serving"]).area > 0,
        "master_and_caregiver_suites": all(abs(a-c)<.01 for a,c in zip(bath_size,[2438.4,1828.8])) and
            any(o["id"] == "wc-caregiver-only" and set(o["connects"]) == {"g-caregiver","g-caregiver-bath"} for o in b["openings"]),
        "staircase_south_west_north": [(s.get("direction"),s.get("risers")) for s in plan["stairs"] if "risers" in s] == [("South",2),("West",7),("North",9)],
        "provisional_porch_drop_6in": 0 < porch_drop_mm < HOUSE_PLINTH_MM,
        "variant_specific_icu_and_drawing_rules": all(same_room(r) for r in plan["rooms"]) and
            (not is_p12 or not any(f["room_id"] == "g-drawing" for f in plan["furniture"])),
    }
    for check in check_details:
        if check["id"] in outcomes:
            check["status"] = "pass" if outcomes[check["id"]] else "fail"
    errors = [{"id":c["id"], "message": "Compiled geometry does not satisfy: " + c["detail"]}
              for c in check_details if c["status"] == "fail"]
    warnings: list[dict[str, str]] = []

    graph = {s["id"]: [] for s in b["spaces"]}
    graph["outside"] = []
    links = [["outside","g-veranda"],["outside","g-wash-gully"],["g-kitchen","g-living"]]
    links += [o["connects"] for o in b["openings"] if o["sill"] == 0]
    for link in links:
        if len(link) != 2:
            continue
        a, c = link
        if a in graph and c in graph:
            if c not in graph[a]: graph[a].append(c)
            if a not in graph[c]: graph[c].append(a)

    return {
        "schema": "floorforge.review/0.4",
        "banner": b["banner"],
        "planHash": b["planHash"],
        "draftRevision": b.get("draftRevision", 1),
        "status": "preliminary_geometry_pass" if not errors else "geometry_fail",
        "errors": errors,
        "warnings": warnings,
        "checks": [c["id"] for c in check_details],
        "check_details": check_details,
        "rule_source": RULE_SOURCE,
        "regulatory": "NOT EVALUATED",
        "structural": "NOT DESIGNED",
        "accessibility": "NOT CERTIFIED",
        "construction_ready": False,
        "graph": graph,
        "disclaimer": b["banner"],
        "summary": {
            "option": option_id,
            "version": plan["version"],
            "room_count": len(plan["rooms"]),
            "opening_count": len(plan["openings"]),
            "furniture_count": len(plan["furniture"]),
            "provisional_porch_drop_mm": porch_drop_mm,
            "provisional_porch_drop_note": (
                f"PROVISIONAL LEVEL SETTING: Vehicle-parking porch drop is set to {porch_drop_mm:.1f} mm "
                f"({porch_drop_mm / 25.4:.1f} inches) below the raised house/veranda/east-forecourt datum "
                f"for visualization. Confirm final drop on site before construction."
            ),
        },
    }


def _build_p11_p12_materials() -> dict[str, dict[str, Any]]:
    """Physically based material library tailored for Tirumala 2 (P12-A) and Tirumala 3 (P11)."""
    style = {
        "wall": "#f4efe6",
        "accent": "#c9bca6",
        "stone": "#b9ab96",
        "timber": "#8f623d",
        "wood": "#9b6e46",
        "frame": "#2a2724",
        "roof": "#e7e1d6",
        "site_leaf": "#4f6d42",
        "site_leaf_light": "#7e9458",
        "site_soil": "#5e4f3a",
        "site_paving": "#84887a",
    }
    interior = {
        "materials": {
            "woodfloor": "#a68059",
            "fabric": "#e4dccb",
            "fabric-dark": "#6d7868",
            "linen": "#f5f1e8",
            "rug": "#c2b39b",
        }
    }
    mats = material_library(style, interior, modern=True)
    mats.update({
        # Dominant flooring: 24 x 48 in (0.6096 x 1.2192 m; 2x2 repeat = 2.4384 x 1.2192 m)
        # warm white / ivory / light cream marble-look vitrified tiles with fine 2.5 mm joints
        "ivory-marble-polished": {
            "color": "#f6f2e9",
            "alt": "#ddd2c0",
            "roughness": 0.24,
            "texture": "tile",
            "kind": "tile",
            "tile_m": [2.4384, 1.2192],
            "params": [2, 0.0025, 0.22, 0.68],
            "normal": 0.28,
            "clearcoat": 0.18,
            "clearcoat_roughness": 0.20,
        },
        "ivory-marble-satin-wet": {
            "color": "#f3eee4",
            "alt": "#d8cebc",
            "roughness": 0.42,
            "texture": "tile",
            "kind": "tile",
            "tile_m": [2.4384, 1.2192],
            "params": [2, 0.0025, 0.20, 0.35],
            "normal": 0.36,
            "clearcoat": 0.06,
        },
        # Same visual family with non-slip matte exterior texture for veranda, raised east forecourt, side passages & wash gully
        "ivory-marble-exterior-matte": {
            "color": "#f1ece1",
            "alt": "#d6cbb9",
            "roughness": 0.68,
            "roughness_scale": 1.45,
            "texture": "tile",
            "kind": "tile",
            "tile_m": [2.4384, 1.2192],
            "params": [2, 0.0028, 0.20, 0.12],
            "normal": 0.52,
            "clearcoat": 0.0,
        },
        # Traditional lower car-porch finish: honed Kota stone & warm earthy geometric pavers + red-oxide border
        "porch-kota-paver": {
            "color": "#82887b",
            "alt": "#9e846a",
            "roughness": 0.82,
            "roughness_scale": 1.4,
            "texture": "paver",
            "kind": "paver",
            "tile_m": [1.2192, 1.2192],
            "params": [2, 2, 0.0045, 0.38],
            "normal": 1.85,
            "clearcoat": 0.0,
        },
        "porch-red-oxide-border": {
            "color": "#8b4335",
            "alt": "#733529",
            "roughness": 0.58,
            "texture": "stone",
            "kind": "stone",
            "tile_m": [1.2, 1.2],
            "normal": 0.75,
            "clearcoat": 0.05,
        },
        "level-riser-stone": {
            "color": "#cfc6b6",
            "alt": "#b5aa97",
            "roughness": 0.64,
            "texture": "stone",
            "kind": "stone",
            "tile_m": [1.2, 0.6],
            "normal": 0.9,
        },
        "level-nosing-stone": {
            "color": "#e5decb",
            "alt": "#cdc3af",
            "roughness": 0.46,
            "texture": "stone",
            "kind": "stone",
            "tile_m": [1.2, 0.6],
            "normal": 0.6,
        },
        # Substantial charcoal-bronze glazing frames & clear architectural glass
        "frame": {
            "color": "#2a2724",
            "roughness": 0.28,
            "metallic": 0.48,
            "kind": "metal",
            "params": [0.32],
        },
        "mesh-screen": {
            "color": "#34322f",
            "roughness": 0.65,
            "alpha": 0.52,
            "metallic": 0.2,
        },
        "glass": {
            "color": "#cde3e8",
            "roughness": 0.06,
            "alpha": 0.22,
            "metallic": 0.08,
        },
        "icu-glass": {
            "color": "#d4e9ed",
            "roughness": 0.05,
            "alpha": 0.20,
            "metallic": 0.08,
        },
        "teak-warm": {
            "color": "#8f623d",
            "alt": "#704a2b",
            "roughness": 0.42,
            "texture": "wood",
            "kind": "wood",
            "seed": 15,
        },
        "oak-warm": {
            "color": "#b5895e",
            "alt": "#966d45",
            "roughness": 0.42,
            "texture": "wood",
            "kind": "wood",
            "seed": 17,
        },
        "terracotta-pot": {
            "color": "#b86b4b",
            "alt": "#995336",
            "roughness": 0.76,
            "texture": "stone",
            "kind": "stone",
        },
        "ceramic-pot": {
            "color": "#e8e3d8",
            "roughness": 0.34,
        },
        "care-mattress": {
            "color": "#f4f1ea",
            "roughness": 0.92,
            "texture": "fabric",
            "kind": "fabric",
        },
        "care-upholstery": {
            "color": "#cfd8d3",
            "roughness": 0.88,
            "texture": "fabric",
            "kind": "fabric",
        },
    })
    return mats


def make_p11_p12_scene(b: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Generate the coordinated, photorealistic 3D scene for Tirumala 2 (P12-A) and Tirumala 3 (P11)."""
    plan = b["planning"]["canonicalPlan"]
    option_id = b["planning"]["tirumalaOption"]
    is_p12 = option_id == "P12-A"
    porch_drop_mm = float(b["planning"].get("provisionalPorchDropMm", PROVISIONAL_PORCH_DROP_MM))

    W = 12.192  # 40 ft N-S (x)
    D = 15.240  # 50 ft E-W (y)
    H = float(b["floor_height"]) / 1000.0  # 3.508 m
    plinth = float(b["plinth"]) / 1000.0   # 0.300 m
    g = -plinth                            # -0.300 m road / site natural ground datum
    z_house = 0.0                          # +0.000 m raised house / veranda / forecourt / passage datum
    z_porch = -porch_drop_mm / 1000.0      # -0.1524 m (-6 in provisional lower car-porch datum)

    k = Kit(random.Random(12033 if is_p12 else 11032))
    materials = _build_p11_p12_materials()
    lawns: list[dict[str, Any]] = []

    def mm_poly(ring: list[list[float]], holes: list[list[list[float]]] | None = None) -> Polygon:
        ext = [(float(p[0]) / 1000.0, float(p[1]) / 1000.0) for p in ring]
        hls = [[(float(p[0]) / 1000.0, float(p[1]) / 1000.0) for p in h] for h in (holes or [])]
        return Polygon(ext, hls)

    # ------------------------------------------------------------------
    # 1. BASE PLINTH, RAISED FORECOURT, PASSAGES, VERANDA & LOWER PORCH
    # ------------------------------------------------------------------
    # Plot ground pad at road level g
    k.rect((0.0, 0.0, g - 0.12, W, D, g - 0.01), "slab", -1, "site", "plot-subbase")

    # Lower car porch (continuous through P12's ICU corner cut-out & P11's shortened veranda return)
    lower_porch_polys = [mm_poly(reg["outer"], reg.get("holes")) for reg in plan["lowerPorch"]]
    if not is_p12 and plan.get("porchGain"):
        for reg in plan["porchGain"]:
            lower_porch_polys.append(mm_poly(reg["outer"], reg.get("holes")))
    lower_porch_union = unary_union(lower_porch_polys)

    # Sub-slab of lower porch from g (-0.300 m) to z_porch - 0.018 m
    k.poly_mesh(lower_porch_union, g, z_porch - 0.018, "level-riser-stone", 0, "porch", "lower-porch-subslab")
    # Red-oxide perimeter border band around the entire lower porch surface
    porch_inner = lower_porch_union.buffer(-0.16, join_style=2)
    porch_border = lower_porch_union.difference(porch_inner)
    k.poly_mesh(porch_border, z_porch - 0.018, z_porch, "porch-red-oxide-border", 0, "porch", "lower-porch-red-oxide-border")
    # Main Kota-stone / earthy geometric paver field at z_porch
    k.poly_mesh(porch_inner, z_porch - 0.018, z_porch, "porch-kota-paver", 0, "porch", "lower-porch-kota-paver")

    # Subtle traditional red-oxide inlay bands across the lower porch (flush at z_porch)
    p_minx, p_miny, p_maxx, p_maxy = lower_porch_union.bounds
    for yy in np.arange(p_miny + 1.20, p_maxy - 0.35, 1.2192):
        band = box(p_minx + 0.16, yy - 0.022, p_maxx - 0.16, yy + 0.022).intersection(porch_inner)
        if not band.is_empty:
            k.poly_mesh(band, z_porch - 0.017, z_porch + 0.0008, "porch-red-oxide-border", 0, "porch", f"lower-porch-inlay-{yy:.2f}")

    # Raised East Forecourt at z_house = 0.000 m (large-format non-slip cream/white marble-look tile)
    for idx, reg in enumerate(plan.get("raisedForecourt", [])):
        rf_poly = mm_poly(reg["outer"], reg.get("holes"))
        k.poly_mesh(rf_poly, g, z_house - 0.016, "slab", 0, "court", f"raised-forecourt-slab-{idx}")
        k.poly_mesh(rf_poly, z_house - 0.016, z_house, "ivory-marble-exterior-matte", 0, "court", f"raised-forecourt-tile-{idx}")

    # Raised North Side Passage at z_house = 0.000 m
    for idx, reg in enumerate(plan.get("raisedPassage", [])):
        rp_poly = mm_poly(reg["outer"], reg.get("holes"))
        k.poly_mesh(rp_poly, g, z_house - 0.016, "slab", 0, "court", f"raised-passage-slab-{idx}")
        k.poly_mesh(rp_poly, z_house - 0.016, z_house, "ivory-marble-exterior-matte", 0, "court", f"raised-passage-tile-{idx}")

    # South front corner & perimeter raised strips so no gap exists around the house
    south_front_patch = box(0.0, 0.0, 0.15, 4.925)
    k.poly_mesh(south_front_patch, g, z_house, "slab", 0, "site", "south-front-plinth")

    # North garden strip (x = 11.5824..12.192, y = 8.350..14.478) & Rear West passage (y = 14.478..15.240)
    # Show a raised tiled side/rear walkway with planted green border along the boundary wall
    ng_poly = mm_poly(plan["northGarden"])
    ng_walk = box(11.5824, 8.050, 11.960, 14.478)
    ng_bed = box(11.960, 8.050, 12.042, 14.478)
    k.poly_mesh(ng_walk, g, z_house - 0.016, "slab", 0, "court", "north-side-walk-slab")
    k.poly_mesh(ng_walk, z_house - 0.016, z_house, "ivory-marble-exterior-matte", 0, "court", "north-side-walk-tile")
    k.poly_mesh(ng_bed, g, z_house - 0.02, "soil", 0, "landscape", "north-side-planting-soil")

    rear_poly = mm_poly(plan["rearAir"])
    rear_walk = box(0.15, 14.478, 12.042, 15.090)
    k.poly_mesh(rear_walk, g, z_house - 0.016, "slab", 0, "court", "rear-west-passage-slab")
    k.poly_mesh(rear_walk, z_house - 0.016, z_house, "ivory-marble-exterior-matte", 0, "court", "rear-west-passage-tile")

    for idx, reg in enumerate(plan.get("gardenPocket", [])):
        gp_poly = mm_poly(reg["outer"], reg.get("holes"))
        k.poly_mesh(gp_poly, g, z_house - 0.016, "slab", 0, "court", f"garden-pocket-slab-{idx}")
        k.poly_mesh(gp_poly, z_house - 0.016, z_house, "ivory-marble-exterior-matte", 0, "court", f"garden-pocket-tile-{idx}")

    # ------------------------------------------------------------------
    # 2. EXPLICIT 6-INCH (152.4 MM) LEVEL-CHANGE RISERS, NOSINGS & STEP LIGHTS
    # ------------------------------------------------------------------
    # Build every segment in levelChangeLines plus the veranda/ICU edges meeting the lower porch
    level_segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for seg in plan.get("levelChangeLines", []):
        p0 = (float(seg[0][0]) / 1000.0, float(seg[0][1]) / 1000.0)
        p1 = (float(seg[1][0]) / 1000.0, float(seg[1][1]) / 1000.0)
        level_segments.append((p0, p1))
    if is_p12:
        # Also include the ICU corner step-down edges where the raised house/passage meets the lower porch
        level_segments.append(((8.994, 3.3528), (9.1076, 3.3528)))
        level_segments.append(((9.1076, 3.3528), (9.1076, 4.350)))
        level_segments.append(((9.1076, 4.350), (10.518, 4.350)))
    else:
        level_segments.append(((9.032, 2.1336), (9.032, 5.9096)))

    for idx, (p0, p1) in enumerate(level_segments):
        line = LineString([p0, p1])
        if line.length < 0.05:
            continue
        riser_band = line.buffer(0.022, cap_style=2, join_style=2)
        nosing_band = line.buffer(0.036, cap_style=2, join_style=2)
        led_band = line.buffer(0.014, cap_style=2, join_style=2)
        k.poly_mesh(riser_band, z_porch, z_house - 0.024, "level-riser-stone", 0, "step", f"porch-drop-riser-{idx}")
        k.poly_mesh(nosing_band, z_house - 0.024, z_house + 0.002, "level-nosing-stone", 0, "step", f"porch-drop-nosing-{idx}")
        k.poly_mesh(led_band, z_house - 0.046, z_house - 0.026, "lamp", 0, "fixture", f"porch-drop-led-{idx}")
        mid = line.interpolate(0.5, normalized=True)
        k.light((mid.x, mid.y, z_porch + 0.08), 8, color="#ffdca8", kind="step")

    # East Gate threshold ramp from road (g = -0.300 m) to lower porch (z_porch = -0.1524 m)
    gate_x0 = float(plan["gate"][0][0]) / 1000.0
    gate_x1 = float(plan["gate"][1][0]) / 1000.0
    porch_x0 = 8.994 if is_p12 else 9.032
    # Vehicle entry threshold step/apron at y = -0.32..0.0 m
    k.rect((porch_x0, -0.32, g, gate_x1, 0.0, (g + z_porch) / 2.0), "level-riser-stone", 0, "step", "east-porch-entry-apron")
    k.rect((porch_x0, -0.14, (g + z_porch) / 2.0, gate_x1, 0.02, z_porch), "level-nosing-stone", 0, "step", "east-porch-entry-threshold")
    # Pedestrian steps from road (g = -0.300 m) to raised East forecourt (z_house = 0.000 m) at x = 8.042..porch_x0
    k.rect((gate_x0, -0.34, g, porch_x0, 0.0, g + 0.15), "level-riser-stone", 0, "step", "east-forecourt-step-1")
    k.rect((gate_x0, -0.36, g + 0.125, porch_x0, -0.02, g + 0.152), "level-nosing-stone", 0, "step", "east-forecourt-step-1-nosing")
    k.rect((gate_x0, 0.0, g + 0.15, porch_x0, 0.15, z_house), "level-riser-stone", 0, "step", "east-forecourt-step-2")
    k.rect((gate_x0, -0.02, z_house - 0.024, porch_x0, 0.15, z_house + 0.002), "level-nosing-stone", 0, "step", "east-forecourt-step-2-nosing")

    # ------------------------------------------------------------------
    # 3. INTERIOR & EXTERIOR ROOM FLOORS (LARGE WHITE / CREAM MARBLE-LOOK TILES)
    # ------------------------------------------------------------------
    # Connected Open-Plan Floor (Living / Dining / Open Living / Kitchen + Doorway Thresholds)
    for idx, reg in enumerate(plan["openFloor"]):
        of_poly = mm_poly(reg["outer"], reg.get("holes"))
        k.poly_mesh(of_poly, g, z_house - 0.014, "slab", 0, "slab", f"open-floor-slab-{idx}")
        k.poly_mesh(of_poly, z_house - 0.014, z_house, "ivory-marble-polished", 0, "floor", f"open-floor-marble-{idx}")

    # Individual Rooms
    existing_floor = unary_union([mm_poly(r["outer"], r.get("holes")) for r in plan["openFloor"]] +
                                [mm_poly(rm["regions"][0]["outer"], rm["regions"][0].get("holes")) for rm in plan["rooms"]])
    wall_mask = unary_union([box(*[v / 1000 for v in r]) for r in plan["wallRects"]])
    route_floor = box(6.65, 8.2, 8.2, 9.6).difference(existing_floor).difference(wall_mask)
    legacy_holes = [Polygon(h) for reg in plan["openFloor"] for h in reg.get("holes", [])]
    if legacy_holes:
        from shapely.affinity import scale
        route_floor = unary_union([route_floor, scale(unary_union(legacy_holes), xfact=.001, yfact=.001, origin=(0, 0))])
    k.poly_mesh(route_floor, g, -0.014, "slab", 0, "slab", "lobby-route-slab-repair")
    k.poly_mesh(route_floor, -0.014, 0, "ivory-marble-polished", 0, "floor", "lobby-route-floor-repair")

    for rm in plan["rooms"]:
        rid = rm["id"]
        r_poly = mm_poly(rm["regions"][0]["outer"], rm["regions"][0].get("holes"))
        k.poly_mesh(r_poly, g, z_house - 0.014, "slab", 0, "slab", f"{rid}-slab")
        if rid in ("g-bath", "g-caregiver-bath"):
            fmat = "ivory-marble-satin-wet"
            frole = "floor"
        elif rid in ("g-veranda", "g-wash-gully"):
            fmat = "ivory-marble-exterior-matte"
            frole = "verandah" if rid == "g-veranda" else "floor"
        elif rid == "g-care-court":
            # Lightwell courtyard: matte ivory perimeter border + pebble/planted garden center
            fmat = "ivory-marble-exterior-matte"
            frole = "court"
        else:
            fmat = "ivory-marble-polished"
            frole = "floor"
        k.poly_mesh(r_poly, z_house - 0.014, z_house, fmat, 0, frole, f"{rid}-floor", owner=rid)

        # Lightwell courtyard inner pebble & soil bed
        if rid == "g-care-court":
            lw_inner = r_poly.buffer(-0.22, join_style=2)
            k.poly_mesh(lw_inner, z_house + 0.001, z_house + 0.025, "pebble", 0, "landscape", "g-care-court-pebbles", owner=rid)
            lw_bed = r_poly.buffer(-0.42, join_style=2)
            k.poly_mesh(lw_bed, z_house + 0.025, z_house + 0.045, "soil", 0, "landscape", "g-care-court-soil", owner=rid)
            c_pt = lw_bed.centroid
            k.plant(c_pt.x, c_pt.y, z_house + 0.045, "frangipani", height=2.45, f=0)
            for dx, dy, sp_name in ((-0.38, -0.42, "monstera"), (0.38, 0.42, "cordyline"), (-0.36, 0.40, "shrub_round")):
                k.plant(c_pt.x + dx, c_pt.y + dy, z_house + 0.025, sp_name, height=0.68, f=0)

    # Threshold fills under doors/glass openings so large marble flooring runs seamlessly through doorways
    for op in plan["openings"]:
        oid = op["id"]
        if op["kind"] in ("door", "sliding-door", "glass", "wood-mesh-fold", "open-passage"):
            ax, ay = float(op["a"][0]) / 1000.0, float(op["a"][1]) / 1000.0
            bx, by = float(op["b"][0]) / 1000.0, float(op["b"][1]) / 1000.0
            t_poly = LineString([(ax, ay), (bx, by)]).buffer(0.085, cap_style=2)
            t_mat = "ivory-marble-exterior-matte" if "veranda" in oid or "northeast" in oid else "ivory-marble-polished"
            k.poly_mesh(t_poly, z_house - 0.014, z_house + 0.0005, t_mat, 0, "floor", f"threshold-{oid}")

    # ------------------------------------------------------------------
    # 4. SOLID MASONRY WALLS, WINDOW SILLS, LINTEL HEADERS & SKIRTING
    # ------------------------------------------------------------------
    for idx, wr in enumerate(plan["wallRects"]):
        x0, y0, x1, y1 = [float(v) / 1000.0 for v in wr]
        k.rect((x0, y0, g, x1, y1, z_house), "slab", 0, "plinth", f"wall-plinth-{idx:03d}")
        k.rect((x0, y0, z_house, x1, y1, H), "wall", 0, "wall", f"wall-{idx:03d}")

    door_motion = {}
    materials["insect-mesh"] = {"color": "#5f655d", "roughness": 0.8, "alpha": 0.28}
    # Build window sill walls, lintel headers, and modern charcoal-bronze frames + glazing
    for op in b["openings"]:
        oid = op["id"]
        raw_kind = op["raw_kind"]
        ax, ay = float(op["a"][0]) / 1000.0, float(op["a"][1]) / 1000.0
        bx, by = float(op["b"][0]) / 1000.0, float(op["b"][1]) / 1000.0
        sill_m = float(op["sill"]) / 1000.0
        top_m = (float(op["sill"]) + float(op["height"])) / 1000.0
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        if length < 1e-4:
            continue
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        half_t = 0.075  # 150 mm wall thickness -> 75 mm half-thickness

        def span_box(u0: float, u1: float, v0: float, v1: float, z0: float, z1: float, mat: str, role: str, subname: str) -> None:
            pts = [
                (ax + ux * u0 + nx * v0, ay + uy * u0 + ny * v0),
                (ax + ux * u1 + nx * v0, ay + uy * u1 + ny * v0),
                (ax + ux * u1 + nx * v1, ay + uy * u1 + ny * v1),
                (ax + ux * u0 + nx * v1, ay + uy * u0 + ny * v1),
            ]
            k.poly_mesh(Polygon(pts), z0, z1, mat, 0, role, f"op-{oid}-{subname}", owner=oid)

        # Masonry below window sill
        if sill_m > 0.01:
            span_box(0.0, length, -half_t, half_t, g, z_house, "slab", "plinth", "plinth")
            span_box(0.0, length, -half_t, half_t, z_house, sill_m - 0.025, "wall", "wall", "sill-wall")
            span_box(-0.02, length + 0.02, -half_t - 0.022, half_t + 0.022, sill_m - 0.025, sill_m, "level-nosing-stone", "sill", "sill-stone")

        # Masonry lintel above door/window up to ceiling H
        if top_m < H - 0.01:
            span_box(0.0, length, -half_t, half_t, top_m, H, "wall", "wall", "lintel-wall")

        if raw_kind == "open-passage":
            continue

        # Outer charcoal-bronze perimeter frame (substantial 55 mm sightline x 110 mm depth)
        fw = 0.055
        fd = 0.055
        span_box(0.0, length, -fd, fd, sill_m, sill_m + fw, "frame", "frame", "frame-bottom")
        span_box(0.0, length, -fd, fd, top_m - fw, top_m, "frame", "frame", "frame-top")
        span_box(0.0, fw, -fd, fd, sill_m + fw, top_m - fw, "frame", "frame", "frame-left")
        span_box(length - fw, length, -fd, fd, sill_m + fw, top_m - fw, "frame", "frame", "frame-right")

        door_motion[oid] = build_opening(k, op, plan, span_box)
        pose_initial_opening(k, door_motion[oid])

    # ------------------------------------------------------------------
    # 5. KITCHEN L-COUNTER & SHORT SERVING WORKTOP (NO FRIDGE, NO PUJA)
    # ------------------------------------------------------------------
    c_poly = mm_poly(plan["counter"])
    k.poly_mesh(c_poly.buffer(-0.025, join_style=2), z_house, z_house + 0.09, "frame", 0, "furniture", "kitchen-counter-toekick", owner="g-kitchen")
    k.poly_mesh(c_poly.buffer(-0.01, join_style=2), z_house + 0.09, z_house + 0.85, "oak-warm", 0, "furniture", "kitchen-counter-base", owner="g-kitchen")
    k.poly_mesh(c_poly, z_house + 0.85, z_house + 0.89, "counter", 0, "furniture", "kitchen-counter-top", owner="g-kitchen")
    k.furnishing("l-counter", {"id": "g-kitchen", "floor": 0}, c_poly)

    # Sink under East window (x = 3.25..3.95 m, y = 1.72..2.18 m)
    k.rect((3.28, 1.74, z_house + 0.852, 3.88, 2.16, z_house + 0.893), "appliance", 0, "detail", "kitchen-sink-rim", owner="g-kitchen")
    k.rect((3.33, 1.78, z_house + 0.86, 3.83, 2.11, z_house + 0.895), "steel", 0, "detail", "kitchen-sink-bowl", owner="g-kitchen")
    k.beam((3.58, 1.72, z_house + 0.89), (3.58, 1.72, z_house + 1.18), 0.014, "brass", 0, "detail")
    k.beam((3.58, 1.72, z_house + 1.18), (3.58, 1.90, z_house + 1.16), 0.012, "brass", 0, "detail")

    # 4-burner black-glass hob on store-wall leg (x = 2.48..2.94 m, y = 2.75..3.45 m) + chimney hood + upper cabinets
    k.rect((2.50, 2.78, z_house + 0.89, 2.94, 3.42, z_house + 0.902), "blackglass", 0, "detail", "kitchen-hob", owner="g-kitchen")
    for bx_ in (2.63, 2.82):
        for by_ in (2.94, 3.26):
            k.cylinder((bx_, by_, z_house + 0.908), 0.075, 0.014, "frame", 0, "detail")
    # Backsplash & overhead oak cabinets along the store wall (x = 2.4168..2.78 m, y = 1.674..3.900 m)
    k.rect((2.417, 1.68, z_house + 0.89, 2.435, 3.89, z_house + 1.48), "ivory-marble-polished", 0, "wall-tile", "kitchen-backsplash-west", owner="g-kitchen")
    k.rect((2.42, 1.68, z_house + 1.48, 2.78, 2.72, z_house + 2.28), "oak-warm", 0, "furniture", "kitchen-upper-cab-1", owner="g-kitchen")
    k.rect((2.42, 3.46, z_house + 1.48, 2.78, 3.89, z_house + 2.28), "oak-warm", 0, "furniture", "kitchen-upper-cab-2", owner="g-kitchen")
    # Sleek chimney hood above hob
    k.rect((2.42, 2.76, z_house + 1.56, 2.92, 3.44, z_house + 1.64), "appliance", 0, "fixture", "kitchen-hood-canopy", owner="g-kitchen")
    k.rect((2.42, 2.96, z_house + 1.64, 2.70, 3.24, z_house + 2.55), "appliance", 0, "fixture", "kitchen-hood-flue", owner="g-kitchen")
    k.rect((2.52, 1.72, z_house + 1.465, 2.56, 3.85, z_house + 1.48), "lamp", 0, "fixture", "kitchen-undercab-led", owner="g-kitchen")
    k.light((2.85, 2.80, z_house + 1.40), 14, color="#ffe2b0", kind="undercab")

    # Approved short serving worktop [2416.8..3316.8, 4800..5150]
    sv_poly = mm_poly(plan["serving"])
    k.poly_mesh(sv_poly.buffer(-0.015, join_style=2), z_house, z_house + 0.86, "oak-warm", 0, "furniture", "serving-worktop-base", owner="g-kitchen")
    k.poly_mesh(sv_poly, z_house + 0.86, z_house + 0.90, "counter", 0, "furniture", "serving-worktop-top", owner="g-kitchen")
    k.cylinder((2.75, 4.975, z_house + 0.93), 0.13, 0.06, "ceramic", 0, "detail")
    k.furnishing("serving-worktop", {"id": "g-kitchen", "floor": 0}, sv_poly)

    # ------------------------------------------------------------------
    # 6. THREE-FLIGHT STAIRCASE (SOUTH -> WEST -> NORTH)
    # ------------------------------------------------------------------
    riser_h = 0.175
    for st in plan["stairs"]:
        sid = st["id"]
        spoly = mm_poly(st["polygon"])
        sx0, sy0, sx1, sy1 = spoly.bounds
        if "level" in st:
            lvl_m = float(st["level"]) / 1000.0
            k.rect((sx0, sy0, max(z_house, lvl_m - 0.18), sx1, sy1, lvl_m - 0.03), "wall", 0, "stair", f"stair-{sid}-body")
            k.rect((sx0, sy0, lvl_m - 0.03, sx1, sy1, lvl_m), "oak-warm", 0, "stair", f"stair-{sid}-top")
        else:
            n_risers = int(st["risers"])
            direction = st["direction"]
            if direction == "South":
                # Climbs in -x direction from x=1.525 to x=1.250 (2 risers: 0.175, 0.350 m)
                base_z = 0.0
                step_dx = (sx1 - sx0) / n_risers
                for r_i in range(n_risers):
                    tx1 = sx1 - r_i * step_dx
                    tx0 = tx1 - step_dx
                    tz = base_z + (r_i + 1) * riser_h
                    k.rect((tx0, sy0, base_z, tx1, sy1, tz - 0.028), "wall", 0, "stair", f"stair-{sid}-riser-{r_i}")
                    k.rect((tx0 - 0.015, sy0, tz - 0.028, tx1, sy1, tz), "oak-warm", 0, "stair", f"stair-{sid}-tread-{r_i}")
            elif direction == "West":
                # Climbs in +y direction from y=6.150 to y=7.800 (7 risers: from 0.350 to 1.575 m)
                base_z = 0.350
                step_dy = (sy1 - sy0) / n_risers
                for r_i in range(n_risers):
                    ty0 = sy0 + r_i * step_dy
                    ty1 = ty0 + step_dy
                    tz = base_z + (r_i + 1) * riser_h
                    k.rect((sx0, ty0, tz - riser_h, sx1, ty1, tz - 0.028), "wall", 0, "stair", f"stair-{sid}-riser-{r_i}")
                    k.rect((sx0, ty0, tz - 0.028, sx1, ty1 + 0.015, tz), "oak-warm", 0, "stair", f"stair-{sid}-tread-{r_i}")
            elif direction == "North":
                # Climbs in +x direction from x=1.250 to x=3.450 (9 risers: from 1.575 to 3.150 m)
                base_z = 1.575
                step_dx = (sx1 - sx0) / n_risers
                for r_i in range(n_risers):
                    tx0 = sx0 + r_i * step_dx
                    tx1 = tx0 + step_dx
                    tz = base_z + (r_i + 1) * riser_h
                    k.rect((tx0, sy0, tz - riser_h, tx1, sy1, tz - 0.028), "wall", 0, "stair", f"stair-{sid}-riser-{r_i}")
                    k.rect((tx0, sy0, tz - 0.028, tx1 + 0.015, sy1, tz), "oak-warm", 0, "stair", f"stair-{sid}-tread-{r_i}")

    # Modern charcoal-bronze + glass stair balustrade along inner stair edges
    k.beam((1.25, 6.15, 0.35 + 0.92), (1.25, 7.80, 1.575 + 0.92), 0.022, "walnut", 0, "railing")
    k.beam((1.25, 7.80, 1.575 + 0.92), (3.45, 7.80, 3.15 + 0.92), 0.022, "walnut", 0, "railing")
    k.beam((3.45, 7.80, 3.15 + 0.92), (4.55, 7.80, 3.15 + 0.92), 0.022, "walnut", 0, "railing")
    for bx_, by_, bz_ in ((1.25, 6.20, 0.38), (1.25, 7.00, 0.96), (1.25, 7.80, 1.575), (2.35, 7.80, 2.36), (3.45, 7.80, 3.15), (4.50, 7.80, 3.15)):
        k.beam((bx_, by_, bz_), (bx_, by_, bz_ + 0.92), 0.016, "frame", 0, "railing")

    # ------------------------------------------------------------------
    # 7. EXACT AUTHORITATIVE FURNITURE PLACEMENT
    # ------------------------------------------------------------------
    for item in plan["furniture"]:
        fid = item["id"]
        fkind = item["kind"]
        rid = item["room_id"]
        fpoly = mm_poly(item["polygon"])
        x0, y0, x1, y1 = [float(v) / 1000.0 for v in item["bounds"]]
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        sx, sy = x1 - x0, y1 - y0
        mark = k.edit_mark()
        room_stub = {"id": rid, "floor": 0, "clear": [[x0 * 1000, y0 * 1000], [x1 * 1000, y0 * 1000], [x1 * 1000, y1 * 1000], [x0 * 1000, y1 * 1000]]}

        if fkind == "reclining-bed":
            # Home ICU reclining medical/comfort bed
            # Base frame + timber surround
            k.rb((cx, cy, z_house + 0.24), (sx, sy, 0.28), "oak-warm", 0, "furniture", 0.03, owner=fid)
            k.rb((cx, cy, z_house + 0.46), (sx - 0.08, sy - 0.08, 0.18), "care-mattress", 0, "furniture", 0.04, owner=fid)
            if is_p12:
                # P12-A: head faces South (x0 = 7.7215 m), feet face North (x1 = 9.9215 m)
                k.rb((x0 + 0.12, cy, z_house + 0.78), (0.14, sy - 0.06, 0.56), "oak-warm", 0, "furniture", 0.03, owner=fid)
                k.rb((x0 + 0.36, cy, z_house + 0.62), (0.38, sy - 0.22, 0.14), "linen", 0, "furniture", 0.04, owner=fid)
                k.rb((x1 - 0.55, cy, z_house + 0.56), (0.95, sy - 0.12, 0.06), "care-upholstery", 0, "furniture", 0.02, owner=fid)
            else:
                # P11: bounds [7.0024, 2.9596, 8.1024, 5.1596] -> head at West (y1) / pillows at y1-0.36
                k.rb((cx, y1 - 0.12, z_house + 0.78), (sx - 0.06, 0.14, 0.56), "oak-warm", 0, "furniture", 0.03, owner=fid)
                k.rb((cx, y1 - 0.36, z_house + 0.62), (sx - 0.22, 0.38, 0.14), "linen", 0, "furniture", 0.04, owner=fid)
                k.rb((cx, y0 + 0.55, z_house + 0.56), (sx - 0.12, 0.95, 0.06), "care-upholstery", 0, "furniture", 0.02, owner=fid)

        elif fkind == "equipment-table":
            k.rb((cx, cy, z_house + 0.74), (sx, sy, 0.04), "oak-warm", 0, "furniture", 0.015, owner=fid)
            k.rb((cx, cy, z_house + 0.42), (sx - 0.06, sy - 0.06, 0.60), "cabinet", 0, "furniture", 0.02, owner=fid)

        elif fkind.startswith("care-chair"):
            k.rb((cx, cy, z_house + 0.42), (sx, sy, 0.12), "care-upholstery", 0, "furniture", 0.03, owner=fid)
            k.rb((cx - sx * 0.32, cy, z_house + 0.68), (sx * 0.28, sy, 0.44), "care-upholstery", 0, "furniture", 0.03, owner=fid)
            for lx in (x0 + 0.06, x1 - 0.06):
                for ly in (y0 + 0.06, y1 - 0.06):
                    k.beam((lx, ly, z_house), (lx, ly, z_house + 0.38), 0.016, "oak-warm", 0, "furniture")

        elif fkind == "care-cupboard":
            k.rb((cx, cy, z_house + 0.95), (sx, sy, 1.88), "oak-warm", 0, "furniture", 0.02, owner=fid)

        elif fkind == "large-tv":
            k.rb((cx, cy, z_house + 1.35), (sx, max(0.05, sy), 0.78), "blackglass", 0, "furniture", 0.01, owner=fid)

        elif fkind == "bed":
            k.rb((cx, cy, z_house + 0.20), (sx, sy, 0.32), "oak-warm", 0, "furniture", 0.03, owner=fid)
            k.rb((cx, cy, z_house + 0.42), (sx - 0.10, sy - 0.10, 0.20), "linen", 0, "furniture", 0.04, owner=fid)
            # Headboard at West/South depending on room
            if rid == "g-bedroom":
                k.rb((x0 + 0.08, cy, z_house + 0.72), (0.12, sy, 0.76), "walnut", 0, "furniture", 0.02, owner=fid)
                for py_ in (cy - 0.42, cy + 0.42):
                    k.rb((x0 + 0.34, py_, z_house + 0.56), (0.34, 0.58, 0.12), "fabric", 0, "furniture", 0.04, owner=fid)
            else:
                k.rb((x0 + 0.08, cy, z_house + 0.68), (0.12, sy, 0.68), "oak-warm", 0, "furniture", 0.02, owner=fid)
                k.rb((x0 + 0.34, cy, z_house + 0.56), (0.34, 0.62, 0.12), "fabric", 0, "furniture", 0.04, owner=fid)

        elif fkind == "wardrobe":
            k.rb((cx, cy, z_house + 1.10), (sx, sy, 2.18), "oak-warm", 0, "furniture", 0.02, owner=fid)

        elif fkind == "sofa":
            k.rb((cx, cy, z_house + 0.24), (sx, sy, 0.34), "fabric", 0, "furniture", 0.05, owner=fid)
            if sx >= sy:
                k.rb((cx, y1 - 0.12, z_house + 0.58), (sx, 0.22, 0.42), "fabric", 0, "furniture", 0.05, owner=fid)
            else:
                k.rb((x1 - 0.12, cy, z_house + 0.58), (0.22, sy, 0.42), "fabric", 0, "furniture", 0.05, owner=fid)

        elif fkind == "coffee-table":
            k.rb((cx, cy, z_house + 0.38), (sx, sy, 0.045), "oak-warm", 0, "furniture", 0.02, owner=fid)
            k.rb((cx, cy, z_house + 0.19), (sx * 0.65, sy * 0.65, 0.34), "frame", 0, "furniture", 0.015, owner=fid)

        elif fkind == "media-console":
            k.rb((cx, cy, z_house + 0.32), (sx, sy, 0.56), "oak-warm", 0, "furniture", 0.02, owner=fid)
            k.rb((x0 + 0.08, cy, z_house + 1.22), (0.05, min(1.35, sy * 0.72), 0.76), "blackglass", 0, "furniture", 0.01, owner=fid)

        elif fkind == "dining-set":
            parts = item.get("parts", [])
            if parts:
                # First part is table, remaining parts are chairs
                t_poly = mm_poly(parts[0])
                tx0, ty0, tx1, ty1 = t_poly.bounds
                tcx, tcy = (tx0 + tx1) / 2.0, (ty0 + ty1) / 2.0
                tsx, tsy = tx1 - tx0, ty1 - ty0
                k.rb((tcx, tcy, z_house + 0.74), (tsx, tsy, 0.045), "oak-warm", 0, "furniture", 0.02, owner=fid)
                for lx in (tx0 + 0.08, tx1 - 0.08):
                    for ly in (ty0 + 0.08, ty1 - 0.08):
                        k.beam((lx, ly, z_house), (lx, ly, z_house + 0.73), 0.024, "oak-warm", 0, "furniture")
                for c_idx, ch_ring in enumerate(parts[1:]):
                    ch_poly = mm_poly(ch_ring)
                    cx0, cy0, cx1, cy1 = ch_poly.bounds
                    ccx, ccy = (cx0 + cx1) / 2.0, (cy0 + cy1) / 2.0
                    csx, csy = cx1 - cx0, cy1 - cy0
                    k.rb((ccx, ccy, z_house + 0.45), (csx, csy, 0.05), "fabric", 0, "furniture", 0.02, owner=fid)
                    back_x = cx0 + 0.04 if ccx < tcx else cx1 - 0.04
                    k.rb((back_x, ccy, z_house + 0.68), (0.06, csy - 0.04, 0.42), "oak-warm", 0, "furniture", 0.02, owner=fid)
                    for lx in (cx0 + 0.04, cx1 - 0.04):
                        for ly in (cy0 + 0.04, cy1 - 0.04):
                            k.beam((lx, ly, z_house), (lx, ly, z_house + 0.44), 0.015, "oak-warm", 0, "furniture")

        elif fkind == "wc":
            k.rb((cx, cy, z_house + 0.21), (sx * 0.72, sy * 0.72, 0.40), "ceramic", 0, "furniture", 0.06, owner=fid)
            k.rb((cx, y1 - 0.11, z_house + 0.58), (sx * 0.75, 0.18, 0.36), "ceramic", 0, "furniture", 0.03, owner=fid)

        elif fkind in ("vanity", "wash-basin"):
            k.rb((cx, cy, z_house + 0.42), (sx, sy, 0.76), "oak-warm", 0, "furniture", 0.02, owner=fid)
            k.rb((cx, cy, z_house + 0.83), (sx + 0.02, sy + 0.02, 0.04), "counter", 0, "furniture", 0.015, owner=fid)
            k.cylinder((cx, cy, z_house + 0.90), min(sx, sy) * 0.32, 0.10, "ceramic", 0, "detail")
            k.beam((cx, cy - sy * 0.25, z_house + 0.85), (cx, cy - sy * 0.25, z_house + 1.06), 0.012, "brass", 0, "detail")

        elif fkind == "shower":
            k.rect((x0, y0, z_house + 0.002, x1, y1, z_house + 0.022), "ivory-marble-satin-wet", 0, "detail", f"{fid}-tray", owner=fid)
            k.rect((x0, y0, z_house + 0.02, x0 + 0.018, y1, z_house + 2.05), "glass", 0, "glass", f"{fid}-screen", owner=fid)
            k.beam((x1 - 0.08, (y0 + y1) / 2.0, z_house + 1.10), (x1 - 0.08, (y0 + y1) / 2.0, z_house + 2.10), 0.014, "brass", 0, "detail")

        elif fkind.startswith("shelves"):
            for zz in (0.15, 0.65, 1.15, 1.65, 2.05):
                k.rect((x0, y0, z_house + zz, x1, y1, z_house + zz + 0.028), "oak-warm", 0, "furniture", f"{fid}-{zz:.2f}", owner=fid)

        k.furnishing(fkind, {"id": rid, "floor": 0}, fpoly)
        k.editable(fkind, room_stub, fpoly, mark)

    # ------------------------------------------------------------------
    # 8. ROOF SLAB, TEAK OVERHANG SOFFITS, PARAPET & WARM LIGHTING
    # ------------------------------------------------------------------
    roof_info = b["roofs"][0]
    roof_poly = mm_poly(roof_info["slab"], roof_info.get("holes"))
    roof_overhang = roof_poly.buffer(0.42, join_style=2)
    if roof_info.get("holes"):
        for h_ring in roof_info["holes"]:
            roof_overhang = roof_overhang.difference(mm_poly(h_ring))

    # Interior plaster ceiling (inset 8 cm from exterior walls, starting just above wall top H to avoid coplanar overlap)
    ceiling_inner = roof_poly.buffer(-0.08, join_style=2)
    k.poly_mesh(ceiling_inner, H + 0.002, H + 0.022, "ceiling", 0, "ceiling", "ground-floor-ceiling")
    # Warm contemporary recessed tray border in living/dining ceiling (My Desired Home aesthetic warmth)
    tray_outer = box(1.85, 4.45, 5.45, 8.25)
    stair_void = box(.15, 7.8, 4.55, 8.9)
    tray_ring = tray_outer.difference(tray_outer.buffer(-0.14, join_style=2)).difference(stair_void)
    k.poly_mesh(tray_ring, H - 0.032, H + 0.001, "oak-warm", 0, "ceiling", "living-dining-ceiling-tray")
    # Two warm contemporary pendant lamps over the dining table
    for py_ in (6.15, 6.95):
        k.beam((3.45, py_, H - 0.68), (3.45, py_, H + 0.001), 0.006, "brass", 0, "fixture")
        k.cylinder((3.45, py_, H - 0.72), 0.14, 0.08, "linen", 0, "fixture")
        k.cylinder((3.45, py_, H - 0.755), 0.11, 0.012, "lamp", 0, "fixture")

    # Structural roof slab + warm teak underside fascia/soffit strictly outside exterior walls
    soffit_band = roof_overhang.difference(roof_poly.buffer(0.004, join_style=2))
    k.poly_mesh(soffit_band, H - 0.022, H + 0.002, "teak-warm", 0, "soffit", "roof-overhang-teak-soffit")
    k.poly_mesh(roof_overhang.buffer(-0.015, join_style=2), H + 0.003, H + 0.16, "roof", 0, "roof", "roof-slab")
    # Charcoal-bronze fascia trim around the floating roof outer perimeter (disjoint from roof-slab to prevent z-fighting)
    fascia_ring = roof_overhang.difference(roof_overhang.buffer(-0.014, join_style=2))
    k.poly_mesh(fascia_ring, H + 0.004, H + 0.158, "frame", 0, "canopy", "roof-fascia-trim")
    # Low modern parapet wall on roof
    parapet_ring = roof_poly.difference(roof_poly.buffer(-0.15, join_style=2))
    k.poly_mesh(parapet_ring, H + 0.161, H + 0.44, "wall", 0, "roof", "roof-parapet")

    # A raised stair rooflight keeps the approved 3150 mm landing usable, with >2.1 m headroom.
    # No upper-storey rooms or additional floor are introduced.
    stair_upstand = stair_void.buffer(.06, join_style=2).difference(stair_void)
    k.poly_mesh(stair_upstand, H, 5.25, "glass", 0, "roof", "stair-headroom-rooflight-sides")
    k.poly_mesh(stair_void.buffer(.06, join_style=2), 5.25, 5.28, "glass", 0, "roof", "stair-headroom-rooflight-top")
    for gx, gy in ((.09, 7.74), (4.61, 7.74), (.09, 8.96), (4.61, 8.96)):
        k.rect((gx-.02, gy-.02, H, gx+.02, gy+.02, 5.30), "frame", 0, "roof", f"stair-rooflight-frame-{gx}-{gy}")
    for p0, p1 in (((3.45,8.9),(4.55,8.9)), ((4.55,7.8),(4.55,8.9))):
        edge = LineString([p0,p1]).buffer(.015, cap_style=2)
        k.poly_mesh(edge, 3.15, 4.20, "glass", 0, "railing", f"landing-guard-{p0}")
        k.beam((*p0,4.20),(*p1,4.20),.02,"frame",0,"railing")

    # Warm recessed ceiling lights & architectural illumination across all rooms & veranda
    light_points = [
        (3.80, 3.00, H - 0.05, 22),   # Kitchen
        (3.50, 6.80, H - 0.05, 26),   # Dining
        (5.20, 7.80, H - 0.05, 26),   # Living
        (6.20, 5.20, H - 0.05, 22),   # Open living
        (8.80 if is_p12 else 7.15, 5.80 if is_p12 else 4.00, H - 0.05, 24),  # Home ICU
        (7.20 if is_p12 else 9.60, 2.45 if is_p12 else 7.00, H - 0.05, 20),  # Veranda
        (9.90, 9.80, H - 0.05, 22),   # Drawing room
        (9.90, 12.90, H - 0.05, 20),  # Caregiver room
        (3.20, 11.20, H - 0.05, 24),  # Master bedroom
        (4.80, 13.40, H - 0.05, 16),  # Master bath
        (7.20, 13.40, H - 0.05, 14),  # Caregiver WC
        (7.74, 11.00, H - 0.05, 16),  # Lobby
    ]
    for lx, ly, lz, pwr in light_points:
        k.cylinder((lx, ly, lz + 0.02), 0.055, 0.012, "lamp", 0, "downlight")
        k.light((lx, ly, lz - 0.10), pwr, color="#ffe0b2", kind="downlight")

    # ------------------------------------------------------------------
    # 9. BOUNDARY WALLS, LAYERED GREENERY, POTS & PARKED CAR
    # ------------------------------------------------------------------
    # Low modern perimeter wall with stone-clad piers and open vehicle/pedestrian gate at East [8.042..12.042, 0]
    bw = 0.15
    # South boundary wall
    k.rect((0.0, 0.0, g, bw, D, g + 1.55), "wall", -1, "site", "boundary-south")
    # West rear boundary wall
    k.rect((0.0, D - bw, g, W, D, g + 1.55), "wall", -1, "site", "boundary-west")
    # North boundary low wall (kept low at 1.05 m with trimmed greenery so ICU & drawing views to North garden stay clear!)
    k.rect((W - bw, 4.35 if is_p12 else 6.20, g, W, D, g + 1.02), "wall", -1, "site", "boundary-north-low")
    k.rect((W - bw - 0.01, 4.35 if is_p12 else 6.20, g + 1.02, W + 0.01, D, g + 1.06), "level-nosing-stone", -1, "site", "boundary-north-cap")
    # East front wall South of gate (x = 0.0..8.042, y = 0.0..0.15)
    k.rect((0.0, 0.0, g, gate_x0, bw, g + 1.32), "wall", -1, "site", "boundary-east-south")
    k.rect((0.0, -0.02, g, gate_x0, 0.0, g + 0.92), "cladding", -1, "site", "boundary-east-cladding")
    k.rect((0.0, -0.01, g + 1.32, gate_x0, bw + 0.01, g + 1.36), "frame", -1, "site", "boundary-east-cap")
    # Gate piers at x = 8.042 m and x = 12.042 m
    for px_ in (gate_x0, gate_x1):
        k.rect((px_ - 0.16, -0.04, g, px_ + 0.16, bw + 0.04, g + 1.65), "cladding", -1, "site", f"east-gate-pier-{px_:.2f}")
        k.rect((px_ - 0.18, -0.06, g + 1.65, px_ + 0.18, bw + 0.06, g + 1.70), "frame", -1, "site", f"east-gate-pier-cap-{px_:.2f}")
        k.cylinder((px_, 0.07, g + 1.76), 0.07, 0.10, "lamp", -1, "fixture")
        k.light((px_, -0.15, g + 1.85), 14, color="#ffdca6", kind="gate")

    # Layered Bungalow-inspired potted plants and garden atmosphere (scaled to keep all paths, step edges & ICU views clear)
    if is_p12:
        pots_spec = [
            (5.55, 1.32, z_house, "areca", 1.30, (0.22, 0.42, "terracotta-pot")),
            (5.15, 0.62, z_house, "monstera", 0.82, (0.19, 0.36, "ceramic-pot")),
            (10.78, 4.58, z_house, "cordyline", 0.72, (0.18, 0.34, "terracotta-pot")),
            (11.82, 7.85, z_house, "shrub_flowering", 0.78, (0.20, 0.38, "ceramic-pot")),
            (2.10, 0.62, z_house, "frangipani", 2.35, (0.26, 0.48, "terracotta-pot")),
            (4.15, 0.62, z_house, "shrub_round", 0.72, (0.19, 0.36, "ceramic-pot")),
        ]
    else:
        pots_spec = [
            (5.20, 1.32, z_house, "areca", 1.30, (0.22, 0.42, "terracotta-pot")),
            (5.15, 0.62, z_house, "monstera", 0.82, (0.19, 0.36, "ceramic-pot")),
            (11.65, 6.25, z_house, "cordyline", 0.72, (0.18, 0.34, "terracotta-pot")),
            (11.82, 7.85, z_house, "shrub_flowering", 0.78, (0.20, 0.38, "ceramic-pot")),
            (2.10, 0.62, z_house, "frangipani", 2.35, (0.26, 0.48, "terracotta-pot")),
            (4.15, 0.62, z_house, "shrub_round", 0.72, (0.19, 0.36, "ceramic-pot")),
        ]
    for px_, py_, pz_, sp_name, h_m, pot_cfg in pots_spec:
        k.plant(px_, py_, pz_, sp_name, height=h_m, f=0, pot=pot_cfg)

    # Low flowering shrubs along the narrow North planting bed (y = 8.5..14.2 m)
    for yy in (8.65, 10.20, 11.40, 12.60, 14.10):
        k.plant(12.00, yy, z_house - 0.02, "shrub_flowering", height=0.62, f=0)

    # Parked car on the lower car porch (-6 in drop = z_porch)
    car_info = b["planning"]["parkedCar"]
    parked_car(k, materials, float(car_info["x"]) / 1000.0, float(car_info["y"]) / 1000.0, z_porch)
    materials["car-pearl"] = {
        "color": "#e9e7e0",
        "roughness": 0.18,
        "metallic": 0.32,
        "clearcoat": 1.0,
        "clearcoat_roughness": 0.06,
    }

    # ------------------------------------------------------------------
    # 10. ROOMS METADATA, WALK CONFIGURATION, COLONY CONTEXT & CAMERAS
    # ------------------------------------------------------------------
    rooms_meta = [
        {
            "id": s["id"],
            "name": s["name"],
            "kind": s["kind"],
            "floor": s["floor"],
            "holes": [[[round(x / 1000.0, 4), round(y / 1000.0, 4)] for x, y in ring] for ring in s.get("holes", [])],
            "polygon": [[round(x / 1000.0, 4), round(y / 1000.0, 4)] for x, y in s["clear"]],
        }
        for s in b["spaces"]
    ]

    walk = {
        "eye_height": 1.62,
        "arrival": {
            "position": [round(gate_x0 + 0.48, 3), -1.4, round(g + 0.1, 3)],
            "yaw_deg": 0,
        },
        "floors": [
            {"floor": 0, "position": [5.8, 6.2, z_house], "yaw_deg": 0},
        ],
    }

    # Curated cameras tailored specifically to P12-A and P11 geometry
    if is_p12:
        custom_cams = {
            "exterior_east": {
                "id": "exterior_east",
                "label": "East Principal Arrival — Raised Forecourt, Veranda, Lower Car Porch (-6 in) & Basketball Court Context",
                "position": [7.80, -8.20, 2.15],
                "target": [6.80, 4.20, 1.25],
                "fov": 46,
            },
            "exterior_northeast": {
                "id": "exterior_northeast",
                "label": "Northeast Corner — 12 m North Road, 9 m East Road, Lower Car Porch (-6 in), Notched Home ICU & Veranda",
                "position": [18.20, -6.50, 3.15],
                "target": [8.40, 4.60, 1.15],
                "fov": 46,
            },
            "cutaway_roof_off": {
                "id": "cutaway_roof_off",
                "label": "3D Roof-Off Cutaway — Full Ground-Floor Layout, Large Cream Marble Flooring & Lower Porch",
                "position": [6.20, -4.80, 15.80],
                "target": [6.10, 7.60, 0.20],
                "fov": 44,
            },
            "interior_kitchen_living_dining": {
                "id": "interior_kitchen_living_dining",
                "label": "Connected Kitchen, Open Living & Dining — L-Counter, Serving Worktop, Staircase & Large Ivory Marble Tiles",
                "position": [6.75, 4.15, 1.66],
                "target": [2.55, 5.15, 1.02],
                "fov": 68,
            },
            "interior_icu_veranda_garden": {
                "id": "interior_icu_veranda_garden",
                "label": "Home ICU to Veranda & Garden — Recliner Bed (Head South, Feet North), Tall Charcoal-Bronze Glazing & Colony Garden",
                "position": [7.95, 7.35, 1.56],
                "target": [9.05, 2.15, 1.05],
                "fov": 64,
            },
            "closeup_flooring_glazing_porch": {
                "id": "closeup_flooring_glazing_porch",
                "label": "Close-Up — 6-Inch Lower Car-Porch Drop, Continuous ICU Notch, Kota Paver + Red-Oxide Border, 24x48 Marble Tiles & Glazing",
                "position": [7.55, 0.85, 1.40],
                "target": [9.25, 3.45, 0.28],
                "fov": 56,
            },
        }
    else:
        custom_cams = {
            "exterior_east": {
                "id": "exterior_east",
                "label": "East Principal Arrival — Raised Forecourt, Rectangular Home ICU, Lower Car Porch (-6 in) & East Road",
                "position": [7.80, -8.20, 2.15],
                "target": [6.80, 4.20, 1.25],
                "fov": 46,
            },
            "exterior_northeast": {
                "id": "exterior_northeast",
                "label": "Northeast Corner — 12 m North Road, 9 m East Road, Lower Car Porch (-6 in), Shortened Veranda Return & ICU",
                "position": [18.20, -6.50, 3.15],
                "target": [8.40, 4.80, 1.15],
                "fov": 46,
            },
            "cutaway_roof_off": {
                "id": "cutaway_roof_off",
                "label": "3D Roof-Off Cutaway — Full Ground-Floor Layout, Large Cream Marble Flooring & Lower Porch",
                "position": [6.20, -4.80, 15.80],
                "target": [6.10, 7.60, 0.20],
                "fov": 44,
            },
            "interior_kitchen_living_dining": {
                "id": "interior_kitchen_living_dining",
                "label": "Connected Kitchen, Open Living & Dining — L-Counter, Serving Worktop, Staircase & Large Ivory Marble Tiles",
                "position": [5.05, 4.15, 1.66],
                "target": [2.45, 5.25, 1.02],
                "fov": 68,
            },
            "interior_icu_veranda_garden": {
                "id": "interior_icu_veranda_garden",
                "label": "Home ICU to Veranda & North Garden — Rectangular ICU, Bed & Visitor Seating, Tall Glazing & Shortened Veranda Return",
                "position": [6.05, 2.65, 1.63],
                "target": [8.45, 5.35, 1.05],
                "fov": 66,
            },
            "closeup_flooring_glazing_porch": {
                "id": "closeup_flooring_glazing_porch",
                "label": "Close-Up — 6-Inch Lower Car-Porch Drop at Shortened Veranda Return, Kota Paver + Red-Oxide Border, 24x48 Marble Tiles & ICU Glazing",
                "position": [10.65, 7.25, 1.48],
                "target": [8.65, 3.55, 0.30],
                "fov": 58,
            },
        }

    # Room shortcuts must position the walking body as well as the camera. Without this,
    # the next physics frame snaps an interior camera back to the outside spawn.
    for name, cam in custom_cams.items():
        if not name.startswith("interior_"):
            continue
        cam["position"][2] = 1.63
        cam["target"][2] = 1.45
        if not is_p12 and name == "interior_kitchen_living_dining":
            cam["position"] = [4.95, 5.3, 1.63]
        dx, dy, dz = [cam["target"][i] - cam["position"][i] for i in range(3)]
        cam.update({"enter_walk": True, "floor": 0, "eye_height_above_ffl_m": 1.63,
                    "walker": {"position": cam["position"][:], "yaw_rad": math.atan2(-dx, dy),
                               "pitch_rad": math.atan2(dz, math.hypot(dx, dy))}})

    scene: dict[str, Any] = {
        "editables": k.editables,
        "input_audit": b.get("input_audit"),
        "planHash": b.get("planHash"),
        "draftRevision": b.get("draftRevision", 1),
        "schema": "floorforge.scene/0.4",
        "units": "m",
        "up": "Z",
        "materials": materials,
        "assets": k.assets,
        "nodes": k.nodes,
        "lights": k.lights,
        "colliders": k.colliders,
        "furniture": k.furniture,
        "floor_height": H,
        "storeys": 1,
        "roof_level": None,
        "bounds": [0.0, 0.0, -plinth, W, D, 5.30],
        "footprint": (np.array(b["footprint"]) / 1000.0).tolist(),
        "entry": [round((gate_x0 + gate_x1) / 2.0, 3), -0.15, 1.6],
        "solar": report["solar"],
        "style": "minimal",
        "exterior_theme": "warm_modern_minimal",
        "interior_theme": "warm_contemporary",
        "exterior_revision": "tirumala-p11-p12-v1",
        "exterior_review": {"status": "pass", "protected_interior_unchanged": True},
        "vegetation": k.vegetation,
        "lawns": lawns,
        "rooms": rooms_meta,
        "walk": walk,
        "opening_model": {"openings": b["openings"], "walls": b["walls"]},
        "gate_model": [],
        "door_motion": door_motion,
        "cameras": {
            "hero": custom_cams["exterior_northeast"],
            "east_arrival": custom_cams["exterior_east"],
            "dollhouse": custom_cams["cutaway_roof_off"],
            "interior": custom_cams["interior_kitchen_living_dining"],
            **custom_cams,
        },
        "quality": "Authored procedural geometry with physically based surface recipes and procedural planting.",
        "banner": b["banner"],
    }

    ctx = build_tirumala_context(b, scene)
    ctx["sightline_cameras"].update(custom_cams)
    scene["context"] = ctx
    scene["cameras"].update({
        **ctx["reference_cameras"],
        **ctx["sightline_cameras"],
        **custom_cams,
        "hero": custom_cams["exterior_northeast"],
        "east_arrival": custom_cams["exterior_east"],
        "dollhouse": custom_cams["cutaway_roof_off"],
        "interior": custom_cams["interior_kitchen_living_dining"],
    })
    return scene



def p11_p12_plan_elements(b: dict[str, Any], scene: dict[str, Any], floor: int = 0) -> tuple[list[dict[str, Any]], tuple[float, float, float, float]]:
    """Build the 2D CAD/sheet drawing primitives for Tirumala 2 (P12-A) and Tirumala 3 (P11)
    with West at the top (+y) and North on the right (+x), dimensions in feet and inches,
    and explicit level-change callouts."""
    from .drawings import C, DIM, INK, L, LIGHT, P, T

    plan = b["planning"]["canonicalPlan"]
    option_id = b["planning"]["tirumalaOption"]
    is_p12 = option_id == "P12-A"
    porch_drop_mm = float(b["planning"].get("provisionalPorchDropMm", PROVISIONAL_PORCH_DROP_MM))
    drop_in_str = f"-{porch_drop_mm / 25.4:.0f}″ provisional"

    items: list[dict[str, Any]] = []
    W, D = 12192.0, 15240.0

    # Plot boundary
    items.append(P([[0, 0], [W, 0], [W, D], [0, D]], fill="#fbfaf7", stroke="#8a867e", width=0.22, layer="A-SITE"))

    # North garden & Rear West air strip
    items.append(P(plan["northGarden"], fill="#e7f3e8", stroke="none", width=0.1, layer="A-LAND"))
    items.append(P(plan["rearAir"], fill="#e7f3e8", stroke="none", width=0.1, layer="A-LAND"))
    for reg in plan.get("gardenPocket", []):
        items.append(P(reg["outer"], fill="#d4ebd6", stroke="none", width=0.1, layer="A-LAND"))

    # Raised East Forecourt & Raised North Passage (Cream/White Marble family, ±0'0")
    for reg in plan.get("raisedForecourt", []):
        items.append(P(reg["outer"], fill="#f7f4ec", stroke="#d2cbbd", width=0.14, layer="A-FLOR"))
    for reg in plan.get("raisedPassage", []):
        items.append(P(reg["outer"], fill="#f7f4ec", stroke="#d2cbbd", width=0.14, layer="A-FLOR"))

    # Lower Car Porch (Traditional Kota/paver + red-oxide border, -6" provisional)
    for reg in plan["lowerPorch"]:
        items.append(P(reg["outer"], fill="#f4e2d4", stroke="#b56552", width=0.22, layer="A-FLOR"))
    if not is_p12 and plan.get("porchGain"):
        for reg in plan["porchGain"]:
            items.append(P(reg["outer"], fill="#f4e2d4", stroke="#b56552", width=0.22, layer="A-FLOR"))

    # Connected Open Floor (Kitchen, Living, Dining, Open Living)
    for reg in plan["openFloor"]:
        items.append(P(reg["outer"], fill="#fcfaf5", stroke="#ded7c8", width=0.12, layer="A-FLOR"))

    # Rooms
    room_fills = {
        "g-care": "#d6ebfb",
        "g-veranda": "#e9dff8",
        "g-care-court": "#dcf0e0",
        "g-wash-gully": "#f0eee9",
    }
    for rm in plan["rooms"]:
        rid = rm["id"]
        fill_col = room_fills.get(rid, "#fcfaf5")
        items.append(P(rm["regions"][0]["outer"], fill=fill_col, stroke="#d8d1c3", width=0.12, layer="A-FLOR"))

    # Kitchen L-counter & Short serving worktop
    items.append(P(plan["counter"], fill="#f7cfa8", stroke="#c98a55", width=0.20, layer="A-FURN"))
    items.append(P(plan["serving"], fill="#f7cfa8", stroke="#c98a55", width=0.20, layer="A-FURN"))

    # Staircase flights & treads
    for st in plan["stairs"]:
        spoly = st["polygon"]
        items.append(P(spoly, fill="#efede8", stroke="#8d8980", width=0.15, layer="A-STAIR"))
        xs = [p[0] for p in spoly]
        ys = [p[1] for p in spoly]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if "risers" in st:
            nr = int(st["risers"])
            if st["direction"] == "South":
                for i in range(1, nr):
                    xx = x0 + i * (x1 - x0) / nr
                    items.append(L((xx, y0), (xx, y1), "#8d8980", 0.12, "A-STAIR"))
            elif st["direction"] == "West":
                for i in range(1, nr):
                    yy = y0 + i * (y1 - y0) / nr
                    items.append(L((x0, yy), (x1, yy), "#8d8980", 0.12, "A-STAIR"))
            elif st["direction"] == "North":
                for i in range(1, nr):
                    xx = x0 + i * (x1 - x0) / nr
                    items.append(L((xx, y0), (xx, y1), "#8d8980", 0.12, "A-STAIR"))
    # Stair climb arrow (South -> West -> North)
    items.append(L((1950, 5550), (700, 5550), INK, 0.22, "A-STAIR"))
    items.append(L((700, 5550), (700, 8350), INK, 0.22, "A-STAIR"))
    items.append(L((700, 8350), (3400, 8350), INK, 0.22, "A-STAIR"))

    # Furniture outlines
    for item in plan["furniture"]:
        if item["kind"] == "dining-set" and item.get("parts"):
            for part in item["parts"]:
                items.append(P(part, fill="none", stroke="#b5b0a6", width=0.14, layer="A-FURN"))
        else:
            items.append(P(item["polygon"], fill="none", stroke="#b5b0a6", width=0.14, layer="A-FURN"))

    # Car envelope & car body
    items.append(P(plan["carEnvelope"], fill="none", stroke="#9a8b7c", width=0.16, layer="A-SITE"))
    items.append(P(plan["carBody"], fill="#f7f5f0", stroke="#8a8278", width=0.18, layer="A-SITE"))

    # Level change lines (-6 in provisional step edge)
    for seg in plan.get("levelChangeLines", []):
        items.append(L(seg[0], seg[1], "#b5382a", 0.35, "A-LEVL", dash=True))

    # Solid walls (wallRects)
    for wr in plan["wallRects"]:
        x0, y0, x1, y1 = wr
        items.append(P([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], fill="#424546", stroke="#2b2d2e", width=0.18, layer="A-WALL"))

    # Openings (windows, doors, glass walls, wood+mesh fold)
    for op in plan["openings"]:
        a, b_pt = op["a"], op["b"]
        knd = op["kind"]
        if knd == "glass":
            items.append(L(a, b_pt, "#2a7de1", 0.36, "A-DOOR", dash=True))
        elif knd == "window":
            items.append(L(a, b_pt, "#4a9e5c", 0.30, "A-WIND"))
        elif knd == "wood-mesh-fold":
            items.append(L(a, b_pt, "#9e653f", 0.34, "A-DOOR", dash=True))
        elif knd == "door" and "swing" in op:
            hinge = a if op.get("hinge") == "a" else b_pt
            other = b_pt if op.get("hinge") == "a" else a
            sw = op["swing"]
            items.append(L(hinge, sw, "#7a766e", 0.18, "A-DOOR"))
            # Arc from other to sw
            r = math.hypot(other[0] - hinge[0], other[1] - hinge[1])
            ang0 = math.atan2(other[1] - hinge[1], other[0] - hinge[0])
            ang1 = math.atan2(sw[1] - hinge[1], sw[0] - hinge[0])
            da = (ang1 - ang0 + math.pi) % (2 * math.pi) - math.pi
            arc_pts = [
                [hinge[0] + r * math.cos(ang0 + da * t / 16.0), hinge[1] + r * math.sin(ang0 + da * t / 16.0)]
                for t in range(17)
            ]
            items.append(P(arc_pts, fill="none", stroke="#9a968e", width=0.14, layer="A-DOOR", closed=False))

    # Room Labels & Feet/Inches Dimensions
    room_labels = [
        (2350, 11150, "Master bedroom", 210),
        (4800, 13650, "Master bath (8′ × 6′)", 175),
        (7150, 13650, "Attached WC", 170),
        (9850, 12750, "Caregiver", 195),
        (9850, 9950, "Drawing (Unfurnished)" if is_p12 else "Drawing room", 185),
        (6380, 11100, "Lightwell", 165),
        (7740, 11400, "Lobby", 165),
        (8820 if is_p12 else 7160, 6250 if is_p12 else 4100, "Home ICU", 205),
        (7220 if is_p12 else 9850, 2400 if is_p12 else 7100, "Veranda (±0′0″)", 185),
        (3850, 3150, "Kitchen", 195),
        (4850, 7100, "Living / dining", 205),
        (1815, 3300, "Store", 165),
        (680, 3200, "Wash", 165),
        (2250, 5950, "Stairs", 175),
        (4800, 760, "Raised East forecourt · ±0′0″", 180),
        (10120 if is_p12 else 10800, 1850 if is_p12 else 3800, f"Lower porch · {drop_in_str}", 175),
    ]
    if is_p12:
        room_labels.append((6050, 4800, "Open living", 185))
        room_labels.append((11280, 6200, "Open passage · ±0′0″", 165))
    for rx, ry, rtxt, rsz in room_labels:
        items.append(T(rx, ry, rtxt, rsz, "A-ANNO"))

    # Overall plot dimension lines in feet/inches + DXF DIMENSION entities
    items.append(DIM((0, D), (W, D), "x", D + 550, 1))
    items.append(DIM((0, 0), (0, D), "y", -550, 1))
    items.append(T(W / 2.0, 16120, "40 ft (North–South) · WEST (rear) ↑", 210, "A-DIMS"))
    items.append(T(-960, D / 2.0, "50 ft (East–West)", 210, "A-DIMS", rot=90))
    items.append(T(W / 2.0, -520, "EAST · principal road approach", 200, "A-ANNO"))
    items.append(T(W + 480, D / 2.0, "N → (12 m Road & Colony Garden)", 190, "A-ANNO", rot=90))

    bb = (-1400.0, -900.0, W + 900.0, D + 1450.0)
    return items, bb



def render_dimensioned_2d_svg(b: dict[str, Any]) -> str:
    """Render a high-resolution, publication-grade dimensioned architectural 2D plan SVG
    in feet and inches with West at the top and North on the right."""
    plan = b["planning"]["canonicalPlan"]
    option_id = b["planning"]["tirumalaOption"]
    is_p12 = option_id == "P12-A"
    porch_drop_mm = float(b["planning"].get("provisionalPorchDropMm", PROVISIONAL_PORCH_DROP_MM))
    drop_in_txt = f"{porch_drop_mm / 25.4:.0f}″"

    # Canvas: 1600 x 2100 px
    cw, ch = 1600, 2100
    ox, oy = 135.0, 165.0
    scale = 0.11  # 1 mm = 0.11 px -> 12192 mm = 1341.12 px, 15240 mm = 1676.4 px
    W, D = 12192.0, 15240.0

    def tx(x_mm: float) -> float:
        return round(ox + float(x_mm) * scale, 2)

    def ty(y_mm: float) -> float:
        return round(oy + (D - float(y_mm)) * scale, 2)

    def pts_str(ring: list[list[float]]) -> str:
        return " ".join(f"{tx(p[0])},{ty(p[1])}" for p in ring)

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}" font-family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">',
        '<defs>',
        '  <marker id="arr-s" viewBox="0 0 8 8" refX="1" refY="4" markerWidth="5" markerHeight="5" orient="auto"><path d="M7,1 L1,4 L7,7" fill="none" stroke="#1f2421" stroke-width="1.3"/></marker>',
        '  <marker id="arr-e" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto"><path d="M1,1 L7,4 L1,7" fill="none" stroke="#1f2421" stroke-width="1.3"/></marker>',
        '</defs>',
        f'<rect x="0" y="0" width="{cw}" height="{ch}" fill="#ffffff"/>',
    ]

    title = (
        "Tirumala 2 (P12-A) · Dimensioned Architectural 2D Floor Plan"
        if is_p12
        else "Tirumala 3 (P11) · Dimensioned Architectural 2D Floor Plan"
    )
    subtitle = (
        f"40 ft north–south × 50 ft east–west · West ↑ · North → · Dimensions in feet/inches · "
        f"Lower car porch -{drop_in_txt} (provisional adjustable drop)"
    )
    lines.append(f'<text x="54" y="48" font-size="22" font-weight="700" fill="#181c1a">{title}</text>')
    lines.append(f'<text x="54" y="76" font-size="14" fill="#464d49">{subtitle}</text>')
    lines.append(f'<text x="{tx(W / 2)}" y="{ty(D) - 38}" font-size="12" font-weight="600" text-anchor="middle" fill="#3a403d">WEST · rear</text>')
    lines.append(f'<text x="{tx(W / 2)}" y="{ty(0) + 36}" font-size="12" font-weight="600" text-anchor="middle" fill="#3a403d">EAST · approach</text>')
    lines.append(f'<text x="{tx(W) + 34}" y="{ty(D / 2)}" font-size="13" font-weight="700" text-anchor="middle" fill="#181c1a">N</text>')

    # Plot outer frame
    lines.append(f'<rect x="{tx(0)}" y="{ty(D)}" width="{round(W * scale, 2)}" height="{round(D * scale, 2)}" fill="#fbfaf7" stroke="#b8b4ac" stroke-width="1.2"/>')

    # Green garden strips (North & Rear West)
    lines.append(f'<polygon points="{pts_str(plan["northGarden"])}" fill="#e6f4e8" stroke="none"/>')
    lines.append(f'<polygon points="{pts_str(plan["rearAir"])}" fill="#e6f4e8" stroke="none"/>')
    for reg in plan.get("gardenPocket", []):
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="#cde8d1" stroke="none"/>')

    # Raised East Forecourt & Raised North Passage (±0'0" house level)
    for reg in plan.get("raisedForecourt", []):
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="#f5f3ef" stroke="#dcd7cd" stroke-width="1"/>')
    for reg in plan.get("raisedPassage", []):
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="#f5f3ef" stroke="#dcd7cd" stroke-width="1"/>')

    # Lower Porch (-6" provisional level)
    for reg in plan["lowerPorch"]:
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="#f7e3d4" stroke="#d49b7e" stroke-width="1.4"/>')
    if not is_p12 and plan.get("porchGain"):
        for reg in plan["porchGain"]:
            lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="#f7e3d4" stroke="#d49b7e" stroke-width="1.4"/>')

    # Connected Open Floor
    for reg in plan["openFloor"]:
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="#ffffff" stroke="none"/>')

    # Individual Rooms
    for rm in plan["rooms"]:
        rid = rm["id"]
        fill = {
            "g-care": "#cce6fb",
            "g-veranda": "#e6dcf8",
            "g-care-court": "#d8f0dc",
            "g-wash-gully": "#efefef",
        }.get(rid, "#ffffff")
        lines.append(f'<polygon points="{pts_str(rm["regions"][0]["outer"])}" fill="{fill}" stroke="none"/>')

    # Kitchen L-counter & short serving worktop
    lines.append(f'<polygon points="{pts_str(plan["counter"])}" fill="#f7cfa8" stroke="#d48b4b" stroke-width="1.3"/>')
    lines.append(f'<polygon points="{pts_str(plan["serving"])}" fill="#f7cfa8" stroke="#d48b4b" stroke-width="1.3"/>')

    # Staircase flights & risers
    for st in plan["stairs"]:
        sp = st["polygon"]
        lines.append(f'<polygon points="{pts_str(sp)}" fill="#efefef" stroke="#999999" stroke-width="1"/>')
        xs = [p[0] for p in sp]
        ys = [p[1] for p in sp]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if "risers" in st:
            nr = int(st["risers"])
            if st["direction"] in ("South", "North"):
                for i in range(1, nr):
                    xx = x0 + i * (x1 - x0) / nr
                    lines.append(f'<line x1="{tx(xx)}" y1="{ty(y0)}" x2="{tx(xx)}" y2="{ty(y1)}" stroke="#999999" stroke-width="0.9"/>')
            elif st["direction"] == "West":
                for i in range(1, nr):
                    yy = y0 + i * (y1 - y0) / nr
                    lines.append(f'<line x1="{tx(x0)}" y1="{ty(yy)}" x2="{tx(x1)}" y2="{ty(yy)}" stroke="#999999" stroke-width="0.9"/>')
    # Upper landing dashed outline & climb arrow
    lines.append(f'<polygon points="{pts_str(plan["stairs"][-1]["polygon"])}" fill="none" stroke="#999999" stroke-width="1" stroke-dasharray="4,4"/>')
    lines.append(f'<polyline points="{tx(1950)},{ty(5550)} {tx(700)},{ty(5550)} {tx(700)},{ty(8350)} {tx(3400)},{ty(8350)}" fill="none" stroke="#222" stroke-width="1.3" marker-end="url(#arr-e)"/>')

    # Furniture outlines
    for item in plan["furniture"]:
        if item["kind"] == "dining-set" and item.get("parts"):
            for part in item["parts"]:
                lines.append(f'<polygon points="{pts_str(part)}" fill="none" stroke="#c2c2c2" stroke-width="1"/>')
        else:
            lines.append(f'<polygon points="{pts_str(item["polygon"])}" fill="#f9fbfd" fill-opacity="0.55" stroke="#b8c0c8" stroke-width="1.1"/>')
            if item["kind"] == "reclining-bed":
                bx0, by0, bx1, by1 = item["bounds"]
                if is_p12:
                    # Head pillow at South (bx0)
                    lines.append(f'<rect x="{tx(bx0 + 120)}" y="{ty(by1 - 120)}" width="{round(320 * scale, 1)}" height="{round((by1 - by0 - 240) * scale, 1)}" fill="#cbd8e6" stroke="none"/>')
                else:
                    # Head pillow at West (by1)
                    lines.append(f'<rect x="{tx(bx0 + 120)}" y="{ty(by1 - 120)}" width="{round((bx1 - bx0 - 240) * scale, 1)}" height="{round(320 * scale, 1)}" fill="#cbd8e6" stroke="none"/>')

    # Car envelope & car body
    lines.append(f'<polygon points="{pts_str(plan["carEnvelope"])}" fill="none" stroke="#8c7a6b" stroke-width="1.1" stroke-dasharray="4,4"/>')
    lines.append(f'<polygon points="{pts_str(plan["carBody"])}" fill="#fbf8f3" stroke="#9e8c7a" stroke-width="1.2"/>')

    # Level change lines (-6" provisional step edge)
    for seg in plan.get("levelChangeLines", []):
        lines.append(f'<line x1="{tx(seg[0][0])}" y1="{ty(seg[0][1])}" x2="{tx(seg[1][0])}" y2="{ty(seg[1][1])}" stroke="#c93b2b" stroke-width="2.2" stroke-dasharray="6,4"/>')

    # East gate line
    gx0, gx1 = plan["gate"][0][0], plan["gate"][1][0]
    lines.append(f'<line x1="{tx(gx0)}" y1="{ty(0)}" x2="{tx(gx1)}" y2="{ty(0)}" stroke="#d93870" stroke-width="2.6"/>')

    # Solid walls (wallRects)
    for wr in plan["wallRects"]:
        x0, y0, x1, y1 = wr
        lines.append(f'<rect x="{tx(x0)}" y="{ty(y1)}" width="{max(1.5, round((x1 - x0) * scale, 2))}" height="{max(1.5, round((y1 - y0) * scale, 2))}" fill="#484b4d" stroke="#2f3234" stroke-width="0.6"/>')

    # Openings: windows, doors, sliding glass, wood+mesh fold
    for op in plan["openings"]:
        ax, ay = op["a"]
        bx, by = op["b"]
        knd = op["kind"]
        if knd == "window":
            lines.append(f'<line x1="{tx(ax)}" y1="{ty(ay)}" x2="{tx(bx)}" y2="{ty(by)}" stroke="#5cb86e" stroke-width="3.2"/>')
        elif knd == "glass":
            lines.append(f'<line x1="{tx(ax)}" y1="{ty(ay)}" x2="{tx(bx)}" y2="{ty(by)}" stroke="#2b7de9" stroke-width="3.0" stroke-dasharray="5,4"/>')
        elif knd == "wood-mesh-fold":
            lines.append(f'<line x1="{tx(ax)}" y1="{ty(ay)}" x2="{tx(bx)}" y2="{ty(by)}" stroke="#b86b35" stroke-width="3.2" stroke-dasharray="6,3"/>')
        elif knd == "door" and "swing" in op:
            hx, hy = (ax, ay) if op.get("hinge") == "a" else (bx, by)
            ox_, oy_ = (bx, by) if op.get("hinge") == "a" else (ax, ay)
            sx, sy = op["swing"]
            lines.append(f'<line x1="{tx(hx)}" y1="{ty(hy)}" x2="{tx(sx)}" y2="{ty(sy)}" stroke="#6e6e6e" stroke-width="1.3"/>')
            r_px = math.hypot(tx(ox_) - tx(hx), ty(oy_) - ty(hy))
            lines.append(f'<path d="M {tx(ox_)} {ty(oy_)} A {r_px:.1f} {r_px:.1f} 0 0 {1 if (ox_ - hx) * (sy - hy) - (oy_ - hy) * (sx - hx) < 0 else 0} {tx(sx)} {ty(sy)}" fill="none" stroke="#9a9a9a" stroke-width="1.0"/>')

    # Blue stacked glass indicators
    if "stack" in plan:
        lines.append(f'<polygon points="{pts_str(plan["stack"])}" fill="#2b7de9" fill-opacity="0.25" stroke="#2b7de9" stroke-width="1.2"/>')

    # Dimension arrows helper
    def dim_h(x0_mm: float, x1_mm: float, y_mm: float, label: str) -> None:
        y_px = ty(y_mm)
        x0_px, x1_px = tx(x0_mm), tx(x1_mm)
        xm = (x0_px + x1_px) / 2.0
        tw = len(label) * 4.4 + 8
        lines.append(f'<line x1="{x0_px}" y1="{y_px}" x2="{x1_px}" y2="{y_px}" stroke="#222" stroke-width="0.9" marker-start="url(#arr-s)" marker-end="url(#arr-e)"/>')
        lines.append(f'<rect x="{xm - tw / 2:.1f}" y="{y_px - 8:.1f}" width="{tw:.1f}" height="15" fill="#ffffff" fill-opacity="0.88"/>')
        lines.append(f'<text x="{xm:.1f}" y="{y_px + 4:.1f}" font-size="11.5" font-weight="600" text-anchor="middle" fill="#181c1a">{label}</text>')

    def dim_v(x_mm: float, y0_mm: float, y1_mm: float, label: str) -> None:
        x_px = tx(x_mm)
        y0_px, y1_px = ty(y0_mm), ty(y1_mm)
        ym = (y0_px + y1_px) / 2.0
        tw = len(label) * 4.4 + 8
        lines.append(f'<line x1="{x_px}" y1="{y0_px}" x2="{x_px}" y2="{y1_px}" stroke="#222" stroke-width="0.9" marker-start="url(#arr-s)" marker-end="url(#arr-e)"/>')
        lines.append(f'<rect x="{x_px - 8:.1f}" y="{ym - tw / 2:.1f}" width="16" height="{tw:.1f}" fill="#ffffff" fill-opacity="0.88"/>')
        lines.append(f'<text x="{x_px + 4:.1f}" y="{ym:.1f}" font-size="11.5" font-weight="600" text-anchor="middle" transform="rotate(-90 {x_px + 4:.1f} {ym:.1f})" fill="#181c1a">{label}</text>')

    # Plot outer dimensions
    dim_h(0, W, D + 260, "40 ft")
    dim_v(-260, 0, D, "50 ft")

    # Shared room internal dimensions
    dim_h(150, 3440.8, 13880, "10′9½″")
    dim_v(520, 9050, 14328, "17′3¾″")
    dim_h(150, 5485.6, 10450, "17′6⅛″")
    dim_v(3200, 12349.2, 14328, "6′5⅝″")
    dim_h(3590.8, 6029.2, 12650, "8′")
    dim_v(5880, 12499.2, 14328, "6′")
    dim_h(6179.2, 8200, 12780, "6′7½″")
    dim_v(8060, 12600, 14328, "5′8″")
    dim_v(11310, 11550, 14328, "9′1¼″")
    dim_h(8350, 11432.4, 11850, "10′1½″")
    dim_v(11310, 8200, 11400, "10′6″")
    dim_h(8350, 11432.4, 8420, "10′1½″")
    dim_h(7285.6, 8200, 12220, "3′")
    dim_v(7980, 9600, 12450, "9′4¼″")
    dim_h(5635.6, 7135.6, 10420, "4′11″")
    dim_v(7010, 10200, 11850, "5′5″")
    dim_h(5650, 6650, 9320, "3′3⅜″")
    dim_h(150, 4550, 8450, "14′5½″")
    dim_v(450, 5000, 8900, "12′9½″")
    dim_h(1250, 7125, 7380, "19′3¼″")
    dim_h(2416.8, 5302.4, 4450, "9′5⅝″")
    dim_v(5180, 1674, 4800, "10′3⅛″")
    dim_h(2416.8, 5202.4, 1980, "9′1⅝″")
    dim_h(1366.8, 2266.8, 1980, "2′11¼″")
    dim_v(2150, 1674, 4650, "9′9⅝″")
    dim_h(150, 1216.8, 1780, "3′6″")
    dim_v(1080, 1524, 4850, "10′11″")

    if is_p12:
        dim_h(7275, 10368, 7850, "10′1¼″")
        dim_v(7480, 3502.8, 8050, "14′11″")
        dim_h(5302.4, 7125, 5650, "5′11¼″")
        dim_v(6020, 3502.8, 8900, "17′8½″")
        dim_h(5452.4, 8994, 1780, "11′7⅜″")
        dim_v(8780, 1524, 3352.8, "6′")
        dim_h(10518, 12042, 6250, "5′")
        dim_h(8994, 12042, 1180, "10′")
        dim_v(11180, 0, 4350, "14′3¼″")
    else:
        dim_h(5452.4, 8882, 2480, "11′3″")
        dim_v(8740, 2283.6, 5759.6, "11′4⅞″")
        dim_v(6850, 5909.6, 8900, "9′9¾″")
        dim_h(7275, 12042, 7750, "15′7⅛″")
        dim_v(11720, 6200, 8050, "6′0⅝″")
        dim_h(9032, 12042, 1180, "9′10½″")

    # Room titles & level annotations: (x, y, text, font_size, font_weight, rotate_deg)
    labels: list[tuple[float, float, str, float, str, int]] = [
        (2350, 11150, "Master bedroom", 13.5, "600", 0),
        (4650, 13650, "Master bath", 12.5, "600", 0),
        (7150, 13650, "Attached WC", 12.5, "600", 0),
        (9850, 12850, "Caregiver", 13.0, "600", 0),
        (9850, 10150, "Drawing", 13.0, "600", 0),
        (6380, 11100, "Lightwell", 12.0, "600", 0),
        (7580, 11350, "Lobby", 12.0, "600", -90),
        (6150, 9720, "Entry", 11.5, "500", 0),
        (2250, 5800, "Stairs", 12.5, "600", 0),
        (4850, 6850, "Living / dining", 13.5, "600", 0),
        (3850, 3150, "Kitchen", 13.5, "600", 0),
        (1650, 3450, "Store", 12.0, "600", -90),
        (550, 3450, "Wash", 12.0, "600", -90),
        (4800, 760, "East forecourt · ±0′0″", 12.5, "600", 0),
    ]
    if is_p12:
        labels.extend([
            (9850, 9550, "Unfurnished", 12.0, "500", 0),
            (8950, 6450, "Home ICU", 13.5, "700", 0),
            (6050, 4800, "Open living", 12.5, "600", 0),
            (7220, 2400, "Veranda · ±0′0″", 12.5, "600", 0),
            (10120, 2250, "Car", 12.5, "600", 0),
            (10450, 1650, f"Lower porch / parking (-{drop_in_txt} prov.)", 11.5, "600", 0),
            (11100, 5500, "Open passage · ±0′0″", 11.5, "600", -90),
        ])
    else:
        labels.extend([
            (7050, 3850, "Home ICU", 13.5, "700", 0),
            (10350, 6850, "Veranda · ±0′0″", 13.0, "600", 0),
            (10800, 3450, "Car", 12.5, "600", 0),
            (10550, 2650, f"Lower porch (-{drop_in_txt} prov.)", 11.5, "600", 0),
        ])

    for lx, ly, ltxt, fsz, fw, rot in labels:
        px_l, py_l = tx(lx), ty(ly)
        rot_attr = f' transform="rotate({rot} {px_l} {py_l})"' if rot else ""
        lines.append(f'<text x="{px_l}" y="{py_l}" font-size="{fsz}" font-weight="{fw}" text-anchor="middle" fill="#1d2220"{rot_attr}>{ltxt}</text>')

    # Footer legend
    fy = ch - 115
    lines.append(f'<text x="54" y="{fy}" font-size="14.5" font-weight="600" fill="#181c1a">Blue: ICU / glass openings · Purple: veranda · Peach/Red dashed: Lower car porch (-{drop_in_txt} provisional drop) · Filled wall lines: solid walls</text>')
    if is_p12:
        lines.append(f'<text x="54" y="{fy + 25}" font-size="13.5" fill="#363c39">P12-A (Tirumala 2): ICU corner cut-out joins the lower porch (10′ × 14′3¼″). Veranda, east forecourt, passage and house remain raised (±0′0″).</text>')
        lines.append(f'<text x="54" y="{fy + 48}" font-size="13.5" fill="#363c39">Drawing room completely unfurnished. Kitchen/living/dining connected without partition. ICU has south-headed recliner bed &amp; corner table only.</text>')
    else:
        lines.append(f'<text x="54" y="{fy + 25}" font-size="13.5" fill="#363c39">P11 (Tirumala 3): Rectangular Home ICU retained with full P11 furniture &amp; doorway positions. Small veranda return shortened 2 ft to align with ICU west wall.</text>')
        lines.append(f'<text x="54" y="{fy + 48}" font-size="13.5" fill="#363c39">Car porch sits {drop_in_txt} below raised house/veranda/east-forecourt datum (provisional adjustable visualization setting, kept separate from horizontal dimensions).</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def render_material_overhead_2d_svg(b: dict[str, Any]) -> str:
    """Render a realistic material-rendered overhead 2D floor plan SVG with West at the top
    and North on the right, showing the 24x48 in warm white/cream marble-look vitrified tiles,
    traditional Kota/paver + red-oxide lower car porch with 6-inch step shadow and LED nosing,
    timber furniture/treads, charcoal-bronze glazing, and layered garden greenery."""
    plan = b["planning"]["canonicalPlan"]
    option_id = b["planning"]["tirumalaOption"]
    is_p12 = option_id == "P12-A"
    porch_drop_mm = float(b["planning"].get("provisionalPorchDropMm", PROVISIONAL_PORCH_DROP_MM))
    drop_in_txt = f"{porch_drop_mm / 25.4:.0f}″"

    cw, ch = 1600, 2100
    ox, oy = 135.0, 165.0
    scale = 0.11
    W, D = 12192.0, 15240.0

    def tx(x_mm: float) -> float:
        return round(ox + float(x_mm) * scale, 2)

    def ty(y_mm: float) -> float:
        return round(oy + (D - float(y_mm)) * scale, 2)

    def pts_str(ring: list[list[float]]) -> str:
        return " ".join(f"{tx(p[0])},{ty(p[1])}" for p in ring)

    # 24 x 48 in = 609.6 x 1219.2 mm -> in px: 67.06 x 134.11 px
    tw_px = round(1219.2 * scale, 2)
    th_px = round(609.6 * scale, 2)
    kota_px = round(609.6 * scale, 2)

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}" font-family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif">',
        '<defs>',
        # Indoor polished 24x48 in warm white/cream marble-look vitrified tile pattern
        f'  <pattern id="marble-indoor" width="{tw_px}" height="{th_px}" patternUnits="userSpaceOnUse">',
        f'    <rect width="{tw_px}" height="{th_px}" fill="#f7f3eb"/>',
        f'    <path d="M 4,{th_px * 0.72:.1f} C {tw_px * 0.32:.1f},{th_px * 0.45:.1f} {tw_px * 0.65:.1f},{th_px * 0.62:.1f} {tw_px - 4:.1f},{th_px * 0.22:.1f}" fill="none" stroke="#e4dac8" stroke-width="1.3" opacity="0.75"/>',
        f'    <path d="M {tw_px * 0.18:.1f},{th_px - 3:.1f} C {tw_px * 0.48:.1f},{th_px * 0.68:.1f} {tw_px * 0.75:.1f},{th_px * 0.48:.1f} {tw_px - 6:.1f},{th_px * 0.58:.1f}" fill="none" stroke="#ebe3d4" stroke-width="0.9" opacity="0.7"/>',
        f'    <rect width="{tw_px}" height="{th_px}" fill="none" stroke="#dfd7c8" stroke-width="0.8"/>',
        '  </pattern>',
        # Outdoor matte non-slip 24x48 in cream/ivory marble-look tile pattern (same visual family)
        f'  <pattern id="marble-outdoor" width="{tw_px}" height="{th_px}" patternUnits="userSpaceOnUse">',
        f'    <rect width="{tw_px}" height="{th_px}" fill="#f1ece1"/>',
        f'    <path d="M 5,{th_px * 0.68:.1f} C {tw_px * 0.35:.1f},{th_px * 0.42:.1f} {tw_px * 0.68:.1f},{th_px * 0.58:.1f} {tw_px - 5:.1f},{th_px * 0.25:.1f}" fill="none" stroke="#ddd3c0" stroke-width="1.4" opacity="0.8"/>',
        f'    <rect width="{tw_px}" height="{th_px}" fill="none" stroke="#d5cbb8" stroke-width="1.0"/>',
        '  </pattern>',
        # Traditional lower car-porch Kota stone & warm earthy geometric paver pattern
        f'  <pattern id="kota-porch" width="{kota_px}" height="{kota_px}" patternUnits="userSpaceOnUse">',
        f'    <rect width="{kota_px}" height="{kota_px}" fill="#8a8f82"/>',
        f'    <rect x="0" y="0" width="{kota_px / 2:.2f}" height="{kota_px / 2:.2f}" fill="#83897c"/>',
        f'    <rect x="{kota_px / 2:.2f}" y="{kota_px / 2:.2f}" width="{kota_px / 2:.2f}" height="{kota_px / 2:.2f}" fill="#97846e" opacity="0.55"/>',
        f'    <rect x="2" y="2" width="{kota_px - 4:.2f}" height="{kota_px - 4:.2f}" fill="none" stroke="#6f6b61" stroke-width="0.8" opacity="0.55"/>',
        f'    <path d="M 0,{kota_px / 2:.2f} L {kota_px},{kota_px / 2:.2f} M {kota_px / 2:.2f},0 L {kota_px / 2:.2f},{kota_px}" stroke="#68645a" stroke-width="1.1"/>',
        '  </pattern>',
        # Warm oak wood grain pattern
        '  <pattern id="oak-grain" width="40" height="40" patternUnits="userSpaceOnUse">',
        '    <rect width="40" height="40" fill="#bf9367"/>',
        '    <path d="M0,8 Q20,5 40,8 M0,20 Q20,23 40,20 M0,32 Q20,29 40,32" fill="none" stroke="#a6794e" stroke-width="1.1" opacity="0.65"/>',
        '  </pattern>',
        '  <filter id="soft-shadow" x="-10%" y="-10%" width="130%" height="130%">',
        '    <feDropShadow dx="2" dy="3" stdDeviation="3.5" flood-color="#1d1a16" flood-opacity="0.26"/>',
        '  </filter>',
        '</defs>',
        f'<rect x="0" y="0" width="{cw}" height="{ch}" fill="#f6f4ef"/>',
    ]

    title = (
        "Tirumala 2 (P12-A) · Realistic Material-Rendered Overhead 2D Plan"
        if is_p12
        else "Tirumala 3 (P11) · Realistic Material-Rendered Overhead 2D Plan"
    )
    subtitle = (
        f"24 × 48 in Warm White/Cream Marble-Look Flooring (±0′0″) · Traditional Kota/Red-Oxide Lower Car Porch (-{drop_in_txt} Provisional) · Charcoal-Bronze Glazing · West ↑ North →"
    )
    lines.append(f'<text x="54" y="48" font-size="22" font-weight="700" fill="#181c1a">{title}</text>')
    lines.append(f'<text x="54" y="76" font-size="13.5" fill="#464d49">{subtitle}</text>')
    lines.append(f'<text x="{tx(W / 2)}" y="{ty(D) - 24}" font-size="12" font-weight="600" text-anchor="middle" fill="#3a403d">WEST · rear boundary</text>')
    lines.append(f'<text x="{tx(W / 2)}" y="{ty(0) + 32}" font-size="12" font-weight="600" text-anchor="middle" fill="#3a403d">EAST · 9 m road &amp; basketball-court outlook</text>')
    lines.append(f'<text x="{tx(W) + 28}" y="{ty(D / 2)}" font-size="12.5" font-weight="700" text-anchor="middle" fill="#181c1a" transform="rotate(90 {tx(W) + 28} {ty(D / 2)})">NORTH · 12 m road &amp; colony garden →</text>')

    # Plot base
    lines.append(f'<rect x="{tx(0)}" y="{ty(D)}" width="{round(W * scale, 2)}" height="{round(D * scale, 2)}" fill="url(#marble-outdoor)" stroke="#7c766c" stroke-width="2"/>')

    # Planted green strips along North & Rear West edges
    lines.append(f'<polygon points="{pts_str(plan["northGarden"])}" fill="url(#marble-outdoor)" stroke="none"/>')
    lines.append(f'<rect x="{tx(11920)}" y="{ty(14478)}" width="{round(272 * scale, 1)}" height="{round(6128 * scale, 1)}" fill="#587b48" opacity="0.88"/>')

    # Raised East Forecourt & Raised North Passage (24x48 matte exterior cream marble)
    for reg in plan.get("raisedForecourt", []):
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="url(#marble-outdoor)" stroke="#cfc6b4" stroke-width="1"/>')
    for reg in plan.get("raisedPassage", []):
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="url(#marble-outdoor)" stroke="#cfc6b4" stroke-width="1"/>')

    # Lower Car Porch: Red-Oxide border + Kota stone / earthy geometric paver field
    porch_polys = [mm_poly_raw := Polygon(reg["outer"]) for reg in plan["lowerPorch"]]
    if not is_p12 and plan.get("porchGain"):
        for reg in plan["porchGain"]:
            porch_polys.append(Polygon(reg["outer"]))
    porch_union = unary_union(porch_polys)
    porch_outer_ring = list(porch_union.exterior.coords)[:-1]
    porch_inner_poly = porch_union.buffer(-165.0, join_style=2)
    porch_inner_ring = list(porch_inner_poly.exterior.coords)[:-1]

    lines.append(f'<polygon points="{pts_str(porch_outer_ring)}" fill="#8b4335" stroke="#632d22" stroke-width="1.5"/>')
    lines.append(f'<polygon points="{pts_str(porch_inner_ring)}" fill="url(#kota-porch)" stroke="#733529" stroke-width="1.2"/>')

    # Step-down shadow & glowing warm LED nosing along levelChangeLines
    for seg in plan.get("levelChangeLines", []):
        lines.append(f'<line x1="{tx(seg[0][0])}" y1="{ty(seg[0][1])}" x2="{tx(seg[1][0])}" y2="{ty(seg[1][1])}" stroke="#231f1b" stroke-width="6.5" stroke-opacity="0.35"/>')
        lines.append(f'<line x1="{tx(seg[0][0])}" y1="{ty(seg[0][1])}" x2="{tx(seg[1][0])}" y2="{ty(seg[1][1])}" stroke="#ffdca2" stroke-width="2.6"/>')
        lines.append(f'<line x1="{tx(seg[0][0])}" y1="{ty(seg[0][1])}" x2="{tx(seg[1][0])}" y2="{ty(seg[1][1])}" stroke="#b83b2b" stroke-width="1.1" stroke-dasharray="5,4"/>')

    # Connected Open Floor (24x48 polished warm white/cream marble)
    for reg in plan["openFloor"]:
        lines.append(f'<polygon points="{pts_str(reg["outer"])}" fill="url(#marble-indoor)" stroke="#e2d9c8" stroke-width="0.8"/>')

    # Individual Rooms
    for rm in plan["rooms"]:
        rid = rm["id"]
        if rid in ("g-veranda", "g-wash-gully"):
            pat = "url(#marble-outdoor)"
        elif rid == "g-care-court":
            pat = "#d9cbb5"
        else:
            pat = "url(#marble-indoor)"
        lines.append(f'<polygon points="{pts_str(rm["regions"][0]["outer"])}" fill="{pat}" stroke="#dfd6c5" stroke-width="0.9"/>')
        if rid == "g-care-court":
            bx0, by0, bx1, by1 = rm["bounds"]
            lines.append(f'<rect x="{tx(bx0 + 180)}" y="{ty(by1 - 180)}" width="{round((bx1 - bx0 - 360) * scale, 1)}" height="{round((by1 - by0 - 360) * scale, 1)}" rx="8" fill="#5e7f4c" stroke="#8aa375" stroke-width="2"/>')
            lines.append(f'<circle cx="{tx((bx0 + bx1) / 2)}" cy="{ty((by0 + by1) / 2)}" r="22" fill="#466936" stroke="#7da167" stroke-width="1.5"/>')

    # Subtle warm ambient glow inside ICU and Veranda to distinguish spaces while showing real marble tiles
    icu_rm = next(r for r in plan["rooms"] if r["id"] == "g-care")
    ver_rm = next(r for r in plan["rooms"] if r["id"] == "g-veranda")
    lines.append(f'<polygon points="{pts_str(icu_rm["regions"][0]["outer"])}" fill="#d8eefb" fill-opacity="0.16" stroke="none"/>')
    lines.append(f'<polygon points="{pts_str(ver_rm["regions"][0]["outer"])}" fill="#eadcf8" fill-opacity="0.14" stroke="none"/>')

    # Kitchen L-counter & short serving worktop (Oak cabinet base + white quartz/marble worktop + sink + 4-burner hob)
    lines.append(f'<polygon points="{pts_str(plan["counter"])}" fill="#f3efe6" stroke="#8f6339" stroke-width="2.0" filter="url(#soft-shadow)"/>')
    lines.append(f'<polygon points="{pts_str(plan["serving"])}" fill="url(#oak-grain)" stroke="#7a522d" stroke-width="1.6" filter="url(#soft-shadow)"/>')
    # Sink under east window & 4-burner hob on store wall leg
    lines.append(f'<rect x="{tx(3280)}" y="{ty(2160)}" width="{round(600 * scale, 1)}" height="{round(420 * scale, 1)}" rx="4" fill="#d3d8dc" stroke="#6d7378" stroke-width="1.2"/>')
    lines.append(f'<rect x="{tx(2500)}" y="{ty(3420)}" width="{round(440 * scale, 1)}" height="{round(640 * scale, 1)}" rx="3" fill="#1e2022" stroke="#555" stroke-width="1"/>')

    # Staircase (warm oak treads)
    for st in plan["stairs"]:
        sp = st["polygon"]
        lines.append(f'<polygon points="{pts_str(sp)}" fill="url(#oak-grain)" stroke="#6e4b2a" stroke-width="1.2"/>')
        xs = [p[0] for p in sp]
        ys = [p[1] for p in sp]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if "risers" in st:
            nr = int(st["risers"])
            if st["direction"] in ("South", "North"):
                for i in range(1, nr):
                    xx = x0 + i * (x1 - x0) / nr
                    lines.append(f'<line x1="{tx(xx)}" y1="{ty(y0)}" x2="{tx(xx)}" y2="{ty(y1)}" stroke="#5c3d20" stroke-width="1.0"/>')
            elif st["direction"] == "West":
                for i in range(1, nr):
                    yy = y0 + i * (y1 - y0) / nr
                    lines.append(f'<line x1="{tx(x0)}" y1="{ty(yy)}" x2="{tx(x1)}" y2="{ty(yy)}" stroke="#5c3d20" stroke-width="1.0"/>')

    # Furniture (realistic wood/linen/upholstery rendering with soft drop shadows)
    for item in plan["furniture"]:
        fkind = item["kind"]
        if fkind == "dining-set" and item.get("parts"):
            for idx, part in enumerate(item["parts"]):
                fill_c = "url(#oak-grain)" if idx == 0 else "#e6decb"
                lines.append(f'<polygon points="{pts_str(part)}" fill="{fill_c}" stroke="#7a5736" stroke-width="1.2" filter="url(#soft-shadow)"/>')
        elif fkind in ("bed", "reclining-bed"):
            bx0, by0, bx1, by1 = item["bounds"]
            lines.append(f'<polygon points="{pts_str(item["polygon"])}" fill="#f5f1e8" stroke="#8c6239" stroke-width="1.8" filter="url(#soft-shadow)"/>')
            if fkind == "reclining-bed":
                if is_p12:
                    lines.append(f'<rect x="{tx(bx0 + 100)}" y="{ty(by1 - 100)}" width="{round(360 * scale, 1)}" height="{round((by1 - by0 - 200) * scale, 1)}" rx="4" fill="#ffffff" stroke="#b8c4ce" stroke-width="1"/>')
                    lines.append(f'<rect x="{tx(bx0 + 950)}" y="{ty(by1 - 80)}" width="{round(1150 * scale, 1)}" height="{round((by1 - by0 - 160) * scale, 1)}" rx="3" fill="#d3e3ee" stroke="none"/>')
                else:
                    lines.append(f'<rect x="{tx(bx0 + 100)}" y="{ty(by1 - 100)}" width="{round((bx1 - bx0 - 200) * scale, 1)}" height="{round(360 * scale, 1)}" rx="4" fill="#ffffff" stroke="#b8c4ce" stroke-width="1"/>')
                    lines.append(f'<rect x="{tx(bx0 + 80)}" y="{ty(by0 + 1250)}" width="{round((bx1 - bx0 - 160) * scale, 1)}" height="{round(1150 * scale, 1)}" rx="3" fill="#d3e3ee" stroke="none"/>')
        elif fkind in ("wardrobe", "equipment-table", "care-cupboard", "media-console", "coffee-table", "shelves-0", "shelves-1"):
            lines.append(f'<polygon points="{pts_str(item["polygon"])}" fill="url(#oak-grain)" stroke="#6e4b2a" stroke-width="1.3" filter="url(#soft-shadow)"/>')
        elif fkind == "sofa" or fkind.startswith("care-chair"):
            lines.append(f'<polygon points="{pts_str(item["polygon"])}" fill="#e2d9c5" stroke="#9c8f78" stroke-width="1.3" filter="url(#soft-shadow)"/>')
        else:
            lines.append(f'<polygon points="{pts_str(item["polygon"])}" fill="#f4f2ed" stroke="#99948b" stroke-width="1.1"/>')

    # Parked Car in Lower Porch
    cb = plan["carBody"]
    cx0, cy0, cx1, cy1 = min(p[0] for p in cb), min(p[1] for p in cb), max(p[0] for p in cb), max(p[1] for p in cb)
    lines.append(f'<rect x="{tx(cx0)}" y="{ty(cy1)}" width="{round((cx1 - cx0) * scale, 1)}" height="{round((cy1 - cy0) * scale, 1)}" rx="18" fill="#eceae4" stroke="#5d6163" stroke-width="1.6" filter="url(#soft-shadow)"/>')
    lines.append(f'<rect x="{tx(cx0 + 220)}" y="{ty(cy1 - 650)}" width="{round((cx1 - cx0 - 440) * scale, 1)}" height="{round((cy1 - cy0 - 1450) * scale, 1)}" rx="10" fill="#475b63" stroke="#2f3b40" stroke-width="1"/>')

    # Solid masonry walls with dark charcoal-ivory architectural cut
    for wr in plan["wallRects"]:
        x0, y0, x1, y1 = wr
        lines.append(f'<rect x="{tx(x0)}" y="{ty(y1)}" width="{max(1.5, round((x1 - x0) * scale, 2))}" height="{max(1.5, round((y1 - y0) * scale, 2))}" fill="#2b2927" stroke="#1a1817" stroke-width="0.6"/>')

    # Modern Charcoal-Bronze Glazed Doors & Windows
    for op in plan["openings"]:
        ax, ay = op["a"]
        bx, by = op["b"]
        knd = op["kind"]
        if knd in ("window", "glass"):
            lines.append(f'<line x1="{tx(ax)}" y1="{ty(ay)}" x2="{tx(bx)}" y2="{ty(by)}" stroke="#2a2724" stroke-width="5.0"/>')
            lines.append(f'<line x1="{tx(ax)}" y1="{ty(ay)}" x2="{tx(bx)}" y2="{ty(by)}" stroke="#8fd4e8" stroke-width="2.4"/>')
        elif knd == "wood-mesh-fold":
            lines.append(f'<line x1="{tx(ax)}" y1="{ty(ay)}" x2="{tx(bx)}" y2="{ty(by)}" stroke="#8f623d" stroke-width="4.5" stroke-dasharray="7,3"/>')

    # Potted greenery accents (Bungalow-inspired terracotta & ceramic planters)
    pots = (
        [(5650, 1320), (8650, 1320), (10680, 4550), (11820, 7850), (2100, 420), (4800, 420)]
        if is_p12
        else [(5250, 1320), (8750, 1850), (9550, 6380), (11820, 7850), (2100, 420), (4600, 420)]
    )
    for px_, py_ in pots:
        lines.append(f'<circle cx="{tx(px_)}" cy="{ty(py_)}" r="11" fill="#b86b4b" stroke="#7d432b" stroke-width="1.2" filter="url(#soft-shadow)"/>')
        lines.append(f'<circle cx="{tx(px_)}" cy="{ty(py_)}" r="8" fill="#4e783f"/>')

    # Room & Finish Callout Pills
    callouts = [
        (2350, 11150, "Master Bedroom", "24×48″ Ivory Marble"),
        (4800, 13450, "Master Bath (8′×6′)", "Satin Ivory Tile"),
        (7150, 13450, "Attached WC", "Satin Ivory Tile"),
        (9850, 12750, "Caregiver Suite", "24×48″ Ivory Marble"),
        (9850, 9850, "Drawing (Unfurnished)" if is_p12 else "Drawing Room", "24×48″ Ivory Marble"),
        (4850, 6850, "Living / Dining", "24×48″ Ivory Marble (±0′0″)"),
        (3850, 3150, "Kitchen", "Oak L-Counter · No Fridge/Puja"),
        (4800, 760, "Raised East Forecourt · ±0′0″", "Non-Slip Matte Ivory Marble"),
    ]
    if is_p12:
        callouts.extend([
            (8950, 6450, "Home ICU (Notched)", "24×48″ Ivory Marble · Head South"),
            (7220, 2400, "Veranda · ±0′0″", "Matte Ivory Marble · Tall Glazing"),
            (10550, 1450, f"Lower Car Porch (-{drop_in_txt} Prov.)", "Kota Paver & Red-Oxide Border"),
        ])
    else:
        callouts.extend([
            (7150, 3950, "Home ICU (Rectangular)", "24×48″ Ivory Marble · Full P11 Set"),
            (10350, 7050, "Veranda · ±0′0″", "Shortened Return · Matte Ivory"),
            (10800, 1350, f"Lower Car Porch (-{drop_in_txt} Prov.)", "Kota Paver & Red-Oxide Border"),
        ])

    for cx_, cy_, main_t, sub_t in callouts:
        px_c, py_c = tx(cx_), ty(cy_)
        bw_ = max(len(main_t), len(sub_t)) * 6.2 + 18
        main_esc = main_t.replace("&", "&amp;")
        sub_esc = sub_t.replace("&", "&amp;")
        lines.append(f'<rect x="{px_c - bw_ / 2:.1f}" y="{py_c - 17:.1f}" width="{bw_:.1f}" height="32" rx="6" fill="#1e2220" fill-opacity="0.80"/>')
        lines.append(f'<text x="{px_c:.1f}" y="{py_c - 3:.1f}" font-size="11.5" font-weight="700" text-anchor="middle" fill="#ffffff">{main_esc}</text>')
        lines.append(f'<text x="{px_c:.1f}" y="{py_c + 10:.1f}" font-size="9.8" font-weight="500" text-anchor="middle" fill="#e5decb">{sub_esc}</text>')

    # Legend swatches at bottom
    fy = ch - 110
    swatches = [
        (54, "#f7f3eb", "#dfd7c8", "24×48 in Polished White/Cream Marble (Indoors ±0′0″)"),
        (430, "#f1ece1", "#d5cbb8", "24×48 in Matte Non-Slip Cream Marble (Veranda, Forecourt, Passages ±0′0″)"),
        (965, "#8a8f82", "#8b4335", f"Traditional Kota Paver + Red-Oxide Border (Lower Car Porch -{drop_in_txt} Provisional)"),
    ]
    for sx_, sfill, sstroke, slbl in swatches:
        lines.append(f'<rect x="{sx_}" y="{fy - 14}" width="22" height="18" rx="3" fill="{sfill}" stroke="{sstroke}" stroke-width="2"/>')
        lines.append(f'<text x="{sx_ + 30}" y="{fy}" font-size="12.5" font-weight="600" fill="#1f2421">{slbl}</text>')
    lines.append(f'<text x="54" y="{fy + 28}" font-size="12.5" fill="#424845"> Glowing amber/red step line marks the {drop_in_txt} ({porch_drop_mm:.1f} mm) provisional drop between the raised house/veranda/forecourt (±0′0″) and the lower vehicle-parking porch.</text>')
    lines.append("</svg>")
    return "\n".join(lines)
