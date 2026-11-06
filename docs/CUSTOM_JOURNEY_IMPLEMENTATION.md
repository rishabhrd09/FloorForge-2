# MyVerandah custom-home journey

Implementation branch: `codex/myverandah-custom-journey`, based on clean
`development` commit `8396097`. No deployment or main-branch merge is part of
this work. Existing planning documents are preserved.

## Baseline audit

| Path | Working before this change | Restriction or missing behavior |
| --- | --- | --- |
| Input / `intent.py`, `home-design.js` | Deterministic brief parser, source priority, input audit | Starting-input selection partly changed navigation; contradictory inputs could be resolved by priority rather than a question |
| Compass | Five grids, 28 room types with capability metadata, both half-cell axes, stable room IDs, Undo/Redo, autosave, keyboard painting | Preparation enlarged rooms only into unused space; empty upper floors could be trimmed |
| Geometry / `custom_plan.py` | Measured clear polygons, wall allowances, hosted openings, stair links, slab holes, open-sky/support checks | No unified approval identity independent of appearance |
| Fitting / `smart_fit.py`, `plan_search.py` | Constrained fit and bounded alternative layouts | Broad search restricted to a ground-floor rectangular programme; no occupied-cell ownership solver |
| Import / `plan_import.py` | Strict layered ASCII DXF with explicit units and exact rectangular rooms | One floor per file; no generic CAD recognition, intake inventory or calibrated image worksheet |
| 2D / `drawings.py` | Dimensioned SVG, PDF, DXF from compiled geometry | The published drawing DAG depended on presentation meshes; no per-floor approval |
| 3D / `scene.py`, `viewer.js` | Offline Three.js, measured furniture, collision, openings/stairs/voids, GLB, optional Cycles scripts | No backend 2D approval gate or final-render job UI |
| Save/reopen | Portable project JSON, inactive drafts, scene hashes | References could retain names only; no durable source answers, geometry certificates or cancellation publication guard |

`evidence/custom-journey/baseline.json` fingerprints 1,700 existing files in
examples, output, assets, planning documents, and gallery/viewer entrypoints.
All 1,700 remain byte-identical. A second comparison covers 1,197 archived
evidence files against the clean starting commit, resolving 302 Git LFS pointer
hashes to their original content SHA-256 values; all are unchanged. See
`preservation-result.json` and `archived-evidence-preservation.json` in the same
evidence directory.
The original full test run had 823 passes, 11 loopback sandbox failures/errors,
and one existing electrical sample viewer equality failure. See the original
log; do not overwrite the sample to make that assertion pass.

## Architecture

The new journey is an orchestration layer around the existing geometry kernel.
It does not introduce a second room generator or replace the sample system.

1. `design_journey.resolve_sources` retains source identities and original
   content, normalizes units, honors activation, merges compatible values and
   disjoint floor layouts, and asks about conflicting measurements or ownership.
   Answers identify the question and candidate values, so edited inputs cannot
   reuse an obsolete answer. Requirements have explicit consumption statuses.
2. The existing Compass adapter or exact/automatic compiler produces measured
   geometry. `myverandah.geometry/1` records stable identities, millimetres,
   tolerances, walls/openings, floors/plates/roofs, stairs, voids and relationships.
   The canonical geometry identity excludes material/lighting/title revisions.
3. `JourneyService` publishes immutable plan-only SVG/PDF/DXF, canonical JSON
   and checksums before any scene is constructed. Signed per-floor approvals
   and whole-home confirmation refer to those measured hashes. A local key is
   stored outside portable projects. Moving to another studio requires review
   there; no project-carried secret is trusted.
4. `pipeline.run` revalidates the certificate and uses the approved building as
   the adapter input. A canonical equality assertion prevents an appearance
   adapter from changing architecture. Existing scene, furniture, collision,
   drawing and export code continues to consume that shared building. The
   approved canonical model and certificate accompany the portable export.
5. `compass_repair` uses a graph of allocations and a bounded HiGHS integer
   ownership model. Connected shape candidates, minimum dimensions, aligned
   stair constraints and exact-cover ownership prune the search. Every returned
   option passes the existing complete compiler. Changes are proposals requiring
   explicit application; pins and floor/room identity remain protected.
6. Jobs snapshot requests, track request ordering, cancel cooperatively at DAG
   boundaries, and guard the latest-build publication. Older preflights and
   workers cannot replace a newer edit. The client also discards stale results.
7. `journey_render` invokes the existing Cycles script against an immutable
   approved GLB/scene pair. It reports queued/running/completed/error/cancelled
   separately from the interactive preview and binds the still to geometryHash.

Existing exact-plan, fitting, room-board, guide and optional AI endpoints also
resolve the selected sources before calling their legacy algorithms. Invalid
geometry stays editable; real source conflicts still require a decision. Returned
proposals retain the portable source/answer state and cannot remove requested
rooms/floors or alter pins. Applying a geometry proposal clears its approvals.
Damaged generated 2D publications are quarantined and rebuilt on retry.

The browser coordinates existing editors with nine explicit stages. It shows
one question with preview/apply/undo, all requested floor plans, whole-home
confirmation, three compatible appearance recipes, then 3D and export.
“Use this appearance” selects a whitelisted finish recipe. “Start from a copy
of this layout” retains the existing explicit sample-copy action.
Every custom preset uses the same construction recipe; selected palettes are
material-record overlays. Tests compare every node, mesh, collider, opening,
furniture item, light, plant and camera across all three presets. Small kitchen,
upholstery and wall-finish modules also change only materials. Their catalogue
reports actual room envelopes before generation and generated component
footprints afterward. Scene cache identity includes appearanceHash so changing
a module cannot accidentally return an earlier material selection.

## Import and persistence contract

Images remain references unless the user supplies a known dimension, confirms
the scale and manually traces room outlines. The worksheet measures pixels
through that calibration; it performs no OCR or automatic room recognition.
Original PNG/JPEG/WebP bytes, SHA-256, MIME, calibration and floor mapping travel
inside the project. The backend checks content, hashes and bounded image size.
Tracing preserves the requested floor count and stable floor order; untraced
floors remain editable placeholders requiring review rather than disappearing.
Legacy filename-only references remain recoverable metadata, not available
image content. Projects accept up to 8 MB of embedded image bytes.

DXF intake inventories units, layers and entity types. Supported rectangles and
opening spans still use the existing exact importer. Unitless drawings need an
explicit unit choice; minimum FF_PLOT X/Y maps to the local origin. One file maps
to an explicit physical floor index with a stable ID. Independently imported
floors merge in physical order regardless of upload order; empty placeholders
retain missing requested levels. Same-level conflicts require a source choice.
Original manual layouts and stair relationships stay recorded when a drawing
is imported. Stairs and cross-floor connections still require review/editing.
DWG, PDF, arbitrary line art, blocks and splines are not automatic imports.

All original inputs, both split axes, reference bytes, selected sources,
answers, presets and approval records are retained. Geometry edits conservatively
invalidate dependent floors; a whole-home certificate also protects cross-floor
relationships. Finishes retain geometry approval. The original draft is preserved
when no validated solution is found.

## Dependency decisions (official sources checked 2026-11-05)

No new runtime dependency or external asset was installed. Existing exact pins
remain in `requirements.lock.txt`, `requirements-dev.lock.txt` and the viewer
lockfile. The table distinguishes architectural evaluation from measured local
performance; none of these sources establishes the speed of this application.

| Candidate | Compatibility, deployment and licensing | Decision |
| --- | --- | --- |
| Shapely 2.1.2 / GEOS | Existing polygon kernel. Spatial indexing and prepared predicates suit repeated validation. Shapely BSD-3-Clause; GEOS LGPL-2.1 requires appropriate native-distribution notices. [Official documentation](https://shapely.readthedocs.io/en/stable/manual.html), [licensing](https://shapely.readthedocs.io/en/stable/index.html) | Reuse; no polygon rewrite |
| NetworkX 3.6.1 | Existing pure-Python graph dependency; adequate for residential room graphs. BSD-3-Clause. [Graph APIs](https://networkx.org/documentation/stable/reference/algorithms/shortest_paths.html), [licence](https://github.com/networkx/networkx/blob/main/LICENSE.txt) | Reuse for allocation adjacency and connectivity |
| SciPy 1.17.0 / HiGHS | Existing native dependency with MILP time/node limits and explicit solver statuses. No per-request API bill; CPU/RAM and wheel size remain deployment costs. SciPy permits commercial use under BSD. [MILP API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html), [licence FAQ](https://scipy.org/faq/) | Reuse bounded ownership optimisation; validate every candidate independently |
| OR-Tools CP-SAT | Integer-domain model supports discrete ownership/topology choices and clearly distinguishes UNKNOWN, FEASIBLE and INFEASIBLE. Apache-2.0. A second native solver adds deployment and maintenance burden. [Solver docs](https://developers.google.com/optimization/cp/cp_solver), [licence](https://github.com/google/or-tools/blob/stable/LICENSE) | Evaluated, not installed: current bounded exact-cover problem already fits HiGHS. Benchmark before adding topology-heavy CP-SAT |
| Existing Three.js viewer | Bundled offline viewer, exact pinned packages, procedural materials/plants; [MIT licence](https://github.com/mrdoob/three.js/blob/dev/LICENSE) and existing notices retained in `licenses/`. No CDN cost or external image transfer | Reuse unchanged bundle; preserve sample behavior |
| Blender / Cycles | Optional local executable; CPU final renders take substantially longer than preview. Blender GPL and bpy-script redistribution conditions need attention if bundling an installer; rendered output is separate from program licensing. [Official licence](https://www.blender.org/about/license/), [FAQ](https://www.blender.org/support/faq/) | Optional process adapter, not a required core runtime; no binary bundled |
| Poly Haven | CC0 asset library supports commercial output; website/API terms are separate from asset licensing. [Asset licence](https://polyhaven.com/license), [API terms](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md) | Evaluated only. No asset downloaded/copied; procedural assets avoid provenance and offline-payload costs |

Search is bounded, not exhaustive. A time limit or empty local candidate set is
not a proof of architectural infeasibility. An optimal result from a small
candidate MILP is not global optimality of a home design.

## Deployment and remaining scope

The server is still loopback-only with Host/Origin/session-token checks. It is
not ready to expose directly as a multi-tenant internet service. Startup work
would add authenticated project storage, tenant-separated job queues, worker
quotas, render process isolation, durable job recovery, backups, observability
without project/credential logging, and a distribution licence review. No
external request is needed for this core journey; existing optional AI still
requires its separate explicit consent and validates proposed changes.

The geometry checks are preliminary screens for access, spans, daylight,
stairs/headroom and coordinated floor envelopes. They do not establish a
structural load path, municipal compliance, services design or construction
approval. Repair explores a bounded family of cell shapes, not arbitrary
architectural topologies. Exact pinned geometry may need manual adjustments.
The three presets reuse existing components; a full manufactured-component
catalogue and unrestricted kitchen/facade configurator are outside this change.
Final Cycles stills use the base exported model materials; presentation GLB
export remains available for higher-detail manual rendering.
The renderer now supports Blender 4.x Nishita and Blender 5.x Single Scattering
sky names without changing the intended sky model, following the
[official Blender 5 release notes](https://developer.blender.org/docs/release_notes/5.0/rendering/).

## Verification and artifacts

The complete local Python run reports **1,040 passed and one pre-existing
failure**, `test_tour_page_loads_its_data_offline`: the electrical sample retains
its archived viewer, which differs from the current root viewer. Both files and
their original hashes were preserved. The initial baseline had the same
assertion failure. The final focused run reports **138 passed**, including the last wall-thickness
clarification correction made after the full run began. Its result is recorded
in `evidence/custom-journey/final-journey-tests.log`. No new regression remains.

The main real-browser journey passes 20 checks covering three-floor upload,
plan-only publication, each signed floor approval, whole-home confirmation,
style/module approval reuse, matching 3D, reference-byte portability, mobile
review, stale responses and conflicting-source preview/apply/undo. The final
local measurements were 0.302 seconds for preparation and 11.759 seconds for
generating and loading 3D with software WebGL; these are fixture-specific.
A separate import browser run passes 15 checks for DXF units/layers, physical
first-floor mapping, original bytes, unsupported PDF recovery, individual
drawing activation, calibrated manual tracing and exact measured coordinates.
Importing over a manual plan retains its original authority, untouched upper
floors and stair relationships, and asks which ground-floor layout to use. The
sample-gallery regression run passes 10 checks, including its 16 ready samples,
copy/adopt, previous-work recovery, reload, floor browsing and mobile layout.
A focused input browser run passes 32 checks: actual plot/survey/text controls
change canonical geometry, excluded sources stay excluded, unresolved drafts
reopen, all five grid controls work, the 28-type catalogue remains visible,
keyboard and touch place rooms, both split axes survive Undo/Redo and reach
measured polygons, and fully occupied ground-plus-first maps compile on every
grid with stable floor ownership. The exact checks and screenshots are in
`evidence/custom-journey/`, with gallery results isolated in its `gallery/`
subdirectory. These are scripted exercises;
a trial with a real novice remains pending.

Occupied G+1 repair benchmarks span all five grids and both split directions:
10 cases, 0.650–0.925 seconds cold, three validated alternatives each. Solver
search limits, infeasible local candidates and cache behavior have separate
tests. The frontend state harness checks 100 metamorphic appearance, source,
answer and pin cases. Numeric/topological integration checks compare room IDs,
polygons, walls, opening spans, door collision gaps, slab/void projections,
furniture containment, PDF text, DXF dimensions and every GLB node transform and
asset vertex. Live HTTP tests verify the approval gate, origin/token checks,
cancellation and portable-project reopening.

`evidence/custom-journey/artifacts/` contains a reproducible three-floor drawing
set, floor SVGs, DXF, GLB, scene/canonical JSON, original portable project,
geometry approvals, export ZIP and a completed local Cycles still. The 16-page
PDF was rendered with Poppler: all three floor plans and the complete page
overview were visually inspected for layout/clipping. It remains a preliminary
study rather than a complete residential programme or a construction package.

Reproduce without changing samples:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_custom_preservation.py
node tests/design_journey_state.cjs
PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node scripts/check_custom_journey.mjs
PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node scripts/check_custom_imports.mjs
PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node scripts/check_custom_inputs.mjs
.venv/bin/python scripts/verify_custom_journey.py --render
```

Omit `--render` when Blender is unavailable. Python dependencies remain pinned;
browser CI pins Playwright 1.62.1 and uses Node 22. CI now fetches LFS artifacts
and has browser jobs for Linux, Windows and macOS in addition to the existing
Python matrix. Remote CI runs have not been triggered or claimed as passing.

Automated browser usability exercises are evidence of working controls, not a
human novice trial. A short trial with a real novice must be recorded before
making ease-of-use or completion-rate claims. Cross-platform CI is configured;
local macOS results are not evidence of Windows/Linux runner success.
At the user's request, the human novice trial is recorded as pending; no human
completion-rate or ease-of-use claim is made.

## Portfolio description

MyVerandah turns mixed homeowner inputs into a reviewable, measured design using
an offline geometry kernel. Its central engineering decision is to separate
source interpretation, geometry identity and appearance identity. A bounded
graph-and-integer repair service suggests changes without silently rewriting
the homeowner’s room ownership, while signed 2D approvals gate presentation
generation. The same approved building drives drawings, interactive scenes,
collision and portable exports. Sample preservation manifests and stale-job
tests make an evolving prototype safer to extend toward a hosted product.


## Follow-up: existing server served an incompatible page

On 2026-11-05, the reported **Create my custom design → Not found** failure was
traced to the existing studio on port 57594. Its Python process had been running
since November 3. It served current frontend files from disk while retaining
its older route table: `/api/design/inputs` returned 404, and the new journey
JavaScript/CSS paths were unavailable. Its session response misleadingly
reported the current disk hash. Earlier end-to-end tests started fresh servers
and therefore missed this upgrade scenario.

The server now reports the code identity captured when its module loaded,
separate from the current disk identity, and an explicit journey API version.
Changed code blocks new design writes with restart guidance, while cancellation
and credential clearing remain available. Starting on an occupied port no
longer silently reuses an incompatible studio. The UI checks compatibility
before creating a project, explains missing assets, and retains failed setup
inputs across reload in tab session storage. A restart followed by a page reload
is necessary when the old process never served the new JavaScript module.

The actual studio was restarted on the same port with the same
`~/.floorforge` directory. All **1,087 existing output files** remain unchanged;
no file was added during the live create-button check. The reported 40 × 60 ft,
west-facing, ground + first + second setup was also entered through the live UI,
and **Create my custom design** opened Compass successfully.

`scripts/check_custom_launch.mjs` runs the actual baseline server module against
current web assets, reproduces the 404 and missing script, restarts at the same
origin, reloads, creates the exact requested setup, and checks save/reopen.
Its **17 browser checks** pass. The complete 20-check approval/3D/export browser
journey was rerun, alongside 76 server/security/journey tests. Evidence is in
`evidence/custom-journey/launch-fix/`. The browser CI job now includes this
upgrade test and fetches the baseline history it needs. The human trial and
remote CI remain pending; these automated checks do not change those statuses.
