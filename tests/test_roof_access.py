"""A roof access level follows the authored core without changing the dwelling's storey count."""
import copy
import json
from pathlib import Path
import pytest
from shapely.geometry import Polygon, LineString, box
from floorforge.model import DesignError, read_json
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate, reports
from floorforge.exterior import apply_exterior_preferences
from floorforge.scene import make_scene
from floorforge.plan_geometry import roof, plate, geometry
from floorforge.rooftop import with_rooftop_objects
from floorforge.plan_tools import guide_check, convert_guide
from floorforge.pipeline import run

ROOT = Path(__file__).resolve().parents[1]


def project():
    p = read_json(ROOT / 'examples/custom/g2-terrace.floorforge.json')
    p['brief']['roof_access'] = True
    return p


@pytest.mark.parametrize('floors', [1, 2, 3])
def test_roof_is_an_access_level_with_aligned_flight_hole_door_and_guards(floors):
    p = project()
    p['brief'].update(storeys=floors, bedrooms=floors)
    p['customPlan']['floors'] = p['customPlan']['floors'][:floors]
    p['customPlan']['stairs'][0]['roomIds'] = p['customPlan']['stairs'][0]['roomIds'][:floors]
    b = apply_exterior_preferences(generate_layout(fuse(p)))
    review = validate(b)
    st = b['stairs'][-1]; r = b['rooftop']; core = r['cores'][0]
    assert b['storeys'] == floors and len(b['floors']) == floors
    assert st['to_floor'] == floors and st['roof_access']
    hole = box(st['x'], st['y'] + st['landing_mm'], st['x'] + st['width'], st['y'] + st['depth'])
    assert roof(b, floors - 1).intersection(hole).area < 1
    assert plate(b, floors).equals(roof(b, floors - 1))
    assert geometry(b['roofs'][-1]['ceiling']).intersection(hole).area < 1
    door = r['openings'][0]
    assert door['floor'] == floors and door['connects'] == [core['roomId'], 'roof-terrace']
    assert door['swing'] == 'roof-terrace' and door['sill'] == 0
    assert geometry(r['terrace']).buffer(1).covers(Polygon(core['approach']))
    assert r['guards'] and all(g['floor'] == floors for g in r['guards'])
    scene = make_scene(b, reports(b, review))
    assert scene['roof_level'] == floors and scene['storeys'] == floors
    assert any(n['owner'] == door['id'] and n['role'] == 'door' for n in scene['nodes'] if 'owner' in n)
    assert door in scene['opening_model']['openings']
    assert not any(s['floor'] == floors for s in scene['walk']['floors'])  # never a roof teleport spawn
    assert any(s['id'] == 'roof-terrace' for s in scene['rooms'])
    assert with_rooftop_objects(with_rooftop_objects(b)) == with_rooftop_objects(b)
    from floorforge.drawings import plan_elements
    drawing, _ = plan_elements(b, scene, floors)
    leaves = [e for e in drawing if e['type']=='line' and e['layer']=='A-DOOR' and e['width']==.28]
    assert leaves and all(geometry(r['terrace']).buffer(1).covers(LineString([e['a'],e['b']])) for e in leaves)


def test_rear_custom_core_coordinates_are_retained_through_roof_and_scene():
    p = project()
    for fl in p['customPlan']['floors']:
        for room in fl['rooms']:
            room['polygon'] = [[x + 400, y + 5000] for x, y in room['polygon']]
    b = apply_exterior_preferences(generate_layout(fuse(p)))
    validate(b)
    assert {(s['x'], s['y']) for s in b['stairs']} == {(550, 5150)}
    assert b['rooftop']['cores'][0]['bounds'][:2] == [400, 5000]
    assert b['planHash'] == fuse(json.loads(json.dumps(p)))['planHash']
    s = make_scene(b, reports(b, validate(b)))
    landing = next(r for r in s['rooms'] if r['name'] == 'Roof stair landing')
    assert min(y for x, y in landing['polygon']) == 5.15


def test_roof_access_is_explicit_for_old_projects_and_changes_the_hash():
    p = project(); p['brief'].pop('roof_access')
    a = fuse(p); assert not a['values']['roof_access']
    assert 'rooftop' not in generate_layout(a)
    p['brief']['roof_access'] = True
    assert fuse(p)['planHash'] != a['planHash']
    assert fuse({'text': 'Staircase to the roof terrace.'})['values']['roof_access']
    assert not fuse({'text': 'No rooftop access.'})['values']['roof_access']


def test_no_roof_stair_fails_instead_of_inventing_a_fixed_core():
    with pytest.raises(DesignError) as e:
        generate_layout(fuse({'brief': {'storeys': 1, 'bedrooms': 1, 'roof_access': True}}))
    assert e.value.code == 'ROOF_STAIR_REQUIRED'
    p = project(); p['brief'].update(storeys=1, bedrooms=1, roof_access=False)
    p['customPlan']['floors'] = p['customPlan']['floors'][:1]
    p['customPlan']['stairs'][0]['roomIds'] = p['customPlan']['stairs'][0]['roomIds'][:1]
    with pytest.raises(DesignError) as e:
        generate_layout(fuse(p))
    assert any(i['code'] == 'STAIR_LINK' for i in e.value.details['errors'])


def test_rear_stair_guide_has_specific_cells_and_conversion_keeps_them():
    rows = [[[''] * 4 for _ in range(4)] for _ in range(2)]
    for f, fl in enumerate(rows):
        fl[3][0] = fl[2][0] = 'stair'; fl[1][3] = f'bedroom-{f+1}'
    p = {'brief': {'storeys': 2, 'bedrooms': 2, 'roof_access': True},
         'grid': {'mode': 'spatial_hint', 'rows': 4, 'cols': 4, 'floors': rows, 'floorIds': ['g', 'f']}}
    check = guide_check(fuse(p))
    conflicts = [r for r in check['rooms'] if r.get('code') == 'GUIDE_STAIR_POSITION']
    assert {r['floor'] for r in conflicts} == {0, 1}
    assert all(r['cells'] == [[0, 2], [0, 3]] for r in conflicts)
    with pytest.raises(DesignError) as e: generate_layout(fuse(p))
    assert e.value.code == 'GUIDE_CONFLICT'
    converted = convert_guide(p)['customPlan']
    assert len(converted['stairs']) == 1
    assert all(Polygon(next(r for r in fl['rooms'] if r['kind']=='stair')['polygon']).bounds[1] > 4000 for fl in converted['floors'])


def test_roof_export_pack_has_one_revision_and_roof_sheet(tmp_path):
    p = project(); result = run(p, tmp_path, use_cache=False); path = Path(result['path'])
    b = read_json(path / 'building.json'); h = b['planHash']
    assert all(read_json(path / (name + '.json'))['planHash'] == h for name in ['scene', 'report', 'manifest'])
    sheets = list((path / 'sheets').glob('*A-104*'))
    assert sheets and 'Roof terrace' in sheets[0].read_text()
    ifc = (path / 'model.ifc').read_text()
    assert 'Roof terrace' in ifc and b['rooftop']['cores'][0]['doorId'] in ifc
    assert "'Roof terrace'" in ifc and h in ifc
    assert 'ROOF TERRACE' in (path / 'floorplans.dxf').read_text()
    report = read_json(path / 'report.json')
    assert report['areas']['roof_terrace_m2'] > 0
    assert report['areas']['gross_floor_m2'] == round(sum(plate(b, f).area for f in range(b['storeys'])) / 1e6, 3)
