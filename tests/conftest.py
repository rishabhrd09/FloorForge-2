from pathlib import Path
import sys,pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate,reports
from floorforge.scene import make_scene

CASES={
'villa':{},
'compact':{'width_mm':9144,'depth_mm':12192,'storeys':1,'bedrooms':2,'front_mm':1800,'rear_mm':900,'left_mm':750,'right_mm':750},
'small':{'width_mm':7620,'depth_mm':10668,'storeys':1,'bedrooms':1,'front_mm':1200,'rear_mm':600,'left_mm':450,'right_mm':450}}
@pytest.fixture(scope='session')
def model():return generate_layout(fuse({'brief':{}}))
@pytest.fixture(scope='session')
def scene(model):return make_scene(model,reports(model,validate(model)))
