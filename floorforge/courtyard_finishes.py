"""Garden planting, drainage and restrained surface finishes for authored outdoor geometry."""
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box


def skylit_garden(k, materials, room, height):
    p=Polygon(np.array(room['clear'])/1000);x0,y0,x1,y1=p.bounds
    f=room['floor'];z=f*height;owner=room['id']
    materials['garden-stone']={'color':'#c7c0ac','alt':'#b0a790','roughness':.85,'texture':'paver','kind':'paver','params':[3,2,.003,.08],'tile_m':1.8}
    k.poly_mesh(p,z+.011,z+.018,'garden-stone',f,'finish',owner+'/stone-path',owner)
    # Narrow planting on the bedroom side, set back from the hall door and both rear doors.
    border=p.buffer(-.10,join_style=2)
    beds=border.intersection(box(x0+.10,y0+.70,x0+.47,y1-.3)).union(border.intersection(box(x0+.10,y1-.47,x1-.10,y1-.10)))
    if y1-y0<1.1:
        beds=border.intersection(box(x0+.10,y1-.22,x1-.10,y1-.06))
    k.poly_mesh(beds,z+.02,z+.10,'soil',f,'landscape',owner+'/garden-bed',owner)
    edging=beds.buffer(.035,join_style=2).difference(beds).intersection(p)
    k.poly_mesh(edging,z+.02,z+.14,'stone',f,'landscape',owner+'/bed-edging',owner)
    for i,yy in enumerate(np.arange(y0+1.0,y1-.65,.70)):
        xx=x0+.285
        if beds.covers(Point(xx,yy).buffer(.14)):
            k.plant(xx,yy,z+.10,'monstera' if i%3 else 'cordyline',height=.70 if i%3 else .95,f=f)
    for xx in np.arange(x0+.7,x1-.3,1.1):
        yy=y1-.285
        if beds.covers(Point(xx,yy).buffer(.14)):k.plant(xx,yy,z+.10,'shrub_round',height=.45,f=f)
    # Small shielded lights are entirely inside the planting, not freestanding in the path.
    for i,yy in enumerate(np.arange(y0+1.1,min(y1-.5,y0+4.5),1.6)):
        xx=x0+.19
        k.rect((xx-.035,yy-.045,z+.12,xx+.035,yy+.045,z+.40),'frame',f,'fixture',owner+f'/path-light-{i}',owner)
        k.rect((xx+.035,yy-.03,z+.31,xx+.041,yy+.03,z+.37),'lamp',f,'fixture',owner+f'/path-glow-{i}',owner)
        k.light((xx+.08,yy,z+.34),8,kind='garden')
    k.rect((x1-.14,y1-.27,z+.022,x1-.04,y1-.08,z+.029),'steel',f,'drain',owner+'/drain',owner)
    # Cover is clear glass only. The compiler still excludes opaque slabs/roofs above it.
    # 180 mm above the ground wall head provides a continuous high-level vent gap.
    cover_z=z+height+.03
    k.poly_mesh(p,cover_z,cover_z+.014,'glass',f,'canopy',owner+'/glass-canopy',owner)
    ring=p.boundary.buffer(.025,cap_style=2,join_style=2)
    k.poly_mesh(ring,cover_z-.065,cover_z,'frame',f,'canopy',owner+'/canopy-rim',owner)
    for i,yy in enumerate(np.arange(y0+1.3,y1,1.3)):
        rib=p.intersection(box(x0,yy-.02,x1,yy+.02))
        k.poly_mesh(rib,cover_z-.055,cover_z,'frame',f,'canopy',owner+f'/canopy-rib-{i}',owner)
    for i,(xx,yy) in enumerate(list(p.exterior.coords)[:-1]):
        # Brackets anchored at wall-head level keep the clear walkway free of posts.
        k.rect((xx-.025,yy-.025,z+height-.15,xx+.025,yy+.025,cover_z),'frame',f,'canopy',owner+f'/vent-bracket-{i}',owner)


def layered_facade(k, materials, building, height):
    """Finish-only bands and slim stone piers, cut around every existing opening."""
    materials['facade-limestone']={'color':'#c4baa8','alt':'#a89e8c','roughness':.88,'texture':'stone','kind':'stone','tile_m':1.6}
    for w in building['walls']:
        # Dress exposed front/left faces, leaving the courtyard walls and boundary wings intact.
        if not w['external'] or w['floor']>1:continue
        a=np.array(w['a'])/1000;b=np.array(w['b'])/1000;u=(b-a)/np.linalg.norm(b-a)
        if abs(u[0])>.01:continue  # Side elevation vertical edges in plan.
        if min(a[0],b[0])<1.5 or max(a[0],b[0])>3.2:continue
        n=np.array([-1.,0.]);f=w['floor'];z=f*height
        line=LineString([a+n*.085,b+n*.085]);L=line.length
        if L<1:continue
        # Surface pier only on a solid portion at the end of the wall.
        end=line.interpolate(min(.42,L/2));strip=LineString([line.interpolate(.08),end]).buffer(.018,cap_style=2)
        ops=[o for o in building['openings'] if o['wall_id']==w['id']]
        for o in ops:
            p0=a+u*(o['offset']/1000-.08);p1=a+u*((o['offset']+o['width'])/1000+.08)
            strip=strip.difference(LineString([p0,p1]).buffer(.3,cap_style=2))
        k.poly_mesh(strip,z+.15,z+height-.22,'facade-limestone',f,'wall-panel',w['id']+'/stone-pier',w['id'])
        band=line.buffer(.027,cap_style=2)
        k.poly_mesh(band,z+height-.16,z+height-.08,'frame',f,'wall-panel',w['id']+'/shadow-band',w['id'])
    for r in building['spaces']:
        if r['kind'] not in ('terrace','balcony') or not r.get('clearAccess'):continue
        p=Polygon(np.array(r['clear'])/1000);f=r['floor'];z=f*height;x0,y0,x1,y1=p.bounds
        if r.get('finishStyle')=='honed-sandstone':
            from .upper_finishes import sandstone_deck
            sandstone_deck(k,materials,p,z,f,r['id'])
        else:
            k.poly_mesh(p,z+.012,z+.019,'facade-limestone',f,'finish',r['id']+'/stone-deck',r['id'])
        # Floating fascia and warm soffit follow the authored L, not its bounding rectangle.
        rim=p.boundary.buffer(.025,join_style=2)
        k.poly_mesh(rim,z-.17,z-.055,'frame',f,'fascia',r['id']+'/slab-edge',r['id'])
        k.poly_mesh(p.buffer(-.06,join_style=2),z-.177,z-.171,'oak',f,'canopy',r['id']+'/timber-soffit',r['id'])
        for i,xx in enumerate(np.arange(x0+.6,x1-.5,1.8)):
            yy=y0+.4
            if p.covers(Point(xx,yy).buffer(.12)):
                k.cylinder((xx,yy,z-.18),.045,.012,'lamp',f,'fixture')
                k.light((xx,yy,z-.20),12,kind='porch')


def sheltered_lawn(k, materials, room, height):
    """A usable rear escape path beside a layered lawn, based on the veranda palette."""
    p=Polygon(np.array(room['clear'])/1000);x0,y0,x1,y1=p.bounds
    f=room['floor'];z=f*height;owner=room['id']
    materials['garden-limestone']={'color':'#cec5ae','alt':'#b4a98f','roughness':.87,'texture':'paver','kind':'paver','params':[3,2,.003,.08],'tile_m':1.8}
    k.poly_mesh(p,z+.012,z+.022,'garden-limestone',f,'finish',owner+'/clear-path',owner)
    # The whole right-hand garden is grass; the independent rear return stays paved.
    lawn=p.intersection(box(x1-2.60,y0+.12,x1-.30,y1-.23))
    k.poly_mesh(lawn,z+.022,z+.032,'lawn',f,'lawn',owner+'/grass',owner)
    edging=lawn.buffer(.035,join_style=2).difference(lawn).intersection(p)
    k.poly_mesh(edging,z+.022,z+.045,'stone',f,'landscape',owner+'/grass-edge',owner)
    beds=p.intersection(box(x1-.30,y0+.45,x1-.08,y1-.28)).union(p.intersection(box(x0+.12,y1-.20,x1-.20,y1-.05)))
    k.poly_mesh(beds,z+.022,z+.095,'soil',f,'landscape',owner+'/planting',owner)
    for i,yy in enumerate(np.arange(y0+1.35,y1-.7,1.45)):
        k.plant(x1-.20,yy,z+.095,'grass_ornamental' if i%2 else 'strelitzia',height=.65 if i%2 else 1.15,f=f)
    # Pots sit in the far corners, never across the rear exit or the veranda approach.
    for xx,yy,species,h,r in [(x1-.47,y0+.36,'strelitzia',1.65,.23),(x1-.43,y1-.40,'cordyline',1.35,.22),(x1-1.22,y1-.38,'monstera',.85,.18)]:
        k.plant(xx,yy,z+.022,species,height=h,f=f,pot=(r,.42,'planter'))
    for i,xx in enumerate(np.arange(x0+.7,x1-1.8,1.1)):
        yy=y1-.13
        if p.covers(Point(xx,yy)):
            k.plant(xx,yy,z+.095,'grass_ornamental',height=.42,f=f)
    # Slim warm lights and a timber screen make the boundary a deliberate garden backdrop.
    for i,yy in enumerate(np.arange(y0+.8,y1-.4,1.35)):
        k.rect((x1-.065,yy-.06,z+.45,x1-.025,yy+.06,z+.70),'frame',f,'fixture',owner+f'/light-{i}',owner)
        k.light((x1-.15,yy,z+.57),13,kind='garden')
    for i,yy in enumerate(np.arange(y0+.30,y1-.25,.14)):
        k.rect((x1-.025,yy,z+.35,x1-.005,yy+.045,z+1.65),'oak',f,'wall-panel',owner+f'/screen-{i}',owner)
    k.rect((x1-.32,y1-.32,z+.023,x1-.20,y1-.20,z+.030),'steel',f,'drain',owner+'/drain',owner)
    return [{'id':owner+'/grass','polygon':[list(q) for q in list(lawn.exterior.coords)[:-1]],'holes':[],'z':z+.032,'heightScale':.42}]


def open_puja_entry(k, building):
    """A continuous front feature bay around the open mandir and adjacent entry.

    Thin finishes follow the authored glazing/door cut-outs; they do not narrow
    openings or add a new partition to the hall.
    """
    for room in building['spaces']:
        if room['floor']!=0 or room.get('altarWall')!='front':continue
        x0,y0,x1,_=Polygon(room['clear']).bounds
        hosts={w['id']:w for w in building['walls']}
        window=next((o for o in building['openings'] if room['id'] in o['connects'] and o['kind']=='window' and hosts[o['wall_id']]['external'] and abs(hosts[o['wall_id']]['a'][1]-hosts[o['wall_id']]['b'][1])<1),None)
        if window is None:continue
        w=hosts[window['wall_id']];face=(w['a'][1]-w['thickness']/2)/1000
        left=(x0-90)/1000;right=(x1+90)/1000
        wx=(min(w['a'][0],w['b'][0])+window['offset'])/1000;wr=wx+window['width']/1000
        sill=window['sill']/1000;head=sill+window['height']/1000;owner=room['id']+'/entry-feature'
        def panel(tag,a,c,lo,hi,mat='facade-limestone',depth=.035):
            k.rect((a,face-depth,lo,c,face-.004,hi),mat,0,'wall-panel',owner+'/'+tag,owner)
        # Limestone backing split around the actual ribbon window.
        panel('lower-stone',left,right,.12,sill-.025)
        panel('upper-stone',left,right,head+.025,2.82)
        panel('left-stone',left,wx-.025,sill-.025,head+.025)
        panel('right-stone',wr+.025,right,sill-.025,head+.025)
        # Dark, recessed reveals make the clerestory part of the feature bay.
        panel('window-left',wx-.025,wx,sill-.025,head+.025,'frame',.065)
        panel('window-right',wr,wr+.025,sill-.025,head+.025,'frame',.065)
        panel('window-head',wx,wr,head,head+.025,'frame',.065)
        panel('window-sill',wx,wr,sill-.025,sill,'frame',.065)
        for i,xx in enumerate(np.arange(left+.035,wx-.055,.062)):
            panel(f'timber-flute-{i}',xx,xx+.025,.16,2.78,'oak',.052)
        entries=[]
        kinds={r['id']:r['kind'] for r in building['spaces']}
        for o in building['openings']:
            host=hosts[o['wall_id']]
            if o['floor']==0 and o['kind']=='door' and 'outside' in o['connects'] and any(kinds.get(i)=='hall' for i in o['connects']) and abs(host['a'][1]-w['a'][1])<1 and abs(host['b'][1]-w['a'][1])<1:
                ex=(min(host['a'][0],host['b'][0])+o['offset'])/1000
                if 0<ex-right<.7:entries.append((o,ex))
        if not entries:continue
        entry,ex=entries[0];er=ex+entry['width']/1000;eh=entry['height']/1000;end=er+.15
        panel('door-left-jamb',ex-.12,ex,.02,2.82,depth=.075)
        panel('door-right-jamb',er,end,.02,2.82,depth=.075)
        panel('door-transom',ex,er,eh,2.82,'walnut',.045)
        # One slim timber soffit unifies the high window and opaque timber door.
        k.rect((left-.035,face-.48,2.83,end+.04,face+.01,2.91),'frame',0,'canopy',owner+'/canopy',owner)
        k.rect((left-.01,face-.455,2.817,end+.015,face-.018,2.829),'oak',0,'canopy',owner+'/soffit',owner)
        k.rect((left+.07,face-.085,2.81,end-.07,face-.063,2.817),'lamp',0,'fixture',owner+'/warm-strip',owner)
        for i,xx in enumerate(((wx+wr)/2,(ex+er)/2)):
            k.cylinder((xx,face-.30,2.813),.035,.008,'lamp',0,'fixture')
            k.light((xx,face-.28,2.76),14,kind='porch')
        sx=(right+ex-.12)/2
        k.rect((sx-.038,face-.105,1.48,sx+.038,face-.035,1.79),'frame',0,'fixture',owner+'/wall-light',owner)
        k.rect((sx-.023,face-.111,1.53,sx+.023,face-.106,1.74),'lamp',0,'fixture',owner+'/wall-light-glow',owner)
        k.light((sx,face-.19,1.65),10,kind='porch')


def daylight_veranda(k, materials, building, room, height):
    """Low planting beneath a real slab cut, with perimeter drainage and a clear route."""
    owner=room['id'];f=room['floor'];z=f*height
    bed=box(*(np.array(room['gardenBed'])/1000));x0,y0,x1,y1=bed.bounds
    # Keep roots/soil below a flush stone edge; grass and foliage are actual geometry.
    k.poly_mesh(bed,z+.018,z+.024,'soil',f,'landscape',owner+'/garden-soil',owner)
    lawn=bed.buffer(-.07,join_style=2)
    k.poly_mesh(lawn,z+.025,z+.030,'lawn',f,'lawn',owner+'/garden-grass',owner)
    k.poly_mesh(bed.difference(lawn),z+.018,z+.025,'stone',f,'landscape',owner+'/flush-edge',owner)
    for i,(xx,yy,species,h,r) in enumerate([(x1-.28,y1-.25,'strelitzia',1.35,.18),(x1-.27,y0+.25,'monstera',.68,.16)]):
        k.plant(xx,yy,z+.025,species,height=h,f=f,pot=(r,.30,'planter'))
    for xx in (x0+.35,x0+1.05):
        k.plant(xx,y1-.20,z+.028,'grass_ornamental',height=.28,f=f)
    for i,xx in enumerate((x0+.35,x1-.38)):
        k.rect((xx-.03,y1-.12,z+.04,xx+.03,y1-.06,z+.23),'frame',f,'fixture',owner+f'/garden-light-{i}',owner)
        k.rect((xx-.025,y1-.125,z+.17,xx+.025,y1-.12,z+.215),'lamp',f,'fixture',owner+f'/garden-glow-{i}',owner)
        k.light((xx,y1-.16,z+.19),6,kind='garden')
    # Ground catch drain and terrace collector discharge down a visible boundary pipe.
    k.rect((x1-.14,y0+.40,z+.027,x1-.04,y0+.60,z+.033),'steel',f,'drain',owner+'/bed-drain',owner)
    for j in range(6):
        yy=y0+.415+j*.03
        k.rect((x1-.135,yy,z+.034,x1-.045,yy+.008,z+.037),'frame',f,'drain',owner+f'/drain-slot-{j}',owner)
    sky=next(s for s in building['spaces'] if s.get('openToSky') and s['floor']==f+1 and Polygon(np.array(s['clear'])/1000).intersects(bed))
    hole=Polygon(np.array(sky['clear'])/1000);a,b,c,d=hole.bounds;top=z+height
    # A 100 mm waterproofing curb sits OUTSIDE the aperture; no opaque cap spans it.
    ring=hole.buffer(.07,join_style=2).difference(hole)
    k.poly_mesh(ring,top,top+.10,'stone',f+1,'drain',sky['id']+'/waterproof-curb',sky['id'])
    channel=hole.buffer(.115,join_style=2).difference(hole.buffer(.075,join_style=2))
    # Restrict collector to the supported deck, not the open-to-below area.
    from .plan_geometry import geometry
    deck=geometry(building['floor_plates'][f+1]['regions'])
    from shapely.affinity import scale
    channel=channel.intersection(scale(deck,xfact=.001,yfact=.001,origin=(0,0)))
    k.poly_mesh(channel,top+.006,top+.013,'steel',f+1,'drain',sky['id']+'/collection-channel',sky['id'])
    # Concealed-under-deck collector run, plus an accessible downpipe on the boundary.
    k.rect((c+.08,y0+.11,top-.115,x1-.10,y0+.17,top-.055),'frame',f,'drain',owner+'/collector-run',owner)
    k.cylinder((x1-.10,y0+.14,z+(height-.075)/2+.02),.035,height-.075,'frame',f,'drain')
    # Warm soffit lights are on the covered route, away from the daylight aperture.
    rx0,ry0,rx1,ry1=Polygon(np.array(room['clear'])/1000).bounds
    for xx in np.linspace(rx0+.85,rx1-.54,3):
        yy=ry0+.38
        k.cylinder((xx,yy,top-.215),.035,.012,'lamp',f,'fixture')
        k.light((xx,yy,top-.25),10,kind='porch')
    return [{'id':owner+'/garden-grass','polygon':[list(q) for q in list(lawn.exterior.coords)[:-1]],'holes':[],'z':z+.030,'heightScale':.27}]
