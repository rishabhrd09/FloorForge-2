// The page's overlay: the sheet's title block and headline, the lens readout, chapter marks, the room ruler, the
// room card and its file. Everything here is plain DOM text, so the walkthrough stays readable without the canvas.
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pad = (n) => String(n).padStart(2, '0');
const num = (v, d = 2) => Number(v).toFixed(d);

const CHAPTERS = [['sheet', 'Sheet'], ['lift', 'Lift'], ['descend', 'Forecourt'], ['rooms', 'Rooms'], ['outro', 'Plan']];
const VASTU = { preferred: 'preferred zone', acceptable: 'acceptable zone', avoid: 'outside the preferred zones' };

export class Hud {
  constructor(data, { onJump }) {
    this.data = data;
    this.onJump = onJump;
    const c = data.copy, stops = data.tour.stops;
    document.title = `${data.title} · Plan Reveal`;
    $('eyebrow').textContent = c.eyebrow;
    $('headline').innerHTML = c.headline.map((line, i) => i === c.headline.length - 1 ? `<em>${esc(line)}</em>` : esc(line)).join('<br>');
    $('lede').textContent = c.lede;
    $('crumb').textContent = `${data.title} · ${data.size.widthFt} × ${data.size.depthFt} ft · ${data.storeys === 1 ? 'ground only' : 'G+' + (data.storeys - 1)}`;
    if (c.cta) $('cta').textContent = c.cta + ' ↗';
    const today = c.date || '';
    $('titleblock').innerHTML = `<div class="project">${esc(data.title)}</div>
      <div><small>Drawing</small>Ground floor plan</div><div><small>Sheet</small>A-101</div>
      <div><small>Plot</small>${data.size.widthFt} × ${data.size.depthFt} ft</div><div><small>Cut</small>+1.20 m · 1:100</div>
      <div><small>Scale bar · 0–5 m</small><div class="scalebar"><span></span><span></span><span></span><span></span><span></span></div></div><div><small>Date</small>${esc(today) || 'Preliminary'}</div>`;
    $('chapters').innerHTML = CHAPTERS.map(([k, label], i) => `<span data-k="${k}">${pad(i + 1)} ${label}</span>`).join('');
    this.rooms = stops.filter((s) => s.number > 0);
    $('ruler').innerHTML = stops.map((s) => `<button type="button" data-stop="${s.number}" data-n="${pad(s.number)} ${esc(short(s.title))}" aria-label="Go to ${esc(s.title)}"></button>`).join('') + '<span class="head" id="ruler-head"></span>';
    $('ruler').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) this.onJump(Number(b.dataset.stop)); });
    $('end').innerHTML = `<h3>${esc(c.endTitle || 'Every room, before it exists.')}</h3><p>${esc(c.endText || 'The drawing and the house are one model. Change the plan in the studio and this walk is rebuilt from it, room by room.')}</p>
      <div class="links" data-interactive><a class="pill" href="drawings.pdf">Drawing set (PDF)</a><a class="pill" href="preview.html">Free 3D walk</a><a class="pill" href="floorplans.dxf">CAD (DXF)</a><button class="pill" type="button" id="again">Back to the sheet</button></div>`;
    $('again').addEventListener('click', () => this.onJump(-1));
    $('sr-rooms').innerHTML = '<h2>Rooms</h2><ol>' + this.rooms.map((s) => `<li>${esc(s.title)}: ${esc(this.facts(s).join(', '))}</li>`).join('') + '</ol>';
    this.file = $('file');
    this.file.addEventListener('click', (e) => { if (e.target === this.file || e.target.closest('.close')) this.file.close(); });
    this.last = {};
  }

  facts(stop) {
    const f = this.data.files[stop.room];
    if (!f) return [];
    const out = [`${num(f.size[0])} × ${num(f.size[1])} m`, `${num(f.area, 1)} m²`];
    if (f.ceiling) out.push(`ceiling ${num(f.ceiling)} m`);
    const ext = f.windows.filter((w) => w.faces !== 'inner');
    if (ext.length) out.push(`light from ${[...new Set(ext.map((w) => w.faces))].join('/')}`);
    return out;
  }

  card(stop, opacity, dark) {
    const el = $('card');
    if (this.last.cardStop !== stop?.number) {
      this.last.cardStop = stop?.number;
      if (stop) {
        const facts = this.facts(stop);
        const file = this.data.files[stop.room];
        el.innerHTML = `<div class="n">${stop.number ? 'Room ' + pad(stop.number) : 'Arrival'}</div><h2>${esc(stop.title)}</h2>
          <div class="facts">${facts.map((f) => `<span>${esc(f)}</span>`).join('<span>·</span>')}</div>${file ? '<button type="button" class="open" id="open-file">Open file +</button>' : ''}
          ${stop.note ? `<p class="note">${esc(stop.note)}</p>` : ''}`;
        el.querySelector('#open-file')?.addEventListener('click', () => this.openFile(stop));
      }
    }
    el.style.opacity = opacity.toFixed(3);
    el.style.transform = `translateY(${(1 - opacity) * 10}px)`;
    el.style.pointerEvents = opacity > .5 ? 'auto' : 'none';
    el.classList.toggle('dark', Boolean(dark));
  }

  openFile(stop) {
    const f = this.data.files[stop.room], room = this.data.rooms.find((r) => r.id === stop.room);
    if (!f || !room) return;
    const rows = [
      ['Clear size', `${num(f.size[0])} × ${num(f.size[1])} m <span class="small">(${num(f.sizeFt[0], 1)} × ${num(f.sizeFt[1], 1)} ft)</span>`],
      ['Floor area', `${num(f.area, 1)} m² <span class="small">(${f.areaFt} ft²)</span>`],
      ['Ceiling', f.ceiling ? `${num(f.ceiling)} m clear` : 'Open to the sky'],
      ['Floor', room.floor === 0 ? 'Ground floor' : room.floor === 1 ? 'First floor' : `Level ${room.floor}`],
    ];
    if (f.windows.length) rows.push(['Openings', f.windows.map((w) => `${w.kind === 'window' ? 'Window' : w.kind === 'glazed' ? 'Glazed door' : 'Door'} ${num(w.width)} × ${num(w.height)} m${w.faces !== 'inner' ? ', faces ' + w.faces : ''}${w.kind === 'window' ? `, sill ${num(w.sill)} m` : ''}`).join('<br>')]);
    if (f.glazingPct != null) rows.push(['Daylight', `Openings ${num(f.glazingPct, 1)}% of the floor area <span class="small">(NBC-style screen asks for at least 10%)</span>`]);
    if (f.vastu) rows.push(['Vastu', `${esc(f.vastu.zone)} zone · ${VASTU[f.vastu.rating] || esc(f.vastu.rating)}${f.vastu.preferred?.length ? ` <span class="small">(preferred: ${esc(f.vastu.preferred.join(', '))})</span>` : ''}`]);
    if (f.furniture.length) rows.push(['Furnished with', esc(f.furniture.join(', '))]);
    this.file.innerHTML = `<button class="pill close" type="button">Close ×</button><div class="eyebrow">Room ${pad(stop.number)} · file</div><h4 id="file-title">${esc(stop.title)}</h4>
      <table>${rows.map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`).join('')}</table>
      ${f.notes.length ? `<p class="small"><b>Review notes.</b> ${esc(f.notes.join(' '))}</p>` : ''}
      <p class="small">Dimensions are the clear room size from the generated model and drawings. Preliminary: survey, structure, services and approvals remain with a qualified professional.</p>`;
    this.file.showModal();
  }

  // The sheet border as a fraction of the screen [left, bottom, right, top] (texture coordinates, y up): drawn lines stop
  // at it, as on a printed sheet.
  frameRect() {
    const W = innerWidth, H = innerHeight, key = `${W}x${H}`;
    if (this.frameKey !== key) {
      const r = $('frame').getBoundingClientRect();
      this.frameKey = key;
      this.frame = r.width ? [r.left / W, 1 - r.bottom / H, r.right / W, 1 - r.top / H] : [0, 0, 1, 1];
    }
    return this.frame;
  }

  // Where the sheet's drawing may sit on a landscape screen, as screen fractions [left, top, right, bottom]: beside
  // the title block or above it, clear of the lens readout and the room ruler. Null when the title block is hidden.
  sheetBoxes() {
    const W = innerWidth, H = innerHeight, key = `${W}x${H}`;
    if (this.boxKey === key) return this.boxes;
    this.boxKey = key;
    this.boxes = null;
    const tb = $('titleblock').getBoundingClientRect(), lens = $('lens').getBoundingClientRect(), ruler = $('ruler').getBoundingClientRect();
    if (tb.width && W / H >= 1.05) {
      const top = (lens.bottom + 14) / H, right = Math.min(lens.right, ruler.width ? ruler.left - 12 : W) / W;
      this.boxes = [[.45, top, (tb.left - 14) / W, tb.bottom / H], [.45, top, right, (tb.top - 14) / H]];
    }
    return this.boxes;
  }

  update(s, director) {
    const chapterKey = ['walk', 'dwell', 'rise', 'floorplan', 'drop'].includes(s.chapter) ? (s.chapter === 'dwell' && s.stop === 0 ? 'descend' : 'rooms')
      : ['colour', 'wipe', 'end'].includes(s.chapter) ? 'outro' : s.chapter;
    if (this.last.chapter !== chapterKey) {
      this.last.chapter = chapterKey;
      for (const el of $('chapters').children) el.classList.toggle('on', el.dataset.k === chapterKey);
    }
    const intro = s.chapter === 'sheet' ? 1 - Math.max(0, (s.p - .55) / .6) : 0;
    $('intro').style.opacity = intro.toFixed(3);
    $('intro').style.transform = window.innerWidth > 760 && innerWidth > innerHeight ? `translateY(calc(-50% - ${(1 - intro) * 18}px))` : `translateY(${-(1 - intro) * 18}px)`;
    $('titleblock').style.opacity = (s.chapter === 'sheet' || s.chapter === 'end' || s.chapter === 'wipe') ? Math.max(intro, s.chapter === 'sheet' ? 1 : s.sheetInk).toFixed(2) : '0';
    $('frame').style.opacity = s.clip > .5 ? '1' : '0';
    const cam = director.viewer.camera;
    // Height above the floor the camera stands on inside; above the street outside.
    const fov = cam.fov, height = cam.position.y - (s.indoor ? s.floor * director.H : director.ground);
    $('lens-fov').textContent = `${fov < 10 ? fov.toFixed(1) : fov.toFixed(0)}°`;
    $('lens-h').textContent = `${height >= 100 ? Math.round(height).toLocaleString('en-US').replace(',', ' ') : height.toFixed(height >= 10 ? 0 : 2)} M`;
    $('lens-cut').textContent = s.cut > 1e4 ? '—' : `+${(s.cut - s.floor * director.H).toFixed(2)} M`;
    const stop = s.stop != null ? director.stops[s.stop] : null;
    this.card(stop, stop ? s.card : 0, s.dark);
    const count = $('count');
    const current = s.stop ?? this.lastStop ?? 0;
    if (s.stop != null) this.lastStop = s.stop;
    count.textContent = `${pad(current)} / ${pad(this.rooms.length)} rooms`;
    count.style.opacity = ['walk', 'dwell', 'rise', 'floorplan', 'drop'].includes(s.chapter) && current > 0 ? '1' : '0';
    count.classList.toggle('light', Boolean(s.dark));
    $('hint').style.opacity = s.chapter === 'dwell' && s.card > .9 ? '.85' : '0';
    $('hint').classList.toggle('light', Boolean(s.dark));
    $('end').style.opacity = s.chapter === 'end' ? '1' : '0';
    $('end').style.pointerEvents = s.chapter === 'end' ? 'auto' : 'none';
    const ruler = !['sheet', 'wipe', 'end'].includes(s.chapter);
    $('ruler').style.opacity = ruler ? '1' : '0';
    $('ruler').style.visibility = ruler ? 'visible' : 'hidden';
    const buttons = $('ruler').querySelectorAll('button');
    buttons.forEach((b, i) => b.classList.toggle('on', i === current && s.chapter !== 'sheet' && s.chapter !== 'lift'));
    const head = $('ruler-head'), total = director.total;
    head.style.top = `${(s.p / total) * 100}%`;
  }
}

function short(t) { return t.replace(/^The /, ''); }
