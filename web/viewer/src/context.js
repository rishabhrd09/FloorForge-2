// Viewer-only neighbourhood context: neighbouring plots and houses, street trees, lamp posts and a distant
// tree line. Deterministic from the plot size. Context is never exported and makes no design claim.
import * as THREE from 'three';
import { mulberry32 } from './util.js';
import { buildSpecies } from './plant-builders.js';

const s2t = (x, y, z) => new THREE.Vector3(x, z, -y);

function boxGeo(x0, y0, z0, x1, y1, z1, out) {
  // Scene-space (Z-up) axis-aligned box appended as non-indexed triangles with box-projected UVs.
  const P = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
  const faces = [[0, 1, 5, 4, [0, -1, 0]], [1, 2, 6, 5, [1, 0, 0]], [2, 3, 7, 6, [0, 1, 0]], [3, 0, 4, 7, [-1, 0, 0]], [4, 5, 6, 7, [0, 0, 1]], [3, 2, 1, 0, [0, 0, -1]]];
  for (const [a, b, c, d, n] of faces) {
    for (const i of [a, b, c, a, c, d]) {
      const p = P[i];
      out.pos.push(p[0], p[2], -p[1]);
      out.nor.push(n[0], n[2], -n[1]);
      const ax = Math.abs(n[0]), ay = Math.abs(n[1]);
      const uv = n[2] !== 0 ? [p[0], p[1]] : ax > ay ? [p[1], p[2]] : [p[0], p[2]];
      out.uv.push(uv[0] / 2.2, uv[1] / 2.2);
    }
  }
}

function geometry(out) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(out.pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(out.nor, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(out.uv, 2));
  g.computeBoundingSphere();
  return g;
}

export function buildContext(viewer, data) {
  const group = new THREE.Group();
  group.name = 'context';
  const [xmin, ymin, gz, xmax, ymax] = data.bounds;
  const g = gz; // ground level
  const W = xmax - xmin, D = ymax - ymin;
  const rnd = mulberry32(Math.round(W * 1000 + D * 7));
  const buckets = { render: { pos: [], nor: [], uv: [] }, render2: { pos: [], nor: [], uv: [] }, glass: { pos: [], nor: [], uv: [] }, frame: { pos: [], nor: [], uv: [] }, roof: { pos: [], nor: [], uv: [] }, wall: { pos: [], nor: [], uv: [] } };
  const trees = [];
  const subjectFloors = data.storeys || 1;
  const house = (x0, y0, x1, y1, facingRoad) => {
    if (x1 - x0 < 4 || y1 - y0 < 4) return;
    const floors = rnd() < .7 ? subjectFloors : subjectFloors === 1 ? 2 : 1;
    const tone = rnd() < .6 ? 'render' : 'render2';
    // Massing: a full ground-floor volume and, on some houses, an upper floor set back from the street.
    const setback = floors > 1 && rnd() < .5 ? 1.2 + rnd() * .9 : 0;
    const fy0 = facingRoad > 0 ? y0 + setback : y0, fy1 = facingRoad > 0 ? y1 : y1 - setback;
    for (let f = 0; f < floors; f++) {
      const [a0, a1] = f === 0 ? [y0, y1] : [fy0, fy1];
      boxGeo(x0, a0, g + f * 3.2, x1, a1, g + (f + 1) * 3.2, buckets[tone]);
      if (f === 0 && setback) { const ov = .25; boxGeo(x0 - ov, y0 - ov, g + 3.2, x1 + ov, y1 + ov, g + 3.2 + .22, buckets.roof); }
    }
    const h = floors * 3.2;
    // Floating roof slab over the top volume.
    const ov = .3 + rnd() * .3;
    boxGeo(x0 - ov, fy0 - ov, g + h, x1 + ov, fy1 + ov, g + h + .28, buckets.roof);
    // Framed glazing on the road-facing side of every floor, with a centre mullion on wide panes.
    for (let f = 0; f < floors; f++) {
      const face = facingRoad > 0 ? (f === 0 ? y0 : fy0) - .02 : (f === 0 ? y1 : fy1) + .02;
      const n = Math.max(1, Math.floor((x1 - x0) / 3));
      for (let i = 0; i < n; i++) {
        const cx = x0 + (i + .5) * (x1 - x0) / n, ww = Math.min(2.4, (x1 - x0) / n - .8);
        const zb = g + f * 3.2 + (f === 0 && rnd() < .5 ? .05 : .8), zt = g + f * 3.2 + 2.65;
        const fa = Math.min(face, face + .04 * facingRoad), fb = Math.max(face, face + .04 * facingRoad);
        boxGeo(cx - ww / 2, fa, zb, cx + ww / 2, fb, zt, buckets.glass);
        const t = .055, o0 = face - .045, o1 = face + .045;
        boxGeo(cx - ww / 2 - t, o0, zb - t, cx + ww / 2 + t, o1, zb, buckets.frame);
        boxGeo(cx - ww / 2 - t, o0, zt, cx + ww / 2 + t, o1, zt + t, buckets.frame);
        boxGeo(cx - ww / 2 - t, o0, zb, cx - ww / 2, o1, zt, buckets.frame);
        boxGeo(cx + ww / 2, o0, zb, cx + ww / 2 + t, o1, zt, buckets.frame);
        if (ww > 1.5) boxGeo(cx - .025, o0, zb, cx + .025, o1, zt, buckets.frame);
      }
    }
    if (rnd() < .8) trees.push({ species: rnd() < .5 ? 'tree_shade' : rnd() < .5 ? 'palm' : 'tree_standard', x: x0 + (x1 - x0) * (rnd() < .5 ? .15 : .85), y: facingRoad > 0 ? y0 - 1.8 : y1 + 1.8, s: .8 + rnd() * .4 });
    // Front-garden shrubs soften the plinth line.
    const sy = facingRoad > 0 ? y0 - .9 : y1 + .9;
    for (let sx = x0 + .6; sx < x1 - .4; sx += 1.1 + rnd() * 1.4) if (rnd() < .7) trees.push({ species: rnd() < .7 ? 'shrub_round' : 'shrub_flowering', x: sx, y: sy, s: .6 + rnd() * .35 });
  };
  // Neighbouring plots on both sides (same depth, similar widths), with boundary walls.
  for (const side of [-1, 1]) {
    let edge = side < 0 ? xmin : xmax;
    for (let k = 0; k < 3; k++) {
      const pw = Math.max(9, W * (.8 + rnd() * .5));
      const px0 = side < 0 ? edge - pw : edge, px1 = side < 0 ? edge : edge + pw;
      const setF = 3.5 + rnd() * 2.5;
      const nearGap = k === 0 ? 3.8 + rnd() * 1.8 : 1.2 + rnd();
      const farGap = 1.2 + rnd();
      const hx0 = side < 0 ? px0 + farGap : px0 + nearGap, hx1 = side < 0 ? px1 - nearGap : px1 - farGap;
      house(hx0, ymin + setF, hx1, ymax - 1.5 - rnd() * 2, 1);
      if (k === 0) {
        const tx = side < 0 ? px1 - nearGap * .5 : px0 + nearGap * .5;
        for (let ty = ymin + 3; ty < ymax - 2; ty += 4.5 + rnd() * 2) trees.push({ species: rnd() < .6 ? 'tree_standard' : 'tree_shade', x: tx, y: ty, s: .7 + rnd() * .35 });
      }
      boxGeo(px0, ymin, g, px1, ymin + .15, g + 1.4, buckets.wall);
      edge = side < 0 ? px0 : px1;
    }
  }
  // Houses across the road and behind. The opposite plots keep deep front gardens so the street-side hero
  // camera stands in open garden, never inside a neighbour's massing.
  const clearX0 = xmin - Math.max(8, W * .6), clearX1 = xmax + Math.max(8, W * .6);
  let x = xmin - W * 2.5;
  while (x < xmax + W * 2.5) {
    const pw = Math.max(9, W * (.8 + rnd() * .5));
    const back = ymin - 23 - rnd() * 2;
    house(x + 1.2, back - D * .6, x + pw - 1.2, back, -1);
    boxGeo(x, ymin - 10.6, g, x + pw, ymin - 10.45, g + 1.4, buckets.wall);
    const tx = x + pw * (.2 + rnd() * .6);
    if (tx < clearX0 || tx > clearX1) trees.push({ species: rnd() < .5 ? 'tree_shade' : 'palm', x: tx, y: ymin - 12.5 - rnd() * 2, s: .8 + rnd() * .4 });
    x += pw;
  }
  x = xmin - W * 1.5;
  while (x < xmax + W * 1.5) {
    const pw = Math.max(9, W * (.8 + rnd() * .5));
    house(x + 1.2, ymax + 3, x + pw - 1.2, ymax + 3 + D * .6, 1);
    x += pw;
  }
  // Street trees and lamp posts along the footpath.
  // Keep the street in front of the plot clear so hero and front cameras are never blocked.
  for (let sx = xmin - W * 2; sx < xmax + W * 2; sx += 9 + rnd() * 3) {
    if (sx > clearX0 && sx < clearX1) continue;
    trees.push({ species: 'tree_shade', x: sx, y: ymin - 1.2, s: .75 + rnd() * .3 });
  }
  for (let sx = xmin - W * 2 + 4; sx < xmax + W * 2; sx += 18) {
    if (sx > clearX0 - 3 && sx < clearX1 + 3) continue;
    boxGeo(sx - .06, ymin - 1.45, g, sx + .06, ymin - 1.33, g + 6.5, buckets.frame);
    boxGeo(sx - .06, ymin - 2.6, g + 6.4, sx + .06, ymin - 1.33, g + 6.5, buckets.frame);
    boxGeo(sx - .12, ymin - 2.75, g + 6.3, sx + .12, ymin - 2.4, g + 6.42, buckets.frame);
  }
  // Distant tree line ring breaking the horizon.
  const cx = (xmin + xmax) / 2, cy = (ymin + ymax) / 2;
  for (let i = 0; i < 90; i++) {
    const a = rnd() * Math.PI * 2, r = 70 + rnd() * 110;
    trees.push({ species: rnd() < .8 ? 'tree_shade' : 'palm', x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r, s: 1 + rnd() * .8, far: true });
  }
  // Nothing grows within reach of either street-side hero camera (the design camera or its sunward mirror).
  const hero = data.cameras?.hero;
  const spots = hero ? [[hero.position[0], hero.position[1]], [2 * hero.target[0] - hero.position[0], hero.position[1]]] : [];
  const planted = trees.filter((t) => t.far || spots.every(([hx, hy]) => Math.hypot(t.x - hx, t.y - hy) > 7.5));
  trees.length = 0;
  trees.push(...planted);
  const mats = viewer.materials;
  const matFor = {
    render: mats.get('wall'), render2: (() => { const m = mats.get('wall').clone(); m.color = new THREE.Color('#e6ddcc'); return m; })(),
    // Reflective glazing: reads as glass (sky and ground reflections), not as black holes.
    glass: new THREE.MeshPhysicalMaterial({ color: '#8a9aa3', roughness: .04, metalness: .85, envMapIntensity: 2.2 }),
    frame: mats.get('frame'), roof: mats.get('roof'), wall: mats.get('wall'),
  };
  const created = [];
  for (const [name, out] of Object.entries(buckets)) {
    if (!out.pos.length) continue;
    const mesh = new THREE.Mesh(geometry(out), matFor[name]);
    mesh.castShadow = name !== 'glass';
    mesh.receiveShadow = true;
    group.add(mesh);
    created.push(mesh);
  }
  if (matFor.render2 !== matFor.render) created.render2 = matFor.render2;
  // Trees: instance a few species variants.
  const veg = viewer.vegetation;
  if (veg && veg.materials) {
    const bySpecies = new Map();
    for (const t of trees) { if (!bySpecies.has(t.species)) bySpecies.set(t.species, []); bySpecies.get(t.species).push(t); }
    for (const [species, list] of bySpecies) {
      const spec = buildSpecies(species, 777 + species.length, {});
      for (const [part, geo] of Object.entries(spec.parts)) {
        if (!geo || part === 'flowers') continue;
        const mesh = new THREE.InstancedMesh(geo, veg.partMaterial(part, spec), list.length);
        const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0);
        list.forEach((t, i) => { q.setFromAxisAngle(up, rnd() * Math.PI * 2); m.compose(s2t(t.x, t.y, g), q, new THREE.Vector3(t.s, t.s, t.s)); mesh.setMatrixAt(i, m); });
        mesh.instanceMatrix.needsUpdate = true;
        mesh.castShadow = true; mesh.receiveShadow = true;
        mesh.computeBoundingSphere();
        group.add(mesh);
        created.push(mesh);
        veg.geometries.push(geo);
      }
    }
  }
  group.userData.dispose = () => { for (const m of created) if (m.geometry) m.geometry.dispose(); matFor.render2.dispose(); matFor.glass.dispose(); };
  return group;
}
