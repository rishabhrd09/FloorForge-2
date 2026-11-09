"""Real loopback HTTP coverage for the no-AI approval and publication journey."""
from __future__ import annotations

import copy
import hashlib
import http.client
import io
import json
from pathlib import Path
import threading
import time

import ezdxf
import pytest

from floorforge.model import sha
from floorforge.server import make_server

ROOT = Path(__file__).resolve().parents[1]


class Client:
    def __init__(self, server):
        self.server = server
        self.token = None
        status, session = self.json('/api/session')
        assert status == 200
        self.token = session['token']

    def request(self, path, body=None, *, authenticated=True, origin=None, raw=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=45)
        headers = {'Content-Type': 'application/json'}
        if authenticated and self.token:
            headers['X-FloorForge-Token'] = self.token
        if origin:
            headers['Origin'] = origin
        data = raw if raw is not None else json.dumps(body).encode() if body is not None else None
        try:
            connection.request('POST' if data is not None else 'GET', path, body=data, headers=headers)
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def json(self, path, body=None, **kwargs):
        status, data, _ = self.request(path, body, **kwargs)
        return status, json.loads(data)

    def wait_job(self, ident, timeout=90):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status, job = self.json('/api/jobs/' + ident)
            assert status == 200
            if job['status'] in ('done', 'error', 'cancelled'):
                return job
            # Bounded polling of a real local job; no external service needed.
            threading.Event().wait(.05)
        pytest.fail('Local approved generation did not complete within the bounded test wait.')


@pytest.fixture
def client(tmp_path):
    server = make_server(tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield Client(server)
    finally:
        server.shutdown()
        server.server_close()
        server.state.pool.shutdown(wait=True, cancel_futures=True)
        server.state.renders.close()
        thread.join(timeout=5)


def three_floor_project():
    fixture = json.loads((ROOT / 'tests/fixtures/compass-three-floors.json').read_text())
    project = {**fixture['project'], 'compass': fixture['compass']}
    project['brief']['road_bearing_deg'] = 180
    project['designJourney'] = {'schema': 'myverandah.journey/1', 'projectId': 'http-three-floors',
                                'enabledInputs': ['plot', 'compass'], 'answers': {}, 'approvals': {},
                                'appearance': {'preset': 'warm-natural'}}
    return project


def exact_edit_project():
    project=json.loads((ROOT / 'examples/custom/g2-terrace.floorforge.json').read_text())
    project['editorState']={'mode':'custom'}
    project['text']='My plot is 50 x 80 feet.'
    project['designJourney']={'schema':'myverandah.journey/1', 'enabledInputs':['plot'],
                              'answers':{}, 'approvals':{}, 'appearance':{'preset':'warm-natural'}}
    return project


@pytest.mark.parametrize('route,nested', [
    ('/api/plan/prepare',False), ('/api/plan/smart-fit',False),
    ('/api/plan/validate',False), ('/api/plan/suggest-openings',False),
    ('/api/plan/upper-constraints',True), ('/api/plan/alternatives',True),
])
def test_existing_edit_tools_consume_selected_journey_inputs(client,route,nested):
    project=exact_edit_project();before=copy.deepcopy(project)
    body={'project':project,'floor':1} if nested else project
    status,result=client.json(route,body)
    assert status==200,result
    assert result.get('code')!='PROJECT_FIELDS'
    if 'customPlan' in result:
        assert [floor['id'] for floor in result['customPlan']['floors']]==[floor['id'] for floor in project['customPlan']['floors']]
    assert project==before
    assert not client.server.state.jobs
    # The same text becomes a real conflict when enabled, before any edit.
    project['designJourney']['enabledInputs'].append('text')
    status,conflict=client.json(route,{'project':project,'floor':1} if nested else project)
    assert status==400 and conflict['code']=='DESIGN_QUESTION',conflict


def test_room_board_and_local_assistant_accept_journey_metadata_without_network(client,monkeypatch):
    from tests.test_room_board import project as board_project, board
    from floorforge import local_planner
    project=board_project();project['brief']['road_bearing_deg']=180
    project['designJourney']={'schema':'myverandah.journey/1','enabledInputs':['plot']}
    status,result=client.json('/api/plan/arrange',{'project':project,'board':board()})
    assert status==200,result
    assert len(result['customPlan']['floors'])==project['brief']['storeys']
    monkeypatch.setattr(local_planner,'call',lambda *args,**kwargs:pytest.fail('No provider request was authorized'))
    status,result=client.json('/api/local-plan/propose',{'project':exact_edit_project(),'instruction':'Help','confirm':False})
    assert status==400 and result['code']!='PROJECT_FIELDS'
    status,result=client.json('/api/ai/propose',{'project':exact_edit_project(),'instruction':'Help','confirm':False})
    assert status==400 and result['code']=='AI_CONSENT',result


def test_disabled_compass_flag_blocks_mutating_consumers_and_keeps_draft_readable(client, monkeypatch):
    monkeypatch.setenv('FLOORFORGE_COMPASS', '0')
    status, session = client.json('/api/session')
    assert status == 200 and session['compass']['enabled'] is False
    project = three_floor_project()
    original = copy.deepcopy(project)
    for route, body in (
        ('/api/compass/convert', {'project': project, 'compass': project['compass']}),
        ('/api/compass/prepare', {'project': project, 'compass': project['compass']}),
        ('/api/generate', project),
    ):
        status, error = client.json(route, body)
        assert status == 400 and error['code'] == 'COMPASS_DISABLED'
    status, editable = client.json('/api/design/inputs', {'project': project})
    assert status == 200 and editable['editable'] and editable['planHash'] is None
    assert next(s for s in editable['sources'] if s['kind'] == 'compass')['geometry'] == original['compass']
    assert project == original
    assert not client.server.state.jobs


@pytest.mark.parametrize('project', [
    {'brief': {}}, {'brief': {'storeys': 1}, 'editorState': {'mode': 'automatic'}},
    {'customPlan': {}}, {'compass': {}}, {'editorState': {'mode': 'custom'}},
])
def test_http_generation_has_no_metadata_bypass_of_approval(client, project):
    status, error = client.json('/api/generate', project)
    assert status == 400 and error['code'] == 'APPROVAL_REQUIRED'
    assert not client.server.state.jobs
    assert not (client.server.state.out / 'builds').exists()


def test_inputs_endpoint_restores_conflicting_and_invalid_drafts_without_publication(client):
    project = three_floor_project()
    project['designJourney']['enabledInputs'].append('text')
    project['text'] = 'My plot is 50 x 80 feet.'
    # Geometry is intentionally incomplete and must still be recoverable.
    project['compass']['rooms'][0]['regions'] = []
    project['draftRevision'] = 27
    original = copy.deepcopy(project)
    status, editable = client.json('/api/design/inputs', {'project': project})
    assert status == 200 and editable['editable']
    assert editable['planHash'] is None and editable['draftRevision'] == 27
    assert any(q['code'] == 'SOURCE_CONFLICT' for q in editable['questions'])
    source = next(s for s in editable['sources'] if s['kind'] == 'compass')
    assert source['geometry'] == original['compass']
    assert project == original
    assert not (client.server.state.out / 'builds').exists()
    assert not (client.server.state.out / 'preparations').exists()
    status, blocked = client.json('/api/design/prepare', {'project': project})
    assert status == 200 and not blocked['valid'] and blocked['question']
    assert not blocked.get('preparationId')


def test_disabled_text_identity_and_provenance_survive_actual_http_preparation(client):
    project = three_floor_project()
    project['text'] = 'My plot is 50 x 80 feet. Seven bedrooms and a helipad.'
    status, prepared = client.json('/api/design/prepare', {'project': project})
    assert status == 200 and prepared['valid'], prepared.get('issues')
    source = next(s for s in prepared['sources'] if s['kind'] == 'text')
    assert source['enabled'] is False
    assert source['text'] == project['text'] and source['provenance']
    entries = [r for r in prepared['requirements'] if r['sourceId'] == source['id']]
    assert entries and all(r['status'] == 'excluded' for r in entries)
    assert prepared['canonical']['site']['width_mm'] == project['brief']['width_mm']
    assert len(prepared['floors']) == 3


@pytest.mark.parametrize('route,body', [
    ('/api/design/approve', {'preparationId': '../secret'}),
    ('/api/design/approve', {'preparationId': '0'*32, 'floorId': 'unknown'}),
    ('/api/design/confirm', {'preparationId': '0'*32, 'geometryHash': 'forged', 'approvals': {}}),
])
def test_unknown_or_malformed_preparation_ids_are_recoverable_http_errors(client, route, body):
    status, error = client.json(route, body)
    assert status == 400
    assert error['code'] in ('PREPARATION_ID', 'PREPARATION_MISSING')
    assert 'Traceback' not in json.dumps(error)
    assert client.json('/api/session')[0] == 200


def test_malformed_json_and_unknown_preparation_download_do_not_break_server(client):
    status, data, _ = client.request('/api/design/approve', raw=b'{invalid json')
    assert status == 400 and json.loads(data)['code'] == 'REQUEST_ERROR'
    assert client.request('/preparations/'+'0'*32+'/floor-1.svg')[0] == 404
    assert client.request('/preparations/'+'0'*32+'/../.journey-signing-key')[0] == 404
    assert client.json('/api/session')[0] == 200


def test_cancellation_endpoints_require_token_and_local_origin(client):
    for route in ('/api/jobs/'+'a'*16+'/cancel', '/api/renders/'+'a'*16+'/cancel'):
        assert client.json(route, {}, authenticated=False)[0] == 403
        assert client.json(route, {}, origin='https://untrusted.example')[0] == 403
        status, error = client.json(route, {})
        assert status == 400 and error['code'] in ('JOB_UNKNOWN', 'RENDER_UNKNOWN')


def test_render_rejects_missing_and_malformed_build_without_starting_blender(client, monkeypatch):
    # Validate the build contract on machines with or without Blender installed;
    # no process is launched in this test.
    monkeypatch.setattr('floorforge.journey_render.blender_path', lambda: '/unused/blender')
    monkeypatch.setattr('floorforge.journey_render.subprocess.Popen', lambda *a, **k: pytest.fail('An invalid render request started a process.'))
    for body in ({}, {'buildId': '../../invalid'}, {'buildId': 'g'*24}, {'buildId': 'a'*24}):
        status, error = client.json('/api/design/render', body)
        assert status == 400 and error['code'] == 'RENDER_BUILD'
    assert not client.server.state.renders.jobs


def test_three_floor_http_approval_generation_and_downloads_share_geometry(client):
    project = three_floor_project()
    status, prepared = client.json('/api/design/prepare', {'project': project})
    assert status == 200 and prepared['valid'], prepared.get('issues')
    assert len(prepared['floors']) == 3
    assert not (client.server.state.out / 'builds').exists()  # 2D publication alone creates no 3D.
    for floor in prepared['floors']:
        status, approved = client.json('/api/design/approve', {
            'preparationId': prepared['preparationId'], 'floorId': floor['id'], 'geometryHash': floor['geometryHash']})
        assert status == 200
        project['designJourney']['approvals'][floor['id']] = approved['approval']
    # All floor certificates are required by the backend, not only the UI.
    approvals = project['designJourney']['approvals']
    status, error = client.json('/api/design/confirm', {
        'preparationId': prepared['preparationId'], 'geometryHash': prepared['geometryHash'],
        'approvals': dict(list(approvals.items())[:2])})
    assert status == 400 and error['code'] == 'APPROVAL_REQUIRED'
    status, confirmed = client.json('/api/design/confirm', {
        'preparationId': prepared['preparationId'], 'geometryHash': prepared['geometryHash'], 'approvals': approvals})
    assert status == 200
    project['designJourney']['confirmation'] = confirmed['confirmation']
    status, queued = client.json('/api/generate', project)
    assert status == 202
    job = client.wait_job(queued['job_id'])
    assert job['status'] == 'done', job.get('error')
    assert job['result']['geometryHash'] == prepared['geometryHash']
    build_id = job['result']['id']
    prefix = '/builds/' + build_id + '/'
    status, model = client.json(prefix+'canonical.json')
    assert status == 200 and sha(model) == prepared['geometryHash']
    status, scene = client.json(prefix+'scene.json')
    assert status == 200 and scene['geometryHash'] == prepared['geometryHash'] and scene['storeys'] == 3
    status, building = client.json(prefix+'building.json')
    assert status == 200 and building['geometryHash'] == prepared['geometryHash'] and building['storeys'] == 3
    assert {r['id'] for r in scene['rooms']} == {r['id'] for r in model['rooms']}
    status, portable = client.json(prefix+'project.floorforge.json')
    assert status == 200 and portable['compass'] == project['compass']
    assert portable['designJourney']['approvals'] == approvals
    assert portable['designJourney']['confirmation'] == confirmed['confirmation']
    status, manifest = client.json(prefix+'manifest.json')
    assert status == 200 and manifest['geometryHash'] == prepared['geometryHash']
    downloads = {}
    for name in ('drawings.pdf', 'floorplans.dxf', 'model.glb'):
        status, data, _ = client.request(prefix+name)
        assert status == 200 and data
        assert hashlib.sha256(data).hexdigest() == manifest['files'][name]
        downloads[name] = data
    assert downloads['drawings.pdf'].startswith(b'%PDF')
    assert downloads['model.glb'].startswith(b'glTF')
    drawing = ezdxf.read(io.StringIO(downloads['floorplans.dxf'].decode('utf-8')))
    labels = [e.dxf.text for e in drawing.modelspace().query('TEXT')]
    assert all(any(f'FLOOR {index} / TRUE MILLIMETRES' in label for label in labels) for index in range(3))
    assert {'GROUND', 'FLOOR-1', 'FLOOR-2'} <= set(drawing.layouts.names())
    status, reopened = client.json('/api/design/prepare', {'project': portable})
    assert status == 200 and reopened['valid'] and reopened['geometryHash'] == prepared['geometryHash']
    # The actual 2D downloads are available before and after the scene job.
    status, canonical_data, _ = client.request(prepared['downloads']['canonical.json'])
    assert status == 200 and sha(json.loads(canonical_data)) == prepared['geometryHash']
    assert client.request(prepared['downloads']['drawings.pdf'])[1].startswith(b'%PDF')
    # A new measured geometry cannot reuse the old signed approval.
    changed = copy.deepcopy(project)
    changed['brief']['width_mm'] += 250
    status, error = client.json('/api/generate', changed)
    assert status == 400 and error['code'] in ('APPROVAL_REQUIRED', 'DESIGN_QUESTION')
    assert client.server.state.latest == build_id
