"""Loopback-only studio server. No telemetry, terminal subprocesses or credential files."""
from __future__ import annotations
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
import concurrent.futures,hashlib,json,mimetypes,secrets,threading,time,webbrowser
from . import __version__
from .model import *
from .pipeline import run,ROOT,runtime_versions,kernel_hash
from .intent import fuse,SETBACKS_BY_DEPTH,SETBACKS_BY_WIDTH
from .ai import Assist
from .exterior import list_available_themes

# The open-space tables behind intent.derive_setbacks, for the studio's live plot summary (JSON has no infinity).
SETBACK_TABLES={'depth':[[None if math.isinf(l) else l,f,r] for l,f,r in SETBACKS_BY_DEPTH],
                'width':[[None if math.isinf(l) else l,sd] for l,sd in SETBACKS_BY_WIDTH]}

class State:
    def __init__(self,out):
        self.out=Path(out);self.token=secrets.token_urlsafe(32);self.jobs={};self.lock=threading.Lock();self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1);self.ai=Assist();self.latest=None
    def submit(self,payload):
        fuse(payload) # Fail invalid input before queueing expensive geometry.
        with self.lock:
            if any(j['status'] in ('queued','running') for j in self.jobs.values()):raise DesignError('BUSY','A design is already generating. Wait for it to finish.')
            if len(self.jobs)>20:self.jobs={k:v for k,v in list(self.jobs.items())[-10:]}
            ident=secrets.token_hex(8);self.jobs[ident]={'id':ident,'status':'queued','events':[]}
        def worker():
            def progress(**event):
                with self.lock:self.jobs[ident]['status']='running';self.jobs[ident]['events'].append(event)
            try:
                result=run(payload,self.out,progress=progress)
                with self.lock:self.jobs[ident].update(status='done',result={k:v for k,v in result.items() if k!='path'});self.latest=result['id']
            except Exception as e:
                error=e.record() if isinstance(e,DesignError) else {'code':'GENERATION_FAILED','message':type(e).__name__+': '+str(e)}
                with self.lock:self.jobs[ident].update(status='error',error=error)
        self.pool.submit(worker);return ident


def make_server(out,port=0):
    state=State(out)
    class Handler(BaseHTTPRequestHandler):
        server_version='FloorForge/'+__version__
        def trusted(self,write=False):
            port=self.server.server_port;hosts={f'127.0.0.1:{port}',f'localhost:{port}'}
            if self.headers.get('Host') not in hosts:return False
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://{h}' for h in hosts}:return False
            if write and not secrets.compare_digest(self.headers.get('X-FloorForge-Token',''),state.token):return False
            return True
        def send(self,data,status=200,content='application/json; charset=utf-8'):
            raw=canonical(data) if not isinstance(data,bytes) else data
            self.send_response(status);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','DENY');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if not self.trusted():self.send({'error':'Local origin required'},403);return
            path=unquote(urlsplit(self.path).path)
            if path=='/api/session':self.send({'token':state.token,'version':__version__,'backend_build_id':kernel_hash(),'defaults':DEFAULTS,'setbacks':SETBACK_TABLES,'styles':STYLES,'themes':list_available_themes(),'latest':state.latest,'runtime':runtime_versions(),'ai':state.ai.status()});return
            if path=='/api/ai/status':self.send(state.ai.status());return
            if path.startswith('/api/jobs/'):
                with state.lock:job=state.jobs.get(path.rsplit('/',1)[1])
                self.send(job or {'error':'Unknown job'},200 if job else 404);return
            if path.startswith('/demo/'):
                base=(ROOT/'examples/demo').resolve();file=(base/path[6:]).resolve()
                if not file.is_relative_to(base):self.send({'error':'Invalid path'},404);return
            elif path.startswith('/builds/'):
                import re
                match=re.fullmatch(r'/builds/([0-9a-f]{24})/(.+)',path)
                if not match or '..' in Path(match[2]).parts:self.send({'error':'Invalid build path'},404);return
                base=(state.out/'builds'/match[1]).resolve();file=(base/match[2]).resolve()
                if not file.is_relative_to(base):self.send({'error':'Invalid path'},404);return
            else:
                permitted={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/viewer.js':'viewer.js','/style.css':'style.css','/three.html':'three.html','/three-studio.js':'dist/three-studio.js'}
                if path not in permitted:self.send({'error':'Not found'},404);return
                file=ROOT/'web'/permitted[path]
            try:data=file.read_bytes()
            except OSError:self.send({'error':'Not found'},404);return
            content={'.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.glb':'model/gltf-binary','.ifc':'application/x-step'}.get(file.suffix,mimetypes.guess_type(file.name)[0] or 'application/octet-stream');self.send(data,content=content)
        def do_POST(self):
            if not self.trusted(write=True):self.send({'error':'Session token and local origin required'},403);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=2_000_000:raise DesignError('REQUEST_SIZE','Request must be between 1 byte and 2 MB.')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise DesignError('CONTENT_TYPE','JSON requests only.')
                body=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
                if not isinstance(body,dict):raise DesignError('SCHEMA','Request must be an object.')
                if path=='/api/intent':self.send(fuse(body))
                elif path=='/api/generate':self.send({'job_id':state.submit(body)},202)
                elif path=='/api/ai/configure':self.send(state.ai.configure(body))
                elif path=='/api/ai/clear':state.ai.clear();self.send(state.ai.status())
                elif path=='/api/ai/estimate':self.send(state.ai.estimate(body))
                elif path=='/api/ai/propose':self.send(state.ai.propose(body.get('project',{}),body.get('instruction',''),body.get('confirm',False)))
                else:self.send({'error':'Not found'},404)
            except (DesignError,ValueError,TypeError) as e:self.send(e.record() if isinstance(e,DesignError) else {'code':'REQUEST_ERROR','message':str(e)},400)
            except Exception:self.send({'code':'INTERNAL_ERROR','message':'Request failed. No credentials or request bodies are logged.'},500)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True;server.state=state
    return server

def serve(out,port=0,open_browser=True):
    server=make_server(out,port);url=f'http://127.0.0.1:{server.server_port}/'
    print('FloorForge Studio '+url+'\nLocal only. Ctrl+C stops the server. No telemetry.')
    if open_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.state.ai.clear();server.server_close();server.state.pool.shutdown(wait=True)
    return 0
