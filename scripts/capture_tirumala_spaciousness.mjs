import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import('/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'output/tirumala-icu-trials');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const checks=[],errors=[];
const cameras={icu:'interior_icu_veranda_garden',living:'interior_kitchen_living_dining',veranda:'interior_veranda_living',
 master:'interior_master',drawing:'interior_drawing',gallery:'upper_gallery',upperMaster:'upper_master',office:'upper_office',terrace:'upper_terrace'};
try {
 for(const key of ['compact-only','south-extension']) {
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  page.on('pageerror',e=>errors.push(`${key}: ${e.message}`));
  await page.goto(`file://${out}/${key}/preview.html`);
  await page.waitForFunction(()=>window.__ff?.ready,null,{timeout:120000});
  await page.selectOption('#trialRoom','interior_kitchen_living_dining');
  await page.click('#trialICU');
  checks.push({check:`${key}: room selector enters walking mode`,pass:await page.evaluate(()=>window.__ff.viewer.mode==='walk')});
  await page.click('#trialOpen');
  await page.evaluate(()=>{
   document.querySelector('header').style.display='none';document.querySelector('aside').style.display='none';
   document.querySelector('main').style.display='block';document.querySelector('main').style.height='100vh';
   document.querySelector('section').style.height='100vh';document.querySelector('.tools').style.display='none';document.querySelector('.status').style.display='none';
   const v=window.__ff.viewer;v.paused=true;v.resize();v.setQuality('balanced');v.setGrade('day');
   for(const i of v.openings.items)if(i.kind!=='window'){i.value=1;i.goal=1;v.openings.pose(i);}v.openings.syncGeometry();
  });
  for(const [label,name] of Object.entries(cameras)) {
   const detail=await page.evaluate(name=>{
    const v=window.__ff.viewer;v.setNamedCamera(name);
    const expected=v.data.cameras[name].position;
    for(let i=0;i<90;i++)v.walker.update(1/90,{forward:0,strafe:0});
    v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone()));v.camera.rotation.set(v.walker.pitch,v.walker.yaw,0);
    v.indoor=v.isIndoors(v.camera.position)?1:0;v.updateProbe();v.updateLights(true);v.metered=null;v.adapt(3);v.hud.show(false);v.composer.render(0);
    return {expected,feet:v.walker.position.toArray(),eye:v.camera.position.toArray(),onGround:v.walker.onGround,
     indoors:v.indoor,lamps:v.lampLevel(),fov:v.camera.fov,rootScale:v.root.scale.toArray(),exposure:v.gradeEffect.uniforms.get('exposure').value,
     movement:Math.hypot(v.walker.position.x-expected[0],v.walker.position.z+expected[1])};
   },name);
   const pass=detail.onGround&&Math.abs(detail.eye[1]-detail.feet[1]-1.63)<.025&&detail.movement<.05&&detail.rootScale.every(v=>v===1)&&detail.fov<=68;
   checks.push({check:`${key}: ${label} safe true-scale eye-level view`,pass,detail});
   if(!pass)throw Error(JSON.stringify(checks.at(-1)));
   await page.waitForTimeout(120);
   await page.locator('#view').screenshot({path:resolve(out,`${key}-${label==='icu'?'interior':label}.png`)});
   console.log('PASS',key,label,detail.indoors.toFixed(2),detail.lamps);
  }
  await page.evaluate(()=>{
   const v=window.__ff.viewer;v.setMode('dollhouse');v.setFloor(0);v.showContext(false);
   v.data.cameras.trialCutaway={position:[6.096,-8,23],target:[6.096,7.5,.2],fov:48};v.setNamedCamera('trialCutaway');v.showContext(false);
   v.materials.clipPlane.constant=1.48;v.indoor=0;v.updateProbe();v.metered=null;v.adapt(3);v.composer.render(0);
  });
  await page.locator('#view').screenshot({path:resolve(out,`${key}-cutaway.png`)});
  await page.close();
 }
 writeFileSync(resolve(out,'spaciousness-browser-checks.json'),JSON.stringify({checks,errors},null,2));
 if(errors.length||checks.some(c=>!c.pass))throw Error(JSON.stringify({checks,errors}));
 console.log('All spaciousness views and controls verified');
}finally{writeFileSync(resolve(out,'spaciousness-browser-checks.json'),JSON.stringify({checks,errors},null,2));await browser.close();}
