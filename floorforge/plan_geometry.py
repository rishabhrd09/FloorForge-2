"""The shared slab/roof contract. Every geometry consumer uses these same regions."""
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from shapely import get_parts


def regions(geometry):
    return [{'polygon':[[round(x,3),round(y,3)] for x,y in list(p.exterior.coords)[:-1]],
             'holes':[[[round(x,3),round(y,3)] for x,y in list(r.coords)[:-1]] for r in p.interiors]}
            for p in sorted(get_parts(geometry),key=lambda p:(p.bounds,p.area)) if p.geom_type=='Polygon' and p.area>1]


def geometry(items):
    return unary_union([Polygon(p['polygon'],p.get('holes',[])) for p in items])


def plate(b,floor):
    if b.get('rooftop') and floor==b['storeys']:return geometry(b['rooftop']['slab'])
    if 'floor_plates' in b:
        return geometry(next(p['regions'] for p in b['floor_plates'] if p['floor']==floor))
    p=Polygon(b['footprint'])
    for st in b['stairs']:
        if st['floor']==floor and floor:
            from .stair_geometry import well
            p=p.difference(well(st))
    return p


def roof(b,floor):
    if b.get('rooftop') and floor==b['storeys']-1:return geometry(b['rooftop']['slab'])
    if 'roofs' in b:return geometry(next(p['regions'] for p in b['roofs'] if p['floor']==floor))
    if floor!=b['storeys']-1:return Polygon()
    p=Polygon(b['footprint'])
    for s in b['spaces']:
        if s['floor']==floor and s['kind']=='terrace':p=p.difference(Polygon(s['polygon']))
    return p


def floor_outline(b,floor):
    if b.get('rooftop') and floor==b['storeys']:return geometry(b['rooftop']['outline'])
    if 'floor_plates' in b:return geometry(next(p['outline'] for p in b['floor_plates'] if p['floor']==floor))
    return Polygon(b['footprint'])
