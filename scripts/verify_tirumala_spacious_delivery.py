"""Verify the current P12/P13 gallery against its archived approved baseline."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from shapely.geometry import Polygon

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from floorforge.tirumala_p11_p12 import build_p11_p12_project, _mm_to_ft_in
from floorforge.intent import fuse

OUT=ROOT/'output/tirumala-spacious-gallery'
digest=lambda b:hashlib.sha256(b).hexdigest()
results={'samples':{},'otherReferenceFilesUnchanged':0}
protected=json.loads((ROOT/'output/tirumala-icu-trials/protected-files.json').read_text())
for path,sha in protected.items():
    if any(path.startswith('examples/gallery/'+s+'/') for s in ('tirumala-2','tirumala-3')):continue
    assert digest((ROOT/path).read_bytes())==sha,path
    results['otherReferenceFilesUnchanged']+=1

for slug in ('tirumala-2','tirumala-3'):
    d=ROOT/'examples/gallery'/slug;before=OUT/'before'/slug
    read=lambda p:json.loads(p.read_text())
    old=read(before/'building.json');b=read(d/'building.json');s=read(d/'scene.json')
    spec=read(d/'specifications.json');m=read(d/'manifest.json');p=read(d/'project.floorforge.json')
    assert b['planHash']==s['planHash']==m['planHash']==spec['planHash']==fuse(p)['planHash']
    rebuilt=build_p11_p12_project(slug)
    assert p['customPlan']==rebuilt['customPlan'],'rebuild would discard current revision'
    assert b['brief']['width_mm']==12192 and b['brief']['depth_mm']==15240 and b['storeys']==2
    assert (before/'source-plan-data.json').read_bytes()==(d/'source-plan-data.json').read_bytes()
    preserved=[]
    for r in old['spaces']:
        actual=next(a for a in b['spaces'] if a['id']==r['id'])
        if r['id'] in ('g-care', 'g-living' if slug=='tirumala-2' else 'u-terrace'):continue
        assert Polygon(r['clear'],r.get('holes',[])).symmetric_difference(Polygon(actual['clear'],actual.get('holes',[]))).area<1,r['id']
        preserved.append(r['id'])
    a=old['planning']['canonicalPlan'];c=b['planning']['canonicalPlan']
    for key in ('stairs','counter','serving','lowerPorch','carEnvelope','carBody','gate','northGarden','rearAir'):
        assert a[key]==c[key],(slug,key)
    assert [f for f in a['furniture'] if f['room_id']!='g-care']==[f for f in c['furniture'] if f['room_id']!='g-care']
    with zipfile.ZipFile(d/'FloorForge-export.zip') as z:
        assert z.testzip() is None
        for name,sha in m['files'].items():
            assert digest((d/name).read_bytes())==sha,(slug,name,'manifest')
            assert digest(z.read(name))==sha,(slug,name,'zip')
        assert z.read('manifest.json')==(d/'manifest.json').read_bytes()
    care=next(r for r in b['spaces'] if r['id']=='g-care');x0,y0,x1,y1=care['bounds']
    results['samples'][slug]={'planHash':b['planHash'],'ICU':[_mm_to_ft_in(x1-x0),_mm_to_ft_in(y1-y0)],
        'ICUAreaSqFt':round(care['area_m2']/.09290304,2),'otherSpacesPreserved':preserved,
        'originalSourcePlanPreserved':True,'manifestFilesVerified':len(m['files']),'zipVerified':True,
        'galleryDisplayOption':spec['option'],'spaciousPresentation':s['presentation']['revision']}
browser=read(OUT/'browser-checks.json')
assert browser['checks'] and not browser['errors'] and all(c['pass'] for c in browser['checks'])
results['liveGalleryChecksPassed']=len(browser['checks'])
(OUT/'delivery-checks.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
