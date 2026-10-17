"""Reproducible Heritage Bungalow sample; no user builds or other samples are changed.

A large, nostalgic G+1 government-style bungalow on a 100 x 130 ft plot, recreated from the owner's
photographs: blush render with a red comb frieze on every parapet, a grilled entrance verandah beside
a corrugated-sheet carport, a grand drawing hall with an open teak stair, high 3.6 m ceilings, a big
clipped lawn, rose-covered mesh fences, Ashoka, neem, mango and Araucaria trees and rows of red pots.

    .venv/bin/python scripts/build_bungalow.py            # regenerate examples/gallery/bungalow and its catalogue entry
    .venv/bin/python scripts/build_bungalow.py --check    # validate the plan only
"""
from pathlib import Path
import sys, json, tempfile, shutil, hashlib
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from shapely.geometry import Polygon
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.pipeline import run, deterministic_zip

SLUG = 'bungalow'
TITLE = 'The Bungalow'


def room(id, kind, name, x0, y0, x1, y1, **extra):
    return dict(id=id, kind=kind, name=name, polygon=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], **extra)


def opening(id, room, side, offset, width, kind='door', height=2400, sill=0, **extra):
    return dict(id=id, roomId=room, side=side, offset=offset, width=width, kind=kind, height=height, sill=sill, hinge='start', **extra)


def window(id, room, side, offset, width, sill=750, height=2250, **extra):
    return opening(id, room, side, offset, width, 'window', height, sill, **extra)


def project():
    # x: west -> east along the road; y: south (road, front) -> north (rear). Clear space, 230 mm brick walls.
    W, D = 19812, 19812
    g = [
        # West wing: grilled entrance verandah, guest toilet and puja, kitchen, pantry and open wash yard.
        room('g-verandah', 'foyer', 'Grilled entrance verandah', 230, 230, 5030, 4430, wallPaint='mint-green', floorFinish='ceramic-white'),
        room('g-powder', 'powder-room', 'Guest toilet', 230, 4660, 2630, 6930, wallPaint='ivory'),
        room('g-puja', 'pooja', 'Puja room', 2860, 4660, 5030, 6930, altarWall='left', wallPaint='lemon', floorFinish='white-marble'),
        room('g-kitchen', 'kitchen', 'Kitchen', 230, 7160, 5030, 12560, wallPaint='cream', floorFinish='kota-stone'),
        room('g-pantry', 'store', 'Pantry and store', 230, 12790, 5030, 15090, wallPaint='cream', floorFinish='kota-stone'),
        room('g-wash', 'drying-yard', 'Open wash yard', 0, 15320, 5260, 18320, drain=True, floorFinish='kota-stone'),
        # Centre: drawing hall, open stair hall, dining hall and the rear verandah.
        room('g-drawing', 'living', 'Drawing hall', 5260, 230, 12660, 6930, wallPaint='sky-blue', floorFinish='white-marble'),
        room('g-stair', 'stair', 'Stair hall', 5260, 7160, 12660, 9560, wallPaint='cream', floorFinish='mosaic'),
        room('g-dining', 'dining', 'Dining hall', 5260, 9790, 12660, 15090, wallPaint='pista', floorFinish='white-marble'),
        room('g-rear-verandah', 'veranda', 'Rear verandah', 5260, 15320, 12660, 18320, clearAccess=True, floorFinish='red-oxide'),
        # East wing: office, master suite, guest suite and garden store.
        room('g-office', 'study', 'Office', 12890, 230, 19582, 4430, wallPaint='cream', floorFinish='ivory-vitrified'),
        room('g-mdress', 'dress', 'Master dressing', 12890, 4660, 16180, 7460, wallPaint='peach'),
        room('g-mbath', 'bathroom', 'Master bath', 16410, 4660, 19582, 7460),
        room('g-master', 'bedroom', 'Master bedroom', 12890, 7690, 19582, 13090, wallPaint='peach', floorFinish='ivory-vitrified'),
        room('g-guest', 'bedroom', 'Guest bedroom', 12890, 13320, 19582, 17520, wallPaint='sky-blue', floorFinish='ivory-vitrified'),
        room('g-gstore', 'store', 'Garden store', 12890, 17750, 16180, 19582, floorFinish='red-oxide'),
        room('g-gbath', 'bathroom', 'Guest bath', 16410, 17750, 19582, 19582),
    ]
    go = [
        # Verandah: an open steel-grille entry door and grille bays to the front, a side grille door to the carport.
        opening('g-entry', 'g-verandah', 'front', 1800, 1200, 'entry', 2400, grille=True),
        window('g-verandah-front-west', 'g-verandah', 'front', 150, 1420, 900, 2250, grille=True),
        window('g-verandah-front-east', 'g-verandah', 'front', 3230, 1420, 900, 2250, grille=True),
        opening('g-verandah-carport', 'g-verandah', 'left', 1550, 1100, 'door', 2400, grille=True),
        window('g-verandah-side-south', 'g-verandah', 'left', 150, 1170, 900, 2250, grille=True),
        window('g-verandah-side-north', 'g-verandah', 'left', 2880, 1170, 900, 2250, grille=True),
        # The grand paired teak doors with mesh shutters open inward to the drawing hall.
        opening('g-drawing-main', 'g-drawing', 'left', 1100, 2000, 'door', 2700, timberScreen=True),
        opening('g-powder-door', 'g-powder', 'front', 800, 800, 'door', 2100),
        window('g-powder-vent', 'g-powder', 'left', 700, 900, 1650, 700),
        opening('g-puja-door', 'g-puja', 'right', 650, 900, 'door', 2400),
        window('g-drawing-front-1', 'g-drawing', 'front', 700, 1500),
        window('g-drawing-front-2', 'g-drawing', 'front', 2950, 1500),
        window('g-drawing-front-3', 'g-drawing', 'front', 5200, 1500),
        opening('g-office-door', 'g-office', 'left', 1500, 1000, 'door', 2400),
        opening('g-drawing-stair-arch', 'g-drawing', 'rear', 4040, 3100, 'cased', 3000),
        opening('g-dining-stair-arch', 'g-dining', 'front', 4040, 3100, 'cased', 3000),
        opening('g-kitchen-door', 'g-dining', 'left', 1000, 1000, 'door', 2400),
        window('g-kitchen-west-1', 'g-kitchen', 'left', 900, 1500, 900, 1500),
        window('g-kitchen-west-2', 'g-kitchen', 'left', 3300, 1500, 900, 1500),
        opening('g-pantry-door', 'g-pantry', 'front', 600, 900, 'door', 2100),
        window('g-pantry-west', 'g-pantry', 'left', 700, 1000, 1200, 1000),
        opening('g-pantry-yard', 'g-pantry', 'rear', 3200, 900, 'door', 2100),
        window('g-dining-rear-1', 'g-dining', 'rear', 600, 1500),
        opening('g-dining-verandah', 'g-dining', 'rear', 2800, 1800, 'door', 2700, timberScreen=True),
        window('g-dining-rear-2', 'g-dining', 'rear', 5300, 1500),
        window('g-office-front-1', 'g-office', 'front', 900, 1800),
        window('g-office-front-2', 'g-office', 'front', 3900, 1800),
        window('g-office-east', 'g-office', 'right', 1200, 1500),
        opening('g-mdress-door', 'g-mdress', 'rear', 1200, 900, 'door', 2400),
        opening('g-mbath-door', 'g-mbath', 'left', 900, 900, 'door', 2100),
        window('g-mbath-east', 'g-mbath', 'right', 900, 1200, 1500, 900),
        opening('g-master-door', 'g-master', 'left', 2610, 1000, 'door', 2400),
        window('g-master-east-1', 'g-master', 'right', 900, 1500),
        window('g-master-east-2', 'g-master', 'right', 3300, 1500),
        opening('g-guest-door', 'g-guest', 'left', 380, 1000, 'door', 2400),
        window('g-guest-east', 'g-guest', 'right', 1200, 1800),
        opening('g-gbath-door', 'g-gbath', 'front', 800, 800, 'door', 2100),
        window('g-gbath-east', 'g-gbath', 'right', 450, 900, 1500, 900),
        opening('g-gstore-door', 'g-gstore', 'rear', 1100, 1000, 'door', 2100),
    ]
    terrace = [[0, 0], [W, 0], [W, 4430], [12660, 4430], [12660, 6930], [0, 6930]]
    u = [
        room('f-stair', 'stair', 'Upper stair hall', 5260, 7160, 12660, 9560, wallPaint='cream', floorFinish='mosaic'),
        dict(id='f-front-terrace', kind='terrace', name='Front terrace · chick pergola', polygon=terrace, clearAccess=True, floorFinish='red-oxide'),
        room('f-lounge', 'family', 'Upper family lounge', 5260, 9790, 12660, 15090, wallPaint='powder-pink', floorFinish='ivory-vitrified'),
        room('f-bed4', 'bedroom', 'Bedroom 4', 230, 7160, 5030, 12560, wallPaint='lilac', floorFinish='ivory-vitrified'),
        room('f-bath4', 'bathroom', 'Bath 4', 230, 12790, 5030, 15090),
        room('f-dress3', 'dress', 'Dressing 3', 12890, 4660, 16180, 7460, wallPaint='mint-green'),
        room('f-bath3', 'bathroom', 'Bath 3', 16410, 4660, 19582, 7460),
        room('f-bed3', 'bedroom', 'Bedroom 3', 12890, 7690, 19582, 13090, wallPaint='mint-green', floorFinish='ivory-vitrified'),
        room('f-rear-terrace', 'terrace', 'Rear terrace', 5260, 15320, 12660, 18320, clearAccess=True, floorFinish='red-oxide'),
    ]
    uo = [
        opening('f-stair-terrace', 'f-stair', 'front', 5500, 1500, 'glazed', 2400),
        opening('f-stair-lounge-arch', 'f-lounge', 'front', 4040, 3100, 'cased', 3000),
        opening('f-lounge-terrace', 'f-lounge', 'rear', 2800, 1800, 'glazed', 2400),
        window('f-lounge-rear-1', 'f-lounge', 'rear', 600, 1500),
        window('f-lounge-rear-2', 'f-lounge', 'rear', 5300, 1500),
        opening('f-bed4-door', 'f-bed4', 'right', 3200, 900, 'door', 2400),
        window('f-bed4-front', 'f-bed4', 'front', 1500, 1800),
        window('f-bed4-west-1', 'f-bed4', 'left', 900, 1500),
        window('f-bed4-west-2', 'f-bed4', 'left', 3300, 1500),
        opening('f-bath4-door', 'f-bath4', 'front', 1800, 900, 'door', 2100),
        window('f-bath4-west', 'f-bath4', 'left', 800, 1000, 1500, 900),
        opening('f-bed3-door', 'f-bed3', 'left', 2800, 900, 'door', 2400),
        window('f-bed3-east-1', 'f-bed3', 'right', 900, 1500),
        window('f-bed3-east-2', 'f-bed3', 'right', 3300, 1500),
        opening('f-dress3-door', 'f-dress3', 'rear', 1200, 900, 'door', 2400),
        window('f-dress3-front', 'f-dress3', 'front', 1000, 1300),
        opening('f-bath3-door', 'f-bath3', 'left', 900, 900, 'door', 2100),
        window('f-bath3-east', 'f-bath3', 'right', 900, 1200, 1500, 900),
    ]
    plan = dict(schema='floorforge.custom-plan/1', units='mm', wallThickness=230, facadeStyle='heritage-bungalow',
                parkedCar=dict(x=-3300, y=1600),
                floors=[dict(id='floor-0', rooms=g, walls=[], openings=go), dict(id='floor-1', rooms=u, walls=[], openings=uo)],
                stairs=[dict(id='grand-stair', roomIds=['g-stair', 'f-stair'], flightWidth=1100, well=200, landing=1200, tread=280, rotation=90)])
    brief = dict(title=TITLE, width_mm=30480, depth_mm=39624, road_bearing_deg=180, front_mm=13716, rear_mm=6096,
                 left_mm=7620, right_mm=3048, storeys=2, bedrooms=4, attached_baths=4, parking=True, pooja=True,
                 eldercare=False, open_kitchen=False, roof_access=True, vastu='flexible', floor_height_mm=3600,
                 plinth_mm=600, budget_lakh=220, finish='premium', soil='black-cotton',
                 latitude=23.2599, longitude=77.4126, timezone_hours=5.5, solar_date='2026-02-14', solar_hour=16,
                 exterior_theme='tropical_verandah', interior_theme='warm_contemporary')
    return dict(schema='floorforge.project/0.4', brief=brief, customPlan=plan)


def check():
    p = project(); b = generate_layout(fuse(p)); review = validate(b)
    return p, b, review


DESCRIPTION = ('A large 100 × 130 ft G+1 government bungalow recreated from the owner\'s photographs: red comb-frieze parapets, '
               'a grilled entrance verandah beside a corrugated carport, a grand drawing hall and dining hall in teak and cane, '
               'four bedrooms, ceiling fans and 3.6 m ceilings, a big clipped lawn, rose-covered fences, neem, mango and Ashoka trees.')
FLOOR = ('Ground', 'First', 'Roof')


def main():
    p, b, review = check()
    if review.get('errors'):
        raise RuntimeError(json.dumps(review['errors'], indent=2))
    dest = ROOT / 'examples/gallery' / SLUG
    dest.mkdir(parents=True, exist_ok=True)
    (ROOT / 'examples/gallery/briefs' / f'{SLUG}.json').write_text(json.dumps(p, indent=2) + '\n')
    with tempfile.TemporaryDirectory(prefix='ff-bungalow-') as tmp:
        result = run(p, Path(tmp), use_cache=False)
        shutil.copytree(result['path'], dest, dirs_exist_ok=True)
    b = json.loads((dest / 'building.json').read_text())
    v = b['brief']
    rooms = []
    for r in b['spaces']:
        x0, y0, x1, y1 = Polygon(r['clear']).bounds
        rooms.append(dict(id=r['id'], name=r['name'], floor=r['floor'], kind=r['kind'], widthM=round((x1 - x0) / 1000, 3),
                          depthM=round((y1 - y0) / 1000, 3), areaM2=r['area_m2'],
                          **({'wallPaint': r['wallPaint']} if r.get('wallPaint') else {}),
                          **({'floorFinish': r['floorFinish']} if r.get('floorFinish') else {})))
    spec = dict(title=TITLE, planHash=b['planHash'], style='Heritage Bungalow',
                orientation='South road/front · west carport and side garden · east service lane · north rear garden',
                plotFt=[100, 130], setbacksFt=dict(front=45, rear=20, west=25, east=10), buildableFt=[65, 65],
                wallThicknessMm=230, floorHeightM=v['floor_height_mm'] / 1000, plinthMm=v['plinth_mm'], rooms=rooms,
                landscape=sorted({f['kind'] for f in b['exterior']['landscape']['features']}))
    (dest / 'specifications.json').write_text(json.dumps(spec, indent=2) + '\n')
    lines = [f'# {TITLE}', '', spec['orientation'], '', DESCRIPTION, '',
             '## Measurements', '',
             'Plot: 100 × 130 ft (30.480 × 39.624 m). Setbacks: front 45 ft, rear 20 ft, west 25 ft, east 10 ft. '
             'Buildable envelope and house footprint: 65 × 65 ft (19.812 × 19.812 m).',
             'Walls: 230 mm brick. Floor-to-floor height: 3.6 m (clear ceilings about 3.44 m). Plinth: 600 mm, reached by '
             'Kota-stone steps at every outside door. Ground + first floor, with a roof terrace reached by the stair headhouse.', '',
             '| Floor | Space | Clear width × depth (m) | Clear width × depth (ft) | Area (m²) | Walls | Floor |',
             '|---|---|---|---|---|---|---|']
    for r in rooms:
        lines.append(f"| {FLOOR[min(r['floor'], 2)]} | {r['name']} | {r['widthM']:.3f} × {r['depthM']:.3f} | "
                     f"{r['widthM'] / .3048:.2f} × {r['depthM'] / .3048:.2f} | {r['areaM2']:.2f} | "
                     f"{r.get('wallPaint', '—').replace('-', ' ')} | {r.get('floorFinish', '—').replace('-', ' ')} |")
    lines += ['', '## The house', '',
              '- **Facade.** Blush lime render with a red comb frieze (a raised red coping with stripes hanging from it) on every '
              'parapet, the terraces and the stair headhouse; a red-oxide plinth; white PVC rain-water pipes with heads.',
              '- **Windows.** Steel windows with small panes and a top ventilator behind dark brick-bond grilles on the ground floor, '
              'sloping sheet sunshades on angle brackets, printed cotton curtains on brass rods inside. Wet rooms have obscured glass.',
              '- **Entrance verandah.** Open brick-bond steel grille bays over a mint-green dado, a grille entrance door with a steel '
              'kick plate and tower bolt, a side grille door to the carport and paired teak doors with mesh shutters into the drawing hall.',
              '- **Rooms.** A 7.4 × 6.7 m drawing hall and a 7.4 × 5.3 m dining hall in white marble with a dark inlay band, joined by '
              'segmental arches to the stair hall; distemper-painted walls (sky blue, pista, peach, lilac, mint, cream, powder pink), '
              'moulded cornices, teak door architraves, ceiling fans, a brass chandelier and lanterns, tube lights in the bedrooms.',
              '- **Furniture.** Slatted teak sofa sets and a diwan with bolsters, a glass-fronted showcase, a radio table, a teak dining '
              'table with cane chairs, a single-door refrigerator, teak double beds with bedspreads, Godrej-style steel almirahs, '
              'dressing tables, aaram-kursi easy chairs, an officer\'s desk, a cane lounge with a carrom board, a jhoola on the rear '
              'verandah, a clay matka, monobloc chairs and moodhas, a charpai and clotheslines on the terraces.',
              '- **Outside.** A corrugated-sheet carport on banded red and black posts, a sheet canopy over the east service lane, a '
              'bamboo chick pergola on the front terrace, a water tank and dish on the headhouse, desert coolers on bracket stands.',
              '- **Garden.** Hexagonal paver drive and paths edged with a painted yellow band, rows of red and pink pots and tiered '
              'plant stands, a large hedged lawn with monobloc chairs under a great neem, rose and lily beds with saw-tooth brick '
              'edging, rose-covered mesh fences, Ashoka spires at the gate, mango and Araucaria trees, a kitchen garden, a tulsi '
              'chaura, a garden swing and a rendered compound wall carrying green shade net between red gate pillars with globe lamps.',
              '', '## Open and edit', '',
              f'In FloorForge choose Sample projects → {TITLE} → Open project & all views. The 3D view, walkthrough, drawings, '
              'DXF, GLB and IFC exports all come from the same model. Furniture groups can be moved in the room editor.',
              '', 'Preliminary visual and planning proposal: not structural, regulatory, horticultural or MEP advice. '
              'The sun study uses an illustrative central-India location until a real site is entered.',
              '', 'Plan hash: ' + b['planHash']]
    (dest / 'DESIGN_GUIDE.md').write_text('\n'.join(lines) + '\n')
    manifest = json.loads((dest / 'manifest.json').read_text())
    for name in ('specifications.json', 'DESIGN_GUIDE.md'):
        manifest['files'][name] = hashlib.sha256((dest / name).read_bytes()).hexdigest()
    (dest / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    files = {name: (dest / name).read_bytes() for name in manifest['files']}
    files['manifest.json'] = (dest / 'manifest.json').read_bytes()
    (dest / 'FloorForge-export.zip').write_bytes(deterministic_zip(files))

    catalog = ROOT / 'examples/gallery/catalog.json'
    items = [s for s in json.loads(catalog.read_text()) if s['id'] != SLUG]
    # Right after the owner's own projects at the head of the gallery.
    at = next((i for i, s in enumerate(items) if not s['id'].startswith('my-desired-home')), len(items))
    items.insert(at, dict(id=SLUG, title=TITLE, description=DESCRIPTION, style='Heritage Bungalow', directory=f'gallery/{SLUG}',
                          bedrooms=v['bedrooms'], storeys=b['storeys'], widthFt=100, depthFt=130, roofAccess=bool(b.get('rooftop')),
                          planHash=b['planHash'], hasSpecifications=True))
    catalog.write_text(json.dumps(items, indent=2) + '\n')
    print(json.dumps({'path': str(dest), 'planHash': b['planHash'], 'review': review.get('status')}))


if __name__ == '__main__':
    if sys.argv[1:] == ['--check']:
        p, b, review = check()
        print(json.dumps({'status': review.get('status'), 'warnings': [w['code'] for w in review.get('warnings', [])]}, indent=1))
    else:
        main()
