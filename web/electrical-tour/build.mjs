// Bundle the standalone, offline electrical tour. The architectural viewer and the
// copied sample files stay independent of this script; only the edition's own
// electrical-manifest.json records the bundle hash.
import * as esbuild from '../viewer/node_modules/esbuild/lib/main.js';
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const edition = new URL('../../examples/gallery/my-desired-home-electrical/', import.meta.url);
const out = new URL('electrical-tour.js', edition);
await esbuild.build({
  entryPoints: [new URL('./src/index.js', import.meta.url).pathname],
  bundle: true,
  format: 'iife',
  target: ['es2020'],
  minify: true,
  legalComments: 'none',
  outfile: out.pathname,
});
const manifestUrl = new URL('electrical-manifest.json', edition);
const manifest = JSON.parse(await readFile(manifestUrl, 'utf8'));
manifest.files['electrical-tour.js'] = createHash('sha256').update(await readFile(out)).digest('hex');
await writeFile(manifestUrl, JSON.stringify(manifest, null, 2) + '\n');
