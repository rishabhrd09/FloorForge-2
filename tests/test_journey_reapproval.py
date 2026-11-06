"""Edits and portable imports must always offer a usable approval path."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from floorforge.design_journey import (
    _signature, approve_floor, confirm_home, prepare, reusable_floor_approvals,
    verify_approval,
)
from floorforge.journey_service import JourneyService
from floorforge.model import DesignError

SECRET = b'local-studio-secret-for-tests'


@pytest.fixture
def project():
    p = json.loads((Path(__file__).parents[1] / 'examples/custom/g2-terrace.floorforge.json').read_text())
    p['designJourney'] = {'schema': 'myverandah.journey/1', 'enabledInputs': ['plot', 'dxf']}
    return p


def certificates(prepared, secret=SECRET):
    assert prepared['valid'], prepared.get('issues')
    return {floor['id']: approve_floor(prepared, floor['id'], floor['geometryHash'], secret)
            for floor in prepared['floors']}


@pytest.mark.parametrize('edit', ['name', 'opening'])
def test_independent_floor_edit_reuses_other_signed_floor_reviews(project, edit):
    before = prepare(project)
    approvals = certificates(before)
    old_confirmation = confirm_home(before, approvals, before['geometryHash'], SECRET)
    if edit == 'name':
        project['customPlan']['floors'][1]['rooms'][2]['name'] = 'Guest bedroom'
    else:
        project['customPlan']['floors'][1]['openings'][2]['offset'] += 50
    after = prepare(project)
    assert after['valid'], after.get('issues')
    retained = reusable_floor_approvals(after, approvals, SECRET)
    assert set(retained) == {'custom-floor-0', 'custom-floor-2'}
    assert all(retained[key] == approvals[key] for key in retained)
    with pytest.raises(DesignError, match='First floor'):
        confirm_home(after, approvals, after['geometryHash'], SECRET)
    first = after['floors'][1]
    retained[first['id']] = approve_floor(after, first['id'], first['geometryHash'], SECRET)
    current = confirm_home(after, retained, after['geometryHash'], SECRET)
    assert verify_approval(after, current, SECRET)
    with pytest.raises(DesignError):
        verify_approval(after, old_confirmation, SECRET)


@pytest.mark.parametrize('edit', ['stairs', 'support-envelope'])
def test_shared_relationship_edits_invalidate_all_floor_reviews(project, edit):
    before = prepare(project)
    approvals = certificates(before)
    if edit == 'stairs':
        project['customPlan']['stairs'][0]['landing'] = 1000
    else:
        project['brief']['width_mm'] += 100
    after = prepare(project)
    assert after['valid'], after.get('issues')
    assert reusable_floor_approvals(after, approvals, SECRET) == {}
    with pytest.raises(DesignError):
        confirm_home(after, approvals, after['geometryHash'], SECRET)


@pytest.mark.parametrize('tamper', ['signature', 'schema', 'floor-id'])
def test_reusable_approval_requires_valid_signature_schema_and_floor(project, tamper):
    prepared = prepare(project)
    approvals = certificates(prepared)
    first = prepared['floors'][0]['id']
    record = approvals[first]
    if tamper == 'signature':
        record['signature'] = 'forged'
    else:
        record['schema' if tamper == 'schema' else 'floorId'] = 'wrong-value'
        record['signature'] = _signature({k: v for k, v in record.items() if k != 'signature'}, SECRET)
    assert first not in reusable_floor_approvals(prepared, approvals, SECRET)
    with pytest.raises(DesignError):
        confirm_home(prepared, approvals, prepared['geometryHash'], SECRET)


def test_portable_foreign_approvals_are_unapproved_and_can_be_reviewed_locally(project, tmp_path):
    original = JourneyService(tmp_path / 'original')
    original.out.mkdir()
    before = original.prepare(project)
    approvals = certificates(before, original.secret())
    project['designJourney'].update(approvals=approvals,
        confirmation=confirm_home(before, approvals, before['geometryHash'], original.secret()))
    same = original.prepare(project)
    assert same['approvals'] == approvals
    assert same['confirmation'] == project['designJourney']['confirmation']

    target = JourneyService(tmp_path / 'imported')
    target.out.mkdir()
    snapshot = deepcopy(project)
    imported = target.prepare(project)
    assert imported['valid'] and imported['geometryHash'] == before['geometryHash']
    assert imported['approvals'] == {} and imported['confirmation'] is None
    assert project == snapshot
    local = {floor['id']: target.approve({'preparationId': imported['preparationId'],
              'floorId': floor['id'], 'geometryHash': floor['geometryHash']})['approval']
             for floor in imported['floors']}
    current = target.confirm({'preparationId': imported['preparationId'],
                              'approvals': local, 'geometryHash': imported['geometryHash']})['confirmation']
    project['designJourney'].update(approvals=local, confirmation=current)
    _, prepared = target.generation_payload(project)
    assert prepared['geometryHash'] == before['geometryHash']


def test_blocked_preparation_cannot_advertise_usable_certificates(project, tmp_path):
    service = JourneyService(tmp_path)
    valid = service.prepare(project)
    approvals = certificates(valid, service.secret())
    project['designJourney'].update(approvals=approvals,
        confirmation=confirm_home(valid, approvals, valid['geometryHash'], service.secret()))
    project['brief']['width_mm'] = 1
    result = service.prepare(project)
    assert not result['valid']
    assert result['approvals'] == {} and result['confirmation'] is None
