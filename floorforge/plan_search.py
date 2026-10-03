"""Bounded, deterministic alternatives for rough rectangular ground-floor sketches.

Explicit opt-in only. Never used by generation, imports, or sample builders.
Searches connected bands, ranks displacement, and returns only compiler-validated
plans. Failure is a search limitation, not a proof that a site is impossible.
"""
from __future__ import annotations
import copy
import math
from shapely.geometry import Polygon
from .intent import fuse
from .model import DesignError
from .spaces import SPACE_REGISTRY
from .plan_assist import prepare_plan


def minimum(room, width, values, plan):
    spec=SPACE_REGISTRY[room['kind']]
    m=max(1000,spec['minimum_width_mm']);area=spec['minimum_area_m2']*1e6
    if room['kind']=='dining':m=max(m,2400);area=max(area,6e6)
    if room['kind']=='stair':
        core=next((s for s in plan['stairs'] if room['id'] in s['roomIds']),{})
        m=2*core.get('flightWidth',1000)+core.get('well',200)
        h=2*core.get('landing',1050)+(math.ceil(values['floor_height_mm']/190/2)-1)*core.get('tread',250)
        if core.get('rotation',0):return math.inf
        return math.ceil(h) if width>=m else math.inf
    return math.ceil(max(m,area/width)) if width>=m else math.inf


def authored_layout(project, plan):
    """Room-level furniture, gardens and slab/support details are authored too."""
    return bool(project.get('roomEdits') or project.get('furnitureLayout') or
        any(fl['walls'] or any(not o['id'].startswith('suggest-') for o in fl['openings']) or
            any(set(r)-{'id','kind','name','polygon','drain','mechanicalVentilation'} for r in fl['rooms'])
            for fl in plan['floors']))


def alternatives(project, floor=0, locked_ids=()):
    intent=fuse(project);plan=intent.get('customPlan')
    if not plan:raise DesignError('CUSTOM_PLAN_REQUIRED','Place rooms in the editor first.')
    if type(floor) is not int or not 0<=floor<len(plan['floors']):raise DesignError('PLAN_FLOOR','Choose an existing floor.')
    rooms=plan['floors'][floor]['rooms'];ids={r['id'] for r in rooms}
    if not isinstance(locked_ids,(list,tuple)) or any(not isinstance(i,str) or i not in ids for i in locked_ids):raise DesignError('PLAN_LOCK','Choose existing room IDs to keep fixed.')
    def stopped(message,questions):
        return {'valid':False,'alternatives':[],'questions':questions,'message':message,'applied':False}
    # Deliberately conservative: no silent relocation of a structural footprint,
    # authored openings, furniture anchors, special polygons or a locked room.
    if floor!=0 or len(plan['floors'])!=1:
        return stopped('Rearrangement currently supports ground-only sketches. Use Smart fit for an upper floor; lower floors stay protected.',[])
    if locked_ids or authored_layout(project,plan):
        return stopped('This draft contains fixed rooms, authored walls/openings or placement edits. They have been preserved.', ['Would you like to rearrange a separate rough copy, or keep these exact positions and edit around them?'])
    if not 2<=len(rooms)<=12 or any(not SPACE_REGISTRY[r['kind']]['floor'] or abs(Polygon(r['polygon']).area-Polygon(r['polygon']).envelope.area)>.1 for r in rooms):
        return stopped('Use 2–12 rectangular, walkable rooms for this search. Exact and more complex plans remain available in Fine-tune.',[])
    v=intent['values'];W=v['width_mm']-v['left_mm']-v['right_mm'];D=v['depth_mm']-v['front_mm']-v['rear_mm'];t=plan['wallThickness']
    public=[r for r in rooms if r['kind'] in {'hall','inner-lobby','foyer','outer-lobby','veranda'}]
    if not public:
        return stopped('A connected passage is needed for independent room access.', ['Add a hall or inner lobby in the editor, then search again. No room will be added without your choice.'])
    center_ids={r['id'] for r in public}
    # An existing courtyard may join the central sequence without being roofed.
    center_ids.update(r['id'] for r in rooms if r['kind']=='courtyard')
    center=sorted([r for r in rooms if r['id'] in center_ids],key=lambda r:(Polygon(r['polygon']).centroid.y,r['id']))
    side=[r for r in rooms if r['id'] not in center_ids]
    if len(side)>9:return stopped('This search supports up to nine rooms beside the connecting passage.',[])
    raw=[]
    for cw in (1200,1500,1800,2400):
        for fraction in (.5,.44,.56):
            available=W-cw-4*t;left=round(available*fraction);right=available-left
            if min(left,right)<1800:continue
            ch=[minimum(r,cw,v,plan) for r in center];free=D-(len(center)+1)*t-sum(ch)
            if free<0:continue
            for mask in range(1,2**len(side)-1):
                lanes=[[r for i,r in enumerate(side) if bool(mask&(1<<i))==flag] for flag in (True,False)]
                for lane in lanes:lane.sort(key=lambda r:(Polygon(r['polygon']).centroid.y,r['id']))
                hs=[[minimum(r,w,v,plan) for r in lane] for lane,w in zip(lanes,(left,right))]
                spare=[D-(len(lane)+1)*t-sum(h) for lane,h in zip(lanes,hs)]
                if min(spare)<0:continue
                candidate=copy.deepcopy(plan);fl=candidate['floors'][0];fl['openings']=[];byid={r['id']:r for r in fl['rooms']}
                def place(sequence,heights,x,w,extra):
                    y=t
                    for r,h in zip(sequence,heights):
                        h+=extra/len(sequence);x1=x+w;y1=y+h
                        byid[r['id']]['polygon']=[[round(x,3),round(y,3)],[round(x1,3),round(y,3)],[round(x1,3),round(y1,3)],[round(x,3),round(y1,3)]];y=y1+t
                place(center,ch,left+2*t,cw,free)
                place(lanes[0],hs[0],t,left,spare[0]);place(lanes[1],hs[1],left+cw+3*t,right,spare[1])
                score=sum(Polygon(r['polygon']).centroid.distance(Polygon(byid[r['id']]['polygon']).centroid) for r in rooms)
                topology=tuple(tuple(r['id'] for r in lane) for lane in lanes)
                raw.append((score,candidate,topology))
    raw.sort(key=lambda q:q[0]);found=[];seen=set();seen_topology=set();checked=0
    # A fixed candidate budget makes the search reproducible and bounded.
    for score,candidate,topology in raw[:36]:
        if topology in seen_topology:continue
        checked+=1
        try:result=prepare_plan({**project,'customPlan':candidate})
        except DesignError:continue
        if not result['valid'] or result['planHash'] in seen:continue
        seen.add(result['planHash']);seen_topology.add(topology)
        changes=[]
        for old,new in zip(rooms,result['customPlan']['floors'][0]['rooms']):
            a=Polygon(old['polygon']);b=Polygon(new['polygon'])
            if not a.equals(b):
                x,y,x1,y1=b.bounds
                changes.append({'kind':'rearrange','id':new['id'],'floor':0,'message':f"{new['name']}: {(x1-x)/1000:.2f} × {(y1-y)/1000:.2f} m; position changed to connect to the passage."})
        found.append({**result,'changes':changes+result['changes'],'proposal':True,'strategy':'rearrange','label':f'Option {len(found)+1}','score':round(score/1000,2),'message':'Connected layout checked for room sizes, openings and access. Review positions before applying.'})
        if len(found)==3:break
    return {'valid':bool(found),'alternatives':found,'checked':checked,'applied':False,'questions':[] if found else ['May any room be removed or made optional, or can the buildable area increase? You can also keep editing positions manually.'], 'message':'Choose a layout to review. Your sketch is unchanged.' if found else 'No checked layout was found within this bounded search. This does not prove that the site is impossible.'}
