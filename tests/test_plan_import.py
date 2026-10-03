"""DXF import keeps authored dimensions and shares the real generation pipeline."""
import io
import json
from pathlib import Path

import ezdxf
import pytest

from floorforge.plan_import import import_dxf, MAX_BYTES
from floorforge.model import DesignError
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.pipeline import run
from test_security_ai import http_server, request

TEMPLATE = Path(__file__).resolve().parents[1] / 'examples/import/ground-floor.dxf'


def drawing(edit=None):
    doc = ezdxf.readfile(TEMPLATE)
    if edit:
        edit(doc)
    stream = io.StringIO(); doc.write(stream)
    return stream.getvalue()


def test_import_single_file_generates_matching_3d_and_exports(tmp_path):
    imported = import_dxf(drawing(), 'My ground floor.dxf')
    assert imported['valid'] and imported['roomCount'] == 4 and imported['openingCount'] == 8
    project = imported['project']; intent = fuse(project); building = generate_layout(intent)
    living = next(r for r in building['spaces'] if r['kind'] == 'living')
    assert living['clear'] == [[150,150],[4150,150],[4150,4150],[150,4150]]
    assert sum(o['kind']=='entry' for o in building['openings']) == 1
    result = run(project,tmp_path,use_cache=False); output = Path(result['path'])
    for name in ('scene.json','building.json','report.json','manifest.json'):
        assert json.loads((output/name).read_text())['planHash'] == intent['planHash']
    for name in ('model.glb','model.ifc','drawings.pdf','floorplans.dxf','preview.html'):
        assert (output/name).stat().st_size > 100
    assert fuse(json.loads((output/'project.floorforge.json').read_text()))['planHash'] == intent['planHash']


@pytest.mark.parametrize('unit,factor',[(4,1),(6,1000),(1,25.4),(2,304.8)])
def test_units_and_translated_origin_preserve_exact_geometry(unit,factor):
    def change(doc):
        doc.units = unit
        for e in doc.modelspace():
            e.translate(12000,15000,0)
            e.scale_uniform(1/factor)
    got = import_dxf(drawing(change))['project']['customPlan']
    expected = import_dxf(drawing())['project']['customPlan']
    assert got == expected


@pytest.mark.parametrize('case', ['unitless','no-plot','open-ring','curve','diagonal','z','block','unknown-layer','room-type','missing-rooms','paper-space','bad-opening','overlap'])
def test_rejects_ambiguous_drawings(case):
    def change(d):
        m=d.modelspace(); room=next(e for e in m if e.dxf.layer=='FF_ROOM_LIVING')
        if case=='unitless':d.units=0
        elif case=='no-plot':m.delete_entity(next(e for e in m if e.dxf.layer=='FF_PLOT'))
        elif case=='open-ring':room.closed=False
        elif case=='curve':room.set_points([(150,150,0,0,1),(4150,150),(4150,4150),(150,4150)])
        elif case=='diagonal':room.rotate_z(.1)
        elif case=='z':room.dxf.elevation=1
        elif case=='block':d.blocks.new('WALL');m.add_blockref('WALL',(0,0),dxfattribs={'layer':'FF_ROOM_LIVING'})
        elif case=='unknown-layer':m.add_line((0,0),(1,1),dxfattribs={'layer':'FF_MYSTERY'})
        elif case=='room-type':room.dxf.layer='FF_ROOM_STAIR'
        elif case=='missing-rooms':
            for e in list(m):
                if e.dxf.layer.startswith('FF_ROOM_'):m.delete_entity(e)
        elif case=='paper-space':d.layout().add_line((0,0),(1,1),dxfattribs={'layer':'FF_DOOR'})
        elif case=='bad-opening':next(e for e in m if e.dxf.layer=='FF_ENTRY').translate(0,25,0)
        elif case=='overlap':next(e for e in m if e.dxf.layer=='FF_ROOM_BEDROOM').translate(-300,0,0)
    with pytest.raises(DesignError):import_dxf(drawing(change))


@pytest.mark.parametrize('text,name',[('not DXF','x.dxf'),('anything','x.pdf'),('AutoCAD Binary DXF\x00','x.dxf'),('x'*(MAX_BYTES+1),'x.dxf')])
def test_bad_file_has_actionable_error(text,name):
    with pytest.raises(DesignError) as error:import_dxf(text,name)
    assert error.value.code=='DXF_IMPORT'


def test_missing_access_returns_editable_draft_instead_of_inventing_doors():
    def change(d):
        m=d.modelspace()
        for e in list(m):
            if e.dxf.layer in ('FF_ENTRY','FF_DOOR'):m.delete_entity(e)
    result=import_dxf(drawing(change))
    assert not result['valid']
    assert {'NO_ENTRY','UNREACHABLE'} <= {e['code'] for e in result['issue']['details']['errors']}
    assert all(o['kind']=='window' for o in result['project']['customPlan']['floors'][0]['openings'])


def test_ignored_annotations_are_disclosed():
    result=import_dxf(drawing(lambda d:d.modelspace().add_text('Ignore this annotation')))
    assert result['valid'] and any('1 entities' in n for n in result['notes'])


def test_live_import_api_protects_session_and_serves_example(http_server):
    token=json.loads(request(http_server,'/api/session')[1])['token']; headers={'X-FloorForge-Token':token}
    status,data=request(http_server,'/api/plan/import-template')
    assert status==200 and import_dxf(data.decode())['valid']
    body={'filename':'example.dxf','text':data.decode()}
    assert request(http_server,'/api/plan/import-dxf',body)[0]==403
    status,data=request(http_server,'/api/plan/import-dxf',body,headers)
    assert status==200 and json.loads(data)['valid']
    assert request(http_server,'/api/plan/import-dxf',{'text':'broken'},headers)[0]==400
