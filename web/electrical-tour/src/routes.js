// Route overlay for a selected circuit and the physical cutaway for the current walk step.
//
// * Trace: a thin cyan strip drawn on the finished ceiling or wall face directly in front
//   of each concealed conduit (pieces precomputed by the builder). It is depth-tested, so
//   walls still hide other rooms; it is an engineering overlay, not a physical object.
// * Cutaway: for one straight piece at a time, a clipping opening in the surface backed by a
//   modelled chase (recess), the real conduit at its true depth cut open lengthwise, and its
//   conductors inside, coloured by their insulation.
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';
import { s2t, sweepTube } from './geom.js';
import { mat, insulation, stripedInsulation, printedTexture, OVERLAY } from './materials.js';
import { chaseOpening } from './aperture.js';
import { wireRadius } from './interiors.js';

const CUT_MAX = 1.2;   // longest inspection chase opened at once (m)

let traceTex = null;
function traceMaterial(strong) {
  traceTex ||= printedTexture(64, 16, (g, w, h) => {
    g.clearRect(0, 0, w, h);
    const grd = g.createLinearGradient(0, 0, 0, h);
    grd.addColorStop(0, 'rgba(62,199,216,0)'); grd.addColorStop(.32, 'rgba(62,199,216,.55)');
    grd.addColorStop(.5, 'rgba(160,240,248,1)'); grd.addColorStop(.68, 'rgba(62,199,216,.55)'); grd.addColorStop(1, 'rgba(62,199,216,0)');
    g.fillStyle = grd; g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(255,255,255,.85)'; g.fillRect(4, h / 2 - 1.5, 14, 3);
  }, 'trace-strip');
  if (traceTex.wrapS !== THREE.RepeatWrapping) { traceTex.wrapS = THREE.RepeatWrapping; traceTex.needsUpdate = true; }
  return new THREE.MeshBasicMaterial({ map: traceTex, color: strong ? '#ffffff' : '#c8f6fb', transparent: true, opacity: strong ? .95 : .7,
    depthWrite: false, toneMapped: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
}

function strip(a, b, normal, width) {
  const A = s2t(a), B = s2t(b), n = new THREE.Vector3(normal[0], normal[2], -normal[1]);
  const dir = B.clone().sub(A);
  const len = dir.length();
  if (len < 1e-4) return null;
  dir.normalize();
  const side = dir.clone().cross(n).normalize().multiplyScalar(width / 2);
  const off = n.clone().multiplyScalar(.0012);
  const p = [A.clone().add(side).add(off), A.clone().sub(side).add(off), B.clone().sub(side).add(off), B.clone().add(side).add(off)];
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(p.flatMap((v) => [v.x, v.y, v.z]), 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 0, 1, len / .2, 1, len / .2, 0], 2));
  g.setIndex([0, 1, 2, 0, 2, 3]);
  return g;
}

export class RouteLayer {
  constructor(ctx) {
    this.ctx = ctx;
    this.group = new THREE.Group();
    this.group.name = 'Engineering overlay: traced route';
    this.group.renderOrder = 20;
    ctx.root.add(this.group);
    this.cut = null;
    this.circuitId = null;
  }

  conduitsFor(circuitId) {
    const m = this.ctx.model;
    const c = m.circuit(circuitId);
    if (!c) return [];
    const ids = new Set(m.data.conduits.filter((k) => k.circuitIds.includes(circuitId)).map((k) => k.id));
    for (const k of m.data.conduits) if (k.function === 'service') ids.add(k.id);
    if (c.floor === 1 || circuitId === 'SUB') for (const k of m.data.conduits) if (k.circuitIds.includes('SUB')) ids.add(k.id);
    return [...ids].map((id) => m.get(id));
  }

  show(circuitId, { emphasise = [] } = {}) {
    this.clear();
    this.circuitId = circuitId;
    if (!circuitId) return;
    const strong = new Set(emphasise);
    const weak = traceMaterial(false), hot = traceMaterial(true);
    for (const c of this.conduitsFor(circuitId)) {
      for (const [pi, p] of (c.reveal || []).entries()) {
        const g = strip(p.a, p.b, p.normal, strong.has(c.id) ? .036 : .028);
        if (!g) continue;
        const mesh = new THREE.Mesh(g, strong.has(c.id) ? hot : weak);
        mesh.renderOrder = 20;
        mesh.userData = { kind: 'trace', ref: c.id, overlay: true, piece: pi };
        mesh.frustumCulled = true;
        this.group.add(mesh);
        this.ctx.pickables.push(mesh);
      }
    }
    // small rings where the route meets a box on a surface
    const ring = new THREE.RingGeometry(.022, .03, 24);
    const ringMat = new THREE.MeshBasicMaterial({ color: OVERLAY.trace, transparent: true, opacity: .9, depthWrite: false, toneMapped: false, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -3 });
    for (const pid of this.ctx.model.pointsByCircuit.get(circuitId) || []) {
      const box = pid.boxId && this.ctx.model.get(pid.boxId);
      if (!box || !box.position || box.mount) continue;
      const r = new THREE.Mesh(ring, ringMat);
      r.position.copy(s2t([box.position[0], box.position[1], box.position[2] - .003]));
      r.rotation.x = Math.PI / 2;
      r.renderOrder = 21;
      this.group.add(r);
    }
    this.ctx.viewer.dirty = true;
  }

  // texture drift along the route while the circuit is supplied (direction of supply)
  flow(t) {
    if (!traceTex) return;
    traceTex.wrapS = THREE.RepeatWrapping;
    traceTex.offset.x = t == null ? 0 : -(t * .6) % 1;
  }

  clear() {
    for (const o of [...this.group.children]) { this.group.remove(o); o.geometry?.dispose(); }
    this.ctx.pickables.splice(0, this.ctx.pickables.length, ...this.ctx.pickables.filter((p) => !p.userData?.overlay));
    this.circuitId = null;
    this.ctx.viewer.dirty = true;
  }

  // ---------------------------------------------------------------- physical cutaway
  // Open a local inspection chase (at most CUT_MAX long) on the longest revealed piece of
  // the conduit in `roomId`, centred on `focus` (world point) when given.
  openCut(conduitId, roomId, focus = null) {
    this.closeCut();
    const m = this.ctx.model;
    const c = m.get(conduitId);
    if (!c || !c.reveal?.length) return null;
    const pieces = c.reveal.filter((p) => !roomId || p.roomId === roomId);
    const piece = (pieces.length ? pieces : c.reveal).reduce((best, p) => {
      const L = Math.hypot(p.b[0] - p.a[0], p.b[1] - p.a[1], p.b[2] - p.a[2]);
      return !best || L > best.L ? { p, L } : best;
    }, null)?.p;
    if (!piece) return null;
    let A = s2t(piece.a), B = s2t(piece.b);
    const full = A.distanceTo(B);
    const clipped = full > CUT_MAX;
    if (clipped) {
      const dir = B.clone().sub(A).normalize();
      const t = focus ? Math.min(Math.max(focus.clone().sub(A).dot(dir), CUT_MAX / 2), full - CUT_MAX / 2) : full / 2;
      const centre = A.clone().addScaledVector(dir, t);
      A = centre.clone().addScaledVector(dir, -CUT_MAX / 2);
      B = centre.clone().addScaledVector(dir, CUT_MAX / 2);
    }
    const n = new THREE.Vector3(piece.normal[0], piece.normal[2], -piece.normal[1]);
    const length = A.distanceTo(B);
    if (length < .08) return null;
    // the true conduit segment behind this surface piece
    const seg = this.trueSegment(c, A, B);
    const depth = seg ? Math.min(.09, seg.depth + seg.r + .012) : .06;
    const width = seg ? Math.max(.09, seg.r * 2 + .06) : .09;
    const box = chaseOpening(A, B, n, width, depth);
    this.ctx.apertures.open(box);
    const g = new THREE.Group();
    g.name = 'cutaway:' + conduitId;
    const dir = B.clone().sub(A).normalize();
    const side = dir.clone().cross(n).normalize();
    // chase recess: back face and two sides (rough plaster/concrete)
    const back = new THREE.Mesh(new THREE.PlaneGeometry(length, width), mat('chase'));
    const basis = new THREE.Matrix4().makeBasis(dir, side, n);
    back.quaternion.setFromRotationMatrix(basis);
    back.position.copy(A.clone().add(B).multiplyScalar(.5)).addScaledVector(n, -depth);
    g.add(back);
    for (const sgn of [-1, 1]) {
      const wall = new THREE.Mesh(new THREE.PlaneGeometry(length, depth), mat('chase'));
      const b2 = new THREE.Matrix4().makeBasis(dir, n, side.clone().multiplyScalar(-sgn));
      wall.quaternion.setFromRotationMatrix(b2);
      wall.position.copy(A.clone().add(B).multiplyScalar(.5)).addScaledVector(side, sgn * width / 2).addScaledVector(n, -depth / 2);
      wall.material = mat('chase');
      wall.material.side = THREE.DoubleSide;
      g.add(wall);
    }
    for (const end of [A, B]) {
      const cap = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), mat('chase'));
      const b3 = new THREE.Matrix4().makeBasis(side, n, dir);
      cap.quaternion.setFromRotationMatrix(b3);
      cap.position.copy(end).addScaledVector(n, -depth / 2);
      cap.material.side = THREE.DoubleSide;
      g.add(cap);
    }
    if (seg) {
      // conduit cut open lengthwise (room-facing half removed) with its conductors inside
      const axisA = seg.a, axisB = seg.b;
      const shellGeo = new THREE.CylinderGeometry(seg.r, seg.r, axisA.distanceTo(axisB), 28, 1, true, Math.PI / 2, Math.PI);
      const shell = new THREE.Mesh(shellGeo, mat('conduitCut'));
      const ax = axisB.clone().sub(axisA).normalize();
      const zf = n.clone().sub(ax.clone().multiplyScalar(n.dot(ax))).normalize();
      const xf = ax.clone().cross(zf).normalize();
      shell.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xf, ax, zf));
      shell.position.copy(axisA.clone().add(axisB).multiplyScalar(.5));
      shell.userData = { kind: 'conduit', ref: conduitId };
      g.add(shell);
      this.ctx.pickables.push(shell);
      const ks = m.conductorsByConduit.get(conduitId) || [];
      ks.forEach((k, i) => {
        const a = (i / Math.max(1, ks.length)) * Math.PI + Math.PI / 2 + .25;
        const rr = seg.r * .52;
        const off = xf.clone().multiplyScalar(Math.sin(a) * rr).addScaledVector(zf, Math.cos(a) * rr * .8 - seg.r * .1);
        const p0 = axisA.clone().add(off), p1 = axisB.clone().add(off);
        const tube = new THREE.Mesh(sweepTube([p0, p1], wireRadius(k.size), 8), k.colour === 'PE' ? stripedInsulation(m.colour('PE').hex, m.colour('PE').stripe) : insulation(m.colour(k.colour).hex));
        tube.userData = { kind: 'conductor', ref: k.id };
        g.add(tube);
        this.ctx.pickables.push(tube);
      });
    }
    this.ctx.root.add(g);
    // the overlay strip stands aside where the surface itself is opened; any rest of
    // that piece keeps its strip on either side of the opening
    const pi = c.reveal.indexOf(piece);
    for (const o of this.group.children) if (o.userData.ref === conduitId && o.userData.piece === pi) o.visible = false;
    if (clipped) {
      const toModel = (v) => [v.x, -v.z, v.y];
      const hot = traceMaterial(true);
      for (const [a, b] of [[piece.a, toModel(A)], [toModel(B), piece.b]]) {
        const geo = strip(a, b, piece.normal, .036);
        if (!geo) continue;
        const rest = new THREE.Mesh(geo, hot);
        rest.renderOrder = 20;
        rest.userData = { kind: 'trace', ref: conduitId, overlay: true };
        g.add(rest);
        this.ctx.pickables.push(rest);
      }
    }
    this.cut = { group: g, conduitId, piece, A: A.clone(), B: B.clone(), anchor: A.clone().add(B).multiplyScalar(.5) };
    this.ctx.viewer.dirty = true;
    return this.cut;
  }

  trueSegment(c, A, B) {
    // nearest straight segment of the conduit centre-line to the opened part of the surface
    const mid = A.clone().add(B).multiplyScalar(.5);
    let best = null;
    for (let i = 0; i < c.points.length - 1; i++) {
      const a = s2t(c.points[i]), b = s2t(c.points[i + 1]);
      const line = new THREE.Line3(a, b);
      const q = line.closestPointToPoint(mid, true, new THREE.Vector3());
      const d = q.distanceTo(mid);
      if (!best || d < best.d) best = { d, a, b };
    }
    if (!best) return null;
    // clip the segment to the piece's extent
    const dir = best.b.clone().sub(best.a).normalize();
    const project = (p) => best.a.clone().addScaledVector(dir, p.clone().sub(best.a).dot(dir));
    return { a: project(A), b: project(B), r: (c.diameter || 20) / 2000, depth: best.d };
  }

  closeCut() {
    for (const o of this.group.children) o.visible = true;
    if (!this.cut) { this.ctx.apertures.close(); return; }
    this.ctx.root.remove(this.cut.group);
    this.cut.group.traverse((o) => o.geometry?.dispose());
    const keep = new Set();
    this.cut.group.traverse((o) => keep.add(o));
    this.ctx.pickables.splice(0, this.ctx.pickables.length, ...this.ctx.pickables.filter((p) => !keep.has(p)));
    this.cut = null;
    this.ctx.apertures.close();
    this.ctx.viewer.dirty = true;
  }
}
