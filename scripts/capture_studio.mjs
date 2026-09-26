// Studio browser evidence: starts the real loopback server, drives the studio UI end to end in headless
// Chromium and records screenshots plus checks in evidence/studio-browser.json.
//
//   node scripts/capture_studio.mjs [--out evidence] [--python .venv/bin/python]
//
// Needs Node 18+ and Playwright with a Chromium build (set PLAYWRIGHT_MODULE to its index.mjs when the
// package is not resolvable from this folder). Software WebGL (SwiftShader) keeps it runnable headless; it is
// not a real-GPU, native-browser or installer sign-off.
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
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

  await page.click('[data-mode="walk"]');
  await page.evaluate(() => { const v = window.__ffApp.viewer; v.paused = true; v.hud.setLocked(true); v.walker.update(1 / 30, v.readInput()); v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone())); v.camera.rotation.set(v.walker.pitch, v.walker.yaw, 0); v.hudUpdate(); v.composer.render(0); });
  const hud = await page.evaluate(() => window.__ffApp.viewer.hud.last);
  check('walk mode opens at the arrival with the room badge', hud && hud.includes('|'), { badge: hud });
  await page.screenshot({ path: join(OUT, 'studio-walk.png') });
  await page.click('[data-mode="solid"]');

  await page.click('[data-tab="drawings"]');
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(OUT, 'studio-drawings.png') });
  const sheets = await page.locator('#sheet-select option').count();
  check('nine generated drawing sheets selectable', sheets === 9, { sheets });
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
  await page.evaluate(() => window.__ffApp.viewer.destroy());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(OUT, 'studio-mobile.png'), fullPage: true });
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
