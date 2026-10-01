"""Stair-local coordinates shared by plan validation, scene and exports.

x/y are the world bounding-box minimum; width/depth describe the unrotated
core. A 90-degree turn sends the first flight toward decreasing world x.
"""
from shapely.affinity import affine_transform
from shapely.geometry import box


def point(st, p, inverse=False, scale=1):
    x,y,d=(st[k]*scale for k in ('x','y','depth'))
    a,b=p
    if st.get('rotation',0)!=90:return [a,b]
    return [x+b-y,y+x+d-a] if inverse else [x+d-(b-y),y+(a-x)]


def shape(st,p):
    if st.get('rotation',0)!=90:return p
    x,y,d=(st[k] for k in ('x','y','depth'))
    return affine_transform(p,[0,-1,1,0,x+d+y,y-x])


def footprint(st):
    return shape(st,box(st['x'],st['y'],st['x']+st['width'],st['y']+st['depth']))


def well(st):
    return shape(st,box(st['x'],st['y']+st['landing_mm'],st['x']+st['width'],st['y']+st['depth']))
