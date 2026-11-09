// Check the final local delivery page after its captures and renders are ready.
// Run: node scripts/check_tirumala_5_delivery.mjs
import {createHash} from 'node:crypto';
import {existsSync, readFileSync, writeFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const directory = resolve(root, 'output/tirumala-5-delivery');
const htmlPath = resolve(directory, 'index.html');
const buildingPath = resolve(root, 'examples/gallery/tirumala-5/building.json');
const scenePath = resolve(root, 'examples/gallery/tirumala-5/scene.json');
const digest = path => createHash('sha256').update(readFileSync(path)).digest('hex');
const building = JSON.parse(readFileSync(buildingPath, 'utf8'));
const scene = JSON.parse(readFileSync(scenePath, 'utf8'));
if (!building.planHash || scene.planHash !== building.planHash) {
  throw new Error('Finish the build first: building and scene plan hashes must agree.');
}
const inputHashes = {htmlSha256: digest(htmlPath), buildingSha256: digest(buildingPath), sceneSha256: digest(scenePath)};
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE ||
  '/Users/rishabh/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs');
const results = [];
const browser = await chromium.launch({headless: true});
try {
  for (const width of [1440, 390]) {
    const errors = [];
    const page = await browser.newPage({viewport: {width, height: 1000}, deviceScaleFactor: 1});
    page.setDefaultTimeout(60000);
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    const screenshot = `delivery-${width === 1440 ? 'desktop' : 'mobile'}.png`;
    let detail = null;
    try {
      await page.goto(pathToFileURL(htmlPath).href, {waitUntil: 'load'});
      // Force the complete page to load its images even below the viewport.
      await page.evaluate(async () => {
        const images = Array.from(document.images);
        for (const image of images) image.loading = 'eager';
        await Promise.race([
          Promise.all(images.map(image => image.decode().catch(() => undefined))),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Timed out waiting for delivery images')), 45000)),
        ]);
        await document.fonts.ready;
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
      });
      detail = await page.evaluate(() => ({
        width: window.innerWidth,
        scrollWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
        height: document.documentElement.scrollHeight,
        revision: document.querySelector('meta[name="project-revision"]')?.content,
        images: Array.from(document.images, image => ({
          src: image.getAttribute('src'), loaded: image.complete && image.naturalWidth > 0,
          naturalWidth: image.naturalWidth, naturalHeight: image.naturalHeight,
        })),
        overflowingElements: Array.from(document.querySelectorAll('main *')).filter(element => {
          const bounds = element.getBoundingClientRect();
          return bounds.width > 0 && (bounds.left < -1 || bounds.right > window.innerWidth + 1);
        }).map(element => ({tag: element.tagName, className: element.className,
          text: (element.textContent || '').trim().slice(0, 100)})).slice(0, 20),
      }));
      await page.screenshot({path: resolve(directory, screenshot), fullPage: true});
    } catch (error) {
      errors.push(error.message);
    } finally {
      await page.close();
    }
    const pass = !!detail && !errors.length && detail.scrollWidth <= width &&
      detail.images.length > 0 && detail.images.every(image => image.loaded) &&
      detail.revision === building.planning.g2Revision;
    const row = {width, pass, detail, errors, screenshot};
    if (detail && existsSync(resolve(directory, screenshot))) row.screenshotSha256 = digest(resolve(directory, screenshot));
    results.push(row);
    console.log(`${pass ? 'PASS' : 'FAIL'} delivery ${width}px: ${detail?.images.length ?? 0} images, scroll width ${detail?.scrollWidth ?? 'unavailable'}`);
  }
} finally {
  await browser.close();
}

const inputsUnchanged = inputHashes.htmlSha256 === digest(htmlPath) &&
  inputHashes.buildingSha256 === digest(buildingPath) && inputHashes.sceneSha256 === digest(scenePath);
const report = {planHash: building.planHash, revision: building.planning.g2Revision,
  generatedAt: new Date().toISOString(), url: pathToFileURL(htmlPath).href,
  ...inputHashes, inputsUnchanged, results,
  passed: inputsUnchanged && results.length === 2 && results.every(row => row.pass)};
writeFileSync(resolve(directory, 'responsive-qa.json'), JSON.stringify(report, null, 2) + '\n');
if (!report.passed) process.exitCode = 1;
