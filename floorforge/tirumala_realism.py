"""Presentation-only Tirumala 4 refinements from the owner's site references.

All dimensions, openings, collision geometry and approved room layouts are retained.
Off-plot dimensions remain visual estimates unless explicitly supplied by the owner.
"""

from __future__ import annotations

import math


def refine_realism(scene: dict) -> None:
    scene['realismRefinement'] = {
        'revision': 'site-reference-and-material-review-2026-11-03',
        'geometryChanged': False,
        'video': {'name': 'tirumala_plot.mp4', 'duration_s': 23.36,
                  'review': 'sampled chronological pan, alongside annotated stills'},
        'confirmed': ['40 ft north–south × 50 ft east–west plot',
                      '12 m north road; 9 m east road',
                      'garden north; screened court east',
                      'vacant immediately adjoining south and west land'],
        'estimated': ['camera positions and bearings', 'garden depth and planting positions',
                      'court dimensions, hidden markings and hoop', 'distant building positions'],
        'referenceNotes': 'R11 annotations share one source; R08 crops share one source. '
                          'R09/R13 junction heading is unconfirmed. Cars are temporary.',
    }
    mats = scene['materials']
    mats['t4-chainlink'] = dict(kind='shade-net', color='#aeb7ae', spacing=.065,
                              wire=.0026, diagonal=True, doubleSided=True, metallic=.35)
    mats['t4-garden-timber'] = dict(kind='wood', color='#71503b', alt='#9a7955',
                                   seed=38, normal=.22, roughness_scale=.85)
    mats['t4-garden-urn'] = dict(kind='stone', color='#82583d', alt='#a47b50',
                                normal=.35, seed=37, roughness_scale=.95)
    mats['t4-colony-road'].update(normal=.30, color='#bdb9ae', roughness_scale=1.05)
    mats['t4-colony-turf'].update(color='#536b39', alt='#798957', normal=.45)
    mats['ivory-marble-polished'].update(color='#f0e8da', alt='#d5c8b4',
                                       normal=.075, roughness_scale=.72,
                                       env=.75, clearcoat=.10, clearcoat_roughness=.3)
    for name in ('oak', 'oak-warm'):
        mats[name].update(color='#9d7854', alt='#c2a37d', normal=.22, roughness_scale=.82)
    mats['counter'].update(clearcoat=.16, clearcoat_roughness=.3, roughness_scale=.72, normal=.12)
    mats['wall'].update(normal=.20, roughness_scale=.97)
    mats['ceiling'].update(normal=.12)
    mats['linen'].update(color='#e9e0d0', sheen=.35, normal=.30)
    # Fine joinery reveals and inset pulls make the existing cabinets readable at
    # human scale, without changing their carcasses or the L-counter footprint.
    def joinery_box(name, bounds, material):
        x0,y0,z0,x1,y1,z1 = bounds
        scene['nodes'].append(dict(id=name,owner=name,asset='unit-box',floor=0,role='decor',
            material=material,position=[(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],
            scale=[x1-x0,y1-y0,z1-z0],rotation=[0,0,0],collide=False))
    for i in range(4):
        x=3.02+i*.54
        joinery_box(f't4-base-east-joint-{i}',[x,2.264,.10,x+.003,2.267,.84],'t4-shadow-line')
        joinery_box(f't4-base-east-pull-{i}',[x+.15,2.266,.76,x+.37,2.272,.774],'t4-shadow-line')
    for i in range(3):
        y=2.28+i*.53
        joinery_box(f't4-base-store-joint-{i}',[3.0068,y,.10,3.0098,y+.003,.84],'t4-shadow-line')
        joinery_box(f't4-base-store-pull-{i}',[3.009,y+.15,.76,3.015,y+.37,.774],'t4-shadow-line')
    for i,y in enumerate([2.20,3.675]):
        joinery_box(f't4-upper-pull-{i}',[2.78,y-.10,1.51,2.786,y+.10,1.524],'t4-shadow-line')
    joinery_box('t4-upper-door-reveal',[2.78,2.1985,1.48,2.783,2.2015,2.28],'t4-shadow-line')
    scene['presentation']['interior'].update(exposureScale=1.0, contrast=1.04, punch=.18,
                                             vignette=.07, warmth=.10, dayLampLevel=.24)
    scene['presentation']['exterior'].update(contrast=1.025, warmth=.07, punch=.17)
    scene['presentation']['shadowContext'] = dict(center=[16, -1, 0], radiusM=43)
    scene['presentation']['lighting']['day'].update(sun=3.3, env=.30, bounce=.65,
        skyBounceColor='#f5f4eb', bounceColor='#d8d0bd', turbidity=2.8)
    scene['presentation']['lighting']['overcast'].update(env=.44, bounce=.70)

    garden = scene['context']['north_colony_garden']
    # N-01 has two rounded ornaments at the pergola, not a row of box planters.
    garden['decorative_pots_scene'] = [dict(position=[25.9, y], radius_m=.37, height_m=.68)
                                       for y in (10.0, 11.35)]
    garden['garden_lights_scene'] = [dict(position=[24.9, 6.7], height_m=3.3),
                                     dict(position=[25.0, 1.3], height_m=2.8)]
    garden['trees_scene'] = [
        dict(species='palm', position=[25.8, 9.0], scale=1.18),
        dict(species='palm', position=[25.9, 3.7], scale=1.25),
        dict(species='tree_shade', position=[30.5, 13.5], scale=1.1),
        dict(species='neem', position=[32.0, -.6], scale=.9),
        dict(species='areca', position=[34.0, 1.8], scale=.65),
        dict(species='shrub_round', position=[34.0, 8.2], scale=1.2),
    ]
    court = scene['context']['east_basketball_court']
    court['screening_trees_scene'] = [
        dict(species=s, position=[x, y], scale=k) for s, x, y, k in [
            ('palm', .1, -9.6, 1.05), ('neem', 2.7, -9.7, .80),
            ('palm', 5.4, -9.65, 1.12), ('neem', 7.8, -9.7, .84),
            ('neem', 10.8, -9.65, .84), ('palm', 14.3, -9.7, 1.12),
            ('neem', 15.0, -13.7, .85), ('palm', 15.0, -18.4, 1.0)]]

    cams = scene['cameras']
    cams['ref_r08_north_garden'].update(position=[18.6, 6.7, 1.33],
        target=[33.4, 6.7, 2.6], fov=57, direction_status='north-confirmed; viewpoint-estimated',
        description='N-01/R08: public north-road viewpoint, clear of the house boundary; camera offset estimated.')
    cams['ref_v01_east_court_road'].update(position=[15.4, -2.4, 1.33],
        target=[8.6, -13.0, 2.5], fov=57, direction_status='east-court-confirmed; viewpoint-estimated')
    cams['ref_r11_ne_corner']['direction_status'] = 'corner-owner-confirmed; camera-bearing-estimated'
    cams['ref_r09_colony_junction']['description'] = 'Illustrative colony road depth; R09/R13 exact heading and building offsets unconfirmed.'
    cams['ref_n03_north_frontage'] = dict(position=[19.5,7.5,1.33],target=[7.0,7.5,2.3],
        fov=62,description='N-03: from the north road facing south toward the proposed house. Estimated viewpoint.')
    cams['ref_n02_northwest_utilities'] = dict(position=[18.0,13.0,1.33],target=[11.5,17.5,1.1],
        fov=60,description='N-02: northwest feeder cabinets and vacant adjoining land; offsets estimated.')
    cams['ref_south_vacant'] = dict(position=[-5.5,-5,1.33],target=[3,6,2.5],fov=62,
        description='South-side vacant grass plot and east approach; vacant condition owner-confirmed.')
    cams['ref_west_vacant'] = dict(position=[5.5,24,1.33],target=[5.5,11,2.5],fov=62,
        description='Rear elevation from the vacant west plot; no invented adjoining house.')
    # Same verified standing point, now actually looking across kitchen and dining.
    cam = cams['interior_kitchen_living_dining']
    cam['target'] = [2.9, 3.4, 1.35]
    dx, dy, dz = [cam['target'][i] - cam['position'][i] for i in range(3)]
    cam['walker']['yaw_rad'] = math.atan2(-dx, dy)
    cam['walker']['pitch_rad'] = math.atan2(dz, math.hypot(dx, dy))
