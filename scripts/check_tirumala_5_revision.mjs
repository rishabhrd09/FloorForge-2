// Acceptance of the approved Tirumala 5 revision on the real, generated geometry.
// One arrival spawn; every subsequent floor change uses walker.update(), never teleport.
// Run after build_tirumala_5.py with the same Node runtime used for the viewer checks.
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

function inspectAtriumRayGeometry() {
  const v = window.__ff.viewer, Vector = v.camera.position.constructor;
  v.root.updateMatrixWorld(true);
  const samples = [v.data.cameras.ground_skylight.position.slice(0,2),[2.1,6.4],[4.5,6.4],[2.1,7.4],[4.5,7.4]]
    .map(([x,y]) => ({origin: [x,y,1.63], hits: []}));
  for (const mesh of v.meshes) {
    const geometry = mesh.geometry, position = geometry.getAttribute('position');
    if (!position) continue;
    const bucket = mesh.userData.bucket || {}, material = mesh.material;
    const transparent = bucket.transparent || material.opacity < .98 || material.transmission > 0;
    const world = new Float64Array(position.count * 3), p = new Vector();
    for (let i=0;i<position.count;i++) {
      p.fromBufferAttribute(position,i).applyMatrix4(mesh.matrixWorld);
      world.set([p.x,p.y,p.z],i*3);
    }
    const index = geometry.index, count = index ? index.count : position.count;
    for (let i=0;i<count;i+=3) {
      const ia=(index ? index.getX(i) : i)*3, ib=(index ? index.getX(i+1) : i+1)*3, ic=(index ? index.getX(i+2) : i+2)*3;
      const ax=world[ia], az=world[ia+2], bx=world[ib], bz=world[ib+2], cx=world[ic], cz=world[ic+2];
      const den=(bz-cz)*(ax-cx)+(cx-bx)*(az-cz);
      if (Math.abs(den)<1e-12) continue;
      for (const sample of samples) {
        const [x,y,originHeight]=sample.origin, z=-y;
        if (x<Math.min(ax,bx,cx)-1e-8 || x>Math.max(ax,bx,cx)+1e-8 || z<Math.min(az,bz,cz)-1e-8 || z>Math.max(az,bz,cz)+1e-8) continue;
        const u=((bz-cz)*(x-cx)+(cx-bx)*(z-cz))/den;
        const vv=((cz-az)*(x-cx)+(ax-cx)*(z-cz))/den, w=1-u-vv;
        if (Math.min(u,vv,w)<-1e-8) continue;
        const height=u*world[ia+1]+vv*world[ib+1]+w*world[ic+1];
        if (height<=originHeight+1e-5) continue;
        const hit={height:Number(height.toFixed(5)),material:bucket.material,floor:bucket.floor,roles:bucket.roles,transparent:!!transparent};
        if (!sample.hits.some(h => h.material===hit.material && Math.abs(h.height-hit.height)<.0001)) sample.hits.push(hit);
      }
    }
  }
  for (const sample of samples) {
    sample.hits.sort((a,b)=>a.height-b.height);
    sample.opaqueObstructions=sample.hits.filter(h=>!h.transparent);
    sample.reachesWeatherGlass=sample.hits.some(h=>h.material==='t5-rooflight-glass' && h.transparent && h.height>10.546);
    sample.pass=sample.reachesWeatherGlass && sample.opaqueObstructions.length===0;
  }
  return {planHash:v.data.planHash,method:'Upward vertical ray / actual transformed render-mesh triangles, including invisible buckets',samples,
    passed:samples.every(s=>s.pass),roofEquipment:v.data.roofEquipment,
    solarPanelCount:v.data.nodes.filter(n=>n.id.startsWith('t5-solar-module-') && n.id.endsWith('-backing')).length};
}

const root = resolve(import.meta.dirname, '..');
const upperOnly = process.argv.includes('--upper-only');
const out = resolve(root, process.env.T5_CHECK_OUT || `evidence/tirumala-5-revision${upperOnly ? '-upper' : ''}`);
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE || '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const building = JSON.parse(readFileSync(resolve(root, 'examples/gallery/tirumala-5/building.json'), 'utf8'));
const plan = building.planning.canonicalPlan;
const upper = building.planning.upperPlan;
const second = building.planning.secondPlan;
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
async function path(name, points, height) {
  for (const [i, point] of points.entries()) {
    await walk(`${name} ${i + 1}`, point[0] / 1000, point[1] / 1000,
      point.length > 2 ? point[2] / 1000 : height);
  }
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
  const retired = ['u-master-south','u-atrium-south','s2-hall-south','s2-stair-south-window-proposed'];
  const east = ['u-stair-east','s2-stair-east','s2-gallery-east'];
  const fresh = main?.a[0] === 7300 && Math.abs(icu?.a[0] - 5452.4) < .01 &&
    /skylit-atrium/.test(upper.revision) && second.stairs.some(s => s.id.startsWith('s2-west-')) &&
    JSON.stringify(second.skylight?.boundsMm) === JSON.stringify([1675,6075,5000,7800]) &&
    Array.isArray(second.atriumOpening) &&
    retired.every(id=>!building.openings.some(o=>o.id===id)) &&
    east.every(id=>building.openings.some(o=>o.id===id)) &&
    building.openings.some(o => o.id === 's2-stair-terrace-proposed');
  check('Generated files contain the approved skylit atrium, east glazing and retained stacked stairs', fresh,
    {main: main?.a, icu: icu?.a, upperRevision: upper.revision,
      internalTerraceDoor: building.openings.some(o => o.id === 's2-stair-terrace-proposed')});
  if (!fresh) throw Error('Fresh Tirumala 5 build required; old geometry was not tested as the new revision.');
  const guest = upper.rooms.find(r => r.id === 'u-bedroom');
  const expectedGuestArea = (3082.4 * 5050 + 304.8 * 2850) / 1e6;
  check('North bedroom gains one foot only at its front section, retaining the rear wall',
    Math.abs(guest.area_m2 - expectedGuestArea) < .00001 &&
    guest.polygon.some(p => Math.abs(p[0] - 8045.2) < .01) &&
    guest.polygon.some(p => Math.abs(p[0] - 8350) < .01),
    {areaSqFt: guest.area_m2 / .09290304, polygon: guest.polygon});
  check('The first-floor connector is the approved indoor east-edge bridge',
    upper.bridgeClearWidthMm === 1100 && upper.bridgeGrossWidthMm === 1200 &&
    upper.circulationPaths.arrival_to_stair.every(p => p[1] >= 4875),
    {clearWidthMm: upper.bridgeClearWidthMm, route: upper.circulationPaths.arrival_to_stair});
  const hallEntry = building.openings.find(o => o.id === 's2-hall-entry');
  const indoorLanding = building.spaces.find(s => s.id === 's2-indoor-landing');
  check('Second-floor arrival is enclosed and roofed with the widened hall doorway',
    indoorLanding?.enclosed === true && indoorLanding?.roofed === true &&
    hallEntry?.width === 1000 && hallEntry?.a[1] === 9050 && hallEntry?.b[1] === 10050,
    {enclosed: indoorLanding?.enclosed, roofed: indoorLanding?.roofed,
      openingMm: hallEntry?.width, jambClearMm: hallEntry?.width - 110});

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
  const skyRays = await page.evaluate(inspectAtriumRayGeometry);
  results.atriumRayGeometry = skyRays;
  check('Ground-to-roof rays reach weather glazing without opaque slab, ceiling or soffit obstructions',
    skyRays.passed && skyRays.planHash === building.planHash, skyRays);
  check('Four actual solar panels remain on the highest hall roof',
    skyRays.solarPanelCount === 4 && skyRays.roofEquipment?.solarModules === 4, skyRays.roofEquipment);
  if (!skyRays.passed) throw Error('Rendered geometry blocks the reviewed ground-to-skylight sightline.');

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
  // The guest extension is stepped: the widened front and the retained rear
  // passage must both be usable with real collision and furnished rooms.
  await walk('First gallery toward enlarged guest',7.4,8.35,3.508);
  await walk('Enlarged guest doorway approach',7.4,8.7,3.508);
  await door('u-bedroom-door',1,true);
  await walk('Enter enlarged north bedroom',8.65,8.7,3.508);
  // The inward-opening leaf lies across y=8.25 to x=8.8702 when open.
  // Walk around its free end before testing the new front floor area.
  await walk('Pass around open bedroom door',9.25,8.7,3.508);
  await walk('Bedroom front beyond open door swing',9.25,7.25,3.508);
  await walk('Use widened bedroom front portion',8.35,7.25,3.508);
  await walk('Return around bedroom door free end',9.25,7.25,3.508);
  await walk('Return behind open bedroom door',9.25,8.7,3.508);
  await walk('Return through enlarged bedroom',8.65,8.7,3.508);
  await walk('Back to guest gallery',7.4,8.7,3.508);
  await door('u-bedroom-door',0);
  const officeRoute = upper.circulationPaths.arrival_to_office.slice(2,-1);
  await path('Retained rear gallery to office',officeRoute,3.508);
  await door('u-office-door',1,true);
  await walk('Enter retained first-floor office',8.8,12.025,3.508);
  await walk('Return from office to retained three-foot gallery',7.7428,12.025,3.508);
  await door('u-office-door',0);
  await path('Return through stepped bedroom gallery',[...officeRoute].reverse(),3.508);
  await walk('Return to main first-floor gallery',7.4,8.35,3.508);
  await walk('Return to first-floor stair arrival',5.7,8.35,3.508);
  for (const [name,x,y,h] of [
    ['First gallery to indoor bridge',6.9,8.35,3.508],
    ['Turn onto east-edge indoor bridge',6.9,5.475,3.508],
    ['Follow indoor bridge to stacked stair start',1.9,5.55,3.508],
    ['Stacked south starter landing',.7,5.55,3.858],
    ['Stacked west flight landing',.7,8.35,5.083],
    ['Stacked north flight upper landing',3.95,8.35,6.658],
    ['Second-floor indoor arrival',5.7,8.35,7.016],
  ]) await walk(name,x,y,h);
  await screenshot('second-indoor-arrival');
  for (const [name,x,y] of [
    ['Enclosed north-side route around atrium',5.8,8.35],
    ['Expanded gallery beside skylight opening',5.8,5.475],
    ['New east gallery in front of large glazing',3.35,5.475],
  ]) await walk(name,x,y,7.016);
  const atriumGuard = await page.evaluate(() => {
    const w=window.__ff.viewer.walker, start=[w.position.x,-w.position.z,w.position.y];
    w.yaw=0; w.pitch=0;
    let minimumHeight=w.position.y;
    for(let i=0;i<180;i++) { w.update(1/120,{forward:1,strafe:0}); minimumHeight=Math.min(minimumHeight,w.position.y); }
    for(let i=0;i<45;i++) w.update(1/120,{forward:0,strafe:0});
    const position=[w.position.x,-w.position.z,w.position.y];
    return {start,position,minimumHeight,grounded:w.onGround,
      pass:w.onGround && Math.abs(w.position.y-7.016)<.055 && minimumHeight>6.96 && position[1]<6.075 && position[1]>5.475};
  });
  results.atriumGuard = atriumGuard;
  check('Atrium east-edge guard physically blocks a walking approach to the open shaft',atriumGuard.pass,atriumGuard);
  if (!atriumGuard.pass) throw Error('Atrium guarding failed real walking collision.');
  await screenshot('second-atrium-guard');
  await walk('Return from atrium edge to clear gallery',3.35,5.475,7.016);
  await walk('Use retained south end of indoor gallery',2.2,5.475,7.016);
  // Walk into the new south-end guard using real capsule input. The removed
  // dead-end slab must not remain as invisible support, nor may a visitor slip
  // around either end of the barrier into the stair/atrium opening.
  results.landingEndGuards = [];
  for (const attempt of [
    {name:'South endpoint blocks ordinary walking',yaw:Math.PI/2},
    {name:'South endpoint blocks running',yaw:Math.PI/2,run:true},
    {name:'South endpoint blocks crouched walking',yaw:Math.PI/2,crouch:true},
    {name:'Atrium-side endpoint corner blocks diagonal running',yaw:Math.PI/4,run:true},
    {name:'Window-side endpoint corner blocks diagonal crouching',yaw:3*Math.PI/4,crouch:true},
  ]) {
    await walk(`Approach: ${attempt.name}`,2.2,5.475,7.016);
    const guard = await page.evaluate(attempt => {
      const w=window.__ff.viewer.walker;
      const start=[w.position.x,-w.position.z,w.position.y],trace=[];
      w.yaw=attempt.yaw;w.pitch=0;
      let minimumHeight=w.position.y,minimumX=w.position.x;
      let minimumY=-w.position.z,maximumY=-w.position.z;
      for(let i=0;i<240;i++) {
        w.update(1/120,{forward:1,strafe:0,run:!!attempt.run,crouch:!!attempt.crouch});
        minimumHeight=Math.min(minimumHeight,w.position.y);
        minimumX=Math.min(minimumX,w.position.x);
        minimumY=Math.min(minimumY,-w.position.z);maximumY=Math.max(maximumY,-w.position.z);
        if(i%24===0)trace.push([w.position.x,-w.position.z,w.position.y,w.onGround]);
      }
      for(let i=0;i<45;i++)w.update(1/120,{forward:0,strafe:0});
      const position=[w.position.x,-w.position.z,w.position.y];
      return {name:attempt.name,start,position,minimumHeight,minimumX,minimumY,maximumY,
        grounded:w.onGround,trace,
        pass:w.onGround && Math.abs(w.position.y-7.016)<.055 && minimumHeight>6.96 &&
          minimumX>=1.675+w.s.radius-.06 && minimumY>4.875 && maximumY<6.075};
    },attempt);
    results.landingEndGuards.push(guard);
    check(attempt.name,guard.pass,guard);
    if(!guard.pass)throw Error(`Second-floor endpoint collision failed: ${attempt.name}`);
  }
  await walk('Return safely from endpoint corner',2.2,5.475,7.016);
  await walk('Endpoint review viewpoint reached by walking',2.8,5.475,7.016);
  await page.evaluate(()=>{const w=window.__ff.viewer.walker;w.yaw=Math.PI/2;w.pitch=-.1;});
  await screenshot('second-landing-endcap');
  for (const [name,x,y] of [
    ['Return through east gallery',5.8,5.475],
    ['Return beside north atrium guard',5.8,8.35],
    ['Enclosed second-floor hall approach',5.95,9.55],
  ]) await walk(name,x,y,7.016);
  await door('s2-hall-entry',1,true);
  await walk('Second-floor hall entry',4.675,9.55,7.016);
  // The open hall door projects west along y=10.05. Follow the actual
  // furnished-room aisle around its free end instead of through its leaf.
  await walk('Hall entry around open door free end',3.95,9.55,7.016);
  await walk('Hall clear of inward door swing',3.95,10.5,7.016);
  await walk('Hall furniture aisle beyond door swing',4.675,10.5,7.016);
  await walk('Second-floor hall garden-door approach',4.675,13.25,7.016);
  await door('s2-hall-garden',1,true);
  await walk('Hall to roof garden terrace',6.1,13.25,7.016);
  await screenshot('second-garden-terrace');
  await walk('Return from garden into hall',4.675,13.25,7.016);
  await walk('Hall return along furniture aisle',4.675,10.5,7.016);
  await walk('Hall return beyond inward door swing',3.95,10.5,7.016);
  await walk('Hall return around open door free end',3.95,9.55,7.016);
  await walk('Hall back to indoor-door approach',4.675,9.55,7.016);
  await walk('Hall back to indoor landing',5.95,9.55,7.016);
  await walk('Indoor terrace-door landing approach',5.95,8.55,7.016);
  await walk('Indoor terrace-door operating clearance',5.5,8.55,7.016);
  await door('s2-stair-terrace-proposed',1,true);
  await walk('Indoor landing directly to terrace',7.15,8.4,7.016);
  await walk('Terrace back to indoor landing',5.5,8.55,7.016);
  await door('s2-stair-terrace-proposed',0);
  await walk('Closed terrace door leaves atrium gallery approach clear',5.8,8.35,7.016);
  await walk('Use atrium gallery with terrace door closed',5.8,5.475,7.016);
  await walk('Return through atrium gallery with terrace door closed',5.8,8.35,7.016);
  await walk('Second-floor stair descent approach',5.7,8.35,7.016);
  for (const [name,x,y,h] of [
    ['Descend stacked arrival connector',3.95,8.35,6.658],
    ['Descend stacked north flight',.7,8.35,5.083],
    ['Descend stacked west flight',.7,5.55,3.858],
    ['Descend stacked south starter',1.9,5.55,3.508],
    ['Return along indoor bridge',6.9,5.475,3.508],
    ['Return to first-floor gallery',6.9,8.35,3.508],
    ['First arrival for ground descent',5.7,8.35,3.508],
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
