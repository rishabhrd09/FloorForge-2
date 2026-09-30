"""Deterministic exterior composition and preservation contracts.

The exterior layer works in the building model's millimetre coordinate system.
Scene conversion to metres happens only in scene.py.  It intentionally creates
preliminary architectural geometry, not structural or regulatory approval.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import math
from typing import Any

from shapely.geometry import Point, Polygon, box

from .frontage import plan_frontage

from .model import DesignError, sha


EXTERIOR_THEME_IDS = (
    "current",
    "modern_tropical",
    "warm_modern_minimal",
    "tropical_verandah",
    "earth_terracotta",
)
INTERIOR_THEME_IDS = (
    "current",
    "bright_natural",
    "warm_contemporary",
    "quiet_minimal",
    "earthy_modern_indian",
)
CHANGE_POLICIES = ("finish_only", "exterior_refinement", "spatial_redesign")


@dataclass(frozen=True)
class DesignPreferences:
    exterior_theme: str = "warm_modern_minimal"
    interior_theme: str = "current"
    change_policy: str = "exterior_refinement"
    interior_layout_locked: bool = True
    seed: int = 0
    theme_version: str = "1"


def _theme(
    label: str,
    description: str,
    porch_depth_mm: int,
    balcony_depth_mm: int,
    porch_width_mm: int,
    materials: dict[str, str],
    geometry: dict[str, Any],
) -> dict[str, Any]:
    return {
        "label": label,
        "description": description,
        "porch_strategy": geometry["porch_strategy"],
        "balcony_strategy": geometry["balcony_strategy"],
        "screen_strategy": geometry["screen_strategy"],
        "opening_policy": geometry["opening_policy"],
        "roof_edge_strategy": geometry["roof_edge_strategy"],
        "boundary_strategy": geometry["boundary_strategy"],
        "planting_strategy": geometry["planting_strategy"],
        "materials": materials,
        "lighting_roles": ["entry_sconce", "porch_wash", "path_bollard"],
        "compact_fallbacks": {
            "porch_depth_mm": min(porch_depth_mm, 900),
            "balcony_depth_mm": min(balcony_depth_mm, 900),
            "omit_secondary_screen": True,
        },
        "porch_depth_mm": porch_depth_mm,
        "balcony_depth_mm": balcony_depth_mm,
        "porch_width_mm": porch_width_mm,
        "geometry": geometry,
    }


EXTERIOR_THEMES: dict[str, dict[str, Any]] = {
    "current": {
        "label": "Current exterior",
        "description": "Preserves the existing facade recipe and saved-project appearance.",
        "porch_strategy": "legacy",
        "balcony_strategy": "legacy",
        "screen_strategy": "legacy",
        "opening_policy": "preserve",
        "roof_edge_strategy": "legacy",
        "boundary_strategy": "legacy",
        "planting_strategy": "legacy",
        "materials": {},
        "lighting_roles": [],
        "compact_fallbacks": {},
        "porch_depth_mm": 0,
        "balcony_depth_mm": 0,
        "geometry": {},
    },
    "modern_tropical": _theme(
        "Modern Tropical",
        "White rendered volumes, slim black full-height glazing, a floating roof slab, a stamped-cobble arrival court, pebble gardens with sculpted planting and a lawn with stepping stones.",
        2100,
        1800,
        4200,
        {
            "wall": "#f1efea",
            "stone": "#8a8883",
            "timber": "#7a5234",
            "frame": "#1d2022",
            "roof": "#ecebe6",
            "site_paving": "#8e9194",
            "site_gate": "#1d2022",
            "site_soil": "#43372b",
            "site_leaf": "#3f6b35",
            "site_leaf_light": "#86a257",
        },
        {
            "porch_strategy": "cantilevered_slab_portico",
            "balcony_strategy": "frameless_glass_balustrade",
            "screen_strategy": "timber_slat_and_stone_cladding",
            "opening_policy": "full_height_glazing",
            "roof_edge_strategy": "floating_roof_slab",
            "boundary_strategy": "rendered_wall_black_slat_gate",
            "planting_strategy": "tropical_layers_pebble_beds_lawn",
        },
    ),
    "warm_modern_minimal": _theme(
        "Warm Modern Minimal",
        "A generous sheltered arrival court, broad glazed openings, a timber screen anchor and a furnished balcony.",
        2950,
        2550,
        7000,
        {
            "wall": "#ded9cd",
            "stone": "#8d806d",
            "timber": "#76583e",
            "frame": "#25292a",
            "roof": "#3d4842",
            "site_paving": "#b8b1a3",
            "site_gate": "#25292a",
            "site_soil": "#625545",
            "site_leaf": "#5c744f",
            "site_leaf_light": "#91a06b",
        },
        {
            "porch_strategy": "thin_sheltered_threshold",
            "balcony_strategy": "clean_frame_with_deep_reveal",
            "screen_strategy": "single_vertical_blade",
            "opening_policy": "living_feature_plus_360mm",
            "roof_edge_strategy": "slim_horizontal_planes",
            "boundary_strategy": "quiet_metal_gate",
            "planting_strategy": "feature_tree_grasses_low_beds",
        },
    ),
    "tropical_verandah": _theme(
        "Tropical Verandah",
        "A deeper shaded sit-out, timber screens, a pergola rhythm and layered foliage.",
        2400,
        1900,
        5400,
        {
            "wall": "#e4dfcf",
            "stone": "#a58d65",
            "timber": "#76583c",
            "frame": "#2d332f",
            "roof": "#635542",
            "site_paving": "#b2a996",
            "site_gate": "#5b684e",
            "site_soil": "#5f513d",
            "site_leaf": "#496b46",
            "site_leaf_light": "#81965d",
        },
        {
            "porch_strategy": "deep_corner_verandah",
            "balcony_strategy": "shaded_seating_edge",
            "screen_strategy": "timber_batten_privacy",
            "opening_policy": "shaded_living_feature_plus_180mm",
            "roof_edge_strategy": "open_pergola_and_fascia",
            "boundary_strategy": "warm_masonry_and_timber_gate",
            "planting_strategy": "layered_foliage_and_shaded_side_passage",
        },
    ),
    "earth_terracotta": _theme(
        "Earth & Terracotta",
        "Warm stone, a terracotta screen, a substantial threshold and planted balcony edge.",
        2100,
        1550,
        4600,
        {
            "wall": "#e8dccb",
            "stone": "#b06d4f",
            "timber": "#704832",
            "frame": "#3a342f",
            "roof": "#955947",
            "site_paving": "#bcae99",
            "site_gate": "#4c453a",
            "site_soil": "#6a4e3c",
            "site_leaf": "#5a7049",
            "site_leaf_light": "#a18b59",
        },
        {
            "porch_strategy": "substantial_warm_threshold",
            "balcony_strategy": "planted_privacy_edge",
            "screen_strategy": "terracotta_brik_screen",
            "opening_policy": "deeper_reveal_plus_180mm",
            "roof_edge_strategy": "warm_coping_and_shadow_band",
            "boundary_strategy": "stone_edge_and_metal_gate",
            "planting_strategy": "flowering_accents_and_stone_beds",
        },
    ),
}


INTERIOR_THEMES: dict[str, dict[str, Any]] = {
    "current": {
        "label": "Current interior",
        "description": "Preserves the existing interior material assignments and furniture layout.",
        "materials": {},
    },
    "bright_natural": {
        "label": "Bright Natural",
        "description": "Light oak floors, warm white walls, sand linen upholstery, walnut and black accents.",
        "materials": {
            "fabric": "#d3c7b3",
            "fabric-dark": "#5d6b57",
            "linen": "#f1ede4",
            "rug": "#c9bda8",
            "woodfloor": "#b89572",
        },
    },
    "warm_contemporary": {
        "label": "Warm Contemporary",
        "description": "Soft clay, linen and walnut-like furniture finishes.",
        "materials": {
            "fabric": "#c8b79f",
            "fabric-dark": "#66715c",
            "linen": "#ede8dc",
            "rug": "#a58a70",
            "woodfloor": "#9d7955",
        },
    },
    "quiet_minimal": {
        "label": "Quiet Minimal",
        "description": "Low-contrast mineral neutrals with calm upholstery.",
        "materials": {
            "fabric": "#c9cec7",
            "fabric-dark": "#56645e",
            "linen": "#f3f1eb",
            "rug": "#b7b9ad",
            "woodfloor": "#b1a99d",
        },
    },
    "earthy_modern_indian": {
        "label": "Earthy Modern Indian",
        "description": "Terracotta, indigo-green and natural fibre accents.",
        "materials": {
            "fabric": "#b87052",
            "fabric-dark": "#5a493b",
            "linen": "#dfc7a4",
            "rug": "#93603f",
            "woodfloor": "#845e42",
        },
    },
}


def get_exterior_theme(theme_id: str) -> dict[str, Any]:
    if theme_id not in EXTERIOR_THEMES:
        raise DesignError("THEME", f"Unknown exterior theme: {theme_id}")
    return deepcopy(EXTERIOR_THEMES[theme_id])


def get_interior_theme(theme_id: str) -> dict[str, Any]:
    if theme_id not in INTERIOR_THEMES:
        raise DesignError("THEME", f"Unknown interior theme: {theme_id}")
    return deepcopy(INTERIOR_THEMES[theme_id])


def list_available_themes() -> dict[str, list[dict[str, str]]]:
    return {
        "exterior": [
            {"id": key, "label": value["label"], "description": value["description"]}
            for key, value in EXTERIOR_THEMES.items()
        ],
        "interior": [
            {"id": key, "label": value["label"], "description": value["description"]}
            for key, value in INTERIOR_THEMES.items()
        ],
    }


def resolve_legacy_preferences(project: dict[str, Any]) -> dict[str, Any]:
    """Preserve pre-upgrade projects unless they explicitly opt into themes."""
    brief = project.get("brief", {}) if isinstance(project, dict) else {}
    if not isinstance(brief, dict):
        brief = {}
    modern_project = project.get("schema") == "floorforge.project/0.3"
    return {
        "exterior_theme": brief.get(
            "exterior_theme",
            "modern_tropical" if modern_project else "current",
        ),
        "interior_theme": brief.get("interior_theme", "current"),
        "change_policy": brief.get("change_policy", "exterior_refinement"),
        "interior_layout_locked": brief.get("interior_layout_locked", True),
        "seed": brief.get("seed", 0),
        "theme_version": brief.get("theme_version", "1"),
    }


def preferences_from_brief(brief: dict[str, Any]) -> DesignPreferences:
    values = {
        "exterior_theme": brief.get("exterior_theme", "current"),
        "interior_theme": brief.get("interior_theme", "current"),
        "change_policy": brief.get("change_policy", "exterior_refinement"),
        "interior_layout_locked": brief.get("interior_layout_locked", True),
        "seed": brief.get("seed", 0),
        "theme_version": brief.get("theme_version", "1"),
    }
    if values["exterior_theme"] not in EXTERIOR_THEME_IDS:
        raise DesignError("THEME", f"Unknown exterior theme: {values['exterior_theme']}")
    if values["interior_theme"] not in INTERIOR_THEME_IDS:
        raise DesignError("THEME", f"Unknown interior theme: {values['interior_theme']}")
    if values["change_policy"] not in CHANGE_POLICIES:
        raise DesignError("CHANGE_POLICY", f"Unknown design change policy: {values['change_policy']}")
    if type(values["interior_layout_locked"]) is not bool:
        raise DesignError("THEME", "interior_layout_locked must be boolean.")
    if type(values["seed"]) is not int or not 0 <= values["seed"] <= 2**31 - 1:
        raise DesignError("THEME", "seed must be a non-negative 32-bit integer.")
    if not isinstance(values["theme_version"], str) or not values["theme_version"]:
        raise DesignError("THEME", "theme_version must be a non-empty string.")
    return DesignPreferences(**values)


def _wall_interval(wall: dict[str, Any], opening: dict[str, Any]) -> tuple[float, float]:
    return float(opening["offset"]), float(opening["offset"] + opening["width"])


def _merge_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[list[float]] = []
    for a, b in sorted(intervals):
        if not result or a > result[-1][1] + 1:
            result.append([a, b])
        else:
            result[-1][1] = max(result[-1][1], b)
    return [(a, b) for a, b in result]


def derive_facade_anchors(building: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive attachment regions from real external wall segments."""
    footprint = Polygon(building["footprint"])
    openings_by_wall: dict[str, list[dict[str, Any]]] = {}
    for opening in building["openings"]:
        openings_by_wall.setdefault(opening["wall_id"], []).append(opening)
    entry_ids = {o["id"] for o in building["openings"] if o["kind"] == "entry"}
    anchors = []
    for wall in building["walls"]:
        if not wall["external"]:
            continue
        a = tuple(wall["a"])
        b = tuple(wall["b"])
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 1:
            continue
        tangent = [round(dx / length, 8), round(dy / length, 8)]
        normal = [-tangent[1], tangent[0]]
        midpoint = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if footprint.covers(Point(midpoint.x + normal[0], midpoint.y + normal[1])):
            normal = [-normal[0], -normal[1]]
        intervals = [_wall_interval(wall, o) for o in openings_by_wall.get(wall["id"], [])]
        keepouts = [
            {"start_mm": max(0, o["offset"] - (450 if o["id"] in entry_ids else 220)),
             "end_mm": min(length, o["offset"] + o["width"] + (450 if o["id"] in entry_ids else 220)),
             "reason": "entrance_access" if o["id"] in entry_ids else "opening_clearance"}
            for o in openings_by_wall.get(wall["id"], [])
        ]
        reserved = _merge_intervals(
            intervals + [(x["start_mm"], x["end_mm"]) for x in keepouts]
        )
        gaps = []
        cursor = 0.0
        for start, end in reserved:
            if start - cursor >= 500:
                gaps.append({"start_mm": round(cursor), "end_mm": round(start)})
            cursor = max(cursor, end)
        if length - cursor >= 500:
            gaps.append({"start_mm": round(cursor), "end_mm": round(length)})
        anchors.append({
            "wall_id": wall["id"],
            "floor_id": wall["floor"],
            "origin": [round(a[0], 3), round(a[1], 3)],
            "tangent": tangent,
            "outward_normal": [round(normal[0], 8), round(normal[1], 8)],
            "wall_height_mm": wall["height"],
            "room_adjacencies": list(wall["rooms"]),
            "existing_opening_intervals": [
                {"start_mm": round(x), "end_mm": round(y)} for x, y in intervals
            ],
            "entrance_and_access_keepouts": keepouts,
            "available_attachment_regions": gaps,
        })
    return anchors


def protected_interior_fingerprint(building: dict[str, Any]) -> str:
    return sha({
        "spaces": [
            {
                "id": s["id"],
                "floor": s["floor"],
                "kind": s["kind"],
                "polygon": s["polygon"],
                "clear": s.get("clear", []),
            }
            for s in building["spaces"]
        ],
        "stairs": building.get("stairs", []),
        "floor_levels": [i * building["brief"]["floor_height_mm"] for i in range(building["storeys"])],
    })


def classify_opening_role(opening: dict[str, Any], adjacent_room_kinds: list[str]) -> str:
    kinds = set(adjacent_room_kinds)
    if opening["kind"] == "glazed":
        return "balcony_access"
    if opening["kind"] in ("entry", "door"):
        return "entrance"
    if "living" in kinds or "family" in kinds or "dining" in kinds:
        return "living_feature"
    if "bedroom" in kinds:
        return "bedroom_primary"
    if "stair" in kinds:
        return "stair_daylight"
    if "bathroom" in kinds:
        return "bathroom_privacy"
    if "kitchen" in kinds:
        return "kitchen_worktop"
    if "utility" in kinds:
        return "utility_service"
    return "secondary_opening"


def _front_entry(building: dict[str, Any]) -> tuple[float, float]:
    entry = next(o for o in building["openings"] if o["kind"] == "entry")
    wall = next(w for w in building["walls"] if w["id"] == entry["wall_id"])
    length = math.dist(wall["a"], wall["b"])
    u = (
        (wall["b"][0] - wall["a"][0]) / length,
        (wall["b"][1] - wall["a"][1]) / length,
    )
    distance = entry["offset"] + entry["width"] / 2
    return wall["a"][0] + u[0] * distance, wall["a"][1] + u[1] * distance


def _bounds_for_front(building: dict[str, Any]) -> tuple[float, float]:
    fp = Polygon(building["footprint"])
    return fp.bounds[2], fp.bounds[3]


def _opening_proposals(
    building: dict[str, Any],
    theme: dict[str, Any],
    policy: str,
) -> list[dict[str, Any]]:
    if theme["label"] == EXTERIOR_THEMES["current"]["label"] or policy == "finish_only":
        return []
    hosts = {w["id"]: w for w in building["walls"]}
    proposals = []
    delta = 360 if "plus_360" in theme["geometry"]["opening_policy"] else 240 if "plus_240" in theme["geometry"]["opening_policy"] else 180
    candidates = []
    for opening in building["openings"]:
        if opening["kind"] not in ("window", "glazed"):
            continue
        wall = hosts[opening["wall_id"]]
        if opening["kind"] == "glazed":
            wall_length = math.dist(wall["a"], wall["b"])
            proposed_width = min(opening["width"] + 600, wall_length - 240) // 300 * 300
            if proposed_width > opening["width"]:
                proposed_offset = round((wall_length - proposed_width) / 2)
                candidates.append((0, {
                    "id": f"{opening['id']}-refinement",
                    "opening_id": opening["id"],
                    "role": "balcony_access",
                    "before": {
                        "offset": opening["offset"],
                        "width": opening["width"],
                        "sill": opening["sill"],
                        "height": opening["height"],
                    },
                    "after": {
                        "offset": proposed_offset,
                        "width": proposed_width,
                        "sill": opening["sill"],
                        "height": opening["height"],
                    },
                    "reason": "Wider room-to-balcony sliding opening; host wall and clearance checked.",
                    "review_status": "geometry_screen_pending",
                }))
            continue
        if not wall["external"]:
            continue
        kinds = [
            next(s["kind"] for s in building["spaces"] if s["id"] == room)
            for room in wall["rooms"]
        ]
        role = classify_opening_role(opening, kinds)
        if not set(kinds).intersection({"living", "family", "dining", "bedroom", "stair"}):
            continue
        wall_length = math.dist(wall["a"], wall["b"])
        role_delta = delta if role == "living_feature" else 240 if role == "bedroom_primary" else 180
        proposed_width = min(opening["width"] + role_delta, wall_length - 360) // 300 * 300
        if proposed_width <= opening["width"]:
            continue
        proposed_offset = round((wall_length - proposed_width) / 2)
        proposed = {
            "id": f"{opening['id']}-refinement",
            "opening_id": opening["id"],
            "role": classify_opening_role(opening, kinds),
            "before": {
                "offset": opening["offset"],
                "width": opening["width"],
                "sill": opening["sill"],
                "height": opening["height"],
            },
            "after": {
                "offset": proposed_offset,
                "width": proposed_width,
                "sill": opening["sill"],
                "height": opening["height"],
            },
            "reason": "Room-aware feature opening refinement; host wall and clearance checked.",
            "review_status": "geometry_screen_pending",
        }
        other = [
            _wall_interval(wall, other)
            for other in building["openings"]
            if other["wall_id"] == wall["id"] and other["id"] != opening["id"]
        ]
        if any(
            proposed_offset < end and proposed_offset + proposed_width > start
            for start, end in other
        ):
            continue
        candidates.append((0 if role == "living_feature" else 1 if role == "bedroom_primary" else 2, proposed))
    candidates.sort(key=lambda item: (item[0], item[1]["opening_id"]))
    return [item[1] for item in candidates[:8]]


def _rectangle_assembly(
    ident: str,
    role: str,
    floor: int,
    bounds_mm: tuple[float, float, float, float],
    geometry: dict[str, Any],
    theme_id: str,
    host_ids: list[str],
) -> dict[str, Any]:
    x0, y0, x1, y1 = bounds_mm
    if x1 <= x0 or y1 <= y0:
        raise DesignError("EXTERIOR_GEOMETRY", f"Exterior assembly {ident} has non-positive dimensions.")
    return {
        "id": ident,
        "role": role,
        "parent_id": None,
        "host_ids": host_ids,
        "floor_id": floor,
        "geometry": {"bounds_mm": [round(x0), round(y0), round(x1), round(y1)], **geometry},
        "material_roles": ["exterior.wall.primary", "exterior.window.frame"],
        "clearance_regions": [],
        "support_intent": "preliminary_visual_coordination_only",
        "review_status": "geometry_screen_pending",
        "theme": theme_id,
    }


def _landscape(building: dict[str, Any], theme_id: str, porch: dict[str, Any] | None) -> dict[str, Any]:
    v = building["brief"]
    W, D = _bounds_for_front(building)
    xmin, ymin, xmax, ymax = Polygon(building["plot"]).bounds
    ex, _ = _front_entry(building)
    porch_x = tuple(porch["geometry"]["bounds_mm"][0::2]) if porch else None
    boundary = {
        **plan_frontage((xmin, ymin, xmax, ymax), ex, steps_x=porch_x, parking=v["parking"], front_mm=v["front_mm"]),
        "movement_clearance_mm": 500,
        "review_status": "geometry_screen_pending",
    }
    # A very shallow front setback cannot safely host a generated path or bed.
    # Keep the theme selectable and the boundary record honest, but omit outdoor
    # objects rather than placing them inside the house or outside the plot.
    if v["front_mm"] < 700:
        return {
            "schema": "floorforge.landscape/0.1",
            "arrival_sequence": ["road_edge", "gate", "approach", "landing", "main_door"],
            "features": [],
            "boundary": boundary,
            "outside_property_context": "not_generated",
        }
    porch_depth = porch["geometry"]["depth_mm"] if porch else 0
    features: list[dict[str, Any]] = []
    path_half = 1200 if theme_id == "warm_modern_minimal" else 900 if v["parking"] else 750
    path = box(
        max(xmin, ex - path_half),
        ymin + 120,
        min(xmax, ex + path_half),
        min(-porch_depth, -120),
    )
    if path.area > 1:
        features.append({
            "id": "site-arrival-path",
            "kind": "path",
            "polygon": [[round(x), round(y)] for x, y in list(path.exterior.coords)[:-1]],
            "material_role": "site.paving",
            "maintenance_clearance_mm": 300,
        })
    # Driveway behind the vehicle gate, clear of the entrance path.
    drive = Polygon()
    vehicle = next((g for g in boundary["gates"] if g["kind"] == "vehicle"), None)
    if vehicle:
        drive = box(vehicle["x0_mm"] + 60, ymin + 120, vehicle["x1_mm"] - 60, -250).difference(path.buffer(80))
        if drive.area > 400_000 and drive.geom_type == "Polygon":
            features.append({
                "id": "site-driveway",
                "kind": "court",
                "polygon": [[round(x), round(y)] for x, y in list(drive.exterior.coords)[:-1]],
                "material_role": "site.cobble",
            })
        else:
            drive = Polygon()
    bed_margin = 350
    left_bed = box(xmin + bed_margin, ymin + 500, max(xmin + bed_margin + 400, ex - path_half - 250), -250)
    right_bed = box(min(xmax - bed_margin - 400, ex + path_half + 250), ymin + 500, xmax - bed_margin, -250)
    for ident, bed in (("site-bed-left", left_bed), ("site-bed-right", right_bed)):
        if not drive.is_empty:
            bed = bed.difference(drive.buffer(200))
            bed = max(getattr(bed, "geoms", [bed]), key=lambda p: p.area) if not bed.is_empty else bed
        if bed.area > 250_000 and bed.geom_type == "Polygon" and not bed.intersects(path):
            features.append({
                "id": ident,
                "kind": "planting_bed",
                "polygon": [[round(x), round(y)] for x, y in list(bed.exterior.coords)[:-1]],
                "material_role": "site.soil",
                "maintenance_clearance_mm": 600,
            })
    tree_xs = [max(xmin + 1200, ex - 3000), min(xmax - 1200, ex + 3000)]
    if v["parking"]:
        tree_xs = [min(xmax - 1200, ex + 2800)]
    for i, x in enumerate(tree_xs):
        y = max(ymin + 1200, -max(1000, v["front_mm"] * 0.48))
        if not path.contains(Point(x, y)) and not drive.buffer(400).contains(Point(x, y)):
            features.append({
                "id": f"feature-tree-{i+1}",
                "kind": "tree",
                "position_mm": [round(x), round(y)],
                "scale": 0.92 if theme_id == "warm_modern_minimal" else 1.05,
                "mature_canopy_radius_mm": 1800 if theme_id == "tropical_verandah" else 1400,
                "material_role": "site.leaf",
            })
    shrub_count = 8 if theme_id == "tropical_verandah" else 5
    for i in range(shrub_count):
        x = xmin + 850 + i * max(550, (W - 1700) / max(1, shrub_count - 1))
        y = min(-350, ymin + 1050)
        if not path.contains(Point(x, y)) and not drive.buffer(250).contains(Point(x, y)):
            features.append({
                "id": f"layered-shrub-{i+1}",
                "kind": "shrub",
                "position_mm": [round(x), round(y)],
                "scale": 0.42 if theme_id != "earth_terracotta" else 0.48,
                "material_role": "site.leaf_light" if i % 3 == 0 else "site.leaf",
            })
    return {
        "schema": "floorforge.landscape/0.1",
        "arrival_sequence": ["road_edge", "gate", "approach", "landing", "main_door"],
        "features": features,
        "boundary": boundary,
        "outside_property_context": "not_generated",
    }


def generate_exterior_candidates(
    building: dict[str, Any],
    preferences: DesignPreferences,
    constraints: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if preferences.exterior_theme == "modern_tropical":
        from .modern_exterior import modern_candidate
        return [modern_candidate(building, preferences, {
            "rectangle_assembly": _rectangle_assembly,
            "front_entry": _front_entry,
            "anchors": derive_facade_anchors,
            "classify": classify_opening_role,
        })]
    if preferences.exterior_theme == "current":
        return [{
            "id": "legacy-current",
            "theme": "current",
            "assemblies": [],
            "landscape": {"schema": "floorforge.landscape/0.1", "features": [], "boundary": {}, "outside_property_context": "not_generated"},
            "opening_changes": [],
            "score": 0,
            "rejections": [],
        }]
    theme = get_exterior_theme(preferences.exterior_theme)
    W, D = _bounds_for_front(building)
    v = building["brief"]
    ex, _ = _front_entry(building)
    front_available = max(0, v["front_mm"] - 250)
    porch_depth = min(theme["porch_depth_mm"], front_available)
    if front_available < 700:
        porch_depth = 0
    porch_width = min(theme["porch_width_mm"], max(2400, round(W * 0.80)))
    porch_width = min(porch_width, W)
    px0 = max(0, min(W - porch_width, ex - porch_width / 2))
    assemblies: list[dict[str, Any]] = []
    porch = None
    if porch_depth >= 600:
        porch = _rectangle_assembly(
            "exterior-porch-01",
            "porch",
            0,
            (px0, -porch_depth, px0 + porch_width, 0),
            {
                "kind": "porch",
                "depth_mm": round(porch_depth),
                "width_mm": round(porch_width),
                "platform_z_mm": -120,
                "canopy_z_mm": 2850,
                "canopy_overhang_mm": 250,
                "support_count": 3 if preferences.exterior_theme == "warm_modern_minimal" else 2 if preferences.exterior_theme != "tropical_verandah" else 3,
            },
            preferences.exterior_theme,
            [next(o["id"] for o in building["openings"] if o["kind"] == "entry")],
        )
        assemblies.append(porch)
    if building["storeys"] > 1 and front_available >= 700:
        terrace = next((s for s in building["spaces"] if s["kind"] == "terrace"), None)
        balcony_center = (
            Polygon(terrace["polygon"]).centroid.x if terrace else max(ex, W * 0.58)
        )
        balcony_width = min(5000 if preferences.exterior_theme == "warm_modern_minimal" else 4300 if preferences.exterior_theme != "tropical_verandah" else 4700, W * 0.70)
        balcony_depth = min(theme["balcony_depth_mm"], front_available)
        bx0 = max(0, min(W - balcony_width, balcony_center - balcony_width / 2))
        glazed = [o for o in building["openings"] if o["kind"] == "glazed" and o["floor"] == 1]
        balcony = _rectangle_assembly(
            "exterior-balcony-01",
            "balcony",
            1,
            (bx0, -balcony_depth, bx0 + balcony_width, 0),
            {
                "kind": "balcony",
                "depth_mm": round(balcony_depth),
                "width_mm": round(balcony_width),
                "platform_z_mm": building["brief"]["floor_height_mm"] - 120,
                "rail_height_mm": 1100,
                "access_opening_id": glazed[0]["id"] if glazed else None,
                "planter_edge": preferences.exterior_theme == "earth_terracotta",
            },
            preferences.exterior_theme,
            [o["id"] for o in glazed],
        )
        assemblies.append(balcony)
    # A side verandah makes the arrival read as a usable L-shaped threshold
    # from the hero and right-side views without changing an interior cell.
    if preferences.exterior_theme == "warm_modern_minimal" and porch and v["right_mm"] >= 700:
        side_depth = min(1000, v["right_mm"])
        assemblies.append(_rectangle_assembly(
            "exterior-side-verandah-01",
            "verandah",
            0,
            (W - 1650, -250, W + side_depth, 2700),
            {
                "kind": "side_verandah",
                "depth_mm": round(side_depth),
                "length_mm": 2950,
                "platform_z_mm": -120,
                "canopy_z_mm": 2850,
                "support_count": 3,
            },
            preferences.exterior_theme,
            [porch["id"]],
        ))
    # The narrow left setback is treated as a real side garden room rather
    # than leftover lawn. It keeps the plot and rooms unchanged while giving
    # the opposite elevation a deliberate paved edge, planting and lighting.
    if preferences.exterior_theme == "warm_modern_minimal" and v["left_mm"] >= 700:
        side_x0 = -v["left_mm"] + 100
        side_x1 = -40
        side_y0 = 450
        side_y1 = max(side_y0 + 1800, D - 450)
        assemblies.append(_rectangle_assembly(
            "exterior-left-side-court-01",
            "side_courtyard",
            0,
            (side_x0, side_y0, side_x1, side_y1),
            {
                "kind": "side_courtyard",
                "path_width_mm": round(side_x1 - side_x0),
                "length_mm": round(side_y1 - side_y0),
                "platform_z_mm": -120,
                "planter_depth_mm": 300,
                "light_spacing_mm": 2200,
            },
            preferences.exterior_theme,
            [],
        ))
        screen_y0 = max(1600, round(D * 0.30))
        screen_y1 = min(D - 1200, screen_y0 + 2500)
        assemblies.append(_rectangle_assembly(
            "exterior-left-side-screen-01",
            "screen",
            0,
            (side_x0 + 80, screen_y0, side_x0 + 150, screen_y1),
            {
                "kind": "screen",
                "spacing_mm": 220,
                "height_mm": building["storeys"] * v["floor_height_mm"] - 650,
                "slat_depth_mm": 65,
            },
            preferences.exterior_theme,
            ["exterior-left-side-court-01"],
        ))
    if preferences.exterior_theme == "warm_modern_minimal":
        # A real blank stair bay gives the facade a dominant vertical anchor;
        # it is deliberately placed on the stair-facing blank wall region, and
        # stops short of the walk to the front door (on narrow plots it is left out).
        entry_w = next(o for o in building["openings"] if o["kind"] == "entry")["width"]
        wall_x1 = min(W - 360, 2550, ex - entry_w / 2 - 450)
        if wall_x1 - 180 >= 900:
            assemblies.append(_rectangle_assembly(
                "exterior-feature-wall-01",
                "feature_wall",
                0,
                (180, -560, wall_x1, -40),
                {
                    "kind": "feature_wall",
                    "height_mm": building["storeys"] * v["floor_height_mm"] - 80,
                    "cap_height_mm": 150,
                },
                preferences.exterior_theme,
                [],
            ))
    if preferences.exterior_theme == "warm_modern_minimal" and building["storeys"] > 1:
        # The first-floor frame only exists where there is a first floor to frame.
        assemblies.append(_rectangle_assembly(
            "exterior-front-frame-01",
            "facade_frame",
            1,
            (2500, -520, min(W - 180, 9800), -40),
            {
                "kind": "facade_frame",
                "height_mm": 3150,
                "depth_mm": 460,
                "side_piers_mm": 140,
                "top_band_mm": 150,
            },
            preferences.exterior_theme,
            [],
        ))
    if preferences.exterior_theme == "tropical_verandah" and porch:
        assemblies.append(_rectangle_assembly(
            "exterior-pergola-01",
            "pergola",
            0,
            (px0, -porch_depth, px0 + porch_width, 0),
            {"kind": "pergola", "spacing_mm": 420, "height_mm": 120, "z_mm": 2850},
            preferences.exterior_theme,
            [porch["id"]],
        ))
        assemblies.append(_rectangle_assembly(
            "exterior-screen-01",
            "screen",
            0,
            (px0, -porch_depth + 250, px0 + 90, -350),
            {"kind": "screen", "spacing_mm": 180, "height_mm": 2500, "slat_depth_mm": 55},
            preferences.exterior_theme,
            [porch["id"]],
        ))
    elif preferences.exterior_theme == "earth_terracotta" and front_available >= 700:
        screen_x = max(180, min(W - 700, px0 - 500))
        assemblies.append(_rectangle_assembly(
            "exterior-screen-01",
            "screen",
            0,
            (screen_x, -260, screen_x + 500, -150),
            {"kind": "screen", "spacing_mm": 180, "height_mm": building["storeys"] * v["floor_height_mm"] - 550, "slat_depth_mm": 95},
            preferences.exterior_theme,
            [],
        ))
    elif front_available >= 700:
        blade_x = max(180, min(W - 400, px0 - 450))
        assemblies.append(_rectangle_assembly(
            "exterior-accent-01",
            "accent",
            0,
            (blade_x, -140, blade_x + 260, -20),
            {"kind": "accent", "height_mm": building["storeys"] * v["floor_height_mm"] - 400, "depth_mm": 120},
            preferences.exterior_theme,
            [],
        ))
    from .modern_exterior import stair_tower_assembly
    tower = stair_tower_assembly(building, preferences.exterior_theme, _rectangle_assembly)
    if tower:
        assemblies.append(tower)
    opening_changes = _opening_proposals(building, theme, preferences.change_policy)
    landscape = _landscape(building, preferences.exterior_theme, porch)
    return [{
        "id": f"{preferences.exterior_theme}-candidate-01",
        "theme": preferences.exterior_theme,
        "assemblies": assemblies,
        "landscape": landscape,
        "opening_changes": opening_changes,
        "score": 100 + len(assemblies) * 8 + len(opening_changes) * 4,
        "rejections": [],
    }]


def evaluate_candidate(
    candidate: dict[str, Any],
    building: dict[str, Any],
    protected_geometry: str,
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plot = Polygon(building["plot"])
    errors: list[dict[str, Any]] = []
    ids: list[str] = []
    for assembly in candidate.get("assemblies", []):
        ids.append(assembly["id"])
        bounds = assembly["geometry"]["bounds_mm"]
        if not plot.covers(box(*bounds)):
            errors.append({"code": "ASSEMBLY_OUTSIDE_PLOT", "id": assembly["id"]})
        if any(float(x) <= 0 for x in (bounds[2] - bounds[0], bounds[3] - bounds[1])):
            errors.append({"code": "ASSEMBLY_DIMENSION", "id": assembly["id"]})
    for feature in candidate.get("landscape", {}).get("features", []):
        ids.append(feature["id"])
        if "polygon" in feature and not plot.covers(Polygon(feature["polygon"])):
            errors.append({"code": "LANDSCAPE_OUTSIDE_PLOT", "id": feature["id"]})
    if len(ids) != len(set(ids)):
        errors.append({"code": "DUPLICATE_EXTERIOR_ID"})
    if protected_geometry != protected_interior_fingerprint(building):
        errors.append({"code": "INTERIOR_FINGERPRINT_INPUT_CHANGED"})
    hosts = {w["id"]: w for w in building["walls"]}
    for change in candidate.get("opening_changes", []):
        opening = next((o for o in building["openings"] if o["id"] == change["opening_id"]), None)
        if opening is None:
            errors.append({"code": "OPENING_MISSING", "id": change["opening_id"]})
            continue
        wall = hosts[opening["wall_id"]]
        after = change["after"]
        length = math.dist(wall["a"], wall["b"])
        if after["offset"] < 0 or after["offset"] + after["width"] > length:
            errors.append({"code": "OPENING_REFINEMENT_OUTSIDE", "id": change["opening_id"]})
    result = deepcopy(candidate)
    result["rejections"] = errors
    result["accepted"] = not errors
    result["score"] = candidate.get("score", 0) - len(errors) * 1000
    return result


def select_candidate(candidates: list[dict[str, Any]], seed: int = 0) -> dict[str, Any]:
    accepted = [candidate for candidate in candidates if candidate.get("accepted")]
    if not accepted:
        reasons = [item for candidate in candidates for item in candidate.get("rejections", [])]
        raise DesignError("EXTERIOR_NO_FIT", "No exterior composition fits the actual plot and protected geometry.", {"rejections": reasons})
    return sorted(accepted, key=lambda candidate: (-candidate["score"], candidate["id"], seed))[0]


def build_exterior_change_set(
    candidate: dict[str, Any],
    building: dict[str, Any],
    preferences: DesignPreferences,
    anchors: list[dict[str, Any]],
) -> dict[str, Any]:
    before = protected_interior_fingerprint(building)
    change_set = {
        "schema": "floorforge.change-set/0.1",
        "id": sha({
            "candidate": candidate,
            "preferences": asdict(preferences),
            "before": before,
        })[:20],
        "theme": candidate["theme"],
        "theme_version": preferences.theme_version,
        "change_policy": preferences.change_policy,
        "anchors": anchors,
        "opening_changes": candidate.get("opening_changes", []),
        "assemblies": candidate.get("assemblies", []),
        "landscape": candidate.get("landscape", {}),
        "protected_interior_before": before,
        "impact": {
            "opening_refinements": len(candidate.get("opening_changes", [])),
            "exterior_assemblies": len(candidate.get("assemblies", [])),
            "landscape_features": len(candidate.get("landscape", {}).get("features", [])),
            "interior_layout": "unchanged",
            "structural_review": "outstanding",
        },
    }
    return change_set


def apply_exterior_preferences(building: dict[str, Any]) -> dict[str, Any]:
    """Return one coordinated building revision for all downstream consumers."""
    preferences = preferences_from_brief(building["brief"])
    anchors = derive_facade_anchors(building)
    protected_before = protected_interior_fingerprint(building)
    candidates = generate_exterior_candidates(building, preferences)
    if building.get('planning',{}).get('custom'):
        # Exact authored openings and floor topology outrank facade refinements.
        for candidate in candidates:
            candidate['opening_changes']=[]
            candidate['assemblies']=[a for a in candidate.get('assemblies',[]) if a['geometry'].get('kind') in ('porch','verandah','screen','accent','carport')]
    evaluated = [
        evaluate_candidate(candidate, building, protected_before)
        for candidate in candidates
    ]
    selected = select_candidate(evaluated, preferences.seed)
    change_set = build_exterior_change_set(selected, building, preferences, anchors)
    revision = deepcopy(building)
    opening_map = {o["id"]: o for o in revision["openings"]}
    applied_openings = []
    for change in selected.get("opening_changes", []):
        opening = opening_map[change["opening_id"]]
        before = deepcopy(opening)
        opening.update(change["after"])
        applied_openings.append({
            **change,
            "before_semantic": before,
            "after_semantic": deepcopy(opening),
            "dependents": [
                "wall_aperture",
                "reveal_sill_lintel",
                "frame_mullions_glazing",
                "curtain_attachment",
                "collision",
                "drawing_dimension",
                "opening_schedule",
                "geometry_exports",
            ],
            "review_status": "accepted_for_geometry_screen",
        })
    change_set["opening_changes"] = applied_openings
    protected_after = protected_interior_fingerprint(revision)
    if protected_before != protected_after:
        raise DesignError("INTERIOR_LOCK", "Exterior refinement changed protected room or stair geometry.")
    exterior = {
        "schema": "floorforge.exterior/0.1",
        "theme": preferences.exterior_theme,
        "theme_version": preferences.theme_version,
        "interior_theme": preferences.interior_theme,
        "change_policy": preferences.change_policy,
        "interior_layout_locked": preferences.interior_layout_locked,
        "revision": change_set["id"],
        "anchors": anchors,
        "change_set": change_set,
        "assemblies": selected.get("assemblies", []),
        "landscape": selected.get("landscape", {}),
        "opening_changes": applied_openings,
        "protected_interior_before": protected_before,
        "protected_interior_after": protected_after,
        "candidate_audit": {
            "selected": selected["id"],
            "score": selected["score"],
            "rejections": [
                {"id": candidate["id"], "rejections": candidate.get("rejections", [])}
                for candidate in evaluated
                if candidate["id"] != selected["id"]
            ],
        },
        "review": {
            "geometry_screen": "preliminary_geometry_pass",
            "structural_review": "OUTSTANDING",
            "regulatory_review": "OUTSTANDING",
            "accessibility_review": "OUTSTANDING",
            "visual_review": "PENDING_OWNER_REVIEW",
        },
    }
    revision["schema"] = "floorforge.building/0.4" if building.get("planning",{}).get("custom") else "floorforge.building/0.3"
    revision["exterior"] = exterior
    return revision


def exterior_review(building: dict[str, Any]) -> dict[str, Any]:
    exterior = building.get("exterior")
    if not exterior:
        return {
            "theme": "current",
            "geometry_screen": "NOT_RUN",
            "protected_interior": "not_fingerprinted",
            "structural_review": "OUTSTANDING",
            "regulatory_review": "OUTSTANDING",
            "accessibility_review": "OUTSTANDING",
        }
    return {
        "theme": exterior["theme"],
        "theme_label": EXTERIOR_THEMES[exterior["theme"]]["label"],
        "revision": exterior["revision"],
        "geometry_screen": exterior["review"]["geometry_screen"],
        "protected_interior": "unchanged" if exterior["protected_interior_before"] == exterior["protected_interior_after"] else "CHANGED",
        "opening_refinements": len(exterior["opening_changes"]),
        "assemblies": len(exterior["assemblies"]),
        "landscape_features": len(exterior.get("landscape", {}).get("features", [])),
        "assembly_count": len(exterior["assemblies"]),
        "landscape_feature_count": len(exterior.get("landscape", {}).get("features", [])),
        "structural_review": exterior["review"]["structural_review"],
        "regulatory_review": exterior["review"]["regulatory_review"],
        "accessibility_review": exterior["review"]["accessibility_review"],
    }
