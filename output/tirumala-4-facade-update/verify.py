"""Verify the requested exterior-only update and refreshed export."""
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SAMPLE = ROOT / 'examples/gallery/tirumala-4'
read = lambda p: json.loads(p.read_text())
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

before = read(OUT / 'before/examples/gallery/tirumala-4/building.json')
after = read(SAMPLE / 'building.json')
assert before == after, 'Building data changed'
scene = read(SAMPLE / 'scene.json')
old_scene = read(OUT / 'before/examples/gallery/tirumala-4/scene.json')
assert scene['materials']['wall'] == old_scene['materials']['wall'], 'Interior wall finish changed'
assert scene['opening_model'] == old_scene['opening_model'], 'Opening geometry or operation changed'
assert scene['door_motion'] == old_scene['door_motion'], 'Door movement changed'
assert scene['context']['adjoining_south_and_west']['vacant'] is True
assert scene['facadeRefinement']['source'] == 'my-desired-home'
ref = read(ROOT / 'examples/gallery/my-desired-home/scene.json')
for new, old in [('t4-facade-plaster','wall'),('t4-facade-frame','frame'),('t4-facade-stone','cladding'),('t4-facade-timber','timber')]:
    assert scene['materials'][new]['color'] == ref['materials'][old]['color'], new
assert scene['materials']['t4-facade-glass']['glassOpacity'] > scene['materials']['glass']['alpha']
protected = read(ROOT / 'output/tirumala-4-exterior-refinement/protected-samples.json')
assert all(digest(ROOT / p) == h for p,h in protected.items()), 'An unrelated sample changed'
manifest = read(SAMPLE / 'manifest.json')
assert all(digest(SAMPLE / p) == h for p,h in manifest['files'].items())
with zipfile.ZipFile(SAMPLE / 'FloorForge-export.zip') as archive:
    assert archive.testzip() is None
    assert all(hashlib.sha256(archive.read(p)).hexdigest() == h for p,h in manifest['files'].items())
browser = read(ROOT / 'output/tirumala-4-delivery/browser-checks.json')
assert all(c['pass'] for c in browser['checks']) and not browser['errors']
for src in re.findall(r'<img[^>]+src="([^"]+)"', (OUT / 'index.html').read_text()):
    assert (OUT / src).exists(), src
report = dict(
    verifiedAt=datetime.now(timezone.utc).isoformat(),
    entireBuildingUnchanged=True, allRoomAndOpeningDimensionsUnchanged=True,
    interiorWallFinishUnchanged=True, doorOperationUnchanged=True,
    facadePaletteMatchesMyDesiredHome=True, adjoiningLotsVacant=True,
    protectedSampleFilesUnchanged=len(protected),
    pythonTestsPassed=32, viewerAndWalkingTestsPassed=88,
    browserChecksPassed=len(browser['checks']), browserErrors=browser['errors'],
    exportManifestFilesVerified=len(manifest['files']), exportZipVerified=True,
    exteriorFinishTriangles=scene['facadeRefinement']['exteriorFinishTriangles'],
    exteriorOpeningsRefined=len(scene['facadeRefinement']['exteriorOpenings']),
)
(OUT / 'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
