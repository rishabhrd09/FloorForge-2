"""Build the private garden verandah house in FloorForge's native custom-plan format."""
import json
import shutil
import sys
import tempfile
from pathlib import Path

from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from floorforge.pipeline import run
from floorforge.tirumala_p11_p12 import _browser_numbers
from floorforge.spaces import SPACE_REGISTRY

GALLERY = ROOT / 'examples/gallery'
DEST = GALLERY / 'tirumala-6'
FT = 304.8
WALL = 120
H = 3508
# One foot of reallocation plus the partition allowance for a full 14-foot worktop.
STAIR_WEST_MM = FT + WALL

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def local(x, y):
    return (round((40-y)*FT, 3), round((50-x)*FT, 3))

def project():
    source = json.loads((DEST/'ground-reference.json').read_text())
    floors = [dict(id=f'floor-{floor}', rooms=[], walls=[], openings=[]) for floor in range(3)]
    nominal = {}
    def room(f, ident, name, kind, shape, **options):
        footprint = Polygon([local(*p) for p in shape.exterior.coords])
        # The approved drawing dimensions include walls. Place outer faces on
        # the plot limits, and share a single wall at each interior boundary.
        enclosed = SPACE_REGISTRY[kind]['enclosed']
        domain = footprint.intersection(box(60,60,12192-60,15240-60)) if enclosed else footprint
        if ident=='drawing':
            # Set out the four-foot lawn from the finished outside face.
            domain=domain.intersection(box(0,4*FT+WALL/2,12192,15240))
        clear = domain.buffer(-60,join_style=2) if enclosed else domain
        vertices = [[round(x,3),round(y,3)] for x,y in list(clear.exterior.coords)[:-1]]
        record = dict(id=ident,name=name,kind=kind,polygon=vertices,**options)
        floors[f]['rooms'].append(record)
        nominal[ident] = footprint
        return record
    def opening(f, name, host, a, b, kind):
        record = next(r for r in floors[f]['rooms'] if r['id']==host)
        poly = Polygon(record['polygon'])
        endpoints = sorted((local(*a),local(*b)))
        midpoint = LineString(endpoints).centroid
        horizontal = endpoints[0][1]==endpoints[1][1]
        edges = [(i,LineString([p,q])) for i,(p,q) in enumerate(zip(poly.exterior.coords,list(poly.exterior.coords)[1:])) if (p[1]==q[1])==horizontal]
        index,line = min(edges,key=lambda item:item[1].distance(midpoint))
        start,end = line.coords
        dx,dy=end[0]-start[0],end[1]-start[1]
        sign=1 if poly.exterior.is_ccw else -1
        side=('right' if dy*sign>0 else 'left') if dy else ('front' if dx*sign>0 else 'rear')
        axis=0 if horizontal else 1
        lo=max(min(start[axis],end[axis])+20,endpoints[0][axis])
        hi=min(max(start[axis],end[axis])-20,endpoints[1][axis])
        spec=dict(id=name,roomId=host,side=side,edgeIndex=index,kind=kind,offset=round(lo-min(start[axis],end[axis]),3),width=round(hi-lo,3),sill=750 if kind=='window' else 0,height=1650 if kind=='window' else 2250,hinge='start')
        if kind=='glazed':spec.update(sliding=True,slidingPanels=2)
        floors[f]['openings'].append(spec)
        return spec
    ids=dict(C='caregiver',G='garden',V='verandah',I='icu',D='drawing',B='care-bath',A='master-bath',M='master',E='east-porch',P='car-porch',U='wash',K='kitchen',L='living',X='lawn')
    kinds=dict(C='bedroom',G='courtyard',V='veranda',I='care-room',D='drawing-room',B='bathroom',A='bathroom',M='bedroom',E='outer-lobby',P='outer-lobby',U='drying-yard',K='kitchen',L='living',X='courtyard')
    shapes={r['id']:Polygon(r['poly']) for r in source['rooms']}
    # Allow 2.4 m clear for the caregiver's bed between finished walls.
    wardrobe_trim=shapes['R'].intersection(box(20.60-STAIR_WEST_MM/FT,31,21,40))
    shapes['R']=shapes['R'].difference(wardrobe_trim)
    shapes['L']=shapes['L'].union(wardrobe_trim)
    nib = box(9,0,9.28,13)
    shapes['C'] = shapes['C'].union(nib)
    for adjacent in ('G','V'):
        shapes[adjacent]=shapes[adjacent].difference(nib)
    for r in source['rooms']:
        k=r['id']
        if k not in ids:continue
        shape=shapes[k]
        opts={}
        if k=='M':shape=shape.union(shapes['R'])
        if k=='U':shape=shape.union(shapes['Z'])
        if k in ('B','A'):opts.update(mechanicalVentilation=True,drain=True)
        if k=='C':opts.update(bedType='single')
        if k in ('G','X'):opts['garden']=True
        if k=='G':opts['centerTree']='frangipani'
        if k=='V':opts['clearAccess']=True
        if k=='I':opts.update(reclinerPosition=list(local(29.65,9.45)),careLayout='equipment-left')
        if k=='L':opts.update(ceilingStyle='plain-downlights',diningPosition=list(local(27.25-STAIR_WEST_MM/FT,29.7)),diningOrientation=0,sofaPosition=list(local(11.1,21.5)),sofaOrientation=270)
        room(0,ids[k],{'L':'Living, dining and stair lobby','B':'Caregiver ensuite','X':'East lawn','P':'Lower car porch','M':'Southwest master suite','U':'Wash utility and drain'}.get(k,r['name']),kinds[k],shape,**opts)
    for i,o in enumerate(source['openings']):
        a,b=o['a'],o['b']
        if a==[9,7.6]:a,b=[9.28,7.6],[9.28,11.6]
        line=LineString([a,b])
        hosts=[k for k in ['C','I','D','B','A','K','M','L'] if shapes[k].boundary.buffer(.0001).covers(line)]
        if not hosts:continue
        if a==[18,27.2]:hosts=['M']
        kind={'window':'window','door':'door','open':'cased','slider':'glazed','pocket':'glazed'}.get(o['kind'])
        if kind:
            if i==16:kind='entry'
            opening(0,'g-opening-'+str(i),ids[hosts[0]],a,b,kind)
            if o['kind']=='pocket' and 'I' in hosts:floors[0]['openings'][-1]['stackingSliding']=True
    opening(0,'living-east-light','living',(34,22.2),(34,29.0),'window')
    # A north-wall window over the porch lights the expanded kitchen.
    opening(0,'kitchen-porch-light','kitchen',(42.1,30),(45.1,30),'window')
    opening(0,'kitchen-wash-light','kitchen',(47,36.2),(47,39.1),'window')
    floors[0]['openings'][-1].update(sill=1100,height=1300)
    # Upstairs gallery spans from the stair head to both bedrooms and the study.
    envelope=box(3,7,44,40).union(box(20.25,1,44,7))
    suites=[
        ('west-suite','Southwest principal bedroom','bedroom',(3,24.8,18.75,40)),
        ('suite-entry','Private suite vestibule','foyer',(9.6,20.65,15.6,24.8)),
        ('shared-bath','Master ensuite','bathroom',(3,14.95,9.6,24.8)),
        ('library','Northwest study','study',(3,7,14.9,14.95)),
        ('garden-suite','Northeast bedroom','bedroom',(20.25,1,36,14.2)),
        ('loggia','Private garden balcony','balcony',(36,1,44,16)),
        ('east-balcony','East gallery balcony','balcony',(38,16,46,28)),
        ('sun-terrace','Open sitting terrace','terrace',(36,32,44,40))]
    for ident,name,kind,bounds in suites:
        room(1,ident,name,kind,box(*bounds))
    gallery=envelope.difference(unary_union([box(*item[-1]) for item in suites]))
    lobby=box(18.75,16,36,40)
    room(1,'gallery','Rectangular stair lobby','inner-lobby',lobby)
    for approach in gallery.difference(lobby).geoms:
        if approach.bounds[0]<18.75:
            room(1,'suite-gallery','Bedroom gallery','inner-lobby',approach)
        else:
            room(1,'balcony-gallery','East balcony approach','inner-lobby',approach)
    for key,a,b in [('north',(25,16),(28,16)),('west',(18.75,20),(18.75,23)),('east',(36,22),(36,25))]:
        opening(1,'lobby-open-'+key,'gallery',a,b,'cased').update(openSide=True,height=H-150)

    for j,(ident,a,b,kind) in enumerate([
        ('suite-entry',(15.6,21.05),(15.6,24.4),'door'),
        ('west-suite',(3,27),(3,36.5),'window'),
        ('garden-suite',(27,14.2),(30.4,14.2),'door'),('garden-suite',(23,1),(32,1),'window'),
        ('west-suite',(10.7,24.8),(14.2,24.8),'door'),
        ('shared-bath',(9.6,21.25),(9.6,24.25),'door'),
        ('garden-suite',(36,4),(36,12),'glazed'),
        ('library',(14.9,9.35),(14.9,12.65),'door'),('shared-bath',(3,18),(3,22.5),'window'),
        ('library',(4.5,7),(12.75,7),'window'),
        ('suite-gallery',(17.3,7),(19.5,7),'window'),
        ('balcony-gallery',(44,28.95),(44,31.25),'window'),
        ('balcony-gallery',(38,18),(38,25.5),'glazed'),('gallery',(36,33.1),(36,38.5),'glazed')
    ]):
        op=opening(1,'u-opening-'+str(j),ident,a,b,kind)
        if j==0:op.update(initiallyClosed=True,hinge='end')
        if j in (4,5):op.update(initiallyClosed=True)
    room(2,'stair-lobby','Open east hall and stair arrival','inner-lobby',box(18.65,15,35,40))
    room(2,'leisure-hall','Private TV lounge and office','family',box(3,15,18.65,40))
    room(2,'roof-garden','North roof terrace','terrace',box(0,0,50,15))
    opening(2,'lobby-hall-door','leisure-hall',(18.65,15.9),(18.65,19.4),'door').update(initiallyClosed=True,hinge='end')
    opening(2,'s-opening-0','stair-lobby',(30.05,15),(34.05,15),'door').update(initiallyClosed=True,swingRoomId='roof-garden')
    opening(2,'tv-terrace-door','leisure-hall',(13.25,15),(17.25,15),'door').update(initiallyClosed=True,swingRoomId='roof-garden')
    opening(2,'s-opening-1','leisure-hall',(3,32.4),(3,38.7),'window')
    for ident,host,a,b in [
        ('s-opening-2','leisure-hall',(4,15),(12.25,15)),
        ('s-opening-3','stair-lobby',(35,16.5),(35,32.5)),
        ('north-return-window','stair-lobby',(20,15),(29,15))
    ]:
        opening(2,ident,host,a,b,'window').update(sill=18*25.4,height=7.5*FT)
    base=json.loads((GALLERY/'briefs/tirumala-5.json').read_text())['brief']
    base.update(title='Tirumala 6',bedrooms=4,style='warm',exterior_theme='warm_modern_minimal',interior_theme='bright_natural')
    cp=dict(schema='floorforge.custom-plan/1',units='mm',wallThickness=WALL,floors=floors,stairs=[],frontCourt='tiled',doorsClosed=False,interiorFloor='ivory-vitrified',tirumalaMeta={'projectId':'tirumala-6'})
    # Same parcel: inherit the surveyed/illustrated site layers, not the old house.
    previous_scene=json.loads((GALLERY/'tirumala-5/scene.json').read_text())
    site_layers=('schema','style','roads','coordinate_system','north_colony_garden','east_basketball_court',
                 'north_frontage_utilities','northwest_feeder_cabinets','adjoining_south_and_west')
    cp['tirumalaMeta']['colony']={key:previous_scene['context'][key] for key in site_layers}
    site_materials=('t4-colony-road','t4-colony-paving','t4-colony-turf','t4-colony-wall','t4-boundary-coping',
                    't4-mulch','t4-chainlink','t4-garden-timber','t4-garden-urn')
    cp['tirumalaMeta']['colonyMaterials']={key:previous_scene['materials'][key] for key in site_materials}
    previous=json.loads((GALLERY/'briefs/tirumala-5.json').read_text())['customPlan']['secondPlan']['stairs']
    cp['tirumalaMeta']['eastGates']=[
        ['east-walk-gate' if o['name']=='Main gate' else 'east-car-gate',
         'pedestrian' if o['name']=='Main gate' else 'vehicle',
         local(*o['a'])[0],local(*o['b'])[0]]
        for o in source['openings'] if o['kind']=='gate']
    cp['tirumalaMeta']['finishEdition']='tirumala-5-ivory-teak'
    cp['tirumalaMeta']['stairTreads']=[dict(id=s['id'],bounds=[v+(STAIR_WEST_MM if j%2 else 0) for j,v in enumerate(s['bounds'])],top=s['top']-H,landing=s['landing']) for s in previous]
    cp['tirumalaMeta']['eastPorchRevision']=True
    cp['tirumalaMeta']['combinedArrival']=True
    cp['tirumalaMeta']['rectangularLanding']=True
    cp['tirumalaMeta']['northTerrace']=True
    return dict(schema='floorforge.project/0.4',brief=base,customPlan=cp,notes='Private garden verandah. Room dimensions on the reference sheet include walls. The shared porch is 16 ft deep by 14 ft wide overall, with a 2 by 1 ft return around the ICU. A vehicle threshold ramp connects the east verge to house level. The 14 ft kitchen platform is measured between finished walls. The stair arrives in the open east hall with a private door to the west TV room. The hall opens directly to the north terrace. The north terrace measures 50 ft east–west by 15 ft north–south and covers the ICU court, east lawn and part of the reading loggia. Its columns and beams are conceptual and require structural design.')
def main():
    payload=_browser_numbers(project())
    with tempfile.TemporaryDirectory(prefix='tirumala6-') as work:
        result=run(payload,Path(work),use_cache=False)
        shutil.copytree(result['path'],DEST,dirs_exist_ok=True)
    dump(GALLERY/'briefs/tirumala-6.json',payload)
    catalog=json.loads((GALLERY/'catalog.json').read_text())
    entry=dict(id='tirumala-6',title='Tirumala 6',description='Private ICU verandah and garden, an open dining gallery, two upper bedrooms, a central east balcony and an open upper stair hall leading into the TV lounge and office next to a full-width north terrace.',style='Ivory limestone · teak · charcoal',directory='gallery/tirumala-6',basedOnSample='tirumala-5',bedrooms=4,storeys=3,widthFt=40,depthFt=50,roofAccess=False,terraceAccess=True,planHash=result['planHash'])
    dump(GALLERY/'catalog.json',[i for i in catalog if i['id']!='tirumala-6']+[entry])
if __name__=='__main__':
    main()
