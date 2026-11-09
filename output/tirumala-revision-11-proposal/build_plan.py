"""Review-only two-floor proposal. Does not modify the five live samples."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

OUT=Path(__file__).parent
def poly(g): return [[round(x,3),round(y,3)] for x,y in g.exterior.coords[:-1]]
def rect(x,y,w,h): return poly(box(x,y,x+w,y+h))
def space(id,name,p,kind,at,short,detail):
    g=Polygon(p)
    return dict(id=id,name=name,p=p,kind=kind,at=at,short=short,area=round(g.area,2),detail=detail)
def furniture(kind,p,label='',floor=0):return dict(kind=kind,p=p,label=label,floor=floor)
def door(id,a,b,clear,kind='wood',swing=1,hinge=0):
    return dict(id=id,a=a,b=b,clear=clear,kind=kind,swing=swing,hinge=hinge)
def line(a,b,kind='wall'):return dict(a=a,b=b,kind=kind)
def outline(x,y,w,h):
    p=rect(x,y,w,h);return [line(p[i],p[(i+1)%4]) for i in range(4)]

# Feet. South -> north is x; east -> west is y. All room polygons are clear floor zones.
g=[]
g.append(space('K','Kitchen',[[4.5,5],[8.5,5],[8.5,9.5],[17,9.5],[17,20.5],[4.5,20.5]],'open',[10.5,14.0],'Kitchen',
 '155.5 sq ft. The east return gains 1 ft of depth; the main working bay remains 12.5 × 11 ft. The kitchen front wall now aligns with puja, EN and the front edge of PO. The entry route stays clear along the north side, and the low platform faces west toward dining.'))
g.append(space('P','Screened puja',rect(9,5,3.5,4),'room',[10.75,7.3],'Puja',
 '3.5 × 4 ft, enlarged by 1 ft toward the front court. Altar stays on the east wall, aligned with the kitchen and EN front walls. Short side screens remain; the west side stays open.'))
g.append(space('EN','Open indoor entry',rect(13,5,4,4.5),'open',[15,7.5],'Entry',
 '4 × 4.5 ft indoor arrival, flush with the kitchen and puja frontage. Enter from PO through a 3.5 ft net-clear single timber door. Hinge at the front corner; the open leaf rests along the EN front wall so the turn into living stays free. No direct front-court doorway.'))
g.append(space('L','Living + west dining',[[4.5,20.5],[23,20.5],[23,37.5],[15,37.5],[15,33.5],[13,33.5],[13,29],[4.5,29]],'open',[18,27.3],'Living',
 'One open family area, with dining west of the kitchen. Dining uses the inside corner of the L stair. A solid drawing-room wall carries the living-room TV; the care-room side remains glazed.'))
g.append(space('DR','Drawing room',rect(17.5,9,11,11),'room',[23,14.3],'Drawing',
 'A true 11 × 11 ft rectangle. Separate 4 ft clear timber entrance from the open porch. Solid partition to the living/kitchen side; no internal glass doorway.'))
g.append(space('C','Rectangular home care',rect(23.5,20.5,12.5,16.5),'care',[29.75,23.0],'Home care',
 '12.5 × 16.5 ft = 206.25 sq ft, without an L-shaped tail. Head south, feet north. Large north garden glazing and east glazing toward parking. The care wall is 3.75 ft from the north plot boundary and over 12 ft from the west boundary.'))
g.append(space('M','Ground master',rect(.5,33.5,14,13.5),'room',[7.5,36.0],'Master',
 '14 × 13.5 ft = 189 sq ft, with normal-size furniture, a 3.5 ft clear entry and a separate attached bathroom. Rear light strip retained behind this bedroom.'))
g.append(space('B','Master bath',rect(15,42,5.5,7),'room',[17.75,45.5],'Bath',
 '5.5 × 7 ft attached bath; 3 ft clear timber pocket door from the master. Fixture arrangement is indicative.'))
g.append(space('CG','Caregiver',rect(21,43,7.5,6),'room',[24.75,47.3],'Caregiver',
 '45 sq ft; 7.5 × 6 ft. Single 3 × 6.5 ft bed and minimal storage, directly off the veranda along the west edge. Compact sleeping accommodation; local habitable-room requirements remain to be checked.'))
g.append(space('WC','Caregiver WC',rect(29,43,5,6),'room',[31.5,46.5],'WC',
 '5 × 6 ft, attached to the caregiver room. Timber pocket door, not a glass panel.'))
g.append(space('V','Rear veranda',[[15,38],[23.5,38],[23.5,37.5],[36,37.5],[36,42.5],[21,42.5],[21,41.5],[15,41.5]],'outdoor',[28.5,40.1],'Veranda',
 '5 ft main depth between care and caregiver, with a 3.5 ft return behind the family hall. Independent timber doors from care and family hall; caregiver access does not require crossing the care room.'))
g.append(space('S','L stair + lower landing',[[.5,17.5],[4,17.5],[4,29.5],[12.5,29.5],[12.5,33],[.5,33]],'stair',[6.8,31.2],'L stair',
 '3.5 ft wide flights: climb west, turn north. 84 sq ft occupied including the lower approach landing; 12 × 15.5 ft bounding box includes the dining corner. 20 proposed rises of 182.9 mm, 287.9 mm treads. The same flights stack to the roof; headroom and structure require design coordination.'))
g.append(space('N','North garden path',rect(36.5,20,3,29.5),'garden',[38,31],'Garden path',
 '3 ft unobstructed walking strip. Wall-trained greenery, with pots in the wider northwest corner rather than in the route.'))
g.append(space('NW','Northwest garden',rect(34.5,43,2,6.5),'garden',[35.5,46.0],'NW',
 'Together with the north strip, a 5 × 6.5 ft northwest garden pocket stays unbuilt. Caregiver and WC occupy the west strip further south.'))
g.append(space('W','Rear light strip',rect(.5,47.5,14,2),'garden',[7.5,48.5],'Light strip',
 '2 ft rear light/maintenance strip behind the ground master. Not labelled as an accessible route.'))
g.append(space('SL','South daylight lane',rect(.5,4.5,3.5,12.5),'outdoor',[2.25,11.5],'3.5 ft lane',
 '3.5 ft clear lane ends at the glazed stair landing. The final landing is inside the house so the west-climbing flight can be entered from the open kitchen/hall.'))
g.append(space('PO','Open-sky porch',rect(17.5,4.5,11,4),'outdoor',[24.25,6.5],'PO · 4 ft deep',
 '11 × 4 ft. PO starts on the same straight line as the kitchen, puja and EN outside wall faces, immediately behind the 4 ft front court. Court plus PO gives 8 ft of outdoor depth before drawing. Separate timber doors lead to EN and drawing. Open to the sky.'))
g.append(space('FC','Front court',rect(.5,.5,28,4),'outdoor',[7.5,2.5],'Front court · 4 ft',
 'Uniform 4 ft allocated depth across the pedestrian frontage, measured from the inside of the front boundary to the aligned building/PO line. The two 150 mm entry steps occupy the first 2 ft locally, leaving 2 ft of raised court before the continuous 4 ft-deep PO. No extra step between court and PO. Parking stays separate at the lower level.'))
g.append(space('CAR','Car bay',rect(29,.5,10.5,19),'outdoor',[34.25,5],'Car bay',
 '10.5 × 19 ft. A 6.5 × 15.5 ft reference car leaves 2 ft side margins and 1.75 ft at each end. Final gate and swept approach depend on the actual vehicle.'))

u=[]
u.append(space('U1','Front master suite',[[11.5,6],[17,6],[17,9],[28.5,9],[28.5,20],[11.5,20]],'room',[20,10.5],'Master 1',
 '203.5 sq ft sleeping/seating space: 17 × 11 ft main rectangle plus the east bay. Over drawing, puja and part of kitchen/entry; separate bath/dress over the remaining kitchen. Timber doors to the family lounge and terrace.'))
u.append(space('UB1','Bath + dressing',rect(4.5,6,6.5,10.5),'room',[7.75,13],'Bath / dress',
 '6.5 × 10.5 ft, combining bathroom and dressing/storage. 3 ft clear timber pocket door from the front master.'))
u.append(space('U2','Rear master suite',rect(.5,34,18,13),'room',[9.5,37],'Master 2',
 '18 × 13 ft = 234 sq ft, mostly over the southwest master and rear service area. A true rectangular sleeping room with a king bed, wardrobe and seating; separate attached bathroom.'))
u.append(space('UB2','Rear ensuite',rect(19,40,6,7),'room',[22,43.5],'Bath',
 '6 × 7 ft attached bathroom with a 3 ft clear timber pocket door. Wet services can align broadly with the ground bath/service zone.'))
u.append(space('O','Small office',rect(25.5,42.5,8.5,6.5),'room',[29.75,47.5],'Office',
 '8.5 × 6.5 ft = 55.25 sq ft, over the caregiver/service strip. Independent 3.5 ft clear timber entry from the common hall; the northwest garden corner remains outside the room.'))
hall=unary_union([box(.5,17,11,21),box(4.5,20.5,23,29),box(13,29,23,33.5),box(19,33.5,23,39.5),box(23,36,34,39.5),box(25.5,39.5,34,42)])
hall=hall.difference(box(16.5,22,23.5,29))
u.append(space('UL','Upper family lounge + circulation',poly(hall),'open',[10.0,24.1],'Family lounge',
 'A furnished 12 × 8.5 ft main lounge bay plus the stair approach and room connections. Rear passage is 4 ft clear, widening to a 6 ft terrace/office lobby. These circulation areas are included in the displayed total, not counted as one rectangular lounge.'))
u.append(space('UV','Double-height living opening',rect(17,22.5,6,6),'void',[20,25.5],'Void',
 '6 × 6 ft = 36 sq ft open to the ground living room, reduced from about 55 sq ft. Retain the approximately 23 ft clear height and a rooflight. Guard the upper edges; no floor or bedroom crosses this opening.'))
u.append(space('UT','Garden terrace',[[29,15],[39,15],[39,20],[36,20],[36,35.5],[23.5,35.5],[23.5,20.5],[29,20.5]],'outdoor',[30,29],'Open terrace',
 '241 sq ft, mostly over the rectangular care room, with a 10 × 5 ft return over the rear portion of parking. Timber doors from both the common lounge and front master. Edge planting and a small pergola seating zone leave the middle open. Parking extension needs structural design, drainage and headroom confirmation.'))
u.append(space('US','L stair: first floor to roof',[[.5,21],[4,21],[4,29.5],[12.5,29.5],[12.5,33],[.5,33]],'stair',[6.8,31.2],'To roof',
 'Repeat the west-then-north L flight above the ground stair. The first-floor approach wraps around the east end to reach the next flight. Proposed roof arrival: 5 × 4 ft landing, enclosed stair head and a 3.5 ft clear timber exit. Roof terrace is one storey above the care-room terrace.'))

gw=[]
gw+=outline(17.25,8.75,11.5,11.5)
gw+=outline(23.25,20.25,13,17)
gw+=outline(.25,33.25,14.5,14)
gw+=outline(14.75,41.75,6,7.5)
gw+=outline(20.75,42.75,8,6.5)
gw+=outline(28.75,42.75,5.5,6.5)
gw += [line([4.25,4.75],[17.25,4.75]),line([4.25,4.75],[4.25,17.25]),
       line([17.25,4.75],[17.25,8.75]),
       line([8.75,4.75],[8.75,9.25]),line([12.75,4.75],[12.75,9.25]),
       line([.25,17.25],[4.25,17.25]),line([.25,17.25],[.25,33.25]),
       line([14.75,37.75],[23.25,37.75]),line([14.75,37.75],[14.75,41.75])]
uw=[]
up=[[11.25,5.75],[17.25,5.75],[17.25,8.75],[28.75,8.75],[28.75,20.25],[11.25,20.25]]
uw += [line(up[i],up[(i+1)%len(up)]) for i in range(len(up))]
uw+=outline(4.25,5.75,7,11)
uw+=outline(.25,33.75,18.5,13.5)
uw+=outline(18.75,39.75,6.5,7.5)
uw+=outline(25.25,42.25,9,7)
uw += [line([23.25,20.25],[23.25,35.75]),line([23.25,35.75],[34.25,35.75]),line([34.25,35.75],[34.25,42.25]),
       line([.25,16.75],[4.25,16.75]),line([.25,16.75],[.25,33.75]),
       line([16.75,22.25],[23.25,22.25],'guard'),line([16.75,22.25],[16.75,28.75],'guard'),line([16.75,28.75],[23.25,28.75],'guard')]
gd=[door('PO to EN living entrance',[17.25,4.875],[17.25,8.625],3.5,'wood',1),
    door('Drawing entrance',[19.875,8.75],[24.125,8.75],4,'wood',1),
    door('Master entry',[14.75,33.625],[14.75,37.375],3.5,'wood',1),
    door('Master bath',[14.75,42.625],[14.75,45.875],3,'pocket'),
    door('Family veranda',[17.875,37.75],[22.125,37.75],4,'wood',-1),
    door('Care veranda',[26.375,37.25],[30.625,37.25],4,'wood',-1),
    door('Caregiver',[23.125,42.75],[26.375,42.75],3,'wood',-1),
    door('Caregiver WC',[28.75,43],[28.75,46],2.75,'pocket'),
    door('Care connection',[23.25,22],[23.25,32],6.4,'glass')]
gd[0]['leaves']=1
ud=[door('Front master',[12.125,20.25],[15.875,20.25],3.5,'wood',-1),
    door('Front bath',[11.25,12.875],[11.25,16.125],3,'pocket'),
    door('Master terrace',[28.75,15.125],[28.75,19.375],4,'wood',1),
    door('Common terrace',[23.25,29.125],[23.25,33.375],4,'wood',1),
    door('Rear master',[13.125,33.75],[16.875,33.75],3.5,'wood',1),
    door('Rear bath',[18.75,40.5],[18.75,43.75],3,'pocket'),
    door('Office',[26,42.25],[29.75,42.25],3.5,'pocket')]
windows={
'ground':[line([4.75,4.75],[8,4.75],'glass'),line([.75,17.25],[3.75,17.25],'glass'),
line([28.75,10.5],[28.75,17.5],'glass'),line([29.5,20.25],[35.25,20.25],'glass'),
line([36.25,22],[36.25,35.5],'glass'),line([.25,36],[.25,43],'glass'),line([2,47.25],[10,47.25],'glass'),
line([21.75,49.25],[27.5,49.25],'glass')],
'first':[line([18.25,8.75],[26.75,8.75],'glass'),line([12.25,5.75],[16.25,5.75],'glass'),
line([23.25,22.25],[23.25,28.75],'glass'),
line([28.75,10],[28.75,14],'glass'),line([6,5.75],[9,5.75],'glass'),
line([.25,37],[.25,43],'glass'),line([2,47.25],[12,47.25],'glass'),line([26.5,49.25],[32.5,49.25],'glass')]}
f=[]
for p in [rect(4.5,5,4,2),rect(4.5,12.5,2,4),rect(8,19,5.5,1.5)]:f.append(furniture('counter',p))
f += [furniture('fridge',rect(4.5,9.5,2.5,2.5)),furniture('altar',rect(9.5,5.1,2.5,.8)),
      furniture('dining',rect(7,23.5,5,3)),furniture('sofa',rect(17,28,6,2.75)),furniture('coffee',rect(18,25,3.5,1.75)),
      furniture('tv',rect(18.5,20.5,4.5,.35),'TV'),furniture('sofa',rect(25.5,11,3,7.5)),furniture('coffee',rect(21,12.5,2,4)),furniture('tv',rect(17.5,12.5,.35,4.5),'TV'),
      furniture('care-bed',rect(26,27,7,3.5)),furniture('seat',rect(32,32.5,2,2)),furniture('equipment',rect(24,28,1.5,1.5)),
      furniture('bed',rect(3,39.5,6,6.5)),furniture('wardrobe',rect(12.5,38.5,2,3.5)),furniture('tv',rect(4.5,33.5,4,.35),'TV'),
      furniture('bed',rect(21.5,45,6.5,3)),furniture('desk',rect(21.5,43.1,2,1.5)),
      furniture('car',rect(31,2.25,6.5,15.5)),furniture('steps',rect(20,0.5,4,2))]
f += [furniture('bed',rect(12.5,10,7,6),'',1),furniture('tv',rect(27.9,10.5,.35,4.5),'TV',1),
      furniture('seat',rect(23,11,2.5,2.5),'',1),furniture('wardrobe',rect(4.5,14,2,2.5),'',1),
      furniture('sofa',rect(6.5,26,7,3),'',1),furniture('coffee',rect(8,23.5,4,1.25),'',1),furniture('tv',rect(12,20.5,4,.35),'TV',1),
      furniture('bed',rect(4,39,6,7),'',1),furniture('wardrobe',rect(16.5,37.5,2,4),'',1),furniture('tv',rect(5,34,4.5,.35),'TV',1),
      furniture('desk',rect(28,47,5,2),'',1),furniture('seat',rect(29.5,45,2,2),'',1),
      furniture('outdoor-sofa',rect(30,32,5,2.5),'',1),furniture('outdoor-table',rect(30.5,29.5,3,1.5),'',1)]
# Indicative bathroom fixtures, kept out of the door zones.
for floor,items in [(0,[(15.3,46,3,2.7,'shower'),(18.5,47,1.5,2,'wc'),(18.8,42.5,1.4,2,'basin'),(31.8,46.5,1.5,2,'wc'),(31,43.2,2,1.4,'basin')]),
                    (1,[(4.5,6,3.5,3.5,'shower'),(9.2,6.5,1.5,2.5,'wc'),(4.5,10,1.5,3,'basin'),(19.3,44,3,3,'shower'),(23.2,44,1.5,2.5,'wc'),(22.5,40.3,2,1.4,'basin')])]:
    for x,y,w,h,k in items:f.append(furniture(k,rect(x,y,w,h),'',floor))
routes={
'ground':[[[22,2.8],[22,6.75],[19,6.75],[15,6.75],[15,18.5],[15,23],[19,23],[24.5,23],[27,24.5]],
[[15,23],[14.75,30],[16.5,33.25],[16.5,35.5],[20,35.5],[20,40],[24.75,40],[24.75,43.5]],
[[7,18.7],[2.25,18.7],[2.25,29.5],[2.25,31.25],[14.5,31.25]]],
'first':[[[14.5,31.25],[14.5,30],[15.5,30],[20.5,30.5],[25,30.5],[28,29]],
[[14.5,30],[15.5,31.5],[20.5,31.5],[20.5,37.5],[27,37.5],[27.875,40.5],[27.875,44.5]],
[[14.5,30],[15,30],[15,22],[7,22],[7,19.5],[2.25,19.5],[2.25,29.5],[2.25,31.25],[14.5,31.25]]]}
plan=dict(revision=11,update='Aligned frontage with uniform 4 ft front court',status='2D proposal only',plot=[40,50],units='ft',wall=.5,
    floors={'ground':g,'first':u},walls={'ground':gw,'first':uw},doors={'ground':gd,'first':ud},windows=windows,furniture=f,routes=routes,
    stair=dict(flight=3.5,treads=9,run=8.5,firstStart=[2.25,21],turn=[2.25,31.25],end=[12.5,31.25],riseMm=182.9,rises=20,floorHeightMm=3658),
    roofAccess=dict(landing=rect(12.5,29,5,4),exitClearFt=3.5,exitMaterial='timber',status='proposed; coordinate headroom, roof edge guards and drainage before 3D'),
    facade=dict(walls='warm white, matching desired-home palette',windows='large aligned glazing; restrained dark frames without heavy projecting boxes',terrace='open care-roof terrace, edge planting and a small pergola over seating',composition='two balanced bedroom volumes, consistent sill/head lines, continuous parapet and recessed roof stair head'),
    levels=dict(roadAndParkingMm=0,groundCourtAndInteriorsMm=300,firstFloorMm=3958,roofMm=7616),
    notes=['Review proposal only; live Revision 10 samples and 3D are unchanged.',
           'Kitchen, puja and EN outside front wall faces align at y=4.5 ft with the front edge of PO. Front court is a uniform 4 ft deep; no entry projection.',
           'Entry correction: front court → PO → EN → open living hall. PO also has the separate drawing-room door. The direct court-to-EN opening is removed.',
           'Room areas are clear polygon areas; walls, terraces and voids are separate.',
           'The upper lounge total includes circulation. Main seating bay is 12 × 8.5 ft.',
           'Terrace over parking is a proposed structural extension, not an approved cantilever.',
           'Local setbacks, structure, drains and roof-stair headroom remain to be coordinated.'])

checks=[]
for floor,rs in plan['floors'].items():
    for r in rs:
        p=Polygon(r['p']);assert p.is_valid and box(0,0,40,50).covers(p),r['id']
    for i,r in enumerate(rs):
        for s in rs[i+1:]:
            overlap=Polygon(r['p']).intersection(Polygon(s['p'])).area
            assert overlap<.001,(floor,r['id'],s['id'],overlap)
    checks.append(f'{floor}: all clear zones valid, within plot and mutually non-overlapping')
care=next(r for r in g if r['id']=='C');assert len(care['p'])==4 and care['area']==206.25
assert not Polygon(care['p']).intersects(box(34.5,43,39.5,49.5))
checks.append('Care is rectangular, outside the northwest pocket and separate from north/west boundaries')
porch=Polygon(next(r['p'] for r in g if r['id']=='PO'))
for r in u:assert porch.intersection(Polygon(r['p'])).area<.001,('porch roof conflict',r['id'])
checks.append('Open-sky drawing porch has no first-floor room or terrace above it')
for floor in ['ground','first']:
    for d in plan['doors'][floor]:
        length=LineString([d['a'],d['b']]).length
        if d['kind']!='glass':assert length-d['clear']>=.249, d['id']
checks.append('Timber door openings include 3 inch total frame allowance beyond labelled clear widths')
entrance=next(d for d in gd if d['id']=='PO to EN living entrance')
assert entrance['a'][0]==entrance['b'][0]==17.25 and entrance['clear']==3.5
assert not any(d['a'][1]==d['b'][1] and d['a'][0]<17.25 and d['a'][1]<6 for d in gd)
checks.append('Living entry comes from PO through the shared side wall; no direct front-court-to-EN doorway remains')
by_id={r['id']:r for r in g}
assert Polygon(by_id['FC']['p']).equals(box(.5,.5,28.5,4.5))
for rid in ['K','P','EN']:
    assert min(y for x,y in by_id[rid]['p'])-.5==4.5,('front alignment',rid)
assert min(y for x,y in by_id['PO']['p'])==4.5
assert Polygon(by_id['PO']['p']).bounds[3]-4.5==4
checks.append('Uniform 4 ft front court; kitchen, puja, EN and PO share one outside alignment; court plus PO depth is 8 ft')
for n,floor in enumerate(['ground','first']):
    floor_poly=unary_union([Polygon(r['p']) for r in plan['floors'][floor] if r['kind']!='void'])
    wall_lines=unary_union([LineString([w['a'],w['b']]) for w in plan['walls'][floor]])
    for item in f:
        if item['floor']==n:assert Polygon(item['p']).difference(floor_poly).area<.01,('furniture outside floor',floor,item['kind'])
    for d in plan['doors'][floor]:
        assert LineString([d['a'],d['b']]).difference(wall_lines.buffer(.01)).length<.01,('door not on wall',d['id'])
        if d['kind']!='wood':continue
        dx=d['b'][0]-d['a'][0];dy=d['b'][1]-d['a'][1];length=math.hypot(dx,dy);tx,ty=dx/length,dy/length
        leaves=d.get('leaves',2 if d['clear']>=4 else 1);leaf=(length-.25)/leaves
        for k in range(leaves):
            sign=1 if k==0 else -1;base=d['a'] if k==0 else d['b'];hinge=[base[0]+sign*tx*.125,base[1]+sign*ty*.125]
            arc=[(hinge[0]+(tx*sign*math.cos(a)-ty*d['swing']*math.sin(a))*leaf,hinge[1]+(ty*sign*math.cos(a)+tx*d['swing']*math.sin(a))*leaf) for a in [i/48*math.pi/2 for i in range(49)]]
            sweep=Polygon([hinge]+arc+[hinge])
            for item in f:
                if item['floor']==n:assert sweep.intersection(Polygon(item['p'])).area<.015,('door sweep meets furniture',d['id'],item['kind'])
checks.append('Furniture footprints stay on clear floor; all openings align to walls; timber door sweeps avoid drawn furniture')
# Freeze the authoritative proposal data for later 3D implementation only after review.
(OUT/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps({'status':'PASS','checks':checks,'limits':plan['notes']},indent=2)+'\n')
print(json.dumps({'areas':{floor:{r['id']:r['area'] for r in rs} for floor,rs in plan['floors'].items()},'checks':checks},indent=2))
