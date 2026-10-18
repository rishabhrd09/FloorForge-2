"""Compare geometry snapshots without treating machine rounding as design edits."""
import math,json
from numbers import Real
from collections import defaultdict
import numpy as np
from shapely.geometry import Polygon,LinearRing
from shapely.ops import unary_union
from floorforge.plan_geometry import geometry


def assert_snapshot(actual, expected, path='root', tolerance=1e-8, rings=()):
    # Keys named in rings hold polygon outlines, such as collider footprints.
    if isinstance(expected, dict):
        assert actual.keys()==expected.keys(), path
        for key in expected:
            if key in rings:assert_ring_snapshot(actual[key],expected[key],f'{path}.{key}',tolerance)
            else:assert_snapshot(actual[key],expected[key],f'{path}.{key}',tolerance,rings)
    elif isinstance(expected,list):
        assert len(actual)==len(expected), f'{path}: item count changed'
        for i,(a,e) in enumerate(zip(actual,expected)):
            assert_snapshot(a,e,f'{path}[{i}]',tolerance,rings)
    elif isinstance(expected,Real) and not isinstance(expected,bool):
        assert math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance), f'{path}: {actual} != {expected}'
    else:
        assert actual==expected, f'{path}: {actual!r} != {expected!r}'


def assert_ring_snapshot(actual,expected,path,tolerance=1e-8):
    # A GEOS overlay can start an unchanged outline at another vertex or keep a
    # collinear one, so compare where the outline lies rather than its vertex list.
    if min(len(actual),len(expected))<3:
        assert_snapshot(actual,expected,path,tolerance);return
    a,e=LinearRing(actual),LinearRing(expected)
    assert a.hausdorff_distance(e)<=tolerance and abs(Polygon(a).area-Polygon(e).area)<1e-9, f'{path}: outline changed'


def assert_mesh_snapshot(actual,expected,path):
    if actual==expected:return
    assert actual['closed']==expected['closed'],path
    # GEOS/Trimesh can reorder vertices or choose the opposite diagonal across
    # a planar face. Compare the complete oriented surface on each plane, so
    # holes, face winding and dimensions remain checked independently of indices.
    def surfaces(mesh):
        groups=defaultdict(list);vertices=np.asarray(mesh['vertices'])
        for face in mesh['faces']:
            tri=vertices[face];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0])
            length=np.linalg.norm(normal)
            if length<1e-12:continue
            normal/=length
            plane=tuple(round(float(v),5) for v in (*normal,np.dot(normal,tri[0])))
            axis=int(np.argmax(np.abs(normal)))
            groups[(plane,axis)].append(Polygon(np.delete(tri,axis,axis=1)))
        return {key:unary_union(value) for key,value in groups.items()}
    ag,eg=surfaces(actual),surfaces(expected)
    assert ag.keys()==eg.keys(),f'{path}: surface planes changed'
    for plane in eg:
        assert ag[plane].symmetric_difference(eg[plane]).area<1e-9,f'{path}: surface changed on {plane}'
    if expected['normals'] is None:
        assert actual['normals'] is None,path
    else:
        def vertex_normals(mesh):
            return sorted([*v,*n] for v,n in zip(mesh['vertices'],mesh['normals']))
        assert_snapshot(vertex_normals(actual),vertex_normals(expected),path+'.normals',tolerance=2e-6)


def metadata(node):
    # Anonymous nodes inherit traversal indices from GEOS multipart output.
    # Named semantic objects retain their identity in the comparison.
    return {k:v for k,v in node.items() if k!='asset'
            and not (k in ('id','owner') and isinstance(v,str) and v.startswith('object-'))}


def sort_value(value):
    if isinstance(value,dict):return {k:sort_value(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [sort_value(v) for v in value]
    if isinstance(value,float):
        rounded=round(value,8)
        return rounded if rounded else 0.0
    return value


def same_snapshot(actual,expected,**options):
    try:assert_snapshot(actual,expected,**options)
    except AssertionError:return False
    return True


def record_matcher(**options):
    """Equality and pairing keys for plain records such as lights or colliders."""
    def key(item):return json.dumps(sort_value(item),sort_keys=True)
    return (lambda a,e:same_snapshot(a,e,**options)),key,key


def node_matcher(actual_assets,expected_assets,fields=metadata):
    """Equality and pairing keys that identify a node by its fields and mesh surface."""
    checked={}
    def pairing(assets):
        bounds={}
        def key(node):
            # A node restored from a fixture whose mesh was never recorded can only
            # be paired, and compared, by its mesh cache key.
            name=node['asset']
            if name in assets and name not in bounds:
                vertices=np.asarray(assets[name]['vertices'])
                bounds[name]=np.round([vertices.min(axis=0),vertices.max(axis=0)],6).tolist()
            return json.dumps(sort_value([fields(node),bounds.get(name,name)]),sort_keys=True)
        return key
    def same(a,e):
        if not same_snapshot(fields(a),fields(e)):return False
        am,em=actual_assets.get(a['asset']),expected_assets.get(e['asset'])
        if am is None or em is None:return am is None and em is None and a['asset']==e['asset']
        pair=a['asset'],e['asset']
        if pair not in checked:
            try:assert_mesh_snapshot(am,em,'mesh');checked[pair]=True
            except AssertionError:checked[pair]=False
        return checked[pair]
    return same,pairing(actual_assets),pairing(expected_assets)


def unpaired(actual,expected,same,actual_key,expected_key):
    """Pair two lists as multisets; return the items of each left without a partner."""
    pools=defaultdict(list)
    for e in expected:pools[expected_key(e)].append(e)
    left=[]
    for a in actual:
        pool=pools.get(actual_key(a),[])
        i=next((i for i,e in enumerate(pool) if same(a,e)),None)
        if i is None:left.append(a)
        else:del pool[i]
    missing=[e for pool in pools.values() for e in pool]
    # A rounded key splits a pair when a coordinate on a rounding boundary rounds
    # the other way on another platform, so compare the leftovers directly.
    rest=[]
    for a in left:
        i=next((i for i,e in enumerate(missing) if same(a,e)),None)
        if i is None:rest.append(a)
        else:del missing[i]
    return rest,missing


def assert_unordered_snapshot(actual,expected,path='root',**options):
    unexpected,missing=unpaired(actual,expected,*record_matcher(**options))
    assert not unexpected and not missing, f'{path}: unexpected {unexpected[:3]}, missing {missing[:3]}'


def assert_nodes_snapshot(actual,expected,actual_assets,expected_assets,path='nodes'):
    """Compare nodes in any order by metadata and mesh surface, whatever their mesh cache keys."""
    unexpected,missing=unpaired(actual,expected,*node_matcher(actual_assets,expected_assets))
    # Keep CI failures reviewable without exporting an entire scene.
    assert not unexpected and not missing, (f'{path}: {len(unexpected)} unexpected, e.g. {[metadata(n) for n in unexpected[:3]]}; '
                                           f'{len(missing)} missing, e.g. {[metadata(n) for n in missing[:3]]}')


def assert_visual_snapshot(actual,expected):
    # Mesh cache keys can encode signed zero or floating-point rounding. Compare
    # the referenced meshes themselves, including topology and smooth normals.
    assert len(actual['assets'])==len(expected['assets'])
    assert len(actual['nodes'])==len(expected['nodes'])
    assert_nodes_snapshot(actual['nodes'],expected['nodes'],actual['assets'],expected['assets'])
    for key in ('materials','lights','cameras','vegetation','lawns'):
        assert_snapshot(actual[key],expected[key],key)


def assert_plate_snapshot(actual,expected):
    assert len(actual)==len(expected)
    for a,e in zip(actual,expected):
        assert a.keys()==e.keys()
        for key in e:
            if key in ('outline','regions'):
                ag,eg=geometry(a[key]),geometry(e[key])
                assert ag.equals(eg), f"{a['id']}.{key}: slab geometry changed"
            else:
                assert_snapshot(a[key],e[key],f"{a['id']}.{key}")
