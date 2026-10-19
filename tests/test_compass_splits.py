"""Both split axes retain authored space through save/reopen and shared geometry."""
import copy
import json
from fractions import Fraction

import pytest
from shapely.geometry import Polygon

from floorforge.compass_input import normalize, microcells, connected, remap, SPLIT_SCHEMA
from floorforge.compass_adapter import proposal
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.scene import make_scene
from floorforge.review import validate, reports
from floorforge.drawings import plan_elements
from floorforge.model import DesignError
from test_compass_grids import SHAPES, grid_project, reviewed


def mixed_project(cols, rows, drawn=False):
    project, compass = grid_project(cols, rows)
    compass['schema'] = SPLIT_SCHEMA
    if drawn:
        compass['programme'] = 'drawn'
        compass['stairLinks'] = []  # Draw-first generation links matching cores.
    for i, floor in enumerate(compass['floors']):
        ref = f'{rows-2}:{cols-2}'
        floor['horizontalSplits'] = [ref]
        route = next(r for r in compass['rooms'] if r['floorId'] == floor['id'] and ref in r['regions'])
        route['regions'].remove(ref)
        route['regions'].append(ref + ':F')
        compass['rooms'].append({'id': f'f{i}-back', 'floorId': floor['id'], 'kind': 'store',
                                 'name': f'Back store {i+1}', 'regions': [ref + ':B'], 'required': True})
    project['editorState']['compassDraft'] = copy.deepcopy(compass)
    return project, compass


@pytest.mark.parametrize('cols,rows', SHAPES)
@pytest.mark.parametrize('scope', [1, 2, 3])
def test_both_split_axes_floors_save_reopen_and_2d_3d(cols, rows, scope, tmp_path):
    project, compass = mixed_project(cols, rows, drawn=True)
    before = copy.deepcopy(compass)
    payload = reviewed(project, compass, scope)
    path = tmp_path / 'mixed.floorforge.json'
    path.write_text(json.dumps(payload))
    reopened = json.loads(path.read_text())
    assert reopened['compass'] == before == reopened['editorState']['compassDraft']
    intent = fuse(reopened)
    assert intent['planHash'] == fuse(payload)['planHash']
    building = generate_layout(intent)
    checked = validate(building)
    assert not checked['errors']
    scene = make_scene(building, reports(building, checked))
    assert scene['planHash'] == building['planHash'] == intent['planHash']
    assert building['storeys'] == scope
    assert sum(s.get('to_floor') is not None for s in building['stairs']) == scope - 1
    for floor in range(scope):
        back = next(s for s in building['spaces'] if s['id'] == f'f{floor}-back')
        x0, y0, x1, y1 = Polygon(back['clear']).bounds
        assert (x1-x0, y1-y0) == pytest.approx((3050, 1550), abs=.01)
        assert y0 == pytest.approx((rows-1.5) * 3400 + 150, abs=.01)
        assert next(r for r in scene['rooms'] if r['id'] == back['id'])['kind'] == 'store'
        elements, _ = plan_elements(building, scene, floor)
        assert any(e.get('text') == back['name'].upper() for e in elements)
    assert compass == before


@pytest.mark.parametrize('bearing', [0, 90, 180, 270])
def test_front_back_geometry_is_road_relative(bearing):
    project, compass = mixed_project(4, 4)
    project['brief']['road_bearing_deg'] = bearing
    result = proposal(project, compass, 1)
    assert result['valid'], result['issues']
    back = next(r for r in result['customPlan']['floors'][0]['rooms'] if r['id'] == 'f0-back')
    assert Polygon(back['polygon']).bounds == pytest.approx((6550, 8650, 9600, 10200))


@pytest.mark.parametrize('cols,rows', SHAPES)
def test_front_half_and_only_drawn_ground_rooms_compile_without_other_steps(cols, rows):
    project, compass = grid_project(cols, rows)
    compass.update(schema=SPLIT_SCHEMA, programme='drawn', stairLinks=[])
    compass['site'].pop('entryRoomId')
    compass['floors'][0]['splits'] = []
    compass['floors'][0]['horizontalSplits'] = ['0:0']
    # Keep the original room requirements and upper-floor drafts for later.
    for room in compass['rooms']:
        if room['floorId'] == 'floor-0':
            room['regions'] = []
    compass['rooms'].extend([
        {'id': 'front-store', 'kind': 'store', 'name': 'Front store', 'floorId': 'floor-0', 'regions': ['0:0:F']},
        {'id': 'drawn-living', 'kind': 'living', 'name': 'Drawn living', 'floorId': 'floor-0',
         'regions': [f'{r}:{c}' for r in range(2) for c in range(cols) if (r, c) != (0, 0)] + ['0:0:B']}])
    project['editorState']['compassDraft'] = copy.deepcopy(compass)
    payload = reviewed(project, compass, 1)
    building = generate_layout(fuse(payload))
    assert not validate(building)['errors']
    assert {r['id'] for r in building['spaces']} == {'front-store', 'drawn-living'}
    assert Polygon(next(r for r in building['spaces'] if r['id'] == 'front-store')['clear']).bounds == pytest.approx((150, 150, 3200, 1700))


@pytest.mark.parametrize('refs,expected', [
    (['0:0:B', '1:0:F'], True), (['0:0:F', '1:0:F'], False),
    (['0:0:F', '0:1:L'], True), (['0:0:F', '1:1:L'], False),
    (['0:0:F', '0:0:B'], True), (['0:0:R', '1:0:F'], True)])
def test_two_axis_edge_adjacency(refs, expected):
    assert connected(refs, 4) is expected


def test_wrong_axis_crossed_partitions_duplicate_ownership_and_old_schema_are_rejected():
    _, compass = mixed_project(4, 4)
    for mutate in (
        lambda c: c['floors'][0]['splits'].append('2:2'),
        lambda c: c['rooms'][-3].update(regions=['2:2:L']),
        lambda c: c['rooms'][0]['regions'].append('2:2:B'),
        lambda c: c.update(schema='floorforge.compass-input/1'),
        lambda c: c['floors'][0]['horizontalSplits'].append('4:0')):
        broken = copy.deepcopy(compass)
        mutate(broken)
        with pytest.raises(DesignError):
            normalize(broken)


def test_drawn_preview_retains_unplaced_rooms_and_upper_drafts_without_checklist_errors():
    project, compass = mixed_project(4, 4, drawn=True)
    compass['rooms'].append({'id': 'later', 'floorId': 'floor-0', 'kind': 'bedroom',
                             'name': 'Bedroom for later', 'required': True, 'regions': []})
    project['brief']['bedrooms'] = 7
    before = copy.deepcopy(compass)
    result = proposal(project, compass, 1)
    assert result['valid'], result['issues']
    assert len(result['customPlan']['floors']) == 1
    assert result['values']['bedrooms'] == 1
    assert any(e['source'] == 'unplaced-rooms' for e in result['effects'])
    intent = fuse(reviewed(project, compass, 1))
    assert next(e for e in intent['input_audit']['entries'] if e['source'] == 'unplaced-rooms')['status'] == 'unapplied'
    assert intent['input_audit']['attention_count'] > 0
    assert compass == before
    strict = copy.deepcopy(compass)
    del strict['programme']
    assert {'UNPLACED', 'BEDROOM_PROGRAMME'} <= {i['code'] for i in proposal(project, strict, 1)['issues']}


def test_empty_floor_and_invalid_small_room_remain_actionable_errors():
    project, compass = mixed_project(4, 4, drawn=True)
    for room in compass['rooms']:
        if room['floorId'] == 'floor-2':
            room['regions'] = []
    assert any(i['code'] == 'EMPTY_FLOOR' for i in proposal(project, compass, 3)['issues'])
    back = next(r for r in compass['rooms'] if r['id'] == 'f0-back')
    back['kind'] = 'bedroom'
    assert any(i['code'] == 'ROOM_MINIMUM' and i['roomId'] == 'f0-back' for i in proposal(project, compass, 1)['issues'])


def test_split_changes_invalidate_acceptance_and_save_pending_drafts():
    project, compass = mixed_project(4, 4)
    payload = reviewed(project, compass, 1)
    changed = copy.deepcopy(payload)
    floor = changed['compass']['floors'][0]
    floor['horizontalSplits'].append('1:1')
    room = next(r for r in changed['compass']['rooms'] if '1:1' in r['regions'])
    room['regions'].remove('1:1')
    room['regions'].extend(['1:1:F', '1:1:B'])
    with pytest.raises(DesignError, match='older map'):
        fuse(changed)
    pending = {**project, 'editorState': {**project['editorState'], 'compassDraft': changed['compass']}}
    assert fuse(json.loads(json.dumps(pending)))


def test_remap_can_use_new_horizontal_halves_without_changing_owner_area():
    _, compass = grid_project(4, 4, 1)
    # Two horizontal bands can be represented exactly on a six-deep grid.
    compass['floors'][0]['splits'] = []
    compass['stairLinks'] = []
    compass['site'].pop('entryRoomId')
    compass['rooms'] = compass['rooms'][:2]
    for i, room in enumerate(compass['rooms']):
        room['regions'] = [f'{r}:{c}' for r in range(i, 4, 2) for c in range(4)]
    # Make each room connected: one front row, three rear rows.
    compass['rooms'][0]['regions'] = [f'0:{c}' for c in range(4)]
    compass['rooms'][1]['regions'] = [f'{r}:{c}' for r in range(1, 4) for c in range(4)]
    result = remap(compass, 6, 4)
    assert result['valid'], result['issues']
    assert result['candidate']['schema'] == SPLIT_SCHEMA
    assert result['candidate']['floors'][0]['horizontalSplits']
    normalize(result['candidate'])
    for before, after in zip(compass['rooms'], result['candidate']['rooms']):
        # normalize sorts IDs, so compare by stable room identity.
        before = next(r for r in compass['rooms'] if r['id'] == after['id'])
        assert Fraction(len(microcells(before['regions'], 4)), 4*4*4) == Fraction(len(microcells(after['regions'], 6)), 4*6*4)


def test_remap_never_silently_replaces_crossed_quarters_or_empty_boundaries():
    _, compass = mixed_project(4, 4)
    before = copy.deepcopy(compass)
    assert remap(compass, 4, 4)['candidate'] == normalize(compass)
    result = remap(compass, 5, 5)
    assert not result['valid']
    assert any(i['code'] in ('REMAP_COLLISION', 'REMAP_BOUNDARY', 'REMAP_PARTITION') for i in result['issues'])
    assert compass == before
