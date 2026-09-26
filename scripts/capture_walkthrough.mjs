// Evidence harness for the realistic viewer: renders exterior grades, the dollhouse and a first-person walk
// through the bundled examples with the committed web/viewer.js, and records what was run.
//
//   node scripts/capture_walkthrough.mjs [--out evidence] [--size 1600x900] [--quality high] [--only stills|preview]
//
// Needs Node 18+ and Playwright with a Chromium build (set PLAYWRIGHT_MODULE to its index.mjs when the
// package is not resolvable from this folder). Software WebGL (SwiftShader) is used so the run is
// reproducible on a headless host; it verifies composition and behaviour, not real-GPU colour or frame rate.
import { readFileSync, writeFileSync, mkdirSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const arg = (name, fallback) => { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : fallback; };
const OUT = resolve(arg('out', join(ROOT, 'evidence')));
const [W, H] = arg('size', '1600x900').split('x').map(Number);
const QUALITY = arg('quality', 'high');
const ONLY = arg('only', 'all'); // all | stills | preview
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');

// Each shot runs a snippet against the page helpers below, then renders one frame and saves it.
const EXTERIOR = [
  ['realistic-hero', "v.hud.setLocked(true); v.setGrade('day'); v.reset()"],
  ['realistic-front', "v.setView('front')"],
  ['realistic-entrance', "v.setView('entrance')"],
  ['realistic-golden', "v.setGrade('golden'); v.reset()"],
  ['realistic-blue-hour', "v.setGrade('dusk'); v.reset()"],
  ['preview-dollhouse-ground', "v.setGrade('day'); v.setMode('dollhouse')"],
  ['preview-dollhouse-upper', 'v.setFloor(1)'],
];
const WALK = [
  ['walk-arrival', "v.setGrade('day'); v.setMode('walk'); v.hud.setLocked(true); walk(1, [])"],
  ['walk-living-day', 'tp(3.2, 3.9, 0, -95)'],
  ['walk-kitchen-day', 'tp(4.0, 7.0, 0, 128)'],
  ['walk-stair', "tp(0.75, 0.9, 0, 0); walk(40, ['KeyW']); walk(20, ['KeyW']); walk(22, ['KeyD']); v.walker.yaw = Math.PI; v.walker.pitch = .12; walk(1, [])"],
  ['walk-bedroom-upper', 'tp(6.4, 9.5, 3.15, -35)'],
  ['walk-terrace', 'tp(7.6, 1.25, 3.15, 180)'],
  ['walk-living-blue-hour', "v.setGrade('dusk'); tp(3.2, 3.9, 0, -95)"],
  ['walk-bedroom-night', "v.setGrade('night'); tp(6.4, 9.5, 3.15, -35)"],
];
const COMPACT = [['realistic-compact', "v.hud.setLocked(true); v.setGrade('day'); v.reset()"]];

const page = (viewer, scene) => `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#222">
<div style="position:relative;width:${W}px;height:${H}px"><canvas id="c" tabindex="0" style="width:100%;height:100%;display:block;outline:none"></canvas></div>
<script>${viewer.replace(/<\/script/gi, '<\\/script')}</script><script id="scene" type="application/json">${scene.replace(/</g, '\\u003c')}</script>
<script>
window.__errors = []; addEventListener('error', (e) => __errors.push(String(e.message)));
const v = window.v = new FloorForgeViewer(document.getElementById('c'), { quality: '${QUALITY}' });
v.setScene(JSON.parse(document.getElementById('scene').textContent));
v.paused = true;
// Step the walker deterministically (fixed 1/30 s steps) instead of relying on wall-clock frames.
window.walk = (frames, keys, dt = 1 / 30) => {
  v.keys = new Set(keys);
  for (let i = 0; i < frames; i++) { v.walker.update(dt, v.readInput()); v.time += dt; }
  v.input.jump = false; v.keys = new Set();
  v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone()));
  v.camera.rotation.set(v.walker.pitch, v.walker.yaw, 0);
  v.floor = v.levelOf(v.walker.position.y); v.hudUpdate();
};
window.tp = (x, y, z, yawDeg) => { v.walker.teleport(new v.camera.position.constructor(x, z + .5, -y), yawDeg * Math.PI / 180, 0); walk(1, []); };
// One frame as the live loop would draw it, waiting for the room probe's metering read-back.
window.frame = async () => {
  v.resize(); v.adapt(30); v.updateProbe();
  if (v.env.probe && v.env.probe.statsReady) await v.env.probe.statsReady;
  v.adapt(30); v.vegetation?.update(v.time, v.camera); v.updateLights(true); v.composer.render(1 / 60);
};
</script></body></html>`;

async function run(browser, scenePath, shots, log) {
  const tab = await browser.newPage({ viewport: { width: W, height: H } });
  const errors = [];
  tab.on('pageerror', (e) => errors.push(e.message));
  tab.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  const started = Date.now();
  await tab.setContent(page(readFileSync(join(ROOT, 'web/viewer.js'), 'utf8'), readFileSync(scenePath, 'utf8')), { waitUntil: 'load', timeout: 300000 });
  const gl = await tab.evaluate(() => { const g = window.v.gl, e = g.getExtension('WEBGL_debug_renderer_info'); return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER); });
  for (const [name, code] of shots) {
    const t = Date.now();
    await tab.evaluate(`(() => { const v = window.v; ${code}; })()`);
    await tab.evaluate(() => window.frame());
    await tab.screenshot({ path: join(OUT, name + '.png'), timeout: 120000 });
    const state = await tab.evaluate(() => { const v = window.v; return { mode: v.mode, grade: v.gradeName, room: v.hud.visible ? v.hud.last : null, probe: Boolean(v.env.probe), exposure: +v.gradeEffect.uniforms.get('exposure').value.toFixed(3) }; });
    log.shots.push({ file: name + '.png', scene: scenePath.replace(ROOT + '/', ''), ms: Date.now() - t, ...state });
    console.log(name, Date.now() - t, 'ms');
  }
  errors.push(...await tab.evaluate(() => window.__errors));
  log.errors.push(...errors);
  log.renderer = gl;
  log.load_ms = (log.load_ms || 0) + (Date.now() - started);
  await tab.close();
}

// The self-contained offline preview, opened from disk exactly as a user double-clicks it.
async function preview(browser) {
  const tab = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  tab.on('pageerror', (e) => errors.push(e.message));
  tab.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await tab.goto('file://' + join(ROOT, 'examples/demo/preview.html'), { waitUntil: 'load', timeout: 300000 });
  await tab.waitForFunction(() => window.__ff && (window.__ff.ready || window.__ff.error), null, { timeout: 300000 });
  const metrics = await tab.evaluate(() => { const v = window.__ff.viewer; v.paused = true; v.composer.render(0); return { ready: Boolean(window.__ff.ready), error: window.__ff.error || null, schema: window.__ff.scene?.schema, nodes: window.__ff.scene?.nodes?.length, status: document.getElementById('status')?.textContent }; });
  await tab.screenshot({ path: join(OUT, 'preview-exterior.png') });
  // The offline page's "Blender GLB" button: the textured, planted scene as binary glTF.
  const [download] = await Promise.all([tab.waitForEvent('download', { timeout: 600000 }), tab.click('#glbBtn')]);
  const saved = await download.path();
  metrics.presentation_glb = { file: download.suggestedFilename(), bytes: statSync(saved).size, magic: readFileSync(saved).subarray(0, 4).toString('latin1') };
  if (metrics.presentation_glb.magic !== 'glTF') errors.push('Blender GLB download is not binary glTF');
  await tab.click('[data-mode="walk"]');
  metrics.walk = await tab.evaluate(() => { const v = window.__ff.viewer; v.paused = true; v.walker.update(1 / 30, v.readInput()); v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone())); v.camera.rotation.set(v.walker.pitch, v.walker.yaw, 0); v.hudUpdate(); v.composer.render(0); return { mode: v.mode, badge: v.hud.last }; });
  await tab.screenshot({ path: join(OUT, 'preview-walk.png') });
  // Live loop: the real requestAnimationFrame loop and keyboard, at performance quality so software WebGL
  // keeps up. Hold W from the footpath outside the gate, then press Space; sample the walker, room and exposure.
  const sample = () => tab.evaluate(() => { const v = window.__ff.viewer, w = v.walker; return { t: +performance.now().toFixed(0), x: +w.position.x.toFixed(3), y: +w.position.y.toFixed(3), z: +w.position.z.toFixed(3), onGround: w.onGround, room: v.hud.last, indoor: +(v.indoor || 0).toFixed(2), probe: Boolean(v.env.probe), exposure: +v.gradeEffect.uniforms.get('exposure').value.toFixed(3) }; });
  await tab.setViewportSize({ width: 480, height: 300 });
  await tab.evaluate(() => { const v = window.__ff.viewer; v.setQuality('performance'); v.spawn('arrival'); v.paused = false; v.hud.setLocked(true); v.canvas.focus(); });
  metrics.live = [await sample()];
  await tab.keyboard.down('KeyW');
  for (let i = 0; i < 45; i++) {
    await tab.waitForTimeout(2000);
    const s = await sample();
    metrics.live.push(s);
    if (s.indoor > .9 && s.probe) break;
  }
  await tab.keyboard.up('KeyW');
  const standing = await sample();
  await tab.keyboard.press('Space');
  const air = [];
  for (let i = 0; i < 14; i++) { await tab.waitForTimeout(150); air.push(await sample()); }
  metrics.live.push(standing, ...air);
  const live = metrics.live;
  metrics.live_summary = { entered: live.some((s) => s.indoor > .5), probe: live.some((s) => s.probe), jumped: air.some((s) => !s.onGround && s.y > standing.y + .05), peak_jump_m: +Math.max(0, ...air.map((s) => s.y - standing.y)).toFixed(3), rooms: [...new Set(live.map((s) => s.room))] };
  await tab.close();
  const record = { method: 'Headless Chromium opened examples/demo/preview.html from disk (file://), software WebGL (SwiftShader). Real GPU unverified.', metrics, errors };
  writeFileSync(join(OUT, 'browser-preview.json'), JSON.stringify(record, null, 2) + '\n');
  return errors;
}

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--allow-file-access-from-files'] });
const log = { method: `Headless Chromium, software WebGL (SwiftShader), ${W}x${H}, quality ${QUALITY}. The committed web/viewer.js renders each example's scene.json; walking uses fixed 1/30 s steps. Composition and behaviour evidence only: not real-GPU colour, frame-rate or native-browser acceptance.`, shots: [], errors: [] };
try {
  // Run one example at a time: several software renderers in parallel starve each other.
  if (ONLY !== 'preview') {
    await run(browser, join(ROOT, 'examples/demo/scene.json'), EXTERIOR, log);
    await run(browser, join(ROOT, 'examples/demo/scene.json'), WALK, log);
    await run(browser, join(ROOT, 'examples/compact/scene.json'), COMPACT, log);
  }
  if (ONLY !== 'stills') log.errors.push(...await preview(browser));
} finally { await browser.close(); }
if (ONLY !== 'preview') writeFileSync(join(OUT, 'walkthrough-capture.json'), JSON.stringify(log, null, 2) + '\n');
if (log.errors.length) { console.error(log.errors); process.exit(1); }
