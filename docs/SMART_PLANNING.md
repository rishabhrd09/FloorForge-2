# Room planning with or without local AI

In **Design rooms → Explore layouts**, choose **Find layouts · no AI needed**.
The Python engine searches alternative arrangements, instead of insisting on the
original room order. It returns up to three layouts with comparison thumbnails.
Choose **Review this layout**, inspect the dashed outlines, then **Yes**. **Undo**
restores the complete previous sketch. A changed request or draft invalidates an
in-flight proposal.

## What the deterministic search does

- Keeps room IDs, names, kinds and floor count; never silently drops a room.
- Searches two room stacks around existing connected circulation. Existing
  courtyards can be incorporated without becoming roofed rooms.
- Sizes rooms against the catalogue minimums, reserves actual wall thickness and
  staircase landings, and ranks arrangements by displacement from the sketch.
- Sends candidates through the existing wall/opening compiler and geometry,
  access, daylight and stair checks. Only passing candidates appear as choices.
- Preserves the original sketch on failure. A bounded search failure does **not**
  establish that no architectural solution exists.

Current scope: one occupied ground floor, 2–12 rectangular walkable rooms, at most
nine beside the central circulation, with an existing hall, lobby, foyer or
veranda. Search checks at most 36 ranked candidates. It does not optimize arbitrary
polygons, foundations or services. The original Smart fit remains available for
nearby adjustments, including its existing upper-floor workflow. Automatic home
generation, exact DXF import and sample generation do not call this new search.

Checked **Keep rooms fixed** entries prevent broad rearrangement. Authored walls,
manual openings, furniture positions, garden/slab/support details and multi-floor
projects are protected. The tool explains that a separate rough copy is needed;
it does not make that copy or remove constraints behind the user's back. Fixed
room choices apply to the current Explore session; they are not saved constraints
in project JSON.

## Optional local interpretation

Ollama is a separately installed runtime. For the recommended vision model:

```sh
# In one terminal, bind only to this computer and disable Ollama cloud:
OLLAMA_HOST=127.0.0.1:11434 OLLAMA_NO_CLOUD=1 ollama serve
# In another terminal (one-time model download, about 6.6 GB):
ollama pull qwen3.5:9b
```

Open **Explore layouts → Describe a change or attach a sketch · local AI**.
Check installed models, enter the model name, describe the request, optionally
attach up to two PNG/JPEG drawings, and confirm the displayed site dimensions.
Click **Send this request to my local model**. No API key is required. Downloads
and model calls are never triggered by normal generation or opening a sample.
The previous brief-only local/cloud AI Assist dialog remains separate.

The model can request a clarification, propose precise room rectangles, request
deterministic rearrangement, or create a requested room programme in an empty
editor. Creation uses the Python search to turn rough placements into connected
alternatives; it needs user-requested connecting circulation. Exact edits are
validated as proposed: a failing dimension is not silently resized to pass.
Rearrangement always uses the current editor rooms; extra model-supplied room
coordinates are ignored and disclosed. Existing room types/names, stairs and
authored plans are protected. Room deletion,
furniture/material changes and multi-floor AI geometry editing are not supported
in this first integration; use the existing editor for those operations.

Inputs can combine the current editor plan, written requirements and reference
images. Confirmed site dimensions and fixed room IDs take priority. The model is
instructed to ask when sources conflict or a reference such as “that bedroom” is
ambiguous. Add answers to the request box and send again, keeping the original
request for context. There is no autonomous conversation memory or guaranteed
architectural interpretation; review every proposal.

## Drawing requirements and limits

- Use a legible, roughly top-down plan. Crop away browser chrome and unused
  page margins so labels stay readable. Room labels and annotated measurements
  help. Confirm plot dimensions and setbacks using the home screen.
- Images alone do not supply trustworthy scale. The system asks for confirmation
  before interpreting them; it never treats pixels as millimetres.
- Browser inputs: up to two PNG/JPEGs, each under 12 MB. They are resized to 1400 px
  on the long edge and JPEG-compressed; each transmitted image must be under
  600 KB. Server decoding also checks file format and pixel count.
- Images are interpretation references, **not an exact tracing/import contract**.
  Use the [dimensioned DXF importer](IMPORT_2D_PLAN.md) for exact supported geometry.
- The local request sends only the selected floor's room data, buildable dimensions,
  instruction, fixed IDs, and selected images to `127.0.0.1:11434`. No project file
  paths, secrets or environment credentials are sent. FloorForge does not persist
  these requests/images. Runtime-level logging is controlled by Ollama.
- The backend checks local installation and vision capability, rejects remote
  Ollama models and redirects, disables environment proxies, validates strict JSON,
  limits inference to one concurrent request and a 16,384-token context, and offers no cloud fallback.
  Missing or stopped Ollama leaves all deterministic tools usable.

These checks establish preliminary geometric consistency, not structural design,
local planning approval, accessibility certification or professional construction
readiness. Model quality and response time vary by hardware and model.

Official integration references:
[Ollama chat API](https://docs.ollama.com/api/chat),
[structured outputs](https://docs.ollama.com/capabilities/structured-outputs),
[Qwen3.5 9B](https://ollama.com/library/qwen3.5:9b),
[model card / Apache 2.0 license](https://huggingface.co/Qwen/Qwen3.5-9B).

## Verification on this workspace (2026-10-02)

The existing full Python suite passed with 485 tests after the integration;
subsequent focused tests cover discarded model coordinates and alternative
layout diversity. Browser checks cover three alternatives, unchanged drafts,
fixed rooms, review/decline/accept, Undo, stale responses, model failure recovery,
mobile layout, and matching 3D generation. All 288 existing sample/reference
files fingerprinted before this work remained byte-for-byte unchanged.

Live Ollama 0.24.0 / Qwen3.5-9B checks on this Mac:

- A written six-room programme produced three geometry-checked alternatives.
- An ambiguous request to move “the bedroom” asked which bedroom and where.
- A ten-room rearrangement produced checked alternatives in about 28 seconds.
- A cropped plan screenshot plus the editor data produced checked alternatives
  in about 33 seconds. A full-screen screenshot with tiny labels produced
  mistaken room observations and clarification questions; crop drawings and
  review interpretations. This is not an image-recognition accuracy benchmark.

The runtime sometimes returned redundant coordinates or JSON code fences despite
its structured-output setting. FloorForge independently validates the response;
rearrangement ignores those coordinates and always uses the actual editor rooms.
No model response directly changes a saved project or 3D scene.

Reproduce the automated checks:

```sh
.venv/bin/python -m pytest -q
node scripts/check_plan_assistance.mjs
```

The browser check needs Playwright installed or `PLAYWRIGHT_MODULE` pointing to an
available Playwright module. It launches an isolated test studio on port 8896.
