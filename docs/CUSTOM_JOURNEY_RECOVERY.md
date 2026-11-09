# Custom journey recovery verification — 6 November 2026

## Branch and preservation

The local `development` and fetched `origin/development` both started at
`839609731077e9623ce819cdfd80b1152a8a0956`; neither was ahead of the other.
The 99 existing changed/new files were backed up with SHA-256 hashes, a binary
patch and a tar archive before switching branches. All earlier implementation
was committed as `7d17668` on `codex/myverandah-custom-journey`; local
`development` was then fast-forwarded to that checkpoint. The original feature
branch still points to the checkpoint. These recovery fixes are a subsequent
local development commit. Nothing was pushed, deployed or merged to `main`.
The latest fetched remote development remains `8396097`; local `main` and
`origin/main` remain `f3b5c98`.

The original preservation manifests still pass: **1,700 sample, asset, output
and planning files plus 1,197 archived evidence files** are unchanged. The live
studio check also preserved all **1,087 files in `~/.floorforge`**, adding none.
The backup of pre-switch files remains in the temporary directory recorded in
`evidence/custom-journey/recovery/summary.json`; the Git checkpoint is the durable
recovery reference.

## Reproduced causes and fixes

The original “Create my custom design → Not found” failure came from an older
Python process serving newer page assets. The existing loaded-revision and API
compatibility safeguards were retained and tested again against the actual old
server module. The fixed studio was started at its previous origin,
`http://127.0.0.1:57594`, with its existing output directory. A fresh in-app
browser entered 40 × 60 ft, West, Ground + First + Second and opened Compass.
The running backend and disk identities match; no restart is pending. An older
open tab should be reloaded to receive the current JavaScript.

The new recovery suite also reproduces the pre-fix behavior at `7d17668`:
Edit description left Apply disabled instead of opening the text field;
an unplaced first-floor bedroom opened Ground with no selected room. The
baseline evidence is retained in `recovery/baseline/`.

The corrections extend the existing editors and compiler:

- Diagnostic context now retains the correct editor, stable floor/room IDs,
  physical floor index, room names, current/minimum sizes and next steps.
  Invalid plot fields point to their actual controls. Missing requested floors
  are explained before dependent stair errors. Malformed input records retain
  the original validation message instead of failing in diagnostic formatting.
- Edit actions open their actual text, plot, survey, reference, exact-plan or
  Compass editor. Compass rerenders the selected floor and room. The visible
  issue banner includes **Recheck my changes** and **Back to the question**.
  Editing a room-goal question enables its real survey consumer. Scope and
  dimension-lock actions reveal the relevant controls.
- Legacy Compass drafts receive missing optional metadata without rewriting
  room IDs, allocations, split axes or geometry. Exact-plan issue miniatures
  use the actual floor polygons, even when an older Compass draft is retained.
- Unavailable automatic recommendations no longer repeat an unchanged search.
  Exact plans no longer offer unsupported partial-scope controls. Existing
  bounded, validated Compass alternatives still require preview and Apply;
  Undo restores their original allocations.
- A signed unchanged floor review can be reused after an independent edit to
  another floor. Its dependency-aware hash includes coordinated stairs,
  support envelopes, voids and pinned requirements. Changed floors require
  fresh approval, and the changed whole home requires explicit confirmation.
- Preparation returns the current studio's signature-verified approvals and
  confirmation. The UI uses this authoritative set. Foreign, forged or stale
  portable certificates no longer disable the controls needed to reapprove.
  No approval is granted automatically and the generation gate remains enforced.

## Validation and scope

The full Python run completed with **1,079 passed, one failed in 433.99 s**.
The remaining failure is
`tests/test_electrical_tour.py::test_tour_page_loads_its_data_offline`: an archived
sample viewer is not byte-identical to the current web viewer. This same
assertion already failed in `evidence/custom-journey/baseline-tests.log` before
custom-journey implementation. Both protected files remain unchanged; the test
was not weakened or the sample overwritten. See `recovery/pytest.log` and
`recovery/pytest.xml` for the complete fresh result.

The full suite includes geometry/topology and numeric agreement between
approved 2D, scene meshes, collision openings, furniture footprints, slabs,
PDF/DXF dimensions and GLB transforms; stale preparation/jobs, cancellation,
source conflicts, imports, pin/scope constraints and portable persistence.
New diagnostics and reapproval tests cover the recovery cases above. The Node
harness also verifies 100 appearance/geometry/source/pin/answer transformations,
all editor actions and floors, legacy metadata, actual geometry illustrations,
and the preparation response's authoritative approval state.

The independently rerun browser suites pass: 20 approval/3D/persistence checks,
32 selected-input/Compass checks, 15 import/tracing checks and 17 old-server
recovery checks. They include all five grids, both split directions, keyboard
and touch entry, fully occupied ground+first maps, conflicting sources and
style-only approval retention. Their separate logs and screenshots are under
`recovery/journey/`, `inputs/`, `imports/` and `launch/`.

The additional guided-recovery browser suite passes **46/46 checks with zero
errors**, bringing the fresh browser total to **130 checks**. Its measured
three-floor generation took **5.232 s**, with 1,132 scene nodes and exactly the
approved geometry hash. The detailed results and timings are recorded in `recovery/verified/checks.json` and the consolidated `recovery/summary.json`.
The scenarios make actual editor changes and recompile: ambiguous units,
invalid setbacks, missing rooms on upper floors, empty Second floor, missing
exact-plan stair links, full-grid repair/Apply/Undo, locked-dimension release,
and the West-facing three-floor journey. The latter edits and reapproves First
while retaining Ground/Second reviews, confirms the whole home, changes
appearance, generates matching 3D, downloads the real Save project file,
uploads it, reloads, and reapproves it in a second studio with a different key.
Test-authored allocation fixtures are used for reproducibility; this is not a
human designing an entire home from an empty grid.

Cross-platform CI is configured to run these browser and Node recovery checks
on Linux, Windows and macOS, alongside the Python matrix. Remote CI has not
been run. The human novice trial remains **pending at the user's request**.
Automated browser success is not a measured human ease-of-use result.

The solver remains bounded; some incompatible or pinned layouts still require
an explicit user edit. The app preserves these drafts and explains the next
required change rather than promising a solution or silently removing floors.
Unsupported CAD formats still need supported DXF conversion or calibrated
manual tracing. Designs remain preliminary and require professional review.

## Architecture and artifacts

The source resolver and geometry kernel remain authoritative. A read-only
diagnostic adapter adds precise editing context to existing validator output;
a frontend router opens the existing editors and feeds changed drafts back to
the same compiler. Immutable floor hashes govern reusable local reviews, while
a separate signed current-home confirmation gates presentation generation.
Appearance identity stays independent. No new runtime library was introduced.

`recovery/verified/generated/` contains the new PDF, DXF, canonical model, scene,
GLB, approval and export manifests; the portable project and screenshots are
beside it. The scene's geometry identity and floor count are checked against the
approved model. The new 16-page PDF's edited First-floor sheet was rasterized
and visually checked: the renamed bedroom, dimensions, stair, north arrow,
scale and notes are legible without overlap. Earlier complete PDF and optional
Cycles rendering evidence remains in `evidence/custom-journey/artifacts/`.
The browser image is an interactive preview, not a claimed photorealistic still.

To reproduce the new checks without overwriting earlier evidence:

```sh
.venv/bin/python -m pytest -q
node tests/design_journey_state.cjs
node tests/design_journey_recovery.cjs
PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node scripts/check_custom_recovery.mjs
.venv/bin/python scripts/check_custom_preservation.py
```

The four existing browser scripts also accept `MYVERANDAH_EVIDENCE_DIR` to keep
rerun artifacts separate from historical evidence.
