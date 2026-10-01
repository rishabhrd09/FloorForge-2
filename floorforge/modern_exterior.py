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

from .frontage import plan_frontage

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
        if o["kind"] == "entry" and o["floor"] == 0:
            # A tall pivot entrance door whose head lines up with the full-height glazing.
            height = min(wall_h - 300, 2600)
            if height > o["height"]:
                out.append({
                    "id": f"{o['id']}-refinement", "opening_id": o["id"], "role": "entrance_pivot",
                    "before": {"offset": o["offset"], "width": o["width"], "sill": o["sill"], "height": o["height"]},
                    "after": {"offset": o["offset"], "width": o["width"], "sill": 0, "height": height},
                    "reason": "Modern Tropical entrance: a tall timber pivot door in a black steel portal, head aligned with the full-height glazing.",
                    "review_status": "geometry_screen_pending",
                })
            continue
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
        step = 150 if role == "bathroom_privacy" else 300
        snapped = max(600, width // step * step)
        if snapped < width:
            offset, width = round(offset + (width - snapped) / 2), snapped
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


def stair_tower_assembly(building: dict[str, Any], theme_id: str, rect):
    """The stair carried on to the roof in a stone-clad tower (the headroom over the roof access): the usual
    vertical accent of a real two-storey home. On the modern theme the roof beside it becomes an open terrace."""
    if building["storeys"] < 2:
        return None
    top_floor = building["storeys"] - 1
    stair = next((s for s in building["spaces"] if s["floor"] == top_floor and s["kind"] == "stair"), None)
    if not stair:
        return None
    sx0, sy0, sx1, sy1 = Polygon(stair["polygon"]).bounds
    return rect("exterior-stair-tower-01", "stair_tower", top_floor, (sx0, sy0, sx1, sy1), {
        "kind": "stair_tower", "height_mm": 2700, "material": "cladding", "roof_access": True,
        "roof_terrace": theme_id == THEME,
    }, theme_id, [])


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
        # L-shaped entrance: the flight of steps covers the door and returns down the side facing the wider
        # yard (where the drive goes); a sit-out with a bench and planter fills the other end of the landing,
        # its corner marked by a stone-clad column under the canopy.
        clear = next(o for o in building["openings"] if o["kind"] == "entry")["width"] / 2 + 300
        room = {"left": ex - clear - px0, "right": px0 + width - ex - clear}
        beyond = {"left": px0 - xmin - BOUNDARY_WALL_MM, "right": xmax - BOUNDARY_WALL_MM - px0 - width}
        flight_side = "left" if beyond["left"] >= beyond["right"] else "right"
        sit_side = "right" if flight_side == "left" else "left"
        if room[sit_side] < 900 <= room[flight_side]:
            sit_side, flight_side = flight_side, sit_side
        sitout = None
        if room[sit_side] >= 900:
            sitout = [round(px0), round(ex - clear)] if sit_side == "left" else [round(ex + clear), round(px0 + width)]
        return_len = min(depth - 300, 1200) if beyond[flight_side] >= 1500 and depth >= 900 else 0
        porch = rect("exterior-porch-01", "porch", 0, (px0, -depth, px0 + width, 0), {
            "kind": "porch", "style": "cantilever", "depth_mm": round(depth), "width_mm": round(width),
            "platform_z_mm": -150, "canopy_z_mm": H - 280 if two_storey else 2950, "canopy_thickness_mm": 260,
            "canopy_overhang_mm": round(overhang), "support_count": 1 if sitout else 0, "canopy_is_balcony": two_storey,
            "flight_side": flight_side, "sitout_x_mm": sitout, "return_steps_mm": round(return_len),
            "step_lighting": "led_under_nosing", "door": "timber_pivot_in_black_portal",
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
    tower = stair_tower_assembly(building, THEME, rect)
    if tower:
        assemblies.append(tower)
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
    if porch and building.get('planning', {}).get('entranceStyle') == 'wall-supported':
        # Resolve the entrance independently of the already designed upper balcony
        # and facade accents. No porch base or column projects into the car gateway.
        pg = porch['geometry']
        half = next(o for o in building['openings'] if o['kind'] == 'entry')['width'] / 2
        pg.update(bounds_mm=[round(ex-half-450), -1200, round(ex+half+450), 0],
                  depth_mm=1200, width_mm=round(2*half+900), sitout_x_mm=None,
                  return_steps_mm=0, support_count=0, wall_supported=True,
                  canopy_bounds_mm=[pg['bounds_mm'][0], -1200, round(ex+half+600), 0])
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
            if kind in ("court", "path", "patio", "deck"):
                hardscape.append(part)

    def add_point(ident, kind, x, y, **extra):
        pt = Point(x, y)
        if not inner.buffer(-120).contains(pt) or house.buffer(150).contains(pt):
            return False
        if kind in ("plant", "tree", "lantern") and any(h.buffer(120).contains(pt) for h in hardscape):
            return False
        features.append({"id": ident, "kind": kind, "position_mm": [round(x), round(y)], **extra})
        return True

    steps_x = carport_x = None
    if porch:
        pg = porch["geometry"]
        s0, s1 = pg["bounds_mm"][0::2]
        ret = 700 if pg.get("return_steps_mm") else 0
        steps_x = (s0 - (ret if pg.get("flight_side") == "left" else 0), s1 + (ret if pg.get("flight_side") == "right" else 0))
    if carport:
        carport_x = tuple(carport["geometry"]["bounds_mm"][0::2])
    side_parking = bool(building.get('planning', {}).get('custom') and v['parking'] and Rm >= 3000 and not carport)
    if side_parking:
        carport_x = (xmax-Rm+(150 if Rm < 3300 else 300), xmax-(300 if Rm < 3300 else 450))
    elif building.get('planning', {}).get('custom') and v['parking'] and not carport:
        # An irregular rear wing may touch the boundary while the front-right
        # parking bay remains open. Test actual geometry, not a uniform setback.
        bay = box(xmax-3000, ymin+200, xmax-200, ymin+5700)
        if inner.covers(bay) and not house.intersects(bay):
            side_parking = True
            carport_x = (xmax-3000, xmax-250)
    frontage = plan_frontage(plot.bounds, ex, steps_x=steps_x, parking=v["parking"], front_mm=F, carport_x=carport_x, wall_mm=wt)
    boundary = {
        **frontage, "movement_clearance_mm": 500,
        "style": "rendered_wall_black_slats", "front_wall_height_mm": 1500, "side_wall_height_mm": 1850,
        "wall_thickness_mm": wt, "review_status": "geometry_screen_pending",
    }
    ped = next(g for g in frontage["gates"] if g["kind"] == "pedestrian")
    vehicle = next((g for g in frontage["gates"] if g["kind"] == "vehicle"), None)
    if porch and porch['geometry'].get('wall_supported'):
        # This shallow court has no safe inward swing over its entry steps.
        # Park the unchanged slatted leaf inside the long boundary wall to the left.
        ped.update(operation='sliding', park='left', travel_mm=ped['x1_mm']-ped['x0_mm']+40)
        if vehicle:vehicle.update(operation='swing', leaves=2, open_deg=90)
    front_y0 = ymin + wt + 30
    landing_y = -porch["geometry"]["depth_mm"] if porch else 0
    steps_y = landing_y - 620 if porch else -900
    if porch:
        p0, _, p1, _ = porch["geometry"]["bounds_mm"]
        hardscape.append(box(p0, steps_y, p1, 0))
        occupied.append(box(p0, steps_y, p1, 0))
        if porch["geometry"].get("return_steps_mm"):
            rx = p0 - 700 if porch["geometry"]["flight_side"] == "left" else p1
            ret = box(rx, landing_y - 1, rx + 700, landing_y + porch["geometry"]["return_steps_mm"])
            hardscape.append(ret)
            occupied.append(ret)

    # ---- Front yard -------------------------------------------------------
    if F >= 700:
        # Entrance path of large slabs from the pedestrian gate to the steps: straight when the gate is on the
        # steps' line, otherwise turning once across the court; an apron of the same slabs meets the steps.
        g0, g1 = ped["x0_mm"] + 40, ped["x1_mm"] - 40
        s0, s1 = (p0 + 250, p1 - 250) if porch else (ex - 700, ex + 700)
        top = steps_y if porch else -DRIP_STRIP_MM - 40
        if g0 >= s0 - 1 and g1 <= s1 + 1:
            path = box(g0, front_y0, g1, top)
        else:
            half = (g1 - g0) / 2
            turn = front_y0 + max(half, min(900, (top - front_y0) * .45))
            to = min(max(ex, s0 + half), s1 - half)
            path = unary_union([box(g0, front_y0, g1, turn + half), box(min(g0, to - half), turn - half, max(g1, to + half), turn + half),
                                box(to - half, turn - half, to + half, top)])
        if porch:
            path = path.union(box(p0 - 300, steps_y - 450, p1 + 300, steps_y + 1))
            if porch["geometry"].get("return_steps_mm"):
                # The apron turns the corner to the foot of the returning steps.
                rx = p0 - 1000 if porch["geometry"]["flight_side"] == "left" else p1 + 700
                path = path.union(box(rx, steps_y - 450, rx + 300, landing_y + porch["geometry"]["return_steps_mm"]))
        add_poly("site-entry-path", "path", path, material_role="site.flagstone")
        # Driveway behind the vehicle gate: cobbles up to the facade's drip strip, or under the carport.
        if vehicle:
            d0, d1 = vehicle["x0_mm"] + 60, vehicle["x1_mm"] - 60
            drive = box(d0, front_y0, d1, -DRIP_STRIP_MM - 40)
            if carport:
                c0, cy0, c1, cy1 = carport["geometry"]["bounds_mm"]
                drive = box(d0, front_y0, d1, cy0 + 10).union(box(c0 - 150, cy0, c1 + 150, cy1 + 150))
            elif side_parking:
                lane_end = min(ymax-300, front_y0+6200)
                if building.get('planning', {}).get('custom'):
                    obstruction=house.intersection(box(carport_x[0],0,carport_x[1],ymax))
                    if not obstruction.is_empty:
                        lane_end=max(lane_end,obstruction.bounds[1]-60)
                drive = drive.union(box(carport_x[0], front_y0, carport_x[1], lane_end))
            add_poly("site-driveway", "court", drive.difference(path.buffer(60)), material_role="site.limestone" if any(r.get("finishStyle")=="warm-stone" for r in building["spaces"]) else "site.cobble")
        cx0, cx1 = g0, g1
        court_shape = unary_union([f for f in occupied[1:]]) if len(occupied) > 1 else path
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
            pg = porch["geometry"]
            ret_x = (p0 - 700 if pg.get("flight_side") == "left" else p1 + 700) if pg.get("return_steps_mm") else None
            for i, x in enumerate((p0 - 380, p1 + 380)):
                if ret_x is not None and abs(x - ret_x) < 900:
                    continue
                add_point(f"entry-topiary-{i}", "plant", x, steps_y + 250, species="topiary_spiral", scale=.95)
            # A faceted planter on the landing beside the door; the sit-out end has its own bench and planter.
            for i, x in enumerate((p0 + 420, p1 - 420)):
                sit = pg.get("sitout_x_mm")
                if sit and sit[0] - 1 <= x <= sit[1] + 1:
                    continue
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

    # A boundary-reaching bedroom can terminate an otherwise open left lane.
    # Pave only the actual exterior remainder; never fill through a room.
    if building.get('planning', {}).get('custom') and Lm < 700:
        front_band = fp.intersection(box(xmin, 0, xmax, 500))
        if not front_band.is_empty and front_band.bounds[0]-xmin >= 700:
            add_poly('left-service-lane', 'path', box(xmin+wt, 0, front_band.bounds[0]-60, D), material_role='site.flagstone')

    # ---- Side passages -------------------------------------------------------
    # A side garden as renovated in the reference: large two-tone slabs laid across the passage with a pebble
    # drip strip against the house, the boundary wall clad in horizontal timber boards, tall pots of planting
    # where the passage is wide enough to walk past them, and wall lights on the house. Narrow passages keep
    # stepping stones in pebbles.
    for side, gap in (("left", Lm), ("right", Rm)):
        if gap < 700:
            continue
        if side == "left":
            x0, x1 = xmin + wt, -60
        else:
            x0, x1 = W + 60, xmax - wt
        y0 = 0 if F >= 700 else ymin + wt
        if side == 'right' and side_parking:
            y0 = max(y0, front_y0 + 6200)
        y1 = D + min(RE, 600)
        wid = x1 - x0
        fence = {"id": f"{side}-fence-cladding", "kind": "fence_cladding", "side": side,
                 "x_mm": round(xmin + wt if side == "left" else xmax - wt), "y0_mm": round(max(y0, 0)),
                 "y1_mm": round(ymax - wt), "height_mm": 1780, "material_role": "site.timber_boards"}
        features.append(fence)
        if wid >= 820:
            # As in the reference garden: large pale pavers laid staggered across a bed of black pebbles, a white
            # pebble drip strip against the house, a breeze-block screen set into the boundary cladding, and pots
            # and a wash basin by the boundary beside pavers that step away from it.
            drip = 170
            bed = box(x0 + 30, y0, x1 - drip, y1) if side == "left" else box(x0 + drip, y0, x1 - 30, y1)
            strip = box(x1 - drip, y0, x1, y1) if side == "left" else box(x0, y0, x0 + drip, y1)
            add_poly(f"{side}-passage-bed", "pebble_bed", bed, material_role="site.pebble_black")
            add_poly(f"{side}-passage-drip", "pebble_bed", strip, edging=True, material_role="site.pebble")
            bx0, _, bx1, _ = bed.bounds
            away = 1 if side == "left" else -1                    # direction from the boundary towards the house
            edge = bx0 if side == "left" else bx1                 # the bed's boundary-side edge
            # A bed 1.3 m wide or more leaves a 0.58 m strip beside each paver that steps away from the boundary,
            # for pots and the basin; a narrower one is paved nearly across for walking.
            roomy = bx1 - bx0 >= 1300
            pw = min(1100, bx1 - bx0 - (640 if roomy else 160))
            shift = max(0., (bx1 - bx0 - pw) / 2 - 60) * (1 if roomy else .8)
            pavers, spots, yy, i = [], [], y0 + 380, 0
            while yy + 300 <= y1 - 150 and len(pavers) < 60:
                cx = (bx0 + bx1) / 2 + (shift if i % 2 else -shift) * away
                pavers.append(_poly(box(cx - pw / 2, yy - 300, cx + pw / 2, yy + 300)))
                gap = abs((cx - away * pw / 2) - edge)
                if roomy and i % 2 and gap >= 560:
                    spots.append((yy, edge + away * (gap / 2 - 10)))
                yy += 760
                i += 1
            features.append({"id": f"{side}-passage-pavers", "kind": "stepping_stones", "stones": pavers, "material_role": "site.paver_large"})
            span = min(2600, (y1 - y0) * .35)
            if span >= 1400:
                sy = (y0 + y1) / 2
                fence["gaps_mm"] = [[round(sy - span / 2), round(sy + span / 2)]]
                features.append({"id": f"{side}-breeze-screen", "kind": "breeze_screen", "side": side, "x_mm": fence["x_mm"],
                                 "y0_mm": round(sy - span / 2), "y1_mm": round(sy + span / 2), "z0_mm": 200, "z1_mm": 1780,
                                 "module_mm": 195, "material_role": "site.breeze_block"})
            if spots:
                by, bxx = spots.pop()
                features.append({"id": f"{side}-garden-basin", "kind": "garden_basin", "side": side, "position_mm": [round(bxx), round(by)]})
            for i, (py, px) in enumerate(spots[::2][:6]):
                species = ("grass_ornamental", "strelitzia", "shrub_round")[i % 3]
                features.append({"id": f"{side}-passage-pot-{i}", "kind": "planter", "position_mm": [round(px), round(py)],
                                 "shape": "round", "size_mm": [440, 440, 580], "species": species,
                                 "scale": {"grass_ornamental": .7, "strelitzia": .45, "shrub_round": .5}[species]})
            yy = y0 + 1800
            i = 0
            while yy < y1 - 1000:
                features.append({"id": f"{side}-wall-light-{i}", "kind": "wall_light", "position_mm": [round(-10 if side == "left" else W + 10), round(yy)], "height_mm": 1900, "facing": -1 if side == "left" else 1})
                yy += 3200
                i += 1
            continue
        passage = box(x0, y0, x1, y1)
        add_poly(f"{side}-passage", "pebble_bed", passage, edging=True, material_role="site.pebble")
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
        # A stone water wall on the rear boundary, on the axis of the patio (or of the house): water falls from a
        # steel lip into a pebble-lined trough, lit from below; the hedge parts around it.
        water = None
        if depth >= 900 and xmax - xmin >= 6000:
            wx = (patio["geometry"]["bounds_mm"][0] + patio["geometry"]["bounds_mm"][2]) / 2 if patio else W / 2
            ww = min(2400, (xmax - xmin) * .28)
            wx = min(max(wx, xmin + wt + ww / 2 + 400), xmax - wt - ww / 2 - 400)
            water = (wx - ww / 2, wx + ww / 2)
            features.append({"id": "rear-water-wall", "kind": "water_wall", "position_mm": [round(wx), round(ymax - wt)],
                             "width_mm": round(ww), "height_mm": 2000, "trough_depth_mm": 420, "material_role": "site.stone_cladding"})
            occupied.append(box(wx - ww / 2 - 100, ymax - wt - 560, wx + ww / 2 + 100, ymax - wt))
            taken = unary_union(occupied)
        if depth >= 1200:
            hedge_y = ymax - wt - 320
            a, b = xmin + wt + 200, xmax - wt - 200
            runs = [(a, water[0] - 350), (water[1] + 350, b)] if water else [(a, b)]
            for i, (ha, hb) in enumerate(r for r in runs if r[1] - r[0] >= 900):
                features.append({"id": "rear-hedge" if i == 0 else f"rear-hedge-{i}", "kind": "hedge", "position_mm": [round((ha + hb) / 2), round(hedge_y)],
                                 "size_mm": [round(hb - ha), 480, 1400], "rotation": 0})
            lawn = rear.difference(taken.buffer(80)).difference(box(xmin, hedge_y - 300, xmax, ymax))
        else:
            lawn = rear.difference(taken.buffer(80))
        for i, part in enumerate([p for p in _parts(lawn) if p.area > 900_000]):
            add_poly(f"rear-lawn-{i}", "lawn", part, material_role="site.lawn")
        if depth >= 1500:
            for i, x in enumerate((xmin + wt + 900, xmax - wt - 900)):
                add_point(f"rear-tree-{i}", "tree", x, D + 60 + depth * .45, species="tree_standard", scale=.85)

    if building.get('planning',{}).get('frontCourt')=='tiled':
        # Only this authored option changes the entrance court; other samples retain planting.
        features=[f for f in features if not (
            (f['kind'] in ('plant','planter','tree','hedge') and f.get('position_mm',[0,1])[1]<0) or
            (f['id'].startswith('front-') and f['kind'] in ('lawn','pebble_bed','stepping_stones')))]
        front=box(xmin+wt,front_y0,xmax-wt,0)
        paving=[Polygon(f['polygon']) for f in features if f['kind'] in ('court','path','patio','deck') and 'polygon' in f]
        # The porch reservation is wider than its actual steps. Tile beneath it
        # too, so its side pockets do not expose the viewer's green ground plane.
        add_poly('front-tiled-court','path',front.difference(unary_union(paving)),material_role='site.flagstone')

    if building.get('planning',{}).get('entranceStyle')=='wall-supported':
        # Recess the front-court lights in the boundary instead of leaving bollards
        # standing in the pedestrian corridor. Retain the existing warm light rhythm.
        for f in features:
            if f['kind']=='lantern' and f.get('position_mm',[0,1])[1]<0:
                f.update(kind='boundary_path_light',position_mm=[f['position_mm'][0],round(ymin+wt)])

    return {
        "schema": "floorforge.landscape/0.2",
        "arrival_sequence": ["road_edge", "gate", "arrival_court", "entrance_steps", "landing", "main_door"],
        "features": features,
        "boundary": boundary,
        "outside_property_context": "viewer_context_only",
        "design_notes": "Stamped-cobble court, pebble beds with steel edging, lawns with stepping stones, lantern light and layered tropical planting.",
    }
