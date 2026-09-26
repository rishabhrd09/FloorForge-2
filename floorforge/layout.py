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

def automatic_spaces(v):
    W=v['width_mm']-v['left_mm']-v['right_mm']; D=v['depth_mm']-v['front_mm']-v['rear_mm']
    if v['variant']==2:D=round(D*.90)
    if W<5400 or D<6300: raise DesignError('ENVELOPE_TOO_SMALL','Usable envelope is too small for this generator. Review plot and setback assumptions.')
    if v['parking'] and v['front_mm']<5500:
        raise DesignError('PARKING_DEPTH','Requested parking needs a 5.5 m depth assumption. Increase front open space or remove parking; no car was silently inserted.')
    n=v['storeys']; total=v['bedrooms']
    if total<n: raise DesignError('PROGRAMME_SPLIT','This two-floor generator requires at least one bedroom per floor.')
    counts=[total] if n==1 else [max(1,total//2),total-max(1,total//2)]
    if max(counts)>4: raise DesignError('PROGRAMME_CAPACITY','At most four bedrooms per floor in this bounded generator.')
    hall=1250 if W<7600 else 1500
    L=round((W-hall)/2); R=L+hall
    rear_min=3100; core_min=2350
    front=round(min(4400,max(3000,D*.31)))
    if n==2: front=4500
    core_end=front+max(2600,min(2800,round((D-front)*.35)))
    if D-core_end<3000: core_end=D-3000
    if core_end-front<2200 or (n==2 and L<2650):
        raise DesignError('PROGRAMME_DOES_NOT_FIT','The public zone, services and bedrooms do not fit. No extra storey has been added. Reduce the programme or setbacks only after local review.')
    spaces=[];stairs=[]
    def add(f,key,name,kind,p): spaces.append(Space(f'F{f}-{key}',name,kind,f,coords(p)))
    for f,num in enumerate(counts):
        if n==2:
            sw=2500; sd=4400
            add(f,'stair','Stair','stair',box(0,0,sw,sd))
            # Public L-shaped polygon; no invented rectangular bounding-box fill.
            pub=box(0,0,W,front).difference(box(0,0,sw,sd))
            if f==0:
                # Split connected public zones without walls.
                dining=pub.intersection(box(0,front*.58,W,front))
                living=pub.difference(dining)
                add(f,'living','Living','living',living); add(f,'dining','Dining','dining',dining)
            else:
                # A genuine open terrace, not a balcony pasted onto an unchanged facade.
                terrace=box(max(sw+1400,W*.54),0,W,1550 if v['style']!='tropical' else 1850)
                add(f,'living','Family lounge','family',pub.difference(terrace))
                add(f,'terrace','Open terrace','terrace',terrace)
            stairs.append({'id':f'ST-{f}','floor':f,'x':250,'y':250,'width':2200,'depth':4100,
                           'flight_width':1000,'well':200,'riser_count':18,'riser_mm':v['floor_height_mm']/18,
                           'tread_mm':250,'landing_mm':1050,'to_floor':f+1 if f+1<n else None})
        else:
            cut=round(W*.47)
            add(f,'dining','Dining','dining',box(0,0,cut,front))
            add(f,'living','Living','living',box(cut,0,W,front))
        compact_single=num==1 and W<8500
        hall_end=core_end if compact_single else min(D,core_end+1200) if num<=2 else D
        add(f,'hall','Hall','hall',box(L,front,R,hall_end))
        add(f,'kitchen','Kitchen' if f==0 else 'Study','kitchen' if f==0 else 'study',box(0,front,L,core_end))
        split=round(front+(core_end-front)*(.50 if f else .54))
        add(f,'bath','Bathroom','bathroom',box(R,front,W,split))
        add(f,'utility','Utility' if f==0 else 'Bathroom 2','utility' if f==0 else 'bathroom',box(R,split,W,core_end))
        if compact_single:
            add(f,'bedroom','Bedroom '+str((f and counts[0])+1),'bedroom',box(0,core_end,W,D))
            continue
        left_count=(num+1)//2;right_count=num//2
        for side, x0,x1,count in [('left',0,L,left_count),('right',R,W,right_count)]:
            count=max(count,1)
            for j in range(count):
                y0=core_end+round(j*(D-core_end)/count);y1=core_end+round((j+1)*(D-core_end)/count)
                kind='study' if side=='right' and right_count==0 else 'bedroom'
                key=f'{side}-{j}'
                name=('Care / study' if v['eldercare'] and f==0 else 'Study') if kind=='study' else ('Bedroom '+str((f and counts[0]) + (j+1 if side=='left' else left_count+j+1)))
                shape=box(x0,y0,x1,y1)
                if side=='left' and j==count-1 and hall_end<D:shape=shape.union(box(L,hall_end,R,D))
                add(f,key,name,kind,shape)
    # Variants are geometric mirrors, never a change to the road/north interpretation.
    if v['variant']==1:
        from shapely.affinity import scale
        for s in spaces: s.polygon=coords(scale(Polygon(s.polygon),xfact=-1,yfact=1,origin=(W/2,0)))
        for s in stairs: s['x']=W-s['x']-s['width'];s['mirrored']=True
    return spaces,stairs,box(0,0,W,D)


def grid_spaces(grid,v):
    if not isinstance(grid,dict) or set(grid)-{'cell_mm','floors','footprint'}:
        raise DesignError('GRID_SCHEMA','Grid accepts cell_mm, floors and optional footprint polygon.')
    cell=grid.get('cell_mm',1000)
    if type(cell) is not int or not 250<=cell<=3000: raise DesignError('GRID_CELL','Cell size must be 250-3000 mm.')
    floors=grid.get('floors',[])
    if len(floors)!=v['storeys']: raise DesignError('GRID_FLOORS','Grid floor count must match the requested storeys.')
    if v['storeys']>1: raise DesignError('GRID_STAIRS_REVIEW','Multi-storey manual grids require an aligned stair contract not yet supported. Automatic G+1 remains available.')
    spaces=[]; footprints=[]
    names={'living':'Living','dining':'Dining','bedroom':'Bedroom','kitchen':'Kitchen','bathroom':'Bathroom','utility':'Utility','hall':'Hall','study':'Study','pooja':'Pooja'}
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
    return spaces,[],footprints[0]


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
            if external and kinds[adjacent[0]]=='terrace':continue
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


def derive_openings(spaces,walls,v):
    output=[];kind={s.id:s.kind for s in spaces}
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
        if length<900: continue
        target=None;width=0;sill=0;height=2150
        ks={kind[r] for r in w.rooms}
        if len(w.rooms)==2:
            if ks.intersection(PUBLIC):
                private=next((r for r in w.rooms if kind[r] not in PUBLIC),None)
                if private and preferred.get(private)!=w.id:continue
                other=next((k for k in ks if k not in PUBLIC),None)
                if other in ('bedroom','study','pooja'): target='door';width=950
                elif other in ('bathroom','utility'):target='door';width=850
                elif other=='kitchen':target='cased' if v['open_kitchen'] else 'door';width=1500 if v['open_kitchen'] else 900
                elif other=='stair':target='cased';width=1100
                elif other=='terrace':target='glazed';width=1800;height=2300
            if target:
                width=min(width,round(length-300))
                if width<800:raise DesignError('PORTAL_WIDTH','A room connection is too narrow.')
        elif w.external:
            if w.floor==0 and ks.intersection({'living','family','dining'}) and max(w.a[1],w.b[1])<240:
                existing=any(o.kind=='entry' for o in output)
                if not existing:target='entry';width=1200;height=2300
            if target is None and not ks.issubset({'hall','stair'}):
                target='window';width=min(2100,round(length*.55));height=1450;sill=850
                if ks.intersection(WET):width=min(900,width);height=600;sill=1750
                if ks.intersection({'living','dining','family'}):height=2200;sill=300
                if ks=={'kitchen'}:height=1150;sill=1100
                if width<600:target=None
        if target:
            output.append(Opening(f'F{w.floor}-{("N" if target=="window" else "D")}{len(output)+1:03d}',w.id,w.floor,target,
                                  round((length-width)/2),width,sill,height,list(w.rooms)+(['outside'] if w.external else [])))
    if not any(o.kind=='entry' for o in output):raise DesignError('NO_ENTRY','There is no public room on the road-facing edge for the entry. Paint a living room at the front.')
    return output


def generate_layout(intent):
    v=intent['values']
    spaces,stairs,footprint=grid_spaces(intent['grid'],v) if intent.get('grid') else automatic_spaces(v)
    walls=derive_walls(spaces,footprint,v);openings=derive_openings(spaces,walls,v)
    return {'schema':'floorforge.building/0.2','units':'mm','up':'Z','brief':v,
            'footprint':coords(footprint),'plot':coords(box(-v['left_mm'],-v['front_mm'],v['width_mm']-v['left_mm'],v['depth_mm']-v['front_mm'])),
            'spaces':[asdict(s) for s in spaces],'walls':[asdict(w) for w in walls],'openings':[asdict(o) for o in openings],
            'stairs':stairs,'storeys':v['storeys'],'banner':__import__('floorforge').BANNER}
