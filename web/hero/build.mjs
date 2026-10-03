import {build} from 'esbuild';
await build({entryPoints:['index.js'],bundle:true,format:'iife',target:['es2020'],minify:true,legalComments:'eof',outfile:'../hero.js',banner:{js:'/* FloorForge homepage. Three.js 0.186.1 (MIT), GSAP 3.13.0 (Standard License). See licenses/hero-js/. Rebuild: cd web/hero && npm ci && npm run build. */'}});
