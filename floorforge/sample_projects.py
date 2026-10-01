"""Read-only catalogue of bundled, fully generated sample projects."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def catalogue():
    records=json.loads((ROOT/'examples/gallery/catalog.json').read_text())
    return [{k:v for k,v in r.items() if k!='directory'} | {'baseUrl':f"/samples/{r['id']}/",'thumbnailUrl':f"/samples/{r['id']}/thumbnail.png"} for r in records]

def sample_file(slug,relative):
    records=json.loads((ROOT/'examples/gallery/catalog.json').read_text())
    record=next((r for r in records if r['id']==slug),None)
    if record is None:return None
    if relative=='thumbnail.png':return ROOT/'examples/gallery/thumbnails'/f'{slug}.png'
    base=(ROOT/'examples'/record['directory']).resolve()
    file=(base/relative).resolve()
    if not base.is_relative_to(ROOT/'examples') or not file.is_relative_to(base):return None
    return file
