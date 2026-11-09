"""Rectangular overlook, opaque gallery walls and the suite's north-facing roof light."""
from math import atan, hypot
from shapely.affinity import scale
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from shapely import get_parts
import trimesh

from .model import DesignError
from .plan_geometry import geometry, regions
from .tirumala_6_daylight import plan_box


def opaque_guard(name, edge, floor, owner):
    footprint = edge.buffer(55, cap_style=2, join_style=2)
    return dict(id=name, floor=floor, owner=owner, points=list(edge.coords),
                height=1100, parapet=regions(footprint))


def opaque_guards(b, overlook):
    def guard(name, edge):
        b['guards'].append(opaque_guard(name, edge, 1, 'gallery'))
    for j,(a,c) in enumerate(zip(overlook.exterior.coords,list(overlook.exterior.coords)[1:])):
        guard(f'overlook-1-{j}', LineString([a,c]))

    treads=b['stairs'][0]['flights']
    well=unary_union([box(*t['bounds']) for t in treads])
    # Leave the full width of each flight open where it meets the level landing.
    mouths=[]
    for tread in (treads[0],treads[-1]):
        _,y,X,Y=tread['bounds']
        mouths.append(LineString([(X,y),(X,Y)]))
    edges=well.boundary.difference(unary_union(mouths).buffer(65))
    for j,line in enumerate(get_parts(edges)):
        for i,(a,c) in enumerate(zip(line.coords,list(line.coords)[1:])):
            edge=LineString([a,c])
            if edge.length>120:
                guard(f'stair-well-1-{j}-{i}',edge)


def suite_northlight(b, spaces):
    # The chase is integral to the west TV-room wall, between the media console
    # and the office. Its lower end is above the suite's window seat.
    cut=plan_box(3.22,28.35,8.22,31.15)
    outer=cut.buffer(85,join_style=2)
    for room_id in ('west-suite','leisure-hall'):
        if not Polygon(spaces[room_id]['polygon']).buffer(85).covers(outer):
            raise DesignError('SUITE_LIGHT_FIT','The suite shaft must stack within both rooms.')
    slab=b['floor_plates'][2]
    slab['regions']=regions(geometry(slab['regions']).difference(cut))
    slab['openings'].append(dict(id='suite-daylight-shaft',regions=regions(cut)))
    for f in (1,2):
        roof=b['roofs'][f]
        roof['ceiling']=regions(geometry(roof['ceiling']).difference(cut))
    roof['regions']=regions(geometry(roof['regions']).difference(cut))
    roof['suiteNorthlight']=regions(cut)
    b['planning']['suiteLightShaft']=regions(outer)
    hall=Polygon(spaces['leisure-hall']['clear'])
    spaces['leisure-hall']['area_m2']=round(hall.difference(outer).area/1e6,6)


def finish_lobby(scene,b,k,H):
    rooms={r['id']:r for r in b['spaces']}
    def metres(poly):
        return scale(poly,xfact=.001,yfact=.001,origin=(0,0))

    for n in scene['nodes']:
        if n['role']=='skirting':
            n['material']='t5-honed-coping'
        elif n['role']=='window-surround':
            n['material']='t5-door-teak' if n['material']=='timber' else 't5-soft-charcoal'
        elif n['role']=='sill':
            n['material']='t5-honed-coping'
        elif n['role']=='door' and n['material']=='oak':
            n['material']='t5-door-teak'
    for g in b['guards']:
        if g.get('parapet') and (g['floor']==1 or g['id'].startswith('overlook-2-')):
            cap=metres(geometry(g['parapet'])).buffer(.009,join_style=2)
            top=g['floor']*H+g['height']/1000
            k.poly_mesh(cap,top,top+.035,'t5-honed-coping',g['floor'],'coping',g['id']+'-coping')
    # One continuous stone fascia and recessed shadow line on the east balcony.
    deck=unary_union([metres(Polygon(rooms[key]['polygon'])) for key in ('loggia','east-balcony')])
    facade=deck.boundary.intersection(LineString([(deck.bounds[0]-1,deck.bounds[1]),(deck.bounds[2]+1,deck.bounds[1])]))
    for j,line in enumerate(get_parts(facade)):
        if line.geom_type!='LineString':continue
        face=line.buffer(.022,cap_style=2)
        k.poly_mesh(face,H-.18,H+.005,'t5-honed-coping',1,'fascia','east-fascia-'+str(j))
        k.poly_mesh(face,H-.205,H-.18,'t5-shadow-reveal',1,'fascia','east-reveal-'+str(j))

    cut=metres(geometry(b['roofs'][2]['suiteNorthlight']))
    outer=metres(geometry(b['planning']['suiteLightShaft']))
    z=3*H
    x,y,X,Y=cut.bounds
    pitch=.65
    def head(u):
        return z+.28+(X-u)*pitch
    # Actual lined vertical shaft and raised sloping kerb. Its glass sees north sky.
    ox,oy,oX,oY=outer.bounds
    for j,(a,c,A,C) in enumerate([(ox,oy,x,oY),(X,oy,oX,oY),(x,oy,X,y),(x,Y,X,oY)]):
        vertices=[(u,v,h) for u in (a,A) for v in (c,C) for h in (2*H-.15,head(u))]
        k.node(k.asset(trimesh.convex.convex_hull(vertices)),'t5-ivory-render',floor=2,
               role='wall',name='suite-light-lining-'+str(j))
    k.obstacle(outer,2,'suite-light-shaft')
    length=(oX-ox)*hypot(1,pitch)
    for name,width,zadd,mat in [('pane',oY-oy,.016,'glass'),('glazing-bar',.035,.04,'t5-soft-charcoal')]:
        k.rb(((ox+oX)/2,(oy+oY)/2,head((ox+oX)/2)+zadd),(length,width,.028),mat,2,'glass' if name=='pane' else 'roof',r=.002)
        k.nodes[-1].update(id='suite-northlight-'+name,rotation=[0,atan(pitch),0])
    # Remove the decorative finish from the actual opening as well as cutting the slab.
    scene['nodes'][:]=[n for n in scene['nodes'] if n['id']!='leisure-hall/floor']
    k.poly_mesh(metres(Polygon(rooms['leisure-hall']['clear'])).difference(outer),
               2*H+.002,2*H+.009,'ivory-vitrified',2,'finish','leisure-hall/floor','leisure-hall')
    trim=cut.buffer(.055,join_style=2).difference(cut)
    k.poly_mesh(trim,2*H-.18,2*H-.157,'t5-door-teak',1,'joinery','suite-daylight-reveal')
