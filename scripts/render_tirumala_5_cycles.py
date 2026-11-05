"""Render the actual Tirumala 5 presentation GLB with Cycles.

Example (run from the repository root):
  blender -b --python scripts/render_tirumala_5_cycles.py -- \
    --scene examples/gallery/tirumala-5/scene.json --glb output/tirumala-5-g2/presentation.glb \
    --out output/tirumala-5-g2/cycles --camera exterior_northeast \
    --camera interior_kitchen_living_dining --camera second_terrace --gpu

This is a rendering adapter only: it does not stretch or replace model geometry.
Camera poses come from the delivered scene, including their real floor heights.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_cycles as base


def arguments():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--scene', type=Path, required=True)
    p.add_argument('--glb', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--camera', action='append', dest='cameras', help='Named scene camera; repeat to render several.')
    p.add_argument('--grade', choices=tuple(base.GRADES), default='day')
    p.add_argument('--width', type=int, default=1600)
    p.add_argument('--height', type=int, default=1040)
    p.add_argument('--samples', type=int, default=96)
    p.add_argument('--gpu', action='store_true')
    p.add_argument('--blend', action='store_true')
    p.add_argument('--exposure', default='auto')
    p.add_argument('--fit-exterior', action='store_true', help='Fit the complete house at the named exterior camera heading.')
    return p.parse_args(argv)


def prepare_tirumala_materials(scene_data, grade):
    """Keep exported textures and fix the scene-specific glass not in the base adapter."""
    base.prepare_materials(grade)
    src = scene_data['materials']
    for material in bpy.data.materials:
        bsdf = base.principled(material)
        if bsdf is None:
            continue
        name = material.name.rsplit('.', 1)[0] if material.name.rsplit('.', 1)[-1].isdigit() else material.name
        spec = src.get(name, {})
        # Black TV glass is an opaque display, unlike the facade/ICU panes.
        clear_glass = name in ('icu-glass', 't4-facade-glass') or (
            name.startswith('t5-') and 'glass' in name and spec.get('alpha', 1) < 1)
        if clear_glass:
            base.archviz_glass(material, (.96, .985, .98, 1), .035)
            bsdf.inputs['Metallic'].default_value = 0.0
        elif name in ('glass', 'railglass', 'context-glass', 'frosted'):
            bsdf.inputs['Metallic'].default_value = 0.0
        elif name == 'ivory-marble-polished' or ('t5-' in name and 'slab' in name):
            # A satin-polished finish keeps real highlights without a wet mirror floor.
            if not bsdf.inputs['Roughness'].is_linked:
                bsdf.inputs['Roughness'].default_value = .24
            base.set_input(bsdf, ['Coat Weight', 'Clearcoat'], .10)
            base.set_input(bsdf, ['Coat Roughness', 'Clearcoat Roughness'], .25)
        elif name == 'ivory-marble-exterior-matte':
            if not bsdf.inputs['Roughness'].is_linked:
                bsdf.inputs['Roughness'].default_value = .66
            base.set_input(bsdf, ['Coat Weight', 'Clearcoat'], 0.0)
        # Preserve all exported image maps and physical UV scales. No ambient
        # emission is added to walls, and no window becomes an opaque mirror.


def physical_sky(scene_data, grade):
    """Nishita in Blender 4.x; its renamed single-scattering model in 5.x.

    Blender 5 renamed the old NISHITA enum and dust_density property. Keep
    this compatibility local, so existing project render scripts are untouched.
    """
    x, y, z = scene_data['solar']['vector_local']
    elevation = math.asin(max(-1.0, min(1.0, z))) if grade['elevation'] is None else math.radians(grade['elevation'])
    rotation = math.atan2(x, y)
    world = bpy.data.worlds.new('Tirumala5 physical sky')
    world.use_nodes = True
    bpy.context.scene.world = world
    nt = world.node_tree
    background = nt.nodes['Background']
    texture = nt.nodes.new('ShaderNodeTexSky')
    available = texture.bl_rna.properties['sky_type'].enum_items.keys()
    texture.sky_type = 'NISHITA' if 'NISHITA' in available else 'SINGLE_SCATTERING'
    texture.sun_disc = False
    texture.sun_size = math.radians(.545)
    texture.sun_elevation = elevation
    texture.sun_rotation = rotation
    texture.altitude = 0
    texture.air_density = 1.0
    if hasattr(texture, 'dust_density'):
        texture.dust_density = .7
    elif hasattr(texture, 'aerosol_density'):
        texture.aerosol_density = .7
    texture.ozone_density = 1.0
    nt.links.new(texture.outputs['Color'], background.inputs['Color'])
    background.inputs['Strength'].default_value = grade['sky']
    if grade['sun'] > 0 and elevation > 0:
        direction = Vector((math.sin(rotation)*math.cos(elevation), math.cos(rotation)*math.cos(elevation), math.sin(elevation)))
        light = bpy.data.lights.new('Tirumala5 sun', 'SUN')
        light.energy = grade['sun']
        light.angle = math.radians(.545)
        light.color = grade['sun_color']
        sun = bpy.data.objects.new(light.name, light)
        sun.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.collection.objects.link(sun)
    return elevation, rotation


def scene_camera(data, key, args):
    cfg = data['cameras'][key]
    pos, target = Vector(cfg['position']), Vector(cfg['target'])
    fov = cfg.get('fov', 62)
    is_interior = cfg.get('enter_walk', False) or key.startswith(('interior_', 'upper_', 'second_', 'living_'))
    if args.fit_exterior and not is_interior:
        lo, hi = base.house_box(data)
        pos, target = base.frame_box(lo, hi, target-pos, fov, args.width/args.height, .82)
    camdata = bpy.data.cameras.new('Tirumala5 ' + key)
    camdata.sensor_fit = 'VERTICAL'
    camdata.angle_y = math.radians(fov)
    camdata.clip_start = .03
    camdata.clip_end = 2000
    camera = bpy.data.objects.new(camdata.name, camdata)
    camera.location = pos
    camera.rotation_euler = (target-pos).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    return camera, is_interior


def main():
    args = arguments()
    data = json.loads(args.scene.read_text())
    keys = args.cameras or ['exterior_northeast', 'interior_kitchen_living_dining', 'second_terrace']
    missing = [k for k in keys if k not in data['cameras']]
    if missing:
        raise ValueError(f'Unknown scene cameras {missing}. Available: {sorted(data["cameras"])}')
    grade = copy.deepcopy(base.GRADES[args.grade])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.glb.resolve()))
    bpy.context.view_layer.update()
    prepare_tirumala_materials(data, grade)
    elevation, rotation = physical_sky(data, grade)
    lamps = base.fixtures(data, grade)
    base.configure(args, grade)
    args.out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    # Render sequentially from the same imported geometry/material state.
    manifest = []
    for key in keys:
        camera, is_interior = scene_camera(data, key, args)
        args.view = 'eye' if is_interior else 'hero'  # metering policy only
        sc.view_settings.exposure = base.meter(args, grade) + grade['exposure'] if args.exposure == 'auto' else float(args.exposure)
        if hasattr(sc.view_settings, 'use_white_balance'):
            sc.view_settings.use_white_balance = is_interior
            if is_interior:
                sc.view_settings.white_balance_temperature = 7400 if grade['lamps'] < 1 else 5600
        stem = key + '-' + args.grade
        output = (args.out / (stem + '.png')).resolve()
        sc.render.filepath = str(output)
        record = dict(camera=key, image=str(output), scene=str(args.scene.resolve()),
                      glb=str(args.glb.resolve()), geometry='delivered presentation GLB; no scaling',
                      position=list(camera.location), target=data['cameras'][key]['target'],
                      fov=data['cameras'][key].get('fov', 62), width=args.width, height=args.height,
                      samples=args.samples, engine='CYCLES', device=sc.cycles.device,
                      exposure_ev=round(sc.view_settings.exposure, 3), grade=args.grade,
                      fixture_lights=lamps, sun_elevation_deg=round(math.degrees(elevation), 3),
                      sun_rotation_deg=round(math.degrees(rotation), 3))
        sc['tirumala5_render'] = json.dumps(record)
        if args.blend:
            bpy.ops.wm.save_as_mainfile(filepath=str((args.out / (stem + '.blend')).resolve()))
        bpy.ops.render.render(write_still=True)
        manifest.append(record)
        (args.out / 'render-manifest.json').write_text(json.dumps(manifest, indent=2))
        print('TIRUMALA5_RENDER ' + json.dumps(record), flush=True)
        bpy.data.objects.remove(camera, do_unlink=True)


if __name__ == '__main__':
    main()
