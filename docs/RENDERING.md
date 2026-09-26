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

**Windows and terraces.** The generated geometry uses one contemporary window system for every exterior theme:
- slim aluminium frames (45 mm face) in the theme's frame colour, staggered sliding panes, and a transom on tall glazing;
- slim sills, and obscured (etched) glass in bathrooms and utility rooms;
- bedroom windows on the facade set in slim projecting pods (50 mm shell, 340 mm deep) lined with timber;
- on the older themes, a slim floating eyebrow over living-room windows in place of deep concrete shades.

First-floor terraces sit level with the floor they open from. Each has a timber deck, a frameless glass balustrade in a base shoe with a slim handrail cap, a pergola of slim posts and timber louvres with downlights, and seating on an outdoor rug between planted corners.

**Frontage and entrance.** The street frontage (`floorforge/frontage.py`, every designed theme) is laid out as built homes are, not as a centred gate between equal walls:
- a pedestrian gate on the door's axis, its leaf shown open against the stop (the walk enters here);
- a separate sliding vehicle gate, closed, over the widest stretch of front yard the entrance steps leave free, or aligned with the carport; its track runs on behind the wall on the side with the longer clear run;
- a stone-clad pier beside the pedestrian gate with a brass house number, a letterbox and a gate light, and on the modern theme a slim steel canopy over the gate with a downlight;
- a cobble driveway behind the vehicle gate and a path of large two-tone slabs from the pedestrian gate to the steps.

The Modern Tropical entrance is an L: the flight covers the door end of the landing and returns down its side toward the wider yard, each tread with a 30 mm nosing over an LED strip; the other end of the landing is a sit-out with a timber bench on a stone plinth, a planter of grasses and a stone-clad column under the canopy. The front door is a tall timber pivot door (its head in line with the full-height glazing) with long black pulls, set in a black steel portal that stands proud of the render.

**Massing and roof.** Two-storey homes raise the stair into a stone-clad tower above the roof (the headroom over the roof access) with a floating lid, a slot window to the street and a glazed door onto the roof. On the modern theme the roof beside it is an open terrace with pavers, a frameless glass balustrade, loungers and planted pots, and a 1 m eave shades the street front, its soffit lined in timber slats with downlights. Every designed theme racks photovoltaic modules over the rear of the roof, tilted 12° toward the midday sun; single-storey modern roofs are finished in gravel. Roof-level furniture and planting sit on the roof level (floor = storeys), so every dollhouse cut hides them.

**Side gardens.** Side passages wide enough to walk are paved in large-format slabs (1.2 × 0.6 m, laid in two tones by the paver shader's fourth parameter) with a pebble drip strip against the house; the side boundary walls are clad inside in horizontal timber boards over a dark batten backing, with a steel cap; tall pots of planting stand where a passage is wide enough to walk past them, and wall lights hang on the house. Narrow passages keep stepping stones in pebbles.

**Neighbourhood context.** The viewer adds context sized from the plot: neighbouring houses with stone plinths, framed reflective glazing, timber entrance doors under slim canopies and some glass-railed balconies, front-garden shrubs, street trees, lamp posts and a horizon tree line. Trees and lamp posts are kept out of the foreground of both hero views, and the context stands aside for the Left and Right elevations, whose cameras would otherwise stand inside a neighbour's house. It is never part of the design exports and makes no design claim; the presentation GLB for offline renders includes it as context.

**Large view and zoom.** **⤢ Large view** makes the 3D fill the whole window, with the view, mode and lighting controls carried along. It uses true full screen where the browser allows it and a window-filling view everywhere else, including iPhone. Esc or the same button returns to the studio.
- **+** and **−** glide the orbit camera in and out; in walk mode they narrow or widen the lens.
- Double-clicking a spot on the house glides in to orbit around that spot.
- **Capture** re-renders the current view at 3840 pixels wide, with the same framing, for a large still.
- Drawing sheets zoom with **+**, **−**, Ctrl/⌘ + scroll or a double-click, pan by dragging, and have their own large view.

**Framing, Focus and the wider view.** Every orbit view frames the home, not the street. `fitHouse` keeps the camera's viewing direction and moves the camera along and across its line of sight to the closest spot from which the home's box (every storey on show, with its porch, terraces and roof; the whole plot for the Top view) fills a set share of the frame, clear of the toolbars laid over the canvas. Each frame edge bounds the camera by a plane, so per screen axis the closest camera maximises a concave piecewise-linear function; `web/viewer/src/framing.js` solves it exactly and centres the axis with room to spare, and a unit test checks the fit from low, high and overhead directions on wide and tall screens. The hero fills 84% of the frame, the elevations and dollhouse about 90%, and a framing the visitor has not touched follows the canvas when it resizes.
- **◎ Focus** enters the large view and shows the home alone (street and neighbours set aside) filling 94% of the screen from the current direction; views, modes and Reset keep that framing until Focus is switched off (walking always shows the street).
- **Aerial** is a high three-quarter view over the roof, its terraces and the garden; **Top** looks straight down through a long lens. The plan and the top view turn the plot's long side across the screen (the street at the bottom, or on the left for a deep plot on a landscape screen), and the dollhouse diagonal is turned the same way, so the home uses the width.
- **Fit** re-frames after zooming or orbiting; **⇤ Wider view** folds the brief panel away (remembered on the device) so the 3D takes the width of the studio.
- The Cycles stills (`scripts/render_cycles.py`) frame their hero and front cameras with the same solve.

**Quality.** Choose Auto, Ultra, High, Balanced or Performance. Auto starts from the device class and steps down when frames are slow.

**Hero view.** The street-side three-quarter hero view is mirrored to whichever diagonal faces the sun, as a photographer would choose. The scene's own camera record is unchanged. The Front, Left and Right views look from the middle of the elevation's height and are then fitted to the home, so single-storey homes are framed as fully as G+1 ones. The Balcony view aims at the generated balcony and is offered only when the home has one.

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

The walk starts on the footpath outside the open gate, facing the house, so you arrive as a guest does: through the gate, across the court and up the entrance step to the front door. Every exterior theme keeps that route clear and climbable, which a test checks for each theme on the villa, on the narrowest plot and on a plot with parking, where a wide drive gate is entered on the front door's line.

The visitor is a capsule 0.27 m in radius and 1.78 m tall, with the eye at 1.63 m.
- It collides against a BVH of the actual generated geometry: walls, glazing, furniture and stair treads.
- Gravity applies. A jump rises about 0.8 m (0.80–0.82 m measured in the live captures).
- Stair treads, kerbs and entrance steps are climbed automatically, so the U-stair is walked continuously from floor to floor, not teleported. The step offset is 0.38 m, but the capsule meets an edge higher than about 0.3 m before its foot probe reaches the top, so 0.3 m is the practical single rise (measured by walking at test boxes).
- Crouching lowers the eye and passes under 1.2 m.
- Falling off the site respawns you at the gate.
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

The viewer captures in `evidence/` (`realistic-*`, `walk-*`, `preview-*`) look convincing but are **not photographs or path-traced renders**, and should not be marketed as such.

## Optional Three.js / path tracer / GSAP lab

`web/src/three-studio.js` and `web/three.html` are a separate, optional source integration. It pins its own versions: Three 0.180.0, three-gpu-pathtracer 0.0.24, three-mesh-bvh 0.9.5 and GSAP 3.13.0. It offers GLB import, optional local HDRI, progressive path tracing and a 4K capture path.

```bash
python scripts/setup_three.py --accept-gsap-standard-license
# Start the ordinary server, then open its /three.html page.
```

**This lab was not built or rendered here.** It is not the default viewer. GSAP's own standard licence must be reviewed, not labelled MIT.

## Path-traced stills with Blender Cycles

For stills beyond real-time rendering, the same home can be path traced in Blender Cycles. Two steps are needed:

```bash
# 1. Export what the viewer draws (textures, grown planting, lawn grass, nearby context) as binary glTF.
node scripts/export_presentation.mjs examples/demo/scene.json build/demo.glb
# 2. Path trace it (Blender 4.2+, or the PyPI `bpy` wheel on Python 3.11).
python scripts/render_cycles.py --glb build/demo.glb --scene examples/demo/scene.json --out build/renders \
    --view hero --grade day --width 1600 --height 900 --samples 128
python scripts/render_cycles.py ... --view eye --eye 3.2,3.9,0,-95 --name living-day   # eye level: x,y,floor,yaw
# or: blender --background --python scripts/render_cycles.py -- (same arguments)
```

**Export.** The **Blender GLB** button in the studio and in every offline preview downloads the presentation file. `export_presentation.mjs` produces the same file headlessly by calling `viewer.exportPresentation()`:
- GPU-synthesised textures are read back into images: colour maps as JPEG, normal and roughness maps as PNG.
- Instanced planting and lawn grass are baked into ordinary meshes.
- Neighbourhood context is kept only within 60 m; the distant horizon ring is backdrop for the live view only.
- Lights, sky and post-processing are left out.

**Render.** `render_cycles.py` rebuilds the lighting from `scene.json`:
- Blender's physical Nishita sky, with its sun disc off.
- A Sun lamp at the site's computed solar position; golden hour lowers it to 7.5°, dusk to the horizon.
- Every visible fixture: downlights as spots, others as points.

It then prepares materials:
- Glazing becomes architectural glass: clear for camera rays, transparent to shadow and diffuse rays, so daylight reaches interiors without caustic noise.
- Leaves get a translucent back side.
- Planting and lawn use their vertex colours.

A quick preview meters exposure like a camera, protecting highlights. Interiors get a daylight white balance, and lamp-lit grades stay warm. Output goes through AgX (Medium High Contrast) and OpenImageDenoise. `--blend` also saves the assembled `.blend` scene.

**Executed here.** The stills in `evidence/cycles-*.jpg` were rendered at 1600×900 on 4 CPU cores with the `bpy` 4.5.14 LTS wheel. `evidence/cycles-renders.json` records each view, grade, sample count, exposure and time. Exteriors took 2 to 4½ minutes, daylight interiors 7 to 9 minutes, and the lamp-lit dusk interior 18 minutes; the stills are stored as JPEG.

Path tracing exposed four defects the rasteriser had hidden. All are fixed at the source:
- **Wall overlaps.** Wall solids overlapped at corners and T-junctions; the coincident faces shaded black. `scene.py` now tiles each storey's walls without overlaps.
- **Trunks.** Plant trunk tubes were wound inside out.
- **Vertex colours.** The export carried vertex colours that the viewer ignores but glTF always applies; they are now kept only where the viewer shows them.
- **Lamp shades.** Unlit lamp shades were black; they now read as opal glass and white diffusers.

**Limits.** These are renders of preliminary generated geometry, not photographs, and are not calibrated to any camera or luminance. There is no live path tracing in the browser. Cycles on a CPU is slow; a GPU (`--gpu`) is much faster but was not available here. 4K output is only a matter of `--width`/`--height` and time, and was not rendered here.

`blender_scene.py` is the older worker. It builds an editable bpy scene directly from `scene.json`, with flat materials and without the grown planting, plus optional FBX and orbit frames. Those FBX and tour paths were not executed.

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
