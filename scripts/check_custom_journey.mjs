/* Real-browser evidence for the deterministic custom-home approval journey. */
import {spawn} from 'node:child_process';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {tmpdir} from 'node:os';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=resolve(import.meta.dirname,'..'),port=Number(process.env.MYVERANDAH_TEST_PORT||8910),url=`http://127.0.0.1:${port}`;
const out=resolve(root,'evidence/custom-journey'),work=mkdtempSync(join(tmpdir(),'myverandah-browser-'));mkdirSync(out,{recursive:true});
const python=process.env.FLOORFORGE_PYTHON||resolve(root,'.venv/bin/python');
const server=spawn(python,['-m','floorforge','serve','--no-browser','--port',String(port),'--out',work],{cwd:root,stdio:['ignore','ignore','pipe']});
let serverErrors='';server.stderr.on('data',chunk=>serverErrors+=chunk.toString());
const checks=[],errors=[],timings={};let browser,page,jobPosts=0;
function check(name,pass,detail){checks.push({name,pass:!!pass,...(detail?{detail}:{})});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);}
const since=()=>performance.now();
try{
 for(let i=0;i<150;i++){try{if((await fetch(url+'/api/session')).ok)break;}catch{}await new Promise(r=>setTimeout(r,200));}
 browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().endsWith('/api/generate')&&r.method()==='POST')jobPosts++;});
 await page.goto(url);await page.waitForFunction(()=>window.__ffApp?.designJourney,null,{timeout:180000});
 check('Journey starts locally without an AI provider',await page.evaluate(()=>document.getElementById('ai-state').textContent.includes('Off')));
 await page.click('[data-start="new"]');check('Six combinable starting inputs are visible',await page.locator('[data-home-input]').count()===6);
 await page.click('[data-home-input="compass"]');await page.click('[data-home-input="survey"]');await page.fill('#start-name','Novice journey browser trial');await page.click('#start-launch');
 await page.waitForSelector('.workspace:visible');check('Nine ordered journey stages are keyboard buttons',await page.locator('[data-journey-step]').count()===9);
 await page.screenshot({path:out+'/browser-inputs-desktop.png',fullPage:true});
 // Use a real portable multi-floor project through the upload control, not an injected compiled model.
 const project=JSON.parse(readFileSync(resolve(root,'examples/custom/g2-terrace.floorforge.json'),'utf8'));
 project.brief.road_bearing_deg??=180;project.brief.title='MyVerandah three-floor approval trial';project.editorState={...(project.editorState||{}),mode:'custom',homeInputs:['plot','dxf']};project.designJourney={schema:'myverandah.journey/1',projectId:'browser-trial',enabledInputs:['plot','dxf'],answers:{},approvals:{},appearance:{preset:'warm-natural'}};
 const input=resolve(work,'three-floors.floorforge.json');writeFileSync(input,JSON.stringify(project));await page.setInputFiles('#project-file',input);
 await page.waitForFunction(()=>window.__ffApp.collect().brief.title==='MyVerandah three-floor approval trial');
 const prepareStarted=since();await page.click('#generate');await page.waitForSelector('#myv-approve-floor',{timeout:180000});timings.prepareSeconds=+( (since()-prepareStarted)/1000).toFixed(3);
 check('All three requested floor drawings publish before 3D',await page.locator('[data-review-floor]').count()===3&&jobPosts===0);
 const beforeGeometry=await page.evaluate(()=>window.__ffApp.designJourney.state.geometryHash);check('2D review dialog fills the actual viewport',await page.locator('#design-journey-dialog').evaluate(d=>Math.abs(d.getBoundingClientRect().top)<1&&Math.abs(d.getBoundingClientRect().height-innerHeight)<1));check('Dimensioned floor image is loaded',await page.locator('.myv-floor-plan').evaluate(i=>i.complete&&i.naturalWidth>0));
 await page.screenshot({path:out+'/browser-2d-ground-desktop.png'});
 for(let i=0;i<3;i++){await page.click('#myv-approve-floor');await page.waitForFunction(n=>Object.keys(window.__ffApp.designJourney.state.approvals).length===n,i+1,{timeout:30000});}
 check('Each requested floor has its own signed approval',await page.evaluate(()=>Object.values(window.__ffApp.designJourney.state.approvals).every(a=>a.signature&&a.geometryHash)));
 await page.click('#myv-whole-home');await page.screenshot({path:out+'/browser-whole-home.png'});await page.click('#myv-confirm-home');await page.waitForSelector('[data-my-preset]');
 check('Three compatible appearance presets follow whole-home confirmation',await page.locator('[data-my-preset]').count()===3&&jobPosts===0);
 const signed=await page.evaluate(()=>JSON.stringify(window.__ffApp.designJourney.state.confirmation));await page.click('[data-my-preset="quiet-modern"]');await page.waitForSelector('#myv-generate-approved',{timeout:180000});
 check('Style-only selection retains exact geometry and signed approval',await page.evaluate(({hash,cert})=>window.__ffApp.designJourney.state.geometryHash===hash&&JSON.stringify(window.__ffApp.designJourney.state.confirmation)===cert,{hash:beforeGeometry,cert:signed}));
 if(await page.locator('[data-appearance-component="furniture"]').count()){await page.selectOption('[data-appearance-component="furniture"]','sage');await page.waitForSelector('#myv-generate-approved',{timeout:180000});check('Modular furniture materials retain geometry approval',await page.evaluate(hash=>window.__ffApp.designJourney.state.geometryHash===hash&&!!window.__ffApp.designJourney.state.confirmation,beforeGeometry));}await page.screenshot({path:out+'/browser-appearance-desktop.png'});
 const started=since();await page.click('#myv-generate-approved');await page.waitForFunction(()=>window.__ffApp.draftStale===false,null,{timeout:300000});timings.generateSeconds=+((since()-started)/1000).toFixed(3);
 check('Approved home generates exactly one matching interactive scene',jobPosts===1&&await page.evaluate(()=>window.__ffApp.viewer.sceneData?.storeys===3||document.getElementById('floor').options.length>=3));
 await page.screenshot({path:out+'/browser-generated-3d.png',fullPage:true});
 // Persist real reference bytes through the browser file picker, save and upload.
 const image=resolve(work,'reference.png');await page.screenshot({path:image,clip:{x:0,y:0,width:128,height:128}});await page.setInputFiles('#reference-files',image);await page.waitForFunction(()=>window.__ffApp.collect().attachments?.some(a=>a.dataUrl));
 const portable=await page.evaluate(()=>window.__ffApp.collect());check('Portable project embeds original reference bytes and IDs',portable.attachments[0].dataUrl.startsWith('data:image/png;base64,')&&!!portable.attachments[0].sha256&&Object.keys(portable.designJourney.approvals).length===3);
 const portablePath=resolve(work,'reopened.floorforge.json');writeFileSync(portablePath,JSON.stringify(portable));await page.setInputFiles('#project-file',portablePath);await page.waitForFunction(()=>window.__ffApp.collect().attachments?.[0]?.dataUrl?.startsWith('data:image/png;base64,'));
 check('Save and upload retain floor IDs and approval records',await page.evaluate(ids=>window.__ffApp.collect().customPlan.floors.map(f=>f.id).join(',')===ids,project.customPlan.floors.map(f=>f.id).join(','))&&await page.evaluate(()=>Object.keys(window.__ffApp.collect().designJourney.approvals).length===3));
 await page.setViewportSize({width:390,height:844});await page.click('[data-journey-step="4"]');await page.waitForSelector('#myv-approve-floor',{timeout:180000});await page.screenshot({path:out+'/browser-2d-mobile.png'});
 check('Mobile 2D review fits the viewport',await page.evaluate(()=>document.getElementById('design-journey-dialog').scrollWidth<=innerWidth));
 await page.click('#myv-close');await page.setViewportSize({width:1440,height:1000});
 // A delayed successful preparation may not publish over a newer dimension edit.
 let release;const gate=new Promise(r=>release=r);let intercepted=false;
 await page.route('**/api/design/prepare',async route=>{const response=await route.fetch();intercepted=true;await gate;await route.fulfill({response});});
 const pending=page.evaluate(()=>window.__ffApp.designJourney.prepare());for(let i=0;i<100&&!intercepted;i++)await page.waitForTimeout(100);
 await page.evaluate(()=>{document.getElementById('width').value=Number(document.getElementById('width').value)+1;document.getElementById('width').dispatchEvent(new Event('input',{bubbles:true}));});release();await pending;
 check('Older preparation cannot replace a newer geometry edit',await page.evaluate(()=>!window.__ffApp.designJourney.ready()));await page.unroute('**/api/design/prepare');
 await page.click('#myv-close');const invalid=structuredClone(portable);invalid.text='The plot is 80 x 100 feet.';invalid.editorState.homeInputs=['plot','dxf','text'];invalid.designJourney.enabledInputs=['plot','dxf','text'];const invalidPath=resolve(work,'conflicting-draft.floorforge.json');writeFileSync(invalidPath,JSON.stringify(invalid));await page.setInputFiles('#project-file',invalidPath);await page.waitForFunction(()=>window.__ffApp.collect().text==='The plot is 80 x 100 feet.');check('An unresolved conflicting draft reopens with every source retained',await page.evaluate(()=>window.__ffApp.collect().customPlan.floors.length===3&&window.__ffApp.collect().editorState.homeInputs.includes('text')));await page.click('[data-journey-step="4"]');await page.waitForSelector('[data-question-choice]',{timeout:180000});check('Conflicting sources become one guided decision',await page.locator('.myv-question').count()===1&&await page.locator('[data-question-choice]').count()>=2);await page.screenshot({path:out+'/browser-source-question.png'});await page.locator('[data-question-choice]').first().click();await page.click('#myv-preview-answer');await page.waitForFunction(()=>!document.getElementById('myv-apply-answer').disabled,{timeout:180000});await page.click('#myv-apply-answer');await page.waitForFunction(()=>Object.keys(window.__ffApp.designJourney.state.answers).length>0);check('Source decision is previewed and applied explicitly',await page.evaluate(()=>Object.keys(window.__ffApp.designJourney.state.answers).length===1));await page.click('#myv-undo');await page.waitForFunction(()=>Object.keys(window.__ffApp.designJourney.state.answers).length===0);check('Undo restores the previous source decision and editable draft',await page.evaluate(()=>window.__ffApp.collect().customPlan.floors.length===3));check('No browser exceptions',errors.length===0,errors);
}catch(error){errors.push(error.stack||String(error));console.error(error);if(page)await page.screenshot({path:out+'/browser-failure.png',fullPage:true}).catch(()=>{});process.exitCode=1;}
finally{writeFileSync(resolve(out,'browser-checks.json'),JSON.stringify({checks,errors,timings,serverOutput:work,serverErrors:serverErrors.slice(-4000)},null,2));await browser?.close();server.kill('SIGTERM');}
