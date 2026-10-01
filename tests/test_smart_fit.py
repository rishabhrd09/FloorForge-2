import copy
from shapely.geometry import Polygon
from floorforge.smart_fit import smart_fit
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from tests.test_plan_assist import rough


def screenshot_sketch():
    p=rough();p['brief'].update(width_mm=9292,depth_mm=13440,roof_access=True)
    rooms=[('master','bedroom',150,9020,2820,2270),('bed','bedroom',3120,9000,2750,2290),('veranda','veranda',6020,8840,2200,2600),('stair','stair',150,6200,1280,2670),('living','living',1730,6500,4320,2270),('kitchen','kitchen',150,2800,1390,3250),('dining','dining',1690,2630,1480,3570),('drawing','drawing-room',3320,3200,2250,3300)]
    p['customPlan']['floors'][0]['rooms']=[{'id':id,'kind':kind,'name':id.title(),'polygon':[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]} for id,kind,x,y,w,h in rooms]
    return p


def test_screenshot_style_small_rooms_and_stair_fit_with_a_valid_roof_route():
    p=screenshot_sketch();before=copy.deepcopy(p);result=smart_fit(p)
    assert p==before and result['proposal'] and result['valid'],result['errors']
    assert {r['id'] for r in result['customPlan']['floors'][0]['rooms']}=={r['id'] for r in p['customPlan']['floors'][0]['rooms']}
    b=generate_layout(fuse({**p,'customPlan':result['customPlan']}))
    assert validate(b)['status']=='preliminary_geometry_pass'
    assert b['storeys']==1 and b['rooftop'] and b['stairs'][0]['to_floor']==1
    stair=next(r for r in result['customPlan']['floors'][0]['rooms'] if r['id']=='stair')
    x,y,x1,y1=Polygon(stair['polygon']).bounds
    assert x1-x>=2200 and y1-y>=4100
    assert all('before' in c and 'after' in c for c in result['changes'] if c['kind']=='smart-fit')
    second=smart_fit({**p,'customPlan':result['customPlan']})
    assert second['valid'] and second['changes']==[] and second['planHash']==result['planHash']


def test_overlapping_rough_rooms_fit_without_swapping_or_losing_them():
    p=rough();p['customPlan']['floors'][0]['rooms'][1]['polygon']=[[x-650,y] for x,y in p['customPlan']['floors'][0]['rooms'][1]['polygon']]
    result=smart_fit(p);assert result['valid'],result['errors']
    rooms={r['id']:Polygon(r['polygon']) for r in result['customPlan']['floors'][0]['rooms']}
    assert rooms['living'].centroid.x<rooms['drawing'].centroid.x
    assert rooms['living'].centroid.y<rooms['kitchen'].centroid.y
    assert all(a.intersection(b).area<1 for i,a in enumerate(rooms.values()) for b in list(rooms.values())[i+1:])


def test_good_exact_dimensions_are_kept_and_no_missing_floor_is_invented():
    p=rough();result=smart_fit(p);assert result['valid']
    assert all(Polygon(r['polygon']).area==16e6 for r in result['customPlan']['floors'][0]['rooms'])
    p['brief']['storeys']=2;p['customPlan']['floors'].append({'id':'floor-1','rooms':[],'walls':[],'openings':[]})
    result=smart_fit(p)
    assert not result['valid'] and result['customPlan']['floors'][1]['rooms']==[]
    assert all(Polygon(r['polygon']).area==16e6 for r in result['customPlan']['floors'][0]['rooms'])


def test_impossible_fit_preserves_sketch_and_explains_space_shortage():
    p=rough();p['brief'].update(width_mm=5000,depth_mm=6500)
    result=smart_fit(p)
    assert not result['valid'] and result['changes']==[]
    assert result['errors'][0]['code']=='SMART_FIT_SPACE'
    assert result['customPlan']==fuse(p)['customPlan']


def test_manual_partition_and_openings_are_not_replaced_by_fitting():
    p=screenshot_sketch();fl=p['customPlan']['floors'][0]
    fl['walls']=[{'id':'my-wall','a':[7500,200],'b':[7500,3000]}]
    fl['openings']=[{'id':'my-window','roomId':'master','kind':'window','side':'rear','offset':400,'width':1000,'height':1200,'sill':900,'hinge':'start'}]
    result=smart_fit(p)
    assert not result['valid'] and result['customPlan']==fuse(p)['customPlan']
