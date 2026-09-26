"""Shared authored geometry for GLB, the live renderer, and external Blender.
No downloaded furniture, protected reference images or image-generation overlays.
"""
from __future__ import annotations
import math, random
import numpy as np
import trimesh
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles, get_parts
from .model import sha, STYLES
from .exterior import apply_exterior_preferences, get_exterior_theme, get_interior_theme


def extrude(poly,z0,z1):
    vertices=[]; faces=[]
    def tri(points):
        k=len(vertices);vertices.extend(points);faces.append([k,k+1,k+2])
    for part in get_parts(poly):
        if part.geom_type!='Polygon' or part.area<1e-8:continue
        for t in get_parts(constrained_delaunay_triangles(part)):
            a,b,c=list(t.exterior.coords)[:3]
            if np.cross(np.array(b)-a,np.array(c)-a)<0:b,c=c,b
            tri([(a[0],a[1],z1),(b[0],b[1],z1),(c[0],c[1],z1)])
            tri([(c[0],c[1],z0),(b[0],b[1],z0),(a[0],a[1],z0)])
        for ring in [part.exterior,*part.interiors]:
            pts=list(ring.coords)
            for a,b in zip(pts,pts[1:]):
                tri([(a[0],a[1],z0),(b[0],b[1],z0),(b[0],b[1],z1)])
                tri([(a[0],a[1],z0),(b[0],b[1],z1),(a[0],a[1],z1)])
    m=trimesh.Trimesh(vertices=np.array(vertices),faces=np.array(faces),process=True)
    m.fix_normals();return m


def rounded_box(size,radius=.05):
    half=np.array(size)/2; core=np.maximum(half-radius,.0001)
    verts=[];faces=[];uv=np.linspace(-1,1,7)
    for axis in range(3):
        others=[i for i in range(3) if i!=axis]
        for sign in (-1,1):
            base=len(verts)
            for a in uv:
                for b in uv:
                    p=np.zeros(3);p[axis]=sign*half[axis];p[others[0]]=a*half[others[0]];p[others[1]]=b*half[others[1]]
                    q=np.clip(p,-core,core);d=p-q;p=q+radius*d/max(np.linalg.norm(d),1e-9);verts.append(p)
            for i in range(6):
                for j in range(6):
                    k=base+i*7+j;faces += [[k,k+1,k+8],[k,k+8,k+7]]
    m=trimesh.Trimesh(vertices=verts,faces=faces,process=True);m.fix_normals();return m


def opening_polygon(w,o,pad=0):
    a=np.array(w['a'],dtype=float); b=np.array(w['b'],dtype=float);u=(b-a)/np.linalg.norm(b-a);n=np.array([-u[1],u[0]])
    p=a+u*(o['offset']-pad);q=a+u*(o['offset']+o['width']+pad);t=w['thickness']+300
    return Polygon([p-n*t,q-n*t,q+n*t,p+n*t])


def make_scene(building,report):
    b=building if building.get('exterior') else apply_exterior_preferences(building)
    v=b['brief'];exterior=b['exterior'];theme_id=exterior['theme']
    facade_style={'warm_modern_minimal':'minimal','tropical_verandah':'tropical','earth_terracotta':'terracotta'}.get(theme_id,v['style'])
    style={**STYLES[facade_style],**get_exterior_theme(theme_id).get('materials',{})}
    interior_theme=get_interior_theme(exterior.get('interior_theme','current'))
    H=v['floor_height_mm']/1000;fp=Polygon(np.array(b['footprint'])/1000);plot=Polygon(np.array(b['plot'])/1000)
    plinth=v['plinth_mm']/1000;g=-plinth
    W,D=fp.bounds[2],fp.bounds[3]
    # Palette changes must not perturb procedural furniture or planting layout.
    rng_seed=sha({'footprint':b['footprint'],'spaces':[(s['id'],s['polygon']) for s in b['spaces']],'seed':v.get('seed',0)})
    rng=random.Random(int(rng_seed[:12],16));assets={};nodes=[];colliders=[];furniture=[];lights=[]
    materials={
      'wall':{'color':style['wall'],'roughness':.88,'texture':'plaster'},
      'stone':{'color':style.get('stone',style['accent']),'roughness':.78,'texture':'stone'},
      'timber':{'color':style.get('timber',style['wood']),'roughness':.46,'texture':'wood'},
      'frame':{'color':style['frame'],'roughness':.32,'metallic':.3},
      'roof':{'color':style['roof'],'roughness':.77,'texture':'concrete'},
      'floor':{'color':'#ddd6c4','roughness':.3,'texture':'tile'},
      'woodfloor':{'color':interior_theme['materials'].get('woodfloor','#a89170'),'roughness':.4,'texture':'wood'},
      'wetfloor':{'color':'#aeb4aa','roughness':.56,'texture':'tile'},
      'fabric':{'color':interior_theme['materials'].get('fabric','#ded5bf'),'roughness':.99,'texture':'fabric'},
      'fabric-dark':{'color':interior_theme['materials'].get('fabric-dark','#7c8870'),'roughness':.94,'texture':'fabric'},
      'linen':{'color':interior_theme['materials'].get('linen','#f2eee2'),'roughness':.98,'texture':'fabric'},
      'rug':{'color':interior_theme['materials'].get('rug','#b7a58b'),'roughness':.98,'texture':'fabric'},
      'glass':{'color':'#aec8cc','roughness':.12,'alpha':.26,'metallic':.1},
      'brass':{'color':'#b69c68','roughness':.28,'metallic':.65},
      'ceramic':{'color':'#eeebe1','roughness':.25},
      'leaf':{'color':style.get('site_leaf','#5b734a'),'roughness':.9},'leaf-light':{'color':style.get('site_leaf_light','#89955f'),'roughness':.9},
      'soil':{'color':style.get('site_soil','#63553d'),'roughness':1.,'texture':'stone'},
      'grass':{'color':'#7d8d60','roughness':1.,'texture':'grass'},
      'asphalt':{'color':'#494d48','roughness':.97,'texture':'asphalt'},
      'paver':{'color':style.get('site_paving','#aca998'),'roughness':.75,'texture':'paver'},
      'lamp':{'color':'#ffde9b','roughness':.5,'emission':1.},
      'art':{'color':'#9a7254','roughness':.95},
    }
    def asset(mesh,key=None,smooth=False):
        key=key or sha({'v':np.round(mesh.vertices,5).tolist(),'f':mesh.faces.tolist()})[:20]
        if key not in assets:
            assets[key]={'vertices':np.round(mesh.vertices,6).tolist(),'faces':mesh.faces.tolist(),
                         'normals':np.round(mesh.vertex_normals,6).tolist() if smooth else None,'closed':bool(mesh.is_watertight)}
        return key
    cube=asset(trimesh.creation.box(),'unit-box');sphere=asset(trimesh.creation.uv_sphere(radius=1,count=[12,16]),'unit-sphere',True)
    cyl=asset(trimesh.creation.cylinder(radius=1,height=1,sections=20),'unit-cylinder',True)
    def node(key,mat,pos=(0,0,0),scale=(1,1,1),rot=(0,0,0),floor=-1,role='detail',name=None,owner=None):
        ident=name or f'object-{len(nodes):05d}'
        nodes.append({'id':ident,'asset':key,'material':mat,'position':list(pos),'scale':list(scale),'rotation':list(rot),
                      'floor':floor,'role':role,'owner':owner or ident})
        return ident
    def rect(bounds,mat,f=-1,role='detail',name=None,owner=None):
        a=np.array(bounds[:3]);z=np.array(bounds[3:]);size=z-a
        if min(size)<=0:return None
        return node(cube,mat,(a+z)/2,size,floor=f,role=role,name=name,owner=owner)
    def rb(center,size,mat,f=0,role='furniture',r=.04,rot=0,owner=None):
        key=asset(rounded_box(size,min(r,min(size)*.35)),smooth=True)
        return node(key,mat,center,rot=(0,0,rot),floor=f,role=role,owner=owner)
    def cylinder(center,radius,height,mat,f=-1,role='detail',rot=(0,0,0)):
        return node(cyl,mat,center,(radius,radius,height),rot,f,role)
    def ball(center,size,mat,f=-1,role='landscape',rot=(0,0,0)):
        return node(sphere,mat,center,size,rot,f,role)
    def beam(p,q,r,mat,f=-1,role='detail'):
        p=np.array(p);q=np.array(q);d=q-p;l=np.linalg.norm(d)
        if l<1e-4:return
        # Euler XYZ carrying the cylinder Z axis into d.
        theta=math.acos(np.clip(d[2]/l,-1,1));phi=math.atan2(d[1],d[0])
        return node(cyl,mat,(p+q)/2,(r,r,l),(0,theta,phi),f,role)
    def poly_mesh(poly,z0,z1,mat,f=-1,role='wall',name=None,owner=None):
        if poly.is_empty:return
        return node(asset(extrude(poly,z0,z1)),mat,floor=f,role=role,name=name,owner=owner)
    leaf_vertices=[[0,0,0],[.28,-.13,.025],[.65,-.12,.06],[1.,0,.015],[.65,.12,.06],[.28,.13,.025],[.48,0,.095]]
    leaf_mesh=trimesh.Trimesh(vertices=leaf_vertices,faces=[[0,1,6],[1,2,6],[2,3,6],[3,4,6],[4,5,6],[5,0,6]],process=False)
    leaf_asset=asset(leaf_mesh,'authored-leaf-blade',smooth=True)
    def plant(x,y,z,scale=1.,f=-1,tree=False):
        pot=.22*scale
        if not tree:
            mesh=trimesh.creation.cylinder(radius=pot,height=.35*scale,sections=20)
            node(asset(mesh,smooth=True),'ceramic',(x,y,z+.175*scale),floor=f,role='landscape')
            cylinder((x,y,z+.355*scale),pot*.87,.012,'soil',f,'landscape')
        height=scale*(2.7 if tree else .9)
        beam((x,y,z+.2*scale),(x+.08*scale,y,z+height),.035*scale if tree else .012*scale,'timber',f,'landscape')
        count=18 if tree else 10
        for i in range(count):
            angle=i*2.399+.12*rng.random();spread=(.30+.58*rng.random())*scale*(1.5 if tree else .45)
            zz=z+height*(.47+.48*rng.random());xx=x+math.cos(angle)*spread;yy=y+math.sin(angle)*spread
            beam((x,y,z+height*.53),(xx,yy,zz),.011*scale if tree else .005*scale,'timber',f,'landscape')
            for j in range(16 if tree else 2):
                a=angle+j*2.4;rad=rng.random()*.34*scale if tree else 0
                center=(xx+math.cos(a)*rad,yy+math.sin(a)*rad,zz+(.18*rng.random()-.08)*scale)
                size=scale*(.20+.12*rng.random()) if tree else scale*(.34+.12*rng.random())
                node(leaf_asset,'leaf-light' if (i+j)%5==0 else 'leaf',center,(size,size,size),(.25*math.sin(a),-.45+(.7*rng.random()),a),f,'landscape')
    def obstacle(p,f,ident):colliders.append({'id':ident,'floor':f,'polygon':[[float(x),float(y)] for x,y in list(p.exterior.coords)[:-1]],'kind':'furniture'})
    def furnishing(kind,room,p):
        furniture.append({'id':f'{room["id"]}/{kind}','kind':kind,'floor':room['floor'],'room_id':room['id'],'footprint':[[float(x),float(y)] for x,y in list(p.exterior.coords)[:-1]]})
        obstacle(p,room['floor'],furniture[-1]['id'])

    # Boundary & honest terrain: road -> kerb -> gate -> court -> porch -> door.
    xmin,ymin,xmax,ymax=plot.bounds
    rect((xmin-8,ymin-7,g-.13,xmax+8,ymax+5,g-.04),'grass',role='terrain')
    rect((xmin-8,ymin-6,g-.05,xmax+8,ymin-.22,g),'asphalt',role='site')
    rect((xmin-.2,ymin-.25,g-.03,xmax+.2,ymin,g+.11),'paver',role='site')
    for x in np.arange(xmin-6,xmax+8,4):rect((x,ymin-3.4,g+.003,x+1.7,ymin-3.34,g+.01),'linen',role='site')
    for xa,ya,xb,yb in [(xmin,ymin,xmin+.15,ymax),(xmax-.15,ymin,xmax,ymax),(xmin,ymax-.15,xmax,ymax)]:
        rect((xa,ya,g,xb,yb,.65),'wall',role='site');rect((xa-.02,ya-.02,.65,xb+.02,yb+.02,.69),'stone',role='site')
    entry=next(o for o in b['openings'] if o['kind']=='entry'); ew=next(w for w in b['walls'] if w['id']==entry['wall_id'])
    u=(np.array(ew['b'])-ew['a'])/math.dist(ew['a'],ew['b']); em=np.array(ew['a'])+u*(entry['offset']+entry['width']/2);ex=em[0]/1000
    gate_half=1.1 if not v['parking'] else 1.7
    for xa,xb in [(xmin,ex-gate_half),(ex+gate_half,xmax)]:
        if xb>xa:
            rect((xa,ymin,g,xb,ymin+.18,.72),'wall',role='site')
            rect((xa,ymin-.02,.72,xb,ymin+.2,.78),'stone',role='site')
    for x in (ex-gate_half-.08,ex+gate_half+.08):rect((x-.11,ymin-.04,g,x+.11,ymin+.24,1.05),'stone',role='site')
    # Gate leaves shown open into the court, never a closed gate across the arrival route.
    for side in (-1,1):
        x=ex+side*gate_half
        for y in np.arange(ymin+.2,ymin+1.7,.16):rect((x-.025,y,g+.17,x+.025,y+.055,.95),'frame',role='gate')
        for z in (g+.25,.83):rect((x-.032,ymin+.17,z,x+.032,ymin+1.8,z+.05),'frame',role='gate')
    rect((ex-1.1,ymin+.2,g,ex+1.1,-.75,g+.02),'paver',role='court')
    for y in np.arange(ymin+.8,-1,.65):rect((ex-.93,y,g+.022,ex+.93,y+.48,g+.039),'stone',role='court')
    for x in (xmin+.55,xmax-.55):
        for y in np.arange(ymin+1.1,ymax-.6,1.65):plant(x,y,g,.6)
    if v['front_mm']>=2500:
        for x in (max(xmin+1.3,ex-3),min(xmax-1.3,ex+3)):
            plant(x,ymin+1.8,g,.9,tree=True)
    # Plinth and steps; explicitly not a step-free access solution.
    plinth=v['plinth_mm']/1000
    poly_mesh(fp,-plinth,-.15,'stone',role='plinth')
    steps=max(1,math.ceil(plinth/.15))
    for i in range(steps):
        y0=-.3*(steps-i);y1=y0+.3
        rect((ex-1.0,y0,-plinth,ex+1.,y1,-plinth+(i+1)*plinth/steps),'stone',role='step')
    # Separate floor slabs, no solid slab over the stair well.
    for f in range(b['storeys']):
        level=f*H;slab=fp
        if f:
            st=b['stairs'][f];sx=st['x']/1000;sy=st['y']/1000
            slab=slab.difference(box(sx,sy+1.05,sx+st['width']/1000,sy+st['depth']/1000))
        poly_mesh(slab,level-.15,level,'floor',f,'floor',f'F{f}-floor')
        for s in [s for s in b['spaces'] if s['floor']==f and s['kind']!='stair']:
            p=Polygon(np.array(s['clear'])/1000)
            mat='woodfloor' if s['kind'] in ('bedroom','study') else 'wetfloor' if s['kind'] in ('bathroom','utility') else 'floor'
            poly_mesh(p,level+.002,level+.009,mat,f,'finish',s['id']+'/floor',s['id'])
        # Ceiling edges, visible linear coves and no invisible interior point-fill.
        for s in [s for s in b['spaces'] if s['floor']==f and s['kind'] in ('living','family','bedroom','dining')]:
            p=Polygon(np.array(s['clear'])/1000); inner=p.buffer(-.16)
            if inner.is_empty:continue
            ring=p.difference(inner)
            poly_mesh(ring,level+H-.35,level+H-.22,'wall',f,'ceiling')
            glow=inner.boundary.buffer(.008).intersection(p)
            poly_mesh(glow,level+H-.257,level+H-.247,'lamp',f,'ceiling')
    top=b['storeys']*H
    roof_fp=fp
    for terrace in [s for s in b['spaces'] if s['floor']==b['storeys']-1 and s['kind']=='terrace']:
        roof_fp=roof_fp.difference(Polygon(np.array(terrace['polygon'])/1000))
    poly_mesh(roof_fp,top-.15,top,'roof',b['storeys']-1,'roof','roof-slab')
    parapet=roof_fp.difference(roof_fp.buffer(-.15))
    poly_mesh(parapet,top,top+.6,'wall',b['storeys']-1,'roof','parapet')
    poly_mesh(fp.buffer(.025).difference(fp.buffer(-.175)),top+.60,top+.65,'stone',b['storeys']-1,'roof','coping')

    # Real polygon wall voids, segmented at sill/lintel levels.
    hosts={w['id']:w for w in b['walls']}
    for w in b['walls']:
        openings=[o for o in b['openings'] if o['wall_id']==w['id']]
        wp=Polygon(np.array(w['polygon'])/1000); cuts={0,w['height']/1000}
        for o in openings:cuts.update((o['sill']/1000,(o['sill']+o['height'])/1000))
        cuts=sorted(cuts)
        from shapely.affinity import scale as pscale
        for k,(z0,z1) in enumerate(zip(cuts,cuts[1:])):
            geom=wp; mid=(z0+z1)*500
            for o in openings:
                if o['sill']<=mid<=o['sill']+o['height']:
                    geom=geom.difference(pscale(opening_polygon(w,o),xfact=.001,yfact=.001,origin=(0,0)))
            poly_mesh(geom,z0+w['floor']*H,z1+w['floor']*H,'wall',w['floor'],'wall',f'{w["id"]}/{k}',w['id'])
        cp=wp
        for o in openings:
            if o['kind']!='window':cp=cp.difference(pscale(opening_polygon(w,o,10),xfact=.001,yfact=.001,origin=(0,0)))
        for j,p in enumerate(get_parts(cp)):
            if p.geom_type=='Polygon':colliders.append({'id':w['id']+f'/{j}','floor':w['floor'],'polygon':[[float(x),float(y)] for x,y in list(p.exterior.coords)[:-1]],'kind':'wall'})
    for o in b['openings']:
        w=hosts[o['wall_id']];a=np.array(w['a'])/1000;bb=np.array(w['b'])/1000;uv=(bb-a)/np.linalg.norm(bb-a);nv=np.array([-uv[1],uv[0]]);ang=math.atan2(uv[1],uv[0]);p=a+uv*o['offset']/1000
        if not fp.covers(Point(*(p+uv*o['width']/2000+nv*.4))):nv=-nv
        base=o['floor']*H;ow=o['width']/1000;z0=base+o['sill']/1000;zh=o['height']/1000
        def part(x,depth,z,sx,sy,sz,mat='frame',role='joinery'):
            q=p+uv*x+nv*depth
            node(cube,mat,(q[0],q[1],z),(sx,sy,sz),(0,0,ang),o['floor'],role,owner=o['id'])
        if o['kind']=='cased':continue
        part(.025,0,z0+zh/2,.05,.10,zh);part(ow-.025,0,z0+zh/2,.05,.10,zh)
        part(ow/2,0,z0+zh-.025,ow-.1,.10,.05)
        if o['kind']=='window':
            part(ow/2,0,z0+.025,ow-.1,.10,.05)
            part(ow/2,0,z0+zh/2,ow-.1,.015,zh-.1,'glass','glass')
            if ow>1.2:part(ow/2,0,z0+zh/2,.035,.08,zh)
            part(ow/2,0,z0-.045,ow+.16,.4,.07,'stone','sill')
            if w['external']:
                part(ow/2,-.18,z0+zh+.12,ow+.3,.7,.10,'roof','shade')
                # Exterior reveals and hoods are coordinated with the actual
                # wall void. They make the opening read as architecture rather
                # than a textured rectangle, while preserving the opening's
                # room and wall coordinates.
                room_kinds=[next((s['kind'] for s in b['spaces'] if s['id']==room),'secondary') for room in w['rooms']]
                surround='stone' if set(room_kinds).intersection({'living','family','dining'}) else 'frame'
                part(-.08,-.08,z0+zh/2,.10,.18,zh+.18,surround,'window-surround')
                part(ow+.08,-.08,z0+zh/2,.10,.18,zh+.18,surround,'window-surround')
                if set(room_kinds).intersection({'living','family','dining'}):
                    part(ow/2,-.32,z0+zh+.17,ow+.46,.52,.10,'stone','window-hood')
                elif zh>1.0:
                    part(ow/2,-.25,z0+zh+.13,ow+.28,.34,.075,'roof','window-hood')
            # Pleated cloth curtain strips on the internal side.
            if zh>1.:
                for edge in (.12,ow-.12):
                    verts=[];fs=[]
                    for j in range(17):
                        xx=edge-.16+j*.02;yy=.19+.028*math.cos(j*math.pi/2)
                        q=p+uv*xx+nv*yy
                        verts.extend([(q[0],q[1],z0-.02),(q[0],q[1],z0+zh+.08)])
                    for j in range(16):k=j*2;fs.extend([[k,k+1,k+3],[k,k+3,k+2]])
                    node(asset(trimesh.Trimesh(vertices=verts,faces=fs,process=False),smooth=True),'linen',floor=o['floor'],role='curtain',owner=o['id'])
        elif o['kind']=='glazed':
            # A partly-open sliding glass leaf, not an opaque timber balcony door.
            part(ow*.74,0,z0+zh/2,ow*.47,.018,zh-.1,'glass','glass')
            for xx in (ow*.505,ow-.04):part(xx,0,z0+zh/2,.035,.07,zh-.04)
            part(ow*.74,0,z0+.025,ow*.48,.07,.05)
        else:
            # Leaves shown open 90 degrees; no invisible solid wall remains in the portal.
            hinge=p+uv*.055;leafcenter=hinge+nv*(ow-.1)/2
            rb((leafcenter[0],leafcenter[1],base+zh/2),(.042,ow-.1,zh-.05),'timber',o['floor'],'door',.008,ang,owner=o['id'])
            knob=hinge+nv*(ow-.18)
            ball((knob[0]+uv[0]*.04,knob[1]+uv[1]*.04,base+1.),(.035,.035,.035),'brass',o['floor'],'door')

    # Furnishing recipes: nested geometry, proper feet, hollow vessels, curved cushions.
    def lamp(x,y,z,f,pendant=False):
        if pendant:
            beam((x,y,z),(x,y,f*H+H-.22),.006,'frame',f,'fixture')
            shade=trimesh.creation.cone(radius=.23,height=.18,sections=24)
            node(asset(shade,smooth=True),'timber',(x,y,z),rot=(math.pi,0,0),floor=f,role='fixture')
            ball((x,y,z-.06),(.07,.07,.07),'lamp',f,'fixture')
        else:
            cylinder((x,y,z+.015),.11,.03,'brass',f,'fixture');beam((x,y,z+.03),(x,y,z+.31),.014,'brass',f,'fixture')
            cylinder((x,y,z+.35),.16,.21,'linen',f,'fixture');ball((x,y,z+.32),(.05,.05,.05),'lamp',f,'fixture')
        lights.append({'position':[x,y,z-.04 if pendant else z+.33],'color':'#ffdfae','power_w':35 if pendant else 12,'fixture_visible':True})
    def chair(x,y,z,f,rot=0):
        c,s=math.cos(rot),math.sin(rot)
        def p(a,b,zz):return (x+a*c-b*s,y+a*s+b*c,z+zz)
        for a in (-.20,.20):
            for bb in (-.19,.19):beam(p(a,bb,.04),p(a*.88,bb*.88,.43),.021,'timber',f,'furniture')
        rb(p(0,0,.46),(.48,.49,.09),'fabric',f,r=.04,rot=rot)
        for a in (-.20,.20):beam(p(a,.20,.43),p(a,.24,.85),.02,'timber',f,'furniture')
        rb(p(0,.23,.74),(.50,.085,.26),'fabric',f,r=.035,rot=rot)
    for room in b['spaces']:
        f=room['floor'];z=f*H;p=Polygon(np.array(room['clear'])/1000)
        layout_rect=box(*p.bounds)
        if not p.buffer(1e-6).covers(layout_rect):
            # Furnish the largest contained axis-aligned rectangle, never an L-room bounding box.
            xs=sorted(set(round(x,6) for x,y in p.exterior.coords));ys=sorted(set(round(y,6) for x,y in p.exterior.coords))
            candidates=sorted(((x1-x0)*(y1-y0),(x0,y0,x1,y1)) for i,x0 in enumerate(xs) for x1 in xs[i+1:] for j,y0 in enumerate(ys) for y1 in ys[j+1:])
            layout_rect=None
            for _,bounds in reversed(candidates):
                q=box(*bounds)
                if p.buffer(1e-5).covers(q):layout_rect=q;break
            if layout_rect is None:continue
        x0,y0,x1,y1=layout_rect.bounds;rw=x1-x0;rd=y1-y0;cx=(x0+x1)/2;cy=(y0+y1)/2;kind=room['kind']
        if kind=='stair' or kind=='hall':continue
        if kind=='bedroom':
            bw=1.6;bl=2.;bx=x0+max(.25,(rw-bw)/2-.2);by=y0+.20
            rect((bx,by,z+.07,bx+bw,by+bl,z+.28),'timber',f,'furniture',owner=room['id'])
            rb((bx+bw/2,by+bl/2,z+.39),(bw+.04,bl+.03,.25),'linen',f,r=.075,owner=room['id'])
            rb((bx+bw/2,by-.035,z+.7),(bw+.35,.14,1.25),'fabric-dark',f,r=.06)
            for px in (bx+.40,bx+1.20):rb((px,by+.38,z+.58),(.68,.42,.17),'linen',f,r=.07,rot=.035)
            # Soft draped duvet with geometric folds rather than a solid block.
            vv=[];ff=[];nx=22;ny=24
            for j in range(ny):
                for i in range(nx):
                    xx=bx-.055+(bw+.11)*i/(nx-1); yy=by+.68+(bl-.58)*j/(ny-1)
                    zz=z+.54+.014*math.cos(i*.9+j*.25)+.007*math.sin(i*1.8)
                    if i in (0,nx-1):zz-=.13
                    vv.append((xx,yy,zz))
            for j in range(ny-1):
                for i in range(nx-1):k=j*nx+i;ff += [[k,k+1,k+nx+1],[k,k+nx+1,k+nx]]
            node(asset(trimesh.Trimesh(vertices=vv,faces=ff,process=False),smooth=True),'fabric',floor=f,role='furniture')
            for side in (-1,1):
                xx=bx-.30 if side==-1 else bx+bw+.30
                if x0+.20<xx<x1-.2:
                    rb((xx,by+.22,z+.31),(.43,.45,.48),'timber',f,r=.014);lamp(xx,by+.22,z+.56,f)
            # Wardrobe with recessed plinth, visible frame, separate front leaves and rails.
            wx=x0+.05;wy=y1-.64;ww=min(1.7,rw-.1)
            for aa,bb,cc,dd in [(wx,wy,wx+.035,wy+.6),(wx+ww-.035,wy,wx+ww,wy+.6),(wx,wy+.565,wx+ww,wy+.6)]:
                rect((aa,bb,z+.08,cc,dd,z+2.25),'timber',f,'furniture')
            rect((wx,wy,z+2.22,wx+ww,wy+.6,z+2.26),'timber',f,'furniture')
            for j in range(3):
                aa=wx+j*ww/3+.012;rect((aa,wy,z+.12,aa+ww/3-.024,wy+.035,z+2.21),'timber',f,'furniture')
                beam((aa+ww/3-.07,wy-.018,z+.9),(aa+ww/3-.07,wy-.018,z+1.2),.008,'brass',f,'furniture')
            furnishing('bed',room,box(bx-.05,by-.12,bx+bw+.05,by+bl+.04))
            furnishing('wardrobe',room,box(wx,wy,wx+ww,wy+.6))
            rect((bx-.32,by+.65,z+.012,bx+bw+.32,min(by+bl+.45,y1-.65),z+.018),'rug',f,'rug')
        elif kind in ('living','family'):
            # Position along the right wall so the entry axis remains open.
            sy=y0+.28;sx=x1-.9;length=min(2.35,rd-.5)
            if length>1.5:
                rb((sx+.2,sy+length/2,z+.25),(.92,length,.28),'fabric',f,r=.07)
                rb((sx+.57,sy+length/2,z+.65),(.20,length,.74),'fabric',f,r=.06)
                for end in (sy+.08,sy+length-.08):rb((sx+.16,end,z+.55),(.9,.18,.50),'fabric',f,r=.06)
                for j in range(3):
                    yy=sy+.26+j*(length-.50)/3
                    rb((sx+.1,yy+(length-.50)/6,z+.46),(.69,(length-.54)/3,.20),'linen',f,r=.055)
                for j in (0,1):ball((sx+.18,sy+.5+j*max(.6,length-1.),z+.69),(.15,.27,.25),'fabric-dark',f,'furniture',(.2,.2,0))
                for yy in (sy+.2,sy+length-.2):cylinder((sx+.16,yy,z+.085),.025,.17,'brass',f,'furniture')
                furnishing('sofa',room,box(sx-.28,sy-.02,sx+.69,sy+length+.02))
                tx=sx-1.0;ty=sy+length*.53
                rb((tx,ty,z+.36),(.75,1.1,.06),'stone',f,r=.09)
                for xx in (tx-.22,tx+.22):cylinder((xx,ty,z+.18),.045,.33,'timber',f,'furniture')
                furnishing('coffee-table',room,box(tx-.375,ty-.55,tx+.375,ty+.55))
                rect((max(x0+.12,tx-1),max(y0+.06,sy-.15),z+.014,x1-.1,min(y1-.06,sy+length+.15),z+.022),'rug',f,'rug')
                # Books and a hollow ceramic vessel.
                rect((tx-.22,ty-.28,z+.394,tx+.06,ty-.08,z+.427),'linen',f,'detail')
                vessel=trimesh.creation.revolve(np.array([[.055,0],[.08,.08],[.075,.16],[.055,.18],[.045,.18],[.064,.15],[.068,.08],[.04,.015]]),sections=24)
                node(asset(vessel,smooth=True),'ceramic',(tx+.13,ty+.1,z+.394),floor=f,role='detail')
            if rd>3.4:chair(x0+.9,y1-1.1,z,f,-.45)
            lamp(cx,y0+rd*.52,z+H-.9,f,True)
        elif kind=='dining':
            # Keep left route to kitchen/stair clear.
            tx=x0+rw*.62;ty=y0+rd*.48;tw=min(1.7,rw*.48);td=.85
            rb((tx,ty,z+.75),(tw,td,.07),'timber',f,r=.035)
            for xx in (-tw*.35,tw*.35):
                for yy in (-.26,.26):beam((tx+xx,ty+yy,z+.04),(tx+xx,ty+yy,z+.72),.038,'timber',f,'furniture')
            for xx in (-tw*.27,tw*.27):
                chair(tx+xx,ty-.67,z,f,math.pi);chair(tx+xx,ty+.67,z,f,0)
            furnishing('dining-set',room,box(tx-tw/2-.1,ty-.92,tx+tw/2+.1,ty+.92))
            for xx in (-tw*.25,tw*.25):
                for yy in (-.22,.22):
                    cylinder((tx+xx,ty+yy,z+.798),.115,.013,'ceramic',f,'detail')
                    cylinder((tx+xx+.15,ty+yy,z+.84),.034,.09,'glass',f,'detail')
            lamp(tx,ty,z+2.20,f,True)
        elif kind=='kitchen':
            # Real counter runs on non-circulation edges; separate fronts and handles.
            dep=.6;run=max(1.8,rw-.15);ky=y0+.08
            for j in range(max(2,int(run/.6))):
                xx=x0+.07+j*run/max(2,int(run/.6));ww=run/max(2,int(run/.6))
                rect((xx,ky,z+.10,xx+ww-.02,ky+dep,z+.83),'timber',f,'furniture')
                for zz in (.30,.59):
                    rect((xx+.02,ky+dep,z+zz,xx+ww-.035,ky+dep+.022,z+zz+.20),'wall',f,'furniture')
                    beam((xx+.14,ky+dep+.04,z+zz+.15),(xx+ww-.14,ky+dep+.04,z+zz+.15),.007,'frame',f,'detail')
            rect((x0+.04,ky-.02,z+.83,x0+run+.10,ky+dep+.06,z+.87),'stone',f,'furniture')
            # Sink opening represented with a real hollow vessel above an open inset.
            basin=trimesh.creation.revolve(np.array([[.07,0],[.20,.04],[.25,.11],[.25,.14],[.23,.15],[.22,.12],[.18,.06],[.07,.025]]),sections=32)
            node(asset(basin,smooth=True),'frame',(x0+run*.7,ky+.32,z+.865),floor=f,role='detail')
            beam((x0+run*.7,ky+.1,z+.88),(x0+run*.7,ky+.1,z+1.17),.012,'brass',f,'detail')
            beam((x0+run*.7,ky+.1,z+1.17),(x0+run*.7,ky+.28,z+1.17),.012,'brass',f,'detail')
            for xx in (.3,.59):
                for yy in (.18,.42):cylinder((x0+xx,ky+yy,z+.88),.095,.016,'frame',f,'detail')
            rect((x0+.15,ky+.08,z+1.60,x0+.92,ky+.5,z+1.7),'frame',f,'detail')
            furnishing('kitchen-run',room,box(x0+.04,ky-.02,x0+run+.10,ky+dep+.06))
            if rd>2.8 and rw>3.5:
                ix=x0+rw*.57;iy=y1-.95
                rect((ix-.70,iy-.30,z+.10,ix+.70,iy+.30,z+.86),'timber',f,'furniture')
                rb((ix,iy,z+.885),(1.48,.72,.055),'stone',f,r=.016)
                furnishing('island',room,box(ix-.74,iy-.36,ix+.74,iy+.36))
        elif kind=='bathroom':
            # Wall-side vanity with hollow basin, faucet and mirror frame.
            vx=x1-.80;vy=y1-.52
            rect((vx-.33,vy-.22,z+.20,vx+.33,vy+.22,z+.77),'timber',f,'furniture')
            rb((vx,vy,z+.79),(.72,.50,.045),'stone',f,r=.02)
            bowl=trimesh.creation.revolve(np.array([[.035,0],[.18,.03],[.245,.115],[.24,.15],[.22,.16],[.215,.13],[.17,.065],[.035,.028]]),sections=32)
            node(asset(bowl,smooth=True),'ceramic',(vx,vy,z+.812),floor=f,role='detail')
            beam((vx+.21,vy+.10,z+.82),(vx+.21,vy+.10,z+1.12),.012,'brass',f,'detail')
            beam((vx+.21,vy+.10,z+1.12),(vx+.08,vy+.10,z+1.12),.012,'brass',f,'detail')
            rect((vx-.31,y1-.025,z+1.08,vx+.31,y1-.009,z+1.82),'glass',f,'detail')
            # WC sculpted bowl + seat ring (visual fixture, not a technical sanitary model).
            wx=x1-.55;wy=y0+.44
            ball((wx,wy,z+.22),(.20,.29,.22),'ceramic',f,'furniture')
            torus=trimesh.creation.torus(major_radius=.17,minor_radius=.03,major_sections=24,minor_sections=8)
            node(asset(torus,smooth=True),'ceramic',(wx,wy-.04,z+.44),(.95,1.45,1),floor=f,role='detail')
            rb((wx,wy+.27,z+.55),(.39,.18,.62),'ceramic',f,r=.05)
            furnishing('vanity',room,box(vx-.36,vy-.25,vx+.36,vy+.25))
            furnishing('wc',room,box(wx-.23,wy-.4,wx+.23,wy+.37))
        elif kind in ('study','utility'):
            if kind=='study':
                tx=x0+rw*.50;ty=y0+.38;tw=min(1.6,rw-.4)
                rect((tx-tw/2,ty-.28,z+.72,tx+tw/2,ty+.28,z+.77),'timber',f,'furniture')
                for xx in (tx-tw/2+.07,tx+tw/2-.07):rect((xx-.03,ty-.22,z,xx+.03,ty+.22,z+.72),'frame',f,'furniture')
                chair(tx,ty+.65,z,f)
                furnishing('desk',room,box(tx-tw/2,ty-.28,tx+tw/2,ty+.94))
                rect((tx-.20,ty-.1,z+.79,tx+.2,ty-.085,z+1.10),'frame',f,'detail')
                lamp(tx+tw/2-.15,ty,z+.77,f)
            else:
                rb((x1-.42,y1-.39,z+.46),(.65,.60,.89),'ceramic',f,r=.03)
                ring=trimesh.creation.torus(major_radius=.20,minor_radius=.035,major_sections=24,minor_sections=8)
                node(asset(ring,smooth=True),'frame',(x1-.42,y1-.70,z+.45),rot=(math.pi/2,0,0),floor=f,role='detail')
                furnishing('laundry',room,box(x1-.745,y1-.69,x1-.095,y1-.09))
        # One restrained plant away from the doorway, not at every corner.
        if kind in ('living','family','study') and rw>3 and rd>3:plant(x0+.3,y1-.35,z,.64,f)

    for st in b['stairs']:
        p=box(st['x']/1000,st['y']/1000,(st['x']+st['width'])/1000,(st['y']+st['depth'])/1000)
        colliders.append({'id':st['id']+'/stair-walk-not-supported','floor':st['floor'],'polygon':list(p.exterior.coords),'kind':'stair'})
    # Guarding follows the actual open terrace perimeter; it is a visual scheme, not a certified balustrade.
    for terr in [s for s in b['spaces'] if s['kind']=='terrace']:
        p=Polygon(np.array(terr['polygon'])/1000);f=terr['floor'];z=f*H
        for a,c in zip(list(p.exterior.coords),list(p.exterior.coords)[1:]):
            edge=LineString([a,c])
            if fp.boundary.buffer(.01).covers(edge):
                beam((*a,z+1.1),(*c,z+1.1),.023,'frame',f,'railing')
                length=edge.length
                for t0 in np.arange(.08,length,.95):
                    q=edge.interpolate(t0);beam((q.x,q.y,z+.02),(q.x,q.y,z+1.1),.018,'frame',f,'railing')
                glass=edge.buffer(.012,cap_style=2);poly_mesh(glass,z+.12,z+1.05,'glass',f,'railing')
        center=p.representative_point();plant(center.x,center.y,z,.8,f)
    # A true U stair: 18 risers, two flights, mid/top landings, no upper slab over the well.
    for st in b['stairs']:
        if st['to_floor'] is None:continue
        f=st['floor'];z=f*H;x=st['x']/1000;y=st['y']/1000;r=st['riser_mm']/1000;t=st['tread_mm']/1000;fw=st['flight_width']/1000;well=st['well']/1000;land=st['landing_mm']/1000
        for j in range(8):
            yy=y+land+j*t
            rect((x,yy,z+max(0,j*r-.08),x+fw,yy+t,z+(j+1)*r),'stone',f,'stair')
        # Landings and structural-stringer intent are visual coordination only.
        mid_y=y+land+8*t
        rect((x,mid_y,z+9*r-.16,x+2*fw+well,mid_y+land,z+9*r),'stone',f,'stair')
        for j in range(8):
            yy=y+land+(7-j)*t
            rect((x+fw+well,yy,z+9*r+j*r-.09,x+2*fw+well,yy+t,z+(10+j)*r),'stone',f,'stair')
        rect((x,y,z+H-.16,x+2*fw+well,y+land,z+H),'stone',f+1,'stair')
        # Handrails and pickets follow the two flight slopes.
        for xrail,start_z,ascending in [(x+fw-.04,z,True),(x+fw+well+.04,z+H,False)]:
            za=start_z+r if ascending else start_z;zb=z+9*r
            beam((xrail,y+land,za+.9),(xrail,mid_y,zb+.9),.025,'timber',f,'railing')
            for j in range(9):
                yy=y+land+j*t;zz=(z+(j+1)*r) if ascending else (z+H-j*r)
                beam((xrail,yy,zz),(xrail,yy,zz+.89),.010,'frame',f,'railing')

    # Facade geometry varies by language; reserve glazing and entry spans first.
    canopy_depth=2.05 if facade_style=='tropical' else 1.55 if facade_style in ('warm','terracotta') else 2.45 if theme_id=='warm_modern_minimal' else 1.05
    cw=2.7 if facade_style!='minimal' else 3.25; cz=2.78
    rect((ex-cw/2,-canopy_depth,cz,ex+cw/2,.16,cz+.18),'roof',0,'canopy','entry-canopy')
    rect((ex-cw/2+.07,-canopy_depth+.07,cz-.055,ex+cw/2-.07,.06,cz),'timber',0,'canopy')
    for xx in (ex-cw/2+.12,ex+cw/2-.12):
        if facade_style=='terracotta':cylinder((xx,-canopy_depth+.13,(cz-plinth)/2),.12,cz+plinth,'wall',0,'post')
        else:rect((xx-.085,-canopy_depth+.06,-plinth,xx+.085,-canopy_depth+.23,cz),'stone' if v['style']=='warm' else 'frame',0,'post')
    for xx in (ex-.6,ex+.6):
        cylinder((xx,-canopy_depth*.55,cz-.065),.06,.013,'lamp',0,'fixture')
        lights.append({'position':[xx,-canopy_depth*.55,cz-.1],'color':'#ffdfae','power_w':20,'fixture_visible':True})
    if facade_style=='tropical':
        for xx in np.arange(ex-cw/2,ex+cw/2,.18):rect((xx,-canopy_depth-.25,cz+.2,xx+.05,.22,cz+.31),'timber',0,'pergola')
    if facade_style=='terracotta':
        # Open slatted screen across only the blank stair facade.
        for xx in np.arange(.35,min(2.25,W*.2),.18):
            for yy in (0,.08):rect((xx,-.24-yy,.65,xx+.05,-.18-yy,top+.5),'stone',0,'screen')
    if facade_style in ('warm','graphite','concrete'):
        blank_width=1.05 if b['storeys']>1 else .6
        rect((.24,-.16,.15,.24+blank_width,-.015,top+.36),'stone',0,'accent','stone-blade')
        if facade_style=='graphite':
            for xx in np.arange(.27,.24+blank_width,.12):rect((xx,-.215,.25,xx+.023,-.17,top+.4),'brass',0,'fin')
    if facade_style in ('minimal','concrete'):
        for f in range(b['storeys']):rect((-.15,-.45,(f+1)*H-.23,W+.15,.07,(f+1)*H-.13),'roof',f,'canopy')

    # Reference-led exterior assemblies. These are real scene components
    # derived from the accepted building revision, not a viewport overlay.
    if theme_id != 'current':
        for assembly in exterior.get('assemblies',[]):
            geo=assembly['geometry'];x0,y0,x1,y1=[q/1000 for q in geo['bounds_mm']]
            kind=geo.get('kind');floor=assembly.get('floor_id',0)
            if kind=='porch':
                platform=geo.get('platform_z_mm',-120)/1000
                roof_z=geo.get('canopy_z_mm',2700)/1000
                rect((x0,y0,platform,x1,y1,platform+.10),'stone',0,'porch',assembly['id']+'-platform',assembly['id'])
                rect((x0-.15,y0-.15,roof_z,x1+.15,y1+.15,roof_z+.14),'roof',0,'canopy',assembly['id']+'-roof',assembly['id'])
                count=geo.get('support_count',2)
                for i in range(count):
                    xx=x0+.16+(x1-x0-.32)*i/max(1,count-1)
                    rect((xx-.045,y0+.10,platform,xx+.045,y0+.20,roof_z),'timber',0,'porch',assembly['id']+f'-post-{i}',assembly['id'])
                rect((x0-.15,y0-.15,roof_z+.14,x1+.15,y0-.05,roof_z+.25),'timber',0,'canopy',assembly['id']+'-fascia',assembly['id'])
                # Reference porches read as outdoor rooms from below. Add a
                # timber soffit and a clear portal around the actual entry,
                # so the door is not lost inside a wide white facade.
                for j,xx in enumerate(np.arange(x0+.28,x1-.10,.52)):
                    rect((xx,y0+.10,roof_z-.035,min(x1,xx+.07),y1-.10,roof_z+.025),'timber',0,'soffit',assembly['id']+f'-soffit-{j}',assembly['id'])
                portal_base=max(0.0,platform+.10);portal_top=min(roof_z-.18,2.60)
                rect((ex-.78,-.10,portal_base,ex-.62,.05,portal_top),'timber',0,'door-portal',assembly['id']+'-door-portal-left',assembly['id'])
                rect((ex+.62,-.10,portal_base,ex+.78,.05,portal_top),'timber',0,'door-portal',assembly['id']+'-door-portal-right',assembly['id'])
                rect((ex-.78,-.12,portal_top,ex+.78,.06,portal_top+.14),'timber',0,'door-portal',assembly['id']+'-door-portal-head',assembly['id'])
                for xx in (x0+(x1-x0)*.34,x0+(x1-x0)*.66):
                    cylinder((xx,y0+.38,roof_z-.13),.07,.02,'lamp',0,'fixture')
                    lights.append({'position':[xx,y0+.38,roof_z-.16],'color':'#ffdfae','power_w':24,'fixture_visible':True})
                # Keep the centerline clear and furnish the porch as a
                # usable arrival room; these are exterior objects only.
                if x1-x0>3.0:
                    seat_x=min(x1-1.25,max(x0+1.15,ex+1.0));seat_y=y0+(y1-y0)*.53
                    rb((seat_x,seat_y,platform+.40),(1.55,.54,.28),'fabric',0,'outdoor-furniture',.07,owner=assembly['id'])
                    rb((seat_x,seat_y+.22,platform+.75),(1.55,.12,.43),'fabric',0,'outdoor-furniture',.06,owner=assembly['id'])
                    for j,dx in enumerate((-1.18,1.18)):
                        rb((seat_x+dx,seat_y-.05,platform+.34),(.62,.60,.24),'fabric-dark',0,'outdoor-furniture',.07,owner=assembly['id'])
                    rb((seat_x,seat_y-.78,platform+.30),(.78,.62,.08),'stone',0,'outdoor-furniture',.08,owner=assembly['id'])
                # A low planted edge makes the covered space read as a room-
                # sized threshold rather than a floating entry canopy.
                rect((x0+.12,y0+.18,platform+.10,x0+.28,y1-.12,platform+.52),'stone',0,'planter',assembly['id']+'-planter',assembly['id'])
                for xx in np.linspace(x0+.48,x0+.95,2):plant(xx,y0+.42,platform+.52,.30,0)
            elif kind=='side_verandah':
                platform=geo.get('platform_z_mm',-120)/1000
                roof_z=geo.get('canopy_z_mm',2700)/1000
                side_x0=max(x0,W)
                rect((side_x0+.02,y0+.28,platform,x1-.04,y1,platform+.10),'stone',0,'verandah',assembly['id']+'-platform',assembly['id'])
                rect((side_x0-.10,y0+.10,roof_z,x1+.10,y1,roof_z+.14),'roof',0,'canopy',assembly['id']+'-roof',assembly['id'])
                for j,yy in enumerate(np.linspace(y0+.45,y1-.25,geo.get('support_count',3))):
                    rect((x1-.16,yy-.045,platform,x1-.06,yy+.045,roof_z),'timber',0,'verandah',assembly['id']+f'-post-{j}',assembly['id'])
                rect((side_x0+.18,y1-.13,platform+.10,side_x0+.48,y1-.02,platform+.68),'stone',0,'planter',assembly['id']+'-edge-planter',assembly['id'])
                rb((x1-.54,y0+1.05,platform+.40),(.95,.48,.28),'fabric',0,'outdoor-furniture',.07,owner=assembly['id'])
            elif kind=='side_courtyard':
                platform=geo.get('platform_z_mm',-120)/1000
                # Full-length pavers, a raised planting strip and low wall
                # lights turn the narrow setback into a usable side passage.
                rect((x0,y0,platform,x1,y1,platform+.045),'paver',0,'side-courtyard',assembly['id']+'-paving',assembly['id'])
                planter_x0=x1-.36;planter_x1=x1-.06
                rect((planter_x0,y0+.18,platform+.045,planter_x1,y1-.18,platform+.36),'stone',0,'planter',assembly['id']+'-planter-edge',assembly['id'])
                rect((planter_x0+.045,y0+.24,platform+.36,planter_x1-.045,y1-.24,platform+.40),'soil',0,'landscape',assembly['id']+'-soil',assembly['id'])
                for j,yy in enumerate(np.arange(y0+.75,y1-.45,1.55)):
                    plant(planter_x0+.15,yy,platform+.40,.42,0)
                for j,yy in enumerate(np.arange(y0+.85,y1-.30,geo.get('light_spacing_mm',2200)/1000)):
                    rect((x1-.08,yy-.04,platform+.12,x1+.02,yy+.04,platform+.64),'lamp',0,'fixture',assembly['id']+f'-light-{j}',assembly['id'])
                    lights.append({'position':[x1-.02,yy,platform+.58],'color':'#ffdfae','power_w':8,'fixture_visible':True})
            elif kind=='feature_wall':
                h=geo.get('height_mm',top*1000-180)/1000
                rect((x0,y0,0,x1,y1,h),'stone',0,'massing',assembly['id'],assembly['id'])
                rect((x0-.05,y0-.06,h,x1+.05,y1+.06,h+.12),'timber',0,'roof-edge',assembly['id']+'-cap',assembly['id'])
                for j,xx in enumerate(np.arange(x0+.26,x1-.05,.34)):
                    rect((xx,y0-.055,.18,min(x1,xx+.035),y0+.015,h-.12),'timber',0,'screen',assembly['id']+f'-fin-{j}',assembly['id'])
            elif kind=='facade_frame':
                h=geo.get('height_mm',3150)/1000;z=H
                depth=geo.get('depth_mm',320)/1000
                for j,xx in enumerate((x0,x1-.14)):
                    rect((xx,y0,z,xx+.14,y1,h+z),'frame',1,'massing',assembly['id']+f'-pier-{j}',assembly['id'])
                rect((x0,y0,h+z-.16,x1,y1,h+z),'roof',1,'roof-edge',assembly['id']+'-head',assembly['id'])
                rect((x0-depth,y0-depth,z,x1+depth,y0+.02,z+.08),'frame',1,'roof-edge',assembly['id']+'-lower-reveal',assembly['id'])
            elif kind=='balcony':
                z=floor*H+geo.get('platform_z_mm',v['floor_height_mm']-120)/1000
                rect((x0,y0,z,x1,y1,z+.12),'stone',floor,'balcony',assembly['id']+'-slab',assembly['id'])
                rail=z+geo.get('rail_height_mm',1100)/1000
                rect((x0,y0-.03,rail,x1,y0+.05,rail+.08),'frame',floor,'railing',assembly['id']+'-front-rail',assembly['id'])
                rect((x0-.03,y0,z,x0+.05,y1,rail),'frame',floor,'railing',assembly['id']+'-left-rail',assembly['id'])
                rect((x1-.05,y0,z,x1+.03,y1,rail),'frame',floor,'railing',assembly['id']+'-right-rail',assembly['id'])
                for j,xx in enumerate(np.arange(x0+.15,x1,.72)):
                    rect((xx-.018,y0-.01,z+.10,xx+.018,y0+.04,rail),'frame',floor,'railing',assembly['id']+f'-baluster-{j}',assembly['id'])
                rect((x0,y0+.06,z+.10,x1,y0+.09,rail-.05),'glass',floor,'railing',assembly['id']+'-glass',assembly['id'])
                # A partial timber privacy blade gives the deeper balcony a
                # side condition and makes its usable depth read in elevation.
                if x1-x0>3.8:
                    for j,yy in enumerate(np.arange(y0+.20,y1-.12,.28)):
                        rect((x1-.20,yy-.035,z+.16,x1-.11,yy+.035,min(z+1.95,rail+.06)),'timber',floor,'screen',assembly['id']+f'-privacy-{j}',assembly['id'])
                if geo.get('planter_edge'):
                    rect((x0+.25,y0-.22,z+.12,x1-.25,y0-.02,z+.34),'stone',floor,'landscape',assembly['id']+'-planter',assembly['id'])
                    for xx in np.arange(x0+.5,x1-.3,1.0):
                        plant(xx,y0-.10,z+.34,.34,floor)
                else:
                    # Furnish the balcony at a real 2.2 m-depth scale.
                    rb(((x0+x1)/2,y0+(y1-y0)*.56,z+.42),(1.65,.52,.30),'fabric',floor,'outdoor-furniture',.08,owner=assembly['id'])
                    rb(((x0+x1)/2,y0+(y1-y0)*.73,z+.72),(1.65,.12,.42),'fabric',floor,'outdoor-furniture',.06,owner=assembly['id'])
                    rb(((x0+x1)/2,y0+(y1-y0)*.22,z+.38),(.55,.55,.34),'stone',floor,'outdoor-furniture',.08,owner=assembly['id'])
                # A slim upper reveal integrates the balcony with the roofline.
                # The reveal belongs just above the balcony head, not above
                # the roof. The previous offset made a visibly floating slab.
                rect((x0-.12,y0-.18,z+.35,x1+.12,y1+.08,z+.48),'roof',floor,'roof-edge',assembly['id']+'-upper-reveal',assembly['id'])
            elif kind in ('screen','accent'):
                h=geo.get('height_mm',top*1000-400)/1000
                material='stone' if theme_id=='earth_terracotta' or kind=='accent' else 'timber'
                if kind=='accent':
                    rect((x0,y0,0,x1,y1,h),material,0,'accent',assembly['id'],assembly['id'])
                elif x1-x0 < y1-y0:
                    spacing=max(0.12,geo.get('spacing_mm',180)/1000)
                    for j,yy in enumerate(np.arange(y0,y1,spacing)):
                        rect((x0,yy,0,x1,min(y1,yy+geo.get('slat_depth_mm',55)/1000),h),material,0,'screen',assembly['id']+f'-slat-{j}',assembly['id'])
                else:
                    spacing=max(0.12,geo.get('spacing_mm',180)/1000)
                    for j,xx in enumerate(np.arange(x0,x1,spacing)):
                        rect((xx,y0,0,min(x1,xx+geo.get('slat_depth_mm',55)/1000),y1,h),material,0,'screen',assembly['id']+f'-slat-{j}',assembly['id'])
            elif kind=='pergola':
                z=geo.get('z_mm',2850)/1000
                rect((x0,y0,z,x1,y0+.08,z+.12),'timber',0,'pergola',assembly['id']+'-header',assembly['id'])
                for j,xx in enumerate(np.arange(x0+.15,x1,.42)):
                    rect((xx,y0, z, min(x1,xx+.09),y1,z+.12),'timber',0,'pergola',assembly['id']+f'-slat-{j}',assembly['id'])
        for feature in exterior.get('landscape',{}).get('features',[]):
            if feature['kind'] in ('path','planting_bed'):
                # Exterior metadata remains in millimetres; scene geometry is metres.
                p=Polygon(np.array(feature['polygon'],dtype=float)/1000)
                mat='paver' if feature['kind']=='path' else 'soil'
                poly_mesh(p,g+.004,g+.025,mat,-1,'landscape',feature['id'],feature['id'])
                if feature['kind']=='planting_bed':
                    border=p.buffer(.045).difference(p)
                    poly_mesh(border,g+.025,g+.12,'stone',-1,'landscape',feature['id']+'-raised-edge',feature['id'])
            elif feature['kind']=='tree':
                x,y=[q/1000 for q in feature['position_mm']]
                plant(x,y,g,feature.get('scale',.9),-1,tree=True)
            elif feature['kind']=='shrub':
                x,y=[q/1000 for q in feature['position_mm']]
                plant(x,y,g,feature.get('scale',.42))
        boundary=exterior.get('landscape',{}).get('boundary',{})
        if boundary:
            gate_x=boundary.get('gate_center_mm',ex*1000)/1000
            gate_w=boundary.get('gate_width_mm',2200)/1000
            rect((gate_x-gate_w/2,ymin+.18,.78,gate_x+gate_w/2,ymin+.25,.86),'timber',-1,'gate','exterior-gate-header','exterior-gate')
    # String courses, downpipes and concealed roof drainage intent.
    for f in range(b['storeys']):rect((0,-.045,(f+1)*H-.20,W,.015,(f+1)*H-.12),'roof',f,'band')
    for xx in (.10,W-.10):
        beam((xx,D+.08,.10),(xx,D+.08,top+.35),.034,'roof',-1,'pipe')
        beam((xx,D+.08,.10),(xx,D+.36,-.22),.034,'roof',-1,'pipe')
    # Warm fixture bollards; actual lights are tied to visible lamp geometry.
    for xx in (ex-1.3,ex+1.3):
        for yy in np.arange(ymin+.9,-.9,1.6):
            rect((xx-.055,yy-.055,-.43,xx+.055,yy+.055,.07),'frame',role='fixture')
            rect((xx-.051,yy-.051,.06,xx+.051,yy+.051,.12),'lamp',role='fixture')
            lights.append({'position':[xx,yy,.15],'color':'#ffdfae','power_w':6,'fixture_visible':True})
    if v['pooja']:
        # An explicitly labelled niche in the 2D schedule, not an invented room.
        xx=W-.65;yy=b['brief']['floor_height_mm']/1000+.3
        rect((xx-.27,yy-.13,.5,xx+.27,yy+.13,1.0),'timber',0,'furniture','pooja-niche')
        rect((xx-.25,yy-.12,1.03,xx+.25,yy+.12,1.07),'stone',0,'furniture')
        cylinder((xx,yy,1.17),.06,.18,'brass',0,'detail')
    # Exact generated scene, not an image substitute.
    return {'schema':'floorforge.scene/0.3','units':'m','up':'Z','materials':materials,'assets':assets,'nodes':nodes,
            'lights':lights,'colliders':colliders,'furniture':furniture,'floor_height':H,'storeys':b['storeys'],
            'bounds':[xmin,ymin,-plinth,xmax,ymax,top+.7],'footprint':(np.array(b['footprint'])/1000).tolist(),
            'entry':[float(ex),-.15,1.6],'solar':report['solar'],'style':v['style'],
            'exterior_theme':theme_id,'interior_theme':exterior.get('interior_theme','current'),
            'exterior_revision':exterior.get('revision'),'exterior_review':exterior.get('review',{}),
            'cameras':{'hero':{'position':[W*1.90,-max(16,D*1.34),top*.68+3.0],'target':[W*.47,D*.25,top*.40],'fov':43},
                       'dollhouse':{'position':[W*1.45,-D*.52,top+max(W,D)*1.55],'target':[W*.5,D*.5,1.],'fov':42},
                       'interior':{'position':[ex,.65,1.6],'target':[W*.72,4.0,1.35],'fov':66}},
            'quality':'Authored procedural geometry; native viewer is a raster study, not verified photorealism.',
            'banner':b['banner']}


def transformation(node):
    m=trimesh.transformations.euler_matrix(*node['rotation'],'sxyz')
    m[:3,:3] = m[:3,:3] @ np.diag(node['scale']);m[:3,3]=node['position'];return m


def glb_bytes(scene):
    out=trimesh.Scene();geometries={}
    for n in scene['nodes']:
        key=n['asset']+'@'+n['material'];a=scene['assets'][n['asset']]
        if key not in geometries:
            m=trimesh.Trimesh(vertices=a['vertices'],faces=a['faces'],process=False)
            color=scene['materials'][n['material']]['color']; rgb=[int(color[i:i+2],16) for i in (1,3,5)]
            mat=scene['materials'][n['material']]
            material=trimesh.visual.material.PBRMaterial(name=n['material'],baseColorFactor=rgb+[round(255*mat.get('alpha',1))],
                metallicFactor=mat.get('metallic',0),roughnessFactor=mat['roughness'],alphaMode='BLEND' if mat.get('alpha',1)<1 else 'OPAQUE',doubleSided=True)
            m.visual=trimesh.visual.TextureVisuals(material=material)
            m.metadata={'source_asset':n['asset'],'scope':'preliminary authored component'}
            out.geometry[key]=m;geometries[key]=m
        # Z-up (m) -> Y-up (m) at export boundary.
        convert=trimesh.transformations.rotation_matrix(-math.pi/2,[1,0,0])
        out.graph.update(frame_to=n['id'],matrix=convert@transformation(n),geometry=key,
                         metadata={'owner':n['owner'],'floor':n['floor'],'role':n['role']})
    out.metadata={'banner':scene['banner'],'units':'m','up':'Y','geometry_scope':'individual closed components plus thin decorative surfaces; not a boolean-unioned building'}
    return out.export(file_type='glb')
