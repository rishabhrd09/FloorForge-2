# Acceptance record

## Automated checks

The focused exterior suite covers legacy migration, all three exterior families, plot containment, protected interior fingerprints, shared opening change records, scene roles, drawings and independent interior palettes.

Current result: `118 passed` in the full suite, including the six focused exterior tests and the loopback server checks.

The full Python suite is the release gate for this slice. Run:

```bash
.venv/bin/pytest -q
```

The 40 × 60 ft G+1 path also publishes all three exterior families through the real `/api/generate` pipeline and verifies GLB re-import node counts.

## Deliberate boundaries

This is preliminary architectural geometry. It does not claim structural sizing, cladding anchorage, drainage design, accessibility certification, municipal compliance, photoreal rendering, independent IFC viewer acceptance or professional construction approval. The existing compact/small programme limitations remain visible instead of being hidden by the exterior layer.
