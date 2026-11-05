"""Opt-in spacious presentation. Never changes architecture or furniture geometry."""
import math

REVISION = 'p12-open-interiors-2026-10-30'


def apply_presentation(scene, building):
    if not building['planning'].get('tirumalaMeta', {}).get('spaciousnessPresentation'):
        return scene
    materials = scene['materials']
    # Keep the approved palette and 24 x 48 inch tile geometry. The tile shader
    # uses two modules per repeat, hence a 2.4384 x 1.2192 m texture repeat.
    for name in ('ivory-marble-polished', 'ivory-marble-exterior-matte', 'ivory-marble-satin-wet'):
        m = materials[name]
        m.update(alt='#e1dacd', normal=.10)
        m['params'] = [2, .0013, .08, .42 if name.endswith('polished') else .18]
    materials['ivory-marble-polished'].update(roughness=.38, clearcoat=.12, clearcoat_roughness=.3)
    materials['ceiling'].update(color='#faf8f2', roughness=.94)
    materials['cabinet'].update(color='#eee8dd', roughness=.58)
    materials['care-upholstery']['color'] = '#e1ded3'
    # Existing room luminaires use a neutral-warm tone. Garden, porch-step and
    # exterior lights retain their prior tones and powers.
    for light in scene['lights']:
        if light['kind'] in ('downlight', 'upper-downlight', 'undercab'):
            light['color'] = '#ffe9ce'
    scene['presentation'] = {
        'revision': REVISION, 'purpose': 'Improve perceived spaciousness at unchanged physical scale',
        'interior': {'dayLampLevel': .24, 'punch': .28, 'contrast': 1.0, 'vignette': .07},
        'geometryScaled': False, 'defaultEyeHeightM': 1.63,
        'notes': ['Continuous ivory floor with quieter veining and grout',
                  'Daytime room lights and neutral-warm ceiling finish',
                  'Existing independent timber, glass and mesh doors remain operable',
                  'Real eye-level views; room and furniture dimensions unchanged'],
    }

    def camera(name, label, position, target, floor=0, fov=64):
        dx, dy, dz = [target[i] - position[i] for i in range(3)]
        scene['cameras'][name] = {
            'id': name, 'label': label, 'position': position, 'target': target, 'fov': fov,
            'enter_walk': True, 'floor': floor, 'eye_height_above_ffl_m': 1.63,
            'walker': {'position': position[:], 'yaw_rad': math.atan2(-dx, dy),
                       'pitch_rad': math.atan2(dz, math.hypot(dx, dy))},
        }

    # Both trial cameras occupy the same unobstructed spots and use identical
    # eye heights and lenses. The former kitchen eye lay inside the moved ICU wall.
    camera('interior_kitchen_living_dining', 'Kitchen to connected dining and living',
           [5.95, 4.2, 1.63], [3.25, 6.85, 1.50])
    camera('interior_icu_veranda_garden', 'ICU to veranda · true eye level',
           [9.5, 7.4, 1.63], [7.65, 4.25, 1.50])
    camera('interior_veranda_living', 'Veranda into living hall',
           [6.05, 2.25, 1.63], [5.8, 7.0, 1.50])
    camera('interior_master', 'Master bedroom · room diagonal',
           [4.7, 9.7, 1.63], [1.5, 13.1, 1.50])
    camera('interior_drawing', 'Drawing room · open furniture-free floor',
           [10.9, 8.6, 1.63], [8.85, 10.85, 1.50])
    if building['planning']['tirumalaOption'] == 'P12-A':
        camera('icu_layered_entry', 'ICU entrance · wood with glass behind',
               [5.85, 7.2012, 1.63], [6.7428, 7.2012, 1.4], fov=62)
    if building['planning']['tirumalaOption'] == 'P11':
        camera('living_double_height', 'Living · double-height gallery',
               [4.8, 5.6, 1.63], [6.8, 8.1, 4.6], fov=68)
        camera('interior_kitchen_living_dining', 'Connected kitchen, living and dining',
               [4.95, 5.3, 1.63], [3.25, 6.85, 1.50])
        camera('interior_icu_veranda_garden', 'P13 ICU · full-size bed and clear circulation',
               [6.3, 2.4, 1.63], [7.7, 5.6, 1.50])
        camera('interior_veranda_living', 'Veranda into living hall',
               [8.3, 7.1, 1.63], [6.3, 7.1, 1.50])
        camera('interior_drawing', 'Drawing room',
               [10.9, 8.6, 1.63], [8.85, 10.85, 1.50])
    scene['cameras']['interior'] = scene['cameras']['interior_kitchen_living_dining']
    return scene
