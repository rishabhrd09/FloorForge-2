"""Versioned content-addressed DAG, atomic publication and traceable export pack."""
from __future__ import annotations
from pathlib import Path
import hashlib,importlib.metadata,io,json,os,platform,shutil,tempfile,time,zipfile
from . import __version__,BANNER
from .model import *
from .intent import fuse
from .layout import generate_layout
from .review import validate,reports
from .scene import make_scene,glb_bytes
from .drawings import make_sheets,svg_sheet,pdf_sheets,dxf_export
from .ifc_export import export_ifc
from .exterior import apply_exterior_preferences,exterior_review,derive_facade_anchors

ROOT=Path(__file__).resolve().parent.parent
DEPS={'intent':(), 'programme':('intent',),'layout':('programme',),'openings':('layout',),
      'anchors':('layout',),'exterior':('layout','anchors'),
      'structure':('layout',),'validate':('layout','openings','exterior','structure'),
      'documents':('exterior','validate'),'scene':('exterior','documents'),
      'sheets':('exterior','scene','documents'),'render':('scene',),
      'exports':('intent','layout','openings','anchors','exterior','validate','structure','documents','scene','sheets','render')}

def runtime_versions():
    result={'python':platform.python_version()}
    for n in ('shapely','numpy','trimesh','ezdxf','reportlab','Pillow'):
        try:result[n]=importlib.metadata.version(n)
        except importlib.metadata.PackageNotFoundError:result[n]='missing'
    return result

def kernel_hash():
    files=sorted((ROOT/'floorforge').glob('*.py'))+sorted((ROOT/'web').glob('*.js'))+sorted((ROOT/'web').glob('*.css'))+sorted((ROOT/'web').glob('*.html'))
    return sha({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})

def preview_html(scene,building,plan_svg):
    # The bundled viewer is inlined; a literal closing script tag inside it would end the element early.
    script=(ROOT/'web/viewer.js').read_text('utf8').replace('</script','<\\/script');data=canonical(scene).decode('utf8').replace('<','\\u003c')
    import html
    title=html.escape(building['brief']['title']);style=STYLES[building['brief']['style']]['label']
    theme=building.get('exterior',{}).get('theme','current');theme_label=html.escape({'modern_tropical':'Modern Tropical','warm_modern_minimal':'Warm Modern Minimal','tropical_verandah':'Tropical Verandah','earth_terracotta':'Earth & Terracotta'}.get(theme,style))
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FloorForge | Offline walkthrough</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f3f1e8;color:#21372d;font:14px/1.5 system-ui}header{height:64px;border-bottom:1px solid #d7dcd0;padding:20px 30px;display:flex;justify-content:space-between}.brand{font-weight:750;letter-spacing:.13em}main{display:grid;grid-template-columns:290px 1fr;height:calc(100vh - 64px)}aside{padding:28px 26px;border-right:1px solid #d7dcd0;overflow:auto}h1{font:40px/1.1 Georgia,serif;letter-spacing:-.04em;margin:10px 0 14px}p{color:#677366}small{color:#7f5840}section{position:relative;min-width:0;background:#1b1f1d}.tools{position:absolute;left:18px;top:16px;right:18px;z-index:4;display:flex;gap:6px;flex-wrap:wrap}button,a{font:inherit;border:1px solid #cfd5ca;padding:8px 13px;border-radius:6px;background:#f9f8f1e6;color:#243b2d;cursor:pointer;text-decoration:none}button.active{background:#243b2d;color:#fff;border-color:#243b2d}button:focus-visible,a:focus-visible{outline:3px solid #9d663f;outline-offset:2px}canvas{width:100%;height:100%;display:block;outline:none}#plan{position:absolute;inset:60px 0 40px;background:white;overflow:auto;z-index:5}#plan svg{width:100%;height:100%}[hidden]{display:none!important}.status{position:absolute;bottom:14px;left:18px;right:18px;z-index:4;font-size:11px;color:#344639;background:#f9f8f1d9;padding:6px 10px;border-radius:5px;max-width:720px}.exports{display:flex;gap:6px;flex-wrap:wrap;margin-top:22px}.exports a{font-size:11px;padding:6px 9px}kbd{border:1px solid #cfd5ca;border-radius:4px;padding:0 5px;background:#fff;font-size:11px}@media(max-width:760px){main{grid-template-columns:1fr;height:auto}aside{padding:18px 22px}h1{font-size:30px;margin:6px 0}section{height:72vh}header{padding:20px}.details{display:none}}</style>
<header><span class="brand">FLOORFORGE</span><span>OFFLINE WALKTHROUGH · ALPHA 0.3</span></header><main><aside><small>GENERATED, NOT A PHOTOGRAPH</small><h1>'''+title+'''</h1><p>'''+theme_label+'''<br>One model. Every view. Walk every room.</p><div class="details"><p><strong>Walk in</strong>, click the view, then use <kbd>W</kbd><kbd>A</kbd><kbd>S</kbd><kbd>D</kbd> to move, the mouse to look, <kbd>Shift</kbd> to run, <kbd>Space</kbd> to jump and <kbd>C</kbd> to crouch. Walk up the stairs to reach the next floor. <kbd>Esc</kbd> releases the mouse.</p><p>Drag to orbit outside; scroll to zoom. This preview needs no installation or network.</p></div><small>PRELIMINARY — ENGINEER TO REVIEW.<br>Not a structural design or construction approval.</small><div class="exports"><a href="drawings.pdf">Drawing set</a><a href="floorplans.dxf">DXF</a><a href="model.glb">GLB</a><a href="model.ifc">IFC*</a><a href="report.json">Review</a></div><p><small>*IFC viewer acceptance remains unverified. Real-time raster render with procedural materials and planting; not a verified photographic still.</small></p></aside>
<section><div class="tools"><button data-mode="solid" class="active">Exterior</button><button data-mode="walk">Walk in</button><button data-mode="dollhouse">Dollhouse</button><button data-mode="tour">Orbit tour</button><button id="planBtn">Drawing</button><button id="floorBtn">Ground floor</button><button id="gradeBtn">Daylight</button><button id="fullBtn">Full screen</button><button id="pngBtn">Save PNG</button><button id="glbBtn" title="The textured scene with its planting, for Blender and other renderers">Blender GLB</button></div><canvas id="view" tabindex="0" aria-label="Interactive 3D home: drag to orbit; in walk mode use W A S D, mouse look, Shift run, Space jump"></canvas><div id="plan" hidden>'''+plan_svg+'''</div><div class="status" id="status">Loading local geometry…</div></section></main><script>'''+script+'''</script><script id="scene-data" type="application/json">'''+data+'''</script><script>
const scene=JSON.parse(document.getElementById('scene-data').textContent);let floor=0,grade=0;const grades=[['day','Daylight'],['golden','Golden hour'],['dusk','Blue hour'],['night','Night']];
const $=id=>document.getElementById(id),setActive=m=>document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===m));
try{let v=new FloorForgeViewer($('view'),{onStatus:t=>$('status').textContent=t,hudInset:64});v.setScene(scene);v.onModeChange=setActive;v.onFloorChange=f=>{floor=f;$('floorBtn').textContent=f?'First floor':'Ground floor';};window.__ff={viewer:v,scene,ready:true};
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{$('plan').hidden=true;v.setMode(b.dataset.mode);setActive(b.dataset.mode);if(b.dataset.mode==='walk')$('view').focus();});
$('planBtn').onclick=()=>$('plan').hidden=!$('plan').hidden;$('floorBtn').onclick=e=>{floor=(floor+1)%scene.storeys;v.setFloor(floor);e.target.textContent=floor?'First floor':'Ground floor';};
$('gradeBtn').onclick=e=>{grade=(grade+1)%grades.length;v.setGrade(grades[grade][0]);e.target.textContent=grades[grade][1];};
$('fullBtn').onclick=()=>{let s=document.querySelector('section');if(document.fullscreenElement)document.exitFullscreen?.();else s.requestFullscreen?.().catch(()=>{});};
const save=(blob,name)=>{let u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};$('pngBtn').onclick=async()=>save(await v.snapshot(),'FloorForge-view.png');$('glbBtn').onclick=async()=>{let b=$('glbBtn');b.disabled=true;$('status').textContent='Preparing the textured scene for Blender…';try{save(new Blob([await v.exportPresentation()],{type:'model/gltf-binary'}),'FloorForge-presentation.glb');$('status').textContent='Saved FloorForge-presentation.glb: open it in Blender, or render it with scripts/render_cycles.py.';}catch(e){$('status').textContent=e.message;}finally{b.disabled=false;}};}catch(e){$('status').textContent=e.message;$('plan').hidden=false;window.__ff={ready:false,error:e.message};}
</script></html>'''

def deterministic_zip(files):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,9,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;z.writestr(info,data)
    return out.getvalue()

def run(payload:dict,out:Path,target='exports',progress=lambda **kw:None,use_cache=True):
    if target not in DEPS:raise DesignError('STAGE','Unknown pipeline stage: '+str(target))
    out=Path(out);cache=out/'.cache';code=kernel_hash();versions=runtime_versions();done={};records=[]
    def visit(name):
        if name in done:return done[name]
        d={dep:visit(dep) for dep in DEPS[name]};key=sha({'name':name,'code':code,'runtime':versions,'deps':{k:sha(v) for k,v in d.items()},'input':payload if name=='intent' else None});path=cache/name/(key+'.json')
        progress(stage=name,status='running');start=time.perf_counter();hit=False
        if use_cache and path.is_file() and name!='exports':
            record=read_json(path)
            if record.get('hash')!=sha(record.get('data')):raise DesignError('CACHE_CORRUPT','Cached stage was modified. Remove only the cache folder and retry.')
            result=record['data'];hit=True
        elif name=='intent':result=fuse(payload)
        elif name=='programme':result=d['intent']
        elif name=='layout':result=generate_layout(d['programme'])
        elif name=='openings':result={'items':d['layout']['openings'],'status':'generated_from_room_adjacency'}
        elif name=='anchors':result=derive_facade_anchors(d['layout'])
        elif name=='exterior':result=apply_exterior_preferences(d['layout'])
        elif name=='structure':result={'status':'not_designed','geometry_is_not_a_load_path':'No member sizes, footings or reinforcement designed.'}
        elif name=='validate':result=validate(d.get('exterior',d['layout']))
        elif name=='documents':result=reports(d['exterior'],d['validate'])
        elif name=='scene':result=make_scene(d['exterior'],d['documents'])
        elif name=='sheets':result=make_sheets(d['exterior'],d['scene'],d['documents'])
        elif name=='render':result={'status':'raster_scene_ready','offline_photoreal':'not_rendered','external_adapter':'scripts/blender_scene.py'}
        elif name=='exports':result=publish(payload,d,out,code,versions,records)
        if name!='exports' and use_cache and not hit:atomic(path,canonical({'hash':sha(result),'data':result}))
        duration=round(time.perf_counter()-start,4)
        record={'stage':name,'revision':__version__,'input_hashes':{k:sha(v) for k,v in d.items()},'output_hash':sha(result),'license':'FloorForge authored code; runtime ledger in licenses/','external_api_cost_usd':0,'local_compute_cost':'not estimated','key':key,'status':result.get('status','generated') if isinstance(result,dict) else 'generated'}
        records.append(record);done[name]=result;progress(stage=name,status='cached' if hit else 'finished',seconds=duration)
        return result
    result=visit(target)
    if target!='exports':
        path=out/('stage-'+target+'.json');atomic(path,canonical({'output':result,'manifest':records}));return {'target':target,'path':str(path),'output':result,'stages':records}
    return result

def publish(payload,d,out,code,versions,records):
    bid=sha({'input':payload,'code':code,'runtime':versions})[:24];parent=out/'builds';dest=parent/bid;parent.mkdir(parents=True,exist_ok=True)
    if dest.is_dir():
        manifest=read_json(dest/'manifest.json')
        for name,expect in manifest['files'].items():
            p=dest/name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expect:raise DesignError('BUILD_MODIFIED','An immutable build was modified: '+name)
        return {'id':bid,'path':str(dest),'status':'published','cached':True}
    temp=Path(tempfile.mkdtemp(prefix='.build-',dir=parent));b=d['exterior'];sc=d['scene'];report=d['documents'];checks={}
    try:
        files={'project.floorforge.json':canonical({'schema':'floorforge.project/0.2',**payload}),
               'intent.json':canonical(d['intent']),'building.json':canonical(b),'scene.json':canonical(sc),
               'report.json':canonical(report),'review.json':canonical(d['validate']),
               'sheets.json':canonical([{'id':s['id'],'title':s['title'],'scale':s['scale']} for s in d['sheets']])}
        for sheet in d['sheets']:files['sheets/'+sheet['id']+'.svg']=svg_sheet(sheet,b).encode('utf8')
        files['drawings.pdf']=pdf_sheets(d['sheets'],b,report)
        files['model.glb']=glb_bytes(sc)
        import trimesh
        reimport=trimesh.load(io.BytesIO(files['model.glb']),file_type='glb',force='scene')
        count=len(reimport.graph.nodes_geometry)
        if count!=len(sc['nodes']):raise DesignError('GLB_REIMPORT','GLB node count changed on re-import.')
        checks['glb']={'status':'trimesh_reimport_pass','node_count':count,'geometries':len(reimport.geometry),'units':'m','up':'Y','separate_viewer':'pending'}
        checks['dxf']=dxf_export(b,sc,temp/'floorplans.dxf');files['floorplans.dxf']=(temp/'floorplans.dxf').read_bytes()
        files['model.ifc'],checks['ifc']=export_ifc(b)
        checks['exterior']=exterior_review(b)
        checks['ifc']['exterior_scope']='Facade and landscape assemblies are represented in scene/GLB and drawings; IFC export remains wall/opening/space coordination only.'
        files['export-checks.json']=canonical(checks)
        files['preview.html']=preview_html(sc,b,svg_sheet(d['sheets'][0],b)).encode('utf8')
        files['REVIEW_BEFORE_USE.txt']=(BANNER+'\n\nNo regulatory or structural approval.\nIFC independently unverified.\nRenders are preliminary raster studies.\n\n'+report['cost']['basis']).encode('utf8')
        manifest={'version':__version__,'build_id':bid,'kernel_sha256':code,'runtime':versions,'input_sha256':sha(payload),'stages':records,'checks':checks,'files':{k:hashlib.sha256(v).hexdigest() for k,v in sorted(files.items())},'banner':BANNER}
        for name,data in files.items():atomic(temp/name,data)
        files['manifest.json']=canonical(manifest);atomic(temp/'manifest.json',files['manifest.json']);atomic(temp/'FloorForge-export.zip',deterministic_zip(files));os.replace(temp,dest)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return {'id':bid,'path':str(dest),'status':'published','cached':False}
