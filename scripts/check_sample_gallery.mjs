// Browser check for the sample gallery: every catalogue home has a card with a rendered thumbnail, previews leave the
// current project untouched, an opened sample survives a refresh, and the previous project can be restored.
//   PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node scripts/check_sample_gallery.mjs
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
 const {samples}=await (await fetch(url+'/api/samples')).json();
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 // Software WebGL can hold a 3D frame for tens of seconds, and clicks and screenshots wait for frames.
 page.setDefaultTimeout(180000);
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:180000});
 const before=await page.evaluate(()=>({draft:JSON.stringify(window.__ffApp.collect()),build:window.__ff.buildId}));
 // The studio opens on its start page; the sidebar gallery button is only shown inside the workspace.
 await page.click('[data-start="samples"]:not([disabled])');await page.waitForSelector('.sample-card');
 check(`All ${samples.length} catalogue samples are visible`,isDeepStrictEqual(await page.locator('.sample-cover').evaluateAll(b=>b.map(x=>x.dataset.sample)),samples.map(s=>s.id)));
 // Thumbnails load lazily, so bring each card into view before checking its image.
 const blank=[];for(const {id} of samples){const card=page.locator(`.sample-card:has(button[data-sample="${id}"])`),img=card.locator('img');await card.scrollIntoViewIfNeeded();await img.evaluate(i=>i.complete?null:new Promise(r=>{i.onload=i.onerror=r;}));if(!await img.evaluate(i=>i.naturalWidth>0))blank.push(id);}
 if(blank.length)console.log('Cards without a thumbnail',blank);check('All cards show actual rendered thumbnails',!blank.length);
 await page.locator('#sample-gallery-dialog').evaluate(d=>d.scrollTop=0);await page.screenshot({path:out+'/gallery-desktop.png'});
 await page.locator('button[data-sample="saved-verandah"]').last().click();const frame=page.frameLocator('#sample-preview-frame');await frame.locator('#view').waitFor({timeout:180000});
 await page.waitForFunction(()=>document.getElementById('sample-preview-frame').contentWindow.__ff?.ready,null,{timeout:180000});
 await frame.locator('[data-mode="dollhouse"]').click();await frame.locator('#floorBtn').click();
 check('Sample opens furnished 3D with floor switching',await frame.locator('#floorBtn').innerText()==='First floor');await page.screenshot({path:out+'/sample-dollhouse.png'});
 check('Browsing samples preserves the current project and model',await page.evaluate(before=>JSON.stringify(window.__ffApp.collect())===before.draft&&window.__ff.buildId===before.build,before));
 await page.click('#sample-preview-back');await page.waitForSelector('.sample-card');await page.locator('button[data-sample="quiet-studio"]').last().click();
 await page.click('#sample-preview-use');await page.waitForTimeout(1500);console.log('Adoption status',await page.evaluate(()=>({build:window.__ff?.buildId,message:document.getElementById('draft-state').textContent,toast:document.getElementById('toast')?.textContent})));await page.waitForFunction(()=>window.__ff?.buildId==='sample:quiet-studio'&&!window.__ffApp.draftStale,null,{timeout:180000}).catch(async e=>{console.log(await page.locator('body').innerText());throw e;});
 check('Opening the sample loads matching editable project and generated model',await page.evaluate(()=>window.__ff.building.brief.title==='The Quiet Studio'&&window.__ffApp.collect().brief.title==='The Quiet Studio'));
 check('Previous project remains available',await page.locator('#sample-return').isVisible()&&await page.evaluate(()=>!!localStorage.getItem('floorforge-project-before-sample')));
 await page.reload();await page.waitForFunction(()=>window.__ffApp?.viewer&&document.getElementById('sample-return').hidden===false,null,{timeout:180000});
 // A refresh opens the start page again; Continue returns to the workspace and its return button.
 await page.click('[data-start="continue"]:not([disabled])');
 check('Sample view and previous project recovery survive a refresh',await page.locator('#sample-return').isVisible()&&await page.evaluate(()=>window.__ff.buildId==='sample:quiet-studio'));
 await page.click('#sample-return');await page.waitForFunction(()=>document.getElementById('sample-return').hidden,null,{timeout:180000});
 const restored=await page.evaluate(()=>window.__ffApp.collect()),original=JSON.parse(before.draft);delete restored.draftRevision;delete original.draftRevision;
 check('Return restores prior settings and 3D',isDeepStrictEqual(restored,original)&&await page.evaluate(()=>window.__ff.buildId)===before.build);
 await page.setViewportSize({width:390,height:844});await page.click('#sample-gallery-open');await page.waitForSelector('.sample-card');
 await page.waitForFunction(()=>{const d=document.getElementById('sample-gallery-dialog').getBoundingClientRect();return [...document.querySelectorAll('.sample-cover img')].every(i=>i.complete||i.getBoundingClientRect().top>=d.bottom);});await page.screenshot({path:out+'/gallery-mobile.png'});
 check('Gallery fits a phone without horizontal overflow',await page.locator('#sample-gallery-dialog').evaluate(el=>el.scrollWidth<=el.clientWidth+1));
 check('No browser errors',errors.length===0);writeFileSync(out+'/checks.json',JSON.stringify({checks,errors},null,2));
}finally{await browser?.close();server.kill('SIGINT');}
