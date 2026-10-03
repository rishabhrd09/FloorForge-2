import copy
import pytest
from shapely.geometry import Polygon
from floorforge.plan_search import alternatives
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from tests.test_plan_assist import rough


def crowded():
    p=rough();p['brief'].update(width_mm=10990,depth_mm=12740,roof_access=True)
    rows=[('bed1','bedroom',1500,7800,3550,2640),('court','courtyard',5200,7800,2400,2940),('kitchen','kitchen',7750,7800,1800,2640),('veranda','veranda',150,5100,1900,2400),('living','living',2200,5100,4850,2480),('dining','dining',7200,5100,1450,2480),('stair','stair',8800,5100,1040,2480),('drawing','drawing-room',2200,1950,2500,3000),('lobby','inner-lobby',4850,1950,1500,3000),('bed2','bedroom',6500,1950,3200,3030)]
    p['customPlan']['floors'][0]['rooms']=[dict(id=i,kind=k,name=i,polygon=[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]) for i,k,x,y,w,h in rows]
    return p


def test_crowded_ten_room_sketch_has_connected_deterministic_alternatives():
    p=crowded();before=copy.deepcopy(p);r=alternatives(p)
    assert r['valid'] and len(r['alternatives'])==3 and p==before
    assert r==alternatives(p)
    for option in r['alternatives']:
        rooms=option['customPlan']['floors'][0]['rooms']
        assert {(r['id'],r['kind'],r['name']) for r in rooms}=={(r['id'],r['kind'],r['name']) for r in p['customPlan']['floors'][0]['rooms']}
        b=generate_layout(fuse({**p,'customPlan':option['customPlan']}))
        assert validate(b)['status']=='preliminary_geometry_pass'
        assert b['rooftop'] and b['stairs'][0]['to_floor']==1
        polygons=[Polygon(q['polygon']) for q in rooms]
        assert all(a.intersection(b).area<1 for i,a in enumerate(polygons) for b in polygons[i+1:])


@pytest.mark.parametrize('protected',['locked','wall','opening','upstairs','furniture'])
def test_authored_geometry_is_not_replanned(protected):
    p=crowded();locks=[]
    if protected=='locked':locks=['living']
    if protected=='wall':p['customPlan']['floors'][0]['walls']=[dict(id='fixed',a=[150,150],b=[150,3000])]
    if protected=='opening':p['customPlan']['floors'][0]['openings']=[dict(id='manual',roomId='bed1',kind='window',side='rear',offset=500,width=1000,height=1200,sill=900,hinge='start')]
    if protected=='upstairs':p['brief']['storeys']=2;p['customPlan']['floors'].append(dict(id='first',rooms=[],walls=[],openings=[]))
    if protected=='furniture':p['furnitureLayout']={'keep':True}
    before=copy.deepcopy(p)
    if protected=='furniture':
        # Placement data is schema-checked by fuse, never ignored.
        from floorforge.model import DesignError
        with pytest.raises(DesignError):alternatives(p)
    else:
        result=alternatives(p,locked_ids=locks);assert not result['valid'] and not result['alternatives']
    assert p==before


def test_search_limits_explained_without_claiming_infeasibility():
    p=crowded();p['brief'].update(width_mm=5000,depth_mm=6500)
    r=alternatives(p);assert not r['valid'] and r['questions'] and 'does not prove' in r['message']
    p=rough();r=alternatives(p);assert not r['valid'] and 'hall' in r['questions'][0]


def test_alternatives_have_different_room_arrangements_not_just_widths():
    result=alternatives(crowded());signatures=[]
    for option in result['alternatives']:
        rooms=option['customPlan']['floors'][0]['rooms'];hall=next(r for r in rooms if r['id']=='lobby');cx=Polygon(hall['polygon']).centroid.x
        signatures.append(tuple(sorted(r['id'] for r in rooms if Polygon(r['polygon']).centroid.x<cx-500)))
    assert len(signatures)==3 and len(set(signatures))==3
