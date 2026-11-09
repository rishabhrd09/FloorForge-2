"""Optional local Cycles stills bound to immutable, approved custom builds."""
from __future__ import annotations

import concurrent.futures
import hashlib
import re
import secrets
import shutil
import subprocess
import threading
from pathlib import Path

from .model import DesignError, atomic, canonical, read_json


def blender_path():
    found = shutil.which('blender')
    if found:return found
    mac = Path('/Applications/Blender.app/Contents/MacOS/Blender')
    return str(mac) if mac.is_file() else None


def capabilities():
    return {'available': bool(blender_path()), 'engine': 'Blender Cycles', 'externalRequests': False,
            'note': 'Optional offline path-traced still. CPU time depends on your machine; interactive preview remains available.'}


class RenderService:
    def __init__(self, out):
        self.out = Path(out);self.jobs = {};self.processes = {};self.lock = threading.RLock()
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def submit(self, body):
        from .pipeline import ROOT
        executable = blender_path()
        if not executable:
            raise DesignError('BLENDER_UNAVAILABLE', 'Install Blender 4.2 or newer to make a Cycles still. The interactive preview needs no Blender.')
        build_id = body.get('buildId')
        if not isinstance(build_id, str) or not re.fullmatch('[0-9a-f]{24}', build_id):
            raise DesignError('RENDER_BUILD', 'Generate the approved home before requesting a final still.')
        build = self.out / 'builds' / build_id
        try:
            manifest = read_json(build / 'manifest.json')
            if not manifest.get('geometryHash'):
                raise DesignError('RENDER_APPROVAL', 'This custom render needs an approved geometry build.')
            for name in ('model.glb', 'scene.json', 'geometry-approval.json'):
                if hashlib.sha256((build / name).read_bytes()).hexdigest() != manifest['files'][name]:
                    raise DesignError('RENDER_MODIFIED', 'The generated model changed. Regenerate before rendering.')
        except (OSError, KeyError) as exc:
            raise DesignError('RENDER_BUILD', 'The complete approved build is unavailable.') from exc
        options = {'view': body.get('view', 'hero'), 'grade': body.get('grade', 'day'),
                   'width': body.get('width', 960), 'height': body.get('height', 540), 'samples': body.get('samples', 32)}
        if options['view'] not in ('hero', 'front', 'entrance') or options['grade'] not in ('day', 'golden', 'dusk'):
            raise DesignError('RENDER_OPTIONS', 'Choose a supported view and lighting grade.')
        for key, bounds in {'width': (320, 1920), 'height': (240, 1080), 'samples': (8, 128)}.items():
            if type(options[key]) is not int or not bounds[0] <= options[key] <= bounds[1]:
                raise DesignError('RENDER_OPTIONS', f'Choose {key} between {bounds[0]} and {bounds[1]}.')
        ident = secrets.token_hex(8);destination = self.out / 'renders' / ident
        destination.mkdir(parents=True)
        with self.lock:
            if any(j['status'] in ('queued', 'running') for j in self.jobs.values()):
                raise DesignError('RENDER_BUSY', 'A final still is already rendering. Cancel it or wait before retrying.')
            self.jobs[ident] = {'id': ident, 'status': 'queued', 'buildId': build_id,
                                'geometryHash': manifest['geometryHash'], 'engine': 'Blender Cycles', 'options': options}
        def worker():
            with self.lock:
                if self.jobs[ident]['status'] == 'cancelled':return
                self.jobs[ident]['status'] = 'running'
            command = [executable, '--background', '--threads', '2', '--python', str(ROOT / 'scripts/render_cycles.py'), '--',
                       '--glb', str(build / 'model.glb'), '--scene', str(build / 'scene.json'),
                       '--out', str(destination), '--name', 'final']
            for key, value in options.items():command.extend(['--' + key, str(value)])
            try:
                with (destination / 'render.log').open('wb') as log:
                    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, shell=False)
                    with self.lock:
                        self.processes[ident] = process
                        if self.jobs[ident]['status'] == 'cancelled':process.terminate()
                    try:code = process.wait(timeout=1800)
                    except subprocess.TimeoutExpired:
                        process.kill();process.wait()
                        raise DesignError('RENDER_TIMEOUT', 'The 30-minute render limit was reached. Retry at a lower resolution or sample count.')
                with self.lock:
                    if self.jobs[ident]['status'] == 'cancelled':return
                    image = destination / 'final.png'
                    if code != 0 or not image.is_file():
                        raise DesignError('RENDER_FAILED', 'Blender could not finish this still. The interactive preview and saved model remain available.')
                    self.jobs[ident].update(status='completed', result={
                        'url': f'/renders/{ident}/final.png', 'geometryHash': manifest['geometryHash'],
                        'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
                        'label': 'Completed Cycles still · base model materials'})
                    atomic(destination / 'result.json', canonical(self.jobs[ident]))
            except Exception as exc:
                with self.lock:
                    if self.jobs[ident]['status'] != 'cancelled':
                        self.jobs[ident].update(status='error', error=exc.record() if isinstance(exc, DesignError) else
                                               {'code': 'RENDER_FAILED', 'message': 'The local renderer could not start or finish.'})
            finally:
                with self.lock:self.processes.pop(ident, None)
        self.pool.submit(worker)
        return dict(self.jobs[ident])

    def get(self, ident):
        with self.lock:
            if ident not in self.jobs:raise DesignError('RENDER_UNKNOWN', 'That final render is unavailable.')
            return dict(self.jobs[ident])

    def cancel(self, ident):
        with self.lock:
            job = self.get(ident)
            if job['status'] in ('queued', 'running'):
                self.jobs[ident]['status'] = 'cancelled'
                process = self.processes.get(ident)
                if process and process.poll() is None:process.terminate()
            return self.get(ident)

    def close(self):
        for ident in list(self.jobs):self.cancel(ident)
        self.pool.shutdown(wait=True)
