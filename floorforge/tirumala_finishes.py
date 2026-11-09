"""Architectural, court, car-bay, veranda, garden, and rooflight finishes for Tirumala Revision 9.

Activated only when ``building['planning']['colonyContext'] == 'tirumala-colony'``.
Implements the Revision 9 site and architectural details across all five Options A–E:
- +300 mm (z = 0.00 m) house, front court, shallow open-to-sky entry porch, West veranda,
  North 3 ft clear garden passage, and NW open garden datum
- Two 150 mm entrance rises at x = 18.5..28.5 ft, y = 0.5..1.5 ft from road/gate level (±0 mm, z = -0.30 m)
- Lower ±0 mm (z = -0.30 m) 10.5 × 19 ft parking bay at x = 29..39.5 ft, y = 0.5..19.5 ft
- Boundary-plane vertical greenery along the North 3 ft clear passage (leaving the full 3 ft walkway clear)
- Shaded West care veranda with teak-collared columns and timber soffit (plus Option E caregiver court)
- Open NW corner garden with lawn, stepping stones, and perimeter planters
- Double-height living rooflight (x = 18.5..22.5 ft, y = drawEnd+2..drawEnd+10 ft) at the upper roof
"""
from __future__ import annotations

import math
import numpy as np
from shapely.geometry import Polygon, box

FT_M = 0.3048


def _ft(val: float) -> float:
    return round(val * FT_M, 4)


def apply_tirumala_finishes(k, materials: dict, building: dict, height: float) -> list[dict]:
    """Add Tirumala Revision 9 site levels, steps, veranda canopy, boundary greenery, NW garden,
    and double-height rooflight. Returns extra lawn polygons to append to scene['lawns']."""
    extra_lawns: list[dict] = []
    materials["tirumala-teak"] = {
        "color": "#7b5131",
        "alt": "#613d22",
        "roughness": 0.42,
        "texture": "wood",
        "kind": "wood",
    }
    materials["tirumala-cane"] = {
        "color": "#cbb07c",
        "alt": "#b3955e",
        "roughness": 0.74,
        "texture": "fabric",
        "kind": "fabric",
    }
    materials["tirumala-terracotta"] = {
        "color": "#b56548",
        "alt": "#994f35",
        "roughness": 0.78,
    }
    materials["tirumala-sandstone"] = {
        "color": "#d6ccb8",
        "alt": "#bfb39c",
        "roughness": 0.82,
        "texture": "paver",
        "kind": "paver",
        "params": [2, 2, 0.003, 0.05],
        "tile_m": 1.2,
    }
    materials["tirumala-court-tile"] = {
        "color": "#ebe7dc",
        "alt": "#ddd7c8",
        "roughness": 0.68,
        "texture": "paver",
        "kind": "paver",
        "params": [2, 2, 0.002, 0.03],
        "tile_m": 0.9,
    }
    materials["tirumala-carbay-paver"] = {
        "color": "#a7a49c",
        "alt": "#918e86",
        "roughness": 0.86,
        "texture": "paver",
        "kind": "paver",
        "params": [3, 2, 0.004, 0.06],
        "tile_m": 0.6,
    }
    materials["tirumala-greenery"] = {
        "color": "#3d6b35",
        "alt": "#568448",
        "roughness": 0.88,
    }

    plinth = building["brief"]["plinth_mm"] / 1000.0  # 0.30 m (+300 mm house datum above g = -0.30 m)
    g = -plinth
    meta = building.get("planning", {}).get("tirumalaMeta") or {}
    params = meta.get("parameters") or {}
    draw_end = float(params.get("drawEnd", 20.5))
    care_end = float(params.get("careEnd", 36.0))
    veranda_end = float(params.get("verandaEnd", 43.0))
    court_end = params.get("courtEnd")

    # 1. Raised +300 mm East Front Court (x = 0.5..28.5 ft, y = 0.5..7.25 ft) & Two 150 mm Entrance Steps
    court_owner = "east-front-court"
    # Main raised court platform behind entrance steps (y = 1.5..7.25 ft, x = 0.5..28.5 ft)
    k.rect(
        (_ft(0.5), _ft(1.5), g, _ft(28.5), _ft(7.25), -0.004),
        "tirumala-court-tile",
        0,
        "court",
        f"{court_owner}/main-slab",
        court_owner,
    )
    # South portion of East front court (x = 0.5..18.5 ft, y = 0.5..1.5 ft)
    k.rect(
        (_ft(0.5), _ft(0.5), g, _ft(18.5), _ft(1.5), -0.004),
        "tirumala-court-tile",
        0,
        "court",
        f"{court_owner}/south-slab",
        court_owner,
    )
    # Two 150 mm entrance rises at x = 18.5..28.5 ft, y = 0.5..1.5 ft (rising from ±0 mm road/gate to +300 mm court)
    steps_owner = "east-entrance-steps"
    # Step 1 (lower tread: +150 mm above road/car-bay datum, y = 0.5..1.0 ft)
    k.rect(
        (_ft(18.5), _ft(0.5), g, _ft(28.5), _ft(1.0), g + 0.15),
        "tirumala-sandstone",
        0,
        "step",
        f"{steps_owner}/step-1",
        steps_owner,
    )
    # Step 2 (upper tread: +300 mm above road/car-bay datum, y = 1.0..1.5 ft)
    k.rect(
        (_ft(18.5), _ft(1.0), g, _ft(28.5), _ft(1.5), -0.002),
        "tirumala-sandstone",
        0,
        "step",
        f"{steps_owner}/step-2",
        steps_owner,
    )
    # Subtle warm LED nosing lines on the two entrance steps
    for idx, (sy, sz) in enumerate(((_ft(0.5), g + 0.145), (_ft(1.0), -0.008))):
        k.rect(
            (_ft(18.7), sy - 0.012, sz - 0.018, _ft(28.3), sy + 0.005, sz),
            "lamp",
            0,
            "fixture",
            f"{steps_owner}/led-{idx}",
            steps_owner,
        )

    # Shallow 10 × 3 ft open-to-sky entry porch sconces (flanking g-entry at x = 23 ft, y = 10.75 ft)
    for idx, sx in enumerate((_ft(21.1), _ft(24.9))):
        sy = _ft(10.5) - 0.04
        k.rect((sx - 0.04, sy - 0.04, 1.95, sx + 0.04, sy + 0.03, 2.22), "frame", 0, "fixture", f"porch-sconce-{idx}", "g-porch")
        k.rect((sx - 0.03, sy - 0.045, 1.98, sx + 0.03, sy - 0.035, 2.19), "lamp", 0, "fixture")
        k.light((sx, sy - 0.25, 2.05), 8, kind="wall")

    # 2. Lower ±0 mm Car Parking Bay (x = 29..39.5 ft, y = 0.5..19.5 ft; 10.5 × 19 ft)
    carbay_owner = "lower-parking-bay"
    k.rect(
        (_ft(29.0), _ft(0.5), g - 0.02, _ft(39.5), _ft(19.5), g + 0.032),
        "tirumala-carbay-paver",
        -1,
        "court",
        f"{carbay_owner}/slab",
        carbay_owner,
    )
    # Wheel-track stone strips for the 6.5 × 15.5 ft parked car (x = 31..37.5 ft, y = 2.25..17.75 ft)
    for idx, wx in enumerate((_ft(32.1), _ft(36.4))):
        k.rect(
            (wx - 0.28, _ft(2.0), g + 0.032, wx + 0.28, _ft(18.0), g + 0.038),
            "tirumala-sandstone",
            -1,
            "path",
            f"{carbay_owner}/track-{idx}",
            carbay_owner,
        )
    # 300 mm sandstone retaining curb between +300 mm court/porch/drawing (x <= 28.75 ft) and ±0 mm car bay (x >= 29 ft)
    k.rect(
        (_ft(28.5), _ft(0.5), g, _ft(29.0), _ft(19.5), 0.02),
        "tirumala-sandstone",
        0,
        "porch",
        f"{carbay_owner}/curb-south",
        carbay_owner,
    )
    # Two 150 mm transition steps at y = 19.5..20.5 ft from ±0 mm car bay up to +300 mm North 3 ft garden passage
    k.rect(
        (_ft(36.5), _ft(19.5), g, _ft(39.5), _ft(20.0), g + 0.15),
        "tirumala-sandstone",
        0,
        "step",
        f"{carbay_owner}/north-step-1",
        carbay_owner,
    )
    k.rect(
        (_ft(36.5), _ft(20.0), g, _ft(39.5), _ft(20.5), -0.002),
        "tirumala-sandstone",
        0,
        "step",
        f"{carbay_owner}/north-step-2",
        carbay_owner,
    )

    # 3. Raised +300 mm North 3 ft Clear Garden Passage (x = 36.5..39.5 ft, y = 19.5..verandaEnd ft)
    # and Boundary-Plane Vertical Greenery (keeping the full 3 ft clear passage unobstructed)
    north_owner = "north-clear-passage"
    k.rect(
        (_ft(36.25), _ft(20.5), g, _ft(39.5), _ft(veranda_end), -0.004),
        "tirumala-sandstone",
        0,
        "path",
        f"{north_owner}/walkway",
        north_owner,
    )
    # Boundary-plane vertical creeper trellis integrated into the North boundary plane (x = 39.5..39.85 ft)
    trellis_x0 = _ft(39.52)
    trellis_x1 = _ft(39.78)
    trellis_y0 = _ft(20.8)
    trellis_y1 = _ft(veranda_end - 0.3)
    k.rect(
        (trellis_x0, trellis_y0, 0.02, trellis_x1, trellis_y1, 0.18),
        "tirumala-sandstone",
        0,
        "landscape",
        f"{north_owner}/boundary-trough",
        north_owner,
    )
    # Vertical creeper panels in the boundary plane (leaves 100% of the 3 ft passage x = 36.5..39.5 ft clear)
    panel_count = max(3, int((trellis_y1 - trellis_y0) // 1.1))
    for i in range(panel_count):
        py0 = trellis_y0 + i * (trellis_y1 - trellis_y0) / panel_count + 0.06
        py1 = trellis_y0 + (i + 1) * (trellis_y1 - trellis_y0) / panel_count - 0.06
        k.rect(
            (trellis_x0 + 0.01, py0, 0.18, trellis_x0 + 0.06, py1, 1.48),
            "tirumala-greenery",
            0,
            "landscape",
            f"{north_owner}/creeper-panel-{i}",
            north_owner,
        )
        k.rect(
            (trellis_x0, py0 - 0.02, 0.18, trellis_x0 + 0.02, py0, 1.52),
            "tirumala-teak",
            0,
            "screen",
            f"{north_owner}/trellis-post-{i}",
            north_owner,
        )

    # 4. Covered West Care Veranda (x = 23.5..36 ft, y = careEnd+0.5..verandaEnd ft) & Option E Caregiver Courtyard
    veranda = next((s for s in building["spaces"] if s["id"] == "g-veranda"), None)
    if veranda:
        owner = "g-veranda"
        vy0 = _ft(care_end + 0.25)
        vy1 = _ft(veranda_end)
        vx0 = _ft(23.25)
        vx1 = _ft(36.25)
        # Sheltering veranda roof canopy & warm teak soffit over main West care veranda
        k.rect(
            (vx0 - 0.08, vy0, height - 0.18, vx1 + 0.08, vy1 + 0.12, height - 0.04),
            "roof",
            0,
            "canopy",
            f"{owner}/canopy-slab",
            owner,
        )
        for j, sx in enumerate(np.arange(vx0 + 0.12, vx1 - 0.12, 0.14)):
            k.rect(
                (sx, vy0 + 0.06, height - 0.205, min(vx1 - 0.08, sx + 0.065), vy1 - 0.04, height - 0.18),
                "tirumala-teak",
                0,
                "soffit",
                f"{owner}/soffit-{j}",
                owner,
            )
        # Slender columns with teak base & capital collars along outer West edge of veranda
        col_y = vy1 - 0.12
        for idx, col_x in enumerate((_ft(24.2), _ft(29.75), _ft(35.3))):
            cid = f"{owner}/veranda-column-{idx}"
            k.rect((col_x - 0.10, col_y - 0.10, 0.015, col_x + 0.10, col_y + 0.10, 0.18), "tirumala-teak", 0, "column", cid + "-base", owner)
            k.rect((col_x - 0.08, col_y - 0.08, 0.18, col_x + 0.08, col_y + 0.08, height - 0.32), "wall", 0, "column", cid + "-shaft", owner)
            k.rect((col_x - 0.11, col_y - 0.11, height - 0.32, col_x + 0.11, col_y + 0.11, height - 0.18), "tirumala-teak", 0, "column", cid + "-capital", owner)

        # Option E: Caregiver courtyard return (x = 20..23.5 ft, y = 32.5..46.5 ft) bench & courtyard accent
        if court_end:
            bench_x0, bench_x1 = _ft(20.3), _ft(21.6)
            bench_y0, bench_y1 = _ft(41.5), _ft(44.2)
            k.rect(
                (bench_x0, bench_y0, 0.02, bench_x1, bench_y1, 0.44),
                "tirumala-teak",
                0,
                "outdoor-furniture",
                f"{owner}/caregiver-court-bench",
                owner,
            )

    # 5. Open Northwest Corner Garden & West Open Strip (exact handoff polygons for each Option A–E, raised at +300 mm datum)
    nw_owner = "nw-open-garden"
    garden_ft = (meta.get("ground_ft") or {}).get("garden") or [
        [30.5, 41], [39.5, 41], [39.5, 47], [30.5, 47],
    ]
    rear_ft = (meta.get("ground_ft") or {}).get("rear") or [
        [0.5, 47.5], [39.5, 47.5], [39.5, 49.5], [0.5, 49.5],
    ]
    from shapely.ops import unary_union
    garden_poly = unary_union([
        Polygon([[_ft(pt[0]), _ft(pt[1])] for pt in garden_ft]),
        Polygon([[_ft(pt[0]), _ft(pt[1])] for pt in rear_ft]),
    ])
    for idx_g, gpart in enumerate([garden_poly] if garden_poly.geom_type == "Polygon" else list(garden_poly.geoms)):
        suffix = "" if idx_g == 0 else f"-{idx_g}"
        k.poly_mesh(gpart, g, -0.015, "tirumala-sandstone", 0, "landscape", f"{nw_owner}/plinth{suffix}", nw_owner)
        lawn_poly = gpart.buffer(-0.10, join_style=2)
        if not lawn_poly.is_empty and lawn_poly.geom_type == "Polygon":
            k.poly_mesh(lawn_poly, -0.015, 0.018, "lawn", 0, "lawn", f"{nw_owner}/lawn{suffix}", nw_owner)
            extra_lawns.append({
                "id": f"{nw_owner}-lawn{suffix}",
                "polygon": [[round(x, 4), round(y, 4)] for x, y in list(lawn_poly.exterior.coords)[:-1]],
                "holes": [],
                "z": 0.018,
            })

    # Sandstone stepping stones in the NW open garden connecting the veranda & North passage
    stone_y = _ft(min(48.2, veranda_end + 2.2))
    for idx, sx_ft in enumerate((37.5, 34.0, 30.5, 27.0, 24.5)):
        sx, sy = _ft(sx_ft), stone_y
        if garden_poly.contains(box(sx - 0.24, sy - 0.20, sx + 0.24, sy + 0.20)):
            k.rect(
                (sx - 0.24, sy - 0.20, 0.018, sx + 0.24, sy + 0.20, 0.042),
                "tirumala-sandstone",
                0,
                "path",
                f"{nw_owner}/stepping-stone-{idx}",
                nw_owner,
            )

    # Perimeter planters in the NW garden & East front court (never in the 3 ft North clear passage)
    pot_placements = [
        # East front court South corner
        (_ft(2.2), _ft(1.2), 0.0, "cordyline", 1.05, 0.22, 0.42, "tirumala-terracotta"),
        (_ft(16.8), _ft(1.2), 0.0, "shrub_round", 0.55, 0.19, 0.35, "planter"),
        # Open NW garden perimeter (West boundary y = 48.6 ft)
        (_ft(38.2), _ft(48.4), 0.018, "frangipani", 2.65, 0.28, 0.50, "tirumala-terracotta"),
        (_ft(32.5), _ft(48.5), 0.018, "strelitzia", 1.35, 0.24, 0.44, "planter"),
        (_ft(26.5), _ft(48.5), 0.018, "monstera", 0.90, 0.22, 0.38, "tirumala-terracotta"),
        (_ft(18.0), _ft(48.5), 0.018, "cordyline", 1.00, 0.20, 0.38, "tirumala-terracotta"),
    ]
    for px, py, pz, species, p_height, radius, pot_h, pot_mat in pot_placements:
        k.plant(px, py, pz, species, height=p_height, pot=(radius, pot_h, pot_mat))

    # 6. Double-Height Living Rooflight (rooflight at x = 18.5..22.5 ft, y = drawEnd+2..drawEnd+10 ft)
    rf_owner = "living-void-rooflight"
    rf_x0, rf_x1 = _ft(18.5), _ft(22.5)
    rf_y0, rf_y1 = _ft(draw_end + 2.0), _ft(min(draw_end + 10.0, 31.0))
    z_roof = 2.0 * height
    # Architectural upstand curb on the upper roof
    for idx, (bx0, by0, bx1, by1) in enumerate([
        (rf_x0 - 0.08, rf_y0 - 0.08, rf_x1 + 0.08, rf_y0),
        (rf_x0 - 0.08, rf_y1, rf_x1 + 0.08, rf_y1 + 0.08),
        (rf_x0 - 0.08, rf_y0, rf_x0, rf_y1),
        (rf_x1, rf_y0, rf_x1 + 0.08, rf_y1),
    ]):
        k.rect((bx0, by0, z_roof - 0.04, bx1, by1, z_roof + 0.22), "frame", 1, "roof-edge", f"{rf_owner}/curb-{idx}", rf_owner)
    # Laminated clear skylight glazing pane
    k.rect((rf_x0, rf_y0, z_roof + 0.18, rf_x1, rf_y1, z_roof + 0.21), "glass", 1, "pergola-glass", f"{rf_owner}/glass", rf_owner)
    # Warm timber shading fins inside the skylight curb for shaded daylight
    for idx, fy in enumerate(np.linspace(rf_y0 + 0.30, rf_y1 - 0.30, 5)):
        k.rect((rf_x0 + 0.02, fy - 0.025, z_roof + 0.04, rf_x1 - 0.02, fy + 0.025, z_roof + 0.16), "tirumala-teak", 1, "soffit", f"{rf_owner}/baffle-{idx}", rf_owner)
    # High-level zenithal daylight source into the ~23 ft double-height living hall
    k.light(((rf_x0 + rf_x1) / 2, (rf_y0 + rf_y1) / 2, z_roof - 0.35), 28, kind="pendant")

    # 7. East Upper Terrace planters (u-terrace at x = 8.75..18.25 ft, y = 7.25..10.75 ft)
    u_terr = next((s for s in building["spaces"] if s["id"] == "u-terrace"), None)
    if u_terr:
        z1 = height
        tx0,ty0,tx1,ty1=Polygon(u_terr['clear']).bounds
        positions=[(tx0/1000+.35,ty0/1000+.35,'monstera',.85),(tx1/1000-.35,ty0/1000+.35,'strelitzia',1.05)]
        for idx, (ux, uy, sp, uh) in enumerate(positions):
            k.plant(ux, uy, z1 + 0.02, sp, height=uh, f=1, pot=(0.20, 0.38, "tirumala-terracotta"))
            k.colliders.append({
                "id": f"u-terrace-pot-{idx}",
                "floor": 1,
                "kind": "landscape",
                "polygon": [[ux - 0.21, uy - 0.21], [ux + 0.21, uy - 0.21], [ux + 0.21, uy + 0.21], [ux - 0.21, uy + 0.21]],
            })

    return extra_lawns
