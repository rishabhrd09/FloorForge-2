import {spawn} from 'node:child_process';
import {mkdtempSync, mkdirSync, writeFileSync, readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),url='http://127.0.0.1:8894';
const out=resolve(process.env.EVIDENCE_DIR||'/tmp/floorforge-import-browser');mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8894','--out',mkdtempSync('/tmp/ff-dxf-')],{cwd:root,stdio:['ignore','ignore','pipe']});
server.stderr.on('data',d=>process.stderr.write(d));
let browser;const errors=[],checks=[];
const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:960}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:180000});
 await page.waitForFunction(()=>!document.querySelector('[data-start="continue"]').disabled);
 await page.click('[data-start="continue"]');
 const before=await page.evaluate(()=>JSON.stringify(window.__ffApp.collect()));
 await page.click('#import-plan-open');
 await page.locator('#import-plan-file').setInputFiles({name:'bad.dxf',mimeType:'application/dxf',buffer:Buffer.from('bad drawing')});
 await page.waitForFunction(()=>document.getElementById('import-plan-result').textContent.includes('Cannot read'));
 check('Malformed upload leaves the current draft unchanged',before===await page.evaluate(()=>JSON.stringify(window.__ffApp.collect())));
 const submitted=[];page.on('request',r=>{if(r.url().endsWith('/api/generate'))submitted.push(r.postDataJSON());});
 await page.locator('#import-plan-file').setInputFiles(resolve(root,'examples/import/ground-floor.dxf'));
 await page.waitForFunction(()=>window.__ffApp.collect().brief.title==='ground-floor'&&!window.__ffApp.draftStale&&!document.getElementById('generate').disabled,null,{timeout:180000});
 check('One file automatically generates the exact custom plan',submitted.length===1&&submitted[0].customPlan.floors[0].rooms.length===4&&!submitted[0].grid);
 check('Uploaded dimensions and opening widths are preserved',submitted[0].customPlan.floors[0].rooms[0].polygon[1][0]===4150&&submitted[0].customPlan.floors[0].openings[0].width===1000);
 check('Import stays on one floor without automatic roof stairs',submitted[0].brief.storeys===1&&!submitted[0].brief.roof_access);
 check('Previous draft is saved',await page.evaluate(()=>!!localStorage.getItem('floorforge-draft-before-dxf-import')));
 await page.screenshot({path:out+'/generated-3d.png'});
 await page.click('#import-plan-open');
 check('Persistent report discloses height assumptions',await page.locator('#import-plan-result').innerText().then(t=>t.includes('3150 mm')));
 // Remove the entry by moving its layer to a normal annotation layer.
 const invalid=readFileSync(resolve(root,'examples/import/ground-floor.dxf'),'utf8').replaceAll('FF_ENTRY','ANNOTATION');
 const oldCount=submitted.length;
 await page.locator('#import-plan-file').setInputFiles({name:'missing-entry.dxf',mimeType:'application/dxf',buffer:Buffer.from(invalid)});
 await page.waitForFunction(()=>document.getElementById('import-plan-result').textContent.includes('3D generation is blocked'));
 check('Invalid access is editable and does not generate a substitute',submitted.length===oldCount&&await page.evaluate(()=>window.__ffApp.draftStale));
 await page.getByRole('button',{name:'Review imported plan'}).click();
 check('Repair opens the exact plan editor',await page.locator('#plan-dialog').evaluate(e=>e.open&&e.dataset.detail==='true'));
 await page.screenshot({path:out+'/repair-plan.png'});
 await page.locator('[data-close="plan-dialog"]').click();await page.setViewportSize({width:390,height:844});await page.click('#import-plan-open');
 check('Import dialog fits a phone screen',await page.locator('#import-plan-dialog').evaluate(e=>e.getBoundingClientRect().width<=window.innerWidth&&e.scrollWidth<=e.clientWidth));
 await page.screenshot({path:out+'/mobile-import.png'});
 check('No browser runtime errors',errors.length===0);
}finally{writeFileSync(out+'/checks.json',JSON.stringify({checks,errors},null,2)+'\n');if(browser)await browser.close();server.kill('SIGINT');}
