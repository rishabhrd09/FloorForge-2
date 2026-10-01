import copy
import pytest
from floorforge.room_board import arrange,normalize_board,KINDS
from floorforge.intent import fuse
from floorforge.custom_plan import compile_plan
from floorforge.model import DesignError


def project():
    return {'brief':{'width_mm':12192,'depth_mm':18288,'left_mm':1100,'right_mm':1100,'front_mm':3300,'rear_mm':1200,'storeys':2,'roof_access':True}}


def board():
    kinds=[['kitchen','drawing-room','stair','living',None,'dining','bedroom','bedroom'],['bathroom','bedroom','stair','family',None,'terrace','bedroom','bedroom']]
    return {'version':1,'floors':[{'rooms':[dict(id=f'card-{f}-{i}',kind=k,name=k,col=i%2,row=i//2) for i,k in enumerate(ks) if k]} for f,ks in enumerate(kinds)]}


def test_board_compiles_positions_without_dimensions_and_roof_is_not_a_storey():
    b=board();before=copy.deepcopy(b);result=arrange(project(),b)
    assert b==before
    p=result['customPlan'];assert len(p['floors'])==2
    for f,fl in enumerate(b['floors']):
        rooms={r['id']:r for r in p['floors'][f]['rooms']}
        for card in fl['rooms']:
            r=rooms[card['id']];assert r['kind']==card['kind']
            assert (r['polygon'][0][0]>4000)==bool(card['col'])
            assert any(o['roomId']==r['id'] and o['kind'] in ('door','cased') for o in p['floors'][f]['openings'])
    assert len(p['stairs'][0]['roomIds'])==2
    assert p['floors'][0]['rooms'][0]['kind']=='hall'


@pytest.mark.parametrize('slot',[0,1,2,3,4,5,6,7])
def test_stair_can_move_to_each_of_eight_positions(slot):
    b=board()
    # Closed rooms upstairs so every stair swap has clear sky/support.
    for fl in b['floors']:
        for r in fl['rooms']:
            if r['kind']=='terrace':r['kind']='bedroom'
        stair=next(r for r in fl['rooms'] if r['kind']=='stair');old=stair['row']*2+stair['col']
        occupant=next((r for r in fl['rooms'] if r['row']*2+r['col']==slot),None)
        if occupant:occupant['col'],occupant['row']=old%2,old//2
        stair['col'],stair['row']=slot%2,slot//2
    result=arrange(project(),b)
    stairs=[next(r for r in fl['rooms'] if r['kind']=='stair') for fl in result['customPlan']['floors']]
    assert stairs[0]['polygon']==stairs[1]['polygon']


def test_automatic_stair_and_empty_upper_floor_are_connected():
    b=board();b['floors'][1]['rooms']=[]
    result=arrange(project(),b)
    assert len(result['customPlan']['stairs'][0]['roomIds'])==2
    assert any(r['kind']=='stair' for r in result['board']['floors'][1]['rooms'])


def test_outdoor_constraint_names_the_room_without_mutating_board():
    b=board();b['floors'][0]['rooms'][0]['kind']='courtyard';before=copy.deepcopy(b)
    with pytest.raises(DesignError,match='above an open-air space'):arrange(project(),b)
    assert b==before


def test_impossible_board_has_actionable_capacity_message():
    p=project();p['brief']['depth_mm']=11000
    with pytest.raises(DesignError,match='Move a card to an empty spot'):arrange(p,board())


def test_duplicate_spots_are_rejected():
    b=board();b['floors'][0]['rooms'][1].update(col=0,row=0)
    with pytest.raises(DesignError,match='one room card'):normalize_board(b)


def test_saved_board_is_roundtrippable_and_inactive_board_does_not_affect_hash():
    p=project();expected=fuse(p)['planHash']
    p['editorState']={'mode':'automatic','guideFloors':[[['']*4 for _ in range(4)] for _ in range(3)],'roomBoard':board(),'useRoomBoard':False}
    assert fuse(p)['planHash']==expected


def test_living_only_board_does_not_inherit_automatic_bedroom_minimum():
    p=project();p['brief']['bedrooms']=0
    b={'version':1,'floors':[{'rooms':[dict(id='living-card',kind='living',name='Living',col=0,row=1)]}]}
    result=arrange(p,b)
    assert result['valid']
    assert not any(r['kind']=='bedroom' for fl in result['customPlan']['floors'] for r in fl['rooms'])


@pytest.mark.parametrize('kind',sorted(KINDS))
def test_every_palette_room_gets_valid_access_and_room_behaviour(kind):
    b={'version':1,'floors':[{'rooms':[dict(id='card',kind=kind,name=kind,col=0,row=1)]}]}
    result=arrange(project(),b)
    assert result['valid']
    room=next(r for r in result['customPlan']['floors'][0]['rooms'] if r['id']=='card')
    assert room['kind']==kind
    if kind=='drying-room':assert room['drain']
