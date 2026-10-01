# Setup, operation, recovery and release packaging

## Core installation

On macOS/Linux, the only normal entrypoints are `bash setup.sh` and `bash start.sh`. `setup.sh` selects Python 3.13, 3.12 or 3.11 in that order, creates or repairs `.venv`, installs `requirements.lock.txt`, runs `scripts/smoke.py`, and writes a readiness record containing the lockfile hash. It does not modify global Python packages. `start.sh` validates that record and the core imports, rerunning setup when the environment is missing, incomplete or stale, then starts the loopback server and opens a browser. `FloorForge.command` is an optional double-click wrapper. The Windows batch launchers provide the corresponding workflow on Windows.

The tested execution environment used Python 3.11.15 and the pinned dependencies. A first-time setup needs internet access or a matching offline wheelhouse; normal generation and viewing are offline after setup.

The locks pin versions, but are **not** complete per-platform `--require-hashes` wheel locks. The optional npm package lock was not generated in the blocked environment; the optional setup script generates one on a networked machine. Do not describe this as a fully reproducible native dependency supply chain yet.

For a matching offline machine, run `scripts/make_wheelhouse.py` on a networked machine with the same OS, architecture and Python version. Copy the resulting wheels and set `FLOORFORGE_WHEELHOUSE` to their path before setup. No model or vendor browser package is downloaded by core setup.

## Where projects live

Generated builds and caches default to `~/.floorforge`. A saved `.floorforge.json` can be kept anywhere. The output directory can be changed with `--out`. Project JSON contains structured input, original prose, the fixed 4 × 4 semantic placement guide and reference-image metadata, not the uploaded image bytes or AI keys. Back up the original images separately. Reference-image pixels are not inspected by generation; their records are for a person to consult.

A build directory is immutable. Do not edit it in place. Copy external CAD edits elsewhere; they are not automatically imported into FloorForge. To revise the design, change the project and generate a new build. A cache mismatch means remove only the relevant `.cache` folder after preserving evidence; do not delete your saved projects as a repair.

## Troubleshooting

| Symptom | Action |
|---|---|
| Python missing/wrong version | Setup automatically searches for Python 3.13, 3.12 and 3.11. Set `FLOORFORGE_PYTHON` to an executable when a non-standard install must be selected; if no compatible interpreter exists, install uv so setup can provision Python 3.13. |
| Package download failed | Check internet/proxy/Python wheel availability; retry setup or use a matching wheelhouse. |
| 3D unavailable | Enable supported WebGL2 hardware acceleration or use Drawing set; the standalone sample embeds a drawing fallback. |
| Browser cannot connect | Keep the launcher running; use the printed `127.0.0.1` URL and actual random port. |
| Port conflict | Launching on a port already serving this FloorForge project reuses that server and opens its URL. Its current settings stay in force. If another application or a different project owns the port, use `--port 0` to choose a free port. |
| Design rejected | Read the error. Relax the programme, enlarge the plot or explicitly choose G+1; the generator will not secretly add floors. |
| 16-cell guide rejected | The board must be exactly 4 × 4, contain at least one supported room label and agree with the programme (for example, do not paint bedroom 4 in a two-bedroom brief). Each requested floor has a separate board; floor assignment is retained, while cell boundaries remain relative. |
| Room appears in the wrong area | Confirm **Apply this positional guide** is on, generate a new build, then inspect the building's placement audit. The planner uses relative targets while retaining minimum sizes, circulation and the painted floor assignment; a cell is not an exact boundary. |
| Description did not change the plan | Open **Review what we understood**. Only listed structured values and supported room-location phrases are applied. Anything under “not understood”, or a disabled description, remains a note. |
| Reference image did not change the plan | Expected: images are metadata/manual references only. Enter the required fact in a supported field, recognised description phrase or the 16-cell guide. |
| “Nothing changed” | Read the visible build ID and manifest and confirm the relevant source is enabled. Theme, brief, description and guide changes require regeneration. |
| Provider error | Verify the exact model ID, endpoint, quota and key; AI stays optional. Keys expire after 30 minutes. |
| IFC viewer rejects a file | Preserve its validation report and do not label IFC accepted; use SVG/DXF/GLB for review while fixing the exporter. |

## Optional tools

- Local model: `python scripts/download_model.py --dry-run`, then an explicit licensed download; see `AI_ASSIST.md`.
- Three/path tracer: `python scripts/setup_three.py --accept-gsap-standard-license` on a networked machine; optional lab at `/three.html`.
- Blender: `blender --background --python scripts/blender_scene.py -- --help`; see `RENDERING.md`.
- IFC acceptance: install `requirements-optional-bim.txt` in a separate environment, then `python scripts/verify_ifc.py path/to/model.ifc`.

## Native packaging — recipes, not shipped binaries

`desktop.py` is a windowed Tk launcher intended for PyInstaller; it opens the local studio in the default browser and offers a stop control. It is not an embedded-webview or auto-updating native client.

On macOS use `packaging/build-macos.sh`. It builds a `.app` and an **unsigned** DMG using PyInstaller and `hdiutil`. On Windows use `packaging/build-windows.ps1`; Inno Setup (`ISCC.exe`) is needed for the wizard installer. Without it, the recipe produces a portable directory. No MSI recipe, code-signing certificate, notarisation token or validated installer is included.

Both native build scripts remain **unexecuted on their target platforms**. A Linux run is not evidence of macOS or Windows success. Inspect dependencies, bundled licenses, application startup, uninstall behaviour, project preservation, host architecture and offline operation before distribution. The authored GitHub workflow does not imply CI has already passed.

## Rollback and updates

Keep the prior release folder and project backups. Shut down its server, install the new source into a **new folder**, recreate its environment and reopen a saved project. Roll back by closing the new server and starting the prior folder. The tool does not auto-migrate or delete project files. No automatic update service or telemetry is implemented. Version 0.2 project schemas do not promise general backward compatibility with the unavailable legacy repository.

One narrow compatibility path is retained for this repository's earlier metric grids: a project containing `cell_mm` and the legacy `floors` matrix can still be read/generated with the old exact, ground-floor rules. When the current studio opens that board, it maps every distinct room label to the nearest free 4 × 4 cell around that room's old centroid; it refuses migration if more than 16 distinct labels would force data loss. A subsequent save emits the current semantic-grid contract and no longer promises the old millimetre cells. Keep a backup if the exact legacy payload matters.

For exact geometry and stale-preview troubleshooting, see [Custom Plan](CUSTOM_PLAN.md). Failed generation keeps the previous design visibly labelled and disables exports for the current draft.


## Opening doors and windows while walking

Approach a generated door or window, look toward its opening and press **F**, or tap/click the contextual button. Both sides work within 2.1 m on the same floor; intervening walls, furniture and other leaves block the interaction. **↑/↓** move forward/back; **←/→** turn; **A/D** strafe; **Q/E** also turn. Held F does not repeatedly toggle the opening, and typing in form fields does not control the walk.

Room and entrance doors swing between their authored open pose and closed pose. A sliding window's first sash moves onto its neighbour; single-pane windows pivot. Raised sills, fixed frames, guards and walls remain physical obstacles. Use a door for gallery/balcony access. Existing balcony glazing is authored half-open: **Open fully** clears its remaining leaf, and **Return to half-open** restores the authored pose. It does not pretend that this partial-panel design can seal the whole aperture.

Moving leaf geometry and walking collision use the same transforms. A panel stops if the visitor enters its sweep; step clear and operate it again. Operating an opening changes only the walkthrough pose, not the draft revision or plan hash. Reloading a design restores authored poses. Canonical GLB/IFC/drawings retain those design poses; a presentation GLB records the currently visible poses in its metadata. Previously exported standalone HTML contains its old embedded viewer; generate a new export for these controls. Old scenes opened in the current studio are supported through their companion building file.

## Combining inputs

**Review what we understood** and **Generate** populate a persistent **Input coverage** panel. It records applied/confirmed fields, overridden values and their winning source, unparsed description requests, disabled sources, inactive plan drafts, reference images and notes. Exact custom geometry controls its rooms, openings and stairs: automatic programme switches and description placements are explicitly reported when they cannot rewrite that geometry. A source is not labelled applied merely because it is enabled. Input coverage is stored with the same plan hash in intent, building, scene and report JSON. Coverage from an older revision is labelled as previous when the draft changes.

Images and arbitrary prose still need manual interpretation; the coverage panel makes that limitation visible. Conflicting equal-priority fields and invalid geometry remain generation errors.
