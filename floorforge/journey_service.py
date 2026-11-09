"""Local immutable 2D publications and approval gate for the custom journey.

The signing key belongs to the local studio, never to portable project files.
An imported certificate from another studio is retained but requires review here.
"""
from __future__ import annotations

import copy
import hashlib
import re
import secrets
import threading
from pathlib import Path

from .model import DesignError, atomic, canonical, read_json, sha


class JourneyService:
    def __init__(self, out):
        self.out = Path(out)
        self.lock = threading.RLock()

    def secret(self):
        with self.lock:
            path = self.out / '.journey-signing-key'
            if not path.exists():
                atomic(path, secrets.token_bytes(32))
                try:
                    path.chmod(0o600)
                except OSError:
                    pass
            return path.read_bytes()

    def inputs(self, project):
        """Restore editable inputs even when they cannot compile a valid home.

        Display values are not an applied-source claim or a geometry identity.
        The independent prepare/generation gates remain mandatory.
        """
        from .design_journey import resolve_sources
        from .model import DEFAULTS
        from .reference_trace import validate_references
        validate_references(project.get('attachments', []))
        result=resolve_sources(project)
        values={**DEFAULTS,**project.get('brief',{})}
        for source in project.get('sources',[]):
            if source.get('id') in ('studio-field-edits','studio-auto-setbacks') and source.get('enabled',True):
                values.update(source.get('values',{}))
        # Saved form revisions are display fallbacks only. An enabled text or
        # drawing source may resolve a field while a different basic still
        # needs a question; that resolved field must win in the visible form.
        values.update(result['project'].get('brief',{}))
        provenance={key:{'selected':['restored-display'],'candidates':[]} for key in values}
        if not any(k in project.get('brief',{}) for k in ('front_mm','rear_mm','left_mm','right_mm')):
            for key in ('front_mm','rear_mm','left_mm','right_mm'):provenance[key]['selected']=['derived-display']
        return {'editable':True,'values':values,'provenance':provenance,'planHash':None,
                'draftRevision':project.get('draftRevision',0),
                **{k:result[k] for k in ('sources','requirements','questions','question')}}

    def prepare(self, project):
        from .design_journey import prepare, reusable_floor_approvals, verify_approval
        from .reference_trace import validate_references
        from .drawings import pdf_sheets, dxf_export
        from .pipeline import kernel_hash
        validate_references(project.get('attachments', []))
        result = prepare(copy.deepcopy(project))
        if not result.get('valid'):
            return {**self.public(result), 'approvals': {}, 'confirmation': None}
        # This identity includes source interpretation and appearance, while the
        # independent geometryHash governs approval reuse across finishes.
        ident = sha({'project': project, 'kernel': kernel_hash()})[:32]
        result['preparationId'] = ident
        base = self.out / 'preparations' / ident
        with self.lock:
            if (base / 'manifest.json').exists():
                try:
                    self.load(ident)
                except DesignError:
                    # A retry must recover from damaged generated files. Keep
                    # the damaged publication outside the served directory,
                    # then rebuild it from the freshly validated model.
                    quarantine = self.out / '.damaged-preparations'
                    quarantine.mkdir(parents=True, exist_ok=True)
                    base.rename(quarantine / (ident + '-' + secrets.token_hex(4)))
            if not (base / 'manifest.json').exists():
                base.mkdir(parents=True, exist_ok=True)
                files = {'preparation.json': canonical(result),
                         'canonical.json': canonical(result['canonical']),
                         'project.floorforge.json': canonical(project),
                         'drawings.pdf': pdf_sheets(result['sheets'], result['building'], result['report'])}
                dxf_export(result['building'], {'furniture': []}, base / 'floorplans.dxf')
                files['floorplans.dxf'] = (base / 'floorplans.dxf').read_bytes()
                for index, floor in enumerate(result['floors']):
                    files[f'floor-{index + 1}.svg'] = floor['svg'].encode('utf-8')
                for name, data in files.items():
                    atomic(base / name, data)
                atomic(base / 'manifest.json', canonical({
                    'schema': 'myverandah.preparation/1', 'geometryHash': result['geometryHash'],
                    'files': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}))
        public = self.public(result)
        public['downloads'] = {name: f'/preparations/{ident}/{name}' for name in
                               ('drawings.pdf', 'floorplans.dxf', 'canonical.json')}
        # Trust is local to this studio, not to a portable JSON record or the
        # immutable drawing cache. Always return the authoritative reusable set
        # so an imported/expired approval cannot disable the review controls.
        journey = project.get('designJourney') or {}
        secret = self.secret()
        public['approvals'] = reusable_floor_approvals(result, journey.get('approvals', {}), secret)
        public['confirmation'] = None
        certificate = journey.get('confirmation')
        if certificate:
            try:
                verify_approval(result, certificate, secret)
            except DesignError:
                pass
            else:
                public['confirmation'] = copy.deepcopy(certificate)
        return public

    @staticmethod
    def public(result):
        return {key: value for key, value in result.items() if key not in ('building', 'sheets', 'report')}

    def load(self, ident):
        if not isinstance(ident, str) or not re.fullmatch(r'[0-9a-f]{32}', ident):
            raise DesignError('PREPARATION_ID', 'Review the current 2D drawings before approving.')
        base = self.out / 'preparations' / ident
        try:
            manifest = read_json(base / 'manifest.json')
            files = manifest['files']
            if not isinstance(files, dict) or not {'preparation.json', 'canonical.json',
                    'project.floorforge.json', 'drawings.pdf', 'floorplans.dxf', 'floor-1.svg'} <= files.keys():
                raise DesignError('PREPARATION_MODIFIED', 'This 2D publication changed. Prepare fresh drawings.')
            for name,digest in files.items():
                file=(base/name).resolve()
                if not file.is_relative_to(base.resolve()) or hashlib.sha256(file.read_bytes()).hexdigest()!=digest:
                    raise DesignError('PREPARATION_MODIFIED', 'This 2D publication changed. Prepare fresh drawings.')
            result = read_json(base / 'preparation.json')
            if any(f'floor-{index+1}.svg' not in files for index in range(len(result['floors']))):
                raise DesignError('PREPARATION_MODIFIED', 'A floor drawing is missing. Prepare fresh drawings.')
            return result
        except DesignError:
            raise
        except (OSError, KeyError, ValueError, TypeError, AttributeError) as exc:
            raise DesignError('PREPARATION_MISSING', 'These drawings are unavailable. Prepare the saved project again.') from exc

    def approve(self, body):
        from .design_journey import approve_floor
        preparation = self.load(body.get('preparationId'))
        if body.get('floorHash') is not None and body.get('geometryHash')!=preparation['geometryHash']:
            raise DesignError('APPROVAL_STALE','The coordinated home changed. Review its current drawings.')
        return {'approval': approve_floor(preparation, body.get('floorId'), body.get('floorHash',body.get('geometryHash')), self.secret())}

    def confirm(self, body):
        from .design_journey import confirm_home
        preparation = self.load(body.get('preparationId'))
        return {'confirmation': confirm_home(preparation, body.get('approvals', {}),
                                             body.get('geometryHash'), self.secret())}

    def generation_payload(self, project):
        from .design_journey import prepare, verify_approval
        from .reference_trace import validate_references
        validate_references(project.get('attachments', []))
        journey = project.get('designJourney')
        if not isinstance(journey, dict):
            raise DesignError('APPROVAL_REQUIRED', 'Review and accept every requested floor in 2D and confirm the whole home before generating 3D.')
        # Recompile the request, not a client-supplied model or a stale saved
        # preparation. Cosmetic changes can reuse the same signed geometry.
        preparation = prepare(copy.deepcopy(project))
        if not preparation.get('valid'):
            raise DesignError('DESIGN_QUESTION', 'Resolve the necessary design question before generating 3D.',
                              self.public(preparation))
        if not verify_approval(preparation, journey.get('confirmation'), self.secret()):
            raise DesignError('APPROVAL_REQUIRED', 'The current geometry needs approval for every floor and the coordinated home.')
        result = copy.deepcopy(preparation['preparedProject'])
        # The pipeline receives the original portable project separately; it is
        # never replaced by this compilation adapter in save/reopen or exports.
        return result, preparation


def needs_approval(project):
    return bool(project.get('designJourney') is not None or project.get('customPlan') is not None
                or project.get('compass') is not None
                or project.get('editorState', {}).get('mode') in ('custom', 'compass'))
