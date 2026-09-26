"""Local installation smoke test: no network, no AI, no rendering."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from floorforge.intent import fuse
from floorforge.layout import generate_layout
from floorforge.review import validate
from floorforge.pipeline import runtime_versions
CASES={"G+1 40x60":{},"G 30x40":{"width_mm":9144,"depth_mm":12192,"storeys":1,"bedrooms":2,"front_mm":1800,"rear_mm":900,"left_mm":750,"right_mm":750},"G 25x35":{"width_mm":7620,"depth_mm":10668,"storeys":1,"bedrooms":1,"front_mm":1200,"rear_mm":600,"left_mm":450,"right_mm":450}}
for name,brief in CASES.items():
 result=validate(generate_layout(fuse({"brief":brief})))
 print(name+": "+result["status"])
print(json.dumps(runtime_versions(),indent=2))
print("Core import and geometry smoke passed. This is not structural or regulatory acceptance.")
