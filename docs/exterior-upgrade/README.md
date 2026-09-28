# Exterior architecture upgrade

This slice turns the exterior design brief into a versioned, deterministic geometry layer shared by the live studio, drawings, GLB and review/export manifests.

The default new-project path is:

`web/app.js` → `POST /api/generate` → `pipeline.run()` → `apply_exterior_preferences()` → `make_scene()` / `make_sheets()` / exports.

There are four selectable exterior families: Modern Tropical (the default for new projects), Warm Modern Minimal, Tropical Verandah, and Earth & Terracotta. Interior palettes (Bright Natural by default, plus Warm Contemporary, Quiet Minimal and Earthy Modern Indian) are independent and preserve the protected room/stair/furniture geometry contract. Existing projects without `floorforge.project/0.3` remain on the current exterior and interior until the owner opts in.

Modern Tropical includes:

- white rendered volumes with slim black full-height glazing;
- a cantilevered portico and a frameless glass balcony under a floating roof slab;
- a stamped-cobble arrival court, with pebble beds edged in steel;
- stepping stones and lawns;
- layered planting: frangipani, columnar conifers, spiral topiary, strelitzia and hedges;
- cube lanterns and geometric planters;
- where the plot allows, a carport and a glass-roof pergola with encaustic tiles and outdoor dining.

The realistic viewer grows its plants procedurally and walks the result in first person; see `docs/RENDERING.md`.

See:

- `SOURCE_MAP.json` for the implemented source boundary.
- `BASELINE.md` for the preserved geometry and existing limitations.
- `DESIGN_DECISIONS.md` for the contracts and change policy.
- `ACCEPTANCE.md` for the runnable checks and known scope boundaries.
