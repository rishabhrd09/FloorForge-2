"""Reproducible expanded east-facing care home; no user builds or other samples changed."""
from pathlib import Path
import sys,json,copy,tempfile,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from shapely.geometry import Polygon,box
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.pipeline import run,deterministic_zip


def room(id,kind,name,x,y,w,d):
    return dict(id=id,kind=kind,name=name,polygon=[[x,y],[x+w,y],[x+w,y+d],[x,y+d]])
def opening(id,room,side,offset,width,kind='cased',height=2400,sill=0):
    return dict(id=id,roomId=room,side=side,offset=offset,width=width,kind=kind,height=height,sill=sill,hinge='start')
def project():
    # x: south -> north; y: east/front -> west/rear. Roof is not an occupied storey.
    W,D=18288,14326
    g=[dict(**room('g-kitchen','kitchen','Modular kitchen · southeast',3174,150,4200,3300),prepStorageWall='rear',kitchenLayout='l-shaped-return'),
       dict(id='g-dining',kind='hall',name='Entry hall',polygon=[[9474,150],[10824,150],[10824,4150],[7524,4150],[7524,1950],[9474,1950]]),
       dict(**room('g-puja','pooja','Open puja alcove',7524,150,1800,1650),altarWall='front'),
       dict(id='g-drawing',kind='drawing-room',name='Drawing room · northeast',polygon=[[10974,150],[15090,150],[15090,5650],[10974,5650]]),
       room('g-stair','stair','Open staircase · south',150,3600,4324,3900),
       dict(id='g-living',kind='living',name='Living and dining hall',diningPosition=[6660,5200],diningOrientation=0,diningLength=1500,diningCounterGap=600,sofaPosition=[10284,4425],sofaOrientation=180,seatingExtension='g-dining',polygon=[[4624,3600],[7374,3600],[7374,4300],[10824,4300],[10824,5800],[11300,5800],[11300,8400],[5750,8400],[5750,7500],[4624,7500]]),
       dict(id='g-veranda',kind='veranda',name='Care veranda · north',polygon=[[11450,5800],[18138,5800],[18138,8400],[11450,8400]],clearAccess=True,finishStyle='warm-stone',gardenBed=[15438,7400,18138,8400],drain=True),
       dict(id='g-bedroom',kind='bedroom',name='Master bedroom · southwest',polygon=[[150,7650],[5600,7650],[5600,11650],[3700,11650],[3700,13276],[150,13276]]),
       dict(id='g-care',kind='care-room',name='Home care room',polygon=[[8500,8550],[15288,8550],[15288,12700],[8500,12700]],reclinerPosition=[12200,10875],tvOffset=-250,careLayout='equipment-left'),
       dict(**room('g-caregiver','bedroom','Caregiver bedroom · rear strip',5950,11050,2400,3126),bedType='single'),
       dict(**room('g-caregiver-bath','bathroom','Caregiver attached toilet',5950,9600,2400,1300),mechanicalVentilation=True),
       dict(**room('g-bath','bathroom','Master attached bathroom',3850,11800,1950,2376),mechanicalVentilation=True),
       dict(id='g-care-court',kind='courtyard',name='Ventilation lightwell',serviceOnly=True,garden=True,glassCover=True,drain=True,polygon=[[5750,8550],[7600,8550],[7600,9450],[5750,9450]]),
       dict(**room('g-court-ledge','veranda','Covered lightwell edge',7600,8550,750,900),clearAccess=True,serviceOnly=True),
       dict(id='g-care-lawn',kind='veranda',name='Care lawn and rear garden path',clearAccess=True,finishStyle='garden-lawn',polygon=[[8500,12850],[15438,12850],[15438,8400],[18138,8400],[18138,14176],[8500,14176]]),
       dict(**room('g-bedroom-airgap','veranda','Rear bedroom ventilation recess',0,13426,3700,900),clearAccess=True,serviceOnly=True,drain=True),
       room('g-kitchen-store','store','Kitchen pantry',1674,150,1350,1850),
       dict(**room('g-wash','drying-yard','Open wash area',1674,2150,1350,1300),drain=True)]
    go=[{**opening('g-dining-east','g-dining','front',2200,1000,'door',2400),'hinge':'end'},
        opening('g-dining-window','g-puja','front',150,1500,'window',450,2200),
        opening('g-entry','g-drawing','front',1800,1200,'entry'),
        opening('g-kitchen-dining','g-kitchen','right',1800,1500,height=3000),
        dict(**opening('g-puja-open-right','g-puja','right',0,1650,height=3000),openSide=True),
        dict(**opening('g-puja-open-rear','g-puja','rear',0,1800,height=3000),openSide=True),
        dict(**opening('g-dining-pier-open','g-dining','left',3375,700,height=3000),openSide=True),
        opening('g-dining-drawing','g-drawing','left',100,900,'door',2100),
        opening('g-dining-living','g-dining','rear',0,3300,height=3000),
        dict(**opening('g-kitchen-serving','g-kitchen','rear',2775,1425,height=2700),servingCounter='full'),
        opening('g-living-stair','g-stair','right',0,3900,height=3000),
        opening('g-bedroom-door','g-bedroom','front',4500,900,'door',2100),
        opening('g-bath-door','g-bath','front',450,900,'door',2100),
        dict(**opening('g-care-living','g-care','front',0,2650,'glazed'),sliding=True),
        dict(**opening('g-care-veranda','g-care','front',4300,2400,'glazed'),sliding=True,slidingPanels=2,stackingSliding=True),
        opening('g-drawing-veranda','g-veranda','front',1250,900,'door',2100),
        opening('g-drawing-veranda-window','g-veranda','front',2550,1000,'window',1500,750),
        opening('g-drawing-parking-window','g-drawing','right',700,3000,'window',1500,750),
        dict(**opening('g-living-veranda','g-veranda','left',0,2600,'door'),timberScreen=True,screenSliding=True,swingRoomId='g-veranda'),
        opening('g-kitchen-east','g-kitchen','front',900,2600,'window',1100,1100),
        opening('g-kitchen-south','g-kitchen','left',300,900,'door',2100),
        opening('g-kitchen-wash','g-kitchen','left',2250,900,'door',2100),
        opening('g-drawing-east','g-drawing','front',150,1400,'window',1800,450),
        {**opening('g-care-caregiver','g-caregiver','right',150,1000,'door',2100),'hinge':'start','swingRoomId':'g-caregiver'},
        {**opening('g-caregiver-toilet','g-caregiver-bath','rear',1000,800,'door',2100),'hinge':'end'},
        opening('g-caregiver-rear-window','g-caregiver','rear',500,1400,'window',1300,1000),
        opening('g-care-garden-window','g-care','rear',3080,3420,'window',1700,600),
        dict(**opening('g-care-lawn-window','g-care','right',200,1000,'window',2400,0),fixed=True),
        opening('g-care-lawn-window-left','g-care','right',2950,1000,'window',2100,300),
        opening('g-bedroom-garden-window','g-bedroom','right',1050,650,'window',1700,650),
        opening('g-caregiver-lightwell-window','g-caregiver-bath','front',250,1100,'window',800,1500),
        dict(**opening('g-caregiver-garden-door','g-caregiver','right',1900,1100,'glazed'),sliding=True),
        opening('g-bedroom-rear-window','g-bedroom','rear',500,2400,'window',1600,800),
        opening('g-stair-window','g-stair','front',50,1274,'window',2500,350)]
    u=[room('u-office','study','Studio and office · southeast',4624,1950,3550,2200),
       dict(id='u-lobby',kind='hall',name='Upper arrival lobby',polygon=[[8324,1950],[10824,1950],[10824,4150],[8324,4150]]),
       dict(id='u-terrace-front',kind='terrace',name='L-shaped open terrace · east and north',clearAccess=True,polygon=[[3174,0],[15090,0],[15090,5800],[10974,5800],[10974,1800],[3174,1800]]),
       dict(**room('u-studio-terrace','terrace','Studio terrace return',3174,1800,1300,1650),clearAccess=True),
       room('u-stair','stair','Open staircase · roof access',150,3600,4324,4800),
       dict(id='u-lounge',kind='hall',name='Overlooking living lobby',polygon=[[4624,4300],[10824,4300],[10824,5300],[6350,5300],[6350,7350],[8800,7350],[8800,8400],[8950,8400],[8950,9550],[7750,9550],[7750,8400],[4624,8400]]),
       dict(id='u-living-void',kind='void',name='Double-height living · open below',polygon=[[6500,5450],[10824,5450],[10824,5800],[11300,5800],[11300,8250],[8950,8250],[8950,7200],[6500,7200]],openToBelow=True),
       dict(id='u-terrace-north',kind='terrace',name='North terrace around daylight garden',clearAccess=True,polygon=[[11450,5800],[18138,5800],[18138,14176],[15438,14176],[15438,8400],[16938,8400],[16938,7400],[15288,7400],[15288,8250],[11450,8250]]),
       dict(**room('u-garden-daylight','void','Open sky above veranda garden',15288,7400,1650,1000),openToBelow=True,openToSky=True,drain=True),
       room('u-bed-south','bedroom','Bedroom 2 · private balcony',150,8550,5450,3000),
       dict(id='u-bedroom-balcony',kind='balcony',name='Bedroom 2 · private rear balcony',clearAccess=True,polygon=[[0,11700],[5600,11700],[5600,11800],[5950,11800],[5950,14326],[0,14326]]),
       dict(**room('u-bath','bathroom','Shared upper bathroom',7750,9700,1200,2802),mechanicalVentilation=True),
       room('u-bed-north','bedroom','Master suite · terrace access',9100,8550,6188,3952)]
    uo=[opening('u-atrium-glass','u-living-void','right',500,2250,'window',2400,450),
        opening('u-office-lobby','u-office','right',700,1000,'door',2100),
        opening('u-lobby-lounge','u-lobby','rear',150,2000,height=3000),
        dict(**opening('u-lobby-terrace','u-lobby','right',250,1800,'glazed'),sliding=True),
        opening('u-lobby-east-window','u-lobby','front',150,2200,'window',2100,300),
        opening('u-stair-lounge','u-stair','right',700,4100,height=3000),
        dict(**opening('u-lounge-terrace','u-lounge','right',100,800,'glazed'),sliding=True),
        opening('u-bed-south-door','u-bed-south','front',4500,900,'door',2100),
        opening('u-bath-door','u-bath','front',100,900,'door',2100),
        opening('u-bed-north-door','u-bed-north','left',100,900,'door',2100),
        dict(**opening('u-bed-north-terrace','u-bed-north','right',450,2400,'glazed'),sliding=True),
        opening('u-office-east','u-office','front',475,2600,'window',2100,300),
        opening('u-office-south','u-office','left',200,1100,'window',1500,750),
        dict(**opening('u-bedroom-balcony-door','u-bed-south','rear',900,2700,'glazed'),sliding=True),
        opening('u-stair-window','u-stair','front',50,1274,'window',2500,350)]
    plan=dict(schema='floorforge.custom-plan/1',units='mm',wallThickness=150,frontCourt='tiled',facadeStyle='warm-layered',entranceStyle='wall-supported',doorsClosed=True,parkedCar=dict(x=17030,y=2600),
              floors=[dict(id='floor-0',rooms=g,walls=[],openings=go),dict(id='floor-1',rooms=u,walls=[dict(id='u-atrium-exterior',a=[11375,5725],b=[11375,8325]),dict(id='u-atrium-exterior-return-a',a=[10899,5375],b=[10899,5725]),dict(id='u-atrium-exterior-return-b',a=[10899,5725],b=[11375,5725])],openings=uo)],
              stairs=[dict(id='south-stair-core',roomIds=['g-stair','u-stair'],flightWidth=1100,well=200,landing=1162,tread=250,rotation=90)])
    p=dict(schema='floorforge.project/0.4',brief=dict(title='My Desired Home',width_mm=18288,depth_mm=16764,road_bearing_deg=90,
       front_mm=2438,rear_mm=0,left_mm=0,right_mm=0,storeys=2,bedrooms=4,parking=True,pooja=True,eldercare=True,
       open_kitchen=True,attached_baths=0,roof_access=True,vastu='moderate',floor_height_mm=3150,
       exterior_theme='modern_tropical',interior_theme='bright_natural'),customPlan=plan,
       notes='East-facing 60 × 55 ft concept. An olive-gold Škoda Kylaq representation occupies the right parking bay with a walking strip beside it. Use Show car / Hide car in the 3D toolbar; the view remembers your choice. Broad aligned 2.4 m-high window heads light the first-floor studio and arrival lobby behind a 1.8 m-deep open front terrace. The front-right 10 ft parking lane beside drawing now continues farther back to the veranda. The 5 ft left lane beside the kitchen ends at the extended staircase enclosure; the 8 ft tiled front court remains. The stair rises south, turns right west at the landing, then right north. Its 1.10 m flights and 1.162 m landings align through the first floor and roof. Tall east-facing glazing overlooks the side corridor; the south wall is solid. Bedroom windows previously facing the side-lane recess move to their rear walls because the expanded stair enclosure occupies that recess. The caregiver door swings into the caregiver bedroom. Boundary-reaching portions are subject to local approval. The master bedroom entry now faces the stair landing; its main bay is 200 mm narrower and its private bathroom is retained. Drawing is a separate 4.116 × 5.500 m room with exactly three doors: the retained front entrance, a small dining door and a small veranda door. There is no door to living. Large parking-facing glazing and a separate veranda window provide views. The home care room is a full 6.788 × 4.150 m rectangle, with no caregiver recess behind the recliner. The straight rear-left caregiver unit has a 2.400 × 3.126 m single bedroom and a 2.400 × 1.300 m attached toilet in line. Its 1 m ICU door is on the head-wall side; the independent 1.1 m sliding garden exit leads along the 1.326 m rear path to the lawn, veranda and outside. The bedroom-side courtyard is now a smaller 1.85 × 0.90 m planted lightwell, with a 0.75 m covered edge beneath the retained upper gallery. Bedroom 1 extends 900 mm toward the stairs and its rear wall moves forward 900 mm, creating a covered rear ventilation recess open along its rear edge. The upper bedroom private balcony slab remains above this recess; the ground-floor recess is still covered. The ground-floor attached bathroom stays fixed. The TV stays in place. Its left window is retained; the right window becomes a single fixed 1 m-wide, 2.4 m-high floor-level pane. Around the corner, the farthest 1.2 m veranda glazing bay becomes solid wall. The remaining two full-height glass doors slide independently along separate tracks and stack in front of that wall, creating coordinated L-shaped glazing with the fixed TV-side pane. The corner pier is retained; glass thickness is visual modelling, not a construction specification. The recliner is 500 mm farther back and 250 mm to the seated person\'s left of the previous centred position. The first two panels of the long left-wall window, nearest the caregiver entrance, are replaced by solid wall; the last three panels remain. The cupboard sits in the corner beside the caregiver entrance. Three visitor chairs are on the recliner\'s right; the left side is reserved for equipment, with the existing equipment table along the new solid wall. The right lawn expands to a 2.7 × 5.776 m garden, using the old caregiver site and the end of the veranda side return; almost its full area is green grass with pots at the perimeter. The main veranda remains 6.688 × 2.600 m, with the living door unchanged and the ICU opening reduced to two wall-stacking glass doors. The living-to-ICU glass opening is still a generous 2.65 m. The rear caregiver exit remains independent of the ICU. Warm matte Jodhpuri sandstone slabs in a restrained honey-buff palette, timber ceiling accents and warm wall lights finish the veranda without adding furniture or changing its access routes. One recliner, three right-side chairs, equipment table and corner cupboard furnish the care room. Living seating and the guarded double-height opening move rearward, with direct connections to dining, stairs, master, care and veranda. The veranda retains its 6.688 × 2.600 m outline. A 2.700 × 1.000 m low garden occupies its outer rear edge, leaving a continuous 1.600 m paved route in front. A 1.650 × 1.000 m open-sky cut above part of the bed has 1.10 m glass guards on the upper terrace, with an approximately 1.20 m outer bypass. The terrace edge has a raised waterproofing curb, a perimeter collection channel and a rainwater pipe; the bed has a drain. These are concept drainage elements requiring construction detailing. The living glass remains 2.60 m wide with two broad sliding panels, approximately 1.21 m clear when open. Warm 900 × 600 mm Jodhpuri sandstone slabs with fine staggered joints finish the veranda; the interior flooring and flush threshold stay unchanged. Low planting keeps the view open, with taller pots at the outer boundary. The sofa remains against the drawing-room divider facing the kitchen and stairs. This partition blocks the garden from the centre seat; dining and the living glass have the garden view. Fabric is gathered above the glazing head because side stacks would extend beyond the room corners. A 1.8 × 1.65 m open puja alcove sits immediately left of the opaque wooden entry door, with the mandir against the east wall below a wide single-pane clerestory. Only the east backing wall and the short full-height kitchen divider remain; both hall-facing sides are completely open without doors or corner posts. A limestone entry feature, timber detailing and warm light integrate the clerestory and wooden entrance into the front elevation. The former projecting hall counter is removed. The kitchen rear wall retains approximately 1.4 m of full-height painting wall followed by a 1.425 m-wide, 950 mm-high serving counter on the same wall line, with an open hatch above and a small end jamb. The modular kitchen has one continuous L-shaped marble worktop under the front window and along the puja-divider wall, with an inset sink, return-wall hob and coordinated upper cupboards. The former rear preparation counter is removed; a standalone fridge sits on that opposite wall with no cupboard above it. The central kitchen aisle remains clear. The compact 1.5 m four-seat dining table runs parallel to the serving counter and moves closer to it, with its light centred above. The sofa backs onto the continuous drawing-room divider, using the open entry-hall edge, and faces the kitchen and stairs; its coffee table moves with it, leaving the centre of the lounge open. Dining stays beside the stairs; the pantry and wash yard remain accessible through the kitchen. Doors and gates start closed and can be opened in the walkthrough. The small lightwell is closed off from the living hall by a plain solid wall, with no door or passage. The narrow ICU window behind the recliner is replaced by plain wall. Windows from Bedroom 1 and the caregiver bathroom, drainage and the ventilated clear-glass canopy are retained for daylight and ventilation. No opaque upper slab or roof covers it. The upper gallery reroutes in front of the lightwell. The first-floor studio and lobby are set back 1.8 m behind the east-facing terrace. The open terrace turns along the north/right side, with direct sliding-door access from the lobby and master suite. The studio is 3.55 × 2.20 m; Bedroom 2 is 5.45 × 3.00 m with a private rear balcony; the master suite is 6.188 × 3.952 m. A continuous guarded gallery connects every room to the existing stairs and overlooks the unchanged living atrium. The shared bathroom remains off the gallery. New internal partitions are concept layouts: final framing and load transfer require structural design. Stone accents, timber soffits and restrained lighting refine the exterior. Bathrooms require designed mechanical ventilation. Side setback fields describe minimum clearance at the boundary-reaching wings. Structural support, boundary permissions, daylight, ventilation and actual equipment clearances require detailed design review. This is a residential care concept, not a clinically specified ICU.')

    p['notes'] += ' The front porch has no freestanding column or projecting sit-out base. A shorter timber canopy uses a wall ledger and brackets; compact front steps leave the right parking approach clear. The black slatted pedestrian gate slides left behind the boundary wall, while the vehicle gate retains two inward-opening leaves. Low boundary lights replace front-court bollards.'

    boards=[]
    for fl in plan['floors']:
        beds=[r for r in fl['rooms'] if r['kind']=='bedroom']
        labels={r['id']:('bedroom-'+str(beds.index(r)+1) if r['kind']=='bedroom' else r['kind']) for r in fl['rooms']}
        rows=[]
        for row in range(4):
            line=[]
            for col in range(4):
                cell=box(col*W/4,row*D/4,(col+1)*W/4,(row+1)*D/4)
                matches=sorted([(Polygon(r['polygon']).intersection(cell).area,r['id']) for r in fl['rooms']],reverse=True)
                line.append(labels[matches[0][1]] if matches[0][0] else '')
            rows.append(line)
        boards.append(rows)
    p['editorState']=dict(mode='custom',guideFloors=boards+[[['']*4 for _ in range(4)]],guideEdited=False,customPlan=copy.deepcopy(plan),useRoomBoard=False)
    return p

def main():
    p=project();b=generate_layout(fuse(p));review=validate(b)
    if review.get('errors'):raise RuntimeError(json.dumps(review['errors'],indent=2))
    dest=ROOT/'examples/gallery/my-desired-home';dest.mkdir(parents=True,exist_ok=True)
    (ROOT/'examples/gallery/briefs/my-desired-home.json').write_text(json.dumps(p,indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='ff-desired-') as tmp:
        result=run(p,Path(tmp),use_cache=False);shutil.copytree(result['path'],dest,dirs_exist_ok=True)
    b=json.loads((dest/'building.json').read_text())
    spec=dict(title='My Desired Home',planHash=b['planHash'],orientation='East road/front · south left · north right · west rear',notes=p['notes'],
              plotFt=[60,55],setbacksFt=dict(east=8,south=0,north=0,west=0),rearSetbackProvisional=True,sideLanesFt=dict(south=5,north=10),sideLaneExtent="South lane ends at staircase; north parking lane ends at veranda. Side setback fields record the minimum at boundary-reaching rear wings.",
              buildableFt=[60,47],rooms=[dict(id=r['id'],name=r['name'],floor=r['floor'],kind=r['kind'],widthM=round((Polygon(r['clear']).bounds[2]-Polygon(r['clear']).bounds[0])/1000,3),depthM=round((Polygon(r['clear']).bounds[3]-Polygon(r['clear']).bounds[1])/1000,3),areaM2=r['area_m2']) for r in b['spaces']])
    (dest/'specifications.json').write_text(json.dumps(spec,indent=2)+'\n')
    lines=['# My Desired Home','',spec['orientation'],'',p['notes'],'',
           '## Measurements','', 'Plot: 60 × 55 ft (18.288 × 16.764 m). Buildable envelope: approximately 60 × 47 ft.',
           'Wall thickness: 150 mm. Floor height: 3.15 m. Ground + first; roof terrace is not another occupied storey.','',
           '| Floor | Space | Clear width × depth (m) | Clear width × depth (ft) | Area (m²) |',
           '|---|---|---|---|---|']
    for r in spec['rooms']:
        lines.append(f"| {('Ground','First')[r['floor']] if r['floor']<2 else 'Roof'} | {r['name']} | {r['widthM']:.3f} × {r['depthM']:.3f} | {r['widthM']/.3048:.2f} × {r['depthM']/.3048:.2f} | {r['areaM2']:.2f} |")
    lines+=['','For L-shaped rooms, width × depth is the overall bounding box, not a rectangle; use the listed polygon area. Roof dimensions are its bounding box; the area excludes the stair headhouse. The care-room veranda has a level sliding glass opening; the living connection is 2.65 m wide. A 1 m door behind the recliner leads directly to the rear caregiver bedroom and its attached toilet. The right parking lane is preserved beside the drawing room until the veranda.',
            '', '## Open and edit','', 'In FloorForge choose Sample projects → My Desired Home → Open project & all views. Use Specifications, Room editor, Cell guide, 2D plans or 3D home. The project selector keeps separate saved working copies on this device. Save project also downloads the editable JSON.',
            '', 'The cell overview summarizes the largest room overlap per cell. It is not a second exact geometry source. Small bathrooms may not appear separately. The exact editor and generated drawings contain every room.',
            '', 'The supplied roof stair is an open inter-floor well with a 3.162 m-long rotated slab opening. Bedrooms 2 and 3, office, overlooking lobby and east/north terraces are upstairs. The living atrium is L-shaped, 4.800 × 2.800 m overall with 1.10 m guards; the lower ceiling and upper slab are cut at this opening. Morning light reaches east-facing rooms; the application sun study uses an illustrative location until a real site is entered.',
            '', 'Plan hash: '+b['planHash']]
    (dest/'DESIGN_GUIDE.md').write_text('\n'.join(lines)+'\n')
    manifest=json.loads((dest/'manifest.json').read_text())
    for name in ('specifications.json','DESIGN_GUIDE.md'):manifest['files'][name]=hashlib.sha256((dest/name).read_bytes()).hexdigest()
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    files={name:(dest/name).read_bytes() for name in manifest['files']};files['manifest.json']=(dest/'manifest.json').read_bytes()
    (dest/'FloorForge-export.zip').write_bytes(deterministic_zip(files))

    catalog=ROOT/'examples/gallery/catalog.json';items=json.loads(catalog.read_text());items=[s for s in items if s['id']!='my-desired-home']
    items.insert(0,dict(id='my-desired-home',title='My Desired Home',description='East-facing 60 × 55 ft home: garden-facing care suite, compact rear caregiver suite and lawn, rear veranda, longer parking approach, separate drawing room with three doors and a double-height family living hall.',style='Your personal project',directory='gallery/my-desired-home',bedrooms=4,storeys=2,widthFt=60,depthFt=55,roofAccess=True,planHash=b['planHash'],hasSpecifications=True))
    catalog.write_text(json.dumps(items,indent=2)+'\n');print(json.dumps({'path':str(dest),'planHash':b['planHash'],'review':review.get('status')}))
if __name__=='__main__':main()
