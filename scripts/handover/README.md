# Saved-home handover tools

These scripts preserve the tools used to prepare the owner-to-engineer handover in `output/pdf/`. They read `examples/gallery/my-desired-home/` without regenerating or changing the sample.

Run from the repository root:

1. `node scripts/handover/capture-handover.mjs` captures the four 3D views into `tmp/pdfs/views/`. Install Playwright or set `PLAYWRIGHT_MODULE` to its module path.
2. `.venv/bin/python scripts/handover/build-handover.py` builds the A3 PDF and DXF. It requires Pillow, ReportLab, Shapely and Trimesh.
3. Render PDF pages 2–4 at 300 DPI into `output/pdf/plan-02.png` through `plan-04.png` using a PDF renderer, and visually inspect the full PDF before packaging.
4. `.venv/bin/python scripts/handover/package-handover.py` checks the plan images and creates the handover ZIP.

The saved verification records are in `evidence/handover/`. Intermediate images stay in ignored `tmp/`; final deliverables and the LLM variation kit are versioned in `output/`. These are preliminary design references for professional review, not construction drawings.
