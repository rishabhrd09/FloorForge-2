"""Variable-column Compass coordinates must survive the complete design path."""
import copy
import json
from pathlib import Path

import pytest
from shapely.geometry import Polygon

from floorforge.compass_api import capabilities, dispatch
from floorforge.compass_input import GRID_OPTIONS, normalize, remap
from floorforge.compass_adapter import proposal
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from floorforge.review import validate, reports
from floorforge.scene import make_scene
from floorforge.drawings import plan_elements

SHAPES = [(s['cols'], s['rows']) for s in GRID_OPTIONS]


def grid_project(cols, rows, storeys=3):
    """Rightmost half on every floor exercises E/F columns and floor identity."""
    project = {'schema': 'floorforge.project/0.5', 'brief': {
        'title': f'Compass {cols} by {rows}', 'width_mm': cols*3200+2150,
        'depth_mm': rows*3400+4350, 'front_mm': 3000, 'rear_mm': 1200,
        'left_mm': 1000, 'right_mm': 1000, 'bedrooms': storeys,
        'storeys': storeys, 'roof_access': False}}
    compass = {'schema': 'floorforge.compass-input/1', 'grid': {
        'rows': rows, 'cols': cols, 'basis': 'buildable-envelope', 'rowOrigin': 'front'},
        'floors': [], 'rooms': [], 'connections': [], 'stairLinks': [],
        'site': {'context': 'middle', 'gate': 'planner', 'entryRoomId': 'f0-hall'},
        'requirements': [{'id': 'note', 'kind': 'note', 'value': 'Retain this wish list.'}]}
    for i in range(storeys):
        fid = f'floor-{i}'
        compass['floors'].append({'id': fid, 'splits': [f'2:{cols-1}']})
        defs = [('stairs', 'stair', ['0:0', '1:0']),
                ('bed', 'bedroom', [f'{rows-1}:{c}' for c in range(cols)]),
                ('half', ('bathroom', 'pooja', 'store')[i], [f'2:{cols-1}:R'])]
        taken = {ref for _, _, refs in defs for ref in refs}
        if i == 0:
            defs.append(('kitchen', 'kitchen', [f'0:{cols-1}']))
            taken.add(f'0:{cols-1}')
        hall = [f'{r}:{c}' for r in range(rows-1) for c in range(cols)
                if f'{r}:{c}' not in taken and (r, c) != (2, cols-1)] + [f'2:{cols-1}:L']
        if i == 0:
            living = [f'0:{c}' for c in range(1, cols-1)]
            defs.append(('route', 'hall', [ref for ref in hall if ref not in living]))
            hall = living
        defs.append(('hall', 'living' if i == 0 else 'hall', hall))
        for name, kind, refs in defs:
            compass['rooms'].append({'id': f'f{i}-{name}', 'kind': kind,
                                    'name': f'{kind} {i+1}', 'floorId': fid,
                                    'regions': refs, 'required': True})
    compass['stairLinks'] = [{'id': 'core', 'roomIds': [f'f{i}-stairs' for i in range(storeys)]}]
    project['editorState'] = {'mode': 'compass', 'homeInputs': ['plot', 'compass', 'text'],
                              'compassDraft': copy.deepcopy(compass), 'compassScope': storeys,
                              'guideFloors': [[['']*4 for _ in range(4)] for _ in range(3)]}
    return project, compass


def reviewed(project, compass, scope=None):
    result = proposal(project, compass, scope)
    assert result['valid'], result['issues']
    return {**project, 'compass': compass, 'compassScope': scope or project['brief']['storeys'],
            'compassAcceptance': {k: result[k] for k in ('sourceHash', 'adapterVersion')}}


def test_one_registry_supplies_all_new_map_choices():
    caps = capabilities()
    assert caps['gridOptions'] == GRID_OPTIONS
    assert [(s['cols'], s['rows'], s['cells']) for s in caps['gridOptions']] == [
        (4, 4, 16), (4, 5, 20), (4, 6, 24), (5, 5, 25), (6, 7, 42)]
    assert caps['densities'] == [16, 20, 24, 25, 42]


@pytest.mark.parametrize('cols,rows', SHAPES + [(4, 8)])
@pytest.mark.parametrize('scope', [1, 2, 3])
def test_shapes_halves_floors_save_reopen_and_shared_geometry(cols, rows, scope, tmp_path):
    project, compass = grid_project(cols, rows)
    original = copy.deepcopy(compass)
    payload = reviewed(project, compass, scope)
    path = tmp_path/'home.floorforge.json'
    path.write_text(json.dumps(payload))
    reopened = json.loads(path.read_text())
    assert reopened['compass'] == original == reopened['editorState']['compassDraft']
    assert reopened['editorState']['homeInputs'] == ['plot', 'compass', 'text']
    intent = fuse(reopened)
    assert intent['planHash'] == fuse(payload)['planHash']
    building = generate_layout(intent)
    checked = validate(building)
    assert not checked['errors']
    scene = make_scene(building, reports(building, checked))
    assert scene['planHash'] == building['planHash'] == intent['planHash']
    assert building['storeys'] == scope
    assert sum(s.get('to_floor') is not None for s in building['stairs']) == scope-1
    for i in range(scope):
        room = next(s for s in building['spaces'] if s['id'] == f'f{i}-half')
        assert room['kind'] == ('bathroom', 'pooja', 'store')[i]
        # Each base allocation is exactly 3200 x 3400; a half reserves
        # 150mm for its enclosing walls, independent of grid column count.
        clear = Polygon(room['clear'])
        x0, y0, x1, y1 = clear.bounds
        assert (x1-x0, y1-y0) == pytest.approx((1450, 3250), abs=.01)
        assert x0 > (cols-1)*3200
        model_room = next(r for r in scene['rooms'] if r['id'] == room['id'])
        assert model_room['kind'] == room['kind']
        plan, _ = plan_elements(building, scene, i)
        assert any(e.get('text') == room['name'].upper() for e in plan)
    assert compass == original


@pytest.mark.parametrize('cols,rows', SHAPES)
def test_grid_bounds_apply_to_whole_cells_halves_and_empty_splits(cols, rows):
    _, compass = grid_project(cols, rows, 1)
    normalize(compass)
    for bad in (f'{rows}:0', f'0:{cols}', f'0:{cols}:R', '00:0', '-1:0'):
        broken = copy.deepcopy(compass)
        broken['rooms'][0]['regions'] = [bad]
        with pytest.raises(DesignError):
            normalize(broken)
    compass['floors'][0]['splits'].append(f'0:{cols}')
    with pytest.raises(DesignError):
        normalize(compass)


@pytest.mark.parametrize('source', SHAPES + [(4, 8)])
@pytest.mark.parametrize('target', SHAPES)
def test_two_axis_remap_keeps_exact_full_envelope_and_all_floor_identities(source, target):
    project, compass = grid_project(*source)
    cols, rows = source
    for floor in compass['floors']:
        floor['splits'] = []
    for room in compass['rooms']:
        room['regions'] = [f'{r}:{c}' for r in range(rows) for c in range(cols)] if room['id'].endswith('-hall') else []
    before = copy.deepcopy(compass)
    result = dispatch('/api/compass/remap', {'compass': compass, 'cols': target[0], 'rows': target[1]})
    assert result['valid'], result['issues']
    candidate = normalize(result['candidate'])
    assert candidate['grid']['cols'] == target[0] and candidate['grid']['rows'] == target[1]
    for room in candidate['rooms']:
        assert len(room['regions']) == (target[0]*target[1] if room['id'].endswith('-hall') else 0)
    for key in ('floors', 'connections', 'stairLinks', 'site', 'requirements'):
        assert candidate[key] == normalize(before)[key]
    assert compass == before


def test_column_remap_refuses_collisions_and_partial_empty_boundaries():
    _, compass = grid_project(4, 4, 1)
    before = copy.deepcopy(compass)
    result = remap(compass, 5, 5)
    assert not result['valid']
    assert any(i['code'] == 'REMAP_COLLISION' for i in result['issues'])
    assert compass == before
    compass['rooms'] = [compass['rooms'][-1]]
    compass['rooms'][0]['regions'] = ['0:0']
    compass['site'].pop('entryRoomId')
    compass['stairLinks'] = []
    result = remap(compass, 5, 5)
    assert not result['valid']
    assert any(i['code'] == 'REMAP_BOUNDARY' for i in result['issues'])


def test_unchanged_legacy_grid_keeps_empty_splits_and_acceptance_hash():
    project, compass = grid_project(4, 8, 1)
    compass['floors'][0]['splits'].append('4:0')
    # This room used the whole cell before the empty partition was authored.
    hall = next(r for r in compass['rooms'] if r['id'] == 'f0-route')
    hall['regions'].remove('4:0')
    hall['regions'].extend(['4:0:L', '4:0:R'])
    expected = normalize(compass)
    assert remap(compass, 8, 4)['candidate'] == expected
    assert proposal(project, compass)['adapterVersion'] == 'compass/2'
