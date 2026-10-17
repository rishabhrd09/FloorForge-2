// Close-up stills of beds, indoor monsteras and default kitchen runs in a published preview.html, for checking
// furnishing geometry and planting by eye. Shots are derived from the page's own scene data, so they follow any
// home. Software WebGL (SwiftShader) is slow: allow a minute or so per shot.
//   PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node scripts/capture_furnishing_closeups.mjs \
//     examples/gallery/long-house/preview.html evidence/fitted-furnishings/long-house [day|golden] [shot-name-regex]
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [page_, outDir, grade = 'day', only = ''] = process.argv.slice(2);
if (!page_ || !outDir) throw Error('Usage: capture_furnishing_closeups.mjs <preview.html> <out-dir> [grade] [regex]');
mkdirSync(outDir, { recursive: true });

// Camera shots in scene metres (x, y, z up): each bed from beyond its foot corners, along a long edge and at its head;
// each potted monstera from eye height and from below; each default kitchen run square on and from either end.
function plan(scene) {
  const H = scene.floor_height, nodes = new Map(scene.nodes.map((n) => [n.id, n])), shots = [];
  const unit = ([x, y]) => { const l = Math.hypot(x, y); return [x / l, y / l]; };
  const at = (c, ...terms) => terms.reduce((p, [v, k]) => [p[0] + v[0] * k, p[1] + v[1] * k], c);
  for (const ed of scene.editables.filter((e) => e.id.endsWith('/bed'))) {
    const parts = ed.nodeIds.map((id) => nodes.get(id)).filter(Boolean), z = ed.floor * H;
    const mattress = parts.find((n) => n.material === 'linen' && n.role === 'furniture' && Math.abs(n.position[2] - z - .39) < .01);
    const board = parts.find((n) => n.material === 'fabric-dark');
    if (!mattress || !board) continue;
    const c = mattress.position.slice(0, 2), head = unit([board.position[0] - c[0], board.position[1] - c[1]]), side = [-head[1], head[0]];
    const foot = at(c, [head, -1]);
    for (const [s, tag] of [[1, 'a'], [-1, 'b']]) {
      shots.push({ name: `${ed.roomId}-bed-${tag}`, floor: ed.floor, fov: 60, eye: [...at(foot, [head, -1.2], [side, s * 1.1]), z + 1.35], target: [...at(c, [head, -.3]), z + .45] });
      shots.push({ name: `${ed.roomId}-bed-edge-${tag}`, floor: ed.floor, fov: 55, eye: [...at(c, [side, s * 1.4], [head, .55]), z + .95], target: [...at(foot, [side, s * .75]), z + .45] });
      shots.push({ name: `${ed.roomId}-bed-head-${tag}`, floor: ed.floor, fov: 50, eye: [...at(c, [side, s * 1.25], [head, -.25]), z + 1.2], target: [...at(c, [head, .3]), z + .55] });
    }
  }
  const bounds = (r) => [0, 1].flatMap((i) => [Math.min(...r.polygon.map((p) => p[i])), Math.max(...r.polygon.map((p) => p[i]))]);
  const inside = (r, x, y) => { const [x0, x1, y0, y1] = bounds(r); return x >= x0 && x <= x1 && y >= y0 && y <= y1; };
  const centre = (r) => [r.polygon.reduce((a, p) => a + p[0], 0) / r.polygon.length, r.polygon.reduce((a, p) => a + p[1], 0) / r.polygon.length];
  for (const v of scene.vegetation.filter((v) => v.species === 'monstera' && (v.floor ?? -1) >= 0)) {
    const [x, y, base] = v.position, room = scene.rooms.find((r) => r.floor === v.floor && r.kind !== 'void' && inside(r, x, y));
    if (!room) continue;
    const d = unit([centre(room)[0] - x, centre(room)[1] - y]);
    for (const [dist, h, tag] of [[1.25, 1.35, 'eye'], [.85, .75, 'low']])
      shots.push({ name: `${v.id}-${room.id}-${tag}`, floor: v.floor, fov: 55, eye: [x + d[0] * dist, y + d[1] * dist, v.floor * H + h], target: [x, y, base + .45] });
  }
  const modular = new Set(scene.nodes.filter((n) => n.owner?.endsWith('/modular-kitchen')).map((n) => n.owner.split('/')[0]));
  for (const run of scene.furniture.filter((f) => f.kind === 'kitchen-run' && !modular.has(f.room_id))) {
    const xs = run.footprint.map((p) => p[0]), ys = run.footprint.map((p) => p[1]), room = scene.rooms.find((r) => r.id === run.room_id);
    const c = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2], rc = centre(room), z = run.floor * H;
    const along = Math.max(...xs) - Math.min(...xs) > Math.max(...ys) - Math.min(...ys);
    const n = along ? [0, rc[1] > c[1] ? 1 : -1] : [rc[0] > c[0] ? 1 : -1, 0], t = [-n[1], n[0]], L = along ? Math.max(...xs) - Math.min(...xs) : Math.max(...ys) - Math.min(...ys);
    shots.push({ name: `${run.room_id}-kitchen`, floor: run.floor, fov: 66, eye: [...at(c, [n, 1.75]), z + 1.6], target: [...c, z + 1.25] });
    for (const [s, tag] of [[1, 'a'], [-1, 'b']])
      shots.push({ name: `${run.room_id}-kitchen-${tag}`, floor: run.floor, fov: 60, eye: [...at(c, [n, 1.15], [t, s * L * .3]), z + 1.55], target: [...at(c, [t, -s * L * .15]), z + 1] });
  }
  return shots;
}

const browser = await chromium.launch({ headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const errors = [], taken = [];
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(pathToFileURL(resolve(page_)).href, { timeout: 900000, waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__ff?.ready || window.__ff?.error, null, { timeout: 900000, polling: 2000 });
  const failure = await page.evaluate(() => window.__ff.error);
  if (failure) throw Error(failure);
  if (grade !== 'day') await page.evaluate((g) => window.__ff.viewer.setGrade(g), grade);
  const shots = plan(await page.evaluate(() => window.__ff.scene)).filter((s) => !only || new RegExp(only).test(s.name));
  for (const s of shots) {
    // Walk mode at a fixed pose: indoor exposure, the room's light probe and the lamps settle before the still.
    await page.evaluate((s) => {
      const v = window.__ff.viewer, e = [s.eye[0], s.eye[2], -s.eye[1]], t = [s.target[0], s.target[2], -s.target[1]];
      v.setMode('walk'); v.paused = true; v.fitHeld = null; v.zoomAnim = null;
      v.walker.teleport(v.walker.position.clone().set(e[0], s.floor * v.H + .3, e[2]));
      v.floor = s.floor; v.camera.fov = s.fov; v.camera.updateProjectionMatrix();
      v.camera.position.set(...e); v.camera.lookAt(...t);
      for (let i = 0; i < 100; i++) v.adapt(.05);
      v.updateProbe();
      for (let i = 0; i < 100; i++) v.adapt(.05);
      v.hud?.show?.(false); v.updateLights(); v.vegetation?.update(v.time, v.camera); v.composer.render(.016);
    }, s);
    const bytes = await page.evaluate(async () => Array.from(new Uint8Array(await (await window.__ff.viewer.snapshot({ width: 1200 })).arrayBuffer())));
    writeFileSync(`${outDir}/${s.name}.png`, Buffer.from(bytes));
    taken.push(s);
    console.log('shot', s.name);
  }
} finally {
  writeFileSync(`${outDir}/shots.json`, JSON.stringify({ page: page_, grade, shots: taken, errors }, null, 2) + '\n');
  await browser.close();
}
if (errors.length) { console.error(errors); process.exitCode = 1; }
