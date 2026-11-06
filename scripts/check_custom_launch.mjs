/* Regression for an old Python process serving newly updated custom-home assets.
 * Uses the actual pre-journey server against the current web files, then restarts
 * a current server on the same origin. Does not control the user's browser.
 */
import {spawn,execFileSync} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {tmpdir} from 'node:os';
import net from 'node:net';

const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..');
const python=process.env.FLOORFORGE_PYTHON||resolve(root,'.venv/bin/python');
const work=mkdtempSync(join(tmpdir(),'myverandah-launch-'));
const out=resolve(root,'evidence/custom-journey/launch-fix');mkdirSync(out,{recursive:true});
const freePort=()=>new Promise((resolve,reject)=>{const s=net.createServer();s.once('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});
const port=Number(process.env.MYVERANDAH_LAUNCH_PORT||await freePort());
const url=`http://127.0.0.1:${port}`;
const baseline='839609731077e9623ce819cdfd80b1152a8a0956';
const legacy=resolve(work,'legacy_server.py');
writeFileSync(legacy,execFileSync('git',['show',`${baseline}:floorforge/server.py`],{cwd:root}));
const bootstrap=resolve(work,'serve_legacy.py');
writeFileSync(bootstrap,`import importlib.util, pathlib, sys
sys.path.insert(0, sys.argv[1])
spec=importlib.util.spec_from_file_location('floorforge._launch_legacy',sys.argv[2])
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
server=module.make_server(pathlib.Path(sys.argv[3]),int(sys.argv[4]))
try: server.serve_forever()
finally:
    server.server_close()
    server.state.pool.shutdown(wait=True)
`);
let server,browser,page;const checks=[],errors=[],serverLogs=[],network=[];
function check(name,pass,detail){checks.push({name,pass:!!pass,...(detail!==undefined?{detail}:{})});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);}
function start(older){
 const args=older?[bootstrap,root,legacy,work,String(port)]:['-m','floorforge','serve','--no-browser','--port',String(port),'--out',work];
 const child=spawn(python,args,{cwd:root,stdio:['ignore','pipe','pipe']});
 const log={kind:older?'legacy':'current',stdout:'',stderr:''};serverLogs.push(log);
 child.stdout.on('data',d=>log.stdout+=d);child.stderr.on('data',d=>log.stderr+=d);return child;
}
async function stop(){
 if(!server)return;
 const child=server;server=null;
 if(child.exitCode!==null)return;
 await new Promise(resolve=>{const timer=setTimeout(()=>{child.kill('SIGKILL');resolve();},5000);child.once('exit',()=>{clearTimeout(timer);resolve();});child.kill('SIGTERM');});
}
async function ready(current=false){
 for(let i=0;i<150;i++){
  if(server.exitCode!==null)throw Error('The owned local test server stopped: '+serverLogs.at(-1).stderr);
  try{const response=await fetch(url+'/api/session');if(response.ok){const data=await response.json();if(!current||data.journey_api_version>=1)return data;}}catch{}
  await new Promise(resolve=>setTimeout(resolve,100));
 }
 throw Error('The owned local test server did not become ready.');
}
const setupValues=()=>page.evaluate(()=>Object.fromEntries(['start-name','start-units','start-width','start-depth','start-floors','start-bearing','start-context'].map(id=>[id,document.getElementById(id).value])));
try{
 server=start(true);const old=await ready();
 check('Fixture reproduces the pre-journey server with no custom-journey capability',!old.journey_api_version);
 const request={project:{brief:{width_mm:12192,depth_mm:18288,storeys:3,road_bearing_deg:270},designJourney:{schema:'myverandah.journey/1',enabledInputs:['plot','compass']}}};
 const missing=await fetch(url+'/api/design/inputs',{method:'POST',headers:{'Content-Type':'application/json','X-FloorForge-Token':old.token},body:JSON.stringify(request)});
 const missingBody=await missing.json();
 check('Actual old route table reproduces the reported Not found response',missing.status===404&&missingBody.error==='Not found');
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 page=await browser.newPage({viewport:{width:1440,height:1000}});
 page.on('pageerror',error=>errors.push(error.message));
 page.on('response',r=>{if(r.url().includes('/api/'))network.push({path:new URL(r.url()).pathname,status:r.status()});});
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp&&!document.querySelector('[data-start="new"]').disabled,null,{timeout:180000});
 check('Actual old server also lacks the new journey script, without blocking setup recovery',await page.evaluate(()=>typeof MyVerandahDesignJourney==='undefined'));
 const preserved=await page.evaluate(()=>{
  const project=window.__ffApp.collect();project.brief.title='Existing family home kept during recovery';
  const draft=JSON.stringify(project),saved=JSON.stringify({'working:existing-family-home':{project,build:'demo',message:'Existing editable project',current:false,title:project.brief.title,savedAt:'2026-11-05T00:00:00.000Z'}});
  localStorage.setItem('floorforge-draft-v1',draft);localStorage.setItem('floorforge-saved-projects',saved);
  return {draft,saved};
 });
 await page.click('[data-start="new"]');
 for(const kind of ['plot','compass','survey','text','sketch','dxf']){
  const choice=page.locator(`[data-home-input="${kind}"]`);
  if((await choice.getAttribute('aria-pressed')==='true')!==['plot','compass'].includes(kind))await choice.click();
 }
 await page.fill('#start-name','West-facing three-floor launch regression');
 await page.selectOption('#start-units','ft');await page.fill('#start-width','40');await page.fill('#start-depth','60');
 await page.selectOption('#start-bearing','270');await page.selectOption('#start-floors','3');await page.selectOption('#start-context','middle');
 const entered=await setupValues();const beforeClick=network.length;
 await page.click('#start-launch');
 await page.waitForFunction(()=>document.getElementById('start-setup-status').textContent.includes('Restart MyVerandah'));
 const message=await page.textContent('#start-setup-status');
 check('Create explains that the running server needs a restart instead of Not found',/older than this page|updated while/.test(message)&&!/^Not found$/.test(message));
 check('Stale-server guard preserves the exact entered setup and selected inputs',JSON.stringify(await setupValues())===JSON.stringify(entered)&&await page.locator('[data-home-input][aria-pressed="true"]').count()===2);
 check('Failed create does not overwrite the existing autosave or saved-project records',await page.evaluate(before=>localStorage.getItem('floorforge-draft-v1')===before.draft&&localStorage.getItem('floorforge-saved-projects')===before.saved,preserved));
 check('Stale create is stopped before any unsupported or mutating endpoint',network.slice(beforeClick).every(r=>r.path==='/api/session'));
 await page.screenshot({path:resolve(out,'stale-server-recovery-message.png'),fullPage:true});
 await page.reload();await page.waitForFunction(()=>window.__ffApp&&!document.querySelector('[data-start="new"]').disabled,null,{timeout:180000});await page.click('[data-start="new"]');
 check('Reload restores the failed setup from local session storage',JSON.stringify(await setupValues())===JSON.stringify(entered));
 const oldToken=old.token;
 await stop();server=start(false);const current=await ready(true);
 check('Same-origin restart provides the required API with a fresh session',current.journey_api_version>=1&&!current.restart_required&&current.token!==oldToken);
 const missingModuleRetry=network.length;await page.click('#start-launch');
 await page.waitForFunction(()=>/reload this page/i.test(document.getElementById('start-setup-status').textContent)&&!document.getElementById('start-setup-status').textContent.includes('older than this page'));
 check('An already-open tab requests its missing module reload before changing any project',network.slice(missingModuleRetry).every(r=>r.path==='/api/session')&&JSON.stringify(await setupValues())===JSON.stringify(entered));
 await page.reload();await page.waitForFunction(()=>window.__ffApp?.designJourney,null,{timeout:180000});await page.click('[data-start="new"]');
 check('Reload after restart loads the new journey module and retains the complete setup',JSON.stringify(await setupValues())===JSON.stringify(entered));
 const retryStart=network.length;await page.click('#start-launch');
 await page.waitForSelector('#compass-dialog[open]',{timeout:180000});
 const draft=await page.evaluate(()=>window.__ffApp.collect());
 const compass=draft.editorState.compassDraft;
 check('The reported button now opens the three-floor Compass workspace',compass.floors.length===3&&await page.locator('[data-c-floor]').count()===3);
 check('Actual saved geometry inputs match 40 by 60 feet with the road to the west',draft.brief.width_mm===12192&&draft.brief.depth_mm===18288&&draft.brief.storeys===3&&draft.brief.road_bearing_deg===270&&compass.site.context==='middle');
 check('Retry after restart calls the real source-input consumer successfully',network.slice(retryStart).some(r=>r.path==='/api/design/inputs'&&r.status===200)&&!network.slice(retryStart).some(r=>r.status===404));
 check('Server restart keeps the original saved project and clears only the completed setup',await page.evaluate(before=>JSON.stringify(JSON.parse(localStorage.getItem('floorforge-saved-projects'))['working:existing-family-home'])===JSON.stringify(JSON.parse(before.saved)['working:existing-family-home'])&&!sessionStorage.getItem('floorforge-start-draft-v1'),preserved));
 await page.screenshot({path:resolve(out,'create-custom-design-working.png'),fullPage:true});
 await page.waitForFunction(()=>JSON.parse(localStorage.getItem('floorforge-draft-v1')||'{}').brief?.title==='West-facing three-floor launch regression');
 await page.reload();await page.waitForFunction(()=>window.__ffApp?.designJourney,null,{timeout:180000});
 const reopened=await page.evaluate(()=>window.__ffApp.collect());
 check('Created three-floor draft autosaves and reopens with the same floor identities',reopened.brief.width_mm===12192&&reopened.brief.depth_mm===18288&&reopened.brief.road_bearing_deg===270&&JSON.stringify(reopened.editorState.compassDraft.floors.map(f=>f.id))===JSON.stringify(compass.floors.map(f=>f.id)));
 check('No browser exceptions during stale-server recovery and creation',errors.length===0,errors);
 writeFileSync(resolve(out,'created-project.floorforge.json'),JSON.stringify(reopened,null,2));
}catch(error){errors.push(error.stack||String(error));console.error(error);process.exitCode=1;await page?.screenshot({path:resolve(out,'launch-failure.png'),fullPage:true}).catch(()=>{});}
finally{
 writeFileSync(resolve(out,'checks.json'),JSON.stringify({checks,errors,baselineServer:baseline,origin:url,serverOutput:work,network,serverLogs},null,2));
 await browser?.close();await stop();
}
