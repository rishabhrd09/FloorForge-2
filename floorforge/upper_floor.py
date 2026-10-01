"""Floor-below guidance and explicit, undoable upper-floor starter proposals."""
from __future__ import annotations
import copy
import math
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from .spaces import SPACE_REGISTRY
from .model import DesignError

OPEN_SKY={'terrace','courtyard','drying-yard','void','balcony'}
def footprint(fl,t):
    return unary_union([Polygon(r['polygon']).buffer(t if SPACE_REGISTRY[r['kind']]['enclosed'] else 0,join_style=2) for r in fl['rooms']])

def usable(plan,floor):
    if floor<1 or floor>=len(plan['floors']):return Polygon()
    support=footprint(plan['floors'][floor-1],plan['wallThickness'])
    holes=unary_union([Polygon(r['polygon']) for fl in plan['floors'][:floor] for r in fl['rooms'] if r['kind'] in OPEN_SKY])
    return support.difference(holes)

def regions(shape):
    if shape.is_empty:return []
    parts=[shape] if shape.geom_type=='Polygon' else [g for g in shape.geoms if g.geom_type=='Polygon']
    return [{'polygon':[list(p) for p in g.exterior.coords[:-1]],'holes':[[list(p) for p in ring.coords[:-1]] for ring in g.interiors]} for g in parts]

def constraints(project,floor):
    from .intent import fuse
    intent=fuse(project);plan=intent.get('customPlan')
    if not plan or type(floor) is not int or not 0<floor<len(plan['floors']):
        raise DesignError('UPPER_FLOOR','Choose an upper floor with a floor below.')
    t=plan['wallThickness'];below=plan['floors'][floor-1];allowed=usable(plan,floor);issues=[]
    for r in plan['floors'][floor]['rooms']:
        shape=Polygon(r['polygon']).buffer(t if SPACE_REGISTRY[r['kind']]['enclosed'] else 0,join_style=2)
        if shape.difference(allowed.buffer(.1)).area>1:
            issues.append({'id':r['id'],'floor':floor,'code':'UPPER_FOOTPRINT','message':r['name']+' extends beyond the shaded floor below or covers an open-air area. Move it into the shaded area, or use Smart fit.'})
    stairs=[copy.deepcopy(r) for r in below['rooms'] if r['kind']=='stair']
    current=[r for r in plan['floors'][floor]['rooms'] if r['kind']=='stair']
    for r in stairs:
        x,y,x1,y1=Polygon(r['polygon']).bounds
        core=next((s for s in plan['stairs'] if r['id'] in s['roomIds']),{})
        width=2*core.get('flightWidth',1000)+core.get('well',200)
        depth=2*core.get('landing',1050)+(math.ceil(intent['values']['floor_height_mm']/190/2)-1)*core.get('tread',250)
        if core.get('rotation')==90:width,depth=depth,width
        if x1-x<width or y1-y<depth:issues.append({'id':r['id'],'floor':floor-1,'code':'STAIR_FIT','message':f"The staircase below is {(x1-x)/1000:g} × {(y1-y)/1000:g} m. This stair model needs {width/1000:g} × {depth/1000:g} m. Fit the lower staircase first, then continue it upstairs."})
        peers=[q for q in current if Polygon(q['polygon']).intersects(Polygon(r['polygon']))]
        if len(peers)>1:issues.append({'floor':floor,'code':'DUPLICATE_STAIR','ids':[q['id'] for q in peers],'message':'Two stairs overlap the connection from below. Keep one aligned staircase; select the extra stair and Delete, or preview Continue stairs.'})
        elif not any(Polygon(q['polygon']).equals(Polygon(r['polygon'])) for q in peers):
            issues.append({'floor':floor,'code':'STAIR_ALIGNMENT','id':peers[0]['id'] if peers else r['id'],'message':'Continue the staircase at the blue outline so the floors connect.'})
    return {'floor':floor,'supported':regions(allowed),'stairs':stairs,'openSky':[r for fl in plan['floors'][:floor] for r in fl['rooms'] if r['kind'] in OPEN_SKY],'issues':issues}

def starter(project,floor,stairs_only=False):
    from .intent import fuse
    from .plan_assist import prepare_plan
    constraints(project,floor)
    if type(stairs_only) is not bool:raise DesignError('UPPER_FLOOR','Choose whether to continue stairs only.')
    plan=copy.deepcopy(fuse(project)['customPlan'])
    target=plan['floors'][floor];below=plan['floors'][floor-1];old_ids={r['id'] for r in target['rooms']};changes=[]
    if not stairs_only:
        ids={r['id']:f"upper-{floor}-{r['id']}" for r in below['rooms'] if r['kind'] not in OPEN_SKY}
        target.update(rooms=[],walls=[],openings=[])
        for r in below['rooms']:
            if r['id'] not in ids:continue
            q=copy.deepcopy(r);q['id']=ids[r['id']]
            # A covered veranda below can support an accessible open terrace above.
            if q['kind']=='veranda':q['kind']='terrace';q['name']='Open terrace'
            target['rooms'].append(q)
        target['walls']=[{**copy.deepcopy(w),'id':f"upper-{floor}-{w['id']}"} for w in below['walls']]
        changes.append({'kind':'upper-starter','floor':floor,'message':'Suggested this floor from the rooms below, keeping their positions and clear sizes. Its previous layout is replaced only after Yes; Undo restores it.'})
        for core in plan['stairs']:core['roomIds']=[i for i in core['roomIds'] if i not in old_ids]
    for source in [r for r in below['rooms'] if r['kind']=='stair']:
        core=next((s for s in plan['stairs'] if source['id'] in s['roomIds']),None)
        peers=[r for r in target['rooms'] if r['kind']=='stair' and (r['id'] in (core or {}).get('roomIds',[]) or Polygon(r['polygon']).intersects(Polygon(source['polygon'])))]
        if len(peers)>1:
            # Only the linked duplicate can be chosen unambiguously. Leave the decision explicit.
            raise DesignError('DUPLICATE_STAIR','Two stairs overlap this connection. Select and delete the extra upper stair, then Continue stairs.',{'errors':[{'code':'DUPLICATE_STAIR','floor':floor,'ids':[r['id'] for r in peers],'message':'Keep one upper stair at the connection from below.'}]})
        peer=peers[0] if peers else {**copy.deepcopy(source),'id':f"upper-{floor}-{source['id']}",'name':'Staircase · '+['Ground','First','Second'][floor]}
        if not peers:target['rooms'].append(peer)
        peer['polygon']=copy.deepcopy(source['polygon'])
        if not core:
            core={'id':'upper-core-'+source['id'],'roomIds':[source['id']],'flightWidth':1000,'well':200,'landing':1050,'tread':250};plan['stairs'].append(core)
        if peer['id'] not in core['roomIds']:core['roomIds'].append(peer['id'])
        by_id={r['id']:f for f,fl in enumerate(plan['floors']) for r in fl['rooms']}
        core['roomIds'].sort(key=lambda i:by_id.get(i,99))
        changes.append({'kind':'stair-link','floor':floor,'id':peer['id'],'message':'Continued the staircase directly above the floor below; the lower staircase is unchanged.'})
    plan['stairs']=[s for s in plan['stairs'] if s['roomIds']]
    result=prepare_plan({**project,'customPlan':plan},fixed_floors=set(range(len(plan['floors'])))-{floor})
    return {**result,'proposal':True,'changes':changes+result['changes']}

def support_box(plan,floor,room):
    """Choose a containing orthogonal support rectangle near the sketch, including wall space."""
    allowed=usable(plan,floor)
    if allowed.is_empty:return None
    shape=Polygon(room['polygon']);pad=plan['wallThickness'] if SPACE_REGISTRY[room['kind']]['enclosed'] else 0
    clear=allowed.buffer(-pad,join_style=2) if pad else allowed
    if clear.is_empty:return None
    coords=[p for part in regions(clear) for ring in [part['polygon'],*part['holes']] for p in ring]
    xs=sorted({round(p[0],3) for p in coords});ys=sorted({round(p[1],3) for p in coords})
    if len(xs)>24 or len(ys)>24:
        candidates=[]
        for r in plan['floors'][floor-1]['rooms']:
            b=Polygon(r['polygon']).bounds
            if clear.buffer(.01).covers(box(*b)):candidates.append((shape.intersection(box(*b)).area,b))
        return max(candidates)[1] if candidates else None
    candidates=[]
    for i,x in enumerate(xs):
        for x1 in xs[i+1:]:
            for j,y in enumerate(ys):
                for y1 in ys[j+1:]:
                    if x1-x<600 or y1-y<600:continue
                    b=box(x,y,x1,y1)
                    # Favor the requested region and room coverage, then room to grow.
                    score=shape.intersection(b).area*10+b.area*.01-shape.centroid.distance(b)*1000
                    candidates.append((score,(x,y,x1,y1)))
    for _,bounds in sorted(candidates,reverse=True):
        if clear.buffer(.01).covers(box(*bounds)):return bounds
    return None
