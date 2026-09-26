import json,threading,urllib.request,urllib.error,pytest
from floorforge.ai import Assist,parse_proposal,NoRedirect
from floorforge.model import DesignError
from floorforge.server import make_server

@pytest.mark.parametrize('proposal',[{'patch':{'execute':'rm'},'critique':[],'rationale':''},{'patch':{'soil':'rocky'},'critique':[],'rationale':''},{'patch':{},'critique':'bad','rationale':''},{'patch':{},'critique':[],'rationale':'','extra':1}])
def test_ai_never_accepts_arbitrary_code_or_protected_assumptions(proposal):
    with pytest.raises(DesignError):parse_proposal(json.dumps(proposal))

def test_ai_schema_valid():assert parse_proposal('{"patch":{"style":"tropical"},"critique":[],"rationale":"Preference"}')['patch']['style']=='tropical'

def test_ai_session_memory_and_clear(tmp_path):
    a=Assist();a.configure({'provider':'anthropic','model':'user-model','key':'secret-test-key'});s=a.status()
    assert s['key_present'] and 'secret-test-key' not in json.dumps(s);assert 'secret-test-key' not in repr(a._config)
    assert a.estimate({'brief':{}})['estimated_usd'] is None
    a.clear();assert not a.status()['key_present'];assert not list(tmp_path.iterdir())

@pytest.mark.parametrize('endpoint',['http://example.org','https://user:key@example.org','https://example.org?key=secret','file:///tmp/a'])
def test_cloud_endpoint_rejected(endpoint):
    with pytest.raises(DesignError):Assist().configure({'provider':'openai-compatible','endpoint':endpoint,'model':'x','key':'test'})

@pytest.mark.parametrize('endpoint',['http://192.168.1.1:8080','http://localhost:8080','https://example.org'])
def test_local_only_literal_loopback(endpoint):
    with pytest.raises(DesignError):Assist().configure({'provider':'local','endpoint':endpoint,'model':'x'})

def test_ai_off_never_calls_provider():
    with pytest.raises(DesignError) as e:Assist().propose({},'test',True)
    assert e.value.code=='AI_OFF'

def test_ai_request_requires_confirm():
    with pytest.raises(DesignError) as e:Assist().propose({},'test',False)
    assert e.value.code=='AI_CONSENT'

def test_redirect_does_not_forward_key():
    with pytest.raises(DesignError):NoRedirect().redirect_request(None,None,302,'Moved',{},'https://other.example')

@pytest.fixture
def http_server(tmp_path):
    s=make_server(tmp_path);t=threading.Thread(target=s.serve_forever,daemon=True);t.start();yield s
    s.shutdown();s.server_close();s.state.pool.shutdown(wait=True)

def request(s,path,body=None,headers=None):
    h={'Content-Type':'application/json',**(headers or {})};r=urllib.request.Request(f'http://127.0.0.1:{s.server_port}'+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
    try:
        with urllib.request.urlopen(r,timeout=5) as response:return response.status,response.read()
    except urllib.error.HTTPError as e:return e.code,e.read()

def test_live_api_token_and_origin(http_server):
    code,data=request(http_server,'/api/session');assert code==200;token=json.loads(data)['token']
    assert request(http_server,'/api/intent',{'brief':{}})[0]==403
    assert request(http_server,'/api/intent',{'brief':{}},{'X-FloorForge-Token':token})[0]==200
    assert request(http_server,'/api/intent',{'brief':{}},{'X-FloorForge-Token':token,'Origin':'https://other.example'})[0]==403

def test_local_host_rebinding_blocked(http_server):assert request(http_server,'/api/session',headers={'Host':'evil.example'})[0]==403

def test_path_traversal_not_exposed(http_server):
    code,_=request(http_server,'/builds/'+'a'*24+'/../../../../etc/passwd');assert code==404

def test_health_and_static_ui(http_server):
    code,data=request(http_server,'/');assert code==200 and b'Generate my home' in data
    assert request(http_server,'/viewer.js')[0]==200
    assert request(http_server,'/api/ai/status')[0]==200
