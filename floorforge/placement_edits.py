"""Explicit placement overrides. Empty overrides leave the authored scene untouched."""
import copy
import math
from shapely.geometry import Polygon, LineString, box
from shapely import affinity
from .model import DesignError, sha


def normalize_edits(payload):
    result = {}
    for key in ('roomEdits', 'furnitureLayout'):
        edits = payload.get(key, [])
        if not isinstance(edits, list) or len(edits) > 500:
            raise DesignError('PLACEMENT_SCHEMA', 'Placement edits must be a list of at most 500 objects.')
        seen = set()
        for e in edits:
            fields = {'id', 'anchorHash', 'polygon'} if key == 'roomEdits' else {'id', 'anchorHash', 'dx', 'dy', 'angle'}
            if not isinstance(e, dict) or set(e) != fields or not isinstance(e['id'], str) or not isinstance(e['anchorHash'], str) or e['id'] in seen:
                raise DesignError('PLACEMENT_SCHEMA', 'Each placement needs a unique object ID and its original anchor.')
            seen.add(e['id'])
            if key == 'roomEdits':
                pts = e['polygon']
                if not isinstance(pts, list) or not 4 <= len(pts) <= 64 or any(not isinstance(p, list) or len(p) != 2 for p in pts):
                    raise DesignError('PLACEMENT_SCHEMA', 'A room needs an orthogonal polygon.')
                nums = [n for p in pts for n in p]
            else:
                nums = [e['dx'], e['dy'], e['angle']]
            if any(type(x) not in (int, float) or not math.isfinite(x) or abs(x) > 100000 for x in nums):
                raise DesignError('PLACEMENT_SCHEMA', 'Placement coordinates must be finite numbers.')
        if edits:
            result[key] = copy.deepcopy(sorted(edits, key=lambda e: e['id']))
    if result.get('roomEdits') and payload.get('customPlan'):
        raise DesignError('PLACEMENT_MODE', 'Edit Custom Plan rooms in the dimensioned editor. Automatic room edits cannot also be applied.')
    return result


def room_anchors(spaces):
    return [{'id': s.id, 'name': s.name, 'kind': s.kind, 'floor': s.floor,
             'polygon': copy.deepcopy(s.polygon), 'anchorHash': sha([s.id, s.kind, s.floor, s.polygon])} for s in spaces]


def apply_room_edits(spaces, stairs, footprint, access, edits, anchors):
    if not edits:
        return
    base = {s['id']: s for s in anchors}
    rooms = {s.id: s for s in spaces}
    for e in edits:
        if e['id'] not in base or base[e['id']]['anchorHash'] != e['anchorHash']:
            raise DesignError('ROOM_ANCHOR', 'The underlying plan changed. Reset room edits before applying a different layout.', {'id': e['id']})
        p = Polygon(e['polygon'])
        if not p.is_valid or p.area < 1 or any(abs(a[0]-c[0]) > .01 and abs(a[1]-c[1]) > .01 for a, c in zip(e['polygon'], e['polygon'][1:] + e['polygon'][:1])):
            raise DesignError('ROOM_SHAPE', 'Room boundaries must remain valid and orthogonal.', {'id': e['id']})
        if not footprint.buffer(.01).covers(p):
            raise DesignError('ROOM_OUTSIDE', rooms[e['id']].name + ' extends outside the building footprint.', {'id': e['id']})
        rooms[e['id']].polygon = copy.deepcopy(e['polygon'])
    # All linked cores move together. The flight retains its exact geometry and orientation.
    cores = [s for s in spaces if s.kind == 'stair']
    for s in cores:
        old, new = Polygon(base[s.id]['polygon']), Polygon(s.polygon)
        dx, dy = new.centroid.x-old.centroid.x, new.centroid.y-old.centroid.y
        if affinity.translate(old, dx, dy).symmetric_difference(new).area > 1:
            raise DesignError('STAIR_SHAPE', 'Move the staircase without resizing or rotating its core.', {'id': s.id})
        for st in stairs:
            if st['floor'] == s.floor:
                st['x'] += dx; st['y'] += dy
                from .stair_geometry import footprint as stair_footprint
                if not new.buffer(.01).covers(stair_footprint(st)):
                    raise DesignError('STAIR_FIT', 'The staircase no longer fits its room.', {'id': s.id})
    if cores and any(Polygon(s.polygon).symmetric_difference(Polygon(cores[0].polygon)).area > 1 for s in cores[1:]):
        raise DesignError('STAIR_ALIGNMENT', 'Move the linked staircase on every occupied floor together.')
    for i, s in enumerate(spaces):
        for t in spaces[i+1:]:
            if s.floor == t.floor and Polygon(s.polygon).intersection(Polygon(t.polygon)).area > 1:
                raise DesignError('ROOM_OVERLAP', f'{s.name} overlaps {t.name}. Swap their positions or move both rooms.', {'ids': [s.id, t.id]})
    # Existing access relationships survive when still adjacent. Otherwise use the actual new neighbour.
    for ident, spec in (access or {}).items():
        if ident not in rooms or not isinstance(spec, dict):
            continue
        s = rooms[ident]
        nearby = [t for t in spaces if t.id != ident and t.floor == s.floor and Polygon(s.polygon).boundary.intersection(Polygon(t.polygon).boundary).length >= 950]
        if not any(t.id == spec.get('from') for t in nearby):
            candidates = [t for t in nearby if t.kind in ('hall', 'living', 'dining', 'family') or (s.kind in ('bathroom', 'dress') and t.kind == 'bedroom')]
            if candidates:
                spec['from'] = min(candidates, key=lambda t: (t.kind != 'hall', t.id)).id
        if ident in {e['id'] for e in edits} or spec.get('from') in {e['id'] for e in edits}:
            spec['near'] = None


def transformed_polygon(points, e, pivot):
    p = affinity.rotate(Polygon(points), e.get('angle', 0), origin=pivot)
    return affinity.translate(p, e.get('dx', 0), e.get('dy', 0))


def apply_furniture_edits(scene, building):
    """Transform complete semantic groups after furnishing; never rerun or replace the furniture recipes."""
    edits = building.get('furnitureLayout', [])
    items = {i['id']: i for i in scene['editables']}
    if len(items) != len(scene['editables']):
        raise DesignError('FURNITURE_IDS', 'Furniture groups must have unique IDs.')
    footprints = {i['id']: Polygon(i['footprint']) for i in scene['furniture']}
    footprints.update({i['id']: Polygon(i['footprint']) for i in items.values()})
    for e in edits:
        item = items.get(e['id'])
        if not item or item['anchorHash'] != e['anchorHash']:
            raise DesignError('FURNITURE_ANCHOR', 'This furniture belongs to a different room layout or theme. Reset placements before regenerating.', {'id': e['id']})
        footprints[e['id']] = transformed_polygon(item['footprint'], e, item['pivot'])
    rooms = {s['id']: s for s in building['spaces']}
    hosts = {w['id']: w for w in building['walls']}
    for e in edits:
        item, p = items[e['id']], footprints[e['id']]
        room = rooms[item['roomId']]
        allowed = Polygon([[x/1000, y/1000] for x,y in room['clear']])
        if item.get('placementArea'):
            allowed = Polygon(item['placementArea'])
        placement_rooms = set(item.get('placementRoomIds',[room['id']]))
        if not allowed.buffer(.006).covers(p):
            raise DesignError('FURNITURE_OUTSIDE', f'{item["label"]} must fit inside {room["name"]}.', {'id': e['id']})
        for other in scene['furniture']:
            if other['id'] == e['id'] or other['floor'] != item['floor']:
                continue
            if p.intersection(footprints[other['id']]).area > .002:
                raise DesignError('FURNITURE_OVERLAP', f'{item["label"]} overlaps {other["kind"].replace("-", " ")}.', {'ids': [e['id'], other['id']]})
        for o in building['openings']:
            if o['kind'] == 'window' or not placement_rooms.intersection(o['connects']):
                continue
            if o['kind']=='cased' and set(o['connects'])<=placement_rooms and not o.get('servingCounter'):
                continue
            w = hosts[o['wall_id']]; a, c = w['a'], w['b']; length = math.dist(a,c)
            u = [(c[j]-a[j])/length for j in (0,1)]
            ends = [[(a[j]+u[j]*(o['offset']+d))/1000 for j in (0,1)] for d in (0, o['width'])]
            if p.intersection(LineString(ends).buffer(.65, cap_style=2)).area > .002:
                raise DesignError('FURNITURE_ACCESS', f'{item["label"]} blocks a doorway. Leave the approach clear.', {'id': e['id'], 'openingId': o['id']})
        # Door leaves need their full swing as well as a clear approach.
        from .review import swing_sector
        from shapely.affinity import scale
        clear_mm = {r['id']: Polygon(r['clear']) for r in building['spaces']}
        for o in building['openings']:
            if o.get('swing') not in placement_rooms:
                continue
            sector = swing_sector(o, hosts[o['wall_id']], clear_mm)
            if sector is not None and p.intersection(scale(sector, xfact=.001, yfact=.001, origin=(0,0))).area > .002:
                raise DesignError('FURNITURE_SWING', f'{item["label"]} obstructs the door swing.', {'id': e['id'], 'openingId': o['id']})
        for st in building['stairs']:
            from .stair_geometry import shape as stair_shape
            stair_zone=scale(stair_shape(st,box(st['x']-200,st['y']-700,st['x']+st['width']+200,st['y']+st['depth']+200)),xfact=.001,yfact=.001,origin=(0,0))
            if st['floor'] == item['floor'] and p.intersection(stair_zone).area > .002:
                raise DesignError('FURNITURE_STAIR', 'Keep the stair flight and landing approach clear.', {'id': e['id']})
    nodes = {n['id']: n for n in scene['nodes']}
    for e in edits:
        item = items[e['id']]; px, py = item['pivot']; theta = math.radians(e['angle']); cs, sn = math.cos(theta), math.sin(theta)
        def position(pos):
            x, y = pos[0]-px, pos[1]-py
            return [px+x*cs-y*sn+e['dx'], py+x*sn+y*cs+e['dy'], *pos[2:]]
        for ident in item['nodeIds']:
            n = nodes[ident]; n['position'] = position(n['position']); n['rotation'][2] += theta
        for index in item['lightIndices']:
            scene['lights'][index]['position'] = position(scene['lights'][index]['position'])
        for f in scene['furniture']:
            if f['id'] == e['id']:
                f['footprint'] = [list(q) for q in transformed_polygon(f['footprint'], e, item['pivot']).exterior.coords[:-1]]
        for c in scene['colliders']:
            if c['id'] == e['id']:
                c['polygon'] = [list(q) for q in transformed_polygon(c['polygon'], e, item['pivot']).exterior.coords[:-1]]
        item['placement'] = {key: e[key] for key in ('dx','dy','angle')}
        item['currentFootprint'] = [list(q) for q in footprints[e['id']].exterior.coords[:-1]]
    return scene
