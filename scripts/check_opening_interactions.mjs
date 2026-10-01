// Exercise keyboard focus, mapping and the real walking controller in the built app.
import { spawn, execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = resolve(import.meta.dirname, '..'), out = resolve(root, 'evidence/opening-interactions');
const port = 8879, url = `http://127.0.0.1:${port}`, checks = [], errors = [];
mkdirSync(out, { recursive: true });
const server = spawn(resolve(root, '.venv/bin/python'), ['-m', 'floorforge', 'serve', '--no-browser', '--port', String(port), '--out', '/tmp/ff-opening-interactions'], { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
server.stderr.on('data', data => process.stderr.write(data));
const check = (name, pass, data) => { checks.push({ name, pass: Boolean(pass), data }); console.log(pass ? 'PASS' : 'FAIL', name); if (!pass) throw Error(name); };
let browser;
try {
  for (let i = 0; i < 80; i++) { try { if ((await fetch(url + '/api/session')).ok) break; } catch {} await new Promise(r => setTimeout(r, 250)); }
  browser = await chromium.launch({ headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(url, { timeout: 180000 });
  await page.waitForFunction(() => window.__ffApp?.viewer && window.__ff?.ready, null, { timeout: 240000 });
  await page.evaluate(() => { const v=window.__ffApp.viewer; v.paused=true; v.setQuality('performance'); v.setMode('walk'); v.canvas.focus(); });
  check('Saved example has an interactive object for every door and window', await page.evaluate(() => {
    const v=window.__ffApp.viewer; return v.openings.items.length>10 && v.openings.items.every(i=>i.parts.every(p=>p.group.children.length));
  }));
  const approach = (kind, side=1, wanted=null) => page.evaluate(({kind,side,wanted}) => {
    const v=window.__ffApp.viewer,w=v.walker;
    for(const item of v.openings.items.filter(i=>i.kind===kind&&(!wanted||i.id===wanted))) {
      for(const along of [.25,.7,.45]) {
        const p=item.start.clone().addScaledVector(item.axis,item.width*along);
        const normal=item.axis.clone().set(-item.axis.z,0,item.axis.x).multiplyScalar(side);
        p.addScaledVector(normal,1.4); p.y=item.base;
        w.position.copy(p);w.velocity.set(0,0,0);w.eyeY=p.y+w.s.eye;w.yaw=Math.atan2(normal.x,normal.z);w.pitch=0;
        v.openings.updateTarget();
        if(v.openings.target===item) {v.camera.position.copy(w.eyePosition(v.camera.position.clone()));v.camera.rotation.set(0,w.yaw,0);v.hud.setLocked(true);v.hudUpdate();return {id:item.id,value:item.value,goal:item.goal};}
      }
    }
    return null;
  },{kind,side,wanted});
  const advance=()=>page.evaluate(()=>{const v=window.__ffApp.viewer;for(let i=0;i<65;i++)v.openings.update(1/60);v.openings.updateTarget();});
  const state=id=>page.evaluate(id=>{const v=window.__ffApp.viewer,i=v.openings.items.find(i=>i.id===id);return {value:i.value,goal:i.goal,message:v.openings.message,matrix:i.parts[0].group.matrix.elements};},id);
  const win=await approach('window');check('Window is reachable from one side with an Open prompt',win&&await page.locator('.ff-interact').textContent().then(t=>t.toLowerCase().includes('open window')));
  const before=await state(win.id);await page.keyboard.press('f');await advance();const opened=await state(win.id);
  check('F opens the actual window geometry',opened.value===1&&JSON.stringify(before.matrix)!==JSON.stringify(opened.matrix),opened);
  const opposite=await approach('window',-1,win.id);check('The same window is reachable from the opposite side',opposite?.id===win.id);
  await page.locator('.ff-interact').click();await advance();check('Tap/click closes that same window', (await state(win.id)).value===0);
  await page.evaluate(()=>{const v=window.__ffApp.viewer;v.composer.render(0);});
  await page.screenshot({path:out+'/nearby-window.png'});
  const door=await approach('door');check('Room door is reachable',door);
  await page.focus('#scene');await page.keyboard.press('f');await advance();check('F closes the room door',(await state(door.id)).value===0,await state(door.id));
  await page.keyboard.press('f');await advance();check('F reopens the room door',(await state(door.id)).value===1);
  const balcony=await approach('glazed');check('Balcony glass leaf has an Open fully action',balcony);
  await page.keyboard.press('f');await advance();check('Balcony leaf clears the wider opening',(await state(balcony.id)).value===1,await state(balcony.id));
  await page.evaluate(()=>{const v=window.__ffApp.viewer;v.composer.render(0);});await page.screenshot({path:out+'/balcony-door.png'});
  await page.focus('#width');const unchanged=await state(balcony.id);await page.keyboard.press('f');check('Typing F in a form does not operate a door',(await state(balcony.id)).value===unchanged.value);
  const customScene = JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',`import json
from pathlib import Path
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import reports,validate
from floorforge.scene import make_scene
b=generate_layout(fuse(json.loads(Path('examples/custom/g2-terrace.floorforge.json').read_text())))
print(json.dumps(make_scene(b,reports(b,validate(b)))))`],{cwd:root,maxBuffer:64*1024*1024}));
  await page.evaluate(scene=>{const v=window.__ffApp.viewer;v.setScene(scene);v.paused=true;v.setMode('walk');v.canvas.focus();},customScene);
  check('New G+2 scene supports interactions without a companion building file',await page.evaluate(()=>{const v=window.__ffApp.viewer;return v.data.storeys===3&&v.openings.items.length===v.data.opening_model.openings.filter(o=>o.kind!=='cased').length;}));
  const customDoor=await approach('door');check('Custom authored door has the same interaction',customDoor);
  await page.focus('#scene');await page.keyboard.press('f');await advance();check('Custom authored door closes with its own stable object ID',(await state(customDoor.id)).value===0,await state(customDoor.id));
  await page.evaluate(()=>{const v=window.__ffApp.viewer;v.setMode('solid');});
  await page.evaluate(async()=>{await window.__ffApp.applyProject({brief:{bedrooms:2,storeys:1},text:'3 bedrooms. A soundproof music studio.',sources:[{id:'manual',kind:'form',values:{bedrooms:4}}]});});
  await page.click('#understand');await page.waitForSelector('#intent-dialog[open]');
  check('Input review names overriding inputs and unapplied requests',await page.locator('#intent-content').textContent().then(t=>t.includes('soundproof')&&t.includes('unapplied')&&t.includes('manual')&&t.includes('3 → 4')));
  await page.evaluate(()=>document.getElementById('intent-dialog').close());
  check('Input coverage stays visible outside the review dialog',await page.locator('#input-coverage').isVisible()&&await page.locator('#input-coverage').getAttribute('open')!==null);
  check('No browser errors',errors.length===0,errors);
} finally {
  writeFileSync(out + '/browser-acceptance.json', JSON.stringify({ checks, errors }, null, 2) + '\n');
  if (browser) await browser.close();
  server.kill();
}
