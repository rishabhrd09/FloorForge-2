"""A long-running Python server must not pretend to have loaded newer routes."""
import copy
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

import pytest

from floorforge import server
from floorforge.model import DesignError


def request(instance, path, body=None, token=None):
    connection=http.client.HTTPConnection('127.0.0.1',instance.server_port,timeout=5)
    headers={'Content-Type':'application/json'}
    if token:headers['X-FloorForge-Token']=token
    try:
        connection.request('GET' if body is None else 'POST',path,
                           body=None if body is None else json.dumps(body),headers=headers)
        response=connection.getresponse()
        return response.status,response.read()
    finally:
        connection.close()


@pytest.fixture
def studio(tmp_path,monkeypatch):
    # Other agents may edit assets while these tests run. Simulate an immutable
    # checkout except in the tests that deliberately change its disk identity.
    monkeypatch.setattr(server,'kernel_hash',lambda:server.LOADED_BUILD_ID)
    instance=server.make_server(tmp_path)
    thread=threading.Thread(target=instance.serve_forever,daemon=True);thread.start()
    try:
        yield instance
    finally:
        instance.shutdown();instance.server_close();thread.join(timeout=5)
        instance.state.pool.shutdown(wait=True,cancel_futures=True)
        instance.state.renders.close()


def test_session_reports_loaded_identity_separately_from_changed_files(studio,monkeypatch):
    status,raw=request(studio,'/api/session');initial=json.loads(raw)
    assert status==200 and initial['journey_api_version']==1
    assert initial['backend_build_id']==initial['loaded_build_id']==initial['disk_build_id']
    assert initial['restart_required'] is False
    monkeypatch.setattr(server,'kernel_hash',lambda:'newer-files-on-disk')
    status,raw=request(studio,'/api/session');changed=json.loads(raw)
    assert status==200
    assert changed['backend_build_id']==initial['backend_build_id']
    assert changed['loaded_build_id']==initial['loaded_build_id']
    assert changed['disk_build_id']=='newer-files-on-disk'
    assert changed['restart_required'] is True
    assert changed['token']==initial['token']


def test_changed_server_rejects_writes_before_consuming_or_overwriting_draft(studio,monkeypatch):
    project={'brief':{'width_mm':12192,'depth_mm':18288,'storeys':3,'road_bearing_deg':270},
             'designJourney':{'schema':'myverandah.journey/1','enabledInputs':['plot','compass']}}
    original=copy.deepcopy(project)
    monkeypatch.setattr(studio.state.journey,'inputs',lambda *_:pytest.fail('Stale route consumed the draft'))
    monkeypatch.setattr(server,'kernel_hash',lambda:'changed')
    status,raw=request(studio,'/api/design/inputs',{'project':project},studio.state.token)
    assert status==503
    error=json.loads(raw)
    assert error['code']=='STUDIO_RESTART_REQUIRED'
    assert 'Restart MyVerandah' in error['message']
    assert project==original and not studio.state.jobs
    # Read-only sample browsing remains available while a restart is needed.
    assert request(studio,'/api/samples')[0]==200
    assert request(studio,'/api/design/inputs',{'project':project})[0]==403


def test_new_state_cannot_disguise_an_already_loaded_old_module(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'kernel_hash',lambda:'newer-than-imported-server-module')
    state=server.State(tmp_path)
    try:
        assert state.loaded_build_id==server.LOADED_BUILD_ID
        assert state.runtime_status()['restart_required'] is True
    finally:
        state.pool.shutdown(wait=True,cancel_futures=True);state.renders.close()


def test_restart_guard_still_allows_cancellation_and_clearing_credentials(studio,monkeypatch):
    ident='a'*16
    studio.state.jobs[ident]={'id':ident,'status':'queued','events':[]}
    monkeypatch.setattr(server,'kernel_hash',lambda:'changed')
    status,raw=request(studio,'/api/jobs/'+ident+'/cancel',{},studio.state.token)
    assert status==200 and json.loads(raw)['status']=='cancelled'
    status,raw=request(studio,'/api/ai/clear',{},studio.state.token)
    assert status==200 and json.loads(raw)['provider']=='off'


def test_current_studio_can_be_reused_without_replacing_projects_or_session(studio):
    assert server.inspect_studio(studio.server_port,studio.state.out)=='current'
    assert server.existing_studio(studio.server_port,studio.state.out)
    token=studio.state.token
    assert server.serve(studio.state.out,studio.server_port,False)==0
    assert studio.state.token==token


def test_stale_studio_is_not_silently_reused(studio,monkeypatch):
    token=studio.state.token
    marker=studio.state.out/'keep-project.json';marker.write_text('{"keep":true}')
    monkeypatch.setattr(server,'kernel_hash',lambda:'updated-checkout')
    assert server.inspect_studio(studio.server_port,studio.state.out)=='stale'
    assert not server.existing_studio(studio.server_port,studio.state.out)
    with pytest.raises(DesignError) as caught:
        server.serve(studio.state.out,studio.server_port,False)
    assert caught.value.code=='STUDIO_RESTART_REQUIRED'
    assert '--port 0' in str(caught.value)
    assert marker.read_text()=='{"keep":true}' and studio.state.token==token


@pytest.mark.parametrize('legacy_identity',[True,False])
def test_legacy_dynamic_disk_hash_cannot_claim_the_new_api(tmp_path,monkeypatch,legacy_identity):
    # This is the observed legacy wire contract: old route table, but a build
    # hash computed from the freshly edited files rather than the loaded code.
    monkeypatch.setattr(server,'kernel_hash',lambda:server.LOADED_BUILD_ID)
    class Legacy(BaseHTTPRequestHandler):
        server_version='FloorForge/0.4'
        def do_GET(self):
            data={'version':'0.4','defaults':{},'backend_build_id':server.LOADED_BUILD_ID}
            if legacy_identity:data['launch_identity']=server.launch_identity(tmp_path)
            raw=json.dumps(data).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def log_message(self,*args):pass
    legacy=HTTPServer(('127.0.0.1',0),Legacy)
    thread=threading.Thread(target=legacy.serve_forever,daemon=True);thread.start()
    try:
        assert server.inspect_studio(legacy.server_port,tmp_path)=='stale'
        assert not server.existing_studio(legacy.server_port,tmp_path)
        with pytest.raises(DesignError) as caught:
            server.serve(tmp_path,legacy.server_port,False)
        assert caught.value.code=='STUDIO_RESTART_REQUIRED'
    finally:
        legacy.shutdown();legacy.server_close();thread.join(timeout=5)


def test_other_project_identity_does_not_get_reused_or_claimed_as_ours(studio,tmp_path):
    assert server.inspect_studio(studio.server_port,tmp_path/'other')=='different'
    with pytest.raises(DesignError) as caught:
        server.serve(tmp_path/'other',studio.server_port,False)
    assert caught.value.code=='PORT_IN_USE'
