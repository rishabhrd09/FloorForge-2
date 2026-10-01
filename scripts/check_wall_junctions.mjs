// Reproduce the reported board through the actual editor and verify its compiled neighbours.
import {spawn} from 'node:child_process';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/wall-junctions'),url='http://127.0.0.1:8881';
mkdirSync(out,{recursive:true});
const source=JSON.parse(readFileSync(resolve(out,'reported-guide.floorforge.json'))),valid=JSON.parse(readFileSync(resolve(out,'valid-outdoor-junction.floorforge.json')));
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8881','--out','/tmp/ff-wall-junction-ui'],{cwd:root,stdio:['ignore','pipe','pipe']});
server.stderr.on('data',d=>console.error(String(d)));
const checks=[],errors=[];let browser;
function check(name,pass,data){checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);}
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,300));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{timeout:180000});await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 await page.evaluate(p=>window.__ffApp.applyProject(p),source);await page.click('#grid-open');await page.click('#grid-check');
 await page.waitForFunction(()=>document.querySelectorAll('#grid-conflicts button').length===5);
 check('All five guide issues are present without a clipped inner list',await page.evaluate(()=>{const d=document.getElementById('grid-conflicts');return d.scrollHeight<=d.clientHeight+1;}));
 check('Each floor shows its own issue count',await page.locator('#grid-floor-tabs .guide-issue-count').allTextContents().then(x=>x.join(',')==='3,1,1'));
 const visibleFooter=()=>page.evaluate(()=>['grid-check','grid-keep','grid-convert'].every(id=>{const r=document.getElementById(id).getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight&&r.right<=innerWidth;}));
 check('Conversion and guide actions stay in the desktop viewport',await visibleFooter());
 check('Ground guide has exactly 16 cells and retains every painted label',await page.locator('#grid-board button').count()===16);
 await page.screenshot({path:out+'/guide-issues-desktop.png'});
 await page.locator('#grid-conflicts button').filter({hasText:'Second has 0 bedrooms'}).click();
 check('Selecting an issue switches to the affected upper floor',await page.locator('#grid-floor-tabs .active').textContent().then(t=>t.startsWith('Second'))&&await page.locator('#grid-board button').allTextContents().then(t=>t.every(s=>!s)));
 await page.setViewportSize({width:390,height:844});
 check('Conversion stays reachable on a phone without horizontal overflow',await visibleFooter()&&await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.screenshot({path:out+'/guide-issues-mobile.png'});await page.setViewportSize({width:1440,height:1000});
 await page.click('#grid-convert');await page.waitForSelector('#plan-dialog[open]');await page.click('#plan-validate');
 await page.waitForFunction(()=>window.__ffApp.planEditor.displayErrors.some(e=>e.code==='EMPTY_FLOOR'));
 check('Custom validation reports both empty floors together',await page.evaluate(()=>window.__ffApp.planEditor.displayErrors.filter(e=>e.code==='EMPTY_FLOOR').map(e=>e.floor).join(',')==='1,2'));
 await page.click('[data-close="plan-dialog"]');const customBefore=await page.evaluate(()=>JSON.stringify(window.__ffApp.collect().customPlan));
 await page.click('#grid-open');
 check('Opening saved guides explicitly preserves active Custom Plan',await page.locator('#grid-mode').textContent().then(t=>t.startsWith('Custom Plan is active'))&&await page.evaluate(()=>document.getElementById('plan-mode').value)==='custom');
 await page.click('#grid-edit-custom');check('Return to Custom Plan keeps authored geometry',await page.evaluate(()=>JSON.stringify(window.__ffApp.collect().customPlan))===customBefore);
 await page.click('[data-close="plan-dialog"]');
 // Reconstruct only Ground to exercise the former topology failure before other floor errors.
 const single={...source,brief:{...source.brief,storeys:1},grid:{...source.grid,floorIds:['g'],floors:[source.grid.floors[0]]}};
 await page.evaluate(p=>window.__ffApp.applyProject(p),single);await page.click('#grid-open');await page.click('#grid-convert');await page.waitForSelector('#plan-dialog[open]');await page.click('#plan-validate');
 await page.waitForFunction(()=>window.__ffApp.planEditor.displayErrors.some(e=>e.code==='ROOM_MINIMUM'));
 check('Reported board clears wall topology and reaches genuine room-size/access validation',await page.evaluate(()=>!window.__ffApp.planEditor.displayErrors.some(e=>e.code==='WALL_TOPOLOGY')&&window.__ffApp.planEditor.active.rooms.length===10));
 await page.screenshot({path:out+'/reported-ground-validation.png'});await page.click('[data-close="plan-dialog"]');
 // A valid plan with the same kind of wall junction must generate all the way to the scene.
 await page.evaluate(p=>window.__ffApp.applyProject(p),valid);await page.click('#custom-open');await page.click('#plan-detail');await page.click('#plan-validate');
 await page.waitForFunction(()=>document.getElementById('plan-validation').textContent.startsWith('Geometry passes'));
 await page.click('#plan-generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const built=await page.evaluate(()=>{const b=window.__ff.building;return {hash:b.planHash,sceneHash:window.__ff.scene.planHash,reportHash:window.__ff.report.planHash,door:b.openings.find(o=>o.id==='veranda-door').connects,window:b.openings.find(o=>o.id==='courtyard-window').connects};});
 check('Generated door connects Living to Veranda',built.door.join(',')==='living,veranda');
 check('Generated window connects Living to Courtyard',built.window.join(',')==='courtyard,living');
 check('Model, scene and report share the authored revision hash',built.hash===built.sceneHash&&built.hash===built.reportHash);
 check('Input coverage remains available without displacing the design',await page.locator('#input-coverage').evaluate(el=>!el.open));
 await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setMode('dollhouse');v.composer.render(0);});await page.screenshot({path:out+'/outdoor-junction-3d.png'});
 // Force a real generation failure and ensure the previous rendering cannot masquerade as current.
 await page.evaluate(p=>window.__ffApp.applyProject(p),{...valid,customPlan:{...valid.customPlan,floors:[{...valid.customPlan.floors[0],openings:[]}]}});
 check('Zero-bedroom custom geometry can submit from the main form',await page.locator('#bedrooms').evaluate(el=>el.readOnly&&el.min==='0'&&el.checkValidity()));
 const invalid=await page.evaluate(()=>Array.from(document.getElementById('brief-form').elements).filter(el=>el.willValidate&&!el.validity.valid).map(el=>({id:el.id,message:el.validationMessage})));check('Exact metric plot dimensions remain valid when displayed in feet',invalid.length===0,invalid);
 await page.click('#generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&document.getElementById('draft-state').textContent.includes('Generation failed'),null,{timeout:120000});
 check('Failed generation retains the stale warning and disables current-design exports',await page.evaluate(()=>window.__ffApp.draftStale&&document.getElementById('export-top').disabled&&!document.getElementById('review-draft-issues').hidden));
 check('No browser runtime errors',errors.length===0,errors);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();server.kill();}
