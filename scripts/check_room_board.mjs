import {spawn} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/room-board'),url='http://127.0.0.1:8891';mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8891','--out',mkdtempSync('/tmp/ff-board-')],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>process.stderr.write(d));
let browser;const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:180000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 await page.click('#custom-open');
 check('Design rooms opens the simple board with no dimension inputs',await page.locator('#room-board-dialog').isVisible()&&await page.locator('#room-board-dialog input[type=number]').count()===0&&!(await page.locator('#plan-dialog').isVisible()));
 await page.locator('.rb-palette summary').click();await page.click('#rb-example');await page.locator('.rb-palette summary').click();
 check('Drawing room is directly available',await page.locator('#rb-palette [data-add="drawing-room"]').isVisible());
 const snapshot=await page.evaluate(()=>JSON.stringify(window.__ffApp.roomBoard.board));
 await page.locator('#rb-board [data-slot="4"]').click();await page.locator('#rb-palette [data-add="bathroom"]').click();check('Tap an empty spot then a room adds it exactly there',await page.locator('#rb-board [data-slot="4"]').innerText().then(t=>t.includes('Bathroom')));await page.click('#rb-undo');
 await page.locator('#rb-board [data-slot="0"]').click();await page.locator('#rb-board [data-slot="1"]').click();
 check('Two taps swap rooms',await page.locator('#rb-board [data-slot="0"]').innerText().then(t=>t.includes('Drawing')));
 await page.click('#rb-undo');check('Undo restores the arrangement',await page.evaluate(()=>JSON.stringify(window.__ffApp.roomBoard.board))===snapshot);
 const a=await page.locator('#rb-board [data-slot="0"]').boundingBox(),b=await page.locator('#rb-board [data-slot="4"]').boundingBox();
 await page.mouse.move(a.x+a.width/2,a.y+a.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:8});await page.mouse.up();
 check('Drag moves a room into an empty spot',await page.locator('#rb-board [data-slot="4"]').innerText().then(t=>t.includes('Kitchen')));await page.click('#rb-undo');
 await page.locator('#rb-board [data-slot="2"]').click();await page.locator('#rb-board [data-slot="4"]').click();
 check('Moving stairs updates both floors',await page.evaluate(()=>window.__ffApp.roomBoard.board.floors.every(fl=>fl.rooms.find(r=>r.kind==='stair').row===2)));await page.click('#rb-undo');
 await page.screenshot({path:out+'/board-desktop.png'});
 await page.click('#rb-build');await page.waitForSelector('#rb-accept:not([hidden])',{timeout:30000});
 check('One action builds validated connected geometry',await page.evaluate(()=>window.__ffApp.roomBoard.pending?.valid===true));
 check('Preview does not replace the drawing before approval',await page.evaluate(()=>!window.__ffApp.planEditor.plan.floors[0].rooms.some(r=>r.kind==='drawing-room')));
 await page.screenshot({path:out+'/connected-preview.png'});
 await page.click('#rb-back');check('No keeps the arrangement unchanged',await page.evaluate(()=>JSON.stringify(window.__ffApp.roomBoard.board))===snapshot);
 await page.click('#rb-build');await page.waitForSelector('#rb-accept:not([hidden])');await page.click('#rb-accept');
 await page.waitForFunction(()=>!window.__ffApp.draftStale,null,{timeout:180000});
 check('Approval generates matching canonical 3D',await page.evaluate(()=>window.__ffApp.collect().customPlan.floors.length===2&&window.__ff.building.storeys===2&&!!window.__ff.building.rooftop));
 await page.evaluate(()=>{window.__ffApp.viewer.paused=false;window.__ffApp.viewer.dirty=true;});await page.waitForTimeout(1800);await page.screenshot({path:out+'/generated-home.png'});await page.click('[data-mode="dollhouse"]');await page.waitForTimeout(1000);await page.screenshot({path:out+'/generated-floor.png'});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 await page.click('#custom-open');await page.locator('#rb-floors [data-floor="1"]').click();await page.screenshot({path:out+'/upper-floor.png'});
 const saved=await page.evaluate(()=>JSON.stringify(window.__ffApp.collect()));await page.click('#rb-close');await page.evaluate(p=>window.__ffApp.applyProject(JSON.parse(p)),saved);
 // Compare explicitly; the saved board is independent of generated geometry.
 check('Saved spatial arrangement reopens unchanged',await page.evaluate(()=>JSON.stringify(window.__ffApp.collect().editorState.roomBoard))===JSON.stringify(JSON.parse(saved).editorState.roomBoard));
 await page.setViewportSize({width:390,height:844});await page.click('#custom-open');await page.screenshot({path:out+'/board-mobile.png'});
 check('Build action remains visible on a phone',await page.locator('#rb-build').isVisible()&&await page.locator('#rb-build').boundingBox().then(b=>b.y+b.height<=844));
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});const touch=await context.newPage();await touch.goto(url);await touch.waitForFunction(()=>window.__ffApp?.roomBoard,null,{timeout:180000});await touch.evaluate(()=>window.__ffApp.viewer.paused=true);await touch.locator('#custom-open').tap();await touch.locator('#rb-palette [data-add="bedroom"]').tap();check('Touch adds a room without entering measurements',await touch.locator('#rb-board [data-room]').count()>=2);await context.close();
 await page.click('#rb-close');await page.selectOption('#plan-mode','automatic');check('Automatic home-screen generation excludes the saved board geometry',await page.evaluate(()=>!window.__ffApp.collect().customPlan&&!window.__ffApp.collect().grid));
 check('No browser runtime errors',errors.length===0);
 writeFileSync(out+'/checks.json',JSON.stringify({checks,errors},null,2));
}finally{await browser?.close();server.kill('SIGINT');}
