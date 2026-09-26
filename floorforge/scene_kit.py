"""Scene-building toolkit shared by the procedural generators.

Geometry is authored once (metres, Z up) as shared assets with transformed
nodes, so the realistic viewer, GLB, drawings and the Blender worker consume
the same model. Surface ``kind`` values name the physically based surface
recipes the viewer synthesises offline (web/viewer/src/textures.js).
"""
from __future__ import annotations

import math

import numpy as np
import trimesh
from shapely.geometry import Polygon, box
from shapely import constrained_delaunay_triangles, get_parts

from .model import sha

# Approximate natural heights (m) of the viewer's procedural species at scale 1.
SPECIES_HEIGHT = {
    'frangipani': 3.4, 'shrub_round': .93, 'shrub_flowering': .95, 'conifer_column': 2.3, 'topiary_spiral': 1.9,
    'strelitzia': 2.2, 'cordyline': .8, 'palm': 6.5, 'grass_ornamental': .7, 'tree_standard': 3.4, 'tree_shade': 7.0,
    'monstera': 1.0, 'fiddle_leaf': 1.8, 'hedge': 1.2,
}
# Ground-level roles whose footprints are not lawn.
GROUND_ROLES = {'site', 'court', 'step', 'porch', 'verandah', 'side-courtyard', 'landscape', 'plinth', 'planter', 'patio',
                'stone-pad', 'edging', 'lawn', 'deck', 'fixture', 'gate', 'carport', 'outdoor-furniture'}


def extrude(poly, z0, z1):
    vertices = []
    faces = []

    def tri(points):
        k = len(vertices)
        vertices.extend(points)
        faces.append([k, k + 1, k + 2])

    for part in get_parts(poly):
        if part.geom_type != 'Polygon' or part.area < 1e-8:
            continue
        for t in get_parts(constrained_delaunay_triangles(part)):
            a, b, c = list(t.exterior.coords)[:3]
            if np.cross(np.array(b) - a, np.array(c) - a) < 0:
                b, c = c, b
            tri([(a[0], a[1], z1), (b[0], b[1], z1), (c[0], c[1], z1)])
            tri([(c[0], c[1], z0), (b[0], b[1], z0), (a[0], a[1], z0)])
        for ring in [part.exterior, *part.interiors]:
            pts = list(ring.coords)
            for a, b in zip(pts, pts[1:]):
                tri([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1)])
                tri([(a[0], a[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)])
    m = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces), process=True)
    m.fix_normals()
    return m


def rounded_box(size, radius=.05):
    half = np.array(size) / 2
    core = np.maximum(half - radius, .0001)
    verts = []
    faces = []
    uv = np.linspace(-1, 1, 7)
    for axis in range(3):
        others = [i for i in range(3) if i != axis]
        for sign in (-1, 1):
            base = len(verts)
            for a in uv:
                for b in uv:
                    p = np.zeros(3)
                    p[axis] = sign * half[axis]
                    p[others[0]] = a * half[others[0]]
                    p[others[1]] = b * half[others[1]]
                    q = np.clip(p, -core, core)
                    d = p - q
                    p = q + radius * d / max(np.linalg.norm(d), 1e-9)
                    verts.append(p)
            for i in range(6):
                for j in range(6):
                    k = base + i * 7 + j
                    faces += [[k, k + 1, k + 8], [k, k + 8, k + 7]]
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.fix_normals()
    return m


def frustum(bottom, top, height, sides=4, rot=math.pi / 4):
    """Closed tapered prism (planters, lantern caps)."""
    verts = []
    for z, r in ((0, bottom), (height, top)):
        for i in range(sides):
            a = rot + i * 2 * math.pi / sides
            verts.append((math.cos(a) * r, math.sin(a) * r, z))
    faces = []
    for i in range(sides):
        j = (i + 1) % sides
        faces += [[i, j, sides + j], [i, sides + j, sides + i]]
    for i in range(1, sides - 1):
        faces += [[0, i + 1, i], [sides, sides + i, sides + i + 1]]
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.fix_normals()
    return m


def material_library(style: dict, interior: dict, modern: bool) -> dict:
    """Physically based surface descriptors. 'texture' is kept for legacy consumers."""
    im = interior.get('materials', {})
    leaf, leaf_light = style.get('site_leaf', '#5b734a'), style.get('site_leaf_light', '#89955f')
    return {
        'wall': {'color': style['wall'], 'roughness': .88, 'texture': 'plaster', 'kind': 'render'},
        'ceiling': {'color': '#f5f3ef', 'roughness': .92, 'texture': 'plaster', 'kind': 'render', 'seed': 2},
        'slab': {'color': '#e6e4de', 'roughness': .9, 'texture': 'plaster', 'kind': 'render', 'seed': 8},
        'stone': {'color': style.get('stone', style['accent']), 'roughness': .78, 'texture': 'stone', 'kind': 'stone'},
        'basalt': {'color': '#4d4c49', 'roughness': .8, 'texture': 'stone', 'kind': 'stone', 'seed': 4},
        'step': {'color': '#a9a59d', 'roughness': .7, 'texture': 'stone', 'kind': 'stone', 'seed': 6},
        'timber': {'color': style.get('timber', style['wood']), 'roughness': .46, 'texture': 'wood', 'kind': 'wood'},
        'frame': {'color': style['frame'], 'roughness': .32, 'metallic': .3, 'kind': 'metal', 'params': [.36]},
        'roof': {'color': style['roof'], 'roughness': .77, 'texture': 'concrete', 'kind': 'render' if modern else 'concrete'},
        'floor': {'color': '#e6e2da' if modern else '#ddd6c4', 'alt': '#b8b2a8', 'roughness': .3, 'texture': 'tile', 'kind': 'tile',
                  'params': [2, .005, .32, .85], 'clearcoat': .2, 'clearcoat_roughness': .12},
        'woodfloor': {'color': im.get('woodfloor', '#a89170'), 'alt': '#8a6a4c', 'roughness': .4, 'texture': 'wood', 'kind': 'woodfloor'},
        'wetfloor': {'color': '#b9b7b1' if modern else '#aeb4aa', 'roughness': .56, 'texture': 'tile', 'kind': 'tile', 'params': [4, .01, 0, .35]},
        'tilewall': {'color': '#ebe8e2', 'alt': '#c9c5bd', 'roughness': .3, 'texture': 'tile', 'kind': 'tile', 'params': [4, .008, .15, .7]},
        'fabric': {'color': im.get('fabric', '#ded5bf'), 'roughness': .99, 'texture': 'fabric', 'kind': 'fabric'},
        'fabric-dark': {'color': im.get('fabric-dark', '#7c8870'), 'roughness': .94, 'texture': 'fabric', 'kind': 'fabric', 'seed': 3},
        'linen': {'color': im.get('linen', '#f2eee2'), 'roughness': .98, 'texture': 'fabric', 'kind': 'fabric', 'seed': 5, 'params': [180]},
        'rug': {'color': im.get('rug', '#b7a58b'), 'alt': '#9c8a70', 'roughness': .98, 'texture': 'fabric', 'kind': 'rug'},
        'glass': {'color': '#aec8cc', 'roughness': .12, 'alpha': .26, 'metallic': .1},
        'brass': {'color': '#b69c68', 'roughness': .28, 'metallic': .65, 'kind': 'brushed', 'params': [.3]},
        'ceramic': {'color': '#eeebe1', 'roughness': .25},
        'leaf': {'color': leaf, 'roughness': .9},
        'leaf-light': {'color': leaf_light, 'roughness': .9},
        'soil': {'color': style.get('site_soil', '#63553d'), 'alt': '#2f261d', 'roughness': 1., 'texture': 'stone', 'kind': 'soil'},
        'grass': {'color': '#5d7a3a', 'alt': '#a19c5e', 'roughness': 1., 'texture': 'grass', 'kind': 'grass'},
        'lawn': {'color': '#557a31', 'alt': '#a7a25c', 'roughness': 1., 'texture': 'grass', 'kind': 'grass', 'seed': 7},
        'asphalt': {'color': '#4a4d4c', 'alt': '#8b8a85', 'roughness': .97, 'texture': 'asphalt', 'kind': 'asphalt'},
        'paver': {'color': style.get('site_paving', '#aca998'), 'alt': '#9c998e', 'roughness': .75, 'texture': 'paver', 'kind': 'paver'},
        'cobble': {'color': style.get('site_paving', '#8e9194'), 'alt': '#6b7176', 'roughness': .6, 'texture': 'paver', 'kind': 'cobble'},
        'pebble': {'color': '#ebe8e1', 'alt': '#a19d94', 'roughness': .5, 'texture': 'stone', 'kind': 'pebbles'},
        'gravel': {'color': '#a09e98', 'alt': '#6e6c67', 'roughness': .85, 'texture': 'stone', 'kind': 'gravel'},
        'steppingstone': {'color': '#62625f', 'roughness': .8, 'texture': 'concrete', 'kind': 'concrete', 'seed': 9, 'tile_m': .9},
        'steel': {'color': '#232526', 'roughness': .45, 'metallic': .6, 'kind': 'metal', 'params': [.45]},
        'planter': {'color': '#f1f0ec', 'roughness': .7, 'texture': 'concrete', 'kind': 'concrete', 'seed': 11},
        'deck': {'color': '#7a5a3e', 'alt': '#5d412b', 'roughness': .7, 'texture': 'wood', 'kind': 'deck'},
        'encaustic': {'color': '#dddbd5', 'alt': '#4a4c50', 'roughness': .55, 'texture': 'tile', 'kind': 'encaustic'},
        'cladding': {'color': '#a39d92', 'alt': '#6f6b64', 'roughness': .9, 'texture': 'stone', 'kind': 'stoneclad'},
        'counter': {'color': '#f0eee9', 'alt': '#9d9b95', 'roughness': .15, 'texture': 'stone', 'kind': 'marble', 'clearcoat': .35},
        'cabinet': {'color': '#e7e2d8', 'roughness': .45, 'kind': 'metal', 'params': [.42]},
        'walnut': {'color': '#5b3e2b', 'roughness': .45, 'texture': 'wood', 'kind': 'wood', 'seed': 13},
        'oak': {'color': '#b48f67', 'roughness': .45, 'texture': 'wood', 'kind': 'wood', 'seed': 17},
        'stairtread': {'color': '#a98262', 'roughness': .4, 'texture': 'wood', 'kind': 'wood', 'seed': 19},
        'doorframe': {'color': '#efede8', 'roughness': .5, 'kind': 'metal', 'params': [.5]},
        'skirting': {'color': '#ecebe6', 'roughness': .5, 'kind': 'metal', 'params': [.5]},
        'appliance': {'color': '#c8cacb', 'roughness': .3, 'metallic': .9, 'kind': 'brushed', 'params': [.3]},
        'blackglass': {'color': '#0f1011', 'roughness': .06, 'metallic': .2},
        'mirror': {'color': '#e6ecee', 'roughness': .02, 'metallic': 1.0},
        'sling': {'color': '#d8cfbd', 'roughness': .95, 'texture': 'fabric', 'kind': 'fabric', 'seed': 21, 'params': [90]},
        'globe': {'color': '#ffd9a3', 'roughness': .3, 'emission': 1.1},
        'lamp': {'color': '#ffde9b', 'roughness': .5, 'emission': 1.},
        'art': {'color': '#b09a80', 'alt': '#3f4d57', 'roughness': .95, 'kind': 'art'},
        'art-2': {'color': '#c9b8a0', 'alt': '#7a5a44', 'roughness': .95, 'kind': 'art', 'seed': 31},
    }


class Kit:
    """Shared assets + transformed nodes + semantic side tables."""

    def __init__(self, seed_rng):
        self.rng = seed_rng
        self.assets = {}
        self.nodes = []
        self.colliders = []
        self.furniture = []
        self.lights = []
        self.vegetation = []
        self.ground = []  # (polygon, top z) of ground-level hardscape, for lawn derivation
        self.cube = self.asset(trimesh.creation.box(), 'unit-box')
        self.sphere = self.asset(trimesh.creation.uv_sphere(radius=1, count=[12, 16]), 'unit-sphere', True)
        self.cyl = self.asset(trimesh.creation.cylinder(radius=1, height=1, sections=20), 'unit-cylinder', True)

    def asset(self, mesh, key=None, smooth=False):
        key = key or sha({'v': np.round(mesh.vertices, 5).tolist(), 'f': mesh.faces.tolist()})[:20]
        if key not in self.assets:
            self.assets[key] = {'vertices': np.round(mesh.vertices, 6).tolist(), 'faces': mesh.faces.tolist(),
                                'normals': np.round(mesh.vertex_normals, 6).tolist() if smooth else None,
                                'closed': bool(mesh.is_watertight)}
        return key

    def node(self, key, mat, pos=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), floor=-1, role='detail', name=None, owner=None):
        ident = name or f'object-{len(self.nodes):05d}'
        self.nodes.append({'id': ident, 'asset': key, 'material': mat, 'position': [float(x) for x in pos],
                           'scale': [float(x) for x in scale], 'rotation': [float(x) for x in rot],
                           'floor': floor, 'role': role, 'owner': owner or ident})
        return ident

    def rect(self, bounds, mat, f=-1, role='detail', name=None, owner=None):
        a = np.array(bounds[:3], dtype=float)
        z = np.array(bounds[3:], dtype=float)
        size = z - a
        if min(size) <= 0:
            return None
        if f == -1 and role in GROUND_ROLES and a[2] < -.2:
            self.ground.append(box(a[0], a[1], z[0], z[1]))
        return self.node(self.cube, mat, (a + z) / 2, size, floor=f, role=role, name=name, owner=owner)

    def rb(self, center, size, mat, f=0, role='furniture', r=.04, rot=0, owner=None):
        key = self.asset(rounded_box(size, min(r, min(size) * .35)), smooth=True)
        return self.node(key, mat, center, rot=(0, 0, rot), floor=f, role=role, owner=owner)

    def cylinder(self, center, radius, height, mat, f=-1, role='detail', rot=(0, 0, 0)):
        return self.node(self.cyl, mat, center, (radius, radius, height), rot, f, role)

    def ball(self, center, size, mat, f=-1, role='landscape', rot=(0, 0, 0)):
        return self.node(self.sphere, mat, center, size, rot, f, role)

    def beam(self, p, q, r, mat, f=-1, role='detail'):
        p = np.array(p, dtype=float)
        q = np.array(q, dtype=float)
        d = q - p
        length = np.linalg.norm(d)
        if length < 1e-4:
            return None
        theta = math.acos(np.clip(d[2] / length, -1, 1))
        phi = math.atan2(d[1], d[0])
        return self.node(self.cyl, mat, (p + q) / 2, (r, r, length), (0, theta, phi), f, role)

    def poly_mesh(self, poly, z0, z1, mat, f=-1, role='wall', name=None, owner=None):
        if poly is None or poly.is_empty or poly.area < 1e-8:
            return None
        if f == -1 and role in GROUND_ROLES and z0 < -.2:
            self.ground.append(poly)
        return self.node(self.asset(extrude(poly, z0, z1)), mat, floor=f, role=role, name=name, owner=owner)

    def light(self, pos, power, color='#ffdfae', kind='fixture'):
        self.lights.append({'position': [float(x) for x in pos], 'color': color, 'power_w': power, 'fixture_visible': True, 'kind': kind})

    def obstacle(self, p, f, ident):
        self.colliders.append({'id': ident, 'floor': f, 'polygon': [[float(x), float(y)] for x, y in list(p.exterior.coords)[:-1]], 'kind': 'furniture'})

    def furnishing(self, kind, room, p):
        self.furniture.append({'id': f'{room["id"]}/{kind}', 'kind': kind, 'floor': room['floor'], 'room_id': room['id'],
                               'footprint': [[float(x), float(y)] for x, y in list(p.exterior.coords)[:-1]]})
        self.obstacle(p, room['floor'], self.furniture[-1]['id'])

    def plant(self, x, y, z, species, height=None, f=-1, pot=None, scale=None, rotation=None, options=None):
        """A procedural plant instance (grown by the viewer) plus a coordination proxy for GLB/drawings.

        pot: None, or (radius, height, material) for a vessel whose soil top becomes the plant base.
        """
        idx = len(self.vegetation)
        top = z
        if pot:
            pr, ph, pm = pot
            vessel = trimesh.creation.cylinder(radius=pr, height=ph, sections=28)
            self.node(self.asset(vessel, smooth=True), pm, (x, y, z + ph / 2), floor=f, role='landscape')
            self.cylinder((x, y, z + ph - .02), pr * .9, .012, 'soil', f, 'landscape')
            top = z + ph - .015
        nominal = SPECIES_HEIGHT.get(species, 1.)
        s = scale if scale is not None else (height / nominal if height else 1.)
        seed = int(sha({'plant': idx, 'x': round(x, 3), 'y': round(y, 3), 'species': species})[:8], 16)
        rot = rotation if rotation is not None else (seed % 6283) / 1000
        item = {'id': f'plant-{idx:03d}', 'species': species, 'position': [round(x, 4), round(y, 4), round(top, 4)],
                'scale': round(s, 4), 'rotation': round(rot, 4), 'seed': seed, 'floor': f}
        if options:
            item['options'] = options
        self.vegetation.append(item)
        h = nominal * s
        canopy = {'frangipani': .45, 'tree_standard': .3, 'tree_shade': .4, 'palm': .3}.get(species, .5)
        r = max(.12, h * canopy * .5)
        if species in ('frangipani', 'tree_standard', 'tree_shade', 'palm', 'fiddle_leaf'):
            self.node(self.cyl, 'timber', (x, y, top + h * .3), (max(.02, h * .018), max(.02, h * .018), h * .6), floor=f, role='plant-proxy')
            self.node(self.sphere, 'leaf', (x, y, top + h * .72), (r, r, h * .3), floor=f, role='plant-proxy')
        else:
            self.node(self.sphere, 'leaf', (x, y, top + h * .5), (r, r, h * .5), floor=f, role='plant-proxy')
        return item

    def hedge(self, x, y, z, size, rotation=0, f=-1):
        idx = len(self.vegetation)
        seed = int(sha({'hedge': idx, 'x': round(x, 3), 'y': round(y, 3)})[:8], 16)
        L, Wd, Hh = size
        self.vegetation.append({'id': f'hedge-{idx:03d}', 'species': 'hedge', 'position': [round(x, 4), round(y, 4), round(z, 4)],
                                'size': [round(L, 3), round(Wd, 3), round(Hh, 3)], 'rotation': round(rotation, 4), 'seed': seed, 'floor': f})
        self.node(self.cube, 'leaf', (x, y, z + Hh / 2), (L, Wd, Hh), (0, 0, rotation), floor=f, role='plant-proxy')
