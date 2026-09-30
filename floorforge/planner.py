"""Residential room planner: architectural partis dimensioned by search and scored against planning rules.

The automatic plan is chosen, not assumed. A public spine (living -> dining -> hall) runs back from the entrance
and the other rooms hang off it in two stacks: the kitchen sits behind the stair with its utility, the pooja and
a common bath open off the dining, and the bedroom suites (attached bath on an outside wall, a dressing room for
the master) take the quiet rear. Every candidate tiles the building envelope exactly with rectangles and is scored
against

* NBC 2016 Part 3 style minimums (hard): habitable room 9.5 m2 and 2.4 m wide, kitchen 5.0 m2 and 1.8 m, bath with
  WC 2.8 m2 and 1.2 m, corridor 1.0 m clear;
* comfortable target sizes that grow with the plot, and caps above which a room is wastefully large;
* proportions (no strip rooms), daylight and air (habitable rooms and baths on an outside wall);
* attached baths as briefed, clustered wet areas (short plumbing runs), the pooja kept off bath walls and out from
  under upper-floor baths, baths kept off habitable rooms below;
* economy of circulation, and Vastu zones when the brief asks for them.

A deterministic coordinate search over the parti's parameters keeps the best-scoring candidate. Coordinates are
integer millimetres in the building envelope: x across the plot, y away from the road (the road is at y < 0).
"""
from __future__ import annotations

import math
from functools import lru_cache

from shapely.geometry import box
from shapely.ops import unary_union

from .model import DesignError, local_to_enu

EXT, INT = 230, 150
HALF = INT // 2
SNAP = 50
STAIR_W, STAIR_D = 2500, 4450
BIG = 10_000.
PLACEMENT_CELL_WEIGHT = 150.       # one 4 x 4-cell miss matters more than a small soft size preference
PLACEMENT_MISSING = 700.           # strongly prefer candidates that contain every requested semantic room
PLACEMENT_MAX_DISTANCE = 2.25      # deliberately coarse tolerance: a little over half of the four-cell board

PUBLIC = frozenset({'living', 'dining', 'hall', 'family', 'foyer'})
WET = frozenset({'bathroom', 'utility', 'kitchen'})
LIT = frozenset({'drawing-room', 'bedroom', 'living', 'family', 'study', 'kitchen'})       # need a window on an outside wall
AIRED = frozenset({'bathroom', 'utility'})                                 # need a ventilator (else a duct)
HABITABLE_BELOW = frozenset({'drawing-room', 'living', 'dining', 'bedroom', 'kitchen', 'study', 'family', 'pooja'})

# kind: (hard min clear width m, hard min clear area m2, comfortable width m, target area on a tight plot and on a
#        generous one m2, area above which the room is wastefully large m2, largest comfortable aspect ratio)
RULES = {
    'master':   (2.4, 9.5, 3.3, 12.5, 19.0, 27.0, 1.50),
    'bedroom':  (2.4, 7.5, 2.9, 10.5, 15.0, 21.0, 1.55),
    'living':   (3.0, 9.5, 3.5, 14.0, 30.0, 46.0, 2.20),
    'drawing-room': (2.4, 7.5, 2.8, 9.0, 13.0, 20.0, 1.8),
    'family':   (2.4, 9.5, 3.0, 12.0, 24.0, 38.0, 2.40),
    'dining':   (2.4, 6.0, 2.7, 7.5, 14.0, 21.0, 1.80),
    'kitchen':  (1.8, 5.0, 2.2, 6.5, 11.0, 16.5, 2.30),
    'utility':  (1.0, 1.8, 1.2, 2.4, 4.5, 7.5, 3.00),
    'bathroom': (1.2, 2.8, 1.4, 3.0, 4.6, 7.2, 2.20),
    'common':   (1.2, 2.8, 1.35, 2.9, 3.8, 5.2, 2.20),
    'pooja':    (0.9, 1.0, 1.2, 1.5, 3.2, 5.5, 1.80),
    'study':    (2.1, 7.5, 2.5, 7.5, 11.0, 16.5, 1.70),
    'dress':    (1.2, 2.0, 1.4, 2.8, 5.0, 8.0, 2.80),
    'store':    (0.9, 1.0, 1.0, 1.6, 3.0, 6.0, 3.40),
}
WEIGHT = {'master': 1.3, 'bedroom': 1.0, 'living': 1.2, 'family': .8, 'dining': .8, 'kitchen': 1.0, 'utility': .5,
          'bathroom': .7, 'common': .7, 'pooja': .8, 'study': .8, 'dress': .4, 'store': .3}
FILLER = {'store': 4., 'linen': 3., 'study': 1.}
L_SHAPE = {'bedroom': 6., 'kitchen': 14., 'bathroom': 30., 'study': 6., 'dining': 4., 'living': 2., 'family': 1.,
           'dress': 8., 'store': 4., 'utility': 10., 'pooja': 10.}


def sn(x: float) -> int:
    return int(round(x / SNAP)) * SNAP


class Rm:
    """A planned room: gross rectangles plus how it is entered."""
    __slots__ = ('key', 'name', 'kind', 'rects', 'access', 'prefer', 'opening', 'dw', 'suite', 'role', 'memo')

    def __init__(self, key, name, kind, rects, access=None, prefer=None, opening='door', dw=900, suite=None, role=''):
        self.key, self.name, self.kind, self.rects = key, name, kind, [tuple(int(round(c)) for c in r) for r in rects]
        self.access, self.prefer, self.opening, self.dw, self.suite, self.role = access, prefer, opening, dw, suite, role
        self.memo = None

    def area(self):
        return sum((x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in self.rects)

    def bounds(self):
        return (min(r[0] for r in self.rects), min(r[1] for r in self.rects), max(r[2] for r in self.rects), max(r[3] for r in self.rects))

    def centre(self):
        a = self.area() or 1
        return (sum((x0 + x1) / 2 * (x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in self.rects) / a,
                sum((y0 + y1) / 2 * (x1 - x0) * (y1 - y0) for x0, y0, x1, y1 in self.rects) / a)


def _own(rects, i, side):
    x0, y0, x1, y1 = rects[i]
    for j, (a0, b0, a1, b1) in enumerate(rects):
        if j == i:
            continue
        if side == 'l' and a1 == x0 and min(y1, b1) - max(y0, b0) > 1:
            return True
        if side == 'r' and a0 == x1 and min(y1, b1) - max(y0, b0) > 1:
            return True
        if side == 'b' and b1 == y0 and min(x1, a1) - max(x0, a0) > 1:
            return True
        if side == 't' and b0 == y1 and min(x1, a1) - max(x0, a0) > 1:
            return True
    return False


def measure(r, W, D):
    """Estimated clear area (m2) and the clear width and depth of the main rectangle (m)."""
    total, best, main = 0., -1., (0., 0.)
    rects = r.rects
    for i, (x0, y0, x1, y1) in enumerate(rects):
        al = EXT if x0 <= 0 else 0 if _own(rects, i, 'l') else HALF
        ar = EXT if x1 >= W else 0 if _own(rects, i, 'r') else HALF
        ab = EXT if y0 <= 0 else 0 if _own(rects, i, 'b') else HALF
        at = EXT if y1 >= D else 0 if _own(rects, i, 't') else HALF
        cw, cd = max(0., (x1 - x0 - al - ar) / 1000), max(0., (y1 - y0 - ab - at) / 1000)
        a = cw * cd
        total += a
        if a > best:
            best, main = a, (cw, cd)
    if len(rects) > 1 and r.kind in PUBLIC:
        # An open room that nearly fills its bounding box (a lounge around a terrace) is measured on that box.
        bx0, by0, bx1, by1 = r.bounds()
        bw = (bx1 - bx0 - (EXT if bx0 <= 0 else HALF) - (EXT if bx1 >= W else HALF)) / 1000
        bd = (by1 - by0 - (EXT if by0 <= 0 else HALF) - (EXT if by1 >= D else HALF)) / 1000
        if total >= .7 * bw * bd:
            main = (bw, bd)
    return total, main


def shared(ra, rb):
    """Shared boundary segments between two rooms: (orientation, fixed coordinate, lo, hi)."""
    segs = []
    for ax0, ay0, ax1, ay1 in ra.rects:
        for bx0, by0, bx1, by1 in rb.rects:
            if ax1 == bx0 or ax0 == bx1:
                lo, hi = max(ay0, by0), min(ay1, by1)
                if hi - lo > 1:
                    segs.append(('v', ax1 if ax1 == bx0 else ax0, lo, hi))
            if ay1 == by0 or ay0 == by1:
                lo, hi = max(ax0, bx0), min(ax1, bx1)
                if hi - lo > 1:
                    segs.append(('h', ay1 if ay1 == by0 else ay0, lo, hi))
    return segs


def outside(r, W, D):
    """Length of the room's boundary on the envelope (walls that can take windows), mm."""
    n = 0
    for x0, y0, x1, y1 in r.rects:
        n += (y1 - y0) * ((x0 <= 0) + (x1 >= W)) + (x1 - x0) * ((y0 <= 0) + (y1 >= D))
    return n


# ------------------------------------------------------------------------------------------------ programme
def lerp(a, b, t):
    return a + (b - a) * t


def target(kind, role, g):
    rule = RULES['master' if role == 'master' else kind]
    return lerp(rule[3], rule[4], g)


def generosity(W, D, kinds, stair):
    """How far the envelope exceeds a tight version of this floor's programme (0 tight .. 1 generous)."""
    lo = sum(RULES[k][3] for k in kinds) * 1.28 + stair
    hi = sum(RULES[k][4] for k in kinds) * 1.28 + stair
    return max(0., min(1., (W * D / 1e6 - lo) / max(hi - lo, 1.)))


# ------------------------------------------------------------------------------------------------ rooms in units
BATH_W = (1650, 1800, 1950, 2100, 2400)
BATH_D = (1950, 2100, 2250, 2400, 2700)


@lru_cache(maxsize=4096)
def bath_size(g, max_w, max_d, rear_ext=False):
    """Gross size (along x, along y) of an attached bath at an outside corner: clear area near the target."""
    want = lerp(3.3, 4.8, g)
    best = None
    for bw in BATH_W:
        if bw > max_w:
            continue
        for bd in BATH_D:
            if bd > max_d:
                continue
            cw, cd = (bw - EXT - HALF) / 1000, (bd - HALF - (EXT if rear_ext else HALF)) / 1000
            if min(cw, cd) < 1.2 or cw * cd < 2.8:
                continue
            ratio = max(cw, cd) / min(cw, cd)
            cost = abs(cw * cd - want) + max(0, ratio - 1.9) * 2
            if best is None or cost < best[0]:
                best = (cost, bw, bd)
    return best[1:] if best else None


_SUITES = {}


def suite_rooms(u, rect, side, W, D, behind, g):
    """Candidate subdivisions of a bedroom suite unit; each is a list of rooms (the bedroom first)."""
    k = (u['key'], u['num'], bool(u.get('ensuite')), bool(u.get('master')), rect, side, W, D, behind, round(g, 4))
    hit = _SUITES.get(k)
    if hit is None:
        if len(_SUITES) > 20000:
            _SUITES.clear()
        hit = _SUITES[k] = _suite_rooms(u, rect, side, W, D, behind, g)
    return hit


def _suite_rooms(u, rect, side, W, D, behind, g):
    x0, y0, x1, y1 = rect
    w, d = x1 - x0, y1 - y0
    key, n = u['key'], u['num']
    master = u.get('master')
    bname = 'Master bedroom' if master else f'Bedroom {n}'
    role = 'master' if master else ''
    inner = x1 if side == 'L' else x0          # the hall side
    door = (inner, y0)
    bath_name = 'Master bath' if master else f'Bath {n}'
    dress_name = 'Master dress' if master else f'Dress {n}'
    bkey, dkey = 'bath-' + key.split('-')[1], 'dress-' + key.split('-')[1]
    options = []

    def bed(rects):
        return Rm(key, bname, 'bedroom', rects, 'hall', door, 'door', 900, role=role)

    merged = [behind] if behind else []
    if not u.get('ensuite'):
        options.append([bed([rect] + merged)])
        return options
    # 1. Attached bath at the front outer corner; the bedroom's entry leg runs beside it from the hall door.
    main_min = 3000 + 300 * g
    size = bath_size(g, w - 1100, d - main_min)
    if size:
        bw, bd = size
        if side == 'L':
            bath = (x0, y0, x0 + bw, y0 + bd); rooms = [(x0 + bw, y0, x1, y0 + bd), (x0, y0 + bd, x1, y1)]
            bp = (x0 + bw, y0 + bd)
        else:
            bath = (x1 - bw, y0, x1, y0 + bd); rooms = [(x0, y0, x1 - bw, y0 + bd), (x0, y0 + bd, x1, y1)]
            bp = (x1 - bw, y0 + bd)
        options.append([bed(rooms + merged), Rm(bkey, bath_name, 'bathroom', [bath], key, bp, 'door', 750, key, 'ensuite')])
    # 2. Bath (and dressing room) along the rear: bedroom -> dress -> bath, or the bath off the bedroom.
    rear_ext = y1 >= D
    size = bath_size(g, w, d - main_min, rear_ext)
    if size:
        bw, bd = size
        if w - bw < 900:
            bw = w
        yb = y1 - bd
        if side == 'L':
            bath = (x0, yb, x0 + bw, y1); rest = (x0 + bw, yb, x1, y1) if bw < w else None
        else:
            bath = (x1 - bw, yb, x1, y1); rest = (x0, yb, x1 - bw, y1) if bw < w else None
        main = (x0, y0, x1, yb)
        if rest and master and rest[2] - rest[0] >= 1400:
            dp = ((rest[0] + rest[2]) / 2, yb)
            bp = (rest[0] if side == 'L' else rest[2], (yb + y1) / 2)
            options.append([bed([main] + merged), Rm(dkey, dress_name, 'dress', [rest], key, dp, 'cased', 900, key, 'dress'),
                            Rm(bkey, bath_name, 'bathroom', [bath], dkey, bp, 'door', 750, key, 'ensuite')])
        rects = [main] + ([rest] if rest else [])
        bp = ((bath[2] if side == 'L' else bath[0]) - (300 if side == 'L' else -300), yb) if bw < w else (inner, yb)
        options.append([bed(rects + merged), Rm(bkey, bath_name, 'bathroom', [bath], key, bp, 'door', 750, key, 'ensuite')])
    # 3. A strip along the outside wall beside a clean rectangular bedroom: the bath at the door end, the dressing
    #    room (master) or a wardrobe bay behind it.
    for sw in (1800, 2100, 2400):
        if w - sw < 3300 or d < 3300:
            continue
        bd = min(2700, max(1950, sn(d * .45)))
        if side == 'L':
            strip0, strip1, bedr = x0, x0 + sw, (x0 + sw, y0, x1, y1)
        else:
            strip0, strip1, bedr = x1 - sw, x1, (x0, y0, x1 - sw, y1)
        shared_x = strip1 if side == 'L' else strip0
        bath = (strip0, y0, strip1, y0 + bd)
        rest = (strip0, y0 + bd, strip1, y1)
        if master and d - bd >= 1500:
            options.append([bed([bedr] + merged), Rm(dkey, dress_name, 'dress', [rest], key, (shared_x, (y0 + bd + y1) / 2), 'cased', 900, key, 'dress'),
                            Rm(bkey, bath_name, 'bathroom', [bath], dkey, ((strip0 + strip1) / 2, y0 + bd), 'door', 750, key, 'ensuite')])
        elif d - bd < 1200:
            options.append([bed([bedr] + merged), Rm(bkey, bath_name, 'bathroom', [(strip0, y0, strip1, y1)], key, (shared_x, y0 + 600), 'door', 750, key, 'ensuite')])
        else:
            options.append([bed([bedr] + merged), Rm(dkey, dress_name, 'dress', [rest], key, (shared_x, (y0 + bd + y1) / 2), 'cased', 900, key, 'dress'),
                            Rm(bkey, bath_name, 'bathroom', [bath], key, (shared_x, y0 + bd / 2), 'door', 750, key, 'ensuite')])
    # 4. Bath (and dressing room) in the bay behind the end of the hall, beside this suite.
    if behind:
        bx0, by0, bx1, by1 = behind
        depth, width = by1 - by0, bx1 - bx0
        if width - INT >= 1200:
            shared_x = bx0 if side == 'L' else bx1
            if master and depth >= 1950 + 1500:
                bd = min(2700, max(1950, depth - 2000))
                dress = (bx0, by0, bx1, by1 - bd); bath = (bx0, by1 - bd, bx1, by1)
                options.append([bed([rect]), Rm(dkey, dress_name, 'dress', [dress], key, (shared_x, (by0 + by1 - bd) / 2), 'cased', 900, key, 'dress'),
                                Rm(bkey, bath_name, 'bathroom', [bath], dkey, ((bx0 + bx1) / 2, by1 - bd), 'door', 750, key, 'ensuite')])
            elif depth <= 3000:
                options.append([bed([rect]), Rm(bkey, bath_name, 'bathroom', [behind], key, (shared_x, (by0 + by1) / 2), 'door', 750, key, 'ensuite')])
            else:
                bd = 2400
                bath = (bx0, by1 - bd, bx1, by1); front = (bx0, by0, bx1, by1 - bd)
                options.append([bed([rect, front]), Rm(bkey, bath_name, 'bathroom', [bath], key, (shared_x, by1 - bd / 2), 'door', 750, key, 'ensuite')])
    if not options:
        options.append([bed([rect] + merged)])
    return options


def unit_rooms(u, rect, side, W, D, behind, g, front_public):
    """Candidate room sets for one unit of a stack."""
    x0, y0, x1, y1 = rect
    inner = x1 if side == 'L' else x0
    t = u['t']
    merged = [behind] if behind else []
    if t == 'suite':
        return suite_rooms(u, rect, side, W, D, behind, g)
    if t == 'toilet':
        return [[Rm('cbath', 'Common bath', 'bathroom', [rect] + merged, 'hall', (inner, y0), 'door', 750, role='common')]]
    if t == 'drawing-room':
        return [[Rm('drawing-room', 'Drawing room', 'drawing-room', [rect] + merged, 'hall', (inner, y0), 'door', 900)]]
    if t == 'study':
        return [[Rm('study', 'Study', 'study', [rect] + merged, 'hall', (inner, y0), 'door', 900)]]
    if t == 'store':
        return [[Rm('store', 'Store', 'store', [rect] + merged, 'hall', (inner, (y0 + y1) / 2), 'door', 750)]]
    if t == 'pooja':
        acc = front_public if front_public else 'hall'
        prefer = ((x0 + x1) / 2, y0) if front_public else (inner, (y0 + y1) / 2)
        return [[Rm('pooja', 'Pooja', 'pooja', [rect] + merged, acc, prefer, 'door', 900)]]
    if t == 'utility':
        return [[Rm('utility', 'Utility', 'utility', [rect] + merged, 'kitchen', (inner - 450 if side == 'L' else inner + 450, y0), 'door', 750)]]
    if t == 'kitchen':
        acc = front_public if front_public else 'hall'
        util = u.get('util')
        kd = y1 - y0 - (u['ud'] if util else 0)
        k = (x0, y0, x1, y0 + kd)
        prefer = ((max(x0, u.get('pub_x0', x0)) + x1) / 2, y0) if front_public else (inner, y0 + min(kd, 2400) / 2 + 300)
        opening = 'cased' if u.get('open') else 'door'
        rooms = [Rm('kitchen', 'Kitchen', 'kitchen', [k], acc, prefer, opening, 1200 if u.get('open') else 900)]
        if util:
            rooms.append(Rm('utility', 'Utility', 'utility', [(x0, y0 + kd, x1, y1)] + merged, 'kitchen', (inner - 500 if side == 'L' else inner + 500, y0 + kd), 'door', 750))
        elif merged:
            rooms[0].rects += merged
        return [rooms]
    raise ValueError(t)


# ------------------------------------------------------------------------------------------------ stacks
UNIT_DEPTH = {  # (min, max) gross depth mm, before the width-dependent target
    'drawing-room': (2700, 4400), 'suite': (2900, 7800), 'toilet': (1500, 2400), 'study': (2700, 4400), 'store': (1100, 2400),
    'pooja': (1200, 2400), 'utility': (1250, 2200), 'kitchen': (2600, 4300),
}


def unit_target_area(u, g):
    t = u['t']
    if t == 'suite':
        a = target('bedroom', 'master' if u.get('master') else '', g)
        if u.get('ensuite'):
            a += lerp(3.3, 4.8, g)
        if u.get('master') and g > .45:
            a += lerp(2.8, 5.0, g) * .8
        return a * 1.14
    if t == 'toilet':
        return lerp(RULES['common'][3], RULES['common'][4], g) * 1.2
    if t == 'kitchen':
        return target('kitchen', '', g) * 1.14 + (target('utility', '', g) * 1.2 if u.get('util') else 0)
    return target(t, '', g) * 1.15


def distribute(units, width, h, g, shift):
    """Depths of the units in a stack of the given width and height (front to rear), or None."""
    lims = []
    for u in units:
        lo, hi = UNIT_DEPTH[u['t']]
        if u['t'] == 'toilet' and width < 2000:
            lo = max(lo, 1950)
        if u['t'] == 'kitchen' and u.get('util'):
            lo, hi = lo + u['ud'], hi + u['ud']
        if u['t'] == 'suite' and u.get('ensuite') and width < 3300 + 1650:
            lo = max(lo, 2900)
        want = unit_target_area(u, g) * 1e6 / max(width, 1)
        lims.append((lo, hi, min(hi, max(lo, want))))
    if sum(l[0] for l in lims) > h:
        return None
    ds = [l[2] for l in lims]
    total = sum(ds)
    if total > h:
        room = sum(d - l[0] for d, l in zip(ds, lims)) or 1
        ds = [d - (total - h) * (d - l[0]) / room for d, l in zip(ds, lims)]
    elif total < h:
        spare = h - total
        room = sum(l[1] - d for d, l in zip(ds, lims))
        if room > spare:
            ds = [d + spare * (l[1] - d) / room for d, l in zip(ds, lims)]
        else:
            ds = [l[1] for l in lims]
            ds[-1] += h - sum(ds)
    if len(ds) > 1 and shift:
        a = max(lims[0][0], min(lims[0][1], ds[0] + shift))
        delta = a - ds[0]
        if lims[1][0] <= ds[1] - delta:
            ds[0], ds[1] = a, ds[1] - delta
    cuts, y = [], 0.
    for d in ds[:-1]:
        y += d
        cuts.append(sn(y))
    return cuts


def back_region(W, D, y0, xh0, wh, left, right, g, shifts, above):
    """Rooms of the region behind the public front: a hall from y0 and two stacks of units beside it.

    `above(x0, x1)` names the public room directly in front of the span x0..x1 at y0 (or None).
    """
    xh1 = xh0 + wh
    if xh0 < 2400 or W - xh1 < 2400:
        return None
    h = D - y0
    stacks = []
    for side, units, x0, x1, shift in (('L', left, 0, xh0, shifts[0]), ('R', right, xh1, W, shifts[1])):
        cuts = distribute(units, x1 - x0, h, g, shift)
        if cuts is None:
            return None
        ys = [y0] + [y0 + c for c in cuts] + [D]
        if any(b - a < 1000 for a, b in zip(ys, ys[1:])):
            return None
        stacks.append((side, units, x0, x1, ys))
    # The hall runs back far enough to reach the door of the rearmost unit that opens off it.
    yh = y0 + 1200
    for side, units, x0, x1, ys in stacks:
        for u, a in zip(units, ys):
            if u['t'] not in ('utility',):
                yh = max(yh, a + 1250)
    yh = sn(yh)
    behind = None
    if D - yh < 1000:
        yh = D
    else:
        behind = (xh0, yh, xh1, D)
    # The bay behind the hall's end goes to the rearmost unit on the side that uses it best, a linen store, or the
    # hall itself (a corridor to a rear window).
    options = []
    for owner in ((('L', 'R', 'store') + (('hall',) if D - yh < 2000 else ())) if behind else (None,)):
        hall = [Rm('hall', 'Hall', 'hall', [(xh0, y0, xh1, D if owner == 'hall' else yh)], None)]
        built = []
        for side, units, x0, x1, ys in stacks:
            for i, u in enumerate(units):
                rect = (x0, ys[i], x1, ys[i + 1])
                pub = above(x0, x1) if i == 0 and ys[i] == y0 else None
                b = behind if (owner == side and i == len(units) - 1) else None
                built.append(unit_rooms(u, rect, side, W, D, b, g, pub))
        extra = []
        if owner == 'store':
            if D - yh > 3000:
                continue
            extra = [Rm('linen', 'Linen store', 'store', [behind], 'hall', ((xh0 + xh1) / 2, yh), 'door', 750)]
        options.append((hall, built, extra))
    return options


# ------------------------------------------------------------------------------------------------ scoring
def room_cost(r, W, D, g):
    k = (W, D, g)
    if r.memo is not None and r.memo[0] == k:
        return r.memo[1]
    c = _room_cost(r, W, D, g)
    r.memo = (k, c)
    return c


def rule_key(r):
    return 'master' if r.role == 'master' else 'common' if r.role == 'common' else r.kind


def _room_cost(r, W, D, g):
    rule = RULES.get(rule_key(r))
    if rule is None:
        return 0.
    wmin, amin, wcomf, t0, t1, amax, asp = rule
    a, (cw, cd) = measure(r, W, D)
    short, long_ = min(cw, cd), max(cw, cd)
    if short < wmin - 1e-6 or a < amin - 1e-6:
        return BIG + 1000 * (max(0., wmin - short) + max(0., amin - a))
    t = lerp(t0, t1, g)
    if a < t:
        c = 40 * ((t - a) / t) ** 2
    elif a <= amax:
        c = 6 * (a - t) / max(amax - t, .1)
    else:
        c = 6 + 90 * ((a - amax) / amax) ** 2 + 8 * (a - amax) / amax
    if r.kind in ('bedroom', 'study', 'kitchen', 'dining', 'living', 'family'):
        wcomf += .45 * g          # generous plots earn wider rooms, not just longer ones
    if short < wcomf:
        c += 12 * (wcomf - short) + 25 * ((wcomf - short) / wcomf) ** 2
    ratio = long_ / max(short, .1)
    if ratio > asp:
        c += (40 if r.kind in ('bathroom', 'kitchen', 'utility') else 14) * (ratio - asp) ** 2
    if len(r.rects) > 1:
        c += L_SHAPE.get(r.kind, 6.) * (len(r.rects) - 1) ** 1.5
    return c * WEIGHT.get(rule_key(r), 1.)


def floor_cost(rooms, W, D, g, needs):
    """Cost of one floor's rooms (lower is better); BIG and above means infeasible."""
    by = {r.key: r for r in rooms}
    c = 0.
    for r in rooms:
        c += room_cost(r, W, D, g)
        if r.kind in LIT and outside(r, W, D) < 1200:
            c += BIG
        if r.kind in AIRED and outside(r, W, D) < 600:
            c += 22
        if r.kind == 'dining' and outside(r, W, D) < 900:
            c += 6
        if r.kind == 'hall':
            x0, y0, x1, y1 = r.rects[0]
            cw = (x1 - x0 - (EXT if x0 <= 0 else HALF) - (EXT if x1 >= W else HALF)) / 1000
            if cw < 1.0:
                c += BIG
            c += (r.area() / 1e6) * 1.1 + 30 * max(0., 1.2 - cw)
            doors = [o.prefer[1] for o in rooms if o.access == 'hall' and o.prefer]
            if doors and y1 > max(doors) + 1100:
                c += (y1 - max(doors) - 1100) / 1000 * (x1 - x0) / 1000 * 2.5
        if r.access:
            p = by.get(r.access)
            if p is None:
                c += BIG
                continue
            segs = shared(r, p)
            need = 800 if (r.kind in PUBLIC and p.kind in PUBLIC) else r.dw + (200 if r.opening == 'cased' else 300)
            if not segs or max(s[3] - s[2] for s in segs) < need:
                c += BIG
    c += sum(FILLER.get(r.key, 0.) for r in rooms)
    wet = [r for r in rooms if r.kind in WET]
    for r in wet:
        if any(o is not r and sum(s[3] - s[2] for s in shared(r, o)) >= 900 for o in wet):
            c -= 3
    pooja = by.get('pooja')
    if pooja:
        for r in rooms:
            if r.kind == 'bathroom' and shared(pooja, r):
                c += 30
    kitchen = by.get('kitchen')
    if kitchen:
        for r in rooms:
            if r.kind == 'bedroom' and sum(s[3] - s[2] for s in shared(kitchen, r)) > 600:
                c += 2
    kinds = [r.kind for r in rooms]
    # Every bedroom needs a bath on its own floor: its own attached bath, or a common bath off the hall.
    served = {r.suite for r in rooms if r.kind == 'bathroom' and r.suite}
    if any(r.kind == 'bedroom' and r.key not in served for r in rooms) and not any(r.role == 'common' for r in rooms):
        c += 90
    for want, penalty in needs.items():
        if want == 'ensuite':
            got = sum(1 for r in rooms if r.role == 'ensuite')
            c += penalty * max(0, needs['ensuite_count'] - got)
        elif want == 'ensuite_count':
            continue
        elif want == 'common':
            if not any(r.role == 'common' for r in rooms):
                c += penalty
        elif want not in kinds:
            c += penalty
    return c


def below_cost(rooms, below):
    """Baths over the kitchen or the pooja of the floor below (the same terms as stacking_cost, and a firmer one for
    the kitchen), so an upper suite chooses where its bath goes knowing what lies underneath."""
    c = 0.
    for r in rooms:
        if r.kind != 'bathroom':
            continue
        for q in below:
            m = overlap(r, q)
            if m > 0:
                c += 25 if q.kind == 'pooja' else 6 * m
    return c


def pooja_corners(plan, needs, hall):
    """When a requested pooja found no slot in the stacks, a small pooja room carved from a rear corner of the living
    room, clear of the hall's mouth and opening into the living room (a common arrangement in Indian homes)."""
    if not needs.get('pooja') or any(r.kind == 'pooja' for r in plan):
        return []
    living = next((r for r in plan if r.key == 'living' and len(r.rects) == 1), None)
    if living is None:
        return []
    x0, y0, x1, y1 = living.rects[0]
    hx0, hy0, hx1, _ = hall.rects[0]
    if hy0 != y1:
        return []
    out = []
    for pw, pd in ((1650, 1650), (1500, 1800), (1800, 1500)):
        if y1 - y0 - pd < 2400 or x1 - x0 - pw < 3000:
            continue
        for a, b in ((x1 - pw, x1), (x0, x0 + pw)):
            if min(b, hx1) - max(a, hx0) > -300:      # keep the hall mouth open, with room to turn into it
                continue
            rest = [(x0, y0, x1, y1 - pd), (x0, y1 - pd, a, y1) if a > x0 else (b, y1 - pd, x1, y1)]
            room = Rm('living', living.name, 'living', rest, living.access, living.prefer, living.opening, living.dw)
            pooja = Rm('pooja', 'Pooja', 'pooja', [(a, y1 - pd, b, y1)], 'living', ((a + b) / 2, y1 - pd), 'door', 750)
            out.append([room if r is living else r for r in plan] + [pooja])
    return out


def overlap(a, b):
    tot = 0
    for ax0, ay0, ax1, ay1 in a.rects:
        for bx0, by0, bx1, by1 in b.rects:
            w, h = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
            if w > 0 and h > 0:
                tot += w * h
    return tot / 1e6


def stacking_cost(ground, upper):
    """Upper-floor baths over habitable rooms, the kitchen or the pooja cost (leaks, and custom avoids a toilet over
    the kitchen or the shrine); over baths and the utility they share a stack and earn a little."""
    c = 0.
    for r in upper:
        if r.kind != 'bathroom':
            continue
        for q in ground:
            m = overlap(r, q)
            if m <= 0:
                continue
            if q.kind == 'pooja':
                c += 25
            elif q.kind == 'kitchen':
                c += 6 * m
            elif q.kind in WET:
                c -= .6 * m
            elif q.kind in HABITABLE_BELOW:
                c += .8 * m
    return c


ZONES = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
VASTU = {'kitchen': ({'SE'}, {'NW', 'E'}), 'master': ({'SW'}, {'S', 'W'}), 'pooja': ({'NE'}, {'N', 'E'})}
VASTU_WEIGHT = {'off': 0., 'flexible': 2., 'moderate': 5., 'strict': 12.}


def zone(x, y, cx, cy, bearing):
    e, n = local_to_enu(x - cx, y - cy, bearing)
    if math.hypot(e, n) < 900:
        return 'C'
    return ZONES[int(((math.degrees(math.atan2(e, n)) % 360) + 22.5) // 45) % 8]


def vastu_cost(floors, W, D, bearing, mirror):
    c = 0.
    cx, cy = W / 2, D / 2
    for rooms in floors:
        for r in rooms:
            key = 'master' if r.role == 'master' else r.kind
            x, y = r.centre()
            if mirror:
                x = W - x
            z = zone(x, y, cx, cy, bearing)
            if key in VASTU:
                best, ok = VASTU[key]
                c += 0 if z in best else .5 if z in ok else 1.
            elif r.kind == 'bathroom' and z in ('NE', 'C'):
                c += .7
    return c


# ------------------------------------------------------------------------------------------------ floors
def terrace_rect(W, style):
    return (sn(max(STAIR_W + 1400, W * .54)), 0, W, 1550 if style != 'tropical' else 1850)


def front_row(W, yF, floor, stair, prog, fr):
    """Stair, living (or family lounge with the open terrace) and an optional front room."""
    rooms = []
    x0 = 0
    if stair:
        rooms.append(Rm('stair', 'Stair', 'stair', [(0, 0, STAIR_W, STAIR_D)]))
        x0 = STAIR_W
    x1 = W - fr if fr else W
    if floor == 0:
        name = 'Living & dining' if prog['combined'] else 'Living'
        rooms.append(Rm('living', name, 'living', [(x0, 0, x1, yF)]))
        if fr:
            rooms.append(Rm('drawing-room' if prog['front_kind']=='drawing-room' else 'front', 'Drawing room' if prog['front_kind']=='drawing-room' else 'Study' if prog['front_kind'] == 'study' else 'Guest room', prog['front_kind'],
                            [(x1, 0, W, yF)], 'living', (x1, yF / 2), 'door', 900))
    else:
        tx0, ty0, tx1, ty1 = terrace_rect(W, prog['style'])
        rooms.append(Rm('family', 'Family lounge', 'family', [(x0, 0, tx0, ty1), (x0, ty1, W, yF)]))
        rooms.append(Rm('terrace', 'Open terrace', 'terrace', [(tx0, ty0, tx1, ty1)], 'family', ((tx0 + tx1) / 2, ty1), 'sliding', 1800))
    return rooms


def public_above(rooms):
    pubs = [r for r in rooms if r.kind in PUBLIC]

    def above(x0, x1):
        for r in pubs:
            for a0, b0, a1, b1 in r.rects:
                if min(x1, a1) - max(x0, a0) >= 1300:
                    return r.key
        return None
    return above


def assignments(fixed, required, optional, suites):
    """(left, right) unit stacks: fixed units lead the left stack, then extras, then suites (the master last)."""
    out = []
    n_req, n_opt = len(required), len(optional)
    for ms in range(1 << len(suites)):
        for mr in range(1 << n_req):
            for mo in range(3 ** n_opt):
                L, R = list(fixed), []
                for i, e in enumerate(required):
                    (R if mr >> i & 1 else L).append(e)
                code = mo
                for e in optional:
                    code, state = divmod(code, 3)
                    if state == 1:
                        L.append(e)
                    elif state == 2:
                        R.append(e)
                for i, s in enumerate(suites):
                    (R if ms >> i & 1 else L).append(s)
                if not L or not R or len(L) > 3 or len(R) > 3:
                    continue
                out.append((tuple(L), tuple(R)))
    # Stable, de-duplicated order.
    seen, result = set(), []
    for a in out:
        k = (tuple(u['key'] for u in a[0]), tuple(u['key'] for u in a[1]))
        if k not in seen:
            seen.add(k)
            result.append(a)
    return result


class House:
    """Programme and search space for one brief."""

    def __init__(self, v, W, D):
        self.v, self.W, self.D0 = v, W, D
        self.placement = [dict(label=p[0],x=float(p[1]),y=float(p[2]),source=p[3],floor=p[4] if len(p)>4 else None)
                          for p in v.get('_placement_hints',())]
        self.storeys = v['storeys']
        self.stair = self.storeys > 1
        total = v['bedrooms']
        self.counts = [total] if self.storeys == 1 else ([max(1,total//2),total-max(1,total//2)] if self.storeys==2 else [total//3+(1 if f>=3-total%3 else 0) for f in range(3)])
        if max(self.counts) > 4:
            raise DesignError('PROGRAMME_CAPACITY', 'At most four bedrooms per floor in this bounded generator.')
        want = v.get('attached_baths', 'all')
        attached = total if want == 'all' else min(int(want), total)
        # Bedrooms, numbered ground floor first; the master is the upper floor's (or the only floor's) last.
        self.below = ()          # kitchen and pooja of the chosen ground floor, for the upper floor's search
        self.suites = []
        num = 1
        for f, k in enumerate(self.counts):
            for i in range(k):
                self.suites.append({'t': 'suite', 'key': f'bed-{num}', 'num': num, 'floor': f})
                num += 1
        for hint in self.placement:
            if hint['floor'] is None:continue
            label=hint['label'];m=__import__('re').fullmatch(r'bedroom-([1-8])',label)
            num=total if label=='master-bedroom' else int(m[1]) if m else None
            if num is not None:
                for suite in self.suites:
                    if suite['num']==num:suite['floor']=hint['floor']
        self.counts=[sum(s['floor']==f for s in self.suites) for f in range(self.storeys)]
        if any(n<1 or n>4 for n in self.counts):
            names=['Ground','First','Second']
            issues=[{'floor':f,'label':'bedrooms','message':f'{names[f]} has {n} bedrooms after your floor assignments; Quick Guide needs 1–4 on each active floor. Assign a bedroom here, change the storey count, or turn the cells into Custom Plan rooms.',
                     'cells':[], 'actual':n, 'required_min':1,'required_max':4} for f,n in enumerate(self.counts) if not 1<=n<=4]
            raise DesignError('PLACEMENT_FLOOR_CAPACITY',issues[0]['message'],{'rooms':issues})
        master = next(s for s in self.suites if s['num']==total)
        master['master'] = True
        master['key'] = 'bed-m'
        order = [master] + [s for s in self.suites if s['floor'] == 0 and s is not master] + [s for s in self.suites if s['floor'] > 0 and s is not master]
        if v.get('eldercare') and self.storeys == 2:
            ground_first=next((s for s in order if s['floor']==0),None)
            if ground_first is not None:order=[ground_first]+[s for s in order if s is not ground_first]
        for s in order[:attached]:
            s['ensuite'] = True
        self.bedroom_keys={s['num']:s['key'] for s in self.suites}
        self.bathroom_keys={s['num']:('bath-m' if s['key']=='bed-m' else 'bath-'+s['key'].split('-')[1]) for s in self.suites}
        self.suite_floors={s['num']:s['floor'] for s in self.suites}
        self.attached = attached
        ups = [s for s in self.suites if s['floor'] == 1]
        need = any(not s.get('ensuite') for s in ups)
        required = [{'t': 'toilet', 'key': 'cbath'}] if need else []
        optional = ([] if need else [{'t': 'toilet', 'key': 'cbath'}]) + [{'t': 'study', 'key': 'study'}]
        if self.wants_guest(1):required.append({'t':'drawing-room','key':'drawing-room'})
        self.fcombos = assignments([], required, optional, sorted(ups, key=lambda s: bool(s.get('master')))) if self.stair else []
        self.upper_combos={1:self.fcombos}
        for f in range(2,self.storeys):
            suites=[s for s in self.suites if s['floor']==f];need=any(not s.get('ensuite') for s in suites)
            required=[{'t':'toilet','key':'cbath'}] if need else []
            optional=([] if need else [{'t':'toilet','key':'cbath'}])+[{'t':'study','key':'study'}]
            if self.wants_guest(f):required.append({'t':'drawing-room','key':'drawing-room'})
            self.upper_combos[f]=assignments([],required,optional,sorted(suites,key=lambda s:bool(s.get('master'))))

    def wants_guest(self, floor):
        return any(h['label']=='drawing-room' and (h['floor'] if h['floor'] is not None else 0)==floor for h in self.placement)

    def matches_hint(self, label, room):
        """Semantic matching is intentionally independent of dimensions. Numbered bedrooms/baths bind to the
        programme's stable keys; generic service labels bind by role/kind."""
        m=__import__('re').fullmatch(r'bedroom-([1-8])',label)
        if m:return room.key==self.bedroom_keys.get(int(m[1]))
        m=__import__('re').fullmatch(r'bathroom-([1-8])',label)
        if m:return room.key==self.bathroom_keys.get(int(m[1]))
        if label=='master-bedroom':return room.role=='master'
        if label=='bathroom':return room.role=='common'
        if label=='dining' and room.key=='living' and 'dining' in room.name.lower():return True
        if label=='store':return room.kind=='store'
        return room.key==label or room.kind==label

    def hint_floor(self, label):
        """Choose the floor on which an existence-sensitive hint is preserved during the per-floor search.

        This fallback serves legacy whole-home and text hints; explicitly painted floors take precedence.
        Stable programme rooms keep their assigned programme floor;
        the one genuinely floor-optional room, a study, uses the upper floor in G+1 homes and the ground floor in a
        single-storey home. This prevents both floor searches from adding duplicate optional rooms merely to avoid a
        local missing-room penalty.
        """
        m=__import__('re').fullmatch(r'(?:bedroom|bathroom)-([1-8])',label)
        if m:return self.suite_floors.get(int(m[1]),0)
        if label=='master-bedroom':return self.storeys-1
        if label=='family':return 1
        if label=='study':return self.storeys-1
        return 0

    def missing_hints(self, rooms, floor):
        """Hints assigned to this floor whose semantic room is absent from a candidate."""
        return [h for h in self.placement if (h['floor'] if h['floor'] is not None else self.hint_floor(h['label']))==floor and
                not any(self.matches_hint(h['label'],room) for room in rooms)]

    def ground_combos(self):
        suites = sorted([s for s in self.suites if s['floor'] == 0], key=lambda s: bool(s.get('master')))
        n = 1
        for fixed, req, opt in (([{'t': 'kitchen', 'key': 'kitchen'}], [{'t': 'toilet', 'key': 'cbath'}], [{'t': 'pooja', 'key': 'pooja'}, {'t': 'study', 'key': 'study'}]),
                                ([{'t': 'utility', 'key': 'utility'}], [{'t': 'toilet', 'key': 'cbath'}], [{'t': 'pooja', 'key': 'pooja'}, {'t': 'study', 'key': 'study'}]),
                                ([], [], [{'t': 'pooja', 'key': 'pooja'}, {'t': 'study', 'key': 'study'}])):
            if self.wants_guest(0):req=[*req,{'t':'drawing-room','key':'drawing-room'}]
            n = max(n, len(assignments(fixed, req, opt, suites)))
        return n

    def rich_area(self):
        """Largest floor area (m2) the programme can use generously, per floor."""
        best = 0.
        for f, k in enumerate(self.counts):
            suites = [s for s in self.suites if s['floor'] == f]
            a = sum(unit_target_area(dict(s), 1.) for s in suites)
            if f == 0:
                a += (RULES['living'][4] + RULES['dining'][4] + RULES['kitchen'][4] + RULES['utility'][4] + RULES['bathroom'][4]
                      + RULES['pooja'][4] + RULES['study'][4]) * 1.15 + (11. if self.stair else 0.)
            else:
                a += (RULES['family'][4] + RULES['study'][4] + RULES['bathroom'][4]) * 1.15 + 11. + 7.
            best = max(best, a * 1.1)
        return best

    # -------------------------------------------------------------------------------------------- ground floor
    def ground(self, p, D):
        v, W = self.v, self.W
        stair = self.stair
        yF = STAIR_D if stair else p['yF']
        fr = p['fr'] if (W - (STAIR_W if stair else 0) - p['fr']) >= 5200 else 0
        suites = [s for s in self.suites if s['floor'] == 0]
        combined = p['gmode'] == 'compact'
        prog = {'combined': combined, 'front_kind': 'drawing-room' if self.wants_guest(0) else 'study', 'style': v['style']}
        rooms = front_row(W, yF, 0, stair, prog, fr)
        needs = {'pooja': 25. if v['pooja'] else 0., 'utility': 10., 'common': 60. if any(not s.get('ensuite') for s in suites) else 22.,
                 'ensuite': 45., 'ensuite_count': sum(1 for s in suites if s.get('ensuite'))}
        kinds = ['living', 'kitchen', 'utility', 'bathroom'] + ['bedroom'] * len(suites) + ['bathroom'] * needs['ensuite_count']
        kinds += ['dining'] if not combined else []
        kinds += ['pooja'] if v['pooja'] else []
        g = generosity(W, D, kinds, 11. if stair else 0.)
        if combined:
            y0 = yF
            above = public_above(rooms)
            kitchen = {'t': 'kitchen', 'key': 'kitchen', 'util': True, 'ud': 1500, 'open': v['open_kitchen'], 'pub_x0': STAIR_W if stair else 0}
            required = [{'t': 'toilet', 'key': 'cbath'}]
            optional = ([{'t': 'pooja', 'key': 'pooja'}] if v['pooja'] else []) + ([] if fr else [{'t': 'study', 'key': 'study'}])
            xh0 = p['xh']
            if stair and xh0 < STAIR_W:
                return None
            if self.wants_guest(0) and not fr:required.append({'t':'drawing-room','key':'drawing-room'})
            combos = assignments([kitchen], required, optional, sorted(suites, key=lambda s: bool(s.get('master'))))
            if not combos:return None
            left, right = combos[p['ga'] % len(combos)]
            res = back_region(W, D, y0, xh0, p['wh'], left, right, g, (p['s1'], p['s2']), above)
            return self._finish(rooms, res, W, D, g, needs, floor=0)
        # Three rows: kitchen (+ utility) | dining | pooja / common bath behind the living; suites at the rear.
        dM, xk, wd = p['dM'], p['xk'], p['wd']
        yD = yF + dM
        xs = xk + wd
        if W - xs < 1300:
            xs = W
        mid = []
        util_in_slot = dM >= 3900
        if util_in_slot:
            ud = sn(min(1800, max(1250, dM - 2850)))
            mid.append(Rm('kitchen', 'Kitchen', 'kitchen', [(0, yF, xk, yD - ud)], 'dining', (xk, yF + (dM - ud) / 2 + 250),
                          'cased' if v['open_kitchen'] else 'door', 1200 if v['open_kitchen'] else 900))
            mid.append(Rm('utility', 'Utility', 'utility', [(0, yD - ud, xk, yD)], 'kitchen', (xk - 500, yD - ud), 'door', 750))
        else:
            mid.append(Rm('kitchen', 'Kitchen', 'kitchen', [(0, yF, xk, yD)], 'dining', (xk, yF + dM / 2 + 250),
                          'cased' if v['open_kitchen'] else 'door', 1200 if v['open_kitchen'] else 900))
        mid.append(Rm('dining', 'Dining', 'dining', [(xk, yF, xs, yD)], 'living'))
        taken = {prog['front_kind']} if fr else set()
        if xs < W:
            opt = p['right']
            parts = opt.split('|')
            if len(parts) == 1:
                cuts = [(yF, yD)]
            else:
                ya = yF + p['rsplit']
                if ya > yD - 1100 or ya < yF + 1100:
                    return None
                cuts = [(yF, ya), (ya, yD)]
            for part, (a, b) in zip(parts, cuts):
                if part == 'pooja':
                    mid.append(Rm('pooja', 'Pooja', 'pooja', [(xs, a, W, b)], 'dining', (xs, (a + b) / 2), 'door', 900))
                elif part == 'toilet':
                    mid.append(Rm('cbath', 'Common bath', 'bathroom', [(xs, a, W, b)], 'dining', (xs, b), 'door', 750, role='common'))
                elif part == 'store':
                    mid.append(Rm('store', 'Store', 'store', [(xs, a, W, b)], 'dining', (xs, (a + b) / 2), 'door', 750))
                elif part == 'drawing-room':
                    if 'drawing-room' in taken:return None
                    mid.append(Rm('drawing-room','Drawing room','drawing-room',[(xs,a,W,b)],'dining',(xs,a),'door',900))
                elif part == 'study':
                    if fr:
                        return None
                    mid.append(Rm('study', 'Study', 'study', [(xs, a, W, b)], 'dining', (xs, a), 'door', 900))
                taken.add(part)
        rooms += mid
        hpos = p['hpos']
        wh = p['wh']
        if xs - xk < wh:
            return None
        xh0 = {'L': xk, 'C': sn((xk + xs - wh) / 2), 'R': xs - wh}[hpos]
        required = [] if 'toilet' in taken else [{'t': 'toilet', 'key': 'cbath'}]
        optional = [{'t': 'study', 'key': 'study'}] if 'study' not in taken else []
        if v['pooja'] and 'pooja' not in taken:
            optional.append({'t': 'pooja', 'key': 'pooja'})
        fixed = [] if util_in_slot else [{'t': 'utility', 'key': 'utility'}]
        if self.wants_guest(0) and 'drawing-room' not in taken:required.append({'t':'drawing-room','key':'drawing-room'})
        combos = assignments(fixed, required, optional, sorted(suites, key=lambda s: bool(s.get('master'))))
        if not combos:
            return None
        left, right = combos[p['ga'] % len(combos)]
        res = back_region(W, D, yD, xh0, wh, left, right, g, (p['s1'], p['s2']), lambda a, b: 'dining' if (a >= xk and b <= xs) else None)
        return self._finish(rooms, res, W, D, g, needs, floor=0)

    # -------------------------------------------------------------------------------------------- upper floor
    def upper(self, p, D, floor=1):
        v, W = self.v, self.W
        suites = [s for s in self.suites if s['floor'] == floor]
        prog = {'combined': False, 'front_kind': None, 'style': v['style']}
        rooms = front_row(W, STAIR_D, floor, True, prog, 0)
        if floor<self.storeys-1:
            for r in rooms:
                if r.kind=='terrace':r.kind='veranda';r.key='veranda';r.name='Covered veranda'
        needs = {'common': 60. if any(not s.get('ensuite') for s in suites) else 0., 'ensuite': 45.,
                 'ensuite_count': sum(1 for s in suites if s.get('ensuite'))}
        kinds = ['family'] + ['bedroom'] * len(suites) + ['bathroom'] * (needs['ensuite_count'] + (1 if needs['common'] else 0))
        g = generosity(W, D, kinds, 11. + 7.)
        combos = self.upper_combos[floor]
        if not combos:
            return None
        left, right = combos[p['fa'] % len(combos)]
        xh0 = p['fxh']
        if xh0 < STAIR_W:
            return None
        res = back_region(W, D, STAIR_D, xh0, p['fwh'], left, right, g, (p['f1'], p['f2']), public_above(rooms))
        return self._finish(rooms, res, W, D, g, needs, self.below, floor=floor)

    def _finish(self, rooms, res, W, D, g, needs, below=(), floor=0):
        """Pick the best subdivision of every unit and the best owner of the bay behind the hall; upstairs, suites
        keep their baths off the kitchen and pooja of the ground floor below (`below`)."""
        if res is None:
            return None
        best = None
        for hall, built, extra in res:
            fixed = rooms + hall + extra
            # Wet rooms and the pooja outside the suites, for the local adjacency terms.
            context = [r for r in fixed if r.kind in WET or r.kind == 'pooja']
            chosen = []
            for cands in built:
                if len(cands) == 1:
                    chosen.append(cands[0])
                    for r in cands[0]:
                        if r.kind in WET or r.kind == 'pooja':
                            context.append(r)
                    continue
                pick = min(range(len(cands)), key=lambda i: (self._local(cands[i], context, W, D, g) + below_cost(cands[i], below), i))
                chosen.append(cands[pick])
            plan = fixed + [r for grp in chosen for r in grp]
            for alt in [plan] + pooja_corners(plan, needs, hall[0]):
                cost = floor_cost(alt, W, D, g, needs) + below_cost(alt, below)
                if self.placement:
                    # Do not let the local search prune the only candidate containing an explicitly positioned
                    # optional room. Floor assignment remains planner-owned (hint_floor); within that floor, room
                    # existence is strict while physical feasibility is still enforced by floor_cost/BIG.
                    if self.missing_hints(alt,floor):
                        continue
                    # Search against the better global hand here; the final hand is selected once both floors pair.
                    cost += min(BIG*.35,.35*placement_cost([alt],W,D,self,include_missing=False,best_hand=True,floor_numbers=[floor]))
                if best is None or cost < best[0]:
                    best = (cost, alt)
        return best

    @staticmethod
    def _local(group, context, W, D, g):
        """Cost of one candidate suite: its rooms, air for its bath, doors inside it, wet and pooja neighbours."""
        c = sum(room_cost(r, W, D, g) for r in group)
        keys = {r.key: r for r in group}
        for r in group:
            if r.kind in AIRED and outside(r, W, D) < 600:
                c += 22
            p = keys.get(r.access)
            if p is not None:
                segs = shared(r, p)
                if not segs or max(s[3] - s[2] for s in segs) < r.dw + 300:
                    c += BIG
            if r.kind == 'bathroom':
                for o in context:
                    if shared(r, o):
                        c += 30 if o.kind == 'pooja' else -2
        return c


def placement_matches(floors, W, D, house, mirror=False, floor_numbers=None):
    """Match semantic targets to rooms and measure their centre-to-target distance. Coordinates are normalised by
    the chosen footprint, so a board never supplies or implies millimetres."""
    floor_numbers=floor_numbers if floor_numbers is not None else list(range(len(floors)))
    available=[(floor,r) for floor,rooms in zip(floor_numbers,floors) for r in rooms]
    matches=[];unmatched=[]
    for hint in house.placement:
        candidates=[]
        for floor,r in available:
            if hint.get('floor') is not None and hint['floor']!=floor:continue
            if not house.matches_hint(hint['label'],r):continue
            cx,cy=r.centre();ax=(W-cx if mirror else cx)/max(W,1);ay=cy/max(D,1)
            distance=math.hypot((ax-hint['x'])*4,(ay-hint['y'])*4)
            candidates.append((distance,floor,r,ax,ay))
        if not candidates:
            unmatched.append(hint);continue
        distance,floor,r,ax,ay=min(candidates,key=lambda item:(item[0],item[1],item[2].key))
        matches.append({'hint':hint,'room':r,'floor':floor,'actual_x':ax,'actual_y':ay,'distance_cells':distance})
    return matches,unmatched


def placement_cost(floors, W, D, house, include_missing=True, best_hand=False, mirror=False, floor_numbers=None):
    def one(hand):
        matches,unmatched=placement_matches(floors,W,D,house,hand,floor_numbers)
        total=sum(PLACEMENT_CELL_WEIGHT*(1.5 if m['hint']['source']=='grid' else 1.)*m['distance_cells']**2 for m in matches)
        if include_missing:total += PLACEMENT_MISSING*sum(1.5 if h['source']=='grid' else 1. for h in unmatched)
        return total
    return min(one(False),one(True)) if best_hand else one(mirror)


def placement_audit(house, floors, W, D, mirror):
    matches,unmatched=placement_matches(floors,W,D,house,mirror)
    items=[]
    for m in matches:
        h,r=m['hint'],m['room']
        zone_match=((h['x']>.25 or m['actual_x']<.5) and (h['x']<.75 or m['actual_x']>.5) and
                    (h['y']>.25 or m['actual_y']<.5) and (h['y']<.75 or m['actual_y']>.5))
        items.append({'label':h['label'],'source':h['source'],'target_normalized':[round(h['x'],4),round(h['y'],4)],
                      'actual_normalized':[round(m['actual_x'],4),round(m['actual_y'],4)],
                      'distance_cells':round(m['distance_cells'],3),'floor':m['floor'],
                      'space_id':f'F{m["floor"]}-{r.key}','space_name':r.name,
                      'zone_match':zone_match,
                      'status':'applied' if zone_match and m['distance_cells']<=PLACEMENT_MAX_DISTANCE else 'unsatisfied'})
    distances=[x['distance_cells'] for x in items]
    return {'mode':'spatial_hint','grid_size':[4,4],'front':'row 0 / road edge','dimensions':'planner-determined',
            'matched':items,'unmatched':[h['label'] for h in unmatched],
            'tolerance_cells':PLACEMENT_MAX_DISTANCE,
            'mean_distance_cells':round(sum(distances)/len(distances),3) if distances else None,
            'max_distance_cells':round(max(distances),3) if distances else None}


# ------------------------------------------------------------------------------------------------ search
def grid(lo, hi, step):
    return list(range(lo, hi + 1, step))


def descend(space, f, seed, passes=3):
    """Discrete coordinate descent from a seed; returns (cost, params)."""
    cur = dict(seed)
    cost = f(cur)
    for _ in range(passes):
        improved = False
        for name, values in space.items():
            if len(values) < 2:
                continue
            for val in values:
                if val == cur[name]:
                    continue
                cand = dict(cur)
                cand[name] = val
                c = f(cand)
                if c < cost - 1e-9:
                    cur, cost, improved = cand, c, True
        if not improved:
            break
    return cost, cur


def memo(space, build):
    cache = {}

    def f(p):
        k = tuple(p[n] for n in space)
        if k not in cache:
            res = build(p)
            cache[k] = (BIG * 10, None) if res is None else res
        return cache[k][0]
    return f, cache


def best_floor(space, build, seeds, keep=3, starts=3, passes=3):
    """Screen many seeds (each with its best unit assignment), then descend from the most promising few."""
    f, cache = memo(space, build)
    screened = []
    for seed in seeds:
        for scan in ('ga', 'fa'):
            if scan in space and len(space[scan]) > 1:
                seed = min(({**seed, scan: i} for i in space[scan]), key=f)
        screened.append((f(seed), len(screened), seed))
    screened.sort(key=lambda t: t[:2])
    found = {}
    for _, _, seed in screened[:starts]:
        cost, p = descend(space, f, seed, passes)
        found[tuple(p[n] for n in space)] = (cost, p)
    out = sorted(found.values(), key=lambda t: t[0])[:keep]
    out = [(c, p, cache[tuple(p[n] for n in space)][1]) for c, p in out]
    return [o for o in out if o[2] is not None]


def plan_house(v, W, D):
    """Search the partis for this brief; returns (house, floors of rooms, footprint width and depth, cost, parameters)."""
    # A wide envelope need not be filled edge to edge: try narrower houses that leave a side garden or drive; a deep one
    # may stop short of the rear setback. Every width and depth is screened quickly, the two best searched in full.
    widths = [12600, 11400] if W > 13500 else [W, 11400] if W > 12900 else [W]
    screened = []
    for Wp in widths:
        for Dp, found in plan_width(v, Wp, D, quick=True):
            screened.append((found[3] + (W - Wp) / 300 * 1.2, Wp, Dp))
    screened.sort()
    best = None
    for _, Wp, Dp in screened[:2]:
        for _, found in plan_width(v, Wp, D, only=Dp):
            cost = found[3] + (W - Wp) / 300 * 1.2
            if best is None or cost < best[0]:
                best = (cost, Wp, found)
    if best is None:
        if v.get('_placement_hints'):
            raise DesignError('PLACEMENT_PROGRAMME_DOES_NOT_FIT','The base programme fits, but not with every requested room-placement target in this bounded planner.',
                              {'labels':[h[0] for h in v['_placement_hints']],
                               'advice':'Remove the named room from the guide, move it to a broader zone, or enlarge the buildable area.'})
        raise DesignError('PROGRAMME_DOES_NOT_FIT', 'The rooms of this brief do not fit the buildable area at the minimum sizes '
                          '(NBC-style habitable 9.5 m2 / 2.4 m, kitchen 5 m2, bath 2.8 m2). No extra storey or smaller room was '
                          'invented. Reduce the bedrooms, add a floor, or review the setbacks.')
    cost, Wp, (house, floors, Dp, _, params) = best
    return house, floors, Wp, Dp, cost, params


def plan_width(v, W, D, quick=False, only=None):
    """Best plans of a house W wide, one per footprint depth tried (or only the given depth)."""
    house = House(v, W, D)
    stair = house.stair
    halls = grid(2400, max(2400, W - 2400 - 1200), 150)
    centre = sn((W - 1350) / 2)
    gspace = {
        'gmode': ['three', 'compact'],
        'yF': [STAIR_D] if stair else grid(3000, 5400, 150),
        'fr': [0, 3000, 3300, 3600, 3900],
        'dM': grid(2700, 4800, 150),
        'xk': [2400, 2550, 2700, 2850, 3000, 3300, 3600, 3900, 4200],
        'wd': grid(2700, 4800, 150),
        'right': ['pooja|store', 'pooja', 'toilet', 'pooja|toilet', 'store|toilet', 'study', 'pooja|study'] if v['pooja'] else ['toilet', 'store|toilet', 'study', 'store'],
        'rsplit': [1200, 1500, 1800, 2100],
        'hpos': ['C', 'L', 'R'],
        'wh': [1200, 1350, 1500],
        'xh': halls,
        'ga': list(range(house.ground_combos())),
        's1': [0, -600, -300, 300, 600],
        's2': [0, -600, -300, 300, 600],
    }
    if house.wants_guest(0):gspace['right'] += ['drawing-room']
    base = {'gmode': 'three', 'yF': STAIR_D if stair else 4200, 'fr': 0, 'dM': 3600, 'xk': 3000, 'wd': 3300, 'right': gspace['right'][0],
            'rsplit': 1800, 'hpos': 'C', 'wh': 1350, 'xh': max(STAIR_W if stair else 2400, min(centre, halls[-1])), 'ga': 0, 's1': 0, 's2': 0}

    def near(values, x):
        return min(values, key=lambda q: abs(q - x))
    gseeds = []
    for yF in ([STAIR_D] if stair else sorted({near(gspace['yF'], y) for y in (3450, 3900, 4500)})):
        for dx in ((0, -750, 750) if not stair else (0, 750)):
            xh = near(halls, centre + dx)
            gseeds.append(dict(base, yF=yF, gmode='compact', xh=xh if not stair else max(xh, near(halls, STAIR_W + 200))))
        for dM, xk, wd in ((3600, 3000, 3300), (3000, 2550, 2850), (4200, 3600, 3900)):
            gseeds.append(dict(base, yF=yF, dM=dM, xk=xk, wd=wd))
            gseeds.append(dict(base, yF=yF, dM=dM, xk=xk, wd=wd, right=gspace['right'][2]))
    fspace = {'fxh': [x for x in halls if x >= STAIR_W] or [STAIR_W], 'fwh': [1200, 1350, 1500], 'fa': list(range(len(house.fcombos))),
              'f1': [0, -600, -300, 300, 600], 'f2': [0, -600, -300, 300, 600]}
    fseeds = [{'fxh': near(fspace['fxh'], centre + d), 'fwh': wh, 'fa': 0, 'f1': 0, 'f2': 0} for d in (0, -900, 900) for wh in (1200, 1500)]
    # The house need not fill a deep envelope: try the full depth and depths that fit a generous programme.
    depths = [D]
    rich = house.rich_area()
    for k in ((.92, 1.02, 1.12, 1.3) if rich * 1.3 < W * D / 1e6 else (1.12, 1.3)):
        dp = sn(min(D, rich * k / W * 1e6))
        if dp < D - 450 and dp >= 6300:
            depths.append(dp)
    if only is not None:
        depths = [only]
    kw = {'starts': 1, 'passes': 1, 'keep': 2} if quick else {}
    if quick:
        gseeds, fseeds = gseeds[::3], fseeds[::2]
    results = []
    for Dp in sorted(set(depths), reverse=True):
        grs = best_floor(gspace, lambda p: house.ground(p, Dp), gseeds, **kw)
        if not grs or grs[0][0] >= BIG:
            continue
        pairs = [(g[0]+(placement_cost([g[2]],W,Dp,house,include_missing=True,best_hand=True) if house.placement else 0),g,None) for g in grs]
        if stair:
            house.below = tuple(r for r in grs[0][2] if r.kind in ('kitchen', 'pooja'))
            ups = best_floor(fspace, lambda p: house.upper(p, Dp), fseeds, **kw)
            if not ups or ups[0][0] >= BIG:
                continue
            # The upper search steered clear of the best ground floor's kitchen and pooja; each pairing is costed on
            # what actually lies below it instead.
            pairs = [(g[0] + u[0] - below_cost(u[2], house.below) + stacking_cost(g[2], u[2]) +
                      (placement_cost([g[2],u[2]],W,Dp,house,include_missing=True,best_hand=True) if house.placement else 0) +
                      (5 if studies(g[2]) and studies(u[2]) else 0), g, u)
                     for g in grs for u in ups]
        cost, g, u = min(pairs, key=lambda t: t[0])
        cost += (D - Dp) / 300 * 1.6
        if cost >= BIG and not house.placement:
            continue
        floors = [g[2]] + ([u[2]] if stair else [])
        if house.storeys==3:
            house.below=tuple(r for r in floors[-1] if r.kind in ('kitchen','pooja'))
            second_space={**fspace,'fa':list(range(len(house.upper_combos[2])))}
            seconds=best_floor(second_space,lambda p:house.upper(p,Dp,2),fseeds,**kw)
            if not seconds or seconds[0][0]>=BIG:continue
            second=min(seconds,key=lambda u:u[0]+stacking_cost(floors[-1],u[2])+(placement_cost([u[2]],W,Dp,house,include_missing=False,best_hand=True,floor_numbers=[2]) if house.placement else 0))
            floors.append(second[2]);cost+=second[0]
        params = {**g[1], **(u[1] if u else {}), 'Dp': Dp, 'Wp': W}
        results.append((Dp, (house, floors, Dp, cost, params)))
    return results


def studies(rooms):
    return any(r.kind == 'study' for r in rooms)


def union_polygon(rects):
    geom = unary_union([box(*r) for r in rects]).simplify(0)
    if geom.geom_type != 'Polygon' or geom.interiors:
        raise DesignError('PLAN_SHAPE', 'A planned room is not a single simple polygon.')
    return geom


@lru_cache(maxsize=64)
def _cached(key):
    v = dict(key)
    W = v['width_mm'] - v['left_mm'] - v['right_mm']
    D = v['depth_mm'] - v['front_mm'] - v['rear_mm']
    if v['variant'] == 2:
        D = round(D * .90)
    return plan_house(v, W, D), W, D


def plan_key(v, placement_hints=()):
    fields = ('width_mm', 'depth_mm', 'left_mm', 'right_mm', 'front_mm', 'rear_mm', 'variant', 'storeys', 'bedrooms',
              'attached_baths', 'pooja', 'open_kitchen', 'eldercare', 'style')
    placement=tuple((h['label'],round(float(h['x']),6),round(float(h['y']),6),h.get('source','text'),h.get('floor')) for h in placement_hints)
    return tuple((k, v.get(k)) for k in fields)+(('_placement_hints',placement),)


def vastu_hand(house, floors, W, D, v):
    """Mirror the plan when that puts kitchen, master bedroom and pooja in better Vastu zones for this facing."""
    weight = VASTU_WEIGHT.get(v.get('vastu', 'off'), 0.)
    if not weight:
        return False, 0.
    a = vastu_cost(floors, W, D, v['road_bearing_deg'], False)
    b = vastu_cost(floors, W, D, v['road_bearing_deg'], True)
    return b + 1e-9 < a, min(a, b) * weight


def choose_hand(house, floors, W, D, v):
    """Placement is evaluated before Vastu because it is a direct room-position instruction. Vastu remains a soft
    preference inside the selected brief and breaks close placement ties."""
    weight=VASTU_WEIGHT.get(v.get('vastu','off'),0.)
    scores=[]
    for mirror in (False,True):
        p=placement_cost(floors,W,D,house,include_missing=True,mirror=mirror) if house.placement else 0.
        va=vastu_cost(floors,W,D,v['road_bearing_deg'],mirror)*weight
        scores.append((p+va,mirror,p,va))
    picked=min(scores,key=lambda item:(item[0],item[1]))
    return picked[1],{'unmirrored':round(scores[0][0],3),'mirrored':round(scores[1][0],3),
                      'placement':round(picked[2],3),'vastu':round(picked[3],3)}
