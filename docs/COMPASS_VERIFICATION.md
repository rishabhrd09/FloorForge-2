# Compass verification — 18 October 2026

This review originally covered the opt-in Compass preview on `development`, based on `ea198aba408f0c9c276bfadbdae83a2099a76d43`. Compass is now enabled by default for normal local launches at the user's request; `FLOORFORGE_COMPASS=0` explicitly disables it. The core input → reviewed Custom Plan → shared 2D/3D/export flow works. This is **not acceptance of every feature in the larger planning specification**. The historical results and remaining work below still apply.

## Results and preservation

- Full regression suite: **595 passed in 218.77 seconds**. Focused Compass suite: **46 passed**. Its Node subprocess includes 12 edit/state tests and 500 deterministic randomized edit attempts.
- Real browser checks used the isolated `FLOORFORGE_COMPASS=1` server on port 8766. The electrical sample server on port 8765 was retained.
- All **445 recorded sample/viewer files** match the pre-Compass baseline byte for byte. No existing `examples/`, viewer source, viewer bundle, or Plan Reveal file is included in the Compass change.
- The recorded plan hashes for `manual-L`, `demo`, `small` and `compact` remain unchanged.
- Two clean generations each of a legacy project and a three-floor Compass project produced equal build IDs and identical bytes for all **27 artifacts per case**. This proves local determinism with the installed dependencies; it does not claim cross-platform byte equivalence.
- The two original Compass planning documents match their safety copies. Their SHA-256 hashes are recorded in `evidence/compass/checks.json`.
- Accepted Compass inputs are recompiled and validated by the server. No browser-supplied derived polygon is accepted as a second geometry authority.

## Issues corrected during the audit

Shared-setting changes invalidate saved acceptance before collection or generation, so a pending map can be saved and reopened for review. Exact-editor return requires a fresh Compass review. Reopening uses the active Compass data ahead of a different retained inactive draft.

Moving an unplaced room now also clears its old floor relationships and entrance selection, with confirmation and atomic Undo. Whole-cell replacement confirms every displaced owner, including a room that owns both halves. Assigning a region to its existing owner is idempotent; Erase remains explicit. Room dimensions, route widths and relationships reject unsupported values before committing them in the UI.

A large bounding box cannot hide an entirely too-thin L-shaped room. Holes, disconnected shapes and wall-offset collapses remain blocking conflicts. Two touching open spaces cannot claim solid separation. The existing Custom Plan access, opening, daylight, support, open-sky and stair checks remain in the conversion path.

## Acceptance matrix

Numbers refer to the acceptance scenarios in `COMPASS_REFACTOR_PLAN.md`. “Verified” describes the stated evidence, not a blanket release certification.

| # | Result | Evidence / boundary |
| --- | --- | --- |
| 1 | Verified desktop core flow | Eight prefilled setup screens; L-shaped living, two bedrooms, bathroom half, explicit review and live generation. |
| 2 | Verified adapter; desktop NE UI | All eight bearings preserve authored polygons. Road/front stays below the map and proposed-plan preview. |
| 3 | Verified | L-room union and separate same-kind room IDs pass canonical geometry review. |
| 4 | Verified | Ownership, corner-only contact, bridge removal, replacement and cancellation covered by schema/state tests and browser checks. |
| 5 | Verified | Refine cancellation does not mutate input; division/assignment Undo and Redo; differing and same-owner replacement confirmation. |
| 6 | Verified partition contract | Density is independent of split cells; whole/half references must match the saved floor partition. |
| 7 | Verified | All-floor remap proposals retain IDs; collision/loss/disconnection blocks applying. Live 16→24 conflict and 16→32 review/cancel/Undo/Redo. |
| 8 | Verified core; further device QA pending | G+2 prefixes and real roof flights validated. Live three-floor navigation, below labels, floor reduction and upper-room restoration. |
| 9 | Verified | Shared grid lines, reserved wall thickness, clear/allocation labels, minimums, thin L shapes, holes and collapse rejection. |
| 10 | Partial, guarded | Supported room relationships and access requirements feed canonical geometry. Custom gates, second roads and site-band zones explicitly block conversion; they are not claimed as applied. |
| 11 | Verified | Required unplaced rooms and unreachable rooms block conversion; no automatic passage is inserted. |
| 12 | Partial | Foundation answers remain prefilled; map/text conflict and explicit Keep my map work. Full conditional survey bank and automatic programme expansion remain unimplemented. |
| 13 | Verified conversion; fitting unavailable | Conversion preserves regions and locks; stale proposal/acceptance guards are present. Automatic lock-aware fitting is unavailable. |
| 14 | Verified regression scope | Full existing suite passes; protected files and four legacy hashes match. Geometry, renderer and sample pipelines remain shared. |
| 15 | Partial | Live accepted and pending draft save/reload; inactive hash isolation; future project versions reject downgrade. A full newer-version read-only recovery UI and geometric legacy migration remain unimplemented. |
| 16 | Verified | Shared building/scene/report/review hashes and PDF/DXF/GLB/IFC exports; active edits mark views stale and block current-draft export. |
| 17 | Partial | Desktop keyboard movement, Enter/Escape, focus return and large refinement targets checked. Physical mobile devices and 200% browser zoom have not been accepted. |
| 18 | Verified shared pipeline; extended manual walk pending | Check operation does not load a scene; original exact editor validates the proposal. Viewer files remain identical and existing regression coverage passes. No new exhaustive manual walkthrough/stair usability session was performed. |
| 19 | Verified | One/two/three-floor prefix tests derive bedrooms/stairs/roof correctly and retain the full draft. Live upper draft archive/Undo preserves placements. |

## Remaining release work

Custom gate and second-road geometry, typed setback-band zones, external stairs/lifts, automatic lock-aware fitting, composite presets, automatic programme expansion, the full conditional survey, geometric migration and the newer-version recovery UI remain future work. Unsupported controls are disabled or return named conflicts. Notes and advisory plot context must not be interpreted as completed geometry requirements.

Physical mobile/zoom checks, accessibility review, novice usability sessions and post-push CI are separate acceptance work. Consult the workflow at the actual pushed commit for remote CI status; local results alone do not prove those jobs passed.

## Re-run

Run `.venv/bin/python -m pytest -q` with loopback socket access. Run `node --test tests/compass_state.cjs` directly to inspect edit/state cases. See `COMPASS_PREVIEW.md` for the preview launch command and `evidence/compass/` for recorded results and screenshots. Use `git diff ea198ab -- examples web/viewer web/viewer.js web/plan-reveal.js` to verify sample/renderer source isolation against this baseline.
