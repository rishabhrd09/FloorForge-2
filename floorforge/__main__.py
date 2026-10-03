from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from . import __version__
from .model import read_json,DesignError

def main():
    p=argparse.ArgumentParser(description='FloorForge offline preliminary design studio')
    p.add_argument('command',choices=['generate','serve','doctor','verify'],nargs='?',default='serve')
    inputs=p.add_mutually_exclusive_group();inputs.add_argument('--project',type=Path);inputs.add_argument('--plan2d',type=Path,help='Import a layered ASCII DXF ground-floor plan and generate 3D');p.add_argument('--out',type=Path,default=Path.home()/'.floorforge');p.add_argument('--target',default='exports');p.add_argument('--port',type=int,default=0);p.add_argument('--no-browser',action='store_true');p.add_argument('--no-cache',action='store_true')
    a=p.parse_args()
    if a.command=='doctor':
        from .pipeline import runtime_versions
        v=runtime_versions();print(json.dumps({'version':__version__,'runtime':v,'blender':__import__('shutil').which('blender'),'offline_core':all(x!='missing' for x in v.values())},indent=2));return 0 if all(x!='missing' for x in v.values()) else 1
    if a.command=='verify':
        import subprocess
        return subprocess.call([sys.executable,'-m','pytest','-q',str(Path(__file__).resolve().parent.parent/'tests')])
    if a.command=='serve':
        from .server import serve
        return serve(a.out,a.port,not a.no_browser)
    from .pipeline import run
    payload=read_json(a.project) if a.project else {'schema':'floorforge.project/0.3','brief':{}}
    if a.plan2d:
        from .plan_import import import_dxf, MAX_BYTES
        if a.plan2d.stat().st_size>MAX_BYTES:raise DesignError('DXF_IMPORT','DXF files must be at most 750 KB.')
        imported=import_dxf(a.plan2d.read_text(encoding='utf-8-sig'),a.plan2d.name)
        if not imported['valid']:
            issue=imported['issue'];raise DesignError(issue['code'],issue['message'],issue.get('details'))
        payload=imported['project']
        print(json.dumps({'import_notes':imported['notes']}))
    result=run(payload,a.out,a.target,progress=lambda **kw:print(json.dumps(kw)),use_cache=not a.no_cache)
    print(json.dumps({k:v for k,v in result.items() if k!='output'},indent=2));return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (DesignError,OSError,ValueError,TypeError) as e:
        print(json.dumps(e.record() if isinstance(e,DesignError) else {'error':type(e).__name__,'message':str(e)}),file=sys.stderr);raise SystemExit(2)
