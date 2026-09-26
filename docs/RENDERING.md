# Rendering, walking, capture and the photoreal gap

## Included and executed: the realistic walkthrough viewer

`web/viewer.js` is a real-time, physically based renderer built on Three.js r186. It is bundled from `web/viewer/src` with esbuild and committed, so running the studio or opening an offline `preview.html` never needs Node or a network. It renders the exact generated `scene.json` (`floorforge.scene/0.4`); nothing is invented except the viewer-only neighbourhood described below.

**Surfaces.** Every material is physically based. At load time the GPU synthesises albedo, normal and roughness maps from each material's `kind`:
- render and plaster, concrete, stone, marble and terrazzo;
- tile, timber flooring and decking;
- stamped cobble, pavers, pebbles, gravel, grass and soil;
- encaustic tile, fabric and rugs;
- brushed metal, stone cladding and bark.

UVs are box-projected, and a world-space macro variation breaks up tiling. The package ships no bitmap texture assets.

**Light outdoors.**
- An analytic Preetham sky is rendered into the background and prefiltered into image-based light. It is used for daylight, golden hour and overcast.
- Below the horizon, a twilight sky model takes over for blue hour and night: a deep zenith, afterglow toward the sun and an anti-twilight band opposite it.
- The sun is a directional light with a 4096-pixel PCF shadow map at high quality. A hemisphere term stands in for bounce light off paving.
- Fixture lights come from the scene's `lights`. The nearest fittings are live: recessed and soffit downlights are downward spotlights, garden uplights point up, and other fittings radiate all round.
- Pooled lights cast no shadows. When walking, fittings with no line of sight to the visitor or the room's middle are switched off, so a lamp behind a wall cannot leak through it.

**Light indoors.** Each room gets its own light probe, a two-pass cube capture from its middle:
- Pass one captures the room lit by the sun, its lamps and the sky through its windows. Pass two re-lights the room with that capture: one radiosity step.
- The probe replaces open-sky lighting while the visitor is inside. Ceilings then receive floor bounce, rooms without sun stop reading blue, and glossy floors reflect the room's walls and windows instead of open sky.
- Probes are cached per room and lighting grade.
- The probe's mean radiance is read back asynchronously and meters the room like a camera. Exposure and white balance adapt smoothly as you walk between rooms.
- Glowing lamp shades are dimmed during the capture, because their light is already carried by their fixture lights.

**Image.** The frame then goes through:
- n8ao ambient occlusion;
- bloom, with a threshold that follows the metered exposure;
- AgX tone mapping with an adjustable "punchy" look;
- contrast, warmth and vignette;
- SMAA anti-aliasing.

**Planting.** Plants are grown procedurally from each scene `vegetation` item:
- species: frangipani, columnar conifer, spiral topiary, strelitzia, cordyline, palm, ornamental grass, shade and standard trees, monstera, fiddle-leaf fig, and round and flowering shrubs;
- painted alpha leaf atlases, wind sway and leaf translucency;
- hedges, and instanced lawn grass that fades with distance.

GLB and drawings keep simple coordination proxies (`role: plant-proxy`) for the same plants.

**Neighbourhood context.** The viewer adds context sized from the plot: neighbouring houses with framed reflective glazing, front-garden shrubs, street trees, lamp posts and a horizon tree line. It is never exported and makes no design claim.

**Quality.** Choose Auto, Ultra, High, Balanced or Performance. Auto starts from the device class and steps down when frames are slow.

**Hero view.** The street-side three-quarter hero view is mirrored to whichever diagonal faces the sun, as a photographer would choose. The scene's own camera record is unchanged.

## Walking through the home

Choose **Walk in**, click the view to capture the mouse, then use these controls:

| Control | Action |
|---|---|
| W A S D / arrow keys | move |
| Mouse | look around |
| Shift | run |
| Space | jump |
| C / Ctrl | crouch |
| Q / E | turn |
| Scroll | lens width |
| Esc | release mouse (Esc again leaves walk mode) |
| Touch | left-side stick to move, drag to look, Jump button |

The visitor is a capsule 0.27 m in radius and 1.78 m tall, with the eye at 1.63 m.
- It collides against a BVH of the actual generated geometry: walls, glazing, furniture and stair treads.
- Gravity applies. A jump rises about 0.8 m (0.82 m measured in the live capture).
- Steps up to 0.38 m are climbed automatically, so the U-stair is walked continuously from floor to floor, not teleported.
- Crouching lowers the eye and passes under 1.2 m.
- Falling off the site respawns you at the arrival court.
- A badge names the current room and storey from the scene's `rooms` metadata. The floor buttons follow the storey you are standing on.

## Honest limits

This is real-time rasterisation, not path tracing.
- **Global illumination** is approximated by one probe per room, not per-pixel bounces.
- **Reflections** come from probes, with no screen-space reflections. Glass is not refractive.
- **Lamp shadows:** lamps cast none.
- **Foliage** is card-based.
- **Neighbourhood** geometry is generic.
- **Dollhouse** views use shader clipping, not capped solid sections. The drawing section is derived separately from actual mesh-plane intersections.
- **Solar timing:** daylight uses the computed solar vector for the brief's date, hour and location. Golden hour, blue hour, night and overcast are **display grades** that keep the sun's azimuth, not recalculated astronomical times. Edit the date, hour or location and regenerate for a real solar study. The method omits atmospheric refraction, a surveyed skyline and weather.
- **Recording:** the WebM control records 12 seconds of browser output. It is not a verified 4K/30 fps film pipeline.

The captures in `evidence/` look convincing but are **not photographs or path-traced renders**, and should not be marketed as such.

## Optional Three.js / path tracer / GSAP lab

`web/src/three-studio.js` and `web/three.html` are a separate, optional source integration. It pins its own versions: Three 0.180.0, three-gpu-pathtracer 0.0.24, three-mesh-bvh 0.9.5 and GSAP 3.13.0. It offers GLB import, optional local HDRI, progressive path tracing and a 4K capture path.

```bash
python scripts/setup_three.py --accept-gsap-standard-license
# Start the ordinary server, then open its /three.html page.
```

**This lab was not built or rendered here.** It is not the default viewer. GSAP's own standard licence must be reviewed, not labelled MIT.

## External Blender

`blender_scene.py` builds an editable bpy scene from `scene.json`: meshes, materials, fixture lights and camera positions. Blender runs as a separate, user-installed process; it is not imported into the core or included in this ZIP.

Example invocation (inspect `--help` for the script's exact options):

```bash
blender --background --python scripts/blender_scene.py -- \
  --scene examples/demo/scene.json --out blender-output \
  --view hero --width 1600 --samples 128
```

**Blender was unavailable here, so no `.blend`, FBX, Cycles still or tour video is claimed.** The realistic viewer's procedural plants and GPU-synthesised textures are not yet translated into the Blender scene.

## Capture protocol

Two Node harnesses produce the screenshots in `evidence/`. Both need Playwright with a Chromium build; set `PLAYWRIGHT_MODULE` to its `index.mjs` if the package is not resolvable from the repository.

```bash
node scripts/capture_walkthrough.mjs   # viewer stills, walk captures, offline preview check
node scripts/capture_studio.mjs        # studio UI end to end against the real loopback server
```

- **`capture_walkthrough.mjs`** runs the committed `web/viewer.js` on each bundled example's `scene.json`. It renders the exterior grades, the dollhouse and a scripted first-person walk, with fixed 1/30 s steps through the door, into rooms, up the stair and onto the terrace. It then opens `examples/demo/preview.html` from disk. It records per-shot mode, grade, room, probe state, exposure and page errors in `walkthrough-capture.json` and `browser-preview.json`.
- **`capture_studio.mjs`** starts the Python server and drives the studio: viewer, walk mode, drawings, review, preflight, a real 30×40 ft generation, grid painter, AI consent dialog and a 390 px mobile layout. It writes `studio-browser.json`.

Both run Chromium's software WebGL (SwiftShader), which is slow. They validate composition, behaviour and absence of page errors. **They do not validate real-GPU colour, 60 fps, input latency or a normal browser installation.**

For release acceptance, open the default URL directly on native macOS and Windows machines. Fix the viewport, camera, floor, grade and quality. Walk the full route, time frame rates, and compare geometry against the drawings and GLB, not merely against an attractive reference.
