"""Publish reproducible approval/export evidence without touching any sample."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from floorforge.journey_service import JourneyService
from floorforge.model import sha
from floorforge.pipeline import run


def main():
    destination = ROOT / 'evidence/custom-journey/artifacts'
    destination.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='myverandah-verified-'))
    project = json.loads((ROOT / 'examples/custom/g2-terrace.floorforge.json').read_text())
    project['brief']['title'] = 'MyVerandah approved three-floor study'
    project['designJourney'] = {'schema': 'myverandah.journey/1', 'projectId': 'verification-study',
                                'enabledInputs': ['plot', 'dxf'], 'answers': {},
                                'appearance': {'preset': 'warm-natural', 'components': {
                                    'kitchen': 'timber', 'furniture': 'linen', 'facade': 'warm-plaster'}}}
    service = JourneyService(output)
    start = time.perf_counter();prepared = service.prepare(project);prepare_time = time.perf_counter() - start
    if not prepared['valid']:raise RuntimeError(prepared['questions'])
    journey = project['designJourney'];journey['geometryHash'] = prepared['geometryHash']
    journey['preparationId'] = prepared['preparationId']
    journey['approvals'] = {f['id']: service.approve({'preparationId': prepared['preparationId'],
        'floorId': f['id'], 'geometryHash': f['geometryHash']})['approval'] for f in prepared['floors']}
    journey['confirmation'] = service.confirm({'preparationId': prepared['preparationId'],
        'geometryHash': prepared['geometryHash'], 'approvals': journey['approvals']})['confirmation']
    start = time.perf_counter();build = run(project, output);generation_time = time.perf_counter() - start
    source = Path(build['path'])
    for name in ('drawings.pdf', 'floorplans.dxf', 'model.glb', 'canonical.json', 'scene.json',
                 'project.floorforge.json', 'geometry-approval.json', 'manifest.json', 'FloorForge-export.zip'):
        shutil.copyfile(source / name, destination / name)
    for i, floor in enumerate(prepared['floors']):
        (destination / f'approved-floor-{i+1}.svg').write_text(floor['svg'])
    canonical = json.loads((source / 'canonical.json').read_text())
    assert sha(canonical) == prepared['geometryHash']
    assert len(canonical['floors']) == len(project['customPlan']['floors']) == 3
    evidence = {'valid': True, 'floorCount': 3, 'geometryHash': prepared['geometryHash'],
                'appearance': prepared['appearance'], 'preparationSeconds': round(prepare_time, 4),
                'generationSeconds': round(generation_time, 4), 'output': str(output), 'buildId': build['id'],
                'note': 'Local timings for this fixture, not a production capacity guarantee. Certificate key stays outside artifacts.'}
    if '--render' in sys.argv:
        from floorforge.journey_render import RenderService
        renderer = RenderService(output);start = time.perf_counter()
        job = renderer.submit({'buildId': build['id'], 'width': 960, 'height': 540, 'samples': 32})
        try:
            while renderer.get(job['id'])['status'] in ('queued', 'running'):time.sleep(.5)
            rendered = renderer.get(job['id']);rendered['seconds'] = round(time.perf_counter() - start, 3)
            evidence['finalRender'] = rendered
            if rendered['status'] == 'completed':
                shutil.copyfile(output / 'renders' / job['id'] / 'final.png', destination / 'cycles-final.png')
            else:raise RuntimeError(rendered)
        finally:renderer.close()
    (destination.parent / 'artifact-verification.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':main()
