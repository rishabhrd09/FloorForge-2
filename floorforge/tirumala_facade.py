"""Presentation-only facade treatment derived from My Desired Home materials."""
from math import cos, sin, sqrt

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union


def vacant_adjoining_context(ctx):
    """Owner correction: adjoining lots are vacant, not inferred residences."""
    ctx['adjoining_south_and_west'] = {
        'status': 'owner-confirmed-vacant-2026-10-31',
        'vacant': True,
        'south_vacant_bounds_scene': [-26.5, 0.0, 0.0, 29.5],
        'west_vacant_bounds_scene': [0.0, 15.24, 12.192, 29.5],
        'note': 'Grass replaces the adjoining and same-block placeholder houses. Road-opposite reference landmarks remain.',
    }


def refine_facade(scene, building):
    mats = scene['materials']
    # Reference values read from examples/gallery/my-desired-home/scene.json.
    mats.update({
        't4-facade-plaster': dict(color='#f1efea', kind='render', texture='plaster',
                                  normal=.12, roughness=.88, roughness_scale=.9),
        't4-facade-stone': dict(color='#a39d92', alt='#6f6b64', kind='stoneclad',
                                texture='stone', normal=.38, roughness=.9, tile_m=[1.6, 1.2]),
        't4-facade-frame': dict(color='#1d2022', kind='metal', metallic=.3,
                                params=[.36], roughness=.32),
        't4-facade-timber': dict(color='#7a5234', kind='wood', texture='wood', roughness=.46),
        't4-facade-glass': dict(color='#aec8cc', alpha=.40, roughness=.035,
                                roughness_override=.035, metallic=.1,
                                glassOpacity=.40, glassReflectivity=.65, glassEnv=2.0),
    })
    vacant_adjoining_context(scene['context'])
    spaces = {r['id']: r for r in building['spaces']}
    closed = {r['id'] for r in building['spaces'] if r.get('enclosed')}
    masks = {}
    for floor in (0, 1):
        polys = [Polygon(r['clear'], r.get('holes', [])) for r in building['spaces']
                 if r['floor'] == floor and r['id'] in closed]
        polys += [Polygon(w['polygon']) for w in building['walls'] if w['floor'] == floor]
        masks[floor] = unary_union(polys).buffer(.5)

    def world_vertices(node):
        # Architectural wall nodes are axis-aligned or rotated around Z only.
        assert abs(node['rotation'][0]) + abs(node['rotation'][1]) < 1e-8
        c, s = cos(node['rotation'][2]), sin(node['rotation'][2])
        tx, ty, tz = node['position']; sx, sy, sz = node['scale']
        return [[tx+c*v[0]*sx-s*v[1]*sy, ty+s*v[0]*sx+c*v[1]*sy, tz+v[2]*sz]
                for v in scene['assets'][node['asset']]['vertices']]

    # Thin finish faces on the OUTSIDE only. No room surfaces or wall solids move.
    finish_faces = 0
    for node in list(scene['nodes']):
        if node.get('role') != 'wall' or node.get('floor') not in masks:
            continue
        if node.get('owner', '').startswith(('boundary-', 'east-gate-')):
            continue
        verts = world_vertices(node)
        out, faces = [], []
        for face in scene['assets'][node['asset']]['faces']:
            a, b, c = [verts[i] for i in face[:3]]
            u = [b[i]-a[i] for i in range(3)]; v = [c[i]-a[i] for i in range(3)]
            n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
            length = sqrt(sum(q*q for q in n))
            if length < 1e-9: continue
            n = [q/length for q in n]
            if abs(n[2]) > .05: continue
            mid = [sum(p[i] for p in [a,b,c])/3 for i in range(3)]
            mask = masks[node['floor']]
            outer = Point((mid[0]+n[0]*.02)*1000, (mid[1]+n[1]*.02)*1000)
            inner = Point((mid[0]-n[0]*.02)*1000, (mid[1]-n[1]*.02)*1000)
            if mask.covers(outer) or not mask.covers(inner): continue
            start = len(out)
            out += [[p[i]+n[i]*.002 for i in range(3)] for p in [a,b,c]]
            faces.append([start, start+1, start+2])
        if not faces: continue
        aid = 't4-exterior-finish-' + node['id']
        scene['assets'][aid] = dict(vertices=out, faces=faces, closed=False)
        scene['nodes'].append(dict(id=aid, owner=aid, asset=aid, role='wall-panel',
            floor=node['floor'], material='t4-facade-plaster', position=[0,0,0],
            scale=[1,1,1], rotation=[0,0,0], collide=False))
        finish_faces += len(faces)

    exterior_openings = []
    for op in scene['opening_model']['openings']:
        inside = [spaces[k] for k in op.get('connects', []) if k in closed]
        outside = [k for k in op.get('connects', []) if k not in closed]
        if not inside or not outside or op.get('kind') == 'open-passage': continue
        exterior_openings.append(op['id'])
        for node in scene['nodes']:
            if node.get('owner') != op['id']: continue
            if node.get('role') == 'glass': node['material'] = 't4-facade-glass'
            elif node.get('material') in ('frame', 'doorframe'): node['material'] = 't4-facade-frame'
            elif node.get('material') in ('timber', 'teak-warm', 'walnut'): node['material'] = 't4-facade-timber'

        # A substantial outer reveal like the reference, entirely outside the aperture.
        a, b = [[q/1000 for q in op[k]] for k in ['a','b']]
        width = sqrt(sum((b[i]-a[i])**2 for i in range(2)))
        ux, uy = [(b[i]-a[i])/width for i in range(2)]
        nx, ny = uy, -ux
        center = [(a[i]+b[i])/2 for i in range(2)]
        room_center = Polygon(inside[0]['clear']).centroid
        if nx*(center[0]-room_center.x/1000) + ny*(center[1]-room_center.y/1000) < 0:
            nx, ny = -nx, -ny
        base = op['floor']*3.508 + op['sill']/1000
        top = base + op['height']/1000
        t = .05
        def trim(s0,s1,z0,z1,label):
            # Non-closed surface asset prevents decorative trim adding a walk collider.
            points = [[a[0]+ux*u+nx*.105, a[1]+uy*u+ny*.105, z]
                      for u,z in [(s0,z0),(s1,z0),(s1,z1),(s0,z1)]]
            name = f't4-reveal-{op["id"]}-{label}'
            scene['assets'][name] = dict(vertices=points, faces=[[0,1,2],[0,2,3]], closed=False)
            scene['nodes'].append(dict(id=name, owner=name, asset=name, role='window-surround',
                floor=op['floor'], material='t4-facade-frame', position=[0,0,0],
                scale=[1,1,1], rotation=[0,0,0], collide=False))
        trim(-t,0,base,top,'left'); trim(width,width+t,base,top,'right')
        trim(-t,width+t,top,top+t,'head')
        if op['sill'] > 0: trim(-t,width+t,base-t,base,'sill')

    def panel(name, rect, material, floor=0, role='cladding'):
        x0,y0,z0,x1,y1,z1 = rect
        scene['nodes'].append(dict(id=name, owner=name, asset='unit-box', material=material,
            floor=floor, role=role, position=[(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],
            scale=[x1-x0,y1-y0,z1-z0], rotation=[0,0,0], collide=False))

    for node in scene['nodes']:
        if node.get('role') == 'cladding': node['material'] = 't4-facade-stone'
        if node.get('role') in ('pergola', 'soffit') and node['material'] in ('timber','teak-warm'):
            node['material'] = 't4-facade-timber'
        if node.get('id') == 'ivory-floating-roof-edge': node['material'] = 't4-facade-plaster'
    # A restrained stone feature on an existing blank east-wall bay, clear of windows.
    panel('t4-east-stone-feature', [7.85,1.508,.12,8.78,1.523,3.30], 't4-facade-stone')
    # Thin dark slab-edge lines echo the reference's horizontal facade composition.
    panel('t4-east-slab-shadow', [1.22,1.505,3.36,8.98,1.524,3.39], 't4-facade-frame', role='fascia')
    panel('t4-north-slab-shadow', [11.583,8.20,3.36,11.602,14.40,3.39], 't4-facade-frame', role='fascia')
    scene['facadeRefinement'] = dict(
        revision='desired-home-exterior-v1-2026-10-31', source='my-desired-home',
        wallColor='#f1efea', frameColor='#1d2022', exteriorFinishTriangles=finish_faces,
        exteriorOpenings=exterior_openings, houseGeometryChanged=False,
        neighbours='Owner-confirmed vacant adjoining lots shown with grass',
    )
