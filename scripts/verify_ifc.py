"""Independent optional IFC4 acceptance. Does not accept self-checks as certification."""
import argparse,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument("file",type=Path);p.add_argument("--report",type=Path,default=Path("ifc-independent-review.json"));a=p.parse_args()
try:
 import ifcopenshell
 import ifcopenshell.validate
except ImportError:
 raise SystemExit("Optional IfcOpenShell is missing. Install requirements-optional-bim.txt in a separate environment.")
f=ifcopenshell.open(str(a.file));logger=ifcopenshell.validate.json_logger()
ifcopenshell.validate.validate(f,logger,express_rules=True)
result={"file":str(a.file),"schema":f.schema,"tool":"IfcOpenShell","version":ifcopenshell.version,"issues":logger.statements,"geometry_viewer_acceptance":"NOT RUN"}
a.report.write_text(json.dumps(result,indent=2,default=str));print(a.report)
sys.exit(1 if logger.statements else 0)
