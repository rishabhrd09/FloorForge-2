"""Render three furnished floor cutaways and architectural views from the gallery GLB.
Run: blender -b -P scripts/render_tirumala_6.py [-- ground first second exterior ...]
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

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import render_cycles as rendering
from render_tirumala_5_cycles import prepare_tirumala_materials

SAMPLE=ROOT/'examples/gallery/tirumala-6'
OUT=SAMPLE/'renders'
OUT.mkdir(exist_ok=True)
data=json.loads((SAMPLE/'scene.json').read_text())
nodes={n['id']:n for n in data['nodes']}
requested=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
args=SimpleNamespace(width=1200,height=920,samples=32,gpu='--gpu' in requested)
grade=rendering.GRADES['day'].copy()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SAMPLE/'model.glb'))
scene=bpy.context.scene
prepare_tirumala_materials(data,grade)
rendering.configure(args,grade)
rendering.sky(data,grade)
rendering.fixtures(data,dict(grade,lamps=.28))
# Daylight fill from the actual window, garden and upper gallery apertures.
for name,pos,aim,size,power in [
    ('Garden daylight',(11.3,10.6,3.8),(9.4,7.6,.8),2.8,380),
    ('North window',(12.35,6.5,2.0),(8.2,8.1,.9),2.4,400),
    ('Gallery daylight',(4.6,6.8,6.3),(3.9,7,1),3.0,620),
    ('East daylight',(4.2,3.95,2.8),(5.5,9,1.2),2.5,320)]:
    light=bpy.data.lights.new(name,'AREA');light.energy=power;light.size=size
    obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj)
    obj.location=pos;obj.rotation_euler=(Vector(aim)-Vector(pos)).to_track_quat('-Z','Y').to_euler()

# Grain follows the long axis of each manufactured part. Natural stone and
# plaster use a quieter variation, and fabric has a fine bump at grazing angles.
for mat in bpy.data.materials:
    props=data['materials'].get(mat.name,{})
    typ=props.get('kind','')
    shader=rendering.principled(mat)
    if shader and not props.get('alpha') and props.get('color') and mat.name not in ('lamp','globe'):
        shader.inputs['Base Color'].default_value=(*rendering.linear(props['color']),1)
    if not shader or typ not in ('wood','woodfloor','stone','tile','fabric','rug','paver','render','grass','concrete','soil'):continue
    tree=mat.node_tree; coord=tree.nodes.new('ShaderNodeTexCoord')
    stretch=tree.nodes.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY'
    stretch.inputs[1].default_value=(2,22,11) if typ in ('wood','woodfloor') else (8,8,8)
    tree.links.new(coord.outputs['Generated'],stretch.inputs[0])
    noise=tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.8;noise.inputs['Detail'].default_value=4.0
    tree.links.new(stretch.outputs[0],noise.inputs['Vector'])
    ramp=tree.nodes.new('ShaderNodeValToRGB');rgb=list(shader.inputs['Base Color'].default_value)[:3]
    for el,t in zip(ramp.color_ramp.elements,[.76,1.16]):el.color=(*[min(1,v*t) for v in rgb],1)
    tree.links.new(noise.outputs['Fac'],ramp.inputs[0]);tree.links.new(ramp.outputs[0],shader.inputs['Base Color'])
    bump=tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.012
    tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);tree.links.new(bump.outputs[0],shader.inputs['Normal'])

# Lay the same large, straight-jointed stone slabs in the Cycles stills.
for name in ('ivory-vitrified','flagstone','floor','ivory-vitrified-matte'):
    material=bpy.data.materials.get(name)
    if not material:continue
    spec=data['materials'][name];w,h=spec['tile_m']
    nt=material.node_tree;shader=rendering.principled(material)
    brick=nt.nodes.new('ShaderNodeTexBrick');brick.offset=0
    brick.inputs['Scale'].default_value=1;brick.inputs['Brick Width'].default_value=w;brick.inputs['Row Height'].default_value=h
    brick.inputs['Mortar Size'].default_value=.002
    color=rendering.linear(spec['color']);brick.inputs['Color1'].default_value=(*color,1)
    brick.inputs['Color2'].default_value=(*[v*.965 for v in color],1)
    brick.inputs['Mortar'].default_value=(*[v*.65 for v in color],1)
    geo=nt.nodes.new('ShaderNodeNewGeometry');nt.links.new(geo.outputs['Position'],brick.inputs['Vector'])
    nt.links.new(brick.outputs['Color'],shader.inputs['Base Color'])

objects={o.name:o for o in scene.objects if o.type=='MESH'}
# Replace each preview foliage proxy with a branched cluster of individual leaves.
for name,obj in list(objects.items()):
    node=nodes.get(name,{})
    if node.get('role')!='plant-proxy' or node.get('material')!='leaf':continue
    rng=random.Random(name);verts=[];faces=[];indices=[]
    for i in range(490):
        a=rng.uniform(0,2*math.pi);z=rng.uniform(-1,1);rad=math.sqrt(1-z*z)*rng.uniform(.3,1)
        c=Vector((rad*math.cos(a),rad*math.sin(a),z*.9))
        sideways=Vector((-math.sin(a),math.cos(a),0))*rng.uniform(.055,.11)
        axis=Vector((math.cos(a),math.sin(a),rng.uniform(-.9,.4)))*rng.uniform(.14,.32)
        n=len(verts);verts.extend([c-axis,c+sideways,c+axis,c-sideways,c+Vector((0,0,.045))]);faces.extend([(n,n+1,n+4),(n+1,n+2,n+4),(n+2,n+3,n+4),(n+3,n,n+4)]);indices.extend([i%2]*4)
    mesh=bpy.data.meshes.new('Leaf canopy');mesh.from_pydata(verts,[],faces)
    for k in ('leaf','leaf-light'):mesh.materials.append(bpy.data.materials.get(k) or bpy.data.materials['leaf'])
    for poly,mi in zip(mesh.polygons,indices):poly.material_index=mi
    obj.data=mesh

def garden_backdrop():
    """Plant neighbouring plots in exterior stills; keep them off the house plans."""
    rng=random.Random(602)
    branches=bpy.data.curves.new('Neighbouring trees','CURVE')
    branches.dimensions='3D';branches.bevel_depth=.12;branches.bevel_resolution=1
    branch_obj=bpy.data.objects.new('Off-site branches',branches)
    scene.collection.objects.link(branch_obj)
    branches.materials.append(bpy.data.materials.get('smoked-oak'))
    verts=[];faces=[];swatches=[]
    def stem(points,radii):
        spline=branches.splines.new('POLY');spline.points.add(len(points)-1)
        for point,position,radius in zip(spline.points,points,radii):
            point.co=(*position,1);point.radius=radius
    for x,y,h in [(-4,6,7.2),(-5,15,8.1),(-1,20,6.5),(6,21,8.8),(12,23,6.2),(-11,1,6.8),(-8,26,9)]:
        base=Vector((x,y,-.39));trunk=base+Vector((.15,.04,h*.56))
        stem([base,trunk],[1.5,.65])
        for j in range(26):
            angle=j*2.399963;extent=h*rng.uniform(.18,.41)
            b=trunk+Vector((extent*math.cos(angle),extent*math.sin(angle),h*rng.uniform(-.09,.39)))
            fork=trunk.lerp(b,.47)+Vector((0,0,.35));stem([trunk,fork,b],[.66,.40,.10])
            for _ in range(520):
                phi=rng.random()*math.tau;dz=rng.uniform(-1,1);rho=math.sqrt(1-dz*dz)*rng.random()**.333
                ctr=b+Vector((math.cos(phi)*rho,math.sin(phi)*rho,dz*.73))*h*.175
                length=rng.uniform(.062,.13);yaw=rng.random()*math.tau
                along=Vector((math.cos(yaw),math.sin(yaw),rng.uniform(-.9,.6)))*length
                across=Vector((-math.sin(yaw),math.cos(yaw),.1))*length*.45
                n=len(verts);verts.extend([ctr-along,ctr+across,ctr+along,ctr-across,ctr+Vector((0,0,.014))])
                faces.extend([(n,n+1,n+4),(n+1,n+2,n+4),(n+2,n+3,n+4),(n+3,n,n+4)])
                swatches.extend([rng.randrange(4)]*4)
    mesh=bpy.data.meshes.new('Garden canopy');mesh.from_pydata(verts,[],faces)
    for rgb in [(53,76,44),(72,93,49),(92,111,64),(108,118,70)]:
        mat=bpy.data.materials.new('Garden foliage');mat.diffuse_color=(*[(v/255)**2.2 for v in rgb],1);mesh.materials.append(mat)
    for poly,idx in zip(mesh.polygons,swatches):poly.material_index=idx
    leaves=bpy.data.objects.new('Off-site foliage',mesh);scene.collection.objects.link(leaves)
    return branch_obj,leaves

views=[v for v in requested if v!='--gpu'] or ['ground','first','second','exterior','east_arrival','icu_garden','leisure_hall','hall_windows','office_corner','upper_balcony','north_roof_terrace','garden_verandah','kitchen','living_gallery','living_rooflight','master_suite','suite_northlight','stair_lobby']
cut_roles={'wall','joinery','glass','door','curtain','wall-tile','wall-panel','post','window-surround','sill','pipe','window-hood','parapet'}
overheads={'roof','ceiling','cove','downlight','ceiling-feature','canopy','band'}
for view in views:
    floor={'ground':0,'first':1,'second':2}.get(view)
    cam=bpy.data.cameras.new(view);camera=bpy.data.objects.new(view,cam);scene.collection.objects.link(camera);scene.camera=camera
    originals={};z=(floor or 0)*3.508
    for light in scene.objects:
        if light.type=='LIGHT' and light.data.type!='SUN':light.hide_render=floor is not None
    backdrop=garden_backdrop() if view in ('exterior','east_arrival') else []

    for name,obj in objects.items():
        n=nodes.get(name)
        if not n:continue
        role=n['role'];f=n['floor'];obj.hide_render=False
        if floor is None:continue
        obj.hide_render=(f!=floor and not(floor==0 and role=='plinth')) or role in overheads
        if obj.hide_render:continue
        bb=[(obj.matrix_world@Vector(c)).z for c in obj.bound_box];lo,hi=min(bb),max(bb)
        if lo>z+2.42 or role in cut_roles and lo>z+.98:
            obj.hide_render=True;continue
        if role not in cut_roles or hi<z+1:continue
        original=obj.data;mesh=original.copy();originals[name]=original;obj.data=mesh
        bm=bmesh.new();bm.from_mesh(mesh);m=obj.matrix_world
        up=Vector((0,0,1));out=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=m.inverted()@Vector((0,0,z+1)),plane_no=m.to_3x3().transposed()@up,clear_outer=True,dist=.00001)
        edges=[e for e in out['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_valid and e.is_boundary]
        if edges:bmesh.ops.holes_fill(bm,edges=edges)
        bm.to_mesh(mesh);bm.free()
    if floor is not None:
        target=Vector((6.15,7.4,z+.22));eye=target+Vector((-6,-.6,19));cam.type='ORTHO';cam.ortho_scale=20.8 if floor==0 else 20.0
        # Soft, neutral background for a measured architectural plate.
        bpy.ops.mesh.primitive_plane_add(size=200,location=(6,7,z-.42))
        ground=bpy.context.object;ground.name='Studio surface'
        mat=bpy.data.materials.get('Studio oatmeal') or bpy.data.materials.new('Studio oatmeal');mat.diffuse_color=(.52,.46,.37,1);ground.data.materials.append(mat)
    else:
        cfg=data['cameras']['hero' if view=='exterior' else view]
        eye=Vector(cfg['position']);target=Vector(cfg['target']);cam.lens=32 if view=='exterior' else 21
        if view=='exterior':
            eye=Vector((19,-16.5,4.8));target=Vector((6.1,6.8,4.65))
            sun=next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN')
            sun.rotation_euler=Vector((-1.1,.83,-1.26)).to_track_quat('-Z','Y').to_euler()
            sun.data.angle=math.radians(2.2)

    if floor is None:
        bpy.ops.mesh.primitive_plane_add(size=1800,location=(6,7,-.397))
        ground=bpy.context.object;mat=bpy.data.materials.get('Studio oatmeal') or bpy.data.materials.new('Studio oatmeal');mat.diffuse_color=(.34,.32,.25,1);ground.data.materials.append(mat)
    camera.location=eye;camera.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler()
    scene.view_settings.exposure=-1.15 if floor is not None else -.55 if view=='exterior' else -.6 if view in ('east_arrival','living_gallery','icu_garden') else .0
    scene.render.filepath=str(OUT/(view+'.png'));bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(ground,do_unlink=True)
    for name,old in originals.items():
        temp=objects[name].data;objects[name].data=old;bpy.data.meshes.remove(temp)
    bpy.data.objects.remove(camera,do_unlink=True)
    for obj in backdrop:bpy.data.objects.remove(obj,do_unlink=True)
    if view=='exterior':
        thumb=bpy.data.images.load(str(OUT/'exterior.png'))
        thumb.scale(720,552);thumb.filepath_raw=str(SAMPLE.parent/'thumbnails/tirumala-6.png')
        thumb.file_format='PNG';thumb.save()

