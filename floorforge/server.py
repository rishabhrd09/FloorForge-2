"""Loopback-only studio; optional local Cycles worker, no telemetry or saved API keys."""
from __future__ import annotations
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
import concurrent.futures,copy,errno,http.client,hashlib,json,mimetypes,re,secrets,socket,threading,time,webbrowser
from . import __version__
from .model import *
from .pipeline import run,ROOT,runtime_versions,kernel_hash
from .intent import fuse,SETBACKS_BY_DEPTH,SETBACKS_BY_WIDTH
from .ai import Assist
from .exterior import list_available_themes
from .spaces import SPACE_REGISTRY, guide_labels, GUIDE_AUTOMATIC_KINDS

# Capture the code identity while this module is loaded. Rehashing only when a
# session is requested would let an old Python route table advertise new files
# from disk, even though it cannot serve their API calls.
LOADED_BUILD_ID = kernel_hash()
JOURNEY_API_VERSION = 1
RESTART_MESSAGE = ('The local app was updated while this server was running. '
                   'Restart MyVerandah, reload this page, then try again. Your saved projects and draft are kept.')

# The open-space tables behind intent.derive_setbacks, for the studio's live plot summary (JSON has no infinity).
SETBACK_TABLES={'depth':[[None if math.isinf(l) else l,f,r] for l,f,r in SETBACKS_BY_DEPTH],
                'width':[[None if math.isinf(l) else l,sd] for l,sd in SETBACKS_BY_WIDTH]}

class StudioHTTPServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR can bind a second server to an occupied port.
    # Exclusive ownership makes repeated launches detect the existing studio.
    allow_reuse_address = not hasattr(socket, 'SO_EXCLUSIVEADDRUSE')
    allow_reuse_port = False

    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def launch_identity(out):
    return sha({'workspace':str(ROOT.resolve()),'output':str(Path(out).resolve())})


def inspect_studio(port, out):
    """Recognize a local studio without following redirects, using proxies or logging its token."""
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=2)
    try:
        connection.request('GET','/api/session')
        response=connection.getresponse()
        if response.status!=200 or not response.getheader('Server','').startswith('FloorForge/'):return 'unavailable'
        data=json.loads(response.read(65537))
        if not isinstance(data,dict) or not isinstance(data.get('defaults'),dict) or not data.get('version'):return 'unavailable'
        if data.get('launch_identity') not in (None,launch_identity(out)):return 'different'
        if (data.get('launch_identity') is None or data.get('journey_api_version')!=JOURNEY_API_VERSION
                or data.get('loaded_build_id')!=LOADED_BUILD_ID or data.get('restart_required')
                or data.get('disk_build_id')!=LOADED_BUILD_ID or kernel_hash()!=LOADED_BUILD_ID):
            return 'stale'
        return 'current'
    except (OSError,ValueError,http.client.HTTPException):return 'unavailable'
    finally:connection.close()


def existing_studio(port, out):
    return inspect_studio(port, out)=='current'

class State:
    def __init__(self,out):
        self.loaded_build_id=LOADED_BUILD_ID
        self.out=Path(out);self.token=secrets.token_urlsafe(32);self.jobs={};self.lock=threading.Lock();self.pool=concurrent.futures.ThreadPoolExecutor(max_workers=1);self.ai=Assist();self.latest=self.restore_latest()
        from .journey_service import JourneyService
        self.journey=JourneyService(out);self.generation_epoch=0;self.request_epoch=0
        from .journey_render import RenderService
        self.renders=RenderService(out)
    def runtime_status(self):
        disk_build_id=kernel_hash()
        return {'journey_api_version':JOURNEY_API_VERSION,'loaded_build_id':self.loaded_build_id,
                'disk_build_id':disk_build_id,'restart_required':disk_build_id!=self.loaded_build_id}
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
        from .journey_service import needs_approval
        payload=copy.deepcopy(payload)
        with self.lock:
            self.request_epoch+=1;request_epoch=self.request_epoch
        if payload.get('compass') is not None or payload.get('editorState',{}).get('mode')=='compass':
            from .compass_api import require_enabled
            require_enabled()
        custom=needs_approval(payload)
        preparation=None
        if custom:
            compiled,preparation=self.journey.generation_payload(payload)
            if compiled.get('compass') is not None:
                from .compass_api import require_enabled
                require_enabled()
            fuse(compiled)
        elif payload.get('compass') is not None or (isinstance(payload.get('editorState'),dict) and payload['editorState'].get('mode')=='compass'):
            from .compass_api import require_enabled
            require_enabled()
            if payload.get('compass') is None:
                raise DesignError('COMPASS_ACCEPTANCE','Review and accept the Compass geometry proposal before generating.')
        if not custom:fuse(payload) # Fail invalid input before queueing expensive geometry.
        with self.lock:
            if request_epoch!=self.request_epoch:raise DesignError('JOB_STALE','A newer generation request superseded this one.')
            active=[j for j in self.jobs.values() if j['status'] in ('queued','running')]
            if active and not custom:raise DesignError('BUSY','A design is already generating. Wait for it to finish.')
            for job in active:job['status']='cancelled'
            if len(self.jobs)>20:self.jobs={k:v for k,v in list(self.jobs.items())[-10:]}
            self.generation_epoch+=1;epoch=self.generation_epoch
            ident=secrets.token_hex(8);self.jobs[ident]={'id':ident,'status':'queued','events':[],
                'draftRevision':payload.get('draftRevision',0),'geometryHash':preparation.get('geometryHash') if preparation else None}
            job=self.jobs[ident]
        def cancelled():
            with self.lock:return job['status']=='cancelled' or epoch!=self.generation_epoch
        def worker():
            if cancelled():return
            def progress(**event):
                with self.lock:
                    if job['status']=='cancelled' or epoch!=self.generation_epoch:raise DesignError('JOB_CANCELLED','Generation cancelled.')
                    job['status']='running';job['events'].append(event)
            try:
                result=run(payload,self.out,progress=progress,cancelled=cancelled)
                with self.lock:
                    if job['status']=='cancelled' or epoch!=self.generation_epoch:return
                    atomic(self.out/'latest-build.json',canonical({'id':result['id'],'workspace':str(ROOT.resolve())}))
                    job.update(status='done',result={k:v for k,v in result.items() if k!='path'})
                    if preparation:job['result']['geometryHash']=preparation['geometryHash']
                    self.latest=result['id']
            except Exception as e:
                error=e.record() if isinstance(e,DesignError) else {'code':'GENERATION_FAILED','message':type(e).__name__+': '+str(e)}
                with self.lock:
                    if job['status']!='cancelled':job.update(status='error',error=error)
        self.pool.submit(worker);return ident

    def cancel(self,ident):
        with self.lock:
            job=self.jobs.get(ident)
            if not job:raise DesignError('JOB_UNKNOWN','That generation job is unavailable.')
            if job['status'] in ('queued','running'):job['status']='cancelled'
            return {'id':ident,'status':job['status']}


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
            if path=='/api/session':
                from .compass_api import capabilities
                from .journey_render import capabilities as render_capabilities
                self.send({'token':state.token,'version':__version__,'launch_identity':launch_identity(state.out),'backend_build_id':state.loaded_build_id,**state.runtime_status(),'spaceRegistry':SPACE_REGISTRY,'guideLabels':guide_labels(),'guideAutomaticKinds':sorted(GUIDE_AUTOMATIC_KINDS),'defaults':DEFAULTS,'setbacks':SETBACK_TABLES,'styles':STYLES,'themes':list_available_themes(),'latest':state.latest,'runtime':runtime_versions(),'ai':state.ai.status(),'compass':capabilities(),'render':render_capabilities()});return
            if path=='/api/plan/import-template':
                self.send((ROOT/'examples/import/ground-floor.dxf').read_bytes(),content='application/dxf');return
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
            if re.fullmatch(r'/api/renders/[0-9a-f]{16}',path):
                try:self.send(state.renders.get(path.rsplit('/',1)[1]))
                except DesignError as error:self.send(error.record(),404)
                return
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
                match=re.fullmatch(r'/builds/([0-9a-f]{24})/(.+)',path)
                if not match or '..' in Path(match[2]).parts:self.send({'error':'Invalid build path'},404);return
                base=(state.out/'builds'/match[1]).resolve();file=(base/match[2]).resolve()
                if not file.is_relative_to(base):self.send({'error':'Invalid path'},404);return
            elif path.startswith('/preparations/'):
                match=re.fullmatch(r'/preparations/([0-9a-f]{32})/(drawings.pdf|floorplans.dxf|canonical.json|floor-[1-3].svg)',path)
                if not match:self.send({'error':'Invalid 2D publication path'},404);return
                base=(state.out/'preparations'/match[1]).resolve();file=base/match[2]
                if not (base/'manifest.json').is_file():self.send({'error':'Drawing publication is incomplete'},404);return
            elif path.startswith('/renders/'):
                match=re.fullmatch(r'/renders/([0-9a-f]{16})/final.png',path)
                if not match:self.send({'error':'Invalid render path'},404);return
                file=state.out/'renders'/match[1]/'final.png'
                if not (file.parent/'result.json').exists():self.send({'error':'Render is not completed'},404);return
            else:
                permitted={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/start-page.js':'start-page.js','/hero.js':'hero.js','/assets/myverandah-hero.png':'assets/myverandah-hero.png','/sample-gallery.js':'sample-gallery.js','/project-workspace.js':'project-workspace.js','/room-board.js':'room-board.js','/plan-editor.js':'plan-editor.js','/plan-assistance.js':'plan-assistance.js','/layout-editor.js':'layout-editor.js','/viewer.js':'viewer.js','/style.css':'style.css','/three.html':'three.html','/three-studio.js':'dist/three-studio.js'}
                for name in ('compass-state.js','compass-editor.js','compass.css','survey-questions.js','home-design.js','home-design.css','design-journey.js','design-journey.css'):
                    permitted['/'+name]=name
                if path not in permitted:self.send({'error':'Not found'},404);return
                file=ROOT/'web'/permitted[path]
            try:data=file.read_bytes()
            except OSError:self.send({'error':'Not found'},404);return
            content={'.js':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.glb':'model/gltf-binary','.ifc':'application/x-step'}.get(file.suffix,mimetypes.guess_type(file.name)[0] or 'application/octet-stream');self.send(data,content=content,frameable=(path.startswith('/samples/') and path.endswith(('preview.html','electrical.html','reveal.html'))) or path=='/samples/tirumala-6/tour.html')
        def do_POST(self):
            if not self.trusted(write=True):self.send({'error':'Session token and local origin required'},403);return
            path=urlsplit(self.path).path
            recovery_action=(path=='/api/ai/clear' or re.fullmatch(r'/api/(jobs|renders)/[0-9a-f]{16}/cancel',path))
            if not recovery_action and state.runtime_status()['restart_required']:
                self.send({'code':'STUDIO_RESTART_REQUIRED','message':RESTART_MESSAGE},503);return
            try:
                path=urlsplit(self.path).path
                length=int(self.headers.get('Content-Length','0'))
                limit=16_000_000 if path.startswith('/api/design/') or path in ('/api/generate','/api/intent') else 2_000_000
                if not 0<length<=limit:raise DesignError('REQUEST_SIZE',f'Request must be between 1 byte and {limit//1_000_000} MB.')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise DesignError('CONTENT_TYPE','JSON requests only.')
                body=json.loads(self.rfile.read(length));path=urlsplit(self.path).path
                if not isinstance(body,dict):raise DesignError('SCHEMA','Request must be an object.')
                def edit(project, operation, target=None):
                    # Existing editing algorithms use the resolved compiler
                    # envelope; source activation and portable metadata stay
                    # at the journey boundary rather than being discarded.
                    from .design_journey import editing_project, editing_result
                    compiled=editing_project(project,target=target)
                    return editing_result(project,operation(compiled),compiled=compiled)
                if path=='/api/intent':
                    if body.get('designJourney') is not None:
                        from .design_journey import prepare
                        prepared=prepare(body)
                        if not prepared.get('valid'):raise DesignError('DESIGN_QUESTION','Resolve the necessary design question.',state.journey.public(prepared))
                        self.send(fuse(prepared['preparedProject']))
                    else:self.send(fuse(body))
                elif path=='/api/design/prepare':self.send(state.journey.prepare(body.get('project',{})))
                elif path=='/api/design/inputs':self.send(state.journey.inputs(body.get('project',{})))
                elif path=='/api/design/approve':self.send(state.journey.approve(body))
                elif path=='/api/design/confirm':self.send(state.journey.confirm(body))
                elif path=='/api/design/render':self.send(state.renders.submit(body),202)
                elif re.fullmatch(r'/api/renders/[0-9a-f]{16}/cancel',path):self.send(state.renders.cancel(path.split('/')[3]))
                elif path=='/api/design/trace':
                    from .reference_trace import trace_reference
                    self.send(trace_reference(body))
                elif re.fullmatch(r'/api/jobs/[0-9a-f]{16}/cancel',path):self.send(state.cancel(path.split('/')[3]))
                elif path.startswith('/api/compass/'):
                    from .compass_api import dispatch
                    self.send(dispatch(path,body))
                elif path=='/api/plan/import-dxf':
                    from .plan_import import import_mapped_dxf
                    self.send(import_mapped_dxf(body))
                elif path=='/api/plan/inspect-dxf':
                    from .plan_import import inspect_dxf
                    self.send(inspect_dxf(body.get('text'),body.get('filename','floor-plan.dxf')))
                elif path=='/api/placements/validate':
                    from .layout import generate_layout
                    from .exterior import apply_exterior_preferences
                    from .review import validate, reports
                    from .scene import make_scene
                    project=body
                    if body.get('designJourney') is not None:
                        from .design_journey import prepare
                        prepared=prepare(body)
                        if not prepared.get('valid'):raise DesignError('DESIGN_QUESTION','Resolve the necessary design question.',state.journey.public(prepared))
                        project=prepared['preparedProject']
                    b=apply_exterior_preferences(generate_layout(fuse(project)))
                    report=reports(b,validate(b));sc=make_scene(b,report)
                    self.send({'valid':True,'planHash':b['planHash'],'editables':len(sc['editables'])})
                elif path=='/api/guide/check':
                    from .plan_tools import guide_check
                    self.send(edit(body,lambda project:guide_check(fuse(project))))
                elif path=='/api/guide/convert':
                    from .plan_tools import convert_guide
                    self.send(edit(body,convert_guide))
                elif path=='/api/plan/arrange':
                    from .room_board import arrange
                    self.send(edit(body.get('project',{}),lambda project:arrange(project,body.get('board')),target='board'))
                elif path=='/api/plan/prepare':
                    from .plan_assist import prepare_plan
                    self.send(edit(body,prepare_plan,target='exact'))
                elif path=='/api/plan/smart-fit':
                    from .smart_fit import smart_fit
                    self.send(edit(body.get('project',body),lambda project:smart_fit(project,floor=body.get('fitFloor')),target='exact'))
                elif path=='/api/plan/alternatives':
                    from .plan_search import alternatives
                    self.send(edit(body.get('project',{}),lambda project:alternatives(project,body.get('floor',0),body.get('lockedIds',[])),target='exact'))
                elif path=='/api/local-plan/models':
                    from .local_planner import models
                    self.send(models())
                elif path=='/api/local-plan/propose':
                    from .local_planner import propose
                    self.send(edit(body.get('project',{}),lambda project:propose(project,body.get('instruction',''),model=body.get('model','qwen3.5:9b'),floor=body.get('floor',0),locked_ids=body.get('lockedIds',[]),images=body.get('images',[]),dimensions_confirmed=body.get('dimensionsConfirmed',False),confirm=body.get('confirm',False)),target='exact'))
                elif path=='/api/plan/upper-constraints':
                    from .upper_floor import constraints
                    self.send(edit(body.get('project',{}),lambda project:constraints(project,body.get('floor')),target='exact'))
                elif path=='/api/plan/upper-starter':
                    from .upper_floor import starter
                    self.send(edit(body.get('project',{}),lambda project:starter(project,body.get('floor'),body.get('stairsOnly',False)),target='exact'))
                elif path=='/api/plan/suggest-openings':
                    from .plan_tools import suggest_openings
                    self.send(edit(body,lambda project:suggest_openings(fuse(project)),target='exact'))
                elif path=='/api/plan/validate':
                    from .layout import generate_layout
                    from .review import validate
                    from .design_journey import editing_project
                    intent=fuse(editing_project(body,target='exact'))
                    try:
                        building=generate_layout(intent);review=validate(building)
                        self.send({'valid':True,'planHash':intent['planHash'],'draftRevision':intent['draftRevision'],'building':building,'review':review})
                    except DesignError as error:self.send({'valid':False,'planHash':intent['planHash'],'draftRevision':intent['draftRevision'],**error.record()})
                elif path=='/api/generate':
                    if not isinstance(body.get('designJourney'),dict):
                        raise DesignError('APPROVAL_REQUIRED','Review and approve every requested 2D floor and confirm the whole home before generating 3D.')
                    self.send({'job_id':state.submit(body)},202)
                elif path=='/api/ai/configure':self.send(state.ai.configure(body))
                elif path=='/api/ai/clear':state.ai.clear();self.send(state.ai.status())
                elif path=='/api/ai/estimate':self.send(state.ai.estimate(body))
                elif path=='/api/ai/propose':self.send(edit(body.get('project',{}),lambda project:state.ai.propose(project,body.get('instruction',''),body.get('confirm',False)),target='brief'))
                else:self.send({'error':'Not found'},404)
            except (DesignError,ValueError,TypeError) as e:self.send(e.record() if isinstance(e,DesignError) else {'code':'REQUEST_ERROR','message':str(e)},400)
            except Exception:self.send({'code':'INTERNAL_ERROR','message':'Request failed. No credentials or request bodies are logged.'},500)
        def log_message(self,*args):pass
    server=StudioHTTPServer(('127.0.0.1',port),Handler);server.daemon_threads=True;server.state=state
    return server

def serve(out,port=0,open_browser=True):
    try:server=make_server(out,port)
    except OSError as error:
        if error.errno!=errno.EADDRINUSE and getattr(error,'winerror',None) not in (10048,10013):raise
        if port and existing_studio(port,out):
            url=f'http://127.0.0.1:{port}/'
            print(f'FloorForge is already running at {url}\nUsing the existing server and its current settings. No second server was started.')
            if open_browser:webbrowser.open(url)
            return 0
        if port and inspect_studio(port,out)=='stale':
            raise DesignError('STUDIO_RESTART_REQUIRED',
                f'An older MyVerandah server is still running on port {port}. Stop that local server and launch again, '
                'or use --port 0 and open the newly printed address. Saved projects are kept; this launch did not replace or delete them.') from error
        raise DesignError('PORT_IN_USE',f'Port {port} is in use by another application or a different FloorForge project. Use --port 0 to choose a free port.') from error
    url=f'http://127.0.0.1:{server.server_port}/'
    print('FloorForge Studio '+url+'\nLocal only. Ctrl+C stops the server. No telemetry.')
    if open_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.state.ai.clear();server.state.renders.close();server.server_close();server.state.pool.shutdown(wait=True)
    return 0
