"""Loopback-only studio server. No telemetry, terminal subprocesses or credential files."""
from __future__ import annotations
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
import concurrent.futures,errno,http.client,hashlib,json,mimetypes,re,secrets,threading,time,webbrowser
from . import __version__
from .model import *
from .pipeline import run,ROOT,runtime_versions,kernel_hash
from .intent import fuse,SETBACKS_BY_DEPTH,SETBACKS_BY_WIDTH
from .ai import Assist
from .exterior import list_available_themes
from .spaces import SPACE_REGISTRY, guide_labels, GUIDE_AUTOMATIC_KINDS

# The open-space tables behind intent.derive_setbacks, for the studio's live plot summary (JSON has no infinity).
SETBACK_TABLES={'depth':[[None if math.isinf(l) else l,f,r] for l,f,r in SETBACKS_BY_DEPTH],
                'width':[[None if math.isinf(l) else l,sd] for l,sd in SETBACKS_BY_WIDTH]}

def launch_identity(out):
    return sha({'workspace':str(ROOT.resolve()),'output':str(Path(out).resolve())})


def existing_studio(port, out):
    """Recognize a local studio without following redirects, using proxies or logging its token."""
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=2)
    try:
        connection.request('GET','/api/session')
        response=connection.getresponse()
        if response.status!=200 or not response.getheader('Server','').startswith('FloorForge/'):return False
        data=json.loads(response.read(65537))
        if not isinstance(data,dict) or not isinstance(data.get('defaults'),dict) or not data.get('version'):return False
        # Older studios have no identity field. Their current settings remain in force.
        return data.get('launch_identity') in (None,launch_identity(out))
    except (OSError,ValueError,http.client.HTTPException):return False
    finally:connection.close()

class State:
    def __init__(self,out):
        self.out=Path(out);self.token=secrets.token_urlsafe(32);self.jobs={};self.lock=threading.Lock();self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1);self.ai=Assist();self.latest=self.restore_latest()
    def restore_latest(self):
        """Restore only a completely published, unchanged build from this studio."""
        try:
            record=read_json(self.out/'latest-build.json');ident=record['id']
            if not isinstance(ident,str) or not re.fullmatch(r'[0-9a-f]{24}',ident):return None
            base=(self.out/'builds'/ident).resolve();manifest=read_json(base/'manifest.json')
            if record.get('workspace')!=str(ROOT.resolve()) or manifest['build_id']!=ident:return None
            if not {'scene.json','building.json','report.json','sheets.json','project.floorforge.json'}<=manifest['files'].keys():return None
            for name,digest in manifest['files'].items():
                file=(base/name).resolve()
                if not file.is_relative_to(base) or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:return None
            return ident
        except (OSError,ValueError,KeyError,TypeError,AttributeError):return None
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
                atomic(self.out/'latest-build.json',canonical({'id':result['id'],'workspace':str(ROOT.resolve())}))
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
        def send(self,data,status=200,content='application/json; charset=utf-8',frameable=False):
            raw=canonical(data) if not isinstance(data,bytes) else data
            self.send_response(status);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('X-Frame-Options','SAMEORIGIN' if frameable else 'DENY');self.send_header('Referrer-Policy','no-referrer');self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if not self.trusted():self.send({'error':'Local origin required'},403);return
            path=unquote(urlsplit(self.path).path)
            if path=='/api/session':self.send({'token':state.token,'version':__version__,'launch_identity':launch_identity(state.out),'backend_build_id':kernel_hash(),'spaceRegistry':SPACE_REGISTRY,'guideLabels':guide_labels(),'guideAutomaticKinds':sorted(GUIDE_AUTOMATIC_KINDS),'defaults':DEFAULTS,'setbacks':SETBACK_TABLES,'styles':STYLES,'themes':list_available_themes(),'latest':state.latest,'runtime':runtime_versions(),'ai':state.ai.status()});return
            if path=='/api/samples':
                from .sample_projects import catalogue
                self.send({'samples':catalogue()});return
            if path=='/api/plan/example':
                from urllib.parse import parse_qs
                raw=parse_qs(urlsplit(self.path).query).get('storeys',['2'])[0]
                n=int(raw) if raw in ('1','2','3') else 0
                if n not in (1,2,3):self.send({'message':'Choose one to three occupied floors.'},400);return
                p=read_json(ROOT/'examples/custom/g2-terrace.floorforge.json');p['brief'].update(storeys=n,roof_access=True)
                p['customPlan']['floors']=p['customPlan']['floors'][:n]
                for st in p['customPlan']['stairs']:st['roomIds']=st['roomIds'][:n]
                self.send(p);return
            if path=='/api/ai/status':self.send(state.ai.status());return
            if path.startswith('/api/jobs/'):
                with state.lock:job=state.jobs.get(path.rsplit('/',1)[1])
                self.send(job or {'error':'Unknown job'},200 if job else 404);return
            if path=='/api/plan/sketch-example':
                self.send(read_json(ROOT/'examples/custom/your-sketch-g1.floorforge.json'));return
            if path.startswith('/samples/your-sketch/'):
                base=(ROOT/'examples/your-sketch').resolve();file=(base/path[len('/samples/your-sketch/'):]).resolve()
                if not file.is_relative_to(base):self.send({'error':'Invalid path'},404);return
            elif path.startswith('/samples/'):
                from .sample_projects import sample_file
                pieces=path.split('/',3)
                file=sample_file(pieces[2],pieces[3]) if len(pieces)==4 else None
                if file is None:self.send({'error':'Unknown sample or invalid path'},404);return
            elif path.startswith('/demo/'):
                base=(ROOT/'examples/demo').resolve();file=(base/path[6:]).resolve()
                if not file.is_relative_to(base):self.send({'error':'Invalid path'},404);return
            elif path.startswith('/builds/'):
                import re
                match=re.fullmatch(r'/builds/([0-9a-f]{24})/(.+)',path)
                if not match or '..' in Path(match[2]).parts:self.send({'error':'Invalid build path'},404);return
                base=(state.out/'builds'/match[1]).resolve();file=(base/match[2]).resolve()
                if not file.is_relative_to(base):self.send({'error':'Invalid path'},404);return
            else:
                permitted={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/sample-gallery.js':'sample-gallery.js','/project-workspace.js':'project-workspace.js','/room-board.js':'room-board.js','/plan-editor.js':'plan-editor.js','/layout-editor.js':'layout-editor.js','/viewer.js':'viewer.js','/style.css':'style.css','/three.html':'three.html','/three-studio.js':'dist/three-studio.js'}
                if path not in permitted:self.send({'error':'Not found'},404);return
                file=ROOT/'web'/permitted[path]
            try:data=file.read_bytes()
            except OSError:self.send({'error':'Not found'},404);return
            content={'.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.glb':'model/gltf-binary','.ifc':'application/x-step'}.get(file.suffix,mimetypes.guess_type(file.name)[0] or 'application/octet-stream');self.send(data,content=content,frameable=path.startswith('/samples/') and path.endswith('/preview.html'))
        def do_POST(self):
            if not self.trusted(write=True):self.send({'error':'Session token and local origin required'},403);return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=2_000_000:raise DesignError('REQUEST_SIZE','Request must be between 1 byte and 2 MB.')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise DesignError('CONTENT_TYPE','JSON requests only.')
                body=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
                if not isinstance(body,dict):raise DesignError('SCHEMA','Request must be an object.')
                if path=='/api/intent':self.send(fuse(body))
                elif path=='/api/placements/validate':
                    from .layout import generate_layout
                    from .exterior import apply_exterior_preferences
                    from .review import validate, reports
                    from .scene import make_scene
                    b=apply_exterior_preferences(generate_layout(fuse(body)))
                    report=reports(b,validate(b));sc=make_scene(b,report)
                    self.send({'valid':True,'planHash':b['planHash'],'editables':len(sc['editables'])})
                elif path=='/api/guide/check':
                    from .plan_tools import guide_check
                    self.send(guide_check(fuse(body)))
                elif path=='/api/guide/convert':
                    from .plan_tools import convert_guide
                    self.send(convert_guide(body))
                elif path=='/api/plan/arrange':
                    from .room_board import arrange
                    self.send(arrange(body.get('project',{}),body.get('board')))
                elif path=='/api/plan/prepare':
                    from .plan_assist import prepare_plan
                    self.send(prepare_plan(body))
                elif path=='/api/plan/smart-fit':
                    from .smart_fit import smart_fit
                    self.send(smart_fit(body.get('project',body),floor=body.get('fitFloor')))
                elif path=='/api/plan/upper-constraints':
                    from .upper_floor import constraints
                    self.send(constraints(body.get('project',{}),body.get('floor')))
                elif path=='/api/plan/upper-starter':
                    from .upper_floor import starter
                    self.send(starter(body.get('project',{}),body.get('floor'),body.get('stairsOnly',False)))
                elif path=='/api/plan/suggest-openings':
                    from .plan_tools import suggest_openings
                    self.send(suggest_openings(fuse(body)))
                elif path=='/api/plan/validate':
                    from .layout import generate_layout
                    from .review import validate
                    intent=fuse(body)
                    try:
                        building=generate_layout(intent);review=validate(building)
                        self.send({'valid':True,'planHash':intent['planHash'],'draftRevision':intent['draftRevision'],'building':building,'review':review})
                    except DesignError as error:self.send({'valid':False,'planHash':intent['planHash'],'draftRevision':intent['draftRevision'],**error.record()})
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
    try:server=make_server(out,port)
    except OSError as error:
        if error.errno!=errno.EADDRINUSE:raise
        if port and existing_studio(port,out):
            url=f'http://127.0.0.1:{port}/'
            print(f'FloorForge is already running at {url}\nUsing the existing server and its current settings. No second server was started.')
            if open_browser:webbrowser.open(url)
            return 0
        raise DesignError('PORT_IN_USE',f'Port {port} is in use by another application or a different FloorForge project. Use --port 0 to choose a free port.') from error
    url=f'http://127.0.0.1:{server.server_port}/'
    print('FloorForge Studio '+url+'\nLocal only. Ctrl+C stops the server. No telemetry.')
    if open_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.state.ai.clear();server.server_close();server.state.pool.shutdown(wait=True)
    return 0
