"""Architectural, veranda, care-access, and garden finishes specific to the Tirumala sample.

Activated only when ``building['planning']['colonyContext'] == 'tirumala-colony'``.
Combines My Desired Home's restrained white/ivory architecture, limestone bands, and warm timber soffits
with selective veranda character from The Bungalow (slender columns with teak collars, cane-and-teak
shaded seating, grouped terracotta/stone pots, and a landscaped Northwest open pocket).
"""
from __future__ import annotations

import math
import numpy as np
from shapely.geometry import Polygon, box


def apply_tirumala_finishes(k, materials: dict, building: dict, height: float) -> list[dict]:
    """Add Tirumala-specific veranda columns, cane seating, accessible ramp, NW garden pocket,
    and upper terrace furnishings. Returns any extra lawn polygons to append to scene['lawns']."""
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

    plinth = building["brief"]["plinth_mm"] / 1000.0
    g = -plinth

    # 1. Shaded North L-Shaped Veranda: slender columns with warm teak base & capital collars
    veranda = next((s for s in building["spaces"] if s["id"] == "g-veranda"), None)
    if veranda:
        owner = "g-veranda"
        col_x = 9.76
        for idx, col_y in enumerate((0.28, 2.85, 5.55, 7.15, 9.55)):
            cid = f"{owner}/veranda-column-{idx}"
            # Teak base plinth
            k.rect((col_x - 0.11, col_y - 0.11, 0.015, col_x + 0.11, col_y + 0.11, 0.18), "tirumala-teak", 0, "column", cid + "-base", owner)
            # Ivory masonry/rendered shaft
            k.rect((col_x - 0.085, col_y - 0.085, 0.18, col_x + 0.085, col_y + 0.085, height - 0.34), "wall", 0, "column", cid + "-shaft", owner)
            # Teak capital collar & bracket
            k.rect((col_x - 0.115, col_y - 0.115, height - 0.34, col_x + 0.115, col_y + 0.115, height - 0.20), "tirumala-teak", 0, "column", cid + "-capital", owner)
            k.rect((col_x - 0.16, col_y - 0.06, height - 0.24, col_x + 0.16, col_y + 0.06, height - 0.175), "tirumala-teak", 0, "column", cid + "-bracket", owner)

        # Cane & Teak Shaded Seating Corner in the sheltered NW veranda bay (x: 8.82..9.45, y: 7.55..9.15)
        # Leaves the L-junction (x: 6.50..8.70, y: 5.75..7.15) and all doorways completely clear.
        seat_owner = "g-veranda/cane-seating-set"
        for c_idx, cy in enumerate((7.85, 8.85)):
            cx = 9.12
            # Teak chair legs & armrests
            for dx in (-0.24, 0.24):
                for dy in (-0.22, 0.22):
                    k.rect((cx + dx - 0.02, cy + dy - 0.02, 0.02, cx + dx + 0.02, cy + dy + 0.02, 0.56), "tirumala-teak", 0, "outdoor-furniture", f"{seat_owner}-leg-{c_idx}-{dx}-{dy}", seat_owner)
            k.rect((cx - 0.26, cy - 0.24, 0.36, cx + 0.26, cy + 0.24, 0.41), "tirumala-teak", 0, "outdoor-furniture", f"{seat_owner}-seat-frame-{c_idx}", seat_owner)
            # Woven cane seat & backrest
            k.rb((cx + 0.02, cy, 0.44), (0.46, 0.44, 0.06), "linen", 0, "outdoor-furniture", 0.02, owner=seat_owner)
            k.rect((cx - 0.25, cy - 0.22, 0.42, cx - 0.19, cy + 0.22, 0.82), "tirumala-teak", 0, "outdoor-furniture", f"{seat_owner}-back-frame-{c_idx}", seat_owner)
            k.rect((cx - 0.23, cy - 0.18, 0.46, cx - 0.20, cy + 0.18, 0.78), "tirumala-cane", 0, "outdoor-furniture", f"{seat_owner}-cane-back-{c_idx}", seat_owner)

        # Round teak & cane tea table at (9.12, 8.35)
        tx, ty = 9.12, 8.35
        k.cylinder((tx, ty, 0.46), 0.24, 0.035, "tirumala-teak", 0, "outdoor-furniture")
        k.cylinder((tx, ty, 0.44), 0.20, 0.02, "tirumala-cane", 0, "outdoor-furniture")
        for angle in (0.0, 2.094, 4.188):
            lx, ly = tx + 0.15 * math.cos(angle), ty + 0.15 * math.sin(angle)
            k.beam((lx, ly, 0.02), (lx, ly, 0.45), 0.018, "tirumala-teak", 0, "outdoor-furniture")
        k.cylinder((tx, ty, 0.51), 0.07, 0.08, "brass", 0, "detail")

        seat_fp = [[8.82, 7.55], [9.45, 7.55], [9.45, 9.15], [8.82, 9.15]]
        k.colliders.append({"id": seat_owner, "floor": 0, "kind": "furniture", "polygon": seat_fp})
        k.furniture.append({"id": seat_owner, "room_id": "g-veranda", "floor": 0, "kind": "cane-seating", "footprint": seat_fp})

    # 2. East Arrival Care-Friendly Stepped Ramp & Handrail (beside main entrance landing)
    ramp_owner = "exterior-care-ramp-01"
    rx0, rx1 = 4.65, 5.55
    ry0, ry1 = -1.65, -0.05
    steps = 8
    for i in range(steps):
        ya = ry0 + i * (ry1 - ry0) / steps
        yb = ry0 + (i + 1) * (ry1 - ry0) / steps
        zt = g + 0.04 + (i + 1) * (plinth - 0.06) / steps
        k.rect((rx0, ya, g, rx1, yb, zt), "tirumala-sandstone", 0, "porch", f"{ramp_owner}-seg-{i}", ramp_owner)
    # Slim dark steel care handrail along the outer edge of the ramp
    k.beam((rx1 - 0.04, ry0 + 0.08, g + 0.90), (rx1 - 0.04, ry1 - 0.08, 0.88), 0.018, "frame", 0, "railing")
    for post_y, post_z in ((ry0 + 0.10, g + 0.05), ((ry0 + ry1) / 2, g + plinth * 0.5), (ry1 - 0.10, -0.02)):
        k.beam((rx1 - 0.04, post_y, post_z), (rx1 - 0.04, post_y, post_z + 0.88), 0.016, "frame", 0, "railing")

    # 3. Northwest Open Pocket Garden, Stepping-Stone Service Route & Quiet Caregiver Courtyard
    nw_owner = "nw-open-pocket"
    # Pocket lawn in the NW corner (x: 8.85..10.90, y: 9.90..13.10)
    nw_lawn = box(8.85, 9.90, 10.90, 13.10)
    k.poly_mesh(nw_lawn, g + 0.015, g + 0.035, "lawn", -1, "lawn", f"{nw_owner}/lawn", nw_owner)
    extra_lawns.append({
        "id": f"{nw_owner}-lawn",
        "polygon": [[round(x, 4), round(y, 4)] for x, y in list(nw_lawn.exterior.coords)[:-1]],
        "holes": [],
        "z": round(g + 0.035, 4),
    })
    # Sandstone stepping stones linking North veranda end (y=9.80) through NW pocket to West service lane
    stone_coords = [
        (9.25, 10.15), (9.25, 10.80), (9.25, 11.45), (9.15, 12.10),
        (8.45, 12.25), (7.65, 12.25), (6.85, 12.25), (6.00, 12.25),
        (5.85, 11.55), (5.85, 10.85), (5.85, 10.15),
    ]
    for idx, (sx, sy) in enumerate(stone_coords):
        k.rect((sx - 0.28, sy - 0.22, g + 0.018, sx + 0.28, sy + 0.22, g + 0.048), "tirumala-sandstone", -1, "path", f"{nw_owner}/stepping-stone-{idx}", nw_owner)

    # Quiet courtyard pocket outside caregiver bedroom (x: 5.35..6.35, y: 9.95..12.00)
    cg_court = box(5.40, 9.95, 6.32, 11.95)
    k.poly_mesh(cg_court, g + 0.012, g + 0.032, "tirumala-sandstone", -1, "court", f"{nw_owner}/caregiver-court", nw_owner)
    # Teak garden bench in the caregiver open pocket
    k.rect((5.52, 10.45, g + 0.035, 5.95, 11.35, g + 0.45), "tirumala-teak", -1, "outdoor-furniture", f"{nw_owner}/caregiver-bench", nw_owner)

    # 4. North Private Setback Lawn & Grouped Pots (low profile to preserve seated care-room sightlines)
    north_strip = box(9.94, 0.15, 10.92, 9.75)
    k.poly_mesh(north_strip, g + 0.015, g + 0.035, "lawn", -1, "lawn", "north-private-setback/lawn", "north-private-setback")
    extra_lawns.append({
        "id": "north-private-setback-lawn",
        "polygon": [[round(x, 4), round(y, 4)] for x, y in list(north_strip.exterior.coords)[:-1]],
        "holes": [],
        "z": round(g + 0.035, 4),
    })

    # Grouped terracotta and stone planters around East entrance, North veranda edge, and NW open pocket
    pot_placements = [
        # East arrival & veranda corner
        (8.95, -0.35, g + 0.02, "strelitzia", 1.15, 0.24, 0.46, "tirumala-terracotta"),
        (9.35, -0.45, g + 0.02, "shrub_round", 0.55, 0.19, 0.36, "planter"),
        (2.45, -0.42, g + 0.02, "cordyline", 1.10, 0.22, 0.44, "tirumala-terracotta"),
        # Along North veranda edge (low/compact plants so seated sightlines at +1.15m remain unobstructed)
        (10.18, 1.40, g + 0.035, "shrub_round", 0.48, 0.20, 0.34, "tirumala-terracotta"),
        (10.18, 4.20, g + 0.035, "monstera", 0.55, 0.21, 0.36, "planter"),
        (10.18, 6.80, g + 0.035, "shrub_round", 0.48, 0.20, 0.34, "tirumala-terracotta"),
        (10.18, 9.20, g + 0.035, "cordyline", 0.85, 0.22, 0.40, "tirumala-terracotta"),
        # In the Northwest open garden pocket (framing the caregiver suite & screening NW corner)
        (10.35, 10.60, g + 0.035, "frangipani", 2.85, 0.30, 0.52, "tirumala-terracotta"),
        (10.45, 12.30, g + 0.035, "strelitzia", 1.45, 0.25, 0.46, "planter"),
        (8.95, 12.55, g + 0.035, "monstera", 0.95, 0.22, 0.40, "tirumala-terracotta"),
        (6.15, 11.75, g + 0.035, "cordyline", 1.05, 0.20, 0.38, "tirumala-terracotta"),
    ]
    for px, py, pz, species, p_height, radius, pot_h, pot_mat in pot_placements:
        k.plant(px, py, pz, species, height=p_height, pot=(radius, pot_h, pot_mat))

    # 5. First-Floor North L-Terrace & East Balcony Lounge Seating and Planters
    u_terr = next((s for s in building["spaces"] if s["id"] == "u-terrace-north"), None)
    if u_terr:
        z1 = height
        ut_owner = "u-terrace-north/cane-lounge"
        for idx, cy in enumerate((6.15, 6.75)):
            cx = 7.35
            k.rect((cx - 0.25, cy - 0.23, z1 + 0.03, cx + 0.25, cy + 0.23, z1 + 0.39), "tirumala-teak", 1, "outdoor-furniture", f"{ut_owner}-chair-{idx}", ut_owner)
            k.rb((cx + 0.02, cy, z1 + 0.43), (0.44, 0.42, 0.07), "linen", 1, "outdoor-furniture", 0.02, owner=ut_owner)
            k.rect((cx - 0.24, cy - 0.21, z1 + 0.40, cx - 0.18, cy + 0.21, z1 + 0.78), "tirumala-cane", 1, "outdoor-furniture", f"{ut_owner}-back-{idx}", ut_owner)
        k.cylinder((7.90, 6.45, z1 + 0.44), 0.25, 0.035, "tirumala-teak", 1, "outdoor-furniture")
        ut_fp = [[7.02, 5.90], [8.18, 5.90], [8.18, 7.00], [7.02, 7.00]]
        k.colliders.append({"id": ut_owner, "floor": 1, "kind": "furniture", "polygon": ut_fp})
        k.furniture.append({"id": ut_owner, "room_id": "u-terrace-north", "floor": 1, "kind": "outdoor-lounge", "footprint": ut_fp})

        for idx, (ux, uy, sp, uh) in enumerate([
            (9.42, 0.55, "strelitzia", 1.15),
            (9.42, 9.35, "cordyline", 1.10),
            (0.55, 0.55, "monstera", 0.90),
        ]):
            k.plant(ux, uy, z1 + 0.022, sp, height=uh, f=1, pot=(0.21, 0.40, "tirumala-terracotta"))
            k.colliders.append({
                "id": f"u-terrace-pot-{idx}",
                "floor": 1,
                "kind": "landscape",
                "polygon": [[ux - 0.22, uy - 0.22], [ux + 0.22, uy - 0.22], [ux + 0.22, uy + 0.22], [ux - 0.22, uy + 0.22]],
            })

    return extra_lawns
