"""Check the original sample/assets/planning inventory without regenerating it."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'evidence/custom-journey/baseline.json'


def check():
    baseline = json.loads(BASELINE.read_text())
    changed, missing = [], []
    current = {}
    for name, digest in baseline['files'].items():
        path = ROOT / name
        if not path.is_file():
            missing.append(name)
            continue
        current[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if current[name] != digest:changed.append(name)
    result = {'baselineCommit': baseline['commit'], 'checked': len(baseline['files']),
              'unchanged': len(current) - len(changed), 'changed': changed, 'missing': missing,
              'passed': not changed and not missing, 'files': current}
    (BASELINE.parent / 'preservation-result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}))
    archive_path = BASELINE.parent / 'archived-evidence-preservation.json'
    archived = json.loads(archive_path.read_text())
    changed = [name for name, record in archived['files'].items()
               if not (ROOT / name).is_file()
               or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != record['sha256']]
    archived.update(changed=changed, passed=not changed)
    archive_path.write_text(json.dumps(archived, indent=2) + '\n')
    print(json.dumps({k: v for k, v in archived.items() if k != 'files'}))
    return result['passed'] and archived['passed']


if __name__ == '__main__':
    raise SystemExit(0 if check() else 1)
