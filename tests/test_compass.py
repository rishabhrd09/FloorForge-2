"""Compass is additive: authored allocations, reviewed proposals and unchanged old inputs."""
import copy
import json
from pathlib import Path
import subprocess
import shutil
import pytest

from floorforge.model import DesignError, sha
from floorforge.intent import fuse
from floorforge.compass_input import normalize, connected, remap, source_hash
from floorforge.compass_adapter import proposal


@pytest.fixture
def project():
    return {'schema': 'floorforge.project/0.5', 'brief': {
        'width_mm': 14000, 'depth_mm': 18000, 'front_mm': 3000, 'rear_mm': 1200,
        'left_mm': 1000, 'right_mm': 1000, 'bedrooms': 2, 'storeys': 1, 'roof_access': False}}


@pytest.fixture
def compass():
    definitions = [
        ('living', 'living', [(r, c) for r in (0, 1) for c in (0, 1)] + [(1, c) for c in (2, 3)]),
        ('kitchen', 'kitchen', [(0, c) for c in (2, 3)]),
        ('bed-one', 'bedroom', [(r, c) for r in (2, 3) for c in (0, 1)]),
        ('bed-two', 'bedroom', [(r, c) for r in (2, 3) for c in (2, 3)]),
    ]
    return {'schema': 'floorforge.compass-input/1',
            'grid': {'rows': 4, 'cols': 4, 'basis': 'buildable-envelope', 'rowOrigin': 'front'},
            'floors': [{'id': 'compass-ground', 'splits': []}],
            'rooms': [{'id': ident, 'kind': kind, 'name': ident, 'floorId': 'compass-ground',
                       'regions': [f'{r}:{c}' for r, c in cells], 'required': True}
                      for ident, kind, cells in definitions]}


def accepted(project, compass):
    result = proposal(project, compass)
    assert result['valid'], result['issues']
    return {**project, 'compass': compass, 'compassAcceptance': {
        'sourceHash': result['sourceHash'], 'adapterVersion': result['adapterVersion']}}


def test_l_shaped_room_is_one_polygon_and_touching_bedrooms_stay_distinct(project, compass):
    from floorforge.layout import generate_layout
    from floorforge.review import validate
    p = accepted(project, compass)
    intent = fuse(p)
    b = generate_layout(intent)
    validate(b)
    assert {s['id'] for s in b['spaces'] if s['kind'] == 'bedroom'} == {'bed-one', 'bed-two'}
    living = next(s for s in b['spaces'] if s['id'] == 'living')
    assert len(living['polygon']) > 4
    assert not any(w['rooms'] == ['living', 'living'] for w in b['walls'])
    assert b['planning']['compass']['sourceHash'] == p['compassAcceptance']['sourceHash']


@pytest.mark.parametrize('rows', [4, 6, 8])
def test_density_and_halves_are_different_partitions(compass, rows):
    compass['grid']['rows'] = rows
    compass['rooms'] = []
    compass['floors'][0]['splits'] = ['0:0']
    data = normalize(compass)
    assert data['grid']['rows'] * data['grid']['cols'] == rows * 4
    assert len(data['floors'][0]['splits']) == 1


@pytest.mark.parametrize('refs,expected', [(['0:0', '1:1'], False), (['0:0:R', '0:1:L'], True), (['0:0:L', '1:0:R'], False), (['0:0', '1:0', '1:1'], True)])
def test_edge_adjacency_including_halves(refs, expected):
    assert connected(refs, 4) is expected


def test_single_owner_and_connected_identity_are_validated(compass):
    compass['rooms'][1]['regions'] = ['0:0']
    with pytest.raises(DesignError, match='only one room'):
        normalize(compass)
    compass['rooms'][1]['regions'] = ['0:3', '3:0']
    with pytest.raises(DesignError, match='share edges'):
        normalize(compass)


def test_unplaced_and_small_rooms_return_repairable_issues(project, compass):
    compass['rooms'][2]['regions'] = []
    result = proposal(project, compass)
    assert not result['valid']
    assert any(i['code'] == 'UNPLACED' and i['roomId'] == 'bed-one' for i in result['issues'])


def test_optional_unplaced_bedroom_is_not_counted_as_a_generated_room(project, compass):
    from floorforge.layout import generate_layout
    compass['rooms'][2].update(required=False, regions=[])
    intent = fuse(accepted(project, compass))
    building = generate_layout(intent)
    assert intent['compassFullValues']['bedrooms'] == 2  # The complete checklist stays saved.
    assert intent['values']['bedrooms'] == building['brief']['bedrooms'] == 1
    assert sum(s['kind'] == 'bedroom' for s in building['spaces']) == 1


def test_unplaced_optional_room_requests_are_not_reported_as_applied(project, compass):
    compass['rooms'][2].update(required=False, regions=[])
    compass['requirements'] = [{'id': 'bed-route', 'kind': 'access-width', 'roomId': 'bed-one', 'value': 900}]
    compass['connections'] = [{'id': 'bed-door', 'from': 'living', 'to': 'bed-one', 'kind': 'door', 'width': 900}]
    intent = fuse(accepted(project, compass))
    entries = {e['source']: e for e in intent['input_audit']['entries']}
    assert entries['bed-route']['status'] == entries['bed-door']['status'] == 'unapplied'
    assert intent['input_audit']['attention_count'] >= 2


def test_excluded_floor_requirements_stay_saved_and_are_reported_off():
    source = json.loads((Path(__file__).parent/'fixtures/compass-three-floors.json').read_text())
    p, c = source['project'], source['compass']
    c['requirements'] = [{'id': 'upper-route', 'kind': 'access-width', 'roomId': 'f1-hall', 'value': 900}]
    result = proposal(p, c, 1)
    assert result['valid'], result['issues']
    assert next(e for e in result['effects'] if e['source'] == 'upper-route')['status'] == 'off'
    assert c['requirements'][0]['roomId'] == 'f1-hall'


def test_size_locks_never_trigger_automatic_movement(project, compass):
    original = copy.deepcopy(compass)
    compass['rooms'][0]['target'] = {'width': 4000, 'depth': 4000, 'locked': True}
    result = proposal(project, compass)
    assert any(i['code'] == 'SIZE_LOCK' for i in result['issues'])
    assert compass['rooms'][0]['regions'] == original['rooms'][0]['regions']


def test_remapping_previews_all_floors_and_refuses_collisions(compass):
    original = copy.deepcopy(compass)
    result = remap(compass, 6)
    assert not result['valid']
    assert any(i['code'] == 'REMAP_COLLISION' for i in result['issues'])
    assert compass == original
    result = remap(compass, 8)
    assert result['valid']
    assert {r['id'] for r in result['candidate']['rooms']} == {r['id'] for r in compass['rooms']}
    assert all(r['regions'] for r in result['candidate']['rooms'])
    normalize(result['candidate'])


def test_acceptance_is_bound_to_site_scope_and_map(project, compass):
    p = accepted(project, compass)
    with pytest.raises(DesignError, match='older map'):
        fuse({**p, 'compassAcceptance': {'sourceHash': '0' * 64, 'adapterVersion': 'compass/1'}})
    p['brief']['road_bearing_deg'] = 90
    with pytest.raises(DesignError, match='older map'):
        fuse(p)


@pytest.mark.parametrize('bearing', [0, 45, 90, 135, 180, 225, 270, 315])
def test_all_bearings_keep_authored_map_positions(project, compass, bearing):
    first = proposal(project, compass)
    project['brief']['road_bearing_deg'] = bearing
    result = proposal(project, compass)
    assert result['valid'], result['issues']
    assert [r['polygon'] for r in result['customPlan']['floors'][0]['rooms']] == [r['polygon'] for r in first['customPlan']['floors'][0]['rooms']]


def test_inactive_drafts_preserve_legacy_hash_and_theme_defaults(compass):
    p = {'schema': 'floorforge.project/0.4', 'brief': {'bedrooms': 3}}
    before = fuse(p)
    p['editorState'] = {'mode': 'automatic', 'guideFloors': [[['']*4 for _ in range(4)] for _ in range(3)], 'compassDraft': compass}
    after = fuse(p)
    assert after['planHash'] == before['planHash']
    assert after['values'] == before['values']
    assert fuse({'schema': 'floorforge.project/0.5'})['values']['exterior_theme'] == before['values']['exterior_theme']
    p['editorState']['compassDraft']['rooms'][0]['name'] = 'An inactive rename'
    assert fuse(p)['planHash'] == before['planHash']


def test_two_authoritative_inputs_are_rejected(project, compass):
    p = accepted(project, compass)
    p['customPlan'] = proposal(project, compass)['customPlan']
    with pytest.raises(DesignError, match='Choose Compass'):
        fuse(p)


def test_notes_are_saved_but_do_not_change_active_geometry_hash(project, compass):
    p = accepted(project, compass)
    before = fuse(p)['planHash']
    compass['requirements'] = [{'id': 'note-1', 'kind': 'note', 'value': 'A future garden swing.'}]
    assert fuse(p)['planHash'] == before
    assert any(e['status'] == 'note only' for e in fuse(p)['input_audit']['entries'])


def test_explicit_opening_relationship_changes_canonical_geometry(project, compass):
    compass['connections'] = [{'id': 'open-living-kitchen', 'from': 'living', 'to': 'kitchen', 'kind': 'open', 'width': 1800}]
    result = proposal(project, compass)
    assert result['valid'], result['issues']
    openings = result['customPlan']['floors'][0]['openings']
    assert next(o for o in openings if o['id'] == 'open-living-kitchen')['kind'] == 'cased'


def test_unavailable_site_choices_are_never_reported_applied(project, compass):
    compass['site'] = {'gate': 'left'}
    result = proposal(project, compass)
    assert not result['valid']
    assert any(i['code'] == 'SITE_UNAVAILABLE' for i in result['issues'])


def test_text_conflict_requires_an_explicit_resolution(project, compass):
    project['text'] = 'kitchen at the rear left'
    result = proposal(project, compass)
    assert any(i['code'] == 'TEXT_CONFLICT' for i in result['issues'])
    compass['requirements'] = [{'id': 'keep-kitchen', 'kind': 'keep-map', 'value': 'kitchen'}]
    assert proposal(project, compass)['valid']


def test_archived_floor_edits_do_not_change_ground_scope_identity(project, compass):
    compass['floors'].append({'id': 'upper-draft', 'splits': []})
    compass['rooms'].append({'id': 'future-study', 'kind': 'study', 'name': 'Future study', 'floorId': 'upper-draft', 'regions': []})
    values = fuse(project)['values']
    before = source_hash(compass, values, 1)
    compass['rooms'][-1]['regions'] = ['3:3']
    assert source_hash(compass, values, 1) == before


def test_zero_bedroom_custom_programme_is_supported(project, compass):
    project['brief']['bedrooms'] = 0
    for room in compass['rooms']:
        if room['kind'] == 'bedroom':
            room['kind'] = 'study'
    assert fuse(accepted(project, compass))['values']['bedrooms'] == 0


def test_compass_flag_and_disabled_generation_preserve_drafts(monkeypatch, tmp_path, compass):
    from floorforge.compass_api import capabilities, dispatch
    from floorforge.server import State
    monkeypatch.delenv('FLOORFORGE_COMPASS', raising=False)
    assert not capabilities()['enabled']
    with pytest.raises(DesignError, match='guarded development'):
        dispatch('/api/compass/remap', {'compass': compass, 'rows': 8})
    monkeypatch.setenv('FLOORFORGE_COMPASS', '1')
    state = State(tmp_path)
    try:
        with pytest.raises(DesignError, match='accept'):
            state.submit({'editorState': {'mode': 'compass'}})
    finally:
        state.pool.shutdown()


def test_geometry_scene_drawings_and_exports_share_identity(project, compass, tmp_path):
    from floorforge.pipeline import run
    p = accepted(project, compass)
    result = run(p, tmp_path)
    directory = Path(result['path'])
    plan_hash = fuse(p)['planHash']
    for name in ('building.json', 'scene.json', 'report.json', 'review.json'):
        assert json.loads((directory/name).read_text())['planHash'] == plan_hash
    assert (directory/'drawings.pdf').exists() and (directory/'floorplans.dxf').exists()
    assert (directory/'model.glb').exists() and (directory/'model.ifc').exists()


def test_mixed_form_map_and_text_inputs_reach_the_shared_geometry(project, compass):
    from floorforge.layout import generate_layout
    from floorforge.review import reports, validate
    from floorforge.scene import make_scene
    from floorforge.drawings import make_sheets
    fields = {'title': 'Mixed-input wiring check', 'width_mm': 15000, 'depth_mm': 19000,
              'front_mm': 3200, 'rear_mm': 1300, 'left_mm': 1100, 'right_mm': 1200,
              'road_bearing_deg': 135, 'floor_height_mm': 3300, 'plinth_mm': 500,
              'budget_lakh': 78}
    project['sources'] = [{'id': 'studio-field-edits', 'kind': 'form', 'values': fields}]
    project['text'] = 'Kitchen at front right. A soundproof music studio.'
    compass['site'] = {'entryRoomId': 'living', 'context': 'middle'}
    compass['connections'] = [{'id': 'open-kitchen', 'from': 'living', 'to': 'kitchen', 'kind': 'open', 'width': 1800}]
    compass['requirements'] = [{'id': 'living-route', 'kind': 'access-width', 'roomId': 'living', 'value': 900},
                               {'id': 'garden-note', 'kind': 'note', 'value': 'Keep a garden swing for later.'}]
    intent = fuse(accepted(project, compass))
    b = generate_layout(intent)
    report = reports(b, validate(b))
    scene = make_scene(b, report)
    sheets = make_sheets(b, scene, report)
    for key, value in fields.items():
        assert b['brief'][key] == intent['values'][key] == value
        assert intent['provenance'][key]['selected'] == ['studio-field-edits']
    assert scene['floor_height'] == 3.3
    assert {r['id'] for r in b['spaces']} == {r['id'] for r in compass['rooms']}
    opening = next(o for o in b['openings'] if o['id'] == 'open-kitchen')
    assert opening['kind'] == 'cased' and opening['width'] == 1800
    assert set(next(o for o in b['openings'] if o['kind'] == 'entry')['connects']) == {'living', 'outside'}
    assert scene['opening_model']['walls'] == b['walls']
    assert scene['opening_model']['openings'] == b['openings']
    assert {o['planHash'] for o in [intent, b, report, scene, *sheets]} == {intent['planHash']}
    effects = {e['source']: e for e in intent['input_audit']['entries']}
    assert effects['open-kitchen']['status'] == effects['living-route']['status'] == effects['entry-destination']['status'] == 'applied'
    assert effects['plot-context']['status'] == effects['garden-note']['status'] == 'note only'
    assert any(e['status'] == 'unapplied' and 'soundproof' in e.get('message', '') for e in effects.values())


def test_frontend_transactions_and_random_sequences():
    if not shutil.which('node'):
        pytest.skip('Node is optional')
    subprocess.run(['node', '--test', 'tests/compass_state.cjs'], check=True, capture_output=True, text=True)


@pytest.mark.parametrize('scope', [1, 2, 3])
def test_three_floor_draft_generates_prefix_scopes_without_removing_upper_drafts(scope):
    from floorforge.layout import generate_layout
    from floorforge.review import validate
    source = json.loads((Path(__file__).parent/'fixtures/compass-three-floors.json').read_text())
    project, compass = source['project'], source['compass']
    original = copy.deepcopy(source)
    result = proposal(project, compass, scope)
    assert result['valid'], result['issues']
    p = {**project, 'compass': compass, 'compassScope': scope, 'compassAcceptance': {
        'sourceHash': result['sourceHash'], 'adapterVersion': result['adapterVersion']}}
    intent = fuse(p)
    b = generate_layout(intent)
    validate(b)
    assert b['storeys'] == scope
    assert intent['values']['bedrooms'] == scope
    assert intent['compassFullValues']['storeys'] == 3
    assert sum(s.get('to_floor') is not None for s in b['stairs']) == max(0, scope-1)
    assert source == original


def test_http_api_keeps_origin_token_and_flag_protections(monkeypatch, tmp_path, project, compass):
    import threading
    import urllib.request
    import urllib.error
    from floorforge.server import make_server
    monkeypatch.setenv('FLOORFORGE_COMPASS', '1')
    server = make_server(tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        session = json.load(urllib.request.urlopen(base+'/api/session'))
        assert session['compass']['enabled']
        data = json.dumps({'project': project, 'compass': compass}).encode()
        request = urllib.request.Request(base+'/api/compass/convert', data, headers={'Content-Type': 'application/json'})
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request)
        assert exc.value.code == 403
        request.add_header('X-FloorForge-Token', session['token'])
        assert json.load(urllib.request.urlopen(request))['valid']
        request.add_header('Origin', 'http://evil.example')
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request)
        assert exc.value.code == 403
    finally:
        server.shutdown()
        server.server_close()
        server.state.pool.shutdown()
        thread.join()


def test_future_project_versions_cannot_be_downgrade_saved():
    with pytest.raises(DesignError, match='newer reader'):
        fuse({'schema':'floorforge.project/0.6','brief':{}})


def test_pending_compass_draft_roundtrip_does_not_require_valid_geometry(compass):
    compass['rooms'][0]['regions']=[]
    p={'schema':'floorforge.project/0.5','brief':{'storeys':1},'editorState':{
        'mode':'compass','compassDraft':compass,'compassScope':1,
        'guideFloors':[[['']*4 for _ in range(4)] for _ in range(3)]}}
    restored=json.loads(json.dumps(p))
    assert fuse(restored)['customPlan'] is None
    assert restored['editorState']['compassDraft']==compass


def test_thin_l_shape_cannot_pass_on_bounding_dimensions_alone(project, compass):
    project['brief']['bedrooms'] = 0
    compass['grid']['rows'] = 8
    compass['floors'][0]['splits'] = [f'{r}:0' for r in range(1, 8)]
    compass['rooms'] = [{**compass['rooms'][0], 'regions':
        [f'0:{c}' for c in range(4)] + [f'{r}:0:L' for r in range(1, 8)]}]
    result = proposal(project, compass)
    assert not result['valid']
    assert any(i['code'] == 'NARROW_NECK' and i['roomId'] == 'living' for i in result['issues'])


def test_holes_are_rejected_without_repairing_or_moving_assignments(project, compass):
    project['brief']['bedrooms'] = 0
    compass['rooms'] = [{**compass['rooms'][0], 'regions':
        [f'{r}:{c}' for r in range(3) for c in range(3) if (r, c) != (1, 1)]}]
    before = copy.deepcopy(compass)
    result = proposal(project, compass)
    assert any(i['code'] == 'COLLAPSED_ROOM' for i in result['issues'])
    assert compass == before


def test_separated_rooms_have_no_direct_opening(project, compass):
    compass['connections'] = [{'id': 'separate-kitchen', 'from': 'living', 'to': 'kitchen', 'kind': 'separated'}]
    result = proposal(project, compass)
    assert not result['valid']  # The kitchen has no other authored access.
    from floorforge.custom_plan import compile_plan
    b = compile_plan({'values': result['values'], 'customPlan': result['customPlan'], 'planHash': result['sourceHash']})
    assert not any(set(o['connects']) == {'living', 'kitchen'} for o in b['openings'])
    assert any(i['code'] == 'UNREACHABLE' and i['roomId'] == 'kitchen' for i in result['issues'])


def test_adjacent_open_spaces_cannot_claim_solid_separation(project, compass):
    project['brief']['bedrooms'] = 0
    for room in compass['rooms']:
        room['kind'] = 'terrace'
    compass['connections'] = [{'id': 'separate-open-spaces', 'from': 'bed-one', 'to': 'bed-two', 'kind': 'separated'}]
    result = proposal(project, compass)
    assert any(i['code'] == 'SEPARATION_WALL' for i in result['issues'])


@pytest.mark.parametrize('scope', [1, 2, 3])
def test_roof_access_is_a_real_stair_flight_only_over_the_full_occupied_scope(scope):
    from floorforge.layout import generate_layout
    from floorforge.review import validate
    source = json.loads((Path(__file__).parent/'fixtures/compass-three-floors.json').read_text())
    p, compass = source['project'], source['compass']
    p['brief']['roof_access'] = True
    result = proposal(p, compass, scope)
    assert result['valid'], result['issues']
    payload = {**p, 'compass': compass, 'compassScope': scope,
               'compassAcceptance': {k: result[k] for k in ('sourceHash', 'adapterVersion')}}
    intent = fuse(payload)
    b = generate_layout(intent)
    validate(b)
    assert bool([s for s in b['stairs'] if s.get('roof_access')]) == (scope == 3)
    assert sum(s.get('to_floor') is not None for s in b['stairs']) == (3 if scope == 3 else scope-1)
    assert len(payload['compass']['floors']) == 3


def test_legacy_conversion_keeps_the_original_exact_project(monkeypatch):
    from floorforge.compass_api import dispatch
    monkeypatch.setenv('FLOORFORGE_COMPASS', '1')
    original = json.loads((Path(__file__).parents[1]/'examples/briefs/manual-L.json').read_text())
    before = copy.deepcopy(original)
    result = dispatch('/api/compass/migrate-preview', {'project': original})
    assert result['originalProject'] == before
    assert original == before
    assert result['candidate'] is None and not result['valid']
