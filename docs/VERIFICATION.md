# Executed verification — 0.3.0-alpha

**This release is runnable but does not complete the original M0–M8 requirements.** See the requirement matrix.

## Executed here

**Tests.** 164 tests passed, 0 failed (112.1 s). The results are in `evidence/pytest.txt` and `pytest.xml`. The 45 realism test cases in `tests/test_realism.py` cover:
- the Modern Tropical default and scene 0.4;
- full-height living glazing within wall height;
- landscape, stepping stones, planting and lawns inside the plot and off the house, for every fixture plot;
- plant coordination proxies;
- room and walk metadata, and climbable stair treads;
- physically based material kinds and furniture containment;
- offline-preview script integrity, and the bundled viewer's presence and licence comments;
- walls that tile each storey without overlapping solids;
- the walk from the footpath through the open gate to the front door, for every exterior theme on the villa, the narrowest plot and a plot with parking: no obstacle in the way and no rise above the walker's practical 0.3 m;
- the refined window system, and each terrace's level, balustrade and pergola, for every exterior theme;
- the large view, zoom and large-still controls in the studio and the offline preview;
- the offline render path: the export in the bundle, and the Blender scripts compiling.

**Reproducibility.** Two clean default generations compared 23 published artifacts with no differences (`evidence/reproducibility.json`), on the same host and runtime.

**Examples.** The three bundled examples were regenerated from `examples/briefs` by `scripts/regenerate_examples.py`, with the final viewer bundle:
- 40×60 ft G+1 with three bedrooms;
- 30×40 ft ground floor with two bedrooms;
- 25×35 ft ground floor with one bedroom.

All three are Modern Tropical.

**Drawings.** All 41 pages across the three example PDFs were rasterised with PyMuPDF 1.28.2. Each is A3 landscape, has the preliminary banner and keeps its text inside the physical page, with 0 issues. Contact sheets and selected full pages were inspected (`evidence/pdf-*`). No physical printing was tested.

**Viewer.** `scripts/capture_walkthrough.mjs` produced 16 captures with no page errors, all in software WebGL (SwiftShader):
- exterior in daylight, golden hour and blue hour, plus front and entrance views;
- both dollhouse levels;
- a scripted first-person walk: the arrival on the footpath outside the gate, dining and living, kitchen, the U-stair mid-landing, a first-floor bedroom and the terrace, plus blue-hour and night interiors;
- the compact example's hero.

Per-shot mode, grade, room badge, probe state and metered exposure are in `evidence/walkthrough-capture.json`.

**Offline preview.** `examples/demo/preview.html` was opened from disk (`file://`) and became ready with no page errors. In a live check with the real animation loop and keyboard, holding W carried the visitor from the footpath through the open gate, across the court, up the entrance step and through the door into the hall and living room. The room probe was captured, exposure adapted, and Space lifted the visitor 0.82 m. The page's **Blender GLB** button downloaded a 76 MB binary glTF (`evidence/browser-preview.json`).

**Studio.** `scripts/capture_studio.mjs` started the real loopback server and passed 17 checks with no page errors (`evidence/studio-browser.json`):
- the bundled scene 0.4 and realistic renderer;
- the 3D view filling the studio at 1440×1024 (554 px tall), and a 1366×768 layout whose panel stays clear of the status bar;
- walk mode with the room badge;
- the large view filling the window with its controls, and **+** gliding the camera from 26.6 m to 18.6 m (`evidence/studio-large-view.png`);
- **Capture** saving a 3840-pixel still;
- nine drawing sheets, and a sheet zooming to 225% for close reading;
- the visible regulatory unknown;
- the fused-source preflight;
- a real 30×40 ft generation that arrives as Modern Tropical, with no Balcony view on the single-storey home and the neighbours standing aside for the side view;
- the grid painter;
- three AI consent choices;
- project collection;
- a 390 px mobile layout without horizontal overflow;
- the **Blender GLB** button downloading a textured binary glTF.

**Path-traced stills.** `scripts/export_presentation.mjs` exported the demo's presentation GLB (74.6 MB, 179 meshes, 143 textures), with the refurbished windows and terrace. `scripts/render_cycles.py` then path traced seven 1600×900 stills (`evidence/cycles-*.jpg`):
- hero in daylight, golden hour and dusk;
- living/dining in daylight and at dusk;
- kitchen and a first-floor bedroom in daylight.

They used Blender Cycles from the PyPI `bpy` 4.5.14 LTS wheel, on 4 CPU cores with OpenImageDenoise. Exteriors took 2¼ to 4½ minutes, daylight interiors 7 to 9½ minutes, and the lamp-lit dusk interior 18½ minutes. The stills are stored as JPEG. Settings, exposure and timings are in `evidence/cycles-renders.json`. A saved `.blend` (`--blend`) was reopened with its 179 meshes, 143 packed textures, sun, camera and Cycles settings intact.

**Packaging.** Python compilation, JavaScript syntax (studio, bundle, viewer sources and harnesses) and Bash syntax passed. All 13 START_HERE links resolve.

## Repairs made during verification

- **Flat, hazy daylight.** The sky light nearly matched the sun on vertical walls. The sun/sky balance was rebalanced and an adjustable AgX look added.
- **Blue-grey interiors.** Interiors were lit by unoccluded open sky. Per-room two-pass light probes now replace it, with metered exposure and white balance.
- **Olive and red blue-hour sky.** The Preetham model breaks down below the horizon, so a twilight sky model replaces it there.
- **Lamps leaking through walls.** Pooled fixture lights have no shadows, so a mirror light behind a wall and an exterior wall light burned hotspots into the dining room. Fixtures now need a line of sight to the visitor or the room's middle. Recessed downlights became downward spotlights.
- **Bloom haze.** Bloom hazed bright interiors because its threshold ignored exposure; the threshold now follows the metered exposure.
- **Wrong lights in probes.** A probe was captured with the previous room's light pool; captures now light from fittings around the probe point.
- **Stale exposure on arrival.** The metered exposure was not applied when a room's first meter reading arrived.
- **Background clutter.** Neighbour glazing rendered as black boxes, and the hero camera stood inside the opposite plots' massing zone. Neighbour glazing is now framed and reflective, the opposite plots have deeper gardens, and trees are kept clear of the hero camera.
- **Walk badge.** The badge read "First floor" at the mid-landing; storeys now switch past half-way up the stair.
- **HUD overlap.** The walk tip overlapped the studio's toolbar; it moved to the top-right.
- **Licence record.** n8ao declares ISC but ships CC0 1.0 text; both are now recorded (`licenses/LEDGER.json`).
- **Overlapping wall solids.** Path tracing showed full-height black bands at wall corners and T-junctions. Overlapping wall solids left coincident faces there, which rays leave and immediately re-hit. `scene.py` now tiles each storey's walls without overlaps, and a regression test compares piece areas with their union.
- **Inside-out trunks.** Plant trunk tubes were wound inward, so the viewer drew their far inner faces and Cycles shaded them black. They now face out.
- **Black planting in Blender.** The presentation export carried builder vertex colours on planting, which three.js ignores unless a material opts in but glTF always multiplies in. They are now exported only for materials that use them.
- **Unlit lamp shades.** Unlit lamp shades rendered black in daylight stills; switched off they now read as opal glass and white diffusers.

## Repairs from the full visual QA

The studio was driven through every tab, camera view, mode and grade, both generated presets and every exterior theme, at 1024×768, 1366×768, 1440×900, 1440×1000, 1920×1080 and 390 px wide. These defects were found and fixed:

- **Cramped walk start.** The walk began inside the gate, 0.45 m from the facade on the smallest plot. It now starts on the footpath outside the open gate, facing the house.
- **Blocked gateway on the older themes.** A timber bar crossed the gateway at chest height. It is now a flush threshold.
- **Porch too high to step onto.** On the Warm Modern Minimal, Tropical Verandah and Earth & Terracotta themes the porch platform stood 0.39–0.43 m above the court with no step, above the walker's practical 0.3 m rise. An inset step on the walk to the door now climbs it.
- **Things in front of the front door.** On those themes a porch post, a porch ottoman and, on narrow plots, the 3 m Warm Modern Minimal feature wall stood in the door's approach. Posts now frame the walk, seating sits beside it, and the feature wall stops short of the door or is left out. Single-storey homes no longer receive the first-floor facade frame.
- **Lamp post across the small-plot hero view.** At wide canvas proportions a street lamp stood in the foreground. Lamp posts are now kept out of both hero views.
- **Side views from inside the neighbours.** The Left and Right cameras stood inside neighbouring houses. The context now stands aside for those views. Front and side views are framed by storey height, where single-storey homes had been cropped to the roof. The Balcony view aims at the generated balcony and is hidden when there is none.
- **Letterboxed viewer.** At 1440×1000 the 3D view was a 311 px strip under two rows of theme cards. Theme cards now take one row each and the view is 530 px tall. At 1366×768, and on phones, the panel content had run under the status bar; it now scrolls within the panel, and on phones the page grows.
- **Phone framing.** On a portrait phone canvas the hero view cropped both ends of the house. Orbit views now step back on portrait canvases.
- **Wording.** The status line kept the walk instructions after leaving walk mode, the heading read "1 bedrooms", and the walk badge called the street "Garden".

## Windows, terraces and the large view

Close-ups of every exterior theme's windows and terraces were rendered from the street, from above, along each side and from the terrace itself, in daylight and at blue hour. These were the findings and the changes:

- **Dated windows.** Bedroom windows sat in 120 mm timber or render boxes. The older themes also had 0.7 m concrete shades over every window, side surrounds and 0.4 m stone sills. All themes now share one slim aluminium system with timber-lined pods on facade bedrooms and etched glass in wet rooms; the older themes keep a slim eyebrow over living-room windows. A test checks, for every theme, that no heavy shades remain, sills stay slim, wet rooms get etched glass and the pods stay slim.
- **Terraces on the roof.** On the three older themes with a balcony, the balcony was placed at twice the floor height, so it floated on the roof as a glass box while the drawings placed it correctly. It now sits level with the first floor.
- **Sparse terraces.** The glass balustrade had no visible edge and the deck was bare. Every terrace now has a handrail cap, a louvred pergola with downlights, seating on a rug and planted corners. A test checks the level, balustrade and pergola for every theme.
- **Large view and zoom.** The studio's large view was driven in a browser at 1440×900 and 390×844. It filled the window with its controls, and **+** zoomed from 26.6 m to 18.6 m. A double-click glided in to the clicked spot. Esc returned to the studio. **Capture** saved a 3840×2400 PNG. A drawing sheet zoomed to 225% and panned by dragging.

## Not accepted

The following were not available or not completed:
- native macOS or Windows runs on a real GPU (colour, frame rate, input latency);
- a clean network installation;
- GPU or in-browser path tracing, 4K stills, photographic calibration, and any film;
- interactive doors;
- accessible-route certification;
- live local or cloud AI inference;
- an independent IFC viewer, or the AutoCAD GUI;
- professional structural design, or official NBC/byelaw certification.

The viewer screenshots are actual engine output from software rendering and document a real-time, physically based preview. The Cycles stills are offline path-traced renders of the same preliminary geometry, not photographs.

## Previous release — 0.2.0-alpha

**This release is runnable but does not complete the original M0–M8 requirements.** See the 80-row requirement matrix.

### Executed here

112 tests passed, 0 failed (18.75 seconds) in the final run. Two clean default generations compared 23 published artifacts with no differences, on the same host/runtime.

Three fully generated examples are bundled: 40×60 ft G+1 with three bedrooms, 30×40 ft ground floor with two bedrooms, and 25×35 ft ground floor with one bedroom. The manual L-grid is an additional input fixture. Geometric acceptance is not a guarantee of construction or regulatory safety.

Each sample DXF was re-imported with ezdxf, and each GLB with Trimesh. IFC4 received only self-reference-integrity checks; no independent schema/BIM-viewer claim. All 41 pages across the three example PDFs were rasterised and inspected via contact sheets; A3 page bounds, banners and text bounds passed. No physical printing was tested.

The browser harness completed nine checks, including a real backend generation triggered from the studio, the resulting exports/model, source preflight, grid interaction, AI choices and a 390px mobile width. No page JavaScript errors were recorded. The controlled test used Chromium under Xvfb/SwiftShader and a loopback fetch binding because managed browser navigation was blocked. It is not native-GPU or unrestricted-browser installation acceptance.

Python compilation, JavaScript syntax and Bash syntax passed. START_HERE links resolve within the package. The exact runtime and dependency notices are in evidence/runtime.json and licenses/LEDGER.json.

### Repairs made during verification

Non-finite input became a structured rejection; duplicate/missing semantic references are rejected before route-graph access; furniture checks treat connected open public zones as a physical union rather than an invented wall. A long circulation hall was shortened, and the upper terrace was made genuinely roof-open across the shared geometry. DXF writer timestamps/GUID metadata were normalised for reproducibility. Report generation no longer mutates a previously validated DAG stage.

### Not accepted

No original legacy repository/tests, native macOS/Windows installers, clean network installation, real-GPU colour test, photoreal still/film, live local/cloud inference, independent IFC viewer, AutoCAD GUI, professional structural design or official NBC/byelaw certification was available or completed. Optional source adapters are marked unverified, not presented as working binaries. The requirement matrix records further functional gaps, including the complete questionnaire, drag-resize designer, unrestricted layouts, image recognition, eldercare accessibility and continuous stair walking.

The actual screenshots are included; no generated-image beautification was substituted for geometry. They document a raster preliminary model, not the requested final photoreal quality bar.
