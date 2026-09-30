# Research, supplied knowledge and independent observations

## Input audit

The mounted materials were five source/reference documents and `house design -1-001.zip`. The archive contained 120 images and six videos, **not** the FloorForge repository. There was no executable legacy backend, `VISION.md` checkout or 243-test suite to run. The previous answer's M0 code had not been supplied as an executed artifact. No legacy test result is inherited.

The 120 images were inspected in five contact sheets as a taste library. Reference patterns were restrained render/stone/timber palettes, contrasting frame lines, deep entry thresholds, articulated roof bands, landscape arrival and layered interiors. This is not a measured design extraction or a license to redistribute those images. They are not bundled in this source distribution. Videos were not reviewed in full. `evidence/input-inventory.json` records the input audit.

Owner-supplied `indian-home-design-rules.md` gives useful targets, but `GENESIS_PROMPT(2).md` section 12 itself requires official BIS clause verification. The implementation stores the research source and null official-clause IDs. It does not falsely promote the supplied numerical summaries into current local law.

## Design decisions and corrections

One orientation convention replaces the documented legacy ambiguity: outward road azimuth, road at local −Y. A requested ground-only house is never auto-promoted. Infeasible input blocks publication instead.

The public rooms form a connected open zone, with a shorter services/circulation core, private rooms behind, aligned upper wet areas/stairs and a real roof-open upper terrace. The bounded strategy is a transparent baseline, not a claim of architectural optimisation over every Indian plot. The current studio exposes the designed exterior and interior themes that have direct downstream effects; the older style field remains only for saved-project/text compatibility because a named exterior theme can supersede much of it.

### Planning like a practising architect (September 2026)

The owner asked for plans with the geometric and spatial discipline of professional CAD/BIM practice and civil-engineering sense, with the fewest survey questions that still fully define a house. Decisions:

- **Rules, not a template.** The room sizes the planner treats as hard limits are the NBC 2016 Part 3 minimums for habitable rooms (9.5 m², 2.4 m; a further room 7.5 m²), kitchens (5 m², 1.8 m) and baths with WC (2.8 m², 1.2 m); comfortable targets grow with the plot and oversize rooms cost too, so a large plot gets generous rooms, not giant ones. Light and air (a window on an outside wall for every habitable room, a ventilator for every bath), clustered wet rooms and short halls are scored, as a reviewing architect would.
- **Indian practice.** Attached baths are asked for directly (every bedroom, the master only, a count or none) because that is how briefs are given; the master gets a dressing room when the suite allows; the pooja is a room kept off bath walls and away from baths overhead (and, when no stack slot suits it, carved from a rear corner of the living room, a common arrangement); upper baths avoid the kitchen below; Vastu is a weighted preference that chooses the plan's hand and is reported as preferred / acceptable / avoid, never claimed.
- **Minimum yet sufficient survey.** Eight questions define a plan: plot size, road side (a compass), bedrooms, storeys, attached baths, Vastu, must-haves (pooja, parking, open kitchen) and budget. Open spaces are derived from the plot (front and rear by depth, sides by width, the way Indian byelaws tabulate them), reproducing the three presets' previous values exactly; stating any setback switches them off. Solar-study, cost-rate, structure and plan-variant fields stay under “Go deeper”.
- **Text as a second way in.** Homeowners write “30 by 40 north facing site, 3BHK duplex, all bedrooms attached, 80 lakhs, vastu compliant”. The parser reads those forms (feet vs metres, sq ft/gaj/cents/guntha/marla areas snapped to standard plots, lakh/crore, G+1/duplex, bath totals) and shows what it read, what it did not and what it assumed, rather than silently guessing.
- **Drawings to office standard.** Plans carry three dimension chains per side, typed opening tags with a schedule sheet, grid bubbles, levels, a north point and a section marker clear of the chains, at 1:100 where the plot allows; DXF plans use true DIMENSION entities.
- **Reference videos.** From the owner's garden and house videos: staggered pale pavers on black pebbles, a breeze-block screen and a wash basin in side passages, a stone water wall on the rear boundary, a stone-clad lit front boundary, a tall vertical timber-slat gate and a slatted timber foyer ceiling. A sala pavilion needs a rear or side garden deeper than Indian setbacks usually leave, so it stands on the open roof terrace instead, where the terrace has room for it beside the loungers.

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
