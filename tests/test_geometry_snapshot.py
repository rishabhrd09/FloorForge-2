import copy
import pytest
from geometry_snapshot import assert_snapshot, assert_plate_snapshot, assert_visual_snapshot


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
