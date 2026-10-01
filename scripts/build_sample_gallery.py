#!/usr/bin/env python3
"""Build complete, offline sample projects without touching the user's builds."""
from pathlib import Path
import argparse,json,shutil,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from floorforge.pipeline import run
from floorforge.intent import fuse


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--saved-build',type=Path);args=ap.parse_args()
    root=ROOT/'examples/gallery';root.mkdir(exist_ok=True)
    briefdir=root/'briefs';briefdir.mkdir(exist_ok=True)
    if args.saved_build:
        b=json.loads((args.saved_build/'building.json').read_text())
        clean={'schema':'floorforge.project/0.4','brief':b['brief']}
        assert fuse(clean)['planHash']==b['planHash'],'Saved sample must retain its published geometry'
        (briefdir/'saved-verandah.json').write_text(json.dumps(clean,indent=2)+'\n')
    compact=json.loads((ROOT/'examples/briefs/compact.json').read_text())['brief']
    small=json.loads((ROOT/'examples/briefs/small.json').read_text())['brief']
    variants=[
      ('garden-pavilion',dict(compact,title='The Garden Pavilion',exterior_theme='earth_terracotta',interior_theme='earthy_modern_indian',roof_access=False)),
      ('quiet-studio',dict(small,title='The Quiet Studio',exterior_theme='warm_modern_minimal',interior_theme='quiet_minimal',roof_access=False)),
      ('palm-terrace',dict(title='The Palm Terrace Villa',width_mm=13716,depth_mm=19812,storeys=2,bedrooms=4,exterior_theme='tropical_verandah',interior_theme='warm_contemporary',roof_access=True,variant=1))]
    for slug,brief in variants:(briefdir/(slug+'.json')).write_text(json.dumps({'schema':'floorforge.project/0.4','brief':brief},indent=2)+'\n')
    descriptions={
      'saved-verandah':('Your saved Verandah House','The design you saved, with broad balconies, bright interiors and an accessible roof terrace.','Saved favourite'),
      'original':('The original Verandah House','The familiar startup home: tropical planting, shaded balconies and a furnished roof terrace.','Original example'),
      'garden-pavilion':('The Garden Pavilion','A warm, earthy two-bedroom home on one level, with relaxed living and a compact garden.','Earth & Terracotta'),
      'quiet-studio':('The Quiet Studio','A compact one-bedroom home with a pale palette and calm, minimal interiors.','Warm Minimal'),
      'palm-terrace':('The Palm Terrace Villa','A larger four-bedroom family home with deep shade, warm interiors and roof access.','Tropical Verandah')}
    records=[]
    for slug in descriptions:
        if slug=='original':dest=ROOT/'examples/demo'
        else:
            payload=json.loads((briefdir/(slug+'.json')).read_text())
            with tempfile.TemporaryDirectory(prefix='ff-gallery-') as tmp:
                result=run(payload,Path(tmp),use_cache=False)
                dest=root/slug
                # Only these reproducible gallery outputs are replaced.
                dest.mkdir(exist_ok=True);shutil.copytree(result['path'],dest,dirs_exist_ok=True)
        b=json.loads((dest/'building.json').read_text());v=b['brief'];title,description,style=descriptions[slug]
        records.append(dict(id=slug,title=title,description=description,style=style,directory=str(dest.relative_to(ROOT/'examples')),bedrooms=v['bedrooms'],storeys=b['storeys'],widthFt=round(v['width_mm']/304.8),depthFt=round(v['depth_mm']/304.8),roofAccess=bool(b.get('rooftop')),planHash=b['planHash']))
        print(slug,b['planHash'][:12],flush=True)
    catalog=root/'catalog.json'
    personal=[r for r in json.loads(catalog.read_text()) if r['id'] not in descriptions] if catalog.exists() else []
    catalog.write_text(json.dumps(personal+records,indent=2)+'\n')

if __name__=='__main__':main()
