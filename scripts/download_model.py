"""Explicit, checksum-verified optional Qwen model download. Never runs at app startup."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,urllib.request
MODELS={
 'qwen3-8b':{'repo':'Qwen/Qwen3-8B-GGUF','file':'Qwen3-8B-Q4_K_M.gguf','revision':'6a569868d07d3bd59e8b97fb001bf8c0b254bb20','sha256':'d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785','approx_gb':5.03,'alias':'Qwen3-8B'},
 'qwen3-4b':{'repo':'Qwen/Qwen3-4B-GGUF','file':'Qwen3-4B-Q4_K_M.gguf','revision':'a9a60d0','sha256':'7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5','approx_gb':2.5,'alias':'Qwen3-4B'}}
def checksum(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while block:=f.read(4*1024*1024):h.update(block)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',choices=MODELS,default='qwen3-8b');p.add_argument('--out',type=Path,default=Path.home()/'.floorforge/models');p.add_argument('--accept-apache-2.0',action='store_true');p.add_argument('--dry-run',action='store_true');a=p.parse_args();m=MODELS[a.model]
 url=f'https://huggingface.co/{m["repo"]}/resolve/{m["revision"]}/{m["file"]}'
 print(json.dumps({**m,'url':url,'license':'Apache-2.0','license_source':f'https://huggingface.co/{m["repo"]}/blob/main/LICENSE','execution_inference_tested':False},indent=2))
 if a.dry_run:return 0
 if not a.accept_apache_2_0:raise SystemExit('Read the official model license, then pass --accept-apache-2.0 to opt into the large download.')
 a.out.mkdir(parents=True,exist_ok=True);dest=a.out/m['file']
 if dest.exists():
  if checksum(dest)!=m['sha256']:raise SystemExit('Existing model checksum differs. Preserve or remove it explicitly; this script will not overwrite it.')
  print('Existing model checksum passed. No download.');return 0
 if shutil.disk_usage(a.out).free<(m['approx_gb']+1)*1e9:raise SystemExit('Insufficient free disk space for the selected model plus working space.')
 part=dest.with_suffix('.gguf.partial');h=hashlib.sha256();size=0;last=0
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'FloorForge-explicit-model-download/0.2'})
  with urllib.request.urlopen(req,timeout=60) as response,part.open('wb') as f:
   while block:=response.read(4*1024*1024):
    size+=len(block)
    if size>(m['approx_gb']+.5)*1e9:raise ValueError('Unexpectedly large response; download stopped.')
    f.write(block);h.update(block)
    if size-last>100_000_000:print(f'{size/1e9:.2f} GB received',flush=True);last=size
  if h.hexdigest()!=m['sha256']:raise ValueError('SHA-256 verification failed. Unverified weights were not installed.')
  os.replace(part,dest)
  # A model does not execute downloaded Python code. Store auditable source receipts.
  receipt={**m,'download_url':url,'bytes':size,'license':'Apache-2.0','checksum_verified':True,'inference_benchmark':'NOT RUN'}
  dest.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2));print('Verified model installed:',dest)
 finally:
  if part.exists():part.unlink()
 return 0
if __name__=='__main__':
 try:raise SystemExit(main())
 except (OSError,ValueError) as e:raise SystemExit('Model download failed: '+str(e))
