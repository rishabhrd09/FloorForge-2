"""One vector drawing list drives SVG and physically-sized PDF sheets."""
from __future__ import annotations
from pathlib import Path
from .model import *
from .scene import opening_polygon, transformation
from .frontage import gate_openings
from shapely.geometry import Polygon, LineString, Point
from shapely import get_parts
from shapely.ops import unary_union
import numpy as np, html, io, math, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

INK='#25372f';LIGHT='#a8afa4';PAPER='#ffffff'

def P(points,fill='none',stroke=INK,width=.2,layer='A-WALL',closed=True):return {'type':'poly','points':[[float(x),float(y)] for x,y in points],'fill':fill,'stroke':stroke,'width':width,'layer':layer,'closed':closed}
def T(x,y,text,size=250,layer='A-ANNO',anchor='middle'):return {'type':'text','x':float(x),'y':float(y),'text':str(text),'size':size,'layer':layer,'anchor':anchor}
def L(a,b,stroke=INK,width=.15,layer='A-ANNO',dash=False):return {'type':'line','a':list(a),'b':list(b),'stroke':stroke,'width':width,'layer':layer,'dash':dash}

def dim(items,a,b,offset,axis='x',label=None):
    if axis=='x':p=(a[0],offset);q=(b[0],offset);val=abs(b[0]-a[0]);txt=((p[0]+q[0])/2,offset+150)
    else:p=(offset,a[1]);q=(offset,b[1]);val=abs(b[1]-a[1]);txt=(offset+150,(p[1]+q[1])/2)
    items.extend([L(a,p,LIGHT,.12,'A-DIMS'),L(b,q,LIGHT,.12,'A-DIMS'),L(p,q,INK,.15,'A-DIMS')])
    for xx,yy in (p,q):items.append(L((xx-60,yy-60),(xx+60,yy+60),INK,.2,'A-DIMS'))
    items.append(T(*txt,label if label is not None else str(round(val)),200,'A-DIMS','middle' if axis=='x' else 'start'))


def plan_elements(b,scene,floor=0):
    elems=[];v=b['brief'];H=v['floor_height_mm'];fp=Polygon(b['footprint']);W,D=fp.bounds[2:]
    for room in [s for s in b['spaces'] if s['floor']==floor]:
        p=Polygon(room['clear']); elems.append(P(room['clear'],'#f0f3ef' if room['kind'] in ('bathroom','utility') else '#fafaf6','none',layer='A-FLOOR'))
    for wall in [w for w in b['walls'] if w['floor']==floor]:
        p=Polygon(wall['polygon'])
        for o in b['openings']:
            if o['wall_id']==wall['id'] and o['sill']<=1200<o['sill']+o['height']:p=p.difference(opening_polygon(wall,o))
        for part in get_parts(p):
            if part.geom_type=='Polygon':elems.append(P(list(part.exterior.coords),INK,INK,.25))
    hosts={w['id']:w for w in b['walls']}
    for o in [o for o in b['openings'] if o['floor']==floor]:
        w=hosts[o['wall_id']];a=np.array(w['a']);bb=np.array(w['b']);u=(bb-a)/np.linalg.norm(bb-a);n=np.array([-u[1],u[0]]);p=a+u*o['offset'];q=p+u*o['width'];m=(p+q)/2
        if not fp.covers(__import__('shapely').Point(*(m+n*400))):n=-n
        if o['kind']=='window':
            for shift in (-25,25):elems.append(L(p+n*shift,q+n*shift,'#657e77',.16,'A-WIND',o['sill']>1200))
        elif o['kind']!='cased':
            elems.append(L(p,p+n*o['width'],INK,.18,'A-DOOR'))
            pts=[p+o['width']*(u*math.cos(t)+n*math.sin(t)) for t in np.linspace(0,math.pi/2,20)]
            elems.append(P(pts,'none',LIGHT,.13,'A-DOOR',False))
        if o['kind']!='window':elems.append(T(*(m-n*260),o['id'].split('-')[-1],155,'A-ANNO'))
    # Show the accepted exterior footprint in the plan drawing so the porch,
    # balcony and screens are inspectable outside the wall line.
    exterior=b.get('exterior',{})
    for assembly in exterior.get('assemblies',[]):
        if assembly.get('floor_id') not in (floor, -1):
            continue
        x0,y0,x1,y1=assembly['geometry']['bounds_mm']
        elems.append(P([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],'none','#9e653f',.3,'A-EXT'))
        elems.append(T((x0+x1)/2,y0-120,assembly['role'].upper(),130,'A-EXT'))
    for furniture in scene['furniture']:
        if furniture['floor']==floor:elems.append(P(np.array(furniture['footprint'])*1000,'none','#a9afa6',.12,'A-FURN'))
    for room in [s for s in b['spaces'] if s['floor']==floor]:
        p=Polygon(room['clear']); c=p.representative_point()
        elems += [T(c.x,c.y+130,room['name'],245),T(c.x,c.y-150,f'{room["area_m2"]:.1f} m² | {room["area_m2"]*10.7639:.0f} ft²',175)]
        if room['kind'] in ('bedroom','kitchen','bathroom','study'):
            bx=p.bounds
            elems.append(T(c.x,c.y-390,f'{(bx[2]-bx[0])/1000:.2f} × {(bx[3]-bx[1])/1000:.2f} m',160))
    for st in [s for s in b['stairs'] if s['floor']==floor]:
        x,y=st['x'],st['y'];fw=st['flight_width'];land=st['landing_mm'];t=st['tread_mm']
        for k in range(9):
            yy=y+land+k*t;elems.append(L((x,yy),(x+fw,yy),INK,.14,'A-STAIR'))
            elems.append(L((x+fw+st['well'],yy),(x+st['width'],yy),INK,.14,'A-STAIR'))
        elems.append(L((x+fw/2,y+land),(x+fw/2,y+land+8*t),INK,.3,'A-STAIR'))
        elems.append(T(x+fw/2,y+land+8*t+200,'UP' if floor==0 else 'DN',180,'A-STAIR'))
        elems.append(T(x+st['width']/2,y+400,f'18R @ {st["riser_mm"]:.0f}; T {t}',150,'A-STAIR'))
    dim(elems,(0,0),(W,0),-700)
    dim(elems,(W,0),(W,D),W+850,'y')
    # Front opening chain follows actual wall coordinates.
    chain={0.,W}
    for o in b['openings']:
        w=hosts[o['wall_id']]
        if o['floor']==floor and w['external'] and max(w['a'][1],w['b'][1])<240:
            direction=(np.array(w['b'])-w['a'])/math.dist(w['a'],w['b'])
            for shift in (o['offset'],o['offset']+o['width']):chain.add(float(w['a'][0]+direction[0]*shift))
    values=sorted(chain)
    for a,c in zip(values,values[1:]):
        if c-a>=150:dim(elems,(a,0),(c,0),-1250)
    # Room partition dimensions across rear band.
    xs=sorted(set([0.,W]+[p[0] for s in b['spaces'] if s['floor']==floor for p in s['polygon'] if abs(p[1]-D)<1]))
    for a,c in zip(xs,xs[1:]):dim(elems,(a,D),(c,D),D+650)
    n=enu_to_local(0,1,v['road_bearing_deg']);origin=(-1200,D-500)
    elems.extend([L(origin,(origin[0]+n[0]*800,origin[1]+n[1]*800),INK,.45),T(origin[0]+n[0]*1100,origin[1]+n[1]*1100,'N',280)])
    ext_y=min([a['geometry']['bounds_mm'][1] for a in exterior.get('assemblies',[])]+[-1800])
    return elems,(min(-1900,ext_y-350),min(-1800,ext_y-350),W+1700,D+1500)


def site_elements(b,scene):
    v=b['brief'];fp=Polygon(b['footprint']);plot=Polygon(b['plot']);xmin,ymin,xmax,ymax=plot.bounds;W,D=fp.bounds[2:]
    elems=[P(list(plot.exterior.coords),'#f0f3eb',INK,.35,'A-SITE'),P(b['footprint'],'#dadfd6',INK,.4)]
    for f in scene['furniture']:pass
    elems.extend([P([(xmin-1000,ymin-4500),(xmax+1000,ymin-4500),(xmax+1000,ymin-200),(xmin-1000,ymin-200)],'#e8e8e2',LIGHT,.2,'A-SITE'),T((xmin+xmax)/2,ymin-2600,'ROAD / WIDTH TO BE SURVEYED',230)])
    ex=scene['entry'][0]*1000
    elems.append(P([(ex-1000,ymin),(ex+1000,ymin),(ex+1000,0),(ex-1000,0)],'#f9f8ee',LIGHT,.15,'A-SITE'))
    exterior=b.get('exterior',{})
    site_colors={'path':'#e5e0d3','planting_bed':'#b9ad91'}
    for feature in exterior.get('landscape',{}).get('features',[]):
        if 'polygon' in feature:
            elems.append(P(feature['polygon'],site_colors.get(feature['kind'],'#d8dfd1'),'#819076',.22,'A-LAND'))
        elif feature['kind'] in ('tree','shrub'):
            x,y=feature['position_mm'];r=feature.get('mature_canopy_radius_mm',350 if feature['kind']=='shrub' else 900)
            elems.append(P(list(Point(x,y).buffer(r).exterior.coords),'#c8d4ba','#819076',.18,'A-LAND'))
    for x,y,txt in [(W/2,-v['front_mm']/2,'FRONT COURT'),(-v['left_mm']/2,D/2,'OPEN'),(W+v['right_mm']/2,D/2,'OPEN'),(W/2,D+v['rear_mm']/2,'REAR YARD')]:
        elems.append(T(x,y,txt,180))
    boundary=exterior.get('landscape',{}).get('boundary',{})
    if boundary:
        # Each gate in the front wall: the vehicle gate's sliding leaf (closed) with its track, the pedestrian
        # gate's leaf open on its swing arc, and the letterbox pier beside it.
        for x0,x1,gate in gate_openings(boundary):
            if gate.get('operation')=='sliding':
                elems.append(L((x0,ymin+170),(x1,ymin+170),'#9e653f',.45,'A-GATE'))
                run=min(x1-x0,gate.get('park_run_mm',x1-x0));t0,t1=((x0-run,x0) if gate.get('park')=='left' else (x1,x1+run))
                elems.extend([L((t0,ymin+230),(t1,ymin+230),'#9e653f',.18,'A-GATE',True),T((x0+x1)/2,ymin+700,'SLIDING GATE',140,'A-GATE')])
            else:
                hx=x1 if gate.get('hinge')=='right' else x0;r=x1-x0;sgn=-1 if gate.get('hinge')=='right' else 1
                elems.append(L((hx,ymin+150),(hx,ymin+150+r),'#9e653f',.35,'A-GATE'))
                arc=[(hx+sgn*r*math.cos(t),ymin+150+r*math.sin(t)) for t in np.linspace(0,math.pi/2,10)]
                elems.append(P(arc,'none','#9e653f',.15,'A-GATE',closed=False))
        pier=boundary.get('letterbox_pier')
        if pier:elems.append(P([(pier['x0_mm'],ymin-60),(pier['x1_mm'],ymin-60),(pier['x1_mm'],ymin+210),(pier['x0_mm'],ymin+210)],'#8f8a80',INK,.2,'A-SITE'))
    for a,c,ofs in [((xmin,ymin),(xmax,ymin),ymax+750)]:dim(elems,a,c,ofs)
    dim(elems,(xmax,ymin),(xmax,ymax),xmax+800,'y')
    dim(elems,(W,0),(W,D),W+350,'y')
    n=enu_to_local(0,1,v['road_bearing_deg']);px=xmin+700;py=ymax-1300
    elems.extend([L((px,py),(px+n[0]*800,py+n[1]*800),INK,.5),T(px+n[0]*1100,py+n[1]*1100,'N',280)])
    return elems,(xmin-1200,ymin-4900,xmax+1700,ymax+1600)


def elevation_elements(b,direction,scene=None):
    v=b['brief'];W,D=Polygon(b['footprint']).bounds[2:];H=v['floor_height_mm'];top=b['storeys']*H;elems=[]
    horizontal=direction in ('Front','Rear');span=W if horizontal else D
    elems.append(P([(0,-v['plinth_mm']),(span,-v['plinth_mm']),(span,top+600),(0,top+600)],'#f2f0e7',INK,.25))
    for f in range(b['storeys']+1):elems.append(L((0,f*H),(span,f*H),INK,.35))
    hosts={w['id']:w for w in b['walls']}
    for o in b['openings']:
        w=hosts[o['wall_id']]
        if not w['external']:continue
        selected=(direction=='Front' and max(w['a'][1],w['b'][1])<240) or (direction=='Rear' and min(w['a'][1],w['b'][1])>D-240) or (direction=='Left' and max(w['a'][0],w['b'][0])<240) or (direction=='Right' and min(w['a'][0],w['b'][0])>W-240)
        if not selected:continue
        u=(np.array(w['b'])-w['a'])/math.dist(w['a'],w['b']);p=np.array(w['a'])+u*o['offset'];q=p+u*o['width'];axis=0 if horizontal else 1;a=min(p[axis],q[axis]);c=max(p[axis],q[axis]);z=o['floor']*H+o['sill']
        elems.append(P([(a,z),(c,z),(c,z+o['height']),(a,z+o['height'])],'#dfe8e7',INK,.25,'A-WIND'))
        if o['width']>1200:elems.append(L(((a+c)/2,z),((a+c)/2,z+o['height']),INK,.15,'A-WIND'))
    # Exterior masses use the same accepted millimetre contract as the plan
    # and scene. They are deliberately schematic rather than construction detail.
    for assembly in b.get('exterior',{}).get('assemblies',[]):
        geo=assembly['geometry'];x0,y0,x1,y1=geo['bounds_mm'];kind=geo.get('kind');floor=assembly.get('floor_id',0)
        if kind=='stair_tower':
            # Seen from every side: the stair's headroom box rising above the roof.
            a,c=(x0,x1) if horizontal else (y0,y1);z1=top+geo.get('height_mm',2700)
            elems.append(P([(a,top),(c,top),(c,z1),(a,z1)],'#e3ddd2','#9e653f',.3,'A-EXT'))
            elems.append(T((a+c)/2,z1+130,'STAIR TOWER',130,'A-EXT'))
            continue
        selected=(direction=='Front' and y1<=300) or (direction=='Rear' and y0>=D-300) or (direction=='Left' and x1<=300) or (direction=='Right' and x1>=W-300 and x0<=W+300)
        if not selected:continue
        if horizontal:
            a,c=x0,x1;z0=floor*H
        else:
            a,c=y0,y1;z0=floor*H
        if kind in ('porch','side_verandah'):z0=geo.get('platform_z_mm',-120)+0.;z1=geo.get('canopy_z_mm',2700)+200
        elif kind=='balcony':z0=floor*H-120;z1=z0+geo.get('rail_height_mm',1100)+120
        else:z1=z0+geo.get('height_mm',top*1000-400)
        elems.append(P([(a,z0),(c,z0),(c,z1),(a,z1)],'none','#9e653f',.3,'A-EXT'))
        elems.append(T((a+c)/2,z1+130,assembly['role'].upper(),130,'A-EXT'))
    dim(elems,(0,0),(span,0),-850)
    dim(elems,(span,0),(span,top),span+700,'y')
    return elems,(-500,-1300,span+1500,top+1200)


def section_elements(b,scene):
    import trimesh
    cut=1.1 if b['storeys']>1 else Polygon(b['footprint']).centroid.x/1000
    elems=[]
    for n in scene['nodes']:
        if n['role'] not in ('wall','floor','roof','stair','plinth'):continue
        a=scene['assets'][n['asset']];m=trimesh.Trimesh(vertices=a['vertices'],faces=a['faces'],process=False);m.apply_transform(transformation(n))
        if not m.bounds[0,0]-.001<=cut<=m.bounds[1,0]+.001:continue
        for line in trimesh.intersections.mesh_plane(m,plane_normal=[1,0,0],plane_origin=[cut,0,0]):
            elems.append(L((line[0,1]*1000,line[0,2]*1000),(line[1,1]*1000,line[1,2]*1000),INK,.25,'A-SECT'))
    D=Polygon(b['footprint']).bounds[3];top=b['storeys']*b['brief']['floor_height_mm'];dim(elems,(D,0),(D,top),D+700,'y')
    return elems,(-900,-1000,D+1700,top+1400),cut


def make_sheets(b,scene,report):
    sheets=[]
    def add(id,title,elements,bounds,notes,table=None):
        width=bounds[2]-bounds[0];height=bounds[3]-bounds[1]
        scale=next(s for s in [50,75,100,125,150,200,250,300,500,750,1000] if width/s<=220 and height/s<=202)
        sheets.append({'id':id,'title':title,'elements':elements,'bounds':bounds,'scale':scale,'notes':notes,'table':table or [],'page_mm':[420,297]})
    for f in range(b['storeys']):
        e,bb=plan_elements(b,scene,f)
        rows=[['SPACE','CLEAR AREA','SIZE / m']]
        for s in b['spaces']:
            if s['floor']==f:
                q=Polygon(s['clear']).bounds
                rows.append([s['name'],f'{s["area_m2"]:.2f} m2',f'{(q[2]-q[0])/1000:.2f} x {(q[3]-q[1])/1000:.2f}'])
        add(f'A-10{f+1}','Ground floor' if f==0 else 'First floor',e,bb,
            ['All plan dimensions are millimetres.','Clear areas exclude walls; open zones are named separately.',
             'Nominal door widths are not finished accessible clear widths.','Above-cut windows are dashed. Furniture is schematic at true scale.',
             'No certified IS 962 or local code compliance is claimed.'],rows)
    e,bb=site_elements(b,scene)
    add('A-001','Site & arrival',e,bb,['Setbacks are design assumptions, not verified byelaws.','Road width, property line and levels need a survey.',
        'No surveyed drainage fall or flood datum supplied.','Default steps are not a step-free route.'],[['AREA STATEMENT','VALUE','UNIT'],
        ['Plot',report['areas']['plot_m2'],'m2'],['Footprint',report['areas']['footprint_m2'],'m2'],['Gross floors',report['areas']['gross_floor_m2'],'m2'],
        ['Coverage',report['areas']['ground_coverage_pct'],'percent'],['Geometric FAR',report['areas']['geometric_far'],'ratio']])
    for i,d in enumerate(['Front','Rear','Left','Right']):
        e,bb=elevation_elements(b,d,scene);add(f'A-20{i+1}',d+' elevation',e,bb,
            ['Wall and opening heights derive from the building model.','This elevation records the primary wall plane.',
             'Decorative facade accessories are coordinated in 3D, not fully detailed here.','No cladding anchors or construction joints are designed.'])
    e,bb,cut=section_elements(b,scene)
    add('A-301',f'Section A-A / x = {cut:.2f} m',e,bb,['Actual mesh-plane intersections, not a generic stair illustration.',
        'Cut objects: walls, floor slabs, roof, stair and plinth.','No reinforcement or foundation design is represented.',
        'Stair headroom and handrails require a separate professional check.'])
    # Coordination axes are intentionally not advertised as a complete RCC scheme.
    e=[];fp=Polygon(b['footprint']);W,D=fp.bounds[2:]
    e.append(P(b['footprint'],'none',LIGHT,.2))
    xs=[115,W/2,W-115];ys=[115,D/2,D-115]
    for i,x in enumerate(xs):e.append(L((x,-600),(x,D+600),LIGHT,.15,'S-GRID',True));e.append(T(x,-1000,chr(65+i),250,'S-GRID'))
    for i,y in enumerate(ys):e.append(L((-600,y),(W+600,y),LIGHT,.15,'S-GRID',True));e.append(T(-1000,y,str(i+1),250,'S-GRID'))
    add('S-001','Coordination axes / NOT a structural design',e,(-1800,-1700,W+1200,D+1000),[
        'Axes shown for coordination only; they are NOT column locations.','No column, beam, slab or footing is sized or certified.',
        'Engineer must establish an actual load path and lateral system.','No soil-bearing capacity is inferred from a soil photograph.'])
    return sheets


def svg_sheet(sheet,b):
    bb=sheet['bounds'];s=sheet['scale'];x0=20+(220-(bb[2]-bb[0])/s)/2;y0=51+(202-(bb[3]-bb[1])/s)/2
    def xy(x,y):return (x0+(x-bb[0])/s,297-y0-(y-bb[1])/s)
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">',
         '<rect width="420" height="297" fill="white"/><g font-family="Arial,Helvetica,sans-serif">']
    def txt(x,y,t,size=3,anchor='start',color=INK):out.append(f'<text x="{x:.4f}" y="{y:.4f}" fill="{color}" font-size="{size}" text-anchor="{anchor}">{html.escape(str(t))}</text>')
    out.append(f'<path d="M 16 31 H 404 M 16 271 H 404" stroke="{INK}" stroke-width=".35"/>')
    txt(17,17,'FLOORFORGE',5.2);txt(17,25,sheet['title'],3.1);txt(403,18,sheet['id'],5,'end');txt(403,25,'REV A / PRELIMINARY',2.6,'end')
    for e in sheet['elements']:
        if e['type']=='poly':
            pts=' '.join(f'{x:.4f},{y:.4f}' for x,y in [xy(*p) for p in e['points']])
            tag='polygon' if e['closed'] else 'polyline';out.append(f'<{tag} points="{pts}" fill="{e["fill"]}" stroke="{e["stroke"]}" stroke-width="{e["width"]}"/>')
        elif e['type']=='line':
            a,c=xy(*e['a']),xy(*e['b']);dash=' stroke-dasharray="1.2 .6"' if e.get('dash') else ''
            out.append(f'<path d="M {a[0]:.4f} {a[1]:.4f} L {c[0]:.4f} {c[1]:.4f}" fill="none" stroke="{e["stroke"]}" stroke-width="{e["width"]}"{dash}/>')
        elif e['type']=='text':
            x,y=xy(e['x'],e['y']);txt(x,y,e['text'],max(1.45,e['size']/s),e['anchor'])
    out.append(f'<path d="M 250 42 V 256" stroke="#c9d0c7" stroke-width=".2"/>')
    txt(261,46,b['brief']['title'],3.8)
    yy=57
    for i,row in enumerate(sheet['table']):
        for j,value in enumerate(row):txt([261,330,367][j],yy,str(value)[:31],2.2 if i else 2.35)
        yy+=6.3
    yy=max(yy+12,150);txt(261,yy,'DRAWING NOTES',2.7);yy+=8
    for note in sheet['notes']:
        for line in textwrap.wrap(note,59):txt(261,yy,line,2.25);yy+=4.3
        yy+=2.5
    txt(261,244,f'SCALE 1:{s} AT A3 / CUT +1200 mm',2.4)
    txt(261,251,'Dimensions govern; do not scale from a screen.',2.2)
    # 4 metre scale bar in paper units.
    xa,ya=22,259;out.append(f'<path d="M {xa} {ya} H {xa+4000/s}" stroke="{INK}" stroke-width=".6"/>')
    for dist in (0,2000,4000):
        xx=xa+dist/s;out.append(f'<path d="M {xx} {ya-1} V {ya+1}" stroke="{INK}" stroke-width=".2"/>');txt(xx,ya+5,f'{dist//1000} m',1.9,'middle')
    txt(17,279,b['banner'],2.65,color='#8a4933');txt(17,286,'Reference design screen only. Survey, structure, services, byelaws and professional approval remain outstanding.',2.15)
    txt(403,283,f'{sheet["id"]}  |  420 x 297 mm',2.35,'end');out.append('</g></svg>');return ''.join(out)


def pdf_sheets(sheets,b,report):
    buf=io.BytesIO();c=canvas.Canvas(buf,pagesize=(420*72/25.4,297*72/25.4),invariant=1,pageCompression=1)
    mm=72/25.4
    def text(x,y,t,size=3):
        c.setFillColor(HexColor(INK));c.setFont('Helvetica',size*mm);c.drawString(x*mm,y*mm,str(t).replace('²','2').replace('×','x').replace('₹','INR '))
    for sh in sheets:
        c.setTitle('FloorForge preliminary drawing and review pack');bb=sh['bounds'];scale=sh['scale'];ox=20+(220-(bb[2]-bb[0])/scale)/2;oy=51+(202-(bb[3]-bb[1])/scale)/2
        def point(x,y):return ((ox+(x-bb[0])/scale)*mm,(oy+(y-bb[1])/scale)*mm)
        text(17,280,'FLOORFORGE',5.2);text(17,272,sh['title'],3.1);text(361,280,sh['id'],5)
        c.setStrokeColor(HexColor(INK));c.setLineWidth(.35*mm);c.line(16*mm,266*mm,404*mm,266*mm);c.line(16*mm,26*mm,404*mm,26*mm)
        for e in sh['elements']:
            if e['type']=='poly':
                path=c.beginPath();p=point(*e['points'][0]);path.moveTo(*p)
                for p in e['points'][1:]:path.lineTo(*point(*p))
                if e['closed']:path.close()
                fill=e['fill']!='none';stroke=e['stroke']!='none'
                if fill:c.setFillColor(HexColor(e['fill']))
                if stroke:c.setStrokeColor(HexColor(e['stroke']))
                c.setLineWidth(e['width']*mm);c.setDash();c.drawPath(path,fill=fill,stroke=stroke)
            elif e['type']=='line':
                c.setStrokeColor(HexColor(e['stroke']));c.setLineWidth(e['width']*mm);c.setDash([1.2*mm,.6*mm] if e.get('dash') else [])
                c.line(*point(*e['a']),*point(*e['b']));c.setDash()
            else:
                x,y=point(e['x'],e['y']);c.setFont('Helvetica',max(1.45,e['size']/scale)*mm);c.setFillColor(HexColor(INK));txt=e['text'].replace('²','2').replace('×','x')
                if e['anchor']=='middle':c.drawCentredString(x,y,txt)
                else:c.drawString(x,y,txt)
        c.setStrokeColor(HexColor('#c9d0c7'));c.setLineWidth(.2*mm);c.line(250*mm,41*mm,250*mm,255*mm)
        text(261,251,b['brief']['title'],3.8);yy=240
        for i,row in enumerate(sh['table']):
            for j,val in enumerate(row):text([261,330,367][j],yy,str(val)[:31],2.2 if i else 2.35)
            yy-=6.3
        yy=min(yy-12,147);text(261,yy,'DRAWING NOTES',2.7);yy-=8
        for note in sh['notes']:
            for line in textwrap.wrap(note,59):text(261,yy,line,2.25);yy-=4.3
            yy-=2.5
        text(261,53,f'SCALE 1:{scale} AT A3 / CUT +1200 mm',2.4);text(261,46,'Dimensions govern; do not scale from a screen.',2.2)
        c.setStrokeColor(HexColor(INK));c.setLineWidth(.6*mm);c.line(22*mm,38*mm,(22+4000/scale)*mm,38*mm)
        for dist in (0,2000,4000):text(22+dist/scale,32,f'{dist//1000} m',1.9)
        text(17,18,b['banner'],2.65);text(17,11,'Survey, structure, services, byelaws and professional approval remain outstanding.',2.15);c.showPage()
    # Programmatic report pages, using line wrapping and measured page bounds.
    sections=[('REVIEW / SCOPE',[('Geometry',report['review']['status']),('Regulatory',report['review']['regulatory']),('Structure',report['review']['structural']),('Accessibility',report['review']['accessibility'])],
        ['Passing geometric checks is not evidence of construction safety or statutory compliance.',*['Warning: '+w.get('message',w['code']) for w in report['review']['warnings']]]),
      ('COST / SCENARIO',[('Gross floor area',f'{report["areas"]["gross_floor_ft2"]} ft2'),('Illustrative range',f'INR {report["cost"]["low_lakh"]} - {report["cost"]["high_lakh"]} lakh'),('Owner budget',f'INR {report["cost"]["budget_lakh"]} lakh'),('Rates',str(report['cost']['rates_inr_ft2'])+' INR/ft2')],
       [report['cost']['basis'],'Excluded: '+', '.join(report['cost']['excludes']),'No reinforcement quantities or cement bag counts are invented from floor area.']),
      ('SITE / SERVICES / STRUCTURE',[('Soil',report['structure']['soil']),('Foundation recommendation','NOT PROVIDED: requires geotechnical design'),('Solar elevation',f'{report["solar"]["elevation_deg"]:.2f} degrees'),('Vastu score',str(report['vastu']['score'])+' / advisory only')],
       [report['structure']['soil_warning'],*report['mep']['notes'],report['vastu']['limitation'],'Solar method: '+report['solar']['method']]),
      ('TIMELINE / ASSUMPTIONS',[(x['phase'],f'Week {x["start_week"]} + {x["duration_weeks"]} weeks') for x in report['timeline']],
       ['Illustrative overlapping phases, not a contractual or local construction schedule.','No government review period or supply lead time has been verified.']),
      ('OPENING SCHEDULE',[(o['id'],f'{o["kind"]} / {o["width"]:.0f} x {o["height"]:.0f} / sill {o["sill"]:.0f} mm') for o in b['openings']],
       ['Nominal wall opening dimensions. Frames, tolerances and clear passage require detailing.'])]
    for title,rows,notes in sections:
        # Split large schedules across pages rather than clipping them.
        for page in range(max(1,math.ceil(len(rows)/23))):
            text(20,276,'FLOORFORGE / '+title,4.5);yy=252
            for key,value in rows[page*23:(page+1)*23]:
                text(22,yy,key,3);text(135,yy,str(value),3);yy-=7.2
            yy=min(yy-15,115)
            for note in notes:
                for line in textwrap.wrap(note,135):text(22,yy,line,2.8);yy-=5
                yy-=4
            text(20,16,b['banner'],2.6);c.showPage()
    c.save();return buf.getvalue()


def dxf_export(b,scene,path):
    import ezdxf, uuid
    doc=ezdxf.new('R2018',setup=True);doc.units=4
    doc.ezdxf_metadata()['CREATED_BY_EZDXF']='ezdxf '+ezdxf.__version__+' / FloorForge deterministic export'
    doc.header['$INSUNITS']=4;doc.header['$MEASUREMENT']=1
    for k in ('$TDCREATE','$TDUPDATE','$TDUCREATE','$TDUUPDATE'):doc.header[k]=2451544.5
    for k in ('$FINGERPRINTGUID','$VERSIONGUID'):doc.header[k]='{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'floorforge:'+sha(b)+k)).upper()+'}'
    for layer,color in [('A-WALL',7),('A-WIND',4),('A-DOOR',3),('A-FLOOR',8),('A-FURN',8),('A-ANNO',7),('A-DIMS',7),('A-STAIR',7),('A-SITE',8),('S-GRID',8)]:
        if layer not in doc.layers:doc.layers.new(layer,dxfattribs={'color':color,'lineweight':35 if layer=='A-WALL' else 18})
    doc.appids.new('FLOORFORGE');msp=doc.modelspace();W=Polygon(b['footprint']).bounds[2]
    for f in range(b['storeys']):
        offset=f*(W+6000);elements,_=plan_elements(b,scene,f)
        for e in elements:
            layer=e['layer'];attrs={'layer':layer}
            if e['type']=='poly':
                pts=[(x+offset,y) for x,y in e['points']]
                entity=msp.add_lwpolyline(pts,close=e['closed'],dxfattribs=attrs)
                if e['fill']==INK:
                    h=msp.add_hatch(color=7,dxfattribs=attrs);h.paths.add_polyline_path(pts,is_closed=True)
            elif e['type']=='line':entity=msp.add_line((e['a'][0]+offset,e['a'][1]),(e['b'][0]+offset,e['b'][1]),dxfattribs=attrs)
            else:
                from ezdxf.enums import TextEntityAlignment
                entity=msp.add_text(e['text'],dxfattribs={**attrs,'height':e['size']})
                entity.set_placement((e['x']+offset,e['y']),align=TextEntityAlignment.MIDDLE_CENTER if e['anchor']=='middle' else TextEntityAlignment.LEFT)
            entity.set_xdata('FLOORFORGE',[(1000,f'floor:{f}'),(1000,'preliminary')])
        fp=Polygon(b['footprint']);D=fp.bounds[3]
        for p1,p2,base,angle in [((offset,0),(offset+W,0),(offset,-2100),0),((offset+W,0),(offset+W,D),(offset+W+2100,0),90)]:
            d=msp.add_linear_dim(base=base,p1=p1,p2=p2,angle=angle,dimstyle='EZDXF',override={'dimtxt':200,'dimasz':120,'dimexo':80,'dimexe':80},dxfattribs={'layer':'A-DIMS'});d.render()
        msp.add_text(b['banner'],dxfattribs={'height':190,'layer':'A-ANNO'}).set_placement((offset,-2900))
        msp.add_text(f'FLOOR {f} / TRUE MILLIMETRES / NO STRUCTURAL CERTIFICATION',dxfattribs={'height':210,'layer':'A-ANNO'}).set_placement((offset,D+1800))
        layout=doc.layouts.new('GROUND' if f==0 else f'FLOOR-{f}')
        layout.page_setup(size=(420,297),margins=(10,10,10,10),units='mm')
        layout.add_viewport(center=(140,145),size=(240,230),view_center_point=(offset+W/2,D/2),view_height=max(D+4500,(W+6000)*230/240))
        layout.add_text('FLOORFORGE / PRELIMINARY',dxfattribs={'height':4}).set_placement((268,255))
    # ezdxf rewrites update timestamps, version GUIDs and its metadata on save.
    # Use its fixed-metadata mode only during serialization, then restore options.
    # This export stage runs in the single-worker generation queue.
    old_fixed=ezdxf.options.write_fixed_meta_data_for_testing
    try:
        ezdxf.options.write_fixed_meta_data_for_testing=True
        doc.saveas(path)
    finally:
        ezdxf.options.write_fixed_meta_data_for_testing=old_fixed
    # Give each design its own stable GUID rather than the testing constant.
    lines=Path(path).read_text('utf8').splitlines()
    for i in range(0,len(lines)-3,2):
        if lines[i].strip()=='9' and lines[i+1] in ('$FINGERPRINTGUID','$VERSIONGUID'):
            lines[i+3]='{'+str(uuid.uuid5(uuid.NAMESPACE_URL,'floorforge:'+sha(b)+lines[i+1])).upper()+'}'
    Path(path).write_bytes(('\n'.join(lines)+'\n').encode('utf8'))
    check=ezdxf.readfile(path);audit=check.audit()
    if audit.has_errors:raise DesignError('DXF_REIMPORT','DXF audit reported errors.',[str(x) for x in audit.errors])
    return {'status':'ezdxf_reimport_pass','entities':len(check.modelspace()),'units':'mm','dimension_entities':len(check.modelspace().query('DIMENSION')),
            'autocad_gui':'NOT TESTED','annotation_scope':'Floor plans and model-space dimensions; elevations and section are in PDF/SVG, not in this DXF.'}
