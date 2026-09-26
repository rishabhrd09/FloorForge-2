# Research, supplied knowledge and independent observations

## Input audit

The mounted materials were five source/reference documents and `house design -1-001.zip`. The archive contained 120 images and six videos, **not** the FloorForge repository. There was no executable legacy backend, `VISION.md` checkout or 243-test suite to run. The previous answer's M0 code had not been supplied as an executed artifact. No legacy test result is inherited.

The 120 images were inspected in five contact sheets as a taste library. Reference patterns were restrained render/stone/timber palettes, contrasting frame lines, deep entry thresholds, articulated roof bands, landscape arrival and layered interiors. This is not a measured design extraction or a license to redistribute those images. They are not bundled in this source distribution. Videos were not reviewed in full. `evidence/input-inventory.json` records the input audit.

Owner-supplied `indian-home-design-rules.md` gives useful targets, but `GENESIS_PROMPT(2).md` section 12 itself requires official BIS clause verification. The implementation stores the research source and null official-clause IDs. It does not falsely promote the supplied numerical summaries into current local law.

## Design decisions and corrections

One orientation convention replaces the documented legacy ambiguity: outward road azimuth, road at local −Y. A requested ground-only house is never auto-promoted. Infeasible input blocks publication instead.

The public rooms form a connected open zone, with a shorter services/circulation core, private rooms behind, aligned upper wet areas/stairs and a real roof-open upper terrace. The bounded strategy is a transparent baseline, not a claim of architectural optimisation over every Indian plot. Six styles change geometry as well as palette, but their variety/photoreal bar is still not accepted.

The first formal suite revealed non-finite input escaping the intended error contract, malformed semantic references reaching the route graph, and a dining-envelope test incorrectly treating two open public zones as physical walls. Non-finite sources and invalid IDs/references now fail early. Furnishing is checked against actual connected public clear space. A separate clean-generation check found DXF creation/update metadata changed bytes; serialization now fixes volatile metadata and preserves a stable per-design GUID. Reproducibility evidence records the subsequent result.

## Primary external checks

Checked during this work on 2026-09-06. URLs are evidence entry points, not downloaded assets.

| Topic | Source | Decision / limit |
|---|---|---|
| Astra workflow | https://developers.openai.com/blog/architectural-visualization-with-astra and `.md` | Fetch failed; used owner Appendix E, not claimed as independently read. |
| OpenAI documentation index | https://developers.openai.com/llms.txt | Retrieved; not a substitute for the missing article. |
| Three baseline | https://raw.githubusercontent.com/mrdoob/three.js/r180/package.json | 0.180.0, MIT; optional build not downloaded here. |
| Path tracer peers | https://raw.githubusercontent.com/gkjohnson/three-gpu-pathtracer/master/package.json | 0.0.24; compatible peer requirements informed optional source. |
| GSAP terms | https://gsap.com/community/standard-license/ | Custom standard license, explicit optional acknowledgement. |
| IFC schema/authoring | https://docs.ifcopenshell.org/ | Independent acceptance tool selected; unavailable here. |
| Qwen | https://huggingface.co/Qwen/Qwen3-8B-GGUF | Apache-2.0 text model, not vision; no inference benchmark. |
| Claude IDs | https://platform.claude.com/docs/en/about-claude/models/overview | Sonnet 5 / Opus 5 / Fable 5 verified in source; Fable 5.1 not established. |
| Solar method | https://gml.noaa.gov/grad/solcalc/solareqns.PDF | Formula source referenced by implementation; no local shading/weather validation. |

## Legal and technical precision

A permissive Python-package label is not a complete transitive license audit. Shapely wheels use GEOS; compiled libraries and bundled assets need their own notices/terms. Blender/IfcOpenShell isolation does not erase licensing obligations. Copyleft does not mean “commercial use is automatically forbidden.” The reference documents' blanket licensing statements are not adopted as legal conclusions. Native redistribution requires a version-specific audit.

Similarly, a watertight component does not establish a watertight union of the house; a window does not establish ventilation compliance; graph reachability is not wheelchair clearance; a solar formula is not an energy simulation; a DLL/IFC self-check is not independent viewer acceptance. All of these distinctions appear in the release ledger.
