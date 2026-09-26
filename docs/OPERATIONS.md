# Setup, operation, recovery and release packaging

## Core installation

On macOS/Linux, the only normal entrypoints are `bash setup.sh` and `bash start.sh`. `setup.sh` selects Python 3.13, 3.12 or 3.11 in that order, creates or repairs `.venv`, installs `requirements.lock.txt`, runs `scripts/smoke.py`, and writes a readiness record containing the lockfile hash. It does not modify global Python packages. `start.sh` validates that record and the core imports, rerunning setup when the environment is missing, incomplete or stale, then starts the loopback server and opens a browser. `FloorForge.command` is an optional double-click wrapper. The Windows batch launchers provide the corresponding workflow on Windows.

The tested execution environment used Python 3.11.15 and the pinned dependencies. A first-time setup needs internet access or a matching offline wheelhouse; normal generation and viewing are offline after setup.

The locks pin versions, but are **not** complete per-platform `--require-hashes` wheel locks. The optional npm package lock was not generated in the blocked environment; the optional setup script generates one on a networked machine. Do not describe this as a fully reproducible native dependency supply chain yet.

For a matching offline machine, run `scripts/make_wheelhouse.py` on a networked machine with the same OS, architecture and Python version. Copy the resulting wheels and set `FLOORFORGE_WHEELHOUSE` to their path before setup. No model or vendor browser package is downloaded by core setup.

## Where projects live

Generated builds and caches default to `~/.floorforge`. A saved `.floorforge.json` can be kept anywhere. The output directory can be changed with `--out`. Project JSON contains structured input, original prose and reference-image metadata, not the uploaded image bytes or AI keys. Back up the original images separately.

A build directory is immutable. Do not edit it in place. Copy external CAD edits elsewhere; they are not automatically imported into FloorForge. To revise the design, change the project and generate a new build. A cache mismatch means remove only the relevant `.cache` folder after preserving evidence; do not delete your saved projects as a repair.

## Troubleshooting

| Symptom | Action |
|---|---|
| Python missing/wrong version | Setup automatically searches for Python 3.13, 3.12 and 3.11. Set `FLOORFORGE_PYTHON` to an executable when a non-standard install must be selected; if no compatible interpreter exists, install uv so setup can provision Python 3.13. |
| Package download failed | Check internet/proxy/Python wheel availability; retry setup or use a matching wheelhouse. |
| 3D unavailable | Enable supported WebGL2 hardware acceleration or use Drawing set; the standalone sample embeds a drawing fallback. |
| Browser cannot connect | Keep the launcher running; use the printed `127.0.0.1` URL and actual random port. |
| Port conflict | Default port `0` chooses a free port; do not force an occupied port. |
| Design rejected | Read the error. Relax the programme, enlarge the plot or explicitly choose G+1; the generator will not secretly add floors. |
| Grid rejected | Ensure connected room labels, exterior light and portal routes, adequate room dimensions, and a fitting ground-only programme. |
| “Nothing changed” | Read the visible build ID and manifest. Style selection requires regeneration. |
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

Keep the prior release folder and project backups. Shut down its server, install the new source into a **new folder**, recreate its environment and reopen a saved project. Roll back by closing the new server and starting the prior folder. The tool does not auto-migrate or delete project files. No automatic update service or telemetry is implemented. Version 0.2 project schemas do not promise backward compatibility with the unavailable legacy repository.
