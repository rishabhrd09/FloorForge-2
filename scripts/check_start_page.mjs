import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),url='http://127.0.0.1:8901',out='/tmp/floorforge-start-page';mkdirSync(out,{recursive:true});
const server=spawn(resolve(root,'.venv/bin/python'),['-m','floorforge','serve','--no-browser','--port','8901','--out',mkdtempSync('/tmp/ff-start-')],{cwd:root,stdio:['ignore','ignore','pipe']});server.stderr.on('data',d=>process.stderr.write(d));
let browser;const checks=[],errors=[];function check(name,ok){checks.push({name,pass:!!ok});console.log(ok?'PASS':'FAIL',name);if(!ok)throw Error(name);}
try{
 for(let i=0;i<150;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const page=await browser.newPage({viewport:{width:1440,height:1100}});page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.waitForFunction(()=>!document.querySelector('[data-start="new"]').disabled,null,{timeout:180000});
 check('Six choices and studio hidden on arrival',await page.locator('[data-start]').count()===6&&await page.locator('.workspace').isHidden());
 check('Real sample cover loaded',await page.locator('.start-hero-image img').evaluate(i=>i.complete&&i.naturalWidth>0));
 await page.waitForFunction(()=>document.querySelector('.start-hero').dataset.garden==='three');
 check('User-selected Verandah image is used',await page.locator('.start-hero-image img').getAttribute('src')==='/assets/myverandah-hero.png');
 check('Hero spans viewport width',await page.locator('.start-hero').evaluate(el=>Math.abs(el.getBoundingClientRect().width-innerWidth)<2));
 await page.waitForTimeout(2200);await page.mouse.move(1100,250);await page.waitForTimeout(500);
 check('GSAP pointer animation moves the image',await page.locator('.start-hero-image').evaluate(el=>getComputedStyle(el).transform!=='none'));
 await page.click('#hero-motion');check('Motion can be paused',await page.locator('.start-hero').getAttribute('data-motion')==='paused');await page.click('#hero-motion');
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForFunction(()=>document.getElementById('hero-motion').disabled);check('Reduced motion is respected',await page.locator('#hero-motion').isDisabled());await page.emulateMedia({reducedMotion:'no-preference'});
 await page.screenshot({path:out+'/desktop.png',fullPage:true});
 const original=await page.evaluate(()=>window.__ffApp.collect());
 await page.click('[data-start="new"]');await page.click('#start-setup-close');
 check('Cancel setup retains draft',JSON.stringify(original)===JSON.stringify(await page.evaluate(()=>window.__ffApp.collect())));
 await page.click('[data-start="samples"]');await page.waitForSelector('.sample-card');await page.click('.sample-cover >> nth=0');await page.waitForSelector('#sample-preview-dialog[open]');await page.click('#sample-preview-close');
 check('Browsing samples retains draft and returns to start',JSON.stringify(original)===JSON.stringify(await page.evaluate(()=>window.__ffApp.collect()))&&await page.locator('#start-page').isVisible());
 await page.click('[data-start="new"]');await page.fill('#start-name','Courtyard test home');await page.fill('#start-width','36');await page.fill('#start-depth','50');await page.click('#start-launch');await page.waitForSelector('#journey-guide:visible');
 const project=await page.evaluate(()=>window.__ffApp.collect());
 check('New no-AI brief uses requested dimensions',project.brief.title==='Courtyard test home'&&project.brief.width_mm===10973&&project.brief.depth_mm===15240);
 check('Previous work saved separately',await page.evaluate(title=>Object.values(JSON.parse(localStorage.getItem('floorforge-saved-projects'))).some(s=>s.project.brief.title===title),original.brief.title));
 await page.click('#start-home');await page.click('[data-start="saved"]');
 check('Saved projects available from start',await page.locator('.start-saved-item').count()>=2);await page.click('#start-saved-close');
 await page.click('[data-start="continue"]');check('Hero animation stops in workspace',await page.locator('.start-hero').getAttribute('data-motion')==='paused');check('Continue keeps new draft',await page.evaluate(()=>window.__ffApp.collect().brief.title)==='Courtyard test home');
 await page.reload();await page.waitForFunction(()=>!document.querySelector('[data-start="new"]').disabled,null,{timeout:180000});
 check('Reload starts at home and preserves new draft',await page.locator('#start-page').isVisible()&&await page.evaluate(()=>window.__ffApp.collect().brief.title)==='Courtyard test home');
 await page.click('[data-start="import"]');check('Import entry selects DXF',await page.inputValue('#start-source')==='dxf');await page.click('#start-launch');await page.waitForSelector('#import-plan-dialog[open]');check('DXF path opens existing importer',true);await page.evaluate(()=>document.getElementById('import-plan-dialog').close());
 await page.click('#start-home');await page.click('[data-start="new"]');await page.selectOption('#start-source','sketch');await page.check('#start-local');await page.click('#start-launch');await page.waitForSelector('#journey-guide:visible');await page.click('#journey-action');await page.waitForSelector('#plan-help-dialog[open]');
 check('Sketch choice routes to local assistant without sending request',await page.locator('#plan-help-results').textContent()==='');await page.evaluate(()=>document.querySelectorAll('dialog[open]').forEach(d=>d.close()));
 await page.click('#start-home');await page.click('[data-start="customize"]');await page.waitForSelector('.sample-card');check('Adapt sample entry offers editable copy',await page.locator('.sample-card').first().textContent().then(t=>t.includes('Preview & adapt')));await page.click('.sample-cover >> nth=0');await page.click('#sample-preview-use');await page.waitForSelector('#sample-preview-dialog',{state:'hidden',timeout:120000});check('Adapting opens workspace with live 3D viewer',await page.locator('.workspace').isVisible()&&await page.evaluate(()=>window.__ffApp.viewer.paused===false));await page.click('#start-home');await page.click('[data-start="saved"]');await page.locator('.start-saved-item').filter({hasText:'Courtyard test home'}).click();await page.waitForSelector('#start-saved',{state:'hidden'});check('Saved draft can be reopened after adapting a sample',await page.evaluate(()=>window.__ffApp.collect().brief.title)==='Courtyard test home');await page.click('#start-home');
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:out+'/mobile.png',fullPage:true});
 check('Mobile page has no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.click('[data-start="new"]');await page.screenshot({path:out+'/mobile-setup.png',fullPage:true});check('Setup fits mobile viewport',await page.locator('#start-setup').evaluate(d=>d.getBoundingClientRect().width<=innerWidth));
 check('No browser exceptions',errors.length===0);
}finally{writeFileSync(out+'/checks.json',JSON.stringify({checks,errors},null,2));await browser?.close();server.kill('SIGTERM');}
