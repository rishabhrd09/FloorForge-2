import {spawn} from 'node:child_process';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/placement-editor'),url='http://127.0.0.1:8882';mkdirSync(out,{recursive:true});
const project={schema:'floorforge.project/0.4',brief:{roof_access:true}};
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8882','--out','/tmp/ff-placement-ui'],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>console.error(String(d)));
let browser;const checks=[],errors=[];const check=(name,pass,data)=>{checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,300));}
 for(const n of [1,2,3]){const p=await (await fetch(url+'/api/plan/example?storeys='+n)).json();check(`${n} occupied floors in the matching example`,p.brief.storeys===n&&p.customPlan.floors.length===n&&p.brief.roof_access);}
 check('Default example is G+1',((await (await fetch(url+'/api/plan/example')).json()).brief.storeys)===2);
 check('Malformed floor count is a clear 400',(await fetch(url+'/api/plan/example?storeys=abc')).status===400);
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{timeout:180000});await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 check('Fresh studio defaults to two occupied floors',await page.locator('#storeys').inputValue()==='2');
 await page.evaluate(p=>window.__ffApp.applyProject(p),project);await page.click('#generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const before=await page.evaluate(()=>({scene:window.__ff.scene,building:window.__ff.building}));
 check('G+1 has two floors plus a separate roof level',before.building.storeys===2&&before.building.floors.length===2&&before.scene.roof_level===2);
 await page.click('#edit-placements');await page.waitForSelector('#placement-dialog[open]');
 const id='F0-living/coffee-table';const pt=await page.evaluate(id=>{const e=window.__ffApp.layoutEditor,i=e.items().find(i=>i.id===id),[x,y]=i.pivot,m=e.svg.getScreenCTM();const p=new DOMPoint(x,e.depth-y).matrixTransform(m);return {x:p.x,y:p.y,dx:m.a*.2};},id);
 await page.mouse.move(pt.x,pt.y);await page.mouse.down();await page.mouse.move(pt.x+pt.dx,pt.y,{steps:8});await page.mouse.up();
 check('Actual pointer drag records a 200 mm table move',await page.evaluate(id=>window.__ffApp.layoutEditor.edits.furnitureLayout.find(e=>e.id===id)?.dx===.2,id));
 await page.click('#placement-undo');check('Undo removes the placement',await page.evaluate(()=>window.__ffApp.layoutEditor.edits.furnitureLayout.length===0));await page.click('#placement-redo');
 await page.screenshot({path:out+'/furniture-editor.png'});
 await page.setViewportSize({width:390,height:844});check('Placement actions remain reachable on a phone',await page.locator('#placement-apply').evaluate(el=>{const r=el.getBoundingClientRect();return r.bottom<=innerHeight&&r.right<=innerWidth; }));await page.screenshot({path:out+'/furniture-editor-mobile.png'});await page.setViewportSize({width:1440,height:1000});
 await page.click('#placement-apply');await page.waitForFunction(()=>!document.getElementById('placement-dialog').open,null,{timeout:120000});await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const after=await page.evaluate(()=>({scene:window.__ff.scene,building:window.__ff.building,project:window.__ffApp.collect(),base:document.querySelector('#export-list a')?.href}));
 const group=before.scene.editables.find(i=>i.id===id),ids=new Set(group.nodeIds);
 check('Only the table assembly changes in the generated scene',before.scene.nodes.every((n,i)=>ids.has(n.id)?Math.abs(after.scene.nodes[i].position[0]-n.position[0]-.2)<1e-8:JSON.stringify(n)===JSON.stringify(after.scene.nodes[i])));
 check('Materials, assets, lighting and cameras are unchanged', ['materials','assets','lights','cameras','vegetation','lawns'].every(k=>JSON.stringify(before.scene[k])===JSON.stringify(after.scene[k])));
 check('Saved project retains the furniture transform',after.project.furnitureLayout[0].dx===.2);
 const session=await (await fetch(url+'/api/session')).json();const post=async(path,p)=>{const r=await fetch(url+path,{method:'POST',headers:{'Content-Type':'application/json','X-FloorForge-Token':session.token},body:JSON.stringify(p)});return {status:r.status,data:await r.json()};};
 check('Save/reopen yields the generated plan hash',(await post('/api/intent',JSON.parse(JSON.stringify(after.project)))).data.planHash===after.scene.planHash);
 writeFileSync(out+'/furniture-move.floorforge.json',JSON.stringify(after.project,null,2)+'\n');
 // A bad move stays staged with an object-level error, leaving the generated scene intact.
 await page.click('#edit-placements');await page.locator('#placement-list button').filter({hasText:'Coffee Table'}).click();await page.fill('#placement-x','100');await page.click('#placement-exact');await page.click('#placement-check');await page.waitForFunction(()=>document.getElementById('placement-status').textContent.includes('must fit inside'),null,{timeout:120000});
 check('Invalid placement is explained without replacing the valid model',await page.evaluate(h=>window.__ff.scene.planHash===h,after.scene.planHash));await page.click('#placement-close');
 // Reset explicitly, generate, then drag one occupied bedroom onto the other.
 await page.click('#reset-placements');await page.click('#generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 await page.click('#edit-placements');await page.click('#placement-rooms');await page.locator('#placement-floors button').filter({hasText:'First'}).click();
 const swap=await page.evaluate(()=>{const e=window.__ffApp.layoutEditor,m=e.svg.getScreenCTM();return ['F1-bed-m','F1-bed-2'].map(id=>{const p=e.polygon(e.items().find(i=>i.id===id)),x=p.reduce((n,p)=>n+p[0],0)/p.length,y=p.reduce((n,p)=>n+p[1],0)/p.length;return new DOMPoint(x,e.depth-y).matrixTransform(m).toJSON();});});
 await page.mouse.move(swap[0].x,swap[0].y);await page.mouse.down();await page.mouse.move(swap[1].x,swap[1].y,{steps:12});await page.mouse.up();
 check('Dropping a bedroom onto another records both destination polygons',await page.evaluate(()=>window.__ffApp.layoutEditor.edits.roomEdits.length===2));await page.screenshot({path:out+'/room-swap-editor.png'});
 await page.click('#placement-apply');await page.waitForFunction(()=>!document.getElementById('placement-dialog').open,null,{timeout:120000});await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 check('Applied bedroom swap changes the canonical room and keeps G+1',await page.evaluate(old=>{const b=window.__ff.building;return b.storeys===2&&JSON.stringify(b.spaces.find(s=>s.id==='F1-bed-m').polygon)===JSON.stringify(old.spaces.find(s=>s.id==='F1-bed-2').polygon);},before.building));
 await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setMode('dollhouse');v.setFloor(1);v.composer.render(0);});await page.screenshot({path:out+'/swapped-bedrooms-3d.png'});
 // Old editor no longer reinserts an unwanted Second floor after a storey reduction.
 const custom=await (await fetch(url+'/api/plan/example?storeys=3')).json();await page.evaluate(p=>window.__ffApp.applyProject(p),custom);await page.selectOption('#storeys','2');await page.click('#custom-open');
 check('Reducing G+2 to G+1 removes the editor Second floor',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.length===2&&document.getElementById('storeys').value==='2'));
 await page.click('#plan-undo');check('Floor removal is undoable',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.length===3));await page.click('#plan-redo');
 await page.click('#plan-example');check('Example loader follows the selected G+1 count',await page.waitForFunction(()=>window.__ffApp.planEditor.plan.floors.length===2).then(()=>true));
 check('No browser runtime errors',errors.length===0,errors);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();server.kill();}
