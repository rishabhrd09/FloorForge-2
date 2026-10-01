"""Explicit room-first preparation: small translations, existing stair links and openings.

Never resizes a room, invents occupied floors or replaces a user's plan with a template.
The returned plan is an undoable proposal; ordinary generation stays authoritative.
"""
from __future__ import annotations
import copy
import numpy as np
from scipy.optimize import linprog
from shapely.geometry import Polygon
from .spaces import SPACE_REGISTRY
from .model import DesignError


def fit_wall_spacing(plan, width, depth, fixed_floors=()):
    changes=[];t=plan['wallThickness'];limit=250
    for f,fl in enumerate(plan['floors']):
        if f in fixed_floors:continue
        rooms=fl['rooms'];n=len(rooms)
        # Complex shapes and hand-authored partitions remain exact. No bounding-box substitute.
        if not rooms or fl['walls'] or any(abs(Polygon(r['polygon']).area-Polygon(r['polygon']).envelope.area)>.1 for r in rooms):continue
        boxes=[Polygon(r['polygon']).bounds for r in rooms];bounds=[];rows=[];rhs=[];eq=[];eqrhs=[]
        for r,(x,y,x1,y1) in zip(rooms,boxes):
            pad=t if SPACE_REGISTRY[r['kind']]['enclosed'] else 0
            # Stair geometry is shared across floors; never shift a single core independently.
            allowance=0 if r['kind']=='stair' else limit
            lo=max(-allowance,pad-x);hi=min(allowance,width-pad-x1)
            bottom=max(-allowance,pad-y);top=min(allowance,depth-pad-y1)
            bounds.extend([(lo,hi),(bottom,top)])
        if any(lo>hi for lo,hi in bounds):continue
        for i in range(n):
            for j in range(i):
                a,b,c,d=boxes[j];x,y,x1,y1=boxes[i]
                choices=[(x-c,0,j,i),(a-x1,0,i,j),(y-d,1,j,i),(b-y1,1,i,j)]
                separation,axis,left,right=max(choices,key=lambda v:v[0])
                gap=t if all(SPACE_REGISTRY[rooms[k]['kind']]['enclosed'] for k in (i,j)) else 0
                row=np.zeros(4*n);row[2*left+axis]=1;row[2*right+axis]=-1
                # Keep existing shared walls joined, including their authored opening hosts.
                cross_overlap=min(boxes[i][3-axis],boxes[j][3-axis])-max(boxes[i][1-axis],boxes[j][1-axis])
                if gap and cross_overlap>450 and -.1<=separation<=gap+.1:
                    eq.append(row);eqrhs.append(separation-gap)
                else:rows.append(row);rhs.append(separation-gap)
        for i in range(2*n):
            row=np.zeros(4*n);row[i]=1;row[2*n+i]=-1;rows.append(row);rhs.append(0)
            row=np.zeros(4*n);row[i]=-1;row[2*n+i]=-1;rows.append(row);rhs.append(0)
        objective=np.r_[np.zeros(2*n),[1+i*1e-5 for i in range(2*n)]]
        result=linprog(objective,A_ub=np.array(rows),b_ub=np.array(rhs),A_eq=np.array(eq) if eq else None,b_eq=np.array(eqrhs) if eq else None,bounds=bounds+[(0,None)]*(2*n),method='highs')
        if not result.success:continue
        for i,r in enumerate(rooms):
            dx,dy=[round(float(v),3) for v in result.x[2*i:2*i+2]]
            if abs(dx)+abs(dy)<.01:continue
            r['polygon']=[[round(x+dx,3),round(y+dy,3)] for x,y in r['polygon']]
            changes.append({'kind':'wall-spacing','id':r['id'],'floor':f,'dx':dx,'dy':dy,'message':f"{r['name']}: adjusted position by {max(abs(dx),abs(dy))/1000:g} m to make space for walls; room size kept."})
    return changes


def link_existing_stairs(plan, roof_access):
    linked={i for st in plan['stairs'] for i in st['roomIds']};changes=[]
    for f,fl in enumerate(plan['floors']):
        for room in fl['rooms']:
            if room['kind']!='stair' or room['id'] in linked:continue
            peers=[room];shape=Polygon(room['polygon'])
            for upper in plan['floors'][f+1:]:
                peer=next((r for r in upper['rooms'] if r['kind']=='stair' and r['id'] not in linked and Polygon(r['polygon']).equals(shape)),None)
                if not peer:break
                peers.append(peer)
            if len(peers)<2 and not (roof_access and f==len(plan['floors'])-1):continue
            ids=[r['id'] for r in peers];ident='assist-core-'+room['id']
            plan['stairs'].append({'id':ident,'roomIds':ids,'flightWidth':1000,'well':200,'landing':1050,'tread':250});linked.update(ids)
            changes.append({'kind':'stair-link','id':room['id'],'floor':f,'message':'Connected the aligned staircase rooms'+(' to the roof terrace.' if roof_access and f+len(peers)==len(plan['floors']) else ' across floors.')})
    return changes


def prepare_plan(project, fixed_floors=()):
    from .intent import fuse
    from .layout import generate_layout
    from .review import validate
    from .plan_tools import suggest_openings
    intent=fuse(project)
    if not intent.get('customPlan'):raise DesignError('CUSTOM_PLAN_REQUIRED','Open the room planner first.')
    plan=copy.deepcopy(intent['customPlan']);v=intent['values']
    changes=fit_wall_spacing(plan,v['width_mm']-v['left_mm']-v['right_mm'],v['depth_mm']-v['front_mm']-v['rear_mm'],fixed_floors)
    changes+=link_existing_stairs(plan,v.get('roof_access'))
    frozen={f:copy.deepcopy(plan['floors'][f]) for f in fixed_floors}
    candidate={**project,'customPlan':plan};errors=[];valid=False
    try:
        proposed=suggest_openings(fuse(candidate));plan=proposed['customPlan']
        for f,fl in frozen.items():plan['floors'][f]=fl
        candidate['customPlan']=plan
        if proposed['added']:changes.append({'kind':'openings','message':f"Added {proposed['added']} doors and windows. You can move or edit them in Fine-tune."})
        final=fuse(candidate);validate(generate_layout(final));valid=True
    except DesignError as error:
        errors=(error.details or {}).get('errors') or [{'code':error.code,'message':str(error)}]
    final=fuse({**candidate,'customPlan':plan})
    return {'customPlan':final['customPlan'],'changes':changes,'valid':valid,'errors':errors,'planHash':final['planHash'],
            'draftRevision':intent.get('draftRevision',0),
            'message':'Your plan is ready to preview.' if valid else 'Your draft is saved. Let’s finish the highlighted part before previewing.'}
