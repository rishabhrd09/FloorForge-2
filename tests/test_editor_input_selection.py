import copy
import pytest
from floorforge.intent import fuse
from floorforge.model import DesignError


def test_inactive_saved_inputs_do_not_change_generated_plan():
    p={'brief':{'bedrooms':3}}
    expected=fuse(p)
    p['editorState']={'mode':'automatic','guideFloors':[[['']*4 for _ in range(4)] for _ in range(3)],'customPlan':None,'usePlacements':False,'savedRoomEdits':[{'id':'old-room','anchorHash':'old','polygon':[[0,0],[4000,0],[4000,4000],[0,4000]]}],'savedFurnitureLayout':[{'id':'old-sofa','anchorHash':'old','dx':1,'dy':1,'angle':90}]}
    p['editorState']['guideFloors'][0][0][0]='kitchen'
    actual=fuse(copy.deepcopy(p))
    assert actual['planHash']==expected['planHash']
    assert not actual.get('roomEdits') and not actual.get('furnitureLayout') and not actual.get('grid')


@pytest.mark.parametrize('field,value',[('usePlacements','false'),('savedRoomEdits',[{}]),('savedFurnitureLayout',[{'id':'x'}])])
def test_saved_input_schema_is_checked_even_when_not_applied(field,value):
    editor={'mode':'automatic','guideFloors':[[['']*4 for _ in range(4)] for _ in range(3)]}
    editor[field]=value
    with pytest.raises(DesignError):fuse({'editorState':editor})
