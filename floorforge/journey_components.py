"""Small authored material modules; no layout or component-coordinate recipes.

All dimensions reported here come from the current building or generated
furniture. Material texture repeats are in metres, matching the existing viewer.
"""
from __future__ import annotations

from copy import deepcopy

from .model import DesignError, sha

DEFAULTS = {'kitchen': 'soft-white', 'furniture': 'linen', 'facade': 'warm-plaster'}
OPTIONS = {
    'kitchen': {'label': 'Kitchen fronts & counter', 'choices': [
        {'id': 'soft-white', 'label': 'Soft white', 'description': 'Soft white cabinet fronts and a pale stone counter.'},
        {'id': 'timber', 'label': 'Timber', 'description': 'Timber cabinet fronts and the same pale stone counter.'}]},
    'furniture': {'label': 'Furniture upholstery', 'choices': [
        {'id': 'linen', 'label': 'Natural linen', 'description': 'Warm neutral upholstery on the fitted furniture.'},
        {'id': 'sage', 'label': 'Sage fabric', 'description': 'Muted green upholstery on the same furniture.'}]},
    'facade': {'label': 'Facade & wall finish', 'choices': [
        {'id': 'warm-plaster', 'label': 'Warm plaster', 'description': 'Warm pale plaster on the shared exterior and interior wall material.'},
        {'id': 'earth-render', 'label': 'Earth render', 'description': 'Muted earth plaster on the same wall surfaces; no new architectural pieces.'}]},
}


def normalize_components(appearance):
    components = appearance.get('components', {})
    if not isinstance(components, dict) or set(components) - set(OPTIONS):
        raise DesignError('APPEARANCE_REVIEW', 'Only material modules are supported here. Architectural changes require a new 2D review.')
    result = dict(DEFAULTS)
    if appearance.get('preset') == 'earth-verandah':
        result.update(kitchen='timber', furniture='sage', facade='earth-render')
    for group, choice in components.items():
        if choice not in {item['id'] for item in OPTIONS[group]['choices']}:
            raise DesignError('APPEARANCE_REVIEW', 'Choose a supported finish module. Component size or architecture changes return to 2D review.')
        result[group] = choice
    return result


def catalogue(building, scene=None):
    rooms = building.get('spaces', [])
    kitchen_ids = {r['id'] for r in rooms if r['kind'] == 'kitchen'}
    result = []
    for group, definition in OPTIONS.items():
        compatible = bool(kitchen_ids) if group == 'kitchen' else bool(rooms)
        if scene is not None and group == 'kitchen':
            compatible = compatible and any(n['material'] in ('cabinet', 'counter') for n in scene.get('nodes', []))
        dimensions = []
        if scene is not None and group in ('kitchen', 'furniture'):
            for item in scene.get('furniture', []):
                is_kitchen = item['room_id'] in kitchen_ids
                if (group == 'kitchen') != is_kitchen:
                    continue
                points = item['footprint']
                dimensions.append({'id': item['id'], 'roomId': item['room_id'], 'kind': 'component-footprint',
                    'width_mm': round((max(p[0] for p in points) - min(p[0] for p in points)) * 1000, 1),
                    'depth_mm': round((max(p[1] for p in points) - min(p[1] for p in points)) * 1000, 1)})
        else:
            for room in rooms:
                if group == 'kitchen' and room['id'] not in kitchen_ids:
                    continue
                if group == 'facade':
                    continue
                points = room.get('clear') or room['polygon']
                dimensions.append({'roomId': room['id'], 'label': room['name'], 'kind': 'room-envelope',
                    'width_mm': round(max(p[0] for p in points) - min(p[0] for p in points), 1),
                    'depth_mm': round(max(p[1] for p in points) - min(p[1] for p in points), 1)})
        result.append({'id': group, **deepcopy(definition), 'compatible': compatible,
            'reason': ('Available on the existing fitted geometry; sizes and clearances stay unchanged.' if compatible else
                       'No compatible kitchen fronts or counter were generated for these rooms.' if group == 'kitchen' and scene is not None else
                       'Add a kitchen in 2D before choosing kitchen finishes.' if group == 'kitchen' else 'No compatible rooms yet.'),
            'geometryEffect': 'none', 'dimensions': dimensions,
            'dimensionNote': 'Room envelope, not a proposed cabinet size.' if scene is None else 'Actual generated component footprint in millimetres.'})
    return result


def apply_components(scene, appearance, building):
    """Return a scene with whitelisted material updates and unchanged geometry."""
    selected = normalize_components(appearance)
    compatibility = catalogue(building, scene)
    result = {**scene, 'materials': deepcopy(scene['materials'])}
    if appearance.get('preset') is not None:
        from .design_journey import PRESETS
        from .exterior import get_exterior_theme, get_interior_theme
        from .scene_kit import material_library
        from .model import STYLES
        preset = PRESETS.get(appearance['preset'])
        if preset is None:
            raise DesignError('APPEARANCE_REVIEW', 'Choose one of the three compatible material presets.')
        theme_id = preset['exterior_theme']
        theme = get_exterior_theme(theme_id)
        facade_style = {'warm_modern_minimal': 'minimal', 'modern_tropical': 'minimal',
                        'tropical_verandah': 'tropical', 'earth_terracotta': 'terracotta'}[theme_id]
        palette = material_library({**STYLES[facade_style], **theme.get('materials', {})},
                                   get_interior_theme(preset['interior_theme']), theme_id == 'modern_tropical')
        # Only material records cross this boundary. No theme-specific scene
        # generator, furniture recipe or sample metadata is invoked.
        for material_id in result['materials'].keys() & palette.keys():
            result['materials'][material_id] = deepcopy(palette[material_id])
    recipes = {
        'kitchen': {
            'soft-white': {'cabinet': {'color': '#e7e2d8', 'roughness': .45, 'metallic': 0, 'kind': 'metal', 'texture': 'metal', 'params': [.42], 'tile_m': 1.2},
                           'counter': {'color': '#ede9df', 'alt': '#b2aaa0', 'roughness': .24, 'kind': 'marble', 'texture': 'stone', 'tile_m': 1.2}},
            'timber': {'cabinet': {'color': '#a77b50', 'roughness': .47, 'metallic': 0, 'kind': 'wood', 'texture': 'wood', 'params': [], 'tile_m': 1.2},
                       'counter': {'color': '#ede9df', 'alt': '#b2aaa0', 'roughness': .24, 'kind': 'marble', 'texture': 'stone', 'tile_m': 1.2}}},
        'furniture': {
            'linen': {'fabric': {'color': '#ded5bf', 'roughness': .99, 'kind': 'fabric', 'texture': 'fabric', 'tile_m': 1.0},
                      'fabric-dark': {'color': '#8b8273', 'roughness': .96, 'kind': 'fabric', 'texture': 'fabric', 'tile_m': 1.0}},
            'sage': {'fabric': {'color': '#9fae95', 'roughness': .99, 'kind': 'fabric', 'texture': 'fabric', 'tile_m': 1.0},
                     'fabric-dark': {'color': '#647b63', 'roughness': .96, 'kind': 'fabric', 'texture': 'fabric', 'tile_m': 1.0}}},
        'facade': {
            'warm-plaster': {'wall': {'color': '#e5ddc9', 'roughness': .88, 'kind': 'render', 'texture': 'plaster', 'tile_m': 2.0}},
            'earth-render': {'wall': {'color': '#c5ac91', 'roughness': .9, 'kind': 'render', 'texture': 'plaster', 'tile_m': 2.0}}},
    }
    ledger = []
    used = {node['material'] for node in scene.get('nodes', [])}
    for group, option in selected.items():
        available = next(c['compatible'] for c in compatibility if c['id'] == group)
        changed = []
        if available:
            for material_id, values in recipes[group][option].items():
                if material_id in result['materials'] and material_id in used:
                    result['materials'][material_id].update(values)
                    changed.append(material_id)
        ledger.append({'module': group, 'choice': option, 'status': 'applied' if changed else 'reference-only',
                       'materialIds': changed, 'geometryEffect': 'none'})
    result['appearanceComponents'] = {'schema': 'myverandah.material-modules/1', 'selection': selected,
                                      'preset': appearance.get('preset'),
                                      'hash': sha(selected), 'ledger': ledger, 'catalogue': compatibility}
    return result
