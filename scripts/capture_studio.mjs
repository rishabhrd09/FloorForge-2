// Studio browser evidence: starts the real loopback server, drives the studio UI end to end in headless
// Chromium and records screenshots plus checks in evidence/studio-browser.json.
//
//   node scripts/capture_studio.mjs [--out evidence] [--python .venv/bin/python]
//
// Needs Node 18+ and Playwright with a Chromium build (set PLAYWRIGHT_MODULE to its index.mjs when the
// package is not resolvable from this folder). Software WebGL (SwiftShader) keeps it runnable headless; it is
// not a real-GPU, native-browser or installer sign-off.
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, readFileSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const arg = (name, fallback) => { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : fallback; };
const OUT = resolve(arg('out', join(ROOT, 'evidence')));
const PYTHON = arg('python', join(ROOT, '.venv/bin/python'));
const PORT = Number(arg('port', 8799));
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');

const work = mkdtempSync(join(tmpdir(), 'ff-studio-'));
const server = spawn(PYTHON, ['-m', 'floorforge', 'serve', '--no-browser', '--port', String(PORT), '--out', work], { cwd: ROOT, stdio: 'ignore' });
const url = `http://127.0.0.1:${PORT}`;
for (let i = 0; i < 60; i++) {
  try { if ((await fetch(url + '/api/session')).ok) break; } catch { /* starting */ }
  await new Promise((r) => setTimeout(r, 500));
}

const checks = [], errors = [], requests = [];
const check = (name, passed, details) => { checks.push(details ? { check: name, passed: Boolean(passed), details } : { check: name, passed: Boolean(passed) }); console.log(passed ? 'PASS' : 'FAIL', name); };
const still = (page) => page.evaluate(() => { const v = window.__ffApp.viewer; v.paused = true; v.composer.render(0); });
mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
let gl = null;
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1024 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('response', (r) => { const u = new URL(r.url()); if (u.origin === url && (u.pathname.startsWith('/api/') || u.pathname.endsWith('.json'))) requests.push({ path: u.pathname, method: r.request().method(), status: r.status() }); });
  await page.goto(url + '/', { waitUntil: 'load', timeout: 180000 });
  await page.waitForFunction(() => window.__ffApp && window.__ffApp.viewer && window.__ff && window.__ff.ready, null, { timeout: 300000 });
  const scene = await page.evaluate(() => ({ schema: window.__ff.scene.schema, theme: window.__ff.scene.exterior_theme }));
  check('bundled project + realistic renderer initialised', scene.schema === 'floorforge.scene/0.4', scene);
  await still(page);
  await page.screenshot({ path: join(OUT, 'studio-desktop.png') });
  // The 3D view takes most of the height and the scrolling panel never runs under the status bar.
  const layout = async () => page.evaluate(() => { const box = (q) => document.querySelector(q).getBoundingClientRect(); return { canvas: Math.round(box('.canvas-wrap').height), panelBottom: Math.round(box('#home-panel').bottom), statusTop: Math.round(box('.status-bar').top), scroll: document.documentElement.scrollHeight - innerHeight }; });
  const roomy = await layout();
  check('viewer fills the studio at 1440×1024', roomy.canvas >= 520 && roomy.panelBottom <= roomy.statusTop + 1 && roomy.scroll <= 0, roomy);
  await page.setViewportSize({ width: 1366, height: 768 });
  await page.waitForTimeout(300);
  const laptop = await layout();
  check('1366×768 laptop layout keeps the panel clear of the status bar', laptop.canvas >= 330 && laptop.panelBottom <= laptop.statusTop + 1 && laptop.scroll <= 0, laptop);
  await page.setViewportSize({ width: 1440, height: 1024 });
  await page.waitForTimeout(300);

  await page.click('[data-mode="walk"]');
  await page.evaluate(() => { const v = window.__ffApp.viewer; v.paused = true; v.hud.setLocked(true); v.walker.update(1 / 30, v.readInput()); v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone())); v.camera.rotation.set(v.walker.pitch, v.walker.yaw, 0); v.hudUpdate(); v.composer.render(0); });
  const hud = await page.evaluate(() => window.__ffApp.viewer.hud.last);
  check('walk mode opens at the arrival with the room badge', hud && hud.includes('|'), { badge: hud });
  await page.screenshot({ path: join(OUT, 'studio-walk.png') });
  await page.click('[data-mode="solid"]');

  // Large view: the 3D fills the whole window with its controls; the zoom buttons glide the camera in.
  await page.click('#fullscreen');
  await page.waitForTimeout(400);
  const distance = () => page.evaluate(() => { const v = window.__ffApp.viewer; for (let i = 0; i < 40 && v.zoomAnim; i++) v.stepZoom(performance.now() + 1000); return v.camera.position.distanceTo(v.controls.target); });
  const far = await distance();
  await page.click('#zoom-in');
  const near = await distance();
  const large = await page.evaluate(() => { const r = document.querySelector('.canvas-wrap').getBoundingClientRect(); return { width: Math.round(r.width), height: Math.round(r.height), window: [innerWidth, innerHeight], controlsInside: !!document.querySelector('.canvas-wrap .canvas-tools') }; });
  await page.evaluate(() => { const v = window.__ffApp.viewer; v.paused = true; v.resize(); v.updateLights(true); v.composer.render(0); });
  await page.screenshot({ path: join(OUT, 'studio-large-view.png') });
  check('large view fills the window with its controls and zooms in', large.width === large.window[0] && large.height === large.window[1] && large.controlsInside && near < far * .8, { ...large, zoom_m: [+far.toFixed(2), +near.toFixed(2)] });
  // Software WebGL needs tens of seconds for a 3840-pixel frame, so allow for it.
  const [still4k] = await Promise.all([page.waitForEvent('download', { timeout: 600000 }), page.click('#snapshot', { timeout: 600000 })]);
  const png = join(work, 'still.png');
  await still4k.saveAs(png);
  const header = readFileSync(png);
  check('Capture saves a large 3840-pixel still', header.readUInt32BE(16) === 3840, { file: still4k.suggestedFilename(), width: header.readUInt32BE(16), height: header.readUInt32BE(20) });
  await page.click('#zoom-out');
  await page.click('#fullscreen');
  await page.waitForTimeout(300);

  // Focus: the home alone fills the whole screen from the current direction (and from the top); leaving Focus
  // brings the street back. The wider view folds the brief panel away so the home takes the width.
  const frame = () => page.evaluate(() => {
    const v = window.__ffApp.viewer; v.paused = true; if (v.resized) v.resize();
    for (let i = 0; i < 40 && v.zoomAnim; i++) v.stepZoom(performance.now() + 1000);
    v.controls.update();
    const b = v.houseBox(), c = v.camera; c.updateMatrixWorld();
    let x0 = 1, x1 = -1, y0 = 1, y1 = -1;
    for (let i = 0; i < 8; i++) { const p = b.min.clone(); if (i & 1) p.x = b.max.x; if (i & 2) p.y = b.max.y; if (i & 4) p.z = b.max.z; p.project(c); x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y); }
    v.updateLights(true); v.vegetation?.update(v.time, v.camera); v.composer.render(0);
    const r = document.querySelector('.canvas-wrap').getBoundingClientRect();
    return { span: [+((x1 - x0) / 2).toFixed(3), +((y1 - y0) / 2).toFixed(3)], inside: x0 > -1 && x1 < 1 && y0 > -1 && y1 < 1, context: v.context.visible, focus: !!v.focus, wrap: [Math.round(r.width), Math.round(r.height)], window: [innerWidth, innerHeight] };
  });
  await page.click('#focus');
  await page.waitForTimeout(400);
  const focus = await frame();
  await page.screenshot({ path: join(OUT, 'studio-focus.png') });
  await page.click('.canvas-wrap [data-view="top"]');
  await page.waitForTimeout(200);
  const topView = await frame();
  await page.screenshot({ path: join(OUT, 'studio-focus-top.png') });
  // A view chosen while a framing glide is still under way takes its own direction, not the glide's.
  await page.click('.canvas-wrap [data-view="hero"]');
  await page.click('#zoom-fit');
  await page.click('.canvas-wrap [data-view="top"]');
  const midGlide = await page.evaluate(() => { const v = window.__ffApp.viewer; const d = v.camera.position.clone().sub(v.controls.target).normalize(); return { up: +d.y.toFixed(3), gliding: !!v.zoomAnim }; });
  check('Focus shows the home alone filling the whole screen', focus.focus && !focus.context && focus.inside && Math.max(...focus.span) >= .75 && focus.wrap[0] === focus.window[0] && focus.wrap[1] === focus.window[1] && topView.inside && midGlide.up > .95 && !midGlide.gliding, { focus, top: topView, view_chosen_mid_glide: midGlide });
  await page.click('#focus');
  await page.waitForTimeout(300);
  const unfocused = await page.evaluate(() => ({ focus: !!window.__ffApp.viewer.focus, context: window.__ffApp.viewer.context.visible, expanded: document.querySelector('.canvas-wrap').classList.contains('expanded') }));
  await page.click('[data-view="hero"]');
  const narrow = await page.evaluate(() => Math.round(document.querySelector('.canvas-wrap').getBoundingClientRect().width));
  await page.click('#brief-toggle');
  await page.waitForTimeout(300);
  const wide = await frame();
  await page.screenshot({ path: join(OUT, 'studio-wide.png') });
  await page.click('#brief-toggle');
  await page.waitForTimeout(300);
  check('wider view folds the brief away; leaving Focus brings the street back', wide.wrap[0] >= narrow + 250 && !unfocused.focus && unfocused.context && !unfocused.expanded, { canvas_px: [narrow, wide.wrap[0]], unfocused });

  const [download] = await Promise.all([page.waitForEvent('download', { timeout: 600000 }), page.click('#export-glb')]);
  const glb = join(work, 'presentation.glb');
  await download.saveAs(glb);
  const glbBytes = statSync(glb).size;
  check('Blender GLB export downloads a textured binary glTF', readFileSync(glb).subarray(0, 4).toString('latin1') === 'glTF' && glbBytes > 1e6, { file: download.suggestedFilename(), bytes: glbBytes });

  await page.click('[data-tab="drawings"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(OUT, 'studio-drawings.png') });
  const sheets = await page.locator('#sheet-select option').count();
  check('nine generated drawing sheets selectable', sheets === 9, { sheets });
  await page.click('#sheet-zoom-in'); await page.click('#sheet-zoom-in');
  await page.waitForTimeout(200);
  const sheetZoom = await page.evaluate(() => { const h = document.querySelector('.drawing-holder'); return { label: document.getElementById('sheet-fit').textContent, scrollable: h.scrollWidth > h.clientWidth * 1.5 }; });
  check('drawing sheets zoom for close reading', sheetZoom.label === '225%' && sheetZoom.scrollable, sheetZoom);
  await page.click('#sheet-fit');
  await page.click('[data-tab="documents"]');
  await page.screenshot({ path: join(OUT, 'studio-review.png') });
  check('regulatory unknown remains visible', (await page.locator('#review-content').innerText()).includes('NOT EVALUATED'));
  await page.click('#understand');
  await page.waitForSelector('#intent-dialog[open]');
  check('fused-source preflight opens', (await page.locator('#intent-content').innerText()).includes('quick-survey'));
  await page.click('[data-close="intent-dialog"]');

  await page.selectOption('#preset', 'compact');
  await page.click('#generate');
  await page.waitForFunction(() => document.getElementById('build-id').textContent !== 'BUNDLED EXAMPLE' && !document.getElementById('generate').disabled, null, { timeout: 300000 });
  const generated = await page.evaluate(() => ({ title: document.getElementById('project-title').textContent, theme: window.__ff.scene.exterior_theme, schema: window.__ff.scene.schema }));
  check('UI POST generation completes for 30x40 with the Modern Tropical default', generated.title.includes('Garden Pavilion') && generated.theme === 'modern_tropical', generated);
  await page.click('[data-tab="home"]');
  const views = await page.evaluate(() => { const v = window.__ffApp.viewer; v.setView('right'); const side = v.context.visible; v.setView('hero'); return { balconyButtonHidden: document.querySelector('[data-view="balcony"]').hidden, contextInSideView: side, contextInHero: v.context.visible }; });
  check('single-storey home: no balcony view, side view clear of the neighbours', views.balconyButtonHidden && !views.contextInSideView && views.contextInHero, views);
  await page.click('[data-mode="dollhouse"]');
  await page.waitForTimeout(500);
  await still(page);
  await page.screenshot({ path: join(OUT, 'studio-generated-compact.png') });

  await page.evaluate(() => document.getElementById('grid-open').click());
  const gridOpen = await page.evaluate(() => document.getElementById('grid-dialog').open);
  await page.evaluate(() => { document.querySelector('#grid-board button').click(); document.getElementById('grid-dialog').close(); });
  check('grid painter interaction', gridOpen);
  await page.evaluate(() => document.getElementById('ai-open').click());
  const aiChoices = await page.locator('[name="ai-tier"]').count();
  await page.evaluate(() => document.getElementById('ai-dialog').close());
  check('three AI consent choices visible', aiChoices === 3, { choices: aiChoices });
  const project = await page.evaluate(() => window.__ffApp.collect());
  check('reopenable project collects actual inputs', project.brief.bedrooms === 2 && project.brief.storeys === 1);

  gl = await page.evaluate(() => { const g = window.__ffApp.viewer.gl, e = g.getExtension('WEBGL_debug_renderer_info'); return { vendor: g.getParameter(g.VENDOR), renderer: e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER) }; });
  // Phone width: draw one frame at the new canvas size (the loop stays paused), then capture the page.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(300);
  await page.evaluate(() => { const v = window.__ffApp.viewer; v.paused = true; v.resize(); v.composer.render(0); });
  await page.screenshot({ path: join(OUT, 'studio-mobile.png'), fullPage: true });
  await page.evaluate(() => window.__ffApp.viewer.destroy());
  const dims = await page.evaluate(() => ({ width: innerWidth, scroll: document.documentElement.scrollWidth }));
  check('mobile no horizontal document overflow', dims.scroll <= dims.width, dims);
} finally {
  await browser.close();
  server.kill();
  rmSync(work, { recursive: true, force: true });
}
const record = { method: 'Headless Chromium with software WebGL (SwiftShader), navigating the real loopback studio server started by this script. Not a real-GPU, native-browser or installer sign-off.', checks, page_errors: errors, requests, gpu: gl };
writeFileSync(join(OUT, 'studio-browser.json'), JSON.stringify(record, null, 2) + '\n');
if (errors.length || checks.some((c) => !c.passed)) { console.error(JSON.stringify({ errors, failed: checks.filter((c) => !c.passed) }, null, 2)); process.exit(1); }
