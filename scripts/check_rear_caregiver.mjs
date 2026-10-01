// Isolated visual checks: no changes to the user's camera or browser storage.
import {writeFileSync} from 'node:fs';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const checks=[],errors=[];const check=(name,pass)=>{checks.push({name,pass:!!pass});console.log(pass?'PASS':'FAIL',name);if(!pass)throw Error(name);};
try{
 const p=await browser.newPage({viewport:{width:1500,height:1000}});p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8765/samples/my-desired-home/preview.html');await p.waitForFunction(()=>window.__ff?.ready,null,{timeout:180000});
 await p.evaluate(()=>{const v=__ff.viewer;for(const id of ['g-care-caregiver','g-caregiver-garden-door']){const d=v.openings.items.find(o=>o.id===id);d.goal=1;}for(let i=0;i<90;i++)v.openings.update(1/60);});
 const shot=async(name,eye,target,fov=65)=>{await p.evaluate(({eye,target,fov})=>{const v=__ff.viewer;v.setMode('solid');v.paused=false;v.fitHeld=null;v.zoomAnim=null;v.camera.fov=fov;v.camera.updateProjectionMatrix();v.camera.position.set(...eye);v.controls.target.set(...target);v.controls.update();v.dirty=true;},{eye,target,fov});await p.waitForTimeout(800);await p.screenshot({path:`evidence/desired-home/${name}.png`});};
 await shot('care-lawn',[15.98,1.65,-8.85],[17.02,1.1,-13.4],65);
 await shot('recliner-lawn-view',[11.32,1.25,-10.875],[15.45,1.30,-10.625],74);
 await shot('rear-caregiver-entry',[9.2,1.6,-11.7],[6.7,1.2,-12.0],70);
 await shot('caregiver-rear-exit',[9.25,1.65,-13.42],[16.1,1.15,-13.5],68);
 await p.evaluate(()=>{const v=__ff.viewer,d=v.openings.items.find(o=>o.id==='g-care-caregiver');d.goal=0;for(let i=0;i<90;i++)v.openings.update(1/60);});
 await shot('icu-equipment-wall',[11.8,1.75,-9.2],[11.8,1.25,-12.7],80);
 check('Lawn is raised to match the garden floor',await p.evaluate(()=>__ff.viewer.data.lawns.some(l=>l.id==='g-care-lawn/grass'&&Math.abs(l.z-.032)<.001)));
 check('No browser errors',errors.length===0);
 writeFileSync('evidence/desired-home/rear-caregiver-checks.json',JSON.stringify({checks,errors},null,2));
}finally{await browser.close();}
