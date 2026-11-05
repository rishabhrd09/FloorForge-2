"""Tirumala 5 reference-led finishes, without changing room footprints.

The tile repeat contains ONE slab, rather than the old recipe's two slabs in
each direction. Dimensions in the material contract are therefore actual
slab dimensions. The first-floor parapet follows the compiled terrace, including
the approved removal of the side connector. Utility privacy follows the
canonical Plan A boundary strips without taking any kitchen or utility floor.
"""
from __future__ import annotations

import math
import random
from copy import deepcopy

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from .scene_kit import Kit

REVISION = 'tirumala-5-reference-finishes-stacked-stair-2026-11-05'
H = 3.508


def _poly(reg):
    return Polygon([(x/1000, y/1000) for x, y in reg['polygon']],
                   [[(x/1000, y/1000) for x, y in r] for r in reg.get('holes', [])])


def _kit(scene):
    k = Kit(random.Random(5105))
    for attr in ('nodes', 'assets', 'colliders', 'furniture', 'editables', 'lights', 'vegetation'):
        setattr(k, attr, scene[attr])
    return k


def _materials(scene):
    mats = scene['materials']
    # 3.2 x 1.6 m slab = 10 ft 6 in x 5 ft 3 in. Thin visible joints, not a
    # texture whose repeat is silently split into four much smaller tiles.
    interior = dict(color='#efe9de', alt='#d5cdbf', kind='tile', texture='tile',
                    tile_m=[3.2, 1.6], params=[1, .0012, .035, .72], normal=.025,
                    roughness=.24, roughness_scale=.90, env=.85,
                    clearcoat=.12, clearcoat_roughness=.24)
    for name in ('floor', 'ivory-marble-polished'):
        mats[name] = dict(interior)
    for name in ('ivory-marble-exterior-matte', 'terrace-stone'):
        mats[name] = dict(interior, color='#e5ded1', alt='#d9d0c1',
                          params=[1, .0015, .025, .12], normal=.055,
                          roughness=.58, roughness_scale=1.40, clearcoat=0)
    mats['ivory-marble-satin-wet'] = dict(interior, tile_m=[1.6, .8],
        params=[1, .002, .025, .08], normal=.075, roughness=.61,
        roughness_scale=1.48, clearcoat=0)
    mats.update({
        't5-ivory-render': dict(color='#f0ede6', texture='plaster', kind='render',
                               normal=.08, roughness=.84, roughness_scale=.96),
        't5-honed-coping': dict(color='#e4ded2', alt='#d8d0c2', texture='stone', kind='stone',
                              normal=.10, roughness=.62, roughness_scale=1.05, tile_m=[1.6, .8]),
        't5-shadow-reveal': dict(color='#89847b', roughness=.83),
        't5-soft-charcoal': dict(color='#24272a', kind='metal', params=[.35], metallic=.22,
                                 roughness=.35, normal=.08),
        't5-door-teak': dict(color='#79583c', alt='#aa8258', kind='wood', texture='wood',
                              seed=52, normal=.12, roughness=.40, roughness_scale=.85,
                              tile_m=[1.4, 2.8], clearcoat=.13, clearcoat_roughness=.32),
        't5-light-timber': dict(color='#b0916a', alt='#c4ad87', kind='wood', texture='wood',
                                seed=29, normal=.10, roughness=.46, roughness_scale=.92,
                                tile_m=[1.2, 2.4]),
        't5-stair-stone': dict(color='#585a57', alt='#77766e', kind='stone', texture='stone',
                                normal=.08, roughness=.50, roughness_scale=.92),
        't5-cove-warm': dict(color='#ffe8c5', emission=.32, roughness=.60),
    })
    for name in ('wall', 'ceiling', 't4-facade-plaster'):
        mats[name].update(color='#f0ede6' if name != 'ceiling' else '#f5f2eb',
                          normal=.08, roughness_scale=.96)
    for name in ('oak', 'oak-warm'):
        mats[name].update(color='#b0916a', alt='#c4ad87', normal=.10, roughness_scale=.92)
    for name in ('timber', 'teak-warm', 't4-facade-timber'):
        mats[name].update(color='#79583c', alt='#aa8258', normal=.12, roughness_scale=.85)
    for name in ('frame', 't4-facade-frame'):
        mats[name].update(color='#24272a', normal=.08, roughness_scale=.95)
    mats['t4-facade-glass'].update(color='#cbd7d5', alpha=.23, glassOpacity=.19,
        glassReflectivity=.56, glassEnv=1.35, roughness_override=.025)
    mats['counter'].update(color='#ece7dd', alt='#c6bfb1', normal=.05,
        roughness_scale=.95, clearcoat=.12, clearcoat_roughness=.25)
    mats['linen'].update(color='#eee8dd', normal=.20, sheen=.24)
    mats['fabric'].update(color='#d5cabc', normal=.20, sheen=.25)
    mats['fabric-dark'].update(color='#6f7a71', normal=.20, sheen=.22)
    mats['stairtread'] = dict(mats['t5-stair-stone'])


def _first_terrace(scene, building, k):
    """Continuous opaque boundary with protected door openings and real coping."""
    up = building['planning']['upperPlan']
    terrace = unary_union([_poly(reg) for room in up['rooms'] if room['id'] == 'u-terrace'
                           for reg in room['regions']])
    enclosed = unary_union([_poly(reg) for room in up['rooms'] if room['kind'] != 'terrace'
                            for reg in room['regions']])
    walls = unary_union([_poly(reg) for reg in up['wallRegions']])
    doorcuts = unary_union([LineString([(x/1000, y/1000) for x, y in (op['a'], op['b'])]).buffer(.16, cap_style=2)
                           for op in building['openings'] if op['floor'] == 1 and op['sill'] == 0])
    # Remove each original exposed-glass panel and its immediate rail. Gallery
    # glass remains: it preserves the requested visual link to the room below.
    remove = set()
    nodes = scene['nodes']
    for i, n in enumerate(nodes):
        if n['id'].startswith('terrace-guard-'):
            remove.add(n['id'])
            if i + 1 < len(nodes) and nodes[i+1].get('role') == 'railing' and nodes[i+1]['asset'] == 'unit-cylinder':
                remove.add(nodes[i+1]['id'])
    nodes[:] = [n for n in nodes if n['id'] not in remove]
    # Build inward: the edge and plot dimensions do not grow with finish depth.
    boundary = terrace.difference(terrace.buffer(-.12, join_style=2))
    boundary = boundary.difference(enclosed.buffer(.055)).difference(walls.buffer(.04)).difference(doorcuts)
    k.poly_mesh(boundary, H, H+1.08, 't5-ivory-render', 1, 'parapet', 't5lux-first-opaque-parapet')
    cap = boundary.buffer(.014, join_style=2).intersection(box(0, 0, 12.192, 15.24)).difference(doorcuts)
    k.poly_mesh(cap, H+1.08, H+1.12, 't5-honed-coping', 1, 'coping', 't5lux-first-parapet-coping')
    # Crisp full-depth fascia under the same terrace perimeter. It reads as a
    # continuous slab edge rather than the former narrow glass-linked ledge.
    # A 4 mm exterior finish offset avoids a coplanar duplicate of the slab
    # face (which otherwise produces a ragged/hatched edge in real-time views).
    fascia = terrace.buffer(.004, join_style=2).intersection(box(0,0,12.192,15.24)).difference(terrace.buffer(-.10, join_style=2))
    k.poly_mesh(fascia, H-.18, H-.016, 't5-ivory-render', 0, 'fascia', 't5lux-first-slab-fascia')
    k.poly_mesh(fascia, H-.20, H-.182, 't5-shadow-reveal', 0, 'fascia', 't5lux-first-slab-drip-reveal')
    # Keep the existing light pergola; articulate its frame with honest beam
    # depth rather than a floating collection of unsupported timber strips.
    for n in nodes:
        if n['id'].startswith('pergola-post-'):
            n['material'] = 't5-soft-charcoal'
            n['scale'][0] = .10; n['scale'][1] = .10
        elif n['id'].startswith('pergola-slat-'):
            # Slats terminate inside the border frame, with their top below
            # its top surface; overlapping coplanar timber/white faces were
            # shimmering and looked like stray hanging fragments.
            index=int(n['id'].rsplit('-',1)[1])
            n['position']=[3.95,2.0+index*2.30/15,H+2.73]
            n['scale']=[2.60,.065,.12]
            n['material']='t5-door-teak'
    for name, bounds in [
        ('east', (2.45,1.80,H+2.58,5.45,2.00,H+2.84)),
        ('west', (2.45,4.30,H+2.58,5.45,4.50,H+2.84)),
        ('south', (2.45,2.00,H+2.58,2.65,4.30,H+2.84)),
        ('north', (5.25,2.00,H+2.58,5.45,4.30,H+2.84)),
    ]:
        k.rect(bounds, 't5-ivory-render', 1, 'pergola', 't5lux-pergola-beam-'+name)
    # A low contained bed behind the opaque east parapet; clear of the lounge
    # and the retained main terrace doorway.
    k.rect((6.25,1.70,H,7.65,2.13,H+.30), 't5-ivory-render', 1, 'planter', 't5lux-first-planter')
    k.rect((6.30,1.75,H+.29,7.60,2.08,H+.31), 'soil', 1, 'landscape', 't5lux-first-planter-soil')
    for x, species, height in [(6.50,'strelitzia',.8),(7.05,'grass_ornamental',.45),(7.48,'strelitzia',.65)]:
        k.plant(x,1.91,H+.31,species,height=height,f=1)
    scene['tirumala5Finish']['firstParapet'] = dict(heightM=1.12, thicknessM=.12,
        material='opaque warm-white render with honed stone coping',
        glassReplaced=len(remove), internalGalleryGlassRetained=True)


def _veranda_soffit(scene, building, k):
    # The inherited single timber bar spanned the veranda's bounding box,
    # crossing empty air at its stepped east/north corner. Follow the real
    # polygon instead; the folded timber doors below are intentional and stay.
    scene['nodes'][:] = [n for n in scene['nodes'] if n['id'] != 'veranda-front-timber-beam']
    room=next(r for r in building['spaces'] if r['id']=='g-veranda')
    veranda=Polygon([(x/1000,y/1000)for x,y in room['clear']])
    edge=veranda.difference(veranda.buffer(-.10,join_style=2))
    k.poly_mesh(edge,H-.32,H-.18,'t5-ivory-render',0,'fascia','t5lux-veranda-stepped-fascia')
    scene['tirumala5Finish']['verandaFascia']='Follows actual stepped veranda perimeter; bounding-box timber bar removed'


def _clip_boundary_box(scene, ident, axis, start, end):
    """Retain only the portions outside a replaced utility boundary segment."""
    node = next((n for n in scene['nodes'] if n['id'] == ident), None)
    if node is None:
        return
    if node['asset'] != 'unit-box' or any(abs(a) > 1e-8 for a in node.get('rotation', [])):
        raise ValueError(f'Unexpected boundary geometry for {ident}')
    lo = node['position'][axis] - node['scale'][axis] / 2
    hi = node['position'][axis] + node['scale'][axis] / 2
    if end <= lo or start >= hi:
        return
    scene['nodes'].remove(node)
    for i, (a, b) in enumerate(((lo, min(start, hi)), (max(end, lo), hi))):
        if b - a < 1e-8:
            continue
        part = deepcopy(node)
        part['id'] = f'{ident}-t5-retained-{i}'
        part['position'][axis] = (a + b) / 2
        part['scale'][axis] = b - a
        scene['nodes'].append(part)


def _utility_privacy(scene, building, k):
    """Opaque south boundary and ventilated east screen; north access is open."""
    privacy = building.get('planning', {}).get('canonicalPlan', {}).get('utilityPrivacy')
    if not privacy:
        return
    south = [v / 1000 for v in privacy['southRectMm']]
    east = [v / 1000 for v in privacy['eastRectMm']]
    height = privacy['heightMm'] / 1000
    sx0, sy0, sx1, sy1 = south
    ex0, ey0, ex1, ey1 = east
    # Replace, rather than overlap, the old boundary wall and its decorative
    # coping/cladding. The rest of the frontage retains its existing design.
    _clip_boundary_box(scene, 'boundary-south', 1, sy0, sy1)
    for ident in ('boundary-east-south', 'boundary-east-cladding', 'boundary-east-cap',
                  't4-boundary-east-reveal-0', 't4-boundary-east-reveal-1'):
        _clip_boundary_box(scene, ident, 0, ex0, ex1)
    scene['nodes'][:] = [n for n in scene['nodes'] if not (
        n['id'].startswith(('t4-boundary-light-', 't4-boundary-light-frame-'))
        and ex0 <= n['position'][0] <= ex1)]
    base = -float(building.get('plinth', 300)) / 1000
    k.rect((sx0, sy0, base, sx1, sy1, height-.04), 't5-ivory-render', 0,
           'privacy-wall', 't5lux-utility-south-wall')
    k.rect((sx0, sy0, height-.04, sx1, sy1, height), 't5-honed-coping', 0,
           'coping', 't5lux-utility-south-coping')
    k.rect((ex0, ey0, base, ex1, ey1, .45), 't5-ivory-render', 0,
           'privacy-wall', 't5lux-utility-east-plinth')
    k.rect((ex0, ey0, .45, ex1, ey1, .48), 't5-honed-coping', 0,
           'coping', 't5lux-utility-east-plinth-coping')
    cy = (ey0 + ey1) / 2
    mid = (ex0 + ex1) / 2
    for i, x in enumerate((ex0+.03, mid, ex1-.03)):
        k.rect((x-.03, cy-.04, .48, x+.03, cy+.04, height), 't5-soft-charcoal',
               0, 'privacy-screen', f't5lux-utility-screen-post-{i}')
    k.rect((ex0, cy-.04, height-.04, ex1, cy+.04, height), 't5-soft-charcoal',
           0, 'privacy-screen', 't5lux-utility-screen-top')
    # Two framed bays of tilted horizontal timber-look fins. They have actual
    # ventilation gaps, real depth and no backing plane blocking the air path.
    bays = ((ex0+.06, mid-.03), (mid+.03, ex1-.06))
    for bay, (a, b) in enumerate(bays):
        for i in range(12):
            k.node(k.cube, 't5-door-teak', ((a+b)/2, cy, .56+i*.10),
                   (b-a, .035, .075), (math.radians(35), 0, 0), floor=0,
                   role='privacy-screen', name=f't5lux-utility-louvre-{bay}-{i}')
    for name, bounds in (('south', south), ('east', east)):
        k.obstacle(box(*bounds), 0, f't5lux-utility-{name}-privacy')
    scene['tirumala5Finish']['utilityPrivacy'] = dict(
        southRectMm=privacy['southRectMm'], eastRectMm=privacy['eastRectMm'],
        heightMm=privacy['heightMm'], northAccessOpen=True,
        south='Opaque ivory wall with stone coping',
        east='Ventilated teak-look louvres above a low ivory plinth',
        kitchenWindowUnobstructed=ex1 < 2.70)


def _upper_revision_cleanup(scene, building):
    """Remove orphan opening details and the three suspended atrium pendants."""
    openings = {o['id'] for o in building['openings']}
    retired = {'u-side-terrace-door', 'u-bedroom-terrace', 's2-stair-entry'} - openings
    prefixes = tuple(prefix + ident + '-' for ident in retired
                     for prefix in ('op-', 't4-exterior-finish-op-', 't5lux-reveal-'))
    remove = {n['id'] for n in scene['nodes'] if n.get('owner') in retired
              or (prefixes and n['id'].startswith(prefixes))}
    if 's2-stair-entry' in retired:
        remove.update(('s2-stair-entry-canopy', 's2-stair-entry-soffit', 's2-stair-start-platform'))
    # These are the source cluster's three locations, plus the previous
    # revision's positions. Each pendant has a cord, brass disc and emissive
    # diffuser; remove all three together rather than leaving floating cords.
    # Restrict the selection to this cluster so ceiling downlights and their
    # actual light sources remain intact. The cluster itself has no point lights.
    pendant_xy = ((3.10, 6.35), (3.65, 6.55), (4.05, 6.15),
                  (3.10, 5.80), (3.65, 6.00), (4.05, 5.65))
    pendants = [n for n in scene['nodes']
                if n.get('floor') == 1 and n.get('role') == 'fixture'
                and n.get('asset') == 'unit-cylinder'
                and n.get('material') in ('brass', 'lamp')
                and n['position'][2] > 4
                and any(abs(n['position'][0]-x) < 1e-6
                        and abs(n['position'][1]-y) < 1e-6 for x, y in pendant_xy)]
    remove.update(n['id'] for n in pendants)
    scene['nodes'][:] = [n for n in scene['nodes'] if n['id'] not in remove]
    scene['colliders'][:] = [c for c in scene['colliders'] if c['id'] not in retired]
    for ident in retired:
        scene.get('door_motion', {}).pop(ident, None)
    if 'openings' in scene.get('opening_model', {}):
        scene['opening_model']['openings'][:] = [o for o in scene['opening_model']['openings']
                                                if o['id'] not in retired]
    scene['tirumala5Finish']['upperCleanup'] = dict(retiredOpeningIds=sorted(retired),
        removedNodeCount=len(remove), pendantPartsRemoved=len(pendants),
        pendantGroupsRemoved=len({tuple(n['position'][:2]) for n in pendants}),
        suspendedAtriumDecoration=False, ceilingDownlightsRetained=True)


def _opening_reveals(scene, building, k):
    """Solid deep trim and sill geometry; apertures/moving panels stay untouched."""
    rooms = {r['id']: r for r in building['spaces']}
    closed = {r['id'] for r in building['spaces'] if r.get('enclosed')}
    scene['nodes'][:] = [n for n in scene['nodes'] if not n['id'].startswith('t4-reveal-')]
    count = 0
    for op in building['openings']:
        inside = [rooms[r] for r in op.get('connects', []) if r in closed]
        outside = [r for r in op.get('connects', []) if r not in closed]
        if not inside or not outside or op.get('kind') == 'open-passage':
            continue
        a,b = [[v/1000 for v in op[p]] for p in ('a','b')]
        length = math.dist(a,b); u=[(b[i]-a[i])/length for i in range(2)]
        n=[u[1],-u[0]];center=[(a[i]+b[i])/2 for i in range(2)]
        pc=Polygon(inside[0]['clear']).centroid
        if n[0]*(center[0]-pc.x/1000)+n[1]*(center[1]-pc.y/1000)<0:n=[-v for v in n]
        floor=op['floor']; base=floor*H+op['sill']/1000; top=base+op['height']/1000
        def span(s0,s1,d0,d1,z0,z1,label,mat='t5-soft-charcoal',role='window-surround'):
            poly=Polygon([(a[0]+u[0]*s+n[0]*d,a[1]+u[1]*s+n[1]*d)
                          for s,d in [(s0,d0),(s1,d0),(s1,d1),(s0,d1)]])
            k.poly_mesh(poly,z0,z1,mat,floor,role,'t5lux-reveal-'+op['id']+'-'+label)
        # Deep rectangular aluminium reveals create visible returns and honest
        # shadows. Their entire cross-section lies outside the clear opening.
        span(-.055,0,.076,.14,base,top+.055,'left')
        span(length,length+.055,.076,.14,base,top+.055,'right')
        span(-.055,length+.055,.076,.14,top,top+.055,'head')
        if op['sill']:
            span(-.08,length+.08,.075,.22,base-.045,base-.012,'stone-sill','t5-honed-coping','sill')
        count+=1
    scene['tirumala5Finish']['deepExteriorReveals'] = count


def _interior_detail(scene, k):
    # Real, small joinery details at the actual kitchen positions; all stay
    # inside existing cabinet footprints and never become circulation barriers.
    for n in scene['nodes']:
        if n.get('role') == 'door' and n.get('material') in ('oak-warm','teak-warm','t4-facade-timber','timber'):
            n['material'] = 't5-door-teak'
        if n.get('role') == 'soffit' and 'timber' in n.get('material',''):
            n['material'] = 't5-door-teak'
        if n['id'].startswith('gallery-glass-'):
            # Keep transparent internal guards, but frame them in warm timber
            # via the existing rail node that follows each panel.
            i=scene['nodes'].index(n)
            if i+1<len(scene['nodes']) and scene['nodes'][i+1].get('role')=='railing':
                scene['nodes'][i+1]['material']='t5-door-teak'
    # Warm shielded strip beneath existing south kitchen upper cabinets.
    k.rect((.48,1.92,1.485,.50,3.82,1.500),'t5-cove-warm',0,'fixture','t5lux-kitchen-task-strip')
    k.light((.66,2.9,1.47),9,color='#ffe8cc',kind='under-cabinet')
    # Ceiling border panels are thin finish geometry. They give the high ICU
    # ceiling a finished edge without lowering it or masking its real height.
    for i,bounds in enumerate([
        (4.34,1.73,3.292,8.84,1.88,3.315),
        (4.34,5.55,3.292,8.84,5.70,3.315),
    ]):
        k.rect(bounds,'ceiling',0,'ceiling-feature','t5lux-icu-ceiling-trim-'+str(i))
    for x,y in [(4.68,2.22),(8.52,2.22),(8.52,5.23)]:
        k.rect((x-.035,y-.035,3.285,x+.035,y+.035,3.298),'t5-cove-warm',0,'fixture',f't5lux-icu-downlight-{x}-{y}')
        k.light((x,y,3.23),10,color='#ffecd6',kind='downlight')


def apply(scene, building):
    """Call after Tirumala 5 base scene refinement; affects this sample only."""
    if building.get('planning',{}).get('tirumalaMeta',{}).get('projectId') != 'tirumala-5':
        return
    if scene.get('tirumala5Finish',{}).get('revision') == REVISION:
        return
    scene['tirumala5Finish'] = dict(revision=REVISION,
        palette='Ivory limestone and teak; pale continuous slab flooring',
        interiorSlabM=[3.2,1.6], exteriorSlabM=[3.2,1.6], slabsPerTextureRepeat=1,
        roomFootprintsChanged=False,
        note='Appearance refinement; parapet and glazing details are architectural concept geometry, not engineered specifications.')
    _materials(scene)
    k=_kit(scene)
    _upper_revision_cleanup(scene,building)
    _first_terrace(scene,building,k)
    _veranda_soffit(scene,building,k)
    _utility_privacy(scene,building,k)
    _opening_reveals(scene,building,k)
    _interior_detail(scene,k)
    # Restrained tone/exposure, no widened geometry or artificial wide-angle
    # camera tricks. Improved diffuse fill keeps ivory from becoming muddy.
    scene['presentation']['interior'].update(exposureScale=1.04,contrast=1.015,
        punch=.14,vignette=.035,warmth=.065,dayLampLevel=.20)
    scene['presentation']['exterior'].update(contrast=1.02,warmth=.055,punch=.14)
    scene['presentation']['lighting']['day'].update(sun=3.15,env=.34,bounce=.74,
        skyBounceColor='#f5f4ef',bounceColor='#e0d9cc',turbidity=2.6)
    scene['quality']='Shared dimensionally consistent architectural model with large-slab PBR finishes, deep joinery reveals and opaque terrace parapets.'
