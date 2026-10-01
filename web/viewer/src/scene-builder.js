// Converts the shared FloorForge scene contract (Z-up metres, instanced assets) into merged,
// UV-mapped Three.js buckets grouped by material / floor / visibility class.
import * as THREE from 'three';
import { rotationMatrix } from './util.js';

const OVERHEAD = new Set(['roof', 'ceiling', 'railing', 'canopy', 'pipe', 'accent', 'fin', 'screen', 'band', 'pergola', 'soffit', 'roof-edge',
  'fascia', 'carport', 'massing', 'door-portal', 'window-hood', 'shade', 'downlight', 'cove', 'pergola-glass', 'coping', 'parapet']);
const OPENING = new Set(['window', 'glazing', 'glass', 'curtain', 'door', 'blind']);
const CLIPPED = new Set(['wall', 'joinery', 'window-surround', 'sill', 'skirting', 'wall-tile', 'cladding', 'wall-panel', 'art', 'mirror']);
const FLOORISH = new Set(['floor', 'finish', 'stair', 'rug', 'threshold']);
// Roles that never block the walking capsule (thin, decorative or overhead light fittings).
const NO_COLLIDE = new Set(['curtain', 'rug', 'detail', 'fixture', 'plant-proxy', 'light-glow', 'downlight', 'cove', 'art', 'decor', 'blind', 'lamp']);
// Proxies exist for GLB/drawings; the realistic viewer grows the actual plants procedurally.
export const SKIP_RENDER = new Set(['plant-proxy', 'screen-wire']);
const GRAIN = new Set(['wood', 'woodfloor', 'deck', 'brushed', 'stoneclad']);

export function visibilityClass(role) {
  if (OVERHEAD.has(role)) return 'overhead';
  if (OPENING.has(role)) return 'opening';
  if (CLIPPED.has(role)) return 'clip';
  if (FLOORISH.has(role)) return 'floor';
  return 'other';
}

export function collides(role) { return !NO_COLLIDE.has(role); }

export function buildBuckets(data, materials) {
  const buckets = new Map();
  const assetInfo = new Map();
  for (const [key, a] of Object.entries(data.assets)) {
    let lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (const v of a.vertices) for (let i = 0; i < 3; i++) { lo[i] = Math.min(lo[i], v[i]); hi[i] = Math.max(hi[i], v[i]); }
    assetInfo.set(key, { lo, hi, closed: a.closed !== false });
  }
  const tileCache = new Map();
  const tileOf = (name) => { if (!tileCache.has(name)) tileCache.set(name, materials.tileSize(name)); return tileCache.get(name); };
  const kindOf = (name) => materials.descriptor(name).kind;

  for (const node of data.nodes) {
    if (SKIP_RENDER.has(node.role)) continue;
    const asset = data.assets[node.asset];
    if (!asset) throw Error('Missing geometry asset ' + node.asset);
    const info = assetInfo.get(node.asset);
    const matDef = data.materials[node.material] || {};
    const transparent = (matDef.alpha ?? 1) < 1;
    const cls = visibilityClass(node.role);
    // Open (non-watertight) surfaces such as duvets, curtains and leaves never block walking.
    const collide = collides(node.role) && info.closed;
    const doubleSided = !info.closed || transparent;
    const key = [node.material, node.floor, cls, collide ? 1 : 0, doubleSided ? 1 : 0].join('|');
    if (!buckets.has(key)) buckets.set(key, { key, material: node.material, floor: node.floor, cls, collide, doubleSided, transparent, pos: [], nor: [], uv: [], roles: new Set() });
    const b = buckets.get(key);
    b.roles.add(node.role);

    const [sx, sy, sz] = node.scale;
    const [rx, ry, rz] = node.rotation;
    const [tx, ty, tz] = node.position;
    const rotated = Math.abs(rx) + Math.abs(ry) + Math.abs(rz) > 1e-9;
    const R = rotationMatrix(rx, ry, rz);
    const tile = tileOf(node.material);
    const kind = kindOf(node.material);
    const grain = GRAIN.has(kind);
    // Extents of the object in its own (scaled) frame — used to run wood grain along the long axis.
    const ext = [0, 1, 2].map((i) => Math.abs((info.hi[i] - info.lo[i]) * node.scale[i]));
    const verts = asset.vertices, norms = asset.normals;
    const nv = verts.length;
    const W = new Float64Array(nv * 3), L = new Float64Array(nv * 3), N = norms ? new Float64Array(nv * 3) : null;
    for (let i = 0; i < nv; i++) {
      const v = verts[i];
      const lx = v[0] * sx, ly = v[1] * sy, lz = v[2] * sz;
      L[i * 3] = lx; L[i * 3 + 1] = ly; L[i * 3 + 2] = lz;
      W[i * 3] = R[0] * lx + R[1] * ly + R[2] * lz + tx;
      W[i * 3 + 1] = R[3] * lx + R[4] * ly + R[5] * lz + ty;
      W[i * 3 + 2] = R[6] * lx + R[7] * ly + R[8] * lz + tz;
      if (N) {
        const n = norms[i];
        const ax = n[0] / (sx || 1), ay = n[1] / (sy || 1), az = n[2] / (sz || 1);
        let wx = R[0] * ax + R[1] * ay + R[2] * az, wy = R[3] * ax + R[4] * ay + R[5] * az, wz = R[6] * ax + R[7] * ay + R[8] * az;
        const l = Math.hypot(wx, wy, wz) || 1;
        N[i * 3] = wx / l; N[i * 3 + 1] = wy / l; N[i * 3 + 2] = wz / l;
      }
    }
    // Box-projected UVs: world-aligned for unrotated architecture (continuous across pieces), object-local otherwise.
    const P = rotated ? L : W;
    const flip = Math.sign(sx * sy * sz) < 0;
    for (const f of asset.faces) {
      const a = f[0], c1 = flip ? f[2] : f[1], c2 = flip ? f[1] : f[2];
      const ids = [a, c1, c2];
      // Face normal in world (for shading) and in projection frame (for UV axis choice).
      const e1 = [W[c1 * 3] - W[a * 3], W[c1 * 3 + 1] - W[a * 3 + 1], W[c1 * 3 + 2] - W[a * 3 + 2]];
      const e2 = [W[c2 * 3] - W[a * 3], W[c2 * 3 + 1] - W[a * 3 + 1], W[c2 * 3 + 2] - W[a * 3 + 2]];
      let fn = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]];
      const fl = Math.hypot(...fn);
      if (fl < 1e-12) continue;
      fn = fn.map((x) => x / fl);
      let pn = fn;
      if (rotated) {
        const p1 = [L[c1 * 3] - L[a * 3], L[c1 * 3 + 1] - L[a * 3 + 1], L[c1 * 3 + 2] - L[a * 3 + 2]];
        const p2 = [L[c2 * 3] - L[a * 3], L[c2 * 3 + 1] - L[a * 3 + 1], L[c2 * 3 + 2] - L[a * 3 + 2]];
        pn = [p1[1] * p2[2] - p1[2] * p2[1], p1[2] * p2[0] - p1[0] * p2[2], p1[0] * p2[1] - p1[1] * p2[0]];
      }
      const ax = Math.abs(pn[0]), ay = Math.abs(pn[1]), az = Math.abs(pn[2]);
      let ua, va;
      if (az >= ax && az >= ay) { ua = 0; va = 1; if (grain && ext[1] > ext[0] * 1.05) { ua = 1; va = 0; } }
      else if (ax >= ay) { ua = 1; va = 2; if (grain && ext[2] > ext[1] * 1.5) { ua = 2; va = 1; } }
      else { ua = 0; va = 2; if (grain && ext[2] > ext[0] * 1.5) { ua = 2; va = 0; } }
      for (const i of ids) {
        b.pos.push(W[i * 3], W[i * 3 + 2], -W[i * 3 + 1]);
        if (N) b.nor.push(N[i * 3], N[i * 3 + 2], -N[i * 3 + 1]);
        else b.nor.push(fn[0], fn[2], -fn[1]);
        b.uv.push(P[i * 3 + ua] / tile[0], P[i * 3 + va] / tile[1]);
      }
    }
  }
  const out = [];
  for (const b of buckets.values()) {
    if (!b.pos.length) continue;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(b.nor, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(b.uv, 2));
    g.computeBoundingSphere();
    g.computeBoundingBox();
    out.push({ ...b, pos: null, nor: null, uv: null, geometry: g, roles: [...b.roles] });
  }
  return out;
}
