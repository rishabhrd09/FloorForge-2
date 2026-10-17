"""Plan Reveal: publish a FloorForge home as a scroll-driven page that opens on its own drawing.

The page is the generated model itself. Cut at +1.2 m and seen from far above through a very long lens it reads as
an ink plan; as the visitor scrolls the cut rises and the walls grow, the camera comes down to the front door and
walks the rooms in order, and each room stays a line drawing until the visitor arrives. Everything is derived from a
published export (building.json + scene.json), so automatic plans and authored custom plans publish the same way:

    python -m floorforge reveal --export path/to/export [--order living,kitchen,bedroom]

writes reveal.html, reveal-data.js, plan-reveal.js and reveal-manifest.json beside the export's files. The page needs
no network and opens straight from disk.
"""
from __future__ import annotations

import base64
import hashlib
import heapq
import html
import json
import math
from pathlib import Path

import numpy as np
from shapely import contains_xy, get_parts
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import polylabel, unary_union
from shapely.prepared import prep

from .drawings import ACCENT, GLASS, INK, LIGHT, plan_elements, primitives, principal_rect
from .model import DesignError, enu_to_local
from .spaces import NON_WALKABLE, SPACE_REGISTRY

SCHEMA = 'floorforge.plan-reveal/1'
ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / 'web/plan-reveal.js'
PAGE = ROOT / 'web/plan-reveal/page.html'
FONTS = ROOT / 'web/plan-reveal/fonts'
FILES = ('reveal.html', 'reveal-data.js', 'plan-reveal.js')
EYE = 1.6     # standing eye height above the finished floor (m)
BODY = .32    # the walking camera keeps this clear of walls, jambs and furniture (m)
CUT = 1.2     # plan cut above each finished floor (m)
CELL = .08    # path-finding grid (m)
PASSAGE = ('door', 'entry', 'cased', 'glazed')
# The order a guest is shown a home; rooms not listed are walked through but not presented.
SHOWN = ['foyer', 'drawing-room', 'living', 'family', 'courtyard', 'dining', 'kitchen', 'pooja', 'veranda', 'study',
         'bedroom', 'care-room', 'terrace', 'balcony']
COMPASS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
STROKES = {INK: 'ink', LIGHT: 'light', ACCENT: 'accent', GLASS: 'glass'}


def r4(v):
    return round(float(v), 4)


# ---------------------------------------------------------------------------------------------- the sheet
def sheet(b, scene, floor):
    """The floor's CAD plan (drawings.plan_elements) as layers the page draws onto the model: wall poché is laid at the
    cut, everything else (openings, stairs, tags, dimension chains, grid, levels, north point) on the floor. Floors and
    furniture are not copied; the model draws its own."""
    elems, bounds = plan_elements(b, scene, floor)
    lines, fills, texts, poche = {}, [], [], []

    def segment(style, a, c):
        lines.setdefault(style, []).extend([r4(a[0] / 1000), r4(a[1] / 1000), r4(c[0] / 1000), r4(c[1] / 1000)])

    def style(stroke, width, dash):
        tone = STROKES.get(stroke, 'ink')
        weight = 'heavy' if width >= .25 else 'medium' if width >= .15 else 'fine'
        return f'{tone}-{weight}' + ('-dash' if dash else '')

    for e in primitives(elems):
        if e['layer'] in ('A-FLOR', 'A-FURN'):
            continue
        if e['type'] == 'poly':
            pts = e['points']
            if e['layer'] == 'A-WALL' and e['fill'] == INK:
                poche.append([[r4(x / 1000), r4(y / 1000)] for x, y in pts])
                continue
            if e['fill'] not in ('none', None, ''):
                fills.append({'points': [[r4(x / 1000), r4(y / 1000)] for x, y in pts], 'tone': 1 if e['fill'] == INK else .18})
            if e['stroke'] not in ('none', None, ''):
                ring = pts + ([pts[0]] if e['closed'] else [])
                for a, c in zip(ring, ring[1:]):
                    segment(style(e['stroke'], e['width'], False), a, c)
        elif e['type'] == 'line':
            segment(style(e['stroke'], e['width'], e.get('dash')), e['a'], e['b'])
        elif e['type'] == 'circle':
            ring = [(e['x'] + e['r'] * math.cos(t), e['y'] + e['r'] * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 49)]
            for a, c in zip(ring, ring[1:]):
                segment(style(e['stroke'], e['width'], False), a, c)
        elif e['type'] == 'text':
            texts.append([r4(e['x'] / 1000), r4(e['y'] / 1000), e['text'], r4(e['size'] / 1000), e['anchor'], round(e.get('rot', 0), 2), e['layer']])
    if floor == 0:
        planting_symbols(scene, b, segment)
    return {'floor': floor, 'level': floor * scene['floor_height'], 'cut': CUT, 'bounds': [r4(v / 1000) for v in bounds],
            'poche': poche, 'fills': fills, 'lines': lines, 'texts': texts}


def planting_symbols(scene, b, segment):
    """Trees and shrubs outside the house, and in its open courts, as plan symbols: a dashed canopy, its trunk and a
    centre cross. A court's tree keeps its canopy inside the court."""
    fp = prep(Polygon(b['footprint']))
    courts = [Polygon(np.array(r['polygon']) * 1000) for r in scene.get('rooms', []) if r['floor'] == 0 and r['kind'] == 'courtyard']
    for v in scene.get('vegetation', []):
        x, y = v['position'][0] * 1000, v['position'][1] * 1000
        court = next((c for c in courts if c.contains(Point(x, y))), None)
        if v.get('floor', 0) != 0 or (fp.contains(Point(x, y)) and court is None):
            continue
        species = v.get('species', '')
        tree = any(k in species for k in ('tree', 'frangipani', 'palm', 'neem', 'olive', 'champa'))
        r = (1500 if tree else 450) * v.get('scale', 1)
        if court is not None:
            r = min(r, court.exterior.distance(Point(x, y)) - 60)
            if not tree or r < 150:
                continue
        for i in range(24):
            if tree and i % 2:
                continue
            t0, t1 = 2 * math.pi * i / 24, 2 * math.pi * (i + 1) / 24
            segment('light-fine', (x + r * math.cos(t0), y + r * math.sin(t0)), (x + r * math.cos(t1), y + r * math.sin(t1)))
        k = 120 if tree else 60
        segment('ink-fine', (x - k, y), (x + k, y))
        segment('ink-fine', (x, y - k), (x, y + k))


# ---------------------------------------------------------------------------------------------- the house
def room_records(b, scene):
    spaces = {s['id']: s for s in b['spaces']}
    out = []
    for r in scene.get('rooms', []):
        poly = Polygon(r['polygon'], r.get('holes') or [])
        if poly.is_empty or poly.area < .2:
            continue
        x0, y0, x1, y1 = principal_rect(Polygon(np.array(r['polygon']) * 1000)) if len(r['polygon']) >= 4 else poly.bounds
        width, depth = (x1 - x0) / 1000, (y1 - y0) / 1000
        spot = polylabel(poly, .02)
        out.append({'id': r['id'], 'floor': r['floor'], 'kind': r['kind'], 'name': r['name'],
                    'polygon': [[r4(x), r4(y)] for x, y in r['polygon']], 'holes': [[[r4(x), r4(y)] for x, y in h] for h in r.get('holes') or []],
                    'area': round(spaces.get(r['id'], {}).get('area_m2', poly.area), 2), 'size': [round(width, 2), round(depth, 2)],
                    'label': [r4(spot.x), r4(spot.y)], 'ceiling': ceiling(scene, r)})
    return out


def ceiling(scene, room):
    """Clear height to the room's ceiling (its lowest ceiling surface over the room), else the storey's clear height."""
    poly = prep(Polygon(room['polygon']))
    base = room['floor'] * scene['floor_height']
    found = [n['position'][2] - abs(n['scale'][2]) / 2 for n in scene['nodes']
             if n.get('role') == 'ceiling' and n.get('floor') == room['floor'] and poly.contains(Point(n['position'][0], n['position'][1]))]
    if found:
        return round(min(found) - base, 2)
    return round(scene['floor_height'] - .15, 2) if SPACE_REGISTRY.get(room['kind'], {}).get('roofed', True) else None


def passages(scene):
    """Doors, cased openings and glazed doors people walk through: centre, the wall's unit vectors and clear width (m)."""
    walls = {w['id']: w for w in scene['opening_model']['walls']}
    out = []
    for o in scene['opening_model']['openings']:
        if o['kind'] not in PASSAGE or o['wall_id'] not in walls:
            continue
        w = walls[o['wall_id']]
        a, c = np.array(w['a'], float) / 1000, np.array(w['b'], float) / 1000
        u = (c - a) / np.linalg.norm(c - a); n = np.array([-u[1], u[0]])
        p = a + u * o['offset'] / 1000
        q = p + u * o['width'] / 1000
        out.append({'id': o['id'], 'floor': o['floor'], 'kind': o['kind'], 'connects': o.get('connects', []), 'center': (p + q) / 2,
                    'u': u, 'n': n, 'p': p, 'q': q, 'width': o['width'] / 1000, 'thickness': w['thickness'] / 1000, 'sill': o.get('sill', 0) / 1000,
                    'panels': o.get('slidingPanels', 3) if o['kind'] == 'glazed' and o.get('sliding') else 0})
    return out


class Floor:
    """Free space for the walking camera on one storey: rooms and the openings between them, less a body's clearance
    from every wall and jamb and from furniture, rasterised for path finding."""

    def __init__(self, scene, b, rooms, doors, floor, outdoor=None):
        self.floor = floor
        walk = [Polygon(r['polygon'], r['holes']) for r in rooms if r['floor'] == floor and r['kind'] not in NON_WALKABLE]
        gaps = [Polygon([d['p'] - d['n'] * (d['thickness'] / 2 + .06), d['q'] - d['n'] * (d['thickness'] / 2 + .06),
                         d['q'] + d['n'] * (d['thickness'] / 2 + .06), d['p'] + d['n'] * (d['thickness'] / 2 + .06)])
                for d in doors if d['floor'] == floor and d['sill'] < .05]
        area = unary_union(walk + gaps + ([outdoor['area']] if outdoor else []))
        furniture = unary_union([Polygon(f['footprint']) for f in scene.get('furniture', []) if f['floor'] == floor] or [Polygon()])
        self.free = area.buffer(-BODY, join_style=2).difference(furniture.buffer(BODY - .04))
        if outdoor:
            # Outside, posts, walls and parked cars keep a body's width away; planting is brushed past.
            self.free = self.free.difference(outdoor['hard'].buffer(BODY - .06)).difference(outdoor['soft'].buffer(.08))
        self.prepared = prep(self.free)
        x0, y0, x1, y1 = area.bounds
        self.origin = np.array([x0, y0])
        self.shape = (int((y1 - y0) / CELL) + 2, int((x1 - x0) / CELL) + 2)
        ys, xs = np.mgrid[0:self.shape[0], 0:self.shape[1]]
        self.ok = contains_xy(self.free, x0 + xs * CELL, y0 + ys * CELL)

    def cell(self, p):
        j, i = np.round((np.array(p) - self.origin) / CELL).astype(int)
        return int(i), int(j)

    def point(self, c):
        return self.origin + np.array([c[1], c[0]]) * CELL

    def nearest_free(self, p, reach=1.2):
        """The free cell nearest to p (within reach), for anchors that land inside furniture clearance."""
        i0, j0 = self.cell(p)
        best = None
        r = int(reach / CELL)
        for i in range(max(0, i0 - r), min(self.shape[0], i0 + r + 1)):
            for j in range(max(0, j0 - r), min(self.shape[1], j0 + r + 1)):
                if self.ok[i, j]:
                    d = (i - i0) ** 2 + (j - j0) ** 2
                    if best is None or d < best[0]:
                        best = (d, (i, j))
        return None if best is None else self.point(best[1])

    def route(self, a, b):
        """Shortest 8-connected path across free cells, pulled taut against the free outline."""
        s, t = self.cell(a), self.cell(b)
        if not (self.inside(s) and self.inside(t)):
            return None
        dist = {s: 0.}; prev = {}; heap = [(0., s)]
        steps = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1), (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142)]
        goal = np.array(t)
        while heap:
            _, c = heapq.heappop(heap)
            if c == t:
                break
            for di, dj, w in steps:
                nb = (c[0] + di, c[1] + dj)
                if not self.inside(nb):
                    continue
                nd = dist[c] + w
                if nd < dist.get(nb, 1e18):
                    dist[nb] = nd; prev[nb] = c
                    heapq.heappush(heap, (nd + float(np.hypot(*(goal - nb))), nb))
        if t not in dist:
            return None
        cells = [t]
        while cells[-1] != s:
            cells.append(prev[cells[-1]])
        pts = [np.array(a, float)] + [self.point(c) for c in reversed(cells[1:-1])] + [np.array(b, float)]
        return self.taut(pts)

    def inside(self, c):
        return 0 <= c[0] < self.shape[0] and 0 <= c[1] < self.shape[1] and bool(self.ok[c])

    def clear(self, a, b):
        return self.prepared.covers(LineString([a, b])) if np.hypot(*(np.array(a) - b)) > 1e-6 else True

    def taut(self, pts):
        out = [pts[0]]; i = 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self.clear(pts[i], pts[j]):
                j -= 1
            out.append(pts[j]); i = j
        return out


def round_corners(pts, floor, passes=2):
    """Chaikin corner cutting that never leaves free space; each corner falls back to its sharp turn if a cut would."""
    for _ in range(passes):
        out = [pts[0]]
        for k in range(1, len(pts) - 1):
            a, c, e = pts[k - 1], pts[k], pts[k + 1]
            q = c + (a - c) * min(.25, .45 / max(np.hypot(*(a - c)), 1e-6))
            r = c + (e - c) * min(.25, .45 / max(np.hypot(*(e - c)), 1e-6))
            if floor.clear(out[-1], q) and floor.clear(q, r):
                out += [q, r]
            else:
                out.append(c)
        out.append(pts[-1])
        pts = out
    return pts


def resample(pts, spacing=.2):
    pts = [np.array(p, float) for p in pts]
    out = [pts[0]]; carry = 0.
    for a, c in zip(pts, pts[1:]):
        seg = float(np.hypot(*(c - a)))
        if seg < 1e-9:
            continue
        t = spacing - carry
        while t < seg:
            out.append(a + (c - a) * t / seg); t += spacing
        carry = seg - (t - spacing)
    if np.hypot(*(out[-1] - pts[-1])) > 1e-6:
        out.append(pts[-1])
    return out


# ---------------------------------------------------------------------------------------------- the tour
def facing(n, bearing):
    """Compass direction of a local (x, y) outward vector."""
    north = np.array(enu_to_local(0, 1, bearing)); east = np.array(enu_to_local(1, 0, bearing))
    ang = math.degrees(math.atan2(float(np.dot(n, east)), float(np.dot(n, north)))) % 360
    return COMPASS[int((ang + 22.5) // 45) % 8]


SMALL_WORDS = {'and', 'of', 'the', 'to', 'in', 'on', 'with', '&'}


def title_of(room):
    words = room['name'].split('·')[0].strip().split()
    name = ' '.join(w if (i and w.lower() in SMALL_WORDS) or not w[:1].isalpha() else w[:1].upper() + w[1:] for i, w in enumerate(words))
    if name.lower().startswith('the ') or name[-1:].isdigit():
        return name
    return 'The ' + name


TALL = {'wardrobe', 'fridge', 'bookshelf', 'shelving', 'tall-unit', 'cabinet-tall', 'kitchen-tall'}


def ray_distances(stand, segments, n=360, reach=30.):
    """Distance from `stand` to the nearest segment along n evenly spaced headings (2-D visibility)."""
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    d = np.stack([np.cos(ang), np.sin(ang)], 1)
    a, b = segments[:, 0], segments[:, 1]
    e = b - a
    out = np.full(n, reach)
    for k in range(len(segments)):
        den = d[:, 0] * e[k, 1] - d[:, 1] * e[k, 0]
        ok = np.abs(den) > 1e-9
        w = a[k] - stand
        t = np.where(ok, (w[0] * e[k, 1] - w[1] * e[k, 0]) / np.where(ok, den, 1), np.inf)
        u = np.where(ok, (w[0] * d[:, 1] - w[1] * d[:, 0]) / np.where(ok, den, 1), -1)
        hit = ok & (t > 1e-6) & (u >= 0) & (u <= 1)
        out = np.where(hit & (t < out), t, out)
    return ang, out


def door_leaves(scene, f):
    """The opened leaves of hinged doors on floor f, as thin rectangles standing into the room they swing into."""
    rooms = {r['id']: Polygon(r['polygon']) for r in scene.get('rooms', []) if r['floor'] == f}
    out = []
    for d in passages(scene):
        if d['floor'] != f or d['kind'] not in ('door', 'entry'):
            continue
        o = next(x for x in scene['opening_model']['openings'] if x['id'] == d['id'])
        hinge = d['p'] + d['u'] * .055 if o.get('hinge', 'start') == 'start' else d['q'] - d['u'] * .055
        n = d['n']
        swing = rooms.get(o.get('swing'))
        if swing is not None and not swing.contains(Point(*(d['center'] + n * .4))):
            n = -n
        leaf = LineString([hinge, hinge + n * max(.4, d['width'] - .06)]).buffer(.05, cap_style=2)
        out.append({'kind': 'door-leaf', 'footprint': [list(c) for c in leaf.exterior.coords[:-1]]})
    return out


# How far back a photographer stands from a room's main fitting to have all of it in frame.
PREFERRED = {'bed': 3.0, 'sofa': 2.8, 'dining-set': 2.6, 'kitchen-run': 2.0, 'recliner': 2.4, 'desk': 2.0, 'vanity': 1.6, 'puja-unit': 1.6}


def standpoint(room, door, floor, features=(), focus_at=None):
    """Where a guest stops: chosen like a photographer would. Candidate spots a step inside the door they came through
    and in the room's corners are each tried at every heading; a view scores for the floor it shows, the room's main
    fitting in frame at a comfortable distance and depth ahead, and loses for a wall in the face, a wall or a tall
    cupboard filling one side of the frame, or a long detour. A court too small to stand back in is seen from the
    doorway: a step back on the visitor's side, the opening framing its tree."""
    poly = Polygon(room['polygon'], room['holes'])
    n = door['n'] if poly.contains(Point(*(door['center'] + door['n'] * .3))) else -door['n']
    if room['kind'] == 'courtyard' and min(room['size']) < 3.2:
        focus = np.array(polylabel(poly, .05).coords[0] if focus_at is None else focus_at, float)
        # A sliding door opens by parking its far panes over the first one: look through the part that opens.
        open_at = door['width'] / (2 * door['panels']) if door.get('panels') else 0.
        for back in (1.15, .9, .65):
            for side in (0., .2, -.2):
                stand = door['center'] - n * back + door['u'] * (open_at + side)
                if floor.prepared.contains(Point(*stand)):
                    return stand, focus, 72.
    segs = []
    for ring in [poly.exterior] + list(poly.interiors):
        c = np.array(ring.coords)
        segs += [(c[i], c[i + 1]) for i in range(len(c) - 1)]
    for f in features:
        if f['kind'] in TALL or f['kind'] == 'door-leaf':   # a swung leaf blocks the lens like a cupboard
            c = np.array(f['footprint'] + f['footprint'][:1])
            segs += [(c[i], c[i + 1]) for i in range(len(c) - 1)]
    segs = np.array(segs, float)
    # Every piece of furniture, however slight (a floor lamp's pole), should not stand right in front of the lens.
    near = [prep(Polygon(f['footprint']).buffer(.12)) for f in features]
    near_geom = [Polygon(f['footprint']).buffer(.12) for f in features]
    main = next((f for f in features if f['kind'] in PREFERRED), None)
    focus = np.array(Polygon(main['footprint']).centroid.coords[0]) if main else None
    pref = PREFERRED[main['kind']] if main else 2.
    if room['kind'] == 'courtyard':
        focus = np.array(polylabel(poly, .05).coords[0])  # the court's tree or planting, seen whole
    if focus_at is not None:
        focus = np.array(focus_at, float)
    w, d = room['size']
    small = min(w, d)
    fov = 66. if room['kind'] in ('courtyard', 'terrace', 'veranda', 'balcony') else float(np.clip(62 - 1.8 * small, 50, 58))
    half = math.atan(math.tan(math.radians(fov) / 2) * 1.6)   # horizontal half-angle on a 16:10 screen
    cands = [door['center'] + n * .15] if room['area'] < 9 else []
    for step in (.7, .95, 1.2, 1.5):
        for side in (0, .35, -.35, .7, -.7):
            cands.append(door['center'] + n * step + door['u'] * side)
    x0, y0, x1, y1 = poly.bounds
    for cx, cy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        for inset in (.55, .8):
            cands.append(np.array([cx + inset * (1 if cx == x0 else -1), cy + inset * (1 if cy == y0 else -1)]))
    best = None
    area = max(poly.area, .5)
    for s in cands:
        threshold = float(np.hypot(*(s - door['center']))) < .3
        if not ((threshold or poly.buffer(-.25).contains(Point(*s))) and floor.prepared.contains(Point(*s))):
            continue
        ang, dist = ray_distances(s, segs)
        step = 2 * np.pi / len(ang)
        detour = float(np.hypot(*(s - door['center'])))
        for k in range(0, len(ang), 6):
            yaw = ang[k]
            rel = (ang - yaw + np.pi) % (2 * np.pi) - np.pi
            wedge = np.abs(rel) <= half
            seen = float(np.sum(dist[wedge] ** 2) * step / 2) / area
            ahead = float(dist[k])
            crowded = float(np.mean(dist[wedge] < .9))   # a wall or tall unit within arm's reach across the frame
            score = min(seen, 1.25) + .12 * min(ahead, 6) - (.9 if ahead < 1.5 else 0) - .05 * detour - 1.8 * crowded
            arc = [s + 1.3 * np.array([math.cos(yaw + a), math.sin(yaw + a)]) for a in np.linspace(-half * .7, half * .7, 7)]
            wedge = Polygon([s] + arc)
            for fp_, geom in zip(near, near_geom):
                if fp_.intersects(wedge):
                    score -= .9 * (1.3 - min(1.3, geom.distance(Point(*s)))) / 1.3 + .3
            if focus is not None:
                v = focus - s; fd = float(np.hypot(*v))
                off = abs((math.atan2(v[1], v[0]) - yaw + math.pi) % (2 * math.pi) - math.pi)
                if off < half * .8 and fd > 1.1:
                    score += 1.1 * (1 - off / half) + .45 * min(1., (fd - 1.1) / (pref - 1.1))
                else:
                    score -= .6
            if best is None or score > best[0]:
                best = (score, s, yaw, ahead)
    if best is None:
        stand = floor.nearest_free(door['center'] + n * .9)
        if stand is None:
            return None
        return stand, stand + n * 3, fov
    _, stand, yaw, ahead = best
    look = stand + np.array([math.cos(yaw), math.sin(yaw)]) * min(max(ahead * .7, 1.6), 5.)
    if focus_at is not None or room['kind'] == 'courtyard':
        look = stand + (focus - stand) * 1.0
    return stand, look, fov


# Outdoor roles a guest walks on or under; anything else standing between knee and head height is in the way.
UNDERFOOT = {'terrain', 'court', 'landscape', 'step', 'plinth', 'porch', 'lawn', 'door-portal', 'door', 'glass', 'drain', 'band', 'canopy', 'soffit',
             'pergola', 'roof', 'fixture-glow', 'downlight', 'cove', 'ceiling', 'ceiling-feature', 'window-hood', 'skirting'}


def node_box(node, assets):
    """World axis-aligned bounds of a scene node, from its asset's local bounds and the node transform."""
    a = assets.get(node['asset'])
    if not a:
        return None
    v = np.array(a['vertices'], float)
    lo, hi = v.min(0), v.max(0)
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]) * np.array(node['scale'])
    rx, ry, rz = node.get('rotation', (0, 0, 0))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    R = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    w = corners @ R.T + np.array(node['position'])
    return w.min(0), w.max(0)


def outdoor_area(b, scene):
    """The plot and the pavement in front of it, for the walk from the gate to the door, with what stands in the way:
    hard obstacles between knee and head height, and soft planting."""
    plot = Polygon(np.array(b['plot']) / 1000)
    x0, y0, x1, _ = plot.bounds
    fp = Polygon(np.array(b['footprint']) / 1000)
    house = prep(fp.buffer(-.02))
    ground = scene['bounds'][2]
    # The pedestrian gate opens for the guest; a vehicle gate stays shut and in the way.
    owners = {g['id'] for g in scene.get('gate_model') or [] if 'pedestrian' in g['id']}
    passable = {i for g in scene.get('gate_model') or [] if g['id'] in owners for part in g['parts'] for i in part['ids']}
    owners |= {o['id'] for o in scene['opening_model']['openings']}
    hard, soft = [], []
    for n in scene['nodes']:
        if n.get('floor', 0) > 0 or n.get('role') in UNDERFOOT or n['id'] in passable or n.get('owner') in owners:
            continue
        bb = node_box(n, scene['assets'])
        if bb is None:
            continue
        (ax, ay, az), (bx, by, bz) = bb
        if bz < ground + .2 or az > ground + 1.9 or (bx - ax) * (by - ay) > 40:
            continue
        foot = box(ax, ay, bx, by)
        if house.intersects(foot):
            continue  # the house itself: its walls and openings are already the edge of the walkable plot
        (soft if n.get('role') == 'plant-proxy' else hard).append(foot)
    for v in scene.get('vegetation', []):
        if v.get('floor', 0) == 0:
            soft.append(Point(*v['position'][:2]).buffer(.2 * v.get('scale', 1)))
    walk = unary_union([plot.buffer(.4), box(x0, y0 - 7, x1, y0)]).difference(fp.buffer(-.05))
    return {'area': walk, 'hard': unary_union(hard) if hard else Polygon(), 'soft': unary_union(soft) if soft else Polygon()}


def tour(b, scene, rooms, order=None, limit=8):
    """The walk: the arrival at the gate, then each presented room in turn, every leg routed through real openings
    with the camera's clearance kept from walls and furniture. A change of floor is a lift through the plan."""
    H = scene['floor_height']
    doors = passages(scene)
    entry = next((d for d in doors if d['kind'] == 'entry'), None) or next((d for d in doors if 'outside' in d['connects']), None)
    if entry is None:
        raise DesignError('REVEAL_ENTRY', 'The home needs an entrance door for the walkthrough.')
    floors = {}

    def floor_of(f):
        if f not in floors:
            floors[f] = Floor(scene, b, rooms, doors, f, outdoor_area(b, scene) if f == 0 else None)
        return floors[f]

    first = next((r for r in rooms if r['id'] in entry['connects']), None)
    if first is None:
        raise DesignError('REVEAL_ENTRY', 'The entrance door does not open into a room.')
    focus_of = {}
    if order:
        stops = [first]
        for key in order:
            ref = key.get('focus') if isinstance(key, dict) else None
            key = key['room'] if isinstance(key, dict) else key
            hit = [r for r in rooms if r not in stops and (r['id'] == key or r['kind'] == key or r['name'].lower() == key.lower())]
            stops += sorted(hit, key=lambda r: -r['area'])[:1]
            target = next((r for r in rooms if r['id'] == ref), None)
            if hit and target is not None:
                focus_of[stops[-1]['id']] = (polylabel(Polygon(target['polygon']), .05).coords[0], target['floor'])
    else:
        stops = choose(rooms, first, limit)
    footprint = Polygon(np.array(b['footprint']) / 1000)
    outward = entry['n'] if not footprint.contains(Point(*(entry['center'] + entry['n'] * .5))) else -entry['n']
    arrival = scene.get('walk', {}).get('arrival', {}).get('position')
    ground = float(arrival[2]) if arrival else scene['bounds'][2]
    f0 = floor_of(0)
    # The arrival is framed from across the pavement on the entrance's own axis, far enough back that the gate and
    # the boundary sit low under the whole front of the house; nearer only where the site runs out.
    start, back = None, 0.
    for back in (9., 8., 7., 6.5, 6., 5.5, 5., 4.5, 4., 3.5, 3., 2.6):
        q = entry['center'] + outward * back
        if f0.prepared.contains(Point(*q)) and f0.route(q, entry['center'] + outward * .8) is not None:
            start = q
            break
    if start is None:
        start = f0.nearest_free(arrival[:2], 2.5) if arrival else None
    if start is None:
        raise DesignError('REVEAL_ENTRY', 'No clear approach to the entrance from the street.')
    presented = [{'id': 'arrival', 'kind': 'arrival', 'floor': 0, 'title': 'The Arrival', 'number': 0,
                  'stand': [r4(start[0]), r4(start[1]), r4(ground + EYE)],
                  'look': [r4(entry['center'][0]), r4(entry['center'][1]), r4(1.45 + .12 * max(0., back - 5.5))], 'fov': 56.}]
    legs = []
    here, here_floor = np.array(start, float), 0
    for room in stops[:limit]:
        fl = floor_of(room['floor'])
        lift = room['floor'] != here_floor
        origin = landing_on(scene, room['floor'], fl) if lift else here
        if origin is None:
            continue
        door = entry if not legs else way_in(room, doors, origin, fl)
        poly_ = Polygon(room['polygon'])
        near = [f for f in scene.get('furniture', []) if f.get('room_id') == room['id']]
        near += [l for l in door_leaves(scene, room['floor']) if poly_.buffer(.3).intersects(Polygon(l['footprint']))]
        aim = focus_of.get(room['id'])
        level = room['floor'] * H
        if aim is None and room['kind'] in ('balcony', 'terrace'):
            # Out over the rail: the view a balcony is for, the garden or street below it.
            c = np.array(poly_.centroid.coords[0])
            away = c - np.array(footprint.centroid.coords[0])
            aim = (c + away / max(float(np.hypot(*away)), 1e-6) * 6., None)
        view = standpoint(room, door, fl, near, aim[0] if aim else None) if door else None
        if view is None:
            continue
        stand, look, fov = view
        path = walk(origin, stand, fl, doors, room['floor'])
        if path is None:
            continue
        z = level + EYE
        if aim and aim[1] is not None:
            # A look across to another storey stays within a comfortable tilt of the horizon.
            look_z = max(aim[1] * H + 1.2, z - math.tan(math.radians(28)) * math.dist(stand, look))
        elif aim:
            look_z = level - .6
        elif room['kind'] == 'courtyard':
            look_z = level + (1.7 if min(room['size']) < 3.2 else 1.9)
        else:
            look_z = level + (1.15 if room['kind'] == 'bedroom' else 1.3)   # a little lower over a bed
        approach = (ground + EYE, entry, footprint) if not legs else None
        cross = crossings(path, rooms, room['floor'], doors)
        opens = opened(path, scene, doors, room['floor'])
        if room['id'] not in {e['room'] for e in cross['enters']}:
            # Seen from its doorway rather than walked into: the door opens for the view, and the room sweeps in from
            # that opening as the guest arrives.
            cross['enters'].append({'s': cross['length'], 'room': room['id'], 'origin': [r4(door['center'][0]), r4(door['center'][1])]})
            opens = opens + [door['id']] if door['id'] not in opens else opens
        legs.append({'kind': 'lift' if lift else 'approach' if not legs else 'walk', 'from': len(presented) - 1, 'to': len(presented),
                     'floor': room['floor'], 'fromFloor': here_floor, 'points': leg_points(path, z, approach),
                     'opens': opens, **cross})
        presented.append({'id': room['id'], 'room': room['id'], 'kind': room['kind'], 'floor': room['floor'], 'title': title_of(room),
                          'number': len(presented), 'stand': [r4(stand[0]), r4(stand[1]), r4(z)],
                          'look': [r4(look[0]), r4(look[1]), r4(look_z)],
                          'fov': round(fov, 1), 'door': door.get('id')})
        here, here_floor = stand, room['floor']
    return {'stops': presented, 'legs': legs}


def choose(rooms, first, limit=8):
    """Default presentation: the entrance room, the living spaces, a courtyard, kitchen and dining, then the two
    largest bedrooms and one terrace, a floor at a time."""
    rank = {k: i for i, k in enumerate(SHOWN)}
    pool = [r for r in rooms if r['kind'] in rank and r is not first and r['area'] >= 4 and (r['kind'] != 'veranda' or r['area'] >= 8)]
    pool.sort(key=lambda r: (r['floor'], rank[r['kind']], -r['area']))
    picked = [first]
    for r in pool:
        if len(picked) >= limit:
            break
        if r['kind'] == 'bedroom' and sum(p['kind'] == 'bedroom' for p in picked) >= 2:
            continue
        if r['kind'] in ('terrace', 'balcony') and any(p['kind'] in ('terrace', 'balcony') for p in picked):
            continue
        picked.append(r)
    return picked


def way_in(room, doors, origin, floor):
    """The opening a guest walking from `origin` comes through: the first point their route enters the room, snapped
    to the room's door there; an open-plan room with no door of its own is entered across its open edge."""
    poly = Polygon(room['polygon'], room['holes'])
    target = floor.nearest_free(polylabel(poly, .05).coords[0], 1.5)
    route = floor.route(origin, target) if target is not None else None
    if not route:
        return None
    pts = resample(route, .05)
    inside = prep(poly.buffer(.02))
    k = next((i for i, p in enumerate(pts) if inside.contains(Point(*p))), None)
    if k is None:
        return None
    at = pts[k]
    own = [d for d in doors if room['id'] in d['connects'] and d['floor'] == room['floor']]
    near = min(own, key=lambda d: float(np.hypot(*(d['center'] - at))), default=None)
    if near is not None and float(np.hypot(*(near['center'] - at))) < near['width'] / 2 + .45:
        return near
    ahead = pts[min(k + 6, len(pts) - 1)] - pts[max(k - 6, 0)]
    n = ahead / max(float(np.hypot(*ahead)), 1e-6)
    return {'id': None, 'kind': 'open', 'center': at, 'n': n, 'u': np.array([-n[1], n[0]]), 'width': 1.2}


def walk(a, b, floor, doors, f):
    """A route from a to b that passes square through the middle of every door it uses."""
    raw = floor.route(a, b)
    if raw is None:
        return None
    line = LineString(raw)
    crossed = []
    for d in doors:
        if d['floor'] != f:
            continue
        half = d['thickness'] / 2 + .06
        gap = Polygon([d['p'] - d['n'] * half, d['q'] - d['n'] * half, d['q'] + d['n'] * half, d['p'] + d['n'] * half])
        if line.intersects(gap):
            crossed.append((line.project(Point(*d['center'])), d))
    anchors = [np.array(a, float)]
    for at, d in sorted(crossed, key=lambda x: x[0]):
        before = np.array(line.interpolate(max(0., at - .7)).coords[0])
        side = 1. if np.dot(before - d['center'], d['n']) >= 0 else -1.
        reach = max(.5, d['thickness'] / 2 + .45)
        anchors += [d['center'] + d['n'] * side * reach, d['center'], d['center'] - d['n'] * side * reach]
    anchors.append(np.array(b, float))
    pts = [anchors[0]]
    for p, q in zip(anchors, anchors[1:]):
        if floor.clear(p, q):
            pts.append(q)
            continue
        seg = floor.route(p, q)
        if seg is None:
            return round_corners(raw, floor)
        pts += seg[1:]
    return round_corners(pts, floor)


def opened(path, scene, doors, f):
    """Doors and gates the walk passes through, so the page can swing them open as the camera arrives."""
    line = LineString(path)
    ids = []
    for d in doors:
        half = d['thickness'] / 2 + .06
        if d['floor'] == f and line.intersects(Polygon([d['p'] - d['n'] * half, d['q'] - d['n'] * half, d['q'] + d['n'] * half, d['p'] + d['n'] * half])):
            ids.append(d['id'])
    for g in scene.get('gate_model') or []:
        start, axis = np.array(g['start'][:2]), np.array(g['axis'][:2])
        if f == 0 and line.intersects(LineString([start, start + axis * g['width']]).buffer(.15)):
            ids.append(g['id'])
    return ids


def landing_on(scene, f, floor):
    spot = next((s for s in scene.get('walk', {}).get('floors', []) if s['floor'] == f), None)
    return floor.nearest_free(spot['position'][:2], 2.) if spot else None


def leg_points(path, z, approach=None):
    """The camera's eye along a leg. On the arrival walk it rises from street level up the front steps, reaching the
    floor at the door."""
    out = []
    for p in resample(path):
        zz = z
        if approach:
            street, entry, footprint = approach
            if not footprint.contains(Point(*p)):
                zz = street + (z - street) * float(np.clip((2.6 - float(np.hypot(*(p - entry['center'])))) / 2.2, 0, 1))
        out.append([r4(p[0]), r4(p[1]), r4(zz)])
    return out


def crossings(path, rooms, f, doors):
    """Where the walk enters each room: its distance along the leg and the point the room's reveal sweeps from."""
    pts = resample(path, .1)
    polys = [(r['id'], prep(Polygon(r['polygon'], r['holes']).buffer(.03))) for r in rooms if r['floor'] == f]
    out, current, run = [], None, 0.
    for k, p in enumerate(pts):
        if k:
            run += float(np.hypot(*(p - pts[k - 1])))
        room = next((rid for rid, poly in polys if poly.contains(Point(*p))), None)
        if room and room != current:
            near = min((d for d in doors if room in d['connects'] and d['floor'] == f), key=lambda d: float(np.hypot(*(d['center'] - p))), default=None)
            origin = near['center'] if near is not None and float(np.hypot(*(near['center'] - p))) < 1.2 else p
            out.append({'s': round(run, 3), 'room': room, 'origin': [r4(origin[0]), r4(origin[1])]})
        if room:
            current = room
    return {'enters': out, 'length': round(run, 3)}


# ---------------------------------------------------------------------------------------------- room files
def room_files(b, scene, rooms, review=None, report=None):
    bearing = b['brief'].get('road_bearing_deg', 0)
    walls = {w['id']: w for w in scene['opening_model']['walls']}
    daylight = {d['space']: d for d in (report or {}).get('daylight', [])}
    vastu = {v['space']: v for v in ((report or {}).get('vastu') or {}).get('rooms', [])}
    notes = {}
    for w in (review or {}).get('warnings', []):
        if w.get('id'):
            notes.setdefault(w['id'], []).append(w['message'])
    furniture = {}
    for f in scene.get('furniture', []):
        furniture.setdefault(f.get('room_id'), []).append(f['kind'].replace('-', ' '))
    footprint = Polygon(np.array(b['footprint']) / 1000)
    out = {}
    for r in rooms:
        windows = []
        for o in scene['opening_model']['openings']:
            if r['id'] not in o.get('connects', []) or o['kind'] not in ('window', 'glazed', 'entry', 'door') or o['wall_id'] not in walls:
                continue
            if o['kind'] in ('door', 'entry') and 'outside' not in o.get('connects', []):
                continue
            w = walls[o['wall_id']]
            a, c = np.array(w['a'], float) / 1000, np.array(w['b'], float) / 1000
            u = (c - a) / np.linalg.norm(c - a); n = np.array([-u[1], u[0]])
            mid = a + u * (o['offset'] + o['width'] / 2) / 1000
            if footprint.buffer(-.02).contains(Point(*(mid + n * .6))):
                n = -n
            windows.append({'kind': o['kind'], 'width': o['width'] / 1000, 'height': o['height'] / 1000, 'sill': o.get('sill', 0) / 1000,
                            'faces': facing(n, bearing) if w.get('external') else 'inner'})
        w_, d_ = r['size']
        day = daylight.get(r['id'], {})
        v = vastu.get(r['name']) or vastu.get(r['name'].split('·')[0].strip())
        out[r['id']] = {'size': [w_, d_], 'sizeFt': [round(w_ / .3048, 1), round(d_ / .3048, 1)], 'area': r['area'], 'areaFt': round(r['area'] * 10.7639),
                        'ceiling': r['ceiling'], 'windows': windows, 'glazingPct': day.get('glazing_to_floor_pct'),
                        'vastu': {'zone': v['zone'], 'rating': v['rating'], 'preferred': v.get('preferred', [])} if v else None,
                        'furniture': sorted(set(furniture.get(r['id'], []))), 'notes': notes.get(r['id'], [])}
    return out


# ---------------------------------------------------------------------------------------------- publication
def reveal_data(b, scene, review=None, report=None, *, order=None, copy=None, grade='golden', limit=8):
    if scene.get('up') != 'Z' or scene.get('units') != 'm':
        raise DesignError('REVEAL_SCENE', 'Plan Reveal needs a Z-up metre scene from FloorForge.')
    rooms = room_records(b, scene)
    floors = sorted({r['floor'] for r in rooms if r['floor'] < b['storeys']})
    t = tour(b, scene, rooms, order=order, limit=limit)
    floors = sorted(set(floors) | {s['floor'] for s in t['stops']})
    v = b['brief']
    plot = [[r4(x / 1000), r4(y / 1000)] for x, y in b['plot']]
    north = enu_to_local(0, 1, v.get('road_bearing_deg', 0))
    text = {'eyebrow': f"{v.get('title', 'FloorForge home')} · ground floor plan · A-101", 'headline': ['Every house', 'starts as a', 'plan.'],
            'lede': 'This drawing is the building. Scroll, and walk into it.', 'cta': 'Open the drawing set', 'theme': 'stencil'}
    text.update(copy or {})
    return {'schema': SCHEMA, 'planHash': b.get('planHash'), 'title': v.get('title', 'FloorForge home'), 'grade': grade,
            **mask_shapes(b, scene, rooms),
            'floorHeight': scene['floor_height'], 'storeys': b['storeys'], 'plinth': v.get('plinth_mm', 0) / 1000,
            'plot': plot, 'footprint': [[r4(x / 1000), r4(y / 1000)] for x, y in b['footprint']], 'north': [r4(north[0]), r4(north[1])],
            'size': {'widthFt': round(v['width_mm'] / 304.8), 'depthFt': round(v['depth_mm'] / 304.8), 'widthM': round(v['width_mm'] / 1000, 2), 'depthM': round(v['depth_mm'] / 1000, 2)},
            'sheets': [sheet(b, scene, f) for f in floors], 'rooms': rooms, 'tour': t,
            'files': room_files(b, scene, rooms, review, report), 'copy': text}


def rings(geom):
    out = []
    for part in get_parts(geom):
        if part.geom_type == 'Polygon' and not part.is_empty and part.area > 1e-3:
            out.append([[[r4(x), r4(y)] for x, y in part.exterior.coords[:-1]]] + [[[r4(x), r4(y)] for x, y in h.coords[:-1]] for h in part.interiors])
    return out


def mask_shapes(b, scene, rooms):
    """Shapes for the reveal mask, one set per storey. A room owns its floor, a few centimetres of each wall face it
    looks at and the doors and windows in its walls; the garden owns everything else on that storey - facades, wall
    cores, roofs and the street - so it all arrives with the garden while each room waits for the visitor."""
    plot = Polygon(np.array(b['plot']) / 1000)
    x0, y0, x1, y1 = plot.bounds
    box_ = (x0 - 6, y0 - 8, x1 + 6, y1 + 6)
    walls = {w['id']: w for w in scene['opening_model']['walls']}
    openings = {}
    for o in scene['opening_model']['openings']:
        w = walls.get(o['wall_id'])
        if not w:
            continue
        a, c = np.array(w['a'], float) / 1000, np.array(w['b'], float) / 1000
        u = (c - a) / np.linalg.norm(c - a); n = np.array([-u[1], u[0]]); half = w['thickness'] / 2000 + .03
        p = a + u * (o['offset'] - 60) / 1000; q = a + u * (o['offset'] + o['width'] + 60) / 1000
        rect = Polygon([p - n * half, q - n * half, q + n * half, p + n * half])
        for rid in o.get('connects', []):
            openings.setdefault(rid, []).append(rect)
    levels = sorted({r['floor'] for r in rooms} | {b['storeys']})
    out = []
    for r in rooms:
        poly = unary_union([Polygon(r['polygon'], r['holes']).buffer(.04, join_style=2)] + openings.get(r['id'], []))
        reach = max(math.dist(a, c) for a in r['polygon'] for c in r['polygon'])
        out.append({'id': r['id'], 'floor': r['floor'], 'polygons': rings(poly), 'reach': round(reach + .8, 2)})
    outside = []
    for f in range(min(3, max(levels) + 1)):
        owned = [Polygon(r['polygon'], r['holes']).buffer(.04, join_style=2) for r in rooms if r['floor'] == f]
        owned += [rect for r in rooms if r['floor'] == f for rect in openings.get(r['id'], [])]
        outside.append({'floor': f, 'polygons': rings(box(*box_).difference(unary_union(owned))) if owned else rings(box(*box_))})
    return {'maskBox': [r4(v) for v in box_], 'maskRooms': out,
            'maskOutside': {'floors': outside, 'reach': round(math.dist(box_[:2], box_[2:]) + 4, 2)}}


def font_faces():
    """Embedded OFL faces for the page (see licenses/plan-reveal-fonts.txt); absent files fall back to system fonts."""
    css = []
    for family, name, weight, style in (('Reveal Mono', 'ibm-plex-mono-400.woff2', 400, 'normal'), ('Reveal Mono', 'ibm-plex-mono-500.woff2', 500, 'normal'),
                                        ('Reveal Stencil', 'big-shoulders-stencil-800.woff2', 800, 'normal'),
                                        ('Reveal Serif', 'instrument-serif-400.woff2', 400, 'normal'), ('Reveal Serif', 'instrument-serif-italic.woff2', 400, 'italic')):
        path = FONTS / name
        if path.is_file():
            data = base64.b64encode(path.read_bytes()).decode('ascii')
            css.append(f"@font-face{{font-family:'{family}';src:url(data:font/woff2;base64,{data}) format('woff2');font-weight:{weight};font-style:{style};font-display:block}}")
    return '\n'.join(css)


def page(data):
    template = PAGE.read_text(encoding='utf-8')
    c = data['copy']
    fields = {'TITLE': html.escape(data['title']), 'DESCRIPTION': html.escape(c.get('lede', '')), 'FONTS': font_faces(), 'THEME': html.escape(c.get('theme', 'stencil'))}
    for k, v in fields.items():
        template = template.replace('{{' + k + '}}', v)
    return template


def publish(folder, out=None, **options):
    """Write the walkthrough beside an export (or into `out`) and return the page's path."""
    folder = Path(folder)
    out = Path(out) if out else folder
    read = lambda n: json.loads((folder / n).read_text(encoding='utf-8')) if (folder / n).is_file() else None
    b, scene = read('building.json'), read('scene.json')
    if not b or not scene:
        raise DesignError('REVEAL_SOURCE', 'Choose a FloorForge export folder containing building.json and scene.json.')
    if b.get('planHash') != scene.get('planHash'):
        raise DesignError('REVEAL_SOURCE', 'building.json and scene.json come from different plans.')
    if not BUNDLE.is_file():
        raise DesignError('REVEAL_BUNDLE', 'web/plan-reveal.js is missing; build it with node web/plan-reveal/build.mjs.')
    data = reveal_data(b, scene, read('review.json'), read('report.json'), **options)
    out.mkdir(parents=True, exist_ok=True)
    packed = 'window.__PLAN_REVEAL__=' + json.dumps({'scene': scene, 'reveal': data}, separators=(',', ':'), ensure_ascii=True).replace('</', '<\\/') + ';\n'
    (out / 'reveal-data.js').write_text(packed, encoding='utf-8', newline='\n')
    (out / 'reveal.html').write_text(page(data), encoding='utf-8', newline='\n')
    (out / 'plan-reveal.js').write_bytes(BUNDLE.read_bytes())
    manifest = {'schema': 'floorforge.plan-reveal-manifest/1', 'planHash': data['planHash'],
                'stops': [s['id'] for s in data['tour']['stops']],
                'files': {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in FILES}}
    (out / 'reveal-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    return out / 'reveal.html'


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog='floorforge reveal', description='Publish a FloorForge export as a scroll-driven Plan Reveal walkthrough.')
    p.add_argument('--export', type=Path, required=True, help='Export folder with building.json and scene.json')
    p.add_argument('--out', type=Path, help='Write the page here instead of beside the export')
    p.add_argument('--order', help='Comma-separated room ids, kinds or names to visit, in order')
    p.add_argument('--grade', default='golden', choices=['day', 'golden', 'dusk', 'overcast'])
    a = p.parse_args(argv)
    path = publish(a.export, a.out, order=[s.strip() for s in a.order.split(',')] if a.order else None, grade=a.grade)
    print(json.dumps({'page': str(path)}))
    return 0
