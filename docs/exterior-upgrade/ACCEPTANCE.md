# Acceptance record

## Automated checks

The focused exterior suite (`tests/test_exterior.py`) covers:

- legacy migration;
- every exterior family;
- plot containment;
- protected interior fingerprints;
- shared opening change records;
- scene roles and drawings;
- independent interior palettes.

`tests/test_realism.py` adds checks for the Modern Tropical default:

- full-height living glazing within wall height;
- landscape, stepping stones, planting and lawns inside the plot and off the house, for every fixture plot;
- coordination proxies for plants;
- room and walk metadata, and the stair treads that make the stair climbable;
- physically based material kinds;
- furniture containment;
- walls that tile each storey without overlapping solids;
- offline-preview script integrity, and the bundled viewer's presence and licence comments.

Current result: see `docs/VERIFICATION.md` for the latest full-suite count, which includes the loopback server checks.

The full Python suite is the release gate for this slice. Run:

```bash
.venv/bin/pytest -q
```

The 40 × 60 ft G+1 path publishes the exterior families through the real `/api/generate` pipeline and verifies GLB re-import node counts. `scripts/capture_studio.mjs` also generates the 30 × 40 ft preset through the studio UI and checks it arrives as Modern Tropical.

## Deliberate boundaries

This is preliminary architectural geometry. It does not claim any of the following:

- structural sizing, cladding anchorage or drainage design;
- glass balustrade engineering;
- accessibility certification or municipal compliance;
- path-traced or photographic rendering;
- independent IFC viewer acceptance;
- professional construction approval. The existing compact/small programme limitations remain visible instead of being hidden by the exterior layer.
