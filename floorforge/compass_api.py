"""Compass entry points, enabled by default with an explicit server opt-out."""
import os
from .model import DesignError
from .compass_input import fields, remap, ADAPTER, SCHEMA, SPLIT_SCHEMA, GRID_OPTIONS


def capabilities():
    return {'enabled': os.environ.get('FLOORFORGE_COMPASS', '1').strip().lower() in ('1', 'true', 'yes'),
            'schema': SCHEMA, 'adapterVersion': ADAPTER, 'densities': [s['cells'] for s in GRID_OPTIONS],
            'schemas': [SCHEMA, SPLIT_SCHEMA], 'splitDirections': ['left-right', 'front-back'],
            'gridOptions': GRID_OPTIONS, 'legacyGridOptions': [{'cols': 4, 'rows': 8, 'cells': 32}],
            'operational': ['room-regions', 'half-cells', 'front-back-halves', 'drawn-room-preview', 'prepare-unused-space', 'connections', 'attached-baths', 'internal-stairs', 'size-targets', 'size-locks', 'scope'],
            'advisory': ['plot-context', 'notes'],
            'unavailable': ['gate-position', 'second-road-geometry', 'setback-band-zones', 'external-stairs', 'lift-design', 'automatic-fit']}


def require_enabled():
    if not capabilities()['enabled']:
        raise DesignError('COMPASS_DISABLED', 'Compass is disabled on this server. Remove the FLOORFORGE_COMPASS override or set it to 1, then restart to edit and generate. Saved drafts remain available.')


def dispatch(path, body):
    require_enabled()
    if path in ('/api/compass/check', '/api/compass/convert', '/api/compass/prepare'):
        fields(body, ('project', 'compass', 'scope'), 'Compass conversion request')
        project = body.get('project', {})
        draft = body.get('compass')
        original = None
        if project.get('designJourney') is not None:
            from copy import deepcopy
            from .design_journey import editing_project
            original = deepcopy(project)
            if draft is not None:
                original['compass'] = deepcopy(draft)
                original.setdefault('editorState', {})['compassDraft'] = deepcopy(draft)
            project = editing_project(original, target='compass')
            # The preparation/search tools read only this metadata for pins;
            # source selection has already been resolved into project.brief.
            if path == '/api/compass/prepare':
                project['designJourney'] = {'pins': deepcopy(original['designJourney'].get('pins', {}))}
        if path == '/api/compass/prepare':
            from .compass_prepare import prepare
            result = prepare(project, draft, body.get('scope'))
        else:
            from .compass_adapter import proposal
            result = proposal(project, draft, body.get('scope'))
        if original is not None:
            result['designJourney'] = deepcopy(original['designJourney'])
            result['draftPreserved'] = True
        return result
    if path == '/api/compass/remap':
        fields(body, ('compass', 'rows', 'cols'), 'Compass remapping request')
        return remap(body.get('compass'), body.get('rows'), body.get('cols'))
    if path == '/api/compass/migrate-preview':
        fields(body, ('project',), 'Compass migration request')
        # Exact polygons and legacy metric cells must never be silently rasterized.
        project = body.get('project')
        if not isinstance(project, dict):
            raise DesignError('COMPASS_MIGRATION', 'Supply the original project for a recoverable conversion preview.')
        return {'valid': False, 'originalProject': project, 'candidate': None,
                'issues': [{'code': 'EXPLICIT_REPLACEMENT', 'message': 'Keep the original geometry input. Start a separate Compass draft; replacing an authored plan requires a reviewed geometry proposal.'}]}
    raise DesignError('COMPASS_ROUTE', 'Unknown Compass operation.')
