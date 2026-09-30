# Executed verification — 0.3.0-alpha

## 2026-09-29 — courtyard/veranda wall junction and guide review

- The full Python suite passed: **286 tests**, including the existing automatic-preset aesthetic hashes and 11 new wall-junction regressions. The viewer unit suite passed **13 tests**.
- Reconstructed the reported 8.692 × 11.588 m guide. The former `WALL_TOPOLOGY` failure occurred because one bedroom wall spanned both veranda and courtyard while ownership was inferred from its midpoint. The compiler now splits at outdoor adjacency transitions, retains exact room polygons, and connects doors/windows to the appropriate neighbour. Tests also cover off-centre junctions, boundary positions at either wall axis or face, corner-only contact, collinear vertices and openings that improperly straddle neighbours.
- Both empty occupied floors are reported together. Room-size, entry, daylight, access and stair requirements remain enforced; conversion does not certify the reported draft as a complete house.
- `scripts/check_wall_junctions.mjs` passed **18 browser checks** in Chromium/SwiftShader with no browser exceptions. It covers all five guide issues, floor badges, a persistent desktop/mobile conversion action, saved-guide/custom-mode separation, conversion and validation of the reported board, full generation of a valid outdoor junction, shared model/scene/report identity, exact metric dimensions displayed in feet, zero-bedroom custom submission and stale-design/export blocking after failure. Evidence is in `evidence/wall-junctions/`.
- Native HTML step validation on the plot inputs and the sidebar's old one-bedroom minimum were found by the main-page submission check and corrected. Custom Plan counts bedrooms from authored rooms. The input coverage summary stays expandable without pushing the design out of view.
- The verified workspace server on port 8765 was refreshed; its live validation API now reaches the reported Ground draft's actual room-size/access/daylight issues without the false wall-junction error. The user's browser draft was not overwritten. Existing exported scenes require regeneration to contain revised geometry.


## 2026-09-29 — roof access and movable linked cores

- 275 Python test cases passed across the full and focused runs: the pre-existing full run passed 260 with seven localhost binds blocked by the sandbox; all 24 security/server cases passed with loopback access; the eight new roof cases passed. The legacy three-preset scene geometry/material/light/camera/landscape hashes still match. This is a scene-data comparison, not native-GPU pixel certification.
- Roof tests cover ground-only Custom Plan, G+1 and G+2; stair coordinates translated toward the rear; the matching final flight and slab/ceiling cutout; outward roof door swing in 3D and drawings; guards, separate terrace area, save/reopen identity, PDF/SVG/DXF/GLB/IFC pipeline identity, explicit missing-core conflicts and guide-to-custom placement retention.
- The 13 viewer unit tests pass, including the fix for legacy self-owned handles that otherwise remained as invisible obstacles after their door moved. Canonical scene geometry is unchanged by opening/closing during a walkthrough.
- `scripts/check_roof_access.mjs` drives the built Chromium/SwiftShader viewer through the actual collision geometry. It climbs and descends every flight for automatic G+1 and a rear-positioned Custom G+2 core; operates the rooftop door from both sides; walks on the terrace; checks floor-selector/roof-cutaway teleport prevention; edits all linked cores together with undo/redo; generates the matching plan; and checks that replacing a walking scene clears its old overlay. Results and screenshots are in `evidence/roof-access/`.

Old projects keep roof access off until explicitly enabled and regenerated. New G+1 studio presets enable it. Exact Custom Plan positions remain authoritative; Quick Guide still uses front-corner stair arrangements and explicitly rejects unsupported positions, with conversion to Custom Plan available. The earlier verification sections below describe prior feature states.

## 2026-09-29 — interactive openings and input coverage

- All 267 Python test cases passed across the full run and the localhost-access retry. The sandboxed full run passed 260; seven HTTP/port tests could not bind sockets. Running `tests/test_security_ai.py` with loopback access passed all 24 cases, including those seven. The existing three-preset aesthetic hash test passed.
- `node --test web/viewer/src/*.test.js`: 12 tests passed. These exercise arrow turning, real closed/open door collision, walking through an open doorway, window collision changes, reach from both sides, floor/distance/facing limits, intervening walls, capsule sweep protection and unchanged canonical scene data.
- `scripts/check_opening_interactions.mjs`: 17 browser checks passed using Chromium/SwiftShader. F and tap controls work on the bundled scene; G+2 Custom Plan scenes work using embedded opening hosts without a companion building file. Form focus, input override reporting, unparsed requests and persistent input coverage passed with no browser exceptions. Evidence is in `evidence/opening-interactions/`.
- The current server on port 8765 was refreshed and `/api/intent` returned the new input audit. Existing saved scenes are supported in the studio; previously exported standalone HTML needs regeneration to embed the updated viewer.

Opening poses are temporary walkthrough state. Raised sills and fixed geometry remain obstacles. Legacy balcony glazing starts half-open and can open fully or return to that pose; it is not represented as a fully sealed sliding assembly. Image pixels and arbitrary prose are not automatically interpreted; the input audit records this explicitly. Mobile tap uses the same button handler; physical-device touch and native GPU performance were not separately tested.


**This release is runnable but does not complete the original M0–M8 requirements.** See the requirement matrix.

## Executed here

**Tests.** 233 tests passed, 0 failed across the current full-suite verification (229 passed in the restricted sandbox; its four loopback-bind cases passed in the separate 21-test security run). The committed evidence files describe the earlier evidence run; beyond those earlier contracts, the suite now covers:
- the planner and review (`tests/test_geometry.py`): every fixture brief screened under NBC 2016 Part 3 style minimums; circulation at most 15% of a floor with halls at least 1 m clear; the professional screen quiet on the default plan (no low daylight, unventilated bath, pooja beside a bath, door-swing clash, or bath over the kitchen or pooja) and raising bath-ventilation and door-swing warnings on a deliberately defective copy; unresolved requests naming an attached-bath shortfall; facing that never rotates the plan (with Vastu off the plan is identical for every road side, with it on the same or its mirror);
- the drawings (`tests/test_exports.py`): ten sheets with plans at 1:50–1:125; dimension chains that close on the footprint on every side; one tag per opening, matching the door and window schedule; the section cut running up the stair flight; DXF DIMENSION entities equal to the drawn chains; schedule text that never cuts a room name;
- the survey and the text reader (`tests/test_intent.py`): six homeowner briefs read field by field (plot sizes and areas, road side, BHK, attached baths, G+1, lakh and crore, pooja, parking, kitchen, Vastu, setbacks, heights, style), phrases not understood and assumptions reported, and open spaces derived from the plot unless stated;
- spatial input (`tests/test_spatial_inputs.py`): the authored board is always exactly 4 × 4 with no physical cell size; opposite left/right guides move the kitchen to opposite sides without changing the footprint or room-area programme; supported directional prose changes placement; grid, description and questionnaire fields compose in one generated building; later user-touched form fields outrank older text/imported edits; requested optional pooja and attached-bath rooms survive candidate pruning; and the changed room polygon reaches the scene contract used by the 3D viewer;
- the realism suite (79 cases), now also: side passages with pale pavers staggered on black pebbles, the breeze-block screen and the boards stopping at it, pots and the wash basin clear of the pavers; the water wall inside the plot with the hedge parted around it and its up-light; the stone-clad street face with up-lights and the tall vertical-slat gate; the slatted foyer ceiling inside the living room below the ceiling line; the roof sala on the terrace, clear of the solar rack and the loungers, and left out on a small roof.

**Reproducibility.** Two clean default generations compared 24 published artifacts with no differences (`evidence/reproducibility.json`), on the same host and runtime.

**Examples.** The three bundled examples were regenerated from `examples/briefs` by `scripts/regenerate_examples.py`:
- 40×60 ft G+1 with three bedrooms, all with attached baths: a three-row ground floor (living; kitchen and utility, dining, store and pooja; a bedroom suite with dressing room and bath, a study and the common bath) and upstairs a family lounge with the open terrace, a master suite with dressing room and bath, a second bedroom with its bath and a study — no bath over the kitchen or the pooja, and no review warning;
- 30×40 ft ground floor with two bedrooms;
- 25×35 ft ground floor with one bedroom, with an attached bath and a common bath.

All three are Modern Tropical, with open spaces derived from the plot (the same values the presets used to state).

**Drawings.** All 43 pages across the three example PDFs (15, 14 and 14) were rasterised with PyMuPDF 1.28.2. Each is A3 landscape, has the preliminary banner and keeps its text inside the physical page, with 0 issues. The demo plans are at 1:100. Contact sheets and selected pages, including the new A-601 door, window and room schedules, were inspected (`evidence/pdf-*`). No physical printing was tested.

**Viewer.** `scripts/capture_walkthrough.mjs` produced 21 captures with no page errors, all in software WebGL (SwiftShader):
- exterior in daylight, golden hour and blue hour, plus front, entrance, aerial and top views, Focus, and the entrance at blue hour;
- both dollhouse levels;
- a scripted first-person walk: the arrival on the footpath outside the pedestrian gate, the living room, the kitchen, the side passage, the stair, a first-floor bedroom and the terrace, plus blue-hour and night interiors;
- the compact example's hero.

Per-shot mode, grade, room badge, probe state and metered exposure are in `evidence/walkthrough-capture.json`.

**Offline preview.** `examples/demo/preview.html` was opened from disk (`file://`) and became ready with no page errors. In a live check with the real animation loop and keyboard, holding W carried the visitor from the street through the garden and the hall into the living room; the room probe was captured and Space lifted the visitor 0.82 m. The page's **Blender GLB** button downloaded an 80.8 MB binary glTF (`evidence/browser-preview.json`).

**Studio.** `scripts/capture_studio.mjs` started the real loopback server and passed 21 checks with no page errors (`evidence/studio-browser.json`), including:
- the 3D view filling the studio at 1440×1024 (694 px tall) and a 1366×768 layout (438 px) whose panel stays clear of the status bar;
- walk mode with the room badge; the large view and zoom (25.2 m to 17.6 m); a 3840-pixel still; Focus from the hero direction and the top; the wider view (1066 px to 1384 px);
- ten drawing sheets, and a sheet zooming to 225%;
- the eight-question survey: the compass setting the road side (and its note), the attached-bath choices following the bedroom count, and the plot summary showing the open spaces derived from its size (`evidence/studio-understood.png` shows the reading of a written brief);
- a written description read back with the phrases understood and a phrase not understood;
- a real 30×40 ft generation, the fixed 16-cell positional painter, three AI consent choices, project collection, a 390 px mobile layout and the **Blender GLB** download.

**Path-traced stills.** `scripts/export_presentation.mjs` exported the demo's presentation GLB (77.9 MB), with the new plan, the stone-clad frontage, the slatted gate, the roof sala and the foyer ceiling. `scripts/render_cycles.py` then path traced eight 1600×900 stills (`evidence/cycles-*.jpg`), framing the hero on the home with the viewer's exact fit:
- hero in daylight, golden hour and dusk;
- the living room in daylight and at dusk, looking past the sofa to the stair, the foyer and the dining;
- the kitchen through its wide opening from the dining table;
- the master bedroom;
- the foyer: the slatted timber ceiling over the pivot door.

They used Blender Cycles from the PyPI `bpy` 4.5.14 LTS wheel, on 4 CPU cores with OpenImageDenoise. Exteriors took 4½ to 8½ minutes, daylight interiors 11 to 13 minutes, and the lamp-lit dusk interior 27 minutes (the test suite ran alongside the first stills). The stills are stored as JPEG. Settings, exposure and timings are in `evidence/cycles-renders.json`. The first interior renders of this round showed a white skirting strip across the open floor between the living and dining rooms; it was fixed (see below) and every still was rendered again from the corrected scene.

**Packaging.** Python compilation, JavaScript syntax (studio, bundle, viewer sources and harnesses) and Bash syntax passed. All 11 START_HERE links resolve.

## Planning, drawings, survey and garden: what the checks found

The planner was swept over ten plots (25×35 to 60×90 ft, G and G+1, one to six bedrooms), and every drawing sheet, the survey, the text reader and the new garden details were inspected in the browser and in path-traced stills. These defects were found and fixed:

- **Spatial inputs had different meanings and did not compose.** Structured questionnaire values already reached the brief, which is why setbacks and counts visibly changed. Free text only affected fields matched by the deterministic grammar; all other prose was retained but not planned. Reference images were metadata only. The former variable metric grid entered a separate exact-layout branch with ground-floor restrictions instead of influencing automatic candidate selection. The current path compiles supported room-location prose and the fixed 4 × 4 board into the same dimensionless placement targets consumed and audited by the automatic planner. References and unparsed prose remain explicitly non-operative.
- **Dimension figures over opening tags.** On the right and bottom chains the figures sat on the tag side of the line, and short segments flipped their figures onto the tags. Figures now sit outside every line and move one row out only when they do not fit between their ticks.
- **Section marker in the chains, and 1:125 plans.** The section bubbles crossed the dimension chains; they now stand beyond them, clear of the grid bubbles. Moving them out pushed the default plan to 1:125, so the drawing area grew to 220 × 216 mm and the default plans are at 1:100 again.
- **Labels on walls.** A shallow assembly's name ("FEATURE WALL") was drawn over the wall; it now sits below the assembly.
- **Living and dining without a table.** On a narrow 30×60 ft plot the lounge group left the combined room no space for a dining table. The room now seats the table first, on the kitchen side, when the lounge group would leave none, keeping that only if both fit.
- **Pooja requested but missing.** On a 60×90 ft plot the planner kept two oversized filler studies and no pooja room; a pooja that finds no slot in the stacks is now carved from a rear corner of the living room.
- **Baths over the kitchen.** The default plan put two upper baths over the kitchen, and three other plots one. A stacking penalty alone could not move them, because each upper suite chose its bath's corner without seeing the floor below; the upper-floor search now sees the ground floor's kitchen and pooja, and each pairing is costed on what lies below it.
- **Skirting across an open floor.** The path-traced living room showed a white skirting strip across the floor between the living and dining rooms; skirting now runs along walls only.
- **Schedule text.** Long location lists were cut mid-word ("…Store, Uti"); they now end "+N more".
- **Pots on the pavers.** Pots and the wash basin could stand on the staggered pavers; wide passages now leave a strip beside the pavers that step away from the boundary, and narrow ones have none.
- **Up-lights that never lit.** Orbit views rank lights by distance to the house, so interior downlights took every spot slot and the boundary up-lights never lit; the viewer now keeps a few slots for the up-lights nearest the camera.
- **Text reading.** "living 15x18 on a 40x60 plot" read the room as the plot; "30*50." was missed before a full stop; a phrase whose only unread word was "site" was reported as not understood. All three are fixed and covered by tests.
- **Harness assumptions.** The studio harness expected nine sheets; the offline preview's screenshots had a 30 s limit, too short for the heavier scene in software WebGL, and now have the same 120 s as the other captures.

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

## Frontage, entrance, massing, side gardens and Focus

The street frontage, entrance, roof and side gardens were rebuilt to read as a home as built, and every view was re-framed on the home. Renders from the street, the court, the steps, the side passages, the roof and above were checked for every plot size and designed theme, by day, at blue hour and at night. These were the findings and the changes:

- **Frontage.** The centred gate between equal walls became a pedestrian gate on the door's axis and a separate sliding vehicle gate over the parking pad (or the carport), with a stone-clad letterbox pier. The open pedestrian leaf, first shown at 78°, reached 2 cm into the walk corridor; it now rests at 88° against its stop. The modern gate canopy (2.14 m above the court) is kept 0.3 m inside the wall so the approach stays clear.
- **Entrance.** Straight steps across the whole landing became an L-shaped flight with a sit-out, a stone-clad column and a tall pivot door in a black steel portal. The LED strips under the nosings were too thin to read at night and were deepened; path lanterns that landed on the paving at the foot of the steps are now rejected on hardscape.
- **Massing.** A flat, featureless roof became a stone-clad stair tower beside an open roof terrace (modern), a deep timber-soffit eave and a solar rack; the tower's door, first facing the solar array, now opens onto the terrace seating. Roof furniture and planting sit on the roof level so every dollhouse cut hides them.
- **Side gardens.** Pebble passages became large two-tone slabs with a timber-clad boundary. The boards' gaps first showed the white render behind; a dark batten backing makes them shadow lines.
- **Framing.** The hero showed the house across about half the frame's width, inside a street scene; every view now fits the home (84% of the frame for the hero). The Top view through the 43° lens let the roof loom over the garden and now uses a 24° lens. The studio's 3D view was 428 px tall on a 1440×900 laptop and is now 568 px, and the brief panel folds away for the width.
- **Walk.** With the real capsule walker (the viewer's physics, fixed 1/30 s steps), holding W carried the visitor from the footpath through the open pedestrian gate, up the L-shaped steps and through the pivot door into the dining room on the villa, the 30×40 and 25×35 ft plots, and a plot with parking.

## Not accepted

The following were not available or not completed:
- native macOS or Windows runs on a real GPU (colour, frame rate, input latency);
- a clean network installation;
- GPU or in-browser path tracing, 4K stills, photographic calibration, and any film;
- interactive doors;
- accessible-route certification;
- live local or cloud AI inference;
- an independent IFC viewer, or the AutoCAD GUI;
- professional structural design, or official NBC/byelaw certification;
- Vastu-driven partis: Vastu chooses the plan's hand (it or its mirror image) and is read room by room, but every parti keeps the living room at the front, so south- and west-facing plots score low and a strict request is reported unresolved;
- a garden sala on plots whose rear or side gardens are deeper than Indian setbacks usually leave (the sala stands on the roof terrace instead).

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


### 2026-09-29 — occupied floors and placement editing

298 Python tests verified across the full run and focused reruns. The seven local-server cases blocked by sandbox socket permissions passed with loopback access; no test failure remains. All 13 opening/walking Node checks and 21 new browser acceptance checks pass. The browser checks exercise G+1 defaults, count-aware examples, undoable G+2→G+1 reduction, actual furniture dragging, exact scene isolation, room drag-to-swap, invalid placement rejection, save/reopen hashes and desktop/mobile controls. Evidence: `evidence/placement-editor/`.

Furniture moves preserve original mesh assets and every unrelated render node; material, light, camera, planting and lawn data are compared exactly. Legacy preset visual scene hashes still pass. GLB re-import confirms the changed node transform. IFC emits the same selected furniture meshes as tessellated assemblies and passes STEP reference integrity; independent IFC schema/viewer approval is still not claimed.


### 2026-09-29 — drawing-room guide and roof/floor correction

All 302 Python tests pass in a complete run with local socket access. This includes legacy aesthetic scene hashes, guest-room generation on Ground and First, separate living/study semantics, named placement conflicts, doors/windows, sofa/coffee-table furnishing and save/reopen plan hashes.

All 22 browser checks in `scripts/check_drawing_room_guide.mjs` pass: visible guest-room card, actual card drag/drop, distinct laundry semantics, occupied-floor/roof controls, explicit G+2 preservation, G+1 correction, guide-board retention, Undo, save/reopen, direct stair hand-off, Custom Plan floor-count Undo, desktop/mobile controls, generated room/furniture and shared building/scene identity. No browser runtime errors were recorded. Evidence: `evidence/drawing-room-guide/`.

No renderer, mesh recipe, material, lighting or camera configuration was changed by this correction. Automatic stair locations remain limited to the existing front-corner arrangements; the interface identifies that limitation and hands off the retained location to Custom Plan. Programme preflight still does not promise every requested room zone will fit.


### 2026-09-30 — simple room-first editing

The complete Python suite passes: **307 tests**, including unchanged automatic-preset aesthetic baselines and five new preparation tests. The new room-first browser harness passes **18 checks**; the existing detailed room workflow passes **16 checks** after explicitly selecting Fine-tune. No JavaScript runtime errors were recorded.

Verified: default progressive disclosure, actual nearby placement, typed 4 × 4 m retention through wall fitting and full generation, edge-handle refinement, one-step Undo/Redo, delayed-response rejection while typing, one-at-a-time floor issues, explicit floor copying/removal, mobile control reachability, exact-editor tools, matching generated hashes, and G+1 stair access to the roof without another occupied floor. The detailed workflow found mobile main-view toolbar overflow; wrapping those controls fixed it and the rerun passes.

The running server on port 8765 was restarted and its new `/api/plan/prepare` endpoint produced a valid prepared plan from the rough fixture. Evidence: `evidence/room-first/`, `evidence/room-workflow/`. Rendering algorithms, assets, material recipes, lighting and cameras were not changed. Assistance is deliberately bounded; large overlaps, unsupported upper floors, inadequate stairs, inaccessible rooms and other unresolved geometry remain blocked rather than silently redesigned.

### 2026-09-30 — delivered roof access and restart restoration

The complaint exposed a delivery gap: fresh generation had roof access, but the actual bundled example still lacked the final usable flight. Server restart also discarded the in-memory latest-build ID. The delivered demo and its entire export package were regenerated with explicit two occupied floors and roof access. Successful builds now save an atomic latest-build pointer; startup restores only a complete, hash-verified build belonging to this workspace. Failed generation preserves the previous successful pointer.

**39 focused Python tests** pass, including the delivered artifact hashes, roof geometry/doors, restart restoration, corrupted/missing/foreign build rejection, server security and unchanged legacy aesthetic baselines. **48 browser checks** pass. The automatic G+1 case now walks the actual startup demo without replacing its scene or forcing roof access in a fixture: Ground → First → roof, F to open the door, terrace roaming, return and descent. Relocated custom G+2 stairs, linked-core editing and generation also pass. Evidence: `evidence/roof-access/browser-acceptance.json` and `live-verification.json`.

The demo retains its occupied room polygons, materials, camera data and lawn data. Necessary roof-access geometry changes include the continued stairs, roof opening and landing door; one stair-side plant moves clear of the flight and one displaced roof wall light is removed. Render algorithms and quality settings are unchanged. The studio on port 8765 was restarted without clearing the user's saved draft.

### 2026-09-30 — rough sketch Smart fit with Yes/No

The full Python suite passes **318 tests**; the five Smart fit tests also pass after the empty-floor-only resize guard was added. The new browser harness passes **17 checks** and the updated room-first workflow passes **18 checks**. Both record no browser runtime errors. The tests cover overlapping rough placement, a screenshot-style eight-room sketch with undersized bedrooms/kitchen/stair, visible proposal geometry and dimensions, Yes/No isolation, whole-plan Undo, manual wall access, stale approval/input protection, full generated plan hashes, roof stairs, mobile approval button visibility, and a real local server restart while the browser remains open.

Two issues found during verification were repaired: proposal buttons clipped on phones, and unnecessary resizing when an empty upper floor was the only unresolved issue. Exact 4 × 4 m rooms now remain unchanged through that workflow. Legacy aesthetic baselines pass. The renderer, material recipes, lighting and cameras were not modified. Evidence: `evidence/smart-fit/`, `evidence/room-first/`. The restarted studio on port 8765 returns a valid eight-room proposal using the new endpoint; no real browser draft was cleared or replaced.

### 2026-09-30 — independent inputs and accessible viewer controls

The new browser harness passes **19 checks**, including actual field-only generation while a saved eight-room custom plan, guide, text and furniture edit remain inactive. It verifies source selection, opening the editor without activating it, restoring displayed-house settings, placement reset/Undo isolation, matching generated building/scene hashes, free-cursor drag walking, held-key release when clicking controls, Fullscreen and Virtual tour from walking, and desktop/phone toolbar visibility. No browser runtime errors were recorded. Screenshot inspection caught and fixed the toolbar scrolling away when the canvas received focus.

**37 focused Python tests** pass for placement editing, saved input validation and custom plans, including legacy preset aesthetic baselines. The earlier input-coverage/spatial run passed **26 tests** (overlapping coverage, not an additive total). All **13 viewer Node tests** pass. Evidence: `evidence/input-modes/`; reproduction: `scripts/check_input_modes.mjs`.

Saved room/furniture moves are validated but remain editor-only until explicitly selected; they do not alter the generated plan hash while off. The default example starts from its own resolved settings and preserves inactive sketches. Materials, mesh recipes, lights and camera presets were not changed. Browser verification used Chromium/SwiftShader; Safari was not independently exercised.

### 2026-09-30 — floor-below guidance and screenshot-derived example

The complete regression run passed **327 tests** before the final three focused assertions were added. The final upper-floor/Smart-fit/preparation run passes **18 tests**, including lower-floor immutability, duplicate-stair detection, alignment without duplication, named support conflicts, usable upper fitting, preserved bedroom/guest dimensions, narrow-stair guidance and structured malformed-request errors. Existing automatic aesthetic baselines passed in the full run.

The upper-floor browser harness passes **13 checks**: loading the bundled worked example with matching hashes, ground drawing-room/veranda semantics, automatic footprint/stair overlays, Yes/No proposal isolation, lower-floor preservation, Undo, duplicate-drop prevention, immediate named support guidance, two fixed 16-cell boards, first-floor Dollhouse and full editor regeneration. Evidence: `evidence/upper-floor/`; reproduction: `scripts/check_upper_floor.mjs`. A separate live check covers the home-screen sample button, passive guide viewing and phone controls.

The sample is reconstructed from screenshot dimensions and approximate positions. The original reconstruction is retained at `examples/custom/your-sketch-original.floorforge.json`; the fitted G+1 project is `examples/custom/your-sketch-g1.floorforge.json`; all generated artifacts are in `examples/your-sketch/`. Bedroom and drawing-room sizes are retained. Necessary fit changes are listed in `example-notes.json` and the editor's change list. The current stair model requires 2.2 × 4.1 m for its default two-flight arrangement, rather than the screenshot's 0.9 × 3.6 m slot. Upper-floor starter proposals reuse the lower rooms and aligned core; upper Smart fit freezes all other floor geometry. Open-air areas below are excluded from the suggested support footprint. This footprint is a geometric planning aid, not a structural load-bearing calculation.

One delivery defect found and corrected during browser testing was a plan hash mismatch caused by Python integral floats versus browser JSON integers. The bundled sample is published using browser-compatible numeric representation; its geometry is unchanged by that conversion. Passive saved cell guides no longer run unrelated automatic-planner checks while the authoritative custom plan is active. No material recipes, lights, camera presets or rendering algorithms were modified.

### Spatial room board (2026-09-30)

`tests/test_room_board.py` covers position-to-canonical compilation, all eight stair locations, upper floor connection, open-air constraints, impossible capacity, duplicate spots, and inactive saved board isolation. The board uses independently fitted room bands on either side of a common passage. No renderer/material/lighting recipes were changed for this workflow.

`scripts/check_room_board.mjs` exercises the actual browser: add at a selected spot, drag, two-tap swap, Undo, linked stair moves, fitting preview, No/Yes, matching G+1 roof model generation, persistence, touch input and phone layout. Artifacts are under `evidence/room-board/`. The default example and existing detailed drawing remain intact; simple-board approval is the point at which the new fitted canonical plan replaces the previous drawing.

### Sample project gallery (2026-09-30)

Five complete offline projects are listed in `examples/gallery/catalog.json`. The saved Verandah sample was rebuilt from the published building brief for build `bd08a75b49f2a0341791581f`; its rooms, scene nodes and materials compare identically to that saved design. Unrelated draft inputs and attachments are omitted from the reusable sample. The original example is served intact from `examples/demo`.

`tests/test_sample_projects.py` checks matching project/build/scene/report/drawing hashes, complete export files, actual catalogue metadata, route traversal rejection and sample variety. `scripts/capture_sample_gallery.mjs` renders real thumbnails through the existing viewer. `scripts/check_sample_gallery.mjs` exercises browsing without mutation, live dollhouse floor switching, adopting an editable sample, returning to the previous project after refresh, and phone layout. Evidence is saved in `evidence/sample-gallery/`.

### My Desired Home (2026-09-30)

The sixth sample is an east-facing 50 × 50 ft G+1 home with the requested 8 ft front, 5 ft south and 12 ft north setbacks. The unspecified rear setback is provisionally 5 ft and is explicitly recorded in its specifications and design guide. Ground and first each contain nine authored spaces. The residential care-room concept includes individually editable reclining and attendant beds, a TV, a wide living connection and level glass access to a covered veranda. It is not a clinically specified ICU. Upper terraces and linked stairs to the roof are represented in the canonical model; the roof is not another occupied storey.

All **46 focused Python tests** pass, including the existing automatic-preset aesthetic baselines, requested room connections, north parking, aligned roof stairs, furniture and exported project hashes. The final **11 browser checks** pass: sample adoption, exact specifications/editor, cell overview, 2D drawings, 3D editables, unchanged hash while switching views, restoration of the previous project, refresh persistence, phone navigation and no runtime errors. Chromium/SwiftShader was used; Safari was not independently tested. Evidence and reproduction scripts are in `evidence/desired-home/`, `scripts/check_desired_home.mjs` and `scripts/capture_sample_gallery.mjs`.

Visual inspection of the ground, first and roof views caught an unfurnished dining area. The authored dining width and opening offsets were adjusted to accommodate the existing four-seat furniture recipe. Existing rendering materials, lighting and cameras were retained. The complete sample includes PDF/SVG, DXF, GLB, IFC, editable project JSON, specifications and a dimension table. The 16-cell guide is a coarse overview, not exact geometry; small rooms can share a cell. Browser-local saved working copies and the new project/view selector preserve separate editing contexts.

The live server on port 8765 was restarted with all six samples available and the previous generated build `bd08a75b49f2a0341791581f` retained. No user browser storage was cleared or modified by the isolated browser verification.

### My Desired Home — connected living and upper overlook (2026-09-30)

The sample now has a 3.25 × 2.80 m kitchen (9.10 m²), with full-height cased kitchen–dining, dining–living and living–stair connections. The kitchen/stair partition remains solid. Drawing-room width changes to 2.708 m to retain the existing setbacks, building envelope, care room and bedrooms. The first-floor lobby wraps an approximately 8 m² living void; its actual slab and the lower ceiling are cut, with 1.10 m glass guards and a separate exterior glazing wall. The sofa sits substantially beneath the opening. The upper office becomes 2.70 × 2.80 m and its arrival lobby widens to keep access around the overlook.

Explicit `openToBelow` voids use guards rather than automatically generated tall indoor walls; manually authored exterior walls remain. Full-height cased stair sides are allowed only when they include at least 750 mm of the front landing. Ordinary doors into flights remain rejected. Exposed stair flights receive outer rails and the upper well receives a guard. Existing automatic aesthetic baselines pass. Dollhouse mode shows lower furniture when the selected floor has a void, so the overlook is legible; ordinary floor cutaways remain unchanged.

The focused Python suite passes **49 tests**, and all **13 viewer tests** pass. Tests include preserved kitchen/stair separation, full-height openings, actual slab/ceiling holes, atrium guarding, sofa position and rejection of a door into a flight. Fresh browser verification and rendered evidence are in `evidence/desired-home/`.

The final browser run passes **13 checks**, including visibility of lower-floor furniture through the first-floor void and preservation of the authored atrium/open stair connection through save/reopen. The server was restarted and export checksums/ZIP integrity pass. Reopen the sample from the Sample projects group to adopt this revision; existing local working copies are not overwritten.

### My Desired Home — care seating and caregiver extension (2026-09-30)

The user selected a compact extension into the rear outdoor strip, subject to local setback review. The sample retains the 50 × 50 ft east-facing plot, G+1 and accessible roof. Front/south clearances stay 8/5 ft. North clearance is now 10 ft, and recovered width is distributed across room spans while protecting 150 mm walls and the aligned 2.20 m stair core. The caregiver extension leaves approximately 2 ft at the rear; the original southwest rooms retain their 5 ft rear line. These are authored concept dimensions, not confirmation of local setback compliance.

The care room is 5.176 × 3.500 m (18.116 m²), with one centered reclining bed facing the north-wall TV, one chair on either side, an equipment table to the right and a small cupboard to the left. The TV is between two north sidelights, with the veranda glass opening to the occupant's right. All six furniture groups are independently editable; the equipment monitor is an illustrative prop. The new caregiver bedroom is 3.300 × 2.642 m and its attached toilet is 1.726 × 2.642 m. A 1.0 m door connects it directly to the care room. The ground plan now has eleven spaces and four bedrooms total, including the caregiver bedroom; the care room is separate from that count.

The care room extends forward into part of the previous veranda/living footprint so the rear suite has usable dimensions. The living room becomes an L shape, retaining the open kitchen–dining–living–stair path. The first-floor overlook is adjusted to a 3.149 × 2.500 m guarded void wholly above the living room, keeping a ceiling over the care room. Materials, lighting and furniture styling remain the existing recipes. Side parking is retained outside the widened building; existing parking offsets for larger side gaps remain unchanged.

All **51 focused Python tests** and **13 browser checks** pass. Tests cover furniture counts, centered recliner/TV alignment, chair/cupboard sides, non-overlap and 600 mm door approaches; direct caregiver/toilet connectivity; preserved open living/stair routes and void; roof access; sample persistence and consistent plan hashes across specifications, editor, 2D/3D and exports. All **27 manifest checksums** and the export ZIP pass. Rendered evidence is in `evidence/desired-home/`. Browser verification used Chromium/SwiftShader; Safari was not independently tested.

The port 8765 server was restarted, retaining previous generated build `bd08a75b49f2a0341791581f`. Existing browser working copies were not overwritten. Reopen **Sample projects → My Desired Home** to adopt the updated sample. Plan hash: `198b4aa4f42ff9a65d2e6e93ab2c941d2c232e4a708d1ff8222fd36e36b725b4`.

## Desired Home — larger rooms, dining entrance and under-stair WC (2026-09-30)

The 50 × 50 ft east-facing sample now uses the full rear depth with a provisional zero rear setback. Its envelope is approximately 35 × 42 ft. Drawing room: 4.018 × 3.300 m; southwest bedroom: 4.150 × 3.802 m; care room: 6.068 × 3.500 m; caregiver bedroom: 3.000 × 2.502 m with a single bed. The direct caregiver/toilet connection, six care furnishings, open living circulation, guarded upper overlook and G+1 roof stairs remain. The former rear common bathroom is replaced by a 1.300 × 1.450 m WC/washbasin beneath the return stair flight. It has a 2.10 m ceiling and no shower. Mechanical exhaust for the internal toilets remains a detailed-design requirement. There are no windows on the rear boundary.

Under-stair rooms have an explicit host reference and validated stair approach/headroom; the overlap exception applies only to that room and its host stair. Their partitions and door are low geometry in the rendered model, drawings and IFC. The stair is enlarged to 2.80 × 5.10 m to retain a clear approach. Canonical opening offsets are checked against host lengths. Stair area schedules exclude the WC area to avoid double-counting. New optional single-bed and tiled-front-court settings do not alter default presets. A wide cased dining opening can share furniture space only when a continuous 800 mm route reaches all its openings. Existing furniture placements are attempted first.

The dining front opening is now an operable glazed door with three entrance levels connecting to the paved court. Front lawn/planting and entrance planters are removed; paving also covers the pockets beside the existing porch steps. Interior and side-yard planting remains. The sample project, specifications, cell overview, SVG/PDF/DXF, IFC and GLB have been regenerated together; all 27 manifest files and the export ZIP checksums match.

Verification: **391 Python tests pass across the full run and permitted localhost-test rerun**. The initial sandboxed full run passed 384 tests; seven server tests could not bind localhost sockets. Rerunning the security suite and final sample tests with localhost permissions passed all 36 tests. The focused geometry/sample/preset suite passed 54 tests, including unchanged automatic-preset aesthetic baselines. The browser checks exercise sample adoption, editor geometry, specifications, 16-cell overview, 2D drawings, 3D, save/refresh and project switching. Physical walkthrough checks pass for the dining door/entrance steps in both directions, standing entry/exit at the under-stair WC, and Ground → First → roof stair ascent. Chromium/SwiftShader was used; Safari was not independently tested. Evidence: `evidence/desired-home/`; reproduction: `scripts/check_desired_home.mjs` and `scripts/capture_sample_gallery.mjs`.


## Desired Home — half serving counter and rear bathroom (2026-09-30)

The kitchen–dining opening now contains a white-base, wood-top serving counter, 1.65 m long, 0.40 m deep and 0.95 m high, with stacked plates and a serving tray. The other 1.65 m remains open. The optional authored opening flag is compiled into canonical counter geometry, shown in the room editor, rendered in the existing scene and included in drawings and exports. Furniture placement reserves its footprint. Existing automatic-preset aesthetic baselines remain unchanged.

The common bathroom returns to the rear service area beside the southwest bedroom, with a full-height ceiling and a door from a living-hall alcove. The separate care-supplies room is absorbed into the bathroom; the care-room cupboard remains. The care room has an L-shaped service recess and 17.44 m² of clear area. Its recliner, two chairs, equipment table, cupboard, TV and veranda connection remain. Both stair flights are completely clear beneath. Ground floor now contains eleven authored spaces.

Verification: **51 focused Python tests and 21 browser checks pass**. Browser checks include walking through the open half of the kitchen opening, standing bathroom entry/exit, dining entrance in both directions, Ground → First → roof stair ascent, matched specifications/editor/cells/drawings/3D, saved-project restoration and phone navigation. Chromium/SwiftShader was used; Safari was not independently tested. Real rendered counter evidence: `evidence/desired-home/serving-counter.png`. Reproduction: `scripts/check_desired_home.mjs`, `scripts/capture_sample_gallery.mjs`.

The sample is rebuilt with matching project, scene, drawings and export hashes. Existing local working copies are preserved; reopen **Sample projects → My Desired Home → Open project & all views** to adopt this revision. Plan hash: `11547b5d5fb712086b00ec8ec42a0917b9bb076126ce0d137767588ac2ce6342`.

## Desired Home — expanded care suite and service wing (2026-09-30)

The revised concept explicitly uses a **60 × 55 ft site**, as allowed by the user if needed. The original 50 × 50 ft sample is preserved separately as `my-desired-home-50ft` in the gallery; its 27 manifest files and ZIP remain intact. Existing browser working copies are not changed. Front/south/north allowances stay 8/5/10 ft; the zero rear allowance remains subject to local review.

The rectangular care room is 7.616 × 4.650 m (35.41 m²), and the clear veranda is 4.066 × 2.750 m (11.18 m²). Living and veranda doors are genuine three-track sliding glass assemblies: two movable leaves stack over the first, including their collision geometry. Their nominal apertures are 2.8/3.4 m and approximate clear passages are 1.76/2.16 m. The veranda's optional `clearAccess` setting omits decorative furniture and plants. The modeled 2.2 × 1.1 m recliner footprint can move toward the TV side, rotate 90 degrees and pass onto the veranda without intersecting the other care furniture or stacked glazing. This checks the model geometry, not clearance for unspecified real clinical equipment or certification.

The toilet returns beneath the higher stair flight, with a 2.10 m ceiling, WC, basin and ventilation provision. The 2.8 × 5.1 m stair core stays aligned through First and roof; occupying its unused volume avoids reducing the modeled headroom and landings. A 1.35 × 1.85 m pantry and 1.35 × 1.30 m open wash yard have separate kitchen doors. The latter has a basin, drain and no roof. A freestanding-sofa fallback retains living seating when wide doors prevent a wall-backed layout; existing layouts are attempted first. The kitchen serving divider, tiled front court, double-height overlook and care furnishings remain.

**54 focused Python tests, 14 viewer unit tests and 26 browser checks pass.** Tests cover actual sliding-panel collision, closed/open behavior, care furniture, recliner translation/rotation, stair-toilet fixtures and headroom, open wash roof geometry, matched plans/exports and retained original sample. Browser walkthroughs verify the toilet, both stair flights, dining exit/return, half-counter passage, both care glass connections, pantry and wash yard. Save/reopen, specifications/editor/cells/drawings/3D navigation, current-project restoration and phone layout also pass. Chromium/SwiftShader was used; Safari was not independently tested. Both sample packages pass all 27 manifest checksums and ZIP integrity checks. Rendered evidence is in `evidence/desired-home/`.

Plan hash: `b3d15460e7a1849708e1e3ee06198cf60781c376efd4a7275bbe24dfff59ca85`. Rebuild with `scripts/build_desired_home.py`; verify through `scripts/check_desired_home.mjs`, `scripts/capture_sample_gallery.mjs`, `tests/test_desired_home.py` and `web/viewer/src/openings.test.js`.


### Desired home — living and veranda revision (2026-09-30)

The 60 × 55 ft east-facing sample now has a 36.99 m² living hall, 18.04 m² veranda and smaller 39.14 m² L-shaped care room. The caregiver bedroom is 7.77 m². The shorter drawing-room extension opens into living; living, drawing and care each connect separately to the veranda. Front-right parking and the 5 ft left service lane remain. The care furniture is placed in the largest rectangular bay so it stays out of the L-shaped notch. Boundary walls are clipped where custom rear wings reach the boundary, eliminating the duplicate dark wall cap inside the care room; legacy sample geometry is unchanged.

Validation: 56 focused Python tests and 14 viewer tests pass. All 30 isolated browser checks pass, including editor/specifications/cell guide/2D/3D consistency, real walking through the new veranda and caregiver connections, climbing to both upper levels, refresh and saved-project switching. A geometric swept-footprint check verifies the recliner translation and turn through the care veranda opening. All 27 manifest files and their ZIP entries match for both this sample and the preserved original 50 × 50 ft example. Regenerated actual 3D captures are in `evidence/desired-home/`.

Plan hash: `da6ca6ce98ef12c951cd4a5dbe5c61dec78966ee1af07fae6e8b2435f20554c4`. The live server was restarted on port 8765 and retained default build `bd08a75b49f2a0341791581f`. Local browser working copies were not overwritten. Geometry screening passes; boundary approvals, structural design and clinical/accessibility specifications are not established by these software checks.


### Desired home — bedroom suite and larger hall (2026-09-30)

Restored full-height drawing/living separation. The ground bedroom is narrower, with its bathroom inside the suite and a private bedroom entrance; the hall no longer has the bathroom doorway. Living reclaims the former bathroom, 1.3 m of bedroom width and the care room’s rear L-shaped extension. The care room is now rectangular, with the living glass wall shifted 800 mm inward. The living/veranda sliding aperture is 2.6 m, and the upper living void grows to 12.81 m². The kitchen gains 200 mm in width; dining retains its 1.5 m stone table, with connected passages checked instead of reserving the whole width of large cased openings. Front parking, left service lane, caregiver suite and roof access remain.

The saved model, exact editor, cell summary, specifications, 2D sheets, 3D and export package were regenerated. 57 focused Python tests and all 32 isolated browser checks pass. Checks include the physical drawing-room wall, bedroom ensuite access, walking through the reclaimed bathroom area, care/veranda links, the route around kitchen cabinets, and stairs to first floor and roof. Care furniture containment, recliner turning, upper void/ceiling alignment and legacy preset visual hashes pass. All 27 manifest entries and ZIP contents match; the original 50 × 50 ft sample remains intact. Actual images include `evidence/desired-home/expanded-living.png` and `ground-3d.png`.

Plan hash: `bf98bb57e1fd06cd8cfb434318f5a06cc66a52b8c9f43591da1e906eb375ecf6`. Server restarted on port 8765; default build and user browser working copies preserved. These tests establish model consistency and simulated routes, not construction, structural or clinical approval.


## Desired home — garden-facing care suite and separate drawing room (2026-09-30)

Rearranged the east-facing 60 × 55 ft saved sample using the rear living recess for a 7.938 × 3.952 m care room. The recliner faces the TV with garden windows on its left, living and veranda sliding doors on its right, and a caregiver door near the left corner of the TV wall. The caregiver bedroom retains its exact 2.700 × 2.876 m dimensions. Its bathroom is on the rear of this compact right-side suite. The master bedroom polygon and attached bathroom are unchanged.

The drawing room is now 4.116 × 5.500 m, with exactly three doors (front, dining, veranda), a large parking-facing window and a veranda window. No opening connects it directly to living. The veranda moves rearward and has a clear 6.688 × 2.600 m bay plus a side return. The parking approach is paved through to the veranda. The living sofa remains beneath the guarded 13.27 m² upper void; upper circulation, two bedrooms, office and terraces are connected. The 5 ft rear garden strip and its side access remain open to the sky through all upper plates.

Validation: 58 focused Python tests passed (desired home, custom plan, roof access and saved samples). 33 browser checks passed, including real walking through the sliding doors, caregiver door, garden door, drawing doors, master ensuite, pantry/wash yard, and both flights to the roof. Editor, 16-cell overview, both drawing sheets, 3D modes, project switching and refresh preserve the same plan. The recliner translation/turning sweep passes with the modeled furniture and stacked glazing. The new dining door swings into drawing so it does not obstruct the dining entrance route.

Both sample manifests and ZIPs verified (27 files each). Original 50 × 50 ft sample hash remains 11547b5d5fb712086b00ec8ec42a0917b9bb076126ce0d137767588ac2ce6342. Updated sample plan hash: 808e2801985b9e4bccd51bce0e1af73a82801cec3423d7c5d6492457e47eef69. Three mechanical ventilation design notes remain; no geometry errors or door-swing clashes. This remains a residential design concept requiring site, structure, ventilation and equipment review.

## Desired home — porch finishes and compact caregiver garden return (2026-09-30)

Limited this revision to the requested porch/veranda finishes and caregiver suite. The veranda and parking approach receive pale stone paving, timber ceiling/boundary accents and warm wall lamps. The veranda remains free of furniture and planters. The caregiver sleeping bay remains 2.700 × 2.876 m, with a 1.350 × 1.524 m rear return consuming 2.0574 m² (about 22 sq ft) of the garden. A new 1.100 m glazed door connects that return directly to the garden. Its 2.700 × 1.450 m toilet moves to the front of the same caregiver unit. A compact 900 mm cupboard preserves circulation around the existing inward-swinging ICU connection.

The layout-lock fixture compares every unaffected authored room, opening, upper-floor wall and stair against the previous saved project. The ICU geometry, furnishings and physical caregiver-door position/swing remain unchanged, as do the rest of the house, car approach dimensions and front entrance.

Validation: 60 focused Python tests and all 35 isolated browser checks pass. The new checks physically walk from ICU through the caregiver room and its L-shaped return to the garden, and separately enter the relocated attached toilet. Existing room connections, stairs, editor/specifications/cell guide/2D/3D switching, saved-project restoration and refresh pass. Both sample packages pass all 27 manifest checksums and ZIP integrity checks. Rendered evidence: `evidence/desired-home/porch-finish.png`, `veranda-finish.png`, `caregiver-garden-door.png`. Chromium/SwiftShader was used.

Plan hash: `ae1bc676c719efbcefc1daaf4b640e45aa62677c375dde1220f36b25110cf4fa`. The original 50 × 50 ft sample remains unchanged. Existing browser working copies are preserved; reopen Sample projects → My Desired Home → Open project & all views for the revised preset.

### Main vehicle gate interaction (2026-09-30)

The main vehicle gate was fixed scene geometry and therefore absent from the nearby-opening controller. It now has two inward-opening leaves, with explicit gate motion descriptors, the same F/tap prompt as doors, and collision that follows the animated panels. Both panels stop if they would intersect the visitor. House layout, dimensions and plan hash are unchanged. The saved sample and embedded offline preview were rebuilt; the live server serves the fix.

Validation: 100 desired-home/exterior Python tests, 15 viewer unit tests and 41 isolated browser checks pass. Browser checks use the actual F key from the street and parking court, verify both prompts, verify the closed gate blocks walking, and walk through the open gateway. All 27 export manifest files and ZIP entries match. Live-preview captures: `evidence/desired-home/main-gate-closed.png` and `main-gate-open.png`.

### Desired home — parked car and front upper window (2026-09-30)

Added a pearl-silver compact car in the right parking bay and a 2.2 × 1.5 m window to the front-facing upper arrival-lobby wall above the entrance. The window uses matching dark frames. All room footprints and existing connections are unchanged. The vehicle is included in saved scene geometry and collision; its position preserves the gate swing and the walking route around the entrance pillar to the veranda. Legacy automatic-preset gate geometry was restored to preserve its visual baseline while custom-project gates retain their interactive leaves.

Validation: 53 focused Python tests and all 43 isolated browser checks pass. Browser checks cover actual gate interaction, walking beside the parked car, the upper window, all existing room connections, stairs, saved-project switching and refresh. Both sample packages pass all 27 manifest checksums and ZIP integrity checks. Rendered evidence: `evidence/desired-home/car-and-front-window.png` and `parked-car.png`.

Plan hash: `08056cfafde9186c17a15d269dccec0bfd62d3107a91cb88806f824f3328bc7f`. The live preview was restarted with its existing default build preserved. The original 50 × 50 ft sample and user browser working copies remain unchanged.

### Desired home — optional Kylaq representation (2026-09-30)

Replaced the generic car with an originally authored olive-gold Kylaq representation, using the official 3995 mm length, 1783 mm body width, 2566 mm wheelbase and 1619 mm roof-rail height as modelling references. Includes sculpted wheel wells, tyre profiles, split-spoke wheels, split front lighting, ribbed grille, door seams, handles, roof rails, glazing and furnished interior. This is an architectural representation, not OEM CAD or a verified photoreal replica. References: https://www.skoda-auto.co.in/_doc/47c740d9-041a-4384-ad47-3169cea47de0 and https://www.skoda-auto.co.in/models/kylaq/kylaq/kylaq-design. No third-party mesh or photo texture was imported.

Both offline preview and editor now have a Show car / Hide car button, with browser-local persistence keyed by plan. Car geometry is isolated from house surfaces and collision. Hidden cars do not obstruct walking or appear in presentation GLB exports; showing is rejected while the visitor occupies the vehicle geometry. Canonical design exports keep the authored car. Room geometry and plan hash remain unchanged.

Validation: 53 focused Python tests, 17 viewer unit tests, 46 full-house browser checks and 8 dedicated preview checks passed. These cover gate access, walking beside and through the empty bay, occupied-space protection, refresh persistence and mode switching. After the final material/trim refinement, both vehicle collision tests and all 8 preview checks were repeated successfully. Both sample packages pass all 27 manifest checksums and ZIP integrity checks. Actual rendered evidence: `evidence/desired-home/kylaq-front.png`, `kylaq-toggle.png`, and `car-and-front-window.png`.

### Desired home — skylit courtyard and L-shaped front balcony (2026-09-30)

Bedroom 1 now enters from the stair-side living hall. Its main bay gives 200 mm and the care room gives 400 mm to a 1.85 m-wide garden between them. Both have courtyard windows, living has a glazed garden door, and the existing care/caregiver garden doors remain. The clear-glass cover has a high-level ventilation gap, planted borders, stone paving and warm path lights; upper floor and opaque roof geometry are cut away above it. The upper gallery routes around the lightwell and retains a 10.70 m² living atrium. The master ensuite, caregiver suite, kitchen, drawing room, veranda, stairs and parking geometry are preserved.

A 1.2 m setback to the first-floor office and lobby front creates a continuous L-shaped balcony linked to the existing right terrace. Balcony walking, glass guards, both front windows and the terrace entrance were checked. Thin stone piers, dark window surrounds, slab fascia and timber soffit finishes refine the side/front elevations without further room changes. The new lightwell requires corresponding local reductions to the upper bedroom and bathroom. Measurements are in the regenerated DESIGN_GUIDE.md and specifications.json.

Validation: 56 Python tests passed (desired home, custom plan, wall junctions); 48 full-house browser checks and 4 courtyard/balcony checks cover walking routes, doors, stairs, car toggle, gallery bypass and balcony. Both sample packages pass 27 manifest checksums and ZIP integrity checks. Screenshots: courtyard-garden.png, balcony-front.png, facade-side.png and balcony-walk.png in evidence/desired-home. The preview was refreshed; original 50 ft sample and default server build remain unchanged.

Plan hash: `14565753cf59c32b3a305815d44ac02f28976eadc58861c9494c17e669b43d9f`. Geometry and visual concept only; structural glazing support, rainwater falls and construction details are not engineered.

### Desired home — rectangular ICU, straight caregiver suite and larger lawn (2026-09-30)

With the user's approval to reduce the bedroom-side courtyard, the ICU is now a full 6.788 × 4.150 m rectangle (28.17 m²). The adjacent caregiver bedroom (2.400 × 3.126 m) and attached toilet (2.400 × 1.300 m) form one straight unit. The retained courtyard is a 1.850 × 0.900 m skylit lightwell with a separate covered edge under the unchanged upper gallery. The master bedroom, ensuite and every upstairs room remain unchanged against the saved pre-revision fixture.

The TV moves toward the recliner's left, with a 2.450 m-wide, low-sill lawn window to its right. The right garden is 2.700 × 5.776 m with 12.48 m² of actual grass, perimeter pots, timber accents and warm lights. The main veranda and its physical ICU/living doorways remain. The caregiver's independent 1.100 m sliding exit reaches a 1.326 m rear path, the lawn, veranda and outside without passing through the ICU.

Validation: all 56 focused Python tests pass (32 custom-plan/wall-junction tests plus the final 24 desired-home tests). All 48 full-house browser checks and 2 focused garden checks pass. Checks cover actual door operation and walking, caregiver/toilet access, the independent rear route, recliner movement through the veranda opening, the recliner-to-lawn sightline, stairs, gate, car toggle, saved-project refresh and unchanged rooms. Both packages pass all 27 manifest checksums and ZIP entry comparisons. The live in-app preview was refreshed successfully.

Rendered evidence: `evidence/desired-home/recliner-lawn-view.png`, `care-lawn.png`, `rear-caregiver-entry.png`, `caregiver-rear-exit.png`; results in `checks.json` and `rear-caregiver-checks.json` in that directory.

Plan hash: `2fc14e18e1dfc0de0a7a4e8a16d6eb4600fe067fe37c9c81f16f1a0294df7038`. The original 50 × 50 ft sample retains hash `11547b5d5fb712086b00ec8ec42a0917b9bb076126ce0d137767588ac2ce6342`.

### Desired home — close living-hall access to ventilation lightwell (2026-09-30)

Removed `g-living-garden-door` and regenerated a continuous plain wall in its place. All room polygons, other openings and furniture positions are retained. The lightwell and its covered edge are designated service-only outdoor spaces; adjoining bedroom/ICU/bathroom windows, drainage and the ventilated glass canopy remain. Service-only spaces cannot be used to bypass occupied-room access validation, and doors into them are rejected.

Validation: 46 desired-home/custom-plan Python tests passed, including rejection of occupied rooms marked service-only and doors into the lightwell. All 48 full-house browser checks passed, including walking collision against the replacement wall and absence of an interactive door. Two focused visual checks passed. All 27 manifest hashes and ZIP entries match. Live preview refreshed. Evidence: `evidence/desired-home/living-lightwell-wall.png` and `lightwell-wall-checks.json`.

Plan hash: `e7d702feba6911ecc96098d507132c25df198d7bdfab5ab9a82ea238c666616a`.

### Desired home — symmetric ICU TV wall (2026-09-30)

Centred the TV on the 4.15 m garden-facing wall, with two matching 1.000 × 2.100 m windows, 300 mm sills and symmetric 200 mm corner offsets. The recliner shifts 375 mm sideways to the same centreline (y = 10.625 m); its distance from the TV wall is retained. Room polygons, other openings and all upstairs geometry are unchanged. Both windows look onto the existing lawn.

Validation: all 24 desired-home tests pass, including furniture/door clearance, recliner transfer to the veranda, centred TV geometry and lawn sightlines through both windows. Two focused browser checks pass with no page errors; the actual recliner view was visually inspected. All 27 manifest checksums and ZIP entries match. The live preview is refreshed. Evidence: `evidence/desired-home/recliner-lawn-view.png`.

Plan hash: `eeed415c18412cde317742062b07dae163e2552ef740a4e52f60fd449f776010`.

### Desired home — left equipment wall and corner cupboard (2026-09-30)

Replaced the two 1140 mm left-wall window panels nearest the caregiver entrance with solid wall; the remaining 3420 mm window retains three equal panels in their former positions. The cupboard is tucked beside the caregiver door in the head-wall corner (900 mm wide, 400 mm deep), clear of its approach and swing. The equipment table moves to the left solid wall, with no visitor chair on that side. Three visitor chairs sit on the right. The recliner moves 500 mm back and 250 mm left, to (12.200, 10.875) m; the TV remains centred at y=10.625 m. Room polygons, upstairs and unrelated openings remain unchanged. Space is reserved for the requested equipment; specific device models and dimensions have not been added.

Validation: all 24 desired-home tests and 48 full-house browser checks passed, including caregiver door access, independent rear exit, furniture clearance and the recliner translation/turn to the veranda. Two visual browser checks passed, screenshots inspected, preview refreshed. All 27 manifest checksums and ZIP entries match. Evidence: `evidence/desired-home/icu-equipment-wall.png`, `recliner-lawn-view.png`.

Plan hash: `737e594451322483be3eb60699b8de5f41f6f2accfe652e42e64e01984b4b101`.

### Desired home — remove narrow ICU head-wall window (2026-09-30)

Removed only `g-care-side-garden-window` (650 mm wide), including its frame, sill and curtains, and regenerated matching solid wall. Compared the full authored plan against the prior revision: this is the sole geometry change. All 24 desired-home tests passed; two focused browser checks verified the opening and its scene parts are absent with no page errors. Export checksums and ZIP entries match for all 27 files. Preview refreshed; screenshot: `evidence/desired-home/icu-head-wall.png`.

Plan hash: `39c929139468ac4f1abac4cb735bcde914a237177be36ac19c41e16fd241c9d5`.

### 2026-09-30 — southbound U stair and inward caregiver door

My Desired Home revision `46ac418b151f06a52ab03f7871eb59bf442203bff55bc2c9755cf055b89a18be` extends the aligned stair enclosure to the south boundary. The 90° rotated stair rises south, turns right west, then right north, with 1.10 m flights, 1.162 m landings and a 3.162 m slab well. Tall east-facing glazing replaces the south stair window. The two bedroom windows facing the filled recess are relocated to rear walls. Caregiver access swings inward with its hinge at the front end, leaving the independent garden route clear.

Validation: 75 tests passed across desired-home, custom-plan, roof-access, upper-floor and placement suites. All 48 full browser checks passed, including ground → first → roof, caregiver entry, rear lawn exit and attached toilet access. Three focused browser checks verify inward swing, the roof terrace exit and absence of browser errors. Screenshots: `evidence/desired-home/rotated-stair.png`, `stair-east-window.png`, `caregiver-door-inward.png`. All 27 manifest entries match both disk and ZIP for the revised sample and original 50 ft sample; original hash remains `11547b5d5fb712086b00ec8ec42a0917b9bb076126ce0d137767588ac2ce6342`. Live preview reloaded; default working project retained.
