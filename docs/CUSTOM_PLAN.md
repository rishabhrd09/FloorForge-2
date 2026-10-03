# Per-floor guides and exact plans

The studio now offers **Automatic**, **Quick Guide**, and **Custom Plan**. Existing automatic presets keep their original scene geometry, materials, lighting, furniture recipes, planting and cameras. The recorded hashes and reference-image inventory are in `evidence/custom-plan/aesthetic-baseline.json`. The comparison is of generated scene data; it is not a new real-GPU pixel certification.

## Import a 2D drawing

Use **Import 2D floor plan → 3D** to upload a layered ASCII DXF ground-floor plan and generate it directly. The first version accepts rectangular clear-room outlines and explicit door/window spans. See [the exact file contract and example](IMPORT_2D_PLAN.md). Images and PDFs remain manual references.

## Quick Guide

Ground, First and Second each have exactly four rows of four cells. Row zero is the road/front. Labels and colours come from `floorforge/spaces.py`, also returned by `/api/session`. New guides store stable `floorIds` next to `floors`. Repeated service labels on different floors remain separate requests. Numbered bedrooms have one floor assignment. The bounded planner can rearrange bedroom assignments; requests outside its available arrangements produce floor- and cell-specific conflicts instead of an unrelated plan.

The automatic G+2 arrangement uses a covered first-floor veranda and an open second-floor terrace. Use Custom Plan to retreat the second floor above a first-floor open terrace. The guide palette does not mean every combination can fit the bounded automatic planner.

Legacy single-board guides retain their whole-home interpretation until edited. Legacy metric grids continue through their original exact-grid path; opening or saving one does not silently replace its dimensions with hints. Painting in the guide explicitly switches that input to the new relative-placement format.

## Custom Plan editor

Open the dimensioned editor to draw rectangular rooms, move rooms, drag their boundary handles, and enter clear width/depth to 1 mm. Entering an area changes a rectangular room's depth. Orthogonal polygons can also be supplied in the versioned project format. Draw or move additional orthogonal walls and edit their endpoint coordinates. Add or edit doors, windows, cased openings and glazed doors by host room, wall side, exact offset, width, sill and height.

The editor includes floor tabs, a floor-below overlay, snapping, multi-selection with Shift, align/distribute, undo/redo, zoom, object selection, and local autosave. **Save project** produces a portable JSON file. Inactive guide boards and the custom draft are retained in `editorState`. Removing the top floor is an explicit, undoable action. Choosing a lower occupied-floor count removes the higher floor in one undoable editor operation; later edits do not restore it automatically.

**Load example for these floors** loads the selected one, two or three occupied floors from `examples/custom/g2-terrace.floorforge.json`, including a linked stair to the roof. It defaults to G+1 and never adds an occupied Second floor to provide roof access. The example is a geometry test fixture, not a complete residential programme or construction plan.

### Geometry contract

`floorforge.custom-plan/1` uses millimetres. Every floor, room, authored wall, opening and stair link has a stable ID. Floors are ordered from ground up. Room polygons describe **clear space**, with unclosed orthogonal rings. Walls occupy the allowance outside that space; the initial allowance is 150 mm. Enclosed neighbours need that gap between clear boundaries. Leave the same allowance to the buildable boundary. Editing exact geometry never invokes the automatic planner or resizes a room to fit.

The compiler nodes shared wall axes and derives canonical walls, hosted apertures, floor plates (including holes), per-floor roofs, ceilings and guards. Custom exterior refinement preserves authored openings as well as rooms and stairs. Themes still supply palettes, surface recipes, window treatment, furniture and landscaping; generated facade additions that presume the automatic floor topology are excluded.

Stairs are linked U cores along the local rear direction. Flight width, tread and landing are explicit in the schema. Riser count follows floor height and the existing geometric screen. Every linked floor must have the same clear stair polygon. Doors enter the front landing. Upper slabs and the ceilings underneath have the same stair openings. The editor's link command creates aligned counterparts; their horizontal access still needs authored doors/landings.

Outdoor semantics are distinct:

- Terraces, balconies, drying yards and courtyards remain open to the sky; an upper floor over them is rejected.
- Verandas and outer lobbies receive covers.
- Drying rooms receive wet finishes, service furnishing, drainage intent and external ventilation checks.
- Double-height voids remove a floor and the ceiling underneath, while retaining the roof at the upper level.
- Lift/shaft zones remove slabs and must align. A working elevator, machinery and lift access design are not supplied.
- Guards follow exposed upper outdoor and void edges; they appear in the scene, drawings and IFC.

Slabs, roofs and stairs use one shared geometry contract for scene/GLB, IFC and drawings. Area calculations sum actual floor plates rather than multiplying one footprint by the storey count.

## Revision identity

Committed edits increment `draftRevision` and immediately mark the previous 3D, drawings and files stale. `planHash` hashes the normalized geometry inputs and resolved brief; revision numbers and editor-only state are excluded, so save/reopen retains the hash. Building, scene, review/report, sheets, PDF metadata, DXF metadata, GLB metadata, IFC properties and manifest carry that hash.

The browser captures the submitted revision and expected hash. A completed job is shown only if both still match the active draft and the returned artifacts agree. Failed generation displays **Previous generated design—not the current draft**. An older in-flight job cannot overwrite newer edits. Export controls for the current draft stay disabled while stale. Selecting a generated room in 2D highlights its stable ID in 3D.

After successful generation the studio lists room additions, removals, area changes and moves, and notes when the exterior theme and palette were preserved.

## Validation and limits

`POST /api/plan/validate` provides object IDs, floor indices and explanations for conflicts. It checks polygon validity, overlap, wall allowance, setbacks, opening bounds/overlap, access, room minimums, daylight/ventilation screens, drying drainage, linked stairs, slab openings, open-sky clearance and support-envelope containment. Invalid geometry can still be saved and reopened for repair.

This release supports orthogonal polygons, rectangular drawing tools, a uniform wall allowance and linked U stairs across up to three floors. It does not support curved/diagonal walls, arbitrary stair geometries, disconnected floor plates, structural cantilever design, functioning elevators, certified accessibility or local regulatory approval. Support checks establish envelope containment; they do not calculate load paths. These limits are explicit conflicts or documented scope, never silent optimization. It should be described as an exact orthogonal editor, not unrestricted architectural CAD.

## Verification

- `tests/test_custom_plan.py`: bypass of the automatic planner, exact 4 × 4 m geometry, G+2 stairs and openings, terrace/veranda/void semantics, rejected conflicts, exact opening edits, kitchen movement, save/reopen hashes, export identity and legacy aesthetic geometry hashes.
- `scripts/check_custom_editor.mjs`: real loopback API and Chromium tests for editing, undo/redo, three fixed boards, validation, generation, matching room selection, superseded jobs, failed generation, autosave and mobile layout. Captures are in `evidence/custom-plan/`.
- Existing intent, geometry, exterior, export, rendering and API-security regression tests remain applicable.

## Easier room placement and repairing a draft

The room palette supports click-then-place and native drag-and-drop. Cards start at usable clear dimensions; set the new-room width and depth before placing. Choose other catalogue types from **Space → Place selected room**. Smart snap aligns neighbouring edges while reserving the shared wall allowance. Pointer placement, movement and resizing stop at the buildable boundary including the outer wall. Typing dimensions remains authoritative: an invalid typed position is shown immediately instead of quietly changing its dimensions.

Boundary and rectangular overlap/clearance feedback appears directly in the editor. **Validate plan** checks the canonical geometry and reports named rooms, floors and measured conflicts. **Move inside** translates a boundary-crossing room without resizing it and can be undone. It does not resolve overlap with another room. A failed generation has a persistent **Review plan issues** action next to the stale-design warning.

**Drawing room · guests** is an enclosed guest sitting room, with sofa furnishing and habitable-room daylight checks. **Living** may be used as a combined family/guest lounge. **Drying room** remains a separate wet service space with drainage and ventilation requirements; existing drying-room drafts are never renamed into drawing rooms.

The guide checks room capabilities and bedroom floor allocation before expensive generation. It identifies the affected floor or painted cells, rather than blaming every brush. A positive programme check does not guarantee the requested positions will fit the automatic arrangements.

**Turn cells into rooms** is an explicit conversion to Custom Plan. It uses the cell boundaries as starting dimensions, preserves connected shapes (including L-shaped lobbies), reserves wall space and retains the original guide boards. It is undoable. Rooms can still need enlargement, access openings or stair work; a stair landing does not create stairs. Empty floors and incompatible upper-floor shapes remain visible for correction.

**Suggest doors & windows** examines actual compiled wall segments and adds editable openings in one undo step. It preserves room geometry and existing openings, avoids overlapping openings, and validates the result for review. It cannot repair disconnected geometry, add missing stair cores, or guarantee a usable opening where no suitable external or shared wall exists. Generation never applies this aid implicitly.

Browser evidence for this workflow is captured by `scripts/check_room_workflow.mjs` in `evidence/room-workflow/`. Backend regressions are in `tests/test_plan_usability.py`.

## Roof terrace access and movable stairs

Enable **Stairs to roof terrace** in Custom Plan, or **Structure & levels → Continue linked stairs to a roof terrace**. Regenerate after enabling it. The final linked flight continues through a matching roof slab/ceiling opening into a hollow stair headhouse with an operable door. The surrounding roof is a walkable, guarded terrace. A G+1 project still has two occupied floors; its roof is a separate access level. G+2 works in the same way. A ground-only Custom Plan can link one stair core to its roof; an automatic ground-only plan has no core and reports that conflict rather than inventing a fixed stair.

The new studio's G+1 preset enables roof access. Old saved projects default to their previous roof behaviour until explicitly enabled, so reopening cannot silently change their appearance. The option participates in `planHash`, save/reopen, validation and the input review. Drawings include A-104, the roof terrace/access plan; scene, GLB, IFC and DXF share the same openings and core location. Roof terrace area is reported separately from occupied gross floor area.

In Walk mode, climb the real flights to reach the roof and press **F** or tap the nearby-door action. The closed door blocks passage; the opened leaf also has a physical swing, so close it if it obstructs your route around a narrow approach. Floor selection is for cutaway viewing; it does not teleport a walking visitor. Entering Walk from a roof cutaway starts at the ground arrival. Descent uses the same stairs.

Custom stairs are positioned by their authored coordinates, including positions away from the front corners. **Move linked stairs on every floor** is enabled by default: moving/resizing one linked room updates all its counterparts in one undo/redo step. Validation still blocks overlaps, misalignment and inaccessible landings. The roof door selects a free front/left/right approach next to the actual landing; invalid roof containment or approach is a named conflict. Stair rotation and alternative stair shapes remain outside this U-core editor's scope.

Quick Guide's automatic solver still offers front-left/front-right stair arrangements. A rear stair hint now produces `GUIDE_STAIR_POSITION` tied to its floor and cells. **Turn cells into rooms** preserves the painted position in Custom Plan for exact editing; generation does not silently relocate it.

Available automatic variations are Public hub, Mirrored hub and Shorter footprint. Exterior themes are Current, Modern Tropical, Warm Modern Minimal, Tropical Verandah and Earth & Terracotta; interior themes are Current, Bright Natural, Warm Contemporary, Quiet Minimal and Earthy Modern Indian. Room and opening placement is editable in Custom Plan. Furniture starts with automatic furnishing and circulation clearances. **Edit placements** adds drag, rotate and exact offsets for supported complete furniture assemblies, with Undo/Redo and explicit validation; see the placement workflow below.

Verification: `tests/test_roof_access.py` covers one/two/three occupied floors, exact relocated cores, shared slab cuts, roof door/guards, old-project behaviour, hash identity, export integration and explicit guide conflicts. `scripts/check_roof_access.mjs` checks the built browser viewer's climb, door interaction, terrace movement, descent, prevention of floor teleporting, linked-core undo/redo and generation. Evidence is written to `evidence/roof-access/`.

## Wall junctions and reviewing guide conflicts

Solid walls are split where their adjoining outdoor space changes. A long bedroom wall beside a veranda and a courtyard therefore has two opening hosts, each connected to the correct neighbour. Outdoor boundaries do not become extra solid walls. Corner-only contact does not create a door route, and an opening spanning two different neighbours is rejected with its opening ID. Clear room polygons and dimensions are retained.

The fixed 16-cell guide now places the board beside its complete issue list, with issue counts on floor tabs and a persistent action bar. Opening a saved guide while Custom Plan is active keeps that mode and its authored geometry; **Return to Custom Plan** returns to the existing draft, while conversion explicitly replaces it in an undoable step. Empty custom floors are reported together. For a roof above the last occupied floor, use **Stairs to roof terrace** instead of adding an empty occupied floor.

Custom Plan's sidebar bedroom count is derived from its room polygons, including zero-bedroom programmes. Plot inputs accept exact converted feet/metre values, avoiding browser step errors when reopening a metric project. Input coverage remains available in its expandable summary so the design and blocking plan issues remain visible.

The reported 8.692 × 11.588 m guide is reconstructed in `evidence/wall-junctions/reported-guide.floorforge.json`. It is a diagnostic reproduction, not a repaired or completed house: the upper guides are blank, several Ground bedrooms are narrow, and doors, windows and an actual linked stair still need authoring. `tests/test_wall_junctions.py` checks that this Ground geometry compiles without the former false three-space wall error. It also checks off-centre outdoor junctions, window/door connections, corner contact, unchanged room polygons and downstream export identity. `scripts/check_wall_junctions.mjs` exercises the real UI and API, with captures in the same evidence directory.


## Occupied floors and placement editing

The default is G+1: Ground and First are occupied floors, with a separate accessible roof terrace above First. Choosing G+2 explicitly creates Second, and the last stair flight then continues from Second to the roof. The floor selector and example loader share this count. Lowering it is undoable in Custom Plan. Legacy saved projects retain their explicit storey count and roof-access setting.

After generating the current draft, choose **Edit placements** beside the viewer modes. The editor uses the generated building's IDs and has two tools:

- **Furniture:** drag a coloured assembly, rotate it, or type offsets from its original position. Sofa cushions, table details, dining chairs and bedside items move with their corresponding assembly. Supported items include sofas, coffee tables, dining sets, beds, wardrobes, desks, bookcases, freestanding shelves, mandirs, laundry sets, islands, lounge chairs and terrace lounge sets when present. Wall finishes, fixed kitchen/plumbing fittings, ceiling fixtures, landscape and roof installations are not independent furniture handles.
- **Rooms:** in automatic designs, drop one room on another to swap their destination slots; each uses the destination shape and size. Shift-click selection and **Swap 2 rooms** are equivalent. This is a change to canonical polygons, followed by walls, openings and all downstream geometry. Custom Plan opens the exact editor instead, where free movement, dimensions, linked-stair movement and the new two-room swap control are available. A packed automatic floor cannot be freely translated into gaps without authoring a new plan.

Use **Check placements**, then **Apply & update 3D**. Edits are staged inside the modal until Apply; closing without Apply discards that staging. Applied overrides autosave and travel in the project file. Invalid moves retain their staged geometry and explain containment, overlap, door approach, door swing or stair conflicts. A different underlying room layout or theme invalidates old furniture anchors instead of applying them to unrelated objects. **Reset placements** removes these overrides explicitly; a reset can be undone. Room changes require resetting existing furniture placements first.

`roomEdits` carries original room anchors and destination polygons in mm. `furnitureLayout` carries semantic ID, anchor hash, metre offsets and yaw in degrees. Empty overrides preserve legacy plan hashes. Furnishing metadata adds no render nodes; moves transform existing nodes, attached lights, drawing footprints and collision footprints. GLB and IFC furniture meshes use those same transforms. IFC remains independently unverified. No-edit visual hashes match the original baselines; intentional room geometry changes can change massing and furnishing arrangements while retaining the selected design language. Furniture-only moves leave unrelated render nodes and aesthetic settings unchanged.

Verification: `tests/test_placement_edits.py`, `scripts/check_placement_editor.mjs`, and `evidence/placement-editor/` cover the default floor count, undoable floor removal, real pointer drags, room swaps, invalid moves, hash round trips and exact preservation of unrelated scene data.


## Drawing rooms in Quick Guide

The visible **Drawing room — Guest seating** card can be selected or dragged onto a guide cell. It creates a distinct enclosed guest sitting room, with sofa seating, a coffee table, access and daylight openings. It is also available in the automatic planner, on the floor where it is painted. **Living** represents a combined family/guest lounge. **Drying room** remains a separate laundry/service type in Custom Plan. Neither guest seating nor a study is substituted for a requested drying room.

The guide dialog exposes **Occupied floors** and **Stair access to roof terrace** separately. For an empty Second guide, **Use G+1 + roof terrace** changes the occupied count to two and enables roof access; original guide boards remain saved, with Undo available. Generation always submits the current active floor boards after a count change; an older saved G+2 grid cannot override that change. Custom Plan floor removal retains its editor's own Undo. Existing saved G+2 projects are never silently reduced.

Quick Guide remains a bounded automatic planner. Guest-room placement is audited and returns a named conflict if the requested zone cannot be honoured. Its front-corner stair restriction is identified as a planner limitation, not proof that a user's location is geometrically invalid. The issue offers a direct conversion into Custom Plan, selecting the stair at its painted position; the user must still author valid dimensions, corresponding cores and landings.

`scripts/check_drawing_room_guide.mjs` exercises the real palette drag/drop, occupied-floor repair and undo, save/reopen, Custom Plan hand-off, full guest-room generation and shared scene identity. Captures are in `evidence/drawing-room-guide/`.


## Room-first preparation (2026-09-30)

The room planner opens in **Arrange rooms**, with placement, size inputs, floor selection, Undo/Redo and **Fit & preview 3D**. The Smart fit proposal flow described below supersedes the original one-step preparation UI. **Fine-tune** reveals authored wall tools, coordinates, alignment, wall thickness and individual opening measurements. Exact-mode generation still bypasses preparation. The main studio Generate button uses the same preparation flow for a custom draft in Arrange mode.

`/api/plan/prepare` returns an explicit undoable proposal. A deterministic constrained translation pass reserves wall space between nearby rectangular rooms; it changes positions by at most 250 mm per axis and never changes room dimensions, removes rooms, adds floors or moves stair cores. Existing partitions and nonrectangular floors opt out of this pass. Existing shared walls remain joined. Aligned unlinked stair rooms are linked, then opening suggestions and full custom-plan validation run. Original authored openings are preserved. Unsupported or larger conflicts stay blocked, with one plain-language issue at a time and an option to inspect the rest. No invalid scene is published.

Simple placement can choose a free spot within 1.2 m of a rough drop when the exact spot collides; only the new room is adjusted, dimensions are retained, and feedback explains the change. Fine-tune keeps the stricter drop behavior. Edge resizing now snaps to nearby wall clearances. Typing dimensions keeps the authored values. Copying an empty floor is explicit and undoable, with fresh room/opening IDs and no duplicated upper-floor main entry. Geometric support, stair access and open-sky checks still apply.

Preparation rejects stale responses when either the plan or surrounding brief changes. Assistance does not certify layouts or invent missing physical provision such as drainage. The rendering pipeline is unchanged. Tests: `tests/test_plan_assist.py`, `scripts/check_room_first.mjs`; evidence: `evidence/room-first/`.


## Smart fit for rough sketches

Arrange rooms accepts rough placements, including overlaps. **Smart fit rooms** and **Fit & preview 3D** request `/api/plan/smart-fit`; dashed outlines and a size-change list show the proposal. **Yes, use this fit** is required before any geometry changes. **No** preserves the sketch, and one Undo restores an accepted fit. Manual walls and exact generation remain available through Fine-tune.

The fitter first tries size-preserving preparation. If that cannot validate the sketch, a constrained rectangular fit can resize and shift rooms, keep their separation directions and floor assignments, reserve walls, meet room-size screening, enlarge stairs to the required flight/landing dimensions, and move linked cores together. Room centres stay within one quarter of the buildable width/depth of their rough locations. Nearby facing edges are joined for doors. Existing partitions fix their floor geometry; nonrectangular shapes are kept exact. The complete compiler and access/daylight validation still decide whether the proposal can generate. Missing floors, unresolvable space shortages and unsupported topology are explained, never silently replaced with a template.

Previously suggested openings may be regenerated for changed walls. Explicitly authored openings stay; editing a suggested opening in Fine-tune makes it an authored opening. No render recipe, material, lighting or camera logic is changed. A rejected local-session token is refreshed and the rejected request retried once, without resetting draft inputs or relaxing origin/token checks.

Courtyard rooms may set `glassCover: true` for a clear canopy with high-level vent gaps, stone paving, planted edges and a drain. The compiler continues to reject opaque upper slabs over that courtyard. This is a visual concept; glazing support, fall and drainage need detailing. `facadeStyle: "warm-layered"` adds finish-only stone accents and balcony slab/soffit details. Both options survive editable project export.

Care-room `reclinerPosition: [x, y]` optionally places the recliner in millimetres; its footprint must remain inside the room. `tvOffset` shifts the TV along the facing wall relative to the recliner, in millimetres. Veranda `finishStyle: "garden-lawn"` provides a planted lawn with a clear rear circulation path; `clearAccess: true` avoids automatic terrace furniture.

Outdoor lightwells and their covered veranda edges can set `serviceOnly: true`. These retain their floor, drainage and daylight geometry but are excluded from occupied circulation; doors into them are rejected. The flag is not allowed on occupied room types.

Care rooms may specify `careLayout: "equipment-left"` to put the cupboard in the rear/head-wall corner, reserve the occupant’s left for equipment, and place three visitor chairs on the right. Furniture still passes footprint, door-approach and swing checks.

Linked U-stair cores accept optional `rotation: 90` (default `0`), rotating the first flight toward decreasing plan x. Flight dimensions stay local to the core. Slab wells, roof access, rails, scene meshes, plan drawings and IFC treads use the same transform. Aligned room footprints must contain the rotated core. Under-stair WCs currently require rotation 0.

A `pooja` space may specify `altarWall` (`front`, `right`, `rear`, or `left`) to orient its mandir explicitly. A cased connection with `openSide: true` removes its entire interior wall segment, including end caps, and must have the full host wall height. It retains a logical connection between the two zones for circulation, drawings and IFC while producing no physical divider or door. This supports open alcoves without changing the floor footprint.

Kitchen `prepStorageWall` selects the side for an additional worktop, base drawers and wall cupboards. A `servingCounter` can occupy half of an internal kitchen opening or a shared hall/living/dining opening; the other half remains a passage. Its footprint is shared by the drawings, model, furniture placement and walkthrough collision.

A cased opening with `servingCounter: "full"` has a 950 mm-high counter across its entire width (minimum 900 mm), and is excluded from walking connectivity. This supports a serving hatch in the same line as a retained wall. The boolean `true` retains the previous half-counter/half-passage arrangement. Shared living rooms may pair `diningPosition` with `diningOrientation` (0 or 90 degrees) and `diningLength` in millimetres. Furniture placement still checks connected passages and door clearance.

Authored living seating can use `sofaPosition` (seat centre in mm) with `sofaOrientation` (0/90/180/270 degrees from +x). `seatingExtension` may name a directly connected hall across a cased opening at least 2400 mm wide; seating can span that open zoning edge while retaining walls and door clearances. The generated editable group records its combined placement area.

`diningCounterGap` sets the authored dining envelope clearance from the serving counter in millimetres (600–1500; default 900). A 1500 mm dining table uses four chairs.
