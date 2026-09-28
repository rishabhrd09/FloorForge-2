# Executed verification — 0.3.0-alpha

**This release is runnable but does not complete the original M0–M8 requirements.** See the requirement matrix.

## Executed here

**Tests.** 214 tests passed, 0 failed (479.3 s). The results are in `evidence/pytest.txt` and `pytest.xml`. Beyond the earlier contracts, the suite now covers:
- the planner and review (`tests/test_geometry.py`): every fixture brief screened under NBC 2016 Part 3 style minimums; circulation at most 15% of a floor with halls at least 1 m clear; the professional screen quiet on the default plan (no low daylight, unventilated bath, pooja beside a bath, door-swing clash, or bath over the kitchen or pooja) and raising bath-ventilation and door-swing warnings on a deliberately defective copy; unresolved requests naming an attached-bath shortfall; facing that never rotates the plan (with Vastu off the plan is identical for every road side, with it on the same or its mirror);
- the drawings (`tests/test_exports.py`): ten sheets with plans at 1:50–1:125; dimension chains that close on the footprint on every side; one tag per opening, matching the door and window schedule; the section cut running up the stair flight; DXF DIMENSION entities equal to the drawn chains; schedule text that never cuts a room name;
- the survey and the text reader (`tests/test_intent.py`): six homeowner briefs read field by field (plot sizes and areas, road side, BHK, attached baths, G+1, lakh and crore, pooja, parking, kitchen, Vastu, setbacks, heights, style), phrases not understood and assumptions reported, and open spaces derived from the plot unless stated;
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
- a real 30×40 ft generation, the grid painter, three AI consent choices, project collection, a 390 px mobile layout and the **Blender GLB** download.

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
