"""Authoritative orthogonal plan compiler. All authored coordinates are clear-space millimetres.

Rooms are never resized, moved, mirrored or sent to the automatic planner. A uniform wall
thickness sits outside their clear boundaries; neighbouring enclosed rooms must leave that
wall allowance. The editor exposes the same contract, including opening hosts and stair links.
"""
from __future__ import annotations
import copy, math, re
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely import get_parts
from .model import DesignError, sha
from .spaces import SPACE_REGISTRY, OPEN_SKY, OUTDOOR, NON_WALKABLE
from .plan_geometry import regions, geometry

SCHEMA='floorforge.custom-plan/1'
ID=re.compile(r'[A-Za-z][A-Za-z0-9_.-]{0,79}')
SIDES=('front','right','rear','left')


def fail(code,message,ident=None,floor=None,**extra):
    issue={'code':code,'message':message,**extra}
    if ident is not None:issue['id']=ident
    if floor is not None:issue['floor']=floor
    raise DesignError('CUSTOM_PLAN_INVALID',message,{'errors':[issue]})


def normalize(plan,storeys):
    if not isinstance(plan,dict) or set(plan)-{'schema','units','wallThickness','floors','stairs','frontCourt','parkedCar','facadeStyle','doorsClosed'}:
        fail('PLAN_SCHEMA','Custom plan accepts schema, units, wallThickness, floors and stairs.')
    if plan.get('schema')!=SCHEMA or plan.get('units')!='mm':
        fail('PLAN_VERSION','Use floorforge.custom-plan/1 in millimetres.')
    result=copy.deepcopy(plan); seen=set()
    if 'doorsClosed' in result and type(result['doorsClosed']) is not bool:fail('DOOR_STATE','doorsClosed must be true or false.')
    if result.get('frontCourt','planted') not in ('planted','tiled'):fail('SITE_STYLE','Choose planted or tiled front court.')
    if result.get('facadeStyle','plain') not in ('plain','warm-layered'):fail('FACADE_STYLE','Choose plain or warm-layered facade finishes.')
    def ident(obj):
        key=obj.get('id')
        if not isinstance(key,str) or not ID.fullmatch(key) or key in seen:fail('PLAN_ID','Every floor, room, wall, opening and stair needs a unique stable ID.',key)
        seen.add(key)
    def numeric(n,lo,hi,key):
        if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or not lo<=n<=hi:
            fail('PLAN_NUMBER',f'{key} must be finite and between {lo:g} and {hi:g}.')
    def point(p,key):
        if not isinstance(p,list) or len(p)!=2:fail('PLAN_POINT',f'{key} needs two coordinates.')
        for n in p:numeric(n,-60000,60000,key)
    t=result.setdefault('wallThickness',150);numeric(t,100,400,'wallThickness')
    if 'parkedCar' in result:
        car=result['parkedCar']
        if not isinstance(car,dict) or set(car)!={'x','y'}:fail('PARKED_CAR','Parked car needs x and y coordinates in millimetres.')
        for key in ('x','y'):numeric(car[key],-60000,60000,'parkedCar.'+key)
    floors=result.get('floors')
    if not isinstance(floors,list) or len(floors)!=storeys:fail('PLAN_FLOORS','Custom-plan floor count must match the brief.')
    for f,fl in enumerate(floors):
        if not isinstance(fl,dict) or set(fl)-{'id','rooms','walls','openings'}:fail('FLOOR_SCHEMA','A floor contains id, rooms, walls and openings.',floor=f)
        ident(fl)
        for key,limit in [('rooms',120),('walls',240),('openings',240)]:
            items=fl.setdefault(key,[])
            if not isinstance(items,list) or len(items)>limit:fail('PLAN_LIMIT',f'{key} must be a list of at most {limit} objects.',fl['id'],f)
            for o in items:
                if not isinstance(o,dict):fail('PLAN_OBJECT','Plan items must be objects.',floor=f)
                ident(o)
                allowed={'rooms':{'id','name','kind','polygon','drain','openToSky','gardenBed','openToBelow','underStair','mechanicalVentilation','bedType','clearAccess','garden','glassCover','finishStyle','reclinerPosition','tvOffset','serviceOnly','careLayout','diningPosition','diningOrientation','diningLength','diningCounterGap','sofaPosition','sofaOrientation','seatingExtension','altarWall','prepStorageWall'},'walls':{'id','a','b'},
                         'openings':{'id','roomId','side','kind','offset','width','height','sill','hinge','servingCounter','sliding','slidingPanels','timberScreen','swingRoomId','openSide'}}[key]
                if set(o)-allowed:fail('PLAN_FIELDS',f'Unsupported fields on {key}.',o['id'],f)
                if key=='rooms':
                    if o.get('kind') not in SPACE_REGISTRY:fail('SPACE_KIND','Choose a room type from the shared catalogue.',o['id'],f)
                    o.setdefault('name',SPACE_REGISTRY[o['kind']]['label'])
                    if not isinstance(o['name'],str) or not 1<=len(o['name'])<=120:fail('SPACE_NAME','Room names need 1–120 characters.',o['id'],f)
                    if 'finishStyle' in o and (o['finishStyle'] not in ('warm-stone','garden-lawn') or o['kind']!='veranda'):fail('FINISH_STYLE','Warm stone finish applies to verandas.',o['id'],f)
                    if 'careLayout' in o and (o['kind']!='care-room' or o['careLayout']!='equipment-left'):fail('CARE_LAYOUT','Choose the equipment-left layout for a care room.',o['id'],f)
                    if 'prepStorageWall' in o and (o['kind']!='kitchen' or o['prepStorageWall'] not in SIDES):fail('PREP_WALL','Choose a kitchen backing wall for prep storage.',o['id'],f)
                    if 'altarWall' in o and (o['kind']!='pooja' or o['altarWall'] not in SIDES):fail('ALTAR_WALL','Choose a front/right/rear/left backing wall for the mandir.',o['id'],f)
                    if 'diningPosition' in o:
                        if o['kind'] not in ('living','family'):fail('DINING_POSITION','A dining position applies to a shared living or family room.',o['id'],f)
                        point(o['diningPosition'],'diningPosition')
                    if 'diningOrientation' in o and ('diningPosition' not in o or type(o['diningOrientation']) is not int or o['diningOrientation'] not in (0,90)):
                        fail('DINING_ORIENTATION','Use 0 or 90 degrees with a dining position.',o['id'],f)
                    if 'diningLength' in o:
                        if 'diningPosition' not in o:fail('DINING_LENGTH','A dining length requires a dining position.',o['id'],f)
                        numeric(o['diningLength'],1200,3000,'diningLength')
                    if 'diningCounterGap' in o:
                        if 'diningPosition' not in o:fail('DINING_GAP','Counter clearance requires a dining position.',o['id'],f)
                        numeric(o['diningCounterGap'],600,1500,'diningCounterGap')
                    if 'sofaPosition' in o:
                        if o['kind'] not in ('living','family'):fail('SOFA_POSITION','Authored seating applies to a living or family room.',o['id'],f)
                        point(o['sofaPosition'],'sofaPosition')
                        if type(o.get('sofaOrientation')) is not int or o['sofaOrientation'] not in (0,90,180,270):fail('SOFA_ORIENTATION','Provide a cardinal seating direction.',o['id'],f)
                    if 'sofaOrientation' in o and 'sofaPosition' not in o:fail('SOFA_POSITION','Seating direction requires a position.',o['id'],f)
                    if 'seatingExtension' in o and ('sofaPosition' not in o or not isinstance(o['seatingExtension'],str)):fail('SEATING_EXTENSION','An open hall extension requires authored seating.',o['id'],f)
                    if 'tvOffset' in o:
                        if o['kind']!='care-room':fail('CARE_POSITION','TV offset applies to a care room.',o['id'],f)
                        numeric(o['tvOffset'],-3000,3000,'tvOffset')
                    if 'reclinerPosition' in o and (o['kind']!='care-room' or not isinstance(o['reclinerPosition'],list) or len(o['reclinerPosition'])!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in o['reclinerPosition'])):fail('CARE_POSITION','Care furniture needs a finite x/y position.',o['id'],f)
                    if 'serviceOnly' in o and (type(o['serviceOnly']) is not bool or o['kind'] not in ('courtyard','veranda')):fail('SERVICE_SPACE','Service-only space applies to a lightwell or its covered outdoor edge.',o['id'],f)
                    if 'openToSky' in o and (type(o['openToSky']) is not bool or o['kind']!='void' or not o.get('openToBelow')):fail('SKY_VOID','An open sky cut requires an open-to-below void.',o['id'],f)
                    if 'gardenBed' in o:
                        bed=o['gardenBed']
                        if o['kind']!='veranda' or not isinstance(bed,list) or len(bed)!=4:fail('GARDEN_BED','A veranda bed needs four rectangle bounds.',o['id'],f)
                        for n in bed:numeric(n,0,60000,'gardenBed')
                        if bed[2]<=bed[0] or bed[3]<=bed[1] or not Polygon(o['polygon']).covers(box(*bed)):fail('GARDEN_BED','Planting must fit inside the veranda.',o['id'],f)
                    if 'glassCover' in o and (type(o['glassCover']) is not bool or o['kind']!='courtyard'):fail('GLASS_COVER','A clear canopy applies to a courtyard.',o['id'],f)
                    if 'garden' in o and (type(o['garden']) is not bool or o['kind']!='courtyard'):fail('GARDEN','Garden planting applies to a courtyard.',o['id'],f)
                    if 'clearAccess' in o and (type(o['clearAccess']) is not bool or o['kind'] not in ('veranda','terrace','balcony')):fail('CLEAR_ACCESS','Clear access applies to outdoor decks.',o['id'],f)
                    if 'drain' in o and type(o['drain']) is not bool:fail('SPACE_DRAIN','Drain must be true or false.',o['id'],f)
                    if 'openToBelow' in o and (type(o['openToBelow']) is not bool or o['kind']!='void'):
                        fail('VOID_SCHEMA','Open-to-below applies only to a double-height void.',o['id'],f)
                    if 'mechanicalVentilation' in o and (type(o['mechanicalVentilation']) is not bool or o['kind'] not in ('bathroom','powder-room')):
                        fail('VENTILATION_SCHEMA','Mechanical exhaust applies to a bathroom or WC.',o['id'],f)
                    if 'bedType' in o and (o['kind']!='bedroom' or o['bedType'] not in ('single','double')):
                        fail('BED_TYPE','Single or double beds apply to bedrooms.',o['id'],f)
                    if 'underStair' in o and (o['kind']!='powder-room' or not isinstance(o['underStair'],str)):
                        fail('UNDER_STAIR_TYPE','Only a compact WC can reference its enclosing stair.',o['id'],f)
                    pts=o.get('polygon')
                    if not isinstance(pts,list) or not 4<=len(pts)<=64:fail('SPACE_POLYGON','Use 4–64 orthogonal polygon vertices.',o['id'],f)
                    for p in pts:point(p,'polygon')
                elif key=='walls':
                    point(o.get('a'),'wall start');point(o.get('b'),'wall end')
                else:
                    if not isinstance(o.get('roomId'),str) or o.get('side') not in SIDES:fail('OPENING_HOST','Choose a room and a front/right/rear/left wall.',o['id'],f)
                    if o.get('kind') not in ('door','entry','window','cased','glazed'):fail('OPENING_KIND','Unsupported opening type.',o['id'],f)
                    o.setdefault('sill',850 if o['kind']=='window' else 0);o.setdefault('height',1450 if o['kind']=='window' else 2100);o.setdefault('hinge','start')
                    if 'openSide' in o and (type(o['openSide']) is not bool or o['kind']!='cased'):fail('OPEN_SIDE','An open side must be a full-height cased connection.',o['id'],f)
                    if 'timberScreen' in o and (type(o['timberScreen']) is not bool or o['kind']!='door' or o.get('sliding') or o['width']<1800):fail('TIMBER_SCREEN','Paired timber and screen leaves require a hinged door at least 1.8 m wide.',o['id'],f)
                    if 'slidingPanels' in o and (not o.get('sliding') or type(o['slidingPanels']) is not int or o['slidingPanels'] not in (2,3)):fail('SLIDING_PANELS','Choose two or three sliding glass panels.',o['id'],f)
                    if 'sliding' in o and (type(o['sliding']) is not bool or o['kind']!='glazed'):fail('SLIDING_OPENING','Sliding panels require a glazed door.',o['id'],f)
                    if 'servingCounter' in o and ((type(o['servingCounter']) is not bool and o['servingCounter']!='full') or o.get('kind')!='cased' or o.get('width',0)<(900 if o['servingCounter']=='full' else 2400)):
                        fail('COUNTER_OPENING','Use a cased opening: at least 2.4 m for a half counter or 0.9 m for a full serving hatch.',o['id'],f)
                    if o['hinge'] not in ('start','end'):fail('OPENING_HINGE','Use start or end hinge.',o['id'],f)
                    for k,lo,hi in [('offset',0,60000),('width',450,6000),('height',300,3600),('sill',0,3000)]:numeric(o.get(k),lo,hi,k)
            fl[key]=sorted(items,key=lambda o:o['id'])
    stairs=result.setdefault('stairs',[])
    if not isinstance(stairs,list) or len(stairs)>8:fail('STAIR_LIMIT','Use at most eight linked stair cores.')
    for st in stairs:
        if not isinstance(st,dict) or set(st)-{'id','roomIds','flightWidth','well','landing','tread','rotation'}:fail('STAIR_SCHEMA','A linked U stair contains id, roomIds, flightWidth, well, landing and tread.')
        ident(st)
        if st.get('rotation',0) not in (0,90):fail('STAIR_ROTATION','Stair rotation must be 0 or 90 degrees.',st['id'])
        ids=st.get('roomIds')
        if not isinstance(ids,list) or not 1<=len(ids)<=3 or any(not isinstance(i,str) for i in ids):fail('STAIR_LINK','Link stair rooms on consecutive floors; a single-floor core needs roof access.',st['id'])
        for k,default,lo,hi in [('flightWidth',1000,1000,2000),('well',200,100,600),('landing',1050,1000,2000),('tread',250,250,350)]:
            numeric(st.setdefault(k,default),lo,hi,k)
    result['stairs']=sorted(stairs,key=lambda o:o['id'])
    return result


def under_stair_rooms(plan,v):
    """Validate the WC against the actual return-flight underside, including walls.

    Keep at least 750 mm of the ground arrival landing open. A flat 2.10 m
    ceiling must fit below every tread; no overlap exception exists elsewhere.
    """
    t=plan['wallThickness']
    for f,fl in enumerate(plan['floors']):
        rooms={r['id']:r for r in fl['rooms']}
        for r in fl['rooms']:
            if not r.get('underStair'):continue
            host=rooms.get(r['underStair']);st=next((s for s in plan['stairs'] if r['underStair'] in s['roomIds']),None)
            if not host or host['kind']!='stair' or not st or f!=0:
                fail('UNDER_STAIR_HOST','A ground-floor WC must reference a linked stair on the same floor.',r['id'],f)
            p=Polygon(r['polygon']);x0,y0,x1,y1=p.bounds;sx,sy,_,_=Polygon(host['polygon']).bounds
            if st.get('rotation'):fail('UNDER_STAIR_ORIENTATION','Under-stair WC currently requires an unrotated core.',r['id'],f)
            fw,well,land=st['flightWidth'],st['well'],st['landing'];H=v['floor_height_mm']
            n=math.ceil(H/190/2);rise=H/(2*n);steps=n-1;mid=sy+land+steps*st['tread']
            if abs(p.area-(x1-x0)*(y1-y0))>1 or x0<sx+fw+well-.01 or x1>sx+2*fw+well+.01 or y0-t<sy+750:
                fail('UNDER_STAIR_APPROACH','Keep the WC below the return flight and leave the stair arrival clear.',r['id'],f)
            back=y1+t
            underside=H-160
            for j in range(steps):
                a=mid-(j+1)*st['tread'];c=a+st['tread']
                if min(back,c)>max(y0-t,a):underside=min(underside,n*rise+j*rise-90)
            if back>mid or underside<2150:
                fail('UNDER_STAIR_HEADROOM','The WC walls and 2.10 m ceiling must fit below the stair with 50 mm allowance.',r['id'],f)


def geometry_preflight(plan, envelope):
    """Report all simple drafting conflicts together, before constructing any walls."""
    errors=[];W,D=envelope.bounds[2:];t=plan['wallThickness']
    for f,fl in enumerate(plan['floors']):
        valid=[]
        if not fl['rooms']:
            name=('Ground','First','Second')[f]
            errors.append({'code':'EMPTY_FLOOR','message':f'{name} floor is empty. Add its rooms, landings or terrace in Custom Plan, or reduce the storey count. A roof terrace above the last occupied floor uses Stairs to roof instead.','id':fl['id'],'name':name+' floor','floor':f})
        for r in fl['rooms']:
            p=Polygon(r['polygon'])
            if not p.is_valid or p.is_empty:continue  # compiler supplies the topology diagnostic
            x,y,x1,y1=p.bounds;pad=t if SPACE_REGISTRY[r['kind']]['enclosed'] else 0
            exceeds={side:round(amount,1) for side,amount in [('left',pad-x),('front',pad-y),('right',x1+pad-W),('rear',y1+pad-D)] if amount>.01}
            if exceeds:
                code='SETBACK' if not envelope.covers(p) else 'WALL_SETBACK'
                message=f"{r['name']} crosses the buildable boundary at "+', '.join(f'{side} by {amount:g} mm' for side,amount in exceeds.items())
                if pad:message+=f' including its {t:g} mm outer wall'
                item={'code':code,'message':message+'. Move it inward; clear dimensions are retained.','id':r['id'],'name':r['name'],'floor':f,'exceeds_mm':exceeds}
                if x1-x<=W-2*pad and y1-y<=D-2*pad:
                    item['fix']={'action':'move','dx':round(max(pad,min(x,W-pad-(x1-x)))-x,3),'dy':round(max(pad,min(y,D-pad-(y1-y)))-y,3)}
                errors.append(item)
            for other,q in valid:
                if r.get('underStair')==other['id'] or other.get('underStair')==r['id']:continue
                if p.intersection(q).area>1:
                    errors.append({'code':'SPACE_OVERLAP','message':f"{r['name']} overlaps {other['name']}. Move or resize one of these rooms.",'id':r['id'],'ids':[r['id'],other['id']],'name':r['name'],'floor':f})
                elif SPACE_REGISTRY[r['kind']]['enclosed'] and SPACE_REGISTRY[other['kind']]['enclosed'] and p.buffer(t-.01,join_style=2).intersection(q).area>1:
                    errors.append({'code':'WALL_CLEARANCE','message':f"Leave {t:g} mm for the shared wall between {r['name']} and {other['name']}. Drag near its edge with Smart snap enabled.",'id':r['id'],'ids':[r['id'],other['id']],'floor':f,'name':r['name']})
            valid.append((r,p))
    if errors:raise DesignError('CUSTOM_PLAN_INVALID',f"Fix {len(errors)} geometry issue{'s' if len(errors)!=1 else ''} on the plan before checking doors and access.",{'errors':errors})


def wall_runs(raw, outdoor, half):
    """Node solid wall axes wherever the adjoining outdoor space changes.

    Outdoor boundaries do not generate walls, but still divide opening hosts.
    Use parallel edge intervals, not distance to a single midpoint: two zones
    can meet at that point while adjoining different portions of the wall.
    A corner touching the end of a wall is not a door connection.
    """
    segments=set()
    for part in get_parts(raw):
        for a,b in zip(part.coords,list(part.coords)[1:]):
            if math.dist(a,b)>1:segments.add(tuple(sorted((tuple(a),tuple(b)))))
    for a,b in sorted(segments):
        axis=0 if a[1]==b[1] else 1;normal=1-axis
        intervals=[];cuts={a[axis],b[axis]}
        for ident,p in outdoor.items():
            edges=[];points=list(p.exterior.coords)
            for c,d in zip(points,points[1:]):
                if abs(c[normal]-d[normal])>.01 or abs(c[normal]-a[normal])>half+.01:continue
                lo=max(a[axis],min(c[axis],d[axis]));hi=min(b[axis],max(c[axis],d[axis]))
                if hi-lo>.01:edges.append((lo,hi))
            # Collinear vertices in a painted polygon are not new wall junctions.
            merged=[]
            for lo,hi in sorted(edges):
                if merged and lo<=merged[-1][1]+.01:merged[-1][1]=max(hi,merged[-1][1])
                else:merged.append([lo,hi])
            for lo,hi in merged:intervals.append((lo,hi,ident));cuts.update((lo,hi))
        cuts=sorted(cuts)
        for lo,hi in zip(cuts,cuts[1:]):
            if hi-lo<=.01:continue
            start=list(a);end=list(b);start[axis]=lo;end[axis]=hi
            owners=sorted({ident for begin,finish,ident in intervals if begin<=(lo+hi)/2<=finish})
            yield tuple(start),tuple(end),owners


def compile_plan(intent):
    v=intent['values'];plan=normalize(intent['customPlan'],v['storeys']);t=plan['wallThickness'];half=t/2
    envelope=box(0,0,v['width_mm']-v['left_mm']-v['right_mm'],v['depth_mm']-v['front_mm']-v['rear_mm'])
    if envelope.area<=0:fail('ENVELOPE','Setbacks leave no buildable envelope.')
    spaces=[];walls=[];openings=[];stairs=[];plates=[];polys={};floor_polys={};room_map={};guards=[]
    under_stair_rooms(plan,v)
    geometry_preflight(plan, envelope)
    for f,fl in enumerate(plan['floors']):
        local={}
        if not fl['rooms']:fail('EMPTY_FLOOR','Each floor needs at least one space.',fl['id'],f)
        for r in fl['rooms']:
            p=Polygon(r['polygon'])
            if not p.is_valid or p.is_empty or p.area<10000:fail('SPACE_GEOMETRY','Room polygon must be simple and have positive area.',r['id'],f)
            for a,b in zip(r['polygon'],r['polygon'][1:]+r['polygon'][:1]):
                if math.dist(a,b)<1 or (abs(a[0]-b[0])>.01 and abs(a[1]-b[1])>.01):fail('ORTHOGONAL','Walls and rooms must be orthogonal; zero-length edges are invalid.',r['id'],f)
            if not envelope.covers(p):fail('SETBACK','Space extends beyond the buildable envelope. Its dimensions were retained.',r['id'],f)
            for oid,q in local.items():
                if r.get('underStair')==oid or room_map[oid][1].get('underStair')==r['id']:continue
                if p.intersection(q).area>1:fail('SPACE_OVERLAP','Spaces overlap.',r['id'],f,ids=[r['id'],oid])
            if r.get('reclinerPosition'):
                cx,cy=r['reclinerPosition']
                if not p.covers(box(cx-1100,cy-550,cx+1100,cy+550)):fail('CARE_POSITION','Recliner footprint must fit inside the care room.',r['id'],f)
            if r.get('diningPosition') and not p.contains(Point(*r['diningPosition'])):fail('DINING_POSITION','The dining position must be inside its room.',r['id'],f)
            spec=SPACE_REGISTRY[r['kind']];local[r['id']]=p;polys[r['id']]=p;room_map[r['id']]=(f,r)
            spaces.append({'id':r['id'],'floorId':fl['id'],'name':r['name'],'kind':r['kind'],'floor':f,
                           'polygon':r['polygon'],'clear':r['polygon'],'area_m2':round(p.area/1e6,6),
                           'enclosed':spec['enclosed'],'roofed':spec['roofed'] and not r.get('openToSky'),'walkable':spec['floor'],
                           'wet':spec['wet'],'drain':r.get('drain',False),
                           **({'mechanicalVentilation':True} if r.get('mechanicalVentilation') else {}),
                           **({'clearAccess':True} if r.get('clearAccess') else {}),
                           **({'serviceOnly':True} if r.get('serviceOnly') else {}),
                           **({'garden':True} if r.get('garden') else {}),
                           **({'gardenBed':r['gardenBed']} if r.get('gardenBed') else {}),
                           **({'openToSky':True} if r.get('openToSky') else {}),
                           **({'glassCover':True} if r.get('glassCover') else {}),
                           **({'finishStyle':r['finishStyle']} if r.get('finishStyle') else {}),
                           **({'bedType':r['bedType']} if r.get('bedType') else {}),
                           **({'reclinerPosition':r['reclinerPosition']} if r.get('reclinerPosition') else {}),
                           **({'prepStorageWall':r['prepStorageWall']} if r.get('prepStorageWall') else {}),
                           **({'altarWall':r['altarWall']} if r.get('altarWall') else {}),
                           **({'diningPosition':r['diningPosition']} if r.get('diningPosition') else {}),
                           **({'diningOrientation':r['diningOrientation']} if 'diningOrientation' in r else {}),
                           **({'diningLength':r['diningLength']} if 'diningLength' in r else {}),
                           **({'diningCounterGap':r['diningCounterGap']} if 'diningCounterGap' in r else {}),
                           **({key:r[key] for key in ('sofaPosition','sofaOrientation','seatingExtension') if key in r}),
                           **({'careLayout':r['careLayout']} if r.get('careLayout') else {}),
                           **({'tvOffset':r['tvOffset']} if r.get('tvOffset') else {}),
                           **({'underStair':r['underStair'],'ceilingHeight':2100,'ventilation':'mechanical-design-required'} if r.get('underStair') else {})})
        floor_polys[f]=local
        # Offset into the wall allowance. Noding merges shared walls and splits T junctions.
        paths=[];source_lines=[]
        for r in fl['rooms']:
            if r.get('underStair') or not SPACE_REGISTRY[r['kind']]['enclosed']:continue
            p=local[r['id']];ring=p.buffer(half,join_style=2).exterior
            points=list(ring.coords)
            for a,b in zip(points,points[1:]):
                line=LineString([a,b]);paths.append(line);source_lines.append((r['id'],line))
        for w in fl['walls']:
            a,b=w['a'],w['b']
            if math.dist(a,b)<100 or (a[0]!=b[0] and a[1]!=b[1]):fail('WALL_GEOMETRY','A wall must be orthogonal and at least 100 mm long.',w['id'],f)
            line=LineString([a,b]);paths.append(line);source_lines.append((w['id'],line))
        raw=unary_union(paths);floor_walls=[]
        outdoor={i:p for i,p in local.items() if not SPACE_REGISTRY[room_map[i][1]['kind']]['enclosed']}
        interior_clear=unary_union([p for i,p in local.items() if i not in outdoor and not room_map[i][1].get('underStair')])
        for a,b,outdoor_owners in wall_runs(raw,outdoor,half):
            line=LineString([a,b]);mid=line.interpolate(.5,normalized=True)
            owners=sorted({i for i,source in source_lines if i in local and source.distance(mid)<.01})
            authored=next((w['id'] for w in fl['walls'] if LineString([w['a'],w['b']]).buffer(.01).covers(line)),None)
            if not owners and not authored:continue
            wallpoly=line.buffer(half,cap_style=3,join_style=2)
            # Outdoor zones may abut the outside face. Clear interiors are never consumed by a wall.
            if wallpoly.intersection(interior_clear).area>1:fail('WALL_CLEARANCE','Leave one wall thickness between rooms; a wall would reduce an exact clear dimension.',owners[0] if owners else authored,f)
            if not envelope.buffer(.01).covers(wallpoly):fail('WALL_SETBACK','The room fits, but its wall thickness crosses the buildable envelope.',owners[0] if owners else authored,f)
            owners=sorted(set(owners+outdoor_owners))
            if len(owners)>2:
                names=[room_map[i][1]['name'] for i in owners]
                fail('WALL_TOPOLOGY','Conflicting wall connections between '+', '.join(names)+'. Review their shared edges.',floor=f,ids=owners,names=names,segment=[list(a),list(b)])
            wid=authored or 'wall-'+sha({'floor':fl['id'],'rooms':sorted(owners),'axis':'x' if a[1]==b[1] else 'y',
                                      'sides':[(i,side_at(local[i],mid)) for i in sorted(owners)]})[:18]
            # Disconnected segments of the same side need distinct stable suffixes.
            base=wid;n=1
            while any(w['id']==wid for w in floor_walls):n+=1;wid=base+'-'+str(n)
            floor_walls.append({'id':wid,'floor':f,'floorId':fl['id'],'a':list(a),'b':list(b),'thickness':t,
                                'height':v['floor_height_mm']-150,'rooms':sorted(owners),'external':len(owners)==1,
                                'polygon':regions(wallpoly)[0]['polygon']})
        # Under-stair partitions are a separate vertical layer. They do not split
        # the full-height stair opening or consume the upper stair flight.
        for r in fl['rooms']:
            if not r.get('underStair'):continue
            host_id=r['underStair'];ring=local[r['id']].buffer(half,join_style=2).exterior
            for n,(a,c) in enumerate(zip(ring.coords,list(ring.coords)[1:])):
                a,c=sorted((a,c))  # opening offsets run from the smaller coordinate
                line=LineString([a,c]);mid=line.interpolate(.5,normalized=True)
                neighbours=[i for i,p in local.items() if i not in (r['id'],host_id) and abs(p.distance(mid)-half)<.01]
                owners=[r['id'],neighbours[0] if neighbours else host_id]
                wallpoly=line.buffer(half,cap_style=3,join_style=2)
                floor_walls.append(dict(id=r['id']+'-partition-'+str(n),floor=f,floorId=fl['id'],a=list(a),b=list(c),thickness=t,
                                        height=2100,rooms=owners,external=False,underStair=host_id,polygon=regions(wallpoly)[0]['polygon']))
        # The slab includes wall allowances and outdoor decks, while voids are actual holes.
        outline=unary_union([*local.values(),*[Polygon(w['polygon']) for w in floor_walls]])
        if outline.geom_type!='Polygon':fail('DISCONNECTED_FLOOR','Connect all floor spaces with rooms, landings or decks.',fl['id'],f)
        slab=outline
        for r in fl['rooms']:
            if r['kind'] in NON_WALKABLE:slab=slab.difference(local[r['id']])
        plates.append({'id':'plate-'+fl['id'],'floor':f,'floorId':fl['id'],'outline':regions(outline),'regions':regions(slab),'openings':[]})
        # An explicitly open atrium retains the wall allowance in the slab outline,
        # but its indoor edges have guards rather than opaque full-height walls.
        # Authored walls (e.g. the atrium's exterior glazing host) remain authoritative.
        atriums={r['id'] for r in fl['rooms'] if r.get('openToBelow')}
        authored_lines=[LineString([w['a'],w['b']]).buffer(.01) for w in fl['walls']]
        floor_walls=[w for w in floor_walls if not atriums.intersection(w['rooms']) or
                     any(p.covers(LineString([w['a'],w['b']])) for p in authored_lines)]
        walls.extend(floor_walls)
        for o in fl['openings']:
            if o['roomId'] not in local:fail('OPENING_ROOM','Opening references a room on another or missing floor.',o['id'],f)
            p=local[o['roomId']];x0,y0,x1,y1=p.bounds;side=o['side'];horiz=side in ('front','rear')
            # Offsets are measured from the smaller x/y coordinate of the clear room bounding box.
            start=(x0+o['offset'], y0-half if side=='front' else y1+half) if horiz else (x0-half if side=='left' else x1+half,y0+o['offset'])
            end=(start[0]+o['width'],start[1]) if horiz else (start[0],start[1]+o['width'])
            span=LineString([start,end]);host=next((w for w in floor_walls if o['roomId'] in w['rooms'] and LineString([w['a'],w['b']]).buffer(.01).covers(span)),None)
            if host is None:fail('OPENING_HOST','Opening does not fit a continuous wall of this room. Move it clear of a corner or junction.',o['id'],f)
            if o['sill']+o['height']>host['height']:fail('OPENING_HEIGHT','Opening crosses the wall head.',o['id'],f)
            if o['kind']!='window' and o['sill']!=0:fail('DOOR_SILL','Circulation openings must start at floor level.',o['id'],f)
            if o['kind']!='window' and o['width']<750 and not (o.get('openSide') and LineString([host['a'],host['b']]).length+t>=750):fail('DOOR_WIDTH','Circulation openings require at least 750 mm clear width.',o['id'],f)
            connects=list(host['rooms'])+(['outside'] if host['external'] else [])
            if len(connects)!=2:fail('OPENING_CONNECTION','An opening needs two adjacent spaces or one space and outside.',o['id'],f)
            if o['kind']=='entry' and (f!=0 or 'outside' not in connects):fail('ENTRY_LOCATION','The main entry must connect the ground floor to outside.',o['id'],f)
            if 'outside' in connects and f>0 and o['kind']!='window':fail('UPPER_EXIT','An upper-floor door must open onto an authored balcony, terrace or landing.',o['id'],f)
            if o['kind']=='window' and all(i!='outside' and room_map[i][1]['kind'] not in OUTDOOR for i in connects):
                fail('WINDOW_AIR','A window must face outside, an outdoor zone or an open ventilation shaft.',o['id'],f)
            if 'swingRoomId' in o and (o['kind'] not in ('door','entry') or o['swingRoomId'] not in local or o['swingRoomId'] not in connects):fail('DOOR_SWING_ROOM','Choose an adjoining room for the door swing.',o['id'],f)
            offset=LineString([host['a'],host['b']]).project(Point(start))
            width=o['width']
            if o.get('openSide'):
                if host['external'] or o['height']!=host['height'] or len(connects)!=2 or any(room_map[i][1]['kind'] in OUTDOOR for i in connects):
                    fail('OPEN_SIDE_HOST','An open side needs two indoor spaces and the full wall height.',o['id'],f)
                # Erase the entire host including square end caps, leaving no corner post.
                offset=-half; width=LineString([host['a'],host['b']]).length+t
            for old in openings:
                if old['wall_id']==host['id'] and min(offset+width,old['offset']+old['width'])>max(offset,old['offset'])+.1 and min(o['sill']+o['height'],old['sill']+old['height'])>max(o['sill'],old['sill']):
                    fail('OPENING_OVERLAP','Two openings overlap.',o['id'],f,ids=[o['id'],old['id']])
            openings.append({'id':o['id'],'wall_id':host['id'],'floor':f,'kind':o['kind'],'offset':offset,
                             'width':width,'sill':o['sill'],'height':o['height'],'connects':connects,
                             'swing':o.get('swingRoomId',o['roomId']) if o['kind'] in ('door','entry') else None,'hinge':o['hinge'],**({'openSide':True} if o.get('openSide') else {}),**({'timberScreen':True} if o.get('timberScreen') else {}),**({'sliding':True} if o.get('sliding') else {}),**({'slidingPanels':o['slidingPanels']} if o.get('slidingPanels') else {}),**({'servingCounter':o['servingCounter']} if o.get('servingCounter') else {})})
    linked=set()
    for st in plan['stairs']:
        ids=st['roomIds']
        if any(i not in room_map or room_map[i][1]['kind']!='stair' for i in ids):fail('STAIR_ROOM','Stairs must link existing staircase spaces.',st['id'])
        fs=[room_map[i][0] for i in ids]
        if len(ids)==1 and not (v.get('roof_access') and fs[0]==v['storeys']-1):fail('STAIR_LINK','A single-floor staircase needs roof terrace access enabled, or a linked stair on another floor.',st['id'])
        if fs!=list(range(fs[0],fs[0]+len(fs))):fail('STAIR_FLOORS','Link staircase spaces in ascending, consecutive floor order.',st['id'])
        if any(i in linked for i in ids):fail('STAIR_DUPLICATE','A staircase space is linked more than once.',st['id'])
        linked.update(ids);p=polys[ids[0]];x,y,x1,y1=p.bounds
        risers=math.ceil(v['floor_height_mm']/190/2)*2;steps=risers//2-1
        width=2*st['flightWidth']+st['well'];depth=2*st['landing']+steps*st['tread']
        from .stair_geometry import point as stair_point, shape as stair_shape
        frame=dict(x=x,y=y,width=width,depth=depth,rotation=st.get('rotation',0))
        fitw,fitd=(depth,width) if frame['rotation']==90 else (width,depth)
        if abs(p.area-(x1-x)*(y1-y))>1 or x1-x<fitw or y1-y<fitd:fail('STAIR_FIT',f'U stair needs a clear {width:g} × {depth:g} mm core for this floor height.',st['id'])
        for j,ident in enumerate(ids):
            f=fs[j]
            open_sides=['right'] if frame['rotation']==90 and y1-y>width else []
            landing_room=polys[ident];lx,ly,lx1,ly1=landing_room.bounds
            # Enclosing arrival space can vary; the aligned flights and slab hole cannot.
            if abs(lx-x)>.1 or abs(ly-y)>.1 or abs(landing_room.area-(lx1-lx)*(ly1-ly))>1 or lx1-lx<fitw or ly1-ly<fitd:
                fail('STAIR_ALIGNMENT','Linked stair rooms must contain the same aligned stair core.',ident,f)
            for o in openings:
                if ident not in o['connects'] or o['kind']=='window':continue
                host=next(w for w in walls if w['id']==o['wall_id']);mid=LineString([host['a'],host['b']]).interpolate(o['offset']+o['width']/2)
                axis=LineString([host['a'],host['b']])
                start=axis.interpolate(o['offset']);end=axis.interpolate(o['offset']+o['width'])
                mid=Point(stair_point(frame,mid.coords[0],inverse=True))
                start=Point(stair_point(frame,start.coords[0],inverse=True));end=Point(stair_point(frame,end.coords[0],inverse=True))
                # Full-height open-plan sides are not doors into a flight: the
                # opening must include a usable front landing; rails guard the well.
                open_side=(o['kind']=='cased' and o['height']==host['height'] and
                           abs(start.x-end.x)<.1 and
                           min(max(start.y,end.y),y+st['landing'])-max(min(start.y,end.y),y)>=750)
                if open_side:open_sides.append('left' if mid.x<x+width/2 else 'right')
                elif mid.y>y+st['landing']+.1:fail('STAIR_ACCESS','Stair doors must enter the front landing, clear of both flights.',o['id'],f)
            stairs.append({'id':st['id']+'-'+str(f),'linkId':st['id'],'roomId':ident,'floor':f,'x':x,'y':y,'width':width,'depth':depth,
                           **({'rotation':90} if frame['rotation']==90 else {}),'flight_width':st['flightWidth'],'well':st['well'],'riser_count':risers,'riser_mm':v['floor_height_mm']/risers,
                           'tread_mm':st['tread'],'landing_mm':st['landing'],'to_floor':fs[j+1] if j+1<len(fs) else None})
            if open_sides:stairs[-1]['open_sides']=sorted(set(open_sides))
            if j:
                hole=stair_shape(frame,box(x,y+st['landing'],x+width,y+depth))
                plates[f]['regions']=regions(geometry(plates[f]['regions']).difference(hole));plates[f]['openings'].append({'id':st['id']+'-void-'+str(f),'stairId':st['id'],'regions':regions(hole)})
                for side in sorted(set(open_sides)):
                    xx=x if side=='left' else x+width
                    guards.append({'id':st['id']+f'-well-guard-{f}-{side}','owner':ident,'floor':f,
                                   'points':[stair_point(frame,[xx,y+st['landing']]),stair_point(frame,[xx,y+depth])],'height':1100})
    for s in spaces:
        if s['kind']=='stair' and s['id'] not in linked:fail('UNLINKED_STAIR','Link this staircase to its corresponding space on the next floor.',s['id'],s['floor'])
    # No automatic structure: unsupported projections and obstructions over an open terrace are blocked.
    for f in range(1,v['storeys']):
        outline=geometry(plates[f]['outline']);below=geometry(plates[f-1]['outline'])
        if outline.difference(below.buffer(.1)).area>1:fail('UNSUPPORTED_FLOOR','Upper-floor geometry projects beyond the supporting floor below.',plan['floors'][f]['id'],f)
        for s in spaces:
            if s['floor']<f and ((s['kind'] in OPEN_SKY and s['kind']!='void') or s.get('openToSky')):
                if outline.intersection(polys[s['id']]).area>1:fail('OPEN_SKY_BLOCKED','A higher floor covers this open-air space. Move it or use a covered veranda.',s['id'],s['floor'])
    for s in spaces:
        if s['kind']=='void':
            if s['floor']==0:fail('VOID_LEVEL','A double-height void belongs on the floor above the room it opens into.',s['id'],s['floor'])
            below=unary_union([Polygon(q['clear']) for q in spaces if q['floor']==s['floor']-1 and q['walkable']])
            if not below.buffer(.1).covers(polys[s['id']]):fail('VOID_ALIGNMENT','The void must lie over occupied space on the floor below.',s['id'],s['floor'])
        if s['kind']=='lift-shaft' and s['floor']>0:
            below=[q for q in spaces if q['floor']==s['floor']-1 and q['kind']=='lift-shaft']
            if not any(polys[s['id']].symmetric_difference(polys[q['id']]).area<1 for q in below):fail('SHAFT_ALIGNMENT','Stack the shaft over a matching shaft on the floor below.',s['id'],s['floor'])
    for s in spaces:
        if s.get('gardenBed') and not any(q.get('openToSky') and q['floor']==s['floor']+1 and polys[q['id']].intersection(box(*s['gardenBed'])).area>1 for q in spaces):
            fail('GARDEN_DAYLIGHT','Place an open-sky void above the veranda garden.',s['id'],s['floor'])
    roofs=[]
    for f in range(v['storeys']):
        outline=geometry(plates[f]['outline']);covered=outline
        for s in spaces:
            if s['floor']==f and (s['kind'] in OPEN_SKY or s.get('openToSky')):covered=covered.difference(polys[s['id']])
        # Double-height voids receive their roof at the next occupied roof level, not above the lower room.
        if f+1<v['storeys']:
            for s in spaces:
                if s['floor']==f+1 and s['kind']=='void':covered=covered.difference(polys[s['id']])
            for opening in plates[f+1]['openings']:covered=covered.difference(geometry(opening['regions']))
        exposed=covered.difference(geometry(plates[f+1]['outline'])) if f+1<v['storeys'] else covered
        roofs.append({'id':'roof-'+plan['floors'][f]['id'],'floor':f,'regions':regions(exposed),'ceiling':regions(covered)})
        # Guard all exposed outdoor/void edges except solid walls and accessible same-level connections.
        for s in spaces:
            if s['floor']!=f or (s['kind'] not in OUTDOOR and s['kind'] not in NON_WALKABLE):continue
            if f==0 and s['kind'] not in NON_WALKABLE:continue
            p=polys[s['id']];other=unary_union([q for i,q in floor_polys[f].items() if i!=s['id'] and room_map[i][1]['kind'] not in NON_WALKABLE])
            wall_union=unary_union([Polygon(w['polygon']) for w in walls if w['floor']==f])
            edge=(p.boundary if s['kind'] in NON_WALKABLE else p.boundary.difference(other.buffer(.1))).difference(wall_union.buffer(.1))
            if s.get('openToSky'):
                # Shared terrace edges already carry a guard; retain guards on any indoor edges.
                outdoor_edges=unary_union([q.boundary for i,q in floor_polys[f].items() if room_map[i][1]['kind'] in OUTDOOR])
                edge=edge.difference(outdoor_edges.buffer(.1))
            for j,line in enumerate(get_parts(edge)):
                if line.geom_type=='LineString' and line.length>1:guards.append({'id':s['id']+'-guard-'+str(j),'owner':s['id'],'floor':f,'points':[list(c) for c in line.coords],'height':1100})
    overall=unary_union([geometry(p['outline']) for p in plates])
    if 'parkedCar' in plan:
        car=plan['parkedCar'];car_foot=box(car['x']-1010,car['y']-2100,car['x']+1010,car['y']+2100)
        site=box(-v['left_mm'],-v['front_mm'],v['width_mm']-v['left_mm'],v['depth_mm']-v['front_mm'])
        if not site.covers(car_foot) or car_foot.intersects(geometry(plates[0]['outline'])):
            fail('PARKED_CAR','Place the parked car inside the plot and outside the ground-floor rooms.')
    b={'schema':'floorforge.building/0.4','units':'mm','up':'Z','brief':v,'storeys':v['storeys'],
       'planning':{'method':'authoritative custom plan','custom':True,'schema':SCHEMA,'dimensions':'exact clear space in mm',**({'frontCourt':plan['frontCourt']} if 'frontCourt' in plan else {})},
       'footprint':regions(overall)[0]['polygon'],'footprint_holes':regions(overall)[0]['holes'],
       'plot':regions(box(-v['left_mm'],-v['front_mm'],v['width_mm']-v['left_mm'],v['depth_mm']-v['front_mm']))[0]['polygon'],
       'floors':[{'id':fl['id'],'index':f} for f,fl in enumerate(plan['floors'])],
       'spaces':spaces,'walls':walls,'openings':openings,'stairs':stairs,'floor_plates':plates,'roofs':roofs,'guards':guards,
       'planHash':intent['planHash'],'draftRevision':intent.get('draftRevision',0),'banner':__import__('floorforge').BANNER}
    if 'doorsClosed' in plan:b['planning']['doorsClosed']=plan['doorsClosed']
    if 'parkedCar' in plan:b['planning']['parkedCar']=plan['parkedCar']
    if 'facadeStyle' in plan:b['planning']['facadeStyle']=plan['facadeStyle']
    for space in spaces:
        if space.get('underStair'):
            host=next(q for q in spaces if q['id']==space['underStair'])
            host['area_m2']=round(host['area_m2']-space['area_m2'],6)
    counters=[]
    for o in openings:
        if not o.get('servingCounter'):continue
        connected=[s['kind'] for s in spaces if s['id'] in o['connects']]
        if 'outside' in o['connects'] or not ('kitchen' in connected or (len(connected)==2 and set(connected)<= {'living','family','hall','dining'})):
            fail('COUNTER_LOCATION','A serving counter belongs in an internal kitchen or living/dining connection.',o['id'],o['floor'])
        w=next(w for w in walls if w['id']==o['wall_id']);line=LineString([w['a'],w['b']]);a=line.interpolate(o['offset']);c=line.interpolate(o['offset']+o['width']/(1 if o.get('servingCounter')=='full' else 2))
        top=LineString([a,c]).buffer(225 if o.get('servingCounter')=='full' else 200,cap_style=2)
        counters.append({'id':o['id']+'-counter','kind':'serving-counter','floor':o['floor'],'openingId':o['id'],'roomIds':o['connects'],'height':950,'polygon':regions(top)[0]['polygon']})
    if counters:b['built_in_counters']=counters
    # Level landing and two intermediate treads at additional front glazed doors.
    entrance_steps=[]
    for o in openings:
        if o['floor']!=0 or o['kind'] not in ('door','glazed') or 'outside' not in o['connects']:continue
        w=next(w for w in walls if w['id']==o['wall_id'])
        if abs(w['a'][1]-half)>.01 or abs(w['b'][1]-half)>.01:continue
        a=w['a'][0]+o['offset'];c=a+o['width'];plinth=v['plinth_mm'];count=max(1,math.ceil(plinth/160))
        if 650+(count-1)*300>v['front_mm']:
            fail('ENTRANCE_STEPS','This front door needs more setback for its landing and entrance steps.',o['id'],0)
        for j in range(count):
            y0=-650-(count-1-j)*300;y1=y0+300 if j<count-1 else 0
            entrance_steps.append({'id':o['id']+'-step-'+str(j),'openingId':o['id'],'polygon':[[a-150,y0],[c+150,y0],[c+150,y1],[a-150,y1]],
                                   'bottom':-plinth,'top':-plinth+(j+1)*plinth/count})
    if entrance_steps:b['entrance_steps']=entrance_steps
    identifiers=[item['id'] for key in ('floors','spaces','walls','openings','stairs','floor_plates','roofs','guards') for item in b[key]]
    if len(identifiers)!=len(set(identifiers)):fail('OBJECT_ID_CONFLICT','An authored ID conflicts with a generated object ID; rename the authored ID.')
    return b


def side_at(poly,point):
    x0,y0,x1,y1=poly.bounds
    return min(zip(SIDES,[abs(point.y-y0),abs(point.x-x1),abs(point.y-y1),abs(point.x-x0)]),key=lambda a:a[1])[0]


def validate_custom(b):
    from .review import professional_screen, RULE_SOURCE
    errors=[];warnings=[];spaces=b['spaces'];by_id={s['id']:s for s in spaces}
    graph={s['id']:set() for s in spaces if s['walkable'] and not s.get('serviceOnly')};graph['outside']=set()
    def error(code,message,s,**kw):errors.append({'code':code,'message':message,'id':s['id'],'floor':s['floor'],**kw})
    for s in spaces:
        p=Polygon(s['clear']);spec=SPACE_REGISTRY[s['kind']];x0,y0,x1,y1=p.bounds
        if s['area_m2']+1e-6<spec['minimum_area_m2'] or min(x1-x0,y1-y0)+.1<spec['minimum_width_mm']:
            error('ROOM_MINIMUM',f"{s['name']} is {s['area_m2']:.2f} m² with a {min(x1-x0,y1-y0)/1000:.2f} m narrow side; this room type needs at least {spec['minimum_area_m2']:g} m² and {spec['minimum_width_mm']/1000:g} m. Enlarge it or choose the intended room type.",s,required_m2=spec['minimum_area_m2'],required_width_mm=spec['minimum_width_mm'])
        if s['kind']=='drying-room':
            vent=sum(o['width']*o['height']/1e6 for o in b['openings'] if s['id'] in o['connects'] and o['kind']=='window')
            if vent<.3:error('DRYING_VENTILATION','Drying room needs at least 0.3 m² of ventilation to open air.',s)
            if not s['drain']:error('DRYING_DRAIN','Specify drainage for the enclosed drying room.',s)
        if s['kind'] in ('living','drawing-room','bedroom','care-room','kitchen','study','family') and not any(o['kind'] in ('window','glazed') and s['id'] in o['connects'] for o in b['openings']):
            error('NO_EXTERNAL_WINDOW','Add a window or glazed opening to open air.',s)
    for o in b['openings']:
        if o['kind']=='window' or o.get('servingCounter')=='full':continue
        a,c=o['connects']
        if a in graph and c in graph:graph[a].add(c);graph[c].add(a)
        elif a in by_id:error('VOID_ACCESS','A door cannot provide access into a shaft or void.',by_id[a])
    # Semi-open decks and landings may join along a clear, unobstructed edge.
    for i,s in enumerate(spaces):
        if s['id'] not in graph:continue
        for q in spaces[i+1:]:
            if q['id'] not in graph or s['floor']!=q['floor'] or s.get('underStair')==q['id'] or q.get('underStair')==s['id']:continue
            edge=Polygon(s['clear']).boundary.intersection(Polygon(q['clear']).boundary)
            if edge.length>=800:
                graph[s['id']].add(q['id']);graph[q['id']].add(s['id'])
        if s['floor']==0 and s['kind'] in ('outer-lobby','veranda','drying-yard','courtyard'):
            # Only the outside perimeter of the ground floor is an entrance from the site.
            boundary=geometry(b['floor_plates'][0]['outline']).boundary
            if boundary.intersection(Polygon(s['clear']).boundary).length>=800:graph['outside'].add(s['id']);graph[s['id']].add('outside')
    for st in b['stairs']:
        if st['to_floor'] is None or st.get('roof_access'):continue
        other=next(q for q in b['stairs'] if q['linkId']==st['linkId'] and q['floor']==st['to_floor'])
        graph[st['roomId']].add(other['roomId']);graph[other['roomId']].add(st['roomId'])
    def reach(blocked=None):
        seen={'outside'};todo=['outside']
        while todo:
            for nxt in graph[todo.pop()]:
                if nxt not in seen and nxt!=blocked:seen.add(nxt);todo.append(nxt)
        return seen
    found=reach()
    for ident in sorted(set(graph)-found):error('UNREACHABLE','Add a continuous door/landing route from the main entrance.',by_id[ident])
    for s in spaces:
        if s['kind']=='bedroom' and len(found)==len(graph):
            cut=set(graph)-{s['id']}-reach(s['id'])
            if any(by_id[i]['kind'] not in ('bathroom','dress') for i in cut):error('BEDROOM_THROUGH_ROUTE','This bedroom is the only route to another occupied space.',s)
    if not any(o['kind']=='entry' for o in b['openings']):errors.append({'code':'NO_ENTRY','message':'Add a main ground-floor entry opening.'})
    professional_screen(b,warnings)
    for warning in list(warnings):
        if warning['code'] in ('LOW_DAYLIGHT','BATH_VENTILATION'):
            errors.append({**warning,'floor':by_id[warning['id']]['floor']});warnings.remove(warning)
    result={'status':'blocked' if errors else 'preliminary_geometry_pass','errors':errors,'warnings':warnings,
            'checks':['exact clear geometry','setback and wall allowance','opening bounds and overlap','room minimums','connected access graph',
                      'aligned stair cores and slab openings','upper-floor support envelope','open-sky clearance','drying ventilation and drainage','exposed-edge guards'],
            'rule_source':RULE_SOURCE,'regulatory':'NOT EVALUATED','structural':'NOT DESIGNED','accessibility':'NOT CERTIFIED',
            'construction_ready':False,'graph':{k:sorted(x) for k,x in graph.items()},'planHash':b['planHash'],
            'disclaimer':b['banner']}
    for item in errors:
        if item.get('id') in by_id:item['name']=by_id[item['id']]['name']
    if errors:raise DesignError('CUSTOM_PLAN_INVALID','Resolve the highlighted plan conflicts before generating.',result)
    return result
