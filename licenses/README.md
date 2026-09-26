# License record

The project source is MIT. Dependencies are installed separately. `LEDGER.json` records actual installed versions and copied text notices. No font files, protected reference images, model weights, Blender, or native runtime binaries are included.

**This is not a completed legal/redistribution audit.** GEOS, numerical libraries, codec libraries, optional GSAP and packaging runtimes need platform-specific review before distributing native installers. Do not remove upstream notices from a future binary build.

## Bundled realistic viewer

`web/viewer.js` is a single offline bundle of FloorForge's viewer source (`web/viewer/src`, MIT) with Three.js 0.186.1 (MIT), three-mesh-bvh 0.9.5 (MIT), postprocessing 6.39.5 (Zlib) and n8ao 2.0.1 (ISC in its package.json; its shipped LICENSE file is CC0 1.0). Their licence texts are copied to `licenses/viewer-js/` and their `@license` comments are preserved at the end of the bundle. No texture bitmaps, HDRIs, fonts or 3D models are shipped: surfaces, foliage and sky are synthesised procedurally at runtime.
