"""Approval publication and asynchronous jobs must remain revision safe."""
import copy
import json
import threading

import pytest

from floorforge import server
from floorforge.journey_service import JourneyService
from floorforge.model import DesignError, canonical


@pytest.fixture
def state(tmp_path):
    instance = server.State(tmp_path)
    yield instance
    instance.pool.shutdown(wait=True, cancel_futures=True)
    instance.renders.close()


def mock_approved(state, monkeypatch, gate=None):
    def approve(payload):
        if gate:
            gate(payload)
        return {}, {'geometryHash': 'geometry-' + str(payload.get('draftRevision', 0))}
    monkeypatch.setattr(state.journey, 'generation_payload', approve)
    monkeypatch.setattr(server, 'fuse', lambda project: project)


def payload(revision):
    return {'brief': {'title': f'Revision {revision}'}, 'draftRevision': revision,
            'designJourney': {'schema': 'myverandah.journey/1', 'projectId': 'job-regression'}}


def result(revision):
    return {'id': str(revision)*24, 'path': '/unused', 'status': 'published'}


@pytest.mark.parametrize('project', [
    {'customPlan': {}}, {'compass': {}}, {'editorState': {'mode': 'custom'}},
    {'editorState': {'mode': 'compass'}}, {'designJourney': {}}
])
def test_custom_generation_requires_backend_approval_before_queueing(state, project):
    with pytest.raises(DesignError) as caught:
        state.submit(project)
    assert caught.value.code in ('APPROVAL_REQUIRED', 'DESIGN_QUESTION')
    assert not state.jobs
    assert state.latest is None
    assert not (state.out / 'builds').exists()


def test_cancellation_never_publishes_late_uncooperative_result(state, monkeypatch):
    mock_approved(state, monkeypatch)
    started, release = threading.Event(), threading.Event()
    def slow_run(project, out, **kwargs):
        started.set()
        assert release.wait(5)
        return result(1)  # Deliberately ignore cooperative cancellation.
    monkeypatch.setattr(server, 'run', slow_run)
    state.latest = 'previous-build'
    marker = {'id': 'previous-build', 'workspace': 'unchanged'}
    (state.out / 'latest-build.json').write_bytes(canonical(marker))
    ident = state.submit(payload(1))
    try:
        assert started.wait(5)
        assert state.cancel(ident)['status'] == 'cancelled'
    finally:
        release.set()
    state.pool.shutdown(wait=True)
    assert state.jobs[ident]['status'] == 'cancelled'
    assert state.latest == 'previous-build'
    assert json.loads((state.out / 'latest-build.json').read_text()) == marker


def test_cancelled_pipeline_never_recompiles_old_geometry(tmp_path, monkeypatch):
    from floorforge.pipeline import run
    monkeypatch.setattr(JourneyService,'generation_payload',lambda *args:pytest.fail('Cancelled geometry was recompiled'))
    with pytest.raises(DesignError) as caught:
        run(payload(1),tmp_path,cancelled=lambda:True)
    assert caught.value.code=='JOB_CANCELLED'
    assert not list(tmp_path.iterdir())


def test_new_request_supersedes_running_job_and_snapshots_queued_input(state, monkeypatch):
    mock_approved(state, monkeypatch)
    started, release = threading.Event(), threading.Event()
    seen = []
    def run(project, out, **kwargs):
        seen.append(copy.deepcopy(project))
        if project['draftRevision'] == 1:
            started.set()
            assert release.wait(5)
        return result(project['draftRevision'])
    monkeypatch.setattr(server, 'run', run)
    old = state.submit(payload(1))
    assert started.wait(5)
    newer = payload(2)
    try:
        current = state.submit(newer)
        # A queued snapshot cannot change after its approval has been checked.
        newer['brief']['title'] = 'Changed after submit'
        newer['designJourney']['projectId'] = 'Changed after submit'
    finally:
        release.set()
    state.pool.shutdown(wait=True)
    assert state.jobs[old]['status'] == 'cancelled'
    assert state.jobs[current]['status'] == 'done'
    assert state.latest == '2'*24
    assert seen[-1]['brief']['title'] == 'Revision 2'
    assert seen[-1]['designJourney']['projectId'] == 'job-regression'
    assert json.loads((state.out / 'latest-build.json').read_text())['id'] == '2'*24


def test_older_slow_approval_preflight_cannot_replace_newer_request(state, monkeypatch):
    started, release = threading.Event(), threading.Event()
    def gate(project):
        if project['draftRevision'] == 1:
            started.set()
            assert release.wait(5)
    mock_approved(state, monkeypatch, gate)
    seen, errors = [], []
    def run(project, out, **kwargs):
        seen.append(project['draftRevision'])
        return result(project['draftRevision'])
    monkeypatch.setattr(server, 'run', run)
    def submit_old():
        try:
            state.submit(payload(1))
        except DesignError as exc:
            errors.append(exc.code)
    thread = threading.Thread(target=submit_old)
    thread.start()
    try:
        assert started.wait(5)
        current = state.submit(payload(2))
    finally:
        release.set()
        thread.join(5)
    assert not thread.is_alive()
    state.pool.shutdown(wait=True)
    assert seen == [2]
    assert errors == ['JOB_STALE']
    assert state.jobs[current]['status'] == 'done'
    assert state.latest == '2'*24


def test_pruning_cancelled_history_does_not_break_a_running_worker(state, monkeypatch):
    mock_approved(state, monkeypatch)
    started, release = threading.Event(), threading.Event()
    def run(project, out, progress, cancelled):
        if project['draftRevision'] == 1:
            started.set()
            assert release.wait(5)
        if cancelled():
            raise DesignError('JOB_CANCELLED', 'Cancelled by a newer request.')
        progress(stage='exports', status='finished')
        return {'id': f'{project["draftRevision"]:024x}', 'status': 'published'}
    monkeypatch.setattr(server, 'run', run)
    state.submit(payload(1))
    assert started.wait(5)
    try:
        for revision in range(2, 25):
            latest = state.submit(payload(revision))
    finally:
        release.set()
    state.pool.shutdown(wait=True)
    assert state.jobs[latest]['status'] == 'done'
    assert state.latest == f'{24:024x}'
    assert not any(job['status'] in ('queued', 'running', 'error') for job in state.jobs.values())


def test_failed_job_can_retry_without_reusing_its_result(state, monkeypatch):
    mock_approved(state, monkeypatch)
    failed = threading.Event()
    def run(project, out, **kwargs):
        if project['draftRevision'] == 1:
            failed.set()
            raise DesignError('GENERATION_TEST', 'Controlled failure.')
        return result(2)
    monkeypatch.setattr(server, 'run', run)
    first = state.submit(payload(1))
    assert failed.wait(5)
    # Await the worker's error recording, without a timing-dependent sleep.
    state.pool.submit(lambda: None).result(timeout=5)
    assert state.jobs[first]['status'] == 'error'
    second = state.submit(payload(2))
    state.pool.shutdown(wait=True)
    assert state.jobs[second]['status'] == 'done'
    assert state.jobs[first]['status'] == 'error'
    assert state.latest == '2'*24


def small_project():
    from test_compass_prepare import starter
    project, draft = starter()
    draft['programme'] = 'drawn'
    draft['rooms'][0]['regions'] = ['0:0', '0:1']
    project['compass'] = draft
    project['brief']['road_bearing_deg'] = 180
    project['designJourney'] = {'schema': 'myverandah.journey/1', 'enabledInputs': ['plot', 'compass'],
                                'appearance': {'preset': 'warm-natural'}}
    return project


def test_reopen_displays_resolved_text_over_excluded_form_revision(tmp_path):
    project={'brief':{'bedrooms':3},'text':'My plot is 50 x 80 feet. 2 bedrooms.',
             'sources':[{'id':'studio-field-edits','kind':'form','enabled':True,'values':{'bedrooms':3}}],
             'designJourney':{'schema':'myverandah.journey/1','enabledInputs':['text']}}
    result=JourneyService(tmp_path).inputs(project)
    assert result['values']['bedrooms']==2
    assert result['values']['width_mm']==15240
    assert result['questions']  # Road/front and floor count remain unanswered.
    assert result['planHash'] is None


def test_published_floor_approval_api_matches_frontend_contract_and_survives_reopen(tmp_path):
    service = JourneyService(tmp_path)
    project = small_project()
    prepared = service.prepare(project)
    assert prepared['valid'], prepared.get('issues')
    floor = prepared['floors'][0]
    approval = service.approve({'preparationId': prepared['preparationId'], 'floorId': floor['id'],
                                'geometryHash': prepared['geometryHash'], 'floorHash': floor['geometryHash']})['approval']
    approvals = {floor['id']: approval}
    confirmation = service.confirm({'preparationId': prepared['preparationId'], 'geometryHash': prepared['geometryHash'],
                                     'approvals': approvals})['confirmation']
    project['designJourney'].update(approvals=approvals, confirmation=confirmation)
    reopened = json.loads(json.dumps(project))
    compiled, checked = JourneyService(tmp_path).generation_payload(reopened)
    assert checked['geometryHash'] == prepared['geometryHash']
    assert compiled['compassScope'] == 1
    assert reopened == project
    # A local signing key is never embedded in portable project data.
    assert 'signing' not in json.dumps(project)
    assert (tmp_path / '.journey-signing-key').read_bytes()


def test_modified_published_drawing_cannot_be_approved(tmp_path):
    service = JourneyService(tmp_path)
    prepared = service.prepare(small_project())
    assert prepared['valid']
    floor = prepared['floors'][0]
    path = tmp_path / 'preparations' / prepared['preparationId'] / 'floor-1.svg'
    path.write_text(path.read_text()+'\n<!-- modified after publication -->')
    with pytest.raises(DesignError) as caught:
        service.approve({'preparationId': prepared['preparationId'], 'floorId': floor['id'],
                         'geometryHash': prepared['geometryHash'], 'floorHash': floor['geometryHash']})
    assert caught.value.code == 'PREPARATION_MODIFIED'


@pytest.mark.parametrize('damage', ['svg', 'manifest', 'missing'])
def test_retry_recovers_damaged_plan_publication_without_editing_project(tmp_path, damage):
    service = JourneyService(tmp_path)
    project = small_project()
    before = copy.deepcopy(project)
    first = service.prepare(project)
    base = tmp_path / 'preparations' / first['preparationId']
    if damage == 'svg':
        (base / 'floor-1.svg').write_text('damaged drawing')
    elif damage == 'missing':
        (base / 'drawings.pdf').unlink()
    else:
        (base / 'manifest.json').write_text('{"files": {}}')
    restored = service.prepare(project)
    assert project == before
    assert restored['preparationId'] == first['preparationId']
    assert restored['geometryHash'] == first['geometryHash']
    assert service.load(restored['preparationId'])['canonical'] == first['canonical']
    assert (base / 'drawings.pdf').read_bytes().startswith(b'%PDF')
    assert '<svg' in (base / 'floor-1.svg').read_text()
    floor = restored['floors'][0]
    assert service.approve({'preparationId': restored['preparationId'], 'floorId': floor['id'],
                            'geometryHash': floor['geometryHash']})['approval']['signature']
    assert len(list((tmp_path / '.damaged-preparations').iterdir())) == 1


def test_unknown_or_traversing_preparation_id_is_rejected(tmp_path):
    service = JourneyService(tmp_path)
    for ident in (None, '../.journey-signing-key', '0'*32):
        with pytest.raises(DesignError) as caught:
            service.load(ident)
        assert caught.value.code in ('PREPARATION_ID', 'PREPARATION_MISSING')
