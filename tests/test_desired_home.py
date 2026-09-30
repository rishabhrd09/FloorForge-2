import json
from pathlib import Path
from shapely.geometry import Polygon,box,LineString
from scripts.build_desired_home import project
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.exterior import apply_exterior_preferences

ROOT=Path(__file__).resolve().parents[1]




def historic_nodes(scene):
    # Restore only the explicitly approved decorative removals when comparing
    # older preservation baselines. A separate check requires them absent now.
    removed=json.loads((ROOT/'tests/fixtures/desired_home_removed_ceiling_decor.json').read_text())
    return scene['nodes']+removed['removed_nodes']


def historic_items(scene,key):
    items=list(scene[key])
    removed=json.loads((ROOT/'tests/fixtures/desired_home_removed_ceiling_decor.json').read_text())
    for entry in removed['removed_'+key]:items.insert(entry['index'],entry['item'])
    return items

def historic_finish(n):
    # The later approved veranda change affects only this surface material.
    if n['id']=='g-veranda/stone-finish':
        assert n['material']=='veranda-jodhpuri'
        return {**n,'material':'porch-limestone'}
    return n

def kitchen_casework_node(n):
    if n.get('owner','').startswith('g-kitchen/modular-kitchen'):return True
    x,y,z=n['position']
    return n.get('owner','').startswith('object-') and n['floor']==0 and n['role'] in ('furniture','detail','wall-tile','fixture') and 3.174<x<7.374 and .15<=y<=3.45 and 0<=z<2.4

def test_requested_direction_dimensions_and_connections():
    p=project();b=generate_layout(fuse(p));assert not validate(b)['errors']
    v=b['brief'];assert (v['width_mm'],v['depth_mm'],v['road_bearing_deg'])==(18288,16764,90)
    assert [v[k] for k in ('front_mm','left_mm','right_mm','rear_mm')]==[2438,0,0,0]
    assert b['storeys']==2 and b['rooftop']['floor']==2
    by={s['id']:s for s in b['spaces']}
    assert len([s for s in b['spaces'] if s['kind']=='bedroom' and s['floor']==0])==2
    assert len([s for s in b['spaces'] if s['kind']=='bedroom' and s['floor']==1])==2
    assert by['g-care']['area_m2']>=26
    for a,c,kind in [('g-care','g-veranda','glazed'),('g-care','g-living','glazed'),('g-kitchen','g-dining','cased'),('g-dining','g-drawing','door'),('g-dining','g-living','cased'),('g-living','g-veranda','door'),('g-drawing','g-veranda','door')]:
        assert any(set(o['connects'])=={a,c} and o['kind']==kind and o['sill']==0 for o in b['openings'])
    assert by['g-kitchen']['polygon'][0]==[3174,150]
    assert by['g-bedroom']['polygon'][0]==[150,7650]
    assert b['stairs'][0]['x']==b['stairs'][1]['x']==150
    assert [s['to_floor'] for s in b['stairs']]==[1,2]
    assert b['floor_plates'][1]['openings']
    assert len(p['editorState']['guideFloors'][0])==4
    assert 'kitchen' in p['editorState']['guideFloors'][0][0]
    assert p['editorState']['guideFloors'][0][3][0].startswith('bedroom')


def test_front_vehicle_court_is_clear_of_boundary_reaching_house():
    b=apply_exterior_preferences(generate_layout(fuse(project())))
    features=b['exterior']['landscape']['features'];drive=next(f for f in features if f['id']=='site-driveway')
    p=Polygon(drive['polygon']);assert p.bounds[0]>14500 and p.bounds[3]>5300 and p.bounds[3]<5800
    assert p.bounds[3]-p.bounds[1]>5500
    assert p.intersection(Polygon(b['footprint'])).area==0
    gate=next(g for g in b['exterior']['landscape']['boundary']['gates'] if g['kind']=='vehicle')
    assert gate['x0_mm']>14500


def test_saved_model_contains_care_furniture_and_matching_editable_rooms():
    root=ROOT/'examples/gallery/my-desired-home';b=json.loads((root/'building.json').read_text());s=json.loads((root/'scene.json').read_text());p=json.loads((root/'project.floorforge.json').read_text())
    assert fuse(p)['planHash']==b['planHash']==s['planHash']
    assert {f['kind'] for f in s['furniture'] if f['room_id']=='g-care'}=={'reclining-bed','care-chair-right','care-chair-right-2','care-chair-right-3','equipment-table','care-cupboard','large-tv'}
    clear=Polygon(next(r for r in b['spaces'] if r['id']=='g-care')['clear']);furn=[f for f in s['furniture'] if f['room_id']=='g-care']
    for f in furn:
        poly=Polygon([[x*1000,y*1000] for x,y in f['footprint']]);assert clear.buffer(.1).covers(poly)
    for i,a in enumerate(furn):
        for c in furn[i+1:]:assert Polygon(a['footprint']).intersection(Polygon(c['footprint'])).area<1e-6
    assert p['customPlan']==p['editorState']['customPlan']


def test_sample_furnishes_the_requested_dining_and_office():
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    assert Polygon(next(f['footprint'] for f in scene['furniture'] if f['kind']=='dining-set' and f['room_id']=='g-living')).area>3.0
    assert any(f['kind']=='kitchen-fridge' for f in scene['furniture'])
    assert any(f['kind']=='desk' and f['room_id']=='u-office' for f in scene['furniture'])
    for rid in ('g-bedroom','g-caregiver','u-bed-south','u-bed-north'):
        assert any(f['kind']=='bed' and f['room_id']==rid for f in scene['furniture'])


def test_open_living_route_keeps_only_the_kitchen_stair_partition():
    from floorforge.scene import opening_polygon
    from shapely.ops import unary_union
    b=generate_layout(fuse(project()));by={s['id']:s for s in b['spaces']}
    assert by['g-kitchen']['area_m2']>9.1
    for oid,width in [('g-kitchen-dining',1500),('g-dining-living',3300),('g-living-stair',3900)]:
        o=next(o for o in b['openings'] if o['id']==oid);w=next(w for w in b['walls'] if w['id']==o['wall_id'])
        assert o['kind']=='cased' and o['sill']==0 and o['height']==w['height']==3000 and o['width']==width
        assert Polygon(opening_polygon(w,o)).area>0
    partition=next(w for w in b['walls'] if set(w['rooms'])=={'g-kitchen','g-stair'})
    assert not any(o['wall_id']==partition['id'] for o in b['openings'])
    assert all(st.get('open_sides')==['right'] for st in b['stairs'])
    assert any(g['owner']=='u-stair' for g in b['guards'])


def test_atrium_is_a_guarded_slab_and_ceiling_hole_with_an_overlooking_lobby():
    from floorforge.plan_geometry import plate,geometry
    from shapely.ops import unary_union
    b=generate_layout(fuse(project()));rooms={s['id']:s for s in b['spaces']}
    void=Polygon(rooms['u-living-void']['polygon'])
    assert 10_000_000<void.area<12_000_000
    assert plate(b,1).intersection(void).area<1
    assert geometry(b['roofs'][0]['ceiling']).intersection(void).area<1
    assert geometry(b['roofs'][1]['ceiling']).covers(void)
    assert Polygon(rooms['g-living']['polygon']).covers(void)
    # The only tall atrium wall is its deliberately authored exterior glazing host.
    assert all(w['id'].startswith('u-atrium-exterior') for w in b['walls'] if 'u-living-void' in w['rooms'])
    guards=[g for g in b['guards'] if g['owner']=='u-living-void']
    assert len(guards)>=3 and all(g['height']==1100 for g in guards)
    assert rooms['u-lounge']['walkable'] and len(rooms['u-lounge']['polygon'])==12
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    sofa=Polygon(next(f['footprint'] for f in scene['furniture'] if f['id']=='g-living/sofa'))
    # Seating now backs onto the drawing-room divider instead of filling the atrium.
    assert sofa.bounds==(9.804,3.25,10.784,5.6)
    editable=next(e for e in scene['editables'] if e['id']=='g-living/sofa')
    assert set(editable['placementRoomIds'])=={'g-living','g-dining'}
    coffee=Polygon(next(f['footprint'] for f in scene['furniture'] if f['id']=='g-living/coffee-table'))
    assert coffee.bounds[2]<sofa.bounds[0]  # Seating faces the kitchen and stairs (-x).


def test_an_actual_door_still_cannot_enter_a_stair_flight():
    import pytest
    from floorforge.model import DesignError
    p=project();o=next(o for o in p['customPlan']['floors'][0]['openings'] if o['id']=='g-living-stair');o.update(kind='door',side='rear',offset=1000,width=900)
    with pytest.raises(DesignError) as err:generate_layout(fuse(p))
    assert any(e['code']=='STAIR_ACCESS' for e in err.value.details['errors'])


def test_care_suite_moves_forward_and_left_with_tv_and_clear_routes():
    from shapely.affinity import scale
    root=ROOT/'examples/gallery/my-desired-home'
    b=json.loads((root/'building.json').read_text());scene=json.loads((root/'scene.json').read_text())
    rooms={r['id']:r for r in b['spaces']}
    care=scale(Polygon(rooms['g-care']['clear']),xfact=.001,yfact=.001,origin=(0,0))
    items={f['kind']:Polygon(f['footprint']) for f in scene['furniture'] if f['room_id']=='g-care'}
    recliner=items['reclining-bed'];cx,cy=recliner.centroid.coords[0]
    assert abs(cx-12.2)<.001 and abs(cy-10.875)<.001
    assert cx>(7.750+15.288)/2 and cy>(8.550+12.502)/2
    assert recliner.bounds[2]-recliner.bounds[0]>recliner.bounds[3]-recliner.bounds[1]
    assert items['large-tv'].centroid.x>cx and abs(items['large-tv'].centroid.y-10.625)<.001
    assert 'care-chair-left' not in items
    assert all(items[k].centroid.y<cy for k in ('care-chair-right','care-chair-right-2','care-chair-right-3'))
    assert items['care-cupboard'].bounds[0]<8.6 and items['care-cupboard'].bounds[3]>12.65
    assert items['care-cupboard'].centroid.y>cy and items['equipment-table'].centroid.y>cy
    # Furniture must leave every care doorway's approach clear, including the new suite.
    from floorforge.scene import opening_polygon
    walls={w['id']:w for w in b['walls']}
    for o in b['openings']:
        if 'g-care' not in o['connects'] or o['kind']=='window':continue
        w=walls[o['wall_id']];a,c=w['a'],w['b'];length=((c[0]-a[0])**2+(c[1]-a[1])**2)**.5
        u=[(c[i]-a[i])/length for i in (0,1)]
        ends=[[(a[i]+u[i]*offset)/1000 for i in (0,1)] for offset in (o['offset'],o['offset']+o['width'])]
        q=LineString(ends).buffer(.6+w['thickness']/2000,cap_style=2).intersection(care)
        assert all(q.intersection(poly).area<.001 for poly in items.values())
    # The TV occupies the solid center wall, between the two north sidelights.
    tv=items['large-tv'].bounds
    for o in project()['customPlan']['floors'][0]['openings']:
        if o['roomId']=='g-care' and o['side']=='right':
            a=care.bounds[1]+o['offset']/1000;c=a+o['width']/1000
            assert c<=tv[1] or a>=tv[3]


def test_caregiver_extension_is_connected_and_stays_inside_the_declared_site():
    p=project();b=generate_layout(fuse(p));rooms={r['id']:r for r in b['spaces']}
    graph=validate(b)['graph']
    assert 'g-caregiver' in graph['g-care'] and 'g-caregiver-bath' in graph['g-caregiver']
    assert rooms['g-caregiver']['area_m2']>=7.5 and rooms['g-caregiver-bath']['area_m2']>=3.0
    old_rear=11278
    extension=Polygon(rooms['g-caregiver']['clear'])
    assert extension.bounds[3]>old_rear and extension.bounds[2]==8350
    assert Polygon(rooms['g-bedroom']['clear']).bounds[3]+150==13426
    assert Polygon(rooms['u-living-void']['clear']).intersection(Polygon(rooms['g-care']['clear'])).area==0
    assert p['brief']['bedrooms']==4 and len([r for r in b['spaces'] if r['kind']=='bedroom'])==4
    assert 'subject to local approval' in p['notes']


def test_dining_entrance_and_tiled_court_are_real_geometry():
    from shapely.ops import unary_union
    root=ROOT/'examples/gallery/my-desired-home';b=json.loads((root/'building.json').read_text());s=json.loads((root/'scene.json').read_text())
    o=next(o for o in b['openings'] if o['id']=='g-dining-east')
    assert o['kind']=='door' and o['sill']==0 and set(o['connects'])=={'g-dining','outside'}
    steps=[q for q in b['entrance_steps'] if q['openingId']==o['id']]
    assert [q['top'] for q in steps]==[-300,-150,0]
    assert all(any(n['id']==q['id'] for n in s['nodes']) for q in steps)
    plot=Polygon(b['plot']);assert all(plot.covers(Polygon(q['polygon'])) for q in steps)
    assert b['planning']['frontCourt']=='tiled'
    assert any(f['id']=='front-tiled-court' for f in b['exterior']['landscape']['features'])
    paving=unary_union([Polygon(f['polygon']) for f in b['exterior']['landscape']['features'] if f['kind'] in ('path','court') and 'polygon' in f])
    assert paving.covers(box(200,-1800,10000,-300))
    assert s['lawns'] and all(min(q[1] for q in lawn['polygon'])>=7.4 for lawn in s['lawns'])  # Rear lawn and new veranda garden; no front-court grass.
    assert not any(f['kind'] in ('plant','planter','tree','hedge') and f.get('position_mm',[0,1])[1]<0 for f in b['exterior']['landscape']['features'])
    # The entry hall stays clear after dining moves beside the stair.
    clear=Polygon([[x/1000,y/1000] for x,y in next(r for r in b['spaces'] if r['id']=='g-dining')['clear']])
    counter=Polygon([[x/1000,y/1000] for x,y in b['built_in_counters'][0]['polygon']])
    assert not any(f['kind']=='dining-set' and f['room_id']=='g-dining' for f in s['furniture'])
    free=clear.buffer(-.4).difference(counter.buffer(.4,join_style=2));walls={w['id']:w for w in b['walls']};portals=[]
    for op in b['openings']:
        if 'g-dining' not in op['connects'] or op['kind']=='window' or op.get('openSide'):continue
        w=walls[op['wall_id']];a,c=w['a'],w['b'];length=LineString([a,c]).length;u=[(c[i]-a[i])/length for i in (0,1)];n=[-u[1],u[0]]
        mid=[(a[i]+u[i]*(op['offset']+op['width']/2))/1000 for i in (0,1)]
        from shapely.geometry import Point
        if clear.distance(Point(*[mid[i]+n[i]*.5 for i in (0,1)]))>clear.distance(Point(*[mid[i]-n[i]*.5 for i in (0,1)])):n=[-q for q in n]
        portals.append(LineString([[(a[i]+u[i]*d)/1000+n[i]*(w['thickness']/2000+.45) for i in (0,1)] for d in (op['offset']+400,op['offset']+op['width']-400)]))
    pieces=[free] if free.geom_type=='Polygon' else list(free.geoms)
    assert any(all(piece.intersects(p) for p in portals) for piece in pieces)


def test_relocated_bathroom_is_private_and_leaves_stairs_open():
    root=ROOT/'examples/gallery/my-desired-home';b=json.loads((root/'building.json').read_text());s=json.loads((root/'scene.json').read_text())
    rooms={r['id']:r for r in b['spaces']};wc=rooms['g-bath']
    assert 'underStair' not in wc and wc['kind']=='bathroom'
    assert Polygon(wc['clear']).bounds==(3850,11800,5800,14176)
    assert not Polygon(rooms['g-stair']['clear']).intersects(Polygon(wc['clear']))
    assert {'wc','vanity'}<={f['kind'] for f in s['furniture'] if f['room_id']=='g-bath'}
    assert validate(b)['graph']['g-bath']==['g-bedroom']
    assert 28_000_000<Polygon(rooms['g-care']['clear']).area<29_000_000
    assert rooms['g-living']['area_m2']>27
    assert any(f['kind']=='sofa' and f['room_id']=='g-living' for f in s['furniture'])


def test_aligned_serving_hatch_is_shared_by_editor_scene_and_exports():
    from floorforge.intent import fuse
    root=ROOT/'examples/gallery/my-desired-home';b=json.loads((root/'building.json').read_text());s=json.loads((root/'scene.json').read_text());p=json.loads((root/'project.floorforge.json').read_text())
    counter=b['built_in_counters'][0]
    assert counter['height']==950 and Polygon(counter['polygon']).bounds==(5949,3300,7374,3750)
    assert set(counter['roomIds'])=={'g-kitchen','g-living'}
    assert next(o for o in p['customPlan']['floors'][0]['openings'] if o['id']=='g-kitchen-serving')['servingCounter']=='full'
    assert any(f['kind']=='serving-counter' and f['room_id']=='g-kitchen' for f in s['furniture'])
    assert any(n['id']==counter['id']+'/top' for n in s['nodes'])
    assert fuse(p)['planHash']==b['planHash']==s['planHash']
    assert 'serving-counter' in (root/'model.ifc').read_text()
    assert not next(o for o in b['openings'] if o['id']=='g-dining-living').get('servingCounter')
    rear=next(w for w in b['walls'] if set(w['rooms'])=={'g-kitchen','g-living'})
    hatch=next(o for o in b['openings'] if o['id']=='g-kitchen-serving')
    assert hatch['wall_id']==rear['id'] and hatch['offset']==1400 and hatch['width']==1425
    assert hatch['height']==2700
    assert 'g-living' not in validate(b)['graph']['g-kitchen']  # A serving hatch is not a walking route.
    from floorforge.scene import opening_polygon
    opening=next(o for o in b['openings'] if o['id']=='g-dining-pier-open')
    pier=next(w for w in b['walls'] if w['id']==opening['wall_id'])
    assert Polygon(pier['polygon']).difference(opening_polygon(pier,opening)).is_empty
    prep=Polygon(next(f['footprint'] for f in s['furniture'] if f['kind']=='kitchen-fridge'))
    assert abs(prep.bounds[3]-3.37)<1e-6 and prep.bounds[1]>2.6
    upper=Polygon(next(f['footprint'] for f in s['furniture'] if f['kind']=='kitchen-upper-storage'))
    assert upper.bounds[0]>6.9 and upper.bounds[3]<1.95 and prep.bounds[2]<5.949
    assert any(n.get('role')=='art' and 4.8<n['position'][0]<5.6 and 3.6<n['position'][1]<3.7 for n in s['nodes'])
    dining=Polygon(next(f['footprint'] for f in s['furniture'] if f['kind']=='dining-set'))
    serving=Polygon(next(f['footprint'] for f in s['furniture'] if f['kind']=='serving-counter'))
    assert abs(dining.bounds[2]-dining.bounds[0]-1.7)<1e-6
    assert not any(f['room_id']=='g-living' and f['kind']=='lounge-chair' for f in s['furniture'])
    sofa=Polygon(next(f['footprint'] for f in s['furniture'] if f['kind']=='sofa' and f['room_id']=='g-living'))
    assert dining.distance(sofa)>=.9-1e-6
    assert .6-1e-6<=dining.distance(serving)<.8  # Clear passage between the ledge and dining chairs.
    assert any(f['kind']=='coffee-table' and f['room_id']=='g-living' for f in s['furniture'])


def test_boundary_extensions_preserve_caregiver_size_and_light_court():
    from floorforge.plan_geometry import plate
    b=generate_layout(fuse(project()));r={s['id']:s for s in b['spaces']}
    assert Polygon(r['g-caregiver']['clear']).bounds==(5950,11050,8350,14176)
    assert Polygon(r['g-bedroom']['clear']).bounds[0]-150==0
    assert 25_000_000<Polygon(r['g-bedroom']['clear']).area<28_000_000
    assert Polygon(r['g-caregiver']['clear']).area==2400*3126
    court=Polygon(r['g-care-court']['clear'])
    assert not r['g-care-court']['roofed']
    assert plate(b,1).intersection(court).area<1
    assert any(o['id']=='g-caregiver-garden-door' and 'g-caregiver' in o['connects'] for o in b['openings'])


def test_service_wing_and_clear_veranda_have_matching_physical_geometry():
    from floorforge.plan_geometry import geometry
    root=ROOT/'examples/gallery/my-desired-home';b=json.loads((root/'building.json').read_text());s=json.loads((root/'scene.json').read_text())
    rooms={r['id']:r for r in b['spaces']};graph=validate(b)['graph']
    assert {'g-wash','g-kitchen-store'}<=set(graph['g-kitchen'])
    assert not rooms['g-wash']['roofed'] and rooms['g-wash']['drain']
    assert geometry(b['roofs'][0]['ceiling']).intersection(Polygon(rooms['g-wash']['clear'])).area<1
    assert any(f['kind']=='wash-basin' and f['room_id']=='g-wash' for f in s['furniture'])
    assert any(f['kind'].startswith('shelves') and f['room_id']=='g-kitchen-store' for f in s['furniture'])
    assert rooms['g-veranda']['clearAccess'] and rooms['g-veranda']['area_m2']>11
    assert not any(f['room_id']=='g-veranda' for f in s['furniture'])
    for oid,width in [('g-care-living',2650),('g-care-veranda',2400)]:
        o=next(o for o in b['openings'] if o['id']==oid)
        assert o['sliding'] and o['sill']==0 and o['width']==width
        assert {n['slidingPanel'] for n in s['nodes'] if n.get('owner')==oid and 'slidingPanel' in n}==set(range(o.get('slidingPanels',3)))


def test_recliner_can_translate_and_turn_onto_the_clear_veranda():
    import math
    from shapely.affinity import rotate,translate,scale
    from shapely.ops import unary_union
    from floorforge.scene import opening_polygon
    root=ROOT/'examples/gallery/my-desired-home';b=json.loads((root/'building.json').read_text());s=json.loads((root/'scene.json').read_text())
    rooms={r['id']:r for r in b['spaces']};items=[f for f in s['furniture'] if f['room_id']=='g-care'];bed=Polygon(next(f['footprint'] for f in items if f['kind']=='reclining-bed'))
    walls={w['id']:w for w in b['walls']};o=next(o for o in b['openings'] if o['id']=='g-care-veranda');w=walls[o['wall_id']]
    portal=scale(Polygon(opening_polygon(w,o,20)),xfact=.001,yfact=.001,origin=(0,0))
    free=unary_union([scale(Polygon(rooms[i]['clear']),xfact=.001,yfact=.001,origin=(0,0)) for i in ['g-care','g-veranda']]+[portal])
    obstacles=[Polygon(f['footprint']) for f in items if f['kind']!='reclining-bed']
    # Fixed/stacked glass takes the first third of the aperture; this route uses the clear two-thirds.
    obstacles.append(box(11.60,8.37,12.81,8.58))
    cx,cy=bed.centroid.coords[0];poses=[]
    for i in range(51):poses.append(translate(bed,xoff=(13.9-cx)*i/50))
    moved=poses[-1]
    for angle in range(0,91,3):poses.append(rotate(moved,angle,origin=(13.9,cy)))
    turned=poses[-1]
    for i in range(101):poses.append(translate(turned,yoff=(7.2-cy)*i/100))
    assert all(free.buffer(.001).covers(q) for q in poses)
    assert all(q.intersection(ob).area<1e-5 for q in poses for ob in obstacles)


def test_partial_side_lanes_remain_until_the_rear_extensions():
    b=apply_exterior_preferences(generate_layout(fuse(project())))
    footprint=Polygon(b['footprint'])
    # Widths are measured from plot boundary to house; walls remain separate.
    assert footprint.intersection(box(0,0,1524,3450)).area<1
    assert footprint.intersection(box(15240,0,18288,3450)).area<1
    rooms={r['id']:Polygon(r['clear']) for r in b['spaces']}
    assert rooms['g-bedroom'].bounds[0]==150
    assert rooms['g-care-lawn'].bounds[2]==rooms['g-veranda'].bounds[2]==18138
    assert rooms['g-drawing'].bounds[3]==5650 and 22_000_000<rooms['g-drawing'].area<23_000_000
    assert rooms['g-kitchen'].area>13_000_000
    assert any(f['id']=='left-service-lane' for f in b['exterior']['landscape']['features'])


def test_rear_care_and_living_remain_connected_to_wider_veranda():
    b=generate_layout(fuse(project()));review=validate(b);r={s['id']:s for s in b['spaces']}
    assert len(r['g-care']['clear'])==4
    assert 28<r['g-care']['area_m2']<29 and r['g-living']['area_m2']>27
    assert r['g-veranda']['area_m2']>17
    assert r['g-caregiver']['area_m2']<10
    assert {'g-living','g-drawing','g-care'}<=set(review['graph']['g-veranda'])
    assert not any(w['code']=='DOOR_SWING_CLASH' for w in review['warnings'])


def test_partition_ensuite_and_reclaimed_rear_hall():
    from floorforge.plan_geometry import geometry,plate
    b=generate_layout(fuse(project()));rooms={r['id']:r for r in b['spaces']};review=validate(b)
    shared=[w for w in b['walls'] if set(w['rooms'])=={'g-drawing','g-living'}]
    assert shared and all(w['height']==3000 for w in shared)
    assert not any(o['wall_id'] in {w['id'] for w in shared} for o in b['openings'])
    assert 'g-living' not in review['graph']['g-drawing']
    assert review['graph']['g-bath']==['g-bedroom']
    living=Polygon(rooms['g-living']['clear'])
    care=Polygon(rooms['g-care']['clear'])
    assert care.equals(box(8500,8550,15288,12700))
    assert living.covers(box(4650,6500,5600,7500))  # Stair-side master approach.
    assert Polygon(rooms['g-care-court']['clear']).covers(box(5750,8550,7600,9450))
    assert care.intersection(living).area==0
    op=next(o for o in b['openings'] if o['id']=='g-living-veranda')
    assert op['timberScreen'] and op['width']==2600 and op['sill']==0
    assert rooms['g-kitchen']['area_m2']>13.8


def test_recliner_orientation_garden_and_three_drawing_doors():
    from floorforge.plan_geometry import plate,geometry
    b=generate_layout(fuse(project()));r={s['id']:s for s in b['spaces']}
    care=Polygon(r['g-care']['clear']);garden=Polygon(r['g-care-court']['clear'])
    assert Polygon(r['g-care-lawn']['clear']).covers(box(8500,12850,18138,14176))
    assert Polygon(r['g-care-lawn']['clear']).covers(box(15438,8400,18138,14176))
    assert plate(b,1).intersection(garden).area<1
    assert geometry(b['roofs'][1]['ceiling']).intersection(garden).area<1
    ops={o['id']:o for o in b['openings']};walls={w['id']:w for w in b['walls']}
    # Facing +x: garden on left (+y), living/veranda on right (-y), solid head wall (-x).
    for oid in ('g-care-living','g-care-veranda'):
        w=walls[ops[oid]['wall_id']];assert w['a'][1]==w['b'][1]==8475
    window=walls[ops['g-care-garden-window']['wall_id']]
    assert window['a'][1]==window['b'][1]==12775
    door=walls[ops['g-care-caregiver']['wall_id']]
    assert door['a'][0]==door['b'][0]==8425
    drawing_doors=[o for o in b['openings'] if 'g-drawing' in o['connects'] and o['kind']!='window']
    assert {o['id'] for o in drawing_doors}=={'g-entry','g-dining-drawing','g-drawing-veranda'}
    assert ops['g-drawing-parking-window']['width']==3000
    assert ops['g-drawing-veranda-window']['kind']=='window'
    # Garden is real visible planting, clear of the front court.
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    assert any(n['id']=='g-care-court/garden-bed' for n in scene['nodes'])
    assert r['g-bedroom']['clear']==[[150,7650],[5600,7650],[5600,11650],[3700,11650],[3700,13276],[150,13276]]


def test_courtyard_and_balcony_preserve_unaffected_authored_spaces():
    old=json.loads((ROOT/'tests/fixtures/desired_home_before_courtyard.json').read_text())
    p=project();assert p['brief']=={**old['brief'],'pooja':True}
    allowed={'g-kitchen','g-dining','g-living','g-bedroom','g-care','g-care-court','u-office','u-lobby','u-terrace-front','u-lounge','u-living-void','u-bed-south','u-bath','g-caregiver','g-caregiver-bath','g-veranda','g-court-ledge','g-stair','u-stair','u-terrace-north'}
    changed_openings={'g-living-veranda','g-dining-living','g-dining-east','g-dining-window','g-kitchen-dining','g-living-stair','g-bedroom-garden-window','g-bedroom-door','g-care-living','g-care-veranda','u-bed-south-door','u-bath-door','u-office-south','g-care-caregiver','g-caregiver-toilet','g-caregiver-veranda-window','g-care-garden-window','g-court-door','g-caregiver-garden-door','g-care-side-garden-window','g-bedroom-court','u-bedroom-court','g-stair-window','u-stair-window'}
    allowed.add('u-bed-north')
    changed_openings.update(o['id'] for o in old['plan']['floors'][1]['openings'] if o['roomId'] not in ('u-stair','u-living-void'))
    changed_openings.add('u-stair-lounge')
    for before,after in zip(old['plan']['floors'],p['customPlan']['floors']):
        new={r['id']:r for r in after['rooms']}
        for r in before['rooms']:
            if r['id'] not in allowed:assert {k:v for k,v in new[r['id']].items() if k not in ('ceilingStyle','guardStyle')}==r
        ops={o['id']:o for o in after['openings']}
        for o in before['openings']:
            if o['id'] not in changed_openings:assert ops[o['id']]==o
        if before['id']=='floor-0':assert before['walls']==after['walls']
        else:assert all(w in after['walls'] for w in before['walls'])
    assert p['customPlan']['stairs'][0]['rotation']==90
    assert p['customPlan']['parkedCar']==old['plan']['parkedCar']


def test_skylit_lightwell_has_no_hall_door_and_remains_uncovered_by_opaque_slabs():
    from floorforge.plan_geometry import plate,geometry
    b=generate_layout(fuse(project()));r={s['id']:s for s in b['spaces']}
    garden=Polygon(r['g-care-court']['clear'])
    assert garden.covers(box(5750,8550,7600,9450))
    assert r['g-care-court']['glassCover'] and r['g-care-court']['drain']
    assert r['g-care-court']['serviceOnly'] and r['g-court-ledge']['serviceOnly']
    assert 'g-care-court' not in validate(b)['graph']
    assert plate(b,1).intersection(garden).area<1
    for roof in b['roofs']:assert geometry(roof['ceiling']).intersection(garden).area<1
    ops={o['id']:o for o in b['openings']}
    assert 'g-living-garden-door' not in ops
    assert not any(o['kind'] in ('door','glazed','opening') and set(o['connects'])=={'g-living','g-care-court'} for o in b['openings'])
    assert set(ops['g-caregiver-lightwell-window']['connects'])=={'g-caregiver-bath','g-care-court'}
    assert set(ops['g-bedroom-garden-window']['connects'])=={'g-bedroom','g-care-court'}
    assert 'g-care-side-garden-window' not in ops
    o=ops['g-bedroom-door'];w=next(w for w in b['walls'] if w['id']==o['wall_id'])
    assert w['a'][1]==w['b'][1]==7575 and set(o['connects'])=={'g-bedroom','g-living'}
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    canopy=next(n for n in scene['nodes'] if n['id']=='g-care-court/glass-canopy')
    assert canopy['material']=='glass'
    assert any(n['id']=='g-care-court/stone-path' for n in scene['nodes'])


def test_front_balcony_wraps_right_terrace_and_retains_window_views():
    b=generate_layout(fuse(project()));r={s['id']:s for s in b['spaces']}
    balcony=Polygon(r['u-terrace-front']['clear'])
    assert balcony.covers(box(3174,0,15090,1200))
    assert balcony.covers(box(10974,0,15090,5650))
    assert r['u-terrace-front']['clearAccess']
    assert any(g['owner']=='u-terrace-front' and g['height']==1100 for g in b['guards'])
    for oid in ('u-office-east','u-lobby-east-window'):
        op=next(o for o in b['openings'] if o['id']==oid)
        assert 'u-terrace-front' in op['connects'] and op['kind']=='window'
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    assert any(n['id']=='u-terrace-front/stone-deck' for n in scene['nodes'])
    # The outdoor bench hugs the outer edge; the continuous walking strip remains clear.
    for item in scene['furniture']:
        if item['room_id']=='u-terrace-front':assert not Polygon(item['footprint']).intersects(box(11,1.8,12.2,5.8))


def test_rear_suite_preserves_other_rooms_and_has_independent_garden_exit():
    old=json.loads((ROOT/'tests/fixtures/desired_home_before_rear_caregiver.json').read_text())
    p=project();changed={'g-kitchen','g-dining','g-bedroom','g-living','g-care','g-caregiver','g-caregiver-bath','g-care-court','g-veranda','g-court-ledge','g-stair','u-stair','u-terrace-north'}
    changed.update(r['id'] for r in old['customPlan']['floors'][1]['rooms'] if r['id'] not in ('u-living-void','u-stair','u-garden-daylight'))
    for before,after in zip(old['customPlan']['floors'],p['customPlan']['floors']):
        new={r['id']:r for r in after['rooms']}
        for r in before['rooms']:
            if r['id'] not in changed:assert r=={k:v for k,v in new[r['id']].items() if k not in ('ceilingStyle','guardStyle')}
    assert all(w in p['customPlan']['floors'][1]['walls'] for w in old['customPlan']['floors'][1]['walls'])
    b=generate_layout(fuse(p));g=validate(b)['graph'];r={r['id']:r for r in b['spaces']}
    assert set(g['g-caregiver'])=={'g-care','g-caregiver-bath','g-care-lawn'}
    assert {'g-veranda','outside'}<=set(g['g-care-lawn'])
    assert r['g-caregiver']['area_m2']<10
    ops={o['id']:o for o in b['openings']};assert set(ops['g-care-caregiver']['connects'])=={'g-care','g-caregiver'}
    assert ops['g-caregiver-garden-door']['width']==1100
    assert Polygon(r['g-care']['clear']).equals(box(8500,8550,15288,12700))
    assert Polygon(r['g-caregiver']['clear']).bounds[::2]==Polygon(r['g-caregiver-bath']['clear']).bounds[::2]
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    assert sum(Polygon(l['polygon']).area for l in scene['lawns'])>12
    # Both TV-side openings retain their horizontal positions and garden sightlines.
    for oid,target_y in [('g-care-lawn-window',8695),('g-care-lawn-window-left',12555)]:
        op=ops[oid];assert op['width']==1000
        assert (op['sill'],op['height'])==((0,2400) if oid=='g-care-lawn-window' else (300,2100))
        line=LineString([(11300,10875),(16800,target_y)])
        w=next(w for w in b['walls'] if w['id']==op['wall_id'])
        wall=LineString([w['a'],w['b']]);hit=wall.intersection(line)
        assert not hit.is_empty
        assert op['offset']<=wall.project(hit)<=op['offset']+op['width']
    rear=ops['g-care-garden-window'];assert rear['width']==3420
    authored=next(o for o in project()['customPlan']['floors'][0]['openings'] if o['id']=='g-care-garden-window')
    assert authored['offset']==3080  # first two 1140 mm panels become wall
    windows=[o for o in project()['customPlan']['floors'][0]['openings'] if o['id'] in ('g-care-lawn-window','g-care-lawn-window-left')]
    centers=[8550+o['offset']+o['width']/2 for o in windows]
    assert sum(centers)/2==(8550+12700)/2==10625


def test_parked_car_and_front_upper_window_keep_rooms_and_access_clear():
    p=project();b=generate_layout(fuse(p));assert not validate(b)['errors']
    car=p['customPlan']['parkedCar'];assert car=={'x':17030,'y':2600}
    # Includes the mirrors: retain a walking strip along the drawing-room wall.
    footprint=box(car['x']-1010,car['y']-2100,car['x']+1010,car['y']+2100)
    assert footprint.bounds[0]-15240>=750
    assert footprint.bounds[3]<5800
    assert footprint.bounds[1]>0  # safely beyond the inward gate swing
    s=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    assert any(n['id']=='parked-car-body' for n in s['nodes'])
    o=next(o for o in b['openings'] if o['id']=='u-lobby-east-window')
    wall=next(w for w in b['walls'] if w['id']==o['wall_id'])
    assert o['floor']==1 and o['kind']=='window' and o['width']==2200 and o['height']==2100
    assert wall['a'][1]==wall['b'][1]==1875
    import pytest
    from floorforge.model import DesignError
    bad=project();bad['customPlan']['parkedCar']={'x':6000,'y':1500}
    with pytest.raises(DesignError):generate_layout(fuse(bad))


def test_rotated_stair_faces_south_then_west_then_north_with_matching_voids():
    from floorforge.stair_geometry import point,footprint,well
    from floorforge.plan_geometry import plate,geometry
    b=generate_layout(fuse(project()));rooms={r['id']:r for r in b['spaces']}
    for st in b['stairs']:
        assert st['rotation']==90
        x,y=st['x'],st['y'];fw=st['flight_width'];land=st['landing_mm']
        path=[point(st,p) for p in [(x+fw/2,y+land),(x+fw/2,y+st['depth']-land/2),(x+st['width']-fw/2,y+st['depth']-land/2),(x+st['width']-fw/2,y+land)]]
        assert path[1][0]<path[0][0] and path[1][1]==path[0][1]
        assert path[2][1]>path[1][1] and path[2][0]==path[1][0]
        assert path[3][0]>path[2][0] and path[3][1]==path[2][1]
        assert Polygon(rooms[st['roomId']]['clear']).covers(footprint(st))
        assert footprint(st).bounds==(150,3600,4474,6000)
        slab=plate(b,1) if st['floor']==0 else geometry(b['rooftop']['slab'])
        assert slab.intersection(well(st)).area<1
    ops={o['id']:o for o in b['openings']};walls={w['id']:w for w in b['walls']}
    for oid in ['g-stair-window','u-stair-window']:
        w=walls[ops[oid]['wall_id']]
        assert w['a'][1]==w['b'][1]==3525
        assert ops[oid]['height']==2500
    assert not any(o['kind']=='window' and walls[o['wall_id']]['a'][0]==walls[o['wall_id']]['b'][0]==75 and any(r in o['connects'] for r in ['g-stair','u-stair']) for o in b['openings'])
    assert ops['g-care-caregiver']['swing']=='g-caregiver'
    from floorforge.review import swing_sector
    sector=swing_sector(ops['g-care-caregiver'],walls[ops['g-care-caregiver']['wall_id']],{r['id']:Polygon(r['clear']) for r in b['spaces']})
    assert sector.intersection(Polygon(rooms['g-care']['clear'])).area<1



def test_puja_dining_and_rear_bedroom_recess_match_approved_changes():
    from floorforge.plan_geometry import plate
    b=generate_layout(fuse(project()));rooms={r['id']:r for r in b['spaces']};ops={o['id']:o for o in b['openings']}
    assert rooms['g-puja']['kind']=='pooja' and rooms['g-puja']['area_m2']==2.97
    partition=[w for w in b['walls'] if set(w['rooms'])=={'g-puja','g-kitchen'}]
    assert partition and sum(LineString([w['a'],w['b']]).length for w in partition)<1900
    assert all(w['height']==3000 for w in partition)
    assert ops['g-kitchen-dining']['width']==1500 and ops['g-kitchen-dining']['kind']=='cased'
    assert ops['g-dining-window']['height']==450 and ops['g-dining-window']['sill']==2200
    assert 'g-puja-door' not in ops and rooms['g-puja']['altarWall']=='front'
    assert ops['g-dining-window']['width']==1500
    from floorforge.scene import opening_polygon
    for side in ('right','rear'):
        o=ops['g-puja-open-'+side];w=next(w for w in b['walls'] if w['id']==o['wall_id'])
        assert o['openSide'] and o['height']==3000
        assert set(o['connects'])=={'g-puja','g-dining'}
        assert Polygon(w['polygon']).difference(opening_polygon(w,o)).area<1
    gap=Polygon(rooms['g-bedroom-airgap']['clear'])
    assert gap.bounds==(0,13426,3700,14326) and rooms['g-bedroom-airgap']['serviceOnly']
    assert plate(b,1).covers(gap)  # Covered recess retained beneath the new private balcony slab.
    assert set(ops['g-bedroom-rear-window']['connects'])=={'g-bedroom','g-bedroom-airgap'}
    assert not any(o['kind']!='window' and 'g-bedroom-airgap' in o['connects'] for o in b['openings'])
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    mandir=Polygon(next(f['footprint'] for f in scene['furniture'] if f['kind']=='mandir' and f['room_id']=='g-puja'))
    assert mandir.bounds[1]<.20 and mandir.bounds[3]<.65
    assert abs(mandir.centroid.x-8.424)<.03  # Centred on the east wall.
    assert not any(n.get('owner')=='g-puja-door' for n in scene['nodes'])
    assert any(n['id']=='g-puja/entry-feature/canopy' for n in scene['nodes'])
    table=Polygon(next(f['footprint'] for f in scene['furniture'] if f['kind']=='dining-set'))
    assert 5<table.centroid.x<7.5 and 4<table.centroid.y<6.5
    assert b['stairs'][0]['x']==b['stairs'][1]['x'] and b['stairs'][0]['y']==b['stairs'][1]['y']


def test_closed_canonical_doors_span_their_openings_and_preserve_inward_swing():
    import math
    import numpy as np
    root=ROOT/'examples/gallery/my-desired-home';b=json.loads((root/'building.json').read_text());s=json.loads((root/'scene.json').read_text())
    walls={w['id']:w for w in b['walls']};nodes={n['id']:n for n in s['nodes']}
    assert b['planning']['doorsClosed']
    for o in b['openings']:
        if o['kind'] not in ('entry','door','glazed') or o.get('sliding') or o.get('timberScreen'):continue
        m=s['door_motion'][o['id']];assert m['ids']
        wall=walls[o['wall_id']];axis=LineString([[x/1000 for x in wall[k]] for k in ('a','b')])
        moving=[nodes[i] for i in m['ids']]
        assert all(axis.distance(__import__('shapely').geometry.Point(n['position'][:2]))<.1 for n in moving)
        assert abs(abs(m['angle'])-math.pi/2)<1e-7
    care=s['door_motion']['g-care-caregiver'];leaf=next(nodes[i] for i in care['ids'] if nodes[i]['owner']=='g-care-caregiver')
    p=np.array(leaf['position'][:2])-care['pivot'][:2];a=care['angle']
    open_x=care['pivot'][0]+math.cos(a)*p[0]-math.sin(a)*p[1]
    assert open_x<care['pivot'][0]  # Into caregiver room, not the ICU.
    assert {g['id'] for g in s['gate_model']}=={'exterior-vehicle-gate','exterior-pedestrian-gate'}
    assert all(g['initial']==0 for g in s['gate_model'])


def test_veranda_garden_has_real_daylight_clear_routes_and_supported_guard():
    from floorforge.plan_geometry import geometry
    b=json.loads((ROOT/'examples/gallery/my-desired-home/building.json').read_text())
    s=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    spaces={r['id']:r for r in b['spaces']}
    hole=Polygon(spaces['u-garden-daylight']['clear'])
    assert hole.area==1650000
    assert geometry(b['floor_plates'][1]['regions']).intersection(hole).area==0
    for roof in b['roofs']:
        assert geometry(roof['regions']).intersection(hole).area==0
        assert geometry(roof['ceiling']).intersection(hole).area==0
    assert geometry(b['rooftop']['slab']).intersection(hole).area==0
    bed=box(*spaces['g-veranda']['gardenBed'])
    assert bed.area==2700000
    route=box(11450,5800,18138,7400)
    assert Polygon(spaces['g-veranda']['clear']).covers(route)
    assert route.intersection(bed).area==0
    upper_route=box(16938,5800,18138,14176)
    assert Polygon(spaces['u-terrace-north']['clear']).covers(upper_route)
    from shapely.ops import unary_union
    guards=unary_union([LineString(g['points']) for g in b['guards'] if g['owner']=='u-terrace-north'])
    assert guards.buffer(1).covers(LineString([(15439,8400),(16938,8400),(16938,7400),(15288,7400),(15288,8249)]))
    assert any(n.get('id')=='u-garden-daylight/collection-channel' for n in s['nodes'])
    assert any(n.get('id')=='g-veranda/bed-drain' for n in s['nodes'])
    assert any(l['id']=='g-veranda/garden-grass' for l in s['lawns'])
    floor=s['materials']['floor'];porch=s['materials']['porch-limestone']
    assert all(floor[k]==porch[k] for k in ('color','texture','params'))
    op=next(o for o in b['openings'] if o['id']=='g-living-veranda')
    assert op['width']==2600 and op['timberScreen']
    panes=[n for n in s['nodes'] if n.get('owner')==op['id'] and n.get('role')=='glass']
    assert not panes
    motion=s['door_motion'][op['id']]
    assert motion['clearWidth']==2.46
    assert len(motion['layers'])==3
    assert s['materials']['insect-mesh']['color']=='#f5f3ed'
    assert len({i for leaf in motion['layers'] for i in leaf['ids']})==sum(len(leaf['ids']) for leaf in motion['layers'])
    for leaf in motion['layers']:
        assert leaf['ids']
        if '/mesh-' in leaf['id']:
            assert 'slide' in leaf and 'angle' not in leaf
            assert abs(__import__('math').hypot(*leaf['slide'][:2])-1.23)<1e-7
        else:assert abs(abs(leaf['angle'])-__import__('math').pi/2)<1e-7


def test_first_floor_redesign_preserves_ground_geometry_and_appearance():
    import hashlib
    from floorforge.plan_geometry import geometry
    old=json.loads((ROOT/'tests/fixtures/desired_home_before_first_floor.json').read_text())
    p=project()
    assert p['brief']==old['brief']
    approved={'g-care-veranda','g-care-lawn-window'}
    def strip_layout(o):return {k:v for k,v in o.items() if k not in ('kitchenLayout','ceilingStyle')}
    def ground(fl):return {**fl,'rooms':[strip_layout(r) for r in fl['rooms']],'openings':[o for o in fl['openings'] if o['id'] not in approved]}
    assert ground(p['customPlan']['floors'][0])==ground(old['customPlan']['floors'][0])
    assert p['customPlan']['stairs']==old['customPlan']['stairs']
    before=generate_layout(fuse(old));after=generate_layout(fuse(p))
    for key in ('spaces','walls','openings','stairs','guards','floor_plates'):
        assert [strip_layout(x) for x in before[key] if x.get('floor')==0 and x['id'] not in approved]==[strip_layout(x) for x in after[key] if x.get('floor')==0 and x['id'] not in approved]
    assert geometry(before['roofs'][0]['ceiling']).equals(geometry(after['roofs'][0]['ceiling']))
    baseline=json.loads((ROOT/'tests/fixtures/desired_home_ground_appearance.json').read_text())
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    def digest(items):return hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    # Roof finishes at the first-floor deck level legitimately follow the revised upper plate.
    # Lock the original ground/site outside the two newly approved ICU openings.
    # Skirting is compared geometrically because boolean cuts reorder mesh vertices.
    corner=json.loads((ROOT/'tests/fixtures/desired_home_before_icu_corner_appearance.json').read_text())
    affected=set(corner['affected'])
    nodes=[]
    for n in historic_nodes(scene):
        if n.get('floor') not in (0,-1) or n['role'] in ('plinth','roof','parapet'):continue
        if n.get('owner') in affected or n['role']=='skirting' or kitchen_casework_node(n):continue
        nodes.append({k:v for k,v in historic_finish(n).items() if k!='id' and not(k=='owner' and v.startswith('object-'))})
    # Baseline is from before the approved kitchen swap; compare all other contents.
    kitchen=json.loads((ROOT/'tests/fixtures/desired_home_before_modular_kitchen.json').read_text())
    assert digest(sorted(nodes,key=lambda x:json.dumps(x,sort_keys=True)))==kitchen['ground_nodes']
    assert digest([x for x in scene['vegetation'] if x.get('floor') in (0,-1)])==baseline['vegetation']
    assert digest([x for x in historic_items(scene,'furniture') if x.get('floor') in (0,-1) and (x['room_id']!='g-kitchen' or x['kind']=='serving-counter')])==kitchen['furniture']
    assert digest([x for x in scene['colliders'] if x.get('floor') in (0,-1)])==json.loads((ROOT/'tests/fixtures/desired_home_before_upper_refinement.json').read_text())['ground_colliders']
    def motion(value):
        if isinstance(value,dict):return {k:motion(v) for k,v in value.items() if k!='ids'}
        if isinstance(value,list):return [motion(v) for v in value]
        return value
    assert digest(motion({k:v for k,v in scene['door_motion'].items() if k.startswith('g-') and k not in approved}))==corner['doors']
    assert all(scene['materials'][k]==v for k,v in baseline['materials'].items())
    from shapely.geometry import shape
    from shapely.ops import unary_union
    for owner,expected in corner['skirting'].items():
        polys=[]
        for n in scene['nodes']:
            if n.get('owner')!=owner or n['role']!='skirting':continue
            mesh=scene['assets'][n['asset']]
            for face in mesh['faces']:
                poly=Polygon([mesh['vertices'][i][:2] for i in face])
                if poly.area>1e-9:polys.append(poly)
        assert unary_union(polys).symmetric_difference(shape(expected)).area<1e-8


def test_first_floor_rooms_lobby_private_balcony_and_continuous_open_terrace():
    from floorforge.plan_geometry import geometry
    b=generate_layout(fuse(project()));r={s['id']:s for s in b['spaces']};graph=validate(b)['graph']
    assert {'u-stair','u-lobby','u-bed-south','u-bed-north','u-bath'}<=set(graph['u-lounge'])
    assert 'u-office' in graph['u-lobby'] and 'u-terrace-front' in graph['u-lobby']
    assert 'u-terrace-north' in graph['u-bed-north']
    assert graph['u-bedroom-balcony']==['u-bed-south']
    assert r['u-bed-north']['area_m2']>r['u-bed-south']['area_m2']>r['u-office']['area_m2']>=7.5
    front=Polygon(r['u-terrace-front']['clear']);north=Polygon(r['u-terrace-north']['clear'])
    assert front.covers(box(3174,0,15090,1800))
    assert front.boundary.intersection(north.boundary).length>=3000
    assert 'u-terrace-north' in graph['u-terrace-front']
    assert geometry(b['roofs'][1]['ceiling']).intersection(front.union(north)).area<1
    assert any(g['owner']=='u-bedroom-balcony' and g['height']==1100 for g in b['guards'])
    # Close the exterior jog where the atrium glazing meets the front gallery.
    assert sum(LineString([w['a'],w['b']]).length for w in b['walls'] if w['id'].startswith('u-atrium-exterior-return'))>=800


def test_icu_corner_keeps_fixed_pane_and_two_independent_wall_stacking_doors():
    p=project();ops={o['id']:o for o in p['customPlan']['floors'][0]['openings']}
    door=ops['g-care-veranda'];fixed=ops['g-care-lawn-window']
    assert (door['offset'],door['width'],door['height'],door['sill'])==(4300,2400,2400,0)
    assert door['stackingSliding'] and door['slidingPanels']==2
    assert (fixed['width'],fixed['height'],fixed['sill'],fixed['fixed'])==(1000,2400,0,True)
    assert ops['g-care-lawn-window-left']['sill']==300
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    assert 'g-care-lawn-window' not in scene['door_motion']
    panes=[n for n in scene['nodes'] if n.get('owner') in (door['id'],fixed['id']) and n['role']=='glass']
    assert len(panes)==3 and all(n['scale'][1]==.024 for n in panes)
    motion=scene['door_motion'][door['id']]
    assert motion['clearWidth']==2.3
    assert {l['id'] for l in motion['layers']}=={'g-care-veranda/panel-b','g-care-veranda/panel-c'}
    nodes={n['id']:n for n in scene['nodes']}
    parked=[];handles=[]
    for leaf in motion['layers']:
        glass=next(nodes[i] for i in leaf['ids'] if nodes[i]['role']=='glass')
        x=glass['position'][0]+leaf['slide'][0];y=glass['position'][1]
        half=glass['scale'][0]/2
        assert 11.4<x-half<x+half<12.8  # A bay plus its existing solid end pier
        parked.append(y)
        handles.append(leaf['handle'][0]+leaf['slide'][0])
    assert abs(parked[0]-parked[1])>=.119  # separate tracks, including handle clearance
    assert abs(handles[0]-handles[1])>.9  # independently targetable when stacked


def test_entrance_cleanup_preserves_every_node_outside_authorized_frontage():
    import hashlib
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    def allowed(n):
        owner=n.get('owner','')
        if owner.startswith(('exterior-porch-01','exterior-pedestrian','site-entry-path','front-tiled-court','front-bed-1-lantern')) or owner=='site-driveway':return True
        x,y,z=n['position']
        return owner.startswith('object-') and ((n['role']=='fixture' and n['floor']==-1 and y<0 and z<0) or (n['role']=='downlight' and n['floor']==0 and 11<x<16 and -1.5<y<0 and 2.7<z<2.9))
    nodes=[{k:v for k,v in historic_finish(n).items() if k!='id' and not(k=='owner' and v.startswith('object-'))} for n in historic_nodes(scene) if n['floor'] in (0,-1) and n['role']!='plinth' and not allowed(n) and not kitchen_casework_node(n)]
    digest=hashlib.sha256(json.dumps(sorted(nodes,key=lambda x:json.dumps(x,sort_keys=True)),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    before=json.loads((ROOT/'tests/fixtures/desired_home_before_modular_kitchen.json').read_text())
    assert digest==json.loads((ROOT/'tests/fixtures/desired_home_before_upper_refinement.json').read_text())['entrance_unaffected_ground_nodes']


def test_front_gates_clear_porch_through_their_entire_motion():
    import numpy as np
    from shapely.geometry import MultiPoint
    from shapely.affinity import rotate,translate
    from floorforge.scene import transformation
    s=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    nodes={n['id']:n for n in s['nodes']}
    assert 'exterior-porch-01-column' not in nodes
    assert not any(n['owner']=='exterior-porch-01' and n['role']=='outdoor-furniture' for n in nodes.values())
    def solid(n):
        vertices=np.array(s['assets'][n['asset']]['vertices']);m=transformation(n)
        vertices=vertices@m[:3,:3].T+m[:3,3]
        return MultiPoint(vertices[:,:2]).convex_hull,vertices[:,2].min(),vertices[:,2].max()
    porch=[solid(n) for n in nodes.values() if n['owner']=='exterior-porch-01' and n['role'] in ('porch','step')]
    for gate in s['gate_model']:
        for part in gate['parts']:
            # A conservative solid leaf envelope includes the spaces between slats.
            solids=[solid(nodes[i]) for i in part['ids']]
            from shapely.ops import unary_union
            leaf=unary_union([p for p,_,_ in solids]).convex_hull
            lo,hi=min(a for _,a,_ in solids),max(b for _,_,b in solids)
            for t in np.linspace(0,1,181):
                p=translate(leaf,xoff=part['slide'][0]*t,yoff=part['slide'][1]*t) if 'slide' in part else rotate(leaf,part['angle']*t,origin=part['pivot'][:2],use_radians=True)
                for obstacle,z0,z1 in porch:
                    if min(hi,z1)>max(lo,z0):assert p.intersection(obstacle).area<1e-8
    # The front porch stays well left of the vehicle gateway, including nosings.
    vehicle=next(g for g in s['gate_model'] if g['id']=='exterior-vehicle-gate')
    assert vehicle['start'][0]-max(p.bounds[2] for p,_,_ in porch)>.30
    ped=next(g for g in s['gate_model'] if g['id']=='exterior-pedestrian-gate')
    assert ped['parts'][0]['slide'][0]<-ped['width']


def test_modular_kitchen_has_connected_l_and_opposite_uncovered_fridge():
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    items={f['kind']:Polygon(f['footprint']) for f in scene['furniture'] if f['room_id']=='g-kitchen'}
    worktop,fridge,upper=(items[k] for k in ('kitchen-run','kitchen-fridge','kitchen-upper-storage'))
    assert 'kitchen-prep-run' not in items
    assert worktop.is_valid and worktop.geom_type=='Polygon'
    assert worktop.covers(box(6.8,.3,7.2,1.7))  # return replaces old fridge
    assert worktop.covers(box(4.3,.3,6.8,.7))  # continuous window run
    assert not worktop.covers(box(4.3,1,5.3,1.5))  # open central aisle
    assert fridge.bounds[1]>2.6 and fridge.bounds[3]>3.3
    assert upper.bounds[0]>6.9 and upper.bounds[3]<1.8
    assert fridge.distance(upper)>1.7
    assert fridge.distance(worktop)>1.5
    # The hall entry and service-door approaches remain outside the cabinetry.
    for opening in (box(7.1,1.95,7.374,3.3),box(3.174,.45,4.08,1.35),box(3.174,2.4,4.08,3.3)):
        assert all(not opening.intersects(p) for p in (worktop,fridge,upper))


def test_kitchen_change_preserves_every_other_rendered_area():
    import hashlib
    before=json.loads((ROOT/'tests/fixtures/desired_home_before_modular_kitchen.json').read_text())
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    nodes=[{k:v for k,v in historic_finish(n).items() if k!='id' and not(k=='owner' and v.startswith('object-'))} for n in historic_nodes(scene) if n['floor'] in (0,-1) and n['role']!='plinth' and not kitchen_casework_node(n)]
    nodes.sort(key=lambda n:json.dumps(n,sort_keys=True))
    assert hashlib.sha256(json.dumps(nodes,sort_keys=True,separators=(',',':')).encode()).hexdigest()==json.loads((ROOT/'tests/fixtures/desired_home_before_upper_refinement.json').read_text())['kitchen_unaffected_ground_nodes']


def test_simple_ceiling_removes_decor_and_kitchen_sink_is_clear_of_carcasses():
    import numpy as np
    from floorforge.scene import transformation
    scene=json.loads((ROOT/'examples/gallery/my-desired-home/scene.json').read_text())
    removed=json.loads((ROOT/'tests/fixtures/desired_home_removed_ceiling_decor.json').read_text())
    def canon(n):return json.dumps({k:v for k,v in n.items() if k!='id' and not(k=='owner' and v.startswith('object-'))},sort_keys=True)
    current={canon(n) for n in scene['nodes']}
    assert all(canon(n) not in current for n in removed['removed_nodes'])
    assert not any(f['kind']=='floor-lamp' and f['room_id'] in ('g-living','g-drawing') for f in scene['furniture'])
    assert any(n['floor']==0 and n['role']=='downlight' for n in scene['nodes'])
    nodes={n['id']:n for n in scene['nodes']}
    prefix='g-kitchen/modular-kitchen/'
    def bounds(n):
        points=np.array(scene['assets'][n['asset']]['vertices']);m=transformation(n)
        points=points@m[:3,:3].T+m[:3,3]
        return points.min(axis=0),points.max(axis=0)
    lo,hi=bounds(nodes[prefix+'sink-bottom'])
    assert lo[0]>6.7 and .8<lo[1]<hi[1]<1.8
    a,b=bounds(nodes[prefix+'hob'])
    assert 4.9<a[0]<b[0]<5.8 and b[1]<.81
    assert prefix+'integrated-hood' not in nodes
    assert bounds(nodes[prefix+'rear-extractor'])[1][2]<1.1
    # Counter/cabinet meshes must actually leave a hole, not fill the new basin.
    basin=box(lo[0]+.02,lo[1]+.02,hi[0]-.02,hi[1]-.02)
    for n in scene['nodes']:
        if n['id'].startswith(prefix) and ('base-top' in n['id'] or n['id'].endswith('l-worktop')):
            from shapely.geometry import MultiPoint
            asset=scene['assets'][n['asset']];m=transformation(n)
            pts=np.array(asset['vertices'])@m[:3,:3].T+m[:3,3]
            for tri in np.array(asset['faces']).reshape(-1,3):
                poly=MultiPoint(pts[tri,:2]).convex_hull
                if poly.geom_type=='Polygon':assert poly.intersection(basin).area<1e-8
