from pathlib import Path
import json, shutil, zipfile, hashlib
from PIL import Image

root=Path(__file__).resolve().parents[2]
out=root/'output/pdf'
src=root/'examples/gallery/my-desired-home'
for index,name in [(2,'ground-floor'),(3,'first-floor'),(4,'roof-plan')]:
    source=out/f'plan-{index:02d}.png'
    if source.exists():source.replace(out/f'my-desired-home-{name}.png')
    with Image.open(out/f'my-desired-home-{name}.png') as image:
        assert image.size==(4961,3508),image.size
        assert abs(image.info['dpi'][0]-300)<1

manifest=json.loads((root/'tmp/pdfs/handover-checks.json').read_text())
manifest['verification']={
    'pdf_pages':11,'paper':'A3 landscape 420 x 297 mm',
    'plan_png_pixels':[4961,3508],'plan_png_dpi':300,
    'rendered_pages_visually_reviewed':11,
    'model_and_3d_capture_reference_match':True,
    'dxf_reimport':'passed / ezdxf audit; AutoCAD GUI not tested',
}
(out/'handover-manifest.json').write_text(json.dumps(manifest,indent=2))
bundle=out/'my-desired-home-engineer-handover.zip'
paths=[out/'my-desired-home-engineer-handover.pdf',out/'my-desired-home-floorplans.dxf',
       out/'my-desired-home-ground-floor.png',out/'my-desired-home-first-floor.png',out/'my-desired-home-roof-plan.png',
       out/'README-handover.txt',out/'handover-manifest.json']
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in paths:z.write(p,p.name)
    for name in ('model.glb','project.floorforge.json','preview.html'):
        z.write(src/name,'digital-model/'+name)
with zipfile.ZipFile(bundle) as z:
    assert z.testzip() is None
    names=z.namelist()
    assert len(names)==10,names
checks={'zip':str(bundle),'files':names,'zip_bytes':bundle.stat().st_size,
        'pdf_bytes':(out/'my-desired-home-engineer-handover.pdf').stat().st_size,
        'pdf_sha256':hashlib.sha256((out/'my-desired-home-engineer-handover.pdf').read_bytes()).hexdigest()}
(root/'tmp/pdfs/package-checks.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
