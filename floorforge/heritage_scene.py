"""Heritage Bungalow scene geometry (metres, Z up), used only by plans with the heritage-bungalow facade style.

The shared scene builder calls into this module at a few hook points; every other scene keeps its exact
geometry. Assemblies come from heritage_bungalow.py (plan millimetres) and are drawn here with the same
Kit, so the live viewer, GLB, drawings and IFC furniture meshes all share one model.
"""
from __future__ import annotations

import math

import numpy as np
import trimesh
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely import get_parts

from .heritage_bungalow import WALL_PAINTS
from .plan_geometry import geometry, roof, floor_outline
from .scene_kit import extrude
from .spaces import OUTDOOR

WET = ('bathroom', 'powder-room', 'utility', 'drying-room')

RED = '#c4323d'


def heritage_materials(materials: dict, M: dict) -> None:
    """Period palette. Only the heritage scene's own material table is changed."""
    materials.update({
        # Blush lime render outside; rooms are painted over it with their own distemper linings.
        'wall': {'color': '#ece0d5', 'roughness': .9, 'texture': 'plaster', 'kind': 'render', 'seed': 23},
        'roof': {'color': '#a9a49a', 'roughness': .86, 'texture': 'concrete', 'kind': 'concrete', 'seed': 27},
        'ceiling': {'color': '#f7f4ee', 'roughness': .93, 'texture': 'plaster', 'kind': 'render', 'seed': 2},
        # Teak joinery replaces the walnut and oak of the modern recipes in this scene only.
        'walnut': {'color': '#5c3920', 'roughness': .5, 'texture': 'wood', 'kind': 'wood', 'seed': 13},
        'oak': {'color': '#8d5d35', 'roughness': .5, 'texture': 'wood', 'kind': 'wood', 'seed': 17},
        'fabric': {'color': '#7d2f2b', 'roughness': .97, 'texture': 'fabric', 'kind': 'fabric', 'params': [70]},
        'fabric-dark': {'color': '#2c3a63', 'roughness': .95, 'texture': 'fabric', 'kind': 'fabric', 'seed': 3, 'params': [70]},
        'linen': {'color': '#efe6d3', 'roughness': .98, 'texture': 'fabric', 'kind': 'fabric', 'seed': 5, 'params': [160]},
        'rug': {'color': '#8f2f2a', 'alt': '#24365c', 'roughness': .98, 'texture': 'fabric', 'kind': 'rug', 'seed': 4},
        'frame': {'color': '#3d4840', 'roughness': .4, 'metallic': .35, 'kind': 'metal', 'params': [.4]},
        'skirting': {'color': '#e6dfd1', 'roughness': .35, 'kind': 'metal', 'params': [.3]},
        'hb-stripe': {'color': RED, 'roughness': .62, 'texture': 'plaster', 'kind': 'render', 'seed': 31},
        'hb-pillar': {'color': '#c14a3d', 'roughness': .78, 'texture': 'plaster', 'kind': 'render', 'seed': 33},
        'hb-boundary': {'color': '#e4b9aa', 'roughness': .9, 'texture': 'plaster', 'kind': 'render', 'seed': 35},
        'hb-plinth': {'color': '#8a3a2f', 'roughness': .7, 'texture': 'plaster', 'kind': 'render', 'seed': 37},
        'hb-grille': {'color': '#e5e0d2', 'roughness': .42, 'metallic': .3, 'kind': 'metal', 'params': [.42]},
        'hb-grille-dark': {'color': '#2d3530', 'roughness': .45, 'metallic': .35, 'kind': 'metal', 'params': [.45]},
        'hb-steel-window': {'color': '#3b4a42', 'roughness': .4, 'metallic': .35, 'kind': 'metal', 'params': [.4]},
        'hb-glass': {'color': '#a9c5bf', 'roughness': .1, 'alpha': .3, 'metallic': .1},
        'hb-chajja': {'color': '#5f4635', 'roughness': .72, 'metallic': .4, 'kind': 'metal', 'params': [.7]},
        'hb-corrugated': {'color': '#3e4243', 'alt': '#5d6061', 'roughness': .6, 'metallic': .45, 'kind': 'corrugated', 'tile_m': .76, 'normal': .4},
        'hb-sheet-light': {'color': '#d4d6d2', 'alt': '#b9bcb8', 'roughness': .45, 'metallic': .5, 'kind': 'corrugated', 'tile_m': .76, 'seed': 3, 'normal': .4},
        'hb-post-red': {'color': '#b5312b', 'roughness': .4, 'metallic': .3, 'kind': 'metal', 'params': [.38]},
        'hb-post-black': {'color': '#1c1e1f', 'roughness': .45, 'metallic': .3, 'kind': 'metal', 'params': [.42]},
        'hb-white-steel': {'color': '#ecebe5', 'roughness': .4, 'metallic': .25, 'kind': 'metal', 'params': [.4]},
        'hb-chick': {'color': '#b99d68', 'alt': '#6f5a37', 'roughness': .85, 'kind': 'chick', 'tile_m': .9},
        'hb-bamboo': {'color': '#a98b57', 'roughness': .6, 'texture': 'wood', 'kind': 'wood', 'seed': 41},
        'hb-net': {'color': '#2f9a58', 'roughness': .9, 'alpha': .82, 'kind': 'shade-net', 'spacing': .006, 'wire': .0042},
        'hb-net-frame': {'color': '#2e5a3a', 'roughness': .45, 'metallic': .3, 'kind': 'metal', 'params': [.45]},
        'hb-wire-mesh': {'color': '#3a3d39', 'roughness': .6, 'alpha': .2, 'kind': 'insect-mesh', 'spacing': .05, 'wire': .0035},
        'hb-fly-mesh': {'color': '#3d423e', 'roughness': .85, 'alpha': .5, 'kind': 'insect-mesh', 'spacing': .006, 'wire': .0013},
        'hb-hex': {'color': '#a05b4e', 'alt': '#8a4c43', 'roughness': .8, 'kind': 'hexpaver', 'tile_m': [1.0, .866]},
        'hb-hex-yellow': {'color': '#d9c35e', 'alt': '#c4a94a', 'roughness': .74, 'kind': 'hexpaver', 'tile_m': [1.0, .866], 'seed': 5},
        'hb-brick': {'color': '#9c4a36', 'alt': '#7e3a2b', 'roughness': .86, 'texture': 'stone', 'kind': 'stone', 'seed': 43},
        'hb-laterite': {'color': '#8d4c34', 'alt': '#6c3a28', 'roughness': .9, 'texture': 'stone', 'kind': 'stone', 'seed': 45},
        'hb-kerb': {'color': '#9b3b33', 'roughness': .8, 'texture': 'plaster', 'kind': 'render', 'seed': 47},
        'hb-murram': {'color': '#9b5a3b', 'alt': '#5f3524', 'roughness': 1., 'texture': 'stone', 'kind': 'soil', 'params': [40, 0, 0, 0]},
        'hb-pot-red': {'color': '#a9392f', 'roughness': .55},
        'hb-pot-pink': {'color': '#d7687c', 'roughness': .5},
        'hb-pot-yellow': {'color': '#e2c34c', 'roughness': .5},
        'hb-limewash': {'color': '#f1efe8', 'roughness': .95, 'texture': 'plaster', 'kind': 'render', 'seed': 49},
        'hb-tank': {'color': '#ecebe4', 'roughness': .5},
        'hb-pvc': {'color': '#e8e5dc', 'roughness': .4},
        'hb-plastic': {'color': '#efeee8', 'roughness': .42},
        'hb-cooler': {'color': '#a3977c', 'roughness': .55, 'metallic': .35, 'kind': 'metal', 'params': [.55]},
        'hb-khus': {'color': '#8c6a3d', 'alt': '#5f4626', 'roughness': .98, 'texture': 'fabric', 'kind': 'fabric', 'params': [40], 'seed': 7},
        'hb-kota': {'color': '#6d7b74', 'alt': '#5b6862', 'roughness': .55, 'texture': 'tile', 'kind': 'tile', 'params': [2, .004, .1, .45], 'tile_m': 1.2},
        'hb-roof-tiles': {'color': '#a5604a', 'alt': '#8a4d3b', 'roughness': .82, 'texture': 'tile', 'kind': 'tile', 'params': [4, .012, 0, .1], 'tile_m': 1.2},
        'hb-globe': {'color': '#fff4dd', 'roughness': .25, 'emission': .9},
        'hb-plate': {'color': '#16191a', 'roughness': .3},
        'hb-plate-text': {'color': '#e9e6dc', 'roughness': .5},
        'hb-sign-yellow': {'color': '#e8c21e', 'roughness': .45},
        'hb-hose': {'color': '#e2cf9b', 'roughness': .5},
        'hb-rope': {'color': '#d9d3c4', 'roughness': .9},
        'hb-teak': {'color': '#7b4c2a', 'roughness': .48, 'texture': 'wood', 'kind': 'wood', 'seed': 51},
        'hb-teak-dark': {'color': '#4e2f1a', 'roughness': .45, 'texture': 'wood', 'kind': 'wood', 'seed': 53},
        'hb-cane': {'color': '#c8a96d', 'alt': '#a88a52', 'roughness': .7, 'texture': 'fabric', 'kind': 'fabric', 'params': [36], 'seed': 55},
        'hb-granite': {'color': '#29282a', 'alt': '#77736d', 'roughness': .18, 'texture': 'stone', 'kind': 'terrazzo', 'clearcoat': .4, 'seed': 57},
        'hb-steel': {'color': '#c3c6c6', 'roughness': .25, 'metallic': .9, 'kind': 'brushed', 'params': [.25]},
        'hb-almirah': {'color': '#8a8e7e', 'roughness': .38, 'metallic': .45, 'kind': 'metal', 'params': [.35]},
        'hb-brass': {'color': '#c09a52', 'roughness': .26, 'metallic': .85, 'kind': 'brushed', 'params': [.25]},
        'hb-fan': {'color': '#e8e3d6', 'roughness': .38, 'metallic': .2},
        'hb-fan-brown': {'color': '#5a3f2c', 'roughness': .35, 'metallic': .25},
        'hb-tube': {'color': '#f4f8fb', 'roughness': .3, 'emission': .8, 'lumen_scale': 7},
        'hb-mirror': {'color': '#e2e8ea', 'roughness': .03, 'metallic': 1.},
        'hb-leather': {'color': '#2f4a35', 'roughness': .5, 'kind': 'leather'},
        'hb-carpet': {'color': '#8d2a2a', 'alt': '#1f335a', 'roughness': .99, 'texture': 'fabric', 'kind': 'rug', 'seed': 9},
        'hb-durrie': {'color': '#c25a33', 'alt': '#2b4f7a', 'roughness': .99, 'texture': 'fabric', 'kind': 'rug', 'seed': 11},
        'hb-print': {'color': '#c9a046', 'alt': '#7a2f2a', 'roughness': .97, 'texture': 'fabric', 'kind': 'fabric', 'params': [50], 'seed': 13},
        'hb-curtain': {'color': '#b9844a', 'alt': '#7b3b2a', 'roughness': .97, 'texture': 'fabric', 'kind': 'fabric', 'params': [90], 'seed': 15},
    })
    for name, color in WALL_PAINTS.items():
        materials['paint-' + name] = {'color': color, 'roughness': .93, 'texture': 'plaster', 'kind': 'render', 'seed': 61}
    # Floors: ivory vitrified tiles (600 mm), white marble with veining, white ceramic (300 mm),
    # polished red oxide, Kota stone and terrazzo mosaic.
    materials.update({
        'floor-ivory-vitrified': {'color': '#e6ddcd', 'alt': '#d4c7b1', 'roughness': .25, 'texture': 'tile', 'kind': 'tile',
                                  'tile_m': 1.2, 'params': [2, .004, .05, .7], 'normal': .35, 'clearcoat': .18, 'clearcoat_roughness': .2},
        'floor-white-marble': {'color': '#eeebe5', 'alt': '#b4b2ad', 'roughness': .14, 'texture': 'tile', 'kind': 'tile',
                               'tile_m': 1.8, 'params': [3, .002, .6, .9], 'normal': .25, 'clearcoat': .35, 'clearcoat_roughness': .1},
        'floor-marble-border': {'color': '#2b2320', 'alt': '#6a5546', 'roughness': .22, 'texture': 'stone', 'kind': 'marble', 'clearcoat': .12},
        'floor-ceramic-white': {'color': '#ece9e1', 'alt': '#c9c4b9', 'roughness': .3, 'texture': 'tile', 'kind': 'tile',
                                'tile_m': 1.2, 'params': [4, .008, 0, .65], 'normal': .6, 'clearcoat': .1},
        'floor-red-oxide': {'color': '#8f3328', 'roughness': .24, 'texture': 'concrete', 'kind': 'concrete', 'seed': 63,
                            'clearcoat': .3, 'clearcoat_roughness': .18, 'tile_m': 3.0},
        'floor-kota-stone': {'color': '#71807a', 'alt': '#5d6b66', 'roughness': .35, 'texture': 'tile', 'kind': 'tile',
                             'tile_m': 1.2, 'params': [2, .003, .15, .55], 'normal': .4, 'clearcoat': .12},
        'floor-mosaic': {'color': '#d8cdb8', 'alt': '#7a6250', 'roughness': .32, 'texture': 'stone', 'kind': 'terrazzo',
                         'clearcoat': .08, 'clearcoat_roughness': .3, 'tile_m': .8},
    })
    M.update(table='hb-teak', legs='hb-teak', bedframe='hb-teak', casework='hb-teak', fronts='hb-teak',
             counter='hb-granite', tread='floor-mosaic', door='hb-teak', doorframe='hb-teak-dark')


# ------------------------------------------------------------------------------------------------ geometry helpers
def brick_grille(w, h, course=.15, brick=.30, bar=.018, frame=.032):
    """A steel grille in running (brick) bond: flat bars on every course, staggered uprights (u, v metres)."""
    parts = [box(0, 0, w, frame), box(0, h - frame, w, h), box(0, 0, frame, h), box(w - frame, 0, w, h)]
    rows = max(1, round((h - 2 * frame) / course))
    step = (h - 2 * frame) / rows
    for r in range(rows):
        v0 = frame + r * step
        if r:
            parts.append(box(0, v0 - bar / 2, w, v0 + bar / 2))
        u = (brick / 2 if r % 2 else brick) + frame * .5
        while u < w - frame - .03:
            parts.append(box(u - bar / 2, v0, u + bar / 2, v0 + step))
            u += brick
    return unary_union(parts)


def panel(k, poly, thickness, mat, origin, along, floor, role, owner=None, name=None):
    """Stand a 2-D (u along, v up) panel in a vertical plane: shared mesh, placed by the node transform."""
    mesh = extrude(poly, -thickness / 2, thickness / 2)
    theta = math.atan2(along[1], along[0])
    return k.node(k.asset(mesh), mat, origin, rot=(math.pi / 2, 0, theta), floor=floor, role=role, name=name, owner=owner)


def sloped(k, poly, z_at, thickness, mat, floor, role, owner=None, name=None):
    """A thin plan polygon whose height follows z_at(x, y) (sheet roofs and sunshades)."""
    mesh = extrude(poly, -thickness, 0)
    mesh.vertices[:, 2] += np.array([z_at(x, y) for x, y in mesh.vertices[:, :2]])
    mesh.fix_normals()
    return k.node(k.asset(mesh), mat, floor=floor, role=role, name=name, owner=owner)


def corrugated(k, x0, y0, x1, y1, z_at, mat, floor, role, owner=None, name=None, pitch=.076, amp=.017):
    """A corrugated sheet as real geometry: flutes running along x, a sine profile across y, both faces shown."""
    n = max(2, int(round((y1 - y0) / pitch * 4)))
    ys = np.linspace(y0, y1, n + 1)
    verts, faces = [], []
    for y in ys:
        dz = amp * math.sin((y - y0) / pitch * 2 * math.pi)
        verts += [(x0, y, z_at(x0, y) + dz), (x1, y, z_at(x1, y) + dz)]
    for i in range(n):
        a = 2 * i
        faces += [[a, a + 1, a + 3], [a, a + 3, a + 2]]
    mesh = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=False)
    return k.node(k.asset(mesh, smooth=True), mat, floor=floor, role=role, name=name, owner=owner)


def _lines(geom):
    out = []
    for g in get_parts(geom):
        if g.geom_type == 'LineString' and g.length > .05:
            out.append(g)
        elif g.geom_type == 'MultiLineString':
            out.extend(p for p in g.geoms if p.length > .05)
    return out


def _segments(lines):
    for line in lines:
        pts = list(line.coords)
        for a, b in zip(pts, pts[1:]):
            if math.dist(a, b) > .05:
                yield np.array(a), np.array(b)


class HeritageScene:
    """Exterior builders. `ctx` carries the scene's shared values (kit, building, heights, plot)."""

    def __init__(self, k, b, materials, M, H, g, plot, fp, metres, hosts, guards):
        self.k, self.b, self.materials, self.M, self.H, self.g = k, b, materials, M, H, g
        self.plot, self.fp, self.metres, self.hosts, self.guards = plot, fp, metres, hosts, guards
        self.storeys = b['storeys']
        self.exterior = b.get('exterior', {})
        self.landscape = self.exterior.get('landscape', {}) or {}
        self.boundary = self.landscape.get('boundary', {}) or {}
        self.gates = []

    # ------------------------------------------------------------------------------------------- street & boundary
    def site(self):
        k, g = self.k, self.g
        xmin, ymin, xmax, ymax = self.plot.bounds
        # A quiet colony road: worn asphalt between red murram shoulders, no kerb or footpath.
        k.rect((xmin - 9, ymin - 9.6, g - .07, xmax + 9, ymin - 2.9, g - .012), 'asphalt', role='site')
        k.rect((xmin - 9, ymin - 2.9, g - .06, xmax + 9, ymin - .02, g - .004), 'hb-murram', role='site')
        k.rect((xmin - 9, ymin - 10.9, g - .06, xmax + 9, ymin - 9.6, g - .004), 'hb-murram', role='site')
        wt = self.boundary.get('wall_thickness_mm', 230) / 1000
        wall_h = self.boundary.get('side_wall_height_mm', 900) / 1000
        net_h = self.boundary.get('net_height_mm', 2050) / 1000
        piers = [(p['x0_mm'] / 1000, p['x1_mm'] / 1000) for p in self.boundary.get('pillars', [])]
        gaps = sorted([(gt['x0_mm'] / 1000, gt['x1_mm'] / 1000) for gt in self.boundary.get('gates', [])] + piers)
        runs = []
        x = xmin
        for a, c in gaps:
            if a - x > .05:
                runs.append(('front', LineString([(x, ymin + wt / 2), (a, ymin + wt / 2)])))
            x = max(x, c)
        if xmax - x > .05:
            runs.append(('front', LineString([(x, ymin + wt / 2), (xmax, ymin + wt / 2)])))
        runs += [('left', LineString([(xmin + wt / 2, ymin + wt), (xmin + wt / 2, ymax - wt)])),
                 ('right', LineString([(xmax - wt / 2, ymin + wt), (xmax - wt / 2, ymax - wt)])),
                 ('rear', LineString([(xmin, ymax - wt / 2), (xmax, ymax - wt / 2)]))]
        for i, (side, line) in enumerate(runs):
            base = line.buffer(wt / 2, cap_style=2)
            k.poly_mesh(base, g, g + wall_h, 'hb-boundary', -1, 'site', f'heritage-boundary-{side}-{i}', 'heritage-boundary')
            k.poly_mesh(line.buffer(wt / 2 + .025, cap_style=2), g + wall_h, g + wall_h + .06, 'hb-stripe', -1, 'site', owner='heritage-boundary')
            # Shade net on a light steel frame above the wall: posts, top rail and the knitted net.
            (ax, ay), (bx, by) = line.coords
            L = line.length
            u = ((bx - ax) / L, (by - ay) / L)
            n = max(1, round(L / 2.4))
            for j in range(n + 1):
                px, py = ax + u[0] * L * j / n, ay + u[1] * L * j / n
                k.rect((px - .02, py - .02, g + wall_h + .06, px + .02, py + .02, g + net_h), 'hb-net-frame', -1, 'fence', owner='heritage-boundary')
            k.poly_mesh(line.buffer(.018, cap_style=2), g + net_h - .03, g + net_h, 'hb-net-frame', -1, 'fence', owner='heritage-boundary')
            panel(k, box(0, 0, L, net_h - wall_h - .1), .003, 'hb-net', (ax, ay, g + wall_h + .07), u, -1, 'fence', 'heritage-boundary')
        car = [(gt['x0_mm'] / 1000, gt['x1_mm'] / 1000) for gt in self.boundary.get('gates', []) if gt['kind'] == 'vehicle']
        for x0, x1 in piers:
            # Red piers frame the pedestrian gate; the car gate hangs between piers in the wall's own blush.
            light = any(abs(x1 - a) < .01 or abs(x0 - c) < .01 for a, c in car)
            self.pillar(x0, x1, ymin, wt, 'hb-boundary' if light else 'hb-pillar')
        lb = self.boundary.get('letterbox_pier')
        if lb:
            self.name_plate(lb['x0_mm'] / 1000, lb['x1_mm'] / 1000, ymin, wt)
        for gate in self.boundary.get('gates', []):
            self.gate(gate, ymin, wt)

    def pillar(self, x0, x1, ymin, wt, mat='hb-pillar'):
        k, g = self.k, self.g
        cy = ymin + wt / 2
        half = (x1 - x0) / 2
        cx = (x0 + x1) / 2
        own = f'heritage-pillar-{cx:.2f}'
        top = g + 1.95
        k.rect((x0, cy - half, g, x1, cy + half, top), mat, -1, 'site', own, own)
        k.rect((x0 - .04, cy - half - .04, top, x1 + .04, cy + half + .04, top + .08), 'hb-boundary', -1, 'site', owner=own)
        k.rect((x0 - .02, cy - half - .02, g, x1 + .02, cy + half + .02, g + .15), 'hb-plinth', -1, 'site', owner=own)
        # The white "mushroom" globe lamp of colony gateposts.
        k.cylinder((cx, cy, top + .12), .05, .1, 'hb-white-steel', -1, 'fixture')
        k.ball((cx, cy, top + .27), (.19, .19, .15), 'hb-globe', -1, 'fixture')
        k.cylinder((cx, cy, top + .17), .13, .03, 'hb-white-steel', -1, 'fixture')
        k.light((cx, cy - .3, top + .3), 9, kind='pillar')
        self.k.obstacle(box(x0, cy - half, x1, cy + half), -1, own)

    def name_plate(self, x0, x1, ymin, wt):
        k, g = self.k, self.g
        cx = (x0 + x1) / 2
        face = ymin + wt / 2 - (x1 - x0) / 2 - .006
        k.rect((cx - .2, face - .01, g + 1.42, cx + .2, face, g + 1.66), 'hb-plate', -1, 'detail', 'heritage-name-plate', 'heritage-name-plate')
        for j, (w_, z) in enumerate(((.3, 1.6), (.22, 1.55), (.26, 1.5), (.16, 1.46))):
            k.rect((cx - w_ / 2, face - .012, g + z - .012, cx + w_ / 2, face - .01, g + z), 'hb-plate-text', -1, 'detail', owner='heritage-name-plate')
        k.cylinder((cx, face - .006, g + 1.18), .11, .012, 'hb-sign-yellow', -1, 'detail', rot=(math.pi / 2, 0, 0))

    def gate(self, gate, ymin, wt):
        k, g = self.k, self.g
        x0, x1 = gate['x0_mm'] / 1000, gate['x1_mm'] / 1000
        hgt = 1.78
        gy = ymin + wt / 2
        k.rect((x0, ymin - .02, g - .02, x1, ymin + wt + .02, g + .03), 'hb-kota', -1, 'gate', owner='heritage-gate-sill')
        leaves = [(x0 + .02, x1 - .02, 'left' if gate.get('hinge', 'left') == 'left' else 'right')] if gate['kind'] == 'pedestrian' else \
            [(x0 + .02, (x0 + x1) / 2 - .01, 'left'), ((x0 + x1) / 2 + .01, x1 - .02, 'right')]
        owner = 'exterior-' + gate['kind'] + '-gate'
        parts = []
        for a, c, hinge in leaves:
            L = c - a
            grid = brick_grille(L, hgt, course=.2, brick=.42, bar=.028, frame=.045)
            mark = len(k.nodes)
            open_deg = 0 if gate['kind'] == 'vehicle' else gate.get('open_deg', 78)
            ang = math.radians(open_deg) * (1 if hinge == 'left' else -1)
            hx = a if hinge == 'left' else c
            # Leaf direction from the hinge, swung into the plot (+y) when open.
            d = (math.cos(ang), math.sin(ang)) if hinge == 'left' else (-math.cos(ang), math.sin(ang))
            origin = (hx, gy, g + .06) if hinge == 'left' else (hx + d[0] * L, gy + d[1] * L, g + .06)
            along = d if hinge == 'left' else (-d[0], -d[1])
            # The pedestrian gate is dark steel; the car gate is painted white (both backed by shade net).
            panel(k, grid, .03, 'hb-white-steel' if gate['kind'] == 'vehicle' else 'hb-grille-dark', origin, along, -1, 'gate', owner, owner if not parts else None)
            panel(k, box(.045, .045, L - .045, hgt - .045), .002, 'hb-net', (origin[0] + along[1] * .02, origin[1] - along[0] * .02, origin[2]), along, -1, 'gate', owner)
            parts.append({'ids': [n['id'] for n in k.nodes[mark:]], 'pivot': [hx, gy, g], 'angle': (math.pi / 2 if hinge == 'left' else -math.pi / 2)})
        if gate['kind'] == 'vehicle':
            self.gates.append({'id': owner, 'label': 'Main car gate', 'floor': -1, 'kind': 'gate', 'start': [x0, gy, g], 'axis': [1, 0, 0],
                               'width': x1 - x0, 'height': hgt + .06, 'base': g, 'sill': 0, 'initial': 0, 'parts': parts})

    # ------------------------------------------------------------------------------------------------ parapets
    def frieze(self, lines, inside, z, height, floor, owner, stripe_len=None):
        """A parapet with the red comb frieze: a raised coping band and stripes hanging from it on the outer face."""
        k = self.k
        if not lines:
            return
        body = unary_union([l.buffer(.23, cap_style=2, join_style=2) for l in lines]).intersection(inside)
        if body.is_empty:
            return
        k.poly_mesh(body, z, z + height - .11, 'wall', floor, 'parapet', owner=owner)
        band = unary_union([l.buffer(.255, cap_style=2, join_style=2) for l in lines]).intersection(inside.buffer(.026, join_style=2))
        k.poly_mesh(band, z + height - .11, z + height, 'hb-stripe', floor, 'coping', owner=owner)
        length = stripe_len or min(.62, height * .58)
        stripes = []
        for a, c in _segments(lines):
            L = float(np.linalg.norm(c - a))
            u = (c - a) / L
            nrm = np.array([-u[1], u[0]])
            mid = (a + c) / 2
            if inside.buffer(-.001).contains(Point(*(mid + nrm * .05))):
                nrm = -nrm
            count = max(1, int((L - .3) / .27))
            ts = np.linspace(.15, L - .15, count + 1) if L > .5 else [L / 2]
            for j, t in enumerate(ts):
                w = .17 if j in (0, len(ts) - 1) else .095
                q = a + u * t
                stripes.append(Polygon([q - u * w / 2, q + u * w / 2, q + u * w / 2 + nrm * .016, q - u * w / 2 + nrm * .016]))
        if stripes:
            k.poly_mesh(unary_union(stripes), z + height - .11 - length, z + height - .11, 'hb-stripe', floor, 'coping', owner=owner)

    def roof_parapets(self):
        """Every exposed roof edge carries the frieze; accessible terraces get theirs from their guard lines."""
        b, k, H = self.b, self.k, self.H
        rooftop = b.get('rooftop')
        for f in range(self.storeys):
            if rooftop and f == self.storeys - 1:
                continue
            field = self.metres(roof(b, f))
            if field.is_empty:
                continue
            outline = self.metres(floor_outline(b, f))
            edges = _lines(field.boundary.intersection(outline.boundary.buffer(.01)))
            z = (f + 1) * H
            self.frieze(edges, field, z, .78, f, f'heritage-parapet-{f}')
            inner = field.buffer(-.23, join_style=2)
            k.poly_mesh(inner, z, z + .03, 'roof', f, 'roof', f'heritage-roof-finish-{f}')
            self.khurras(edges, field, z, f)
        if rooftop:
            terrace = self.metres(geometry(rooftop['terrace']))
            k.poly_mesh(terrace.buffer(-.23, join_style=2), self.storeys * H, self.storeys * H + .03, 'hb-roof-tiles', self.storeys, 'roof', 'heritage-roof-terrace-tiles')

    def khurras(self, edges, field, z, floor):
        """Rain-water spouts through the parapet at intervals."""
        for i, (a, c) in enumerate(_segments(edges)):
            L = float(np.linalg.norm(c - a))
            if L < 3:
                continue
            u = (c - a) / L
            nrm = np.array([-u[1], u[0]])
            if field.buffer(-.001).contains(Point(*((a + c) / 2 + nrm * .05))):
                nrm = -nrm
            q = (a + c) / 2 + nrm * .12
            self.k.beam((q[0] - nrm[0] * .2, q[1] - nrm[1] * .2, z + .05), (q[0] + nrm[0] * .12, q[1] + nrm[1] * .12, z + .02), .035, 'hb-pvc', floor, 'pipe')

    def guard(self, guard, space, colliders):
        """Terrace and roof guards become rendered parapets with the frieze; stair-well guards a teak balustrade."""
        k, H = self.k, self.H
        f = guard['floor']
        z = f * H
        edge = LineString(np.array(guard['points']) / 1000)
        owner = guard['owner']
        if space.get('kind') == 'terrace' or owner == 'roof-terrace':
            if space:
                poly = Polygon(np.array(space['polygon']) / 1000, [np.array(h) / 1000 for h in space.get('holes', [])])
            else:
                poly = self.metres(geometry(self.b['rooftop']['terrace']))
            inside = poly.buffer(.001, join_style=2)
            self.frieze([edge], inside, z, 1.08, f, guard['id'], .6)
            body = edge.buffer(.23, cap_style=2, join_style=2).intersection(inside)
            for part in get_parts(body):
                if part.geom_type == 'Polygon' and part.area > 1e-3:
                    colliders.append({'id': guard['id'], 'floor': f, 'polygon': list(part.exterior.coords), 'kind': 'guard'})
            return
        self.balustrade(edge, z, f, guard['id'], owner)
        colliders.append({'id': guard['id'], 'floor': f, 'polygon': list(edge.buffer(.06, cap_style=2).exterior.coords), 'kind': 'guard'})

    def balustrade(self, edge, z, f, name, owner):
        """Turned teak balusters under a moulded handrail."""
        k = self.k
        k.poly_mesh(edge.buffer(.04, cap_style=2, join_style=2), z + 1.0, z + 1.06, 'hb-teak-dark', f, 'railing', name + '-handrail', owner)
        k.poly_mesh(edge.buffer(.03, cap_style=2, join_style=2), z + .02, z + .08, 'hb-teak-dark', f, 'railing', name + '-bottom', owner)
        count = max(1, math.ceil(edge.length / .13))
        for i in range(count + 1):
            q = edge.interpolate(i / count, normalized=True)
            k.cylinder((q.x, q.y, z + .54), .022, .92, 'hb-teak', f, 'railing')
            k.ball((q.x, q.y, z + .3), (.034, .034, .05), 'hb-teak', f, 'railing')
            k.ball((q.x, q.y, z + .78), (.032, .032, .045), 'hb-teak', f, 'railing')

    # ------------------------------------------------------------------------------------------ windows & doors
    def window(self, o, w, part, p, uv, nv, room_kinds, outdoor_kind):
        """Steel windows with small panes and a top ventilator, a brick-bond grille outside the ground floor and a
        sloping sheet-metal sunshade on angle brackets wherever the window faces open sky."""
        k, H = self.k, self.H
        ow = o['width'] / 1000; zh = o['height'] / 1000; base = o['floor'] * H; z0 = base + o['sill'] / 1000
        t_half = w['thickness'] / 2000
        wet = bool(set(room_kinds) & {'bathroom', 'utility', 'drying-room', 'powder-room'})
        mat = 'hb-steel-window'
        if o.get('grille'):
            grid = brick_grille(ow, zh, course=.15, brick=.3, bar=.02, frame=.04)
            panel(k, grid, .025, 'hb-grille', (p[0], p[1], z0), uv, o['floor'], 'joinery', o['id'])
            # A fly screen just inside the bars, as on most verandah grilles.
            q = p + nv * .03
            panel(k, box(.04, .04, ow - .04, zh - .04), .002, 'hb-fly-mesh', (q[0], q[1], z0), uv, o['floor'], 'blind', o['id'])
            part(ow / 2, t_half - .04, z0 - .02, ow, .08, .04, 'floor-kota-stone', 'sill')
            part(ow / 2, -t_half - .06, z0 - .025, ow + .1, .12, .05, 'floor-kota-stone', 'sill')
            return
        fw, fd = .05, .06
        part(fw / 2, 0, z0 + zh / 2, fw, fd, zh, mat); part(ow - fw / 2, 0, z0 + zh / 2, fw, fd, zh, mat)
        part(ow / 2, 0, z0 + zh - fw / 2, ow, fd, fw, mat); part(ow / 2, 0, z0 + fw / 2, ow, fd, fw, mat)
        cols = max(2, round(ow / .5))
        vent = min(.45, zh * .22) if zh > 1.2 else 0
        for i in range(1, cols):
            part(ow * i / cols, 0, z0 + zh / 2, .03, fd * .8, zh - 2 * fw, mat)
        rows = 2 if zh - vent > 1.2 else 1
        main = zh - vent - fw
        for j in range(1, rows):
            part(ow / 2, 0, z0 + fw + main * j / rows, ow - 2 * fw, fd * .8, .028, mat)
        if vent:
            part(ow / 2, 0, z0 + zh - vent, ow - 2 * fw, fd, .04, mat)
        part(ow / 2, .004, z0 + zh / 2, ow - .06, .01, zh - .06, 'frosted' if wet else 'hb-glass', 'glass')
        if o['sill'] > 100:
            part(ow / 2, t_half - .04, z0 - .02, ow + .04, .1, .04, 'floor-kota-stone', 'sill')
            part(ow / 2, -t_half - .05, z0 - .025, ow + .12, .1, .05, 'floor-kota-stone', 'sill')
        open_air = outdoor_kind in (None, 'terrace', 'balcony', 'drying-yard', 'courtyard')
        if o['floor'] == 0 and open_air:
            grid = brick_grille(ow + .08, zh + .06, course=.15, brick=.3, bar=.018, frame=.03)
            q = p - uv * .04 - nv * (t_half + .035)
            panel(k, grid, .02, 'hb-grille-dark', (q[0], q[1], z0 - .03), uv, o['floor'], 'joinery', o['id'])
        if open_air:
            self.chajja(p, uv, nv, ow, z0 + zh + .1, t_half, o['floor'], o['id'])

    def chajja(self, p, uv, nv, ow, z_wall, t_half, floor, owner, depth=.6, slope=.42):
        """A sloping sheet sunshade on two angle-iron brackets."""
        k = self.k
        out = -nv
        a = p - uv * .2 + out * t_half
        c = p + uv * (ow + .2) + out * t_half
        poly = Polygon([a, c, c + out * depth, a + out * depth])
        drop = math.tan(slope)
        def z_at(x, y):
            return z_wall + .32 - max(0., float(np.dot(np.array([x, y]) - a, out))) * drop
        sloped(k, poly, z_at, .012, 'hb-chajja', floor, 'window-hood', owner)
        for end in (a + uv * .05, c - uv * .05):
            tip = end + out * (depth - .03)
            k.beam((end[0], end[1], z_wall - .12), (tip[0], tip[1], z_wall + .3 - depth * drop), .011, 'hb-chajja', floor, 'window-hood')
            k.beam((end[0], end[1], z_wall + .3), (tip[0], tip[1], z_wall + .3 - depth * drop), .009, 'hb-chajja', floor, 'window-hood')

    def grille_door(self, o, w, p, uv, nv, base, zh, ow, swing_poly):
        """An open steel grille door: brick-bond bars above a sheet kick panel and a tower bolt, swung 90 degrees
        into the space it serves. The viewer closes it about the planned hinge like any other hinged leaf."""
        k = self.k
        t_half = w['thickness'] / 2000
        if swing_poly is not None and not swing_poly.buffer(.05).contains(Point(*(p + uv * ow / 2 + nv * (t_half + .3)))):
            nv = -nv
        hinge = p + uv * (.055 if o.get('hinge', 'start') == 'start' else ow - .055)
        L = ow - .1
        lh = zh - .05
        rot = math.atan2(nv[1], nv[0])
        kick = hinge + nv * L / 2
        k.rb((kick[0], kick[1], base + .45), (L, .012, .8), 'hb-grille', o['floor'], 'door', .004, rot, owner=o['id'])
        grid = brick_grille(L, lh, course=.15, brick=.3, bar=.02, frame=.04)
        panel(k, grid, .03, 'hb-grille', (hinge[0], hinge[1], base + .02), nv, o['floor'], 'door', o['id'])
        bolt = hinge + nv * (L - .12)
        k.rect((bolt[0] - .03, bolt[1] - .03, base + 1.05, bolt[0] + .03, bolt[1] + .03, base + 1.25), 'hb-steel', o['floor'], 'door', owner=o['id'])

    def door_panels(self, leafcenter, nv, uv, base, zh, ow, mat, floor, owner):
        """Raised teak panels on both faces of an open hinged leaf (the leaf lies along nv)."""
        k = self.k
        L = ow - .1
        for face in (-1, 1):
            for j, (v0, v1) in enumerate(((.12, .82), (.95, 1.65), (1.78, zh - .14))):
                if v1 - v0 < .2:
                    continue
                for s in ((-L / 4, L / 4) if L > .75 else (0,)):
                    c = leafcenter + nv * s + uv * face * .024
                    w_ = L / 2 - .14 if L > .75 else L - .2
                    rot = math.atan2(uv[1], uv[0])
                    k.rb((c[0], c[1], base + (v0 + v1) / 2), (.008, w_, v1 - v0), mat, floor, 'door', .002, rot, owner=owner)
        knob = leafcenter + nv * (L / 2 - .08)
        for face in (-1, 1):
            q = knob + uv * face * .05
            k.ball((q[0], q[1], base + 1.0), (.026, .026, .026), 'hb-brass', floor, 'door')

    def bx(self, p, uv, nv, x, depth, z, size, mat, floor, role, owner=None):
        """A box in an opening's frame: x along the wall from p, depth along nv, centred at height z."""
        q = p + uv * x + nv * depth
        return self.k.node(self.k.cube, mat, (q[0], q[1], z), size, (0, 0, math.atan2(uv[1], uv[0])), floor, role, owner=owner)

    def arch(self, o, w, p, uv, nv):
        """Wide cased openings become segmental arches: lime-washed spandrels, an archivolt band, a keystone and
        plain pilasters with moulded caps on both faces."""
        ow, zh = o['width'] / 1000, o['height'] / 1000
        if ow < 1.8 or zh < 2.6:
            return
        k = self.k
        f = o['floor']
        base = f * self.H + o['sill'] / 1000
        t = w['thickness'] / 1000
        rise = min(.5, ow * .16)
        R = ((ow / 2) ** 2 + rise ** 2) / (2 * rise)
        centre = Point(ow / 2, zh - R)
        spandrel = box(0, zh - rise, ow, zh).difference(centre.buffer(R, 96))
        panel(k, spandrel, t - .004, 'hb-limewash', (p[0], p[1], base), uv, f, 'wall', o['id'], o['id'] + '-arch')
        band = centre.buffer(R + .11, 96).difference(centre.buffer(R, 96)).intersection(box(0, zh - rise, ow, zh))
        panel(k, band, t + .036, 'paint-ivory', (p[0], p[1], base), uv, f, 'wall-panel', o['id'])
        key = Polygon([(ow / 2 - .07, zh - .005), (ow / 2 + .07, zh - .005), (ow / 2 + .1, min(zh + .2, zh + .2)), (ow / 2 - .1, zh + .2)])
        panel(k, key.difference(centre.buffer(R, 96)).intersection(box(0, 0, ow, zh)), t + .05, 'paint-ivory', (p[0], p[1], base), uv, f, 'wall-panel', o['id'])
        spring = zh - rise
        for x in (-.07, ow + .07):
            for side in (-1, 1):
                d = side * (t / 2 + .009)
                self.bx(p, uv, nv, x, d, base + spring / 2, (.16, .018, spring), 'paint-ivory', f, 'wall-panel', o['id'])
                self.bx(p, uv, nv, x, side * (t / 2 + .02), base + spring - .06, (.22, .04, .1), 'paint-ivory', f, 'wall-panel', o['id'])

    def curtains(self, o, p, uv, nv, room_kinds):
        """Printed cotton curtains gathered on a brass rod with ball finials, in living rooms and bedrooms."""
        if not set(room_kinds) & {'bedroom', 'living', 'drawing-room', 'family', 'dining', 'study', 'dress'} or o['height'] < 1000:
            return
        k, H = self.k, self.H
        f = o['floor']
        ow = o['width'] / 1000; base = f * H; z0 = base + o['sill'] / 1000; zh = o['height'] / 1000
        top = min(base + H - .3, z0 + zh + .16)
        rod = .2
        a = p - uv * .32 + nv * rod
        c = p + uv * (ow + .32) + nv * rod
        k.beam((a[0], a[1], top), (c[0], c[1], top), .011, 'hb-brass', f, 'curtain')
        for q in (a, c):
            k.ball((q[0], q[1], top), (.028, .028, .028), 'hb-brass', f, 'curtain')
            w0 = q - nv * (rod - .12)
            k.beam((w0[0], w0[1], top), (q[0], q[1], top), .006, 'hb-brass', f, 'curtain')
        bottom = base + .03 if o['sill'] < 300 else max(base + .03, z0 - .18)
        for u0, u1 in ((-.27, .3), (ow - .3, ow + .27)):
            verts, faces = [], []
            n = 18
            for j in range(n + 1):
                uu = u0 + (u1 - u0) * j / n
                q = p + uv * uu + nv * (rod - .025 + .03 * math.cos(j * math.pi))
                verts.extend([(q[0], q[1], bottom), (q[0], q[1], top - .025)])
            for j in range(n):
                kk = j * 2
                faces.extend([[kk, kk + 1, kk + 3], [kk, kk + 3, kk + 2]])
            k.node(k.asset(trimesh.Trimesh(vertices=verts, faces=faces, process=False), smooth=True), 'hb-curtain', floor=f, role='curtain', owner=o['id'])

    def french_door(self, o, w, p, uv, nv, base, zh, ow, space_poly, space_kind, door_motion):
        """A pair of steel-framed glazed doors with small panes, closed in the frame; each leaf opens outward."""
        k = self.k
        f = o['floor']
        outside = next((space_poly[r] for r in w['rooms'] if space_kind.get(r) in OUTDOOR), None)
        out = nv if outside is None or outside.covers(Point(*(p + uv * ow / 2 + nv * .3))) else -nv
        lw = (ow - .1) / 2
        layers = []
        for side in range(2):
            mark = len(k.nodes)
            sgn = 1 if side == 0 else -1
            hx = .05 if side == 0 else ow - .05
            cx = hx + sgn * lw / 2
            depth = float(np.dot(out, nv)) * .02
            fr = .045
            for xx in (hx + sgn * fr / 2, hx + sgn * (lw - fr / 2)):
                self.bx(p, uv, nv, xx, depth, base + zh / 2, (fr, .04, zh - .06), 'hb-steel-window', f, 'door', o['id'])
            for zz, hh in ((base + .05, .06), (base + zh - .06, .05), (base + .55, .04)):
                self.bx(p, uv, nv, cx, depth, zz, (lw, .04, hh), 'hb-steel-window', f, 'door', o['id'])
            self.bx(p, uv, nv, cx, depth, base + .3, (lw - .06, .012, .44), 'hb-steel-window', f, 'door', o['id'])
            for j in range(1, 3):
                self.bx(p, uv, nv, hx + sgn * lw * j / 3, depth, base + (zh + .55) / 2, (.022, .03, zh - .62), 'hb-steel-window', f, 'door', o['id'])
            for j in range(1, 4):
                self.bx(p, uv, nv, cx, depth, base + .57 + (zh - .63) * j / 4, (lw - .06, .03, .022), 'hb-steel-window', f, 'door', o['id'])
            self.bx(p, uv, nv, cx, depth, base + (zh + .55) / 2, (lw - .06, .008, zh - .64), 'hb-glass', f, 'glass', o['id'])
            handle = p + uv * (hx + sgn * (lw - .09)) + nv * depth
            for face in (-1, 1):
                q = handle + nv * face * .04
                k.beam((q[0], q[1], base + .95), (q[0], q[1], base + 1.2), .009, 'hb-brass', f, 'door')
            angle = sgn * math.atan2(uv[0] * out[1] - uv[1] * out[0], float(np.dot(uv, out)))
            pivot = p + uv * hx + nv * depth
            layers.append({'id': f"{o['id']}/leaf-{'left' if side == 0 else 'right'}", 'label': f"Glazed door · {'left' if side == 0 else 'right'} leaf",
                           'ids': [n['id'] for n in k.nodes[mark:]], 'pivot': [float(pivot[0]), float(pivot[1]), base], 'angle': angle,
                           'handle': [float(handle[0]), float(handle[1]), base + 1.1]})
        door_motion[o['id']] = {'layers': layers, 'clearWidth': ow - .14}

    def floor_material(self, s):
        if s.get('floorFinish'):
            return 'floor-' + s['floorFinish']
        if s['kind'] in WET:
            return 'floor-ceramic-white'
        return 'floor-red-oxide' if s['kind'] in OUTDOOR else 'floor-ivory-vitrified'

    def headhouses(self):
        """The stair headhouse keeps the house's render and carries the same red frieze on its own parapet."""
        rooftop = self.b.get('rooftop')
        if not rooftop:
            return
        k = self.k
        f = self.storeys
        for core in rooftop['cores']:
            x0, y0, x1, y1 = [q / 1000 for q in core['bounds']]
            z1 = f * self.H + core['height'] / 1000
            aid = core['id']
            k.rect((x0, y0, z1 - .15, x1, y1, z1), 'roof', f, 'roof', aid + '-lid', aid)
            ring = box(x0, y0, x1, y1)
            self.frieze([LineString(list(ring.exterior.coords))], ring.buffer(.001, join_style=2), z1, .62, f, aid + '-parapet', .36)
            k.poly_mesh(ring.buffer(-.23, join_style=2), z1, z1 + .02, 'roof', f, 'roof', owner=aid)

    def finish_scene(self, scene):
        """Scene-level context for the viewer: a quiet residential colony around the compound."""
        scene['context'] = {'style': 'colony'}
        W = max(x for x, _ in scene['footprint'])
        D = max(y for _, y in scene['footprint'])
        top = scene['storeys'] * scene['floor_height']
        # From the drive side, as the owner photographed it: carport, grilled verandah and the frieze in afternoon sun.
        scene['cameras']['hero'] = {'position': [-W * .6, -max(19., D * 1.2), top * .5 + 2.4], 'target': [W * .47, D * .22, top * .36], 'fov': 44}
        scene['cameras']['interior'] = {'position': [W * .3, 1.0, 1.6], 'target': [W * .58, D * .26, 1.3], 'fov': 66}

    # ------------------------------------------------------------------------------------------------- assemblies
    def assemblies(self):
        for a in self.exterior.get('assemblies', []):
            geo = a['geometry']
            x0, y0, x1, y1 = [q / 1000 for q in geo['bounds_mm']]
            kind = geo.get('kind')
            if kind == 'sheet_carport':
                self.carport(a, x0, y0, x1, y1, geo)
            elif kind == 'sheet_canopy':
                self.side_canopy(a, x0, y0, x1, y1, geo)
            elif kind == 'chick_pergola':
                self.chick_pergola(a, x0, y0, x1, y1, geo)
            elif kind == 'water_tank':
                self.water_tank(a, x0, y0, x1, y1, geo)
            elif kind == 'desert_cooler':
                self.cooler(a, x0, y0, x1, y1, geo)

    def banded_post(self, x, y, z0, z1, floor, owner, r=.038):
        k = self.k
        k.cylinder((x, y, (z0 + min(z1, z0 + 1.0)) / 2), r, min(z1, z0 + 1.0) - z0, 'hb-post-black', floor, 'carport')
        if z1 > z0 + 1.0:
            k.cylinder((x, y, (z0 + 1.0 + z1) / 2), r, z1 - z0 - 1.0, 'hb-post-red', floor, 'carport')
        k.colliders.append({'id': owner + f'/post-{x:.2f}-{y:.2f}', 'floor': floor, 'polygon': list(Point(x, y).buffer(r + .02, 6).exterior.coords), 'kind': 'furniture'})

    def carport(self, a, x0, y0, x1, y1, geo):
        """Corrugated sheet on a red angle frame, banded red-and-black posts and a tube light under it."""
        k, g = self.k, self.g
        aid = a['id']
        low, high = geo['roof_low_mm'] / 1000, geo['roof_high_mm'] / 1000
        west = geo.get('fall') == 'west'
        def z_at(x, y):
            t = (x - x0) / (x1 - x0)
            return g + (low + (high - low) * t if west else high - (high - low) * t)
        corrugated(k, x0 - .25, y0 - .25, x1 + .25, y1 + .25, lambda x, y: z_at(x, y) + .02, 'hb-corrugated', -1, 'carport', aid, aid)
        posts_y = [y0 + .15, (y0 + y1) / 2, y1 - .15]
        for x in (x0 + .15, x1 - .15):
            for y in posts_y:
                self.banded_post(x, y, g, z_at(x, y) - .06, -1, aid)
            k.beam((x, y0 - .2, z_at(x, y0) - .05), (x, y1 + .2, z_at(x, y1) - .05), .03, 'hb-post-red', -1, 'carport')
        for y in np.linspace(y0 - .1, y1 + .1, 6):
            k.beam((x0 - .2, y, z_at(x0 - .2, y) - .02), (x1 + .2, y, z_at(x1 + .2, y) - .02), .022, 'hb-post-red', -1, 'carport')
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        zt = z_at(cx, cy) - .1
        k.rect((cx - .62, cy - .05, zt - .05, cx + .62, cy + .05, zt), 'hb-white-steel', -1, 'fixture')
        k.rect((cx - .6, cy - .02, zt - .07, cx + .6, cy + .02, zt - .05), 'hb-tube', -1, 'fixture')
        k.light((cx, cy, zt - .25), 22, color='#f3f6ff', kind='downlight')

    def side_canopy(self, a, x0, y0, x1, y1, geo):
        """White-post walkway canopy with a light corrugated sheet sloping away from the house wall."""
        k, g = self.k, self.g
        aid = a['id']
        h = geo.get('height_mm', 2750) / 1000
        house_x = x0
        def z_at(x, y):
            return g + .6 + h + .25 - .25 * (x - house_x) / max(.1, x1 - house_x)
        corrugated(k, x0 + .03, y0, x1 + .15, y1, z_at, 'hb-sheet-light', -1, 'canopy', aid, aid)
        n = max(2, round((y1 - y0) / (geo.get('post_spacing_mm', 2600) / 1000)) + 1)
        for y in np.linspace(y0 + .1, y1 - .1, n):
            k.rect((x1 - .06, y - .03, g, x1, y + .03, z_at(x1, y) - .03), 'hb-white-steel', -1, 'canopy')
            k.obstacle(box(x1 - .06, y - .03, x1, y + .03), -1, aid + f'/post-{y:.2f}')
        k.rect((x1 - .07, y0, z_at(x1, y0) - .09, x1 + .01, y1, z_at(x1, y0) - .03), 'hb-white-steel', -1, 'canopy')
        k.rect((x0 + .02, y0, z_at(x0, y0) - .06, x0 + .07, y1, z_at(x0, y0) - .01), 'hb-white-steel', -1, 'canopy')
        for y in np.linspace(y0 + .4, y1 - .4, max(1, round((y1 - y0) / 6))):
            k.rect((x0 + .4, y - .3, z_at(x0 + .4, y) - .07, x0 + .46, y + .3, z_at(x0 + .4, y) - .04), 'hb-tube', -1, 'fixture')
            k.light((x0 + .5, y, z_at(x0 + .5, y) - .3), 12, color='#f3f6ff', kind='downlight')

    def chick_pergola(self, a, x0, y0, x1, y1, geo):
        """Bamboo posts and a steel angle frame carry a sloping bamboo chick screen over the front terrace."""
        k, H = self.k, self.H
        f = a.get('floor_id', 1)
        z = f * H
        h = geo.get('height_mm', 2450) / 1000
        aid = a['id']
        def z_at(x, y):
            return z + h + .12 - .18 * (y - y0) / max(.1, y1 - y0)
        sloped(k, box(x0 - .15, y0 - .15, x1 + .15, y1 + .15), lambda x, y: z_at(x, y) + .02, .012, 'hb-chick', f, 'pergola', aid, aid)
        nx = max(2, round((x1 - x0) / 2.4) + 1)
        ny = max(2, round((y1 - y0) / 2.4) + 1)
        for x in np.linspace(x0, x1, nx):
            k.beam((x, y0 - .1, z_at(x, y0) - .02), (x, y1 + .1, z_at(x, y1) - .02), .02, 'hb-grille-dark', f, 'pergola')
        for y in np.linspace(y0, y1, ny):
            k.beam((x0 - .1, y, z_at(x0, y) - .03), (x1 + .1, y, z_at(x1, y) - .03), .018, 'hb-grille-dark', f, 'pergola')
        for x in (x0, x1):
            for y in (y0, y1):
                k.cylinder((x, y, z + (z_at(x, y) - z) / 2), .045, z_at(x, y) - z, 'hb-bamboo', f, 'pergola')
                k.obstacle(Point(x, y).buffer(.06, 6), f, aid + f'/post-{x:.1f}-{y:.1f}')
                for zz in np.arange(z + .4, z_at(x, y) - .1, .4):
                    k.cylinder((x, y, zz), .048, .018, 'hb-bamboo', f, 'detail')
        # Strings of the chick and a bare bulb pendant under it.
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        k.beam((cx, cy, z_at(cx, cy) - .02), (cx, cy, z_at(cx, cy) - .55), .004, 'hb-rope', f, 'fixture')
        k.ball((cx, cy, z_at(cx, cy) - .6), (.06, .06, .08), 'hb-globe', f, 'fixture')
        k.light((cx, cy, z_at(cx, cy) - .7), 14, kind='pendant')

    def water_tank(self, a, x0, y0, x1, y1, geo):
        """A ribbed white water tank on the stair headhouse, a steel ladder up its wall and a dish antenna."""
        k, H = self.k, self.H
        f = self.storeys
        rooftop = self.b.get('rooftop') or {}
        core = next((c for c in rooftop.get('cores', []) if c['id'] == geo.get('core_id')), None)
        hz = f * H + (core['height'] / 1000 if core else 2.7)
        r = geo.get('diameter_mm', 1380) / 2000
        th = geo.get('height_mm', 1620) / 1000
        cx = x0 + .25 + r + .3
        cy = (y0 + y1) / 2
        aid = a['id']
        k.rect((cx - r - .08, cy - r - .08, hz, cx + r + .08, cy + r + .08, hz + .08), 'roof', f, 'roof', owner=aid)
        tank = trimesh.creation.revolve(np.array([[0, 0], [r * .96, 0], [r, .04], [r, th * .82], [r * .78, th * .96], [r * .32, th],
                                                  [.001, th]]), sections=36)
        k.node(k.asset(tank, smooth=True), 'hb-tank', (cx, cy, hz + .08), floor=f, role='roof', name=aid, owner=aid)
        for zz in np.linspace(hz + .3, hz + th * .75, 5):
            k.cylinder((cx, cy, zz), r + .012, .04, 'hb-tank', f, 'roof')
        k.cylinder((cx, cy, hz + .1 + th), .2, .06, 'hb-tank', f, 'roof')
        k.beam((cx + r * .7, cy, hz + .3), (cx + r * .7, cy, hz - .4), .025, 'hb-pvc', f, 'pipe')
        # Ladder on the headhouse face toward the terrace (the free x side).
        lx = x1 + .03
        for yy in (cy - .22, cy + .22):
            k.beam((lx + .08, yy, f * H + .02), (lx + .02, yy, hz + .9), .018, 'hb-grille-dark', f, 'railing')
        for zz in np.arange(f * H + .3, hz + .7, .3):
            k.beam((lx + .07, cy - .22, zz), (lx + .07, cy + .22, zz), .011, 'hb-grille-dark', f, 'railing')
        if geo.get('dish_antenna'):
            dx, dy = x1 - .45, y0 + .45
            k.beam((dx, dy, hz + .05), (dx, dy, hz + .75), .022, 'hb-steel', f, 'roof')
            dish = trimesh.creation.revolve(np.array([[0, 0], [.28, .07], [.3, .09], [.001, .09]]), sections=24)
            k.node(k.asset(dish, smooth=True), 'hb-white-steel', (dx - .1, dy + .05, hz + .85), rot=(1.1, 0, .6), floor=f, role='roof', owner=aid)

    def cooler(self, a, x0, y0, x1, y1, geo):
        """A desert cooler on brackets outside a bedroom window: louvred khus-pad sides and a small hood."""
        k, H = self.k, self.H
        o = next((q for q in self.b['openings'] if q['id'] == geo['opening_id']), None)
        if o is None:
            return
        f = o['floor']
        z0 = f * H + o['sill'] / 1000 - .05
        z1 = z0 + 1.05
        aid = a['id']
        k.rect((x0, y0, z0, x1, y1, z1), 'hb-cooler', f, 'appliance', aid, aid)
        side = geo.get('facing', 1)
        face = x1 if side > 0 else x0
        for zz in np.arange(z0 + .12, z1 - .12, .07):
            k.rect((min(face, face + side * .015), y0 + .08, zz, max(face, face + side * .015), y1 - .08, zz + .035), 'hb-khus', f, 'appliance', owner=aid)
        for yy in (y0, y1):
            k.rect((x0 + .06, min(yy, yy + .01), z0 + .1, x1 - .06, max(yy, yy + .01), z1 - .1), 'hb-khus', f, 'appliance', owner=aid)
        k.rect((x0 - .03, y0 - .03, z1, x1 + .03, y1 + .03, z1 + .04), 'hb-cooler', f, 'appliance', owner=aid)
        wall = x0 if side > 0 else x1
        for yy in (y0 + .1, y1 - .1):
            k.beam((wall, yy, z0 - .45), (face - side * .05, yy, z0 - .01), .014, 'hb-chajja', f, 'appliance')

    # ------------------------------------------------------------------------------------------------- landscape
    def landscape_features(self):
        """Draw the heritage site plan. Returns lawn records for the viewer's instanced grass."""
        k, g = self.k, self.g
        lawns = []
        for feat in self.landscape.get('features', []):
            fk = feat['kind']
            poly = None
            if 'polygon' in feat:
                poly = Polygon(np.array(feat['polygon'], dtype=float) / 1000)
                if not poly.is_valid:
                    poly = poly.buffer(0)
            if fk == 'hex_paving':
                mat = 'hb-hex-yellow' if feat.get('tone') == 'yellow' else 'hb-hex'
                k.poly_mesh(poly, g - .02, g + (.038 if feat.get('tone') == 'yellow' else .035), mat, -1, 'court', feat['id'], feat['id'])
            elif fk == 'lawn':
                k.poly_mesh(poly, g - .03, g + .012, 'lawn', -1, 'lawn', feat['id'], feat['id'])
                lawns.append({'id': feat['id'], 'polygon': [[round(x, 4), round(y, 4)] for x, y in list(poly.exterior.coords)[:-1]],
                              'holes': [[[round(x, 4), round(y, 4)] for x, y in list(r.coords)[:-1]] for r in poly.interiors], 'z': round(g + .012, 4)})
            elif fk == 'flower_bed':
                self.flower_bed(feat, poly)
            elif fk == 'kitchen_garden':
                self.kitchen_garden(feat, poly)
            elif fk == 'entry_steps':
                self.steps(feat)
            elif fk == 'hedge':
                x, y = [q / 1000 for q in feat['position_mm']]
                L, Wd, Hh = [q / 1000 for q in feat['size_mm']]
                k.hedge(x, y, g + .01, (L, Wd, Hh), feat.get('rotation', 0))
                if feat.get('flowering'):
                    k.vegetation[-1]['options'] = {'flowers': 'white'}
                k.ground.append(box(x - L / 2, y - Wd / 2, x + L / 2, y + Wd / 2))
            elif fk == 'tree':
                x, y = [q / 1000 for q in feat['position_mm']]
                self.tree(x, y, feat.get('species', 'neem'), feat.get('scale', 1.))
            elif fk == 'plant':
                x, y = [q / 1000 for q in feat['position_mm']]
                k.plant(x, y, g + .02, feat.get('species', 'areca'), scale=feat.get('scale', 1.))
            elif fk == 'pot':
                x, y = [q / 1000 for q in feat['position_mm']]
                self.pot(x, y, g + .035, feat['radius_mm'] / 1000, feat['height_mm'] / 1000, feat.get('tone', 'red'), feat.get('species', 'marigold'), -1, feat.get('rim'))
            elif fk == 'rose_fence':
                self.rose_fence(feat)
            elif fk == 'plant_stand':
                x, y = [q / 1000 for q in feat['position_mm']]
                self.plant_stand(x, y, g + .035, feat.get('rotation', 0), -1, feat['id'])
            elif fk == 'garden_seat':
                x, y = [q / 1000 for q in feat['position_mm']]
                self.garden_seat(x, y, feat.get('rotation', 0), feat['id'])
            elif fk == 'jhoola':
                x, y = [q / 1000 for q in feat['position_mm']]
                self.swing(x, y, feat.get('rotation', 0), feat['id'])
            elif fk == 'tulsi':
                x, y = [q / 1000 for q in feat['position_mm']]
                self.tulsi(x, y, feat['id'])
            elif fk == 'hose_reel':
                x, y = [q / 1000 for q in feat['position_mm']]
                for i in range(4):
                    ring = trimesh.creation.torus(major_radius=.24 - i * .025, minor_radius=.012, major_sections=28, minor_sections=6)
                    k.node(k.asset(ring, smooth=True), 'hb-hose', (x + i * .01, y, g + .03 + i * .022), floor=-1, role='detail')
        return lawns

    def tree(self, x, y, species, scale):
        """A tree, with the lime-washed band that colony gardeners paint around trunks."""
        k, g = self.k, self.g
        k.plant(x, y, g + .015, species, scale=scale)
        trunk = {'neem': .2, 'mango': .21, 'ashoka': .12, 'araucaria': .13}.get(species)
        if trunk:
            r = trunk * scale + .012
            k.cylinder((x, y, g + .45), r, .9, 'hb-limewash', -1, 'landscape')
            k.cylinder((x, y, g + .93), r + .003, .07, 'hb-stripe', -1, 'landscape')
            k.cylinder((x, y, g + .02), r + .25, .04, 'soil', -1, 'landscape')

    def pot(self, x, y, z, r, h, tone, species, floor=-1, rim=None):
        """A rolled-rim garden pot with soil and a plant."""
        k = self.k
        profile = np.array([[0, 0], [r * .62, 0], [r * .66, .02], [r * .92, h * .86], [r * 1.02, h * .88], [r * 1.04, h],
                            [r * .9, h], [r * .86, h * .9], [r * .6, .06], [.001, .06]])
        vessel = trimesh.creation.revolve(profile, sections=24)
        mat = {'red': 'hb-pot-red', 'pink': 'hb-pot-pink'}.get(tone, 'hb-pot-red')
        k.node(k.asset(vessel, smooth=True), mat, (x, y, z), floor=floor, role='planter')
        if rim:
            k.cylinder((x, y, z + h - .02), r * 1.045, .04, 'hb-pot-yellow', floor, 'planter')
        k.cylinder((x, y, z + h * .86), r * .9, .01, 'soil', floor, 'landscape')
        spec, scale, opts = PLANT_IN_POT.get(species, ('flower_clump', .45, {'color': 'marigold'}))
        k.plant(x, y, z + h * .86, spec, scale=scale * (r / .19), f=floor, options=opts)

    def plant_stand(self, x, y, z, rot, floor, owner):
        """A tiered white steel plant stand carrying small pots."""
        k = self.k
        c, s = math.cos(rot), math.sin(rot)
        def P(u, v):
            return x + u * c - v * s, y + u * s + v * c
        for u in (-.33, .33):
            for v in (-.18, .18):
                px, py = P(u, v)
                k.rect((px - .012, py - .012, z, px + .012, py + .012, z + 1.05), 'hb-white-steel', floor, 'furniture')
        for j, (zz, v) in enumerate(((.32, .12), (.66, 0), (1.0, -.12))):
            px, py = P(0, v)
            k.rb((px, py, z + zz), (.7, .2, .025), 'hb-white-steel', floor, 'furniture', .005, rot)
            for u in (-.2, .2) if j < 2 else (0,):
                qx, qy = P(u, v)
                self.pot(qx, qy, z + zz + .013, .085, .13, ('pink', 'red')[(j + int(u > 0)) % 2], ('geranium', 'periwinkle', 'marigold')[j], floor)
        k.obstacle(Polygon([P(-.38, -.22), P(.38, -.22), P(.38, .22), P(-.38, .22)]), floor, owner)

    def flower_bed(self, feat, poly):
        """Soil, a saw-tooth brick (or laterite) edging and a planting mix."""
        k, g = self.k, self.g
        if poly is None or poly.is_empty:
            return
        k.poly_mesh(poly, g - .02, g + .03, 'soil', -1, 'landscape', feat['id'], feat['id'])
        edge_mat = 'hb-laterite' if feat.get('edging') == 'laterite' else 'hb-brick'
        ring = poly.exterior
        n = max(4, int(ring.length / .23))
        bricks = []
        for i in range(n):
            q = ring.interpolate(i / n, normalized=True)
            q2 = ring.interpolate((i + .5) / n, normalized=True)
            d = np.array([q2.x - q.x, q2.y - q.y])
            if np.linalg.norm(d) < 1e-6:
                continue
            d /= np.linalg.norm(d)
            m = np.array([-d[1], d[0]])
            c = np.array([q.x, q.y])
            # Bricks set on end at 45 degrees: a saw-tooth edge.
            u = (d + m) / math.sqrt(2)
            v = np.array([-u[1], u[0]])
            pts = [c - u * .11 - v * .04, c + u * .11 - v * .04, c + u * .11 + v * .04, c - u * .11 + v * .04]
            bricks.append(Polygon(pts))
        k.poly_mesh(unary_union(bricks).intersection(poly.buffer(.06)), g - .01, g + .12, edge_mat, -1, 'edging', feat['id'] + '-edge', feat['id'])
        mix = feat.get('mix', 'seasonal')
        x0, y0, x1, y1 = poly.bounds
        inner = poly.buffer(-.28 if min(x1 - x0, y1 - y0) > 1.2 else -.14)
        step = {'roses': .75, 'lilies': .42, 'facade': .5, 'seasonal': .55}.get(mix, .6)
        # Seeded from the bed's id (not Python's salted hash) so every build plants the same bed.
        rng = np.random.default_rng(sum(map(ord, feat['id'])))
        i = 0
        for yy in np.arange(y0 + .2, y1 - .1, step * .87):
            for xx in np.arange(x0 + .25 + (step / 2 if i % 2 else 0), x1 - .15, step):
                px, py = xx + rng.uniform(-.08, .08), yy + rng.uniform(-.08, .08)
                if not inner.contains(Point(px, py)):
                    continue
                spec, scale, opts = BED_MIX[mix][int(rng.integers(len(BED_MIX[mix])))]
                k.plant(px, py, g + .03, spec, scale=scale * rng.uniform(.85, 1.15), options=opts)
            i += 1

    def kitchen_garden(self, feat, poly):
        k, g = self.k, self.g
        k.poly_mesh(poly, g - .02, g + .035, 'soil', -1, 'landscape', feat['id'], feat['id'])
        x0, y0, x1, y1 = poly.bounds
        for j, yy in enumerate(np.arange(y0 + .5, y1 - .3, .9)):
            ridge = box(x0 + .3, yy - .22, x1 - .3, yy + .22).intersection(poly.buffer(-.2))
            if ridge.is_empty:
                continue
            k.poly_mesh(ridge, g + .03, g + .1, 'soil', -1, 'landscape', owner=feat['id'])
            for xx in np.arange(x0 + .5, x1 - .4, .45):
                if ridge.contains(Point(xx, yy)):
                    k.plant(xx, yy, g + .1, 'vegetable', scale=.8 + .1 * ((j + int(xx * 3)) % 3), options={'kind': ('leafy', 'tomato', 'brinjal')[j % 3]})
        # A bamboo trellis for gourds at the back.
        for xx in np.arange(x0 + .4, x1 - .3, 1.2):
            k.cylinder((xx, y1 - .35, g + .9), .02, 1.8, 'hb-bamboo', -1, 'landscape')
        k.beam((x0 + .4, y1 - .35, g + 1.75), (x1 - .4, y1 - .35, g + 1.75), .015, 'hb-bamboo', -1, 'landscape')

    def steps(self, feat):
        """Kota stone steps with rounded nosings; the main entry adds low rendered cheek walls with pots."""
        k = self.k
        for j, t in enumerate(feat['treads']):
            poly = Polygon(np.array(t['polygon']) / 1000)
            top = t['top_mm'] / 1000
            k.poly_mesh(poly, feat['bottom_mm'] / 1000, top, 'hb-kota', 0, 'step', f"{feat['id']}-{j}", feat['opening_id'])
        for j, c in enumerate(feat.get('cheeks', [])):
            poly = Polygon(np.array(c) / 1000)
            k.poly_mesh(poly, feat['bottom_mm'] / 1000, .45, 'wall', 0, 'step', f"{feat['id']}-cheek-{j}", feat['opening_id'])
            k.poly_mesh(poly.buffer(.025, join_style=2), .45, .52, 'hb-stripe', 0, 'step', owner=feat['opening_id'])
            cx, cy = poly.centroid.x, poly.centroid.y
            n = np.array(feat['normal'])
            q = (cx + n[0] * .2, cy + n[1] * .2)
            self.pot(q[0], q[1], .52, .16, .3, 'red', 'croton', 0)

    def rose_fence(self, feat):
        """A red-painted brick kerb carrying a welded-mesh fence on angle posts, smothered in climbers."""
        k, g = self.k, self.g
        a = np.array(feat['a_mm']) / 1000
        c = np.array(feat['b_mm']) / 1000
        L = float(np.linalg.norm(c - a))
        u = (c - a) / L
        line = LineString([a, c])
        kerb = feat.get('kerb_mm', 300) / 1000
        h = feat.get('height_mm', 1850) / 1000
        k.poly_mesh(line.buffer(.115, cap_style=2), g, g + kerb, 'hb-kerb', -1, 'site', feat['id'], feat['id'])
        n = max(1, round(L / 2.4))
        for j in range(n + 1):
            p = a + u * L * j / n
            k.rect((p[0] - .022, p[1] - .022, g + kerb, p[0] + .022, p[1] + .022, g + h), 'hb-grille-dark', -1, 'fence', owner=feat['id'])
        k.poly_mesh(line.buffer(.015, cap_style=2), g + h - .03, g + h, 'hb-grille-dark', -1, 'fence', owner=feat['id'])
        panel(k, box(0, 0, L, h - kerb - .03), .003, 'hb-wire-mesh', (a[0], a[1], g + kerb), u, -1, 'fence', feat['id'])
        k.obstacle(line.buffer(.12, cap_style=2), -1, feat['id'])
        # Climbing roses and creepers trained along the mesh, with a variegated bougainvillea every few bays.
        t = .6
        i = 0
        while t < L - .4:
            p = a + u * t
            species = 'bougainvillea' if i % 5 == 2 else 'climber'
            opts = {'length': 2.2, 'height': h + .25, 'flowers': ('white', 'pink', 'white', 'red')[i % 4]} if species == 'climber' else {'bracts': 'white'}
            k.plant(p[0], p[1], g + kerb, species, scale=1., rotation=math.atan2(u[1], u[0]), options=opts)
            t += 2.0
            i += 1

    def garden_seat(self, x, y, rot, owner):
        """Four white moulded plastic chairs round a small plastic table on the lawn."""
        k, g = self.k, self.g
        z = g + .012
        k.cylinder((x, y, z + .36), .04, .7, 'hb-plastic', -1, 'outdoor-furniture')
        k.cylinder((x, y, z + .72), .38, .03, 'hb-plastic', -1, 'outdoor-furniture')
        k.cylinder((x, y, z + .02), .25, .04, 'hb-plastic', -1, 'outdoor-furniture')
        for i in range(4):
            a = rot + i * math.pi / 2
            cx, cy = x + math.cos(a) * .78, y + math.sin(a) * .78
            plastic_chair(k, cx, cy, z, a + math.pi / 2, -1)
        k.obstacle(Point(x, y).buffer(1.1, 8), -1, owner)

    def swing(self, x, y, rot, owner):
        """A garden jhoola: a painted steel A-frame and a slatted teak bench on chains."""
        k, g = self.k, self.g
        c, s = math.cos(rot), math.sin(rot)
        def P(u, v):
            return x + u * c - v * s, y + u * s + v * c
        top = g + 2.15
        for u in (-1.05, 1.05):
            for v in (-.55, .55):
                bx, by = P(u * 1.12, v)
                tx, ty = P(u, 0)
                k.beam((bx, by, g), (tx, ty, top), .028, 'hb-net-frame', -1, 'outdoor-furniture')
        a0, a1 = P(-1.1, 0), P(1.1, 0)
        k.beam((a0[0], a0[1], top), (a1[0], a1[1], top), .035, 'hb-net-frame', -1, 'outdoor-furniture')
        seat_z = g + .48
        for u in (-.62, .62):
            hx, hy = P(u, 0)
            k.beam((hx, hy, top), (hx, hy, seat_z + .02), .006, 'hb-steel', -1, 'outdoor-furniture')
        for j, v in enumerate(np.arange(-.22, .23, .088)):
            px, py = P(0, v)
            k.rb((px, py, seat_z), (1.3, .07, .035), 'hb-teak', -1, 'outdoor-furniture', .008, rot)
        bx, by = P(0, .26)
        k.rb((bx, by, seat_z + .28), (1.3, .04, .44), 'hb-teak', -1, 'outdoor-furniture', .01, rot)
        k.obstacle(Polygon([P(-1.25, -.65), P(1.25, -.65), P(1.25, .65), P(-1.25, .65)]), -1, owner)

    def tulsi(self, x, y, owner):
        """A tulsi chaura: a stepped, lime-washed pedestal with a red band, a diya niche and the holy basil."""
        k, g = self.k, self.g
        k.rect((x - .42, y - .42, g, x + .42, y + .42, g + .12), 'hb-kota', -1, 'landscape', owner, owner)
        k.rect((x - .3, y - .3, g + .12, x + .3, y + .3, g + .82), 'hb-limewash', -1, 'landscape', owner=owner)
        k.rect((x - .34, y - .34, g + .82, x + .34, y + .34, g + .9), 'hb-stripe', -1, 'landscape', owner=owner)
        k.rect((x - .1, y - .305, g + .35, x + .1, y - .29, g + .55), 'hb-plate', -1, 'landscape', owner=owner)
        k.cylinder((x, y - .33, g + .37), .03, .02, 'hb-brass', -1, 'detail')
        k.plant(x, y, g + .9, 'tulsi', scale=1.)
        k.obstacle(box(x - .42, y - .42, x + .42, y + .42), -1, owner)

    # ------------------------------------------------------------------------------------------------ rainwater
    def downpipes(self):
        """White PVC rain-water pipes at the outer corners, with a shoe at the foot."""
        k, g, H = self.k, self.g, self.H
        fp = self.fp
        corners = []
        for x, y in list(fp.exterior.coords)[:-1]:
            prev_in = fp.buffer(-.01).contains(Point(x - .2, y - .2)) + fp.buffer(-.01).contains(Point(x + .2, y - .2)) + \
                fp.buffer(-.01).contains(Point(x - .2, y + .2)) + fp.buffer(-.01).contains(Point(x + .2, y + .2))
            if prev_in == 1:
                corners.append((x, y))
        outlines = [self.metres(floor_outline(self.b, f)).buffer(.35) for f in range(self.storeys)]
        roofs = [self.metres(roof(self.b, f)).buffer(.35) for f in range(self.storeys)]
        for i, (x, y) in enumerate(corners[:8]):
            dx = .09 if fp.contains(Point(x - .2, y)) else -.09
            dy = .09 if fp.contains(Point(x, y - .2)) else -.09
            px, py = x - dx, y + (-.15 if dy > 0 else .15)
            # Each pipe rises to the parapet of the roof or open terrace it drains and ends in a rain-water head.
            covered = [f for f in range(self.storeys) if roofs[f].contains(Point(x, y))]
            level = max(covered) + 1 if covered else max(f for f in range(self.storeys) if outlines[f].contains(Point(x, y)))
            top = level * H + .42
            if top < 2:
                continue
            k.beam((px, py, g + .15), (px, py, top), .045, 'hb-pvc', -1, 'pipe')
            k.rect((px - .09, py - .09, top - .02, px + .09, py + .09, top + .14), 'hb-pvc', -1, 'pipe')
            k.beam((px, py, g + .15), (px - dx * 2.5, py, g + .05), .045, 'hb-pvc', -1, 'pipe')

    def plinth(self):
        """A red-oxide plinth band below the blush render."""
        self.k.poly_mesh(self.fp, -self.b['brief']['plinth_mm'] / 1000, -.15, 'hb-plinth', role='plinth')
        self.k.poly_mesh(self.fp.buffer(.012, join_style=2).difference(self.fp), -self.b['brief']['plinth_mm'] / 1000, .05, 'hb-plinth', role='plinth', name='heritage-plinth-band')


def plastic_chair(k, x, y, z, rot, floor):
    """A white moulded monobloc chair."""
    c, s = math.cos(rot), math.sin(rot)
    def P(u, v, zz):
        return (x + u * c - v * s, y + u * s + v * c, z + zz)
    for u in (-.2, .2):
        for v in (-.18, .2):
            a, b = P(u, v, 0), P(u * .92, v * .92, .42)
            k.beam(a, b, .022, 'hb-plastic', floor, 'outdoor-furniture')
    k.rb(P(0, 0, .44), (.46, .44, .035), 'hb-plastic', floor, 'outdoor-furniture', .015, rot)
    k.rb(P(0, .22, .7), (.46, .035, .44), 'hb-plastic', floor, 'outdoor-furniture', .015, rot)
    k.nodes[-1]['rotation'][0] = -.12
    for u in (-.25, .25):
        k.rb(P(u, 0, .62), (.035, .4, .03), 'hb-plastic', floor, 'outdoor-furniture', .01, rot)


# Plants in pots and beds: (viewer species, scale, options).
PLANT_IN_POT = {
    'marigold': ('flower_clump', .85, {'color': 'marigold'}),
    'geranium': ('flower_clump', .8, {'color': 'red'}),
    'croton': ('croton', .62, {}),
    'periwinkle': ('flower_clump', .75, {'color': 'pink'}),
    'tulsi': ('tulsi', .75, {}),
    'jade': ('shrub_round', .32, {}),
    'poinsettia': ('croton', .65, {'leaf': 'poinsettia'}),
    'gerbera': ('flower_clump', .8, {'color': 'orange'}),
    'bougainvillea': ('bougainvillea', .5, {'bracts': 'magenta'}),
}
BED_MIX = {
    'roses': [('rose_bush', 1., {'color': 'red'}), ('rose_bush', 1., {'color': 'pink'}), ('rose_bush', .9, {'color': 'white'})],
    'lilies': [('amaryllis', 1., {}), ('amaryllis', .9, {}), ('flower_clump', .95, {'color': 'pink'}), ('croton', .7, {'leaf': 'poinsettia'})],
    'facade': [('croton', .8, {}), ('flower_clump', .95, {'color': 'red'}), ('rose_bush', .85, {'color': 'pink'}), ('flower_clump', .9, {'color': 'marigold'})],
    'seasonal': [('flower_clump', 1.0, {'color': 'marigold'}), ('flower_clump', .95, {'color': 'yellow'}), ('flower_clump', .9, {'color': 'purple'}),
                 ('flower_clump', .95, {'color': 'white'})],
}
