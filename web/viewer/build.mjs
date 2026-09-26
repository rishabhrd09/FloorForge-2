// Builds web/viewer.js: a single offline IIFE bundle exposing window.FloorForgeViewer.
// The output is committed so FloorForge's Python core never needs Node at runtime.
import * as esbuild from 'esbuild';
import { readFileSync } from 'node:fs';
const watch = process.argv.includes('--watch');
const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url)));
const versions = Object.entries(pkg.dependencies).map(([k, v]) => `${k}@${v}`).join(', ');
const options = {
  entryPoints: ['src/index.js'],
  bundle: true,
  format: 'iife',
  target: ['es2020'],
  minify: true,
  legalComments: 'eof',
  outfile: '../viewer.js',
  banner: { js: `/* FloorForge realistic walkthrough viewer ${pkg.version}. Offline bundle built from web/viewer/src with ${versions}. Third-party licences: licenses/viewer-js/. */` },
  logLevel: 'info',
};
if (watch) { const ctx = await esbuild.context(options); await ctx.watch(); }
else await esbuild.build(options);
