#!/usr/bin/env python3
"""Install optional Three.js/GSAP/path-tracing lab. Network access is explicit."""
import argparse,subprocess,shutil,sys,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--accept-gsap-standard-license',action='store_true');a=p.parse_args()
if not a.accept_gsap_standard_license:
    raise SystemExit('Review https://gsap.com/community/standard-license/ first. Then rerun with --accept-gsap-standard-license. GSAP is NOT MIT/Apache/BSD.')
root=Path(__file__).resolve().parents[1];npm=shutil.which('npm')
if not npm:raise SystemExit('Install Node.js LTS (including npm) and retry. Core FloorForge does not need Node.')
# First install creates a real dependency lock; no fabricated lockfile or integrity hash.
command=[npm,'ci'] if (root/'web/package-lock.json').exists() else [npm,'install']
subprocess.run(command,cwd=root/'web',check=True);subprocess.run([npm,'run','build'],cwd=root/'web',check=True)
licenses={}
for package in ['three','three-gpu-pathtracer','three-mesh-bvh','gsap','esbuild']:
    folder=root/'web/node_modules'/package;target=root/'licenses/optional-js'/package;target.mkdir(parents=True,exist_ok=True)
    meta=json.loads((folder/'package.json').read_text());licenses[package]={'version':meta['version'],'license':meta.get('license','REVIEW REQUIRED')}
    for src in folder.glob('*LICENSE*'):
        if src.is_file():shutil.copy2(src,target/src.name)
(root/'licenses/optional-js/installed.json').write_text(json.dumps(licenses,indent=2))
print('Optional lab built. Restart FloorForge, then open /three.html. Hardware/GPU acceptance remains your verification gate.')
