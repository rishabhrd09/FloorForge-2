# Architecture and contracts

## One authority, explicit export boundaries

`intent.py` preserves sources and compiles supported input into a brief. `layout.py` produces the canonical building: local plan coordinates in millimetres, Z up, stable semantic IDs, polygonal room cells and clear spaces, walls, hosted openings, floors and stair parameters. The road is at local −Y; `road_bearing_deg` is the azimuth from the house outward towards the road. North, solar direction, annotations and entrance geometry use that single convention.

`scene.py` transforms the building into authored shared meshes in **metres / Z-up**. The live renderer and Blender worker consume that scene. GLB converts at its boundary to **metres / Y-up**. IFC remains **millimetres / Z-up** with explicit project units. Plan dimensions remain millimetres. No exporter invents a different layout.

Scene schema `floorforge.scene/0.4` adds four blocks to the nodes, materials, lights and cameras:

- `vegetation`: seeded plant instances with species, position, scale and rotation. The viewer grows them procedurally; `plant-proxy` nodes keep them in the GLB and drawings.
- `lawns`: lawn polygons.
- `rooms`: clear room polygons per storey, used for the walk badge and room light probes.
- `walk`: the arrival spawn (on the footpath outside the open gate, facing the house), a spawn per floor and the eye height.

Materials may declare a physically based `kind` (render, stone, cobble, pebbles, woodfloor and so on) that the viewer turns into GPU-synthesised texture maps.

## DAG

```
intent → programme → layout → openings
                       ├── structure (explicitly not designed)
                       └── validate
                            ├── documents
                            └── scene → sheets
                                      └── render (raster-ready; offline render pending)
                                                   └── exports
```

The exact dependency map is `pipeline.DEPS`; the schematic above is abbreviated. Run a target with `--target intent`, `layout`, `validate`, `scene`, `sheets` or another registered stage. Dependencies execute in order. A stage's key includes inputs, dependency hashes, the implementation-source fingerprint and installed runtime versions. Stage JSON is written atomically; caches are checked before use. Published outputs carry hashes and are immutable. The generation queue has one worker to bound concurrent expensive work.

This is a modular functional core, not a claim that all functions have passed a strict type checker. Dataclass contracts are typed; several JSON-facing functions still require annotation/schema tightening. `programme` and `openings` currently wrap parts of the layout generator. `structure` and `render` expose honest statuses, not fake engineering/rendering computation.

## Input precedence and source truth

Default < derived < survey < recognised text < manually structured sketch < grid/plan < explicit edit. Equal-priority conflicting field values block generation. Disabled source records remain archived. A high-priority source can therefore override a changed low-priority survey answer; the preflight shows which source won.

The `derived-setbacks` source (`intent.derive_setbacks`) sets the four open spaces from the plot unless an input states them: front and rear by plot depth, each side by plot width, as Indian byelaws usually tabulate them (`SETBACKS_BY_DEPTH`, `SETBACKS_BY_WIDTH`), and a 5.5 m front for a parking court where the plot is deep enough. The studio omits the setback fields while “Open spaces from the plot size” is on, and shows the same tables live (they travel in the session payload). They are design assumptions to verify with the authority, not a rule pack.

The `text` parser is a deterministic grammar of the phrases homeowners write, not general language understanding: plot size (`30x40`, `30 by 40`, `30' x 40'`, `9m x 12m`, `30*50`, width/depth statements; a size right after a room name is a room, not the plot; unitless sizes are read as feet from 20 up and said so), plot area (sq ft, sq yd/gaj, sq m, cents, guntha, marla; common areas snap to the standard Indian plot, others to a 2:3 plot, built-up and carpet areas are ignored), BHK/bedrooms, attached baths (all, a count, the master only, none, or inferred from a bath total), storeys (G+n capped at G+1 with a notice, duplex, two-storey, ground only), facing (`east facing`, `NE-facing`, `facing north`, `road on the west`), budget (lakh, crore, rupees after “budget”), pooja, parking, kitchen, eldercare, Vastu (off, flexible, strict, else preferred), setbacks, floor-to-floor or ceiling height, plinth and style words. It returns `reading`: the phrases understood with the fields they set, the phrases not understood (kept as notes, not applied), and the assumptions made; `fuse` exposes it as `text_reading` and adds the assumptions to the notices.

A ground-floor grid's labelled cells are unioned as polygons. Room names must form connected regions; holes or inaccessible layouts are rejected. It is not a room-suggestion grid that gets discarded after input. A programmatic source marked `plan` means manually verified structured information; it does not imply an automatic plan-recognition engine exists.

## Layout and checks

`planner.py` searches a family of partis rather than filling one template: a public spine (living, dining, hall) with two stacks of units beside it — bedroom suites (attached bath at an outside corner, a dressing room for the master), the common bath, study, kitchen with utility, pooja and store — in a three-row ground floor (living | kitchen, dining, services | suites) or a compact one (living and dining | kitchen and suites), and on the upper floor a family lounge with the open terrace. Coordinate descent over hall position and width, stack orders, row depths and envelope width/depth, with several seeds, finds the lowest cost. The cost encodes NBC 2016 Part 3 style minimums as hard limits and comfortable targets that grow with the plot as soft ones, maximum sizes and aspect ratios, L-shape penalties, a window on an outside wall for lit rooms and air for baths, wet-room clustering, the pooja off bath walls, a bath on every bedroom floor, dead-end and long halls, filler rooms, stacking between floors (baths over baths or the utility, never over the kitchen or pooja) and the Vastu hand. When a requested pooja finds no slot, a small pooja room is carved from a rear corner of the living room, clear of the hall's mouth. Results are cached per brief. The `planning` record in the building names the parti, envelope, score, mirror and attached baths requested/provided. It is still a bounded search, not general constraint solving or a house for every plot.

The deterministic screen checks partition coverage, containment, overlap, NBC-style room minimums, corridor width and circulation share, window presence, opening hosting/bounds, portal connectivity, bedroom-through-route avoidance (a bedroom's own bath and dressing room may lie beyond it), requested floor/bedroom counts and basic stair proportions/alignment. `professional_screen` adds recorded warnings a reviewing architect would raise: openings under a tenth of a habitable room's floor, a bath without a 0.3 m² opening to open air, a pooja beside a bath or under an upper bath, a bath over the kitchen, two door leaves sweeping the same floor, and fewer attached baths than requested. Those are useful checks, but insufficient to prove buildability. Width screening of nonrectangular rooms currently uses a bounding short side, not a full local-clearance medial-axis calculation. Furniture recipes use a contained rectangle within nonrectangular clear space rather than filling the entire bounding box.

User-reference dimensional targets have **no verified BIS clause ID**. `official_clause` remains null; statutory status remains `NOT EVALUATED`. The structural stage returns `NOT DESIGNED`. The report clones its input review before appending report-only warnings, preserving DAG purity.

## Geometry and surfaces

Walls are polygon extrusions split vertically around hosted doors and windows. Each storey's walls are tiled without overlaps: external walls claim corners and T-junctions, and later walls keep only the unfilled part. No two solids therefore share a face, since coincident faces shade black in path tracers and z-fight in other viewers. Walk colliders keep the full wall polygons. Slabs preserve stair/terrace voids. Decorative objects and furniture are shared geometry with transforms, not painted rectangles. Bed frames, mattresses, shaped bedding, chair frames, cabinets, handles, hollow vessels, fixture bulbs and leaf meshes are procedural.

Not every decorative surface is a closed manifold, and the whole building is not a single boolean-unioned watertight object. The GLB retains individual components and stable scene names.

Walking uses the same geometry. The viewer merges every collidable closed surface (walls, glazing, slabs, stair treads, furniture) into a BVH. A capsule with a 0.27 m radius and 1.78 m height moves against it with gravity, a 0.38 m step offset (about 0.3 m in practice for a single rise), snap-down, jump and crouch, so the stair core is climbed continuously. Headroom is checked by ray before standing up. This is walkable geometry, not an accessible-route or egress certification. Doors are fixed open leaves.

The Modern Tropical exterior (`modern_exterior.py`) derives its assemblies from the same facade anchors, plot polygon and protected interior fingerprint as the other families:

- a cantilevered portico or balcony soffit over an L-shaped entrance: the flight covers the door end of the landing and returns down its side (`flight_side`, `return_steps_mm`), a sit-out with a bench, planter and stone-clad column fills the other end (`sitout_x_mm`), and the entry opening is refined into a tall pivot door (`entrance_pivot`);
- a frameless glass balcony with a timber deck, handrail cap and louvred pergola;
- slim aluminium windows, with timber-lined pods on facade bedrooms and etched glass in wet rooms;
- a floating roof slab with a deep street-side eave, a timber-slat soffit and downlights;
- a stone-clad stair tower over the top-floor stair (`stair_tower`, shared with the other designed themes), beside an open roof terrace, and a solar rack; a timber-slat sala on a floating deck (`roof-sala`) where the terrace has room for it beside the loungers;
- a clad feature wall;
- a carport and glass-roof pergola when the plot allows;
- a Shapely-built landscape: driveway, entrance path, pebble beds, stepping stones, lawns, planting, lanterns and boundary; side passages with pale pavers staggered over black pebbles, timber-clad boundary walls with a breeze-block screen (`breeze_screen`), pots and a wash basin (`garden_basin`); a stone water wall with a lit trough on the rear boundary (`water_wall`) with the hedge parting around it;
- a stone-clad street face on the front boundary with up-lights, and a vertical timber-slat vehicle gate; inside, a slatted timber foyer ceiling behind the main door.

The street frontage for every designed theme comes from `frontage.py`: `boundary.gates` lists a swing pedestrian gate on the door's axis and, where a 2.4 m stretch of front yard is clear of the entrance (or a carport is built), a sliding vehicle gate with the side its leaf parks on; `letterbox_pier` places the stone pier beside the pedestrian gate. `gate_center_mm` and `gate_width_mm` keep naming the arrival gateway (the pedestrian gate) for older consumers.

Every landscape polygon is kept inside the plot and off the house footprint. Tests check this for all fixture plots.

## Files

| File | Responsibility |
|---|---|
| `floorforge/model.py` | Data classes, defaults, hashes, orientation |
| `intent.py` | Supported field validation, text reading with understood/not-understood feedback, derived setbacks, provenance |
| `planner.py` | Parti search and rule-scored room planning (NBC-style minimums, light and air, wet stacks, Vastu hand) |
| `layout.py` | Polygons, walls, planned doors and stock-size windows, stairs |
| `review.py` | Preliminary checks, professional warnings, scenario reports, Vastu readings, solar |
| `scene.py` | Shared procedural geometry, scene 0.4 metadata and GLB |
| `scene_kit.py` | Geometry helpers, physically based material library, plant/light registration |
| `exterior.py` | Exterior/interior theme registry, legacy migration, candidate assemblies |
| `modern_exterior.py` | Modern Tropical openings, assemblies and plot-aware landscape |
| `frontage.py` | Street frontage for every designed theme: pedestrian and vehicle gates, letterbox pier |
| `drawings.py` | SVG/ReportLab sheets (dimension chains, tags, grid, levels, section marker, schedules), DXF floor plans with DIMENSION entities |
| `ifc_export.py` | IFC4 STEP entities, relations and self-integrity |
| `pipeline.py` | DAG, caching, immutable builds, export ZIP |
| `ai.py` | Memory-only optional provider proposals |
| `server.py` | Loopback API, host/origin/token checks, queue |
| `web/app.js` | New studio UI and input/review/save flow |
| `web/viewer.js` | Bundled realistic viewer (built from `web/viewer/src`, committed) |
| `web/viewer/src/` | Viewer sources: materials/texture synthesis, sky/sun/probes, walker, planting, context, HUD, grade, presentation export; `framing.js` is the exact camera fit behind every view and Focus |
| `web/src/three-studio.js` | Optional unbuilt Three/path-tracing lab |
| `scripts/blender_scene.py` | External unexecuted Blender worker |
| `scripts/regenerate_examples.py` | Rebuilds the three bundled examples from `examples/briefs` |
| `scripts/capture_walkthrough.mjs`, `scripts/capture_studio.mjs` | Browser evidence harnesses (Playwright, software WebGL) |
| `scripts/export_presentation.mjs` | Headless export of the viewer's presentation GLB |
| `scripts/render_cycles.py` | Blender Cycles path-traced stills from that GLB and `scene.json` |

## Engineering technology choices

Shapely, Trimesh, ezdxf and ReportLab solve the implemented stages. CadQuery/build123d, Manifold3D, pvlib, Manim and Mitsuba were not installed simply to satisfy a tool list. BREP/STEP, exact boolean-unioned solids, Manim explanations and validated pvlib comparison remain future work. A custom IFC serializer does not substitute for independent IFC schema/geometry acceptance.

The default viewer bundles Three.js r186, three-mesh-bvh 0.9.5, postprocessing 6.39.5 and n8ao 2.0.1 (MIT, zlib, and ISC/CC0 licences); their notices are in `licenses/viewer-js/` and the bundle's legal comments. The bundle is committed, so the ZIP stays useful offline without Node. It does not prove the separate optional Three/path-tracer/GSAP lab works. GSAP has a custom standard license and requires an explicit optional-build acknowledgement. GEOS transitive license obligations are also recorded rather than hidden behind Shapely's permissive Python license.
