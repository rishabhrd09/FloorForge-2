// Real UI regression for palette placement, boundary repair and guide-to-plan generation.
import {spawn} from 'node:child_process';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/room-workflow'),port=8877,url=`http://127.0.0.1:${port}`;
mkdirSync(out,{recursive:true});const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port',String(port),'--out','/tmp/ff-room-workflow'],{cwd:root,stdio:['ignore','pipe','pipe']});
const checks=[],errors=[];server.stderr.on('data',data=>console.error(String(data)));
const check=(name,pass,data)=>{checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
let browser;
try{
 for(let i=0;i<80;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,300));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1512,height:1050},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url,{timeout:180000});await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 const brief={storeys:1,bedrooms:1,width_mm:10000,depth_mm:12000,left_mm:1000,right_mm:1000,front_mm:1000,rear_mm:1000,parking:false,pooja:false};
 await page.evaluate(p=>window.__ffApp.applyProject(p),{brief});await page.click('#custom-open');await page.click('#plan-detail');
 const screen=async(x,y)=>page.evaluate(([x,y])=>{const svg=document.getElementById('plan-canvas'),D=svg.viewBox.baseVal.height-900;const p=new DOMPoint(x,D-y).matrixTransform(svg.getScreenCTM());return {x:p.x,y:p.y};},[x,y]);
 const clickPoint=async(x,y)=>{const p=await screen(x,y);await page.mouse.click(p.x,p.y);};
 const drag=async(a,b)=>{await page.mouse.move(a.x,a.y);await page.mouse.down();await page.mouse.move(b.x,b.y,{steps:12});await page.mouse.up();};
 await page.click('#plan-palette [data-kind="drawing-room"]');await clickPoint(1650,1650);
 check('Click-to-place guest drawing room at real dimensions',await page.evaluate(()=>{const r=window.__ffApp.planEditor.active.rooms[0];return r.kind==='drawing-room'&&r.polygon[0][0]===150&&r.polygon[0][1]===150&&window.__ffApp.planEditor.area(r)===9;}));
 check('Drawing-room inspector explains seating, not drainage',await page.locator('#plan-room-help').textContent().then(x=>x.includes('sofa'))&&!(await page.locator('#plan-drain-field').isVisible()));
 await page.click('#plan-palette [data-kind="bedroom"]');const target=await screen(4970,1750),box=await page.locator('#plan-canvas').boundingBox();
 await page.locator('#plan-palette [data-kind="bedroom"]').dragTo(page.locator('#plan-canvas'),{targetPosition:{x:target.x-box.x,y:target.y-box.y}});
 check('Native palette drag-and-drop reserves a shared 150 mm wall',await page.evaluate(()=>{const e=window.__ffApp.planEditor,r=e.active.rooms.find(r=>r.kind==='bedroom');return r&&e.bounds(r)[0]===3300&&e.bounds(r)[1]===150;}));
 await page.click('#plan-select');const count=await page.evaluate(()=>window.__ffApp.planEditor.active.rooms.length);
 await page.click('#plan-palette [data-kind="kitchen"]');await clickPoint(1800,1800);
 check('Overlapping palette drop is explained and not committed',await page.evaluate(n=>window.__ffApp.planEditor.active.rooms.length===n&&document.getElementById('plan-placement-note').textContent.includes('overlaps'),count));
 await page.click('#plan-select');await page.click('#plan-room-list button:text-is("Drawing room · guests")');
 const firstId=await page.evaluate(()=>window.__ffApp.planEditor.active.rooms[0].id);await drag(await screen(1650,1650),await screen(-250,-250));
 check('Dragging outside keeps clear size and outer walls inside boundary',await page.evaluate(id=>{const e=window.__ffApp.planEditor,r=e.active.rooms.find(r=>r.id===id);return e.bounds(r)[0]===150&&e.bounds(r)[1]===150&&e.area(r)===9;},firstId));
 await page.fill('#plan-x','7.5');await page.click('#plan-apply');
 check('Typed boundary conflict is immediate and named',await page.locator('#plan-errors').textContent().then(x=>x.includes('Drawing room')&&x.includes('right by 2650 mm')));
 await page.screenshot({path:out+'/named-boundary-repair.png'});
 await page.locator('#plan-errors .issue-fix').first().click();
 check('Move inside repair keeps exact dimensions and stable ID',await page.evaluate(id=>{const e=window.__ffApp.planEditor,r=e.active.rooms.find(r=>r.id===id);return e.bounds(r)[0]===4850&&e.area(r)===9;},firstId));
 await page.click('#plan-undo');check('Boundary repair is undoable',await page.inputValue('#plan-x')==='7.500');await page.click('[data-close="plan-dialog"]');
 // The failing screenshot programme: two assigned ground bedrooms leave a G+2 floor empty.
 const floors=Array.from({length:3},()=>Array.from({length:4},()=>Array(4).fill('')));floors[0][3]=['master-bedroom','courtyard','bedroom-1','bedroom-1'];floors[0][0]=Array(4).fill('outer-lobby');floors[0][1][0]='kitchen';
 await page.evaluate(p=>window.__ffApp.applyProject(p),{brief:{...brief,storeys:3,bedrooms:3},grid:{mode:'spatial_hint',rows:4,cols:4,floorIds:['g','f','s'],floors}});await page.click('#grid-open');await page.click('#grid-check');
 await page.waitForFunction(()=>document.getElementById('grid-conflicts').textContent.includes('Second has 0 bedrooms'));
 check('Guide preflight identifies the empty floor before generation',await page.locator('#grid-conflicts').textContent().then(x=>x.includes('Second has 0 bedrooms')&&!x.includes('kitchen:')));
 check('Unsupported courtyard remains visible with a Custom Plan route',await page.locator('#grid-conflicts').textContent().then(x=>x.includes('Courtyard is available in Custom Plan')));
 await page.screenshot({path:out+'/guide-preflight.png'});await page.click('[data-close="grid-dialog"]');
 const rows=[['hall','hall','drawing-room','drawing-room'],['hall','hall','drawing-room','drawing-room'],['kitchen','kitchen','bedroom-1','bedroom-1'],['kitchen','kitchen','bedroom-1','bedroom-1']];
 await page.evaluate(p=>window.__ffApp.applyProject(p),{brief,grid:{mode:'spatial_hint',rows:4,cols:4,floorIds:['g'],floors:[rows]}});await page.click('#grid-open');await page.click('#grid-convert');await page.waitForSelector('#plan-dialog[open]');
 check('Cell conversion creates four editable rooms and keeps original board',await page.evaluate(()=>{const p=window.__ffApp.collect();return p.customPlan.floors[0].rooms.length===4&&p.editorState.guideFloors[0][0][2]==='drawing-room';}));
 await page.click('#plan-suggest-openings');await page.waitForFunction(()=>document.getElementById('plan-validation').textContent.startsWith('Geometry passes'),null,{timeout:60000});
 check('Suggested doors and windows produce a validated access graph',await page.evaluate(()=>window.__ffApp.planEditor.active.openings.length>=7));
 await page.screenshot({path:out+'/rooms-ready-to-generate.png'});await page.click('#plan-generate');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const state=await page.evaluate(()=>{const b=window.__ff.building,s=window.__ff.scene,r=window.__ff.report,room=b.spaces.find(r=>r.kind==='drawing-room');return {hash:b.planHash,sceneHash:s.planHash,reportHash:r.planHash,sofa:s.furniture.some(f=>f.kind==='sofa'&&f.room_id===room.id),id:window.__ff.buildId};});
 check('Converted drawing room reaches the 3D scene with sofa seating',state.sofa);
 check('Generated model, 3D and report share the draft hash',state.hash===state.sceneHash&&state.hash===state.reportHash);
 await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setMode('dollhouse');v.composer.render(0);});await page.screenshot({path:out+'/converted-plan-3d.png'});
 await page.click('#custom-open');await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/mobile-palette.png',fullPage:true});
 check('Mobile editor keeps every control in document width',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 check('No browser runtime errors',errors.length===0,errors);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();server.kill();}
