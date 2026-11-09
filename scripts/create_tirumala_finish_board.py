"""Export three original finish concepts without changing the approved plan."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from floorforge.tirumala_luxury import PALETTES

out=ROOT/'output/tirumala-luxury-review';out.mkdir(exist_ok=True)
cards=[]
descriptions={
 'ivory-teak':('Confirmed by you · applied','Warm ivory walls, soft cream marble-look tiles and warm teak. Closest to My Desired Home.'),
 'pearl-walnut':('Alternative for review','A quieter, cooler pearl-and-greige home, with deeper walnut doors and graphite frames.'),
 'sand-bronze':('Alternative for review','Soft sand walls, natural oak and bronze frames, for a warmer bungalow-inspired veranda.'),
}
for i,(key,p) in enumerate(PALETTES.items()):
 status,desc=descriptions[key]
 swatches=''.join(f'<div><i style="background:{p[k]}"></i><span>{name}</span><small>{p[k]}</small></div>' for k,name in [('wall','Wall'),('stone','Stone'),('floor','Floor'),('wood','Door'),('frame','Frame')])
 # Stylised joinery/material study, explicitly a concept rather than a room rendering.
 svg=f'''<svg viewBox="0 0 360 310" xmlns="http://www.w3.org/2000/svg">
 <defs><linearGradient id="shade-{i}" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#000" stop-opacity=".12"/></linearGradient></defs>
 <rect width="360" height="310" fill="{p['wall']}"/>
 <path d="M0 242 L360 224 L360 310 L0 310 Z" fill="{p['floor']}"/>
 <path d="M0 280 L360 257 M90 237 L48 310 M240 231 L283 310" fill="none" stroke="#ada798" stroke-opacity=".35"/>
 <path d="M0 296 Q85 269 133 283 T324 267 M210 244 Q237 259 350 246" fill="none" stroke="#b3aa9a" stroke-width=".7" opacity=".35"/>
 <rect x="25" y="30" width="95" height="212" fill="{p['stone']}"/>
 <path d="M25 83 H120 M25 136 H120 M25 189 H120" stroke="#aa9c87" opacity=".35"/>
 <rect x="135" y="32" width="195" height="213" fill="{p['frame']}"/>
 <rect x="142" y="39" width="90" height="199" fill="{p['wood']}"/>
 <path d="M164 39 V238 M186 39 V238 M208 39 V238" stroke="#1f1b16" opacity=".17"/>
 <rect x="211" y="129" width="4" height="34" rx="2" fill="#b49a65"/>
 <rect x="239" y="39" width="84" height="199" fill="#cbd9d1"/>
 <path d="M244 169 L318 80 M244 185 L318 96" stroke="#fff" opacity=".5" stroke-width="8"/>
 <path d="M267 39 V238 M296 39 V238" stroke="{p['frame']}" stroke-width="3"/>
 <rect x="136" y="21" width="198" height="8" fill="{p['wood']}"/>
 <rect width="360" height="310" fill="url(#shade-{i})"/>
 <ellipse cx="59" cy="247" rx="22" ry="5" fill="#616b54" opacity=".2"/>
 <path d="M42 217 L76 217 L71 245 L48 245 Z" fill="#d9d1c2"/>
 <path d="M59 217 Q35 171 39 164 Q65 183 59 217 M59 216 Q84 168 91 169 Q80 204 59 216 M59 214 Q57 160 63 153 Q73 189 59 214" fill="#526b4b"/>
 </svg>'''
 cards.append(f'<article class="card {"selected" if i==0 else ""}" data-id="{key}"><div class="tag">{chr(65+i)} · {status}</div><h2>{p["name"]}</h2>{svg}<div class="swatches">{swatches}</div><p>{desc}</p><button data-palette="{key}">Copy this finish choice</button></article>')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tirumala · Finish options</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f5f3ed;color:#273d33;font-family:Arial,sans-serif}main{max-width:1440px;margin:auto;padding:42px}header{display:flex;justify-content:space-between;gap:60px;align-items:end;margin-bottom:28px}.eyebrow{font-size:12px;letter-spacing:2px;color:#7b7d70}h1{font-size:36px;font-weight:500;margin:12px 0}header p{max-width:460px;color:#6a7067;line-height:1.5;font-size:14px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}.card{background:#fffdfa;border:1px solid #dedbd1;padding:22px;border-radius:12px}.card.selected{outline:2px solid #647b66;outline-offset:3px}.tag{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#8b7960}h2{font-size:20px;font-weight:500;margin:14px 0 20px}.card svg{width:100%;border-radius:7px}.swatches{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:20px}.swatches i{display:block;height:34px;border:1px solid #ddd;border-radius:3px}.swatches span,.swatches small{display:block;margin-top:7px;font-size:10px}.swatches small{color:#8b8c80;font-size:9px}.card p{font-size:13px;color:#656e63;line-height:1.55;min-height:62px}button{background:#2e4738;color:#fff;border:0;border-radius:5px;padding:12px 17px;cursor:pointer}footer{border-top:1px solid #d9d6ca;margin-top:35px;padding-top:20px;display:grid;grid-template-columns:repeat(3,1fr);gap:30px;font-size:13px;line-height:1.6}footer strong{display:block;margin-bottom:6px}footer p{margin:0;color:#687064}#status{margin:20px 0;font-size:13px}@media(max-width:900px){.grid,footer{grid-template-columns:1fr}header{display:block}main{padding:24px}}</style>
<main><header><div><div class="eyebrow">TIRUMALA 2 + 3 · MATERIAL STUDIES</div><h1>Warm, calm, contemporary.</h1></div><p>Three finish concepts for the same 40 × 50 ft home. A is confirmed and implemented. B and C are alternatives; selecting a card copies your choice without altering room geometry.</p></header><div class="grid">'''+''.join(cards)+'''</div>
<footer><div><strong>Continuous light flooring</strong><p>24 × 48 in cream marble-look tiles. Soft satin indoors; coordinated matte on veranda and wet passages. Lower car porch keeps its Kota and red-oxide character.</p></div><div><strong>Two independent ICU doors</strong><p>Hall-facing timber privacy doors conceal an independent glass slider directly behind them. Opening the wood reveals the glass. The veranda glass retains its fully opening side stack.</p></div><div><strong>Modern home, bungalow veranda</strong><p>Broad ivory roof edges, framed glass, warm timber soffits, layered greenery and an open terrace with a light pergola. These are finish studies, not room renders.</p></div></footer><p id="status" aria-live="polite"></p></main>
<script>const options='''+json.dumps(PALETTES)+''';document.querySelectorAll('[data-palette]').forEach(b=>b.onclick=async()=>{const p=options[b.dataset.palette];document.querySelectorAll('.card').forEach(c=>c.classList.toggle('selected',c.dataset.id===b.dataset.palette));const message='Use the '+p.name+' finish palette for Tirumala 2 and Tirumala 3; retain all room dimensions and the approved G+1 layout.';try{await navigator.clipboard.writeText(message);document.querySelector('#status').textContent='Copied: '+message;}catch{document.querySelector('#status').textContent=message;}});</script></html>'''
(out/'finish-options.html').write_text(html)
print(out/'finish-options.html')
