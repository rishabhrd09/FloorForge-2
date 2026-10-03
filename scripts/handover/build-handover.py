"""An owner-to-engineer print set from the unchanged saved FloorForge model."""
from pathlib import Path
import sys, json, math, shutil, textwrap, zipfile, io
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from shapely.geometry import Polygon, LineString, box
from shapely.ops import polylabel
from floorforge.drawings import (make_sheets, primitives, principal_rect, opening_types,
                                T, P, L, C, DIM, bounds_of, level_scale, building_levels, INK, LIGHT)
from floorforge.rooftop import with_rooftop_objects
from floorforge.scene import transformation

SRC = ROOT / 'examples/gallery/my-desired-home'
OUT = ROOT / 'output/pdf'
VIEWS = ROOT / 'tmp/pdfs/views'
OUT.mkdir(parents=True, exist_ok=True)
b, scene, report = [json.loads((SRC / (name + '.json')).read_text()) for name in ('building', 'scene', 'report')]
full = with_rooftop_objects(b)
assert b['planHash'] == scene['planHash'] == report['review']['planHash']
assert not report['review']['errors']
sheets = {s['id']: s for s in make_sheets(b, scene, report)}
MM = 72 / 25.4
W, H = 420, 297
BLUE, GREY, RED = '#315865', '#5a6868', '#954b40'
PALE, LINE = '#f3f6f5', '#ccd6d3'
PDF = OUT / 'my-desired-home-engineer-handover.pdf'
c = canvas.Canvas(str(PDF), pagesize=(W*MM,H*MM), pageCompression=1, invariant=1)
c.setTitle('My Desired Home - architectural concept and engineer handover')
c.setAuthor('FloorForge / owner design study')
c.setSubject('Saved 60 x 55 ft G+1 design; preliminary engineer review; planHash:' + b['planHash'])
c.setKeywords('A3, 1:100, architectural floor plans, preliminary, not for construction')
page_records=[]
STAIR_CUT_Y = b['stairs'][0]['y'] + b['stairs'][0]['flight_width']/2

def stair_flight_section():
    """Cut the actual rotated stair along its run, using the saved scene meshes."""
    import trimesh
    elems=[]
    for n in scene['nodes']:
        if n['role'] not in ('wall','floor','roof','stair','plinth'):continue
        asset=scene['assets'][n['asset']]
        mesh=trimesh.Trimesh(vertices=asset['vertices'],faces=asset['faces'],process=False)
        mesh.apply_transform(transformation(n))
        cut=STAIR_CUT_Y/1000
        if not mesh.bounds[0,1]-.001<=cut<=mesh.bounds[1,1]+.001:continue
        for seg in trimesh.intersections.mesh_plane(mesh,plane_normal=[0,1,0],plane_origin=[0,cut,0]):
            elems.append(L((seg[0,0]*1000,seg[0,2]*1000),(seg[1,0]*1000,seg[1,2]*1000),INK,.25,'A-SECT'))
    span=Polygon(b['footprint']).bounds[2];v=b['brief'];top=b['storeys']*v['floor_height_mm']
    elems.append(L((-1000,-v['plinth_mm']),(span+1000,-v['plinth_mm']),INK,.5,'A-SITE'))
    for f in range(b['storeys']):
        elems.append(DIM((span,f*v['floor_height_mm']),(span,(f+1)*v['floor_height_mm']),'y',span+700,-1))
    elems.append(DIM((span,-v['plinth_mm']),(span,top),'y',span+1300,-1))
    level_scale(elems,span+2600,building_levels(b))
    return elems,bounds_of(elems)

room_order = [
 ('g-dining','ENTRY HALL'),('g-drawing','DRAWING ROOM'),('g-living','LIVING / DINING'),
 ('g-kitchen','KITCHEN'),('g-kitchen-store','PANTRY'),('g-wash','WASH AREA'),('g-puja','PUJA'),
 ('g-stair','STAIRCASE'),('g-bedroom','MASTER BEDROOM'),('g-bath','ATTACHED BATH'),
 ('g-care','HOME CARE ROOM'),('g-caregiver','CAREGIVER ROOM'),('g-caregiver-bath','CAREGIVER WC'),
 ('g-veranda','VERANDA'),('g-care-lawn','LAWN / GARDEN PATH'),('g-care-court','LIGHTWELL'),
 ('g-court-ledge','COVERED LIGHTWELL EDGE'),('g-bedroom-airgap','REAR VENTILATION RECESS'),
 ('u-lobby','ARRIVAL LOBBY'),('u-office','STUDIO / OFFICE'),('u-stair','STAIRCASE'),
 ('u-lounge','OVERLOOKING LOBBY'),('u-bed-south','BEDROOM 2'),('u-bedroom-balcony','REAR BALCONY'),
 ('u-bath','SHARED BATH'),('u-bed-north','MASTER SUITE'),('u-terrace-north','GARDEN BALCONY'),
 ('u-terrace-front','FRONT / NORTH TERRACE'),('u-studio-terrace','TERRACE RETURN'),
 ('u-veranda-terrace','VERANDA ROOF TERRACE'),('u-living-void','OPEN BELOW'),('u-garden-daylight','OPEN TO SKY'),
 ('south-stair-core-1-roof-landing','ROOF LANDING'),('roof-terrace','ROOF TERRACE'),
]
by_id={s['id']:s for s in full['spaces']}
rooms=[]; counters={0:0,1:0,2:0}
for sid,name in room_order:
    s=by_id[sid]; floor=s['floor']; counters[floor]+=1
    poly=Polygon(s['clear'],s.get('holes',[])); rect=principal_rect(poly)
    dx,dy=rect[2]-rect[0],rect[3]-rect[1]
    irregular=not poly.buffer(1).covers(box(*poly.bounds))
    rooms.append({**s,'code':('G','F','R')[floor]+str(counters[floor]).zfill(2),'short':name,
                  'dx':dx,'dy':dy,'irregular':irregular,'poly':poly})
codes={r['id']:r['code'] for r in rooms}

def clean(s):
    return str(s).replace('\u00b2','2').replace('\u00d7','x').replace('\u00b1','+/-').replace('\u00b7','/').replace('\u2014','-').replace('\u2013','-')

def text(x,y,s,size=3,font='Helvetica',color=INK,anchor='start',rot=0):
    c.setFillColor(HexColor(color));c.setFont(font,size*MM);s=clean(s)
    if rot:
        c.saveState();c.translate(x*MM,y*MM);c.rotate(rot);c.drawCentredString(0,0,s);c.restoreState()
    elif anchor=='middle':c.drawCentredString(x*MM,y*MM,s)
    elif anchor=='end':c.drawRightString(x*MM,y*MM,s)
    else:c.drawString(x*MM,y*MM,s)

def line(x1,y1,x2,y2,color=LINE,width=.2):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width*MM);c.setDash();c.line(x1*MM,y1*MM,x2*MM,y2*MM)

def rect(x,y,w,h,fill=None,stroke=None,width=.2):
    if fill:c.setFillColor(HexColor(fill))
    if stroke:c.setStrokeColor(HexColor(stroke))
    c.setLineWidth(width*MM);c.rect(x*MM,y*MM,w*MM,h*MM,fill=bool(fill),stroke=bool(stroke))

def wrap(s,width,size=3,font='Helvetica'):
    result=[];current=''
    for word in clean(s).split():
        candidate=(current+' '+word).strip()
        if stringWidth(candidate,font,size*MM)>width*MM and current:result.append(current);current=word
        else:current=candidate
    if current:result.append(current)
    return result

def paragraph(x,y,s,width,size=3,leading=4.5,color=GREY,font='Helvetica'):
    for part in wrap(s,width,size,font):text(x,y,part,size,font,color);y-=leading
    return y

def heading(x,y,s,width=100):
    text(x,y,s,3.4,'Helvetica-Bold',BLUE);line(x,y-3,x+width,y-3);return y-10

def start(sid,title,subtitle,scale='NTS'):
    n=len(page_records)+1
    page_records.append({'sheet':sid,'title':title,'page':n,'scale':scale})
    c.bookmarkPage(sid);c.addOutlineEntry(sid+' - '+title,sid,level=0,closed=False)
    text(14,282,'MY DESIRED HOME',5.6,'Helvetica-Bold')
    text(14,274,title,3.5,'Helvetica',BLUE)
    text(14,267,subtitle,2.65,color=GREY)
    text(406,282,sid,5.6,'Helvetica-Bold',anchor='end')
    text(406,275,'OWNER / CIVIL ENGINEER HANDOVER',2.65,anchor='end',color=BLUE)
    text(406,267,'REV A  |  02 OCT 2026',2.65,anchor='end',color=GREY)
    line(14,262,406,262,INK,.4)
    line(14,34,406,34,INK,.4)
    text(14,27,'PRELIMINARY - ENGINEER TO REVIEW - NOT FOR CONSTRUCTION',3,'Helvetica-Bold',RED)
    text(14,19,'Source: saved My Desired Home / 60 x 55 ft / G+1 / east-facing design',2.5,color=GREY)
    text(14,12,'Model reference: '+b['planHash'][:16]+'  |  Architecture and geometry study',2.4,color=GREY)
    text(406,27,('1:'+str(scale)+' AT A3' if isinstance(scale,int) else scale),3,'Helvetica-Bold',anchor='end')
    text(406,19,'A3 LANDSCAPE 420 x 297 mm  |  PRINT 100%',2.5,anchor='end',color=GREY)
    text(406,12,f'SHEET {n:02d} / 11  |  FLOORFORGE',2.4,anchor='end',color=GREY)

def end():c.showPage()

def draw(elements,bounds,scale,area):
    x,y,w,h=area;bw=(bounds[2]-bounds[0])/scale;bh=(bounds[3]-bounds[1])/scale
    assert bw<=w+.01 and bh<=h+.01,(bw,bh,w,h)
    ox=x+(w-bw)/2;oy=y+(h-bh)/2
    def pt(x,y):return ((ox+(x-bounds[0])/scale)*MM,(oy+(y-bounds[1])/scale)*MM)
    for e in primitives(elements):
        typ=e['type']
        if typ=='poly':
            if not e['points']:continue
            path=c.beginPath();path.moveTo(*pt(*e['points'][0]))
            for p in e['points'][1:]:path.lineTo(*pt(*p))
            if e['closed']:path.close()
            fill=e['fill']!='none';stroke=e['stroke']!='none'
            if fill:c.setFillColor(HexColor(e['fill']))
            if stroke:c.setStrokeColor(HexColor(e['stroke']))
            c.setLineWidth(e['width']*MM);c.setDash();c.drawPath(path,fill=fill,stroke=stroke)
        elif typ=='line':
            c.setStrokeColor(HexColor(e['stroke']));c.setLineWidth(e['width']*MM)
            c.setDash([1.1*MM,.65*MM] if e.get('dash') else [])
            c.line(*pt(*e['a']),*pt(*e['b']));c.setDash()
        elif typ=='circle':
            px,py=pt(e['x'],e['y']);c.setStrokeColor(HexColor(e['stroke']));c.setLineWidth(e['width']*MM)
            if e.get('fill','none')!='none':c.setFillColor(HexColor(e['fill']))
            c.circle(px,py,e['r']/scale*MM,stroke=1,fill=e.get('fill','none')!='none')
        else:
            px,py=pt(e['x'],e['y']);size=max(1.8,e['size']/scale)
            if e['layer'] in ('A-DIMS','A-TAGS'):size=max(2.0,size)
            font='Helvetica-Bold' if e['layer']=='HANDOVER-ROOM' else 'Helvetica'
            s=clean(e['text'])
            if e['layer']=='HANDOVER-ROOM':
                tw=stringWidth(s,font,size*MM)
                c.setFillColor(HexColor('#ffffff'));c.rect(px-tw/2-.45*MM,py-.5*MM,tw+.9*MM,(size+1)*MM,fill=1,stroke=0)
            c.setFillColor(HexColor(BLUE if e['layer']=='HANDOVER-ROOM' else INK));c.setFont(font,size*MM)
            if e.get('rot'):
                c.saveState();c.translate(px,py);c.rotate(e['rot']);c.drawCentredString(0,0,s);c.restoreState()
            elif e['anchor']=='middle':c.drawCentredString(px,py,s)
            elif e['anchor']=='end':c.drawRightString(px,py,s)
            else:c.drawString(px,py,s)

def scale_bar(x=27,y=43,scale=100):
    for i in range(4):rect(x+i*1000/scale,y,1000/scale,1.5,INK if i%2==0 else '#ffffff',INK,.18)
    for d in (0,2000,4000):text(x+d/scale,y-4,str(d//1000)+' m',2.4,anchor='middle')

def plan_elements(floor):
    sh=sheets[{0:'A-101',1:'A-102',2:'A-104'}[floor]]
    e=[dict(p) for p in sh['elements'] if p['layer']!='A-SECT' and not(p['type']=='text' and p['layer']=='A-ANNO' and p['text']!='N')]
    # Section A-A follows the rotated stair flight at y=4150, not the original unrotated x axis.
    span=Polygon(b['footprint']).bounds[2]
    for x,sign in [(-1800,-1),(span+1800,1)]:
        e.append(C(x,STAIR_CUT_Y,280,INK,.2,'A-SECT'))
        e.append(T(x,STAIR_CUT_Y-85,'A',220,'A-SECT'))
        edge=0 if sign<0 else span
        e.append(L((edge,STAIR_CUT_Y),(x-sign*280,STAIR_CUT_Y),INK,.1,'A-SECT',True))
        e.append(P([(x-120,STAIR_CUT_Y+280),(x,STAIR_CUT_Y+620),(x+120,STAIR_CUT_Y+280)],INK,INK,.1,'A-SECT'))
    # Room reference replaces long inherited labels; the architectural geometry is unchanged.
    for r in [r for r in rooms if r['floor']==floor]:
        poly=r['poly'];spot=polylabel(poly,10)
        if r['id']=='g-bedroom-airgap':spot=type(spot)(spot.x-850,spot.y+50)
        if r['id']=='u-studio-terrace':spot=type(spot)(spot.x-180,spot.y-440)
        if r['kind']=='void':
            for shift in range(-20000,30000,400):
                cut=poly.intersection(LineString([(shift,-10000),(shift+30000,20000)]))
                for seg in getattr(cut,'geoms',[cut]):
                    if seg.geom_type=='LineString':e.append(P(list(seg.coords),'none','#d4dcd9',.1,'HANDOVER-VOID',False))
        if r['kind']=='stair':
            # Keep the stair walking line and tread notes exposed.
            if floor<2:spot=Polygon(r['clear']).representative_point();spot=type(spot)(r['poly'].bounds[2]-500,r['poly'].bounds[1]+800)
            e.append(T(spot.x,spot.y,r['code'],240,'HANDOVER-ROOM'));continue
        available=2*spot.distance(poly.boundary)
        small=available<1850 or r['id'] in ('u-lounge','g-care-court','g-court-ledge','g-bedroom-airgap','u-studio-terrace')
        name=r['short'];label=r['code']+' '+name
        size=230
        if stringWidth(label,'Helvetica-Bold',size)>max(available-180,400):small=True
        if small:e.append(T(spot.x,spot.y,r['code'],240,'HANDOVER-ROOM'))
        else:
            e.append(T(spot.x,spot.y+160,label,size,'HANDOVER-ROOM'))
            if r['kind']=='void':detail='VOID / NO FLOOR'
            elif floor==2:detail=f'{r["area_m2"]:.2f} m2 / OPEN ROOF'
            else:detail=f'{r["dx"]:.0f} x {r["dy"]:.0f}'+('*' if r['irregular'] else '')+' mm'
            e.append(T(spot.x,spot.y-175,detail,205,'HANDOVER-ROOM'))
    return e,bounds_of(e)

def plan_panel(floor):
    x=303;line(295,48,295,253)
    y=heading(x,252,['GROUND FLOOR KEY','FIRST FLOOR KEY','ROOF LEVEL KEY'][floor],103)
    text(x,y,'REF / SPACE',2.5,'Helvetica-Bold',GREY);text(406,y,'AREA m2',2.5,'Helvetica-Bold',GREY,'end');y-=7
    for r in [r for r in rooms if r['floor']==floor]:
        text(x,y,r['code'],2.6,'Helvetica-Bold',BLUE)
        name=r['short'].title()
        # At this width short room references fit on one line; exact dimensions are on A-601.
        text(x+11,y,name,2.35,color=INK)
        text(406,y,f'{r["area_m2"]:.2f}'+(' v' if r['kind']=='void' else ''),2.35,anchor='end')
        y-=6.1
    y-=5;y=heading(x,y,'READ THIS DRAWING',103)
    for note in [
        'Dimensions in millimetres. Levels in metres relative to the assumed natural ground level (NGL).',
        '* = principal clear rectangle within an irregular room; see A-601 for sizes and actual polygon areas.',
        'D = door; SD = sliding glazing; O = open / cased opening; W = window; V = ventilator. See A-602.',
        'Solid walls are cut at +1200 mm above the selected floor. Dashed windows sit above the cut plane.',
        'Furniture is schematic. Grid bubbles A/B/C and 1/2/3 are coordination axes, not column locations.',
    ]:
        y=paragraph(x,y,note,102,2.6,3.8);y-=3
    if floor==0:extra='Ground FFL +0.450 m. Timber door daylight and bathroom exhaust remain open review items.'
    elif floor==1:extra='First FFL +3.600 m. F13 is open below; F14 remains open to sky. Neither is usable floor area.'
    else:extra='Roof slab datum +6.750 m. Guard height modelled at 1100 mm; sizing, drainage slopes and waterproofing require detailing.'
    y=paragraph(x,y-2,extra,102,2.6,3.8,RED)
    assert y>=47,('panel overflow',floor,y)

def picture(path,x,y,w,h):
    # High-quality JPEG encoding keeps the print PDF easy to transfer; plan linework remains vector.
    encoded=io.BytesIO()
    with Image.open(path) as source:source.convert('RGB').save(encoded,format='JPEG',quality=94,subsampling=0)
    encoded.seek(0)
    image=ImageReader(encoded);iw,ih=image.getSize();ratio=min(w/iw,h/ih)
    dw,dh=iw*ratio,ih*ratio
    c.drawImage(image,(x+(w-dw)/2)*MM,(y+(h-dh)/2)*MM,dw*MM,dh*MM,mask='auto')

# 1. Site and a concise sheet index.
start('A-001','Site arrangement and design brief','Plot dimensions and access follow the saved concept. A boundary survey is still required.',125)
sh=sheets['A-001'];elems=[e for e in sh['elements'] if not(e['type']=='text' and e['text']=='REAR YARD')]
draw(elems,sh['bounds'],125,(16,48,267,209));scale_bar(scale=125)
line(295,48,295,253)
y=heading(303,252,'PROJECT BRIEF',103)
for label,value in [('Plot','18288 x 16764 mm / 60 x 55 ft'),('Orientation','East road / north points right'),('Storeys','Ground + first + roof access'),('Plot area','306.58 m2 / 3300 ft2'),('Floor rise','3150 mm between occupied floors'),('Model walls','150 mm nominal thickness')]:
    text(303,y,label.upper(),2.5,'Helvetica-Bold',GREY);y-=5
    text(303,y,value,2.8);y-=9
y=heading(303,y-2,'PRINT SET CONTENTS',103)
for sid,title in [('A-101','Ground floor / 1:100'),('A-102','First floor / 1:100'),('A-104','Roof and stair access / 1:100'),('A-301','Measured model section / 1:100'),('P-101','Ground floor 3D cutaway'),('P-102','First floor 3D cutaway'),('P-103','Exterior and roof 3D views'),('A-601','Clear room sizes and areas'),('A-602','Door and window sizes'),('A-901','Civil engineer review brief')]:
    text(303,y,sid,2.6,'Helvetica-Bold',BLUE);text(321,y,title,2.55);y-=5.4
y=paragraph(303,y-5,'The 2438 mm front court and boundary-reaching side / rear portions are authored assumptions. Local setbacks, road width and property levels must be checked before this layout is adopted.',103,2.65,4,RED)
assert y>47
end()

# 2-4. The three full-size vector plans.
for floor,sid,title in [(0,'A-101','Ground floor - dimensioned architectural plan'),(1,'A-102','First floor - dimensioned architectural plan'),(2,'A-104','Roof terrace - stair access and guarded edges')]:
    start(sid,title,'Original room geometry, wall openings and stair core retained. Read sizes with the room schedule.',100)
    e,bounds=plan_elements(floor);draw(e,bounds,100,(15,48,275,211 if floor else 215));scale_bar();plan_panel(floor);end()

# 5. One actual mesh cut, kept distinct from a structural drawing.
start('A-301','Section A-A through the south stair flight','Section position is marked A on the plans. Model cut at local y = 4150 mm, along the rotated stair run.',100)
section,section_bounds=stair_flight_section();draw(section,section_bounds,100,(18,118,274,133));scale_bar(scale=100)
line(295,48,295,253)
y=heading(303,252,'LEVELS / STAIR',103)
for name,value in [('Natural ground','+/-0.000 m, assumed'),('Ground finished floor','+0.450 m'),('First finished floor','+3.600 m'),('Roof slab datum','+6.750 m'),('Rise between floors','3150 mm'),('Each storey flight pair','18 risers at 175 mm'),('Tread / flight width','250 mm / 1100 mm'),('Turning landing','1162 mm nominal')]:
    text(303,y,name,2.8,color=GREY);text(303,y-5,value,3,'Helvetica-Bold');y-=13
y=heading(303,y-1,'SECTION SCOPE',103)
y=paragraph(303,y,'The section intersects the saved wall, floor, stair, roof and plinth meshes. It documents the concept geometry. It does not provide RCC member sizes, reinforcement or foundations.',103,2.8,4.4)
y=paragraph(303,y-5,'Stair headroom, handrails, guards, slab openings and the double-height edge need coordinated architectural and structural review.',103,2.8,4.4,RED)
text(27,93,'How to use this sheet',3.8,'Helvetica-Bold',BLUE)
paragraph(27,84,'Use it to discuss the stair route from the ground floor to the first floor and roof. The two linked stair cores stay aligned. Floor finish build-ups and structural slab thicknesses must be resolved by the engineer before setting levels on site.',245,3.1,4.7)
end()

# 6-8. Real model views, not newly invented house images.
for floor,sid,title,filename in [(0,'P-101','Ground floor - furnished 3D cutaway','ground-3d.png'),(1,'P-102','First floor - furnished 3D cutaway','first-3d.png')]:
    start(sid,title,'Rendered from the same saved model as A-101 / A-102. Roof and upper walls removed for visibility.','3D REFERENCE / NTS')
    picture(VIEWS/filename,14,48,294,207);line(315,48,315,253)
    y=heading(323,252,'DESIGN TO DISCUSS',83)
    if floor==0:
        topics=[('Arrival and privacy','Entry hall and separate drawing room retain independent front access.'),('Family zone','Kitchen, puja, dining, living and the south staircase share the main circulation.'),('Master bedroom','Southwest master bedroom has a private attached bathroom.'),('Care suite','Garden-facing care room connects to living, veranda and caregiver bedroom.'),('Independent caregiver route','Caregiver bedroom and attached toilet sit along the rear strip, with their own garden exit.'),('Outdoor space','Veranda opens toward the north lawn and garden path.')]
    else:
        topics=[('Private rooms','Two bedrooms occupy the rear of the first floor.'),('Arrival and work','The upper lobby and studio open toward the east terrace.'),('Double-height living','The guarded opening looks down to the ground-floor family living area.'),('Terraces','Front / north shared terraces remain distinct from the private bedroom balconies.'),('Daylight gap','The outer 2700 x 2600 mm sky opening remains unbuilt above the veranda edge.'),('Roof access','The retained staircase continues to the roof landing and guarded terrace.')]
    for label,detail in topics:
        text(323,y,label,3.0,'Helvetica-Bold',BLUE);y-=6
        y=paragraph(323,y,detail,83,2.9,4.4);y-=7
    paragraph(323,y,'Use the 2D plans for dimensions. Furniture, materials, plants and car are presentation objects.',83,2.8,4.3,RED)
    end()

start('P-103','Exterior and accessible roof - 3D study','Neighbourhood context is hidden. House massing, balconies and roof access follow the saved model.','3D REFERENCE / NTS')
picture(VIEWS/'exterior-3d.png',15,94,191,158);picture(VIEWS/'roof-3d.png',214,94,191,158)
line(210,92,210,254)
text(20,84,'01 / Exterior massing',3.8,'Helvetica-Bold',BLUE)
paragraph(20,75,'G+1 house, open terraces, private balconies and roof stair headhouse. Facade finishes and canopy supports are design studies requiring construction details.',182,3.1,4.7)
text(220,84,'02 / Roof access and terrace',3.8,'Helvetica-Bold',BLUE)
paragraph(220,75,'The roof is accessed from the aligned south staircase. Terrace area is 106.049 m2 in the saved model. Guard geometry is visible; structural anchorage, falls, outlets and waterproofing remain to be designed.',182,3.1,4.7)
end()

# 9. Room schedule: exact principal dimensions, areas from real polygons, feet for the owner.
start('A-601','Room schedule - clear dimensions and actual areas','Primary dimensions are millimetres. Decimal feet are approximate owner references.','SCHEDULE / NTS')
for floor,x,width in [(0,15,191),(1,219,186)]:
    y=heading(x,252,['GROUND FLOOR','FIRST FLOOR'][floor],width)
    cols=[x,x+13,x+79,x+123,x+165]
    for xp,s in zip(cols,['REF','SPACE','CLEAR SIZE mm','APPROX. ft','AREA m2']):text(xp,y,s,2.45,'Helvetica-Bold',GREY)
    y-=7
    for idx,r in enumerate(r for r in rooms if r['floor']==floor):
        if idx%2==0:rect(x,y-4,width,9.4,PALE)
        text(cols[0],y,r['code'],2.8,'Helvetica-Bold',BLUE)
        # Name wraps only inside its own fixed-width cell.
        parts=wrap(r['short'].title(),63,2.7)
        for j,p in enumerate(parts):text(cols[1],y-j*3.5,p,2.7)
        dim=f'{r["dx"]:.0f} x {r["dy"]:.0f}'+('*' if r['irregular'] else '')
        text(cols[2],y,dim,2.65)
        text(cols[3],y,f'{r["dx"]/304.8:.1f} x {r["dy"]/304.8:.1f}',2.65)
        text(cols[4],y,f'{r["area_m2"]:.2f}'+(' v' if r['kind']=='void' else ''),2.65)
        y-=9.4
    if floor==1:
        y=heading(x,y-8,'ROOF LEVEL',width)
        for r in [r for r in rooms if r['floor']==2]:
            text(x,y,r['code']+'  '+r['short'].title(),2.9,'Helvetica-Bold',BLUE)
            text(x+165,y,f'{r["area_m2"]:.3f}',2.9);y-=7
        y=paragraph(x,y-2,'Roof landing is the clear arrival patch beside the stair well. Roof terrace is open access space, not another occupied storey.',width,2.8,4.2)
    assert y>=58
line(212,48,212,252)
paragraph(15,56,'* Irregular / L-shaped space: clear size is its largest inscribed rectangle; area is the actual clear polygon. v = void, excluded from usable floor area. Stair room areas include the circulation envelope. Dimensions are model values and must be checked against site measurements.',389,2.65,4)
end()

# 10. Opening type schedule with counts and exact nominal aperture sizes.
tags,types=opening_types(b)
types_by_tag={t['tag']:t for t in types}
instances={t['tag']:[] for t in types}
for o in full['openings']:instances[tags[o['id']]].append(o)
def kind_name(tag):
    os=instances[tag];t=types_by_tag[tag]
    if any(o.get('timberScreen') for o in os):return 'Timber / mesh assembly'
    if any(o.get('fixed') for o in os):return 'Fixed glazing'
    if any(o.get('stackingSliding') for o in os):return 'Wall-stacking glazing'
    if t['kind']=='glazed':return 'Sliding glazing'
    if t['kind']=='cased':return 'Cased / open passage'
    if tag.startswith('V'):return 'High-level vent / glazing'
    if t['kind']=='window':return 'Window glazing'
    if t['kind']=='entry':return 'Entry door'
    return 'Hinged door'
start('A-602','Opening schedule - doors, windows and vents','Type tags correspond to A-101, A-102 and A-104. Width / height / sill are in millimetres.','SCHEDULE / NTS')
groups=[[t for t in types if not t['tag'].startswith(('W','V'))],[t for t in types if t['tag'].startswith(('W','V'))]]
for group,x,width,title in [(groups[0],15,191,'DOORS / PASSAGES'),(groups[1],219,186,'WINDOWS / VENTS')]:
    y=heading(x,252,title,width)
    cols=[x,x+16,x+35,x+54,x+71,x+84,x+110]
    for xp,s in zip(cols,['TAG','WIDTH','HEIGHT','SILL','QTY','LEVEL','TYPE']):text(xp,y,s,2.45,'Helvetica-Bold',GREY)
    y-=7
    for idx,t in enumerate(group):
        if idx%2==0:rect(x,y-3.8,width,6.2,PALE)
        levels='/'.join(('G','F','R')[f] for f in sorted({o['floor'] for o in instances[t['tag']]}))
        values=[t['tag'],t['width'],t['height'],t['sill'],t['count'],levels,kind_name(t['tag'])]
        for j,(xp,val) in enumerate(zip(cols,values)):text(xp,y,val,2.55,'Helvetica-Bold' if j==0 else 'Helvetica',BLUE if j==0 else INK)
        y-=6.2
    assert y>=70
line(212,48,212,252)
text(15,68,'SCHEDULE NOTES',3.3,'Helvetica-Bold',BLUE)
paragraph(15,59,'These are nominal model opening sizes, not frame manufacturing sizes or guaranteed clear passage widths. Sill levels are above the respective finished floor. G = ground; F = first; R = roof landing. D/SD tags group by geometry; specialist timber/mesh and glass assemblies need their own detailing.',389,2.9,4.4)
paragraph(15,46,'Confirm door handing, tracks, thresholds, ventilation performance and safety glazing with the engineer / supplier. No frame deductions, fabrication tolerances or glazing thickness specification is supplied.',389,2.8,4.2)
end()

# 11. Concise actionable professional review brief; no fabricated engineering sign-off.
start('A-901','Civil engineer handover - design checks and decisions','An architectural concept package for review, survey and engineering development.','REVIEW BRIEF / NTS')
items=[
 ('01 / Site and local approvals','Survey all plot corners, road width, north direction and levels. Confirm the 60 x 55 ft plot and actual boundary position. The model assumes a 2438 mm front court with boundary-reaching side / rear wings; establish legal setbacks and permissible development before adoption.'),
 ('02 / Structure and soil','Arrange the site and soil assessment needed for foundation design. Develop the structural system, columns, beams, slabs, load paths, balcony / canopy supports and reinforcement. The coordination grid on these plans is not a column or foundation layout.'),
 ('03 / Double-height living and stairs','Resolve the F13 slab opening, guard anchorage and its interface with the living room below. Check the aligned staircase, 18 x 175 mm risers, 250 mm treads, 1100 mm flights, 1162 mm landing, headroom, handrails and slab-edge details.'),
 ('04 / Daylight and exhaust','The saved review flags the living hall timber door: daylight is blocked when its timber leaves are closed. Review permanent glazing. Mechanical exhaust is selected for G10, G13 and F07; design duct routes, outlet positions and capacities.'),
 ('05 / Water, drainage and terraces','Coordinate bathroom and kitchen water supply, soil / waste pipes, traps, drain routes and inspection access. Resolve roof and balcony falls, outlets, gutters, downpipes, waterproofing and level changes at thresholds.'),
 ('06 / Care room and access','Confirm the care room brief, equipment clearances and circulation with the owner. The model is a residential care concept. Review entry steps, practical mobility access and door clear widths for the intended users.'),
 ('07 / Wall and opening details','Model walls are 150 mm nominal. Confirm the wall system, lintels, damp-proofing, materials, facade anchors, frames, glass, timber / mesh assemblies, sliding tracks and tolerances. Furniture shown establishes intent and is schematic.'),
 ('08 / Freeze a surveyed revision','Record agreed changes, issue coordinated architectural, structural and service drawings, and obtain the required professional and authority approvals. Use an approved revision for site setting-out and construction.'),
]
for group,x in [(items[:4],16),(items[4:],219)]:
    y=251
    for title,body in group:
        text(x,y,title,3.4,'Helvetica-Bold',BLUE);y-=7
        y=paragraph(x,y,body,185,3.1,4.65);y-=11
    assert y>=79,(x,y)
line(211,78,211,253)
rect(15,42,390,30,PALE,LINE)
text(20,64,'ENGINEER / OWNER REVIEW RECORD',3.1,'Helvetica-Bold',BLUE)
text(20,55,'Engineer / firm: _________________________     Owner: _________________________     Date: ______________',3)
text(20,47,'Surveyed plot confirmed: ____________     Revision requested: ____________     Approval / drawing reference: __________________',2.85)
end()

c.save()
assert len(page_records)==11
# Export the same floor geometry, room references and section markers to an editable millimetre DXF.
import floorforge.drawings as drawing_module
original_plan_elements=drawing_module.plan_elements
original_layers=drawing_module.LAYERS
try:
    drawing_module.plan_elements=lambda building,scene,floor=0:plan_elements(floor)
    drawing_module.LAYERS=original_layers+[('HANDOVER-ROOM',4,18),('HANDOVER-VOID',8,13)]
    cad_checks=drawing_module.dxf_export(b,scene,OUT/'my-desired-home-floorplans.dxf')
finally:
    drawing_module.plan_elements=original_plan_elements
    drawing_module.LAYERS=original_layers
for name in ('ground-3d','first-3d','roof-3d','exterior-3d'):
    shutil.copy2(VIEWS/(name+'.png'),OUT/('my-desired-home-'+name+'.png'))
manifest={
 'title':'My Desired Home / owner-to-engineer handover',
 'revision':'A / 2026-10-02','planHash':b['planHash'],
 'source':'examples/gallery/my-desired-home',
 'source_geometry_changed':False,'paper_mm':[420,297],
 'construction_ready':False,'primary_dimensions':'mm',
 'room_refs':[{k:r[k] for k in ('id','code','short','floor','dx','dy','irregular','area_m2')} for r in rooms],
 'sheet_index':page_records,
 'opening_types':len(types),'opening_instances':len(full['openings']),
 'cad_export':cad_checks,'section_plane':{'axis':'y','coordinate_mm':STAIR_CUT_Y},
 'review_warnings':report['review']['warnings'],
}
(ROOT/'tmp/pdfs/handover-checks.json').write_text(json.dumps(manifest,indent=2))
readme='''MY DESIRED HOME - OWNER TO CIVIL ENGINEER HANDOVER

PRELIMINARY - ENGINEER TO REVIEW - NOT FOR CONSTRUCTION

This set follows the saved 60 x 55 ft, east-facing G+1 design shown in the owner's screenshots.
No rooms, walls, openings, stair cores or structural dimensions have been redesigned.

Print the PDF on A3 (420 x 297 mm), landscape, actual size / 100 percent.
Do not use Fit to page if measuring the scale bar. Plans A-101, A-102 and A-104 are 1:100;
site A-001 is 1:125. The 3D views are not to scale. Millimetre dimensions govern.
The PDF has vector linework; the separate plan PNGs are high-resolution print / sharing copies.

The DXF contains the unchanged floor geometry (millimetres), with the PDF room reference codes
and matching A-A section markers. It includes floor plans, not the section body or schedules.
Room references and the drawing index are documented in handover-manifest.json.
The GLB and editable FloorForge project are included for digital review. preview.html is the
original standalone interactive 3D viewer; open it locally in a WebGL2-capable browser.

Professional follow-up: site survey, local setback / approval checks, geotechnical and structural
design, service design, stair / guard details, daylight and bathroom exhaust, drainage and access.
See A-901 for the project-specific review brief. No engineering certification or statutory approval
is claimed. The saved model coordinates and ground / road datums are design assumptions.

Model reference: '''+b['planHash']+'\n'
(OUT/'README-handover.txt').write_text(readme)
print(json.dumps({'pdf':str(PDF),'pages':len(page_records),'planHash':b['planHash'],'rooms':len(rooms),'opening_types':len(types)},indent=2))
