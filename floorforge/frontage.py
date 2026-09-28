"""Street frontage planning shared by every exterior theme (plan millimetres, road at local -Y).

A real compound wall is not a centred gate with equal walls either side. The planner lays out what a
built home has: a pedestrian gate on the path to the front door, a separate vehicle gate over the
parking pad (aligned with the carport when there is one, otherwise over the widest stretch of front
yard the entrance steps leave free), and a stone-clad pier beside the pedestrian gate carrying the
house number, letterbox and gate light. The rest of the frontage is wall between piers. It is a
preliminary geometry proposal; gate widths, swing and sliding clearances still need site review.
"""
from __future__ import annotations

from typing import Any

PEDESTRIAN_GATE_MM = 1100
LETTERBOX_PIER_MM = 520
END_WALL_MM = 300        # least wall kept between a gate and a corner pier


def vehicle_gate_width(parking: bool, front_mm: float) -> int:
    """Clear width of the vehicle gate: a car gate with parking, a narrower one for two-wheelers otherwise."""
    if parking:
        return 3600
    return 3000 if front_mm >= 2500 else 2400


def plan_frontage(plot_bounds, entry_x: float, *, steps_x: tuple[float, float] | None, parking: bool, front_mm: float,
                  carport_x: tuple[float, float] | None = None, wall_mm: float = 150) -> dict[str, Any]:
    """Gates and piers along the front boundary (x ranges in plan millimetres).

    `steps_x` is the x range of the porch and its steps (the driveway keeps clear of it); `carport_x` the
    carport's x range when one is built.
    """
    xmin, _, xmax, _ = plot_bounds
    lo, hi = xmin + wall_mm + END_WALL_MM, xmax - wall_mm - END_WALL_MM
    pw, pier = PEDESTRIAN_GATE_MM, LETTERBOX_PIER_MM
    p0 = min(max(entry_x - pw / 2, lo), hi - pw)
    vehicle = None
    if front_mm >= 1100:
        if carport_x:
            c0, c1 = carport_x
            vw = min(3600, c1 - c0 + 300)
            v0 = min(max((c0 + c1) / 2 - vw / 2, lo), hi - vw)
            vehicle = (v0, v0 + vw)
            # The pedestrian gate keeps to the door axis unless the car gate claims it; then it moves beside it.
            if p0 < vehicle[1] + pier and p0 + pw > vehicle[0] - pier:
                left, right = vehicle[0] - pier - pw, vehicle[1] + pier
                options = [x for x in (left, right) if lo <= x <= hi - pw]
                if options:
                    p0 = min(options, key=lambda x: abs(x + pw / 2 - entry_x))
        else:
            want = vehicle_gate_width(parking, front_mm)
            blocked = [(p0 - pier - 150, p0 + pw + pier + 150)]
            if steps_x:
                blocked.append((steps_x[0] - 150, steps_x[1] + 150))
            zones, x = [], lo
            for a, b in sorted(blocked):
                if a > x:
                    zones.append((x, min(a, hi)))
                x = max(x, b)
            if x < hi:
                zones.append((x, hi))
            zones = [z for z in zones if z[1] - z[0] >= 2400]
            if zones:
                z0, z1 = max(zones, key=lambda z: z[1] - z[0])
                vw = min(want, z1 - z0)
                c = (z0 + z1) / 2
                vehicle = (c - vw / 2, c + vw / 2)
    ped = (p0, p0 + pw)
    # The letterbox pier stands on the side of the pedestrian gate facing the vehicle gate (or the longer wall).
    if vehicle:
        pier_left = (vehicle[0] + vehicle[1]) / 2 < p0
    else:
        pier_left = (p0 - xmin) > (xmax - p0 - pw)
    letterbox = (p0 - pier, p0) if pier_left else (p0 + pw, p0 + pw + pier)
    gates = [{
        "id": "gate-pedestrian", "kind": "pedestrian", "x0_mm": round(ped[0]), "x1_mm": round(ped[1]),
        "operation": "swing", "hinge": "right" if pier_left else "left", "open_deg": 88,
    }]
    if vehicle:
        # The sliding leaf parks behind the longer clear stretch of wall beside the opening (up to the pedestrian
        # gate and its pier, or the corner); a stretch shorter than the opening needs a telescopic two-leaf gate.
        span = (min(ped[0], letterbox[0]), max(ped[1], letterbox[1]))
        left_stop = span[1] if span[1] <= vehicle[0] else xmin + wall_mm
        right_stop = span[0] if span[0] >= vehicle[1] else xmax - wall_mm
        run_l, run_r = vehicle[0] - left_stop, right_stop - vehicle[1]
        run = max(run_l, run_r)
        gates.append({
            "id": "gate-vehicle", "kind": "vehicle", "x0_mm": round(vehicle[0]), "x1_mm": round(vehicle[1]),
            "operation": "sliding", "park": "left" if run_l >= run_r else "right", "state": "closed",
            "leaves": 1 if run >= vehicle[1] - vehicle[0] else 2, "park_run_mm": round(run),
        })
    return {
        "gate_center_mm": round((ped[0] + ped[1]) / 2), "gate_width_mm": round(pw),
        "gates": gates,
        "letterbox_pier": {"x0_mm": round(letterbox[0]), "x1_mm": round(letterbox[1]), "height_mm": 2100},
    }


def gate_openings(boundary: dict[str, Any]) -> list[tuple[float, float, dict[str, Any]]]:
    """(x0, x1, gate) for each gate in the front wall, in millimetres; older records carry a single gate."""
    gates = boundary.get("gates")
    if gates:
        return sorted(((g["x0_mm"], g["x1_mm"], g) for g in gates), key=lambda t: t[0])
    c, w = boundary.get("gate_center_mm"), boundary.get("gate_width_mm", 2200)
    if c is None:
        return []
    return [(c - w / 2, c + w / 2, {"id": "gate", "kind": "pedestrian", "operation": "swing", "x0_mm": c - w / 2, "x1_mm": c + w / 2})]
