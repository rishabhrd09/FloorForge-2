"""Deterministic corridor-and-public-hub packing with true polygon support."""
from __future__ import annotations
from .model import *
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union
from shapely import get_parts
import numpy as np

PUBLIC={'living','dining','hall','family','foyer'}
WET={'bathroom','utility'}

def coords(poly): return [[round(float(x),3),round(float(y),3)] for x,y in list(poly.exterior.coords)[:-1]]

def automatic_spaces(v, placement_hints=()):
    """Planned rooms for a brief (floorforge.planner), the stair records, the footprint and the planned doors."""
    from shapely.affinity import scale
    from . import planner
    W=v['width_mm']-v['left_mm']-v['right_mm']; D=v['depth_mm']-v['front_mm']-v['rear_mm']
    if v['variant']==2:D=round(D*.90)
    if W<5400 or D<6300: raise DesignError('ENVELOPE_TOO_SMALL','Usable envelope is too small for this generator. Review plot and setback assumptions.')
    if v['parking'] and v['front_mm']<5500:
        raise DesignError('PARKING_DEPTH','Requested parking needs a 5.5 m depth assumption. Increase front open space or remove parking; no car was silently inserted.')
    n=v['storeys']; total=v['bedrooms']
    if total<n: raise DesignError('PROGRAMME_SPLIT','The bounded guide planner requires at least one bedroom per floor. Use Custom Plan for a different programme.')
    try:
        (house,floors,Wp,Dp,cost,params),W,D=planner._cached(planner.plan_key(v,placement_hints))
    except DesignError as error:
        if placement_hints:
            detail=error.details if isinstance(error.details,dict) else {}
            error.details={**detail,'rooms':detail.get('rooms') or list(placement_hints)}
        raise
    # Variants are geometric mirrors, never a change to the road/north interpretation; Vastu may pick the hand.
    mirror,hand_scores=planner.choose_hand(house,floors,Wp,Dp,v)
    vastu_preferred_mirror=planner.vastu_hand(house,floors,Wp,Dp,v)[0]
    placement_mirror=mirror if placement_hints else None
    # A direct room-position instruction outranks the survey's generic "mirrored hub" variant. Without a placement
    # instruction, variant 1 retains its original deterministic mirror behaviour.
    variant_mirror_superseded=bool(placement_hints and v['variant']==1)
    if v['variant']==1 and not placement_hints: mirror=not mirror
    vastu_mirror=bool(not placement_hints and v.get('vastu')!='off' and mirror and vastu_preferred_mirror)
    spaces=[];access={}
    for f,rooms in enumerate(floors):
        for r in rooms:
            poly=planner.union_polygon(r.rects)
            if mirror: poly=scale(poly,xfact=-1,yfact=1,origin=(Wp/2,0))
            sid=f'F{f}-{r.key}'
            spaces.append(Space(sid,r.name,r.kind,f,coords(poly)))
            if r.access:
                near=r.prefer
                if near is not None and mirror: near=(Wp-near[0],near[1])
                access[sid]={'from':f'F{f}-{r.access}','near':None if near is None else [round(near[0]),round(near[1])],
                             'opening':r.opening,'width':r.dw}
    stairs=[]
    if n>1:
        for f in range(n):
            s={'id':f'ST-{f}','floor':f,'x':250,'y':250,'width':2200,'depth':4100,
               'flight_width':1000,'well':200,'riser_count':18,'riser_mm':v['floor_height_mm']/18,
               'tread_mm':250,'landing_mm':1050,'to_floor':f+1 if f+1<n else None}
            if mirror: s['x']=Wp-s['x']-s['width'];s['mirrored']=True
            stairs.append(s)
    ensuites=sum(1 for rooms in floors for r in rooms if r.role=='ensuite')
    placement=None
    if placement_hints:
        placement=planner.placement_audit(house,floors,Wp,Dp,mirror)
        supplied={(h.get('floor'),h['label']):h for h in placement_hints}
        for item in placement['matched']:
            original=supplied.get((item['floor'],item['label'])) or supplied[(None,item['label'])]
            if 'cells' in original:item['target_cells']=original['cells']
            if 'phrase' in original:item['phrase']=original['phrase']
        if placement['unmatched']:
            raise DesignError('PLACEMENT_UNMATCHED','The automatic programme cannot represent every requested spatial-guide room.',
                              {'labels':placement['unmatched'],'rooms':[h for h in placement_hints if h['label'] in placement['unmatched'] and not any(i['label']==h['label'] and i['floor']==h.get('floor') for i in placement['matched'])],'advice':'Align room labels with the bedroom count and enabled must-haves.'})
        unsatisfied=[item for item in placement['matched'] if item['status']=='unsatisfied']
        if unsatisfied:
            raise DesignError('PLACEMENT_UNSATISFIED','The bounded planner could not honour every requested relative room position.',
                              {'rooms':[{'label':x['label'],'floor':x['floor'],'cells':x.get('target_cells',[]),'distance_cells':x['distance_cells'],'zone_match':x['zone_match'],
                                         'target_normalized':x['target_normalized'],'actual_normalized':x['actual_normalized']} for x in unsatisfied],
                               'tolerance_cells':placement['tolerance_cells'],'advice':'Move the room nearer its broad front/rear or left/right zone, or simplify competing hints.'})
    planning={'method':'parti search scored against residential planning rules (floorforge/planner.py)',
              'parti':'three-row: living | kitchen, dining, services | suites' if params['gmode']=='three' else 'compact: living and dining | kitchen and suites',
              'envelope_mm':[W,D],'footprint_mm':[Wp,Dp],'score':round(cost,2),'mirrored':mirror,'vastu_mirrored':vastu_mirror,
              'placement_mirrored':placement_mirror,'vastu_preferred_mirror':vastu_preferred_mirror,
              'variant_mirror_superseded':variant_mirror_superseded,'hand_scores':hand_scores,
              'attached_baths':{'requested':house.attached,'provided':ensuites},
              'rules':'NBC 2016 Part 3 style minimums (hard) with comfortable targets, proportions, light and air, wet-area clustering and circulation economy (scored)'}
    if placement:planning['placement']=placement
    return spaces,stairs,box(0,0,Wp,Dp),access,planning


def grid_spaces(grid,v):
    if not isinstance(grid,dict) or set(grid)-{'cell_mm','floors','footprint'}:
        raise DesignError('GRID_SCHEMA','Grid accepts cell_mm, floors and optional footprint polygon.')
    cell=grid.get('cell_mm',1000)
    if type(cell) is not int or not 250<=cell<=3000: raise DesignError('GRID_CELL','Cell size must be 250-3000 mm.')
    floors=grid.get('floors',[])
    if len(floors)!=v['storeys']: raise DesignError('GRID_FLOORS','Grid floor count must match the requested storeys.')
    if v['storeys']>1: raise DesignError('GRID_STAIRS_REVIEW','Multi-storey manual grids require an aligned stair contract not yet supported. Automatic G+1 remains available.')
    spaces=[]; footprints=[]
    names={'living':'Living','dining':'Dining','bedroom':'Bedroom','kitchen':'Kitchen','bathroom':'Bathroom','utility':'Utility','hall':'Hall','study':'Study','pooja':'Pooja','store':'Store'}
    for f,rows in enumerate(floors):
        if not isinstance(rows,list) or not rows or len(rows)>40: raise DesignError('GRID_ROWS','Use 1-40 rows per floor.')
        if any(not isinstance(r,list) or len(r)!=len(rows[0]) or len(r)>40 for r in rows): raise DesignError('GRID_RECT','Grid rows must have equal length, at most 40 cells.')
        groups={}
        for y,row in enumerate(rows):
            for x,name in enumerate(row):
                if not name: continue
                if not isinstance(name,str) or not __import__('re').fullmatch(r'[a-z]+(?:-[0-9]+)?',name): raise DesignError('GRID_LABEL','Use room labels such as bedroom-1, kitchen, hall.')
                kind=name.split('-')[0]
                if kind not in names: raise DesignError('GRID_KIND',f'Unsupported grid room: {kind}')
                groups.setdefault(name,[]).append(box(x*cell,y*cell,(x+1)*cell,(y+1)*cell))
        polygons=[]
        for name,parts in sorted(groups.items()):
            p=unary_union(parts)
            if p.geom_type!='Polygon' or p.interiors: raise DesignError('GRID_CONNECTED',f'{name} must be connected and cannot contain a hole.')
            spaces.append(Space(f'F{f}-{name}',names[name.split('-')[0]]+' '+name.split('-')[-1] if '-' in name else names[name],name.split('-')[0],f,coords(p)))
            polygons.append(p)
        footprint=unary_union(polygons)
        if footprint.geom_type!='Polygon' or footprint.interiors: raise DesignError('FOOTPRINT_CONNECTED','Manual footprint must be one connected polygon without holes in this release.')
        footprints.append(footprint)
    envelope=box(0,0,v['width_mm']-v['left_mm']-v['right_mm'],v['depth_mm']-v['front_mm']-v['rear_mm'])
    if not envelope.covers(footprints[0]): raise DesignError('GRID_OUTSIDE','Painted layout exceeds the available envelope; grid cells were not resized.')
    if sum(s.kind=='bedroom' for s in spaces)!=v['bedrooms']: raise DesignError('GRID_BEDROOM_COUNT','Grid bedroom count must match the brief; repeated cells with the same name are one room.')
    if grid.get('footprint'):
        declared=Polygon(grid['footprint'])
        if not declared.is_valid or declared.symmetric_difference(footprints[0]).area>1:
            raise DesignError('GRID_FOOTPRINT','Declared footprint must match painted cells.')
    return spaces,[],footprints[0],None,None


def derive_walls(spaces,footprint,v):
    result=[]
    for floor in range(v['storeys']):
        rooms=[s for s in spaces if s.floor==floor]; polys={s.id:Polygon(s.polygon) for s in rooms}; kinds={s.id:s.kind for s in rooms}
        edges=unary_union([p.boundary for p in polys.values()])
        segments=[]
        for line in get_parts(edges):
            points=list(line.coords)
            for a,b in zip(points,points[1:]):
                if a>b:a,b=b,a
                if math.dist(a,b)>1: segments.append((tuple(a),tuple(b)))
        segments=sorted(set(segments))
        for a,b in segments:
            seg=LineString([a,b]);mid=seg.interpolate(.5,normalized=True)
            adjacent=sorted(k for k,p in polys.items() if p.boundary.distance(mid)<.1)
            if len(adjacent)>2: raise DesignError('TOPOLOGY','More than two rooms share an edge.')
            if len(adjacent)==2:
                ks={kinds[k] for k in adjacent}
                if ks.issubset(PUBLIC) or ks=={'stair','living'} or ks=={'stair','dining'} or ks=={'stair','family'}:
                    continue
            external=len(adjacent)==1
            if external and kinds[adjacent[0]] in ('terrace','veranda'):continue
            t=230 if external or any(kinds[r]=='terrace' for r in adjacent) else 150
            # One-sided external thickness, centred internal thickness.
            poly=seg.buffer(t if external else t/2,cap_style=3,join_style=2).intersection(footprint)
            if poly.geom_type!='Polygon':raise DesignError('WALL_POLYGON','Unsupported split wall.')
            dx,dy=b[0]-a[0],b[1]-a[1];ln=math.hypot(dx,dy)
            if external:
                normal=(-dy/ln,dx/ln)
                if not footprint.covers(Point(mid.x+normal[0],mid.y+normal[1])): normal=(-normal[0],-normal[1])
                a=(a[0]+normal[0]*t/2,a[1]+normal[1]*t/2);b=(b[0]+normal[0]*t/2,b[1]+normal[1]*t/2)
            w=Wall(f'F{floor}-W{len(result)+1:03d}',floor,list(a),list(b),t,v['floor_height_mm']-150,adjacent,external,coords(poly))
            result.append(w)
        wall_union=unary_union([Polygon(w.polygon) for w in result if w.floor==floor])
        for s in rooms:
            clear=Polygon(s.polygon).difference(wall_union)
            if clear.geom_type!='Polygon' or not clear.is_valid or clear.is_empty:
                raise DesignError('CLEAR_SPACE','Wall thickness leaves an invalid clear room: '+s.name)
            s.clear=coords(clear);s.area_m2=round(clear.area/1e6,4)
    return result


def _door_on(walls,sid,parent,near,width):
    """The wall between two rooms and the door offset on it nearest `near`, 150 mm clear of either end."""
    best=None
    for w in walls:
        if set(w.rooms)!={sid,parent}: continue
        a=np.array(w.a,float);b=np.array(w.b,float);L=float(np.linalg.norm(b-a))
        if L<width+300: continue
        u=(b-a)/L
        if near is None: t=L/2;d=0.
        else:
            q=np.array(near,float);t=float(np.clip(np.dot(q-a,u),0,L));d=float(np.linalg.norm(a+u*t-q))
        t=min(max(t,150+width/2),L-150-width/2)
        key=(round(d),-L)
        if best is None or key<best[0]:best=(key,w,t-width/2,L)
    return None if best is None else best[1:]


def entry_offset(w,length,width,spaces):
    a=np.array(w.a,float);b=np.array(w.b,float);u=(b-a)/length
    ground=[s for s in spaces if s.floor==0]
    stair=next((Polygon(s.polygon) for s in ground if s.kind=='stair'),None)
    hall=next((Polygon(s.polygon) for s in ground if s.kind=='hall'),None)
    lo,hi=700,length-700-width
    if hi<lo:return (length-width)/2
    if stair is not None and stair.distance(Point(*a))<400 or stair is not None and stair.distance(Point(*b))<400:
        near_a=stair.distance(Point(*a))<=stair.distance(Point(*b))
        return lo if near_a else hi
    if hall is not None:
        # Toward the end of the facade nearer the hall, so the other end keeps room for a drive.
        t=float(np.dot(np.array(hall.centroid.coords[0])-a,u))
        return lo if t<=length/2 else hi
    return (length-width)/2


def derive_openings(spaces,walls,v,access=None):
    output=[];kind={s.id:s.kind for s in spaces}
    def add(w,target,offset,width,sill,height,swing=None,hinge='start'):
        output.append(Opening(f'F{w.floor}-{("N" if target=="window" else "D")}{len(output)+1:03d}',w.id,w.floor,target,
                              round(offset),width,sill,height,list(w.rooms)+(['outside'] if w.external else []),swing,hinge))
    if access is not None:
        # Planned doors: each room opens off the room it is entered from, at the planned spot (near a corner, clear
        # of the counter, off the hall), hinged on the jamb nearer the corner so the leaf folds back against a wall.
        for sid,a in sorted(access.items()):
            parent=a['from']
            if kind.get(parent) is None: raise DesignError('PLAN_ACCESS','A planned room opens off a missing room: '+sid)
            if kind[sid] in PUBLIC and kind[parent] in PUBLIC: continue
            opening=a['opening'];width=a['width']
            if opening=='cased' and kind[sid]=='kitchen':width=1500
            target={'door':'door','cased':'cased','sliding':'glazed'}[opening]
            found=_door_on(walls,sid,parent,a['near'],width)
            if found is None and width>900:
                width=900;found=_door_on(walls,sid,parent,a['near'],width)
            if found is None:
                if any(set(w.rooms)=={sid,parent} for w in walls): raise DesignError('PORTAL_WIDTH','A room connection is too narrow: '+sid)
                continue
            w,offset,L=found
            height=2300 if target=='glazed' else 2100
            hinge='start' if offset<=L-offset-width else 'end'
            add(w,target,offset,width,0,height,sid if target=='door' else None,hinge)
    else:
        preferred={}
        # A private/service room receives one deliberate public portal, not a door
        # on every shared edge. Prefer the hall; keep toilets off the living facade.
        for room in spaces:
            if room.kind in PUBLIC or room.kind=='stair': continue
            options=[]
            for wall in walls:
                if room.id not in wall.rooms or len(wall.rooms)!=2: continue
                other=next(r for r in wall.rooms if r!=room.id)
                if kind[other] not in PUBLIC or math.dist(wall.a,wall.b)<1150:continue
                rank=(3 if kind[other]=='hall' else 1)
                if room.kind=='kitchen' and kind[other]=='dining':rank=4
                options.append((rank,math.dist(wall.a,wall.b),wall.id))
            if options:preferred[room.id]=max(options)[2]
        for w in walls:
            length=math.dist(w.a,w.b)
            if length<900 or len(w.rooms)!=2: continue
            ks={kind[r] for r in w.rooms}
            if not ks.intersection(PUBLIC): continue
            private=next((r for r in w.rooms if kind[r] not in PUBLIC),None)
            if private is None or preferred.get(private)!=w.id:continue
            other=kind[private];target=None;height=2100
            if other in ('bedroom','study','pooja','store','dress'): target='door';width=900
            elif other in ('bathroom','utility'):target='door';width=750
            elif other=='kitchen':target='cased' if v['open_kitchen'] else 'door';width=1500 if v['open_kitchen'] else 900
            elif other=='stair':target='cased';width=1100
            elif other in ('terrace','veranda'):target='glazed';width=1800;height=2300
            if not target: continue
            width=min(width,round(length-300))
            if width<700:raise DesignError('PORTAL_WIDTH','A room connection is too narrow.')
            # Doors sit near the end of the wall closer to the public room's middle, not in the middle of a room wall.
            offset=(length-width)/2;hinge='start'
            if target=='door':
                pub=next(r for r in w.rooms if r!=private);c=Polygon(next(s.polygon for s in spaces if s.id==pub)).centroid
                a=np.array(w.a,float);b=np.array(w.b,float)
                near_a=math.dist((c.x,c.y),a)<=math.dist((c.x,c.y),b)
                offset=150 if near_a else length-150-width
                hinge='start' if near_a else 'end'
            add(w,target,offset,width,0,height,private if target=='door' else None,hinge)
    for w in walls:
        if not w.external: continue
        length=math.dist(w.a,w.b)
        if length<900: continue
        target=None;width=0;sill=0;height=2150
        ks={kind[r] for r in w.rooms}
        if w.floor==0 and ks.intersection({'living','family','dining'}) and max(w.a[1],w.b[1])<240:
            if not any(o.kind=='entry' for o in output):target='entry';width=1200;height=2300
        if target is None and not ks.issubset({'stair'}) and not ks.intersection({'pooja','terrace'}):
            target='window';width=min(2100,round(length*.55));height=1450;sill=850
            if ks.intersection(WET):width=min(900,width);height=600;sill=1750
            if ks=={'utility'}:width=min(1200,round(length*.6));height=1050;sill=1000
            if ks.intersection({'living','drawing-room','dining','family'}):height=2200;sill=300
            if ks=={'kitchen'}:height=1150;sill=1100
            if ks=={'dress'}:width=min(900,width);height=1200;sill=1000
            if ks=={'store'}:width=min(600,width);height=450;sill=1800
            if ks=={'hall'}:width=min(900,width);height=1450;sill=850
            if width<600:target=None
            elif target=='window':
                # Stock sizes: windows in 300 mm steps from 600, ventilators 450/600/750/900.
                width=max([m for m in ((450,600,750,900) if sill>=1500 else (600,900,1200,1500,1800,2100,2400)) if m<=width] or [width])
        if target=='entry':
            # The front door sits beside the stair (a foyer at the foot of the flight) or on the axis of the hall that
            # leads to the rooms behind, never blindly in the middle of the living room; the rest of the frontage
            # stays free for the living room's window and for a drive.
            offset=entry_offset(w,length,width,spaces)
            room=next(r for r in w.rooms if kind[r] in ('living','family','dining'))
            add(w,'entry',offset,width,sill,height,room,'start' if offset<=length-offset-width else 'end')
            side,other=offset,length-offset-width
            lo,hi=(0,offset) if side>=other else (offset+width,length)
            if hi-lo>=1500:
                ww=min(2400,round(hi-lo-700))
                add(w,'window',lo+(hi-lo-ww)/2,ww,300,2200,None)
        elif target:
            add(w,target,(length-width)/2,width,sill,height,None)
    if not any(o.kind=='entry' for o in output):raise DesignError('NO_ENTRY','There is no public room on the road-facing edge for the entry. Paint a living room at the front.')
    return output


def generate_layout(intent):
    from .rooftop import add_roof_access
    v=intent['values']
    if intent.get('customPlan') is not None:
        from .custom_plan import compile_plan
        b = compile_plan(intent)
        b['input_audit'] = intent.get('input_audit')
        b['furnitureLayout'] = intent.get('furnitureLayout', [])
        return add_roof_access(b)
    grid=intent.get('grid')
    if intent.get('placement_hints'):
        from .plan_tools import guide_check
        check=guide_check(intent)
        if not check['valid']:raise DesignError('GUIDE_CONFLICT',check['message'],{'rooms':check['rooms']})
    exact_grid=grid and not (isinstance(grid,dict) and grid.get('mode')=='spatial_hint')
    spaces,stairs,footprint,access,planning=grid_spaces(grid,v) if exact_grid else automatic_spaces(v,intent.get('placement_hints',()))
    from .placement_edits import room_anchors, apply_room_edits
    anchors=room_anchors(spaces)
    apply_room_edits(spaces,stairs,footprint,access,intent.get('roomEdits',[]),anchors)
    walls=derive_walls(spaces,footprint,v);openings=derive_openings(spaces,walls,v,access)
    return add_roof_access({'roomEditBase':anchors,'roomEdits':intent.get('roomEdits',[]),'furnitureLayout':intent.get('furnitureLayout',[]),'input_audit':intent.get('input_audit'),'planHash':intent.get('planHash'),'draftRevision':intent.get('draftRevision',0),'schema':'floorforge.building/0.2','units':'mm','up':'Z','brief':v,'planning':planning or {'method':'manual grid'},
            'footprint':coords(footprint),'plot':coords(box(-v['left_mm'],-v['front_mm'],v['width_mm']-v['left_mm'],v['depth_mm']-v['front_mm'])),
            'floors':[{'id':(grid.get('floorIds') or [f'floor-{i}' for i in range(v['storeys'])])[f] if grid and grid.get('mode')=='spatial_hint' else f'floor-{f}','index':f} for f in range(v['storeys'])],'spaces':[asdict(s) for s in spaces],'walls':[asdict(w) for w in walls],'openings':[asdict(o) for o in openings],
            'stairs':stairs,'storeys':v['storeys'],'banner':__import__('floorforge').BANNER})
