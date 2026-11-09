"""Versioned, road-relative Compass drafts. No legacy grid interpretation lives here."""
from __future__ import annotations

import copy
import json
import math
import re
from fractions import Fraction
from pathlib import Path
from .model import DesignError, sha
from .spaces import SPACE_REGISTRY

SCHEMA = 'floorforge.compass-input/1'
# New partitions/programme choices opt into v2. Reading a v1 draft does not
# rewrite its serialized content or invalidate its reviewed geometry identity.
SPLIT_SCHEMA = 'floorforge.compass-input/2'
ADAPTER = 'compass/2'
ID = re.compile(r'[A-Za-z][A-Za-z0-9_.-]{0,79}')
GRID_OPTIONS = json.loads(Path(__file__).with_name('compass_grids.json').read_text())
# Legacy 32-cell projects retain their exact coordinates and generation identity.
GRID_SHAPES = {(s['cols'], s['rows']) for s in GRID_OPTIONS} | {(4, 8)}


def fail(code, message, **details):
    raise DesignError('COMPASS_' + code, message, details)


def fields(obj, allowed, label):
    if not isinstance(obj, dict) or set(obj) - set(allowed):
        fail('SCHEMA', f'Unsupported fields in {label}.')


def number(value, lo, hi, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
        fail('NUMBER', f'{label} must be a finite number between {lo:g} and {hi:g}.')


def cell(value, rows, cols=4):
    if not isinstance(value, str) or not re.fullmatch(r'(?:0|[1-9][0-9]?):(?:0|[1-9][0-9]?)(?::[LRFB])?', value):
        fail('REGION', 'Use row:column, or row:column:L/R/F/B for a divided cell.')
    parts = value.split(':')
    row, col = map(int, parts[:2])
    if row >= rows or col >= cols:
        fail('REGION', 'Region is outside this grid.', region=value)
    return row, col, parts[2] if len(parts) == 3 else None


def microcells(regions, rows, cols=4):
    """Exact quarter occupancy for adjacency; authors still choose two halves."""
    result = set()
    for ref in regions:
        row, col, half = cell(ref, rows, cols)
        result.update((2 * row + y, 2 * col + x) for y in (0, 1) for x in (0, 1)
                      if (half not in ('L', 'R') or half == ('L', 'R')[x])
                      and (half not in ('F', 'B') or half == ('F', 'B')[y]))
    return result


def connected(regions, rows, cols=4):
    todo = microcells(regions, rows, cols)
    if not todo:
        return True
    pending = [todo.pop()]
    while pending:
        row, col = pending.pop()
        for neighbour in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbour in todo:
                todo.remove(neighbour)
                pending.append(neighbour)
    return not todo


def normalize(value):
    fields(value, ('schema', 'grid', 'floors', 'rooms', 'connections', 'stairLinks', 'site', 'requirements', 'programme'), 'Compass input')
    if value.get('schema') not in (SCHEMA, SPLIT_SCHEMA):
        fail('VERSION', 'This Compass version is unsupported. Keep the original project file for recovery.')
    out = copy.deepcopy(value)
    modern = out['schema'] == SPLIT_SCHEMA
    if 'programme' in out and (not modern or out['programme'] != 'drawn'):
        fail('PROGRAMME', 'Drawn-room generation requires Compass version 2.')
    grid = out.get('grid')
    fields(grid, ('rows', 'cols', 'basis', 'rowOrigin'), 'Compass grid')
    if type(grid.get('rows')) is not int or type(grid.get('cols')) is not int or (grid['cols'], grid['rows']) not in GRID_SHAPES:
        fail('GRID', 'Choose 4 × 4, 4 × 5, 4 × 6, 5 × 5 or 6 × 7 (across × deep). Saved 4 × 8 maps remain supported.')
    if grid.get('basis') != 'buildable-envelope' or grid.get('rowOrigin') != 'front':
        fail('BASIS', 'Compass uses the buildable envelope with row zero at the front.')
    rows, cols = grid['rows'], grid['cols']
    seen = set()

    def ident(obj):
        key = obj.get('id')
        if not isinstance(key, str) or not ID.fullmatch(key) or key in seen:
            fail('ID', 'Use unique stable identifiers for floors, rooms and relationships.', id=key)
        seen.add(key)

    floors = out.get('floors')
    if not isinstance(floors, list) or not 1 <= len(floors) <= 3:
        fail('FLOORS', 'Keep one to three occupied-floor drafts.')
    splits = {}
    for floor in floors:
        fields(floor, ('id', 'splits', 'horizontalSplits') if modern else ('id', 'splits'), 'Compass floor')
        ident(floor)
        floor.setdefault('splits', [])
        orientations = {}
        for field, halves in (('splits', 'LR'), ('horizontalSplits', 'FB')):
            refs = floor.get(field, [])
            if not isinstance(refs, list) or len(refs) > rows * cols or len(set(map(str, refs))) != len(refs):
                fail('SPLITS', 'List each divided base cell once.')
            for ref in refs:
                if cell(ref, rows, cols)[2] is not None or ref in orientations:
                    fail('SPLITS', 'Each base cell can have one split direction.')
                orientations[ref] = halves
            if field in floor:
                floor[field] = sorted(refs)
        splits[floor['id']] = orientations
    rooms = out.get('rooms')
    if not isinstance(rooms, list) or len(rooms) > 360:
        fail('ROOMS', 'Use at most 120 rooms per floor.')
    occupied = set()
    for room in rooms:
        fields(room, ('id', 'floorId', 'kind', 'name', 'role', 'regions', 'required', 'target', 'mechanicalVentilation', 'drain'), 'Compass room')
        ident(room)
        if not isinstance(room.get('floorId'),str) or room['floorId'] not in splits or not isinstance(room.get('kind'),str) or room['kind'] not in SPACE_REGISTRY:
            fail('ROOM', 'Choose a supported room type and an existing floor.', roomId=room['id'])
        if not isinstance(room.get('name'), str) or not 1 <= len(room['name'].strip()) <= 120:
            fail('NAME', 'Give the room a name of 1–120 characters.')
        room['name'] = room['name'].strip()
        if room.get('role', '') not in ('', 'master', 'caregiver'):
            fail('ROLE', 'Use master or caregiver as an optional room role.')
        for key in ('required', 'mechanicalVentilation', 'drain'):
            if key in room and type(room[key]) is not bool:
                fail('BOOLEAN', f'{key} must be true or false.')
        refs = room.setdefault('regions', [])
        if not isinstance(refs, list) or len(refs) > rows * cols * 2 or len(set(map(str, refs))) != len(refs):
            fail('REGIONS', 'List each room region once.')
        for ref in refs:
            row, col, half = cell(ref, rows, cols)
            orientation = splits[room['floorId']].get(f'{row}:{col}')
            if (orientation is None and half is not None) or (orientation is not None and (half is None or half not in orientation)):
                fail('PARTITION', 'Use halves only in divided cells; keep whole cells elsewhere.', roomId=room['id'], region=ref)
            for y, x in microcells([ref], rows, cols):
                key = (room['floorId'], y, x)
                if key in occupied:
                    fail('OWNERSHIP', 'A region can belong to only one room.', roomId=room['id'], region=ref)
                occupied.add(key)
        if not connected(refs, rows, cols):
            fail('CONNECTED', f'{room["name"]} must share edges; corner contact does not join a room.', roomId=room['id'], regions=refs)
        room['regions'] = sorted(refs)
        if 'target' in room:
            target = room['target']
            fields(target, ('width', 'depth', 'locked'), 'room size target')
            for key in ('width', 'depth'):
                number(target.get(key), 300, 60000, key)
            if type(target.get('locked', False)) is not bool:
                fail('BOOLEAN', 'A size lock must be true or false.')
    by_id = {r['id']: r for r in rooms}
    for floor in floors:
        if sum(r['floorId'] == floor['id'] for r in rooms) > 120:
            fail('ROOMS', 'Use at most 120 rooms per floor.')
    links = out.setdefault('connections', [])
    if not isinstance(links, list) or len(links) > 360:
        fail('CONNECTIONS', 'Use at most 360 room relationships.')
    pairs = set()
    for link in links:
        fields(link, ('id', 'from', 'to', 'kind', 'width'), 'connection')
        ident(link)
        if not isinstance(link.get('from'),str) or not isinstance(link.get('to'),str) or link['from'] not in by_id or link['to'] not in by_id or link['from'] == link['to']:
            fail('CONNECTION', 'A connection needs two distinct existing rooms.')
        if by_id[link['from']]['floorId'] != by_id[link['to']]['floorId']:
            fail('CONNECTION', 'Connect rooms on one floor; use stair links between floors.')
        pair = tuple(sorted((link['from'], link['to'])))
        if pair in pairs:
            fail('CONNECTION', 'Keep one explicit relationship per room pair.')
        pairs.add(pair)
        if link.get('kind') not in ('door', 'open', 'separated', 'attached', 'glazed'):
            fail('CONNECTION', 'Choose door, open, separated, attached or glazed.')
        number(link.setdefault('width', 900), 700, 6000, 'connection width')
        if link['kind'] == 'attached' and not any(by_id[i]['kind'] in ('bathroom', 'powder-room', 'dress') for i in pair):
            fail('ATTACHMENT', 'An attachment must include a bathroom or dressing room.')
    stairs = out.setdefault('stairLinks', [])
    if not isinstance(stairs, list) or len(stairs) > 8:
        fail('STAIRS', 'Use at most eight linked stair cores.')
    for stair in stairs:
        fields(stair, ('id', 'roomIds', 'flightWidth', 'well', 'landing', 'tread', 'rotation'), 'stair link')
        ident(stair)
        ids = stair.get('roomIds')
        if not isinstance(ids, list) or not 1 <= len(ids) <= 3 or len(set(map(str, ids))) != len(ids) or any(not isinstance(i,str) or i not in by_id or by_id[i]['kind'] != 'stair' for i in ids):
            fail('STAIRS', 'Link actual stair rooms on consecutive occupied floors.')
        indices = [next(i for i, f in enumerate(floors) if f['id'] == by_id[r]['floorId']) for r in ids]
        if indices != list(range(indices[0], indices[0] + len(indices))):
            fail('STAIRS', 'Stair links must be ordered and consecutive.')
        for key, default, lo, hi in (('flightWidth', 1000, 800, 2500), ('well', 200, 0, 1000), ('landing', 1050, 800, 2500), ('tread', 250, 250, 350)):
            number(stair.setdefault(key, default), lo, hi, key)
        if stair.get('rotation', 0) not in (0, 90):
            fail('STAIRS', 'Use a 0° or 90° stair core.')
    site = out.setdefault('site', {})
    fields(site, ('context', 'gate', 'entryRoomId', 'zones', 'secondRoad'), 'site')
    if site.setdefault('context', 'unknown') not in ('unknown', 'middle', 'corner', 'three-open', 'independent'):
        fail('SITE', 'Choose a supported plot context.')
    if site.setdefault('gate', 'planner') not in ('planner', 'left', 'center', 'right'):
        fail('GATE', 'Choose planner, left, center or right.')
    if site.get('entryRoomId') is not None and (not isinstance(site['entryRoomId'],str) or site['entryRoomId'] not in by_id):
        fail('ENTRY', 'The entry destination must be an existing room.')
    if 'secondRoad' in site:
        number(site['secondRoad'], 0, 359.999, 'second-road bearing')
    zones = site.setdefault('zones', [])
    if not isinstance(zones, list) or len(zones) > 8:
        fail('SITE', 'Use at most eight site zone requests.')
    for zone in zones:
        fields(zone, ('id', 'kind', 'band'), 'site zone')
        ident(zone)
        if zone.get('kind') not in ('garden', 'yard', 'parking', 'arrival') or zone.get('band') not in ('front', 'rear', 'left', 'right'):
            fail('SITE', 'Use a typed outdoor site-band request.')
    requirements = out.setdefault('requirements', [])
    if not isinstance(requirements, list) or len(requirements) > 200:
        fail('REQUIREMENTS', 'Keep at most 200 explicit requirements.')
    for requirement in requirements:
        fields(requirement, ('id', 'kind', 'roomId', 'value', 'source'), 'requirement')
        ident(requirement)
        if requirement.get('kind') not in ('note', 'keep-map', 'access-width'):
            fail('REQUIREMENT', 'Unsupported operational requirement; preserve it as a note.')
        if 'roomId' in requirement and (not isinstance(requirement['roomId'],str) or requirement['roomId'] not in by_id):
            fail('REQUIREMENT', 'Requirement refers to a missing room.')
        if requirement['kind'] == 'access-width':
            if requirement.get('roomId') not in by_id:
                fail('REQUIREMENT', 'A passage-width requirement needs a room.')
            number(requirement.get('value'), 800, 5000, 'clear access width')
        elif not isinstance(requirement.get('value'), str) or len(requirement['value']) > 2000:
            fail('REQUIREMENT', 'Notes and map resolutions must be text up to 2,000 characters.')
        if 'source' in requirement and (not isinstance(requirement['source'], str) or len(requirement['source']) > 120):
            fail('REQUIREMENT', 'Use a short provenance label.')
    out['rooms'] = sorted(rooms, key=lambda r: r['id'])
    out['connections'] = sorted(links, key=lambda c: c['id'])
    out['stairLinks'] = sorted(stairs, key=lambda s: s['id'])
    out['requirements'] = sorted(requirements, key=lambda r: r['id'])
    return out


def source_hash(compass, values, scope):
    """All effective site/theme facts count; archived floors do not change a scoped result."""
    data = normalize(compass)
    included = {f['id'] for f in data['floors'][:scope]}
    data['floors'] = data['floors'][:scope]
    data['rooms'] = [r for r in data['rooms'] if r['floorId'] in included]
    ids = {r['id'] for r in data['rooms']}
    data['connections'] = [c for c in data['connections'] if c['from'] in ids and c['to'] in ids]
    data['stairLinks'] = [{**s, 'roomIds': [r for r in s['roomIds'] if r in ids]} for s in data['stairLinks']]
    data['stairLinks'] = [s for s in data['stairLinks'] if s['roomIds']]
    data['requirements'] = [r for r in data['requirements'] if r['kind']!='note' and ('roomId' not in r or r['roomId'] in ids)]
    data['site'].pop('context', None)  # Advisory context does not claim a geometry effect.
    return sha({'compass': data, 'values': values, 'scope': scope, 'adapterVersion': ADAPTER})


def remap(value, rows, cols=None):
    """Preview every floor; never choose a majority owner or discard a room silently."""
    original = normalize(value)
    # Older clients send only rows; new clients always send both dimensions.
    cols = original['grid']['cols'] if cols is None else cols
    if type(rows) is not int or type(cols) is not int or (cols, rows) not in GRID_SHAPES:
        fail('GRID', 'Choose a supported grid shape (across × deep).')
    candidate = copy.deepcopy(original)
    old_rows, old_cols = original['grid']['rows'], original['grid']['cols']
    candidate['grid'].update(rows=rows, cols=cols)
    issues, changes = [], []
    if (old_cols, old_rows) == (cols, rows):
        return {'valid': True, 'candidate': candidate, 'issues': [], 'changes': [], 'sourceHash': sha(original),
                'message': 'The grid is unchanged.'}
    # Exact rational intervals on BOTH axes, including empty space. A partial
    # overlap must not silently grow a room across an unassigned boundary.
    def axis_overlaps(count, old_count):
        return [[old for old in range(old_count)
                 if min(Fraction(i + 1, count), Fraction(old + 1, old_count)) >
                    max(Fraction(i, count), Fraction(old, old_count))] for i in range(count)]
    ys, xs = axis_overlaps(2 * rows, 2 * old_rows), axis_overlaps(2 * cols, 2 * old_cols)
    by_id = {r['id']: r for r in candidate['rooms']}
    for room in candidate['rooms']:
        room['regions'] = []
    for floor in candidate['floors']:
        floor['splits'] = []
        if 'horizontalSplits' in floor:
            floor['horizontalSplits'] = []
        owners = {}
        for room in original['rooms']:
            if room['floorId'] == floor['id']:
                owners.update({(y, x): room['id'] for y, x in microcells(room['regions'], old_rows, old_cols)})
        pixels = {}
        for y in range(2 * rows):
            for x in range(2 * cols):
                overlaps = {owners.get((oy, ox)) for oy in ys[y] for ox in xs[x]}
                if len(overlaps) > 1:
                    ids = sorted(r for r in overlaps if r is not None)
                    names = ', '.join(by_id[r]['name'] for r in ids) + (' and unassigned space' if None in overlaps else '')
                    issues.append({'code': 'REMAP_BOUNDARY' if None in overlaps else 'REMAP_COLLISION', 'floorId': floor['id'], 'region': f'{y//2}:{x//2}', 'roomIds': ids, 'message': f'{floor["id"]} · row {y//2+1}, column {x//2+1}: {names} share a proposed region. Keep this grid or revise those assignments first.'})
                pixels[y, x] = next(iter(overlaps)) if len(overlaps) == 1 else None
        for y in range(rows):
            for x in range(cols):
                fl, fr, bl, br = (pixels[2*y+dy, 2*x+dx] for dy, dx in ((0,0),(0,1),(1,0),(1,1)))
                if fl == fr == bl == br:
                    if fl:
                        by_id[fl]['regions'].append(f'{y}:{x}')
                elif fl == bl and fr == br:
                    floor['splits'].append(f'{y}:{x}')
                    for half, owner in zip(('L', 'R'), (fl, fr)):
                        if owner:
                            by_id[owner]['regions'].append(f'{y}:{x}:{half}')
                elif fl == fr and bl == br:
                    candidate['schema'] = SPLIT_SCHEMA
                    floor.setdefault('horizontalSplits', []).append(f'{y}:{x}')
                    for half, owner in zip(('F', 'B'), (fl, bl)):
                        if owner:
                            by_id[owner]['regions'].append(f'{y}:{x}:{half}')
                else:
                    issues.append({'code': 'REMAP_PARTITION', 'floorId': floor['id'], 'region': f'{y}:{x}',
                                   'message': f'Row {y+1}, column {x+1} would need quarter cells. Keep this grid or revise its assignments.'})
    for room in candidate['rooms']:
        previous = next(r for r in original['rooms'] if r['id'] == room['id'])
        if previous['regions'] and not room['regions']:
            issues.append({'code': 'REMAP_LOSS', 'roomId': room['id'], 'message': f'{room["name"]} would lose all its assigned space.'})
        if not connected(room['regions'], rows, cols):
            issues.append({'code': 'REMAP_DISCONNECTED', 'roomId': room['id'], 'message': f'{room["name"]} would become disconnected.'})
        if previous['regions'] != room['regions'] or (old_cols, old_rows) != (cols, rows):
            changes.append({'roomId': room['id'], 'name': room['name'], 'before': previous['regions'], 'after': room['regions']})
    return {'valid': not issues, 'candidate': candidate, 'issues': issues, 'changes': changes,
            'sourceHash': sha(original), 'message': 'Grid remapping changes allocation spans. Review every affected floor before applying.'}
