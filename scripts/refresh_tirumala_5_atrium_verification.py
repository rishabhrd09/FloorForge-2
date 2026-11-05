#!/usr/bin/env python3
"""Refresh Tirumala 5 atrium delivery evidence from completed current checks.

Run preservation-only immediately after a stable build. Run the full refresh
after the runtime/capture reports and hash-bearing Cycles manifests are final.
This script does not run tests, rebuild geometry, or fabricate pass counts or
render provenance. Baseline files are explicit inputs; preserve them with the
review evidence when moving this workflow to another machine.
"""
import argparse
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stamp(path):
    return {'path': str(path.resolve()), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def room_shape(room):
    rr = room.get('regions') or [{'polygon': room.get('clear') or room['polygon'], 'holes': room.get('holes', [])}]
    return unary_union([Polygon(r.get('polygon', r.get('outer')), r.get('holes', [])) for r in rr])


def ground_preservation(old, building):
    """Allow one precisely specified window change, not arbitrary ground edits.

    Wall fragment IDs are regenerated after subtraction, so compare their real
    geometry rather than expecting fragment names to remain identical.
    """
    records = lambda model, key: {r['id']: r for r in model[key] if r.get('floor') == 0}
    old_openings, new_openings = records(old, 'openings'), records(building, 'openings')
    expected_openings = deepcopy(old_openings)
    expected_openings['drawing-north'].update(a=[11507.4,8600], b=[11507.4,11000], width=2400)
    cut = box(11432.4,8600,11582.4,11000)
    walls = lambda model: unary_union([Polygon(r['polygon']) for r in model['walls']
                                      if r.get('floor') == 0 and not r.get('hostOnly')])
    wall_difference = walls(old).difference(cut).symmetric_difference(walls(building)).area
    old_hosts = {i:r for i,r in records(old,'walls').items() if r.get('hostOnly')}
    new_hosts = {i:r for i,r in records(building,'walls').items() if r.get('hostOnly')}
    expected_hosts = deepcopy(old_hosts)
    host = expected_hosts['w-host-drawing-north']
    host.update(a=[11507.4,8600], start=[11507.4,8600], b=[11507.4,11000], end=[11507.4,11000],
                polygon=[[11582.4,8600],[11582.4,11000],[11432.4,11000],[11432.4,8600]])
    old_plan, new_plan = old['planning']['canonicalPlan'], building['planning']['canonicalPlan']
    expected_plan = deepcopy(old_plan)
    for op in expected_plan['openings']:
        if op['id']=='drawing-north':
            op.update(a=[11507.4,8600],b=[11507.4,11000],sill=450,height=2400,
                      window_style='picture-with-sliding-vents')
    expected_plan['groundRevision']['drawingNorthWindowMm'] = {
        'a':[11507.4,8600],'b':[11507.4,11000],'sill':450,'height':2400}
    expected_wall = unary_union([box(*r) for r in old_plan['wallRects']]).difference(cut)
    actual_wall = unary_union([box(*r) for r in new_plan['wallRects']])
    canonical_wall_difference = expected_wall.symmetric_difference(actual_wall).area
    # Wall rectangle ordering/fragment IDs have no geometric meaning.
    expected_plan.pop('wallRects'); comparable_new = deepcopy(new_plan); comparable_new.pop('wallRects')
    checks = {
        'spacesUnchanged': records(old,'spaces') == records(building,'spaces'),
        'stairsUnchanged': records(old,'stairs') == records(building,'stairs'),
        'openingsExactlyApprovedWindowChange': new_openings == expected_openings,
        'wallHostsExactlyApprovedWindowChange': new_hosts == expected_hosts,
        'masonryExactlyApprovedCutout': wall_difference <= 1,
        'canonicalMasonryExactlyApprovedCutout': canonical_wall_difference <= 1,
        'canonicalOtherFieldsUnchanged': comparable_new == expected_plan,
        'wallHeightsUnchanged': {r['height'] for r in records(old,'walls').values()} ==
                                {r['height'] for r in records(building,'walls').values()},
    }
    return {'checks':checks, 'passed':all(checks.values()),
            'approvedOpening':'drawing-north',
            'approvedOpeningMm':{'a':[11507.4,8600],'b':[11507.4,11000],'width':2400,'height':2400,'sill':450},
            'approvedMasonryCutoutMm':list(cut.bounds),
            'compiledWallDifferenceBeyondApprovedMm2':wall_difference,
            'canonicalWallDifferenceBeyondApprovedMm2':canonical_wall_difference}


def preservation(args, root, building, meta):
    old = read(args.baseline)
    before = {r['id']: r for r in old['spaces']}
    after = {r['id']: r for r in building['spaces']}
    changed, unchanged = [], []
    authorized = {'s2-indoor-landing', 's2-terrace'}
    allowed_spatial_fields = {'clear', 'regions', 'polygon', 'areaSqFt', 'area_m2', 'bounds', 'holes'}
    metadata_changes = []
    for ident in sorted(before.keys() | after.keys()):
        if ident not in before or ident not in after:
            changed.append({'room': ident, 'status': 'added' if ident in after else 'removed', 'authorized': False})
            continue
        fields = [k for k in before[ident].keys() | after[ident].keys()
                  if before[ident].get(k) != after[ident].get(k)
                  and not (ident in authorized and k in allowed_spatial_fields)]
        if fields:
            metadata_changes.append({'room': ident, 'unauthorizedFields': sorted(fields)})
        a, b = room_shape(before[ident]), room_shape(after[ident])
        difference = a.symmetric_difference(b).area
        row = {'room': ident, 'floor': after[ident]['floor'], 'differenceMm2': difference,
               'beforeSqFt': a.area / 92903.04, 'afterSqFt': b.area / 92903.04,
               'areaChangeSqFt': (b.area - a.area) / 92903.04}
        if difference > 1:
            row['authorized'] = ident in authorized
            changed.append(row)
        else:
            unchanged.append(row)
    ground = ground_preservation(old, building)
    rooms = dict(meta, baseline=stamp(args.baseline), plotUnchanged=old['plot'] == building['plot'],
                 allowedRoomPolygonChanges=sorted(authorized),
                 otherRoomFieldsUnchanged=not metadata_changes, unauthorizedRoomFields=metadata_changes,
                 allStairRecordsUnchanged=old['stairs'] == building['stairs'],
                 storeysUnchanged=old.get('storeys') == building.get('storeys'),
                 ground=ground, roomDifferences=changed, unchangedRooms=unchanged,
                 passed=old['plot'] == building['plot'] and ground['passed'] and not metadata_changes
                        and old['stairs'] == building['stairs'] and old.get('storeys') == building.get('storeys')
                        and all(r['authorized'] for r in changed))
    baseline = read(args.other_baseline)
    changes, missing, additions = [], [], []
    checked = 0
    for sample, files in baseline.items():
        directory = root / 'examples/gallery' / sample
        for rel, digest in files.items():
            checked += 1
            path = directory / rel
            if not path.is_file():
                missing.append(str(path.relative_to(root)))
            elif sha(path) != digest:
                changes.append(str(path.relative_to(root)))
        additions += [str(p.relative_to(root)) for p in directory.rglob('*')
                      if p.is_file() and str(p.relative_to(directory)) not in files]
    sources = dict(meta, baseline=stamp(args.other_baseline), filesChecked=checked,
                   changed=changes, missing=missing, added=additions,
                   passed=not (changes or missing or additions))
    return rooms, sources


def report_hashes(value):
    found = set()
    if isinstance(value, dict):
        if isinstance(value.get('planHash'), str):
            found.add(value['planHash'])
        for child in value.values():
            found.update(report_hashes(child))
    elif isinstance(value, list):
        for child in value:
            found.update(report_hashes(child))
    return found


def fresh_report(path, expected, *input_paths):
    data = read(path)
    hashes = report_hashes(data)
    if hashes != {expected}:
        raise RuntimeError(f'{path}: current plan hash required; found {sorted(hashes)}')
    if path.stat().st_mtime < max(p.stat().st_mtime for p in input_paths):
        raise RuntimeError(f'{path}: report predates stable model inputs; rerun it')
    checks = data.get('checks', [])
    failures = [r for r in checks if not r.get('pass')]
    return data, {'source': stamp(path), 'checkCount': len(checks), 'failures': failures,
                  'errors': data.get('errors', []),
                  'passed': bool(checks) and not failures and not data.get('errors') and not data.get('failure')}


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for field in ('src', 'href'):
            if field in a:
                self.refs.append((tag, a[field]))


def delivery_assets(path, meta):
    parser = References()
    parser.feed(path.read_text())
    local, external = [], []
    for tag, value in parser.refs:
        url = urlparse(value)
        if url.scheme in ('http', 'https'):
            external.append(value)
            continue
        if url.scheme and url.scheme != 'file':
            continue
        if not url.path:
            continue
        target = Path(unquote(url.path)) if url.scheme == 'file' else path.parent / unquote(url.path)
        target = target.resolve()
        row = {'tag': tag, 'reference': value, 'path': str(target), 'exists': target.is_file()}
        if row['exists']:
            row['sha256'] = sha(target)
            if tag == 'img':
                from PIL import Image
                try:
                    with Image.open(target) as image:
                        row['dimensions'] = list(image.size)
                        image.verify()
                    row['imageDecodes'] = True
                except Exception as error:
                    row['imageDecodes'] = False
                    row['error'] = str(error)
        local.append(row)
    return dict(meta, html=stamp(path), audit='Static local references and image decoding only',
                localReferences=local, missingFiles=[r['path'] for r in local if not r['exists']],
                externalLinksNotFetched=sorted(set(external)),
                desktopOverflow=None, mobileOverflow=None,
                responsiveLayoutStatus='Not evaluated by this static audit; do not infer a browser QA pass',
                passed=all(r['exists'] and r.get('imageDecodes', True) for r in local))


def cycles_audit(root, directory, meta, qa, current_glb):
    """Verify render-time inputs without changing or replacing those inputs."""
    entries = []
    for path in sorted(directory.rglob('render-manifest.json')):
        for row in read(path):
            problems = []
            if row.get('planHash') != meta['planHash']:
                problems.append('Render record does not bind to the current planHash')
            inputs = {}
            for key in ('scene', 'glb', 'image'):
                p = Path(row.get(key, ''))
                if not p.is_absolute():
                    p = root / p
                p = p.resolve()
                digest = row.get(key + 'Sha256')
                if not p.is_file():
                    problems.append(f'{key}: file missing')
                    continue
                actual = sha(p)
                inputs[key] = {'path': str(p), 'recordedSha256': digest, 'actualSha256': actual}
                if not digest or digest != actual:
                    problems.append(f'{key}: generation-time hash absent or mismatched')
                if key == 'scene' and read(p).get('planHash') != meta['planHash']:
                    problems.append('Render scene file belongs to another plan')
                if key == 'scene' and actual != meta['sceneSha256']:
                    problems.append('Render scene differs from the current built scene')
                if key == 'glb' and actual != current_glb['sha256']:
                    problems.append('Render GLB differs from the current delivered presentation GLB')
            entries.append({'camera': row.get('camera'), 'manifest': stamp(path),
                            'inputs': inputs, 'verified': not problems, 'problems': problems})
    required = sorted({r['path'] for r in qa['localReferences']
                       if r['path'].endswith('.png') and Path(r['path']).is_relative_to(directory.resolve())})
    references = []
    for image in required:
        matches = [e for e in entries if e['inputs'].get('image', {}).get('path') == image]
        references.append({'image': image, 'verified': any(e['verified'] for e in matches),
                           'matchingManifestCount': len(matches)})
    return dict(meta, directory=str(directory.resolve()), currentPresentationGlb=current_glb,
                renders=entries, deliveryImages=references,
                verified=bool(entries) and all(e['verified'] for e in entries)
                         and all(e['verified'] for e in references),
                method='Checks generation-time manifest hashes against actual files; never relabels old renders as current')


def responsive_audit(path, expected, html):
    data = read(path)
    if (report_hashes(data) != {expected} or path.stat().st_mtime < html.stat().st_mtime
            or data.get('htmlSha256') != sha(html) or not data.get('inputsUnchanged')):
        raise RuntimeError('Responsive report must describe the current plan and final HTML')
    rows = data.get('results', [])
    passed = bool(rows) and data.get('passed') and all(r.get('pass') and not r.get('errors')
                and r.get('detail', {}).get('scrollWidth') <= r.get('detail', {}).get('width', 0)
                and bool(r.get('detail', {}).get('images'))
                and all(i.get('loaded') for i in r['detail']['images']) for r in rows)
    return {'source': stamp(path), 'results': rows, 'passed': bool(passed)}


def junit(path):
    doc = ET.parse(path).getroot()
    suites = [s for s in doc.iter('testsuite') if not list(s.iter('testsuite'))[1:]]
    counts = {k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
    return {'source': stamp(path), **counts, 'passed': counts['tests'] > 0 and counts['failures'] == counts['errors'] == 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path.cwd())
    ap.add_argument('--baseline', type=Path, default=Path('evidence/tirumala-5-atrium/baselines/pre-atrium-building.json'))
    ap.add_argument('--other-baseline', type=Path, default=Path('evidence/tirumala-5-atrium/baselines/other-samples-sha256.json'))
    ap.add_argument('--runtime', type=Path, default=Path('evidence/tirumala-5-atrium/runtime-acceptance.json'))
    ap.add_argument('--capture', type=Path, default=Path('output/tirumala-5-delivery/browser-checks.json'))
    ap.add_argument('--cycles-dir', type=Path, default=Path('output/tirumala-5-delivery/cycles-atrium'))
    ap.add_argument('--glb', type=Path, default=Path('output/tirumala-5-delivery/tirumala-5-presentation.glb'))
    ap.add_argument('--python-junit', type=Path)
    ap.add_argument('--python-report', type=Path, help='Observed test result JSON with planHash, command, exitCode, and passed count')
    ap.add_argument('--preservation-only', action='store_true')
    args = ap.parse_args()
    root = args.root.resolve()
    args.baseline = root / args.baseline
    args.other_baseline = root / args.other_baseline
    sample = root / 'examples/gallery/tirumala-5'
    delivery = root / 'output/tirumala-5-delivery'
    verification = sample / 'verification'
    building_path = sample / 'building.json'
    scene_path = sample / 'scene.json'
    building, scene = read(building_path), read(scene_path)
    if scene.get('planHash') != building['planHash']:
        raise RuntimeError('Building and scene hashes differ; finish the build first')
    meta = {'project': 'Tirumala 5', 'revision': building['planning']['g2Revision'],
            'planHash': building['planHash'], 'buildingSha256': sha(building_path),
            'sceneSha256': sha(scene_path), 'verificationScript': stamp(Path(__file__)),
            'generatedAt': datetime.now(timezone.utc).isoformat()}
    rooms, sources = preservation(args, root, building, meta)
    if args.preservation_only:
        write(verification / 'room-preservation.json', rooms)
        write(verification / 'source-preservation.json', sources)
        print(json.dumps({'preservationPassed': rooms['passed'], 'otherSamplesPassed': sources['passed'],
                          'filesChecked': sources['filesChecked'], 'roomChanges': rooms['roomDifferences']}, indent=2))
        return 0 if rooms['passed'] and sources['passed'] else 1
    runtime_path = root / args.runtime
    capture_path = root / args.capture
    runtime, walk_summary = fresh_report(runtime_path, meta['planHash'], building_path, scene_path)
    capture, capture_summary = fresh_report(capture_path, meta['planHash'], building_path, scene_path)
    if runtime.get('mode') != 'full gate-to-roof round trip':
        raise RuntimeError('A complete ground-to-roof-to-ground runtime report is required')
    routes = runtime.get('routes', [])
    continuous = bool(routes) and runtime.get('passed') and all(r.get('pass') for r in routes) and runtime.get('initialSpawns') == 1 and runtime.get('laterTeleports') == 0
    route_report = dict(meta, source=stamp(runtime_path), segments=routes, passed=bool(continuous),
                        initialSpawns=runtime.get('initialSpawns'), laterTeleports=runtime.get('laterTeleports'),
                        checks=runtime.get('checks', []), failure=runtime.get('failure'))
    qa = delivery_assets(delivery / 'index.html', meta)
    responsive = responsive_audit(delivery / 'responsive-qa.json', meta['planHash'], delivery / 'index.html')
    qa.update(responsive=responsive, responsiveLayoutStatus='Verified by the recorded browser checks',
              desktopOverflow=any(r['detail']['scrollWidth'] > r['detail']['width'] for r in responsive['results'] if r['width'] >= 768),
              mobileOverflow=any(r['detail']['scrollWidth'] > r['detail']['width'] for r in responsive['results'] if r['width'] < 768),
              passed=qa['passed'] and responsive['passed'])
    # Only read render-time inputs. Copying a newer scene over a rendered input
    # would invalidate provenance and cannot establish that a render is fresh.
    glb_path = root / args.glb
    if glb_path.stat().st_mtime < max(building_path.stat().st_mtime, scene_path.stat().st_mtime):
        raise RuntimeError('Presentation GLB predates current model inputs; export the final scene before rendering')
    cycles_dir = root / args.cycles_dir
    cycles = cycles_audit(root, cycles_dir, meta, qa, stamp(glb_path))
    if args.python_junit and (root / args.python_junit).stat().st_mtime < max(building_path.stat().st_mtime, scene_path.stat().st_mtime):
        raise RuntimeError('JUnit report predates the current stable model inputs; rerun tests')
    tests = junit(root / args.python_junit) if args.python_junit else {'status': 'Not supplied; no previous counts carried forward'}
    if args.python_report:
        test_path = root / args.python_report
        observed = read(test_path)
        if observed.get('planHash') != meta['planHash'] or test_path.stat().st_mtime < building_path.stat().st_mtime:
            raise RuntimeError('Observed test report is not bound to the current build')
        saved_test_path = verification / 'python-tests.json'
        write(saved_test_path, observed)
        tests = {'source': stamp(saved_test_path), 'observedResult': observed,
                 'passed': observed.get('exitCode') == 0 and isinstance(observed.get('passed'), int) and observed['passed'] > 0}
    summary = dict(meta, preservation=rooms['passed'], otherSamples=sources['passed'],
                   continuousWalkPassed=bool(continuous), walkSegments=len(routes),
                   runtime=walk_summary, browserCapture=capture_summary, pythonTests=tests,
                   responsiveBrowser=responsive,
                   deliveryAssetsPassed=qa['passed'], cyclesVerified=cycles['verified'],
                   architecturalModelOnly=True, structuralDesignCertified=False,
                   exportChecks=read(sample / 'export-checks.json'),
                   passed=rooms['passed'] and sources['passed'] and continuous and walk_summary['passed'] and capture_summary['passed'] and qa['passed'] and cycles['verified'] and tests.get('passed', False))
    # Never retain earlier pass counts under these compatibility filenames.
    for name in ('browser-checks.json', 'render-checks.json', 'browser-checks-all-views.json'):
        write(verification / name, dict(capture, **meta, evidenceSource=stamp(capture_path),
                                       scope='Exactly the checks recorded in the current capture report; not additional checks'))
    for name, data in [('room-preservation.json', rooms), ('source-preservation.json', sources),
                       ('runtime-acceptance.json', runtime), ('complete-stair-route.json', route_report),
                       ('final-summary.json', summary)]:
        write(verification / name, data)
    write(delivery / 'complete-stair-route.json', route_report)
    write(delivery / 'delivery-qa.json', qa)
    write(cycles_dir / 'geometry-provenance.json', cycles)
    write(root / 'evidence/tirumala-5-revision/runtime-acceptance.json',
          dict(runtime, evidenceSource=stamp(runtime_path),
               scope='Compatibility copy of the final continuous acceptance report; earlier debug result superseded'))
    print(json.dumps({'planHash': meta['planHash'], 'passed': bool(summary['passed']),
                      'walkSegments': len(routes), 'cyclesVerified': cycles['verified']}, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
