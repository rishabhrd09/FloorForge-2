// Procedural plant geometry. Each builder returns parts {wood, leaves, flowers, mass} as BufferGeometries
// built in a local frame (Y up, base at origin). Attributes: position, normal, uv, aSway (0 rigid .. 1 tip).
import * as THREE from 'three';
import { mulberry32 } from './util.js';

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const UP = V(0, 1, 0);

export class GeoBuilder {
  constructor() { this.pos = []; this.nor = []; this.uv = []; this.sway = []; this.col = []; this.idx = []; this.hasColor = false; }
  get count() { return this.pos.length / 3; }
  vert(p, n, u, v, s, color) {
    this.pos.push(p.x, p.y, p.z); this.nor.push(n.x, n.y, n.z); this.uv.push(u, v); this.sway.push(s);
    if (color) { this.hasColor = true; this.col.push(color.r, color.g, color.b); } else this.col.push(1, 1, 1);
    return this.count - 1;
  }
  tri(a, b, c) { this.idx.push(a, b, c); }
  build() {
    if (!this.idx.length) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.nor, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('aSway', new THREE.Float32BufferAttribute(this.sway, 1));
    if (this.hasColor) g.setAttribute('color', new THREE.Float32BufferAttribute(this.col, 3));
    g.setIndex(this.idx);
    g.computeBoundingSphere();
    return g;
  }
}

// Tapered tube along a polyline (parallel-transport frames). uv: u around (0..circ/uvScale), v along.
export function tube(b, points, radii, sides = 7, sway = [0, .2], uvScale = [.6, 1.2]) {
  const n = points.length;
  let normal = null;
  let lengthSoFar = 0;
  const rings = [];
  for (let i = 0; i < n; i++) {
    const p = points[i];
    const t = (i < n - 1 ? points[i + 1].clone().sub(p) : p.clone().sub(points[i - 1])).normalize();
    if (!normal) { normal = Math.abs(t.y) < .9 ? V(0, 1, 0).cross(t).normalize() : V(1, 0, 0).cross(t).normalize(); }
    else { const bin = t.clone().cross(normal); normal = bin.cross(t).normalize(); }
    const bin = t.clone().cross(normal).normalize();
    if (i > 0) lengthSoFar += p.distanceTo(points[i - 1]);
    const r = radii[i];
    const ring = [];
    const circ = 2 * Math.PI * Math.max(r, .01);
    const sw = sway[0] + (sway[1] - sway[0]) * (i / (n - 1));
    for (let k = 0; k <= sides; k++) {
      const a = (k / sides) * Math.PI * 2;
      const dir = normal.clone().multiplyScalar(Math.cos(a)).addScaledVector(bin, Math.sin(a));
      ring.push(b.vert(p.clone().addScaledVector(dir, r), dir, (k / sides) * circ / uvScale[0], lengthSoFar / uvScale[1], sw));
    }
    rings.push(ring);
  }
  for (let i = 0; i < n - 1; i++) for (let k = 0; k < sides; k++) {
    const a = rings[i][k], c = rings[i][k + 1], d = rings[i + 1][k], e = rings[i + 1][k + 1];
    // Counter-clockwise seen from outside, matching the outward ring normals (front faces face out).
    b.tri(a, c, d); b.tri(c, e, d);
  }
}

// Curved path helper: start, direction, length, gravity bend, upward curl.
function curve(start, dir, len, segs, bend = 0, curl = 0, jitter = 0, rnd = Math.random) {
  const pts = [start.clone()];
  const d = dir.clone().normalize();
  const step = len / segs;
  let p = start.clone();
  for (let i = 1; i <= segs; i++) {
    d.y -= bend * step * 1.2;
    d.y += curl * step;
    if (jitter) { d.x += (rnd() - .5) * jitter; d.z += (rnd() - .5) * jitter; }
    d.normalize();
    p = p.clone().addScaledVector(d, step);
    pts.push(p);
  }
  return pts;
}

// Alpha card (quad) centred at c; normal can be bent toward `radial` for volumetric canopy shading.
export function card(b, c, right, up, w, h, cell, cells = 2, sway = .6, radial = null, bendNormals = .75) {
  const n = right.clone().cross(up).normalize();
  const nn = radial ? n.clone().multiplyScalar(1 - bendNormals).addScaledVector(radial, bendNormals).normalize() : n;
  const cu = (cell % cells) / cells, cv = Math.floor(cell / cells) / cells, s = 1 / cells;
  const hw = w / 2, hh = h / 2;
  const i0 = b.vert(c.clone().addScaledVector(right, -hw).addScaledVector(up, -hh), nn, cu, cv, sway * .6);
  const i1 = b.vert(c.clone().addScaledVector(right, hw).addScaledVector(up, -hh), nn, cu + s, cv, sway * .6);
  const i2 = b.vert(c.clone().addScaledVector(right, hw).addScaledVector(up, hh), nn, cu + s, cv + s, sway);
  const i3 = b.vert(c.clone().addScaledVector(right, -hw).addScaledVector(up, hh), nn, cu, cv + s, sway);
  b.tri(i0, i1, i2); b.tri(i0, i2, i3);
}

// A leaf blade: a folded, drooping strip with the atlas cell mapped base→tip (v) and edge→edge (u).
export function blade(b, base, dir, side, len, width, cell, { segs = 4, bend = .25, fold = .18, sway = [.4, 1], cells = 2, twist = 0, widthProfile = null } = {}) {
  const cu = (cell % cells) / cells, cv = Math.floor(cell / cells) / cells, s = 1 / cells;
  const pts = curve(base, dir, len, segs, bend, 0);
  const rows = [];
  const sideN = side.clone().normalize();
  for (let i = 0; i <= segs; i++) {
    const t = i / segs;
    const p = pts[i];
    const tangent = (i < segs ? pts[i + 1].clone().sub(p) : p.clone().sub(pts[i - 1])).normalize();
    let sd = sideN.clone();
    if (twist) sd.applyAxisAngle(tangent, twist * t);
    const up = sd.clone().cross(tangent).normalize();
    if (up.y < 0) up.negate();
    const wp = widthProfile ? widthProfile(t) : Math.sin(Math.min(1, t * 1.15) * Math.PI) * .9 + .1 * (1 - t);
    const hw = width * .5 * Math.max(.05, wp);
    const foldUp = up.clone().multiplyScalar(fold * hw);
    const l = p.clone().addScaledVector(sd, -hw).add(foldUp);
    const r = p.clone().addScaledVector(sd, hw).add(foldUp);
    const sw = sway[0] + (sway[1] - sway[0]) * t;
    rows.push([
      b.vert(l, up.clone().addScaledVector(sd, -.35).normalize(), cu, cv + s * t, sw),
      b.vert(p, up, cu + s * .5, cv + s * t, sw),
      b.vert(r, up.clone().addScaledVector(sd, .35).normalize(), cu + s, cv + s * t, sw),
    ]);
  }
  for (let i = 0; i < segs; i++) for (let k = 0; k < 2; k++) {
    const a = rows[i][k], c = rows[i][k + 1], d = rows[i + 1][k], e = rows[i + 1][k + 1];
    b.tri(a, c, e); b.tri(a, e, d);
  }
}

// Noise-displaced ellipsoid used as the dense inner mass of clipped shrubs and canopies.
function blob(b, center, radii, rnd, detail = 2, bumps = .08, sway = .15, flatBottom = false) {
  const g = new THREE.IcosahedronGeometry(1, detail);
  const pos = g.attributes.position;
  const seeds = [rnd() * 10, rnd() * 10, rnd() * 10];
  const base = b.count;
  for (let i = 0; i < pos.count; i++) {
    const v = V(pos.getX(i), pos.getY(i), pos.getZ(i)).normalize();
    const n = 1 + bumps * (Math.sin(v.x * 5 + seeds[0]) * Math.sin(v.y * 4 + seeds[1]) * Math.sin(v.z * 5 + seeds[2]) + .35 * Math.sin(v.x * 11 + v.z * 9 + seeds[0]));
    const p = V(v.x * radii.x * n, v.y * radii.y * n, v.z * radii.z * n);
    if (flatBottom && p.y < -radii.y * .55) p.y = -radii.y * .55 + (p.y + radii.y * .55) * .25;
    b.vert(p.clone().add(center), v, v.x * .5 + .5, v.y * .5 + .5, sway);
  }
  const idx = g.index ? g.index.array : [...Array(pos.count).keys()];
  for (let i = 0; i < idx.length; i += 3) b.tri(base + idx[i], base + idx[i + 1], base + idx[i + 2]);
  g.dispose();
}

// Cards scattered over an ellipsoid surface (plus a few inside) to make a leafy, fuzzy silhouette.
function canopyCards(b, center, radii, count, size, rnd, { cells = [0, 1, 2], swayScale = 1, depth = .12, upBias = .15, sizeJitter = .35 } = {}) {
  const golden = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < count; i++) {
    const y = 1 - (i + .5) / count * 2;
    const r = Math.sqrt(1 - y * y);
    const th = golden * i + rnd() * .4;
    const dir = V(Math.cos(th) * r, y + upBias * (rnd() - .3), Math.sin(th) * r).normalize();
    const inset = 1 - depth * rnd();
    const p = V(dir.x * radii.x * inset, dir.y * radii.y * inset, dir.z * radii.z * inset).add(center);
    const radial = V(dir.x / radii.x, dir.y / radii.y, dir.z / radii.z).normalize();
    let right = UP.clone().cross(radial);
    if (right.lengthSq() < 1e-4) right = V(1, 0, 0);
    right.normalize();
    let up = radial.clone().cross(right).normalize();
    const rot = (rnd() - .5) * Math.PI;
    right.applyAxisAngle(radial, rot); up.applyAxisAngle(radial, rot);
    // Tilt cards so they are not perfectly tangent (reads as layered foliage).
    const tilt = (rnd() - .5) * .9;
    up.applyAxisAngle(right, tilt);
    const s = size * (1 - sizeJitter * .5 + sizeJitter * rnd());
    const sway = Math.min(1, (.35 + .65 * (p.y / Math.max(.5, center.y + radii.y))) * swayScale);
    card(b, p, right, up, s, s, cells[Math.floor(rnd() * cells.length)], 2, sway, radial, .8);
  }
}

// ---------------- species ----------------
const SPECIES = {};

SPECIES.frangipani = (rnd) => {
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder();
  const tips = [];
  const branch = (start, dir, len, r0, depth) => {
    const pts = curve(start, dir, len, 5, -.05, .22, .1, rnd);
    const r1 = r0 * .8;
    tube(wood, pts, pts.map((_, i) => r0 + (r1 - r0) * i / (pts.length - 1)), 8, [depth * .12, depth * .12 + .15]);
    const end = pts[pts.length - 1];
    const endDir = end.clone().sub(pts[pts.length - 2]).normalize();
    if (depth >= 3 || len < .3) { tips.push({ p: end, d: endDir }); return; }
    const kids = depth === 0 ? 3 : rnd() < .6 ? 2 : 3;
    const az0 = rnd() * Math.PI * 2;
    for (let k = 0; k < kids; k++) {
      const az = az0 + k * Math.PI * 2 / kids + (rnd() - .5) * .6;
      const spread = .45 + rnd() * .35;
      const nd = endDir.clone().multiplyScalar(Math.cos(spread)).add(V(Math.cos(az), 0, Math.sin(az)).multiplyScalar(Math.sin(spread))).normalize();
      nd.y = Math.max(nd.y, .25);
      branch(end, nd.normalize(), len * (.72 + rnd() * .15), r1 * .92, depth + 1);
    }
  };
  const trunkH = .7 + rnd() * .3;
  const trunk = curve(V(0, 0, 0), V((rnd() - .5) * .15, 1, (rnd() - .5) * .15), trunkH, 4, 0, 0, .05, rnd);
  tube(wood, trunk, trunk.map((_, i) => .17 - .03 * i / 4), 9, [0, .05]);
  branch(trunk[trunk.length - 1], V((rnd() - .5) * .2, 1, (rnd() - .5) * .2), .62 + rnd() * .15, .135, 0);
  for (const { p, d } of tips) {
    // Rosette of broad obovate leaves radiating from each blunt branch tip.
    const n = 16 + Math.floor(rnd() * 8);
    for (let i = 0; i < n; i++) {
      const az = i / n * Math.PI * 2 + rnd() * .3;
      const el = .2 + rnd() * .8;
      const dir = V(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)).add(d.clone().multiplyScalar(.3)).normalize();
      const side = UP.clone().cross(dir).normalize();
      const len = .34 + rnd() * .16;
      blade(leaves, p.clone().addScaledVector(dir, .02), dir, side, len, len * .42, 0, { segs: 3, bend: .55, fold: .28, sway: [.65, 1] });
    }
    if (rnd() < .55) {
      const c = p.clone().addScaledVector(d, .1).add(V(0, .06, 0));
      const s = .24 + rnd() * .1;
      card(flowers, c, V(1, 0, 0), V(0, 0, 1), s, s, 0, 2, .9, UP, .6);
      card(flowers, c.clone().add(V(0, .03, 0)), V(.7, 0, .7).normalize(), V(-.7, .1, .7).normalize(), s * .9, s * .9, 0, 2, .9, UP, .6);
    }
  }
  return { wood, leaves, flowers, leafAtlas: 'leaves', height: 3.4, bark: 'smooth' };
};

SPECIES.shrub_round = (rnd, opts = {}) => {
  const mass = new GeoBuilder(), leaves = new GeoBuilder();
  const R = opts.radius || .5;
  const c = V(0, R * .92, 0);
  blob(mass, c, V(R * .9, R * .85, R * .9), rnd, 3, .05, .1, true);
  canopyCards(leaves, c, V(R, R * .93, R), Math.round(210 * (R / .5) ** 2), R * .5, rnd, { swayScale: .25, depth: .1, upBias: .05 });
  return { mass, leaves, leafAtlas: 'cluster', height: R * 1.85 };
};

SPECIES.shrub_flowering = (rnd, opts = {}) => {
  const mass = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder(), wood = new GeoBuilder();
  const R = .55;
  const c = V(0, R * .8, 0);
  blob(mass, c, V(R * .7, R * .62, R * .7), rnd, 2, .12, .2, true);
  for (let i = 0; i < 6; i++) {
    const a = rnd() * Math.PI * 2;
    const pts = curve(V(Math.cos(a) * .05, 0, Math.sin(a) * .05), V(Math.cos(a) * .4, 1, Math.sin(a) * .4), R * 1.2, 3, 0, 0, .2, rnd);
    tube(wood, pts, pts.map((_, k) => .015 - k * .003), 5, [0, .5]);
  }
  canopyCards(leaves, c, V(R, R * .85, R), 150, R * .55, rnd, { cells: [0, 1, 2], depth: .35, upBias: .1, swayScale: .8 });
  const cell = opts.flower ?? 1;
  const heads = 16 + Math.floor(rnd() * 10);
  for (let i = 0; i < heads; i++) {
    const th = rnd() * Math.PI * 2, y = rnd() * .9 + .05;
    const r = Math.sqrt(1 - y * y);
    const dir = V(Math.cos(th) * r, y, Math.sin(th) * r).normalize();
    const p = V(dir.x * R, dir.y * R * .85, dir.z * R).add(c);
    let right = UP.clone().cross(dir); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
    const up = dir.clone().cross(right).normalize();
    const s = (cell === 1 ? .22 : .16) + rnd() * .08;
    card(flowers, p.addScaledVector(dir, .02), right, up, s, s, cell, 2, .8, dir, .5);
  }
  return { wood, mass, leaves, flowers, leafAtlas: 'clusterLight', height: R * 1.7 };
};

SPECIES.conifer_column = (rnd) => {
  const mass = new GeoBuilder(), leaves = new GeoBuilder();
  const H = 2.3, R = .36;
  const g = new GeoBuilder();
  // Lathe-like column: widest in the lower third, rounded top.
  const rings = 14, sides = 14;
  const profile = (t) => R * Math.pow(Math.sin(Math.PI * Math.min(1, .08 + t * .95)), .55) * (1 - .35 * t) + .01;
  const idx = [];
  for (let i = 0; i <= rings; i++) {
    const t = i / rings;
    const r = profile(t);
    for (let k = 0; k <= sides; k++) {
      const a = k / sides * Math.PI * 2;
      const wob = 1 + .06 * Math.sin(a * 3 + t * 9 + rnd());
      const n = V(Math.cos(a), .25, Math.sin(a)).normalize();
      idx.push(mass.vert(V(Math.cos(a) * r * wob, t * H, Math.sin(a) * r * wob), n, k / sides, t, t * .3));
    }
  }
  for (let i = 0; i < rings; i++) for (let k = 0; k < sides; k++) {
    const a = idx[i * (sides + 1) + k], b1 = idx[i * (sides + 1) + k + 1], c1 = idx[(i + 1) * (sides + 1) + k], d = idx[(i + 1) * (sides + 1) + k + 1];
    mass.tri(a, c1, b1); mass.tri(b1, c1, d);
  }
  const count = 380;
  for (let i = 0; i < count; i++) {
    const t = Math.pow(rnd(), .9);
    const a = rnd() * Math.PI * 2;
    const r = profile(t) * (1.02 + rnd() * .12);
    const radial = V(Math.cos(a), .35 + (t > .85 ? 1.2 : 0), Math.sin(a)).normalize();
    const p = V(Math.cos(a) * r, t * H, Math.sin(a) * r);
    let right = UP.clone().cross(radial); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
    const up = radial.clone().cross(right).normalize();
    const s = .24 + rnd() * .12;
    card(leaves, p, right, up.applyAxisAngle(radial, (rnd() - .5) * .8), s, s * 1.15, 3, 2, .1 + t * .3, radial, .7);
  }
  return { mass, leaves, leafAtlas: 'cluster', height: H };
};

SPECIES.topiary_spiral = (rnd) => {
  const mass = new GeoBuilder(), leaves = new GeoBuilder(), wood = new GeoBuilder();
  const H = 1.9, turns = 3.4;
  tube(wood, [V(0, 0, 0), V(0, H * .5, 0), V(0, H, 0)], [.03, .025, .015], 6, [0, 0]);
  const pts = [], radii = [];
  const N = 70;
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const a = t * turns * Math.PI * 2;
    const R = .36 * (1 - t) + .06;
    pts.push(V(Math.cos(a) * R * .55, .2 + t * (H - .25), Math.sin(a) * R * .55));
    radii.push(.2 * (1 - t) + .06);
  }
  tube(mass, pts, radii, 10, [.05, .2]);
  for (let i = 0; i < 900; i++) {
    const j = Math.floor(rnd() * N);
    const t = j / N;
    const p0 = pts[j];
    const tangent = pts[Math.min(N, j + 1)].clone().sub(pts[Math.max(0, j - 1)]).normalize();
    let nrm = V(rnd() - .5, rnd() - .5, rnd() - .5); nrm.addScaledVector(tangent, -nrm.dot(tangent)).normalize();
    const p = p0.clone().addScaledVector(nrm, radii[j] * (1 + rnd() * .12));
    let right = tangent.clone(); const up = nrm.clone().cross(right).normalize();
    right = up.clone().cross(nrm).normalize();
    const s = (.16 + rnd() * .08) * (1.1 - t * .4);
    card(leaves, p, right, up, s, s, 3, 2, .2, nrm, .75);
  }
  return { wood, mass, leaves, leafAtlas: 'cluster', height: H };
};

SPECIES.strelitzia = (rnd) => {
  const leaves = new GeoBuilder(), wood = new GeoBuilder();
  const n = 8 + Math.floor(rnd() * 5);
  for (let i = 0; i < n; i++) {
    const az = i / n * Math.PI * 2 + rnd() * .5;
    const lean = .12 + rnd() * .35;
    const dir = V(Math.cos(az) * lean, 1, Math.sin(az) * lean).normalize();
    const start = V(Math.cos(az) * .06, 0, Math.sin(az) * .06);
    const plen = .7 + rnd() * .7;
    const pts = curve(start, dir, plen, 4, .05, 0, .04, rnd);
    tube(wood, pts, pts.map((_, k) => .028 - k * .004), 5, [.05, .6]);
    const top = pts[pts.length - 1];
    const d2 = top.clone().sub(pts[pts.length - 2]).normalize();
    const side = UP.clone().cross(d2.clone().setY(0).lengthSq() > 1e-4 ? d2 : V(1, 0, 0)).normalize();
    const len = .9 + rnd() * .45;
    blade(leaves, top, d2.clone().add(V(Math.cos(az) * .25, 0, Math.sin(az) * .25)).normalize(), side, len, .38 + rnd() * .08, 2, { segs: 6, bend: .38, fold: .12, sway: [.6, 1], twist: (rnd() - .5) * .8 });
  }
  return { wood, leaves, leafAtlas: 'leaves', height: 2.2, woodColor: '#6f7d4a' };
};

SPECIES.cordyline = (rnd) => {
  const leaves = new GeoBuilder(), wood = new GeoBuilder();
  const trunkH = .15 + rnd() * .2;
  tube(wood, [V(0, 0, 0), V(0, trunkH, 0)], [.03, .025], 6, [0, .1]);
  const n = 18 + Math.floor(rnd() * 8);
  for (let i = 0; i < n; i++) {
    const az = i * 2.399 + rnd() * .3;
    const el = .5 + rnd() * .9;
    const dir = V(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)).normalize();
    const side = UP.clone().cross(dir).normalize();
    const len = .38 + rnd() * .22;
    blade(leaves, V(0, trunkH, 0), dir, side, len, .13, 1, { segs: 4, bend: .8, fold: .25, sway: [.5, 1] });
  }
  return { wood, leaves, leafAtlas: 'leaves', height: .8 };
};

SPECIES.palm = (rnd) => {
  const leaves = new GeoBuilder(), wood = new GeoBuilder();
  const H = 5.6 + rnd() * 1.5;
  const lean = V((rnd() - .5) * .25, 1, (rnd() - .5) * .25).normalize();
  const trunk = curve(V(0, 0, 0), lean, H, 10, -.01, .02, .02, rnd);
  tube(wood, trunk, trunk.map((_, i) => .17 - .05 * i / 10), 9, [0, .15], [.5, .6]);
  const top = trunk[trunk.length - 1];
  const n = 13 + Math.floor(rnd() * 5);
  for (let i = 0; i < n; i++) {
    const az = i * 2.399 + rnd() * .2;
    const el = .9 - (i / n) * 1.25 + (rnd() - .5) * .2;
    const dir = V(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)).normalize();
    const side = UP.clone().cross(dir).normalize();
    blade(leaves, top, dir, side, 2.3 + rnd() * .8, 1.25, i % 4, { segs: 7, bend: .55, fold: .05, sway: [.35, 1], cells: 2, widthProfile: () => 1 });
  }
  return { wood, leaves, leafAtlas: 'fronds', height: H + 1.2, woodColor: '#8f8474', bark: 'palm' };
};

SPECIES.grass_ornamental = (rnd, opts = {}) => {
  const leaves = new GeoBuilder();
  const n = 90;
  const base = new THREE.Color(opts.color || '#6b8a3a'), tip = base.clone().lerp(new THREE.Color('#d9d49a'), .45);
  for (let i = 0; i < n; i++) {
    const az = rnd() * Math.PI * 2;
    const el = .55 + rnd() * .95;
    const dir = V(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)).normalize();
    const side = UP.clone().cross(dir).normalize();
    const len = .6 + rnd() * .4;
    const start = leaves.count;
    blade(leaves, V(Math.cos(az) * .05, 0, Math.sin(az) * .05), dir, side, len, .022, 0, { segs: 4, bend: 1.1, fold: 0, sway: [.2, 1], widthProfile: (t) => 1 - t * .9 });
    for (let k = start; k < leaves.count; k++) {
      const t = (leaves.pos[k * 3 + 1]) / .8;
      const c = base.clone().lerp(tip, Math.min(1, Math.max(0, t)));
      leaves.col[k * 3] = c.r; leaves.col[k * 3 + 1] = c.g; leaves.col[k * 3 + 2] = c.b;
    }
    leaves.hasColor = true;
  }
  return { leaves, leafAtlas: 'solid', height: .7 };
};

SPECIES.tree_standard = (rnd) => {
  const wood = new GeoBuilder(), mass = new GeoBuilder(), leaves = new GeoBuilder();
  const trunkH = 1.9 + rnd() * .3;
  const trunk = curve(V(0, 0, 0), V(0, 1, 0), trunkH + .5, 5, 0, 0, .03, rnd);
  tube(wood, trunk, trunk.map((_, i) => .075 - .03 * i / 5), 8, [0, .1]);
  for (let i = 0; i < 5; i++) {
    const a = rnd() * Math.PI * 2;
    const pts = curve(V(0, trunkH, 0), V(Math.cos(a), 1.1, Math.sin(a)), .6, 3, 0, 0, .1, rnd);
    tube(wood, pts, [.035, .028, .02, .012], 5, [.1, .3]);
  }
  const c = V(0, trunkH + .55, 0);
  blob(mass, c, V(.82, .68, .82), rnd, 2, .1, .3);
  canopyCards(leaves, c, V(.95, .8, .95), 420, .42, rnd, { cells: [0, 1, 2], depth: .2, upBias: .1, swayScale: .9 });
  return { wood, mass, leaves, leafAtlas: 'clusterLight', height: trunkH + 1.4 };
};

SPECIES.tree_shade = (rnd) => {
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), mass = new GeoBuilder();
  const tips = [];
  const branch = (start, dir, len, r0, depth) => {
    const pts = curve(start, dir, len, 4, .02, .05, .25, rnd);
    tube(wood, pts, pts.map((_, i) => r0 * (1 - .35 * i / 4)), depth < 2 ? 7 : 5, [depth * .15, depth * .15 + .2]);
    const end = pts[pts.length - 1];
    const d = end.clone().sub(pts[pts.length - 2]).normalize();
    if (depth >= 3) { tips.push(end); return; }
    const kids = 2 + (rnd() < .7 ? 1 : 0);
    for (let k = 0; k < kids; k++) {
      const az = rnd() * Math.PI * 2;
      const nd = d.clone().multiplyScalar(.7).add(V(Math.cos(az), .3, Math.sin(az)).multiplyScalar(.6)).normalize();
      branch(end, nd, len * (.68 + rnd() * .12), r0 * .62, depth + 1);
    }
  };
  const trunkH = 2 + rnd() * .6;
  const trunk = curve(V(0, 0, 0), V(0, 1, 0), trunkH, 4, 0, 0, .06, rnd);
  tube(wood, trunk, trunk.map((_, i) => .2 - .06 * i / 4), 9, [0, .05]);
  branch(trunk[trunk.length - 1], V(.1, 1, .05), 1.6, .15, 0);
  for (const t of tips) {
    blob(mass, t, V(.7, .55, .7), rnd, 1, .15, .6);
    canopyCards(leaves, t, V(.95, .75, .95), 38, .62, rnd, { cells: [0, 1, 2], depth: .4, swayScale: 1 });
  }
  return { wood, leaves, mass, leafAtlas: 'clusterLight', height: 7 };
};

SPECIES.monstera = (rnd) => {
  const leaves = new GeoBuilder(), wood = new GeoBuilder();
  const n = 7 + Math.floor(rnd() * 4);
  for (let i = 0; i < n; i++) {
    const az = i * 2.399 + rnd() * .4;
    const lean = .3 + rnd() * .5;
    const dir = V(Math.cos(az) * lean, 1, Math.sin(az) * lean).normalize();
    const pts = curve(V(0, 0, 0), dir, .45 + rnd() * .35, 3, .15, 0, .05, rnd);
    tube(wood, pts, pts.map(() => .011), 5, [.1, .7]);
    const top = pts[pts.length - 1];
    const out = V(Math.cos(az), -.1 - rnd() * .3, Math.sin(az)).normalize();
    const side = UP.clone().cross(out).normalize();
    blade(leaves, top, out, side, .42 + rnd() * .15, .5, 3, { segs: 4, bend: .35, fold: .1, sway: [.5, 1], widthProfile: (t) => Math.sin(Math.min(1, .15 + t) * Math.PI) * .95 + .05 });
  }
  return { wood, leaves, leafAtlas: 'leaves', height: 1.0, woodColor: '#4f6b35' };
};

SPECIES.fiddle_leaf = (rnd) => {
  const leaves = new GeoBuilder(), wood = new GeoBuilder();
  const H = 1.5 + rnd() * .3;
  const stem = curve(V(0, 0, 0), V((rnd() - .5) * .1, 1, (rnd() - .5) * .1), H, 6, 0, 0, .05, rnd);
  tube(wood, stem, stem.map((_, i) => .025 - .012 * i / 6), 6, [0, .3]);
  for (let i = 0; i < 26; i++) {
    const t = .35 + .65 * (i / 26);
    const p = stem[Math.min(6, Math.floor(t * 6))].clone().lerp(stem[Math.min(6, Math.ceil(t * 6))], (t * 6) % 1);
    const az = i * 2.399;
    const dir = V(Math.cos(az), .25 + rnd() * .5, Math.sin(az)).normalize();
    const side = UP.clone().cross(dir).normalize();
    blade(leaves, p, dir, side, .3 + rnd() * .1, .28, 0, { segs: 3, bend: .5, fold: .2, sway: [.4, .9], widthProfile: (tt) => Math.sin(Math.min(1, .1 + tt * .95) * Math.PI) * (.7 + .3 * tt) + .1 });
  }
  return { wood, leaves, leafAtlas: 'leaves', height: H + .2 };
};

SPECIES.hedge = (rnd, opts = {}) => {
  const [L, Wd, Hh] = opts.size || [2, .5, 1];
  const mass = new GeoBuilder(), leaves = new GeoBuilder();
  const box = new THREE.BoxGeometry(L - .06, Hh - .06, Wd - .06, Math.max(2, Math.round(L * 3)), 3, 2);
  const pos = box.attributes.position, nor = box.attributes.normal;
  const base = mass.count;
  for (let i = 0; i < pos.count; i++) {
    const p = V(pos.getX(i), pos.getY(i) + Hh / 2, pos.getZ(i));
    p.addScaledVector(V(nor.getX(i), nor.getY(i), nor.getZ(i)), (Math.sin(p.x * 7 + p.y * 5) * .5 + .5) * .03);
    mass.vert(p, V(nor.getX(i), nor.getY(i), nor.getZ(i)), 0, 0, .05);
  }
  const idx = box.index.array;
  for (let i = 0; i < idx.length; i += 3) mass.tri(base + idx[i], base + idx[i + 1], base + idx[i + 2]);
  box.dispose();
  // Cards on each exposed face, density per square metre.
  const faces = [
    { n: V(0, 1, 0), c: V(0, Hh, 0), u: V(1, 0, 0), v: V(0, 0, 1), a: L, b: Wd },
    { n: V(0, 0, 1), c: V(0, Hh / 2, Wd / 2), u: V(1, 0, 0), v: V(0, 1, 0), a: L, b: Hh },
    { n: V(0, 0, -1), c: V(0, Hh / 2, -Wd / 2), u: V(1, 0, 0), v: V(0, 1, 0), a: L, b: Hh },
    { n: V(1, 0, 0), c: V(L / 2, Hh / 2, 0), u: V(0, 0, 1), v: V(0, 1, 0), a: Wd, b: Hh },
    { n: V(-1, 0, 0), c: V(-L / 2, Hh / 2, 0), u: V(0, 0, 1), v: V(0, 1, 0), a: Wd, b: Hh },
  ];
  for (const f of faces) {
    const count = Math.round(f.a * f.b * 70);
    for (let i = 0; i < count; i++) {
      const p = f.c.clone().addScaledVector(f.u, (rnd() - .5) * f.a).addScaledVector(f.v, (rnd() - .5) * f.b).addScaledVector(f.n, .01 + rnd() * .05);
      let right = f.u.clone().applyAxisAngle(f.n, rnd() * Math.PI);
      const up = f.n.clone().cross(right).normalize().applyAxisAngle(right, (rnd() - .5) * .8);
      right = up.clone().cross(f.n).normalize();
      const s = .2 + rnd() * .1;
      card(leaves, p, right, up, s, s, Math.floor(rnd() * 3), 2, .15 + .2 * (p.y / Hh), f.n, .7);
    }
  }
  return { mass, leaves, leafAtlas: 'cluster', height: Hh };
};

export const SPECIES_NAMES = Object.keys(SPECIES);

export function buildSpecies(name, seed, opts = {}) {
  const fn = SPECIES[name] || SPECIES.shrub_round;
  const rnd = mulberry32(seed >>> 0);
  const out = fn(rnd, opts);
  const parts = {};
  for (const key of ['wood', 'leaves', 'flowers', 'mass']) if (out[key]) parts[key] = out[key].build();
  return { ...out, parts };
}
