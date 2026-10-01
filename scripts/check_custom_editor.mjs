// Browser acceptance through the real local server. Run with PLAYWRIGHT_MODULE if needed.
import {spawn} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/custom-plan'),port=8876,url=`http://127.0.0.1:${port}`;
mkdirSync(out,{recursive:true});const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port',String(port),'--out','/tmp/ff-editor-browser'],{cwd:root,stdio:['ignore','pipe','pipe']});
const errors=[],checks=[];server.stderr.on('data',data=>console.error(String(data)));
const check=(name,pass,data)=>{checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
for(let i=0;i<60;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,300));}
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1024},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{timeout:180000});await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});
 await page.evaluate(()=>{window.__ffApp.viewer.paused=true;});
 await page.selectOption('#storeys','3');await page.click('#custom-open');await page.click('#plan-detail');await page.click('#plan-example');await page.waitForFunction(()=>window.__ffApp.planEditor.plan.floors.length===3);
 check('G+2 editor has three floor tabs',await page.locator('#plan-floor-tabs button').count()===3);
 await page.click('#plan-floor-tabs button:nth-child(2)');await page.click('#plan-room-list button:text-is("Bedroom")');
 check('Exact 4 × 4 m room',await page.inputValue('#plan-width')==='4.000'&&await page.inputValue('#plan-depth')==='4.000');
 await page.fill('#plan-width','4.010');await page.click('#plan-apply');check('Typed dimensions retained',await page.inputValue('#plan-width')==='4.010');
 await page.click('#plan-undo');check('Undo returns exact width',await page.evaluate(()=>window.__ffApp.planEditor.active.rooms.find(r=>r.kind==='bedroom').polygon[1][0])===7850);
 await page.click('#plan-redo');await page.click('#plan-undo');
 // Exercise the drawing surface itself, including coordinate transforms and pointer capture.
 const screen=async(x,y)=>page.evaluate(([x,y])=>{const svg=document.getElementById('plan-canvas'),D=svg.viewBox.baseVal.height-900;const p=new DOMPoint(x,D-y).matrixTransform(svg.getScreenCTM());return {x:p.x,y:p.y};},[x,y]);
 const drag=async(a,b)=>{await page.mouse.move(a.x,a.y);await page.mouse.down();await page.mouse.move(b.x,b.y,{steps:8});await page.mouse.up();};
 const initialCount=await page.evaluate(()=>window.__ffApp.planEditor.active.rooms.length);
 await page.selectOption('#plan-kind','store');await page.click('#plan-add');await drag(await screen(8400,9500),await screen(9400,10500));
 check('Pointer drawing creates exact snapped room',await page.evaluate(n=>{const e=window.__ffApp.planEditor,r=e.active.rooms.at(-1);return e.active.rooms.length===n+1&&e.area(r)===1;},initialCount));
 await page.click('#plan-undo');await page.click('#plan-wall');await drag(await screen(8400,9500),await screen(9000,9500));
 check('Pointer drawing creates orthogonal wall',await page.evaluate(()=>{const w=window.__ffApp.planEditor.active.walls.at(-1);return w.a[1]===w.b[1]&&Math.abs(w.b[0]-w.a[0])===600;}));
 await drag(await screen(8700,9500),await screen(8900,9600));
 check('Moving a wall retains its ID and length',await page.evaluate(()=>{const w=window.__ffApp.planEditor.active.walls.at(-1);return w.a[0]===8600&&w.a[1]===9600&&w.b[0]-w.a[0]===600;}));
 await page.click('#plan-undo');await page.click('#plan-undo');await page.click('#plan-room-list button:text-is("Bedroom")');
 const openingId=await page.evaluate(()=>window.__ffApp.planEditor.active.openings.find(o=>o.id==='custom-F1-bed-window').id);
 await page.locator('#plan-opening-list .plan-opening-row').filter({hasText:'window'}).locator('button').first().click();
 await page.fill('#plan-opening-width','1.8');await page.click('#plan-opening-add');
 check('Editing an opening retains stable ID',await page.evaluate(id=>window.__ffApp.planEditor.active.openings.find(o=>o.id===id)?.width===1800,openingId));
 await page.click('#plan-undo');await page.click('#plan-remove-floor');check('Remove floor is explicit',await page.locator('#plan-floor-tabs button').count()===2);await page.click('#plan-undo');
 check('Undo restores floor and linked stairs',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.length===3&&window.__ffApp.planEditor.plan.stairs[0].roomIds.length===3));
 await page.click('#plan-validate');
 await page.waitForFunction(()=>document.getElementById('plan-validation').textContent.startsWith('Geometry passes'),null,{timeout:60000});
 await page.click('#plan-room-list button:text-is("Bedroom")');await page.screenshot({path:out+'/editor-first-floor.png'});
 const original=await page.evaluate(()=>window.__ffApp.collect());
 await page.click('#plan-generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const generated=await page.evaluate(()=>({hash:window.__ff.scene.planHash,buildingHash:window.__ff.building.planHash,reportHash:window.__ff.report.planHash,floors:window.__ff.scene.storeys}));
 check('Same revision in model, scene and report',generated.hash===generated.buildingHash&&generated.hash===generated.reportHash&&generated.floors===3,generated);
 await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setView('hero');v.composer.render(0);});await page.screenshot({path:out+'/custom-g2-hero.png'});
 await page.click('#custom-open');await page.click('#plan-floor-tabs button:nth-child(2)');await page.click('#plan-room-list button:text-is("Bedroom")');await page.click('#plan-show-3d');
 check('2D selection highlights matching stable 3D room',await page.evaluate(()=>window.__ffApp.viewer.selectedRoomId)==='custom-F1-bedroom');
 await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.composer.render(0);});await page.screenshot({path:out+'/custom-room-selection.png'});
 // A newer edit while generation is running must never be replaced by the older build.
 const before=await page.evaluate(()=>window.__ff.buildId);
 await page.evaluate(()=>{window.__ffApp.generate();window.__ffApp.markDraftChanged();});await page.waitForFunction(()=>!document.getElementById('generate').disabled,null,{timeout:240000});
 check('Older in-flight generation does not replace current draft',await page.evaluate(()=>window.__ffApp.draftStale&&document.getElementById('draft-state').textContent.includes('Previous')));
 // Remove terrace access and ensure failure leaves the old preview clearly labelled.
 await page.click('#custom-open');await page.click('#plan-floor-tabs button:nth-child(2)');await page.click('#plan-room-list button:text-is("Hall")');
 const hallRemove=page.locator('#plan-opening-list .plan-opening-row').filter({hasText:'glazed'}).locator('button').last();await hallRemove.click();await page.click('#plan-validate');
 await page.waitForFunction(()=>document.getElementById('plan-errors').textContent.includes('UNREACHABLE'),null,{timeout:60000});
 await page.screenshot({path:out+'/editor-conflict.png'});await page.click('#plan-generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled,null,{timeout:240000});
 check('Failure visibly marks previous design and blocks current export',await page.evaluate(()=>window.__ffApp.draftStale&&document.getElementById('draft-state').textContent.includes('Generation failed')&&document.getElementById('export-top').disabled));
 check('Failed generation retains previous build identity',await page.evaluate(()=>window.__ff.buildId)===before);
 await page.evaluate(p=>window.__ffApp.applyProject(p),original);
 await page.selectOption('#plan-mode','guide');await page.click('#grid-open');
 for(let f=0;f<3;f++){await page.click(`#grid-floor-tabs button:nth-child(${f+1})`);check(`Floor ${f} always has 16 cells`,await page.locator('#grid-board button').count()===16);await page.selectOption('#grid-brush',`bedroom-${f+1}`);await page.locator('#grid-board button').first().click();}
 await page.click('#grid-keep');const guide=await page.evaluate(()=>window.__ffApp.collect().grid);
 check('All three distinct boards submitted',guide.floors.length===3&&guide.floors.every((rows,f)=>rows.flat().includes(`bedroom-${f+1}`)),guide);
 await page.evaluate(p=>window.__ffApp.applyProject(p),original);await page.waitForTimeout(700);
 const beforeSave=await page.evaluate(()=>window.__ffApp.collect());await page.reload();await page.waitForFunction(()=>window.__ffApp?.planEditor?.plan?.floors.length===3,null,{timeout:240000});
 check('Autosave restores all floors and terrace',await page.evaluate(()=>window.__ffApp.collect().customPlan.floors[1].rooms.some(r=>r.kind==='terrace')));
 const p=await page.evaluate(()=>window.__ffApp.collect());
 async function hash(project){const s=await (await fetch(url+'/api/session')).json();return (await(await fetch(url+'/api/intent',{method:'POST',headers:{'Content-Type':'application/json','X-FloorForge-Token':s.token},body:JSON.stringify(project)})).json()).planHash;}
 check('Save/reopen retains plan hash',await hash(p)===await hash(beforeSave));
 await page.click('#custom-open');await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/editor-mobile.png',fullPage:true});
 check('Mobile editor does not overflow document',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 check('No browser runtime errors',errors.length===0,errors);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');await browser.close();server.kill();}
