// Browser acceptance for the actual gallery projects (not synthetic floor geometry).
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, mkdtempSync } from 'node:fs';
import { resolve } from 'node:path';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const root = resolve(import.meta.dirname, '..'), out = resolve(root, 'evidence/tirumala-audit');
const baseline = process.argv.includes('--baseline'), port = 8897, url = `http://127.0.0.1:${port}`;
mkdirSync(out, { recursive: true });
const server = spawn(resolve(root, '.venv/bin/python'), ['-m', 'floorforge', 'serve', '--no-browser', '--port', String(port), '--out', mkdtempSync('/tmp/ff-tirumala-audit-')], { cwd: root, stdio: ['ignore', 'ignore', 'pipe'] });
server.stderr.on('data', d => process.stderr.write(d));
let browser; const results = [], errors = [];
try {
  for (let i=0; i<100; i++) { try { if ((await fetch(url+'/api/session')).ok) break; } catch {} await new Promise(r=>setTimeout(r,200)); }
  browser = await chromium.launch({ headless:true, args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport:{width:1440,height:1000} });
  page.on('pageerror', e=>errors.push(e.message));
  await page.goto(url);
  await page.waitForFunction(()=>window.__ffApp?.viewer && window.__ff?.ready && !document.querySelector('[data-start="continue"]')?.disabled,null,{timeout:180000});
  await page.click('[data-start="continue"]'); await page.click('#design-result');
  for (const slug of ['tirumala-2','tirumala-3']) {
    await page.selectOption('#workspace-project',`sample:${slug}`);
    await page.waitForFunction(id=>window.__ff?.buildId===id && !window.__ffApp.draftStale,`sample:${slug}`,{timeout:60000});
    await page.click('.project-workspace [data-project-view="3d"]');
    await page.click('[data-mode="walk"]');
    const result = await page.evaluate(()=>{
      const v=window.__ffApp.viewer; v.setQuality('performance'); v.paused=true; v.resize();
      const start=v.walker.position.toArray();
      for(let i=0;i<180;i++) v.walker.update(1/60,{forward:0,strafe:0});
      v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone())); v.camera.rotation.set(0,v.walker.yaw,0);
      v.composer.render(0);
      return {start,afterThreeSeconds:v.walker.position.toArray(),onGround:v.walker.onGround,
        doors:v.openings.items.map(i=>({id:i.id,initial:i.initial,parts:i.parts.length,ids:i.parts.flatMap(p=>p.ids)}))};
    });
    const acceptance = [];
    const check = (name, pass, detail) => { acceptance.push({name,pass:!!pass,detail}); console.log(pass?'PASS':'FAIL',slug,name); };
    if (!baseline) {
      const viewport=await page.evaluate(()=>{
        const r=document.getElementById('scene').getBoundingClientRect();
        return {height:r.height,visibleHeight:Math.max(0,Math.min(innerHeight,r.bottom)-Math.max(0,r.top)),
          alternativesHidden:document.getElementById('tirumala-option-buttons').hidden,
          cameras:[...document.getElementById('tirumala-room-view').options].map(o=>o.value)};
      });
      check('Normal 3D view has usable height and only the current plan controls',viewport.visibleHeight>400&&viewport.alternativesHidden&&viewport.cameras.includes('interior_icu_veranda_garden'),viewport);
      await page.evaluate(()=>window.__ffApp.viewer.canvas.focus());
      await page.keyboard.down('ArrowUp');
      const movement = await page.evaluate(()=>{
        const v=window.__ffApp.viewer,w=v.walker,start=w.position.toArray();
        for(let i=0;i<100;i++)w.update(1/120,v.readInput());
        return {start,end:w.position.toArray(),supported:w.onGround};
      });
      await page.keyboard.up('ArrowUp');
      check('ArrowUp walks from the roadside across the entrance threshold',movement.supported&&movement.end[2]<-.2&&movement.end[1]>-.2,movement);
      const interaction=await page.evaluate(()=>{
        const v=window.__ffApp.viewer,item=v.openings.items.find(i=>i.id==='icu-glass-living');
        const normal=item.axis.clone().set(-item.axis.z,0,item.axis.x);
        const feet=item.center.clone().addScaledVector(normal,1.1);feet.y=.05;
        v.walker.teleport(feet,Math.atan2(normal.x,normal.z));
        v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone()));v.camera.rotation.set(0,v.walker.yaw,0);
        v.openings.updateTarget();v.canvas.focus();
        return {target:v.openings.target?.id,value:item.value};
      });
      check('ICU glass opening can be targeted from walking mode',interaction.target==='icu-glass-living',interaction);
      await page.keyboard.press('f');
      const closed=await page.evaluate(()=>{const v=window.__ffApp.viewer;for(let i=0;i<90;i++)v.openings.update(1/60);return v.openings.items.find(i=>i.id==='icu-glass-living').value;});
      check('F closes the ICU glass panels',closed===0,closed);
      await page.evaluate(()=>window.__ffApp.viewer.openings.updateTarget());
      await page.keyboard.press('f');
      const reopened=await page.evaluate(()=>{const v=window.__ffApp.viewer;for(let i=0;i<90;i++)v.openings.update(1/60);return v.openings.items.find(i=>i.id==='icu-glass-living').value;});
      check('F fully reopens the ICU connection',reopened===1,reopened);
      for(const name of ['interior_kitchen_living_dining','interior_icu_veranda_garden']){
        const camera=await page.evaluate(name=>{
          const v=window.__ffApp.viewer;v.setGrade('day');v.setQuality('balanced');v.setNamedCamera(name);v.resize();
          for(let i=0;i<60;i++)v.walker.update(1/60,{forward:0,strafe:0});
          v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone()));v.camera.rotation.set(v.walker.pitch,v.walker.yaw,0);
          v.indoor=1;v.updateProbe();v.updateLights(true);v.adapt(4);v.composer.render(0);
          return {mode:v.mode,feet:v.walker.position.toArray(),eye:v.camera.position.toArray(),fov:v.camera.fov,grounded:v.walker.onGround};
        },name);
        check(`${name} stays at real eye level after physics`,camera.mode==='walk'&&camera.grounded&&Math.abs(camera.eye[1]-camera.feet[1]-1.63)<.02,camera);
        await page.locator('#scene').screenshot({path:resolve(out,`${slug}-${name}.png`)});
      }
      const mode=await page.evaluate(()=>{const v=window.__ffApp.viewer;v.setNamedCamera('exterior_east');return v.mode;});
      check('Exterior camera exits walking without snapping back',mode==='solid',mode);
    }
    results.push({slug,...result,acceptance});
    await page.screenshot({path:resolve(out,`${slug}-${baseline?'before':'after'}-arrival.png`)});
    console.log(slug,JSON.stringify({start:result.start,after:result.afterThreeSeconds,onGround:result.onGround,doors:result.doors.map(d=>d.id)}));
  }
} finally {
  writeFileSync(resolve(out,`${baseline?'baseline':'browser'}-results.json`),JSON.stringify({results,errors},null,2)+'\n');
  await browser?.close(); server.kill();
}
if (!baseline && (errors.length || results.some(r=>!r.onGround || r.afterThreeSeconds[1]<-.5 || r.acceptance.some(c=>!c.pass)))) process.exitCode=1;
