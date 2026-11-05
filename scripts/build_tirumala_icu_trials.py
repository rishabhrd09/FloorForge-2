#!/usr/bin/env python3
"""Build separate P12 furniture/width trials without replacing approved samples."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shapely.geometry import Polygon, box
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.pipeline import run, deterministic_zip
from floorforge.tirumala_p11_p12 import _mm_to_ft_in, _browser_numbers, build_p11_p12_project
from floorforge.tirumala_luxury import upper_plan

OUT = ROOT / 'output/tirumala-icu-trials'
SOURCE = ROOT / 'examples/gallery/tirumala-2'
DELTA = 457.2


from floorforge.tirumala_icu_revision import trial_project


def metrics(b):
    plan = b['planning']['canonicalPlan']
    room = next(r for r in b['spaces'] if r['id'] == 'g-care')
    bed = next(f for f in plan['furniture'] if f['id'] == 'g-care/reclining-bed')
    door = next(o for o in b['openings'] if o['id'] == 'living-veranda')
    width, depth = room['bounds'][2] - room['bounds'][0], room['bounds'][3] - room['bounds'][1]
    south, north = bed['bounds'][0] - room['bounds'][0], room['bounds'][2] - bed['bounds'][2]
    table = next(f for f in plan['furniture'] if f['id'] == 'g-care/equipment-table')
    return {'icuWidthMm': width, 'icuDepthMm': depth, 'areaSqFt': Polygon(room['clear']).area / 92903.04,
            'icuWidthFt': _mm_to_ft_in(width), 'icuDepthFt': _mm_to_ft_in(depth),
            'headGapMm': south, 'footGapMm': north,
            'headGapFt': _mm_to_ft_in(south), 'footGapFt': _mm_to_ft_in(north),
            'livingStripMm': room['bounds'][0] - 150 - 5302.4,
            'livingStripFt': _mm_to_ft_in(room['bounds'][0] - 150 - 5302.4),
            'verandaDoorApertureMm': door['width'], 'verandaDoorClearMm': door['width'] - 110,
            'verandaDoorClearFt': _mm_to_ft_in(door['width'] - 110),
            'tableBounds': table['bounds'], 'bedBounds': bed['bounds']}


def check_geometry(base, b, extend):
    old = base['planning']['canonicalPlan']; new = b['planning']['canonicalPlan']
    for key in ('counter', 'serving', 'stairs', 'lowerPorch', 'raisedPassage', 'raisedForecourt',
                'carBody', 'carEnvelope', 'gate', 'northGarden', 'rearAir'):
        assert old[key] == new[key], key
    for a, c in zip(old['rooms'], new['rooms']):
        if a['id'] != 'g-care': assert a == c, a['id']
    before = {r['id']: r for r in base['spaces']}; after = {r['id']: r for r in b['spaces']}
    assert Polygon(before['g-kitchen']['clear']).symmetric_difference(Polygon(after['g-kitchen']['clear'])).area < 1
    assert before['g-kitchen']['bounds'] == after['g-kitchen']['bounds']
    # The first floor may acquire equivalent collinear polygon vertices; compare shapes.
    for key in (r['id'] for r in base['spaces'] if r['floor'] == 1):
        def shape(r):
            from shapely.ops import unary_union
            return unary_union([Polygon(q['polygon'], q['holes']) for q in r['regions']])
        assert shape(before[key]).symmetric_difference(shape(after[key])).area < 1, key
    care = Polygon(after['g-care']['clear'])
    living = Polygon(after['g-living']['clear'], after['g-living'].get('holes', []))
    assert care.intersection(living).area < 1
    assert abs(care.area / 92903.04 - (158.627947589 if extend else 136.249994833)) < .001
    for f in new['furniture']:
        if f['room_id'] == 'g-care': assert Polygon(f['polygon']).difference(care).area < 1
    for o in new['openings']:
        if o['id'] not in ('icu-glass-living', 'living-veranda'):
            assert o == next(q for q in old['openings'] if q['id'] == o['id']), o['id']


def preview_controls(dest):
    path = dest / 'preview.html'
    text = path.read_text()
    if 'id="trialICU"' not in text:
        text = text.replace('<div class="tools">', '<div class="tools"><select id="trialRoom" aria-label="Jump to an interior"><option value="interior_icu_veranda_garden">ICU</option><option value="interior_kitchen_living_dining">Kitchen / living</option><option value="interior_veranda_living">Veranda</option><option value="interior_master">Master bedroom</option><option value="interior_drawing">Drawing room</option><option value="upper_gallery">Upper gallery</option><option value="upper_master">Upper master</option><option value="upper_office">Office</option><option value="upper_terrace">Terrace</option></select><button id="trialICU">Go to room</button><button id="trialOpen">Open connecting doors</button>')
        text = text.replace('</html>', '''<script>
document.getElementById('trialOpen').onclick=()=>{const v=window.__ff.viewer;for(const i of v.openings.items)if(i.id.startsWith('icu-')||i.id.startsWith('living-veranda'))i.goal=1;};
document.getElementById('trialICU').onclick=()=>{const v=window.__ff.viewer;v.setNamedCamera(document.getElementById('trialRoom').value);document.getElementById('view').focus();};
</script></html>''')
        path.write_text(text)
    manifest = json.loads((dest / 'manifest.json').read_text())
    manifest['files']['preview.html'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (dest / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    files = {name: (dest / name).read_bytes() for name in manifest['files']}
    files['manifest.json'] = (dest / 'manifest.json').read_bytes()
    (dest / 'FloorForge-export.zip').write_bytes(deterministic_zip(files))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    protected = {}
    for slug in ('tirumala-2', 'tirumala-3', 'my-desired-home', 'bungalow', 'tirumala'):
        for p in (ROOT / 'examples/gallery' / slug).rglob('*'):
            if p.is_file(): protected[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    # Trials always start from the archived source coordinates, even after the
    # selected extension is promoted to the main gallery sample.
    base_p = build_p11_p12_project('tirumala-2', apply_revision=False)
    base_b = generate_layout(fuse(base_p))
    result = {'baseline': metrics(base_b), 'options': []}
    (OUT / 'baseline-plan.json').write_text(json.dumps(base_b['planning']['canonicalPlan']))
    for extend in (False, True):
        key = 'south-extension' if extend else 'compact-only'
        p = trial_project(base_p, extend)
        b = generate_layout(fuse(p))
        check_geometry(base_b, b, extend)
        dest = OUT / key
        with tempfile.TemporaryDirectory(prefix='tirumala-icu-trial-') as tmp:
            built = run(p, Path(tmp), use_cache=False)
            shutil.copytree(built['path'], dest, dirs_exist_ok=True)
        preview_controls(dest)
        result['options'].append({'id': key, 'title': p['brief']['title'], 'metrics': metrics(b)})
        print(key, json.dumps(metrics(b)), flush=True)
    for path, digest in protected.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    result['protectedFilesUnchanged'] = len(protected)
    (OUT / 'comparison-data.json').write_text(json.dumps(result, indent=2) + '\n')
    (OUT / 'protected-files.json').write_text(json.dumps(protected, indent=2) + '\n')
    print('Protected originals unchanged:', len(protected), flush=True)


if __name__ == '__main__': main()
