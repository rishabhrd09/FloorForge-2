"""A roof access level shared by scene, walking, drawings and IFC; never an extra dwelling storey."""
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from shapely import get_parts
from .model import DesignError
from .plan_geometry import roof, geometry, regions


def with_rooftop_objects(b):
    r = b.get('rooftop')
    if not r:
        return b
    return {**b, **{key: list({obj['id']: obj for obj in b.get(key, []) + r.get(key, [])}.values())
                   for key in ('spaces', 'walls', 'openings', 'guards')}}


def add_roof_access(b):
    if not b['brief'].get('roof_access'):
        return b
    floor = b['storeys']; t = 150; H = b['brief']['floor_height_mm']
    top_stairs = [st for st in b['stairs'] if st['floor'] == floor - 1]
    if not top_stairs:
        raise DesignError('ROOF_STAIR_REQUIRED', 'Roof terrace access needs a linked staircase reaching the top occupied floor. Add a stair core in Custom Plan, or turn off roof access.')
    field = roof(b, floor - 1); shells = []; cores = []; walls = []; openings = []; spaces = []; holes = []
    def coords(p): return regions(p)[0]['polygon']
    for st in top_stairs:
        x, y, width, depth, land = [st[k] for k in ('x', 'y', 'width', 'depth', 'landing_mm')]
        from .stair_geometry import shape as stair_shape, point as stair_point
        clear = stair_shape(st,box(x,y,x+width,y+depth)); shell=clear.buffer(t,join_style=2)
        if not field.buffer(1).covers(shell):
            raise DesignError('ROOF_HEADROOM_FIT', 'The stair headhouse must fit on the covered roof above its core; move or resize the core explicitly.', {'errors': [{'code': 'ROOF_HEADROOM_FIT', 'id': st.get('roomId', st['id']), 'floor': floor - 1, 'message': 'Leave 150 mm around the roof stair for its enclosing walls.'}]})
        if any(shell.intersection(p).area > 1 for p in shells):
            raise DesignError('ROOF_CORE_OVERLAP', 'Roof stair enclosures overlap. Separate the linked stair cores.')
        sid = st['id'] + '-roof-landing'; terrace = 'roof-terrace'
        # Prefer an exit from the front landing onto a real, one-metre-deep patch of terrace.
        doors = [('right', box(x+width+t, y, x+width+t+1000, y+land)),
                 ('left', box(x-t-1000, y, x-t, y+land)),
                 ('front', box(x+width-1000, y-t-1000, x+width, y-t))]
        doors=[(side,stair_shape(st,patch)) for side,patch in doors]
        available = [(side, patch) for side, patch in doors if field.buffer(1).covers(patch)]
        if not available:
            raise DesignError('ROOF_DOOR_ACCESS', 'The roof landing has no clear terrace beside it. Leave a one-metre approach at the front, left or right of the stair landing.', {'errors': [{'code': 'ROOF_DOOR_ACCESS', 'id': st.get('roomId', st['id']), 'floor': floor-1, 'message': 'No supported terrace approach beside the roof stair landing.'}]})
        side, approach = available[0]
        axes = {'front': ([x-t/2,y-t/2],[x+width+t/2,y-t/2]), 'right': ([x+width+t/2,y-t/2],[x+width+t/2,y+depth+t/2]),
                'rear': ([x-t/2,y+depth+t/2],[x+width+t/2,y+depth+t/2]), 'left': ([x-t/2,y-t/2],[x-t/2,y+depth+t/2])}
        for face, (a, z) in axes.items():
            a,z=stair_point(st,a),stair_point(st,z)
            wid = st['id'] + '-roof-wall-' + face
            walls.append({'id': wid, 'floor': floor, 'a': a, 'b': z, 'polygon': coords(LineString([a,z]).buffer(t/2,cap_style=2)),
                          'thickness': t, 'height': 2500, 'rooms': [sid], 'external': True})
            if face == side:
                offset = t/2 + (land-900)/2 if face != 'front' else t/2 + width - 975
                openings.append({'id': st['id']+'-roof-door','wall_id':wid,'floor':floor,'kind':'door','offset':offset,
                                 'width':900,'height':2150,'sill':0,'connects':[sid,terrace],'swing':terrace,'hinge':'end'})
        hole = stair_shape(st,box(x, y+land, x+width, y+depth)); holes.append(hole); shells.append(shell)
        spaces.append({'id':sid,'name':'Roof stair landing','kind':'stair','enclosed':True,'floor':floor,'polygon':coords(clear),'clear':coords(stair_shape(st,box(x,y,x+width,y+land))), 'area_m2':width*land/1e6})
        cores.append({'id':st['id']+'-headhouse','stairId':st['id'],'roomId':sid,'bounds':list(shell.bounds),
                      'clear':coords(clear),'hole':regions(hole),'doorId':st['id']+'-roof-door','approach':coords(approach),'height':2700})
        st['to_floor'] = floor; st['roof_access'] = True
    for core in cores:
        others=unary_union([box(*q['bounds']) for q in cores if q['id']!=core['id']])
        if Polygon(core['approach']).intersection(others).area>1:
            raise DesignError('ROOF_DOOR_ACCESS','Another stair enclosure blocks a rooftop door approach. Move the cores apart.')
    slab = field.difference(unary_union(holes)); outdoor = field.difference(unary_union(shells))
    if outdoor.is_empty or outdoor.geom_type != 'Polygon':
        raise DesignError('ROOF_TERRACE_DISCONNECTED', 'The roof stair enclosure separates the roof into disconnected terraces. Adjust the core or roof outline to keep one accessible terrace.')
    spaces.append({'id':'roof-terrace','name':'Roof terrace','kind':'terrace','enclosed':False,'floor':floor,'polygon':coords(outdoor),'clear':coords(outdoor),'holes':regions(outdoor)[0]['holes'],'area_m2':round(outdoor.area/1e6,3)})
    guards = []
    # Guard every roof boundary, including existing courtyard/void holes; the stair well is inside its headhouse.
    edge = field.boundary.difference(unary_union(shells).buffer(1))
    for i,line in enumerate(get_parts(edge)):
        if line.geom_type in ('LineString','LinearRing') and line.length>1:
            guards.append({'id':f'roof-guard-{i}','owner':'roof-terrace','floor':floor,'points':[list(c) for c in line.coords],'height':1100})
    b['rooftop'] = {'id':'roof-level','floor':floor,'elevation':floor*H,'outline':regions(field),'slab':regions(slab),'terrace':regions(outdoor),
                    'cores':cores,'spaces':spaces,'walls':walls,'openings':openings,'guards':guards,
                    'access':'Linked staircase and landing door; not an additional occupied storey.'}
    if 'roofs' in b:
        record = b['roofs'][-1]
        record['regions'] = regions(slab)
        record['ceiling'] = regions(geometry(record['ceiling']).difference(unary_union(holes)))
    return b
