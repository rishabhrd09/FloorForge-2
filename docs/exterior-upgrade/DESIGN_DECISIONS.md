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
