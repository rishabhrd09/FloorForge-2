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
function canopyCards(b, center, radii, count, size, rnd, { cells = [0, 1, 2], swayScale = 1, depth = .12, upBias = .15, sizeJitter = .35, grid = 2 } = {}) {
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
    card(b, p, right, up, s, s, cells[Math.floor(rnd() * cells.length)], grid, sway, radial, .8);
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
  if (!opts.flowers) return { mass, leaves, leafAtlas: 'cluster', height: Hh };
  // A flowering hedge (heritage gardens): small blooms scattered over the clipped top and upper sides.
  const flowers = new GeoBuilder();
  const cell = { white: GF.jasmine, red: GF.geranium, yellow: GF.yellow, pink: GF.periwinkle }[opts.flowers] ?? GF.jasmine;
  for (const f of faces) {
    const count = Math.round(f.a * f.b * (f.n.y > .5 ? 26 : 9));
    for (let i = 0; i < count; i++) {
      const p = f.c.clone().addScaledVector(f.u, (rnd() - .5) * f.a).addScaledVector(f.v, (rnd() - .5) * f.b).addScaledVector(f.n, .05 + rnd() * .03);
      if (f.n.y < .5 && p.y < Hh * .45) continue;
      let right = f.u.clone().applyAxisAngle(f.n, rnd() * Math.PI);
      const up = f.n.clone().cross(right).normalize();
      right = up.clone().cross(f.n).normalize();
      const s = .08 + rnd() * .05;
      card(flowers, p, right, up, s, s, cell, 4, .3, f.n, .6);
    }
  }
  return { mass, leaves, flowers, leafAtlas: 'cluster', flowerAtlas: 'gardenFlowers', height: Hh };
};

// ---------------- Indian garden species (the Heritage Bungalow sample) ----------------
// Cells of the 4x4 garden atlases painted in foliage-textures.js (gardenLeafAtlas / gardenFlowerAtlas).
export const GL = { neem: 0, mango: 1, ashoka: 2, araucaria: 3, areca: 4, croton: 5, croton2: 6, poinsettia: 7, tulsi: 8, rose: 9, leafy: 10, tomato: 11, strap: 12, heart: 13, bougainvillea: 14, feathery: 15 };
export const GF = { marigold: 0, yellow: 1, red: 2, pink: 3, white: 4, periwinkle: 5, geranium: 6, orange: 7, amaryllis: 8, bractWhite: 9, magenta: 10, purple: 11, jasmine: 12, mango: 13, tulsi: 14, daisy: 15 };
const CLUMP_FLOWER = { marigold: GF.marigold, yellow: GF.yellow, red: GF.geranium, pink: GF.periwinkle, purple: GF.purple, white: GF.daisy, orange: GF.orange };

// A spreading broadleaf tree: forked limbs, a leafy dome at each branch tip.
function broadleaf(rnd, { trunkH, trunkR, limb, spread, depth = 3, tip, cards, cardSize, cell, massScale = .7, height, fruit = 0 }) {
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), mass = new GeoBuilder(), flowers = new GeoBuilder();
  const tips = [];
  const branch = (start, dir, len, r0, d) => {
    const pts = curve(start, dir, len, 4, .015, .03, .22, rnd);
    tube(wood, pts, pts.map((_, i) => r0 * (1 - .35 * i / 4)), d < 2 ? 8 : 5, [d * .15, d * .15 + .2]);
    const end = pts[pts.length - 1];
    const dd = end.clone().sub(pts[pts.length - 2]).normalize();
    if (d >= depth) { tips.push(end); return; }
    const kids = d === 0 ? 4 : 2 + (rnd() < .6 ? 1 : 0);
    const az0 = rnd() * Math.PI * 2;
    for (let k = 0; k < kids; k++) {
      const az = az0 + k * Math.PI * 2 / kids + (rnd() - .5) * .7;
      const nd = dd.clone().multiplyScalar(.55).add(V(Math.cos(az), .55, Math.sin(az)).multiplyScalar(spread)).normalize();
      branch(end, nd, len * (.7 + rnd() * .12), r0 * .62, d + 1);
    }
  };
  const trunk = curve(V(0, 0, 0), V((rnd() - .5) * .1, 1, (rnd() - .5) * .1), trunkH, 5, 0, 0, .05, rnd);
  tube(wood, trunk, trunk.map((_, i) => trunkR * (1 - .25 * i / 5)), 10, [0, .05]);
  branch(trunk[trunk.length - 1], V((rnd() - .5) * .2, 1, (rnd() - .5) * .2), limb, trunkR * .8, 0);
  for (const t of tips) {
    blob(mass, t, tip.clone().multiplyScalar(massScale), rnd, 1, .18, .55);
    canopyCards(leaves, t, tip, cards, cardSize, rnd, { cells: [cell], grid: 4, depth: .45, swayScale: 1, upBias: .2 });
    for (let i = 0; i < fruit; i++) {
      const a = rnd() * Math.PI * 2;
      const p = t.clone().add(V(Math.cos(a) * tip.x * .8, -tip.y * (.35 + rnd() * .3), Math.sin(a) * tip.z * .8));
      card(flowers, p, V(Math.cos(a + 1.6), 0, Math.sin(a + 1.6)), V(0, 1, 0), .22, .3, GF.mango, 4, .5);
    }
  }
  return { wood, leaves, mass, ...(fruit ? { flowers, flowerAtlas: 'gardenFlowers' } : {}), leafAtlas: 'gardenLeaves', height };
}

SPECIES.neem = (rnd) => broadleaf(rnd, { trunkH: 2.4, trunkR: .24, limb: 2.2, spread: .75, tip: V(1.3, 1.1, 1.3), cards: 70, cardSize: .7, cell: GL.neem, massScale: .6, height: 9.5 });

SPECIES.mango = (rnd) => broadleaf(rnd, { trunkH: 1.5, trunkR: .25, limb: 1.9, spread: .85, tip: V(1.25, 1.15, 1.25), cards: 92, cardSize: .66, cell: GL.mango, massScale: .55, height: 7.5 });

SPECIES.ashoka = (rnd) => {
  // Polyalthia longifolia 'pendula': a slender spire densely hung with long wavy leaves.
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), mass = new GeoBuilder();
  const H = 9 + rnd() * .6;
  tube(wood, [V(0, 0, 0), V(0, H * .5, 0), V(0, H * .97, 0)], [.16, .1, .03], 8, [0, .2]);
  const R = (t) => t < .13 ? .05 : .1 + .68 * Math.pow(Math.sin(Math.PI * Math.min(1, .1 + t * .93)), .75) * (1 - .55 * t);
  // Inner mass: a narrow lathe keeps the spire dense and dark.
  const rings = 18, sides = 14, idx = [];
  for (let i = 0; i <= rings; i++) {
    const t = .08 + .9 * i / rings, r = R(t) * .7;
    for (let k = 0; k <= sides; k++) {
      const a = k / sides * Math.PI * 2;
      const wob = 1 + .08 * Math.sin(a * 3 + t * 11 + rnd());
      idx.push(mass.vert(V(Math.cos(a) * r * wob, t * H, Math.sin(a) * r * wob), V(Math.cos(a), .15, Math.sin(a)).normalize(), k / sides, t, t * .3));
    }
  }
  for (let i = 0; i < rings; i++) for (let k = 0; k < sides; k++) {
    const a = idx[i * (sides + 1) + k], b1 = idx[i * (sides + 1) + k + 1], c1 = idx[(i + 1) * (sides + 1) + k], d = idx[(i + 1) * (sides + 1) + k + 1];
    mass.tri(a, c1, b1); mass.tri(b1, c1, d);
  }
  // A few drooping branchlets, then curtains of hanging leaf cards over the whole spire (leaf bases up).
  for (let i = 0; i < 18; i++) {
    const t = .12 + .8 * i / 18, a = rnd() * Math.PI * 2;
    const pts = curve(V(0, t * H, 0), V(Math.cos(a), .2, Math.sin(a)), R(t) * .85, 2, .4, 0, .1, rnd);
    tube(wood, pts, [.016, .011, .006], 4, [.2, .6]);
  }
  const count = 620;
  for (let i = 0; i < count; i++) {
    const t = .15 + .84 * Math.pow(rnd(), .95);
    const a = rnd() * Math.PI * 2;
    const r = R(t) * (.92 + rnd() * .2);
    const out = V(Math.cos(a), 0, Math.sin(a));
    const p = V(Math.cos(a) * r, t * H, Math.sin(a) * r);
    const right = V(-out.z, 0, out.x).applyAxisAngle(out, (rnd() - .5) * .3);
    const down = V(0, -1, 0).addScaledVector(out, .18).normalize();
    card(leaves, p, right, down, .36 + rnd() * .12, .58 + rnd() * .2, GL.ashoka, 4, .2 + .5 * t, out.clone().setY(.2).normalize(), .6);
  }
  for (let k = 0; k < 5; k++) card(leaves, V(0, H * .96, 0), V(Math.cos(k * 1.3), 0, Math.sin(k * 1.3)), V(0, -1, 0), .3, .8, GL.ashoka, 4, .8, V(Math.cos(k * 1.3), .6, Math.sin(k * 1.3)).normalize(), .5);
  return { wood, leaves, mass, leafAtlas: 'gardenLeaves', height: H };
};

SPECIES.araucaria = (rnd) => {
  // Cook / Norfolk pine: open tiers of level branches whorled round a straight trunk.
  const wood = new GeoBuilder(), leaves = new GeoBuilder();
  const H = 8 + rnd() * .5;
  tube(wood, [V(0, 0, 0), V(0, H * .5, 0), V(0, H, 0)], [.15, .09, .02], 8, [0, .15]);
  const y0 = 1.0, step = .36;
  let az = rnd() * Math.PI * 2;
  for (let y = y0; y < H - .25; y += step * (.9 + rnd() * .2)) {
    const t = (y - y0) / (H - y0);
    const L = 1.75 * Math.pow(1 - t, .85) + .18;
    for (let k = 0; k < 5; k++) {
      const a = az + k * Math.PI * 2 / 5 + (rnd() - .5) * .25;
      const out = V(Math.cos(a), 0, Math.sin(a));
      const pts = curve(V(0, y, 0), out.clone().setY(-.05), L, 3, -.05, .12, .05, rnd);
      tube(wood, pts, pts.map((_, i) => .03 * (1 - .7 * i / 3)), 4, [.15, .5]);
      const n = Math.max(3, Math.round(L / .13));
      for (let j = 0; j < n; j++) {
        const f = (j + .5) / n;
        const p = pts[0].clone().lerp(pts[pts.length - 1], f);
        const right = out.clone();
        const up = V(-out.z, 0, out.x);
        const w = (.55 * (1 - .45 * f) + .12) * (1 - .35 * t);
        card(leaves, p.clone().add(V(0, .03, 0)), right, up.clone().applyAxisAngle(right, .35), .42, w, GL.araucaria, 4, .2 + .4 * f, V(0, 1, 0), .6);
        card(leaves, p.clone().add(V(0, -.02, 0)), right, up.clone().applyAxisAngle(right, -.35), .42, w * .9, GL.araucaria, 4, .2 + .4 * f, V(0, 1, 0), .6);
      }
    }
    az += 2.399;
  }
  for (let k = 0; k < 3; k++) card(leaves, V(0, H - .2, 0), V(Math.cos(k * 2.1), 0, Math.sin(k * 2.1)), V(0, 1, 0), .25, .6, GL.araucaria, 4, .6);
  return { wood, leaves, leafAtlas: 'gardenLeaves', height: H };
};

SPECIES.areca = (rnd) => {
  // A clumping butterfly palm: slender ringed canes and arching feathery fronds.
  const wood = new GeoBuilder(), leaves = new GeoBuilder();
  const n = 6 + Math.floor(rnd() * 3);
  for (let i = 0; i < n; i++) {
    const a = i / n * Math.PI * 2 + rnd() * .4;
    const lean = .06 + rnd() * .2;
    const h = 1.1 + rnd() * .9;
    const pts = curve(V(Math.cos(a) * .06, 0, Math.sin(a) * .06), V(Math.cos(a) * lean, 1, Math.sin(a) * lean), h, 4, 0, 0, .03, rnd);
    tube(wood, pts, pts.map((_, k) => .028 - .004 * k), 6, [0, .35]);
    const top = pts[pts.length - 1];
    const fronds = 3 + Math.floor(rnd() * 3);
    for (let j = 0; j < fronds; j++) {
      const fa = a + (j - fronds / 2) * .9 + (rnd() - .5) * .4;
      const el = .7 + rnd() * .5;
      const dir = V(Math.cos(fa) * Math.cos(el), Math.sin(el), Math.sin(fa) * Math.cos(el)).normalize();
      const side = UP.clone().cross(dir).normalize();
      blade(leaves, top, dir, side, .9 + rnd() * .5, .6, (i + j) % 4, { segs: 6, bend: .75, fold: .05, sway: [.4, 1], cells: 2, widthProfile: (t) => Math.sin(Math.min(1, .15 + t) * Math.PI) * .8 + .2 });
    }
  }
  return { wood, leaves, leafAtlas: 'fronds', height: 2.5, woodColor: '#9a9a4a' };
};

SPECIES.rose_bush = (rnd, opts = {}) => {
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder();
  const cell = GF[opts.color] ?? GF.red;
  const canes = 7 + Math.floor(rnd() * 4);
  for (let i = 0; i < canes; i++) {
    const a = rnd() * Math.PI * 2, lean = .15 + rnd() * .35;
    const pts = curve(V(Math.cos(a) * .04, 0, Math.sin(a) * .04), V(Math.cos(a) * lean, 1, Math.sin(a) * lean), .55 + rnd() * .4, 4, .05, 0, .2, rnd);
    tube(wood, pts, pts.map((_, k) => .01 - .0015 * k), 4, [0, .6]);
    for (let j = 1; j < pts.length; j++) {
      for (let q = 0; q < 3; q++) {
        const p = pts[j].clone().add(V((rnd() - .5) * .12, (rnd() - .5) * .08, (rnd() - .5) * .12));
        const r = V(rnd() - .5, rnd() * .6, rnd() - .5).normalize();
        let right = UP.clone().cross(r); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
        card(leaves, p, right, r.clone().cross(right).normalize(), .16, .16, GL.rose, 4, .4 + .5 * j / pts.length, r, .6);
      }
    }
    const tip = pts[pts.length - 1];
    for (let q = 0; q < 1 + Math.floor(rnd() * 2); q++) {
      const p = tip.clone().add(V((rnd() - .5) * .08, .03 + rnd() * .04, (rnd() - .5) * .08));
      const face = V(rnd() - .5, .8, rnd() - .5).normalize();
      let right = UP.clone().cross(face); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
      card(flowers, p, right, face.clone().cross(right).normalize(), .11 + rnd() * .03, .11 + rnd() * .03, cell, 4, .8, face, .5);
    }
  }
  return { wood, leaves, flowers, leafAtlas: 'gardenLeaves', flowerAtlas: 'gardenFlowers', height: .9, woodColor: '#4f6a32' };
};

SPECIES.flower_clump = (rnd, opts = {}) => {
  // Marigolds, geraniums, periwinkles and gerberas: a low mound of foliage studded with blooms.
  const mass = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder();
  const R = .25;
  const c = V(0, R * .75, 0);
  blob(mass, c, V(R * .8, R * .65, R * .8), rnd, 2, .1, .2, true);
  const leafCell = opts.color === 'marigold' || opts.color === 'yellow' ? GL.feathery : GL.tulsi;
  canopyCards(leaves, c, V(R, R * .8, R), 64, .17, rnd, { cells: [leafCell, GL.rose], grid: 4, depth: .3, swayScale: .4, upBias: .25 });
  const cell = CLUMP_FLOWER[opts.color] ?? GF.marigold;
  const heads = 20 + Math.floor(rnd() * 8);
  for (let i = 0; i < heads; i++) {
    const th = rnd() * Math.PI * 2, y = .25 + rnd() * .75;
    const r = Math.sqrt(1 - y * y);
    const dir = V(Math.cos(th) * r, y, Math.sin(th) * r).normalize();
    const p = V(dir.x * R * 1.02, dir.y * R * .85, dir.z * R * 1.02).add(c);
    let right = UP.clone().cross(dir); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
    const s = .075 + rnd() * .035;
    card(flowers, p.addScaledVector(dir, .015), right, dir.clone().cross(right).normalize(), s, s, cell, 4, .5, dir, .5);
  }
  return { mass, leaves, flowers, leafAtlas: 'gardenLeaves', flowerAtlas: 'gardenFlowers', height: R * 1.75 };
};

SPECIES.amaryllis = (rnd) => {
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder();
  const n = 9 + Math.floor(rnd() * 4);
  for (let i = 0; i < n; i++) {
    const az = i * 2.399 + rnd() * .3, el = .7 + rnd() * .6;
    const dir = V(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)).normalize();
    blade(leaves, V(0, .02, 0), dir, UP.clone().cross(dir).normalize(), .4 + rnd() * .15, .06, GL.strap, { segs: 4, bend: .9, fold: .2, sway: [.4, 1], cells: 4 });
  }
  const stalks = 2 + Math.floor(rnd() * 2);
  for (let i = 0; i < stalks; i++) {
    const a = rnd() * Math.PI * 2;
    const top = V(Math.cos(a) * .08, .55 + rnd() * .15, Math.sin(a) * .08);
    tube(wood, [V(0, 0, 0), top.clone().multiplyScalar(.5), top], [.012, .01, .008], 5, [0, .5]);
    for (let k = 0; k < 4; k++) {
      const fa = a + k * Math.PI / 2;
      const face = V(Math.cos(fa), .35, Math.sin(fa)).normalize();
      const right = V(-Math.sin(fa), 0, Math.cos(fa));
      card(flowers, top.clone().addScaledVector(face, .07), right, face.clone().cross(right).normalize(), .17, .17, GF.amaryllis, 4, .7, face, .5);
    }
  }
  return { wood, leaves, flowers, leafAtlas: 'gardenLeaves', flowerAtlas: 'gardenFlowers', height: .72, woodColor: '#5c7a38' };
};

SPECIES.croton = (rnd, opts = {}) => {
  const wood = new GeoBuilder(), leaves = new GeoBuilder();
  const poinsettia = opts.leaf === 'poinsettia';
  const stems = 3 + Math.floor(rnd() * 3);
  for (let i = 0; i < stems; i++) {
    const a = rnd() * Math.PI * 2, lean = .1 + rnd() * .25;
    const pts = curve(V(0, 0, 0), V(Math.cos(a) * lean, 1, Math.sin(a) * lean), .45 + rnd() * .25, 3, 0, 0, .1, rnd);
    tube(wood, pts, [.016, .013, .01, .008], 5, [0, .4]);
    const top = pts[pts.length - 1];
    const count = 12 + Math.floor(rnd() * 6);
    for (let k = 0; k < count; k++) {
      const t = k / count;
      const base = pts[Math.min(pts.length - 1, Math.floor(1 + t * (pts.length - 1)))].clone().lerp(top, t * .5);
      const az = k * 2.399 + rnd() * .3;
      const el = poinsettia ? .25 + (1 - t) * .4 : .1 + rnd() * .8;
      const dir = V(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)).normalize();
      const cell = poinsettia ? (t > .45 ? GL.poinsettia : GL.heart) : (k % 3 === 0 ? GL.croton2 : GL.croton);
      blade(leaves, base, dir, UP.clone().cross(dir).normalize(), .17 + rnd() * .08, .085, cell, { segs: 3, bend: .45, fold: .15, sway: [.4, .9], cells: 4 });
    }
  }
  return { wood, leaves, leafAtlas: 'gardenLeaves', height: .85, woodColor: '#5c6b3a' };
};

SPECIES.climber = (rnd, opts = {}) => {
  // Roses and creepers trained on a mesh fence: a deep green curtain along local X, flowering on both faces.
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder();
  const L = opts.length || 2, Hh = opts.height || 2;
  for (let i = 0; i < 4; i++) {
    const pts = [];
    let x = (rnd() - .5) * L * .5;
    for (let j = 0; j <= 6; j++) { x += (rnd() - .5) * .5; pts.push(V(Math.max(-L / 2, Math.min(L / 2, x)), Hh * j / 6, (rnd() - .5) * .08)); }
    tube(wood, pts, pts.map((_, k) => .012 - .0012 * k), 4, [0, .3]);
  }
  const count = Math.round(L * Hh * 70);
  for (let i = 0; i < count; i++) {
    const y = Math.pow(rnd(), .8) * Hh, side = rnd() < .5 ? -1 : 1;
    const p = V((rnd() - .5) * L, y, side * (.04 + rnd() * .12));
    const n = V((rnd() - .5) * .6, (rnd() - .3) * .5, side).normalize();
    let right = UP.clone().cross(n); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
    right.applyAxisAngle(n, rnd() * Math.PI);
    card(leaves, p, right, n.clone().cross(right).normalize(), .2 + rnd() * .08, .2 + rnd() * .08, rnd() < .6 ? GL.heart : GL.rose, 4, .3 + .5 * y / Hh, n, .7);
  }
  const cell = { white: GF.jasmine, pink: GF.pink, red: GF.red, yellow: GF.yellow }[opts.flowers] ?? GF.white;
  const blooms = Math.round(L * Hh * 11);
  for (let i = 0; i < blooms; i++) {
    const y = .3 + rnd() * (Hh - .25), side = rnd() < .5 ? -1 : 1;
    const p = V((rnd() - .5) * L, y, side * (.14 + rnd() * .06));
    const n = V((rnd() - .5) * .4, .2, side).normalize();
    let right = UP.clone().cross(n); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
    const s = (cell === GF.jasmine ? .13 : .1) + rnd() * .04;
    card(flowers, p, right, n.clone().cross(right).normalize(), s, s, cell, 4, .5, n, .5);
  }
  return { wood, leaves, flowers, leafAtlas: 'gardenLeaves', flowerAtlas: 'gardenFlowers', height: Hh };
};

SPECIES.bougainvillea = (rnd, opts = {}) => {
  const wood = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder();
  const cell = opts.bracts === 'white' ? GF.bractWhite : GF.magenta;
  const canes = 8 + Math.floor(rnd() * 5);
  for (let i = 0; i < canes; i++) {
    const a = rnd() * Math.PI * 2;
    const pts = curve(V(0, 0, 0), V(Math.cos(a) * .45, 1, Math.sin(a) * .45), 1.1 + rnd() * .6, 5, .45, 0, .15, rnd);
    tube(wood, pts, pts.map((_, k) => .016 - .002 * k), 4, [0, .6]);
    for (let j = 1; j < pts.length; j++) {
      const outer = j / (pts.length - 1);
      for (let q = 0; q < 3; q++) {
        const p = pts[j].clone().add(V((rnd() - .5) * .22, (rnd() - .5) * .14, (rnd() - .5) * .22));
        const r = V(rnd() - .5, rnd() * .5 + .1, rnd() - .5).normalize();
        let right = UP.clone().cross(r); if (right.lengthSq() < 1e-3) right = V(1, 0, 0); right.normalize();
        const bract = rnd() < .25 + .55 * outer;
        card(bract ? flowers : leaves, p, right, r.clone().cross(right).normalize(), bract ? .17 + rnd() * .07 : .18, bract ? .17 + rnd() * .07 : .18,
          bract ? cell : GL.bougainvillea, 4, .4 + .5 * outer, r, .6);
      }
    }
  }
  return { wood, leaves, flowers, leafAtlas: 'gardenLeaves', flowerAtlas: 'gardenFlowers', height: 1.4 };
};

SPECIES.tulsi = (rnd) => {
  const wood = new GeoBuilder(), mass = new GeoBuilder(), leaves = new GeoBuilder(), flowers = new GeoBuilder();
  const R = .22, c = V(0, .3, 0);
  for (let i = 0; i < 5; i++) {
    const a = rnd() * Math.PI * 2;
    const pts = curve(V(0, 0, 0), V(Math.cos(a) * .3, 1, Math.sin(a) * .3), .42, 3, 0, 0, .15, rnd);
    tube(wood, pts, [.01, .008, .006, .004], 4, [0, .4]);
  }
  blob(mass, c, V(R * .7, R * .8, R * .7), rnd, 2, .12, .2, true);
  canopyCards(leaves, c, V(R, R * 1.05, R), 70, .13, rnd, { cells: [GL.tulsi], grid: 4, depth: .3, swayScale: .5, upBias: .3 });
  for (let i = 0; i < 14; i++) {
    const th = rnd() * Math.PI * 2, r = rnd() * R * .8;
    const p = V(Math.cos(th) * r, c.y + R * (.75 + rnd() * .3), Math.sin(th) * r);
    card(flowers, p, V(Math.cos(th + 1.6), 0, Math.sin(th + 1.6)), V(0, 1, 0), .05, .14, GF.tulsi, 4, .7);
  }
  return { wood, mass, leaves, flowers, leafAtlas: 'gardenLeaves', flowerAtlas: 'gardenFlowers', height: .55 };
};

SPECIES.vegetable = (rnd, opts = {}) => {
  const leaves = new GeoBuilder(), flowers = new GeoBuilder(), mass = new GeoBuilder();
  if (opts.kind === 'leafy') {
    const n = 9 + Math.floor(rnd() * 5);
    for (let i = 0; i < n; i++) {
      const az = i * 2.399 + rnd() * .3, el = .5 + rnd() * .6;
      const dir = V(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)).normalize();
      blade(leaves, V(0, .02, 0), dir, UP.clone().cross(dir).normalize(), .22 + rnd() * .08, .14, GL.leafy, { segs: 3, bend: .6, fold: .2, sway: [.3, .8], cells: 4 });
    }
    return { leaves, leafAtlas: 'gardenLeaves', height: .3 };
  }
  const R = .26, c = V(0, .28, 0);
  blob(mass, c, V(R * .7, R * .75, R * .7), rnd, 2, .12, .2, true);
  canopyCards(leaves, c, V(R, R * 1.05, R), 60, .18, rnd, { cells: [GL.tomato], grid: 4, depth: .35, swayScale: .5 });
  const fruit = opts.kind === 'brinjal' ? GF.purple : GF.geranium;
  for (let i = 0; i < 8; i++) {
    const th = rnd() * Math.PI * 2;
    const p = V(Math.cos(th) * R * .9, c.y - R * .2 + rnd() * R * .6, Math.sin(th) * R * .9);
    card(flowers, p, V(Math.cos(th + 1.6), 0, Math.sin(th + 1.6)), V(0, 1, 0), .07, .07, fruit, 4, .5);
  }
  return { mass, leaves, flowers, leafAtlas: 'gardenLeaves', flowerAtlas: 'gardenFlowers', height: .55 };
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
