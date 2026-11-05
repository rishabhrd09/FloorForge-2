import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
const {chromium}=await import('/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'output/tirumala-icu-trials');
const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
const errors=[],checks=[];
try {
  const visual=await browser.newPage({viewport:{width:1100,height:1000},deviceScaleFactor:1.5});
  visual.on('pageerror',e=>errors.push(e.message));
  await visual.goto('file:///tmp/p12-icu-trials-visual-preview.html');
  const frame=visual.frames().find(f=>f.parentFrame());
  await frame.waitForSelector('#p12-trial-a text');
  await visual.screenshot({path:resolve(out,'comparison-detail.png'),fullPage:true});
  await frame.locator('#p12-trial-view').selectOption('full');
  await visual.waitForTimeout(150);
  await visual.screenshot({path:resolve(out,'comparison-full.png'),fullPage:true});
  checks.push({check:'Full ground-floor selector works',pass:await frame.locator('#p12-trial-a').textContent().then(t=>t.includes('Master bedroom'))});
  await visual.setViewportSize({width:360,height:900});
  await frame.locator('#p12-trial-view').selectOption('detail');
  await visual.waitForTimeout(150);
  checks.push({check:'Mobile comparison does not overflow',pass:await frame.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2)});
  await visual.screenshot({path:resolve(out,'comparison-mobile.png'),fullPage:true});
  await visual.close();
  for(const key of process.argv.includes('--visual-only')?[]:['compact-only','south-extension']) {
    const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
    page.on('pageerror',e=>errors.push(key+': '+e.message));
    await page.goto(`file://${out}/${key}/preview.html`);
    await page.waitForFunction(()=>window.__ff?.ready,null,{timeout:120000});
    console.log('Loaded',key);
    await page.evaluate(()=>{
      document.querySelector('header').style.display='none';document.querySelector('aside').style.display='none';
      document.querySelector('main').style.display='block';document.querySelector('main').style.height='100vh';
      document.querySelector('section').style.height='100vh';
      document.querySelector('.tools').style.display='none';document.querySelector('.status').style.display='none';
      const v=window.__ff.viewer;v.paused=true;v.resize();v.setQuality('balanced');v.setFloor(0);v.setGrade('day');
      for(const o of v.openings.items)if(o.kind!=='window'){o.value=1;o.goal=1;v.openings.pose(o);}v.openings.syncGeometry();
      v.setMode('solid');
      v.data.cameras.trialInterior={position:[9.5,7.4,1.63],target:[7.65,4.25,1.25],fov:64};
      v.setNamedCamera('trialInterior');v.indoor=1;v.updateProbe();v.updateLights(true);v.adapt(3);v.hud.show(false);v.composer.render(0);
    });
    await page.waitForTimeout(800);
    await page.locator('#view').screenshot({path:resolve(out,`${key}-interior.png`)});
    const state=await page.evaluate(()=>({scale:window.__ff.viewer.root.scale.toArray(),eye:window.__ff.viewer.camera.position.y,fov:window.__ff.viewer.camera.fov}));
    checks.push({check:key+' same true-scale interior camera',pass:state.scale.every(s=>s===1)&&Math.abs(state.eye-1.63)<1e-8&&state.fov===64,detail:state});
    await page.evaluate(()=>{
      const v=window.__ff.viewer;v.setMode('dollhouse');v.showContext(false);
      v.data.cameras.trialCutaway={position:[6.096,-8,23],target:[6.096,7.5,.2],fov:48};v.setNamedCamera('trialCutaway');v.showContext(false);
      v.materials.clipPlane.constant=1.48;v.indoor=0;v.updateProbe();v.updateLights(true);v.adapt(2.5);v.composer.render(0);
    });
    await page.waitForTimeout(500);
    await page.locator('#view').screenshot({path:resolve(out,`${key}-cutaway.png`)});
    await page.close();console.log('Captured',key);
  }
  writeFileSync(resolve(out,process.argv.includes('--visual-only')?'visual-checks.json':'browser-checks.json'),JSON.stringify({checks,errors},null,2));
  if(errors.length||checks.some(c=>!c.pass))throw Error(JSON.stringify({checks,errors}));
  console.log('All browser checks passed');
}finally{await browser.close();}
