"""User-requested G+1 addition to the locked P11/P12 ground plans.

All coordinates remain metric and the plot/ground rooms are untouched. Upper
rooms, terrace and the open-to-below gallery share one geometry definition for
the editor, dimensioned drawings, exported model and walking collision.
"""
from copy import deepcopy
import math
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union

REVISION = 'luxury-g1-2026-10-30'
JOINERY_REVISION = 'ivory-teak-wood-front-glass-behind-v2'
H = 3508.0
# Increase glazing vertically within the existing wall spans, preserving every
# room and opening position. Kitchen sill stays above its worktop.
GROUND_PICTURE_WINDOWS = {
    'master-rear': (600, 2250),
    'drawing-north': (450, 2400),
    'caregiver-north': (750, 2100),
    'caregiver-rear': (750, 2100),
    'kitchen-east': (950, 1900),
    'icu-veranda-window': (450, 2400),
    'icu-east-window': (450, 2400),
    'icu-north-window': (450, 2400),
}
PALETTES = {
    'ivory-teak': {'name':'Ivory · limestone · teak', 'wall':'#f1efea', 'stone':'#c3b6a1',
                   'floor':'#ede7dc', 'wood':'#79543c', 'frame':'#282928'},
    'pearl-walnut': {'name':'Pearl · greige · walnut', 'wall':'#eeece7', 'stone':'#afa99f',
                    'floor':'#e7e3dc', 'wood':'#624b3d', 'frame':'#252a2d'},
    'sand-bronze': {'name':'Soft sand · bronze · oak', 'wall':'#ede7dc', 'stone':'#c5b89e',
                   'floor':'#e8dfcf', 'wood':'#9b7957', 'frame':'#50443a'},
}


def ring(p):
    return [[round(float(x),4),round(float(y),4)] for x,y in list(p.exterior.coords)[:-1]]


def regions(p):
    return [{'polygon':ring(q),'holes':[ring(Polygon(r)) for r in q.interiors]}
            for q in ([p] if p.geom_type == 'Polygon' else p.geoms) if q.geom_type == 'Polygon' and q.area > 1]


def upper_plan(ground):
    rooms = {r['id']:r for r in ground['rooms']}
    def poly(ident):
        r=rooms[ident]['regions'][0]
        return Polygon(r['outer'],r.get('holes',[]))
    definitions=[
        ('u-master','bedroom','Upper master suite',poly('g-bedroom')),
        ('u-master-bath','bathroom','Master ensuite',poly('g-bath')),
        ('u-study','study','Office / study',poly('g-caregiver')),
        ('u-bedroom','bedroom','Guest bedroom',poly('g-drawing')),
        ('u-bath','bathroom','Shared bathroom',poly('g-caregiver-bath')),
    ]
    lightwell=poly('g-care-court').buffer(150,join_style=2)
    # A 1.9 m gallery overlooks a genuine 5.05 x 3 m living/dining void.
    gallery=unary_union([box(5150,7800,8200,8900),box(6300,4800,8200,7800),
                        box(6650,8900,8200,12450),box(5485.6,8900,6650,10050)]).difference(lightwell)
    gallery=gallery.difference(unary_union([r[3].buffer(150,join_style=2) for r in definitions]))
    void=box(1250,4875,6300,7800)
    stair_void=unary_union([box(150,5000,1250,8900),box(1250,7800,5150,8900)])
    # Terrace covers supported ground-floor roofs, not the parking forecourt.
    ground_roof=unary_union([poly(r) for r in rooms if r not in ('g-care-court','g-wash-gully')]+
        [box(*wr) for wr in ground['wallRects']]+
        [LineString([o['a'],o['b']]).buffer(75,cap_style=2) for o in ground['openings']]+
        [Polygon(r['outer'],r.get('holes',[])) for r in ground['openFloor']])
    terrace=ground_roof.intersection(unary_union([box(1216.8,1524,11582.4,8050), box(0,1524,1216.8,4800)]) if ground.get("utilityPlan")=="forecourt" else box(1216.8,1524,11582.4,8050)).difference(
        unary_union([gallery,void,stair_void,box(0,4800,6300,7800)]))
    # Fill small former furniture exclusions, never courtyard/structural voids.
    terrace=unary_union([Polygon(q.exterior) for q in ([terrace] if terrace.geom_type=='Polygon' else terrace.geoms) if q.geom_type=='Polygon'])
    definitions += [('u-gallery','hall','Gallery overlooking living',gallery),
                    ('u-terrace','terrace','Open garden terrace',terrace)]
    out=[]
    for ident,kind,name,p in definitions:
        out.append({'id':ident,'kind':kind,'name':name,'regions':regions(p),
                    'polygon':ring(p if p.geom_type=='Polygon' else max(p.geoms,key=lambda x:x.area)),
                    'area_m2':p.area/1e6,'bounds':list(p.bounds)})
    # Only the enclosed rear rooms, gallery and atrium receive an upper roof.
    roof=unary_union([box(0,8900,11582.4,14478),box(0,4800,8350,8900)]).difference(lightwell)
    return {'revision':REVISION,'rooms':out,'void':ring(void),'stairVoid':regions(stair_void),
            'lightwell':ring(lightwell),'lightwellClear':ring(poly('g-care-court')),'roof':regions(roof),'levelMm':H,
            'connectorSteps':[{'bounds':[4550,7800,4850,8900],'top':3329},
                              {'bounds':[4850,7800,5150,8900],'top':3508}]}


def project_addition(project):
    cp=project['customPlan']; up=upper_plan(cp['canonicalPlan'])
    cp['luxuryRevision']=REVISION; cp['upperPlan']=up
    cp['joineryRevision']=JOINERY_REVISION
    cp['finishSelection']={'palette':'ivory-teak','status':'user-approved'}
    cp['floors'].append({'id':'floor-1','rooms':[{'id':r['id'],'kind':r['kind'],
        'name':r['name'],'polygon':r['polygon']} for r in up['rooms']], 'walls':[], 'openings':[]})
    project['editorState']['customPlan']=deepcopy(cp)
    project['brief'].update(storeys=2,bedrooms=4,roof_access=False)
    project['notes'] += (' G+1 revision: upper master above the ground master, office, guest bedroom, '
        'open terrace and gallery above double-height living. Ground dimensions retained. '
        'ICU entrance has hall-side wooden privacy doors with sliding glass directly behind them. '
        'User-approved Ivory/limestone/teak palette; tall picture glazing with sliding side vents.')
    return project


def compile_addition(b):
    up=upper_plan(b['planning']['canonicalPlan']); b['planning']['upperPlan']=up
    b['planning']['luxuryRevision']=REVISION
    b['planning']['joineryRevision']=JOINERY_REVISION
    b['planning']['finishSelection']={'palette':'ivory-teak','status':'user-approved'}
    b['storeys']=2; b['brief']['storeys']=2
    b['floors'].append({'id':'floor-1','index':1})
    for r in up['rooms']:
        b['spaces'].append({'id':r['id'],'name':r['name'],'kind':r['kind'],'floor':1,'floorId':'floor-1',
            'polygon':r['polygon'],'clear':r['polygon'],'holes':r['regions'][0]['holes'],
            'regions':r['regions'],'bounds':r['bounds'],'area_m2':r['area_m2'],
            'areaSqFt':r['area_m2']/0.09290304,'elevation_mm':H,'walkable':True,
            'enclosed':r['kind']!='terrace','roofed':r['kind']!='terrace','wet':r['kind']=='bathroom'})
    b['stairs'][0]['to_floor']=1
    b['stairs'][0]['arrival_connector']=deepcopy(up['connectorSteps'])
    b['stairs'][0]['total_risers_to_first']=20
    b['stairs'][0]['arrival_elevation_mm']=H
    b['shafts'][0]['floors']=[0,1]
    b['shafts'].append({'id':'living-double-height','kind':'open-to-below', 'polygon':up['void'],'floors':[0,1]})

    # Masonry follows existing rear load lines; lightwell stays open through both floors.
    solids=[]
    for r in up['rooms']:
        if r['kind'] in ('hall','terrace'):continue
        p=Polygon(r['polygon']); solids.append(p.buffer(150,join_style=2).difference(p))
    gallery_enclosure=unary_union([box(6250,4725,8350,4875),box(8200,4800,8350,8125),
        box(0,4800,150,8900),box(150,4725,6300,4875)])
    solids.append(gallery_enclosure)
    lw=Polygon(up['lightwellClear'])
    solids.append(lw.buffer(150,join_style=2).difference(lw))
    wall_shape=unary_union(solids)
    # a,b are at wall centre; clear openings are preserved across the full wall thickness.
    defs=[
        ('u-master-door',[5650,8975],[6450,8975],'door',0,2450,['u-gallery','u-master']),
        ('u-master-bath-door',[3515.766667,12700],[3515.766667,13600],'door',0,2300,['u-master','u-master-bath']),
        ('u-office-door',[8275,11600],[8275,12500],'door',0,2450,['u-gallery','u-study']),
        ('u-bedroom-door',[8275,8500],[8275,9400],'door',0,2450,['u-gallery','u-bedroom']),
        ('u-bath-door',[7200,12525],[8100,12525],'door',0,2300,['u-gallery','u-bath']),
        ('u-terrace-door',[6500,4800],[8100,4800],'sliding-door',0,2700,['u-gallery','u-terrace']),
        ('u-side-terrace-door',[8275,6500],[8275,7900],'sliding-door',0,2700,['u-gallery','u-terrace']),
        ('u-master-rear',[650,14403],[2850,14403],'window',450,2500,['u-master','outside']),
        ('u-master-south',[75,10100],[75,11800],'window',450,2500,['u-master','outside']),
        ('u-office-rear',[8750,14403],[11000,14403],'window',450,2500,['u-study','outside']),
        ('u-office-north',[11507.4,12400],[11507.4,13900],'window',450,2500,['u-study','outside']),
        ('u-bedroom-north',[11507.4,9100],[11507.4,11000],'window',450,2500,['u-bedroom','outside']),
        ('u-bedroom-terrace',[8750,8125],[11000,8125],'window',400,2550,['u-bedroom','u-terrace']),
        ('u-bath-rear',[6600,14403],[7750,14403],'window',1700,1000,['u-bath','outside']),
        ('u-ensuite-rear',[4100,14403],[5350,14403],'window',1700,1000,['u-master-bath','outside']),
        ('u-gallery-lightwell',[7210.6,10450],[7210.6,11650],'window',900,1800,['u-gallery','outside']),
        ('u-master-lightwell',[5560.6,10600],[5560.6,11400],'window',900,1800,['u-master','outside']),
        ('u-atrium-east',[1800,4800],[5700,4800],'window',150,2900,['u-gallery','u-terrace']),
        ('u-atrium-south',[75,5450],[75,7300],'window',150,2900,['u-gallery','outside']),
    ]
    openings=[]
    for ident,a,c,kind,sill,height,connects in defs:
        width=math.dist(a,c); cut=LineString([a,c]).buffer(90,cap_style=2)
        wall_shape=wall_shape.difference(cut)
        w={'id':'host-'+ident,'floor':1,'floorId':'floor-1','a':a,'b':c,'start':a,'end':c,
           'polygon':ring(LineString([a,c]).buffer(75,cap_style=2)),'thickness':150,'height':H,
           'rooms':[s for s in connects if s!='outside'],'external':'outside' in connects or 'u-terrace' in connects,
           'structural':False,'hostOnly':True}
        b['walls'].append(w)
        op={'id':ident,'floor':1,'floorId':'floor-1','wall':w['id'],'wall_id':w['id'],
            'a':a,'b':c,'kind':'window' if sill else 'door','raw_kind':kind,'sill':sill,'height':height,
            'width':width,'offset':0,'connects':connects,'hinge':'a','elevation_mm':H}
        if ident=='u-master-door':op.update(hinge='b',swing_vec=[c[0],c[1]+width])
        if ident in ('u-office-door','u-bedroom-door'):op['swing_vec']=[a[0]+width,a[1]]
        if kind=='window' and height>=2400:
            op['window_style']='picture-with-sliding-vents'
        openings.append(op)
    b['openings']+=openings
    for i,reg in enumerate(regions(wall_shape)):
        p=Polygon(reg['polygon'],reg['holes']);a=list(p.exterior.coords)[0];c=list(p.exterior.coords)[1]
        b['walls'].append({'id':f'u-wall-{i}','floor':1,'floorId':'floor-1','a':list(a),'b':list(c),
            'start':list(a),'end':list(c),'polygon':reg['polygon'],'holes':reg['holes'],'thickness':150,
            'height':H,'rooms':[],'external':True,'structural':True})
    up['wallRegions']=regions(wall_shape)
    thresholds=[LineString([o['a'],o['b']]).buffer(90,cap_style=2) for o in openings if o['sill']==0]
    plate=unary_union([Polygon(r['polygon'],r['holes']) for rm in up['rooms'] for r in rm['regions']]+[wall_shape]+thresholds)
    up['floorPlate']=regions(plate)
    b['floor_plates'].append({'id':'plate-floor-1','floor':1,'floorId':'floor-1','regions':regions(plate),
        'outline':regions(plate),'slab':ring(plate if plate.geom_type=='Polygon' else max(plate.geoms,key=lambda p:p.area)),
        'holes':[],'thickness':180,'elevation':H,'openings':[up['void'],up['lightwell']]})
    b['roofs']=[{'id':'roof-floor-0','floor':0,'regions':up['floorPlate'],'ceiling':up['floorPlate'],
        'slab':up['floorPlate'][0]['polygon'],'holes':up['floorPlate'][0]['holes'],
        'elevation':H,'thickness':180,'parapet_height':0},
        {'id':'roof-floor-1','floor':1,'regions':up['roof'],'ceiling':up['roof'],
        'slab':up['roof'][0]['polygon'],'holes':up['roof'][0]['holes'],'elevation':H*2,
        'thickness':180,'parapet_height':450}]
    return b


def validate_addition(b):
    """Check upper spaces and floor voids using their actual geometry."""
    up=b['planning'].get('upperPlan',{});expected={'u-master','u-master-bath','u-study','u-bedroom','u-bath','u-gallery','u-terrace'}
    rooms={r['id']:unary_union([Polygon(reg['polygon'],reg['holes']) for reg in r['regions']]) for r in up.get('rooms',[])}
    actual={r['id']:Polygon(r['clear'],r.get('holes',[])) for r in b['spaces'] if r['floor']==1}
    shapes_ok=set(rooms)==expected and all(p.is_valid and p.area>1e6 and p.difference(Polygon(b['plot'])).area<1 for p in rooms.values())
    overlaps=any(a.intersection(c).area>1 for aid,a in rooms.items() for cid,c in rooms.items() if aid<cid)
    same=all(ident in actual and p.symmetric_difference(actual[ident]).area<1 for ident,p in rooms.items())
    slab=unary_union([Polygon(r['polygon'],r['holes']) for r in up.get('floorPlate',[])])
    void=Polygon(up.get('void',[]));lw=Polygon(up.get('lightwellClear',[]))
    return [
        {'id':'upper_floor_rooms_and_dimensions','category':'geometry','status':'pass' if shapes_ok and same and not overlaps else 'fail',
         'detail':'Upper master, study, guest bedroom, baths, gallery and terrace fit the plot without overlaps.'},
        {'id':'double_height_and_lightwell_open','category':'geometry','status':'pass' if slab.intersection(void.buffer(-1)).area<1 and slab.intersection(lw.buffer(-1)).area<1 else 'fail',
         'detail':'First-floor slab leaves living/dining and the lightwell open.'},
        {'id':'stair_arrival_matches_upper_level','category':'circulation','status':'pass' if b['stairs'][0].get('arrival_elevation_mm')==H and b['stairs'][0].get('total_risers_to_first')==20 else 'fail',
         'detail':'18 approved risers plus two 179 mm arrival risers reach the 3508 mm first floor.'},
    ]


def luxury_materials(mats, selection='ivory-teak'):
    p=PALETTES[selection]
    mats['wall']['color']=p['wall'];mats['frame']['color']=p['frame'];mats['roof']['color']='#eeece6'
    for ident in ('ivory-marble-polished','ivory-marble-exterior-matte','ivory-marble-satin-wet'):
        mats[ident].update(color=p['floor'],alt='#cfc8bb',tile_m=[2.4384,1.2192],normal=.18)
        mats[ident]['params']=[2,.0017,.13,.7 if ident.endswith('polished') else .18]
    mats['teak-warm'].update(color=p['wood'],alt='#65503e',roughness=.38)
    mats['oak-warm'].update(color='#ab9173',alt='#8d765d',roughness=.46)
    mats['limestone']={'color':p['stone'],'alt':'#b1a48f','kind':'stone','roughness':.73,'normal':.3,'tile_m':[1.8,.6]}
    mats['terrace-stone']={'color':'#d4c9b4','alt':'#c0b49e','kind':'tile','params':[2,.002,.06,.2],
                           'tile_m':[2.4,1.2],'roughness':.65,'normal':.2}
    mats['grass'].update(color='#527348',alt='#87976b')
    mats['cladding']={**mats['limestone']}
    mats['brass']['color']='#a88e5c'
    mats['railglass'].update(color='#dce5df',alpha=.13,roughness=.05,metallic=.05)
    mats['glass'].update(color='#d4e0df',alpha=.17)


def add_scene(k,mats,b,door_motion,lawns):
    """Draw first floor plus finishes; ground-floor joinery and rooms are already present."""
    from .tirumala_openings import build_opening,pose_initial_opening
    up=b['planning']['upperPlan']; z=H/1000; top=2*z
    def p(reg):return Polygon([(x/1000,y/1000) for x,y in reg['polygon']],
                              [[(x/1000,y/1000) for x,y in h] for h in reg.get('holes',[])])
    for i,reg in enumerate(up['floorPlate']):
        k.poly_mesh(p(reg),z-.18,z-.014,'slab',1,'slab',f'upper-slab-{i}')
        k.poly_mesh(p(reg),z-.014,z,'ivory-marble-polished',1,'floor',f'upper-floor-{i}')
        k.poly_mesh(p(reg),z-.193,z-.183,'ceiling',0,'ceiling',f'ground-ceiling-under-upper-{i}')
    for i,reg in enumerate(up['wallRegions']):
        k.poly_mesh(p(reg),z,top,'wall',1,'wall',f'upper-wall-{i}')
    for i,st in enumerate(up['connectorSteps']):
        x0,y0,x1,y1=[v/1000 for v in st['bounds']]; zz=st['top']/1000
        k.rect((x0,y0,3.15,x1,y1,zz-.022),'wall',0,'stair',f'arrival-connector-{i}')
        k.rect((x0,y0,zz-.022,x1,y1,zz),'teak-warm',0,'stair',f'arrival-connector-tread-{i}')
    # Upper openings have elevation-aware poses and share the tested controller.
    for op in (o for o in b['openings'] if o['floor']==1):
        ax,ay=[v/1000 for v in op['a']];bx,by=[v/1000 for v in op['b']]
        length=math.hypot(bx-ax,by-ay);ux,uy=(bx-ax)/length,(by-ay)/length;nx,ny=-uy,ux
        def span(a,c,d,e,lo,hi,mat,role,name):
            poly=Polygon([(ax+ux*a+nx*d,ay+uy*a+ny*d),(ax+ux*c+nx*d,ay+uy*c+ny*d),
                          (ax+ux*c+nx*e,ay+uy*c+ny*e),(ax+ux*a+nx*e,ay+uy*a+ny*e)])
            k.poly_mesh(poly,z+lo,z+hi,mat,1,role,'op-'+op['id']+'-'+name,owner=op['id'])
        sill=op['sill']/1000;t=(op['sill']+op['height'])/1000
        if sill:span(0,length,-.075,.075,0,sill,'wall','wall','sill')
        span(0,length,-.075,.075,t,z,'wall','wall','lintel')
        for a,c,lo,hi in [(0,.045,sill,t),(length-.045,length,sill,t),(0,length,t-.045,t)]:
            span(a,c,-.055,.055,lo,hi,'frame','frame','jamb-'+str(a)+'-'+str(lo))
        if sill:span(0,length,-.055,.055,sill,sill+.045,'frame','frame','bottom')
        motion=build_opening(k,op,b['planning']['canonicalPlan'],span)
        for part in motion.get('parts',[]):
            if 'pivot' in part:part['pivot'][2]+=z
        if op['sill']==0:motion['initial']=1
        door_motion[op['id']]=motion;pose_initial_opening(k,motion)

    # Glass gallery balustrades terminate before the stair arrival: no barrier across the route.
    guard_segments=[((6.30,4.9),(6.30,7.8)),((5.15,7.8),(6.30,7.8)),
                    ((4.55,7.8),(5.15,7.8)),((4.55,8.9),(5.15,8.9))]
    for i,(a,c) in enumerate(guard_segments):
        strip=LineString([a,c]).buffer(.012,cap_style=2)
        k.poly_mesh(strip,z+.08,z+1.08,'railglass',1,'railing',f'gallery-glass-{i}')
        k.beam((*a,z+1.10),(*c,z+1.10),.018,'frame',1,'railing')
    # Upper roof has broad ivory fascia / timber soffits, referencing My Desired Home.
    roof=unary_union([p(r) for r in up['roof']])
    over=roof.buffer(.32,join_style=2).intersection(box(.0,4.45,11.9,14.80))
    lw=Polygon([(x/1000,y/1000) for x,y in up['lightwell']]);over=over.difference(lw)
    k.poly_mesh(roof,top,top+.18,'roof',1,'roof','upper-roof-slab')
    k.poly_mesh(roof,top-.025,top-.005,'ceiling',1,'ceiling','upper-ceiling')
    k.poly_mesh(over.difference(roof),top-.075,top+.16,'wall',1,'roof','ivory-floating-roof-edge')
    k.poly_mesh(over.difference(roof),top-.085,top-.075,'teak-warm',1,'soffit','timber-roof-soffit')
    edge=over.difference(over.buffer(-.025,join_style=2))
    k.poly_mesh(edge,top+.11,top+.17,'frame',1,'canopy','thin-charcoal-roof-trim')
    # Ground-floor atrium side wall / roof void have one tall window above the original opening.
    k.poly_mesh(LineString([(0.15,4.925),(1.25,4.925)]).buffer(.065,cap_style=2),z,top,'wall',1,'wall','atrium-stair-return')

    terrace=unary_union([p(reg) for r in up['rooms'] if r['id']=='u-terrace' for reg in r['regions']])
    k.poly_mesh(terrace,z+.001,z+.016,'terrace-stone',1,'terrace','open-terrace-finish')
    # Only exposed perimeter edges get a guard; gallery doors have no barrier.
    enclosed=unary_union([p(reg) for r in up['rooms'] if r['kind']!='terrace' for reg in r['regions']])
    walls=unary_union([p(reg) for reg in up['wallRegions']])
    # Guard every exposed terrace edge, including the store/wash-side return.
    edge_lines=terrace.boundary.difference(enclosed.buffer(.16)).difference(walls.buffer(.04))
    for i,line in enumerate(getattr(edge_lines,'geoms',[edge_lines])):
        if line.geom_type!='LineString' or line.length<.15:continue
        pts=list(line.coords)
        for j,(a,c) in enumerate(zip(pts,pts[1:])):
            k.poly_mesh(LineString([a,c]).buffer(.016,cap_style=2),z+.12,z+1.10,'railglass',1,'railing',f'terrace-guard-{i}-{j}')
            k.beam((*a,z+1.12),(*c,z+1.12),.022,'frame',1,'railing')
    # Opening the low-sill atrium glazing must never expose a drop into the living room.
    k.poly_mesh(LineString([(1.8,4.8),(5.7,4.8)]).buffer(.012,cap_style=2),z+.04,z+1.10,
                'railglass',1,'railing','atrium-window-permanent-guard')
    # A light timber pergola and built-in lounge on the south/east terrace, clear of access.
    for x,y in [(2.55,1.85),(5.35,1.85),(2.55,4.35),(5.35,4.35)]:
        k.rect((x-.045,y-.045,z,x+.045,y+.045,z+2.7),'frame',1,'pergola',f'pergola-post-{x}-{y}')
    for i in range(16):
        y=1.80+i*.175
        k.rect((2.45,y,z+2.7,5.45,y+.06,z+2.82),'teak-warm',1,'pergola',f'pergola-slat-{i}')
    k.rb((3.85,2.35,z+.38),(2.10,.75,.32),'fabric',1,'furniture',.08)
    k.rb((3.85,2.05,z+.70),(2.10,.16,.55),'linen',1,'furniture',.05)
    k.rb((3.85,3.35,z+.42),(1.10,.60,.06),'limestone',1,'furniture',.03)
    k.rect((3.47,3.17,z,4.23,3.53,z+.39),'teak-warm',1,'furniture','terrace-table-base')
    for x,y in [(2.65,4.05),(5.15,4.05)]:k.plant(x,y,z,'strelitzia',height=1.2,f=1,pot=(.20,.40,'ceramic-pot'))

    # Furnished upper rooms, with generous circulation around their real-size furniture.
    def bed(cx,cy,w,l):
        k.rb((cx,cy,z+.24),(w+.08,l+.08,.32),'oak-warm',1,'furniture',.05)
        k.rb((cx,cy,z+.48),(w,l,.23),'linen',1,'furniture',.09)
        k.rb((cx,cy+l/2+.08,z+.75),(w+.20,.14,1.05),'fabric',1,'furniture',.06)
        for xx in (cx-w/4,cx+w/4):k.rb((xx,cy+l*.30,z+.64),(w*.40,.42,.14),'linen',1,'furniture',.07)
        k.rb((cx,cy-l*.25,z+.61),(w+.02,l*.40,.04),'fabric-dark',1,'detail',.01)
    bed(2.10,11.40,1.9,2.05);bed(9.9,10.15,1.50,2.00)
    k.rect((.20,9.35,z,.78,11.35,z+2.65),'oak-warm',1,'furniture','upper-master-wardrobe')
    k.rect((8.50,12.95,z+.73,10.55,13.65,z+.78),'teak-warm',1,'furniture','office-desk')
    k.rb((9.55,12.45,z+.48),(.6,.60,.12),'fabric',1,'furniture',.04)
    k.rect((9.15,13.12,z+.78,9.85,13.22,z+1.20),'frame',1,'detail','office-display')
    for y in [11.8,12.8,13.8]:
        k.rect((10.95,y,z+.15,11.35,y+.75,z+2.20),'oak-warm',1,'furniture','office-shelf-'+str(y))
    for cx,cy in [(4.7,13.9),(7.1,13.9)]:
        k.rb((cx,cy,z+.43),(.95,.5,.80),'oak-warm',1,'furniture',.02)
        k.rb((cx,cy,z+.85),(1,.55,.06),'counter',1,'furniture',.02)
        k.cylinder((cx,cy,z+.92),.20,.08,'ceramic',1,'detail')
        wcx=cx+.8 if cx<6 else 6.55
        k.rb((wcx,cy-.8,z+.24),(.42,.62,.43),'ceramic',1,'furniture',.08)

    # Restrained facade stone panels, double-height glazing and warm metal accents.
    for bounds in [(0.0,9.05,z,.03,10.0,top),(11.58,11.5,z,11.61,12.25,top)]:
        k.rect(bounds,'limestone',1,'cladding')
    # Timber veranda ceiling and thin eaves retain a bungalow-like sheltered character.
    veranda=next(r for r in b['spaces'] if r['id']=='g-veranda')
    vp=Polygon([(x/1000,y/1000) for x,y in veranda['clear']])
    k.poly_mesh(vp,z-.235,z-.210,'teak-warm',0,'soffit','veranda-timber-ceiling')
    vx0,vy0,vx1,vy1=vp.bounds
    for x in [vx0+.2,vx1-.2]:
        k.cylinder((x,vy0+.23,2.90),.07,.14,'lamp',0,'fixture')
        k.light((x,vy0+.23,2.78),12,color='#ffe6be',kind='veranda')
    # A shallow timber entry portal fits within the veranda edge and existing levels.
    k.rect((vx0,vy0-.035,z-.30,vx1,vy0+.045,z-.22),'teak-warm',0,'soffit','veranda-front-timber-beam')
    # Real blade grass and low planting in the fixed two-foot north strip.
    # 360 mm stepping pads preserve the existing narrow maintenance access.
    north=box(11.59,8.20,12.035,14.43)
    pads=unary_union([box(11.62,y,11.98,y+.50) for y in [8.25,8.95,9.65,10.35,11.05,11.75,12.45,13.15,13.85]])
    grass=north.difference(pads)
    k.poly_mesh(grass,-.04,-.018,'soil',0,'landscape','north-living-garden-soil')
    k.poly_mesh(grass,-.018,.002,'grass',0,'lawn','north-living-garden-turf')
    for reg in ([grass] if grass.geom_type=='Polygon' else grass.geoms):
        lawns.append({'polygon':ring(reg),'holes':[ring(Polygon(r)) for r in reg.interiors],
                      'z':.003,'heightScale':.45})
    k.poly_mesh(pads,-.015,.003,'terrace-stone',0,'court','north-stepping-pads')
    for y in [8.8,10.2,11.6,13.0,14.2]:
        k.plant(12.0,y,0,'grass_ornamental',height=.32,f=0)
        k.rect((12.035,y-.10,.18,12.045,y+.10,.28),'lamp',-1,'fixture','garden-edge-light-'+str(y))

    # An intentionally uncluttered double-height room with a suspended light cluster.
    for x,y,d in [(3.1,6.35,.0),(3.65,6.55,.30),(4.05,6.15,-.20)]:
        zz=4.30+d
        k.beam((x,y,zz),(x,y,top-.02),.006,'brass',1,'fixture')
        k.cylinder((x,y,zz),.18,.05,'brass',1,'fixture')
        k.cylinder((x,y,zz-.029),.16,.008,'lamp',1,'fixture')
    for x,y in [(2.5,11.4),(4.8,13.3),(7.3,13.3),(9.8,10),(9.8,13),(6.8,8.3),(7.2,5.6)]:
        k.cylinder((x,y,top-.05),.055,.015,'lamp',1,'fixture')
        k.light((x,y,top-.16),22,color='#ffe5c4',kind='upper-downlight')

    # Operable slatted entry gate, parked behind the existing front boundary.
    gx0,gx1=[v[0]/1000 for v in b['planning']['canonicalPlan']['gate']]
    mark=len(k.nodes)
    for zz in [.0,1.42]:
        k.poly_mesh(box(gx0,.22,gx1,.28),zz,zz+.08,'frame',-1,'gate','arrival-gate-rail-'+str(zz))
    for i in range(35):
        xx=gx0+i*(gx1-gx0)/35
        k.poly_mesh(box(xx,.235,xx+.055,.265),.08,1.42,'teak-warm',-1,'gate','arrival-gate-slat-'+str(i))
    motion={'parts':[{'ids':[n['id'] for n in k.nodes[mark:]],'slide':[-(gx1-gx0)-.12,0,0]}],'initial':1}
    pose_initial_opening(k,motion)
    return [{'id':'arrival-sliding-gate','floor':-1,'kind':'gate','label':'Timber and charcoal sliding gate',
             'start':[gx0,.25,0],'axis':[1,0,0],'width':gx1-gx0,'height':1.5,'base':0,'sill':0,
             'parts':motion['parts'],'initial':1}]


def cameras(b):
    z=H/1000
    defs={
        'upper_gallery':('Gallery · view down to living', [6.95,7.4,z+1.63],[3.6,6.1,1.6],68),
        'upper_master':('Upper master suite',[4.95,9.8,z+1.63],[1.8,12.0,z+1.4],66),
        'upper_office':('Study / office',[8.9,11.95,z+1.63],[10.1,13.4,z+1.4],64),
        'upper_guest':('Guest bedroom',[8.9,8.85,z+1.63],[10.1,10.2,z+1.35],66),
        'upper_terrace':('Open terrace · pergola & garden',[6.9,3.9,z+1.63],[3.4,2.8,z+1.0],68),
        'living_double_height':('Living · double-height gallery',[5.1,5.6,1.63],[6.8,8.1,4.6],68),
    }
    entry=next(o for o in b['openings'] if o['id']=='icu-glass-living')
    a,c=entry['a'],entry['b'];length=math.dist(a,c)
    n=[-(c[1]-a[1])/length,(c[0]-a[0])/length]
    mid=[(a[i]+c[i])/2000 for i in range(2)]
    defs['icu_layered_entry']=('ICU entrance · wood with glass behind',
        [mid[0]+n[0]*1.7,mid[1]+n[1]*1.7,1.63],[*mid,1.4],62)
    out={}
    for ident,(label,pos,target,fov) in defs.items():
        dx,dy,dz=[target[i]-pos[i] for i in range(3)]
        out[ident]={'id':ident,'label':label,'position':pos,'target':target,'fov':fov,
                    'floor':0 if ident in ('living_double_height','icu_layered_entry') else 1,'enter_walk':True,
                    'eye_height_above_ffl_m':1.63,'walker':{'position':pos[:],
                    'yaw_rad':math.atan2(-dx,dy),'pitch_rad':math.atan2(dz,math.hypot(dx,dy))}}
    return out


def upper_plan_elements(b):
    from .drawings import P,T,L,DIM
    from .tirumala_p11_p12 import _mm_to_ft_in
    up=b['planning']['upperPlan'];items=[]
    items.append(P(b['plot'],fill='#faf8f2',stroke='#bbb',width=.2,layer='A-SITE'))
    colors={'bedroom':'#f1e8da','bathroom':'#e7eceb','study':'#e9e4d7','hall':'#f6f0e4','terrace':'#e5eddd'}
    for rm in up['rooms']:
        for reg in rm['regions']:items.append(P(reg['polygon'],fill=colors[rm['kind']],stroke='#b8afa0',width=.2,layer='A-AREA'))
        poly=Polygon(rm['polygon']);pt=poly.representative_point();x0,y0,x1,y1=rm['bounds']
        items.append(T(pt.x,pt.y+150,rm['name'],190,layer='A-ANNO'))
        items.append(T(pt.x,pt.y-150,f'{_mm_to_ft_in(x1-x0)} × {_mm_to_ft_in(y1-y0)}',165,layer='A-ANNO'))
    items.append(P(up['void'],fill='#ffffff',stroke='#7a9b8d',width=.3,layer='A-VOID'))
    items.append(T(3700,6400,'OPEN TO LIVING BELOW',210,layer='A-ANNO'))
    items.append(T(3700,6050,'Double height · 23 ft overall',170,layer='A-ANNO'))
    for reg in up['wallRegions']:items.append(P(reg['polygon'],fill='#414844',stroke='none',width=.1,layer='A-WALL'))
    for o in (o for o in b['openings'] if o['floor']==1):
        items.append(L(o['a'],o['b'],stroke='#3e8e9e' if o['sill'] else '#9c6c42',width=.6,layer='A-DOOR'))
    items.append(T(3800,8300,'STAIR ↑ + 2 arrival steps',170,layer='A-ANNO'))
    items.append(DIM([0,15240],[12192,15240],'x',15550))
    items.append(DIM([0,0],[0,15240],'y',-300))
    return items,(-850,-450,12800,15900)


def upper_svg(b):
    """Readable portrait reference, in feet, from the same upper-floor polygons."""
    import html
    from .tirumala_p11_p12 import _mm_to_ft_in
    up=b['planning']['upperPlan']; scale=.066;left=84;top=105;depth=15240
    tx=lambda x:round(left+x*scale,2)
    ty=lambda y:round(top+(depth-y)*scale,2)
    pts=lambda r:' '.join(f'{tx(x)},{ty(y)}' for x,y in r)
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="980" height="1450" viewBox="0 0 980 1450">',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M10 1 L0 5 L10 9" fill="none" stroke="#657168"/></marker></defs>',
         '<rect width="980" height="1450" fill="#faf9f5"/><g font-family="Arial,sans-serif" fill="#253c34">',
         f'<text x="55" y="40" font-size="25" font-weight="700">{html.escape(b["brief"]["title"])} · First floor</text>',
         '<text x="55" y="66" font-size="14">40 × 50 ft plot · West ↑ · North → · Ground-room footprints retained</text>',
         f'<rect x="{tx(0)}" y="{ty(15240)}" width="{12192*scale}" height="{15240*scale}" fill="#f1efe7" stroke="#c7c4b8"/>']
    def text(x,y,s,size=13,weight=400):
        out.append(f'<text x="{tx(x)}" y="{ty(y)}" text-anchor="middle" font-size="{size}" font-weight="{weight}">{html.escape(s)}</text>')
    def dimension(x1,y1,x2,y2,label):
        a,c=tx(x1),ty(y1);d,e=tx(x2),ty(y2)
        out.append(f'<line x1="{a}" y1="{c}" x2="{d}" y2="{e}" stroke="#657168" stroke-width=".9" marker-start="url(#a)" marker-end="url(#a)"/>')
        angle=-90 if x1==x2 else 0
        out.append(f'<text x="{(a+d)/2}" y="{(c+e)/2-5}" transform="rotate({angle} {(a+d)/2} {(c+e)/2})" text-anchor="middle" font-size="12" stroke="#faf9f5" stroke-width="5" paint-order="stroke">{html.escape(label)}</text>')
    cols={'bedroom':'#e9dfd0','bathroom':'#dce6e3','study':'#e8e0c8','hall':'#f7f1e4','terrace':'#dbe7d3'}
    for r in up['rooms']:
        for reg in r['regions']:out.append(f'<polygon points="{pts(reg["polygon"])}" fill="{cols[r["kind"]]}" stroke="#cbc1b2"/>')
    out.append(f'<polygon points="{pts(up["void"])}" fill="#fff" stroke="#9aafa2" stroke-dasharray="7 5"/>')
    text(3700,6500,'OPEN TO LIVING / DINING',14,700);text(3700,6150,'23 ft double-height space',13)
    text(6400,11100,'LIGHTWELL',11);text(3650,8300,'Stairs ↑',12);text(4800,8300,'+2',11)
    for reg in up['wallRegions']:out.append(f'<polygon points="{pts(reg["polygon"])}" fill="#394942"/>')
    for o in (o for o in b['openings'] if o['floor']==1):
        out.append(f'<line x1="{tx(o["a"][0])}" y1="{ty(o["a"][1])}" x2="{tx(o["b"][0])}" y2="{ty(o["b"][1])}" stroke="{"#57919c" if o["sill"] else "#aa794b"}" stroke-width="3"/>')
    for r in up['rooms']:
        x0,y0,x1,y1=r['bounds'];poly=Polygon(r['polygon']);pt=poly.representative_point()
        if r['id']=='u-master':cx,cy=2600,11100
        elif r['id']=='u-gallery':cx,cy=7250,6950
        elif r['id']=='u-terrace':cx,cy=6000,2800
        else:cx,cy=pt.x,pt.y
        text(cx,cy+250,r['name'],13,700)
        text(cx,cy-40,f'{r["area_m2"]/.09290304:.0f} sq ft',12)
        if r['kind'] not in ('hall','terrace'):
            dimension(x0+80,y0+350,x1-80,y0+350,_mm_to_ft_in(x1-x0))
            dimension(x1-170,y0+80,x1-170,y1-80,_mm_to_ft_in(y1-y0))
    dimension(0,15600,12192,15600,'40 ft');dimension(-450,0,-450,15240,'50 ft')
    text(6100,-450,'EAST · arrival below',14,700)
    out.append('<text x="55" y="1185" font-size="16" font-weight="700">Connected upper floor</text>')
    for i,line in enumerate(['Master suite directly above ground master; ensuite follows existing wet wall.',
                             'Office + guest bedroom; shared bath accessed from the gallery.',
                             'Gallery overlooks living. Open terrace is on this same first-floor level.',
                             'Existing 18 stair risers retained + two 179 mm arrival risers to +3.508 m.',
                             'Room dimensions are bounding spans; irregular rooms use polygon area.',
                             'Concept layout — structural support and local approvals require design review.']):
        out.append(f'<text x="55" y="{1215+i*27}" font-size="13">{html.escape(line)}</text>')
    out.append('</g></svg>')
    return ''.join(out)
