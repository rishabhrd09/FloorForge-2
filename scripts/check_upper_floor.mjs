import {spawn} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'evidence/upper-floor'),url='http://127.0.0.1:8887';mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8887','--out',mkdtempSync('/tmp/ff-upper-')],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>process.stderr.write(d));
let browser;const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:180000});await page.evaluate(()=>window.__ffApp.viewer.paused=true);
 await page.click('#custom-open');await page.click('#plan-sketch-example');await page.waitForFunction(()=>window.__ff?.buildId==='your-sketch'&&!window.__ffApp.draftStale,null,{timeout:180000});
 check('One click loads the matching sample model and editable ground plan',await page.evaluate(()=>window.__ffApp.planEditor.plan.floors[0].rooms.length===8&&window.__ff.building.storeys===2&&!!window.__ff.building.rooftop));
 check('Sample keeps drawing room and veranda on Ground',await page.evaluate(()=>['drawing-room','veranda'].every(k=>window.__ffApp.planEditor.plan.floors[0].rooms.some(r=>r.kind===k))));
 await page.screenshot({path:out+'/ground-example.png'});
 await page.locator('#plan-floor-tabs button').nth(1).click();await page.waitForSelector('.upper-support');
 check('First floor shows footprint and aligned stair overlays before validation',await page.locator('.upper-stair-guide').count()===1&&await page.locator('#plan-upper-help').isVisible());
 const before=await page.evaluate(()=>window.__ffApp.planEditor.snapshot()),lower=await page.evaluate(()=>JSON.stringify(window.__ffApp.planEditor.plan.floors[0]));
 await page.click('#plan-upper-suggest');await page.waitForSelector('#plan-fit-choice:not([hidden])');
 check('Upper suggestion is a preview and leaves the draft unchanged',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);
 await page.click('#plan-fit-no');check('No keeps both floors unchanged',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);
 await page.click('#plan-upper-suggest');await page.waitForSelector('#plan-fit-choice:not([hidden])');await page.click('#plan-fit-yes');
 check('Yes adapts only the upper floor',await page.evaluate(()=>JSON.stringify(window.__ffApp.planEditor.plan.floors[0]))===lower);
 await page.click('#plan-undo');check('One Undo restores the original upper design',await page.evaluate(()=>window.__ffApp.planEditor.snapshot())===before);
 await page.waitForSelector('.upper-support');await page.screenshot({path:out+'/first-guidance.png'});
 // Check real rough placement in the inherited core selects rather than duplicates.
 const n=await page.evaluate(()=>window.__ffApp.planEditor.active.rooms.length);
 await page.evaluate(()=>{const ed=window.__ffApp.planEditor,r=ed.active.rooms.find(r=>r.kind==='stair'),[x,y,x1,y1]=ed.bounds(r);ed.chooseRoom('stair');ed.placeRoom([(x+x1)/2,(y+y1)/2]);});
 check('Dropping a second stair onto the inherited stair reuses it',await page.evaluate(()=>window.__ffApp.planEditor.active.rooms.length)===n);
 await page.evaluate(()=>{const ed=window.__ffApp.planEditor,r=ed.active.rooms.find(r=>r.kind==='bedroom');ed.change(()=>{r.polygon=r.polygon.map(([x,y])=>[x+6000,y]);});});
 await page.waitForFunction(()=>document.getElementById('plan-upper-issues').textContent.includes('extends beyond'));
 check('Unsupported upper room is named while drawing',await page.locator('#plan-upper-issues').innerText().then(t=>t.includes('shaded area')));
 await page.click('#plan-undo');await page.click('[data-close="plan-dialog"]');
 await page.click('#grid-open');check('Sample includes separate fixed cell guides for both floors',await page.locator('#grid-board button').count()===16&&await page.locator('#grid-floor-tabs button').count()===2);await page.screenshot({path:out+'/cell-guide.png'});await page.click('[data-close="grid-dialog"]');
 await page.click('[data-mode="dollhouse"]');await page.selectOption('#floor','1');await page.evaluate(()=>{window.__ffApp.viewer.paused=false;window.__ffApp.viewer.dirty=true;});await page.waitForTimeout(1000);await page.screenshot({path:out+'/first-3d.png'});
 check('Dollhouse shows sample first floor from the same building',await page.evaluate(()=>window.__ffApp.viewer.floor===1&&window.__ff.building.planHash===window.__ff.scene.planHash));
 await page.click('[data-mode="solid"]');await page.click('[data-view="hero"]');await page.waitForTimeout(1000);await page.screenshot({path:out+'/exterior.png'});
 // Reopen the untouched sample before testing generation; no stale fixture injection.
 await page.click('#custom-open');await page.click('#plan-sketch-example');await page.waitForFunction(()=>!window.__ffApp.draftStale);await page.click('#plan-generate');await page.waitForSelector('#plan-fit-choice:not([hidden])');await page.click('#plan-fit-yes');
 await page.waitForFunction(()=>!window.__ffApp.draftStale&&!document.getElementById('generate').disabled&&!document.getElementById('plan-dialog').open,null,{timeout:240000});
 check('Sample regenerates through the real editor with matching export hashes',await page.evaluate(()=>window.__ff.buildId!=='your-sketch'&&window.__ff.scene.planHash===window.__ff.building.planHash));
 check('No browser runtime errors',!errors.length);
}finally{writeFileSync(out+'/browser-acceptance.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();server.kill('SIGINT');}
