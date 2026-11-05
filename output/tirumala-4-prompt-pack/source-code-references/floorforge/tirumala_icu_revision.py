"""Explicit ICU revisions; source P11/P12 coordinates remain archived and reproducible."""
from copy import deepcopy
from shapely.geometry import Polygon, box
from .tirumala_p11_p12 import _browser_numbers
from .tirumala_luxury import upper_plan

DELTA = 457.2


def regions(p):
    parts = [p] if p.geom_type == 'Polygon' else list(p.geoms)
    return [{'outer': [[round(x, 6), round(y, 6)] for x, y in list(q.exterior.coords)[:-1]],
             'holes': [[[round(x, 6), round(y, 6)] for x, y in list(h.coords)[:-1]] for h in q.interiors]}
            for q in parts if q.geom_type == 'Polygon' and q.area > 1]


def furniture_bounds(f, bounds):
    f['bounds'] = bounds
    f['polygon'] = regions(box(*bounds))[0]['outer']
    f.update(changed=True, replacement=True)


def trial_project(base, extend):
    p = deepcopy(base)
    cp = p['customPlan']; plan = cp['canonicalPlan']
    key = 'south-extension' if extend else 'compact-only'
    title = 'Tirumala 2 · P12 — ' + ('1½ ft south trial' if extend else 'Compact furniture trial')
    plan.update(version='p12-icu-' + key + '-2026-10-30', name=title)
    cp['tirumalaMeta'].update(projectId='tirumala-2-icu-' + key, version=plan['version'], label=title,
                             trial=True, sourceProject='tirumala-2', extensionSouthMm=DELTA if extend else 0,
                             spaciousnessPresentation=True)
    # Current P12 has no chairs. Retain no more than the bed and a compact drawer table.
    plan['furniture'] = [f for f in plan['furniture']
                         if f['room_id'] != 'g-care' or f['kind'] in ('reclining-bed', 'equipment-table')]
    table = next(f for f in plan['furniture'] if f['id'] == 'g-care/equipment-table')
    # Two-foot-wide, fourteen-inch-deep low closed storage at the northwest
    # corner, away from the porch cut-out and the route around the bed's feet.
    furniture_bounds(table, [10368 - 609.6, 8050 - 355.6, 10368, 8050])
    table['name'] = 'Compact closed drawer table · 2 ft × 14 in'

    if extend:
        room = next(r for r in plan['rooms'] if r['id'] == 'g-care')
        for pt in room['regions'][0]['outer']:
            if pt[0] == 7275: pt[0] -= DELTA
        room['bounds'][0] -= DELTA
        area = Polygon(room['regions'][0]['outer']).area / 92903.04
        room['areaSqFt'] = round(area, 1)
        for d in plan['dimensions']:
            if d['id'] == 'g-care': d.update(widthMm=3093 + DELTA, area=round(area, 1))
        # Translate only the south ICU wall, extend its west return, and close the
        # removed portion of the hall-veranda opening. No kitchen boundary moves.
        for wr in plan['wallRects']:
            if wr[0] == 7125 and wr[2] == 7275:
                wr[0] -= DELTA; wr[2] -= DELTA
            elif wr[0] == 7125 and wr[1] == 8050:
                wr[0] -= DELTA
            elif wr == [7100, 3352.8, 7357.6, 3502.8]:
                wr[0] = 7125 - DELTA
        # Rebuild open living floor including its threshold: no stale floor fills
        # inside the newly acquired ICU strip or below the new solid front wall.
        old_open = plan['openFloor'][0]
        floor = Polygon(old_open['outer'], old_open.get('holes', []))
        cut = box(7125 - DELTA, 3352.8, 7275, 8200)
        plan['openFloor'][0:1] = regions(floor.difference(cut))
        for op in plan['openings']:
            if op['id'] == 'icu-glass-living':
                op['a'][0] -= DELTA; op['b'][0] -= DELTA
            elif op['id'] == 'living-veranda':
                op['b'][0] = 7125 - DELTA
                width = op['b'][0] - op['a'][0]
                op.update(clearWidthMm=width, leafMm=width / 4)
        for pt in plan['glass']['path']: pt[0] -= DELTA
        for i in (0, 2): plan['glass']['stackBounds'][i] -= DELTA
        for pt in plan['stack']: pt[0] -= DELTA
        entrance = plan['entrance']; width = (7125 - DELTA) - 5500
        entrance['clearWidthMm'] = width
        entrance['meshStacks'][1][0] = 7125 - DELTA + 10
        entrance['meshStacks'][1][2] = 7125 - DELTA + 40
        entrance['woodStacks'][1][0] = 7125 - DELTA + 10
        entrance['woodStacks'][1][2] = 7125 - DELTA + 40
        for stack in entrance['woodStacks']: stack[1] = stack[3] - width / 4
        bed = next(f for f in plan['furniture'] if f['id'] == 'g-care/reclining-bed')
        a, b, c, d = bed['bounds']
        furniture_bounds(bed, [a - DELTA / 2, b, c - DELTA / 2, d])

    for room in cp['floors'][0]['rooms']:
        source = next((r for r in plan['rooms'] if r['id'] == room['id']), None)
        if source: room['polygon'] = deepcopy(source['regions'][0]['outer'])
    cp['upperPlan'] = upper_plan(plan)
    p['brief']['title'] = title
    p['notes'] = (title + '. Separate design trial, not a replacement of the approved P12. '
                  '40 × 50 ft plot; Ivory/limestone/teak; original G+1 rooms, kitchen, stairs, '
                  'wash gully, veranda, lower porch and parking retained. No global scaling. '
                  'ICU contains the same full-size recliner and a 2 ft × 14 in compact drawer table. '
                  + ('South ICU wall moves 457.2 mm into open living; bed recentred 228.6 mm south. '
                     'Hall-veranda folding wooden/netted doorway narrows to 1167.8 mm aperture, '
                     '1057.8 mm between jambs. ICU hall wooden/glass layers and veranda glass remain.'
                     if extend else 'Room boundaries and all openings unchanged.'))
    p['draftRevision'] += 1
    p['editorState']['customPlan'] = deepcopy(cp)
    return _browser_numbers(p)


def p13_project(base):
    """Extend P11's ICU east to the kitchen front, preserving a five-foot forecourt."""
    p = deepcopy(base)
    cp = p['customPlan']; plan = cp['canonicalPlan']
    delta = 609.6
    plan.update(version='p13-icu-east-extension-2026-10-30', name='P13 · longer ICU, compact storage')
    room = next(r for r in plan['rooms'] if r['id'] == 'g-care')
    assert room['bounds'] == [5452.4, 2283.6, 8882, 5759.6]
    for pt in room['regions'][0]['outer']:
        if pt[1] == 2283.6: pt[1] -= delta
    room['bounds'][1] -= delta
    room['areaSqFt'] = round(Polygon(room['regions'][0]['outer']).area / 92903.04, 1)
    for d in plan['dimensions']:
        if d['id'] == 'g-care': d.update(depthMm=4085.6, area=room['areaSqFt'])
    # Move the east wall, retaining the south/kitchen wall fragment at the old corner.
    walls = []
    for wr in plan['wallRects']:
        if wr == [5302.4, 2133.6, 5602.4, 2283.6]:
            walls += [[5302.4, 1524, 5602.4, 1674], [5302.4, 2133.6, 5452.4, 2283.6]]
        elif wr == [6602.4, 2133.6, 9032, 2283.6]:
            walls.append([6602.4, 1524, 9032, 1674])
        else:
            walls.append(wr)
    walls.append([8882, 1674, 9032, 2283.6])
    plan['wallRects'] = walls
    for op in plan['openings']:
        if op['id'] == 'icu-east-window':
            for end in ('a', 'b'): op[end][1] -= delta
    # The acquired strip is forecourt, never living, kitchen, veranda or car bay.
    for pt in plan['forecourt']:
        if pt[1] == 2133.6: pt[1] = 1524
    for r in plan['raisedForecourt']:
        for pt in r['outer']:
            if pt[1] == 2133.6: pt[1] = 1524
    # Alignment collapses the former step in the outline. Remove the resulting
    # repeated/collinear vertices so the rendered floor triangulates correctly.
    plan['forecourt'] = regions(Polygon(plan['forecourt']).simplify(0))[0]['outer']
    plan['raisedForecourt'] = [r2 for r in plan['raisedForecourt']
        for r2 in regions(Polygon(r['outer'], r.get('holes', [])).simplify(0))]
    for line in plan['levelChangeLines']:
        for pt in line:
            if pt == [9032, 2133.6]: pt[1] = 1524
    # Keep one companion chair and the full-size bed. Replace bulky cabinet/table
    # with a low closed drawer unit; TV follows the relocated east wall.
    remove = {'g-care/care-chair-right-2', 'g-care/care-chair-right-3', 'g-care/care-cupboard'}
    plan['furniture'] = [f for f in plan['furniture'] if f['id'] not in remove]
    for f in plan['furniture']:
        if f['id'] == 'g-care/reclining-bed':
            a,b,c,d = f['bounds']; furniture_bounds(f,[a,b-delta/2,c,d-delta/2])
        elif f['id'] == 'g-care/large-tv':
            a,b,c,d = f['bounds']; furniture_bounds(f,[a,b-delta,c,d-delta])
        elif f['id'] == 'g-care/equipment-table':
            furniture_bounds(f,[5502.4,1724,6112,2079.6])
            f['name'] = 'Compact closed drawer table · 2 ft × 14 in'
    cp['tirumalaMeta'].update(projectId='tirumala-3', version=plan['version'], label=plan['name'],
        displayOption='P13', sourceOption='P11', galleryRevision='spacious-2026-10-30',
        extensionEastMm=delta, spaciousnessPresentation=True, trial=False)
    cp['tirumalaMeta']['parameters']['careFront'] = 1674/304.8
    p['notes'] += (' P13 revision: ICU extends 2 ft east to the kitchen front wall, retaining a 5 ft forecourt. '
        'ICU clear size 11 ft 3 in × 13 ft 4 7/8 in (150.8 sq ft). Two extra ICU chairs and the tall cabinet '
        'are removed; one companion chair, the same recliner, TV and compact closed drawer table remain. '
        'Bed is recentered 1 ft east with its head west and feet east. All ground rooms other than ICU, '
        'door openings, kitchen, veranda, parking and stair footprints remain unchanged. '
        'The terrace roof plate follows the enlarged ICU; upper enclosed rooms and gallery remain unchanged.')
    p['brief']['title'] = 'Tirumala 3'
    p['draftRevision'] += 1
    return sync_project(p)


def sync_project(p):
    cp = p['customPlan']; plan = cp['canonicalPlan']
    care = next(r for r in plan['rooms'] if r['id']=='g-care')['bounds']
    cp['tirumalaMeta']['parameters'].update(careStart=round(care[0]/304.8,2),
        careFront=round(care[1]/304.8,2), careEnd=round(care[2]/304.8,2))
    for r in cp['floors'][0]['rooms']:
        source = next((s for s in plan['rooms'] if s['id'] == r['id']), None)
        if source: r['polygon'] = deepcopy(source['regions'][0]['outer'])
    cp['upperPlan'] = upper_plan(plan)
    cp['floors'][1]['rooms'] = [{'id':r['id'], 'kind':r['kind'], 'name':r['name'],
        'polygon':deepcopy(r['polygon'])} for r in cp['upperPlan']['rooms']]
    p['editorState']['customPlan'] = deepcopy(cp)
    return _browser_numbers(p)


def apply_gallery_revision(base, slug):
    """Only a checked-in selection activates changes to the named gallery samples."""
    import json
    from pathlib import Path
    selection = Path(__file__).resolve().parents[1] / 'examples/gallery/briefs/tirumala-spaciousness.json'
    if not selection.exists(): return base
    choices = json.loads(selection.read_text())
    if slug == 'tirumala-3' and choices.get(slug) == 'p13-east-2ft':
        return p13_project(base)
    if slug == 'tirumala-2' and choices.get(slug) in ('compact-only', 'south-extension'):
        p = trial_project(base, choices[slug] == 'south-extension')
        meta = p['customPlan']['tirumalaMeta']
        meta.update(projectId=slug, displayOption='P12', galleryRevision='spacious-2026-10-30', trial=False)
        label = 'P12 · wider ICU and compact storage' if choices[slug] == 'south-extension' else 'P12 · compact ICU storage'
        meta['label'] = label
        p['customPlan']['canonicalPlan']['name'] = label
        p['brief']['title'] = 'Tirumala 2'
        p['notes'] = p['notes'].replace('Separate design trial, not a replacement of the approved P12.',
            'Current Tirumala 2 gallery sample; original approved P12 archived before revision.')
        p['notes'] = p['notes'].replace('south trial.', 'south extension.').replace('Compact furniture trial.', 'Compact furniture revision.')
        return sync_project(p)
    return base

