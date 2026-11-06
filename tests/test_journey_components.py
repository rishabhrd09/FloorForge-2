"""Finish modules must not turn a cosmetic choice into an architectural edit."""
from copy import deepcopy
from itertools import product
import json
from pathlib import Path

import pytest

from floorforge.design_journey import prepare
from floorforge.journey_components import apply_components, catalogue, normalize_components
from floorforge.model import DEFAULTS, DesignError, sha


@pytest.fixture(scope='module')
def material_home():
    from floorforge.scene import make_scene
    p = {'schema': 'floorforge.project/0.5', 'brief': dict(DEFAULTS),
         'designJourney': {'schema': 'myverandah.journey/1', 'enabledInputs': ['plot', 'survey']}}
    result = prepare(p)
    assert result['valid'], result['questions']
    return result['building'], make_scene(result['building'], result['report'])


@pytest.mark.parametrize('kitchen,furniture,facade', product(
    ['soft-white', 'timber'], ['linen', 'sage'], ['warm-plaster', 'earth-render']))
def test_all_material_modules_preserve_nodes_meshes_and_collision(material_home, kitchen, furniture, facade):
    model, scene = material_home
    before = sha(scene)
    chosen = {'components': {'kitchen': kitchen, 'furniture': furniture, 'facade': facade}}
    result = apply_components(scene, chosen, model)
    assert sha(scene) == before
    for key in scene:
        if key != 'materials':
            assert result[key] == scene[key], key
    assert result['appearanceComponents']['selection'] == chosen['components']
    assert all(entry['geometryEffect'] == 'none' for entry in result['appearanceComponents']['ledger'])
    assert result['materials']['asphalt'] == scene['materials']['asphalt']
    assert result['materials']['linen'] == scene['materials']['linen']  # white road markings share this legacy material
    assert result['materials']['fabric']['tile_m'] == 1.0
    assert result['materials']['cabinet']['tile_m'] == 1.2


def test_actual_dimensions_come_from_generated_furniture(material_home):
    model, scene = material_home
    options = catalogue(model, scene)
    all_dims = [d for group in options for d in group['dimensions']]
    assert all(d['kind'] == 'component-footprint' for d in all_dims)
    dimensions = {d['id']: d for d in all_dims}
    for item in scene['furniture']:
        assert item['id'] in dimensions
        points = item['footprint']
        assert dimensions[item['id']]['width_mm'] == round((max(p[0] for p in points)-min(p[0] for p in points))*1000, 1)
        assert dimensions[item['id']]['roomId'] == item['room_id']


def test_pre3d_catalogue_honestly_labels_room_envelopes(material_home):
    model, _ = material_home
    options = catalogue(model)
    assert all(d['kind'] == 'room-envelope' for group in options for d in group['dimensions'])
    assert all('not a proposed cabinet' in group['dimensionNote'] for group in options)


def test_absent_kitchen_cannot_claim_finish_was_applied(material_home):
    model, scene = material_home
    home = deepcopy(model)
    home['spaces'] = [r for r in home['spaces'] if r['kind'] != 'kitchen']
    option = next(x for x in catalogue(home) if x['id'] == 'kitchen')
    assert not option['compatible']
    result = apply_components(scene, {'components': {'kitchen': 'timber'}}, home)
    assert result['materials']['cabinet'] == scene['materials']['cabinet']
    assert next(x for x in result['appearanceComponents']['ledger'] if x['module'] == 'kitchen')['status'] == 'reference-only'


@pytest.mark.parametrize('components', [
    {'facade': 'add-balcony'}, {'kitchen': 'island-2m'}, {'stairs': 'wider'}, [], None,
])
def test_architectural_or_unknown_component_options_return_to_review(components):
    with pytest.raises(DesignError) as error:
        normalize_components({'components': components})
    assert error.value.code == 'APPEARANCE_REVIEW'


def test_material_module_choice_changes_appearance_identity_only():
    path = Path(__file__).resolve().parents[1] / 'examples/custom/g2-terrace.floorforge.json'
    p = json.loads(path.read_text())
    p['designJourney'] = {'schema': 'myverandah.journey/1', 'enabledInputs': ['plot', 'dxf']}
    before = prepare(p)
    p['designJourney']['appearance'] = {'preset': 'warm-natural', 'components': {'furniture': 'sage'}}
    after = prepare(p)
    assert after['valid'] and before['valid']
    assert before['geometryHash'] == after['geometryHash']
    assert before['appearance']['appearanceHash'] != after['appearance']['appearanceHash']
    assert after['appearance']['componentOptions']


def test_all_three_presets_preserve_every_presentation_component():
    from floorforge.scene import make_scene
    result = []
    payloads = []
    for preset in ('warm-natural', 'quiet-modern', 'earth-verandah'):
        p = {'schema': 'floorforge.project/0.5', 'brief': dict(DEFAULTS),
             'designJourney': {'schema': 'myverandah.journey/1', 'enabledInputs': ['plot', 'survey'],
                               'appearance': {'preset': preset}}}
        prepared = prepare(p)
        assert prepared['valid'], prepared['questions']
        payloads.append(prepared['preparedProject'])
        scene = make_scene(prepared['building'], prepared['report'])
        result.append(apply_components(scene, prepared['appearance'], prepared['building']))
    assert payloads[0] == payloads[1] == payloads[2]
    for current in result[1:]:
        for key in ('nodes', 'assets', 'colliders', 'furniture', 'opening_model', 'rooms', 'lights',
                    'walk', 'vegetation', 'lawns', 'cameras', 'bounds', 'footprint'):
            assert current[key] == result[0][key], key
    assert len({sha(current['materials']) for current in result}) == 3
