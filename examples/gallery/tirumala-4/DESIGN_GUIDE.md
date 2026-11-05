# Tirumala 4 — P13 Site-Calibrated Reference

Approved source: `tirumala-3` (`p13-icu-east-extension-2026-10-30`, source `planHash`: `22453e485574c04b3780e1bcabb816917ae4ab81ea91093e1720de9fe99271ba`, `geometryHash`: `b6484526b3006577c8ea77d195487ec31e7226a90a9804cd2f2d400bc74b78fc`).
Plot: **40 ft north–south × 50 ft east–west** (`12.192 × 15.240 m`, `2,000 sq ft`). West is up and north is right in overhead 2D plans.

Tirumala 4 preserves every room polygon, wall thickness, opening span, stair flight, ceiling height, and P13 Home ICU enlargement from Tirumala 3 (`geometryHash` identical), while calibrating the real Tirumala Colony surroundings (`R07`–`R14`, `V01`–`V06`), separating pre-construction plot vegetation into the `Existing plot` site mode toggle, keeping the private car porch empty by default (`defaultCarVisible: false`), and refining interior daylight/overcast material response.

## Ground & First Floor Room Schedule

| Room | Floor | Clear bounding span (feet / inches) | Net Area (sq ft) | Net Area (m²) |
|---|---:|---|---:|---:|
| Master bedroom | Ground | 22′11″ × 17′3¾″ | 276.7 | 25.71 |
| Master bath | Ground | 8′ × 6′ | 48.0 | 4.46 |
| Home ICU | Ground | 11′3″ × 13′4⅞″ | 150.8 | 14.01 |
| Drawing room | Ground | 10′1⅜″ × 10′6″ | 106.2 | 9.86 |
| Caregiver | Ground | 10′1⅜″ × 9′1⅜″ | 92.2 | 8.56 |
| Caregiver WC | Ground | 6′7½″ × 5′8″ | 37.6 | 3.49 |
| Lightwell | Ground | 4′11″ × 5′5″ | 26.6 | 2.48 |
| Store | Ground | 2′11⅜″ × 9′9⅛″ | 28.8 | 2.68 |
| Lobby | Ground | 3′ × 9′4¼″ | 28.1 | 2.61 |
| Veranda | Ground | 15′7⅝″ × 7′0¼″ | 102.8 | 9.55 |
| Wash gully | Ground | 3′6″ × 10′11″ | 38.2 | 3.55 |
| Kitchen | Ground | 9′5⅝″ × 10′3⅛″ | 97.1 | 9.02 |
| Living / dining | Ground | 22′9⅝″ × 17′2¾″ | 223.5 | 20.76 |
| Stairs | Ground | 10′9⅞″ × 12′9½″ | 80.5 | 7.48 |
| Upper master suite | First | 22′11″ × 17′3¾″ | 276.7 | 25.71 |
| Master ensuite | First | 8′ × 6′ | 48.0 | 4.46 |
| Office / study | First | 10′1⅜″ × 9′1⅜″ | 92.2 | 8.56 |
| Guest bedroom | First | 10′1⅜″ × 10′6″ | 106.2 | 9.86 |
| Shared bathroom | First | 6′7½″ × 5′8″ | 37.6 | 3.49 |
| Gallery overlooking living | First | 10′0⅛″ × 25′1⅛″ | 140.3 | 13.03 |
| Open garden terrace | First | 34′0⅛″ × 21′4⅞″ | 357.9 | 33.25 |

## Door & Full-Height Opening Schedule

Jambs reduce door aperture width by `110 mm` (`4⅜ in`). The ground-floor master bedroom entry recess is not the bedroom doorway.

| Opening ID | Floor | Raw Kind | Structural Aperture | Clear Between Jambs |
|---|---:|---|---:|---:|
| `drawing-veranda-only` | Ground | `door` | 2′11⅜″ (`900.0 mm`) | 2′7⅛″ (`790.0 mm`) |
| `living-veranda` | Ground | `wood-mesh-fold` | 5′10⅞″ (`1800.0 mm`) | 5′6½″ (`1690.0 mm`) |
| `icu-glass-living` | Ground | `glass` | 5′2⅞″ (`1597.6 mm`) | 4′10⅝″ (`1487.6 mm`) |
| `store-door` | Ground | `sliding-door` | 2′5½″ (`750.0 mm`) | 2′1¼″ (`640.0 mm`) |
| `icu-veranda-glass` | Ground | `glass` | 3′3⅜″ (`1000.0 mm`) | 2′11″ (`890.0 mm`) |
| `master-door` | Ground | `door` | 2′7½″ (`800.0 mm`) | 2′3⅛″ (`690.0 mm`) |
| `bath-door` | Ground | `door` | 2′11⅜″ (`900.0 mm`) | 2′7⅛″ (`790.0 mm`) |
| `caregiver-lobby` | Ground | `door` | 2′7½″ (`800.0 mm`) | 2′3⅛″ (`690.0 mm`) |
| `wc-caregiver-only` | Ground | `door` | 2′7½″ (`800.0 mm`) | 2′3⅛″ (`690.0 mm`) |
| `lightwell-maintenance` | Ground | `door` | 2′7½″ (`800.0 mm`) | 2′3⅛″ (`690.0 mm`) |
| `u-master-door` | First | `door` | 2′7½″ (`800.0 mm`) | 2′3⅛″ (`690.0 mm`) |
| `u-master-bath-door` | First | `door` | 2′11⅜″ (`900.0 mm`) | 2′7⅛″ (`790.0 mm`) |
| `u-office-door` | First | `door` | 2′11⅜″ (`900.0 mm`) | 2′7⅛″ (`790.0 mm`) |
| `u-bedroom-door` | First | `door` | 2′11⅜″ (`900.0 mm`) | 2′7⅛″ (`790.0 mm`) |
| `u-bath-door` | First | `door` | 2′11⅜″ (`900.0 mm`) | 2′7⅛″ (`790.0 mm`) |
| `u-terrace-door` | First | `sliding-door` | 5′3″ (`1600.0 mm`) | 4′10⅝″ (`1490.0 mm`) |
| `u-side-terrace-door` | First | `sliding-door` | 4′7⅛″ (`1400.0 mm`) | 4′2¾″ (`1290.0 mm`) |

## Measured Circulation & Bottleneck Clearance Audit

| Passage / Pinch Point | Clear Width (ft / in) | Clear Width (mm) | Notes |
|---|---:|---:|---|
| Home ICU (g-care) — Room clear dimensions | 11 ft 3 in x 13 ft 4 7/8 in (150.8 sq ft) | `3429.6 (N-S) x 4085.6 (E-W)` | Includes 2 ft (609.6 mm) east extension aligning ICU east exterior wall with kitchen front (y = 1524 mm), retaining 5 ft East forecourt. |
| Home ICU — Bed foot to East wall/window | 3 ft 1 1/8 in | `942.8` | Recliner bed east foot at y = 2616.8 mm to ICU east inner wall at y = 1674.0 mm. |
| Home ICU — Bed head to West wall | 3 ft 1 1/8 in | `942.8` | Recliner bed west head at y = 4816.8 mm to ICU west inner wall at y = 5759.6 mm. |
| Home ICU — Bed south side to Hall–ICU door wall | 3 ft 2 7/8 in | `987.6` | Recliner bed south edge at x = 6440.0 mm to south inner wall at x = 5452.4 mm (857.6 mm clear past wall-mounted TV). |
| Home ICU — Bed north side to Veranda door wall | 4 ft 4 7/8 in | `1342.0` | Recliner bed north edge at x = 7540.0 mm to north inner wall at x = 8882.0 mm; companion chair in NW pocket leaves 520 mm diagonal gap to bed corner and 267.6 mm to veranda door jamb. |
| Hall–ICU layered entrance (icu-glass-living) | 6 ft 10 11/16 in structural / 6 ft 6 3/8 in clear | `2100.0 structural / 1990.0 clear between jambs` | Hall-side 4-panel folding teak privacy door conceals independent 4-panel sliding glass directly behind it within the same opening. |
| ICU–Veranda slide-and-turn glass door (icu-veranda-door) | 6 ft 0 in structural / 5 ft 7 11/16 in clear | `1828.8 structural / 1718.8 clear between jambs` | 4-panel slide-and-turn frameless glass assembly opening onto the North veranda. |
| Living–Veranda folding wood + mesh door (living-veranda) | 3 ft 10 in structural / 3 ft 5 5/8 in clear | `1167.8 structural / 1057.8 clear between jambs` | Outward-folding teak leaves + retractable pleated insect mesh; unchanged from Tirumala 3. |
| Principal East house entrance (main-entry) | 4 ft 6 in structural / 4 ft 1 11/16 in clear | `1371.6 structural / 1261.6 clear between jambs` | Double teak entry doors from the 5 ft raised East forecourt (+300 mm). |
| Living / Dining / Open Kitchen circulation | 4 ft 0 3/8 in / 4 ft 9 1/16 in | `1230.0 (sofa to coffee table) / 1450.0 (kitchen worktop pass-through)` | Unobstructed sightline and step-free level path from East entry through living/dining to veranda and bedrooms. |
| Master Bedroom doorway (master-door) | 2 ft 7 1/2 in leaf in 3 ft 3 3/8 in throat | `800.0 leaf in 1000.0 throat (690.0 clear between frame stops)` | Preserved from authoritative P11/P13 geometry; recorded as the narrowest bedroom doorway throat. |
| Wash gully doorway & Caregiver WC door | 2 ft 3 9/16 in structural / 1 ft 11 1/4 in clear | `700.0 structural / 590.0 clear between jambs` | Secondary service/WC doors preserved from authoritative P11/P13 geometry. |

## Kitchen, Levels, Stairs & Finishes

- **Kitchen**: Serving worktop `2′11⅜″ × 1′1¾″`. L-counter along the store and east walls; east run `9′1⅝″`. No fridge or puja room.
- **Levels**: House, veranda, east forecourt, and side/rear passages sit at `0 mm` house datum (`+300 mm` above road NGL). Road NGL is `-300 mm`. Lower car porch sits at `-152.4 mm` (`-6 in` provisional adjustable drop, separate from horizontal plot/room dimensions). Default car visibility is `false` (empty porch); the accurately sized Škoda Kylaq (`4098 × 1975 × 1522 mm`) can be toggled on via `Show car` for a parking check.
- **Stairs & Upper Floor**: 18 risers (`175 mm`) to `3150 mm` landing, plus 2 arrival connector risers (`179 mm`) to `3508 mm` first-floor slab. Ground-floor clear ceiling is `3315 mm`; double-height living void reaches `6991 mm` (`~23 ft`). First floor comprises the upper master suite (`276.7 sq ft`), master ensuite (`48.0 sq ft`), study/office (`92.2 sq ft`), guest bedroom (`106.2 sq ft`), shared bathroom (`37.6 sq ft`), gallery overlooking the double-height living hall, and open garden terrace reached directly from the gallery (no stair to the roof above the first floor).
- **Material Palette**: Large `24 × 48 in` (`609.6 × 1219.2 mm`) warm white/ivory marble-look tiles (soft-satin indoors, coordinated non-slip matte on veranda and wet gullies), textured Kota stone with red-oxide border on the lower car porch, warm limestone exterior cladding, teak timber accents, charcoal aluminium glazing, and warm daylight (`day`) + neutral overcast (`overcast`) lighting grades.
- **Layered Hall–ICU Entrance**: Wooden privacy doors sit on the hall side concealing an independent sliding glass door behind them (`icu-glass-living-wood` + `icu-glass-living`). Both layers operate independently (`Wood closed`, `Reveal glass`, `Both open`). The separate ICU–veranda glass opening (`icu-veranda-glass`) stacks neatly to the side.

## Exterior refinement — 31 October 2026

The proposed house boundary retains its masonry and gate geometry with ivory render, a honed limestone base, thin stone coping and inset light faces. Solid burgundy hedge proxy boxes are replaced by actual leaf geometry; photographed colony walls remain muted mauve-grey. The corner paving gap becomes an edged grass/groundcover pocket. Existing north-strip pads and circulation remain unchanged. Context roads/pavers gain textured finishes and streetlights have slimmer round poles. Per-project neutral/warm bounce light reduces the blue cast. These are real-time rendered improvements, not a surveyed or photographic reconstruction.

## My Desired Home exterior match — owner revision

Warm off-white exterior plaster (#f1efea), textured stone accents (#a39d92 / #6f6b64), charcoal window surrounds (#1d2022) and timber (#7a5234) derive from My Desired Home. Exterior glazing now has stronger reflection and a light blue-green tint while retaining every opening size and operating door layer. Interior plaster is unchanged. Owner-confirmed vacant South/West adjoining land replaces the earlier inferred houses with grass; buildings across the roads remain context landmarks. This correction supersedes prior claims that R10/R12 buildings adjoined this plot.

## Site reference and rendering review — 3 November 2026

Reviewed the owner's annotated stills and sampled the 23.36-second video pan. North garden: visible lawn blades, two rounded ornaments, stone pergola posts, slim park lamps and the reference house's horizontal upper window. East court: fine anti-aliased diamond chain-link, raised planting and softer background depth. Road joints are thinner and drain apertures round. Sun-shadow coverage includes the garden and court. Ivory tile, timber, fabric and kitchen joinery details are refined without resizing rooms or furnishings. Eight exterior reference views are available in the sample's view selector.

The 12 m north and 9 m east widths represent overall road corridors, including the modeled verges. Their internal split is estimated. Camera coordinates, garden depth, distant buildings, hidden court details and plant positions remain illustrative. R09/R13's heading is unconfirmed. These real-time 3D views are not survey-grade or photographic reconstructions.

## Colony Site Calibration & Evidence Hygiene (`R07`–`R14`, `V01`–`V06`)

- **Existing vs Proposed Site Layer Toggle**: Pre-construction trees, wild scrub, and footing blocks (`R07`, `R10`, `R12`, `V05`, `V06`) are isolated in the `Existing plot` site mode (`Site: Existing plot` button) so zero tree trunks or branches pass through rooms or block access in `Proposed` mode.
- **Colony Road & Boundary Details**: Grooved concrete carriageways (`12 m` North road, `9 m` East road), interlocking dusty-rose/grey paver verges, precast concrete storm-drain cover slabs with paired circular holes (`V01`, `R09`, `R13`), muted mauve-taupe boundary walls (`#8e7e85`) with pale grey coping (`#c8c4bc`) and horizontally grooved square corner piers (`R11`, `R14`, `V02`, `V05`), mixed burgundy *Acalypha* and white-flowering green *Tabernaemontana* hedges (`R10`, `R12`, `V03`), slim dark-grey LED street luminaires (`R09`, `R13`, `R14`, `V04`), and round-hooded post-top park lamp + fenced basketball court with terracotta key and white markings (`V01`, `E-01`).
- **R11 Duplicate Photo Discrepancy**: Two attachments in the reference set use the identical underlying photograph (`1000145311.jpg`) with different annotations (`R11-NE-corner-owner-labelled.png` vs `alternate-annotation/R11-wall-return-unconfirmed.png`). They are documented as a single photograph in `photo-reference-manifest.json` and `assumptions-register.json`; the owner-confirmed NE corner interpretation is used while preserving the locked `40 × 50 ft` boundary.
- **V06 Video Roll Caution**: Near the end of the walk-around video (`V06`, `20.0 s`), the camera tilts/rolls while framing plot vegetation; compass bearings are derived from continuous pan landmarks (`V01`–`V05`), never from camera roll.
- **Transient Exclusions**: All temporary parked cars, covered vehicles, scooters, and pedestrians visible in `R09`, `R10`, `R12`, and `R13` are excluded from the permanent 3D colony scene.

Plan hash: `096ae83c8d2a08b4a39649e25b2643cf7d52eaa2db140a71c59ec5ac015550fd`. Geometry hash: `b6484526b3006577c8ea77d195487ec31e7226a90a9804cd2f2d400bc74b78fc` (matches Tirumala 3 / P13).
