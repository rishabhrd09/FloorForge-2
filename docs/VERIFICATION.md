# Executed verification — 0.3.0-alpha

**This release is runnable but does not complete the original M0–M8 requirements.** See the requirement matrix.

## Executed here

**Tests.** 137 tests passed, 0 failed (53.0 s). The results are in `evidence/pytest.txt` and `pytest.xml`. The 18 new realism tests in `tests/test_realism.py` cover:
- the Modern Tropical default and scene 0.4;
- full-height living glazing within wall height;
- landscape, stepping stones, planting and lawns inside the plot and off the house, for every fixture plot;
- plant coordination proxies;
- room and walk metadata, and climbable stair treads;
- physically based material kinds and furniture containment;
- offline-preview script integrity, and the bundled viewer's presence and licence comments.

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

**Offline preview.** `examples/demo/preview.html` was opened from disk (`file://`) and became ready with no page errors. In a live check with the real animation loop and keyboard, holding W carried the visitor from the arrival court up the entrance step and through the door into the living and dining area. The room probe was captured, exposure adapted, and Space lifted the visitor 0.82 m (`evidence/browser-preview.json`).

**Studio.** `scripts/capture_studio.mjs` started the real loopback server and passed 10 checks with no page errors (`evidence/studio-browser.json`):
- the bundled scene 0.4 and realistic renderer;
- walk mode with the room badge;
- nine drawing sheets;
- the visible regulatory unknown;
- the fused-source preflight;
- a real 30×40 ft generation that arrives as Modern Tropical;
- the grid painter;
- three AI consent choices;
- project collection;
- a 390 px mobile layout without horizontal overflow.

**Packaging.** Python compilation, JavaScript syntax (studio, bundle, viewer sources and harnesses) and Bash syntax passed. All 12 START_HERE links resolve.

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

## Not accepted

The following were not available or not completed:
- native macOS or Windows runs on a real GPU (colour, frame rate, input latency);
- a clean network installation;
- path-traced, Blender or photographic stills, and any film;
- interactive doors;
- accessible-route certification;
- live local or cloud AI inference;
- an independent IFC viewer, or the AutoCAD GUI;
- professional structural design, or official NBC/byelaw certification.

The screenshots are actual engine output from software rendering. They document a real-time, physically based preview model, not the final photoreal quality bar.

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
