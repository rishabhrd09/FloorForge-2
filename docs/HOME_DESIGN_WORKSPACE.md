# Custom-design workspace

The local UI now follows a single journey: choose inputs → arrange or refine rooms → review → generate. It retains the existing Python compiler, Custom Plan validator, sample packages, renderer and exporters.

## Starting a home

**Design a new home** opens a full page rather than a setup dialog. Six combinable choices explain what the user can provide: plot dimensions, a Compass map, a guided home brief, a rough sketch, a prepared DXF plan, and written requirements. The adjacent essentials panel asks for the home name, width, depth, units, road side, occupied floors and plot context. Room preferences come later. Optional local sketch assistance appears only for the sketch choice and never sends an interpretation request automatically.

The selected inputs choose an entry route. DXF supplies exact geometry when selected; Compass remains an explicit, separately reviewed alternative. A sketch is a reference unless the user explicitly requests local interpretation. Written requirements use the existing parser and input-coverage review. Choosing several cards does not create competing geometry authorities.

New projects derive their initial setbacks through the existing resolver. Roof access is an additional requirement, not an inferred occupied floor. Previous work is checkpointed before a new project is adopted; cancelling intake does not replace it.

## Editing and review

The editing workspace gives the requirement panel and design overview equal width on desktop. Plot, Rooms, Ideas and Details show one category at a time. The overview distinguishes an illustrative Compass explanation from an actual saved room map. Previously generated homes are separated into the Generated home view.

Compass is a full-window plot canvas, with the Rooms palette hidden initially. The Rooms button slides a narrow palette in from the right on desktop, reducing only the available canvas width; Hide and Escape return that space to the map while retaining the selected room. On narrow screens the palette overlays the canvas. The palette groups room creation and exact requirements under disclosures. Bold cells, split labels, a plot boundary and a marked road show the room arrangement and frontage. A placement indicator and Next room support placing rooms with the palette closed. The map fits all 16/24/32 cells while preserving plot proportions; Zoom and Fit plot change only the viewport. All three densities were checked live in the desktop browser, along with placement, Undo/Redo, drawer controls and zoom. Small regions open enlarged refinement targets. The map keeps the front road below the cells for every bearing.

Arrange rooms, Connections & needs, Review & generate, and Advanced room editing are separate sections. Advanced editing opens the existing exact editor after a reviewed Compass proposal, with explicit Back to Compass map and Back to custom design controls. Direct editing still switches geometry authority to Custom Plan and retains the Compass draft. The separate room planner is absent from the primary new-home navigation; legacy draft readers and tools remain available.

The input-review page starts with plot and room/floor summaries. Full resolved settings, provenance and coverage remain under a disclosure. Pending maps route to geometry review before generation. Accepted maps generate through the same building, scene, drawings and exports. Save/reopen retains grid density, split ownership and acceptance.

## Verification and limits

`evidence/compass-ui/` records the local browser checks and captures. The full regression suite passed 595 tests; the Node command suite passed 15 tests, including mixed-entry routing, integer-mm units, map fitting and 500 randomized edit attempts. The follow-up plot-canvas checks in `evidence/compass-canvas/` record 46 Compass regression tests, 15 Node tests and live drawer/placement/zoom checks. The 445 protected sample/viewer files and four recorded legacy plan hashes remain unchanged. Both original Compass planning documents match their safety copies.

This UI work retains the preview flag and the documented feature boundaries. Plot context does not infer second-road geometry. Site-band design, automatic lock-aware fitting, automatic programme expansion and the full conditional survey bank remain future work. Physical mobile-device, 200% zoom and first-time-user acceptance are not claimed by these desktop checks.

## Input wiring audit · 18 October 2026

The Compass canvas uses larger room labels, with one label anchored inside each room’s owned regions. Narrow rooms use a leader label when there is room beside the plot. Cell targets, half ownership and keyboard navigation remain available below the labels. The broader road marks the front approach and displays the resolved facing direction. These viewport details leave the authored allocations intact.

| Input | Engine path and checked result |
| --- | --- |
| Plot dimensions, units, road bearing, setbacks | `collect()` preserves explicit form sources; `intent.fuse()` resolves them; Compass builds its polygons inside that envelope. The live check submitted 15 × 19 m, east-facing, with a 12 × 14.8 m buildable area. |
| Room types, names, cells, halves and required/optional state | Versioned Compass records retain stable room IDs. The adapter unions each room’s regions and reserves walls before Custom Plan validation. Optional unplaced bedrooms now stay in the checklist while the generated bedroom total counts the placed rooms. |
| Room dimensions, size locks and clear routes | Targets are compared with the compiled clear polygon. Locks and insufficient routes produce repairable errors. A preferred size is reported as checked; it does not silently resize the room. Unplaced-room requests are marked unapplied. |
| Relationships, clear opening widths and entrance destination | Authored neighbours compile into checked wall openings. The live 1.8 m open kitchen connection became a 1,800 mm cased opening, and the main entry connected Living to outside. The scene uses those same walls and openings. |
| Floors, linked stairs, roof access and generation scope | Scope compiles a consecutive prefix of occupied floors. Regression tests cover one, two and three floors and real roof stair flights. Upper drafts stay saved; excluded requirements and stair links are reported off. |
| Floor height, plinth, budget, themes and other shared settings | Explicit form sources retain their provenance in the resolved brief. The live 3,200 mm floor height became 3.2 m in the scene; the budget value 75 was retained in the generated brief. The full regression suite covers the shared planners, reviews and exporters. |
| Written requirements and multiple sources | The existing source resolver and spatial checks surface conflicts. Authored geometry remains the selected arrangement. Unparsed requests and automatic programme switches requiring room edits remain visible in input coverage. |
| Plot context, notes and reference images | Saved with explicit advisory/reference status. Context does not infer additional road geometry; references require tracing or an explicitly selected interpretation/import workflow. |
| Review, save/reopen, generation and exports | Acceptance is bound to the map, effective settings and scope. Changes invalidate old acceptance. Reopening retains the map and acceptance; a matching scene hash now correctly restores the Current state and export availability. |

`evidence/compass-entrance-audit/` contains the test logs, browser captures, sample-render results and generated artifact checks. All **599 Python tests** and **16 JavaScript tests** passed. All **11 sample viewers** reached render-ready status; **445 protected sample/viewer files**, four recorded legacy plan identities and both original planning documents remain unchanged. The generated building, scene, report, review and drawing sheets share one plan hash, with PDF, DXF, GLB, IFC and ZIP artifacts present.
