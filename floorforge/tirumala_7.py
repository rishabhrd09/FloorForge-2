"""Tirumala 7: 50' x 40' three-floor corner home with 12' x 5' rooflight shaft and video-matched interiors."""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from .custom_plan import get_parts, geometry, regions
from .modular_kitchen import straight_run_kitchen
from .scene_kit import Kit as SceneKit, rounded_box
from .spaces import NON_WALKABLE, OUTDOOR, SPACE_REGISTRY

FT = 304.8
WALL_MM = 120.0
HALF_WALL_MM = 60.0
FLOOR_H_MM = 3150.0
FLOOR_H_M = 3.150
PLINTH_MM = 300.0
PLINTH_M = 0.300


def local_mm(x_ft: float, y_ft: float) -> list[float]:
    """Convert PDF feet (x_ft east of west boundary 0..50, y_ft south of north road 0..40)
    to FloorForge building millimetres (+X north, +Y west)."""
    return [round((40.0 - float(y_ft)) * FT, 3), round((50.0 - float(x_ft)) * FT, 3)]


def local_m(x_ft: float, y_ft: float) -> tuple[float, float]:
    """Convert PDF feet (x_ft, y_ft) to FloorForge scene metres (+X north, +Y west)."""
    return (round((40.0 - float(y_ft)) * 0.3048, 4), round((50.0 - float(x_ft)) * 0.3048, 4))


def box_mm(x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float) -> Polygon:
    """Create a Shapely box in building millimetres from PDF foot bounds."""
    p0 = local_mm(x0_ft, y0_ft)
    p1 = local_mm(x1_ft, y1_ft)
    return box(min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]))


def box_m(x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float) -> tuple[float, float, float, float]:
    """Return (X0, Y0, X1, Y1) in scene metres from PDF foot bounds."""
    x0, y0 = local_m(x1_ft, y1_ft)
    x1, y1 = local_m(x0_ft, y0_ft)
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def poly_coords_mm(poly: Polygon) -> list[list[float]]:
    return [[round(float(x), 3), round(float(y), 3)] for x, y in list(poly.exterior.coords)[:-1]]


def _room_kind_map() -> dict[str, str]:
    return {
        # Ground floor
        'outside_gully': 'courtyard',
        'caregiver': 'bedroom',
        'caregiver_bath': 'bathroom',
        'hall_entry': 'foyer',
        'drawing_room': 'drawing-room',
        'covered_entry': 'outer-lobby',
        'verandah': 'veranda',
        'car_porch': 'outer-lobby',
        'living_hall': 'living',
        'home_icu': 'care-room',
        'master_bath': 'bathroom',
        'west_gully': 'courtyard',
        'master_bedroom': 'bedroom',
        'bedroom_entry': 'foyer',
        'dining_hall': 'dining',
        'kitchen': 'kitchen',
        'work_bay': 'foyer',
        'stair': 'stair',
        'stair_gap': 'foyer',
        'stair_side_gap': 'foyer',
        'store': 'store',
        'wash_area': 'drying-room',
        # First floor
        'u_master_bedroom': 'bedroom',
        'u_dressing': 'dress',
        'u_en_suite': 'bathroom',
        'u_study_meditation': 'study',
        'u_family_gallery': 'inner-lobby',
        'u_open_to_below': 'void',
        'u_shared_bath': 'bathroom',
        'u_medium_bedroom': 'bedroom',
        'u_stair': 'stair',
        'u_large_terrace': 'terrace',
        # Second floor
        's_office_tv_hall': 'family',
        's_lobby_passage': 'inner-lobby',
        's_stair_lobby': 'stair',
        's_raised_rooflight': 'void',
        's_open_terrace': 'terrace',
    }


def coordinate_levels(b: dict, plan: dict) -> None:
    """Populate exact 3-floor PDF geometry into building `b` from `plan-reference.json`."""
    meta = plan.get('tirumalaMeta', {})
    ref = meta.get('planReference')
    if not ref:
        ref_path = Path(__file__).resolve().parents[1] / 'examples/gallery/tirumala-7/plan-reference.json'
        ref = json.loads(ref_path.read_text())

    b['brief']['floor_height_mm'] = int(FLOOR_H_MM)
    b['brief']['plinth_mm'] = int(PLINTH_MM)
    b['brief']['storeys'] = 3
    b['brief']['bedrooms'] = 4
    b['storeys'] = 3
    b['planning']['tirumala7'] = True
    b['planning']['tirumalaMeta'] = meta

    kind_map = _room_kind_map()
    spaces: list[dict] = []
    walls: list[dict] = []
    openings: list[dict] = []

    # 1. Build spaces across Ground (0), First (1), and Second (2) floors
    floor_keys = [('ground', 0, 'floor-0', ''), ('first', 1, 'floor-1', 'u_'), ('second', 2, 'floor-2', 's_')]
    space_polys_by_floor: dict[int, dict[str, Polygon]] = {0: {}, 1: {}, 2: {}}

    for fkey, f_idx, fl_id, prefix in floor_keys:
        f_data = ref['floors'][fkey]
        for raw_id, r in f_data['rooms'].items():
            if raw_id in ('prep_counter_zone', 'bedroom_roof_non_walkable') or raw_id.startswith('not_'):
                continue
            # Consolidate segmented terrace pieces into the single continuous terrace space per upper floor
            if f_idx == 1 and raw_id in ('large_terrace_north', 'large_terrace_nw', 'large_terrace_study_strip', 'east_terrace', 'se_terrace'):
                continue
            if f_idx == 2 and raw_id.startswith('open_terrace_'):
                continue

            sid = prefix + raw_id if not raw_id.startswith(prefix) else raw_id
            kind = kind_map.get(sid, 'foyer')
            spec = SPACE_REGISTRY[kind]

            x0_ft, x1_ft = r['x_ft']
            y0_ft, y1_ft = r['y_ft']
            poly = box_mm(x0_ft, y0_ft, x1_ft, y1_ft)
            if sid == 'living_hall':
                poly = unary_union([poly, box_mm(17.5, 9.0, 24.0, 16.0)])
            elif sid == 'u_family_gallery':
                poly = unary_union([
                    box_mm(18.0, 9.0, 24.0, 26.0),
                    box_mm(24.0, 21.0, 39.0, 26.0),
                    box_mm(17.0, 26.0, 21.0, 33.0),
                    box_mm(7.0, 24.0, 17.0, 29.0),
                    box_mm(15.0, 17.0, 18.0, 24.0),
                ])
            clear_poly = poly
            space_polys_by_floor[f_idx][sid] = poly

            rec = {
                'id': sid,
                'pdf_id': raw_id,
                'floorId': fl_id,
                'name': r.get('name') or r.get('label') or raw_id,
                'kind': kind,
                'floor': f_idx,
                'polygon': poly_coords_mm(poly),
                'clear': poly_coords_mm(clear_poly),
                'area_m2': round(poly.area / 1e6, 6),
                'nominal_area_sqft': round((x1_ft - x0_ft) * (y1_ft - y0_ft), 2),
                'x_ft': [float(x0_ft), float(x1_ft)],
                'y_ft': [float(y0_ft), float(y1_ft)],
                'size_ft': [round(x1_ft - x0_ft, 3), round(y1_ft - y0_ft, 3)],
                'size_mm': [round((x1_ft - x0_ft) * FT, 2), round((y1_ft - y0_ft) * FT, 2)],
                'enclosed': spec['enclosed'],
                'roofed': spec['roofed'] and raw_id not in ('outside_gully', 'west_gully'),
                'walkable': spec['floor'] and raw_id not in ('open_to_below', 'raised_rooflight'),
                'wet': spec['wet'],
                'drain': kind in ('bathroom', 'drying-room'),
            }
            if kind == 'bathroom':
                rec['mechanicalVentilation'] = True
            if raw_id in ('outside_gully', 'west_gully'):
                rec['openToSky'] = True
            if raw_id in ('stair_gap', 'stair_side_gap'):
                rec['serviceOnly'] = True
            if raw_id == 'caregiver':
                rec['bedType'] = 'single'
            if raw_id == 'car_porch':
                rec['openSkyStripFt'] = {'x_ft': [47.0, 50.0], 'y_ft': [0.0, 20.0]}
            if raw_id in ('open_to_below', 'raised_rooflight'):
                rec['openToBelow'] = True
            if raw_id == 'raised_rooflight':
                rec['glassCover'] = True
            spaces.append(rec)

        # Add the continuous walkable terrace on First Floor (exact 520.0 sq ft)
        if f_idx == 1:
            t_parts = [
                box_mm(23.0, 0.0, 47.0, 8.0),
                box_mm(18.0, 2.0, 24.0, 9.0),
                box_mm(39.0, 8.0, 47.0, 40.0),
                box_mm(33.0, 34.0, 39.0, 40.0),
            ]
            t_poly = unary_union(t_parts)
            space_polys_by_floor[1]['u_large_terrace'] = t_poly
            spaces.append({
                'id': 'u_large_terrace',
                'pdf_id': 'large_terrace',
                'floorId': 'floor-1',
                'name': 'Large terrace (shared)',
                'kind': 'terrace',
                'floor': 1,
                'polygon': poly_coords_mm(t_poly),
                'clear': poly_coords_mm(t_poly),
                'area_m2': round(t_poly.area / 1e6, 6),
                'nominal_area_sqft': round(t_poly.area / (FT * FT), 2),
                'x_ft': [18.0, 47.0],
                'y_ft': [0.0, 40.0],
                'east_edge_x_ft': 47.0,
                'enclosed': False,
                'roofed': False,
                'walkable': True,
                'wet': False,
                'drain': True,
            })

        # Add the continuous walkable terrace on Second Floor (exact 858.0 sq ft)
        if f_idx == 2:
            t2_parts = [
                box_mm(23.0, 0.0, 44.0, 8.0),
                box_mm(0.0, 2.0, 23.0, 8.0),
                box_mm(0.0, 8.0, 3.0, 26.0),
                box_mm(2.0, 26.0, 17.0, 29.0),
                box_mm(7.0, 29.0, 17.0, 40.0),
                box_mm(33.0, 8.0, 44.0, 31.0),
                box_mm(34.0, 31.0, 44.0, 40.0),
            ]
            t2_poly = unary_union(t2_parts)
            space_polys_by_floor[2]['s_open_terrace'] = t2_poly
            spaces.append({
                'id': 's_open_terrace',
                'pdf_id': 'open_terrace',
                'floorId': 'floor-2',
                'name': 'Open terrace',
                'kind': 'terrace',
                'floor': 2,
                'polygon': poly_coords_mm(t2_poly),
                'clear': poly_coords_mm(t2_poly),
                'area_m2': round(t2_poly.area / 1e6, 6),
                'nominal_area_sqft': round(t2_poly.area / (FT * FT), 2),
                'x_ft': [0.0, 44.0],
                'y_ft': [0.0, 40.0],
                'east_edge_x_ft': 44.0,
                'enclosed': False,
                'roofed': False,
                'walkable': True,
                'wet': False,
                'drain': True,
            })

    # 2. Build walls on each floor directly from PDF wall axes in `plan-reference.json`,
    # bridging across door/window spans so every opening has a continuous host wall with lintel above.
    wall_height = int(FLOOR_H_MM - 150)  # 3000 mm
    for fkey, f_idx, fl_id, prefix in floor_keys:
        by_axis: dict[tuple[str, float], list[tuple[float, float, bool]]] = {}
        for seg in ref['floors'][fkey]['walls_ft']:
            (x0, y0), (x1, y1) = seg[0], seg[1]
            if abs(x0 - x1) < 0.01:
                by_axis.setdefault(('x', round(x0, 2)), []).append((min(y0, y1), max(y0, y1), True))
            elif abs(y0 - y1) < 0.01:
                by_axis.setdefault(('y', round(y0, 2)), []).append((min(x0, x1), max(x0, x1), True))
        for item in list(ref['floors'][fkey].get('doors', [])) + list(ref['floors'][fkey].get('windows', [])):
            ax, val_s = item['wall'].split('=')
            val = round(float(val_s), 2)
            s0, s1 = float(item['span_ft'][0]), float(item['span_ft'][1])
            by_axis.setdefault((ax, val), []).append((min(s0, s1), max(s0, s1), False))

        raw_segments = []
        for (ax, val), intervals in sorted(by_axis.items()):
            intervals.sort(key=lambda t: (t[0], t[1]))
            merged: list[list] = []
            for lo, hi, is_wall in intervals:
                if merged and lo <= merged[-1][1] + 0.25:
                    merged[-1][1] = max(merged[-1][1], hi)
                    merged[-1][2] = merged[-1][2] or is_wall
                else:
                    merged.append([lo, hi, is_wall])
            for lo, hi, has_wall in merged:
                if not has_wall and (hi - lo) < 0.5:
                    continue
                if ax == 'x':
                    raw_segments.append([[val, round(lo, 3)], [val, round(hi, 3)]])
                else:
                    raw_segments.append([[round(lo, 3), val], [round(hi, 3), val]])

        sp_map = space_polys_by_floor[f_idx]
        for w_idx, (a_ft, b_ft) in enumerate(raw_segments):
            p0 = local_mm(*a_ft)
            p1 = local_mm(*b_ft)
            a, b_pt = sorted((p0, p1))
            line = LineString([a, b_pt])
            if line.length < 50.0:
                continue
            wpoly = line.buffer(HALF_WALL_MM, cap_style=3, join_style=2)
            adj = sorted([
                sid for sid, sp in sp_map.items()
                if sp.buffer(HALF_WALL_MM + 5.0).intersects(line)
                and sp.buffer(HALF_WALL_MM + 5.0).intersection(line).length >= 100.0
            ])
            if not adj:
                adj = [next(iter(sp_map.keys()))]
            is_ext = (
                len(adj) == 1
                or any(c in (0.0, 50.0) for c in (a_ft[0], b_ft[0]))
                or any(c in (0.0, 40.0) for c in (a_ft[1], b_ft[1]))
            )
            walls.append({
                'id': f'{fkey[0]}-wall-{w_idx}',
                'floor': f_idx,
                'floorId': fl_id,
                'a': list(a),
                'b': list(b_pt),
                'a_ft': a_ft,
                'b_ft': b_ft,
                'thickness': int(WALL_MM),
                'height': wall_height,
                'rooms': adj[:2],
                'external': bool(is_ext),
                'polygon': regions(wpoly)[0]['polygon'],
            })

    # 3. Build openings on each floor from `plan-reference.json` (`doors` + `windows`)
    opening_connects_override = {
        # Ground floor doors
        'caregiver_north_door': (['caregiver', 'outside_gully'], 'caregiver'),
        'caregiver_hall_door': (['caregiver', 'hall_entry'], 'caregiver'),
        'caregiver_bath_door': (['caregiver_bath', 'caregiver'], 'caregiver_bath'),
        'drawing_east_door': (['drawing_room', 'living_hall'], 'drawing_room'),
        'main_double_doors': (['covered_entry', 'living_hall'], 'living_hall'),
        'icu_north_slider': (['home_icu', 'verandah'], None),
        'icu_west_clear_opening': (['home_icu', 'living_hall'], None),
        'master_bath_door': (['master_bath', 'master_bedroom'], 'master_bath'),
        'master_west_gully_door': (['master_bedroom', 'west_gully'], 'master_bedroom'),
        'master_bedroom_door': (['master_bedroom', 'bedroom_entry'], 'master_bedroom'),
        'work_bay_porch_door': (['work_bay', 'car_porch'], 'work_bay'),
        'store_door': (['store', 'kitchen'], 'store'),
        'wash_area_door': (['wash_area', 'kitchen'], 'wash_area'),
        # Ground floor windows
        'caregiver_west_window': (['caregiver', 'outside'], None),
        'drawing_north_window': (['drawing_room', 'outside_gully'], None),
        'drawing_east_window_1': (['drawing_room', 'covered_entry'], None),
        'drawing_east_window_2': (['drawing_room', 'covered_entry'], None),
        'icu_north_fixed_glazing_west': (['home_icu', 'verandah'], None),
        'icu_north_fixed_glazing_east': (['home_icu', 'verandah'], None),
        'icu_east_window_1': (['home_icu', 'car_porch'], None),
        'icu_east_window_2': (['home_icu', 'car_porch'], None),
        'master_bath_high_window': (['master_bath', 'outside'], None),
        'master_west_window': (['master_bedroom', 'west_gully'], None),
        'master_south_window': (['master_bedroom', 'outside'], None),
        'wash_south_window': (['wash_area', 'outside'], None),
        # First floor doors
        'ff_master_door': (['u_master_bedroom', 'u_family_gallery'], 'u_master_bedroom'),
        'ff_dressing_opening': (['u_master_bedroom', 'u_dressing'], None),
        'ff_ensuite_door': (['u_en_suite', 'u_dressing'], 'u_en_suite'),
        'ff_gallery_terrace_double_doors': (['u_family_gallery', 'u_large_terrace'], 'u_family_gallery'),
        'ff_study_door': (['u_study_meditation', 'u_family_gallery'], 'u_study_meditation'),
        'ff_study_terrace_slider': (['u_study_meditation', 'u_large_terrace'], None),
        'ff_medium_bedroom_door': (['u_medium_bedroom', 'u_family_gallery'], 'u_medium_bedroom'),
        'ff_shared_bath_door': (['u_shared_bath', 'u_family_gallery'], 'u_shared_bath'),
        # First floor windows
        'ff_master_north_window': (['u_master_bedroom', 'outside'], None),
        'ff_master_west_window': (['u_master_bedroom', 'outside'], None),
        'ff_ensuite_south_high_window': (['u_en_suite', 'outside'], None),
        'ff_study_north_glazing': (['u_study_meditation', 'u_large_terrace'], None),
        'ff_shared_bath_east_window': (['u_shared_bath', 'u_large_terrace'], None),
        'ff_medium_west_window': (['u_medium_bedroom', 'outside'], None),
        'ff_medium_south_window': (['u_medium_bedroom', 'outside'], None),
        # Second floor doors & windows
        'sf_hall_lobby_door': (['s_office_tv_hall', 's_lobby_passage'], 's_office_tv_hall'),
        'sf_hall_terrace_slider': (['s_office_tv_hall', 's_open_terrace'], None),
        'sf_hall_north_window': (['s_office_tv_hall', 's_open_terrace'], None),
        'sf_hall_west_window': (['s_office_tv_hall', 's_open_terrace'], None),
        'sf_hall_east_window': (['s_office_tv_hall', 's_open_terrace'], None),
    }

    for fkey, f_idx, fl_id, _ in floor_keys:
        f_walls = [w for w in walls if w['floor'] == f_idx]
        raw_openings = []
        for d in ref['floors'][fkey].get('doors', []):
            otype = d.get('type', 'door')
            kind = (
                'entry' if d['id'] == 'main_double_doors'
                else 'glazed' if otype == 'sliding_glass_door'
                else 'cased' if otype in ('clear_opening_no_door', 'sliding_or_open')
                else 'door'
            )
            raw_openings.append({**d, 'kind': kind, 'double_leaf': otype == 'double_door', 'sliding': otype == 'sliding_glass_door'})
        for w_item in ref['floors'][fkey].get('windows', []):
            raw_openings.append({**w_item, 'kind': 'window', 'fixed': 'fixed' in w_item['id']})

        for o in raw_openings:
            oid = o['id']
            w_axis, w_val_str = o['wall'].split('=')
            w_val = float(w_val_str)
            s0, s1 = float(o['span_ft'][0]), float(o['span_ft'][1])
            # Leave a 100 mm mullion between ICU north fixed glazing and the 7' slider so wall cuts don't touch
            if oid == 'icu_north_fixed_glazing_west':
                s1 = 27.95
            elif oid == 'icu_north_fixed_glazing_east':
                s0 = 35.05
            if w_axis == 'y':
                a_ft, b_ft = [s0, w_val], [s1, w_val]
            else:
                a_ft, b_ft = [w_val, s0], [w_val, s1]

            p0 = local_mm(*a_ft)
            p1 = local_mm(*b_ft)
            span_start, span_end = sorted((p0, p1))
            span_line = LineString([span_start, span_end])
            mid = span_line.centroid

            # Find best matching parallel wall on this floor
            horiz = abs(span_start[1] - span_end[1]) < 1.0
            candidates = [
                w for w in f_walls
                if (abs(w['a'][1] - w['b'][1]) < 1.0) == horiz
                and LineString([w['a'], w['b']]).distance(mid) < 150.0
            ]
            host = min(candidates, key=lambda w: LineString([w['a'], w['b']]).distance(mid))
            w_line = LineString([host['a'], host['b']])
            offset = round(max(20.0, w_line.project(Point(span_start))), 2)
            width = round(span_line.length, 2)
            if offset + width > w_line.length - 20.0:
                offset = max(10.0, round(w_line.length - width - 20.0, 2))

            kind = o['kind']
            connects, swing = opening_connects_override.get(oid, (host['rooms'][:2], host['rooms'][0]))
            if len(connects) == 1:
                connects = [connects[0], 'outside']

            sill = 0
            height = 2250
            if kind == 'window':
                if o.get('fixed'):
                    sill = 150
                    height = 2100
                elif 'bath' in oid or 'ensuite' in oid:
                    sill = 1050
                    height = 1200
                else:
                    sill = 750
                    height = 1650
            elif kind == 'cased':
                sill = 0
                height = 2400 if oid == 'icu_west_clear_opening' else 2250

            rec = {
                'id': oid,
                'wall_id': host['id'],
                'floor': f_idx,
                'kind': kind,
                'offset': offset,
                'width': width,
                'sill': sill,
                'height': height,
                'connects': list(connects),
                'swing': swing if kind in ('door', 'entry') else None,
                'hinge': 'start',
                'a_ft': a_ft,
                'b_ft': b_ft,
                'wall_ref': o['wall'],
                'span_ft': list(o['span_ft']),
                'nominal_width_ft': float(o.get('width_ft', round(abs(s1 - s0), 2))),
            }
            if o.get('sliding') or kind == 'glazed':
                rec['sliding'] = True
                rec['slidingPanels'] = 2
            if o.get('double_leaf'):
                rec['doubleLeaf'] = True
            if o.get('fixed'):
                rec['fixed'] = True
            openings.append(rec)

    # 4. Build the 2/9/4 U-turn stair (`stair-0` Ground->First, `stair-1` First->Second)
    # Well is x_ft: 17..32 (width 15' = 4572 mm along Y), y_ft: 33..40 (depth 7' = 2133.6 mm along X)
    stair_box = box_mm(17.0, 33.0, 32.0, 40.0)
    sx0, sy0, sx1, sy1 = stair_box.bounds
    stairs = []
    for f_idx, room_id, next_f in ((0, 'stair', 1), (1, 'u_stair', 2), (2, 's_stair_lobby', None)):
        stairs.append({
            'id': f'stair-{f_idx}',
            'linkId': 'main-stair',
            'roomId': room_id,
            'floor': f_idx,
            'to_floor': next_f,
            'x': sx0,
            'y': sy0,
            'width': round(sx1 - sx0, 2),
            'depth': round(sy1 - sy0, 2),
            'flight_width': round(3.5 * FT, 2),   # 1066.8 mm (>= 1000 mm)
            'well': 0,
            'landing_mm': round(3.5 * FT, 2),     # 1066.8 mm
            'riser_count': 18,
            'riser_mm': 175.0,                    # <= 190 mm
            'tread_mm': 292.6,                    # >= 250 mm
            'headroom_mm': 2775.0,                # >= 2100 mm
            'tread_sequence': [2, 9, 4],
            'direction': 'east-south-west-north',
        })

    # 5. Build Floor Plates & Roofs across all 3 levels
    void_poly = box_mm(21.0, 26.0, 33.0, 31.0)         # 12' x 5' double-height shaft & rooflight
    stair_well_f1 = box_mm(17.0, 33.0, 32.0, 40.0)
    stair_well_f2 = box_mm(17.0, 33.0, 32.0, 40.0)

    # Plate 0: full 50' x 40' ground footprint
    plate0_outline = box_mm(0.0, 0.0, 50.0, 40.0)
    # Plate 1: First-floor slab (east edge straight at x=47 for full 40'; excludes north gully, west gully, and 3' east setback)
    plate1_outline = box_mm(0.0, 0.0, 47.0, 40.0).difference(
        unary_union([box_mm(0.0, 0.0, 23.0, 2.0), box_mm(0.0, 26.0, 2.0, 40.0)])
    )
    plate1_slab = plate1_outline.difference(unary_union([void_poly, stair_well_f1]))

    # Plate 2: Second-floor slab (east edge straight at x=44 for full 40'; excludes north gully, west gully, and 6' east setback)
    plate2_outline = box_mm(0.0, 0.0, 44.0, 40.0).difference(
        unary_union([box_mm(0.0, 0.0, 23.0, 2.0), box_mm(0.0, 26.0, 2.0, 40.0)])
    )
    plate2_slab = plate2_outline.difference(unary_union([void_poly, stair_well_f2]))

    plates = [
        {
            'id': 'plate-floor-0',
            'floor': 0,
            'floorId': 'floor-0',
            'outline': regions(plate0_outline),
            'regions': regions(plate0_outline),
            'openings': [],
        },
        {
            'id': 'plate-floor-1',
            'floor': 1,
            'floorId': 'floor-1',
            'outline': regions(plate1_outline),
            'regions': regions(plate1_slab),
            'openings': [
                {'id': 'u-void-opening', 'regions': regions(void_poly)},
                {'id': 'main-stair-void-1', 'stairId': 'main-stair', 'regions': regions(stair_well_f1)},
            ],
        },
        {
            'id': 'plate-floor-2',
            'floor': 2,
            'floorId': 'floor-2',
            'outline': regions(plate2_outline),
            'regions': regions(plate2_slab),
            'openings': [
                {'id': 's-rooflight-opening', 'regions': regions(void_poly)},
                {'id': 'main-stair-void-2', 'stairId': 'main-stair', 'regions': regions(stair_well_f2)},
            ],
        },
    ]

    # Roofs & ceilings per level:
    # Floor 0 ceiling excludes open-to-sky gullies, the outer 3' strip of the car porch (x=47..50, y=0..20),
    # the 12' x 5' double-height void (x=21..33, y=26..31), and the stair well.
    g_open_sky = unary_union([
        box_mm(0.0, 0.0, 23.0, 2.0),
        box_mm(0.0, 26.0, 2.0, 40.0),
        box_mm(47.0, 0.0, 50.0, 20.0),
    ])
    roof0_covered = plate0_outline.difference(unary_union([g_open_sky, void_poly, stair_well_f1]))
    roof0_exposed = roof0_covered.difference(plate1_outline)

    # Floor 1 ceiling covers enclosed rooms on Floor 1 (excludes open terrace, void, and stair well)
    u_enclosed = unary_union([
        box_mm(0.0, 2.0, 18.0, 17.0),   # u_master_bedroom
        box_mm(7.0, 17.0, 15.0, 24.0),  # u_dressing
        box_mm(0.0, 17.0, 7.0, 26.0),   # u_en_suite
        box_mm(24.0, 8.0, 39.0, 21.0),  # u_study_meditation
        box_mm(15.0, 9.0, 39.0, 34.0),  # u_family_gallery + u_shared_bath
        box_mm(2.0, 29.0, 17.0, 40.0),  # u_medium_bedroom
        box_mm(17.0, 33.0, 33.0, 40.0), # u_stair
    ]).difference(void_poly)
    roof1_covered = u_enclosed.difference(stair_well_f2)
    roof1_exposed = roof1_covered.difference(plate2_outline)

    # Floor 2 roof covers s_office_tv_hall, s_lobby_passage, s_stair_lobby, plus the raised rooflight frame (cut by rooflight glass)
    s_enclosed = unary_union([
        box_mm(3.0, 8.0, 33.0, 26.0),   # s_office_tv_hall
        box_mm(17.0, 26.0, 34.0, 40.0), # s_lobby_passage + s_stair_lobby + rooflight curb zone
    ])
    roof2_covered = s_enclosed.difference(void_poly)

    roofs = [
        {'id': 'roof-floor-0', 'floor': 0, 'regions': regions(roof0_exposed), 'ceiling': regions(roof0_covered)},
        {'id': 'roof-floor-1', 'floor': 1, 'regions': regions(roof1_exposed), 'ceiling': regions(roof1_covered)},
        {
            'id': 'roof-floor-2',
            'floor': 2,
            'regions': regions(roof2_covered),
            'ceiling': regions(roof2_covered),
            'rooflight': regions(void_poly),
        },
    ]

    # 6. Build Guards:
    # - First-floor 12' x 5' void open edges (north y=26 x=21..33, west x=21 y=26..31, south y=31 x=21..33; east x=33 is shared_bath wall)
    # - Second-floor 12' x 5' raised rooflight perimeter curb/guard
    # - First-floor & Second-floor terrace perimeter guards
    guards = [
        {
            'id': 'u-void-guard-north',
            'owner': 'u_open_to_below',
            'floor': 1,
            'edge': 'north',
            'points': [local_mm(21.0, 26.0), local_mm(33.0, 26.0)],
            'height': 1100,
        },
        {
            'id': 'u-void-guard-west',
            'owner': 'u_open_to_below',
            'floor': 1,
            'edge': 'west',
            'points': [local_mm(21.0, 26.0), local_mm(21.0, 31.0)],
            'height': 1100,
        },
        {
            'id': 'u-void-guard-south',
            'owner': 'u_open_to_below',
            'floor': 1,
            'edge': 'south',
            'points': [local_mm(21.0, 31.0), local_mm(33.0, 31.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-north',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'north',
            'points': [local_mm(21.0, 26.0), local_mm(33.0, 26.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-west',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'west',
            'points': [local_mm(21.0, 26.0), local_mm(21.0, 31.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-south',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'south',
            'points': [local_mm(21.0, 31.0), local_mm(33.0, 31.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-east',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'east',
            'points': [local_mm(33.0, 26.0), local_mm(33.0, 31.0)],
            'height': 1100,
        },
        # Terrace outer edges
        {
            'id': 'u-terrace-guard-east',
            'owner': 'u_large_terrace',
            'floor': 1,
            'points': [local_mm(47.0, 0.0), local_mm(47.0, 40.0)],
            'height': 1100,
        },
        {
            'id': 'u-terrace-guard-north',
            'owner': 'u_large_terrace',
            'floor': 1,
            'points': [local_mm(23.0, 0.0), local_mm(47.0, 0.0)],
            'height': 1100,
        },
        {
            'id': 'u-terrace-guard-south',
            'owner': 'u_large_terrace',
            'floor': 1,
            'points': [local_mm(33.0, 40.0), local_mm(47.0, 40.0)],
            'height': 1100,
        },
        {
            'id': 's-terrace-guard-east',
            'owner': 's_open_terrace',
            'floor': 2,
            'points': [local_mm(44.0, 0.0), local_mm(44.0, 40.0)],
            'height': 1100,
        },
        {
            'id': 's-terrace-guard-north-e',
            'owner': 's_open_terrace',
            'floor': 2,
            'points': [local_mm(23.0, 0.0), local_mm(44.0, 0.0)],
            'height': 1100,
        },
        {
            'id': 's-terrace-guard-north-w',
            'owner': 's_open_terrace',
            'floor': 2,
            'points': [local_mm(0.0, 2.0), local_mm(23.0, 2.0)],
            'height': 1100,
        },
        {
            'id': 's-terrace-guard-west',
            'owner': 's_open_terrace',
            'floor': 2,
            'points': [local_mm(0.0, 2.0), local_mm(0.0, 26.0)],
            'height': 1100,
        },
    ]

    meta = b['planning'].pop('tirumalaMeta', None) or plan.get('tirumalaMeta', {})
    b['planning']['tirumala7'] = True
    b['planning']['colonyContext'] = 'tirumala-colony'
    b['planning']['colony'] = meta.get('colony')
    b['planning']['colonyMaterials'] = meta.get('colonyMaterials')
    b['planning']['eastGates'] = meta.get('eastGates', [('east-walk-gate', 'pedestrian', 11125.2, 9753.6)])
    b['spaces'] = spaces
    b['walls'] = walls
    b['openings'] = openings
    b['stairs'] = stairs
    b['floor_plates'] = plates
    b['roofs'] = roofs
    b['guards'] = guards
    b['footprint'] = regions(plate0_outline)[0]['polygon']
    b['footprint_holes'] = []


def compile_tirumala_7_plan(intent: dict) -> dict:
    """Compile the Tirumala 7 custom plan directly from `plan-reference.json`."""
    from .custom_plan import SCHEMA, normalize
    v = intent['values']
    plan = normalize(intent['customPlan'], v['storeys'])
    b = {
        'schema': 'floorforge.building/0.4',
        'units': 'mm',
        'up': 'Z',
        'brief': v,
        'storeys': v['storeys'],
        'planning': {
            'method': 'authoritative custom plan',
            'custom': True,
            'schema': SCHEMA,
            'dimensions': 'exact clear space in mm',
            'tirumala7': True,
            'colonyContext': 'tirumala-colony',
            'colony': plan.get('tirumalaMeta', {}).get('colony'),
            'colonyMaterials': plan.get('tirumalaMeta', {}).get('colonyMaterials'),
            'eastGates': plan.get('tirumalaMeta', {}).get('eastGates', [('east-walk-gate', 'pedestrian', 11125.2, 9753.6)]),
            **({'frontCourt': plan['frontCourt']} if 'frontCourt' in plan else {}),
        },
        'footprint': [],
        'footprint_holes': [],
        'plot': regions(box(-v['left_mm'], -v['front_mm'], v['width_mm'] - v['left_mm'], v['depth_mm'] - v['front_mm']))[0]['polygon'],
        'floors': [{'id': fl['id'], 'index': f} for f, fl in enumerate(plan['floors'])],
        'spaces': [],
        'walls': [],
        'openings': [],
        'stairs': [],
        'floor_plates': [],
        'roofs': [],
        'guards': [],
        'planHash': intent['planHash'],
        'draftRevision': intent.get('draftRevision', 0),
        'banner': __import__('floorforge').BANNER,
    }
    for k_name in ('doorsClosed', 'sceneSeed', 'interiorFloor', 'parkedCar', 'facadeStyle', 'entranceStyle', 'colonyContext', 'tirumalaRevision', 'tirumalaOption', 'tirumalaMeta'):
        if k_name in plan:
            b['planning'][k_name] = plan[k_name]
    coordinate_levels(b, plan)
    return b


def _register_video_materials(scene: dict) -> None:
    """Register the video-sampled materials & finishes into scene['materials']."""
    from .tirumala_5_finishes import apply_house_daylight, apply_house_palette
    mats = scene['materials']
    for name, base, color, rough in [
        ('travertine', 'stone', '#cfb99b', .58),
        ('olive-velvet', 'fabric', '#686b50', .92),
        ('smoked-oak', 'timber', '#79543c', .50),
        ('bronze', 'brass', '#ad8658', .32),
        ('acoustic-felt', 'fabric', '#45434a', .98),
        ('cinema-screen', 'linen', '#f4ede0', .83),
    ]:
        if base in mats:
            mats[name] = {**mats[base], 'color': color, 'roughness': rough}
    apply_house_palette(mats)
    profile = scene.setdefault('presentation', {})
    apply_house_daylight(profile)
    profile['interior'].update(daylightExposureScale=.38, contrast=1.085, punch=.30)
    for target, source in [
        ('ivory-vitrified', 'ivory-marble-polished'),
        ('ivory-vitrified-matte', 'ivory-marble-satin-wet'),
        ('flagstone', 'ivory-marble-exterior-matte'),
        ('travertine', 't5-honed-coping'),
        ('smoked-oak', 't5-door-teak'),
        ('bronze', 't5-soft-charcoal'),
        ('doorframe', 't5-door-teak'),
        ('cabinet', 't5-light-timber'),
    ]:
        if source in mats:
            mats[target] = dict(mats[source])
    mats.update({
        'kitchen_sage_teal_gloss': {'color': '#68928e', 'roughness': 0.14, 'metallic': 0.04, 'clearcoat': 0.85, 'clearcoat_roughness': 0.08, 'kind': 'metal', 'params': [0.14]},
        'kitchen_sage_teal_loft': {'color': '#567b77', 'roughness': 0.18, 'metallic': 0.04, 'clearcoat': 0.70, 'clearcoat_roughness': 0.10, 'kind': 'metal', 'params': [0.18]},
        'gola_matte_black': {'color': '#1e2223', 'roughness': 0.28, 'metallic': 0.85, 'kind': 'metal', 'params': [0.28]},
        'quartz_nano_white': {'color': '#f2efe9', 'roughness': 0.18, 'metallic': 0.02, 'kind': 'marble', 'clearcoat': 0.35},
        'backsplash_fluted_ivory': {'color': '#eae5dc', 'roughness': 0.26, 'kind': 'tile', 'tile_m': [0.06, 0.60]},
        'cladding_fluted_teak': {'color': '#8f5b3c', 'roughness': 0.42, 'kind': 'wood', 'texture': 'wood'},
        'cove_led_warm': {'color': '#ffe4b5', 'roughness': 0.10, 'emission': 1.2, 'emissive': '#ffd89b', 'emissive_strength': 4.5},
        'glass_smoked_fluted': {'color': '#2a2f33', 'roughness': 0.12, 'alpha': 0.42, 'metallic': 0.10, 'kind': 'glass'},
        'floor_ivory_vitrified_800': {'color': '#eceae4', 'roughness': 0.18, 'kind': 'tile', 'tile': [0.80, 0.80], 'tile_m': [0.80, 0.80], 'grout': '#d5d1c8'},
        'border_inlay_charcoal': {'color': '#282a2c', 'roughness': 0.22, 'metallic': 0.08, 'kind': 'stone'},
        'sofa_terracotta_velvet': {'color': '#c85a32', 'roughness': 0.76, 'kind': 'fabric'},
        'sofa_taupe_boucle': {'color': '#b9ada1', 'roughness': 0.78, 'kind': 'fabric'},
        'curtain_taupe_drape': {'color': '#7a6a5e', 'roughness': 0.82, 'kind': 'fabric'},
        'curtain_sheer_ivory': {'color': '#f4f1ea', 'roughness': 0.85, 'alpha': 0.38, 'kind': 'fabric'},
        'chandelier_gold_ring': {'color': '#d4af37', 'roughness': 0.22, 'metallic': 0.90, 'kind': 'metal'},
        'dining_marble_top': {'color': '#f4f1eb', 'roughness': 0.16, 'vein': '#c8c2b8', 'kind': 'marble'},
        'travertine_warm': {'color': '#dfd6c7', 'roughness': 0.36, 'kind': 'stone', 'tile': [0.60, 1.20], 'tile_m': [0.60, 1.20]},
        'terrace_wood_deck': {'color': '#8a5a3c', 'roughness': 0.52, 'kind': 'wood', 'tile': [0.15, 1.20], 'tile_m': [0.15, 1.20]},
        'terrace_grey_paver': {'color': '#cfcbc2', 'roughness': 0.58, 'kind': 'paver', 'tile': [0.60, 0.60], 'tile_m': [0.60, 0.60]},
    })
    mats['wall'].update({'color': '#f3efe6', 'roughness': 0.62})
    mats['floor'] = dict(mats['floor_ivory_vitrified_800'])
    mats['Walnut'] = {'color': '#6e472f', 'roughness': 0.38, 'kind': 'wood'}
    mats['walnut'] = {'color': '#6e472f', 'roughness': 0.38, 'kind': 'wood'}


def _build_stair_294(k: SceneKit, H: float) -> None:
    """Build the exact 2/9/4 U-turn staircase (18 risers x 175 mm = 3150 mm) for Ground->First and First->Second.

    Stair well in PDF feet: x_ft: 17..32, y_ft: 33..40.
    - Flight 1 (East leg, x_ft: 28.5..32.0): starts at y_ft=33.0, climbs 2 treads SOUTH to y_ft=36.5 (risers 1..2),
      plus SE corner landing (x_ft: 28.5..32.0, y_ft: 36.5..40.0) at riser 3 (+0.525 m).
    - Flight 2 (South leg, y_ft: 36.5..40.0): climbs 9 treads WEST from x_ft=28.5 to x_ft=20.5 (risers 4..12),
      plus SW corner landing (x_ft: 17.0..20.5, y_ft: 36.5..40.0) at riser 13 (+2.275 m).
    - Flight 3 (West leg, x_ft: 17.0..20.5): climbs 4 treads NORTH from y_ft=36.5 to y_ft=33.0 (risers 14..17),
      stepping onto the upper floor landing at y_ft=33.0 (riser 18 = +3.150 m).
    """
    riser = H / 18.0  # 0.175 m
    for f_idx in (0, 1):
        z0 = f_idx * H
        owner = f'stair-{f_idx}'

        def step_block(x0_ft, y0_ft, x1_ft, y1_ft, r_idx, name, is_landing=False):
            bx0, by0, bx1, by1 = box_m(x0_ft, y0_ft, x1_ft, y1_ft)
            top_z = z0 + r_idx * riser
            bot_z = max(z0, top_z - (0.16 if is_landing else riser * 1.35))
            # Structural concrete waist/step + ivory riser + warm teak tread nosing + warm LED strip
            k.rect((bx0, by0, bot_z, bx1, by1, top_z - 0.032), 'floor_ivory_vitrified_800', f_idx, 'stair', f'{owner}/{name}-body', owner)
            k.rect((bx0 - 0.006, by0 - 0.006, top_z - 0.032, bx1 + 0.006, by1 + 0.006, top_z), 'cladding_fluted_teak', f_idx, 'stair', f'{owner}/{name}-tread', owner)
            if not is_landing:
                k.rect((bx0 + 0.04, by0 + 0.04, top_z - 0.042, bx1 - 0.04, by1 - 0.04, top_z - 0.032), 'cove_led_warm', f_idx, 'detail', f'{owner}/{name}-led', owner)

        # Flight 1: 2 treads south along east leg (x_ft: 28.5..32.0, y_ft: 33.0 -> 36.5)
        dy1 = 3.5 / 2.0
        for i in range(2):
            ya = 33.0 + i * dy1
            yb = ya + dy1
            step_block(28.5, ya, 32.0, yb, i + 1, f'f1-tread-{i+1}')
        # SE corner landing (riser 3)
        step_block(28.5, 36.5, 32.0, 40.0, 3, 'se-landing', is_landing=True)

        # Flight 2: 9 treads west along south leg (x_ft: 28.5 -> 20.5, y_ft: 36.5..40.0)
        dx2 = 8.0 / 9.0
        for i in range(9):
            xb = 28.5 - i * dx2
            xa = xb - dx2
            step_block(xa, 36.5, xb, 40.0, 4 + i, f'f2-tread-{i+1}')
        # SW corner landing (riser 13)
        step_block(17.0, 36.5, 20.5, 40.0, 13, 'sw-landing', is_landing=True)

        # Flight 3: 4 treads north along west leg (x_ft: 17.0..20.5, y_ft: 36.5 -> 33.0)
        dy3 = 3.5 / 4.0
        for i in range(4):
            yb = 36.5 - i * dy3
            ya = yb - dy3
            step_block(17.0, ya, 20.5, yb, 14 + i, f'f3-tread-{i+1}')

        # Inner well balustrade & warm teak handrail along the U-turn inner edge
        ix0, iy0, ix1, iy1 = box_m(20.5, 33.0, 28.5, 36.5)
        # East inner stringer rail
        k.beam((ix1, iy0, z0 + 0.18), (ix1, iy0, z0 + 0.525), 0.035, 'gola_matte_black', f_idx, 'railing')
        k.beam((ix1, iy0, z0 + 1.05), (ix0, iy0, z0 + 1.40), 0.042, 'cladding_fluted_teak', f_idx, 'railing')
        # South inner flight glass balustrade & handrail
        k.rect((ix0 - 0.015, iy0, z0 + 0.55, ix0 + 0.015, iy1, z0 + 3.05), 'glass', f_idx, 'railing', f'{owner}/inner-glass-s', owner)
        k.beam((ix0, iy0, z0 + 1.42), (ix0, iy1, z0 + 3.12), 0.042, 'cladding_fluted_teak', f_idx, 'railing')
        # West inner flight handrail
        k.beam((ix0, iy1, z0 + 3.12), (ix1, iy1, z0 + 4.02), 0.042, 'cladding_fluted_teak', f_idx, 'railing')


def _build_double_height_shaft_and_rooflight(k: SceneKit, H: float) -> None:
    """Build the 12' x 5' (x_ft: 21..33, y_ft: 26..31) double-height shaft features:
    - Full-height vertical fluted teak cladding + travertine stone panels + vertical 3000K LED cove strips
    - First-floor frameless glass balustrade with matte-black shoe & walnut handrail on all open edges
    - Second-floor raised glazed rooflight curb (+6.30..6.68 m), sloped low-E glass & black mullion grid, and protective rail
    - 3-ring brushed-gold & warm-LED chandelier suspended through the shaft over the dining table
    """
    vx0, vy0, vx1, vy1 = box_m(21.0, 26.0, 33.0, 31.0)
    owner = 'double-height-shaft'

    # 1. Full-height fluted teak & travertine feature cladding on the east shaft wall (x_ft=33 -> Y=vy0) at First Floor (z = H..2*H)
    # so the Ground Floor open-plan dining-to-kitchen connection (z = 0..H) remains completely unobstructed!
    k.rect((vx0, vy0 - 0.025, H, vx1, vy0 + 0.015, 2 * H), 'cladding_fluted_teak', 1, 'wall-panel', f'{owner}/east-fluted-wall', owner)
    n_ribs = int((vx1 - vx0) / 0.055)
    for i in range(n_ribs):
        rx = vx0 + i * 0.055 + 0.012
        k.rect((rx, vy0 + 0.012, H + 0.04, rx + 0.024, vy0 + 0.028, 2 * H - 0.05), 'cladding_fluted_teak', 1, 'detail', f'{owner}/east-rib-{i}', owner)
    # Vertical warm LED cove strips framing the east shaft feature wall
    k.rect((vx0 + 0.02, vy0 + 0.015, H + 0.06, vx0 + 0.045, vy0 + 0.032, 2 * H - 0.08), 'cove_led_warm', 1, 'cove', f'{owner}/east-led-s', owner)
    k.rect((vx1 - 0.045, vy0 + 0.015, H + 0.06, vx1 - 0.02, vy0 + 0.032, 2 * H - 0.08), 'cove_led_warm', 1, 'cove', f'{owner}/east-led-n', owner)

    # Travertine + fluted teak accent panel on the north face of the dining/void zone (ICU south wall, y_ft=26 -> X=vx1)
    k.rect((vx1 - 0.022, vy0, 0.90, vx1 + 0.005, vy1, H - 0.12), 'travertine_warm', 0, 'wall-panel', f'{owner}/north-travertine', owner)
    k.rect((vx1 - 0.028, vy0 + 0.35, 0.95, vx1 - 0.012, vy1 - 0.35, H - 0.18), 'cladding_fluted_teak', 0, 'wall-panel', f'{owner}/north-teak-inset', owner)
    k.rect((vx1 - 0.030, vy0 + 0.33, 0.94, vx1 - 0.014, vy1 - 0.33, 0.96), 'cove_led_warm', 0, 'cove', f'{owner}/north-cove-bot', owner)
    k.rect((vx1 - 0.030, vy0 + 0.33, H - 0.18, vx1 - 0.014, vy1 - 0.33, H - 0.16), 'cove_led_warm', 0, 'cove', f'{owner}/north-cove-top', owner)

    # Slab edge fascia trim around the First-Floor void opening (z = H - 0.16 .. H + 0.04)
    void_ring = box(vx0, vy0, vx1, vy1).exterior.buffer(0.035, join_style=2)
    k.poly_mesh(void_ring, H - 0.16, H + 0.04, 'cladding_fluted_teak', 1, 'fascia', f'{owner}/f1-void-fascia', owner)

    # 2. First-floor frameless glass balustrade (height 1.10 m) on all 3 open edges of the 12' x 5' void:
    # North edge (X=vx1, Y=vy0..vy1), West edge (X=vx0..vx1, Y=vy1), South edge (X=vx0, Y=vy0..vy1)
    guard_edges = [
        ('north', (vx1, vy0), (vx1, vy1)),
        ('west', (vx0, vy1), (vx1, vy1)),
        ('south', (vx0, vy0), (vx0, vy1)),
    ]
    for ename, p_a, p_b in guard_edges:
        line = LineString([p_a, p_b])
        shoe = line.buffer(0.032, cap_style=2, join_style=2)
        pane = line.buffer(0.010, cap_style=2, join_style=2)
        rail = line.buffer(0.028, cap_style=2, join_style=2)
        k.poly_mesh(shoe, H, H + 0.085, 'gola_matte_black', 1, 'railing', f'u-void-guard-{ename}-shoe', 'u_open_to_below')
        k.poly_mesh(pane, H + 0.085, H + 1.055, 'glass', 1, 'railing', f'u-void-guard-{ename}-glass', 'u_open_to_below')
        k.poly_mesh(rail, H + 1.055, H + 1.100, 'cladding_fluted_teak', 1, 'railing', f'u-void-guard-{ename}-rail', 'u_open_to_below')

    # 3. Second-floor Raised Glazed Rooflight (z = 2*H = 6.30 m .. 6.68 m)
    z_roof = 2 * H
    outer_curb = box(vx0 - 0.16, vy0 - 0.16, vx1 + 0.16, vy1 + 0.16)
    inner_aperture = box(vx0, vy0, vx1, vy1)
    curb_wall = outer_curb.difference(inner_aperture)
    coping = outer_curb.buffer(0.03, join_style=2).difference(inner_aperture.buffer(-0.02, join_style=2))
    # Raised 320 mm masonry upstand curb + sloped stone coping for drainage falls
    k.poly_mesh(curb_wall, z_roof - 0.15, z_roof + 0.32, 'wall', 2, 'parapet', 's-rooflight-upstand-curb', 's_raised_rooflight')
    k.poly_mesh(coping, z_roof + 0.32, z_roof + 0.36, 'travertine_warm', 2, 'coping', 's-rooflight-curb-coping', 's_raised_rooflight')
    # Perimeter matte-black aluminium skylight frame & 4x2 structural mullion grid
    frame_ring = outer_curb.buffer(-0.04, join_style=2).difference(inner_aperture)
    k.poly_mesh(frame_ring, z_roof + 0.36, z_roof + 0.43, 'gola_matte_black', 2, 'window-surround', 's-rooflight-frame', 's_raised_rooflight')
    # Laminated solar glazing pane across the 12' x 5' rooflight
    k.rect((vx0 - 0.02, vy0 - 0.02, z_roof + 0.385, vx1 + 0.02, vy1 + 0.02, z_roof + 0.415), 'glass', 2, 'glass', 's-rooflight-glass', 's_raised_rooflight')
    # Mullions (3 transverse mullions along 12' Y-axis, 1 longitudinal ridge bar along 5' X-axis)
    for i in range(1, 4):
        my = vy0 + i * (vy1 - vy0) / 4.0
        k.rect((vx0 - 0.04, my - 0.025, z_roof + 0.35, vx1 + 0.04, my + 0.025, z_roof + 0.435), 'gola_matte_black', 2, 'joinery', f's-rooflight-mullion-y-{i}', 's_raised_rooflight')
    mx_mid = 0.5 * (vx0 + vx1)
    k.rect((mx_mid - 0.025, vy0 - 0.04, z_roof + 0.35, mx_mid + 0.025, vy1 + 0.04, z_roof + 0.445), 'gola_matte_black', 2, 'joinery', 's-rooflight-mullion-x', 's_raised_rooflight')
    # Protective perimeter safety guard around the non-walkable rooflight curb on Second Floor
    guard_ring = outer_curb.buffer(0.08, join_style=2).exterior.buffer(0.018, join_style=2)
    k.poly_mesh(guard_ring, z_roof + 0.36, z_roof + 1.10, 'glass', 2, 'railing', 's-rooflight-safety-glass', 's_raised_rooflight')
    k.poly_mesh(guard_ring, z_roof + 1.07, z_roof + 1.11, 'gola_matte_black', 2, 'railing', 's-rooflight-safety-rail', 's_raised_rooflight')

    # 4. 3-Ring Brushed-Gold & Warm-LED Chandelier dropping from the rooflight through the void over the dining table (D-01, D-02, D-04)
    cx, cy = local_m(28.0, 28.5)
    k.cylinder((cx, cy, z_roof + 0.32), 0.18, 0.04, 'chandelier_gold_ring', 2, 'fixture')
    rings = [
        (0.68, H + 1.25, 0.02),
        (0.50, H + 0.55, -0.02),
        (0.34, H - 0.15, 0.01),
    ]
    for idx, (rad, rz, tilt) in enumerate(rings):
        torus_gold = trimesh.creation.torus(major_radius=rad, minor_radius=0.022, major_sections=48, minor_sections=16)
        torus_led = trimesh.creation.torus(major_radius=rad - 0.018, minor_radius=0.014, major_sections=48, minor_sections=12)
        k.node(k.asset(torus_gold, smooth=True), 'chandelier_gold_ring', (cx, cy, rz), rot=(tilt, -tilt, 0), floor=1, role='fixture', name=f'void-chandelier-ring-{idx}', owner=owner)
        k.node(k.asset(torus_led, smooth=True), 'cove_led_warm', (cx, cy, rz - 0.012), rot=(tilt, -tilt, 0), floor=1, role='fixture', name=f'void-chandelier-glow-{idx}', owner=owner)
        for c_i in range(3):
            ang = c_i * 2.0 * math.pi / 3.0 + idx * 0.4
            px = cx + rad * math.cos(ang)
            py = cy + rad * math.sin(ang)
            k.beam((px, py, rz), (cx + 0.12 * math.cos(ang), cy + 0.12 * math.sin(ang), z_roof + 0.34), 0.005, 'chandelier_gold_ring', 1, 'fixture')

    # Daylight shaft lights + warm chandelier lights so the rooflight visibly illuminates the dining & living hall
    k.light((cx, cy, z_roof - 0.20), 65, kind='daylight-shaft')
    k.light((cx, cy, H + 0.90), 50, kind='chandelier')
    k.light((cx, cy, 2.35), 42, kind='chandelier')


def _build_terraces_and_parapets(k: SceneKit, b: dict, H: float) -> None:
    """Build First-Floor (x=47) and Second-Floor (x=44) terrace paving, parapets with glass guards, and built-in planters."""
    # First-floor terrace pavers & wood deck outside study
    u_terrace = next(s for s in b['spaces'] if s['id'] == 'u_large_terrace')
    u_poly = Polygon(np.array(u_terrace['polygon']) / 1000.0)
    k.poly_mesh(u_poly, H + 0.010, H + 0.028, 'terrace_grey_paver', 1, 'floor', 'u-terrace-pavers', 'u_large_terrace')
    # Timber lounge deck outside Study east slider (x_ft: 39..45, y_ft: 11..20)
    dx0, dy0, dx1, dy1 = box_m(39.2, 11.5, 45.0, 20.0)
    k.rect((dx0, dy0, H + 0.028, dx1, dy1, H + 0.048), 'terrace_wood_deck', 1, 'floor', 'u-study-terrace-deck', 'u_large_terrace')

    # Second-floor terrace pavers
    s_terrace = next(s for s in b['spaces'] if s['id'] == 's_open_terrace')
    s_poly = Polygon(np.array(s_terrace['polygon']) / 1000.0)
    k.poly_mesh(s_poly, 2 * H + 0.010, 2 * H + 0.028, 'terrace_grey_paver', 2, 'floor', 's-terrace-pavers', 's_open_terrace')

    # Low masonry parapet + glass railing along First-Floor terrace edge (x_ft=47) and Second-Floor terrace edge (x_ft=44)
    for f_idx, z_b, edges_ft in [
        (1, H, [
            ((47.0, 0.0), (47.0, 40.0)),
            ((23.0, 0.0), (47.0, 0.0)),
            ((18.0, 2.0), (23.0, 2.0)),
            ((33.0, 40.0), (47.0, 40.0)),
        ]),
        (2, 2 * H, [
            ((44.0, 0.0), (44.0, 40.0)),
            ((23.0, 0.0), (44.0, 0.0)),
            ((0.0, 2.0), (23.0, 2.0)),
            ((0.0, 2.0), (0.0, 26.0)),
            ((2.0, 26.0), (2.0, 29.0)),
            ((2.0, 29.0), (7.0, 29.0)),
            ((7.0, 29.0), (7.0, 40.0)),
            ((7.0, 40.0), (17.0, 40.0)),
            ((34.0, 40.0), (44.0, 40.0)),
        ]),
    ]:
        for idx, (pa, pb) in enumerate(edges_ft):
            line = LineString([local_m(*pa), local_m(*pb)])
            upstand = line.buffer(0.075, cap_style=3, join_style=2)
            coping = line.buffer(0.090, cap_style=3, join_style=2)
            glass = line.buffer(0.010, cap_style=2, join_style=2)
            rail = line.buffer(0.025, cap_style=2, join_style=2)
            k.poly_mesh(upstand, z_b, z_b + 0.42, 'wall', f_idx, 'parapet', f'f{f_idx}-parapet-{idx}', f'terrace-{f_idx}')
            k.poly_mesh(coping, z_b + 0.42, z_b + 0.45, 'travertine_warm', f_idx, 'coping', f'f{f_idx}-coping-{idx}', f'terrace-{f_idx}')
            k.poly_mesh(glass, z_b + 0.45, z_b + 1.06, 'glass', f_idx, 'railing', f'f{f_idx}-glass-guard-{idx}', f'terrace-{f_idx}')
            k.poly_mesh(rail, z_b + 1.06, z_b + 1.10, 'gola_matte_black', f_idx, 'railing', f'f{f_idx}-top-rail-{idx}', f'terrace-{f_idx}')


def _add_curtains_and_pelmet(k: SceneKit, x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float, f_idx: int, H: float, owner: str) -> None:
    """Add video-matched floor-to-ceiling sheer ivory + taupe drape curtains with warm 3000K recessed pelmet."""
    bx0, by0, bx1, by1 = box_m(x0_ft, y0_ft, x1_ft, y1_ft)
    z0 = f_idx * H
    # Pelmet box + warm LED strip
    k.rect((bx0 - 0.04, by0 - 0.04, z0 + 2.72, bx1 + 0.04, by1 + 0.04, z0 + 2.96), 'cladding_fluted_teak', f_idx, 'curtain', f'{owner}/pelmet', owner)
    k.rect((bx0 - 0.02, by0 - 0.02, z0 + 2.70, bx1 + 0.02, by1 + 0.02, z0 + 2.72), 'cove_led_warm', f_idx, 'cove', f'{owner}/pelmet-led', owner)
    # Center sheer curtain + flanking taupe outer drapes
    k.rect((bx0 + 0.03, by0 + 0.03, z0 + 0.02, bx1 - 0.03, by1 - 0.03, z0 + 2.72), 'curtain_sheer_ivory', f_idx, 'curtain', f'{owner}/sheer', owner)
    horiz = (bx1 - bx0) < (by1 - by0)
    if horiz:
        w_drape = min(0.45, (by1 - by0) * 0.22)
        k.rect((bx0, by0, z0 + 0.02, bx1, by0 + w_drape, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-L', owner)
        k.rect((bx0, by1 - w_drape, z0 + 0.02, bx1, by1, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-R', owner)
    else:
        w_drape = min(0.45, (bx1 - bx0) * 0.22)
        k.rect((bx0, by0, z0 + 0.02, bx0 + w_drape, by1, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-L', owner)
        k.rect((bx1 - w_drape, by0, z0 + 0.02, bx1, by1, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-R', owner)


def _add_bed_assembly(k: SceneKit, x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float, head_dir: str, f_idx: int, H: float, room_id: str, single: bool = False) -> None:
    """Build a video-matched luxury upholstered bed with fluted headboard, pillows, duvet, and warm cove lighting."""
    bx0, by0, bx1, by1 = box_m(x0_ft, y0_ft, x1_ft, y1_ft)
    z0 = f_idx * H
    # Bed frame & mattress
    k.rect((bx0, by0, z0 + 0.04, bx1, by1, z0 + 0.30), 'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/bed-base', room_id)
    k.rect((bx0 + 0.04, by0 + 0.04, z0 + 0.30, bx1 - 0.04, by1 - 0.04, z0 + 0.54), 'curtain_sheer_ivory', f_idx, 'furniture', f'{room_id}/mattress', room_id)
    k.rect((bx0 + 0.03, by0 + 0.03, z0 + 0.015, bx1 - 0.03, by1 - 0.03, z0 + 0.035), 'cove_led_warm', f_idx, 'cove', f'{room_id}/bed-under-led', room_id)
    # Headboard & pillows according to head_dir in PDF orientation:
    # Recall: +X is North (y_ft=0), -X is South (y_ft=40), +Y is West (x_ft=0), -Y is East (x_ft=50)
    if head_dir == 'north':      # near bx1
        k.rect((bx1 - 0.14, by0 - 0.05, z0 + 0.04, bx1, by1 + 0.05, z0 + 1.25), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.03, by0 + 0.03, z0 + 0.54, bx1 - 0.52, by1 - 0.03, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx1 - 0.46, by0 + 0.12, z0 + 0.54, bx1 - 0.16, by1 - 0.12, z0 + 0.68), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    elif head_dir == 'south':    # near bx0
        k.rect((bx0, by0 - 0.05, z0 + 0.04, bx0 + 0.14, by1 + 0.05, z0 + 1.25), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.52, by0 + 0.03, z0 + 0.54, bx1 - 0.03, by1 - 0.03, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx0 + 0.16, by0 + 0.12, z0 + 0.54, bx0 + 0.46, by1 - 0.12, z0 + 0.68), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    elif head_dir == 'west':     # near by1
        k.rect((bx0 - 0.05, by1 - 0.14, z0 + 0.04, bx1 + 0.05, by1, z0 + 1.25), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.03, by0 + 0.03, z0 + 0.54, bx1 - 0.03, by1 - 0.52, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx0 + 0.12, by1 - 0.46, z0 + 0.54, bx1 - 0.12, by1 - 0.16, z0 + 0.68), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    elif head_dir == 'east':     # near by0 (e.g. Home ICU bed head at east, facing west TV)
        k.rect((bx0 - 0.04, by0, z0 + 0.04, bx1 + 0.04, by0 + 0.14, z0 + 1.18), 'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.03, by0 + 0.52, z0 + 0.54, bx1 - 0.03, by1 - 0.03, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx0 + 0.12, by0 + 0.16, z0 + 0.54, bx1 - 0.12, by0 + 0.46, z0 + 0.70), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    k.furnishing('bed' if not single else 'single-bed', {'id': room_id, 'floor': f_idx}, box(bx0, by0, bx1, by1))


def _add_bath_fittings(k: SceneKit, basin_ft, wc_ft, shower_ft, f_idx: int, H: float, room_id: str) -> None:
    """Place vanity basin + LED mirror, wall-hung WC, and glass shower enclosure."""
    z0 = f_idx * H
    # Vanity basin & backlit mirror
    vx0, vy0, vx1, vy1 = box_m(*basin_ft)
    k.rect((vx0, vy0, z0 + 0.25, vx1, vy1, z0 + 0.82), 'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/vanity-cabinet', room_id)
    k.rect((vx0 - 0.01, vy0 - 0.01, z0 + 0.82, vx1 + 0.01, vy1 + 0.01, z0 + 0.86), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/vanity-top', room_id)
    k.cylinder((0.5 * (vx0 + vx1), 0.5 * (vy0 + vy1), z0 + 0.86), 0.18, 0.11, 'quartz_nano_white', f_idx, 'detail')
    # WC
    wx0, wy0, wx1, wy1 = box_m(*wc_ft)
    k.rect((wx0, wy0, z0 + 0.08, wx1, wy1, z0 + 0.43), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/wc-bowl', room_id)
    # Shower screen & rain head
    sx0, sy0, sx1, sy1 = box_m(*shower_ft)
    k.rect((sx0, sy0, z0 + 0.01, sx1, sy0 + 0.015, z0 + 2.10), 'glass', f_idx, 'glass', f'{room_id}/shower-glass', room_id)
    k.cylinder((0.5 * (sx0 + sx1), 0.5 * (sy0 + sy1), z0 + 2.15), 0.14, 0.015, 'gola_matte_black', f_idx, 'detail')
    k.furnishing('bath-fittings', {'id': room_id, 'floor': f_idx}, box(vx0, vy0, vx1, vy1))


def _furnish_ground_floor(k: SceneKit, b: dict, H: float) -> None:
    """Place all Ground Floor furniture, straight-run kitchen, ceilings, floor border inlays, and curtains."""
    # 1. Glossy 800x800 ivory floor with dark charcoal perimeter inlay border in Living, Dining & Kitchen (K-05, D-03, L-01)
    for zone_name, bounds_ft in [
        ('living-border', (6.5, 16.6, 23.4, 25.4)),
        ('foyer-border', (18.2, 9.6, 23.4, 16.0)),
        ('dining-border', (24.4, 26.4, 35.6, 32.6)),
        ('kitchen-border', (36.4, 26.4, 47.6, 33.4)),
    ]:
        bx0, by0, bx1, by1 = box_m(*bounds_ft)
        outer = box(bx0, by0, bx1, by1)
        inlay = outer.difference(outer.buffer(-0.075, join_style=2))
        k.poly_mesh(inlay, 0.001, 0.004, 'border_inlay_charcoal', 0, 'finish', f'g-{zone_name}', 'living_hall')

    # 2. Straight-Run Modular Kitchen + Work Bay Tall Units + Prep Counter (exact PDF layout + Video K-01..K-06 style)
    kitchen_room = next(s for s in b['spaces'] if s['id'] == 'kitchen')
    kx0, ky0, kx1, ky1 = box_m(48.0, 20.30, 50.0, 33.70)
    sx0, _, sx1, _ = box_m(48.2, 22.25, 49.8, 24.35)
    hx0, _, hx1, _ = box_m(48.2, 30.00, 49.8, 32.15)
    px0, py0, px1, py1 = box_m(34.10, 26.18, 38.10, 27.93)
    ctx = {'room': kitchen_room, 'floor': 0, 'clear': Polygon(np.array(kitchen_room['clear']) / 1000.0), 'placed': []}
    finishes = {
        'fronts': 'kitchen_sage_teal_gloss',
        'loft': 'kitchen_sage_teal_loft',
        'gola': 'gola_matte_black',
        'counter': 'quartz_nano_white',
        'backsplash': 'backsplash_fluted_ivory',
        'casework': 'cladding_fluted_teak',
        'led': 'cove_led_warm',
        'smoked_glass': 'glass_smoked_fluted',
    }
    straight_run_kitchen(k, ctx, H, finishes, spec={
        'x_south': kx0,
        'x_north': kx1,
        'y_wall': 0.060,
        'depth': 0.600,
        'sink_x0': sx0,
        'sink_x1': sx1,
        'hob_x0': hx0,
        'hob_x1': hx1,
        'prep_x0': px0,
        'prep_x1': px1,
        'prep_y0': py0,
        'prep_y1': py1,
    })

    # 3. Dining Hall (x_ft: 24..36, y_ft: 26..33): Banquette on ICU south wall, 6-seater marble table & chairs under void
    banq_x0, banq_y0, banq_x1, banq_y1 = box_m(25.0, 26.20, 31.0, 27.60)
    k.rect((banq_x0, banq_y0, 0.0, banq_x1, banq_y1, 0.46), 'cladding_fluted_teak', 0, 'furniture', 'dining/banquette-base', 'dining_hall')
    k.rect((banq_x0 + 0.02, banq_y0 + 0.02, 0.46, banq_x1 - 0.02, banq_y1 - 0.02, 0.54), 'sofa_taupe_boucle', 0, 'furniture', 'dining/banquette-cushion', 'dining_hall')
    k.rect((banq_x1 - 0.12, banq_y0 + 0.02, 0.54, banq_x1, banq_y1 - 0.02, 0.92), 'sofa_taupe_boucle', 0, 'furniture', 'dining/banquette-back', 'dining_hall')
    # Marble dining table (x_ft: 25.0..31.0, y_ft: 27.65..30.15)
    dtx0, dty0, dtx1, dty1 = box_m(25.0, 27.65, 31.0, 30.15)
    k.rect((dtx0, dty0, 0.72, dtx1, dty1, 0.76), 'dining_marble_top', 0, 'furniture', 'dining/table-top', 'dining_hall')
    k.rect((dtx0 + 0.18, dty0 + 0.35, 0.0, dtx1 - 0.18, dty0 + 0.50, 0.72), 'gola_matte_black', 0, 'furniture', 'dining/table-leg-E', 'dining_hall')
    k.rect((dtx0 + 0.18, dty1 - 0.50, 0.0, dtx1 - 0.18, dty1 - 0.35, 0.72), 'gola_matte_black', 0, 'furniture', 'dining/table-leg-W', 'dining_hall')
    # 3 south dining chairs + 2 end chairs
    for idx, cx_ft in enumerate((26.0, 28.0, 30.0)):
        cx0, cy0, cx1, cy1 = box_m(cx_ft - 0.75, 30.25, cx_ft + 0.75, 31.65)
        k.rect((cx0, cy0, 0.42, cx1, cy1, 0.48), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-s-{idx}', 'dining_hall')
        k.rect((cx0, cy0, 0.48, cx0 + 0.09, cy1, 0.86), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-s-back-{idx}', 'dining_hall')
    for side, (cx0_ft, cx1_ft) in (('west', (23.5, 24.85)), ('east', (31.15, 32.5))):
        cx0, cy0, cx1, cy1 = box_m(cx0_ft, 28.1, cx1_ft, 29.7)
        k.rect((cx0, cy0, 0.42, cx1, cy1, 0.48), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-{side}', 'dining_hall')
        back_y0 = cy1 - 0.09 if side == 'west' else cy0
        back_y1 = cy1 if side == 'west' else cy0 + 0.09
        k.rect((cx0, back_y0, 0.48, cx1, back_y1, 0.86), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-{side}-back', 'dining_hall')
    k.furnishing('dining-set', {'id': 'dining_hall', 'floor': 0}, box(dtx0, dty0, banq_x1, dty1))

    # 4. Living Hall (x_ft: 5.5..24, y_ft: 16..26): Terracotta velvet sofa (L-01), coffee table, 75" TV on south wall (L-02),
    # and signature diagonal linear LED ceiling profiles (L-01)!
    lsx0, lsy0, lsx1, lsy1 = box_m(9.65, 16.45, 16.25, 19.30)
    k.rect((lsx0, lsy0, 0.04, lsx1, lsy1, 0.43), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-seat', 'living_hall')
    k.rect((lsx1 - 0.22, lsy0, 0.43, lsx1, lsy1, 0.84), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-back', 'living_hall')
    k.rect((lsx0, lsy0, 0.43, lsx1, lsy0 + 0.20, 0.66), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-arm-E', 'living_hall')
    k.rect((lsx0, lsy1 - 0.20, 0.43, lsx1, lsy1, 0.66), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-arm-W', 'living_hall')
    # Rug + Coffee table
    rx0, ry0, rx1, ry1 = box_m(8.8, 17.5, 17.0, 24.2)
    k.rect((rx0, ry0, 0.005, rx1, ry1, 0.016), 'curtain_sheer_ivory', 0, 'rug', 'living/area-rug', 'living_hall')
    ctx0, cty0, ctx1, cty1 = box_m(10.65, 20.15, 15.25, 22.40)
    k.rect((ctx0, cty0, 0.36, ctx1, cty1, 0.42), 'dining_marble_top', 0, 'furniture', 'living/coffee-table-top', 'living_hall')
    k.rect((ctx0 + 0.12, cty0 + 0.12, 0.02, ctx1 - 0.12, cty1 - 0.12, 0.36), 'gola_matte_black', 0, 'furniture', 'living/coffee-table-base', 'living_hall')
    # 75" wall-mounted TV on south wall (y_ft=26, x_ft: 10.25..15.65) + walnut floating console & fluted panel (L-02)
    tvx0, tvy0, tvx1, tvy1 = box_m(10.25, 25.45, 15.65, 25.92)
    k.rect((tvx0, tvy0 - 0.25, 0.32, tvx1 + 0.38, tvy1 + 0.25, 0.62), 'cladding_fluted_teak', 0, 'furniture', 'living/tv-console', 'living_hall')
    k.rect((tvx0, tvy0 - 0.15, 0.85, tvx0 + 0.04, tvy1 + 0.15, 2.35), 'cladding_fluted_teak', 0, 'wall-panel', 'living/tv-backpanel', 'living_hall')
    k.rect((tvx0 + 0.04, tvy0, 1.05, tvx0 + 0.09, tvy1, 2.02), 'blackglass', 0, 'furniture', 'living/tv-75in', 'living_hall')
    # Living hall false ceiling with warm cove & diagonal linear LED strips (L-01)
    lcx0, lcy0, lcx1, lcy1 = box_m(6.2, 16.5, 20.5, 25.5)
    k.rect((lcx0, lcy0, H - 0.18, lcx1, lcy1, H - 0.15), 'wall', 0, 'ceiling', 'living/false-ceiling', 'living_hall')
    k.beam((lcx0 + 0.3, lcy0 + 0.4, H - 0.185), (lcx1 - 0.3, lcy1 - 0.4, H - 0.185), 0.035, 'cove_led_warm', 0, 'cove')
    k.beam((lcx0 + 0.3, lcy1 - 0.4, H - 0.185), (lcx1 - 0.3, lcy0 + 0.4, H - 0.185), 0.035, 'cove_led_warm', 0, 'cove')
    k.furnishing('sofa', {'id': 'living_hall', 'floor': 0}, box(lsx0, lsy0, lsx1, lsy1))
    k.furnishing('tv-75in', {'id': 'living_hall', 'floor': 0}, box(tvx0, tvy0, tvx1, tvy1))

    # 5. Home ICU (15' x 17', x_ft: 24..39, y_ft: 9..26):
    # Hospital bed running east-west, head to the east (x_ft=38.5), facing west to 55" TV on west wall (x_ft=24)
    _add_bed_assembly(k, 31.10, 15.80, 38.50, 19.85, 'east', 0, H, 'home_icu')
    # 55" TV on west wall (x_ft: 24.0..24.45, y_ft: 15.80..20.30)
    itvx0, itvy0, itvx1, itvy1 = box_m(24.05, 15.80, 24.45, 20.30)
    k.rect((itvx0, itvy1 - 0.08, 1.05, itvx1, itvy1 - 0.02, 1.85), 'blackglass', 0, 'furniture', 'home_icu/tv-55in', 'home_icu')
    k.furnishing('icu-tv-55in', {'id': 'home_icu', 'floor': 0}, box(itvx0, itvy0, itvx1, itvy1))
    # Bedside clinical monitor & equipment table (x_ft: 36.6..38.5, y_ft: 13.7..15.4)
    eqx0, eqy0, eqx1, eqy1 = box_m(36.60, 13.70, 38.50, 15.40)
    k.rect((eqx0, eqy0, 0.04, eqx1, eqy1, 0.78), 'quartz_nano_white', 0, 'furniture', 'home_icu/equipment-cart', 'home_icu')
    k.rect((eqx0 + 0.10, eqy0 + 0.12, 0.78, eqx1 - 0.10, eqy1 - 0.12, 1.18), 'blackglass', 0, 'detail', 'home_icu/patient-monitor', 'home_icu')
    k.furnishing('icu-equipment', {'id': 'home_icu', 'floor': 0}, box(eqx0, eqy0, eqx1, eqy1))
    # Companion recliner chair in ICU (x_ft: 26.2..28.8, y_ft: 11.2..13.8)
    rcx0, rcy0, rcx1, rcy1 = box_m(26.2, 11.2, 28.8, 13.8)
    k.rect((rcx0, rcy0, 0.04, rcx1, rcy1, 0.45), 'sofa_taupe_boucle', 0, 'furniture', 'home_icu/companion-recliner', 'home_icu')
    k.rect((rcx1 - 0.18, rcy0, 0.45, rcx1, rcy1, 0.92), 'sofa_taupe_boucle', 0, 'furniture', 'home_icu/companion-recliner-back', 'home_icu')
    k.furnishing('icu-companion-chair', {'id': 'home_icu', 'floor': 0}, box(rcx0, rcy0, rcx1, rcy1))
    _add_curtains_and_pelmet(k, 24.5, 9.1, 38.5, 9.6, 0, H, 'home_icu/north-curtain')

    # 6. Caregiver Room (8' x 10', x_ft: 0..8, y_ft: 2..12) & Caregiver Bath (5' x 6', x_ft: 0..5, y_ft: 12..18)
    _add_bed_assembly(k, 0.40, 4.50, 6.90, 7.90, 'west', 0, H, 'caregiver', single=True)
    _add_bath_fittings(k, (0.4, 14.0, 2.0, 15.7), (0.4, 16.0, 2.4, 17.4), (0.4, 12.3, 3.0, 13.9), 0, H, 'caregiver_bath')

    # 7. Drawing Room (9'6" x 14', x_ft: 8..17.5, y_ft: 2..16): Sofa on north wall + coffee table + curtains
    dsx0, dsy0, dsx1, dsy1 = box_m(9.75, 2.35, 15.75, 5.20)
    k.rect((dsx0, dsy0, 0.04, dsx1, dsy1, 0.43), 'sofa_taupe_boucle', 0, 'furniture', 'drawing_room/sofa-seat', 'drawing_room')
    k.rect((dsx1 - 0.20, dsy0, 0.43, dsx1, dsy1, 0.84), 'sofa_taupe_boucle', 0, 'furniture', 'drawing_room/sofa-back', 'drawing_room')
    dct0, dcty0, dct1, dcty1 = box_m(10.8, 6.2, 14.7, 8.2)
    k.rect((dct0, dcty0, 0.36, dct1, dcty1, 0.42), 'dining_marble_top', 0, 'furniture', 'drawing_room/coffee-table', 'drawing_room')
    _add_curtains_and_pelmet(k, 10.5, 2.1, 16.8, 2.6, 0, H, 'drawing_room/north-curtain')
    k.furnishing('drawing-sofa', {'id': 'drawing_room', 'floor': 0}, box(dsx0, dsy0, dsx1, dsy1))

    # 8. Ground Master Bedroom (15' x 14', x_ft: 2..17, y_ft: 26..40) & Master Bath (5'6" x 8', x_ft: 0..5.5, y_ft: 18..26)
    _add_bed_assembly(k, 6.75, 33.10, 12.75, 39.60, 'south', 0, H, 'master_bedroom')
    # Wardrobe on north wall of master bedroom (x_ft: 5.6..15.2, y_ft: 26.2..28.1)
    mwx0, mwy0, mwx1, mwy1 = box_m(5.6, 26.2, 15.2, 28.1)
    k.rect((mwx0, mwy0, 0.0, mwx1, mwy1, 2.40), 'cladding_fluted_teak', 0, 'furniture', 'master_bedroom/wardrobe', 'master_bedroom')
    k.furnishing('wardrobe', {'id': 'master_bedroom', 'floor': 0}, box(mwx0, mwy0, mwx1, mwy1))
    _add_bath_fittings(k, (0.4, 20.3, 2.0, 22.0), (0.4, 22.3, 2.4, 23.7), (0.4, 18.3, 3.2, 20.1), 0, H, 'master_bath')

    # 9. Store (7' x 6', x_ft: 34..41, y_ft: 34..40) & Wash Area (9' x 6', x_ft: 41..50, y_ft: 34..40)
    stx0, sty0, stx1, sty1 = box_m(34.2, 34.2, 35.8, 39.8)
    for sz in (0.45, 0.95, 1.45, 1.95):
        k.rect((stx0, sty0, sz, stx1, sty1, sz + 0.04), 'cladding_fluted_teak', 0, 'furniture', f'store/shelf-{sz}', 'store')
    k.furnishing('store-shelves', {'id': 'store', 'floor': 0}, box(stx0, sty0, stx1, sty1))

    # Washer + utility sink + floor drain in Wash Area
    wmx0, wmy0, wmx1, wmy1 = box_m(47.6, 34.5, 49.8, 36.7)
    k.rect((wmx0, wmy0, 0.0, wmx1, wmy1, 0.85), 'quartz_nano_white', 0, 'furniture', 'wash_area/washer', 'wash_area')
    k.cylinder((wmx0 + 0.32, wmy1 + 0.01, 0.45), 0.22, 0.02, 'blackglass', 0, 'detail')
    usx0, usy0, usx1, usy1 = box_m(47.8, 36.8, 49.8, 39.2)
    k.rect((usx0, usy0, 0.0, usx1, usy1, 0.85), 'kitchen_sage_teal_gloss', 0, 'furniture', 'wash_area/utility-sink', 'wash_area')
    k.furnishing('washer', {'id': 'wash_area', 'floor': 0}, box(wmx0, wmy0, wmx1, wmy1))
    k.furnishing('utility-sink', {'id': 'wash_area', 'floor': 0}, box(usx0, usy0, usx1, usy1))

    # 10. Verandah deck (16' x 9', x_ft: 23..39, y_ft: 0..9)
    vx0, vy0, vx1, vy1 = box_m(23.0, 0.0, 39.0, 9.0)
    k.rect((vx0, vy0, 0.002, vx1, vy1, 0.028), 'terrace_wood_deck', 0, 'floor', 'verandah/wood-deck', 'verandah')


def _furnish_first_floor(k: SceneKit, b: dict, H: float) -> None:
    """Place all First Floor furniture: Master Suite, Study/Meditation, Shared Bath, Medium Bedroom, Terrace seating & planters."""
    z1 = H
    # 1. Master Bedroom (18' x 15', x_ft: 0..18, y_ft: 2..17): Bed head on north wall, bench at foot, side table
    _add_bed_assembly(k, 8.60, 2.35, 14.60, 8.85, 'north', 1, H, 'u_master_bedroom')
    mbx0, mby0, mbx1, mby1 = box_m(9.30, 9.00, 13.90, 10.30)
    k.rect((mbx0, mby0, z1 + 0.04, mbx1, mby1, z1 + 0.45), 'sofa_taupe_boucle', 1, 'furniture', 'u_master_bedroom/foot-bench', 'u_master_bedroom')
    k.furnishing('master-bench', {'id': 'u_master_bedroom', 'floor': 1}, box(mbx0, mby0, mbx1, mby1))
    stx0, sty0, stx1, sty1 = box_m(15.35, 2.35, 17.15, 4.15)
    k.rect((stx0, sty0, z1 + 0.04, stx1, sty1, z1 + 0.55), 'cladding_fluted_teak', 1, 'furniture', 'u_master_bedroom/side-table', 'u_master_bedroom')
    _add_curtains_and_pelmet(k, 2.5, 2.1, 10.5, 2.6, 1, H, 'u_master_bedroom/north-curtain')

    # 2. Dressing Room (8' x 7', x_ft: 7..15, y_ft: 17..24): Wardrobes
    dwx0, dwy0, dwx1, dwy1 = box_m(12.8, 17.3, 14.8, 23.7)
    k.rect((dwx0, dwy0, z1, dwx1, dwy1, z1 + 2.40), 'cladding_fluted_teak', 1, 'furniture', 'u_dressing/wardrobe-east', 'u_dressing')
    dwx2, dwy2, dwx3, dwy3 = box_m(7.3, 22.0, 12.8, 23.7)
    k.rect((dwx2, dwy2, z1, dwx3, dwy3, z1 + 2.40), 'kitchen_sage_teal_gloss', 1, 'furniture', 'u_dressing/wardrobe-south', 'u_dressing')
    k.furnishing('dressing-wardrobes', {'id': 'u_dressing', 'floor': 1}, box(dwx0, dwy0, dwx1, dwy1))

    # 3. En-suite Bath (7' x 9', x_ft: 0..7, y_ft: 17..26) & Shared Bath (6' x 8', x_ft: 33..39, y_ft: 26..34)
    _add_bath_fittings(k, (0.3, 20.5, 2.1, 22.5), (0.3, 23.8, 2.5, 25.5), (0.3, 17.3, 3.4, 20.1), 1, H, 'u_en_suite')
    _add_bath_fittings(k, (37.0, 28.1, 38.7, 29.9), (36.8, 31.4, 38.7, 32.8), (33.4, 31.0, 36.2, 33.7), 1, H, 'u_shared_bath')

    # 4. Study / Meditation Room (15' x 13', x_ft: 24..39, y_ft: 8..21):
    # Study desk & chair at NW (x_ft: 24.4..29.4, y_ft: 8.35..10.35), Meditation platform at NE (x_ft: 33.8..38.6, y_ft: 8.35..12.85)
    sdx0, sdy0, sdx1, sdy1 = box_m(24.4, 8.35, 29.4, 10.35)
    k.rect((sdx0, sdy0, z1 + 0.72, sdx1, sdy1, z1 + 0.76), 'cladding_fluted_teak', 1, 'furniture', 'u_study_meditation/desk-top', 'u_study_meditation')
    k.rect((sdx0 + 0.08, sdy0 + 0.08, z1, sdx1 - 0.08, sdy0 + 0.16, z1 + 0.72), 'gola_matte_black', 1, 'furniture', 'u_study_meditation/desk-leg', 'u_study_meditation')
    scx0, scy0, scx1, scy1 = box_m(26.1, 10.6, 27.7, 12.2)
    k.rect((scx0, scy0, z1 + 0.44, scx1, scy1, z1 + 0.50), 'sofa_taupe_boucle', 1, 'furniture', 'u_study_meditation/desk-chair', 'u_study_meditation')
    k.furnishing('study-desk', {'id': 'u_study_meditation', 'floor': 1}, box(sdx0, sdy0, sdx1, sdy1))

    mpx0, mpy0, mpx1, mpy1 = box_m(33.8, 8.35, 38.6, 12.85)
    k.rect((mpx0, mpy0, z1 + 0.02, mpx1, mpy1, z1 + 0.22), 'cladding_fluted_teak', 1, 'furniture', 'u_study_meditation/meditation-platform', 'u_study_meditation')
    k.rect((mpx0 + 0.04, mpy0 + 0.04, z1, mpx1 - 0.04, mpy1 - 0.04, z1 + 0.025), 'cove_led_warm', 1, 'cove', 'u_study_meditation/meditation-led', 'u_study_meditation')
    k.cylinder((0.5 * (mpx0 + mpx1), 0.5 * (mpy0 + mpy1), z1 + 0.22), 0.38, 0.09, 'sofa_taupe_boucle', 1, 'furniture')
    k.furnishing('meditation-platform', {'id': 'u_study_meditation', 'floor': 1}, box(mpx0, mpy0, mpx1, mpy1))

    # 5. Medium Bedroom (15' x 11', x_ft: 2..17, y_ft: 29..40): Bed head on west wall + Wardrobe on south wall
    _add_bed_assembly(k, 2.35, 31.30, 8.85, 36.80, 'west', 1, H, 'u_medium_bedroom')
    uwx0, uwy0, uwx1, uwy1 = box_m(10.2, 37.8, 16.7, 39.75)
    k.rect((uwx0, uwy0, z1, uwx1, uwy1, z1 + 2.40), 'cladding_fluted_teak', 1, 'furniture', 'u_medium_bedroom/wardrobe', 'u_medium_bedroom')
    k.furnishing('medium-wardrobe', {'id': 'u_medium_bedroom', 'floor': 1}, box(uwx0, uwy0, uwx1, uwy1))

    # 6. First-Floor Terrace Seating outside Study + NE & SE Planters
    for idx, (cx0_ft, cy0_ft, cx1_ft, cy1_ft) in enumerate([
        (41.3, 13.0, 43.3, 15.0),
        (41.3, 17.0, 43.3, 19.0),
    ]):
        tx0, ty0, tx1, ty1 = box_m(cx0_ft, cy0_ft, cx1_ft, cy1_ft)
        k.rect((tx0, ty0, z1 + 0.05, tx1, ty1, z1 + 0.42), 'sofa_taupe_boucle', 1, 'furniture', f'u_large_terrace/chair-{idx}', 'u_large_terrace')
    tbx0, tby0, tbx1, tby1 = box_m(41.6, 15.3, 43.0, 16.7)
    k.rect((tbx0, tby0, z1 + 0.05, tbx1, tby1, z1 + 0.45), 'travertine_warm', 1, 'furniture', 'u_large_terrace/side-table', 'u_large_terrace')
    k.furnishing('terrace-seating', {'id': 'u_large_terrace', 'floor': 1}, box(tbx0, tby0, tbx1, tby1))

    for pname, pbounds in [('ne-planter', (40.0, 0.25, 46.7, 1.75)), ('se-planter', (40.0, 38.25, 46.7, 39.75))]:
        px0, py0, px1, py1 = box_m(*pbounds)
        k.rect((px0, py0, z1 + 0.03, px1, py1, z1 + 0.55), 'travertine_warm', 1, 'planter', f'u_large_terrace/{pname}', 'u_large_terrace')
        k.plant(0.5 * (px0 + px1), 0.5 * (py0 + py1), z1 + 0.52, 'shrub_round', f=1, scale=0.65)


def _furnish_second_floor(k: SceneKit, b: dict, H: float) -> None:
    """Place all Second Floor furniture: 3 computer desks & chairs, sofa facing east to 75" TV, and terrace planters."""
    z2 = 2 * H
    # 1. Three computer desks + dual monitors + office chairs along north wall at west end (x_ft: 4..20, y_ft: 8.35..12.5)
    for idx, (dx0_ft, dx1_ft) in enumerate([(4.1, 8.9), (9.6, 14.4), (15.1, 19.9)]):
        bx0, by0, bx1, by1 = box_m(dx0_ft, 8.35, dx1_ft, 10.55)
        k.rect((bx0, by0, z2 + 0.72, bx1, by1, z2 + 0.76), 'cladding_fluted_teak', 2, 'furniture', f's_office_tv_hall/desk-{idx+1}', 's_office_tv_hall')
        k.rect((bx0 + 0.06, by0 + 0.06, z2, bx1 - 0.06, by0 + 0.14, z2 + 0.72), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/desk-leg-E-{idx+1}', 's_office_tv_hall')
        k.rect((bx0 + 0.06, by1 - 0.14, z2, bx1 - 0.06, by1 - 0.06, z2 + 0.72), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/desk-leg-W-{idx+1}', 's_office_tv_hall')
        # Computer monitor on desk
        k.rect((bx1 - 0.22, 0.5 * (by0 + by1) - 0.32, z2 + 0.76, bx1 - 0.16, 0.5 * (by0 + by1) + 0.32, z2 + 1.14), 'blackglass', 2, 'detail', f's_office_tv_hall/monitor-{idx+1}', 's_office_tv_hall')
        # Office chair south of desk
        cx0, cy0, cx1, cy1 = box_m(0.5 * (dx0_ft + dx1_ft) - 0.85, 10.8, 0.5 * (dx0_ft + dx1_ft) + 0.85, 12.4)
        k.rect((cx0, cy0, z2 + 0.44, cx1, cy1, z2 + 0.50), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/chair-{idx+1}', 's_office_tv_hall')
        k.rect((cx0, cy0, z2 + 0.50, cx0 + 0.10, cy1, z2 + 0.94), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/chair-back-{idx+1}', 's_office_tv_hall')
        k.furnishing(f'office-desk-{idx+1}', {'id': 's_office_tv_hall', 'floor': 2}, box(bx0, by0, bx1, by1))

    # 2. Lounge sofa facing east to the 75" TV (x_ft: 20.5..23.3, y_ft: 16..24) + coffee table + 75" TV on east wall (x_ft=33)
    ssx0, ssy0, ssx1, ssy1 = box_m(20.5, 16.0, 23.3, 24.0)
    k.rect((ssx0, ssy0, z2 + 0.04, ssx1, ssy1, z2 + 0.43), 'sofa_terracotta_velvet', 2, 'furniture', 's_office_tv_hall/sofa-seat', 's_office_tv_hall')
    k.rect((ssx0, ssy1 - 0.22, z2 + 0.43, ssx1, ssy1, z2 + 0.84), 'sofa_terracotta_velvet', 2, 'furniture', 's_office_tv_hall/sofa-back', 's_office_tv_hall')
    sctx0, scty0, sctx1, scty1 = box_m(24.4, 17.6, 26.4, 22.4)
    k.rect((sctx0, scty0, z2 + 0.36, sctx1, scty1, z2 + 0.42), 'dining_marble_top', 2, 'furniture', 's_office_tv_hall/coffee-table', 's_office_tv_hall')
    stvx0, stvy0, stvx1, stvy1 = box_m(32.3, 17.0, 32.85, 22.4)
    k.rect((stvx0, stvy0 - 0.20, z2 + 0.30, stvx1 + 0.05, stvy1 + 0.20, z2 + 0.58), 'cladding_fluted_teak', 2, 'furniture', 's_office_tv_hall/tv-console', 's_office_tv_hall')
    k.rect((stvx0, stvy0, z2 + 1.05, stvx0 + 0.06, stvy1, z2 + 2.02), 'blackglass', 2, 'furniture', 's_office_tv_hall/tv-75in', 's_office_tv_hall')
    k.furnishing('office-sofa', {'id': 's_office_tv_hall', 'floor': 2}, box(ssx0, ssy0, ssx1, ssy1))
    k.furnishing('office-tv-75in', {'id': 's_office_tv_hall', 'floor': 2}, box(stvx0, stvy0, stvx1, stvy1))

    # 3. Second-floor terrace planters as drawn in PDF
    for pname, pbounds in [
        ('nw-planter', (0.25, 2.25, 7.0, 3.6)),
        ('ne-planter', (37.0, 0.25, 43.75, 1.6)),
        ('sw-planter', (7.25, 38.25, 13.8, 39.75)),
        ('se-planter', (37.0, 38.25, 43.75, 39.75)),
    ]:
        px0, py0, px1, py1 = box_m(*pbounds)
        k.rect((px0, py0, z2 + 0.03, px1, py1, z2 + 0.55), 'travertine_warm', 2, 'planter', f's_open_terrace/{pname}', 's_open_terrace')
        k.plant(0.5 * (px0 + px1), 0.5 * (py0 + py1), z2 + 0.52, 'shrub_round', f=2, scale=0.65)


def _add_site_context_and_gates(k: SceneKit, scene: dict, building: dict, H: float) -> None:
    """Reuse colony context from Tirumala 6 and build the East Pedestrian Gate + North Car Porch Vehicle Gate."""
    from .tirumala_6_site import boundary_layout, build_enclosure
    planning = building['planning']
    planning['lowerPorchMm'] = 0
    spans = planning.get('eastGates') or [('east-walk-gate', 'pedestrian', 11125.2, 9753.6)]
    boundary = boundary_layout(building, spans)
    building['siteBoundary'] = boundary
    build_enclosure(k, scene, boundary)

    if planning.get('colonyMaterials'):
        scene['materials'].update(planning['colonyMaterials'])
    if planning.get('colony'):
        scene['context'] = {
            **planning['colony'],
            'project_id': 'tirumala-7',
            'detailLevel': 'reference',
            'entryGaps': [[g['x0_mm'] / 1000.0, g['x1_mm'] / 1000.0] for g in boundary['gates']],
            'northVehicleGate': {'x_ft': [39.5, 49.5], 'y_ft': 0.0},
        }
        scene['nodes'] = [
            n for n in scene['nodes']
            if n['id'] != 'north-road' and not (
                n['floor'] == -1 and n['role'] == 'site' and n['material'] in ('asphalt', 'paver', 'linen')
            )
        ]

    # Build the North-South Car Porch paving, parked car (facing north road), and North Vehicle Gate (x_ft: 39.5..49.5, y_ft=0)
    px0, py0, px1, py1 = box_m(39.0, 0.0, 50.0, 20.0)
    k.rect((px0, py0, -0.28, px1, py1, 0.002), 'terrace_grey_paver', 0, 'floor', 'car_porch/paving', 'car_porch')
    # Parked car oriented North-South (length along X, width along Y) inside Car Porch (x_ft: 41.8..47.6, y_ft: 4.2..17.2)
    cx0, cy0, cx1, cy1 = box_m(41.8, 4.2, 47.6, 17.2)
    k.rb((0.5 * (cx0 + cx1), 0.5 * (cy0 + cy1), 0.42), (cx1 - cx0, cy1 - cy0, 0.56), 'ivory-vitrified', 0, 'vehicle', 0.12, owner='parked-car')
    k.rb((0.5 * (cx0 + cx1) - 0.18, 0.5 * (cy0 + cy1), 0.92), ((cx1 - cx0) * 0.56, (cy1 - cy0) * 0.84, 0.50), 'glass_smoked_fluted', 0, 'vehicle', 0.10, owner='parked-car')
    k.rb((0.5 * (cx0 + cx1) - 0.18, 0.5 * (cy0 + cy1), 1.18), ((cx1 - cx0) * 0.50, (cy1 - cy0) * 0.80, 0.06), 'ivory-vitrified', 0, 'vehicle', 0.04, owner='parked-car')
    for wx in (cx0 + 0.68, cx1 - 0.68):
        for wy in (cy0 + 0.08, cy1 - 0.08):
            k.cylinder((wx, wy, 0.30), 0.30, 0.22, 'gola_matte_black', 0, 'vehicle', rot=(math.pi / 2, 0, 0))
    # Vehicle ramp from North Road (X = 12.192..13.20 m, Y = 0.15..3.20 m)
    gx0, gy0, gx1, gy1 = box_m(39.5, 0.0, 49.5, 0.5)
    k.rect((12.192, gy0, -0.30, 13.15, gy1, -0.02), 'terrace_grey_paver', -1, 'landscape', 'north-vehicle-ramp', 'north-vehicle-gate')
    # Sliding matte-black & teak vehicle gate at the north boundary of the car porch
    k.rect((12.15, gy0, -0.25, 12.22, gy1, 1.35), 'gola_matte_black', -1, 'gate', 'north-vehicle-gate', 'north-vehicle-gate')

    # East pedestrian arrival steps & path (from East Road at y_ft: 3.5..8.0 across porch & verandah to 6' double doors)
    eax0, eay0, eax1, eay1 = box_m(49.5, 3.5, 50.0, 8.0)
    k.rect((eax0, -0.85, -0.30, eax1, 0.0, -0.15), 'travertine_warm', -1, 'landscape', 'east-arrival-step-1', 'east-pedestrian-gate')
    k.rect((eax0, -0.42, -0.15, eax1, 0.0, 0.0), 'travertine_warm', -1, 'landscape', 'east-arrival-step-2', 'east-pedestrian-gate')


def _configure_cameras_and_walk(scene: dict, H: float) -> None:
    """Configure hero, cutaway, exterior, interior, and walkthrough presets for Tirumala 7."""
    def cam(eye_ft, target_ft, z_eye, z_target, fov=52):
        ex, ey = local_m(*eye_ft)
        tx, ty = local_m(*target_ft)
        return {'position': [round(ex, 3), round(ey, 3), round(z_eye, 3)],
                'target': [round(tx, 3), round(ty, 3), round(z_target, 3)],
                'fov': fov}

    scene['cameras'].update({
        'hero': {'position': [21.5, -10.5, 8.2], 'target': [6.2, 6.8, 3.4], 'fov': 44},
        'exterior': {'position': [21.5, -10.5, 8.2], 'target': [6.2, 6.8, 3.4], 'fov': 44},
        'east_arrival': {'position': [9.8, -9.2, 2.4], 'target': [8.8, 4.5, 2.0], 'fov': 48},
        'north_frontage': {'position': [23.8, 6.8, 3.2], 'target': [6.5, 7.2, 3.4], 'fov': 46},
        'colony_overview': {'position': [28.0, -16.0, 14.5], 'target': [6.0, 7.6, 3.0], 'fov': 45},
        'roof_terraces': {'position': [19.5, -8.5, 13.8], 'target': [5.8, 7.8, 6.4], 'fov': 46},
        'kitchen_run': cam((35.5, 29.8), (49.2, 26.8), 1.52, 1.42, 58),
        'kitchen_from_dining': cam((25.5, 30.5), (49.0, 27.2), 1.52, 1.42, 56),
        'dining_double_height': cam((18.5, 29.2), (29.5, 28.2), 1.45, 3.85, 62),
        'living_hall': cam((21.5, 19.5), (11.5, 22.8), 1.52, 1.32, 58),
        'living_to_icu': cam((15.5, 22.2), (35.0, 17.5), 1.52, 1.30, 56),
        'icu': cam((25.5, 12.0), (36.5, 18.5), 1.55, 1.15, 58),
        'verandah': cam((37.5, 3.2), (24.5, 7.2), 1.52, 1.35, 58),
        'drawing_room': cam((15.8, 14.2), (11.5, 4.5), 1.50, 1.20, 58),
        'master_bedroom': cam((13.8, 28.8), (6.5, 36.8), 1.48, 1.12, 58),
        'gallery_void': cam((18.2, 28.5), (29.5, 28.5), H + 1.58, 1.20, 60),
        'master_suite': cam((3.0, 15.5), (12.5, 5.5), H + 1.48, H + 1.10, 58),
        'study_meditation': cam((25.5, 19.2), (35.5, 11.5), H + 1.50, H + 1.10, 58),
        'medium_bedroom': cam((15.2, 30.8), (4.5, 36.0), H + 1.50, H + 1.10, 58),
        'east_terrace': cam((43.5, 34.5), (41.5, 10.0), H + 1.58, H + 1.35, 56),
        'office_tv_hall': cam((7.5, 22.0), (27.5, 15.0), 2 * H + 1.38, 2 * H + 1.15, 58),
        'north_terrace': cam((39.0, 4.2), (10.0, 5.5), 2 * H + 1.58, 2 * H + 1.30, 56),
        'rooflight': cam((35.5, 25.5), (25.5, 28.8), 2 * H + 1.75, H + 1.20, 60),
        'stair_lobby': cam((30.5, 34.8), (18.5, 36.5), 2 * H + 1.55, 2 * H + 0.90, 58),
    })

    # Walkthrough floor starts
    f0_x, f0_y = local_m(20.5, 18.5)
    f1_x, f1_y = local_m(19.0, 24.0)
    f2_x, f2_y = local_m(19.0, 22.0)
    arr_x, arr_y = local_m(48.0, 6.0)
    scene['walk'] = {
        'eye_height': 1.63,
        'arrival': {'position': [round(arr_x, 3), round(arr_y, 3), 0.0], 'yaw_deg': 270},
        'floors': [
            {'floor': 0, 'position': [round(f0_x, 3), round(f0_y, 3), 0.0], 'yaw_deg': 180},
            {'floor': 1, 'position': [round(f1_x, 3), round(f1_y, 3), round(H, 3)], 'yaw_deg': 180},
            {'floor': 2, 'position': [round(f2_x, 3), round(f2_y, 3), round(2 * H, 3)], 'yaw_deg': 0},
        ],
    }


def make_tirumala_7_scene(building: dict, report: dict, base_scene_builder) -> dict:
    """Build the complete Tirumala 7 3D scene."""
    scene = base_scene_builder(building, report)
    H = scene['floor_height']

    # Remove generic auto-placed furniture/stairs/guards/canopies/skirting so only exact PDF + video-styled geometry remains
    drop_roles = {'furniture', 'stair', 'railing', 'curtain', 'canopy', 'band', 'pipe', 'carport', 'skirting', 'post'}
    scene['nodes'][:] = [
        n for n in scene['nodes']
        if n.get('role') not in drop_roles
        and not str(n.get('owner', '')).startswith('stair-')
        and not (n.get('floor') == -1 and n.get('role') in ('gate', 'fixture', 'detail', 'plinth', 'step'))
    ]
    scene['furniture'][:] = []
    scene['editables'][:] = []

    _register_video_materials(scene)
    import random
    k = SceneKit(random.Random(707))

    _build_stair_294(k, H)
    _build_double_height_shaft_and_rooflight(k, H)
    _build_terraces_and_parapets(k, building, H)
    _furnish_ground_floor(k, building, H)
    _furnish_first_floor(k, building, H)
    _furnish_second_floor(k, building, H)
    _add_site_context_and_gates(k, scene, building, H)
    _configure_cameras_and_walk(scene, H)

    for i, node in enumerate(k.nodes):
        if node['id'].startswith('object-'):
            node['id'] = f't7-detail-{i}'
    scene['nodes'].extend(k.nodes)
    scene['assets'].update(k.assets)
    scene['lights'].extend(k.lights)
    for plant in k.vegetation:
        plant['id'] = 't7-' + plant['id']
    scene['vegetation'].extend(k.vegetation)
    scene['furniture'].extend(k.furniture)
    scene['colliders'].extend(k.colliders)
    scene['editables'].extend(k.editables)

    return scene
