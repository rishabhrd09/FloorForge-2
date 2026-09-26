"""Generate twice from clean caches and compare published artifact hashes."""
from pathlib import Path
import sys,tempfile,json,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from floorforge.pipeline import run
from floorforge.model import read_json
start=time.perf_counter()
with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
 x=run({'brief':{}},Path(a),use_cache=False);y=run({'brief':{}},Path(b),use_cache=False)
 first=read_json(Path(x['path'])/'manifest.json');second=read_json(Path(y['path'])/'manifest.json')
 changed=[name for name,h in first['files'].items() if second['files'].get(name)!=h]
 result={'two_clean_generations':True,'equal_build_ids':x['id']==y['id'],'files_compared':len(first['files']),'changed_artifacts':changed,'seconds':round(time.perf_counter()-start,3),'scope':'Same process and dependency versions; not cross-platform bitwise equivalence.'}
 out=Path(__file__).resolve().parents[1]/'evidence/reproducibility.json';out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
 raise SystemExit(bool(changed))
