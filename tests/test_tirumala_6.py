"""Design regressions that a successful export alone cannot detect."""
import json

from shapely.geometry import Polygon, Point, box
from floorforge.sample_projects import sample_file
from floorforge.plan_geometry import geometry


def read(name):
    return json.loads(sample_file('tirumala-6', name).read_text())


def test_care_route_and_room_programme():
    b=read('building.json')
    rooms={room['id']:room for room in b['spaces']}
    assert {r['id'] for r in rooms.values() if r['floor']==1 and r['kind']=='bedroom'}=={'west-suite','garden-suite'}
    assert rooms['library']['kind']=='study' and rooms['library']['floor']==1
    assert 32.8 < rooms['leisure-hall']['area_m2'] < 33.1 and rooms['leisure-hall']['floor']==2
    doors=[set(o['connects']) for o in b['openings'] if o['kind']!='window']
    assert {'caregiver','care-bath'} in doors and {'living','care-bath'} not in doors
    assert {'icu','verandah'} in doors and {'caregiver','verandah'} in doors
    assert {'east-porch','drawing'} in doors and {'wash','kitchen'} in doors
    assert b['planning']['lowerPorchMm']==0


def test_openings_and_stair_arrival_at_actual_floor_plates():
    b=read('building.json')
    rooms={room['id']:room for room in b['spaces']}
    court=Polygon(rooms['garden']['polygon']).buffer(-2)
    shift=304.8+120
    for floor in (1,2):
        plate=geometry(b['floor_plates'][floor]['regions'])
        assert plate.covers(court) if floor==2 else plate.intersection(court).area<1
        assert plate.covers(Point(5155,8350+shift))
        last=b['stairs'][floor-1]['flights'][-1]
        assert last['bounds']==[4850,7800+shift,5150,8900+shift] and last['top']==3508*floor
        assert not plate.covers(Point(5000,8350+shift))

    scene=read('scene.json')
    seats={n['owner'].split('-')[2] for n in scene['nodes'] if n['owner'].startswith('cinema-seat-')}
    assert not seats
    assert len({n['id'] for n in scene['nodes']})==len(scene['nodes'])


def test_perimeter_is_continuous_except_at_the_two_reference_gates():
    from shapely.ops import unary_union
    from shapely.geometry import LineString
    b=read('building.json')
    boundary=b['siteBoundary']
    reference=[o for o in read('ground-reference.json')['openings'] if o['kind']=='gate']
    assert len(reference)==len(boundary['gates'])==2
    occupied=unary_union([Polygon(w['polygon']) for w in b['walls'] if w['floor']==0]+
                         [Polygon(r['polygon']) for r in boundary['runs']]+
                         [box(*[p['bounds'][i] for i in (0,1,3,4)]) for p in boundary['parts'] if '-jamb-' in p['id']])
    perimeter=Polygon(b['plot']).boundary
    measured=[]
    for source,gate in zip(reference,boundary['gates']):
        lo,hi=sorted((40-p[1])*304.8 for p in [source['a'],source['b']])
        assert abs(lo-gate['x0_mm'])<.001 and abs(hi-gate['x1_mm'])<.001
        opening=LineString([(lo,0),(hi,0)])
        assert occupied.intersection(opening).length<.01
        measured.append(opening)
    assert perimeter.difference(unary_union([occupied,*measured]).buffer(.001)).length<.01


def test_gate_leaves_and_finishes_reach_the_walkthrough():
    scene=read('scene.json')
    nodes={n['id']:n for n in scene['nodes']}
    walk,car=scene['gate_model']
    assert walk['parts'][0]['slide'][0]>walk['width']
    assert len(car['parts'])==2 and car['parts'][0]['angle']==-car['parts'][1]['angle']
    for motion in [*walk['parts'],*car['parts']]:
        assert all(nodes[i]['role']=='gate' for i in motion['ids'])
    assert scene['materials']['ivory-vitrified']['tile_m']==[3.2,1.6]
    assert scene['materials']['smoked-oak']==scene['materials']['t5-door-teak']


def test_exterior_walk_starts_within_reach_of_the_correct_gate_in_the_shared_colony():
    from math import atan2, degrees, hypot
    s=read('scene.json')
    previous=json.loads(sample_file('tirumala-5','scene.json').read_text())
    for layer in ('roads','north_colony_garden','east_basketball_court','north_frontage_utilities',
                  'northwest_feeder_cabinets','adjoining_south_and_west'):
        assert s['context'][layer]==previous['context'][layer]
    gate=next(g for g in s['gate_model'] if g['id']=='east-walk-gate')
    x,y,z=s['walk']['arrival']['position']
    dx=gate['start'][0]+gate['width']/2-x
    dy=gate['start'][1]-y
    assert y<0 and z<0 and hypot(dx,dy)<2.1
    assert abs(s['walk']['arrival']['yaw_deg']-degrees(atan2(-dx,dy)))<10
    assert s['walk']['startOnOpen'] and 'colony_overview' in s['cameras']
    for opening in ('g-opening-17','g-opening-10'):
        motion=s['door_motion'][opening]
        assert motion['clearWidth']>1 and len(motion['parts'])==2


def test_long_porches_and_uninterrupted_kitchen_run():
    b=read('building.json')
    rooms={r['id']:Polygon(r['clear']) for r in b['spaces']}
    assert 'car-porch' not in rooms
    porch=rooms['east-porch']
    x,y,X,Y=porch.bounds
    assert abs(Y-y-16*304.8)<.001 and abs(X-x-14*304.8)<.001
    assert abs(porch.area/(304.8**2)-222)<.001  # 2 × 1 ft corner wraps around the ICU.
    ramp=b['vehicleRamp']
    assert (ramp['z1']-ramp['z0'])/(ramp['y1']-ramp['y0'])==.1
    assert ramp['y0']>=-1500 and ramp['z1']==9
    assert not geometry(b['floor_plates'][0]['regions']).covers(Point((ramp['x0']+ramp['x1'])/2,500))
    assert rooms['kitchen'].bounds[2]-rooms['kitchen'].bounds[0]==10*304.8-180
    east=min(w['a'][1] for w in b['walls'] if 'drawing' in w['rooms'] and w['floor']==0)
    assert abs(east-60-4*304.8)<.001
    assert abs(rooms['kitchen'].bounds[3]-rooms['kitchen'].bounds[1]-14*304.8)<.001
    door=next(o for o in b['openings'] if o['id']=='g-opening-20')
    assert door['kind']=='door' and set(door['connects'])=={'kitchen','wash'} and door['width']>=750
    scene=read('scene.json')
    top=next(n for n in scene['nodes'] if n['owner']=='kitchen-platform')
    fridge=next(n for n in scene['nodes'] if n['id']=='north-wall-fridge')
    assert abs(top['scale'][1]-14*.3048)<.000001
    assert fridge['position'][0]-top['position'][0]-(fridge['scale'][0]+top['scale'][0])/2>.85


def test_leisure_hall_and_accessible_upper_decks():
    b=read('building.json')
    rooms={r['id']:r for r in b['spaces']}
    for ident,area in [('east-balcony',96),('sun-terrace',64),('roof-garden',750)]:
        assert abs(rooms[ident]['area_m2']/.09290304-area)<.01
    doors=[set(o['connects']) for o in b['openings'] if o['kind']=='glazed']
    for pair in [('balcony-gallery','east-balcony'),('gallery','sun-terrace')]:
        assert set(pair) in doors
    plate=geometry(b['floor_plates'][2]['regions'])
    for name in ('sun-terrace','east-balcony'):
        deck=Polygon(rooms[name]['polygon'])
        assert plate.intersection(deck).area<1
        assert any(g['owner']==name for g in b['guards'])
    scene=read('scene.json')
    deck=Polygon(rooms['roof-garden']['polygon'])
    assert deck.equals(box(25*304.8,0,40*304.8,50*304.8))
    assert deck.intersection(geometry(b['roofs'][2]['ceiling'])).area==0
    assert deck.difference(plate).area<1
    assert [o['kind'] for o in b['openings'] if 'roof-garden' in o['connects'] and o['kind']!='window']==['door','door']
    assert b['stairs'][2]['roomId']=='stair-lobby'
    landing=Point(scene['walk']['floors'][2]['position'][:2])
    landing_mm=Point(1000*landing.x,1000*landing.y)
    assert Polygon(rooms['stair-lobby']['clear']).contains(landing_mm)
    assert geometry(b['roofs'][2]['ceiling']).covers(landing_mm)
    assert set(next(o for o in b['openings'] if o['id']=='s-opening-0')['connects'])=={'stair-lobby','roof-garden'}
    hall_doors={o['id']:o for o in b['openings'] if o['floor']==2 and o['kind']=='door'}
    assert set(hall_doors)=={'lobby-hall-door','s-opening-0','tv-terrace-door'}
    assert set(hall_doors['lobby-hall-door']['connects'])=={'stair-lobby','leisure-hall'}
    assert all(o['initiallyClosed'] and scene['door_motion'][o['id']]['ids'] for o in hall_doors.values())
    walls={w['id']:w for w in b['walls']}
    glazed=[(walls[o['wall_id']],o) for o in b['openings'] if o['floor']==2 and o['kind']=='window'
            and o['height']==2286]
    assert any(w['a'][0]==w['b'][0]==7620 and 'roof-garden' in o['connects'] for w,o in glazed)
    assert any(w['a'][1]==w['b'][1]==4572 and 'outside' in o['connects'] for w,o in glazed)
    assert all(deck.buffer(-61).intersection(Polygon(w['polygon'])).area<1 for w in b['walls'] if w['floor']==2)
    guards=[g for g in b['guards'] if g['owner']=='roof-garden']
    assert len(guards)==1 and all(g.get('parapet') and g['height']==1100 for g in guards)
    assert all(n['material']=='t5-ivory-render' for n in scene['nodes']
               if n['owner']=='roof-garden' and n['role']!='finish')
    furnishings=[i for i in scene['furniture'] if i['room_id']=='leisure-hall']
    assert sorted(i['kind'] for i in furnishings)==['coffee-table','desk','media-console','office-chair','sofa']
    for item in furnishings:
        assert Polygon(rooms['leisure-hall']['clear']).covers(Polygon([(x*1000,y*1000) for x,y in item['footprint']]))
    nodes={n['id'] for n in scene['nodes']}
    assert {'family-tv-display','desktop-tower','monitor-display','office-table-top'}<=nodes
    assert not {'screen-stage','projection-screen'}&nodes


def test_north_terrace_supports_clear_doors_and_windows():
    from shapely.geometry import LineString
    b=read('building.json')
    walls={w['id']:w for w in b['walls']}
    columns=[m for m in b['terraceFrame'] if m['kind']=='column']
    assert len(columns)==16
    assert {tuple(m['bounds']) for m in columns if m['floor']==0}=={tuple(m['bounds']) for m in columns if m['floor']==1}
    for post in columns:
        for opening in b['openings']:
            if opening['floor']!=post['floor']:continue
            w=walls[opening['wall_id']]
            axis=LineString([w['a'],w['b']])
            lo=opening['offset']
            aperture=LineString([axis.interpolate(lo),axis.interpolate(lo+opening['width'])])
            assert box(*post['bounds']).distance(aperture)>w['thickness']/2


def test_suite_doors_and_clear_sunlight_path():
    b,scene=read('building.json'),read('scene.json')
    rooms={s['id']:s for s in b['spaces']}
    doors=[set(o['connects']) for o in b['openings'] if o['kind']!='window']
    assert [d for d in doors if 'shared-bath' in d]==[{'shared-bath','suite-entry'}]
    assert {'suite-entry','west-suite'} in doors and {'suite-entry','suite-gallery'} in doors
    assert {'garden-suite','loggia'} in doors and rooms['loggia']['area_m2']>11
    assert 'ensuite' not in rooms and rooms['west-suite']['area_m2']>20
    eye=scene['cameras']['living_rooflight']['position']
    sky=scene['cameras']['living_rooflight']['target']
    def sightline(z):
        t=(z-eye[2])/(sky[2]-eye[2])
        return Point([(a+t*(b-a))*1000 for a,b in zip(eye[:2],sky[:2])])
    for f in (1,2):
        for z in (f*3.508-.157,f*3.508):
            assert not geometry(b['floor_plates'][f]['regions']).intersects(sightline(z))
            assert not geometry(b['roofs'][f-1]['ceiling']).intersects(sightline(z))
    assert geometry(b['roofs'][2]['rooflight']).covers(sightline(3*3.508))
    assert any(n['id']=='living-rooflight-pane' and n['material']=='glass' for n in scene['nodes'])


def test_rectangular_lobby_opaque_guards_and_north_sky():
    b,s=read('building.json'),read('scene.json')
    spaces={r['id']:r for r in b['spaces']}
    lobby=Polygon(spaces['gallery']['clear'])
    assert lobby.equals(box(*lobby.bounds))
    overlook=geometry(next(h['regions'] for h in b['floor_plates'][1]['openings'] if h['id']=='living-lightwell-1'))
    assert overlook.equals(box(*overlook.bounds)) and abs(overlook.area/304.8**2-72.5)<.01
    guards=[g for g in b['guards'] if g['floor']==1 and g['owner']=='gallery']
    assert guards and all(g.get('parapet') for g in guards)
    shaft=geometry(b['roofs'][2]['suiteNorthlight'])
    for surface in (b['floor_plates'][2]['regions'],b['roofs'][1]['ceiling'],b['roofs'][2]['regions'],b['roofs'][2]['ceiling']):
        assert shaft.intersection(geometry(surface)).area<1
    assert Polygon(spaces['west-suite']['clear']).covers(shaft)
    pane=next(n for n in s['nodes'] if n['id']=='suite-northlight-pane')
    assert pane['material']=='glass' and 0<pane['rotation'][1]<1
    indoor=[Polygon(r['polygon']) for r in b['spaces'] if r['floor']==0 and r['enclosed']]
    for plant in s['vegetation']:
        if plant['floor']==-1:
            assert all(not p.covers(Point([v*1000 for v in plant['position'][:2]])) for p in indoor)
