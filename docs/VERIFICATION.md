# Executed verification — 0.3.0-alpha

**This release is runnable but does not complete the original M0–M8 requirements.** See the requirement matrix.

## Executed here

**Tests.** 139 tests passed, 0 failed (52.1 s). The results are in `evidence/pytest.txt` and `pytest.xml`. The 20 new realism tests in `tests/test_realism.py` cover:
- the Modern Tropical default and scene 0.4;
- full-height living glazing within wall height;
- landscape, stepping stones, planting and lawns inside the plot and off the house, for every fixture plot;
- plant coordination proxies;
- room and walk metadata, and climbable stair treads;
- physically based material kinds and furniture containment;
- offline-preview script integrity, and the bundled viewer's presence and licence comments;
- walls that tile each storey without overlapping solids;
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
- a scripted first-person walk: arrival, dining and living, kitchen, the U-stair mid-landing, a first-floor bedroom and the terrace, plus blue-hour and night interiors;
- the compact example's hero.

Per-shot mode, grade, room badge, probe state and metered exposure are in `evidence/walkthrough-capture.json`.

**Offline preview.** `examples/demo/preview.html` was opened from disk (`file://`) and became ready with no page errors. In a live check with the real animation loop and keyboard, holding W carried the visitor from the arrival court up the entrance step and through the door into the living and dining area. The room probe was captured, exposure adapted, and Space lifted the visitor 0.80 m. The page's **Blender GLB** button downloaded a 74 MB binary glTF (`evidence/browser-preview.json`).

**Studio.** `scripts/capture_studio.mjs` started the real loopback server and passed 11 checks with no page errors (`evidence/studio-browser.json`):
- the bundled scene 0.4 and realistic renderer;
- walk mode with the room badge;
- nine drawing sheets;
- the visible regulatory unknown;
- the fused-source preflight;
- a real 30×40 ft generation that arrives as Modern Tropical;
- the grid painter;
- three AI consent choices;
- project collection;
- a 390 px mobile layout without horizontal overflow;
- the **Blender GLB** button downloading a textured binary glTF.

**Path-traced stills.** `scripts/export_presentation.mjs` exported the demo's presentation GLB (72.5 MB, 174 meshes, 141 textures). `scripts/render_cycles.py` then path traced seven 1600×900 stills (`evidence/cycles-*.jpg`):
- hero in daylight, golden hour and dusk;
- living/dining in daylight and at dusk;
- kitchen and a first-floor bedroom in daylight.

They used Blender Cycles from the PyPI `bpy` 4.5.14 LTS wheel, on 4 CPU cores with OpenImageDenoise. Exteriors took 2 to 4½ minutes, daylight interiors 7 to 9 minutes, and the lamp-lit dusk interior 18 minutes. The stills are stored as JPEG. Settings, exposure and timings are in `evidence/cycles-renders.json`. A saved `.blend` (`--blend`) was reopened with its geometry, 141 packed textures, sun, camera and Cycles settings intact.

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
