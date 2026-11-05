"""Verify delivered sample files, preserved source plans and package checksums."""
import hashlib
import json
from pathlib import Path
import zipfile
from shapely.geometry import Polygon

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'evidence/tirumala-luxury'
hash_bytes=lambda data:hashlib.sha256(data).hexdigest()
originals=json.loads((E/'protected-originals.json').read_text())
assert all(hash_bytes((ROOT/p).read_bytes())==h for p,h in originals.items()),'Original reference sample changed'
results={'originalFilesPreserved':len(originals),'samples':{}}
for slug in ('tirumala-2','tirumala-3'):
    d=ROOT/'examples/gallery'/slug
    b=json.loads((d/'building.json').read_text());scene=json.loads((d/'scene.json').read_text())
    spec=json.loads((d/'specifications.json').read_text());manifest=json.loads((d/'manifest.json').read_text())
    src=json.loads((d/'source-plan-data.json').read_text())['plans'][0]
    assert b['planHash']==scene['planHash']==spec['planHash']==manifest['planHash']
    assert b['storeys']==scene['storeys']==2
    assert b['brief']['width_mm']==12192 and b['brief']['depth_mm']==15240
    unchanged=[]
    for room in src['rooms']:
        actual=next(r for r in b['spaces'] if r['id']==room['id'])
        old=room['regions'][0]
        assert Polygon(old['outer'],old.get('holes',[])).symmetric_difference(Polygon(actual['clear'],actual.get('holes',[]))).area<1,room['id']
        unchanged.append(room['id'])
    for key in ('wallRects','counter','serving','furniture','openings','gate'):
        assert b['planning']['canonicalPlan'][key]==src[key],key
    assert all(hash_bytes((d/p).read_bytes())==h for p,h in manifest['files'].items()),'Stale manifest'
    with zipfile.ZipFile(d/'FloorForge-export.zip') as z:
        assert z.testzip() is None
        assert all(hash_bytes(z.read(p))==h for p,h in manifest['files'].items()),'Stale ZIP'
        assert z.read('manifest.json')==(d/'manifest.json').read_bytes()
    results['samples'][slug]={'planHash':b['planHash'],'groundRoomsUnchanged':unchanged,
      'sourceVersion':src['version'],'manifestFilesVerified':len(manifest['files']),
      'zipVerified':True,'upperAreasSqFt':{r['id']:round(r['area_m2']/.09290304,2) for r in b['spaces'] if r['floor']==1}}
(E/'delivery-verification.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
