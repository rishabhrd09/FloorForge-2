"""Compass allocation → reviewed Custom Plan; the renderer remains a shared consumer."""
from __future__ import annotations

import math
from shapely.geometry import box, LineString
from shapely.ops import unary_union
from .model import DesignError, sha
from .spaces import SPACE_REGISTRY
from .compass_input import normalize, cell, source_hash, ADAPTER


def compile_compass(value, values, scope=None, hints=()):
    from .custom_plan import compile_plan, side_at, normalize as normalize_plan, validate_custom
    from .review import LIT_KINDS

    compass = normalize(value)
    drawn = compass.get('programme') == 'drawn'
    count = values['storeys']
    if len(compass['floors']) < count:
        raise DesignError('COMPASS_FLOORS', 'Keep a Compass draft for each requested occupied floor.')
    scope = count if scope is None else scope
    if type(scope) is not int or not 1 <= scope <= count:
        raise DesignError('COMPASS_SCOPE', 'Generate a consecutive prefix: Ground, Ground and First, or all floors.')
    identity = source_hash(compass, values, scope)
    floors = compass['floors'][:scope]
    included = {f['id'] for f in floors}
    rooms = [r for r in compass['rooms'] if r['floorId'] in included]
    by_id = {r['id']: r for r in rooms}
    v = {**values, 'storeys': scope, 'bedrooms': sum(r['kind'] == 'bedroom' and bool(r['regions']) for r in rooms),
         'roof_access': values['roof_access'] and scope == count}
    W = v['width_mm'] - v['left_mm'] - v['right_mm']
    D = v['depth_mm'] - v['front_mm'] - v['rear_mm']
    issues, changes, sizes, effects = [], [], [], []

    def issue(code, message, room=None, **extra):
        issues.append({'code': code, 'message': message, 'severity': 'error',
                       **({'roomId': room['id'], 'floor': next(i for i, f in enumerate(floors) if f['id'] == room['floorId']), 'regions': room['regions']} if room else {}), **extra})

    if W < 1000 or D < 1000:
        issue('ENVELOPE', 'Plot dimensions and setbacks leave too little buildable area.')
    expected = sum(r['kind'] == 'bedroom' for r in compass['rooms'] if r['floorId'] in {f['id'] for f in compass['floors'][:count]})
    if not drawn and expected != values['bedrooms']:
        issue('BEDROOM_PROGRAMME', f'The setup requests {values["bedrooms"]} bedrooms but the active floor checklists contain {expected}. Add or revise room requirements explicitly.')
    if drawn:
        omitted = [r['name'] for r in rooms if not r['regions']]
        if omitted:
            effects.append({'source': 'unplaced-rooms', 'status': 'unapplied',
                            'message': 'Not drawn yet: ' + ', '.join(omitted) + '. These rooms remain in your saved draft.'})
        effects.append({'source': 'drawn-programme', 'status': 'applied',
                        'message': f'Preview only the placed rooms on {scope} floor(s), including {v["bedrooms"]} bedrooms. Empty cells stay empty; upper drafts remain saved.'})
    site = compass['site']
    if site['gate'] != 'planner' or site.get('zones') or 'secondRoad' in site:
        issue('SITE_UNAVAILABLE', 'Custom gate positions, additional road geometry and setback-band zones need the site compiler extension. Keep planner gate placement and record these requests as notes for now.')
    effects.append({'source': 'plot-context', 'status': 'note only', 'message': f'Plot context: {site["context"]}. Exposure and additional roads are not inferred.'})
    plan = {'schema': 'floorforge.custom-plan/1', 'units': 'mm', 'wallThickness': 150, 'floors': [], 'stairs': []}
    polygons = {}
    t = plan['wallThickness']
    cols = compass['grid']['cols']
    xs = [round(t / 2 + i * (W - t) / (2 * cols), 3) for i in range(2 * cols + 1)]
    ys = [round(t / 2 + i * (D - t) / (2 * compass['grid']['rows']), 3) for i in range(2 * compass['grid']['rows'] + 1)]
    for floor in floors:
        target = {'id': floor['id'], 'rooms': [], 'walls': [], 'openings': []}
        for room in (r for r in rooms if r['floorId'] == floor['id']):
            if room['kind'] == 'lift-shaft':
                issue('ROOM_UNAVAILABLE', 'Lift design is unavailable in Compass. Keep it as a note for further design.', room)
                continue
            if not room['regions']:
                if room.get('required', True) and not drawn:
                    issue('UNPLACED', f'Place {room["name"]}, or explicitly make it optional.', room)
                continue
            parts = []
            for ref in room['regions']:
                row, col, half = cell(ref, compass['grid']['rows'], cols)
                left = 2 * col + (1 if half == 'R' else 0)
                right = 2 * col + (1 if half == 'L' else 2)
                front = 2 * row + (1 if half == 'B' else 0)
                back = 2 * row + (1 if half == 'F' else 2)
                parts.append(box(xs[left], ys[front], xs[right], ys[back]))
            allocated = unary_union(parts)
            spec = SPACE_REGISTRY[room['kind']]
            p = allocated.buffer(-t / 2, join_style=2) if spec['enclosed'] else allocated
            if p.is_empty or p.geom_type != 'Polygon' or p.interiors:
                issue('COLLAPSED_ROOM', f'{room["name"]} collapses after wall allowance, contains a hole, or has a disconnected shape.', room)
                continue
            x, y, x1, y1 = p.bounds
            minimum = spec['minimum_width_mm']
            core = p.buffer(-minimum / 2 + 1, join_style=2) if minimum else p
            if core.is_empty or core.geom_type == 'MultiPolygon':
                issue('NARROW_NECK', f'{room["name"]} has a connection narrower than its {minimum / 1000:g} m minimum. Widen the bridge between its regions.', room)
            if p.area / 1e6 + 1e-6 < spec['minimum_area_m2'] or min(x1 - x, y1 - y) + .1 < minimum:
                issue('ROOM_MINIMUM', f'{room["name"]}: {p.area / 1e6:.2f} m², {min(x1-x, y1-y)/1000:.2f} m narrow side. This type needs {spec["minimum_area_m2"]:g} m² and {minimum/1000:g} m. Enlarge its assigned area.', room)
            size = {'roomId': room['id'], 'name': room['name'], 'allocationSpan': [round(allocated.bounds[2]-allocated.bounds[0], 3), round(allocated.bounds[3]-allocated.bounds[1], 3)], 'clearSize': [round(x1-x, 3), round(y1-y, 3)], 'area_m2': round(p.area/1e6, 3)}
            sizes.append(size)
            target_size = room.get('target')
            if target_size:
                size['target'] = target_size
                matches = all(abs(actual - target_size[key]) < 1 for actual, key in zip(size['clearSize'], ('width', 'depth')))
                if target_size.get('locked') and not matches:
                    issue('SIZE_LOCK', f'{room["name"]} does not match its locked clear dimensions. Adjust its regions or explicitly unlock the target; fitting never moves it silently.', room)
                effects.append({'source': room['id'] + '-size', 'status': 'applied' if matches else 'preference checked', 'message': 'Clear-size target compared with the accepted polygon.'})
            polygons[room['id']] = p
            q = {k: room[k] for k in ('id', 'kind', 'name', 'mechanicalVentilation', 'drain') if k in room}
            q['polygon'] = [[round(float(a), 3), round(float(b), 3)] for a, b in list(p.exterior.coords)[:-1]]
            if q['kind'] == 'drying-room':
                q.setdefault('drain', True)
            if scope < count and scope == 1 and q['kind'] == 'stair':
                q['kind'] = 'stair-landing'
                changes.append({'roomId': q['id'], 'message': 'Ground-only scope reserves this stair area as a landing; unfinished upper-floor flights and roof access are omitted.'})
            target['rooms'].append(q)
        plan['floors'].append(target)
        if drawn and not target['rooms']:
            issue('EMPTY_FLOOR', 'Draw at least one room on this floor, or choose fewer floors for the preview.', floor=floors.index(floor))
    stair_links = list(compass['stairLinks'])
    if drawn and scope > 1:
        linked = {rid for s in stair_links for rid in s['roomIds']}
        for first in (r for r in rooms if r['floorId'] == floors[0]['id'] and r['kind'] == 'stair' and r['id'] in polygons and r['id'] not in linked):
            matches = [first]
            for floor in floors[1:]:
                match = next((r for r in rooms if r['floorId'] == floor['id'] and r['kind'] == 'stair'
                              and r['id'] in polygons and r['id'] not in linked
                              and polygons[r['id']].equals(polygons[first['id']])), None)
                if match is None:
                    break
                matches.append(match)
            if len(matches) == scope:
                ids = [r['id'] for r in matches]
                stair_links.append({'id': 'compass-auto-core-' + sha(ids)[:16], 'roomIds': ids,
                                    'flightWidth': 1000, 'well': 200, 'landing': 1050, 'tread': 250, 'rotation': 0})
                linked.update(ids)
                effects.append({'source': 'matching-stairs', 'status': 'applied', 'message': 'Matching stair rooms are linked automatically; their positions are unchanged.'})
    for stair in stair_links:
        ids = [r for r in stair['roomIds'] if r in polygons]
        if len(ids) > 1 or (ids and v['roof_access']):
            plan['stairs'].append({**stair, 'roomIds': ids})
    if (scope > 1 or v['roof_access']) and not plan['stairs']:
        issue('STAIR_LINK', 'Place matching stair rooms on consecutive floors and link the core. A landing label alone does not create stairs.')
    overrides = {r['value'] for r in compass['requirements'] if r['kind'] == 'keep-map'}
    for hint in hints:
        if hint['label'] in overrides:
            continue
        kind = 'bedroom' if hint['label'].startswith(('bedroom-', 'master-bedroom')) else hint['label']
        matching = [r for r in rooms if r['kind'] == kind and r['id'] in polygons]
        if len(matching) != 1:
            continue
        room = matching[0]
        center = polygons[room['id']].centroid
        if ((center.x / W - hint['x']) ** 2 + (center.y / D - hint['y']) ** 2) ** .5 > .40:
            issue('TEXT_CONFLICT', f'The description asks for {hint.get("phrase", hint["label"])} but the authored map places {room["name"]} elsewhere.', room, label=hint['label'], actions=['keep-map', 'edit-requirement', 'move-room'])
    for requirement in compass['requirements']:
        if requirement.get('roomId') and requirement['roomId'] not in by_id:
            effects.append({'source': requirement['id'], 'status': 'off', 'message': 'Room requirement retained on an excluded floor; it is not part of this generated scope.'})
            continue
        if requirement['kind'] == 'access-width' and requirement['roomId'] not in polygons:
            effects.append({'source': requirement['id'], 'status': 'unapplied', 'message': f'Clear-route request for {by_id[requirement["roomId"]]["name"]} was not checked because this optional room is unplaced.'})
            continue
        if requirement['kind'] == 'access-width' and requirement['roomId'] in polygons:
            p = polygons[requirement['roomId']]
            width = requirement['value']
            core = p.buffer(-width / 2 + 1, join_style=2)
            if core.is_empty or core.geom_type != 'Polygon':
                issue('ACCESS_WIDTH', f'This route does not keep the requested {width / 1000:g} m clear width.', by_id[requirement['roomId']])
        effects.append({'source': requirement['id'], 'status': 'note only' if requirement['kind'] == 'note' else 'applied', 'message': str(requirement['value'])})
    for relation in compass['connections']:
        if relation['from'] not in by_id or relation['to'] not in by_id:
            effects.append({'source': relation['id'], 'status': 'off', 'message': 'Room relationship retained on an excluded floor.'})
        elif relation['from'] not in polygons or relation['to'] not in polygons:
            effects.append({'source': relation['id'], 'status': 'unapplied', 'message': 'Room relationship was not applied because an optional room is unplaced. Place both rooms to use this connection.'})
    changes.append({'message': 'Union each room’s regions before reserving walls. Keep assigned positions and room IDs; leave unassigned space empty.'})
    if scope < count:
        changes.append({'message': f'Generate {scope} of {count} occupied floors. Retain all upper drafts and omit roof access over unfinished floors.'})
    result = {'valid': False, 'customPlan': plan, 'issues': issues, 'changes': changes, 'sizes': sizes, 'effects': effects,
              'sourceHash': identity, 'adapterVersion': ADAPTER, 'scope': scope, 'values': v,
              'roomMapping': {r['id']: r['id'] for r in rooms if r['id'] in polygons}}
    if issues:
        return result
    intent = {'values': v, 'customPlan': plan, 'planHash': identity}
    try:
        b = compile_plan(intent)
        spaces = {s['id']: s for s in b['spaces']}
        for relation in compass['connections']:
            if relation['kind'] != 'separated' or relation['from'] not in polygons or relation['to'] not in polygons:
                continue
            a, c = (polygons[relation[key]] for key in ('from', 'to'))
            if a.boundary.intersection(c.boundary).length > .1:
                issue('SEPARATION_WALL', 'These open spaces share an unobstructed edge. Choose enclosed room types or leave a gap to keep them separated.', by_id[relation['from']], connectionId=relation['id'])
        explicit = {frozenset((c['from'], c['to'])) for c in compass['connections'] if c['from'] in polygons and c['to'] in polygons}
        occupied = {}

        def add_opening(wall, rid, kind, width, ident, height=2100, sill=0):
            p = polygons[rid]
            line = LineString([wall['a'], wall['b']])
            side = side_at(p, line.interpolate(.5, normalized=True))
            horizontal = abs(wall['a'][1]-wall['b'][1]) < .01
            if horizontal != (side in ('front','rear')):
                return False
            fixed = 1 if horizontal else 0
            expected = (p.bounds[1]-t/2 if side=='front' else p.bounds[3]+t/2) if horizontal else (p.bounds[0]-t/2 if side=='left' else p.bounds[2]+t/2)
            if abs(wall['a'][fixed]-expected) > .1:
                return False  # The canonical host must be a supported clear bounding side.
            axis = 0 if side in ('front', 'rear') else 1
            lo = max(p.bounds[axis], min(wall['a'][axis], wall['b'][axis])) + 150
            hi = min(p.bounds[axis + 2], max(wall['a'][axis], wall['b'][axis])) - 150
            if by_id[rid]['kind']=='stair' and kind!='window':
                lo=max(p.bounds[axis],min(wall['a'][axis],wall['b'][axis]))+50
                hi=min(p.bounds[axis+2],max(wall['a'][axis],wall['b'][axis]))-50
                stair=next((s for s in b['stairs'] if s['roomId']==rid),None)
                if stair:
                    if stair.get('rotation')==90:
                        if side=='left':return False
                        if horizontal:lo=max(lo,stair['x']+stair['depth']-stair['landing_mm']+50)
                    else:
                        if side=='rear':return False
                        if not horizontal:hi=min(hi,p.bounds[1]+stair['landing_mm']-50)
            if hi - lo < width:
                return False
            floor_index = next(i for i, f in enumerate(floors) if f['id'] == by_id[rid]['floorId'])
            slots=[(lo+hi-width)/2,lo,hi-width]
            for start,end in occupied.get(wall['id'],[]):slots.extend((start-width-150,end+150))
            for position in slots:
                if position<lo-.1 or position+width>hi+.1:continue
                o={'id':ident,'roomId':rid,'kind':kind,'side':side,'offset':round(position-p.bounds[axis],3),
                   'width':width,'height':height,'sill':sill,'hinge':'start'}
                plan['floors'][floor_index]['openings'].append(o)
                try:
                    compile_plan({**intent,'customPlan':plan})
                except DesignError:
                    plan['floors'][floor_index]['openings'].pop()
                    continue
                occupied.setdefault(wall['id'],[]).append((position,position+width))
                return True
            return False

        # Only actual authored neighbours receive proposed access; no room is moved
        # and no circulation is invented. Validate each host with the shared compiler.
        public={'living','drawing-room','family','dining','hall','inner-lobby','foyer','stair','stair-landing','veranda','outer-lobby'}
        for wall in b['walls']:
            if len(wall['rooms'])!=2 or frozenset(wall['rooms']) in explicit:continue
            a,c=[spaces[r] for r in wall['rooms']]
            if not a['walkable'] or not c['walkable']:continue
            if not (a['kind'] in public or c['kind'] in public or ({a['kind'],c['kind']} <= {'bedroom','bathroom','dress'} and a['kind']!=c['kind'])):continue
            width=800 if any(s['kind'] in ('bathroom','powder-room') for s in (a,c)) else 900
            ident='compass-door-'+sha(wall['id'])[:20]
            hosts=sorted(wall['rooms'],key=lambda rid:spaces[rid]['kind']!='stair')
            any(add_opening(wall,rid,'door',width,ident) for rid in hosts)

        if not site.get('entryRoomId'):
            entry_walls=sorted([w for w in b['walls'] if w['floor']==0 and len(w['rooms'])==1 and spaces[w['rooms'][0]]['kind'] in public],key=lambda w:(min(w['a'][1],w['b'][1]),w['id']))
            if not any(add_opening(w,w['rooms'][0],'entry',1000,'compass-main-entry') for w in entry_walls):
                issue('ENTRY_WALL','Choose or place a public ground-floor room with an external entrance wall.')

        outdoor={key for key,spec in SPACE_REGISTRY.items() if not spec['enclosed']}
        for room in rooms:
            if room['id'] not in polygons or room['kind'] not in LIT_KINDS | {'bathroom','utility','drying-room','powder-room'}:continue
            wet=SPACE_REGISTRY[room['kind']]['wet']
            height,sill=(900,1200) if wet else (1500,750)
            need=max(.6,polygons[room['id']].area/1e6*.10)
            candidates=sorted([w for w in b['walls'] if room['id'] in w['rooms'] and (len(w['rooms'])==1 or any(spaces[r]['kind'] in outdoor for r in w['rooms']))],key=lambda w:-LineString([w['a'],w['b']]).length)
            for wall in candidates:
                if need<=.001:break
                available=min(6000,math.floor((LineString([wall['a'],wall['b']]).length-450)/50)*50)
                width=min(available,max(600,math.ceil(need*1e6/height/50)*50))
                if width<450:continue
                ident='compass-window-'+sha({'wall':wall['id'],'room':room['id']})[:20]
                if add_opening(wall,room['id'],'window',width,ident,height,sill):need-=width*height/1e6

        for relation in compass['connections']:
            if relation['from'] not in polygons or relation['to'] not in polygons or relation['kind'] == 'separated':
                continue
            pair = {relation['from'], relation['to']}
            candidates = [w for w in b['walls'] if set(w['rooms']) == pair]
            kind = {'open': 'cased', 'attached': 'door'}.get(relation['kind'], relation['kind'])
            if not any(add_opening(w, rid, kind, relation['width'], relation['id']) for w in candidates for rid in (relation['from'],relation['to'])):
                issue('CONNECTION_WALL', 'The requested rooms need a shared wall wide enough for this connection.', by_id[relation['from']], connectionId=relation['id'])
            elif relation['kind'] == 'attached':
                changes.append({'message': f'Provide direct attachment access between {by_id[relation["from"]]["name"]} and {by_id[relation["to"]]["name"]}.'})
        if site.get('entryRoomId'):
            rid = site['entryRoomId']
            if rid not in polygons or by_id[rid]['floorId'] != floors[0]['id'] or by_id[rid]['kind'] not in ('living', 'drawing-room', 'family', 'dining', 'hall', 'foyer', 'outer-lobby', 'veranda'):
                issue('ENTRY_DESTINATION', 'Choose a public room on the ground floor as the entrance destination.')
            else:
                walls = sorted([w for w in b['walls'] if w['floor'] == 0 and w['rooms'] == [rid]], key=lambda w: min(w['a'][1], w['b'][1]))
                if not any(add_opening(w, rid, 'entry', 1000, 'compass-main-entry') for w in walls):
                    issue('ENTRY_WALL', 'The entry destination needs an external wall with enough width for its door.')
        plan = normalize_plan(plan, scope)
        result['customPlan'] = plan
        if not issues:
            final_building = compile_plan({**intent, 'customPlan': plan})
            result['review'] = validate_custom(final_building)
            result['valid'] = True
            for relation in compass['connections']:
                if relation['from'] in polygons and relation['to'] in polygons:
                    effects.append({'source': relation['id'], 'status': 'applied', 'message': f'{by_id[relation["from"]]["name"]} → {by_id[relation["to"]]["name"]}: {relation["kind"]} relationship checked on the authored walls.'})
            if site.get('entryRoomId'):
                effects.append({'source': 'entry-destination', 'status': 'applied', 'message': f'Main entrance opens into {by_id[site["entryRoomId"]]["name"]}.'})
            for stair in stair_links:
                applied = any(s['id'] == stair['id'] for s in plan['stairs'])
                effects.append({'source': stair['id'], 'status': 'applied' if applied else 'off', 'message': 'Linked stair core compiled into the included floors.' if applied else 'Stair link retained; no flight is included in this floor scope.'})
        changes.append({'message': f'Review {sum(len(f["openings"]) for f in plan["floors"])} proposed doors and windows on the actual room walls. No rooms were moved or resized.'})
    except DesignError as exc:
        detail = exc.details if isinstance(exc.details, dict) else {}
        for problem in detail.get('errors', [{'code': exc.code, 'message': str(exc)}]):
            issues.append({**problem, 'roomId': problem.get('id'), 'severity': 'error'})
    return result


def proposal(project, compass=None, scope=None):
    from .intent import fuse
    if not isinstance(project,dict):
        raise DesignError('COMPASS_SCHEMA','Supply a project object for Compass conversion.')
    data = compass if compass is not None else project.get('compass')
    base = {k: v for k, v in project.items() if k not in ('compass', 'compassScope', 'compassAcceptance', 'grid', 'customPlan', 'roomEdits', 'furnitureLayout')}
    # Compass uses the custom-plan programme limits, including a valid zero-bedroom design.
    base['customPlan'] = None
    intent = fuse(base, compass_draft=True)
    return compile_compass(data, intent['values'], scope, intent['placement_hints'])
