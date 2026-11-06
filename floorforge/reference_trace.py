"""Portable references and explicit calibrated manual tracing; no image inference."""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import math
import re

from PIL import Image

from .model import DesignError, sha

MAX_ASSETS = 8_000_000
ALLOWED_FIELDS = {'id', 'name', 'kind', 'sha256', 'note', 'mimeType', 'dataUrl', 'units', 'floorId', 'calibration', 'enabled', 'byteLength', 'originPixels'}


def validate_references(attachments):
    if not isinstance(attachments, list) or len(attachments) > 12:
        raise DesignError('ATTACHMENT_LIMIT', 'Keep at most 12 reference assets.')
    total = 0
    for asset in attachments:
        if not isinstance(asset, dict) or set(asset) - ALLOWED_FIELDS:
            raise DesignError('ATTACHMENT_SCHEMA', 'Reference metadata contains unsupported fields.')
        if 'dataUrl' not in asset:
            continue  # Legacy filename-only references stay explicitly unavailable.
        value = asset['dataUrl']
        if not isinstance(value, str) or len(value) > MAX_ASSETS * 4 / 3 + 100:
            raise DesignError('ATTACHMENT_SIZE', 'Keep original reference images below 8 MB total.')
        match = re.fullmatch(r'data:(image/(?:png|jpeg|webp));base64,([A-Za-z0-9+/=\r\n]+)', value)
        if not match:
            raise DesignError('ATTACHMENT_TYPE', 'Embed PNG, JPEG or WebP references; URLs and executable documents are unsupported.')
        try:
            raw = base64.b64decode(match[2], validate=True)
            total += len(raw)
            if total > MAX_ASSETS:
                raise DesignError('ATTACHMENT_SIZE', 'Keep original reference images below 8 MB total.')
            digest = hashlib.sha256(raw).hexdigest()
            if asset.get('sha256') != digest:
                raise DesignError('ATTACHMENT_HASH', 'A reference image no longer matches its saved hash. Attach the original again.')
            with Image.open(io.BytesIO(raw)) as image:
                if image.width * image.height > 40_000_000:
                    raise DesignError('ATTACHMENT_SIZE', 'Use a reference smaller than 40 megapixels.')
                expected = {'PNG': 'image/png', 'JPEG': 'image/jpeg', 'WEBP': 'image/webp'}.get(image.format)
                if expected != match[1] or asset.get('mimeType', expected) != expected:
                    raise DesignError('ATTACHMENT_TYPE', 'Reference image content and MIME type disagree.')
                image.verify()
        except (ValueError, OSError, Image.DecompressionBombError) as exc:
            if isinstance(exc, DesignError):raise
            raise DesignError('ATTACHMENT_TYPE', 'This reference image is damaged or unsupported.') from exc
    return total


def trace_reference(body):
    """Convert user-authored pixel rectangles, using a user-confirmed scale.

    Pixel Y is explicitly front-to-back here. This is a manual coordinate
    worksheet; neither OCR nor recognition of rooms is performed.
    """
    from .custom_plan import normalize
    project = copy.deepcopy(body.get('project', {}))
    assets = project.get('attachments', [])
    validate_references(assets)
    reference = next((a for a in assets if a.get('id') == body.get('referenceId')), None)
    if reference is None or not reference.get('dataUrl'):
        raise DesignError('TRACE_REFERENCE', 'Keep the original image in the project before tracing.')
    calibration = body.get('calibration', {})
    if calibration.get('confirmed') is not True or body.get('confirmed') is not True:
        raise DesignError('TRACE_CONFIRMATION', 'Confirm the known dimension and your manually traced room interpretation.')
    def point(value):
        if (not isinstance(value, list) or len(value) != 2
                or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or abs(x)>100_000 for x in value)):
            raise DesignError('TRACE_POINT', 'Use finite image coordinates within 100,000 pixels.')
        return value
    pixels = calibration.get('pixels', [])
    if len(pixels) != 2:
        raise DesignError('TRACE_SCALE', 'Mark two endpoints of a known measured dimension.')
    span = math.dist(point(pixels[0]), point(pixels[1]))
    factor = {'mm': 1, 'm': 1000, 'ft': 304.8, 'in': 25.4}.get(calibration.get('units'))
    length = calibration.get('length')
    if (span < 1 or factor is None or isinstance(length, bool) or not isinstance(length, (int, float))
            or not math.isfinite(length) or not 0 < length * factor <= 100_000):
        raise DesignError('TRACE_SCALE', 'Enter a positive known dimension with explicit units and distinct endpoints.')
    scale = length * factor / span
    origin = point(body.get('originPixels', [0, 0]))
    floor_id = body.get('floorId')
    if not isinstance(floor_id, str) or not re.fullmatch(r'[\w-]{1,64}', floor_id):
        raise DesignError('TRACE_FLOOR', 'Choose the destination floor before tracing.')
    rooms = body.get('rooms', [])
    if not isinstance(rooms, list) or not 1 <= len(rooms) <= 120:
        raise DesignError('TRACE_ROOMS', 'Trace between one and 120 room outlines.')
    traced = []
    for room in rooms:
        polygon = room.get('polygon', [])
        if not isinstance(polygon, list) or not 4 <= len(polygon) <= 32:
            raise DesignError('TRACE_POLYGON', 'Draw an orthogonal room outline with 4–32 vertices.')
        traced.append({'id': room.get('id'), 'name': room.get('name', room.get('kind')),
                       'kind': room.get('kind'), 'polygon': [
                           [round((point(p)[i] - origin[i]) * scale, 3) for i in (0, 1)] for p in polygon]})
    editor = project.get('editorState') or {}
    # The tracing picker uses the exact editor's stable floor identities even
    # when Compass is currently active. Keep that saved draft instead of
    # replacing it with a new single-floor plan.
    original_plan = project.get('customPlan') or editor.get('customPlan')
    from .design_journey import resolve_sources
    resolved = resolve_sources(project)
    requested = resolved['project'].get('brief', {}).get('storeys', project.get('brief', {}).get('storeys'))
    if requested is not None and (type(requested) is not int or not 1 <= requested <= 3):
        raise DesignError('TRACE_FLOORS', 'Confirm one to three requested floors before tracing.')
    if original_plan:
        plan = copy.deepcopy(original_plan)
        if not isinstance(plan, dict) or not isinstance(plan.get('floors'), list):
            raise DesignError('TRACE_FLOORS', 'Keep a valid editable floor list before tracing.')
        count = max(requested or 1, len(plan['floors']))
    else:
        compass = project.get('compass') or editor.get('compassDraft') or {}
        saved_floors = compass.get('floors', [])
        count = max(requested or 1, len(saved_floors))
        plan = {'schema': 'floorforge.custom-plan/1', 'units': 'mm', 'wallThickness': 150,
                'floors': [{'id': f['id'], 'rooms': [], 'walls': [], 'openings': []} for f in saved_floors],
                'stairs': []}
    if not 1 <= count <= 3:
        raise DesignError('TRACE_FLOORS', 'Keep one to three occupied floors for this tracing adapter.')
    floor_index = body.get('floorIndex')
    if floor_index is not None and (type(floor_index) is not int or not 0 <= floor_index < count):
        raise DesignError('TRACE_FLOOR_MAPPING', 'Choose an existing requested floor index for the tracing.')
    mapped_index = next((i for i, f in enumerate(plan['floors']) if f['id'] == floor_id), None)
    if mapped_index is not None and floor_index is not None and mapped_index != floor_index:
        raise DesignError('TRACE_FLOOR_MAPPING', 'The selected floor identity and its floor index disagree.')
    if mapped_index is None:
        if plan['floors'] and (floor_index is None or floor_index < len(plan['floors'])):
            raise DesignError('TRACE_FLOOR_MAPPING', 'Choose an existing saved floor identity; tracing cannot rename or add an occupied floor silently.')
        # With no prior floor map, a multi-floor destination needs its explicit
        # index. An opaque ID such as "first" must never silently become Ground.
        if floor_index is None:
            if count > 1:
                raise DesignError('TRACE_FLOOR_MAPPING', 'Choose the destination floor index before tracing this multi-floor home.')
            floor_index = 0
        mapped_index = floor_index
    used_ids = {f['id'] for f in plan['floors']} | {floor_id}
    used_ids.update(item['id'] for f in plan['floors'] for key in ('rooms', 'walls', 'openings') for item in f.get(key, []))
    used_ids.update(item['id'] for item in plan.get('stairs', []))
    while len(plan['floors']) < count:
        index = len(plan['floors'])
        ident = floor_id if index == mapped_index else f'trace-floor-{index}'
        suffix = 0
        while index != mapped_index and ident in used_ids:
            suffix += 1
            ident = f'trace-floor-{index}-{suffix}'
        used_ids.add(ident)
        plan['floors'].append({'id': ident, 'rooms': [], 'walls': [], 'openings': []})
    existing = next((f for f in plan['floors'] if f['id'] == floor_id), None)
    if existing and existing.get('rooms'):
        raise DesignError('TRACE_OVERLAP', 'Trace into an empty floor or explicitly resolve the existing authoritative layout first.')
    floor = {'id': floor_id, 'rooms': traced, 'walls': [], 'openings': []}
    if existing is not None:plan['floors'][plan['floors'].index(existing)] = floor
    else:plan['floors'].append(floor)
    # Normalization checks shape and identity, not architectural feasibility.
    plan = normalize(plan, len(plan['floors']))
    reference.update(floorId=floor_id, calibration={**calibration, 'mmPerPixel': scale,
                                                   'originPixels': origin, 'interpretationConfirmed': True})
    project['customPlan'] = plan
    project.setdefault('brief', {}).setdefault('storeys', count)
    project.setdefault('editorState', {})['mode'] = 'custom'
    journey = project.setdefault('designJourney', {'schema': 'myverandah.journey/1'})
    journey['approvals'] = {};journey.pop('confirmation', None)
    if 'inputs' in journey:
        # An explicit source registry is authoritative. Append the measured
        # tracing as a distinct source, retaining old layouts so any overlap is
        # resolved by the ordinary authority question instead of ignoring it.
        if not isinstance(journey['inputs'], list):
            raise DesignError('SOURCE_LIMIT', 'Keep a list of source records before adding a tracing.')
        source_id = 'trace-' + sha({'reference': reference['id'], 'floor': floor_id, 'plan': plan})[:24]
        source = {'id': source_id, 'kind': 'plan', 'enabled': True, 'units': 'mm',
                  'floorIds': [f['id'] for f in plan['floors']], 'geometry': copy.deepcopy(plan),
                  'interpretation': {'method': 'confirmed manual calibrated tracing'},
                  'provenance': {'referenceId': reference['id'], 'sha256': reference['sha256'],
                                 'calibration': copy.deepcopy(reference['calibration'])}}
        journey['inputs'] = [s for s in journey['inputs'] if s.get('id') != source_id] + [source]

    return {'project': project, 'status': 'traced-unvalidated', 'mmPerPixel': scale,
            'notes': ['Only your manually entered outlines were measured. Review wall allowances, doors, windows and stairs in 2D.',
                      'The image remains a reference; geometric validation runs when you prepare the home.']}
