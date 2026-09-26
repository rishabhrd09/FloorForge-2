# FloorForge Studio — 0.2.0-alpha

**A runnable, offline-first preliminary design application, with source, tests, generated examples and evidence. This is not a completed M0–M8 commercial release.**

The previous M0 response was unexecuted source. This distribution is a new multi-file implementation that has actually generated houses, drawings, meshes and export packages. Read `docs/REQUIREMENT_MATRIX.md` for the original brief's implemented, partial, unverified and missing requirements. Do not present this release as sanctioned, architect-approved, structurally designed, photoreal or construction-ready.

## See it immediately — no installation

Open **`START_HERE.html`**, then **`examples/demo/preview.html`** in a modern desktop browser. The preview contains the actual scene and viewer code, with no CDN, server, account or AI dependency. Its drawing is embedded too. WebGL2 is required for 3D; the drawing remains available without it.

The full extracted folder must stay together for the PDF/DXF/GLB/IFC links beside a preview to work. Viewing a sample is not generating a new design.

## Generate your own home

### macOS / Linux

Extract the ZIP into a normal writable folder, not inside the ZIP viewer. From that folder, run the two scripts:

```bash
bash setup.sh
bash start.sh
```

`setup.sh` finds the first installed Python 3.11–3.13 even when `python3` points to a newer release, creates or repairs the local `.venv`, installs the pinned dependencies, and runs a smoke check. If no supported Python is installed but `uv` is available, setup can provision Python 3.13 automatically. `start.sh` checks the environment and repeats setup automatically when it is missing, incomplete or out of date. No `chmod`, global package install or manual virtual-environment activation is required. On macOS, `FloorForge.command` is an optional double-click wrapper around `start.sh`.

The scripts need internet access for the first dependency install, unless `FLOORFORGE_WHEELHOUSE` points to a matching offline wheelhouse. They are developer launchers, not signed native installers.

### Windows

Install Python **3.11–3.13** with the Python launcher, extract the ZIP, and double-click **`FloorForge.bat`**. It calls `setup.bat` on the first run, then `start.bat`. Alternatively run those two scripts yourself. A console remains visible in this developer distribution.

The first setup installs exact-version Python dependencies into `.venv`. **Normal generation and the bundled viewer use no network after setup.** Node, Blender, an AI model and API keys are not required for the core.

If installation fails, read the error and check the selected Python, network access and available disk space. Do not run with administrator/root privileges to work around an ordinary dependency problem. Optional features have separate installers and their failures do not disable the core.

## The workflow

Start with a tested preset: 40×60 ft / G+1 / three bedrooms; 30×40 ft / ground / two bedrooms; or 25×35 ft / ground / one bedroom. Change the five essential fields, then open “Go deeper” only as needed. Review what the fused inputs mean before generating. Inspect the home, drawing set and design review; save a project JSON or export the entire design package.

The generator is bounded, not universal. Infeasible requests return explicit errors rather than adding floors or silently shrinking an exact grid. The tiny-plot example has one bedroom deliberately; a two-bedroom request has not been smuggled into a second floor.

The grid is exact when enabled: cells form real connected polygons, including L-shaped rooms and footprints. Manual grids are currently ground-floor only. Uploaded photos/sketches are **manual references**, not automatically recognised geometry. Image bytes remain in the browser session; project files preserve their metadata, not the image files. Save your originals separately.

## What is included

- Deterministic source fusion and a cached, content-addressed Python DAG.
- G / G+1 reference-family generation, actual room polygons, opening-cut walls, aligned stair cores and a roof-open upper terrace.
- A new responsive studio and an authored offline WebGL2 inspection viewer; six geometric facade recipes, furnished interiors, orbit/dollhouse/plan/walk modes, explicit floor switching, raster captures and an orbit-recording control.
- Three explicit exterior architecture families with real porch, balcony, opening, facade-screen and landscape geometry, plus four independent interior palette choices. The exterior upgrade contract and evidence are in `docs/exterior-upgrade/`.
- SVG drawings and an A3 PDF drawing/review set; layered DXF floor plans with dimension entities; GLB; an IFC4 STEP exporter with a deliberately limited acceptance claim.
- Preliminary room/area/opening schedules, an editable cost scenario, timeline, solar study, Vastu preferences, services notes and review limitations.
- Session-memory local/cloud AI proposal adapters, which are off by default. Real provider/model inference was not run here.
- Optional Three.js/path-tracing/GSAP source, an external Blender worker, optional model download/start scripts, and native packaging recipes. These optional paths are not falsely marked built or accepted.

## Actual output layout

```
~/.floorforge/
  .cache/<stage>/<hash>.json
  builds/<build-id>/
    preview.html
    project.floorforge.json
    intent.json
    building.json
    scene.json
    report.json
    review.json
    sheets.json
    sheets/*.svg
    drawings.pdf
    floorplans.dxf
    model.glb
    model.ifc
    export-checks.json
    manifest.json
    FloorForge-export.zip
```

Builds are immutable. Editing an exported drawing does not update the source project. Save a revised project and regenerate; preserve externally edited drawings separately. Cache corruption and modified published files are rejected, not silently trusted.

## Developer commands

```bash
# Optional developer checks. Normal use only needs setup.sh and start.sh.
.venv/bin/python -m floorforge doctor
.venv/bin/python -m floorforge generate --project examples/briefs/compact.json
.venv/bin/python -m floorforge generate --target layout
.venv/bin/python -m floorforge serve --no-browser --port 8765
.venv/bin/python -m pip install -r requirements-dev.lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_reproducibility.py
```

On Windows replace `.venv/bin/python` with `.venv\Scripts\python.exe`. Use `--out PATH` to put generated projects somewhere else. Ctrl+C stops the developer server. The windowed `desktop.py` launcher is intended for the native packaging recipes.

## Evidence, not marketing

`evidence/pytest.txt` and `pytest.xml` contain the executed suite. `evidence/reproducibility.json` compares two clean generations. `evidence/studio-browser.json` describes the browser checks and their restricted-host transport method. Screenshots are actual engine output, not generated-image substitutions.

DXF was read back and audited by ezdxf; GLB was read back by Trimesh. **That is not AutoCAD GUI acceptance or an independent glTF-validator pass.** IFC reference integrity was self-checked; independent IfcOpenShell/schema/viewer acceptance remains open. PDF page size and text placement were checked, but no physical printer/plotter was tested. Browser rendering used software SwiftShader, not a real GPU.

The supplied archive held 120 images and six videos, not the original FloorForge repository. Its claimed 243 legacy tests were unavailable and are not included in the new test count.

## Important release limits

The output has **no structural design, official NBC clause validation, sanctioned byelaw pack, geotechnical assessment, reinforcement schedule or accessibility/ICU certification**. The cost range uses editable example rates, not market quotations. “Strict Vastu” is reported as unresolved when unmet; it does not create a false pass.

The live renderer is a raster study. Photoreal quality, 4K path-traced output, an interior cinematic film, full stair/capsule physics, drag-resize design editing, automatic sketch/CV interpretation, a complete questionnaire and all native installers are not finished requirements.

No `.dmg`, `.exe` or `.msi` binary is disguised inside this ZIP. `packaging/` contains build recipes that still need execution, signing and clean-machine testing on their target operating systems.

## Documentation

See `docs/ARCHITECTURE.md`, `docs/REQUIREMENT_MATRIX.md`, `docs/AI_ASSIST.md`, `docs/RENDERING.md`, `docs/OPERATIONS.md`, `docs/ACCEPTANCE_PLAN.md`, `docs/RESEARCH_AND_DECISIONS.md` and `licenses/LEDGER.json`.

**Use this to develop and review a design with a competent local professional—not to instruct construction.**
