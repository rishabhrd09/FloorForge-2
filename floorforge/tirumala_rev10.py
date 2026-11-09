"""Tirumala A–E: L stair, expanded kitchen and two-suite upper floor.

The revision-9 north/care/site arrangement is retained. Coordinates remain clear
millimetres, with x south-to-north and y east-to-west. All published zones derive
from these same polygons; the corner inside the L stair belongs to the hall.
"""
from copy import deepcopy
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from .model import sha
from .tirumala_rev8 import OPTIONS, ft, fp, fn, rect_poly, build_option_project as previous

REVISION=10
WALL=150
HEIGHT=3508
SX=fp(.25); SY=ft(20); FW=1067; RUN=2591; EXT=FW+RUN
STAIR=[[SX,SY],[SX+FW,SY],[SX+FW,SY+RUN],[SX+EXT,SY+RUN],[SX+EXT,SY+EXT],[SX,SY+EXT]]

def stable_numbers(value):
    # JavaScript serializes integral doubles as integers; keep the same plan hash
    # before and after a browser JSON round trip.
    if isinstance(value,float) and value.is_integer():return int(value)
    if isinstance(value,dict):return {k:stable_numbers(v) for k,v in value.items()}
    if isinstance(value,list):return [stable_numbers(v) for v in value]
    return value

def poly(p):
    return [[round(x,4),round(y,4)] for x,y in p.exterior.coords[:-1]]

def room(ident,kind,name,p,**kw):
    return dict(id=ident,kind=kind,name=name,polygon=poly(p) if hasattr(p,'exterior') else p,**kw)

def opening(r,ident,side,axis,center,width,kind='door',height=2400,**kw):
    """Host an opening on a specific (including concave) clear polygon edge."""
    p=Polygon(r['polygon']);pts=list(p.exterior.coords);sign=1 if p.exterior.is_ccw else -1
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=(dx*dx+dy*dy)**.5
        nx,ny=sign*dy/length,-sign*dx/length
        s='right' if nx>.5 else 'left' if nx<-.5 else 'rear' if ny>.5 else 'front'
        horizontal=side in ('front','rear');k=0 if horizontal else 1
        if s==side and abs(a[1-k]-axis)<.1 and min(a[k],b[k])-.1<=center-width/2 and max(a[k],b[k])+.1>=center+width/2:
            return dict(id=ident,roomId=r['id'],side=side,edgeIndex=i,kind=kind,
                        offset=round(center-width/2-min(a[k],b[k]),4),width=width,height=height,sill=0,hinge='start',**kw)
    raise ValueError(f'No edge for {ident}: {side} axis={axis}, center={center}, width={width}: {pts}')

def build_option_project(option_code='A'):
    p=previous(option_code);cp=p['customPlan'];g=cp['floors'][0];gr={r['id']:r for r in g['rooms']};o=OPTIONS[option_code]
    kleft=SX+FW+WALL
    gr['g-stair'].update(name='Corner L stair · quarter turn',polygon=deepcopy(STAIR))
    gr['g-kitchen']['polygon']=[[kleft,fp(7.25)],[fn(9.25),fp(7.25)],[fn(9.25),fp(10.75)],
                               [fn(14.75),fp(10.75)],[fn(14.75),fn(21.75)],[kleft,fn(21.75)]]
    gr['g-kitchen']['name']='Expanded open kitchen · serving counter'
    gr['g-south-lane']['polygon']=rect_poly(SX,fn(7.25),SX+FW,SY-WALL)
    # The 150 mm boundary wall is outside the 3.5 ft clear daylight lane.
    g['walls'].append(dict(id='g-south-lane-boundary',a=[SX-WALL/2,fn(7.25)+WALL/2],
                          b=[SX-WALL/2,SY-WALL/2],height=1100))
    f=gr['g-family'];f['polygon']=[
        [fp(13.75),fp(7.25)],[fn(17.25),fp(7.25)],[fn(17.25),fp(o['drawEnd']+.25)],
        [fn(23.25),fp(o['drawEnd']+.25)],[fn(23.25),fn(32.25)],
        [SX+EXT+WALL,fn(32.25)],[SX+EXT+WALL,SY+RUN-WALL],
        [kleft,SY+RUN-WALL],[kleft,fp(21.75)],[fp(14.75),fp(21.75)],
        [fp(14.75),fn(10.75)],[fp(13.75),fn(10.75)]]
    f.update(diningPosition=[ft(10.5),ft(25.1)],diningOrientation=90,diningLength=1524,
             name='Open living · west dining · kitchen connection')
    # Rehost only openings affected by the new kitchen and L stair.
    removed={'g-kitchen-open-north','g-kitchen-rear-open','g-stair-east-window','g-stair-open-arrival',
             'g-stair-open-west','g-stair-open-east','g-master-door'}
    g['openings']=[a for a in g['openings'] if a['id'] not in removed]
    for a in g['openings']:
        if a['id']=='g-care-return-door':a['offset']=ft(17.8)-kleft
    stair=gr['g-stair'];k=gr['g-kitchen']
    g['openings'] += [
        opening(k,'g-kitchen-open-north','right',fn(14.75),(fp(10.75)+fn(21.75))/2,fn(21.75)-fp(10.75),'cased',HEIGHT,openSide=True),
        # One erased interface, with a low half-width serving counter and a wide walk-through beside it.
        opening(k,'g-kitchen-rear-open','rear',fn(21.75),(kleft+fn(14.75))/2,fn(14.75)-kleft,'cased',HEIGHT,openSide=True,servingCounter=True,counterInset=650),
        opening(stair,'g-stair-east-window','front',SY,SX+FW/2,990,'window',2500,sill_override=350),
        opening(stair,'g-stair-open-arrival','right',SX+EXT,SY+RUN+FW/2,FW,'cased',HEIGHT,openSide=True),
        opening(stair,'g-stair-inner-west','front',SY+RUN,(SX+FW+SX+EXT)/2,RUN-300,'cased',HEIGHT,openSide=True),
        opening(stair,'g-stair-inner-south','right',SX+FW,(fp(21.75)+SY+RUN-WALL)/2,SY+RUN-WALL-fp(21.75),'cased',HEIGHT,openSide=True),
        opening(gr['g-master'],'g-master-door','front',fp(32.25),ft(14.25),ft(2.5)),
    ]
    # Upper floor: a broad furnished lounge, two proper suites, a small office and a shared terrace.
    master1=deepcopy(gr['g-master']);master1.update(id='u-master',name='Master suite 1 · southwest',wardrobeWall='rear')
    bath1=deepcopy(gr['g-bath']);bath1.update(id='u-bath',name='Suite 1 attached bath')
    master2=room('u-master-2','bedroom','Master suite 2 · terrace access',
        [[fp(17.25),fp(17.25)],[fn(28.75),fp(17.25)],[fn(28.75),ft(23)],
         [fn(35.75),ft(23)],[fn(35.75),fn(36.25)],[fp(23.25),fn(36.25)],
         [fp(23.25),fn(21.75)],[fp(17.25),fn(21.75)]],wardrobeWall='right')
    bath2=room('u-bath-2','bathroom','Suite 2 attached bath',box(fp(24.75),fp(36.25),fn(30.25),fn(43.75)))
    office_front=40.25 if option_code=='E' else 40.75
    office_rear=46.75 if option_code=='E' else 47.25
    office=room('u-study','study','Compact home office',box(fp(15.75),fp(office_front),fn(24.75),fn(office_rear)))
    terrace=room('u-terrace','terrace','Shared open terrace',box(fp(17.25),fp(10.75),fn(28.75),fn(17.25)),clearAccess=True,finishStyle='honed-sandstone')
    ustair=room('u-stair','stair','L stair · upper arrival',deepcopy(STAIR),guardStyle='white-timber')
    void=room('u-living-void','void','Double-height living',box(fp(17.25),fp(o['drawEnd']+.75),fn(23.25),fn(32.25)),openToBelow=True,guardStyle='white-timber')
    lounge_shape=unary_union([box(SX,fp(7.25),fn(17.25),fn(32.25)),box(fp(15.75),fn(32.25),fn(17.25),fp(32.25)),box(fp(15.75),fp(32.25),fn(23.25),fn(office_front))]).difference(Polygon(STAIR).buffer(WALL,join_style=2))
    lounge=room('u-lobby','living','Upper family lounge · open landing',lounge_shape,ceilingStyle='plain-downlights')
    u={'id':'floor-1','rooms':[ustair,void,lounge,master1,bath1,master2,bath2,office,terrace],'walls':[],'openings':[]}
    # The side of the void facing a bedroom stays opaque; lounge edges use open guards.
    u['walls']=[dict(id='u-suite-void-wall',a=[ft(23.25),ft(o['drawEnd']+.75)],b=[ft(23.25),ft(32.25)])]
    u['openings']=[
        opening(ustair,'u-stair-open-arrival','front',SY,SX+FW/2,FW,'cased',HEIGHT,openSide=True),
        opening(ustair,'u-stair-inner-south','right',SX+FW,SY+RUN/2,RUN-300,'cased',HEIGHT,openSide=True),
        opening(ustair,'u-stair-inner-west','front',SY+RUN,SX+FW+RUN/2,RUN-300,'cased',HEIGHT,openSide=True),
        opening(ustair,'u-stair-end-open','right',SX+EXT,SY+RUN+FW/2,FW,'cased',HEIGHT,openSide=True),
        opening(master1,'u-master-door','right',fn(15.75),ft(35.0),ft(3)),
        opening(bath1,'u-bath-door','front',fp(39.75),ft(13.2),ft(2.5)),
        opening(bath1,'u-bath-west-window','rear',fn(47.25),ft(13.2),ft(2.5),'window',700,sill_override=1500),
        opening(master1,'u-master-south-window','left',SX,ft(39),ft(6),'window',1900,sill_override=600),
        opening(master1,'u-master-west-window','rear',fn(47.25),ft(5.5),ft(6),'window',1900,sill_override=600),
        opening(master2,'u-master-2-door','left',fp(17.25),ft(19.5),ft(3)),
        opening(master2,'u-master-2-north-window','right',fn(35.75),ft(29.5),ft(8),'window',2100,sill_override=500),
        opening(master2,'u-master-2-east-window','front',ft(23),ft(32.5),ft(5),'window',1900,sill_override=600),
        opening(bath2,'u-bath-2-door','front',fp(36.25),ft(27.5),ft(2.5)),
        opening(bath2,'u-bath-2-north-window','right',fn(30.25),ft(40),ft(2),'window',700,sill_override=1500),
        opening(office,'u-study-door','front',fp(office_front),ft(20),ft(3)),
        opening(office,'u-study-west-window','rear',fn(office_rear),ft(20),ft(5),'window',1600,sill_override=700),
        opening(terrace,'u-lobby-terrace-door','left',fp(17.25),ft(14),ft(5),'glazed',2700,sliding=True,slidingPanels=2),
        opening(terrace,'u-master-terrace-door','rear',fn(17.25),ft(24),ft(5),'glazed',2700,sliding=True,slidingPanels=2),
        opening(lounge,'u-lounge-east-window','front',fp(7.25),ft(9),ft(9),'window',2200,sill_override=600),
        opening(lounge,'u-lounge-south-window','left',SX,ft(12.5),ft(6),'window',2200,sill_override=600),
    ]
    names = {'g-kitchen':'Open kitchen', 'g-family':'Living + dining', 'g-stair':'Corner L stair', 'g-care':'Home care suite', 'g-drawing':'Drawing room', 'g-master':'Master bedroom', 'u-stair':'L stair arrival', 'u-lobby':'Upper family lounge', 'u-master':'Master suite 1', 'u-master-2':'Master suite 2', 'u-living-void':'Living void'}
    for fl in (g,u):
        for r in fl['rooms']:
            if r['id'] in names:r['name']=names[r['id']]
        for a in fl['openings']:
            if 'sill_override' in a:a['sill']=a.pop('sill_override')
    cp['floors'][1]=u
    cp['stairs']=[dict(id='south-corner-stair',roomIds=['g-stair','u-stair'],shape='quarter-turn',riseDirection='south-east',
                       openArrival=True,flightWidth=FW,well=152,landing=FW,tread=RUN/9)]
    cp['tirumalaRevision']=REVISION
    meta=cp['tirumalaMeta'];meta['revision']=REVISION
    mapping={'kitchen':k,'south':gr['g-south-lane'],'stair':stair,'family':f,'livingVoid':void,'uMaster':master1,
             'uMaster2':master2,'uBath':bath1,'uBath2':bath2,'uStudy':office,'uLounge':lounge,'uTerrace':terrace}
    for key,r in mapping.items():
        meta['canonicalZones'][key]=deepcopy(r['polygon'])
        dest=meta['first_ft'] if key.startswith('u') or key=='livingVoid' else meta['ground_ft']
        dest[key]=[[round(x/304.8,5),round(y/304.8,5)] for x,y in r['polygon']]
    meta['canonicalZones']['groundStairArrival']=rect_poly(SX+EXT,ft(28.5),ft(17),SY+EXT)
    meta['canonicalZones']['upperStairArrival']=rect_poly(SX,ft(16.5),SX+FW,SY)
    meta['ground_ft']['groundStairArrival']=[[x/304.8,y/304.8] for x,y in meta['canonicalZones']['groundStairArrival']]
    meta['first_ft']['upperStairArrival']=[[x/304.8,y/304.8] for x,y in meta['canonicalZones']['upperStairArrival']]
    meta['canonicalZones']['dining']=rect_poly(ft(9),ft(22.6),ft(12),ft(27.6))
    meta['furniture_ft']['diningTable']=[9,22.6,3,5]
    meta['geometryHash']=sha(stable_numbers({'revision':REVISION,'option':option_code,'floors':cp['floors'],'stairs':cp['stairs']}))
    p['brief']['bedrooms']=4
    p['notes']=f'Tirumala revision 10 — {o["label"]}. Corner L stair climbs south then east, freeing the west dining alcove. Enlarged connected kitchen with a low serving counter. Two upper master suites, compact office, furnished common lounge and shared open terrace with separate bedroom and lounge access. Care suite and site context retained. Design visualization; structural and surveyed dimensions need professional coordination.'
    p['draftRevision']=REVISION;p['editorState']['customPlan']=cp
    p['editorState']['guideFloors'][1]=[['bathroom','study','bathroom',''],['bedroom-1','hall','bedroom-2','bedroom-2'],['stair','living','void','bedroom-2'],['living','living','terrace','terrace']]
    return stable_numbers(p)

def canonical_handoff_zones(option_code='A'):
    return build_option_project(option_code)['customPlan']['tirumalaMeta']

def all_option_projects():
    return {code:build_option_project(code) for code in OPTIONS}
