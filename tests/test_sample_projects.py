import json
from pathlib import Path
import pytest
from floorforge.sample_projects import catalogue,sample_file,ROOT
from floorforge.intent import fuse

@pytest.mark.parametrize('sample',catalogue(),ids=lambda s:s['id'])
def test_every_sample_is_complete_and_its_starter_matches_the_3d(sample):
    slug=sample['id'];read=lambda n:json.loads(sample_file(slug,n).read_text(encoding='utf-8'))
    building=read('building.json');project=read('project.floorforge.json');project['brief']=building['brief']
    assert fuse(project)['planHash']==sample['planHash']
    def browser_numbers(value):
        if isinstance(value,float) and value.is_integer():return int(value)
        if isinstance(value,dict):return {k:browser_numbers(v) for k,v in value.items()}
        if isinstance(value,list):return [browser_numbers(v) for v in value]
        return value
    assert fuse(browser_numbers(read('project.floorforge.json')))['planHash']==sample['planHash']
    for filename in ['building.json','scene.json','report.json','intent.json']:
        assert read(filename)['planHash']==sample['planHash']
    assert all(s['planHash']==sample['planHash'] for s in read('sheets.json'))
    for filename in ['preview.html','drawings.pdf','floorplans.dxf','model.glb','model.ifc','FloorForge-export.zip']:
        assert sample_file(slug,filename).stat().st_size>100
    assert building['brief']['bedrooms']==sample['bedrooms']
    assert building['storeys']==sample['storeys']
    assert sample['roofAccess']==bool(building.get('rooftop'))


def test_sample_route_rejects_unknown_projects_and_traversal():
    assert sample_file('missing','scene.json') is None
    assert sample_file('saved-verandah','../../../web/app.js') is None
    assert sample_file('original','/etc/passwd') is None


def test_gallery_is_a_mix_of_scales_and_designs():
    samples=catalogue()
    assert len(samples)>=5
    assert len({s['planHash'] for s in samples})==len(samples)
    assert {1,2} <= {s['storeys'] for s in samples}
    assert {1,2,3,4} <= {s['bedrooms'] for s in samples}
    assert all('directory' not in s for s in samples)


def test_saved_favourite_contains_only_the_published_design():
    p=json.loads(sample_file('saved-verandah','project.floorforge.json').read_text(encoding='utf-8'))
    assert set(p)=={'schema','brief'}
    assert not any(k in p for k in ('attachments','editorState','sources','text'))
