// Guest-room generation and floor/roof controls through the real studio.
import {spawn} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/drawing-room-guide'),url='http://127.0.0.1:8883';mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8883','--out','/tmp/ff-guest-guide-ui'],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>console.error(String(d)));
let browser;const checks=[],errors=[];const check=(name,pass,data)=>{checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
const empty=()=>Array.from({length:4},()=>Array(4).fill(''));
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,300));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{timeout:180000});await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 await page.click('#grid-open');
 check('Drawing room is visible as a guest-seating card',await page.locator('#grid-palette [data-room="drawing-room"]').isVisible()&&await page.locator('#grid-palette [data-room="drawing-room"]').textContent()==='Drawing roomGuest seating');
 check('Drawing room is offered by Quick Guide',!(await page.locator('#grid-brush option[value="drawing-room"]').textContent()).includes('Custom Plan'));
 await page.selectOption('#grid-brush','drying-room');check('Drying room is explicitly laundry/service', (await page.locator('#grid-brush-help').textContent()).includes('laundry drying'));
 await page.click('#grid-palette [data-room="drawing-room"]');check('Guest room is clearly distinct from shared Living', (await page.locator('#grid-brush-help').textContent()).includes('separate guest sitting room'));
 await page.click('[data-close="grid-dialog"]');
 const boards=[empty(),empty(),empty()];boards[0][3][0]='master-bedroom';boards[0][3][1]='master-bedroom';boards[0][2][0]='stair';boards[0][2][1]='living';boards[0][1][0]='kitchen';boards[0][1][1]='dining';
 const project={brief:{storeys:3,bedrooms:3,roof_access:false},grid:{mode:'spatial_hint',rows:4,cols:4,floorIds:['floor-0','floor-1','floor-2'],floors:boards}};
 await page.evaluate(p=>window.__ffApp.applyProject(p),project);await page.click('#grid-open');await page.click('#grid-check');await page.waitForFunction(()=>document.getElementById('grid-conflicts').textContent.includes('Second has 0 bedrooms'));
 check('An explicitly selected G+2 remains three occupied floors',await page.locator('#grid-floor-tabs button').count()===3);
 check('Stair restriction is identified as a planner limitation', (await page.locator('#grid-conflicts').textContent()).includes('Planner limitation'));
 check('Stair issue has a direct exact-editor action',await page.locator('#grid-conflicts .issue-fix').isVisible());
 await page.click('#grid-use-g1');await page.waitForFunction(()=>!document.getElementById('grid-conflicts').textContent.includes('Second has 0 bedrooms'));
 const corrected=await page.evaluate(()=>window.__ffApp.collect());
 check('G+1 submits only Ground and First, with separate roof access',corrected.grid.floors.length===2&&corrected.sources.find(s=>s.id==='studio-field-edits').values.storeys===2&&corrected.sources.find(s=>s.id==='studio-field-edits').values.roof_access===true);
 check('Original three guide boards stay saved for undo',corrected.editorState.guideFloors.length===3&&JSON.stringify(corrected.grid.floors[0])===JSON.stringify(boards[0]));
 check('The guide shows exactly two floor tabs and 16 cells',await page.locator('#grid-floor-tabs button').count()===2&&await page.locator('#grid-board button').count()===16);
 await page.click('#grid-undo-levels');check('Floor change has working undo',await page.locator('#grid-floor-tabs button').count()===3&&!(await page.locator('#grid-roof-access').isChecked()));
 await page.click('#grid-use-g1');await page.click('[data-close="grid-dialog"]');
 const saved=await page.evaluate(()=>window.__ffApp.collect());await page.evaluate(p=>window.__ffApp.applyProject(p),JSON.parse(JSON.stringify(saved)));await page.click('#grid-open');
 check('Save/reopen does not resurrect the unwanted Second floor',await page.locator('#grid-floor-tabs button').count()===2&&await page.evaluate(()=>window.__ffApp.collect().grid.floors.length===2));
 await page.click('#grid-check');await page.waitForFunction(()=>document.getElementById('grid-conflicts').textContent.includes('Planner limitation'));
 await page.screenshot({path:out+'/guide-issues-and-floors.png'});
 await page.click('#grid-conflicts .issue-fix');await page.waitForSelector('#plan-dialog[open]');
 check('Stair action opens and selects the authored stair without moving it to a front corner',await page.evaluate(()=>{const e=window.__ffApp.planEditor,r=e.plan.floors[e.floor].rooms.find(r=>e.selected.has(r.id));return r?.kind==='stair'&&Math.min(...r.polygon.map(p=>p[1]))>6000;}));
 await page.click('[data-close="plan-dialog"]');
 // Main floor selector must still trim an active custom plan, with the editor's existing undo.
 const custom=await (await fetch(url+'/api/plan/example?storeys=3')).json();await page.evaluate(p=>window.__ffApp.applyProject(p),custom);await page.selectOption('#storeys','2');await page.click('#custom-open');
 check('Main floor count still synchronizes an active Custom Plan',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.length===2));
 await page.click('#plan-undo');check('Custom floor removal keeps working undo',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.length===3));await page.click('[data-close="plan-dialog"]');
 // Fresh guide: drag a guest-room card into the front-right cell, then generate it.
 await page.evaluate(()=>window.__ffApp.applyProject({brief:{storeys:2,roof_access:true}}));await page.click('#grid-open');
 await page.locator('#grid-palette [data-room="drawing-room"]').dragTo(page.locator('#grid-board button').nth(15));
 check('Dragging the card writes a drawing-room hint to the selected cell',await page.evaluate(()=>window.__ffApp.collect().grid?.floors[0][0][3]==='drawing-room'));
 await page.click('#grid-check');await page.waitForFunction(()=>document.getElementById('grid-state').textContent.includes('Programme checks pass'));
 await page.locator('.guide-board-panel').evaluate(el=>el.scrollTop=0);await page.screenshot({path:out+'/drawing-room-palette.png'});
 await page.setViewportSize({width:390,height:844});await page.locator('.guide-workspace').evaluate(el=>el.scrollTop=0);check('Guide actions remain reachable on a phone',await page.locator('#grid-keep').evaluate(el=>{const r=el.getBoundingClientRect();return r.bottom<=innerHeight&&r.right<=innerWidth;}));await page.screenshot({path:out+'/drawing-room-mobile.png'});await page.setViewportSize({width:1440,height:1000});
 await page.click('#grid-keep');await page.click('#generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const result=await page.evaluate(()=>({b:window.__ff.building,s:window.__ff.scene,p:window.__ffApp.collect()})),guest=result.b.spaces.find(r=>r.kind==='drawing-room');
 check('Generated G+1 contains a separate Drawing room and Living',result.b.storeys===2&&!!guest&&result.b.spaces.some(r=>r.kind==='living'&&r.id!==guest.id));
 check('Guest room has a sofa and coffee table in the actual scene',['sofa','coffee-table'].every(kind=>result.s.furniture.some(f=>f.room_id===guest.id&&f.kind===kind)));
 check('Roof terrace is reachable above First without another occupied floor',result.b.floors.length===2&&result.s.roof_level===2&&result.b.rooftop&&result.b.stairs.some(s=>s.to_floor===2||s.toFloor===2),result.b.stairs);
 check('Building and scene share the generated plan hash',result.b.planHash===result.s.planHash);
 writeFileSync(out+'/drawing-room.floorforge.json',JSON.stringify(result.p,null,2)+'\n');
 await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setMode('dollhouse');v.setFloor(0);v.composer.render(0);});await page.screenshot({path:out+'/drawing-room-3d.png'});
 check('No browser runtime errors',errors.length===0,errors);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();server.kill();}
