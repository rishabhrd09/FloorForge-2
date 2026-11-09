# Plan Reveal samples: frame review

The two walkthrough samples were captured frame by frame at 1440×900 with headless Chromium on software WebGL (SwiftShader). An independent reviewer that had not seen the code then scored every screenshot from 1 to 10. Its rubric: 10 is premium architecture-studio portfolio quality, 8 is good, 5 is mediocre and 3 is broken. Each review was followed by fixes. `aangan-house-walkthrough.png` and `long-house-walkthrough.png` are contact sheets of the final captures. `checks.json` and the other screenshots come from `scripts/check_plan_reveal.mjs`, which runs the walkthroughs inside the studio.

| Review | Aangan House | Long House | Notes |
| --- | --- | --- | --- |
| First | 5.5 | 4.7 | The paper states scored best. Room views lost the most. |
| Second, after the first fixes | 5.7 | 5.3 | Opening and end sheets about 7. Colour plan about 7. Rooms about 4.5. |

The second review used frames from before the last round of changes below, so it did not score that round.

## Found and fixed

- The upper floor's annotations, north point and grid printed over the ground-floor sheet. Each storey is now annotated on its own.
- The opening sheet and end card overlapped the title block and lens readout. The plan is now fitted into the space they leave free.
- The lift's final framing cut off the front garden. It now projects the plot's corners to fit the whole plot.
- Drawn lines ran past the sheet border. They now stop at it.
- The arrival was framed against a gate pier. It now stands back across the pavement on the entrance axis.
- Kitchen counters ran across a cased opening, and a window sat behind wall cabinets. Both sample plans were corrected.
- A bedroom had an opening in every wall, so no bed could be placed. Its outer wall is now solid.
- A court view was taken 1 m from the tree trunk. Small courts are now framed through their opened sliding door.
- The sweep accent caught surfaces lying on a mask edge, such as a cabinet back. Still edges are now snapped.
- The colour plan was small, sat among neighbours' roofs, and had flat light. It is now framed on the plot. The neighbours sink away, the surroundings fold into paper, the plan light is high with short shadows, and walls are drawn with poché. Trees stay whole.
- The overlay was hard to read over 3D. It now sits on paper chips with a crisp room card. The room ruler shows only during the walk, and the height readout is measured from the floor.
- Interiors were hazy and their verticals converged. Rooms are now metered darker with less bloom. Each stop settles to about 1.35 m and holds level, with a lens shift instead of a tilt.

## Known limits (shared assets, not changed here)

The bedspread and leaf-material glitches, repeated wall art, and the default kitchen's fittings (vessel sink, no hood) come from the shared scene generator and viewer. Every sample uses those, so they were left unchanged here. Within the samples themselves, a later pass replaced the low-poly frangipani with the viewer's mango (Aangan) and ashoka (Long House) builders. It also moved the Long House to the L-shaped modular kitchen, with an inset sink, a tap and handled cabinets, and stopped a tulsi vrindavan cutting into a small court's planter.
