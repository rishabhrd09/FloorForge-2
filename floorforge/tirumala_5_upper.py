"""Tirumala 5 G+2 architectural addition, in millimetres (+x north, +y west).

The lower rooms are retained. This module adds a roof-level hall and usable roof
terrace, plus a second stair stacked over the existing stair core. Member sizes
are architectural placeholders, not a structural design or reinforcement schedule.
"""
from copy import deepcopy
import html
import math
import re

from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

from .tirumala_luxury import H, ring, regions, upper_plan

REVISION = 'tirumala-5-g2-skylit-atrium-2026-11-05'
LEVEL = 2 * H
ROOM_HEIGHT = 3350
HALL = [150, 9050, 5335.6, 14328]
GUEST = [8350, 6350, 11432.4, 11400]
GUEST_EXTENSION = [8045.2, 6350, 8350, 9200]
FIRST_APPROACH = [1525, 4875, 6300, 6075]
SECOND_SHAFT = [150, 5000, 5150, 8900]
HEADHOUSE_CLEAR = [150, 4875, 6600, 10050]
HEADHOUSE_OUTER = [0, 4725, 6750, 10200]
SECOND_LOBBY = [5150, 7800, 6600, 8900]
BEDROOM_ROOF = [7895.2, 6200, 11582.4, 11550]
STAIR_WIDTH = 1100
RISE = 175
ARRIVAL_RISE = (H - 18 * RISE) / 2
ATRIUM = [1675, 6075, 5000, 7800]
EAST_ENCLOSURE = [1525, 4875, 6600, 7800]


def guest_shape():
    return box(*GUEST).union(box(*GUEST_EXTENSION))


def headhouse_shape():
    # Follow the stair core; the north return is clear of the last connector.
    return unary_union([box(150, 6600, 5335.6, 8900),
                        box(150, 4875, 1525, 6600),
                        box(*SECOND_LOBBY), box(5485.6, 8900, 6600, 10050),
                        box(*EAST_ENCLOSURE)])


def stacked_steps(ground):
    """Exact lower-stair XY and levels, translated up one floor."""
    steps = []; rise_index = 0
    for st in ground['stairs']:
        x0, y0, x1, y1 = Polygon(st['polygon']).bounds
        if 'level' in st:
            steps.append(dict(id='s2-'+st['id'], bounds=[x0,y0,x1,y1],
                              top=H+st['level'], landing=True))
            continue
        n = int(st['risers']); direction = st['direction']
        for i in range(n):
            if direction == 'South':
                dx=(x1-x0)/n; bounds=[x1-(i+1)*dx,y0,x1-i*dx,y1]
            elif direction == 'West':
                dy=(y1-y0)/n; bounds=[x0,y0+i*dy,x1,y0+(i+1)*dy]
            else:
                dx=(x1-x0)/n; bounds=[x0+i*dx,y0,x0+(i+1)*dx,y1]
            rise_index += 1
            steps.append(dict(id=f"s2-{st['id']}-{i+1}", bounds=bounds,
                              top=H+rise_index*RISE, landing=False))
    for i,st in enumerate(upper_plan(ground)['connectorSteps']):
        steps.append(dict(id=f's2-arrival-connector-{i+1}', bounds=st['bounds'][:],
                          top=H+st['top'], landing=False))
    return steps


def stacked_shaft(ground):
    return unary_union([box(*st['bounds']) for st in stacked_steps(ground)])


def _shape(regs):
    return unary_union([Polygon(r['polygon'], r.get('holes', [])) for r in regs])


def _room(ident, kind, name, poly):
    rr=regions(poly)
    return dict(id=ident, kind=kind, name=name, polygon=rr[0]['polygon'],
                regions=rr, bounds=list(poly.bounds), area_m2=poly.area/1e6,
                enclosed=kind!='terrace',roofed=kind!='terrace')


# Fixed, reviewed opening schedule for the approved first-floor revision.
# The unaffected room openings retain their existing locations and sizes.
FIRST_OPENINGS = [{'id': 'u-master-door',
  'a': [5650, 8975],
  'b': [6450, 8975],
  'raw_kind': 'door',
  'sill': 0,
  'height': 2450,
  'connects': ['u-gallery', 'u-master'],
  'hinge': 'b',
  'swing_vec': [6450, 9775.0]},
 {'id': 'u-master-bath-door',
  'a': [3515.766667, 12700],
  'b': [3515.766667, 13600],
  'raw_kind': 'door',
  'sill': 0,
  'height': 2300,
  'connects': ['u-master', 'u-master-bath'],
  'hinge': 'a'},
 {'id': 'u-office-door',
  'a': [8275, 11600],
  'b': [8275, 12500],
  'raw_kind': 'door',
  'sill': 0,
  'height': 2450,
  'connects': ['u-gallery', 'u-study'],
  'hinge': 'a',
  'swing_vec': [9175.0, 11600]},
 {'id': 'u-bedroom-door',
  'a': [7970.2, 8250],
  'b': [7970.2, 9150],
  'raw_kind': 'door',
  'sill': 0,
  'height': 2450,
  'connects': ['u-gallery', 'u-bedroom'],
  'hinge': 'a',
  'swing_vec': [8870.2, 8250]},
 {'id': 'u-bath-door',
  'a': [7200, 12525],
  'b': [8100, 12525],
  'raw_kind': 'door',
  'sill': 0,
  'height': 2300,
  'connects': ['u-gallery', 'u-bath'],
  'hinge': 'a'},
 {'id': 'u-terrace-door',
  'a': [6500, 4800],
  'b': [8100, 4800],
  'raw_kind': 'sliding-door',
  'sill': 0,
  'height': 2700,
  'connects': ['u-gallery', 'u-terrace'],
  'hinge': 'a'},
 {'id': 'u-master-rear',
  'a': [650, 14403],
  'b': [2850, 14403],
  'raw_kind': 'window',
  'sill': 450,
  'height': 2500,
  'connects': ['u-master', 'outside'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'},
 {'id': 'u-master-south',
  'a': [75, 10100],
  'b': [75, 11800],
  'raw_kind': 'window',
  'sill': 450,
  'height': 2500,
  'connects': ['u-master', 'outside'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'},
 {'id': 'u-office-rear',
  'a': [8750, 14403],
  'b': [11000, 14403],
  'raw_kind': 'window',
  'sill': 450,
  'height': 2500,
  'connects': ['u-study', 'outside'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'},
 {'id': 'u-office-north',
  'a': [11507.4, 12400],
  'b': [11507.4, 13900],
  'raw_kind': 'window',
  'sill': 450,
  'height': 2500,
  'connects': ['u-study', 'outside'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'},
 {'id': 'u-bedroom-north',
  'a': [11507.4, 9100],
  'b': [11507.4, 11000],
  'raw_kind': 'window',
  'sill': 450,
  'height': 2500,
  'connects': ['u-bedroom', 'outside'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'},
 {'id': 'u-bedroom-east-proposed',
  'a': [8750, 6275],
  'b': [11000, 6275],
  'raw_kind': 'window',
  'sill': 400,
  'height': 2550,
  'connects': ['u-bedroom', 'outside'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'},
 {'id': 'u-bath-rear',
  'a': [6600, 14403],
  'b': [7750, 14403],
  'raw_kind': 'window',
  'sill': 1700,
  'height': 1000,
  'connects': ['u-bath', 'outside'],
  'hinge': 'a'},
 {'id': 'u-ensuite-rear',
  'a': [4100, 14403],
  'b': [5350, 14403],
  'raw_kind': 'window',
  'sill': 1700,
  'height': 1000,
  'connects': ['u-master-bath', 'outside'],
  'hinge': 'a'},
 {'id': 'u-gallery-lightwell',
  'a': [7210.6, 10450],
  'b': [7210.6, 11650],
  'raw_kind': 'window',
  'sill': 900,
  'height': 1800,
  'connects': ['u-gallery', 'outside'],
  'hinge': 'a'},
 {'id': 'u-master-lightwell',
  'a': [5560.6, 10600],
  'b': [5560.6, 11400],
  'raw_kind': 'window',
  'sill': 900,
  'height': 1800,
  'connects': ['u-master', 'outside'],
  'hinge': 'a'},
 {'id': 'u-atrium-east',
  'a': [1800, 4800],
  'b': [5700, 4800],
  'raw_kind': 'window',
  'sill': 150,
  'height': 2900,
  'connects': ['u-gallery', 'u-terrace'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'},
 {'id': 'u-atrium-south',
  'a': [75, 5450],
  'b': [75, 7300],
  'raw_kind': 'window',
  'sill': 150,
  'height': 2900,
  'connects': ['u-gallery', 'outside'],
  'hinge': 'a',
  'window_style': 'picture-with-sliding-vents'}]


FIRST_OPENINGS = [o for o in FIRST_OPENINGS
                  if o['id'] not in ('u-master-south', 'u-atrium-south')]
FIRST_OPENINGS.append(dict(id='u-stair-east', a=[250,4800], b=[1250,4800],
    raw_kind='window', sill=150, height=2900, connects=['u-gallery','outside'],
    hinge='a', window_style='picture-with-sliding-vents'))


def first_plan(ground):
    """Approved upper rooms and internal approach, without an exterior stair detour."""
    up=upper_plan(ground)
    rooms={r['id']:r for r in up['rooms']}
    rooms['u-bedroom'].update(_room('u-bedroom','bedroom','Guest bedroom',guest_shape()))
    gallery=_shape(rooms['u-gallery']['regions']).union(box(*FIRST_APPROACH))
    gallery=gallery.difference(guest_shape().buffer(150,join_style=2))
    rooms['u-gallery'].update(_room('u-gallery','hall','Gallery overlooking living',gallery))
    terrace=_shape(rooms['u-terrace']['regions']).intersection(box(0,1524,9032,4800))
    rooms['u-terrace'].update(_room('u-terrace','terrace','Open garden terrace',terrace))
    solids=[]
    for r in rooms.values():
        if r['kind'] not in ('hall','terrace'):
            pp=_shape(r['regions']);solids.append(pp.buffer(150,join_style=2).difference(pp))
    solids.append(unary_union([box(6250,4725,8350,4875),box(8200,4800,8350,6200),
                               box(0,4800,150,8900),box(150,4725,6300,4875)]))
    lightwell=Polygon(up['lightwellClear'])
    solids.append(lightwell.buffer(150,join_style=2).difference(lightwell))
    raw=unary_union(solids);wall=raw
    for op in FIRST_OPENINGS:wall=wall.difference(LineString([op['a'],op['b']]).buffer(90,cap_style=2))
    void=box(1250,6075,6300,7800)
    plate=unary_union([_shape(r['regions']) for r in rooms.values()]+[raw])
    plate=plate.difference(lightwell).difference(_shape(up['stairVoid'])).difference(void)
    up.update(revision=REVISION,wallRegions=regions(wall),floorPlate=regions(plate),void=ring(void),
        roof=regions(_shape(up['roof']).union(guest_shape().buffer(150,join_style=2))),
        openingSchedule=deepcopy(FIRST_OPENINGS),stairApproach=FIRST_APPROACH[:],
        galleryGuards=[[[6300,6075],[6300,7800]],[[1525,6075],[6300,6075]],
                       [[5150,7800],[6300,7800]],[[4550,7800],[5150,7800]],
                       [[4550,8900],[5150,8900]]],
        circulationPaths={
          'arrival_to_stair':[[5700,8350],[6900,8350],[6900,5475],[1525,5475]],
          'arrival_to_guest':[[5700,8350],[7400,8350],[7400,8700],[7895.2,8700]],
          'arrival_to_main_terrace':[[5700,8350],[7300,8350],[7300,4800]],
          'arrival_to_office':[[5700,8350],[7400,8350],[7400,9250],[7380,9520],[7600,9700],[7742.8,9900],[7742.8,12025],[8200,12025]]},
        balconyRevision='Small north balcony absorbed; front guest section extends 1 ft south with a stepped return retaining the rear gallery; large terrace retained.',
        guestExtensionMm=GUEST_EXTENSION[:],bridgeClearWidthMm=1100,bridgeGrossWidthMm=1200)
    return up


def second_plan(ground):
    up=first_plan(ground)
    roof=_shape(up['roof'])
    shaft=stacked_shaft(ground)
    atrium=box(*ATRIUM)
    plate=roof.difference(shaft).difference(Polygon(up['lightwell'])).difference(atrium)
    hall=box(*HALL);hall_shell=hall.buffer(150,join_style=2)
    headhouse=headhouse_shape().buffer(150,join_style=2)
    terrace=plate.difference(hall_shell.union(headhouse))
    landing=headhouse_shape().difference(shaft).difference(atrium)
    steps=stacked_steps(ground)
    furniture=[
        dict(id='s2-sofa',kind='sofa',bounds=[900,13000,3400,13900]),
        dict(id='s2-coffee',kind='table',bounds=[1700,11700,2800,12350]),
        dict(id='s2-lounge-1',kind='chair',bounds=[600,11200,1400,12000]),
        dict(id='s2-lounge-2',kind='chair',bounds=[3000,11200,3800,12000]),
        dict(id='s2-media',kind='console',bounds=[1300,9075,3600,9325]),
        dict(id='s2-library',kind='shelf',bounds=[450,12500,850,14300]),
        dict(id='s2-terrace-sofa',kind='sofa',bounds=[6500,12900,9000,13800]),
        dict(id='s2-terrace-table',kind='table',bounds=[7200,11800,8300,12450]),
    ]
    return dict(revision=REVISION,levelMm=LEVEL,roomHeightMm=ROOM_HEIGHT,
                rooms=[_room('s2-hall','hall','Second-floor family hall',hall),
                       _room('s2-indoor-landing','hall','Enclosed stair landing',landing),
                       _room('s2-terrace','terrace','Open roof garden terrace',terrace)],
                floorPlate=regions(plate),stairVoid=regions(shaft),stairs=steps,
                atriumOpening=ring(atrium),eastEnclosure=EAST_ENCLOSURE[:],
                skylight=dict(boundsMm=ATRIUM[:],clearSizeMm=[3325,1725],
                    areaSqFt=atrium.area/92903.04,roofElevationMm=LEVEL+ROOM_HEIGHT,
                    glazing='Insulated solar-control glazing with laminated inner pane; sloping framed rooflight on raised drained curb.',
                    scope='Architectural representation; structural support, glazing specification, fixing and waterproofing require engineering.'),
                stairStartLanding=FIRST_APPROACH[:],stairArrival=SECOND_LOBBY[:],
                headhouseClearEnvelope=HEADHOUSE_CLEAR[:],headhouseOuterEnvelope=HEADHOUSE_OUTER[:],
                secondLanding=SECOND_LOBBY[:],headhouseRegions=regions(headhouse),lightwell=up['lightwell'],
                lightwellClear=up['lightwellClear'],
                hallRoof=regions(hall_shell.union(headhouse).difference(atrium)),roofOutline=regions(roof),
                newBedRoof=regions(guest_shape().buffer(150,join_style=2)),furniture=furniture,
                landingGuards=[[[1250,6600],[1525,6600]],
                               [[1250,6600],[1250,7800]],[[1250,7800],[5150,7800]],
                               [[1675,6075],[1675,7800]],[[1675,6075],[5000,6075]],
                               [[5000,6075],[5000,7800]]],
                circulationPaths={'stairs_to_hall':[[5150,8350],[6050,8350],[6050,9550],[5200,9550]],
                  'stairs_to_terrace':[[5150,8350],[6050,8350],[6050,8400],[6900,8400]],
                  'stairs_to_east_gallery':[[5700,8350],[5800,8350],[5800,5475],[2200,5475]]},
                minimumAnalyticGroundStairHeadroomMm=H-RISE-180,
                riserHeightsMm=[RISE]*18+[ARRIVAL_RISE]*2,
                pantryClearance={'cabinetHeightMm':1800,
                  'minimumUnderWaistMm':1575+(2000-1250)/2200*1575-150,
                  'centreUnderWaistMm':1575+((2000+3371.6)/2-1250)/2200*1575-150,
                  'waistThicknessMm':150,
                  'note':'Dry cabinet below sloping ground stair; minimum occurs at its south end, not a walk-in room.'},
                structuralConcept={'hallSupportLinesMm':[[0,8975,5550,8975],[0,14403,5550,14403]],
                 'headhouseSupportEnvelopeMm':HEADHOUSE_OUTER[:],
                 'guestRoofRegions':regions(guest_shape().buffer(150,join_style=2)),
                 'landingReturnSupport':'The final 150 mm wall band follows the existing lightwell wall directly below; slab cutout and clear lightwell stay unchanged.',
                 'atriumSupport':'Trim second-floor slab and highest roof around the aligned aperture; enclosure and trimmer supports must be coordinated with the lower structure. Preserve the clear vertical sightline.',
                 'status':'Concept only: design foundations, continuous load paths, new bedroom edge support and roof, approach landing and stair waist, seismic system and saturated planter loads before construction.'},
                gardenNote='Shallow perimeter planting; raised pots over supported edges; paved circulation, drainage and overflow provision.')


def project_addition(project):
    cp=project['customPlan']
    cp['upperPlan']=first_plan(cp['canonicalPlan'])
    cp['secondPlan']=second_plan(cp['canonicalPlan'])
    cp['g2Revision']=REVISION
    cp['floors']=[f for f in cp['floors'] if f.get('id')!='floor-2']
    cp['floors'][1]['rooms']=[dict(id=r['id'],kind=r['kind'],name=r['name'],polygon=deepcopy(r['polygon'])) for r in cp['upperPlan']['rooms']]
    cp['floors'].append(dict(id='floor-2',rooms=[dict(id=r['id'],kind=r['kind'],name=r['name'],
        polygon=deepcopy(r['polygon']),enclosed=r['kind']!='terrace',roofed=r['kind']!='terrace')
        for r in cp['secondPlan']['rooms']],walls=[],openings=[]))
    project['brief'].update(storeys=3,roof_access=False)
    project['editorState']['customPlan']=deepcopy(cp)
    return project


def _opening(b,ident,floor,a,c,kind,sill,height,connects):
    width=math.dist(a,c)
    wall=dict(id='host-'+ident,floor=floor,floorId=f'floor-{floor}',a=a,b=c,start=a,end=c,
              polygon=ring(LineString([a,c]).buffer(75,cap_style=2)),thickness=150,height=ROOM_HEIGHT if floor==2 else H,
              rooms=[v for v in connects if v!='outside'],
              external=bool(set(connects)&{'outside','u-terrace','s2-terrace'}),structural=False,hostOnly=True)
    b['walls'].append(wall)
    op=dict(id=ident,floor=floor,floorId=f'floor-{floor}',wall=wall['id'],wall_id=wall['id'],a=a,b=c,
            kind='window' if sill else 'door',raw_kind=kind,sill=sill,height=height,width=width,offset=0,
            connects=connects,hinge='a',elevation_mm=floor*H)
    if sill:op['window_style']='picture-with-sliding-vents'
    b['openings'].append(op)
    return op


def compile_addition(b):
    up=first_plan(b['planning']['canonicalPlan']);b['planning']['upperPlan']=up
    # Recompose only the approved first-floor changes. Ground geometry is untouched.
    for r in up['rooms']:
        ss=next(s for s in b['spaces'] if s['id']==r['id'])
        ss.update(polygon=r['polygon'],clear=r['polygon'],holes=r['regions'][0]['holes'],
                  regions=r['regions'],bounds=r['bounds'],area_m2=r['area_m2'],areaSqFt=r['area_m2']/.09290304)
    f1=next(f for f in b['floor_plates'] if f['floor']==1)
    f1.update(regions=deepcopy(up['floorPlate']),outline=deepcopy(up['floorPlate']),
              slab=up['floorPlate'][0]['polygon'],holes=up['floorPlate'][0]['holes'],
              openings=[up['void'],up['lightwell']]+[r['polygon'] for r in up['stairVoid']])
    roof0=next(r for r in b['roofs'] if r['floor']==0)
    roof0.update(regions=deepcopy(up['floorPlate']),ceiling=deepcopy(up['floorPlate']),
                 slab=up['floorPlate'][0]['polygon'],holes=up['floorPlate'][0]['holes'])
    next(s for s in b['shafts'] if s['id']=='living-double-height')['polygon']=deepcopy(up['void'])
    b['walls']=[w for w in b['walls'] if w['floor']!=1]
    b['openings']=[o for o in b['openings'] if o['floor']!=1]
    for d in up['openingSchedule']:
        op=_opening(b,d['id'],1,d['a'],d['b'],d['raw_kind'],d['sill'],d['height'],d['connects'])
        for key in ('hinge','swing_vec','window_style'):
            if key in d:op[key]=deepcopy(d[key])
    for i,r in enumerate(up['wallRegions']):
        a,c=r['polygon'][:2]
        b['walls'].append(dict(id=f'u-wall-{i}',floor=1,floorId='floor-1',a=a,b=c,start=a,end=c,
                              polygon=r['polygon'],holes=r['holes'],thickness=150,height=H,rooms=[],external=True,structural=True))
    sp=second_plan(b['planning']['canonicalPlan'])
    b['planning']['secondPlan']=sp;b['planning']['g2Revision']=REVISION
    b['storeys']=3;b['brief'].update(storeys=3,roof_access=False)
    b['floors'].append(dict(id='floor-2',index=2))
    for r in sp['rooms']:
        b['spaces'].append(dict(id=r['id'],name=r['name'],kind=r['kind'],floor=2,floorId='floor-2',
          polygon=r['polygon'],clear=r['polygon'],holes=r['regions'][0]['holes'],regions=r['regions'],
          bounds=r['bounds'],area_m2=r['area_m2'],areaSqFt=r['area_m2']/.09290304,elevation_mm=LEVEL,
          walkable=True,enclosed=r['kind']!='terrace',roofed=r['kind']!='terrace',wet=False,ceilingHeight=ROOM_HEIGHT))
    stair_poly=_shape(sp['stairVoid'])
    b['stairs'].append(dict(id='s2-stair',floor=1,to_floor=2,roomId='s2-stair',linkId='s2-stair',
       shape='three-flight-c-stair',kind='three-flight-c-stair',risers=20,riser_count=20,riser_mm=RISE,
       tread_mm=2200/9,flight_width=1100,landing_mm=1100,width=5000,depth=3900,x=150,y=5000,
       riser_heights_mm=sp['riserHeightsMm'],
       polygon=ring(stair_poly),flights=deepcopy(sp['stairs']),arrival_elevation_mm=LEVEL,
       elevation_mm=H,route='First gallery → indoor east-edge bridge → South / West / North stacked stair → enclosed second landing → hall / roof garden'))
    hall=box(*HALL); wall=unary_union([hall.buffer(150,join_style=2).difference(hall),
        headhouse_shape().buffer(150,join_style=2).difference(headhouse_shape())])
    defs=[('s2-hall-entry',[5410.6,9050],[5410.6,10050],'door',0,2700,['s2-indoor-landing','s2-hall']),
          ('s2-hall-garden',[5410.6,12400],[5410.6,14100],'sliding-door',0,2850,['s2-hall','s2-terrace']),
          ('s2-hall-rear',[800,14403],[4400,14403],'window',600,2250,['s2-hall','outside']),
          ('s2-stair-terrace-proposed',[6675,7900],[6675,8900],'door',0,2700,['s2-indoor-landing','s2-terrace']),
          ('s2-stair-east',[250,4800],[1250,4800],'window',150,2900,['s2-indoor-landing','outside']),
          ('s2-gallery-east',[1800,4800],[5700,4800],'window',150,2900,['s2-indoor-landing','outside'])]
    for ident,a,c,kind,sill,height,conn in defs:
        op=_opening(b,ident,2,a,c,kind,sill,height,conn)
        if ident=='s2-hall-entry':op.update(hinge='b',swing_vec=[4410.6,10050])
        if ident=='s2-stair-terrace-proposed':op.update(hinge='a',swing_vec=[7675,7900])
        wall=wall.difference(LineString([a,c]).buffer(90,cap_style=2))
    sp['wallRegions']=regions(wall)
    sp['openingSchedule']=deepcopy([o for o in b['openings'] if o['floor']==2])
    for i,r in enumerate(sp['wallRegions']):
        a,c=r['polygon'][:2]
        b['walls'].append(dict(id=f's2-wall-{i}',floor=2,floorId='floor-2',a=a,b=c,start=a,end=c,
           polygon=r['polygon'],holes=r['holes'],thickness=150,height=ROOM_HEIGHT,rooms=['s2-hall','s2-indoor-landing'],external=True,structural=True))
    b['floor_plates'].append(dict(id='plate-floor-2',floor=2,floorId='floor-2',regions=sp['floorPlate'],
       outline=sp['floorPlate'],slab=sp['floorPlate'][0]['polygon'],holes=sp['floorPlate'][0]['holes'],
       thickness=180,elevation=LEVEL,openings=[r['polygon'] for r in sp['stairVoid']]+[sp['lightwell'],sp['atriumOpening']]))
    roof1=next(r for r in b['roofs'] if r['floor']==1)
    roof1.update(regions=sp['floorPlate'],ceiling=sp['floorPlate'],slab=sp['floorPlate'][0]['polygon'],
                 holes=sp['floorPlate'][0]['holes'],elevation=LEVEL,parapet_height=1100)
    b['roofs'].append(dict(id='roof-floor-2',floor=2,regions=sp['hallRoof'],ceiling=sp['hallRoof'],
       slab=sp['hallRoof'][0]['polygon'],holes=sp['hallRoof'][0]['holes'],elevation=LEVEL+ROOM_HEIGHT,thickness=180,parapet_height=300))
    b['shafts'][0]['floors']=[0,1,2]
    b['shafts'].append(dict(id='living-rooflight-atrium',kind='atrium',floors=[0,1,2],
                           polygon=sp['atriumOpening'],rooflight=deepcopy(sp['skylight'])))
    return b


def add_scene(k,mats,b,door_motion,lawns):
    from .tirumala_openings import build_opening,pose_initial_opening
    import trimesh
    sp=b['planning']['secondPlan'];z=LEVEL/1000;top=z+ROOM_HEIGHT/1000;z1=H/1000
    def p(r):return Polygon([(x/1000,y/1000) for x,y in r['polygon']], [[(x/1000,y/1000) for x,y in h] for h in r.get('holes',[])])
    # Replace the previous top roof with a genuine occupied slab, clearing the stair hole.
    old={'upper-roof-slab','upper-ceiling','ivory-floating-roof-edge','timber-roof-soffit','thin-charcoal-roof-trim','atrium-stair-return'}
    # The shared G+1 renderer still emits the old gallery guards. Remove each
    # panel and its immediately following handrail before drawing the reviewed
    # boundaries; the old rail at y7.8 would block the new indoor approach.
    retained=[];skip_rail=False
    for node in k.nodes:
        if node['id'].startswith('gallery-glass-'):
            skip_rail=True;continue
        if skip_rail and node.get('role')=='railing':
            skip_rail=False;continue
        skip_rail=False
        if node['id'] not in old:retained.append(node)
    k.nodes[:]=retained
    for i,(a,c) in enumerate(b['planning']['upperPlan']['galleryGuards']):
        aa=tuple(v/1000 for v in a);cc=tuple(v/1000 for v in c)
        k.poly_mesh(LineString([aa,cc]).buffer(.012,cap_style=2),z1+.08,z1+1.08,
                    'railglass',1,'railing',f'internal-gallery-guard-{i}')
        k.beam((*aa,z1+1.10),(*cc,z1+1.10),.018,'frame',1,'railing')
    for i,r in enumerate(sp['floorPlate']):
        k.poly_mesh(p(r),z-.18,z-.014,'slab',2,'slab',f's2-slab-{i}')
        k.poly_mesh(p(r),z-.014,z,'ivory-marble-polished',2,'floor',f's2-floor-{i}')
        k.poly_mesh(p(r),z-.20,z-.18,'ceiling',1,'ceiling',f's2-soffit-{i}')
    for i,r in enumerate(sp['wallRegions']):k.poly_mesh(p(r),z,top,'wall',2,'wall',f's2-wall-{i}')
    # Roof slab and broad ivory fascia with timber soffit; stops short of the lightwell.
    roof=_shape(sp['hallRoof']);atrium=Polygon(sp['atriumOpening'])
    roof_envelope=roof.union(atrium)
    outer_over=roof_envelope.buffer(300,join_style=2).intersection(box(0,4425,7050,14780)).difference(Polygon(sp['lightwell']))
    over=outer_over.difference(atrium)
    def mm(poly):
        from shapely.affinity import scale
        return scale(poly,xfact=.001,yfact=.001,origin=(0,0))
    k.poly_mesh(mm(roof),top,top+.18,'roof',2,'roof','s2-hall-roof')
    k.poly_mesh(mm(roof),top-.025,top,'ceiling',2,'ceiling','s2-hall-ceiling')
    fascia=mm(over.difference(roof))
    k.poly_mesh(fascia,top-.08,top+.18,'wall',2,'fascia','s2-hall-fascia')
    k.poly_mesh(fascia,top-.095,top-.08,'teak-warm',2,'soffit','s2-hall-timber-soffit')
    # Conceptual support lines remain in structuralConcept metadata. Their
    # embedded concrete is represented by the enclosing masonry/slab envelope;
    # duplicate coplanar pier/beam faces would create dark render artifacts.
    # Service fall/drain points are expressed at the outer edge; waterproofing
    # design and outlet sizing remain a documented construction-design task.
    for x,y in [(11.30,13.90),(8.05,5.05)]:
        k.rect((x-.06,y-.06,z+.013,x+.06,y+.06,z+.018),'steel',2,'detail','s2-drain-'+str(x))

    # Continuous high-level band makes roof depth legible; a 300mm non-accessible roof upstand.
    edge=mm(outer_over.difference(outer_over.buffer(-140,join_style=2)))
    k.poly_mesh(edge,top+.18,top+.48,'wall',2,'parapet','s2-upper-roof-upstand')
    from .tirumala_5_rooflight import add_rooflight_and_solar
    roof_equipment=add_rooflight_and_solar(k,mats,b)
    k.roof_equipment=roof_equipment
    for op in (o for o in b['openings'] if o['floor']==2):
        ax,ay=[v/1000 for v in op['a']];bx,by=[v/1000 for v in op['b']]
        length=math.hypot(bx-ax,by-ay);ux,uy=(bx-ax)/length,(by-ay)/length;nx,ny=-uy,ux
        def span(a,c,d,e,lo,hi,mat,role,name):
            q=Polygon([(ax+ux*a+nx*d,ay+uy*a+ny*d),(ax+ux*c+nx*d,ay+uy*c+ny*d),
               (ax+ux*c+nx*e,ay+uy*c+ny*e),(ax+ux*a+nx*e,ay+uy*a+ny*e)])
            k.poly_mesh(q,z+lo,z+hi,mat,2,role,'op-'+op['id']+'-'+name,owner=op['id'])
        sill=op['sill']/1000;t=(op['sill']+op['height'])/1000
        if sill:span(0,length,-.075,.075,0,sill,'wall','wall','sill')
        span(0,length,-.075,.075,t,ROOM_HEIGHT/1000,'wall','wall','lintel')
        for a,c,lo,hi in [(0,.055,sill,t),(length-.055,length,sill,t),(0,length,t-.055,t)]:
            span(a,c,-.065,.065,lo,hi,'frame','frame','jamb-'+str(a)+'-'+str(lo))
        if sill:span(0,length,-.065,.065,sill,sill+.055,'frame','frame','bottom')
        motion=build_opening(k,op,b['planning']['canonicalPlan'],span)
        if op['id']=='s2-hall-garden':
            for node in k.nodes:
                if node.get('owner')==op['id'] and node['material']=='frosted':node['material']='icu-glass'
        for part in motion.get('parts',[]):
            if 'pivot' in part:part['pivot'][2]+=z
        if op['sill']==0:motion['initial']=1
        door_motion[op['id']]=motion;pose_initial_opening(k,motion)
    # Consistent stair risers, actual treads, landing, sloping concrete waist and handrails.
    def waist(name,xy0,xy1,width,lo,hi,floor=1,thickness=.18):
        # A 2mm inset at each edge keeps the concrete waist below the unchanged
        # tread/riser skins. Coincident side planes otherwise create dark
        # triangular interference where stepped bodies overlap the sloping waist.
        waist_width=width-.004
        a=xy0;c=xy1;dx,dy=c[0]-a[0],c[1]-a[1];ln=math.hypot(dx,dy);nx,ny=-dy/ln*waist_width/2,dx/ln*waist_width/2
        vv=[]
        for zz0,zz1 in [(lo-thickness,hi-thickness),(lo,hi)]:
            vv.extend([[a[0]+nx,a[1]+ny,zz0],[a[0]-nx,a[1]-ny,zz0],
                       [c[0]-nx,c[1]-ny,zz1],[c[0]+nx,c[1]+ny,zz1]])
        mesh=trimesh.Trimesh(vv,[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],
             [1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]],process=True)
        k.node(k.asset(mesh),'wall',floor=floor,role='stair',name=name)
    # Existing ground stair receives a continuous concrete soffit under the
    # unchanged treads. At the pantry centre this leaves over2.4m headroom.
    waist('g-south-waist',(1.525,5.55),(1.25,5.55),1.1,0,.35,floor=0,thickness=.15)
    waist('g-west-waist',(.7,6.15),(.7,7.8),1.1,.35,1.575,floor=0,thickness=.15)
    waist('g-north-waist',(1.25,8.35),(3.45,8.35),1.1,1.575,3.15,floor=0,thickness=.15)
    waist('s2-south-waist',(1.525,5.55),(1.25,5.55),1.1,z1,z1+.35)
    waist('s2-west-waist',(.7,6.15),(.7,7.8),1.1,z1+.35,z1+1.575)
    waist('s2-north-waist',(1.25,8.35),(3.45,8.35),1.1,z1+1.575,z1+3.15)
    for step in sp['stairs']:
        x0,y0,x1,y1=[v/1000 for v in step['bounds']];zz=step['top']/1000
        # Contiguous tread bodies meet without duplicated coplanar side faces.
        k.rect((x0,y0,zz-.19,x1,y1,zz-.025),'wall',1,'stair',step['id']+'-body')
        k.rect((x0,y0,zz-.025,x1,y1,zz),'limestone',1,'stair',step['id']+'-tread')
    # Guard only exposed sides; never cap a starter, turn or arrival route.
    railpaths=[[(1.525,6.10,z1),(1.25,6.10,z1+.35)],
               [(1.25,6.15,z1+.35),(1.25,7.80,z1+1.575)],
               [(1.25,7.80,z1+1.575),(3.45,7.80,z1+3.15)],
               [(3.45,7.80,z1+3.15),(4.55,7.80,z1+3.15)],
               [(4.55,7.80,z1+3.15),(5.15,7.80,z)],
               [(3.45,8.90,z1+3.15),(4.55,8.90,z1+3.15)],
               [(4.55,8.90,z1+3.15),(5.15,8.90,z)]]
    for i,(a,c) in enumerate(railpaths):
        k.beam((a[0],a[1],a[2]+1.05),(c[0],c[1],c[2]+1.05),.035,'teak-warm',1,'railing')
        count=max(2,math.ceil(math.dist(a[:2],c[:2])/.12))
        for j in range(count+1):
            t=j/count;x=a[0]+(c[0]-a[0])*t;y=a[1]+(c[1]-a[1])*t;zz=a[2]+(c[2]-a[2])*t
            k.beam((x,y,zz+.02),(x,y,zz+1.02),.012,'frame',1,'railing')
    # Opaque perimeter / lightwell parapets; inset on supported slab edges.
    plate=mm(_shape(sp['floorPlate']))
    enclosed_shell=mm(box(*HALL).buffer(150,join_style=2).union(_shape(sp['headhouseRegions'])))
    terrace=mm(_shape(next(r for r in sp['rooms'] if r['id']=='s2-terrace')['regions']))
    k.poly_mesh(terrace,z+.001,z+.012,'terrace-stone',2,'terrace','s2-terrace-finish')
    boundary=plate.difference(plate.buffer(-.12,join_style=2)).difference(enclosed_shell.buffer(.05))
    k.poly_mesh(boundary,z,z+1.10,'wall',2,'parapet','s2-opaque-terrace-parapet')
    k.poly_mesh(boundary.buffer(.015,join_style=2),z+1.10,z+1.14,'limestone',2,'coping','s2-terrace-coping')
    # Guard the exposed shaft edges and close the unusably narrow ledge near
    # the starter. The actual x5.15 arrival remains open to the enclosed lobby.
    for i,(a,c) in enumerate(sp['landingGuards']):
        aa=tuple(v/1000 for v in a);cc=tuple(v/1000 for v in c)
        k.poly_mesh(LineString([aa,cc]).buffer(.012,cap_style=2),z+.08,z+1.08,
                    'railglass',2,'railing',f's2-landing-guard-{i}')
        k.beam((*aa,z+1.10),(*cc,z+1.10),.018,'frame',2,'railing')
    # Furnish the hall sparingly: full size seating, compact library, generous central routes.
    k.rb((2.15,13.45,z+.37),(2.5,.9,.60),'fabric',2,'furniture',.11,owner='s2-sofa')
    k.rb((2.15,13.82,z+.79),(2.5,.16,.65),'linen',2,'furniture',.06)
    for xx in [1.0,3.3]:k.rb((xx,13.45,z+.65),(.20,.92,.44),'linen',2,'furniture',.07)
    k.rb((2.25,12.025,z+.41),(1.1,.65,.09),'limestone',2,'furniture',.06,owner='s2-coffee')
    k.rect((1.90,11.80,z+.02,2.60,12.25,z+.37),'teak-warm',2,'furniture','s2-table-base')
    for xx in [1.0,3.4]:
        k.rb((xx,11.6,z+.4),(.8,.8,.62),'linen',2,'furniture',.12)
        k.rb((xx,11.96,z+.75),(.8,.14,.62),'fabric',2,'furniture',.04)
    k.rect((1.3,9.075,z+.16,3.6,9.325,z+.47),'teak-warm',2,'furniture','s2-media-console')
    k.rect((1.65,9.05,z+.88,3.25,9.08,z+1.78),'blackglass',2,'detail','s2-tv')
    for zz in [.18,.75,1.35,1.95]:k.rect((.45,12.5,z+zz,.85,14.30,z+zz+.055),'oak-warm',2,'furniture','s2-library-'+str(zz))
    k.rect((.45,12.50,z+.18,.52,14.30,z+2.05),'oak-warm',2,'furniture','s2-library-back')
    # Roof garden uses shallow planting and freely draining mineral beds, not deep soil.
    for x0,y0,x1,y1 in [(5.85,14.00,10.8,14.30),(10.8,10.0,11.2,13.5),(6.8,5.10,7.9,5.50)]:
        k.rect((x0,y0,z,x1,y1,z+.42),'wall',2,'landscape',f's2-planter-{x0}-{y0}')
        k.rect((x0+.06,y0+.06,z+.42,x1-.06,y1-.06,z+.44),'soil',2,'landscape')
        n=max(1,int(max(x1-x0,y1-y0)/.7))
        for i in range(n):
            t=(i+.5)/n;k.plant(x0+.5*(x1-x0) if y1-y0>x1-x0 else x0+t*(x1-x0),
                  y0+t*(y1-y0) if y1-y0>x1-x0 else y0+.5*(y1-y0),z+.44,'grass_ornamental',height=.30 if y0==14.00 else .55,f=2)
    lawn=box(8.0,10.2,10.6,12.55)
    k.poly_mesh(lawn,z+.013,z+.045,'grass',2,'lawn','s2-garden-turf')
    lawns.append(dict(polygon=ring(lawn),holes=[],z=z+.046,heightScale=.40))
    for x,y in [(10.8,9.35)]:k.plant(x,y,z,'strelitzia',height=1.2,f=2,pot=(.24,.46,'ceramic-pot'))
    k.rb((7.75,13.35,z+.40),(2.5,.9,.62),'fabric',2,'furniture',.10,owner='s2-terrace-sofa')
    k.rb((7.75,13.72,z+.75),(2.5,.15,.58),'linen',2,'furniture',.06)
    k.rb((7.75,12.10,z+.38),(1.1,.65,.08),'limestone',2,'furniture',.035)
    for x,y in [(9.30,12.50)]:k.rb((x,y,z+.42),(.7,.75,.62),'linen',2,'furniture',.09)
    # Light pergola frame is explicitly supported at four corners, not floating.
    for x,y in [(6.05,12.05),(9.75,12.05),(6.05,14.20),(9.75,14.20)]:
        k.rect((x-.055,y-.055,z,x+.055,y+.055,z+2.65),'frame',2,'pergola')
    for y in [12.05,14.20]:k.rect((5.95,y-.055,z+2.60,9.85,y+.055,z+2.74),'wall',2,'pergola')
    for i in range(16):
        x=6.0+i*.25;k.rect((x,11.95,z+2.72,x+.06,14.30,z+2.82),'teak-warm',2,'pergola')
    for x,y in [(1.8,10),(4.6,10),(1.8,13),(4.6,13)]:
        k.cylinder((x,y,top-.04),.065,.02,'lamp',2,'fixture');k.light((x,y,top-.15),28,color='#ffe6ce',kind='s2-hall')
    for x,y in [(4.7,5.45),(5.8,7.15),(.7,7.75)]:
        k.cylinder((x,y,top-.04),.055,.02,'lamp',2,'fixture');k.light((x,y,top-.15),20,color='#ffe6ce',kind='s2-stair')
    for x,y in [(6.3,12.3),(9.5,12.3)]:k.light((x,y,z+2.45),16,color='#ffe6bf',kind='s2-pergola')
    _trim_embedded_slab_faces(k,b)
    return []


def _trim_embedded_slab_faces(k,b):
    """Expose the wall/slab union without duplicate vertical coplanar skins.

    Only hidden side triangles are omitted; floor top triangles, canonical
    footprints, stair/lightwell openings and walkable surfaces are untouched.
    """
    import numpy as np
    import trimesh
    from .scene import transformation
    from shapely.affinity import scale
    for node in k.nodes:
        if not node['id'].startswith(('upper-slab-','upper-floor-','s2-slab-','s2-floor-')):continue
        lower=node['floor']-1
        walls=[w for w in b['walls'] if w['floor']==lower]
        if not walls:continue
        asset=k.assets[node['asset']];local=np.asarray(asset['vertices'],float);matrix=transformation(node)
        vertices=local@matrix[:3,:3].T+matrix[:3,3];keep=[];removed=0
        for face in asset['faces']:
            v=vertices[face]
            if np.ptp(v[:,2])<.001:
                keep.append(face);continue
            normal=np.cross(v[1]-v[0],v[2]-v[0])
            if abs(normal[2])>1e-8:
                keep.append(face);continue
            projected=LineString(v[:,:2]).convex_hull
            covering=[]
            for wall in walls:
                base=lower*H/1000
                if v[:,2].min()>=base-.00001 and v[:,2].max()<=base+wall['height']/1000+.00001:
                    covering.append(scale(Polygon(wall['polygon'],wall.get('holes',[])),xfact=.001,yfact=.001,origin=(0,0)))
            hidden=covering and unary_union(covering).buffer(.00001).covers(projected)
            if hidden:removed+=1
            else:keep.append(face)
        if removed:
            node['asset']=k.asset(trimesh.Trimesh(vertices=local,faces=keep,process=False))
            node['embeddedSideFacesRemoved']=removed
            # The walls close the omitted side skins in the assembled building.
            # Preserve the unchanged horizontal walk surface as a collider even
            # though the isolated render asset is no longer watertight.
            node['collisionEnvelope']='wall-integrated-slab'


def cameras(b):
    z=LEVEL/1000
    defs={'second_hall':('Second floor · family hall',[4.4,10.75,z+1.63],[2.2,12.4,z+1.35],66),
          'second_terrace':('Second floor · open garden terrace',[10.0,9.3,z+1.63],[7.5,13.1,z+1.1],66),
          'second_stair_arrival':('Second floor · stair arrival',[5.8,8.35,z+1.63],[3.5,8.35,z-.5],66),
          'first_stair_up':('First floor · indoor bridge and stacked stairs',[5.7,5.475,H/1000+1.63],[1.55,5.475,H/1000+1.4],64),
          'ground_skylight':('Ground floor · view through atrium to rooflight',[3.7,7.6,1.63],[3.35,6.96,10.85],70),
          'second_atrium':('Second floor · enclosed east landing and skylight',[5.8,5.45,z+1.63],[2.8,7.0,9.4],70),
          'roof_solar':('Highest roof · skylight and compact solar array',[16,-5,20],[3.8,9.0,9.0],50)}
    out={}
    for ident,(label,pos,target,fov) in defs.items():
        dx,dy,dz=[target[i]-pos[i] for i in range(3)]
        floor=0 if ident=='ground_skylight' else 1 if ident=='first_stair_up' else 2
        out[ident]=dict(id=ident,label=label,position=pos,target=target,fov=fov,floor=floor,
            enter_walk=ident!='roof_solar',eye_height_above_ffl_m=1.63,walker=dict(position=pos[:],yaw_rad=math.atan2(-dx,dy),pitch_rad=math.atan2(dz,math.hypot(dx,dy))))
    return out


def finalize_scene(scene,b):
    # Plan A abuts the south boundary. Keep the boundary's exterior at x=0,
    # while recessing its interior skin 2mm into its own thickness; otherwise
    # that skin coincides with the house's x=.15 internal wall and renders as
    # a dark band indoors. This changes neither plot nor room dimensions.
    for node in scene['nodes']:
        if node['id']=='boundary-south' and not node.get('interiorSkinInsetMm'):
            node['scale'][0]-=.002
            node['position'][0]-=.001
            node['interiorSkinInsetMm']=2
    scene['storeys']=3
    scene['bounds'][5]=LEVEL/1000+ROOM_HEIGHT/1000+.80
    scene['walk']['floors'].append(dict(floor=2,position=[5.8,8.35,LEVEL/1000],yaw_deg=0))
    scene['cameras'].update(cameras(b))
    scene['g2Addition']={'revision':REVISION,'stairRiserMm':RISE,'stairWidthMm':1100,
         'secondFloorMm':LEVEL,'hallClearMm':[HALL[2]-HALL[0],HALL[3]-HALL[1]],
         'stairRoute':'First gallery → east-edge indoor bridge → South / West / North stacked stair → enclosed second landing.',
         'secondStairHeadroomMm':b['planning']['secondPlan']['minimumAnalyticGroundStairHeadroomMm'],
         'firstDoubleHeightClearMm':[5050,1725],
         'continuousAtriumClearMm':[3325,1725],
         'skylight':deepcopy(b['planning']['secondPlan']['skylight']),
         'solarModules':4,'solarRoof':'Highest roof above second-floor hall; no extra storey',
         'guestBedroomClearMm':[GUEST[2]-GUEST[0],GUEST[3]-GUEST[1]],
         'guestBedroomFrontClearMm':GUEST[2]-GUEST_EXTENSION[0],
         'guestBedroomExtensionMm':GUEST_EXTENSION[:],
         'stairRiserHeightsMm':b['planning']['secondPlan']['riserHeightsMm'],
         'bridgeClearWidthMm':1100,
         'structuralStatus':b['planning']['secondPlan']['structuralConcept']['status'],
         'pantryClearance':deepcopy(b['planning']['secondPlan']['pantryClearance'])}


def second_plan_elements(b):
    from .drawings import P,T,L,DIM
    from .tirumala_p11_p12 import _mm_to_ft_in
    sp=b['planning']['secondPlan'];items=[P(b['plot'],fill='#faf8f2',stroke='#bbb',width=.2,layer='A-SITE')]
    for r in sp['rooms']:
        for reg in r['regions']:items.append(P(reg['polygon'],fill='#f3e9d8' if r['kind']=='hall' else '#deead8',stroke='#c4c8ba',width=.2,layer='A-AREA'))
    for reg in sp['wallRegions']:items.append(P(reg['polygon'],fill='#394942',stroke='none',width=.1,layer='A-WALL'))
    for o in (o for o in b['openings'] if o['floor']==2):items.append(L(o['a'],o['b'],stroke='#3e8e9e' if o['sill'] else '#9c6c42',width=.6,layer='A-DOOR'))
    for st in sp['stairs']:items.append(P(ring(box(*st['bounds'])),fill='#f4f0e8',stroke='#889087',width=.15,layer='A-STAIR'))
    for a,c in [([5500,8350],[700,8350]),([700,8350],[700,5550]),([700,5550],[1750,5550])]:
        items.append(L(a,c,stroke='#38584a',width=.5,layer='A-STAIR'))
    for a,c in sp['landingGuards']:items.append(L(a,c,stroke='#38584a',width=.7,layer='A-GUARD'))
    items.append(P(sp['atriumOpening'],fill='#edf5f7',stroke='#397d90',width=.5,layer='A-VOID'))
    items.append(T(3350,7100,'OPEN TO GROUND BELOW',140,layer='A-ANNO'))
    items.append(T(3350,6800,'ROOFLIGHT ABOVE',140,layer='A-ANNO'))
    items.append(T(2700,8550,'DOWN TO FIRST FLOOR',150,layer='A-ANNO'))
    items.append(T(3700,5600,'ENCLOSED EAST LANDING',140,layer='A-ANNO'))
    for f in sp['furniture']:items.append(P(ring(box(*f['bounds'])),fill='#c6b59d',stroke='#8a8276',width=.15,layer='A-FURN'))
    items.append(T(2750,10600,'Second-floor family hall',210,layer='A-ANNO'))
    items.append(T(2750,10150,f'{_mm_to_ft_in(HALL[2]-HALL[0])} × {_mm_to_ft_in(HALL[3]-HALL[1])}',180,layer='A-ANNO'))
    items.append(T(9000,10000,'Open roof garden terrace',210,layer='A-ANNO'))
    items.append(DIM([0,15240],[12192,15240],'x',15550));items.append(DIM([0,0],[0,15240],'y',-300))
    return items,(-850,-450,12800,15900)


def second_svg(b):
    from .tirumala_p11_p12 import _mm_to_ft_in
    sp=b['planning']['secondPlan'];s=.066;left=84;top=105;depth=15240
    tx=lambda x:left+x*s;ty=lambda y:top+(depth-y)*s
    pts=lambda r:' '.join(f'{tx(x):.2f},{ty(y):.2f}' for x,y in r)
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="980" height="1450" viewBox="0 0 980 1450">',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M10 1 L0 5 L10 9" fill="none" stroke="#657168"/></marker></defs>',
         '<rect width="980" height="1450" fill="#faf9f5"/><g font-family="Arial,sans-serif" fill="#253c34">',
         '<text x="55" y="40" font-size="25" font-weight="700">Tirumala 5 · Second floor / roof garden</text>',
         '<text x="55" y="66" font-size="14">40 × 50 ft plot · West ↑ · North → · Internal stair and enclosed landing</text>',
         f'<rect x="{tx(0)}" y="{ty(15240)}" width="{12192*s}" height="{15240*s}" fill="#f1efe7" stroke="#c7c4b8"/>']
    def text(x,y,t,size=13,weight=400):out.append(f'<text x="{tx(x)}" y="{ty(y)}" text-anchor="middle" font-size="{size}" font-weight="{weight}">{html.escape(t)}</text>')
    def poly(p,fill,stroke='#b5b9ad'):out.append(f'<polygon points="{pts(p)}" fill="{fill}" stroke="{stroke}"/>')
    def dim(x0,y0,x1,y1,t):
        a,c,d,e=tx(x0),ty(y0),tx(x1),ty(y1);ang=-90 if x0==x1 else 0
        out.append(f'<line x1="{a}" y1="{c}" x2="{d}" y2="{e}" stroke="#657168" marker-start="url(#a)" marker-end="url(#a)"/>')
        out.append(f'<text x="{(a+d)/2}" y="{(c+e)/2-5}" transform="rotate({ang} {(a+d)/2} {(c+e)/2})" text-anchor="middle" font-size="12" stroke="#faf9f5" stroke-width="5" paint-order="stroke">{html.escape(t)}</text>')
    for r in sp['rooms']:
        for reg in r['regions']:poly(reg['polygon'],'#f3e9d8' if r['kind']=='hall' else '#dce8d3')
    poly(sp['lightwell'],'#fff');text(6380,11000,'LIGHTWELL',11)
    for reg in sp['stairVoid']:poly(reg['polygon'],'#fff')
    for step in sp['stairs']:poly(ring(box(*step['bounds'])),'#f4f0e8','#aaa99d')
    for reg in sp['wallRegions']:poly(reg['polygon'],'#394942','#394942')
    poly(sp['atriumOpening'],'#edf5f7','#397d90')
    for f in sp['furniture']:poly(ring(box(*f['bounds'])),'#c6b59d','#8d8578')
    for o in (o for o in b['openings'] if o['floor']==2):out.append(f'<line x1="{tx(o["a"][0])}" y1="{ty(o["a"][1])}" x2="{tx(o["b"][0])}" y2="{ty(o["b"][1])}" stroke="{"#57919c" if o["sill"] else "#aa794b"}" stroke-width="4"/>')
    text(2800,10320,'FAMILY HALL',16,700)
    text(2800,9930,f'{_mm_to_ft_in(HALL[2]-HALL[0])} × {_mm_to_ft_in(HALL[3]-HALL[1])}',14)
    text(2800,9570,f'{(HALL[2]-HALL[0])*(HALL[3]-HALL[1])/92903.04:.0f} sq ft · clear',12)
    text(9200,10000,'OPEN ROOF GARDEN',15,700)
    area=next(r['area_m2'] for r in sp['rooms'] if r['id']=='s2-terrace')/.09290304
    text(9200,9610,f'{area:.0f} sq ft · irregular terrace',12)
    text(3700,5500,'ENCLOSED EAST LANDING',12,700)
    text(2700,8650,'DOWN TO FIRST',10,700)
    text(3337,7150,'OPEN TO GROUND',11,700)
    text(3337,6900,'Rooflight above',11)
    text(3337,6600,'10′11″ × 5′8″',12,700)
    text(3337,6350,'61.7 sq ft clear aperture',10)
    for a,c in sp['landingGuards']:
        out.append(f'<line x1="{tx(a[0])}" y1="{ty(a[1])}" x2="{tx(c[0])}" y2="{ty(c[1])}" stroke="#38584a" stroke-width="3"/>')
    down=[[5500,8350],[700,8350],[700,5550],[1750,5550]]
    out.append(f'<polyline points="{pts(down)}" fill="none" stroke="#38584a" stroke-width="1.6"/>')
    out.append(f'<path d="M {tx(1590)} {ty(5650)} L {tx(1750)} {ty(5550)} L {tx(1590)} {ty(5450)}" fill="none" stroke="#38584a" stroke-width="1.6"/>')
    poly(ring(box(8000,10200,10600,12550)),'#8aa276')
    text(9300,11380,'Shallow garden',12)
    dim(150,14700,HALL[2],14700,_mm_to_ft_in(HALL[2]-HALL[0]));dim(5150,9050,5150,14328,_mm_to_ft_in(5278))
    dim(0,15600,12192,15600,'40 ft');dim(-450,0,-450,15240,'50 ft')
    text(6100,-450,'EAST · entrance side below',14,700)
    notes=['New second floor at +23 ft ¼ in; hall clear height 10 ft 11⅞ in.',
           'Same lower stair footprint: 18 risers of 6⅞ in plus 2 arrival risers of 7 in.',
           'Indoor bridge reaches the South → West → North stair; 3 ft 7¼ in clear width.',
           'Opaque parapets, shallow planters, pergola and clear paved walking routes.',
           'Enclosed landing gains 48.8 sq ft; aligned rooflight is visible from ground floor.',
           'Concept model: foundations, member sizes, wind/seismic and garden loads need engineering.']
    for i,t in enumerate(notes):out.append(f'<text x="55" y="{1200+i*28}" font-size="13">{html.escape(t)}</text>')
    out.append('</g></svg>');return ''.join(out)


def validate_addition(b):
    """Geometry and circulation checks; not a structural engineering sign-off."""
    sp=b['planning'].get('secondPlan',{})
    if not sp:return [dict(id='g2_addition_present',category='geometry',status='fail',detail='Second-floor plan missing.')]
    rooms={r['id']:_shape(r['regions']) for r in sp['rooms']}
    plate=_shape(sp['floorPlate']);shaft=_shape(sp['stairVoid']);plot=Polygon(b['plot'])
    fit=all(p.is_valid and plot.covers(p) for p in rooms.values())
    no_overlap=rooms['s2-hall'].intersection(rooms['s2-terrace']).area<1
    treads=[st for st in sp['stairs'] if not st.get('landing')]
    rises=[treads[0]['top']-H]+[c['top']-a['top'] for a,c in zip(treads,treads[1:])]
    flight_ok=len(treads)==20 and all(abs(r-e)<.001 for r,e in zip(rises,[175]*18+[179]*2)) and abs(treads[-1]['top']-LEVEL)<.001
    # Congruent upper/lower flights: the leading-edge difference subtracts
    # one 175 mm rise and the 180 mm waist from the 3508 mm floor spacing.
    minimum_lower_stair_headroom_mm=sp['minimumAnalyticGroundStairHeadroomMm']
    up=b['planning']['upperPlan']
    gallery=_shape(next(r for r in up['rooms'] if r['id']=='u-gallery')['regions'])
    route=LineString(up['circulationPaths']['arrival_to_stair']).buffer(550,cap_style=2,join_style=2)
    indoor_route=gallery.buffer(.01).covers(route)
    no_outside_entry=not any(o['id']=='s2-stair-entry' for o in b['openings'])
    entry=next((o for o in b['openings'] if o['id']=='s2-hall-entry'),None)
    arrival=box(*sp['stairArrival'])
    hall_entry=LineString(sp['circulationPaths']['stairs_to_hall']).buffer(350,cap_style=2)
    return [
      dict(id='g2_hall_terrace_fit',category='geometry',status='pass' if fit and no_overlap else 'fail',
           detail='Second hall and open terrace fit the retained 40 × 50 ft plot without overlapping rooms.'),
      dict(id='g2_stair_risers_and_landings',category='circulation',status='pass' if flight_ok and entry and plate.covers(arrival) and plate.covers(hall_entry) else 'fail',
           detail='Ground stair footprint copied exactly: 18 × 175 mm risers plus 2 × 179 mm arrival risers, 1100 mm wide, reaching +7016 mm.'),
      dict(id='g2_indoor_stair_route',category='circulation',status='pass' if indoor_route and no_outside_entry and entry and entry['connects']==['s2-indoor-landing','s2-hall'] else 'fail',
           detail='1100 mm clear indoor east-edge bridge leads to the stacked South / West / North stair; enclosed top landing connects hall and terrace.'),
      dict(id='g2_stair_opening_and_headroom',category='circulation',status='pass' if plate.intersection(shaft).area<1 and minimum_lower_stair_headroom_mm>=2100 else 'fail',
           detail=f'Second slab clears stair void. Analytic minimum above retained ground stair under new waist: {minimum_lower_stair_headroom_mm:.0f}mm.'),
      dict(id='g2_lightwell_retained',category='geometry',status='pass' if plate.intersection(Polygon(sp['lightwell']).buffer(-1)).area<1 else 'fail',
           detail='Lightwell remains open to sky through the second-floor slab.'),
    ]


def first_plan_elements(b):
    from .tirumala_luxury import upper_plan_elements
    from .drawings import P,T,L
    items,bounds=upper_plan_elements(b)
    items=[i for i in items if i.get('text') not in
           ('STAIR ↑ + 2 arrival steps','OPEN TO LIVING BELOW','Double height · 23 ft overall')]
    sp=b['planning']['secondPlan'];up=b['planning']['upperPlan']
    for st in sp['stairs']:
        items.append(P(ring(box(*st['bounds'])),fill='#e9e2d6',stroke='#889087',width=.15,layer='A-STAIR'))
    for a,c in [([1800,5550],[700,5550]),([700,5550],[700,8350]),([700,8350],[5500,8350])]:
        items.append(L(a,c,stroke='#38584a',width=.5,layer='A-STAIR'))
    for a,c in up['galleryGuards']:items.append(L(a,c,stroke='#38584a',width=.7,layer='A-GUARD'))
    items.append(T(2750,8500,'UP TO SECOND · 20 RISERS',145,layer='A-ANNO'))
    items.append(T(5450,8050,'Arrival from ground',115,layer='A-ANNO'))
    items.append(T(4000,5500,'INDOOR BRIDGE · 3 ft 7¼ in CLEAR',140,layer='A-ANNO'))
    items.append(T(3700,7050,'OPEN TO LIVING BELOW',210,layer='A-ANNO'))
    items.append(T(3700,6700,'94 sq ft clear opening',170,layer='A-ANNO'))
    return items,bounds


def first_svg(b):
    """Approved bedroom extension and continuous indoor stair circulation."""
    from .tirumala_luxury import upper_svg
    out=upper_svg(b)
    out=out.replace('Stairs ↑','').replace('>+2<','>↓ GF<')
    out=re.sub(r'<text[^>]*>(OPEN TO LIVING / DINING|23 ft double-height space)</text>','',out)
    out=out.replace('Existing 18 stair risers retained + two 179 mm arrival risers to +3.508 m.',
                    'Ground stair retained; same footprint above reached by an indoor east-edge bridge.')
    out=out.replace('Gallery overlooks living. Open terrace is on this same first-floor level.',
                    'Guest room extends 1 ft south at front; 3 ft rear gallery and large terrace retained.')
    out=out.replace('Office + guest bedroom; shared bath accessed from the gallery.',
                    'Guest width: 11 ft 1⅜ in at front, 10 ft 1⅜ in at rear; area 177 sq ft.')
    sp=b['planning']['secondPlan'];up=b['planning']['upperPlan'];s=.066;left=84;top=105;depth=15240
    tx=lambda x:left+x*s;ty=lambda y:top+(depth-y)*s
    pts=lambda p:' '.join(f'{tx(x):.2f},{ty(y):.2f}' for x,y in p)
    extra=['<defs><marker id="stair-up-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 1 L9 5 L0 9" fill="none" stroke="#38584a"/></marker></defs><g font-family="Arial,sans-serif" fill="#253c34">']
    for st in sp['stairs']:
        extra.append(f'<polygon points="{pts(ring(box(*st["bounds"])))}" fill="#e9e2d6" stroke="#a7ab9c" stroke-width=".7"/>')
    up_arrow=[[1800,5550],[700,5550],[700,8350],[5500,8350]]
    extra.append(f'<polyline points="{pts(up_arrow)}" fill="none" stroke="#38584a" stroke-width="2" marker-end="url(#stair-up-arrow)"/>')
    for a,c in up['galleryGuards']:
        extra.append(f'<line x1="{tx(a[0])}" y1="{ty(a[1])}" x2="{tx(c[0])}" y2="{ty(c[1])}" stroke="#38584a" stroke-width="2"/>')
    for x,y,t,sz in [(2700,8630,'UP TO SECOND · 20 RISERS',10),
                     (4000,5550,'Indoor bridge · 3 ft 7¼ in clear',11),(5600,8100,'From ground',10),
                     (3700,7050,'OPEN TO LIVING / DINING',14),(3700,6700,'94 sq ft clear opening',13)]:
        extra.append(f'<text x="{tx(x)}" y="{ty(y)}" text-anchor="middle" font-size="{sz}" font-weight="700" stroke="#faf9f5" stroke-width="3" paint-order="stroke">{t}</text>')
    extra.append('</g>')
    return out.replace('</g></svg>','</g>'+''.join(extra)+'</svg>')


def roof_svg(b):
    """Dimensioned highest-roof equipment plan, authored from the same geometry."""
    from .tirumala_p11_p12 import _mm_to_ft_in
    sp=b['planning']['secondPlan'];s=.066;left=84;top=105
    tx=lambda x:left+x*s;ty=lambda y:top+(15240-y)*s
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="980" height="1320" viewBox="0 0 980 1320">',
      '<rect width="980" height="1320" fill="#faf9f5"/><g font-family="Arial,sans-serif" fill="#253c34">',
      '<text x="55" y="40" font-size="25" font-weight="700">Tirumala 5 · Highest roof / solar and rooflight</text>',
      '<text x="55" y="66" font-size="14">Ground + first + second floor · West ↑ · North → · 40 × 50 ft plot</text>']
    def poly(points,fill,stroke='#8b978d'):
        pts=' '.join(f'{tx(x):.2f},{ty(y):.2f}' for x,y in points)
        out.append(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}"/>')
    def text(x,y,t,size=13):
        out.append(f'<text x="{tx(x)}" y="{ty(y)}" text-anchor="middle" font-size="{size}">{html.escape(t)}</text>')
    poly(b['plot'],'#f5f2e9')
    for reg in sp['roofOutline']:poly(reg['polygon'],'#e1e8d8')
    for reg in sp['hallRoof']:poly(reg['polygon'],'#faf8f0')
    poly(sp['lightwell'],'#fff')
    text(6300,11000,'Lightwell',11)
    poly(sp['atriumOpening'],'#b9dbe2','#397d90')
    for i in (1,2):
        x=ATRIUM[0]+(ATRIUM[2]-ATRIUM[0])*i/3
        poly(ring(box(x-18,ATRIUM[1],x+18,ATRIUM[3])),'#3b4f4b')
    text(3337,7450,'GLAZED ROOFLIGHT',12)
    text(3337,7020,'10′11″ × 5′8″',14)
    text(3337,6610,'View to ground below',11)
    for row in range(2):
        for col in range(2):
            x=1150+1230*col;y=10000+1860*row
            poly(ring(box(x,y,x+1130,y+1760)),'#243b51','#526875')
            for r in range(1,10):
                out.append(f'<line x1="{tx(x)}" y1="{ty(y+r*176)}" x2="{tx(x+1130)}" y2="{ty(y+r*176)}" stroke="#718497" stroke-width=".5"/>')
    text(2950,13950,'4 solar modules · face south',13)
    text(4450,11900,'Clear service path',11)
    text(2800,9450,'On roof above family hall',12)
    text(9000,9700,'OPEN TERRACE BELOW',14)
    text(9000,9250,'477 sq ft',13)
    text(6100,-400,'EAST · entrance side',14)
    for i,line in enumerate([
        'Rooflight slopes 3° east; raised curb, framed glass and external drainage channel.',
        'Solar array footprint: 7′9″ × 11′10½″. Clear east service approach: about 3′1⅜″.',
        'No added storey. Solar panels sit on the highest roof above the second-floor hall.',
        'Concept model: structural trimmers, glass, waterproofing and solar anchorage require engineering.'
    ]):out.append(f'<text x="55" y="{1190+i*28}" font-size="13">{html.escape(line)}</text>')
    out.append('</g></svg>')
    return ''.join(out)
