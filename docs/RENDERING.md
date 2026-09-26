# Rendering, capture and the photoreal gap

## Included and executed

The default viewer is an authored offline WebGL2 raster renderer, fed by the exact generated scene. It has shared geometry, shadows, procedural surface variation, fixture-linked point lights, model-relative camera framing, six style recipes and inspectable furniture. The delivered captures show its actual ceiling. They are **not photoreal** and should not be marketed as such.

Exterior, dollhouse, top-down and first-person views are available. The eye is 1.6 m above the selected floor. Collision is a horizontal-circle approximation against selected wall/furniture footprints; stair cores are blocked and the floor control explicitly changes level. There is no certified capsule navigation, continuous stair walk or click-to-travel solver. The orbit tour is an orbit, not the requested directed interior cinema. The WebM control records 12 seconds of browser raster output; that control is not a verified 4K/30fps film pipeline.

Dollhouse is a visibility/fragment clipping view, not a full capped solid section operation. A shader-clipped wall does not become a CAD section. The drawing section is separately derived from actual mesh-plane intersections.

Day uses the computed solar vector. Warm and dusk controls are **display grades**, not recalculated astronomical times. Edit the date/hour/location and regenerate for a changed solar study. The method omits atmospheric refraction, a surveyed skyline and weather. The default is not automatically optimised for every facade orientation.

## Optional Three.js / path tracer / GSAP lab

`web/src/three-studio.js` and `web/three.html` are an optional source integration using Three 0.180.0, three-gpu-pathtracer 0.0.24, three-mesh-bvh 0.9.5 and GSAP 3.13.0. The package build uses esbuild. The code offers GLB import, optional local HDRI, mean-luminance normalisation, progressive path tracing and a 4K capture path.

```bash
python scripts/setup_three.py --accept-gsap-standard-license
# Start the ordinary server, then open its /three.html page.
```

Dependency download was blocked in the execution container; **this bundle was not built or rendered**. A version-specific compatibility test, loaded GLB checks, sampling convergence, resource cleanup and real-GPU colour/quality review remain required. This lab is separate from the default studio, not a completed replacement for it. GSAP's own standard license must be reviewed, not labelled MIT.

## External Blender

`blender_scene.py` builds an editable bpy scene from `scene.json`, with meshes, materials, fixture lights and camera positions. Blender is invoked as a separate user-installed process. It is not imported into the core or included in this ZIP.

Example invocation (inspect `--help` for the script's exact options):

```bash
blender --background --python scripts/blender_scene.py -- \
  --scene examples/demo/scene.json --out blender-output \
  --view hero --width 1600 --samples 128
```

The worker contains optional FBX+JSON and tour-frame paths. **Blender was unavailable, so no `.blend`, FBX, Cycles still or tour video is claimed to have been produced.** A live validation/repair loop, full interior camera route, realistic materials, texture-scale audit, collision and 4K review remain open.

The supplied Astra article URL could not be retrieved. Its owner-provided Appendix E was treated as a workflow target: plan first; editable scene; actual furniture; inspect geometry; match light to visible fixtures; review camera routes; export the same scene. That is adoption of a supplied specification, not independent verification of the article or completion of its full workflow.

## Capture protocol

`evidence/` contains actual screenshots and method logs. The managed browser environment disallowed normal navigation. We used Playwright `set_content` with the self-contained preview; the studio harness bridged its fetch calls to the actual loopback Python server. Chromium used SwiftShader under Xvfb. This validates visible composition and selected interactions; **it does not validate real-GPU colour, native input performance, 60fps or a normal browser installation path**.

For next-stage acceptance run the default URL directly on native macOS and Windows. Fix viewport, camera, style, floor, time and exposure. Capture exterior day/golden/dusk, both dollhouse levels, living, bedrooms, kitchen, stair and all six styles. Compare geometry against the drawing and GLB, not merely against an attractive reference. Test a software fallback separately; do not treat it as colour truth.
