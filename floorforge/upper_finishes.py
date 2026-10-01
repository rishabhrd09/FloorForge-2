"""Coordinated upper decks and a residential metal-and-timber balustrade."""
import math
from shapely.geometry import LineString


def white_timber_guard(k, materials, edge, z, floor, name, owner):
    materials['guard-ivory']={'color':'#e6e4db','roughness':.48,'metalness':.3}
    # A continuous rectangular timber cap mitres neatly through every corner.
    k.poly_mesh(edge.buffer(.038,cap_style=2,join_style=2),z+1.065,z+1.12,
                'oak',floor,'railing',name+'-timber-cap',owner)
    k.poly_mesh(edge.buffer(.017,cap_style=2,join_style=2),z+.075,z+.105,
                'guard-ivory',floor,'railing',name+'-bottom-rail',owner)
    coords=list(edge.coords)
    for j,(a,b) in enumerate(zip(coords,coords[1:])):
        run=LineString([a,b]);count=max(1,math.ceil(run.length/.115))
        for i in range(count+1):
            if j and not i:continue
            q=run.interpolate(i/count,normalized=True)
            # 25 mm vertical strips, with end posts and concealed base plates.
            post=i in (0,count);w=.04 if post else .025
            k.rect((q.x-w/2,q.y-w/2,z+.09,q.x+w/2,q.y+w/2,z+1.065),
                   'guard-ivory',floor,'railing',name+f'-upright-{j}-{i}',owner)
            if post:
                k.rect((q.x-.045,q.y-.045,z+.014,q.x+.045,q.y+.045,z+.026),
                       'guard-ivory',floor,'railing',name+f'-base-{j}-{i}',owner)


def sandstone_deck(k, materials, polygon, z, floor, owner):
    # A shared world-aligned tile grid keeps every return and threshold coherent.
    materials['upper-sandstone']={'color':'#c9b18d','alt':'#d9c5a5',
        'kind':'paver','texture':'paver','tile_m':[1.8,1.2],
        'params':[2,2,.003,0],'roughness':.83,'normal':.7,'clearcoat':0}
    materials['upper-stone-border']={'color':'#bda27d','roughness':.83,'kind':'stone',
        'texture':'stone','tile_m':1.2}
    k.poly_mesh(polygon,z+.012,z+.019,'upper-sandstone',floor,'finish',owner+'/stone-deck',owner)
    border=polygon.difference(polygon.buffer(-.10,join_style=2))
    k.poly_mesh(border,z+.019,z+.021,'upper-stone-border',floor,'finish',owner+'/stone-border',owner)


def privacy_wall_finish(k, wall, height):
    f=wall['floor'];z=f*height;top=z+wall['height']/1000
    a,b=([v/1000 for v in wall[key]] for key in ('a','b'))
    edge=LineString([a,b]);half=wall['thickness']/2000;owner=wall['id']
    k.poly_mesh(edge.buffer(half+.018,cap_style=3),top,top+.045,'oak',f,'wall-panel',owner+'/cap',owner)
    dx=(b[0]-a[0])/edge.length;dy=(b[1]-a[1])/edge.length
    count=max(1,math.floor(edge.length/.14))
    for i in range(1,count):
        q=edge.interpolate(i/count,normalized=True)
        for side in (-1,1):
            x=q.x-dy*side*(half+.012);y=q.y+dx*side*(half+.012)
            segment=LineString([(x-dx*.018,y-dy*.018),(x+dx*.018,y+dy*.018)])
            k.poly_mesh(segment.buffer(.012,cap_style=2),z+.18,top-.12,'oak',f,'wall-panel',owner+f'/batten-{i}-{side}',owner)


def glass_deck_canopy(k, materials, room, height):
    """Concept glass roof with a consistent fall, frame, drainage and support lines.

    Member sizes describe the visual model, not a structural specification.
    Ground columns align with canopy posts and have independent pier bases.
    """
    import numpy as np
    from shapely.geometry import Polygon, box
    from .scene_kit import extrude
    p=Polygon(np.array(room['clear'])/1000).buffer(-.035,join_style=2)
    x0,y0,x1,y1=p.bounds;f=room['floor'];z=f*height;owner=room['id']
    # All panels share a 1:40 fall towards the outer edge and its gutter.
    # The common origin aligns the adjoining front and studio-return roofs.
    origin=x0
    roof_z=lambda x:z+2.98-.025*(x-origin)
    materials['canopy-glass']={**materials['glass'],'color':'#c8e1e5','alpha':.24,'roughness':.08,'roughness_override':.08}
    materials['canopy-metal']={'color':'#354249','roughness':.42,'metalness':.65}
    def slope(poly,low,high,mat,name):
        if poly.is_empty or poly.area<1e-8:return
        mesh=extrude(poly,low,high)
        mesh.vertices[:,2]+=z+2.98-.025*(mesh.vertices[:,0]-origin)
        k.node(k.asset(mesh),mat,floor=f,role='canopy',name=owner+'/'+name,owner=owner)
    # Small separate panes, with visible glazing bars and a continuous perimeter beam.
    nx=max(1,math.ceil((x1-x0)/1.1));ny=max(1,math.ceil((y1-y0)/1.25))
    xs=np.linspace(x0,x1,nx+1);ys=np.linspace(y0,y1,ny+1)
    for i in range(nx):
        for j in range(ny):
            pane=p.intersection(box(xs[i]+.024,ys[j]+.024,xs[i+1]-.024,ys[j+1]-.024))
            slope(pane,.012,.032,'canopy-glass',f'glass-{i}-{j}')
    slope(p.boundary.buffer(.042,join_style=2).intersection(p),-.14,.012,'canopy-metal','perimeter-frame')
    for i,x in enumerate(xs[1:-1]):
        slope(p.intersection(box(x-.025,y0,x+.025,y1)),-.075,.016,'canopy-metal',f'rafter-{i}')
    for j,y in enumerate(ys[1:-1]):
        slope(p.intersection(box(x0,y-.022,x1,y+.022)),-.065,.012,'canopy-metal',f'crossbar-{j}')
    for i,(xx,yy) in enumerate(room.get('canopyPosts',[])):
        x,y=xx/1000,yy/1000;foot=box(x-.06,y-.06,x+.06,y+.06)
        k.poly_mesh(foot,z+.025,roof_z(x)-.01,'canopy-metal',f,'column',owner+f'/canopy-post-{i}',owner)
        k.rect((x-.095,y-.095,z+.022,x+.095,y+.095,z+.047),'canopy-metal',f,'column',owner+f'/post-base-{i}',owner)
        k.obstacle(foot,f,owner+f'/canopy-post-{i}')
        # Short cantilever brackets tie the roof edge back to each support.
        slope(p.intersection(box(x-.055,y-.22,x+.055,y+.22)),-.18,-.13,'canopy-metal',f'post-head-{i}')
    for i,(xx,yy) in enumerate(room.get('supportColumns',[])):
        x,y=xx/1000,yy/1000;foot=box(x-.11,y-.11,x+.11,y+.11)
        k.poly_mesh(foot,-.30,z-.16,'wall',0,'column',owner+f'/ground-column-{i}',owner)
        k.rect((x-.16,y-.16,-.32,x+.16,y+.16,.04),'stone',0,'column',owner+f'/pier-{i}',owner)
        k.obstacle(box(x-.16,y-.16,x+.16,y+.16),0,owner+f'/ground-column-{i}')
    if room.get('supportColumns'):
        # Continuous edge beam lands on all three outer columns; wall-side bearing
        # remains on the existing care-room wall line.
        x=room['supportColumns'][0][0]/1000
        k.rect((x-.11,y0,z-.32,x+.11,y1,z-.16),'wall',0,'beam',owner+'/balcony-support-beam',owner)
    # Outer gutter is an open U section, with a downpipe beside the end post.
    edge=p.intersection(box(x1-.11,y0,x1,y1))
    slope(edge,-.06,-.042,'canopy-metal','gutter-bottom')
    for a,b in ((x1-.11,x1-.098),(x1-.012,x1)):
        slope(p.intersection(box(a,y0,b,y1)),-.042,.045,'canopy-metal','gutter-lip-'+str(a))
    if room.get('canopyPosts'):
        xx,yy=max(room['canopyPosts'],key=lambda q:(q[0],q[1]));x,y=xx/1000-(.17 if room.get('supportColumns') else .09),yy/1000
        # Short outlet links the gutter to the pipe, clear of the wider ground pier.
        k.rect((x-.025,y-.025,roof_z(x1)-.08,x1-.035,y+.025,roof_z(x1)-.03),'canopy-metal',f,'drain',owner+'/gutter-outlet',owner)
        bottom=.06 if room.get('supportColumns') else z+.045
        k.cylinder((x,y,(bottom+roof_z(x)-.04)/2),.028,roof_z(x)-.04-bottom,'canopy-metal',f,'drain')
        k.rect((x-.08,y-.08,bottom-.01,x+.08,y+.08,bottom+.006),'steel',0 if room.get('supportColumns') else f,'drain',owner+'/drain-outlet',owner)
