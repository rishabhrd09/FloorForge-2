# Plan Reveal: walk in from the plan

Plan Reveal publishes a generated home as a scroll-driven page that opens on the home's own floor-plan drawing and ends inside it. Scrolling is the only clock. Each frame (camera, cut height, which rooms are in colour, doors, captions) is a pure function of the scroll position, so scrolling back un-builds the house exactly as it was built.

Two gallery samples use it: **The Aangan House** and **The Long House**. Their gallery cards open with **Walk in from the plan ↗**. Any other published export can get the same page with one command (see below).

## What the visitor sees

| Chapter | What happens |
| --- | --- |
| 01 Sheet | The ground-floor plan as a drawing, with the headline on the left and a title block. The drawing *is* the 3D model, cut at +1.2 m and seen from about a kilometre up through a 2° lens. The drawing set's own annotations are laid over it: wall poché, door swings, tags, dimension chains, grid and levels. |
| 02 Lift | A dolly zoom. The lens opens from 2° to 40° while the framing holds and the cut rises, so the walls grow into an axonometric line drawing. |
| 03 Forecourt | The camera comes down to the street in front of the gate. The garden, the facades and the street sweep from drawing into colour, starting at the gate, with an orange line at the sweeping edge. |
| 04 Rooms | The camera walks the real route from room to room, through real openings, with at least 20 cm of clearance from walls and furniture. Doors and gates open as the walk reaches them. Each room stays a line drawing until the visitor steps in; then it sweeps into colour from the doorway they came through. Every stop has a room card (size, area, ceiling, where the light comes from), and **Open file +** shows the room file: clear size in m and ft, area, ceiling, every opening, the daylight ratio, and the Vastu zone when the report has one. A change of floor lifts out of the current floor, shows the next floor's plan from above, and drops into it. |
| 05 Plan | The camera climbs back out and the house is cut down to its plan. The neighbours sink away, everything beyond the plot folds back into paper, and the light changes to a high plan light. The result is the plot as a full-colour rendered plan on its sheet, with poché walls and whole tree canopies. Paper then wipes back across it, and the end card links to the drawing set (PDF), the free 3D walk and the CAD (DXF). |

The room ruler on the right jumps to any room. With `prefers-reduced-motion` the camera holds still at each stop instead of drifting. A plain-text list of the rooms and their facts is in the page for screen readers.

## The two samples

- **The Aangan House** (`examples/gallery/aangan-house/`) is a single-storey, east-facing house on a 55 × 80 ft plot. Every room opens onto a central aangan with a mango tree in a seat-height planter and a tulsi vrindavan. It is drawn in the stencil theme.
- **The Long House** (`examples/gallery/long-house/`) is a G+1, north-facing house on a 30 × 60 ft plot. It is laid on one line: living room, a light court open to the sky through both floors with an ashoka rising through it, dining, kitchen and a rear garden. Upstairs are a gallery over the court, two bedrooms and a garden balcony. It is drawn in the serif theme.

Both are authored custom plans (`floorforge.custom-plan/1`). `scripts/build_plan_reveal_samples.py` holds their exact rooms, openings, stair, walk order and page copy. It runs the normal FloorForge pipeline and publishes the walkthrough beside the usual exports:

```bash
.venv/bin/python scripts/build_plan_reveal_samples.py                 # both samples, refreshes catalog.json
.venv/bin/python scripts/build_plan_reveal_samples.py long-house      # one sample
```

Their clean source projects are in `examples/gallery/briefs/aangan-house.json` and `long-house.json`. **Use this sample** in the studio loads them as editable custom plans.

## Make one for your own home

Generate and export a home as usual (automatic, Quick Guide or Custom Plan), then:

```bash
.venv/bin/python -m floorforge reveal --export path/to/export
.venv/bin/python -m floorforge reveal --export path/to/export --order living,kitchen,master --grade dusk
```

This writes `reveal.html`, `reveal-data.js`, `plan-reveal.js` and `reveal-manifest.json` beside `building.json` and `scene.json`. Pass `--out` to write the page somewhere else. The page needs no network and opens straight from disk. Keep the folder together, because the end card links to the export's `drawings.pdf`, `preview.html` and `floorplans.dxf`.

- `--order` lists the rooms to present by id, kind or name, in walking order. By default the walk takes the entrance room, the living spaces, a courtyard, the kitchen and dining, then the two largest bedrooms and one terrace, a floor at a time (at most eight stops).
- `--grade` picks the light: `golden` (default), `day`, `dusk` or `overcast`.
- From Python, `plan_reveal.publish(folder, order=[...], copy={...})` also takes page copy (eyebrow, headline lines, lede, end title and text, `theme: 'stencil' | 'serif'`). An order entry may be `{'room': 'u-gallery', 'focus': 'l-court'}` to stand in one room and look into another.

To add another curated sample, copy one of the two project functions in `scripts/build_plan_reveal_samples.py` and add it to `SAMPLES` with its title, copy and order. The script validates the plan and refuses one with review errors. The custom-plan option `centerTree` on an open courtyard gives the aangan finish used by both samples, with a frangipani, a mango or an ashoka (see [CUSTOM_PLAN.md](CUSTOM_PLAN.md)).

## How the page is made

- **Sheet.** `floorforge/plan_reveal.py` converts the drawing set's plan elements (`drawings.plan_elements`) into instanced screen-width lines, text and poché. The page does not draw floors or furniture from the sheet, because the model draws its own.
- **Ink.** A second render of the same model into a normal and depth buffer gives the pen lines: silhouettes where inverse depth stops being planar, creases where normals turn. These are composited after the photographic grade, on a warm paper with fibre and mottling.
- **Reveal mask.** A plan-view texture with one channel per storey. Each room owns its floor, a few centimetres of its wall faces, and the doors and windows in its walls. The garden owns everything else on that storey. A room's shape is drawn with a soft disc that grows from its doorway.
- **Walk.** The route is A\* on an 8 cm grid over the free floor (rooms and door gaps, eroded by the camera's body, minus furniture). Outside, it also avoids hard obstacles and planting. The path is pulled taut, passes square through doors and is smoothed. Each stop is chosen like a photographer would: candidate spots by the door and in the corners are tried at every heading. A view scores for the floor it shows, depth ahead, and the room's main fitting in frame at a comfortable distance. It loses for a wall in the face, a wall or tall cupboard filling one side, furniture or a door leaf in front of the lens, or a long detour. A court too small to stand back in is framed from its doorway. A balcony looks out over the rail. At each stop the camera settles to about 1.35 m and holds level, with a lens shift instead of a tilt, so walls stay vertical as in an interior photograph.
- **Viewer.** The page subclasses the realistic walkthrough viewer (`web/viewer/src`), so materials, planting, light, grades, ambient occlusion and the AgX grade are the same as in `preview.html`. One cut plane is shared by every material in the house and the site. Planting is not sliced: plants stand whole up to the storey being cut.

The page source is `web/plan-reveal/src` and the template is `web/plan-reveal/page.html`. Rebuild the bundle with `node web/plan-reveal/build.mjs`; it reuses `web/viewer/node_modules`. Then rerun the sample script, because `tests/test_plan_reveal.py` checks that every published copy matches `web/plan-reveal.js` by digest. The fonts are embedded OFL faces (IBM Plex Mono, Big Shoulders Stencil Display, Instrument Serif). See `licenses/plan-reveal-fonts/`.

## Ideas taken from the reference walkthroughs, and what is different

The reference videos showed a plan-to-walkthrough presentation. In it, a drawing lifts into 3D with a dolly zoom, the camera walks room by room, each room arrives as a reveal from line drawing to render, a title block and lens readout frame the page, and a second reviewer scores a screenshot of every room. Plan Reveal keeps those ideas, and adds:

- The drawing is the real model and the real drawing set (same cut, same poché and dimensions as `drawings.pdf`), not a separate illustration.
- The reveal is spatial. A room turns to colour when the camera walks into it, sweeping from that doorway, while rooms ahead stay drawings. It is not a screen-space wipe.
- The walk is computed from the plan, through real openings with clearance. The page can be published for any FloorForge home, including your own custom plans.
- Floor changes, room files with measured facts, a closing colour plan and an offline single-folder page.
- Both samples were reviewed frame by frame, including by a second, independent reviewer that scored every screenshot, and the problems found were fixed. These included an arrival blocked by a gate pier, kitchen counters across a cased opening, a window behind wall cabinets, a bedroom with no wall for its bed, an over-close court view, both floors' annotations printed on one sheet, and a sweep accent caught on a cabinet back.

## Limits

- The page needs WebGL 2. On software rendering (no GPU) it works but is slow.
- The look is the realtime viewer's. Materials are procedural (no downloaded PBR scans), and there is no path tracing.
- The route and the views are computed. A home with unusual rooms may need `--order` to pick better stops.
- Like every FloorForge output, this is a design-communication aid for review with a competent local professional, not construction documentation.
