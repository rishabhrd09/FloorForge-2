"""Heritage Bungalow: an opt-in custom-plan facade style (plan millimetres, road at local -Y).

Distilled from Indian government bungalows of the 1960s-80s: blush-white lime render with a red
comb frieze (a raised coping band with stripes hanging from it) on every parapet, steel windows
behind brick-bond grilles under sloping metal sunshades, a grilled entrance verandah, a carport
of corrugated sheet on banded steel posts, a bamboo chick pergola on the front terrace, a water
tank on the stair headhouse, a hexagonal paver court edged with a painted yellow band, rows of
terracotta pots, a large clipped lawn, rose-covered mesh fences and a shade-net boundary.

Only plans that set ``facadeStyle: "heritage-bungalow"`` reach this module; every other plan,
theme and sample keeps its existing composition. Everything here is a preliminary visual and
landscape proposal: it is not structural, regulatory or horticultural advice.
"""
from __future__ import annotations

import math
from typing import Any

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERITAGE = 'heritage-bungalow'

# Nostalgic distemper colours for enclosed rooms (sRGB). Names are the authored schema values.
WALL_PAINTS = {
    'sky-blue': '#c6d6dd',
    'mint-green': '#c9dcbb',
    'cream': '#ecdcb9',
    'pista': '#d6dfb4',
    'peach': '#efcfb2',
    'lilac': '#d6cae0',
    'ivory': '#f1ece0',
    'powder-pink': '#edcdc7',
    'lemon': '#efe0a0',
}

# Period floor finishes for walkable spaces.
FLOOR_FINISHES = ('ivory-vitrified', 'white-marble', 'ceramic-white', 'red-oxide', 'kota-stone', 'mosaic')

BOUNDARY_MM = 230          # compound wall
PILLAR_MM = 460            # rendered gate pillar, square
PEDESTRIAN_GATE_MM = 1200
VEHICLE_GATE_MM = 3600
TREAD_MM, RISER_MM = 300, 150


def is_heritage(building) -> bool:
    return (building or {}).get('planning', {}).get('facadeStyle') == HERITAGE


def _poly(p) -> list[list[int]]:
    return [[round(x), round(y)] for x, y in list(p.exterior.coords)[:-1]]


def _parts(geom):
    if geom.is_empty:
        return []
    if geom.geom_type == 'Polygon':
        return [geom]
    return [g for g in getattr(geom, 'geoms', []) if g.geom_type == 'Polygon']


def exterior_doors(building: dict[str, Any]) -> list[dict[str, Any]]:
    """Ground-floor doors in external walls, with their outer-face span and outward normal (mm)."""
    hosts = {w['id']: w for w in building['walls']}
    fp = Polygon(building['footprint'])
    out = []
    for o in building['openings']:
        if o['floor'] != 0 or o['kind'] not in ('entry', 'door', 'glazed') or 'outside' not in o['connects']:
            continue
        w = hosts[o['wall_id']]
        (ax, ay), (bx, by) = w['a'], w['b']
        length = math.hypot(bx - ax, by - ay)
        u = ((bx - ax) / length, (by - ay) / length)
        n = (-u[1], u[0])
        mid = (ax + u[0] * (o['offset'] + o['width'] / 2), ay + u[1] * (o['offset'] + o['width'] / 2))
        half = w['thickness'] / 2
        if fp.contains(Point(mid[0] + n[0] * (half + 60), mid[1] + n[1] * (half + 60))):
            n = (-n[0], -n[1])
        face = (mid[0] + n[0] * half, mid[1] + n[1] * half)
        out.append({'id': o['id'], 'kind': o['kind'], 'width': o['width'], 'u': u, 'n': n, 'face': face})
    return out


def _frame(door, along0, along1, out0, out1):
    """A rectangle in a door's frame: along the wall (u) and outward from its face (n)."""
    (fx, fy), (ux, uy), (nx, ny) = door['face'], door['u'], door['n']
    pts = [(fx + ux * a + nx * o, fy + uy * a + ny * o) for a, o in ((along0, out0), (along1, out0), (along1, out1), (along0, out1))]
    return Polygon(pts)


def open_edges(building: dict[str, Any]) -> list[dict[str, Any]]:
    """The middle of the longest garden edge of each ground-level verandah or yard, as a door-like opening."""
    fp = Polygon(building['footprint'])
    out = []
    for s in building['spaces']:
        if s['floor'] != 0 or s['kind'] not in ('veranda', 'drying-yard'):
            continue
        p = Polygon(s['clear'])
        best = None
        for a, b in zip(p.exterior.coords, list(p.exterior.coords)[1:]):
            edge = LineString([a, b])
            if edge.length < 1800 or not fp.boundary.buffer(1).covers(edge):
                continue
            if best is None or edge.length > best.length:
                best = edge
        if best is None:
            continue
        (ax, ay), (bx, by) = best.coords
        u = ((bx - ax) / best.length, (by - ay) / best.length)
        n = (-u[1], u[0])
        mid = best.interpolate(.5, normalized=True)
        if p.buffer(1).contains(Point(mid.x + n[0] * 50, mid.y + n[1] * 50)):
            n = (-n[0], -n[1])
        width = min(2400 if s['kind'] == 'veranda' else 1500, best.length - 800)
        out.append({'id': s['id'] + '-edge', 'kind': 'edge', 'width': width, 'u': u, 'n': n, 'face': (mid.x, mid.y)})
    return out


def entry_steps(building: dict[str, Any]) -> list[dict[str, Any]]:
    """Steps from every external ground-floor door (and open verandah edge) down the plinth, with low cheek
    walls at the main entry."""
    plinth = building['brief']['plinth_mm']
    count = max(1, math.ceil(plinth / RISER_MM))
    rise = plinth / count
    flights = []
    for door in exterior_doors(building) + open_edges(building):
        main = door['kind'] == 'entry'
        half = door['width'] / 2 + (600 if main else 300)
        landing = 1000 if main else 700
        depth = landing + (count - 1) * TREAD_MM
        treads = []
        for j in range(count):
            # j = 0 is the lowest tread; the top tread is the landing at the door threshold.
            o0 = depth - (j + 1) * TREAD_MM if j < count - 1 else 0
            o1 = depth - j * TREAD_MM
            treads.append({'polygon': _poly(_frame(door, -half, half, o0, o1)), 'top_mm': round(-plinth + (j + 1) * rise, 1)})
        cheeks = [_poly(_frame(door, s, s + 300, 0, depth)) for s in ((-half - 300, half) if main else ())]
        flights.append({'id': door['id'] + '-steps', 'kind': 'entry_steps', 'opening_id': door['id'], 'main': main,
                        'polygon': _poly(_frame(door, -half - (300 if main else 0), half + (300 if main else 0), 0, depth)),
                        'treads': treads, 'cheeks': cheeks, 'bottom_mm': -plinth, 'normal': list(door['n'])})
    return flights


def heritage_candidate(building: dict[str, Any], preferences, rect) -> dict[str, Any]:
    v = building['brief']
    fp = Polygon(building['footprint'])
    W, D = fp.bounds[2], fp.bounds[3]
    plot = Polygon(building['plot'])
    xmin, ymin, xmax, ymax = plot.bounds
    wt = BOUNDARY_MM
    inner = box(xmin + wt, ymin + wt, xmax - wt, ymax - wt)
    house = fp.buffer(40, join_style=2)
    features: list[dict[str, Any]] = []
    assemblies: list[dict[str, Any]] = []
    occupied = [house]

    flights = entry_steps(building)
    for f in flights:
        occupied.append(Polygon(f['polygon']).buffer(60, join_style=2))
    features.extend(flights)
    main = next((f for f in flights if f['main']), None)
    entry = next((o for o in building['openings'] if o['kind'] == 'entry'), None)
    if main:
        steps = Polygon(main['polygon'])
        ex = steps.centroid.x
        front_y = steps.bounds[1]
    else:
        ex, front_y = W / 2, -1200

    lawns: list[Polygon] = []      # trees, seats and the swing may stand on lawn, not on paving or in beds

    def add_poly(ident, kind, geom, **extra):
        geom = geom.intersection(inner).difference(house)
        for i, part in enumerate(sorted(_parts(geom), key=lambda p: -p.area)):
            part = part.buffer(0)
            if part.area < 120_000:
                continue
            features.append({'id': ident if i == 0 else f'{ident}-{i}', 'kind': kind, 'polygon': _poly(part), **extra})
            (lawns if kind == 'lawn' else occupied).append(part)

    def free(x, y, r=0):
        p = Point(x, y)
        return inner.buffer(-r - 60).contains(p) and not unary_union(occupied).buffer(r).intersects(p)

    def add_point(ident, kind, x, y, r=0, **extra):
        if not free(x, y, r):
            return False
        features.append({'id': ident, 'kind': kind, 'position_mm': [round(x), round(y)], **extra})
        occupied.append(Point(x, y).buffer(max(r, 60)))
        return True

    # ---- Gates: the pedestrian gate on the entry steps, a double-leaf car gate on the parking bay ----------
    lo, hi = xmin + wt + 600, xmax - wt - 600
    p0 = min(max(ex - PEDESTRIAN_GATE_MM / 2, lo + PILLAR_MM), hi - PILLAR_MM - PEDESTRIAN_GATE_MM)
    ped = (p0, p0 + PEDESTRIAN_GATE_MM)
    car = building.get('planning', {}).get('parkedCar')
    vehicle = None
    if car and v['front_mm'] >= 3000:
        c0 = min(max(car['x'] - VEHICLE_GATE_MM / 2, lo + PILLAR_MM), hi - PILLAR_MM - VEHICLE_GATE_MM)
        if c0 + VEHICLE_GATE_MM + PILLAR_MM * 2 + 600 <= ped[0] or c0 - PILLAR_MM * 2 - 600 >= ped[1]:
            vehicle = (c0, c0 + VEHICLE_GATE_MM)
    pillars = []
    for a, b in ([ped] + ([vehicle] if vehicle else [])):
        pillars += [(a - PILLAR_MM, a), (b, b + PILLAR_MM)]
    # The name-plate pillar faces the street on the side of the pedestrian gate away from the car gate.
    plate_left = not (vehicle and vehicle[1] < ped[0])
    plate = (ped[0] - PILLAR_MM, ped[0]) if plate_left else (ped[1], ped[1] + PILLAR_MM)
    gates = [{'id': 'gate-pedestrian', 'kind': 'pedestrian', 'x0_mm': round(ped[0]), 'x1_mm': round(ped[1]),
              'operation': 'swing', 'hinge': 'right' if plate_left else 'left', 'open_deg': 78}]
    if vehicle:
        gates.append({'id': 'gate-vehicle', 'kind': 'vehicle', 'x0_mm': round(vehicle[0]), 'x1_mm': round(vehicle[1]),
                      'operation': 'swing', 'leaves': 2, 'state': 'closed'})
    boundary = {
        'style': 'heritage_rendered_wall_shade_net', 'gates': gates,
        'gate_center_mm': round((ped[0] + ped[1]) / 2), 'gate_width_mm': PEDESTRIAN_GATE_MM,
        'letterbox_pier': {'x0_mm': round(plate[0]), 'x1_mm': round(plate[1]), 'height_mm': 1650, 'name_plate': True},
        'pillars': [{'x0_mm': round(a), 'x1_mm': round(b), 'globe': True} for a, b in sorted(pillars)],
        'front_wall_height_mm': 1050, 'side_wall_height_mm': 900, 'net_height_mm': 2050, 'wall_thickness_mm': wt,
        'movement_clearance_mm': 500, 'review_status': 'geometry_screen_pending',
    }
    for a, b in pillars:
        occupied.append(box(a - 50, ymin, b + 50, ymin + wt + 400))

    # ---- Carport and drive ------------------------------------------------------------------------------
    carport = None
    front_walk_y = (-2150, -650)
    if car:
        cx, cy = car['x'], car['y']
        x0, x1 = cx - 2150, cx + 2150
        x1 = min(x1, -150) if cx < 0 else x1
        x0 = max(x0, xmin + wt + 300)
        y0, y1 = cy - 3100, cy + 3100
        if x1 - x0 >= 3200 and inner.covers(box(x0, y0, x1, y1)) and not box(x0, y0, x1, y1).intersects(house):
            carport = rect('heritage-carport', 'carport', 0, (x0, y0, x1, y1), {
                'kind': 'sheet_carport', 'roof_low_mm': 2500, 'roof_high_mm': 2850, 'post_mm': 76, 'bands': ['red', 'black'],
                'fall': 'west' if cx < W / 2 else 'east', 'tube_light': True,
            }, HERITAGE, [])
            assemblies.append(carport)
        if vehicle:
            g0, g1 = vehicle
            drive = box(g0 + 120, ymin + wt, g1 - 120, cy)
            if carport:
                b0 = carport['geometry']['bounds_mm']
                drive = drive.union(box(b0[0], b0[1], b0[2], b0[3]))
            add_poly('site-drive', 'hex_paving', drive, tone='terracotta', role='drive')
            # The painted yellow hexagon band marks the edge of the drive toward the garden.
            band = box(g1 - 120, ymin + wt + 400, g1 + 160, (carport['geometry']['bounds_mm'][1] if carport else cy) - 200)
            add_poly('site-drive-band', 'hex_paving', band, tone='yellow', role='band')

    # ---- Entrance path from the gate, a front walk along the facade and the facade beds -------------------
    path = box(ex - 900, ymin + wt, ex + 900, front_y + 10)
    add_poly('site-entry-path', 'hex_paving', path, tone='terracotta', role='path')
    walk_x0 = (carport['geometry']['bounds_mm'][2] if carport else xmin + wt + 300)
    walk = box(walk_x0, front_walk_y[0], xmax - wt - 300, front_walk_y[1])
    add_poly('site-front-walk', 'hex_paving', walk, tone='terracotta', role='walk')
    add_poly('site-front-walk-band', 'hex_paving', box(walk_x0, front_walk_y[0] - 280, xmax - wt - 300, front_walk_y[0]), tone='yellow', role='band')
    facade = box(-400, front_walk_y[1], W + 400, 0)
    add_poly('site-facade-bed', 'flower_bed', facade, mix='facade', edging='brick')

    # ---- Big front lawn behind a clipped hedge, with a flower border and an Ashoka avenue on the boundary --
    lawn_x0, lawn_x1 = ex + 900 + 1100, xmax - wt - 1300
    border_y1 = ymin + wt + 1600
    lawn = box(lawn_x0, border_y1 + 800, lawn_x1, front_walk_y[0] - 280 - 900)
    hedges = []
    if lawn.area > 6e6:
        lx0, ly0, lx1, ly1 = lawn.bounds
        hedges = [((lx0 + lx1) / 2, ly0 - 300, lx1 - lx0, 0), (lx1 + 300, (ly0 + ly1) / 2, ly1 - ly0 + 600, math.pi / 2)]
        # The path side keeps a 1.6 m gap so the lawn is entered from the entrance path.
        gap = 1600
        upper = (ly0 + ly1) / 2 + gap / 2
        hedges += [(lx0 - 300, (ly0 - 300 + (ly0 + ly1) / 2 - gap / 2) / 2, (ly0 + ly1) / 2 - gap / 2 - (ly0 - 300), math.pi / 2),
                   (lx0 - 300, (upper + ly1 + 300) / 2, ly1 + 300 - upper, math.pi / 2),
                   ((lx0 + lx1) / 2 - gap, ly1 + 300, lx1 - lx0 - 2 * gap, 0)]
        for i, (hx, hy, length, rot) in enumerate(hedges):
            if length >= 900:
                features.append({'id': f'front-lawn-hedge-{i}', 'kind': 'hedge', 'position_mm': [round(hx), round(hy)],
                                 'size_mm': [round(length), 450, 550], 'rotation': rot, 'flowering': True})
                L = length / 2
                occupied.append(box(hx - (L if rot == 0 else 225), hy - (225 if rot == 0 else L), hx + (L if rot == 0 else 225), hy + (225 if rot == 0 else L)))
        add_poly('front-lawn', 'lawn', lawn)
    # One Ashoka (Polyalthia pendula) spire beside the pedestrian gate, away from the drive, as in the photographs.
    gx = ped[1] + PILLAR_MM + 650 if not (vehicle and vehicle[0] > ped[1]) else ped[0] - PILLAR_MM - 650
    add_point('ashoka-gate', 'tree', gx, ymin + wt + 650, 300, species='ashoka', scale=.86, mature_canopy_radius_mm=800)
    border = box(max(ex + 900 + 600, gx + 700), ymin + wt + 300, xmax - wt - 300, border_y1)
    add_poly('front-border-bed', 'flower_bed', border, mix='seasonal', edging='brick')
    # A great neem shades the far corner of the lawn; garden chairs gather under it.
    nx, ny = xmax - wt - 3600, ymin + wt + 4300
    if add_point('neem-front', 'tree', nx, ny, 400, species='neem', scale=1.0, mature_canopy_radius_mm=5200):
        add_point('lawn-chairs', 'garden_seat', nx - 2600, ny + 2600, 900, rotation=-.4)
    # Between the drive and the path: a rose bed with a row of pots along the path.
    if vehicle:
        mid = box(vehicle[1] + 300, ymin + wt + 1500, ex - 900 - 450, front_walk_y[0] - 400)
        add_poly('rose-bed', 'flower_bed', mid, mix='roses', edging='brick')

    # ---- Pots in rows along the path and the walk, flanking steps; tiered white plant stands ----------------
    pots = []
    y = ymin + wt + 1100
    while y < front_y - 500:
        for s in (-1, 1):
            pots.append((ex + s * 1040, y))
        y += 760
    yy = front_walk_y[0] - 140
    x = walk_x0 + 600
    while x < xmax - wt - 600:
        if abs(x - ex) > 1300:
            pots.append((x, yy))
        x += 820
    for k, (px, py) in enumerate(pots):
        tone = 'pink' if k % 7 == 3 else 'red'
        species = ('marigold', 'geranium', 'croton', 'periwinkle', 'tulsi', 'jade')[k % 6]
        features.append({'id': f'pot-{k:03d}', 'kind': 'pot', 'position_mm': [round(px), round(py)], 'radius_mm': 170 + 20 * (k % 3),
                         'height_mm': 280 + 30 * (k % 2), 'tone': tone, 'species': species})
    if main:
        sx0, sy0, sx1, sy1 = Polygon(main['polygon']).bounds
        for k, px in enumerate((sx0 - 700, sx1 + 700)):
            add_point(f'plant-stand-{k}', 'plant_stand', px, -1250, 350, rotation=0)

    # ---- West side garden: mango by the carport, side lawn, rose-covered mesh fence, Araucaria, a swing -----
    side_x0, side_x1 = xmin + wt, 0
    if side_x1 - side_x0 >= 3000:
        start = (carport['geometry']['bounds_mm'][3] if carport else 0) + 900
        add_point('mango-carport', 'tree', side_x0 + 1700, start + 1300, 300, species='mango', scale=1.0, mature_canopy_radius_mm=3800)
        fence_x = side_x0 + 1400
        features.append({'id': 'west-rose-fence', 'kind': 'rose_fence', 'a_mm': [round(fence_x), round(start + 3200)],
                         'b_mm': [round(fence_x), round(ymax - wt - 900)], 'height_mm': 1850, 'kerb_mm': 300})
        occupied.append(box(fence_x - 250, start + 3000, fence_x + 250, ymax - wt - 700))
        for k, yy in enumerate((start + 4600, start + 9800, start + 15000)):
            add_point(f'araucaria-west-{k}', 'tree', side_x0 + 650, yy, 250, species='araucaria', scale=.9 + .1 * (k % 2), mature_canopy_radius_mm=1300)
        hedge_x = fence_x + 650
        if ymax - wt - 900 - (start + 3200) > 2000:
            L = ymax - wt - 900 - (start + 3200)
            features.append({'id': 'west-rose-hedge', 'kind': 'hedge', 'position_mm': [round(hedge_x), round(start + 3200 + L / 2)],
                             'size_mm': [round(L), 450, 500], 'rotation': math.pi / 2, 'flowering': True})
            occupied.append(box(hedge_x - 225, start + 3200, hedge_x + 225, ymax - wt - 900))
        side = box(hedge_x + 500, start, side_x1 - 900, D - 600).difference(unary_union(occupied).buffer(150))
        add_poly('west-lawn', 'lawn', side)
        lawn_poly = next((Polygon(f['polygon']) for f in features if f['id'] == 'west-lawn'), None)
        if lawn_poly is not None:
            c = lawn_poly.centroid
            add_point('west-swing', 'jhoola', c.x, c.y + 1500, 900, rotation=math.pi / 2)
            add_point('west-hose', 'hose_reel', side_x1 - 600, start + 800, 300)

    # ---- East service lane: a covered paved walk beside the house and a lily border on the boundary ---------
    lane_x0, lane_x1 = W, xmax - wt
    if lane_x1 - lane_x0 >= 2000:
        walk_e = box(lane_x0 + 150, front_walk_y[0], lane_x0 + 1550, D - 300)
        add_poly('east-walk', 'hex_paving', walk_e, tone='terracotta', role='lane')
        assemblies.append(rect('heritage-side-canopy', 'canopy', 0, (lane_x0, 600, lane_x0 + 1750, D - 900), {
            'kind': 'sheet_canopy', 'height_mm': 2750, 'post_spacing_mm': 2600,
        }, HERITAGE, []))
        bed = box(lane_x0 + 1750, front_walk_y[1], lane_x1 - 100, D - 600)
        add_poly('east-lily-bed', 'flower_bed', bed, mix='lilies', edging='laterite')
        y = 900
        k = 0
        while y < D - 1500:
            features.append({'id': f'east-pot-{k:02d}', 'kind': 'pot', 'position_mm': [round(lane_x0 + 1660), round(y)], 'radius_mm': 190,
                             'height_mm': 300, 'tone': 'pink' if k % 2 else 'red', 'species': ('poinsettia', 'gerbera', 'marigold')[k % 3], 'rim': 'yellow'})
            y += 1500
            k += 1

    # ---- Rear garden: lawn, kitchen garden, tulsi, trees and a boundary hedge -------------------------------
    # The rear line is the nearest part of the back of the house (a recessed rear verandah sets it).
    rear0 = min(fp.intersection(LineString([(x, -1), (x, D + 1)])).bounds[3] for x in [W * k / 40 for k in range(1, 40)]
                if not fp.intersection(LineString([(x, -1), (x, D + 1)])).is_empty)
    if ymax - wt - rear0 >= 3000:
        hedge_y = ymax - wt - 550
        features.append({'id': 'rear-hedge', 'kind': 'hedge', 'position_mm': [round((xmin + xmax) / 2), round(hedge_y)],
                         'size_mm': [round(xmax - xmin - 2 * wt - 1200), 500, 1100], 'rotation': 0, 'flowering': False})
        occupied.append(box(xmin, hedge_y - 250, xmax, ymax))
        kg_x1 = min(1200, W * .1)
        kg = box(max(xmin + wt + 700, -4600), rear0 + 1500, kg_x1, hedge_y - 700).difference(house.buffer(800))
        add_poly('kitchen-garden', 'kitchen_garden', kg)
        add_poly('rear-lawn', 'lawn', box(kg_x1 + 700, rear0 + 300, xmax - wt - 900, hedge_y - 600)
                 .difference(house.buffer(500)).difference(unary_union(occupied).buffer(150)))
        rear_steps = max((Polygon(f['polygon']) for f in flights if f['normal'][1] > .5 and not f['main']),
                         key=lambda p: p.length, default=None)
        if rear_steps is not None:
            sx0, sy0, sx1, sy1 = rear_steps.bounds
            # A tulsi chaura on the axis of the rear verandah steps, with areca palms framing the steps.
            add_point('tulsi', 'tulsi', (sx0 + sx1) / 2, sy1 + 1700, 450)
            for k, x in enumerate((sx0 - 700, sx1 + 700)):
                add_point(f'rear-areca-{k}', 'plant', x, sy0 + 700, 300, species='areca', scale=.9)
        add_point('mango-rear', 'tree', xmax - wt - 2600, ymax - wt - 2400, 400, species='mango', scale=1.1, mature_canopy_radius_mm=4200)
        add_point('neem-rear', 'tree', kg_x1 + 2600, ymax - wt - 2300, 400, species='neem', scale=.85, mature_canopy_radius_mm=4500)
        for k, x in enumerate((W * .62, W * .78)):
            add_point(f'araucaria-rear-{k}', 'tree', x, ymax - wt - 1700, 250, species='araucaria', scale=.95, mature_canopy_radius_mm=1300)

    # ---- Roof fittings and the chick pergola ---------------------------------------------------------------
    terraces = [s for s in building['spaces'] if s['kind'] == 'terrace' and s['floor'] == 1]
    front_terrace = min(terraces, key=lambda s: Polygon(s['polygon']).bounds[1], default=None)
    if front_terrace:
        t = Polygon(front_terrace['polygon'])
        tx0, ty0, tx1, ty1 = t.bounds
        zone = box(tx0 + 450, ty0 + 450, min(tx1, tx0 + 5200) - 300, ty1 - 350).intersection(t.buffer(-350, join_style=2))
        if zone.area > 6e6 and zone.geom_type == 'Polygon':
            zx0, zy0, zx1, zy1 = zone.bounds
            assemblies.append(rect('heritage-chick-pergola', 'pergola', 1, (zx0, zy0, zx1, zy1), {
                'kind': 'chick_pergola', 'height_mm': 2450, 'post_spacing_mm': 2400, 'deck_space_id': front_terrace['id'],
            }, HERITAGE, []))
    cores = (building.get('rooftop') or {}).get('cores', [])
    if cores:
        c0 = cores[0]
        bx0, by0, bx1, by1 = c0['bounds']
        assemblies.append(rect('heritage-water-tank', 'roof_tank', building['storeys'], (bx0, by0, bx1, by1), {
            'kind': 'water_tank', 'capacity_l': 2000, 'diameter_mm': 1380, 'height_mm': 1620, 'core_id': c0['id'],
            'ladder': True, 'dish_antenna': True,
        }, HERITAGE, []))

    # A desert cooler on brackets outside one large bedroom window per side elevation, as in the reference.
    hosts = {w['id']: w for w in building['walls']}
    kinds = {s['id']: s['kind'] for s in building['spaces']}
    sides_done = set()
    for o in sorted(building['openings'], key=lambda o: (-o['floor'], o['id'])):
        if o['kind'] != 'window' or o.get('grille') or o['width'] < 1400:
            continue
        w = hosts[o['wall_id']]
        if not w['external'] or not any(kinds.get(r) == 'bedroom' for r in w['rooms']):
            continue
        (ax, ay), (bx, by) = w['a'], w['b']
        side = 1 if ax > W / 2 else -1
        if abs(ax - bx) > 1 or side in sides_done:      # one per side elevation, never the street front or rear
            continue
        y = min(ay, by) + o['offset'] + o['width'] / 2
        face = ax + side * w['thickness'] / 2
        x0, x1 = sorted((face + side * 60, face + side * 760))
        assemblies.append(rect(f'heritage-cooler-{len(sides_done)}', 'appliance', o['floor'], (x0, y - 460, x1, y + 460), {
            'kind': 'desert_cooler', 'opening_id': o['id'], 'facing': side,
        }, HERITAGE, [o['id']]))
        sides_done.add(side)

    return {
        'id': f'{HERITAGE}-candidate-01',
        'theme': preferences.exterior_theme,
        'assemblies': assemblies,
        'landscape': {
            'schema': 'floorforge.landscape/0.2', 'style': HERITAGE,
            'arrival_sequence': ['road_edge', 'gate', 'entrance_path', 'entrance_steps', 'grilled_verandah', 'main_door'],
            'features': features, 'boundary': boundary, 'outside_property_context': 'viewer_context_only',
            'design_notes': 'Hexagonal paver drive and paths edged with a painted yellow band, rows of terracotta pots, a clipped '
                            'and hedged lawn, rose-covered mesh fences, an Ashoka avenue, neem, mango and Araucaria trees and a '
                            'shade-net boundary on a rendered compound wall.',
        },
        'opening_changes': [],
        'score': 100 + len(assemblies) * 8,
        'rejections': [],
    }
