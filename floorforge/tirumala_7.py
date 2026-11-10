"""Tirumala 7: 50' x 40' three-floor corner home with full-span double-height atrium sunroof,
3' east kitchen setback, 22' car porch with NE car gate, verandah north lawn court, and video-matched interiors."""
from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
import numpy as np
import trimesh
from shapely.affinity import scale as shp_scale
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from .custom_plan import geometry, regions
from .modular_kitchen import straight_run_kitchen
from .scene_kit import Kit as SceneKit
from .spaces import SPACE_REGISTRY

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
        'east_setback': 'courtyard',
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
    """Populate exact 3-floor geometry into building `b` from `plan-reference.json`."""
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

    # 1. Build non-overlapping spaces across Ground (0), First (1), and Second (2) floors
    floor_keys = [('ground', 0, 'floor-0', ''), ('first', 1, 'floor-1', 'u_'), ('second', 2, 'floor-2', 's_')]
    space_polys_by_floor: dict[int, dict[str, Polygon]] = {0: {}, 1: {}, 2: {}}

    for fkey, f_idx, fl_id, prefix in floor_keys:
        f_data = ref['floors'][fkey]
        for raw_id, r in f_data['rooms'].items():
            if raw_id in ('prep_counter_zone', 'bedroom_roof_non_walkable') or raw_id.startswith('not_'):
                continue
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
            if sid == 'hall_entry':
                poly = unary_union([poly, box_mm(5.0, 16.0, 5.5, 18.0)])
            elif sid == 'living_hall':
                poly = unary_union([poly, box_mm(17.5, 9.0, 24.0, 16.0)])
            elif sid == 'dining_hall':
                poly = unary_union([
                    poly,
                    box_mm(21.0, 26.0, 24.0, 33.0),
                    box_mm(33.0, 33.0, 35.0, 35.0),
                ])
            elif sid == 'u_family_gallery':
                poly = unary_union([
                    box_mm(18.0, 9.0, 24.0, 25.0),   # Central gallery hall
                    box_mm(24.0, 21.0, 39.0, 25.0),  # North atrium overlook walkway
                    box_mm(17.0, 25.0, 20.5, 33.0),  # 3.5' West Atrium Bridge (from stair arrival)
                    box_mm(30.5, 25.0, 34.0, 33.0),  # 3.5' East Sky-Lit Bridge (to Floor 1->2 stair)
                    box_mm(7.0, 24.0, 17.0, 29.0),   # West suite & medium bedroom passage
                    box_mm(15.0, 17.0, 18.0, 25.0),  # Dressing east alcove
                ])
            clear_poly = poly
            space_polys_by_floor[f_idx][sid] = poly

            open_sky_space = raw_id in ('outside_gully', 'west_gully', 'east_setback')
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
                'enclosed': spec['enclosed'] and not open_sky_space,
                'roofed': spec['roofed'] and not open_sky_space,
                'walkable': spec['floor'] and raw_id not in ('open_to_below', 'raised_rooflight'),
                'wet': spec['wet'],
                'drain': kind in ('bathroom', 'drying-room') or open_sky_space,
            }
            if kind == 'bathroom':
                rec['mechanicalVentilation'] = True
            if open_sky_space:
                rec['openToSky'] = True
            if raw_id == 'caregiver':
                rec['bedType'] = 'single'
            if raw_id == 'car_porch':
                rec['openSkyStripFt'] = {'x_ft': [47.0, 50.0], 'y_ft': [0.0, 22.0]}
            if raw_id in ('open_to_below', 'raised_rooflight'):
                rec['openToBelow'] = True
            if raw_id == 'raised_rooflight':
                rec['glassCover'] = True
            spaces.append(rec)

        # Continuous walkable terrace on First Floor (east edge x=47')
        if f_idx == 1:
            t_parts = [
                box_mm(23.0, 0.0, 47.0, 8.0),
                box_mm(18.0, 2.0, 24.0, 9.0),
                box_mm(39.0, 8.0, 47.0, 40.0),
                box_mm(33.0, 33.0, 39.0, 40.0),
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

        # Continuous walkable terrace on Second Floor (east edge x=44')
        if f_idx == 2:
            t2_parts = [
                box_mm(23.0, 0.0, 44.0, 8.0),
                box_mm(0.0, 2.0, 23.0, 8.0),
                box_mm(0.0, 8.0, 3.0, 26.0),
                box_mm(3.0, 25.0, 17.0, 26.0),
                box_mm(2.0, 26.0, 17.0, 29.0),
                box_mm(7.0, 29.0, 17.0, 40.0),
                box_mm(34.0, 8.0, 44.0, 40.0),
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

    # 2. Build walls on each floor from `plan-reference.json` wall axes
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
            outdoor_adj = any(s in ('outside_gully', 'west_gully', 'east_setback', 'car_porch', 'verandah', 'covered_entry', 'u_large_terrace', 's_open_terrace') for s in adj)
            is_ext = (
                len(adj) == 1
                or outdoor_adj
                or any(c in (0.0, 47.0, 50.0) for c in (a_ft[0], b_ft[0]))
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
        'kitchen_east_window_1': (['kitchen', 'east_setback'], None),
        'kitchen_east_window_2': (['kitchen', 'east_setback'], None),
        'wash_east_window': (['wash_area', 'east_setback'], None),
        'wash_south_window': (['wash_area', 'outside'], None),
        'master_bath_high_window': (['master_bath', 'outside'], None),
        'master_west_window': (['master_bedroom', 'west_gully'], None),
        'master_south_window': (['master_bedroom', 'outside'], None),
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
        'sf_hall_lobby_door': (['s_office_tv_hall', 's_lobby_passage'], 's_lobby_passage'),
        'sf_hall_terrace_slider': (['s_office_tv_hall', 's_open_terrace'], None),
        'sf_lobby_terrace_door': (['s_lobby_passage', 's_open_terrace'], 's_lobby_passage'),
        'sf_stair_terrace_door': (['s_stair_lobby', 's_open_terrace'], 's_stair_lobby'),
        'sf_hall_north_window': (['s_office_tv_hall', 's_open_terrace'], None),
        'sf_hall_west_window': (['s_office_tv_hall', 's_open_terrace'], None),
        'sf_hall_east_window': (['s_office_tv_hall', 's_open_terrace'], None),
        'sf_hall_atrium_window': (['s_office_tv_hall', 's_raised_rooflight'], None),
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
            raw_openings.append({**w_item, 'kind': 'window', 'fixed': 'fixed' in w_item['id'] or 'atrium' in w_item['id']})

        for o in raw_openings:
            oid = o['id']
            w_axis, w_val_str = o['wall'].split('=')
            w_val = float(w_val_str)
            s0, s1 = float(o['span_ft'][0]), float(o['span_ft'][1])
            if oid == 'icu_north_fixed_glazing_west':
                s1 = min(s1, 27.85)
            elif oid == 'icu_north_fixed_glazing_east':
                s0 = max(s0, 35.15)
            if w_axis == 'y':
                a_ft, b_ft = [s0, w_val], [s1, w_val]
            else:
                a_ft, b_ft = [w_val, s0], [w_val, s1]

            p0 = local_mm(*a_ft)
            p1 = local_mm(*b_ft)
            span_start, span_end = sorted((p0, p1))
            span_line = LineString([span_start, span_end])
            mid = span_line.centroid

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
                if oid in ('kitchen_east_window_1', 'kitchen_east_window_2'):
                    sill = 960
                    height = 1340
                elif oid == 'sf_hall_atrium_window':
                    sill = 1050
                    height = 1450
                elif 'icu_north_fixed' in oid:
                    sill = 150
                    height = 2100
                elif 'bath' in oid or 'ensuite' in oid or 'wash_' in oid:
                    sill = 1050
                    height = 1200
                else:
                    sill = 750
                    height = 1650
            elif kind == 'cased':
                sill = 0
                height = 2400 if oid == 'icu_west_clear_opening' else 2250

            # Hinge single-leaf doors on whichever jamb sits closer to a perpendicular wall so open leaves fold flat
            perp_lines = [
                LineString([pw['a'], pw['b']])
                for pw in f_walls
                if (abs(pw['a'][1] - pw['b'][1]) < 1.0) != horiz
            ]
            if perp_lines and kind in ('door', 'entry') and not o.get('double_leaf'):
                d_start = min(pl.distance(w_line.interpolate(offset)) for pl in perp_lines)
                d_end = min(pl.distance(w_line.interpolate(offset + width)) for pl in perp_lines)
                best_hinge = 'start' if d_start <= d_end else 'end'
            else:
                best_hinge = 'start'

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
                'hinge': best_hinge,
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
    # Well is x_ft: 17..33 (width 16' = 4876.8 mm along Y), y_ft: 33..40 (depth 7' = 2133.6 mm along X)
    stair_box = box_mm(17.0, 33.0, 33.0, 40.0)
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
            'tread_mm': 304.8,                    # 1.0 ft >= 250 mm
            'headroom_mm': 2775.0,                # >= 2100 mm
            'tread_sequence': [2, 9, 4],
            'direction': 'east-south-west-north',
        })

    # 5. Build Floor Plates & Roofs across all 3 levels
    # First-floor double-height atrium spans full 8' N-S gap from Home ICU/Dining wall (y=25') right up to Staircase (y=33'),
    # framed symmetrically by the 3.5' West Atrium Bridge (x=17..20.5) and 3.5' East Sky-Lit Bridge (x=30.5..34.0).
    void_f1 = box_mm(20.5, 25.0, 30.5, 33.0)       # 10' x 8' (80 sq ft) full-gap double-height dining atrium
    void_f2 = box_mm(20.5, 25.0, 34.0, 33.0)       # 13.5' x 8' (108 sq ft) raised glazed sunroof above atrium + east bridge
    stair_well_f1 = box_mm(17.0, 33.0, 33.0, 40.0)
    stair_well_f2 = box_mm(17.0, 33.0, 33.0, 40.0)

    # Plate 0: full 50' x 40' ground footprint (with open-to-sky gullies, 3' east setback, and outer 3' of 22' car porch)
    plate0_outline = box_mm(0.0, 0.0, 50.0, 40.0)
    # Plate 1: First-floor slab (east edge straight at x=47 for full 40', matching Ground Kitchen 3' east setback!)
    plate1_outline = box_mm(0.0, 0.0, 47.0, 40.0).difference(
        unary_union([box_mm(0.0, 0.0, 23.0, 2.0), box_mm(0.0, 26.0, 2.0, 40.0)])
    )
    plate1_slab = plate1_outline.difference(unary_union([void_f1, stair_well_f1]))

    # Plate 2: Second-floor slab (east edge straight at x=44 for full 40'; 6' east setback)
    plate2_outline = box_mm(0.0, 0.0, 44.0, 40.0).difference(
        unary_union([box_mm(0.0, 0.0, 23.0, 2.0), box_mm(0.0, 26.0, 2.0, 40.0)])
    )
    plate2_slab = plate2_outline.difference(unary_union([void_f2, stair_well_f2]))

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
                {'id': 'u-void-opening', 'regions': regions(void_f1)},
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
                {'id': 's-rooflight-opening', 'regions': regions(void_f2)},
                {'id': 'main-stair-void-2', 'stairId': 'main-stair', 'regions': regions(stair_well_f2)},
            ],
        },
    ]

    # Floor 0 ceiling excludes open-to-sky gullies, the entire x=47..50 east strip (outer 3' of 22' car porch + 3' kitchen setback),
    # the 10' x 8' full-span dining atrium void, and the stair well.
    g_open_sky = unary_union([
        box_mm(0.0, 0.0, 23.0, 2.0),
        box_mm(0.0, 26.0, 2.0, 40.0),
        box_mm(47.0, 0.0, 50.0, 40.0),
    ])
    roof0_covered = plate0_outline.difference(unary_union([g_open_sky, void_f1, stair_well_f1]))
    roof0_exposed = roof0_covered.difference(plate1_outline)

    # Floor 1 ceiling covers enclosed rooms on Floor 1, excluding the 13.5' x 8' sunroof shaft (so both atrium & east bridge are sky-lit!)
    u_enclosed = unary_union([
        box_mm(0.0, 2.0, 18.0, 17.0),   # u_master_bedroom
        box_mm(7.0, 17.0, 15.0, 24.0),  # u_dressing
        box_mm(0.0, 17.0, 7.0, 26.0),   # u_en_suite
        box_mm(24.0, 8.0, 39.0, 21.0),  # u_study_meditation
        box_mm(15.0, 9.0, 39.0, 33.0),  # u_family_gallery + bridges + u_shared_bath
        box_mm(7.0, 24.0, 17.0, 29.0),  # u_family_gallery west corridor
        box_mm(2.0, 29.0, 17.0, 40.0),  # u_medium_bedroom
        box_mm(17.0, 33.0, 33.0, 40.0), # u_stair
    ]).difference(void_f2)
    roof1_covered = u_enclosed.difference(stair_well_f2)
    roof1_exposed = roof1_covered.difference(plate2_outline)

    # Floor 2 roof covers enclosed indoor rooms (s_office_tv_hall, s_lobby_passage, s_stair_lobby)
    s_enclosed = unary_union([
        box_mm(3.0, 8.0, 34.0, 25.0),
        box_mm(17.0, 25.0, 20.5, 33.0),
        box_mm(17.0, 33.0, 34.0, 40.0),
    ])
    roof2_covered = s_enclosed

    roofs = [
        {'id': 'roof-floor-0', 'floor': 0, 'regions': regions(roof0_exposed), 'ceiling': regions(roof0_covered)},
        {'id': 'roof-floor-1', 'floor': 1, 'regions': regions(roof1_exposed), 'ceiling': regions(roof1_covered)},
        {
            'id': 'roof-floor-2',
            'floor': 2,
            'regions': regions(roof2_covered),
            'ceiling': regions(roof2_covered),
            'rooflight': regions(void_f2),
        },
    ]

    # 6. Build Guards around First-Floor 10' x 8' atrium, Second-Floor 13.5' x 8' raised sunroof, and stepped terraces
    guards = [
        {
            'id': 'u-void-guard-north',
            'owner': 'u_open_to_below',
            'floor': 1,
            'edge': 'north',
            'points': [local_mm(20.5, 25.0), local_mm(30.5, 25.0)],
            'height': 1100,
        },
        {
            'id': 'u-void-guard-west',
            'owner': 'u_open_to_below',
            'floor': 1,
            'edge': 'west',
            'points': [local_mm(20.5, 25.0), local_mm(20.5, 33.0)],
            'height': 1100,
        },
        {
            'id': 'u-void-guard-east',
            'owner': 'u_open_to_below',
            'floor': 1,
            'edge': 'east',
            'points': [local_mm(30.5, 25.0), local_mm(30.5, 33.0)],
            'height': 1100,
        },
        {
            'id': 'u-void-guard-south',
            'owner': 'u_open_to_below',
            'floor': 1,
            'edge': 'south',
            'points': [local_mm(20.5, 33.0), local_mm(29.5, 33.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-north',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'north',
            'points': [local_mm(20.5, 25.0), local_mm(34.0, 25.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-west',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'west',
            'points': [local_mm(20.5, 25.0), local_mm(20.5, 33.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-south',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'south',
            'points': [local_mm(20.5, 33.0), local_mm(34.0, 33.0)],
            'height': 1100,
        },
        {
            'id': 's-rooflight-curb-east',
            'owner': 's_raised_rooflight',
            'floor': 2,
            'edge': 'east',
            'points': [local_mm(34.0, 25.0), local_mm(34.0, 33.0)],
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
    """Register the video-sampled and architectural luxury materials into scene['materials']."""
    from .tirumala_5_finishes import apply_house_daylight, apply_house_palette
    mats = scene['materials']
    for name, base, color, rough in [
        ('travertine', 'stone', '#cfb99b', .56),
        ('olive-velvet', 'fabric', '#686b50', .90),
        ('smoked-oak', 'timber', '#79543c', .46),
        ('bronze', 'brass', '#ad8658', .30),
        ('acoustic-felt', 'fabric', '#45434a', .96),
        ('cinema-screen', 'linen', '#f4ede0', .83),
    ]:
        if base in mats:
            mats[name] = {**mats[base], 'color': color, 'roughness': rough}
    apply_house_palette(mats)
    profile = scene.setdefault('presentation', {})
    apply_house_daylight(profile)
    profile['interior'].update(daylightExposureScale=.38, contrast=1.09, punch=.30)
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
        'cladding_fluted_teak': {'color': '#8f5b3c', 'roughness': 0.40, 'kind': 'wood', 'texture': 'wood'},
        'cove_led_warm': {'color': '#ffe4b5', 'roughness': 0.10, 'emission': 1.2, 'emissive': '#ffd89b', 'emissive_strength': 4.2},
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
        'terrace_wood_deck': {'color': '#8a5a3c', 'roughness': 0.50, 'kind': 'wood', 'tile': [0.15, 1.20], 'tile_m': [0.15, 1.20]},
        'terrace_grey_paver': {'color': '#cfcbc2', 'roughness': 0.56, 'kind': 'paver', 'tile': [0.60, 0.60], 'tile_m': [0.60, 0.60]},
        'verandah_lawn_velvet': {'color': '#556d43', 'roughness': 0.88, 'kind': 'grass'},
        'car_pearl_metallic': {'color': '#eae7e1', 'roughness': 0.20, 'metallic': 0.14, 'clearcoat': 0.65, 'kind': 'metal'},
        'tv_oled_screen': {'color': '#090a0d', 'roughness': 0.24, 'metallic': 0.04, 'clearcoat': 0.08, 'kind': 'metal'},
    })
    mats['wall'].update({'color': '#f3efe6', 'roughness': 0.60})
    mats['floor'] = dict(mats['floor_ivory_vitrified_800'])
    mats['Walnut'] = {'color': '#6e472f', 'roughness': 0.38, 'kind': 'wood'}
    mats['walnut'] = {'color': '#6e472f', 'roughness': 0.38, 'kind': 'wood'}


def _build_stair_294(k: SceneKit, H: float) -> None:
    """Build the 2/9/4 U-turn staircase (18 risers x 175 mm = 3150 mm) for Ground->First and First->Second.

    Stair well in PDF feet: x_ft: 17..33, y_ft: 33..40.
    - Flight 1 (East leg, x_ft: 29.5..33.0): starts at y_ft=33.0 (fed on Floor 1 by the 3.5' East Sky-Lit Bridge!),
      climbs 2 treads SOUTH to y_ft=36.5 (risers 1..2), plus SE corner landing (x_ft: 29.5..33.0, y_ft: 36.5..40.0) at riser 3.
    - Flight 2 (South leg, y_ft: 36.5..40.0): climbs 9 treads WEST from x_ft=29.5 to x_ft=20.5 (risers 4..12, 304.8 mm treads),
      plus SW corner landing (x_ft: 17.0..20.5, y_ft: 36.5..40.0) at riser 13.
    - Flight 3 (West leg, x_ft: 17.0..20.5): climbs 4 treads NORTH from y_ft=36.5 to y_ft=33.0 (risers 14..17),
      stepping onto the 3.5' West Atrium Bridge / Second-Floor Lobby at y_ft=33.0 (riser 18 = +3.150 m).
    """
    riser = H / 18.0
    for f_idx in (0, 1):
        z0 = f_idx * H
        owner = f'stair-{f_idx}'

        def step_block(x0_ft, y0_ft, x1_ft, y1_ft, r_idx, name, is_landing=False):
            bx0, by0, bx1, by1 = box_m(x0_ft, y0_ft, x1_ft, y1_ft)
            top_z = z0 + r_idx * riser
            bot_z = max(z0, top_z - (0.16 if is_landing else riser * 1.35))
            k.rect((bx0, by0, bot_z, bx1, by1, top_z - 0.032), 'floor_ivory_vitrified_800', f_idx, 'stair', f'{owner}/{name}-body', owner)
            k.rect((bx0 - 0.006, by0 - 0.006, top_z - 0.032, bx1 + 0.006, by1 + 0.006, top_z), 'cladding_fluted_teak', f_idx, 'stair', f'{owner}/{name}-tread', owner)
            if not is_landing:
                k.rect((bx0 + 0.04, by0 + 0.04, top_z - 0.042, bx1 - 0.04, by1 - 0.04, top_z - 0.032), 'cove_led_warm', f_idx, 'cove', f'{owner}/{name}-led', owner)

        # Flight 1: 2 treads south along east leg (x_ft: 29.5..33.0, y_ft: 33.0 -> 36.5)
        dy1 = 3.5 / 2.0
        for i in range(2):
            ya = 33.0 + i * dy1
            step_block(29.5, ya, 33.0, ya + dy1, i + 1, f'f1-tread-{i+1}')
        step_block(29.5, 36.5, 33.0, 40.0, 3, 'se-landing', is_landing=True)

        # Flight 2: 9 treads west along south leg (x_ft: 29.5 -> 20.5, y_ft: 36.5..40.0)
        dx2 = 9.0 / 9.0
        for i in range(9):
            xb = 29.5 - i * dx2
            step_block(xb - dx2, 36.5, xb, 40.0, 4 + i, f'f2-tread-{i+1}')
        step_block(17.0, 36.5, 20.5, 40.0, 13, 'sw-landing', is_landing=True)

        # Flight 3: 4 treads north along west leg (x_ft: 17.0..20.5, y_ft: 36.5 -> 33.0)
        dy3 = 3.5 / 4.0
        for i in range(4):
            yb = 36.5 - i * dy3
            step_block(17.0, yb - dy3, 20.5, yb, 14 + i, f'f3-tread-{i+1}')

        # Inner well frameless glass balustrade & warm teak handrail
        ix0, iy0, ix1, iy1 = box_m(20.5, 33.0, 29.5, 36.5)
        k.beam((ix1, iy0, z0 + 1.05), (ix0, iy0, z0 + 1.45), 0.040, 'cladding_fluted_teak', f_idx, 'railing')
        k.rect((ix0 - 0.012, iy0, z0 + 0.55, ix0 + 0.012, iy1, z0 + 3.05), 'glass', f_idx, 'railing', f'{owner}/inner-glass-s', owner)
        k.beam((ix0, iy0, z0 + 1.45), (ix0, iy1, z0 + 3.12), 0.040, 'cladding_fluted_teak', f_idx, 'railing')
        k.beam((ix0, iy1, z0 + 3.12), (ix1, iy1, z0 + 4.02), 0.040, 'cladding_fluted_teak', f_idx, 'railing')

    # Second-floor stair well south/east arrival balustrade along open inner well (x_ft: 20.5..33.0, y_ft=33.0..36.5)
    z2 = 2 * H
    sx0, sy0, sx1, sy1 = box_m(20.5, 33.0, 33.0, 36.5)
    for ename, pa, pb in [
        ('west', (sx0, sy1), (sx1, sy1)),
        ('south', (sx0, sy0), (sx0, sy1)),
    ]:
        line = LineString([pa, pb])
        k.poly_mesh(line.buffer(0.028, cap_style=2), z2, z2 + 0.08, 'gola_matte_black', 2, 'railing', f's-stair-well-shoe-{ename}', 's_stair_lobby')
        k.poly_mesh(line.buffer(0.010, cap_style=2), z2 + 0.08, z2 + 1.05, 'glass', 2, 'railing', f's-stair-well-glass-{ename}', 's_stair_lobby')
        k.poly_mesh(line.buffer(0.026, cap_style=2), z2 + 1.05, z2 + 1.10, 'cladding_fluted_teak', 2, 'railing', f's-stair-well-rail-{ename}', 's_stair_lobby')


def _build_double_height_shaft_and_rooflight(k: SceneKit, H: float) -> None:
    """Build the full-span Double-Height Dining Atrium (x_ft: 20.5..30.5, y_ft: 25.0..33.0, 10' x 8' = 80 sq ft)
    and Overhead Glazed Sunroof (x_ft: 20.5..34.0, y_ft: 25.0..33.0, 13.5' x 8' = 108 sq ft):
    - Spans the ENTIRE 8' N-S gap from the Dining Hall north wall (y=25') right up to the Staircase (y=33')
    - Symmetrical 3.5' West & East Atrium Bridges on First Floor with fluted-teak slab fascias & frameless glass guards
    - Two-storey travertine & fluted-teak feature cladding + warm linear LED coves
    - Raised architectural solar-glass sunroof with 5x2 matte-black structural mullion grid directly overhead
    - Sculptural 3-ring brushed-gold & warm-LED chandelier centered over the marble dining table
    """
    vx0, vy0, vx1, vy1 = box_m(20.5, 25.0, 30.5, 33.0)
    rx0, ry0, rx1, ry1 = box_m(20.5, 25.0, 34.0, 33.0)
    owner = 'double-height-shaft'

    # 1. Full-height fluted teak & travertine feature wall on u_shared_bath west wall (x_ft=34.0 -> Y=ry0 + 0.062) at First Floor
    wy_face = ry0 + 0.064
    k.rect((rx0 + 0.05, wy_face, H + 0.02, rx1 - 0.05, wy_face + 0.026, 2 * H - 0.02), 'cladding_fluted_teak', 1, 'wall-panel', f'{owner}/east-fluted-wall', owner)
    n_ribs = int((rx1 - rx0 - 0.14) / 0.055)
    for i in range(n_ribs):
        rx_i = rx0 + 0.07 + i * 0.055
        k.rect((rx_i, wy_face + 0.024, H + 0.05, rx_i + 0.024, wy_face + 0.038, 2 * H - 0.05), 'cladding_fluted_teak', 1, 'detail', f'{owner}/east-rib-{i}', owner)
    k.rect((rx0 + 0.06, wy_face + 0.025, H + 0.06, rx0 + 0.085, wy_face + 0.042, 2 * H - 0.06), 'cove_led_warm', 1, 'cove', f'{owner}/east-led-s', owner)
    k.rect((rx1 - 0.085, wy_face + 0.025, H + 0.06, rx1 - 0.06, wy_face + 0.042, 2 * H - 0.06), 'cove_led_warm', 1, 'cove', f'{owner}/east-led-n', owner)

    # Ground-floor Dining north wall feature cladding (Home ICU south wall at y_ft=25.0 -> inner south face X = vx1 - 0.064)
    # Spanning x_ft: 24.2..34.8 cleanly below the First-Floor atrium slab!
    dn_x0, dn_y0, dn_x1, dn_y1 = box_m(24.2, 25.0, 34.8, 25.2)
    nx_face = vx1 - 0.064
    k.rect((nx_face - 0.022, dn_y0, 0.55, nx_face, dn_y1, H - 0.16), 'travertine_warm', 0, 'wall-panel', f'{owner}/north-travertine', owner)
    k.rect((nx_face - 0.036, dn_y0 + 0.45, 0.85, nx_face - 0.020, dn_y1 - 0.45, H - 0.22), 'cladding_fluted_teak', 0, 'wall-panel', f'{owner}/north-teak-inset', owner)
    k.rect((nx_face - 0.038, dn_y0 + 0.42, 0.83, nx_face - 0.022, dn_y1 - 0.42, 0.85), 'cove_led_warm', 0, 'cove', f'{owner}/north-cove-bot', owner)
    k.rect((nx_face - 0.038, dn_y0 + 0.42, H - 0.22, nx_face - 0.022, dn_y1 - 0.42, H - 0.20), 'cove_led_warm', 0, 'cove', f'{owner}/north-cove-top', owner)

    # Crisp fluted-teak architectural fascia around the 10' x 8' First-Floor atrium slab opening + structural header beam at y=33'
    void_ring = box(vx0, vy0, vx1, vy1).exterior.buffer(0.038, join_style=2)
    k.poly_mesh(void_ring, H - 0.18, H + 0.03, 'cladding_fluted_teak', 1, 'fascia', f'{owner}/f1-void-fascia', owner)
    # Recessed warm perimeter cove glow around the atrium opening
    cove_ring = box(vx0, vy0, vx1, vy1).buffer(0.015, join_style=2).difference(box(vx0, vy0, vx1, vy1))
    k.poly_mesh(cove_ring, H - 0.19, H - 0.17, 'cove_led_warm', 1, 'cove', f'{owner}/f1-void-cove', owner)

    # 2. First-floor frameless glass balustrade (height 1.10 m) on all 4 open edges of the 10' x 8' atrium
    guard_edges = [
        ('north', (vx1 + 0.05, vy0 - 0.04), (vx1 + 0.05, vy1 + 0.04)),
        ('west', (vx0, vy1 + 0.05), (vx1 + 0.05, vy1 + 0.05)),
        ('east', (vx0 + 0.10, vy0 - 0.05), (vx1 + 0.05, vy0 - 0.05)),
        ('south', (vx0, vy0 + 0.30), (vx0, vy1 + 0.05)),
    ]
    for ename, p_a, p_b in guard_edges:
        line = LineString([p_a, p_b])
        shoe = line.buffer(0.030, cap_style=2, join_style=2)
        pane = line.buffer(0.010, cap_style=2, join_style=2)
        rail = line.buffer(0.026, cap_style=2, join_style=2)
        k.poly_mesh(shoe, H, H + 0.085, 'gola_matte_black', 1, 'railing', f'u-void-guard-{ename}-shoe', 'u_open_to_below')
        k.poly_mesh(pane, H + 0.085, H + 1.055, 'glass', 1, 'railing', f'u-void-guard-{ename}-glass', 'u_open_to_below')
        k.poly_mesh(rail, H + 1.055, H + 1.100, 'cladding_fluted_teak', 1, 'railing', f'u-void-guard-{ename}-rail', 'u_open_to_below')

    # 3. Second-floor Full-Span Raised Architectural Glazed Sunroof (13.5' x 8' = 108 sq ft, x_ft: 20.5..34.0, y_ft: 25.0..33.0)
    z_roof = 2 * H
    # Inset 70 mm from north/west/south walls so the curb sits cleanly against the masonry walls without overlapping indoor rooms!
    inner_ap = box(rx0 + 0.06, ry0 + 0.02, rx1 - 0.06, ry1 - 0.06)
    outer_curb = inner_ap.buffer(0.14, join_style=2)
    curb_wall = outer_curb.difference(inner_ap)
    coping = outer_curb.buffer(0.025, join_style=2).difference(inner_ap.buffer(-0.015, join_style=2))
    k.poly_mesh(curb_wall, z_roof - 0.16, z_roof + 0.34, 'wall', 2, 'parapet', 's-rooflight-upstand-curb', 's_raised_rooflight')
    k.poly_mesh(coping, z_roof + 0.34, z_roof + 0.38, 'travertine_warm', 2, 'coping', 's-rooflight-curb-coping', 's_raised_rooflight')

    frame_ring = outer_curb.buffer(-0.03, join_style=2).difference(inner_ap)
    k.poly_mesh(frame_ring, z_roof + 0.38, z_roof + 0.45, 'gola_matte_black', 2, 'window-surround', 's-rooflight-frame', 's_raised_rooflight')
    gx0, gy0, gx1, gy1 = inner_ap.bounds
    k.rect((gx0 - 0.02, gy0 - 0.02, z_roof + 0.405, gx1 + 0.02, gy1 + 0.02, z_roof + 0.435), 'glass', 2, 'glass', 's-rooflight-glass', 's_raised_rooflight')

    # 5x2 structural architectural mullion grid across the 13.5' x 8' sunroof
    for i in range(1, 5):
        my = gy0 + i * (gy1 - gy0) / 5.0
        k.rect((gx0 - 0.03, my - 0.022, z_roof + 0.37, gx1 + 0.03, my + 0.022, z_roof + 0.455), 'gola_matte_black', 2, 'joinery', f's-rooflight-mullion-y-{i}', 's_raised_rooflight')
    mx_mid = 0.5 * (gx0 + gx1)
    k.rect((mx_mid - 0.025, gy0 - 0.03, z_roof + 0.37, mx_mid + 0.025, gy1 + 0.03, z_roof + 0.465), 'gola_matte_black', 2, 'joinery', 's-rooflight-mullion-x', 's_raised_rooflight')

    # Frameless safety balustrade along the open east terrace side of the sunroof (x_ft=34.0, y_ft: 25.0..33.0)
    east_guard_line = LineString([(rx0 + 0.02, ry0 - 0.14), (rx1 - 0.02, ry0 - 0.14)])
    k.poly_mesh(east_guard_line.buffer(0.028, cap_style=2), z_roof, z_roof + 0.085, 'gola_matte_black', 2, 'railing', 's-rooflight-safety-shoe', 's_raised_rooflight')
    k.poly_mesh(east_guard_line.buffer(0.010, cap_style=2), z_roof + 0.085, z_roof + 1.06, 'glass', 2, 'railing', 's-rooflight-safety-glass', 's_raised_rooflight')
    k.poly_mesh(east_guard_line.buffer(0.025, cap_style=2), z_roof + 1.06, z_roof + 1.10, 'gola_matte_black', 2, 'railing', 's-rooflight-safety-rail', 's_raised_rooflight')

    # 4. Sculptural 3-Ring Brushed-Gold & Warm-LED Chandelier suspended down the center of the 10' x 8' atrium (x=26.2', y=29.0')
    cx, cy = local_m(26.2, 29.0)
    k.cylinder((cx, cy, z_roof + 0.36), 0.20, 0.04, 'chandelier_gold_ring', 2, 'fixture')
    rings = [
        (0.76, H + 1.45, 0.03),
        (0.56, H + 0.65, -0.03),
        (0.38, H - 0.12, 0.02),
    ]
    for idx, (rad, rz, tilt) in enumerate(rings):
        torus_gold = trimesh.creation.torus(major_radius=rad, minor_radius=0.022, major_sections=56, minor_sections=16)
        torus_led = trimesh.creation.torus(major_radius=rad - 0.018, minor_radius=0.014, major_sections=56, minor_sections=12)
        k.node(k.asset(torus_gold, smooth=True), 'chandelier_gold_ring', (cx, cy, rz), rot=(tilt, -tilt, 0), floor=1, role='fixture', name=f'void-chandelier-ring-{idx}', owner=owner)
        k.node(k.asset(torus_led, smooth=True), 'cove_led_warm', (cx, cy, rz - 0.012), rot=(tilt, -tilt, 0), floor=1, role='fixture', name=f'void-chandelier-glow-{idx}', owner=owner)
        for c_i in range(3):
            ang = c_i * 2.0 * math.pi / 3.0 + idx * 0.42
            px = cx + rad * math.cos(ang)
            py = cy + rad * math.sin(ang)
            k.beam((px, py, rz), (cx + 0.14 * math.cos(ang), cy + 0.14 * math.sin(ang), z_roof + 0.38), 0.005, 'chandelier_gold_ring', 1, 'fixture')

    k.light((cx, cy, z_roof - 0.15), 75, kind='daylight-shaft')
    k.light((cx, cy, H + 0.95), 52, kind='chandelier')
    k.light((cx, cy, 2.35), 44, kind='chandelier')


def _build_terraces_and_parapets(k: SceneKit, b: dict, H: float) -> None:
    """Build First-Floor (x=47) and Second-Floor (x=44) terrace paving, wood lounge decks, and glass-topped parapets (zero round shrubs)."""
    u_terrace = next(s for s in b['spaces'] if s['id'] == 'u_large_terrace')
    u_poly = Polygon(np.array(u_terrace['polygon']) / 1000.0)
    k.poly_mesh(u_poly, H + 0.010, H + 0.028, 'terrace_grey_paver', 1, 'floor', 'u-terrace-pavers', 'u_large_terrace')
    dx0, dy0, dx1, dy1 = box_m(39.2, 11.2, 45.4, 20.4)
    k.rect((dx0, dy0, H + 0.028, dx1, dy1, H + 0.048), 'terrace_wood_deck', 1, 'floor', 'u-study-terrace-deck', 'u_large_terrace')

    s_terrace = next(s for s in b['spaces'] if s['id'] == 's_open_terrace')
    s_poly = Polygon(np.array(s_terrace['polygon']) / 1000.0)
    k.poly_mesh(s_poly, 2 * H + 0.010, 2 * H + 0.028, 'terrace_grey_paver', 2, 'floor', 's-terrace-pavers', 's_open_terrace')
    sdx0, sdy0, sdx1, sdy1 = box_m(22.5, 0.6, 35.5, 7.6)
    k.rect((sdx0, sdy0, 2 * H + 0.028, sdx1, sdy1, 2 * H + 0.048), 'terrace_wood_deck', 2, 'floor', 's-north-terrace-deck', 's_open_terrace')

    for f_idx, z_b, edges_ft in [
        (1, H, [
            ((47.0, 0.0), (47.0, 40.0)),
            ((23.0, 0.0), (47.0, 0.0)),
            ((18.0, 2.0), (23.0, 2.0)),
            ((2.0, 26.0), (2.0, 29.0)),
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

    # Architectural travertine roof cornice & low parapet cap on the top 2nd-floor roof slab (z = 3*H)
    top_roof_poly = shp_scale(
        unary_union([
            box_mm(3.0, 8.0, 34.0, 25.0),
            box_mm(17.0, 25.0, 20.5, 33.0),
            box_mm(17.0, 33.0, 34.0, 40.0),
        ]),
        xfact=0.001, yfact=0.001, origin=(0, 0),
    )
    top_ring = top_roof_poly.buffer(0.08, join_style=2).difference(top_roof_poly.buffer(-0.10, join_style=2))
    k.poly_mesh(top_ring, 3 * H, 3 * H + 0.24, 'wall', 2, 'roof', 'f2-top-roof-parapet', 'roof-floor-2')
    k.poly_mesh(top_ring.buffer(0.02, join_style=2), 3 * H + 0.24, 3 * H + 0.29, 'travertine_warm', 2, 'roof', 'f2-top-roof-coping', 'roof-floor-2')


def _add_tv_wall_assembly(
    k: SceneKit,
    wall_side: str,
    wall_coord_ft: float,
    span0_ft: float,
    span1_ft: float,
    f_idx: int,
    H: float,
    room_id: str,
    tv_id: str,
    width_m: float,
    height_m: float,
    with_console: bool = True,
    with_panel: bool = True,
) -> Polygon:
    """Mount a complete, ultra-crisp OLED TV + fluted-teak media panel + floating console strictly proud of the 60 mm half-wall face.

    `wall_side` indicates which wall of the room hosts the TV:
    - `'south'`: wall at `y_ft = wall_coord_ft`, facing NORTH (`+X`) into the room
    - `'north'`: wall at `y_ft = wall_coord_ft`, facing SOUTH (`-X`) into the room
    - `'east'`:  wall at `x_ft = wall_coord_ft`, facing WEST (`+Y`) into the room
    - `'west'`:  wall at `x_ft = wall_coord_ft`, facing EAST (`-Y`) into the room
    """
    z0 = f_idx * H
    z_tv0 = z0 + 1.04
    z_tv1 = z_tv0 + height_m
    half_w = 0.5 * width_m

    if wall_side in ('south', 'north'):
        xw = (40.0 - wall_coord_ft) * 0.3048
        ym = 0.5 * ((50.0 - span0_ft) * 0.3048 + (50.0 - span1_ft) * 0.3048)
        s = 1.0 if wall_side == 'south' else -1.0
        x_face = xw + s * 0.064
        if with_panel:
            xa, xb = sorted((x_face, x_face + s * 0.026))
            k.rect((xa, ym - half_w - 0.24, z0 + 0.76, xb, ym + half_w + 0.24, z0 + 2.42),
                   'cladding_fluted_teak', f_idx, 'wall-panel', f'{room_id}/{tv_id}-panel', room_id)
            k.rect((xa, ym - half_w - 0.26, z0 + 0.74, xb, ym + half_w + 0.26, z0 + 0.76),
                   'cove_led_warm', f_idx, 'cove', f'{room_id}/{tv_id}-halo', room_id)
        if with_console:
            ca, cb = sorted((x_face, x_face + s * 0.36))
            k.rect((ca, ym - half_w - 0.28, z0 + 0.28, cb, ym + half_w + 0.28, z0 + 0.54),
                   'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/{tv_id}-console', room_id)
            k.rect((ca, ym - half_w - 0.28, z0 + 0.54, cb, ym + half_w + 0.28, z0 + 0.565),
                   'quartz_nano_white', f_idx, 'furniture', f'{room_id}/{tv_id}-console-top', room_id)
        ba, bb = sorted((x_face + s * 0.030, x_face + s * 0.062))
        sa, sb = sorted((x_face + s * 0.062, x_face + s * 0.070))
        k.rect((ba, ym - half_w - 0.015, z_tv0 - 0.015, bb, ym + half_w + 0.015, z_tv1 + 0.015),
               'gola_matte_black', f_idx, 'detail', f'{room_id}/{tv_id}-bezel', room_id)
        k.rect((sa, ym - half_w, z_tv0, sb, ym + half_w, z_tv1),
               'tv_oled_screen', f_idx, 'furniture', f'{room_id}/{tv_id}', room_id)
        return box(min(ba, sb), ym - half_w, max(ba, sb), ym + half_w)

    yw = (50.0 - wall_coord_ft) * 0.3048
    xm = 0.5 * ((40.0 - span0_ft) * 0.3048 + (40.0 - span1_ft) * 0.3048)
    s = 1.0 if wall_side == 'east' else -1.0
    y_face = yw + s * 0.064
    if with_panel:
        ya, yb = sorted((y_face, y_face + s * 0.026))
        k.rect((xm - half_w - 0.22, ya, z0 + 0.76, xm + half_w + 0.22, yb, z0 + 2.42),
               'cladding_fluted_teak', f_idx, 'wall-panel', f'{room_id}/{tv_id}-panel', room_id)
        k.rect((xm - half_w - 0.24, ya, z0 + 0.74, xm + half_w + 0.24, yb, z0 + 0.76),
               'cove_led_warm', f_idx, 'cove', f'{room_id}/{tv_id}-halo', room_id)
    if with_console:
        ca, cb = sorted((y_face, y_face + s * 0.36))
        k.rect((xm - half_w - 0.25, ca, z0 + 0.28, xm + half_w + 0.25, cb, z0 + 0.54),
               'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/{tv_id}-console', room_id)
        k.rect((xm - half_w - 0.25, ca, z0 + 0.54, xm + half_w + 0.25, cb, z0 + 0.565),
               'quartz_nano_white', f_idx, 'furniture', f'{room_id}/{tv_id}-console-top', room_id)
    ba, bb = sorted((y_face + s * 0.030, y_face + s * 0.062))
    sa, sb = sorted((y_face + s * 0.062, y_face + s * 0.070))
    k.rect((xm - half_w - 0.015, ba, z_tv0 - 0.015, xm + half_w + 0.015, bb, z_tv1 + 0.015),
           'gola_matte_black', f_idx, 'detail', f'{room_id}/{tv_id}-bezel', room_id)
    k.rect((xm - half_w, sa, z_tv0, xm + half_w, sb, z_tv1),
           'tv_oled_screen', f_idx, 'furniture', f'{room_id}/{tv_id}', room_id)
    return box(xm - half_w, min(ba, sb), xm + half_w, max(ba, sb))


def _add_curtains_and_pelmet(k: SceneKit, x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float, f_idx: int, H: float, owner: str) -> None:
    """Add floor-to-ceiling sheer ivory + taupe drape curtains offset cleanly inside the room."""
    bx0, by0, bx1, by1 = box_m(x0_ft, y0_ft, x1_ft, y1_ft)
    z0 = f_idx * H
    k.rect((bx0 - 0.03, by0 - 0.03, z0 + 2.72, bx1 + 0.03, by1 + 0.03, z0 + 2.95), 'cladding_fluted_teak', f_idx, 'curtain', f'{owner}/pelmet', owner)
    k.rect((bx0 - 0.015, by0 - 0.015, z0 + 2.70, bx1 + 0.015, by1 + 0.015, z0 + 2.72), 'cove_led_warm', f_idx, 'cove', f'{owner}/pelmet-led', owner)
    k.rect((bx0 + 0.02, by0 + 0.02, z0 + 0.02, bx1 - 0.02, by1 - 0.02, z0 + 2.72), 'curtain_sheer_ivory', f_idx, 'curtain', f'{owner}/sheer', owner)
    horiz = (bx1 - bx0) < (by1 - by0)
    if horiz:
        w_drape = min(0.42, (by1 - by0) * 0.20)
        k.rect((bx0, by0, z0 + 0.02, bx1, by0 + w_drape, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-L', owner)
        k.rect((bx0, by1 - w_drape, z0 + 0.02, bx1, by1, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-R', owner)
    else:
        w_drape = min(0.42, (bx1 - bx0) * 0.20)
        k.rect((bx0, by0, z0 + 0.02, bx0 + w_drape, by1, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-L', owner)
        k.rect((bx1 - w_drape, by0, z0 + 0.02, bx1, by1, z0 + 2.72), 'curtain_taupe_drape', f_idx, 'curtain', f'{owner}/drape-R', owner)


def _add_bed_assembly(k: SceneKit, x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float, head_dir: str, f_idx: int, H: float, room_id: str, single: bool = False) -> None:
    """Build a luxury upholstered bed with fluted headboard, pillows, duvet, and warm under-bed cove lighting."""
    bx0, by0, bx1, by1 = box_m(x0_ft, y0_ft, x1_ft, y1_ft)
    z0 = f_idx * H
    k.rect((bx0, by0, z0 + 0.04, bx1, by1, z0 + 0.30), 'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/bed-base', room_id)
    k.rect((bx0 + 0.04, by0 + 0.04, z0 + 0.30, bx1 - 0.04, by1 - 0.04, z0 + 0.54), 'curtain_sheer_ivory', f_idx, 'furniture', f'{room_id}/mattress', room_id)
    k.rect((bx0 + 0.03, by0 + 0.03, z0 + 0.015, bx1 - 0.03, by1 - 0.03, z0 + 0.035), 'cove_led_warm', f_idx, 'cove', f'{room_id}/bed-under-led', room_id)
    if head_dir == 'north':
        k.rect((bx1 - 0.14, by0 - 0.05, z0 + 0.04, bx1, by1 + 0.05, z0 + 1.25), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.03, by0 + 0.03, z0 + 0.54, bx1 - 0.52, by1 - 0.03, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx1 - 0.46, by0 + 0.12, z0 + 0.54, bx1 - 0.16, by1 - 0.12, z0 + 0.68), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    elif head_dir == 'south':
        k.rect((bx0, by0 - 0.05, z0 + 0.04, bx0 + 0.14, by1 + 0.05, z0 + 1.25), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.52, by0 + 0.03, z0 + 0.54, bx1 - 0.03, by1 - 0.03, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx0 + 0.16, by0 + 0.12, z0 + 0.54, bx0 + 0.46, by1 - 0.12, z0 + 0.68), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    elif head_dir == 'west':
        k.rect((bx0 - 0.05, by1 - 0.14, z0 + 0.04, bx1 + 0.05, by1, z0 + 1.25), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.03, by0 + 0.03, z0 + 0.54, bx1 - 0.03, by1 - 0.52, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx0 + 0.12, by1 - 0.46, z0 + 0.54, bx1 - 0.12, by1 - 0.16, z0 + 0.68), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    elif head_dir == 'east':
        k.rect((bx0 - 0.04, by0, z0 + 0.04, bx1 + 0.04, by0 + 0.14, z0 + 1.18), 'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/headboard', room_id)
        k.rect((bx0 + 0.03, by0 + 0.52, z0 + 0.54, bx1 - 0.03, by1 - 0.03, z0 + 0.60), 'sofa_taupe_boucle', f_idx, 'furniture', f'{room_id}/duvet', room_id)
        k.rect((bx0 + 0.12, by0 + 0.16, z0 + 0.54, bx1 - 0.12, by0 + 0.46, z0 + 0.70), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/pillows', room_id)
    k.furnishing('bed' if not single else 'single-bed', {'id': room_id, 'floor': f_idx}, box(bx0, by0, bx1, by1))


def _add_bath_fittings(k: SceneKit, basin_ft, wc_ft, shower_ft, f_idx: int, H: float, room_id: str) -> None:
    """Place floating vanity basin, wall-hung WC, and frameless glass shower enclosure."""
    z0 = f_idx * H
    vx0, vy0, vx1, vy1 = box_m(*basin_ft)
    k.rect((vx0, vy0, z0 + 0.25, vx1, vy1, z0 + 0.82), 'cladding_fluted_teak', f_idx, 'furniture', f'{room_id}/vanity-cabinet', room_id)
    k.rect((vx0 - 0.01, vy0 - 0.01, z0 + 0.82, vx1 + 0.01, vy1 + 0.01, z0 + 0.86), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/vanity-top', room_id)
    k.cylinder((0.5 * (vx0 + vx1), 0.5 * (vy0 + vy1), z0 + 0.86), 0.18, 0.11, 'quartz_nano_white', f_idx, 'detail')
    wx0, wy0, wx1, wy1 = box_m(*wc_ft)
    k.rect((wx0, wy0, z0 + 0.08, wx1, wy1, z0 + 0.43), 'quartz_nano_white', f_idx, 'furniture', f'{room_id}/wc-bowl', room_id)
    sx0, sy0, sx1, sy1 = box_m(*shower_ft)
    k.rect((sx0, sy0, z0 + 0.01, sx1, sy0 + 0.015, z0 + 2.10), 'glass', f_idx, 'glass', f'{room_id}/shower-glass', room_id)
    k.cylinder((0.5 * (sx0 + sx1), 0.5 * (sy0 + sy1), z0 + 2.15), 0.14, 0.015, 'gola_matte_black', f_idx, 'detail')
    k.furnishing('bath-fittings', {'id': room_id, 'floor': f_idx}, box(vx0, vy0, vx1, vy1))


def _furnish_ground_floor(k: SceneKit, b: dict, H: float) -> None:
    """Place all Ground Floor furniture, wide east-platform kitchen, full-span atrium dining, clean TVs, and verandah lawn court."""
    # 1. Glossy 800x800 ivory floor with dark charcoal perimeter inlay border in Living, Dining & Kitchen
    for zone_name, bounds_ft in [
        ('living-border', (6.5, 16.6, 23.4, 25.4)),
        ('foyer-border', (18.2, 9.6, 23.4, 16.0)),
        ('dining-border', (21.6, 25.6, 34.4, 32.5)),
        ('kitchen-border', (35.4, 25.6, 43.8, 34.4)),
    ]:
        bx0, by0, bx1, by1 = box_m(*bounds_ft)
        outer = box(bx0, by0, bx1, by1)
        inlay = outer.difference(outer.buffer(-0.075, join_style=2))
        k.poly_mesh(inlay, 0.001, 0.004, 'border_inlay_charcoal', 0, 'finish', f'g-{zone_name}', 'living_hall')

    # 2. Redesigned East-Wall Wide Platform Kitchen (x_ft: 44.05..46.80, y_ft: 22.20..34.80):
    # - 2'9" (840 mm) wide nano-white quartz platform along east wall (x=47', 3' setback from plot boundary!)
    # - Full storage beneath platform ONLY + minimalist floating teak shelves on center pier (clear of both east windows!)
    # - Fridge, oven/microwave, and tall pantry shifted WEST against Home ICU south wall (y=25', x=35.05..38.95)
    kitchen_room = next(s for s in b['spaces'] if s['id'] == 'kitchen')
    kx0 = (40.0 - 35.0) * 0.3048 + 0.062  # 1.586 m (flush with south wall inner face)
    kx1 = (40.0 - 22.0) * 0.3048 - 0.062  # 5.424 m (flush with north wall inner face)
    sx0, _, sx1, _ = box_m(44.5, 23.50, 46.6, 25.70)   # Centered under kitchen_east_window_1 (y=23..27)
    pier_x0, _, pier_x1, _ = box_m(46.0, 27.05, 46.8, 30.75)  # Solid pier between east windows (y=27..30.8)
    hx0, _, hx1, _ = box_m(44.5, 28.60, 46.6, 30.65)   # Hob on south half of solid center pier
    app_x0, app_y0, app_x1, app_y1 = box_m(35.05, 25.20, 38.95, 27.33)  # Shifted west against y=25' wall!
    px0, py0, px1, py1 = box_m(35.40, 30.00, 39.20, 31.65)
    y_east_wall_inner = (50.0 - 47.0) * 0.3048 + 0.060  # 0.9744 m

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
        'y_wall': y_east_wall_inner,
        'depth': 0.840,
        'sink_x0': sx0,
        'sink_x1': sx1,
        'pier_x0': pier_x0,
        'pier_x1': pier_x1,
        'hob_x0': hx0,
        'hob_x1': hx1,
        'app_x0': app_x0,
        'app_x1': app_x1,
        'fridge_y0': app_y0,
        'fridge_y1': app_y0 + 0.74,
        'pantry_y0': app_y0 + 0.75,
        'pantry_y1': app_y1,
        'prep_x0': px0,
        'prep_x1': px1,
        'prep_y0': py0,
        'prep_y1': py1,
    })

    # 3. Dining Hall under the Full-Span 10' x 8' Atrium (x_ft: 21..35, y_ft: 25..33):
    # Banquette on Home ICU south wall (y=25.2..26.6), 6-seater marble table centered under atrium chandelier (x=23.4..29.2, y=27.2..30.0)
    banq_x0, banq_y0, banq_x1, banq_y1 = box_m(24.3, 25.25, 29.5, 26.65)
    k.rect((banq_x0, banq_y0, 0.0, banq_x1, banq_y1, 0.46), 'cladding_fluted_teak', 0, 'furniture', 'dining/banquette-base', 'dining_hall')
    k.rect((banq_x0 + 0.02, banq_y0 + 0.02, 0.46, banq_x1 - 0.02, banq_y1 - 0.02, 0.54), 'sofa_taupe_boucle', 0, 'furniture', 'dining/banquette-cushion', 'dining_hall')
    k.rect((banq_x1 - 0.12, banq_y0 + 0.02, 0.54, banq_x1, banq_y1 - 0.02, 0.92), 'sofa_taupe_boucle', 0, 'furniture', 'dining/banquette-back', 'dining_hall')
    dtx0, dty0, dtx1, dty1 = box_m(23.6, 27.30, 29.2, 29.90)
    k.rect((dtx0, dty0, 0.72, dtx1, dty1, 0.76), 'dining_marble_top', 0, 'furniture', 'dining/table-top', 'dining_hall')
    k.rect((dtx0 + 0.18, dty0 + 0.35, 0.0, dtx1 - 0.18, dty0 + 0.50, 0.72), 'gola_matte_black', 0, 'furniture', 'dining/table-leg-E', 'dining_hall')
    k.rect((dtx0 + 0.18, dty1 - 0.50, 0.0, dtx1 - 0.18, dty1 - 0.35, 0.72), 'gola_matte_black', 0, 'furniture', 'dining/table-leg-W', 'dining_hall')
    for idx, cx_ft in enumerate((24.6, 26.4, 28.2)):
        cx0, cy0, cx1, cy1 = box_m(cx_ft - 0.72, 30.15, cx_ft + 0.72, 31.55)
        k.rect((cx0, cy0, 0.42, cx1, cy1, 0.48), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-s-{idx}', 'dining_hall')
        k.rect((cx0, cy0, 0.48, cx0 + 0.09, cy1, 0.86), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-s-back-{idx}', 'dining_hall')
    for side, (cx0_ft, cx1_ft) in (('west', (22.0, 23.35)), ('east', (29.45, 30.8))):
        cx0, cy0, cx1, cy1 = box_m(cx0_ft, 27.8, cx1_ft, 29.4)
        k.rect((cx0, cy0, 0.42, cx1, cy1, 0.48), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-{side}', 'dining_hall')
        back_y0 = cy1 - 0.09 if side == 'west' else cy0
        back_y1 = cy1 if side == 'west' else cy0 + 0.09
        k.rect((cx0, back_y0, 0.48, cx1, back_y1, 0.86), 'sofa_taupe_boucle', 0, 'furniture', f'dining/chair-{side}-back', 'dining_hall')
    k.furnishing('dining-set', {'id': 'dining_hall', 'floor': 0}, box(dtx0, dty0, banq_x1, dty1))

    # 4. Living Hall (x_ft: 5.5..24, y_ft: 16..26): Terracotta velvet sofa + marble coffee table + complete 75" TV on south wall (y=26')
    lsx0, lsy0, lsx1, lsy1 = box_m(9.2, 16.50, 16.4, 19.35)
    k.rect((lsx0, lsy0, 0.04, lsx1, lsy1, 0.43), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-seat', 'living_hall')
    k.rect((lsx1 - 0.22, lsy0, 0.43, lsx1, lsy1, 0.84), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-back', 'living_hall')
    k.rect((lsx0, lsy0, 0.43, lsx1, lsy0 + 0.20, 0.66), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-arm-E', 'living_hall')
    k.rect((lsx0, lsy1 - 0.20, 0.43, lsx1, lsy1, 0.66), 'sofa_terracotta_velvet', 0, 'furniture', 'living/sofa-arm-W', 'living_hall')
    rx0, ry0, rx1, ry1 = box_m(8.6, 17.5, 17.0, 24.4)
    k.rect((rx0, ry0, 0.005, rx1, ry1, 0.016), 'curtain_sheer_ivory', 0, 'rug', 'living/area-rug', 'living_hall')
    ctx0, cty0, ctx1, cty1 = box_m(10.5, 20.30, 15.1, 22.50)
    k.rect((ctx0, cty0, 0.36, ctx1, cty1, 0.42), 'dining_marble_top', 0, 'furniture', 'living/coffee-table-top', 'living_hall')
    k.rect((ctx0 + 0.12, cty0 + 0.12, 0.02, ctx1 - 0.12, cty1 - 0.12, 0.36), 'gola_matte_black', 0, 'furniture', 'living/coffee-table-base', 'living_hall')

    tv_poly = _add_tv_wall_assembly(k, 'south', 26.0, 10.0, 15.6, 0, H, 'living_hall', 'tv-75in', width_m=1.66, height_m=0.95)
    lcx0, lcy0, lcx1, lcy1 = box_m(6.2, 16.5, 20.5, 25.5)
    k.rect((lcx0, lcy0, H - 0.18, lcx1, lcy1, H - 0.15), 'wall', 0, 'ceiling', 'living/false-ceiling', 'living_hall')
    k.beam((lcx0 + 0.3, lcy0 + 0.4, H - 0.185), (lcx1 - 0.3, lcy1 - 0.4, H - 0.185), 0.032, 'cove_led_warm', 0, 'cove')
    k.beam((lcx0 + 0.3, lcy1 - 0.4, H - 0.185), (lcx1 - 0.3, lcy0 + 0.4, H - 0.185), 0.032, 'cove_led_warm', 0, 'cove')
    k.furnishing('sofa', {'id': 'living_hall', 'floor': 0}, box(lsx0, lsy0, lsx1, lsy1))
    k.furnishing('tv-75in', {'id': 'living_hall', 'floor': 0}, tv_poly)

    # 5. Home ICU (15' x 16', x_ft: 24..39, y_ft: 9..25):
    # Bed centered at y=13.2..17.2 (facing solid west wall y=9..19, keeping the 5'6" clear opening y=19..24.5 100% clear!)
    _add_bed_assembly(k, 31.20, 13.20, 38.45, 17.20, 'east', 0, H, 'home_icu')
    icu_tv_poly = _add_tv_wall_assembly(k, 'west', 24.0, 13.4, 17.0, 0, H, 'home_icu', 'tv-55in', width_m=1.24, height_m=0.72, with_console=False, with_panel=True)
    k.furnishing('icu-tv-55in', {'id': 'home_icu', 'floor': 0}, icu_tv_poly)

    eqx0, eqy0, eqx1, eqy1 = box_m(36.50, 10.80, 38.45, 12.60)
    k.rect((eqx0, eqy0, 0.04, eqx1, eqy1, 0.78), 'quartz_nano_white', 0, 'furniture', 'home_icu/equipment-cart', 'home_icu')
    k.rect((eqx0 + 0.10, eqy0 + 0.12, 0.78, eqx1 - 0.10, eqy1 - 0.12, 1.18), 'blackglass', 0, 'detail', 'home_icu/patient-monitor', 'home_icu')
    k.furnishing('icu-equipment', {'id': 'home_icu', 'floor': 0}, box(eqx0, eqy0, eqx1, eqy1))

    rcx0, rcy0, rcx1, rcy1 = box_m(26.4, 10.6, 29.2, 13.2)
    k.rect((rcx0, rcy0, 0.04, rcx1, rcy1, 0.45), 'sofa_taupe_boucle', 0, 'furniture', 'home_icu/companion-recliner', 'home_icu')
    k.rect((rcx1 - 0.18, rcy0, 0.45, rcx1, rcy1, 0.92), 'sofa_taupe_boucle', 0, 'furniture', 'home_icu/companion-recliner-back', 'home_icu')
    k.furnishing('icu-companion-chair', {'id': 'home_icu', 'floor': 0}, box(rcx0, rcy0, rcx1, rcy1))
    _add_curtains_and_pelmet(k, 24.8, 9.35, 38.2, 9.75, 0, H, 'home_icu/north-curtain')

    # 6. Caregiver Room (8' x 10') & Caregiver Bath (5' x 6')
    _add_bed_assembly(k, 0.45, 4.50, 6.90, 7.90, 'west', 0, H, 'caregiver', single=True)
    _add_bath_fittings(k, (0.4, 14.0, 2.0, 15.7), (0.4, 16.0, 2.4, 17.4), (0.4, 12.3, 3.0, 13.9), 0, H, 'caregiver_bath')

    # 7. Drawing Room (9'6" x 14', x_ft: 8..17.5, y_ft: 2..16)
    dsx0, dsy0, dsx1, dsy1 = box_m(9.75, 2.45, 15.75, 5.30)
    k.rect((dsx0, dsy0, 0.04, dsx1, dsy1, 0.43), 'sofa_taupe_boucle', 0, 'furniture', 'drawing_room/sofa-seat', 'drawing_room')
    k.rect((dsx1 - 0.20, dsy0, 0.43, dsx1, dsy1, 0.84), 'sofa_taupe_boucle', 0, 'furniture', 'drawing_room/sofa-back', 'drawing_room')
    dct0, dcty0, dct1, dcty1 = box_m(10.8, 6.3, 14.7, 8.3)
    k.rect((dct0, dcty0, 0.36, dct1, dcty1, 0.42), 'dining_marble_top', 0, 'furniture', 'drawing_room/coffee-table', 'drawing_room')
    _add_curtains_and_pelmet(k, 10.5, 2.35, 16.6, 2.75, 0, H, 'drawing_room/north-curtain')
    k.furnishing('drawing-sofa', {'id': 'drawing_room', 'floor': 0}, box(dsx0, dsy0, dsx1, dsy1))

    # 8. Ground Master Bedroom (15' x 14') & Master Bath (5'6" x 8')
    _add_bed_assembly(k, 6.75, 33.10, 12.75, 39.55, 'south', 0, H, 'master_bedroom')
    mwx0, mwy0, mwx1, mwy1 = box_m(5.6, 26.3, 15.2, 28.2)
    k.rect((mwx0, mwy0, 0.0, mwx1, mwy1, 2.40), 'cladding_fluted_teak', 0, 'furniture', 'master_bedroom/wardrobe', 'master_bedroom')
    k.furnishing('wardrobe', {'id': 'master_bedroom', 'floor': 0}, box(mwx0, mwy0, mwx1, mwy1))
    _add_bath_fittings(k, (0.4, 20.3, 2.0, 22.0), (0.4, 22.3, 2.4, 23.7), (0.4, 18.3, 3.2, 20.1), 0, H, 'master_bath')

    # 9. Store (7' x 5', x_ft: 33..40, y_ft: 35..40) & Wash Area (7' x 5', x_ft: 40..47, y_ft: 35..40)
    # Storage shifted west away from east wall!
    stx0, sty0, stx1, sty1 = box_m(33.3, 35.3, 35.0, 39.7)
    for sz in (0.45, 0.95, 1.45, 1.95):
        k.rect((stx0, sty0, sz, stx1, sty1, sz + 0.04), 'cladding_fluted_teak', 0, 'furniture', f'store/shelf-{sz}', 'store')
    k.furnishing('store-shelves', {'id': 'store', 'floor': 0}, box(stx0, sty0, stx1, sty1))

    wmx0, wmy0, wmx1, wmy1 = box_m(44.4, 35.4, 46.6, 37.4)
    k.rect((wmx0, wmy0, 0.0, wmx1, wmy1, 0.85), 'quartz_nano_white', 0, 'furniture', 'wash_area/washer', 'wash_area')
    k.cylinder((wmx0 + 0.32, wmy1 + 0.01, 0.45), 0.22, 0.02, 'blackglass', 0, 'detail')
    usx0, usy0, usx1, usy1 = box_m(44.6, 37.5, 46.6, 39.5)
    k.rect((usx0, usy0, 0.0, usx1, usy1, 0.85), 'kitchen_sage_teal_gloss', 0, 'furniture', 'wash_area/utility-sink', 'wash_area')
    k.furnishing('washer', {'id': 'wash_area', 'floor': 0}, box(wmx0, wmy0, wmx1, wmy1))
    k.furnishing('utility-sink', {'id': 'wash_area', 'floor': 0}, box(usx0, usy0, usx1, usy1))

    # 10. Verandah (16' x 9', x_ft: 23..39, y_ft: 0..9) + Manicured North-Wall Lawn Court (x_ft: 24.2..37.8, y_ft: 0.45..3.05)
    vx0, vy0, vx1, vy1 = box_m(23.0, 3.10, 39.0, 9.0)
    k.rect((vx0, vy0, 0.002, vx1, vy1, 0.028), 'terrace_wood_deck', 0, 'floor', 'verandah/wood-deck', 'verandah')
    # North strip paving flanking the lawn court
    for side_n, (sx_a, sx_b) in (('west-pad', (23.0, 24.2)), ('east-pad', (37.8, 39.0))):
        pxa, pya, pxb, pyb = box_m(sx_a, 0.35, sx_b, 3.10)
        k.rect((pxa, pya, 0.002, pxb, pyb, 0.028), 'travertine_warm', 0, 'floor', f'verandah/{side_n}', 'verandah')

    # Recessed manicured architectural velvet lawn court along the north wall (NO round shrubs, NO spiky grass clumps!)
    lx0, ly0, lx1, ly1 = box_m(24.2, 0.45, 37.8, 3.05)
    lawn_outer = box(lx0, ly0, lx1, ly1)
    lawn_inner = lawn_outer.buffer(-0.14, join_style=2)
    lawn_coping = lawn_outer.difference(lawn_inner)
    k.poly_mesh(lawn_coping, 0.002, 0.088, 'travertine_warm', 0, 'finish', 'verandah/north-lawn-coping', 'verandah')
    k.poly_mesh(lawn_inner, 0.002, 0.048, 'verandah_lawn_velvet', 0, 'finish', 'verandah/north-lawn-turf', 'verandah')
    # Subtle warm 3000K linear LED graze strip tucked under the south coping lip facing the lawn
    k.rect((lx0 + 0.14, ly0 + 0.16, 0.052, lx0 + 0.165, ly1 - 0.16, 0.070), 'cove_led_warm', 0, 'cove', 'verandah/north-lawn-led', 'verandah')
    # Four floating honed-travertine stepping pads across the manicured lawn court
    for pad_i, pad_x_ft in enumerate((26.2, 29.4, 32.6, 35.8)):
        sx0_p, sy0_p, sx1_p, sy1_p = box_m(pad_x_ft - 0.85, 1.15, pad_x_ft + 0.85, 2.35)
        k.rect((sx0_p, sy0_p, 0.048, sx1_p, sy1_p, 0.072), 'travertine_warm', 0, 'finish', f'verandah/lawn-stepping-pad-{pad_i}', 'verandah')

    # Minimalist outdoor teak & taupe-boucle lounge bench on the verandah timber deck
    vbx0, vby0, vbx1, vby1 = box_m(24.4, 4.2, 26.2, 7.8)
    k.rect((vbx0, vby0, 0.04, vbx1, vby1, 0.38), 'cladding_fluted_teak', 0, 'furniture', 'verandah/lounge-bench', 'verandah')
    k.rect((vbx0 + 0.03, vby0 + 0.03, 0.38, vbx1 - 0.03, vby1 - 0.03, 0.46), 'sofa_taupe_boucle', 0, 'furniture', 'verandah/lounge-cushion', 'verandah')


def _furnish_first_floor(k: SceneKit, b: dict, H: float) -> None:
    """Place all First Floor furniture cleanly with zero plant spheres."""
    z1 = H
    # 1. Master Bedroom (18' x 15', x_ft: 0..18, y_ft: 2..17)
    _add_bed_assembly(k, 8.60, 2.45, 14.60, 8.95, 'north', 1, H, 'u_master_bedroom')
    mbx0, mby0, mbx1, mby1 = box_m(9.30, 9.10, 13.90, 10.40)
    k.rect((mbx0, mby0, z1 + 0.04, mbx1, mby1, z1 + 0.45), 'sofa_taupe_boucle', 1, 'furniture', 'u_master_bedroom/foot-bench', 'u_master_bedroom')
    k.furnishing('master-bench', {'id': 'u_master_bedroom', 'floor': 1}, box(mbx0, mby0, mbx1, mby1))
    stx0, sty0, stx1, sty1 = box_m(15.35, 2.45, 17.15, 4.25)
    k.rect((stx0, sty0, z1 + 0.04, stx1, sty1, z1 + 0.55), 'cladding_fluted_teak', 1, 'furniture', 'u_master_bedroom/side-table', 'u_master_bedroom')
    _add_curtains_and_pelmet(k, 3.2, 2.35, 10.2, 2.75, 1, H, 'u_master_bedroom/north-curtain')

    # 2. Dressing Room (8' x 7', x_ft: 7..15, y_ft: 17..24)
    dwx0, dwy0, dwx1, dwy1 = box_m(12.9, 17.35, 14.75, 23.65)
    k.rect((dwx0, dwy0, z1, dwx1, dwy1, z1 + 2.40), 'cladding_fluted_teak', 1, 'furniture', 'u_dressing/wardrobe-east', 'u_dressing')
    dwx2, dwy2, dwx3, dwy3 = box_m(7.35, 22.0, 12.85, 23.65)
    k.rect((dwx2, dwy2, z1, dwx3, dwy3, z1 + 2.40), 'kitchen_sage_teal_gloss', 1, 'furniture', 'u_dressing/wardrobe-south', 'u_dressing')
    k.furnishing('dressing-wardrobes', {'id': 'u_dressing', 'floor': 1}, box(dwx0, dwy0, dwx1, dwy1))

    # 3. En-suite Bath (7' x 9') & Shared Bath (5' x 8', x_ft: 34..39, y_ft: 25..33)
    _add_bath_fittings(k, (0.35, 20.5, 2.1, 22.5), (0.35, 23.8, 2.5, 25.5), (0.35, 17.35, 3.4, 20.1), 1, H, 'u_en_suite')
    _add_bath_fittings(k, (37.0, 27.2, 38.65, 29.0), (36.8, 30.4, 38.65, 31.8), (34.35, 30.2, 36.6, 32.65), 1, H, 'u_shared_bath')

    # 4. Study / Meditation Room (15' x 13', x_ft: 24..39, y_ft: 8..21)
    sdx0, sdy0, sdx1, sdy1 = box_m(24.45, 8.40, 29.45, 10.40)
    k.rect((sdx0, sdy0, z1 + 0.72, sdx1, sdy1, z1 + 0.76), 'cladding_fluted_teak', 1, 'furniture', 'u_study_meditation/desk-top', 'u_study_meditation')
    k.rect((sdx0 + 0.08, sdy0 + 0.08, z1, sdx1 - 0.08, sdy0 + 0.16, z1 + 0.72), 'gola_matte_black', 1, 'furniture', 'u_study_meditation/desk-leg', 'u_study_meditation')
    scx0, scy0, scx1, scy1 = box_m(26.1, 10.65, 27.7, 12.25)
    k.rect((scx0, scy0, z1 + 0.44, scx1, scy1, z1 + 0.50), 'sofa_taupe_boucle', 1, 'furniture', 'u_study_meditation/desk-chair', 'u_study_meditation')
    k.furnishing('study-desk', {'id': 'u_study_meditation', 'floor': 1}, box(sdx0, sdy0, sdx1, sdy1))

    mpx0, mpy0, mpx1, mpy1 = box_m(33.8, 8.40, 38.55, 12.80)
    k.rect((mpx0, mpy0, z1 + 0.02, mpx1, mpy1, z1 + 0.22), 'cladding_fluted_teak', 1, 'furniture', 'u_study_meditation/meditation-platform', 'u_study_meditation')
    k.rect((mpx0 + 0.04, mpy0 + 0.04, z1, mpx1 - 0.04, mpy1 - 0.04, z1 + 0.025), 'cove_led_warm', 1, 'cove', 'u_study_meditation/meditation-led', 'u_study_meditation')
    k.cylinder((0.5 * (mpx0 + mpx1), 0.5 * (mpy0 + mpy1), z1 + 0.22), 0.38, 0.09, 'sofa_taupe_boucle', 1, 'furniture')
    k.furnishing('meditation-platform', {'id': 'u_study_meditation', 'floor': 1}, box(mpx0, mpy0, mpx1, mpy1))

    # 5. Medium Bedroom (15' x 11', x_ft: 2..17, y_ft: 29..40)
    _add_bed_assembly(k, 2.45, 31.30, 8.95, 36.80, 'west', 1, H, 'u_medium_bedroom')
    uwx0, uwy0, uwx1, uwy1 = box_m(10.2, 37.8, 16.65, 39.65)
    k.rect((uwx0, uwy0, z1, uwx1, uwy1, z1 + 2.40), 'cladding_fluted_teak', 1, 'furniture', 'u_medium_bedroom/wardrobe', 'u_medium_bedroom')
    k.furnishing('medium-wardrobe', {'id': 'u_medium_bedroom', 'floor': 1}, box(uwx0, uwy0, uwx1, uwy1))

    # 6. First-Floor Terrace Outdoor Lounge Chairs & Travertine Coffee Table (NO shrub balls!)
    for idx, (cx0_ft, cy0_ft, cx1_ft, cy1_ft) in enumerate([
        (41.4, 12.6, 43.8, 15.0),
        (41.4, 17.0, 43.8, 19.4),
    ]):
        tx0, ty0, tx1, ty1 = box_m(cx0_ft, cy0_ft, cx1_ft, cy1_ft)
        k.rect((tx0, ty0, z1 + 0.05, tx1, ty1, z1 + 0.38), 'cladding_fluted_teak', 1, 'furniture', f'u_large_terrace/chair-base-{idx}', 'u_large_terrace')
        k.rect((tx0 + 0.03, ty0 + 0.03, z1 + 0.38, tx1 - 0.03, ty1 - 0.03, z1 + 0.46), 'sofa_taupe_boucle', 1, 'furniture', f'u_large_terrace/chair-{idx}', 'u_large_terrace')
        k.rect((tx0 + 0.03, ty0, z1 + 0.46, tx1 - 0.03, ty0 + 0.14, z1 + 0.80), 'sofa_taupe_boucle', 1, 'furniture', f'u_large_terrace/chair-back-{idx}', 'u_large_terrace')
    tbx0, tby0, tbx1, tby1 = box_m(41.7, 15.3, 43.3, 16.7)
    k.rect((tbx0, tby0, z1 + 0.05, tbx1, tby1, z1 + 0.44), 'travertine_warm', 1, 'furniture', 'u_large_terrace/side-table', 'u_large_terrace')
    k.furnishing('terrace-seating', {'id': 'u_large_terrace', 'floor': 1}, box(tbx0, tby0, tbx1, tby1))


def _furnish_second_floor(k: SceneKit, b: dict, H: float) -> None:
    """Place all Second Floor furniture: 3 computer desks & chairs, lounge sofa facing east to complete 75\" TV on x=34', and north terrace lounge."""
    z2 = 2 * H
    # 1. Three executive workstations along north wall (x_ft: 4.2..20.2, y_ft: 8.45..12.4)
    for idx, (dx0_ft, dx1_ft) in enumerate([(4.2, 9.0), (9.7, 14.5), (15.2, 20.0)]):
        bx0, by0, bx1, by1 = box_m(dx0_ft, 8.45, dx1_ft, 10.65)
        k.rect((bx0, by0, z2 + 0.72, bx1, by1, z2 + 0.76), 'cladding_fluted_teak', 2, 'furniture', f's_office_tv_hall/desk-{idx+1}', 's_office_tv_hall')
        k.rect((bx0 + 0.06, by0 + 0.06, z2, bx1 - 0.06, by0 + 0.14, z2 + 0.72), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/desk-leg-E-{idx+1}', 's_office_tv_hall')
        k.rect((bx0 + 0.06, by1 - 0.14, z2, bx1 - 0.06, by1 - 0.06, z2 + 0.72), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/desk-leg-W-{idx+1}', 's_office_tv_hall')
        k.rect((bx1 - 0.24, 0.5 * (by0 + by1) - 0.34, z2 + 0.76, bx1 - 0.18, 0.5 * (by0 + by1) + 0.34, z2 + 1.15), 'blackglass', 2, 'detail', f's_office_tv_hall/monitor-{idx+1}', 's_office_tv_hall')
        cx0, cy0, cx1, cy1 = box_m(0.5 * (dx0_ft + dx1_ft) - 0.85, 10.9, 0.5 * (dx0_ft + dx1_ft) + 0.85, 12.5)
        k.rect((cx0, cy0, z2 + 0.44, cx1, cy1, z2 + 0.50), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/chair-{idx+1}', 's_office_tv_hall')
        k.rect((cx0, cy0, z2 + 0.50, cx0 + 0.10, cy1, z2 + 0.94), 'gola_matte_black', 2, 'furniture', f's_office_tv_hall/chair-back-{idx+1}', 's_office_tv_hall')
        k.furnishing(f'office-desk-{idx+1}', {'id': 's_office_tv_hall', 'floor': 2}, box(bx0, by0, bx1, by1))

    # 2. Lounge L-sofa facing EAST toward complete 75" OLED TV mounted cleanly on the east wall (x_ft=34.0, y_ft: 16.2..22.2)
    ssx0, ssy0, ssx1, ssy1 = box_m(21.2, 15.8, 24.1, 23.2)
    k.rect((ssx0, ssy0, z2 + 0.04, ssx1, ssy1, z2 + 0.43), 'sofa_terracotta_velvet', 2, 'furniture', 's_office_tv_hall/sofa-seat', 's_office_tv_hall')
    k.rect((ssx0, ssy1 - 0.22, z2 + 0.43, ssx1, ssy1, z2 + 0.84), 'sofa_terracotta_velvet', 2, 'furniture', 's_office_tv_hall/sofa-back', 's_office_tv_hall')
    k.rect((ssx0, ssy0, z2 + 0.43, ssx0 + 0.20, ssy1, z2 + 0.66), 'sofa_terracotta_velvet', 2, 'furniture', 's_office_tv_hall/sofa-arm-S', 's_office_tv_hall')
    k.rect((ssx1 - 0.20, ssy0, z2 + 0.43, ssx1, ssy1, z2 + 0.66), 'sofa_terracotta_velvet', 2, 'furniture', 's_office_tv_hall/sofa-arm-N', 's_office_tv_hall')

    srx0, sry0, srx1, sry1 = box_m(21.0, 15.4, 32.8, 23.6)
    k.rect((srx0, sry0, z2 + 0.004, srx1, sry1, z2 + 0.014), 'curtain_sheer_ivory', 2, 'rug', 's_office_tv_hall/lounge-rug', 's_office_tv_hall')

    sctx0, scty0, sctx1, scty1 = box_m(25.4, 17.6, 27.6, 21.4)
    k.rect((sctx0, scty0, z2 + 0.36, sctx1, scty1, z2 + 0.42), 'dining_marble_top', 2, 'furniture', 's_office_tv_hall/coffee-table', 's_office_tv_hall')
    k.rect((sctx0 + 0.12, scty0 + 0.12, z2 + 0.02, sctx1 - 0.12, scty1 - 0.12, z2 + 0.36), 'gola_matte_black', 2, 'furniture', 's_office_tv_hall/coffee-table-base', 's_office_tv_hall')

    stv_poly = _add_tv_wall_assembly(k, 'east', 34.0, 16.5, 22.0, 2, H, 's_office_tv_hall', 'tv-75in', width_m=1.66, height_m=0.95)
    k.furnishing('office-sofa', {'id': 's_office_tv_hall', 'floor': 2}, box(ssx0, ssy0, ssx1, ssy1))
    k.furnishing('office-tv-75in', {'id': 's_office_tv_hall', 'floor': 2}, stv_poly)

    # 3. Second-Floor North Terrace Outdoor Lounge Sofa & Travertine Table on timber deck (zero green shrub balls!)
    ntx0, nty0, ntx1, nty1 = box_m(25.0, 1.4, 32.5, 3.8)
    k.rect((ntx0, nty0, z2 + 0.05, ntx1, nty1, z2 + 0.38), 'cladding_fluted_teak', 2, 'furniture', 's_open_terrace/lounge-base', 's_open_terrace')
    k.rect((ntx0 + 0.04, nty0 + 0.04, z2 + 0.38, ntx1 - 0.04, nty1 - 0.04, z2 + 0.47), 'sofa_taupe_boucle', 2, 'furniture', 's_open_terrace/lounge-seat', 's_open_terrace')
    k.rect((ntx1 - 0.16, nty0 + 0.04, z2 + 0.47, ntx1, nty1 - 0.04, z2 + 0.80), 'sofa_taupe_boucle', 2, 'furniture', 's_open_terrace/lounge-back', 's_open_terrace')
    ntt0, ntty0, ntt1, ntty1 = box_m(26.8, 4.4, 30.7, 6.2)
    k.rect((ntt0, ntty0, z2 + 0.05, ntt1, ntty1, z2 + 0.40), 'travertine_warm', 2, 'furniture', 's_open_terrace/lounge-table', 's_open_terrace')


def _build_sloped_vehicle_ramp(k: SceneKit, x0_m: float, x1_m: float, y0_m: float, y1_m: float, z_low: float, z_high: float) -> None:
    """Build a true sloped honed-stone vehicle driveway ramp from the North Road (z_low=-0.30 m) up into the Car Porch (z_high=0.00 m)."""
    top = [
        (x0_m, y0_m, z_high),
        (x0_m, y1_m, z_high),
        (x1_m, y1_m, z_low),
        (x1_m, y0_m, z_low),
    ]
    bot = [(a, b, z - 0.10) for a, b, z in top]
    verts = top + bot
    faces = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6)]
    for i in range(4):
        j = (i + 1) % 4
        faces.extend([(i, 4 + i, 4 + j), (i, 4 + j, j)])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces)
    k.node(k.asset(mesh), 'travertine_warm', floor=0, role='floor', name='north-vehicle-ramp', owner='north-vehicle-gate')


def _add_site_context_and_gates(k: SceneKit, scene: dict, building: dict, H: float) -> None:
    """Build custom perimeter enclosure with BOTH the East Pedestrian Gate AND the NE Corner Car Gate,
    sloped stone vehicle ramp, 22' car porch with sleek SUV & timber soffit, and 3' east kitchen setback walk."""
    planning = building['planning']
    if planning.get('colonyMaterials'):
        scene['materials'].update(planning['colonyMaterials'])
    if planning.get('colony'):
        ped_lo, ped_hi = sorted((local_mm(50.0, 8.0)[0], local_mm(50.0, 3.5)[0]))
        scene['context'] = {
            **planning['colony'],
            'project_id': 'tirumala-7',
            'detailLevel': 'reference',
            'entryGaps': [[ped_lo / 1000.0, ped_hi / 1000.0]],
            'northVehicleGate': {'x_ft': [39.5, 49.5], 'y_ft': 0.0},
        }

    # Re-tint generic world terrain from neon-green grass to warm architectural stone/road tone
    for n in scene['nodes']:
        if n.get('role') == 'terrain':
            n['material'] = 't4-colony-road' if 't4-colony-road' in scene['materials'] else 'terrace_grey_paver'

    g = -PLINTH_M  # -0.300 m road datum
    W_m, D_m = 40.0 * 0.3048, 50.0 * 0.3048  # 12.192 m (+X north), 15.240 m (+Y west)

    # 1. Grounded 300 mm travertine plinth base under the house footprint (excluding sloped porch ramp mouth)
    ramp_mouth_mm = box_mm(39.2, 0.0, 49.8, 3.5)
    plinth_poly = geometry(building['floor_plates'][0]['outline']).difference(ramp_mouth_mm)
    k.poly_mesh(shp_scale(plinth_poly, xfact=0.001, yfact=0.001, origin=(0, 0)), g, 0.0, 'travertine_warm', -1, 'plinth', 't7-house-plinth', 'tirumala-7')

    # 2. Paved open-to-sky perimeter setback passages (3' East Kitchen Setback x=47..50, North Gully, West Gully)
    esx0, esy0, esx1, esy1 = box_m(47.0, 22.0, 50.0, 40.0)
    k.rect((esx0, esy0, 0.001, esx1, esy1, 0.022), 'terrace_grey_paver', 0, 'floor', 'east_setback/paving', 'east_setback')
    # Stepping stones along the 3' east kitchen setback passage
    for s_idx, sy_ft in enumerate((24.0, 27.0, 30.0, 33.0, 36.0, 38.8)):
        st0, sty0, st1, sty1 = box_m(47.6, sy_ft - 0.85, 49.4, sy_ft + 0.85)
        k.rect((st0, sty0, 0.022, st1, sty1, 0.040), 'travertine_warm', 0, 'finish', f'east_setback/step-pad-{s_idx}', 'east_setback')

    # 3. 22' Car Porch (x_ft: 39.0..50.0, y_ft: 0.0..22.0): paving, sloped stone ramp, sleek SUV, and smoked-oak ceiling slats
    px0, py0, px1, py1 = box_m(39.0, 3.5, 50.0, 22.0)
    k.rect((px0, py0, 0.001, px1, py1, 0.024), 'terrace_grey_paver', 0, 'floor', 'car_porch/paving', 'car_porch')
    # True 3D sloped travertine ramp from North Road (X=13.35 m, z=-0.30 m) up into the Car Porch (X=11.125 m, z=0.02 m)
    _, ry0, _, ry1 = box_m(39.5, 0.0, 49.5, 3.5)
    _build_sloped_vehicle_ramp(k, (40.0 - 3.5) * 0.3048, W_m + 1.15, ry0, ry1, g, 0.022)

    # Smoked-oak slatted ceiling soffit + recessed warm LED strips under covered portion of Car Porch (x_ft: 39.2..46.8, y_ft: 0.5..21.8)
    for j in range(18):
        sy_ft = 1.0 + j * 1.18
        sx0_s, sy0_s, sx1_s, sy1_s = box_m(39.3, sy_ft, 46.8, sy_ft + 0.42)
        k.rect((sx0_s, sy0_s, H - 0.21, sx1_s, sy1_s, H - 0.16), 'cladding_fluted_teak', 0, 'ceiling', f'car_porch/soffit-slat-{j}', 'car_porch')
    for lx_ft in (41.0, 45.0):
        lx0_s, ly0_s, lx1_s, ly1_s = box_m(lx_ft - 0.08, 2.0, lx_ft + 0.08, 20.5)
        k.rect((lx0_s, ly0_s, H - 0.22, lx1_s, ly1_s, H - 0.205), 'cove_led_warm', 0, 'cove', f'car_porch/soffit-led-{lx_ft}', 'car_porch')

    # Sleek Pearl-Metallic SUV parked inside the spacious 22' Car Porch (x_ft: 41.6..47.4, y_ft: 5.8..19.6)
    cx0, cy0, cx1, cy1 = box_m(41.6, 5.8, 47.4, 19.6)
    cm_x, cm_y = 0.5 * (cx0 + cx1), 0.5 * (cy0 + cy1)
    car_len, car_wid = cx1 - cx0, cy1 - cy0
    k.rb((cm_x, cm_y, 0.45), (car_len, car_wid, 0.56), 'car_pearl_metallic', 0, 'vehicle', 0.12, owner='parked-car')
    # Solid dark interior cabin core + pearl roof & pillars so greenhouse reads solid, never hollow
    k.rb((cm_x - 0.22, cm_y, 0.89), (car_len * 0.48, car_wid * 0.76, 0.40), 'gola_matte_black', 0, 'vehicle', 0.06, owner='parked-car')
    k.rb((cm_x - 0.22, cm_y, 0.93), (car_len * 0.56, car_wid * 0.84, 0.46), 'tv_oled_screen', 0, 'vehicle', 0.09, owner='parked-car')
    k.rb((cm_x - 0.22, cm_y, 1.19), (car_len * 0.52, car_wid * 0.81, 0.06), 'car_pearl_metallic', 0, 'vehicle', 0.03, owner='parked-car')
    for px_off in (-0.88, -0.18, 0.52):
        for py_side in (cy0 + 0.17, cy1 - 0.17):
            k.rect((cm_x + px_off - 0.045, py_side - 0.025, 0.72, cm_x + px_off + 0.045, py_side + 0.025, 1.18),
                   'car_pearl_metallic', 0, 'vehicle', f'parked-car/pillar-{px_off:.2f}-{py_side:.2f}', 'parked-car')
    # Front grille + headlights facing North Road (+X) & slim rear tail-light bar (-X)
    k.rect((cx1 - 0.02, cy0 + 0.46, 0.34, cx1 + 0.012, cy1 - 0.46, 0.56), 'gola_matte_black', 0, 'vehicle', 'parked-car/grille', 'parked-car')
    k.rect((cx1 - 0.03, cy0 + 0.14, 0.50, cx1 + 0.012, cy0 + 0.42, 0.58), 'cove_led_warm', 0, 'vehicle', 'parked-car/headlight-R', 'parked-car')
    k.rect((cx1 - 0.03, cy1 - 0.42, 0.50, cx1 + 0.012, cy1 - 0.14, 0.58), 'cove_led_warm', 0, 'vehicle', 'parked-car/headlight-L', 'parked-car')
    k.rect((cx0 - 0.012, cy0 + 0.18, 0.56, cx0 + 0.02, cy1 - 0.18, 0.61), 'sofa_terracotta_velvet', 0, 'vehicle', 'parked-car/taillight', 'parked-car')
    for wx in (cx0 + 0.76, cx1 - 0.76):
        for wy in (cy0 + 0.08, cy1 - 0.08):
            k.cylinder((wx, wy, 0.32), 0.32, 0.22, 'gola_matte_black', 0, 'vehicle', rot=(math.pi / 2, 0, 0))
            k.cylinder((wx, wy + (-0.115 if wy < cm_y else 0.115), 0.32), 0.19, 0.03, 'travertine_warm', 0, 'vehicle', rot=(math.pi / 2, 0, 0))

    # 4. Custom Architectural Compound Enclosure with BOTH East Pedestrian Gate & North-East Corner Car Gate
    def wall_run(ident: str, x0_ft: float, y0_ft: float, x1_ft: float, y1_ft: float, h_masonry: float, louvered_top: float | None = None):
        bx0, by0, bx1, by1 = box_m(x0_ft, y0_ft, x1_ft, y1_ft)
        k.rect((bx0, by0, g, bx1, by1, g + h_masonry - 0.04), 'wall', 0, 'wall', ident, ident)
        k.rect((bx0 - 0.015, by0 - 0.015, g + h_masonry - 0.04, bx1 + 0.015, by1 + 0.015, g + h_masonry),
               'travertine_warm', 0, 'coping', f'{ident}-coping', ident)
        if louvered_top and louvered_top > h_masonry + 0.12:
            along_x = (bx1 - bx0) >= (by1 - by0)
            span = (bx1 - bx0) if along_x else (by1 - by0)
            n_posts = max(2, int(round(span / 1.5)) + 1)
            for p_i in range(n_posts):
                t = p_i / (n_posts - 1)
                if along_x:
                    px = bx0 + 0.04 + t * (bx1 - bx0 - 0.08)
                    k.rect((px - 0.02, by0 + 0.03, g + h_masonry, px + 0.02, by1 - 0.03, g + louvered_top),
                           'gola_matte_black', 0, 'wall', f'{ident}-post-{p_i}', ident)
                else:
                    py = by0 + 0.04 + t * (by1 - by0 - 0.08)
                    k.rect((bx0 + 0.03, py - 0.02, g + h_masonry, bx1 - 0.03, py + 0.02, g + louvered_top),
                           'gola_matte_black', 0, 'wall', f'{ident}-post-{p_i}', ident)
            z_cur = g + h_masonry + 0.04
            s_i = 0
            while z_cur + 0.055 <= g + louvered_top - 0.02:
                if along_x:
                    k.rect((bx0 + 0.02, by0 + 0.045, z_cur, bx1 - 0.02, by1 - 0.045, z_cur + 0.052),
                           'cladding_fluted_teak', 0, 'wall', f'{ident}-slat-{s_i}', ident)
                else:
                    k.rect((bx0 + 0.045, by0 + 0.02, z_cur, bx1 - 0.045, by1 - 0.02, z_cur + 0.052),
                           'cladding_fluted_teak', 0, 'wall', f'{ident}-slat-{s_i}', ident)
                z_cur += 0.088
                s_i += 1

    # East boundary south of Pedestrian Gate (x_ft: 49.6..50.0, y_ft: 8.2..40.0): dwarf wall + smoked-oak louver screen
    wall_run('t7-boundary-east-south', 49.6, 8.2, 50.0, 40.0, h_masonry=0.82, louvered_top=1.52)
    # NE corner sculptural travertine pier between East Pedestrian Gate (y=3.5..8.0) and North Car Gate (x=39.5..49.5)
    cpx0, cpy0, cpx1, cpy1 = box_m(49.5, 0.0, 50.0, 3.3)
    k.rect((cpx0, cpy0, g, cpx1, cpy1, 1.32), 'travertine_warm', 0, 'wall', 't7-ne-corner-pier', 't7-ne-corner-pier')
    k.rect((cpx0 - 0.02, cpy0 - 0.02, 1.32, cpx1 + 0.02, cpy1 + 0.02, 1.37), 'gola_matte_black', 0, 'coping', 't7-ne-corner-cap', 't7-ne-corner-pier')

    # North boundary along Verandah & Lawn Court (x_ft: 23.0..39.2, y_ft: 0.0..0.4): low dwarf wall + airy oak louver screen
    wall_run('t7-boundary-north-verandah', 23.0, 0.0, 39.2, 0.4, h_masonry=0.68, louvered_top=1.28)
    # North boundary along Caregiver Gully (x_ft: 0.0..23.0, y_ft: 0.0..0.4)
    wall_run('t7-boundary-north-gully', 0.0, 0.0, 23.0, 0.4, h_masonry=1.42)
    # West boundary gaps (y_ft: 0.0..2.0 and y_ft: 26.0..40.0) & South boundary gaps (x_ft: 0.0..2.0 and x_ft: 47.0..50.0)
    wall_run('t7-boundary-west-n', 0.0, 0.0, 0.4, 2.0, h_masonry=1.55)
    wall_run('t7-boundary-west-s', 0.0, 26.0, 0.4, 40.0, h_masonry=1.55)
    wall_run('t7-boundary-south-w', 0.0, 39.6, 2.0, 40.0, h_masonry=1.55)
    wall_run('t7-boundary-south-e', 47.0, 39.6, 50.0, 40.0, h_masonry=1.55)

    # 5. East Pedestrian Gate (x_ft=50.0, y_ft: 3.5..8.0) — travertine jamb piers, louvered oak gate leaf, and arrival steps
    eg_x0, eg_y0, eg_x1, eg_y1 = box_m(49.65, 3.5, 49.95, 8.0)
    for j_i, (ja, jb) in enumerate(((eg_x0 - 0.22, eg_x0), (eg_x1, eg_x1 + 0.18))):
        k.rect((ja, 0.0, g, jb, 0.16, 1.32), 'travertine_warm', 0, 'wall', f'east-walk-gate-jamb-{j_i}', 'east-walk-gate')
    eg_leaf_ids = []
    for suffix, bounds in [
        ('foot', (eg_x0 + 0.02, 0.06, 0.03, eg_x1 - 0.02, 0.11, 0.075)),
        ('head', (eg_x0 + 0.02, 0.06, 1.20, eg_x1 - 0.02, 0.11, 1.245)),
        ('left', (eg_x0 + 0.02, 0.06, 0.075, eg_x0 + 0.06, 0.11, 1.20)),
        ('right', (eg_x1 - 0.06, 0.06, 0.075, eg_x1 - 0.02, 0.11, 1.20)),
    ]:
        nid = f'east-walk-gate-leaf-0-{suffix}'
        k.rect(bounds, 'gola_matte_black', 0, 'gate', nid, 'east-walk-gate-leaf-0')
        eg_leaf_ids.append(nid)
    for row in range(12):
        zb = 0.095 + row * 0.090
        nid = f'east-walk-gate-leaf-0-blade-{row}'
        k.rect((eg_x0 + 0.06, 0.07, zb, eg_x1 - 0.06, 0.10, zb + 0.058), 'cladding_fluted_teak', 0, 'gate', nid, 'east-walk-gate-leaf-0')
        eg_leaf_ids.append(nid)
    k.rect((eg_x0, -0.78, g, eg_x1, 0.0, -0.15), 'travertine_warm', -1, 'step', 'east-arrival-step-1', 'east-pedestrian-gate')
    k.rect((eg_x0, -0.38, -0.15, eg_x1, 0.0, 0.0), 'travertine_warm', -1, 'step', 'east-arrival-step-2', 'east-pedestrian-gate')

    # 6. North-East Corner Car Gate (x_ft: 39.5..49.5, y_ft=0.0 -> 10' clear vehicle entrance!)
    # West pier at x_ft: 39.2..39.5 + paired architectural horizontal smoked-oak & matte-black louver swing leaves
    wp_x0, wp_y0, wp_x1, wp_y1 = box_m(39.15, 0.0, 39.5, 0.45)
    k.rect((wp_x0, wp_y0, g, wp_x1, wp_y1, 1.32), 'travertine_warm', 0, 'wall', 'north-car-gate-west-pier', 'north-vehicle-gate')
    k.rect((wp_x0 - 0.02, wp_y0 - 0.02, 1.32, wp_x1 + 0.02, wp_y1 + 0.02, 1.37), 'gola_matte_black', 0, 'coping', 'north-car-gate-west-cap', 'north-vehicle-gate')

    ng_x0, ng_y0, ng_x1, ng_y1 = box_m(39.5, 0.08, 49.5, 0.24)
    ng_ym = 0.5 * (ng_y0 + ng_y1)
    ng_motion = []
    for leaf_idx, (lya, lyb, pivot_y, ang) in enumerate([
        (ng_y0 + 0.02, ng_ym - 0.015, ng_y0 + 0.02, -math.pi / 2),
        (ng_ym + 0.015, ng_y1 - 0.02, ng_y1 - 0.02, math.pi / 2),
    ]):
        leaf_owner = f'north-vehicle-gate-leaf-{leaf_idx}'
        l_ids = []
        for suffix, bounds in [
            ('foot', (ng_x0, lya, -0.02, ng_x1, lyb, 0.025)),
            ('head', (ng_x0, lya, 1.18, ng_x1, lyb, 1.225)),
            ('left', (ng_x0, lya, 0.025, ng_x1, lya + 0.042, 1.18)),
            ('right', (ng_x0, lyb - 0.042, 0.025, ng_x1, lyb, 1.18)),
        ]:
            nid = f'{leaf_owner}-{suffix}'
            k.rect(bounds, 'gola_matte_black', 0, 'gate', nid, leaf_owner)
            l_ids.append(nid)
        for row in range(12):
            zb = 0.050 + row * 0.092
            nid = f'{leaf_owner}-blade-{row}'
            k.rect((ng_x0 + 0.008, lya + 0.042, zb, ng_x1 - 0.008, lyb - 0.042, zb + 0.056),
                   'cladding_fluted_teak', 0, 'gate', nid, leaf_owner)
            l_ids.append(nid)
        ng_motion.append({'ids': l_ids, 'pivot': [round(0.5 * (ng_x0 + ng_x1), 3), round(pivot_y, 3), 0.0], 'angle': ang})

    scene['gate_model'] = [
        {
            'id': 'east-walk-gate',
            'label': 'East pedestrian gate',
            'kind': 'gate',
            'floor': 0,
            'start': [round(eg_x0, 3), 0.085, 0.03],
            'axis': [1, 0, 0],
            'base': 0.03,
            'sill': 0,
            'width': round(eg_x1 - eg_x0, 3),
            'height': 1.22,
            'initial': 0,
            'parts': [{'ids': eg_leaf_ids, 'slide': [round(eg_x1 - eg_x0 + 0.04, 3), 0, 0]}],
        },
        {
            'id': 'north-vehicle-gate',
            'label': 'North-east corner car gate',
            'kind': 'gate',
            'floor': 0,
            'start': [round(0.5 * (ng_x0 + ng_x1), 3), round(ng_y0, 3), 0.0],
            'axis': [0, 1, 0],
            'base': 0.0,
            'sill': 0,
            'width': round(ng_y1 - ng_y0, 3),
            'height': 1.22,
            'initial': 0,
            'parts': ng_motion,
        },
    ]


def _configure_cameras_and_walk(scene: dict, H: float) -> None:
    """Configure hero, cutaway, exterior, interior, and walkthrough presets for Tirumala 7."""
    def cam(eye_ft, target_ft, z_eye, z_target, fov=52):
        ex, ey = local_m(*eye_ft)
        tx, ty = local_m(*target_ft)
        return {'position': [round(ex, 3), round(ey, 3), round(z_eye, 3)],
                'target': [round(tx, 3), round(ty, 3), round(z_target, 3)],
                'fov': fov}

    scene['cameras'].update({
        'hero': {'position': [21.8, -10.2, 8.0], 'target': [6.0, 6.6, 3.3], 'fov': 44},
        'exterior': {'position': [21.8, -10.2, 8.0], 'target': [6.0, 6.6, 3.3], 'fov': 44},
        'east_arrival': {'position': [9.8, -9.2, 2.3], 'target': [8.6, 4.5, 1.9], 'fov': 48},
        'north_frontage': {'position': [23.8, 5.8, 3.1], 'target': [6.5, 6.5, 3.2], 'fov': 46},
        'colony_overview': {'position': [28.0, -16.0, 14.5], 'target': [6.0, 7.6, 3.0], 'fov': 45},
        'roof_terraces': {'position': [19.5, -8.5, 13.8], 'target': [5.8, 7.8, 6.4], 'fov': 46},
        'kitchen_run': cam((37.4, 34.0), (45.8, 25.2), 1.50, 1.28, 60),
        'kitchen_from_dining': cam((25.0, 30.8), (45.8, 27.5), 1.50, 1.32, 56),
        'dining_double_height': cam((18.6, 29.2), (28.5, 28.2), 1.45, 3.95, 62),
        'living_hall': cam((21.0, 18.8), (11.8, 23.8), 1.52, 1.32, 58),
        'living_to_icu': cam((15.5, 22.0), (35.0, 16.0), 1.52, 1.30, 56),
        'icu': cam((37.2, 22.5), (25.2, 14.8), 1.52, 1.22, 58),
        'verandah': cam((38.0, 4.2), (24.5, 3.5), 1.52, 1.05, 58),
        'drawing_room': cam((15.8, 14.2), (11.5, 4.5), 1.50, 1.20, 58),
        'master_bedroom': cam((13.8, 28.8), (6.5, 36.8), 1.48, 1.12, 58),
        'gallery_void': cam((18.2, 28.8), (29.5, 28.8), H + 1.58, 1.25, 60),
        'master_suite': cam((3.0, 15.5), (12.5, 5.5), H + 1.48, H + 1.10, 58),
        'study_meditation': cam((25.5, 19.2), (35.5, 11.5), H + 1.50, H + 1.10, 58),
        'medium_bedroom': cam((15.2, 30.8), (4.5, 36.0), H + 1.50, H + 1.10, 58),
        'east_terrace': cam((43.5, 34.5), (41.5, 10.0), H + 1.58, H + 1.35, 56),
        'office_tv_hall': cam((9.0, 18.5), (33.5, 18.8), 2 * H + 1.45, 2 * H + 1.32, 58),
        'north_terrace': cam((39.0, 4.2), (12.0, 4.8), 2 * H + 1.58, 2 * H + 1.20, 56),
        'rooflight': cam((36.5, 27.5), (25.5, 29.0), 2 * H + 1.75, H + 1.20, 60),
        'stair_lobby': cam((31.5, 35.0), (18.5, 36.5), 2 * H + 1.55, 2 * H + 0.90, 58),
    })

    # Walkthrough floor starts
    f0_x, f0_y = local_m(20.5, 18.5)
    f1_x, f1_y = local_m(19.0, 23.0)
    f2_x, f2_y = local_m(18.5, 21.0)
    arr_x, arr_y = local_m(47.5, 6.0)
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
    """Build the complete, glitch-free Tirumala 7 3D scene."""
    scene = base_scene_builder(building, report)
    H = scene['floor_height']

    # Strip ALL generic auto-generated clutter, stray rugs, bed-leg dots, conical funnels, ceiling slats,
    # generic perimeter walls, and ALL round/spiky green plant proxies from `scene.py`!
    drop_roles = {
        'furniture', 'stair', 'railing', 'curtain', 'canopy', 'band', 'pipe',
        'carport', 'skirting', 'post', 'detail', 'rug', 'ceiling-feature',
        'cove', 'plant', 'plant-proxy', 'pot', 'planter', 'landscape',
        'parapet', 'coping', 'vehicle', 'gate', 'site', 'plinth', 'step',
    }
    scene['nodes'][:] = [
        n for n in scene['nodes']
        if n.get('role') not in drop_roles
        and not (n.get('role') == 'fixture' and not str(n.get('id', '')).endswith('/exhaust-grille'))
        and not str(n.get('owner', '')).startswith('stair-')
    ]
    scene['furniture'][:] = []
    scene['editables'][:] = []
    scene['vegetation'][:] = []
    scene['lawns'][:] = []

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
    # Explicitly keep scene['vegetation'] empty so zero round/spiky green plants ever spawn
    scene['vegetation'][:] = []
    scene['furniture'].extend(k.furniture)
    scene['colliders'].extend(k.colliders)
    scene['editables'].extend(k.editables)

    return scene
