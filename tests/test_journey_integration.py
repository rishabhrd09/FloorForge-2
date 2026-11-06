"""Real publication, scene and portable-project agreement for the new journey."""
from copy import deepcopy
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zlib
import zipfile

import ezdxf
import networkx as nx
import numpy as np
from PIL import Image
import pytest
from shapely.affinity import scale
from shapely.geometry import Polygon
from shapely.ops import unary_union
import trimesh

from floorforge.design_journey import SCHEMA, canonical_model, prepare, verify_approval
from floorforge.journey_service import JourneyService
from floorforge.model import DesignError, read_json, sha
from floorforge.pipeline import run
from floorforge.scene import opening_polygon, transformation

ROOT = Path(__file__).resolve().parents[1]


def project():
    p = read_json(ROOT / 'examples/custom/g2-terrace.floorforge.json')
    image = io.BytesIO()
    Image.new('RGB', (3, 2), 'white').save(image, format='PNG')
    raw = image.getvalue()
    p['attachments'] = [{'id': 'original-sketch', 'name': 'reference.png', 'kind': 'visual-reference',
                         'mimeType': 'image/png', 'sha256': hashlib.sha256(raw).hexdigest(),
                         'dataUrl': 'data:image/png;base64,' + base64.b64encode(raw).decode(), 'units': 'px'}]
    p['designJourney'] = {'schema': SCHEMA, 'projectId': 'integration-home',
                          'enabledInputs': ['plot', 'dxf', 'sketch'], 'answers': {'retained-answer': 'retain'},
                          'appearance': {'preset': 'warm-natural'}, 'approvals': {}}
    return p


def approve(service, p):
    prepared = service.prepare(p)
    assert prepared['valid'], prepared['questions']
    approvals = {floor['id']: service.approve({'preparationId': prepared['preparationId'],
                 'floorId': floor['id'], 'geometryHash': floor['geometryHash']})['approval'] for floor in prepared['floors']}
    p['designJourney']['approvals'] = approvals
    p['designJourney']['confirmation'] = service.confirm({'preparationId': prepared['preparationId'],
        'approvals': approvals, 'geometryHash': prepared['geometryHash']})['confirmation']
    return prepared


@pytest.fixture(scope='module')
def published(tmp_path_factory):
    out = tmp_path_factory.mktemp('journey-artifacts')
    service = JourneyService(out)
    p = project()
    prepared = approve(service, p)
    result = run(p, out, use_cache=False)
    return {'out': out, 'project': p, 'prepared': prepared, 'path': Path(result['path']),
            'building': read_json(Path(result['path']) / 'building.json'),
            'scene': read_json(Path(result['path']) / 'scene.json')}


def pdf_text_streams(raw):
    """Inspect ReportLab's documented ASCII85+Flate streams without a new runtime dependency."""
    streams = []
    for match in re.finditer(rb'<<(.*?)>>\s*stream\r?\n(.*?)endstream', raw, re.S):
        attrs, data = match.groups()
        if b'/ASCII85Decode' in attrs:
            data = base64.a85decode(data.strip(), adobe=True)
        if b'/FlateDecode' in attrs:
            data = zlib.decompress(data)
        streams.append(data)
    return b'\n'.join(streams)


def test_2d_publication_has_all_floors_before_any_scene(tmp_path):
    p = project()
    service = JourneyService(tmp_path)
    prepared = service.prepare(p)
    assert prepared['valid'], prepared['questions']
    base = tmp_path / 'preparations' / prepared['preparationId']
    assert len(list(base.glob('floor-*.svg'))) == 3
    assert (base / 'drawings.pdf').read_bytes().startswith(b'%PDF-')
    assert ezdxf.readfile(base / 'floorplans.dxf').units == 4
    assert not list(tmp_path.rglob('scene.json'))
    assert not list(tmp_path.rglob('*.glb'))
    with pytest.raises(DesignError, match='Approve'):
        run(p, tmp_path, target='scene')


def test_material_modules_invalidate_scene_cache_without_reapproving_geometry(tmp_path):
    p=project();service=JourneyService(tmp_path);prepared=approve(service,p)
    certificate=deepcopy(p['designJourney']['confirmation'])
    linen=run(p,tmp_path,target='scene')['output']
    p['designJourney']['appearance']['components']={'furniture':'sage'}
    sage=run(p,tmp_path,target='scene')['output']
    assert linen['materials']['fabric']['color']!=sage['materials']['fabric']['color']
    assert linen['appearanceHash']!=sage['appearanceHash']
    assert linen['geometryHash']==sage['geometryHash']==prepared['geometryHash']
    assert linen['nodes']==sage['nodes'] and linen['colliders']==sage['colliders']
    assert p['designJourney']['confirmation']==certificate
    p['designJourney']['appearance']['components']={'furniture':'linen'}
    cached=run(p,tmp_path,target='scene')['output']
    assert cached['materials']==linen['materials']


def test_pipeline_building_and_scene_share_the_approved_geometry(published):
    p, b, scene = published['prepared'], published['building'], published['scene']
    assert sha(canonical_model(b)) == p['geometryHash']
    assert b['geometryHash'] == scene['geometryHash'] == p['geometryHash']
    assert b['storeys'] == scene['storeys'] == len(p['floors']) == 3
    assert scene['floor_height'] * 1000 == b['brief']['floor_height_mm']
    room_by_id = {r['id']: r for r in scene['rooms']}
    assert set(room_by_id) == {r['id'] for r in p['canonical']['rooms']}
    for room in p['canonical']['rooms']:
        actual = room_by_id[room['id']]
        assert actual['floor'] == room['floor'] and actual['kind'] == room['kind']
        np.testing.assert_allclose(np.asarray(actual['polygon']) * 1000, room['clear'], atol=.051)
    assert scene['opening_model']['openings'] == p['canonical']['openings']
    assert scene['opening_model']['walls'] == p['canonical']['walls']


def test_opening_topology_agrees_in_approved_model_and_3d(published):
    model, scene = published['prepared']['canonical'], published['scene']
    def graph(openings):
        g = nx.MultiGraph()
        for opening in openings:
            if opening['kind'] != 'window' and len(opening['connects']) == 2:
                g.add_edge(*opening['connects'], key=opening['id'], width=opening['width'], floor=opening['floor'])
        return g
    approved, rendered = graph(model['openings']), graph(scene['opening_model']['openings'])
    assert nx.utils.graphs_equal(approved, rendered)
    assert nx.has_path(approved, 'outside', next(r['id'] for r in model['rooms'] if r['kind'] == 'bedroom' and r['floor'] == 0))


def test_collision_walls_have_the_actual_approved_door_gaps(published):
    scene = published['scene']
    for wall in published['prepared']['canonical']['walls']:
        expected = Polygon(np.asarray(wall['polygon']) / 1000)
        for opening in published['prepared']['canonical']['openings']:
            if opening['wall_id'] == wall['id'] and opening['kind'] != 'window':
                expected = expected.difference(scale(opening_polygon(wall, opening, 10), xfact=.001, yfact=.001, origin=(0, 0)))
        parts = [Polygon(c['polygon']) for c in scene['colliders'] if c['kind'] == 'wall' and c['id'].startswith(wall['id'] + '/')]
        assert unary_union(parts).symmetric_difference(expected).area < 1e-8, wall['id']


def test_furniture_is_true_scale_inside_its_approved_room(published):
    model = published['prepared']['canonical']
    room_by_id = {r['id']: r for r in model['rooms']}
    assert published['scene']['furniture']
    for furniture in published['scene']['furniture']:
        room = room_by_id[furniture['room_id']]
        clear = Polygon(np.asarray(room['clear']) / 1000)
        footprint = Polygon(furniture['footprint'])
        assert room['floor'] == furniture['floor']
        assert clear.buffer(.015).covers(footprint), furniture['id']
        assert 0.03 < footprint.area < 30


def test_scene_floor_meshes_reproduce_canonical_slab_openings(published):
    from floorforge.plan_geometry import plate
    scene, building = published['scene'], published['building']
    for floor in range(building['storeys']):
        node = next(n for n in scene['nodes'] if n['id'] == f'F{floor}-floor')
        asset = scene['assets'][node['asset']]
        mesh = trimesh.Trimesh(vertices=asset['vertices'], faces=asset['faces'], process=False)
        mesh.apply_transform(transformation(node))
        horizontal = []
        for triangle in mesh.triangles:
            if max(triangle[:, 2]) - min(triangle[:, 2]) < 1e-7:
                p = Polygon(triangle[:, :2])
                if p.area > 1e-9:
                    horizontal.append(p)
        projection = unary_union(horizontal)
        expected = scale(plate(building, floor), xfact=.001, yfact=.001, origin=(0, 0))
        assert projection.symmetric_difference(expected).area < 1e-6


def test_pdf_and_dxf_publish_the_approved_dimensions(published):
    prepared, out, path = published['prepared'], published['out'], published['path']
    base = out / 'preparations' / prepared['preparationId']
    raw = (base / 'drawings.pdf').read_bytes()
    text = pdf_text_streams(raw)
    assert len(re.findall(rb'/Type\s*/Page\b', raw)) >= 3
    assert b'Ground floor' in text and b'First floor' in text and b'Second floor' in text
    assert b'All dimensions in millimetres' in text
    assert prepared['preparedProject']['brief']['title'].encode() in text
    before = ezdxf.readfile(base / 'floorplans.dxf')
    after = ezdxf.readfile(path / 'floorplans.dxf')
    assert before.units == after.units == 4
    dims_before, dims_after = list(before.modelspace().query('DIMENSION')), list(after.modelspace().query('DIMENSION'))
    assert len(dims_before) == len(dims_after) > 30
    for a, b in zip(dims_before, dims_after):
        np.testing.assert_allclose(a.dxf.defpoint2, b.dxf.defpoint2, atol=.001)
        np.testing.assert_allclose(a.dxf.defpoint3, b.dxf.defpoint3, atol=.001)
        assert a.get_xdata('FLOORFORGE') == b.get_xdata('FLOORFORGE')
    manifest = read_json(path / 'manifest.json')
    assert manifest['geometryHash'] == prepared['geometryHash']
    assert manifest['checks']['dxf']['status'] == 'ezdxf_reimport_pass'


def test_glb_meshes_preserve_scene_transform_and_physical_units(published):
    scene = published['scene']
    glb = trimesh.load(published['path'] / 'model.glb', force='scene')
    assert len(glb.graph.nodes_geometry) == len(scene['nodes'])
    conversion = trimesh.transformations.rotation_matrix(-math.pi / 2, [1, 0, 0])
    # Check every physical node transform, not just an overall bounding box.
    for node in scene['nodes']:
        matrix, geometry = glb.graph[node['id']]
        np.testing.assert_allclose(matrix, conversion @ transformation(node), atol=1e-6)
        expected = np.asarray(scene['assets'][node['asset']]['vertices'])
        np.testing.assert_allclose(glb.geometry[geometry].vertices, expected, atol=3e-6)
    assert glb.metadata['units'] == 'm'


def test_portable_package_retains_original_refs_answers_and_approvals(published):
    path, original = published['path'], published['project']
    portable = read_json(path / 'project.floorforge.json')
    assert portable == original
    with zipfile.ZipFile(path / 'FloorForge-export.zip') as archive:
        assert json.loads(archive.read('project.floorforge.json')) == original
        assert json.loads(archive.read('canonical.json')) == published['prepared']['canonical']
        assert json.loads(archive.read('geometry-approval.json'))['confirmation'] == original['designJourney']['confirmation']
    # A fresh service on the same studio can reopen approvals; the signing key
    # is deliberately absent from the portable project and archive.
    service = JourneyService(published['out'])
    compiler, current = service.generation_payload(portable)
    assert current['geometryHash'] == published['prepared']['geometryHash']
    assert 'dataUrl' not in json.dumps(compiler)
    assert '.journey-signing-key' not in zipfile.ZipFile(path / 'FloorForge-export.zip').namelist()


def test_appearance_selection_reuses_approval_but_not_appearance_identity(published):
    p = deepcopy(published['project'])
    p['designJourney']['appearance'] = {'preset': 'earth-verandah'}
    service = JourneyService(published['out'])
    compiler, prepared = service.generation_payload(p)
    assert prepared['geometryHash'] == published['prepared']['geometryHash']
    assert prepared['appearance']['appearanceHash'] != published['prepared']['appearance']['appearanceHash']
    assert compiler['brief']['interior_theme'] == 'bright_natural'  # fixed geometry recipe
    assert prepared['appearance']['materials']['interior_theme'] == 'earthy_modern_indian'


def test_changed_geometry_and_tampered_certificates_cannot_reuse_approval(published):
    service = JourneyService(published['out'])
    p = deepcopy(published['project'])
    p['brief']['road_bearing_deg'] = 45
    with pytest.raises(DesignError, match='Approve'):
        service.generation_payload(p)
    p = deepcopy(published['project'])
    p['designJourney']['confirmation']['signature'] = '0' * 64
    with pytest.raises(DesignError, match='Approve'):
        run(p, published['out'], target='scene')


@pytest.mark.parametrize('bearing', range(0, 360, 45))
@pytest.mark.parametrize('offset', [(0, 0), (250, 500), (600, 1000)])
def test_metamorphic_translation_and_orientation_keep_room_topology(bearing, offset):
    p = project()
    p['brief']['road_bearing_deg'] = bearing
    dx, dy = offset
    for floor in p['customPlan']['floors']:
        for room in floor['rooms']:
            room['polygon'] = [[x + dx, y + dy] for x, y in room['polygon']]
    original = deepcopy(p)
    r = prepare(p)
    assert r['valid'], r['questions']
    assert p == original
    rooms = {r['id']: r for r in r['canonical']['rooms']}
    for floor in p['customPlan']['floors']:
        for room in floor['rooms']:
            np.testing.assert_allclose(rooms[room['id']]['clear'], room['polygon'], atol=.001)
    assert len(r['canonical']['floors']) == 3
    assert {r['kind'] for r in r['canonical']['rooms']} == {r['kind'] for f in p['customPlan']['floors'] for r in f['rooms']}
