"""Concept framing for the full north deck of Tirumala 6, in building mm."""
from shapely.geometry import box

FT = 304.8


def north_deck():
    return box(25*FT, 0, 40*FT, 50*FT)


def frame_members(floor_height):
    """Two rows of aligned posts rise to edge beams and four transverse beams."""
    deck = north_deck()
    south, east, north, west = deck.bounds
    half = 125
    post_x = [south+half, north-half]
    post_y = [0.9*FT, 13*FT, 30.25*FT, 49.5*FT]
    members = []
    for row,x in enumerate(post_x):
        for col,y in enumerate(post_y):
            for floor in (0,1):
                members.append(dict(id=f'north-deck-column-{row}-{col}-{floor}',kind='column',
                                    floor=floor, bounds=[x-half,y-half,x+half,y+half],
                                    base=0, top=floor_height-(480 if floor==1 else 0)))
    def beam(name, bounds):
        members.append(dict(id='north-deck-beam-'+name, kind='beam', floor=1,
                            bounds=bounds, base=floor_height-480, top=floor_height-150))
    for j,x in enumerate(post_x):
        beam(f'edge-{j}', [x-half,east,x+half,west])
    for j,y in enumerate(post_y):
        beam(f'cross-{j}', [south+2*half,y-half,north-2*half,y+half])
    return members
