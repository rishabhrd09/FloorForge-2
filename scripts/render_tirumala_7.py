"""Render the 26 furnished floor cutaways, exterior, and interior views for Tirumala 7 using Blender Cycles.
Run: /opt/homebrew/bin/blender -b -P scripts/render_tirumala_7.py [-- --gpu ground first second exterior ...]
"""
import json
import math
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import render_cycles as rendering
from render_tirumala_5_cycles import prepare_tirumala_materials

SAMPLE = ROOT / 'examples/gallery/tirumala-7'
OUT = SAMPLE / 'renders'
OUT.mkdir(exist_ok=True)
data = json.loads((SAMPLE / 'scene.json').read_text())
nodes = {n['id']: n for n in data['nodes']}
requested = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
args = SimpleNamespace(width=1200, height=920, samples=24, gpu='--gpu' in requested)
grade = rendering.GRADES['day'].copy()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SAMPLE / 'model.glb'))
scene = bpy.context.scene
H = float(data.get('floor_height', 3.15))

prepare_tirumala_materials(data, grade)
rendering.configure(args, grade)
rendering.sky(data, grade)
rendering.fixtures(data, dict(grade, lamps=0.35))

# Convert local PDF feet (x_ft east of west line, y_ft south of north line) to building metres (+X north, +Y west)
FT = 0.3048
def lm(x_ft: float, y_ft: float, z: float) -> tuple[float, float, float]:
    return ((40.0 - y_ft) * FT, (50.0 - x_ft) * FT, z)

# Architectural daylight & warm interior fill lights across all three floors and the 12' x 5' rooflight shaft
area_lights = [
    # Rooflight shaft daylight pouring down through 2nd and 1st floor into dining
    ('Rooflight top sun', lm(27.0, 28.5, 2 * H + 0.35), lm(27.0, 28.5, 0.5), 3.2, 680, (1.0, 0.97, 0.91)),
    ('Rooflight mid shaft', lm(27.0, 28.5, H + 0.20), lm(27.0, 28.5, 0.2), 2.8, 460, (1.0, 0.96, 0.89)),
    # Ground floor rooms
    ('Kitchen fill', lm(42.5, 27.5, 2.75), lm(48.5, 27.0, 1.10), 2.6, 420, (1.0, 0.95, 0.86)),
    ('Work bay fill', lm(44.0, 23.0, 2.75), lm(48.5, 23.0, 1.10), 2.2, 320, (1.0, 0.96, 0.88)),
    ('Dining warm fill', lm(28.0, 29.0, 2.85), lm(31.0, 28.0, 1.00), 2.5, 360, (1.0, 0.94, 0.84)),
    ('Living hall fill', lm(15.5, 21.0, 2.80), lm(13.0, 22.0, 1.00), 3.0, 440, (1.0, 0.95, 0.86)),
    ('Home ICU fill', lm(31.5, 17.5, 2.80), lm(34.0, 17.5, 1.00), 3.2, 480, (1.0, 0.97, 0.92)),
    ('Verandah daylight', lm(31.0, 4.5, 2.85), lm(28.0, 7.0, 1.00), 3.4, 420, (1.0, 0.98, 0.94)),
    ('Drawing room fill', lm(12.8, 9.0, 2.80), lm(12.5, 6.0, 1.00), 2.6, 380, (1.0, 0.95, 0.87)),
    ('Ground master fill', lm(9.5, 33.0, 2.80), lm(9.5, 35.5, 1.00), 2.8, 400, (1.0, 0.95, 0.86)),
    # First floor rooms
    ('First gallery fill', lm(20.0, 22.0, H + 2.80), lm(24.0, 26.0, H + 1.00), 2.8, 380, (1.0, 0.96, 0.88)),
    ('First master fill', lm(11.5, 9.5, H + 2.80), lm(11.0, 6.5, H + 1.00), 3.2, 440, (1.0, 0.95, 0.87)),
    ('Study meditation fill', lm(31.5, 14.5, H + 2.80), lm(34.0, 13.0, H + 1.00), 2.8, 400, (1.0, 0.96, 0.89)),
    ('Medium bedroom fill', lm(8.5, 34.5, H + 2.80), lm(6.0, 35.5, H + 1.00), 2.6, 380, (1.0, 0.95, 0.87)),
    # Second floor rooms
    ('Office TV hall west', lm(11.0, 17.0, 2 * H + 2.80), lm(16.0, 16.0, 2 * H + 1.00), 3.4, 450, (1.0, 0.96, 0.88)),
    ('Office TV hall east', lm(24.0, 17.0, 2 * H + 2.80), lm(28.0, 17.0, 2 * H + 1.00), 3.4, 450, (1.0, 0.96, 0.88)),
    ('Stair lobby fill', lm(24.5, 36.5, 2 * H + 2.80), lm(22.0, 36.5, 2 * H + 1.00), 2.6, 380, (1.0, 0.96, 0.89)),
]
for name, pos, aim, size, power, rgb in area_lights:
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = power
    light.size = size
    light.color = rgb
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (Vector(aim) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()

# Configure PBR shaders for video-matched materials and standard surfaces
for mat in bpy.data.materials:
    props = data['materials'].get(mat.name, {})
    typ = props.get('kind', '')
    shader = rendering.principled(mat)
    if not shader:
        continue
    if not props.get('alpha') and props.get('color') and mat.name not in ('lamp', 'globe', 'cove_led_warm'):
        shader.inputs['Base Color'].default_value = (*rendering.linear(props['color']), 1)
    if 'roughness' in props and 'Roughness' in shader.inputs:
        shader.inputs['Roughness'].default_value = float(props['roughness'])
    if 'metallic' in props and 'Metallic' in shader.inputs:
        shader.inputs['Metallic'].default_value = float(props['metallic'])
    if 'clearcoat' in props:
        for cc_key in ('Coat Weight', 'Clearcoat'):
            if cc_key in shader.inputs:
                shader.inputs[cc_key].default_value = float(props['clearcoat'])
    if mat.name == 'cove_led_warm' or props.get('emissive'):
        em_col = rendering.linear(props.get('emissive', '#ffd89b'))
        for em_key in ('Emission Color', 'Emission'):
            if em_key in shader.inputs:
                shader.inputs[em_key].default_value = (*em_col, 1)
        if 'Emission Strength' in shader.inputs:
            shader.inputs['Emission Strength'].default_value = float(props.get('emissive_strength', 3.5))
        continue
    if props.get('alpha') and props['alpha'] < 0.95:
        shader.inputs['Alpha'].default_value = float(props['alpha'])
        for tr_key in ('Transmission Weight', 'Transmission'):
            if tr_key in shader.inputs:
                shader.inputs[tr_key].default_value = 0.72
        continue
    if typ not in ('wood', 'woodfloor', 'stone', 'tile', 'fabric', 'rug', 'paver', 'render', 'grass', 'concrete', 'soil', 'marble'):
        continue
    tree = mat.node_tree
    coord = tree.nodes.new('ShaderNodeTexCoord')
    stretch = tree.nodes.new('ShaderNodeVectorMath')
    stretch.operation = 'MULTIPLY'
    stretch.inputs[1].default_value = (2, 22, 11) if typ in ('wood', 'woodfloor') else (8, 8, 8)
    tree.links.new(coord.outputs['Generated'], stretch.inputs[0])
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 2.8
    noise.inputs['Detail'].default_value = 4.0
    tree.links.new(stretch.outputs[0], noise.inputs['Vector'])
    ramp = tree.nodes.new('ShaderNodeValToRGB')
    rgb = list(shader.inputs['Base Color'].default_value)[:3]
    for el, t in zip(ramp.color_ramp.elements, [0.82, 1.12]):
        el.color = (*[min(1, v * t) for v in rgb], 1)
    tree.links.new(noise.outputs['Fac'], ramp.inputs[0])
    tree.links.new(ramp.outputs[0], shader.inputs['Base Color'])
    bump = tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.14
    bump.inputs['Distance'].default_value = 0.010
    tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    tree.links.new(bump.outputs[0], shader.inputs['Normal'])

# Lay large straight-jointed 800x800 stone/vitrified slabs in Cycles stills
for name in ('floor_ivory_vitrified_800', 'ivory-vitrified', 'flagstone', 'floor', 'ivory-vitrified-matte', 'terrace_grey_paver', 'travertine_warm'):
    material = bpy.data.materials.get(name)
    if not material:
        continue
    spec = data['materials'].get(name, {})
    tile_m = spec.get('tile_m') or spec.get('tile') or [0.80, 0.80]
    w, h = tile_m[0], tile_m[1]
    nt = material.node_tree
    shader = rendering.principled(material)
    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.offset = 0
    brick.inputs['Scale'].default_value = 1
    brick.inputs['Brick Width'].default_value = w
    brick.inputs['Row Height'].default_value = h
    brick.inputs['Mortar Size'].default_value = 0.0025
    color = rendering.linear(spec.get('color', '#eceae4'))
    brick.inputs['Color1'].default_value = (*color, 1)
    brick.inputs['Color2'].default_value = (*[v * 0.968 for v in color], 1)
    brick.inputs['Mortar'].default_value = (*[v * 0.72 for v in color], 1)
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    nt.links.new(geo.outputs['Position'], brick.inputs['Vector'])
    nt.links.new(brick.outputs['Color'], shader.inputs['Base Color'])

objects = {o.name: o for o in scene.objects if o.type == 'MESH'}
# Replace each preview foliage proxy with a branched cluster of individual leaves
for name, obj in list(objects.items()):
    node = nodes.get(name, {})
    if node.get('role') != 'plant-proxy' or node.get('material') != 'leaf':
        continue
    rng = random.Random(name)
    verts, faces, indices = [], [], []
    for i in range(420):
        a = rng.uniform(0, 2 * math.pi)
        z = rng.uniform(-1, 1)
        rad = math.sqrt(1 - z * z) * rng.uniform(0.3, 1.0)
        c = Vector((rad * math.cos(a), rad * math.sin(a), z * 0.9))
        sideways = Vector((-math.sin(a), math.cos(a), 0)) * rng.uniform(0.055, 0.11)
        axis = Vector((math.cos(a), math.sin(a), rng.uniform(-0.9, 0.4))) * rng.uniform(0.14, 0.32)
        n = len(verts)
        verts.extend([c - axis, c + sideways, c + axis, c - sideways, c + Vector((0, 0, 0.045))])
        faces.extend([(n, n + 1, n + 4), (n + 1, n + 2, n + 4), (n + 2, n + 3, n + 4), (n + 3, n, n + 4)])
        indices.extend([i % 2] * 4)
    mesh = bpy.data.meshes.new('Leaf canopy')
    mesh.from_pydata(verts, [], faces)
    for k in ('leaf', 'leaf-light'):
        mesh.materials.append(bpy.data.materials.get(k) or bpy.data.materials['leaf'])
    for poly, mi in zip(mesh.polygons, indices):
        poly.material_index = mi
    obj.data = mesh


def garden_backdrop():
    """Plant neighbouring plots in exterior stills; keep them off the house plans."""
    rng = random.Random(702)
    branches = bpy.data.curves.new('Neighbouring trees', 'CURVE')
    branches.dimensions = '3D'
    branches.bevel_depth = 0.12
    branches.bevel_resolution = 1
    branch_obj = bpy.data.objects.new('Off-site branches', branches)
    scene.collection.objects.link(branch_obj)
    branches.materials.append(bpy.data.materials.get('smoked-oak') or bpy.data.materials.get('Walnut'))
    verts, faces, swatches = [], [], []

    def stem(points, radii):
        spline = branches.splines.new('POLY')
        spline.points.add(len(points) - 1)
        for point, position, radius in zip(spline.points, points, radii):
            point.co = (*position, 1)
            point.radius = radius

    for x, y, h in [(-4, 6, 7.2), (-5, 15, 8.1), (-1, 20, 6.5), (6, 21, 8.8), (12, 23, 6.2), (-11, 1, 6.8), (-8, 26, 9)]:
        base = Vector((x, y, -0.39))
        trunk = base + Vector((0.15, 0.04, h * 0.56))
        stem([base, trunk], [1.5, 0.65])
        for j in range(22):
            angle = j * 2.399963
            extent = h * rng.uniform(0.18, 0.41)
            b = trunk + Vector((extent * math.cos(angle), extent * math.sin(angle), h * rng.uniform(-0.09, 0.39)))
            fork = trunk.lerp(b, 0.47) + Vector((0, 0, 0.35))
            stem([trunk, fork, b], [0.66, 0.40, 0.10])
            for _ in range(420):
                phi = rng.random() * math.tau
                dz = rng.uniform(-1, 1)
                rho = math.sqrt(1 - dz * dz) * rng.random() ** 0.333
                ctr = b + Vector((math.cos(phi) * rho, math.sin(phi) * rho, dz * 0.73)) * h * 0.175
                length = rng.uniform(0.062, 0.13)
                yaw = rng.random() * math.tau
                along = Vector((math.cos(yaw), math.sin(yaw), rng.uniform(-0.9, 0.6))) * length
                across = Vector((-math.sin(yaw), math.cos(yaw), 0.1)) * length * 0.45
                n = len(verts)
                verts.extend([ctr - along, ctr + across, ctr + axis if False else ctr + along, ctr - across, ctr + Vector((0, 0, 0.014))])
                faces.extend([(n, n + 1, n + 4), (n + 1, n + 2, n + 4), (n + 2, n + 3, n + 4), (n + 3, n, n + 4)])
                swatches.extend([rng.randrange(4)] * 4)
    mesh = bpy.data.meshes.new('Garden canopy')
    mesh.from_pydata(verts, [], faces)
    for rgb in [(53, 76, 44), (72, 93, 49), (92, 111, 64), (108, 118, 70)]:
        mat = bpy.data.materials.new('Garden foliage')
        lin = (*[(v / 255) ** 2.2 for v in rgb], 1)
        mat.diffuse_color = lin
        sh = rendering.principled(mat)
        if sh:
            sh.inputs['Base Color'].default_value = lin
            sh.inputs['Roughness'].default_value = 0.68
        mesh.materials.append(mat)
    for poly, idx in zip(mesh.polygons, swatches):
        poly.material_index = idx
    leaves = bpy.data.objects.new('Off-site foliage', mesh)
    scene.collection.objects.link(leaves)
    return branch_obj, leaves


ALL_VIEWS = [
    # Plan cutaways (3)
    'ground', 'first', 'second',
    # Exterior (5)
    'exterior', 'east_arrival', 'north_frontage', 'colony_overview', 'roof_terraces',
    # Ground floor (9)
    'kitchen_run', 'kitchen_from_dining', 'dining_double_height', 'living_hall',
    'living_to_icu', 'icu', 'verandah', 'drawing_room', 'master_bedroom',
    # First floor (5)
    'gallery_void', 'master_suite', 'study_meditation', 'medium_bedroom', 'east_terrace',
    # Second floor (4)
    'office_tv_hall', 'north_terrace', 'rooflight', 'stair_lobby',
]
views = [v for v in requested if v != '--gpu'] or ALL_VIEWS

cut_roles = {'wall', 'joinery', 'glass', 'door', 'curtain', 'wall-tile', 'wall-panel', 'post', 'window-surround', 'sill', 'pipe', 'window-hood', 'parapet'}
overheads = {'roof', 'ceiling', 'cove', 'downlight', 'ceiling-feature', 'canopy', 'band'}
exterior_views = {'exterior', 'east_arrival', 'north_frontage', 'colony_overview', 'roof_terraces'}

for view in views:
    floor = {'ground': 0, 'first': 1, 'second': 2}.get(view)
    cam = bpy.data.cameras.new(view)
    camera = bpy.data.objects.new(view, cam)
    scene.collection.objects.link(camera)
    scene.camera = camera
    originals = {}
    z = (floor or 0) * H

    for light in scene.objects:
        if light.type == 'LIGHT' and light.data.type != 'SUN':
            light.hide_render = floor is not None
    backdrop = garden_backdrop() if view in exterior_views else []

    for name, obj in objects.items():
        n = nodes.get(name)
        if not n:
            continue
        role = n['role']
        f = n['floor']
        obj.hide_render = False
        if floor is None:
            continue
        obj.hide_render = (
            f != floor
            and not (floor == 0 and role in ('plinth', 'vehicle'))
            and not (floor > 0 and f == floor - 1 and role == 'stair')
        ) or role in overheads
        if obj.hide_render:
            continue
        bb = [(obj.matrix_world @ Vector(c)).z for c in obj.bound_box]
        lo, hi = min(bb), max(bb)
        if (lo > z + 1.35 and 'chandelier' not in name and role != 'stair') or (role in cut_roles and lo > z + 0.98):
            obj.hide_render = True
            continue
        if (role not in cut_roles and hi < z + 1.35) or hi < z + 1.0 or 'chandelier' in name or role == 'stair':
            continue
        original = obj.data
        mesh = original.copy()
        originals[name] = original
        obj.data = mesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        m = obj.matrix_world
        up = Vector((0, 0, 1))
        out = bmesh.ops.bisect_plane(
            bm,
            geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
            plane_co=m.inverted() @ Vector((0, 0, z + 1.0)),
            plane_no=m.to_3x3().transposed() @ up,
            clear_outer=True,
            dist=0.00001,
        )
        edges = [e for e in out['geom_cut'] if isinstance(e, bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
        if edges:
            bmesh.ops.holes_fill(bm, edges=edges)
        bm.to_mesh(mesh)
        bm.free()

    if floor is not None:
        target = Vector((6.10, 7.62, z + 0.22))
        eye = target + Vector((-5.8, -0.6, 19.0))
        cam.type = 'ORTHO'
        cam.ortho_scale = 20.6 if floor == 0 else 20.0
        bpy.ops.mesh.primitive_plane_add(size=200, location=(6, 7.6, z - 0.35))
        ground = bpy.context.object
        ground.name = 'Studio surface'
        mat = bpy.data.materials.get('Studio oatmeal') or bpy.data.materials.new('Studio oatmeal')
        mat.diffuse_color = (0.52, 0.46, 0.37, 1)
        ground.data.materials.append(mat)
    else:
        cfg = data['cameras'][view]
        eye = Vector(cfg['position'])
        target = Vector(cfg['target'])
        cam.lens = 28 if view in exterior_views else 20
        if view in exterior_views:
            sun = next(o for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN')
            sun.rotation_euler = Vector((-1.1, 0.83, -1.26)).to_track_quat('-Z', 'Y').to_euler()
            sun.data.angle = math.radians(2.2)

    if floor is None:
        bpy.ops.mesh.primitive_plane_add(size=1800, location=(6, 7.6, -0.397))
        ground = bpy.context.object
        mat = bpy.data.materials.get('Studio oatmeal') or bpy.data.materials.new('Studio oatmeal')
        mat.diffuse_color = (0.34, 0.32, 0.25, 1)
        ground.data.materials.append(mat)

    camera.location = eye
    camera.rotation_euler = (target - eye).to_track_quat('-Z', 'Y').to_euler()
    scene.view_settings.exposure = (
        -1.15 if floor is not None
        else -0.55 if view in exterior_views
        else -0.35 if view in ('verandah', 'east_terrace', 'north_terrace', 'rooflight')
        else 0.05
    )
    scene.render.filepath = str(OUT / (view + '.png'))
    bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(ground, do_unlink=True)
    for name, old in originals.items():
        temp = objects[name].data
        objects[name].data = old
        bpy.data.meshes.remove(temp)
    bpy.data.objects.remove(camera, do_unlink=True)
    for obj in backdrop:
        bpy.data.objects.remove(obj, do_unlink=True)

    if view == 'exterior':
        thumb = bpy.data.images.load(str(OUT / 'exterior.png'))
        thumb.scale(720, 552)
        thumb.filepath_raw = str(SAMPLE.parent / 'thumbnails/tirumala-7.png')
        thumb.file_format = 'PNG'
        thumb.save()
