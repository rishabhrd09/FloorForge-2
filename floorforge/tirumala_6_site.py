"""Plot enclosure in building coordinates (mm). +X is north, +Y is west."""
from collections import defaultdict
from math import pi

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union


def boundary_layout(building, gate_spans):
    """Use the house itself wherever an exterior wall already meets the plot line."""
    width, depth = Polygon(building['plot']).bounds[2:]
    house = unary_union([Polygon(w['polygon']) for w in building['walls'] if w['floor']==0])
    ground = -building['brief']['plinth_mm']
    gates = []
    for name, kind, a, b in gate_spans:
        lo, hi = sorted([a, b])
        gates.append(dict(id=name, kind=kind, x0_mm=lo, x1_mm=hi,
                          operation='sliding' if kind=='pedestrian' else 'paired-swing',
                          park='right', base_mm=0 if kind=='pedestrian' else building['planning']['lowerPorchMm'],
                          height_mm=1450))
    breaks = unary_union([box(g['x0_mm']-100, -1, g['x1_mm']+100, 150) for g in gates])
    sides = [('west', (0,depth),(width,depth)), ('north',(width,0),(width,depth)),
             ('south',(0,0),(0,depth)), ('east',(0,0),(width,0))]
    parts, runs = [], []
    def piece(ident, owner, bounds, material):
        parts.append(dict(id=ident, owner=owner, bounds=list(bounds), material=material))
    for side,a,b in sides:
        axis=LineString([a,b]).difference(house)
        if side=='east':axis=axis.difference(breaks)
        for i,line in enumerate(getattr(axis,'geoms',[axis])):
            if line.is_empty or line.length<1:continue
            x,y,X,Y=line.bounds
            # North/south returns terminate against the east and west wall faces.
            if side in ('north','south'):
                y,Y=max(120,y),min(depth-120,Y)
                if Y<=y:continue
                if side=='south':X=x+120
                else:x=X-120
            elif side=='west':y=Y-120
            else:Y=y+120
            ident=f't6-boundary-{side}-{i}'
            privacy=side in ('south','west') or side=='east' and X<=min(g['x0_mm'] for g in gates)+1
            screen=side=='east' and not privacy and X-x>900
            height=1650 if privacy else 1230 if screen else 1050
            top=ground+height
            cap=ground+510 if screen else top
            runs.append(dict(id=ident,side=side,polygon=list(box(x,y,X,Y).exterior.coords)[:-1],height_mm=height))
            piece(ident,ident,(x,y,ground,X,Y,cap-38),'wall')
            piece(ident+'-cap',ident,(x,y,cap-38,X,Y,cap),'travertine')
            if screen:
                count=max(1,round((X-x)/1400))
                for j in range(count+1):
                    post=x+17+(X-x-34)*j/count
                    piece(f'{ident}-post-{j}',ident,(post-17,40,cap,post+17,82,top),'frame')
                for j in range(8):
                    z=cap+21+j*88
                    piece(f'{ident}-slat-{j}',ident,(x,24,z,X,53,z+55),'smoked-oak')
    for gate in gates:
        lo,hi,h=gate['x0_mm'],gate['x1_mm'],gate['height_mm']
        z=gate['base_mm']+25
        # Posts sit outside the dimensioned opening. The narrow central return
        # shares the masonry between the two gate jambs.
        for j,(start,end) in enumerate([(lo-100,lo),(hi,hi+100)]):
            piece(f"{gate['id']}-jamb-{j}",f"{gate['id']}-jamb-{j}",(start,0,ground,end,140,z+h+40),'travertine')
        middle=(lo+hi)/2
        panels=[(lo+8,hi-8)] if gate['operation']=='sliding' else [(lo+8,middle-5),(middle+5,hi-8)]
        for j,(start,end) in enumerate(panels):
            name=f"{gate['id']}-leaf-{j}"
            for suffix,rect in [('foot',(start,162,z,end,207,z+45)),('head',(start,162,z+h-40,end,207,z+h)),
                                ('left',(start,162,z+45,start+32,207,z+h-40)),('right',(end-32,162,z+45,end,207,z+h-40))]:
                piece(name+'-'+suffix,name,rect,'frame')
            for row in range(15):
                bottom=z+61+89*row
                piece(f'{name}-blade-{row}',name,(start+32,170,bottom,end-32,198,bottom+65),'smoked-oak')
    return dict(runs=runs, parts=parts, gates=gates)


def build_enclosure(kit, scene, boundary):
    leaves=defaultdict(list)
    for part in boundary['parts']:
        bounds=[v/1000 for v in part['bounds']]
        moving='-leaf-' in part['owner']
        kit.rect(bounds,part['material'],0,'gate' if moving else 'wall',part['id'],part['owner'])
        if moving:leaves[part['owner']].append(part['id'])
    scene['gate_model']=[]
    for g in boundary['gates']:
        lo,hi=g['x0_mm']/1000,g['x1_mm']/1000
        w=hi-lo;base=(g['base_mm']+25)/1000
        motion=[]
        if g['operation']=='sliding':
            motion.append(dict(ids=leaves[g['id']+'-leaf-0'], slide=[w+.02,0,0]))
        else:
            for j,pivot,angle in [(0,lo+.008,pi/2),(1,hi-.008,-pi/2)]:
                motion.append(dict(ids=leaves[f"{g['id']}-leaf-{j}"],pivot=[pivot,.185,base],angle=angle))
        scene['gate_model'].append(dict(id=g['id'],label='East pedestrian gate' if g['kind']=='pedestrian' else 'Car porch gate',
                                        kind='gate',floor=0,start=[lo,.185,base],axis=[1,0,0],
                                        base=base,sill=0,width=w,height=g['height_mm']/1000,initial=0,parts=motion))


def ramp_geometry(ramp):
    """Eight vertices in mm, with a 100 mm apron under the sloped face."""
    x,X,y,Y,lo,hi=(ramp[k] for k in ('x0','x1','y0','y1','z0','z1'))
    top=[(x,y,lo),(X,y,lo),(X,Y,hi),(x,Y,hi)]
    vertices=top+[(a,b,z-100) for a,b,z in top]
    faces=[(0,1,2),(0,2,3),(4,6,5),(4,7,6)]
    for i in range(4):
        j=(i+1)%4
        faces.extend([(i,4+i,4+j),(i,4+j,j)])
    return vertices,faces


def add_vehicle_ramp(kit,ramp):
    import trimesh
    vertices,faces=ramp_geometry(ramp)
    mesh=trimesh.Trimesh(vertices=[[c/1000 for c in v] for v in vertices],faces=faces)
    kit.node(kit.asset(mesh),'flagstone',floor=0,role='floor',name='car-entry-ramp',owner='east-porch')
