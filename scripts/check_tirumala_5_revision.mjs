// Acceptance of the approved Tirumala 5 revision on the real, generated geometry.
// One arrival spawn; every subsequent floor change uses walker.update(), never teleport.
// Run after build_tirumala_5.py with the same Node runtime used for the viewer checks.
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const root = resolve(import.meta.dirname, '..');
const upperOnly = process.argv.includes('--upper-only');
const out = resolve(root, process.env.T5_CHECK_OUT || `evidence/tirumala-5-revision${upperOnly ? '-upper' : ''}`);
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const building = JSON.parse(readFileSync(resolve(root, 'examples/gallery/tirumala-5/building.json'), 'utf8'));
const plan = building.planning.canonicalPlan;
const results = {planHash: building.planHash, mode: upperOnly ? 'first-floor arrival → second → first' : 'full gate-to-roof round trip', started: new Date().toISOString(), checks: [], routes: [], interactions: [], errors: [], initialSpawns: 1, laterTeleports: 0};
mkdirSync(out, {recursive: true});
const browser = await chromium.launch({headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
let page;
function check(name, pass, detail) {
  const row = {name, pass: Boolean(pass), detail};
  results.checks.push(row);
  console.log(`${pass ? 'PASS' : 'FAIL'} ${name}${detail == null ? '' : ' ' + JSON.stringify(detail)}`);
  return row;
}
async function screenshot(name) {
  await page.evaluate(() => {
    const v = window.__ff.viewer, w = v.walker;
    v.camera.position.copy(w.eyePosition(v.camera.position.clone()));
    v.camera.rotation.set(w.pitch, w.yaw, 0, 'YXZ');
    v.hudUpdate(); v.updateProbe(); v.updateLights(true); v.adapt(2); v.composer.render(0);
  });
  await page.screenshot({path: resolve(out, `${name}.png`)});
}
async function walk(name, x, y, h, options = {}) {
  const result = await page.evaluate(({name, x, y, h, options}) => window.__t5Harness.walk(name, x, y, h, options), {name, x, y, h, options});
  results.routes.push(result);
  check(name, result.pass, {position: result.position, error: result.error, supported: result.grounded, reason: result.reason, frames: result.frames});
  if (!result.pass) {
    await screenshot('failed-route');
    throw Error(`Walking route failed: ${name}`);
  }
  return result;
}
async function door(id, desired = 1, exercise = false) {
  const sequence = exercise ? [desired === 1 ? 0 : 1, desired] : [desired];
  for (const wanted of sequence) {
    const target = await page.evaluate(({id, wanted}) => window.__t5Harness.aim(id, wanted), {id, wanted});
    if (target.already) {
      results.interactions.push({id, desired: wanted, already: true, pass: true});
      continue;
    }
    if (!target.pass) {
      results.interactions.push({...target, id, desired: wanted, pass: false});
      check(`Target ${id}`, false, target);
      throw Error(`Cannot target ${id} from current walking position`);
    }
    // Use the same focused keyboard event and interaction handler as a visitor.
    await page.keyboard.press('f');
    const result = await page.evaluate(({id, wanted}) => window.__t5Harness.settleDoor(id, wanted), {id, wanted});
    results.interactions.push({...result, id, desired: wanted});
    check(`${wanted ? 'Open' : 'Close'} ${id} using F`, result.pass, result);
    if (!result.pass) throw Error(`Door interaction failed: ${id}`);
  }
}
try {
  const aperture = id => plan.openings.find(o => o.id === id);
  const main = aperture('living-veranda'), icu = aperture('icu-glass-living');
  const fresh = main?.a[0] === 7300 && Math.abs(icu?.a[0] - 5452.4) < .01 && building.openings.some(o => o.id === 's2-stair-terrace-proposed');
  check('Generated files contain the approved junction and internal upper stair revision', fresh, {main: main?.a, icu: icu?.a, internalTerraceDoor: building.openings.some(o => o.id === 's2-stair-terrace-proposed')});
  if (!fresh) throw Error('Fresh Tirumala 5 build required; old geometry was not tested as the new revision.');

  page = await browser.newPage({viewport: {width: 1280, height: 900}});
  page.on('pageerror', e => results.errors.push(e.message));
  await page.goto(process.env.T5_PREVIEW_URL || pathToFileURL(resolve(root, 'examples/gallery/tirumala-5/preview.html')).href, {timeout: 120000});
  await page.waitForFunction(() => window.__ff?.ready && window.__ff.viewer?.walker, null, {timeout: 180000});
  const initial = await page.evaluate(upperOnly => {
    const v = window.__ff.viewer;
    v.paused = true; v.setQuality('performance'); v.floor = upperOnly ? 1 : 0; v.setMode('walk'); v.setCarVisible(true);
    const w = v.walker;
    // The harness changes heading and movement input only. No position writes after the arrival spawn.
    const idle = n => { for (let i = 0; i < n; i++) w.update(1 / 120, {forward: 0, strafe: 0}); };
    idle(120);
    window.__t5Harness = {
      walk(name, x, y, h, options = {}) {
        const start = [w.position.x, -w.position.z, w.position.y], trace = [];
        let frames = 0, error = Infinity, reason = '', lastProgress = 0, bestError = Infinity;
        let minimumY = w.position.y, maximumY = w.position.y, maxAirFrames = 0, airFrames = 0;
        for (; frames < (options.maxFrames || 2400); frames++) {
          const dx = x - w.position.x, dy = y + w.position.z;
          error = Math.hypot(dx, dy);
          if (error < .012) break;
          if (error < bestError - .005) { bestError = error; lastProgress = frames; }
          if (frames - lastProgress > 240) { reason = 'blocked or no forward progress for two simulated seconds'; break; }
          w.yaw = Math.atan2(-dx, dy); w.pitch = 0;
          w.update(1 / 120, {forward: Math.min(1, error / .6), strafe: 0});
          minimumY = Math.min(minimumY, w.position.y); maximumY = Math.max(maximumY, w.position.y);
          airFrames = w.onGround ? 0 : airFrames + 1; maxAirFrames = Math.max(maxAirFrames, airFrames);
          if (frames % 24 === 0) trace.push([w.position.x, -w.position.z, w.position.y, w.onGround]);
          if (w.position.y < -.75) { reason = 'fell below the site floor'; break; }
        }
        idle(45);
        error = Math.hypot(x - w.position.x, y + w.position.z);
        const position = [w.position.x, -w.position.z, w.position.y];
        const pass = error < .12 && w.onGround && Math.abs(w.position.y - h) < (options.heightTolerance || .055) && !reason;
        return {name, start, target: [x, y, h], position, frames, error, grounded: w.onGround, pass, reason, minimumY, maximumY, maxAirFrames, trace};
      },
      aim(id, desired) {
        const item = v.openings.items.find(i => i.id === id);
        if (!item) return {pass: false, reason: 'opening descriptor missing', available: v.openings.items.map(i => i.id)};
        if (item.value === desired && item.goal === desired) return {already: true, pass: true};
        const eye = w.eyePosition(v.camera.position.clone()), candidates = [];
        if (item.handle) candidates.push(item.handle.clone().applyMatrix4(item.parts[0].group.matrixWorld));
        for (const f of [.5, .25, .75, .1, .9]) {
          const p = item.start.clone().addScaledVector(item.axis, item.width * f);
          p.y = Math.max(item.start.y + .2, Math.min(item.start.y + item.height - .2, eye.y));
          candidates.push(p);
        }
        const observed = [];
        for (const p of candidates) {
          const d = p.clone().sub(eye), planar = Math.hypot(d.x, d.z);
          w.yaw = Math.atan2(-d.x, -d.z); w.pitch = Math.atan2(d.y, planar);
          v.openings.updateTarget(); observed.push(v.openings.target?.id || null);
          if (v.openings.target?.id === id) { v.canvas.focus(); return {pass: true, id, value: item.value, position: [w.position.x, -w.position.z, w.position.y]}; }
        }
        return {pass: false, reason: 'opening not selectable from walked approach', observed, position: [w.position.x, -w.position.z, w.position.y], value: item.value};
      },
      settleDoor(id, wanted) {
        const item = v.openings.items.find(i => i.id === id);
        const before = item.value;
        for (let i = 0; i < 120; i++) { v.openings.update(1 / 120); w.update(1 / 120, {forward: 0, strafe: 0}); }
        return {before, value: item.value, goal: item.goal, wanted, pass: item.value === wanted && item.goal === wanted, message: v.openings.message};
      }
    };
    return {position: [w.position.x, -w.position.z, w.position.y], supported: w.onGround, carVisible: v.carVisible, planHash: v.data.planHash, settings: w.s, openings: v.openings.items.map(i => ({id: i.id, initial: i.value, clearWidth: i.clearWidth}))};
  }, upperOnly);
  results.initial = initial;
  check('Viewer loaded the current generated project', initial.planHash === building.planHash, initial.planHash);
  check('Initial arrival settles on the real floor with the parked car visible', initial.supported && initial.carVisible, initial.position);

  if (!upperOnly) {
  await walk('Street approach to gate', 9.45, -1.0, -.3);
  await door('arrival-sliding-gate', 1, true);
  await walk('Through east gate onto lower porch', 9.45, 1.0, -.1524);
  await walk('Walk beside the parked car', 9.45, 5.35, -.1524);
  await walk('Step onto raised veranda', 9.45, 6.65, 0);
  await walk('Drawing room door approach', 8.95, 7.15, 0);
  await door('drawing-veranda-only', 1);
  await walk('Enter retained independent drawing room', 8.95, 8.75, 0);
  await walk('Return from drawing room to veranda', 8.95, 7.15, 0);
  await door('drawing-veranda-only', 0);
  await walk('Approach the infilled extra opening',7.8,7.5,0);
  const infill = await page.evaluate(() => {
    const w = window.__ff.viewer.walker, start = [w.position.x,-w.position.z,w.position.y];
    w.yaw = 0;
    for (let i=0;i<180;i++) w.update(1/120,{forward:1,strafe:0});
    for (let i=0;i<45;i++) w.update(1/120,{forward:0,strafe:0});
    return {start,position:[w.position.x,-w.position.z,w.position.y],grounded:w.onGround};
  });
  check('New infill blocks the unwanted veranda shortcut',infill.grounded && infill.position[1] < 8.05 && infill.position[1] > 7.5,infill);
  if (!(infill.grounded && infill.position[1] < 8.05)) throw Error('Extra opening remains traversable.');
  await walk('Shifted living entrance approach', 8.35, 7.0, 0);
  await door('living-veranda-wood', 1, true);
  await walk('Through shifted living entrance', 6.3, 7.0, 0);
  await walk('Inner insect-screen handle approach',6.8,6.45,0);
  await door('living-veranda-mesh', 1, true);
  await walk('Return from screen control to living',6.3,7.0,0);
  await screenshot('ground-living-arrival');

  for (const [name, x, y] of [
    ['Living circulation',6.2,7.2],['Rear turn approach',6.2,7.8],['Before closed extra opening',6.45,8.15],
    ['Pass safely behind the new infill',6.9375,8.55],['Rear corridor approach',7.5,9],
    ['Retained lobby entrance',7.7428,9.4],['Retained rear lobby',7.7428,10.5],['Caregiver door approach',7.7428,12.05]
  ]) await walk(name,x,y,0);
  await door('caregiver-lobby',1);
  await walk('Enter caregiver room from retained rear lobby',9.35,12.05,0);
  await walk('Return to rear lobby',7.7428,12.05,0);
  await door('caregiver-lobby',0);
  for (const [x,y] of [[7.7428,10.5],[7.7428,9.4],[7.5,9],[6.9375,8.55],[6.45,8.15],[6.2,7.8],[6.2,7.2]]) await walk('Return along rear lobby route',x,y,0);

  await walk('Shifted ICU wooden-door handle approach',5.65,6.65,0);
  await door('icu-glass-living-wood',1,true);
  await walk('Shifted ICU glass-door approach',6.2,6.65,0);
  await door('icu-glass-living',1,true);
  await walk('Enter ICU through shifted wooden and glass connection',6.2,5.25,0);
  await walk('ICU veranda-glass approach',7.95,5.25,0);
  await door('icu-veranda-glass',1,true);
  await walk('ICU directly to veranda',7.95,6.65,0);
  await walk('Veranda back into ICU',7.95,5.25,0);
  await walk('ICU back to living-door approach',6.2,5.25,0);
  await walk('Return from ICU to living',6.2,6.65,0);

  // The revised coffee-table position preserves this route above the dining furniture.
  for (const [name,x,y,h] of [
    ['Above dining circulation',5.9,7.65,0],['Clear dining to pantry aisle',3.7,7.65,0],
    ['Beside ground stair',1.9,7.65,0],['Ground stair start approach',1.9,5.6,0],
    ['Ground south flight',.7,5.6,.35],['Ground west flight landing',.7,8.35,1.575],
    ['First-floor stair arrival',5.7,8.35,3.508]
  ]) await walk(name,x,y,h);
  } else await walk('First-floor interior arrival',5.7,8.35,3.508);
  for (const [name,x,y,h] of [
    ['First interior connector',5.7,7.15,3.508],
    ['Internal upper-stair approach',4.45,7.15,3.508],['Upper south-flight landing',.7,7.15,5.262],
    ['Upper turn landing',.7,8.35,5.262],['Second-floor indoor arrival',4.675,8.35,7.016]
  ]) await walk(name,x,y,h);
  await screenshot('second-indoor-arrival');
  await door('s2-hall-entry',1,true);
  await walk('Second-floor hall entry',4.675,9.7,7.016);
  await walk('Second-floor hall garden-door approach',4.675,13.25,7.016);
  await door('s2-hall-garden',1,true);
  await walk('Hall to roof garden terrace',6.1,13.25,7.016);
  await screenshot('second-garden-terrace');
  await walk('Return from garden into hall',4.675,13.25,7.016);
  await walk('Hall back to indoor landing',4.675,8.35,7.016);
  await walk('Indoor terrace-door operating clearance',4.675,8.2,7.016);
  await door('s2-stair-terrace-proposed',1,true);
  await walk('Indoor terrace-door approach',4.675,7.15,7.016);
  await walk('Indoor landing directly to terrace',5.95,7.15,7.016);
  await walk('Terrace back to indoor landing',4.675,7.15,7.016);
  await walk('Step clear of terrace door before closing',4.675,8.2,7.016);
  await door('s2-stair-terrace-proposed',0);
  await walk('Second-floor stair descent approach',4.675,8.35,7.016);
  for (const [name,x,y,h] of [
    ['Descend upper north flight',.7,8.35,5.262],['Return across intermediate landing',.7,7.15,5.262],
    ['Descend upper south flight',4.25,7.15,3.508],['Back in first-floor interior',5.7,7.15,3.508],
    ['First arrival for ground descent',5.7,8.35,3.508]
  ]) await walk(name,x,y,h);
  if (!upperOnly) for (const [name,x,y,h] of [
    ['Descend to ground stair landing',.7,8.35,1.575],
    ['Descend ground west flight',.7,5.6,.35],['Ground stair exit',1.9,5.6,0],
    ['Ground side aisle return',1.9,7.65,0],['Ground dining aisle return',3.7,7.65,0],
    ['Ground living return',5.9,7.65,0]
  ]) await walk(name,x,y,h);
  await screenshot('completed-round-trip');
  check(`${upperOnly ? 'First interior' : 'Ground → first'} → second hall and terrace → ${upperOnly ? 'first interior' : 'ground'} completed without teleportation`,true,{initialSpawns:1,laterTeleports:0});
  check('No browser runtime errors',results.errors.length===0,results.errors);
} catch (error) {
  results.failure = String(error?.stack || error);
  console.error(results.failure);
  if (page) { try { await screenshot('failure'); } catch {} }
} finally {
  results.finished = new Date().toISOString();
  results.passed = !results.failure && !results.errors.length && results.checks.length>0 && results.checks.every(c=>c.pass);
  writeFileSync(resolve(out,'runtime-acceptance.json'),JSON.stringify(results,null,2)+'\n');
  await browser.close();
}
if (!results.passed) process.exitCode=1;
