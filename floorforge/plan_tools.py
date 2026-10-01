"""Explicit drafting aids. They return editable proposals; generation never applies them."""
from __future__ import annotations
import copy, math
from shapely.geometry import box, Polygon, LineString, Point
from shapely.ops import unary_union
from shapely import get_parts
from .model import DesignError, sha
from .spaces import SPACE_REGISTRY, GUIDE_AUTOMATIC_KINDS, guide_kind, OUTDOOR, NON_WALKABLE


def guide_check(intent):
    hints=intent.get('placement_hints',[]);issues=[]
    for h in hints:
        kind=guide_kind(h['label'])
        if kind not in GUIDE_AUTOMATIC_KINDS:
            issues.append({**h,'code':'CUSTOM_ROOM_REQUIRED','message':f"{SPACE_REGISTRY[kind]['label']} is available in Custom Plan. Turn your cells into rooms to keep this space and its position."})
    cores=[h for h in hints if guide_kind(h['label'])=='stair']
    for h in cores:
        if h['y']>.5 or intent['values']['storeys']==1:
            issues.append({**h,'code':'GUIDE_STAIR_POSITION','message':'Planner limitation: Quick Guide only offers front-left or front-right stairs on multi-floor homes. This warning does not mean your chosen position is invalid. Edit it in Custom Plan to keep this position, then check the stair size, landings and alignment on every floor.'})
    if len(cores)>1 and any(abs(a['x']-c['x'])>.3 or abs(a['y']-c['y'])>.3 for a in cores for c in cores):
        issues.extend({**h,'code':'STAIR_ALIGNMENT','message':'One linked stair core must occupy matching positions on every floor. Align the stair hints or author separate cores in Custom Plan.'} for h in cores)
    from .planner import House
    v=intent['values'];v={**v,'_placement_hints':[(h['label'],h['x'],h['y'],h['source'],h.get('floor')) for h in hints]}
    try:House(v,v['width_mm']-v['left_mm']-v['right_mm'],v['depth_mm']-v['front_mm']-v['rear_mm'])
    except DesignError as error:
        issues.extend((error.details or {}).get('rooms',[]) or [{'code':error.code,'message':str(error)}])
    return {'valid':not issues,'rooms':issues,'message':f'{len(issues)} guide issue(s). Review the marked floors or turn these cells into editable rooms.' if issues else 'Programme checks pass. Generate to check whether the requested positions fit.'}


def convert_guide(project):
    """Use painted cell boundaries as an explicit initial scale, with real wall allowances."""
    from .intent import fuse, _validate_spatial_grid
    base={k:v for k,v in project.items() if k not in ('grid','customPlan')};intent=fuse(base);v=intent['values']
    grid=project.get('grid');_validate_spatial_grid(grid,v['storeys'])
    if len(grid['floors'])!=v['storeys']:raise DesignError('GUIDE_CONVERSION','Assign one board to each floor before converting a legacy whole-home guide.')
    W=v['width_mm']-v['left_mm']-v['right_mm'];D=v['depth_mm']-v['front_mm']-v['rear_mm'];t=150
    plan={'schema':'floorforge.custom-plan/1','units':'mm','wallThickness':t,'floors':[],'stairs':[]}
    for f,rows in enumerate(grid['floors']):
        fl={'id':f'guide-floor-{f}','rooms':[],'walls':[],'openings':[]};groups={}
        for y,row in enumerate(rows):
            for x,label in enumerate(row):
                if label:groups.setdefault(label,[]).append(box(round(t/2+x*(W-t)/4),round(t/2+y*(D-t)/4),round(t/2+(x+1)*(W-t)/4),round(t/2+(y+1)*(D-t)/4)))
        for label,cells in groups.items():
            kind=guide_kind(label);spec=SPACE_REGISTRY[kind]
            for i,p in enumerate(sorted(get_parts(unary_union(cells)),key=lambda p:p.bounds)):
                if spec['enclosed']:p=p.buffer(-t/2,join_style=2)
                if p.is_empty or p.geom_type!='Polygon' or p.interiors:
                    raise DesignError('GUIDE_CONVERSION',f'{label} has a shape that cannot become one clear room. Split it with another room label.',{'rooms':[{'label':label,'floor':f}]})
                name=label.replace('-',' ').title() if label.startswith(('bedroom-','bathroom-')) or label=='master-bedroom' else spec['label']
                if i:name+=f' {i+1}'
                fl['rooms'].append({'id':f'guide-{f}-{label}-{i}','kind':kind,'name':name,'polygon':[[round(x,3),round(y,3)] for x,y in list(p.exterior.coords)[:-1]]})
        plan['floors'].append(fl)
    # Only link truly corresponding cores. A landing label never creates a flight of stairs.
    first=plan['floors'][0]['rooms']
    for r in first:
        if r['kind']!='stair':continue
        peers=[next((q for q in fl['rooms'] if q['kind']=='stair' and Polygon(q['polygon']).equals(Polygon(r['polygon']))),None) for fl in plan['floors']]
        if (len(peers)>1 or v.get('roof_access')) and all(peers):plan['stairs'].append({'id':'link-'+r['id'],'roomIds':[q['id'] for q in peers],'flightWidth':1000,'well':200,'landing':1050,'tread':250})
    from .custom_plan import normalize
    plan=normalize(plan,v['storeys'])
    return {'customPlan':plan,'message':'Cells are now dimensioned rooms with wall allowances. Check room sizes, doors, windows and linked stairs before generating. Your original guides are retained.'}


def suggest_openings(intent):
    """Add openings along actual canonical wall segments without moving any authored object."""
    from .custom_plan import compile_plan, side_at
    if not intent.get('customPlan'):raise DesignError('CUSTOM_PLAN_REQUIRED','Open Custom Plan before suggesting doors and windows.')
    b=compile_plan(intent);plan=copy.deepcopy(intent['customPlan']);by_id={s['id']:s for s in b['spaces']};added=[];occupied={}
    for o in b['openings']:occupied.setdefault(o['wall_id'],[]).append((o['offset'],o['offset']+o['width']))
    def propose(w,room,kind,width,height=2100,sill=0):
        line=LineString([w['a'],w['b']]);length=line.length
        # Keep room offsets nonnegative and retain room corner piers.
        poly=Polygon(room['clear']);x,y,x1,y1=poly.bounds;mid=line.interpolate(.5,normalized=True);side=side_at(poly,mid)
        low=x if side in ('front','rear') else y;high=x1 if side in ('front','rear') else y1
        axis=0 if side in ('front','rear') else 1;origin=w['a'][axis]
        lo=max(150,low-origin+150);hi=min(length-150,high-origin-150)
        if room['kind']=='stair' and kind!='window':
            st=next((st for st in b['stairs'] if st['roomId']==room['id']),None)
            if not st:return False
            if st.get('rotation')==90:
                if side=='left':return False
                if side in ('front','rear'):lo=max(lo,st['x']+st['depth']-st['landing_mm']-origin+50)
            else:
                if side=='rear':return False
                if side in ('left','right'):hi=min(hi,y+st['landing_mm']-origin-50)
        # Prefer the wall centre, then available end spans; do not overwrite an existing opening.
        slots=[lo,hi-width,(lo+hi-width)/2] if kind=='entry' else [(lo+hi-width)/2,lo,hi-width]
        for a,c in occupied.get(w['id'],[]):slots.extend([a-width-150,c+150])
        for offset in slots:
            offset=round(offset)
            if offset<lo or offset+width>hi:continue
            if any(min(offset+width,c+100)>max(offset,a-100) for a,c in occupied.get(w['id'],[])):continue
            start=line.interpolate(offset);room_offset=round(start.coords[0][axis]-low)
            ident='suggest-'+sha({'wall':w['id'],'kind':kind})[:22]
            existing={o['id'] for fl in plan['floors'] for o in fl['openings']}
            while ident in existing:ident+='x'
            o={'id':ident,'roomId':room['id'],'kind':kind,'side':side,'offset':room_offset,'width':width,'height':height,'sill':sill,'hinge':'start'}
            plan['floors'][room['floor']]['openings'].append(o);occupied.setdefault(w['id'],[]).append((offset,offset+width));added.append(o);return True
        return False
    public={'living','drawing-room','family','dining','hall','inner-lobby','foyer','stair','stair-landing'}|OUTDOOR
    connected={frozenset(o['connects']) for o in b['openings'] if o['kind']!='window'}
    # One site entry, only into a public ground-floor room. Prefer the road-facing edge.
    if not any(o['kind']=='entry' for o in b['openings']):
        candidates=[w for w in b['walls'] if w['floor']==0 and len(w['rooms'])==1 and by_id[w['rooms'][0]]['kind'] in public]
        candidates.sort(key=lambda w:(min(w['a'][1],w['b'][1]),w['id']))
        for w in candidates:
            if propose(w,by_id[w['rooms'][0]],'entry',1000):break
    for w in b['walls']:
        if len(w['rooms'])!=2 or frozenset(w['rooms']) in connected:continue
        a,c=[by_id[i] for i in w['rooms']]
        if any(s['kind'] in NON_WALKABLE for s in (a,c)):continue
        if not (a['kind'] in public or c['kind'] in public or {a['kind'],c['kind']}<= {'bedroom','bathroom','dress'}):continue
        room=next((r for r in (a,c) if r['kind']=='stair'),a)
        if propose(w,room,'door',800 if any(r['kind']=='bathroom' for r in (a,c)) else 900):connected.add(frozenset(w['rooms']))
    for room in b['spaces']:
        if room['kind'] not in {'living','drawing-room','family','dining','bedroom','study','kitchen','bathroom','utility','drying-room'}:continue
        if any(o['kind'] in ('window','glazed') and room['id'] in o['connects'] for o in b['openings']):continue
        need=max(.6,room['area_m2']*.10);height=900 if room['wet'] else 1500;sill=1200 if room['wet'] else 750
        width=max(600,math.ceil(need*1e6/height/50)*50)
        candidates=[w for w in b['walls'] if room['id'] in w['rooms'] and (len(w['rooms'])==1 or any(by_id[i]['kind'] in OUTDOOR for i in w['rooms']))]
        candidates.sort(key=lambda w:-LineString([w['a'],w['b']]).length)
        for w in candidates:
            if propose(w,room,'window',width,height,sill):break
    # Every suggested host is checked before the proposal leaves the server.
    compile_plan({**intent,'customPlan':plan})
    return {'customPlan':plan,'added':len(added),'message':f'{len(added)} suggested openings added. Review their positions and validate access and daylight; room geometry is unchanged.'}
