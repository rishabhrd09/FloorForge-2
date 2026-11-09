# Tirumala Revision 10 — Option C (C — Garden first) Design Guide & Colony Context Register

> **Preliminary Design Disclaimer:** PRELIMINARY - ENGINEER TO REVIEW - NOT FOR CONSTRUCTION

## 1. Site Overview, Confirmed Orientation & Coordinate System

- **Project Name:** Tirumala (`id: tirumala`, Revision 10, Options A–E)
- **Plot Classification:** Northeast (NE) corner plot with an **EAST-facing principal entrance** (`road_bearing_deg: 90`).
- **Authoritative Conversion:** `1 ft = 304.8 mm` from the Southeast (SE) plot corner `(0, 0)`: `x` runs South-to-North `0..40 ft` (`0..12,192 mm`); `y` runs East-to-West `0..50 ft` (`0..15,240 mm`).
- **Confirmed Boundaries:**
  - **EAST frontage (Front, `y = 0`):** `40 ft 0 in = 12.192 m (12,192 mm)`, adjoining the **9.0 m East colony road** and **basketball-court enclosure & planting** beyond (`E-01`, `N-04`).
  - **WEST boundary (Rear, `y = 15,240 mm`):** `40 ft 0 in = 12.192 m (12,192 mm)`.
  - **NORTH boundary (Right, `x = 12,192 mm`):** `50 ft 0 in = 15.240 m (15,240 mm)`, adjoining the **12.0 m North colony road**, the **opposite colony garden** (lawn, raised planting kerb, pergola/seating, palms, slim lights), and the **two-storey white/grey house with dark blue-grey vertical facade** beyond (`N-01`, `N-02`, `N-03`).
  - **SOUTH boundary (Left, `x = 0`):** `50 ft 0 in = 15.240 m (15,240 mm)`.
- **Total Plot Area:** `2,000 sq ft = 185.806 m²`.

## 2. Five Revision-10 Coordinated Alternatives (A–E)

| Option | Title | Care Area (sq ft) | Drawing Size (ft) | Caregiver Area (sq ft) | Main Rear Veranda Depth (ft) | Geometry Hash | Plan Hash |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`A`** | A — Original flow | `192.0` | `11.0 × 10.0` | `51.0` | `5.5` | `be629eea20f8` | `dae756745908` |
| **`B`** | B — Larger care suite | `224.5` | `11.0 × 10.0` | `51.0` | `3.5` | `d1e499796c9a` | `16b9ee1fe2f7` |
| **`C`** | C — Garden first | `179.5` | `11.0 × 10.0` | `51.0` | `6.5` | `c8ba66f8e766` | `fcf63e7d4efa` |
| **`D`** | D — Larger drawing room | `179.5` | `11.0 × 12.0` | `51.0` | `4.5` | `391c1221ea50` | `d026f2cbfe47` |
| **`E`** | E — Caregiver courtyard | `192.0` | `11.0 × 10.0` | `52.0` | `5.0` | `516de0cde1a1` | `c8fb1526d089` |

## 3. Corner L Stair, Double-Height Living & Floor Levels

- **L stair:** two perpendicular 1,067 mm wide flights and a square landing, climbing SOUTH then EAST. The 12 × 12 ft bounding box includes the dining corner; actual stair footprint is approximately 71.8 sq ft, not 144 sq ft.
- **Risers & treads:** 20 equal rises over 3,658 mm, 18 treads at 287.89 mm, with the upper floor cut only over the L-shaped stair. The east upper arrival is outside the living void.
- **Kitchen & dining:** approximately 121 sq ft kitchen, opening north to the hall and west to dining through a low 950 mm serving counter plus a clear passage. The 3.5 ft south daylight lane ends at the tall stair window.
- **First floor:** two master suites, a compact office, a furnished common lounge, and a small open terrace with separate doors from the lounge and suite 2. A smaller double-height opening preserves the height and rooflight while allowing the larger upstairs accommodation.
- **Floor Levels:** Continuous `+300 mm` datum across all ground-floor rooms, West veranda, `3 ft` shallow open-to-sky porch (`11 × 3 ft`), and `28 × 6.5 ft` East front court (`5.5 ft` standing depth behind two `150 mm` entrance rises at `y = 0.5..1.5 ft`). The `10.5 × 19 ft` Northeast car bay (`x = 29..39.5 ft, y = 0.5..19.5 ft`) remains at ground datum `±0 mm` (`300 mm` lower) with a `6.5 × 15.5 ft` reference car (`2 ft` side gaps, `1.75 ft` end gaps).

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

## 6. Room-by-Room Schedule (Option C)

| Floor | ID | Room Name | Kind | Clear Bounding Size (m) | Clear Area (m²) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Ground` | `g-bath` | Master attached bath | `bathroom` | `1.53 × 2.14` | `3.26` |
| `Ground` | `g-care` | Home care suite | `care-room` | `6.10 × 4.58` | `16.70` |
| `Ground` | `g-caregiver` | Caregiver room | `bedroom` | `2.59 × 1.83` | `4.75` |
| `Ground` | `g-drawing` | Drawing room | `drawing-room` | `3.35 × 3.05` | `10.23` |
| `Ground` | `g-family` | Living + dining | `family` | `5.64 × 7.47` | `17.33` |
| `Ground` | `g-kitchen` | Open kitchen | `kitchen` | `3.05 × 4.27` | `11.24` |
| `Ground` | `g-master` | Master bedroom | `bedroom` | `4.58 × 4.42` | `16.40` |
| `Ground` | `g-porch` | Shallow entry porch | `veranda` | `3.35 × 0.92` | `3.08` |
| `Ground` | `g-puja` | Screened puja niche | `pooja` | `1.22 × 0.92` | `1.12` |
| `Ground` | `g-south-lane` | South daylight lane | `veranda` | `1.07 × 3.81` | `4.07` |
| `Ground` | `g-stair` | Corner L stair | `stair` | `3.66 × 3.66` | `6.67` |
| `Ground` | `g-veranda` | Open rear veranda | `veranda` | `6.10 × 1.98` | `10.61` |
| `Ground` | `g-wc` | Caregiver WC | `bathroom` | `1.53 × 1.83` | `2.79` |
| `First` | `u-bath` | Suite 1 attached bath | `bathroom` | `1.53 × 2.14` | `3.26` |
| `First` | `u-bath-2` | Suite 2 attached bath | `bathroom` | `1.53 × 2.14` | `3.26` |
| `First` | `u-living-void` | Living void | `void` | `1.68 × 3.05` | `5.12` |
| `First` | `u-lobby` | Upper family lounge | `living` | `6.86 × 10.06` | `35.06` |
| `First` | `u-master` | Master suite 1 | `bedroom` | `4.58 × 4.42` | `16.40` |
| `First` | `u-master-2` | Master suite 2 | `bedroom` | `5.49 × 5.64` | `19.30` |
| `First` | `u-stair` | L stair arrival | `stair` | `3.66 × 3.66` | `6.67` |
| `First` | `u-study` | Compact home office | `study` | `2.59 × 1.83` | `4.75` |
| `First` | `u-terrace` | Shared open terrace | `terrace` | `3.35 × 1.83` | `6.14` |

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

Plan hash: `fcf63e7d4efaafbd6a2cf3c6a4998a72d76b7b28bfa7a58704e169cd6e79b884` | Geometry hash: `c8ba66f8e766a3dce75e9fd60362f7221693bd3b404c3d2724dc31395993d3b6`
