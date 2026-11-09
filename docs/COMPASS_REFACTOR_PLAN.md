# FloorForge Compass and survey implementation plan

Refactor the planning input experience so a person can describe a home, answer a few questions, and click rooms onto a Compass map. Preserve those choices through the existing validated geometry pipeline into the 2D drawings, furnished 3D model, walkthrough and exports.

The recommended architecture adds a versioned Compass input model and an adapter into FloorForge's Custom Plan compiler. Keep the current automatic and legacy guide paths available. Improve input and interpretation without replacing the renderer or creating a second source of building geometry.

This is an implementation specification. It does not change application code. “Floorforce 2” is treated as the FloorForge project in this workspace; if the implementation happens in another checkout, verify its integration points before applying the plan.

## Current implementation and compatibility boundaries

| Area | Current FloorForge behaviour | Refactor requirement |
| --- | --- | --- |
| Quick Guide | Fixed 4 × 4 per-floor relative placement; cells have no metric size | Retain its existing schema and interpretation; introduce the richer Compass format separately |
| Simple room board | Two columns × four positions, up to eight room cards per floor; compilation introduces a connecting hall and coordinated stairs | Preserve existing saved boards; avoid using its automatic passage and room rearrangement rules for precise Compass assignments |
| Exact editor | Orthogonal clear-space polygons in millimetres, authored openings, linked stairs, undo and validation | Use it as the geometry destination and advanced editing escape route |
| Levels | Ground, First and Second, with separate roof-access behaviour | Preserve G, G+1 and G+2; roof access must not add an occupied floor |
| Inputs | Source fusion, explicit form overrides, description parsing and input coverage | Retain provenance and explain contradictory or unsupported answers |
| Output identity | `draftRevision`, normalized `planHash`, immutable builds and stale-export protection | Extend these protections to Compass; an old generation job cannot replace a newer draft |
| Rendering | Shared building geometry feeds drawings, scene, collisions and exports | Keep materials, lighting, themes, camera behaviour, furniture and walkthrough controls working |
| Persistence | Browser autosave, saved workspace projects and portable JSON | Extend existing storage rather than introducing an unrelated draft store |

Relevant implementation references:

- [Studio state and generation](../web/app.js): `collect`, `applyProject`, `guideProject`, `convertGuide`, `markDraftChanged`, `generate` and `loadBuild`.
- [Input contracts](../floorforge/intent.py): `_validate_spatial_grid`, `validate_values`, `fuse` and strict editor-state validation.
- [Guide conversion](../floorforge/plan_tools.py): `guide_check`, `convert_guide`, `suggest_openings`.
- [Existing room board](../floorforge/room_board.py), [Smart fit](../floorforge/smart_fit.py) and [plan preparation](../floorforge/plan_assist.py).
- [Space semantics](../floorforge/spaces.py), [Custom Plan compiler](../floorforge/custom_plan.py), [layout dispatch](../floorforge/layout.py), [input audit](../floorforge/input_audit.py), [local API](../floorforge/server.py).
- [Exact-plan and revision contract](CUSTOM_PLAN.md), [current requirements](REQUIREMENT_MATRIX.md) and [planning assistance](SMART_PLANNING.md).

There are tests that explicitly require the legacy guide to remain 4 × 4. Keep those format guarantees. Update UI assertions only where the interface intentionally changes, and add separate tests for the new format.

## Reference Compass notes

The supplied GazeConnect description and its `CompassMapScreen.tsx`, `CompassRefineFocus.tsx`, `compassPlan.ts` and `surveyQuestions.ts` establish the following interaction pattern.

| Carry into FloorForge | Adapt for FloorForge |
| --- | --- |
| Road at the bottom, back at the top, persistent left/right orientation | Preserve FloorForge's eight road bearings; the source has four primary directions |
| Room first, then click cells to place or enlarge | Also support cell first, then choose a room, using identical rules |
| Eight large room cards per page, four columns × two rows | Use a responsive two-column picker on narrow screens |
| One cell can become equal left/right halves through a focused editor | Keep each divided cell one large target on the overview |
| Stable room identities, connected assignments, replacement confirmation and undo | Distinguish Bedroom 1 from Bedroom 2 even if they touch |
| Floor switching and “Below” information upstairs | Support Ground, First and Second, plus existing roof access |
| Short setup and a separate conditional survey | Prefill from existing inputs and avoid asking the same placement twice |
| One authoritative design with plan, furnished top and exterior views | Reuse FloorForge's existing viewer modes, walkthrough and export formats |

The reference currently has **16 base cells**, with optional halves. **24 and 32 base cells are proposed additions**, not capabilities to assume exist in the reference. Gaze READY controls, dwell timing, gaze toggles and its medical workflow do not belong in the default mouse interface.

## User journey and number of questions

Offer three entry routes: **Describe my home**, **Answer a few questions**, and **Arrange rooms**. They open the same project and share its requirements. Existing saved projects should open where the person left off.

Use **eight short setup steps**, based on the reference's seven foundation questions plus grid detail. Unit selection belongs inside the dimension controls. These are eight screens, not a claim that the project contains only eight data fields.

| Step | Question and choices | Required behaviour |
| --- | --- | --- |
| 1 | **Which side of your plot has the main road?** N, E, S, W; expose NE, SE, SW, NW as additional directions | Store the outward road-side bearing; never describe it as the direction a person looks while standing on the road |
| 2 | **How wide is the plot along the road?** 20, 25, 30, 35, 40, 50, 60 ft, or Custom | Feet/inches and metre entry; preserve exact canonical conversions |
| 3 | **How deep is it from road to back?** 30, 40, 50, 60, 70, 80, 100 ft, or Custom | Preview the rectangular proportions and plot area |
| 4 | **What surrounds your plot?** Middle plot, Corner, Three sides open, Independent, or Choose later | Ask the second road side for a corner plot and neighbouring built boundaries when relevant; unknown stays unknown |
| 5 | **How many occupied floors?** Ground only, G+1, G+2 | Show a separate “Stairs to roof terrace” toggle; preserve existing project values |
| 6 | **How many bedrooms?** 1, 2, 3, 4, or Custom within the selected planning path's limits | Show a per-floor allocation only for multiple floors; custom zero-bedroom projects remain valid |
| 7 | **Where should the main gate be?** Left, Center, Right, or Let the planner choose | Illustrate the selected position; distinguish gate position from the front door's destination |
| 8 | **How much grid detail?** Simple 16, Detailed 24, Fine 32 | Default to 16, show previews and approximate dimensions; allow continuing without changing the default |

For a new project, road direction, width, depth, occupied floors and bedroom requirement must be known or visibly confirmed from defaults. Plot context, gate and density can remain at an explicit default or “choose later.” Missing required dimensions block generation with an explanation, while a draft can still be saved.

Keep **Back**, **Continue**, **Save and exit**, a short explanation and a progress indicator in consistent positions. Skip means retain the current answer or record unanswered; it never resets a prefilled answer. Do not automatically advance as soon as a card is clicked. Description-derived values show their source and need no repeated entry.

After setup, show the map with a checklist of required rooms. Keep attached bathrooms, kitchen openness, pooja, parking, Vastu and budget available in **Home preferences**. These existing FloorForge inputs remain accessible even though they are outside the eight foundation steps. Ask further questions only when the selected programme or a conflict requires them. A typical project should need about **5–12 relevant follow-up answers**, an interaction target to validate with users rather than a fixed questionnaire length.

## Compass screen layout

Use a full planning workspace that retains FloorForge's visual language and the reference's generous spacing.

| Region | Contents |
| --- | --- |
| Header | Back to project, project name, saved/saving state, Undo and Redo |
| Floor tabs | Ground, First, Second as applicable; issue counts; clear separate roof-access control |
| Main map | Room regions, names and colour markers, back/left/right labels, compass, scale, setbacks and gate |
| Action rail | Rooms, Next room, Refine, Check layout, Generate plan |
| Road strip | FRONT / MAIN ROAD, road bearing, frontage width, selected room and assignment coverage |
| Requirements panel | Required/placed/unplaced room checklist, relevant questions and actionable conflicts |

On smaller screens the requirements panel becomes a drawer and the action rail becomes a stable bottom toolbar with safe-area clearance. Keep the road visible in the focused editor. At 24 or 32 cells, offer a larger regional editing view rather than shrinking the text or click targets.

**Recommended FloorForge geometry adaptation:** display the full plot and setbacks, but anchor the dimensioned room grid to the **buildable envelope**, matching the current guide-to-Custom Plan conversion. Label it “Room grid inside the buildable area.” Show front, rear and side open spaces as distinct surrounding site bands that can be selected for garden, yard, parking or arrival requirements. Outdoor spaces can also occupy cells inside the buildable envelope. This avoids implying that an indoor room may consume a setback. Site bands are not additional base cells.

A cell's displayed width/depth is its allocation span. A generated room's clear dimensions account for walls. Show both with those names; a grid span must never be labelled clear width. Keep the map's metric aspect ratio correct and display approximate dimensions before generation. Changing plot dimensions or setbacks after placement requires a review of affected rooms and a geometry proposal; do not silently stretch an authored plan.

Keep the road at the bottom in the editor, generated 2D plan and furnished top view. Changing bearing changes geographical labels and solar/Vastu orientation without permuting room assignments. The north-up road chooser may rotate its small illustrative plot, as it already does. Exterior cameras retain their existing controls; named Front Left/Front Right/Back Left/Back Right shortcuts may be added through existing viewer APIs.

## Placement and room identity

Support these equivalent interactions:

1. Choose **Bedroom 1**, then click its cell; click an adjoining cell to enlarge it.
2. Click an empty cell, then choose an existing room or **Add another bedroom**.

Offer a dedicated **Erase** action as well as toggling an already selected region off. **Next room** advances the requirements checklist and can leave a room unplaced. It does not invent a position. Selecting or opening the map does not switch the active generation input.

Apply one rule set to all placement routes:

- A room's ID stays stable through renaming, resizing, save/reopen, geometry compilation and selection in 3D.
- Adjoining regions with the **same room ID** form one room. Same type alone does not merge two bedrooms.
- A room is connected through a shared edge with positive length. Corner contact alone is insufficient, including whole-to-half and half-to-half contact.
- Adding a disconnected region to an existing room asks whether to create another room or choose a connected position. Do not quietly create a disconnected Bedroom 1.
- Removing or replacing a region checks the connectivity of the donor and recipient rooms before committing.
- Replacing another room identifies it and asks for confirmation. If it removes the last region, say that the room becomes unplaced; retain a required room in the checklist.
- Connectivity-breaking edits are rejected with alternatives such as “Use the other half,” “Keep the bridge,” or “Create a separate room.”
- Empty means **unassigned**. Garden, passage, terrace, open-to-below and a room not yet placed are separate states.
- Coverage is assignment progress, not a validity score. Show counts of required rooms placed alongside it. Never force 100% occupancy.
- The simple workflow proposes one linked stair core. Existing advanced plans with additional supported cores remain editable in Custom Plan.

### Room catalogue

Use eight large cards per page, with a name, consistent colour marker, placement status and a plain-language fit warning. Show the current room and nearby compatible rooms first. Keep search and categories secondary to the primary cards.

| Group | Choices and semantics |
| --- | --- |
| Entry and outdoors | Porch/outer lobby, verandah, garden/lawn, backyard, courtyard/lightwell, parking, balcony, terrace, drying yard |
| Living | Drawing room, living hall, family lounge, dining, foyer, passage/hall |
| Cooking and storage | Kitchen, pantry/store, utility, drying room, dressing |
| Private | Master bedroom, numbered bedrooms, study/office |
| Bathrooms | Common, attached, powder room and service bathroom; attachment is an explicit relationship |
| Vertical and open space | Staircase, stair landing, open to below; advanced lift/shaft only with the existing support limits explained |
| Optional needs | Pooja, home care room, caregiver room and other supported specialist requirements |

Use `spaces.py` as the semantic source. **Drawing room** and **drying room** must remain different types. Master is a bedroom identity/role. “Kitchen + store,” “Living + stairs,” and “Dining + stairs” are convenient composite presets that create explicit component rooms, connections and a stair core in a reviewed proposal. They must not become arbitrary strings that the compiler cannot interpret. A host room excludes its stair core's area.

Garden, backyard and parking are not currently interchangeable room kinds. Implement typed site-zone mappings and their effects before showing them as applied choices. Reuse courtyard or garden attributes only when their compiled semantics truly match. Never disguise unsupported site inputs as enclosed rooms.

## Grid resolution and focused refinement

| Option | Columns × rows | Maximum regions if all cells are split |
| --- | --- | --- |
| 16 base cells | 4 × 4 | 32 halves |
| 24 base cells | 4 × 6 | 48 halves |
| 32 base cells | 4 × 8 | 64 halves |

Grid density is independent of room count. One room can cover many neighbouring regions and form an orthogonal L shape. All occupied floors share the same grid definition and alignment. Wider alternative arrangements can follow later; the first release needs the three predictable arrangements above.

Use logical `row = 0` at the front and `col = 0` at the left. Display the highest row first, so the back remains at the top. Human labels are Row 1 at the front through Row 4/6/8 at the back. UI projection must never reverse saved row order.

Changing an occupied grid's resolution is an explicit proposal across every floor. Compare normalized spatial overlap to suggest a remapping; preview moved, merged, split, unassigned and conflicting regions. Preserve room IDs and both the original draft and proposed mapping. Do not resolve a collision by dropping a room or taking the majority owner silently. Confirm the remapping as one undoable transaction. Cancel restores the original exactly. A higher-detail grid can make narrow assignments less usable; it is not automatically a better plan.

### Half-cell workflow

1. Choose **Refine**, then a cell.
2. Open a focused view with two large choices: **LEFT HALF** and **RIGHT HALF**.
3. Choose a half, then select a room or **Leave empty**.
4. Commit division and assignment together after validation.
5. Return to the map, then choose **Done refining**.

The focused view shows the floor, row/column, highlighted miniature map, current owners, span dimensions, estimated clear dimensions, warnings and the road strip. Upstairs, show the room or space below each half, including multiple owners when the lower cell is itself divided. Include Undo, Whole cell and Back to map. Lock background actions while the focused editor or confirmation is open.

Opening the focused view, selecting a half, or cancelling its picker changes nothing. When an occupied whole cell is first divided, its room retains both halves until an assignment changes. If a room is selected in ordinary placement and the user clicks a divided cell, open the same large half choices and apply the selected room there. The overview cell remains one selectable target.

**Whole cell** merges the two halves. If owners differ, ask which should receive the whole cell, or cancel; validate the room losing its half. Splits are exactly 50/50 left/right in map coordinates. Arbitrary percentages, quarter cells and freehand dividers are outside this refactor.

The source application's 2 ft 6 in half-width threshold is an application rule. Do not substitute it for FloorForge's room-specific minimums. Validate resulting room polygons after joining neighbouring regions and reserving walls. Small regions may be parts of a usable larger room. Show draft warnings and block generation for actual invalid geometry using existing FloorForge rules. Include a local narrow-neck check for new nonrectangular unions; the current bounding-box short side alone can miss a thin connection. Keep new checks scoped so legacy no-edit outputs retain their behaviour.

## Conditional survey and answer effects

Organize deeper questions by Site, Rooms, Connections, Upper floors, Sizes and Preferences. Use large answer cards, short help text, a skippable optional path and a review summary. Do not reproduce sixteen slot questions followed by sixteen repeated map assignments. An optional guided placement wizard should select the corresponding cell and issue the same assignment command as the map.

Every question definition needs a stable ID, answer type, choices/custom-entry rule, applicability condition, default policy, model target, compiler/validation consumer and user-visible effect. Track each retained answer as **applied**, **preference checked**, **needs clarification**, or **note only**. Do not offer an operational choice whose only implementation is storing a label.

| Survey topic and retained reference choices | Effect or required implementation |
| --- | --- |
| Plot context, second road, neighbouring built edges | Site context and permitted opening/exposure assumptions; additional-road geometry needs an explicit site compiler extension |
| All-around, L-shaped, front/back or front-only open space; front/rear/left/right setbacks | Resolve explicit setback values and show the resulting envelope. Keep L-shaped outdoor placement distinct from a promise of a nonrectangular buildable boundary |
| Front/side/back entrances | Explicit entry objects and access relationships; validate actual external routes |
| Floor programme and bedrooms per floor | Required room instances with floor assignments; no unrequested occupied floor |
| Home care and caregiver | Optional room instances and relevant access requirements; preserve specialist notes as notes |
| Large living, drawing + living, family lounge, or open living/dining/kitchen | Room instances plus open/separated connection requirements |
| Dining separate, connected to living/kitchen, open plan, or verandah | Connection graph and a defined dining location; avoid generating a second dining room for one requirement |
| Kitchen closed, open, partially screened, utility, pantry or island | Actual openings/enclosure, component spaces and furnishing constraints; screened/island choices require a real supported mapping |
| Pooja room, niche or none | A room, supported furnishing feature, or no object; do not model a niche as a full room |
| Master attached with/without dressing, guest attached, common, entrance powder, care or service bathroom | Separate room identities, `attachedTo`/access edges, dressing where requested, wet-space validation |
| Internal center/side stairs, external side/rear, lift + stairs, or none | Explicit core and landing proposal. Disable unsupported external/lift configurations with a reason rather than mapping them to unrelated stairs |
| Courtyard, lightwell, none, or planner choice | A typed outdoor/void zone and its vertical open-sky consequences |
| Upper master/kids bedrooms, lounge, study, balcony, terrace garden, theatre | Per-floor room requirements and support/roof/void checks. Theatre is a named supported room use or an explicit unsupported request |
| Preferred room dimensions | Targets or explicit locks; show target versus resulting clear size; exact locked dimensions cannot be overridden by a fit |
| Main door opens into foyer/drawing/living/corridor/verandah/porch/sit-out | Entry destination in the access graph; distinct from gate position |
| Secondary door and kitchen/master/care-room access | Required access edges; reject invalid routes such as a shared-room route through a private bedroom |
| Passage width: 3, 3.5, 4, 5 ft, custom, or open plan | A metric target or locked constraint, checked against the compiled path; open plan does not mean all access checks disappear |
| Kitchen/master/pooja/stair/care compass preferences | Bearing-aware preferences compared to authored positions; conflicts ask whether to retain the map or revise it |
| Vastu, style, budget, special requests, final notes and draft confidence | Preserve existing Vastu/theme/report behaviour. Confidence is metadata. Unsupported prose remains visible as a note |

Retain useful dimension presets from the reference, with Custom available: master 12×12, 12×14, 14×16, 16×20 ft; kitchen 8×10, 10×10, 10×12, 12×14; drawing 12×14, 14×16, 16×18, 18×20; living 14×16, 16×18, 18×20, 20×24. Care presets 12×14/14×16/16×18 and caregiver presets 8×8/8×10/10×10 appear only when requested. Presets are targets, not guaranteed fits.

Ask focused clarifications when needed: one room or two adjacent same-type rooms; open or separated drawing/living; open, screened or closed kitchen; shared-room stair hosting; landing destination; terrace versus enclosed room versus open-to-below; narrow-room expansion; wheelchair route destinations; and map/text disagreement. Present two or three understandable choices with a highlighted preview. An unresolved geometry conflict blocks generation while preserving the draft.

## Generation and plan review

Before generation, summarize required rooms, unplaced items, blocking issues and the floors included. Offer **Ground only**, **Ground and First**, or **All occupied floors** when applicable, without discarding unfinished upper-floor drafts. Generate only a consecutive prefix of the occupied floors; an upstairs-only model would omit its supporting geometry.

Treat this as an explicit generation scope. Derive its floor count, bedroom count, linked stair extent and roof-access eligibility in a temporary generation input, while preserving the full project. Show what is omitted before acceptance. Do not put an accessible roof over an unfinished floor as a substitute for the requested upper storey. Include the effective scope in the Compass build identity, and label partial results and downloads with their included floors. The current-output check must compare both the relevant semantic input and the selected scope.

The results screen should provide **Back to map**, floor switching, **2D plan**, **Furnished top view**, and **Exterior**, using existing FloorForge viewer modes. Retain the existing walkthrough and furniture tools. Add named exterior-angle shortcuts through the existing camera interface where useful. Show plan notes, requirement coverage, warnings and actionable generation errors with Retry. A 2D room selection and its corresponding 3D highlight use the same stable ID.

Keep current PNG capture, PDF drawing sheets, DXF, GLB, IFC and package exports. A PNG represents its selected view; drawings and model exports represent the accepted geometry and scope. A higher-detail export may add documentation but must not redesign the house. Drawings, top views and exterior perspectives must come from the shared geometry rather than independent generated images. Changes in the map immediately identify the displayed result as belonging to a previous revision.

## Shared model and geometry integration

### Versioned Compass input

Introduce a separate `floorforge.compass-input/1` contract. Keep dimensions in FloorForge's canonical millimetres and use an explicit rounding policy at geometry projection; do not import the source application's integer-inch model. Derive shared grid lines once so rounding cannot introduce gaps or overlaps between neighbours.

The contract should include:

- `grid`: rows, columns, buildable-envelope basis, row-origin convention and per-cell split state.
- `floors`: stable IDs, ordered occupied levels and references to their room assignments.
- `rooms`: stable ID, kind, name/role, floor ID, whole/half region references, required status, target dimensions and optional locks.
- `connections`: stable room IDs, open/door/separated/attached relationship and any required passage/access width.
- `stairLinks`: explicit related cores, host relationships and landing destinations across floors.
- `site`: typed outdoor zone assignments, plot context, neighbour boundaries, second road and gate preference, referencing canonical plot facts.
- `requirements`: normalized, supported survey choices and provenance; notes remain distinguishable from constraints.

Keep plot width, depth, bearing, occupied-floor count, themes and other existing facts in the resolved brief. Do not create competing plot dimensions inside the Compass model. Store an envelope hash with conversion proposals to detect obsolete proposals after site edits. A region has at most one owner; derive the unassigned set from the complete region partition rather than maintaining contradictory ownership arrays.

UI selection, picker page, zoom, current floor, pending confirmation and undo history are editor state. Pending proposals are separate from committed input and cannot affect generation until accepted. Save an optional proposal for resumption only with its base hash and an explicit unapplied status.

### Active input and compilation

Use this sequence:

`Description and survey → resolved requirements → Compass assignments → checked geometry proposal → accepted Custom Plan → existing building, scene, drawings and exports`.

Retain legacy Automatic, Quick Guide, room-board and exact Custom Plan modes. Add an explicit Compass input selection; keep other drafts saved but inactive. Never submit both an authoritative legacy `grid` and `customPlan`, and do not accidentally send an inactive Compass draft into generation.

The new adapter should:

1. Validate the new schema and resolve existing facts with the normal provenance rules.
2. Build a region adjacency graph, including split boundaries; verify ownership and connected room IDs.
3. Project grid regions into the buildable envelope, union each room's regions and reserve the existing wall allowance after union. Internal boundaries inside one room do not create walls.
4. Produce stable Custom Plan room IDs and orthogonal clear-space polygons. Reject collapsed shapes, holes or unsupported disconnected geometry with room and region references.
5. Translate connection choices using supported `door`, `entry`, `cased`, `glazed` and `openSide` semantics. Propose openings on actual shared walls; do not treat every grid boundary as a wall or every neighbour as a doorway.
6. Coordinate stair cores, landings, voids, open-sky spaces, support envelopes and roof access. A landing label cannot create a staircase.
7. Use existing preparation/opening helpers where appropriate. Run canonical validation before offering the proposal as usable. Return valid partial previews and structured issues without presenting them as a finished plan.
8. Offer fitting only as an explicit proposal. Existing Smart fit can move rectangles and does not fully solve arbitrary orthogonal shapes. Add lock-aware constraints for the new path; preserve assigned regions and floor IDs by default. A proposal leaving a user's placement or size lock must request acceptance and show the difference.
9. On acceptance, commit the proposal and its Compass-to-room mapping in one undo step; run the ordinary generation pipeline.

Keep the accepted compiled Custom Plan as a derived artifact while Compass is active, identified by the Compass semantic hash and adapter version. It is never an independently editable second authority. Any relevant Compass/site edit invalidates it. Opening **Fine-tune** and accepting a direct polygon edit explicitly switches authority to Custom Plan and retains the original Compass draft. Returning to Compass must not overwrite the exact edit without a conversion preview.

Unassigned space stays unassigned. If circulation is missing, propose named passage regions or ask which rooms should connect. Never inherit the room board's automatic central hall or silently carve corridors out of locked rooms. A constrained-plan failure returns a useful conflict, not an unrelated automatic layout.

### Conflict priority

Preserve existing source priorities for old projects. For the new Compass path, a committed placement controls that room's location. Explicit resolved site dimensions control the envelope. Survey/text preferences that disagree with either produce a named conflict or an input-coverage explanation. A new optional AI proposal remains unapplied until accepted; confidence does not grant it priority over an authored map.

Example: “Kitchen in the south-east” and a front-left Kitchen assignment must be evaluated against the current bearing. Show the disagreement and offer **Keep my map**, **Move kitchen in a preview**, or **Edit requirement**. Record the selected resolution; never repeatedly ask the same resolved question.

## Persistence and schema migration

Add a versioned project format only where required, with explicit readers for current projects and legacy grid formats. A likely new version is `floorforge.project/0.5`; confirm it against repository conventions during implementation.

This requires coordinated changes: `intent.fuse` rejects unknown top-level fields, editor state currently requires three fixed 4 × 4 guide drafts, and source values accept only fields from `DEFAULTS`. New survey/site records need intentional validators and consumers. They cannot simply be added to the payload and assumed to work.

The existing theme-default compatibility branch recognizes project versions 0.3 and 0.4 explicitly. If adding 0.5, update that logic deliberately so a new Compass project does not fall back to legacy `current` themes. Preserve old projects' resolved defaults and appearance.

| Saved input | Migration behaviour |
| --- | --- |
| Existing `spatial_hint` guide | Retain relative semantics until an explicit conversion; no dimensional promise on reopen |
| Older `cell_mm` grid | Preserve its exact legacy generation path and metric dimensions; conversion needs a preview and backup |
| Existing room board | Preserve eight-position draft and original compile path; conversion into Compass is explicit |
| Existing Custom Plan/imported DXF | Retain polygons, openings, stair links and placement overrides; do not auto-rasterize into cells |
| New Compass | Restore density, split cells, identities, requirements, relationships, site context and active input |
| Unknown newer version | Open a recoverable read-only view where possible, allow original-file download, and never overwrite it |

Backups precede destructive conversion or reset. Confirm replacement of another room, replacing an authored plan, clearing a floor/project, discarding upper-floor content and changing an occupied grid's density. Routine navigation and additive edits need no confirmation. Lowering visible floor count archives higher Compass drafts for restoration; generation includes only selected occupied floors. Existing Custom Plan floor-removal semantics remain available in its editor.

Extend the current browser autosave, workspace checkpoints and portable JSON flow. Do not claim backend draft autosaving exists merely because the source application has it. Expose storage/quota failures and a working Save project action. Verify save/reopen through both the new Compass UI and the existing project switcher.

### Hashes and stale output

Include all active semantic inputs, accepted conflict resolutions and adapter version in the new Compass identity. Keep selection, zoom, question page, undo history and revision counters outside the semantic hash. Changes to an inactive draft must not change the active plan hash.

Preserve the exact old hash calculation when Compass is absent; adding an always-present null key would change old hashes. Opening the new UI without edits must not change old geometry, themes or export identity.

Every committed output-affecting edit marks previous 3D, drawings and exports stale. Reuse the existing revision/hash guards for check, conversion, fitting and generation responses. A response applies only to the matching base hash/revision. Gate/site/relationship answers must participate when they actually affect output. Editor-only confidence and draft notes should not force a geometry change.

## API and file change plan

Keep the current plain-JavaScript/Python stack. A frontend framework migration is unnecessary.

| File or proposed module | Responsibility |
| --- | --- |
| `web/compass-state.js` new | Explicit edit modes, pure assignment commands, validation feedback and undo transactions |
| `web/compass-editor.js` new | Map, floor tabs, room cards, road/gate, issue focus and responsive regional view |
| `web/compass-refine.js` new | Enlarged half choices, whole-cell merge and owner confirmations |
| `web/survey-questions.js` and `web/survey-flow.js` new | Typed question definitions, conditional flow, prefilling and answer effects |
| `web/app.js`, `web/index.html`, `web/style.css` | Narrow integration for input selection, saving, stale state and scoped UI styling |
| `floorforge/compass_input.py` new | Normalize/validate versioned input, ownership, adjacency and migrations |
| `floorforge/compass_adapter.py` new | Region-to-polygon proposal, stable IDs, relationship/opening and stair mapping |
| `floorforge/intent.py`, `model.py`, `input_audit.py` | Allowed schemas, provenance, supported new facts and conditional hash extension |
| `floorforge/plan_tools.py`, `plan_assist.py`, `smart_fit.py` | Reuse helpers; add explicit Compass lock semantics without changing legacy behaviour |
| `floorforge/spaces.py`, site compilation modules | Supported catalogue and typed site-zone/gate effects; additive changes with regression checks |
| `floorforge/server.py` | Capability discovery, new routes and static-file allowlist; retain request/origin/token protections |
| Tests, browser scripts, fixture/evidence directories | Schema, geometry, migration, interaction and rendering regression coverage |

Proposed new endpoints: `POST /api/compass/check`, `/api/compass/convert`, `/api/compass/remap` and `/api/compass/migrate-preview`. Use the existing `/api/intent`, plan validation and `/api/generate` contracts for the accepted result. Conversion returns the candidate, changes, issues, source hash and adapter version; it does not publish a build or mutate the saved project. Request bodies must pass explicit size/field limits, and errors identify floor, room, regions, code, severity and valid repair actions.

Expose capability information from `/api/session` so the UI can distinguish supported, advisory and unavailable catalogue/survey choices. A feature flag should enable the new entry point while keeping legacy readers and outputs accessible. Do not modify the viewer bundle or rendering dependencies for the input refactor. Geometry/site additions go upstream and must satisfy the existing scene contract.

## Implementation sequence and completion gates

| Phase | Deliverable | Completion gate |
| --- | --- | --- |
| 1. Baseline and contracts | Record current no-edit hashes/output fixtures, document active-input rules, define new schema and survey effect table | Legacy fixtures and saved-mode behaviour are reproduced; new fields cannot leak into old inputs |
| 2. Editing foundation | Versioned state, room identity, 16-cell placement, all existing floors, undo/redo and autosave | Both click routes work; cancellation, connectivity and stale state behave correctly |
| 3. Refinement and density | Focused 50/50 editor, whole-cell recovery, 24/32 cells and reviewed remapping | Tiny-target selection is unnecessary; remapping cannot lose a room; all-floor undo is atomic |
| 4. Survey integration | Eight foundation steps, prefilled answers, conditional question bank and coverage review | Each enabled answer has a defined applied/preference/note status and no duplicate slot entry |
| 5. Geometry and site wiring | Polygon adapter, connections, coordinated stairs, site/gate requirements and explicit fit proposal | Accepted input produces the expected geometry or named repairable conflicts; no silent relocation or corridor creation |
| 6. Shared-output validation | Generate through existing pipeline; preserve room IDs, themes, furniture and walkthrough | 2D, scene, collisions and exports agree on hash and geometry; previous render baselines remain valid |
| 7. Migration and release | Legacy fixtures, mobile/keyboard QA, usability sessions, documentation and guarded rollout | Save/reopen and rollback retain all drafts; novice users complete the core tasks without precision drawing |

Ship complete vertical slices behind the flag. Do not expose an enabled control before its model consumer and validation exist. Rollback disables the new entry point while retaining the ability to recover newly saved Compass data; never downgrade-save it through an older writer.

## Acceptance and regression checks

The change is ready when these observable scenarios pass:

1. A new user completes the eight-step setup, places a living room and two distinct bedrooms with clicks, refines a bathroom half, and generates a matching plan without drawing walls.
2. N/E/S/W and NE/SE/SW/NW update geographical interpretation while every room stays in its chosen map position. The road remains at the bottom of 2D/top views.
3. An L-shaped same-ID room has no wall on its internal cell boundary. Two touching same-type bedroom IDs remain separate rooms.
4. Corner-only contact, a removed bridge and a replacement that disconnects another room are identified before commit. Cancelling confirmation retains the exact draft.
5. Opening Refine and cancelling does not split the cell. Assigning a half is one undo step. Whole cell asks about differing owners, and Undo restores both owners.
6. A 16-cell map with all cells split is saved as 16 cells/32 regions, independently of a 32-cell map with up to 64 regions.
7. Switching 16/24/32 previews affected assignments on all floors, retains IDs, and either commits without unresolved loss or stays unapplied. Save/reopen preserves the choice.
8. A G+2 project keeps three occupied floors, matching stair cores, upper-floor below labels and separate roof access. Reducing active floors retains recoverable Compass drafts.
9. Indoor geometry stays within the buildable envelope. Allocation spans and clear dimensions are different labels; narrow necks and wall-offset collapses identify the affected room/regions.
10. Gate, open/separated room relationships, attached bathrooms, outdoor zones and requested access change the actual model when shown as applied. Unsupported requests remain visible and are never reported as satisfied.
11. An unplaced required room and missing circulation produce a useful repair task. Empty space never silently becomes a corridor or an invented room.
12. A map/text conflict is resolved once with a visible choice. Skipping or returning through questions preserves prefilled answers. Editing the map updates the guided-placement answer automatically.
13. Conversion and fitting retain positions by default. Proposed moves, size changes, new passage areas and linked-floor edits are listed before acceptance. Old asynchronous responses cannot overwrite newer input.
14. Existing Automatic presets, relative guides, metric grids, eight-position boards, exact plans, DXF imports, saved placements, sample projects and themes still open and generate through their original paths.
15. New and legacy save/reopen operations preserve IDs and the expected hash. Inactive Compass edits cannot alter active automatic/custom outputs. Unknown versions remain recoverable.
16. An accepted Compass design has matching building/scene/drawing/report/export identities. Editing it marks old outputs stale and blocks exporting them as the current draft.
17. At narrow mobile widths, with keyboard only and at 200% zoom, all actions and confirmation choices remain reachable. Focus returns to the originating cell; names/status supplement colour. All placement tasks work without dragging or hover.
18. A plan-only/check operation does not unexpectedly change camera, lighting, themes, materials, furnishing or a previously loaded scene. Walkthrough doors, collision, stairs and existing furniture editing still work after generation.
19. Generating Ground only preserves unfinished upper-floor drafts, labels the result's scope, and derives valid floor/bedroom/stair/roof inputs without changing the full saved project. Returning to all floors restores those drafts and requires a matching new build.

Use existing backend regression suites, especially `test_spatial_inputs.py`, `test_custom_plan.py`, `test_plan_usability.py`, `test_editor_input_selection.py`, `test_input_coverage.py`, `test_roof_access.py` and `test_wall_junctions.py`. Add meaningful new Compass schema, adjacency, projection, relationship, migration and API tests rather than rewriting tests to accept lost behaviour. Include randomized assignment/removal sequences to check single ownership, connectivity and undo restoration.

Extend the real browser evidence approach used by `scripts/check_custom_editor.mjs`, `check_room_workflow.mjs`, `check_input_modes.mjs` and the roof-access checks. Capture 16/24/32 maps, the picker, refinement, conflicts, mobile and generated views. Run the full regression suite and reproducibility check before enabling the new path broadly. Compare existing deterministic scene/geometry baselines and capture browser rendering; investigate differences rather than updating the baseline automatically.

Use spacious targets, preferably 64–80 CSS pixels for primary cards and selection controls when space permits. Provide enlarged editing when that size cannot fit. Keep visible focus, accessible names, arrow-key grid navigation, Enter/Space selection, Escape/back and accessible Undo/Redo. Treat these dimensions as product design targets, not a compliance certification.

For formative usability, ask several first-time users to complete setup, place/expand a room, split a cell, repair a conflict, switch floors, generate and return to edit. Record hesitation, accidental replacement and facilitator help; refine the flow before setting a completion-time promise.

## Developer handoff

Use [the implementation prompt](COMPASS_REFACTOR_IMPLEMENTATION_PROMPT.md) with this specification. Begin with the baseline/schema phase, then deliver each working slice with its tests and evidence. The central release criterion is simple: a user's room placement must meaningfully control the generated house while existing FloorForge designs and rendering continue to work.
