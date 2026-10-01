"""Regression coverage for user-authored spatial input.

The 4 x 4 board is deliberately a *placement hint*, not a dimensioning grid.
The automatic planner remains responsible for room sizes, walls, openings and
the physical model.  These tests keep that distinction observable all the way
through the scene contract.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import Polygon

from floorforge.exterior import apply_exterior_preferences
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from floorforge.review import reports, validate
from floorforge.scene import make_scene


ROOT = Path(__file__).resolve().parents[1]


COMPACT = {
    "width_mm": 9144,
    "depth_mm": 12192,
    "storeys": 1,
    "bedrooms": 2,
    "front_mm": 1800,
    "rear_mm": 900,
    "left_mm": 750,
    "right_mm": 750,
    "pooja": False,
    "parking": False,
    "vastu": "off",
}


SPACIOUS_G1 = {
    "width_mm": 12192,
    "depth_mm": 18288,
    "storeys": 2,
    "bedrooms": 4,
    "front_mm": 3000,
    "rear_mm": 1200,
    "left_mm": 1000,
    "right_mm": 1000,
    "pooja": True,
    "parking": False,
    "attached_baths": "all",
    "vastu": "off",
}


def spatial_grid(rows):
    return {
        "mode": "spatial_hint",
        "rows": 4,
        "cols": 4,
        "floors": [rows],
    }


LEFT_SERVICE_GRID = spatial_grid(
    [
        ["living", "living", "living", "living"],
        ["kitchen", "hall", "bedroom-1", "bedroom-1"],
        ["utility", "hall", "bedroom-2", "bedroom-2"],
        ["bathroom", "hall", "bedroom-2", "bedroom-2"],
    ]
)


RIGHT_SERVICE_GRID = spatial_grid(
    [
        ["living", "living", "living", "living"],
        ["bedroom-1", "bedroom-1", "hall", "kitchen"],
        ["bedroom-2", "bedroom-2", "hall", "utility"],
        ["bedroom-2", "bedroom-2", "hall", "bathroom"],
    ]
)


def _build(*, grid=None, text=None, brief=None):
    project = {"schema": "floorforge.project/0.3", "brief": dict(brief or COMPACT)}
    if grid is not None:
        project["grid"] = grid
    if text is not None:
        project["text"] = text
    return generate_layout(fuse(project))


def centred_hint(label):
    rows = [[""] * 4 for _ in range(4)]
    for y in (1, 2):
        for x in (1, 2):
            rows[y][x] = label
    return spatial_grid(rows)


def _centre(building, kind):
    room = next(s for s in building["spaces"] if s["floor"] == 0 and s["kind"] == kind)
    return Polygon(room["polygon"]).centroid


@pytest.mark.parametrize(
    "grid",
    [
        {"mode": "spatial_hint", "rows": 3, "cols": 4, "floors": [[['living'] * 4 for _ in range(3)]]},
        {"mode": "spatial_hint", "rows": 4, "cols": 5, "floors": [[['living'] * 5 for _ in range(4)]]},
        {"mode": "spatial_hint", "rows": 4, "cols": 4, "floors": [[['living'] * 4 for _ in range(3)]]},
        {"mode": "spatial_hint", "rows": 4, "cols": 4, "floors": [[['living'] * 3 for _ in range(4)]]},
    ],
)
def test_spatial_hint_grid_is_always_exactly_sixteen_cells(grid):
    with pytest.raises(DesignError) as error:
        _build(grid=grid)
    assert error.value.code == "GRID_SIZE"


def test_spatial_hint_grid_has_no_physical_cell_size_contract():
    legacy_exact_grid = {**LEFT_SERVICE_GRID, "cell_mm": 1000}
    with pytest.raises(DesignError) as error:
        _build(grid=legacy_exact_grid)
    assert error.value.code == "GRID_SCHEMA"


def test_studio_emits_one_fixed_four_by_four_spatial_guide():
    html = (ROOT / "web/index.html").read_text("utf8")
    app = (ROOT / "web/app.js").read_text("utf8")
    css = (ROOT / "web/style.css").read_text("utf8")

    assert 'id="grid-cell"' not in html
    assert "const GRID_SIZE=4" in app
    assert "mode:'spatial_hint',rows:GRID_SIZE,cols:GRID_SIZE" in app
    assert "gridRows=emptyGrid()" in app
    assert "$('grid-cell')" not in app
    assert "kind:'form'" in app
    assert "delete p.brief[key];delete edited[key]" in app
    assert "source.id!=='ai-proposal'" in app
    assert "groups.size>GRID_SIZE*GRID_SIZE" in app
    assert "for(let setback of SETBACK_KEYS)explicitEdits.add(setback)" in app
    assert ".grid-dialog #grid-board{grid-template-columns:repeat(4" in css
    assert "syncGridBrushes" in app


def test_latest_user_touched_form_field_wins_over_text_and_imported_edits():
    intent = fuse(
        {
            "brief": {"bedrooms": 2},
            "text": "Make it a 3 BHK home.",
            "sources": [
                {"id": "older-ai-edit", "kind": "edit", "enabled": True, "values": {"bedrooms": 4}},
                {"id": "studio-field-edits", "kind": "form", "enabled": True, "values": {"bedrooms": 2}},
            ],
        }
    )

    assert intent["values"]["bedrooms"] == 2
    assert intent["provenance"]["bedrooms"]["selected"] == ["studio-field-edits"]


def test_four_by_four_hint_changes_relative_room_placement_not_dimensions():
    left = _build(grid=LEFT_SERVICE_GRID)
    right = _build(grid=RIGHT_SERVICE_GRID)
    left_mid = Polygon(left["footprint"]).centroid.x
    right_mid = Polygon(right["footprint"]).centroid.x

    assert _centre(left, "kitchen").x < left_mid
    assert _centre(right, "kitchen").x > right_mid
    assert left["footprint"] == right["footprint"]
    assert sorted((s["kind"], s["area_m2"]) for s in left["spaces"]) == sorted(
        (s["kind"], s["area_m2"]) for s in right["spaces"]
    )
    assert left["planning"]["method"] != "manual grid"
    assert right["planning"]["method"] != "manual grid"


def test_supported_description_reaches_layout_instead_of_remaining_metadata():
    building = _build(
        text="30 by 40 ft plot, 2 BHK ground floor only, closed kitchen, no pooja and no parking."
    )
    assert building["brief"]["width_mm"] == 9144
    assert building["brief"]["depth_mm"] == 12192
    assert building["brief"]["open_kitchen"] is False
    assert sum(s["kind"] == "bedroom" for s in building["spaces"]) == 2

    kitchen_id = next(s["id"] for s in building["spaces"] if s["kind"] == "kitchen")
    assert any(
        opening["kind"] == "door" and kitchen_id in opening["connects"]
        for opening in building["openings"]
    )


def test_directional_description_changes_room_position():
    left = _build(text="Place the kitchen on the left side and bedrooms on the right side.")
    right = _build(text="Place the kitchen on the right side and bedrooms on the left side.")
    midpoint = Polygon(left["footprint"]).centroid.x

    assert _centre(left, "kitchen").x < midpoint
    assert _centre(right, "kitchen").x > midpoint
    assert left["spaces"] != right["spaces"]


@pytest.mark.parametrize(
    ("label", "space_id"),
    [("pooja", "F0-pooja"), ("bathroom-1", "F0-bath-1")],
)
def test_optional_room_hint_survives_local_candidate_pruning(label, space_id):
    building = _build(grid=centred_hint(label), brief=SPACIOUS_G1)
    audit = next(item for item in building["planning"]["placement"]["matched"] if item["label"] == label)

    assert audit["space_id"] == space_id
    assert audit["status"] == "applied"
    assert any(space["id"] == space_id for space in building["spaces"])


def test_compass_pooja_description_preserves_and_places_the_optional_room():
    # With an east-side road, geographic north-east is the plan's front-right zone.
    building = _build(
        text="Place the pooja towards north-east.",
        brief={**SPACIOUS_G1, "road_bearing_deg": 90},
    )
    audit = next(item for item in building["planning"]["placement"]["matched"] if item["label"] == "pooja")

    assert audit["space_id"] == "F0-pooja"
    assert audit["status"] == "applied"
    assert audit["source"] == "text"


def test_newer_form_programme_drops_stale_incompatible_text_placement():
    intent = fuse(
        {
            "text": "Place the pooja towards north-east and bedroom 4 at the rear.",
            "sources": [
                {
                    "id": "studio-field-edits",
                    "kind": "form",
                    "enabled": True,
                    "values": {"pooja": False, "bedrooms": 2},
                }
            ],
        }
    )

    assert intent["values"]["pooja"] is False and intent["values"]["bedrooms"] == 2
    assert intent["placement_hints"] == []
    assert sum("Ignored description placement" in notice for notice in intent["notices"]) == 2


def test_grid_target_supersedes_even_conflicting_text_targets_for_same_room():
    intent = fuse(
        {
            "text": "Put the kitchen on the left and put the kitchen on the right.",
            "grid": centred_hint("kitchen"),
        }
    )

    assert len(intent["placement_hints"]) == 1
    assert intent["placement_hints"][0]["label"] == "kitchen"
    assert intent["placement_hints"][0]["source"] == "grid"


def test_compact_combined_living_and_dining_accepts_dining_hint():
    building = _build(
        grid=centred_hint("dining"),
        brief={"width_mm": 9144, "depth_mm": 12192, "bedrooms": 2, "storeys": 1},
    )
    audit = next(item for item in building["planning"]["placement"]["matched"] if item["label"] == "dining")

    assert audit["space_name"] == "Living & dining"
    assert audit["status"] == "applied"


def test_grid_description_and_question_fields_are_composed():
    building = _build(
        grid=RIGHT_SERVICE_GRID,
        text="Use a closed kitchen, no pooja, no parking, and a front setback of 2 m.",
    )
    midpoint = Polygon(building["footprint"]).centroid.x
    kitchen = next(s for s in building["spaces"] if s["kind"] == "kitchen")

    assert Polygon(kitchen["polygon"]).centroid.x > midpoint
    assert building["brief"]["front_mm"] == 2000
    assert building["brief"]["open_kitchen"] is False
    assert building["brief"]["pooja"] is False
    assert any(
        opening["kind"] == "door" and kitchen["id"] in opening["connects"]
        for opening in building["openings"]
    )


def test_spatial_hint_is_reflected_in_the_scene_room_contract():
    left_building = apply_exterior_preferences(_build(grid=LEFT_SERVICE_GRID))
    right_building = apply_exterior_preferences(_build(grid=RIGHT_SERVICE_GRID))

    def scene_for(building):
        review = validate(building)
        return make_scene(building, reports(building, review))

    left_scene = scene_for(left_building)
    right_scene = scene_for(right_building)
    left_kitchen = next(r for r in left_scene["rooms"] if r["kind"] == "kitchen")
    right_kitchen = next(r for r in right_scene["rooms"] if r["kind"] == "kitchen")

    assert Polygon(left_kitchen["polygon"]).centroid.x < Polygon(left_scene["footprint"]).centroid.x
    assert Polygon(right_kitchen["polygon"]).centroid.x > Polygon(right_scene["footprint"]).centroid.x
    assert left_kitchen["polygon"] != right_kitchen["polygon"]
    assert any(n.get("owner") == left_kitchen["id"] and n["role"] == "finish" for n in left_scene["nodes"])
    assert any(n.get("owner") == right_kitchen["id"] and n["role"] == "finish" for n in right_scene["nodes"])
