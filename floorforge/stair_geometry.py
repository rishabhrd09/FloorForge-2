"""Stair-local coordinates shared by plan validation, scene and exports.

x/y are the world bounding-box minimum; width/depth describe the unrotated
core. A 90-degree turn sends the first flight toward decreasing world x.
"""
from shapely.affinity import affine_transform
from shapely.geometry import box
from shapely.ops import unary_union


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
    if st.get('shape') == 'quarter-turn':
        x, y, fw, land = (st[k] for k in ('x','y','flight_width','landing_mm'))
        run = (st['riser_count']//2-1)*st['tread_mm']
        return unary_union([box(x,y,x+fw,y+run), box(x,y+run,x+land,y+run+land),
                            box(x+land,y+run+land-fw,x+land+run,y+run+land)])
    return shape(st,box(st['x'],st['y'],st['x']+st['width'],st['y']+st['depth']))


def well(st):
    if st.get('shape') == 'quarter-turn':return footprint(st)
    start = 0 if st.get('open_arrival') or st.get('openArrival') else st['landing_mm']
    return shape(st,box(st['x'],st['y']+start,st['x']+st['width'],st['y']+st['depth']))


def quarter_parts(st):
    """Actual tread/landing solids in millimetres, shared by scene and IFC."""
    x,y,fw,land,t,r=(st[k] for k in ('x','y','flight_width','landing_mm','tread_mm','riser_mm'))
    n=st['riser_count']//2; run=(n-1)*t
    reverse=st.get('rise_direction')=='south-east'
    parts=[]
    for j in range(n-1):
        # One flight runs E-W beside the south wall; the other runs S-N at the west end.
        a=y+j*t; z=(2*n-1-j if reverse else j+1)*r
        parts.append({'id':f'east-west-{j}', 'bounds':[x,a,max(0,z-r-80),x+fw,a+t,z]})
        a=x+land+j*t; z=(n-1-j if reverse else n+1+j)*r
        parts.append({'id':f'south-north-{j}', 'bounds':[a,y+run+land-fw,max(0,z-r-80),a+t,y+run+land,z]})
    parts.append({'id':'turn-landing','bounds':[x,y+run,n*r-160,x+land,y+run+land,n*r]})
    return parts


def quarter_path(st):
    x,y,fw,land=(st[k] for k in ('x','y','flight_width','landing_mm'))
    run=(st['riser_count']//2-1)*st['tread_mm']
    p=[[x+fw/2,y],[x+fw/2,y+run+land/2],[x+land+run,y+run+land-fw/2]]
    return list(reversed(p)) if st.get('rise_direction')=='south-east' else p
