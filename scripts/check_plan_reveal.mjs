// Browser check for the Plan Reveal samples inside the studio: their gallery cards, the walkthrough opening in the
// sample preview (scrollable, with its own overlay), scrolling into the lift, and adopting the sample as a project.
//   PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node scripts/check_plan_reveal.mjs
import {spawn} from 'node:child_process';
import {mkdirSync,mkdtempSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),url='http://127.0.0.1:8894',out=resolve(root,'evidence/plan-reveal');mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8894','--out',mkdtempSync('/tmp/ff-reveal-test-')],{cwd:root,stdio:['ignore','pipe','pipe']});server.stderr.on('data',d=>process.stderr.write(d));
let browser;const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 for(let i=0;i<100;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.viewer&&window.__ff?.ready,null,{timeout:300000});
 await page.click('[data-start="samples"]:not([disabled])');await page.waitForSelector('.sample-card');
 for(const id of ['aangan-house','long-house']){
  const card=page.locator(`.sample-card:has(button[data-sample="${id}"])`);
  check(`${id}: card offers the walkthrough`,(await card.locator('button.secondary').innerText()).includes('Walk in from the plan'));
  await card.scrollIntoViewIfNeeded();await card.locator('img').evaluate(i=>i.complete?null:new Promise(r=>{i.onload=i.onerror=r;}));
  check(`${id}: card shows a rendered thumbnail`,await card.locator('img').evaluate(i=>i.complete&&i.naturalWidth>=800));
 }
 await page.screenshot({path:out+'/gallery.png',timeout:180000});
 await page.locator('button.secondary[data-sample="aangan-house"]').click();
 await page.waitForFunction(()=>document.getElementById('sample-preview-frame').contentWindow?.__planReveal?.ready,null,{timeout:300000});
 const frame=page.frames().find(f=>f.url().endsWith('/reveal.html'));
 check('The walkthrough opens in the sample preview',!!frame);
 const layout=await frame.evaluate(()=>({scroll:document.documentElement.scrollHeight/innerHeight,bar:getComputedStyle(document.querySelector('header.bar')).display,lens:getComputedStyle(document.getElementById('lens')).display,chapter:window.__planReveal.state()?.chapter}));
 check('The preview keeps the walkthrough scrollable (its own layout, not the 3D preview overrides)',layout.scroll>20&&layout.bar!=='none'&&layout.lens!=='none');
 check('It opens on the sheet',layout.chapter==='sheet');
 await page.screenshot({path:out+'/preview-sheet.png',timeout:180000});
 await frame.evaluate(()=>{const d=window.__planReveal.director,max=document.documentElement.scrollHeight-innerHeight;scrollTo(0,(d.startOf('lift')+.9)/d.total*max);});
 await page.waitForFunction(()=>{const r=document.getElementById('sample-preview-frame').contentWindow.__planReveal;return r.state()?.chapter==='lift';},null,{timeout:120000});
 check('Scrolling the preview lifts the drawing into 3D',true);
 // Hold that frame (software WebGL renders slowly) for the screenshot.
 await frame.evaluate(()=>{const r=window.__planReveal;r.still(r.state().p);});
 await page.screenshot({path:out+'/preview-lift.png',timeout:180000});
 await page.click('#sample-preview-use');
 const adopted=await page.waitForFunction(()=>window.__ff?.buildId==='sample:aangan-house'&&!window.__ffApp.draftStale,null,{timeout:300000}).catch(()=>null);
 if(!adopted)console.log('Adoption status',await page.evaluate(()=>({build:window.__ff?.buildId,stale:window.__ffApp?.draftStale,message:document.getElementById('draft-state')?.textContent,toast:document.getElementById('toast')?.textContent})));
 check('Opening the project loads the matching editable custom plan',await page.evaluate(()=>window.__ffApp.collect().customPlan?.floors?.length===1&&window.__ff.building.brief.title==='The Aangan House'));
 await page.click('#sample-return');await page.waitForFunction(()=>document.getElementById('sample-return').hidden,null,{timeout:180000});
 check('No browser errors',errors.length===0);
 writeFileSync(out+'/checks.json',JSON.stringify({checks,errors},null,2));
}finally{await browser?.close();server.kill('SIGINT');}
