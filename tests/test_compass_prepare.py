"""Draw-first preparation must be reversible and reach the real shared pipeline."""
import copy
import json
from pathlib import Path

import pytest

from floorforge.compass_api import dispatch
from floorforge.compass_adapter import proposal
from floorforge.compass_input import microcells, normalize
from floorforge.compass_prepare import prepare
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from floorforge.review import validate, reports
from floorforge.scene import make_scene
from floorforge.drawings import plan_elements
from test_compass_grids import SHAPES
from test_compass_splits import mixed_project


def starter(cols=4, rows=4):
    project = {'schema': 'floorforge.project/0.5', 'brief': {
        'title': 'Draw first', 'width_mm': 12192, 'depth_mm': 18288,
        'front_mm': 3000, 'rear_mm': 1200, 'left_mm': 1000, 'right_mm': 1000,
        'storeys': 1, 'bedrooms': 7, 'roof_access': False}}
    draft = {'schema': 'floorforge.compass-input/2', 'grid': {
        'rows': rows, 'cols': cols, 'basis': 'buildable-envelope', 'rowOrigin': 'front'},
        'floors': [{'id': 'ground', 'splits': [], 'horizontalSplits': []}],
        'rooms': [{'id': 'living', 'name': 'Living', 'kind': 'living',
                   'floorId': 'ground', 'regions': ['0:0']}],
        'connections': [], 'stairLinks': [], 'site': {}, 'requirements': []}
    return project, draft


def accepted(project, result):
    return {**project, 'compass': result['candidate'], 'compassScope': result['scope'],
            'compassAcceptance': {k: result[k] for k in ('sourceHash', 'adapterVersion')},
            'editorState': {'mode': 'compass', 'homeInputs': ['plot', 'compass', 'survey', 'text'],
                            'compassDraft': result['candidate'], 'compassScope': result['scope'],
                            'guideFloors': [[[''] * 4 for _ in range(4)] for _ in range(3)]}}


@pytest.mark.parametrize('cols,rows', SHAPES)
@pytest.mark.parametrize('axis,half', [('splits', 'L'), ('horizontalSplits', 'F')])
def test_small_room_fits_unused_space_with_each_grid_and_split_axis(cols, rows, axis, half):
    project, draft = starter(cols, rows)
    draft['floors'][0][axis] = ['0:0']
    draft['rooms'][0]['regions'] = ['0:0:' + half]
    original = copy.deepcopy(draft)
    result = dispatch('/api/compass/prepare', {'project': project, 'compass': draft})
    assert result['valid'], result['issues']
    assert result['adjustments'][0]['code'] == 'GROW_INTO_EMPTY'
    candidate = result['candidate']
    assert candidate['floors'] == original['floors']
    assert candidate['rooms'][0]['id'] == 'living'
    assert candidate['rooms'][0]['kind'] == 'living'
    assert microcells(original['rooms'][0]['regions'], rows, cols) < microcells(candidate['rooms'][0]['regions'], rows, cols)
    assert draft == original
    assert normalize(candidate)
    reopened = json.loads(json.dumps(accepted(project, result)))
    intent = fuse(reopened)
    building = generate_layout(intent)
    checked = validate(building)
    assert checked['errors'] == []
    scene = make_scene(building, reports(building, checked))
    elements, _ = plan_elements(building, scene, 0)
    assert any(e.get('text') == 'LIVING' for e in elements)
    assert scene['planHash'] == building['planHash'] == intent['planHash']
    assert scene['rooms'][0]['kind'] == 'living'
    assert fuse(reopened)['planHash'] == fuse(accepted(project, result))['planHash']


def test_fitting_keeps_occupied_neighbour_and_dimensions_locked():
    project, draft = starter()
    project['brief']['width_mm'] = 13000
    draft['rooms'].append({'id': 'store', 'kind': 'store', 'name': 'Store',
                           'floorId': 'ground', 'regions': ['0:1']})
    original = copy.deepcopy(draft)
    result = prepare(project, draft)
    assert result['valid'], result['issues']
    rooms = {r['id']: r for r in result['candidate']['rooms']}
    assert rooms['store'] == original['rooms'][1]
    assert rooms['living']['regions'] == ['0:0', '1:0']
    draft['rooms'][0]['target'] = {'width': 2360.5, 'depth': 3334.5, 'locked': True}
    locked = prepare(project, draft)
    assert not locked['valid'] and not locked['adjustments']
    assert locked['candidate']['rooms'] == normalize(draft)['rooms']


def test_full_grid_never_steals_regions_to_make_an_impossible_room_fit():
    project, draft = starter()
    draft['rooms'].append({'id': 'hall', 'kind': 'hall', 'name': 'Hall', 'floorId': 'ground',
                           'regions': [f'{r}:{c}' for r in range(4) for c in range(4) if (r, c) != (0, 0)]})
    before = copy.deepcopy(draft)
    result = prepare(project, draft)
    assert not result['valid']
    assert any(i['code'] == 'ROOM_MINIMUM' for i in result['issues'])
    assert not result['adjustments']
    assert result['candidate']['rooms'] == normalize(draft)['rooms']
    assert draft == before


def test_trailing_empty_floors_generate_now_and_survive_reopen():
    project, draft = starter()
    project['brief']['storeys'] = 3
    draft['floors'] += [{'id': 'first', 'splits': []}, {'id': 'second', 'splits': []}]
    draft['rooms'].append({'id': 'later', 'kind': 'bedroom', 'name': 'Bedroom later',
                           'floorId': 'second', 'regions': [], 'required': True})
    result = prepare(project, draft, 3)
    assert result['valid'], result['issues']
    assert result['scope'] == 1
    assert any(c['code'] == 'DRAWN_FLOORS' for c in result['adjustments'])
    reopened = json.loads(json.dumps(accepted(project, result)))
    assert len(reopened['compass']['floors']) == 3
    assert next(r for r in reopened['compass']['rooms'] if r['id'] == 'later') == draft['rooms'][-1]
    assert fuse(reopened)['values']['storeys'] == 1
    assert fuse(reopened)['compassFullValues']['storeys'] == 3


@pytest.mark.parametrize('cols,rows', SHAPES)
@pytest.mark.parametrize('scope', [1, 2, 3])
def test_valid_mixed_floor_plans_remain_exact_without_fitting(cols, rows, scope):
    project, draft = mixed_project(cols, rows, drawn=True)
    before = copy.deepcopy(draft)
    exact = proposal(project, draft, scope)
    result = prepare(project, draft, scope)
    assert result['valid'], result['issues']
    assert not result['adjustments']
    assert result['customPlan'] == exact['customPlan']
    assert result['sourceHash'] == exact['sourceHash']
    assert result['candidate'] == normalize(before)
    assert draft == before


def test_corrupt_ownership_is_not_repaired_by_discarding_user_rooms():
    project, draft = starter()
    draft['rooms'].append({**draft['rooms'][0], 'id': 'another'})
    before = copy.deepcopy(draft)
    with pytest.raises(DesignError, match='only one room'):
        prepare(project, draft)
    assert draft == before


def test_prepared_geometry_exports_share_the_accepted_input_hash(tmp_path):
    from floorforge.pipeline import run
    project, draft = starter()
    # A sample reference must not replace authored Compass dimensions or rooms.
    project['attachments'] = [{'name': 'Sample inspiration', 'kind': 'image/png', 'sha256': 'a' * 64, 'note': 'Room style reference'}]
    result = prepare(project, draft)
    payload = json.loads(json.dumps(accepted(project, result)))
    built = run(payload, tmp_path)
    directory = Path(built['path'])
    expected = fuse(payload)['planHash']
    for name in ('building.json', 'scene.json', 'review.json', 'report.json'):
        assert json.loads((directory / name).read_text())['planHash'] == expected
    building = json.loads((directory / 'building.json').read_text())
    assert building['brief']['width_mm'] == 12192
    assert [(s['id'], s['kind']) for s in building['spaces']] == [('living', 'living')]
    for name in ('drawings.pdf', 'floorplans.dxf', 'model.glb', 'model.ifc', 'project.floorforge.json'):
        assert (directory / name).stat().st_size > 0
