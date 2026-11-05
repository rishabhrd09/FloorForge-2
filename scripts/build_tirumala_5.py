#!/usr/bin/env python3
"""Build the independent Tirumala 5 / Plan A sample; never rebuild its sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from floorforge.pipeline import run, deterministic_zip
from floorforge.tirumala_5 import build_project, REVISION, ICU, KITCHEN, UTILITY, PANTRY, PANTRY_AISLE
from floorforge.tirumala_p11_p12 import render_dimensioned_2d_svg, render_material_overhead_2d_svg, _mm_to_ft_in
from floorforge.tirumala_5_upper import first_svg, second_svg, roof_svg, REVISION as UPPER_REVISION
from floorforge.tirumala_4 import generate_site_context_plan_svg
from shapely.geometry import Polygon

OUT=ROOT/'examples/gallery/tirumala-5'
SOURCE=ROOT/'examples/gallery/tirumala-4'


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')


def main(finalize=False):
    OUT.mkdir(exist_ok=True)
    if not finalize:
        project=build_project()
        dump(ROOT/'examples/gallery/briefs/tirumala-5.json',project)
        with tempfile.TemporaryDirectory(prefix='ff-t5-') as tmp:
            result=run(project,Path(tmp),use_cache=False)
            shutil.copytree(result['path'],OUT,dirs_exist_ok=True)
    b=json.loads((OUT/'building.json').read_text());scene=json.loads((OUT/'scene.json').read_text())
    source=json.loads((SOURCE/'building.json').read_text())
    plan=b['planning']['canonicalPlan']
    void_sqft=Polygon(b['planning']['upperPlan']['void']).area/92903.04
    guest=next(r for r in b['planning']['upperPlan']['rooms'] if r['id']=='u-bedroom')
    second=b['planning']['secondPlan']
    second_rooms={r['id']:r for r in second['rooms']}
    terrace_sqft=second_rooms['s2-terrace']['area_m2']/0.09290304
    landing_sqft=second_rooms['s2-indoor-landing']['area_m2']/0.09290304
    # Measured comparison with the delivered stacked-gallery revision, not an
    # estimate based on rectangular envelopes of these irregular spaces.
    previous_landing_sqft=87.06555781167117
    previous_atrium_landing_sqft=135.89097837917896
    previous_terrace_sqft=583.6450604845654
    landing_gain_sqft=landing_sqft-previous_landing_sqft
    landing_tail_removed_sqft=previous_atrium_landing_sqft-landing_sqft
    skylight=second['skylight']
    aperture_ft=' × '.join(_mm_to_ft_in(v) for v in skylight['clearSizeMm'])
    geom_hash=hashlib.sha256(json.dumps({'ground':plan,'upper':b['planning']['upperPlan'],'second':b['planning']['secondPlan']},sort_keys=True).encode()).hexdigest()
    rooms=[dict(id=r['id'],name=r['name'],floor=r['floor'],kind=r['kind'],
        widthM=(r['bounds'][2]-r['bounds'][0])/1000,depthM=(r['bounds'][3]-r['bounds'][1])/1000,
        widthFtIn=_mm_to_ft_in(r['bounds'][2]-r['bounds'][0]),depthFtIn=_mm_to_ft_in(r['bounds'][3]-r['bounds'][1]),
        areaM2=r['area_m2'],areaSqFt=round(r['area_m2']/0.09290304,1)) for r in b['spaces']]
    spec=json.loads((SOURCE/'specifications.json').read_text())
    spec.update(title='Tirumala 5',id='tirumala-5',projectId='tirumala-5',basedOnSample='tirumala-4',option='Plan A',version=UPPER_REVISION,
        subtitle='G+2 · skylit atrium · guarded second landing · family hall and roof garden',
        description='40 × 50 ft G+2: retained Plan A rooms and stacked indoor stairs, a continuous glazed-roof atrium, a shortened second-floor east gallery with a continuous metal-and-teak end guard, tall east glazing, a wider drawing-room north window and compact solar panels above the family hall.',
        sourceProject='tirumala-4',sourcePlanHash=source['planHash'],sourceVersion=source['planning']['canonicalPlan']['version'],
        currentVersion=UPPER_REVISION,optionLabel='Ivory · limestone · teak · Plan A',
        optionTag='Plan A · 15 ft ICU · Forecourt utility · Under-stair pantry · G+2',
        optionTrade=f'Plan A kitchen, ICU, forecourt washing bay, pantry, stacked stairs and the enlarged first-floor bedroom are retained. Removing the unused second-floor east passage tail reduces the clear landing/gallery from {previous_atrium_landing_sqft:.1f} to {landing_sqft:.1f} sq ft; it remains {landing_gain_sqft:.1f} sq ft larger than the delivered stacked-gallery revision. A continuous metal-and-teak guard closes the shortened end and joins the atrium edge. The coordinated enclosure, atrium and walls previously reduced the roof terrace by {previous_terrace_sqft-terrace_sqft:.1f} sq ft; it remains {terrace_sqft:.1f} sq ft open. The family hall, stairs, first and ground floors, terraces, opaque highest roof and glazed atrium are unchanged by this landing revision.',
        notes=json.loads((OUT/'project.floorforge.json').read_text())['notes'],
        groundGeometryHash=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),
        planHash=b['planHash'],geometryHash=geom_hash,rooms=rooms,upperFloor=b['planning']['upperPlan'],secondFloor=b['planning']['secondPlan'],
        clearanceAudit=[
            dict(zone='Kitchen to living, beside serving top',measuredMm=843.2,measuredFtIn=_mm_to_ft_in(843.2),note='Clear between unchanged serving top and new ICU partition.'),
            dict(zone='Pantry standing aisle',measuredMm=914.4,measuredFtIn='3′',note='Dining shifted 425 mm east; pantry is cabinetry, not a walk-in room.'),
            dict(zone='Open washing bay working depth',measuredMm=771.6,measuredFtIn=_mm_to_ft_in(771.6),note='600 mm deep fixtures; top-loading washer, no front door swing.'),
            dict(zone='Living coffee table to sofa',measuredMm=800,measuredFtIn=_mm_to_ft_in(800),note='Coffee table shifted 400 mm east to open the tested route around dining to the ground stair.'),
        ],planA=scene['planA'])
    spec['facadeRefinement']=scene['facadeRefinement']
    spec['exteriorRefinement']=scene['exteriorRefinement']
    spec['g2Design']=scene.get('g2Addition',second)
    spec['atriumRevision']=dict(
        clearApertureMm=skylight['clearSizeMm'],clearApertureFtIn=aperture_ft,
        apertureAreaSqFt=round(skylight['areaSqFt'],2),
        firstFloorDoubleHeightAreaSqFt=round(void_sqft,2),
        secondLandingAreaSqFt=round(landing_sqft,2),
        secondLandingGainSqFt=round(landing_gain_sqft,2),
        previousAtriumLandingAreaSqFt=round(previous_atrium_landing_sqft,2),
        secondLandingTailRemovedSqFt=round(landing_tail_removed_sqft,2),
        landingTrimComparisonRevision='tirumala-5-g2-skylit-atrium-2026-11-05',
        landingGuard='Continuous visible metal pickets and teak handrail across the shortened east passage end, joining the atrium guard.',
        remainingSecondTerraceAreaSqFt=round(terrace_sqft,2),
        previousSecondTerraceAreaSqFt=round(previous_terrace_sqft,2),
        comparisonRevision='tirumala-5-g2-stacked-gallery-2026-11-05',
        glazing=skylight['glazing'],
        windows='South-facing first- and second-floor windows removed; tall east stair/gallery bays retained or added; drawing north window is one 2400 mm opening.',
        solar='Four compact modules above the opaque second-floor family-hall roof, clear of the atrium; no extra storey.')
    if scene.get('roofEquipment'):
        spec['roofEquipment']=scene['roofEquipment']
    spec['finishRefinement']=scene.get('finishRefinement',scene.get('tirumala5Finish',{}))
    spec['flooringSpecification']['dominantInterior'].update(tileSizeMm=[3200,1600],moduleMm=[3200,1600],moduleIn=[3200/25.4,1600/25.4],finish='Ivory stone-look large slabs, subtle veining and joints')
    spec['floorLevelsMm'].update(second_floor_mm=7016,second_hall_clear_height_mm=3350)
    # Avoid inherited claims about the old room width or removed store.
    spec['careRoomVerification']=dict(boundsMm=ICU,widthMm=4572,depthMm=4085.6,areaSqFt=201.1)
    spec['windowSchedule']=[dict(id=o['id'],floor=o['floor'],widthMm=o['width'],heightMm=o['height'],
        sillMm=o['sill'],style=o.get('window_style','framed glazing')) for o in b['openings'] if o['kind']=='window']
    spec['doorSchedule']=[dict(id=o['id'],floor=o['floor'],rawKind=o['raw_kind'],apertureMm=o['width'],
        apertureFtIn=_mm_to_ft_in(o['width']),heightMm=o['height']) for o in b['openings']
        if o['sill']==0 and o['raw_kind']!='open-passage']
    spec['flooringSpecification']['dominantInterior']['appliesTo']=[r for r in spec['flooringSpecification']['dominantInterior']['appliesTo'] if r!='g-kitchen-store']
    dump(OUT/'specifications.json',spec)
    dump(OUT/'source-plan-data.json',dict(plans=[plan],sourceProject='tirumala-4',sourcePlanHash=source['planHash']))
    ctx=json.loads((SOURCE/'site-context.json').read_text());ctx.update(projectId='tirumala-5',project_id='tirumala-5',sourceProjectId='tirumala-4',sourcePlanHash=source['planHash'],care_room_verification=spec['careRoomVerification'])
    ctx['siteModes']['proposedDescription']=ctx['siteModes']['proposedDescription'].replace('Tirumala 4','Tirumala 5')
    # The colony evidence is inherited; changed interior measurements are recalculated.
    ctx['measuredClearanceAuditMm']=[a for a in ctx['measuredClearanceAuditMm'] if not any(t in a['zone'] for t in ('Room clear dimensions','south side','Living / Dining','Wash gully'))]
    ctx['measuredClearanceAuditMm'] += [
        dict(zone='Home ICU — clear dimensions',measuredMm='4572 × 4085.6',measuredFtIn='15 ft × 13 ft 4⅞ in',status='Plan A geometry'),
        dict(zone='Home ICU — bed south edge to south wall',measuredMm=1457.6,measuredFtIn=_mm_to_ft_in(1457.6),note='Head faces south; furniture projections reduce this envelope span.'),
        dict(zone='Home ICU — foot aisle to north wall',measuredMm=914.4,measuredFtIn='3′',note='Bed ends at 7967.6 mm; room north inner face 8882 mm.'),
    ]+spec['clearanceAudit']
    for camera_group in ('reference_cameras','sightline_cameras'):
        for key,cam in ctx.get(camera_group,{}).items():
            if key in scene['cameras']: ctx[camera_group][key]=scene['cameras'][key]
    dump(OUT/'site-context.json',ctx)
    for name in ('photo-reference-manifest.json','assumptions-register.json'):
        obj=json.loads((SOURCE/name).read_text());obj.update(projectId='tirumala-5',project_id='tirumala-5',inheritedFrom='tirumala-4')
        if 'title' in obj: obj['title']=obj['title'].replace('Tirumala 4','Tirumala 5')
        dump(OUT/name,obj)
    lines=['# Tirumala 5 · Plan A · G+2 · Skylit atrium','',
        'Independent sample derived from the delivered Tirumala 4. Plot: 40 ft north–south × 50 ft east–west. West ↑, North → in the 2D plan.','',
        '| Room / area | Clear bounding span | Net area |','|---|---|---|']
    for r in rooms: lines.append(f"| {r['name']} ({['ground','first','second'][r['floor']]}) | {r['widthFtIn']} × {r['depthFtIn']} | {r['areaSqFt']} sq ft |")
    lines += ['', '## Selected changes','',
        '- ICU: 15 ft × 13 ft 4⅞ in, about 201.1 sq ft. North, east and west limits unchanged; south wall moves 3 ft 9 in south. Recliner now has its head south and feet north, with a 3 ft foot aisle. ICU living glass/wood assembly shifts 150 mm south; veranda assembly shifts 100 mm north. Extra corner gap is infilled; drawing and true rear-lobby doors remain.',
        '- Kitchen: 13 ft 1⅞ in × 10 ft 3⅛ in; the former wash/store strip becomes kitchen. L-counter stays along south and east walls. Cooking fittings move with the south leg; sink remains beneath the east window. No fridge or puja.',
        '- Forecourt utility: 7 ft × 4 ft 6 in, open to sky at the southeast end, with sink, top-loading washer, short worktop and indicative drain. Fixtures are 600 mm deep, leaving 771.6 mm (2 ft 6⅜ in) working depth. Enter from the east forecourt at the north end; no new kitchen door. South opaque ivory wall and ventilated east teak-look screen are 1800 mm high, within boundary thickness.',
        '- Dry pantry: 4 ft 6 in × 2 ft cabinet below the high stair flight, 1800 mm tall. The added stair waist leaves approximately 1962 mm minimum height above the floor over this cabinet, about 162 mm above its top at the lowest end. A 3 ft operating aisle is reserved. Dining shifts 425 mm east. This is cabinet storage, not a walk-in room.',
        '- Kitchen-to-hall opening beside the retained serving top is 843.2 mm (2 ft 9¼ in). This is the narrowest new connection; no claim of wheelchair certification.',
        f'- The kitchen extension retains coordinated roof/terrace coverage. The approved ground rooms remain unchanged. The first-floor gallery retains its {void_sqft:.1f} sq ft open-to-below area. Within it, an aligned {aperture_ft} (3325 × 1725 mm, {skylight["areaSqFt"]:.1f} sq ft) aperture continues through the second-floor slab and highest roof to the glazed rooflight; the full first-floor opening is not a roof aperture.',
        '- The living coffee table moves 400 mm east, opening an 800 mm gap to the sofa and clearing the tested route around dining to the ground stair.',
        '- Ground room dimensions and original ground stair retained. The upper stair follows the same South–West–North footprint, one floor above, reached through the 1100 mm clear indoor passage beside the east glazing. The enclosed second landing and short return connect to the unchanged family hall. Hanging gold-disc pendants and their cords remain removed; ceiling lights remain.',
        f'- North first-floor bedroom: front portion widened one foot south to 11 ft 1⅜ in; rear width 10 ft 1⅜ in and east–west length 16 ft 6⅞ in. Stepped clear area {guest["area_m2"]/0.09290304:.1f} sq ft. Rear wall retained to preserve the 3 ft passage. Small balcony and connector remain removed; large first terrace retained with opaque ivory parapets.',
        f'- Second-floor landing, before → after: the unused east/window-side passage tail is removed, reducing clear landing/gallery floor from {previous_atrium_landing_sqft:.1f} to {landing_sqft:.1f} sq ft ({landing_tail_removed_sqft:.1f} sq ft removed). The remaining landing is {landing_gain_sqft:.1f} sq ft larger than the delivered stacked-gallery revision. A continuous visible metal-picket guard with a teak handrail closes the new end at X=1675 mm, Y=4875–6075 mm, then joins the atrium edge (+X north, +Y west). The stair route and hall access remain open.',
        f'- This landing trim changes only the second-floor passage end. The ground and first floors, all stairs, furnished family hall, terraces, opaque highest roof and atrium/skylight remain unchanged. The open garden terrace remains {terrace_sqft:.1f} sq ft, following the earlier {previous_terrace_sqft-terrace_sqft:.1f} sq ft reduction for the enclosure, rooflight opening and wall allowance. Keep planting at supported edges and walking routes open.',
        '- Rooflight: sloping framed solar-control glazing with a laminated inner pane, raised opaque curb, narrow mullions and an east-side gutter. The curb and drainage sit outside the clear vertical aperture. This is an architectural assembly; final glass build-up, anchorage, waterproofing and drainage need project-specific engineering.',
        '- Windows: south-facing openings on the first and second floors are removed. Tall east-facing stair/gallery bays use 150 mm sills and 2900 mm glazing height. The ground-floor drawing room has one north-facing 2400 mm (7 ft 10½ in) wide × 2400 mm high opening with a 450 mm sill and retained end piers; its veranda entrance and room dimensions remain unchanged.',
        '- Solar: four compact photovoltaic modules sit on the highest opaque roof above the second-floor family hall. They face south on low supports and remain clear of the skylight, terrace routes and stairs. This is roof equipment, not another floor; output, mounting loads and electrical design are not certified by the visualization.',
        '- Interior floors use 3200 × 1600 mm (approximately 10½ × 5¼ ft) ivory slabs. Outdoor variants have matte surfaces; teak joinery, substantial dark window frames, white fascia and timber soffits follow supplied references.',
        '', '## Coordination still needed','',
        'Architectural visualization, not a certified structural design: the additional occupied floor requires an engineer to verify foundations, column and beam continuity, slab and balcony loads, lateral stability, stair support, guard design and saturated terrace planter loads. Final falls, waterproofing, drains and overflow outlets need construction detailing. Road widths and context evidence follow Tirumala 4; unmeasured background geometry remains illustrative.',
        '', f"Plan hash: `{b['planHash']}`",'']
    (OUT/'DESIGN_GUIDE.md').write_text('\n'.join(lines))
    rd=OUT/'renders';rd.mkdir(exist_ok=True)
    if not finalize:
        (rd/'plan-2d-dimensioned.svg').write_text(render_dimensioned_2d_svg(b))
        (rd/'plan-2d-material-overhead.svg').write_text(render_material_overhead_2d_svg(b))
        (rd/'plan-first-floor.svg').write_text(first_svg(b))
        (rd/'plan-second-floor.svg').write_text(second_svg(b))
        (rd/'plan-roof.svg').write_text(roof_svg(b))
        (rd/'site-context-plan.svg').write_text(generate_site_context_plan_svg(b).replace('Tirumala 4','Tirumala 5'))
    catalog_path=ROOT/'examples/gallery/catalog.json';catalog=json.loads(catalog_path.read_text())
    entry=dict(id='tirumala-5',title='Tirumala 5',description=spec['description']+' ICU 15 ft wide; open washing bay and under-stair pantry.',
        style='Ivory · limestone · teak · Plan A',directory='gallery/tirumala-5',basedOnSample='tirumala-4',
        bedrooms=4,storeys=3,widthFt=40,depthFt=50,roofAccess=False,terraceAccess=True,planHash=b['planHash'],hasSpecifications=True)
    catalog=[e for e in catalog if e['id']!='tirumala-5'];catalog.append(entry);dump(catalog_path,catalog)
    manifest=json.loads((OUT/'manifest.json').read_text())
    for f in OUT.rglob('*'):
        if f.is_file() and f.name not in ('manifest.json','FloorForge-export.zip'):
            manifest['files'][str(f.relative_to(OUT))]=hashlib.sha256(f.read_bytes()).hexdigest()
    dump(OUT/'manifest.json',manifest)
    files={n:(OUT/n).read_bytes() for n in manifest['files'] if (OUT/n).is_file()}
    files['manifest.json']=(OUT/'manifest.json').read_bytes()
    (OUT/'FloorForge-export.zip').write_bytes(deterministic_zip(files))
    print(json.dumps(dict(project='tirumala-5',planHash=b['planHash'],output=str(OUT))))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--finalize',action='store_true')
    main(parser.parse_args().finalize)
