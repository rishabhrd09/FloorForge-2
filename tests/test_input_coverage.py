"""Every supplied input has an honest, revision-linked application status."""
import json
from pathlib import Path
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import reports, validate
from floorforge.scene import make_scene

ROOT = Path(__file__).resolve().parents[1]


def test_combined_inputs_report_overrides_without_losing_them():
    p = {'brief': {'bedrooms': 2}, 'text': '3 bedrooms. A soundproof music studio.',
         'sources': [{'id': 'manual', 'kind': 'form', 'values': {'bedrooms': 4, 'style': 'warm'}},
                     {'id': 'old-survey', 'kind': 'survey', 'enabled': False, 'values': {'bedrooms': 1}}]}
    i = fuse(p); audit = i['input_audit']
    assert i['values']['bedrooms'] == 4
    rows = {r['source']: r for r in audit['entries'] if 'overridden' in r}
    assert rows['description']['overridden'] == [{'field': 'bedrooms', 'requested': 3, 'resolved': 4, 'by': ['manual']}]
    assert rows['old-survey']['status'] == 'off'
    assert rows['manual']['status'] == 'applied'
    assert any(e['status'] == 'unapplied' and 'soundproof' in e['message'] for e in audit['entries'])
    assert audit['planHash'] == i['planHash'] and audit['attention_count'] > 0


def test_custom_plan_does_not_claim_description_placement_or_programme_switches_changed_geometry():
    p = json.loads((ROOT / 'examples/custom/g2-terrace.floorforge.json').read_text(encoding='utf-8'))
    p['text'] = 'Kitchen at rear right.'; p['sources'] = [{'id': 'manual', 'kind': 'form', 'values': {'pooja': True, 'open_kitchen': True}}]
    i = fuse(p); audit = i['input_audit']
    assert next(e for e in audit['entries'] if e['source'] == 'custom-plan')['status'] == 'applied'
    assert set(next(e for e in audit['entries'] if e['source'] == 'manual')['authored']) == {'pooja', 'open_kitchen'}
    assert any(e['source'] == 'description-placement' and e['status'] == 'review' for e in audit['entries'])
    b = generate_layout(i); r = reports(b, validate(b)); s = make_scene(b, r)
    assert b['input_audit'] == r['input_audit'] == s['input_audit'] == audit
    assert s['opening_model']['openings'] == b['openings']
    assert s['opening_model']['walls'] == b['walls']


def test_references_and_inactive_editor_drafts_are_never_claimed_as_applied():
    p = {'attachments': [{'name': 'plan.png', 'kind': 'visual-reference', 'note': 'look here'}], 'notes': 'Keep these notes',
         'editorState': {'mode': 'automatic', 'guideFloors': [[[""] * 4 for _ in range(4)] for _ in range(3)]}}
    p['editorState']['guideFloors'][0][0][0] = 'kitchen'
    rows = {r['source']: r for r in fuse(p)['input_audit']['entries']}
    assert rows['reference-image']['status'] == 'reference'
    assert rows['project-notes']['status'] == 'reference'
    assert rows['saved-floor-guides']['status'] == 'off'


def test_save_reopen_keeps_input_coverage_and_plan_hash():
    p = {'text': '2 bedrooms. Kitchen at rear left.', 'brief': {'storeys': 1}}
    a = fuse(p); b = fuse(json.loads(json.dumps(p)))
    assert a['input_audit'] == b['input_audit']
    placement = next(e for e in a['input_audit']['entries'] if e['source'] == 'description-placement')
    assert placement['status'] == 'applied'
