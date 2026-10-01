// Isolated preview check: never changes the user's live browser storage.
import {writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const results=[];const check=(name,ok)=>{results.push({name,pass:!!ok});if(!ok)throw Error(name);console.log('PASS',name);};
try {
 const p=await browser.newPage({viewport:{width:1400,height:900}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
 const ready=()=>p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
 await p.goto(process.env.PREVIEW_URL||'http://127.0.0.1:8765/samples/my-desired-home/preview.html');await ready();
 check('Preview offers one-click Hide car',await p.locator('#carBtn').innerText()==='Hide car');
 await p.locator('#carBtn').click();
 check('Preview hides all car surfaces and collision',await p.evaluate(()=>{const v=__ff.viewer;return !v.carVisible&&v.vehicle.meshes.every(m=>!m.visible)&&v.walker.optionalBVHs.length===0;}));
 await p.reload();await ready();
 check('Hidden preference survives refresh',await p.locator('#carBtn').innerText()==='Show car'&&await p.evaluate(()=>!__ff.viewer.carVisible));
 await p.locator('[data-mode="dollhouse"]').click();
 check('View switching keeps the car hidden',await p.evaluate(()=>__ff.viewer.vehicle.meshes.every(m=>!m.visible)));
 await p.locator('[data-mode="walk"]').click();
 await p.evaluate(()=>{const v=__ff.viewer;v.paused=true;v.walker.teleport(v.walker.position.clone().set(17.03,-.41,-2.6));});
 await p.locator('#carBtn').click();
 check('Showing car is blocked while standing in its space',await p.evaluate(()=>!__ff.viewer.carVisible));
 await p.evaluate(()=>{const v=__ff.viewer;v.walker.teleport(v.walker.position.clone().set(15.6,-.41,-2.6));});
 await p.locator('#carBtn').click();
 check('Showing car restores geometry and collision',await p.evaluate(()=>__ff.viewer.carVisible&&__ff.viewer.walker.optionalBVHs.length===1));
 await p.reload();await ready();
 check('Visible preference survives refresh',await p.evaluate(()=>__ff.viewer.carVisible));
 await p.evaluate(()=>{const v=__ff.viewer;v.setMode('solid');v.fitHeld=null;v.zoomAnim=null;v.camera.fov=58;v.camera.updateProjectionMatrix();v.camera.position.set(15.6,1.25,.9);v.controls.target.set(17,.45,-2.6);v.controls.update();v.dirty=true;});
 await p.waitForTimeout(700);await p.screenshot({path:resolve('evidence/desired-home/kylaq-toggle.png')});
 check('No browser errors',errors.length===0);
 writeFileSync(resolve('evidence/desired-home/car-toggle-checks.json'),JSON.stringify({checks:results},null,2));
} finally {await browser.close();}
