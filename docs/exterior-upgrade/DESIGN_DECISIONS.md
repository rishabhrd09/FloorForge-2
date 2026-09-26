# Design decisions

## One shared model boundary

The exterior system runs after layout/opening derivation and before validation, documents, scene, drawings and exports. This keeps the porch, balcony, landscape, opening changes and review status consistent across the live custom WebGL viewer and non-visual artifacts.

## Explicit change policy

`finish_only` preserves openings and emits no new exterior proposal. `exterior_refinement` is the default for a new project and may widen room-aware feature openings while retaining room/stair geometry. `spatial_redesign` is accepted by the schema for future topology work but is not used by this bounded generator; no spatial redesign is silently performed.

## Interior protection

The protected fingerprint covers room ids, floor, kind, polygon, clear polygon, stairs and floor levels. Any mismatch aborts the exterior revision. Exterior materials and interior palette materials are separate registries.

## Anchors and fit

Facade anchors derive from external wall segments, existing openings and access keepouts. Candidate assemblies and landscape polygons must fit inside the supplied plot. These are preliminary geometry checks, not structural, accessibility or regulatory approvals.

## Legacy migration

Projects without `floorforge.project/0.3` and without an explicit exterior theme resolve to `current`. The studio writes `floorforge.project/0.3` with an explicit theme, so the upgrade is opt-in for saved legacy files and explicit for new generations.

## Modern Tropical

Modern Tropical is a separate candidate path (`modern_exterior.py`). It uses the same anchors, change policy and interior fingerprint as the other families.

**Openings.** Each change is fitted between neighbouring openings, recorded on the shared openings as a before/after refinement, and never taller than its host wall.

- Living, family and dining glazing becomes full-height glass: sill 0, up to 2.7 m high and 5.6 m wide.
- Bedrooms get tall windows from a 450 mm sill.
- Kitchens get worktop-height glazing.
- Bathrooms get high privacy windows.
- Balcony doors widen.
- Every family draws its windows with one slim aluminium system (staggered sliding panes, slim sills, etched glass in wet rooms). Facade bedroom windows sit in slim projecting pods lined with timber; the older families shade living-room windows with a slim eyebrow.

**Assemblies.**
- The portico is a cantilevered slab. On G+1 plans the balcony soffit takes that role.
- The balcony is a frameless-glass slab across the widest upper-floor frontage, level with the floor it opens from. It has a timber deck, a slim handrail cap on the glass, a pergola of timber louvres with downlights, and seating between planted corners. The other families use the same terrace build in their own slab, handrail and pergola finishes.
- The roof reads as a floating slab with an overhang and upstand, deepened to 1 m along the street front with a timber-slat soffit and downlights (the eave stops at terrace openings and at a single-storey porch canopy, which keep their own edges).
- The entrance is an L-shaped porch. The flight covers the door end of the landing (the door width plus 300 mm either side) and returns down the side facing the wider yard, where the drive goes; the other end becomes a sit-out (at least 900 mm) with a bench, a planter and a stone-clad column under the canopy. Every tread has a nosing over an LED strip. The entry opening is refined to a tall pivot door whose head lines up with the full-height glazing, in a black steel portal.
- Two-storey plans raise the top-floor stair into a stone-clad tower 2.7 m above the roof: the headroom over the roof access that real homes have, and their usual vertical accent. Its clad faces are the ones that continue the facade; its door opens onto the roof terrace. The other designed families use the same tower.
- The roof beside the tower is an open terrace (pavers, frameless glass balustrade, loungers, planted pots); a solar rack over the rear of the roof tilts toward the midday sun. Single-storey roofs are gravel with the same rack.
- A carport is added only when parking is requested and the front setback is at least 5.5 m.
- A glass-roof pergola is added only when the rear setback is at least 2.6 m.

**Frontage.** A built compound wall is not a centred gate with equal walls either side, so every designed family uses `frontage.py`:
- a pedestrian gate (1.1 m) on the front door's axis, shown open (the walk enters here, then up the steps and in at the door);
- a separate sliding vehicle gate (3.6 m with parking, 3.0 m, or 2.4 m for two-wheelers on a shallow yard) over the widest stretch of front yard left clear by the entrance, or centred on the carport; none where no 2.4 m stretch is clear (a deep verandah across a small plot);
- a stone-clad pier beside the pedestrian gate with the house number, letterbox and gate light, and on the modern family a slim steel canopy over the gate;
- a cobble driveway behind the vehicle gate and a path of large two-tone slabs from the pedestrian gate to the steps (turning once when the gate cannot sit on the steps' line).
The boundary record keeps `gate_center_mm`/`gate_width_mm` as the arrival gateway and adds `gates` and `letterbox_pier`; the site plan draws both gates, the swing and the track.

**Landscape.** The landscape is built with Shapely inside the plot polygon, minus the house footprint and clearances:
- driveway, entrance path, front beds, drip strip, side passages, stepping stones, rear patio, hedge and lawns;
- side passages at least 820 mm wide are paved in large two-tone slabs with a pebble drip strip against the house, and the side boundary walls are clad in horizontal timber boards (after the side-garden renovation reference); tall pots stand only where a passage is at least 1.2 m wide, so the walk can pass them;
- plants, lanterns and planters are placed as points, and are rejected on hardscape;
- every polygon and stone must lie inside the plot and off the house (see `tests/test_realism.py`).

**Planting.** The scene publishes plants as `vegetation` items (species, position, scale, rotation), grown by the viewer. Simple `plant-proxy` meshes keep the GLB and drawings coordinated. Every family publishes planting or lawns.

