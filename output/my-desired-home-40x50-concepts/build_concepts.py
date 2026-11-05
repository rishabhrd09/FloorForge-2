"""Independent review drawings; never writes either source sample or the gallery."""
from pathlib import Path
import json, math, hashlib
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
FT = 304.8
LONG, SHORT = 6788 / FT, 4150 / FT

def points(poly):
    return [[round(x, 6), round(y, 6)] for x, y in list(poly.exterior.coords)[:-1]]

def room(id, name, coords, kind='room', note='', label=None):
    geom = box(*coords) if len(coords) == 4 and isinstance(coords[0], (int, float)) else Polygon(coords)
    x0,y0,x1,y1 = geom.bounds
    pt = geom.representative_point()
    return dict(id=id,name=name,p=points(geom),kind=kind,note=note,
                area=round(geom.area,3),rectangular=abs(geom.area-(x1-x0)*(y1-y0))<.00001,size=[round(x1-x0,6),round(y1-y0,6)],
                at=label or [pt.x,pt.y])

def door(id, a, b, connects, kind='wood'):
    return dict(id=id,a=a,b=b,connects=connects,kind=kind,
                width=round(math.dist(a,b),4))

def furnishing(kind, coords, label=''):
    return dict(kind=kind,p=points(box(*coords)),label=label)

def finish_floor(rooms, doors, furniture):
    indoor=[Polygon(r['p'],r.get('holes',[])) for r in rooms if r['kind'] not in ('outdoor','garden','void','parking')]
    all_clear=unary_union([Polygon(r['p'],r.get('holes',[])) for r in rooms])
    wall_geom=unary_union([p.buffer(.5,join_style=2) for p in indoor]).difference(all_clear)
    walls=[]
    for p in ([wall_geom] if wall_geom.geom_type=='Polygon' else wall_geom.geoms):
        if p.geom_type=='Polygon':
            walls.append(dict(outer=points(p),holes=[[[round(x,6),round(y,6)] for x,y in list(r.coords)[:-1]] for r in p.interiors]))
    return dict(rooms=rooms,doors=doors,furniture=furniture,walls=walls)

def make_option(key, name, width, rotated=False):
    # North is up. x grows eastward from West boundary; y grows southward from North boundary.
    care_x = 26 if rotated else 47.5-width
    care_y = 4 if rotated else .5
    care_w, care_d = (LONG,SHORT) if rotated else (width,LONG)
    care_end = care_y+care_d
    v_left = 20.5 if rotated else care_x-6
    v_right = care_x-.5
    dr_right=v_left-.5
    dr_top=4 if rotated else .5
    dr_bottom=care_end if rotated else 14
    hall_top=dr_bottom+.5
    hall_right=34 if rotated else care_x-.5
    porch_left=34.5 if rotated else care_x
    porch_top=hall_top if rotated else care_end+.5
    g=[
      room('CG','Caregiver',[.5,.5,9,10.75],note='8.5 × 10.25 ft clear. Moved to the west of the drawing room. Independent hall/service-spine entry; no door to drawing or care room.'),
      room('CL','Caregiver lobby',[.5,11.25,9,13.5],'circulation','Pass-through landing: the caregiver door aligns directly with the 3.5 ft spine. The west pocket can contain shallow storage.'),
      room('SP','Service spine',[5.5,14,9,27],'circulation','3.5 ft clear. Connects living, caregiver lobby, common toilet and ground bedroom. Never passes through drawing.'),
      room('WC','Common / caregiver WC',[.5,14,5,20],'wet','4.5 × 6 ft. Reuses the west service zone associated with the former caregiver suite; adapted position on the smaller plot, not identical original coordinates.'),
      room('MB','Master bathroom',[.5,20.5,5,27],'wet','4.5 × 6.5 ft. Door from the master bedroom only.'),
      room('M','Ground master',[.5,27.5,11,39.5],note='10.5 × 12 ft clear. Reduced substantially from the 55 × 60 source to protect the full care-room dimensions.'),
      room('S','Stair',[11.5,27.5,19.5,39.5],'stair','8 × 12 ft reserved core. Schematic dogleg stair, aligned on both floors; use the source 3150 mm floor-to-floor height. Final stair/headroom design is pending.'),
      room('K','L-shaped kitchen',[20,29,30,39.5],'kitchen','10 × 10.5 ft. Two-foot-deep L counter on south/east walls. No puja room, no external kitchen entrance and no old entry-hall/puja doorway. Pantry cupboard and laundry niche replace separate rooms.'),
      room('P','Parking',[30.5,29,49.5,39.5],'parking','19 × 10.5 ft reference bay, entered from the east. Check actual vehicle and gate sweep.'),
      room('DR','Drawing',[9.5,dr_top,dr_right,dr_bottom],note='Exactly ONE wooden door, on the east wall from the veranda. All walls to living, caregiver and care room stay solid. No internal family-hall door.'),
      room('V','Veranda',[v_left,dr_top,v_right,dr_bottom],'outdoor','On the east/right of drawing. Single wooden visitor door to drawing; separate family-hall connection. North entry from the Tirumala road side.'),
      room('ICU','Home care / ICU',[care_x,care_y,care_x+care_w,care_end],'care','Original care room is 6788 × 4150 mm (303.222 sq ft). Both original dimensions are preserved or enlarged. Glass sliding connection to living. Residential care concept; equipment and operating clearances have not been clinically validated.'),
      room('L','Living + dining',[[9.5,hall_top],[hall_right,hall_top],[hall_right,28.5],[20,28.5],[20,27],[9.5,27]],'living','Open family hall connects porch, kitchen, stairs, service spine and care room. No drawing-room door. Dining is within this area, not an extra room.',label=[16.2,(hall_top+26)/2]),
      room('E','Entry porch',[porch_left,porch_top,49.5,28.5],'outdoor','Main east entrance leads directly to family living. No entry through the former kitchen/puja route.'),
      room('G','East planting strip',[care_x+care_w+.5,care_y,49.5,care_end],'garden','Narrow planting/maintenance strip; not an accessible route or an approved setback.'),
    ]
    if rotated:
        g.append(room('NP','North path',[9.5,.5,49.5,3.5],'outdoor','3 ft clear north path. Requires a step-free gate/threshold design if used for assisted access. Care room rotated 90 degrees to make room for this strip.'))
        g.append(room('NW','Open pocket',[9.5,4,20,dr_top] if dr_top>4 else [9.5,.5,20,3.5],'outdoor')) if False else None
    doors=[
      door('caregiver-entry',[5.5,11],[9,11],['CG','CL']),
      door('lobby-spine',[5.5,13.75],[9,13.75],['CL','SP'],'open'),
      door('spine-living',[9.25,22.5],[9.25,26],['SP','L'],'open'),
      door('wc-entry',[5.25,15.5],[5.25,18.5],['SP','WC']),
      door('master-entry',[5.5,27.25],[9,27.25],['SP','M']),
      door('master-bath',[1,27.25],[4,27.25],['M','MB']),
      door('stair-entry',[12,27.25],[19,27.25],['L','S'],'open'),
      door('kitchen-entry',[21,28.75],[26,28.75],['L','K'],'open'),
      door('drawing-only-door',[dr_right+.25,7],[dr_right+.25,10.5],['V','DR']),
      door('veranda-living',[v_left+1,dr_bottom+.25],[v_left+4.5,dr_bottom+.25],['V','L']),
      door('east-main-gate',[49.75,24],[49.75,28],['outside','E'],'gate'),
      door('family-entry',[porch_left-.25,28],[porch_left-.25,24],['E','L']),
      door('car-gate',[49.75,30.5],[49.75,38.5],['outside','P'],'gate'),
      door('north-veranda-entry',[v_left+.75,dr_top-.25],[v_right-.75,dr_top-.25],['NP' if rotated else 'outside','V'],'open'),
    ]
    if rotated:
        doors.append(door('care-living-glass',[26.5,care_end+.25],[33.5,care_end+.25],['L','ICU'],'glass'))
        doors.append(door('north-path-gate',[49.75,.5],[49.75,3.5],['outside','NP'],'gate'))
    else:
        doors.append(door('care-living-glass',[care_x-.25,14.75],[care_x-.25,22.25],['L','ICU'],'glass'))
    # Window lines are not doors and do not count toward drawing's one-door rule.
    doors.extend([
      door('care-north-window',[care_x+1,care_y-.25],[care_x+care_w-1,care_y-.25],[],'window'),
      door('drawing-north-window',[11,dr_top-.25],[dr_right-1,dr_top-.25],[],'window'),
      door('caregiver-window',[.25,2],[.25,7],[],'window'),
      door('master-window',[.25,32],[.25,37],[],'window'),
      door('kitchen-window',[22,39.75],[27,39.75],[],'window'),
    ])
    furn=[furnishing('bed',[.8,.8,3.8,7.3]),furnishing('bed',[1,31.5,7,38.5]),
          furnishing('car',[32.25,31,47.75,37.5]),
          furnishing('counter',[20,37.5,30,39.5]),furnishing('counter',[28,29,30,37.5]),
          furnishing('fridge',[20,29,22,31]),furnishing('table',[22,24.5,27,27]),
          furnishing('sofa',[10.5,5,13,11] if rotated else [11,dr_top+1,17,dr_top+3.5]),
          furnishing('sofa',[10.25,hall_top+1,12.75,hall_top+7]),
          furnishing('wc',[1,15,3,17.5]),furnishing('wc',[1,21,3,23.5]),
          furnishing('shower',[.5,24,3.5,27]),
          furnishing('stair-left',[11.5,27.5,15,36]),furnishing('stair-right',[16,27.5,19.5,36]),
          furnishing('landing',[11.5,36,19.5,39.5])]
    if rotated:
        furn.extend([furnishing('care-bed',[36,8,39.5,15]),furnishing('equipment',[32,10,34,14]),furnishing('chair',[43,10,45.5,12.5])])
    else:
        bx=care_x+care_w*.60
        furn.extend([furnishing('care-bed',[bx,11,bx+3.5,18]),furnishing('equipment',[care_x+1,11,care_x+3,15]),furnishing('chair',[care_x+1,4,care_x+3.5,6.5])])
    # Upper floor retains two family bedrooms, office, terraces and a modest living void.
    u=[
      room('B2','Bedroom 2',[.5,27.5,11,39.5],note='10.5 × 12 ft. Above ground master.'),
      room('UB','Upper bathroom',[.5,20.5,5,27],'wet','4.5 × 6.5 ft. Access from gallery; services broadly align with ground master bath.'),
      room('US','Stair',[11.5,27.5,19.5,39.5],'stair','Aligned with ground stair.'),
      room('O','Office',[20,29,30,39.5],note='10 × 10.5 ft, above kitchen; wardrobe/pantry below must be coordinated with services.'),
      room('T','East terrace',[[porch_left,porch_top],[49.5,porch_top],[49.5,39.5],[30.5,39.5],[30.5,29],[porch_left,29]],'outdoor','Terrace above porch and parking. New beams/columns and drainage are required; spans are not structurally designed.'),
      room('NT','North terrace',[9.5,dr_top,dr_right,dr_bottom],'outdoor','Open terrace over the drawing room, analogous to the original shared terrace.'),
      room('RT','Caregiver roof',[.5,.5,9,10.75],'garden','Unoccupied planted/maintenance roof; no new room.'),
      room('UL','West landing',[.5,11.25,9,13.5],'circulation','Secondary landing over caregiver lobby.'),
      room('UP','West gallery',[5.5,14,9,27],'circulation','Gallery links Bedroom 2 and shared bathroom.'),
    ]
    hall_geom=Polygon(next(r['p'] for r in g if r['id']=='L'))
    north_link=box(v_left,dr_top,v_right,dr_bottom)
    # Bridge the separating nominal partition into a continuous upper gallery.
    hall_geom=unary_union([hall_geom,north_link,box(v_left,dr_bottom,v_right,hall_top+.01)])
    if rotated:
        void=box(11,18.75,17,24.75)
        b3=[26,4,41.77,care_end]; bath=[42.27,4,48.27,11.5]; balcony=[42.27,12,48.27,care_end]
    else:
        void=box(19,18.5,25,24.5)
        b3=[care_x,.5,47.5,14]; bath=[care_x,14.5,care_x+6,care_end]; balcony=[care_x+6.5,14.5,47.5,care_end]
    if not rotated: hall_geom=hall_geom.difference(void.buffer(.5,join_style=2))
    assert hall_geom.geom_type=='Polygon', key
    # A hole-bearing gallery is represented with its exact holes for validation/rendering.
    ur=room('U','Upper gallery',points(hall_geom),'circulation','Connects all upper rooms, north terrace and east terrace. Guard the 6 × 6 ft living void.')
    ur['holes']=[[[x,y] for x,y in list(r.coords)[:-1]] for r in hall_geom.interiors]
    ur['area']=round(hall_geom.area,3)
    ur['at']=[22,22] if rotated else [14.5,18]
    ur['rectangular']=False
    u += [ur,room('VOID','Living void',points(void),'void','6 × 6 ft double-height opening above living; guarded perimeter.'),
          room('B3','Upper master',b3,note='North/east bedroom over the care room. The reduced ground plot requires a new structural layout.'),
          room('B3B','Master ensuite',bath,'wet','Separate upper ensuite.'),room('BAL','Private balcony',balcony,'outdoor','Garden-facing upper balcony; guards and drainage to be detailed.')]
    ud=[door('u-bedroom2',[5.5,27.25],[9,27.25],['UP','B2']),
        door('u-bath',[5.25,22],[5.25,25],['UP','UB']),
        door('u-west-gallery',[9.25,22.5],[9.25,26],['UP','U'],'open'),
        door('u-stair',[12,27.25],[19,27.25],['U','US'],'open'),
        door('u-office',[21,28.75],[24.5,28.75],['U','O']),
        door('u-east-terrace',[porch_left-.25,24],[porch_left-.25,27.5],['U','T']),
        door('u-north-terrace',[dr_right+.25,7],[dr_right+.25,10.5],['U','NT']),
        door('u-lobby-spine',[5.5,13.75],[9,13.75],['UL','UP'],'open')]
    if rotated:
        ud += [door('u-master',[26.5,care_end+.25],[30,care_end+.25],['U','B3']),
               door('u-ensuite',[42.02,6],[42.02,9],['B3','B3B']),
               door('u-balcony',[42.02,13],[42.02,16],['B3','BAL'])]
    else:
        ud += [door('u-master',[care_x-.25,7],[care_x-.25,10.5],['U','B3']),
               door('u-ensuite',[care_x+1,14.25],[care_x+4,14.25],['B3','B3B']),
               door('u-balcony',[care_x+7,14.25],[care_x+10,14.25],['B3','BAL'])]
    if rotated:
        u=[r for r in u if r['id']!='VOID']
        next(r for r in u if r['id']=='U')['note']='Continuous upper family gallery. This alternative omits the double-height void to simplify circulation and create the north path arrangement.'
    uf=[furnishing('bed',[1,31.5,7,38.5]),furnishing('desk',[21,36,27,38]),
        furnishing('bed',[b3[0]+4,b3[1]+3,b3[0]+10,b3[1]+10]),
        furnishing('stair-left',[11.5,27.5,15,36]),furnishing('stair-right',[16,27.5,19.5,36]),furnishing('landing',[11.5,36,19.5,39.5])]
    summaries={
      'A':'Balanced enlargement: 16 ft east–west × 22.27 ft north–south care room; a 15.5 × 13.5 ft drawing room.',
      'B':'Closest to original care dimensions: 13.62 × 22.27 ft; the largest drawing and family hall among the unrotated versions.',
      'C':'Maximum care area: 18 × 22.27 ft; the drawing room reduces to 13.5 × 13.5 ft.',
      'D':'Original care rectangle rotated 90°: 22.27 × 13.62 ft; adds a 3 ft north path, with a smaller drawing room and a continuous upper floor instead of the living void.'}
    return dict(id=key,name=name,plot=[50,40],summary=summaries[key],
                careOriginalMm=[6788,4150],rotatedCare=rotated,
                floors={'ground':finish_floor(g,doors,furn),'first':finish_floor(u,ud,uf)})

def original():
    p=json.loads((ROOT/'examples/gallery/my-desired-home/project.floorforge.json').read_text())
    b=json.loads((ROOT/'examples/gallery/my-desired-home/building.json').read_text())
    transform=lambda pt:[(14326-pt[1])/FT,60-pt[0]/FT]
    codes={'u-office':'O','u-lobby':'EN','u-terrace-front':'ET','u-studio-terrace':'ST','u-stair':'S','u-lounge':'L','u-living-void':'VOID','u-terrace-north':'BAL','u-veranda-terrace':'NT','u-garden-daylight':'SKY','u-bed-south':'B2','u-bedroom-balcony':'WB','u-bath':'UB','u-bed-north':'B3','g-care':'ICU','g-drawing':'DR','g-caregiver':'CG','g-caregiver-bath':'WC','g-veranda':'V','g-living':'L','g-dining':'EN','g-kitchen':'K','g-puja':'PU','g-stair':'S','g-bedroom':'M','g-bath':'MB','g-care-lawn':'G','g-care-court':'LW','g-court-ledge':'LE','g-kitchen-store':'ST','g-wash':'WY','g-bedroom-airgap':'AG'}
    fs={}
    for index,fl in enumerate(p['customPlan']['floors']):
        rr=[]
        for r in fl['rooms']:
            kind='room'
            if r['kind'] in ('veranda','terrace','balcony','courtyard'):kind='outdoor'
            if r['kind']=='care-room':kind='care'
            if r['kind']=='kitchen':kind='kitchen'
            if r['kind']=='living':kind='living'
            if r['kind']=='bathroom':kind='wet'
            if r['kind']=='stair':kind='stair'
            if r['kind']=='void':kind='void'
            rr.append(room(codes.get(r['id'],r['id'][2:].upper()),r['name'],[transform(pt) for pt in r['polygon']],kind,'Exact polygon from the saved 55 × 60 source project.'))
        walls={w['id']:w for w in b['walls'] if w['floor']==index}
        dd=[]
        for o in b['openings']:
            if o['floor']!=index:continue
            w=walls[o['wall_id']];a=w['a'];c=w['b'];ln=math.dist(a,c);v=[(c[j]-a[j])/ln for j in (0,1)]
            pa=[a[j]+v[j]*o['offset'] for j in (0,1)];pb=[a[j]+v[j]*(o['offset']+o['width']) for j in (0,1)]
            dd.append(door(o['id'],transform(pa),transform(pb),[],{'glazed':'glass','window':'window','cased':'open'}.get(o['kind'],'wood')))
        fs['ground' if index==0 else 'first']=dict(rooms=rr,doors=dd,furniture=[],walls=[dict(outer=[transform(pt) for pt in w['polygon']],holes=[]) for w in walls.values()])
    return dict(id='original',name='Original · 55 × 60',plot=[55,60],summary='Unchanged reference geometry. North is up here; the original sheet puts north on the right. Care room: 6788 × 4150 mm.',floors=fs)

def geometry(r):return Polygon(r['p'],r.get('holes',[]))

def validate(data):
    checks=[]
    for o in data['options']:
        for level,fl in o['floors'].items():
            for r in fl['rooms']:
                p=geometry(r)
                assert p.is_valid and p.area>0,(o['id'],level,r['id'],'invalid')
                assert box(0,0,50,40).buffer(.00001).covers(p),(o['id'],r['id'],'outside plot')
            for i,a in enumerate(fl['rooms']):
                for b in fl['rooms'][i+1:]:
                    overlap=geometry(a).intersection(geometry(b)).area
                    assert overlap<.0001,(o['id'],level,a['id'],b['id'],'overlap',overlap)
            ids={r['id'] for r in fl['rooms']}
            edges={i:set() for i in ids|{'outside'}}
            for d in fl['doors']:
                if len(d['connects'])==2:
                    a,b=d['connects'];assert a in edges and b in edges
                    line=LineString([d['a'],d['b']])
                    for connected in (a,b):
                        if connected!='outside':
                            rp=geometry(next(r for r in fl['rooms'] if r['id']==connected))
                            assert rp.buffer(.36).covers(line),(o['id'],level,d['id'],'not on room boundary')
                    edges[a].add(b);edges[b].add(a)
            seen=set();todo=['outside' if level=='ground' else 'US']
            while todo:
                x=todo.pop()
                if x in seen:continue
                seen.add(x);todo.extend(edges[x]-seen)
            needed={r['id'] for r in fl['rooms'] if r['kind'] not in ('garden','void')}
            assert needed<=seen,(o['id'],level,'inaccessible',needed-seen)
        fl=o['floors']['ground'];care=next(r for r in fl['rooms'] if r['id']=='ICU')
        assert all(a+.00001>=b for a,b in zip(sorted(care['size']),sorted([SHORT,LONG])))
        dr_doors=[d for d in fl['doors'] if 'DR' in d['connects']]
        assert len(dr_doors)==1 and set(dr_doors[0]['connects'])=={'DR','V'} and dr_doors[0]['kind']=='wood'
        assert not any('CG' in d['connects'] and 'DR' in d['connects'] for d in fl['doors'])
        assert all(r['id']!='PU' for r in fl['rooms'])
        checks.append(dict(option=o['id'],careSizeFt=care['size'],careAreaSqFt=care['area'],originalAreaSqFt=round(LONG*SHORT,3),roomOverlap=False,withinPlot=True,allOccupiedRoomsConnected=True,drawingDoors=1,drawingEntry='veranda only',pujaRemoved=True))
    return dict(status='passed',checks=checks,limits=['Geometric concept checks only, not building approval, structural design or clinical ICU validation.','Door lines were checked against both connected room polygons. Usable opening, furniture routes, swing conflicts and stair headroom still require detailed design.','Original caregiver coordinates cannot remain identical when reducing the plot; its west service zone is adapted into toilets and a separate caregiver room.','Nominal 6-inch partitions; legal setbacks have not been established.'])

if __name__=='__main__':
    protected=[ROOT/'examples/gallery/my-desired-home/project.floorforge.json',ROOT/'examples/gallery/my-desired-home/building.json',ROOT/'examples/gallery/briefs/my-desired-home.json',ROOT/'examples/gallery/briefs/tirumala.json',ROOT/'examples/gallery/tirumala/building.json',ROOT/'examples/gallery/catalog.json']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    hashes={str(p.relative_to(ROOT)):sha(p) for p in protected}
    data=dict(title='My Desired Home · 40 × 50 concepts',units='feet',coordinateSystem='North-up; x east from west boundary; y south from north boundary',
              status='Review-only proposal: no 3D build or sample-gallery registration performed',
              confirmed=['Drawing door from veranda only, wooden, one door','Caregiver west of drawing; former caregiver/service location becomes toilet','40 ft north–south × 50 ft east–west; east frontage','Tirumala north road/garden and east road/basketball court'],
              context=dict(northRoadM=12,eastRoadM=9,northGarden='Colony garden with lawn, palms, pergola and planting beyond north road',eastCourt='Basketball court with pale mesh enclosure and palms beyond east road',source='floorforge/tirumala_context.py; exterior context lies outside the 2000 sq ft private plot'),
              options=[make_option('A','Balanced care enlargement',16),make_option('B','Original care size',SHORT),make_option('C','Maximum care room',18),make_option('D','North path + rotated care',LONG,True)],original=original(),sourceHashes=hashes)
    validation=validate(data)
    (OUT/'concepts.json').write_text(json.dumps(data,indent=2)+'\n')
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    (OUT/'source-integrity.json').write_text(json.dumps(dict(before=hashes,after={str(p.relative_to(ROOT)):sha(p) for p in protected},unchanged=all(sha(p)==hashes[str(p.relative_to(ROOT))] for p in protected)),indent=2)+'\n')
    print(json.dumps(validation,indent=2))
