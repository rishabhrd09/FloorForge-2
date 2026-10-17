// 2D wiring plan of one floor, drawn from the same model as the 3D tour.
// Architectural walls/openings come from the copied building; electrical
// symbols, conduit runs and the selected circuit are overlays. Every symbol
// carries a data-ref so selection stays synchronised with the 3D view.
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const f = (v) => Math.round(v * 1000) / 1000;

// Auto view: the floor's walls, or the selected circuit's parts on this floor.
export function autoView(model, floor, circuitId) {
  const plan = model.plan.floors.find((p) => p.floor === floor);
  const pts = [];
  if (circuitId) {
    for (const c of model.conduits) if (c.circuitIds.includes(circuitId) && c.planFloor === floor) for (const p of c.points) pts.push(p);
    for (const e of model.enclosures) if (e.floor === floor && e.circuitIds?.includes(circuitId)) pts.push(e.mount.face);
  }
  if (pts.length < 2) for (const w of plan.walls) for (const p of w) pts.push(p);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const pad = circuitId && pts.length >= 2 ? 1.6 : .9;
  let x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad, y0 = Math.min(...ys) - pad, y1 = Math.max(...ys) + pad;
  const minW = 7;
  if (x1 - x0 < minW) { const c = (x0 + x1) / 2; x0 = c - minW / 2; x1 = c + minW / 2; }
  if (y1 - y0 < minW * .6) { const c = (y0 + y1) / 2; y0 = c - minW * .3; y1 = c + minW * .3; }
  return [x0, -y1, x1 - x0, y1 - y0];
}

export function planSvg(model, ui) {
  const { floor, selection, circuitId, traceStep, snapshot } = ui;
  const plan = model.plan.floors.find((p) => p.floor === floor);
  if (!plan) return '';
  const [x0, y0, x1, y1] = model.plan.bounds;
  const vb = ui.view || autoView(model, floor, circuitId);
  const k = Math.max(.12, vb[2] / 70);          // text size in metres, readable at any zoom
  const sym = Math.max(1, vb[2] / 10);          // symbol scale
  const Y = (y) => -y;
  const P = (p) => `${f(p[0])},${f(Y(p[1]))}`;
  const circuit = model.circuits.find((c) => c.id === circuitId);
  const selectedRef = selection?.ref;
  const out = [];
  out.push(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vb.map(f).join(' ')}" data-vb="${vb.map(f).join(' ')}" class="plan-drawing" role="img" aria-label="${esc(`${floor ? 'First' : 'Ground'}-floor wiring plan`)}" style="--k:${f(k)};--sym:${f(sym)}">`);
  out.push('<defs><pattern id="hatch" width=".12" height=".12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2=".12" stroke="var(--plan-wall-hatch)" stroke-width=".03"/></pattern></defs>');
  // rooms
  for (const r of plan.rooms) {
    const active = circuit?.rooms?.includes(r.id);
    out.push(`<polygon class="plan-room${active ? ' served' : ''}" data-room="${esc(r.id)}" points="${r.polygon.map(P).join(' ')}"/>`);
  }
  // slab openings (stair wells, voids)
  for (const h of plan.voids || []) out.push(`<polygon class="plan-void" points="${h.map(P).join(' ')}"/>`);
  // walls
  for (const w of plan.walls) out.push(`<polygon class="plan-wall" points="${w.map(P).join(' ')}"/>`);
  // openings: doors with swing arcs, windows as triple lines
  for (const o of plan.openings) {
    if (o.kind === 'window' || o.kind === 'glazed') {
      out.push(`<line class="plan-window" x1="${f(o.p0[0])}" y1="${f(Y(o.p0[1]))}" x2="${f(o.p1[0])}" y2="${f(Y(o.p1[1]))}"/>`);
    } else if (o.kind === 'door' || o.kind === 'entry') {
      const hinge = o.hinge === 'end' ? o.p1 : o.p0, latch = o.hinge === 'end' ? o.p0 : o.p1;
      const w = Math.hypot(latch[0] - hinge[0], latch[1] - hinge[1]);
      const n = o.swingNormal || [0, 0];
      const leaf = [hinge[0] + n[0] * w, hinge[1] + n[1] * w];
      out.push(`<line class="plan-door-gap" x1="${f(o.p0[0])}" y1="${f(Y(o.p0[1]))}" x2="${f(o.p1[0])}" y2="${f(Y(o.p1[1]))}"/>`);
      out.push(`<line class="plan-door" x1="${f(hinge[0])}" y1="${f(Y(hinge[1]))}" x2="${f(leaf[0])}" y2="${f(Y(leaf[1]))}"/>`);
      const cross = (latch[0] - hinge[0]) * n[1] - (latch[1] - hinge[1]) * n[0];
      out.push(`<path class="plan-swing" d="M${f(leaf[0])} ${f(Y(leaf[1]))} A${f(w)} ${f(w)} 0 0 ${cross > 0 ? 1 : 0} ${f(latch[0])} ${f(Y(latch[1]))}"/>`);
    } else {
      out.push(`<line class="plan-door-gap" x1="${f(o.p0[0])}" y1="${f(Y(o.p0[1]))}" x2="${f(o.p1[0])}" y2="${f(Y(o.p1[1]))}"/>`);
    }
  }
  // conduit runs on this floor: faint for all, bright for the selected circuit
  const tracedConduits = new Set(circuit ? model.conduits.filter((c) => c.circuitIds.includes(circuit.id)).map((c) => c.id) : []);
  const stepRefs = new Set(traceStep?.refs || []);
  for (const c of model.conduits) {
    if (c.planFloor !== floor) continue;
    const pts = c.points.map((p) => [p[0], p[1]]);
    const dedup = pts.filter((p, i) => !i || Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) > .005);
    if (dedup.length < 2) continue;
    const on = tracedConduits.has(c.id);
    const cls = ['plan-conduit', c.function, on ? 'traced' : '', stepRefs.has(c.id) ? 'step' : '', selectedRef === c.id ? 'selected' : ''].join(' ');
    out.push(`<polyline class="${cls}" data-ref="${esc(c.id)}" points="${dedup.map(P).join(' ')}"/>`);
    if (on && c.kind === 'chase') {
      const p = dedup[0];
      out.push(`<circle class="plan-drop${on ? ' traced' : ''}" cx="${f(p[0])}" cy="${f(Y(p[1]))}" r=".05"/>`);
    }
  }
  // enclosures
  for (const e of model.enclosures) {
    if (e.floor !== floor || !e.mount) continue;
    const m = e.mount, w = Math.max(.16, e.size.w), t = .07;
    const cx = m.face[0] + m.normal[0] * t / 2, cy = m.face[1] + m.normal[1] * t / 2;
    const ang = Math.atan2(-m.tangent[1], m.tangent[0]) * 180 / Math.PI;
    const sel = selectedRef === e.id, served = circuit?.enclosures?.includes(e.id);
    const cls = `plan-enc ${e.kind}${served ? ' traced' : ''}${sel ? ' selected' : ''}${stepRefs.has(e.id) ? ' step' : ''}`;
    out.push(`<g class="${cls}" data-ref="${esc(e.id)}" transform="translate(${f(cx)} ${f(Y(cy))}) rotate(${f(ang)})">`);
    if (e.kind === 'meter') out.push(`<rect x="${f(-w / 2)}" y="${-t}" width="${f(w)}" height="${t * 2}" rx=".02"/><text class="plan-sym" y=".04">kWh</text>`);
    else if (e.kind === 'main-db' || e.kind === 'sub-db') out.push(`<rect x="${f(-w / 2)}" y="${-t}" width="${f(w)}" height="${t * 2}"/><path d="M${f(-w / 2)} ${t} L${f(w / 2)} ${-t}" class="plan-db-diag"/>`);
    else out.push(`<rect x="${f(-w / 2)}" y="${-t / 2}" width="${f(w)}" height="${t}" rx=".01"/>`);
    out.push('</g>');
  }
  // points
  for (const p of model.points) {
    if (p.floor !== floor) continue;
    const on = snapshot?.points?.[p.id];
    const traced = circuit && p.circuitId === circuit.id;
    const sel = selectedRef === p.id;
    const cls = `plan-point ${p.kind}${on ? ' on' : ''}${traced ? ' traced' : ''}${sel ? ' selected' : ''}${stepRefs.has(p.id) ? ' step' : ''}`;
    const [x, y] = p.position;
    out.push(`<g class="${cls}" data-ref="${esc(p.id)}" transform="translate(${f(x)} ${f(Y(y))}) scale(${f(Math.min(sym, 2.2))})">${symbol(p.kind)}</g>`);
  }
  // earth electrodes / pits
  for (const b of model.boxes) {
    if (b.kind !== 'earth-pit' || floor !== 0) continue;
    out.push(`<g class="plan-earth${selectedRef === b.id ? ' selected' : ''}" data-ref="${esc(b.id)}" transform="translate(${f(b.position[0])} ${f(Y(b.position[1]))})"><rect x="-.15" y="-.15" width=".3" height=".3"/><path d="M-.1 .02H.1M-.065 .07H.065M-.03 .12H.03M0 -.1V.02"/></g>`);
  }
  // room labels
  for (const r of plan.rooms) if (r.enclosed) out.push(`<text class="plan-label" x="${f(r.label[0])}" y="${f(Y(r.label[1]))}" style="font-size:${f(k)}px">${esc(r.name)}</text>`);
  out.push(`<text class="plan-front" x="${f((x0 + x1) / 2)}" y="${f(Y(y0) - .3)}" style="font-size:${f(k * .9)}px">FRONT · ROAD SIDE</text>`);
  // scale bar (1 m) in the lower-left of the current view
  out.push(`<g class="plan-scale" transform="translate(${f(vb[0] + k * 2)} ${f(vb[1] + vb[3] - k * 2)})"><path d="M0 0H1M0 -.06V.06M1 -.06V.06" style="stroke-width:${f(k * .12)}px"/><text x=".5" y="${f(-k * .5)}" style="font-size:${f(k * .9)}px">1 m</text></g>`);
  out.push('</svg>');
  return out.join('');
}

// Plan symbols drawn around the origin (metres). Adapted conventional forms;
// see the legend for their meaning in this simulation.
function symbol(kind) {
  switch (kind) {
    case 'downlight': case 'light': return '<circle r=".11"/><path d="M-.078 -.078L.078 .078M-.078 .078L.078 -.078"/>';
    case 'mirror-light': case 'undercabinet': case 'cove': return '<rect x="-.14" y="-.05" width=".28" height=".1"/><path d="M-.1 0H.1"/>';
    case 'fan': return '<circle r=".13"/><path d="M0 0L.0 -.12M0 0L.104 .06M0 0L-.104 .06"/><circle r=".03" class="hub"/>';
    case 'exhaust': return '<rect x="-.12" y="-.12" width=".24" height=".24"/><path d="M-.08 -.08L.08 .08M-.08 .08L.08 -.08"/>';
    case 'socket6': return '<path d="M-.1 0A.1 .1 0 0 1 .1 0Z"/><path d="M0 -.1V-.16"/>';
    case 'socket16': return '<path d="M-.12 0A.12 .12 0 0 1 .12 0Z"/><path d="M-.05 -.12V-.18M.05 -.12V-.18"/>';
    case 'geyser-outlet': return '<rect x="-.12" y="-.08" width=".24" height=".16"/><text class="plan-sym" y=".04">G</text>';
    default: return '<circle r=".06"/>';
  }
}
