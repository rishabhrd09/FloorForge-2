"""Residential furniture for the upper family room. Local +X faces north."""
from math import sin, cos, tau
from shapely.geometry import box


def furnish_lounge(k, room, z, west_media_wall=False):
    # Mount the media wall at the actual finished face in both hall widths.
    east_face = min(y for x,y in room['clear']) / 1000
    media_offset = 0 if west_media_wall else east_face - 9.5088
    west_face = max(y for x,y in room['clear']) / 1000
    def lounge_y(y):
        return west_face - (y - 9.5088) if west_media_wall else y

    def cushion(center, *args, **kwargs):
        x,y,h = center
        k.rb((x,lounge_y(y),h), *args, **kwargs)

    def footprint(x0,y0,x1,y1):
        return box(x0,lounge_y(y0),x1,lounge_y(y1))

    def piece(name, bounds, material, owner, role='furniture'):
        x,y,bottom,X,Y,top=bounds
        if not west_media_wall and owner in ('family-tv','media-console'):
            y += media_offset
            Y += media_offset
        if owner in ('family-tv','media-console','lounge-rug','coffee-table'):
            y,Y = sorted((lounge_y(y),lounge_y(Y)))
        k.rect((x,y,z+bottom,X,Y,z+top),material,2,role,name,owner)

    # The low teak console and three-seat linen sofa follow Tirumala 5's hall.
    cx,cy=(5.15 if west_media_wall else 7.25),13.35
    cushion((cx,cy,z+.24),(2.62,.95,.38),'fabric',2,r=.09,owner='family-sofa')
    cushion((cx,cy+.38,z+.62),(2.62,.19,.62),'linen',2,r=.07,owner='family-sofa')
    for offset in (-1.23,1.23):
        cushion((cx+offset,cy,z+.47),(.18,.91,.45),'fabric',2,r=.06,owner='family-sofa')
    for offset in (-.765,0,.765):
        cushion((cx+offset,cy-.07,z+.425),(.75,.71,.15),'linen',2,r=.06,owner='family-sofa')
        cushion((cx+offset,cy+.25,z+.68),(.74,.16,.47),'fabric',2,r=.055,owner='family-sofa')
    for offset,material in [(-.91,'olive-velvet'),(.91,'fabric-dark')]:
        cushion((cx+offset,cy+.13,z+.65),(.40,.17,.36),material,2,r=.085,owner='family-sofa')
    k.furnishing('sofa',room,footprint(cx-1.31,cy-.475,cx+1.31,cy+.475))
    piece('woven-area-rug',(cx-1.54,11.02,.011,cx+1.54,13.11,.024),'rug','lounge-rug','rug')
    piece('coffee-table-plinth',(cx-.48,11.79,.03,cx+.48,12.20,.34),'smoked-oak','coffee-table')
    cushion((cx,12,z+.385),(1.17,.65,.085),'travertine',2,r=.04,owner='coffee-table')
    k.furnishing('coffee-table',room,footprint(cx-.585,11.675,cx+.585,12.325))
    # A 98-inch 16:9 flat panel on the solid east wall, between the doors.
    piece('tv-wall-bracket',(cx-.30,9.516,1.04,cx+.30,9.57,1.48),'frame','family-tv')
    piece('family-tv-bezel',(cx-1.092,9.57,.85,cx+1.092,9.618,2.085),'frame','family-tv')
    piece('family-tv-display',(cx-1.082,9.618,.861,cx+1.082,9.623,2.078),'blackglass','family-tv')
    piece('low-media-console',(cx-1.20,9.52,.16,cx+1.20,9.91,.51),'smoked-oak','media-console')
    for j in range(3):
        x=cx-1.185+j*.79
        piece('console-front-'+str(j),(x,9.911,.18,x+.775,9.925,.483),'oak','media-console')
    k.furnishing('media-console',room,footprint(cx-1.20,9.52+media_offset,cx+1.20,9.93+media_offset))
    # The desk faces south with the west window beside it. Its chair pulls
    # back into the work area, keeping the east-side passage clear.
    dx,dy=1.35,12.25
    piece('office-table-top',(dx-.41,dy-.91,.725,dx+.41,dy+.91,.77),'smoked-oak','office-desk')
    for xx in (dx-.32,dx+.32):
        for yy in (dy-.81,dy+.81):
            piece(f'desk-leg-{xx}-{yy}',(xx-.025,yy-.025,.01,xx+.025,yy+.025,.73),'frame','office-desk')
    k.furnishing('desk',room,box(dx-.41,dy-.91,dx+.41,dy+.91))
    piece('computer-base',(dx-.21,dy-.14,.77,dx+.03,dy+.14,.788),'frame','desktop-computer')
    piece('monitor-neck',(dx-.14,dy-.03,.788,dx-.09,dy+.03,1.05),'steel','desktop-computer')
    piece('monitor-bezel',(dx-.14,dy-.32,1.00,dx-.09,dy+.32,1.38),'frame','desktop-computer')
    piece('monitor-display',(dx-.089,dy-.309,1.012,dx-.086,dy+.309,1.368),'blackglass','desktop-computer')
    piece('keyboard',(dx+.11,dy-.22,.77,dx+.24,dy+.22,.791),'frame','desktop-computer')
    k.rb((dx+.18,dy-.34,z+.791),(.097,.057,.034),'frame',2,r=.016,owner='desktop-computer')
    piece('desktop-tower',(dx-.30,dy+.53,.02,dx+.09,dy+.72,.49),'frame','desktop-computer')
    chx,chy=dx+.97,dy
    k.rb((chx,chy,z+.49),(.48,.53,.115),'olive-velvet',2,r=.05,owner='office-chair')
    k.rb((chx+.20,chy,z+.77),(.10,.49,.52),'olive-velvet',2,r=.045,owner='office-chair')
    k.cylinder((chx,chy,z+.27),.035,.35,'steel',2,'furniture')
    for j in range(5):
        a=tau*j/5
        tip=(chx+.31*cos(a),chy+.31*sin(a))
        k.beam((chx,chy,z+.15),(*tip,z+.09),.018,'frame',2,'furniture')
        k.ball((*tip,z+.055),(.05,.04,.05),'frame',2,'furniture')
    k.furnishing('office-chair',room,box(chx-.32,chy-.32,chx+.32,chy+.32))
    for x,y in [(cx+1.2,lounge_y(12.65)),(cx-.65,lounge_y(10.6+media_offset)),(2.25,12.1)]:
        k.light((x,y,z+3.12),20,'#fff0d6','family-hall')
