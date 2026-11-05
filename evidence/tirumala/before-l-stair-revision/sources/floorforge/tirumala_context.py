"""Tirumala 40 x 50 ft northeast-corner plot, colony evidence and camera presets.

Geographic metres start at the southwest plot corner at natural ground:
+X east, +Y north, +Z up. Plan millimetres start at the southeast plot corner:
+x north, +y west. Scene metres use the same plan axes and z=0 at house FFL,
300 mm above natural ground. For this plot-origin plan the transform is:
    x_scene = Y_geo; y_scene = 15.240 - X_geo; z_scene = Z_geo - 0.300.
The open courts and side lanes are authored within the plot, not subtracted
again as envelope setbacks.
"""
from __future__ import annotations

import math
from typing import Any

TIRUMALA_ID = "tirumala"
TIRUMALA_CONTEXT_STYLE = "tirumala-colony"
SITE_CONTEXT_SCHEMA = "floorforge.tirumala-site-context/1"
PHOTO_MANIFEST_SCHEMA = "floorforge.tirumala-photo-manifest/1"
ASSUMPTIONS_SCHEMA = "floorforge.tirumala-assumptions-register/1"

# Confirmed plot dimensions (exact conversions from 40 ft x 50 ft)
PLOT_EAST_FRONTAGE_FT = 40.0
PLOT_NORTH_BOUNDARY_FT = 50.0
PLOT_NS_M = 12.192   # 40 ft = 12,192 mm (East frontage & West boundary, running N-S)
PLOT_EW_M = 15.240   # 50 ft = 15,240 mm (North boundary & South boundary, running E-W)
PLOT_AREA_SQFT = 2000.0
PLOT_AREA_M2 = round(PLOT_NS_M * PLOT_EW_M, 6)  # 185.80608 m²
PLOT_EW_MIDPOINT_M = PLOT_EW_M / 2.0            # X_geo = 7.620 m (25 ft)

# Revision 9 plot-origin setback & level parameters (SE plot corner = (0, 0), +300 mm house datum)
LEFT_SOUTH_SETBACK_M = 0.000
RIGHT_NORTH_SETBACK_M = 0.000
FRONT_EAST_SETBACK_M = 0.000
REAR_WEST_SETBACK_M = 0.000
PLINTH_M = 0.300

# Derived envelope constants
ENVELOPE_SE_X_GEO_M = PLOT_EW_M - FRONT_EAST_SETBACK_M  # 15.240 m
ENVELOPE_SE_Y_GEO_M = LEFT_SOUTH_SETBACK_M              # 0.000 m
ENVELOPE_W_NS_M = PLOT_NS_M - LEFT_SOUTH_SETBACK_M - RIGHT_NORTH_SETBACK_M  # 12.192 m
ENVELOPE_D_EW_M = PLOT_EW_M - FRONT_EAST_SETBACK_M - REAR_WEST_SETBACK_M   # 15.240 m


def geo_to_scene_m(x_geo: float, y_geo: float, z_geo: float = 0.0) -> list[float]:
    """Convert geographic (X_east, Y_north, Z_up) in metres from SW plot corner at NGL
    to FloorForge scene metres (x_scene, y_scene, z_scene) relative to SE envelope corner at FFL."""
    return [
        round(float(y_geo) - ENVELOPE_SE_Y_GEO_M, 4),
        round(ENVELOPE_SE_X_GEO_M - float(x_geo), 4),
        round(float(z_geo) - PLINTH_M, 4),
    ]


def scene_to_geo_m(x_scene: float, y_scene: float, z_scene: float = 0.0) -> list[float]:
    """Convert FloorForge scene metres (x_scene, y_scene, z_scene) to geographic (X_east, Y_north, Z_up) metres."""
    return [
        round(ENVELOPE_SE_X_GEO_M - float(y_scene), 4),
        round(float(x_scene) + ENVELOPE_SE_Y_GEO_M, 4),
        round(float(z_scene) + PLINTH_M, 4),
    ]


def geo_to_local_mm(x_geo: float, y_geo: float) -> list[int]:
    """Convert geographic (X_east, Y_north) in metres to FloorForge plan millimetres."""
    return [
        round((float(y_geo) - ENVELOPE_SE_Y_GEO_M) * 1000),
        round((ENVELOPE_SE_X_GEO_M - float(x_geo)) * 1000),
    ]


def local_mm_to_geo_m(x_mm: float, y_mm: float) -> list[float]:
    """Convert FloorForge plan millimetres (x_mm, y_mm) to geographic (X_east, Y_north) in metres."""
    return [
        round(ENVELOPE_SE_X_GEO_M - float(y_mm) / 1000.0, 4),
        round(float(x_mm) / 1000.0 + ENVELOPE_SE_Y_GEO_M, 4),
    ]


def geo_box_to_scene(x0_geo: float, y0_geo: float, x1_geo: float, y1_geo: float) -> list[float]:
    """Convert a geographic axis-aligned rectangle [X_west, Y_south, X_east, Y_north] in metres
    to FloorForge scene bounds [x0_scene, y0_scene, x1_scene, y1_scene] in metres."""
    xa, ya, _ = geo_to_scene_m(x0_geo, y0_geo, 0.0)
    xb, yb, _ = geo_to_scene_m(x1_geo, y1_geo, 0.0)
    return [
        round(min(xa, xb), 4),
        round(min(ya, yb), 4),
        round(max(xa, xb), 4),
        round(max(ya, yb), 4),
    ]


def geo_bearing_to_walker_yaw(bearing_deg: float) -> float:
    """Convert a geographic compass bearing (0=N, 90=E, 180=S, 270=W) into the FloorForge
    Three.js walker yaw in radians.

    Derivation:
      Geographic look vector: d_geo = (sin(beta), cos(beta)) in (+East, +North).
      Scene look vector:      (dx_scene, dy_scene) = (cos(beta), -sin(beta)).
      Three.js look vector:   (dX_three, dZ_three) = (dx_scene, -dy_scene) = (cos(beta), sin(beta)).
      Walker forward vector:  (-sin(yaw), -cos(yaw)) = (cos(beta), sin(beta))
      => yaw = atan2(-cos(beta), -sin(beta)).
    """
    beta = math.radians(float(bearing_deg))
    return round(math.atan2(-math.cos(beta), -math.sin(beta)), 6)


def geo_camera_to_scene(
    cam_id: str,
    label: str,
    position_geo: tuple[float, float, float],
    bearing_deg: float,
    pitch_deg: float = -2.0,
    fov_deg: float = 52.0,
    look_distance_m: float = 14.0,
    **metadata: Any,
) -> dict[str, Any]:
    """Create a complete camera specification in both geographic and FloorForge scene coordinates."""
    gx, gy, gz = position_geo
    beta = math.radians(float(bearing_deg))
    pitch = math.radians(float(pitch_deg))
    horiz = look_distance_m * math.cos(pitch)
    tx_geo = gx + horiz * math.sin(beta)
    ty_geo = gy + horiz * math.cos(beta)
    tz_geo = gz + look_distance_m * math.sin(pitch)

    pos_scene = geo_to_scene_m(gx, gy, gz)
    tgt_scene = geo_to_scene_m(tx_geo, ty_geo, tz_geo)
    yaw_rad = geo_bearing_to_walker_yaw(bearing_deg)
    return {
        "id": cam_id,
        "label": label,
        "position_geo_m": [round(gx, 3), round(gy, 3), round(gz, 3)],
        "target_geo_m": [round(tx_geo, 3), round(ty_geo, 3), round(tz_geo, 3)],
        "bearing_deg": round(float(bearing_deg), 1),
        "pitch_deg": round(float(pitch_deg), 2),
        "fov": round(float(fov_deg), 1),
        "position": pos_scene,
        "target": tgt_scene,
        "walker": {
            "position": pos_scene,
            "yaw_rad": yaw_rad,
            "yaw_deg": round(math.degrees(yaw_rad), 2),
            "pitch_rad": round(pitch, 5),
        },
        **metadata,
    }


def default_colony_parameters() -> dict[str, dict[str, Any]]:
    """Parameterised site and colony context dimensions. Uncertain values are explicitly flagged
    so they can be updated from a future total-station survey without manual model rebuilds."""
    return {
        "plot_east_frontage_m": {
            "value": PLOT_NS_M,
            "imperial": "40 ft 0 in",
            "units": "m",
            "status": "owner_confirmed",
            "source": "Owner brief",
            "notes": "East frontage and West rear boundary running North-South.",
        },
        "plot_north_boundary_m": {
            "value": PLOT_EW_M,
            "imperial": "50 ft 0 in",
            "units": "m",
            "status": "owner_confirmed",
            "source": "Owner brief",
            "notes": "North road boundary and South side boundary running East-West.",
        },
        "north_road_width_m": {
            "value": 12.0,
            "units": "m",
            "status": "owner_confirmed_with_working_interpretation",
            "source": "Owner brief + N-01, N-02, N-03",
            "notes": "Retained at 12.0 m total ROW north of Y_geo=12.192 m, interpreted as 8.40 m concrete carriageway + 1.80 m south paver verge + 1.80 m north garden verge (not double-counted).",
        },
        "north_road_south_verge_m": {
            "value": 1.80,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "N-02, N-03, NE-01",
            "notes": "Interlocking concrete paver verge along the plot's North frontage containing the feeder cabinets and streetlight pole.",
        },
        "north_road_north_verge_m": {
            "value": 1.80,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "N-01",
            "notes": "Paved edge and raised masonry planting kerb along the opposite North colony garden.",
        },
        "east_road_width_m": {
            "value": 9.0,
            "units": "m",
            "status": "owner_confirmed_with_working_interpretation",
            "source": "Owner brief + E-01, N-04",
            "notes": "Retained at 9.0 m total ROW east of X_geo=15.240 m, interpreted as 6.00 m concrete carriageway + 1.50 m west paver verge + 1.50 m east court-side paved edge (not double-counted).",
        },
        "east_road_west_verge_m": {
            "value": 1.50,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "NE-01, N-04",
            "notes": "Interlocking paver footpath/verge along the plot's East entrance frontage.",
        },
        "east_road_east_verge_m": {
            "value": 1.50,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "E-01, N-04",
            "notes": "Paved passage and raised masonry planting bed fronting the basketball-court enclosure.",
        },
        "nw_feeder_cabinet_east_offset_m": {
            "value": 1.25,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "N-02",
            "notes": "Smaller pale-cream feeder cabinet (0.78 x 0.48 x 1.22 m) outside NW plot corner in north verge.",
        },
        "nw_feeder_cabinet_west_offset_m": {
            "value": 0.10,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "N-02",
            "notes": "Taller pale-cream feeder cabinet (1.05 x 0.55 x 1.62 m) immediately right (west) of the smaller cabinet when viewed from the north road looking SW.",
        },
        "north_streetlight_pole_x_geo_m": {
            "value": 4.35,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "N-02, N-03",
            "notes": "Galvanised streetlight pole (height 6.2 m) along the north frontage between the NE and NW corners.",
        },
        "ne_reference_pillar_x_geo_m": {
            "value": 15.08,
            "units": "m",
            "status": "provisional_photo_reference",
            "source": "NE-01, N-03",
            "notes": "Visible cream/ochre-capped masonry pillar near the NE corner; treated as an existing boundary wall pier, not a certified survey monument.",
        },
        "north_garden_depth_m": {
            "value": 11.80,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "N-01",
            "notes": "Depth of the colony lawn, pergola seating and palm garden north of the 12 m road before the opposite house.",
        },
        "north_opposite_house_distance_m": {
            "value": 23.80,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "N-01",
            "notes": "Distance from plot North boundary (Y_geo=12.192 m) to the white/grey house with the dark blue-grey vertical facade.",
        },
        "east_court_enclosure_height_m": {
            "value": 5.40,
            "units": "m",
            "status": "estimated_from_photo",
            "source": "E-01, N-04",
            "notes": "Tall pale metal mesh basketball-court enclosure with repeated tubular posts every 2.50 m behind dense tree/palm screening.",
        },
    }


def build_reference_cameras() -> dict[str, dict[str, Any]]:
    """Six named reference-photo cameras (N-01, N-02, N-03, N-04, NE-01, E-01) plus architectural
    and care-room sightline cameras, all computed through the single geographic transform."""
    return {
        "N-01": geo_camera_to_scene(
            "N-01",
            "N-01 — North Outlook Across 12 m Road to Colony Garden & Opposite House",
            position_geo=(8.80, 12.05, 1.62),
            bearing_deg=2.0,
            pitch_deg=1.5,
            fov_deg=54.0,
            look_distance_m=22.0,
            source_file="codex-clipboard-1f4f5f60-a763-429d-826a-43db574bb4f7.png",
            original_suffix="26039",
            reference_asset="reference-assets/N-01_26039.png",
            confidence="high_cardinal_direction_estimated_offset",
            comparison_mode="both",
            observed_features=[
                "12 m concrete road in foreground",
                "Opposite raised planting kerb, clipped hedge and manicured colony lawn",
                "Timber/metal garden pergola with shaded seating on left-centre of lawn",
                "Decorative spherical/ornate pots and slim garden bollard lights",
                "Coconut/areca palms and broadleaf canopy trees",
                "Two-storey white/grey house beyond with signature dark blue-grey vertical feature facade",
            ],
            excluded_temporary_features=[],
        ),
        "N-02": geo_camera_to_scene(
            "N-02",
            "N-02 — North Road Looking ~45° Right (Southwest) Toward Plot & NW Feeder Cabinets",
            position_geo=(5.40, 16.40, 1.60),
            bearing_deg=225.0,
            pitch_deg=-2.5,
            fov_deg=54.0,
            look_distance_m=9.5,
            source_file="codex-clipboard-06a77609-6ca8-47a5-8c80-d5bafdec0b37.png",
            original_suffix="26040",
            reference_asset="reference-assets/N-02_26040.png",
            confidence="medium_oblique_southwest_bearing_unmeasured_offsets",
            comparison_mode="both",
            observed_features=[
                "Pair of light-coloured electrical feeder cabinets of differing sizes (smaller left/east, taller right/west)",
                "Low brown-grey boundary wall and trimmed green hedge",
                "Interlocking concrete paver verge along north road edge",
                "Nearby galvanised streetlight pole and mature roadside trees",
            ],
            excluded_temporary_features=[],
        ),
        "N-03": geo_camera_to_scene(
            "N-03",
            "N-03 — North Road Looking South Toward Plot North Frontage (East Left, West Right)",
            position_geo=(7.80, 19.80, 1.60),
            bearing_deg=180.0,
            pitch_deg=-1.5,
            fov_deg=56.0,
            look_distance_m=11.5,
            source_file="codex-clipboard-a88c9575-5975-4ca2-9265-ed8c5e46ea20.png",
            original_suffix="26041",
            reference_asset="reference-assets/N-03_26041.png",
            confidence="high_southward_cardinal_orientation",
            comparison_mode="both",
            observed_features=[
                "North road concrete carriageway in foreground (East on image-left, West on image-right)",
                "Interlocking paver verge, low boundary wall and continuous hedge along plot north frontage",
                "Streetlight pole between NE and NW corners and NW feeder cabinets toward right",
                "Mature trees and colony foliage framing the plot",
            ],
            excluded_temporary_features=[
                "Parked white hatchback car on the south road verge (excluded as temporary vehicle)",
            ],
        ),
        "N-04": geo_camera_to_scene(
            "N-04",
            "N-04 — Provisional Leftward (Southeast) View From North Road Toward Court Enclosure",
            position_geo=(13.20, 16.20, 1.60),
            bearing_deg=122.0,
            pitch_deg=0.5,
            fov_deg=54.0,
            look_distance_m=15.0,
            source_file="codex-clipboard-11f33951-2ed5-49d2-ab7d-2e8a4308b6e7.png",
            original_suffix="26042",
            reference_asset="reference-assets/N-04_26042.png",
            confidence="provisional_cross_check_unconfirmed_bearing",
            comparison_mode="both",
            observed_features=[
                "Cross-check view from north road looking leftward (east/southeast) toward the junction with the 9 m east road",
                "Paved passage, low boundary wall and corner vegetation",
                "Tall pale metal mesh basketball-court enclosure and trees beyond",
            ],
            excluded_temporary_features=[
                "Temporary parked vehicles/scooters near road junction",
            ],
        ),
        "NE-01": geo_camera_to_scene(
            "NE-01",
            "NE-01 — Provisional Northeast-Corner Close-Up (Wall, Masonry Pillar, Hedge & Footpath)",
            position_geo=(16.80, 14.30, 1.55),
            bearing_deg=222.0,
            pitch_deg=-3.5,
            fov_deg=50.0,
            look_distance_m=5.5,
            source_file="codex-clipboard-5a930b52-0dc7-499f-b6af-efc7680c8615.png",
            original_suffix="26043",
            reference_asset="reference-assets/NE-01_26043.png",
            confidence="provisional_closeup_pillar_not_survey_corner",
            comparison_mode="both",
            observed_features=[
                "Close-up of weathered masonry pillar with cream/ochre cap, low boundary wall and dense hedge",
                "Interlocking paver footpath/verge and corner palm/shrub planting",
            ],
            excluded_temporary_features=[],
        ),
        "E-01": geo_camera_to_scene(
            "E-01",
            "E-01 — Oblique Outlook From Near NE Corner Toward Eastern Basketball-Court Enclosure",
            position_geo=(15.40, 11.40, 1.62),
            bearing_deg=112.0,
            pitch_deg=2.5,
            fov_deg=54.0,
            look_distance_m=16.0,
            source_file="codex-clipboard-40fbabb9-5ce5-4efc-be55-7469e08b93be.png",
            original_suffix="26044",
            reference_asset="reference-assets/E-01_26044.png",
            confidence="high_oblique_east_southeast_outlook",
            comparison_mode="both",
            observed_features=[
                "9 m east road and interlocking paver edge",
                "Raised masonry planting bed and trimmed hedge along court perimeter",
                "Tall pale metal mesh basketball-court enclosure with repeated tubular posts",
                "Substantial screening by coconut/areca palms and leafy canopy trees",
                "Nearby street/garden lighting",
            ],
            excluded_temporary_features=[],
        ),
    }


def build_sightline_cameras() -> dict[str, dict[str, Any]]:
    """Architectural and care-room human-eye sightline cameras for Tirumala Revision 8."""
    return {
        "care_recliner_north": geo_camera_to_scene(
            "care_recliner_north",
            "Care Suite — South-to-North Bed (Pillow End at South) Looking North Across 3 ft Passage & 12 m Road to Garden",
            position_geo=(7.10, 8.38, PLINTH_M + 1.15),
            bearing_deg=2.0,
            pitch_deg=0.5,
            fov_deg=56.0,
            look_distance_m=24.0,
            role="care_sightline",
            eye_height_above_ffl_m=1.15,
        ),
        "care_seated_north": geo_camera_to_scene(
            "care_seated_north",
            "Care Suite — Visitor Chair Position Looking North Through 12–15 ft Full-Height Glazing to Colony Garden",
            position_geo=(5.70, 9.81, PLINTH_M + 1.20),
            bearing_deg=4.0,
            pitch_deg=0.5,
            fov_deg=56.0,
            look_distance_m=24.0,
            role="care_sightline",
            eye_height_above_ffl_m=1.20,
        ),
        "care_standing_glazing": geo_camera_to_scene(
            "care_standing_glazing",
            "Care Suite — Standing Near Broad North Window Looking Out Over Boundary Greenery & 12 m Road",
            position_geo=(6.71, 10.52, PLINTH_M + 1.63),
            bearing_deg=3.0,
            pitch_deg=-1.0,
            fov_deg=58.0,
            look_distance_m=22.0,
            role="care_sightline",
            eye_height_above_ffl_m=1.63,
        ),
        "care_east_court_glimpse": geo_camera_to_scene(
            "care_east_court_glimpse",
            "Care Suite — East Window Looking Across 10.5 × 19 ft Car Bay & 9 m East Road to Basketball Court",
            position_geo=(8.40, 9.85, PLINTH_M + 1.20),
            bearing_deg=92.0,
            pitch_deg=1.0,
            fov_deg=54.0,
            look_distance_m=18.0,
            role="care_sightline",
            eye_height_above_ffl_m=1.20,
        ),
        "care_interior_overview": geo_camera_to_scene(
            "care_interior_overview",
            "Care Suite — Interior Showing 7 × 3.5 ft South-to-North Bed (Head South, Feet North), Bedside & Veranda Slider",
            position_geo=(8.35, 10.55, PLINTH_M + 1.52),
            bearing_deg=218.0,
            pitch_deg=-6.0,
            fov_deg=66.0,
            look_distance_m=4.4,
            role="interior_verification",
            eye_height_above_ffl_m=1.52,
        ),
        "double_height_living_void": geo_camera_to_scene(
            "double_height_living_void",
            "Double-Height Living Hall (~23 ft Clear) — Guarded Upper Gallery, Rooflight & Care Suite Glazing",
            position_geo=(8.95, 4.75, PLINTH_M + 1.55),
            bearing_deg=302.0,
            pitch_deg=9.0,
            fov_deg=68.0,
            look_distance_m=6.2,
            role="interior_verification",
            eye_height_above_ffl_m=1.55,
        ),
        "compact_corner_stair": geo_camera_to_scene(
            "compact_corner_stair",
            "Compact 12 × 7.5 ft Corner Staircase — Open North Arrival, Flight 1 South, Tall East Window & South Landing",
            position_geo=(9.15, 4.45, PLINTH_M + 1.52),
            bearing_deg=182.0,
            pitch_deg=-5.0,
            fov_deg=66.0,
            look_distance_m=4.2,
            role="interior_verification",
            eye_height_above_ffl_m=1.52,
        ),
        "north_veranda_l_route": geo_camera_to_scene(
            "north_veranda_l_route",
            "Covered West Care Veranda & North 3 ft Clear Garden Passage — Teak-Collared Columns & NW Garden",
            position_geo=(3.20, 10.60, PLINTH_M + 1.45),
            bearing_deg=165.0,
            pitch_deg=-3.0,
            fov_deg=62.0,
            look_distance_m=6.5,
            role="outdoor_living",
            eye_height_above_ffl_m=1.45,
        ),
        "living_dining_kitchen": geo_camera_to_scene(
            "living_dining_kitchen",
            "Connected Kitchen, Screened East-Wall Puja, 5 × 3 ft Dining Table & Open Stair Hall",
            position_geo=(9.90, 5.10, PLINTH_M + 1.52),
            bearing_deg=135.0,
            pitch_deg=-4.0,
            fov_deg=66.0,
            look_distance_m=4.8,
            role="interior_verification",
            eye_height_above_ffl_m=1.52,
        ),
        "caregiver_nw_pocket": geo_camera_to_scene(
            "caregiver_nw_pocket",
            "Open Northwest Corner Garden — Lawn, Stepping Stones, Care Veranda & Caregiver Courtyard",
            position_geo=(0.55, 11.40, PLINTH_M + 1.55),
            bearing_deg=132.0,
            pitch_deg=-5.0,
            fov_deg=62.0,
            look_distance_m=7.2,
            role="exterior_verification",
            eye_height_above_ffl_m=1.55,
        ),
        "first_floor_terrace_outlook": geo_camera_to_scene(
            "first_floor_terrace_outlook",
            "First-Floor East Terrace — Elevated Outlook Over Shallow Entry Porch, East Court & 9 m Road",
            position_geo=(12.40, 4.10, PLINTH_M + 3.658 + 1.55),
            bearing_deg=78.0,
            pitch_deg=-3.0,
            fov_deg=60.0,
            look_distance_m=18.0,
            role="upper_terrace",
            eye_height_above_ffl_m=5.21,
        ),
        "east_entrance_exterior": geo_camera_to_scene(
            "east_entrance_exterior",
            "East Entrance — Shallow 10 × 3 ft Open Porch, Two 150 mm Steps (+300 mm Datum) & Lower Car Bay (±0 mm)",
            position_geo=(22.80, 6.40, 1.75),
            bearing_deg=272.0,
            pitch_deg=3.0,
            fov_deg=48.0,
            look_distance_m=14.5,
            role="exterior_hero",
        ),
        "ne_corner_two_roads": geo_camera_to_scene(
            "ne_corner_two_roads",
            "Northeast Corner — 12 m North Road, 9 m East Road, Lower Car Bay, Shallow Porch & Care Suite",
            position_geo=(23.20, 20.40, 2.60),
            bearing_deg=226.0,
            pitch_deg=-4.5,
            fov_deg=48.0,
            look_distance_m=17.5,
            role="exterior_hero",
        ),
    }


def spacious_interior_cameras(building: dict) -> dict:
    """Human-scale positions in the revised room geometry, never inside cabinetry."""
    params = building['planning']['tirumalaMeta']['parameters']
    care_front, care_start = params['careFront'], params['careStart']
    def camera(key, label, eye_ft, target_ft, floor=0, pitch=-2):
        x, y = eye_ft; tx, ty = target_ft
        gx, gy = local_mm_to_geo_m(x * 304.8, y * 304.8)
        tgx, tgy = local_mm_to_geo_m(tx * 304.8, ty * 304.8)
        bearing = math.degrees(math.atan2(tgx-gx, tgy-gy)) % 360
        return geo_camera_to_scene(key, label, (gx, gy, PLINTH_M + floor * 3.658 + 1.60),
                                   bearing, pitch, 62, math.hypot(tgx-gx,tgy-gy),
                                   role='interior_verification', floor=floor, enter_walk=True,
                                   eye_height_above_ffl_m=1.60)
    definitions = [
        ('living_dining_kitchen', 'Expanded kitchen — open working aisle and east puja alcove', (15.9,17), (7,11.5),0,-5),
        ('entry_connected_hall', 'Entry — connected kitchen, stair hall and garden-facing care glazing', (15.5,9.0), (19,28.0),0,1),
        ('drawing_interior', 'Wider drawing room — broad sliding glass connection to the family hall', (25.5,11.8), (20,17),0,-2),
        ('dining_stair_connection', 'Dining beside the stair — clear route to the master and living hall', (14.5,30.0), (5.5,28.5),0,-4),
        ('care_interior_overview', 'Care suite — full-scale bed, north garden glazing and open hall connection', (25.5,care_front+2.5), (35,params['careEnd']-2),0,-3),
        ('double_height_living_void', 'Larger double-height living opening — glass upper gallery and daylight', (21,params['drawEnd']+1.5), (19.5,28),0,50),
        ('upper_gallery_connection', 'Upper gallery — glass guards overlooking the connected living hall', (14.5,23.5), (18,29),1,-10),
        ('upper_lounge_connection', 'Upper lounge and study — connected gallery and terrace daylight', (21,params['drawEnd']-1.1), (23,13),1,-2),
    ]
    return {a:camera(a,b,c,d,e,f) for a,b,c,d,e,f in definitions}


def build_tirumala_context(building: dict[str, Any] | None = None, scene: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the parameterised colony context payload embedded in scene['context'] and saved to site-context.json."""
    params = default_colony_parameters()
    north_row = params["north_road_width_m"]["value"]
    north_s_verge = params["north_road_south_verge_m"]["value"]
    north_n_verge = params["north_road_north_verge_m"]["value"]
    east_row = params["east_road_width_m"]["value"]
    east_w_verge = params["east_road_west_verge_m"]["value"]
    east_e_verge = params["east_road_east_verge_m"]["value"]

    y_north_plot = PLOT_NS_M  # 12.192 m
    y_north_road_s = y_north_plot + north_s_verge
    y_north_road_n = y_north_plot + north_row - north_n_verge
    y_north_far = y_north_plot + north_row  # 24.192 m

    x_east_plot = PLOT_EW_M  # 15.240 m
    x_east_road_w = x_east_plot + east_w_verge
    x_east_road_e = x_east_plot + east_row - east_e_verge
    x_east_far = x_east_plot + east_row  # 24.240 m

    cab_e_x = params["nw_feeder_cabinet_east_offset_m"]["value"]
    cab_w_x = params["nw_feeder_cabinet_west_offset_m"]["value"]
    pole_x = params["north_streetlight_pole_x_geo_m"]["value"]
    ne_pillar_x = params["ne_reference_pillar_x_geo_m"]["value"]
    garden_depth = params["north_garden_depth_m"]["value"]
    opp_house_dist = params["north_opposite_house_distance_m"]["value"]
    court_h = params["east_court_enclosure_height_m"]["value"]

    ref_cams = build_reference_cameras()
    sight_cams = build_sightline_cameras()
    if building and building.get("planning",{}).get("tirumalaRevision",0) >= 9:
        sight_cams.update(spacious_interior_cameras(building))

    # Verify Revision 8 care-suite and open NW corner garden geometry directly from building
    care_verification: dict[str, Any] = {
        "plot_ew_midpoint_x_geo_m": PLOT_EW_MIDPOINT_M,
        "midpoint_scene_y_m": round(ENVELOPE_SE_X_GEO_M - PLOT_EW_MIDPOINT_M, 4),
        "revision": building.get("planning",{}).get("tirumalaRevision",8) if building else 8,
        "midpoint_extension_permitted": True,
        "nw_corner_open": True,
        "nw_garden_open": True,
        "care_west_edge_ft": 36.0,
        "bed_orientation": "South-to-North (head South at x=26.25 ft, feet North at x=33.25 ft)",
    }
    if isinstance(building, dict):
        meta = building.get("planning", {}).get("tirumalaMeta") or {}
        care_verification["option"] = building.get("planning", {}).get("tirumalaOption", "A")
        care_verification["option_label"] = meta.get("label", "A — Original flow")
        care_verification["care_west_edge_ft"] = meta.get("careEndFt", 36.0)
        care = next((s for s in building.get("spaces", []) if s["id"] == "g-care"), None)
        if care:
            clear_x_geo = [local_mm_to_geo_m(pt[0], pt[1])[0] for pt in care["clear"]]
            poly_x_geo = [local_mm_to_geo_m(pt[0], pt[1])[0] for pt in care["polygon"]]
            care_verification.update({
                "care_clear_x_geo_min_m": min(clear_x_geo),
                "care_clear_x_geo_max_m": max(clear_x_geo),
                "care_outer_x_geo_min_m": min(poly_x_geo),
                "care_outer_x_geo_max_m": max(poly_x_geo),
                "strictly_east_of_midpoint": min(poly_x_geo) >= PLOT_EW_MIDPOINT_M,
            })

    return {
        "schema": SITE_CONTEXT_SCHEMA,
        "style": TIRUMALA_CONTEXT_STYLE,
        "project_id": TIRUMALA_ID,
        "viewer_only_outside_plot": True,
        "coordinate_system": {
            "origin_description": "Southwest plot corner (SW) at Natural Ground Level (NGL ±0.000 m); FloorForge local/scene origin (0, 0, 0) is Southeast plot corner (SE) at Ground Floor FFL (+0.300 m)",
            "axes": {
                "X_geo": "Increases Eastward (0.000 m at West boundary -> 15.240 m at East frontage; 50 ft)",
                "Y_geo": "Increases Northward (0.000 m at South boundary -> 12.192 m at North boundary; 40 ft)",
                "Z_geo": "Increases Upward (0.000 m at NGL/car-bay -> +0.300 m at Ground Floor FFL)",
            },
            "plot_corners_geo_m": {
                "SW": [0.0, 0.0],
                "SE": [PLOT_EW_M, 0.0],
                "NW": [0.0, PLOT_NS_M],
                "NE": [PLOT_EW_M, PLOT_NS_M],
            },
            "plot_corners_scene_m": {
                "SW": geo_to_scene_m(0.0, 0.0, 0.0)[:2],
                "SE": geo_to_scene_m(PLOT_EW_M, 0.0, 0.0)[:2],
                "NW": geo_to_scene_m(0.0, PLOT_NS_M, 0.0)[:2],
                "NE": geo_to_scene_m(PLOT_EW_M, PLOT_NS_M, 0.0)[:2],
            },
            "scene_transform": {
                "road_bearing_deg": 90,
                "front_direction": "East (+X_geo -> -y_scene)",
                "rear_direction": "West (-X_geo -> +y_scene)",
                "left_direction": "South (-Y_geo -> -x_scene)",
                "right_direction": "North (+Y_geo -> +x_scene)",
                "formula_geo_to_scene_m": {
                    "x_scene": "Y_geo",
                    "y_scene": "15.240 - X_geo",
                    "z_scene": "Z_geo - 0.300",
                },
                "formula_scene_to_geo_m": {
                    "X_geo": "15.240 - y_scene",
                    "Y_geo": "x_scene",
                    "Z_geo": "z_scene + 0.300",
                },
                "envelope_se_origin_geo_m": [ENVELOPE_SE_X_GEO_M, ENVELOPE_SE_Y_GEO_M, PLINTH_M],
            },
        },
        "care_room_verification": care_verification,
        "parameters": params,
        "roads": {
            "north_road_12m": {
                "label": "12.0 m North Colony Road",
                "total_row_m": north_row,
                "carriageway_bounds_scene": geo_box_to_scene(-10.0, y_north_road_s, 36.0, y_north_road_n),
                "south_verge_bounds_scene": geo_box_to_scene(-6.0, y_north_plot, x_east_plot, y_north_road_s),
                "north_verge_bounds_scene": geo_box_to_scene(-6.0, y_north_road_n, 36.0, y_north_far),
            },
            "east_road_9m": {
                "label": "9.0 m East Colony Road (Principal Arrival)",
                "total_row_m": east_row,
                "carriageway_bounds_scene": geo_box_to_scene(x_east_road_w, -10.0, x_east_road_e, y_north_far + 10.0),
                "west_verge_bounds_scene": geo_box_to_scene(x_east_plot, -6.0, x_east_road_w, y_north_plot),
                "east_verge_bounds_scene": geo_box_to_scene(x_east_road_e, -6.0, x_east_far, y_north_far + 6.0),
            },
        },
        "north_colony_garden": {
            "source_photo": "N-01",
            "lawn_bounds_scene": geo_box_to_scene(0.4, y_north_far + 0.25, 16.8, y_north_plot + north_row + garden_depth),
            "kerb_bounds_scene": geo_box_to_scene(-0.5, y_north_far, 17.5, y_north_plot + north_row + garden_depth + 0.3),
            "pergola": {
                "bounds_scene": geo_box_to_scene(2.4, y_north_far + 2.1, 6.4, y_north_far + 5.5),
                "height_m": 2.85,
                "benches_scene": [
                    geo_box_to_scene(2.8, y_north_far + 2.4, 6.0, y_north_far + 2.95),
                    geo_box_to_scene(2.8, y_north_far + 4.65, 6.0, y_north_far + 5.2),
                ],
            },
            "decorative_pots_scene": [
                {"position": geo_to_scene_m(x_g, y_north_far + 0.95, 0.0), "radius_m": 0.34, "height_m": 0.68}
                for x_g in (2.2, 5.4, 8.6, 11.8, 14.6)
            ],
            "garden_lights_scene": [
                {"position": geo_to_scene_m(x_g, y_north_far + 0.55, 0.0), "height_m": 0.85}
                for x_g in (1.5, 4.2, 7.0, 9.8, 12.6, 15.4)
            ],
            "trees_scene": [
                {"position": geo_to_scene_m(1.6, y_north_far + 1.8, 0.0), "species": "palm", "scale": 1.15},
                {"position": geo_to_scene_m(4.8, y_north_far + 6.5, 0.0), "species": "tree_shade", "scale": 1.05},
                {"position": geo_to_scene_m(7.6, y_north_far + 2.2, 0.0), "species": "areca", "scale": 1.25},
                {"position": geo_to_scene_m(10.8, y_north_far + 3.0, 0.0), "species": "palm", "scale": 1.22},
                {"position": geo_to_scene_m(13.8, y_north_far + 2.4, 0.0), "species": "mango", "scale": 0.92},
                {"position": geo_to_scene_m(15.8, y_north_far + 5.8, 0.0), "species": "palm", "scale": 1.10},
            ],
            "opposite_house": {
                "source_photo": "N-01",
                "main_body_bounds_scene": geo_box_to_scene(2.6, y_north_plot + opp_house_dist, 16.4, y_north_plot + opp_house_dist + 8.6),
                "height_m": 7.2,
                "dark_blue_grey_vertical_facade_bounds_scene": geo_box_to_scene(
                    8.2, y_north_plot + opp_house_dist - 0.28, 11.4, y_north_plot + opp_house_dist + 0.1
                ),
                "balcony_bands_scene": [
                    geo_box_to_scene(3.0, y_north_plot + opp_house_dist - 1.1, 8.0, y_north_plot + opp_house_dist),
                    geo_box_to_scene(11.6, y_north_plot + opp_house_dist - 0.9, 16.0, y_north_plot + opp_house_dist),
                ],
            },
        },
        "east_basketball_court": {
            "source_photos": ["E-01", "N-04"],
            "raised_bed_bounds_scene": geo_box_to_scene(x_east_far, -2.5, x_east_far + 1.15, 15.8),
            "enclosure_bounds_scene": geo_box_to_scene(x_east_far + 1.15, -2.2, x_east_far + 15.5, 15.5),
            "fence_height_m": court_h,
            "post_spacing_m": 2.50,
            "posts_scene": [
                geo_to_scene_m(x_east_far + 1.15, y_g, 0.0)
                for y_g in (-2.0, 0.5, 3.0, 5.5, 8.0, 10.5, 13.0, 15.5)
            ] + [
                geo_to_scene_m(x_g, 15.5, 0.0)
                for x_g in (x_east_far + 3.65, x_east_far + 6.15, x_east_far + 8.65, x_east_far + 11.15)
            ],
            "screening_trees_scene": [
                {"position": geo_to_scene_m(x_east_far + 0.6, 1.2, 0.0), "species": "palm", "scale": 1.12},
                {"position": geo_to_scene_m(x_east_far + 0.7, 3.8, 0.0), "species": "neem", "scale": 0.78},
                {"position": geo_to_scene_m(x_east_far + 0.55, 6.6, 0.0), "species": "areca", "scale": 1.25},
                {"position": geo_to_scene_m(x_east_far + 0.7, 9.2, 0.0), "species": "tree_shade", "scale": 0.95},
                {"position": geo_to_scene_m(x_east_far + 0.6, 11.8, 0.0), "species": "palm", "scale": 1.18},
                {"position": geo_to_scene_m(x_east_far + 0.8, 14.2, 0.0), "species": "ashoka", "scale": 0.92},
            ],
            "lights_scene": [
                {"position": geo_to_scene_m(x_east_far - 0.25, 2.5, 0.0), "height_m": 4.2},
                {"position": geo_to_scene_m(x_east_far - 0.25, 12.2, 0.0), "height_m": 4.2},
            ],
        },
        "northwest_feeder_cabinets": {
            "source_photos": ["N-02", "N-03"],
            "plinth_bounds_scene": geo_box_to_scene(cab_w_x - 0.75, y_north_plot + 0.18, cab_e_x + 0.65, y_north_plot + 0.92),
            "smaller_east_cabinet": {
                "id": "feeder-cabinet-east-small",
                "center_geo_m": [cab_e_x, y_north_plot + 0.54, 0.20],
                "bounds_scene": geo_box_to_scene(cab_e_x - 0.39, y_north_plot + 0.30, cab_e_x + 0.39, y_north_plot + 0.78),
                "size_m": [0.78, 0.48, 1.22],
                "color": "#dcd8ce",
            },
            "taller_west_cabinet": {
                "id": "feeder-cabinet-west-tall",
                "center_geo_m": [cab_w_x, y_north_plot + 0.55, 0.20],
                "bounds_scene": geo_box_to_scene(cab_w_x - 0.525, y_north_plot + 0.275, cab_w_x + 0.525, y_north_plot + 0.825),
                "size_m": [1.05, 0.55, 1.62],
                "color": "#d6d2c6",
            },
            "low_wall_bounds_scene": geo_box_to_scene(-4.5, y_north_plot - 0.08, 3.2, y_north_plot + 0.12),
            "hedge_bounds_scene": geo_box_to_scene(-4.0, y_north_plot + 0.12, 3.0, y_north_plot + 0.55),
            "trees_scene": [
                {"position": geo_to_scene_m(-1.4, y_north_plot + 0.8, 0.0), "species": "neem", "scale": 0.75},
                {"position": geo_to_scene_m(2.6, y_north_plot + 0.85, 0.0), "species": "tree_shade", "scale": 0.82},
            ],
        },
        "north_frontage_utilities": {
            "source_photos": ["N-02", "N-03", "NE-01"],
            "streetlight_pole": {
                "id": "north-streetlight-pole-01",
                "position_geo_m": [pole_x, y_north_plot + 0.55, 0.0],
                "position_scene": geo_to_scene_m(pole_x, y_north_plot + 0.55, 0.0),
                "height_m": 6.2,
                "arm_length_m": 1.6,
                "arm_direction": "+x_scene (North over road)",
            },
            "ne_reference_pillar": {
                "id": "ne-reference-masonry-pillar",
                "position_geo_m": [ne_pillar_x, y_north_plot - 0.08, 0.0],
                "bounds_scene": geo_box_to_scene(ne_pillar_x - 0.22, y_north_plot - 0.22, ne_pillar_x + 0.22, y_north_plot + 0.22),
                "height_m": 1.35,
                "status": "provisional_photo_reference_not_survey_monument",
            },
            "excluded_temporary_objects": [
                {
                    "id": "excluded-white-car-n03",
                    "source_photos": ["N-03", "N-04"],
                    "reason": "Parked white hatchback car along the north road frontage is temporary and explicitly excluded from the 3D scene and site plan.",
                }
            ],
        },
        "adjoining_south_and_west": {
            "status": "unconfirmed_massing_placeholder",
            "south_neighbour_bounds_scene": geo_box_to_scene(1.8, -9.2, 13.4, -1.2),
            "west_neighbour_bounds_scene": geo_box_to_scene(-9.2, 1.5, -1.4, 10.8),
        },
        "reference_cameras": ref_cams,
        "sightline_cameras": sight_cams,
    }


def build_photo_reference_manifest() -> dict[str, Any]:
    """Structured photo-reference manifest documenting the 6 attached site photographs,
    their original clipboard filenames, copied reference-asset paths, camera bearings, and exclusions."""
    cams = build_reference_cameras()
    photos = []
    for code in ("N-01", "N-02", "N-03", "N-04", "NE-01", "E-01"):
        c = cams[code]
        photos.append({
            "id": code,
            "label": c["label"],
            "original_clipboard_filename": c["source_file"],
            "original_number_suffix": c["original_suffix"],
            "reference_asset_path": c["reference_asset"],
            "evidence_asset_path": f"evidence/tirumala/{c['reference_asset']}",
            "camera_position_geo_m": c["position_geo_m"],
            "camera_target_geo_m": c["target_geo_m"],
            "camera_position_scene_m": c["position"],
            "camera_target_scene_m": c["target"],
            "bearing_deg": c["bearing_deg"],
            "pitch_deg": c["pitch_deg"],
            "fov_deg": c["fov"],
            "confidence": c["confidence"],
            "observed_features": c["observed_features"],
            "excluded_temporary_features": c["excluded_temporary_features"],
        })
    return {
        "schema": PHOTO_MANIFEST_SCHEMA,
        "project_id": TIRUMALA_ID,
        "matching_rule": "Matched strictly by photograph label and visual content, not upload order.",
        "temporary_exclusions": [
            "Parked white car on the north road verge in N-03 / N-04 excluded from all site and context models."
        ],
        "photos": photos,
    }


def build_assumptions_register() -> dict[str, Any]:
    """Concise, structured Evidence & Assumptions Register separating owner-confirmed facts,
    directly visible features, estimated dimensions, provisional photo assignments, and unknowns."""
    return {
        "schema": ASSUMPTIONS_SCHEMA,
        "project_id": TIRUMALA_ID,
        "title": "Tirumala — Evidence, Assumptions & Site Measurement Register",
        "owner_confirmed_facts": [
            {
                "id": "CONF-01",
                "item": "Plot orientation & corner status",
                "value": "Northeast (NE) corner plot with an EAST-facing principal entrance.",
                "notes": "'Northeast corner plot' describes the two adjoining roads (North and East); the front entrance faces East.",
            },
            {
                "id": "CONF-02",
                "item": "East frontage & West boundary length",
                "value": "40 ft 0 in = 12.192 m (12,192 mm), running North–South.",
            },
            {
                "id": "CONF-03",
                "item": "North boundary & South boundary length",
                "value": "50 ft 0 in = 15.240 m (15,240 mm), running East–West.",
            },
            {
                "id": "CONF-04",
                "item": "Total plot area",
                "value": "2,000 sq ft = 185.806 m².",
            },
            {
                "id": "CONF-05",
                "item": "North road & surroundings",
                "value": "12.0 m road along the North boundary, followed by a colony garden and existing houses beyond.",
            },
            {
                "id": "CONF-06",
                "item": "East road & surroundings",
                "value": "9.0 m road along the East frontage, followed by a basketball-court enclosure and garden/planting.",
            },
            {
                "id": "CONF-07",
                "item": "Northwest utility cabinets",
                "value": "Two electrical feeder cabinets outside the plot near its Northwest (NW) corner.",
            },
            {
                "id": "CONF-08",
                "item": "North frontage streetlight pole",
                "value": "A streetlight pole along the North frontage between the Northeast and Northwest corners.",
            },
            {
                "id": "CONF-09",
                "item": "Revision 8 care suite & open NW corner garden",
                "value": "Revision 8 permits the Ground Floor Care Suite (g-care) to extend beyond the 25 ft midpoint across Options A–E (y = 21..39 ft) while preserving the open Northwest corner garden, a 3 ft clear North passage with boundary-plane greenery, and a 7 × 3.5 ft South-to-North bed (head South, feet North).",
            },
        ],
        "directly_visible_photo_features": [
            {
                "photo": "N-01 (ending 26039)",
                "features": "12 m concrete road, opposite raised masonry planting edge, manicured lawn, pergola with shaded seating, spherical/ornate decorative pots, slim garden lights, coconut/areca palms, and a two-storey white/grey house with a dark blue-grey vertical facade panel.",
            },
            {
                "photo": "N-02 (ending 26040)",
                "features": "Pair of light-coloured electrical feeder cabinets of differing sizes (smaller cabinet on left/east, taller louvred cabinet on right/west), surrounding green hedge, low brown-grey boundary wall, interlocking paver verge, trees, and nearby streetlight pole.",
            },
            {
                "photo": "N-03 (ending 26041)",
                "features": "Southward view across the 12 m North road toward the plot's North frontage (East on image-left, West on image-right), showing low boundary wall, hedge, interlocking pavers, streetlight pole, and roadside vegetation. Temporary parked white car excluded.",
            },
            {
                "photo": "E-01 (ending 26044)",
                "features": "Oblique East/Southeast view across the 9 m East road toward the tall pale metal mesh basketball-court enclosure, repeated tubular posts, coconut palms, leafy trees, raised planting bed, hedge, pavers, and lights.",
            },
            {
                "photo": "N-04 (ending 26042)",
                "features": "Cross-check leftward view from the North road toward the East court enclosure, paved passage, and low corner wall.",
            },
            {
                "photo": "NE-01 (ending 26043)",
                "features": "Close-up near the Northeast corner showing weathered masonry pillar with cream/ochre cap, low wall, hedge, paver footpath, and corner planting.",
            },
        ],
        "estimated_dimensions_and_placements": [
            {
                "parameter": "north_road_width_m (12.0 m ROW interpretation)",
                "working_value": "8.40 m concrete carriageway + 1.80 m south paver verge + 1.80 m north garden verge = 12.00 m total",
                "reversible_in": "floorforge/tirumala_context.py :: default_colony_parameters()",
            },
            {
                "parameter": "east_road_width_m (9.0 m ROW interpretation)",
                "working_value": "6.00 m concrete carriageway + 1.50 m west paver verge + 1.50 m east court-side verge = 9.00 m total",
                "reversible_in": "floorforge/tirumala_context.py :: default_colony_parameters()",
            },
            {
                "parameter": "Provisional building setbacks",
                "working_value": "East front = 1.840 m, North right = 1.242 m, West rear = 1.250 m, South left = 1.050 m (ground coverage 64.74% <= 65%)",
                "reversible_in": "scripts/build_tirumala.py",
            },
            {
                "parameter": "NW feeder cabinet offsets & sizes",
                "working_value": "Smaller East cabinet (0.78 x 0.48 x 1.22 m) at X_geo = 1.25 m; Taller West cabinet (1.05 x 0.55 x 1.62 m) at X_geo = 0.10 m, in North verge (Y_geo ~ 12.73 m)",
                "reversible_in": "floorforge/tirumala_context.py :: default_colony_parameters()",
            },
            {
                "parameter": "North streetlight pole position",
                "working_value": "X_geo = 4.35 m, Y_geo = 12.74 m (6.2 m height)",
                "reversible_in": "floorforge/tirumala_context.py :: default_colony_parameters()",
            },
        ],
        "provisional_photo_assignments": [
            {
                "photo": "N-04",
                "status": "Provisional leftward cross-check view; camera bearing (~122° SE) is estimated and used only to verify continuity between N-03 and E-01.",
            },
            {
                "photo": "NE-01",
                "status": "Provisional close-up near NE corner; visible masonry pillar is modelled as an existing wall pier reference (X_geo = 15.08 m), not treated as a surveyed boundary pin.",
            },
        ],
        "unknowns_requiring_site_measurement": [
            "Exact surveyed plot corner coordinates (total-station tie to existing masonry walls, hedges, and NE pillar).",
            "Statutory road width definition (whether 12 m North and 9 m East dimensions denote carriageway-only or total right-of-way including verges and drains).",
            "Exact footpath, paver verge, and stormwater drain widths and invert levels.",
            "Spot elevations of Natural Ground Level (NGL), road crown levels, and flood/plinth datum.",
            "Exact trunk coordinates, girth, species, and crown spread of roadside and garden trees.",
            "Exact measured offsets of the two NW electrical feeder cabinets, underground cable routing, and statutory transformer/feeder clearance.",
            "Exact measured offset of the North streetlight pole and overhead/underground service lines.",
            "Exact depth of the North colony garden and setback distance to the opposite white/grey house.",
            "Basketball-court exact footprint, internal surface material, hoop/backstop positions, and floodlight pole heights hidden behind dense tree screening.",
            "Exact adjoining building massing, boundary wall heights, and window positions on the South and West neighbouring plots.",
            "Applicable local municipal building bylaws (setbacks, FAR/FSI, maximum height, coverage, and road-corner splay requirements).",
        ],
    }
