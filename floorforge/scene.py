"""Shared authored geometry for GLB, the live renderer, and external Blender.
No downloaded furniture, protected reference images or image-generation overlays.

The realistic viewer grows planting procedurally from ``vegetation`` records
and synthesises surfaces from each material's ``kind``; GLB/drawings receive
coordination proxies for the same plants.
"""
from __future__ import annotations
import math, random
import numpy as np
import trimesh
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import get_parts
from shapely.affinity import scale as pscale
from .model import sha, STYLES
from .exterior import apply_exterior_preferences, get_exterior_theme, get_interior_theme
from .scene_kit import Kit, extrude, rounded_box, frustum, material_library, SPECIES_HEIGHT

__all__ = ['make_scene', 'glb_bytes', 'transformation', 'extrude', 'rounded_box', 'opening_polygon']


def opening_polygon(w, o, pad=0):
    a = np.array(w['a'], dtype=float); b = np.array(w['b'], dtype=float); u = (b - a) / np.linalg.norm(b - a); n = np.array([-u[1], u[0]])
    p = a + u * (o['offset'] - pad); q = a + u * (o['offset'] + o['width'] + pad); t = w['thickness'] + 300
    return Polygon([p - n * t, q - n * t, q + n * t, p + n * t])


def _parts(geom):
    return [p for p in get_parts(geom) if p.geom_type == 'Polygon' and p.area > 1e-6] if not geom.is_empty else []


def make_scene(building, report):
    b = building if building.get('exterior') else apply_exterior_preferences(building)
    v = b['brief']; exterior = b['exterior']; theme_id = exterior['theme']
    modern = theme_id == 'modern_tropical'
    facade_style = {'warm_modern_minimal': 'minimal', 'tropical_verandah': 'tropical', 'earth_terracotta': 'terracotta',
                    'modern_tropical': 'minimal'}.get(theme_id, v['style'])
    style = {**STYLES[facade_style], **get_exterior_theme(theme_id).get('materials', {})}
    interior_id = exterior.get('interior_theme', 'current')
    interior_theme = get_interior_theme(interior_id)
    H = v['floor_height_mm'] / 1000; fp = Polygon(np.array(b['footprint']) / 1000); plot = Polygon(np.array(b['plot']) / 1000)
    plinth = v['plinth_mm'] / 1000; g = -plinth
    W, D = fp.bounds[2], fp.bounds[3]
    storeys = b['storeys']; top = storeys * H
    # Palette changes must not perturb procedural furniture or planting layout.
    rng_seed = sha({'footprint': b['footprint'], 'spaces': [(s['id'], s['polygon']) for s in b['spaces']], 'seed': v.get('seed', 0)})
    rng = random.Random(int(rng_seed[:12], 16))
    k = Kit(rng)
    materials = material_library(style, interior_theme, modern)
    node, rect, rb, cylinder, ball, beam, poly_mesh = k.node, k.rect, k.rb, k.cylinder, k.ball, k.beam, k.poly_mesh
    cube, cyl, asset = k.cube, k.cyl, k.asset
    lights, colliders, furniture, furnishing = k.lights, k.colliders, k.furniture, k.furnishing
    upgraded_interior = modern or interior_id != 'current'
    M = {  # interior material roles (legacy palette keeps its original assignments)
        'table': 'walnut' if upgraded_interior else 'timber', 'legs': 'oak' if upgraded_interior else 'timber',
        'bedframe': 'oak' if upgraded_interior else 'timber', 'casework': 'oak' if upgraded_interior else 'timber',
        'fronts': 'cabinet' if upgraded_interior else 'wall', 'counter': 'counter' if upgraded_interior else 'stone',
        'tread': 'stairtread' if upgraded_interior else 'stone', 'door': 'oak' if upgraded_interior else 'timber',
        'doorframe': 'doorframe' if upgraded_interior else 'frame',
    }

    xmin, ymin, xmax, ymax = plot.bounds
    hosts = {w['id']: w for w in b['walls']}
    entry = next(o for o in b['openings'] if o['kind'] == 'entry'); ew = hosts[entry['wall_id']]
    u = (np.array(ew['b']) - ew['a']) / math.dist(ew['a'], ew['b']); em = np.array(ew['a']) + u * (entry['offset'] + entry['width'] / 2); ex = em[0] / 1000
    landscape = exterior.get('landscape', {}) or {}
    boundary = landscape.get('boundary', {}) or {}
    features = landscape.get('features', []) if theme_id != 'current' else []
    assemblies = exterior.get('assemblies', []) if theme_id != 'current' else []
    porch_asm = next((a for a in assemblies if a['geometry'].get('kind') == 'porch'), None)
    wall_union = {f: unary_union([Polygon(np.array(w['polygon']) / 1000) for w in b['walls'] if w['floor'] == f]) for f in range(storeys)}
    opening_polys = {f: [] for f in range(storeys)}
    for o in b['openings']:
        opening_polys[o['floor']].append((o, pscale(opening_polygon(hosts[o['wall_id']], o, 60), xfact=.001, yfact=.001, origin=(0, 0))))

    def wall_behind(f, x, y, nx, ny, half, zlo, zhi):
        """A solid wall stretch without openings (between zlo..zhi) behind a wall-mounted item."""
        tx, ty = -ny, nx
        for t in np.linspace(-half, half, 7):
            if not wall_union[f].contains(Point(x + tx * t - nx * .08, y + ty * t - ny * .08)):
                return False
        seg = LineString([(x - tx * half - nx * .08, y - ty * half - ny * .08), (x + tx * half - nx * .08, y + ty * half - ny * .08)])
        for o, poly in opening_polys[f]:
            z0, z1 = o['sill'] / 1000, (o['sill'] + o['height']) / 1000
            if z1 > zlo and z0 < zhi and poly.intersects(seg):
                return False
        return True

    def lining(room, f, z0, z1, mat, role, thickness=.012):
        """Thin wall lining (skirting, wainscot tiles) inside a room, cut at openings overlapping z0..z1."""
        clear = Polygon(np.array(room['clear']) / 1000)
        ring = clear.difference(clear.buffer(-thickness, join_style=2))
        for o, poly in opening_polys[f]:
            oz0, oz1 = o['sill'] / 1000, (o['sill'] + o['height']) / 1000
            if o['kind'] == 'cased' or (oz1 > z0 - f * H and oz0 < z1 - f * H):
                ring = ring.difference(poly)
        for part in _parts(ring):
            poly_mesh(part, z0, z1, mat, f, role, owner=room['id'])

    # ---------------------------------------------------------------- site
    rect((xmin - 9, ymin - 9, g - .13, xmax + 9, ymax + 7, g - .04), 'grass', role='terrain')
    if modern:
        rect((xmin - 9, ymin - 1.6, g - .04, xmax + 9, ymin - .02, g + .1), 'paver', role='site')
        rect((xmin - 9, ymin - 1.76, g - .04, xmax + 9, ymin - 1.6, g + .13), 'step', role='site')
        rect((xmin - 9, ymin - 8.6, g - .1, xmax + 9, ymin - 1.76, g - .02), 'asphalt', role='site')
        for x in np.arange(xmin - 8, xmax + 8, 4.5):
            rect((x, ymin - 5.2, g - .021, x + 2.2, ymin - 5.1, g - .012), 'linen', role='site')
    else:
        rect((xmin - 8, ymin - 6, g - .05, xmax + 8, ymin - .22, g), 'asphalt', role='site')
        rect((xmin - .2, ymin - .25, g - .03, xmax + .2, ymin, g + .11), 'paver', role='site')
        for x in np.arange(xmin - 6, xmax + 8, 4):
            rect((x, ymin - 3.4, g + .003, x + 1.7, ymin - 3.34, g + .01), 'linen', role='site')

    gate_half = 1.1 if not v['parking'] else 1.7
    if modern:
        wt = boundary.get('wall_thickness_mm', 150) / 1000
        fh = boundary.get('front_wall_height_mm', 1500) / 1000
        sh = boundary.get('side_wall_height_mm', 1850) / 1000
        gate_c = boundary.get('gate_center_mm', ex * 1000) / 1000
        gate_w = boundary.get('gate_width_mm', 2600) / 1000
        for xa, ya, xb, yb in [(xmin, ymin, xmin + wt, ymax), (xmax - wt, ymin, xmax, ymax), (xmin, ymax - wt, xmax, ymax)]:
            rect((xa, ya, g, xb, yb, g + sh), 'wall', role='site')
            rect((xa - .012, ya - .012, g + sh, xb + .012, yb + .012, g + sh + .035), 'frame', role='site')
        gx0, gx1 = gate_c - gate_w / 2, gate_c + gate_w / 2
        solid = .95
        for xa, xb in [(xmin, gx0 - .4), (gx1 + .4, xmax)]:
            if xb - xa < .15:
                continue
            rect((xa, ymin, g, xb, ymin + wt, g + solid), 'wall', role='site')
            rect((xa, ymin - .006, g + solid, xb, ymin + wt + .006, g + solid + .03), 'frame', role='site')
            z = g + solid + .075
            while z + .07 <= g + fh + .001:
                rect((xa + .02, ymin + .035, z, xb - .02, ymin + .095, z + .065), 'frame', role='site')
                z += .1
            n = max(1, round((xb - xa) / 3.2))
            for i in range(n + 1):
                px = min(max(xa + (xb - xa) * i / n, xa + .17), xb - .17)
                rect((px - .17, ymin - .03, g, px + .17, ymin + wt + .03, g + fh + .08), 'wall', role='site')
                rect((px - .18, ymin - .04, g + fh + .08, px + .18, ymin + wt + .04, g + fh + .12), 'frame', role='site')
        for side, px in ((-1, gx0 - .2), (1, gx1 + .2)):
            rect((px - .2, ymin - .04, g, px + .2, ymin + wt + .04, g + fh + .35), 'wall', role='site')
            rect((px - .21, ymin - .05, g + fh + .35, px + .21, ymin + wt + .05, g + fh + .39), 'frame', role='site')
            rect((px - .07, ymin - .075, g + fh - .05, px + .07, ymin - .04, g + fh + .08), 'frame', role='fixture')
            rect((px - .05, ymin - .079, g + fh - .03, px + .05, ymin - .075, g + fh + .06), 'lamp', role='fixture')
            k.light((px, ymin - .2, g + fh), 8, kind='pillar')
        rect((gx1 + .06, ymin - .058, g + 1.1, gx1 + .34, ymin - .04, g + 1.28), 'brass', role='detail', name='house-number-plate')
        # Sliding black slatted gate, parked open behind the wall on the longer side.
        slide_left = (gx0 - .4 - xmin) >= gate_w
        gx_a, gx_b = (gx0 - gate_w + .15, gx0 + .1) if slide_left else (gx1 - .1, gx1 + gate_w - .15)
        gy = ymin + wt + .02
        for zz in (g + .06, g + fh - .05):
            rect((gx_a, gy, zz, gx_b, gy + .05, zz + .05), 'frame', role='gate')
        for xx in (gx_a, gx_b - .05):
            rect((xx, gy, g + .06, xx + .05, gy + .05, g + fh), 'frame', role='gate')
        z = g + .16
        while z < g + fh - .1:
            rect((gx_a + .05, gy + .01, z, gx_b - .05, gy + .04, z + .07), 'frame', role='gate')
            z += .105
        rect((min(gx_a, gx0) - .1, ymin + .02, g - .02, max(gx_b, gx1) + .1, ymin + .06, g + .012), 'steel', role='gate')
    else:
        for xa, ya, xb, yb in [(xmin, ymin, xmin + .15, ymax), (xmax - .15, ymin, xmax, ymax), (xmin, ymax - .15, xmax, ymax)]:
            rect((xa, ya, g, xb, yb, .65), 'wall', role='site'); rect((xa - .02, ya - .02, .65, xb + .02, yb + .02, .69), 'stone', role='site')
        for xa, xb in [(xmin, ex - gate_half), (ex + gate_half, xmax)]:
            if xb > xa:
                rect((xa, ymin, g, xb, ymin + .18, .72), 'wall', role='site')
                rect((xa, ymin - .02, .72, xb, ymin + .2, .78), 'stone', role='site')
        for x in (ex - gate_half - .08, ex + gate_half + .08):
            rect((x - .11, ymin - .04, g, x + .11, ymin + .24, 1.05), 'stone', role='site')
        # Gate leaves shown open into the court, never a closed gate across the arrival route.
        for side in (-1, 1):
            x = ex + side * gate_half
            for y in np.arange(ymin + .2, ymin + 1.7, .16):
                rect((x - .025, y, g + .17, x + .025, y + .055, .95), 'frame', role='gate')
            for z in (g + .25, .83):
                rect((x - .032, ymin + .17, z, x + .032, ymin + 1.8, z + .05), 'frame', role='gate')
        rect((ex - 1.1, ymin + .2, g, ex + 1.1, -.75, g + .02), 'paver', role='court')
        for y in np.arange(ymin + .8, -1, .65):
            rect((ex - .93, y, g + .022, ex + .93, y + .48, g + .039), 'stone', role='court')
        for x in (xmin + .55, xmax - .55):
            for y in np.arange(ymin + 1.1, ymax - .6, 1.65):
                k.plant(x, y, g, 'shrub_round', height=.55, pot=(.13, .21, 'ceramic'))
        if v['front_mm'] >= 2500:
            for x in (max(xmin + 1.3, ex - 3), min(xmax - 1.3, ex + 3)):
                k.plant(x, ymin + 1.8, g, 'tree_standard', height=2.6)

    # ---------------------------------------------------------------- plinth, entry steps
    poly_mesh(fp, -plinth, -.15, 'basalt' if modern else 'stone', role='plinth')
    if modern:
        poly_mesh(fp.buffer(.015, join_style=2).difference(fp), g, 0, 'basalt', role='plinth', name='plinth-band')
    if not (modern and porch_asm):
        steps = max(1, math.ceil(plinth / .15))
        for i in range(steps):
            y0 = -.3 * (steps - i); y1 = y0 + .3
            rect((ex - 1.0, y0, -plinth, ex + 1., y1, -plinth + (i + 1) * plinth / steps), 'step' if modern else 'stone', role='step')

    # ---------------------------------------------------------------- slabs, finishes, ceilings
    stair_holes = {}
    for f in range(storeys):
        level = f * H; slab = fp
        if f:
            st = b['stairs'][f]; sx = st['x'] / 1000; sy = st['y'] / 1000
            stair_holes[f] = box(sx, sy + 1.05, sx + st['width'] / 1000, sy + st['depth'] / 1000)
            slab = slab.difference(stair_holes[f])
        poly_mesh(slab, level - .15, level, 'slab', f, 'floor', f'F{f}-floor')
        for s in [s for s in b['spaces'] if s['floor'] == f and s['kind'] != 'stair']:
            p = Polygon(np.array(s['clear']) / 1000)
            mat = 'woodfloor' if s['kind'] in ('bedroom', 'study') else 'wetfloor' if s['kind'] in ('bathroom', 'utility') else 'deck' if (s['kind'] == 'terrace' and modern) else 'floor'
            poly_mesh(p, level + .002, level + .009, mat, f, 'finish', s['id'] + '/floor', s['id'])
        # Ceiling coves with a concealed warm glow line.
        for s in [s for s in b['spaces'] if s['floor'] == f and s['kind'] in ('living', 'family', 'bedroom', 'dining')]:
            p = Polygon(np.array(s['clear']) / 1000); inner = p.buffer(-.16)
            if inner.is_empty:
                continue
            ring = p.difference(inner)
            poly_mesh(ring, level + H - .35, level + H - .22, 'ceiling', f, 'ceiling')
            glow = inner.boundary.buffer(.008).intersection(p)
            poly_mesh(glow, level + H - .257, level + H - .247, 'lamp', f, 'cove')
    roof_fp = fp
    terraces = [Polygon(np.array(s['polygon']) / 1000) for s in b['spaces'] if s['floor'] == storeys - 1 and s['kind'] == 'terrace']
    for terrace in terraces:
        roof_fp = roof_fp.difference(terrace)
    for f in range(storeys):
        ceil = roof_fp if f == storeys - 1 else fp.difference(stair_holes.get(f + 1, Polygon()))
        poly_mesh(ceil, (f + 1) * H - .157, (f + 1) * H - .151, 'ceiling', f, 'ceiling', f'F{f}-ceiling')

    # ---------------------------------------------------------------- roof
    poly_mesh(roof_fp, top - .15, top, 'roof', storeys - 1, 'roof', 'roof-slab')
    if modern:
        over = roof_fp.buffer(.45, join_style=2)
        for terrace in terraces:
            over = over.difference(terrace)
        poly_mesh(over.difference(roof_fp), top - .15, top + .22, 'roof', storeys - 1, 'fascia', 'roof-overhang')
        poly_mesh(roof_fp.difference(roof_fp.buffer(-.22, join_style=2)), top, top + .22, 'roof', storeys - 1, 'parapet', 'roof-upstand')
        for f in range(1, storeys):
            band = fp.buffer(.1, join_style=2).difference(fp)
            poly_mesh(band, f * H - .25, f * H - .02, 'roof', f - 1, 'band', f'F{f}-slab-band')
    else:
        parapet = roof_fp.difference(roof_fp.buffer(-.15))
        poly_mesh(parapet, top, top + .6, 'wall', storeys - 1, 'roof', 'parapet')
        poly_mesh(fp.buffer(.025).difference(fp.buffer(-.175)), top + .60, top + .65, 'stone', storeys - 1, 'roof', 'coping')

    # ---------------------------------------------------------------- walls (true voids, split at sill/lintel)
    # Wall polygons overlap at corners and T-junctions. Each storey's walls are tiled instead: external walls
    # claim junctions first and later walls keep only what is still unfilled, so no two solids share a face
    # (coincident faces shade black in path tracers and z-fight in other viewers). Colliders keep full polygons.
    tiled = {}
    for f in range(storeys):
        taken = Polygon()
        for w in sorted((w for w in b['walls'] if w['floor'] == f), key=lambda w: not w['external']):
            full = Polygon(np.array(w['polygon']) / 1000)
            own = full.difference(taken) if not taken.is_empty else full
            tiled[w['id']] = unary_union([q for q in get_parts(own) if q.geom_type == 'Polygon' and q.area > 1e-5])
            taken = taken.union(full)
    for w in b['walls']:
        openings = [o for o in b['openings'] if o['wall_id'] == w['id']]
        wp = tiled.get(w['id'], Polygon(np.array(w['polygon']) / 1000)); cuts = {0, w['height'] / 1000}
        for o in openings:
            cuts.update((o['sill'] / 1000, (o['sill'] + o['height']) / 1000))
        cuts = sorted(cuts)
        for i, (z0, z1) in enumerate(zip(cuts, cuts[1:])):
            geom = wp; mid = (z0 + z1) * 500
            for o in openings:
                if o['sill'] <= mid <= o['sill'] + o['height']:
                    geom = geom.difference(pscale(opening_polygon(w, o), xfact=.001, yfact=.001, origin=(0, 0)))
            poly_mesh(geom, z0 + w['floor'] * H, z1 + w['floor'] * H, 'wall', w['floor'], 'wall', f'{w["id"]}/{i}', w['id'])
        cp = Polygon(np.array(w['polygon']) / 1000)
        for o in openings:
            if o['kind'] != 'window':
                cp = cp.difference(pscale(opening_polygon(w, o, 10), xfact=.001, yfact=.001, origin=(0, 0)))
        for j, p in enumerate(get_parts(cp)):
            if p.geom_type == 'Polygon':
                colliders.append({'id': w['id'] + f'/{j}', 'floor': w['floor'], 'polygon': [[float(x), float(y)] for x, y in list(p.exterior.coords)[:-1]], 'kind': 'wall'})

    # ---------------------------------------------------------------- openings
    space_kind = {s['id']: s['kind'] for s in b['spaces']}
    for o in b['openings']:
        w = hosts[o['wall_id']]; a = np.array(w['a']) / 1000; bb = np.array(w['b']) / 1000; uv = (bb - a) / np.linalg.norm(bb - a); nv = np.array([-uv[1], uv[0]]); ang = math.atan2(uv[1], uv[0]); p = a + uv * o['offset'] / 1000
        if not fp.covers(Point(*(p + uv * o['width'] / 2000 + nv * .4))):
            nv = -nv
        base = o['floor'] * H; ow = o['width'] / 1000; z0 = base + o['sill'] / 1000; zh = o['height'] / 1000
        t_half = w['thickness'] / 2000

        def part(x, depth, z, sx, sy, sz, mat='frame', role='joinery'):
            q = p + uv * x + nv * depth
            node(cube, mat, (q[0], q[1], z), (sx, sy, sz), (0, 0, ang), o['floor'], role, owner=o['id'])
        if o['kind'] == 'cased':
            continue
        room_kinds = [space_kind.get(room, 'secondary') for room in w['rooms']]
        if o['kind'] == 'window' and modern:
            # Slim black aluminium: perimeter frame, mullions every ~1.25 m, staggered sliding panes.
            fw = .045
            part(fw / 2, 0, z0 + zh / 2, fw, .075, zh); part(ow - fw / 2, 0, z0 + zh / 2, fw, .075, zh)
            part(ow / 2, 0, z0 + zh - fw / 2, ow, .075, fw); part(ow / 2, 0, z0 + fw / 2, ow, .075, fw)
            panels = max(1, math.ceil(ow / 1.25))
            for i in range(1, panels):
                part(ow * i / panels, 0, z0 + zh / 2, .04, .075, zh - 2 * fw)
            if zh > 2.4:
                part(ow / 2, 0, z0 + 2.12, ow - 2 * fw, .075, .04)
            for i in range(panels):
                part(ow * (i + .5) / panels, (i % 2) * .028 - .014, z0 + zh / 2, ow / panels - .04, .012, zh - 2 * fw, 'glass', 'glass')
            if o['sill'] > 100 and w['external']:
                part(ow / 2, -t_half - .03, z0 - .015, ow + .06, .09, .03, 'frame', 'sill')
                part(ow / 2, t_half - .05, z0 - .02, ow, .14, .03, M['counter'], 'sill')
            if w['external'] and 'bedroom' in room_kinds and zh < 2.6:
                # Projecting box-frame surround gives the bedroom glazing depth and shadow.
                clad = 'timber' if o['floor'] % 2 else 'roof'
                d = .32
                part(-.06, -t_half - d / 2, z0 + zh / 2, .12, d, zh + .24, clad, 'window-surround')
                part(ow + .06, -t_half - d / 2, z0 + zh / 2, .12, d, zh + .24, clad, 'window-surround')
                part(ow / 2, -t_half - d / 2, z0 + zh + .06, ow + .24, d, .12, clad, 'window-surround')
                part(ow / 2, -t_half - d / 2, z0 - .06, ow + .24, d, .12, clad, 'window-surround')
        elif o['kind'] == 'window':
            part(.025, 0, z0 + zh / 2, .05, .10, zh); part(ow - .025, 0, z0 + zh / 2, .05, .10, zh)
            part(ow / 2, 0, z0 + zh - .025, ow - .1, .10, .05)
            part(ow / 2, 0, z0 + .025, ow - .1, .10, .05)
            part(ow / 2, 0, z0 + zh / 2, ow - .1, .015, zh - .1, 'glass', 'glass')
            if ow > 1.2:
                part(ow / 2, 0, z0 + zh / 2, .035, .08, zh)
            part(ow / 2, 0, z0 - .045, ow + .16, .4, .07, 'stone', 'sill')
            if w['external']:
                part(ow / 2, -.18, z0 + zh + .12, ow + .3, .7, .10, 'roof', 'shade')
                surround = 'stone' if set(room_kinds).intersection({'living', 'family', 'dining'}) else 'frame'
                part(-.08, -.08, z0 + zh / 2, .10, .18, zh + .18, surround, 'window-surround')
                part(ow + .08, -.08, z0 + zh / 2, .10, .18, zh + .18, surround, 'window-surround')
                if set(room_kinds).intersection({'living', 'family', 'dining'}):
                    part(ow / 2, -.32, z0 + zh + .17, ow + .46, .52, .10, 'stone', 'window-hood')
                elif zh > 1.0:
                    part(ow / 2, -.25, z0 + zh + .13, ow + .28, .34, .075, 'roof', 'window-hood')
        if o['kind'] == 'window':
            # Pleated sheer curtains on the room side.
            if zh > 1. and not ('bathroom' in room_kinds or 'utility' in room_kinds):
                for edge in (.12, ow - .12):
                    verts = []; fs = []
                    for j in range(17):
                        xx = edge - .16 + j * .02; yy = .19 + .028 * math.cos(j * math.pi / 2)
                        q = p + uv * xx + nv * yy
                        verts.extend([(q[0], q[1], max(base + .01, z0 - .02)), (q[0], q[1], min(base + H - .2, z0 + zh + .08))])
                    for j in range(16):
                        kk = j * 2; fs.extend([[kk, kk + 1, kk + 3], [kk, kk + 3, kk + 2]])
                    node(asset(trimesh.Trimesh(vertices=verts, faces=fs, process=False), smooth=True), 'linen', floor=o['floor'], role='curtain', owner=o['id'])
            continue
        frame_mat = 'frame' if (o['kind'] in ('entry', 'glazed') or not upgraded_interior) else M['doorframe']
        part(.025, 0, z0 + zh / 2, .05, .10, zh, frame_mat); part(ow - .025, 0, z0 + zh / 2, .05, .10, zh, frame_mat)
        part(ow / 2, 0, z0 + zh - .025, ow - .1, .10, .05, frame_mat)
        if o['kind'] == 'glazed':
            # A partly-open sliding glass leaf, not an opaque balcony door.
            part(ow * .74, 0, z0 + zh / 2, ow * .47, .018, zh - .1, 'glass', 'glass')
            for xx in (ow * .505, ow - .04):
                part(xx, 0, z0 + zh / 2, .035, .07, zh - .04)
            part(ow * .74, 0, z0 + .025, ow * .48, .07, .05)
        else:
            # Leaves shown open 90 degrees; no invisible solid wall remains in the portal.
            hinge = p + uv * .055; leafcenter = hinge + nv * (ow - .1) / 2
            leaf_mat = 'walnut' if (o['kind'] == 'entry' and upgraded_interior) else M['door']
            rb((leafcenter[0], leafcenter[1], base + zh / 2), (.042, ow - .1, zh - .05), leaf_mat, o['floor'], 'door', .008, ang, owner=o['id'])
            knob = hinge + nv * (ow - .18)
            if upgraded_interior:
                if o['kind'] == 'entry':
                    for side in (-1, 1):
                        q = knob + uv * .05 * side
                        beam((q[0], q[1], base + .75), (q[0], q[1], base + 1.75), .014, 'frame', o['floor'], 'door')
                else:
                    for side in (-1, 1):
                        q = knob + uv * .045 * side
                        beam((q[0], q[1], base + 1.02), (q[0] + nv[0] * .12, q[1] + nv[1] * .12, base + 1.02), .009, 'frame', o['floor'], 'door')
            else:
                ball((knob[0] + uv[0] * .04, knob[1] + uv[1] * .04, base + 1.), (.035, .035, .035), 'brass', o['floor'], 'door')

    # ---------------------------------------------------------------- furniture
    def lamp(x, y, z, f, pendant=False):
        if pendant:
            beam((x, y, z), (x, y, f * H + H - .16), .006, 'frame', f, 'fixture')
            shade = trimesh.creation.cone(radius=.23, height=.18, sections=28)
            node(asset(shade, smooth=True), 'frame' if upgraded_interior else 'timber', (x, y, z), rot=(math.pi, 0, 0), floor=f, role='fixture')
            ball((x, y, z - .06), (.07, .07, .07), 'lamp', f, 'fixture')
        else:
            cylinder((x, y, z + .015), .11, .03, 'brass', f, 'fixture'); beam((x, y, z + .03), (x, y, z + .31), .014, 'brass', f, 'fixture')
            cylinder((x, y, z + .35), .16, .21, 'linen', f, 'fixture'); ball((x, y, z + .32), (.05, .05, .05), 'lamp', f, 'fixture')
        k.light((x, y, z - .04 if pendant else z + .33), 35 if pendant else 12, kind='pendant' if pendant else 'lamp')

    def chandelier(x, y, f):
        """Branching globe pendant (warm glass spheres on black stems)."""
        zc = f * H + H - .16
        hub = zc - .62
        beam((x, y, hub), (x, y, zc), .008, 'frame', f, 'fixture')
        for i in range(7):
            a = i * 2 * math.pi / 7 + .3
            r = .22 + .12 * (i % 2)
            dz = -.08 - .11 * ((i * 3) % 4) / 3
            end = (x + math.cos(a) * r, y + math.sin(a) * r, hub + dz)
            beam((x, y, hub), end, .006, 'frame', f, 'fixture')
            ball(end, (.095, .095, .095), 'globe', f, 'fixture')
        k.light((x, y, hub - .12), 45, kind='chandelier')

    def chair(x, y, z, f, rot=0):
        c, s = math.cos(rot), math.sin(rot)
        def p(a, b2, zz): return (x + a * c - b2 * s, y + a * s + b2 * c, z + zz)
        for a in (-.20, .20):
            for bb in (-.19, .19):
                beam(p(a, bb, .04), p(a * .88, bb * .88, .43), .021, M['legs'], f, 'furniture')
        rb(p(0, 0, .46), (.48, .49, .09), 'fabric', f, r=.04, rot=rot)
        for a in (-.20, .20):
            beam(p(a, .20, .43), p(a, .24, .85), .02, M['legs'], f, 'furniture')
        rb(p(0, .23, .74), (.50, .085, .26), 'fabric', f, r=.035, rot=rot)

    def downlights(room, f, z):
        p = Polygon(np.array(room['clear']) / 1000)
        x0, y0, x1, y1 = p.bounds
        nx = max(1, round((x1 - x0 - .9) / 1.5) + 1); ny = max(1, round((y1 - y0 - .9) / 1.5) + 1)
        placed = 0
        for i in range(nx):
            for j in range(ny):
                xx = x0 + .6 + (x1 - x0 - 1.2) * (i / (nx - 1) if nx > 1 else .5)
                yy = y0 + .6 + (y1 - y0 - 1.2) * (j / (ny - 1) if ny > 1 else .5)
                if not p.buffer(-.35).contains(Point(xx, yy)):
                    continue
                cylinder((xx, yy, z - .006), .05, .008, 'frame', f, 'downlight')
                cylinder((xx, yy, z - .011), .038, .004, 'lamp', f, 'downlight')
                placed += 1
                if placed % 2 == 1:
                    k.light((xx, yy, z - .2), 9, kind='downlight')

    for room in b['spaces']:
        f = room['floor']; z = f * H; p = Polygon(np.array(room['clear']) / 1000)
        kind = room['kind']
        if kind not in ('stair', 'terrace'):
            lining(room, f, z + .009, z + .09, 'skirting', 'skirting')
            downlights(room, f, z + H - .157)
        layout_rect = box(*p.bounds)
        if not p.buffer(1e-6).covers(layout_rect):
            # Furnish the largest contained axis-aligned rectangle, never an L-room bounding box.
            xs = sorted(set(round(x, 6) for x, y in p.exterior.coords)); ys = sorted(set(round(y, 6) for x, y in p.exterior.coords))
            candidates = sorted(((x1 - x0) * (y1 - y0), (x0, y0, x1, y1)) for i, x0 in enumerate(xs) for x1 in xs[i + 1:] for j, y0 in enumerate(ys) for y1 in ys[j + 1:])
            layout_rect = None
            for _, bounds in reversed(candidates):
                q = box(*bounds)
                if p.buffer(1e-5).covers(q):
                    layout_rect = q; break
            if layout_rect is None:
                continue
        x0, y0, x1, y1 = layout_rect.bounds; rw = x1 - x0; rd = y1 - y0; cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
        if kind in ('stair', 'hall', 'terrace'):
            continue
        if kind == 'bedroom':
            bw = 1.6; bl = 2.; bx = x0 + max(.25, (rw - bw) / 2 - .2); by = y0 + .20
            rect((bx, by, z + .07, bx + bw, by + bl, z + .28), M['bedframe'], f, 'furniture', owner=room['id'])
            rb((bx + bw / 2, by + bl / 2, z + .39), (bw + .04, bl + .03, .25), 'linen', f, r=.075, owner=room['id'])
            rb((bx + bw / 2, by - .035, z + .7), (bw + .35, .14, 1.25), 'fabric-dark', f, r=.06)
            if upgraded_interior and wall_behind(f, bx + bw / 2, y0, 0, 1, 1.45, .05, 2.55):
                # Full-width timber wall panel behind the bed.
                for j, xx in enumerate(np.arange(bx + bw / 2 - 1.42, bx + bw / 2 + 1.42, .085)):
                    rect((xx, y0 + .003, z + .1, xx + .06, y0 + .028, z + 2.55), M['casework'], f, 'wall-panel')
            for px in (bx + .40, bx + 1.20):
                rb((px, by + .38, z + .58), (.68, .42, .17), 'linen', f, r=.07, rot=.035)
            # Soft draped duvet with geometric folds rather than a solid block.
            vv = []; ff = []; nx = 22; ny = 24
            for j in range(ny):
                for i in range(nx):
                    xx = bx - .055 + (bw + .11) * i / (nx - 1); yy = by + .68 + (bl - .58) * j / (ny - 1)
                    zz = z + .54 + .014 * math.cos(i * .9 + j * .25) + .007 * math.sin(i * 1.8)
                    if i in (0, nx - 1):
                        zz -= .13
                    vv.append((xx, yy, zz))
            for j in range(ny - 1):
                for i in range(nx - 1):
                    kk = j * nx + i; ff += [[kk, kk + 1, kk + nx + 1], [kk, kk + nx + 1, kk + nx]]
            node(asset(trimesh.Trimesh(vertices=vv, faces=ff, process=False), smooth=True), 'fabric', floor=f, role='furniture')
            for side in (-1, 1):
                xx = bx - .30 if side == -1 else bx + bw + .30
                if x0 + .20 < xx < x1 - .2:
                    rb((xx, by + .22, z + .31), (.43, .45, .48), M['casework'], f, r=.014); lamp(xx, by + .22, z + .56, f)
            # Wardrobe with recessed plinth, visible frame, separate front leaves and rails.
            wx = x0 + .05; wy = y1 - .64; ww = min(1.7, rw - .1)
            for aa, bb2, cc, dd in [(wx, wy, wx + .035, wy + .6), (wx + ww - .035, wy, wx + ww, wy + .6), (wx, wy + .565, wx + ww, wy + .6)]:
                rect((aa, bb2, z + .08, cc, dd, z + 2.25), M['casework'], f, 'furniture')
            rect((wx, wy, z + 2.22, wx + ww, wy + .6, z + 2.26), M['casework'], f, 'furniture')
            for j in range(3):
                aa = wx + j * ww / 3 + .012; rect((aa, wy, z + .12, aa + ww / 3 - .024, wy + .035, z + 2.21), M['casework'], f, 'furniture')
                beam((aa + ww / 3 - .07, wy - .018, z + .9), (aa + ww / 3 - .07, wy - .018, z + 1.2), .008, 'frame' if upgraded_interior else 'brass', f, 'furniture')
            furnishing('bed', room, box(bx - .05, by - .12, bx + bw + .05, by + bl + .04))
            furnishing('wardrobe', room, box(wx, wy, wx + ww, wy + .6))
            rect((bx - .32, by + .65, z + .012, bx + bw + .32, min(by + bl + .45, y1 - .65), z + .018), 'rug', f, 'rug')
            if upgraded_interior and x1 - (bx + bw + .3) > .75 and y1 - .64 - (by + bl) > .2:
                k.plant(x1 - .38, wy - .42, z, 'monstera', height=.95, f=f, pot=(.19, .36, 'planter'))
        elif kind in ('living', 'family'):
            # Position along the right wall so the entry axis remains open.
            sy = y0 + .28; sx = x1 - .9; length = min(2.35, rd - .5)
            if length > 1.5:
                rb((sx + .2, sy + length / 2, z + .25), (.92, length, .28), 'fabric', f, r=.07)
                rb((sx + .57, sy + length / 2, z + .65), (.20, length, .74), 'fabric', f, r=.06)
                for end in (sy + .08, sy + length - .08):
                    rb((sx + .16, end, z + .55), (.9, .18, .50), 'fabric', f, r=.06)
                for j in range(3):
                    yy = sy + .26 + j * (length - .50) / 3
                    rb((sx + .1, yy + (length - .50) / 6, z + .46), (.69, (length - .54) / 3, .20), 'linen', f, r=.055)
                for j in (0, 1):
                    ball((sx + .18, sy + .5 + j * max(.6, length - 1.), z + .69), (.15, .27, .25), 'fabric-dark', f, 'furniture', (.2, .2, 0))
                for yy in (sy + .2, sy + length - .2):
                    cylinder((sx + .16, yy, z + .085), .025, .17, 'brass', f, 'furniture')
                furnishing('sofa', room, box(sx - .28, sy - .02, sx + .69, sy + length + .02))
                tx = sx - 1.0; ty = sy + length * .53
                rb((tx, ty, z + .36), (.75, 1.1, .06), M['counter'] if upgraded_interior else 'stone', f, r=.09)
                for xx in (tx - .22, tx + .22):
                    cylinder((xx, ty, z + .18), .045, .33, M['table'], f, 'furniture')
                furnishing('coffee-table', room, box(tx - .375, ty - .55, tx + .375, ty + .55))
                rect((max(x0 + .12, tx - 1), max(y0 + .06, sy - .15), z + .014, x1 - .1, min(y1 - .06, sy + length + .15), z + .022), 'rug', f, 'rug')
                # Books and a hollow ceramic vessel.
                rect((tx - .22, ty - .28, z + .394, tx + .06, ty - .08, z + .427), 'linen', f, 'detail')
                vessel = trimesh.creation.revolve(np.array([[.055, 0], [.08, .08], [.075, .16], [.055, .18], [.045, .18], [.064, .15], [.068, .08], [.04, .015]]), sections=24)
                node(asset(vessel, smooth=True), 'ceramic', (tx + .13, ty + .1, z + .394), floor=f, role='detail')
                if upgraded_interior:
                    # Media wall opposite the sofa: timber slats, floating console, screen.
                    mid = sy + length / 2
                    if wall_behind(f, x0, mid, 1, 0, 1.25, .2, 2.6) and tx - .375 - x0 > 1.2:
                        for j, yy in enumerate(np.arange(mid - 1.22, mid + 1.22, .075)):
                            rect((x0 + .003, yy, z + .09, x0 + .03, yy + .05, z + 2.62), 'walnut', f, 'wall-panel')
                        rect((x0 + .035, mid - .95, z + .26, x0 + .45, mid + .95, z + .6), 'walnut', f, 'furniture')
                        rect((x0 + .045, mid - .73, z + 1.02, x0 + .085, mid + .73, z + 1.84), 'blackglass', f, 'detail')
                        rect((x0 + .037, mid - .74, z + 1.01, x0 + .045, mid + .74, z + 1.85), 'frame', f, 'detail')
                        furnishing('media-console', room, box(x0 + .035, mid - .95, x0 + .45, mid + .95))
                    if wall_behind(f, x1, mid, -1, 0, .75, 1.25, 2.25):
                        rect((x1 - .045, mid - .72, z + 1.3, x1 - .005, mid + .72, z + 2.22), 'frame', f, 'art')
                        rect((x1 - .05, mid - .68, z + 1.34, x1 - .042, mid + .68, z + 2.18), 'art', f, 'art')
                    # Arc floor lamp beside the sofa.
                    fx, fy = sx + .2, sy - .2 if sy - .2 > y0 + .2 else sy + length + .2
                    if y0 + .2 < fy < y1 - .2:
                        cylinder((fx, fy, z + .02), .16, .04, 'basalt', f, 'furniture')
                        beam((fx, fy, z + .04), (fx, fy, z + 1.55), .012, 'frame', f, 'furniture')
                        beam((fx, fy, z + 1.55), (fx - .75, fy, z + 1.9), .012, 'frame', f, 'furniture')
                        shade = trimesh.creation.cone(radius=.2, height=.2, sections=28)
                        node(asset(shade, smooth=True), 'frame', (fx - .8, fy, z + 1.78), rot=(math.pi, 0, 0), floor=f, role='fixture')
                        ball((fx - .8, fy, z + 1.74), (.05, .05, .05), 'lamp', f, 'fixture')
                        k.light((fx - .8, fy, z + 1.7), 18, kind='lamp')
                        furnishing('floor-lamp', room, box(fx - .18, fy - .18, fx + .18, fy + .18))
            if rd > 3.4:
                chair(x0 + .9, y1 - 1.1, z, f, -.45)
            if rw > 3 and rd > 3:
                k.plant(x0 + .38, y1 - .4, z, 'fiddle_leaf' if upgraded_interior else 'monstera', height=1.65 if upgraded_interior else .8, f=f,
                        pot=(.21, .44, 'planter' if upgraded_interior else 'ceramic'))
            lamp(cx, y0 + rd * .52, z + H - .9, f, True)
        elif kind == 'dining':
            # Keep left route to kitchen/stair clear.
            tx = x0 + rw * .62; ty = y0 + rd * .48; tw = min(1.7, rw * .48); td = .85
            rb((tx, ty, z + .75), (tw, td, .07), M['table'], f, r=.035)
            for xx in (-tw * .35, tw * .35):
                for yy in (-.26, .26):
                    beam((tx + xx, ty + yy, z + .04), (tx + xx, ty + yy, z + .72), .038, M['table'], f, 'furniture')
            for xx in (-tw * .27, tw * .27):
                chair(tx + xx, ty - .67, z, f, math.pi); chair(tx + xx, ty + .67, z, f, 0)
            furnishing('dining-set', room, box(tx - tw / 2 - .1, ty - .92, tx + tw / 2 + .1, ty + .92))
            for xx in (-tw * .25, tw * .25):
                for yy in (-.22, .22):
                    cylinder((tx + xx, ty + yy, z + .798), .115, .013, 'ceramic', f, 'detail')
                    cylinder((tx + xx + .15, ty + yy, z + .84), .034, .09, 'glass', f, 'detail')
            if upgraded_interior:
                chandelier(tx, ty, f)
            else:
                lamp(tx, ty, z + 2.20, f, True)
        elif kind == 'kitchen':
            # Real counter runs on non-circulation edges; separate fronts and handles.
            dep = .6; run = max(1.8, rw - .15); ky = y0 + .08
            fridge = upgraded_interior and run > 2.7
            base_run = run - .78 if fridge else run
            nseg = max(2, int(base_run / .6))
            for j in range(nseg):
                xx = x0 + .07 + j * base_run / nseg; ww = base_run / nseg
                rect((xx, ky, z + .10, xx + ww - .02, ky + dep, z + .83), M['casework'], f, 'furniture')
                for zz in (.30, .59):
                    rect((xx + .02, ky + dep, z + zz, xx + ww - .035, ky + dep + .022, z + zz + .20), M['fronts'], f, 'furniture')
                    beam((xx + .14, ky + dep + .04, z + zz + .15), (xx + ww - .14, ky + dep + .04, z + zz + .15), .007, 'frame', f, 'detail')
            rect((x0 + .04, ky - .02, z + .83, x0 + base_run + .10, ky + dep + .06, z + .87), M['counter'], f, 'furniture')
            if fridge:
                fx0 = x0 + .07 + base_run + .02
                rect((fx0, ky, z + .02, fx0 + .72, ky + dep + .05, z + 1.95), 'appliance', f, 'furniture')
                beam((fx0 + .06, ky + dep + .08, z + 1.0), (fx0 + .06, ky + dep + .08, z + 1.6), .01, 'frame', f, 'detail')
            # Sink opening represented with a real hollow vessel above an open inset.
            basin = trimesh.creation.revolve(np.array([[.07, 0], [.20, .04], [.25, .11], [.25, .14], [.23, .15], [.22, .12], [.18, .06], [.07, .025]]), sections=32)
            node(asset(basin, smooth=True), 'appliance' if upgraded_interior else 'frame', (x0 + base_run * .7, ky + .32, z + .865), floor=f, role='detail')
            beam((x0 + base_run * .7, ky + .1, z + .88), (x0 + base_run * .7, ky + .1, z + 1.17), .012, 'brass', f, 'detail')
            beam((x0 + base_run * .7, ky + .1, z + 1.17), (x0 + base_run * .7, ky + .28, z + 1.17), .012, 'brass', f, 'detail')
            if upgraded_interior:
                rect((x0 + .16, ky + .08, z + .87, x0 + .76, ky + .56, z + .877), 'blackglass', f, 'detail')
            for xx in (.3, .59):
                for yy in (.18, .42):
                    cylinder((x0 + xx, ky + yy, z + .88), .095, .016, 'frame', f, 'detail')
            if upgraded_interior and wall_behind(f, x0 + .07 + base_run / 2, y0, 0, 1, base_run / 2 - .05, .9, 2.3):
                rect((x0 + .07, y0 + .002, z + .87, x0 + .07 + base_run, y0 + .014, z + 1.5), 'tilewall', f, 'wall-tile')
                for j in range(nseg):
                    xx = x0 + .07 + j * base_run / nseg; ww = base_run / nseg
                    rect((xx, y0 + .015, z + 1.52, xx + ww - .015, y0 + .37, z + 2.28), M['fronts'], f, 'furniture')
                rect((x0 + .07, y0 + .015, z + 1.505, x0 + .07 + base_run, y0 + .34, z + 1.515), 'lamp', f, 'fixture')
                k.light((x0 + .07 + base_run / 2, y0 + .3, z + 1.4), 12, kind='undercabinet')
            else:
                rect((x0 + .15, ky + .08, z + 1.60, x0 + .92, ky + .5, z + 1.7), 'appliance' if upgraded_interior else 'frame', f, 'detail')
            furnishing('kitchen-run', room, box(x0 + .04, ky - .02, x0 + run + .10, ky + dep + .06))
            if rd > 2.8 and rw > 3.5:
                ix = x0 + rw * .57; iy = y1 - .95
                rect((ix - .70, iy - .30, z + .10, ix + .70, iy + .30, z + .86), M['casework'], f, 'furniture')
                rb((ix, iy, z + .885), (1.48, .72, .055), M['counter'], f, r=.016)
                furnishing('island', room, box(ix - .74, iy - .36, ix + .74, iy + .36))
                if upgraded_interior:
                    for xx in (ix - .45, ix + .45):
                        lamp(xx, iy, z + 1.75, f, True)
        elif kind == 'bathroom':
            # Wall-side vanity with hollow basin, faucet and mirror frame.
            vx = x1 - .80; vy = y1 - .52
            if upgraded_interior:
                lining(room, f, z + .009, z + 1.55, 'tilewall', 'wall-tile', .01)
            rect((vx - .33, vy - .22, z + .20, vx + .33, vy + .22, z + .77), 'walnut' if upgraded_interior else 'timber', f, 'furniture')
            rb((vx, vy, z + .79), (.72, .50, .045), M['counter'], f, r=.02)
            bowl = trimesh.creation.revolve(np.array([[.035, 0], [.18, .03], [.245, .115], [.24, .15], [.22, .16], [.215, .13], [.17, .065], [.035, .028]]), sections=32)
            node(asset(bowl, smooth=True), 'ceramic', (vx, vy, z + .812), floor=f, role='detail')
            beam((vx + .21, vy + .10, z + .82), (vx + .21, vy + .10, z + 1.12), .012, 'frame' if upgraded_interior else 'brass', f, 'detail')
            beam((vx + .21, vy + .10, z + 1.12), (vx + .08, vy + .10, z + 1.12), .012, 'frame' if upgraded_interior else 'brass', f, 'detail')
            rect((vx - .31, y1 - .025, z + 1.08, vx + .31, y1 - .009, z + 1.82), 'mirror' if upgraded_interior else 'glass', f, 'mirror')
            if upgraded_interior:
                rect((vx - .33, y1 - .03, z + 1.84, vx + .33, y1 - .012, z + 1.86), 'lamp', f, 'fixture')
                k.light((vx, y1 - .3, z + 1.9), 8, kind='mirror')
            # WC sculpted bowl + seat ring (visual fixture, not a technical sanitary model).
            wx = x1 - .55; wy = y0 + .44
            ball((wx, wy, z + .22), (.20, .29, .22), 'ceramic', f, 'furniture')
            torus = trimesh.creation.torus(major_radius=.17, minor_radius=.03, major_sections=24, minor_sections=8)
            node(asset(torus, smooth=True), 'ceramic', (wx, wy - .04, z + .44), (.95, 1.45, 1), floor=f, role='detail')
            rb((wx, wy + .27, z + .55), (.39, .18, .62), 'ceramic', f, r=.05)
            furnishing('vanity', room, box(vx - .36, vy - .25, vx + .36, vy + .25))
            furnishing('wc', room, box(wx - .23, wy - .4, wx + .23, wy + .37))
            if upgraded_interior and rw >= 2.0 and rd >= 2.0:
                # Walk-in shower: frameless glass screen, black rain head.
                sxp = x0 + .95
                if sxp < wx - .35:
                    rect((sxp - .005, y0 + .01, z + .02, sxp + .005, y0 + min(1.25, rd * .55), z + 2.0), 'glass', f, 'glass')
                    rect((sxp - .012, y0 + .01, z + 2.0, sxp + .012, y0 + min(1.25, rd * .55), z + 2.02), 'frame', f, 'detail')
                    beam((x0 + .45, y0 + .06, z + 2.18), (x0 + .45, y0 + .42, z + 2.18), .01, 'frame', f, 'detail')
                    cylinder((x0 + .45, y0 + .42, z + 2.16), .11, .012, 'frame', f, 'detail')
                    rect((x0 + .3, y0 + .3, z + .009, x0 + .6, y0 + .34, z + .012), 'appliance', f, 'detail')
        elif kind in ('study', 'utility'):
            if kind == 'study':
                tx = x0 + rw * .50; ty = y0 + .38; tw = min(1.6, rw - .4)
                rect((tx - tw / 2, ty - .28, z + .72, tx + tw / 2, ty + .28, z + .77), M['table'], f, 'furniture')
                for xx in (tx - tw / 2 + .07, tx + tw / 2 - .07):
                    rect((xx - .03, ty - .22, z, xx + .03, ty + .22, z + .72), 'frame', f, 'furniture')
                chair(tx, ty + .65, z, f)
                furnishing('desk', room, box(tx - tw / 2, ty - .28, tx + tw / 2, ty + .94))
                rect((tx - .20, ty - .1, z + .79, tx + .2, ty - .085, z + 1.10), 'blackglass' if upgraded_interior else 'frame', f, 'detail')
                lamp(tx + tw / 2 - .15, ty, z + .77, f)
                if rw > 3 and rd > 3:
                    k.plant(x0 + .35, y1 - .38, z, 'monstera', height=.9, f=f, pot=(.18, .34, 'planter' if upgraded_interior else 'ceramic'))
            else:
                rb((x1 - .42, y1 - .39, z + .46), (.65, .60, .89), 'ceramic', f, r=.03)
                ring = trimesh.creation.torus(major_radius=.20, minor_radius=.035, major_sections=24, minor_sections=8)
                node(asset(ring, smooth=True), 'frame', (x1 - .42, y1 - .70, z + .45), rot=(math.pi / 2, 0, 0), floor=f, role='detail')
                furnishing('laundry', room, box(x1 - .745, y1 - .69, x1 - .095, y1 - .09))

    # ---------------------------------------------------------------- stairs & terraces
    for st in b['stairs']:
        p = box(st['x'] / 1000, st['y'] / 1000, (st['x'] + st['width']) / 1000, (st['y'] + st['depth']) / 1000)
        colliders.append({'id': st['id'] + '/stair-walk-not-supported', 'floor': st['floor'], 'polygon': list(p.exterior.coords), 'kind': 'stair'})
    # Guarding follows the actual open terrace perimeter; it is a visual scheme, not a certified balustrade.
    for terr in [s for s in b['spaces'] if s['kind'] == 'terrace']:
        p = Polygon(np.array(terr['polygon']) / 1000); f = terr['floor']; z = f * H
        for a, c in zip(list(p.exterior.coords), list(p.exterior.coords)[1:]):
            edge = LineString([a, c])
            if fp.boundary.buffer(.01).covers(edge):
                if modern:
                    glass = edge.buffer(.008, cap_style=2); poly_mesh(glass, z + .06, z + 1.1, 'glass', f, 'railing')
                    poly_mesh(edge.buffer(.03, cap_style=2), z + .009, z + .08, 'frame', f, 'railing')
                    poly_mesh(edge.buffer(.02, cap_style=2), z + 1.1, z + 1.13, 'frame', f, 'railing')
                else:
                    beam((*a, z + 1.1), (*c, z + 1.1), .023, 'frame', f, 'railing')
                    for t0 in np.arange(.08, edge.length, .95):
                        q = edge.interpolate(t0); beam((q.x, q.y, z + .02), (q.x, q.y, z + 1.1), .018, 'frame', f, 'railing')
                    glass = edge.buffer(.012, cap_style=2); poly_mesh(glass, z + .12, z + 1.05, 'glass', f, 'railing')
        center = p.representative_point()
        if modern:
            tx0, ty0, tx1, ty1 = p.bounds
            for i, xx in enumerate((tx0 + .5, tx1 - .5)):
                k.plant(xx, ty0 + .45, z, 'cordyline' if i else 'shrub_round', height=.8, f=f, pot=(.24, .5, 'planter'))
            if tx1 - tx0 > 2.6 and ty1 - ty0 > 1.9:
                for j, xx in enumerate((center.x - .55, center.x + .55)):
                    rb((xx, center.y + .1, z + .22), (.62, 1.5, .12), 'sling', f, 'outdoor-furniture', .04)
                    rb((xx, center.y + .72, z + .4), (.62, .35, .1), 'sling', f, 'outdoor-furniture', .04)
                    for dx in (-.26, .26):
                        for dy in (-.6, .75):
                            beam((xx + dx, center.y + dy, z + .01), (xx + dx, center.y + dy, z + .17), .013, 'frame', f, 'outdoor-furniture')
                furnishing('lounge', terr, box(center.x - .9, center.y - .66, center.x + .9, center.y + .95))
        else:
            k.plant(center.x, center.y, z, 'shrub_flowering', height=.75, f=f, pot=(.2, .32, 'ceramic'))
    # A true U stair: 18 risers, two flights, mid/top landings, no upper slab over the well.
    for st in b['stairs']:
        if st['to_floor'] is None:
            continue
        f = st['floor']; z = f * H; x = st['x'] / 1000; y = st['y'] / 1000; r = st['riser_mm'] / 1000; t = st['tread_mm'] / 1000; fw = st['flight_width'] / 1000; well = st['well'] / 1000; land = st['landing_mm'] / 1000
        for j in range(8):
            yy = y + land + j * t
            rect((x, yy, z + max(0, j * r - .08), x + fw, yy + t, z + (j + 1) * r), M['tread'], f, 'stair')
        # Landings and structural-stringer intent are visual coordination only.
        mid_y = y + land + 8 * t
        rect((x, mid_y, z + 9 * r - .16, x + 2 * fw + well, mid_y + land, z + 9 * r), M['tread'], f, 'stair')
        for j in range(8):
            yy = y + land + (7 - j) * t
            rect((x + fw + well, yy, z + 9 * r + j * r - .09, x + 2 * fw + well, yy + t, z + (10 + j) * r), M['tread'], f, 'stair')
        rect((x, y, z + H - .16, x + 2 * fw + well, y + land, z + H), M['tread'], f + 1, 'stair')
        # Handrails and pickets follow the two flight slopes.
        for xrail, start_z, ascending in [(x + fw - .04, z, True), (x + fw + well + .04, z + H, False)]:
            za = start_z + r if ascending else start_z; zb = z + 9 * r
            beam((xrail, y + land, za + .9), (xrail, mid_y, zb + .9), .025, 'timber' if not upgraded_interior else 'walnut', f, 'railing')
            for j in range(9):
                yy = y + land + j * t; zz = (z + (j + 1) * r) if ascending else (z + H - j * r)
                beam((xrail, yy, zz), (xrail, yy, zz + .89), .010, 'frame', f, 'railing')

    # ---------------------------------------------------------------- legacy facade recipes
    if not modern:
        canopy_depth = 2.05 if facade_style == 'tropical' else 1.55 if facade_style in ('warm', 'terracotta') else 2.45 if theme_id == 'warm_modern_minimal' else 1.05
        cw = 2.7 if facade_style != 'minimal' else 3.25; cz = 2.78
        rect((ex - cw / 2, -canopy_depth, cz, ex + cw / 2, .16, cz + .18), 'roof', 0, 'canopy', 'entry-canopy')
        rect((ex - cw / 2 + .07, -canopy_depth + .07, cz - .055, ex + cw / 2 - .07, .06, cz), 'timber', 0, 'canopy')
        for xx in (ex - cw / 2 + .12, ex + cw / 2 - .12):
            if facade_style == 'terracotta':
                cylinder((xx, -canopy_depth + .13, (cz - plinth) / 2), .12, cz + plinth, 'wall', 0, 'post')
            else:
                rect((xx - .085, -canopy_depth + .06, -plinth, xx + .085, -canopy_depth + .23, cz), 'stone' if v['style'] == 'warm' else 'frame', 0, 'post')
        for xx in (ex - .6, ex + .6):
            cylinder((xx, -canopy_depth * .55, cz - .065), .06, .013, 'lamp', 0, 'fixture')
            k.light((xx, -canopy_depth * .55, cz - .1), 20)
        if facade_style == 'tropical':
            for xx in np.arange(ex - cw / 2, ex + cw / 2, .18):
                rect((xx, -canopy_depth - .25, cz + .2, xx + .05, .22, cz + .31), 'timber', 0, 'pergola')
        if facade_style == 'terracotta':
            # Open slatted screen across only the blank stair facade.
            for xx in np.arange(.35, min(2.25, W * .2), .18):
                for yy in (0, .08):
                    rect((xx, -.24 - yy, .65, xx + .05, -.18 - yy, top + .5), 'stone', 0, 'screen')
        if facade_style in ('warm', 'graphite', 'concrete'):
            blank_width = 1.05 if storeys > 1 else .6
            rect((.24, -.16, .15, .24 + blank_width, -.015, top + .36), 'stone', 0, 'accent', 'stone-blade')
            if facade_style == 'graphite':
                for xx in np.arange(.27, .24 + blank_width, .12):
                    rect((xx, -.215, .25, xx + .023, -.17, top + .4), 'brass', 0, 'fin')
        if facade_style in ('minimal', 'concrete'):
            for f in range(storeys):
                rect((-.15, -.45, (f + 1) * H - .23, W + .15, .07, (f + 1) * H - .13), 'roof', f, 'canopy')

    # ---------------------------------------------------------------- exterior assemblies
    for assembly in assemblies:
        geo = assembly['geometry']; x0, y0, x1, y1 = [q / 1000 for q in geo['bounds_mm']]
        kind = geo.get('kind'); floor = assembly.get('floor_id', 0); aid = assembly['id']
        if kind == 'porch' and geo.get('style') == 'cantilever':
            land = geo.get('platform_z_mm', -150) / 1000
            rect((x0, y0, g, x1, y1, land), 'step', 0, 'porch', aid + '-landing', aid)
            for i, (d0, d1) in enumerate(((.62, .31), (.31, 0))):
                rect((x0 - .3 + i * .0, y0 - d0, g, x1 + .3 - i * .0, y0 - d1, g + (i + 1) * (land - g) / 2 - .0005), 'step', 0, 'step', aid + f'-step-{i}', aid)
            cz = geo.get('canopy_z_mm', 2950) / 1000; th = geo.get('canopy_thickness_mm', 260) / 1000; ov = geo.get('canopy_overhang_mm', 300) / 1000
            if geo.get('canopy_is_balcony'):
                ov = 0
            else:
                # Single storey: the entrance slab continues the floating roof fascia.
                if storeys == 1:
                    cz = top + .22 - th
                rect((x0 - .3, y0 - ov, cz, x1 + .3, 0, cz + th), 'roof', 0, 'canopy', aid + '-slab', aid)
            soffit_z = cz
            for j, xx in enumerate(np.arange(x0 - .22, x1 + .22, .11)):
                rect((xx, y0 - ov + .06, soffit_z - .025, xx + .06, -.02, soffit_z), 'timber', 0, 'soffit', aid + f'-soffit-{j}', aid)
            for i, xx in enumerate(np.linspace(x0 + .5, x1 - .5, 3)):
                cylinder((xx, (y0 - ov) * .5, soffit_z - .03), .045, .01, 'lamp', 0, 'downlight')
                k.light((xx, (y0 - ov) * .5, soffit_z - .15), 14, kind='soffit')
            # Wall washers flanking the door.
            for side in (-1, 1):
                xx = ex + side * (entry['width'] / 2000 + .45)
                rect((xx - .035, -.09, 2.0, xx + .035, -.005, 2.26), 'frame', 0, 'fixture', aid + f'-washer-{side}', aid)
                rect((xx - .03, -.092, 1.995, xx + .03, -.012, 2.0), 'lamp', 0, 'fixture')
                rect((xx - .03, -.092, 2.26, xx + .03, -.012, 2.265), 'lamp', 0, 'fixture')
                k.light((xx, -.35, 2.1), 10, kind='wall')
        elif kind == 'porch':
            platform = geo.get('platform_z_mm', -120) / 1000
            roof_z = geo.get('canopy_z_mm', 2700) / 1000
            # The platform stands more than a stride above the court, so an inset step on the walk to the front
            # door climbs it; elsewhere the platform edge stays a clean plinth line.
            rise = platform + .10 - g
            sx0, sx1 = max(x0, ex - .8), min(x1, ex + .8)
            depth = min(.36, (y1 - y0) * .45)
            if rise > .3 and sx1 - sx0 > .9:
                for xa, xb in ((x0, sx0), (sx1, x1)):
                    rect((xa, y0, platform, xb, y1, platform + .10), 'stone', 0, 'porch', owner=aid)
                rect((sx0, y0 + depth, platform, sx1, y1, platform + .10), 'stone', 0, 'porch', aid + '-platform', aid)
                rect((sx0, y0, g - .02, sx1, y0 + depth, g + rise / 2), 'stone', 0, 'porch', aid + '-step', aid)
            else:
                rect((x0, y0, platform, x1, y1, platform + .10), 'stone', 0, 'porch', aid + '-platform', aid)
            rect((x0 - .15, y0 - .15, roof_z, x1 + .15, y1 + .15, roof_z + .14), 'roof', 0, 'canopy', aid + '-roof', aid)
            count = geo.get('support_count', 2)
            posts = [x0 + .16 + (x1 - x0 - .32) * i / max(1, count - 1) for i in range(count)]
            # A post never stands in the walk to the front door: one that would is split into a pair framing it.
            clear = entry['width'] / 2000 + .55
            if any(abs(xx - ex) < clear for xx in posts):
                moved = sorted([xx for xx in posts if abs(xx - ex) >= clear] + [xx for xx in (ex - clear, ex + clear) if x0 + .16 <= xx <= x1 - .16])
                posts = [xx for j, xx in enumerate(moved) if j == 0 or xx - moved[j - 1] > .6]
            for i, xx in enumerate(posts):
                rect((xx - .045, y0 + .10, platform, xx + .045, y0 + .20, roof_z), 'timber', 0, 'porch', aid + f'-post-{i}', aid)
            rect((x0 - .15, y0 - .15, roof_z + .14, x1 + .15, y0 - .05, roof_z + .25), 'timber', 0, 'canopy', aid + '-fascia', aid)
            for j, xx in enumerate(np.arange(x0 + .28, x1 - .10, .52)):
                rect((xx, y0 + .10, roof_z - .035, min(x1, xx + .07), y1 - .10, roof_z + .025), 'timber', 0, 'soffit', aid + f'-soffit-{j}', aid)
            portal_base = max(0.0, platform + .10); portal_top = min(roof_z - .18, 2.60)
            rect((ex - .78, -.10, portal_base, ex - .62, .05, portal_top), 'timber', 0, 'door-portal', aid + '-door-portal-left', aid)
            rect((ex + .62, -.10, portal_base, ex + .78, .05, portal_top), 'timber', 0, 'door-portal', aid + '-door-portal-right', aid)
            rect((ex - .78, -.12, portal_top, ex + .78, .06, portal_top + .14), 'timber', 0, 'door-portal', aid + '-door-portal-head', aid)
            for xx in (x0 + (x1 - x0) * .34, x0 + (x1 - x0) * .66):
                cylinder((xx, y0 + .38, roof_z - .13), .07, .02, 'lamp', 0, 'fixture')
                k.light((xx, y0 + .38, roof_z - .16), 24)
            # Porch seating sits beside the walk to the front door, never across it.
            clear = entry['width'] / 2000 + .45
            side = 1 if x1 - ex >= ex - x0 else -1
            seat_x = ex + side * (clear + .8); seat_y = y0 + (y1 - y0) * .53
            if x1 - x0 > 3.0 and x0 + 1.1 <= seat_x <= x1 - 1.0:
                rb((seat_x, seat_y, platform + .40), (1.55, .54, .28), 'fabric', 0, 'outdoor-furniture', .07, owner=aid)
                rb((seat_x, seat_y + .22, platform + .75), (1.55, .12, .43), 'fabric', 0, 'outdoor-furniture', .06, owner=aid)
                for dx in (-1.18, 1.18):
                    if abs(seat_x + dx - ex) >= clear + .31 and x0 + .6 <= seat_x + dx <= x1 - .35:
                        rb((seat_x + dx, seat_y - .05, platform + .34), (.62, .60, .24), 'fabric-dark', 0, 'outdoor-furniture', .07, owner=aid)
                if seat_y - 1.1 >= y0:
                    rb((seat_x, seat_y - .78, platform + .30), (.78, .62, .08), 'stone', 0, 'outdoor-furniture', .08, owner=aid)
            rect((x0 + .12, y0 + .18, platform + .10, x0 + .28, y1 - .12, platform + .52), 'stone', 0, 'planter', aid + '-planter', aid)
            for xx in np.linspace(x0 + .48, x0 + .95, 2):
                k.plant(xx, y0 + .42, platform + .52, 'shrub_round', height=.3)
        elif kind == 'side_verandah':
            platform = geo.get('platform_z_mm', -120) / 1000
            roof_z = geo.get('canopy_z_mm', 2700) / 1000
            side_x0 = max(x0, W)
            rect((side_x0 + .02, y0 + .28, platform, x1 - .04, y1, platform + .10), 'stone', 0, 'verandah', aid + '-platform', aid)
            rect((side_x0 - .10, y0 + .10, roof_z, x1 + .10, y1, roof_z + .14), 'roof', 0, 'canopy', aid + '-roof', aid)
            for j, yy in enumerate(np.linspace(y0 + .45, y1 - .25, geo.get('support_count', 3))):
                rect((x1 - .16, yy - .045, platform, x1 - .06, yy + .045, roof_z), 'timber', 0, 'verandah', aid + f'-post-{j}', aid)
            rect((side_x0 + .18, y1 - .13, platform + .10, side_x0 + .48, y1 - .02, platform + .68), 'stone', 0, 'planter', aid + '-edge-planter', aid)
            rb((x1 - .54, y0 + 1.05, platform + .40), (.95, .48, .28), 'fabric', 0, 'outdoor-furniture', .07, owner=aid)
        elif kind == 'side_courtyard':
            platform = geo.get('platform_z_mm', -120) / 1000
            rect((x0, y0, platform, x1, y1, platform + .045), 'paver', 0, 'side-courtyard', aid + '-paving', aid)
            planter_x0 = x1 - .36; planter_x1 = x1 - .06
            rect((planter_x0, y0 + .18, platform + .045, planter_x1, y1 - .18, platform + .36), 'stone', 0, 'planter', aid + '-planter-edge', aid)
            rect((planter_x0 + .045, y0 + .24, platform + .36, planter_x1 - .045, y1 - .24, platform + .40), 'soil', 0, 'landscape', aid + '-soil', aid)
            for j, yy in enumerate(np.arange(y0 + .75, y1 - .45, 1.55)):
                k.plant(planter_x0 + .15, yy, platform + .40, 'shrub_round', height=.4)
            for j, yy in enumerate(np.arange(y0 + .85, y1 - .30, geo.get('light_spacing_mm', 2200) / 1000)):
                rect((x1 - .08, yy - .04, platform + .12, x1 + .02, yy + .04, platform + .64), 'lamp', 0, 'fixture', aid + f'-light-{j}', aid)
                k.light((x1 - .02, yy, platform + .58), 8)
        elif kind == 'feature_wall' and geo.get('material') == 'cladding':
            h = geo.get('height_mm', top * 1000 - 120) / 1000
            rect((x0, y0, g, x1, y1, h), 'cladding', 0, 'cladding', aid, aid)
            if geo.get('slats'):
                for j, xx in enumerate(np.arange(x1 - .75, x1 - .06, .1)):
                    rect((xx, y0 - .07, g + .1, xx + .05, y0 - .005, h - .05), 'timber', 0, 'screen', aid + f'-slat-{j}', aid)
            for xx in (x0 + .3, x1 - 1.0):
                rect((xx - .04, y0 - .08, g + .02, xx + .04, y0, g + .08), 'frame', 0, 'fixture')
                k.light((xx, y0 - .25, g + .3), 7, kind='uplight')
        elif kind == 'feature_wall':
            h = geo.get('height_mm', top * 1000 - 180) / 1000
            rect((x0, y0, 0, x1, y1, h), 'stone', 0, 'massing', aid, aid)
            rect((x0 - .05, y0 - .06, h, x1 + .05, y1 + .06, h + .12), 'timber', 0, 'roof-edge', aid + '-cap', aid)
            for j, xx in enumerate(np.arange(x0 + .26, x1 - .05, .34)):
                rect((xx, y0 - .055, .18, min(x1, xx + .035), y0 + .015, h - .12), 'timber', 0, 'screen', aid + f'-fin-{j}', aid)
        elif kind == 'facade_frame':
            h = geo.get('height_mm', 3150) / 1000; z = H
            depth = geo.get('depth_mm', 320) / 1000
            for j, xx in enumerate((x0, x1 - .14)):
                rect((xx, y0, z, xx + .14, y1, h + z), 'frame', 1, 'massing', aid + f'-pier-{j}', aid)
            rect((x0, y0, h + z - .16, x1, y1, h + z), 'roof', 1, 'roof-edge', aid + '-head', aid)
            rect((x0 - depth, y0 - depth, z, x1 + depth, y0 + .02, z + .08), 'frame', 1, 'roof-edge', aid + '-lower-reveal', aid)
        elif kind == 'balcony' and geo.get('style') == 'frameless_glass':
            ztop = geo.get('platform_z_mm', v['floor_height_mm'] - 30) / 1000
            th = geo.get('slab_thickness_mm', 250) / 1000
            rect((x0, y0, ztop - th, x1, y1, ztop), 'roof', floor, 'balcony', aid + '-slab', aid)
            rect((x0 + .03, y0 + .03, ztop, x1 - .03, y1 - .01, ztop + .025), 'deck', floor, 'balcony', aid + '-deck', aid)
            rail = geo.get('rail_height_mm', 1100) / 1000
            for (ax, ay, bx2, by2) in [(x0, y0, x1, y0 + .012), (x0, y0, x0 + .012, y1 - .02), (x1 - .012, y0, x1, y1 - .02)]:
                rect((ax + .02, ay + .02, ztop + .04, bx2 - .0, by2 + .0, ztop + rail), 'glass', floor, 'railing', owner=aid)
            rect((x0, y0, ztop, x1, y0 + .07, ztop + .06), 'frame', floor, 'railing', aid + '-shoe', aid)
            if y1 - y0 >= 1.4 and x1 - x0 >= 2.6:
                cx0 = x0 + (x1 - x0) * .3
                for j, xx in enumerate((cx0 - .4, cx0 + .4)):
                    rb((xx, y0 + (y1 - y0) * .55, ztop + .36), (.66, .7, .12), 'sling', floor, 'outdoor-furniture', .05, owner=aid)
                    rb((xx, y0 + (y1 - y0) * .55 + .33, ztop + .6), (.66, .1, .42), 'sling', floor, 'outdoor-furniture', .04, owner=aid)
                cylinder((cx0, y0 + (y1 - y0) * .38, ztop + .25), .22, .03, M['counter'], floor, 'outdoor-furniture')
                beam((cx0, y0 + (y1 - y0) * .38, ztop + .02), (cx0, y0 + (y1 - y0) * .38, ztop + .24), .02, 'frame', floor, 'outdoor-furniture')
                k.plant(x1 - .45, y0 + .45, ztop + .025, 'strelitzia', height=1.3, f=floor, pot=(.22, .45, 'planter'))
        elif kind == 'balcony':
            z = floor * H + geo.get('platform_z_mm', v['floor_height_mm'] - 120) / 1000
            rect((x0, y0, z, x1, y1, z + .12), 'stone', floor, 'balcony', aid + '-slab', aid)
            rail = z + geo.get('rail_height_mm', 1100) / 1000
            rect((x0, y0 - .03, rail, x1, y0 + .05, rail + .08), 'frame', floor, 'railing', aid + '-front-rail', aid)
            rect((x0 - .03, y0, z, x0 + .05, y1, rail), 'frame', floor, 'railing', aid + '-left-rail', aid)
            rect((x1 - .05, y0, z, x1 + .03, y1, rail), 'frame', floor, 'railing', aid + '-right-rail', aid)
            for j, xx in enumerate(np.arange(x0 + .15, x1, .72)):
                rect((xx - .018, y0 - .01, z + .10, xx + .018, y0 + .04, rail), 'frame', floor, 'railing', aid + f'-baluster-{j}', aid)
            rect((x0, y0 + .06, z + .10, x1, y0 + .09, rail - .05), 'glass', floor, 'railing', aid + '-glass', aid)
            if x1 - x0 > 3.8:
                for j, yy in enumerate(np.arange(y0 + .20, y1 - .12, .28)):
                    rect((x1 - .20, yy - .035, z + .16, x1 - .11, yy + .035, min(z + 1.95, rail + .06)), 'timber', floor, 'screen', aid + f'-privacy-{j}', aid)
            if geo.get('planter_edge'):
                rect((x0 + .25, y0 - .22, z + .12, x1 - .25, y0 - .02, z + .34), 'stone', floor, 'landscape', aid + '-planter', aid)
                for xx in np.arange(x0 + .5, x1 - .3, 1.0):
                    k.plant(xx, y0 - .10, z + .34, 'shrub_flowering', height=.35, f=floor)
            else:
                rb(((x0 + x1) / 2, y0 + (y1 - y0) * .56, z + .42), (1.65, .52, .30), 'fabric', floor, 'outdoor-furniture', .08, owner=aid)
                rb(((x0 + x1) / 2, y0 + (y1 - y0) * .73, z + .72), (1.65, .12, .42), 'fabric', floor, 'outdoor-furniture', .06, owner=aid)
                rb(((x0 + x1) / 2, y0 + (y1 - y0) * .22, z + .38), (.55, .55, .34), 'stone', floor, 'outdoor-furniture', .08, owner=aid)
            rect((x0 - .12, y0 - .18, z + .35, x1 + .12, y1 + .08, z + .48), 'roof', floor, 'roof-edge', aid + '-upper-reveal', aid)
        elif kind in ('screen', 'accent'):
            h = geo.get('height_mm', top * 1000 - 400) / 1000
            material = 'stone' if theme_id == 'earth_terracotta' or kind == 'accent' else 'timber'
            if kind == 'accent':
                rect((x0, y0, 0, x1, y1, h), material, 0, 'accent', aid, aid)
            elif x1 - x0 < y1 - y0:
                spacing = max(0.12, geo.get('spacing_mm', 180) / 1000)
                for j, yy in enumerate(np.arange(y0, y1, spacing)):
                    rect((x0, yy, 0, x1, min(y1, yy + geo.get('slat_depth_mm', 55) / 1000), h), material, 0, 'screen', aid + f'-slat-{j}', aid)
            else:
                spacing = max(0.12, geo.get('spacing_mm', 180) / 1000)
                for j, xx in enumerate(np.arange(x0, x1, spacing)):
                    rect((xx, y0, 0, min(x1, xx + geo.get('slat_depth_mm', 55) / 1000), y1, h), material, 0, 'screen', aid + f'-slat-{j}', aid)
        elif kind == 'carport':
            rz = geo.get('roof_z_mm', 2750) / 1000; th = geo.get('slab_thickness_mm', 220) / 1000
            rect((x0 - .15, y0 - .15, g + rz, x1 + .15, y1 + .15, g + rz + th), 'roof', -1, 'carport', aid + '-roof', aid)
            for i, (cx2, cy2) in enumerate(((x0 + .1, y0 + .1), (x1 - .1, y0 + .1), (x0 + .1, y1 - .1), (x1 - .1, y1 - .1))):
                rect((cx2 - .09, cy2 - .09, g, cx2 + .09, cy2 + .09, g + rz), 'roof', -1, 'carport', aid + f'-column-{i}', aid)
            for yy in np.linspace(y0 + 1, y1 - 1, 3):
                cylinder(((x0 + x1) / 2, yy, g + rz - .005), .05, .01, 'lamp', -1, 'downlight')
                k.light(((x0 + x1) / 2, yy, g + rz - .2), 12, kind='soffit')
        elif kind == 'pergola' and geo.get('style') == 'glass_roof':
            z = g + geo.get('z_mm', 2750) / 1000
            for i, (cx2, cy2) in enumerate(((x0 + .06, y1 - .06), (x1 - .06, y1 - .06))):
                rect((cx2 - .05, cy2 - .05, g, cx2 + .05, cy2 + .05, z), 'frame', -1, 'pergola', aid + f'-post-{i}', aid)
            rect((x0, y1 - .12, z, x1, y1, z + .16), 'frame', -1, 'pergola', aid + '-beam', aid)
            for j, xx in enumerate(np.arange(x0, x1 + .01, geo.get('spacing_mm', 900) / 1000)):
                rect((min(xx, x1 - .06), y0, z, min(xx, x1 - .06) + .06, y1, z + .14), 'frame', -1, 'pergola', aid + f'-rafter-{j}', aid)
            rect((x0, y0, z + .14, x1, y1, z + .152), 'glass', -1, 'pergola-glass', aid + '-glazing', aid)
            lamp_x, lamp_y = (x0 + x1) / 2, (y0 + y1) / 2
            beam((lamp_x, lamp_y, z - .7), (lamp_x, lamp_y, z), .006, 'frame', -1, 'fixture')
            ball((lamp_x, lamp_y, z - .75), (.2, .2, .13), 'globe', -1, 'fixture')
            k.light((lamp_x, lamp_y, z - .85), 30, kind='pendant')
        elif kind == 'pergola':
            z = geo.get('z_mm', 2850) / 1000
            rect((x0, y0, z, x1, y0 + .08, z + .12), 'timber', 0, 'pergola', aid + '-header', aid)
            for j, xx in enumerate(np.arange(x0 + .15, x1, .42)):
                rect((xx, y0, z, min(x1, xx + .09), y1, z + .12), 'timber', 0, 'pergola', aid + f'-slat-{j}', aid)

    # ---------------------------------------------------------------- landscape features
    lawns = []
    for feature in features:
        fk = feature['kind']
        if 'polygon' in feature:
            poly = Polygon(np.array(feature['polygon'], dtype=float) / 1000)
            if not poly.is_valid:
                poly = poly.buffer(0)
        if fk == 'path':
            poly_mesh(poly, g + .004, g + .025, 'paver', -1, 'landscape', feature['id'], feature['id'])
        elif fk == 'planting_bed':
            poly_mesh(poly, g + .004, g + .025, 'soil', -1, 'landscape', feature['id'], feature['id'])
            border = poly.buffer(.045).difference(poly)
            poly_mesh(border, g + .025, g + .12, 'stone', -1, 'landscape', feature['id'] + '-raised-edge', feature['id'])
        elif fk == 'court':
            poly_mesh(poly, g - .02, g + .04, 'cobble', -1, 'court', feature['id'], feature['id'])
        elif fk == 'patio':
            poly_mesh(poly, g - .02, g + .06, 'encaustic', -1, 'patio', feature['id'], feature['id'])
        elif fk == 'deck':
            poly_mesh(poly, g - .02, g + .08, 'deck', -1, 'deck', feature['id'], feature['id'])
        elif fk == 'lawn':
            poly_mesh(poly, g - .03, g + .012, 'lawn', -1, 'lawn', feature['id'], feature['id'])
            lawns.append({'id': feature['id'], 'polygon': [[round(x, 4), round(y, 4)] for x, y in list(poly.exterior.coords)[:-1]],
                          'holes': [[[round(x, 4), round(y, 4)] for x, y in list(r.coords)[:-1]] for r in poly.interiors], 'z': round(g + .012, 4)})
        elif fk == 'pebble_bed':
            poly_mesh(poly, g - .02, g + .03, 'pebble', -1, 'landscape', feature['id'], feature['id'])
            if feature.get('edging'):
                edge = poly.buffer(.006, join_style=2).difference(poly)
                poly_mesh(edge, g - .02, g + .065, 'steel', -1, 'edging', feature['id'] + '-edging', feature['id'])
        elif fk == 'stepping_stones':
            for i, stone in enumerate(feature.get('stones', [])):
                sp = Polygon(np.array(stone, dtype=float) / 1000)
                poly_mesh(sp, g - .01, g + .055, 'steppingstone', -1, 'stone-pad', f"{feature['id']}-{i}", feature['id'])
        elif fk in ('plant', 'tree', 'shrub'):
            x, y = [q / 1000 for q in feature['position_mm']]
            species = feature.get('species') or ('tree_standard' if fk == 'tree' else 'shrub_round')
            if fk == 'shrub' and not feature.get('species'):
                k.plant(x, y, g + .02, 'shrub_round', height=max(.35, feature.get('scale', .42) * 1.1))
            elif fk == 'tree' and not feature.get('species'):
                k.plant(x, y, g + .02, 'tree_standard', height=2.7 * feature.get('scale', .9))
            else:
                k.plant(x, y, g + .02, species, scale=feature.get('scale', 1.))
            if feature.get('uplight'):
                cylinder((x + .35, y - .35, g + .04), .05, .04, 'frame', -1, 'fixture')
                cylinder((x + .35, y - .35, g + .061), .035, .004, 'lamp', -1, 'fixture')
                k.light((x + .2, y - .2, g + .5), 10, kind='uplight')
        elif fk == 'hedge':
            x, y = [q / 1000 for q in feature['position_mm']]
            L, Wd, Hh = [q / 1000 for q in feature['size_mm']]
            k.hedge(x, y, g + .01, (L, Wd, Hh), feature.get('rotation', 0))
            k.ground.append(box(x - L / 2, y - Wd / 2, x + L / 2, y + Wd / 2))
        elif fk == 'lantern':
            x, y = [q / 1000 for q in feature['position_mm']]
            rect((x - .1, y - .1, g, x + .1, y + .1, g + .02), 'frame', -1, 'fixture', feature['id'] + '-base', feature['id'])
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                rect((x + sx * .085 - .012, y + sy * .085 - .012, g + .02, x + sx * .085 + .012, y + sy * .085 + .012, g + .36), 'frame', -1, 'fixture')
            rect((x - .075, y - .075, g + .03, x + .075, y + .075, g + .33), 'lamp', -1, 'fixture', feature['id'] + '-glow', feature['id'])
            node(asset(frustum(.15, .06, .07)), 'frame', (x, y, g + .36), floor=-1, role='fixture')
            k.light((x, y, g + .25), 7, kind='lantern')
        elif fk == 'planter':
            x, y = [q / 1000 for q in feature['position_mm']]
            pw, _, ph = [q / 1000 for q in feature.get('size_mm', [500, 500, 600])]
            zb = porch_asm['geometry'].get('platform_z_mm', -150) / 1000 if (feature.get('on') == 'landing' and porch_asm) else g
            node(asset(frustum(pw * .5, pw * .68, ph)), 'planter', (x, y, zb), floor=-1, role='planter', owner=feature['id'])
            k.plant(x, y, zb + ph - .03, feature.get('species', 'shrub_round'), scale=feature.get('scale', .5))
        elif fk == 'wall_light':
            x, y = [q / 1000 for q in feature['position_mm']]
            z = feature.get('height_mm', 1900) / 1000
            s = feature.get('facing', 1)
            rect((x - (0 if s > 0 else .09), y - .05, z - .1, x + (.09 if s > 0 else 0), y + .05, z + .1), 'frame', 0, 'fixture', feature['id'], feature['id'])
            rect((x + s * .02 - .025, y - .04, z - .105, x + s * .02 + .025, y + .04, z - .1), 'lamp', 0, 'fixture')
            k.light((x + s * .25, y, z - .3), 8, kind='wall')
        elif fk == 'outdoor_dining':
            x, y = [q / 1000 for q in feature['position_mm']]
            zb = g + .06
            rect((x - .8, y - .45, zb + .72, x + .8, y + .45, zb + .75), M['counter'], -1, 'outdoor-furniture', feature['id'] + '-top', feature['id'])
            for dx in (-.72, .72):
                for dy in (-.38, .38):
                    rect((x + dx - .02, y + dy - .02, zb, x + dx + .02, y + dy + .02, zb + .72), 'frame', -1, 'outdoor-furniture')
            for dx in (-.4, .4):
                for dy, rot in ((-.72, math.pi), (.72, 0)):
                    cxx, cyy = x + dx, y + dy
                    rb((cxx, cyy, zb + .44), (.5, .48, .05), 'sling', -1, 'outdoor-furniture', .02, rot=rot)
                    back_y = cyy + (.24 if rot == 0 else -.24)
                    rb((cxx, back_y, zb + .72), (.5, .05, .5), 'sling', -1, 'outdoor-furniture', .02, rot=rot)
                    for ddx in (-.22, .22):
                        for ddy in (-.2, .2):
                            beam((cxx + ddx, cyy + ddy, zb), (cxx + ddx, cyy + ddy, zb + .42), .012, 'frame', -1, 'outdoor-furniture')
            k.plant(x + 1.15, y - .2, zb, 'shrub_round', height=.5, pot=(.22, .5, 'planter'))
    if boundary and theme_id != 'current' and not modern:
        # A flush timber threshold marks the gateway between the pillars; nothing spans the opening at body
        # height, so a visitor can walk in from the street.
        rect((ex - gate_half + .03, ymin - .02, g - .02, ex + gate_half - .03, ymin + .2, g + .05), 'timber', -1, 'gate', 'exterior-gate-threshold', 'exterior-gate')

    # ---------------------------------------------------------------- bands, drainage, bollards
    if not modern:
        for f in range(storeys):
            rect((0, -.045, (f + 1) * H - .20, W, .015, (f + 1) * H - .12), 'roof', f, 'band')
    for xx in (.10, W - .10):
        beam((xx, D + .08, .10), (xx, D + .08, top + .35), .034, 'frame' if modern else 'roof', -1, 'pipe')
        beam((xx, D + .08, .10), (xx, D + .36, -.22), .034, 'frame' if modern else 'roof', -1, 'pipe')
    if not modern:
        for xx in (ex - 1.3, ex + 1.3):
            for yy in np.arange(ymin + .9, -.9, 1.6):
                rect((xx - .055, yy - .055, -.43, xx + .055, yy + .055, .07), 'frame', role='fixture')
                rect((xx - .051, yy - .051, .06, xx + .051, yy + .051, .12), 'lamp', role='fixture')
                k.light((xx, yy, .15), 6)
    if v['pooja']:
        # An explicitly labelled niche in the 2D schedule, not an invented room.
        xx = W - .65; yy = b['brief']['floor_height_mm'] / 1000 + .3
        rect((xx - .27, yy - .13, .5, xx + .27, yy + .13, 1.0), M['casework'], 0, 'furniture', 'pooja-niche')
        rect((xx - .25, yy - .12, 1.03, xx + .25, yy + .12, 1.07), M['counter'], 0, 'furniture')
        cylinder((xx, yy, 1.17), .06, .18, 'brass', 0, 'detail')

    # ---------------------------------------------------------------- lawns for legacy themes
    if not lawns:
        inner = plot.buffer(-.2)
        taken = unary_union([fp.buffer(.25)] + [q.buffer(.05) for q in k.ground]) if k.ground else fp.buffer(.25)
        for i, part in enumerate(_parts(inner.difference(taken))):
            if part.area > 1.2:
                lawns.append({'id': f'lawn-{i}', 'polygon': [[round(x, 4), round(y, 4)] for x, y in list(part.exterior.coords)[:-1]],
                              'holes': [[[round(x, 4), round(y, 4)] for x, y in list(r.coords)[:-1]] for r in part.interiors], 'z': round(g - .04, 4)})

    # ---------------------------------------------------------------- walk + rooms metadata
    rooms = [{'id': s['id'], 'name': s['name'], 'kind': s['kind'], 'floor': s['floor'],
              'polygon': [[round(x / 1000, 4), round(y / 1000, 4)] for x, y in s['clear']]} for s in b['spaces']]
    # The walk starts on the street outside the open gate, facing the house, so the visitor arrives the way a
    # guest does (the modern gate is parked open and its track is flush; legacy leaves stand open). A wide
    # drive gate is entered on the front door's line, clear of the carport posts.
    arrive_x = ex
    if modern and boundary:
        gate_c, gate_w = boundary.get('gate_center_mm', ex * 1000) / 1000, boundary.get('gate_width_mm', 2600) / 1000
        arrive_x = min(max(ex, gate_c - gate_w / 2 + .6), gate_c + gate_w / 2 - .6)
    walk = {'eye_height': 1.63, 'arrival': {'position': [round(arrive_x, 3), round(ymin - 1.3, 3), round(g + (.1 if modern else 0), 3)], 'yaw_deg': 0}, 'floors': []}
    for f in range(storeys):
        options = [s for s in b['spaces'] if s['floor'] == f and s['kind'] in ('living', 'family', 'dining', 'hall')]
        if not options:
            continue
        s = options[0]
        c = Polygon(np.array(s['clear']) / 1000).representative_point()
        walk['floors'].append({'floor': f, 'position': [round(c.x, 3), round(c.y, 3), round(f * H, 3)], 'yaw_deg': 180 if f else 0})

    # Exact generated scene, not an image substitute.
    return {'schema': 'floorforge.scene/0.4', 'units': 'm', 'up': 'Z', 'materials': materials, 'assets': k.assets, 'nodes': k.nodes,
            'lights': lights, 'colliders': colliders, 'furniture': furniture, 'floor_height': H, 'storeys': storeys,
            'bounds': [xmin, ymin, -plinth, xmax, ymax, top + .7], 'footprint': (np.array(b['footprint']) / 1000).tolist(),
            'entry': [float(ex), -.15, 1.6], 'solar': report['solar'], 'style': v['style'],
            'exterior_theme': theme_id, 'interior_theme': interior_id,
            'exterior_revision': exterior.get('revision'), 'exterior_review': exterior.get('review', {}),
            'vegetation': k.vegetation, 'lawns': lawns, 'rooms': rooms, 'walk': walk,
            'cameras': {'hero': {'position': [W * 1.90, -max(16, D * 1.34), top * .68 + 3.0], 'target': [W * .47, D * .25, top * .40], 'fov': 43},
                        'dollhouse': {'position': [W * 1.45, -D * .52, top + max(W, D) * 1.55], 'target': [W * .5, D * .5, 1.], 'fov': 42},
                        'interior': {'position': [ex, .65, 1.6], 'target': [W * .72, 4.0, 1.35], 'fov': 66}},
            'quality': 'Authored procedural geometry with physically based surface recipes and procedural planting; not a verified photographic render.',
            'banner': b['banner']}


def transformation(node):
    m = trimesh.transformations.euler_matrix(*node['rotation'], 'sxyz')
    m[:3, :3] = m[:3, :3] @ np.diag(node['scale']); m[:3, 3] = node['position']; return m


def glb_bytes(scene):
    out = trimesh.Scene(); geometries = {}
    for n in scene['nodes']:
        key = n['asset'] + '@' + n['material']; a = scene['assets'][n['asset']]
        if key not in geometries:
            m = trimesh.Trimesh(vertices=a['vertices'], faces=a['faces'], process=False)
            color = scene['materials'][n['material']]['color']; rgb = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            mat = scene['materials'][n['material']]
            material = trimesh.visual.material.PBRMaterial(name=n['material'], baseColorFactor=rgb + [round(255 * mat.get('alpha', 1))],
                metallicFactor=mat.get('metallic', 0), roughnessFactor=mat['roughness'], alphaMode='BLEND' if mat.get('alpha', 1) < 1 else 'OPAQUE', doubleSided=True)
            m.visual = trimesh.visual.TextureVisuals(material=material)
            m.metadata = {'source_asset': n['asset'], 'scope': 'preliminary authored component'}
            out.geometry[key] = m; geometries[key] = m
        # Z-up (m) -> Y-up (m) at export boundary.
        convert = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0])
        out.graph.update(frame_to=n['id'], matrix=convert @ transformation(n), geometry=key,
                         metadata={'owner': n['owner'], 'floor': n['floor'], 'role': n['role']})
    out.metadata = {'banner': scene['banner'], 'units': 'm', 'up': 'Y', 'geometry_scope': 'individual closed components plus thin decorative surfaces; not a boolean-unioned building'}
    return out.export(file_type='glb')
