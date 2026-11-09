"""Portable originals and explicitly calibrated intake contracts."""
import base64
from copy import deepcopy
import hashlib
import io
from pathlib import Path

import ezdxf
from PIL import Image
import pytest

from floorforge.model import DesignError
from floorforge.plan_import import inspect_dxf, import_mapped_dxf
from floorforge.reference_trace import trace_reference, validate_references

ROOT = Path(__file__).resolve().parents[1]


def asset():
    stream = io.BytesIO();Image.new('RGB', (200, 200), 'white').save(stream, format='PNG')
    data = stream.getvalue()
    return {'id': 'reference-test', 'name': 'measured-plan.png', 'kind': 'visual-reference',
            'mimeType': 'image/png', 'sha256': hashlib.sha256(data).hexdigest(),
            'dataUrl': 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')}


def tracing():
    return {'project': {'brief': {'width_mm': 10000, 'depth_mm': 10000}, 'attachments': [asset()]},
            'referenceId': 'reference-test', 'floorId': 'ground', 'originPixels': [0, 0], 'confirmed': True,
            'calibration': {'pixels': [[0, 0], [100, 0]], 'length': 5, 'units': 'm', 'confirmed': True},
            'rooms': [{'id': 'my-living', 'name': 'Living', 'kind': 'living',
                       'polygon': [[10, 10], [90, 10], [90, 90], [10, 90]]}]}


def test_original_reference_bytes_verified_and_preserved():
    reference = asset()
    assert validate_references([reference]) > 0
    request = tracing();before = deepcopy(request)
    result = trace_reference(request)
    assert request == before
    assert result['project']['attachments'][0]['dataUrl'] == reference['dataUrl']
    assert result['project']['customPlan']['floors'][0]['rooms'][0]['polygon'] == [[500, 500], [4500, 500], [4500, 4500], [500, 4500]]
    assert result['status'] == 'traced-unvalidated'
    assert result['project']['attachments'][0]['calibration']['mmPerPixel'] == 50


@pytest.mark.parametrize('scale', [0.25, 0.5, 2, 4, 10])
def test_calibration_is_independent_of_screen_or_image_pixel_scale(scale):
    original = tracing();scaled = deepcopy(original)
    scaled['calibration']['pixels'] = [[x * scale, y * scale] for x, y in scaled['calibration']['pixels']]
    scaled['rooms'][0]['polygon'] = [[x * scale, y * scale] for x, y in scaled['rooms'][0]['polygon']]
    assert trace_reference(original)['project']['customPlan'] == trace_reference(scaled)['project']['customPlan']


@pytest.mark.parametrize('mutation', ['unconfirmed', 'no-scale', 'bad-hash', 'missing-image', 'zero-length'])
def test_image_does_not_imply_trusted_measurements(mutation):
    request = tracing()
    if mutation == 'unconfirmed':request['confirmed'] = False
    elif mutation == 'no-scale':request['calibration'].pop('confirmed')
    elif mutation == 'bad-hash':request['project']['attachments'][0]['sha256'] = '0' * 64
    elif mutation == 'missing-image':request['project']['attachments'][0].pop('dataUrl')
    elif mutation == 'zero-length':request['calibration']['length'] = 0
    with pytest.raises(DesignError):trace_reference(request)


def test_trace_cannot_overwrite_existing_floor_ownership():
    request = tracing();request['project'] = trace_reference(request)['project']
    with pytest.raises(DesignError, match='empty floor'):trace_reference(request)


def test_dxf_inspection_explains_unsupported_layers_and_mapping():
    text = (ROOT / 'examples/import/ground-floor.dxf').read_text()
    inventory = inspect_dxf(text)
    assert inventory['units'] == 'mm'
    assert inventory['origin'] == [0, 0]
    assert any(layer['name'] == 'FF_PLOT' and layer['supported'] for layer in inventory['layers'])
    mapped = import_mapped_dxf({'text': text, 'filename': 'site.dxf', 'floorId': 'first', 'floorIndex': 1,
                              'floorCount': 3, 'floorIds': ['ground', 'first', 'second'], 'origin': [0, 0]})
    assert mapped['source']['rawText'] == text
    assert mapped['source']['floorIds'] == ['first']
    assert mapped['source']['floorIndices'] == [1]
    floors = mapped['project']['customPlan']['floors']
    assert [floor['id'] for floor in floors] == ['ground', 'first', 'second']
    assert floors[1]['rooms'] and floors[0]['rooms'] == floors[2]['rooms'] == []
    assert mapped['project']['brief']['storeys'] == 3
    assert not mapped['valid'] and mapped['issue']['code'] == 'DXF_FLOORS_PENDING'
    assert mapped['source']['geometry']['floors'] == [floors[1]]
    assert mapped['source']['provenance']['geometry']['floors'] == [floors[1]]
    assert mapped['source']['provenance']['originalGeometry']['floors'][0]['id'] == 'dxf-ground'


@pytest.mark.parametrize('mapping', [
    {'floorIndex': 1, 'floorCount': 1}, {'floorIndex': True}, {'floorCount': 4},
    {'floorCount': 2, 'floorId': 'first'}, {'floorIndex': -1}, {'floorIndex': '1'},
    {'floorCount': 2, 'requestedFloorCount': 3, 'floorIndex': 1},
    {'floorIndex': 1, 'floorCount': 2, 'floorIds': ['ground', 'ground']},
    {'floorIndex': 1, 'floorCount': 2, 'floorIds': ['ground']},
    {'floorIndex': 1, 'floorCount': 2, 'floorIds': ['ground', 'first'], 'floorId': 'renamed'},
])
def test_dxf_floor_mapping_requires_unambiguous_order_and_count(mapping):
    text = (ROOT / 'examples/import/ground-floor.dxf').read_text()
    with pytest.raises(DesignError):
        import_mapped_dxf({'text': text, **mapping})


def test_dxf_mapped_entity_identity_is_repeatable_and_disjoint_between_floors():
    text = (ROOT / 'examples/import/ground-floor.dxf').read_text()
    body = {'text': text, 'floorCount': 2, 'floorIds': ['ground', 'first'], 'floorIndex': 0}
    before = deepcopy(body)
    ground = import_mapped_dxf(body)
    again = import_mapped_dxf(body)
    first = import_mapped_dxf({**body, 'floorIndex': 1})
    assert body == before
    assert ground['source'] == again['source']
    def objects(result):
        floor = result['source']['geometry']['floors'][0]
        return floor['rooms'] + floor['walls'] + floor['openings']
    ground_ids = {obj['id'] for obj in objects(ground)}
    first_ids = {obj['id'] for obj in objects(first)}
    assert not ground_ids & first_ids
    for result in (ground, first):
        floor = result['source']['geometry']['floors'][0]
        room_ids = {room['id'] for room in floor['rooms']}
        assert all(opening['roomId'] in room_ids for opening in floor['openings'])
        original = result['source']['provenance']['originalGeometry']['floors'][0]
        assert [room['polygon'] for room in floor['rooms']] == [room['polygon'] for room in original['rooms']]
        assert [opening['kind'] for opening in floor['openings']] == [opening['kind'] for opening in original['openings']]
    # Imported originals cannot be changed through the editable placeholder draft.
    ground['project']['customPlan']['floors'][0]['rooms'][0]['polygon'][0][0] += 100
    assert ground['source']['geometry'] == again['source']['geometry']


def test_dxf_mapped_partial_plan_retains_source_validation_scope():
    text = (ROOT / 'examples/import/ground-floor.dxf').read_text()
    result = import_mapped_dxf({'text': text, 'requestedFloorCount': 3, 'floorIndex': 2, 'floorId': 'second'})
    assert result['sourceValidation']['valid']
    assert not result['valid'] and 'review' not in result
    assert result['status'] == 'mapped-unvalidated'
    assert result['source']['floorIndices'] == [2]
    assert result['source']['requestedFloorCount'] == 3
    assert result['issue']['details']['pendingFloorIndices'] == [0, 1]
    assert any('FF_ENTRY' in note for note in result['notes'])


@pytest.mark.parametrize('reverse', [False, True])
def test_independent_dxf_sources_merge_by_physical_level_without_renaming(reverse):
    from floorforge.design_journey import resolve_sources
    text = (ROOT / 'examples/import/ground-floor.dxf').read_text()
    mapped = [import_mapped_dxf({'text': text, 'floorIndex': index, 'floorCount': 3,
                                'floorIds': ['ground', 'first', 'second']}) for index in (0, 1)]
    sources = [result['source'] for result in mapped]
    brief = mapped[0]['project']['brief']
    plot = {'id': 'plot', 'kind': 'plot', 'enabled': True, 'units': 'mm',
            'values': {key: brief[key] for key in ('width_mm', 'depth_mm', 'storeys', 'road_bearing_deg')}}
    project = {'designJourney': {'schema': 'myverandah.journey/1', 'inputs':
                                [plot, *(reversed(sources) if reverse else sources)]}}
    before = deepcopy(project)
    resolved = resolve_sources(project)
    assert project == before
    assert not any(question['code'] == 'LAYOUT_AUTHORITY' for question in resolved['questions'])
    floors = resolved['project']['customPlan']['floors']
    assert [floor['id'] for floor in floors] == ['ground', 'first', 'second']
    assert floors[0] == sources[0]['geometry']['floors'][0]
    assert floors[1] == sources[1]['geometry']['floors'][0]
    assert floors[2]['rooms'] == []
    assert resolved['project']['brief']['storeys'] == 3


def test_sequential_dxf_editor_import_keeps_earlier_level_authority():
    from floorforge.design_journey import resolve_sources
    text = (ROOT / 'examples/import/ground-floor.dxf').read_text()
    mapped = [import_mapped_dxf({'text': text, 'floorIndex': index, 'floorCount': 3,
                                'floorIds': ['ground', 'first', 'second']}) for index in (0, 1)]
    project = deepcopy(mapped[1]['project'])
    project['editorState'] = {'mode': 'custom', 'homeInputs': ['plot', 'dxf']}
    project['designJourney'] = {'schema': 'myverandah.journey/1', 'enabledInputs': ['plot', 'dxf'],
                               'imports': [deepcopy(result['source']) for result in mapped]}
    result = resolve_sources(project)
    assert not any(question['code'] == 'LAYOUT_AUTHORITY' for question in result['questions'])
    floors = result['project']['customPlan']['floors']
    assert floors[0] == mapped[0]['source']['geometry']['floors'][0]
    assert floors[1] == mapped[1]['source']['geometry']['floors'][0]
    assert floors[2]['rooms'] == []


def test_unitless_dxf_requires_explicit_unit_choice():
    document = ezdxf.readfile(ROOT / 'examples/import/ground-floor.dxf');document.units = 0
    stream = io.StringIO();document.write(stream)
    assert inspect_dxf(stream.getvalue())['units'] == 'unknown'
    with pytest.raises(DesignError, match='Select drawing units'):
        import_mapped_dxf({'text': stream.getvalue()})
    assert import_mapped_dxf({'text': stream.getvalue(), 'units': 'mm'})['valid']


def test_dxf_cannot_silently_change_origin_or_claim_pdf_support():
    text = (ROOT / 'examples/import/ground-floor.dxf').read_text()
    with pytest.raises(DesignError, match='origin'):
        import_mapped_dxf({'text': text, 'origin': [100, 200]})
    with pytest.raises(DesignError, match='DWG and PDF'):
        inspect_dxf(text, 'plan.pdf')


def test_tracing_one_floor_retains_all_requested_floors_and_explicit_floor_index():
    request = tracing()
    request['project']['brief']['storeys'] = 3
    request['floorId'] = 'first'
    request['floorIndex'] = 1
    before = deepcopy(request)
    result = trace_reference(request)['project']
    assert request == before
    assert result['brief']['storeys'] == 3
    floors = result['customPlan']['floors']
    assert len(floors) == 3
    assert floors[1]['id'] == 'first' and floors[1]['rooms'][0]['id'] == 'my-living'
    assert floors[0]['rooms'] == floors[2]['rooms'] == []


def test_multifloor_trace_never_guesses_an_unknown_floor_identity():
    request = tracing()
    request['project']['brief']['storeys'] = 3
    request['floorId'] = 'first'
    with pytest.raises(DesignError) as caught:
        trace_reference(request)
    assert caught.value.code == 'TRACE_FLOOR_MAPPING'


def test_tracing_preserves_saved_inactive_exact_floors_and_other_room_geometry():
    request = tracing()
    prior = trace_reference(request)['project']['customPlan']
    original_room = deepcopy(prior['floors'][0]['rooms'][0])
    prior['floors'].extend([{'id': 'first', 'rooms': [], 'walls': [], 'openings': []},
                            {'id': 'second', 'rooms': [], 'walls': [], 'openings': []}])
    request['project']['editorState'] = {'mode': 'compass', 'customPlan': prior}
    request['project']['brief']['storeys'] = 3
    request['floorId'] = 'first'; request['floorIndex'] = 1
    request['rooms'][0]['id'] = 'upper-living'
    result = trace_reference(request)['project']
    assert [f['id'] for f in result['customPlan']['floors']] == ['ground', 'first', 'second']
    assert result['customPlan']['floors'][0]['rooms'][0] == original_room
    assert result['customPlan']['floors'][1]['rooms'][0]['id'] == 'upper-living'
    assert result['editorState']['customPlan'] == prior
    # The source exact draft remains saved; it was not silently overwritten.
    assert result['brief']['storeys'] == 3


def test_trace_uses_saved_compass_floor_identities_without_replacing_compass():
    from test_compass_grids import grid_project
    project, compass = grid_project(4, 4, 3)
    request = tracing()
    request['project'] = {**project, 'compass': compass, 'attachments': [asset()]}
    request['floorId'] = compass['floors'][2]['id'];request['floorIndex'] = 2
    result = trace_reference(request)['project']
    assert result['compass'] == compass
    assert len(result['customPlan']['floors']) == result['brief']['storeys'] == 3
    assert [f['id'] for f in result['customPlan']['floors']] == [f['id'] for f in compass['floors']]
    assert result['customPlan']['floors'][2]['rooms']
    assert not result['customPlan']['floors'][0]['rooms']
    request['floorIndex'] = 0
    with pytest.raises(DesignError) as caught:trace_reference(request)
    assert caught.value.code == 'TRACE_FLOOR_MAPPING'


def test_trace_registered_input_is_not_ignored_or_silently_substituted():
    from floorforge.design_journey import resolve_sources
    request = tracing()
    request['floorId'] = 'first';request['floorIndex'] = 1
    request['project']['designJourney'] = {'schema': 'myverandah.journey/1', 'inputs': [
        {'id': 'plot', 'kind': 'plot', 'enabled': True, 'units': 'mm',
         'values': {'width_mm': 10000, 'depth_mm': 10000, 'storeys': 3, 'road_bearing_deg': 180}}]}
    original_inputs = deepcopy(request['project']['designJourney']['inputs'])
    result = trace_reference(request)['project']
    assert result['brief']['storeys'] == 3
    assert result['designJourney']['inputs'][:-1] == original_inputs
    traced = result['designJourney']['inputs'][-1]
    assert traced['kind'] == 'plan' and traced['provenance']['referenceId'] == 'reference-test'
    resolved = resolve_sources(result)
    assert resolved['project']['customPlan'] == result['customPlan']
    assert resolved['project']['customPlan']['floors'][1]['rooms']


def test_trace_can_fill_a_requested_missing_upper_floor_without_changing_ground():
    request = tracing();project = trace_reference(request)['project']
    original_ground = deepcopy(project['customPlan']['floors'][0])
    project['brief']['storeys'] = 3
    request.update(project=project, floorId='first', floorIndex=1)
    request['rooms'][0]['id'] = 'first-living'
    result = trace_reference(request)['project']
    assert result['customPlan']['floors'][0] == original_ground
    assert [len(f['rooms']) for f in result['customPlan']['floors']] == [1, 1, 0]
    assert result['brief']['storeys'] == 3
