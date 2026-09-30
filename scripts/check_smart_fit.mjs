import {spawn,execFileSync} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/smart-fit'),url='http://127.0.0.1:8885',builds=mkdtempSync('/tmp/ff-smart-fit-');mkdirSync(out,{recursive:true});
const rough=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c','import json;from tests.test_smart_fit import screenshot_sketch;print(json.dumps(screenshot_sketch()))'],{cwd:root}));
writeFileSync(out+'/rough.floorforge.json',JSON.stringify(rough,null,2)+'\n');
let server,browser;const checks=[],errors=[];
const check=(name,pass,data)=>{checks.push({name,pass:!!pass,data});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
async function start(){server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8885','--out',builds],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>process.stderr.write(d));for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)return;}catch{}await new Promise(r=>setTimeout(r,200));}throw Error('server start');}
async function stop(){await new Promise(resolve=>{server.once('exit',resolve);server.kill('SIGINT');});}
try{
 await start();browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1512,height:1050}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:240000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 const empty=structuredClone(rough);empty.customPlan.floors[0].rooms=[];await page.evaluate(p=>window.__ffApp.applyProject(p),empty);await page.click('#custom-open');
 const pt=await page.evaluate(()=>{const e=window.__ffApp.planEditor,[,d]=e.getEnvelope();return new DOMPoint(2600,d-2600).matrixTransform(e.svg.getScreenCTM()).toJSON();});
 await page.click('#plan-palette [data-kind="bedroom"]');await page.mouse.click(pt.x,pt.y);await page.click('#plan-palette [data-kind="living"]');await page.mouse.click(pt.x,pt.y);
 check('Rough overlapping placements are kept instead of rejected',await page.evaluate(()=>window.__ffApp.planEditor.active.rooms.length===2));
 check('No wall-gap error interrupts rough sketching',await page.locator('#plan-errors .plan-issue').count()===0);
 await page.click('[data-close="plan-dialog"]');await page.evaluate(p=>window.__ffApp.applyProject(p),rough);await page.click('#custom-open');
 const before=await page.evaluate(()=>window.__ffApp.planEditor.snapshot());
 await page.click('#plan-assist');await page.waitForSelector('#plan-fit-choice:not([hidden])');
 check('Fitting proposes changes without modifying the sketch',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);
 check('Proposed room dimensions and dashed outlines are reviewable',await page.locator('#plan-fit-changes li').count()>=8&&await page.locator('.plan-fit-outline').count()===8);
 await page.locator('#plan-fit-choice details').evaluate(e=>e.open=true);await page.screenshot({path:out+'/fit-proposal-desktop.png'});
 await page.click('#plan-fit-no');check('No preserves every room and opening',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);
 await page.click('#plan-assist');await page.waitForSelector('#plan-fit-choice:not([hidden])');await page.setViewportSize({width:390,height:844});
 check('Yes and No fit on a phone',await page.locator('#plan-fit-yes').evaluate(e=>{const r=e.getBoundingClientRect();return r.right<=innerWidth&&r.bottom<=innerHeight&&r.top>=0;})&&await page.locator('#plan-fit-no').evaluate(e=>{const r=e.getBoundingClientRect();return r.right<=innerWidth&&r.bottom<=innerHeight&&r.top>=0;}));await page.screenshot({path:out+'/fit-proposal-mobile.png'});await page.setViewportSize({width:1512,height:1050});
 await page.click('#plan-fit-yes');const fitted=await page.evaluate(()=>window.__ffApp.collect());
 check('Yes fixes small rooms, stair dimensions and openings',await page.locator('#plan-errors .plan-issue').count()===0&&fitted.customPlan.floors[0].openings.length>=12);
 check('All eight rooms and their floor assignments survive',fitted.customPlan.floors.length===1&&fitted.customPlan.floors[0].rooms.map(r=>r.id).sort().join()===rough.customPlan.floors[0].rooms.map(r=>r.id).sort().join());
 await page.click('#plan-undo');check('One Undo restores the entire rough sketch',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);await page.click('#plan-redo');
 await page.click('#plan-detail');check('Manual walls remain available in Fine-tune',await page.locator('#plan-wall').isVisible());await page.click('#plan-arrange');
 // A proposal must never overwrite a later edit, including an unfinished typed dimension.
 await page.click('#plan-assist');await page.waitForSelector('#plan-fit-choice:not([hidden])');await page.locator('#plan-room-list button').filter({hasText:'Master'}).click();await page.fill('#plan-width','4.23');await page.click('#plan-fit-yes');
 check('Approval of an outdated proposal preserves newly typed dimensions',await page.locator('#plan-width').inputValue()==='4.23'&&await page.locator('#plan-fit-choice').isHidden());
 await page.click('[data-close="plan-dialog"]');await page.evaluate(p=>window.__ffApp.applyProject(p),rough);await page.click('#custom-open');
 // Reproduce the screenshot's exact cause: leave the browser open through a server restart.
 await stop();await start();let rejected=0;page.on('response',r=>{if(r.status()===403)rejected++;});
 await page.click('#plan-generate');await page.waitForSelector('#plan-fit-choice:not([hidden])');
 check('An old browser session automatically reconnects after server restart',rejected===1);
 check('Reconnect and proposal preserve the draft',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);
 await page.click('#plan-fit-yes');await page.waitForFunction(()=>!document.getElementById('generate').disabled&&!window.__ffApp.draftStale,null,{timeout:240000});
 const generated=await page.evaluate(()=>({project:window.__ffApp.collect(),building:window.__ff.building,scene:window.__ff.scene}));
 check('Accepted fit generates the matching eight-room building and 3D',generated.building.spaces.length===8&&generated.building.planHash===generated.scene.planHash);
 check('Stair reaches the roof without adding an occupied floor',generated.building.storeys===1&&generated.scene.roof_level===1&&generated.building.stairs.some(s=>s.roof_access));
 const session=await (await fetch(url+'/api/session')).json();const intent=await (await fetch(url+'/api/intent',{method:'POST',headers:{'Content-Type':'application/json','X-FloorForge-Token':session.token},body:JSON.stringify(generated.project)})).json();
 check('Saved fitted project reopens with the generated plan hash',intent.planHash===generated.scene.planHash);
 writeFileSync(out+'/fitted.floorforge.json',JSON.stringify(generated.project,null,2)+'\n');await page.evaluate(()=>{const v=window.__ffApp.viewer;v.paused=true;v.setMode('dollhouse');v.setFloor(0);v.composer.render(0);});await page.screenshot({path:out+'/fitted-3d.png'});
 check('No browser runtime errors',errors.length===0,errors);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();if(server?.exitCode===null)server.kill('SIGINT');}
