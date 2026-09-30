"""Propose a fitted version of a rough room sketch. Applying it requires the UI's Yes.

Rectangle ordering, room IDs and floor assignments survive the fit. This is not
an alternate generation path: the ordinary compiler must validate the proposal.
"""
from __future__ import annotations
import copy
import math
import numpy as np
from scipy.optimize import linprog
from shapely.geometry import Polygon
from .intent import fuse
from .model import DesignError
from .spaces import SPACE_REGISTRY
from .plan_assist import prepare_plan


def fit_rectangles(plan, values, floor=None):
    width=values['width_mm']-values['left_mm']-values['right_mm']
    depth=values['depth_mm']-values['front_mm']-values['rear_mm']
    t=plan['wallThickness']
    entries=[(f,r) for f,fl in enumerate(plan['floors']) for r in fl['rooms']]
    if not entries:return []
    if len(entries)>100:raise DesignError('FIT_LIMIT','Fit up to 100 rooms at a time. Larger plans can still be edited in Fine-tune.')
    n=len(entries);size=8*n;boxes=[Polygon(r['polygon']).bounds for _,r in entries]
    rows=[];rhs=[];eq=[];eqrhs=[];bounds=[]
    def constraint(terms, value, equal=False):
        row=np.zeros(size)
        for index,coefficient in terms:row[index]+=coefficient
        (eq if equal else rows).append(row);(eqrhs if equal else rhs).append(value)
    for i,(f,r) in enumerate(entries):
        x,y,x1,y1=boxes[i];spec=SPACE_REGISTRY[r['kind']];pad=t if spec['enclosed'] else 0
        fixed=(floor is not None and f!=floor) or bool(plan['floors'][f]['walls']) or abs(Polygon(r['polygon']).area-(x1-x)*(y1-y))>.1
        bounds.extend([(v,v) for v in boxes[i]] if fixed else [(pad,width-pad),(pad,depth-pad),(pad,width-pad),(pad,depth-pad)])
        minimum=max(600,spec['minimum_width_mm']);area=spec['minimum_area_m2']*1e6
        if r['kind']=='dining':minimum=max(minimum,2400);area=max(area,6e6)
        if spec['circulation'] or not spec['enclosed']:minimum=max(minimum,1000)
        ratio=max(.65,min(1.55,(x1-x)/max(1,y1-y)))
        mw=max(minimum,math.sqrt(area*ratio));mh=max(minimum,area/mw if area else minimum)
        if r['kind']=='stair':
            core=next((s for s in plan['stairs'] if r['id'] in s['roomIds']),{})
            mw=2*core.get('flightWidth',1000)+core.get('well',200)
            steps=math.ceil(values['floor_height_mm']/190/2)-1
            mh=2*core.get('landing',1050)+steps*core.get('tread',250)
            if core.get('rotation')==90:mw,mh=mh,mw
        if floor is not None and f==floor and f>0:
            from .upper_floor import support_box
            limits=support_box(plan,f,r)
            if limits is None:raise DesignError('UPPER_FOOTPRINT',r['name']+' needs a usable footprint below.',{'errors':[{'code':'UPPER_FOOTPRINT','floor':f,'id':r['id'],'message':'Place this room above the shaded floor below.'}]})
            lx,ly,rx,ry=limits
            for k,lo,hi in ((0,lx,rx),(1,ly,ry),(2,lx,rx),(3,ly,ry)):
                constraint([(4*i+k,-1)],-lo);constraint([(4*i+k,1)],hi)
        # Rounding up prevents a sub-millimetre numerical result failing minimum checks.
        mw=math.ceil(mw);mh=math.ceil(mh)
        if floor is not None and f!=floor:mw=x1-x;mh=y1-y
        constraint([(4*i,1),(4*i+2,-1)],-mw)
        constraint([(4*i+1,1),(4*i+3,-1)],-mh)
        if not fixed:
            # Stay near the requested region even if a crowded sketch cannot be fitted.
            for axis,span in ((0,width),(1,depth)):
                center=boxes[i][axis]+boxes[i][axis+2]
                constraint([(4*i+axis,1),(4*i+axis+2,1)],center+span*.5)
                constraint([(4*i+axis,-1),(4*i+axis+2,-1)],-center+span*.5)
    # Preserve separation direction, and join nearby facing edges for automatic walls/doors.
    for i,(f,r) in enumerate(entries):
        for j in range(i):
            if entries[j][0]!=f or (floor is not None and f!=floor):continue
            a,b,c,d=boxes[j];x,y,x1,y1=boxes[i]
            gap,axis,left,right=max([(x-c,0,j,i),(a-x1,0,i,j),(y-d,1,j,i),(b-y1,1,i,j)],key=lambda q:q[0])
            wall=t if any(SPACE_REGISTRY[entries[k][1]['kind']]['enclosed'] for k in (i,j)) else 0
            cross=1-axis;overlap=min(boxes[i][cross+2],boxes[j][cross+2])-max(boxes[i][cross],boxes[j][cross])
            contact=gap<=800 and overlap>=min(600,(boxes[i][cross+2]-boxes[i][cross])*.4,(boxes[j][cross+2]-boxes[j][cross])*.4)
            constraint([(4*left+axis+2,1),(4*right+axis,-1)],-wall,contact)
            if contact:
                for aidx,bidx in ((i,j),(j,i)):
                    constraint([(4*aidx+cross,1),(4*bidx+cross+2,-1)],-1200)
    # Existing linked cores, plus already aligned unlinked cores, must move together.
    groups=[s['roomIds'] for s in plan['stairs']]
    for i,(_,r) in enumerate(entries):
        if r['kind']=='stair':groups.append([q['id'] for j,(_,q) in enumerate(entries) if q['kind']=='stair' and boxes[j]==boxes[i]])
    indices={r['id']:i for i,(_,r) in enumerate(entries)}
    for group in groups:
        for rid in group[1:]:
            if rid not in indices or group[0] not in indices:continue
            for k in range(4):constraint([(4*indices[rid]+k,1),(4*indices[group[0]]+k,-1)],0,True)
    targets=np.array(boxes).flatten()
    for k,v in enumerate(targets):
        constraint([(k,1),(4*n+k,-1)],v)
        constraint([(k,-1),(4*n+k,-1)],-v)
    objective=np.r_[np.zeros(4*n),[1+k*1e-6 for k in range(4*n)]]
    result=linprog(objective,A_ub=np.array(rows),b_ub=np.array(rhs),A_eq=np.array(eq) if eq else None,b_eq=np.array(eqrhs) if eq else None,bounds=bounds+[(0,None)]*(4*n),method='highs',options={'time_limit':5})
    if not result.success:
        raise DesignError('SMART_FIT_SPACE','These rooms cannot fit near these positions at usable sizes. Spread them into the empty area, remove a room, or enlarge the buildable area. Your sketch is unchanged.')
    changes=[]
    for i,(f,r) in enumerate(entries):
        old=boxes[i];x,y,x1,y1=[round(float(v),3) for v in result.x[4*i:4*i+4]]
        if all(abs(a-b)<.01 for a,b in zip(old,(x,y,x1,y1))):continue
        r['polygon']=[[x,y],[x1,y],[x1,y1],[x,y1]]
        before=[round((old[2]-old[0])/1000,3),round((old[3]-old[1])/1000,3)];after=[round((x1-x)/1000,3),round((y1-y)/1000,3)]
        changes.append({'kind':'smart-fit','id':r['id'],'floor':f,'before':before,'after':after,'message':f"{['Ground','First','Second'][f]} · {r['name']}: {before[0]:g} × {before[1]:g} → {after[0]:g} × {after[1]:g} m; fitted near your chosen position."})
    return changes


def smart_fit(project, floor=None):
    if floor is not None and (type(floor) is not int or not 0<=floor<len(project.get('customPlan',{}).get('floors',[]))):
        raise DesignError('UPPER_FLOOR','Choose an existing floor to fit.')
    fixed=set(range(len(project.get('customPlan',{}).get('floors',[]))))-{floor} if floor is not None else set()
    initial=prepare_plan(project,fixed_floors=fixed)
    resize_reasons={'ROOM_MINIMUM','SPACE_OVERLAP','WALL_CLEARANCE','WALL_SETBACK','SETBACK','STAIR_FIT','UNREACHABLE','UNSUPPORTED_FLOOR','OPEN_SKY_BLOCKED'}
    if initial['valid'] or not any(e['code'] in resize_reasons for e in initial['errors']):return {**initial,'proposal':True}
    intent=fuse(project);plan=copy.deepcopy(intent['customPlan'])
    try:changes=fit_rectangles(plan,intent['values'],floor)
    except DesignError as error:
        return {**initial,'customPlan':intent['customPlan'],'changes':[],'valid':False,'proposal':True,'errors':[error.record()],'message':str(error)}
    # Suggested openings are disposable; explicitly authored openings remain protected.
    removed=0
    if changes:
        for f,fl in enumerate(plan['floors']):
            if f in fixed:continue
            retained=[o for o in fl['openings'] if not o['id'].startswith('suggest-')]
            removed+=len(fl['openings'])-len(retained);fl['openings']=retained
    result=prepare_plan({**project,'customPlan':plan},fixed_floors=fixed)
    if removed:changes.append({'kind':'openings','message':'Repositioned previously suggested doors and windows for the fitted walls. Manually placed openings were kept.'})
    return {**result,'proposal':True,'changes':changes+result['changes']}
