"""Transparent design screening; no statutory/structural certification."""
from __future__ import annotations
from .model import *
from .layout import PUBLIC
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
import datetime, math
import numpy as np
from .exterior import exterior_review, protected_interior_fingerprint

# Minimum clear sizes after NBC 2016 Part 3 (habitable room 9.5 m2 / 2.4 m, kitchen 5.0 m2 / 1.8 m, bath with WC
# 2.8 m2 / 1.2 m) and common practice for the rooms NBC does not size. A screening reference, NOT a verified
# statutory rule pack: local byelaws govern.
GUIDELINES={
 'bedroom':(9.5,2400), 'living':(9.5,2400), 'drawing-room':(7.5,2400),'family':(9.5,2400),
 'kitchen':(5.,1800),'bathroom':(2.8,1200),'utility':(1.8,1000),
 'study':(7.5,2100),'pooja':(1.,850),'dress':(2.,1200),'store':(1.,900),
}
RULE_SOURCE={'document':'NBC 2016 Part 3 (Development control rules and general building requirements), as screening minimums',
 'section':'Requirements of parts of buildings: habitable rooms, kitchens, bathrooms and water-closets',
 'authority':'national model code, applied as a design screen','official_clause':None,'legal_status':'not_verified'}
WINDOW_SHARE=.10      # openable glazing as a share of floor area for habitable rooms (NBC minimum is 1/10)
BATH_VENT_M2=.3       # opening to external air for a bath or WC (NBC-style screening value)
CORRIDOR_MIN=1000     # clear corridor width, mm
SUITE_KINDS={'bathroom','dress'}
LIT_KINDS={'bedroom','care-room','living','drawing-room','family','dining','study','kitchen'}


def swing_sector(o,w,rooms):
    """The quarter circle a hinged leaf sweeps in the room it opens into, or None for other openings."""
    if o['kind'] not in ('door','entry') or o.get('swing') not in rooms:
        return None
    a=np.array(w['a'],float);c=np.array(w['b'],float);u=(c-a)/np.linalg.norm(c-a);n=np.array([-u[1],u[0]])
    p=a+u*o['offset'];q=p+u*o['width'];t=w['thickness']/2
    if not rooms[o['swing']].buffer(5).contains(Point(*((p+q)/2+n*(t+300)))):n=-n
    hinge,free=(p,q) if o.get('hinge','start')=='start' else (q,p)
    h=hinge+n*t;along=(free-hinge)/o['width']
    return Polygon([h]+[h+o['width']*(along*math.cos(th)+n*math.sin(th)) for th in np.linspace(0,math.pi/2,13)])


def professional_screen(b,warnings):
    """Advisory checks a reviewing architect would make: daylight share, bath ventilation, sacred and wet rooms,
    door swings and attached baths. Warnings only: they are recorded, never silently fixed."""
    spaces=b['spaces'];poly={s['id']:Polygon(s['polygon']) for s in spaces};clear={s['id']:Polygon(s['clear']) for s in spaces}
    hosts={w['id']:w for w in b['walls']};kinds={s['id']:s['kind'] for s in spaces}
    def glazing(ids):
        # Windows plus glazed doors to open air or a terrace; solid doors are excluded as NBC excludes doors.
        return sum(o['width']*o['height']/1e6 for o in b['openings'] if set(o['connects'])&ids and
                   (o['kind']=='window' or (o['kind']=='glazed' and ({'outside'}|{i for i in kinds if kinds[i] in ('terrace','veranda','balcony','courtyard','outer-lobby','drying-yard')})&set(o['connects']))))
    seen=set()
    for s in spaces:
        if s['kind'] not in LIT_KINDS or s['id'] in seen:continue
        group={s['id']}
        if s['kind'] in ('living','dining'):
            group={t['id'] for t in spaces if t['floor']==s['floor'] and t['kind'] in ('living','dining')}
        seen|=group
        area=sum(clear[i].area for i in group)/1e6;share=glazing(group)/max(area,.01)
        if share<WINDOW_SHARE:
            warnings.append({'code':'LOW_DAYLIGHT','id':s['id'],'glazing_to_floor_pct':round(share*100,1),'required_pct':WINDOW_SHARE*100,
                             'message':f'{s["name"]}: openings are {share*100:.2f}% of the floor area; NBC-style screening asks for at least 10%.'})
    for s in spaces:
        if s['kind'] in ('bathroom','powder-room'):
            if s.get('mechanicalVentilation'):
                warnings.append({'code':'MECHANICAL_EXHAUST_DESIGN','id':s['id'],'message':f'{s["name"]}: mechanical exhaust selected; duct route and capacity require design.'})
                continue
            vent=sum(o['width']*o['height']/1e6 for o in b['openings'] if o['kind']=='window' and s['id'] in o['connects'])
            if vent<BATH_VENT_M2:
                warnings.append({'code':'BATH_VENTILATION','id':s['id'],'opening_m2':round(vent,3),'required_m2':BATH_VENT_M2,
                                 'message':f'{s["name"]} has no {BATH_VENT_M2} m2 opening to open air; provide a shaft or mechanical exhaust.'})
    for s in spaces:
        if s['kind']!='pooja':continue
        for t in spaces:
            if t['floor']==s['floor'] and t['kind']=='bathroom' and poly[s['id']].boundary.intersection(poly[t['id']].boundary).length>=300:
                warnings.append({'code':'POOJA_BESIDE_BATH','ids':[s['id'],t['id']],'message':f'{s["name"]} shares a wall with {t["name"]}.'})
    for s in spaces:
        if s['kind']!='bathroom' or s['floor']==0:continue
        for t in spaces:
            if t['floor']==s['floor']-1 and t['kind'] in ('pooja','kitchen'):
                over=poly[s['id']].intersection(poly[t['id']]).area/1e6
                if over>.3:
                    warnings.append({'code':'WET_ABOVE_'+t['kind'].upper(),'ids':[s['id'],t['id']],'overlap_m2':round(over,2),
                                     'message':f'{s["name"]} sits over the {t["name"].lower()} below: plumbing and custom both advise against it.'})
    for f in range(b['storeys']):
        sectors=[(o['id'],swing_sector(o,hosts[o['wall_id']],clear)) for o in b['openings'] if o['floor']==f and o['wall_id'] in hosts]
        sectors=[(i,q) for i,q in sectors if q is not None and q.is_valid]
        for i,(ia,qa) in enumerate(sectors):
            for ib,qb in sectors[i+1:]:
                if qa.intersection(qb).area>2e4:
                    warnings.append({'code':'DOOR_SWING_CLASH','ids':[ia,ib],'message':'Two door leaves sweep the same floor area.'})
    want=b.get('planning',{}).get('attached_baths',{})
    if isinstance(want.get('requested'),int) and want.get('provided',0)<want['requested']:
        warnings.append({'code':'ENSUITE_SHORTFALL','requested':want['requested'],'provided':want['provided'],
                         'message':f'{want["provided"]} of {want["requested"]} requested attached baths fit this plot.'})

def validate(b):
    if b.get('planning',{}).get('custom'):
        from .custom_plan import validate_custom
        return validate_custom(b)
    v=b['brief'];errors=[];warnings=[];checks=[]; spaces=b['spaces']; fp=Polygon(b['footprint'])
    ids=[s['id'] for key in ('spaces','walls','openings') for s in b[key]]
    if len(ids)!=len(set(ids)):
        raise DesignError('DESIGN_SCREEN_FAILED','Duplicate semantic IDs are not allowed.',{'errors':[{'code':'DUPLICATE_ID'}]})
    space_ids={s['id'] for s in spaces}|{'outside'}
    for opening in b['openings']:
        if len(opening.get('connects',[]))!=2 or any(i not in space_ids for i in opening['connects']):
            raise DesignError('DESIGN_SCREEN_FAILED','An opening references a missing space.',{'errors':[{'code':'MISSING_SPACE','id':opening['id']}]})
    if not fp.is_valid or fp.is_empty:errors.append({'code':'FOOTPRINT_INVALID'})
    if not Polygon(b['plot']).covers(fp):errors.append({'code':'PLOT_CONTAINMENT'})
    graph={s['id']:set() for s in spaces};graph['outside']=set()
    beds=[s for s in spaces if s['kind']=='bedroom']
    floor_home='home'
    largest={floor_home:max(beds,key=lambda s:s['area_m2'])['id']} if beds else {}
    for floor in range(b['storeys']):
        ss=[s for s in spaces if s['floor']==floor]
        for i,s in enumerate(ss):
            p=Polygon(s['polygon']); c=Polygon(s['clear'])
            if not fp.buffer(.01).covers(p):errors.append({'code':'SPACE_OUTSIDE','id':s['id']})
            for q in ss[i+1:]:
                if p.intersection(Polygon(q['polygon'])).area>1:errors.append({'code':'SPACE_OVERLAP','ids':[s['id'],q['id']]})
                # Shared edge without a wall is an open connection.
                edge=p.boundary.intersection(Polygon(q['polygon']).boundary)
                wall=any(set(w['rooms'])=={s['id'],q['id']} for w in b['walls'])
                if edge.length>=800 and not wall:
                    graph[s['id']].add(q['id']);graph[q['id']].add(s['id'])
            area,width=GUIDELINES.get(s['kind'],(0,0))
            if s['kind']=='bedroom' and s['id']!=largest.get(floor_home, s['id']):
                area=7.5   # NBC: one habitable room of 9.5 m2; a further room may be 7.5 m2
            bounds=c.bounds; minwidth=min(bounds[2]-bounds[0],bounds[3]-bounds[1])
            if s['kind'] in ('living','dining'):
                combined=unary_union([Polygon(t['clear']) for t in ss if t['kind'] in ('living','dining')])
                area_actual=combined.area/1e6
                bx=combined.bounds;minwidth=min(bx[2]-bx[0],bx[3]-bx[1])
            else:area_actual=c.area/1e6
            if area_actual+1e-5<area or minwidth+.01<width:
                errors.append({'code':'GUIDELINE_ROOM_SIZE','id':s['id'],'actual_m2':round(area_actual,3),
                    'required_m2':area,'bounding_short_side_mm':round(minwidth),'target_width_mm':width,'source':RULE_SOURCE})
            if not c.is_valid or c.area<=0:errors.append({'code':'CLEAR_INVALID','id':s['id']})
            if s['kind']=='hall':
                if minwidth+.01<CORRIDOR_MIN:
                    errors.append({'code':'CORRIDOR_WIDTH','id':s['id'],'clear_width_mm':round(minwidth),'required_mm':CORRIDOR_MIN})
                share=c.area/max(1.,sum(Polygon(t['clear']).area for t in ss))
                if share>.12:
                    warnings.append({'code':'LONG_CIRCULATION','id':s['id'],'message':f'Circulation takes {share*100:.2f}% of this floor; review whether rooms can open off a shorter hall.'})
        if abs(unary_union([Polygon(s['polygon']) for s in ss]).area-fp.area)>2:
            errors.append({'code':'UNTILED_FLOOR','floor':floor})
    hosts={w['id']:w for w in b['walls']}
    for o in b['openings']:
        if o['wall_id'] not in hosts:errors.append({'code':'MISSING_HOST','id':o['id']});continue
        w=hosts[o['wall_id']];length=math.dist(w['a'],w['b'])
        if o['offset']<0 or o['offset']+o['width']>length+.1 or o['sill']+o['height']>w['height']:
            errors.append({'code':'OPENING_OUTSIDE','id':o['id']})
        if o['kind']!='window':
            a,c=o['connects'];graph[a].add(c);graph[c].add(a)
    if b['storeys']>1:
        cores=[s for s in spaces if s['kind']=='stair']
        if len(cores)!=b['storeys']:errors.append({'code':'STAIR_COUNT'})
        for a,c in zip(cores,cores[1:]):
            if Polygon(a['polygon']).symmetric_difference(Polygon(c['polygon'])).area>1:errors.append({'code':'STAIR_ALIGNMENT'})
            graph[a['id']].add(c['id']);graph[c['id']].add(a['id'])
        for s in b['stairs']:
            if not (s['riser_mm']<=190 and s['tread_mm']>=250 and s['flight_width']>=1000):errors.append({'code':'STAIR_PROPORTION'})
    def reach(blocked=None):
        found={'outside'}; todo=['outside']
        while todo:
            for nxt in graph[todo.pop()]:
                if nxt not in found and nxt!=blocked:found.add(nxt);todo.append(nxt)
        return found
    missing=set(graph)-reach()
    if missing: errors.append({'code':'UNREACHABLE','ids':sorted(missing)})
    kinds={s['id']:s['kind'] for s in spaces}
    suites={}
    for s in spaces:
        if not missing and s['kind']=='bedroom':
            cut=set(graph)-{s['id']}-reach(s['id'])
            # Only the bedroom's own attached bath and dressing room may lie beyond it.
            if any(kinds.get(r) not in SUITE_KINDS for r in cut):errors.append({'code':'BEDROOM_THROUGH_ROUTE','id':s['id']})
            elif cut:suites[s['id']]=sorted(cut)
        if s['kind'] in {'bedroom','living','drawing-room','kitchen','study','family'}:
            if not any(o['kind']=='window' and s['id'] in o['connects'] for o in b['openings']):
                errors.append({'code':'NO_EXTERNAL_WINDOW','id':s['id']})
    if sum(s['kind']=='bedroom' for s in spaces)!=v['bedrooms']:errors.append({'code':'BEDROOM_COUNT'})
    professional_screen(b,warnings)
    exterior=b.get('exterior')
    exterior_status=exterior_review(b)
    if exterior:
        ext_ids=[a['id'] for a in exterior.get('assemblies',[])]
        ext_ids += [f['id'] for f in exterior.get('landscape',{}).get('features',[])]
        if len(ext_ids)!=len(set(ext_ids)):
            errors.append({'code':'DUPLICATE_EXTERIOR_ID'})
        plot=Polygon(b['plot'])
        for assembly in exterior.get('assemblies',[]):
            bounds=assembly['geometry']['bounds_mm']
            if bounds[2]<=bounds[0] or bounds[3]<=bounds[1] or not plot.covers(box(*bounds)):
                errors.append({'code':'EXTERIOR_ASSEMBLY_OUTSIDE','id':assembly['id']})
        for feature in exterior.get('landscape',{}).get('features',[]):
            if 'polygon' in feature and not plot.covers(Polygon(feature['polygon'])):
                errors.append({'code':'LANDSCAPE_OUTSIDE','id':feature['id']})
        if exterior.get('protected_interior_before')!=protected_interior_fingerprint(b):
            errors.append({'code':'INTERIOR_LOCK_VIOLATION'})
        checks_extra=['exterior assembly containment','protected interior fingerprint','landscape/path reservation',
                      'exterior theme and opening change record']
    else:
        checks_extra=[]
    checks=['valid footprint and plot containment','no overlapping room cells','floor coverage','clear-space reference sizes',
            'opening host and bounds','connected portal graph','no bedroom as required through-route',
            'external-window presence','bedroom and floor counts','stair proportions and vertical alignment',
            'corridor width and circulation share','daylight share of habitable rooms (1/10)','bath and WC ventilation',
            'pooja beside or below wet areas','door swing clashes','attached baths against the request']+checks_extra
    result={'planHash':b.get('planHash'),'draftRevision':b.get('draftRevision',0),'status':'blocked' if errors else 'preliminary_geometry_pass','checks':checks,'errors':errors,'warnings':warnings,
            'rule_source':RULE_SOURCE,'regulatory':'NOT EVALUATED','structural':'NOT DESIGNED','accessibility':'NOT CERTIFIED',
            'collision_scope':'2D circle against opening-cut walls and furnishings; not a full-body physics certification.',
            'construction_ready':False,'graph':{k:sorted(val) for k,val in graph.items()},
            'exterior':exterior_status,
            'disclaimer':__import__('floorforge').BANNER}
    if errors:raise DesignError('DESIGN_SCREEN_FAILED','The design failed the preliminary geometry screen; no final model was published.',result)
    return result


def solar_position(v):
    """NOAA-style closed-form study; no refraction, horizon or weather model."""
    day=datetime.date.fromisoformat(v['solar_date']).timetuple().tm_yday
    hour=v['solar_hour'];lat=math.radians(v['latitude'])
    gamma=2*math.pi/365*(day-1+(hour-12)/24)
    eq=229.18*(.000075+.001868*math.cos(gamma)-.032077*math.sin(gamma)-.014615*math.cos(2*gamma)-.040849*math.sin(2*gamma))
    dec=.006918-.399912*math.cos(gamma)+.070257*math.sin(gamma)-.006758*math.cos(2*gamma)+.000907*math.sin(2*gamma)-.002697*math.cos(3*gamma)+.00148*math.sin(3*gamma)
    mins=hour*60+eq+4*v['longitude']-60*v['timezone_hours']
    h=math.radians(mins/4-180)
    e=-math.cos(dec)*math.sin(h)
    n=math.cos(lat)*math.sin(dec)-math.sin(lat)*math.cos(dec)*math.cos(h)
    up=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(h)
    x,y=enu_to_local(e,n,v['road_bearing_deg'])
    return {'vector_local':[x,y,up],'elevation_deg':math.degrees(math.asin(max(-1,min(1,up)))),
            'azimuth_deg':math.degrees(math.atan2(e,n))%360,'method':'NOAA-style closed-form solar study; no atmospheric refraction',
            'source':'https://gml.noaa.gov/grad/solcalc/solareqns.PDF','inputs':{k:v[k] for k in ('latitude','longitude','timezone_hours','solar_date','solar_hour')}}


def reports(b,review):
    # Do not mutate an earlier DAG stage when appending report-only warnings.
    import copy
    review=copy.deepcopy(review)
    v=b['brief'];fp=Polygon(b['footprint']); plot=Polygon(b['plot']); gross=fp.area/1e6*b['storeys'];ft2=gross*10.7639104
    if 'floor_plates' in b:
        from .plan_geometry import plate
        gross=sum(plate(b,f).area for f in range(b['storeys']))/1e6;ft2=gross*10.7639104
    low=ft2*v['rate_low_inr_ft2'];high=ft2*v['rate_high_inr_ft2'];factor=1+v['cost_contingency_pct']/100
    areas={'plot_m2':round(plot.area/1e6,3),'footprint_m2':round(fp.area/1e6,3),'gross_floor_m2':round(gross,3),
           'gross_floor_ft2':round(ft2,2),'ground_coverage_pct':round(fp.area/plot.area*100,2),
           'geometric_far':round(gross*1e6/plot.area,3),'roof_terrace_m2':b.get('rooftop',{}).get('spaces',[{}])[-1].get('area_m2',0),'open_terrace_m2':round(sum(Polygon(s['polygon']).area for s in b['spaces'] if s['kind']=='terrace')/1e6,3),
           'area_basis':'Gross plan envelopes include wall/stair cells and open terraces; not carpet area or statutory floor area.',
           'far_legal_definition':'Unverified local inclusions/exclusions; geometric ratio only.'}
    cost={'low_lakh':round(low*factor/1e5,2),'high_lakh':round(high*factor/1e5,2),'budget_lakh':v['budget_lakh'],
          'within_budget_low':low*factor<=v['budget_lakh']*1e5,'within_budget_high':high*factor<=v['budget_lakh']*1e5,
          'basis':'Illustrative user-editable gross-plan-envelope rates, including open terrace cells. NOT a quote, tender, BOQ or market survey.',
          'rates_inr_ft2':[v['rate_low_inr_ft2'],v['rate_high_inr_ft2']],'contingency_pct':v['cost_contingency_pct'],
          'excludes':['land','approvals and professional fees','tax treatment','abnormal foundations','lifts','loose furniture','external services']}
    windows={s['id']:sum(o['width']*o['height']/1e6 for o in b['openings'] if o['kind']=='window' and s['id'] in o['connects']) for s in b['spaces']}
    center=fp.centroid; zones=[]
    # Common Vastu readings: (preferred zones, acceptable zones). The master suite takes the south-west; other
    # bedrooms the west, north-west or south; the kitchen the south-east (north-west acceptable); the pooja the north-east.
    preferred={'kitchen':({'SE'},{'NW','E'}),'master':({'SW'},{'S','W'}),'bedroom':({'W','NW','S'},{'SW','E'}),'pooja':({'NE'},{'N','E'}),
               'living':({'N','NE','E'},{'NW'}),'family':({'N','NE','E'},{'NW','W'}),'stair':({'S','W','SW'},{'SE','NW'})}
    compass=['N','NE','E','SE','S','SW','W','NW']
    beds=[s for s in b['spaces'] if s['kind']=='bedroom'];master=max(beds,key=lambda s:(s['name'].startswith('Master'),s['area_m2']))['id'] if beds else None
    for s in b['spaces']:
        if s['kind']=='stair' and s['floor']>0:continue
        key='master' if s['id']==master else s['kind']
        if key not in preferred:continue
        c=Polygon(s['clear']).centroid;e,n=local_to_enu(c.x-center.x,c.y-center.y,v['road_bearing_deg'])
        az=math.degrees(math.atan2(e,n))%360;zone=compass[int((az+22.5)//45)%8]
        best,ok=preferred[key]
        zones.append({'space':s['name'],'zone':zone,'preferred':sorted(best),'acceptable':sorted(ok),'matches':zone in best,
                      'rating':'preferred' if zone in best else 'acceptable' if zone in ok else 'avoid'})
    vastu={'setting':v['vastu'],'status':'off' if v['vastu']=='off' else 'advisory','rooms':zones,
           'score':None if v['vastu']=='off' else round(100*sum(1 if z['matches'] else .5 if z['rating']=='acceptable' else 0 for z in zones)/max(1,len(zones))),
           'limitation':'Preference heuristic from supplied brief, not a safety or scientific rating. Strict requests are flagged, not guaranteed.'}
    if v['vastu']=='strict' and any(x['rating']=='avoid' for x in zones):
        review['warnings'].append({'code':'VASTU_STRICT_UNRESOLVED','message':'Not all strict Vastu preferences are satisfied. This is a visible unresolved preference, not a compliant design.'})
    mep={'status':'schematic intent only','wet_spaces':[s['id'] for s in b['spaces'] if s['kind'] in ('bathroom','kitchen','utility','drying-room','drying-yard')],
         'notes':['Cluster wet areas; a plumbing designer must size and route stacks, vents and gradients.',
                  'No electrical cable sizing, protection coordination or circuit approval.',
                  'No medical gas, life-support power or ICU services design.'],
         'electrical':[{'room':s['id'],'intent':'lighting + separately designed power circuit'} for s in b['spaces']]}
    timeline=[{'phase':name,'start_week':start,'duration_weeks':duration,'basis':'Illustrative planning assumption, not a site schedule'} for name,start,duration in
              [('Survey, soil and approvals',0,6),('Foundations and substructure',6,5),('Frame and roof',11,6*b['storeys']),
               ('Masonry and services',11+4*b['storeys'],7),('Finishes and joinery',18+4*b['storeys'],8),('Testing and handover',26+4*b['storeys'],2)]]
    structure={'status':'coordination grid only - no member sizing or design','assumed_system':'RCC frame with masonry infill, subject to engineer selection',
               'grid_x':sorted(set(round(x) for x,y in b['footprint'])),
               'grid_y':sorted(set(round(y) for x,y in b['footprint'])),
               'required':['survey and authority byelaws','geotechnical investigation','load paths and lateral stability','IS 456/875/1893 applicability review',
                           'foundation design against measured soil parameters','reinforcement, deflection and connection design'],
               'soil':v['soil'],'foundation_recommendation':None,
               'soil_warning':'A soil name or photograph cannot establish bearing capacity, swelling or an appropriate foundation.'}
    daylight=[{'space':s['id'],'window_area_m2':round(windows[s['id']],3),'glazing_to_floor_pct':round(100*windows[s['id']]/max(s['area_m2'],.01),1),
               'status':'geometric opening ratio, not daylight autonomy or ventilation compliance'} for s in b['spaces']]
    wallvol=sum(Polygon(w['polygon']).area*w['height'] for w in b['walls'])/1e9
    openingvol=sum(o['width']*o['height']*next(w['thickness'] for w in b['walls'] if w['id']==o['wall_id']) for o in b['openings'])/1e9
    quantities={'nominal_wall_solid_m3':round(wallvol-openingvol,3),'status':'Approximate geometry volume; overlapping wall joints and unbuilt assumptions prevent BOQ certification.',
                'cement_bags':None,'reinforcement_kg':None,'reason':'Material quantities need mix designs, reinforcement schedules and measured assemblies; not invented from floor area.'}
    return {'input_audit':b.get('input_audit'),'planHash':b.get('planHash'),'draftRevision':b.get('draftRevision',0),'banner':__import__('floorforge').BANNER,'areas':areas,'cost':cost,'timeline':timeline,'vastu':vastu,'structure':structure,'mep':mep,
            'daylight':daylight,'solar':solar_position(v),'quantities':quantities,'review':review,
            'exterior': exterior_review(b),
            'unresolved_requests':unresolved(b)}


def unresolved(b):
    """Brief requests the plan does not (fully) meet, in plain words."""
    v=b['brief'];out=[];kinds=[s['kind'] for s in b['spaces']]
    if v['pooja'] and 'pooja' not in kinds:out.append('Pooja requested: only a niche fits, no separate pooja room')
    want=b.get('planning',{}).get('attached_baths',{})
    if isinstance(want.get('requested'),int) and want.get('provided',0)<want['requested']:
        out.append(f'Attached baths: {want["provided"]} of {want["requested"]} requested fit this plot')
    if v['eldercare']:out.append('Eldercare/ICU and step-free routes not designed')
    return out
