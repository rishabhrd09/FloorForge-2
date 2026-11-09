"""The approved wider north window is local to Tirumala 5 and cuts real masonry."""
import json
from pathlib import Path

import pytest
from shapely.geometry import box
from shapely.ops import unary_union

from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.tirumala_5 import build_project

ROOT=Path(__file__).resolve().parents[1]


def test_drawing_window_matches_editable_compiled_and_wall_geometry():
    project=build_project()
    plan=project['customPlan']['canonicalPlan']
    building=generate_layout(fuse(project))
    editable=next(o for o in plan['openings'] if o['id']=='drawing-north')
    compiled=next(o for o in building['openings'] if o['id']=='drawing-north')
    assert editable['a']==compiled['a']==[11507.4,8600]
    assert editable['b']==compiled['b']==[11507.4,11000]
    assert editable['sill']==compiled['sill']==450
    assert editable['height']==compiled['height']==2400
    assert compiled['width']==2400
    assert compiled['window_style']=='picture-with-sliding-vents'
    assert compiled['connects']==['g-drawing','outside']
    assert len([o for o in building['openings'] if o['floor']==0 and
                o['kind']=='window' and o['connects']==['g-drawing','outside']])==1
    masonry=unary_union([box(*r) for r in plan['wallRects']])
    assert masonry.intersection(box(11432.4,8600,11582.4,11000)).area<.01
    assert masonry.covers(box(11432.4,8200,11582.4,8600))
    assert masonry.covers(box(11432.4,11000,11582.4,11400))
    host=next(w for w in building['walls'] if w['id']==compiled['wall_id'])
    assert host['hostOnly'] and host['a']==compiled['a'] and host['b']==compiled['b']
    assert project['editorState']['customPlan']['canonicalPlan']['openings']==plan['openings']


def test_wider_window_retains_drawing_room_door_and_source_tirumala_4():
    source=json.loads((ROOT/'examples/gallery/tirumala-4/building.json').read_text())['planning']['canonicalPlan']
    plan=build_project()['customPlan']['canonicalPlan']
    for ident in ('drawing-veranda-only',):
        assert next(o for o in source['openings'] if o['id']==ident)==next(o for o in plan['openings'] if o['id']==ident)
    assert next(r for r in source['rooms'] if r['id']=='g-drawing')==next(r for r in plan['rooms'] if r['id']=='g-drawing')
    old=next(o for o in source['openings'] if o['id']=='drawing-north')
    assert old['a']==pytest.approx([11507.4,9600])
    assert old['b']==pytest.approx([11507.4,10800])
