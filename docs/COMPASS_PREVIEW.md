# Compass custom-home preview

Compass is an opt-in development workflow for designing a new custom home. It adds a separate versioned input and a reviewed adapter into Custom Plan. The existing Automatic, fixed 16-cell Quick Guide, room board, exact editor, saved projects, sample gallery and renderer remain available.

## Run locally

```sh
FLOORFORGE_COMPASS=1 .venv/bin/python -m floorforge serve --out /private/tmp/floorforge-compass-preview --port 8766 --no-browser
```

Open `http://127.0.0.1:8766/`, enter the workspace, then choose **Arrange on Compass map**. Without the environment flag the new entry point is hidden and generation from Compass is disabled. New-format draft readers remain available for recovery and downloading the saved project.

## Working flow

1. Complete or retain the eight prefilled setup answers. Dimensions use canonical integer millimetres; feet/inches and metres are supported. Road bearing changes geographical labels, not region positions. Plot context is advisory. Custom gate positions are visibly unavailable.
2. Choose a room and click neighbouring cells, or click an empty cell and choose its room. Different bedroom identities remain separate. Use the checklist to add supported room types. Unassigned cells remain empty. Required unplaced rooms block conversion.
3. Choose **Refine a cell** for large left/right half targets. Opening or cancelling does not divide the cell. Committing a half assignment, including division, is one undoable transaction. Replacements identify the donor room. Removing a bridge cannot disconnect it.
4. Choose 16, 24 or 32 cells. Changing an occupied grid requests an all-floor remapping preview. Collisions and lost/disconnected rooms block applying it; no majority owner is selected silently.
5. Review relationships, entrance destination, clear-size targets/locks and route widths. Place and link actual matching stair rooms for multiple occupied floors or roof access. Upper-floor support and open-sky checks use Custom Plan's existing rules. Room/floor IDs remain stable.
6. Select Ground only, Ground and First, or all occupied floors. Higher-floor drafts remain saved. A partial scope derives its bedroom/floor counts and omits roof access over unfinished upper floors.
7. **Check layout and propose geometry** displays clear polygons, allocation spans versus clear bounding dimensions, door/window proposals and structured issues. No scene is loaded during a check. Explicit acceptance selects Compass as the geometry authority; stale map/site/scope proposals cannot be used.
8. Generate through the normal pipeline. Building, scene, drawings, review, PDF, DXF, GLB, IFC and ZIP come from the accepted geometry. Fine-tuning explicitly switches authority to Custom Plan and retains the Compass draft. Save project files and the normal workspace checkpoints retain Compass data.

Home preferences remain accessible. Programme switches such as pooja, attached bathrooms and kitchen openness do not silently add or rearrange authored rooms: represent these requirements with room cards and relationships, and inspect the input-coverage review. A requested relationship that cannot be placed on a canonical wall is reported as a conflict.

## Contracts and isolation

- `floorforge.compass-input/1`: shared buildable-envelope grid, logical row zero at the front, stable floors and room identities, single-owner whole/half regions, explicit relationships, stair links, site requests and typed requirements.
- `floorforge.project/0.5`: active `compass`, `compassScope`, `compassAcceptance`; inactive drafts and UI selection are kept under `editorState`. An accepted Custom Plan is derived on the server, never trusted as a second editable authority.
- `POST /api/compass/check` and `/convert`: pure proposal requests with a project, Compass draft and optional scope. Return candidate Custom Plan, issues, changes, sizes, source hash and adapter version.
- `POST /api/compass/remap`: previews a requested row density on all saved floors.
- `POST /api/compass/migrate-preview`: retains the original input and reports the need for explicit replacement. It does not rasterize existing exact/metric plans or activate a new input.
- All writes retain the existing JSON size limit, local host/origin rules and session-token checks. `/api/session` describes enabled, advisory and unavailable capabilities.
- Legacy hash calculation has no added null Compass key. Inactive Compass data does not change legacy hashes. UI state and notes do not determine the active Compass build identity; archived floor geometry is omitted from partial scopes.

## Guarded rollout and remaining work

This is a working preview of the core placement-to-generation slice, not completion of every item in the larger implementation plan. Keep the flag off for a general release until the remaining acceptance work is complete.

Custom gate positions, additional road geometry, setback-band site zones, external stair/lift design and automatic lock-aware fitting are unavailable. Composite room presets, automatic conditional programme expansion, geometric migration from legacy inputs, the full reference survey question bank, and first-time-user usability sessions remain future slices. Current room cards, explicit relationships and the exact editor are the supported ways to express these custom-home requirements.

Keyboard arrows move between map cells; Enter/Space select them. Focused refinement and confirmations use modal dialogs. Narrow layouts stack the map and room panel and retain large half-cell targets. Browser checks do not constitute accessibility certification or real-user usability acceptance.

## Verification

Run `.venv/bin/python -m pytest -q` with local loopback socket access. `tests/test_compass.py` covers region topology, hashes, inactive drafts, all eight bearings, room identities, explicit connections, size locks, remapping, G+2 prefix scopes, API protection, and generation through the shared exporters. `tests/compass_state.cjs` exercises pure edit commands, atomic undo and 500 deterministic randomized assignment/removal attempts.

`evidence/compass/` records new-workflow browser captures, reproducibility and the preservation comparison. No sample or renderer regeneration is part of this input refactor. The two original Compass planning documents remain unmodified.

The [dated verification report](COMPASS_VERIFICATION.md) maps the original acceptance scenarios to tested behavior, audit fixes and remaining release work.
