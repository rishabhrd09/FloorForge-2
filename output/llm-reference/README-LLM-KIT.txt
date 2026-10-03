MY DESIRED HOME - LLM VARIATION KIT

Recommended attachments to an LLM with JSON/PDF reading and code/file tools:
1. baseline-my-desired-home.floorforge.json (editable geometry; most important)
2. my-desired-home-engineer-handover.pdf (human-readable 2D/3D reference)
3. Your completed custom-requirements.txt

Paste MASTER-PROMPT.txt as your instruction. baseline-room-index.json is optional but
useful for mapping PDF room references to JSON IDs and exact baseline sizes.
Optional: add the ground/first floor PNGs if the LLM cannot inspect PDF drawings well.
These PNGs reproduce the floor-plan sheets and are not editable geometry.

Do not upload the ZIP alone unless the LLM can extract it. Extract it first and attach the
individual files. preview.html contains a bundled viewer and compiled scene and can consume
substantial context; it is useful for opening a 3D preview, not as the first design input.

If a CAD-capable tool is involved, the DXF from the engineer handover is an optional source of
editable drawing entities. If a 3D-capable tool is involved, model.glb from that handover is an
optional baseline model. Neither carries the full editable FloorForge project semantics.

Reliable workflow:
- Fill frontage/depth, the number of variants, explicit room moves, locks, minimum clear sizes
  and setbacks. Identify which setbacks are confirmed and which remain assumptions.
- Let the LLM return separate complete OPTION-A.floorforge.json, OPTION-B.floorforge.json, etc.
- In FloorForge, use Open project to load an option. Inspect Custom Plan, validate and generate.
- Resolve reported geometry issues before relying on exported 3D and drawings. A compiler
  validation pass is not structural design or local approval.
- Export the generated PDF, SVG/DXF and GLB/viewer. Both 2D and 3D should have the same new
  plan identity. Re-export after every geometry edit.
- Take the selected option to the architect/civil engineer for site, structure, services and approval work.

FloorForge developer workflow (from the repository, with its existing Python environment):
  python -m floorforge generate --project /path/to/OPTION-A.floorforge.json --out /path/to/option-a-output
The CLI route uses the exact custom-plan compiler when customPlan is present. Invalid geometry
must be repaired; do not replace it with an unrelated automatic preset.

For this G+1 home, load the updated .floorforge.json project. The current DXF importer accepts
one specially layered, rectangular-room ground-floor drawing, with explicit opening spans; it
does not import this handover's multi-floor A-WALL-style DXF or infer its stairs/voids from a PDF.

An image-generation-only model can propose appearance variations, but its images alone do
not establish reliable dimensions or matching 2D/3D geometry. Use structured project geometry
and an actual renderer/compiler for consistent outputs.

All supplied drawings are preliminary for professional review, not construction-approved.
