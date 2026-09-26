import copy

import pytest

from floorforge.exterior import (
    EXTERIOR_THEME_IDS,
    INTERIOR_THEME_IDS,
    apply_exterior_preferences,
    protected_interior_fingerprint,
)
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import reports, validate
from floorforge.scene import make_scene
from floorforge.drawings import make_sheets


BASE_BRIEF = {
    'width_mm': 12192,
    'depth_mm': 18288,
    'bedrooms': 3,
    'storeys': 2,
    'front_mm': 3300,
}


def revised(exterior='warm_modern_minimal', interior='current'):
    payload={'schema':'floorforge.project/0.3','brief':{
        **BASE_BRIEF,
        'exterior_theme':exterior,
        'interior_theme':interior,
    }}
    return apply_exterior_preferences(generate_layout(fuse(payload)))


def test_legacy_projects_keep_current_exterior_until_opted_in():
    legacy=fuse({'brief':{}})
    modern=fuse({'schema':'floorforge.project/0.3','brief':{}})
    assert legacy['values']['exterior_theme']=='current'
    assert legacy['values']['interior_theme']=='current'
    assert modern['values']['exterior_theme']=='modern_tropical'
    assert modern['values']['interior_theme']=='bright_natural'


@pytest.mark.parametrize('theme',EXTERIOR_THEME_IDS[1:])
def test_exterior_theme_is_real_coordinated_geometry(theme):
    building=revised(theme)
    before=protected_interior_fingerprint(building)
    assert building['exterior']['theme']==theme
    assert building['exterior']['assemblies']
    assert building['exterior']['landscape']['features']
    assert building['exterior']['protected_interior_before']==before
    assert building['exterior']['protected_interior_after']==before
    review=validate(building)
    report=reports(building,review)
    scene=make_scene(building,report)
    roles={node['role'] for node in scene['nodes']}
    assert roles.intersection({'porch','balcony','screen','pergola','accent'})
    assert 'landscape' in roles
    assert len(make_sheets(building,scene,report))==9


def test_interior_palette_changes_materials_without_layout_change():
    warm=revised('warm_modern_minimal','warm_contemporary')
    quiet=revised('warm_modern_minimal','quiet_minimal')
    assert protected_interior_fingerprint(warm)==protected_interior_fingerprint(quiet)
    r1=reports(warm,validate(warm));r2=reports(quiet,validate(quiet))
    s1=make_scene(warm,r1);s2=make_scene(quiet,r2)
    geometry=lambda s:[{k:n[k] for k in ('id','asset','position','scale','rotation','floor','role','owner')} for n in s['nodes']]
    assert geometry(s1)==geometry(s2)
    assert s1['materials']['fabric']['color']!=s2['materials']['fabric']['color']


def test_exterior_change_set_updates_shared_opening_record():
    building=revised('tropical_verandah')
    changes=building['exterior']['opening_changes']
    assert changes
    openings={o['id']:o for o in building['openings']}
    for change in changes:
        opening=openings[change['opening_id']]
        assert opening['width']==change['after']['width']
        assert change['dependents']
        assert change['review_status']=='accepted_for_geometry_screen'
