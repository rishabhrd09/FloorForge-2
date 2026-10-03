# Upload a 2D floor plan and generate 3D

Choose **Import 2D floor plan → 3D** in the studio, then **Choose DXF & generate 3D**. A valid file loads as an exact, editable Custom Plan and automatically generates the 3D viewer, walk-through, GLB, IFC, drawings and saved FloorForge project. No second input or AI service is required. Existing projects are saved before a successful import replaces the active draft. Reopen the import dialog to read its assumptions and ignored-entity count.

Before this feature, the studio could reopen structured FloorForge JSON projects and generate from manually authored rooms or guides. Image attachments were reference notes only. That remains true for photos, PNG/JPG, scans, PDFs, DWG and unstructured line drawings: this importer does **not** recognize or trace them.

[Download the example drawing](../examples/import/ground-floor.dxf) or use the download button in the import dialog. It contains a living room, bedroom, kitchen and bathroom. Open it in a DXF-capable CAD editor and use the same layers when preparing another drawing.

## Exact file contract

- ASCII DXF, R2000 or later, UTF-8 (ASCII is also accepted), maximum **750,000 bytes**. Binary DXF is unsupported.
- Set `$INSUNITS`: `4` = millimetres, `6` = metres, `1` = inches, `2` = feet. Unitless drawings are rejected. Draw at actual size; printed scale and dimension annotations are not used.
- **One ground floor per file**, in model space, flat XY geometry at Z=0, normal extrusion. Minimum Y is the front/road, positive Y runs toward the rear, positive X runs to the right. The plot can have a translated origin: import subtracts its minimum X/Y without scaling or rotating the plan.
- One **closed rectangular LWPOLYLINE** on `FF_PLOT`. Plot width: 5–50 m; depth: 6.5–60 m; whole-millimetre plot dimensions.
- Each room is one **closed, four-corner, axis-aligned rectangular LWPOLYLINE**, describing its **clear inside-wall boundary**, on `FF_ROOM_<kind>`. No bulges, polyline widths, diagonals, duplicate closing segments, nested room holes or overlapping rooms. A repeated endpoint equal to the first is allowed.
- Leave **150 mm between neighbouring enclosed room outlines** for their shared wall and at least **150 mm between an enclosed room and the plot edge** for its exterior wall. Rooms must form a connected floor plate; extra garden/site space can remain empty within the plot.
- Draw opening spans as **LINE** entities on `FF_ENTRY`, `FF_DOOR`, or `FF_WINDOW`. A line lies on the wall **centreline**, 75 mm outside a clear room edge. Its endpoints define the exact opening width. Do not draw door leaves, swing arcs or window rectangles on these layers. A shared door is drawn once. Door widths must be at least 750 mm, and spans must stay on one continuous wall segment, away from corners/junctions.
- Include a ground-floor entry to the outside, continuous door access to every occupied room, and exterior windows for habitable rooms/kitchens and ventilation for bathrooms. The existing minimum-room-size and daylight checks apply. No missing doors/windows are invented.
- Maximum 120 rooms, 240 openings and 5,000 model-space entities, within the file-size cap.

Room layers use the catalogue kind in uppercase; hyphens can be written as underscores. Examples: `FF_ROOM_LIVING`, `FF_ROOM_BEDROOM`, `FF_ROOM_KITCHEN`, `FF_ROOM_BATHROOM`, `FF_ROOM_DRAWING_ROOM`, `FF_ROOM_HALL`, `FF_ROOM_STUDY`, `FF_ROOM_DINING`, `FF_ROOM_POOJA`, `FF_ROOM_UTILITY`, `FF_ROOM_STORE`, `FF_ROOM_DRESS`, `FF_ROOM_VERANDA`, `FF_ROOM_COURTYARD`, `FF_ROOM_TERRACE`, `FF_ROOM_BALCONY`, `FF_ROOM_OUTER_LOBBY`, `FF_ROOM_INNER_LOBBY`, `FF_ROOM_FOYER`, `FF_ROOM_FAMILY`, `FF_ROOM_POWDER_ROOM`, `FF_ROOM_CARE_ROOM`, `FF_ROOM_DRYING_YARD`.

Stairs, stair landings, shafts, voids and drying rooms requiring drainage metadata are unsupported in this importer. Create linked upper floors and stairs in the exact editor or use a saved `.floorforge.json` project for those. General orthogonal polygons are supported by the exact editor's project format, but this DXF importer deliberately accepts rectangles only.

Other layers are ignored and their entity count is disclosed. Put annotations and furniture there. Unknown `FF_` layers, unsupported entities on import layers, and import geometry in paper space are rejected. Explode blocks before importing. Text labels do not assign room types; the layer does. Rooms receive editable catalogue names and stable IDs based on DXF handles.

## Heights and other assumptions

A 2D drawing does not specify vertical construction. The generated model uses **150 mm walls, 3150 mm floor-to-floor height, 450 mm plinth, 2100 mm door height, and windows with 900 mm sill and 1200 mm height**. Review/edit these in the studio and exact editor. Furniture and finishes use the existing procedural renderer; they are not imported from CAD symbols.

Plot setbacks are explicitly zero in the imported brief: actual clear space drawn inside the plot is retained, but local setback compliance is not inferred. The import does not assert structural adequacy or construction approval. Its output is the same preliminary model and review pipeline as other FloorForge projects.

Malformed/ambiguous drawings preserve the current project and show an error, including the entity handle and layer where available. Parsed drawings with access/daylight/opening validation failures load as editable drafts but do not generate 3D until repaired. The previous generated design remains marked stale.

## Command line and API

```sh
python -m floorforge generate --plan2d examples/import/ground-floor.dxf --out /tmp/floorforge-import
```

`--plan2d` and `--project` are mutually exclusive. The CLI prints import assumptions, validates the drawing, then runs the existing export pipeline; invalid plans exit without generating a substitute layout.

`POST /api/plan/import-dxf` accepts `{ "filename": "home.dxf", "text": "...DXF contents..." }` through the existing local session-token protection. It returns `project`, `valid`, counts, notes and either a review or a validation issue. The studio then submits the returned project to `/api/generate`. The upload is processed locally and is never sent to an AI provider. `GET /api/plan/import-template` serves the example.

Regression coverage: `tests/test_plan_import.py` checks exact dimensions, unit/origin conversion, malformed input, unsupported geometry, access failures, session protection and matching 3D/export plan hashes. `scripts/check_plan_import.mjs` exercises file upload and generation in the browser.
