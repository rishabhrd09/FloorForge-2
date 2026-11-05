"""Physical material scale and terrace circulation checks for the G+2 upgrade."""
import copy
import json
import random
from pathlib import Path

import pytest
import numpy as np
from shapely.geometry import LineString, Polygon, MultiPoint, box
from shapely.ops import unary_union
from trimesh.transformations import euler_matrix

from floorforge.tirumala_5_finishes import (
    apply, _kit, _materials, _utility_privacy, _upper_revision_cleanup, _opening_reveals,
)
from floorforge.scene_kit import Kit
from floorforge.tirumala_openings import build_opening, pose_initial_opening

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def delivery():
    base = ROOT/'examples/gallery/tirumala-5'
    return json.loads((base/'scene.json').read_text()), json.loads((base/'building.json').read_text())


def _footprint(asset):
    triangles=[]
    for f in asset['faces']:
        p=Polygon([asset['vertices'][i][:2] for i in f])
        if p.area>1e-10:triangles.append(p)
    return unary_union(triangles)


def _world_vertices(scene, node):
    vertices = np.asarray(scene['assets'][node['asset']]['vertices'], dtype=float)
    vertices *= np.asarray(node.get('scale', [1, 1, 1]))
    vertices = vertices @ euler_matrix(*node.get('rotation', [0, 0, 0]))[:3, :3].T
    return vertices + np.asarray(node.get('position', [0, 0, 0]))


def test_actual_slab_sizes_match_the_label(delivery):
    scene,_=delivery
    # The tile shader divides the repeat by params[0] along BOTH axes.  The
    # former repeat of 8x4 ft with two tiles actually showed only 4x2 ft tiles.
    for name in ('ivory-marble-polished','ivory-marble-exterior-matte','terrace-stone'):
        d=scene['materials'][name]
        n=d['params'][0]
        assert [v/n for v in d['tile_m']]==pytest.approx([3.2,1.6])
        assert d['params'][1]>0, 'Real slab joints must remain visible'
    assert scene['materials']['ivory-marble-exterior-matte']['roughness']>.5


def test_opaque_terrace_edge_keeps_gallery_glass_and_doorways(delivery):
    scene,building=delivery
    assert not any(n['id'].startswith('terrace-guard-') for n in scene['nodes'])
    assert len([n for n in scene['nodes'] if n['id'].startswith(('gallery-glass-', 'internal-gallery-guard-'))])>=2
    node=next(n for n in scene['nodes'] if n['id']=='t5lux-first-opaque-parapet')
    assert scene['materials'][node['material']].get('alpha',1)==1
    asset=scene['assets'][node['asset']]
    assert asset['closed']
    z=[v[2]for v in asset['vertices']]
    assert max(z)-min(z)==pytest.approx(1.08)
    edge=_footprint(asset)
    for op in building['openings']:
        if op['floor']!=1 or op['sill']!=0:continue
        door=LineString([(x/1000,y/1000)for x,y in (op['a'],op['b'])]).buffer(.15,cap_style=2)
        assert edge.intersection(door).area<1e-8,op['id']


def test_finish_refinement_does_not_mutate_building_or_repeat_geometry(delivery):
    scene,building=map(copy.deepcopy,delivery)
    before=copy.deepcopy(building)
    count=len(scene['nodes'])
    apply(scene,building)
    assert building==before
    assert len(scene['nodes'])==count
    assert scene['tirumala5Finish']['roomFootprintsChanged'] is False
    assert all(n['material']in scene['materials']and n['asset']in scene['assets']for n in scene['nodes'])


def test_utility_privacy_retains_window_air_gaps_and_north_access(delivery):
    scene, building = map(copy.deepcopy, delivery)
    building['planning']['canonicalPlan']['utilityPrivacy'] = {
        'southRectMm': [0, 150, 148, 1521.6],
        'eastRectMm': [150, 0, 2283.6, 150], 'heightMm': 1800,
    }
    before = copy.deepcopy(building)
    # Exercise the new boundary operation directly against the inherited scene.
    scene['nodes'][:] = [n for n in scene['nodes'] if not n['id'].startswith('t5lux-utility-')]
    scene['colliders'][:] = [c for c in scene['colliders'] if not c['id'].startswith('t5lux-utility-')]
    _materials(scene)
    _utility_privacy(scene, building, _kit(scene))
    nodes = [n for n in scene['nodes'] if n['id'].startswith('t5lux-utility-')]
    assert len([n for n in nodes if '-louvre-' in n['id']]) == 24
    clear_utility = box(.15, .15, 2.2836, 1.5216)
    north_access = box(2.2836, .15, 2.9, .9)
    for node in nodes:
        vertices = _world_vertices(scene, node)
        plan = MultiPoint(vertices[:, :2]).convex_hull
        assert plan.intersection(clear_utility).area < 1e-9, node['id']
        assert plan.intersection(north_access).area < 1e-9, node['id']
        assert vertices[:, 2].max() <= 1.800001
        assert vertices[:, 0].max() < 2.7, 'Kitchen window starts at2700mm'
    fins = sorted([n for n in nodes if n['id'].startswith('t5lux-utility-louvre-0-')],
                  key=lambda n: n['position'][2])
    for lower, upper in zip(fins, fins[1:]):
        assert _world_vertices(scene, upper)[:, 2].min() - _world_vertices(scene, lower)[:, 2].max() > .015
    privacy_colliders = [c for c in scene['colliders'] if c['id'].startswith('t5lux-utility-')]
    assert {c['id'] for c in privacy_colliders} == {
        't5lux-utility-south-privacy', 't5lux-utility-east-privacy'}
    assert building == before
    assert not any(n['id'] == 'boundary-east-south' for n in scene['nodes'])
    retained = [n for n in scene['nodes'] if n['id'].startswith('boundary-east-south-t5-retained-')]
    assert retained
    assert max(_world_vertices(scene, n)[:, 0].max() for n in retained) == pytest.approx(8.042)


def test_upper_revision_clears_retired_details_and_relocates_complete_pendants(delivery):
    scene, building = map(copy.deepcopy, delivery)
    retired = {'u-side-terrace-door', 'u-bedroom-terrace', 's2-stair-entry'}
    building['openings'][:] = [o for o in building['openings'] if o['id'] not in retired]
    building['planning']['upperPlan']['void'] = [[1250,4875], [6300,4875], [6300,6600], [1250,6600]]
    before = copy.deepcopy(building)
    _upper_revision_cleanup(scene, building)
    for node in scene['nodes']:
        assert node.get('owner') not in retired
        assert not any(node['id'].startswith(prefix + ident + '-')
                       for ident in retired for prefix in ('op-', 't4-exterior-finish-op-', 't5lux-reveal-'))
    assert not any('s2-stair-entry-canopy' == n['id'] for n in scene['nodes'])
    assert not retired.intersection(scene['door_motion'])
    moved = [n for n in scene['nodes'] if n.get('floor') == 1 and n.get('role') == 'fixture'
             and n['asset'] == 'unit-cylinder' and n['position'][2] > 4
             and any(abs(n['position'][0]-x)<1e-6 and abs(n['position'][1]-y)<1e-6
                     for x,y in [(3.1,5.8), (3.65,6.0), (4.05,5.65)])]
    assert len(moved) == 9
    assert all(_world_vertices(scene,n)[:,1].max() < 6.6 for n in moved)
    assert building == before


def test_new_guest_east_window_gets_reveals_at_new_wall(delivery):
    scene, building = map(copy.deepcopy, delivery)
    scene['nodes'][:] = [n for n in scene['nodes'] if not n['id'].startswith('t5lux-reveal-')]
    window = next(o for o in building['openings'] if o['id'] in ('u-bedroom-terrace', 'u-bedroom-east-proposed'))
    window.update(id='u-bedroom-east-proposed', a=[8750,6275], b=[11000,6275],
                  connects=['u-bedroom','outside'])
    _materials(scene)
    _opening_reveals(scene, building, _kit(scene))
    detail = [n for n in scene['nodes'] if n['id'].startswith('t5lux-reveal-u-bedroom-east-proposed-')]
    assert len(detail) == 4
    assert all(_world_vertices(scene,n)[:,1].max() < 6.3 for n in detail)
    assert not any(n['id'].startswith('t5lux-reveal-u-bedroom-terrace-') for n in scene['nodes'])


def test_insect_screen_target_tracks_a_rigid_visible_handle():
    """The screen must have a distinct real control, even when fully parked."""
    k = Kit(random.Random(0))
    op = {'id':'living-veranda', 'raw_kind':'door', 'a':[7300,6100],
          'b':[7300,7900], 'sill':0, 'height':2400}
    plan = {'entrance': {
        'woodStacks': [[7460,5950,7540,6050], [7460,7950,7540,8050]],
        'meshStacks': [[7210,6050,7224,6060], [7210,7940,7224,7950]],
    }}

    def span(lo,hi,v0,v1,z0,z1,material,role,name):
        # Axis north/south screen: its positive normal faces the living hall.
        polygon = Polygon([(7.3-v0,6.1+lo), (7.3-v0,6.1+hi),
                           (7.3-v1,6.1+hi), (7.3-v1,6.1+lo)])
        k.poly_mesh(polygon,z0,z1,material,0,role,'op-living-veranda-'+name)

    motion = build_opening(k,op,plan,span)
    screen = next(layer for layer in motion['layers'] if layer['id'].endswith('-mesh'))
    grip = next(n for n in k.nodes if n['id'].endswith('-mesh-leading-handle'))
    vertices = np.asarray(k.assets[grip['asset']]['vertices'])
    closed_center = (vertices.min(axis=0)+vertices.max(axis=0))/2
    assert screen['handle'] == pytest.approx(closed_center)
    assert screen['handle'] == pytest.approx([7.185,6.975,1.11])
    assert screen['parts'][0]['ids'] == [grip['id']]
    assert 'scaleTo' not in screen['parts'][0]
    closed_size = vertices.max(axis=0)-vertices.min(axis=0)
    assert closed_size == pytest.approx([.078,.03,.22])

    pose_initial_opening(k,motion)
    opened = np.asarray(k.assets[grip['asset']]['vertices'])
    open_center = (opened.min(axis=0)+opened.max(axis=0))/2
    assert screen['handle'] == pytest.approx(open_center)
    assert screen['handle'] == pytest.approx([7.102,6.0649375,1.11])
    # Kit assets quantize vertex coordinates to a micrometre on serialization.
    assert opened.max(axis=0)-opened.min(axis=0) == pytest.approx(closed_size,abs=2e-6)
    assert open_center+np.asarray(screen['parts'][0]['slide']) == pytest.approx(closed_center)
