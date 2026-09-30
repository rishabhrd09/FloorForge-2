import {spawn} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {isDeepStrictEqual} from 'node:util';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),url='http://127.0.0.1:8893',out=resolve(root,'evidence/sample-gallery');mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8893','--out',mkdtempSync('/tmp/ff-gallery-test-')],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>process.stderr.write(d));
let browser;const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:180000});
 const before=await page.evaluate(()=>({draft:JSON.stringify(window.__ffApp.collect()),build:window.__ff.buildId}));
 await page.click('#sample-gallery-open');await page.waitForSelector('.sample-card');check('Six ready-made samples are visible',await page.locator('.sample-card').count()===6);
 await page.waitForFunction(()=>[...document.querySelectorAll('.sample-cover img')].every(i=>i.complete&&i.naturalWidth>0));check('All cards show actual rendered thumbnails',true);await page.screenshot({path:out+'/gallery-desktop.png'});
 await page.locator('button[data-sample="saved-verandah"]').last().click();const frame=page.frameLocator('#sample-preview-frame');await frame.locator('#view').waitFor({timeout:180000});
 await page.waitForFunction(()=>document.getElementById('sample-preview-frame').contentWindow.__ff?.ready,null,{timeout:180000});
 await frame.locator('[data-mode="dollhouse"]').click();await frame.locator('#floorBtn').click();
 check('Sample opens furnished 3D with floor switching',await frame.locator('#floorBtn').innerText()==='First floor');await page.screenshot({path:out+'/sample-dollhouse.png'});
 check('Browsing samples preserves the current project and model',await page.evaluate(before=>JSON.stringify(window.__ffApp.collect())===before.draft&&window.__ff.buildId===before.build,before));
 await page.click('#sample-preview-back');await page.waitForSelector('.sample-card');await page.locator('button[data-sample="quiet-studio"]').last().click();
 await page.click('#sample-preview-use');await page.waitForTimeout(1500);console.log('Adoption status',await page.evaluate(()=>({build:window.__ff?.buildId,message:document.getElementById('draft-state').textContent,toast:document.getElementById('toast')?.textContent})));await page.waitForFunction(()=>window.__ff?.buildId==='sample:quiet-studio'&&!window.__ffApp.draftStale,null,{timeout:30000}).catch(async e=>{console.log(await page.locator('body').innerText());throw e;});
 check('Use this sample loads matching editable project and generated model',await page.evaluate(()=>window.__ff.building.brief.title==='The Quiet Studio'&&window.__ffApp.collect().brief.title==='The Quiet Studio'));
 check('Previous project remains available',await page.locator('#sample-return').isVisible()&&await page.evaluate(()=>!!localStorage.getItem('floorforge-project-before-sample')));
 await page.reload();await page.waitForFunction(()=>window.__ffApp?.viewer&&document.getElementById('sample-return').hidden===false,null,{timeout:180000});
 check('Sample view and previous project recovery survive a refresh',await page.locator('#sample-return').isVisible()&&await page.evaluate(()=>window.__ff.buildId==='sample:quiet-studio'));
 await page.click('#sample-return');await page.waitForFunction(()=>document.getElementById('sample-return').hidden,null,{timeout:180000});
 const restored=await page.evaluate(()=>window.__ffApp.collect()),original=JSON.parse(before.draft);delete restored.draftRevision;delete original.draftRevision;
 check('Return restores prior settings and 3D',isDeepStrictEqual(restored,original)&&await page.evaluate(()=>window.__ff.buildId)===before.build);
 await page.setViewportSize({width:390,height:844});await page.click('#sample-gallery-open');await page.waitForSelector('.sample-card');await page.screenshot({path:out+'/gallery-mobile.png'});
 check('Gallery fits a phone without horizontal overflow',await page.locator('#sample-gallery-dialog').evaluate(el=>el.scrollWidth<=el.clientWidth+1));
 check('No browser errors',errors.length===0);writeFileSync(out+'/checks.json',JSON.stringify({checks,errors},null,2));
}finally{await browser?.close();server.kill('SIGINT');}
