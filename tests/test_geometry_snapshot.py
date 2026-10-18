import copy
import pytest
from geometry_snapshot import (assert_snapshot, assert_plate_snapshot, assert_visual_snapshot,
                               assert_nodes_snapshot, assert_unordered_snapshot)


def test_snapshot_tolerates_roundoff_but_rejects_position_and_material_changes():
    assert_snapshot({'x':1.0+1e-10,'material':'oak'},{'x':1.0,'material':'oak'})
    for changed in ({'x':1.001,'material':'oak'},{'x':1.0,'material':'glass'}):
        with pytest.raises(AssertionError):
            assert_snapshot(changed,{'x':1.0,'material':'oak'})


def test_plate_accepts_ring_start_change_but_rejects_a_new_opening():
    ring=[[0,0],[2,0],[2,2],[0,2]]
    expected=[{'id':'plate','regions':[{'polygon':ring,'holes':[]}]}]
    actual=copy.deepcopy(expected);actual[0]['regions'][0]['polygon']=ring[2:]+ring[:2]
    assert_plate_snapshot(actual,expected)
    actual[0]['regions'][0]['holes']=[[[.5,.5],[1,.5],[1,1],[.5,1]]]
    with pytest.raises(AssertionError):assert_plate_snapshot(actual,expected)


def test_visual_checks_mesh_even_when_cache_key_changes():
    mesh={'vertices':[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],'faces':[[0,1,2]],'normals':None,'closed':False}
    expected={'assets':{'old':mesh},'nodes':[{'id':'chair','asset':'old','material':'oak'}],
              **{key:[] for key in ('materials','lights','cameras','vegetation','lawns')}}
    actual=copy.deepcopy(expected);actual['assets']={'new':copy.deepcopy(mesh)};actual['nodes'][0]['asset']='new'
    assert_visual_snapshot(actual,expected)
    actual['assets']['new']['vertices'][1][0]=1.01
    with pytest.raises(AssertionError):assert_visual_snapshot(actual,expected)


def test_mesh_accepts_retriangulation_but_rejects_missing_faces():
    from geometry_snapshot import assert_mesh_snapshot
    mesh={'vertices':[[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]],
          'faces':[[0,1,2],[0,2,3]],'normals':None,'closed':False}
    other=copy.deepcopy(mesh);other['faces']=[[0,1,3],[1,2,3]]
    assert_mesh_snapshot(other,mesh,'slab')
    other['faces'].pop()
    with pytest.raises(AssertionError):assert_mesh_snapshot(other,mesh,'slab')
    other=copy.deepcopy(mesh);other['faces']=[[2,1,0],[3,2,0]]
    with pytest.raises(AssertionError):assert_mesh_snapshot(other,mesh,'slab')


def test_visual_matches_anonymous_parts_by_geometry_not_traversal_index():
    mesh={'vertices':[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],'faces':[[0,1,2]],'normals':None,'closed':False}
    other=copy.deepcopy(mesh);other['vertices']=[[x+2,y,z] for x,y,z in other['vertices']]
    expected={'assets':{'left':mesh,'right':other},
              'nodes':[{'id':'object-00001','owner':'object-00001','asset':'left','material':'oak'},
                       {'id':'object-00002','owner':'object-00002','asset':'right','material':'oak'}],
              **{key:[] for key in ('materials','lights','cameras','vegetation','lawns')}}
    actual=copy.deepcopy(expected)
    actual['nodes'][0]['asset']='right';actual['nodes'][1]['asset']='left'
    assert_visual_snapshot(actual,expected)
    actual['nodes'][0]['material']='glass'
    with pytest.raises(AssertionError):assert_visual_snapshot(actual,expected)


def test_visual_order_is_not_changed_by_signed_zero():
    mesh={'vertices':[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]],'faces':[[0,1,2]],'normals':None,'closed':False}
    expected={'assets':{'mesh':mesh},
              'nodes':[{'id':'object-1','asset':'mesh','position':[0.,1.,0.]},
                       {'id':'object-2','asset':'mesh','position':[0.,2.,0.]}],
              **{key:[] for key in ('materials','lights','cameras','vegetation','lawns')}}
    actual=copy.deepcopy(expected);actual['nodes'][1]['position'][0]=-0.0
    assert_visual_snapshot(actual,expected)


def test_ring_accepts_another_start_vertex_but_rejects_a_moved_outline():
    ring=[[0.,0.],[2.,0.],[2.,1.],[0.,1.]];expected={'id':'wall/0','polygon':ring}
    # A rotated start, an explicit closing vertex or a collinear vertex keeps the outline.
    for same in (ring[2:]+ring[:2],ring+ring[:1],[[0.,0.],[1.,0.],*ring[1:]]):
        assert_snapshot({'id':'wall/0','polygon':same},expected,rings=('polygon',))
    for changed in ([[x+.01,y] for x,y in ring],[[0.,0.],[2.,0.],[2.,1.],[0.,.5]],ring[:3]):
        with pytest.raises(AssertionError):assert_snapshot({'id':'wall/0','polygon':changed},expected,rings=('polygon',))


def test_nodes_match_whatever_their_order_mesh_key_or_rounding():
    square={'vertices':[[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]],'faces':[[0,1,2],[0,2,3]],'normals':None,'closed':False}
    other=copy.deepcopy(square);other['faces']=[[0,1,3],[1,2,3]]
    # Either side of a rounding boundary of the pairing key, yet within tolerance.
    low,high=1.000000005-1e-13,1.000000005+1e-13
    assert round(low,8)!=round(high,8)
    expected=[{'asset':'a','material':'oak','position':[low,0.,0.]},{'asset':'b','material':'oak','position':[3.,0.,0.]}]
    actual=[{'asset':'b2','material':'oak','position':[3.,0.,0.]},{'asset':'a2','material':'oak','position':[high,0.,0.]}]
    recorded={'a':square,'b':square};rebuilt={'a2':copy.deepcopy(other),'b2':copy.deepcopy(other)}
    assert_nodes_snapshot(actual,expected,rebuilt,recorded)
    for edit in ({'position':[3.01,0.,0.]},{'material':'glass'}):
        changed=copy.deepcopy(actual);changed[0].update(edit)
        with pytest.raises(AssertionError):assert_nodes_snapshot(changed,expected,rebuilt,recorded)
    rebuilt['b2']['vertices'][2]=[1.,1.01,0.]
    with pytest.raises(AssertionError):assert_nodes_snapshot(actual,expected,rebuilt,recorded)


def test_restored_node_without_recorded_mesh_is_compared_by_cache_key():
    restored=[{'asset':'never-recorded','material':'oak','position':[0.,0.,0.]}]
    assert_nodes_snapshot(copy.deepcopy(restored),restored,{},{})
    with pytest.raises(AssertionError):assert_nodes_snapshot([{**restored[0],'asset':'other'}],restored,{},{})


def test_unordered_records_tolerate_roundoff_but_not_a_brighter_light():
    lights=[{'kind':'porch','position':[12.774,.4,2.95],'power_w':12},{'kind':'porch','position':[16.038,8.8,2.95],'power_w':12}]
    actual=copy.deepcopy(lights[::-1]);actual[1]['position'][0]+=2e-15
    assert_unordered_snapshot(actual,lights,'lights')
    actual[0]['power_w']=14
    with pytest.raises(AssertionError):assert_unordered_snapshot(actual,lights,'lights')
