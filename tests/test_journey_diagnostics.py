"""Blocked journeys must identify the actual edit, without changing the draft."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from floorforge.compass_adapter import proposal
from floorforge.compass_repair import guided_question
from floorforge.design_journey import SCHEMA, _geometry_question, prepare, resolve_sources
from floorforge.journey_diagnostics import enrich_issues, error_issues
from floorforge.model import DesignError
from test_compass_prepare import starter


@pytest.fixture
def home():
    source = json.loads((Path(__file__).parent / 'fixtures/compass-three-floors.json').read_text())
    value = {**source['project'], 'compass': source['compass'],
             'designJourney': {'schema': SCHEMA, 'enabledInputs': ['plot', 'compass']}}
    value['brief']['road_bearing_deg'] = 180
    return value


@pytest.mark.parametrize('index', [1, 2])
def test_unplaced_upper_room_targets_that_room_and_floor(home, index):
    room = next(room for room in home['compass']['rooms']
                if room['floorId'] == home['compass']['floors'][index]['id'])
    room['regions'] = []
    original = deepcopy(home)
    result = prepare(home)
    q = result['question']
    assert q['code'] == 'REQUIRED_ROOM_UNPLACED'
    assert q['editor'] == {'kind': 'compass', 'view': 'map', 'floor': index, 'floorIndex': index,
                           'floorId': room['floorId'], 'roomId': room['id']}
    assert q['choices'][0]['editor'] == q['editor']
    assert q['affected'][0]['name'] == room['name']
    assert q['affected'][0]['floorName'] in q['title']
    assert q['steps'] and not any(c['action'] == 'repair-layout' for c in q['choices'])
    assert home == original


def test_strict_empty_upper_floor_is_shown_before_missing_stair_link(home):
    draft = home['compass']
    floor_id = draft['floors'][2]['id']
    draft['rooms'] = [room for room in draft['rooms'] if room['floorId'] != floor_id]
    draft['stairLinks'] = []
    result = prepare(home)
    q = result['question']
    assert q['code'] == 'EMPTY_FLOOR'
    assert q['editor']['floorIndex'] == 2 and q['editor']['floorId'] == floor_id
    assert q['affected'][0]['floorName'] == 'Second floor'
    assert result['search']['status'] == 'clarification-required'
    assert 'choose-scope' in {c['action'] for c in q['choices']}
    assert len(draft['floors']) == 3


def test_plot_error_does_not_send_user_back_to_room_editor(home):
    home['brief']['left_mm'] = 12000
    q = prepare(home)['question']
    assert q['code'] == 'FIELD_RANGE'
    assert q['editor']['kind'] == 'plot'
    assert q['editor']['field'] == 'left_mm'
    assert q['choices'][0]['action'] == 'edit-plot'
    assert not any(c['action'] == 'repair-layout' for c in q['choices'])
    assert 'left_mm' in q['explanation']


def test_invalid_room_goal_names_the_survey_field():
    issue = error_issues(DesignError('FIELD_RANGE', 'bedrooms must be an integer between 0 and 8.'))
    q = _geometry_question(issue, {})
    assert q['editor']['kind'] == 'survey'
    assert q['editor']['field'] == 'bedrooms'


@pytest.mark.parametrize('missing', ['width_mm', 'depth_mm', 'storeys', 'road_bearing_deg'])
def test_missing_essential_targets_exact_input_field(missing):
    values = {'width_mm': 12000, 'depth_mm': 18000, 'storeys': 2, 'road_bearing_deg': 180}
    del values[missing]
    result = resolve_sources({'designJourney': {'schema': SCHEMA, 'inputs': [
        {'id': 'plot', 'kind': 'plot', 'values': values}]}})
    q = next(q for q in result['questions'] if q['code'] == 'PLOT_BASICS')
    assert q['editor'] == {'kind': 'plot', 'field': missing}
    assert q['choices'][0]['editor'] == q['editor']
    assert q['missingFields'] == [missing]


def test_room_minimum_exposes_measured_and_required_dimensions():
    project, draft = starter()
    result = proposal(project, draft)
    issue = next(p for p in result['issues'] if p['code'] == 'ROOM_MINIMUM')
    q = guided_question(draft, {**result, 'issues': [issue]})
    area = q['affected'][0]
    assert area['roomId'] == 'living' and area['floorId'] == 'ground'
    assert area['current']['area_m2'] < area['required']['minimum_area_m2']
    assert area['required']['minimum_width_mm'] == 2400
    assert q['editor']['roomId'] == 'living'


def test_missing_stairs_targets_first_missing_floor_without_hiding_existing_rooms(home):
    draft = home['compass']
    missing = draft['floors'][1]['id']
    for room in draft['rooms']:
        if room['floorId'] == missing and room['kind'] == 'stair':
            room['kind'] = 'store'
    draft['stairLinks'] = []
    result = prepare(home)
    q = result['question']
    assert q['code'] == 'STAIR_LINK'
    assert q['editor']['floorId'] == missing
    assert q['affected'][0]['floorName'] == 'First floor'
    assert any(item.get('roomId') for item in q['affected'][1:])


def test_exact_overlap_identifies_both_rooms_and_their_floor():
    rooms = [{'id': name, 'name': name.title(), 'kind': 'bedroom',
              'polygon': [[0, 0], [3000, 0], [3000, 3000], [0, 3000]]}
             for name in ('a', 'b')]
    project = {'customPlan': {'floors': [{'id': 'first', 'rooms': rooms}]}}
    q = _geometry_question([{'code': 'SPACE_OVERLAP', 'message': 'A overlaps B.',
                            'id': 'a', 'ids': ['a', 'b'], 'floor': 0}], project)
    assert q['editor']['kind'] == 'plan' and q['editor']['roomId'] == 'a'
    assert {item['roomId'] for item in q['affected']} == {'a', 'b'}
    assert all(item['current']['area_m2'] == 9 for item in q['affected'])


def test_exact_empty_floor_only_offers_supported_edit_actions():
    project = {'customPlan': {'floors': [{'id': 'ground', 'rooms': []}]}}
    q = _geometry_question([{'code': 'EMPTY_FLOOR', 'floor': 0, 'id': 'ground',
                            'message': 'Ground floor is empty.'}], project)
    assert q['editor']['kind'] == 'plan'
    assert {choice['action'] for choice in q['choices']} == {'edit-layout'}
    assert 'scope' not in ' '.join(q['steps'])


def test_stair_core_identifier_maps_to_real_linked_rooms():
    rooms = [{'id': name, 'name': 'Stairs', 'kind': 'stair',
              'polygon': [[0, 0], [2200, 0], [2200, 3000], [0, 3000]]} for name in ('g-stair', 'f-stair')]
    project = {'customPlan': {'floors': [{'id': fid, 'rooms': [room]}
                                        for fid, room in zip(('ground', 'first'), rooms)],
                              'stairs': [{'id': 'core', 'roomIds': ['g-stair', 'f-stair']}]}}
    q = _geometry_question([{'code': 'STAIR_FIT', 'id': 'core', 'message': 'U stair needs a clear 2200 × 4200 mm core.'}], project)
    assert q['editor']['roomId'] == 'g-stair'
    assert {a['roomId'] for a in q['affected']} == {'g-stair', 'f-stair'}
    assert 'exact plan editor' in ' '.join(q['steps'])


def test_nested_error_context_and_missing_messages_remain_actionable(home):
    error = DesignError('PLACEMENT_PROGRAMME', 'Room programme needs revision.',
                        {'rooms': [{'label': 'bedroom-1', 'floor': 1, 'cells': [[0, 0]]}]})
    records = error_issues(error)
    assert records[0]['floor'] == 1 and records[0]['cells'] == [[0, 0]]
    room = home['compass']['rooms'][-1]
    issue = enrich_issues([{'code': 'NO_EXTERNAL_WINDOW', 'id': room['id']}], home)[0]
    assert room['name'] in issue['message']
    assert issue['editor']['floorId'] == room['floorId']


def test_ambiguous_text_edit_choice_has_specific_source_editor(home):
    home['text'] = 'The plot is 40 x 60.'
    home['designJourney']['enabledInputs'].append('text')
    result = resolve_sources(home)
    question = next(q for q in result['questions'] if q['code'] == 'TEXT_INTERPRETATION')
    edit = next(c for c in question['choices'] if c['id'] == 'edit')
    assert edit['editor']['kind'] == 'text'
    assert edit['editor']['sourceId']


def test_partial_scope_does_not_show_excluded_empty_floor(home):
    draft = home['compass']
    floor_id = draft['floors'][2]['id']
    draft['rooms'] = [room for room in draft['rooms'] if room['floorId'] != floor_id]
    saved_ids = {room['id'] for room in draft['rooms']}
    for link in draft['stairLinks']:
        link['roomIds'] = [rid for rid in link['roomIds'] if rid in saved_ids]
    home['designJourney'].update(scope=2, scopeConfirmed=True)
    result = prepare(home)
    assert result['valid'], result['question']
    assert result['includedFloorCount'] == 2 and result['requestedFloorCount'] == 3
    assert len(draft['floors']) == 3


@pytest.mark.parametrize('floor,room', [
    ({}, {'id': 'unnamed', 'kind': 'bedroom', 'polygon': [[0, 0], [3000, 0], [0, 3000]]}),
    ({'id': 'ground'}, {'id': 'unnamed', 'kind': 'bedroom', 'polygon': 'invalid coordinates'}),
    ({'id': 'ground'}, {'kind': 'bedroom'}),
])
def test_invalid_import_context_never_hides_the_original_validation_error(floor, room):
    project = {'customPlan': {'floors': [dict(floor, rooms=[room])], 'stairs': [None]}}
    q = _geometry_question([{'code': 'PLAN_SCHEMA', 'message': 'Repair the imported room record.',
                            'id': room.get('id'), 'floor': 0}], project)
    assert q['explanation'] == 'Repair the imported room record.'
    assert q['editor']['kind'] == 'plan'
    assert q['editor']['floorIndex'] == 0
