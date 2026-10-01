"""Option A: a true sky gap, separate usable decks and bounded ground changes."""
import json
from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import Polygon, LineString, MultiPoint, box
from shapely.ops import unary_union
from shapely.affinity import scale
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.model import DesignError
from floorforge.plan_geometry import geometry
from floorforge.scene import transformation
from scripts.build_desired_home import project

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def model():
    base=ROOT/'examples/gallery/my-desired-home'
    return json.loads((base/'building.json').read_text()),json.loads((base/'scene.json').read_text())


def vertices(scene,node):
    v=np.array(scene['assets'][node['asset']]['vertices'])
    return (np.c_[v,np.ones(len(v))] @ transformation(node).T)[:,:3]


def footprint(scene,node):
    v=vertices(scene,node)
    faces=scene['assets'][node['asset']]['faces']
    triangles=[Polygon(v[face,:2]) for face in faces]
    return unary_union([p for p in triangles if p.area>1e-10])


def test_open_veranda_has_no_bridge_floating_guard_or_cover(model):
    b,s=model;rooms={r['id']:r for r in b['spaces']}
    gap=Polygon(rooms['u-garden-daylight']['clear'])
    assert gap.equals(Polygon(rooms['g-veranda']['clear']))
    assert geometry(b['floor_plates'][1]['regions']).intersection(gap).area<1
    for roof in b['roofs']:
        for key in ('regions','ceiling'):assert geometry(roof[key]).intersection(gap).area<1
    assert geometry(b['rooftop']['slab']).intersection(gap).area<1
    # Guards follow occupied edges only; no freestanding box in the void.
    assert not any(g['owner']=='u-garden-daylight' for g in b['guards'])
    for owner,line in [('u-terrace-front',[(11451,5800),(15089,5800)]),('u-terrace-north',[(15439,8400),(18137,8400)])]:
        guards=unary_union([LineString(g['points']) for g in b['guards'] if g['owner']==owner])
        assert guards.buffer(1).covers(LineString(line))
    assert not any(n['owner']=='g-veranda' and n['role']=='ceiling' for n in s['nodes'])
    assert not any(w['id']=='u-balcony-privacy' for w in b['walls'])


def test_separate_glass_roofs_are_sloped_supported_and_outside_gap(model):
    b,s=model;gap=box(11.45,5.8,18.138,8.4)
    for r in [r for r in b['spaces'] if r.get('canopyStyle')]:
        p=Polygon(np.array(r['clear'])/1000)
        panes=[n for n in s['nodes'] if n['owner']==r['id'] and n['material']=='canopy-glass']
        assert panes and s['materials']['canopy-glass']['alpha']<.3
        glass=unary_union([footprint(s,n) for n in panes])
        assert glass.area>p.buffer(-.035,join_style=2).area*.80
        assert p.covers(glass) and glass.intersection(gap).area<1e-7
        for pane in panes:
            v=vertices(s,pane)
            assert v[:,2].min()>5.5  # roof above head, never a glass floor
            flat=v[:,2]+.025*v[:,0]
            assert abs(np.ptp(flat)-.020)<1e-5
        for q in r['canopyPosts']:
            assert any(n['owner']==r['id'] and '/canopy-post-' in n['id'] and footprint(s,n).covers(MultiPoint([[q[0]/1000,q[1]/1000]])) for n in s['nodes'])
        assert any(n['id']==r['id']+'/gutter-bottom' for n in s['nodes'])
        assert any(n['id']==r['id']+'/gutter-outlet' for n in s['nodes'])
        assert any(n['id']==r['id']+'/drain-outlet' for n in s['nodes'])


def test_balcony_columns_reach_ground_without_blocking_paved_route(model):
    b,s=model;r=next(r for r in b['spaces'] if r['id']=='u-terrace-north')
    columns=[n for n in s['nodes'] if n['owner']==r['id'] and '/ground-column-' in n['id']]
    assert len(columns)==3
    route=box(11.6,5.95,18.0,7.4)
    for n,q in zip(columns,r['supportColumns']):
        v=vertices(s,n)
        assert v[:,2].min()<0 and v[:,2].max()>2.9
        assert footprint(s,n).intersection(route).area==0
        assert np.allclose(v[:,:2].mean(axis=0),np.array(q)/1000)
        assert any(c['id']==n['id'] and c['floor']==0 for c in s['colliders'])
    # The actual ground furnishings and plants (not merely restored snapshots) stay fixed.
    prior=json.loads((ROOT/'tests/fixtures/desired_home_before_open_veranda.json').read_text())
    for key in ('furniture','vegetation'):
        assert [n for n in s[key] if n.get('floor') in(-1,0)]==prior['ground_'+key]
    old=geometry(prior['ground_roof']['ceiling']);new=geometry(b['roofs'][0]['ceiling'])
    assert old.difference(box(11450,5800,18138,8400)).equals(new)
    # Existing fixed TV-side window and operable paired care doors are retained.
    ops={o['id']:o for o in b['openings']}
    assert ops['g-care-lawn-window']['fixed']
    assert ops['g-care-veranda']['slidingPanels']==2
    assert ops['g-caregiver-garden-door']['kind']=='door'


@pytest.mark.parametrize('field,value',[('canopyStyle','opaque'),('canopyPosts',[[18000,7000]]),('supportColumns',[[17700,9000]])])
def test_invalid_canopy_geometry_is_rejected(field,value):
    p=project();r=next(r for r in p['customPlan']['floors'][1]['rooms'] if r['id']=='u-terrace-north');r[field]=value
    with pytest.raises(DesignError):generate_layout(fuse(p))
