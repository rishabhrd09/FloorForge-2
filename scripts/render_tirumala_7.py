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
args = SimpleNamespace(width=1200, height=920, samples=36, gpu='--gpu' in requested)
grade = rendering.GRADES['day'].copy()

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SAMPLE / 'model.glb'))
scene = bpy.context.scene
H = float(data.get('floor_height', 3.15))

prepare_tirumala_materials(data, grade)
rendering.configure(args, grade)
rendering.sky(data, grade)
rendering.fixtures(data, dict(grade, lamps=0.30))

FT = 0.3048
def lm(x_ft: float, y_ft: float, z: float) -> tuple[float, float, float]:
    return ((40.0 - y_ft) * FT, (50.0 - x_ft) * FT, z)

# Architectural daylight & warm interior fill lights tuned to the full-span atrium & east kitchen windows
area_lights = [
    # Full-span 13.5' x 8' sunroof pouring natural sky light down through First Floor into the Dining Atrium
    ('Sunroof top sky', lm(26.5, 29.0, 2 * H + 0.32), lm(26.2, 29.0, 0.4), 3.6, 540, (1.0, 0.98, 0.93)),
    ('Atrium mid shaft', lm(25.8, 29.0, H + 0.25), lm(26.2, 29.0, 0.2), 3.0, 380, (1.0, 0.96, 0.90)),
    # Ground floor rooms + morning east window daylight into kitchen
    ('Kitchen east window light', lm(48.4, 28.5, 1.85), lm(42.0, 28.5, 0.95), 2.8, 360, (1.0, 0.98, 0.93)),
    ('Kitchen warm fill', lm(40.5, 28.5, 2.75), lm(45.5, 27.5, 1.05), 2.8, 300, (1.0, 0.95, 0.87)),
    ('Dining warm fill', lm(26.5, 29.0, 2.82), lm(28.0, 28.0, 0.95), 2.6, 280, (1.0, 0.94, 0.85)),
    ('Living hall fill', lm(15.5, 20.8, 2.76), lm(12.8, 23.5, 1.10), 3.0, 340, (1.0, 0.95, 0.87)),
    ('Home ICU fill', lm(31.5, 15.8, 2.78), lm(26.0, 15.2, 1.15), 3.2, 360, (1.0, 0.97, 0.92)),
    ('Verandah daylight', lm(31.0, 4.2, 2.82), lm(28.5, 3.0, 0.60), 3.4, 340, (1.0, 0.98, 0.94)),
    ('Drawing room fill', lm(12.8, 9.0, 2.78), lm(12.5, 5.5, 1.00), 2.6, 300, (1.0, 0.95, 0.88)),
    ('Ground master fill', lm(9.5, 33.0, 2.78), lm(9.5, 36.0, 1.00), 2.8, 320, (1.0, 0.95, 0.87)),
    # First floor rooms
    ('First gallery fill', lm(20.5, 22.5, H + 2.78), lm(25.5, 27.5, H + 1.00), 2.8, 310, (1.0, 0.96, 0.89)),
    ('First master fill', lm(11.5, 9.5, H + 2.78), lm(11.5, 6.0, H + 1.00), 3.2, 350, (1.0, 0.95, 0.88)),
    ('Study meditation fill', lm(31.5, 14.5, H + 2.78), lm(34.0, 12.5, H + 1.00), 2.8, 320, (1.0, 0.96, 0.90)),
    ('Medium bedroom fill', lm(8.5, 34.5, H + 2.78), lm(5.5, 35.5, H + 1.00), 2.6, 300, (1.0, 0.95, 0.88)),
    # Second floor rooms
    ('Office TV hall west', lm(11.5, 16.5, 2 * H + 2.78), lm(15.0, 15.0, 2 * H + 1.05), 3.4, 340, (1.0, 0.96, 0.89)),
    ('Office TV hall east', lm(24.5, 18.5, 2 * H + 2.78), lm(32.5, 19.0, 2 * H + 1.25), 3.4, 360, (1.0, 0.96, 0.89)),
    ('Stair lobby fill', lm(25.0, 36.5, 2 * H + 2.78), lm(20.0, 36.5, 2 * H + 1.00), 2.6, 300, (1.0, 0.96, 0.90)),
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
    if hasattr(obj, 'visible_camera'):
        obj.visible_camera = False
    if hasattr(obj, 'visible_glossy'):
        obj.visible_glossy = False

# Configure PBR shaders for architectural & video-matched materials
for mat in bpy.data.materials:
    base_name = (mat.name or '').split('.')[0]
    if base_name in ('glass', 'railglass', 'frosted', 'context-glass'):
        continue
    props = data['materials'].get(mat.name, {})
    typ = props.get('kind', '')
    shader = rendering.principled(mat)
    if not shader:
        continue
    if base_name == 'tv_oled_screen':
        shader.inputs['Base Color'].default_value = (0.004, 0.005, 0.007, 1.0)
        if 'Roughness' in shader.inputs:
            shader.inputs['Roughness'].default_value = 0.25
        if 'Metallic' in shader.inputs:
            shader.inputs['Metallic'].default_value = 0.04
        for cc_key in ('Coat Weight', 'Clearcoat'):
            if cc_key in shader.inputs:
                shader.inputs[cc_key].default_value = 0.06
        continue
    if base_name == 'blackglass':
        shader.inputs['Base Color'].default_value = (0.006, 0.008, 0.011, 1.0)
        if 'Roughness' in shader.inputs:
            shader.inputs['Roughness'].default_value = 0.06
        if 'Metallic' in shader.inputs:
            shader.inputs['Metallic'].default_value = 0.15
        for cc_key in ('Coat Weight', 'Clearcoat'):
            if cc_key in shader.inputs:
                shader.inputs[cc_key].default_value = 0.90
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
            shader.inputs['Emission Strength'].default_value = float(props.get('emissive_strength', 3.2))
        continue
    if props.get('alpha') and props['alpha'] < 0.95:
        shader.inputs['Alpha'].default_value = float(props['alpha'])
        for tr_key in ('Transmission Weight', 'Transmission'):
            if tr_key in shader.inputs:
                shader.inputs[tr_key].default_value = 0.76
        continue
    if typ not in ('wood', 'woodfloor', 'stone', 'tile', 'fabric', 'rug', 'paver', 'render', 'grass', 'concrete', 'soil', 'marble'):
        continue
    tree = mat.node_tree
    coord = tree.nodes.new('ShaderNodeTexCoord')
    stretch = tree.nodes.new('ShaderNodeVectorMath')
    stretch.operation = 'MULTIPLY'
    stretch.inputs[1].default_value = (2, 22, 11) if typ in ('wood', 'woodfloor') else (18, 18, 18) if typ == 'grass' else (8, 8, 8)
    tree.links.new(coord.outputs['Generated'], stretch.inputs[0])
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 6.5 if typ == 'grass' else 2.8
    noise.inputs['Detail'].default_value = 5.0 if typ == 'grass' else 4.0
    tree.links.new(stretch.outputs[0], noise.inputs['Vector'])
    ramp = tree.nodes.new('ShaderNodeValToRGB')
    rgb = list(shader.inputs['Base Color'].default_value)[:3]
    for el, t in zip(ramp.color_ramp.elements, [0.85, 1.10]):
        el.color = (*[min(1, v * t) for v in rgb], 1)
    tree.links.new(noise.outputs['Fac'], ramp.inputs[0])
    tree.links.new(ramp.outputs[0], shader.inputs['Base Color'])
    bump = tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.22 if typ == 'grass' else 0.13
    bump.inputs['Distance'].default_value = 0.008
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


def add_box_mesh(name: str, bounds: tuple[float, float, float, float, float, float], mat) -> bpy.types.Object:
    x0, y0, z0, x1, y1, z1 = bounds
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    m = bpy.data.meshes.new(name)
    m.from_pydata(verts, [], faces)
    if mat:
        m.materials.append(mat)
    o = bpy.data.objects.new(name, m)
    scene.collection.objects.link(o)
    return o


def exterior_context():
    """Build brushed-concrete North & East colony roads, paver footpaths, and distant mature off-site trees for exterior stills."""
    created = []
    road_mat = bpy.data.materials.get('Studio road')
    if not road_mat:
        road_mat = bpy.data.materials.new('Studio road')
        sh = rendering.principled(road_mat)
        if sh:
            sh.inputs['Base Color'].default_value = (*rendering.linear('#9b968d'), 1)
            sh.inputs['Roughness'].default_value = 0.78
    verge_mat = bpy.data.materials.get('travertine_warm') or road_mat

    # 12 m North Colony Road (X = 13.35..24.20 m) & 9 m East Colony Road (X = -16.0..13.35 m, non-overlapping!) + stone footpath verges
    created.append(add_box_mesh('North road carriageway', (13.35, -24.0, -0.36, 24.20, 32.0, -0.302), road_mat))
    created.append(add_box_mesh('East road carriageway', (-16.0, -9.00, -0.36, 13.35, -0.90, -0.302), road_mat))
    created.append(add_box_mesh('North footpath west of ramp', (12.192, 3.22, -0.34, 13.35, 16.0, -0.285), verge_mat))
    created.append(add_box_mesh('East footpath verge', (-2.0, -0.90, -0.34, 13.35, 0.0, -0.295), verge_mat))
    created.append(add_box_mesh('North avenue opposite verge', (24.20, -20.0, -0.34, 26.20, 28.0, -0.285), verge_mat))

    # Distant mature off-site canopy trees across the colony avenue & adjoining parcels (NO round shrub spheres!)
    rng = random.Random(702)
    branches = bpy.data.curves.new('Neighbouring trees', 'CURVE')
    branches.dimensions = '3D'
    branches.bevel_depth = 0.11
    branches.bevel_resolution = 1
    branch_obj = bpy.data.objects.new('Off-site branches', branches)
    scene.collection.objects.link(branch_obj)
    branches.materials.append(bpy.data.materials.get('smoked-oak') or bpy.data.materials.get('Walnut'))
    created.append(branch_obj)
    verts, faces, swatches = [], [], []

    def stem(points, radii):
        spline = branches.splines.new('POLY')
        spline.points.add(len(points) - 1)
        for point, position, radius in zip(spline.points, points, radii):
            point.co = (*position, 1)
            point.radius = radius

    for x, y, h in [
        (-4.5, 6.0, 7.2), (-5.2, 15.0, 8.0), (-1.5, 20.5, 6.6),
        (6.0, 21.5, 8.5), (12.0, 23.0, 6.4),
        (26.5, -5.0, 7.6), (26.2, 4.0, 7.8), (26.8, 12.5, 8.4), (26.0, 21.0, 7.4),
    ]:
        base = Vector((x, y, -0.35))
        trunk = base + Vector((0.14, 0.04, h * 0.56))
        stem([base, trunk], [1.4, 0.60])
        for j in range(20):
            angle = j * 2.399963
            extent = h * rng.uniform(0.18, 0.40)
            b_pt = trunk + Vector((extent * math.cos(angle), extent * math.sin(angle), h * rng.uniform(-0.08, 0.38)))
            fork = trunk.lerp(b_pt, 0.47) + Vector((0, 0, 0.34))
            stem([trunk, fork, b_pt], [0.62, 0.38, 0.09])
            for _ in range(380):
                phi = rng.random() * math.tau
                dz = rng.uniform(-1, 1)
                rho = math.sqrt(1 - dz * dz) * rng.random() ** 0.333
                ctr = b_pt + Vector((math.cos(phi) * rho, math.sin(phi) * rho, dz * 0.72)) * h * 0.17
                length = rng.uniform(0.06, 0.125)
                yaw = rng.random() * math.tau
                along = Vector((math.cos(yaw), math.sin(yaw), rng.uniform(-0.9, 0.6))) * length
                across = Vector((-math.sin(yaw), math.cos(yaw), 0.1)) * length * 0.45
                n = len(verts)
                verts.extend([ctr - along, ctr + across, ctr + along, ctr - across, ctr + Vector((0, 0, 0.014))])
                faces.extend([(n, n + 1, n + 4), (n + 1, n + 2, n + 4), (n + 2, n + 3, n + 4), (n + 3, n, n + 4)])
                swatches.extend([rng.randrange(4)] * 4)
    mesh = bpy.data.meshes.new('Garden canopy')
    mesh.from_pydata(verts, [], faces)
    for rgb in [(58, 76, 48), (74, 92, 54), (90, 106, 66), (104, 114, 72)]:
        mat = bpy.data.materials.new('Garden foliage')
        lin = (*[(v / 255) ** 2.2 for v in rgb], 1)
        mat.diffuse_color = lin
        sh = rendering.principled(mat)
        if sh:
            sh.inputs['Base Color'].default_value = lin
            sh.inputs['Roughness'].default_value = 0.70
        mesh.materials.append(mat)
    for poly, idx in zip(mesh.polygons, swatches):
        poly.material_index = idx
    leaves = bpy.data.objects.new('Off-site foliage', mesh)
    scene.collection.objects.link(leaves)
    created.append(leaves)
    return created


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
context_views = exterior_views | {'verandah', 'east_terrace', 'north_terrace', 'rooflight'}

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
    backdrop = exterior_context() if view in context_views else []

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
            and not (floor == 0 and role in ('plinth', 'vehicle', 'gate', 'step'))
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
        sh = rendering.principled(mat)
        if sh:
            sh.inputs['Base Color'].default_value = (0.48, 0.44, 0.38, 1)
            sh.inputs['Roughness'].default_value = 0.88
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
        mat = bpy.data.materials.get('Studio urban earth') or bpy.data.materials.new('Studio urban earth')
        sh = rendering.principled(mat)
        if sh:
            sh.inputs['Base Color'].default_value = (0.36, 0.33, 0.28, 1)
            sh.inputs['Roughness'].default_value = 0.90
        ground.data.materials.append(mat)

    camera.location = eye
    camera.rotation_euler = (target - eye).to_track_quat('-Z', 'Y').to_euler()
    scene.view_settings.exposure = (
        -1.10 if floor is not None
        else -0.60 if view in exterior_views
        else -0.42 if view in ('verandah', 'east_terrace', 'north_terrace', 'rooflight')
        else -0.22
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
        m_data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(m_data, bpy.types.Mesh):
            bpy.data.meshes.remove(m_data)
        elif isinstance(m_data, bpy.types.Curve):
            bpy.data.curves.remove(m_data)

    if view == 'exterior':
        thumb = bpy.data.images.load(str(OUT / 'exterior.png'))
        thumb.scale(720, 552)
        thumb.filepath_raw = str(SAMPLE.parent / 'thumbnails/tirumala-7.png')
        thumb.file_format = 'PNG'
        thumb.save()
