"""Recover common draw-first omissions without changing an authored neighbour.

Preparation is a proposal, separate from exact Compass conversion. The client
reviews it and saves the candidate before accepting its fresh geometry hash.
"""
from __future__ import annotations

from .compass_input import SPLIT_SCHEMA, normalize, microcells
from .compass_adapter import proposal
from .spaces import SPACE_REGISTRY


def _grow(room, draft, values):
    """Smallest free rectangular extension containing every authored region.

    Use the existing partition atoms, never quarters, and never take a region
    from another room. Locked dimensions, room identity and split axes survive.
    """
    if room.get('target', {}).get('locked') or not room['regions']:
        return None
    rows, cols = draft['grid']['rows'], draft['grid']['cols']
    floor = next(f for f in draft['floors'] if f['id'] == room['floorId'])
    own = microcells(room['regions'], rows, cols)
    occupied = set().union(*(microcells(r['regions'], rows, cols) for r in draft['rooms']
                             if r['floorId'] == room['floorId'] and r['id'] != room['id']))
    miny, maxy = min(y for y, x in own), max(y for y, x in own) + 1
    minx, maxx = min(x for y, x in own), max(x for y, x in own) + 1
    atoms = []
    for row in range(rows):
        for col in range(cols):
            base = f'{row}:{col}'
            halves = 'LR' if base in floor['splits'] else 'FB' if base in floor.get('horizontalSplits', []) else ''
            for ref in ([base + ':' + half for half in halves] if halves else [base]):
                atoms.append((ref, microcells([ref], rows, cols)))
    width = (values['width_mm'] - values['left_mm'] - values['right_mm'] - 150) / (2 * cols)
    depth = (values['depth_mm'] - values['front_mm'] - values['rear_mm'] - 150) / (2 * rows)
    if width <= 0 or depth <= 0:
        return None
    spec = SPACE_REGISTRY[room['kind']]
    allowance = 150 if spec['enclosed'] else 0
    choices = []
    for y0 in range(miny + 1):
        for y1 in range(maxy, 2 * rows + 1):
            for x0 in range(minx + 1):
                for x1 in range(maxx, 2 * cols + 1):
                    w, d = (x1 - x0) * width - allowance, (y1 - y0) * depth - allowance
                    if min(w, d) + .1 < spec['minimum_width_mm'] or w * d / 1e6 + 1e-6 < spec['minimum_area_m2']:
                        continue
                    rectangle = {(y, x) for y in range(y0, y1) for x in range(x0, x1)}
                    if rectangle & occupied or rectangle == own:
                        continue
                    refs = [ref for ref, cells in atoms if cells <= rectangle]
                    if microcells(refs, rows, cols) != rectangle:
                        continue  # Would cut a whole cell or cross the saved split direction.
                    choices.append((len(rectangle - own), abs(w - d), sorted(refs)))
    return min(choices)[2] if choices else None


def prepare(project, compass, scope=None):
    draft = normalize(compass)
    draft['schema'] = SPLIT_SCHEMA
    draft['programme'] = 'drawn'
    changes = []
    # Compile once to resolve all form/text/source precedence through the same
    # intent path used for actual generation; never reinterpret the plot here.
    initial = proposal(project, draft, scope)
    scope = initial['scope']
    included = draft['floors'][:scope]
    placed = {r['floorId'] for r in draft['rooms'] if r['regions']}
    while scope > 1 and included[scope - 1]['id'] not in placed:
        scope -= 1
    if scope != initial['scope']:
        changes.append({'code': 'DRAWN_FLOORS', 'message': f'Generate the {scope} drawn floor(s) now. Unfinished upper floors remain saved.',
                        'before': initial['scope'], 'after': scope})
        initial = proposal(project, draft, scope)
    by_id = {r['id']: r for r in draft['rooms']}
    repaired = set()
    for problem in initial['issues']:
        ident = problem.get('roomId')
        if problem['code'] not in ('ROOM_MINIMUM', 'NARROW_NECK') or ident not in by_id or ident in repaired:
            continue
        repaired.add(ident)
        room = by_id[ident]
        refs = _grow(room, draft, initial['values'])
        if refs is not None:
            changes.append({'code': 'GROW_INTO_EMPTY', 'roomId': ident, 'name': room['name'],
                            'message': f'Enlarge {room["name"]} into unused adjoining space. Keep its room type and existing allocations.',
                            'before': list(room['regions']), 'after': refs})
            room['regions'] = refs
    # Exact conversion still owns openings, access, support and geometry checks.
    result = proposal(project, draft, scope) if changes else initial
    return {**result, 'candidate': draft, 'adjustments': changes}
