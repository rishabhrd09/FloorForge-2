// Geometry helpers for installed electrical parts. Scene data is Z-up metres;
// Three.js is Y-up, so s2t maps (x, y, z) -> (x, z, -y).
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';
import { mergeGeometries } from '../../viewer/node_modules/three/examples/jsm/utils/BufferGeometryUtils.js';

export const s2t = (p) => new THREE.Vector3(p[0], p[2], -p[1]);
export const t2s = (v) => [v.x, -v.z, v.y];
export { mergeGeometries };

// Polyline with rounded corners: straight runs keep two rings, bends get `bendSegments`.
export function roundedPath(points, radius, bendSegments = 8) {
  const pts = points.map((p) => (p.isVector3 ? p.clone() : new THREE.Vector3(...p)));
  const clean = [pts[0]];
  for (const p of pts.slice(1)) if (p.distanceTo(clean[clean.length - 1]) > 1e-5) clean.push(p);
  if (clean.length < 3 || radius <= 0) return clean;
  const out = [clean[0].clone()];
  for (let i = 1; i < clean.length - 1; i++) {
    const a = clean[i - 1], b = clean[i], c = clean[i + 1];
    const d1 = b.clone().sub(a), d2 = c.clone().sub(b);
    const l1 = d1.length(), l2 = d2.length();
    d1.normalize(); d2.normalize();
    const turn = d1.angleTo(d2);
    if (turn < 1e-3) { out.push(b.clone()); continue; }
    const t = Math.min(radius * Math.tan(turn / 2), l1 * .48, l2 * .48);
    const p0 = b.clone().addScaledVector(d1, -t), p1 = b.clone().addScaledVector(d2, t);
    const curve = new THREE.QuadraticBezierCurve3(p0, b, p1);
    for (let k = 0; k <= bendSegments; k++) out.push(curve.getPoint(k / bendSegments));
  }
  out.push(clean[clean.length - 1].clone());
  return out;
}

// Tube swept along sampled points with parallel-transport frames (no twisting at bends).
export function sweepTube(samples, radius, radial = 10, { caps = true } = {}) {
  const n = samples.length;
  if (n < 2) return null;
  const tangents = samples.map((p, i) => {
    const a = samples[Math.max(0, i - 1)], b = samples[Math.min(n - 1, i + 1)];
    return b.clone().sub(a).normalize();
  });
  let normal = new THREE.Vector3(0, 1, 0);
  if (Math.abs(normal.dot(tangents[0])) > .9) normal.set(1, 0, 0);
  normal.sub(tangents[0].clone().multiplyScalar(normal.dot(tangents[0]))).normalize();
  const normals = [normal.clone()];
  for (let i = 1; i < n; i++) {
    const axis = tangents[i - 1].clone().cross(tangents[i]);
    const len = axis.length();
    if (len > 1e-8) {
      const angle = Math.acos(THREE.MathUtils.clamp(tangents[i - 1].dot(tangents[i]), -1, 1));
      normal = normal.clone().applyAxisAngle(axis.divideScalar(len), angle);
    }
    normals.push(normal.clone());
  }
  const pos = [], nor = [], uv = [], idx = [];
  let along = 0;
  for (let i = 0; i < n; i++) {
    if (i) along += samples[i].distanceTo(samples[i - 1]);
    const t = tangents[i], N = normals[i], B = t.clone().cross(N).normalize();
    for (let k = 0; k <= radial; k++) {
      const a = k / radial * Math.PI * 2;
      const dir = N.clone().multiplyScalar(Math.cos(a)).addScaledVector(B, Math.sin(a));
      pos.push(samples[i].x + dir.x * radius, samples[i].y + dir.y * radius, samples[i].z + dir.z * radius);
      nor.push(dir.x, dir.y, dir.z);
      uv.push(k / radial, along);
    }
  }
  for (let i = 0; i < n - 1; i++) for (let k = 0; k < radial; k++) {
    const a = i * (radial + 1) + k, b = a + radial + 1;
    idx.push(a, b, a + 1, b, b + 1, a + 1);
  }
  if (caps) for (const [i, sign] of [[0, -1], [n - 1, 1]]) {
    const centre = pos.length / 3;
    const t = tangents[i];
    pos.push(samples[i].x, samples[i].y, samples[i].z); nor.push(t.x * sign, t.y * sign, t.z * sign); uv.push(.5, .5);
    for (let k = 0; k <= radial; k++) {
      const j = i * (radial + 1) + k;
      pos.push(pos[j * 3], pos[j * 3 + 1], pos[j * 3 + 2]); nor.push(t.x * sign, t.y * sign, t.z * sign); uv.push(0, 0);
    }
    for (let k = 0; k < radial; k++) {
      const a = centre + 1 + k, b = a + 1;
      if (sign < 0) idx.push(centre, b, a); else idx.push(centre, a, b);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  return g;
}

export function pathTube(points, radius, { bend = radius * 4, radial = 10, bendSegments = 8, caps = true } = {}) {
  return sweepTube(roundedPath(points, bend, bendSegments), radius, radial, { caps });
}

export function smoothTube(points, radius, { samples = 40, radial = 8, tension = .5 } = {}) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => (p.isVector3 ? p : new THREE.Vector3(...p))), false, 'centripetal', tension);
  return sweepTube(curve.getPoints(samples), radius, radial);
}

// Rounded rectangle plate in the XY plane, extruded `depth` toward +Z.
export function roundedPlate(width, height, depth, radius = .006, bevel = .0015) {
  const w = width / 2 - bevel, h = height / 2 - bevel, r = Math.min(radius, w, h);
  const s = new THREE.Shape();
  s.moveTo(-w + r, -h); s.lineTo(w - r, -h); s.quadraticCurveTo(w, -h, w, -h + r);
  s.lineTo(w, h - r); s.quadraticCurveTo(w, h, w - r, h); s.lineTo(-w + r, h);
  s.quadraticCurveTo(-w, h, -w, h - r); s.lineTo(-w, -h + r); s.quadraticCurveTo(-w, -h, -w + r, -h);
  const g = new THREE.ExtrudeGeometry(s, { depth: Math.max(1e-4, depth - 2 * bevel), bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2, curveSegments: 6 });
  g.translate(0, 0, bevel);
  return g;
}

// Rectangle frame (outer minus inner), extruded toward +Z.
export function frameGeometry(w, h, iw, ih, depth, r = .004) {
  const s = new THREE.Shape();
  const W = w / 2, H = h / 2;
  s.moveTo(-W, -H); s.lineTo(W, -H); s.lineTo(W, H); s.lineTo(-W, H); s.lineTo(-W, -H);
  const hole = new THREE.Path();
  const a = iw / 2, b = ih / 2;
  hole.moveTo(-a + r, -b); hole.lineTo(a - r, -b); hole.quadraticCurveTo(a, -b, a, -b + r); hole.lineTo(a, b - r);
  hole.quadraticCurveTo(a, b, a - r, b); hole.lineTo(-a + r, b); hole.quadraticCurveTo(-a, b, -a, b - r); hole.lineTo(-a, -b + r);
  hole.quadraticCurveTo(-a, -b, -a + r, -b);
  s.holes.push(hole);
  return new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: false, curveSegments: 4 });
}

// Open-front box (5 faces) of sheet thickness `t`, opening toward +Z, back at z = -depth.
export function openBox(w, h, depth, t = .0012) {
  const parts = [];
  const back = new THREE.BoxGeometry(w, h, t); back.translate(0, 0, -depth + t / 2); parts.push(back);
  const top = new THREE.BoxGeometry(w, t, depth); top.translate(0, h / 2 - t / 2, -depth / 2); parts.push(top);
  const bottom = new THREE.BoxGeometry(w, t, depth); bottom.translate(0, -h / 2 + t / 2, -depth / 2); parts.push(bottom);
  const left = new THREE.BoxGeometry(t, h, depth); left.translate(-w / 2 + t / 2, 0, -depth / 2); parts.push(left);
  const right = new THREE.BoxGeometry(t, h, depth); right.translate(w / 2 - t / 2, 0, -depth / 2); parts.push(right);
  return mergeGeometries(parts.map((g) => g.toNonIndexed()));
}

export function screwHead(radius = .0028, height = .0012, slot = true) {
  const head = new THREE.CylinderGeometry(radius, radius * .92, height, 16);
  head.rotateX(Math.PI / 2);
  head.translate(0, 0, height / 2);
  if (!slot) return head;
  return head;
}

// Frame that maps a wall-mounted enclosure's local axes (x along the wall, y up,
// z out of the face) into Three space, positioned at the finished face centre.
export function mountMatrix(mount) {
  const origin = s2t(mount.face);
  const xAxis = new THREE.Vector3(mount.tangent[0], 0, -mount.tangent[1]);
  const zAxis = new THREE.Vector3(mount.normal[0], 0, -mount.normal[1]);
  // keep a right-handed frame: x = y × z
  const yAxis = new THREE.Vector3(0, 1, 0);
  const x = yAxis.clone().cross(zAxis).normalize();
  if (x.dot(xAxis) < 0) { /* local x runs the other way along the wall */ }
  const m = new THREE.Matrix4().makeBasis(x, yAxis, zAxis);
  m.setPosition(origin);
  return m;
}

export function groupAtMount(mount) {
  const g = new THREE.Group();
  const m = mountMatrix(mount);
  m.decompose(g.position, g.quaternion, g.scale);
  return g;
}
