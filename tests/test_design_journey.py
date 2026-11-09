"""Behavioural contracts for source consumption and immutable 2D approval."""
from copy import deepcopy
import json
from pathlib import Path
import random

import pytest

from floorforge.design_journey import (
    SCHEMA, PRESETS, approve_floor, canonical_model, confirm_home, floor_hashes,
    normalize_sources, prepare, resolve_sources, verify_approval,
    editing_project, editing_result,
)
from floorforge.model import DesignError, sha

ROOT = Path(__file__).resolve().parents[1]
SECRET = b'test-only-server-held-approval-key'


@pytest.fixture
def exact():
    p = json.loads((ROOT / 'examples/custom/g2-terrace.floorforge.json').read_text())
    p['designJourney'] = {'schema': SCHEMA, 'enabledInputs': ['plot', 'dxf']}
    return p


@pytest.fixture
def compass():
    source = json.loads((ROOT / 'tests/fixtures/compass-three-floors.json').read_text())
    p = {**source['project'], 'compass': source['compass']}
    p['brief']['road_bearing_deg'] = 180
    p['designJourney'] = {'schema': SCHEMA, 'enabledInputs': ['plot', 'compass']}
    return p


def sign_home(preparation):
    approvals = {f['id']: approve_floor(preparation, f['id'], f['geometryHash'], SECRET) for f in preparation['floors']}
    return confirm_home(preparation, approvals, preparation['geometryHash'], SECRET)


def test_preparation_is_2d_only_and_keeps_every_floor(exact, monkeypatch):
    monkeypatch.setattr('floorforge.scene.make_scene', lambda *args: pytest.fail('2D preparation constructed presentation meshes'))
    p = prepare(exact)
    assert p['valid'], p['questions']
    assert len(p['floors']) == len(exact['customPlan']['floors']) == 3
    assert {r['id'] for r in p['canonical']['rooms']} == {r['id'] for f in exact['customPlan']['floors'] for r in f['rooms']}
    for floor in p['floors']:
        assert '<svg ' in floor['svg'] and 'All dimensions in millimetres' in floor['svg']
        assert floor['geometryHash'] and floor['scale'] > 0
    assert p['canonical']['units'] == 'mm'
    assert p['canonical']['tolerance']['coordinate_mm'] == .001


def test_disabled_text_does_not_change_compilation_or_disappear(exact):
    p = deepcopy(exact)
    p['text'] = 'The plot is 50 x 80 feet. Four bedrooms and a helipad.'
    original = deepcopy(p)
    resolved = resolve_sources(p)
    assert resolved['project']['brief']['width_mm'] == p['brief']['width_mm']
    text = next(s for s in resolved['sources'] if s['kind'] == 'text')
    assert not text['enabled'] and text['text'] == p['text']
    entries = [r for r in resolved['requirements'] if r['sourceId'] == text['id']]
    assert entries and all(r['status'] == 'excluded' for r in entries)
    assert p == original


def test_deselected_dxf_never_reappears_as_an_enabled_exact_plan(exact):
    exact['designJourney']['imports'] = [{'id': 'drawing-source', 'kind': 'dxf', 'text': 'retained original'}]
    exact['designJourney']['enabledInputs'] = ['plot']
    exact['editorState'] = {'mode': 'custom'}
    exact['sources'] = [{'id': 'imported-dxf-measurements', 'kind': 'plan', 'enabled': True,
                         'values': {'width_mm': 30000}}]
    r = resolve_sources(exact)
    assert 'customPlan' not in r['project']
    assert r['project']['brief']['width_mm'] == exact['brief']['width_mm']
    assert next(s for s in r['sources'] if s['id'] == 'exact-layout')['kind'] == 'dxf'
    assert not next(s for s in r['sources'] if s['id'] == 'exact-layout')['enabled']
    assert all(e['status'] == 'excluded' for e in r['requirements'] if e['field'] == 'layout')


def test_individually_disabled_latest_dxf_is_excluded_even_when_dxf_method_enabled(exact):
    original = deepcopy(exact['customPlan'])
    exact['designJourney']['imports'] = [{'id': 'individual-drawing', 'kind': 'dxf', 'enabled': False,
                                         'provenance': {'geometry': original, 'rawText': 'retained DXF'}}]
    r = resolve_sources(exact)
    assert 'customPlan' not in r['project']
    source = next(s for s in r['sources'] if s['id'] == 'exact-layout')
    assert not source['enabled'] and source['geometry'] == original
    assert all(e['status'] == 'excluded' for e in r['requirements'] if e['field'] == 'layout')
    assert not any(q['code'] == 'MISSING_INPUT' for q in r['questions'])
    assert any(q['code'] == 'ROOM_GOALS' for q in r['questions'])  # no silent automatic default programme
    exact['designJourney']['imports'][0]['enabled'] = True
    restored = resolve_sources(exact)
    assert restored['project']['customPlan'] == original


def test_input_selection_controls_explicit_registry_sources():
    p = {'designJourney': {'schema': SCHEMA, 'enabledInputs': ['plot'], 'inputs': [
        {'id': 'plot', 'kind': 'plot', 'values': {'width_mm': 12000, 'depth_mm': 18000, 'storeys': 1, 'road_bearing_deg': 180, 'bedrooms': 2}},
        {'id': 'text', 'kind': 'text', 'enabled': True, 'text': 'The plot is 50 x 80 feet.'},
    ]}}
    r = resolve_sources(p)
    assert not r['questions']
    assert r['project']['brief']['width_mm'] == 12000
    assert next(s for s in r['sources'] if s['id'] == 'text')['originalEnabled'] is True
    assert next(s for s in r['sources'] if s['id'] == 'text')['enabled'] is False


def test_plot_only_journey_asks_missing_room_goal_before_planning():
    p = {'brief': {'width_mm': 12000, 'depth_mm': 18000, 'storeys': 1, 'road_bearing_deg': 180},
         'designJourney': {'schema': SCHEMA, 'enabledInputs': ['plot']}}
    r = resolve_sources(p)
    assert r['question']['code'] == 'ROOM_GOALS'
    p['designJourney']['answers'] = {r['question']['id']: '2'}
    decided = resolve_sources(p)
    assert not decided['questions']
    assert decided['project']['brief']['bedrooms'] == 2
    assert decided['project']['brief']['pooja'] is False
    assert decided['project']['brief']['attached_baths'] == 0


def test_enabled_saved_dxf_remains_authoritative_when_compass_editor_open(exact, compass):
    exact['editorState'] = {'mode': 'compass', 'customPlan': exact.pop('customPlan'), 'compassDraft': compass['compass']}
    exact['designJourney']['enabledInputs'].append('compass')
    r = resolve_sources(exact)
    assert any(q['code'] == 'LAYOUT_AUTHORITY' for q in r['questions'])
    assert not any(q['code'] == 'MISSING_INPUT' for q in r['questions'])
    assert next(s for s in r['sources'] if s['id'] == 'exact-layout')['enabled']


def test_original_dxf_imports_keep_distinct_sources_and_resolve_overlap(exact):
    first = deepcopy(exact['customPlan'])
    first['floors'][0]['rooms'][0]['name'] = 'Original first drawing'
    exact['designJourney']['imports'] = [
        {'id': 'drawing-one', 'kind': 'dxf', 'name': 'first.dxf', 'units': 'mm', 'provenance': {'geometry': first, 'rawText': 'first drawing bytes'}},
        {'id': 'drawing-two', 'kind': 'dxf', 'name': 'second.dxf', 'units': 'mm', 'provenance': {'geometry': exact['customPlan'], 'rawText': 'second drawing bytes'}},
    ]
    r = resolve_sources(exact)
    assert next(s for s in r['sources'] if s['id'] == 'drawing-one')['geometry'] == first
    assert next(s for s in r['sources'] if s['id'] == 'exact-layout')['provenance']['originalSource']['id'] == 'drawing-two'
    assert any(q['code'] == 'LAYOUT_AUTHORITY' for q in r['questions'])


def test_enabling_text_creates_actual_measurement_conflict(exact):
    exact['text'] = 'My plot is 50 x 80 feet.'
    exact['designJourney']['enabledInputs'].append('text')
    r = resolve_sources(exact)
    q = next(q for q in r['questions'] if q['code'] == 'SOURCE_CONFLICT')
    assert q['choices'][0]['id'] == 'plot-basics'
    exact['designJourney']['answers'] = {q['id']: 'written-requirements'}
    chosen = resolve_sources(exact)
    assert chosen['project']['brief']['width_mm'] == 15240
    assert any(x['field'] == 'width_mm' and x['sourceId'] == 'plot-basics' and x['status'] == 'excluded' for x in chosen['requirements'])
    # The original plot and old answer survive; changed candidate values need a new answer.
    exact['text'] = 'My plot is 60 x 80 feet.'
    changed = resolve_sources(exact)
    assert any(q['id'] not in exact['designJourney']['answers'] for q in changed['questions'] if q['code'] == 'SOURCE_CONFLICT')


def test_current_form_edits_are_revisions_not_independent_conflicts(exact):
    original_width = exact['brief']['width_mm']
    exact['sources'] = [{'id': 'studio-field-edits', 'kind': 'form', 'enabled': True,
                         'values': {'width_mm': 20000, 'bedrooms': 7}}]
    resolved = resolve_sources(exact)
    assert not resolved['questions']
    assert resolved['project']['brief']['width_mm'] == 20000
    # Disabled guided survey remains disabled even when its field was edited.
    assert 'bedrooms' not in resolved['project']['brief']
    assert next(s for s in resolved['sources'] if s['id'] == 'plot-basics')['provenance']['supersededValues']['width_mm'] == original_width
    assert exact['brief']['width_mm'] == original_width


def test_compatible_sources_combine_after_units_conversion():
    p = {'designJourney': {'schema': SCHEMA, 'inputs': [
        {'id': 'survey', 'kind': 'survey', 'enabled': True, 'units': 'ft',
         'values': {'width': 40, 'depth': 60, 'storeys': 1, 'road_bearing_deg': 90}},
        {'id': 'measured', 'kind': 'plot', 'enabled': True, 'units': 'mm',
         'values': {'width_mm': 12192, 'bedrooms': 2}, 'confidence': .95,
         'provenance': {'origin': 'site-measurement', 'author': 'owner'}},
    ]}}
    r = resolve_sources(p)
    assert not r['questions']
    assert r['project']['brief']['depth_mm'] == 18288
    assert r['project']['brief']['bedrooms'] == 2
    assert all(x['status'] == 'applied' for x in r['requirements'])
    assert r['sources'][1]['confidence'] == .95


def test_disabled_measurements_are_not_replaced_by_silent_defaults():
    p = {'brief': {'width_mm': 15000, 'depth_mm': 20000},
         'designJourney': {'schema': SCHEMA, 'enabledInputs': ['text']}, 'text': 'Two bedrooms'}
    result = resolve_sources(p)
    assert result['question']['code'] == 'PLOT_BASICS'
    assert 'width_mm' not in result['project']['brief']
    q = result['question']
    p['designJourney']['answers'] = {q['id']: 'defaults'}
    assert resolve_sources(p)['project']['brief']['width_mm'] == 12192


def test_uncalibrated_image_is_never_applied_geometry(exact):
    exact['designJourney']['enabledInputs'].append('sketch')
    exact['attachments'] = [{'name': 'sketch.png', 'sha256': 'sample', 'kind': 'visual-reference',
                             'dataUrl': 'data:image/png;base64,c2FtcGxl'}]
    r = resolve_sources(exact)
    image = next(x for x in r['requirements'] if x['field'] == 'reference')
    assert image['status'] == 'reference-only'
    assert next(s for s in r['sources'] if s['kind'] == 'sketch')['reference']['dataUrl'].endswith('c2FtcGxl')
    assert r['project']['customPlan'] == exact['customPlan']


def test_overlapping_authorities_require_choice_and_keep_originals(exact, compass):
    exact['compass'] = compass['compass']
    exact['designJourney']['enabledInputs'].append('compass')
    r = resolve_sources(exact)
    q = next(q for q in r['questions'] if q['code'] == 'LAYOUT_AUTHORITY')
    exact['designJourney']['answers'] = {q['id']: 'compass-map'}
    r = resolve_sources(exact)
    assert 'compass' in r['project'] and 'customPlan' not in r['project']
    assert next(x for x in r['requirements'] if x['sourceId'] == 'exact-layout' and x['field'] == 'layout')['status'] == 'reference-only'
    assert next(s for s in r['sources'] if s['id'] == 'exact-layout')['geometry'] == exact['customPlan']


def test_disjoint_exact_sources_merge_with_floor_mapping(exact):
    base = exact['customPlan']
    p = {'designJourney': {'schema': SCHEMA, 'inputs': [
        {'id': 'plot', 'kind': 'plot', 'values': exact['brief']},
        *[{'id': 'drawing-' + str(i), 'kind': 'dxf', 'floorIds': ['mapped-' + str(i)],
           'geometry': {**base, 'floors': [fl], 'stairs': []}} for i, fl in enumerate(base['floors'])],
    ]}}
    r = resolve_sources(p)
    assert not r['questions']
    assert [f['id'] for f in r['project']['customPlan']['floors']] == ['mapped-0', 'mapped-1', 'mapped-2']
    # Missing linked stair information must be diagnosed, never reconstructed silently.
    assert not prepare(p)['valid']


def mapped_source(exact, index, ident=None):
    floor = deepcopy(exact['customPlan']['floors'][index])
    return {'id': ident or 'drawing-' + str(index), 'kind': 'dxf', 'enabled': True,
            'floorIds': [floor['id']], 'floorIndices': [index], 'requestedFloorCount': 3,
            'floorOrder': [f['id'] for f in exact['customPlan']['floors']],
            'geometry': {**deepcopy(exact['customPlan']), 'floors': [floor], 'stairs': []}}


def mapped_project(exact, sources):
    return {'designJourney': {'schema': SCHEMA, 'inputs': [
        {'id': 'plot', 'kind': 'plot', 'values': exact['brief']}, *sources]}}


def test_mapped_drawings_merge_by_physical_floor_independent_of_input_order(exact):
    sources = [mapped_source(exact, i) for i in range(3)]
    results = [resolve_sources(mapped_project(exact, ordered)) for ordered in (sources, list(reversed(sources)))]
    assert all(not r['questions'] for r in results)
    assert results[0]['project']['customPlan'] == results[1]['project']['customPlan']
    assert [f['id'] for f in results[0]['project']['customPlan']['floors']] == [f['id'] for f in exact['customPlan']['floors']]


def test_single_upper_drawing_preserves_missing_levels_without_owning_them(exact):
    r = resolve_sources(mapped_project(exact, [mapped_source(exact, 1)]))
    floors = r['project']['customPlan']['floors']
    assert len(floors) == 3 and floors[1]['rooms']
    assert not floors[0]['rooms'] and not floors[2]['rooms']
    assert [f['id'] for f in floors] == [f['id'] for f in exact['customPlan']['floors']]
    assert not prepare(mapped_project(exact, [mapped_source(exact, 1)]))['valid']


def test_same_physical_floor_with_different_ids_requires_choice_keeps_other_floors(exact):
    sources = [mapped_source(exact, i) for i in range(3)]
    replacement = mapped_source(exact, 1, 'replacement')
    replacement['floorIds'] = ['different-id']
    p = mapped_project(exact, [replacement, *sources])
    r = resolve_sources(p)
    q = next(q for q in r['questions'] if q['code'] == 'LAYOUT_AUTHORITY')
    assert q['affected'][0]['floorIndex'] == 1
    p['designJourney']['answers'] = {q['id']: 'replacement'}
    selected = resolve_sources(p)
    assert not selected['questions']
    assert [f['id'] for f in selected['project']['customPlan']['floors']] == [sources[0]['floorIds'][0], 'different-id', sources[2]['floorIds'][0]]
    assert next(e for e in selected['requirements'] if e['sourceId'] == 'drawing-1' and e['field'] == 'layout')['status'] == 'reference-only'


def test_live_full_plan_deduplicates_original_import_and_ignores_placeholders(exact):
    original = mapped_source(exact, 0)
    latest = mapped_source(exact, 1)
    exact['designJourney']['imports'] = [original, latest]
    exact['customPlan']['floors'][2] = {'id': exact['customPlan']['floors'][2]['id'], 'rooms': [], 'walls': [], 'openings': []}
    exact['customPlan']['stairs'] = []
    r = resolve_sources(exact)
    assert not r['questions']
    assert len(r['project']['customPlan']['floors']) == 3
    assert r['project']['customPlan']['floors'][0]['rooms']
    assert r['project']['customPlan']['floors'][1]['rooms']
    assert not r['project']['customPlan']['floors'][2]['rooms']
    assert all(e['status'] == 'applied' for e in r['requirements'] if e['field'] == 'layout')


def test_retained_manual_layout_conflicts_only_at_overwritten_floor(exact):
    original = deepcopy(exact['customPlan'])
    imported = mapped_source(exact, 1)
    imported['geometry']['floors'][0]['rooms'][0]['polygon'][0][0] += 25
    exact['designJourney']['layoutSources'] = [{'id': 'manual-before-import', 'kind': 'plan', 'enabled': True,
        'geometry': original, 'floorIndices': [0, 1, 2], 'provenance': {'origin': 'manual-exact-editor'}}]
    exact['designJourney']['imports'] = [imported]
    exact['customPlan']['floors'][1] = deepcopy(imported['geometry']['floors'][0])
    r = resolve_sources(exact)
    questions = [q for q in r['questions'] if q['code'] == 'LAYOUT_AUTHORITY']
    assert len(questions) == 1 and questions[0]['affected'][0]['floorIndex'] == 1
    assert next(s for s in r['sources'] if s['id'] == 'manual-before-import')['geometry'] == original
    exact['designJourney']['answers'] = {questions[0]['id']: 'manual-before-import'}
    decided = resolve_sources(exact)
    assert not decided['questions']
    assert decided['project']['customPlan']['floors'] == original['floors']
    assert decided['project']['customPlan']['stairs'] == sorted(original['stairs'], key=sha)


def test_mapped_floor_outside_requested_scope_is_not_silently_omitted(exact):
    p = mapped_project(exact, [mapped_source(exact, 2)])
    p['designJourney']['inputs'][0]['values'] = {**exact['brief'], 'storeys': 2}
    r = resolve_sources(p)
    assert any(q['code'] == 'FLOOR_MAPPING' for q in r['questions'])
    assert next(e for e in r['requirements'] if e['field'] == 'layout')['status'] == 'awaiting clarification'
    assert not prepare(p)['valid']
    assert r['sources'][1]['geometry']['floors'][0]['rooms']


def test_combined_drawings_require_explicit_wall_allowance_resolution(exact):
    sources = [mapped_source(exact, i) for i in range(3)]
    sources[1]['geometry']['wallThickness'] = 200
    p = mapped_project(exact, sources)
    r = resolve_sources(p)
    q = next(q for q in r['questions'] if q['code'] == 'SOURCE_CONFLICT')
    assert 'wall thickness' in q['prompt']
    p['designJourney']['answers'] = {q['id']: 'drawing-1'}
    decided = resolve_sources(p)
    assert not decided['questions']
    assert decided['project']['customPlan']['wallThickness'] == 200
    assert len(decided['project']['customPlan']['floors']) == 3
    assert next(e for e in decided['requirements'] if e['sourceId'] == 'drawing-0' and e['field'] == 'wall_thickness_mm')['status'] == 'excluded'


@pytest.mark.parametrize('mapping', [[True], [-1], [3], [], [[1]]])
def test_invalid_physical_floor_mapping_rejected(exact, mapping):
    source = mapped_source(exact, 1)
    source['floorIndices'] = mapping
    with pytest.raises(DesignError) as error:
        resolve_sources(mapped_project(exact, [source]))
    assert error.value.code == 'SOURCE_FLOOR_INDICES'


def test_saved_compass_programme_supplies_bedroom_goal_with_survey_disabled():
    from test_compass_grids import grid_project
    project, draft = grid_project(4, 4, 2)
    project['compass'] = draft
    project['designJourney'] = {'schema': SCHEMA, 'enabledInputs': ['plot', 'compass']}
    project['brief']['road_bearing_deg'] = 180
    r = resolve_sources(project)
    actual = sum(room['kind'] == 'bedroom' for room in draft['rooms'])
    assert actual == 2 and r['project']['brief']['bedrooms'] == actual
    assert not any(q['code'] == 'BEDROOM_PROGRAMME' for q in prepare(project)['questions'])


def test_prepare_unaccepted_compass_draft(compass):
    draft = compass.pop('compass')
    compass['editorState'] = {'mode': 'compass', 'compassDraft': draft}
    r = prepare(compass)
    assert r['valid'], r['questions']
    assert len(r['floors']) == 3
    assert r['preparedProject']['compassAcceptance']['sourceHash']
    assert next(x for x in r['requirements'] if x['field'] == 'plot-context')['status'] == 'reference-only'
    assert len([x for x in r['requirements'] if x.get('roomId')]) == len(draft['rooms'])


def test_requested_empty_upper_floor_stays_blocked_and_editable(compass):
    compass['compass']['rooms'] = [r for r in compass['compass']['rooms'] if r['floorId'] != compass['compass']['floors'][-1]['id']]
    original = deepcopy(compass)
    r = prepare(compass)
    assert not r['valid'] and r['question']
    assert compass == original
    assert len(compass['compass']['floors']) == 3


def test_unplaced_required_rooms_not_omitted_by_drawn_mode(compass):
    compass['compass']['programme'] = 'drawn'
    compass['compass']['rooms'][0]['regions'] = []
    r = prepare(compass)
    assert not r['valid']
    assert r['issues'][0]['code'] == 'REQUIRED_ROOM_UNPLACED'


def test_partial_scope_needs_explicit_choice(compass):
    compass['designJourney']['scope'] = 1
    r = prepare(compass)
    assert not r['valid'] and r['issues'][0]['code'] == 'SCOPE_CONFIRMATION'
    compass['designJourney']['scopeConfirmed'] = True
    r = prepare(compass)
    assert r['valid'], r['questions']
    assert r['includedFloorCount'] == 1 and r['requestedFloorCount'] == 3
    upper = [x for x in r['requirements'] if x.get('roomId') and x['floorIds'] != [compass['compass']['floors'][0]['id']]]
    assert upper and all(x['status'] == 'excluded' for x in upper)


def test_no_unsigned_or_partial_approval_can_generate(exact):
    r = prepare(exact)
    with pytest.raises(DesignError, match='Approve'):
        verify_approval(r, {'geometryHash': r['geometryHash']}, SECRET)
    one = approve_floor(r, r['floors'][0]['id'], r['floors'][0]['geometryHash'], SECRET)
    with pytest.raises(DesignError, match='First floor'):
        confirm_home(r, [one], r['geometryHash'], SECRET)
    certificate = sign_home(r)
    assert verify_approval(r, certificate, SECRET)
    with pytest.raises(DesignError):
        verify_approval(r, certificate, b'a-different-server-held-secret')
    certificate['floors'].pop()
    with pytest.raises(DesignError):
        verify_approval(r, certificate, SECRET)


def test_appearance_and_revision_changes_preserve_geometry_approval(exact):
    initial = prepare(exact)
    certificate = sign_home(initial)
    for preset in PRESETS:
        p = deepcopy(exact)
        p['draftRevision'] = 999
        p['brief']['title'] = 'A different title'
        p['designJourney']['appearance'] = {'preset': preset}
        r = prepare(p)
        assert r['valid'], r['questions']
        assert r['geometryHash'] == initial['geometryHash']
        assert verify_approval(r, certificate, SECRET)
    assert prepare(p)['appearance']['appearanceHash'] != initial['appearance']['appearanceHash']


def test_geometry_edit_invalidates_coupled_floor_and_home_approval(exact):
    initial = prepare(exact)
    certificate = sign_home(initial)
    changed = deepcopy(exact)
    changed['brief']['floor_height_mm'] += 50
    r = prepare(changed)
    assert r['valid'], r['questions']
    assert r['geometryHash'] != initial['geometryHash']
    assert all(a['geometryHash'] != b['geometryHash'] for a, b in zip(initial['floors'], r['floors']))
    with pytest.raises(DesignError):
        verify_approval(r, certificate, SECRET)


def test_roof_access_landings_and_openings_are_in_the_approval_identity(exact):
    exact['brief']['roof_access'] = True
    r = prepare(exact)
    assert r['valid'], r['questions']
    assert r['canonical']['roofAccess']['openings']
    changed = deepcopy(r['building'])
    changed['rooftop']['openings'][0]['width'] += 50
    assert sha(canonical_model(changed)) != r['geometryHash']


def test_json_roundtrip_keeps_model_sources_and_approval(exact):
    initial = prepare(exact)
    exact['designJourney']['confirmation'] = sign_home(initial)
    exact['designJourney']['answers'] = {'saved-question': 'chosen-option'}
    reopened = json.loads(json.dumps(exact))
    result = prepare(reopened)
    assert result['canonical'] == initial['canonical']
    assert result['sources'] == initial['sources']
    assert verify_approval(result, reopened['designJourney']['confirmation'], SECRET)


def test_regeneration_uses_identical_measured_geometry_and_finish_only(exact):
    from floorforge.intent import fuse
    from floorforge.layout import generate_layout
    from floorforge.exterior import apply_exterior_preferences
    r = prepare(exact)
    regenerated = apply_exterior_preferences(generate_layout(fuse(r['preparedProject'])))
    assert sha(canonical_model(regenerated)) == r['geometryHash']
    assert r['preparedProject']['brief']['change_policy'] == 'finish_only'


@pytest.mark.parametrize('seed', range(10))
def test_metamorphic_source_order_does_not_change_compatible_measurements(seed):
    sources = [
        {'id': 'a', 'kind': 'plot', 'units': 'm', 'values': {'width': 12, 'depth': 18}},
        {'id': 'b', 'kind': 'survey', 'values': {'storeys': 1, 'road_bearing_deg': 180, 'bedrooms': 2}},
        {'id': 'c', 'kind': 'plot', 'units': 'mm', 'values': {'width_mm': 12000}},
        {'id': 'unused', 'kind': 'plot', 'enabled': False, 'values': {'depth_mm': 30000}},
    ]
    expected = resolve_sources({'designJourney': {'schema': SCHEMA, 'inputs': sources}})['project']
    random.Random(seed).shuffle(sources)
    result = resolve_sources({'designJourney': {'schema': SCHEMA, 'inputs': sources}})
    assert not result['questions']
    assert result['project'] == expected


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -1, 1.1, True])
def test_invalid_source_confidence_is_rejected(value):
    p = {'designJourney': {'schema': SCHEMA, 'inputs': [{'id': 'a', 'kind': 'plot', 'confidence': value}]}}
    with pytest.raises((DesignError, ValueError)):
        normalize_sources(p)


def test_legacy_editor_adapter_resolves_selected_inputs_without_validating_rough_layout(exact):
    from floorforge.plan_assist import prepare_plan
    exact['text'] = 'The plot is 80 x 120 feet.'  # deliberately disabled
    original = deepcopy(exact)
    compiled = editing_project(exact, target='exact')
    assert 'designJourney' not in compiled
    assert compiled['brief']['width_mm'] == exact['brief']['width_mm']
    assert prepare_plan(compiled)['valid']
    # A rough invalid rectangle remains editable; final geometry validation is
    # the proposal tool's job, not a prerequisite for opening it.
    exact['customPlan']['floors'][0]['rooms'][0]['polygon'][1][0] += 2000
    assert editing_project(exact, target='exact')['customPlan'] == exact['customPlan']
    assert original['text'] == exact['text']


def test_exact_editor_cannot_silently_take_over_selected_compass(compass):
    with pytest.raises(DesignError) as error:
        editing_project(compass, target='exact')
    assert error.value.code == 'JOURNEY_EDITOR_AUTHORITY'


def test_legacy_tools_return_real_source_questions(exact):
    exact['designJourney']['enabledInputs'].append('text')
    exact['text'] = 'The plot is 80 x 120 feet.'
    with pytest.raises(DesignError) as error:
        editing_project(exact, target='exact')
    assert error.value.code == 'DESIGN_QUESTION'
    assert error.value.details['question']['code'] == 'SOURCE_CONFLICT'


def test_editor_result_protects_pins_rooms_floors_and_original_approvals(exact):
    compiled = editing_project(exact, target='exact')
    ident = compiled['customPlan']['floors'][0]['rooms'][0]['id']
    exact['designJourney'].update(pins={'positions': [ident]}, confirmation={'signature': 'original'}, approvals={'floor': 'original'})
    original = deepcopy(exact)
    moved = deepcopy(compiled['customPlan'])
    moved['floors'][0]['rooms'][0]['polygon'] = [[x+50, y] for x, y in moved['floors'][0]['rooms'][0]['polygon']]
    result = editing_result(exact, {'valid': True, 'customPlan': moved}, compiled)
    assert not result['valid'] and result['errors'][0]['code'] == 'PINNED_POSITION'
    assert result['customPlan'] == compiled['customPlan']
    assert exact == original
    dropped = deepcopy(compiled['customPlan']); dropped['floors'].pop()
    result = editing_result(exact, {'valid': True, 'customPlan': dropped}, compiled)
    assert not result['valid'] and result['errors'][0]['code'] == 'REQUESTED_FLOORS'
    dropped = deepcopy(compiled['customPlan']); dropped['floors'][0]['rooms'].pop()
    result = editing_result(exact, {'valid': True, 'alternatives': [{'customPlan': dropped}]}, compiled)
    assert not result['valid'] and not result['alternatives']


def test_editor_candidate_retains_inputs_and_answers_but_needs_fresh_approval(exact):
    compiled = editing_project(exact, target='exact')
    exact['designJourney'].update(answers={'earlier-choice': 'keep'}, confirmation={'signature': 'original'}, approvals={'floor': 'original'})
    plan = deepcopy(compiled['customPlan'])
    plan['floors'][0]['rooms'][0]['name'] = 'Edited room name'
    result = editing_result(exact, {'valid': True, 'customPlan': plan}, compiled)
    candidate = result['candidate_project']
    assert candidate['designJourney']['answers'] == exact['designJourney']['answers']
    assert candidate['designJourney']['approvals'] == {}
    assert 'confirmation' not in candidate['designJourney']
    assert exact['designJourney']['confirmation']['signature'] == 'original'


def test_single_authoritative_registry_source_tracks_explicit_exact_edits(exact):
    source_plan = deepcopy(exact['customPlan'])
    exact['designJourney']['inputs'] = [
        {'id': 'site', 'kind': 'plot', 'values': exact['brief']},
        {'id': 'trace-source', 'kind': 'plan', 'geometry': source_plan,
         'provenance': {'referenceId': 'calibrated-original', 'mmPerPixel': 10}},
    ]
    exact['customPlan']['floors'][0]['rooms'][0]['name'] = 'Revised exact room'
    exact['editorState'] = {'mode': 'custom', 'customPlan': deepcopy(exact['customPlan'])}
    resolved = resolve_sources(exact)
    source = next(s for s in resolved['sources'] if s['id'] == 'trace-source')
    assert source['geometry'] == exact['customPlan']
    assert source['provenance']['originalGeometry'] == source_plan
    assert source['provenance']['referenceId'] == 'calibrated-original'
    assert exact['designJourney']['inputs'][1]['geometry'] == source_plan


def test_ambiguous_registry_edit_never_silently_rebinds_two_sources(exact):
    source_plan = deepcopy(exact['customPlan'])
    exact['designJourney']['inputs'] = [
        {'id': 'site', 'kind': 'plot', 'values': exact['brief']},
        {'id': 'one', 'kind': 'plan', 'geometry': deepcopy(source_plan)},
        {'id': 'two', 'kind': 'plan', 'geometry': deepcopy(source_plan)},
    ]
    exact['customPlan']['floors'][0]['rooms'][0]['name'] = 'Changed draft'
    exact['editorState'] = {'mode': 'custom', 'customPlan': deepcopy(exact['customPlan'])}
    r = resolve_sources(exact)
    assert any(q['code'] == 'LAYOUT_AUTHORITY' for q in r['questions'])
    assert all(s['geometry'] == source_plan for s in r['sources'] if s['kind'] == 'plan')


def test_ai_editor_candidate_goes_back_through_source_questions(exact):
    from floorforge.ai import proposal_candidate
    exact['designJourney']['enabledInputs'].append('survey')
    compiled = editing_project(exact, target='exact')
    candidate = proposal_candidate(compiled, {'width_mm': 15000})
    result = editing_result(exact, {'candidate_project': candidate, 'validation': 'valid'}, compiled)
    assert result['validation'] == 'awaiting journey review' and not result['valid']
    assert any(q['code'] == 'SOURCE_CONFLICT' for q in result['questions'])
    assert result['candidate_project']['brief'] == exact['brief']


def test_compass_api_resolves_newest_draft_and_disabled_text(compass):
    from floorforge.compass_api import dispatch
    compass['text'] = 'The plot is 80 x 120 feet.'
    latest = deepcopy(compass['compass'])
    latest['rooms'][0]['name'] = 'Current editable room'
    result = dispatch('/api/compass/check', {'project': compass, 'compass': latest})
    assert result['valid'], result['issues']
    assert result['values']['width_mm'] == compass['brief']['width_mm']
    edited = next(r for f in result['customPlan']['floors'] for r in f['rooms'] if r['id'] == latest['rooms'][0]['id'])
    assert edited['name'] == 'Current editable room'
    assert result['designJourney'] == compass['designJourney']
