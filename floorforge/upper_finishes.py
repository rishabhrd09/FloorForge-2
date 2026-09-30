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
