// Live regression and screenshots for the spacious Revision 10 samples.
// Start the local server first; override FLOORFORGE_URL when using another port.
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';
const sharp=createRequire(import.meta.url)(process.env.SHARP_MODULE || '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ||
  '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const root = resolve(import.meta.dirname, '..');
const out = resolve(root, 'evidence/tirumala/revision-10');
mkdirSync(out, { recursive: true });
const checks = [], errors = [], optionHashes = {};
const check = (name, pass, detail) => {
  checks.push({ name, pass: !!pass, detail });
  console.log(pass ? 'PASS' : 'FAIL', name, detail ? JSON.stringify(detail) : '');
  if (!pass) throw Error(name);
};
const browser = await chromium.launch({ headless: true,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  const page = await browser.newPage({ viewport: { width: 1512, height: 1050 } });
  page.setDefaultTimeout(120000);
  page.on('pageerror', e => {errors.push(e.message);console.log('PAGE ERROR',e.message);});
  // The landing-page animation is unrelated to the model being tested.
  await page.route('**/hero.js', r => r.fulfill({ status: 200, contentType: 'application/javascript', body: '' }));
  console.log('Opening local preview');
  await page.goto(process.env.FLOORFORGE_URL || 'http://127.0.0.1:8897');
  console.log('Preview loaded');
  await page.waitForFunction(() => window.__ffApp?.viewer && !document.querySelector('[data-start="continue"]').disabled);
  console.log('Viewer initialized');
  await page.click('[data-start="continue"]');
  await page.click('#design-result');
  console.log('Opening Tirumala');
  await page.selectOption('#workspace-project', 'sample:tirumala');
  await page.waitForFunction(() => window.__ff?.buildId === 'sample:tirumala' && !window.__ffApp.draftStale, null, {timeout:30000}).catch(async e=>{console.log('LOAD STATE',await page.evaluate(()=>({build:window.__ff?.buildId,stale:window.__ffApp?.draftStale,toast:document.getElementById('toast')?.textContent,status:document.getElementById('status')?.textContent})));throw e;});
  await page.evaluate(() => { const v = window.__ffApp.viewer; v.autoQuality = false; v.setQuality('performance'); });
  check('Revision 10 opens through the sample selector with twelve interior presets', await page.evaluate(() =>
    window.__ff.building.planning.tirumalaRevision === 10 && document.querySelector('#tirumala-room-view').options.length === 13));
  const capture = async name => {
    await page.evaluate(() => { window.__ffApp.viewer.paused = true; document.getElementById('toast').hidden = true; });
    const data = await page.evaluate(async () => {
      const blob = await window.__ffApp.viewer.snapshot({width:1800});
      return await new Promise(resolve => {const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsDataURL(blob);});
    });
    writeFileSync(resolve(out,name),Buffer.from(data.split(',')[1],'base64'));
  };
  for (const code of 'ABCDE') {
    if (code !== 'A') {
      await page.click(`[data-tirumala-option="${code}"]`);
      await page.waitForFunction(c => window.__ffApp.currentTirumalaOption === c && !window.__ffApp.draftStale, code);
    }
    const state = await page.evaluate(() => {
      const { building: b, scene: s, sheets } = window.__ff;
      const area = id => b.spaces.find(r => r.id === id).area_m2 / .09290304;
      return { hash: s.planHash, consistent: b.planHash === s.planHash && sheets.every(p => p.planHash === s.planHash),
        kitchen: area('g-kitchen'), drawing: area('g-drawing'), upperBedroom: area('u-master'),
        editorIssues: window.__ffApp.planEditor.localIssues().length };
    });
    optionHashes[code] = state.hash;
    check(`Option ${code}: synchronized 2D/3D, enlarged rooms, no editor issues`,
      state.consistent && state.kitchen > 120 && state.drawing > 109 && state.upperBedroom > 176 && state.editorIssues === 0, state);
    await page.evaluate(()=>{window.__ffApp.viewer.paused=true;});
    await page.locator('.project-workspace [data-project-view="2d"]').click();
    await page.selectOption('#sheet-select', 'A-101');
    await page.waitForFunction(() => document.querySelector('#drawing-image').complete && document.querySelector('#drawing-image').naturalWidth > 0);
    await sharp(resolve(root,`examples/gallery/tirumala/variants/${code}/sheets/A-101.svg`),{density:150}).resize({width:3000}).png().toFile(resolve(out,`option-${code}-ground-plan.png`));
    await page.selectOption('#sheet-select', 'A-102');
    await page.waitForFunction(() => document.querySelector('#drawing-image').complete && document.querySelector('#drawing-image').naturalWidth > 0);
    await sharp(resolve(root,`examples/gallery/tirumala/variants/${code}/sheets/A-102.svg`),{density:150}).resize({width:3000}).png().toFile(resolve(out,`option-${code}-upper-plan.png`));
    await page.locator('.project-workspace [data-project-view="3d"]').click();
    await page.evaluate(() => { const v = window.__ffApp.viewer; v.paused = false; v.setFloor(0); v.setMode('dollhouse'); });
    await page.waitForTimeout(1000);
    await capture(`option-${code}-dollhouse.png`);
    await page.evaluate(() => {const v=window.__ffApp.viewer;v.paused=false;v.setFloor(1);v.setMode('dollhouse');});
    await page.waitForTimeout(1000);
    await capture(`option-${code}-upper-dollhouse.png`);
  }
  check('All five variants remain distinct', new Set(Object.values(optionHashes)).size === 5);
  await page.click('[data-tirumala-option="A"]');
  await page.waitForFunction(() => window.__ffApp.currentTirumalaOption === 'A' && !window.__ffApp.draftStale);
  // Confirm the selector itself enters walking mode; then use focus mode for full-size captures.
  await page.selectOption('#tirumala-room-view', 'living_dining_kitchen');
  check('Explore-inside selector enters the kitchen in walk mode', await page.evaluate(() => window.__ffApp.viewer.mode === 'walk'));
  await page.click('#focus');
  await page.evaluate(() => { const v = window.__ffApp.viewer; v.setQuality('balanced'); v.autoQuality = false; });
  const cameras = ['living_dining_kitchen', 'drawing_interior', 'entry_connected_hall', 'dining_stair_connection',
    'care_interior_overview', 'double_height_living_void', 'upper_gallery_connection', 'upper_lounge_connection', 'upper_master_one', 'upper_master_two', 'upper_office', 'shared_upper_terrace'];
  for (const name of cameras) {
    const state = await page.evaluate(name => {
      const v = window.__ffApp.viewer;
      v.paused = true;
      v.setNamedCamera(name);
      const c = v.data.cameras[name], expected = c.walker.position;
      for (let i = 0; i < 120; i++) v.walker.update(1 / 60, { forward: 0, strafe: 0 });
      const p = v.walker.position;
      const delta = Math.hypot(p.x - expected[0], p.z + expected[1]);
      const elevation = p.y - c.floor * v.H;
      v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone()));
      v.paused = false;
      return { mode: v.mode, floor: v.floor, expectedFloor: c.floor, delta, elevation, fov: v.camera.fov };
    }, name);
    check(`Preset ${name}: valid floor, human lens and unobstructed standing position`,
      state.mode === 'walk' && state.floor === state.expectedFloor && state.delta < .08 && Math.abs(state.elevation) < .08 && state.fov === 62, state);
    await page.waitForTimeout(1400);
    await capture(`${name}.png`);
  }
  const routes = await page.evaluate(() => {
    const v = window.__ffApp.viewer; v.paused = true; v.setFloor(0); v.setMode('walk');
    const w = v.walker, results = [];
    const open = id => { const items = v.openings.items.filter(o => o.id === id || o.id.startsWith(id + '/'));
      for (const d of items) d.goal = 1; for (let i = 0; i < 90; i++) v.openings.update(1/60); return items.length; };
    const spawn = (x,y,z=0) => w.teleport(w.position.clone().set(x,z,-y));
    const walk = (x,y) => { for (let i=0;i<650;i++) { const dx=x-w.position.x,dz=-y-w.position.z;
      if (Math.hypot(dx,dz)<.09) return true; w.yaw=Math.atan2(-dx,-dz);w.update(1/60,{forward:1,strafe:0}); } return false; };
    open('g-entry');spawn(7.12,2.75);results.push({route:'Porch to drawing',pass:walk(7.12,3.8)});
    open('g-care-hall-slider');spawn(6.72,8.2);results.push({route:'Hall to care',pass:walk(7.55,8.2)});
    open('g-care-veranda-slider');spawn(9.45,9.8);results.push({route:'Care to veranda',pass:walk(9.45,11.3)});
    spawn(4.35,9.22);const stair=[[.685,9.22],[.685,5.70]].every(([x,y])=>walk(x,y));
    for(let i=0;i<30;i++)w.update(1/60,{forward:0,strafe:0});
    results.push({route:'L stair: south flight, quarter turn, east flight',pass:stair && Math.abs(w.position.y-3.658)<.15,position:w.position.toArray()});
    results.push({route:'Upper stair arrival into open lounge',pass:walk(4.5,5.70),position:w.position.toArray()});
    // Descend the same actual tread geometry, without teleporting between floors.
    const down=[[.685,5.70],[.685,9.22],[4.35,9.22]].every(([x,y])=>walk(x,y));
    for(let i=0;i<30;i++)w.update(1/60,{forward:0,strafe:0});
    results.push({route:'L stair return to ground hall',pass:down && Math.abs(w.position.y)<.15,position:w.position.toArray()});
    spawn(4.5,7.7);results.push({route:'Dining to kitchen past the low serving counter',pass:walk(4.5,5.5)&&walk(3.5,5.5)});
    open('u-lobby-terrace-door');spawn(4.8,4.65,3.658);
    results.push({route:'Common lounge directly onto open terrace',pass:walk(5.8,4.65)});
    open('u-master-terrace-door');spawn(7.70,4.6,3.658);
    results.push({route:'Terrace directly into master suite 2',pass:walk(7.70,5.6)});
    open('u-master-2-door');spawn(4.8,5.94,3.658);
    results.push({route:'Common lounge into master suite 2',pass:walk(5.9,5.94)});
    open('u-master-door');spawn(5.3,10.668,3.658);
    results.push({route:'Common hall into master suite 1',pass:walk(4.4,10.668)});
    open('u-study-door');spawn(6.096,12.0,3.658);
    results.push({route:'Common hall into small office',pass:walk(6.096,12.6)});
    return results;
  });
  console.log('ROUTES',JSON.stringify(routes));
  for (const r of routes) check(r.route, r.pass, r);
  await page.click('#focus');
  for (const slug of ['my-desired-home', 'saved-verandah', 'bungalow']) {
    await page.selectOption('#workspace-project', `sample:${slug}`);
    await page.waitForFunction(id => window.__ff?.buildId === `sample:${id}` && !window.__ffApp.draftStale, slug);
    check(`${slug} still loads without Tirumala controls`, await page.evaluate(() => document.getElementById('tirumala-options-bar').hidden));
  }
  check('No browser page errors', errors.length === 0, errors);
} catch (e) {
  errors.push(e.message); throw e;
} finally {
  writeFileSync(resolve(out, 'browser-checks.json'), JSON.stringify({ revision: 10, optionHashes, checks, errors }, null, 2));
  await browser.close();
}
