#!/usr/bin/env python3
"""Two sample homes published with the Plan Reveal walkthrough; no other sample or user build is touched.

The Aangan House is a single-storey, east-facing courtyard home on a 55 x 80 ft plot: every room opens off a
veranda around an open aangan with a mango tree, as Indian courtyard houses have for centuries. The Long House
is a G+1 on the commonest Indian plot, 30 x 60 ft: one straight line from the front door through living, a light
court open to the sky through both floors (an ashoka rising through it), dining and kitchen to the rear garden.

Both are authored custom plans (floorforge.custom-plan/1), generated through the normal pipeline, then published
with floorforge.plan_reveal, which works the same way for any user's plan:

    python3 scripts/build_plan_reveal_samples.py
"""
from pathlib import Path
import copy, hashlib, json, shutil, sys, tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shapely.geometry import Polygon, box
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.pipeline import run, deterministic_zip
from floorforge import plan_reveal

GALLERY = ROOT / 'examples/gallery'


def room(id, kind, name, x, y, w, d, **extra):
    return dict(id=id, kind=kind, name=name, polygon=[[x, y], [x + w, y], [x + w, y + d], [x, y + d]], **extra)


def opening(id, room_id, side, offset, width, kind='door', height=2100, sill=0, **extra):
    return dict(id=id, roomId=room_id, side=side, offset=offset, width=width, kind=kind, height=height, sill=sill, hinge=extra.pop('hinge', 'start'), **extra)


def window(id, room_id, side, offset, width, height=1500, sill=750, **extra):
    return opening(id, room_id, side, offset, width, 'window', height, sill, **extra)


# ---------------------------------------------------------------------------------------------- The Aangan House
def aangan():
    """x runs south to north (left to right seen from the road), y from the east-facing front to the west rear."""
    t = 230
    A0, A1 = 230, 4130          # living wing (south)
    B0, B1 = 4360, 8166         # aangan
    V1 = 9966                   # veranda along the bedroom wing
    C0, C1 = 10196, 14096       # bedroom wing (north)
    g = [
        room('a-living', 'living', 'Living room', A0, 230, A1 - A0, 6060),
        room('a-foyer', 'foyer', 'Entrance hall', B0, 230, V1 - B0, 4200),
        room('a-study', 'bedroom', 'Guest room', C0, 230, C1 - C0, 4200, bedType='double', wardrobeWall='rear'),
        room('a-dining', 'dining', 'Dining room', A0, 6520, A1 - A0, 3600),
        room('a-kitchen', 'kitchen', 'Kitchen', A0, 10350, A1 - A0, 3300, kitchenLayout='l-shaped-return', prepStorageWall='left'),
        room('a-utility', 'utility', 'Utility', A0, 13880, A1 - A0, 1500),
        room('a-yard', 'drying-yard', 'Drying yard', 0, 15610, A1, 4202, drain=True),
        room('a-court', 'courtyard', 'Aangan', B0, 4660, B1 - B0, 7200, centerTree='mango', drain=True),
        room('a-veranda', 'veranda', 'Veranda', B1, 4660, V1 - B1, 11630, finishStyle='warm-stone', clearAccess=True),
        room('a-family', 'family', 'Family lounge', B0, 12090, B1 - 230 - B0, 4200),
        dict(id='a-garden', kind='courtyard', name='Rear garden', garden=True, drain=True,
             polygon=[[B0, 16520], [B1, 16520], [B1, 16290], [V1, 16290], [V1, 19812], [B0, 19812]]),
        room('a-bed2', 'bedroom', 'Bedroom', C0, 4660, C1 - C0, 3900, bedType='double', wardrobeWall='rear'),
        room('a-bath2', 'bathroom', 'Bath', C0, 8790, C1 - C0, 1800),
        room('a-master', 'bedroom', 'Master bedroom', C0, 10820, C1 - C0, 4500, bedType='double', wardrobeWall='rear'),
        room('a-dress', 'dress', 'Dressing', C0, 15550, C1 - C0, 1500),
        room('a-mbath', 'bathroom', 'Master bath', C0, 17280, C1 - C0, 2302),
    ]
    o = [
        opening('a-entry', 'a-foyer', 'front', (V1 - B0 - 1200) // 2, 1200, 'entry', 2400),
        window('a-foyer-front-l', 'a-foyer', 'front', 500, 1100),
        window('a-foyer-front-r', 'a-foyer', 'front', V1 - B0 - 1600, 1100),
        opening('a-foyer-living', 'a-foyer', 'left', 1100, 2000, 'cased', 2400),
        opening('a-foyer-study', 'a-study', 'left', 2900, 900, hinge='end'),
        opening('a-foyer-court', 'a-foyer', 'rear', 800, 2200, 'glazed', 2400, sliding=True, slidingPanels=2),
        opening('a-foyer-veranda', 'a-foyer', 'rear', 4000, 1300, 'cased', 2400),
        window('a-living-front', 'a-living', 'front', 700, 2500, 1600, 600),
        window('a-living-south', 'a-living', 'left', 1200, 2600, 1600, 600),
        window('a-living-court', 'a-living', 'right', 4550, 1300, 1500, 750),
        opening('a-living-dining', 'a-living', 'rear', 700, 2400, 'cased', 2400),
        opening('a-dining-court', 'a-dining', 'right', 600, 2400, 'glazed', 2400, sliding=True, slidingPanels=2),
        window('a-dining-south', 'a-dining', 'left', 900, 2000, 1500, 750),
        # At the free end of the kitchen's L, so the worktop has a solid wall behind it.
        opening('a-dining-kitchen', 'a-dining', 'rear', 100, 900, 'cased', 2400),
        window('a-kitchen-south', 'a-kitchen', 'left', 900, 1500, 1100, 1050),
        opening('a-kitchen-utility', 'a-kitchen', 'rear', 2700, 900),
        opening('a-utility-yard', 'a-utility', 'rear', 400, 900),
        window('a-utility-south', 'a-utility', 'left', 400, 800, 900, 1200),
        opening('a-family-court', 'a-family', 'front', 700, 2400, 'glazed', 2400, sliding=True, slidingPanels=2),
        opening('a-family-veranda', 'a-family', 'right', 1300, 1400, 'cased', 2400),
        opening('a-family-garden', 'a-family', 'rear', 700, 2400, 'glazed', 2400, sliding=True, slidingPanels=2),
        opening('a-bed2-veranda', 'a-bed2', 'left', 400, 900),
        window('a-bed2-court', 'a-bed2', 'left', 1700, 1700, 1500, 750),
        window('a-bed2-north', 'a-bed2', 'right', 1000, 1900, 1500, 750),
        opening('a-bath2-veranda', 'a-bath2', 'left', 500, 800),
        window('a-bath2-north', 'a-bath2', 'right', 300, 1200, 600, 1500),
        opening('a-master-veranda', 'a-master', 'left', 400, 1000),
        window('a-master-court', 'a-master', 'left', 1900, 1900, 1500, 750),
        window('a-master-north', 'a-master', 'right', 1100, 2200, 1500, 750),
        opening('a-master-dress', 'a-master', 'rear', 300, 900, 'cased', 2100),
        opening('a-dress-bath', 'a-dress', 'rear', 300, 800),
        window('a-mbath-north', 'a-mbath', 'right', 700, 1100, 600, 1500),
        window('a-mbath-rear', 'a-mbath', 'rear', 1500, 1200, 600, 1500),
        window('a-study-front', 'a-study', 'front', 900, 2000, 1500, 750),
        window('a-study-north', 'a-study', 'right', 1100, 1800, 1500, 750),
    ]
    plan = dict(schema='floorforge.custom-plan/1', units='mm', wallThickness=t, frontCourt='planted', facadeStyle='warm-layered',
                entranceStyle='wall-supported', interiorFloor='ivory-vitrified', doorsClosed=False,
                sceneSeed='5a1e0c2d9f8b4e7a6c3d2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2918',
                floors=[dict(id='floor-0', rooms=g, walls=[], openings=o)], stairs=[])
    brief = dict(title='The Aangan House', width_mm=16764, depth_mm=24384, road_bearing_deg=90, front_mm=3048, rear_mm=1524,
                 left_mm=1219, right_mm=1219, storeys=1, bedrooms=3, parking=False, pooja=False, eldercare=False, open_kitchen=False,
                 attached_baths=1, roof_access=False, vastu='moderate', floor_height_mm=3300, exterior_theme='earth_terracotta',
                 interior_theme='earthy_modern_indian', solar_hour=8.5)
    notes = ('East-facing 55 × 80 ft courtyard home on one level. The entrance hall looks straight across the aangan to '
             'its mango tree; living and dining open to it on the south, a covered veranda on the north leads to the '
             'bedrooms, and the family lounge opens to both the aangan and the rear garden. Every room has daylight and '
             'cross-ventilation from two sides. Preliminary concept: structure, services and approvals remain with a '
             'qualified professional.')
    return dict(schema='floorforge.project/0.4', brief=brief, customPlan=plan, notes=notes)


# ---------------------------------------------------------------------------------------------- The Long House
def long_house():
    """30 x 60 ft, north-facing. x runs east to west across the plot, y from the street to the rear garden."""
    t = 230
    M0, M1 = 230, 4784          # the line: court and passage, dining, kitchen
    C1, P0 = 2730, 2960         # light court | glazed passage beside it
    S0, S1 = 5014, 7114         # service strip: stair, powder room, utility
    g = [
        room('l-living', 'living', 'Living room', M0, 230, S1 - M0, 4000),
        room('l-court', 'courtyard', 'Light court', M0, 4460, C1 - M0, 2600, centerTree='ashoka', drain=True),
        room('l-passage', 'hall', 'Garden passage', P0, 4460, M1 - P0, 2600),
        room('l-stair', 'stair', 'Staircase', S0, 4460, S1 - S0, 4100),
        room('l-dining', 'dining', 'Dining room', M0, 7290, M1 - M0, 2800),
        room('l-powder', 'powder-room', 'Powder room', S0, 8790, S1 - S0, 1300),
        room('l-kitchen', 'kitchen', 'Kitchen', M0, 10320, M1 - M0, 2400, kitchenLayout='l-shaped-return', prepStorageWall='left'),
        room('l-utility', 'utility', 'Utility', S0, 10320, S1 - S0, 2400),
        room('l-garden', 'courtyard', 'Rear garden', 0, 12950, 7344, 814, garden=True, drain=True),
    ]
    go = [
        opening('l-entry', 'l-living', 'front', 4500, 1100, 'entry', 2400),
        window('l-living-front', 'l-living', 'front', 600, 2600, 1700, 500),
        window('l-living-east', 'l-living', 'left', 900, 2200, 1700, 500),
        window('l-living-west', 'l-living', 'right', 1200, 1600, 1500, 750),
        window('l-living-court', 'l-living', 'rear', 300, 1900, 1500, 750),
        opening('l-living-passage', 'l-living', 'rear', 2830, 1500, 'cased', 2400),
        opening('l-passage-court', 'l-passage', 'left', 250, 2100, 'glazed', 2400, sliding=True, slidingPanels=2),
        opening('l-passage-stair', 'l-passage', 'right', 100, 900, 'cased', 2400),
        opening('l-passage-dining', 'l-passage', 'rear', 250, 1300, 'cased', 2400),
        opening('l-dining-court', 'l-dining', 'front', 300, 1900, 'glazed', 2400, sliding=True, slidingPanels=2),
        window('l-dining-east', 'l-dining', 'left', 600, 1600, 1500, 750),
        opening('l-dining-powder', 'l-powder', 'left', 300, 750, hinge='end'),
        # At the free end of the kitchen's L, so the worktop has a solid wall behind it.
        opening('l-dining-kitchen', 'l-dining', 'rear', 100, 900, 'cased', 2400),
        window('l-kitchen-east', 'l-kitchen', 'left', 500, 1400, 1100, 1050),
        opening('l-kitchen-garden', 'l-kitchen', 'rear', 2400, 1700, 'glazed', 2400, sliding=True, slidingPanels=2),
        opening('l-kitchen-utility', 'l-kitchen', 'right', 1630, 750),   # past the end of the L's return
        opening('l-utility-garden', 'l-utility', 'rear', 600, 900),
        window('l-utility-west', 'l-utility', 'right', 700, 1000, 900, 1200),
        window('l-stair-west', 'l-stair', 'right', 1800, 1200, 1500, 900),
        window('l-powder-west', 'l-powder', 'right', 350, 600, 600, 1500),
    ]
    u = [
        room('u-master', 'bedroom', 'Master bedroom', M0, 230, M1 - M0, 4000, bedType='double', wardrobeWall='left'),
        room('u-mbath', 'bathroom', 'Master bath', S0, 230, S1 - S0, 2400),
        room('u-dress', 'dress', 'Dressing', S0, 2860, S1 - S0, 1370),
        room('u-gallery', 'hall', 'Gallery', P0, 4460, M1 - P0, 2600),
        room('u-stair', 'stair', 'Staircase', S0, 4460, S1 - S0, 4100, guardStyle='white-timber'),
        room('u-bed2', 'bedroom', 'Bedroom', M0, 7290, M1 - M0, 2800, bedType='double', wardrobeWall='left'),
        room('u-bath2', 'bathroom', 'Bath', S0, 8790, S1 - S0, 1340),
        room('u-balcony', 'balcony', 'Garden balcony', M0, 10320, M1 - M0, 2400, clearAccess=True, finishStyle='honed-sandstone'),
    ]
    uo = [
        window('u-master-front', 'u-master', 'front', 500, 2600, 1700, 500),
        window('u-master-east', 'u-master', 'left', 900, 1800, 1500, 750),
        opening('u-master-bath', 'u-mbath', 'left', 500, 750, hinge='end'),
        opening('u-master-dress', 'u-dress', 'left', 300, 800, 'cased', 2100),
        opening('u-gallery-master', 'u-gallery', 'front', 600, 900),
        window('u-gallery-court', 'u-gallery', 'left', 300, 2000, 1800, 450),
        window('u-master-court', 'u-master', 'rear', 300, 1900, 1500, 750),
        opening('u-gallery-stair', 'u-gallery', 'right', 100, 900, 'cased', 2400),
        opening('u-gallery-bed2', 'u-gallery', 'rear', 400, 900),
        window('u-bed2-court', 'u-bed2', 'front', 300, 1900, 1500, 750),
        opening('u-bed2-bath', 'u-bath2', 'left', 300, 750, hinge='end'),
        opening('u-bed2-balcony', 'u-bed2', 'rear', 1200, 1800, 'glazed', 2400, sliding=True, slidingPanels=2),
        window('u-mbath-west', 'u-mbath', 'right', 800, 600, 600, 1500),
        window('u-bath2-west', 'u-bath2', 'right', 350, 600, 600, 1500),
        window('u-stair-west', 'u-stair', 'right', 1800, 1200, 1500, 900),
    ]
    plan = dict(schema='floorforge.custom-plan/1', units='mm', wallThickness=t, frontCourt='tiled', facadeStyle='warm-layered',
                entranceStyle='wall-supported', interiorFloor='ivory-vitrified', doorsClosed=False,
                sceneSeed='0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0',
                # The light court is closed on its outer (east) side on both floors; above it is only sky.
                floors=[dict(id='floor-0', rooms=g, walls=[dict(id='l-court-east-wall', a=[115, 4345], b=[115, 7175])], openings=go),
                        dict(id='floor-1', rooms=u, walls=[dict(id='u-court-east-wall', a=[115, 4345], b=[115, 7175])], openings=uo)],
                stairs=[dict(id='long-stair', roomIds=['l-stair', 'u-stair'], flightWidth=1000, well=100, landing=1050, tread=250)])
    brief = dict(title='The Long House', width_mm=9144, depth_mm=18288, road_bearing_deg=0, front_mm=3000, rear_mm=1524,
                 left_mm=900, right_mm=900, storeys=2, bedrooms=2, parking=False, pooja=False, eldercare=False, open_kitchen=False,
                 attached_baths=2, roof_access=False, vastu='moderate', floor_height_mm=3150, exterior_theme='warm_modern_minimal',
                 interior_theme='quiet_minimal', solar_hour=16.5)
    notes = ('North-facing 30 × 60 ft home on two levels, laid on one line: from the front door the eye runs through the '
             'living room and a glazed passage beside a light court open to the sky, to the dining room, the kitchen and '
             'the rear garden. Stair, powder room and utility share a service strip along the west wall. Upstairs a gallery '
             'overlooks the court and serves the front master suite and the rear bedroom with its garden balcony. '
             'Preliminary concept: structure, services and approvals remain with a qualified professional.')
    return dict(schema='floorforge.project/0.4', brief=brief, customPlan=plan, notes=notes)


SAMPLES = [
    ('aangan-house', aangan, {
        'title': 'The Aangan House', 'style': 'Plan Reveal · courtyard',
        'description': 'A single-storey courtyard home on a 55 × 80 ft plot: every room opens to an aangan with a mango tree. Opens as its own drawing; scroll to walk in.',
        'copy': {'eyebrow': 'The Aangan House · ground floor plan · A-101', 'headline': ['Every room', 'opens to', 'the aangan.'], 'theme': 'stencil',
                 'lede': 'One level, one courtyard and its tree. This drawing is the house itself, cut at 1.2 m. Scroll, and walk in.',
                 'cta': 'Drawing set', 'endTitle': 'Built around a tree.', 'endText': 'The drawing and the house are one model. Change the plan in the studio and this walk is rebuilt from it, room by room.'},
        'order': ['a-foyer', 'a-living', 'a-court', 'a-dining', 'a-kitchen', 'a-family', 'a-master', 'a-bed2'], 'grade': 'golden'}),
    ('long-house', long_house, {
        'title': 'The Long House', 'style': 'Plan Reveal · one line',
        'description': 'A G+1 home on a 30 × 60 ft plot laid on one line: living, a light court open to the sky, dining, kitchen and garden. Opens as its own drawing; scroll to walk in.',
        'copy': {'eyebrow': 'The Long House · ground floor plan · A-101', 'headline': ['A house', 'on one', 'line.'], 'theme': 'serif',
                 'lede': 'Eighteen metres from the street to the garden, on a 30 × 60 ft plot. This drawing is the building. Scroll and walk into it.',
                 'cta': 'Drawing set', 'endTitle': 'Light, all the way through.', 'endText': 'The drawing and the house are one model. Change the plan in the studio and this walk is rebuilt from it, room by room.'},
        'order': ['l-living', 'l-court', 'l-dining', 'l-kitchen', 'u-master', 'u-bed2'], 'grade': 'golden'}),
]


def editor_state(project):
    plan = project['customPlan']; v = project['brief']
    W = v['width_mm'] - v['left_mm'] - v['right_mm']; D = v['depth_mm'] - v['front_mm'] - v['rear_mm']
    boards = []
    for fl in plan['floors']:
        beds = [r for r in fl['rooms'] if r['kind'] == 'bedroom']
        labels = {r['id']: ('bedroom-' + str(beds.index(r) + 1) if r['kind'] == 'bedroom' else r['kind']) for r in fl['rooms']}
        rows = []
        for row in range(4):
            line = []
            for col in range(4):
                cell = box(col * W / 4, row * D / 4, (col + 1) * W / 4, (row + 1) * D / 4)
                matches = sorted([(Polygon(r['polygon']).intersection(cell).area, r['id']) for r in fl['rooms']], reverse=True)
                line.append(labels[matches[0][1]] if matches and matches[0][0] else '')
            rows.append(line)
        boards.append(rows)
    # The editor keeps three 16-cell guide drafts (ground, first, roof) whatever the storey count.
    boards += [[[''] * 4 for _ in range(4)] for _ in range(3 - len(boards))]
    return dict(mode='custom', guideFloors=boards, guideEdited=False, customPlan=copy.deepcopy(plan), useRoomBoard=False)


def build(slug, make, meta):
    p = make()
    p['editorState'] = editor_state(p)
    b = generate_layout(fuse(p))
    review = validate(b)
    if review.get('errors'):
        raise RuntimeError(slug + ': ' + json.dumps(review['errors'], indent=2))
    dest = GALLERY / slug
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    (GALLERY / 'briefs' / f'{slug}.json').write_text(json.dumps(p, indent=2) + '\n', encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='ff-reveal-') as tmp:
        result = run(p, Path(tmp), use_cache=False)
        shutil.copytree(result['path'], dest, dirs_exist_ok=True)
    plan_reveal.publish(dest, order=meta['order'], copy=meta['copy'], grade=meta['grade'])
    built = json.loads((dest / 'building.json').read_text(encoding='utf-8'))
    record = dict(id=slug, title=meta['title'], description=meta['description'], style=meta['style'], directory=f'gallery/{slug}',
                  bedrooms=p['brief']['bedrooms'], storeys=built['storeys'], widthFt=round(p['brief']['width_mm'] / 304.8),
                  depthFt=round(p['brief']['depth_mm'] / 304.8), roofAccess=bool(built.get('rooftop')), planHash=built['planHash'],
                  featurePage='reveal.html', hasPlanReveal=True)
    print(json.dumps({'sample': slug, 'planHash': built['planHash'][:12], 'review': review.get('status'), 'warnings': len(review.get('warnings', []))}))
    return record


def main():
    only = set(sys.argv[1:])
    records = [build(slug, make, meta) for slug, make, meta in SAMPLES if not only or slug in only]
    catalog = GALLERY / 'catalog.json'
    items = json.loads(catalog.read_text(encoding='utf-8'))
    ids = {r['id'] for r in records}
    items = [s for s in items if s['id'] not in ids]
    # The walkthrough samples follow the personal projects, ahead of the generated presets.
    at = next((i for i, s in enumerate(items) if s['id'] == 'saved-verandah'), len(items))
    items[at:at] = records
    catalog.write_text(json.dumps(items, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
