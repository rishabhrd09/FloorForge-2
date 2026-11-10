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

    # Reuse the colony site layers from tirumala-6's scene.json
    previous_scene = json.loads((GALLERY / 'tirumala-6/scene.json').read_text())
    site_layers = (
        'schema', 'style', 'roads', 'coordinate_system', 'north_colony_garden',
        'east_basketball_court', 'north_frontage_utilities',
        'northwest_feeder_cabinets', 'adjoining_south_and_west',
    )
    colony = {key: previous_scene['context'][key] for key in site_layers if key in previous_scene.get('context', {})}
    site_materials = (
        't4-colony-road', 't4-colony-paving', 't4-colony-turf', 't4-colony-wall',
        't4-boundary-coping', 't4-mulch', 't4-chainlink', 't4-garden-timber', 't4-garden-urn',
    )
    colony_materials = {key: previous_scene['materials'][key] for key in site_materials if key in previous_scene.get('materials', {})}

    # Pedestrian gate on the PDF's curved east arrival route near the NE corner (y_ft: 3.5..8.0)
    ped_a = local(50.0, 8.0)[0]
    ped_b = local(50.0, 3.5)[0]
    east_gates = [['east-walk-gate', 'pedestrian', min(ped_a, ped_b), max(ped_a, ped_b)]]

    cp = dict(
        schema='floorforge.custom-plan/1',
        units='mm',
        wallThickness=int(WALL_MM),
        floors=floors,
        stairs=[],
        frontCourt='tiled',
        doorsClosed=False,
        interiorFloor='ivory-vitrified',
        parkedCar={'x': round((40.0 - 10.5) * FT, 2), 'y': round((50.0 - 44.5) * FT, 2)},
        tirumalaMeta={
            'projectId': 'tirumala-7',
            'planReference': source,
            'colony': colony,
            'colonyMaterials': colony_materials,
            'eastGates': east_gates,
            'northVehicleGate': {'x_ft': [39.5, 49.5], 'y_ft': 0.0},
            'finishEdition': 'tirumala-7-sage-teal-fluted-teak',
        },
    )

    notes = (
        "Three-floor 50' x 40' north-east corner home with a 12' x 5' double-height rooflight shaft "
        "(x 21-33 ft, y 26-31 ft) aligned vertically over the ground-floor dining area, first-floor "
        "guarded overlook, and second-floor raised glazed rooflight. Ground floor includes a 15' x 17' "
        "Home ICU with a 7' north slider to the verandah and a 5'6\" clear west opening (no door leaf), "
        "caregiver suite, drawing room, living hall, master suite, straight-run 13'6\" east-wall modular "
        "kitchen with work-bay sink and south hob, prep counter, store, wash area, and a 2/9/4 U-turn stair "
        "(18 risers @ 175 mm = 3150 mm floor-to-floor, clear headroom 2775 mm). First floor steps back to "
        "x=47 ft (520 sq ft walkable terrace) with a 389 sq ft master suite, study/meditation room, shared "
        "bath, and medium bedroom. Second floor steps back to x=44 ft (858 sq ft walkable terrace) with a "
        "30' x 18' office & TV hall and raised non-walkable rooflight curb. All structure (columns, beams, "
        "slabs, cantilevers), waterproofing, drainage falls, and MEP/medical services are conceptual only "
        "and require licensed professional engineering design before construction."
    )
    return dict(schema='floorforge.project/0.4', brief=base, customPlan=cp, notes=notes)


def build_tour_html(dest: Path) -> None:
    """Create `examples/gallery/tirumala-7/tour.html` modelled on `tirumala-6/tour.html`."""
    html = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tirumala 7 · Three-floor corner home with rooflight</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f6f3eb;color:#292b24;font:16px/1.5 "DM Sans",system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:clamp(18px,4vw,54px)}header{display:flex;align-items:end;justify-content:space-between;flex-wrap:wrap;gap:1rem;margin-bottom:1.4rem}h1{font:clamp(38px,6vw,74px)/1 Georgia,serif;font-weight:400;letter-spacing:-.05em;margin:0}p{margin:.4rem 0}a{color:#354b3c;text-underline-offset:4px}.actions{display:flex;align-items:center;gap:1.3rem;flex-wrap:wrap}.action{color:white;background:#334839;text-decoration:none;padding:.7rem 1rem;border-radius:3px}nav{display:flex;gap:.45rem;flex-wrap:wrap;margin:1rem 0}button{border:1px solid #cbc7b9;color:inherit;background:transparent;font:inherit;padding:.45rem .8rem;cursor:pointer;border-radius:3px}button[aria-pressed=true]{background:#353a31;border-color:#353a31;color:white}figure{margin:0}img{width:100%;height:auto;display:block;aspect-ratio:1200/920;object-fit:contain;background:#e4e2d9}figcaption{margin-top:.8rem}strong{font-weight:600}
</style>
<main><header><div><h1>Tirumala 7</h1><p>Three-floor corner home with 12′ × 5′ rooflight · 50′ × 40′ plot</p></div><div class="actions"><a id="walkLink" class="action" href="preview.html">Enter the 3D walkthrough</a><a href="drawings.pdf">Floor drawings</a><a href="model.glb" download>3D model (GLB)</a></div></header>
<nav aria-label="Rendered views"></nav>
<figure><img id="render" width="1200" height="920" src="renders/ground.png" alt="Furnished ground-floor cutaway."><figcaption aria-live="polite" id="caption"></figcaption></figure>
</main>
<script>
const views=[
 ['Ground floor','ground','Care suite, 15′ × 17′ Home ICU with 7′ north slider and 5′6″ clear west opening, living hall, dining under the 12′ × 5′ void, straight-run 13′6″ east kitchen and 2/9/4 U-turn stair.'],
 ['First floor','first','389 sq ft master suite with dressing room and bath, 11′ × 12′ study/meditation room, medium bedroom, guarded 12′ × 5′ overlook and 520 sq ft shared terrace.'],
 ['Second floor','second','30′ × 18′ office and TV hall with three-person desk, L-sofa and 100″ TV, raised 12′ × 5′ glazed rooflight and 858 sq ft open terrace.'],
 ['Exterior','exterior','North-east corner view showing the stepped east terraces (x=47′ first floor, x=44′ second floor), north verandah and car porch.'],
 ['East arrival','east_arrival','East pedestrian gate and car porch frontage along the 9 m east road.'],
 ['North frontage','north_frontage','North road view across the 16′ × 9′ decked verandah, covered entry and car porch.'],
 ['Colony view','colony_overview','The 50′ × 40′ north-east corner parcel in the Tirumala colony facing the north garden and east basketball court.'],
 ['Roof terraces','roof_terraces','Elevated view of the first-floor (520 sq ft) and second-floor (858 sq ft) terraces and the raised 12′ × 5′ glazed rooflight.'],
 ['Kitchen run','kitchen_run','13′6″ straight east-wall modular kitchen with high-gloss sage-teal base units, matte-black Gola channels, nano-white quartz worktop, fluted ivory backsplash, smoked glass uppers and full-height ceiling loft.'],
 ['Kitchen from dining','kitchen_from_dining','View from the dining hall past the 4′ × 1′9″ waterfall quartz and fluted-teak prep counter toward the straight-run kitchen and work bay.'],
 ['Dining double-height','dining_double_height','Double-height dining space under the 12′ × 5′ shaft with first-floor frameless glass balustrade, two-storey fluted-teak and marble feature wall, and tiered gold ring chandelier.'],
 ['Living hall','living_hall','18′6″ × 10′ core living hall with terracotta velvet sofa, nested coffee tables and 75″ TV on a fluted-teak media wall.'],
 ['Living to ICU','living_to_icu','Sightline from the living hall through the 5′6″ clear west opening into the 15′ × 17′ Home ICU.'],
 ['Home ICU','icu','15′ × 17′ Home ICU with hospital bed facing the west-wall 75″ TV, medical headwall console, visitor armchair, south bathroom and 7′ north slider to the verandah.'],
 ['Verandah','verandah','16′ × 9′ north verandah connecting the covered entry, Home ICU 7′ glass slider and car porch.'],
 ['Drawing room','drawing_room','9′6″ × 14′ drawing room with north sofa, coffee table, north window and east windows to the covered entry.'],
 ['Master bedroom','master_bedroom','15′ × 14′ ground-floor master bedroom with fluted headboard wall, south and west windows, en-suite bath and west gully door.'],
 ['Gallery void','gallery_void','First-floor family gallery looking across the 12′ × 5′ guarded void down to the dining table below.'],
 ['Master suite','master_suite','First-floor master bedroom (389 sq ft suite) with king bed, upholstered bench, dressing room and north terrace access.'],
 ['Study / meditation','study_meditation','11′ × 12′ first-floor study and meditation room with work desk, bookshelf and meditation mat, opening to the north terrace.'],
 ['Medium bedroom','medium_bedroom','10′6″ × 11′ first-floor southwest bedroom with wardrobe and south/west windows.'],
 ['East terrace','east_terrace','First-floor 8′-wide east terrace (outer edge at x=47′) with planter boxes and outdoor seating.'],
 ['Office & TV hall','office_tv_hall','30′ × 18′ second-floor office and TV hall with three-person north desk, L-shaped lounge sofa and 100″ east-wall TV.'],
 ['North terrace','north_terrace','Second-floor north terrace (858 sq ft continuous L/U terrace) with outdoor lounge and dining zones.'],
 ['Rooflight','rooflight','Second-floor raised 12′ × 5′ non-walkable laminated glass rooflight curb and surrounding 1100 mm guard.'],
 ['Stair lobby','stair_lobby','Second-floor stair lobby at the head of the 2/9/4 U-turn staircase with north glass door to the terrace.']
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
            'Three-floor 50′ × 40′ corner home with a 12′ × 5′ double-height rooflight shaft over dining, '
            'a 15′ × 17′ home ICU opening to a north verandah, a straight-run sage-teal and fluted-teak '
            'modular kitchen, four bedrooms, a meditation study, and a second-floor office & TV hall '
            'wrapped by 520 and 858 sq ft stepped terraces.'
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
