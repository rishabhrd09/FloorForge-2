# Architecture and contracts

## One authority, explicit export boundaries

`intent.py` preserves sources and compiles supported input into a brief. `layout.py` produces the canonical building: local plan coordinates in millimetres, Z up, stable semantic IDs, polygonal room cells and clear spaces, walls, hosted openings, floors and stair parameters. The road is at local −Y; `road_bearing_deg` is the azimuth from the house outward towards the road. North, solar direction, annotations and entrance geometry use that single convention.

`scene.py` transforms the building into authored shared meshes in **metres / Z-up**. The live renderer and Blender worker consume that scene. GLB converts at its boundary to **metres / Y-up**. IFC remains **millimetres / Z-up** with explicit project units. Plan dimensions remain millimetres. No exporter invents a different layout.

Scene schema `floorforge.scene/0.4` adds four blocks to the nodes, materials, lights and cameras:

- `vegetation`: seeded plant instances with species, position, scale and rotation. The viewer grows them procedurally; `plant-proxy` nodes keep them in the GLB and drawings.
- `lawns`: lawn polygons.
- `rooms`: clear room polygons per storey, used for the walk badge and room light probes.
- `walk`: the arrival spawn, a spawn per floor and the eye height.

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

Default < survey < recognised text < manually structured sketch < grid/plan < explicit edit. Equal-priority conflicting field values block generation. Disabled source records remain archived. A high-priority source can therefore override a changed low-priority survey answer; the preflight shows which source won.

The `text` parser recognises only a small grammar: dimensions with units, BHK/bedroom count, G+n or ground-only, cardinal/diagonal facing, a lakh amount and selected style/kitchen/parking phrases. It preserves the raw text and displays an unenforced-remainder notice. This is not unrestricted natural-language understanding.

A ground-floor grid's labelled cells are unioned as polygons. Room names must form connected regions; holes or inaccessible layouts are rejected. It is not a room-suggestion grid that gets discarded after input. A programmatic source marked `plan` means manually verified structured information; it does not imply an automatic plan-recognition engine exists.

## Layout and checks

The current strategy is a bounded public-hub / services-band / private-room family with mirrored and shorter-footprint variants. The G+1 plan has distinct upper programming, a vertically aligned stair and a real uncovered terrace. It is not arbitrary stochastic optimisation, general constraint solving or a house for every plot.

The deterministic screen checks partition coverage, containment, overlap, supplied-reference size targets, window presence, opening hosting/bounds, portal connectivity, bedroom-through-route avoidance, requested floor/bedroom counts and basic stair proportions/alignment. Those are useful checks, but insufficient to prove buildability. Width screening of nonrectangular rooms currently uses a bounding short side, not a full local-clearance medial-axis calculation. Furniture recipes use a contained rectangle within nonrectangular clear space rather than filling the entire bounding box.

User-reference dimensional targets have **no verified BIS clause ID**. `official_clause` remains null; statutory status remains `NOT EVALUATED`. The structural stage returns `NOT DESIGNED`. The report clones its input review before appending report-only warnings, preserving DAG purity.

## Geometry and surfaces

Walls are polygon extrusions split vertically around hosted doors and windows. Each storey's walls are tiled without overlaps: external walls claim corners and T-junctions, and later walls keep only the unfilled part. No two solids therefore share a face, since coincident faces shade black in path tracers and z-fight in other viewers. Walk colliders keep the full wall polygons. Slabs preserve stair/terrace voids. Decorative objects and furniture are shared geometry with transforms, not painted rectangles. Bed frames, mattresses, shaped bedding, chair frames, cabinets, handles, hollow vessels, fixture bulbs and leaf meshes are procedural.

Not every decorative surface is a closed manifold, and the whole building is not a single boolean-unioned watertight object. The GLB retains individual components and stable scene names.

Walking uses the same geometry. The viewer merges every collidable closed surface (walls, glazing, slabs, stair treads, furniture) into a BVH. A capsule with a 0.27 m radius and 1.78 m height moves against it with gravity, step-up of 0.38 m, snap-down, jump and crouch, so the stair core is climbed continuously. Headroom is checked by ray before standing up. This is walkable geometry, not an accessible-route or egress certification. Doors are fixed open leaves.

The Modern Tropical exterior (`modern_exterior.py`) derives its assemblies from the same facade anchors, plot polygon and protected interior fingerprint as the other families:

- a cantilevered portico or balcony soffit;
- a frameless glass balcony;
- a floating roof slab;
- a clad feature wall;
- a carport and glass-roof pergola when the plot allows;
- a Shapely-built landscape: court, pebble beds, stepping stones, lawns, planting, lanterns and boundary.

Every landscape polygon is kept inside the plot and off the house footprint. Tests check this for all fixture plots.

## Files

| File | Responsibility |
|---|---|
| `floorforge/model.py` | Data classes, defaults, hashes, orientation |
| `intent.py` | Supported field validation, text extraction, provenance |
| `layout.py` | Polygonal layout, walls, openings, stairs |
| `review.py` | Preliminary checks, scenario reports, solar |
| `scene.py` | Shared procedural geometry, scene 0.4 metadata and GLB |
| `scene_kit.py` | Geometry helpers, physically based material library, plant/light registration |
| `exterior.py` | Exterior/interior theme registry, legacy migration, candidate assemblies |
| `modern_exterior.py` | Modern Tropical openings, assemblies and plot-aware landscape |
| `drawings.py` | SVG/ReportLab sheets, DXF floor plans |
| `ifc_export.py` | IFC4 STEP entities, relations and self-integrity |
| `pipeline.py` | DAG, caching, immutable builds, export ZIP |
| `ai.py` | Memory-only optional provider proposals |
| `server.py` | Loopback API, host/origin/token checks, queue |
| `web/app.js` | New studio UI and input/review/save flow |
| `web/viewer.js` | Bundled realistic viewer (built from `web/viewer/src`, committed) |
| `web/viewer/src/` | Viewer sources: materials/texture synthesis, sky/sun/probes, walker, planting, context, HUD, grade, presentation export |
| `web/src/three-studio.js` | Optional unbuilt Three/path-tracing lab |
| `scripts/blender_scene.py` | External unexecuted Blender worker |
| `scripts/regenerate_examples.py` | Rebuilds the three bundled examples from `examples/briefs` |
| `scripts/capture_walkthrough.mjs`, `scripts/capture_studio.mjs` | Browser evidence harnesses (Playwright, software WebGL) |
| `scripts/export_presentation.mjs` | Headless export of the viewer's presentation GLB |
| `scripts/render_cycles.py` | Blender Cycles path-traced stills from that GLB and `scene.json` |

## Engineering technology choices

Shapely, Trimesh, ezdxf and ReportLab solve the implemented stages. CadQuery/build123d, Manifold3D, pvlib, Manim and Mitsuba were not installed simply to satisfy a tool list. BREP/STEP, exact boolean-unioned solids, Manim explanations and validated pvlib comparison remain future work. A custom IFC serializer does not substitute for independent IFC schema/geometry acceptance.

The default viewer bundles Three.js r186, three-mesh-bvh 0.9.5, postprocessing 6.39.5 and n8ao 2.0.1 (MIT, zlib, and ISC/CC0 licences); their notices are in `licenses/viewer-js/` and the bundle's legal comments. The bundle is committed, so the ZIP stays useful offline without Node. It does not prove the separate optional Three/path-tracer/GSAP lab works. GSAP has a custom standard license and requires an explicit optional-build acknowledgement. GEOS transitive license obligations are also recorded rather than hidden behind Shapely's permissive Python license.
