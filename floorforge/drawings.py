"""One vector drawing list drives SVG, physically sized PDF sheets and a layered DXF.

The plans follow common architectural drafting practice: walls cut at +1.2 m and filled; each door drawn with its
leaf and swing into the room it serves, hinged on the jamb nearer the corner; sliding doors and cased openings in
their own symbols; windows as sill and glass lines; typed door and window tags (D, SD, O, W, V) with a schedule;
three dimension chains on every side (openings, walls, overall); coordination grid bubbles; finished floor levels;
the section line and a north point. Room tags give the name, the clear size of the room's principal rectangle and
the clear area.
"""
from __future__ import annotations
from pathlib import Path
from .model import *
from .scene import opening_polygon, transformation
from .frontage import gate_openings
from shapely.geometry import Polygon, LineString, Point, box
from shapely import get_parts
from shapely.ops import unary_union, polylabel
import numpy as np, html, io, math, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

INK = '#25372f'; LIGHT = '#a8afa4'; PAPER = '#ffffff'; ACCENT = '#9e653f'; GLASS = '#5f7d78'
AREA = (220, 216)  # drawing area of an A3 sheet in mm, left of the schedule panel and between the title and footer rules
LAYERS = [('A-WALL', 7, 35), ('A-WIND', 4, 18), ('A-DOOR', 3, 18), ('A-FLOR', 8, 13), ('A-FURN', 8, 13), ('A-ANNO', 7, 18),
          ('A-DIMS', 7, 13), ('A-STAIR', 7, 18), ('A-SITE', 8, 18), ('A-TAGS', 1, 13), ('A-GRID', 8, 13), ('A-LEVL', 7, 13),
          ('A-SECT', 1, 35), ('A-EXT', 30, 18), ('A-GATE', 30, 18), ('A-LAND', 3, 13), ('S-GRID', 8, 13)]


def P(points, fill='none', stroke=INK, width=.2, layer='A-WALL', closed=True):
    return {'type': 'poly', 'points': [[float(x), float(y)] for x, y in points], 'fill': fill, 'stroke': stroke, 'width': width, 'layer': layer, 'closed': closed}


def T(x, y, text, size=250, layer='A-ANNO', anchor='middle', rot=0):
    return {'type': 'text', 'x': float(x), 'y': float(y), 'text': str(text), 'size': size, 'layer': layer, 'anchor': anchor, 'rot': rot}


def L(a, b, stroke=INK, width=.15, layer='A-ANNO', dash=False):
    return {'type': 'line', 'a': [float(a[0]), float(a[1])], 'b': [float(b[0]), float(b[1])], 'stroke': stroke, 'width': width, 'layer': layer, 'dash': dash}


def C(x, y, r, stroke=INK, width=.18, layer='A-ANNO', fill='none'):
    return {'type': 'circle', 'x': float(x), 'y': float(y), 'r': float(r), 'stroke': stroke, 'width': width, 'layer': layer, 'fill': fill}


def DIM(p1, p2, axis, at, side=1, layer='A-DIMS', stagger=False):
    """A linear dimension between two points, its line at y=`at` (axis 'x') or x=`at` (axis 'y'); `side` puts the
    figure above/left (+1) or below/right (-1) of the line; `stagger` lifts a figure that does not fit between its
    ticks one text row further out, clear of its neighbours."""
    return {'type': 'dim', 'p1': [float(p1[0]), float(p1[1])], 'p2': [float(p2[0]), float(p2[1])], 'axis': axis, 'at': float(at), 'side': side,
            'layer': layer, 'stagger': bool(stagger)}


def dim(items, a, b, offset, axis='x', label=None):
    items.append(DIM(a, b, axis, offset))


def dim_parts(e):
    """Extension lines, the dimension line, architectural ticks and the figure of a DIM, as drawing primitives."""
    (x1, y1), (x2, y2) = e['p1'], e['p2']; at = e['at']; out = []; lay = e['layer']
    if e['axis'] == 'x':
        for px, py in ((x1, y1), (x2, y2)):
            d = 1 if at > py else -1
            out.append(L((px, py + d * 120), (px, at + d * 120), LIGHT, .12, lay))
        a, c = (min(x1, x2), at), (max(x1, x2), at)
        out.append(L(a, c, INK, .15, lay))
        for x in (a[0], c[0]):
            out.append(L((x - 55, at - 55), (x + 55, at + 55), INK, .28, lay))
        figure = str(round(abs(x2 - x1))); lift = 200 if e.get('stagger') else 0
        out.append(T((a[0] + c[0]) / 2, at + 70 + lift if e['side'] > 0 else at - 250 - lift, figure, 180, lay))
    else:
        for px, py in ((x1, y1), (x2, y2)):
            d = 1 if at > px else -1
            out.append(L((px + d * 120, py), (at + d * 120, py), LIGHT, .12, lay))
        a, c = (at, min(y1, y2)), (at, max(y1, y2))
        out.append(L(a, c, INK, .15, lay))
        for y in (a[1], c[1]):
            out.append(L((at - 55, y - 55), (at + 55, y + 55), INK, .28, lay))
        figure = str(round(abs(y2 - y1))); lift = 200 if e.get('stagger') else 0
        out.append(T(at - 70 - lift if e['side'] > 0 else at + 250 + lift, (a[1] + c[1]) / 2, figure, 180, lay, 'middle', 90))
    return out


def primitives(elements):
    out = []
    for e in elements:
        out.extend(dim_parts(e) if e['type'] == 'dim' else [e])
    return out


# ---------------------------------------------------------------------------------------------- shared geometry
def frame(w, o):
    a = np.array(w['a'], float); bb = np.array(w['b'], float); length = float(np.linalg.norm(bb - a)); u = (bb - a) / length
    n = np.array([-u[1], u[0]]); p = a + u * o['offset']; q = p + u * o['width']
    return a, bb, length, u, n, p, q


def principal_rect(poly):
    """The largest axis-aligned rectangle inside a room outline (its principal clear size)."""
    x0, y0, x1, y1 = poly.bounds
    if poly.buffer(1).covers(box(x0, y0, x1, y1)):
        return (x0, y0, x1, y1)
    xs = sorted(set(round(x, 3) for x, _ in poly.exterior.coords)); ys = sorted(set(round(y, 3) for _, y in poly.exterior.coords))
    best = None
    inner = poly.buffer(1)
    for i, a in enumerate(xs):
        for c in xs[i + 1:]:
            for j, bb in enumerate(ys):
                for d in ys[j + 1:]:
                    area = (c - a) * (d - bb)
                    if (best is None or area > best[0]) and inner.covers(box(a, bb, c, d)):
                        best = (area, (a, bb, c, d))
    return best[1] if best else (x0, y0, x1, y1)


def opening_types(b):
    if b.get('rooftop') and not any(o['floor']==b['storeys'] for o in b['openings']):
        from .rooftop import with_rooftop_objects
        b=with_rooftop_objects(b)
    """Tags by type (D door, SD sliding door, O cased opening, W window, V ventilator): one tag per distinct kind
    and size, numbered in order of appearance; returns ({opening id: tag}, schedule rows)."""
    names = {s['id']: s['name'] for s in b['spaces']}
    types, tags, counters = {}, {}, {}
    for o in sorted(b['openings'], key=lambda o: (o['floor'], o['id'])):
        kind = 'glazed' if b.get('planning', {}).get('g2Revision') and o.get('raw_kind') == 'sliding-door' else o['kind']
        if kind == 'window':
            pre = 'V' if (o['sill'] >= 1500 or o['height'] <= 700) else 'W'
        else:
            pre = {'glazed': 'SD', 'cased': 'O'}.get(kind, 'D')
        key = (pre, kind, round(o['width']), round(o['height']), round(o['sill']), bool(o.get('fixed')), bool(o.get('stackingSliding')))
        if key not in types:
            counters[pre] = counters.get(pre, 0) + 1
            types[key] = {'tag': f'{pre}{counters[pre]}', 'kind': kind, 'width': round(o['width']), 'height': round(o['height']),
                          'sill': round(o['sill']), 'count': 0, 'rooms': [], **({'fixed':True} if o.get('fixed') else {}), **({'stackingSliding':True} if o.get('stackingSliding') else {})}
        t = types[key]; t['count'] += 1; tags[o['id']] = t['tag']
        room = next((names[r] for r in o['connects'] if r in names and (o['kind'] == 'window' or r == o.get('swing'))), None) or \
            ' / '.join(names[r] for r in o['connects'] if r in names)
        if room not in t['rooms']:
            t['rooms'].append(room)
    order = {'D': 0, 'SD': 1, 'O': 2, 'W': 3, 'V': 4}
    rows = sorted(types.values(), key=lambda t: (order[t['tag'].rstrip('0123456789')], int(t['tag'].lstrip('DSOWV'))))
    return tags, rows


DESCRIPTION = {'entry': 'Main door, solid timber leaf in frame', 'door': 'Flush door, hardwood frame', 'glazed': 'Sliding glazed door, aluminium',
               'cased': 'Cased opening, no leaf', 'window': 'Sliding window, aluminium'}


def describe(t):
    if t.get('fixed'):
        return 'Fixed full-pane glazing, aluminium frame'
    if t.get('stackingSliding'):
        return 'Two independent sliding leaves, wall-stacking'
    if t['tag'].startswith('V'):
        return 'Ventilator, obscured glass / louvres'
    if t['kind'] == 'door' and t['width'] <= 800:
        return 'Flush door, water-resistant (WPC)'
    return DESCRIPTION.get(t['kind'], t['kind'])


def grid_axes(b, floor=0):
    """Coordination axes on the outer walls and on long interior walls: ([x], [y]) in plan millimetres."""
    W, D = Polygon(b['footprint']).bounds[2:]
    xs, ys = {}, {}
    for w in b['walls']:
        if w['floor'] != floor:
            continue
        (ax, ay), (bx, by) = w['a'], w['b']
        length = math.dist(w['a'], w['b'])
        if abs(ax - bx) < 1:
            xs[round(ax)] = xs.get(round(ax), 0) + length
        elif abs(ay - by) < 1:
            ys[round(ay)] = ys.get(round(ay), 0) + length

    def pick(found, span, limit):
        lines = sorted(x for x, total in found.items() if total >= span * limit or x < 400 or x > span - 400)
        keep = []
        for x in lines:
            if not keep or x - keep[-1] > 450:
                keep.append(x)
        return keep
    return pick(xs, D, .4), pick(ys, W, .4)


def axis_label(i):
    letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    return letters[i] if i < len(letters) else letters[i // len(letters) - 1] + letters[i % len(letters)]


def level(elems, x, y, text, layer='A-LEVL', size=160):
    """A finished-level mark: a filled triangle on the level line and its figure."""
    elems.append(P([(x - 110, y + 190), (x + 110, y + 190), (x, y)], INK, INK, .15, layer))
    elems.append(L((x - 380, y), (x + 380, y), INK, .15, layer))
    elems.append(T(x + 170, y + 60, text, size, layer, 'start'))


def north_point(elems, x, y, bearing, r=550):
    n = enu_to_local(0, 1, bearing)
    elems.append(C(x, y, r, INK, .2))
    tip = (x + n[0] * r * .92, y + n[1] * r * .92); tail = (x - n[0] * r * .55, y - n[1] * r * .55)
    side = (-n[1] * r * .28, n[0] * r * .28)
    elems.append(P([tip, (tail[0] + side[0], tail[1] + side[1]), (x - n[0] * r * .2, y - n[1] * r * .2)], INK, INK, .15))
    elems.append(P([tip, (tail[0] - side[0], tail[1] - side[1]), (x - n[0] * r * .2, y - n[1] * r * .2)], 'none', INK, .15))
    elems.append(T(x + n[0] * (r + 260) , y + n[1] * (r + 260) - 90, 'N', 260))


def bounds_of(elems, pad=250):
    xs, ys = [], []
    for e in primitives(elems):
        if e['type'] == 'poly':
            xs += [p[0] for p in e['points']]; ys += [p[1] for p in e['points']]
        elif e['type'] == 'line':
            xs += [e['a'][0], e['b'][0]]; ys += [e['a'][1], e['b'][1]]
        elif e['type'] == 'circle':
            xs += [e['x'] - e['r'], e['x'] + e['r']]; ys += [e['y'] - e['r'], e['y'] + e['r']]
        elif e['type'] == 'text':
            w = len(e['text']) * e['size'] * .55
            if e.get('rot'):
                xs += [e['x'] - e['size'], e['x'] + e['size']]; ys += [e['y'] - w / 2, e['y'] + w / 2]
            else:
                x0 = e['x'] - (w / 2 if e['anchor'] == 'middle' else 0)
                xs += [x0, x0 + w]; ys += [e['y'], e['y'] + e['size']]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


# ---------------------------------------------------------------------------------------------- floor plans
def _tirumala_rev8_meta(b):
    p = b.get('planning', {})
    if p.get('tirumalaOption') in ('P12-A', 'P11'):
        return None
    return p.get('tirumalaMeta') or p.get('tirumalaRev8')


def _tirumala_rev8_plan_underlays(b, floor):
    rev8 = _tirumala_rev8_meta(b)
    if not rev8:
        return [], []
    cz = rev8.get('canonicalZones', {})
    under, over = [], []
    # Plot perimeter 40 x 50 ft (12192 x 15240 mm)
    under.append(P([(0, 0), (12192, 0), (12192, 15240), (0, 15240)], '#fafaf5', INK, .3, 'A-SITE'))
    over.append(T(6096, -340, 'EAST ROAD — 9.0 m ROW (40 FT FRONTAGE / PRINCIPAL ARRIVAL)', 155, 'A-SITE'))
    over.append(T(12520, 7620, 'NORTH ROAD — 12.0 m ROW (50 FT DEPTH)', 155, 'A-SITE', rot=90))
    opt = rev8.get('option', 'A')
    lbl = rev8.get('label', '')
    gh = rev8.get('geometryHash', '')[:12]
    over.append(T(6096, 15560, f'TIRUMALA REV {rev8.get("revision", 8)} — OPTION {opt} ({lbl.upper()}) | GEOM HASH {gh}', 165, 'A-ANNO'))
    if floor == 0:
        fc = cz.get('frontCourt')
        if fc:
            under.append(P(fc, '#f4efe2', '#b5aa94', .18, 'A-SITE'))
            over.append(T(4267, 1250, 'FRONT COURT (28 x 6.5 FT / +0.300 m)', 135, 'A-SITE'))
        st = cz.get('entrySteps')
        if st:
            under.append(P(st, '#e6decb', INK, .22, 'A-STAIR'))
            under.append(L((st[0][0], 305), (st[1][0], 305), INK, .18, 'A-STAIR'))
            over.append(T((st[0][0] + st[1][0]) / 2, 290, '2 UP (2 x 150 mm -> +0.300 m)', 115, 'A-STAIR'))
        pk = cz.get('parking')
        if pk:
            under.append(P(pk, '#e7e6de', '#8a887f', .22, 'A-SITE'))
            over.append(T(10440, 5620, 'CAR BAY 10.5 x 19 FT (FFL ±0.000 m)', 130, 'A-SITE'))
        car = cz.get('car')
        if car:
            over.append(P(car, '#f7f8f6', INK, .22, 'A-FURN'))
            cx0, cy0 = car[0]; cx1, cy1 = car[2]
            over.append(P([(cx0 + 180, cy0 + 950), (cx1 - 180, cy0 + 950), (cx1 - 180, cy1 - 850), (cx0 + 180, cy1 - 850)], 'none', LIGHT, .14, 'A-FURN'))
            over.append(T((cx0 + cx1) / 2, (cy0 + cy1) / 2, 'CAR 6.5 x 15.5 FT', 125, 'A-FURN'))
        npas = cz.get('north')
        if npas:
            under.append(P(npas, '#dfead5', '#78916b', .18, 'A-LAND'))
            nx0, ny0 = npas[0]; nx1, ny1 = npas[2]
            under.append(L((nx1 - 60, ny0), (nx1 - 60, ny1), '#4c6b3c', .35, 'A-LAND', True))
            over.append(T((nx0 + nx1) / 2, (ny0 + ny1) / 2, '3 FT CLEAR NORTH PASSAGE (+0.300 m)', 115, 'A-LAND', rot=90))
        gdn = cz.get('garden')
        if gdn:
            under.append(P(gdn, '#d7e5c8', '#6b845e', .2, 'A-LAND'))
            gp = polylabel(Polygon(gdn), 10)
            over.append(T(gp.x, gp.y + 120, 'OPEN NW GARDEN (+0.300 m)', 155, 'A-LAND'))
            over.append(T(gp.x, gp.y - 140, 'UNBUILT / STEPPING STONES & LAWN', 120, 'A-LAND'))
        gsa = cz.get('groundStairArrival')
        if gsa:
            over.append(P(gsa, 'none', ACCENT, .16, 'A-STAIR', True))
            if rev8.get('revision',8)>=10:
                ap=polylabel(Polygon(gsa),10)
                over.append(T(ap.x,ap.y,'STAIR ENTRY',100,'A-STAIR'))
            else:over.append(T(4343, 6020, 'STAIR ARRIVAL', 110, 'A-STAIR'))
        puja = cz.get('puja')
        if puja:
            over.append(P(puja, '#f7f1e1', ACCENT, .18, 'A-FURN', True))
            px0, py0 = puja[0]; px1, py1 = puja[2]
            over.append(P([(px0 + 180, py0 + 60), (px1 - 180, py0 + 60), (px1 - 180, py0 + 280), (px0 + 180, py0 + 280)], '#d8b979', INK, .16, 'A-FURN'))
            over.append(T((px0 + px1) / 2, (py0 + py1) / 2 + 90, 'PUJA 4x3 FT (EAST ALTAR)', 105, 'A-ANNO'))
        lv = cz.get('livingVoid')
        if lv:
            over.append(P(lv, 'none', ACCENT, .18, 'A-FLOR', True))
            over.append(T(5950, 8650, 'VOID ABOVE (~23 FT CLEAR)', 120, 'A-ANNO'))
        bed = cz.get('bed')
        if bed:
            bx0, by0 = bed[0]; bx1, by1 = bed[2]; bcy = (by0 + by1) / 2
            # Pillow at South head end (x = bx0)
            over.append(P([(bx0 + 90, by0 + 120), (bx0 + 380, by0 + 120), (bx0 + 380, by1 - 120), (bx0 + 90, by1 - 120)], '#ece7dc', INK, .14, 'A-FURN'))
            # Sightline arrow to North glazing & garden
            over.append(L((bx0 + 550, bcy), (11850, bcy), GLASS, .18, 'A-ANNO', True))
            over.append(T((bx0 + bx1) / 2, bcy, 'BED 7x3.5 FT (HEAD S -> FEET N)', 105, 'A-ANNO'))
    elif floor == 1:
        usa = cz.get('upperStairArrival')
        if usa:
            over.append(P(usa, 'none', ACCENT, .18, 'A-STAIR', True))
            if rev8.get('revision',8)>=10:
                ap=polylabel(Polygon(usa),10)
                over.append(T(ap.x,ap.y,'ARRIVAL',100,'A-STAIR'))
            else:over.append(T(4343, 7240, 'UPPER ARRIVAL (OUTSIDE VOID)', 110, 'A-STAIR'))
        lv = cz.get('livingVoid')
        if lv:
            over.append(P(lv, 'none', INK, .22, 'A-FLOR', True))
            lv_bb = Polygon(lv).bounds
            over.append(L((lv_bb[0], lv_bb[1]), (lv_bb[2], lv_bb[3]), LIGHT, .14, 'A-FLOR', True))
            over.append(L((lv_bb[0], lv_bb[3]), (lv_bb[2], lv_bb[1]), LIGHT, .14, 'A-FLOR', True))
            if rev8.get('revision',8)<10:
                over.append(T((lv_bb[0] + lv_bb[2]) / 2, (lv_bb[1] + lv_bb[3]) / 2, 'DOUBLE-HEIGHT LIVING VOID (~23 FT CLEAR)', 135, 'A-ANNO'))
        rl = cz.get('rooflight')
        if rl:
            over.append(P(rl, 'none', GLASS, .22, 'A-WIND', True))
            rx0, ry0 = rl[0]; rx1, ry1 = rl[2]
            light_size = f'{(rx1-rx0)/304.8:.0f} x {(ry1-ry0)/304.8:.0f}'
            over.append(T((rx0 + rx1) / 2, (ry0 + ry1) / 2 - 260, f'ROOFLIGHT ({light_size} FT OVERHEAD)', 115, 'A-WIND'))
    return under, over


def plan_elements(b, scene, floor=0):
    from .tirumala_p11_p12 import is_p11_p12, p11_p12_plan_elements
    if is_p11_p12(b):
        return p11_p12_plan_elements(b, scene, floor)
    if b.get('rooftop'):
        from .rooftop import with_rooftop_objects
        b=with_rooftop_objects(b)
    elems = []; v = b['brief']; H = v['floor_height_mm']; fp = Polygon(b['footprint']); W, D = fp.bounds[2:]
    spaces = [s for s in b['spaces'] if s['floor'] == floor]
    polys = {s['id']: Polygon(s['polygon'], s.get('holes', [])) for s in b['spaces']}
    hosts = {w['id']: w for w in b['walls']}
    tags, _ = opening_types(b)
    plinth = v['plinth_mm']
    rev8_under, rev8_over = _tirumala_rev8_plan_underlays(b, floor)
    elems.extend(rev8_under)
    for room in spaces:
        elems.append(P(room['clear'], '#eef2ef' if room['kind'] in ('bathroom', 'utility') else '#fbfbf7', 'none', layer='A-FLOR'))
    if b.get('floor_plates') or b.get('rooftop'):
        from .plan_geometry import plate
        for part in get_parts(plate(b,floor)):
            if part.geom_type!='Polygon':continue
            elems.append(P(list(part.exterior.coords),'none',LIGHT,.15,'A-FLOR'))
            for hole in part.interiors:elems.append(P(list(hole.coords),'none',INK,.2,'A-FLOR'))
        for guard in b.get('guards',[]):
            if guard['floor']!=floor:continue
            if guard.get('parapet'):
                for region in guard['parapet']:
                    elems.append(P(region['polygon'],'#e7e4dc',INK,.25,'A-WALL'))
            else:elems.append(P(guard['points'],'none',ACCENT,.3,'A-FLOR',False))
    if b.get('planning',{}).get('privateGarden') and b['roofs'][-1].get('rooflight'):
        if floor==1:
            hole=next(h for h in b['floor_plates'][1]['openings'] if h['id']=='living-lightwell-1')
            label=Polygon(hole['regions'][0]['polygon']).representative_point()
            elems.append(T(label.x,label.y,'OPEN TO LIVING BELOW',125,'A-FLOR'))
        if floor in (1,2) and b['roofs'][-1].get('suiteNorthlight'):
            shaft=Polygon(b['roofs'][-1]['suiteNorthlight'][0]['polygon'])
            elems.append(P(list(shaft.exterior.coords),'none',ACCENT,.25,'A-WIND'))
            elems.append(T(shaft.centroid.x,shaft.centroid.y,'SUITE NORTHLIGHT',105,'A-WIND'))
        if floor==2:
            glass=Polygon(b['roofs'][-1]['rooflight'][0]['polygon'])
            elems.append(P(list(glass.exterior.coords),'none',ACCENT,.25,'A-WIND'))
            elems.append(T(glass.centroid.x,glass.centroid.y,'ROOFLIGHT OVER',125,'A-WIND'))
    for member in b.get('terraceFrame', []):
        if member['kind']=='column' and member['floor']==floor:
            elems.append(P(list(box(*member['bounds']).exterior.coords),'#aaa7a0',INK,.25,'A-WALL'))
    # Walls cut at +1.2 m: solid poché with every opening that crosses the cut removed.
    for wall in [w for w in b['walls'] if w['floor'] == floor]:
        p = Polygon(wall['polygon'])
        for o in b['openings']:
            if o['wall_id'] == wall['id'] and o['sill'] <= 1200 < o['sill'] + o['height']:
                p = p.difference(opening_polygon(wall, o))
        for part in get_parts(p):
            if part.geom_type == 'Polygon' and not part.is_empty:
                elems.append(P(list(part.exterior.coords), INK, INK, .25))
    # Openings, each with its type tag.
    for o in [o for o in b['openings'] if o['floor'] == floor]:
        w = hosts[o['wall_id']]; a, bb, length, u, n, p, q = frame(w, o); t = w['thickness'] / 2; m = (p + q) / 2
        inside = polys.get(o.get('swing')) if o.get('swing') else None
        if inside is None:
            inner = next((r for r in o['connects'] if r in polys and r != 'outside'), None)
            inside = polys.get(inner) if inner else fp
        if not inside.buffer(5).contains(Point(*(m + n * (t + 300)))):
            n = -n
        if o['kind'] == 'window':
            above = o['sill'] > 1200
            for s_ in (-t, t):
                elems.append(L(p + n * s_, q + n * s_, INK, .13, 'A-WIND', above))
            for s_ in (-18, 18):
                elems.append(L(p + n * s_, q + n * s_, GLASS, .16, 'A-WIND', above))
            elems.append(L(p - n * t, p + n * t, INK, .13, 'A-WIND')); elems.append(L(q - n * t, q + n * t, INK, .13, 'A-WIND'))
            out = n if not fp.buffer(-5).contains(Point(*(m + n * (t + 300)))) else -n
            c = m + out * (t + 380)
            elems.append(T(c[0], c[1] - 60, tags[o['id']], 150, 'A-TAGS'))
            continue
        if o.get('timberScreen'):
            radius=(o['width']-140)/2-4
            for normal in ((n,) if o.get('screenSliding') else (n,-n)):
                for h,along in ((p+u*70+normal*105,u),(q-u*70+normal*105,-u)):
                    elems.append(L(h,h+normal*radius,INK,.2,'A-DOOR'))
                    arc=[h+radius*(along*math.cos(th)+normal*math.sin(th)) for th in np.linspace(0,math.pi/2,25)]
                    for v0,v1 in zip(arc,arc[1:]):elems.append(L(v0,v1,INK,.1,'A-DOOR',True))
            if o.get('screenSliding'):
                elems.append(L(p+u*70-n*105,m-n*105,GLASS,.2,'A-DOOR'))
                elems.append(L(m-n*245,q-u*70-n*245,GLASS,.2,'A-DOOR'))
                tip=m-n*350-u*200
                elems.append(L(tip+u*400,tip,INK,.13,'A-DOOR'))
                elems.append(L(tip,tip+u*80+n*50,INK,.13,'A-DOOR'))
        elif o['kind'] == 'glazed':
            half = o['width'] / 2 + 40
            for s0, s1, off in ((0, half, 22), (o['width'] - half, o['width'], -22)):
                a0 = p + u * s0; a1 = p + u * s1
                elems.append(P([a0 + n * (off - 16), a1 + n * (off - 16), a1 + n * (off + 16), a0 + n * (off + 16)], '#e3ebea', GLASS, .15, 'A-DOOR'))
            arrow = m - n * (t + 160)
            elems.append(L(arrow - u * 250, arrow + u * 250, INK, .13, 'A-DOOR'))
            elems.append(L(arrow + u * 250, arrow + u * 170 + n * 60, INK, .13, 'A-DOOR'))
        elif o['kind'] == 'cased':
            for s_ in (-t, t):
                elems.append(L(p + n * s_, q + n * s_, INK, .12, 'A-DOOR', True))
        else:
            hinge_at_start = o.get('hinge', 'start') == 'start'
            hj = (p if hinge_at_start else q) + n * t; oj = (q if hinge_at_start else p) + n * t
            r = o['width']; along = (oj - hj) / r
            elems.append(L(hj, hj + n * r, INK, .28, 'A-DOOR'))
            arc = [hj + r * (along * math.cos(th) + n * math.sin(th)) for th in np.linspace(0, math.pi / 2, 18)]
            elems.append(P(arc, 'none', LIGHT, .13, 'A-DOOR', False))
        c = m - n * (t + 250)
        elems.append(T(c[0], c[1] - 60, tags[o['id']], 150, 'A-TAGS'))
    # Stairs: treads, the walking line with its arrow, UP/DN and the riser note.
    for st in [s for s in b['stairs'] if s['floor'] == floor]:
        if st.get('shape')=='three-flight-c-stair' and st.get('flights') and 'bounds' in st['flights'][0]:
            for part in st['flights']:
                a,c,d,e=part['bounds']
                elems.append(P([(a,c),(d,c),(d,e),(a,e)],'none',INK,.15,'A-STAIR'))
            continue
        x, y = st['x'], st['y']; fw = st['flight_width']; land = st['landing_mm']; tr = st['tread_mm']
        if st.get('shape')=='quarter-turn':
            from .stair_geometry import quarter_parts, quarter_path
            for part in quarter_parts(st):
                a,c,_,d,e,_=part['bounds'];elems.append(P([(a,c),(d,c),(d,e),(a,e)],'none',INK,.14,'A-STAIR'))
            walk=quarter_path(st)
            if st.get('to_floor') is None:walk=list(reversed(walk))
            elems.append(P(walk,'none',INK,.2,'A-STAIR',False))
            end=np.array(walk[-1]);u=(end-np.array(walk[-2]));u=u/np.linalg.norm(u);normal=np.array([-u[1],u[0]])
            elems.append(P([end,end-u*140+normal*70,end-u*140-normal*70],INK,INK,.15,'A-STAIR'))
            elems.append(T(walk[0][0],walk[0][1]-170,'DN' if st.get('to_floor') is None else 'UP',140,'A-STAIR'))
            elems.append(T(x+fw/2,y+(st['depth']-land)/2,f'{st["riser_count"]}R / L STAIR',120,'A-STAIR'))
            continue
        start_land = 0 if st.get('open_arrival') else land
        from .stair_geometry import point as stair_point
        pt=lambda p: stair_point(st,p)
        for k in range(st['riser_count']//2):
            yy = y + start_land + k * tr
            elems.append(L(pt((x, yy)), pt((x + fw, yy)), INK, .14, 'A-STAIR'))
            elems.append(L(pt((x + fw + st['well'], yy)), pt((x + st['width'], yy)), INK, .14, 'A-STAIR'))
        top = y + start_land + (st['riser_count']//2-1) * tr
        walk_start = y + start_land + (150 if st.get('open_arrival') else 0)
        walk = [(x + fw / 2, walk_start), (x + fw / 2, top + land / 2), (x + st['width'] - fw / 2, top + land / 2), (x + st['width'] - fw / 2, walk_start)]
        elems.append(P([pt(p) for p in walk], 'none', INK, .2, 'A-STAIR', False))
        ex, ey = walk[-1]
        elems.append(P([pt(p) for p in [(ex - 70, ey + 140), (ex + 70, ey + 140), (ex, ey)]], INK, INK, .15, 'A-STAIR'))
        elems.append(T(*pt((x + fw / 2, y + start_land - 260)), 'UP TO ROOF' if st.get('roof_access') else 'UP' if floor == 0 else 'UP / DN', 170, 'A-STAIR'))
        elems.append(T(*pt((x + st['width'] / 2, top + land / 2 if st.get('open_arrival') else y + 300)), f'{st["riser_count"]}R @ {st["riser_mm"]:.0f} / T {tr:.0f}', 140, 'A-STAIR'))
    if floor==0:
        for step in b.get('entrance_steps',[]):elems.append(P(step['polygon'],'none',INK,.15,'A-STAIR'))
    for item in scene['furniture']:
        if item['floor'] == floor:
            elems.append(P(np.array(item['footprint']) * 1000, 'none', '#a3aaa1', .12, 'A-FURN'))
    exterior = b.get('exterior', {})
    for assembly in exterior.get('assemblies', []):
        if assembly.get('floor_id') not in (floor, -1) or assembly['geometry'].get('kind') == 'stair_tower':
            continue
        x0, y0, x1, y1 = assembly['geometry']['bounds_mm']
        elems.append(P([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 'none', ACCENT, .25, 'A-EXT'))
        if y1 <= 10:
            # Deep assemblies (porch, deck) carry their name inside; shallow ones (a feature wall) just below.
            elems.append(T((x0 + x1) / 2, y0 + 120 if y1 - y0 > 600 else y0 - 250, assembly['role'].replace('_', ' ').upper(), 130, 'A-EXT'))
    # Room tags: name, clear principal size and clear area, at the room's pole of inaccessibility.
    for room in spaces:
        clear = Polygon(room['clear'],room.get('holes',[]))
        if clear.is_empty:
            continue
        spot = polylabel(clear, 10)
        rx0, ry0, rx1, ry1 = principal_rect(clear)
        small = min(rx1 - rx0, ry1 - ry0) < 1700
        name = room['name'].upper()
        s1 = 170 if small else 220; s2 = 130 if small else 150
        elems.append(T(spot.x, spot.y + s1 * .35, name, s1))
        if room['kind'] not in ('stair', 'hall'):
            star = '' if clear.buffer(1).covers(box(*clear.bounds)) else '*'
            elems.append(T(spot.x, spot.y - s2 * 1.35, f'{(rx1 - rx0) / 1000:.2f} x {(ry1 - ry0) / 1000:.2f}{star}', s2))
            elems.append(T(spot.x, spot.y - s2 * 2.75, f'{room["area_m2"]:.1f} m²', s2))
    elems.extend(rev8_over)
    # Three dimension chains on each side: openings, walls, overall.
    ext = unary_union([fp] + [box(*a['geometry']['bounds_mm']) for a in exterior.get('assemblies', [])
                              if a.get('floor_id') in (floor, -1) and a['geometry'].get('kind') != 'stair_tower'])
    ex0, ey0, ex1, ey1 = ext.bounds
    walls = [w for w in b['walls'] if w['floor'] == floor]
    for side in ('S', 'N', 'W', 'E'):
        horiz = side in ('S', 'N')
        span = W if horiz else D
        k = 0 if horiz else 1

        def on_side(pt):
            return (pt[1] < 240) if side == 'S' else (pt[1] > D - 240) if side == 'N' else (pt[0] < 240) if side == 'W' else (pt[0] > W - 240)
        opening_pts, wall_pts = {0., float(span)}, {0., float(span)}
        for o in b['openings']:
            if o['floor'] != floor:
                continue
            w = hosts[o['wall_id']]
            if not w['external'] or not (on_side(w['a']) and on_side(w['b'])):
                continue
            _, _, _, u, _, p, q = frame(w, o)
            opening_pts.update((float(p[k]), float(q[k])))
        for w in walls:
            if w['external']:
                continue
            (ax, ay), (bx, by) = w['a'], w['b']
            if horiz and abs(ax - bx) < 1 and ((side == 'S' and min(ay, by) < 5) or (side == 'N' and max(ay, by) > D - 5)):
                wall_pts.add(float(ax))
            if not horiz and abs(ay - by) < 1 and ((side == 'W' and min(ax, bx) < 5) or (side == 'E' and max(ax, bx) > W - 5)):
                wall_pts.add(float(ay))
        base = {'S': ey0, 'N': ey1, 'W': ex0, 'E': ex1}[side]
        sign = -1 if side in ('S', 'W') else 1
        # Figures sit on the far side of each line, leaving the band next to the wall to the opening tags.
        away = 1 if side in ('N', 'W') else -1
        chains = [sorted(opening_pts), sorted(wall_pts), [0., float(span)]]
        level_ = 0
        for ci, pts in enumerate(chains):
            if len(pts) <= 2 and ci < 2:
                continue
            dedup = []
            for x in pts:
                if not dedup or x - dedup[-1] > 20:
                    dedup.append(x)
            at = base + sign * (550 + 450 * level_)
            lifted = False
            for x1_, x2_ in zip(dedup, dedup[1:]):
                # A figure wider than its segment moves one row out; consecutive short segments alternate rows.
                lifted = (x2_ - x1_) < len(str(round(x2_ - x1_))) * 110 + 140 and not lifted
                if horiz:
                    y_obj = 0 if side == 'S' else D
                    elems.append(DIM((x1_, y_obj), (x2_, y_obj), 'x', at, away, stagger=lifted))
                else:
                    x_obj = 0 if side == 'W' else W
                    elems.append(DIM((x_obj, x1_), (x_obj, x2_), 'y', at, away, stagger=lifted))
            level_ += 1
    # Coordination grid: light axes through the plan and bubbles beyond the dimension chains (top and left).
    gx, gy = grid_axes(b, floor)
    top = ey1 + 550 + 450 * 2 + 650; left = ex0 - 550 - 450 * 2 - 650
    for i, x in enumerate(gx):
        elems.append(L((x, ey0 - 200), (x, top - 300), LIGHT, .1, 'A-GRID', True))
        elems.append(C(x, top, 300, INK, .15, 'A-GRID')); elems.append(T(x, top - 90, axis_label(i), 220, 'A-GRID'))
    for j, y in enumerate(gy):
        elems.append(L((left + 300, y), (ex1 + 200, y), LIGHT, .1, 'A-GRID', True))
        elems.append(C(left, y, 300, INK, .15, 'A-GRID')); elems.append(T(left, y - 90, str(j + 1), 220, 'A-GRID'))
    # Finished floor level near the entrance (ground) or in the lounge (upper floor).
    entry = next((o for o in b['openings'] if o['kind'] == 'entry'), None)
    lvl = plinth + floor * H
    target = next((s for s in spaces if s['kind'] in ('living', 'drawing-room', 'family')), spaces[0])
    lp = polylabel(Polygon(target['clear']), 10)
    lx0, ly0, lx1, ly1 = Polygon(target['clear']).bounds
    level(elems, min(lx1 - 1400, lp.x + 1300), max(ly0 + 450, lp.y - 900), f'FFL {("+" if lvl else "±")}{lvl / 1000:.3f}')
    # Section A-A (see section_cut): a bubble beyond the dimension chains at each end - below the overall chain, and
    # on the row of the grid bubbles at the top (one row higher when an axis is close) - with a thick end stroke,
    # tied back to the building face by a light cut line.
    cut = section_cut(b)
    near = any(abs(cut - x) < 1000 for x in gx)
    for cy, sgn in ((ey0 - 2150, -1), (top + (650 if near else 0), 1)):
        stroke = cy - sgn * 580
        elems.append(L((cut, ey0 - 100 if sgn < 0 else ey1 + 100), (cut, stroke), INK, .1, 'A-SECT', True))
        elems.append(L((cut, stroke), (cut, cy - sgn * 280), INK, .45, 'A-SECT'))
        elems.append(C(cut, cy, 280, INK, .2, 'A-SECT')); elems.append(T(cut, cy - 85, 'A', 220, 'A-SECT'))
        elems.append(P([(cut - 280, cy + sgn * 120), (cut - 620, cy), (cut - 280, cy - sgn * 120)], INK, INK, .1, 'A-SECT'))
    north_point(elems, left - 1500, top - 700, v['road_bearing_deg'])
    if floor==0 and b.get('siteBoundary'):
        elems.extend(enclosure_elements(b['siteBoundary'], b.get('vehicleRamp')))
    return elems, bounds_of(elems)


# ---------------------------------------------------------------------------------------------- site plan
def enclosure_elements(boundary, ramp=None):
    items=[P(run['polygon'], '#b9b2a5', INK, .22, 'A-SITE') for run in boundary['runs']]
    if ramp:
        x,X,y,Y=(ramp[k] for k in ('x0','x1','y0','y1'))
        items.append(P([(x,y),(X,y),(X,Y),(x,Y)],'none',ACCENT,.22,'A-SITE'))
        mid=(x+X)/2
        items.append(L((mid,y+80),(mid,Y-160),ACCENT,.3,'A-SITE'))
        items.append(P([(mid-70,Y-330),(mid,Y-160),(mid+70,Y-330)],'none',ACCENT,.25,'A-SITE',closed=False))
        items.append(T(mid,Y+300,'UP 1:10',115,'A-SITE'))
    for gate in boundary['gates']:
        lo,hi=gate['x0_mm'],gate['x1_mm']
        items.append(L((lo,185),(hi,185),ACCENT,.45,'A-GATE'))
        if gate['operation']=='sliding':
            items.append(L((hi,210),(hi+hi-lo,210),ACCENT,.18,'A-GATE',True))
        else:
            for pivot,direction in ((lo,1),(hi,-1)):
                radius=(hi-lo)/2
                arc=[(pivot+direction*radius*math.cos(t),185+radius*math.sin(t)) for t in np.linspace(0,math.pi/2,14)]
                items.append(P(arc,'none',ACCENT,.18,'A-GATE',closed=False))
                items.append(L((pivot,185),(pivot,185+radius),ACCENT,.22,'A-GATE'))
    return items


def site_elements(b, scene):
    v = b['brief']; fp = Polygon(b['footprint']); plot = Polygon(b['plot']); xmin, ymin, xmax, ymax = plot.bounds; W, D = fp.bounds[2:]
    elems = [P(list(plot.exterior.coords), '#f0f3eb', INK, .35, 'A-SITE'), P(b['footprint'], '#dadfd6', INK, .4)]
    if b.get('planning', {}).get('colonyContext') == 'tirumala-colony':
        # East 9.0 m road (at local -Y) + Basketball Court Enclosure beyond
        elems.extend([
            P([(xmin - 1200, ymin - 9200), (xmax + 12200, ymin - 9200), (xmax + 12200, ymin - 200), (xmin - 1200, ymin - 200)], '#e8e8e2', LIGHT, .2, 'A-SITE'),
            T((xmin + xmax) / 2, ymin - 4600, 'EAST ROAD — 9.0 m ROW (PRINCIPAL ARRIVAL / 40 FT FRONTAGE)', 210),
            P([(xmin - 600, ymin - 13400), (xmax + 4000, ymin - 13400), (xmax + 4000, ymin - 9400), (xmin - 600, ymin - 9400)], '#dce5d8', '#6e8068', .22, 'A-SITE'),
            T((xmin + xmax) / 2 + 1200, ymin - 11400, 'BASKETBALL-COURT ENCLOSURE & SCREENING PLANTING (E-01 / N-04)', 180),
            # North 12.0 m road (at local +X) + Opposite Colony Garden & N-01 House beyond
            P([(xmax + 200, ymin - 9200), (xmax + 12200, ymin - 9200), (xmax + 12200, ymax + 1200), (xmax + 200, ymax + 1200)], '#e8e8e2', LIGHT, .2, 'A-SITE'),
            T(xmax + 6200, (ymin + ymax) / 2, 'NORTH ROAD — 12.0 m ROW (50 FT NORTH BOUNDARY)', 210),
            P([(xmax + 12400, ymin - 1000), (xmax + 18200, ymin - 1000), (xmax + 18200, ymax + 800), (xmax + 12400, ymax + 800)], '#d6e3cb', '#6e8068', .22, 'A-SITE'),
            T(xmax + 15300, (ymin + ymax) / 2, 'OPPOSITE NORTH COLONY GARDEN, PERGOLA & N-01 HOUSE BEYOND', 175),
            # Two NW electrical feeder cabinets outside plot near NW corner (N-02)
            P([(xmax + 280, ymax - 1650), (xmax + 780, ymax - 1650), (xmax + 780, ymax - 850), (xmax + 280, ymax - 850)], '#dcd8ce', INK, .2, 'A-SITE'),
            P([(xmax + 260, ymax - 620), (xmax + 820, ymax - 620), (xmax + 820, ymax + 420), (xmax + 260, ymax + 420)], '#d6d2c6', INK, .2, 'A-SITE'),
            T(xmax + 2650, ymax - 450, '2x NW FEEDER CABINETS (N-02)', 155),
            # North streetlight pole between NE and NW corners (N-03)
            C(xmax + 550, ymax - 4350, 180, INK, .25, 'A-SITE'),
            T(xmax + 2550, ymax - 4350, 'STREETLIGHT POLE (N-03)', 155),
            # Plot E-W midpoint line (X_geo = 7.620 m -> y_local = 7620 mm in Rev 8)
            L((xmin, 7620 if _tirumala_rev8_meta(b) else 5780), (xmax, 7620 if _tirumala_rev8_meta(b) else 5780), ACCENT, .18, 'A-GRID', True),
            T(xmax - 2800, (7620 if _tirumala_rev8_meta(b) else 5780) - 260, 'PLOT E-W MIDPOINT (X_geo = 7.620 m / 25 FT)', 145, 'A-GRID'),
            # Explicit Geographic Corner Coordinates
            T(xmin + 1450, ymax + 420, 'SW ORIGIN (0.000, 0.000) m', 145, 'A-SITE'),
            T(xmin + 1450, ymin - 420, 'SE (15.240, 0.000) m', 145, 'A-SITE'),
            T(xmax - 1450, ymax + 420, 'NW (0.000, 12.192) m', 145, 'A-SITE'),
            T(xmax - 1450, ymin - 420, 'NE CORNER (15.240, 12.192) m', 145, 'A-SITE'),
        ])
        if _tirumala_rev8_meta(b):
            u_site, o_site = _tirumala_rev8_plan_underlays(b, 0)
            elems.extend(u_site[1:] + o_site[2:])
    else:
        elems.extend([P([(xmin - 1000, ymin - 4500), (xmax + 1000, ymin - 4500), (xmax + 1000, ymin - 200), (xmin - 1000, ymin - 200)], '#e8e8e2', LIGHT, .2, 'A-SITE'),
                      T((xmin + xmax) / 2, ymin - 2600, 'ROAD / WIDTH TO BE SURVEYED', 230)])
    exterior = b.get('exterior', {})
    site_colors = {'path': '#e5e0d3', 'planting_bed': '#b9ad91', 'court': '#dcd6c8', 'lawn': '#d4e0c6', 'pebble_bed': '#d6d3cb'}
    for feature in exterior.get('landscape', {}).get('features', []):
        if 'polygon' in feature:
            elems.append(P(feature['polygon'], site_colors.get(feature['kind'], '#d8dfd1'), '#819076', .18, 'A-LAND'))
        elif feature['kind'] in ('tree', 'shrub'):
            x, y = feature['position_mm']; r = feature.get('mature_canopy_radius_mm', 350 if feature['kind'] == 'shrub' else 900)
            elems.append(P(list(Point(x, y).buffer(r).exterior.coords), '#c8d4ba', '#819076', .18, 'A-LAND'))
    for x, y, txt in [(W / 2, -v['front_mm'] / 2, 'FRONT SETBACK'), (-v['left_mm'] / 2, D / 2, ''), (W + (xmax - W) / 2, D / 2, ''), (W / 2, D + (ymax - D) / 2, 'REAR YARD')]:
        if txt:
            elems.append(T(x, y, txt, 170))
    boundary = exterior.get('landscape', {}).get('boundary', {})
    if b.get('siteBoundary'):
        elems.extend(enclosure_elements(b['siteBoundary'], b.get('vehicleRamp')))
        for gate in b['siteBoundary']['gates']:
            label='PEDESTRIAN / SLIDING' if gate['kind']=='pedestrian' else 'CAR / INWARD PAIR'
            elems.append(T((gate['x0_mm']+gate['x1_mm'])/2,-1050,label,115,'A-GATE'))
        elems.append(T(xmax+850,(ymin+ymax)/2,'NORTH ROAD',160,'A-SITE'))
    elif boundary:
        for x0, x1, gate in gate_openings(boundary):
            if gate.get('operation') == 'sliding':
                elems.append(L((x0, ymin + 170), (x1, ymin + 170), ACCENT, .45, 'A-GATE'))
                run = min(x1 - x0, gate.get('park_run_mm', x1 - x0)); t0, t1 = ((x0 - run, x0) if gate.get('park') == 'left' else (x1, x1 + run))
                elems.extend([L((t0, ymin + 230), (t1, ymin + 230), ACCENT, .18, 'A-GATE', True), T((x0 + x1) / 2, ymin + 700, 'SLIDING GATE', 140, 'A-GATE')])
            else:
                hx = x1 if gate.get('hinge') == 'right' else x0; r = x1 - x0; sgn = -1 if gate.get('hinge') == 'right' else 1
                elems.append(L((hx, ymin + 150), (hx, ymin + 150 + r), ACCENT, .35, 'A-GATE'))
                arc = [(hx + sgn * r * math.cos(t), ymin + 150 + r * math.sin(t)) for t in np.linspace(0, math.pi / 2, 10)]
                elems.append(P(arc, 'none', ACCENT, .15, 'A-GATE', closed=False))
        pier = boundary.get('letterbox_pier')
        if pier:
            elems.append(P([(pier['x0_mm'], ymin - 60), (pier['x1_mm'], ymin - 60), (pier['x1_mm'], ymin + 210), (pier['x0_mm'], ymin + 210)], '#8f8a80', INK, .2, 'A-SITE'))
    # Plot size, the building's setbacks from each boundary and the building's size.
    elems.append(DIM((xmin, ymax), (xmax, ymax), 'x', ymax + 900))
    elems.append(DIM((xmax, ymin), (xmax, ymax), 'y', xmax + 1500, -1))
    elems.append(DIM((0, 0), (W, 0), 'x', ymin - 600, -1))
    elems.append(DIM((0, ymin), (0, 0), 'y', -max(600, (0 - xmin) / 2), 1))
    elems.append(DIM((W / 2, D), (W / 2, ymax), 'y', W / 2 + 350, -1))
    elems.append(DIM((xmin, D / 2), (0, D / 2), 'x', D / 2 + 320))
    elems.append(DIM((W, D / 2), (xmax, D / 2), 'x', D / 2 + 320))
    elems.append(DIM((W, 0), (W, D), 'y', xmax + 700, -1))
    plinth = v['plinth_mm']
    level(elems, xmin + 400, ymin - 1300, 'ROAD -0.150 (assumed)')
    level(elems, xmax - 2600, ymin + 900, 'NGL ±0.000')
    level(elems, W / 2 + 900, D / 2 - 600, f'PL / FFL +{plinth / 1000:.3f}')
    north_point(elems, xmin + 900, ymax - 1100, v['road_bearing_deg'])
    return elems, bounds_of(elems)


# ---------------------------------------------------------------------------------------------- elevations and section
def level_scale(elems, x, levels):
    for z, text in levels:
        elems.append(L((x - 500, z), (x + 200, z), LIGHT, .12, 'A-LEVL', True))
        level(elems, x + 450, z, text, size=150)


def building_levels(b, top_extra=0):
    v = b['brief']; H = v['floor_height_mm']; plinth = v['plinth_mm']; n = b['storeys']
    marks = [(-plinth, 'NGL ±0.000'), (0, f'FFL +{plinth / 1000:.3f}')]
    marks += [(f * H, f'FFL +{(plinth + f * H) / 1000:.3f}') for f in range(1, n)]
    top = n * H
    if b.get('planning', {}).get('g2Revision'):
        r = next(r for r in b['roofs'] if r['floor'] == n - 1)
        top = r['elevation'] + r['thickness']
    marks.append((top, f'TOS +{(plinth + top) / 1000:.3f}'))
    if top_extra:
        marks.append((top + top_extra, f'TOP +{(plinth + top + top_extra) / 1000:.3f}'))
    return marks


def elevation_elements(b, direction, scene=None):
    from .rooftop import with_rooftop_objects
    b=with_rooftop_objects(b)
    v = b['brief']; W, D = Polygon(b['footprint']).bounds[2:]; H = v['floor_height_mm']; top = b['storeys'] * H; elems = []
    if b.get('planning', {}).get('g2Revision'):top = building_levels(b)[-1][0]
    horizontal = direction in ('Front', 'Rear'); span = W if horizontal else D
    if b.get('planning',{}).get('custom'):
        from .plan_geometry import plate,roof
        axis=0 if horizontal else 1
        for w in b['walls']:
            bb=Polygon(w['polygon']).bounds;a,c=bb[axis],bb[axis+2];z=w['floor']*H
            elems.append(P([(a,z),(c,z),(c,z+w['height']),(a,z+w['height'])],'#f2f0e7',INK,.2))
        for f in range(b['storeys']):
            slab_depth = 180 if b.get('planning', {}).get('g2Revision') else 150
            roof_top = (f+1)*H
            if b.get('planning', {}).get('g2Revision'):
                r = next(r for r in b['roofs'] if r['floor']==f)
                roof_top = r['elevation'] + (r['thickness'] if f==b['storeys']-1 else 0)
            for geom,z in ((plate(b,f),f*H),(roof(b,f),roof_top)):
                for part in get_parts(geom):
                    if part.geom_type!='Polygon':continue
                    bb=part.bounds;a,c=bb[axis],bb[axis+2]
                    elems.append(P([(a,z-slab_depth),(c,z-slab_depth),(c,z),(a,z)],'#dadbd4',INK,.25))
    else:
        elems.append(P([(0, -v['plinth_mm']), (span, -v['plinth_mm']), (span, top + 600), (0, top + 600)], '#f2f0e7', INK, .25))
    elems.append(L((-1500, -v['plinth_mm']), (span + 1500, -v['plinth_mm']), INK, .5, 'A-SITE'))
    for f in ([] if b.get('planning',{}).get('custom') else range(b['storeys'] + 1)):
        elems.append(L((0, f * H), (span, f * H), INK, .35))
    if b.get('rooftop'):
        for core in b['rooftop']['cores']:
            x0,y0,x1,y1=core['bounds'];a,c=(x0,x1) if horizontal else (y0,y1);z1=top+core['height']
            elems.append(P([(a,top),(c,top),(c,z1),(a,z1)],'#e3ddd2',ACCENT,.3,'A-EXT'))
            elems.append(T((a+c)/2,z1+130,'ROOF STAIR ACCESS',130,'A-EXT'))
    hosts = {w['id']: w for w in b['walls']}
    tags, _ = opening_types(b)
    for o in b['openings']:
        w = hosts[o['wall_id']]
        custom=b.get('planning',{}).get('custom')
        if not w['external'] and not (custom and any(space['kind'] in ('terrace','balcony','veranda','courtyard','drying-yard','outer-lobby') and space['id'] in w['rooms'] for space in b['spaces'])):
            continue
        selected = (direction == 'Front' and max(w['a'][1], w['b'][1]) < 240) or (direction == 'Rear' and min(w['a'][1], w['b'][1]) > D - 240) or \
                   (direction == 'Left' and max(w['a'][0], w['b'][0]) < 240) or (direction == 'Right' and min(w['a'][0], w['b'][0]) > W - 240)
        if custom or (b.get('rooftop') and w['floor']==b['storeys']):
            axis=0 if horizontal else 1
            selected=abs(w['a'][1-axis]-w['b'][1-axis])<.01
            toward={'Front':(0,-1),'Rear':(0,1),'Left':(-1,0),'Right':(1,0)}[direction]
            mid=(np.array(w['a'])+w['b'])/2+np.array(toward)*(w['thickness']/2+1)
            if any(space.get('enclosed',True) and space['id'] in w['rooms'] and Polygon(space['clear']).covers(Point(mid)) for space in b['spaces']):selected=False
        if not selected:
            continue
        u = (np.array(w['b']) - w['a']) / math.dist(w['a'], w['b']); p = np.array(w['a']) + u * o['offset']; q = p + u * o['width']
        axis = 0 if horizontal else 1; a = min(p[axis], q[axis]); c = max(p[axis], q[axis]); z = o['floor'] * H + o['sill']
        elems.append(P([(a, z), (c, z), (c, z + o['height']), (a, z + o['height'])], '#dfe8e7', INK, .25, 'A-WIND'))
        if o['width'] > 1200:
            elems.append(L(((a + c) / 2, z), ((a + c) / 2, z + o['height']), INK, .15, 'A-WIND'))
        elems.append(T((a + c) / 2, z + o['height'] + 90, tags[o['id']], 130, 'A-TAGS'))
    for assembly in b.get('exterior', {}).get('assemblies', []):
        geo = assembly['geometry']; x0, y0, x1, y1 = geo['bounds_mm']; kind = geo.get('kind'); floor = assembly.get('floor_id', 0)
        if kind == 'stair_tower':
            if b.get('rooftop'):continue
            a, c = (x0, x1) if horizontal else (y0, y1); z1 = top + geo.get('height_mm', 2700)
            elems.append(P([(a, top), (c, top), (c, z1), (a, z1)], '#e3ddd2', ACCENT, .3, 'A-EXT'))
            elems.append(T((a + c) / 2, z1 + 130, 'STAIR TOWER', 130, 'A-EXT'))
            continue
        selected = (direction == 'Front' and y1 <= 300) or (direction == 'Rear' and y0 >= D - 300) or (direction == 'Left' and x1 <= 300) or (direction == 'Right' and x1 >= W - 300 and x0 <= W + 300)
        if not selected:
            continue
        a, c = (x0, x1) if horizontal else (y0, y1); z0 = floor * H
        if kind in ('porch', 'side_verandah'):
            z0 = geo.get('platform_z_mm', -120) + 0.; z1 = geo.get('canopy_z_mm', 2700) + 200
        elif kind == 'balcony':
            z0 = floor * H - 120; z1 = z0 + geo.get('rail_height_mm', 1100) + 120
        else:
            z1 = z0 + geo.get('height_mm', top * 1000 - 400)
        elems.append(P([(a, z0), (c, z0), (c, z1), (a, z1)], 'none', ACCENT, .3, 'A-EXT'))
        elems.append(T((a + c) / 2, z1 + 130, assembly['role'].replace('_', ' ').upper(), 130, 'A-EXT'))
    elems.append(DIM((0, -v['plinth_mm']), (span, -v['plinth_mm']), 'x', -v['plinth_mm'] - 900, -1))
    elems.append(DIM((span, -v['plinth_mm']), (span, top), 'y', span + 900, -1))
    for f in range(b['storeys']):
        elems.append(DIM((0, f * H), (0, top if f == b['storeys']-1 else (f + 1) * H), 'y', -700, 1))
    level_scale(elems, span + 2200, building_levels(b))
    return elems, bounds_of(elems)


def section_cut(b):
    """The plan x (mm) of section A-A: along the up flight of the stair, or through the living room of a single-storey
    house, kept clear of the overall dimension figure at mid-width."""
    if b.get('planning', {}).get('tirumala7'):
        return 3505  # Cut through the 12' x 5' double-height void & dining shaft (y_ft = 28.5)
    W = Polygon(b['footprint']).bounds[2]
    if b['stairs'] and (b['storeys'] > 1 or b.get('rooftop')):
        st = b['stairs'][0]
        return round(st['x'] + st['flight_width'] / 2)
    living = next((s for s in b['spaces'] if s['floor'] == 0 and s['kind'] == 'living'), None)
    x = Polygon(living['clear']).centroid.x if living else W / 2
    if abs(x - W / 2) < 700:
        x = W / 2 + (700 if x >= W / 2 else -700)
    return round(x)


def _tirumala_living_section_elements(b, scene):
    """South-to-North (x = 0..12192 mm) projected stair, upper landing, double-height living (~23 ft clear),
    rooflight, and care suite (~11 ft clear) section, combined with 3D mesh-plane intersections."""
    import trimesh
    ft = lambda f: round(f * 304.8)
    elems = []
    # Plot & ground datum
    elems.append(L((-800, -300), (13000, -300), INK, .45, 'A-SITE'))
    elems.append(P([(ft(0.5), -300), (ft(39.5), -300), (ft(39.5), 0), (ft(0.5), 0)], '#e7e2d4', INK, .25, 'A-SECT'))
    # Stair & hall zone (x = 0.5..16.25 ft, z = 0..7010 mm)
    elems.append(P([(ft(0.5), 0), (ft(16.25), 0), (ft(16.25), ft(23)), (ft(0.5), ft(23))], '#fafaf5', INK, .22, 'A-SECT'))
    # Double-height living void (x = 16.25..23 ft, z = 0..7010 mm, ~23 ft clear)
    elems.append(P([(ft(16.25), 0), (ft(23), 0), (ft(23), ft(23)), (ft(16.25), ft(23))], '#f4f6f1', INK, .25, 'A-SECT'))
    # Rooflight shaft & glazing at x = 18.5..22.5 ft, z = 23 ft (7010 mm)
    elems.append(P([(ft(18.5), ft(2)), (ft(22.5), ft(2)), (ft(22.5), ft(22.8)), (ft(18.5), ft(22.8))], '#eef5f4', 'none', .1, 'A-WIND'))
    elems.append(L((ft(18.5), ft(23)), (ft(22.5), ft(23)), GLASS, .45, 'A-WIND'))
    rl = Polygon(b['planning']['tirumalaMeta']['canonicalZones']['rooflight']).bounds
    light_size = f'{(rl[2]-rl[0])/304.8:.0f} x {(rl[3]-rl[1])/304.8:.0f}'
    elems.append(T(ft(20.5), ft(23.8), f'ROOFLIGHT ({light_size} FT)', 155, 'A-WIND'))
    # Care suite (x = 23.5..36 ft, z = 0..3353 mm (~11 ft clear), upper slab z = 3353..3658 mm)
    elems.append(P([(ft(23.5), 0), (ft(36), 0), (ft(36), ft(11)), (ft(23.5), ft(11))], '#f6f3ea', INK, .25, 'A-SECT'))
    elems.append(P([(ft(23.5), ft(11)), (ft(36), ft(11)), (ft(36), ft(12)), (ft(23.5), ft(12))], '#dadbd4', INK, .25, 'A-SECT'))
    elems.append(P([(ft(23.5), ft(12)), (ft(36), ft(12)), (ft(36), ft(23)), (ft(23.5), ft(23))], '#fbfbf8', INK, .2, 'A-SECT'))
    # Full-height North glazing on Care (x = 36 ft) & Hall-side sliding glass (x = 23.25 ft)
    elems.append(L((ft(35.92), 0), (ft(35.92), ft(11)), GLASS, .35, 'A-WIND'))
    elems.append(L((ft(36.08), 0), (ft(36.08), ft(11)), GLASS, .35, 'A-WIND'))
    elems.append(L((ft(23.25), 0), (ft(23.25), ft(11)), GLASS, .32, 'A-DOOR', True))
    # 3 ft clear North garden passage (x = 36.5..39.5 ft)
    elems.append(P([(ft(36.5), 0), (ft(39.5), 0), (ft(39.5), ft(1.2)), (ft(36.5), ft(1.2))], '#dce8cf', '#6f8762', .2, 'A-LAND'))
    # Upper stair arrival slab (x = 12.5..16 ft, z = 11..12 ft) & guard/wall at x = 16 ft stopping outside void
    elems.append(P([(ft(12.5), ft(11)), (ft(16), ft(11)), (ft(16), ft(12)), (ft(12.5), ft(12))], '#dadbd4', INK, .28, 'A-STAIR'))
    elems.append(L((ft(16), ft(12)), (ft(16), ft(15.5)), INK, .3, 'A-STAIR'))
    elems.append(L((ft(12.5), ft(15.5)), (ft(16), ft(15.5)), INK, .22, 'A-STAIR'))
    # South turning landing (x = 0.5..4 ft, z = 6 ft = 1829 mm) & parallel flights (20 risers @ 182.88 mm, 9 treads @ 287.87 mm)
    elems.append(P([(ft(0.5), ft(5.65)), (ft(4), ft(5.65)), (ft(4), ft(6.0)), (ft(0.5), ft(6.0))], '#dadbd4', INK, .28, 'A-STAIR'))
    dx = ft(8.5) / 9.0
    dz = ft(6.0) / 10.0
    # First flight climbing SOUTH (x = 12.5 -> 4 ft, z = 0 -> 6 ft)
    elems.append(L((ft(12.5), 0), (ft(12.5), dz), INK, .22, 'A-STAIR'))
    for i in range(9):
        ax = ft(12.5) - i * dx; bx = ax - dx; z = (i + 1) * dz
        elems.append(L((ax, z), (bx, z), INK, .22, 'A-STAIR'))
        elems.append(L((bx, z), (bx, z + dz), INK, .22, 'A-STAIR'))
    # Return flight climbing NORTH (x = 4 -> 12.5 ft, z = 6 -> 12 ft)
    elems.append(L((ft(4), ft(6)), (ft(4), ft(6) + dz), INK, .22, 'A-STAIR'))
    for i in range(9):
        cx = ft(4) + i * dx; ex = cx + dx; zz = ft(6) + (i + 1) * dz
        elems.append(L((cx, zz), (ex, zz), INK, .22, 'A-STAIR'))
        elems.append(L((ex, zz), (ex, zz + dz), INK, .22, 'A-STAIR'))
    # Care bed (x = 26.25..33.25 ft, head South at 26.25 ft, feet North at 33.25 ft) + North sightline ray
    elems.append(P([(ft(26.25), 0), (ft(33.25), 0), (ft(33.25), ft(2.0)), (ft(26.25), ft(2.0))], '#f2ece0', INK, .2, 'A-FURN'))
    elems.append(P([(ft(26.5), ft(2.0)), (ft(27.6), ft(2.0)), (ft(27.6), ft(2.5)), (ft(26.5), ft(2.5))], '#e5dec9', INK, .18, 'A-FURN'))
    elems.append(L((ft(27.2), ft(2.7)), (ft(39.0), ft(2.7)), GLASS, .22, 'A-ANNO', True))
    # Labels & dimensions
    elems.append(T(ft(7.5), ft(18.5), 'COMPACT STAIR (12 x 7.5 FT): SOUTH <- UP / RETURN -> NORTH', 140, 'A-STAIR'))
    elems.append(T(ft(7.5), ft(17.1), '20 RISERS @ 182.9 mm / 9 TREADS PER FLIGHT @ 287.9 mm', 120, 'A-STAIR'))
    elems.append(T(ft(14.25), ft(16.1), 'UPPER LANDING (OUTSIDE VOID)', 120, 'A-STAIR'))
    elems.append(T(ft(19.6), ft(16.8), 'DOUBLE-HEIGHT LIVING VOID', 155, 'A-ANNO'))
    elems.append(T(ft(19.6), ft(15.0), '~23 FT (7010 mm) CLEAR', 145, 'A-ANNO'))
    elems.append(T(ft(19.6), ft(7.5), 'FAMILY / LIVING HALL (+0.300 m)', 135, 'A-ANNO'))
    elems.append(T(ft(29.7), ft(6.2), 'CARE SUITE (~11 FT / 3353 mm CLEAR)', 140, 'A-ANNO'))
    elems.append(T(ft(29.7), ft(3.6), 'BED 7x3.5 FT (HEAD SOUTH -> FEET NORTH)', 120, 'A-FURN'))
    elems.append(T(ft(29.7), ft(17.5), 'UPPER FLOOR ACCOMMODATION', 135, 'A-ANNO'))
    elems.append(T(ft(38.0), ft(3.5), '3 FT NORTH GARDEN', 115, 'A-LAND'))
    elems.append(DIM((ft(21.5), 0), (ft(21.5), ft(23)), 'y', ft(21.5), -1))
    elems.append(DIM((ft(34.5), 0), (ft(34.5), ft(11)), 'y', ft(34.5), -1))
    elems.append(DIM((ft(0.5), -300), (ft(39.5), -300), 'x', -1100, -1))
    level_scale(elems, ft(40) + 1800, [
        (-300, 'CAR BAY / NGL ±0.000'),
        (0, 'HOUSE / COURT / VERANDA FFL +0.300'),
        (ft(6), 'SOUTH LANDING +2.129'),
        (ft(11), 'ORDINARY CEILING +3.653 (~11 FT CLEAR)'),
        (ft(12), 'FIRST FLOOR FFL +3.958 (12 FT FLOOR-TO-FLOOR)'),
        (ft(23), 'DOUBLE-HEIGHT LIVING CEILING +7.310 (~23 FT CLEAR)'),
    ])
    return elems, bounds_of(elems), round(ft(19.5) / 1000, 2)


def _tirumala_entry_section_elements(b):
    """East-to-West front entrance steps (+300 mm continuous house/court/porch/veranda datum)
    and South-to-North Front Court (+300 mm) vs. Lower Car Bay (±0 mm) section."""
    ft = lambda f: round(f * 304.8)
    rev8 = _tirumala_rev8_meta(b) or {}
    opt = rev8.get('option', 'A')
    elems = []
    # --- Top profile: East-to-West (y = 0..45 ft mapped horizontally 0..13716 mm, vertical rise 6x enlarged for legibility) ---
    z_top = 4200
    vscale = 4  # 300 mm -> 1200 drawing units for unmistakable step legibility, with true mm dimensions labeled
    elems.append(T(6800, z_top + 2400, f'PROFILE 1 (EAST -> WEST): FRONT ENTRANCE STEPS (2 x 150 mm) TO CONTINUOUS +300 mm HOUSE / PORCH / VERANDA DATUM (OPTION {opt})', 165, 'A-ANNO'))
    elems.append(L((-600, z_top), (ft(46), z_top), LIGHT, .2, 'A-SITE', True))
    # Step 1 at y = 0.5 ft (152 mm), Step 2 at y = 1.5 ft (457 mm), Court y = 1.5..7.25 ft, Porch y = 7.5..10.5 ft, House y = 10.5..39 ft, Veranda y = 39..44.5 ft
    pts = [
        (0, z_top),
        (ft(0.5), z_top),
        (ft(0.5), z_top + 150 * vscale),
        (ft(1.5), z_top + 150 * vscale),
        (ft(1.5), z_top + 300 * vscale),
        (ft(44.5), z_top + 300 * vscale),
        (ft(44.5), z_top),
    ]
    elems.append(P(pts, '#eee9dc', INK, .3, 'A-SECT'))
    # Zone dividers along the flush +300 mm platform
    for x_div in (ft(7.25), ft(10.5), ft(38.5)):
        elems.append(L((x_div, z_top + 300 * vscale - 180), (x_div, z_top + 300 * vscale + 450), ACCENT, .2, 'A-SECT', True))
    elems.append(T(ft(0.0), z_top - 360, 'EAST ROAD / NGL ±0.000 m', 135, 'A-LEVL'))
    elems.append(T(ft(1.0), z_top + 150 * vscale + 260, '2 x 150 mm RISES (INTERMEDIATE TREAD +150 mm)', 125, 'A-STAIR'))
    elems.append(T(ft(4.4), z_top + 300 * vscale + 260, 'FRONT COURT (5.5 FT STANDING / +300 mm)', 130, 'A-SITE'))
    elems.append(T(ft(9.0), z_top + 300 * vscale + 620, 'SHALLOW PORCH (3 FT / +300 mm)', 125, 'A-SITE'))
    elems.append(T(ft(24.5), z_top + 300 * vscale + 260, 'DRAWING / FAMILY / CARE ROOMS (FLUSH +300 mm — NO STEP)', 140, 'A-FLOR'))
    elems.append(T(ft(41.5), z_top + 300 * vscale + 260, 'WEST VERANDA (+300 mm)', 130, 'A-FLOR'))

    # --- Bottom profile: South-to-North across Frontage (x = 0.5..39.5 ft -> 152..12040 mm) ---
    z_bot = 0
    elems.append(T(6096, z_bot + 2500, 'PROFILE 2 (SOUTH -> NORTH): RAISED FRONT COURT / CARE (+300 mm) VS. LOWER CAR BAY (10.5 x 19 FT AT ±0.000 m)', 165, 'A-ANNO'))
    elems.append(L((-600, z_bot), (12800, z_bot), INK, .35, 'A-SITE'))
    # Raised court/house x = 0.5..28.5 ft at +300 mm
    elems.append(P([
        (ft(0.5), z_bot),
        (ft(28.5), z_bot),
        (ft(28.5), z_bot + 300 * vscale),
        (ft(0.5), z_bot + 300 * vscale),
    ], '#eee9dc', INK, .3, 'A-SECT'))
    # Lower Car Bay x = 29..39.5 ft at ±0 mm
    elems.append(P([
        (ft(28.5), z_bot - 120),
        (ft(39.5), z_bot - 120),
        (ft(39.5), z_bot),
        (ft(28.5), z_bot),
    ], '#dcdbd3', INK, .25, 'A-SITE'))
    # Reference car (6.5 ft wide at x = 31..37.5 ft, 2 ft side gaps)
    car_x0, car_x1 = ft(31.0), ft(37.5)
    elems.append(P([
        (car_x0, z_bot + 180),
        (car_x1, z_bot + 180),
        (car_x1 - 180, z_bot + 1350),
        (car_x0 + 180, z_bot + 1350),
    ], '#f5f7f6', INK, .25, 'A-FURN'))
    elems.append(C(car_x0 + 320, z_bot + 180, 180, INK, .22, 'A-FURN'))
    elems.append(C(car_x1 - 320, z_bot + 180, 180, INK, .22, 'A-FURN'))
    elems.append(T(ft(14.5), z_bot + 300 * vscale + 280, 'FRONT COURT / DRAWING / CARE (+300 mm)', 145, 'A-FLOR'))
    elems.append(T(ft(34.25), z_bot + 1550, 'CAR BAY 10.5 x 19 FT (±0.000 m) / CAR 6.5 x 15.5 FT (2 FT SIDE GAPS)', 130, 'A-SITE'))
    elems.append(DIM((ft(0.5), z_bot - 450), (ft(28.5), z_bot - 450), 'x', z_bot - 650, -1))
    elems.append(DIM((ft(29.0), z_bot - 450), (ft(39.5), z_bot - 450), 'x', z_bot - 650, -1))
    return elems, bounds_of(elems)


def section_elements(b, scene):
    if _tirumala_rev8_meta(b) and b['planning'].get('tirumalaRevision',8)<10:
        return _tirumala_living_section_elements(b, scene)
    import trimesh
    cut = section_cut(b) / 1000
    elems = []
    for n in scene['nodes']:
        if n['role'] not in ('wall', 'floor', 'roof', 'stair', 'plinth'):
            continue
        a = scene['assets'][n['asset']]; m = trimesh.Trimesh(vertices=a['vertices'], faces=a['faces'], process=False); m.apply_transform(transformation(n))
        if not m.bounds[0, 0] - .001 <= cut <= m.bounds[1, 0] + .001:
            continue
        for line in trimesh.intersections.mesh_plane(m, plane_normal=[1, 0, 0], plane_origin=[cut, 0, 0]):
            elems.append(L((line[0, 1] * 1000, line[0, 2] * 1000), (line[1, 1] * 1000, line[1, 2] * 1000), INK, .25, 'A-SECT'))
    v = b['brief']; D = Polygon(b['footprint']).bounds[3]; H = v['floor_height_mm']; top = b['storeys'] * H
    if b.get('planning', {}).get('g2Revision'):top = building_levels(b)[-1][0]
    elems.append(L((-1500, -v['plinth_mm']), (D + 1500, -v['plinth_mm']), INK, .5, 'A-SITE'))
    for f in range(b['storeys']):
        elems.append(DIM((D, f * H), (D, top if f == b['storeys']-1 else (f + 1) * H), 'y', D + 700, -1))
    elems.append(DIM((D, -v['plinth_mm']), (D, top), 'y', D + 1300, -1))
    level_scale(elems, D + 2600, building_levels(b))
    return elems, bounds_of(elems), cut


# ---------------------------------------------------------------------------------------------- schedules
def listing(names, limit):
    """Names joined up to `limit` characters, ending "+N more" rather than cutting a word."""
    out = []
    for i, n in enumerate(names):
        more = len(names) - i
        text = ', '.join(out + [n])
        if len(text) > limit or (more > 1 and len(text) + len(f', +{more - 1} more') > limit):
            return ', '.join(out) + f' +{more} more' if out else n[:limit]
        out.append(n)
    return ', '.join(out)


def schedule_tables(b, report):
    if b.get('rooftop'):
        from .rooftop import with_rooftop_objects
        b=with_rooftop_objects(b)
    tags, types = opening_types(b)
    doors = [['TAG', 'DESCRIPTION', 'SIZE W x H (mm)', 'SILL', 'NO.', 'LOCATION']]
    for t in types:
        doors.append([t['tag'], describe(t), f'{t["width"]} x {t["height"]}', str(t['sill']) if t['sill'] else '-', str(t['count']),
                      listing(t['rooms'], 46)])
    rooms = [['SPACE', 'FLOOR', 'CLEAR SIZE (m)', 'CLEAR SIZE (ft-in)', 'AREA m2', 'AREA ft2']]

    def ftin(mm):
        inches = round(mm / 25.4)
        return f"{inches // 12}'{inches % 12}\""
    for s in b['spaces']:
        if s['kind'] in ('stair',):
            continue
        rx0, ry0, rx1, ry1 = principal_rect(Polygon(s['clear']))
        rooms.append([s['name'], 'Roof terrace' if b.get('rooftop') and s['floor']==b['storeys'] else 'Ground' if s['floor'] == 0 else 'First' if s['floor'] == 1 else str(s['floor']),
                      f'{(rx1 - rx0) / 1000:.2f} x {(ry1 - ry0) / 1000:.2f}', f'{ftin(rx1 - rx0)} x {ftin(ry1 - ry0)}',
                      f'{s["area_m2"]:.2f}', f'{s["area_m2"] * 10.7639:.0f}'])
    return [{'title': 'DOOR AND WINDOW SCHEDULE', 'x': 22, 'widths': [13, 60, 30, 13, 9, 70], 'rows': doors},
            {'title': 'ROOM SCHEDULE (CLEAR SIZE OF THE PRINCIPAL RECTANGLE)', 'x': 222, 'widths': [42, 15, 29, 37, 18, 18], 'rows': rooms}]


# ---------------------------------------------------------------------------------------------- sheets
def make_sheets(b, scene, report):
    sheets = []

    def add(id, title, elements, bounds, notes, table=None, schedule=None):
        width = bounds[2] - bounds[0]; height = bounds[3] - bounds[1]
        scale = next((s for s in [50, 75, 100, 125, 150, 200, 250, 300, 500, 750, 1000] if width / s <= AREA[0] and height / s <= AREA[1]), 1000)
        sheets.append({'planHash':b.get('planHash'),'id': id, 'title': title, 'elements': elements, 'bounds': bounds, 'scale': scale, 'notes': notes, 'table': table or [],
                       'schedule': schedule or [], 'page_mm': [420, 297]})
    for f in range(b['storeys']):
        e, bb = plan_elements(b, scene, f)
        rows = [['SPACE', 'CLEAR SIZE m', 'AREA m2']]
        for s in b['spaces']:
            if s['floor'] == f and s['kind'] != 'stair':
                rx0, ry0, rx1, ry1 = principal_rect(Polygon(s['clear']))
                star = '' if Polygon(s['clear']).buffer(1).covers(box(*Polygon(s['clear']).bounds)) else '*'
                rows.append([s['name'], f'{(rx1 - rx0) / 1000:.2f} x {(ry1 - ry0) / 1000:.2f}{star}', f'{s["area_m2"]:.2f}'])
        add(f'A-10{f + 1}', ['Ground floor plan','First floor plan','Second floor plan'][f], e, bb,
            ['All dimensions in millimetres; levels in metres above natural ground level (NGL).',
             'Room sizes are clear sizes between finished wall faces; * marks the principal rectangle of an L-shaped room.',
             'Dimension chains: openings, walls, overall. Tags: D door, SD sliding door, O cased opening, W window, V ventilator (see A-601).',
             'Door leaves are drawn in the room they open into. Windows above the +1.2 m cut are dashed; furniture is schematic at true scale.',
             'Grid bubbles are coordination axes only, not column positions. No certified IS 962 or local-code compliance is claimed.'], rows)
    if b.get('rooftop'):
        e,bb=plan_elements(b,scene,b['storeys'])
        for core in b['rooftop']['cores']:
            for part in core['hole']:
                e.append(P(part['polygon'],'none',INK,.2,'A-STAIR'))
                cx,cy=Polygon(part['polygon']).centroid.coords[0];e.append(T(cx,cy,'STAIR WELL / DOWN',150,'A-STAIR'))
        add('A-104','Roof terrace and stair access',e,bb,
            ['Roof access level, not an additional occupied storey.', 'Use the linked stair and its landing door to reach the guarded terrace.',
             'Roof openings and headhouse positions follow the authored stair core.'],
            [['SPACE','AREA m2'],['Open roof terrace',f"{b['rooftop']['spaces'][-1]['area_m2']:.2f}"]])
    e, bb = site_elements(b, scene)
    add('A-001', 'Site plan', e, bb, ['Setbacks shown are design assumptions, not verified byelaws.', 'Road width, property line and levels need a survey.',
                                     'No surveyed drainage fall or flood datum supplied.', 'Default steps are not a step-free route.'],
        [['AREA STATEMENT', 'VALUE', 'UNIT'], ['Plot', report['areas']['plot_m2'], 'm2'], ['Footprint', report['areas']['footprint_m2'], 'm2'],
         ['Gross floors', report['areas']['gross_floor_m2'], 'm2'], ['Coverage', report['areas']['ground_coverage_pct'], 'percent'],
         ['Geometric FAR', report['areas']['geometric_far'], 'ratio']])
    for i, d in enumerate(['Front', 'Rear', 'Left', 'Right']):
        e, bb = elevation_elements(b, d, scene)
        add(f'A-20{i + 1}', d + ' elevation', e, bb,
            ['Wall and opening heights derive from the building model; levels in metres above NGL.', 'This elevation records the primary wall plane.',
             'Decorative facade accessories are coordinated in 3D, not fully detailed here.', 'No cladding anchors or construction joints are designed.'])
    e, bb, cut = section_elements(b, scene)
    add('A-301', f'Section A-A / x = {cut:.2f} m (Double-height living & stair)' if _tirumala_rev8_meta(b) else f'Section A-A / x = {cut:.2f} m', e, bb, [
        'South-to-north projected stair, upper landing (outside void), ~23 ft double-height living void and ~11 ft care suite.' if _tirumala_rev8_meta(b) else 'Actual mesh-plane intersections, not a generic stair illustration.',
        'Cut objects: walls, floor slabs, roof, stair and plinth. Levels in metres above NGL.', 'No reinforcement or foundation design is represented.',
        'Stair headroom and handrails require a separate professional check.'])
    if _tirumala_rev8_meta(b):
        e_lvl, bb_lvl = _tirumala_entry_section_elements(b)
        add('A-302', 'Section B-B / Entrance steps, +300 mm house datum & ±0 mm car bay', e_lvl, bb_lvl, [
            'Two 150 mm entrance rises lead to a continuous +300 mm floor across front court, shallow porch, rooms and veranda.',
            'No additional step occurs court-to-porch-to-house. The 10.5 x 19 ft car bay remains at ±0.000 m (300 mm lower).',
            'Vertical rise enlarged in schematic profile for step legibility; annotated millimetre levels govern.',
            'Entrance steps are not wheelchair accessible; step-free care arrival requires portable ramp or regraded threshold.'])
    add('A-601', 'Door, window and room schedules', [P([(0, 0), (1, 0), (1, 1)], 'none', PAPER, .01)], (0, 0, 100, 100),
        ['Nominal structural opening sizes; frames, tolerances and clear passage widths need detailing.',
         'Room sizes are clear dimensions of the principal rectangle between finished wall faces.'], schedule=schedule_tables(b, report))
    # Coordination axes from the plan's outer and long interior walls; intentionally not advertised as an RCC scheme.
    e = []; fp = Polygon(b['footprint']); W, D = fp.bounds[2:]
    e.append(P(b['footprint'], 'none', LIGHT, .2))
    for w in b['walls']:
        if w['floor'] == 0:
            e.append(P(w['polygon'], '#d9ddd6', LIGHT, .1, 'A-WALL'))
    gx, gy = grid_axes(b, 0)
    for i, x in enumerate(gx):
        e.append(L((x, -600), (x, D + 600), INK, .15, 'S-GRID', True)); e.append(C(x, D + 1000, 300, INK, .15, 'S-GRID')); e.append(T(x, D + 910, axis_label(i), 220, 'S-GRID'))
    for j, y in enumerate(gy):
        e.append(L((-600, y), (W + 600, y), INK, .15, 'S-GRID', True)); e.append(C(-1000, y, 300, INK, .15, 'S-GRID')); e.append(T(-1000, y - 90, str(j + 1), 220, 'S-GRID'))
    for a_, c_ in zip(gx, gx[1:]):
        e.append(DIM((a_, 0), (c_, 0), 'x', -900, -1, 'S-GRID'))
    for a_, c_ in zip(gy, gy[1:]):
        e.append(DIM((W, a_), (W, c_), 'y', W + 900, -1, 'S-GRID'))
    add('S-001', 'Coordination axes / NOT a structural design', e, bounds_of(e), [
        'Axes follow the outer walls and the long interior walls; they are NOT column locations.', 'No column, beam, slab or footing is sized or certified.',
        'Engineer must establish an actual load path and lateral system.', 'No soil-bearing capacity is inferred from a soil photograph.'])
    return sheets


def _clean(t):
    return str(t).replace('²', '2').replace('×', 'x').replace('₹', 'INR ').replace('±', '+/-')


def svg_sheet(sheet, b):
    bb = sheet['bounds']; s = sheet['scale']; x0 = 20 + (AREA[0] - (bb[2] - bb[0]) / s) / 2; y0 = 44 + (AREA[1] - (bb[3] - bb[1]) / s) / 2

    def xy(x, y):
        return (x0 + (x - bb[0]) / s, 297 - y0 - (y - bb[1]) / s)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">',
           f'<metadata>planHash:{b.get("planHash","legacy")}</metadata><rect width="420" height="297" fill="white"/><g font-family="Arial,Helvetica,sans-serif">']

    def txt(x, y, t, size=3, anchor='start', color=INK, rot=0):
        extra = f' transform="rotate({-rot:.1f} {x:.4f} {y:.4f})"' if rot else ''
        out.append(f'<text x="{x:.4f}" y="{y:.4f}" fill="{color}" font-size="{size}" text-anchor="{anchor}"{extra}>{html.escape(str(t))}</text>')
    out.append(f'<path d="M 16 31 H 404 M 16 271 H 404" stroke="{INK}" stroke-width=".35"/>')
    txt(17, 17, 'FLOORFORGE', 5.2); txt(17, 25, sheet['title'], 3.1); txt(403, 18, sheet['id'], 5, 'end'); txt(403, 25, 'REV A / PRELIMINARY', 2.6, 'end')
    if sheet.get('schedule'):
        for tab in sheet['schedule']:
            x0_ = tab.get('x', 22); yy = 42
            txt(x0_, yy, tab['title'], 3); yy += 6
            xs = [x0_]
            for wd in tab['widths'][:-1]:
                xs.append(xs[-1] + wd)
            for i, row in enumerate(tab['rows']):
                if yy > 258:
                    break
                for j, val in enumerate(row):
                    txt(xs[j], yy, str(val), 2.1 if i else 2.2)
                if i == 0:
                    out.append(f'<path d="M {x0_} {yy + 1.4} H {x0_ + sum(tab["widths"])}" stroke="{INK}" stroke-width=".2"/>')
                yy += 4.2 if i else 5.2
    else:
        for e in primitives(sheet['elements']):
            if e['type'] == 'poly':
                pts = ' '.join(f'{x:.4f},{y:.4f}' for x, y in [xy(*p) for p in e['points']])
                tag = 'polygon' if e['closed'] else 'polyline'; out.append(f'<{tag} points="{pts}" fill="{e["fill"]}" stroke="{e["stroke"]}" stroke-width="{e["width"]}"/>')
            elif e['type'] == 'line':
                a, c = xy(*e['a']), xy(*e['b']); dash = ' stroke-dasharray="1.2 .6"' if e.get('dash') else ''
                out.append(f'<path d="M {a[0]:.4f} {a[1]:.4f} L {c[0]:.4f} {c[1]:.4f}" fill="none" stroke="{e["stroke"]}" stroke-width="{e["width"]}"{dash}/>')
            elif e['type'] == 'circle':
                cx, cy = xy(e['x'], e['y'])
                out.append(f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{e["r"] / s:.4f}" fill="{e["fill"]}" stroke="{e["stroke"]}" stroke-width="{e["width"]}"/>')
            elif e['type'] == 'text':
                x, y = xy(e['x'], e['y']); txt(x, y, e['text'], max(1.45, e['size'] / s), e['anchor'], rot=e.get('rot', 0))
        out.append('<path d="M 250 42 V 256" stroke="#c9d0c7" stroke-width=".2"/>')
        txt(261, 46, b['brief']['title'], 3.8)
        yy = 57
        for i, row in enumerate(sheet['table'][:26]):
            for j, value in enumerate(row):
                txt([261, 322, 372][j], yy, str(value)[:30], 2.2 if i else 2.35)
            yy += 5.4
        yy = max(yy + 8, 150); txt(261, yy, 'DRAWING NOTES', 2.7); yy += 7
        for note in sheet['notes']:
            for line in textwrap.wrap(note, 64):
                txt(261, yy, line, 2.1); yy += 3.9
            yy += 1.8
        txt(261, 244, f'SCALE 1:{s} AT A3 / CUT +1200 mm', 2.4)
        txt(261, 251, 'Dimensions govern; do not scale from a screen.', 2.2)
        xa, ya = 22, 259; out.append(f'<path d="M {xa} {ya} H {xa + 4000 / s}" stroke="{INK}" stroke-width=".6"/>')
        for dist in (0, 2000, 4000):
            xx = xa + dist / s; out.append(f'<path d="M {xx} {ya - 1} V {ya + 1}" stroke="{INK}" stroke-width=".2"/>'); txt(xx, ya + 5, f'{dist // 1000} m', 1.9, 'middle')
    for i, note in enumerate(sheet['notes'] if sheet.get('schedule') else []):
        txt(22, 263 + i * 4, note, 2.1)
    txt(17, 279, b['banner'], 2.65, color='#8a4933'); txt(17, 286, 'Reference design screen only. Survey, structure, services, byelaws and professional approval remain outstanding.', 2.15)
    txt(403, 283, f'{sheet["id"]}  |  420 x 297 mm', 2.35, 'end'); out.append('</g></svg>'); return ''.join(out)


def pdf_sheets(sheets, b, report):
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(420 * 72 / 25.4, 297 * 72 / 25.4), invariant=1, pageCompression=1)
    c.setSubject('planHash:'+b.get('planHash','legacy')); c.setKeywords('FloorForge planHash:'+b.get('planHash','legacy'))
    mm = 72 / 25.4

    def pdf_text(value):
        value = _clean(value)
        if b.get('planning', {}).get('g2Revision'):
            # Built-in Helvetica has no eighth-fraction glyphs. Keep the exact
            # Tirumala 5 dimensions readable in portable PDF viewers.
            for glyph, fraction in [('⅛', ' 1/8'), ('¼', ' 1/4'), ('⅜', ' 3/8'),
                                    ('½', ' 1/2'), ('⅝', ' 5/8'), ('¾', ' 3/4'), ('⅞', ' 7/8')]:
                value = value.replace(glyph, fraction)
            value = value.replace('′', "'").replace('″', '"').replace('↑', 'UP').replace('↓', 'DOWN').replace('→', '>')
        return value

    def text(x, y, t, size=3, anchor='start', rot=0):
        c.setFillColor(HexColor(INK)); c.setFont('Helvetica', size * mm)
        t = pdf_text(t)
        if rot:
            c.saveState(); c.translate(x * mm, y * mm); c.rotate(rot); c.drawCentredString(0, 0, t); c.restoreState()
        elif anchor == 'middle':
            c.drawCentredString(x * mm, y * mm, t)
        elif anchor == 'end':
            c.drawRightString(x * mm, y * mm, t)
        else:
            c.drawString(x * mm, y * mm, t)
    for sh in sheets:
        c.setTitle('FloorForge preliminary drawing and review pack'); bb = sh['bounds']; scale = sh['scale']
        ox = 20 + (AREA[0] - (bb[2] - bb[0]) / scale) / 2; oy = 44 + (AREA[1] - (bb[3] - bb[1]) / scale) / 2

        def point(x, y):
            return ((ox + (x - bb[0]) / scale) * mm, (oy + (y - bb[1]) / scale) * mm)
        text(17, 280, 'FLOORFORGE', 5.2); text(17, 272, sh['title'], 3.1); text(403, 280, sh['id'], 5, 'end')
        c.setStrokeColor(HexColor(INK)); c.setLineWidth(.35 * mm); c.line(16 * mm, 266 * mm, 404 * mm, 266 * mm); c.line(16 * mm, 26 * mm, 404 * mm, 26 * mm)
        if sh.get('schedule'):
            for tab in sh['schedule']:
                x0_ = tab.get('x', 22); yy = 255
                text(x0_, yy, tab['title'], 3); yy -= 6
                xs = [x0_]
                for wd in tab['widths'][:-1]:
                    xs.append(xs[-1] + wd)
                for i, row in enumerate(tab['rows']):
                    if yy < 39:
                        break
                    for j, val in enumerate(row):
                        text(xs[j], yy, str(val), 2.1 if i else 2.2)
                    if i == 0:
                        c.setLineWidth(.2 * mm); c.line(x0_ * mm, (yy - 1.4) * mm, (x0_ + sum(tab['widths'])) * mm, (yy - 1.4) * mm)
                    yy -= 4.2 if i else 5.2
            for i, note in enumerate(sh['notes']):
                text(22, 34 - i * 4, note, 2.1)
        else:
            for e in primitives(sh['elements']):
                if e['type'] == 'poly':
                    path = c.beginPath(); p = point(*e['points'][0]); path.moveTo(*p)
                    for p in e['points'][1:]:
                        path.lineTo(*point(*p))
                    if e['closed']:
                        path.close()
                    fill = e['fill'] != 'none'; stroke = e['stroke'] != 'none'
                    if fill:
                        c.setFillColor(HexColor(e['fill']))
                    if stroke:
                        c.setStrokeColor(HexColor(e['stroke']))
                    c.setLineWidth(e['width'] * mm); c.setDash(); c.drawPath(path, fill=fill, stroke=stroke)
                elif e['type'] == 'line':
                    c.setStrokeColor(HexColor(e['stroke'])); c.setLineWidth(e['width'] * mm); c.setDash([1.2 * mm, .6 * mm] if e.get('dash') else [])
                    c.line(*point(*e['a']), *point(*e['b'])); c.setDash()
                elif e['type'] == 'circle':
                    x, y = point(e['x'], e['y']); c.setStrokeColor(HexColor(e['stroke'])); c.setLineWidth(e['width'] * mm)
                    c.circle(x, y, e['r'] / scale * mm, stroke=1, fill=0)
                else:
                    x, y = point(e['x'], e['y']); size = max(1.45, e['size'] / scale)
                    c.setFont('Helvetica', size * mm); c.setFillColor(HexColor(INK)); t = pdf_text(e['text'])
                    if e.get('rot'):
                        c.saveState(); c.translate(x, y); c.rotate(e['rot']); c.drawCentredString(0, 0, t); c.restoreState()
                    elif e['anchor'] == 'middle':
                        c.drawCentredString(x, y, t)
                    else:
                        c.drawString(x, y, t)
            c.setStrokeColor(HexColor('#c9d0c7')); c.setLineWidth(.2 * mm); c.line(250 * mm, 41 * mm, 250 * mm, 255 * mm)
            text(261, 251, b['brief']['title'], 3.8); yy = 240
            for i, row in enumerate(sh['table'][:26]):
                for j, val in enumerate(row):
                    text([261, 322, 372][j], yy, str(val)[:30], 2.2 if i else 2.35)
                yy -= 5.4
            yy = min(yy - 8, 147); text(261, yy, 'DRAWING NOTES', 2.7); yy -= 7
            for note in sh['notes']:
                for line in textwrap.wrap(note, 64):
                    text(261, yy, line, 2.1); yy -= 3.9
                yy -= 1.8
            text(261, 53, f'SCALE 1:{scale} AT A3 / CUT +1200 mm', 2.4); text(261, 46, 'Dimensions govern; do not scale from a screen.', 2.2)
            c.setStrokeColor(HexColor(INK)); c.setLineWidth(.6 * mm); c.line(22 * mm, 38 * mm, (22 + 4000 / scale) * mm, 38 * mm)
            for dist in (0, 2000, 4000):
                text(22 + dist / scale, 32, f'{dist // 1000} m', 1.9)
        text(17, 18, b['banner'], 2.65); text(17, 11, 'Survey, structure, services, byelaws and professional approval remain outstanding.', 2.15); c.showPage()
    # Programmatic report pages, using line wrapping and measured page bounds.
    _, types = opening_types(b)
    sections = [('REVIEW / SCOPE', [('Geometry', report['review']['status']), ('Regulatory', report['review']['regulatory']), ('Structure', report['review']['structural']), ('Accessibility', report['review']['accessibility'])],
                 ['Passing geometric checks is not evidence of construction safety or statutory compliance.', *['Warning: ' + w.get('message', w['code']) for w in report['review']['warnings']]]),
                ('COST / SCENARIO', [('Gross floor area', f'{report["areas"]["gross_floor_ft2"]} ft2'), ('Illustrative range', f'INR {report["cost"]["low_lakh"]} - {report["cost"]["high_lakh"]} lakh'), ('Owner budget', f'INR {report["cost"]["budget_lakh"]} lakh'), ('Rates', str(report['cost']['rates_inr_ft2']) + ' INR/ft2')],
                 [report['cost']['basis'], 'Excluded: ' + ', '.join(report['cost']['excludes']), 'No reinforcement quantities or cement bag counts are invented from floor area.']),
                ('SITE / SERVICES / STRUCTURE', [('Soil', report['structure']['soil']), ('Foundation recommendation', 'NOT PROVIDED: requires geotechnical design'), ('Solar elevation', f'{report["solar"]["elevation_deg"]:.2f} degrees'), ('Vastu score', str(report['vastu']['score']) + ' / advisory only')],
                 [report['structure']['soil_warning'], *report['mep']['notes'], report['vastu']['limitation'], 'Solar method: ' + report['solar']['method']]),
                ('TIMELINE / ASSUMPTIONS', [(x['phase'], f'Week {x["start_week"]} + {x["duration_weeks"]} weeks') for x in report['timeline']],
                 ['Illustrative overlapping phases, not a contractual or local construction schedule.', 'No government review period or supply lead time has been verified.']),
                ('OPENING SCHEDULE', [(f'{t["tag"]}  x{t["count"]}', f'{describe(t)} / {t["width"]} x {t["height"]} / sill {t["sill"]} mm') for t in types],
                 ['Nominal wall opening dimensions. Frames, tolerances and clear passage require detailing.'])]
    for title, rows, notes in sections:
        # Split large schedules across pages rather than clipping them.
        for page in range(max(1, math.ceil(len(rows) / 23))):
            text(20, 276, 'FLOORFORGE / ' + title, 4.5); yy = 252
            for key, value in rows[page * 23:(page + 1) * 23]:
                text(22, yy, key, 3); text(135, yy, str(value), 3); yy -= 7.2
            yy = min(yy - 15, 115)
            for note in notes:
                for line in textwrap.wrap(note, 135):
                    text(22, yy, line, 2.8); yy -= 5
                yy -= 4
            text(20, 16, b['banner'], 2.6); c.showPage()
    c.save(); return buf.getvalue()


def dxf_export(b, scene, path):
    import ezdxf, uuid
    from ezdxf.enums import TextEntityAlignment
    doc = ezdxf.new('R2018', setup=True); doc.units = 4
    doc.ezdxf_metadata()['CREATED_BY_EZDXF'] = 'ezdxf ' + ezdxf.__version__ + ' / FloorForge deterministic export'
    doc.ezdxf_metadata()['PLAN_HASH'] = b.get('planHash','legacy')
    doc.header['$INSUNITS'] = 4; doc.header['$MEASUREMENT'] = 1
    for k in ('$TDCREATE', '$TDUPDATE', '$TDUCREATE', '$TDUUPDATE'):
        doc.header[k] = 2451544.5
    for k in ('$FINGERPRINTGUID', '$VERSIONGUID'):
        doc.header[k] = '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'floorforge:' + sha(b) + k)).upper() + '}'
    for layer, color, weight in LAYERS:
        if layer not in doc.layers:
            doc.layers.new(layer, dxfattribs={'color': color, 'lineweight': weight})
    if 'FF-ARCH' not in doc.dimstyles:
        ds = doc.dimstyles.new('FF-ARCH')
        ds.dxf.dimtxt = 180; ds.dxf.dimtsz = 60; ds.dxf.dimasz = 90; ds.dxf.dimexo = 120; ds.dxf.dimexe = 120; ds.dxf.dimgap = 60
        ds.dxf.dimdec = 0; ds.dxf.dimtad = 1
    doc.appids.new('FLOORFORGE'); msp = doc.modelspace(); W = Polygon(b['footprint']).bounds[2]
    dims = 0
    for f in range(b['storeys']+bool(b.get('rooftop'))):
        offset = f * (W + 12000); elements, _ = plan_elements(b, scene, f)
        for e in elements:
            layer = e['layer']; attrs = {'layer': layer}
            if e['type'] == 'dim':
                (x1, y1), (x2, y2) = e['p1'], e['p2']
                if e['axis'] == 'x':
                    base, angle = (x1 + offset, e['at']), 0
                else:
                    base, angle = (e['at'] + offset, y1), 90
                d = msp.add_linear_dim(base=base, p1=(x1 + offset, y1), p2=(x2 + offset, y2), angle=angle, dimstyle='FF-ARCH', dxfattribs=attrs)
                d.render(); entity = d.dimension; dims += 1
            elif e['type'] == 'poly':
                pts = [(x + offset, y) for x, y in e['points']]
                entity = msp.add_lwpolyline(pts, close=e['closed'], dxfattribs=attrs)
                if e['fill'] == INK:
                    h = msp.add_hatch(color=7, dxfattribs=attrs); h.paths.add_polyline_path(pts, is_closed=True)
            elif e['type'] == 'line':
                entity = msp.add_line((e['a'][0] + offset, e['a'][1]), (e['b'][0] + offset, e['b'][1]), dxfattribs=attrs)
            elif e['type'] == 'circle':
                entity = msp.add_circle((e['x'] + offset, e['y']), e['r'], dxfattribs=attrs)
            else:
                entity = msp.add_text(_clean(e['text']), dxfattribs={**attrs, 'height': e['size'], 'rotation': e.get('rot', 0)})
                entity.set_placement((e['x'] + offset, e['y']), align=TextEntityAlignment.BOTTOM_CENTER if e['anchor'] == 'middle' else TextEntityAlignment.LEFT)
            entity.set_xdata('FLOORFORGE', [(1000, f'floor:{f}'), (1000, 'preliminary')])
        fp = Polygon(b['footprint']); D = fp.bounds[3]
        msp.add_text(b['banner'], dxfattribs={'height': 190, 'layer': 'A-ANNO'}).set_placement((offset, -5200))
        msp.add_text(f'FLOOR {f} / TRUE MILLIMETRES / NO STRUCTURAL CERTIFICATION', dxfattribs={'height': 210, 'layer': 'A-ANNO'}).set_placement((offset, D + 4800))
        layout = doc.layouts.new('GROUND' if f == 0 else f'FLOOR-{f}')
        layout.page_setup(size=(420, 297), margins=(10, 10, 10, 10), units='mm')
        layout.add_viewport(center=(140, 145), size=(240, 230), view_center_point=(offset + W / 2, D / 2), view_height=max(D + 9000, (W + 9000) * 230 / 240))
        layout.add_text('FLOORFORGE / PRELIMINARY', dxfattribs={'height': 4}).set_placement((268, 255))
    # ezdxf rewrites update timestamps, version GUIDs and its metadata on save.
    # Use its fixed-metadata mode only during serialization, then restore options.
    # This export stage runs in the single-worker generation queue.
    old_fixed = ezdxf.options.write_fixed_meta_data_for_testing
    try:
        ezdxf.options.write_fixed_meta_data_for_testing = True
        doc.saveas(path)
    finally:
        ezdxf.options.write_fixed_meta_data_for_testing = old_fixed
    # Give each design its own stable GUID rather than the testing constant.
    lines = Path(path).read_text('utf8').splitlines()
    for i in range(0, len(lines) - 3, 2):
        if lines[i].strip() == '9' and lines[i + 1] in ('$FINGERPRINTGUID', '$VERSIONGUID'):
            lines[i + 3] = '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'floorforge:' + sha(b) + lines[i + 1])).upper() + '}'
    Path(path).write_bytes(('\n'.join(lines) + '\n').encode('utf8'))
    check = ezdxf.readfile(path); audit = check.audit()
    if audit.has_errors:
        raise DesignError('DXF_REIMPORT', 'DXF audit reported errors.', [str(x) for x in audit.errors])
    return {'status': 'ezdxf_reimport_pass', 'entities': len(check.modelspace()), 'units': 'mm', 'dimension_entities': len(check.modelspace().query('DIMENSION')),
            'dimension_chains': dims, 'layers': [l for l, _, _ in LAYERS],
            'autocad_gui': 'NOT TESTED', 'annotation_scope': 'Floor plans with dimension chains (true DIMENSION entities), tags, grid, levels and section marker; elevations, section and schedules are in PDF/SVG.'}
