import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),url='http://127.0.0.1:8896',out='/tmp/floorforge-plan-assistance';mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8896','--out',mkdtempSync('/tmp/ff-plan-search-')],{cwd:root,stdio:['ignore','ignore','pipe']});server.stderr.on('data',d=>process.stderr.write(d));
const checks=[],errors=[];let browser;
function check(name,ok){checks.push({name,pass:!!ok});console.log(ok?'PASS':'FAIL',name);if(!ok)throw Error(name);}
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.planEditor,null,{timeout:180000});
 await page.waitForFunction(()=>!document.querySelector('[data-start="continue"]').disabled);
 await page.click('[data-start="continue"]');
 const fixture=JSON.parse(readFileSync(resolve(root,'tests/fixtures/crowded-room-sketch.json'),'utf8'));
 await page.evaluate(async p=>{await window.__ffApp.applyProject(p);document.getElementById('plan-dialog').showModal();window.__ffApp.planEditor.render();},fixture);
 const snapshot=()=>page.evaluate(()=>window.__ffApp.planEditor.snapshot()),before=await snapshot();
 await page.click('#plan-explore');await page.click('#plan-help-search');await page.waitForSelector('.plan-help-option');
 check('Python finds three alternatives without an AI request',await page.locator('.plan-help-option').count()===3);
 check('Searching preserves the original draft',await snapshot()===before);
 await page.screenshot({path:out+'/alternatives.png'});
 await page.locator('.plan-help-option button').first().click();
 check('Review shows a proposal without applying it',await snapshot()===before&&await page.locator('#plan-fit-choice').isVisible());
 await page.click('#plan-fit-no');check('Declining retains the sketch',await snapshot()===before);
 await page.click('#plan-explore');await page.getByText('Keep rooms fixed',{exact:true}).click();await page.locator('#plan-help-locks input[value="living"]').check();await page.click('#plan-help-search');
 await page.waitForFunction(()=>document.getElementById('plan-help-status').textContent.includes('fixed rooms'));
 check('Locked rooms stop broad rearrangement',await page.locator('.plan-help-option').count()===0&&await snapshot()===before);
 await page.locator('#plan-help-locks input[value="living"]').uncheck();await page.click('#plan-help-search');await page.waitForSelector('.plan-help-option');await page.locator('.plan-help-option button').first().click();await page.click('#plan-fit-yes');
 check('Only Yes applies the selected plan',await snapshot()!==before);
 await page.click('#plan-undo');check('Undo restores every room exactly',await snapshot()===before);
 // Request changes invalidate an in-flight result, including after closing/reopening.
 let release;await page.route('**/api/plan/alternatives',async route=>{await new Promise(r=>release=r);await route.fulfill({json:{message:'stale result',alternatives:[]}});});
 await page.click('#plan-explore');await page.click('#plan-help-search');await page.waitForTimeout(100);await page.locator('#plan-help-local summary').click();await page.fill('#plan-help-instruction','A newer request');release();await page.waitForFunction(()=>!document.getElementById('plan-help-search').disabled);
 check('Changed request rejects stale results',await page.locator('#plan-help-status').innerText().then(t=>t.includes('changed')));
 await page.unroute('**/api/plan/alternatives');
 // Offline failure is recoverable and does not affect the deterministic workflow.
 await page.route('**/api/local-plan/propose',route=>route.fulfill({status:422,json:{error:'Local Ollama request failed. The Python planner remains available.'}}));
 await page.locator('#plan-help-scale').check();await page.click('#plan-help-ask');await page.waitForFunction(()=>document.getElementById('plan-help-status').textContent.includes('Ollama request failed'));
 check('Unavailable local model leaves the sketch untouched',await snapshot()===before);
 await page.click('#plan-help-search');await page.waitForSelector('.plan-help-option');check('Python still works after local-model failure',await page.locator('.plan-help-option').count()===3);
 await page.setViewportSize({width:390,height:844});check('Proposal dialog fits mobile width',await page.locator('#plan-help-dialog').evaluate(e=>e.getBoundingClientRect().width<=innerWidth&&e.scrollWidth<=e.clientWidth));await page.screenshot({path:out+'/mobile.png'});
 await page.setViewportSize({width:1440,height:1000});await page.locator('.plan-help-option button').first().click();await page.click('#plan-fit-yes');
 await page.click('#plan-generate');await page.waitForSelector('#plan-fit-choice:not([hidden])');await page.click('#plan-fit-yes');
 await page.waitForFunction(()=>!window.__ffApp.draftStale&&!document.getElementById('generate').disabled,null,{timeout:180000});
 check('Accepted alternative generates a matching 3D project',await page.evaluate(()=>window.__ffApp.collect().customPlan.floors[0].rooms.length===10));
 await page.screenshot({path:out+'/generated-3d.png'});
 check('No browser exceptions',errors.length===0);
}finally{writeFileSync(out+'/checks.json',JSON.stringify({checks,errors},null,2));if(browser)await browser.close();server.kill('SIGINT');}
