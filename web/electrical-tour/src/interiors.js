// Opened views: what an electrician sees with the cover off (de-energised in reality).
// Everything here is built on demand for one enclosure at a time and disposed on close.
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';
import { openBox, roundedPlate, frameGeometry, smoothTube, sweepTube, pathTube, s2t } from './geom.js';
import { mat, insulation, stripedInsulation, printedMaterial } from './materials.js';

const MW = .0225, MH = .045, DIN = .018;
const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);

export function wireRadius(size) {
  if (size == null) return .0027;           // service / submain / earthing: size by designer
  return ({ 1.5: .0015, 2.5: .0017, 4: .0021, 6: .0024, 10: .0031 })[size] || .0018;
}

function insulationMaterial(model, k) {
  const c = model.colour(k.colour);
  if (k.colour === 'PE') return stripedInsulation(c.hex, c.stripe);
  return insulation(c.hex);
}

// Wire from a to b (local coords) with start/end tangents; bare copper at a terminal end.
function wire(model, k, pts, { bareEnd = true, bareStart = false, radius } = {}) {
  const r = radius ?? wireRadius(k.size);
  const g = new THREE.Group();
  const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal', .5);
  const samples = Math.max(16, Math.round(curve.getLength() / .004));
  const all = curve.getSpacedPoints(samples);
  const bare = .011;                         // ~10-12 mm stripped (Legrand 10 mm, Easy9 12 mm)
  const len = curve.getLength();
  const cut0 = bareStart ? Math.min(.45, bare / len) : 0, cut1 = bareEnd ? Math.max(.55, 1 - bare / len) : 1;
  const ins = all.filter((_, i) => i / samples >= cut0 && i / samples <= cut1);
  const tube = sweepTube(ins.length > 1 ? ins : all, r, 8, { caps: true });
  const mesh = new THREE.Mesh(tube, insulationMaterial(model, k));
  mesh.userData = { kind: 'conductor', ref: k.id };
  g.add(mesh);
  if (bareEnd) {
    const tail = all.filter((_, i) => i / samples >= cut1 - .001);
    if (tail.length > 1) g.add(new THREE.Mesh(sweepTube(tail, r * .55, 6), mat('copper')));
  }
  if (bareStart) {
    const head = all.filter((_, i) => i / samples <= cut0 + .001);
    if (head.length > 1) g.add(new THREE.Mesh(sweepTube(head, r * .55, 6), mat('copper')));
  }
  g.userData = { kind: 'conductor', ref: k.id };
  return { group: g, mesh };
}

function screw(r = .0026) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, .0016, 14), mat('screw'));
  m.rotation.x = Math.PI / 2;
  const slot = new THREE.Mesh(new THREE.BoxGeometry(r * 1.6, r * .35, .0006), mat('galvDark'));
  slot.position.y = .0009;
  slot.rotation.x = -Math.PI / 2;
  m.add(slot);
  return m;
}

// Conduit mouths at an owner (local coords + inward direction), by conduit id.
function mouths(model, owner, inv) {
  const out = new Map();
  for (const cid of owner.conduitIds || []) {
    const c = model.get(cid);
    const pts = c.points;
    const atStart = c.from === owner.id;
    const p = atStart ? pts[0] : pts[pts.length - 1];
    const q = atStart ? pts[1] : pts[pts.length - 2];
    const P = s2t(p).applyMatrix4(inv), Q = s2t(q).applyMatrix4(inv);
    const dir = P.clone().sub(Q).normalize();          // pointing into the box
    out.set(cid, { pos: P, dir, conduit: c });
  }
  return out;
}

function laneOffset(i, n, r) {
  if (n <= 1) return new THREE.Vector2();
  const a = i / n * Math.PI * 2 + .4;
  return new THREE.Vector2(Math.cos(a) * r, Math.sin(a) * r);
}

function perpBasis(dir) {
  const up = Math.abs(dir.y) > .9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
  const u = up.clone().cross(dir).normalize();
  const w = dir.clone().cross(u).normalize();
  return [u, w];
}

// ------------------------------------------------------------------ flush modular box
export function openModularBox(ctx, enc, parts) {
  const { model } = ctx;
  const group = new THREE.Group();
  group.name = 'interior:' + enc.id;
  parts.group.add(group);
  const inv = model.frame(enc).clone().invert();
  const bw = enc.size.boxW, bh = enc.size.boxH, depth = enc.size.depth;
  const box = new THREE.Mesh(openBox(bw, bh, depth, .0012), mat('galv'));
  box.userData = { kind: 'enclosure', ref: enc.id };
  group.add(box);
  ctx.pickables.push(box);
  // knockouts and conduit stubs entering the box (CPWD: conduits enter boxes through bushes)
  const ms = mouths(model, enc, inv);
  for (const [cid, m] of ms) {
    const c = m.conduit, r = (c.diameter || 20) / 2000;
    const stubStart = m.pos.clone().addScaledVector(m.dir, -.06), stubEnd = m.pos.clone().addScaledVector(m.dir, .004);
    const stub = new THREE.Mesh(sweepTube([stubStart, stubEnd], r, 18), mat('conduit'));
    stub.userData = { kind: 'conduit', ref: cid };
    group.add(stub);
    ctx.pickables.push(stub);
    const bush = new THREE.Mesh(new THREE.TorusGeometry(r * .93, r * .16, 8, 24), mat('rubber'));
    bush.position.copy(stubEnd);
    bush.lookAt(stubEnd.clone().add(m.dir));
    group.add(bush);
    const inner = new THREE.Mesh(new THREE.CircleGeometry(r * .82, 20), mat('rubber'));
    inner.position.copy(stubEnd.clone().addScaledVector(m.dir, -.001));
    inner.lookAt(stubEnd.clone().add(m.dir));
    group.add(inner);
  }
  // P/N/E connector blocks (CPWD 3.5.6) and the earth stud (CPWD 4.3.3)
  const callouts = [];
  const termPos = new Map();
  const fixed = new Set(Object.values(enc.connectors || {}));
  const conMat = { P: printedMaterial('blk-P', 32, 32, (g) => { g.fillStyle = '#c23b2f'; g.fillRect(0, 0, 32, 32); }),
                   N: printedMaterial('blk-N', 32, 32, (g) => { g.fillStyle = '#222'; g.fillRect(0, 0, 32, 32); }),
                   E: printedMaterial('blk-E', 32, 32, (g) => { g.fillStyle = '#3f9442'; g.fillRect(0, 0, 32, 32); g.fillStyle = '#d6c52a'; g.fillRect(0, 12, 32, 8); }) };
  for (const [role, tid] of Object.entries(enc.connectors || {})) {
    const t = model.get(tid);
    const p = v3(t.local);
    if (role === 'stud') {
      const s = screw(.0032);
      s.position.copy(p);
      s.userData = { kind: 'terminal', ref: tid };
      group.add(s);
      ctx.pickables.push(s);
      const washer = new THREE.Mesh(new THREE.CylinderGeometry(.0048, .0048, .0006, 16), mat('screw'));
      washer.rotation.x = Math.PI / 2; washer.position.copy(p).add(new THREE.Vector3(0, 0, -.0011));
      group.add(washer);
      termPos.set(tid, { pos: p.clone().add(new THREE.Vector3(0, 0, .002)), dir: new THREE.Vector3(0, 0, 1) });
      callouts.push({ local: p.clone(), text: 'Box earth stud', ref: tid });
      continue;
    }
    const blk = new THREE.Mesh(new THREE.BoxGeometry(.014, .016, .012), mat('connector'));
    blk.position.copy(p).add(new THREE.Vector3(0, 0, -.004));
    blk.userData = { kind: 'terminal', ref: tid };
    group.add(blk);
    ctx.pickables.push(blk);
    const tag = new THREE.Mesh(new THREE.PlaneGeometry(.012, .0035), conMat[role]);
    tag.position.set(0, -.0062, .0061);
    blk.add(tag);
    const s = screw(.0024);
    s.position.set(0, .002, .0062);
    blk.add(s);
    termPos.set(tid, { pos: p.clone().add(new THREE.Vector3(0, -.003, .002)), dir: new THREE.Vector3(0, 0, 1) });
    callouts.push({ local: p.clone(), text: { P: 'Phase connector', N: 'Neutral connector', E: 'Earth connector' }[role], ref: tid });
  }
  // module rear housings and their terminals ride on the swinging assembly
  const assembly = parts.assembly;
  const rearGroup = new THREE.Group();
  assembly.add(rearGroup);
  for (const m of enc.modules) {
    if (m.kind === 'blank') continue;
    const span = m.span;
    const deep = m.kind === 'regulator' ? .056 : .036;
    const body = new THREE.Mesh(new THREE.BoxGeometry(span * MW - .0012, MH - .0012, deep), mat('moduleRear'));
    body.position.set(m.x, m.y, -deep / 2);
    body.userData = { kind: 'device', ref: m.deviceId };
    rearGroup.add(body);
    ctx.pickables.push(body);
  }
  const supportFrame = new THREE.Mesh(frameGeometry(bw - .004, bh - .004, Math.min(bw - .02, (enc.plateModules <= 8 ? enc.plateModules : 6) * MW + .004),
                                                    Math.min(bh - .02, (enc.plateModules <= 8 ? 1 : 2) * MH + .004), .0015, .001), mat('frame'));
  supportFrame.position.z = -.0015;
  rearGroup.add(supportFrame);
  // the support frame is screwed to the box lugs (two fixing screws)
  for (const sx of [-1, 1]) {
    const fs = screw(.0026);
    fs.position.set(sx * (bw / 2 - .009), 0, -.0005);
    fs.userData = { kind: 'enclosure', ref: enc.id };
    rearGroup.add(fs);
  }
  for (const t of model.termsByOwner.get(enc.id) || []) {
    if (fixed.has(t.id)) continue;
    const p = v3(t.local);
    const s = screw(.0021);
    s.position.copy(p).add(new THREE.Vector3(0, 0, -.0035));
    s.rotation.x = -Math.PI / 2;
    s.userData = { kind: 'terminal', ref: t.id };
    rearGroup.add(s);
    ctx.pickables.push(s);
    termPos.set(t.id, { pos: p.clone().add(new THREE.Vector3(0, 0, -.006)), dir: new THREE.Vector3(0, 0, -1), moving: true });
  }
  // curated callouts: one per kind of part (individual parts are identified by clicking them)
  const mods = enc.modules.filter((m) => m.kind !== 'blank');
  const firstOf = (kinds) => mods.find((m) => kinds.includes(m.kind));
  const sw = firstOf(['switch', 'switch16']), reg = firstOf(['regulator']), sock = firstOf(['socket6', 'socket16']), mcbm = firstOf(['mcb']);
  const conns = callouts.filter((c) => /connector$/.test(c.text));
  const stud = callouts.find((c) => c.text === 'Box earth stud');
  callouts.length = 0;
  if (ms.size) {
    const first = [...ms.values()][0];
    callouts.push({ local: first.pos.clone(), text: ms.size > 1 ? `${ms.size} conduit entries (circuit in, loop out, point wiring)` : 'Conduit entry', ref: [...ms.keys()][0] });
  }
  if (conns.length) callouts.push({ local: conns[0].local.clone().add(new THREE.Vector3(.02, 0, 0)), text: 'Phase · neutral · earth connector blocks (CPWD 3.5.6)', ref: conns[0].ref });
  if (sw) callouts.push({ local: new THREE.Vector3(sw.x, sw.y, -.02), text: mods.filter((m) => m.kind.startsWith('switch')).length > 1 ? 'Switches: live in → switched live out' : 'Switch: live in → switched live out', ref: sw.deviceId, moving: true });
  if (reg) callouts.push({ local: new THREE.Vector3(reg.x, reg.y, -.03), text: 'Fan regulator in series after its switch', ref: reg.deviceId, moving: true });
  if (sock) callouts.push({ local: new THREE.Vector3(sock.x, sock.y, -.02), text: 'Socket: L, N and earth terminals', ref: sock.deviceId, moving: true });
  if (mcbm) callouts.push({ local: new THREE.Vector3(mcbm.x, mcbm.y, -.02), text: 'Local 16 A MCB (water heater)', ref: mcbm.deviceId, moving: true });
  if (stud) callouts.push(stud);
  // conductors inside the box
  const wires = [];
  const wiresGroup = new THREE.Group();
  group.add(wiresGroup);
  const segs = segmentsAt(model, enc);
  const laneCount = new Map(), laneIndex = new Map();
  for (const s of segs) for (const end of [s.a, s.b]) if (end.mouth) laneCount.set(end.mouth, (laneCount.get(end.mouth) || 0) + 1);
  function endPoint(end, k) {
    if (end.mouth) {
      const m = ms.get(end.mouth);
      const n = laneCount.get(end.mouth) || 1;
      const i = laneIndex.get(end.mouth + k.id) ?? (laneIndex.set(end.mouth + k.id, laneIndex.get(end.mouth + '#') || 0), laneIndex.set(end.mouth + '#', (laneIndex.get(end.mouth + '#') || 0) + 1), laneIndex.get(end.mouth + k.id));
      const [u, w] = perpBasis(m.dir);
      const off = laneOffset(i, n, ((m.conduit.diameter || 20) / 2000) * .5);
      const p = m.pos.clone().addScaledVector(u, off.x).addScaledVector(w, off.y);
      return { pos: p, dir: m.dir.clone(), moving: false };
    }
    const tp = termPos.get(end.terminal);
    return tp ? { ...tp, pos: tp.pos.clone(), dir: tp.dir.clone() } : null;
  }
  for (const s of segs) {
    const a = endPoint(s.a, s.k), b = endPoint(s.b, s.k);
    if (!a || !b) continue;
    wires.push({ k: s.k, a, b, mesh: null, aT: s.a.terminal, bT: s.b.terminal });
  }
  const rebuild = () => {
    assembly.updateMatrix();
    for (const w of wires) {
      if (w.mesh) {
        wiresGroup.remove(w.mesh); w.mesh.traverse((o) => o.geometry?.dispose());
        const i = ctx.pickables.indexOf(w.pick); if (i >= 0) ctx.pickables.splice(i, 1);
      }
      const pa = w.a.moving ? w.a.pos.clone().applyMatrix4(assembly.matrix) : w.a.pos;
      const pb = w.b.moving ? w.b.pos.clone().applyMatrix4(assembly.matrix) : w.b.pos;
      const da = w.a.moving ? w.a.dir.clone().transformDirection(assembly.matrix) : w.a.dir;
      const db = w.b.moving ? w.b.dir.clone().transformDirection(assembly.matrix) : w.b.dir;
      // dress the wire: leave its entry, drop down the back of the box, then reach for the terminal
      const back = -depth + .01 + (wires.indexOf(w) % 5) * .003;
      const lane = ((wires.indexOf(w) % 9) - 4) * .006;
      const pts = [pa, pa.clone().addScaledVector(da, .012)];
      const moving = w.a.moving || w.b.moving;
      if (!w.a.moving) pts.push(new THREE.Vector3(pa.x + lane * .5, Math.max(Math.min(pa.y, pb.y), -bh / 2 + .02) * .6, back));
      if (moving) {
        const tip = (w.b.moving ? pb : pa);
        pts.push(new THREE.Vector3((tip.x + (w.b.moving ? pa.x : pb.x)) / 2 + lane, -bh / 2 + .006, .02));
      } else pts.push(new THREE.Vector3((pa.x + pb.x) / 2 + lane, (pa.y + pb.y) / 2 - .012, back + .006));
      if (!w.b.moving) pts.push(new THREE.Vector3(pb.x + lane * .5, pb.y + .012, back));
      pts.push(pb.clone().addScaledVector(db, .012), pb);
      if (w.b.moving && !w.a.moving) { /* order already a -> b */ }
      const built = wire(ctx.model, w.k, pts, { bareEnd: Boolean(w.bT), bareStart: Boolean(w.aT) });
      w.mesh = built.group;
      wiresGroup.add(w.mesh);
      w.pick = built.mesh;
      ctx.pickables.push(built.mesh);
    }
  };
  rebuild();
  const plateW = enc.size.w;
  let t = 0;
  const handle = {
    enc, group, wires, callouts, kind: 'box',
    set(progress) {
      t = Math.max(0, Math.min(1, progress));
      const e = t * t * (3 - 2 * t);
      // pull the plate assembly forward, then swing it open about its left edge
      const pull = Math.min(1, e / .35), swing = Math.max(0, (e - .35) / .65);
      const ang = swing * 1.35;                 // about 77 degrees: module backs turn toward the viewer
      assembly.position.set(-plateW / 2 * (1 - Math.cos(ang)) - swing * .05, -swing * .03, .012 + pull * .11 + Math.sin(ang) * plateW / 2);
      assembly.rotation.y = -ang;
      rebuild();
    },
    anchor(c) {
      const p = c.local.clone();
      if (c.moving) { assembly.updateMatrix(); p.applyMatrix4(assembly.matrix); }
      return p.applyMatrix4(parts.group.matrixWorld);
    },
    dispose() {
      parts.group.remove(group);
      assembly.remove(rearGroup);
      group.traverse((o) => o.geometry?.dispose());
      rearGroup.traverse((o) => o.geometry?.dispose());
      assembly.position.set(0, 0, 0);
      assembly.rotation.set(0, 0, 0);
    },
  };
  return handle;
}

// Conductors to draw inside an owner: terminal<->terminal (internal), terminal<->conduit mouth, and
// mouth<->mouth pass-throughs (a conductor running through a box without being joined).
export function segmentsAt(model, owner) {
  const out = [];
  const here = (tid) => { const t = model.get(tid); return t && (t.enclosureId === owner.id || t.boxId === owner.id); };
  const conductors = new Set(model.conductorsOf(owner.id));
  for (const cid of owner.conduitIds || []) for (const k of model.conductorsByConduit.get(cid) || []) conductors.add(k);
  for (const k of conductors) {
    const ha = here(k.from), hb = here(k.to);
    if (ha && hb) { out.push({ k, a: { terminal: k.from }, b: { terminal: k.to } }); continue; }
    if (ha && k.conduits.length) { out.push({ k, a: { terminal: k.from }, b: { mouth: k.conduits[0] } }); continue; }
    if (hb && k.conduits.length) { out.push({ k, a: { mouth: k.conduits[k.conduits.length - 1] }, b: { terminal: k.to } }); continue; }
    for (let i = 0; i < k.conduits.length - 1; i++) {
      const c1 = model.get(k.conduits[i]), c2 = model.get(k.conduits[i + 1]);
      const shared = [c1.from, c1.to].find((x) => x === c2.from || x === c2.to);
      if (shared === owner.id) out.push({ k, a: { mouth: c1.id }, b: { mouth: c2.id } });
    }
  }
  return out;
}

// ------------------------------------------------------------------ distribution board + loose-wire box
export function openDB(ctx, enc, parts, lwbEnc, lwbParts) {
  const { model } = ctx;
  const group = new THREE.Group();
  group.name = 'interior:' + enc.id;
  parts.group.add(group);
  const W = enc.size.w, H = enc.size.h, D = enc.size.depth;
  const box = new THREE.Mesh(openBox(W - .004, H - .004, D, .0015), mat('enclosureInner'));
  box.userData = { kind: 'enclosure', ref: enc.id };
  group.add(box);
  ctx.pickables.push(box);
  const callouts = [];
  const devices = model.devicesByEnclosure.get(enc.id) || [];
  const termPos = new Map();
  const rails = new Set(devices.filter((d) => d.y != null && ['mcb', 'mcb4p', 'rccb4p', 'isolator2p'].includes(d.kind)).map((d) => d.y));
  for (const y of rails) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(W - .05, .035, .0075), mat('dinRail'));
    rail.position.set(0, y, -D + .012);
    group.add(rail);
  }
  const front = -.006;
  for (const d of devices) {
    if (['mcb', 'mcb4p', 'rccb4p', 'isolator2p'].includes(d.kind)) {
      const w = d.modules * DIN - .0006;
      const g = new THREE.Group();
      g.position.set(d.x, d.y, 0);
      const back = new THREE.Mesh(new THREE.BoxGeometry(w, .081, .044), mat('device'));
      back.position.z = -D + .016 + .022;
      const nose = new THREE.Mesh(new THREE.BoxGeometry(w, .045, D - .016 - .044 + front), mat('device'));
      nose.position.z = (-D + .016 + .044 + front) / 2;
      back.userData = nose.userData = { kind: 'device', ref: d.id };
      g.add(back, nose);
      ctx.pickables.push(back, nose);
      const toggle = new THREE.Mesh(new THREE.BoxGeometry(Math.min(w - .004, .012 * (d.poles > 1 ? 2.6 : 1)), .014, .008), mat(d.kind === 'rccb4p' ? 'toggleRed' : 'toggle'));
      toggle.position.set(0, .006, front + .002);
      toggle.userData = { kind: 'device', ref: d.id, toggle: true };
      g.add(toggle);
      ctx.pickables.push(toggle);
      d._toggle = toggle;
      if (d.kind === 'rccb4p') {
        const test = new THREE.Mesh(new THREE.CylinderGeometry(.0035, .0035, .004, 12), mat('deviceGrey'));
        test.rotation.x = Math.PI / 2; test.position.set(w / 2 - .01, -.014, front + .001);
        g.add(test);
      }
      const label = new THREE.Mesh(new THREE.PlaneGeometry(w - .002, .01), printedMaterial('lbl:' + d.id, 128, 40, (c, cw, ch) => {
        c.fillStyle = '#f2f1ea'; c.fillRect(0, 0, cw, ch);
        c.fillStyle = '#26302c'; c.font = `bold ${d.kind === 'mcb' ? 26 : 22}px system-ui`; c.textAlign = 'center';
        c.fillText(d.kind === 'mcb' ? d.circuitId : d.kind === 'rccb4p' ? 'RCCB 30mA' : d.kind === 'mcb4p' ? 'MAIN' : 'ISOL', cw / 2, 29);
      }));
      label.position.set(0, -.016, front + .0005);
      g.add(label);
      if (d.phase) {
        const mark = new THREE.Mesh(new THREE.PlaneGeometry(.006, .003), insulation(model.colour(d.phase).hex));
        mark.position.set(0, .019, front + .0005);
        g.add(mark);
      }
      group.add(g);
      for (const [name, tid] of Object.entries(d.terminals || {})) {
        const t = model.get(tid);
        const p = v3(t.local);
        const s = screw(.0022);
        s.position.set(p.x, p.y + (p.y > d.y ? -.004 : .004), front + .0004);
        group.add(s);
        termPos.set(tid, { pos: p.clone(), dir: new THREE.Vector3(0, Math.sign(p.y - d.y) || 1, 0) });
      }
      if (d.kind === 'mcb4p') callouts.push({ local: new THREE.Vector3(d.x, d.y, front), text: 'Incoming 4-pole MCB (main switch)', ref: d.id });
      if (d.kind === 'rccb4p') callouts.push({ local: new THREE.Vector3(d.x, d.y, front), text: 'RCCB 4-pole, 30 mA, Type A', ref: d.id });
      if (d.kind === 'isolator2p') callouts.push({ local: new THREE.Vector3(d.x, d.y, front), text: 'Incoming 2-pole isolator', ref: d.id });
    } else if (d.kind === 'neutral-bar' || d.kind === 'earth-bar') {
      const n = Object.keys(d.terminals || {}).length;
      const len = Math.max(.07, n * .01 + .02);
      const bar = new THREE.Mesh(new THREE.BoxGeometry(len, .009, .007), mat(d.kind === 'neutral-bar' ? 'brass' : 'tinned'));
      const x0 = Math.min(...Object.values(d.terminals || {}).map((tid) => model.get(tid).local[0]).concat([d.x])) - .012;
      bar.position.set(x0 + len / 2, d.y, -D + .03);
      bar.userData = { kind: 'device', ref: d.id };
      group.add(bar);
      ctx.pickables.push(bar);
      for (const sx of [x0 + .004, x0 + len - .004]) {
        const ins = new THREE.Mesh(new THREE.CylinderGeometry(.004, .004, .02, 12), mat(d.kind === 'neutral-bar' ? 'rubber' : 'galvDark'));
        ins.rotation.x = Math.PI / 2; ins.position.set(sx, d.y, -D + .015);
        group.add(ins);
      }
      const tagMat = d.kind === 'neutral-bar' ? printedMaterial('tag-N', 64, 32, (c) => { c.fillStyle = '#2a2a2a'; c.fillRect(0, 0, 64, 32); c.fillStyle = '#fff'; c.font = 'bold 24px system-ui'; c.fillText('N', 24, 25); })
        : printedMaterial('tag-PE', 64, 32, (c) => { c.fillStyle = '#3f9442'; c.fillRect(0, 0, 64, 32); c.fillStyle = '#d6c52a'; c.fillRect(0, 10, 64, 12); c.fillStyle = '#111'; c.font = 'bold 20px system-ui'; c.fillText('PE', 18, 23); });
      const tag = new THREE.Mesh(new THREE.PlaneGeometry(.016, .008), tagMat);
      tag.position.set(x0 - .012, d.y, -D + .035);
      group.add(tag);
      for (const tid of Object.values(d.terminals || {})) {
        const t = model.get(tid);
        const s = screw(.0019);
        s.position.set(t.local[0], d.y, -D + .034);
        group.add(s);
        termPos.set(tid, { pos: new THREE.Vector3(t.local[0], d.y - .006, -D + .03), dir: new THREE.Vector3(0, -1, .3).normalize() });
      }
      callouts.push({ local: new THREE.Vector3(x0 + len / 2, d.y, -D + .03), text: d.label, ref: d.id });
    } else if (d.kind === 'busbar') {
      const feeds = Object.values(d.terminals || {});
      const outs = devices.filter((x) => x.kind === 'mcb');
      if (!outs.length) continue;
      const xs = outs.map((x) => x.x);
      const y = outs[0].y + .034;
      const len = Math.max(...xs) - Math.min(...xs) + DIN + .02;
      const cx = (Math.max(...xs) + Math.min(...xs)) / 2;
      const bar = new THREE.Mesh(new THREE.BoxGeometry(len, .006, .012), mat('copper'));
      bar.position.set(cx, y + .006, -D + .05);
      bar.userData = { kind: 'device', ref: d.id };
      const cover = new THREE.Mesh(new THREE.BoxGeometry(len + .004, .01, .016), new THREE.MeshStandardMaterial({ color: '#5d6467', roughness: .5, transparent: true, opacity: .45 }));
      cover.position.copy(bar.position);
      cover.userData = { kind: 'device', ref: d.id };
      group.add(bar, cover);
      ctx.pickables.push(bar, cover);
      for (const o of outs) {
        const tooth = new THREE.Mesh(new THREE.BoxGeometry(.004, .012, .006), mat('copper'));
        tooth.position.set(o.x, y, -D + .05);
        group.add(tooth);
        const ph = new THREE.Mesh(new THREE.BoxGeometry(.006, .003, .0162), insulation(model.colour(o.phase).hex));
        ph.position.set(o.x, y + .011, -D + .05);
        group.add(ph);
      }
      for (const tid of feeds) termPos.set(tid, { pos: v3(model.get(tid).local), dir: new THREE.Vector3(-1, 0, 0) });
      callouts.push({ local: new THREE.Vector3(cx, y + .006, -D + .05), text: d.label, ref: d.id });
    }
  }
  const outs = devices.filter((x) => x.kind === 'mcb');
  if (outs.length) callouts.push({ local: new THREE.Vector3(outs[Math.floor(outs.length / 2)].x, outs[0].y, front), text: `Outgoing MCBs (${outs.length} ways)`, ref: outs[0].id });
  // dead-front (centre plate) lifts away when opened
  const dead = new THREE.Mesh(frameGeometry(W - .012, H - .012, W - .06, .16, .0015, .002), mat('deadFront'));
  dead.position.z = front - .0002;
  group.add(dead);
  // wires: everything with an end at this DB (or passing to the loose-wire box)
  const inv = model.frame(enc).clone().invert();
  const ms = mouths(model, enc, inv);
  for (const [cid, m] of ms) {
    const c = m.conduit, r = (c.diameter || 20) / 2000;
    const stub = new THREE.Mesh(sweepTube([m.pos.clone().addScaledVector(m.dir, -.07), m.pos.clone().addScaledVector(m.dir, .005)], r, 18), mat(c.function === 'service' ? 'galvDark' : 'conduit'));
    stub.userData = { kind: 'conduit', ref: cid };
    group.add(stub);
    ctx.pickables.push(stub);
  }
  const wiresGroup = new THREE.Group();
  group.add(wiresGroup);
  const counts = new Map();
  const segs = segmentsAt(model, enc).filter((s) => s.k.kind !== 'busbar');
  segs.forEach((s) => { for (const e of [s.a, s.b]) if (e.mouth) counts.set(e.mouth, (counts.get(e.mouth) || 0) + 1); });
  const used = new Map();
  const ep = (e, k) => {
    if (e.terminal) return termPos.get(e.terminal) || { pos: v3(model.get(e.terminal).local), dir: new THREE.Vector3(0, 0, 1) };
    const m = ms.get(e.mouth);
    const i = used.get(e.mouth) || 0; used.set(e.mouth, i + 1);
    const [u, w] = perpBasis(m.dir);
    const off = laneOffset(i, counts.get(e.mouth) || 1, ((m.conduit.diameter || 20) / 2000) * .55);
    return { pos: m.pos.clone().addScaledVector(u, off.x).addScaledVector(w, off.y), dir: m.dir.clone() };
  };
  const channelX = W / 2 - .028;
  const wires = [];
  for (const s of segs) {
    const a = ep(s.a, s.k), b = ep(s.b, s.k);
    if (!a || !b) continue;
    // route along the wiring channel at the side, behind the devices
    const zc = -D + .022;
    const side = (a.pos.x + b.pos.x) / 2 > 0 ? channelX : -channelX;
    const pts = [a.pos, a.pos.clone().addScaledVector(a.dir, .014)];
    if (Math.abs(a.pos.y - b.pos.y) > .05) {
      pts.push(new THREE.Vector3(side - Math.sign(side) * (wires.length % 6) * .0035, a.pos.y + a.dir.y * .02, zc));
      pts.push(new THREE.Vector3(side - Math.sign(side) * (wires.length % 6) * .0035, b.pos.y + b.dir.y * .02, zc));
    } else pts.push(a.pos.clone().add(b.pos).multiplyScalar(.5).add(new THREE.Vector3(0, .012, -.004)));
    pts.push(b.pos.clone().addScaledVector(b.dir, .014), b.pos);
    const built = wire(model, s.k, pts, { bareEnd: Boolean(s.b.terminal), bareStart: Boolean(s.a.terminal) });
    wiresGroup.add(built.group);
    ctx.pickables.push(built.mesh);
    wires.push({ k: s.k, mesh: built.group });
  }
  callouts.push({ local: new THREE.Vector3(-W / 2 + .06, -H / 2 + .03, -D / 2), text: 'Incoming meter tails (R, Y, B, N)', ref: wires.find((w) => w.k.kind === 'meter-tail')?.k.id });
  let lwbHandle = null;
  if (lwbEnc && lwbParts) lwbHandle = openLWB(ctx, lwbEnc, lwbParts);
  const handle = {
    enc, group, wires, kind: 'db',
    callouts: callouts.concat(lwbHandle ? lwbHandle.callouts.map((c) => ({ ...c, lwb: true })) : []),
    set(progress) {
      const e = Math.max(0, Math.min(1, progress));
      const s = e * e * (3 - 2 * e);
      if (parts.left) parts.left.rotation.y = -s * 1.9;
      if (parts.right) parts.right.rotation.y = s * 1.9;
      dead.position.set(-s * .02, -s * (H * .55), front - .0002 + s * .16);
      dead.rotation.x = s * .35;
      dead.visible = s < .999;
      lwbHandle?.set(progress);
    },
    anchor(c) {
      if (c.lwb) return lwbHandle.anchor(c);
      return c.local.clone().applyMatrix4(parts.group.matrixWorld);
    },
    dispose() {
      parts.group.remove(group);
      group.traverse((o) => o.geometry?.dispose());
      if (parts.left) parts.left.rotation.y = 0;
      if (parts.right) parts.right.rotation.y = 0;
      lwbHandle?.dispose();
    },
  };
  return handle;
}

function openLWB(ctx, enc, parts) {
  const { model } = ctx;
  const group = new THREE.Group();
  parts.group.add(group);
  const W = enc.size.w, H = enc.size.h, D = enc.size.depth;
  const box = new THREE.Mesh(openBox(W - .004, H - .004, D, .0015), mat('enclosureInner'));
  box.userData = { kind: 'enclosure', ref: enc.id };
  group.add(box);
  ctx.pickables.push(box);
  const rail = new THREE.Mesh(new THREE.BoxGeometry(W - .04, .035, .0075), mat('dinRail'));
  rail.position.set(0, -.02, -D + .012);
  group.add(rail);
  const termPos = new Map();
  const callouts = [];
  const colours = { P: '#b8352b', N: '#2a2a2a', E: '#3f9442' };
  for (const t of model.termsByOwner.get(enc.id) || []) {
    const p = v3(t.local);
    const blk = new THREE.Mesh(new THREE.BoxGeometry(.0062, .042, .045), new THREE.MeshStandardMaterial({ color: colours[t.role] || '#888', roughness: .55 }));
    blk.position.set(p.x, -.02, -D + .012 + .0225);
    blk.userData = { kind: 'terminal', ref: t.id };
    group.add(blk);
    ctx.pickables.push(blk);
    for (const sy of [.012, -.012]) {
      const s = screw(.0017);
      s.position.set(p.x, -.02 + sy, -D + .0355);
      group.add(s);
    }
    termPos.set(t.id + ':low', { pos: new THREE.Vector3(p.x, -.02 - .024, -D + .03), dir: new THREE.Vector3(0, -1, 0) });
    termPos.set(t.id + ':high', { pos: new THREE.Vector3(p.x, -.02 + .024, -D + .03), dir: new THREE.Vector3(0, 1, 0) });
  }
  const blocks = (model.termsByOwner.get(enc.id) || []);
  if (blocks.length) {
    const xs = blocks.map((b) => b.local[0]);
    callouts.push({ local: new THREE.Vector3((Math.min(...xs) + Math.max(...xs)) / 2, -.02, -D + .04), text: `Outgoing P/N/E terminal blocks (${blocks.length / 3} circuits)`, ref: blocks[0].id });
  }
  const inv = model.frame(enc).clone().invert();
  const ms = mouths(model, enc, inv);
  for (const [cid, m] of ms) {
    const r = (m.conduit.diameter || 20) / 2000;
    const stub = new THREE.Mesh(sweepTube([m.pos.clone().addScaledVector(m.dir, -.07), m.pos.clone().addScaledVector(m.dir, .005)], r, 18), mat('conduit'));
    stub.userData = { kind: 'conduit', ref: cid };
    group.add(stub);
    ctx.pickables.push(stub);
  }
  if (ms.size) callouts.push({ local: [...ms.values()][0].pos.clone(), text: 'Outgoing circuit conduits (to slab)', ref: [...ms.keys()][0] });
  const counts = new Map();
  const segs = segmentsAt(model, enc);
  segs.forEach((s) => { for (const e of [s.a, s.b]) if (e.mouth) counts.set(e.mouth, (counts.get(e.mouth) || 0) + 1); });
  const used = new Map();
  for (const s of segs) {
    const fromBelow = (e) => e.mouth && model.get(e.mouth).kind === 'coupler';
    const termEnd = s.a.terminal ? s.a : s.b, other = s.a.terminal ? s.b : s.a;
    if (!termEnd.terminal || !other.mouth) continue;
    const below = fromBelow(other);
    const tp = termPos.get(termEnd.terminal + (below ? ':low' : ':high'));
    const m = ms.get(other.mouth);
    if (!tp || !m) continue;
    const i = used.get(other.mouth) || 0; used.set(other.mouth, i + 1);
    const [u, w] = perpBasis(m.dir);
    const off = laneOffset(i, counts.get(other.mouth) || 1, ((m.conduit.diameter || 20) / 2000) * .55);
    const mp = m.pos.clone().addScaledVector(u, off.x).addScaledVector(w, off.y);
    const pts = [mp, mp.clone().addScaledVector(m.dir, .02), tp.pos.clone().addScaledVector(tp.dir, .02), tp.pos];
    const built = wire(model, s.k, pts, { bareEnd: true });
    group.add(built.group);
    ctx.pickables.push(built.mesh);
  }
  const cover = parts.cover;
  return {
    callouts,
    set(progress) {
      const s = progress * progress * (3 - 2 * progress);
      if (cover) { cover.position.set(0, s * (H * .9), .006 + s * .12); cover.visible = s < .999; }
    },
    anchor(c) { return c.local.clone().applyMatrix4(parts.group.matrixWorld); },
    dispose() { parts.group.remove(group); group.traverse((o) => o.geometry?.dispose()); if (cover) { cover.position.set(0, 0, .006); cover.visible = true; } },
  };
}

// ------------------------------------------------------------------ slab point boxes (light / fan / cove)
export function openSlabBox(ctx, box, extras = {}) {
  const { model } = ctx;
  const frame = model.frame(box);
  const holder = new THREE.Group();
  frame.decompose(holder.position, holder.quaternion, holder.scale);
  ctx.root.add(holder);
  const r = box.size[0] / 2, depth = box.size[2];
  const body = new THREE.Mesh(new THREE.CylinderGeometry(r, r, depth, 32, 1, true), mat('pvcBox'));
  body.rotation.x = Math.PI / 2;
  body.position.z = -depth / 2;
  body.material.side = THREE.DoubleSide;
  body.userData = { kind: 'box', ref: box.id };
  const lid = new THREE.Mesh(new THREE.CircleGeometry(r, 32), mat('pvcBox'));
  lid.position.z = -depth;
  holder.add(body, lid);
  ctx.pickables.push(body);
  const callouts = [{ local: new THREE.Vector3(0, 0, -depth / 2), text: box.label, ref: box.id }];
  if (box.kind === 'fan-box') {
    // CPWD Fig. 4: 12 mm MS U-rod bound to the top reinforcement; exposed loop ~100 mm below the ceiling
    const hook = pathTube([[-.045, 0, -depth - .05], [-.045, 0, .01], [-.045, 0, .07], [.045, 0, .07], [.045, 0, .01], [.045, 0, -depth - .05]].map((p) => new THREE.Vector3(...p)), .006, { bend: .03 });
    const hm = new THREE.Mesh(hook, mat('hook'));
    hm.userData = { kind: 'box', ref: box.id };
    holder.add(hm);
    const ins = new THREE.Mesh(new THREE.TorusGeometry(.016, .006, 10, 24), mat('rubber'));
    ins.position.set(0, 0, .082);
    holder.add(ins);
    callouts.push({ local: new THREE.Vector3(0, 0, .07), text: 'Fan hook (12 mm MS U-rod) with insulator', ref: box.id });
  }
  // a 3-way connector hanging just inside the box mouth
  const termPos = new Map();
  for (const t of model.termsByOwner.get(box.id) || []) {
    const p = v3(t.local);
    p.z = .01;
    const blk = new THREE.Mesh(new THREE.BoxGeometry(.011, .013, .011), mat('connector'));
    blk.position.copy(p);
    blk.userData = { kind: 'terminal', ref: t.id };
    holder.add(blk);
    ctx.pickables.push(blk);
    termPos.set(t.id, { pos: p.clone().add(new THREE.Vector3(0, 0, -.007)), dir: new THREE.Vector3(0, 0, -1) });
  }
  callouts.push({ local: new THREE.Vector3(0, 0, .012), text: box.kind === 'fan-box' ? 'Fan connector (house wiring side)' : 'Point connector', ref: (model.termsByOwner.get(box.id) || [])[0]?.id });
  const inv = frame.clone().invert();
  const ms = mouths(model, box, inv);
  for (const [cid, m] of ms) {
    const rr = (m.conduit.diameter || 20) / 2000;
    const stub = new THREE.Mesh(sweepTube([m.pos.clone().addScaledVector(m.dir, -.08), m.pos.clone().addScaledVector(m.dir, .004)], rr, 16), mat('conduit'));
    stub.userData = { kind: 'conduit', ref: cid };
    holder.add(stub);
    ctx.pickables.push(stub);
  }
  const counts = new Map();
  const segs = segmentsAt(model, box);
  segs.forEach((s) => { for (const e of [s.a, s.b]) if (e.mouth) counts.set(e.mouth, (counts.get(e.mouth) || 0) + 1); });
  const used = new Map();
  const ep = (e) => {
    if (e.terminal) return termPos.get(e.terminal);
    const m = ms.get(e.mouth);
    if (!m) return null;
    const i = used.get(e.mouth) || 0; used.set(e.mouth, i + 1);
    const [u, w] = perpBasis(m.dir);
    const off = laneOffset(i, counts.get(e.mouth) || 1, ((m.conduit.diameter || 20) / 2000) * .5);
    return { pos: m.pos.clone().addScaledVector(u, off.x).addScaledVector(w, off.y), dir: m.dir.clone() };
  };
  for (const s of segs) {
    const a = ep(s.a), b = ep(s.b);
    if (!a || !b) continue;
    const mid = a.pos.clone().add(b.pos).multiplyScalar(.5);
    mid.z = Math.min(mid.z, -.015);
    const built = wire(model, s.k, [a.pos, a.pos.clone().addScaledVector(a.dir, .015), mid, b.pos.clone().addScaledVector(b.dir, .015), b.pos],
                       { bareEnd: Boolean(s.b.terminal), bareStart: Boolean(s.a.terminal) });
    holder.add(built.group);
    ctx.pickables.push(built.mesh);
  }
  if (box.kind === 'fan-box') {
    // the fan's own supply leads leave the connector down the rod (fan side; internal motor wiring not shown)
    const leads = new THREE.Group();
    const colours = ['#b5302a', '#1e1f21', '#3e9440'];
    [-.012, 0, .012].forEach((x, i) => {
      const g = smoothTube([new THREE.Vector3(x, 0, .017), new THREE.Vector3(x * .3, .004, .05), new THREE.Vector3(0, .0, .2)], .0011, { samples: 24 });
      const m = new THREE.Mesh(g, insulation(colours[i]));
      m.userData = { kind: 'fan-lead', ref: box.pointId };
      leads.add(m);
      ctx.pickables.push(m);
    });
    holder.add(leads);
    callouts.push({ local: new THREE.Vector3(0, .004, .08), text: "Fan's own leads (manufacturer side)", ref: box.pointId });
  }
  return {
    enc: box, group: holder, callouts, kind: 'slab',
    set() {},
    anchor(c) { return c.local.clone().applyMatrix4(holder.matrixWorld); },
    dispose() { ctx.root.remove(holder); holder.traverse((o) => o.geometry?.dispose()); },
  };
}

// Wall outlet box behind a mirror light, under-cabinet light or exhaust-fan cord outlet.
export function openWallBox(ctx, box, outletParts) {
  const fake = { ...box, size: { boxW: box.size[0], boxH: box.size[1], depth: box.size[2], w: .086 }, connectors: {}, modules: [], plateModules: 2 };
  const parts = { group: outletParts.group, assembly: outletParts.assembly || outletParts.group };
  return openModularBox(ctx, fake, parts);
}
