"""Check the delivered model, not just a freshly compiled fixture with roof access forced on."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from floorforge.model import DesignError, read_json
from floorforge.server import State

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / 'examples/demo'


def test_delivered_demo_has_roof_stairs_and_consistent_exports():
    b = read_json(DEMO / 'building.json')
    s = read_json(DEMO / 'scene.json')
    manifest = read_json(DEMO / 'manifest.json')
    assert b['storeys'] == len(b['floors']) == 2
    assert b['brief']['roof_access'] and s['roof_level'] == 2
    assert any(st['floor'] == 1 and st['to_floor'] == 2 and st['roof_access'] for st in b['stairs'])
    assert b['rooftop']['openings'][0]['floor'] == 2
    assert b['planHash'] == s['planHash'] == manifest['planHash']
    for name, digest in manifest['files'].items():
        assert hashlib.sha256((DEMO / name).read_bytes()).hexdigest() == digest, name


def publish_demo(tmp_path, monkeypatch):
    ident = read_json(DEMO / 'manifest.json')['build_id']
    shutil.copytree(DEMO, tmp_path / 'builds' / ident)
    monkeypatch.setattr('floorforge.server.run', lambda *a, **kw: {'id': ident, 'status': 'published'})
    state = State(tmp_path)
    job = state.submit({'brief': {}})
    state.pool.shutdown(wait=True)
    assert state.jobs[job]['status'] == 'done'
    return ident


def test_latest_published_house_survives_restart_and_failed_generation(tmp_path, monkeypatch):
    ident = publish_demo(tmp_path, monkeypatch)
    state = State(tmp_path)
    assert state.latest == ident
    def fail(*args, **kwargs):
        raise DesignError('INVALID_PLAN', 'Invalid draft')
    monkeypatch.setattr('floorforge.server.run', fail)
    job = state.submit({'brief': {}})
    state.pool.shutdown(wait=True)
    assert state.jobs[job]['status'] == 'error'
    restarted = State(tmp_path)
    try:
        assert restarted.latest == ident
    finally:
        restarted.pool.shutdown(wait=True)


@pytest.mark.parametrize('damage', ['missing-scene', 'changed-building', 'invalid-pointer', 'other-workspace'])
def test_latest_restore_rejects_missing_modified_or_foreign_build(tmp_path, monkeypatch, damage):
    ident = publish_demo(tmp_path, monkeypatch)
    build = tmp_path / 'builds' / ident
    if damage == 'missing-scene':
        (build / 'scene.json').unlink()
    elif damage == 'changed-building':
        (build / 'building.json').write_text('{}')
    else:
        record = read_json(tmp_path / 'latest-build.json')
        record['id' if damage == 'invalid-pointer' else 'workspace'] = '../outside'
        (tmp_path / 'latest-build.json').write_text(json.dumps(record))
    state = State(tmp_path)
    try:
        assert state.latest is None
    finally:
        state.pool.shutdown(wait=True)
