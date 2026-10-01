import copy
import json
import pytest
from shapely.geometry import Polygon
from floorforge.model import DesignError, sha
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.exterior import apply_exterior_preferences
from floorforge.review import validate, reports
from floorforge.scene import make_scene
from floorforge.placement_edits import apply_furniture_edits

PROJECT={'schema':'floorforge.project/0.4','brief':{'roof_access':True}}

@pytest.fixture(scope='module')
def design():
    b=apply_exterior_preferences(generate_layout(fuse(PROJECT)))
    return b,make_scene(b,reports(b,validate(b)))


def movement(scene,dx=.2,dy=0,angle=0):
    item=next(i for i in scene['editables'] if i['id']=='F0-living/coffee-table')
    return dict(id=item['id'],anchorHash=item['anchorHash'],dx=dx,dy=dy,angle=angle)


def test_default_roof_is_not_an_occupied_third_floor(design):
    b,s=design
    assert b['storeys']==2 and len(b['floors'])==2 and s['roof_level']==2
    assert b['stairs'][-1]['to_floor']==2
    assert not any(r['floor']==2 for r in b['spaces'])


def test_complete_table_move_keeps_every_other_render_object(design):
    b,s=design;edit=movement(s);m=apply_furniture_edits(copy.deepcopy(s),{**b,'furnitureLayout':[edit]})
    item=next(i for i in s['editables'] if i['id']==edit['id']);ids=set(item['nodeIds'])
    assert len(ids)>=5 # top, supports, book and vase
    for original,moved in zip(s['nodes'],m['nodes']):
        if original['id'] not in ids:assert original==moved
        else:
            assert moved['position'][0]==pytest.approx(original['position'][0]+.2)
            assert moved['position'][1:]==original['position'][1:]
            assert {k:v for k,v in moved.items() if k!='position'}=={k:v for k,v in original.items() if k!='position'}
    for key in ('assets','materials','lights','cameras','vegetation','lawns'):assert s[key]==m[key]
    for key,field in [('furniture','footprint'),('colliders','polygon')]:
        a=next(i for i in s[key] if i['id']==edit['id']);c=next(i for i in m[key] if i['id']==edit['id'])
        assert Polygon(c[field]).centroid.x-Polygon(a[field]).centroid.x==pytest.approx(.2)


def test_rotation_preserves_models_and_pivot(design):
    b,s=design;edit=movement(s,0,0,90);m=apply_furniture_edits(copy.deepcopy(s),{**b,'furnitureLayout':[edit]})
    item=next(i for i in m['editables'] if i['id']==edit['id'])
    assert Polygon(item['currentFootprint']).centroid.coords[0]==pytest.approx(item['pivot'])
    assert m['assets']==s['assets'] and m['materials']==s['materials']


@pytest.mark.parametrize('dx,dy',[(100,0),(0,100)])
def test_invalid_move_blocks_instead_of_silently_relocating(design,dx,dy):
    b,s=design
    with pytest.raises(DesignError,match='must fit inside'):apply_furniture_edits(copy.deepcopy(s),{**b,'furnitureLayout':[movement(s,dx,dy)]})


def test_stale_item_rejected_and_hash_save_roundtrip(design):
    b,s=design;e=movement(s);p={**PROJECT,'furnitureLayout':[e]}
    assert fuse(p)['planHash']!=fuse(PROJECT)['planHash']
    assert fuse(p)['planHash']==fuse(json.loads(json.dumps(p)))['planHash']
    e['anchorHash']='outdated'
    with pytest.raises(DesignError,match='different room layout'):apply_furniture_edits(copy.deepcopy(s),{**b,'furnitureLayout':[e]})


def test_room_swap_preserves_requested_slots_and_roof(design):
    b,s=design;a,c=[next(r for r in b['roomEditBase'] if r['id']==id) for id in ('F1-bed-m','F1-bed-2')]
    edits=[{'id':r['id'],'anchorHash':r['anchorHash'],'polygon':t['polygon']} for r,t in ((a,c),(c,a))]
    moved=generate_layout(fuse({**PROJECT,'roomEdits':edits}));validate(moved)
    assert next(r for r in moved['spaces'] if r['id']==a['id'])['polygon']==c['polygon']
    assert moved['storeys']==2 and moved['rooftop']['floor']==2
    assert moved['walls']!=b['walls'] and moved['openings']!=b['openings']


def test_room_overlap_reports_both_objects(design):
    b,s=design;a,c=b['roomEditBase'][1:3]
    with pytest.raises(DesignError) as caught:generate_layout(fuse({**PROJECT,'roomEdits':[{'id':a['id'],'anchorHash':a['anchorHash'],'polygon':c['polygon']}]}))
    assert caught.value.code=='ROOM_OVERLAP' and set(caught.value.details['ids'])=={a['id'],c['id']}


def test_empty_edits_keep_legacy_intent_hash():
    assert fuse(PROJECT)['planHash']==fuse({**PROJECT,'roomEdits':[],'furnitureLayout':[]})['planHash']


@pytest.mark.parametrize('edit',[{'id':'x','anchorHash':'x','dx':float('nan'),'dy':0,'angle':0},{'id':'x','anchorHash':'x','dx':0,'dy':0,'angle':True}])
def test_nonfinite_or_boolean_positions_rejected(edit):
    with pytest.raises(DesignError):fuse({**PROJECT,'furnitureLayout':[edit]})


def test_furniture_meshes_reach_ifc_and_glb(design):
    import io
    import re
    import numpy as np
    import trimesh
    from floorforge.scene import glb_bytes, transformation
    from floorforge.ifc_export import export_ifc
    b,s=design;e=movement(s);m=apply_furniture_edits(copy.deepcopy(s),{**b,'furnitureLayout':[e]})
    item=next(i for i in m['editables'] if i['id']==e['id'])
    glb=trimesh.load(io.BytesIO(glb_bytes(m)),file_type='glb',force='scene')
    node=next(n for n in m['nodes'] if n['id']==item['nodeIds'][0])
    convert=trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0])
    assert glb.graph[node['id']][0]==pytest.approx(convert @ transformation(node),abs=1e-5)
    data,check=export_ifc(b,m);text=data.decode('ascii')
    assert check['furnishing_count']==len(m['editables'])
    assert text.count('=IFCFURNISHINGELEMENT(')==len(m['editables'])
    assert "'F0-living/coffee-table'" in text and '=IFCTRIANGULATEDFACESET(' in text
    refs={int(x) for x in re.findall(r'#(\d+)',text)}
    defined={int(x) for x in re.findall(r'#(\d+)=',text)}
    assert refs==defined
