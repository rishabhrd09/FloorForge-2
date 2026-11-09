"""Actionable, read-only context for the existing geometry validators.

Diagnostics identify an editor, floor and room without changing the draft or
inventing a repair. Dimensions come from compiler sizes or measured polygons.
"""
from copy import deepcopy
import re

from .spaces import SPACE_REGISTRY

FLOOR_NAMES = ('Ground floor', 'First floor', 'Second floor')
PRIORITY = {'ENVELOPE': 0, 'ENVELOPE_TOO_SMALL': 0, 'FIELD_RANGE': 0,
            'EMPTY_FLOOR': 1, 'UNPLACED': 2, 'REQUIRED_ROOM_UNPLACED': 2,
            'STAIR_LINK': 3, 'STAIR_ALIGNMENT': 3, 'STAIR_FIT': 3, 'UNLINKED_STAIR': 3,
            'OPEN_SKY_BLOCKED': 4, 'UNSUPPORTED_FLOOR': 4,
            'SIZE_LOCK': 5, 'TEXT_CONFLICT': 5, 'NO_ENTRY': 6, 'ENTRY_WALL': 6,
            'UNREACHABLE': 7, 'BEDROOM_THROUGH_ROUTE': 7,
            'NO_EXTERNAL_WINDOW': 8, 'LOW_DAYLIGHT': 8, 'BATH_VENTILATION': 8}


def _layout(project):
    editor = project.get('editorState') or {}
    editor = editor if isinstance(editor, dict) else {}
    compass = project.get('compass')
    exact = project.get('customPlan')
    if not compass and not exact:
        compass = editor.get('compassDraft') if editor.get('mode') == 'compass' else None
        exact = editor.get('customPlan') if editor.get('mode') == 'custom' else None
    def records(value):
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
    def floors(value):
        # Keep the physical indices even when the compiler rejects a missing
        # stable ID; diagnostics must not shift First into Ground.
        return [item if isinstance(item, dict) else {} for item in value] if isinstance(value, list) else []
    if isinstance(compass, dict) and compass:
        return 'compass', floors(compass.get('floors')), records(compass.get('rooms'))
    if isinstance(exact, dict) and exact:
        levels = floors(exact.get('floors'))
        return 'plan', levels, [dict(room, floorId=floor.get('id'), floorIndex=i)
            for i, floor in enumerate(levels) for room in records(floor.get('rooms'))]
    return 'survey', [], []


def error_issues(error):
    """Retain contextual details from both compiler error shapes."""
    details = error.details if isinstance(error.details, dict) else {}
    records = details.get('errors') or details.get('rooms')
    if records:
        return [dict(item, code=item.get('code', error.code), message=item.get('message', str(error)))
                for item in records]
    issue = {**error.record(), **{key: details[key] for key in
             ('floor', 'floorId', 'floorIndex', 'roomId', 'id', 'ids', 'regions', 'cells', 'advice', 'field') if key in details}}
    if error.code in ('FIELD_RANGE', 'FIELD_TYPE', 'FIELD_CHOICE') and 'field' not in issue:
        # The existing field validator emits this exact stable identifier.
        # Carry it separately so the UI does not have to guess which input to open.
        match = re.match(r'(?:Invalid )?([a-z][a-z0-9_]*)\b', str(error))
        if match:
            issue['field'] = match.group(1)
    return [issue]


def enrich_issues(issues, project, sizes=()):
    kind, floors, rooms = _layout(project)
    by_id = {room['id']: room for room in rooms if isinstance(room.get('id'), str)}
    floor_indices = {floor['id']: i for i, floor in enumerate(floors) if isinstance(floor.get('id'), str)}
    measured = {size['roomId']: size for size in sizes}
    layout = project.get('compass') or project.get('customPlan') or {}
    layout = layout if isinstance(layout, dict) else {}
    stairs = layout.get('stairLinks', layout.get('stairs', []))
    stair_rooms = {stair['id']: stair['roomIds'] for stair in stairs
                   if isinstance(stair, dict) and isinstance(stair.get('id'), str) and isinstance(stair.get('roomIds'), list)} if isinstance(stairs, list) else {}
    result = []
    for raw in issues:
        item = deepcopy(raw)
        ident = item.get('roomId') or item.get('id')
        room = by_id.get(ident) if isinstance(ident, str) else None
        if not room and isinstance(ident, str) and ident in stair_rooms:
            item['ids'] = [rid for rid in stair_rooms[ident] if isinstance(rid, str) and rid in by_id]
            room = by_id.get(next(iter(item['ids']), None))
        # Validator IDs may name a floor, stair core or opening, not a room.
        if not isinstance(ident, str) or ident not in by_id:
            item.pop('roomId', None)
        if room:
            spec = SPACE_REGISTRY.get(room.get('kind'), {}) if isinstance(room.get('kind'), str) else {}
            item.update(roomId=room['id'], name=room.get('name') or spec.get('label', room['id']))
            if isinstance(room.get('floorId'), str):
                item['floorId'] = room['floorId']
            if type(room.get('floorIndex')) is int:
                item['floorIndex'] = room['floorIndex']
            if isinstance(room.get('regions'), list):
                item['regions'] = list(room['regions'])
            if room.get('polygon'):
                item['polygon'] = deepcopy(room['polygon'])
            required = {'minimum_width_mm': spec.get('minimum_width_mm', 0),
                        'minimum_area_m2': spec.get('minimum_area_m2', 0)}
            if isinstance(room.get('target'), dict) and room['target'].get('locked') and all(k in room['target'] for k in ('width', 'depth')):
                required.update(width_mm=room['target']['width'], depth_mm=room['target']['depth'], locked=True)
            item['required'] = required
            if room['id'] in measured:
                size = measured[room['id']]
                item['current'] = dict(zip(('width_mm', 'depth_mm'), size['clearSize']))
                item['current']['area_m2'] = size['area_m2']
            elif room.get('polygon'):
                from shapely.geometry import Polygon
                try:
                    shape = Polygon(room['polygon'])
                except (ValueError, TypeError, IndexError):
                    shape = None
                if shape is not None and shape.is_valid and not shape.is_empty:
                    x, y, x1, y1 = shape.bounds
                    item['current'] = {'width_mm': round(x1-x, 3), 'depth_mm': round(y1-y, 3),
                                       'area_m2': round(shape.area/1e6, 3)}
        elif isinstance(ident, str) and ident in floor_indices:
            item['floorId'] = ident
        index = floor_indices.get(item.get('floorId')) if isinstance(item.get('floorId'), str) else None
        if index is None:
            index = item.get('floorIndex', item.get('floor'))
        if type(index) is int and 0 <= index < len(floors):
            item.update(floor=index, floorIndex=index,
                        floorName=FLOOR_NAMES[index] if index < 3 else f'Floor {index+1}')
            if isinstance(floors[index].get('id'), str):
                item['floorId'] = floors[index]['id']
        item['message'] = item.get('message') or _fallback(item.get('code', ''), room)
        item['editor'] = editor_for(item, kind)
        result.append(item)
    return result


def _fallback(code, room):
    name = (room.get('name') or room.get('id', 'this room')) if room else 'this part of the home'
    messages = {'UNREACHABLE': f'{name} needs a continuous door and landing route from the main entrance.',
                'NO_EXTERNAL_WINDOW': f'{name} needs a window or glazed opening to outside air.',
                'STAIR_ALIGNMENT': 'The stair core must occupy matching areas on the connected floors.',
                'NO_ENTRY': 'Choose a public room along the road/front for the main entrance.',
                'EMPTY_FLOOR': 'Place the rooms on this requested floor before reviewing the whole home.'}
    return messages.get(code, f'Review {name}: {code.replace("_", " ").lower()}.')


def editor_for(issue, layout_kind):
    code = issue.get('code', '')
    if code in {'ENVELOPE', 'ENVELOPE_TOO_SMALL', 'FIELD_RANGE', 'FIELD_TYPE', 'FIELD_CHOICE',
                'PARKING_DEPTH', 'COMPASS_FLOORS', 'PLAN_FLOORS', 'REQUESTED_FLOORS', 'SITE_UNAVAILABLE'}:
        kind = 'plot'
    elif code.startswith('SOURCE_'):
        kind = 'inputs'
    elif code in {'TEXT_CONFLICT', 'TEXT_LIMIT'}:
        kind = layout_kind
    elif code.startswith('PROGRAMME_') or code == 'BEDROOM_PROGRAMME':
        kind = 'survey'
    else:
        kind = layout_kind
    if code in ('FIELD_RANGE', 'FIELD_TYPE', 'FIELD_CHOICE') and issue.get('field') in (
            'bedrooms', 'attached_baths', 'pooja', 'parking', 'eldercare'):
        kind = 'survey'
    result = {'kind': kind, 'view': 'map', **{key: issue[key] for key in
              ('floor', 'floorIndex', 'floorId', 'roomId', 'field') if key in issue}}
    if code in ('COMPASS_FLOORS', 'PLAN_FLOORS', 'REQUESTED_FLOORS'):
        result['field'] = 'storeys'
    return result


def first_issue(issues):
    return min(issues, key=lambda item: PRIORITY.get(item.get('code'), 9)) if issues else {
        'code': 'LAYOUT_REVIEW', 'message': 'Review the editable layout.', 'editor': {'kind': 'compass', 'view': 'map'}}


def next_steps(issue):
    code = issue.get('code', '')
    name = issue.get('name', 'the affected room')
    floor = issue.get('floorName', 'the affected floor')
    exact = issue.get('editor', {}).get('kind') == 'plan'
    if code in ('ENVELOPE', 'ENVELOPE_TOO_SMALL', 'FIELD_RANGE', 'PARKING_DEPTH'):
        return ['Open Plot basics and check the named measurement and units.',
                'Check that setbacks leave enough width and depth, then review the floor plans again.']
    if code == 'EMPTY_FLOOR':
        return [f'Open {floor} and place its intended rooms.',
                'Keep matching stair areas on connected floors.' + ('' if exact else
                ' Use the floor-scope control only if you explicitly want fewer floors.')]
    if code in ('UNPLACED', 'REQUIRED_ROOM_UNPLACED'):
        return [f'On {floor}, select {name} from the room checklist and assign connected cells.',
                'If this room is no longer wanted, explicitly change its required setting. Then check again.']
    if 'STAIR' in code:
        return (['Keep matching measured stair outlines on every connected floor.',
                 'Review the stair core dimensions, linked rooms, flights and landings in the exact plan editor.'] if exact else
                ['Place a Staircase room in matching cells on every connected floor; a landing label alone is not a staircase.',
                 'Leave room for both flights and landings, then use “Link matching authored stair rooms” under Connections.'])
    if code == 'SIZE_LOCK':
        return [f'Open {name} and compare its measured clear size with the locked target.',
                'Adjust its assigned cells, or explicitly unlock the size target in Room details before requesting a new recommendation.']
    if code in ('NO_EXTERNAL_WINDOW', 'LOW_DAYLIGHT', 'BATH_VENTILATION'):
        return [f'Place {name} beside an outside wall or an open-sky courtyard.',
                'Review the window or ventilation opening before checking the home again.']
    if code in ('NO_ENTRY', 'ENTRY_WALL'):
        return ['Place a living room, foyer or other public entrance room along the road/front.',
                'Choose it as the main door destination in Connections and check again.']
    if code in ('UNREACHABLE', 'BEDROOM_THROUGH_ROUTE', 'PORTAL_WIDTH'):
        return [f'Connect {name} to a hall, living room or stair landing along a usable shared wall.',
                'Keep a continuous public route from the main entrance; do not make a bedroom the only passage to another room.']
    if code in ('ROOM_MINIMUM', 'NARROW_NECK', 'COLLAPSED_ROOM'):
        return [f'Give {name} enough '+('measured clear space' if exact else 'connected cells')+' for its minimum size after walls.',
                'If neighbouring cells are occupied, review a proposed boundary change or explicitly reassign cells. Pinned rooms stay fixed.']
    if code == 'UNSUPPORTED_FLOOR':
        return [f'Compare {floor} with the floor below.', 'Move the projecting area inside the supporting outline, or explicitly add support through a professional design.']
    if code == 'OPEN_SKY_BLOCKED':
        return [f'Keep the area above {name} open on every higher floor.',
                'Move the upper rooms away, or explicitly change the lower space to an appropriate covered room type.']
    return [issue.get('advice') or issue.get('message', 'Review the highlighted area.'),
            'After changing the draft, check the floor plans again.']


def contextualize_question(question, issues, project, sizes=()):
    """Add precise targets to a question while preserving its answer identity."""
    question = deepcopy(question)
    enriched = enrich_issues(issues, project, sizes)
    problem = next((item for item in enriched if item.get('code') == question.get('code')), first_issue(enriched))
    kind, floors, rooms = _layout(project)
    by_id = {room['id']: room for room in rooms if isinstance(room.get('id'), str)}
    affected = question.get('affected') or []
    if not affected:
        affected = [problem]
        affected += [{'roomId': rid} for rid in problem.get('ids', []) if rid in by_id and rid != problem.get('roomId')]
    # A missing stair must point at the first floor without a staircase, rather
    # than highlighting only the stairs that already exist on other floors.
    if problem.get('code') == 'STAIR_LINK':
        missing = [dict(floorId=floor['id'], regions=[]) for floor in floors if isinstance(floor.get('id'), str)
                   if not any(room.get('kind') == 'stair' and room.get('regions', room.get('polygon'))
                              and room.get('floorId') == floor['id'] for room in rooms)]
        affected = missing + affected
    contextual = enrich_issues([{'code': problem['code'], **item} for item in affected], project, sizes)
    keys = ('floor', 'floorIndex', 'floorId', 'floorName', 'roomId', 'name', 'regions', 'polygon', 'current', 'required')
    question['affected'] = [{key: item[key] for key in keys if key in item} for item in contextual]
    question['affected'] = [item for item in question['affected'] if item]
    target = next((item for item in contextual if item.get('floorId') or item.get('roomId')), problem)
    question['editor'] = editor_for({**problem, **{key: target[key] for key in
        ('floor', 'floorIndex', 'floorId', 'roomId') if key in target}}, kind)
    question['steps'] = next_steps({**problem, **{key: target[key] for key in ('floorName', 'name') if key in target}})
    question['issue'] = problem
    question['remainingIssueCount'] = max(0, len(issues)-1)
    question['draftPreserved'] = True
    for choice in question.get('choices', []):
        if choice.get('action', '').startswith(('edit', 'review-')):
            choice.setdefault('editor', deepcopy(question['editor']))
            if choice['action'] in ('edit-plot', 'review-plot'):
                choice['editor'] = {'kind': 'plot'}
            elif choice['action'] == 'edit-survey':
                choice['editor'] = {'kind': 'survey'}
    return question
