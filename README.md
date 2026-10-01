# FloorForge Studio — 0.3.0-alpha

**A runnable, offline-first preliminary design application, with source, tests, generated examples and evidence. This is not a completed M0–M8 commercial release.**

The previous M0 response was unexecuted source. This distribution is a new multi-file implementation that has actually generated houses, drawings, meshes and export packages. Read `docs/REQUIREMENT_MATRIX.md` for the original brief's implemented, partial, unverified and missing requirements. Do not present this release as sanctioned, architect-approved, structurally designed, photoreal or construction-ready.

## See it immediately — no installation

Open **`START_HERE.html`**, then **`examples/demo/preview.html`** in a modern desktop browser. The preview contains the actual scene and the realistic walkthrough viewer, with no CDN, server, account or AI dependency. Its drawing is embedded too. WebGL2 is required for 3D; the drawing remains available without it.

## Walk through your home

Every generated home opens in a real-time, physically based walkthrough: an analytic sky and sun with soft shadows, image-based light, ambient occlusion, bloom and a filmic (AgX) grade; surfaces synthesised on your GPU at load time, with no texture downloads (white render, stamped cobblestone, pebbles, lawn, oak planks, porcelain and marble, stone cladding, patterned cement tiles, fabric); procedurally grown planting (frangipani, clipped shrubs, columnar conifers, spiral topiary, strelitzia, palms, ornamental grasses, hedges, indoor plants) swaying in the wind; and instanced lawn grass.

Choose **Walk in**, click the view and explore on foot:

| Input | Action |
|---|---|
| Mouse (pointer lock) or drag | Look around |
| `↑` / `↓` or `W` / `S` | Walk forward / backward |
| `←` / `→` or `Q` / `E` | Turn left / right |
| `A` / `D` | Move sideways left / right |
| `Shift` | Run |
| `Space` | Jump |
| `C` | Crouch |
| Scroll | Lens width (field of view) |
| `Esc` | Release the mouse; press again to return to the exterior |

The walk starts on the footpath outside the open pedestrian gate, facing the house, so you arrive as a guest does: through the gate, up the entrance steps and in at the front door. Walking uses capsule collision against the actual generated walls, furniture, railings and glazing, with gravity and step-up climbing: walk up the real stair treads to change floor, jump onto low platforms, crouch under obstacles. Touch screens get a thumb stick and a jump button. Lighting offers Daylight (the computed solar position), Golden hour, Blue hour, Night and Overcast. Indoors, each room is lit by its own captured light probe (sun, lamps and sky through its windows, bounced once off the room), and exposure and white balance meter the room like a camera as you walk between rooms. A neighbourhood context (street, footpath, neighbouring houses, trees, lamp posts) is drawn by the viewer only and is never exported as part of your design.

**Explore in a large view.** **⤢ Large view** fills the whole window with the home (true full screen where the browser allows it, a window-filling view everywhere else, including iPhone), keeping the view, mode and lighting controls. The **+** and **−** buttons glide the camera in and out, scroll or pinch zooms, and double-clicking a spot on the house glides in to orbit around it. **Capture** saves the current view as a large 3840-pixel still. Drawing sheets zoom too: **+**, **−**, Ctrl/⌘ + scroll or a double-click, drag to pan, and a large view of their own.

**Focus on the home, in the whole screen.** Every view frames the home itself, not the street: the camera keeps its viewing direction and moves to the closest spot from which the whole house fills the frame, clear of the toolbars laid over it. **◎ Focus** shows the home alone (street and neighbours set aside) filling the whole screen, in every view and mode, until you leave it. **Aerial** looks down over the roof, its terraces and the garden; **Top** looks straight down; the plan and the top view turn the plot's long side across the screen so the home uses the width. **Fit** re-frames after you have zoomed or orbited, and **⇤ Wider view** folds the brief panel away so the 3D takes the width of the studio.

**A home as built, seen from the street.** The compound wall has a pedestrian gate on the path to the front door, shown open, a separate sliding vehicle gate over the parking pad (or the carport), and a stone-clad pier beside the pedestrian gate with the house number, letterbox and gate light; a cobble driveway and a path of large two-tone slabs lead in. The Modern Tropical entrance is an L-shaped porch: steps across the door end of the landing that return down its side, every tread with an LED strip under its nosing, and a sit-out at the other end with a bench, a planter and a stone-clad column, in front of a tall timber pivot door in a black steel portal. Two-storey homes raise the stair into a stone-clad tower above the roof, beside an open roof terrace with a glass balustrade, loungers and planting and, where the roof has room, a sala like the one in the reference garden: slim black posts and roof over a slatted timber ceiling, a slatted back screen and a daybed on a floating timber deck with a hidden LED strip; a deep eave with a timber soffit and downlights shades the street front, and solar modules sit on a rack over the rear of the roof. Side passages are laid like the reference garden: large pale pavers staggered across a bed of black pebbles, a white pebble drip strip against the house, side boundary walls clad in horizontal timber boards with a breeze-block screen set into them, pots of planting and a stone wash basin. The front boundary is clad in stone on the street side, washed at night by up-lights at its foot, and the vehicle gate is a tall screen of vertical timber slats on a black steel frame. Where the rear garden allows, a stone water wall stands on the rear boundary on the axis of the patio: water falls from a steel lip into a pebble-lined trough lit from below, with the hedge parting around it. Inside the front door, a slatted oak ceiling on a walnut ground marks the foyer.

**Windows and terraces.** Every exterior theme uses one contemporary window system: slim aluminium frames with staggered sliding panes, slim sills, and obscured glass in bathrooms. Bedroom windows on the facade sit in slim projecting pods lined with timber. First-floor terraces have a timber deck, a frameless glass balustrade with a slim handrail, a pergola of timber louvres with downlights, and seating between planted corners.

The full extracted folder must stay together for the PDF/DXF/GLB/IFC links beside a preview to work. Viewing a sample is not generating a new design.

## Start simply, refine later

Choose **Design rooms → Arrange rooms** to place and size rooms. **Smart fit rooms** proposes room sizes, wall spacing, stairs, doors and windows. Choose **Yes** to use the fit or **No** to keep your sketch; one Undo restores the original. **Fit & preview 3D** also generates after approval. **Fine-tune** reveals detailed drafting tools when needed. See [the short user guide](docs/QUICK_START.md).

## Generate your own home

### macOS / Linux

Extract the ZIP into a normal writable folder, not inside the ZIP viewer. From that folder, run the two scripts:

```bash
bash setup.sh
bash start.sh
```

`setup.sh` finds the first installed Python 3.11–3.13 even when `python3` points to a newer release, creates or repairs the local `.venv`, installs the pinned dependencies, and runs a smoke check. If no supported Python is installed but `uv` is available, setup can provision Python 3.13 automatically. `start.sh` checks the environment and repeats setup automatically when it is missing, incomplete or out of date. No `chmod`, global package install or manual virtual-environment activation is required. On macOS, `FloorForge.command` is an optional double-click wrapper around `start.sh`.

The scripts need internet access for the first dependency install, unless `FLOORFORGE_WHEELHOUSE` points to a matching offline wheelhouse. They are developer launchers, not signed native installers.

### Windows

Install Python **3.11–3.13** with the Python launcher, extract the ZIP, and double-click **`FloorForge.bat`**. It calls `setup.bat` on the first run, then `start.bat`. Alternatively run those two scripts yourself. A console remains visible in this developer distribution.

The first setup installs exact-version Python dependencies into `.venv`. **Normal generation and the bundled viewer use no network after setup.** Node, Blender, an AI model and API keys are not required for the core; Blender is only needed for optional path-traced stills.

If installation fails, read the error and check the selected Python, network access and available disk space. Do not run with administrator/root privileges to work around an ordinary dependency problem. Optional features have separate installers and their failures do not disable the core.

## The workflow

Start with a tested preset: 40×60 ft / G+1 / three bedrooms; 30×40 ft / ground / two bedrooms; or 25×35 ft / ground / one bedroom. Then answer the eight questions that actually shape a plan:

1. **The plot** — width × depth in feet or metres. The studio shows the plot area and the open spaces it takes from its size (front and rear by depth, sides by width, as Indian byelaws usually tabulate them; a car-parking court takes a 5.5 m front where the plot is deep enough), and the buildable area that leaves.
2. **The road side** — pick it on the compass; the small plot in its centre turns its road edge to face that way. The front, gate and entrance face the road.
3. **Bedrooms** and 4. **storeys** (ground, or ground + first).
5. **Attached baths** — every bedroom, the master only, a number of bedrooms, or none (a common bath is always planned where a bedroom has none).
6. **Vastu** — not needed, if it fits, preferred or strictly (advisory; unmet preferences are reported, never faked).
7. **Must-haves** — pooja room, car parking, open kitchen.
8. **Budget** in lakh (a context, not a quote).

Everything else has a sensible default under “Go deeper” (open spaces, plinth, floor height, soil, cost rates, plan variant); typing your authority's own setbacks there switches the derived ones off. You can also **describe the home in words** — “30 by 40 north facing site, 3BHK duplex, all bedrooms with attached bathrooms, pooja room, car parking, open kitchen, budget 80 lakhs, vastu compliant” — and **Review what we understood** lists each phrase that was read and what it set, the phrases that were not understood (kept as notes, not applied), and any assumption made (such as “30 by 40 read as feet” or “1200 sq ft read as the standard 30 × 40 ft plot”). Plot areas in sq ft, sq yd/gaj, sq m, cents, guntha and marla, budgets in lakh or crore, G+1/duplex, BHK and bath counts, setbacks and floor heights are understood. Explicit room-location phrases such as “kitchen on the left”, “master bedroom at the rear” or “south-east kitchen” are also compiled as spatial hints. Unlisted or unparsed prose remains a reference note; it is not sent through to the planner as a hidden constraint. If a visible form control is changed after older description, imported-plan or AI data, that touched control is recorded as the final authoritative value; the review table shows the winning source and whether each visible input affects plan/site geometry, vertical 3D, finishes, metadata or reports only. Inspect the home, drawing set and design review; save a project JSON or export the entire design package.

**Quick Guide has a fixed 16-cell board per floor.** Ground, First and Second tabs retain room assignments and request broad front/rear/left/right placement. Cells carry no physical size and do not define exact boundaries. The bounded planner either meets the placement screen or reports a floor- and cell-specific conflict. For exact dimensions, authored openings, different floor plates and first-floor open terraces, choose **Custom Plan** and open the dimensioned editor. See [the editor workflow and geometry contract](docs/CUSTOM_PLAN.md).

Reference images are different: they are **manual visual references only**. The core does not inspect, trace or infer rooms, style or dimensions from their pixels. A saved project contains their name, hash and note, not their bytes, so keep the originals separately.

### How the plan is made

`floorforge/planner.py` plans the way an architect sketches: a public spine (living, dining, hall) with two stacks of rooms beside it — bedroom suites with attached baths and a dressing room for the master, the common bath, study, kitchen with its utility, pooja and store. It searches hall positions, stack orders and room depths and scores every candidate against residential planning rules: NBC 2016 Part 3 style minimums as hard limits (habitable room 9.5 m² / 2.4 m wide, a second bedroom 7.5 m², kitchen 5 m², bath 2.8 m² / 1.2 m), comfortable sizes that grow with the plot, proportions, a window on an outside wall for every habitable room and air for every bath, wet rooms clustered for short plumbing, a bath on every bedroom floor, a short hall, no bath beside or above the pooja or over the kitchen, and the Vastu hand (the plan or its mirror image). A pooja that finds no slot in the stacks is carved from a rear corner of the living room. Doors swing into the rooms they serve and are hinged at the nearer corner; windows come in stock module widths.

The generator is bounded, not universal. Infeasible requests return explicit errors rather than adding floors or pretending a positional cell supplied buildable dimensions. The tiny-plot example has one bedroom deliberately; a two-bedroom request has not been smuggled into a second floor.

New projects use only the fixed 4 × 4 semantic placement guide described above. Older project JSON that contains a metric `cell_mm` exact grid remains readable through the legacy compatibility path, including its old ground-floor and connectivity restrictions. The studio does not expose a variable grid or cell-size control; once an older grid is edited and saved in the current studio, it is represented as the 16-cell spatial guide rather than a promise to preserve its old metric cell geometry.

## What is included

- Deterministic source fusion and a cached, content-addressed Python DAG.
- G / G+1 / G+2 reference-family generation and an authoritative orthogonal custom-plan compiler, actual room polygons, opening-cut walls, aligned stair cores and a roof-open upper terrace.
- A responsive studio and the bundled realistic walkthrough viewer (Three.js, fully offline): furnished interiors, orbit/dollhouse/plan/walk modes, first-person walking with stairs, five lighting grades, PNG capture and an orbit-recording control. Six legacy facade recipes remain available.
- Four explicit exterior architecture families, with Modern Tropical as the default for new projects. Each has real porch, balcony, opening, facade-screen, landscape and planting geometry. There are also five independent interior palette choices, with Bright Natural as the default. The exterior upgrade contract and evidence are in `docs/exterior-upgrade/`.
- SVG drawings and an A3 PDF drawing/review set at 1:100 where the plot allows: plans with three dimension chains per side (openings, walls, overall), typed door and window tags (D, SD, O, W, V), coordination grid bubbles, finished floor levels, a north point and the section marker; a door, window and room schedule sheet (A-601); layered DXF floor plans with true DIMENSION entities; GLB; an IFC4 STEP exporter with a deliberately limited acceptance claim.
- A professional review: NBC-style room minimums, corridor width and circulation share, daylight (openings a tenth of the floor), bath ventilation, pooja beside or below wet rooms, baths over the kitchen, door-swing clashes and attached-bath shortfall, reported as recorded warnings with plain-language unresolved requests. Preliminary room/area/opening schedules, an editable cost scenario, timeline, solar study, Vastu readings (preferred / acceptable / avoid), services notes and review limitations.
- Session-memory local/cloud AI proposal adapters, which are off by default. Real provider/model inference was not run here.
- Path-traced stills with Blender Cycles: the viewer exports a presentation GLB (the **Blender GLB** button, or `scripts/export_presentation.mjs`) and `scripts/render_cycles.py` renders it under a physical sky, the site's sun and every fixture light. It needs Blender 4.2+ or the `bpy` wheel, not the core. Samples are in `evidence/cycles-*.jpg`.
- Optional Three.js/path-tracing/GSAP source, optional model download/start scripts, and native packaging recipes. These optional paths are not falsely marked built or accepted.

## Actual output layout

```
~/.floorforge/
  .cache/<stage>/<hash>.json
  builds/<build-id>/
    preview.html
    project.floorforge.json
    intent.json
    building.json
    scene.json
    report.json
    review.json
    sheets.json
    sheets/*.svg
    drawings.pdf
    floorplans.dxf
    model.glb
    model.ifc
    export-checks.json
    manifest.json
    FloorForge-export.zip
```

Builds are immutable. Editing an exported drawing does not update the source project. Save a revised project and regenerate; preserve externally edited drawings separately. Cache corruption and modified published files are rejected, not silently trusted.

## Developer commands

```bash
# Optional developer checks. Normal use only needs setup.sh and start.sh.
.venv/bin/python -m floorforge doctor
.venv/bin/python -m floorforge generate --project examples/briefs/compact.json
.venv/bin/python -m floorforge generate --target layout
.venv/bin/python -m floorforge serve --no-browser --port 8765
.venv/bin/python -m pip install -r requirements-dev.lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_reproducibility.py
# Optional browser evidence (Node + Playwright with Chromium; software WebGL is slow):
node scripts/capture_walkthrough.mjs
node scripts/capture_studio.mjs
# Optional path-traced stills (Node + Playwright, then Blender 4.2+ or the bpy wheel):
node scripts/export_presentation.mjs examples/demo/scene.json build/demo.glb
python scripts/render_cycles.py --glb build/demo.glb --scene examples/demo/scene.json --out build/renders --view hero --grade day
```

On Windows replace `.venv/bin/python` with `.venv\Scripts\python.exe`. Use `--out PATH` to put generated projects somewhere else. Ctrl+C stops the developer server. The windowed `desktop.py` launcher is intended for the native packaging recipes.

## Evidence, not marketing

`evidence/pytest.txt` and `pytest.xml` contain the executed suite. `evidence/reproducibility.json` compares two clean generations. `evidence/studio-browser.json`, `walkthrough-capture.json` and `browser-preview.json` record the browser checks. They are produced by `scripts/capture_studio.mjs` and `scripts/capture_walkthrough.mjs`. Screenshots are actual engine output, not generated-image substitutions.

DXF was read back and audited by ezdxf; GLB was read back by Trimesh. **That is not AutoCAD GUI acceptance or an independent glTF-validator pass.** IFC reference integrity was self-checked; independent IfcOpenShell/schema/viewer acceptance remains open. PDF page size and text placement were checked, but no physical printer/plotter was tested. Browser rendering used software SwiftShader, not a real GPU.

The supplied archive held 120 images and six videos, not the original FloorForge repository. Its claimed 243 legacy tests were unavailable and are not included in the new test count.

## Important release limits

The output has **no structural design, official NBC clause validation, sanctioned byelaw pack, geotechnical assessment, reinforcement schedule or accessibility/ICU certification**. The cost range uses editable example rates, not market quotations. “Strict Vastu” is reported as unresolved when unmet; it does not create a false pass.

The live renderer is a real-time raster approximation of photographic lighting. It has no path-traced global illumination and no ray-traced reflections; one light probe per room approximates bounce light. Its looks were verified in software-rendered Chromium, not on real GPUs. Path-traced stills come from the separate offline Cycles path, not the live viewer. 4K path-traced output, an interior cinematic film, individual furniture drag/rotate editing, automatic sketch/CV interpretation, a complete questionnaire and all native installers are not finished requirements.

## Rebuilding the viewer (developers only)

`web/viewer.js` is committed, so running FloorForge never needs Node. To change the viewer, edit `web/viewer/src` and rebuild:

```bash
cd web/viewer
npm ci
npm run build      # writes ../viewer.js
cd ../.. && .venv/bin/python scripts/regenerate_examples.py
```

No `.dmg`, `.exe` or `.msi` binary is disguised inside this ZIP. `packaging/` contains build recipes that still need execution, signing and clean-machine testing on their target operating systems.

## Documentation

See `docs/ARCHITECTURE.md`, `docs/REQUIREMENT_MATRIX.md`, `docs/AI_ASSIST.md`, `docs/RENDERING.md`, `docs/OPERATIONS.md`, `docs/ACCEPTANCE_PLAN.md`, `docs/RESEARCH_AND_DECISIONS.md` and `licenses/LEDGER.json`.

**Use this to develop and review a design with a competent local professional—not to instruct construction.**

### Exact per-floor plans

Choose **Quick Guide** for separate Ground/First/Second 16-cell placement boards, or **Custom Plan** for the full-screen dimensioned editor. Custom plans preserve clear room geometry, authored openings, floor assignments and linked U stairs; valid geometry bypasses the automatic planner. The G+2 example includes bedrooms and an accessible first-floor open terrace. Edits visibly mark old 3D and exports stale until the matching revision generates successfully.

See [the custom-plan contract, workflow and limits](docs/CUSTOM_PLAN.md). The editor supports orthogonal plans with a uniform wall allowance; it is not unrestricted architectural CAD or a construction-approval system.

Enable **Stairs to roof terrace** and regenerate to extend the actual linked core through the roof, with a landing door, walkable terrace and guards. In Walk mode use the stairs and **F** to open the door; the floor selector cannot teleport you. Custom core placement follows the drawing, and **Move linked stairs on every floor** keeps counterparts aligned in one undoable edit. Existing saved projects retain their old roof until this option is enabled.

## Sample project gallery

Open **Sample projects · explore in 3D** in the left sidebar for five completed homes with rendered thumbnails: the saved Verandah House, the original startup example, Garden Pavilion, Quiet Studio and Palm Terrace Villa. Explore their exteriors, furnished floor plans and walkthroughs immediately. Browsing keeps the current project untouched. **Use this sample** loads an editable copy, and **Back to my previous project** restores the preceding project.

Rebuild curated variants with `.venv/bin/python scripts/build_sample_gallery.py`; render their thumbnails with `scripts/capture_sample_gallery.mjs`. The saved favourite’s clean source brief is kept under `examples/gallery/briefs/`.
