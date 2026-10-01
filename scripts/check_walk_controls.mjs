// Exercise keyboard focus, mapping and the real walking controller in the built app.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = resolve(import.meta.dirname, '..'), out = resolve(root, 'evidence/walk-controls');
const port = 8878, url = `http://127.0.0.1:${port}`, checks = [], errors = [];
mkdirSync(out, { recursive: true });
const server = spawn(resolve(root, '.venv/bin/python'), ['-m', 'floorforge', 'serve', '--no-browser', '--port', String(port), '--out', '/tmp/ff-walk-controls'], { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] });
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
  await page.evaluate(() => {
    const v = window.__ffApp.viewer; v.paused = true; v.setQuality('performance'); v.setMode('walk'); v.canvas.focus();
    for (let i = 0; i < 30; i++) v.walker.update(1 / 60, v.readInput());
    window.walkTestBase = v.walker.position.toArray();
  });
  const reset = () => page.evaluate(() => { const v = window.__ffApp.viewer; v.keys.clear(); v.walker.teleport(v.camera.position.clone().fromArray(window.walkTestBase), 0); v.canvas.focus(); });
  const state = () => page.evaluate(() => { const v = window.__ffApp.viewer; return { yaw: v.walker.yaw, position: v.walker.position.toArray(), input: { ...v.readInput() } }; });
  const step = () => page.evaluate(() => { const v = window.__ffApp.viewer; for (let i = 0; i < 60; i++) v.walker.update(1 / 60, v.readInput()); });
  for (const [key, direction] of [['ArrowLeft', 1], ['ArrowRight', -1]]) {
    await reset(); const before = await state(); await page.keyboard.down(key);
    const input = await state(); await state();
    check(`${key} requests turning without strafe or input-read side effects`, input.input.turn === direction && input.input.strafe === 0 && input.yaw === 0);
    await step(); await page.keyboard.up(key); const after = await state();
    check(`${key} turns in place`, Math.abs(after.yaw - direction * 1.68) < 1e-8 && Math.hypot(after.position[0] - before.position[0], after.position[2] - before.position[2]) < .001, { before, after });
    await step(); check(`${key} stops turning on release`, (await state()).yaw === after.yaw);
  }
  for (const [key, axis, value] of [['ArrowUp', 'forward', 1], ['ArrowDown', 'forward', -1], ['a', 'strafe', -1], ['d', 'strafe', 1], ['q', 'turn', 1], ['e', 'turn', -1]]) {
    await reset(); await page.keyboard.down(key); const result = await state(); await page.keyboard.up(key);
    check(`${key} retains its intended ${axis} control`, result.input[axis] === value && (axis === 'turn' ? result.input.strafe === 0 : result.input.turn === 0));
  }
  await reset(); await page.keyboard.down('ArrowUp'); await page.keyboard.down('ArrowRight');
  check('Forward and turn can be held together', await page.evaluate(() => { const i = window.__ffApp.viewer.readInput(); return i.forward === 1 && i.turn === -1 && i.strafe === 0; }));
  await page.keyboard.up('ArrowUp'); await page.keyboard.up('ArrowRight');
  await reset(); await page.keyboard.down('ArrowLeft'); await page.keyboard.down('ArrowRight');
  check('Opposite turning keys cancel', (await state()).input.turn === 0);
  await page.keyboard.up('ArrowLeft'); await page.keyboard.up('ArrowRight');
  await page.focus('#width'); await page.keyboard.down('ArrowRight');
  check('Editing a form does not turn the camera', (await state()).input.turn === 0); await page.keyboard.up('ArrowRight');
  await reset(); await page.keyboard.down('ArrowRight'); await page.evaluate(() => window.dispatchEvent(new Event('blur')));
  check('Losing window focus releases held turn keys', (await state()).input.turn === 0); await page.keyboard.up('ArrowRight');
  check('Walk overlay explains the new arrow mapping', await page.locator('.ff-keys').textContent().then(text => text.includes('←') && text.includes('turn left / right') && text.includes('forward / back') && text.includes('move sideways')));
  await reset();
  await page.evaluate(() => { const v = window.__ffApp.viewer; v.camera.position.copy(v.walker.eyePosition(v.camera.position.clone())); v.camera.rotation.set(v.walker.pitch, v.walker.yaw, 0); v.hud.setLocked(false); v.composer.render(0); });
  await page.screenshot({ path: out + '/walk-keyboard-guide.png' });
  check('No browser errors', errors.length === 0, errors);
} finally {
  writeFileSync(out + '/browser-acceptance.json', JSON.stringify({ checks, errors }, null, 2) + '\n');
  if (browser) await browser.close();
  server.kill();
}
