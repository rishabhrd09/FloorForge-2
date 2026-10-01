"""Compare geometry snapshots without treating machine rounding as design edits."""
import math
from numbers import Real
from floorforge.plan_geometry import geometry


def assert_snapshot(actual, expected, path='root', tolerance=1e-8):
    if isinstance(expected, dict):
        assert actual.keys()==expected.keys(), path
        for key in expected:
            assert_snapshot(actual[key],expected[key],f'{path}.{key}',tolerance)
    elif isinstance(expected,list):
        assert len(actual)==len(expected), f'{path}: item count changed'
        for i,(a,e) in enumerate(zip(actual,expected)):
            assert_snapshot(a,e,f'{path}[{i}]',tolerance)
    elif isinstance(expected,Real) and not isinstance(expected,bool):
        assert math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance), f'{path}: {actual} != {expected}'
    else:
        assert actual==expected, f'{path}: {actual!r} != {expected!r}'


def assert_visual_snapshot(actual,expected):
    # Mesh cache keys can encode signed zero or floating-point rounding. Compare
    # the referenced meshes themselves, including topology and smooth normals.
    assert len(actual['assets'])==len(expected['assets'])
    assert len(actual['nodes'])==len(expected['nodes'])
    checked=set()
    for a,e in zip(actual['nodes'],expected['nodes']):
        assert_snapshot({k:v for k,v in a.items() if k!='asset'},
                        {k:v for k,v in e.items() if k!='asset'},a['id'])
        pair=(a['asset'],e['asset'])
        if pair not in checked:
            assert_snapshot(actual['assets'][pair[0]],expected['assets'][pair[1]],
                            f"mesh for {a['id']}",tolerance=1e-6)
            checked.add(pair)
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
