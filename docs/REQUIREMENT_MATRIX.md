# Original brief — requirement-by-requirement status

**All original requirements complete: NO.** This is a delivered runnable alpha, not an accepted M0–M8 commercial release. No score or test count overrides a missing requirement.

TESTED_SCOPE = a bounded behaviour demonstrated here; PARTIAL = useful implementation with known gaps; AUTHORED_UNVERIFIED = source exists but its runtime path was not executed; NOT_IMPLEMENTED / NOT_VERIFIED / BLOCKED are explicit open work.

| Gate | Requirement | Status | Evidence / implementation | What remains |
|---|---|---|---|---|
| M0 | Reference inventory and fresh design direction | PARTIAL | evidence/input-inventory.json | Images reviewed in contact sheets; videos not fully reviewed; original repo unavailable. |
| M0 | Legacy contracts and 243 tests | BLOCKED | Input audit | Supply original repository and run unchanged suite. |
| M0 | Shared units, orientation and semantic building model | TESTED_SCOPE | model.py; orientation and geometry tests | No licensed surveying or georeferencing certification. |
| M0 | Typed contracts and pure stages | PARTIAL | Dataclasses; intent/layout/review modules | Strict complete annotations/type-check gate not run. |
| M0 | Selectable cached DAG and manifests | TESTED_SCOPE | pipeline.py; cache tests | Programme/openings remain coupled to layout; structural/render stages expose placeholders honestly. |
| M0 | Determinism from two clean runs | TESTED_SCOPE | evidence/reproducibility.json | Same runtime/OS; cross-platform bitwise equivalence unverified. |
| M0 | License and asset ledger | PARTIAL | licenses/LEDGER.json | Complete native/transitive redistribution audit open. |
| M1 | Eight-question path with derived defaults | TESTED_SCOPE | Studio survey: plot, road-side compass, bedrooms, storeys, attached baths, Vastu, must-haves, budget; intent.derive_setbacks and its tests | Bounded valid programme/plot range only; derived open spaces are typical byelaw values, not a verified local rule pack. |
| M1 | Source precedence, conflict and Used/Off | TESTED_SCOPE | intent.py; source tests | Image semantics/manual grid comparisons remain limited. |
| M1 | Free text understanding | PARTIAL | parse_text grammar (plot size/area units, BHK, attached baths, G+1/duplex, facing, lakh/crore, pooja, parking, kitchen, Vastu, setbacks, heights) with understood / not-understood / assumption feedback; sample-brief tests | Unrestricted prose, Hindi and semantic placement (which room goes where) not implemented. |
| M1 | Exact cell grid and L polygons | PARTIAL_TESTED | Grid union and nonrectangular tests | Only ground-floor manual grids; no arbitrary multi-level edited polygons. |
| M1 | Survey G/G+1 distinct floors | TESTED_SCOPE | Fixture/variants/stair tests | No G+2/G+3, stilt, basement or arbitrary room-per-floor programme. |
| M1 | No silent added storeys | TESTED_SCOPE | Intent and infeasibility tests | Rejected requests need explicit owner revision. |
| M1 | Open public zones/private room routing | TESTED_SCOPE | Portal graph and through-bedroom tests | Graph access does not prove furniture-clearance or universal accessibility. |
| M1 | Minimum-size, overlap and containment screen | PARTIAL_TESTED | review.py: NBC 2016 Part 3 style minimums, corridor width and circulation share, daylight share, bath ventilation, pooja/wet adjacency and stacking, door-swing clashes, attached-bath shortfall | Screening values, not a verified clause pack; local width/clearance by medial axis not computed. |
| M1 | Official NBC/byelaw validator | NOT_IMPLEMENTED | Statuses NOT EVALUATED | Authorised clause-specific jurisdiction pack and professional acceptance. |
| M1 | Aligned wet services and stairs | PARTIAL_TESTED | Planner stacking cost (baths over baths/utility, never over kitchen or pooja); layout/stair core tests | Full structural/headroom/MEP coordination not designed. |
| M1 | Automatic courtyard/lightwell/double-height solving | NOT_IMPLEMENTED | No hidden claims | Need new topology, void and circulation solver. |
| M1 | Eldercare/ICU/accessibility design | NOT_IMPLEMENTED | Preserved intent and NOT CERTIFIED status | Specialist patient/equipment/step-free route and services review. |
| M1 | Sketch/photo/OCR/CV interpretation | NOT_IMPLEMENTED | Browser manual references only | Recognition, confidence, tracing/correction and image persistence. |
| M1 | Vastu lever and strict satisfaction | PARTIAL | Planner chooses the plan hand by Vastu cost; review rates rooms preferred / acceptable / avoid; unmet-strict warning | No enforced strict optimiser over room placement or scientific claim. |
| M2 | True walls/openings and plan schedules | PARTIAL_TESTED | SVG/PDF/DXF plans with typed D/SD/O/W/V tags and the A-601 door, window and room schedule; stock window modules; tests | Professional drafting review, exact clear openings/finishes needed. |
| M2 | Overall/room/opening dimension chains | PARTIAL_TESTED | Three chains per side (openings, walls, overall) closing on the footprint, grid bubbles, levels, section marker; true DXF DIMENSION entities; tests | Internal room dimension strings and irregular-edge chains not drawn. |
| M2 | Site plan/elevations/stair section | PARTIAL_TESTED | Ten default drawing sheets including the schedule sheet | Elevations simplified; full facade/building details and slopes absent. |
| M2 | IS 962 convention certification | NOT_IMPLEMENTED | Layer/line-weight-inspired drawing system | No official standard compliance audit. |
| M2 | Indicative structural member/footing drawing | NOT_IMPLEMENTED | S-001 coordination axes only | No columns/beams/slab sizing/footings/rebar certification. |
| M2 | A3 PDF/SVG export | TESTED_SCOPE | Page/text checks and actual captures | Physical printer/plotter acceptance open. |
| M2 | DXF re-import | TESTED_SCOPE | ezdxf audit; deterministic metadata tests | AutoCAD GUI not tested; elevations/section not exported in DXF. |
| M2 | IFC4 export/re-import | PARTIAL_UNVERIFIED | IFC STEP self-reference checks | Independent schema/viewer untested; door/window-fill semantics incomplete. |
| M2 | GLB geometry export/re-import | TESTED_SCOPE | Trimesh round-trip | Independent glTF validator and a second viewer open; not one watertight house union. |
| M2 | DWG, STEP/BREP exports | NOT_IMPLEMENTED | No mislabeled substitute | License-reviewed backend and acceptance fixtures required. |
| M3 | Six user-selectable geometric exterior languages | PARTIAL_TESTED | Legacy style recipes remain available; `docs/exterior-upgrade/` adds four explicit exterior families (Modern Tropical is the new-project default) with real porch/balcony/opening/landscape/planting geometry on the live pipeline | No real-GPU fixed-camera realism acceptance per family, broad massing variety or structural facade design. |
| M3 | Road/kerb/gate/court/porch/door arrival | PARTIAL | A built frontage for every designed theme (floorforge/frontage.py): a pedestrian gate on the door's axis, shown open, a separate sliding vehicle gate over the parking pad or carport and a stone-clad letterbox pier; a cobble driveway and a slab path; the modern entrance is an L-shaped porch with lit steps, a sit-out and a tall pivot door. Tests keep the route from the footpath through the gate to the door clear and climbable for every theme, and the real capsule walker reached the door on four plots | No surveyed site levels/engineering of access. |
| M3 | Conditional parking/car/site request fulfilment | PARTIAL | Parking court/envelope validation; the vehicle gate is aligned with the carport, or placed over the widest stretch of front yard the entrance leaves free, with a cobble driveway | No detailed car model, full gate options or all outdoor programmes. |
| M3 | Articulated neighbours and context | PARTIAL | Viewer-only procedural neighbourhood sized from the plot: neighbouring houses with plinths, framed glazing, entrance doors under canopies and some balconies, street trees, lamp posts and a horizon tree line (never part of the design exports; included in the presentation GLB as context) | Generic context, not surveyed: no real neighbour heights, setbacks or scanned surroundings. |
| M3 | Compass-correct solar study | PARTIAL_TESTED | Orientation + solar implementation | No refraction, skyline, automatic front-lit-hour search or pvlib comparison. |
| M3 | HDRI normalisation and physical IBL | PARTIAL_TESTED | Default viewer: analytic Preetham sky (and a twilight sky model below the horizon) prefiltered into image-based light; indoors, per-room captured light probes with metered exposure and white balance; software-rendered captures | No HDRI asset import in the default viewer; luminance not photometrically calibrated; real-GPU colour acceptance open. |
| M3 | Geometry-accurate varied massing and terraces | PARTIAL_TESTED | True L polygons, mirrored/shorter plans, upper terrace; first-floor terraces level with their floor with a timber deck, glass balustrade and handrail, louvred pergola and seating; a stone-clad stair tower over the roof access and a solar rack on every designed theme; an open roof terrace with a glass balustrade and a deep timber-soffit eave on the modern theme (tested) | Not architecture optimisation or all requested typologies. |
| M4 | Detailed furniture/soft layers | PARTIAL | Authored mesh recipes and furnished captures | Curated high-quality library, all doorway clearances and full interiors remain open. |
| M4 | Visible-fixture-linked lights | TESTED_SCOPE | Fixture metadata tests; the viewer lights the nearest visible fittings (downlights as downward spots, line-of-sight culled) | Pooled lights cast no shadows; luminance not photometrically calibrated. |
| M4 | Dollhouse/top-down/floor inspection | PARTIAL_TESTED | Software-rendered captures; Aerial and Top views; every view fitted to the home itself, the plan and top view turned to use the screen's width; Focus shows the home alone filling the screen (studio check, framing unit test) | Shader clipping has no proper capped-solid dollhouse sections. |
| M4 | First-person at 1.6m with collision | PARTIAL_TESTED | Capsule collision against a BVH of the actual walls, glazing, furniture and stair treads; gravity, jump, crouch, run and continuous stair climbing; scripted and live walk captures (evidence/walk-*.png, walkthrough-capture.json) | Doors are fixed open leaves (no interactive state); no accessibility-route certification; real-GPU frame-rate acceptance open. |
| M4 | Click travel and interactive doors/drawers | NOT_IMPLEMENTED | No fake buttons | Navigation and interaction metadata/state required. |
| M4 | No room labels in 3D | TESTED_SCOPE | Viewer and actual captures | Labels remain in 2D/review only. |
| M5 | Cinematic arrival/interior/exit film | NOT_IMPLEMENTED | Orbit control only | Directed validated interior route and render/encode/QA needed. |
| M5 | Day/golden/dusk display | PARTIAL | Five lighting grades: daylight uses the computed solar vector; golden hour, blue hour, night and overcast are display grades that keep its azimuth | Non-daylight grades are not recalculated true solar times. |
| M5 | Raster PNG capture | TESTED_SCOPE | Viewer Capture re-renders the current view at 3840 px wide; the studio harness saves one and checks its width | Real-GPU colour acceptance remains open. |
| M5 | 12-second WebM orbit capture | AUTHORED_UNVERIFIED | Viewer MediaRecorder code | No recorded video acceptance or frame-rate benchmark. |
| M5 | Photoreal live path tracing / 4K still | PARTIAL_TESTED | Offline Blender Cycles path-traced stills executed here (bpy 4.5.14 LTS, CPU) from the viewer's presentation GLB: scripts/export_presentation.mjs + scripts/render_cycles.py; evidence/cycles-*.jpg and cycles-renders.json | No live in-browser path tracing; 4K supported by the script but not rendered here; renders are uncalibrated studies of preliminary geometry. |
| M5 | Editable Blender scene / FBX + JSON / tour frames | PARTIAL | render_cycles.py assembles and can save a .blend (--blend) with imported geometry, sky, sun, fixtures and camera; blender_scene.py keeps the FBX/tour-frame worker | FBX export and tour frames (blender_scene.py) not executed here; no validated interior camera route. |
| M5 | Astra inspect/repair/lived-in quality loop | PARTIAL | Owner Appendix E and procedural scene | Original article fetch failed; full loop and photoreal target not completed. |
| M5 | Manim reveal / AI image enhancement | NOT_IMPLEMENTED | No substitution for true geometry | Optional future explanation/appearance tools, carefully labelled. |
| M6 | New responsive studio/real-engine landing | TESTED_SCOPE | studio-browser.json; desktop/mobile captures; Focus mode, the fitted views and the folding brief panel checked in the studio harness | Native direct-navigation, touch and accessibility audit remain open. |
| M6 | Full conditional civil questionnaire | PARTIAL | Eight essential questions, derived open spaces and selected deeper fields | Not the entire supplied questionnaire; no unsupported answers disguised as honoured. |
| M6 | Review fused intent and conflicts | TESTED_SCOPE | Preflight UI and tests | Arbitrary recognition hypotheses not implemented. |
| M6 | Save/reopen project and export bundle | PARTIAL_TESTED | JSON contract, UI collection, explicit exterior/interior theme persistence and actual files | Image bytes, undo and compare are absent; legacy files preserve their current exterior until opted in. |
| M6 | Drag-resize-rotate/snapping designer | NOT_IMPLEMENTED | Grid painter only | Semantic editor, undo and constraint-preserving updates required. |
| M6 | GSAP choreography | AUTHORED_UNVERIFIED | Optional lab only | Default UI uses CSS; no accepted production GSAP integration. |
| M6 | Keyboard/reduced-motion/accessibility | PARTIAL | Focus states, controls, reduced-motion handling | Formal keyboard, touch, screen-reader and contrast audit open. |
| M6 | Three user-consent AI questions | TESTED_SCOPE | Dialog and schema/consent tests | Not every cloud/local provider exercised. |
| M6 | Local Qwen download + llama-server | AUTHORED_UNVERIFIED | Pinned hash downloader dry-run and starter | No weights/runtime/inference test bundled. |
| M6 | Cloud BYOK and validated edit proposals | PARTIAL_TESTED | Mock/schema/security tests and adapter | No paid provider request; no image input; structural/regulatory gates unavailable. |
| M6 | Session keys/clear/estimate/privacy | PARTIAL_TESTED | Security tests | OS-keychain, secure RAM erase, formal audit not implemented. |
| M6 | Every higher AI tier visibly better | NOT_VERIFIED | No invented benchmark | Controlled accepted-plan evaluation required; no blanket guarantee. |
| M7 | Area/room/opening schedules | TESTED_SCOPE | Generated drawing/report data | Gross envelope includes terraces/stair cells, not statutory/carpet area. |
| M7 | Cost in lakhs and timeline | PARTIAL | Editable illustrative scenarios | No location/date rate survey, BOQ or commitment. |
| M7 | Indicative RCC/foundations/steel/material quantities | NOT_IMPLEMENTED | No fabricated values | Professional calculations and measured soil/assemblies required. |
| M7 | Soil/photo/geotech recommendation | NOT_IMPLEMENTED | Soil context and warning only | Never infer bearing capacity or a pile scheme from a photo/name. |
| M7 | Drainage/plinth/RWH design | PARTIAL | Plinth geometry/input; notes | No surveyed falls, stormwater sizing or rainwater engineering. |
| M7 | MEP schematics and loads | PARTIAL | Services intent tables | No routed plumbing/electrical sizing, one-line design or medical services. |
| M7 | Understandable quality scores | PARTIAL | Vastu/opening ratios and warnings | No verified daylight, energy, thermal or universal circulation score. |
| M7 | Preliminary banner throughout | TESTED_SCOPE | PDF page tests and output headers | Cannot replace professional review. |
| M8 | Setup/start scripts and double-click wrappers | PARTIAL_TESTED | Shell syntax + installed-runtime smoke | Fresh network install and native OS execution unverified; terminals visible. |
| M8 | No-terminal native launcher | AUTHORED_UNVERIFIED | desktop.py / PyInstaller spec | Target-platform runtime build and acceptance needed. |
| M8 | macOS .app/.dmg and Windows .exe/.msi | AUTHORED_UNVERIFIED | macOS and Inno Setup recipes | No binaries built, signed or notarised. MSI recipe absent. |
| M8 | Offline release/runtime/assets | PARTIAL_TESTED | Self-contained preview + no-network core | Core dependencies first need installation; model/optional assets separate. |
| M8 | Update/rollback | PARTIAL | Documented side-by-side rollback | No automatic updater/migration service. |
| M8 | Real GPU and clean-machine acceptance | NOT_VERIFIED | Software-renderer evidence only | Actual macOS/Windows GPU and setup/installer tests required. |
| M8 | Adversarial review and tests | TESTED_SCOPE | pytest; repaired defects; reproducibility | Not equivalent to legacy 243 tests, independent engineering review or penetration test. |
| M8 | Final demo film and photoreal reference match | NOT_IMPLEMENTED | Real-time physically based captures and offline Cycles stills only | Film, formal reference comparison and artistic acceptance needed. |
