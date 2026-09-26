# Exterior architecture upgrade

This slice turns the exterior design brief into a versioned, deterministic geometry layer shared by the live studio, drawings, GLB and review/export manifests.

The default new-project path is:

`web/app.js` → `POST /api/generate` → `pipeline.run()` → `apply_exterior_preferences()` → `make_scene()` / `make_sheets()` / exports.

The three selectable exterior families are Warm Modern Minimal, Tropical Verandah, and Earth & Terracotta. Interior palettes are independent and preserve the protected room/stair/furniture geometry contract. Existing projects without `floorforge.project/0.3` remain on the current exterior until the owner opts in.

See:

- `SOURCE_MAP.json` for the implemented source boundary.
- `BASELINE.md` for the preserved geometry and existing limitations.
- `DESIGN_DECISIONS.md` for the contracts and change policy.
- `ACCEPTANCE.md` for the runnable checks and known scope boundaries.
