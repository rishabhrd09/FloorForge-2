// Builds web/plan-reveal.js: the offline Plan Reveal bundle (the realistic viewer's source plus the drawing state,
// the reveal mask and the scroll choreography). It resolves three, postprocessing and n8ao from the viewer's
// pinned packages, so both bundles use the same versions. web/viewer.js itself is not touched.
//   node web/plan-reveal/build.mjs
import * as esbuild from '../viewer/node_modules/esbuild/lib/main.js';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const here = (p) => fileURLToPath(new URL(p, import.meta.url));
const pkg = JSON.parse(readFileSync(here('../viewer/package.json')));
const versions = Object.entries(pkg.dependencies).map(([k, v]) => `${k}@${v}`).join(', ');
await esbuild.build({
  entryPoints: [here('./src/index.js')],
  bundle: true,
  format: 'iife',
  target: ['es2020'],
  minify: true,
  legalComments: 'eof',
  nodePaths: [here('../viewer/node_modules')],
  outfile: here('../plan-reveal.js'),
  banner: { js: `/* FloorForge Plan Reveal. Offline bundle built from web/plan-reveal/src and web/viewer/src with ${versions}. Third-party licences: licenses/viewer-js/. */` },
  logLevel: 'info',
});
