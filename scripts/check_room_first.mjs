import {spawn} from 'node:child_process';
import {mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/room-first'),url='http://127.0.0.1:8884';mkdirSync(out,{recursive:true});
const rooms=[['living','living',150,150],['drawing','drawing-room',4150,150],['kitchen','kitchen',150,4150],['bed','bedroom',4150,4150]].map(([id,kind,x,y])=>({id,kind,name:kind==='drawing-room'?'Drawing room':kind[0].toUpperCase()+kind.slice(1),polygon:[[x,y],[x+4000,y],[x+4000,y+4000],[x,y+4000]]}));
const rough={brief:{storeys:1,bedrooms:1,width_mm:10000,depth_mm:12000,left_mm:500,right_mm:500,front_mm:1000,rear_mm:1000,roof_access:false},customPlan:{schema:'floorforge.custom-plan/1',units:'mm',wallThickness:150,floors:[{id:'floor-0',rooms,walls:[],openings:[]}],stairs:[]}};
writeFileSync(out+'/rough.floorforge.json',JSON.stringify(rough,null,2)+'\n');
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8884','--out','/tmp/ff-room-first-ui'],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>console.error(String(d)));
let browser;const checks=[],errors=[];const check=(name,pass,data)=>{checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,300));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1512,height:1050},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{timeout:180000});await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 const empty=structuredClone(rough);empty.customPlan.floors[0].rooms=[];await page.evaluate(p=>window.__ffApp.applyProject(p),empty);await page.click('#custom-open');
 const prepareFit=async()=>{await page.click('#plan-assist');await page.waitForFunction(()=>!window.__ffApp.planEditor.preparing);if(await page.locator('#plan-fit-choice').isVisible())await page.click('#plan-fit-yes');};
 const screen=async(x,y)=>page.evaluate(({x,y})=>{const e=window.__ffApp.planEditor,[,d]=e.getEnvelope();return new DOMPoint(x,d-y).matrixTransform(e.svg.getScreenCTM()).toJSON();},{x,y});
 await page.click('#plan-palette [data-kind="drawing-room"]');let pt=await screen(1650,1650);await page.mouse.click(pt.x,pt.y);
 await page.click('#plan-palette [data-kind="living"]');pt=await screen(4650,1950);await page.mouse.click(pt.x,pt.y);
 check('Rough placement keeps rooms near the chosen positions without rejecting overlaps',await page.evaluate(()=>{const e=window.__ffApp.planEditor,r=e.active.rooms;return r.length===2&&Math.min(...r.find(r=>r.kind==='drawing-room').polygon.map(p=>p[0]))===150;})&&(await page.locator('#plan-placement-note').textContent()).includes('Smart fit'));
 await page.click('[data-close="plan-dialog"]');
 await page.evaluate(p=>window.__ffApp.applyProject(p),rough);await page.click('#custom-open');
 check('Arrange rooms is the default, with wall and opening tools hidden',await page.locator('#plan-arrange').getAttribute('aria-pressed')==='true'&&!(await page.locator('#plan-wall').isVisible())&&!(await page.locator('#plan-opening-kind').isVisible()));
 await page.locator('#plan-room-list button').filter({hasText:'Bedroom'}).click();check('Room dimensions stay available without technical position fields',await page.locator('#plan-width').isVisible()&&await page.locator('#plan-depth').isVisible()&&!(await page.locator('#plan-x').isVisible()));
 await page.fill('#plan-width','4');await page.fill('#plan-depth','4');await page.click('#plan-apply');
 const before=await page.evaluate(()=>window.__ffApp.planEditor.snapshot());
 await prepareFit();
 const prepared=await page.evaluate(()=>window.__ffApp.collect());
 check('One action fixes shared wall space and adds openings',prepared.customPlan.floors[0].openings.length>=8&&await page.locator('#plan-errors .plan-issue').count()===0);
 check('Every authored room retains its exact 4 × 4 m size',prepared.customPlan.floors[0].rooms.every(r=>Math.max(...r.polygon.map(p=>p[0]))-Math.min(...r.polygon.map(p=>p[0]))===4000&&Math.max(...r.polygon.map(p=>p[1]))-Math.min(...r.polygon.map(p=>p[1]))===4000));
 check('Assistance explains its changes',await page.locator('#plan-assist-changes').isVisible()&&(await page.locator('#plan-assist-changes').textContent()).includes('room size kept'));
 await page.click('#plan-undo');check('Undo restores the whole rough plan',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);await page.click('#plan-redo');
 const edge=await screen(8300,6300),movedEdge=await screen(8350,6300);await page.mouse.move(edge.x,edge.y);await page.mouse.down();await page.mouse.move(movedEdge.x,movedEdge.y,{steps:8});await page.mouse.up();
 check('Room edge handles allow later size refinement',await page.evaluate(()=>{const r=window.__ffApp.planEditor.active.rooms.find(r=>r.id==='bed');return Math.max(...r.polygon.map(p=>p[0]))-Math.min(...r.polygon.map(p=>p[0]))===4050;}));await page.click('#plan-undo');
 await page.screenshot({path:out+'/arrange-desktop.png'});
 let releasePrepare,receivedPrepare;const pendingResponse=new Promise(r=>receivedPrepare=r),release=new Promise(r=>releasePrepare=r);
 await page.route('**/api/plan/smart-fit',async route=>{const response=await route.fetch();receivedPrepare();await release;await route.fulfill({response});});
 const stable=await page.evaluate(()=>window.__ffApp.planEditor.snapshot());await page.click('#plan-assist');await pendingResponse;await page.fill('#plan-width','4.2');releasePrepare();await page.waitForFunction(()=>!window.__ffApp.planEditor.preparing);
 check('A delayed preparation never overwrites dimensions being typed',await page.locator('#plan-width').inputValue()==='4.2'&&await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===stable&&(await page.locator('#plan-validation').textContent()).includes('changed the draft'));
 await page.unroute('**/api/plan/smart-fit');await page.fill('#plan-width','4');
 await page.click('#plan-detail');check('Fine-tune reveals exact wall and opening tools',await page.locator('#plan-wall').isVisible()&&await page.locator('#plan-x').isVisible()&&await page.locator('#plan-opening-kind').isVisible());await page.screenshot({path:out+'/fine-tune-desktop.png'});await page.click('#plan-arrange');
 await page.setViewportSize({width:390,height:844});check('Phone preview action stays inside the viewport',await page.locator('#plan-generate').evaluate(el=>{const r=el.getBoundingClientRect();return r.bottom<=innerHeight&&r.right<=innerWidth;}));await page.screenshot({path:out+'/arrange-mobile.png'});await page.setViewportSize({width:1512,height:1050});
 // Show the screenshot's empty-upper-floor problem as one actionable decision.
 await page.click('[data-close="plan-dialog"]');const three=structuredClone(rough);three.brief.storeys=3;three.customPlan.floors.push({id:'floor-1',rooms:[],walls:[],openings:[]},{id:'floor-2',rooms:[],walls:[],openings:[]});await page.evaluate(p=>window.__ffApp.applyProject(p),three);await page.click('#custom-open');await prepareFit();
 check('Empty floors are explained one at a time without raw error codes',await page.locator('#plan-errors .plan-issue').count()===1&&!(await page.locator('#plan-errors').textContent()).includes('EMPTY_FLOOR'));
 await page.locator('#plan-errors button').filter({hasText:'Copy floor below'}).click();check('Copy below starts an editable floor in one step',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors[1].rooms.length===4));await page.click('#plan-undo');
 await prepareFit();await page.screenshot({path:out+'/empty-floor-action.png'});
 await page.locator('#plan-errors button').filter({hasText:'Use Ground only'}).click();check('Unused floors are removed only by an explicit action',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors.length===1&&document.getElementById('storeys').value==='1'));
 // The main Generate button must use the same assisted flow as the editor.
 await page.click('[data-close="plan-dialog"]');await page.click('#generate');await page.waitForSelector('#plan-fit-choice:not([hidden])');await page.click('#plan-fit-yes');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const result=await page.evaluate(()=>({scene:window.__ff.scene,building:window.__ff.building,project:window.__ffApp.collect()}));
 check('Rough rooms reach a matching generated building and scene',result.building.planning.custom&&result.scene.planHash===result.building.planHash&&result.building.spaces.length===4);
 check('Exact dimensions survive all the way to the building',result.building.spaces.every(s=>Math.abs(s.area_m2-16)<1e-6));
 writeFileSync(out+'/prepared.floorforge.json',JSON.stringify(result.project,null,2)+'\n');await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setMode('dollhouse');v.setFloor(0);v.composer.render(0);});await page.screenshot({path:out+'/prepared-3d.png'});
 const g1=await (await fetch(url+'/api/plan/example?storeys=2')).json();await page.evaluate(p=>window.__ffApp.applyProject(p),g1);await page.click('#custom-open');await page.click('#plan-generate');await page.waitForSelector('#plan-fit-choice:not([hidden])');await page.click('#plan-fit-yes');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 check('Assisted G+1 preview has two occupied floors and stair access to its roof',await page.evaluate(()=>window.__ff.building.storeys===2&&window.__ff.building.floors.length===2&&window.__ff.scene.roof_level===2&&window.__ff.building.stairs.some(s=>s.roof_access)));
 check('No browser runtime errors',errors.length===0,errors);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();server.kill();}
