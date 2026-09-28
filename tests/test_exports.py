import io,json,re,pytest
from pathlib import Path
import trimesh
from shapely.geometry import Polygon
from floorforge.scene import glb_bytes
from floorforge.drawings import make_sheets,pdf_sheets,dxf_export,svg_sheet,plan_elements,opening_types,schedule_tables,section_cut
from floorforge.ifc_export import export_ifc,guid
from floorforge.review import reports,validate
from floorforge.pipeline import run
from floorforge.model import *

def test_scene_units_and_semantics(scene):
    assert scene['units']=='m' and scene['up']=='Z'
    assert max(x for x,y in scene['footprint'])<50
    ids=[n['id'] for n in scene['nodes']];assert len(ids)==len(set(ids))
    assert all(n['asset'] in scene['assets'] for n in scene['nodes'])

def test_visible_fixture_lights_only(scene):assert all(l['fixture_visible'] for l in scene['lights'])

def test_glb_roundtrip(scene):
    raw=glb_bytes(scene);s=trimesh.load(io.BytesIO(raw),file_type='glb',force='scene')
    assert len(s.graph.nodes_geometry)==len(scene['nodes']);assert raw[:4]==b'glTF'
    assert s.bounds[1,0]-s.bounds[0,0]<100

def test_furniture_footprints_within_physical_clear_space(model,scene):
    rooms={s['id']:Polygon([[x/1000,y/1000] for x,y in s['clear']]) for s in model['spaces']}
    # Living and dining are named zones of one continuous open room, not walls.
    from shapely.ops import unary_union
    for space in model['spaces']:
        if space['kind'] in ('living','dining'):
            rooms[space['id']]=unary_union([Polygon([[x/1000,y/1000] for x,y in s['clear']])
                for s in model['spaces'] if s['floor']==space['floor'] and s['kind'] in ('living','dining')])
    for item in scene['furniture']:
        assert rooms[item['room_id']].buffer(.015).covers(Polygon(item['footprint'])),item['id']

def test_roof_does_not_cover_terrace(model,scene):
    terrace=next(s for s in model['spaces'] if s['kind']=='terrace');p=Polygon([[x/1000,y/1000] for x,y in terrace['polygon']])
    roof=next(n for n in scene['nodes'] if n['id']=='roof-slab');mesh=scene['assets'][roof['asset']]
    for face in mesh['faces']:
        vs=[mesh['vertices'][i] for i in face]
        if max(v[2] for v in vs)-min(v[2] for v in vs)<1e-5:
            q=Polygon([[v[0],v[1]] for v in vs]);assert q.intersection(p).area<1e-6

def test_svg_and_pdf_sheet_geometry(model,scene):
    r=reports(model,validate(model));s=make_sheets(model,scene,r)
    assert len(s)==10 and {'A-101','A-301','A-601','S-001'}<={x['id'] for x in s}
    assert all(x['scale'] in (50,75,100,125) for x in s if x['id'].startswith('A-10'))
    assert 'width="420mm" height="297mm"' in svg_sheet(s[0],model)
    data=pdf_sheets(s,model,r);assert data.startswith(b'%PDF-')
    try:
        import fitz
        pdf=fitz.open(stream=data,filetype='pdf');assert len(pdf)>=13
        assert abs(pdf[0].rect.width-420/25.4*72)<1
        for p in pdf:assert 'PRELIMINARY' in p.get_text()
    except ImportError:pass

def test_dxf_dimensions_and_units(model,scene,tmp_path):
    p=tmp_path/'model.dxf';check=dxf_export(model,scene,p);assert check['status']=='ezdxf_reimport_pass'
    assert check['dimension_entities']==check['dimension_chains']>=20
    import ezdxf
    doc=ezdxf.readfile(p);assert doc.units==4;assert all(k in doc.layers for k in ['A-WALL','A-DOOR','A-WIND','A-DIMS'])

def test_ifc_semantics_and_reference_integrity(model):
    raw,r=export_ifc(model);text=raw.decode('ascii');assert "FILE_SCHEMA(('IFC4'))" in text
    assert len(re.findall(r'=IFCWALL\(',text))==len(model['walls'])
    assert len(re.findall(r'=IFCRELVOIDSELEMENT\(',text))==len(model['openings'])
    assert len(re.findall(r'=IFCSPACE\(',text))==len(model['spaces'])
    assert r['independent_schema_validation']=='NOT RUN'
    assert len(guid('hello'))==22 and guid('hello')==guid('hello')

def test_cache_tampering_is_detected(tmp_path):
    run({'brief':{}},tmp_path,target='intent');p=next((tmp_path/'.cache/intent').glob('*.json'));d=read_json(p);d['data']['values']['bedrooms']=8;atomic(p,canonical(d))
    with pytest.raises(DesignError) as e:run({'brief':{}},tmp_path,target='intent')
    assert e.value.code=='CACHE_CORRUPT'

def test_pipeline_target_only_runs_dependencies(tmp_path):
    result=run({'brief':{}},tmp_path,target='layout');names=[s['stage'] for s in result['stages']]
    assert names==['intent','programme','layout'];assert not (tmp_path/'.cache/scene').exists()


def test_dxf_bytes_repeat_on_clean_export(model,scene,tmp_path):
    first=tmp_path/'first.dxf';second=tmp_path/'second.dxf'
    dxf_export(model,scene,first);dxf_export(model,scene,second)
    assert first.read_bytes()==second.read_bytes()


def test_plan_chains_close_on_the_footprint_and_every_opening_is_tagged(model,scene):
    W,D=Polygon(model['footprint']).bounds[2:];tags,rows=opening_types(model)
    for f in range(model['storeys']):
        elems,_=plan_elements(model,scene,f);dims=[e for e in elems if e['type']=='dim']
        for axis,span in (('x',W),('y',D)):
            spans=[abs(e['p2'][0 if axis=='x' else 1]-e['p1'][0 if axis=='x' else 1]) for e in dims if e['axis']==axis]
            # Each side's overall figure is the building's full extent, and its chains add up to it.
            assert spans.count(span)>=2
            assert abs(sum(spans)-span*round(sum(spans)/span))<2
        texts=[e['text'] for e in elems if e['type']=='text' and e['layer']=='A-TAGS']
        here=[o for o in model['openings'] if o['floor']==f]
        assert len(texts)==len(here) and sorted(texts)==sorted(tags[o['id']] for o in here)
    scheduled={r[0] for r in schedule_tables(model,reports(model,validate(model)))[0]['rows'][1:]}
    assert set(tags.values())<=scheduled and len(rows)==len(scheduled)

def test_section_cut_runs_up_the_stair_flight(model):
    x=section_cut(model);st=model['stairs'][0]
    assert st['x']<x<st['x']+st['flight_width']


def test_schedule_locations_never_cut_a_word(model):
    names={s_['name'] for s_ in model['spaces']}
    for row in schedule_tables(model,reports(model,validate(model)))[0]['rows'][1:]:
        parts=[q.strip() for q in row[5].split(',')]
        last=parts[-1].rsplit(' +',1)[0]
        assert all(q in names or ' / ' in q for q in parts[:-1]+[last]),row
