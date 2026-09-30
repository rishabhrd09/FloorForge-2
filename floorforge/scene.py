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
from shapely.ops import unary_union, nearest_points
from shapely import get_parts
from shapely.affinity import scale as pscale
from shapely.prepared import prep
from .model import sha, STYLES, enu_to_local
from .exterior import apply_exterior_preferences, get_exterior_theme, get_interior_theme
from .scene_kit import Kit, extrude, rounded_box, frustum, material_library, SPECIES_HEIGHT
from .frontage import gate_openings
from .plan_geometry import plate, roof, geometry, floor_outline
from .spaces import OUTDOOR, NON_WALKABLE

__all__ = ['make_scene', 'glb_bytes', 'transformation', 'extrude', 'rounded_box', 'opening_polygon']


def opening_polygon(w, o, pad=0):
    a = np.array(w['a'], dtype=float); b = np.array(w['b'], dtype=float); u = (b - a) / np.linalg.norm(b - a); n = np.array([-u[1], u[0]])
    p = a + u * (o['offset'] - pad); q = a + u * (o['offset'] + o['width'] + pad); t = w['thickness'] + 300
    return Polygon([p - n * t, q - n * t, q + n * t, p + n * t])


def _parts(geom):
    return [p for p in get_parts(geom) if p.geom_type == 'Polygon' and p.area > 1e-6] if not geom.is_empty else []


# Window pod shell and lining per exterior theme, and the eyebrow canopy over legacy living-room windows.
WINDOW_POD = {'modern_tropical': ('frame', 'timber'), 'warm_modern_minimal': ('frame', 'timber'), 'tropical_verandah': ('timber', None),
              'earth_terracotta': ('stone', 'timber'), 'current': ('frame', None)}
WINDOW_EYEBROW = {'warm_modern_minimal': 'timber', 'tropical_verandah': 'timber', 'earth_terracotta': 'stone', 'current': 'frame'}

# Terrace finishes per exterior theme: slab edge, handrail cap and pergola frame.
TERRACE_FINISH = {'modern_tropical': {'slab': 'roof', 'cap': 'frame', 'pergola': 'frame'},
                  'warm_modern_minimal': {'slab': 'stone', 'cap': 'frame', 'pergola': 'frame'},
                  'tropical_verandah': {'slab': 'stone', 'cap': 'timber', 'pergola': 'timber'},
                  'earth_terracotta': {'slab': 'stone', 'cap': 'frame', 'pergola': 'frame'},
                  'current': {'slab': 'stone', 'cap': 'frame', 'pergola': 'frame'}}

def make_scene(building, report):
    b = building if building.get('exterior') else apply_exterior_preferences(building)
    v = b['brief']; exterior = b['exterior']; theme_id = exterior['theme']
    custom = bool(b.get('planning',{}).get('custom'))
    from .rooftop import with_rooftop_objects
    rb_model = with_rooftop_objects(b)
    rooftop = b.get('rooftop')
    metres = lambda p: pscale(p,xfact=.001,yfact=.001,origin=(0,0))
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
    gates = []; door_motion = {}
    doors_closed = b.get('planning',{}).get('doorsClosed',False)
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
    hosts = {w['id']: w for w in rb_model['walls']}
    entry = next(o for o in b['openings'] if o['kind'] == 'entry'); ew = hosts[entry['wall_id']]
    u = (np.array(ew['b']) - ew['a']) / math.dist(ew['a'], ew['b']); em = np.array(ew['a']) + u * (entry['offset'] + entry['width'] / 2); ex = em[0] / 1000
    landscape = exterior.get('landscape', {}) or {}
    boundary = landscape.get('boundary', {}) or {}
    features = landscape.get('features', []) if theme_id != 'current' else []
    assemblies = exterior.get('assemblies', []) if theme_id != 'current' else []
    porch_asm = next((a for a in assemblies if a['geometry'].get('kind') == 'porch'), None)
    # Fully open zoning edges cannot support art, cabinetry, or skirting.
    open_hosts = {o['wall_id'] for o in b['openings'] if o.get('openSide')}
    wall_union = {f: unary_union([Polygon(np.array(w['polygon']) / 1000) for w in b['walls'] if w['floor'] == f and w['id'] not in open_hosts]) for f in range(storeys)}
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
        # Only along walls: an open edge between two rooms (living and dining) carries no skirting across the floor.
        ring = clear.difference(clear.buffer(-thickness, join_style=2)).intersection(wall_union[f].buffer(thickness + .02, join_style=2))
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
    if boundary and (modern or boundary.get('gates')):
        # A real frontage (floorforge/frontage.py): a pedestrian gate on the path to the door, shown open, a
        # separate sliding vehicle gate (closed) over the parking pad, and a stone-clad letterbox pier with the
        # house number and a gate light beside the pedestrian gate; wall runs between piers elsewhere.
        wt = boundary.get('wall_thickness_mm', 150) / 1000
        if modern:
            fh, sh, solid, cap, pier_mat, tall = (boundary.get('front_wall_height_mm', 1500) / 1000, boundary.get('side_wall_height_mm', 1850) / 1000,
                                                   .95, 'frame', 'wall', 2.1)
        else:
            fh, sh, solid, cap, pier_mat, tall = .72 - g, .65 - g, .72 - g, 'stone', 'stone', 1.35 - g
        for xa, ya, xb, yb in [(xmin, ymin, xmin + wt, ymax), (xmax - wt, ymin, xmax, ymax), (xmin, ymax - wt, xmax, ymax)]:
            # Rear wings can meet the boundary. Do not draw a second site wall
            # or its dark cap through their interior finishes.
            boundary_run = box(xa, ya, xb, yb)
            cap_run = box(xa - .012, ya - .012, xb + .012, yb + .012)
            if custom:
                boundary_run = boundary_run.difference(fp.buffer(.02))
                cap_run = cap_run.difference(fp.buffer(.02))
                for part in _parts(boundary_run):
                    poly_mesh(part, g, g + sh, 'wall', role='site')
                for part in _parts(cap_run):
                    poly_mesh(part, g + sh, g + sh + (.035 if modern else .04), cap, role='site')
            else:
                rect((xa, ya, g, xb, yb, g + sh), 'wall', role='site')
                rect((xa - .012, ya - .012, g + sh, xb + .012, yb + .012, g + sh + (.035 if modern else .04)), cap, role='site')
        openings = [(x0 / 1000, x1 / 1000, gate) for x0, x1, gate in gate_openings(boundary)]
        lb = boundary.get('letterbox_pier')
        lbx = (lb['x0_mm'] / 1000, lb['x1_mm'] / 1000) if lb else None

        def pier(px, half=.17, extra=.08):
            if modern:
                rect((px - half, ymin - .03, g, px + half, ymin + wt + .03, g + fh + extra), pier_mat, role='site')
                rect((px - half - .01, ymin - .04, g + fh + extra, px + half + .01, ymin + wt + .04, g + fh + extra + .04), cap, role='site')
            else:
                rect((px - .11, ymin - .04, g, px + .11, ymin + wt + .09, 1.05), 'stone', role='site')

        taken = []
        for x0, x1, gate in openings:
            if gate['kind'] == 'pedestrian':
                left = lbx if lbx and lbx[1] <= x0 + .01 else (x0 - .3, x0)
                right = lbx if lbx and lbx[0] >= x1 - .01 else (x1, x1 + .3)
                taken.append((left[0], right[1]))
            else:
                taken.append((x0 - .36, x1 + .36))
        x = xmin
        runs = []
        for a, b2 in sorted(taken):
            if a - x > .05:
                runs.append((x, a))
            x = max(x, b2)
        if xmax - x > .05:
            runs.append((x, xmax))
        for xa, xb in runs:
            rect((xa, ymin, g, xb, ymin + wt, g + solid), 'wall', role='site')
            rect((xa, ymin - .006, g + solid, xb, ymin + wt + .006, g + solid + .03), cap, role='site')
            if modern and xb - xa > .6:
                # Stone cladding on the street face of the solid wall, washed by small up-lights set at its foot.
                rect((xa, ymin - .025, g, xb, ymin, g + solid), 'cladding', role='site', name=f'exterior-boundary-cladding-{xa:.2f}')
                for i in range(max(1, int((xb - xa) // 1.6))):
                    lx = xa + (i + .5) * (xb - xa) / max(1, int((xb - xa) // 1.6))
                    rect((lx - .05, ymin - .35, g - .01, lx + .05, ymin - .25, g + .02), 'frame', role='fixture')
                    rect((lx - .035, ymin - .34, g + .02, lx + .035, ymin - .26, g + .024), 'lamp', role='fixture')
                    k.light((lx, ymin - .3, g + .12), 10, kind='uplight')
            if modern:
                z = g + solid + .075
                while z + .07 <= g + fh + .001:
                    rect((xa + .02, ymin + .035, z, xb - .02, ymin + .095, z + .065), 'frame', role='site')
                    z += .1
            # Piers at the plot corners and along the run, never more than ~2.9 m apart.
            n = max(1, round((xb - xa) / 2.9))
            posts = [xa + (xb - xa) * i / n for i in range(1, n)]
            posts += [p for p, edge in ((xa + .17, xa <= xmin + .01), (xb - .17, xb >= xmax - .01)) if edge]
            for px in posts:
                pier(px)
        for x0, x1, gate in openings:
            if gate['kind'] == 'vehicle':
                for px in (x0 - .18, x1 + .18):
                    if modern:
                        pier(px, .18, .2)
                        rect((px - .07, ymin - .075, g + fh - .02, px + .07, ymin - .04, g + fh + .12), 'frame', role='fixture')
                        rect((px - .05, ymin - .079, g + fh, px + .05, ymin - .075, g + fh + .1), 'lamp', role='fixture')
                        k.light((px, ymin - .2, g + fh + .05), 7, kind='pillar')
                    else:
                        pier(px)
                if custom:
                    # Two inward-opening leaves retain the closed frontage and clear the car gateway.
                    gy, top_z = ymin + wt + .02, g + (fh + .15 if modern else .95 - g)
                    middle = (x0 + x1) / 2
                    parts = []
                    for leaf, (la, lb, pivot, angle) in enumerate(((x0-.1, middle-.012, x0, math.pi/2),
                                                                  (middle+.012, x1+.1, x1, -math.pi/2))):
                        mark = len(k.nodes)
                        owner = 'exterior-vehicle-gate'
                        rect((la, gy, g+.05, lb, gy+.05, g+.1), 'frame', role='gate',
                             name=owner if leaf == 0 else owner+'-right', owner=owner)
                        rect((la, gy, top_z-.05, lb, gy+.05, top_z), 'frame', role='gate', owner=owner)
                        for xx in (la, lb-.05):
                            rect((xx, gy, g+.05, xx+.05, gy+.05, top_z), 'frame', role='gate', owner=owner)
                        for xx in np.arange(la+.05, lb-.055, .08 if modern else .12):
                            rect((xx, gy+.005, g+.1, min(xx+(.05 if modern else .025),lb-.025), gy+.045, top_z-.05),
                                 'timber' if modern else 'frame', role='gate', owner=owner)
                        parts.append({'ids':[n['id'] for n in k.nodes[mark:]], 'pivot':[pivot,gy+.025,g], 'angle':angle})
                    gates.append({'id':'exterior-vehicle-gate','label':'Main vehicle gate','floor':-1,'kind':'gate',
                                  'start':[x0,gy+.025,g], 'axis':[1,0,0], 'width':x1-x0,'height':top_z-g,
                                  'base':g,'sill':0,'initial':0,'parts':parts})
                else:
                    # Preserve the authored frontage of legacy automatic presets.
                    gy, top_z = ymin + wt + .02, g + (fh + .15 if modern else .95 - g)
                    rect((x0 - .1, gy, g + .05, x1 + .1, gy + .05, g + .1), 'frame', role='gate', name='exterior-vehicle-gate', owner='exterior-vehicle-gate')
                    rect((x0 - .1, gy, top_z - .05, x1 + .1, gy + .05, top_z), 'frame', role='gate', owner='exterior-vehicle-gate')
                    for xx in (x0 - .1, (x0 + x1) / 2 - .025, x1 + .05):
                        rect((xx, gy, g + .05, xx + .05, gy + .05, top_z), 'frame', role='gate', owner='exterior-vehicle-gate')
                    if modern:
                        for xx in np.arange(x0 - .05, x1 + .05 - .045, .08):
                            rect((xx, gy + .005, g + .1, xx + .05, gy + .045, top_z - .05), 'timber', role='gate', owner='exterior-vehicle-gate')
                    else:
                        for xx in np.arange(x0 + .06, x1 - .03, .12):
                            rect((xx, gy + .01, g + .1, xx + .025, gy + .04, top_z - .05), 'frame', role='gate', owner='exterior-vehicle-gate')
                    span = min(x1 - x0, gate.get('park_run_mm', (x1 - x0) * 1000) / 1000) + .1
                    t0, t1 = (x0 - span, x1 + .1) if gate.get('park') == 'left' else (x0 - .1, x1 + span)
                    rect((max(t0, xmin + wt), ymin + wt + .01, g - .02, min(t1, xmax - wt), ymin + wt + .07, g + .012), 'steel', role='gate', owner='exterior-vehicle-gate')

            else:
                hinge_right = gate.get('hinge') == 'right'
                pier_left = bool(lbx and lbx[1] <= x0 + .01)
                jamb = (x1, x1 + .3) if pier_left else (x0 - .3, x0)
                top_j = g + tall if modern else 1.05
                if modern:
                    rect((jamb[0], ymin - .03, g, jamb[1], ymin + wt + .03, top_j), 'wall', role='site')
                    rect((jamb[0] - .01, ymin - .04, top_j, jamb[1] + .01, ymin + wt + .04, top_j + .04), cap, role='site')
                else:
                    pier((jamb[0] + jamb[1]) / 2)
                if lbx:
                    l0, l1 = lbx
                    top_l = g + tall
                    rect((l0, ymin - .06, g, l1, ymin + wt + .06, top_l), 'cladding', role='site', name='exterior-letterbox-pier', owner='exterior-letterbox-pier')
                    rect((l0 - .015, ymin - .075, top_l, l1 + .015, ymin + wt + .075, top_l + .04), cap, role='site', owner='exterior-letterbox-pier')
                    fx = (l0 + l1) / 2
                    rect((fx - .13, ymin - .072, g + 1.42, fx + .13, ymin - .06, g + 1.6), 'brass', role='detail', name='house-number-plate', owner='exterior-letterbox-pier')
                    rect((fx - .16, ymin - .1, g + .95, fx + .16, ymin - .06, g + 1.2), 'steel', role='detail', name='exterior-letterbox', owner='exterior-letterbox-pier')
                    rect((fx - .11, ymin - .103, g + 1.15, fx + .11, ymin - .1, g + 1.165), 'basalt', role='detail', owner='exterior-letterbox-pier')
                    rect((fx - .045, ymin - .11, top_l - .34, fx + .045, ymin - .06, top_l - .2), 'frame', role='fixture', owner='exterior-letterbox-pier')
                    rect((fx - .035, ymin - .114, top_l - .33, fx + .035, ymin - .11, top_l - .21), 'lamp', role='fixture', owner='exterior-letterbox-pier')
                    k.light((fx, ymin - .35, top_l - .3), 6, kind='pillar')
                    if modern:
                        # A slim steel canopy over the pedestrian gate, carried by the stone pier and the jamb.
                        c0, c1 = min(l0, jamb[0]) - .06, max(l1, jamb[1]) + .06
                        rect((c0, ymin - .55, top_l + .04, c1, ymin + wt + .3, top_l + .12), 'frame', role='canopy', name='exterior-gate-canopy', owner='exterior-gate-canopy')
                        gc = (x0 + x1) / 2
                        rect((gc - .06, ymin - .06, top_l + .035, gc + .06, ymin + .06, top_l + .04), 'lamp', role='downlight', owner='exterior-gate-canopy')
                        k.light((gc, ymin, top_l - .1), 9, kind='downlight')
                # The leaf stands open into the court against its hinge jamb; a flush stone sill marks the gateway.
                rect((x0, ymin - .02, g - .02, x1, ymin + wt + .02, g + (.105 if modern else .05)), 'step', role='gate', name='exterior-gate-sill', owner='exterior-pedestrian-gate')
                L, hgt = x1 - x0 - .06, (fh - .05 if modern else .95 - g)
                mark = len(k.nodes)
                ang = 0 if doors_closed else math.radians(gate.get('open_deg', 85))
                dx, dy = (-math.cos(ang), math.sin(ang)) if hinge_right else (math.cos(ang), math.sin(ang))
                hx, hy = (x1 - .03 if hinge_right else x0 + .03), ymin + wt + .04
                rot = math.atan2(dy, dx)
                at = lambda t, z: (hx + dx * t, hy + dy * t, z)
                zb = g + (.11 if modern else .06)
                for z in (zb + .03, zb + hgt - .03):
                    rb(at(L / 2, z), (L, .05, .05), 'frame', -1, 'gate', .006, rot=rot, owner='exterior-pedestrian-gate')
                for t in (.025, L - .025):
                    rb(at(t, zb + hgt / 2), (.05, .05, hgt), 'frame', -1, 'gate', .006, rot=rot, owner='exterior-pedestrian-gate')
                if modern:
                    z = zb + .12
                    while z < zb + hgt - .1:
                        rb(at(L / 2, z), (L - .08, .03, .07), 'frame', -1, 'gate', .004, rot=rot, owner='exterior-pedestrian-gate')
                        z += .105
                else:
                    for t in np.arange(.13, L - .1, .12):
                        rb(at(t, zb + hgt / 2), (.025, .025, hgt - .08), 'frame', -1, 'gate', .004, rot=rot, owner='exterior-pedestrian-gate')
                rb(at(L - .09, zb + 1.0), (.03, .09, .16), 'brass', -1, 'fixture', .01, rot=rot, owner='exterior-pedestrian-gate')
                if doors_closed:
                    gates.append({'id':'exterior-pedestrian-gate','label':'Pedestrian gate','floor':-1,'kind':'gate',
                                  'start':[x0,hy,g],'axis':[1,0,0],'width':x1-x0,'height':hgt+.11,'base':g,'sill':0,'initial':0,
                                  'parts':[{'ids':[n['id'] for n in k.nodes[mark:]],'pivot':[hx,hy,zb],'angle':-math.pi/2 if hinge_right else math.pi/2}]})
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
        if custom:
            slab=metres(plate(b,f))
            stair_holes[f]=metres(floor_outline(b,f)).difference(slab)
        elif f:
            st = b['stairs'][f]; sx = st['x'] / 1000; sy = st['y'] / 1000
            stair_holes[f] = box(sx, sy + 1.05, sx + st['width'] / 1000, sy + st['depth'] / 1000)
            slab = slab.difference(stair_holes[f])
        poly_mesh(slab, level - .15, level, 'slab', f, 'floor', f'F{f}-floor')
        for s in [s for s in b['spaces'] if s['floor'] == f and s['kind'] not in ({'stair'} | NON_WALKABLE)]:
            p = Polygon(np.array(s['clear']) / 1000)
            mat = 'woodfloor' if s['kind'] in ('bedroom', 'study') else 'wetfloor' if s['kind'] in ('bathroom', 'powder-room', 'utility','drying-room') else 'deck' if (s['kind'] == 'terrace' and modern) else 'floor'
            poly_mesh(p, level + .002, level + .009, mat, f, 'finish', s['id'] + '/floor', s['id'])
        # Ceiling coves with a concealed warm glow line.
        for s in [s for s in b['spaces'] if s['floor'] == f and s['kind'] in ('living', 'drawing-room', 'family', 'bedroom', 'dining')]:
            p = Polygon(np.array(s['clear']) / 1000)
            if custom:p=p.intersection(metres(geometry(b['roofs'][f]['ceiling'])))
            inner = p.buffer(-.16)
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
    if custom or rooftop:roof_fp=metres(roof(b,storeys-1))
    for f in range(storeys):
        ceil = roof_fp if f == storeys - 1 else fp.difference(stair_holes.get(f + 1, Polygon()))
        if custom:ceil=metres(geometry(b['roofs'][f]['ceiling']))
        poly_mesh(ceil, (f + 1) * H - .157, (f + 1) * H - .151, 'ceiling', f, 'ceiling', f'F{f}-ceiling')

    # ---------------------------------------------------------------- roof
    if custom:
        for f in range(storeys):
            poly_mesh(metres(roof(b,f)),(f+1)*H-.15,(f+1)*H,'roof',f,'roof',b['roofs'][f]['id'])
    else:
        poly_mesh(roof_fp, top - .15, top, 'roof', storeys - 1, 'roof', 'roof-slab')
    fr = storeys - 1
    tower = next((a for a in assemblies if a['geometry'].get('kind') == 'stair_tower'), None)
    tower_fp = box(*[q / 1000 for q in tower['geometry']['bounds_mm']]) if tower else Polygon()
    if rooftop:
        tower_fp=unary_union([box(*[q/1000 for q in core['bounds']]) for core in rooftop['cores']])

    def solar(field, rear, z):
        """Photovoltaic modules on a light rack over the rear of the roof, tilted toward the midday sun."""
        south = enu_to_local(0, -1, v.get('road_bearing_deg', 180))
        tilt = math.radians(12) * (1 if south[1] < 0 else -1)
        fx0, fy0, fx1, fy1 = field.bounds
        rack = field.buffer(-.35).intersection(box(fx0, fy0 + (fy1 - fy0) * rear, fx1, fy1))
        placed = 0
        for yy in np.arange(fy1 - 1.3, fy0, -2.05):
            for xx in np.arange(fx0 + .9, fx1 - .5, 1.06):
                if placed >= 16 or not rack.contains(box(xx - .5, yy - .83, xx + .5, yy + .83)):
                    continue
                node(cube, 'solar', (xx, yy, z + .39), (1.0, 1.66, .035), (tilt, 0, 0), fr, 'roof')
                node(cube, 'steel', (xx, yy, z + .37), (1.02, 1.68, .02), (tilt, 0, 0), fr, 'roof')
                for dy, hh in ((-.7, .21), (.7, .57)):
                    y_leg = yy + dy
                    for lx in (xx - .47, xx + .43):
                        rect((lx, y_leg - .02, z, lx + .04, y_leg + .02, z + (hh if tilt > 0 else .78 - hh)), 'steel', fr, 'roof')
                placed += 1
        return rack if placed else Polygon()

    def roof_sala(zone, z, S=2.5):
        """A timber-slat sala on a floating deck, as in the reference garden: set in the corner of the roof terrace
        farthest from the street and the stair tower, open towards the rest of the terrace, and only where the
        loungers still fit beside it. Returns its footprint, or None."""
        zx0, zy0, zx1, zy1 = zone.bounds
        best = None
        for sx in np.arange(zx0 + S / 2, zx1 - S / 2 + 1e-6, .2):
            for sy in np.arange(zy0 + S / 2, zy1 - S / 2 + 1e-6, .2):
                foot = box(sx - S / 2, sy - S / 2, sx + S / 2, sy + S / 2)
                if not zone.contains(foot):
                    continue
                rest = [q for q in _parts(zone.difference(foot.buffer(.35, join_style=2))) if q.area > 3]
                big = max(rest, key=lambda q: q.area) if rest else None
                if big is None:
                    continue
                c = big.centroid
                if not big.contains(box(c.x - .9, c.y - 1.1, c.x + .9, c.y + 1.1)):
                    continue
                score = sy + .5 * min(foot.distance(tower_fp), 3.) if not tower_fp.is_empty else sy
                if best is None or score > best[0]:
                    best = (score, sx, sy, c)
        if best is None:
            return None
        _, sx, sy, c = best
        # Open towards the rest of the terrace; the slatted screen closes the opposite side.
        ox, oy = c.x - sx, c.y - sy
        o = (np.sign(ox), 0.) if abs(ox) >= abs(oy) else (0., np.sign(oy))
        h = S / 2
        own = 'roof-sala'
        rect((sx - h + .08, sy - h + .08, z, sx + h - .08, sy + h - .08, z + .1), 'frame', fr, 'sala', owner=own)
        rect((sx - h, sy - h, z + .1, sx + h, sy + h, z + .16), 'deck', fr, 'sala', 'roof-sala-deck', own)
        # A hidden LED strip under the deck's open edge.
        ex_, ey_ = sx + o[0] * (h - .09), sy + o[1] * (h - .09)
        if o[0]:
            rect((ex_ - .005, sy - h + .15, z + .05, ex_ + .005, sy + h - .15, z + .09), 'lamp', fr, 'fixture', owner=own)
        else:
            rect((sx - h + .15, ey_ - .005, z + .05, sx + h - .15, ey_ + .005, z + .09), 'lamp', fr, 'fixture', owner=own)
        k.light((sx + o[0] * (h + .3), sy + o[1] * (h + .3), z + .12), 5, kind='lantern')
        top_z = z + 2.55
        for px in (sx - h + .12, sx + h - .12):
            for py in (sy - h + .12, sy + h - .12):
                rect((px - .045, py - .045, z + .16, px + .045, py + .045, top_z), 'frame', fr, 'sala', owner=own)
        rect((sx - h - .15, sy - h - .15, top_z, sx + h + .15, sy + h + .15, top_z + .1), 'frame', fr, 'sala', 'roof-sala-roof', own)
        for t in np.arange(-h + .08, h - .05, .1):
            if o[0]:
                rect((sx - h + .05, sy + t, top_z - .06, sx + h - .05, sy + t + .045, top_z), 'timber', fr, 'sala', owner=own)
            else:
                rect((sx + t, sy - h + .05, top_z - .06, sx + t + .045, sy + h - .05, top_z), 'timber', fr, 'sala', owner=own)
        # Vertical timber slats close the back.
        bx_, by_ = sx - o[0] * (h - .12), sy - o[1] * (h - .12)
        for t in np.arange(-h + .2, h - .2, .09):
            if o[0]:
                rect((bx_ - .02, sy + t, z + .16, bx_ + .02, sy + t + .04, top_z - .06), 'timber', fr, 'sala', owner=own)
            else:
                rect((sx + t, by_ - .02, z + .16, sx + t + .04, by_ + .02, top_z - .06), 'timber', fr, 'sala', owner=own)
        # A daybed against the screen, a low table in front of it and a pendant over them.
        dx_, dy_ = sx - o[0] * .55, sy - o[1] * .55
        size = (.8, S - .7) if o[0] else (S - .7, .8)
        rb((dx_, dy_, z + .16 + .2), (size[0], size[1], .2), 'frame', fr, 'outdoor-furniture', .02, owner=own)
        rb((dx_, dy_, z + .16 + .36), (size[0] - .04, size[1] - .04, .14), 'fabric', fr, 'outdoor-furniture', .05, owner=own)
        rb((sx - o[0] * .98, sy - o[1] * .98, z + .16 + .62), ((.16, S - .8, .4) if o[0] else (S - .8, .16, .4)), 'fabric-dark', fr, 'outdoor-furniture', .06, owner=own)
        rb((sx + o[0] * .35, sy + o[1] * .35, z + .16 + .2), (.6, .6, .06), 'stone', fr, 'outdoor-furniture', .03, owner=own)
        beam((sx, sy, top_z - .06), (sx, sy, top_z - .7), .006, 'frame', fr, 'fixture')
        ball((sx, sy, top_z - .78), (.22, .22, .16), 'globe', fr, 'fixture')
        k.light((sx, sy, top_z - .9), 14, kind='pendant')
        return box(sx - h - .15, sy - h - .15, sx + h + .15, sy + h + .15)

    if custom:
        # Per-floor roof edges use the selected palette, without bridging an authored terrace or void.
        for f in range(storeys):
            field=metres(roof(b,f));edge=field.difference(field.buffer(-.15,join_style=2)).difference(tower_fp);z=(f+1)*H
            poly_mesh(edge,z,z+.22,'roof' if modern else 'wall',f,'parapet','custom-roof-edge-'+str(f))
            poly_mesh(field.buffer(-.15,join_style=2),z,z+.025,'paver' if rooftop and f==storeys-1 else 'gravel',f,'roof','custom-roof-finish-'+str(f))
    elif modern:
        # A deep eave along the street front (shade, and a soffit of timber slats with downlights); 0.45 m on
        # the other sides. Terraces open in the roof and the porch canopy keep their own edges.
        fb = fp.bounds
        front = box(fb[0] - .45, -1.0, fb[2] + .45, 0)
        for terrace in terraces:
            tx0, ty0, tx1, _ = terrace.bounds
            if ty0 < .05:
                front = front.difference(box(tx0 - .01, -1.1, tx1 + .01, .01))
        if porch_asm and not porch_asm['geometry'].get('canopy_is_balcony'):
            pa = [q / 1000 for q in porch_asm['geometry']['bounds_mm']]
            front = front.difference(box(pa[0] - .3, pa[1] - porch_asm['geometry'].get('canopy_overhang_mm', 300) / 1000 - .05, pa[2] + .3, .01))
        roof_outline = metres(geometry(rooftop['outline'])) if rooftop else roof_fp
        over = roof_outline.buffer(.45, join_style=2).union(front)
        for terrace in terraces:
            over = over.difference(terrace)
        if porch_asm and not porch_asm['geometry'].get('canopy_is_balcony'):
            over = over.difference(box(pa[0] - .3, pa[1] - porch_asm['geometry'].get('canopy_overhang_mm', 300) / 1000, pa[2] + .3, 0))
        poly_mesh(over.difference(roof_outline), top - .15, top + .22, 'roof', fr, 'fascia', 'roof-overhang')
        eave = front.intersection(over).difference(fp.buffer(.02, join_style=2))
        for xx in np.arange(fb[0] - .4, fb[2] + .4, .11):
            for part in _parts(eave.intersection(box(xx, -.97, xx + .06, -.03))):
                poly_mesh(part, top - .176, top - .15, 'timber', fr, 'soffit')
        span = [q for q in _parts(eave) if q.area > .5]
        for part in span:
            ex0, _, ex1, _ = part.bounds
            for xx in np.linspace(ex0 + .6, ex1 - .6, max(1, round((ex1 - ex0) / 2.2))):
                cylinder((xx, -.5, top - .185), .045, .01, 'lamp', fr, 'downlight')
                k.light((xx, -.62, top - .35), 12, kind='soffit')
        poly_mesh(roof_fp.difference(roof_fp.buffer(-.22, join_style=2)).difference(tower_fp), top, top + .22, 'roof', fr, 'parapet', 'roof-upstand')
        field = roof_fp.buffer(-.22, join_style=2).difference(tower_fp)
        if tower:
            # Open roof terrace beside the stair tower: pavers, a frameless glass balustrade, loungers, planters.
            poly_mesh(field, top, top + .03, 'paver', fr, 'roof', 'roof-terrace-pavers')
            rail = LineString() if rooftop else roof_fp.buffer(-.3, join_style=2).exterior.difference(tower_fp.buffer(.32, join_style=2))
            for piece in getattr(rail, 'geoms', [rail]):
                if piece.length < .3:
                    continue
                poly_mesh(piece.buffer(.009, cap_style=2, join_style=2), top + .1, top + 1.02, 'railglass', fr, 'railing')
                poly_mesh(piece.buffer(.03, cap_style=2, join_style=2), top + .03, top + .1, 'frame', fr, 'railing')
                poly_mesh(piece.buffer(.022, cap_style=2, join_style=2), top + 1.02, top + 1.055, 'frame', fr, 'railing')
        else:
            poly_mesh(field, top, top + .025, 'gravel', fr, 'roof', 'roof-gravel')
        rack = solar(field, .5 if tower else .35, top + .03)
        if tower:
            # Loungers and planted pots on the open part of the terrace, clear of the array and the tower door.
            used = rack.buffer(.4)
            free = field.buffer(-.45, join_style=2).difference(used).difference(tower_fp.buffer(1.3, join_style=2))
            spots = sorted(_parts(free), key=lambda q: -q.area)
            if spots:
                zone = spots[0]
                sala = roof_sala(zone, top + .03)
                if sala is not None:
                    rest = sorted(_parts(zone.difference(sala.buffer(.35, join_style=2))), key=lambda q: -q.area)
                    zone = rest[0]
                cx, cy = zone.centroid.x, zone.centroid.y
                for dx in (-.45, .45):
                    lx, ly = cx + dx, cy
                    if not zone.contains(box(lx - .36, ly - 1.0, lx + .36, ly + 1.0)):
                        continue
                    for sx in (-.3, .3):
                        for sy in (-.85, .85):
                            rect((lx + sx - .02, ly + sy - .02, top + .03, lx + sx + .02, ly + sy + .02, top + .3), 'frame', fr, 'roof')
                    rect((lx - .34, ly - .95, top + .3, lx + .34, ly + .95, top + .33), 'frame', fr, 'roof')
                    rb((lx, ly - .3, top + .38), (.64, 1.2, .09), 'sling', fr, 'roof', .035)
                    node(asset(rounded_box((.64, .72, .09), .03), smooth=True), 'sling', (lx, ly + .56, top + .55), rot=(math.radians(38), 0, 0), floor=fr, role='roof')
                if zone.contains(box(cx - .2, cy - .2, cx + .2, cy + .2)):
                    cylinder((cx, cy, top + .24), .2, .42, 'counter', fr, 'roof')
                x0z, y0z, x1z, y1z = zone.bounds
                for i, (px, py) in enumerate(((x0z + .35, y0z + .35), (x1z - .35, y0z + .35), (x0z + .35, y1z - .35), (x1z - .35, y1z - .35))):
                    if zone.contains(Point(px, py)) and not box(cx - 1.0, cy - 1.2, cx + 1.0, cy + 1.2).contains(Point(px, py)):
                        # (floor = storeys: the roof level, above every storey a dollhouse cut can show)
                        k.plant(px, py, top + .03, 'strelitzia' if i % 2 == 0 else 'grass_ornamental', f=storeys, scale=.6, pot=(.26, .62, 'planter'))
        for f in range(1, storeys):
            band = fp.buffer(.1, join_style=2).difference(fp)
            poly_mesh(band, f * H - .25, f * H - .02, 'roof', f - 1, 'band', f'F{f}-slab-band')
    else:
        parapet = roof_fp.difference(roof_fp.buffer(-.15)).difference(tower_fp)
        poly_mesh(parapet, top, top + .6, 'wall', storeys - 1, 'roof', 'parapet')
        poly_mesh(fp.buffer(.025).difference(fp.buffer(-.175)).difference(tower_fp.buffer(.03, join_style=2)), top + .60, top + .65, 'stone', storeys - 1, 'roof', 'coping')
        if theme_id != 'current':
            solar(roof_fp.buffer(-.15, join_style=2).difference(tower_fp), .35, top)

    # ---------------------------------------------------------------- walls (true voids, split at sill/lintel)
    # Wall polygons overlap at corners and T-junctions. Each storey's walls are tiled instead: external walls
    # claim junctions first and later walls keep only what is still unfilled, so no two solids share a face
    # (coincident faces shade black in path tracers and z-fight in other viewers). Colliders keep full polygons.
    tiled = {}
    for f in range(storeys + bool(rooftop)):
        taken = Polygon()
        for w in sorted((w for w in rb_model['walls'] if w['floor'] == f), key=lambda w: (not bool(w.get('underStair')),not w['external'])):
            full = Polygon(np.array(w['polygon']) / 1000)
            own = full.difference(taken) if not taken.is_empty else full
            tiled[w['id']] = unary_union([q for q in get_parts(own) if q.geom_type == 'Polygon' and q.area > 1e-5])
            taken = taken.union(full)
    for w in rb_model['walls']:
        openings = [o for o in rb_model['openings'] if o['wall_id'] == w['id']]
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
    space_kind = {s['id']: s['kind'] for s in rb_model['spaces']}
    space_poly = {s['id']: Polygon(np.array(s['polygon']) / 1000, [np.array(h)/1000 for h in s.get('holes',[])]) for s in rb_model['spaces']}
    for o in rb_model['openings']:
        w = hosts[o['wall_id']]; a = np.array(w['a']) / 1000; bb = np.array(w['b']) / 1000; uv = (bb - a) / np.linalg.norm(bb - a); nv = np.array([-uv[1], uv[0]]); ang = math.atan2(uv[1], uv[0]); p = a + uv * o['offset'] / 1000
        if not fp.covers(Point(*(p + uv * o['width'] / 2000 + nv * .4))):
            nv = -nv
        if custom and o['kind']=='window':
            # Courtyards and terraces also belong to the footprint. Pick the enclosed
            # room explicitly so curtains stay indoors and projecting reveals outdoors.
            indoor=next((space_poly[r] for r in w['rooms'] if space_kind.get(r) not in OUTDOOR and space_kind.get(r) not in NON_WALKABLE),None)
            if indoor is not None and not indoor.covers(Point(*(p+uv*o['width']/2000+nv*.3))):nv=-nv
        base = o['floor'] * H; ow = o['width'] / 1000; z0 = base + o['sill'] / 1000; zh = o['height'] / 1000
        t_half = w['thickness'] / 2000

        def part(x, depth, z, sx, sy, sz, mat='frame', role='joinery'):
            q = p + uv * x + nv * depth
            node(cube, mat, (q[0], q[1], z), (sx, sy, sz), (0, 0, ang), o['floor'], role, owner=o['id'])
        if o['kind'] == 'cased':
            continue
        room_kinds = [space_kind.get(room, 'secondary') for room in w['rooms']]
        if o['kind'] == 'window':
            # One contemporary window system for every theme: slim powder-coated aluminium, staggered sliding
            # panes, a transom on tall glazing and a slim sill; wet rooms get obscured glass.
            wet = bool(set(room_kinds) & {'bathroom', 'utility', 'drying-room', 'toilet', 'wc', 'powder'})
            fw, fd = .045, .075
            part(fw / 2, 0, z0 + zh / 2, fw, fd, zh); part(ow - fw / 2, 0, z0 + zh / 2, fw, fd, zh)
            part(ow / 2, 0, z0 + zh - fw / 2, ow, fd, fw); part(ow / 2, 0, z0 + fw / 2, ow, fd, fw)
            panels = 1 if 'pooja' in room_kinds and zh < .7 else max(1 if ow < .9 else 2, math.ceil(ow / 1.25))
            for i in range(1, panels):
                part(ow * i / panels, 0, z0 + zh / 2, .04, fd, zh - 2 * fw)
            if zh > 2.4:
                part(ow / 2, 0, z0 + 2.12, ow - 2 * fw, fd, .04)
            for i in range(panels):
                part(ow * (i + .5) / panels, (i % 2) * .028 - .014, z0 + zh / 2, ow / panels - .04, .012, zh - 2 * fw, 'frosted' if wet else 'glass', 'glass')
            if o['sill'] > 100:
                part(ow / 2, t_half - .05, z0 - .02, ow, .14, .03, M['counter'], 'sill')
            pod = zh < 2.6 and ((w['external'] and 'bedroom' in room_kinds) or (b.get('planning',{}).get('facadeStyle')=='warm-layered' and o['floor']==1 and 'courtyard' not in room_kinds and o['sill']>100))
            if pod:
                # Window pod: a slim projecting box, lined with warm timber, gives bedroom glazing depth and shade.
                shell, reveal = WINDOW_POD.get(theme_id, WINDOW_POD['current'])
                d = .16 if 'terrace' in room_kinds else .34; y = -t_half - d / 2
                part(-.025, y, z0 + zh / 2, .05, d, zh + .1, shell, 'window-surround')
                part(ow + .025, y, z0 + zh / 2, .05, d, zh + .1, shell, 'window-surround')
                part(ow / 2, y, z0 + zh + .025, ow + .1, d, .05, shell, 'window-surround')
                part(ow / 2, y, z0 - .025, ow + .1, d, .05, shell, 'window-surround')
                if reveal:
                    part(.008, y, z0 + zh / 2, .016, d - .02, zh, reveal, 'window-surround')
                    part(ow - .008, y, z0 + zh / 2, .016, d - .02, zh, reveal, 'window-surround')
                    part(ow / 2, y, z0 + zh - .008, ow - .032, d - .02, .016, reveal, 'window-surround')
            elif o['sill'] > 100 and w['external']:
                part(ow / 2, -t_half - .03, z0 - .015, ow + .06, .09, .03, 'frame', 'sill')
            if w['external'] and not modern and not pod and zh < 2.6 and set(room_kinds) & {'living', 'drawing-room', 'family', 'dining'}:
                # A slim floating eyebrow in the theme's accent shades the living-room glazing.
                part(ow / 2, -t_half - .225, z0 + zh + .1, ow + .3, .45, .05, WINDOW_EYEBROW.get(theme_id, 'frame'), 'window-hood')
        if o['kind'] == 'window':
            # Pleated sheer curtains on the room side.
            if zh > 1. and not ('bathroom' in room_kinds or 'utility' in room_kinds or 'drying-room' in room_kinds):
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
        if o.get('timberScreen'):
            # Two full timber leaves outside, two independent insect-screen leaves inside.
            # Timber swings outward; the optional screen bypasses its fixed companion.
            outside=space_poly[o['swing']]
            materials['insect-mesh']={'color':'#f5f3ed','roughness':.9,'alpha':.09,'kind':'insect-mesh','spacing':.008,'wire':.00035}
            materials['screen-wire-white']={'color':'#f5f3ed','roughness':.9}
            if not outside.covers(Point(*(p+uv*ow/2+nv*.3))):nv=-nv
            for xx in (.035,ow-.035):part(xx,0,z0+zh/2,.07,.30,zh,'walnut')
            part(ow/2,0,z0+zh-.035,ow,.30,.07,'walnut')
            layers=[];lw=(ow-.14)/2-.004;lh=zh-.09
            if o.get('screenSliding'):
                # Recessed floor guide and slim head track stay inside the existing reveal.
                for zz in (z0+.008,z0+zh-.054):part(ow/2,-.175,zz,ow-.14,.18,.016,'frame')
            for layer,layer_depth,direction in [('timber',.105,1),('mesh',-.105,-1)]:
                for side in range(2):
                    depth=layer_depth-(.14*side if layer=='mesh' and o.get('screenSliding') else 0)
                    mark=len(k.nodes);sgn=1 if side==0 else -1
                    hinge_x=.07 if side==0 else ow-.07
                    cx=hinge_x+sgn*lw/2
                    if layer=='timber':
                        part(cx,depth,z0+.025+lh/2,lw,.055,lh,'walnut','door')
                        # Inset warm oak field and thin dark reveals on both faces.
                        for face in (-1,1):
                            part(cx,depth+face*.029,z0+.025+lh/2,lw-.13,.006,lh-.14,'oak','door')
                            for groove in (-.30,0,.30):
                                part(cx+groove,depth+face*.033,z0+.025+lh/2,.004,.003,lh-.16,'walnut','door')
                    else:
                        for xx in (hinge_x+sgn*.021,hinge_x+sgn*(lw-.021)):
                            part(xx,depth,z0+.025+lh/2,.042,.032,lh,'frame','door')
                        for zz in (z0+.046,z0+.025+lh-.021):
                            part(cx,depth,zz,lw,.032,.042,'frame','door')
                        part(cx,depth,z0+.10,lw,.033,.12,'frame','door')
                        # Real wire mesh with open holes; shared mesh asset, no glass wash.
                        wires=[];mw=lw-.084;mh=lh-.16
                        for xx in np.arange(-mw/2,mw/2+.001,.008):
                            wires.append(trimesh.creation.box(extents=(.00035,.00035,mh)).apply_translation((xx,0,0)))
                        for zz in np.arange(-mh/2,mh/2+.001,.008):
                            wires.append(trimesh.creation.box(extents=(mw,.00035,.00035)).apply_translation((0,.0002,zz)))
                        q=p+uv*cx+nv*depth
                        node(asset(trimesh.util.concatenate(wires)),'screen-wire-white',(q[0],q[1],z0+.13+mh/2),rot=(0,0,ang),floor=o['floor'],role='screen-wire',owner=o['id'])
                        # Filtered mesh surface in the live view; fine wire geometry remains
                        # in exports. The thin closed surface supplies stable screen collision.
                        part(cx,depth,z0+.13+mh/2,mw,.001,mh,'insect-mesh','door')
                    hx=hinge_x+sgn*(lw-.12)
                    for face in (-1,1):
                        d=depth+face*(.075 if layer=='timber' else .05)
                        part(hx,d,z0+1.15,.025,.026,.72 if layer=='timber' else .28,'frame','door')
                        for zz in ((.81,1.49) if layer=='timber' else (1.03,1.27)):
                            part(hx,depth+face*.047,z0+zz,.025,.075,.024,'frame','door')
                    pivot=p+uv*hinge_x+nv*depth
                    angle=sgn*direction*math.atan2(uv[0]*nv[1]-uv[1]*nv[0],float(np.dot(uv,nv)))
                    handle=p+uv*hx+nv*depth
                    if layer=='mesh' and o.get('screenSliding') and side==0:continue
                    layers.append({'id':f"{o['id']}/{layer}-{'left' if side==0 else 'right'}",
                                   'label':f"{'Timber door' if layer=='timber' else 'Mesh screen'} · {'left' if side==0 else 'right'} leaf",
                                   'ids':[n['id'] for n in k.nodes[mark:]],
                                   **({'slide':[-float(uv[0])*(lw+.004),-float(uv[1])*(lw+.004),0], 'clearWidth':lw-.06} if layer=='mesh' and o.get('screenSliding') else {'pivot':[float(pivot[0]),float(pivot[1]),base], 'angle':angle}),
                                   'handle':[float(handle[0]),float(handle[1]),z0+1.15]})
            door_motion[o['id']]={'layers':layers,'clearWidth':ow-.14}
            continue
        frame_mat = 'frame' if (o['kind'] in ('entry', 'glazed') or not upgraded_interior) else M['doorframe']
        part(.025, 0, z0 + zh / 2, .05, .10, zh, frame_mat); part(ow - .025, 0, z0 + zh / 2, .05, .10, zh, frame_mat)
        part(ow / 2, 0, z0 + zh - .025, ow - .1, .10, .05, frame_mat)
        if o['kind'] == 'glazed' and o.get('sliding'):
            # Authored two- or three-track glazing; matching motion uses the same panel count.
            panel_count=o.get('slidingPanels',3)
            if panel_count==2:
                # Full-width glass meets room corners: park fabric ABOVE the head,
                # instead of pushing side stacks into adjoining rooms or across glass.
                inside=next((space_poly[r] for r in w['rooms'] if space_kind.get(r) not in OUTDOOR),None)
                cn=nv if inside is None or inside.covers(Point(*(p+uv*ow/2+nv*.2))) else -nv
                for fold in range(4):
                    q=p+uv*ow/2+cn*(.16+fold*.012)
                    node(cube,'linen',(q[0],q[1],z0+zh+.065+fold*.035),(ow-.1,.075,.033),(0,0,ang),o['floor'],'curtain',owner=o['id'])
            for pane in range(panel_count):
                mark=len(k.nodes);pw=(ow-.1)/panel_count;left=.05+pane*pw;depth=pane*.035
                part(left+pw/2,depth,z0+zh/2,pw-.035,.018,zh-.1,'glass','glass')
                for xx in (left,left+pw):part(xx,depth,z0+zh/2,.035,.045,zh-.06)
                for zz in (z0+.025,z0+zh-.025):part(left+pw/2,depth,zz,pw,.045,.05)
                for item in k.nodes[mark:]:item['slidingPanel']=pane
            continue
        mark = len(k.nodes)
        if o['kind'] == 'glazed' and doors_closed:
            # Closed full-width hinged glazing; fixed jambs are outside the moving set.
            part(ow/2,0,z0+zh/2,ow-.1,.018,zh-.1,'glass','glass')
            for xx in (.05,ow-.05):part(xx,0,z0+zh/2,.035,.07,zh-.06)
            for zz in (z0+.04,z0+zh-.04):part(ow/2,0,zz,ow-.1,.07,.04)
            pivot=p+uv*(ow-.05)
            angle=math.atan2(-uv[0]*nv[1]+uv[1]*nv[0],-uv[0]*nv[0]-uv[1]*nv[1])
            door_motion[o['id']]={'ids':[n['id'] for n in k.nodes[mark:]],'pivot':[float(pivot[0]),float(pivot[1]),base],'angle':angle}
        elif o['kind'] == 'glazed':
            # A partly-open sliding glass leaf, not an opaque balcony door.
            part(ow * .74, 0, z0 + zh / 2, ow * .47, .018, zh - .1, 'glass', 'glass')
            for xx in (ow * .505, ow - .04):
                part(xx, 0, z0 + zh / 2, .035, .07, zh - .04)
            part(ow * .74, 0, z0 + .025, ow * .48, .07, .05)
        elif o['kind'] == 'entry' and modern:
            # A tall timber pivot door, shown open, turned about a pivot a sixth of the way across: grooved walnut
            # with long black pulls on both faces, set in a black steel portal that stands proud of the render.
            lw = ow - .1; pv = p + uv * (.05 + lw * .17); leafcenter = pv + nv * lw * (.5 - .17)
            rb((leafcenter[0], leafcenter[1], base + zh / 2), (.056, lw, zh - .04), 'walnut', o['floor'], 'door', .006, ang, owner=o['id'])
            for zz in np.arange(base + .32, base + zh - .25, .32):
                rb((leafcenter[0], leafcenter[1], zz), (.06, lw - .08, .007), 'frame', o['floor'], 'door', .002, ang, owner=o['id'])
            for side in (-1, 1):
                q = pv + nv * (lw * .83 - .1) + uv * side * .075
                beam((q[0], q[1], base + .55), (q[0], q[1], base + min(2.05, zh - .3)), .016, 'frame', o['floor'], 'door')
            dp = .18; yy = -t_half - dp / 2 + .01
            part(-.06, yy, z0 + (zh + .12) / 2, .12, dp, zh + .12, 'frame', 'door-portal')
            part(ow + .06, yy, z0 + (zh + .12) / 2, .12, dp, zh + .12, 'frame', 'door-portal')
            part(ow / 2, yy, z0 + zh + .06, ow + .24, dp, .12, 'frame', 'door-portal')
        else:
            # Leaves shown open 90 degrees into the room they serve, hinged on the planned jamb so the leaf folds
            # back against the nearer wall; no invisible solid wall remains in the portal.
            if o.get('swing') in space_poly:
                if not space_poly[o['swing']].buffer(.05).contains(Point(*(p + uv * ow / 2 + nv * (t_half + .3)))):
                    nv = -nv
            hinge = p + uv * (.055 if o.get('hinge', 'start') == 'start' else ow - .055); leafcenter = hinge + nv * (ow - .1) / 2
            leaf_mat = 'walnut' if (upgraded_interior and (o['kind'] == 'entry' or (w['external'] and 'hall' in room_kinds and b.get('planning',{}).get('facadeStyle')=='warm-layered'))) else M['door']
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

        if doors_closed and o['kind'] in ('door','entry'):
            # Store closed canonical geometry for exports, with explicit inward runtime motion.
            pivot = pv if o['kind']=='entry' and modern else hinge
            direction = uv if o.get('hinge','start')=='start' or (o['kind']=='entry' and modern) else -uv
            angle = math.atan2(direction[0]*nv[1]-direction[1]*nv[0],float(np.dot(direction,nv)))
            cc,ss=math.cos(-angle),math.sin(-angle)
            moving=[n for n in k.nodes[mark:] if n['role']=='door']
            for item in moving:
                xx,yy=item['position'][0]-pivot[0],item['position'][1]-pivot[1]
                item['position'][0]=float(pivot[0]+cc*xx-ss*yy)
                item['position'][1]=float(pivot[1]+ss*xx+cc*yy)
                item['rotation'][2]-=angle
            door_motion[o['id']]={'ids':[n['id'] for n in moving],'pivot':[float(pivot[0]),float(pivot[1]),base],'angle':angle}

    # ---------------------------------------------------------------- furniture
    def lamp(x, y, z, f, pendant=False):
        if custom and pendant and not metres(geometry(b['roofs'][f]['ceiling'])).covers(Point(x,y)):return
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
        if custom and not metres(geometry(b['roofs'][f]['ceiling'])).covers(Point(x,y)):return
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
        if custom:p=p.intersection(metres(geometry(b['roofs'][f]['ceiling'])))
        if p.is_empty:return
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

    # ---------------------------------------------------------------- furniture placement
    # Every piece stands against a solid stretch of wall, clear of the swing or approach zone of each door, of
    # windows lower than the piece, and of pieces already placed; the room's clear polygon (L-shapes included)
    # is the only floor it may occupy.
    solid = {f: prep(wall_union[f]) for f in range(storeys)}

    def open_keepouts(ctx):
        """Open edges a room shares with the stair or the hall stay walkable: 1 m in front of the stair, the hall's
        mouth and every open connection to another public room."""
        room, clear = ctx['room'], ctx['clear']
        zones = []
        for s in b['spaces']:
            if s['floor'] != room['floor'] or s['id'] == room['id'] or s['kind'] not in ('stair', 'hall', 'living', 'dining', 'family'):
                continue
            other = Polygon(np.array(s['polygon']) / 1000)
            edge = other.intersection(Polygon(np.array(room['polygon']) / 1000).buffer(.01))
            if edge.is_empty or edge.area < .002:
                continue
            reach = 1.0 if s['kind'] == 'stair' else .6
            zones.append(edge.buffer(reach).intersection(clear))
        return [z for z in zones if not z.is_empty]

    def free_path(ctx, block, a, b2):
        """True when a 0.8 m wide route still joins points a and b2 around `block`."""
        free = ctx['clear'].buffer(-.4).difference(block.buffer(.4))
        if free.is_empty:
            return False
        pa, pb = Point(*a), Point(*b2)
        for part in _parts(free):
            if part.buffer(.45).contains(pa) and part.buffer(.45).contains(pb):
                return True
        return False

    def sofa_group(ctx):
        """Sofa facing a media wall at viewing distance (floating in the room if need be), coffee table, rug, arc
        lamp and a lounge chair; failing a media wall, a sofa backed by a wall (a low sill is acceptable)."""
        room, f, clear = ctx['room'], ctx['floor'], ctx['clear']; z = f * H
        if room.get('seatingExtension'):
            # A wall-backed sofa may span the zoning edge of an adjoining open
            # hall. The physical walls, door swings and passage remain intact.
            other = next((r for r in b['spaces'] if r['id']==room['seatingExtension'] and r['floor']==f and r['kind']=='hall'), None)
            links = [o for o in b['openings'] if o['kind']=='cased' and o['width']>=2400 and not o.get('servingCounter') and set(o['connects'])=={room['id'],room['seatingExtension']}]
            if other is None or not links:
                raise ValueError('Authored seating extension requires a directly connected open hall.')
            extra = room_context(other)
            bridges = [metres(opening_polygon(hosts[o['wall_id']],o,200)) for o in links]
            clear = unary_union([clear,extra['clear'],*bridges])
            link_ids = {o['id'] for o in links}
            ctx = {**ctx, 'clear':clear, 'inside':prep(clear.buffer(.004)),
                   'doors':[(q,o) for q,o in ctx['doors']+extra['doors'] if o.get('id') not in link_ids and o['kind']!='open'],
                   'windows':ctx['windows']+extra['windows'], 'placed':ctx['placed']+extra['placed']}
        keep = [q for q, _ in ctx['doors']]
        if 'diningOrientation' in room:
            keep += [Polygon(item['footprint']).buffer(.9,join_style=2) for item in furniture if item['room_id']==room['id'] and item['kind']=='dining-set']

        def fits(sp, length, table=True):
            pieces = [lpoly(sp, -length / 2, length / 2, .2, 1.18)] + ([lpoly(sp, -.55, .55, 1.525, 2.275)] if table else [])
            legroom = lpoly(sp, -length / 2 + .3, length / 2 - .3, 1.18, 1.75)
            return all(ctx['inside'].covers(q) and not hits(q, keep) and not hits(q, ctx['placed']) for q in pieces) and ctx['inside'].covers(legroom)
        choice = None
        if room.get('sofaPosition'):
            theta=math.radians(room['sofaOrientation']);n=np.round([math.cos(theta),math.sin(theta)],8)
            centre=np.array(room['sofaPosition'])/1000
            sp={'c':centre-n*.7,'t':np.array([n[1],-n[0]]),'n':n,'s':0.,'L':0.}
            if not fits(sp,2.35):raise ValueError('Authored sofa and coffee table obstruct a wall, furniture or doorway.')
            back=sp['c']+n*.16
            if not wall_behind(f,*back,*n,1.175,.2,.95):raise ValueError('Authored sofa needs a solid backing wall.')
            choice=(sp,2.35,None)
        for m in ([] if choice else sorted(spots(ctx, 2.5, .45, front=2.4, height=2.62, step=.1), key=lambda s: abs(s['s'] - s['L'] / 2))):
            for D in (4.0, 3.8, 3.6):
                for length in (2.35, 2.1, 1.8):
                    sp = {'c': m['c'] + m['n'] * D, 't': -m['t'], 'n': -m['n'], 's': 0., 'L': 0.}
                    if fits(sp, length):
                        choice = (sp, length, (0., m, D))
                        break
                if choice:
                    break
            if choice:
                break
        if choice is None:
            for height, table in ((.95, True), (.3, True), (.95, False), (.3, False)):
                for length in (2.35, 2.1, 1.8, 1.6, 1.4):
                    cands = [c for c in spots(ctx, length, 1.2, front=.6, height=height, step=.05) if fits(c, length, table)]
                    if cands:
                        sp = max(cands, key=lambda c: (round(far_from_doors(ctx, c), 1), -abs(c['s'] - c['L'] / 2)))
                        choice = (sp, length, None)
                        break
                if choice:
                    break
        if choice is None:
            # A floating group in a glazed or open-plan room: facing the widest glazing (the view), with a walkway
            # all round and the stair, doors and open edges left clear.
            x0, y0, x1, y1 = clear.bounds
            views = [(q, o) for q, o in ctx['windows'] if o['sill'] < 900]
            best = None
            for length in (2.35, 2.1, 1.8, 1.6, 1.4):
                for nx_, ny_ in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    n_ = np.array([nx_, ny_], float); t_ = np.array([-ny_, nx_], float) * -1
                    for cx_ in np.arange(x0 + .4, x1 - .4 + 1e-6, .2):
                        for cy_ in np.arange(y0 + .4, y1 - .4 + 1e-6, .2):
                            sp = {'c': np.array([cx_, cy_]), 't': t_, 'n': n_, 's': 0., 'L': 0.}
                            group = lpoly(sp, -length / 2, length / 2, .2, 2.275)
                            if not ctx['inside'].covers(group.buffer(.35)) or hits(group.buffer(.25), keep) or hits(group, ctx['placed']):
                                continue
                            view = sum(o['width'] / 1000 * max(0., float(np.dot(n_, (np.array(q.centroid.coords[0]) - sp['c']) / max(1e-6, np.linalg.norm(np.array(q.centroid.coords[0]) - sp['c'])))))
                                       for q, o in views)
                            gc = np.array(group.centroid.coords[0]); rc = np.array(clear.centroid.coords[0])
                            score = (length, round(view, 1), -float(np.linalg.norm(gc - rc)))
                            if best is None or score > best[0]:
                                best = (score, sp, length)
                if best:
                    break
            if best is None and custom:
                # In an open care/living connection, prefer a freestanding sofa without
                # a coffee table to leaving the lounge empty or blocking the glass doors.
                for length in (2.35,2.1,1.8):
                    for nx_,ny_ in ((0,1),(0,-1),(1,0),(-1,0)):
                        n_=np.array([nx_,ny_],float);t_=np.array([ny_,-nx_],float)
                        for cx_ in np.arange(x0+.4,x1-.4,.2):
                            for cy_ in np.arange(y0+.4,y1-.4,.2):
                                sp={'c':np.array([cx_,cy_]),'t':t_,'n':n_,'s':0.,'L':0.}
                                q=lpoly(sp,-length/2,length/2,.2,1.18)
                                if not fits(sp,length,False) or not ctx['inside'].covers(q.buffer(.15)) or hits(q.buffer(.05),keep):continue
                                score=(length,-q.centroid.distance(clear.centroid))
                                if best is None or score>best[0]:best=(score,sp,length)
                    if best:break
            if best is None:
                return None
            choice = (best[1], best[2], None)
        if custom and not room.get('sofaPosition'):
            above = unary_union([metres(Polygon(r['polygon'])) for r in b['spaces'] if r['floor']==f+1 and r['kind']=='void'])
            above = above.difference(metres(geometry(b['roofs'][f]['ceiling'])))
            if not above.is_empty and above.intersection(clear).area > 2:
                # Keep the seating visible from the authored upper overlook.
                # Door approaches and usable legroom still take precedence.
                best = None
                for length in (2.35, 2.1, 1.8):
                    for nx_,ny_ in ((0,1),(0,-1),(1,0),(-1,0)):
                        for cx_ in np.arange(above.bounds[0], above.bounds[2], .15):
                            for cy_ in np.arange(above.bounds[1], above.bounds[3], .15):
                                sp={'c':np.array([cx_,cy_]),'t':np.array([ny_,-nx_],float),'n':np.array([nx_,ny_],float),'s':0.,'L':0.}
                                q=lpoly(sp,-length/2,length/2,.2,1.18)
                                if not fits(sp,length,False) or q.intersection(above).area/q.area < .8:continue
                                # Keep the complete lounge setting when the dining
                                # arrangement needs a little more space beside it.
                                score=(int(fits(sp,length,True)),length,-q.centroid.distance(above.centroid))
                                if best is None or score>best[0]:best=(score,sp,length)
                if best:choice=(best[1],best[2],None)
        sp, length, fw = choice
        edit_mark = k.edit_mark()
        seating_edit_start = len(k.editables)
        h = length / 2
        lrb(sp, 0, .7, z + .25, (length, .92, .28), 'fabric', f, r=.07)
        lrb(sp, 0, .33, z + .65, (length, .20, .74), 'fabric', f, r=.06)
        for su in (-1, 1):
            lrb(sp, su * (h - .08), .74, z + .55, (.18, .9, .50), 'fabric', f, r=.06)
        for j in range(3):
            lrb(sp, -h + .26 + (j + .5) * (length - .5) / 3, .8, z + .46, ((length - .54) / 3, .69, .20), 'linen', f, r=.055)
        for j in (0, 1):
            x, y = P(sp, -h + .5 + j * max(.6, length - 1.), .72)
            ball((x, y, z + .69), (.27, .15, .25), 'fabric-dark', f, 'furniture', (.2, .2, lrot(sp)))
        for uu in (-h + .2, h - .2):
            x, y = P(sp, uu, .74)
            cylinder((x, y, z + .085), .025, .17, 'brass', f, 'furniture')
        sofa = lpoly(sp, -h, h, .2, 1.18)
        ctx['placed'].append(sofa)
        furnishing('sofa', room, sofa)
        k.editable('sofa', room, sofa, edit_mark)
        table = lpoly(sp, -.55, .55, 1.525, 2.275)
        if ctx['inside'].covers(table) and not hits(table, keep) and not hits(table, ctx['placed']):
            edit_mark = k.edit_mark()
            lrb(sp, 0, 1.9, z + .36, (1.1, .75, .06), M['counter'] if upgraded_interior else 'stone', f, r=.09)
            for vv in (1.68, 2.12):
                x, y = P(sp, 0, vv)
                cylinder((x, y, z + .18), .045, .33, M['table'], f, 'furniture')
            ctx['placed'].append(table)
            furnishing('coffee-table', room, table)
            lbox(sp, -.28, -.08, 1.84, 2.12, z + .394, z + .427, 'linen', f, 'detail')
            vessel = trimesh.creation.revolve(np.array([[.055, 0], [.08, .08], [.075, .16], [.055, .18], [.045, .18], [.064, .15], [.068, .08], [.04, .015]]), sections=24)
            x, y = P(sp, .1, 1.77)
            node(asset(vessel, smooth=True), 'ceramic', (x, y, z + .394), floor=f, role='detail')
            k.editable('coffee-table', room, table, edit_mark)
        rug = lpoly(sp, -h - .15, h + .15, .1, 2.9).intersection(clear.buffer(-.1))
        if not rug.is_empty and rug.geom_type == 'Polygon':
            rx0, ry0, rx1, ry1 = rug.bounds
            rect((rx0, ry0, z + .014, rx1, ry1, z + .022), 'rug', f, 'rug')
        if upgraded_interior and fw is not None:
            _, m, d = fw
            wx, wy = P(m, 0, 0)
            if wall_behind(f, wx, wy, m['n'][0], m['n'][1], 1.25, .2, 2.6):
                for uu in np.arange(-1.22, 1.22, .075):
                    lbox(m, uu, uu + .05, .003, .03, z + .09, z + 2.62, 'walnut', f, 'wall-panel')
            edit_mark = k.edit_mark()
            lbox(m, -.95, .95, .035, .45, z + .26, z + .6, 'walnut', f)
            lbox(m, -.74, .74, .037, .045, z + 1.01, z + 1.85, 'frame', f, 'detail')
            lbox(m, -.73, .73, .045, .085, z + 1.02, z + 1.84, 'blackglass', f, 'detail')
            console = lpoly(m, -.95, .95, .035, .45)
            ctx['placed'].append(console)
            furnishing('media-console', room, console)
            k.editable('media-console', room, console, edit_mark)
        if upgraded_interior:
            # Arc floor lamp at the sofa's end, its shade reaching over the seat.
            for su in (-1, 1):
                base = lpoly(sp, su * (h + .2) - .18, su * (h + .2) + .18, .52, .88)
                if ctx['inside'].covers(base) and not hits(base, ctx['placed']) and not hits(base, keep):
                    bx_, by_ = P(sp, su * (h + .2), .7)
                    ex_, ey_ = P(sp, su * (h + .2) - su * .75, .9)
                    sx_, sy_ = P(sp, su * (h + .2) - su * .8, .9)
                    edit_mark = k.edit_mark()
                    cylinder((bx_, by_, z + .02), .16, .04, 'basalt', f, 'furniture')
                    beam((bx_, by_, z + .04), (bx_, by_, z + 1.55), .012, 'frame', f, 'furniture')
                    beam((bx_, by_, z + 1.55), (ex_, ey_, z + 1.9), .012, 'frame', f, 'furniture')
                    shade = trimesh.creation.cone(radius=.2, height=.2, sections=28)
                    node(asset(shade, smooth=True), 'frame', (sx_, sy_, z + 1.78), rot=(math.pi, 0, 0), floor=f, role='fixture')
                    ball((sx_, sy_, z + 1.74), (.05, .05, .05), 'lamp', f, 'fixture')
                    k.light((sx_, sy_, z + 1.7), 18, kind='lamp')
                    ctx['placed'].append(base)
                    furnishing('floor-lamp', room, base)
                    k.editable('floor-lamp', room, base, edit_mark)
                    break
        # A lounge chair at the side of the table, turned toward it.
        for su in (() if room.get('sofaPosition') else (1, -1)):
            spot = lpoly(sp, su * (h + .75) - .35, su * (h + .75) + .35, 1.55, 2.25)
            if ctx['inside'].covers(spot) and not hits(spot, ctx['placed']) and not hits(spot, keep):
                cx_, cy_ = P(sp, su * (h + .75), 1.9)
                face = -su * sp['t']
                edit_mark = k.edit_mark()
                chair(cx_, cy_, z, f, math.atan2(face[0], -face[1]))
                furnishing('lounge-chair', room, spot)
                k.editable('lounge-chair', room, spot, edit_mark)
                ctx['placed'].append(spot)
                break
        px, py = P(sp, 0, 1.9)
        lamp(px, py, z + H - .9, f, True)
        if room.get('seatingExtension'):
            for item in k.editables[seating_edit_start:]:
                item['placementArea']=[list(p) for p in clear.exterior.coords[:-1]]
                item['placementRoomIds']=[room['id'],room['seatingExtension']]
        return sp

    def dining_group(ctx, route=None, anchor=None, sizes=(1.8, 1.5, 1.2, 1.0), open_plan=False):
        """A table for six (four in a small room) with chairs, free-standing where a 0.8 m route stays open; centred
        in the room, or drawn toward `anchor` (the kitchen side of a combined living and dining room)."""
        room, f, clear = ctx['room'], ctx['floor'], ctx['clear']; z = f * H
        x0, y0, x1, y1 = clear.bounds
        serving = next((c for c in b.get('built_in_counters', []) if room['id'] in c['roomIds']), None)
        if serving and anchor is None:
            # Place a generous dining setting near the serving ledge while the
            # existing passage solver protects every door and the open half.
            ledge = metres(Polygon(serving['polygon'])).centroid
            centre = clear.centroid
            dx, dy = centre.x - ledge.x, centre.y - ledge.y
            length = max(.001, math.hypot(dx, dy))
            anchor = Point(ledge.x + dx / length * 1.8, ledge.y + dy / length * 1.8)
            sizes = (2.2, 1.8, 1.5, 1.2)
        zones = [q for q, o in ctx['doors'] if not ((open_plan or serving) and o['kind']=='cased' and o['width']>=2000)] + ctx['placed']
        def connected_passages(zone):
            # A wide, wall-free opening needs a route through it, rather than an
            # empty strip along its entire length. Reserve a continuous 800 mm path.
            free=clear.buffer(-.4).difference(unary_union([zone,*ctx['placed']]).buffer(.4,join_style=2))
            portals=[]
            for q,o in ctx['doors']:
                if 'wall_id' not in o:continue  # existing open-plan furniture keepout
                w=hosts[o['wall_id']];a=np.array(w['a'])/1000;end=np.array(w['b'])/1000
                u=(end-a)/np.linalg.norm(end-a);n=np.array([-u[1],u[0]])
                mid=a+u*(o['offset']+o['width']/2)/1000
                if clear.distance(Point(*(mid+n*.5)))>clear.distance(Point(*(mid-n*.5))):n=-n
                inset=min(.4,o['width']/2000-.01)
                portals.append(LineString([a+u*(o['offset']/1000+inset)+n*(w['thickness']/2000+.45),
                                           a+u*((o['offset']+o['width'])/1000-inset)+n*(w['thickness']/2000+.45)]))
            pieces=[free] if free.geom_type=='Polygon' else list(getattr(free,'geoms',[]))
            return any(all(piece.intersects(portal) for portal in portals) for piece in pieces)
        best = None
        for tw in sizes:
            for along_x in ((room['diningOrientation']==0,) if 'diningOrientation' in room else (True, False)):
                wx_, wy_ = (tw + .2, 2.0) if along_x else (2.0, tw + .2)
                for cx_ in np.arange(x0 + wx_ / 2 + .25, x1 - wx_ / 2 - .25 + 1e-6, .1):
                    for cy_ in np.arange(y0 + wy_ / 2 + .25, y1 - wy_ / 2 - .25 + 1e-6, .1):
                        zone = box(cx_ - wx_ / 2, cy_ - wy_ / 2, cx_ + wx_ / 2, cy_ + wy_ / 2)
                        # Compact authored dining may approach the open hall edge;
                        # actual furniture containment and connected paths still apply.
                        edge_margin=.05 if room.get('diningCounterGap',900)<900 else .25
                        if not ctx['inside'].covers(zone.buffer(edge_margin)) or hits(zone.buffer(.1), zones):
                            continue
                        if 'diningOrientation' in room and serving and zone.distance(metres(Polygon(serving['polygon'])))<room.get('diningCounterGap',900)/1000-1e-6:continue
                        if route and not free_path(ctx, zone, *route):
                            continue
                        if (open_plan or serving) and not connected_passages(zone):
                            continue
                        c = anchor or clear.centroid
                        score = (tw, -abs(cx_ - c.x) - abs(cy_ - c.y))
                        if best is None or score > best[0]:
                            best = (score, cx_, cy_, tw, along_x)
            if best:
                break
        if not best and custom and not open_plan and any(o['kind']=='cased' and o['width']>=2000 for _,o in ctx['doors']):
            return dining_group(ctx,route,anchor,sizes,open_plan=True)
        if not best:
            # A table for four against a wall: two chairs along the open side, one at each end.
            for cands in (spots(ctx, 2.3, .8, front=.6, height=.8, step=.05),):
                ok = [c for c in cands if not route or free_path(ctx, lpoly(c, -1.15, 1.15, 0, 1.4), *route)]
                if ok:
                    sp = min(ok, key=lambda c: -far_from_doors(ctx, c))
                    edit_mark = k.edit_mark()
                    lrb(sp, 0, .4, z + .75, (1.2, .8, .07), M['table'], f, r=.035)
                    for uu in (-.52, .52):
                        for vv in (.08, .72):
                            x, y = P(sp, uu, vv)
                            beam((x, y, z + .04), (x, y, z + .72), .038, M['table'], f, 'furniture')
                    for uu in (-.3, .3):
                        x, y = P(sp, uu, 1.07)
                        chair(x, y, z, f, lrot(sp))
                    for su in (-1, 1):
                        x, y = P(sp, su * .9, .4)
                        face = -su * sp['t']
                        chair(x, y, z, f, math.atan2(face[0], -face[1]))
                    zone = lpoly(sp, -1.15, 1.15, .02, 1.35)
                    ctx['placed'].append(zone)
                    furnishing('dining-set', room, zone)
                    k.editable('dining-set', room, zone, edit_mark)
                    x, y = P(sp, 0, .4)
                    lamp(x, y, z + 2.2, f, True)
                    return (x, y)
            return None
        _, tx, ty, tw, along_x = best
        td = .9
        size = (tw, td) if along_x else (td, tw)
        edit_mark = k.edit_mark()
        rb((tx, ty, z + .75), (size[0], size[1], .07), M['counter'] if serving else M['table'], f, r=.12 if serving else .035)
        if serving:
            # Two broad oak pedestals leave the upholstered chairs uncluttered.
            for a in (-tw * .27, tw * .27):
                xx, yy = (tx + a, ty) if along_x else (tx, ty + a)
                rb((xx, yy, z + .38), (.18, .55, .69) if along_x else (.55, .18, .69), M['table'], f, r=.04)
        else:
            for a in (-tw * .35, tw * .35):
                for bb2 in (-.26, .26):
                    xx, yy = (tx + a, ty + bb2) if along_x else (tx + bb2, ty + a)
                    beam((xx, yy, z + .04), (xx, yy, z + .72), .038, M['table'], f, 'furniture')
        seats = (-tw * .3, 0., tw * .3) if tw >= 1.8 else (-tw * .27, tw * .27)
        for a in seats:
            if along_x:
                chair(tx + a, ty - .67, z, f, math.pi); chair(tx + a, ty + .67, z, f, 0)
            else:
                chair(tx - .67, ty + a, z, f, math.pi / 2); chair(tx + .67, ty + a, z, f, -math.pi / 2)
        for a in seats:
            for bb2 in (-.22, .22):
                xx, yy = (tx + a, ty + bb2) if along_x else (tx + bb2, ty + a)
                cylinder((xx, yy, z + .798), .115, .013, 'ceramic', f, 'detail')
        zone = box(tx - (tw / 2 + .1 if along_x else .92), ty - (.92 if along_x else tw / 2 + .1), tx + (tw / 2 + .1 if along_x else .92), ty + (.92 if along_x else tw / 2 + .1))
        ctx['placed'].append(zone)
        furnishing('dining-set', room, zone)
        k.editable('dining-set', room, zone, edit_mark)
        if upgraded_interior:
            chandelier(tx, ty, f)
        else:
            lamp(tx, ty, z + 2.20, f, True)
        return (tx, ty)

    def public_route(room):
        """The mouth of the hall and the middle of the edge shared with the living room: the route through."""
        f = room['floor']
        me = Polygon(np.array(room['polygon']) / 1000)
        pts = []
        for s in b['spaces']:
            if s['floor'] == f and s['id'] != room['id'] and s['kind'] in ('hall', 'living', 'family'):
                e = Polygon(np.array(s['polygon']) / 1000).intersection(me.buffer(.01))
                if not e.is_empty and e.area > .002:
                    c = e.centroid
                    pts.append((c.x, c.y))
        return pts[:2] if len(pts) >= 2 else None


    def room_context(room):
        f = room['floor']
        clear = Polygon(np.array(room['clear']) / 1000)
        doors, windows = [], []
        for o in b['openings']:
            if o['floor'] != f or room['id'] not in o['connects']:
                continue
            w = hosts[o['wall_id']]
            a = np.array(w['a'], float) / 1000; bb = np.array(w['b'], float) / 1000
            u = (bb - a) / np.linalg.norm(bb - a); nrm = np.array([-u[1], u[0]])
            p0 = a + u * o['offset'] / 1000; p1 = p0 + u * o['width'] / 1000; m = (p0 + p1) / 2
            if clear.distance(Point(*(m + nrm * .5))) > clear.distance(Point(*(m - nrm * .5))):
                nrm = -nrm
            face = w['thickness'] / 2000
            q0 = p0 - u * .06 + nrm * face; q1 = p1 + u * .06 + nrm * face
            if o['kind'] == 'window':
                windows.append((Polygon([q0, q1, q1 + nrm * .5, q0 + nrm * .5]), o))
                continue
            # Open alcove edges are room zoning, not door approaches.
            if o.get('openSide') or o.get('servingCounter')=='full':continue
            # A passage 0.6 m deep in front of every opening, and the quarter circle a leaf sweeps into this room.
            zone = Polygon([q0, q1, q1 + nrm * .6, q0 + nrm * .6])
            if o['kind'] == 'door' and o.get('swing') == room['id']:
                hinge = (p0 if o.get('hinge', 'start') == 'start' else p1) + nrm * face
                along = u if o.get('hinge', 'start') == 'start' else -u
                r = o['width'] / 1000 + .05
                arc = [hinge] + [hinge + r * (along * math.cos(a) + nrm * math.sin(a)) for a in np.linspace(0, math.pi / 2, 9)]
                zone = zone.union(Polygon(arc).buffer(.02))
            doors.append((zone, o))
        return {'room': room, 'clear': clear, 'inside': prep(clear.buffer(.004)), 'doors': doors, 'windows': windows,
                'floor': f, 'placed': [metres(Polygon(c['polygon'])).intersection(clear) for c in b.get('built_in_counters',[]) if room['id'] in c['roomIds']]}

    def hits(poly, zones):
        return any(poly.intersects(q) and poly.intersection(q).area > 2e-4 for q in zones)

    def spots(ctx, width, depth, front=.6, height=1., step=.1, sides=0., tall=None, low_wall=False):
        """Placements of a width x depth piece backed by solid wall: [{'c', 't', 'n', 'foot', 's', 'L'}]. `c` is the
        wall-face point at the piece's centre, `t` runs along the wall and `n` into the room (a proper rotation)."""
        clear, f = ctx['clear'], ctx['floor']
        # Wall junctions leave collinear vertices on the clear outline; each straight wall is one run.
        pts = list(clear.simplify(1e-4, preserve_topology=True).exterior.coords)
        out = []
        placed = ctx['placed']
        door_zones = [q for q, _ in ctx['doors']]
        low_windows = [q for q, o in ctx['windows'] if o['sill'] / 1000 < height]
        for (ax, ay), (bx2, by2) in zip(pts, pts[1:]):
            L = math.hypot(bx2 - ax, by2 - ay)
            if L + 1e-6 < width:
                continue
            t = np.array([(bx2 - ax) / L, (by2 - ay) / L]); nrm = np.array([-t[1], t[0]])
            A = np.array([ax, ay], float)
            mid = A + t * L / 2
            flip = not clear.contains(Point(*(mid + nrm * .03)))
            if flip:
                nrm = -nrm
            positions = np.arange(width / 2, L - width / 2 + 1e-6, step)
            if not len(positions):
                positions = [L / 2]
            for s in positions:
                c = A + t * s
                tt = -t if flip else t
                e0 = c - tt * (width / 2 + sides); e1 = c + tt * (width / 2 + sides)
                foot = Polygon([c - tt * width / 2 + nrm * .003, c + tt * width / 2 + nrm * .003,
                                c + tt * width / 2 + nrm * depth, c - tt * width / 2 + nrm * depth])
                if not ctx['inside'].covers(foot):
                    continue
                if not all(solid[f].contains(Point(*(c + tt * q - nrm * .07))) for q in np.linspace(-width / 2 + .04, width / 2 - .04, 4)) and not (low_wall and wall_behind(f, c[0], c[1], nrm[0], nrm[1], width/2-.04, .10, height)):
                    continue
                upright = foot if tall is None else Polygon([c - tt * width / 2 + nrm * .003, c + tt * width / 2 + nrm * .003,
                                                             c + tt * width / 2 + nrm * tall, c - tt * width / 2 + nrm * tall])
                if hits(foot, door_zones) or hits(upright, low_windows) or hits(foot, placed):
                    continue
                if front > 0:
                    zone = Polygon([e0 + nrm * depth, e1 + nrm * depth, e1 + nrm * (depth + front), e0 + nrm * (depth + front)])
                    if not ctx['inside'].covers(zone) or hits(zone, placed):
                        continue
                out.append({'c': c, 't': tt, 'n': nrm, 'foot': foot, 's': s, 'L': L, 'A': A})
        return out

    def door_centres(ctx):
        return [np.array(q.centroid.coords[0]) for q, _ in ctx['doors']]

    def far_from_doors(ctx, sp):
        ds = [float(np.linalg.norm(sp['c'] + sp['n'] * .5 - d)) for d in door_centres(ctx)]
        return min(ds) if ds else 0.

    def P(sp, u, v):
        q = sp['c'] + sp['t'] * u + sp['n'] * v
        return float(q[0]), float(q[1])

    def lbox(sp, u0, u1, v0, v1, z0, z1, mat, f, role='furniture', owner=None):
        xs, ys = zip(*(P(sp, uu, vv) for uu in (u0, u1) for vv in (v0, v1)))
        rect((min(xs), min(ys), z0, max(xs), max(ys), z1), mat, f, role, owner=owner)

    def lpoly(sp, u0, u1, v0, v1):
        xs, ys = zip(*(P(sp, uu, vv) for uu in (u0, u1) for vv in (v0, v1)))
        return box(min(xs), min(ys), max(xs), max(ys))

    def lrot(sp):
        return math.atan2(sp['n'][1], sp['n'][0]) - math.pi / 2

    def lrb(sp, u, v, zc, size, mat, f, role='furniture', r=.04, owner=None, extra=0.):
        x, y = P(sp, u, v)
        rb((x, y, zc), size, mat, f, role, r, lrot(sp) + extra, owner=owner)

    def wall_art(ctx, width=.9, height=.7, zc=1.55):
        """A framed print on the widest solid wall stretch not already used, above any furniture."""
        f = ctx['floor']; z = f * H
        serving_hosts=[hosts[o['wall_id']] for o in b['openings'] if o.get('servingCounter')=='full' and ctx['room']['id'] in o['connects']]
        art_ctx={**ctx,'doors':[],'placed':[]} if serving_hosts else ctx
        cands = spots(art_ctx, width + .3, .03, front=0, height=zc + height / 2 + .1, step=.05 if serving_hosts else .2)
        if serving_hosts:
            cands = [s for s in cands if wall_behind(f, *s['c'], s['n'][0], s['n'][1], width / 2 + .02, zc - height / 2, zc + height / 2)]
        if not cands:
            return
        preferred=[s for s in cands if any(LineString(np.array([w['a'],w['b']])/1000).distance(Point(*s['c']))<.1 for w in serving_hosts)]
        sp = max(preferred or cands, key=lambda s: (-abs(s['s'] - s['L'] / 2), s['L']))
        lbox(sp, -width / 2, width / 2, .004, .035, z + zc - height / 2, z + zc + height / 2, 'frame', f, 'art')
        lbox(sp, -width / 2 + .04, width / 2 - .04, .035, .042, z + zc - height / 2 + .04, z + zc + height / 2 - .04, 'art', f, 'art')

    def wardrobe(ctx, lengths=(2.4, 2.1, 1.8, 1.5, 1.2, .9), name='wardrobe', prefer_door=True):
        room, f = ctx['room'], ctx['floor']; z = f * H
        for ww in lengths:
            cands = spots(ctx, ww, .6, front=.75, height=2.3) or spots(ctx, ww, .6, front=.6, height=2.3)
            if cands:
                sp = min(cands, key=lambda s: (far_from_doors(ctx, s) if prefer_door else -far_from_doors(ctx, s), abs(s['s'] - s['L'] / 2)))
                break
        else:
            return None
        edit_mark = k.edit_mark()
        # Frame, top, three or four leaves with bar handles, on a recessed plinth.
        for u0, u1, v0, v1 in ((-ww / 2, -ww / 2 + .035, 0, .6), (ww / 2 - .035, ww / 2, 0, .6), (-ww / 2, ww / 2, 0, .035)):
            lbox(sp, u0, u1, v0, v1, z + .08, z + 2.25, M['casework'], f)
        lbox(sp, -ww / 2, ww / 2, 0, .6, z + 2.22, z + 2.26, M['casework'], f)
        leaves = 4 if ww >= 2.0 else 3 if ww >= 1.4 else 2
        for j in range(leaves):
            a0 = -ww / 2 + j * ww / leaves + .012; a1 = a0 + ww / leaves - .024
            lbox(sp, a0, a1, .565, .6, z + .12, z + 2.21, M['casework'], f)
            hu = a1 - .06 if j % 2 == 0 else a0 + .06
            x, y = P(sp, hu, .62)
            beam((x, y, z + .9), (x, y, z + 1.2), .008, 'frame' if upgraded_interior else 'brass', f, 'furniture')
        foot = lpoly(sp, -ww / 2, ww / 2, 0, .6)
        ctx['placed'].append(foot)
        furnishing(name, room, foot)
        k.editable(name, room, foot, edit_mark)
        return sp

    def dresser(ctx):
        room, f = ctx['room'], ctx['floor']; z = f * H
        for dw_ in (1.2, .9, .75):
            cands = spots(ctx, dw_, .48, front=.6, height=.85, step=.05)
            if cands:
                sp = min(cands, key=lambda s: abs(s['s'] - s['L'] / 2))
                edit_mark = k.edit_mark()
                lbox(sp, -dw_ / 2, dw_ / 2, .02, .48, z + .08, z + .82, M['casework'], f)
                for j in range(3):
                    lbox(sp, -dw_ / 2 + .03, dw_ / 2 - .03, .48, .5, z + .12 + j * .23, z + .31 + j * .23, M['casework'], f)
                    a_, b_ = P(sp, -.12, .52), P(sp, .12, .52)
                    beam((a_[0], a_[1], z + .22 + j * .23), (b_[0], b_[1], z + .22 + j * .23), .007, 'frame' if upgraded_interior else 'brass', f, 'detail')
                foot = lpoly(sp, -dw_ / 2, dw_ / 2, .02, .5)
                ctx['placed'].append(foot)
                furnishing('wardrobe', room, foot)
                k.editable('wardrobe', room, foot, edit_mark)
                return sp
        return None

    def bed_set(ctx, master):
        room, f, clear = ctx['room'], ctx['floor'], ctx['clear']; z = f * H
        area = clear.area
        bw = 1.8 if (master and area > 15) else 1.6 if area > 10.5 else 1.5
        bl = 2.05
        head = 1.25
        good = []
        options=((.0,1.0,1.3),(.0,1.0,.8)) if room.get('bedType')=='single' else ((.52, bw, 1.3), (.0, bw, 1.3), (.0, min(bw, 1.35), 1.3), (.0, min(bw, 1.5), .8), (.0, 1.35, .8))
        for tables, bw_, height in options:
            bw = bw_
            if height < 1:
                head = .72              # a low headboard below the window sill
            cands = spots(ctx, bw + 2 * tables + .1, bl + .15, front=.55, height=height, tall=.25)
            # Walking room on at least one long side of the bed.
            good = []
            for sp in cands:
                side = [lpoly(sp, -bw / 2 - tables - .55, -bw / 2 - tables, .3, bl), lpoly(sp, bw / 2 + tables, bw / 2 + tables + .55, .3, bl)]
                if any(ctx['inside'].covers(q) and not hits(q, ctx['placed']) for q in side):
                    good.append(sp)
            if good:
                break
        if not good:
            return None
        # The command position: the headboard on the wall farthest from the door, centred on it.
        sp = max(good, key=lambda s: (round(far_from_doors(ctx, s), 1), -abs(s['s'] - s['L'] / 2)))
        edit_mark = k.edit_mark()
        v0 = .1
        lbox(sp, -bw / 2, bw / 2, v0, v0 + bl, z + .07, z + .28, M['bedframe'], f, owner=room['id'])
        lrb(sp, 0, v0 + bl / 2, z + .39, (bw + .04, bl + .03, .25), 'linen', f, r=.075, owner=room['id'])
        lrb(sp, 0, v0 - .03, z + head / 2 + .075, (bw + .35, .12, head), 'fabric-dark', f, r=.05)
        if upgraded_interior and head > 1 and wall_behind(f, *P(sp, 0, 0), sp['n'][0], sp['n'][1], 1.45, .05, 2.55):
            for uu in np.arange(-1.42, 1.42, .085):
                lbox(sp, uu, uu + .06, .003, .028, z + .1, z + 2.55, M['casework'], f, 'wall-panel')
        for pu in ((0,) if bw<1.2 else (-bw / 4, bw / 4)):
            lrb(sp, pu, v0 + .38, z + .58, (bw-.2 if bw<1.2 else bw / 2 - .12, .42, .17), 'linen', f, r=.07, extra=.035)
        vv, ff = [], []
        nx, ny = 22, 24
        for j in range(ny):
            for i in range(nx):
                uu = -bw / 2 - .055 + (bw + .11) * i / (nx - 1); wv = v0 + .68 + (bl - .58) * j / (ny - 1)
                zz = z + .54 + .014 * math.cos(i * .9 + j * .25) + .007 * math.sin(i * 1.8)
                if i in (0, nx - 1):
                    zz -= .13
                x, y = P(sp, uu, wv)
                vv.append((x, y, zz))
        for j in range(ny - 1):
            for i in range(nx - 1):
                q = j * nx + i
                ff += [[q, q + 1, q + nx + 1], [q, q + nx + 1, q + nx]]
        node(asset(trimesh.Trimesh(vertices=vv, faces=ff, process=False), smooth=True), 'fabric', floor=f, role='furniture')
        if tables:
            for su in (-1, 1):
                tu = su * (bw / 2 + .30)
                lrb(sp, tu, .25, z + .31, (.43, .45, .48), M['casework'], f, r=.014)
                x, y = P(sp, tu, .25)
                lamp(x, y, z + .56, f)
        foot = lpoly(sp, -bw / 2 - tables, bw / 2 + tables, .02, v0 + bl + .04)
        ctx['placed'].append(foot)
        furnishing('bed', room, lpoly(sp, -bw / 2 - .05, bw / 2 + .05, .02, v0 + bl + .04))
        k.editable('bed', room, foot, edit_mark)
        rug = lpoly(sp, -bw / 2 - .32, bw / 2 + .32, v0 + .65, v0 + bl + .45).intersection(clear.buffer(-.12))
        if not rug.is_empty and rug.geom_type == 'Polygon':
            x0r, y0r, x1r, y1r = rug.bounds
            rect((x0r, y0r, z + .012, x1r, y1r, z + .018), 'rug', f, 'rug')
        return sp

    def bath_set(ctx):
        """WC, basin and shower, planned together: a glass-screened tray at the far end from the door when the room
        allows it, otherwise a walk-in wet area with a floor drain; the WC and a basin with its lit mirror always."""
        room, f, clear = ctx['room'], ctx['floor'], ctx['clear']; z = f * H
        if upgraded_interior:
            lining(room, f, z + .009, z + 1.55, 'tilewall', 'wall-tile', .01)
        x0, y0, x1, y1 = clear.bounds
        sw = min(1.2, max(.8, min(x1 - x0, y1 - y0) - .05))
        sd = .9 if clear.area >= 2.6 else .8
        base = list(ctx['placed'])

        def pick_shower():
            showers = spots(ctx, sw, sd, front=0, height=1.0, step=.05)
            if room['kind']=='powder-room' or not showers or clear.area < 2.0:
                return None
            sp = max(showers, key=lambda s: (round(far_from_doors(ctx, s), 1), -min(s['s'], s['L'] - s['s'])))
            ctx['placed'].append(lpoly(sp, -sw / 2, sw / 2, 0, sd))
            return sp

        def pick_wc():
            cands = spots(ctx, .8, .72, front=.55, height=.8, step=.05) or spots(ctx, .7, .7, front=.5, height=.8, step=.05)
            if not cands:
                return None
            sp = max(cands, key=lambda s: (round(far_from_doors(ctx, s), 1) * .5, -abs(s['s'] - s['L'] / 2)))
            ctx['placed'].append(lpoly(sp, -.35, .35, .02, .74))
            return sp

        def pick_basin():
            for vw in (1.0, .8, .65, .5):
                cands = spots(ctx, vw, .52 if vw > .5 else .42, front=.6 if vw > .5 else .5, height=.85, step=.05)
                if cands:
                    sp = min(cands, key=lambda s: (round(far_from_doors(ctx, s), 1), abs(s['s'] - s['L'] / 2)))
                    ctx['placed'].append(lpoly(sp, -vw / 2, vw / 2, .02, .52 if vw > .5 else .42))
                    return sp, vw
            return None, 0
        shower = pick_shower(); wc = pick_wc(); basin, vw = pick_basin()
        if wc is None or basin is None:
            # A small bath: the WC and basin come first, the shower becomes a walk-in wet area.
            ctx['placed'][:] = base
            wc = pick_wc(); basin, vw = pick_basin(); shower = pick_shower()
        wet = None
        if shower is None and room['kind']!='powder-room':
            heads = spots(ctx, .6, .05, front=.6, height=1.0, step=.05)
            if heads:
                wet = max(heads, key=lambda s: round(far_from_doors(ctx, s), 1))
        if shower is not None:
            tray = lpoly(shower, -sw / 2, sw / 2, 0, sd)
            tx0, ty0, tx1, ty1 = tray.bounds
            rect((tx0 + .01, ty0 + .01, z + .009, tx1 - .01, ty1 - .01, z + .02), 'wetfloor', f, 'detail')
            if upgraded_interior:
                # Frameless glass along the open side of the tray, a black rain head and a linear drain.
                edge = [(shower['c'] + shower['t'] * (-sw / 2) + shower['n'] * sd), (shower['c'] + shower['t'] * (sw / 2) + shower['n'] * sd)]
                gx0, gy0 = np.minimum(*edge); gx1, gy1 = np.maximum(*edge)
                rect((gx0 - .004, gy0 - .004, z + .02, gx1 + .004, gy1 + .004, z + 2.0), 'glass', f, 'glass')
                lbox(shower, -sw / 2 + .12, sw / 2 - .12, sd - .12, sd - .08, z + .02, z + .024, 'appliance', f, 'detail')
            head = shower
        else:
            head = wet
        if head is not None:
            hx, hy = P(head, 0, .3)
            bx_, by_ = P(head, 0, .02)
            beam((bx_, by_, z + 2.15), (hx, hy, z + 2.15), .01, 'frame' if upgraded_interior else 'brass', f, 'detail')
            cylinder((hx, hy, z + 2.13), .11, .012, 'frame' if upgraded_interior else 'brass', f, 'detail')
            mx, my = P(head, 0, .03)
            cylinder((mx, my, z + 1.1), .045, .03, 'frame' if upgraded_interior else 'brass', f, 'detail', rot=(math.pi / 2, 0, lrot(head)))
            if shower is None:
                dx, dy = P(head, 0, .45)
                cylinder((dx, dy, z + .011), .06, .004, 'appliance', f, 'detail')
        if wc is not None:
            bx_, by_ = P(wc, 0, .44)
            ball((bx_, by_, z + .22), (.20, .29, .22), 'ceramic', f, 'furniture', (0, 0, lrot(wc)))
            torus = trimesh.creation.torus(major_radius=.17, minor_radius=.03, major_sections=24, minor_sections=8)
            sx_, sy_ = P(wc, 0, .40)
            node(asset(torus, smooth=True), 'ceramic', (sx_, sy_, z + .44), (.95, 1.45, 1), (0, 0, lrot(wc)), floor=f, role='detail')
            lrb(wc, 0, .1, z + .55, (.39, .18, .62), 'ceramic', f, r=.05)
            furnishing('wc', room, lpoly(wc, -.23, .23, .02, .74))
        if basin is not None:
            vd = .5 if vw > .5 else .4
            lbox(basin, -vw / 2, vw / 2, .02, vd, z + .20, z + .77, 'walnut' if upgraded_interior else 'timber', f)
            lrb(basin, 0, vd / 2 + .01, z + .79, (vw + .02, vd, .045), M['counter'], f, r=.02)
            bowl = trimesh.creation.revolve(np.array([[.035, 0], [.18, .03], [.245, .115], [.24, .15], [.22, .16], [.215, .13], [.17, .065], [.035, .028]]), sections=32)
            bx_, by_ = P(basin, 0, vd / 2 + .02)
            node(asset(bowl, smooth=True), 'ceramic', (bx_, by_, z + .812), (.85 if vw <= .5 else 1, .85 if vw <= .5 else 1, 1), floor=f, role='detail')
            t0, t1 = P(basin, 0, .06), P(basin, 0, .17)
            beam((t0[0], t0[1], z + .82), (t0[0], t0[1], z + 1.12), .012, 'frame' if upgraded_interior else 'brass', f, 'detail')
            beam((t0[0], t0[1], z + 1.12), (t1[0], t1[1], z + 1.12), .012, 'frame' if upgraded_interior else 'brass', f, 'detail')
            half = min(.31, vw / 2 - .03)
            if wall_behind(f, *P(basin, 0, 0), basin['n'][0], basin['n'][1], half, 1.05, 1.85):
                lbox(basin, -half, half, .009, .025, z + 1.08, z + 1.82, 'mirror' if upgraded_interior else 'glass', f, 'mirror')
                if upgraded_interior:
                    lbox(basin, -half - .02, half + .02, .012, .03, z + 1.84, z + 1.86, 'lamp', f, 'fixture')
                    mx, my = P(basin, 0, .3)
                    k.light((mx, my, z + 1.9), 8, kind='mirror')
            furnishing('vanity', room, lpoly(basin, -vw / 2, vw / 2, .02, vd + .02))
        if upgraded_interior:
            rails = spots(ctx, .6, .08, front=0, height=1.6, step=.1)
            if rails:
                sp = rails[len(rails) // 2]
                a_, b_ = P(sp, -.28, .06), P(sp, .28, .06)
                beam((a_[0], a_[1], z + 1.25), (b_[0], b_[1], z + 1.25), .01, 'frame', f, 'detail')

    def desk_set(ctx):
        room, f, clear = ctx['room'], ctx['floor'], ctx['clear']; z = f * H
        for tw in (1.6, 1.4, 1.2):
            desks = spots(ctx, tw, .6, front=.8, height=.8, step=.1)
            if desks:
                break
        else:
            return
        # Under a window if one has a sill above the desk, else the widest wall.
        def lit(s):
            return any(o['sill'] / 1000 >= .8 and q.intersects(lpoly(s, -tw / 2, tw / 2, 0, .8)) for q, o in ctx['windows'])
        sp = max(desks, key=lambda s: (lit(s), -abs(s['s'] - s['L'] / 2)))
        edit_mark = k.edit_mark()
        lbox(sp, -tw / 2, tw / 2, .02, .6, z + .72, z + .77, M['table'], f)
        for su in (-1, 1):
            lbox(sp, su * (tw / 2 - .07) - .03, su * (tw / 2 - .07) + .03, .08, .52, z, z + .72, 'frame', f)
        cx_, cy_ = P(sp, 0, .98)
        chair(cx_, cy_, z, f, lrot(sp))
        lbox(sp, -.2, .2, .12, .135, z + .79, z + 1.10, 'blackglass' if upgraded_interior else 'frame', f, 'detail')
        lx, ly = P(sp, tw / 2 - .15, .3)
        lamp(lx, ly, z + .77, f)
        foot = lpoly(sp, -tw / 2, tw / 2, .02, 1.25)
        ctx['placed'].append(foot)
        furnishing('desk', room, foot)
        k.editable('desk', room, foot, edit_mark)
        # A bookcase on another wall.
        cases = spots(ctx, 1.2, .35, front=.7, height=2.0, step=.1)
        if cases:
            bk = max(cases, key=lambda s: -abs(s['s'] - s['L'] / 2))
            edit_mark = k.edit_mark()
            for u0, u1 in ((-.6, -.575), (.575, .6)):
                lbox(bk, u0, u1, 0, .35, z, z + 2.0, M['casework'], f)
            for zz in (.02, .42, .82, 1.22, 1.62, 1.97):
                lbox(bk, -.6, .6, 0, .35, z + zz, z + zz + .03, M['casework'], f)
            for j, uu in enumerate(np.arange(-.52, .5, .09)):
                if j % 4 == 3:
                    continue
                for zz in (.05, .85):
                    lbox(bk, uu, uu + .06, .06, .3, z + zz, z + zz + .24 + .04 * (j % 3), ('linen', 'fabric', 'rug')[j % 3], f, 'detail')
            foot = lpoly(bk, -.6, .6, 0, .35)
            ctx['placed'].append(foot)
            furnishing('bookcase', room, foot)
            k.editable('bookcase', room, foot, edit_mark)
        if clear.area > 9:
            corners = spots(ctx, .5, .5, front=0, height=1.2, step=.2)
            if corners:
                sp = max(corners, key=lambda s: min(s['s'], s['L'] - s['s']) * -1)
                px, py = P(sp, 0, .3)
                k.plant(px, py, z, 'monstera', height=.9, f=f, pot=(.18, .34, 'planter' if upgraded_interior else 'ceramic'))

    def utility_set(ctx):
        room, f = ctx['room'], ctx['floor']; z = f * H
        for run in (1.9, 1.5, 1.2, .7):
            runs = spots(ctx, run, .62, front=.7, height=.9, step=.1)
            if runs:
                break
        else:
            return
        sp = max(runs, key=lambda s: -abs(s['s'] - s['L'] / 2))
        edit_mark = k.edit_mark()
        # Front-loading washer, a steel wash sink on a counter, and a drying rack above.
        lrb(sp, -run / 2 + .33, .31, z + .44, (.6, .6, .86), 'ceramic', f, r=.03)
        ring = trimesh.creation.torus(major_radius=.2, minor_radius=.035, major_sections=24, minor_sections=8)
        rx, ry = P(sp, -run / 2 + .33, .62)
        node(asset(ring, smooth=True), 'frame', (rx, ry, z + .45), rot=(math.pi / 2, 0, lrot(sp)), floor=f, role='detail')
        if run >= 1.2:
            lbox(sp, -run / 2 + .66, run / 2, .02, .6, z + .1, z + .86, M['casework'], f)
            lbox(sp, -run / 2 + .66, run / 2, 0, .62, z + .86, z + .9, M['counter'], f)
            sx_, sy_ = P(sp, (run / 2 - .66 + -run / 2 + .66) / 2 + .25, .3)
            rect((sx_ - .22, sy_ - .18, z + .78, sx_ + .22, sy_ + .18, z + .905), 'steel', f, 'detail')
        for dz in (1.95,):
            a_, b_ = P(sp, -run / 2 + .1, .35), P(sp, run / 2 - .1, .35)
            beam((a_[0], a_[1], z + dz), (b_[0], b_[1], z + dz), .012, 'frame', f, 'detail')
        foot = lpoly(sp, -run / 2, run / 2, .02, .62)
        ctx['placed'].append(foot)
        furnishing('laundry', room, foot)
        k.editable('laundry', room, foot, edit_mark)

    def dress_set(ctx):
        room, f = ctx['room'], ctx['floor']; z = f * H
        first = wardrobe(ctx, (2.7, 2.4, 2.1, 1.8, 1.5, 1.2), 'wardrobe', prefer_door=False)
        if first is None:
            return
        second = wardrobe(ctx, (2.4, 2.1, 1.8, 1.5, 1.2, .9), 'wardrobe-2', prefer_door=False)
        # A full-length mirror on a free wall.
        mirrors = spots(ctx, .6, .03, front=.8, height=1.95, step=.1)
        if mirrors:
            sp = mirrors[len(mirrors) // 2]
            lbox(sp, -.3, .3, .004, .02, z + .15, z + 1.95, 'mirror' if upgraded_interior else 'glass', f, 'mirror')

    def pooja_set(ctx):
        """A mandir: a teak cabinet with a marble altar shelf, a carved back panel lit from behind, brass lamps
        and a bell, on the wall facing the door."""
        room, f = ctx['room'], ctx['floor']; z = f * H
        for mw in ((1.4,1.2,1.0,.8,.6) if room.get('altarWall') else (1.2,1.0,.8,.6)):
            cands = spots(ctx, mw, .45, front=.7, height=2.1, step=.05)
            if room.get('altarWall'):
                normal={'front':(0,1),'rear':(0,-1),'left':(1,0),'right':(-1,0)}[room['altarWall']]
                cands=[s for s in cands if np.allclose(s['n'],normal)]
            if cands:
                break
        else:
            return
        sp = max(cands, key=lambda s: (round(far_from_doors(ctx, s), 1), -abs(s['s'] - s['L'] / 2)))
        edit_mark = k.edit_mark()
        lbox(sp, -mw / 2, mw / 2, .02, .45, z, z + .75, 'walnut', f)
        lbox(sp, -mw / 2 - .01, mw / 2 + .01, 0, .47, z + .75, z + .8, 'stone', f)
        for su in (-1, 1):
            lbox(sp, su * mw / 2 - .04 * (su > 0), su * mw / 2 + .04 * (su < 0), .02, .4, z + .8, z + 1.95, 'walnut', f)
        lbox(sp, -mw / 2, mw / 2, .02, .45, z + 1.95, z + 2.05, 'walnut', f)
        lbox(sp, -mw / 2 + .06, mw / 2 - .06, .01, .03, z + .82, z + 1.9, 'lamp', f, 'fixture')
        for uu in np.arange(-mw / 2 + .1, mw / 2 - .08, .09):
            lbox(sp, uu, uu + .018, .03, .045, z + .84, z + 1.88, 'walnut', f, 'detail')
        mx, my = P(sp, 0, .25)
        k.light((mx, my, z + 1.5), 10, kind='lamp')
        for uu in (-.25 * mw, .25 * mw):
            x, y = P(sp, uu, .3)
            cylinder((x, y, z + .82), .045, .06, 'brass', f, 'detail')
            ball((x, y, z + .9), (.018, .018, .03), 'lamp', f, 'detail')
        bx_, by_ = P(sp, 0, .36)
        cylinder((bx_, by_, z + 1.5), .06, .09, 'brass', f, 'detail')
        beam((bx_, by_, z + 1.59), (bx_, by_, z + 1.95), .004, 'brass', f, 'detail')
        foot = lpoly(sp, -mw / 2, mw / 2, .02, .47)
        ctx['placed'].append(foot)
        furnishing('mandir', room, foot)
        k.editable('mandir', room, foot, edit_mark)
        fx_, fy_ = P(sp, 0, .95)
        rect((fx_ - .35, fy_ - .25, z + .012, fx_ + .35, fy_ + .25, z + .018), 'rug', f, 'rug')

    def store_set(ctx):
        room, f = ctx['room'], ctx['floor']; z = f * H
        for i in range(2):
            for sw_, top in ((2.4, 2.2), (1.8, 2.2), (1.2, 2.2), (.9, 2.2), (1.8, 1.7), (1.2, 1.7), (.9, 1.7)):
                cands = spots(ctx, sw_, .45, front=.5, height=top, step=.1)
                if cands:
                    sp = max(cands, key=lambda s: s['L'])
                    edit_mark = k.edit_mark()
                    for zz in [q for q in (.05, .5, .95, 1.4, 1.85) if q < top - .1]:
                        lbox(sp, -sw_ / 2, sw_ / 2, 0, .45, z + zz, z + zz + .025, 'steel' if not upgraded_interior else M['casework'], f)
                    for su in (-1, 1):
                        lbox(sp, su * sw_ / 2 - .03 * (su > 0), su * sw_ / 2 + .03 * (su < 0), 0, .45, z, z + top - .3, 'frame', f)
                    for j, uu in enumerate(np.arange(-sw_ / 2 + .1, sw_ / 2 - .2, .32)):
                        lbox(sp, uu, uu + .26, .06, .38, z + .52 + .45 * (j % 3), z + .52 + .45 * (j % 3) + .24, ('linen', 'fabric', 'ceramic')[j % 3], f, 'detail')
                    foot = lpoly(sp, -sw_ / 2, sw_ / 2, 0, .45)
                    ctx['placed'].append(foot)
                    furnishing(f'shelves-{i}', room, foot)
                    k.editable(f'shelves-{i}', room, foot, edit_mark)
                    break

    def kitchen_set(ctx):
        """The longest solid wall takes the counter (a window above the worktop is welcome); sink under the window,
        hob clear of it, tall fridge at the end, wall cabinets and a lit backsplash where the wall is blank, and an
        island in a large kitchen."""
        room, f, clear = ctx['room'], ctx['floor'], ctx['clear']; z = f * H
        x0, y0, x1, y1 = clear.bounds
        found = None
        for run in np.arange(round(min(4.5, max(x1 - x0, y1 - y0) - .08), 1), 1.49, -.3):
            cands = spots(ctx, run + .08, .66, front=.95, height=.92, step=.05)
            if cands:
                found = (float(run), max(cands, key=lambda s: (-abs(s['s'] - s['L'] / 2), s['L'])))
                break
        if not found:
            return
        run, sp = found
        fridge = upgraded_interior and run > 2.7
        base_run = run - .78 if fridge else run
        u0 = -run / 2
        nseg = max(2, int(base_run / .6))
        for j in range(nseg):
            a0 = u0 + j * base_run / nseg; ww = base_run / nseg
            lbox(sp, a0, a0 + ww - .02, 0, .6, z + .10, z + .83, M['casework'], f)
            for zz in (.30, .59):
                lbox(sp, a0 + .02, a0 + ww - .035, .6, .622, z + zz, z + zz + .20, M['fronts'], f)
                h0, h1 = P(sp, a0 + .14, .64), P(sp, a0 + ww - .14, .64)
                beam((h0[0], h0[1], z + zz + .15), (h1[0], h1[1], z + zz + .15), .007, 'frame', f, 'detail')
        lbox(sp, u0 - .03, u0 + base_run + .03, 0, .66, z + .83, z + .87, M['counter'], f)
        if fridge:
            f0 = u0 + base_run + .02
            lbox(sp, f0, f0 + .72, 0, .65, z + .02, z + 1.95, 'appliance', f)
            h0 = P(sp, f0 + .06, .68)
            beam((h0[0], h0[1], z + 1.0), (h0[0], h0[1], z + 1.6), .01, 'frame', f, 'detail')
        su = u0 + base_run * .7
        for q, o in ctx['windows']:
            if o['sill'] / 1000 >= .9:
                wc = np.array(q.centroid.coords[0]) - sp['c']
                cu = float(np.dot(wc, sp['t']))
                if u0 + .45 <= cu <= u0 + base_run - .45 and float(np.dot(wc, sp['n'])) < 1.0:
                    su = cu
        basin = trimesh.creation.revolve(np.array([[.07, 0], [.20, .04], [.25, .11], [.25, .14], [.23, .15], [.22, .12], [.18, .06], [.07, .025]]), sections=32)
        bx_, by_ = P(sp, su, .32)
        node(asset(basin, smooth=True), 'appliance' if upgraded_interior else 'frame', (bx_, by_, z + .865), floor=f, role='detail')
        t0, t1 = P(sp, su, .1), P(sp, su, .28)
        beam((t0[0], t0[1], z + .88), (t0[0], t0[1], z + 1.17), .012, 'brass', f, 'detail')
        beam((t0[0], t0[1], z + 1.17), (t1[0], t1[1], z + 1.17), .012, 'brass', f, 'detail')
        hu = u0 + .5 if su - (u0 + .5) >= .9 else u0 + base_run - .5
        if upgraded_interior:
            lbox(sp, hu - .3, hu + .3, .08, .56, z + .87, z + .877, 'blackglass', f, 'detail')
        for du in (-.15, .14):
            for dv in (.18, .42):
                x, y = P(sp, hu + du, dv)
                cylinder((x, y, z + .88), .095, .016, 'frame', f, 'detail')
        wx, wy = P(sp, u0 + base_run / 2, 0)
        if upgraded_interior and wall_behind(f, wx, wy, sp['n'][0], sp['n'][1], base_run / 2 - .05, .9, 2.3):
            lbox(sp, u0, u0 + base_run, .002, .014, z + .87, z + 1.5, 'tilewall', f, 'wall-tile')
            for j in range(nseg):
                a0 = u0 + j * base_run / nseg; ww = base_run / nseg
                lbox(sp, a0, a0 + ww - .015, .015, .37, z + 1.52, z + 2.28, M['fronts'], f)
            lbox(sp, u0, u0 + base_run, .015, .34, z + 1.505, z + 1.515, 'lamp', f, 'fixture')
            lx, ly = P(sp, u0 + base_run / 2, .3)
            k.light((lx, ly, z + 1.4), 12, kind='undercabinet')
        else:
            lbox(sp, hu - .38, hu + .38, .08, .5, z + 1.6, z + 1.7, 'appliance' if upgraded_interior else 'frame', f, 'detail')
        foot = lpoly(sp, u0 - .03, u0 + run + .03, .005, .66)
        ctx['placed'].append(foot)
        furnishing('kitchen-run', room, foot)
        if custom and clear.area >= 12 and (room.get('prepStorageWall') or any(room['id'] in c['roomIds'] for c in b.get('built_in_counters', []))):
            # A second modular prep/storage run complements the serving ledge.
            # Reuse collision-aware wall placement so pantry/wash doors stay clear.
            candidates=[]
            for prep_width in (2.2,1.8,1.4,1.1):
                candidates=spots(ctx,prep_width+.08,.66,front=.95,height=.92,step=.1,low_wall=True)
                if room.get('prepStorageWall'):
                    normal={'front':(0,1),'rear':(0,-1),'left':(1,0),'right':(-1,0)}[room['prepStorageWall']]
                    candidates=[c for c in candidates if np.allclose(c['n'],normal)]
                if candidates:break
            if not candidates and not room.get('prepStorageWall'):
                # At a relocated serving ledge, tuck base cabinets beneath its kitchen side.
                # Keep the working aisle and the open half of the portal unobstructed.
                for counter in b.get('built_in_counters',[]):
                    if room['id'] not in counter['roomIds']:continue
                    cp=metres(Polygon(counter['polygon']));ax,ay,bx,by=cp.bounds
                    horizontal=bx-ax>by-ay
                    for sign in (-1,1):
                        c=np.array([(ax+bx)/2,ay if sign<0 else by]) if horizontal else np.array([ax if sign<0 else bx,(ay+by)/2])
                        tt=np.array([1.,0.]) if horizontal else np.array([0.,1.])
                        nn=np.array([0.,float(sign)]) if horizontal else np.array([float(sign),0.])
                        width=(bx-ax if horizontal else by-ay)-.08
                        candidate={'c':c,'t':tt,'n':nn,'s':0.,'L':width}
                        zone=lpoly(candidate,-width/2,width/2,.01,.66)
                        aisle=lpoly(candidate,-width/2,width/2,.01,1.61)
                        if width>=1.1 and ctx['inside'].covers(aisle) and not hits(aisle,[q for q,op in ctx['doors'] if op['id']!=counter['openingId']]) and not hits(zone,ctx['placed']):
                            candidates=[candidate];prep_width=width;break
                    if candidates:break
            if candidates:
                prep = max(candidates, key=lambda q: np.linalg.norm(q['c'] - sp['c']))
                segments=max(2,round(prep_width/.55));module=prep_width/segments
                for j in range(segments):
                    a = -prep_width/2 + j * module
                    lbox(prep, a, a + module-.02, 0, .60, z + .10, z + .83, M['casework'], f)
                    for zz in (.30, .59):
                        lbox(prep, a + .02, a + module-.04, .60, .622, z + zz, z + zz + .20, M['fronts'], f)
                        h0, h1 = P(prep, a + .14, .64), P(prep, a + module-.11, .64)
                        beam((h0[0], h0[1], z + zz + .15), (h1[0], h1[1], z + zz + .15), .007, 'frame', f, 'detail')
                lbox(prep, -prep_width/2-.03, prep_width/2+.03, 0, .66, z + .83, z + .87, M['counter'], f)
                prep_foot = lpoly(prep, -prep_width/2-.03, prep_width/2+.03, .005, .66)
                ctx['placed'].append(prep_foot)
                furnishing('kitchen-prep-run', room, prep_foot)
                if room.get('prepStorageWall') and wall_behind(f,*P(prep,0,0),prep['n'][0],prep['n'][1],prep_width/2,.9,2.3):
                    lbox(prep,-prep_width/2,prep_width/2,.002,.014,z+.87,z+1.5,'tilewall',f,'wall-tile')
                    for j in range(segments):
                        a=-prep_width/2+j*module
                        lbox(prep,a,a+module-.02,.015,.35,z+1.52,z+2.28,M['casework'],f)
                        lbox(prep,a+.012,a+module-.032,.35,.373,z+1.535,z+2.265,M['fronts'],f)
                        h0,h1=P(prep,a+module-.09,.386),P(prep,a+module-.09,.386)
                        beam((h0[0],h0[1],z+1.59),(h1[0],h1[1],z+1.80),.007,'frame',f,'detail')
                    lbox(prep,-prep_width/2,prep_width/2,.02,.32,z+1.505,z+1.515,'lamp',f,'fixture')
                    lx,ly=P(prep,0,.32);k.light((lx,ly,z+1.43),12,kind='undercabinet')
                    furnishing('kitchen-upper-storage',room,lpoly(prep,-prep_width/2,prep_width/2,.015,.386))
        # An island parallel to the run with a 1.05 m aisle, in a kitchen big enough to walk round it.
        if clear.area > 11:
            for iw in (1.6, 1.3):
                isl = lpoly(sp, -iw / 2, iw / 2, .66 + 1.05, .66 + 1.05 + .75)
                ring = isl.buffer(.9, join_style=2)
                if ctx['inside'].covers(isl) and ctx['inside'].covers(ring.intersection(clear.buffer(-.01)).buffer(0)) and not hits(isl, [q for q, _ in ctx['doors']]) and not hits(ring, [q for q, _ in ctx['doors']] + [p_ for p_ in ctx['placed'] if p_ is not foot]):
                    ix0, iy0, ix1, iy1 = isl.bounds
                    edit_mark = k.edit_mark()
                    rect((ix0 + .04, iy0 + .04, z + .10, ix1 - .04, iy1 - .04, z + .86), M['casework'], f, 'furniture')
                    rect((ix0, iy0, z + .86, ix1, iy1, z + .91), M['counter'], f, 'furniture')
                    ctx['placed'].append(isl)
                    furnishing('island', room, isl)
                    k.editable('island', room, isl, edit_mark)
                    if upgraded_interior:
                        for du in (-iw / 4, iw / 4):
                            x, y = P(sp, du, .66 + 1.05 + .375)
                            lamp(x, y, z + 1.75, f, True)
                    break

    def care_room_set(ctx):
        """One residential recliner facing north (+x), with editable support furniture.

        The monitor is an illustrative prop, not a clinical equipment specification.
        All pieces use the existing house materials and respect door approaches.
        """
        room, f, clear = ctx['room'], ctx['floor'], ctx['clear']; z = f * H
        # Furnish the main rectangular bay of an L-shaped care room, rather
        # than its bounding box (whose centre may lie in the missing corner).
        xs = sorted({pt[0] for pt in clear.exterior.coords})
        ys = sorted({pt[1] for pt in clear.exterior.coords})
        bays = [box(a, c, bb, d) for i, a in enumerate(xs) for bb in xs[i+1:]
                for j, c in enumerate(ys) for d in ys[j+1:]
                if clear.covers(box(a, c, bb, d))]
        main_bay = max(bays, key=lambda q: q.area) if bays else clear
        x0, y0, x1, y1 = main_bay.bounds; cx, cy = (x0+x1)/2, (y0+y1)/2
        if room.get('reclinerPosition'):
            cx,cy=np.array(room['reclinerPosition'])/1000
            # The TV stays on the solid wall directly in front of the authored chair.
            ray=clear.intersection(LineString([(cx,cy),(clear.bounds[2]+1,cy)]))
            x1=ray.bounds[2]
        def allowed(foot):
            return ctx['inside'].covers(foot) and not hits(foot, ctx['placed']+[q for q,_ in ctx['doors']])
        def finish(kind, foot, mark):
            furnishing(kind,room,foot);k.editable(kind,room,foot,mark);ctx['placed'].append(foot)
        foot=box(cx-1.1,cy-.55,cx+1.1,cy+.55)
        if allowed(foot):
            mark=k.edit_mark()
            rb((cx,cy,z+.26),(2.15,1.1,.25),M['bedframe'],f,r=.04,owner=room['id'])
            rb((cx+.28,cy,z+.48),(1.5,1.1,.22),'linen',f,r=.07,owner=room['id'])
            rb((cx-.70,cy,z+.64),(.70,1.1,.20),'linen',f,r=.07,owner=room['id'])
            k.nodes[-1]['rotation'][1]=.40
            rb((cx-.90,cy,z+.86),(.40,.94,.15),'linen',f,r=.06,owner=room['id'])
            for xx in (cx-.9,cx+.9):
                for yy in (cy-.45,cy+.45):cylinder((xx,yy,z+.10),.05,.15,'steel',f)
            finish('reclining-bed',foot,mark)
        # Facing +x, the occupant's left is +y and the veranda is to the right.
        equipment_left=room.get('careLayout')=='equipment-left'
        seats=([(name,x0+1.45+i*.85,y0+1.30,math.pi) for i,name in enumerate(('care-chair-right','care-chair-right-2','care-chair-right-3'))]
               if equipment_left else [(name,cx-.55,yy,math.pi/2) for name,yy in [('care-chair-left',cy+.85),('care-chair-right',cy-.85)]])
        for name,xx,yy,angle in seats:
            foot=box(xx-.28,yy-.27,xx+.28,yy+.27)
            if allowed(foot):
                mark=k.edit_mark();chair(xx,yy,z,f,angle);finish(name,foot,mark)
        xx,yy=(x0+2.0,y1-.55) if equipment_left else ((cx-1.55 if room.get('reclinerPosition') else cx+.75),cy-.85)
        foot=box(xx-.40,yy-.25,xx+.40,yy+.25)
        if allowed(foot):
            mark=k.edit_mark()
            rb((xx,yy,z+.77),(.80,.50,.07),M['counter'],f,r=.025)
            for dx in (-.32,.32):
                for dy in (-.18,.18):beam((xx+dx,yy+dy,z+.06),(xx+dx,yy+dy,z+.74),.018,'steel',f,'furniture')
            rb((xx+.13,yy,z+.84),(.20,.22,.05),'frame',f,r=.015)
            beam((xx+.13,yy,z+.85),(xx+.13,yy,z+1.03),.022,'steel',f,'furniture')
            rb((xx+.13,yy,z+1.13),(.06,.32,.25),'frame',f,r=.02)
            rect((xx+.095,yy-.135,z+1.03,xx+.101,yy+.135,z+1.22),'blackglass',f,'furniture')
            rb((xx-.20,yy,z+.83),(.20,.28,.045),M['casework'],f,r=.015)
            finish('equipment-table',foot,mark)
        xx,yy=(x0+.52,y1-.22) if equipment_left else ((x0+1.7,cy+.1) if room.get('reclinerPosition') else (cx+.65,cy+1.10))
        cupboard_depth=.40 if equipment_left else .45
        foot=box(xx-.45,yy-cupboard_depth/2,xx+.45,yy+cupboard_depth/2)
        if allowed(foot):
            mark=k.edit_mark()
            rb((xx,yy,z+.52),(.90,cupboard_depth,1.0),M['casework'],f,r=.02)
            for dx in (-.225,.225):
                rb((xx+dx,yy-cupboard_depth/2-.007,z+.54),(.43,.025,.90),M['bedframe'],f,r=.006)
                beam((xx+dx,yy-cupboard_depth/2-.030,z+.55),(xx+dx,yy-cupboard_depth/2-.030,z+.70),.008,'steel',f,'furniture')
            finish('care-cupboard',foot,mark)
        ty=cy+room.get('tvOffset',0)/1000
        mark=k.edit_mark()
        rect((x1-.06,ty-.70,z+1.05,x1-.01,ty+.70,z+1.85),'frame',f,'furniture',owner=room['id'])
        rect((x1-.067,ty-.65,z+1.10,x1-.059,ty+.65,z+1.80),'blackglass',f,'furniture',owner=room['id'])
        foot=box(x1-.07,ty-.70,x1,ty+.70)
        finish('large-tv',foot,mark)

    for counter in b.get('built_in_counters',[]):
        f=counter['floor'];z=f*H;counter_top=metres(Polygon(counter['polygon']));body=counter_top.buffer(-.025,join_style=2);mark=k.edit_mark()
        room=next((r for r in b['spaces'] if r['id'] in counter['roomIds'] and r['kind']=='kitchen'),None)
        if room is None:room=next(r for r in b['spaces'] if r['id'] in counter['roomIds'] and r['kind'] in ('hall','dining','living','family'))
        poly_mesh(body,z,z+.89,'wall',f,'furniture',counter['id']+'/base',room['id'])
        poly_mesh(counter_top,z+.89,z+.95,M['casework'],f,'furniture',counter['id']+'/top',room['id'])
        center=counter_top.centroid;x0,y0,x1,y1=counter_top.bounds
        horizontal=x1-x0>y1-y0
        px,py=(x0+.34,center.y) if horizontal else (center.x,y0+.34)
        bx,by=(x1-.40,center.y) if horizontal else (center.x,y1-.40)
        for i in range(5):cylinder((px,py,z+.96+i*.017),.12,.015,'ceramic',f,'detail')
        rb((bx,by,z+.976),(.40,.27,.04) if horizontal else (.27,.40,.04),M['table'],f,r=.025)
        furnishing('serving-counter',room,counter_top);k.editable('serving-counter',room,counter_top,mark)

    room_lawns=[]
    for room in b['spaces']:
        f = room['floor']; z = f * H; p = Polygon(np.array(room['clear']) / 1000)
        kind = room['kind']
        if kind not in ({'stair'} | OUTDOOR | NON_WALKABLE):
            lining(room, f, z + .009, z + .09, 'skirting', 'skirting')
            downlights(room, f, z + room['ceilingHeight']/1000 - .007 if 'ceilingHeight' in room else z + H - .157)
            if room.get('underStair'):
                poly_mesh(p,z+2.10,z+2.14,'ceiling',f,'ceiling',room['id']+'/ceiling',room['id'])
            if room.get('mechanicalVentilation'):
                cp=p.representative_point();ch=room.get('ceilingHeight',H*1000-150)/1000
                rect((cp.x-.12,cp.y-.12,z+ch-.02,cp.x+.12,cp.y+.12,z+ch-.01),'frame',f,'fixture',room['id']+'/exhaust-grille',room['id'])
        if custom and kind == 'drying-yard' and room.get('drain'):
            x0,y0,x1,y1=p.bounds;xx=(x0+x1)/2;yy=y0+.28;mark=k.edit_mark()
            rb((xx,yy,z+.40),(.64,.48,.78),M['casework'],f,r=.02)
            rb((xx,yy,z+.83),(.70,.52,.10),'ceramic',f,r=.06)
            rb((xx,yy,z+.884),(.47,.30,.012),'steel',f,r=.03)
            beam((xx,yy-.18,z+.85),(xx,yy-.18,z+1.08),.018,'steel',f,'fixture')
            beam((xx,yy-.18,z+1.08),(xx,yy,z+1.08),.018,'steel',f,'fixture')
            foot=box(xx-.35,yy-.26,xx+.35,yy+.26);furnishing('wash-basin',room,foot);k.editable('wash-basin',room,foot,mark)
            rect((x1-.22,y1-.22,z+.01,x1-.1,y1-.1,z+.02),'steel',f,'drain',room['id']+'-drain',room['id'])
            continue
        if custom and room.get('finishStyle')=='garden-lawn':
            from .courtyard_finishes import sheltered_lawn
            room_lawns.extend(sheltered_lawn(k,materials,room,H))
            continue
        if custom and kind == 'courtyard' and room.get('glassCover'):
            from .courtyard_finishes import skylit_garden
            skylit_garden(k,materials,room,H)
            continue
        if custom and kind == 'courtyard' and room.get('garden'):
            # A low planted border on the far edge leaves the window-side path clear.
            # It sits above the authored courtyard slab, not below it at site grade.
            x0,y0,x1,y1=p.bounds
            bed=p.buffer(-.15,join_style=2).intersection(box(x0+.15,y1-.65,x1-.15,y1-.15))
            poly_mesh(bed,z+.012,z+.04,'soil',f,'landscape',room['id']+'/garden-bed',room['id'])
            for i,xx in enumerate(np.arange(x0+.45,x1-.35,1.25)):
                yy=y1-.40
                if bed.covers(Point(xx,yy).buffer(.19)):
                    k.plant(xx,yy,z+.04,'shrub_round',height=.55)
            continue
        if kind == 'care-room':
            care_room_set(room_context(room))
            continue
        if kind in ('living', 'drawing-room', 'family', 'dining'):
            ctx = room_context(room)
            ctx['doors'] = ctx['doors'] + [(q, {'kind': 'open'}) for q in open_keepouts(ctx)]
            if kind in ('living', 'drawing-room', 'family'):
                mark = k.checkpoint(); before = (list(ctx['placed']), list(ctx['doors']))
                if room.get('diningPosition'):
                    dining_group(ctx,anchor=Point(*(np.array(room['diningPosition'])/1000)),sizes=(room['diningLength']/1000,) if room.get('diningLength') else (2.2,1.8,1.5),open_plan=True)
                sofa_group(ctx)
                if not room.get('diningPosition') and 'dining' in room['name'].lower() and dining_group(ctx) is None:
                    # Too tight for a table once the lounge group is down: seat the table first and fit the lounge
                    # around it, keeping that only if both groups found a place.
                    def reset():
                        k.rollback(mark); ctx['placed'], ctx['doors'] = list(before[0]), list(before[1])
                    reset()
                    kitchen = next((Polygon(np.array(s['polygon']) / 1000) for s in b['spaces'] if s['floor'] == f and s['kind'] == 'kitchen'), None)
                    near = nearest_points(ctx['clear'], kitchen)[0] if kitchen is not None else None
                    dining_group(ctx, anchor=near, sizes=(1.2, 1.0)); sofa_group(ctx)
                    got = {it['kind'] for it in furniture if it['room_id'] == room['id']}
                    if not {'sofa', 'dining-set'} <= got:
                        reset(); sofa_group(ctx)
                if upgraded_interior and p.area > 9:
                    corners = spots(ctx, .6, .6, front=0, height=2.0, step=.2)
                    if corners:
                        sp = min(corners, key=lambda s: min(s['s'], s['L'] - s['s']))
                        px, py = P(sp, 0, .34)
                        k.plant(px, py, z, 'fiddle_leaf', height=1.65, f=f, pot=(.21, .44, 'planter'))
                wall_art(ctx, 1.0 if any(o.get('servingCounter')=='full' and room['id'] in o['connects'] for o in b['openings']) else 1.2, .8)
            else:
                dining_group(ctx, public_route(room))
                wall_art(ctx, 1.0, .7)
            continue
        if kind in ('bedroom', 'bathroom', 'powder-room', 'study', 'utility', 'drying-room', 'dress', 'pooja', 'store', 'kitchen', 'hall'):
            ctx = room_context(room)
            if kind == 'bedroom':
                bed_set(ctx, room['name'].startswith('Master'))
                # A compact single-bed L-shaped room needs circulation at its return.
                compact_return = room.get('bedType') == 'single' and p.area < 10 and len(p.exterior.coords) > 5
                storage = wardrobe(ctx, (.9,)) if compact_return else wardrobe(ctx)
                if storage is None:
                    dresser(ctx)
                if upgraded_interior and p.area > 12:
                    corners = spots(ctx, .55, .55, front=0, height=1.3, step=.2)
                    if corners:
                        sp = min(corners, key=lambda s: min(s['s'], s['L'] - s['s']))
                        px, py = P(sp, 0, .32)
                        k.plant(px, py, z, 'monstera', height=.95, f=f, pot=(.19, .36, 'planter'))
                wall_art(ctx)
            elif kind in ('bathroom','powder-room'):
                bath_set(ctx)
            elif kind == 'kitchen':
                kitchen_set(ctx)
            elif kind == 'study':
                desk_set(ctx)
                wall_art(ctx)
            elif kind in ('utility','drying-room'):
                utility_set(ctx)
                if kind=='drying-room' and room.get('drain'):
                    cp=p.representative_point();rect((cp.x-.06,cp.y-.06,z+.009,cp.x+.06,cp.y+.06,z+.012),'steel',f,'drain',room['id']+'-drain',room['id'])
            elif kind == 'dress':
                dress_set(ctx)
            elif kind == 'pooja':
                pooja_set(ctx)
            elif kind == 'store':
                store_set(ctx)
            elif kind == 'hall' and p.area > 3:
                wall_art(ctx, .8, .6)
            continue

    # ---------------------------------------------------------------- stairs & terraces
    for st in b['stairs']:
        from .stair_geometry import footprint as stair_footprint
        p = metres(stair_footprint(st))
        colliders.append({'id': st['id'] + '/stair-walk-not-supported', 'floor': st['floor'], 'polygon': list(p.exterior.coords), 'kind': 'stair'})
    # Guarding follows the actual open terrace perimeter; it is a visual scheme, not a certified balustrade.
    if upgraded_interior:
        # A foyer inside the main door, marked by a slatted timber ceiling as in the reference house: oak slats on
        # a walnut ground, with two downlights beneath them.
        ea = np.array(ew['a'], float) / 1000; eb = np.array(ew['b'], float) / 1000
        eu = (eb - ea) / np.linalg.norm(eb - ea); en = np.array([-eu[1], eu[0]])
        em = ea + eu * (entry['offset'] + entry['width'] / 2) / 1000
        host = next((s_ for s_ in b['spaces'] if s_['id'] == entry.get('swing')), None) or \
            next((s_ for s_ in b['spaces'] if s_['floor'] == 0 and s_['kind'] == 'living'), None)
        if host is not None:
            hclear = Polygon(np.array(host['clear']) / 1000)
            if not hclear.contains(Point(*(em + en * .6))):
                en = -en
            half, deep = entry['width'] / 2000 + .7, 1.9
            quad = lambda t0, t1: Polygon([em + eu * t0, em + eu * t1, em + eu * t1 + en * deep, em + eu * t0 + en * deep])
            zone = quad(-half, half).intersection(hclear.buffer(-.03))
            if custom:zone=zone.intersection(metres(geometry(b['roofs'][0]['ceiling'])))
            if not zone.is_empty and zone.geom_type == 'Polygon' and zone.area > 2.:
                poly_mesh(zone, H - .2, H - .156, 'walnut', 0, 'ceiling-feature', 'foyer-ceiling', 'foyer-ceiling')
                for t in np.arange(-half + .06, half - .04, .085):
                    slat = quad(t - .019, t + .019).intersection(zone)
                    if slat.geom_type == 'Polygon' and slat.area > .01:
                        poly_mesh(slat, H - .25, H - .2, 'oak', 0, 'ceiling-feature', owner='foyer-ceiling')
                for d_ in (.65, 1.35):
                    lx, ly = em + en * d_
                    if zone.contains(Point(lx, ly)):
                        cylinder((lx, ly, H - .256), .045, .008, 'frame', 0, 'downlight')
                        cylinder((lx, ly, H - .261), .034, .004, 'lamp', 0, 'downlight')
                        k.light((lx, ly, H - .45), 9, kind='downlight')

    if custom or rooftop:
        for guard in rb_model.get('guards',[]):
            edge=LineString(np.array(guard['points'])/1000);f=guard['floor'];z=f*H;own=guard['owner']
            poly_mesh(edge.buffer(.008,cap_style=2),z+.06,z+1.1,'glass',f,'railing',guard['id'],own)
            poly_mesh(edge.buffer(.02,cap_style=2),z+1.1,z+1.13,'frame',f,'railing',guard['id']+'-cap',own)
            colliders.append({'id':guard['id'],'floor':f,'polygon':list(edge.buffer(.06,cap_style=2).exterior.coords),'kind':'guard'})
    for terr in [s for s in b['spaces'] if s['kind'] in ('terrace','veranda','balcony')]:
        p = Polygon(np.array(terr['polygon']) / 1000); f = terr['floor']; z = f * H
        for a, c in zip(list(p.exterior.coords), list(p.exterior.coords)[1:]):
            edge = LineString([a, c])
            if not custom and fp.boundary.buffer(.01).covers(edge):
                if modern:
                    glass = edge.buffer(.008, cap_style=2); poly_mesh(glass, z + .06, z + 1.1, 'glass', f, 'railing')
                    poly_mesh(edge.buffer(.03, cap_style=2), z + .009, z + .08, 'frame', f, 'railing')
                    poly_mesh(edge.buffer(.02, cap_style=2), z + 1.1, z + 1.13, 'frame', f, 'railing')
                else:
                    beam((*a, z + 1.1), (*c, z + 1.1), .023, 'frame', f, 'railing')
                    for t0 in np.arange(.08, edge.length, .95):
                        q = edge.interpolate(t0); beam((q.x, q.y, z + .02), (q.x, q.y, z + 1.1), .018, 'frame', f, 'railing')
                    glass = edge.buffer(.012, cap_style=2); poly_mesh(glass, z + .12, z + 1.05, 'glass', f, 'railing')
        if terr.get('finishStyle')=='warm-stone':
            # Finish-only layers: the authored floor, doors and clear circulation stay fixed.
            materials['porch-limestone']={**materials['floor'],'roughness':.72,'clearcoat':0}
            bed=box(*(np.array(terr['gardenBed'])/1000)) if terr.get('gardenBed') else Polygon()
            poly_mesh(p.difference(bed),z+.011,z+.017,'porch-limestone',f,'finish',terr['id']+'/stone-finish',terr['id'])
            inset=p.buffer(-.18,join_style=2).intersection(metres(geometry(b['roofs'][f]['ceiling'])));x0,y0,x1,y1=p.bounds
            for j,xx in enumerate(np.arange(x0+.18,x1-.18,.18)):
                strip=inset.intersection(box(xx,y0,xx+.135,y1))
                if not strip.is_empty:
                    poly_mesh(strip,z+H-.205,z+H-.17,'oak',f,'ceiling',terr['id']+f'/ceiling-slat-{j}',terr['id'])
            if terr.get('gardenBed'):
                from .courtyard_finishes import daylight_veranda
                room_lawns.extend(daylight_veranda(k,materials,b,terr,H))
                colliders.append({'id':terr['id']+'/garden-bed','floor':f,'polygon':list(bed.exterior.coords),'kind':'landscape'})
            # Wall lamps sit above door heads, never in the clear glass openings.
            for wall in [w for w in b['walls'] if terr['id'] in w['rooms']]:
                a=np.array(wall['a'])/1000;c=np.array(wall['b'])/1000;length=np.linalg.norm(c-a)
                if length<1.2:continue
                t=(c-a)/length;n=np.array([-t[1],t[0]])
                if not p.buffer(.01).covers(Point(*( (a+c)/2+n*.12))):n=-n
                for j,tt in enumerate(np.arange(.45,length-.25,2.3)):
                    q=a+t*tt+n*(wall['thickness']/2000+.035)
                    if not p.buffer(.02).covers(Point(*q)):continue
                    rb((q[0],q[1],z+2.60),(.10,.075,.22),'frame',f,'fixture',r=.015,rot=math.atan2(t[1],t[0]))
                    rb((q[0],q[1],z+2.485),(.075,.055,.012),'lamp',f,'fixture',r=.003)
                    k.light((q[0]+n[0]*.08,q[1]+n[1]*.08,z+2.46),22,kind='wall')
            # Thin timber bands dress the plot-side wall; nothing stands in the walkway.
            if abs(x1-(xmax-.15))<.05:
                for j,zz in enumerate(np.arange(.35,1.46,.16)):
                    rect((x1-.07,max(0,ymin)+.18,z+zz,x1-.045,y1-.18,z+zz+.10),'oak',f,'wall-panel',terr['id']+f'/boundary-band-{j}',terr['id'])
        center = p.representative_point()
        if terr.get('clearAccess'):continue
        if modern:
            tx0, ty0, tx1, ty1 = p.bounds
            for i, xx in enumerate((tx0 + .5, tx1 - .5)):
                k.plant(xx, ty0 + .45, z, 'cordyline' if i else 'shrub_round', height=.8, f=f, pot=(.24, .5, 'planter'))
            if tx1 - tx0 > 2.6 and ty1 - ty0 > 1.9:
                edit_mark = k.edit_mark()
                for j, xx in enumerate((center.x - .55, center.x + .55)):
                    rb((xx, center.y + .1, z + .22), (.62, 1.5, .12), 'sling', f, 'outdoor-furniture', .04)
                    rb((xx, center.y + .72, z + .4), (.62, .35, .1), 'sling', f, 'outdoor-furniture', .04)
                    for dx in (-.26, .26):
                        for dy in (-.6, .75):
                            beam((xx + dx, center.y + dy, z + .01), (xx + dx, center.y + dy, z + .17), .013, 'frame', f, 'outdoor-furniture')
                furnishing('lounge', terr, box(center.x - .9, center.y - .66, center.x + .9, center.y + .95))
                k.editable('lounge', terr, box(center.x - .9, center.y - .66, center.x + .9, center.y + .95), edit_mark)
        else:
            k.plant(center.x, center.y, z, 'shrub_flowering', height=.75, f=f, pot=(.2, .32, 'ceramic'))
    # A true U stair: 18 risers, two flights, mid/top landings, no upper slab over the well.
    for st in b['stairs']:
        if st['to_floor'] is None:
            continue
        f = st['floor']; z = f * H; x = st['x'] / 1000; y = st['y'] / 1000; r = st['riser_mm'] / 1000; t = st['tread_mm'] / 1000; fw = st['flight_width'] / 1000; well = st['well'] / 1000; land = st['landing_mm'] / 1000
        node_start=len(k.nodes)
        n=st['riser_count']//2;steps=n-1
        for j in range(steps):
            yy = y + land + j * t
            rect((x, yy, z + max(0, j * r - .08), x + fw, yy + t, z + (j + 1) * r), M['tread'], f, 'stair')
        # Landings and structural-stringer intent are visual coordination only.
        mid_y = y + land + steps * t
        rect((x, mid_y, z + n * r - .16, x + 2 * fw + well, mid_y + land, z + n * r), M['tread'], f, 'stair')
        for j in range(steps):
            yy = y + land + (steps - 1 - j) * t
            rect((x + fw + well, yy, z + n * r + j * r - .09, x + 2 * fw + well, yy + t, z + (n + 1 + j) * r), M['tread'], f, 'stair')
        rect((x, y, z + H - .16, x + 2 * fw + well, y + land, z + H), M['tread'], f + 1, 'stair')
        # Handrails and pickets follow the two flight slopes.
        rails=[(x + fw - .04, z, True), (x + fw + well + .04, z + H, False)]
        if 'left' in st.get('open_sides',[]):rails.append((x+.04,z,True))
        if 'right' in st.get('open_sides',[]):rails.append((x+2*fw+well-.04,z+H,False))
        for xrail, start_z, ascending in rails:
            za = start_z + r if ascending else start_z; zb = z + n * r
            beam((xrail, y + land, za + .9), (xrail, mid_y, zb + .9), .025, 'timber' if not upgraded_interior else 'walnut', f, 'railing')
            for j in range(n):
                yy = y + land + j * t; zz = (z + (j + 1) * r) if ascending else (z + H - j * r)
                beam((xrail, yy, zz), (xrail, yy, zz + .89), .010, 'frame', f, 'railing')

        if st.get('rotation')==90:
            from .stair_geometry import point as stair_point
            for item in k.nodes[node_start:]:
                item['position'][:2]=stair_point(st,item['position'][:2],scale=.001)
                item['rotation'][2]+=math.pi/2

    if b.get('planning',{}).get('facadeStyle')=='warm-layered':
        from .courtyard_finishes import layered_facade, open_puja_entry
        layered_facade(k,materials,b,H)
        open_puja_entry(k,b)

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
        # Facade accents go on the blank end of the front wall away from the door (the door may sit near either end).
        door_left = ex < W / 2
        if facade_style == 'terracotta':
            # Open slatted screen across only the blank end of the facade.
            span = min(1.9, W * .2 - .35)
            lo = W - .35 - span if door_left else .35
            lo, hi = (max(lo, ex + .95), W - .35) if door_left else (lo, min(lo + span, ex - .95))
            for xx in np.arange(lo, hi - .05, .18):
                for yy in (0, .08):
                    rect((xx, -.24 - yy, .65, xx + .05, -.18 - yy, top + .5), 'stone', 0, 'screen')
        if facade_style in ('warm', 'graphite', 'concrete'):
            blank_width = 1.05 if storeys > 1 else .6
            b0 = W - .24 - blank_width if door_left else .24
            if (b0 > ex + .9) if door_left else (b0 + blank_width < ex - .9):
                rect((b0, -.16, .15, b0 + blank_width, -.015, top + .36), 'stone', 0, 'accent', 'stone-blade')
                if facade_style == 'graphite':
                    for xx in np.arange(b0 + .03, b0 + blank_width, .12):
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
            # L-shaped entrance (modern_exterior.py): the flight covers the door end of the landing and returns down
            # its side; the other end is a sit-out. Every tread has a nosing with an LED strip in its shadow.
            sit = [q / 1000 for q in geo['sitout_x_mm']] if geo.get('sitout_x_mm') else None
            ret = geo.get('return_steps_mm', 0) / 1000
            right = geo.get('flight_side') == 'right'
            fx0, fx1 = x0 - .3, x1 + .3
            if sit:
                fx0, fx1 = (sit[1], fx1) if sit[0] <= x0 + .01 else (fx0, sit[0])
            rise = (land - g) / 2

            def nosing(xa, ya, xb, yb, zt, axis):
                # A tread nosing projecting 3 cm over an LED strip set into the riser just below it.
                if axis == 'y':
                    rect((xa, ya - .03, zt - .035, xb, ya, zt), 'step', 0, 'step', owner=aid)
                    rect((xa + .04, ya - .016, zt - .062, xb - .04, ya + .004, zt - .036), 'lamp', 0, 'fixture', owner=aid)
                else:
                    s = 1 if right else -1
                    edge = xb if right else xa
                    rect((min(edge, edge + s * .03), ya, zt - .035, max(edge, edge + s * .03), yb, zt), 'step', 0, 'step', owner=aid)
                    rect((min(edge - s * .004, edge + s * .016), ya + .04, zt - .062, max(edge - s * .004, edge + s * .016), yb - .04, zt - .036), 'lamp', 0, 'fixture', owner=aid)

            for i, (d0, d1) in enumerate(((.62, .31), (.31, 0))):
                zt = g + (i + 1) * rise - .0005
                a, b2 = fx0, fx1
                if ret:
                    a, b2 = (a, x1 + d0) if right else (x0 - d0, b2)
                rect((a, y0 - d0, g, b2, y0 - d1, zt), 'step', 0, 'step', aid + f'-step-{i}', aid)
                nosing(a, y0 - d0, b2, y0 - d0, zt, 'y')
                if ret:
                    ra, rb2 = (x1 + d1, x1 + d0) if right else (x0 - d0, x0 - d1)
                    rect((ra, y0 - d1, g, rb2, y0 + ret, zt), 'step', 0, 'step', aid + f'-return-{i}', aid)
                    nosing(ra, y0 - d1, rb2, y0 + ret, zt, 'x')
            k.light(((fx0 + fx1) / 2, y0 - .9, g + .25), 6, kind='step')
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
            if sit:
                # Sit-out: a stone-clad column at its outer front corner carries the canopy (or balcony) edge; a
                # raised planter of grasses runs along the front beside it and a timber bench on a stone plinth
                # stands against the facade.
                sx0, sx1 = sit
                on_left = sx0 <= x0 + .01
                cx = sx0 + .17 if on_left else sx1 - .17
                rect((cx - .15, y0 + .02, land, cx + .15, y0 + .32, cz), 'cladding', 0, 'cladding', aid + '-column', aid)
                pa, pb = (cx + .2, sx1 - .05) if on_left else (sx0 + .05, cx - .2)
                if pb - pa > .5 and b.get('planning',{}).get('frontCourt')!='tiled':
                    rect((pa, y0 + .03, land, pb, y0 + .43, land + .42), 'planter', 0, 'planter', aid + '-sitout-planter', aid)
                    rect((pa + .04, y0 + .07, land + .42, pb - .04, y0 + .39, land + .43), 'soil', 0, 'planter', owner=aid)
                    for xx in np.arange(pa + .22, pb - .1, .42):
                        k.plant(xx, y0 + .23, land + .43, 'grass_ornamental', scale=.55)
                ba, bb = sx0 + .12, sx1 - .12
                if bb - ba > .7:
                    rect((ba + .08, -.5, land, bb - .08, -.12, land + .36), 'cladding', 0, 'outdoor-furniture', aid + '-bench-plinth', aid)
                    for j, yy in enumerate(np.arange(-.54, -.1, .075)):
                        rect((ba, yy, land + .36, bb, yy + .06, land + .41), 'timber', 0, 'outdoor-furniture', owner=aid)
                    rb(((ba + bb) / 2, -.32, land + .46), (bb - ba - .12, .4, .09), 'fabric', 0, 'outdoor-furniture', .035, owner=aid)
                    rb((bb - .28, -.14, land + .64), (.4, .12, .36), 'fabric-dark', 0, 'outdoor-furniture', .05, owner=aid)
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
        elif kind == 'balcony':
            # Refurbished terrace: slab and timber deck at the first-floor level, a frameless glass balustrade in a
            # base shoe with a slim handrail cap, a pergola of slim posts and timber louvres with downlights, and
            # seating on an outdoor rug between planted corners.
            frameless = geo.get('style') == 'frameless_glass'
            fz = floor * H
            deck = fz - .005 if frameless else fz
            th = geo.get('slab_thickness_mm', 250 if frameless else 220) / 1000
            finish = TERRACE_FINISH.get(theme_id, TERRACE_FINISH['current'])
            rect((x0, y0, deck - .025 - th, x1, y1, deck - .025), 'roof' if frameless else finish['slab'], floor, 'balcony', aid + '-slab', aid)
            rect((x0 + .03, y0 + .03, deck - .025, x1 - .03, y1 - .01, deck), 'deck', floor, 'balcony', aid + '-deck', aid)
            rail = geo.get('rail_height_mm', 1100) / 1000
            # Base shoe, glass and handrail cap on the three open sides (front, then the two returns to the facade).
            for sx0, sy0, sx1, sy1 in ((x0, y0, x1, y0 + .07), (x0, y0 + .07, x0 + .07, y1 - .01), (x1 - .07, y0 + .07, x1, y1 - .01)):
                along_x = sy1 - sy0 < .1
                rect((sx0, sy0, deck, sx1, sy1, deck + .07), 'frame', floor, 'railing', owner=aid)
                pane = (sx0, sy0 + .029, sx1, sy0 + .041) if along_x else (sx0 + .029, sy0, sx0 + .041, sy1)
                rect((pane[0], pane[1], deck + .07, pane[2], pane[3], deck + rail - .04), 'railglass', floor, 'railing', owner=aid)
                cap = (sx0, sy0 + .01, sx1, sy1 - .01) if along_x else (sx0 + .01, sy0, sx1 - .01, sy1)
                rect((cap[0], cap[1], deck + rail - .04, cap[2], cap[3], deck + rail), finish['cap'], floor, 'railing', owner=aid)
            width, depth = x1 - x0, y1 - y0
            pz = min(top - .2, deck + 2.95)
            if depth >= 1.2 and width >= 2.4 and pz - deck >= 2.4:
                pm, slat = finish['pergola'], 'timber'
                for px in (x0 + .1, x1 - .18):
                    rect((px, y0 + .1, deck, px + .08, y0 + .18, pz - .16), pm, floor, 'pergola', owner=aid)
                rect((x0 + .06, y0 + .1, pz - .16, x1 - .06, y0 + .18, pz), pm, floor, 'pergola', aid + '-pergola', aid)
                for px in (x0 + .06, x1 - .14):
                    rect((px, y0 + .18, pz - .16, px + .08, y1 - .08, pz), pm, floor, 'pergola', owner=aid)
                rect((x0 + .14, y1 - .08, pz - .16, x1 - .14, y1, pz), pm, floor, 'pergola', owner=aid)
                for xx in np.arange(x0 + .24, x1 - .2, .16):
                    rect((xx, y0 + .18, pz - .13, xx + .045, y1 - .08, pz - .02), slat, floor, 'pergola', owner=aid)
                for fx in (x0 + width * .3, x0 + width * .7):
                    cylinder((fx, y0 + .14, pz - .18), .035, .02, 'lamp', floor, 'downlight')
                    k.light((fx, y0 + .14, pz - .3), 18, kind='downlight')
            if geo.get('planter_edge'):
                rect((x0 + .25, y0 - .22, deck - .1, x1 - .25, y0 - .02, deck + .12), 'stone', floor, 'landscape', aid + '-planter', aid)
                for xx in np.arange(x0 + .5, x1 - .3, 1.0):
                    k.plant(xx, y0 - .10, deck + .12, 'shrub_flowering', height=.35, f=floor)
            if not frameless and width > 3.8:
                for j, yy in enumerate(np.arange(y0 + .3, y1 - .15, .11)):
                    rect((x1 - .26, yy - .02, deck + .02, x1 - .21, yy + .02, deck + 1.95), 'timber', floor, 'screen', aid + f'-privacy-{j}', aid)
            if depth >= 1.2 and width >= 2.6:
                # Seating on an outdoor rug, backs to the facade and clear of a door opening onto the deck, with a
                # tall planter at each front corner.
                half = .9
                lo, hi = x0 + .75 + half, x1 - .75 - half
                cx0 = min(max(x0 + width * .38, lo), hi) if hi >= lo else None
                door = next((o for o in b['openings'] if o['id'] == geo.get('access_opening_id')), None)
                if cx0 is not None and door:
                    dw = hosts[door['wall_id']]; da = np.array(dw['a']) / 1000; du = np.array(dw['b']) / 1000 - da; du /= np.linalg.norm(du)
                    ends = [da + du * (door['offset'] + t) / 1000 for t in (0, door['width'])]
                    d0, d1 = sorted(e[0] for e in ends)
                    if abs(ends[0][1] - y1) < .4 and d1 + .3 > cx0 - half and d0 - .3 < cx0 + half:
                        cx0 = d0 - .3 - half if d0 - .3 - half >= lo else d1 + .3 + half if d1 + .3 + half <= hi else None
                if cx0 is not None:
                    rect((cx0 - half, max(y0 + .3, y1 - 1.3), deck, cx0 + half, y1 - .12, deck + .008), 'rug', floor, 'rug', owner=aid)
                    if frameless:
                        for xx in (cx0 - .5, cx0 + .5):
                            rb((xx, y1 - .6, deck + .36), (.66, .7, .12), 'sling', floor, 'outdoor-furniture', .05, owner=aid)
                            rb((xx, y1 - .27, deck + .6), (.66, .1, .42), 'sling', floor, 'outdoor-furniture', .04, owner=aid)
                        cylinder((cx0, y1 - .6, deck + .45), .15, .03, M['counter'], floor, 'outdoor-furniture')
                        beam((cx0, y1 - .6, deck + .01), (cx0, y1 - .6, deck + .435), .018, 'frame', floor, 'outdoor-furniture')
                    else:
                        rb((cx0, y1 - .52, deck + .3), (1.65, .6, .3), 'fabric', floor, 'outdoor-furniture', .08, owner=aid)
                        rb((cx0, y1 - .25, deck + .62), (1.65, .12, .42), 'fabric', floor, 'outdoor-furniture', .06, owner=aid)
                        if y1 - 1.35 - .225 >= y0 + .2:
                            rb((cx0, y1 - 1.35, deck + .19), (.7, .45, .06), 'stone', floor, 'outdoor-furniture', .05, owner=aid)
                k.plant(x1 - .45 if frameless else x1 - .6, y0 + .45, deck, 'strelitzia', height=1.3, f=floor, pot=(.22, .45, 'planter'))
                k.plant(x0 + .45, y0 + .45, deck, 'grass_ornamental', height=.55, f=floor, pot=(.24, .42, 'planter'))
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
        elif kind == 'stair_tower':
            if rooftop:continue  # physical hollow headhouses are rendered from canonical roof objects below
            # The stair's headroom over the roof: a rendered box with stone cladding on the faces that continue
            # the facade, a floating lid, a slot window to the street and a glazed door onto the roof terrace.
            zt, z1 = top, top + geo.get('height_mm', 2700) / 1000
            fb = fp.bounds
            rect((x0, y0, zt, x1, y1, z1 - .2), 'wall', floor, 'massing', aid + '-body', aid)
            edge = {'front': abs(y0 - fb[1]) < .05, 'back': abs(y1 - fb[3]) < .05, 'left': abs(x0 - fb[0]) < .05, 'right': abs(x1 - fb[2]) < .05}
            c = .04
            if edge['front']:
                rect((x0 - (c if edge['left'] else 0), y0 - c, zt + .22, x1 + (c if edge['right'] else 0), y0, z1 - .2), 'cladding', floor, 'massing', aid + '-cladding-front', aid)
            for side, xa, xb in (('left', x0 - c, x0), ('right', x1, x1 + c)):
                if edge[side]:
                    rect((xa, y0, zt + .22, xb, y1, z1 - .2), 'cladding', floor, 'massing', aid + f'-cladding-{side}', aid)
            rect((x0 - .18, y0 - .18, z1 - .2, x1 + .18, y1 + .18, z1), 'roof', floor, 'massing', aid + '-lid', aid)
            rect((x0 - .19, y0 - .19, z1 - .21, x1 + .19, y0 - .17, z1 - .19), 'frame', floor, 'massing', owner=aid)
            if edge['front']:
                xc = (x0 + x1) / 2
                rect((xc - .13, y0 - c - .012, zt + .55, xc + .13, y0 - c, z1 - .55), 'blackglass', floor, 'massing', aid + '-slot', aid)
                rect((xc - .16, y0 - c - .02, zt + .52, xc + .16, y0 - c - .012, zt + .55), 'frame', floor, 'massing', owner=aid)
            # Door onto the terrace on the inner face with the most roof in front of it.
            faces = []
            if not edge['right']:
                faces.append((fb[2] - x1, 'right'))
            if not edge['left']:
                faces.append((x0 - fb[0], 'left'))
            if not edge['back']:
                faces.append((fb[3] - y1, 'back'))
            if faces:
                # A side face opens onto the terrace seating; the back (toward the solar array) only as a fallback.
                sides = [q for q in faces if q[1] != 'back' and q[0] >= 2.0]
                _, side = max(sides or faces)
                if side in ('right', 'left'):
                    xf = x1 if side == 'right' else x0
                    s_ = 1 if side == 'right' else -1
                    yc = y0 + min(1.0, (y1 - y0) / 2)
                    rect((min(xf, xf + s_ * .03), yc - .45, zt + .03, max(xf, xf + s_ * .03), yc + .45, zt + 2.15), 'blackglass', floor, 'massing', aid + '-door', aid)
                    rect((min(xf, xf + s_ * .05), yc - .5, zt + 2.15, max(xf, xf + s_ * .05), yc + .5, zt + 2.2), 'frame', floor, 'massing', owner=aid)
                    rect((min(xf, xf + s_ * .09), yc - .05, zt + 2.3, max(xf, xf + s_ * .09), yc + .05, zt + 2.42), 'frame', floor, 'fixture', owner=aid)
                    k.light((xf + s_ * .4, yc, zt + 2.2), 6, kind='wall')
                else:
                    xc = (x0 + x1) / 2
                    rect((xc - .45, y1, zt + .03, xc + .45, y1 + .03, zt + 2.15), 'blackglass', floor, 'massing', aid + '-door', aid)
                    rect((xc - .5, y1, zt + 2.15, xc + .5, y1 + .05, zt + 2.2), 'frame', floor, 'massing', owner=aid)
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

    if rooftop:
        for core in rooftop['cores']:
            x0,y0,x1,y1=[q/1000 for q in core['bounds']];zt=top;z1=top+core['height']/1000;aid=core['id']
            # Keep the established rendered wall, stone and floating-lid vocabulary; the inside remains hollow.
            rect((x0-.18,y0-.18,z1-.2,x1+.18,y1+.18,z1),'roof',storeys,'roof',aid+'-lid',aid)
            rect((x0-.19,y0-.19,z1-.21,x1+.19,y0-.17,z1-.19),'frame',storeys,'massing',owner=aid)
            door=next(o for o in rooftop['openings'] if o['id']==core['doorId'])
            for face in ('front','left','right'):
                wall=next(w for w in rooftop['walls'] if w['id']==core['stairId']+'-roof-wall-'+face)
                if wall['id']==door['wall_id']:continue
                if face=='front':rect((x0,y0-.04,zt+.22,x1,y0,z1-.2),'cladding',storeys,'massing',owner=aid)
                elif face=='left' and x0<.2:rect((x0-.04,y0,zt+.22,x0,y1,z1-.2),'cladding',storeys,'massing',owner=aid)
                elif face=='right' and x1>W-.2:rect((x1,y0,zt+.22,x1+.04,y1,z1-.2),'cladding',storeys,'massing',owner=aid)

    for step in b.get('entrance_steps',[]):
        poly_mesh(Polygon(np.array(step['polygon'])/1000),step['bottom']/1000,step['top']/1000,'step',0,'step',step['id'],step['openingId'])

    # ---------------------------------------------------------------- landscape features
    lawns = list(room_lawns)
    for feature in features:
        fk = feature['kind']
        if 'polygon' in feature:
            poly = Polygon(np.array(feature['polygon'], dtype=float) / 1000)
            if not poly.is_valid:
                poly = poly.buffer(0)
        if fk == 'path':
            slabs = feature.get('material_role') == 'site.flagstone'
            poly_mesh(poly, g - .02, g + .045, 'flagstone', -1, 'court', feature['id'], feature['id']) if slabs else \
                poly_mesh(poly, g + .004, g + .025, 'paver', -1, 'landscape', feature['id'], feature['id'])
        elif fk == 'planting_bed':
            poly_mesh(poly, g + .004, g + .025, 'soil', -1, 'landscape', feature['id'], feature['id'])
            border = poly.buffer(.045).difference(poly)
            poly_mesh(border, g + .025, g + .12, 'stone', -1, 'landscape', feature['id'] + '-raised-edge', feature['id'])
        elif fk == 'court':
            poly_mesh(poly, g - .02, g + .04, 'porch-limestone' if feature.get('material_role')=='site.limestone' else 'cobble', -1, 'court', feature['id'], feature['id'])
        elif fk == 'patio':
            poly_mesh(poly, g - .02, g + .06, 'encaustic', -1, 'patio', feature['id'], feature['id'])
        elif fk == 'deck':
            poly_mesh(poly, g - .02, g + .08, 'deck', -1, 'deck', feature['id'], feature['id'])
        elif fk == 'lawn':
            poly_mesh(poly, g - .03, g + .012, 'lawn', -1, 'lawn', feature['id'], feature['id'])
            lawns.append({'id': feature['id'], 'polygon': [[round(x, 4), round(y, 4)] for x, y in list(poly.exterior.coords)[:-1]],
                          'holes': [[[round(x, 4), round(y, 4)] for x, y in list(r.coords)[:-1]] for r in poly.interiors], 'z': round(g + .012, 4)})
        elif fk == 'pebble_bed':
            pebbles = 'pebbleblack' if feature.get('material_role') == 'site.pebble_black' else 'pebble'
            poly_mesh(poly, g - .02, g + .03, pebbles, -1, 'landscape', feature['id'], feature['id'])
            if feature.get('edging'):
                edge = poly.buffer(.006, join_style=2).difference(poly)
                poly_mesh(edge, g - .02, g + .065, 'steel', -1, 'edging', feature['id'] + '-edging', feature['id'])
        elif fk == 'stepping_stones':
            large = feature.get('material_role') == 'site.paver_large'
            for i, stone in enumerate(feature.get('stones', [])):
                sp = Polygon(np.array(stone, dtype=float) / 1000)
                poly_mesh(sp, g - .01, g + (.06 if large else .055), 'paverlarge' if large else 'steppingstone', -1, 'stone-pad', f"{feature['id']}-{i}", feature['id'])
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
        elif fk == 'fence_cladding':
            # Horizontal timber boards with shadow gaps on the inside face of the side boundary wall, capped in steel.
            fx = feature['x_mm'] / 1000; ya, yb = feature['y0_mm'] / 1000, feature['y1_mm'] / 1000
            into = 1 if feature['side'] == 'left' else -1
            top_z = g + feature.get('height_mm', 1780) / 1000
            # A dark batten backing so the gaps between boards read as shadow lines, not white render.
            # Runs between any gaps left for a breeze-block screen.
            cuts = sorted((a / 1000, b2 / 1000) for a, b2 in feature.get('gaps_mm', []))
            runs, y_ = [], ya
            for a, b2 in cuts:
                if a - y_ > .05:
                    runs.append((y_, a))
                y_ = max(y_, b2)
            if yb - y_ > .05:
                runs.append((y_, yb))
            for ra, rb_ in runs:
                xa, xb = sorted((fx, fx + into * .012))
                rect((xa, ra, g + .2, xb, rb_, top_z), 'steel', -1, 'fence', owner=feature['id'])
                z = g + .22
                while z + .13 <= top_z + .001:
                    xa, xb = sorted((fx + into * .012, fx + into * .034))
                    rect((xa, ra, z, xb, rb_, z + .13), 'timber', -1, 'fence', owner=feature['id'])
                    z += .15
            xa, xb = sorted((fx, fx + into * .05))
            rect((xa, ya, top_z, xb, yb, top_z + .03), 'frame', -1, 'fence', owner=feature['id'])
        elif fk == 'breeze_screen':
            # Off-white breeze blocks (a circle in each square module) over a dark backing, framed in steel.
            fx = feature['x_mm'] / 1000; ya, yb = feature['y0_mm'] / 1000, feature['y1_mm'] / 1000
            za, zb = feature['z0_mm'] / 1000, feature['z1_mm'] / 1000
            into = 1 if feature['side'] == 'left' else -1
            m = feature.get('module_mm', 195) / 1000
            nu, nz = max(1, int((yb - ya) // m)), max(1, int((zb - za) // m))
            u0, z0_ = (ya + yb - nu * m) / 2, za
            face = box(u0, z0_, u0 + nu * m, z0_ + nz * m)
            holes = [Point(u0 + (i + .5) * m, z0_ + (j + .5) * m).buffer(m * .34, 5) for i in range(nu) for j in range(nz)]
            panel = face.difference(unary_union(holes))
            # Extruded in the wall's own (along, up) plane, then stood up against the boundary.
            mesh = extrude(panel, 0, .09)
            mesh.apply_transform(np.array([[0, 0, into, fx + into * .03], [1, 0, 0, 0], [0, 1, 0, g], [0, 0, 0, 1]], dtype=float))
            mesh.fix_normals()
            node(asset(mesh), 'breeze', floor=-1, role='fence', name=feature['id'], owner=feature['id'])
            xa, xb = sorted((fx, fx + into * .03))
            rect((xa, u0, z0_, xb, u0 + nu * m, z0_ + nz * m), 'basalt', -1, 'fence', owner=feature['id'])
            xa, xb = sorted((fx, fx + into * .13))
            for ua, ub in ((u0 - .05, u0), (u0 + nu * m, u0 + nu * m + .05)):
                rect((xa, ua, g, xb, ub, z0_ + nz * m + .04), 'frame', -1, 'fence', owner=feature['id'])
            rect((xa, u0 - .05, z0_ + nz * m, xb, u0 + nu * m + .05, z0_ + nz * m + .04), 'frame', -1, 'fence', owner=feature['id'])
        elif fk == 'water_wall':
            # A stone-clad wall on the rear boundary: a sheet of water falls from a steel lip into a stone trough.
            wx, wy = [q / 1000 for q in feature['position_mm']]
            ww, hh, td = feature['width_mm'] / 1000, feature['height_mm'] / 1000, feature.get('trough_depth_mm', 420) / 1000
            a, c = wx - ww / 2, wx + ww / 2
            fid = feature['id']
            rect((a, wy - .2, g, c, wy, g + hh), 'cladding', -1, 'water-wall', fid, fid)
            rect((a - .02, wy - .23, g + hh, c + .02, wy, g + hh + .04), 'frame', -1, 'water-wall', owner=fid)
            ty0 = wy - .2 - td
            for q in (box(a, ty0, c, ty0 + .06), box(a, ty0, a + .06, wy - .2), box(c - .06, ty0, c, wy - .2)):
                poly_mesh(q, g - .02, g + .45, 'basalt', -1, 'water-wall', owner=fid)
            rect((a + .06, ty0 + .06, g - .02, c - .06, wy - .2, g + .30), 'basalt', -1, 'water-wall', owner=fid)
            rect((a + .06, ty0 + .06, g + .30, c - .06, wy - .2, g + .39), 'water', -1, 'water', fid + '-pool', fid)
            lip = wy - .31
            rect((a + .25, lip, g + 1.22, c - .25, wy - .2, g + 1.25), 'steel', -1, 'water-wall', owner=fid)
            rect((a + .27, lip - .004, g + .39, c - .27, lip + .004, g + 1.22), 'waterfall', -1, 'water', fid + '-fall', fid)
            rect((a + .3, lip + .01, g + 1.212, c - .3, wy - .21, g + 1.22), 'lamp', -1, 'fixture', owner=fid)
            k.light((wx, lip - .3, g + .5), 12, kind='uplight')
            k.obstacle(box(a, ty0, c, wy), -1, fid)
        elif fk == 'garden_basin':
            # A stone basin on a plinth with a brass tap from the boundary wall, for washing up after the garden.
            x, y = [q / 1000 for q in feature['position_mm']]
            into = 1 if feature.get('side') == 'left' else -1
            fid = feature['id']
            rect((x - .17, y - .15, g, x + .17, y + .15, g + .74), 'cladding', -1, 'garden-basin', fid, fid)
            rb((x, y, g + .8), (.5, .4, .12), 'counter', -1, 'garden-basin', .05, owner=fid)
            tap = x - into * .3
            beam((tap, y, g + 1.02), (x - into * .06, y, g + 1.02), .012, 'brass', -1, 'detail')
            beam((x - into * .06, y, g + 1.02), (x - into * .06, y, g + .95), .01, 'brass', -1, 'detail')
            k.obstacle(box(x - .25, y - .2, x + .25, y + .2), -1, fid)
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
    if v['pooja'] and not any(s['kind'] == 'pooja' for s in b['spaces']):
        # An explicitly labelled niche in the 2D schedule, not an invented room.
        xx = W - .65; yy = b['brief']['floor_height_mm'] / 1000 + .3
        rect((xx - .27, yy - .13, .5, xx + .27, yy + .13, 1.0), M['casework'], 0, 'furniture', 'pooja-niche')
        rect((xx - .25, yy - .12, 1.03, xx + .25, yy + .12, 1.07), M['counter'], 0, 'furniture')
        cylinder((xx, yy, 1.17), .06, .18, 'brass', 0, 'detail')

    # ---------------------------------------------------------------- lawns for legacy themes
    if not lawns and b.get('planning',{}).get('frontCourt')!='tiled':
        inner = plot.buffer(-.2)
        taken = unary_union([fp.buffer(.25)] + [q.buffer(.05) for q in k.ground]) if k.ground else fp.buffer(.25)
        for i, part in enumerate(_parts(inner.difference(taken))):
            if part.area > 1.2:
                lawns.append({'id': f'lawn-{i}', 'polygon': [[round(x, 4), round(y, 4)] for x, y in list(part.exterior.coords)[:-1]],
                              'holes': [[[round(x, 4), round(y, 4)] for x, y in list(r.coords)[:-1]] for r in part.interiors], 'z': round(g - .04, 4)})

    # ---------------------------------------------------------------- walk + rooms metadata
    rooms = [{'id': s['id'], 'name': s['name'], 'kind': s['kind'], 'floor': s['floor'],
              'holes': [[[round(x / 1000, 4), round(y / 1000, 4)] for x,y in ring] for ring in s.get('holes',[])],
              'polygon': [[round(x / 1000, 4), round(y / 1000, 4)] for x, y in s['clear']]} for s in rb_model['spaces']]
    # The walk starts on the street outside the open pedestrian gate, facing the house, so the visitor arrives the
    # way a guest does (the vehicle gate beside it stays closed).
    arrive_x = ex
    if boundary and (modern or boundary.get('gates')):
        # Through the pedestrian gate (the arrival gateway the boundary record names).
        gate_c, gate_w = boundary.get('gate_center_mm', ex * 1000) / 1000, boundary.get('gate_width_mm', 2600) / 1000
        slack = max(0., gate_w / 2 - .45)
        arrive_x = min(max(ex, gate_c - slack), gate_c + slack)
    walk = {'eye_height': 1.63, 'arrival': {'position': [round(arrive_x, 3), round(ymin - 1.3, 3), round(g + (.1 if modern else 0), 3)], 'yaw_deg': 0}, 'floors': []}
    for f in range(storeys):
        options = [s for s in b['spaces'] if s['floor'] == f and s['kind'] in ('living', 'drawing-room', 'family', 'dining', 'hall')]
        if not options:
            continue
        s = options[0]
        c = Polygon(np.array(s['clear']) / 1000).representative_point()
        walk['floors'].append({'floor': f, 'position': [round(c.x, 3), round(c.y, 3), round(f * H, 3)], 'yaw_deg': 180 if f else 0})

    car = b.get('planning', {}).get('parkedCar')
    if car:
        from .vehicle import parked_car
        parked_car(k, materials, car['x']/1000, car['y']/1000, g+.04)

    if b.get('planning',{}).get('facadeStyle')=='warm-layered':
        from .upper_floor_finishes import upper_floor_finishes
        upper_floor_finishes(k,b,H)

    # Exact generated scene, not an image substitute.
    scene = {'editables': k.editables, 'input_audit':b.get('input_audit'),'planHash':b.get('planHash'),'draftRevision':b.get('draftRevision',0),'schema': 'floorforge.scene/0.4', 'units': 'm', 'up': 'Z', 'materials': materials, 'assets': k.assets, 'nodes': k.nodes,
            'lights': lights, 'colliders': colliders, 'furniture': furniture, 'floor_height': H, 'storeys': storeys, 'roof_level': storeys if rooftop else None,
            'bounds': [xmin, ymin, -plinth, xmax, ymax, top + (2.7 if rooftop else .7)], 'footprint': (np.array(b['footprint']) / 1000).tolist(),
            'entry': [float(ex), -.15, 1.6], 'solar': report['solar'], 'style': v['style'],
            'exterior_theme': theme_id, 'interior_theme': interior_id,
            'exterior_revision': exterior.get('revision'), 'exterior_review': exterior.get('review', {}),
            'vegetation': k.vegetation, 'lawns': lawns, 'rooms': rooms, 'walk': walk,
            # Canonical opening hosts let the offline viewer animate the actual authored leaves.
            # These descriptors do not alter the exported design's initial geometry or plan hash.
            'opening_model': {'openings': rb_model['openings'], 'walls': rb_model['walls']},
            'gate_model': gates,
            'door_motion': door_motion,
            'cameras': {'hero': {'position': [W * 1.90, -max(16, D * 1.34), top * .68 + 3.0], 'target': [W * .47, D * .25, top * .40], 'fov': 43},
                        'dollhouse': {'position': [W * 1.45, -D * .52, top + max(W, D) * 1.55], 'target': [W * .5, D * .5, 1.], 'fov': 42},
                        'interior': {'position': [ex, .65, 1.6], 'target': [W * .72, 4.0, 1.35], 'fov': 66}},
            'quality': 'Authored procedural geometry with physically based surface recipes and procedural planting; not a verified photographic render.',
            'banner': b['banner']}
    from .placement_edits import apply_furniture_edits
    return apply_furniture_edits(scene, b)


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
    out.metadata = {'planHash':scene.get('planHash'),'draftRevision':scene.get('draftRevision',0),'banner': scene['banner'], 'units': 'm', 'up': 'Y', 'geometry_scope': 'individual closed components plus thin decorative surfaces; not a boolean-unioned building'}
    return out.export(file_type='glb')
