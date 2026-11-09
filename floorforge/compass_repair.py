"""Bounded ownership proposals for Compass, including fully occupied floors.

The existing compiler remains the authority. HiGHS chooses among a deliberately
small set of connected shapes; it does not prove feasibility of arbitrary house
plans. No proposal is applied here, and no room/floor/type is removed.
"""
from __future__ import annotations

import copy
import math
import time
import threading
from collections import OrderedDict
from itertools import product

import networkx as nx
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
from shapely.geometry import box
from shapely.ops import unary_union

from .compass_input import microcells, normalize
from .compass_adapter import proposal
from .model import DesignError, sha
from .spaces import SPACE_REGISTRY

MAX_SECONDS = 6.0
MAX_CHECKED = 12
MAX_OPTIONS = 1600
_CACHE = OrderedDict()
_CACHE_LOCK = threading.RLock()
_PUBLIC = {'living', 'drawing-room', 'family', 'dining', 'hall', 'inner-lobby',
           'foyer', 'stair', 'stair-landing', 'veranda', 'outer-lobby'}


def _connected(cells):
    if not cells:
        return False
    graph = nx.Graph()
    graph.add_nodes_from(cells)
    graph.add_edges_from((a, (a[0]+dy, a[1]+dx)) for a in cells
                         for dy, dx in ((1, 0), (0, 1))
                         if (a[0]+dy, a[1]+dx) in cells)
    return nx.is_connected(graph)


def _adjacent(a, b):
    return any((y+dy, x+dx) in b for y, x in a
               for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))


def _atoms(floor, rows, cols):
    result = []
    for row in range(rows):
        for col in range(cols):
            ref = f'{row}:{col}'
            halves = 'LR' if ref in floor['splits'] else 'FB' if ref in floor.get('horizontalSplits', []) else ''
            for name in [ref+':'+h for h in halves] if halves else [ref]:
                result.append((name, frozenset(microcells([name], rows, cols))))
    return result


def _refs(cells, atoms):
    selected = [(name, group) for name, group in atoms if group <= cells]
    return sorted(name for name, group in selected) if set().union(*(group for name, group in selected)) == cells else None


def _bounds(cells):
    return min(x for y, x in cells), min(y for y, x in cells), max(x for y, x in cells)+1, max(y for y, x in cells)+1


def _center(cells):
    return sum(x for y, x in cells)/len(cells), sum(y for y, x in cells)/len(cells)


def _minimum(room, cells, sx, sy, values, links):
    if not _connected(cells):
        return False
    spec = SPACE_REGISTRY[room['kind']]
    shape = unary_union([box(x*sx, y*sy, (x+1)*sx, (y+1)*sy) for y, x in cells])
    clear = shape.buffer(-75, join_style=2) if spec['enclosed'] else shape
    if clear.is_empty or clear.geom_type != 'Polygon' or clear.interiors:
        return False
    x, y, x1, y1 = clear.bounds
    width = spec['minimum_width_mm']
    if min(x1-x, y1-y)+.1 < width or clear.area+1 < spec['minimum_area_m2']*1e6:
        return False
    core = clear.buffer(-width/2+1, join_style=2) if width else clear
    if core.is_empty or core.geom_type != 'Polygon':
        return False
    if room['kind'] == 'stair':
        link = next((s for s in links if room['id'] in s['roomIds']), {})
        sw = 2*link.get('flightWidth', 1000)+link.get('well', 200)
        sd = 2*link.get('landing', 1050)+(math.ceil(values['floor_height_mm']/190/2)-1)*link.get('tread', 250)
        if link.get('rotation', 0):
            sw, sd = sd, sw
        if abs(clear.area-(x1-x)*(y1-y)) > 1 or x1-x+.1 < sw or y1-y+.1 < sd:
            return False
    target = room.get('target', {})
    if target.get('locked') and any(abs(a-target[k]) >= 1 for a, k in ((x1-x, 'width'), (y1-y, 'depth'))):
        return False
    return True


def allocation_graph(draft, scope=None):
    """Potential edge adjacency, explicitly not proof of a usable door route."""
    rows, cols = draft['grid']['rows'], draft['grid']['cols']
    floors = draft['floors'][:scope]
    included = {f['id'] for f in floors}
    rooms = [r for r in draft['rooms'] if r['floorId'] in included and r['regions']]
    cells = {r['id']: microcells(r['regions'], rows, cols) for r in rooms}
    graph = nx.Graph()
    graph.add_nodes_from(r['id'] for r in rooms)
    for i, room in enumerate(rooms):
        for other in rooms[i+1:]:
            if room['floorId'] == other['floorId'] and _adjacent(cells[room['id']], cells[other['id']]):
                graph.add_edge(room['id'], other['id'])
    return {'kind': 'potential-allocation-adjacency', 'nodes': sorted(graph),
            'edges': sorted([sorted(e) for e in graph.edges]),
            'floorOccupancy': [{'floorId': f['id'],
                                'occupiedMicrocells': len(set().union(*(cells[r['id']] for r in rooms if r['floorId'] == f['id']))),
                                'capacityMicrocells': rows*cols*4} for f in floors],
            'doorRoutesRequireCompiler': True}


def _shape_options(draft, values, pins, deadline):
    rows, cols = draft['grid']['rows'], draft['grid']['cols']
    sx = (values['width_mm']-values['left_mm']-values['right_mm']-150)/(cols*2)
    sy = (values['depth_mm']-values['front_mm']-values['rear_mm']-150)/(rows*2)
    if min(sx, sy) <= 0:
        return {}, {}
    floors = {f['id']: _atoms(f, rows, cols) for f in draft['floors']}
    existing = {r['id']: frozenset(microcells(r['regions'], rows, cols)) for r in draft['rooms'] if r['regions']}
    rooms = {r['id']: r for r in draft['rooms'] if r['regions']}
    if len(rooms) > 48:
        return {}, existing
    options = {rid: {cells} for rid, cells in existing.items()}
    frozen = {rid for rid, r in rooms.items() if rid in pins or r.get('target', {}).get('locked')
              or not SPACE_REGISTRY[r['kind']]['enclosed'] or not SPACE_REGISTRY[r['kind']]['floor']}
    for rid, old in existing.items():
        if time.perf_counter() >= deadline:
            break
        room = rooms[rid]
        if rid in frozen:
            continue
        x0, y0, x1, y1 = _bounds(old)
        # A local rectangle neighbourhood; no enumeration of arbitrary partitions.
        axes = [sorted({min(max(v+d, 0), end) for d in (-2, -1, 0, 1, 2)})
                for v, end in ((x0, 2*cols), (y0, 2*rows), (x1, 2*cols), (y1, 2*rows))]
        raw = []
        for a, b, c, d in product(*axes):
            if a >= c or b >= d:
                continue
            shape = frozenset((y, x) for y in range(b, d) for x in range(a, c))
            delta = len(old ^ shape)
            if delta > max(16, len(old)//2) or _refs(shape, floors[room['floorId']]) is None:
                continue
            # Reject changes to any fixed owner's cells before geometry work.
            if any(shape & existing[fixed] for fixed in frozen
                   if fixed != rid and rooms[fixed]['floorId'] == room['floorId']):
                continue
            raw.append((delta, len(old-shape), tuple(sorted(shape)), shape))
        for _, _, _, shape in sorted(raw)[:40]:
            options[rid].add(shape)
        # Whole-allocation swaps let interior rooms reach an exterior wall.
        for other, shape in existing.items():
            if other not in frozen and rooms[other]['floorId'] == room['floorId'] and .4 <= len(shape)/len(old) <= 2.5 and _refs(shape, floors[room['floorId']]) is not None:
                options[rid].add(shape)
    # If one room borrows an occupied boundary, its neighbour can retain its
    # connected remainder, including L-shaped circulation. No cells disappear.
    transfers = [(rid, shape) for rid, variants in options.items() for shape in variants]
    for rid, shape in transfers:
        if time.perf_counter() >= deadline:
            return {}, existing
        for donor, old in existing.items():
            if donor == rid or donor in frozen or rooms[donor]['floorId'] != rooms[rid]['floorId'] or not shape & old:
                continue
            remainder = old-shape
            # A moved room may exchange its vacated cells with a connected
            # neighbour; this repairs occupied stair alignment without forcing
            # every other room to relocate. Exact-cover constraints choose one
            # owner for any released cell.
            for balance in (remainder, remainder | (existing[rid]-shape)):
                if balance and _refs(balance, floors[rooms[donor]['floorId']]) is not None:
                    options[donor].add(frozenset(balance))
    output = {}
    for rid, variants in options.items():
        room = rooms[rid]
        ranked = sorted(variants, key=lambda cells: (len(cells ^ existing[rid]), tuple(sorted(cells))))
        output[rid] = [cells for cells in ranked[:96] if _minimum(room, cells, sx, sy, values, draft['stairLinks'])]
        if time.perf_counter() >= deadline:
            return {}, existing
    return output, existing


def _changes(before, after):
    old = {r['id']: r for r in before['rooms']}
    return [{'code': 'REASSIGN_REGIONS', 'roomId': r['id'], 'floorId': r['floorId'],
             'name': r['name'], 'before': old[r['id']]['regions'], 'after': r['regions'],
             'message': f'Review changed space for {r["name"]}; its identity, type and floor are retained.'}
            for r in after['rooms'] if r['regions'] != old[r['id']]['regions']]


def search(project, compass, initial, *, max_seconds=MAX_SECONDS, max_checked=MAX_CHECKED):
    """Return validated choices, never an applied replacement or infeasibility claim."""
    started = time.perf_counter()
    deadline = started+max(0, min(float(max_seconds), 30))
    draft = normalize(compass)
    scope = initial['scope']
    pins = project.get('designJourney', {}).get('pins', {})
    pinned = set(pins.get('positions', [])) | set(pins.get('dimensions', []))
    key = sha({'project': project, 'draft': draft, 'scope': scope, 'maxSeconds': max_seconds, 'maxChecked': max_checked})
    with _CACHE_LOCK:
        if key in _CACHE:
            result = copy.deepcopy(_CACHE[key]); result['search']['cacheHit'] = True
            return result
    metadata = {'method': 'bounded-shape-ownership/HiGHS', 'maxSeconds': max_seconds,
                'maxValidatedCandidates': max_checked, 'checked': 0, 'solverRuns': 0,
                'globalOptimality': False, 'provenInfeasible': False, 'cacheHit': False}
    result = {'alternatives': [], 'applied': False, 'search': metadata,
              'graph': allocation_graph(draft, scope)}
    blocking = {'EMPTY_FLOOR', 'UNPLACED', 'ROOM_UNAVAILABLE', 'SITE_UNAVAILABLE', 'SIZE_LOCK', 'TEXT_CONFLICT', 'BEDROOM_PROGRAMME'}
    missing_core = any(p['code'] == 'STAIR_LINK' for p in initial['issues']) and any(
        not any(r['kind'] == 'stair' and r['regions'] and r['floorId'] == f['id'] for r in draft['rooms'])
        for f in draft['floors'][:scope])
    if initial['valid'] or missing_core or any(p['code'] in blocking for p in initial['issues']):
        metadata['status'] = 'not-needed' if initial['valid'] else 'clarification-required'
    else:
        included = {f['id'] for f in draft['floors'][:scope]}
        work = copy.deepcopy(draft)
        work['rooms'] = [r for r in work['rooms'] if r['floorId'] in included]
        choices, original = _shape_options(work, initial['values'], pinned, deadline)
        rooms = {r['id']: r for r in work['rooms'] if r['regions']}
        if not choices or any(not x for x in choices.values()) or len(rooms) > 48 or sum(map(len, choices.values())) > MAX_OPTIONS:
            metadata['status'] = 'time-limit' if time.perf_counter() >= deadline else 'candidate-limit'
        else:
            variants = [(rid, cells) for rid in sorted(choices) for cells in choices[rid]]
            byroom = {rid: [i for i, (other, _) in enumerate(variants) if other == rid] for rid in rooms}
            coeff, lower, upper = [], [], []
            def constraint(items, lo, hi):
                coeff.append(dict(items)); lower.append(lo); upper.append(hi)
            for rid, indices in byroom.items():
                constraint(((i, 1) for i in indices), 1, 1)
            occupied = {(r['floorId'], y, x) for rid, r in rooms.items() for y, x in original[rid]}
            covered = {}
            for i, (rid, cells) in enumerate(variants):
                for y, x in cells:
                    covered.setdefault((rooms[rid]['floorId'], y, x), []).append(i)
            for atom in sorted(set(covered) | occupied):
                constraint(((i, 1) for i in covered.get(atom, [])), int(atom in occupied), 1)
            # Coordinate every linked stair (or the sole core on each floor).
            groups = [[rid for rid in s['roomIds'] if rid in rooms] for s in work['stairLinks']]
            if not groups and scope > 1:
                byfloor = [[r['id'] for r in rooms.values() if r['floorId'] == f['id'] and r['kind'] == 'stair'] for f in work['floors'][:scope]]
                if all(len(ids) == 1 for ids in byfloor):
                    groups = [[ids[0] for ids in byfloor]]
            for group in groups:
                for rid in group[1:]:
                    first = group[0]
                    for cell in set().union(*choices[first], *choices[rid]):
                        constraint([(i, 1) for i in byroom[first] if cell in variants[i][1]]+
                                   [(i, -1) for i in byroom[rid] if cell in variants[i][1]], 0, 0)
            objective = []
            for rid, cells in variants:
                old = original[rid]
                move = math.dist(_center(old), _center(cells))
                # Preserve arrangement first. Target dimensions remain a soft
                # preference unless locked; physical validation is never soft.
                x0, y0, x1, y1 = _bounds(cells)
                target = rooms[rid].get('target', {})
                sx = (initial['values']['width_mm']-initial['values']['left_mm']-initial['values']['right_mm']-150)/(work['grid']['cols']*2)
                sy = (initial['values']['depth_mm']-initial['values']['front_mm']-initial['values']['rear_mm']-150)/(work['grid']['rows']*2)
                preference = (abs((x1-x0)*sx-150-target['width'])+abs((y1-y0)*sy-150-target['depth']))/1000 if target else 0
                objective.append(1000*bool(cells != old)+10*len(cells ^ old)+move+preference)
            seen_signatures = set()
            while metadata['checked'] < max_checked and time.perf_counter() < deadline:
                rr, cc, dd = [], [], []
                for row, values in enumerate(coeff):
                    for col, value in values.items():
                        rr.append(row); cc.append(col); dd.append(value)
                matrix = coo_matrix((dd, (rr, cc)), shape=(len(coeff), len(variants))).tocsc()
                solution = milp(np.asarray(objective), integrality=np.ones(len(variants)),
                                bounds=Bounds(0, 1), constraints=LinearConstraint(matrix, lower, upper),
                                options={'time_limit': max(.01, min(1.0, deadline-time.perf_counter())), 'mip_rel_gap': .01})
                metadata['solverRuns'] += 1
                if solution.x is None:
                    metadata['status'] = 'time-limit' if solution.status == 1 else 'candidate-set-exhausted'
                    break
                selected = [i for i, value in enumerate(solution.x) if value > .5]
                constraint(((i, 1) for i in selected), 0, len(rooms)-1)
                candidate = copy.deepcopy(draft)
                by_id = {r['id']: r for r in candidate['rooms']}
                atom_by_floor = {f['id']: _atoms(f, draft['grid']['rows'], draft['grid']['cols']) for f in draft['floors']}
                for i in selected:
                    rid, cells = variants[i]
                    by_id[rid]['regions'] = _refs(cells, atom_by_floor[rooms[rid]['floorId']])
                metadata['checked'] += 1
                try:
                    compiler_project = {k: v for k, v in project.items() if k != 'designJourney'}
                    checked = proposal(compiler_project, candidate, scope)
                except DesignError:
                    continue
                if not checked['valid']:
                    continue
                changed = _changes(draft, candidate)
                # Real grid ownership differs; numerical jitter cannot create a
                # purportedly different alternative.
                signature = sha([(r['id'], r['regions']) for r in candidate['rooms']])
                if signature in seen_signatures or not changed:
                    continue
                seen_signatures.add(signature)
                cost = round(sum(objective[i] for i in selected), 3)
                result['alternatives'].append({**checked, 'id': 'repair-'+signature[:16],
                    'candidate': candidate, 'adjustments': changed, 'score': cost,
                    'label': f'Option {len(result["alternatives"])+1}', 'requiresExplicitApply': True,
                    'message': 'Review the highlighted ownership changes on every floor before applying.',
                    'validation': 'shared-compiler-and-coordinated-floor-checks'})
                if len(result['alternatives']) == 3:
                    metadata['status'] = 'alternatives-found'
                    break
            metadata.setdefault('status', 'time-limit' if time.perf_counter() >= deadline else 'candidate-limit')
    result['alternatives'].sort(key=lambda item: (item['score'], item['id']))
    for i, alternative in enumerate(result['alternatives']):
        alternative['label'] = f'Option {i+1}'
    metadata['seconds'] = round(time.perf_counter()-started, 4)
    result['message'] = ('Review a validated alternative; your saved map is unchanged.' if result['alternatives'] else
                         'No validated alternative was found in this bounded local search. This is not proof that your home is impossible; keep the draft and review the next specific change.')
    with _CACHE_LOCK:
        _CACHE[key] = copy.deepcopy(result)
        while len(_CACHE) > 24:
            _CACHE.popitem(last=False)
    return result


def guided_question(draft, result):
    """One coupled decision at a time; the remaining issues stay inspectable."""
    if result.get('valid'):
        return None
    from .journey_diagnostics import enrich_issues, first_issue, contextualize_question
    context = {'compass': {**draft, 'floors': draft['floors'][:result.get('scope')]},
               'brief': result.get('values', {})}
    problems = enrich_issues(result.get('issues', []), context, result.get('sizes', []))
    problem = first_issue(problems)
    code = problem['code']
    by_id = {r['id']: r for r in draft['rooms']}
    rid = problem.get('roomId') or problem.get('id')
    affected_ids = [rid] if rid in by_id else [r['id'] for r in draft['rooms'] if
        (r['kind'] == 'stair' if 'STAIR' in code else r['floorId'] == problem.get('floorId'))]
    affected = [{'roomId': ident, 'floorId': by_id[ident]['floorId'], 'regions': by_id[ident]['regions']} for ident in affected_ids]
    if not affected and problem.get('floorId'):
        affected = [{'floorId': problem['floorId'], 'regions': []}]
    if not affected and 'STAIR' in code:
        affected = [{'floorId': floor['id'], 'regions': []} for floor in draft['floors'][:result.get('scope')]]
    alternatives = result.get('alternatives', [])
    if alternatives:
        title = ('May I align these stairs and adjust their adjoining rooms?' if 'STAIR' in code else
                 'May I adjust these room boundaries to make the home work?')
        choices = [{'id': item['id'], 'label': f'Preview option {i+1}', 'action': 'preview-alternative',
                    'alternativeId': item['id'], 'recommended': i == 0,
                    'illustration': [{'floorId': c['floorId'], 'roomId': c['roomId'], 'before': c['before'], 'after': c['after']} for c in item['adjustments']]}
                   for i, item in enumerate(alternatives[:2])]
        choices.append({'id': 'edit-map', 'label': 'Keep my map and edit', 'action': 'edit', 'recommended': False})
    elif code == 'EMPTY_FLOOR':
        title = 'Would you like to finish every requested floor or review a smaller scope?'
        choices = [{'id': 'finish-floors', 'label': 'Finish the requested floors', 'action': 'edit', 'recommended': True},
                   {'id': 'choose-scope', 'label': 'Choose a smaller preview scope', 'action': 'choose-scope', 'recommended': False}]
    elif code in ('UNPLACED', 'REQUIRED_ROOM_UNPLACED'):
        title = f'Where should {problem.get("name", "this required room")} go on {problem.get("floorName", "this floor")}?'
        choices = [{'id': 'place-room', 'label': 'Place this required room', 'action': 'edit', 'recommended': True}]
    elif code in ('ENVELOPE', 'ENVELOPE_TOO_SMALL', 'FIELD_RANGE'):
        title = 'Check the plot dimensions and setbacks first'
        choices = [{'id': 'review-plot', 'label': 'Review plot dimensions and setbacks', 'action': 'review-plot', 'recommended': True}]
    elif 'STAIR' in code:
        title = 'May I reserve one aligned stair area on the requested floors?'
        choices = [{'id': 'align-stairs', 'label': 'Edit aligned stairs and landings', 'action': 'edit-stairs', 'recommended': True},
                   {'id': 'keep-stairs', 'label': 'Keep these positions and revise rooms', 'action': 'edit', 'recommended': False}]
    elif code in ('NO_EXTERNAL_WINDOW', 'LOW_DAYLIGHT', 'BATH_VENTILATION'):
        title = 'How should this room reach outside light and ventilation?'
        choices = [{'id': 'outside-wall', 'label': 'Move beside an outside wall', 'action': 'edit', 'recommended': True},
                   {'id': 'lightwell', 'label': 'Review an open-sky lightwell', 'action': 'edit', 'recommended': False}]
    elif code == 'SIZE_LOCK':
        title = 'This map does not match a pinned dimension. Which should stay fixed?'
        choices = [{'id': 'keep-dimension', 'label': 'Keep the exact dimension; edit regions', 'action': 'edit', 'recommended': True},
                   {'id': 'review-pin', 'label': 'Review the dimension pin', 'action': 'review-pin', 'recommended': False}]
    else:
        name = by_id.get(rid, {}).get('name', 'this area')
        title = f'How would you like to resolve {name} first?'
        choices = [{'id': 'edit-area', 'label': 'Edit the highlighted area', 'action': 'edit', 'recommended': True},
                   {'id': 'review-plot', 'label': 'Review plot dimensions and setbacks', 'action': 'review-plot', 'recommended': False}]
    question = {'id': 'question-'+sha({'code': code, 'affected': affected, 'sourceHash': result.get('sourceHash')})[:16],
            'code': code, 'title': title, 'prompt': title, 'explanation': problem.get('message', ''),
            'affected': affected, 'choices': choices, 'recommended': choices[0]['id'],
            'remainingIssueCount': max(0, len(problems)-1), 'draftPreserved': True}
    return contextualize_question(question, problems, context, result.get('sizes', []))
