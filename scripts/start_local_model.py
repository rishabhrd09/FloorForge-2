"""Run a user-installed llama-server locally. No auto-download or shell execution."""
from pathlib import Path
import argparse,subprocess,shutil
from download_model import MODELS,checksum

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=MODELS,default='qwen3-8b');p.add_argument('--directory',type=Path,default=Path.home()/'.floorforge/models');p.add_argument('--llama-server',default='llama-server');p.add_argument('--port',type=int,default=8080);p.add_argument('--context',type=int,default=4096);p.add_argument('--gpu-layers',type=int,default=0);a=p.parse_args();m=MODELS[a.model]
 executable=shutil.which(a.llama_server)
 if not executable:raise SystemExit('Install llama.cpp from its official release first; llama-server was not found. See docs/AI_ASSIST.md.')
 model=a.directory/m['file']
 if not model.is_file() or checksum(model)!=m['sha256']:raise SystemExit('A verified model is required. Run scripts/download_model.py with explicit consent first.')
 if not 1024<=a.port<=65535 or not 1024<=a.context<=32768:raise SystemExit('Use port 1024-65535 and context 1024-32768.')
 command=[executable,'-m',str(model),'--host','127.0.0.1','--port',str(a.port),'--alias',m['alias'],'-c',str(a.context),'-ngl',str(a.gpu_layers),'--jinja']
 print('Starting local inference only. In FloorForge choose Local, endpoint http://127.0.0.1:'+str(a.port)+', model '+m['alias'])
 return subprocess.call(command)
if __name__=='__main__':raise SystemExit(main())
