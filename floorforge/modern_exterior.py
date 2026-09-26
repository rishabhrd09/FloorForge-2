"""Modern Tropical exterior composition (plan millimetres, road at local -Y).

A deterministic, plot-aware design recipe distilled from contemporary tropical
homes: white rendered volumes with slim black full-height glazing, a floating
roof slab, a cantilevered entrance slab, a stamped-cobble arrival court, pebble
beds with steel edging, lawns crossed by stepping stones, sculpted planting and
lantern light. Every polygon is clipped to the supplied plot and kept clear of
the building footprint; point features are placed inside the plot. It remains a
preliminary visual/landscape proposal, not an approved design.
"""
from __future__ import annotations

import math
from typing import Any

from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union

THEME = "modern_tropical"
BOUNDARY_WALL_MM = 150
DRIP_STRIP_MM = 450


def _poly(p) -> list[list[int]]:
    return [[round(x), round(y)] for x, y in list(p.exterior.coords)[:-1]]


def _parts(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]


def _fit_opening(length: float, center: float, width: float, blocked: list[tuple[float, float]], margin: float):
    lo, hi = margin, length - margin
    for a, b in blocked:
        a -= margin
        b += margin
        if b <= center:
            lo = max(lo, b)
        elif a >= center:
            hi = min(hi, a)
        else:
            return None
    if hi - lo < 600:
        return None
    w = min(width, hi - lo)
    off = min(max(center - w / 2, lo), hi - w)
    return round(off), round(w)


def modern_opening_proposals(building: dict[str, Any], classify) -> list[dict[str, Any]]:
    """Full-height glazing for living rooms, tall bedroom windows, worktop-height kitchen glazing."""
    hosts = {w["id"]: w for w in building["walls"]}
    kinds = {s["id"]: s["kind"] for s in building["spaces"]}
    wall_h = building["brief"]["floor_height_mm"] - 150
    out = []
    for o in building["openings"]:
        if o["kind"] not in ("window", "glazed"):
            continue
        wall = hosts[o["wall_id"]]
        if o["kind"] == "window" and not wall["external"]:
            continue
        length = math.dist(wall["a"], wall["b"])
        role = classify(o, [kinds[r] for r in wall["rooms"]])
        blocked = [(p["offset"], p["offset"] + p["width"]) for p in building["openings"] if p["wall_id"] == wall["id"] and p["id"] != o["id"]]
        center = o["offset"] + o["width"] / 2
        if role == "living_feature":
            target, sill, height = min(5600, length * .84), 0, min(wall_h - 300, 2700)
        elif role == "bedroom_primary":
            target, sill, height = min(2800, length * .62), 450, min(wall_h - 750, 2250)
        elif role == "kitchen_worktop":
            target, sill, height = min(2400, length * .55), 1000, 1350
        elif role == "balcony_access":
            target, sill, height = min(length - 240, o["width"] + 900), o["sill"], min(wall_h - 300, 2600)
        elif role == "bathroom_privacy":
            target, sill, height = min(1400, length * .5), 1650, 700
        else:
            continue
        fit = _fit_opening(length, center, target, blocked, 300 if o["kind"] == "window" else 120)
        if not fit:
            continue
        offset, width = fit
        height = min(height, wall_h - sill)
        if width <= o["width"] and sill == o["sill"] and height == o["height"]:
            continue
        out.append({
            "id": f"{o['id']}-refinement",
            "opening_id": o["id"],
            "role": role,
            "before": {"offset": o["offset"], "width": o["width"], "sill": o["sill"], "height": o["height"]},
            "after": {"offset": offset, "width": width, "sill": sill, "height": height},
            "reason": "Modern Tropical glazing: full-height living glass, tall bedroom windows and worktop-height kitchen glazing; host wall and neighbouring openings checked.",
            "review_status": "geometry_screen_pending",
        })
    return out


def modern_candidate(building: dict[str, Any], preferences, helpers: dict[str, Any]) -> dict[str, Any]:
    rect = helpers["rectangle_assembly"]
    v = building["brief"]
    fp = Polygon(building["footprint"])
    W, D = fp.bounds[2], fp.bounds[3]
    xmin, ymin, xmax, ymax = Polygon(building["plot"]).bounds
    ex, _ = helpers["front_entry"](building)
    F, Lm, Rm, RE = v["front_mm"], v["left_mm"], v["right_mm"], v["rear_mm"]
    H = v["floor_height_mm"]
    entry_id = next(o["id"] for o in building["openings"] if o["kind"] == "entry")
    assemblies: list[dict[str, Any]] = []
    front_available = max(0, F - 250)
    porch = None
    balcony = None
    if front_available >= 700:
        depth = min(2100, max(900, front_available - (1500 if F >= 2600 else 700)), front_available)
        width = min(4600, max(2600, W * .42), W)
        px0 = max(0, min(W - width, ex - width / 2))
        two_storey = building["storeys"] > 1
        overhang = max(0, min(350, F - depth - 450))
        porch = rect("exterior-porch-01", "porch", 0, (px0, -depth, px0 + width, 0), {
            "kind": "porch", "style": "cantilever", "depth_mm": round(depth), "width_mm": round(width),
            "platform_z_mm": -150, "canopy_z_mm": H - 280 if two_storey else 2950, "canopy_thickness_mm": 260,
            "canopy_overhang_mm": round(overhang), "support_count": 0, "canopy_is_balcony": two_storey,
        }, THEME, [entry_id])
        assemblies.append(porch)
        if two_storey:
            terrace = next((s for s in building["spaces"] if s["kind"] == "terrace"), None)
            center = Polygon(terrace["polygon"]).centroid.x if terrace else ex
            bw = min(4800, W * .62)
            bx0 = max(0, min(W - bw, center - bw / 2))
            x0, x1 = min(bx0, px0), max(bx0 + bw, px0 + width)
            glazed = [o for o in building["openings"] if o["kind"] == "glazed" and o["floor"] == 1]
            balcony = rect("exterior-balcony-01", "balcony", 1, (x0, -depth, x1, 0), {
                "kind": "balcony", "style": "frameless_glass", "depth_mm": round(depth), "width_mm": round(x1 - x0),
                "platform_z_mm": H - 30, "slab_thickness_mm": 250, "rail_height_mm": 1100,
                "access_opening_id": glazed[0]["id"] if glazed else None, "planter_edge": False,
            }, THEME, [o["id"] for o in glazed])
            assemblies.append(balcony)
    # Stone-clad feature panel on the widest blank stretch of the front facade.
    anchors = helpers["anchors"](building)
    best = None
    for a in anchors:
        if a["floor_id"] != 0 or a["outward_normal"][1] > -.9:
            continue
        for g in a["available_attachment_regions"]:
            x_a = a["origin"][0] + a["tangent"][0] * g["start_mm"]
            x_b = a["origin"][0] + a["tangent"][0] * g["end_mm"]
            lo, hi = sorted((x_a, x_b))
            lo, hi = max(lo, 0), min(hi, W)
            if porch:
                p0, _, p1, _ = porch["geometry"]["bounds_mm"]
                if lo < p1 and hi > p0:
                    hi = min(hi, p0 - 120) if (lo + hi) / 2 < (p0 + p1) / 2 else hi
                    lo = max(lo, p1 + 120) if (lo + hi) / 2 >= (p0 + p1) / 2 else lo
            if hi - lo >= 1100 and (best is None or hi - lo > best[1] - best[0]):
                best = (lo, hi)
    if best:
        lo, hi = best
        w = min(2800, hi - lo - 160)
        cx = (lo + hi) / 2
        assemblies.append(rect("exterior-feature-wall-01", "feature_wall", 0, (cx - w / 2, -70, cx + w / 2, 0), {
            "kind": "cladding", "height_mm": building["storeys"] * H - 120, "material": "cladding",
            "slats": True,
        }, THEME, []))
    carport = None
    if v["parking"] and F >= 5500 and porch:
        cw, cd = 3200, min(5600, F - 450)
        p0, _, p1, _ = porch["geometry"]["bounds_mm"]
        right = (p1 + 250, p1 + 250 + cw)
        left = (p0 - 250 - cw, p0 - 250)
        inner0, inner1 = xmin + BOUNDARY_WALL_MM + 50, xmax - BOUNDARY_WALL_MM - 50
        choice = right if right[1] <= inner1 else left if left[0] >= inner0 else None
        if choice:
            carport = rect("exterior-carport-01", "carport", 0, (choice[0], -cd - 250, choice[1], -250), {
                "kind": "carport", "roof_z_mm": 2750, "column_count": 4, "slab_thickness_mm": 220,
            }, THEME, [])
            assemblies.append(carport)
    patio = None
    if RE >= 2600:
        pd = min(3400, RE - 700)
        pw = min(4800, W * .55)
        px = W / 2
        patio = rect("exterior-pergola-01", "pergola", 0, (px - pw / 2, D + 60, px + pw / 2, D + 60 + pd), {
            "kind": "pergola", "style": "glass_roof", "z_mm": 2750, "spacing_mm": 900, "height_mm": 160,
        }, THEME, [])
        assemblies.append(patio)
    landscape = modern_landscape(building, porch, carport, patio)
    return {
        "id": f"{THEME}-candidate-01",
        "theme": THEME,
        "assemblies": assemblies,
        "landscape": landscape,
        "opening_changes": modern_opening_proposals(building, helpers["classify"]),
        "score": 100 + len(assemblies) * 8,
        "rejections": [],
    }


def modern_landscape(building: dict[str, Any], porch, carport, patio) -> dict[str, Any]:
    v = building["brief"]
    fp = Polygon(building["footprint"])
    W, D = fp.bounds[2], fp.bounds[3]
    plot = Polygon(building["plot"])
    xmin, ymin, xmax, ymax = plot.bounds
    entry = next(o for o in building["openings"] if o["kind"] == "entry")
    wall = next(w for w in building["walls"] if w["id"] == entry["wall_id"])
    length = math.dist(wall["a"], wall["b"])
    ex = wall["a"][0] + (wall["b"][0] - wall["a"][0]) / length * (entry["offset"] + entry["width"] / 2)
    F, Lm, Rm, RE = v["front_mm"], v["left_mm"], v["right_mm"], v["rear_mm"]
    wt = BOUNDARY_WALL_MM
    inner = box(xmin + wt, ymin + wt + 30, xmax - wt, ymax - wt)
    house = fp.buffer(30, join_style=2)
    features: list[dict[str, Any]] = []
    occupied = [house]
    hardscape: list[Any] = []

    def add_poly(ident, kind, geom, **extra):
        geom = geom.intersection(inner).difference(house)
        for i, part in enumerate(_parts(geom)):
            part = part.buffer(0)
            if part.area < 150_000:
                continue
            features.append({"id": ident if i == 0 else f"{ident}-{i}", "kind": kind, "polygon": _poly(part), **extra})
            occupied.append(part)
            if kind in ("court", "patio", "deck"):
                hardscape.append(part)

    def add_point(ident, kind, x, y, **extra):
        pt = Point(x, y)
        if not inner.buffer(-120).contains(pt) or house.buffer(150).contains(pt):
            return False
        if kind in ("plant", "tree") and any(h.buffer(120).contains(pt) for h in hardscape):
            return False
        features.append({"id": ident, "kind": kind, "position_mm": [round(x), round(y)], **extra})
        return True

    gate_w = 3400 if v["parking"] else 2600
    gate_center = ex
    if carport:
        c0, _, c1, _ = carport["geometry"]["bounds_mm"]
        gate_center = (min(c0, ex - 700) + max(c1, ex + 700)) / 2
        gate_w = min(max(c1, ex + 700) - min(c0, ex - 700), 6000)
    boundary = {
        "gate_center_mm": round(gate_center), "gate_width_mm": round(gate_w), "movement_clearance_mm": 500,
        "style": "rendered_wall_black_slats", "front_wall_height_mm": 1500, "side_wall_height_mm": 1850,
        "wall_thickness_mm": wt, "review_status": "geometry_screen_pending",
    }
    front_y0 = ymin + wt + 30
    landing_y = -porch["geometry"]["depth_mm"] if porch else 0
    steps_y = landing_y - 620 if porch else -900
    if porch:
        p0, _, p1, _ = porch["geometry"]["bounds_mm"]
        hardscape.append(box(p0, steps_y, p1, 0))
        occupied.append(box(p0, steps_y, p1, 0))

    # ---- Front yard -------------------------------------------------------
    if F >= 700:
        half = max(900, min(1500, gate_w / 2))
        cx0, cx1 = max(xmin + wt, ex - half), min(xmax - wt, ex + half)
        court = box(cx0, front_y0, cx1, max(front_y0 + 450, steps_y))
        if porch:
            p0, p_y0, p1, _ = porch["geometry"]["bounds_mm"]
            court = court.union(box(p0 - 300, steps_y - 450, p1 + 300, steps_y + 1))
        if carport:
            c0, cy0, c1, cy1 = carport["geometry"]["bounds_mm"]
            court = court.union(box(c0 - 150, front_y0, c1 + 150, cy1 + 150))
        add_poly("site-arrival-court", "court", court, material_role="site.cobble")
        court_shape = unary_union([f for f in occupied[1:]]) if len(occupied) > 1 else court
        bed_d = min(950, max(500, F * .24))
        beds = box(xmin + wt, front_y0, xmax - wt, front_y0 + bed_d).difference(court_shape.buffer(120))
        for i, part in enumerate(_parts(beds)):
            if part.area < 400_000:
                continue
            add_poly(f"front-bed-{i}", "pebble_bed", part, edging=True, material_role="site.pebble")
            bx0, by0, bx1, by1 = part.bounds
            n = max(1, int((bx1 - bx0) // 1350))
            for k in range(n):
                x = bx0 + (k + .5) * (bx1 - bx0) / n
                add_point(f"front-bed-{i}-conifer-{k}", "plant", x, (by0 + by1) / 2, species="conifer_column", scale=.9 + .1 * ((k * 7) % 3) / 2)
                if k < n - 1:
                    add_point(f"front-bed-{i}-ball-{k}", "plant", bx0 + (k + 1) * (bx1 - bx0) / n, (by0 + by1) / 2 - 60, species="shrub_round", scale=.72)
                if k % 2 == 0:
                    add_point(f"front-bed-{i}-lantern-{k}", "lantern", x + 380, by1 - 160)
        # Pebble drip strip against the facade (keeps render clean, reads as crafted edge).
        drip = box(-400, -DRIP_STRIP_MM, W + 400, 0).difference(court_shape.buffer(80))
        if porch:
            drip = drip.difference(box(porch["geometry"]["bounds_mm"][0] - 200, landing_y - 700, porch["geometry"]["bounds_mm"][2] + 200, 0))
        add_poly("front-drip-strip", "pebble_bed", drip, edging=True, material_role="site.pebble")
        # Lawn fills what remains between the planting strip and the house.
        taken = unary_union(occupied)
        lawn = box(xmin + wt, front_y0 + bed_d + 120, xmax - wt, -DRIP_STRIP_MM - 20).difference(taken.buffer(100))
        lawn_parts = [p for p in _parts(lawn) if p.area > 1_200_000]
        for i, part in enumerate(lawn_parts):
            add_poly(f"front-lawn-{i}", "lawn", part, material_role="site.lawn")
        # Specimen planting: a frangipani on the larger lawn, strelitzia at the house corner,
        # spiral topiaries flanking the entrance steps, cordylines for colour.
        if lawn_parts:
            big = max(lawn_parts, key=lambda p: p.area)
            c = big.representative_point()
            bx0, by0, bx1, by1 = big.bounds
            tx = bx0 + (bx1 - bx0) * (.35 if (bx0 + bx1) / 2 < ex else .65)
            ty = (by0 + by1) / 2
            if big.buffer(-500).contains(Point(tx, ty)) and add_point("front-specimen-frangipani", "tree", tx, ty, species="frangipani", scale=1.0 if F >= 2800 else .8, uplight=True):
                pass
            elif big.buffer(-400).contains(c):
                add_point("front-specimen-frangipani", "tree", c.x, c.y, species="frangipani", scale=.85, uplight=True)
            # Stepping stones from the court across the lawn towards the side passage.
            sx_dir = -1 if (bx0 + bx1) / 2 < ex else 1
            y_line = (by0 + by1) / 2 + (350 if F >= 2600 else 0)
            stones = []
            x = (bx1 - 350) if sx_dir < 0 else (bx0 + 350)
            end = bx0 + 300 if sx_dir < 0 else bx1 - 300
            while (x - end) * sx_dir < 0 and len(stones) < 14:
                s = box(x - 250, y_line - 175, x + 250, y_line + 175)
                if big.buffer(-60).contains(s) and not s.buffer(250).contains(Point(tx, ty)):
                    stones.append(_poly(s))
                x += 700 * sx_dir
            if stones:
                features.append({"id": "front-stepping-stones", "kind": "stepping_stones", "stones": stones, "material_role": "site.stone_pad"})
        if porch:
            p0, _, p1, _ = porch["geometry"]["bounds_mm"]
            for i, x in enumerate((p0 - 380, p1 + 380)):
                add_point(f"entry-topiary-{i}", "plant", x, steps_y + 250, species="topiary_spiral", scale=.95)
            for i, x in enumerate((p0 + 420, p1 - 420)):
                add_point(f"entry-planter-{i}", "planter", x, landing_y + 380, shape="faceted", size_mm=[520, 520, 620], species="shrub_round", scale=.52, on="landing")
        for i, x in enumerate((.35, .92)):
            add_point(f"front-strelitzia-{i}", "plant", W * x if x < .5 else W - 700, -DRIP_STRIP_MM - 520, species="strelitzia", scale=.9)
        # Lanterns along the court edges.
        cy = front_y0 + 600
        k = 0
        while cy < steps_y - 300 and k < 8:
            for side, x in (("l", cx0 - 260), ("r", cx1 + 260)):
                add_point(f"court-lantern-{side}-{k}", "lantern", x, cy)
            cy += 1800
            k += 1

    # ---- Side passages -------------------------------------------------------
    for side, gap in (("left", Lm), ("right", Rm)):
        if gap < 700:
            continue
        if side == "left":
            x0, x1 = xmin + wt, -60
        else:
            x0, x1 = W + 60, xmax - wt
        y0 = 0 if F >= 700 else ymin + wt
        y1 = D + min(RE, 600)
        passage = box(x0, y0, x1, y1)
        add_poly(f"{side}-passage", "pebble_bed", passage, edging=True, material_role="site.pebble")
        wid = x1 - x0
        stone_w = min(620, wid - 260)
        if stone_w >= 380:
            cx = (x0 + x1) / 2
            stones = []
            y = y0 + 500
            while y < y1 - 400 and len(stones) < 40:
                stones.append(_poly(box(cx - stone_w / 2, y - 200, cx + stone_w / 2, y + 200)))
                y += 720
            features.append({"id": f"{side}-passage-stones", "kind": "stepping_stones", "stones": stones, "material_role": "site.stone_pad"})
        # Planting against the boundary wall; wall lights on the house side.
        edge_x = x0 + 230 if side == "left" else x1 - 230
        yy = y0 + 1400
        i = 0
        while yy < y1 - 900:
            species = "grass_ornamental" if i % 3 == 1 else "shrub_round"
            add_point(f"{side}-passage-plant-{i}", "plant", edge_x, yy, species=species, scale=.55 if species == "shrub_round" else .75)
            yy += 2300
            i += 1
        yy = y0 + 1800
        i = 0
        while yy < y1 - 1000:
            features.append({"id": f"{side}-wall-light-{i}", "kind": "wall_light", "position_mm": [round(-10 if side == "left" else W + 10), round(yy)], "height_mm": 1900, "facing": -1 if side == "left" else 1})
            yy += 3200
            i += 1

    # ---- Rear garden ---------------------------------------------------------
    if RE >= 700:
        rear = box(xmin + wt, D + 60, xmax - wt, ymax - wt)
        if patio:
            q0, qy0, q1, qy1 = patio["geometry"]["bounds_mm"]
            add_poly("rear-patio", "patio", box(q0, qy0, q1, qy1), material_role="site.encaustic")
            features.append({"id": "rear-dining-set", "kind": "outdoor_dining", "position_mm": [round((q0 + q1) / 2), round((qy0 + qy1) / 2)]})
        taken = unary_union(occupied)
        depth = RE - wt - 60
        if depth >= 1200:
            hedge_y = ymax - wt - 320
            L = (xmax - wt - 200) - (xmin + wt + 200)
            features.append({"id": "rear-hedge", "kind": "hedge", "position_mm": [round((xmin + xmax) / 2), round(hedge_y)], "size_mm": [round(L), 480, 1400], "rotation": 0})
            lawn = rear.difference(taken.buffer(80)).difference(box(xmin, hedge_y - 300, xmax, ymax))
        else:
            lawn = rear.difference(taken.buffer(80))
        for i, part in enumerate([p for p in _parts(lawn) if p.area > 900_000]):
            add_poly(f"rear-lawn-{i}", "lawn", part, material_role="site.lawn")
        if depth >= 1500:
            for i, x in enumerate((xmin + wt + 900, xmax - wt - 900)):
                add_point(f"rear-tree-{i}", "tree", x, D + 60 + depth * .45, species="tree_standard", scale=.85)

    return {
        "schema": "floorforge.landscape/0.2",
        "arrival_sequence": ["road_edge", "gate", "arrival_court", "entrance_steps", "landing", "main_door"],
        "features": features,
        "boundary": boundary,
        "outside_property_context": "viewer_context_only",
        "design_notes": "Stamped-cobble court, pebble beds with steel edging, lawns with stepping stones, lantern light and layered tropical planting.",
    }
