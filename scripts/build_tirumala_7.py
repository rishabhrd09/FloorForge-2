"""Build the Tirumala 7 three-floor corner home with 12' x 5' rooflight in FloorForge's custom-plan format."""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from floorforge.pipeline import run
from floorforge.spaces import SPACE_REGISTRY
from floorforge.tirumala_7 import FLOOR_H_MM, FT, PLINTH_MM, WALL_MM, _room_kind_map, local_mm
from floorforge.tirumala_p11_p12 import _browser_numbers

GALLERY = ROOT / 'examples/gallery'
DEST = GALLERY / 'tirumala-7'


def dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def local(x: float, y: float) -> tuple[float, float]:
    pt = local_mm(x, y)
    return (pt[0], pt[1])


def project() -> dict:
    source = json.loads((DEST / 'plan-reference.json').read_text())
    kind_map = _room_kind_map()
    floors = [dict(id=f'floor-{f}', rooms=[], walls=[], openings=[]) for f in range(3)]

    for f_idx, (fkey, prefix) in enumerate((('ground', ''), ('first', 'u_'), ('second', 's_'))):
        f_data = source['floors'][fkey]
        for raw_id, r in f_data['rooms'].items():
            if raw_id in ('prep_counter_zone', 'bedroom_roof_non_walkable') or raw_id.startswith('not_'):
                continue
            sid = prefix + raw_id if not raw_id.startswith(prefix) else raw_id
            kind = kind_map.get(sid, 'foyer')
            x0, x1 = r['x_ft']
            y0, y1 = r['y_ft']
            p0 = local(x0, y0)
            p1 = local(x1, y1)
            poly = box(min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1]))
            verts = [[round(x, 3), round(y, 3)] for x, y in list(poly.exterior.coords)[:-1]]
            floors[f_idx]['rooms'].append({
                'id': sid,
                'name': r.get('name') or r.get('label') or raw_id,
                'kind': kind,
                'polygon': verts,
            })

    base = json.loads((GALLERY / 'briefs/tirumala-6.json').read_text())['brief']
    base.update(
        title='Tirumala 7',
        bedrooms=4,
        storeys=3,
        floor_height_mm=int(FLOOR_H_MM),
        plinth_mm=int(PLINTH_MM),
        roof_access=False,
        style='warm',
        exterior_theme='warm_modern_minimal',
        interior_theme='bright_natural',
    )

    # Reuse the colony site layers from tirumala-6's scene.json (omitting `north_frontage_utilities`
    # and any `shrub_round` entries so zero round green shrub balls spawn along the East/North gates).
    previous_scene = json.loads((GALLERY / 'tirumala-6/scene.json').read_text())
    site_layers = (
        'schema', 'style', 'roads', 'coordinate_system', 'north_colony_garden',
        'east_basketball_court', 'northwest_feeder_cabinets', 'adjoining_south_and_west',
    )
    colony = json.loads(json.dumps({
        key: previous_scene['context'][key]
        for key in site_layers
        if key in previous_scene.get('context', {})
    }))
    if 'northwest_feeder_cabinets' in colony:
        colony['northwest_feeder_cabinets']['hedge_bounds_scene'] = [0, 0, 0, 0]
    if 'north_colony_garden' in colony:
        colony['north_colony_garden']['trees_scene'] = [
            t for t in colony['north_colony_garden'].get('trees_scene', [])
            if 'shrub' not in t.get('species', '')
        ]
    if 'east_basketball_court' in colony:
        colony['east_basketball_court']['screening_trees_scene'] = [
            t for t in colony['east_basketball_court'].get('screening_trees_scene', [])
            if 'shrub' not in t.get('species', '')
        ]
    site_materials = (
        't4-colony-road', 't4-colony-paving', 't4-colony-turf', 't4-colony-wall',
        't4-boundary-coping', 't4-mulch', 't4-chainlink', 't4-garden-timber', 't4-garden-urn',
    )
    colony_materials = {key: previous_scene['materials'][key] for key in site_materials if key in previous_scene.get('materials', {})}

    # East Pedestrian Gate (y_ft: 2.2..5.8) + 13'2" East Sliding Car Gate (y_ft: 7.0..20.2)
    ped_a, ped_b = local(50.0, 5.8)[0], local(50.0, 2.2)[0]
    car_a, car_b = local(50.0, 20.2)[0], local(50.0, 7.0)[0]
    east_gates = [
        ['east-walk-gate', 'pedestrian', min(ped_a, ped_b), max(ped_a, ped_b)],
        ['east-sliding-car-gate', 'vehicle', min(car_a, car_b), max(car_a, car_b)],
    ]

    cp = dict(
        schema='floorforge.custom-plan/1',
        units='mm',
        wallThickness=int(WALL_MM),
        floors=floors,
        stairs=[],
        frontCourt='tiled',
        doorsClosed=False,
        interiorFloor='ivory-vitrified',
        parkedCar={'x': round((40.0 - 11.70) * FT, 2), 'y': round((50.0 - 44.35) * FT, 2)},
        tirumalaMeta={
            'projectId': 'tirumala-7',
            'parkedCarModel': 'honda-city-sedan',
            'planReference': source,
            'colony': colony,
            'colonyMaterials': colony_materials,
            'eastGates': east_gates,
            'eastSlidingVehicleGate': {'x_ft': 50.0, 'y_ft': [7.0, 20.2]},
            'northVehicleGate': {'x_ft': [39.5, 49.5], 'y_ft': 0.0},
            'plinthMm': int(PLINTH_MM),
            'porchDropMm': 220,
            'finishEdition': 'tirumala-7-sage-teal-fluted-teak',
        },
    )

    notes = (
        "Three-floor 50' x 40' north-east corner home set on a 600 mm (2'0\") raised residential plinth above "
        "colony road level, with a stepped-down 22' car porch (-220 mm below the verandah and main ground floor), "
        "dual vehicle access via a 13'2\" east sliding car gate and a 10' NE corner car gate with sloped stone "
        "ramps, and a sleek Honda City sedan parked inside the porch. Features a widened 9'-deep dining hall "
        "(y 24-33 ft) under the 10' x 8' double-height atrium and 13.5' x 8' raised glazed sunroof, a merged "
        "wash/utility alcove and 3' east kitchen gully (x=47-50 ft) accessed from the kitchen south door with a "
        "continuous south wall, a 16' x 9' north verandah with recessed manicured lawn court, a 15' x 15' Home ICU, "
        "and an open-plan kitchen (solid north wall to porch) with an unobstructed dining-to-kitchen sightline, a "
        "wide 2'9\" (840 mm) east-wall quartz platform beneath two east windows, a N-S waterfall quartz center "
        "counter parallel to the east platform near the dining table, and a compact corner refrigerator on the "
        "small 2' west corner wall. First floor steps back to x=47 ft with symmetrical 3.5' atrium "
        "bridges, a 389 sq ft master suite, study/meditation room, shared bath, and medium bedroom. Second floor "
        "steps back to x=44 ft with a 31' x 17' office & TV hall and raised glazed sunroof. All structure, "
        "waterproofing, drainage falls, and MEP/medical services are conceptual only and require licensed "
        "professional engineering design before construction."
    )
    return dict(schema='floorforge.project/0.4', brief=base, customPlan=cp, notes=notes)


def build_tour_html(dest: Path) -> None:
    """Create `examples/gallery/tirumala-7/tour.html` modelled on `tirumala-6/tour.html`."""
    html = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tirumala 7 · Three-floor corner home with full-span atrium sunroof</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f6f3eb;color:#292b24;font:16px/1.5 "DM Sans",system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:clamp(18px,4vw,54px)}header{display:flex;align-items:end;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:1.4rem}h1{font:clamp(38px,6vw,74px)/1 Georgia,serif;font-weight:400;letter-spacing:-.05em;margin:0}p{margin:.4rem 0}a{color:#354b3c;text-underline-offset:4px}.actions{display:flex;align-items:center;gap:1.3rem;flex-wrap:wrap}.action{color:white;background:#334839;text-decoration:none;padding:.7rem 1rem;border-radius:3px}nav{display:flex;gap:.45rem;flex-wrap:wrap;margin:1rem 0}button{border:1px solid #cbc7b9;color:inherit;background:transparent;font:inherit;padding:.45rem .8rem;cursor:pointer;border-radius:3px}button[aria-pressed=true]{background:#353a31;border-color:#353a31;color:white}figure{margin:0}img{width:100%;height:auto;display:block;aspect-ratio:1200/920;object-fit:contain;background:#e4e2d9}figcaption{margin-top:.8rem}strong{font-weight:600}
</style>
<main><header><div><h1>Tirumala 7</h1><p>Three-floor corner home with full-span atrium sunroof · 50′ × 40′ plot</p></div><div class="actions"><a id="walkLink" class="action" href="preview.html">Enter the 3D walkthrough</a><a href="drawings.pdf">Floor drawings</a><a href="model.glb" download>3D model (GLB)</a></div></header>
<nav aria-label="Rendered views"></nav>
<figure><img id="render" width="1200" height="920" src="renders/ground.png" alt="Furnished ground-floor cutaway."><figcaption aria-live="polite" id="caption"></figcaption></figure>
</main>
<script>
const views=[
 ['Ground floor','ground','600 mm raised plinth with stepped-down 22′ car porch (-220 mm), Honda City sedan, 13′2″ east sliding car gate + 10′ NE car gate, 16′ × 9′ verandah lawn court, 15′ × 15′ Home ICU, living hall, widened dining atrium, open-plan kitchen with N–S center counter and compact corner fridge, and wash utility merged into the 3′ east gully.'],
 ['First floor','first','389 sq ft master suite with dressing room and bath, study/meditation room, medium bedroom, symmetrical 3.5′ bridges with solid white opaque balustrades framing the 10′ × 8′ dining atrium, two tall vertical east sunlight windows on the staircase wall, and 526 sq ft shared terrace.'],
 ['Second floor','second','31′ × 17′ office and TV hall with three workstations, lounge sofa and 75″ east-wall TV, 13.5′ × 8′ raised glazed sunroof directly above the dining atrium, and 873 sq ft open terrace.'],
 ['Exterior','exterior','North-east corner view showing the 600 mm raised plinth, stepped-down 22′ car porch with Honda City sedan, 13′2″ east sliding car gate, 10′ NE car gate, 3′ east kitchen setback with east windows, north verandah lawn court, and stepped terraces.'],
 ['East arrival','east_arrival','9 m east colony road arrival showing the 13′2″ east sliding car gate and sloped stone vehicle ramp alongside the east pedestrian gate, with the Honda City sedan inside the stepped-down 22′ car porch.'],
 ['North frontage','north_frontage','North road view across the 10′ NE car gate and sloped ramp, stepped-down car porch, 600 mm house plinth, 16′ × 9′ verandah with manicured north-wall lawn court, and covered entry.'],
 ['Colony view','colony_overview','The 50′ × 40′ north-east corner parcel in the Tirumala colony facing the north garden and east basketball court.'],
 ['Roof terraces','roof_terraces','Elevated view of the first-floor and second-floor stepped terraces and the full-span 13.5′ × 8′ raised glazed sunroof.'],
 ['Kitchen run','kitchen_run','Wide 2′9″ (840 mm) east-wall nano-white quartz platform beneath two east windows, solid north wall, N–S parallel waterfall center counter, compact corner refrigerator, and south wash door opening directly into the merged 3′ east gully.'],
 ['Kitchen from dining','kitchen_from_dining','Spacious, unobstructed open-plan sightline across the widened dining-to-kitchen zone (y=24′ partition) over the N–S waterfall center counter to the sunlit 2′9″ east kitchen platform.'],
 ['Dining double-height','dining_double_height','Spacious dining hall (widened 1′ north to y=24′) under the double-height atrium extending right up to the staircase, crowned by the 13.5′ × 8′ glazed sunroof and 3-ring brushed-gold chandelier.'],
 ['Living hall','living_hall','Core living hall with terracotta velvet sofa, marble coffee table, and 75″ OLED TV on a fluted-teak media wall.'],
 ['Living to ICU','living_to_icu','Clean sightline from the living hall into the 15′ × 15′ Home ICU and across the shifted y=24′ partition into the widened dining and kitchen zone.'],
 ['Home ICU','icu','15′ × 15′ Home ICU with hospital bed facing the complete 55″ west-wall TV, clinical monitor cart, companion recliner, and 7′ north slider to the verandah.'],
 ['Verandah','verandah','16′ × 9′ north verandah featuring a recessed manicured velvet lawn court with honed-travertine coping, stepping pads, and warm LED graze lighting.'],
 ['Drawing room','drawing_room','9′6″ × 14′ drawing room with taupe bouclé sofa, marble coffee table, and sheer/taupe drapery.'],
 ['Master bedroom','master_bedroom','15′ × 14′ ground-floor master bedroom with upholstered headboard, full-height fluted-teak wardrobe, and en-suite bath.'],
 ['Gallery void','gallery_void','First-floor gallery looking across the full-span 10′ × 8′ atrium and sky-lit east bridge with solid white opaque balustrades down to the dining hall.'],
 ['Master suite','master_suite','First-floor master bedroom (389 sq ft suite) with king bed, upholstered foot bench, dressing room, and north curtains.'],
 ['Study / meditation','study_meditation','First-floor study and meditation room with teak work desk, backlit meditation platform, and east terrace slider.'],
 ['Medium bedroom','medium_bedroom','15′ × 11′ first-floor southwest bedroom with west headboard, south wardrobe, solid south boundary wall, and west window.'],
 ['East terrace','east_terrace','First-floor 8′-wide east terrace (outer edge at x=47′) with timber lounge deck and outdoor seating.'],
 ['Office & TV hall','office_tv_hall','31′ × 17′ second-floor office and TV hall with three north workstations, terracotta lounge sofa, and 75″ east-wall OLED TV.'],
 ['North terrace','north_terrace','Second-floor north terrace with timber lounge deck, outdoor sofa, and travertine table.'],
 ['Rooflight','rooflight','Second-floor 13.5′ × 8′ raised laminated-glass sunroof curb with 5×2 structural mullion grid directly above the dining atrium.'],
 ['Stair lobby','stair_lobby','Second-floor stair lobby at the head of the U-turn staircase with solid white opaque balustrade and sunlit east staircase windows below.']
];
const nav=document.querySelector('nav'),image=document.querySelector('#render'),caption=document.querySelector('#caption');
function selectView(index){const [title,id,description]=views[index];document.getElementById('walkLink').href='preview.html#'+id;image.src='renders/'+id+'.png';image.alt=title+'. '+description;caption.textContent=description;Array.from(nav.children).forEach((button,i)=>button.setAttribute('aria-pressed',String(index===i)));}
views.forEach(([name],i)=>{const button=document.createElement('button');button.type='button';button.textContent=name;button.addEventListener('click',()=>selectView(i));nav.append(button)});
function openLinkedView(){selectView(Math.max(0,views.findIndex(view=>view[1]===location.hash.slice(1))))}
window.addEventListener('hashchange',openLinkedView);openLinkedView();
</script></html>"""
    (dest / 'tour.html').write_text(html)


def main() -> None:
    payload = _browser_numbers(project())
    with tempfile.TemporaryDirectory(prefix='tirumala7-') as work:
        result = run(payload, Path(work), use_cache=False)
        # Ensure conceptual structure & waterproofing disclaimer is prominent in REVIEW_BEFORE_USE.txt
        review_txt = Path(work) / 'REVIEW_BEFORE_USE.txt'
        if review_txt.exists():
            txt = review_txt.read_text()
            extra = (
                "\nCONCEPTUAL STRUCTURE & WATERPROOFING NOTE (TIRUMALA 7):\n"
                "- All columns, beams, slab openings (including the 12' x 5' double-height void and raised rooflight\n"
                "  curb), and stepped terrace slabs (x=47 ft on First Floor, x=44 ft on Second Floor) are conceptual.\n"
                "- Structural framing, waterproofing membranes, rooflight upstand flashing, drainage falls, and\n"
                "  Home ICU electrical/medical services require licensed professional engineering design.\n"
            )
            if "CONCEPTUAL STRUCTURE & WATERPROOFING NOTE (TIRUMALA 7)" not in txt:
                review_txt.write_text(txt + extra)
        shutil.copytree(result['path'], DEST, dirs_exist_ok=True)

    build_tour_html(DEST)

    # Save brief without bloating briefs/tirumala-7.json with redundant nested copies if needed,
    # keeping the exact payload that reproduces the same planHash.
    dump(GALLERY / 'briefs/tirumala-7.json', payload)

    catalog = json.loads((GALLERY / 'catalog.json').read_text())
    entry = dict(
        id='tirumala-7',
        title='Tirumala 7',
        description=(
            'Three-floor 50′ × 40′ corner home on a 600 mm raised plinth with a stepped-down 22′ car porch, '
            'dual car gates (13′2″ east sliding + 10′ NE corner) and Honda City sedan, widened dining hall under '
            'a double-height atrium with 13.5′ × 8′ raised glazed sunroof, open-plan kitchen with 2′9″ east quartz '
            'platform, N–S center counter, compact corner fridge and wash area merged into the 3′ east gully, '
            '16′ × 9′ verandah lawn court, 15′ × 15′ home ICU, four bedrooms, meditation study, and office & TV hall.'
        ),
        style='Sage-teal gloss · fluted teak · ivory vitrified',
        directory='gallery/tirumala-7',
        basedOnSample='tirumala-6',
        bedrooms=4,
        storeys=3,
        widthFt=40,
        depthFt=50,
        roofAccess=False,
        terraceAccess=True,
        planHash=result['planHash'],
    )
    dump(GALLERY / 'catalog.json', [i for i in catalog if i['id'] != 'tirumala-7'] + [entry])
    print(f"Built tirumala-7 successfully (planHash={result['planHash']})")


if __name__ == '__main__':
    main()
