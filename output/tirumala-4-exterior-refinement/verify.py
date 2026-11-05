"""Check this exterior revision against the saved pre-change sample."""
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SAMPLE = ROOT / 'examples/gallery/tirumala-4'

def read(path):
    return json.loads(path.read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

before = read(OUT / 'before/examples/gallery/tirumala-4/building.json')
after = read(SAMPLE / 'building.json')
assert before == after, 'Building geometry or room metadata changed'
protected = read(OUT / 'protected-samples.json')
changed = [name for name, sha in protected.items() if digest(ROOT / name) != sha]
assert not changed, changed
manifest = read(SAMPLE / 'manifest.json')
mismatches = [name for name, sha in manifest['files'].items() if digest(SAMPLE / name) != sha]
assert not mismatches, mismatches
with zipfile.ZipFile(SAMPLE / 'FloorForge-export.zip') as archive:
    assert archive.testzip() is None
    for name, sha in manifest['files'].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == sha, name
    archive_count = len(archive.namelist())
browser = read(ROOT / 'output/tirumala-4-delivery/browser-checks.json')
assert all(c['pass'] for c in browser['checks']), browser
assert not browser.get('errors'), browser.get('errors')
scene = read(SAMPLE / 'scene.json')
assert scene['exteriorRefinement']['houseGeometryChanged'] is False
assert len([p for p in scene['vegetation'] if p['species'] == 'grass_ornamental' and p['scale'] == .20]) == 5
for src in re.findall(r'<img[^>]+src="([^"]+)"', (OUT / 'index.html').read_text()):
    assert (OUT / src).exists(), src
report = dict(
    verifiedAt=datetime.now(timezone.utc).isoformat(),
    entireBuildingUnchanged=before == after,
    geometryHash=read(SAMPLE / 'specifications.json')['geometryHash'],
    protectedSampleFilesUnchanged=len(protected),
    exportManifestFilesVerified=len(manifest['files']),
    exportZipEntriesVerified=archive_count,
    browserChecksPassed=len(browser['checks']),
    browserErrors=browser.get('errors', []),
    earlierTestResults={'pythonSampleAndPlanTests': 32, 'viewerAndWalkingTests': 87},
    lowNorthStripAccents=5,
    reviewImagesExist=True,
)
(OUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
