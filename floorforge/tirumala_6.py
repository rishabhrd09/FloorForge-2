"""Private garden house. The ordinary custom-plan compiler owns walls and doors.
These details add the two stacked Tirumala flights, open dining gallery, lower
arrival porch and furnished family hall to that same model.
"""
import math
import random

from shapely import get_parts
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, linemerge
from shapely.affinity import scale
from .plan_geometry import geometry, regions
from .scene_kit import Kit
from .model import DesignError

FT = .3048
H = 3.508

def xy(east, south):
    return ((40-south)*FT, (50-east)*FT)

def private_garden(building):
    return building.get('planning',{}).get('privateGarden',False)

def coordinate_levels(b, plan):
    spaces = {s['id']:s for s in b['spaces']}
    b['planning']['rectangularLanding']=plan['tirumalaMeta'].get('rectangularLanding',False)
    north_terrace = plan['tirumalaMeta'].get('northTerrace', False)
    b['planning']['northTerrace'] = north_terrace
    if north_terrace:
        from .tirumala_6_terrace import frame_members
        b['terraceFrame'] = frame_members(b['brief']['floor_height_mm'])
    stair_host = 'leisure-hall' if north_terrace else 'upper-landing' if 'upper-landing' in spaces else 'roof-garden'
    hosts = ('living','gallery','stair-lobby' if 'stair-lobby' in spaces else stair_host)
    if 'upper-landing' not in spaces:
        deck = Polygon(spaces['roof-garden']['polygon'])
        edges = [g['points'] for g in b['guards'] if g['owner'] == 'roof-garden']
        b['guards'] = [g for g in b['guards'] if g['owner'] != 'roof-garden']
        for index, edge in enumerate(get_parts(linemerge(edges))):
            # The white parapet turns continuously at the corners. Keep its
            # full thickness on the deck so the street elevation follows the slab.
            masonry = edge.buffer(120, cap_style=3, join_style=2).intersection(deck)
            b['guards'].append(dict(id=f'roof-garden-guard-{index}', owner='roof-garden',
                                    floor=2, height=1100, points=list(edge.coords),
                                    parapet=regions(masonry)))
    combined=plan['tirumalaMeta'].get('combinedArrival',False)
    porch_id='east-porch' if combined else 'car-porch'
    hall='leisure-hall' if 'leisure-hall' in spaces else 'auditorium'
    if not all(key in spaces for key in (*hosts,porch_id,hall)) or b['brief']['floor_height_mm']!=3508:
        raise DesignError('TIRUMALA_STAIR_FIT','The garden house needs its three stair lobbies and 3508 mm floor pitch.')
    source=plan['tirumalaMeta'].get('stairTreads', [])
    if (not isinstance(source,list) or len(source)!=23 or
            any(not isinstance(s,dict) or not isinstance(s.get('top'),(int,float)) or
                len(s.get('bounds',[]))!=4 or not all(isinstance(v,(float,int)) and math.isfinite(v) for v in s['bounds'])
                for s in source) or source[-1]['top']!=3508):
        raise DesignError('TIRUMALA_STAIR_FIT','Supply all three flights, their landings and first-floor arrival.')

    well=unary_union([box(*step['bounds']) for step in source])
    west=source[-1]['bounds'][1]-7800
    void=box(1250,6075+west,6300,7800+west)
    b['planning']['stairWestMm']=west
    b['planning']['eastPorchRevision']=plan['tirumalaMeta'].get('eastPorchRevision',False)
    for f,host in enumerate(hosts):
        if not Polygon(spaces[host]['clear']).buffer(1).covers(well):
            raise DesignError('TIRUMALA_STAIR_FIT','The original Tirumala stair no longer fits its lobby.')
        flights=[{**step,'top':step['top']+3508*f} for step in source]
        b['stairs'].append(dict(id=f't6-stair-{f}',shape='three-flight-c-stair',linkId='garden-stair',roomId=host,floor=f,to_floor=f+1 if f<2 else None,
            x=150,y=5000+west,width=5000,depth=3900,flight_width=1100,landing_mm=1100,well=100,riser_count=20,riser_mm=175.4,tread_mm=245,flights=flights))
        if f:
            hole=well.union(void) if f==1 and 'suite-entry' not in spaces else well
            plate=b['floor_plates'][f]
            plate['regions']=regions(geometry(plate['regions']).difference(hole))
            plate['openings'].append(dict(id=f't6-slab-cut-{f}',regions=regions(hole)))
            ceiling=b['roofs'][f-1]
            ceiling['ceiling']=regions(geometry(ceiling['ceiling']).difference(hole))
            if f==1 and 'suite-entry' not in spaces and not Polygon(spaces[host]['clear']).covers(void):
                raise DesignError('TIRUMALA_VOID_FIT','The dining opening must lie inside the first-floor gallery.')
    if 'suite-entry' in spaces:
        from .tirumala_6_daylight import cut_lightwell
        cut_lightwell(b,spaces)
    plate=b['floor_plates'][0]
    if not combined:
        plate['regions']=regions(geometry(plate['regions']).difference(Polygon(spaces[porch_id]['polygon'])))
    b['planning']['lowerPorchMm']=0 if combined else -152.4
    from .tirumala_6_site import boundary_layout
    # Older saved copies predate the boundary schedule.
    spans=plan['tirumalaMeta'].get('eastGates', [('east-walk-gate','pedestrian',7101.84,5547.36),('east-car-gate','vehicle',5303.52,2621.28)])
    enclosure=boundary_layout(b,spans)
    b['siteBoundary']=enclosure
    if combined:
        gate=next(gate for gate in enclosure['gates'] if gate['kind']=='vehicle')
        # The outer 1.48 m is within the paved roadside verge. Carry the last
        # 1.26 m through the gateway to keep the gradient at 1:10.
        ramp=dict(x0=gate['x0_mm'],x1=gate['x1_mm'],y0=-1480,y1=1260,z0=-265,z1=9)
        b['vehicleRamp']=ramp
        ramp_plan=box(ramp['x0'],ramp['y0'],ramp['x1'],ramp['y1'])
        plate['regions']=regions(geometry(plate['regions']).difference(ramp_plan))
    if plan['tirumalaMeta'].get('colony'):
        b['planning']['colony']=plan['tirumalaMeta']['colony']
        b['planning']['colonyMaterials']=plan['tirumalaMeta']['colonyMaterials']
    perimeter_foundation=unary_union([Polygon(r['polygon']) for r in enclosure['runs']]+[
        box(*[part['bounds'][i] for i in (0,1,3,4)]) for part in enclosure['parts'] if '-jamb-' in part['id']])
    enclosure['masonryFootprint']=regions(perimeter_foundation)
    # Do not run the porch/garden floor slab through the masonry at the plot line.
    plate['regions']=regions(geometry(plate['regions']).difference(perimeter_foundation))

def furnish(scene,b):
    kit=Kit(random.Random(606))
    rooms={r['id']:r for r in b['spaces']}
    west=b['planning']['stairWestMm']/1000
    revised=b['planning']['eastPorchRevision']
    east=1 if revised else 0
    extra=2 if revised else 0
    ramp=b.get('vehicleRamp')
    mats=scene['materials']
    for name,base,color,rough in [('travertine','stone','#cfb99b',.58),('olive-velvet','fabric','#686b50',.92),('smoked-oak','timber','#79543c',.5),('bronze','brass','#ad8658',.32),('acoustic-felt','fabric','#45434a',.98),('cinema-screen','linen','#f4ede0',.83)]:
        mats[name]={**mats[base],'color':color,'roughness':rough}
    from .tirumala_5_finishes import apply_house_daylight, apply_house_palette
    apply_house_palette(mats)
    profile = scene.setdefault('presentation', {})
    apply_house_daylight(profile)
    # Match the finished hall's daylight plate without dimming exterior or night views.
    profile['interior'].update(daylightExposureScale=.38, contrast=1.085, punch=.30)
    for surface in ('wall', 'ceiling'):
        mats[surface].update(params=[.12,0,0,0], normal=.10)
    for target,source in [('ivory-vitrified','ivory-marble-polished'),('ivory-vitrified-matte','ivory-marble-satin-wet'),
                          ('flagstone','ivory-marble-exterior-matte'),('travertine','t5-honed-coping'),('smoked-oak','t5-door-teak'),
                          ('bronze','t5-soft-charcoal'),('doorframe','t5-door-teak'),('cabinet','t5-light-timber')]:
        mats[target]=dict(mats[source])
    def block(name,rect,z0,z1,mat,f,role='furniture'):
        a,c=xy(rect[0],rect[1]),xy(rect[2],rect[3])
        kit.rect((min(a[0],c[0]),min(a[1],c[1]),z0,max(a[0],c[0]),max(a[1],c[1]),z1),mat,f,role,name,name)
    def care_block(name,rect,*args):
        a,b,c,d=rect
        block(name,(a+east,b,c+east,d),*args)
    def chair(east,south,base,index):
        x,y=xy(east,south)
        for suffix,offset,dims,mat in [
            ('plinth',(0,0,.18),(.63,.55,.32),'smoked-oak'),
            ('seat',(0,0,.43),(.56,.57,.16),'olive-velvet'),
            ('back',(-.29,0,.68),(.14,.61,.65),'olive-velvet'),
            ('arm-left',(0,.32,.55),(.59,.075,.18),'smoked-oak'),
            ('arm-right',(0,-.32,.55),(.59,.075,.18),'smoked-oak')]:
            kit.rb((x+offset[0],y+offset[1],base+offset[2]),dims,mat,2,r=.045,owner=f'cinema-seat-{index}-{suffix}')
    has_foyer = 'upper-landing' in rooms
    north_terrace = b['planning'].get('northTerrace', False)
    landing = b['stairs'][2]['roomId']
    scene['nodes']=[n for n in scene['nodes'] if n['id'] not in ('car-porch/floor','gallery/floor',landing+'/floor')]
    # At zero road setback only the two east bays receive gate piers.
    # Remove the automatic single-drive boundary and replace its plinth return.
    scene['nodes']=[n for n in scene['nodes'] if n['floor']!=-1 or n['role'] not in ('gate','fixture','detail','plinth','step') and not(n['role']=='site' and n['material'] not in ('asphalt','paver','linen'))]
    if ramp:
        porch=box(ramp['x0'],ramp['y0'],ramp['x1'],ramp['y1'])
        scene['nodes']=[n for n in scene['nodes'] if n['id']!='east-porch/floor']
        floor=Polygon(rooms['east-porch']['polygon']).difference(porch).difference(geometry(b['siteBoundary']['masonryFootprint']))
        kit.poly_mesh(scale(floor,xfact=.001,yfact=.001,origin=(0,0)),.002,.009,'flagstone',0,'finish','shared-porch-paving','east-porch')
        from .tirumala_6_site import add_vehicle_ramp
        add_vehicle_ramp(kit,ramp)
    else:
        porch=Polygon(rooms['car-porch']['polygon'])
    plinth=geometry(b['floor_plates'][0]['outline']).difference(porch).difference(geometry(b['siteBoundary']['masonryFootprint']))
    kit.poly_mesh(scale(plinth,xfact=.001,yfact=.001,origin=(0,0)),-.30,-.15,'stone',-1,'plinth','t6-plinth')
    from .tirumala_6_site import build_enclosure
    build_enclosure(kit,scene,b['siteBoundary'])
    kit.rect((12.26,-8,-.35,21.26,21,-.31),'asphalt',-1,'site','north-road')
    block('utility-washer',(47.3,37.7,49.6,39.7),.012,.89,'appliance',0)
    block('washer-lid',(47.5,37.86,49.4,39.5),.89,.92,'frame',0)
    block('wash-basin',(47.4,35.7 if revised else 33.5,49.6,37.1 if revised else 34.9),.69,.87,'ceramic',0)
    block('wash-bowl',(47.58,35.9 if revised else 33.7,49.4,36.88 if revised else 34.68),.87,.876,'steel',0)
    care_block('monitor-cart',(22.1,3.0,24.3,4.5),.05,.78,'smoked-oak',0)
    care_block('monitor-foot',(22.7,3.45,23.55,4.05),.78,.82,'frame',0)
    care_block('monitor-stand',(23.06,3.59,23.18,3.8),.82,.99,'steel',0)
    care_block('bedside-monitor',(22.35,3.55,23.94,3.85),.99,1.32,'frame',0)
    for side in (32.5,33.85):
        care_block('icu-chair-arm-'+str(side),(side,8,side+.19,10.05),.28,.66,'smoked-oak',0)
    care_block('icu-chair-seat',(32.65,8,33.9,10.05),.32,.48,'olive-velvet',0)
    care_block('icu-chair-back',(32.5,8,34.02,8.23),.46,.93,'olive-velvet',0)
    # The stock street canopy assumes one facade plane. Fit eaves and screens
    # to each actual step in the east elevation instead.
    scene['nodes']=[n for n in scene['nodes'] if n['role'] not in ('canopy','band','pipe') and
                    not(n['floor']==0 and n['role'] in ('post','fixture') and n['position'][1]<-.45)]
    for n in scene['nodes']:
        if n['id'] in ('library/floor','west-suite/floor','garden-suite/floor','master/floor','caregiver/floor'):n['material']='woodfloor'
        elif north_terrace and n['id']=='roof-garden/floor':n['material']='flagstone'
        elif n['id']=='auditorium/floor':n['material']='acoustic-felt'
    for member in b.get('terraceFrame', []):
        x,y,X,Y = [v/1000 for v in member['bounds']]
        f = member['floor']
        base = f*H + member['base']/1000
        top = f*H + member['top']/1000
        kit.rect((x,y,base,X,Y,top),'t5-ivory-render',f,'post' if member['kind']=='column' else 'beam',member['id'],member['id'])
        if member['kind']=='column':
            kit.obstacle(box(x,y,X,Y),f,member['id'])
    # The top terrace looks across the north garden. A colonnade carries the
    # pergola on the terrace itself, leaving the screened gallery door clear.
    if has_foyer:
        for ex in (19.6,34.3):
            for sy in (7.6,14.4):
                block(f'pergola-post-{ex}-{sy}',(ex,sy,ex+.32,sy+.32),2*H,2*H+2.45,'smoked-oak',2,'post')
            block(f'pergola-beam-{ex}',(ex,7.4,ex+.34,14.95),2*H+2.44,2*H+2.61,'smoked-oak',2,'canopy')
        for j in range(15):
            sy=7.45+j*.52
            block('pergola-blade-'+str(j),(19.35,sy,34.88,sy+.18),2*H+2.57,2*H+2.70,'smoked-oak',2,'canopy')
    screen_start=28.9 if not has_foyer else 25.1 if 'east-balcony' in rooms else 18.0
    screen_count=5 if not has_foyer else 10 if 'east-balcony' in rooms else 15
    for j in range(screen_count):
        sy=screen_start+j*.50
        block('gallery-sunscreen-'+str(j),(44.23,sy,44.75,sy+.15),H+.12,2*H-.13,'smoked-oak',1,'facade-screen')
    block('gallery-screen-sill',(43.85,screen_start-.2,44.9,screen_start+(screen_count-1)*.5+.30),H+.02,H+.14,'travertine',1,'facade')
    block('gallery-screen-lintel',(43.85,screen_start-.2,44.9,screen_start+(screen_count-1)*.5+.30),2*H-.2,2*H-.08,'travertine',1,'facade')
    if ramp:
        roof=scale(Polygon(rooms['east-porch']['polygon']),xfact=.001,yfact=.001,origin=(0,0))
        kit.poly_mesh(roof,H-.19,H-.035,'travertine',0,'canopy','combined-porch-canopy')
    else:
        block('entrance-canopy',(38.1-extra,16.1,49.92,22),H-.19,H-.035,'travertine',0,'canopy')
    # Bronze shadow joint beneath the limestone fascia, recessed at the road edge.
    block('garden-bench',(10,11.7,13.25,12.0),.43,.76,'smoked-oak',0)
    block('verandah-side-table',(15.5,11.8,16.65,12.95),.02,.43,'travertine',0)
    seat_north = 1.6 if north_terrace else 8.5
    block('terrace-seat',(22,seat_north,28.8,seat_north+2.2),2*H+.08,2*H+.37,'smoked-oak',2)
    block('terrace-upholstery',(22.05,seat_north+.05,28.75,seat_north+2.15),2*H+.37,2*H+.50,'olive-velvet',2)
    kit.plant(*xy(31.9,2.5 if north_terrace else 10.25),2*H+.01,'fiddle_leaf',height=1.65,f=2,pot=(.25,.43,'ceramic'))
    for f,host in [(1,'gallery'),(2,landing)]:
        surface=geometry(b['floor_plates'][f]['regions']).intersection(Polygon(rooms[host]['clear']))
        kit.poly_mesh(scale(surface,xfact=.001,yfact=.001,origin=(0,0)),f*H+.002,f*H+.009,'flagstone' if host=='roof-garden' else 'ivory-vitrified',f,'finish',host+'/floor',host)
    for f in (0,1):
        for j,step in enumerate(b['stairs'][f]['flights']):
            x,y,X,Y=[v/1000 for v in step['bounds']]
            z=step['top']/1000
            kit.rect((x,y,max(f*H,z-.19),X,Y,z-.025),'travertine',f,'stair',f't6-flight-{f}-{j}')
            kit.rect((x,y,z-.025,X,Y,z),'smoked-oak',f,'stair',f't6-tread-{f}-{j}')
        for a,c in [((1.525,6.1,0),(1.25,6.1,.35)),((1.25,6.15,.35),(1.25,7.8,1.575)),((1.25,7.8,1.575),(3.45,7.8,3.15)),((3.45,7.8,3.15),(4.55,7.8,3.15)),((4.55,7.8,3.15),(5.15,7.8,H))]:
            a=(a[0],a[1]+west,a[2]);c=(c[0],c[1]+west,c[2])
            za=f*H+a[2];zc=f*H+c[2]
            kit.beam((*a[:2],za+.95),(*c[:2],zc+.95),.027,'smoked-oak',f,'railing')
            if f==1 and b['planning'].get('rectangularLanding'):
                import trimesh
                dx,dy=c[0]-a[0],c[1]-a[1]
                d=math.hypot(dx,dy)
                vertices=[(p[0]-side*dy/d,p[1]+side*dx/d,z+offset)
                          for p,z in ((a,za),(c,zc)) for side in (-.035,.035) for offset in (0,.94)]
                kit.node(kit.asset(trimesh.convex.convex_hull(vertices)),'t5-ivory-render',floor=f,role='railing')
                continue
            count=max(1,math.ceil(math.dist(a[:2],c[:2])/.14))
            for j in range(count):
                t=j/count;x=a[0]+t*(c[0]-a[0]);y=a[1]+t*(c[1]-a[1]);z=za+t*(zc-za)
                kit.beam((x,y,z),(x,y,z+.94),.009,'bronze',f,'railing')
    for f in (1,2):
        # Keep the two landing edges open and protect exposed gallery sides.
        well=unary_union([box(*s['bounds']) for s in b['stairs'][0]['flights']])
        cut=well.union(box(1250,6075+west*1000,6300,7800+west*1000)) if f==1 and 'suite-entry' not in rooms else well
        landings=[LineString([(5150,7800+west*1000),(5150,8900+west*1000)])]
        # The first floor also has an upward flight. At the top there is only
        # an arrival, so the guard continues past the foot of the flight below.
        if f==1 or has_foyer:
            landings.append(LineString([(1525,5000+west*1000),(1525,6100+west*1000)]))
        if f==1 and b['planning'].get('rectangularLanding'):
            continue  # The modelled opaque stair guard already follows this well.
        rail=cut.boundary.difference(unary_union(landings).buffer(2))
        for edge in getattr(rail,'geoms',[rail]):
            for a,c in zip(edge.coords,list(edge.coords)[1:]):
                a,c=[(x/1000,y/1000) for x,y in [a,c]]
                if math.dist(a,c)<.12:continue
                kit.beam((*a,f*H+1.03),(*c,f*H+1.03),.028,'smoked-oak',f,'railing')
                if f==1 and box(1.25,6.075+west,6.3,7.8+west).boundary.distance(Point((a[0]+c[0])/2,(a[1]+c[1])/2))<.005:
                    parapet=LineString([a,c]).buffer(.055,cap_style=2)
                    kit.poly_mesh(parapet,f*H,f*H+1.02,'t5-ivory-render',f,'railing')
                    continue
                for j in range(math.ceil(math.dist(a,c)/.15)):
                    t=j/math.ceil(math.dist(a,c)/.15);x=a[0]+t*(c[0]-a[0]);y=a[1]+t*(c[1]-a[1])
                    kit.beam((x,y,f*H), (x,y,f*H+1.02),.009,'bronze',f,'railing')
    if not ramp:block('drop-off-paving',(38-extra,22,50,32),-.29,-.1524,'flagstone',0,'floor')
    block('east-lawn',(45.1+east,.1,49.9,15.9),.01,.045,'lawn',0,'landscape')
    block('court-grass',(9.38,.12,18.9+east,5.9),.01,.05,'lawn',0,'landscape')
    block('verandah-bench',(10.0,12,13.2,13.5),.08,.39,'smoked-oak',0)
    block('verandah-cushion',(10.0,12,13.2,13.5),.39,.49,'olive-velvet',0)
    for y in [1.8,5.2,9.3,13.7]:
        kit.plant(*xy(48.4,y),.05,'shrub_flowering',height=.7,f=0)
    for e in [39-extra,49]:
        block('portal-'+str(e),(e,16.1,e+.37,16.6),0,H-.14,'travertine',0,'post')
    for j in range(25+int(2*extra)):
        block('porch-soffit-'+str(j),(38.25-extra+j*.46,16.2,38.37-extra+j*.46,21.8),H-.255,H-.195,'smoked-oak',0,'ceiling')
    for e in (39.6-extra,44-extra/2,48.4):
        kit.light((*xy(e,19),H-.28),12,'#ffdda9','porch')
    # Portal joinery, paving border and riser belong to the walkable model.
    for i in range(14):
        x=8.05+i*.046
        kit.rect((x,9.33-east*FT,.012,x+.029,9.377-east*FT,2.55),'smoked-oak',0,'joinery',f'icu-teak-reveal-{i}')
    if not ramp:
        for x in (2.5,5.425):
            kit.rect((x-.05,.02,-.1524,x+.05,3.635+extra*FT,-.149),'kota-stone',0,'finish',f'porch-kota-edge-{x}')
        for y in (.075,3.58+extra*FT):
            kit.rect((2.55,y-.05,-.1524,5.375,y+.05,-.149),'kota-stone',0,'finish',f'porch-cross-edge-{y}')
        kit.rect((5.48,.01,-.1524,5.50,3.64+extra*FT,.008),'travertine',0,'step','east-porch-stone-riser')
    for e,y,h in [(15.2,4.6,1.6),(17.4,3.7,1.22)]:
        kit.plant(*xy(e,y),.05,'palm',height=h,f=0)
    # Tubular side rails and an IV stand distinguish the adjustable care bed.
    equipment_start=len(kit.nodes)
    for yy in (5.96,7.055):
        kit.beam((8.67,yy,.84),(9.64,yy,.84),.017,'steel',0,'furniture')
        for xx in (8.67,9.64):kit.beam((xx,yy,.53),(xx,yy,.84),.016,'steel',0,'furniture')
    kit.cylinder((8.49,7.28,.94),.014,1.84,'steel',0,'furniture')
    for angle in range(0,360,90):
        a=math.radians(angle);xx=8.49+.20*math.cos(a);yy=7.28+.20*math.sin(a)
        kit.beam((8.49,7.28,.10),(xx,yy,.08),.015,'steel',0,'furniture')
        kit.ball((xx,yy,.05),(.045,.032,.045),'frame',0,'furniture')
    kit.beam((8.33,7.28,1.85),(8.65,7.28,1.85),.012,'steel',0,'furniture')
    kit.rb((8.64,7.28,1.72),(.08,.05,.19),'frosted',0,r=.022)
    for node in kit.nodes[equipment_start:]:node['position'][1]-=east*FT
    if b['planning'].get('rectangularLanding'):
        from .tirumala_6_lobby import finish_lobby
        finish_lobby(scene,b,kit,H)
    z=2*H
    if 'leisure-hall' in rooms:
        from .tirumala_6_lounge import furnish_lounge
        furnish_lounge(kit,rooms['leisure-hall'],z,west_media_wall=north_terrace)
        # Planters at the far edges leave the sliding-door approaches clear.
        for ex,sy in [(42.7,22.45),(42.2,38.3)]:
            kit.plant(*xy(ex,sy),H+.01,'fiddle_leaf',height=1.1,f=1,pot=(.17,.33,'ceramic'))
        block('terrace-teak-bench',(38.2,38.1,41.5,39.35),H+.07,H+.42,'smoked-oak',1)
        kit.plant(*xy(8.2 if north_terrace else 33.6,2.0 if north_terrace else 21.5),z+.01,'shrub_flowering',height=.82,f=2,pot=(.23,.38,'ceramic'))
    else:
        # Theatre: broad screen wall, flush entry aisle, five rows with a centre aisle.
        block('screen-wall',(3.28,7.35,18.7,7.65),z+.01,z+3.15,'acoustic-felt',2)
        block('projection-screen',(4.45,7.67,17.55,7.72),z+.83,z+2.89,'cinema-screen',2)
        block('screen-stage',(3.4,7.8,18.6,11.6),z+.01,z+.20,'smoked-oak',2)
        for j,sy in enumerate([15.1,19.25,26.8,31.05,35.3]):
            for i,ex in enumerate([5.3,7.75,13.35,15.8]):chair(ex,sy,z,j*4+i+1)
        for i,sy in enumerate([10.4,13.8,17.2,20.6,26.8,30.2,33.6,37.0]):
            block('acoustic-panel-'+str(i),(18.62,sy,18.76,sy+1.85),z+.68,z+2.85,'acoustic-felt',2)
            block('oak-reveal-'+str(i),(18.58,sy,18.62,sy+.09),z+.66,z+2.88,'bronze',2)
        for sy in [12,20,28,36]:
            for ex in [4.5,17.4]:kit.light((*xy(ex,sy),z+3.15),38,'#ffe4bb','auditorium')
    if 'suite-entry' in rooms:
        from .tirumala_6_daylight import finish_lightwell, stair_soffits
        finish_lightwell(kit,b,H)
        for f in (0,1):
            stair_soffits(kit,b['stairs'][f]['flights'],f)
        # Continuous timber seat along the bedroom balcony's east edge.
        block('loggia-bench',(42.35,2.1,43.7,8.8),H+.09,H+.43,'smoked-oak',1)
        block('loggia-seat',(42.32,2.14,43.65,8.76),H+.43,H+.48,'olive-velvet',1)
        kit.plant(*xy(42.75,12.8),H+.01,'fiddle_leaf',height=1.3,f=1,pot=(.22,.38,'ceramic'))
        for node in scene['nodes']:
            if node['id'] in ('loggia/floor','east-balcony/floor','sun-terrace/floor'):
                node['material']='flagstone'
        block('suite-window-seat',(3.4,27.35,5.0,31.15),H+.12,H+.40,'smoked-oak',1)
        block('suite-window-cushion',(3.45,27.4,5.0,31.1),H+.40,H+.49,'linen',1)
        block('suite-vestibule-console',(10.2,20.85,12.8,21.65),H+.68,H+.83,'smoked-oak',1)
    for i,node in enumerate(kit.nodes):
        if node['id'].startswith('object-'):node['id']=f't6-detail-{i}'
    scene['nodes'].extend(kit.nodes);scene['assets'].update(kit.assets);scene['lights'].extend(kit.lights)
    for plant in kit.vegetation:plant['id']='t6-'+plant['id']
    scene['vegetation'].extend(kit.vegetation)
    scene['furniture'].extend(kit.furniture);scene['colliders'].extend(kit.colliders)
    scene['cameras'].update(hero=dict(position=[23,-17,14],target=[6,6.5,4],fov=43))
    for key,eye,aim,fov in [
        ('east_arrival',(68,12,1.65),(44,23,1.55),63),('icu_garden',(30.25+east,15.5,1.57),(19.52+east,7.95,1.22),70),('garden_verandah',(18,12.9,1.5),(12.4,3.4,.95),64),
        ('leisure_hall',(5.4,30.9,z+1.58),(15.0,15.8,z+1.2),68),
        ('office_corner',(13.2 if not has_foyer else 15.6,24.5,z+1.56),(8.6,36.7,z+1.10),64),
        ('upper_balcony',(39.0,26.7,H+1.58),(45.4,16.4,H+.95),68),
        ('east_roof_terrace',(32.8,37.9,z+1.62),(22.4,9.1,z+1.05),70),
        ('kitchen',(33.65,35.8,1.52),(44.2,36.15,1.27),74),
        ('living_gallery',(33.1,36.9,1.91),(21.78,22.0,2.12),72)]:
        scene['cameras'][key]=dict(position=[*xy(*eye[:2]),eye[2]],target=[*xy(*aim[:2]),aim[2]],fov=fov,label=key.replace('_',' ').title(),floor=2 if key in ('leisure_hall','office_corner','east_roof_terrace') else 1 if key=='upper_balcony' else 0)
    if north_terrace:
        for key,eye,aim in [
            ('leisure_hall',(19.6,30.3),(4.8,22.3)),
            ('north_roof_terrace',(48.0,12.4),(8.0,7.5))
        ]:
            scene['cameras'][key]=dict(position=[*xy(*eye),z+1.60],target=[*xy(*aim),z+1.15],
                                       fov=66,label=key.replace('_',' ').title(),floor=2)
        scene['cameras'].pop('east_roof_terrace')
        if 'stair-lobby' in rooms:
            scene['cameras']['leisure_hall'].update(position=[*xy(16.8,32.2),z+1.58],target=[*xy(7.6,18.2),z+1.25])
            eye = [*xy(28.1,32.2),z+1.58]
            target = [*xy(29,16.3),z+1.40]
            dx,dy,dz = (target[i]-eye[i] for i in range(3))
            # The Cycles plate uses a 21 mm lens, 36 mm sensor and a 1200 × 920 crop.
            vertical_fov = math.degrees(2*math.atan(18/21 * 920/1200))
            scene['cameras']['hall_windows']=dict(position=eye,target=target,fov=vertical_fov,
                label='Hall windows and terrace door',floor=2,enter_walk=True,eye_height_above_ffl_m=1.58,
                walker=dict(position=eye,yaw_rad=math.atan2(-dx,dy),pitch_rad=math.atan2(dz,math.hypot(dx,dy))))
    if 'suite-entry' in rooms:
        for key,eye,aim,f in [
            ('living_rooflight',((28.35 if b['planning'].get('rectangularLanding') else 14.0), (21.0 if b['planning'].get('rectangularLanding') else 17.35),1.55),(28.85,18.45,3*H+.28),0),
            ('living_gallery',(32.25,27.5,1.6),(12.7,20.45,2.8),0),
            *(([('stair_lobby',(21.25,17.25,H+1.58),(26.5,29.35,H+.70),1),
                ('suite_northlight',(6.75,30.4,H+1.63),(5.9,29.1,3*H+.65),1)]
                if b['planning'].get('rectangularLanding') else [])),
            ('master_suite',(5.8,26.1,H+1.58),(13.7,36.0,H+1.10),1),
            ('upper_balcony',(42.4,26.9,H+1.58),(40.6,4.7,H+1.12),1)
        ]:
            ep=[*xy(*eye[:2]),eye[2]]
            tp=[*xy(*aim[:2]),aim[2]]
            dx,dy,dz=[t-e for e,t in zip(ep,tp)]
            scene['cameras'][key]=dict(position=ep,target=tp,fov=68,label=key.replace('_',' ').title(),
                floor=f,enter_walk=True,eye_height_above_ffl_m=eye[2]-f*H,
                walker=dict(position=ep,yaw_rad=math.atan2(-dx,dy),pitch_rad=math.atan2(dz,math.hypot(dx,dy))))
    gate=next(g for g in b['siteBoundary']['gates'] if g['kind']=='pedestrian')
    gate_center=(gate['x0_mm']+gate['x1_mm'])/2000
    # Both glazed leaves stack together so one interaction clears the passage
    # from either side, including the living-hall approach.
    for opening in b['openings']:
        if 'icu' not in opening['connects'] or not opening.get('stackingSliding'):
            continue
        motion=scene['door_motion'][opening['id']]
        motion['parts']=[{'ids':leaf['ids'],'slide':leaf['slide']} for leaf in motion.pop('layers')]
    scene['walk']['arrival']={'position':[gate_center+.12,-1.23,-.265],'yaw_deg':7}
    scene['walk']['startOnOpen']=True
    if b['planning'].get('colony'):
        scene['context']={**b['planning']['colony'],'project_id':'tirumala-6','detailLevel':'reference',
                          'entryGaps':[[g['x0_mm']/1000,g['x1_mm']/1000] for g in b['siteBoundary']['gates']]}
        scene['materials'].update(b['planning']['colonyMaterials'])
        scene['cameras']['colony_overview']=dict(position=[34,-26,24],target=[11,1,1.5],fov=60,label='Colony view')
        # The shared colony supplies the street surface, verges, kerbs and markings.
        scene['nodes']=[n for n in scene['nodes'] if n['id']!='north-road' and not
                        (n['floor']==-1 and n['role']=='site' and n['material'] in ('asphalt','paver','linen'))]

    scene['walk']['floors']=[dict(floor=f,position=[*xy(22.6-west/FT,21.05),f*H],yaw_deg=0) for f in range(3)]
    return scene
