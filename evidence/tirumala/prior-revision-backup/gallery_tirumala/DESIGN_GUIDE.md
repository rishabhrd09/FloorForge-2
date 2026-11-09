# Tirumala — Design Guide, Coordinate System & Colony Context Register

> **Preliminary Design Disclaimer:** PRELIMINARY - ENGINEER TO REVIEW - NOT FOR CONSTRUCTION

## 1. Site Overview & Confirmed Orientation

- **Project Name:** Tirumala (`id: tirumala`)
- **Plot Classification:** Northeast (NE) corner plot with an **EAST-facing principal entrance** (`road_bearing_deg: 90`).
- **Confirmed Boundaries:**
  - **EAST frontage (Front):** `40 ft 0 in = 12.192 m (12,192 mm)`, running North–South, adjoining the **9.0 m East colony road** and the **basketball-court enclosure & planting** beyond (`E-01`, `N-04`).
  - **WEST boundary (Rear):** `40 ft 0 in = 12.192 m (12,192 mm)`, running North–South.
  - **NORTH boundary (Right):** `50 ft 0 in = 15.240 m (15,240 mm)`, running East–West, adjoining the **12.0 m North colony road**, the **opposite colony garden** (lawn, raised planting kerb, pergola/seating, decorative pots, palms, slim lights), and the **two-storey white/grey house with dark blue-grey vertical facade** beyond (`N-01`, `N-02`, `N-03`).
  - **SOUTH boundary (Left):** `50 ft 0 in = 15.240 m (15,240 mm)`, running East–West.
- **Total Plot Area:** `2,000 sq ft = 185.806 m²`.
- **Confirmed Roadside Utilities:**
  - **Two Electrical Feeder Cabinets:** Outside the plot near its **Northwest (NW) corner** in the North road paver verge (`N-02`): a smaller pale-cream cabinet (`0.78 × 0.48 × 1.22 m`) on the left/east and a taller louvred cabinet (`1.05 × 0.55 × 1.62 m`) on the right/west when viewed from the North road looking Southwest.
  - **Streetlight Pole:** Along the North frontage between the Northeast and Northwest corners (`N-02`, `N-03`).

## 2. Explicit Geographic Coordinate System & FloorForge Transformation

All site geometry, room polygons, road corridors, utility cabinets, and reference cameras are anchored to a single geographic coordinate system:

- **Origin `(0.000, 0.000, 0.000)`:** Southwest (SW) plot corner at Natural Ground Level (`NGL ±0.000 m`).
- **`+X_geo` (Eastward):** `0.000 m` at West boundary $\to$ `15.240 m` (`50 ft`) at East frontage.
- **`+Y_geo` (Northward):** `0.000 m` at South boundary $\to$ `12.192 m` (`40 ft`) at North boundary.
- **`+Z_geo` (Upward):** `0.000 m` at NGL $\to$ `+0.450 m` at Ground Floor Finished Floor Level (`FFL`).

| Plot Corner | Geographic `(X_geo, Y_geo)` (m) | FloorForge Scene `(x_scene, y_scene)` (m) | FloorForge Plan `(x_mm, y_mm)` (mm) |
| :--- | :--- | :--- | :--- |
| **SW Corner** | `(0.000, 0.000)` | `(-1.050, 13.400)` | `(-1050, 13400)` |
| **SE Corner** | `(15.240, 0.000)` | `(-1.050, -1.840)` | `(-1050, -1840)` |
| **NW Corner** | `(0.000, 12.192)` | `(11.142, 13.400)` | `(11142, 13400)` |
| **NE Corner** | `(15.240, 12.192)` | `(11.142, -1.840)` | `(11142, -1840)` |

**Exact Affine Transformation (`road_bearing_deg = 90`):**
- `x_scene = Y_geo - 1.050`  $\iff$  `Y_geo = x_scene + 1.050`
- `y_scene = 13.400 - X_geo` $\iff$  `X_geo = 13.400 - y_scene`
- `z_scene = Z_geo - 0.450`  $\iff$  `Z_geo = z_scene + 0.450`
- Compass bearing $\beta_{\text{geo}}$ (`0°=N, 90°=E, 180°=S, 270°=W`) $\to$ Walker `yaw_rad = atan2(-cos(β), -sin(β))`.

## 3. Care Room Relocation & Northwest Open Pocket Verification

- **Plot East–West Midpoint:** `X_geo = 7.620 m` (`25 ft`, corresponding to `y_local = 5,780 mm` / `y_scene = 5.780 m`).
- **Residential Care Room (`g-care`) Clear Span:** `X_geo` from **`7.800 m` to `13.250 m`** (`Y_geo` from `6.100 m` to `9.600 m`, `19.08 m²`).
- **Residential Care Room (`g-care`) Outer Wall Span:** `X_geo` from **`7.800 m` to `13.250 m`** — **100% east of the `7.620 m` plot midpoint (`strictly_east_of_midpoint = True`)**.
- **Dual-Aspect Sightlines from Care Room:**
  - **Northward (`N-01`):** Two large windows (`1.65 m × 1.95 m` and `1.55 m × 1.95 m`) with `450 mm` low sills (`o-care-n1`, `o-care-n2`) and a `1.15 m` glazed door (`o-care-ver-door`) look across the shaded North veranda (`FFL +0.45 m`), over the low `0.90 m` North road boundary wall (`+0.45 m` above FFL), across the 12 m road into the opposite colony garden, pergola, palms, and house (`N-01`) from reclined (`+1.15 m`), seated (`+1.20 m`), and standing (`+1.63 m`) eye heights.
  - **Eastward (`E-01`):** A `1.80 m × 1.95 m` low-sill East window (`o-care-e`) provides an oblique outlook across the 9 m East road toward the tall pale metal mesh basketball-court enclosure and screening palms/trees (`E-01`).
- **Northwest Caregiver Suite & Open Garden Pocket:**
  - The Caregiver Bedroom (`g-caregiver`, `8.00 m²`) and Attached Toilet (`g-caregiver-bath`, `2.87 m²`) sit in the West/Northwest zone (`X_geo in [2.05, 6.10] m`), directly connected to `g-care` via the sheltered L-shaped North Veranda (`g-veranda`).
  - The Northwest corner of the plot (`x_local in [8700, 11142], y_local in [9800, 13400]` and `x_local in [5350, 8700], y_local in [11500, 13400]`) is preserved as a landscaped open garden pocket with lawn, stepping-stone service path, terracotta planters, and `1.90 m–3.60 m` separation from the West boundary.

## 4. Six Reference Photographs & Camera Presets

| ID | Original Suffix | Bearing | Confidence | Key Reproduced Features |
| :--- | :--- | :--- | :--- | :--- |
| **`N-01`** | `26039` | `2.0°` | `high_cardinal_direction_estimated_offset` | 12 m concrete road in foreground; Opposite raised planting kerb, clipped hedge and manicured colony lawn |
| **`N-02`** | `26040` | `225.0°` | `medium_oblique_southwest_bearing_unmeasured_offsets` | Pair of light-coloured electrical feeder cabinets of differing sizes (smaller left/east, taller right/west); Low brown-grey boundary wall and trimmed green hedge |
| **`N-03`** | `26041` | `180.0°` | `high_southward_cardinal_orientation` | North road concrete carriageway in foreground (East on image-left, West on image-right); Interlocking paver verge, low boundary wall and continuous hedge along plot north frontage |
| **`N-04`** | `26042` | `122.0°` | `provisional_cross_check_unconfirmed_bearing` | Cross-check view from north road looking leftward (east/southeast) toward the junction with the 9 m east road; Paved passage, low boundary wall and corner vegetation |
| **`NE-01`** | `26043` | `222.0°` | `provisional_closeup_pillar_not_survey_corner` | Close-up of weathered masonry pillar with cream/ochre cap, low boundary wall and dense hedge; Interlocking paver footpath/verge and corner palm/shrub planting |
| **`E-01`** | `26044` | `112.0°` | `high_oblique_east_southeast_outlook` | 9 m east road and interlocking paver edge; Raised masonry planting bed and trimmed hedge along court perimeter |

## 5. Room-by-Room Schedule

| Floor | ID | Room Name | Kind | Clear Bounding Size (m) | Clear Area (m²) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Ground` | `g-bath` | Ground Family Bathroom | `bathroom` | `2.20 × 2.00` | `4.40` |
| `Ground` | `g-bedroom` | Ground Family Bedroom | `bedroom` | `2.70 × 4.70` | `12.69` |
| `Ground` | `g-care` | Residential Care Room (Home ICU) | `care-room` | `3.50 × 5.45` | `19.07` |
| `Ground` | `g-caregiver` | Caregiver Bedroom | `bedroom` | `3.20 × 2.50` | `8.00` |
| `Ground` | `g-caregiver-bath` | Caregiver Attached Toilet | `bathroom` | `2.05 × 1.40` | `2.87` |
| `Ground` | `g-kitchen` | Sociable Modular Kitchen | `kitchen` | `2.20 × 2.60` | `5.72` |
| `Ground` | `g-living` | Entrance, Sitting, Living & Dining Hall | `living` | `3.85 × 7.00` | `18.83` |
| `Ground` | `g-puja` | Open Puja Alcove | `pooja` | `2.20 × 0.90` | `1.98` |
| `Ground` | `g-stair` | Staircase | `stair` | `2.20 × 4.10` | `9.02` |
| `Ground` | `g-utility` | Pantry & Utility Room | `utility` | `2.20 × 1.65` | `3.63` |
| `Ground` | `g-veranda` | North L-Shaped Shaded Veranda | `veranda` | `3.40 × 9.80` | `14.84` |
| `First` | `u-balcony-east` | East Front Balcony | `balcony` | `8.70 × 1.35` | `11.74` |
| `First` | `u-bath-north` | First-Floor Principal Bathroom | `bathroom` | `2.20 × 1.65` | `3.63` |
| `First` | `u-bath-south` | First-Floor En-Suite Bathroom | `bathroom` | `2.20 × 2.00` | `4.40` |
| `First` | `u-bed-north` | First-Floor North-East Principal Bedroom | `bedroom` | `3.50 × 4.10` | `14.35` |
| `First` | `u-bed-south` | First-Floor South-West Bedroom | `bedroom` | `2.70 × 4.70` | `12.69` |
| `First` | `u-lobby` | Upper Gallery & Family Lounge | `hall` | `3.85 × 5.65` | `15.59` |
| `First` | `u-office` | Compact Office / Studio | `study` | `3.20 × 2.50` | `8.00` |
| `First` | `u-stair` | Staircase | `stair` | `2.20 × 4.10` | `9.02` |
| `First` | `u-store` | Upper Linen & Utility Store | `store` | `2.20 × 2.30` | `5.06` |
| `First` | `u-terrace-north` | North L-Shaped Terrace | `terrace` | `3.40 × 9.80` | `14.84` |

## 6. Assumptions & Unknowns Requiring Survey Verification

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

Plan hash: `ecec1dcca986058d49251457904d8c3fc5ae4d4d728d34bfdf2c7aa781a0f0e5`
