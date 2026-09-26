"""Path-traced stills of a generated home with Blender Cycles.

Renders the realistic viewer's presentation GLB (``scripts/export_presentation.mjs``: GPU-synthesised textures,
grown planting, lawn grass and nearby context) under Blender's physical Nishita sky with the site's computed
sun, lights every visible fixture from ``scene.json``, and writes PNG stills.

    node scripts/export_presentation.mjs examples/demo/scene.json build/demo.glb
    python scripts/render_cycles.py --glb build/demo.glb --scene examples/demo/scene.json --out build/renders \\
        --view hero --grade day --width 1600 --height 900 --samples 128
    python scripts/render_cycles.py ... --view eye --eye 3.2,3.9,0,-95 --name living-day

or run the same arguments inside Blender: ``blender --background --python scripts/render_cycles.py -- ...``.
Needs Blender 4.2 or newer, or the ``bpy`` wheel from PyPI on Python 3.11. Cycles runs on the CPU unless
``--gpu`` is given; CPU stills take minutes. This is an offline presentation path: it does not change the
design, and the stills are renders of preliminary geometry, not photographs or approvals.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

WALK_EYE = 1.63     # metres above the finished floor, as in the walkthrough viewer
WALK_FOV = 62       # vertical degrees, the viewer's walking lens
GRADES = {
    # sun elevation (None = computed solar position), sun lamp W/m2 and colour, sky strength, metering bias
    # (EV added to the auto exposure), fixture scale and lamp-shade glow. Golden hour and dusk keep the azimuth.
    'day': {'elevation': None, 'sun': 5.0, 'sun_color': (1.0, .95, .88), 'sky': .14, 'exposure': 0.0, 'lamps': 0.0, 'glow': 0.0},
    'golden': {'elevation': 7.5, 'sun': 3.2, 'sun_color': (1.0, .68, .42), 'sky': .32, 'exposure': 0.0, 'lamps': .35, 'glow': 6.0},
    'dusk': {'elevation': 0.4, 'sun': 0.0, 'sun_color': (1.0, .6, .4), 'sky': .32, 'exposure': -.6, 'lamps': 1.0, 'glow': 12.0},
}


def arguments():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--glb', type=Path, required=True, help='presentation GLB from scripts/export_presentation.mjs')
    p.add_argument('--scene', type=Path, required=True, help='the scene.json the GLB was exported from')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--view', choices=['hero', 'entrance', 'front', 'eye'], default='hero')
    p.add_argument('--eye', help='eye-level camera: x,y,floor,yaw_deg[,pitch_deg] in plan metres (with --view eye)')
    p.add_argument('--grade', choices=sorted(GRADES), default='day')
    p.add_argument('--name', help='output file stem (default: view-grade)')
    p.add_argument('--width', type=int, default=1600)
    p.add_argument('--height', type=int, default=900)
    p.add_argument('--samples', type=int, default=128)
    p.add_argument('--exposure', default='auto', help="'auto' meters a quick preview (like a camera); or EV stops")
    p.add_argument('--gpu', action='store_true', help='render on an available GPU device')
    p.add_argument('--blend', action='store_true', help='also save the assembled .blend scene')
    return p.parse_args(argv)


def linear(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]


def principled(material):
    if not material.use_nodes:
        return None
    return next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)


def output_node(material):
    return next(n for n in material.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')


def set_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


# Glass kinds from the scene: clear windows and context glazing, the lightly green balustrade glass, and the
# obscured (acid-etched) glass of wet rooms.
GLASS = {'glass': ((.92, .95, .95, 1), 0.0), 'context-glass': ((.92, .95, .95, 1), 0.0),
         'railglass': ((.84, .93, .9, 1), 0.0), 'frosted': ((.95, .96, .96, 1), .32)}


def archviz_glass(material, colour=(.92, .95, .95, 1), roughness=0.0):
    """Glass for camera and reflection rays; transparent to shadow and diffuse rays, so sunlight and
    skylight reach interiors without caustic noise (the usual architectural-visualisation compromise)."""
    nt = material.node_tree
    for link in list(nt.links):
        if link.to_socket.name == 'Alpha':
            nt.links.remove(link)
    bsdf = principled(material)
    bsdf.inputs['Base Color'].default_value = colour
    set_input(bsdf, ['Transmission Weight', 'Transmission'], 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['IOR'].default_value = 1.45
    bsdf.inputs['Alpha'].default_value = 1.0
    path = nt.nodes.new('ShaderNodeLightPath')
    either = nt.nodes.new('ShaderNodeMath')
    either.operation = 'MAXIMUM'
    nt.links.new(path.outputs['Is Shadow Ray'], either.inputs[0])
    nt.links.new(path.outputs['Is Diffuse Ray'], either.inputs[1])
    clear = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(either.outputs[0], mix.inputs['Fac'])
    nt.links.new(bsdf.outputs['BSDF'], mix.inputs[1])
    nt.links.new(clear.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], output_node(material).inputs['Surface'])


def leaf(material, translucency=.3):
    """Thin foliage: alpha cut-out from the leaf atlas plus light passing through the blade."""
    nt = material.node_tree
    bsdf = principled(material)
    colour = next((l.from_socket for l in nt.links if l.to_socket == bsdf.inputs['Base Color']), None)
    alpha = next((l.from_socket for l in nt.links if l.to_socket == bsdf.inputs['Alpha']), None)
    back = nt.nodes.new('ShaderNodeBsdfTranslucent')
    if colour:
        nt.links.new(colour, back.inputs['Color'])
    else:
        back.inputs['Color'].default_value = bsdf.inputs['Base Color'].default_value
    body = nt.nodes.new('ShaderNodeMixShader')
    body.inputs['Fac'].default_value = translucency
    nt.links.new(bsdf.outputs['BSDF'], body.inputs[1])
    nt.links.new(back.outputs['BSDF'], body.inputs[2])
    shader = body.outputs['Shader']
    if alpha:
        # Principled alpha no longer reaches the output once mixed, so cut out explicitly.
        cut = nt.nodes.new('ShaderNodeMixShader')
        hole = nt.nodes.new('ShaderNodeBsdfTransparent')
        step = nt.nodes.new('ShaderNodeMath')
        step.operation = 'GREATER_THAN'
        step.inputs[1].default_value = .42
        nt.links.new(alpha, step.inputs[0])
        nt.links.new(step.outputs[0], cut.inputs['Fac'])
        nt.links.new(hole.outputs['BSDF'], cut.inputs[1])
        nt.links.new(shader, cut.inputs[2])
        shader = cut.outputs['Shader']
    nt.links.new(shader, output_node(material).inputs['Surface'])


def vertex_colour(material):
    """Planting and lawn carry per-vertex colour (glTF COLOR_0): make sure it tints the base colour."""
    nt = material.node_tree
    bsdf = principled(material)
    if any(n.type == 'VERTEX_COLOR' for n in nt.nodes) or bsdf.inputs['Base Color'].is_linked:
        return
    attr = nt.nodes.new('ShaderNodeVertexColor')
    attr.layer_name = 'Color'
    nt.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])


def prepare_materials(grade):
    for material in bpy.data.materials:
        bsdf = principled(material)
        if bsdf is None:
            continue
        name = (material.name or '').split('.')[0]
        if name in GLASS:
            archviz_glass(material, *GLASS[name])
        elif name == 'mirror':
            bsdf.inputs['Metallic'].default_value = 1.0
            bsdf.inputs['Roughness'].default_value = .02
        elif name.startswith('plant-foliage'):
            if name in ('plant-foliage-lawn', 'plant-foliage-solid'):
                vertex_colour(material)
            leaf(material, .18 if name == 'plant-foliage-lawn' else .3)
        if name in ('globe', 'lamp'):
            # The viewer draws shades as black + emission; switched off they should read as opal glass and
            # white diffusers, and glow only as much as the grade's lamps.
            bsdf.inputs['Base Color'].default_value = (.88, .84, .78, 1) if name == 'globe' else (.84, .84, .82, 1)
            bsdf.inputs['Roughness'].default_value = .35
            emission = bsdf.inputs.get('Emission Strength')
            if emission is not None:
                emission.default_value = grade['glow']


def sky(scene_data, grade):
    x, y, z = scene_data['solar']['vector_local']
    elevation = math.asin(max(-1.0, min(1.0, z))) if grade['elevation'] is None else math.radians(grade['elevation'])
    # Nishita places the sun toward (sin r, cos r) in plan for rotation r (checked with a test shadow).
    rotation = math.atan2(x, y)
    world = bpy.data.worlds.new('FloorForge sky')
    world.use_nodes = True
    bpy.context.scene.world = world
    nt = world.node_tree
    background = nt.nodes['Background']
    texture = nt.nodes.new('ShaderNodeTexSky')
    texture.sky_type = 'NISHITA'
    # The sky carries the sun's scattered glow; direct sunlight comes from a Sun lamp below, which Cycles samples
    # far better than a 0.5 degree disc in the world texture (crisp shadows, no denoiser smearing).
    texture.sun_disc = False
    texture.sun_size = math.radians(.545)
    texture.sun_elevation = elevation
    texture.sun_rotation = rotation
    texture.altitude = 0
    texture.air_density = 1.0
    texture.dust_density = .7
    texture.ozone_density = 1.0
    nt.links.new(texture.outputs['Color'], background.inputs['Color'])
    background.inputs['Strength'].default_value = grade['sky']
    if grade['sun'] > 0 and elevation > 0:
        direction = Vector((math.sin(rotation) * math.cos(elevation), math.cos(rotation) * math.cos(elevation), math.sin(elevation)))
        light = bpy.data.lights.new('Sun (site solar position)', 'SUN')
        light.energy = grade['sun']
        light.angle = math.radians(.545)
        light.color = grade['sun_color']
        sun = bpy.data.objects.new(light.name, light)
        sun.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.collection.objects.link(sun)
    return elevation, rotation


def fixtures(scene_data, grade):
    if grade['lamps'] <= 0:
        return 0
    count = 0
    for i, light in enumerate(scene_data.get('lights', [])):
        if not light.get('fixture_visible', True):
            continue
        kind = light.get('kind', 'fixture')
        directed = kind in ('downlight', 'soffit', 'uplight')
        data = bpy.data.lights.new(f'fixture-{i}-{kind}', 'SPOT' if directed else 'POINT')
        # Electrical watts to a Cycles emitter power that reads as a lit LED fitting of that rating.
        data.energy = light.get('power_w', 10) * 4.0 * grade['lamps']
        data.color = linear(light.get('color', '#ffdfae'))
        data.shadow_soft_size = .03 if directed else .06
        if directed:
            data.spot_size = math.radians(110 if kind != 'uplight' else 60)
            data.spot_blend = .6
        obj = bpy.data.objects.new(data.name, data)
        obj.location = light['position']
        if kind == 'uplight':
            obj.rotation_euler = (math.pi, 0, 0)
        bpy.context.collection.objects.link(obj)
        count += 1
    return count


def house_box(scene_data):
    """World bounds of the home (every storey with its porch, terraces and roof; not the garden or street), from
    the scene's instanced assets and their Rz.Ry.Rx transforms, as the viewer frames it."""
    assets, lo, hi = scene_data['assets'], [1e9] * 3, [-1e9] * 3
    bounds = {}
    for n in scene_data['nodes']:
        if n.get('floor', -1) < 0 or n['role'] == 'plant-proxy':
            continue
        if n['asset'] not in bounds:
            vs = assets[n['asset']]['vertices']
            bounds[n['asset']] = ([min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)])
        a, b = bounds[n['asset']]
        rx, ry, rz = n.get('rotation', (0, 0, 0))
        cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
        for i in range(8):
            q = [(b if i >> k & 1 else a)[k] * n['scale'][k] for k in range(3)]
            q = [q[0], cx * q[1] - sx * q[2], sx * q[1] + cx * q[2]]
            q = [cy * q[0] + sy * q[2], q[1], -sy * q[0] + cy * q[2]]
            q = [cz * q[0] - sz * q[1], sz * q[0] + cz * q[1], q[2]]
            for k in range(3):
                v = q[k] + n['position'][k]
                lo[k], hi[k] = min(lo[k], v), max(hi[k], v)
    return lo, hi


def frame_box(lo, hi, forward, fov, aspect, fill, up=Vector((0, 0, 1)), min_reach=1.5):
    """The closest camera, looking along `forward`, from which the box fills `fill` of the frame on its limiting
    axis, centred on the other: the solve of web/viewer/src/framing.js (every frame edge bounds the camera by a
    plane; per screen axis the closest camera maximises a concave piecewise-linear function)."""
    F = forward.normalized()
    R = F.cross(up).normalized()
    U = R.cross(F)
    tv = math.tan(math.radians(fov) / 2)
    pts = []
    for i in range(8):
        p = Vector([(hi if i >> k & 1 else lo)[k] for k in range(3)])
        pts.append((p.dot(R), p.dot(U), p.dot(F)))

    def axis(k, t):
        def g(c):
            return min(p[2] - max((p[k] - c) / (fill * t), (p[k] - c) / (-fill * t)) for p in pts)
        a, b = min(p[k] for p in pts), max(p[k] for p in pts)
        for _ in range(100):
            m1, m2 = a + (b - a) / 3, b - (b - a) / 3
            if g(m1) < g(m2):
                a = m1
            else:
                b = m2
        return (a + b) / 2, g, b - a + 1

    (bx, gx, spx), (by, gy, spy) = axis(0, tv * aspect), axis(1, tv)
    depth = min(gx(bx), gy(by), min(p[2] for p in pts) - .5)

    def centre(best, g, span):
        if g(best) <= depth + 1e-9:
            return best
        ends = []
        for d in (-1, 1):
            inside, step = best, span
            out = best + d * step
            while g(out) >= depth:
                inside, step = out, step * 2
                out = best + d * step
            for _ in range(60):
                m = (inside + out) / 2
                if g(m) >= depth:
                    inside = m
                else:
                    out = m
            ends.append(inside)
        return sum(ends) / 2

    position = R * centre(bx, gx, spx) + U * centre(by, gy, spy) + F * depth
    mid = Vector([(lo[k] + hi[k]) / 2 for k in range(3)])
    return position, position + F * max(min_reach, mid.dot(F) - depth)


def camera(scene_data, args):
    cameras = scene_data['cameras']
    if args.view == 'eye':
        parts = [float(v) for v in args.eye.split(',')]
        x, y, floor, yaw = parts[:4]
        pitch = math.radians(parts[4]) if len(parts) > 4 else 0.0
        z = floor * scene_data['floor_height'] + .01 + WALK_EYE
        yaw = math.radians(yaw)
        forward = Vector((-math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
        position, fov = Vector((x, y, z)), WALK_FOV
    else:
        if args.view == 'hero':
            c = cameras['hero']
            target, position = Vector(c['target']), Vector(c['position'])
            # Photograph from the sunlit diagonal, as the viewer's hero view does.
            sun_x = scene_data['solar']['vector_local'][0]
            if abs(sun_x) > .2 and (sun_x > 0) != (position.x - target.x > 0):
                position.x = 2 * target.x - position.x
            fov = c.get('fov', 43)
            # Framed like the viewer's hero: the home itself fills 84% of the frame from that direction.
            lo, hi = house_box(scene_data)
            position, target = frame_box(lo, hi, target - position, fov, args.width / args.height, .84)
        else:
            fp = scene_data['footprint']
            xs, ys = [p[0] for p in fp], [p[1] for p in fp]
            w, d, h = max(xs) - min(xs), max(ys) - min(ys), scene_data['floor_height']
            mid_x = (min(xs) + max(xs)) / 2
            if args.view == 'entrance':
                target, theta, phi, distance = Vector((scene_data['entry'][0], -.65, 1.65)), -math.pi / 2, .12, 7.2
            else:
                target, theta, phi, distance = Vector((mid_x, -.2, min(h * 1.15 + .2, 4.2))), -math.pi / 2, .2, max(w, d) * 1.05
            position = target + distance * Vector((math.cos(phi) * math.cos(theta), math.cos(phi) * math.sin(theta), math.sin(phi)))
            fov = 43
            if args.view == 'front':
                lo, hi = house_box(scene_data)
                position, target = frame_box(lo, hi, target - position, fov, args.width / args.height, .88)
        forward = target - position
    data = bpy.data.cameras.new('FloorForge camera')
    data.sensor_fit = 'VERTICAL'
    data.angle_y = math.radians(fov)
    data.clip_start = .05
    data.clip_end = 2000
    obj = bpy.data.objects.new('FloorForge camera', data)
    obj.location = position
    obj.rotation_euler = forward.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(obj)
    bpy.context.scene.camera = obj


def configure(args, grade):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    cycles = scene.cycles
    cycles.device = 'CPU'
    if args.gpu:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for backend in ('OPTIX', 'CUDA', 'HIP', 'METAL', 'ONEAPI'):
            try:
                prefs.compute_device_type = backend
                prefs.get_devices()
                if any(d.type != 'CPU' for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = True
                    cycles.device = 'GPU'
                    break
            except TypeError:
                continue
    cycles.samples = args.samples
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = .02
    cycles.use_denoising = True
    cycles.denoiser = 'OPENIMAGEDENOISE'
    cycles.max_bounces = 8
    cycles.diffuse_bounces = 4
    cycles.glossy_bounces = 4
    cycles.transmission_bounces = 8
    cycles.transparent_max_bounces = 24
    cycles.caustics_reflective = False
    cycles.caustics_refractive = False
    cycles.blur_glossy = 1.0
    cycles.sample_clamp_indirect = 8.0
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_depth = '8'
    scene.view_settings.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'AgX - Punchy'):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            continue
    scene.view_settings.exposure = grade['exposure']


def meter(args, grade):
    """Camera-style metering: render a small preview, then expose its log-average luminance to a bright key.
    Interiors therefore open up by a few stops, as a photographer's camera would, instead of reading dark."""
    scene = bpy.context.scene
    settings = scene.render.image_settings
    keep = (scene.render.resolution_x, scene.render.resolution_y, scene.cycles.samples, scene.render.filepath, settings.file_format, settings.color_depth)
    scene.render.resolution_x, scene.render.resolution_y = 160, max(1, round(160 * args.height / args.width))
    scene.cycles.samples = 16
    scene.render.image_settings.file_format = 'OPEN_EXR'
    probe = (args.out / '.meter.exr').resolve()
    scene.render.filepath = str(probe)
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(str(probe))
    px = image.pixels[:]
    lum = sorted(max(1e-5, .2126 * px[i] + .7152 * px[i + 1] + .0722 * px[i + 2]) for i in range(0, len(px), 4))
    bpy.data.images.remove(image)
    probe.unlink(missing_ok=True)
    scene.render.resolution_x, scene.render.resolution_y, scene.cycles.samples, scene.render.filepath, settings.file_format, depth = keep
    settings.color_depth = depth
    average = math.exp(sum(math.log(v) for v in lum) / len(lum))
    key = .26 if grade['lamps'] < 1 else .16
    # Expose the log-average to a bright key, but never so far that the brightest tenth (lit walls near lamps,
    # bright sky) is pushed far past display white.
    highlight = lum[int(len(lum) * .9)]
    # Daylit rooms may let their windows run bright, as interior photographs do; lamp-lit scenes keep their walls.
    ceiling = 4.0 if grade['lamps'] < 1 and args.view == 'eye' else 1.6
    return max(-4.0, min(8.0, math.log2(key / average), math.log2(ceiling / highlight)))


def main():
    args = arguments()
    grade = GRADES[args.grade]
    scene_data = json.loads(args.scene.read_text('utf8'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
    prepare_materials(grade)
    elevation, rotation = sky(scene_data, grade)
    lamps = fixtures(scene_data, grade)
    camera(scene_data, args)
    configure(args, grade)
    args.out.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.view_settings.exposure = meter(args, grade) + grade['exposure'] if args.exposure == 'auto' else float(args.exposure)
    if args.view == 'eye' and hasattr(scene.view_settings, 'use_white_balance'):
        # Interiors lit by blue skylight read cold; balance like a camera set for the room (lamp-lit rooms stay warm).
        scene.view_settings.use_white_balance = True
        scene.view_settings.white_balance_temperature = 7400 if grade['lamps'] < 1 else 5600
    stem = args.name or f'{args.view}-{args.grade}'
    scene.render.filepath = str((args.out / f'{stem}.png').resolve())
    scene['floorforge'] = json.dumps({'scene': str(args.scene), 'view': args.view, 'eye': args.eye, 'grade': args.grade,
                                      'sun_elevation_deg': round(math.degrees(elevation), 2), 'sun_rotation_deg': round(math.degrees(rotation), 2),
                                      'fixture_lights': lamps, 'samples': args.samples, 'exposure_ev': round(scene.view_settings.exposure, 2),
                                      'banner': scene_data.get('banner')})
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=str((args.out / f'{stem}.blend').resolve()))
    bpy.ops.render.render(write_still=True)
    print(f'wrote {scene.render.filepath} (exposure {scene.view_settings.exposure:+.2f} EV)')


if __name__ == '__main__':
    main()
