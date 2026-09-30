"""An explicit account of which inputs control a generation and which cannot be applied."""
from .model import canonical

# These switches arrange the automatic programme; they cannot rewrite an authored plan.
CUSTOM_PROGRAMME = {'attached_baths', 'pooja', 'open_kitchen', 'variant', 'eldercare'}


def audit_inputs(payload, intent):
    entries = []
    custom = intent.get('customPlan') is not None
    for source in intent['sources']:
        if source['kind'] in ('defaults', 'derived'):
            continue
        applied, overridden, authored = [], [], []
        enabled = source.get('enabled', True)
        for key, value in source.get('values', {}).items():
            if not enabled:
                continue
            choice = intent['provenance'][key]
            if custom and key in CUSTOM_PROGRAMME:
                authored.append(key)
            elif source['id'] in choice['selected'] or canonical(value) == canonical(choice['value']):
                applied.append(key)
            else:
                overridden.append({'field': key, 'requested': value, 'resolved': choice['value'], 'by': choice['selected']})
        entries.append({'source': source['id'], 'status': 'off' if not enabled else 'review' if overridden or authored else 'applied' if applied else 'parsed' if source['id'] == 'description' and intent.get('text_reading') else 'reference',
                        'applied': applied, 'overridden': overridden, 'authored': authored})
    for key, label in (('roomEdits', 'Room positions'), ('furnitureLayout', 'Furniture positions')):
        if intent.get(key):
            entries.append({'source': key, 'status': 'applied', 'message': f'{label}: {len(intent[key])} explicit edits; conflicts block generation.'})
    if custom:
        entries.append({'source': 'custom-plan', 'status': 'applied', 'message': 'Exact room geometry, floor assignments, stairs, doors and windows control the building. Programme switches do not add or rearrange these objects.'})
    if intent.get('grid'):
        entries.append({'source': 'floor-guides', 'status': 'applied', 'message': 'Floor and relative room positions are constraints; a conflict blocks generation.'})
    spatial = (intent.get('text_reading') or {}).get('understood', [])
    placements = [u for u in spatial if any(isinstance(v, dict) and 'position' in v for v in u['values'].values())]
    for placement in placements:
        phrase = placement['text']
        retained = any(h.get('phrase') == phrase for h in intent.get('placement_hints', []))
        reason = ('Custom Plan geometry controls placement; this description does not move its rooms.' if custom else
                  'A painted guide or the resolved programme overrides this description placement.' if not retained else
                  'This room position constrains the planner; a conflict blocks generation.')
        entries.append({'source': 'description-placement', 'status': 'review' if custom or not retained else 'applied', 'message': phrase + ': ' + reason})
    for text in (intent.get('text_reading') or {}).get('not_understood', []):
        entries.append({'source': 'description', 'status': 'unapplied', 'message': 'Not interpreted; retained as a note: ' + text})
    for attachment in intent.get('attachments', []):
        entries.append({'source': 'reference-image', 'status': 'reference', 'message': str(attachment.get('name', 'Image')) + ': manual reference only; image content is not automatically traced into geometry.'})
    if payload.get('notes'):
        entries.append({'source': 'project-notes', 'status': 'reference', 'message': 'Project notes are preserved; they are not parsed as modelling instructions.'})
    editor = payload.get('editorState') or {}
    if editor.get('customPlan') and not custom:
        entries.append({'source': 'saved-custom-draft', 'status': 'off', 'message': 'Saved for editing, but not selected for this generation.'})
    if not intent.get('grid') and any(cell for board in editor.get('guideFloors', []) for row in board for cell in row):
        entries.append({'source': 'saved-floor-guides', 'status': 'off', 'message': 'Saved for editing, but not selected for this generation.'})
    return {'schema': 'floorforge.input-audit/1', 'planHash': intent['planHash'], 'entries': entries,
            'attention_count': sum(e['status'] in ('review', 'unapplied', 'reference') for e in entries)}
