#!/usr/bin/env python3
"""Regenerate the bundled examples/<name>/ builds from examples/briefs/*.json.

Each example is an ordinary published build (preview.html, scene.json, drawings,
GLB, IFC, DXF, report and export ZIP) copied into examples/<name>/ so the studio
can open it offline. Run after changing the generator or web/viewer.js.
"""
from pathlib import Path
import argparse, json, shutil, sys, tempfile, time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from floorforge.pipeline import run  # noqa: E402
from floorforge.model import read_json  # noqa: E402

EXAMPLES = [('demo', 'demo.json'), ('compact', 'compact.json'), ('small', 'small.json')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=[name for name, _ in EXAMPLES])
    args = parser.parse_args()
    evidence = ROOT / 'evidence/examples.json'
    records = [r for r in read_json(evidence) if r['name'] != args.only] if args.only and evidence.exists() else []
    for name, brief in EXAMPLES:
        if args.only and name != args.only:
            continue
        payload = read_json(ROOT / 'examples/briefs' / brief)
        start = time.perf_counter()
        with tempfile.TemporaryDirectory() as tmp:
            result = run(payload, Path(tmp), use_cache=False)
            dest = ROOT / 'examples' / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(result['path'], dest)
        seconds = round(time.perf_counter() - start, 3)
        records.append({'name': name, 'build_id': result['id'], 'project': f'examples/briefs/{brief}', 'outputs': f'examples/{name}', 'seconds': seconds})
        print(f'{name}: {result["id"]} in {seconds}s')
    evidence.write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
