"""Tirumala 4 finishes only: no changes to the approved house geometry."""


def refine_exterior(scene):
    scene['exteriorRefinement'] = {
        'revision': 'ivory-boundary-natural-planting-2026-10-31',
        'houseGeometryChanged': False,
        'boundary': 'Ivory render, honed limestone lower band and thin coping; existing gate width retained',
        'planting': 'Low mixed leaf planting replaces solid burgundy hedge blocks; edged grass pockets',
        'contextConfidence': 'Photo-informed appearance; existing unmeasured landmark offsets remain provisional',
    }
    mats = scene['materials']
    mats.update({
        't4-boundary-ivory': dict(kind='render', color='#eee8db', normal=.24, roughness_scale=.95),
        't4-boundary-limestone': dict(kind='stone', color='#d1c3ac', alt='#c7b89f', normal=.22,
                                     tile_m=[1.2, .45], roughness_scale=.9),
        't4-boundary-coping': dict(kind='stone', color='#ddd1bb', alt='#d1c5b0', normal=.12,
                                  tile_m=[1.2, .25], roughness_scale=.85),
        't4-shadow-line': dict(color='#a59a88', roughness=.9),
        't4-colony-road': dict(kind='concrete', color='#bdb9ae', alt='#b3aea2', normal=.4,
                               roughness_scale=1, tile_m=[2.2, 2.2]),
        't4-colony-paving': dict(kind='paver', color='#b6aea0', alt='#ae968a',
                                 params=[11, 6, .008, .22], normal=.45, tile_m=[2.2, 2.2]),
        't4-colony-wall': dict(kind='render', color='#9e9093', normal=.4, roughness_scale=1),
        't4-colony-turf': dict(kind='grass', color='#557447', alt='#789261', normal=.65,
                               roughness_scale=1, tile_m=[2.2, 2.2]),
        't4-mulch': dict(kind='soil', color='#574c3e', alt='#685c49', normal=.55),
    })
    for name, descriptor in mats.items():
        if name.startswith('t4-'):
            descriptor.setdefault('roughness', .85)
    scene['cameras']['north_garden_passage'] = dict(position=[11.78, 7.4, 1.58],
        target=[11.81, 11.5, .5], fov=52, description='Existing north garden strip, flush pads and lawn edging')
    # Reassign only perimeter finishes. The masonry, gate openings and levels stay put.
    for node in scene['nodes']:
        owner = node.get('owner', '')
        if owner.startswith('boundary-'):
            node['material'] = ('t4-boundary-coping' if 'cap' in owner else
                                't4-boundary-limestone' if 'cladding' in owner else 't4-boundary-ivory')
        elif owner.startswith('east-gate-pier'):
            node['material'] = 't4-boundary-coping' if 'cap' in owner else 't4-boundary-limestone'

    def detail(name, bounds, material):
        x0, y0, z0, x1, y1, z1 = bounds
        scene['nodes'].append(dict(id=name, owner=name, asset='unit-box', floor=-1,
            role='detail', material=material, position=[(x0+x1)/2, (y0+y1)/2, (z0+z1)/2],
            scale=[x1-x0, y1-y0, z1-z0], rotation=[0, 0, 0], collide=False))

    # Fine horizontal stone joints, not projecting posts or additional obstructions.
    for i, z in enumerate([.14, .57]):
        detail(f't4-boundary-east-reveal-{i}', [.04, -.021, z, 7.87, -.018, z+.008], 't4-shadow-line')
    detail('t4-boundary-north-stone-base', [12.192, 6.24, -.28, 12.207, 15.20, -.04], 't4-boundary-limestone')
    detail('t4-boundary-north-reveal', [12.192, 6.24, .64, 12.196, 15.20, .648], 't4-shadow-line')
    # Discreet inset light faces on existing wall; no freestanding bollards in paths.
    for i, x in enumerate([1.6, 4.0, 6.4]):
        detail(f't4-boundary-light-frame-{i}', [x-.09, -.025, .34, x+.09, -.021, .385], 'frame')
        detail(f't4-boundary-light-{i}', [x-.065, -.028, .351, x+.065, -.026, .367], 'lamp')
    # Crisp flush edging around the existing north-side grass; pads/route remain unchanged.
    detail('t4-north-lawn-edging', [11.59, 8.20, -.012, 11.615, 14.43, .005], 't4-boundary-coping')
    for lawn in scene.get('lawns', []):
        lawn['heightScale'] = .30
    # Low accents in the narrow strip: tall grasses previously spilled over the pads.
    for plant in scene.get('vegetation', []):
        x, y, _ = plant['position']
        if plant['species'] == 'grass_ornamental' and x >= 11.59 and y >= 8.2:
            plant['scale'] = .20
        elif plant['species'] == 'shrub_flowering' and x >= 11.59 and 7.7 <= y <= 8.2:
            plant['scale'] = .50
    mats['grass'].update(color='#62824e', alt='#7e9563', normal=.65)

    scene['presentation']['exterior'].update(warmth=.12, contrast=1.015, punch=.19)
    # Per-project light overrides, leaving all other sample profiles unchanged.
    scene['presentation']['lighting'] = {
        'day': dict(sun=3.7, env=.24, bounce=.85, skyBounceColor='#fff5e5', bounceColor='#ded0b8',
                    fog='#deded5', fogDensity=.0013, rayleigh=.8, turbidity=3.1),
        'overcast': dict(sun=.7, env=.48, bounce=.85, skyBounceColor='#f2efe6', bounceColor='#ddd3c1',
                         fog='#d8d9d5', fogDensity=.0025),
    }
