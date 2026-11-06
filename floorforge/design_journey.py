"""Deterministic custom-home input, geometry and approval contract.

The legacy compiler remains the single geometry kernel. This module is an
opt-in boundary around it: sources are resolved before compilation, plan sheets
are published without presentation meshes, and approvals identify measured
geometry rather than an appearance-dependent cache key.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import hmac
import math
import re

from .model import DEFAULTS, DesignError, canonical, sha

SCHEMA = 'myverandah.journey/1'
MODEL_SCHEMA = 'myverandah.geometry/1'
TOLERANCE = {'coordinate_mm': .001, 'comparison_mm': 1., 'area_mm2': 1.}
INPUT_KINDS = {'plot', 'survey', 'text', 'compass', 'dxf', 'plan', 'sketch', 'grid'}
PLOT_FIELDS = {'width_mm', 'depth_mm', 'road_bearing_deg', 'storeys', 'front_mm',
               'rear_mm', 'left_mm', 'right_mm', 'plinth_mm', 'floor_height_mm',
               'roof_access', 'latitude', 'longitude', 'timezone_hours'}
COSMETIC_FIELDS = {'title', 'style', 'finish', 'exterior_theme', 'interior_theme',
                  'change_policy', 'interior_layout_locked', 'theme_version',
                  'seed', 'solar_date', 'solar_hour', 'budget_lakh',
                  'rate_low_inr_ft2', 'rate_high_inr_ft2', 'cost_contingency_pct'}
PRESETS = {
    'warm-natural': {'label': 'Warm natural', 'description': 'Warm stone, timber and soft natural finishes.',
                     'style': 'warm', 'exterior_theme': 'warm_modern_minimal', 'interior_theme': 'bright_natural'},
    'quiet-modern': {'label': 'Quiet modern', 'description': 'Pale finishes, quiet contrasts and simple furniture.',
                     'style': 'minimal', 'exterior_theme': 'modern_tropical', 'interior_theme': 'quiet_minimal'},
    'earth-verandah': {'label': 'Earth verandah', 'description': 'Earth colours and timber with a warm interior.',
                       'style': 'terracotta', 'exterior_theme': 'earth_terracotta', 'interior_theme': 'earthy_modern_indian'},
}


def appearance_catalogue():
    return [{'id': key, **deepcopy(value), 'geometryEffect': 'none',
             'compatible': True, 'previewKind': 'material recipe',
             'note': 'Finishes only. New porches, facades or openings require a new 2D review.'}
            for key, value in PRESETS.items()]


def _metadata(project):
    value = project.get('designJourney', {})
    if not isinstance(value, dict) or value.get('schema', SCHEMA) != SCHEMA:
        raise DesignError('JOURNEY_VERSION', 'This design journey needs a compatible reader. Keep the original project.')
    canonical(value)  # Reject non-finite or non-JSON state before signing anything.
    return deepcopy(value)


def _question(code, prompt, explanation, choices, *, affected=(), identity=None):
    ident = code.lower() + '-' + sha(identity if identity is not None else [prompt, choices])[:16]
    return {'id': ident, 'code': code, 'prompt': prompt, 'title': prompt,
            'explanation': explanation, 'affected': list(affected), 'choices': choices,
            'recommended': next((c['id'] for c in choices if c.get('recommended')), choices[0]['id'] if choices else None)}


def _choice(ident, label, description, recommended=False, **more):
    return {'id': ident, 'label': label, 'description': description, 'recommended': recommended, **more}


def _normal_values(source):
    values = deepcopy(source.get('values') or {})
    if not isinstance(values, dict):
        raise DesignError('SOURCE_VALUES', 'Source measurements must be an object.')
    unit = source.get('units', 'mm')
    if source.get('kind') == 'sketch' and unit == 'px' and not values:
        return {}  # Pixels describe an unmeasured reference, never a room size.
    factors = {'mm': 1, 'cm': 10, 'm': 1000, 'ft': 304.8, 'in': 25.4}
    if unit not in factors:
        raise DesignError('SOURCE_UNITS', 'Choose mm, cm, m, ft or in for a measured input.')
    # Explicit *_mm fields already have units; human-sized width/depth use the
    # source's declared units. There is no inference from image pixel counts.
    for field in ('width', 'depth', 'front', 'rear', 'left', 'right', 'floor_height'):
        if field in values:
            value = values.pop(field)
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
                raise DesignError('SOURCE_MEASUREMENT', 'Use a finite number for each measurement.')
            values[field + '_mm'] = round(value * factors[unit])
    return values


def _legacy_sources(project, meta):
    """Migrate existing editor choices without modifying the original payload."""
    editor = project.get('editorState') or {}
    selected = meta.get('enabledInputs', editor.get('homeInputs'))
    selected = set(selected) if selected is not None else None
    enabled = lambda kind: selected is None or kind in selected
    brief = deepcopy(project.get('brief') or {})
    # These two IDs are authored by the studio when the owner edits the same
    # form. They are revisions of that form, not independent surveys that ought
    # to trigger a question against its older value. Preserve the originals in
    # provenance while using the latest enabled revision.
    revisions = [deepcopy(s) for s in project.get('sources', [])
                 if s.get('id') in ('studio-field-edits', 'studio-auto-setbacks') and s.get('enabled', True)]
    superseded = {k: brief.get(k) for s in revisions for k in s.get('values', {}) if k in brief}
    for revision in revisions:
        brief.update(revision.get('values', {}))
    result = []

    def add(ident, kind, **fields):
        result.append({'id': ident, 'kind': kind, 'enabled': enabled(kind), 'units': 'mm',
                       'floorIds': [], 'provenance': {'origin': 'project', 'path': fields.pop('path', kind)}, **fields})

    add('plot-basics', 'plot', values={k: v for k, v in brief.items() if k in PLOT_FIELDS}, path='brief')
    add('home-goals', 'survey', values={k: v for k, v in brief.items() if k not in PLOT_FIELDS | COSMETIC_FIELDS}, path='brief')
    for src in result:
        if revisions:
            src['provenance'].update(revisions=revisions, supersededValues=superseded)
    if project.get('text'):
        add('written-requirements', 'text', text=project['text'], path='text')
    compass = project.get('compass') or editor.get('compassDraft')
    if compass is not None:
        add('compass-map', 'compass', geometry=deepcopy(compass),
            floorIds=[f['id'] for f in compass.get('floors', [])], path='compass / editorState.compassDraft')
    saved_exact = editor.get('customPlan')
    custom = project.get('customPlan') or (saved_exact if isinstance(saved_exact, dict) and
        (editor.get('mode') == 'custom' or any(f.get('rooms') for f in saved_exact.get('floors', []))) else None)
    imports = [item for item in meta.get('imports', []) if isinstance(item, dict) and item.get('kind') == 'dxf']
    # Each earlier imported drawing remains a distinct input. The most recent
    # import is represented by the live exact editor, whose later edits are a
    # revision of that source. Two overlapping drawings trigger one question;
    # disjoint floor mappings can be combined below.
    for index, original in enumerate(imports[:-1] if custom is not None else imports):
        supplied = original.get('provenance', {})
        geometry = supplied.get('geometry') or original.get('geometry')
        if geometry:
            add(original.get('id') or 'imported-drawing-' + str(index), 'dxf', geometry=deepcopy(geometry),
                floorIds=[f['id'] for f in geometry.get('floors', [])],
                units=original.get('units', 'mm'), enabled=enabled('dxf') and original.get('enabled', True),
                provenance=deepcopy(original))
            for key in ('floorIndices', 'floorOrder', 'requestedFloorCount'):
                if key in original or key in supplied:
                    result[-1][key] = deepcopy(original.get(key, supplied.get(key)))
    for index, original in enumerate(meta.get('layoutSources', [])):
        if not isinstance(original, dict) or original.get('kind') != 'plan' or not isinstance(original.get('geometry'), dict):
            raise DesignError('SOURCE_SCHEMA', 'Retained manual layouts need a measured plan and a stable source identity.')
        geometry = original['geometry']
        add(original.get('id') or 'manual-layout-' + str(index), 'plan', geometry=deepcopy(geometry),
            enabled=original.get('enabled', True), units=original.get('units', 'mm'),
            floorIds=deepcopy(original.get('floorIds', [f['id'] for f in geometry.get('floors', [])])),
            provenance=deepcopy(original.get('provenance', {'origin': 'manual-exact-editor'})))
        for key in ('floorIndices', 'floorOrder', 'requestedFloorCount'):
            if key in original:
                result[-1][key] = deepcopy(original[key])
    if custom is not None:
        # Direct exact editing is a supported layout even when the old picker
        # had no separate "plan" checkbox. DXF selection remains operational.
        imported = (any(s.get('kind') == 'dxf' for s in meta.get('imports', []))
                    or any(str(f.get('id', '')).startswith('dxf-') or
                           any(str(r.get('id', '')).startswith('dxf-room-') for r in f.get('rooms', []))
                           for f in custom.get('floors', [])))
        kind = 'dxf' if imported or selected is not None and 'dxf' in selected else 'plan'
        add('exact-layout', kind, geometry=deepcopy(custom),
            enabled=(enabled('dxf') and (not imports or imports[-1].get('enabled', True))
                     if kind == 'dxf' else editor.get('mode', 'custom') == 'custom'),
            floorIds=[f['id'] for f in custom.get('floors', [])], path='customPlan',
            provenance={'origin': 'exact-editor', **({'originalSource': deepcopy(imports[-1])} if imports else {})})
        if imports and ('floorIndices' in imports[-1] or 'floorIndices' in imports[-1].get('provenance', {})):
            original = imports[-1]
            supplied = original.get('provenance', {})
            # The editor displays the complete ordered home, while the saved
            # import contains only its original mapped floor. Empty editor
            # placeholders reserve an index without owning any room geometry.
            result[-1]['floorIndices'] = (list(range(len(custom.get('floors', []))))
                if len(custom.get('floors', [])) > 1 else deepcopy(original.get('floorIndices', supplied.get('floorIndices'))))
            for key in ('floorOrder', 'requestedFloorCount'):
                if key in original or key in supplied:
                    result[-1][key] = deepcopy(original.get(key, supplied.get(key)))
    if project.get('grid') is not None:
        add('floor-guide', 'grid', geometry=deepcopy(project['grid']), enabled=editor.get('mode', 'guide') == 'guide', path='grid')
    for i, source in enumerate(project.get('sources') or []):
        if source.get('id') in ('studio-field-edits', 'studio-auto-setbacks'):
            continue
        kind = source.get('kind', 'survey')
        if kind == 'plan' and source.get('id', '').startswith(('imported-dxf', 'dxf-')):
            kind = 'dxf'
        kind = {'form': 'plot', 'edit': 'plot', 'proposal': 'survey', 'sketch': 'sketch', 'plan': 'plan'}.get(kind, kind)
        if kind not in INPUT_KINDS:
            kind = 'survey'
        add('loaded-' + source.get('id', str(i)), kind, values=deepcopy(source.get('values', {})),
            text=source.get('raw_text', '') if kind == 'text' else '',
            enabled=bool(source.get('enabled', True)) and enabled(kind),
            provenance={'origin': 'saved-source', 'sourceId': source.get('id')})
    for i, asset in enumerate(project.get('attachments') or []):
        add(asset.get('id') or 'reference-' + str(i), 'sketch', reference=deepcopy(asset), units=asset.get('units','px'),
            enabled=enabled('sketch') and asset.get('enabled', True) is not False, path='attachments/' + str(i))
    return result


def normalize_sources(project):
    meta = _metadata(project)
    sources = deepcopy(meta.get('inputs')) if 'inputs' in meta else _legacy_sources(project, meta)
    if not isinstance(sources, list) or len(sources) > 64:
        raise DesignError('SOURCE_LIMIT', 'Keep at most 64 source records.')
    seen = set()
    selected = meta.get('enabledInputs', (project.get('editorState') or {}).get('homeInputs'))
    if selected is not None and (not isinstance(selected, list) or any(k not in {'plot', 'survey', 'text', 'compass', 'dxf', 'sketch'} for k in selected)):
        raise DesignError('INPUT_SELECTION', 'Choose supported input methods.')
    for src in sources:
        if not isinstance(src, dict):
            raise DesignError('SOURCE_SCHEMA', 'Every input must have an identity and a supported kind.')
        ident = src.get('id')
        if not isinstance(ident, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', ident) or ident in seen:
            raise DesignError('SOURCE_ID', 'Give each input a unique stable identity.')
        seen.add(ident)
        if src.get('kind') not in INPUT_KINDS or type(src.get('enabled', True)) is not bool:
            raise DesignError('SOURCE_SCHEMA', 'Choose a supported source kind and a boolean enabled state.')
        src.setdefault('enabled', True)
        if 'inputs' in meta and selected is not None and src['kind'] not in ('plan', 'grid'):
            src['originalEnabled'] = src['enabled']
            src['enabled'] = src['enabled'] and src['kind'] in selected
            src['enabledByInputChoice'] = src['kind'] in selected
        src.setdefault('units', 'mm')
        src.setdefault('floorIds', [])
        if not isinstance(src['floorIds'], list) or any(not isinstance(x, str) for x in src['floorIds']):
            raise DesignError('SOURCE_FLOORS', 'Floor mapping must contain stable floor identities.')
        if 'floorIndices' in src:
            indices = src['floorIndices']
            floors = (src.get('geometry') or {}).get('floors', [])
            if (not isinstance(indices, list) or len(indices) != len(floors)
                    or any(type(i) is not int or not 0 <= i < 3 for i in indices)
                    or len(set(indices)) != len(indices)):
                raise DesignError('SOURCE_FLOOR_INDICES', 'Map each supplied floor to a distinct physical level: ground 0, first 1 or second 2.')
        if 'floorOrder' in src:
            order = src['floorOrder']
            if (not isinstance(order, list) or not 1 <= len(order) <= 3
                    or any(not isinstance(i, str) or not i for i in order) or len(set(order)) != len(order)):
                raise DesignError('SOURCE_FLOORS', 'Keep a unique stable identity for each ordered physical floor.')
        if 'requestedFloorCount' in src and (type(src['requestedFloorCount']) is not int or not 1 <= src['requestedFloorCount'] <= 3):
            raise DesignError('SOURCE_FLOORS', 'Choose one, two or three requested physical floors.')
        src.setdefault('provenance', {'origin': 'user-supplied'})
        if 'confidence' in src and (isinstance(src['confidence'], bool) or not isinstance(src['confidence'], (int, float))
                                    or not math.isfinite(src['confidence']) or not 0 <= src['confidence'] <= 1):
            raise DesignError('SOURCE_CONFIDENCE', 'Confidence must be a number from zero to one.')
        src['values'] = _normal_values(src)
        if src['kind'] == 'text' and src.get('text'):
            from .intent import parse_text
            parsed = parse_text(src['text'])
            src['values'] = {**parsed['values'], **src['values']}
            src['interpretation'] = {'method': 'deterministic grammar', 'reading': parsed['reading'],
                                     'spatialHints': parsed.get('spatial_hints', [])}
        else:
            src.setdefault('interpretation', {'method': 'explicit measured data' if src.get('geometry') or src['values'] else 'reference'})
        canonical(src)
    if 'inputs' in meta:
        editor = project.get('editorState') or {}
        live = project.get('customPlan')
        explicit_edit = (meta.get('editingSourceId') is not None or editor.get('mode') == 'custom'
                         and editor.get('customPlan') is not None and editor['customPlan'] == live)
        if explicit_edit and isinstance(live, dict):
            live_floors = [f['id'] for f in live.get('floors', [])]
            possible = [s for s in sources if s['enabled'] and s['kind'] in ('plan', 'dxf') and s.get('geometry')
                        and [f['id'] for f in s['geometry'].get('floors', [])] == live_floors
                        and (not meta.get('editingSourceId') or s['id'] == meta['editingSourceId'])]
            # A single source with the same stable floor identities is the
            # current exact editor's revision. Competing sources are never
            # silently rebound by their position in the list.
            if len(possible) == 1 and possible[0]['geometry'] != live:
                src = possible[0]
                src['provenance'] = {**src['provenance'], 'editorRevisionOf': sha(src['geometry']),
                                     'originalGeometry': deepcopy(src['geometry'])}
                src['geometry'] = deepcopy(live)
                src['interpretation'] = {'method': 'explicit exact-editor revision',
                                         'sourceId': src['id'], 'originalRetained': True}
    return sources


def _requirement(src, field, value, status='applied', message=''):
    return {'id': src['id'] + ':' + field, 'sourceId': src['id'], 'source': src['id'],
            'label': field.replace('_mm', '').replace('_', ' '), 'field': field, 'value': value,
            'status': status, 'message': message, 'units': src['units'],
            'floorIds': deepcopy(src['floorIds']), 'floorIndices': deepcopy(src.get('floorIndices', [])),
            'provenance': deepcopy(src['provenance'])}


def _merge_mapped_exact(active, requested_count, answers, requirements, questions):
    """Resolve exact ownership per physical level, never by upload order."""
    count = int(requested_count)
    owners, placeholders, orders = {}, {}, []
    for src in active:
        if src.get('floorOrder'):
            orders.append(src['floorOrder'])
        for local_index, original in enumerate(src['geometry'].get('floors', [])):
            index = src.get('floorIndices', list(range(len(src['geometry']['floors']))))[local_index]
            floor = deepcopy(original)
            if len(src['floorIds']) > local_index:
                floor['id'] = src['floorIds'][local_index]
            placeholders.setdefault(index, []).append(floor['id'])
            if floor.get('rooms') or floor.get('openings') or floor.get('walls'):
                owners.setdefault(index, []).append((src, floor))
    chosen, applied, waiting = {}, set(), set()
    for index, entries in sorted(owners.items()):
        if index >= count:
            q = _question('FLOOR_MAPPING', 'Include the floor from this drawing?',
                f'An enabled drawing maps rooms to physical floor {index + 1}, but the home requests {count} floors. Confirm the floor count or explicitly exclude that input.',
                [_choice('edit', 'Review requested floors', 'Keep every original room and confirm the intended home scope.', True, action='edit-plot'),
                 _choice('sources', 'Review selected drawings', 'Explicitly exclude a drawing if it is outside this home.', action='edit-input')],
                affected=[{'floorId': f['id'], 'floorIndex': index} for _, f in entries],
                identity=[count, index, [(s['id'], sha(f)) for s, f in entries]])
            questions.insert(0, q)
            waiting.update(s['id'] for s, _ in entries)
            continue
        groups = {}
        for src, floor in entries:
            groups.setdefault(sha(floor), []).append((src, floor))
        selected = entries[0] if len(groups) == 1 else None
        if selected is None:
            q = _question('LAYOUT_AUTHORITY', 'Which drawing should control this floor?',
                f'Enabled layouts disagree on physical floor {index + 1}. The other floors and every original drawing stay saved.',
                [_choice(s['id'], 'Follow ' + s['id'], 'Use its measured room outlines on this floor.', i == 0, sourceId=s['id'])
                 for i, (s, _) in enumerate(entries)],
                affected=[{'floorId': f['id'], 'floorIndex': index} for _, f in entries],
                identity=[index, [(s['id'], sha(f)) for s, f in entries]])
            selected = next(((s, f) for s, f in entries if s['id'] == answers.get(q['id'])), None)
            if selected is None:
                questions.insert(0, q)
                waiting.update(s['id'] for s, _ in entries)
        if selected:
            chosen[index] = selected[1]
            applied.update(s['id'] for s, f in entries if sha(f) == sha(selected[1]))
        for src, floor in entries:
            selected_here = selected is not None and sha(floor) == sha(selected[1])
            entry = _requirement(src, 'layout-floor-' + str(index), floor['id'],
                'applied' if selected_here else 'reference-only' if selected else 'awaiting clarification',
                'Measured layout at the confirmed physical floor.' if selected_here else
                'Another layout was explicitly selected for this floor; the original stays saved.' if selected else
                'Two enabled drawings claim this physical floor.')
            entry.update(floorIds=[floor['id']], floorIndices=[index])
            requirements.append(entry)
    for entry in requirements:
        if entry['field'] == 'layout' and entry['sourceId'] in {s['id'] for s in active}:
            entry['status'] = ('awaiting clarification' if entry['sourceId'] in waiting else
                               'applied' if entry['sourceId'] in applied else 'reference-only')
            entry['message'] = 'See the per-floor ownership records. Empty placeholders are not measured room layouts.'
    # Deterministic shell identity does not depend on which drawing was uploaded
    # first. Nonempty chosen floors retain their original stable identities.
    plan = deepcopy(sorted(active, key=lambda s: s['id'])[0]['geometry'])
    plan['floors'] = []
    used_ids = {f['id'] for f in chosen.values()}
    for index in range(count):
        if index in chosen:
            plan['floors'].append(chosen[index])
            continue
        possible = sorted({order[index] for order in orders if len(order) > index} | set(placeholders.get(index, [])))
        ident = next((i for i in possible if i not in used_ids), 'floor-' + str(index))
        while ident in used_ids:
            ident += '-empty'
        used_ids.add(ident)
        plan['floors'].append({'id': ident, 'rooms': [], 'walls': [], 'openings': []})
    stairs = {}
    for src in active:
        for stair in src['geometry'].get('stairs', []):
            stairs.setdefault(sha(stair), deepcopy(stair))
    plan['stairs'] = [stairs[key] for key in sorted(stairs)]
    return plan


def resolve_sources(project):
    """Return a legacy compiler payload only from enabled, resolved sources.

    Conflicts are never decided by numeric source priority. An answer is tied to
    both the candidates and their values, so later edits cannot reuse a stale
    decision. Every original source remains in the returned source ledger.
    """
    if not isinstance(project, dict):
        raise DesignError('INPUT_OBJECT', 'Supply a project object.')
    meta = _metadata(project)
    sources = normalize_sources(project)
    answers = meta.get('answers', {})
    if not isinstance(answers, dict):
        raise DesignError('JOURNEY_ANSWERS', 'Saved answers must be an object.')
    requirements, questions, candidates = [], [], {}
    for src in sources:
        state = 'applied' if src['enabled'] else 'excluded'
        for key, value in src['values'].items():
            status = state if key in DEFAULTS else 'unsupported' if src['enabled'] else 'excluded'
            requirements.append(_requirement(src, key, value, status,
                'Excluded by your input choice.' if not src['enabled'] else 'No geometry consumer exists for this field.' if key not in DEFAULTS else ''))
            if src['enabled'] and key in DEFAULTS:
                candidates.setdefault(key, []).append(src)
        if src['kind'] == 'sketch':
            requirements.append(_requirement(src, 'reference', src.get('reference', {}).get('name', src['id']),
                'reference-only' if src['enabled'] else 'excluded',
                'Reference only. Calibrate a known dimension and explicitly trace room outlines before using measured geometry.'))
        reading = src.get('interpretation', {}).get('reading', {})
        for i, phrase in enumerate(reading.get('not_understood', [])):
            requirements.append(_requirement(src, 'unparsed-' + str(i), phrase,
                'unsupported' if src['enabled'] else 'excluded', 'Retained verbatim; the deterministic parser cannot apply this requirement.'))
        for i, assumption in enumerate(reading.get('assumptions', [])):
            if src['enabled']:
                q = _question('TEXT_INTERPRETATION', 'Is this interpretation correct?', assumption,
                    [_choice('confirm', 'Use this interpretation', assumption, True),
                     _choice('edit', 'Edit the description', 'Add explicit units or measurements.', action='edit-input',
                             editor={'kind': 'text', 'sourceId': src['id']})],
                    identity=[src['id'], src.get('text'), assumption])
                if answers.get(q['id']) != 'confirm':
                    questions.append(q)
        if src.get('geometry') is not None:
            requirements.append(_requirement(src, 'layout', src['floorIds'], state,
                'Measured room layout.' if src['enabled'] else 'Original layout retained but excluded by your choice.'))
            if src['kind'] == 'compass':
                for room in src['geometry'].get('rooms', []):
                    status = state
                    if src['enabled'] and not room.get('regions'):
                        status = 'awaiting clarification' if room.get('required', True) else 'excluded'
                    entry = _requirement(src, 'room-' + room['id'], room['kind'], status,
                        'Room identity, type and floor are retained.' if room.get('regions') else
                        'Required room still needs an allocation.' if room.get('required', True) else
                        'Room explicitly marked optional and not allocated; retained in the draft.')
                    entry.update(roomId=room['id'], floorIds=[room['floorId']], fixed=bool(room.get('target', {}).get('locked')))
                    requirements.append(entry)
    resolved = {}
    for key, items in candidates.items():
        distinct = {canonical(src['values'][key]) for src in items}
        selected = items[0]
        if len(distinct) > 1:
            q = _question('SOURCE_CONFLICT', 'Which ' + key.replace('_mm', '').replace('_', ' ') + ' should I use?',
                'Your enabled inputs disagree. The originals stay saved.',
                [_choice(src['id'], str(src['values'][key]) + (' mm' if key.endswith('_mm') else ''),
                         'From ' + src['id'], i == 0, sourceId=src['id']) for i, src in enumerate(items)],
                identity=[key, [(s['id'], s['values'][key]) for s in items]])
            choice = answers.get(q['id'])
            selected = next((s for s in items if s['id'] == choice), None)
            if selected is None:
                questions.append(q)
            for entry in requirements:
                if entry['field'] == key and entry['sourceId'] in {s['id'] for s in items}:
                    same = selected is not None and canonical(entry['value']) == canonical(selected['values'][key])
                    entry.update(status='applied' if same else 'excluded' if selected else 'awaiting clarification',
                                 message='Selected by your saved answer.' if same else 'Another measurement was explicitly selected.' if selected else 'Conflicting enabled measurements need your choice.')
        if selected:
            resolved[key] = selected['values'][key]

    # A newly selected input must not quietly borrow disabled measurements or
    # create a 40 x 60 ft house from application defaults. Existing values are
    # offered by the editable Plot group, so enabling it is an explicit action.
    essential = [key for key in ('width_mm', 'depth_mm', 'storeys', 'road_bearing_deg') if key not in resolved]
    if 'storeys' in essential:
        counts = {s.get('requestedFloorCount', max(s.get('floorIndices', [-1]), default=-1) + 1
                  if 'floorIndices' in s else len(s['geometry'].get('floors', []))) for s in sources
                  if s['enabled'] and s.get('geometry') and s['kind'] in ('compass', 'dxf', 'plan')}
        if len(counts) == 1 and 0 < next(iter(counts)) <= 3:
            resolved['storeys'] = counts.pop()
            essential.remove('storeys')
    # Legacy projects historically omitted orientation and storeys; their
    # deterministic defaults are retained during migration, while new journey
    # envelopes must explicitly supply or confirm these basics.
    if not project.get('designJourney'):
        essential = [key for key in essential if key in ('width_mm', 'depth_mm')]
    if essential:
        q = _question('PLOT_BASICS', 'Confirm the remaining plot basics',
            'Please supply ' + ', '.join(k.replace('_mm', '').replace('_', ' ') for k in essential) + ' in Plot basics or an enabled written input.',
            [_choice('edit', 'Complete plot basics', 'Enable plot dimensions and confirm the road and requested floors.', True,
                     action='edit-plot', editor={'kind': 'plot', 'field': essential[0]}),
             _choice('defaults', 'Use these starting values', ', '.join(k.replace('_mm', '').replace('_', ' ') + ': ' + str(DEFAULTS[k]) + (' mm' if k.endswith('_mm') else '') for k in essential),
                     values={k: DEFAULTS[k] for k in essential})], identity=essential)
        q.update(editor={'kind': 'plot', 'field': essential[0]}, missingFields=list(essential))
        if answers.get(q['id']) == 'defaults':
            resolved.update({k: DEFAULTS[k] for k in essential})
        else:
            questions.append(q)

    active = [s for s in sources if s['enabled'] and s.get('geometry') is not None]
    requested = set(meta.get('enabledInputs', (project.get('editorState') or {}).get('homeInputs', [])))
    pending_layouts = {kind for kind in requested.intersection({'compass', 'dxf'})
                       if not any(s['kind'] == kind and s.get('geometry') is not None for s in sources)}
    if not active and 'bedrooms' not in resolved and not pending_layouts:
        minimum = max(2, resolved.get('storeys', 1))
        q = _question('ROOM_GOALS', 'How many bedrooms should this home have?',
            'Your plot is recorded. Choose the missing essential room goal; the basic programme includes living, dining, kitchen and shared bathroom space.',
            [_choice(str(minimum), f'{minimum} bedrooms', 'Use a basic programme without optional pooja, parking or attached baths.', True),
             _choice(str(minimum + 1), f'{minimum + 1} bedrooms', 'Keep the same basic programme with one more bedroom.'),
             _choice('edit', 'Set my room goals', 'Open the guided home brief for a different programme.', action='edit-survey')],
            identity={'storeys': resolved.get('storeys', 1)})
        q['editor'] = {'kind': 'survey', 'field': 'bedrooms'}
        if answers.get(q['id']) in (str(minimum), str(minimum + 1)):
            resolved.update(bedrooms=int(answers[q['id']]), attached_baths=0, pooja=False, parking=False, eldercare=False)
            source = {'id': 'room-goal-answer', 'kind': 'survey', 'enabled': True, 'units': 'mm', 'floorIds': [],
                      'values': {k: resolved[k] for k in ('bedrooms', 'attached_baths', 'pooja', 'parking', 'eldercare')},
                      'interpretation': {'method': 'explicit guided answer'}, 'provenance': {'questionId': q['id']}}
            sources.append(source)
            requirements.extend(_requirement(source, k, v) for k, v in source['values'].items())
        else:
            questions.append(q)
    # Multiple exact inputs can contribute disjoint floors. Coincident or
    # overlapping ownership must be resolved explicitly before unioning them.
    exact = all(s['kind'] in ('dxf', 'plan') for s in active)
    mapped_plan = None
    if active and exact and any('floorIndices' in s for s in active):
        inferred_count = max((max(s.get('floorIndices', list(range(len(s['geometry'].get('floors', []))))), default=-1) + 1
                              for s in active), default=1)
        mapped_plan = _merge_mapped_exact(active, resolved.get('storeys', inferred_count), answers, requirements, questions)
    elif len(active) > 1:
        occupied = set()
        disjoint = exact
        for src in active:
            ids = set(src['floorIds'] or [f['id'] for f in src['geometry'].get('floors', [])])
            disjoint = disjoint and not (ids & occupied)
            occupied |= ids
        if not disjoint:
            q = _question('LAYOUT_AUTHORITY', 'Which layout should control these rooms?',
                'More than one enabled layout owns the same home area. Keep one canonical layout and retain the other as a reference.',
                [_choice(s['id'], 'Follow ' + s['id'], 'Preserve its room positions and measured outlines.', i == 0, sourceId=s['id']) for i, s in enumerate(active)],
                identity=[(s['id'], s['floorIds'], sha(s['geometry'])) for s in active])
            choice = answers.get(q['id'])
            chosen = next((s for s in active if s['id'] == choice), None)
            if chosen:
                active = [chosen]
            else:
                questions.insert(0, q)
            for entry in requirements:
                if (entry['field'] == 'layout' or entry.get('roomId')) and entry['status'] != 'excluded':
                    if not chosen:
                        entry['status'] = 'awaiting clarification'
                    elif entry['sourceId'] != chosen['id']:
                        entry.update(status='reference-only', message='You selected a different authoritative layout; this original is retained as a reference.')

    # Authored Compass rooms are an explicit programme even when the separate
    # survey input is excluded. Do not leak the legacy three-bedroom default
    # into a saved checklist with two drawn bedrooms.
    if 'bedrooms' not in resolved and len(active) == 1 and active[0]['kind'] == 'compass':
        source = active[0]
        floors = source['geometry'].get('floors', [])
        requested_ids = {f['id'] for f in floors[:resolved.get('storeys', len(floors))]}
        count = sum(r.get('kind') == 'bedroom' and r.get('floorId') in requested_ids for r in source['geometry'].get('rooms', []))
        if meta.get('scopeConfirmed') and type(meta.get('scope')) is int:
            floors = floors[:meta['scope']]
        included = {f['id'] for f in floors}
        if count:
            resolved['bedrooms'] = count
            in_scope = sum(r.get('kind') == 'bedroom' and r.get('floorId') in included for r in source['geometry'].get('rooms', []))
            requirements.append(_requirement(source, 'bedrooms', in_scope,
                message='Inferred from the enabled Compass room programme within the explicitly selected floor scope.'))

    # A clean compiler envelope contains no hidden sample planning metadata.
    legacy = {k: deepcopy(project[k]) for k in ('schema', 'draftRevision', 'notes', 'roomEdits', 'furnitureLayout') if k in project}
    legacy['schema'] = 'floorforge.project/0.5'
    legacy['brief'] = {k: deepcopy(v) for k, v in (project.get('brief') or {}).items() if k in COSMETIC_FIELDS}
    legacy['brief'].update(resolved)
    # Description measurements have been explicitly resolved above; only its
    # surviving spatial hints are passed to the geometry consumer below.
    legacy['sources'] = []
    if active:
        first = active[0]
        if first['kind'] == 'compass':
            legacy['compass'] = deepcopy(first['geometry'])
        elif first['kind'] == 'grid':
            legacy['grid'] = deepcopy(first['geometry'])
        elif first['kind'] in ('dxf', 'plan'):
            plan = mapped_plan if mapped_plan is not None else deepcopy(first['geometry'])
            if mapped_plan is None and len(active) > 1:
                plan['floors'] = []
                plan['stairs'] = []
                for src in active:
                    for i, fl in enumerate(src['geometry'].get('floors', [])):
                        floor = deepcopy(fl)
                        if len(src['floorIds']) > i:
                            floor['id'] = src['floorIds'][i]
                        plan['floors'].append(floor)
                    plan['stairs'].extend(deepcopy(src['geometry'].get('stairs', [])))
            # The existing kernel has one wall-thickness setting per home.
            # Combining independently measured floors must not silently take
            # that value from whichever file happened to supply the shell.
            contributing = {entry['sourceId'] for entry in requirements
                            if entry['field'] == 'layout' and entry['status'] == 'applied'}
            measured = [s for s in active if s['id'] in contributing]
            thicknesses = {s['geometry'].get('wallThickness', 150) for s in measured}
            selected_wall = measured[0] if measured else None
            if len(thicknesses) > 1:
                q = _question('SOURCE_CONFLICT', 'Which wall thickness should this home use?',
                    'The measured drawings specify different wall thicknesses. The current geometry engine uses one thickness throughout the coordinated home.',
                    [_choice(s['id'], str(s['geometry'].get('wallThickness', 150)) + ' mm',
                             'Measured in ' + s['id'], i == 0, sourceId=s['id']) for i, s in enumerate(measured)],
                    identity=['wallThickness', [(s['id'], s['geometry'].get('wallThickness', 150)) for s in measured]])
                selected_wall = next((s for s in measured if s['id'] == answers.get(q['id'])), None)
                if selected_wall is None:
                    questions.append(q)
            if selected_wall:
                plan['wallThickness'] = selected_wall['geometry'].get('wallThickness', 150)
            for source in measured:
                value = source['geometry'].get('wallThickness', 150)
                status = ('awaiting clarification' if selected_wall is None else
                          'applied' if value == plan['wallThickness'] else 'excluded')
                requirements.append(_requirement(source, 'wall_thickness_mm', value, status,
                    'The coordinated home uses your selected measured wall thickness.' if status == 'applied' else
                    'Another wall thickness was explicitly selected.' if status == 'excluded' else
                    'Conflicting measured wall allowances need a choice.'))
            legacy['customPlan'] = plan
    # Enabled layout source with no supplied content cannot masquerade as
    # applied. Request the missing input while retaining all other work.
    for kind in ('compass', 'dxf'):
        if kind in requested and not any(s['kind'] == kind and s.get('geometry') for s in sources):
            q = _question('MISSING_INPUT', 'Add your ' + ('Compass rooms' if kind == 'compass' else 'DXF drawing'),
                'This input is enabled but no layout is available yet.',
                [_choice('add', 'Add this input', 'Open the editor or importer.', True, action='edit-' + kind),
                 _choice('exclude', 'Continue without it', 'Exclude this input explicitly.', action='exclude-' + kind)], identity=kind)
            if answers.get(q['id']) != 'exclude':
                questions.append(q)
    return {'project': legacy, 'sources': sources, 'requirements': requirements, 'questions': questions,
            'question': questions[0] if questions else None, 'answers': deepcopy(answers), 'meta': meta,
            'activeSourceIds': [s['id'] for s in active]}


def _geometry_question(issues, project=None):
    from .journey_diagnostics import enrich_issues, first_issue, contextualize_question
    project = project or {}
    enriched = enrich_issues(issues, project)
    problem = first_issue(enriched)
    kind = problem['editor']['kind']
    name, floor = problem.get('name', 'This part of the plan'), problem.get('floorName')
    title = name + (' · ' + floor if floor else '')
    choices = [_choice('edit', 'Open ' + (floor or 'the affected layout'),
                       'The editor will show the issue and the next steps. Your draft stays saved.', True,
                       action='edit-layout', editor=problem['editor'])]
    if kind == 'plot':
        title = 'Check this plot measurement before arranging rooms'
        choices = [_choice('edit', 'Review plot dimensions and setbacks', problem['message'], True,
                           action='edit-plot', editor={'kind': 'plot'})]
    elif kind == 'survey':
        title = 'Review the room goals and available space'
        choices = [_choice('edit', 'Review room goals', 'Keep each requested room unless you explicitly revise it.', True,
                           action='edit-survey', editor={'kind': 'survey'}),
                   _choice('plot', 'Review plot dimensions and setbacks', 'Check the buildable area and units.',
                           action='edit-plot', editor={'kind': 'plot'})]
    elif kind == 'inputs':
        choices = [_choice('edit', 'Review the selected input', problem['message'], True,
                           action='edit-input', editor={'kind': 'inputs'})]
    elif problem['code'] == 'EMPTY_FLOOR':
        title = (floor or 'This requested floor') + ' still needs rooms'
        if kind == 'compass':
            choices.append(_choice('scope', 'Choose a smaller preview scope',
                                   'Only include fewer floors after an explicit scope choice.', action='choose-scope'))
    elif problem['code'] in ('UNPLACED', 'REQUIRED_ROOM_UNPLACED'):
        title = 'Place ' + name + (' on ' + floor if floor else '')
    q = _question(problem['code'], title, problem['message'], choices, identity=issues)
    return contextualize_question(q, enriched, project)


def _apply_appearance(project, meta):
    from .journey_components import normalize_components
    chosen = meta.get('appearance', {})
    if isinstance(chosen, str):
        chosen = {'preset': chosen}
    if not isinstance(chosen, dict):
        raise DesignError('APPEARANCE', 'Choose an appearance preset.')
    preset = chosen.get('preset', 'warm-natural')
    if preset not in PRESETS:
        raise DesignError('APPEARANCE', 'Choose one of the three compatible finish presets.')
    recipe = PRESETS[preset]
    result = deepcopy(project)
    # All custom journeys construct presentation components with one fixed
    # recipe. The legacy renderer branches on these values for porch, garden
    # and furniture geometry, even under finish_only. A preset is therefore a
    # later material-library overlay, never a recipe switch in that renderer.
    result.setdefault('brief', {}).update(style='warm', exterior_theme='warm_modern_minimal',
                                          interior_theme='bright_natural')
    result['brief'].update(change_policy='finish_only', interior_layout_locked=True)
    appearance = {'preset': preset, 'schema': 'myverandah.appearance/1', 'geometryEffect': 'none',
                  'materials': {k: recipe[k] for k in ('style', 'exterior_theme', 'interior_theme')},
                  'components': normalize_components(chosen)}
    appearance['appearanceHash'] = sha(appearance)
    return result, appearance


def canonical_model(building, *, pins=None):
    """Measured, versioned projection shared by approval and scene checks."""
    room_keys = {'id', 'name', 'kind', 'floor', 'polygon', 'clear', 'holes', 'area_m2',
                 'mechanicalVentilation', 'drain', 'serviceOnly', 'glassCover'}
    geometry = {'schema': MODEL_SCHEMA, 'units': 'mm', 'up': 'Z', 'tolerance': TOLERANCE,
                'orientation': 'Road at local -Y; road bearing is true azimuth.',
                'site': {k: building['brief'][k] for k in sorted(PLOT_FIELDS) if k in building['brief']},
                'boundaries': {k: deepcopy(building[k]) for k in ('plot', 'footprint', 'footprint_holes') if k in building},
                'floors': deepcopy(building['floors']), 'rooms': [{k: deepcopy(v) for k, v in r.items() if k in room_keys} for r in building['spaces']],
                'pins': deepcopy(pins or {})}
    for key in ('walls', 'openings', 'stairs', 'floor_plates', 'roofs', 'guards', 'entrance_steps'):
        geometry[key] = deepcopy(building.get(key, []))
    geometry['roofAccess'] = deepcopy(building.get('rooftop'))
    geometry['relationships'] = [{'id': o['id'], 'kind': o['kind'], 'connects': sorted(o.get('connects', [])), 'floor': o['floor']}
                                 for o in building['openings']]
    return geometry


def floor_hashes(model):
    """Coupled floor hashes include every lower/upper structural envelope.

    Conservative cross-floor invalidation prevents a landing, void or support
    edit from leaving another floor approved against obsolete relationships.
    Cosmetic changes and revision counters do not enter these identities.
    """
    shared = {k: model[k] for k in ('schema', 'site', 'boundaries', 'stairs', 'floor_plates', 'roofs', 'roofAccess', 'pins', 'tolerance')}
    return {fl['id']: sha({'shared': shared, 'floor': fl,
                          **{key: [v for v in model[key] if v.get('floor') == fl['index']]
                             for key in ('rooms', 'walls', 'openings', 'guards', 'relationships')}})
            for fl in model['floors']}


def plan_sheets(building):
    """Reuse floor drawing primitives without constructing a single mesh."""
    from .drawings import AREA, plan_elements, principal_rect
    from shapely.geometry import Polygon
    sheets = []
    names = ['Ground floor', 'First floor', 'Second floor']
    for floor in building['floors']:
        index = floor['index']
        elements, bounds = plan_elements(building, {'furniture': []}, index)
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        scale = next((s for s in (50, 75, 100, 125, 150, 200, 250, 300, 500, 750, 1000)
                      if width / s <= AREA[0] and height / s <= AREA[1]), 1000)
        table = [['SPACE', 'CLEAR SIZE m', 'AREA m2']]
        for room in (r for r in building['spaces'] if r['floor'] == index):
            x, y, xx, yy = principal_rect(Polygon(room['clear']))
            table.append([room['name'], f'{(xx-x)/1000:.3f} x {(yy-y)/1000:.3f}', f'{room["area_m2"]:.2f}'])
        sheets.append({'id': f'A-10{index+1}', 'floorId': floor['id'], 'title': names[index] + ' — review for approval',
                       'planHash': building['planHash'], 'elements': elements, 'bounds': bounds, 'scale': scale,
                       'notes': ['All dimensions in millimetres. Room dimensions are clear space between wall faces.',
                                 'Road / front is local -Y. North arrow shows the selected true bearing.',
                                 'Doors, windows, stairs and slab openings come from the same measured geometry.',
                                 'Furniture and presentation meshes are generated only after whole-home approval.',
                                 'Preliminary design: professional review is required before construction.'],
                       'table': table, 'schedule': [], 'page_mm': [420, 297]})
    return sheets


def prepare(project):
    """Prepare every requested floor for 2D review; never generate meshes."""
    from .intent import fuse
    from .layout import generate_layout
    from .review import validate, reports
    from .drawings import svg_sheet
    resolved = resolve_sources(project)
    result = {k: deepcopy(resolved[k]) for k in ('sources', 'requirements', 'questions', 'question', 'answers')}
    result.update(valid=False, schema=SCHEMA, issues=[], floors=[], appearanceOptions=appearance_catalogue())
    if resolved['questions']:
        return result
    payload, appearance = _apply_appearance(resolved['project'], resolved['meta'])
    result['appearance'] = appearance
    for entry in result['requirements']:
        if entry['field'] in ('style', 'exterior_theme', 'interior_theme', 'change_policy') and entry['status'] == 'applied':
            applied_value = appearance['materials'].get(entry['field'], payload['brief'].get(entry['field']))
            if entry['value'] != applied_value:
                entry.update(status='reference-only', message='The selected compatible appearance preset controls this finish choice.')
    try:
        # Resolve through the existing field validator before interpreting maps.
        if payload.get('compass') is not None:
            from .compass_adapter import proposal
            from .compass_input import ADAPTER
            draft = payload['compass']
            scope = resolved['meta'].get('scope')
            requested = payload['brief'].get('storeys', DEFAULTS['storeys'])
            if scope is not None and scope != requested:
                if resolved['meta'].get('scopeConfirmed') is not True:
                    raise DesignError('SCOPE_CONFIRMATION', 'Explicitly confirm which floors to exclude before partial generation.')
            included = {f['id'] for f in draft.get('floors', [])[:scope or requested]}
            unplaced = [r for r in draft.get('rooms', []) if r.get('required', True) and not r.get('regions') and r['floorId'] in included]
            if unplaced:
                raise DesignError('REQUIRED_ROOM_UNPLACED', 'Place every required room before reviewing this home.',
                                  {'errors': [{'code': 'REQUIRED_ROOM_UNPLACED', 'roomId': r['id'], 'floorId': r['floorId'],
                                               'message': 'Place ' + r['name'] + ', or explicitly make this room optional.'} for r in unplaced]})
            check = proposal(payload, draft, scope)
            source = next(s for s in resolved['sources'] if s['id'] in resolved['activeSourceIds'] and s['kind'] == 'compass')
            statuses = {'applied': 'applied', 'off': 'excluded', 'unapplied': 'excluded',
                        'note only': 'reference-only', 'preference checked': 'reference-only'}
            for effect in check.get('effects', []):
                result['requirements'].append(_requirement(source, effect['source'], effect.get('message', ''),
                    statuses.get(effect.get('status'), 'unsupported'), effect.get('message', '')))
            if scope is not None and scope < requested:
                for entry in result['requirements']:
                    if entry.get('roomId') and entry['floorIds'][0] not in included:
                        entry.update(status='excluded', message='You explicitly excluded this floor from the generated scope; its room remains saved.')
            if not check['valid']:
                from .compass_repair import search, guided_question
                repair_project = {**payload, 'designJourney': resolved['meta']}
                repair = search(repair_project, draft, check)
                from .journey_diagnostics import enrich_issues
                result['issues'] = enrich_issues(check['issues'], payload, check.get('sizes', []))
                result.update({k: repair[k] for k in ('alternatives', 'search', 'graph') if k in repair})
                result['question'] = guided_question(draft, {**check, **repair}) or _geometry_question(check['issues'], payload)
                result['questions'] = [result['question']]
                return result
            payload['compassScope'] = check['scope']
            payload['compassAcceptance'] = {'sourceHash': check['sourceHash'], 'adapterVersion': ADAPTER}
        intent = fuse(payload)
        # Preserve spatial prose in the automatic planner. Authored layouts
        # receive a separately validated comparison, never an ignored hint.
        from .intent import _resolve_text_spatial
        hints = []
        for src in resolved['sources']:
            if src['enabled']:
                hints += [{**h, 'sourceId': src['id']} for h in _resolve_text_spatial(
                    src.get('interpretation', {}).get('spatialHints', []), intent['values']['road_bearing_deg'])]
        if hints and intent.get('customPlan') is None:
            intent['placement_hints'] = [{k: v for k, v in h.items() if k != 'sourceId'} for h in hints]
            intent['planHash'] = sha({'base': intent['planHash'], 'placement_hints': intent['placement_hints']})
            # Persist only understood placement phrases so regeneration uses
            # exactly this consumer, without resurrecting resolved measurements.
            payload['text'] = '. '.join(h['phrase'] for h in hints)
            for hint in hints:
                src = next(s for s in resolved['sources'] if s['id'] == hint['sourceId'])
                result['requirements'].append(_requirement(src, 'position-' + sha(hint)[:10], hint['phrase'],
                    'applied', 'This relative room position is a validated planner constraint.'))
        building = generate_layout(intent)
        review = validate(building)
        from .journey_components import catalogue
        appearance['componentOptions'] = catalogue(building)
        expected = payload['brief'].get('storeys', DEFAULTS['storeys'])
        explicit_scope = resolved['meta'].get('scope') if resolved['meta'].get('scopeConfirmed') is True else expected
        if building['storeys'] != explicit_scope:
            raise DesignError('REQUESTED_FLOORS', 'Every requested floor must remain included unless you explicitly choose a partial scope.')
        _audit_authored_requirements(resolved, payload, building, hints, result)
        if result['questions']:
            result['question'] = result['questions'][0]
            return result
        model = canonical_model(building, pins=resolved['meta'].get('pins'))
        geometry_hash = sha(model)
        hashes = floor_hashes(model)
        sheets = plan_sheets(building)
        floors = [{'id': fl['id'], 'name': ['Ground floor', 'First floor', 'Second floor'][fl['index']],
                   'index': fl['index'], 'geometryHash': hashes[fl['id']], 'dependsOn': [x['id'] for x in model['floors']],
                   'roomCount': sum(r['floor'] == fl['index'] for r in model['rooms']),
                   'svg': svg_sheet(sheets[fl['index']], building), 'scale': sheets[fl['index']]['scale']}
                  for fl in model['floors']]
        result.update(valid=True, geometryHash=geometry_hash, canonical=model, floors=floors, building=building,
                      sheets=sheets, report=reports(building, review), preparedProject=payload,
                      requestedFloorCount=expected, includedFloorCount=len(floors),
                      geometryRevision=project.get('draftRevision', 0))
        return result
    except DesignError as exc:
        from .journey_diagnostics import enrich_issues, error_issues
        result['issues'] = enrich_issues(error_issues(exc), payload)
        result['question'] = _geometry_question(result['issues'], payload)
        result['questions'] = [result['question']]
        return result


def _audit_authored_requirements(resolved, payload, building, hints, result):
    """Account for authored-layout requirements that old fusion only noted."""
    if not payload.get('customPlan') and not payload.get('compass'):
        return
    from shapely.geometry import Polygon
    kinds = [r['kind'] for r in building['spaces']]
    tests = {'bedrooms': lambda v: kinds.count('bedroom') == v,
             'pooja': lambda v: ('pooja' in kinds) == v,
             'attached_baths': lambda v: None, 'eldercare': lambda v: None,
             'open_kitchen': lambda v: None, 'variant': lambda v: None, 'vastu': lambda v: None,
             'soil': lambda v: None}
    by_id = {s['id']: s for s in resolved['sources']}
    for entry in result['requirements']:
        if entry['status'] != 'applied' or entry['field'] not in tests:
            continue
        matched = tests[entry['field']](entry['value'])
        if matched is None:
            entry.update(status='reference-only', message='Preserved as a preference; this option does not modify an authored room layout.')
        elif not matched:
            q = _question('ROOM_PROGRAMME', 'Keep the drawn rooms or update the room goal?',
                'Your ' + entry['label'] + ' request does not match the authored plan.',
                [_choice('layout', 'Keep the drawn rooms', 'Explicitly exclude this conflicting room-count preference.', True),
                 _choice('edit', 'Add or edit rooms', 'Return to your map and preserve the requested room goal.', action='edit-layout')],
                identity=[entry['id'], entry['value'], [(r['id'], r['kind']) for r in building['spaces']]])
            if resolved['answers'].get(q['id']) == 'layout':
                entry.update(status='excluded', message='You explicitly chose the authored room programme.')
            else:
                entry['status'] = 'awaiting clarification'
                result['questions'].append(q)
    width = building['brief']['width_mm'] - building['brief']['left_mm'] - building['brief']['right_mm']
    depth = building['brief']['depth_mm'] - building['brief']['front_mm'] - building['brief']['rear_mm']
    for hint in hints:
        src = by_id[hint['sourceId']]
        label = hint['label']
        kind = 'bedroom' if 'bedroom' in label else 'bathroom' if 'bathroom' in label else label
        rooms = [r for r in building['spaces'] if r['id'] == label or r['kind'] == kind]
        matched = False
        if len(rooms) == 1:
            centre = Polygon(rooms[0]['polygon']).centroid
            matched = math.hypot(centre.x / width - hint['x'], centre.y / depth - hint['y']) <= .28
        entry = _requirement(src, 'position-' + sha(hint)[:10], hint['phrase'], 'applied' if matched else 'awaiting clarification',
                             'Position verified against the authored geometry.' if matched else 'Written position and room layout need clarification.')
        result['requirements'].append(entry)
        if not matched:
            q = _question('ROOM_POSITION', 'Which room position should I follow?',
                hint['phrase'] + ' does not unambiguously match the drawn layout.',
                [_choice('layout', 'Keep the drawn position', 'Retain the text as a reference.', True),
                 _choice('edit', 'Edit the map', 'Move or identify the requested room explicitly.', action='edit-layout')],
                affected=[{'roomId': r['id'], 'floor': r['floor']} for r in rooms],
                identity=[hint, [(r['id'], r['polygon']) for r in rooms]])
            if resolved['answers'].get(q['id']) == 'layout':
                entry.update(status='reference-only', message='You explicitly retained the drawn position.')
            else:
                result['questions'].append(q)


def _signature(record, secret):
    if isinstance(secret, str):
        secret = secret.encode('utf8')
    if not isinstance(secret, bytes) or len(secret) < 16:
        raise DesignError('APPROVAL_KEY', 'Approval signing needs a server-held key of at least 16 bytes.')
    return hmac.new(secret, canonical(record), hashlib.sha256).hexdigest()


def _valid_signature(record, secret):
    if not isinstance(record, dict) or not isinstance(record.get('signature'), str):
        return False
    unsigned = {k: v for k, v in record.items() if k != 'signature'}
    return hmac.compare_digest(record['signature'], _signature(unsigned, secret))


def approve_floor(preparation, floorId, geometryHash, secret):
    if not preparation.get('valid'):
        raise DesignError('APPROVAL_INVALID', 'Resolve the plan before approving it.')
    floor = next((f for f in preparation['floors'] if f['id'] == floorId), None)
    if floor is None or geometryHash != floor['geometryHash']:
        raise DesignError('APPROVAL_STALE', 'This floor changed. Review its current drawing before approving.')
    record = {'schema': 'myverandah.floor-approval/1', 'floorId': floorId,
              'geometryHash': geometryHash, 'homeGeometryHash': preparation['geometryHash']}
    return {**record, 'signature': _signature(record, secret)}


def reusable_floor_approvals(preparation, approvals, secret):
    """Retain only authentic reviews of the current dependency-aware floors.

    The signed homeGeometryHash records the original review's provenance. An
    independent floor edit need not change a different floor's review: its hash
    already includes shared stairs, support envelopes, voids and pinned rules.
    The current coordinated home still requires a new explicit confirmation.
    """
    if not preparation.get('valid'):
        return {}
    if isinstance(approvals, dict):
        approvals = list(approvals.values())
    if not isinstance(approvals, list):
        return {}
    current = {floor['id']: floor['geometryHash'] for floor in preparation['floors']}
    return {record['floorId']: deepcopy(record) for record in approvals
            if isinstance(record, dict)
            and record.get('schema') == 'myverandah.floor-approval/1'
            and isinstance(record.get('floorId'), str)
            and record['floorId'] in current
            and record.get('geometryHash') == current[record['floorId']]
            and _valid_signature(record, secret)}


def confirm_home(preparation, approvals, geometryHash, secret):
    if not preparation.get('valid') or geometryHash != preparation.get('geometryHash'):
        raise DesignError('APPROVAL_STALE', 'Review the current coordinated home before confirming.')
    if isinstance(approvals, dict):
        approvals = list(approvals.values())
    if not isinstance(approvals, list):
        raise DesignError('APPROVAL_REQUIRED', 'Approve every requested floor first.')
    reusable = reusable_floor_approvals(preparation, approvals, secret)
    signed = []
    for floor in preparation['floors']:
        if floor['id'] not in reusable:
            raise DesignError('APPROVAL_REQUIRED', 'Approve the current drawing for ' + floor['name'] + ' first.')
        signed.append({'floorId': floor['id'], 'geometryHash': floor['geometryHash']})
    record = {'schema': 'myverandah.home-approval/1', 'geometryHash': geometryHash, 'floors': signed}
    return {**record, 'signature': _signature(record, secret)}


def verify_approval(preparation, certificate, secret):
    expected = [{'floorId': f['id'], 'geometryHash': f['geometryHash']} for f in preparation.get('floors', [])]
    if (not preparation.get('valid') or not _valid_signature(certificate, secret)
            or certificate.get('schema') != 'myverandah.home-approval/1'
            or certificate.get('geometryHash') != preparation.get('geometryHash')
            or certificate.get('floors') != expected):
        raise DesignError('APPROVAL_REQUIRED', 'Approve every current 2D floor and confirm the coordinated home before generating 3D.')
    return True


def editing_project(original, target=None):
    """Adapt a journey to an existing proposal tool without approving geometry.

    This deliberately stops before layout validation: invalid, incomplete exact
    drafts must remain repairable. Source conflicts still require a decision.
    The returned payload is disposable; callers retain the original project.
    """
    if original.get('designJourney') is None:
        return deepcopy(original)
    resolved = resolve_sources(original)
    questions = [q for q in resolved['questions'] if not (target == 'board' and q['code'] == 'ROOM_GOALS')]
    if questions:
        raise DesignError('DESIGN_QUESTION', 'Resolve the selected input question before using this proposal tool.',
                          {'question': questions[0], 'questions': questions, 'requirements': resolved['requirements'],
                           'draftPreserved': True})
    payload, _ = _apply_appearance(resolved['project'], resolved['meta'])
    if target == 'exact' and payload.get('compass') is not None:
        raise DesignError('JOURNEY_EDITOR_AUTHORITY', 'Compass is the selected room layout. Use its tools, or explicitly select the exact layout before editing it.')
    if target == 'exact' and payload.get('customPlan') is None:
        raise DesignError('CUSTOM_PLAN_REQUIRED', 'Enable and select the exact room layout before requesting an edit proposal. Excluded drawings remain saved.')
    if target == 'compass':
        if payload.get('compass') is None:
            raise DesignError('SOURCE_EXCLUDED', 'Enable the Compass input before compiling its draft. Your allocations remain saved.')
        for key in ('compass', 'compassScope', 'compassAcceptance', 'customPlan', 'grid', 'roomEdits', 'furnitureLayout'):
            payload.pop(key, None)
        return payload
    if payload.get('compass') is not None:
        # A brief/placement review may inspect a validated Compass conversion;
        # it must not become the saved authoritative input or a 3D bypass.
        from .compass_adapter import proposal
        check = proposal(payload, payload['compass'], resolved['meta'].get('scope'))
        if not check['valid']:
            raise DesignError('DESIGN_QUESTION', 'Resolve the Compass layout before using this advanced proposal tool.',
                              {'question': _geometry_question(check['issues']), 'errors': check['issues'], 'draftPreserved': True})
        payload['customPlan'] = check['customPlan']
        payload['brief'].update(check['values'])
        for key in ('compass', 'compassScope', 'compassAcceptance'):
            payload.pop(key, None)
    return payload


def editing_result(original, result, compiled=None):
    """Guard legacy proposals and reattach source/answer state to candidates.

    No original approval or editable source is mutated. A proposal's portable
    candidate clears approvals and must pass the ordinary journey on Apply.
    """
    if original.get('designJourney') is None or not isinstance(result, dict):
        return result
    returned = deepcopy(result)
    ai_candidate = isinstance(result.get('candidate_project'), dict) and any(
        s.get('id') == 'ai-proposal' for s in result['candidate_project'].get('sources', []))
    returned['designJourney'] = deepcopy(original['designJourney'])
    returned['draftPreserved'] = True
    base = compiled if compiled is not None else editing_project(original)
    baseline = base.get('customPlan') or {}
    base_floors = baseline.get('floors', [])
    before = {r['id']: (f['id'], r) for f in base_floors for r in f['rooms']}
    pins = original['designJourney'].get('pins', {})
    position_pins, dimension_pins = set(pins.get('positions', [])), set(pins.get('dimensions', []))
    compass = original.get('compass') or (original.get('editorState') or {}).get('compassDraft') or {}
    dimension_pins.update(r['id'] for r in compass.get('rooms', []) if r.get('target', {}).get('locked'))

    def errors_for(plan):
        if not isinstance(plan, dict):
            return []
        problems = []
        expected = base.get('brief', {}).get('storeys', len(base_floors) or DEFAULTS['storeys'])
        if len(plan.get('floors', [])) != expected:
            problems.append({'code': 'REQUESTED_FLOORS', 'message': 'This tool cannot change the requested floor count. Choose scope explicitly in the home journey.'})
        after = {r['id']: (f['id'], r) for f in plan.get('floors', []) for r in f['rooms']}
        from shapely.geometry import Polygon
        for ident, (floor_id, old) in before.items():
            new = after.get(ident)
            if new is None or new[0] != floor_id or new[1]['kind'] != old['kind']:
                problems.append({'code': 'REQUIRED_ROOM_CHANGED', 'roomId': ident, 'message': 'Keep this room identity, type and assigned floor. Remove or reassign rooms only through an explicit editor action.'})
                continue
            a, b = Polygon(old['polygon']), Polygon(new[1]['polygon'])
            if ident in position_pins and not a.equals_exact(b, TOLERANCE['comparison_mm'], normalize=True):
                problems.append({'code': 'PINNED_POSITION', 'roomId': ident, 'message': 'This proposal changes a pinned room position or boundary. Keep the pin or explicitly edit it first.'})
            if ident in dimension_pins:
                aw, ad = a.bounds[2] - a.bounds[0], a.bounds[3] - a.bounds[1]
                bw, bd = b.bounds[2] - b.bounds[0], b.bounds[3] - b.bounds[1]
                if abs(aw-bw) > TOLERANCE['comparison_mm'] or abs(ad-bd) > TOLERANCE['comparison_mm']:
                    problems.append({'code': 'PINNED_DIMENSION', 'roomId': ident, 'message': 'This proposal changes an exact pinned dimension. Keep the dimension or explicitly edit its pin first.'})
        return problems

    def candidate(plan=None, source_patch=None):
        value = deepcopy(original)
        if plan is not None:
            value['customPlan'] = deepcopy(plan)
            value.setdefault('editorState', {})['customPlan'] = deepcopy(plan)
        if source_patch is not None:
            # Optional AI patches remain proposals layered over originals, so
            # normal source conflicts are questioned again when applied.
            proposal_sources = [s for s in source_patch.get('sources', []) if s.get('id') == 'ai-proposal']
            value['sources'] = [s for s in value.get('sources', []) if s.get('id') != 'ai-proposal'] + deepcopy(proposal_sources)
        journey = value['designJourney']
        journey['approvals'] = {}
        journey.pop('confirmation', None)
        journey.pop('preparationId', None)
        journey.pop('geometryHash', None)
        return value

    if isinstance(returned.get('alternatives'), list):
        accepted, rejected = [], []
        for option in returned['alternatives']:
            problems = errors_for(option.get('customPlan'))
            if problems:
                rejected.extend(problems)
            else:
                if option.get('customPlan') is not None:
                    option['candidate_project'] = candidate(option['customPlan'])
                accepted.append(option)
        returned['alternatives'] = accepted
        if rejected:
            returned['protectedChanges'] = rejected
            if not accepted:
                returned.update(valid=False, applied=False, errors=rejected,
                                message='No offered alternative preserves the protected rooms and floors. Your draft is unchanged.')
    proposed_plan = returned.get('customPlan')
    if isinstance(returned.get('candidate_project'), dict):
        proposed_plan = returned['candidate_project'].get('customPlan', proposed_plan)
    problems = errors_for(proposed_plan)
    if problems:
        returned.pop('candidate_project', None)
        if baseline:
            returned['customPlan'] = deepcopy(baseline)
        returned.update(valid=False, applied=False, changes=[], errors=problems,
                        message='This proposal would change a protected requirement. Your editable draft and approvals are retained.')
    elif proposed_plan is not None:
        returned['candidate_project'] = candidate(proposed_plan, returned.get('candidate_project'))
    elif isinstance(returned.get('candidate_project'), dict):
        returned['candidate_project'] = candidate(source_patch=returned['candidate_project'])
    if ai_candidate and returned.get('candidate_project') is not None:
        checked = prepare(returned['candidate_project'])
        returned['journeyValidation'] = {k: checked.get(k) for k in ('valid', 'question', 'questions', 'issues', 'requirements', 'geometryHash')}
        requested = {k for s in result['candidate_project'].get('sources', []) if s.get('id') == 'ai-proposal' for k in s.get('values', {})}
        applied = {e['field'] for e in checked.get('requirements', []) if e['sourceId'] == 'loaded-ai-proposal' and e['status'] == 'applied'}
        complete = checked.get('valid', False) and requested <= applied
        returned.update(valid=bool(complete), applied=False,
                        validation='geometry-checked-proposal' if complete else 'awaiting journey review',
                        questions=checked.get('questions', []), question=checked.get('question'))
        if not complete:
            returned['message'] = 'The suggested values still need input clarification or activation. The original project is unchanged; apply only to review those decisions.'
    return returned
