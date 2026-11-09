"""Living-gallery openings and roof glazing, in the same millimetre grid as the stairs."""
from math import atan2, hypot
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from .model import DesignError
from .plan_geometry import geometry, regions

FT = 304.8


def plan_box(west,north,east,south):
    return box((40-south)*FT,(50-east)*FT,(40-north)*FT,(50-west)*FT)


def cut_lightwell(b, spaces):
    # The northwest return leaves a passage from the bedroom gallery to the study.
    lower=unary_union([plan_box(9.95,15.2,16.5,20.4),
                       plan_box(16.45,17.25,19.55,20.4),
                       plan_box(19.45,17.65,32.5,19.50),
                       plan_box(25.2,17.65,32.5,29.5)])
    revised=b['planning'].get('rectangularLanding',False)
    if revised:
        lower=plan_box(26.5,17.4,33.75,27.4)
    upper=plan_box(22.35,15.20,29.6,20.0)
    glass=plan_box(23.1,16.0,29.5,19.75)
    if not Polygon(spaces['living']['clear']).covers(lower):
        raise DesignError('TIRUMALA_VOID_FIT','The overlook must remain above the open living hall.')
    for f,host,cut in [(1,'gallery',lower),(2,'stair-lobby',upper)]:
        plate=b['floor_plates'][f]
        if not Polygon(spaces[host]['clear']).covers(cut) or not geometry(plate['regions']).covers(cut):
            raise DesignError('TIRUMALA_VOID_FIT','Keep daylight openings in the gallery and clear of stair flights.')
        plate['regions']=regions(geometry(plate['regions']).difference(cut))
        plate['openings'].append(dict(id=f'living-lightwell-{f}',regions=regions(cut)))
        spaces[host]['area_m2']=round(geometry(plate['regions']).intersection(Polygon(spaces[host]['clear'])).area/1e6,6)
        ceiling=b['roofs'][f-1]
        ceiling['ceiling']=regions(geometry(ceiling['ceiling']).difference(cut))
        if f==1 and revised:
            from .tirumala_6_lobby import opaque_guards
            opaque_guards(b,cut)
            continue
        for j,(a,c) in enumerate(zip(cut.exterior.coords,list(cut.exterior.coords)[1:])):
            if f==2 and a[0]==c[0]==cut.bounds[2]:continue  # north window wall
            if f==2 and revised:
                from .tirumala_6_lobby import opaque_guard
                b['guards'].append(opaque_guard(f'overlook-{f}-{j}',LineString([a,c]),f,host))
                continue
            b['guards'].append(dict(id=f'overlook-{f}-{j}',owner=host,floor=f,points=[a,c],height=1100))
    roof=b['roofs'][2]
    for key in ('regions','ceiling'):
        roof[key]=regions(geometry(roof[key]).difference(glass))
    roof['rooflight']=regions(glass)
    if revised:
        from .tirumala_6_lobby import suite_northlight
        suite_northlight(b,spaces)


def finish_lightwell(kit,b,H):
    import trimesh
    p=geometry(b['roofs'][2]['rooflight'])
    x,y,X,Y=[c/1000 for c in p.bounds]
    # Sloped glass and intermediate glazing bar on the raised roof kerb.
    pitch=.05
    for name,low,high in [('pane',.254,.276),('bar',.276,.311)]:
        thick=high-low
        depth=Y-y+.13
        kit.rb(((x+X)/2,(y+Y)/2,3*H+(low+high)/2+pitch*depth/2),
                    ((X-x+.13) if name=='pane' else .04,depth*hypot(1,pitch),thick),
                    'glass' if name=='pane' else 'frame',2,'glass' if name=='pane' else 'roof',r=.002)
        node=kit.nodes[-1]
        node['id']='living-rooflight-'+name
        node['rotation'][0]=atan2(pitch,1)
    for i,(y0,y1) in enumerate([(y-.065,y),(Y,Y+.065)]):
        kit.rect((x-.065,y0,3*H+.20,X+.065,y1,3*H+.256+(y0-y+.065)*pitch),'frame',2,'roof',f'rooflight-kerb-{i}')
    for i,x0 in enumerate([x-.065,X]):
        corners=[(xx,yy,zz) for xx in (x0,x0+.065) for yy in (y-.065,Y+.065)
                 for zz in (3*H+.20,3*H+.255+pitch*(yy-y+.065))]
        kit.node(kit.asset(trimesh.convex.convex_hull(corners)),'frame',floor=2,role='roof',name=f'rooflight-side-{i}')



def stair_soffits(kit,steps,f):
    """Line the underside of each straight run without altering its walking surface."""
    import trimesh
    for prefix,axis in [('west-flight',1),('north-flight',0),('arrival-connector',0)]:
        flight=[s for s in steps if prefix in s['id']]
        first,last=flight[0],flight[-1]
        bounds=[v/1000 for v in first['bounds']]
        end=last['bounds'][axis+2]/1000
        rise=(last['top']-first['top'])/1000
        run=(last['bounds'][axis]-first['bounds'][axis])/1000
        slope=rise/run
        vertices=[]
        for u in (bounds[axis],end):
            z=first['top']/1000-.19+(u-bounds[axis])*slope
            for v in (bounds[1-axis],bounds[3-axis]):
                for h in (z-.095,z+.012):
                    vertices.append((u,v,h) if axis==0 else (v,u,h))
        mesh=trimesh.convex.convex_hull(vertices)
        kit.node(kit.asset(mesh),'t5-ivory-render',floor=f,role='stair',name=f'stair-soffit-{f}-{prefix}')
