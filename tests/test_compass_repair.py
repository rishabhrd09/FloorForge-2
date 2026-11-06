"""Occupied-map repair is bounded, reversible and validated across all floors."""
import copy
import json

import pytest

from floorforge.compass_adapter import proposal
from floorforge.compass_input import microcells, normalize
from floorforge.compass_prepare import prepare
from floorforge.compass_repair import search, allocation_graph
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from test_compass_grids import grid_project, SHAPES
from test_compass_prepare import starter


def occupied_small_room(axis=None, half=None):
    project, draft = starter()
    if axis:
        draft['floors'][0][axis] = ['0:0']
        draft['rooms'][0]['regions'] = ['0:0:'+half]
    whole = [f'{r}:{c}' for r in range(4) for c in range(4) if (r, c) != (0, 0)]
    if half:
        whole += ['0:0:'+({'L': 'R', 'F': 'B'}[half])]
    draft['rooms'].append({'id': 'hall', 'floorId': 'ground', 'kind': 'hall', 'name': 'Hall', 'regions': whole})
    return project, draft


def misaligned_stairs(cols=4, rows=4):
    project, draft = grid_project(cols, rows, 2)
    draft.update(schema='floorforge.compass-input/2', programme='drawn')
    stair = next(r for r in draft['rooms'] if r['id'] == 'f1-stairs')
    hall = next(r for r in draft['rooms'] if r['id'] == 'f1-hall')
    hall['regions'] = [r for r in hall['regions'] if r not in ['0:1', '1:1']] + stair['regions']
    stair['regions'] = ['0:1', '1:1']
    return project, draft


def assert_preserved(before, candidate):
    assert before['floors'] == candidate['floors']
    assert before['grid'] == candidate['grid']
    assert before['connections'] == candidate['connections']
    assert before['stairLinks'] == candidate['stairLinks']
    assert {(r['id'], r['kind'], r['floorId']) for r in before['rooms']} == {
        (r['id'], r['kind'], r['floorId']) for r in candidate['rooms']}
    rows, cols = before['grid']['rows'], before['grid']['cols']
    for floor in before['floors']:
        def cover(draft):
            return set().union(*(microcells(r['regions'], rows, cols) for r in draft['rooms'] if r['floorId'] == floor['id']))
        assert cover(before) <= cover(candidate)
    assert normalize(candidate)


@pytest.mark.parametrize('axis,half', [(None, None), ('splits', 'L'), ('horizontalSplits', 'F')])
def test_full_grid_repair_returns_reviewable_alternatives_without_taking_ownership(axis, half):
    project, draft = occupied_small_room(axis, half)
    before = copy.deepcopy(draft)
    result = prepare(project, draft)
    assert not result['valid']  # The current map is still invalid; no automatic ownership change.
    assert draft == before
    assert result['candidate']['rooms'] == normalize(before)['rooms']
    assert not result['adjustments']
    assert 1 <= len(result['alternatives']) <= 3
    assert result['applied'] is False
    assert result['question']['recommended'] == result['alternatives'][0]['id']
    assert all(c['occupiedMicrocells'] == c['capacityMicrocells'] for c in result['graph']['floorOccupancy'])
    hashes = set()
    for item in result['alternatives']:
        assert item['requiresExplicitApply'] and item['valid']
        assert item['adjustments']
        assert item['sourceHash'] not in hashes
        hashes.add(item['sourceHash'])
        assert_preserved(normalize(before), item['candidate'])
        assert proposal(project, item['candidate'])['valid']
    assert result['search']['globalOptimality'] is False
    assert result['search']['provenInfeasible'] is False
    assert result['search']['checked'] <= result['search']['maxValidatedCandidates']


@pytest.mark.parametrize('cols,rows', SHAPES)
def test_multifloor_occupied_map_aligns_stairs_and_retains_every_room(cols, rows):
    project, draft = misaligned_stairs(cols, rows)
    before = copy.deepcopy(draft)
    result = prepare(project, draft)
    assert any(p['code'] == 'STAIR_ALIGNMENT' for p in result['issues'])
    assert result['scope'] == 2
    assert result['alternatives'], result['search']
    assert draft == before
    assert all(c['occupiedMicrocells'] == c['capacityMicrocells'] for c in result['graph']['floorOccupancy'])
    best = result['alternatives'][0]
    assert_preserved(normalize(before), best['candidate'])
    # The best local correction repairs the shifted first-floor stair and hall.
    assert {change['roomId'] for change in best['adjustments']} == {'f1-stairs', 'f1-hall'}
    payload = {**project, 'compass': best['candidate'], 'compassScope': 2,
               'compassAcceptance': {key: best[key] for key in ('sourceHash', 'adapterVersion')}}
    reopened = json.loads(json.dumps(payload))
    building = generate_layout(fuse(reopened))
    assert building['storeys'] == 2
    assert len(building['spaces']) == len(draft['rooms'])
    assert not validate(building)['errors']


def test_pinned_positions_never_move_even_in_alternative_proposals():
    project, draft = misaligned_stairs()
    project['designJourney'] = {'pins': {'positions': ['f0-stairs'], 'dimensions': ['f0-kitchen']}}
    result = prepare(project, draft)
    assert result['alternatives']
    for item in result['alternatives']:
        for rid in ('f0-stairs', 'f0-kitchen'):
            assert next(r for r in item['candidate']['rooms'] if r['id'] == rid) == next(r for r in normalize(draft)['rooms'] if r['id'] == rid)


def test_locked_impossible_room_keeps_draft_and_asks_about_pin():
    project, draft = occupied_small_room()
    draft['rooms'][0]['target'] = {'width': 2400, 'depth': 4000, 'locked': True}
    before = copy.deepcopy(draft)
    result = prepare(project, draft)
    assert not result['alternatives']
    assert result['question']['code'] == 'SIZE_LOCK'
    assert result['search']['status'] == 'clarification-required'
    assert not result['search']['provenInfeasible']
    assert draft == before


def test_time_limit_is_not_infeasibility_and_recommendations_are_cached_by_full_input():
    project, draft = occupied_small_room()
    draft.update(programme='drawn')
    initial = proposal(project, draft)
    limited = search(project, draft, initial, max_seconds=0)
    assert limited['search']['status'] == 'time-limit'
    assert limited['search']['checked'] == 0
    assert not limited['search']['provenInfeasible']
    assert not limited['search']['globalOptimality']
    first = search(project, draft, initial)
    again = search(project, draft, initial)
    assert again['search']['cacheHit']
    assert again['alternatives'] == first['alternatives']
    # A caller cannot mutate a cached proposal.
    again['alternatives'].clear()
    assert search(project, draft, initial)['alternatives']
    changed = copy.deepcopy(project)
    changed['brief']['road_bearing_deg'] = 90
    assert not search(changed, draft, proposal(changed, draft))['search']['cacheHit']


def test_missing_stairs_is_one_coupled_question_not_silent_room_insertion():
    project, draft = grid_project(4, 4, 2)
    for room in draft['rooms']:
        if room['kind'] == 'stair':
            room['kind'] = 'store'
    draft['stairLinks'] = []
    result = prepare(project, draft)
    assert not result['valid'] and not result['alternatives']
    assert result['question']['code'] == 'STAIR_LINK'
    assert 'aligned stair' in result['question']['title']
    assert len(result['question']['choices']) == 2
    assert {(r['id'], r['kind']) for r in result['candidate']['rooms']} == {(r['id'], r['kind']) for r in draft['rooms']}


def test_adjacency_graph_discloses_it_is_not_an_access_certificate():
    _, draft = occupied_small_room()
    graph = allocation_graph(normalize(draft))
    assert graph['edges'] == [['hall', 'living']]
    assert graph['doorRoutesRequireCompiler']


def test_position_pin_blocks_even_empty_space_growth():
    project, draft = starter()
    project['designJourney'] = {'pins': {'positions': ['living']}}
    before = copy.deepcopy(draft)
    result = prepare(project, draft)
    assert not result['valid']
    assert not result['adjustments']
    assert not result['alternatives']
    assert draft == before
    assert result['candidate']['rooms'] == normalize(before)['rooms']


def test_internal_bedroom_reaches_daylight_by_reviewable_occupied_boundary_change():
    project, draft = starter()
    project['brief'].update(width_mm=15000, depth_mm=18000)
    draft['rooms'] = [
        {'id': 'bed', 'name': 'Bedroom', 'kind': 'bedroom', 'floorId': 'ground',
         'regions': [f'{r}:{c}' for r in (1, 2) for c in (1, 2)]},
        {'id': 'hall', 'name': 'Hall', 'kind': 'hall', 'floorId': 'ground',
         'regions': [f'{r}:{c}' for r in range(4) for c in range(4) if r not in (1, 2) or c not in (1, 2)]}]
    result = prepare(project, draft)
    assert result['alternatives']
    for option in result['alternatives']:
        assert_preserved(normalize(draft), option['candidate'])
        # The full shared compiler's daylight and privacy checks are required.
        assert option['review']['errors'] == []
        bedroom = next(r for r in option['candidate']['rooms'] if r['id'] == 'bed')
        cells = microcells(bedroom['regions'], 4, 4)
        assert any(y in (0, 7) or x in (0, 7) for y, x in cells)
