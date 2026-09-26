"""Blender external worker. Usage:
blender --background --python scripts/blender_scene.py -- --scene SCENE.json --out RENDERS --view hero --width 3840 --samples 128 --fbx
The delivery environment did not contain Blender. This worker is supplied, not render-verified.
"""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--scene',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--view',choices=['hero','dollhouse','interior'],default='hero');p.add_argument('--width',type=int,default=1920);p.add_argument('--samples',type=int,default=96);p.add_argument('--fbx',action='store_true');p.add_argument('--tour',action='store_true');p.add_argument('--frames',type=int,default=360);p.add_argument('--dusk',action='store_true');args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);data=json.loads(args.scene.read_text());args.out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.render.engine='CYCLES';scene.cycles.samples=args.samples;scene.cycles.use_adaptive_sampling=True;scene.cycles.use_denoising=True;scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width*9/16);scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
try:scene.view_settings.view_transform='AgX'
except TypeError:pass
mats={}
def linear(color):
    rgb=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    return [x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
for name,src in data['materials'].items():
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=(*linear(src['color']),1);nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*linear(src['color']),1);bs.inputs['Roughness'].default_value=src.get('roughness',.8);bs.inputs['Metallic'].default_value=src.get('metallic',0)
    if src.get('alpha',1)<1:
        transmission=bs.inputs.get('Transmission Weight') or bs.inputs.get('Transmission')
        if transmission:transmission.default_value=.95
        bs.inputs['IOR'].default_value=1.45
    if src.get('emission'):
        em=bs.inputs.get('Emission Color') or bs.inputs.get('Emission')
        if em:em.default_value=(*linear(src['color']),1)
        strength=bs.inputs.get('Emission Strength')
        if strength:strength.default_value=3 if args.dusk else .6
    if src.get('texture'):
        tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=40 if src['texture'] in ('plaster','fabric') else 4;tex.inputs['Detail'].default_value=2
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.10;bump.inputs['Distance'].default_value=.003;links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    mats[name]=mat
meshes={}
for key,src in data['assets'].items():
    mesh=bpy.data.meshes.new(key);mesh.from_pydata(src['vertices'],[],src['faces']);mesh.update()
    if src.get('normals'):
        for poly in mesh.polygons:poly.use_smooth=True
    meshes[key]=mesh
for n in data['nodes']:
    if args.view=='dollhouse' and (n['floor']>0 or n['role'] in ('roof','ceiling','canopy','pipe','accent','fin','screen','band','pergola')):continue
    obj=bpy.data.objects.new(n['id'],meshes[n['asset']]);bpy.context.collection.objects.link(obj);obj.location=n['position'];obj.scale=n['scale'];obj.rotation_euler=n['rotation'];obj['semantic_owner']=n['owner'];obj['floor']=n['floor'];obj['role']=n['role']
    # Object-linked material slots preserve shared mesh instancing with distinct finishes.
    if not obj.data.materials:obj.data.materials.append(mats[n['material']])
    obj.material_slots[0].link='OBJECT';obj.material_slots[0].material=mats[n['material']]
world=bpy.data.worlds.new('FloorForge sky');world.use_nodes=True;scene.world=world;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.24,.39,1) if args.dusk else (.65,.75,.86,1);world.node_tree.nodes['Background'].inputs[1].default_value=.18 if args.dusk else .38
sun_data=bpy.data.lights.new('Astronomical study sun','SUN');sun_data.energy=.10 if args.dusk else 2.5;sun_data.angle=math.radians(.8);sun=bpy.data.objects.new('Astronomical study sun',sun_data);bpy.context.collection.objects.link(sun);sun.rotation_euler=(-Vector(data['solar']['vector_local'])).to_track_quat('-Z','Y').to_euler()
for i,light in enumerate(data['lights']):
    if not light.get('fixture_visible'):continue
    lamp=bpy.data.lights.new('Visible fixture '+str(i),'POINT');lamp.energy=light['power_w']*(1 if args.dusk else .25);lamp.color=(1,.72,.44);lamp.shadow_soft_size=.07;obj=bpy.data.objects.new(lamp.name,lamp);bpy.context.collection.objects.link(obj);obj.location=light['position']
camdata=bpy.data.cameras.new('FloorForge directed camera');camera=bpy.data.objects.new('FloorForge directed camera',camdata);bpy.context.collection.objects.link(camera);scene.camera=camera;cfg=data['cameras'][args.view];camera.location=cfg['position'];camera.rotation_euler=(Vector(cfg['target'])-camera.location).to_track_quat('-Z','Y').to_euler();camdata.lens=36/(2*math.tan(math.radians(cfg['fov'])/2));camdata.dof.use_dof=False
scene['review_status']=data['banner'];scene['render_scope']='Unverified procedural archviz adapter. Review composition, joinery, lighting and intersections before sharing.'
if args.tour:
    # Exterior orbit only: no false claim of a validated room-to-room/stair tour.
    scene.frame_start=1;scene.frame_end=args.frames;scene.render.fps=30;center=Vector(cfg['target']);start=Vector(cfg['position'])-center
    for frame,angle in [(1,0),(args.frames,math.pi*.65)]:
        camera.location=center+Vector((start.x*math.cos(angle)-start.y*math.sin(angle),start.x*math.sin(angle)+start.y*math.cos(angle),start.z));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.keyframe_insert(data_path='location',frame=frame);camera.keyframe_insert(data_path='rotation_euler',frame=frame)
    scene.render.filepath=str(args.out/'frames'/'frame_');(args.out/'frames').mkdir(exist_ok=True)
else:scene.render.filepath=str(args.out/(args.view+('-dusk' if args.dusk else '')+'.png'))
bpy.ops.wm.save_as_mainfile(filepath=str(args.out/'FloorForge.blend'))
if args.fbx:
    bpy.ops.export_scene.fbx(filepath=str(args.out/'FloorForge.fbx'),use_selection=False,apply_unit_scale=True,axis_forward='-Z',axis_up='Y',bake_anim=False)
    (args.out/'scene.json').write_text(json.dumps(data))
bpy.ops.render.render(animation=args.tour,write_still=not args.tour)
