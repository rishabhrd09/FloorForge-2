"""Make the local before/after visual review; does not alter model geometry."""
from pathlib import Path
import html
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/tirumala-4-realism-review'
TMP = Path('/var/folders/wd/schw303n1tv16s7w0y_07mpc0000gn/T')
refs = [
    ('N01-north-garden', 'a2861165-fc43-46cc-a9c2-6833c6f3b124', 'North: garden, pergola and white/navy house'),
    ('E01-east-court', '3a9be68c-d080-4c89-8fc1-2beabec15189', 'East: screened court across the road'),
    ('N02-northwest', '74354112-bacd-4597-952e-f88b00678587', 'Northwest: two feeder cabinets'),
    ('N03-north-frontage', '350a9c4f-6937-4e3c-930d-22eb785cd43d', 'North road: looking south at the plot'),
    ('R11-ne-corner', '8fb5347d-88ce-4744-acf0-445134550681', 'Northeast boundary corner'),
    ('R13-junction', 'fa05047e-9484-4051-b8fa-5a5d06ab3b45', 'Distant junction: exact heading unconfirmed'),
]
(OUT/'references').mkdir(exist_ok=True)
for name, suffix, _ in refs:
    p=TMP/f'codex-clipboard-{suffix}.png'
    if p.exists(): shutil.copy2(p, OUT/'references'/f'{name}.png')

shots=[
    dict(name='Our house · northeast',file='exterior-northeast.png',note='Ivory exterior, charcoal glazing surrounds, limestone boundary and vacant adjoining land.'),
    dict(name='North garden',file='ref-r08-north-garden.png',ref='N01-north-garden',note='Corrected public-road viewpoint. Lawn blades, rounded ornaments, pergola and the horizontal window pattern now follow N-01 more closely.'),
    dict(name='East court',file='ref-v01-east-court-road.png',ref='E01-east-court',note='Fine diamond mesh, palms and broadleaf screening, raised hedge, soil bed, paving and round drain apertures. Court dimensions and hidden details remain illustrative.'),
    dict(name='Kitchen',file='interior-kitchen-living-dining.png',note='Same L-counter footprint. Clearer cabinet divisions and inset pulls, warm timber, restrained ivory veining and revised daylight. Camera now faces the worktop.'),
    dict(name='Home ICU',file='interior-icu-veranda-garden.png',note='Room and furniture dimensions preserved. Materials, daylight and rendering quality refined; entrance layers remain independently operable.'),
    dict(name='Veranda & living',file='interior-veranda-living.png',note='Approved connected layout, wooden doors and glazing retained.'),
    dict(name='North frontage',file='ref-n03-north-frontage.png',ref='N03-north-frontage',note='Proposed house viewed from the north road. The reference shows the plot before construction.',fresh=True),
    dict(name='Northwest utilities',file='ref-n02-northwest-utilities.png',ref='N02-northwest',note='Owner-identified feeder cabinets and vacant west-side land. Exact camera and utility offsets are estimates.',fresh=True),
    dict(name='South vacant plot',file='ref-south-vacant.png',note='No adjoining house has been introduced. Vacant grass and distant foliage preserve the open setting.',fresh=True),
    dict(name='West vacant plot',file='ref-west-vacant.png',note='Rear elevation and grass on the vacant west plot.',fresh=True),
    dict(name='Upper terrace',file='upper-terrace.png',note='Approved G+1 geometry and terrace access remain unchanged.'),
]
payload=json.dumps(shots).replace('</','<\/')
audit=json.loads((OUT/'geometry-verification.json').read_text())
ref_html=''.join(f'<figure><a href="references/{n}.png"><img loading="lazy" src="references/{n}.png" alt="{html.escape(c)}"></a><figcaption>{html.escape(c)}</figcaption></figure>' for n,_,c in refs)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tirumala 4 · Site & interior review</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f0e9;color:#25352d;font:16px/1.55 system-ui,sans-serif}main{max-width:1420px;margin:auto;padding:36px 28px}header{max-width:900px}small{letter-spacing:.13em;text-transform:uppercase;color:#6e786c}h1{font-size:clamp(30px,4vw,48px);line-height:1.12;margin:12px 0 18px;font-weight:600}p{color:#606b60}.chips{display:flex;flex-wrap:wrap;gap:10px;margin:22px 0}.chips span{padding:7px 13px;background:#e0e7da;border-radius:25px;font-size:14px}nav{display:flex;flex-wrap:wrap;gap:7px;margin:24px 0 16px}button{font:inherit;cursor:pointer;padding:9px 14px;border:1px solid #c5ccbf;border-radius:5px;background:#faf8f2;color:#334338}button.active{background:#304938;color:white;border-color:#304938}button:focus-visible{outline:3px solid #b27b3e;outline-offset:3px}.toolbar{display:flex;gap:12px;align-items:center;justify-content:space-between;margin:10px 0}.toolbar h2{margin:0;font-weight:600}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.pair figure,.refs figure{margin:0;background:white;border:1px solid #dedfd6;border-radius:8px;overflow:hidden}figure img{display:block;width:100%;aspect-ratio:20/13;object-fit:contain;background:#e9e9e1}figcaption{padding:11px 15px;font-size:14px;color:#5e685d}.pair.single{grid-template-columns:1fr}.pair.single figure:nth-child(2){display:none}h2{font-size:24px;margin:36px 0 12px}details{margin-top:30px;border-top:1px solid #cdd2c7;padding-top:20px}summary{cursor:pointer;font-size:22px}.refs{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:20px}.refs img{aspect-ratio:1/1;object-fit:contain}.audit{background:#e4e9dd;padding:22px;border-radius:8px;margin-top:32px}.audit p{margin:6px 0}code{background:#e8e6dd;padding:3px 6px;border-radius:3px}a{color:#355b40}footer{margin-top:34px;font-size:14px}.video{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.video img{width:100%}@media(max-width:800px){main{padding:24px 16px}.pair{grid-template-columns:1fr}.refs{grid-template-columns:repeat(2,1fr)}.toolbar{align-items:flex-start;flex-direction:column}.video{grid-template-columns:repeat(3,1fr)}}
</style><main>
<header><small>Tirumala 4 / 3 November 2026</small><h1>A closer match to the real colony.</h1><p>Updated surroundings and interior finishes from your annotated photographs and the sampled video pan. Compare the actual real-time renders below.</p></header>
<div class="chips"><span>40 × 50 ft retained</span><span>Approved G+1 retained</span><span>No adjoining houses</span><span>Independent wood + glass doors</span></div>
<nav id="views" aria-label="Review views"></nav>
<div class="toolbar"><h2 id="name"></h2><div><button id="compare" class="active">Before / after</button> <button id="reference">Photo / model</button> <button id="latest">Latest only</button></div></div>
<div class="pair" id="pair"><figure><a id="leftlink"><img id="left" alt=""></a><figcaption id="leftcap"></figcaption></figure><figure><a id="rightlink"><img id="right" alt=""></a><figcaption>Updated Tirumala 4 · click to inspect full resolution</figcaption></figure></div><p id="note"></p>
<div class="audit"><strong>Verified without resizing the house</strong><p>AUDIT_TEXT</p><p>All existing house node positions, sizes and assets match the saved baseline. The 17 new cabinet details are non-colliding trim. Master bedroom, kitchen footprint, stairs, wash area, ICU layout, drawing room, doors and upper floor retain their approved geometry.</p><p><a href="geometry-verification.json">Geometry verification</a> · <a href="browser-verification.log">Browser & walkthrough checks</a> · <a href="viewer-tests.log">Viewer tests</a> · <a href="python-tests.log">Plan tests</a></p></div>
<h2>What the references establish</h2><p>The garden and white/navy house lie across the north road; the screened basketball court lies across the east road. The north road is 12 m and the east road is 9 m overall; the modeled verges are included. The immediately adjoining south and west plots remain vacant. Temporary cars in the photos are excluded.</p><p>Camera coordinates, garden depth, background building offsets, tree positions and hidden court details are visual estimates. R09/R13's exact heading is unconfirmed. The duplicate R11 annotations and R08 crops are not separate viewpoints. This is an improved real-time model, not a survey or a photographic reconstruction.</p>
<details><summary>Original site references</summary><div class="refs">REFS</div></details>
<details><summary>Video review · chronological samples</summary><p>12 frames across the 23.36-second pan, sampled every two seconds. The camera rolls toward the end; that roll is not treated as a compass bearing.</p><div class="video">FRAMES</div></details>
<h2>Open the updated sample</h2><p>From the project folder, run <code>.venv/bin/python -m floorforge serve</code>. Choose <strong>Sample projects → Tirumala 4</strong>. The view selector now includes <strong>Around Tirumala 4 · site references</strong>. High quality gives the clearest materials and shadow detail; the existing lower quality settings remain available for slower hardware.</p>
<footer>Tirumala 2 and 3 are unchanged. The kitchen/utility relocation alternatives have not been applied.</footer>
</main><script>
const shots=PAYLOAD, base='../../examples/gallery/tirumala-4/renders/';let current=0,mode='compare';
const el=id=>document.getElementById(id);function update(){const s=shots[current];el('name').textContent=s.name;el('note').textContent=s.note;el('reference').disabled=!s.ref;let m=mode;if(m==='reference'&&!s.ref)m='latest';if(m==='compare'&&s.fresh)m='latest';const single=m==='latest';el('pair').classList.toggle('single',single);const left=single?base+s.file:m==='reference'?'references/'+s.ref+'.png':'before/renders/'+s.file;el('left').src=left;el('leftlink').href=left;el('left').alt=s.name+' '+(single?'updated':m==='reference'?'reference photograph':'before');el('leftcap').textContent=single?'Updated Tirumala 4 · click to inspect full resolution':m==='reference'?'Owner-supplied reference · exact lens and camera offset unmeasured':'Before · camera framing may differ';el('right').src=base+s.file;el('rightlink').href=base+s.file;el('right').alt=s.name+' updated';for(const b of el('views').children)b.classList.toggle('active',+b.dataset.index===current);for(const k of ['compare','reference','latest'])el(k).classList.toggle('active',k===m);}
shots.forEach((s,i)=>{const b=document.createElement('button');b.textContent=s.name;b.dataset.index=i;b.onclick=()=>{current=i;update()};el('views').append(b)});for(const k of ['compare','reference','latest'])el(k).onclick=()=>{mode=k;update()};update();
</script></html>'''
page=page.replace('PAYLOAD',payload).replace('REFS',ref_html).replace('AUDIT_TEXT',f"{audit['houseNodeTransformsUnchanged']:,} existing house objects preserved; {audit['houseAssetsUnchanged']:,} assets unchanged. All {audit['protectedTirumala2And3FilesUnchanged']} checked Tirumala 2/3 files unchanged.")
page=page.replace('FRAMES',''.join(f'<a href="video-frames/frame-{i:02}.jpg"><img loading="lazy" src="video-frames/frame-{i:02}.jpg" alt="Video sample {i}"></a>' for i in range(1,13)))
(OUT/'index.html').write_text(page)
print(OUT/'index.html')
