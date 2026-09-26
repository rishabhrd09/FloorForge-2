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

**Assemblies.**
- The portico is a cantilevered slab. On G+1 plans the balcony soffit takes that role.
- The balcony is a frameless-glass slab across the widest upper-floor frontage.
- The roof reads as a floating slab with an overhang and upstand.
- A carport is added only when parking is requested and the front setback is at least 5.5 m.
- A glass-roof pergola is added only when the rear setback is at least 2.6 m.

**Landscape.** The landscape is built with Shapely inside the plot polygon, minus the house footprint and clearances:
- arrival court, front beds, drip strip, side passages, stepping stones, rear patio, hedge and lawns;
- plants, lanterns and planters are placed as points, and are rejected on hardscape;
- every polygon and stone must lie inside the plot and off the house (see `tests/test_realism.py`).

**Planting.** The scene publishes plants as `vegetation` items (species, position, scale, rotation), grown by the viewer. Simple `plant-proxy` meshes keep the GLB and drawings coordinated. Every family publishes planting or lawns.

