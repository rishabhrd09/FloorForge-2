"""Tirumala 5: owner-selected Plan A, derived from the delivered Tirumala 4.

Coordinates are millimetres, +x north and +y west. Presentation is inherited;
the editable plan, compiled geometry, drawings and walkthrough use this one plan.
"""
from copy import deepcopy
import json
import math
from pathlib import Path

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
REVISION = 'tirumala-5-indoor-stair-revision-2026-11-05'
KITCHEN = [150, 1674, 4160, 4800]
ICU = [4310, 1674, 8882, 5759.6]
UTILITY = [150, 150, 2283.6, 1521.6]
PANTRY = [2000, 8290, 3371.6, 8899.6]
PANTRY_AISLE = [2000, 7375.6, 3371.6, 8290]


def ground_revision(plan):
    """Apply the approved doorway, corner closure and recliner proposal only."""
    removed = {(7200,5759.6,7502.4,5909.6), (7200,5909.6,7275,5924.6),
               (7125,5924.6,7275,6100), (7125,7900,7275,8050),
               (4160,5759.6,5602.4,5909.6)}
    plan['wallRects'] = [r for r in plan['wallRects'] if tuple(r) not in removed]
    plan['wallRects'] += [[7225,5909.6,7375,6100], [7225,7900,7375,8050],
        [4160,5759.6,5452.4,5909.6], [7050,5759.6,7502.4,5909.6],
        [7225,8050,8200,8200]]
    for opening in plan['openings']:
        dx = 100 if opening['id']=='living-veranda' else -150 if opening['id']=='icu-glass-living' else 0
        if dx:
            for key in ('a','b','swing'):
                if key in opening: opening[key][0] += dx
    for key in ('woodStacks','meshStacks'):
        for b in plan['entrance'][key]: b[0] += 100; b[2] += 100
    for p in plan['glass']['path']: p[0] -= 150
    for key in ('stackBounds',):
        b=plan['glass'][key]; b[0] -= 150; b[2] -= 150
    if plan.get('stack'):
        # The canonical stack is a polygon; the detail metadata above is bounds.
        for p in plan['stack']: p[0] -= 150
    veranda=next(r for r in plan['rooms'] if r['id']=='g-veranda')
    poly=Polygon([[7375 if x==7275 else x,y] for x,y in veranda['regions'][0]['outer']])
    veranda.update(bounds=list(poly.bounds),regions=regions(poly),areaSqFt=round(poly.area/92903.04,1))
    floor=unary_union([Polygon(r['outer'],r.get('holes',[])) for r in plan['openFloor']])
    floor=floor.union(box(7125,5909.6,7225,8050)).union(box(7225,6100,7375,7900))
    # Incorporate the existing compiled lobby floor repair into the editable plan.
    floor=floor.union(box(6650,8200,8200,9600)).difference(unary_union([box(*r) for r in plan['wallRects']]))
    plan['openFloor']=regions(floor)
    for f in plan['furniture']:
        if f['room_id']=='g-care' and f['kind']=='reclining-bed':
            f.update(bounds=[5767.6,3204.8,7967.6,4304.8],headDirection='South',feetDirection='North')
            f['polygon']=ring(box(*f['bounds']))
        elif f['room_id']=='g-care' and f['kind'].startswith('care-chair'):
            f['bounds']=[4927.6,3409.6,5467.6,3969.6]; f['polygon']=ring(box(*f['bounds']))
        elif f['id']=='g-living/coffee-table':
            # Open the passage between the lounge and dining/stair approach.
            # The former 400 mm sofa/table gap trapped the walking capsule.
            f['bounds']=[4550,6600,5050,7200]; f['polygon']=ring(box(*f['bounds']))
    plan['utilityPrivacy']=dict(southRectMm=[0,150,148,1521.6],eastRectMm=[150,0,2283.6,150],
        heightMm=1800,southFinish='opaque ivory',eastFinish='ventilated teak-look slats',access='north side open')
    plan['groundRevision']=dict(extraCornerClosed=True,livingDoorNorthShiftMm=100,
        icuLivingDoorSouthShiftMm=150,icuFootAisleMm=914.4,retainedRearLobbyDoor='lobby-open-entry',
        livingCoffeeTableEastShiftMm=400)


def ring(poly):
    return [[round(float(x), 4), round(float(y), 4)] for x,y in list(poly.exterior.coords)[:-1]]


def regions(poly):
    parts = [poly] if poly.geom_type == 'Polygon' else list(poly.geoms)
    return [dict(outer=ring(p), holes=[ring(Polygon(h)) for h in p.interiors])
            for p in sorted(parts, key=lambda p: -p.area) if p.geom_type == 'Polygon' and p.area > 1]


def set_room(room, bounds, name=None):
    p=box(*bounds)
    room.update(bounds=bounds[:], regions=regions(p), areaSqFt=round(p.area/92903.04,1))
    if name: room['name']=name


def furniture(ident, kind, room, bounds, **extra):
    return dict(id=ident, kind=kind, room_id=room, bounds=bounds, polygon=ring(box(*bounds)), **extra)


def build_project():
    # Start with the delivered project, not an earlier P11 prototype.
    source=ROOT/'examples/gallery/tirumala-4'
    project=json.loads((source/'project.floorforge.json').read_text())
    building=json.loads((source/'building.json').read_text())
    cp=project['customPlan']; plan=deepcopy(building['planning']['canonicalPlan'])
    plan.update(version=REVISION, name='Tirumala 5 · Plan A · Forecourt utility',
                kitchenBounds=KITCHEN[:], utilityPlan='forecourt', pantryBounds=PANTRY[:],
                pantryAisle=PANTRY_AISLE[:])
    plan['rooms']=[r for r in plan['rooms'] if r['id']!='g-kitchen-store']
    set_room(next(r for r in plan['rooms'] if r['id']=='g-care'), ICU)
    set_room(next(r for r in plan['rooms'] if r['id']=='g-wash-gully'), UTILITY, 'Forecourt utility')

    # Delete the old store / wash strip and move only the kitchen–ICU partition.
    kept=[]
    for wr in plan['wallRects']:
        x0,y0,x1,y1=wr
        old_strip = y0 < 4800 and x0 >= 1216.7 and x1 <= 2416.9
        old_east_kitchen = y0==1524 and x0 < 5452.4 and x1 <= 5602.4
        old_icu_south = x0==5302.4 and y0 < 5909.6
        if not (old_strip or old_east_kitchen or old_icu_south): kept.append(wr)
    kept += [[0,1524,150,4925], [150,1524,2700,1674],
             [4160,1524,5602.4,1674], [4160,1674,4310,5759.6],
             [4160,5759.6,5602.4,5909.6]]
    plan['wallRects']=kept
    mask=unary_union([box(*r) for r in kept])
    old_main=Polygon(plan['openFloor'][0]['outer'],plan['openFloor'][0].get('holes',[]))
    main=old_main.union(box(150,1674,4160,4850)).difference(box(4160,1674,5452.4,5909.6)).difference(mask)
    main=main.union(box(2000,7375.6,3371.6,8899.6))
    plan['openFloor']=regions(main)+plan['openFloor'][1:]
    plan['counter']=[[150,1674],[4060,1674],[4060,2274],[750,2274],[750,3900],[150,3900]]
    plan['openings']=[o for o in plan['openings'] if o['id']!='store-door']
    for o in plan['openings']:
        if o['id']=='kitchen-east': o['b'][0]=4160
        if o['id']=='icu-east-window':
            o['a'][0]=5200
            o['b'][0]=7400
        if o['id']=='stair-window':
            o.update(connects=['g-kitchen','g-stair'],ventilation=False)
    plan['raisedForecourt']=regions(unary_union([Polygon(r['outer']) for r in plan['raisedForecourt']]).difference(box(*UTILITY)))
    plan['furniture']=[f for f in plan['furniture'] if f['room_id'] not in ('g-kitchen-store','g-wash-gully')]
    # Reorient only the approved ICU furniture after the Plan A conversion.
    # Move the dining ensemble 425 mm east to preserve the pantry's standing aisle.
    for f in plan['furniture']:
        if f['kind']=='dining-set':
            f['polygon']=[[x,y-425] for x,y in f['polygon']]
            f['bounds']=[f['bounds'][0],f['bounds'][1]-425,f['bounds'][2],f['bounds'][3]-425]
            f['parts']=[[[x,y-425] for x,y in part] for part in f['parts']]
    plan['furniture'] += [
        furniture('g-living/pantry-cabinet','pantry-cabinet','g-living',PANTRY[:],heightMm=1800),
        furniture('g-wash-gully/laundry-sink','laundry-sink','g-wash-gully',[250,921.6,950,1521.6]),
        furniture('g-wash-gully/top-load-washer','top-load-washer','g-wash-gully',[1100,921.6,1700,1521.6]),
        furniture('g-wash-gully/utility-worktop','utility-worktop','g-wash-gully',[1770,921.6,2250,1521.6]),
    ]
    ground_revision(plan)
    plan['dimensions']=[dict(id=r['id'],name=r['name'],widthMm=r['bounds'][2]-r['bounds'][0],
        depthMm=r['bounds'][3]-r['bounds'][1],area=r['areaSqFt'],stepped=len(r['regions'][0]['outer'])>4) for r in plan['rooms']]
    cp['canonicalPlan']=plan
    cp['tirumalaMeta'].update(projectId='tirumala-5',sourceProject='tirumala-4',
        sourcePlanHash=building['planHash'],displayOption='Plan A',version=REVISION,
        label=plan['name'],galleryRevision=REVISION,tirumala4Presentation=True,
        utilityPlan='forecourt',trial=False)
    cp['floors'][0]['rooms']=[dict(id=r['id'],kind=next((s['kind'] for s in building['spaces'] if s['id']==r['id']),'hall'),
                                   name=r['name'],polygon=deepcopy(r['regions'][0]['outer'])) for r in plan['rooms']]
    from .tirumala_luxury import upper_plan
    cp['upperPlan']=upper_plan(plan)
    cp['floors'][1]['rooms']=[dict(id=r['id'],kind=r['kind'],name=r['name'],polygon=deepcopy(r['polygon'])) for r in cp['upperPlan']['rooms']]
    project['brief']['title']='Tirumala 5'
    project['draftRevision']=4
    project['notes']='Tirumala 5 — selected Plan A, based on Tirumala 4. 40 × 50 ft; 15 ft wide ICU; kitchen against south wall; 7 × 4.5 ft forecourt utility; dry pantry below high stair flight. Ground room sizes, ground staircase and parking retained. Living entrance shifted 100 mm north, ICU living opening 150 mm south, extra corner gap closed while drawing and rear-lobby access remain. ICU recliner head south, feet north. Utility screened in ivory and teak.'
    from .tirumala_5_upper import project_addition
    project_addition(project)
    project['notes'] += ' G+2 revision: an indoor gallery beside the east glazing leads to a South–West–North upper staircase aligned directly above the original ground stair, with an enclosed second landing and family hall. The first north guest bedroom extends one foot south in its front portion; its rear wall retains the three-foot circulation passage. The small balcony, connector and projecting corner remain removed. Main terrace retained with opaque ivory parapets. The double-height opening remains beside the indoor gallery and the hanging disc pendants are removed. Large 3200 × 1600 mm slabs, substantial glazing, teak joinery and coordinated roof/beam expression. Structural dimensions are architectural concept placeholders pending engineering.'
    project['editorState']['customPlan']=deepcopy(cp)
    # JavaScript serializes 150.0 as 150; use the same numeric form before hashing.
    from .tirumala_p11_p12 import _browser_numbers
    return _browser_numbers(project)


def add_fixture(k, item, poly):
    """Furniture built from the exact same footprints drawn in 2D."""
    x0,y0,x1,y1=[v/1000 for v in item['bounds']]
    cx,cy=(x0+x1)/2,(y0+y1)/2
    owner=item['id']; kind=item['kind']
    if kind=='pantry-cabinet':
        k.rect((x0,y0,.08,x1,y1,1.8),'oak-warm',0,'furniture',owner,owner=owner)
        for i in range(3):
            a=x0+i*(x1-x0)/3
            k.rect((a+.008,y0-.014,.12,a+(x1-x0)/3-.008,y0,1.78),'cabinet',0,'detail',f'{owner}-front-{i}',owner=owner)
            k.beam((a+.31,y0-.027,.89),(a+.31,y0-.027,1.05),.009,'brass',0,'detail')
    elif kind=='top-load-washer':
        k.rb((cx,cy,.45),(x1-x0,y1-y0,.9),'ceramic',0,'furniture',.025,owner=owner)
        k.rect((x0+.045,y0+.06,.901,x1-.045,y1-.10,.912),'blackglass',0,'detail',owner+'-lid',owner=owner)
        k.rect((x0+.035,y1-.09,.9,x1-.035,y1-.025,.96),'appliance',0,'detail',owner+'-controls',owner=owner)
    elif kind=='laundry-sink':
        # Recessed open basin, four rim strips and a bottom (no solid plug across bowl).
        k.rect((x0,y0,.08,x1,y1,.78),'cabinet',0,'furniture',owner+'-base',owner=owner)
        for i,b in enumerate([(x0,y0,.78,x1,y0+.09,.89),(x0,y1-.09,.78,x1,y1,.89),
                              (x0,y0,.78,x0+.09,y1,.89),(x1-.09,y0,.78,x1,y1,.89),
                              (x0+.09,y0+.09,.785,x1-.09,y1-.09,.80)]):
            k.rect(b,'ceramic',0,'detail',owner+f'-bowl-{i}',owner=owner)
        k.beam((cx,y1-.04,.89),(cx,y1-.04,1.17),.012,'brass',0,'detail')
        k.beam((cx,y1-.04,1.17),(cx,cy,1.14),.012,'brass',0,'detail')
    elif kind=='utility-worktop':
        k.rect((x0,y0,.08,x1,y1,.85),'cabinet',0,'furniture',owner+'-base',owner=owner)
        k.rect((x0,y0,.85,x1,y1,.89),'counter',0,'detail',owner+'-top',owner=owner)


def refine_scene(scene, building):
    """Inherit T4 appearance, then adapt details and cameras to the selected plan."""
    from .tirumala_4 import apply_tirumala_4_scene
    apply_tirumala_4_scene(scene,building)
    scene['tirumala5']=True
    scene['presentation']['style']='tirumala-5-plan-a'
    scene['exterior_review']['protected_interior_unchanged']=False
    scene['planA']={'revision':REVISION,'source':'tirumala-4','kitchenMm':KITCHEN,
        'icuMm':ICU,'utilityMm':UTILITY,'pantryMm':PANTRY,'pantryStandingAisleMm':PANTRY_AISLE,
        'utilityWorkingDepthMm':771.6,'pantryCabinetHeightMm':1800,
        'services':'Tap and drain indicative; plumbing route and final fall require site coordination.'}
    # Relocate T4's cabinet seams and pulls to the new south leg; no stray panels.
    for n in scene['nodes']:
        name=n['id']
        if name.startswith(('t4-base-store','t4-upper-')): n['position'][0]-=2.2668
        elif name.startswith('t4-base-east-'): n['position'][0]-=1.0
    # A flush drain and backsplash identify the open wash bay without enclosing it.
    def detail(ident,b,mat):
        x0,y0,z0,x1,y1,z1=b
        scene['nodes'].append(dict(id=ident,owner=ident,asset='unit-box',material=mat,
            position=[(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],scale=[x1-x0,y1-y0,z1-z0],
            rotation=[0,0,0],floor=0,role='decor',collide=False))
    detail('t5-utility-drain',[.30,.72,.001,2.16,.78,.004],'steel')
    detail('t5-utility-backsplash',[.15,1.515,.02,2.2836,1.523,1.25],'ivory-marble-satin-wet')
    for i in range(20):
        x=.33+i*.09
        detail(f't5-drain-slot-{i}',[x,.729,.004,x+.012,.771,.005],'blackglass')
    def camera(key,label,pos,target,fov=64):
        dx,dy,dz=[target[i]-pos[i] for i in range(3)]
        scene['cameras'][key]=dict(id=key,label=label,position=pos,target=target,fov=fov,
            enter_walk=True,floor=0,eye_height_above_ffl_m=pos[2],
            walker=dict(position=pos[:],yaw_rad=math.atan2(-dx,dy),pitch_rad=math.atan2(dz,math.hypot(dx,dy))))
    camera('interior_kitchen_living_dining','Wider kitchen · connected dining',[3.5,2.8,1.63],[3.8,6.5,1.4],68)
    camera('interior_icu_veranda_garden','15 ft ICU · true eye level',[4.95,2.6,1.63],[7.6,5.2,1.4])
    camera('living_double_height','Living and double-height gallery',[5.3,6.5,1.63],[6.8,8.1,4.6],68)
    camera('forecourt_utility','Forecourt wash bay',[2.9,.53,1.63],[.9,1.18,.8])
    camera('under_stair_pantry','Dry pantry below high stair flight',[3.5,7.7,1.63],[2.65,8.6,1.1])
    scene['cameras']['care_recliner_eye_level']=dict(id='care_recliner_eye_level',
        label='ICU recliner · looking north',position=[6.12,3.7548,1.18],
        target=[10.5,3.7548,1.32],fov=52,floor=0,eye_height_above_ffl_m=1.18,
        posture='recliner-seated-1.18m',description='Head south, feet north; seated sightline toward the north glazing.')
    scene['cameras']['interior']=scene['cameras']['interior_kitchen_living_dining']
    # The widened ICU now lies under part of the earlier double-height rectangle.
    # A local ceiling covers that corner; the living atrium above stays unchanged.
    from .scene_kit import extrude
    cap=box(4.16,4.875,6.30,5.9096)
    mesh=extrude(cap,3.315,3.335)
    scene['assets']['t5-icu-ceiling']=dict(vertices=mesh.vertices.tolist(),faces=mesh.faces.tolist(),closed=True)
    scene['nodes'].append(dict(id='t5-icu-ceiling',owner='g-care',asset='t5-icu-ceiling',
        material='ceiling',position=[0,0,0],scale=[1,1,1],rotation=[0,0,0],floor=0,role='ceiling'))
