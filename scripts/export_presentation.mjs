// Writes the viewer's presentation GLB (synthesised textures, grown planting, lawn, context) for a scene.json,
// ready for scripts/render_cycles.py.
//
//   node scripts/export_presentation.mjs examples/demo/scene.json build/demo-presentation.glb [--no-context] [--no-grass]
//
// Needs Node 18+ and Playwright with a Chromium build (set PLAYWRIGHT_MODULE to its index.mjs when the
// package is not resolvable from this folder). Runs the committed web/viewer.js in headless software WebGL.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const [scenePath, outPath] = process.argv.slice(2).filter((a) => !a.startsWith('--'));
if (!scenePath || !outPath) { console.error('usage: node scripts/export_presentation.mjs SCENE.json OUT.glb [--no-context] [--no-grass]'); process.exit(2); }
const options = { context: !process.argv.includes('--no-context'), grass: !process.argv.includes('--no-grass') };
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');

const viewer = readFileSync(join(ROOT, 'web/viewer.js'), 'utf8');
const scene = readFileSync(resolve(scenePath), 'utf8');
const html = `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">
<div style="position:relative;width:640px;height:360px"><canvas id="c" style="width:100%;height:100%;display:block"></canvas></div>
<script>${viewer.replace(/<\/script/gi, '<\\/script')}</script><script id="scene" type="application/json">${scene.replace(/</g, '\\u003c')}</script>
<script>window.v = new FloorForgeViewer(document.getElementById('c'), { quality: 'ultra' }); v.paused = true; v.setScene(JSON.parse(document.getElementById('scene').textContent));</script></body></html>`;

const browser = await chromium.launch({ headless: true, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
try {
  const page = await browser.newPage({ viewport: { width: 640, height: 360 } });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.setContent(html, { waitUntil: 'load', timeout: 300000 });
  const size = await page.evaluate(async (opts) => { const buf = await window.v.exportPresentation(opts); window.__glb = new Uint8Array(buf); return window.__glb.length; }, options);
  const CHUNK = 4 << 20, parts = [];
  for (let offset = 0; offset < size; offset += CHUNK) {
    const b64 = await page.evaluate(([o, n]) => {
      const a = window.__glb.subarray(o, o + n); let s = '';
      for (let i = 0; i < a.length; i += 32768) s += String.fromCharCode.apply(null, a.subarray(i, i + 32768));
      return btoa(s);
    }, [offset, CHUNK]);
    parts.push(Buffer.from(b64, 'base64'));
  }
  if (errors.length) throw new Error(errors.join('\n'));
  mkdirSync(dirname(resolve(outPath)), { recursive: true });
  writeFileSync(resolve(outPath), Buffer.concat(parts));
  console.log(`${outPath}: ${(size / 1048576).toFixed(1)} MB`);
} finally { await browser.close(); }
