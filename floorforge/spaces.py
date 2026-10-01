"""Shared, serializable space semantics for intent, the editor and the compiler."""
from __future__ import annotations

def space(label, color, *, enclosed=True, roofed=True, floor=True, wet=False, circulation=False, minimum=(0, 0)):
    return dict(label=label, color=color, enclosed=enclosed, roofed=roofed, floor=floor,
                wet=wet, circulation=circulation, minimum_area_m2=minimum[0], minimum_width_mm=minimum[1])

SPACE_REGISTRY = {
    'drawing-room': space('Drawing room · guests', '#d9c8b3', minimum=(7.5,2400)),
    'living': space('Living', '#cbd7bd', minimum=(9.5,2400)),
    'dining': space('Dining', '#dcd6b9'),
    'bedroom': space('Bedroom', '#cec4b0', minimum=(7.5,2400)),
    'care-room': space('Home care room', '#c6d8d5', minimum=(16,3500)),
    'kitchen': space('Kitchen', '#bacdbd', wet=True, minimum=(5,1800)),
    'powder-room': space('Toilet / washbasin', '#b6cacc', wet=True, minimum=(1.8,1200)),
    'bathroom': space('Bathroom', '#b6cacc', wet=True, minimum=(2.8,1200)),
    'utility': space('Utility', '#cad2c7', wet=True, minimum=(1.8,1000)),
    'drying-room': space('Drying room', '#a9caca', wet=True, minimum=(1.8,1000)),
    'drying-yard': space('Drying yard', '#c6dccb', enclosed=False, roofed=False, wet=True),
    'terrace': space('Open terrace', '#d8dfbb', enclosed=False, roofed=False),
    'veranda': space('Veranda', '#dbd4b9', enclosed=False, circulation=True),
    'outer-lobby': space('Outer lobby', '#e0d9bb', enclosed=False, circulation=True),
    'balcony': space('Balcony', '#d4dfc5', enclosed=False, roofed=False),
    'courtyard': space('Courtyard', '#b9d5b4', enclosed=False, roofed=False),
    'foyer': space('Foyer', '#e5ddcc', circulation=True),
    'inner-lobby': space('Inner lobby', '#e6e5d6', circulation=True),
    'hall': space('Hall', '#e6e5d6', circulation=True, minimum=(0,1000)),
    'family': space('Family lounge', '#d3d9bd', minimum=(9.5,2400)),
    'study': space('Study', '#dbc8b5', minimum=(7.5,2100)),
    'pooja': space('Pooja', '#e6cfa9', minimum=(1,850)),
    'store': space('Store', '#d3d0c6', minimum=(1,900)),
    'dress': space('Dressing', '#dcd2c2', minimum=(2,1200)),
    'stair': space('Staircase', '#bfc7d3', circulation=True),
    'stair-landing': space('Stair landing', '#cbd2dc', circulation=True, minimum=(1,1000)),
    'lift-shaft': space('Lift / shaft', '#b7bac5', floor=False),
    'void': space('Double-height void', '#edf0ef', enclosed=False, roofed=True, floor=False),
}
OUTDOOR = {k for k,v in SPACE_REGISTRY.items() if not v['enclosed'] and v['floor']}
OPEN_SKY = {k for k,v in SPACE_REGISTRY.items() if not v['roofed']}
NON_WALKABLE = {k for k,v in SPACE_REGISTRY.items() if not v['floor']}

def guide_labels():
    return [k for k in SPACE_REGISTRY if k!='bedroom'] + [f'bedroom-{n}' for n in range(1,9)] + [f'bathroom-{n}' for n in range(1,9)] + ['master-bedroom']

# These are the roles the bounded automatic planner actually knows how to construct.
GUIDE_AUTOMATIC_KINDS = {'drawing-room','living','dining','bedroom','kitchen','bathroom','utility','hall','family','study','pooja','store','dress','stair','terrace','veranda'}
def guide_kind(label):
    return 'bedroom' if label=='master-bedroom' or label.startswith('bedroom-') else 'bathroom' if label.startswith('bathroom-') else label
