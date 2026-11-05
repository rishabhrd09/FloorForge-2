# Tirumala Revision 8 — Option D (D — Larger drawing room) Design Guide & Colony Context Register

> **Preliminary Design Disclaimer:** PRELIMINARY - ENGINEER TO REVIEW - NOT FOR CONSTRUCTION

## 1. Site Overview, Confirmed Orientation & Coordinate System

- **Project Name:** Tirumala (`id: tirumala`, Revision 8, Options A–E)
- **Plot Classification:** Northeast (NE) corner plot with an **EAST-facing principal entrance** (`road_bearing_deg: 90`).
- **Authoritative Conversion:** `1 ft = 304.8 mm` from the Southeast (SE) plot corner `(0, 0)`: `x` runs South-to-North `0..40 ft` (`0..12,192 mm`); `y` runs East-to-West `0..50 ft` (`0..15,240 mm`).
- **Confirmed Boundaries:**
  - **EAST frontage (Front, `y = 0`):** `40 ft 0 in = 12.192 m (12,192 mm)`, adjoining the **9.0 m East colony road** and **basketball-court enclosure & planting** beyond (`E-01`, `N-04`).
  - **WEST boundary (Rear, `y = 15,240 mm`):** `40 ft 0 in = 12.192 m (12,192 mm)`.
  - **NORTH boundary (Right, `x = 12,192 mm`):** `50 ft 0 in = 15.240 m (15,240 mm)`, adjoining the **12.0 m North colony road**, the **opposite colony garden** (lawn, raised planting kerb, pergola/seating, palms, slim lights), and the **two-storey white/grey house with dark blue-grey vertical facade** beyond (`N-01`, `N-02`, `N-03`).
  - **SOUTH boundary (Left, `x = 0`):** `50 ft 0 in = 15.240 m (15,240 mm)`.
- **Total Plot Area:** `2,000 sq ft = 185.806 m²`.

## 2. Five Revision-8 Coordinated Alternatives (A–E)

| Option | Title | Care Area (sq ft) | Drawing Size (ft) | Caregiver Area (sq ft) | Main Rear Veranda Depth (ft) | Geometry Hash | Plan Hash |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`A`** | A — Original flow | `192.0` | `10.0 × 10.0` | `51.0` | `5.5` | `63e3b8c5e7ea` | `0aadd1866c8b` |
| **`B`** | B — Larger care suite | `224.5` | `10.0 × 10.0` | `51.0` | `3.5` | `e002b5ee1d3a` | `23d6796d9764` |
| **`C`** | C — Garden first | `179.5` | `10.0 × 10.0` | `51.0` | `6.5` | `c9b8f23bc1f5` | `776cfc4d9c77` |
| **`D`** | D — Larger drawing room | `179.5` | `10.0 × 12.0` | `51.0` | `4.5` | `dd445ea76d65` | `9ac1a315d184` |
| **`E`** | E — Caregiver courtyard | `192.0` | `10.0 × 10.0` | `52.0` | `5.0` | `525cdbde46c9` | `25675697a5b3` |

## 3. Compact Corner Staircase (`12 × 7.5 ft`), Double-Height Living (`~23 ft`) & Floor Levels

- **Compact Stair Core:** `x = 0.5..12.5 ft`, `y = 18..25.5 ft` (`12 ft` S–N × `7.5 ft` E–W = `90 sq ft`), touching the South wall (`x = 0.5 ft`) and starting immediately behind the kitchen/stair wall (`y = 18 ft`).
- **Climbing Sequence:** Enter from North open hall arrival (`x = 12.5..16 ft, y = 18..21.5 ft`), climb SOUTH (`x = 12.5 -> 4 ft`), turn WEST on the South landing (`x = 0.5..4 ft, y = 18..25.5 ft`), climb NORTH (`x = 4 -> 12.5 ft`) to the upper arrival (`x = 12.5..16 ft, y = 22..25.5 ft`, kept outside the double-height living void).
- **Risers & Treads:** `12 ft (3,658 mm)` floor-to-floor height with `20` equal risers of `182.88 mm` (`10` per flight) and `9` treads per flight at `287.87 mm`.
- **East Stair Window:** `3.25 ft` wide × `2,500 mm` tall (`sill 350 mm`) centered at `x = 2.25 ft` on `y = 17.75 ft`, visually connecting the `3.5 ft` clear South kitchen lane (`x = 0.5..4 ft, y = 7.5..17.5 ft`) to the stair.
- **Floor Levels:** Continuous `+300 mm` datum across all ground-floor rooms, West veranda, `3 ft` shallow open-to-sky porch (`10 × 3 ft`), and `28 × 6.5 ft` East front court (`5.5 ft` standing depth behind two `150 mm` entrance rises at `y = 0.5..1.5 ft`). The `10.5 × 19 ft` Northeast car bay (`x = 29..39.5 ft, y = 0.5..19.5 ft`) remains at ground datum `±0 mm` (`300 mm` lower) with a `6.5 × 15.5 ft` reference car (`2 ft` side gaps, `1.75 ft` end gaps).

## 4. Care Suite, Bed Orientation & Northwest Open Garden Verification

- **Care Bed (`7 × 3.5 ft`):** Head SOUTH (`x = 26.25 ft`), feet NORTH (`x = 33.25 ft`), preserving north-facing sightlines through broad full-height North glazing (`x = 36 ft`) across the `3 ft` clear North garden passage (`x = 36.5..39.5 ft`) to the 12 m road and opposite colony garden (`N-01`), plus the `6.5 ft` East window (`y = careFront`) toward the car court and East basketball enclosure (`E-01`).
- **Farthest West Care Edge:** `35.5 ft` from East frontage; Northwest garden remains open (`nw_garden_open = True`).

## 5. Six Reference Photographs & Camera Presets

| ID | Original Suffix | Bearing | Confidence | Key Reproduced Features |
| :--- | :--- | :--- | :--- | :--- |
| **`N-01`** | `26039` | `2.0°` | `high_cardinal_direction_estimated_offset` | 12 m concrete road in foreground; Opposite raised planting kerb, clipped hedge and manicured colony lawn |
| **`N-02`** | `26040` | `225.0°` | `medium_oblique_southwest_bearing_unmeasured_offsets` | Pair of light-coloured electrical feeder cabinets of differing sizes (smaller left/east, taller right/west); Low brown-grey boundary wall and trimmed green hedge |
| **`N-03`** | `26041` | `180.0°` | `high_southward_cardinal_orientation` | North road concrete carriageway in foreground (East on image-left, West on image-right); Interlocking paver verge, low boundary wall and continuous hedge along plot north frontage |
| **`N-04`** | `26042` | `122.0°` | `provisional_cross_check_unconfirmed_bearing` | Cross-check view from north road looking leftward (east/southeast) toward the junction with the 9 m east road; Paved passage, low boundary wall and corner vegetation |
| **`NE-01`** | `26043` | `222.0°` | `provisional_closeup_pillar_not_survey_corner` | Close-up of weathered masonry pillar with cream/ochre cap, low boundary wall and dense hedge; Interlocking paver footpath/verge and corner palm/shrub planting |
| **`E-01`** | `26044` | `112.0°` | `high_oblique_east_southeast_outlook` | 9 m east road and interlocking paver edge; Raised masonry planting bed and trimmed hedge along court perimeter |

## 6. Room-by-Room Schedule (Option D)

| Floor | ID | Room Name | Kind | Clear Bounding Size (m) | Clear Area (m²) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Ground` | `g-bath` | Master attached bath | `bathroom` | `1.53 × 2.14` | `3.26` |
| `Ground` | `g-care` | Home care suite · north | `care-room` | `6.10 × 3.96` | `16.70` |
| `Ground` | `g-caregiver` | Caregiver room | `bedroom` | `2.59 × 1.83` | `4.75` |
| `Ground` | `g-drawing` | Drawing room · guests | `drawing-room` | `3.05 × 3.66` | `11.16` |
| `Ground` | `g-family` | Living · dining · stair hall | `family` | `6.86 × 7.47` | `23.92` |
| `Ground` | `g-kitchen` | Open kitchen · southeast | `kitchen` | `1.53 × 3.05` | `4.66` |
| `Ground` | `g-master` | Master bedroom · southwest | `bedroom` | `4.58 × 4.42` | `16.40` |
| `Ground` | `g-porch` | Shallow entry porch | `veranda` | `3.05 × 0.92` | `2.80` |
| `Ground` | `g-puja` | Screened puja niche | `pooja` | `1.45 × 0.61` | `0.89` |
| `Ground` | `g-south-lane` | South daylight lane | `veranda` | `1.22 × 3.20` | `3.90` |
| `Ground` | `g-stair` | Compact corner stair | `stair` | `3.66 × 2.29` | `8.36` |
| `Ground` | `g-veranda` | Open rear veranda | `veranda` | `6.10 × 1.37` | `8.38` |
| `Ground` | `g-wc` | Caregiver WC | `bathroom` | `1.53 × 1.83` | `2.79` |
| `First` | `u-bath` | Upper bathroom · southeast | `bathroom` | `2.44 × 3.05` | `7.45` |
| `First` | `u-living-void` | Double-height living void | `void` | `3.05 × 2.37` | `6.62` |
| `First` | `u-lobby` | Upper stair arrival & gallery | `hall` | `5.26 × 7.55` | `15.39` |
| `First` | `u-master` | Upper bedroom · southwest | `bedroom` | `3.66 × 2.98` | `10.89` |
| `First` | `u-stair` | Upper staircase core | `stair` | `3.66 × 2.29` | `8.36` |
| `First` | `u-study` | Upper study · northeast | `study` | `3.74 × 2.82` | `10.54` |
| `First` | `u-terrace` | East upper terrace | `terrace` | `2.75 × 0.92` | `2.52` |

## 7. Assumptions & Unknowns Requiring Survey Verification

- Exact surveyed plot corner coordinates (total-station tie to existing masonry walls, hedges, and NE pillar).
- Statutory road width definition (whether 12 m North and 9 m East dimensions denote carriageway-only or total right-of-way including verges and drains).
- Exact footpath, paver verge, and stormwater drain widths and invert levels.
- Spot elevations of Natural Ground Level (NGL), road crown levels, and flood/plinth datum.
- Exact trunk coordinates, girth, species, and crown spread of roadside and garden trees.
- Exact measured offsets of the two NW electrical feeder cabinets, underground cable routing, and statutory transformer/feeder clearance.
- Exact measured offset of the North streetlight pole and overhead/underground service lines.
- Exact depth of the North colony garden and setback distance to the opposite white/grey house.
- Basketball-court exact footprint, internal surface material, hoop/backstop positions, and floodlight pole heights hidden behind dense tree screening.
- Exact adjoining building massing, boundary wall heights, and window positions on the South and West neighbouring plots.
- Applicable local municipal building bylaws (setbacks, FAR/FSI, maximum height, coverage, and road-corner splay requirements).

Plan hash: `9ac1a315d1849d22e1bae5f2e2814abbe70061012ce1aca2259822523c68cdaa` | Geometry hash: `dd445ea76d651340204ebd2208c091b638f203d66072f1cd1a9ecd919382a385`
