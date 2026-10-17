// Screen-space labels for the 3D view: one amber selection label placed beside
// the exact picked object, and numbered cyan callouts for an opened enclosure or
// a traced route step. Leader lines are 1 px SVG strokes; labels never sit on
// top of the object they describe. Labels hide when their anchor is occluded.
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const v = new THREE.Vector3();

export class LabelLayer {
  constructor(host, viewer) {
    this.host = host;
    this.viewer = viewer;
    this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    this.svg.setAttribute('class', 'leader-layer');
    this.layer = document.createElement('div');
    this.layer.className = 'label-layer';
    host.append(this.svg, this.layer);
    this.selection = null;
    this.callouts = [];
    this.selEl = document.createElement('div');
    this.selEl.className = 'scene-label selected';
    this.selEl.hidden = true;
    this.layer.append(this.selEl);
    this.calloutEls = [];
    this.visibleCheck = 0;
  }

  // anchor: THREE.Vector3 (world). rows: [[term, value], ...]
  select(anchor, title, rows = [], tone = 'selected') {
    this.selection = { anchor: anchor.clone(), title, rows, tone, seen: true, checked: 0 };
    this.selEl.className = `scene-label ${tone}`;
    this.selEl.innerHTML = `<strong>${esc(title)}</strong>${rows.length ? `<dl>${rows.map(([k, val]) => `<dt>${esc(k)}</dt><dd>${esc(val)}</dd>`).join('')}</dl>` : ''}`;
    this.selEl.hidden = false;
  }

  clearSelection() { this.selection = null; this.selEl.hidden = true; }

  // items: [{ n, anchor: Vector3, text, ref }]
  setCallouts(items, { tone = 'trace', onPick = null } = {}) {
    for (const el of this.calloutEls) el.remove();
    this.calloutEls = items.map((item) => {
      const el = document.createElement('button');
      el.type = 'button';
      el.className = `scene-callout ${tone}`;
      el.innerHTML = `<span class="num">${esc(item.n)}</span><span class="txt">${esc(item.text)}</span>`;
      if (onPick && item.ref) el.addEventListener('click', (e) => { e.stopPropagation(); onPick(item.ref); });
      this.layer.append(el);
      return el;
    });
    this.callouts = items.map((i) => ({ ...i, anchor: i.anchor.clone(), seen: true }));
  }

  clearCallouts() { this.setCallouts([]); }

  project(world) {
    const cam = this.viewer.camera;
    v.copy(world).project(cam);
    const w = this.host.clientWidth, h = this.host.clientHeight;
    return { x: (v.x * .5 + .5) * w, y: (-v.y * .5 + .5) * h, inFront: v.z > -1 && v.z < 1, w, h };
  }

  occluded(world) {
    const viewer = this.viewer;
    if (viewer.mode === 'walk' && viewer.walker) return !viewer.walker.sees(viewer.camera.position, world, .06);
    return false;
  }

  update(force = false) {
    const lines = [];
    const doCheck = force || (++this.visibleCheck % 6 === 0);
    if (this.selection) {
      const s = this.selection;
      const p = this.project(s.anchor);
      if (doCheck) s.seen = !this.occluded(s.anchor);
      const show = p.inFront && s.seen && p.x > -40 && p.x < p.w + 40 && p.y > -40 && p.y < p.h + 40;
      this.selEl.hidden = !show;
      if (show) {
        const box = this.selEl.getBoundingClientRect();
        const right = p.x < p.w * .62;
        let lx = right ? p.x + 46 : p.x - 46 - box.width;
        let ly = p.y - box.height - 26;
        if (ly < 48) ly = p.y + 26;            // keep clear of the view chips along the top edge
        lx = Math.max(8, Math.min(p.w - box.width - 8, lx));
        ly = Math.max(48, Math.min(p.h - box.height - 8, ly));
        this.selEl.style.transform = `translate(${Math.round(lx)}px, ${Math.round(ly)}px)`;
        const ex = right ? lx : lx + box.width, ey = Math.min(Math.max(p.y, ly + 10), ly + box.height - 10);
        lines.push(`<circle cx="${p.x}" cy="${p.y}" r="3.2" class="anchor selected"/><polyline class="leader selected" points="${p.x},${p.y} ${(p.x + ex) / 2},${ey} ${ex},${ey}"/>`);
      }
    }
    if (this.callouts.length) {
      const pts = this.callouts.map((c) => {
        const p = this.project(c.anchor);
        return { c, p };
      });
      const visible = pts.filter(({ p }) => p.inFront && p.x > 0 && p.x < p.w && p.y > 0 && p.y < p.h);
      const cx = visible.length ? visible.reduce((a, { p }) => a + p.x, 0) / visible.length : 0;
      const minX = Math.min(...visible.map(({ p }) => p.x)), maxX = Math.max(...visible.map(({ p }) => p.x));
      const left = visible.filter(({ p }) => p.x <= cx).sort((a, b) => a.p.y - b.p.y);
      const right = visible.filter(({ p }) => p.x > cx).sort((a, b) => a.p.y - b.p.y);
      const place = (list, side) => {
        let lastY = -Infinity;
        for (const item of list) {
          const el = this.calloutEls[this.callouts.indexOf(item.c)];
          const r = el.getBoundingClientRect();
          let y = Math.max(item.p.y - r.height / 2, lastY + 4, 48);
          y = Math.min(y, item.p.h - r.height - 70);
          lastY = y + r.height;
          const gap = 34;
          let x = side < 0 ? Math.min(minX, item.p.x) - gap - r.width : Math.max(maxX, item.p.x) + gap;
          x = Math.max(6, Math.min(item.p.w - r.width - 6, x));
          el.style.transform = `translate(${Math.round(x)}px, ${Math.round(y)}px)`;
          el.hidden = false;
          const ex = side < 0 ? x + r.width : x, ey = y + r.height / 2;
          lines.push(`<circle cx="${item.p.x}" cy="${item.p.y}" r="2.6" class="anchor trace"/><polyline class="leader trace" points="${item.p.x},${item.p.y} ${ex + (side < 0 ? 10 : -10)},${ey} ${ex},${ey}"/>`);
        }
      };
      for (const el of this.calloutEls) el.hidden = true;
      place(left, -1);
      place(right, 1);
    }
    this.svg.innerHTML = lines.join('');
  }
}
