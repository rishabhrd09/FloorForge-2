// Viewer-only neighbourhood context: neighbouring plots and houses, street trees, lamp posts and a distant
// tree line. Deterministic from the plot size. Context is never exported and makes no design claim.
import * as THREE from 'three';
import { mulberry32 } from './util.js';
import { buildSpecies } from './plant-builders.js';
import { buildLawn } from './grass.js';

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

function tubeGeo(a, b, radius, out) {
  const start=s2t(...a), end=s2t(...b), delta=end.clone().sub(start);
  const geo=new THREE.CylinderGeometry(radius,radius,delta.length(),12,1).toNonIndexed();
  geo.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize()));
  geo.translate(...start.add(end).multiplyScalar(.5).toArray());
  out.pos.push(...geo.attributes.position.array); out.nor.push(...geo.attributes.normal.array);
  out.uv.push(...geo.attributes.uv.array); geo.dispose();
}

function geometry(out) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(out.pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(out.nor, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(out.uv, 2));
  g.computeBoundingSphere();
  return g;
}

// Turned objects keep curved silhouettes at street scale; inputs are radius/height.
function turnedGeo(profile, x, y, z, out) {
  const geo = new THREE.LatheGeometry(profile.map(p => new THREE.Vector2(...p)), 32).toNonIndexed();
  geo.translate(x, z, -y);
  out.pos.push(...geo.attributes.position.array);
  out.nor.push(...geo.attributes.normal.array);
  out.uv.push(...geo.attributes.uv.array);
  geo.dispose();
}

export function buildContext(viewer, data) {
  if (data.context?.style === 'tirumala-colony') {
    return buildTirumalaColonyContext(viewer, data);
  }
  const group = new THREE.Group();
  group.name = 'context';
  const [xmin, ymin, gz, xmax, ymax] = data.bounds;
  const g = gz; // ground level
  const W = xmax - xmin, D = ymax - ymin;
  const rnd = mulberry32(Math.round(W * 1000 + D * 7));
  const buckets = { render: { pos: [], nor: [], uv: [] }, render2: { pos: [], nor: [], uv: [] }, glass: { pos: [], nor: [], uv: [] }, frame: { pos: [], nor: [], uv: [] }, roof: { pos: [], nor: [], uv: [] }, wall: { pos: [], nor: [], uv: [] }, plinth: { pos: [], nor: [], uv: [] }, door: { pos: [], nor: [], uv: [] } };
  const trees = [];
  // A government colony (heritage bungalow scenes): deep front gardens, parapets with a red coping, big shade trees.
  const colony = data.context?.style === 'colony' && data.materials?.['hb-stripe'];
  if (colony) buckets.stripe = { pos: [], nor: [], uv: [] };
  const colonyTree = () => { const r = rnd(); return r < .45 ? 'neem' : r < .7 ? 'mango' : r < .85 ? 'ashoka' : 'tree_shade'; };
  const subjectFloors = data.storeys || 1;
  const house = (x0, y0, x1, y1, facingRoad) => {
    if (x1 - x0 < 4 || y1 - y0 < 4) return;
    if (colony) {
      // Colony bungalows stand in their gardens: at most 17 x 15 m, centred on the plot width.
      const cx = (x0 + x1) / 2, w = Math.min(x1 - x0, 17);
      x0 = cx - w / 2; x1 = cx + w / 2;
      if (facingRoad > 0) y1 = Math.min(y1, y0 + 15); else y0 = Math.max(y0, y1 - 15);
    }
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
    // Floating roof slab over the top volume (a parapet with a red coping in a colony).
    const ov = .3 + rnd() * .3;
    if (colony) {
      // A flat roof inside a rendered parapet ring with a red coping.
      boxGeo(x0, fy0, g + h, x1, fy1, g + h + .12, buckets.roof);
      const t = .2;
      for (const [a0, b0, a1, b1] of [[x0, fy0, x1, fy0 + t], [x0, fy1 - t, x1, fy1], [x0, fy0, x0 + t, fy1], [x1 - t, fy0, x1, fy1]]) {
        boxGeo(a0, b0, g + h, a1, b1, g + h + .72, buckets[tone]);
        boxGeo(a0 - .04, b0 - .04, g + h + .72, a1 + .04, b1 + .04, g + h + .82, buckets.stripe);
      }
    } else boxGeo(x0 - ov, fy0 - ov, g + h, x1 + ov, fy1 + ov, g + h + .28, buckets.roof);
    // A stone plinth grounds the ground-floor volume.
    boxGeo(x0 - .03, y0 - .03, g, x1 + .03, y1 + .03, g + .42, buckets.plinth);
    // Framed glazing on the road-facing side of every floor, with a centre mullion on wide panes. The middle bay of
    // the ground floor is the entrance (timber door, sidelight and canopy); some upper floors open onto a balcony.
    const n = Math.max(1, Math.floor((x1 - x0) / 3)), mid = Math.floor(n / 2);
    for (let f = 0; f < floors; f++) {
      const face = facingRoad > 0 ? (f === 0 ? y0 : fy0) - .02 : (f === 0 ? y1 : fy1) + .02;
      const balcony = f > 0 && rnd() < .5;
      for (let i = 0; i < n; i++) {
        const cx = x0 + (i + .5) * (x1 - x0) / n, ww = Math.min(colony ? 1.5 : 2.4, (x1 - x0) / n - .8);
        const entry = f === 0 && i === mid, full = entry || (balcony && i === mid);
        const zb = g + f * 3.2 + (full ? .45 : f === 0 && rnd() < .5 ? .45 : .8), zt = g + f * 3.2 + 2.65;
        const fa = Math.min(face, face + .04 * facingRoad), fb = Math.max(face, face + .04 * facingRoad);
        const t = .055, o0 = face - .045, o1 = face + .045;
        if (entry) {
          // Door leaf on one side of the bay, glass beside it, a slim canopy slab above.
          const dw = Math.min(1.05, ww * .5), dx0 = cx - ww / 2 + t, dx1 = dx0 + dw;
          boxGeo(dx0, Math.min(o0, o0 + .03 * facingRoad), zb, dx1, Math.max(o1, o1 + .03 * facingRoad), zt - .25, buckets.door);
          boxGeo(dx1 + t, fa, zb, cx + ww / 2, fb, zt, buckets.glass);
          boxGeo(dx1, o0, zb, dx1 + t, o1, zt, buckets.frame);
          boxGeo(dx0, o0, zt - .25, dx1, o1, zt, buckets.frame);
          const c0 = facingRoad > 0 ? face - 1.1 : face, c1 = facingRoad > 0 ? face : face + 1.1;
          boxGeo(cx - ww / 2 - .35, c0, zt + .12, cx + ww / 2 + .35, c1, zt + .26, buckets.roof);
        } else boxGeo(cx - ww / 2, fa, zb, cx + ww / 2, fb, zt, buckets.glass);
        boxGeo(cx - ww / 2 - t, o0, zb - t, cx + ww / 2 + t, o1, zb, buckets.frame);
        boxGeo(cx - ww / 2 - t, o0, zt, cx + ww / 2 + t, o1, zt + t, buckets.frame);
        boxGeo(cx - ww / 2 - t, o0, zb, cx - ww / 2, o1, zt, buckets.frame);
        boxGeo(cx + ww / 2, o0, zb, cx + ww / 2 + t, o1, zt, buckets.frame);
        if (ww > 1.5 && !entry) boxGeo(cx - .025, o0, zb, cx + .025, o1, zt, buckets.frame);
        if (balcony && i === mid) {
          // Balcony: slab, glass balustrade and a slim cap rail.
          const b0 = facingRoad > 0 ? face - 1.2 : face, b1 = facingRoad > 0 ? face : face + 1.2, bz = g + f * 3.2 + .3;
          boxGeo(cx - ww / 2 - .3, b0, bz, cx + ww / 2 + .3, b1, bz + .15, buckets.roof);
          const rail = facingRoad > 0 ? [b0 + .03, b0 + .045] : [b1 - .045, b1 - .03];
          boxGeo(cx - ww / 2 - .27, rail[0], bz + .15, cx + ww / 2 + .27, rail[1], bz + 1.18, buckets.glass);
          boxGeo(cx - ww / 2 - .28, rail[0] - .015, bz + 1.18, cx + ww / 2 + .28, rail[1] + .015, bz + 1.22, buckets.frame);
        }
      }
    }
    if (rnd() < .8) trees.push({ species: colony ? colonyTree() : rnd() < .5 ? 'tree_shade' : rnd() < .5 ? 'palm' : 'tree_standard', x: x0 + (x1 - x0) * (rnd() < .5 ? .15 : .85), y: facingRoad > 0 ? y0 - 1.8 : y1 + 1.8, s: colony ? .55 + rnd() * .3 : .8 + rnd() * .4 });
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
      const setF = colony ? 9 + rnd() * 4 : 3.5 + rnd() * 2.5;
      const nearGap = k === 0 ? 3.8 + rnd() * 1.8 : 1.2 + rnd();
      const farGap = 1.2 + rnd();
      const hx0 = side < 0 ? px0 + farGap : px0 + nearGap, hx1 = side < 0 ? px1 - nearGap : px1 - farGap;
      house(hx0, ymin + setF, hx1, ymax - 1.5 - rnd() * 2, 1);
      if (k === 0) {
        const tx = side < 0 ? px1 - nearGap * .5 : px0 + nearGap * .5;
        for (let ty = ymin + 3; ty < ymax - 2; ty += 4.5 + rnd() * 2) trees.push({ species: rnd() < .6 ? 'tree_standard' : 'tree_shade', x: tx, y: ty, s: .7 + rnd() * .35 });
      }
      boxGeo(px0, ymin, g, px1, ymin + .15, g + (colony ? 1.0 : 1.4), buckets.wall);
      if (colony) boxGeo(px0 - .02, ymin - .02, g + 1.0, px1 + .02, ymin + .17, g + 1.07, buckets.stripe);
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
  // The street-side hero cameras: the design camera and its sunward mirror, both aimed at the same target.
  const hero = data.cameras?.hero;
  const spots = hero ? [[hero.position[0], hero.position[1]], [2 * hero.target[0] - hero.position[0], hero.position[1]]] : [];
  const inHeroShot = (x, y) => spots.some(([hx, hy]) => {
    const vx = x - hx, vy = y - hy, tx = hero.target[0] - hx, ty = hero.target[1] - hy, d = Math.hypot(vx, vy);
    return d < 26 && (vx * tx + vy * ty) / (d * Math.hypot(tx, ty) || 1) > Math.cos(68 * Math.PI / 180);
  });
  // Street trees and lamp posts along the footpath.
  // Keep the street in front of the plot clear so hero and front cameras are never blocked.
  for (let sx = xmin - W * 2; sx < xmax + W * 2; sx += 9 + rnd() * 3) {
    if (sx > clearX0 && sx < clearX1) continue;
    trees.push({ species: colony ? colonyTree() : 'tree_shade', x: sx, y: ymin - 1.2, s: colony ? .6 + rnd() * .3 : .75 + rnd() * .3 });
  }
  for (let sx = xmin - W * 2 + 4; sx < xmax + W * 2; sx += 18) {
    // A lamp post in the foreground of a hero view (even on a very wide screen) would split the picture.
    if ((sx > clearX0 - 3 && sx < clearX1 + 3) || inHeroShot(sx, ymin - 1.4)) continue;
    boxGeo(sx - .06, ymin - 1.45, g, sx + .06, ymin - 1.33, g + 6.5, buckets.frame);
    boxGeo(sx - .06, ymin - 2.6, g + 6.4, sx + .06, ymin - 1.33, g + 6.5, buckets.frame);
    boxGeo(sx - .12, ymin - 2.75, g + 6.3, sx + .12, ymin - 2.4, g + 6.42, buckets.frame);
  }
  // Distant tree line ring breaking the horizon.
  const cx = (xmin + xmax) / 2, cy = (ymin + ymax) / 2;
  for (let i = 0; i < 90; i++) {
    const a = rnd() * Math.PI * 2, r = 70 + rnd() * 110;
    trees.push({ species: colony ? (rnd() < .5 ? 'neem' : 'tree_shade') : rnd() < .8 ? 'tree_shade' : 'palm', x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r, s: colony ? .8 + rnd() * .5 : 1 + rnd() * .8, far: true });
  }
  // Nothing grows within reach of either street-side hero camera (the design camera or its sunward mirror).
  const planted = trees.filter((t) => t.far || spots.every(([hx, hy]) => Math.hypot(t.x - hx, t.y - hy) > 7.5));
  trees.length = 0;
  trees.push(...planted);
  const mats = viewer.materials;
  const matFor = {
    render: mats.get('wall'), render2: (() => { const m = mats.get('wall').clone(); m.color = new THREE.Color('#e6ddcc'); return m; })(),
    // Reflective glazing: reads as glass (sky and ground reflections), not as black holes.
    glass: new THREE.MeshPhysicalMaterial({ color: '#8a9aa3', roughness: .04, metalness: .85, envMapIntensity: 2.2 }),
    frame: mats.get('frame'), roof: mats.get('roof'), wall: mats.get('wall'), plinth: mats.get('stone'), door: mats.get('walnut'),
    ...(colony ? { stripe: mats.get('hb-stripe'), plinth: mats.get('hb-plinth') } : {}),
  };
  matFor.render2.name = 'context-render'; matFor.glass.name = 'context-glass';
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
        list.forEach((t, i) => { q.setFromAxisAngle(up, rnd() * Math.PI * 2); const st=t.stretch||[1,1,1];
          m.compose(s2t(t.x, t.y, g), q, new THREE.Vector3(t.s*st[0], t.s*st[1], t.s*st[2])); mesh.setMatrixAt(i, m); });
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

function buildTirumalaColonyContext(viewer, data) {
  const group = new THREE.Group();
  group.name = 'context';
  const ctx = data.context || {};
  const [xmin, ymin, gz, xmax, ymax] = data.bounds;
  const g = gz;
  const rnd = mulberry32(26039);
  const refined = !!data.exteriorRefinement;
  const realistic = !!data.realismRefinement;
  const lawnPockets = [];
  const meshFaces = [];
  const jointHalf = realistic ? .006 : .025;

  const buckets = {
    plantingSoil: { pos: [], nor: [], uv: [] },
    concreteRoad: { pos: [], nor: [], uv: [] },
    roadJoint: { pos: [], nor: [], uv: [] },
    drainSlab: { pos: [], nor: [], uv: [] },
    drainHole: { pos: [], nor: [], uv: [] },
    paverVerge: { pos: [], nor: [], uv: [] },
    kerbStone: { pos: [], nor: [], uv: [] },
    colonyLawn: { pos: [], nor: [], uv: [] },
    houseWhite: { pos: [], nor: [], uv: [] },
    houseGrey: { pos: [], nor: [], uv: [] },
    houseBlueGrey: { pos: [], nor: [], uv: [] },
    neighbourCream: { pos: [], nor: [], uv: [] },
    neighbourBand: { pos: [], nor: [], uv: [] },
    glass: { pos: [], nor: [], uv: [] },
    darkFrame: { pos: [], nor: [], uv: [] },
    timberWarm: { pos: [], nor: [], uv: [] },
    potStone: { pos: [], nor: [], uv: [] },
    terracotta: { pos: [], nor: [], uv: [] },
    courtSurface: { pos: [], nor: [], uv: [] },
    courtRed: { pos: [], nor: [], uv: [] },
    courtLine: { pos: [], nor: [], uv: [] },
    paleMesh: { pos: [], nor: [], uv: [] },
    cabinetBody: { pos: [], nor: [], uv: [] },
    cabinetTrim: { pos: [], nor: [], uv: [] },
    weatheredWall: { pos: [], nor: [], uv: [] },
    mauveWall: { pos: [], nor: [], uv: [] },
    mauveGroove: { pos: [], nor: [], uv: [] },
    wallCoping: { pos: [], nor: [], uv: [] },
    burgundyShrub: { pos: [], nor: [], uv: [] },
    whiteBlossom: { pos: [], nor: [], uv: [] },
    pillarCap: { pos: [], nor: [], uv: [] },
    galvSteel: { pos: [], nor: [], uv: [] },
    lampGlow: { pos: [], nor: [], uv: [] },
  };
  const existingBuckets = {
    weatheredWall: { pos: [], nor: [], uv: [] },
    mauveWall: { pos: [], nor: [], uv: [] },
    mauveGroove: { pos: [], nor: [], uv: [] },
    wallCoping: { pos: [], nor: [], uv: [] },
    redEarth: { pos: [], nor: [], uv: [] },
    footingBlock: { pos: [], nor: [], uv: [] },
    colonyLawn: { pos: [], nor: [], uv: [] },
    burgundyShrub: { pos: [], nor: [], uv: [] },
    whiteBlossom: { pos: [], nor: [], uv: [] },
    pillarCap: { pos: [], nor: [], uv: [] },
  };

  // Helper: add precast storm-drain cover slabs with paired circular drainage holes (V01, R09, R13)
  const addDrainSlabRun = (x0, y0, x1, y1, alongX) => {
    const step = 1.25;
    if (alongX) {
      for (let x = x0 + 0.4; x < x1 - 0.8; x += step) {
        boxGeo(x, y0, g + 0.018, x + 1.12, y1, g + 0.042, buckets.drainSlab);
        const cy = (y0 + y1) / 2;
        if (realistic) {
          for (const dx of [.385,.735]) turnedGeo([[0,0],[.035,0],[.035,.004],[0,.004]],x+dx,cy,g+.043,buckets.drainHole);
        } else {
          boxGeo(x + 0.34, cy - 0.045, g + 0.02, x + 0.43, cy + 0.045, g + 0.045, buckets.drainHole);
          boxGeo(x + 0.69, cy - 0.045, g + 0.02, x + 0.78, cy + 0.045, g + 0.045, buckets.drainHole);
        }
      }
    } else {
      for (let y = y0 + 0.4; y < y1 - 0.8; y += step) {
        boxGeo(x0, y, g + 0.018, x1, y + 1.12, g + 0.042, buckets.drainSlab);
        const cx = (x0 + x1) / 2;
        if (realistic) {
          for (const dy of [.385,.735]) turnedGeo([[0,0],[.035,0],[.035,.004],[0,.004]],cx,y+dy,g+.043,buckets.drainHole);
        } else {
          boxGeo(cx - 0.045, y + 0.34, g + 0.02, cx + 0.045, y + 0.43, g + 0.045, buckets.drainHole);
          boxGeo(cx - 0.045, y + 0.69, g + 0.02, cx + 0.045, y + 0.78, g + 0.045, buckets.drainHole);
        }
      }
    }
  };

  // Helper: add horizontally grooved square corner pier (R11, V02, V05)
  const addGroovedCornerPier = (px0, py0, px1, py1, ph, targetBuckets = buckets) => {
    boxGeo(px0, py0, g, px1, py1, g + ph - 0.12, targetBuckets.mauveWall);
    for (let z = g + 0.18; z < g + ph - 0.18; z += 0.15) {
      boxGeo(px0 - 0.012, py0 - 0.012, z, px1 + 0.012, py1 + 0.012, z + 0.028, targetBuckets.mauveGroove);
    }
    boxGeo(px0 - 0.045, py0 - 0.045, g + ph - 0.12, px1 + 0.045, py1 + 0.045, g + ph, targetBuckets.wallCoping);
  };

  // Helper: add mixed burgundy Acalypha + white-flowering green Tabernaemontana roadside hedge (R10, R12, V03, V05)
  const addMixedHedgePoint = (hx, hy, idx, targetBuckets = buckets, targetTrees = trees) => {
    if (refined) {
      // Leaf geometry replaces the accidental opaque red 'pillars'. Keep the
      // planting below the low wall and within the existing verge strip.
      targetTrees.push({species: idx % 5 === 0 ? 'croton' : 'shrub_round',
        x: hx + (rnd()-.5)*.055, y: hy + (rnd()-.5)*.055,
        s: .65 + rnd()*.12, stretch: [.92, .82, 1.05]});
      if (idx % 3 === 1) targetTrees.push({species:'flower_clump', opts:{color:'white'},
        x:hx+.10, y:hy+.08, s:.70});
      return;
    }
    targetTrees.push({ species: idx % 2 === 0 ? 'shrub_flowering' : 'shrub_round', x: hx, y: hy, s: 0.66 + (idx % 3) * 0.06 });
    if (idx % 2 === 0) {
      boxGeo(hx - 0.28, hy - 0.28, g + 0.55, hx + 0.28, hy + 0.28, g + 1.12, targetBuckets.burgundyShrub);
      boxGeo(hx - 0.18, hy - 0.36, g + 0.72, hx + 0.22, hy + 0.18, g + 1.24, targetBuckets.burgundyShrub);
    } else {
      boxGeo(hx - 0.05, hy - 0.14, g + 0.98, hx + 0.05, hy - 0.04, g + 1.06, targetBuckets.whiteBlossom);
      boxGeo(hx + 0.08, hy + 0.06, g + 1.02, hx + 0.16, hy + 0.14, g + 1.10, targetBuckets.whiteBlossom);
    }
  };

  // Helper: add slim dark-grey angled LED street luminaire on concrete plinth (R09, R13, R14, V04)
  const addStreetLight = (px, py, ph, armDx, armDy) => {
    if (refined) {
      boxGeo(px-.10,py-.10,g,px+.10,py+.10,g+.20,buckets.wallCoping);
      tubeGeo([px,py,g+.20],[px,py,g+ph-.35],.045,buckets.darkFrame);
      tubeGeo([px,py,g+ph-.35],[px+armDx*.85,py+armDy*.85,g+ph],.035,buckets.darkFrame);
      const ex=px+armDx,ey=py+armDy;
      boxGeo(ex-.20,ey-.07,g+ph-.07,ex+.20,ey+.07,g+ph+.005,buckets.darkFrame);
      boxGeo(ex-.17,ey-.055,g+ph-.076,ex+.17,ey+.055,g+ph-.07,buckets.lampGlow);
      return;
    }

    boxGeo(px - 0.14, py - 0.14, g, px + 0.14, py + 0.14, g + 0.42, buckets.wallCoping);
    boxGeo(px - 0.075, py - 0.075, g + 0.42, px + 0.075, py + 0.075, g + 1.15, buckets.darkFrame);
    boxGeo(px - 0.05, py - 0.05, g + 1.15, px + 0.05, py + 0.05, g + ph, buckets.darkFrame);
    const ex = px + armDx, ey = py + armDy;
    const ax0 = Math.min(px, ex) - 0.035, ax1 = Math.max(px, ex) + 0.035;
    const ay0 = Math.min(py, ey) - 0.035, ay1 = Math.max(py, ey) + 0.035;
    boxGeo(ax0, ay0, g + ph - 0.10, ax1, ay1, g + ph + 0.04, buckets.darkFrame);
    boxGeo(ex - 0.22, ey - 0.14, g + ph - 0.14, ex + 0.22, ey + 0.14, g + ph - 0.02, buckets.cabinetTrim);
    boxGeo(ex - 0.18, ey - 0.10, g + ph - 0.17, ex + 0.18, ey + 0.10, g + ph - 0.13, buckets.lampGlow);
  };

  const trees = [];
  const existingTrees = [];

  // 1. Confirmed North 12 m Road & East 9 m Road with paver verges and concrete carriageways
  const nRoad = ctx.roads?.north_road_12m;
  if (nRoad) {
    const [rx0, ry0, rx1, ry1] = nRoad.carriageway_bounds_scene;
    boxGeo(rx0, ry0, g - 0.04, rx1, ry1, g + 0.015, buckets.concreteRoad);
    for (let y = ry0 + 3.5; y < ry1 - 1.0; y += 3.8) {
      boxGeo(rx0 + 0.05, y - jointHalf, g + 0.016, rx1 - 0.05, y + jointHalf, g + 0.02, buckets.roadJoint);
    }
    const [sv0, sv1, sv2, sv3] = nRoad.south_verge_bounds_scene;
    boxGeo(sv0, sv1, g - 0.03, sv2, sv3, g + 0.035, buckets.paverVerge);
    addDrainSlabRun(refined ? sv2-.62 : sv0+.1, sv1, refined ? sv2-.07 : sv0+.65, sv3, false);
    const [nv0, nv1, nv2, nv3] = nRoad.north_verge_bounds_scene;
    boxGeo(nv0, nv1, g - 0.03, nv2, nv3, g + 0.035, buckets.paverVerge);
    addDrainSlabRun(nv0 - 0.62, nv1, nv0 - 0.08, nv3, false);
  }

  const eRoad = ctx.roads?.east_road_9m;
  if (eRoad) {
    const [ex0, ey0, ex1, ey1] = eRoad.carriageway_bounds_scene;
    boxGeo(ex0, ey0, g - 0.04, ex1, ey1, g + 0.014, buckets.concreteRoad);
    for (let x = ex0 + 3.5; x < ex1 - 1.0; x += 3.8) {
      boxGeo(x - jointHalf, ey0 + 0.05, g + 0.015, x + jointHalf, ey1 - 0.05, g + 0.019, buckets.roadJoint);
    }
    const [wv0, wv1, wv2, wv3] = eRoad.west_verge_bounds_scene;
    boxGeo(wv0, wv1, g - 0.03, wv2, wv3, g + 0.035, buckets.paverVerge);
    addDrainSlabRun(wv0, wv1 - 0.62, wv2, wv1 - 0.08, true);
    const [ev0, ev1, ev2, ev3] = eRoad.east_verge_bounds_scene;
    boxGeo(ev0, ev1, g - 0.03, ev2, ev3, g + 0.035, buckets.paverVerge);
    addDrainSlabRun(ev0, ev1 + 0.08, ev2, ev1 + 0.62, true);
  }

  if (refined) {
    const ax=xmax, bx=xmax+1.8, ay=-1.5, by=0;
    const x0=xmax+.36, x1=xmax+1.40, y0=-1.18, y1=-.18;
    for (const b of [[ax,ay,bx,y0],[ax,y1,bx,by],[ax,y0,x0,y1],[x1,y0,bx,y1]])
      boxGeo(b[0],b[1],g-.025,b[2],b[3],g+.035,buckets.paverVerge);
    boxGeo(x0,y0,g,x1,y1,g+.035,buckets.colonyLawn);
    for (const b of [[x0,y0,x1,y0+.035],[x0,y1-.035,x1,y1],[x0,y0,x0+.035,y1],[x1-.035,y0,x1,y1]])
      boxGeo(b[0],b[1],g+.03,b[2],b[3],g+.045,buckets.wallCoping);
    lawnPockets.push({polygon:[[x0+.04,y0+.04],[x1-.04,y0+.04],[x1-.04,y1-.04],[x0+.04,y1-.04]],
      holes:[[[xmax+.41,-.59],[xmax+.69,-.59],[xmax+.69,-.31],[xmax+.41,-.31]]],z:g+.04,heightScale:.32});
    // Subtle groundcover at one edge; leave the gate and paved turn fully clear.
    for(let i=0;i<3;i++) trees.push({species:'flower_clump',opts:{color:'white'},x:x1-.18,y:y0+.18+i*.26,s:.5});
  }

  // 2. Opposite North Colony Garden, Pergola, Pots, Lights & N-01 House
  const nGarden = ctx.north_colony_garden;
  if (nGarden) {
    const [kx0, ky0, kx1, ky1] = nGarden.kerb_bounds_scene;
    // Raised planting edge along road side (kx0)
    boxGeo(kx0, ky0, g, kx0 + 0.35, ky1, g + 0.38, buckets.kerbStone);
    boxGeo(kx0 - 0.03, ky0 - 0.03, g + 0.38, kx0 + 0.38, ky1 + 0.03, g + 0.43, buckets.potStone);
    const [lx0, ly0, lx1, ly1] = nGarden.lawn_bounds_scene;
    boxGeo(lx0, ly0, g, lx1, ly1, g + 0.08, buckets.colonyLawn);
    if (realistic) {
      const p=nGarden.pergola.bounds_scene, pad=.26;
      lawnPockets.push({polygon:[[lx0,ly0],[lx1,ly0],[lx1,ly1],[lx0,ly1]],
        holes:[[[p[0]-pad,p[1]-pad],[p[2]+pad,p[1]-pad],[p[2]+pad,p[3]+pad],[p[0]-pad,p[3]+pad]]],
        z:g+.085,heightScale:.32});
    }
    // Clipped hedge along raised garden edge
    for (let y = ly0 + 0.6; y < ly1 - 0.6; y += 0.95) {
      trees.push({species:realistic?'vegetable':'shrub_round',opts:realistic?{kind:'leafy'}:{},
        x:kx0+.65,y,s:realistic?1.15:.62,z:realistic?g+.09:g});
    }
    // Pergola & shaded seating (N-01 left-centre)
    const perg = nGarden.pergola;
    if (perg) {
      const [px0, py0, px1, py1] = perg.bounds_scene;
      const ph = perg.height_m || 2.85;
      boxGeo(px0 - 0.25, py0 - 0.25, g + 0.08, px1 + 0.25, py1 + 0.25, g + 0.16, buckets.paverVerge);
      for (const cx of [px0 + 0.12, px1 - 0.12]) {
        for (const cy of [py0 + 0.12, py1 - 0.12]) {
          const pr=realistic?.16:.08;
          boxGeo(cx-pr,cy-pr,g+.16,cx+pr,cy+pr,g+ph,realistic?buckets.potStone:buckets.darkFrame);
          if (realistic) for(let h=.60;h<ph;h+=.45)
            boxGeo(cx-pr-.004,cy-pr-.004,g+h,cx+pr+.004,cy+pr+.004,g+h+.012,buckets.houseGrey);
        }
      }
      boxGeo(px0, py0, g + ph - 0.14, px1, py0 + 0.14, g + ph, buckets.darkFrame);
      boxGeo(px0, py1 - 0.14, g + ph - 0.14, px1, py1, g + ph, buckets.darkFrame);
      for (let y = py0 - 0.15; y <= py1 + 0.15; y += 0.42) {
        boxGeo(px0 - 0.2, y - 0.04, g + ph, px1 + 0.2, y + 0.04, g + ph + 0.1, buckets.timberWarm);
      }
      for (const [bx0, by0, bx1, by1] of perg.benches_scene || []) {
        boxGeo(bx0, by0, g + 0.16, bx1, by1, g + 0.56, buckets.timberWarm);
        boxGeo(bx0 + 0.06, by0 + 0.06, g + 0.16, bx1 - 0.06, by1 - 0.06, g + 0.46, buckets.kerbStone);
      }
    }
    // Decorative spherical / ornate garden pots on plinths (N-01)
    for (const pot of nGarden.decorative_pots_scene || []) {
      const [px, py] = pot.position;
      const r = pot.radius_m || 0.34, h = pot.height_m || 0.68;
      if (realistic) {
        turnedGeo([[0,0],[r*.52,0],[r*.56,.04],[r*.90,h*.25],[r,h*.50],
          [r*.87,h*.78],[r*.48,h*.93],[r*.43,h],[r*.34,h],[r*.32,h*.92]],px,py,g+.17,buckets.terracotta);
        continue;
      }
      boxGeo(px - r * 0.85, py - r * 0.85, g + 0.08, px + r * 0.85, py + r * 0.85, g + 0.28, buckets.kerbStone);
      boxGeo(px - r * 0.72, py - r * 0.72, g + 0.28, px + r * 0.72, py + r * 0.72, g + 0.28 + h * 0.45, buckets.potStone);
      boxGeo(px - r, py - r, g + 0.28 + h * 0.35, px + r, py + r, g + 0.28 + h * 0.85, buckets.potStone);
      boxGeo(px - r * 0.78, py - r * 0.78, g + 0.28 + h * 0.85, px + r * 0.78, py + r * 0.78, g + 0.28 + h, buckets.terracotta);
      trees.push({ species: 'shrub_flowering', x: px, y: py, s: 0.48 });
    }
    // Slim garden bollard/post lights (N-01)
    for (const lt of nGarden.garden_lights_scene || []) {
      const [lx, ly] = lt.position;
      const lh = lt.height_m || 0.85;
      if (realistic) {
        tubeGeo([lx,ly,g+.08],[lx,ly,g+.08+lh],.045,buckets.galvSteel);
        turnedGeo([[0,0],[.11,0],[.20,.19],[.12,.23],[0,.23]],lx,ly,g+lh,buckets.lampGlow);
        turnedGeo([[0,.30],[.27,.24],[.27,.21],[0,.21]],lx,ly,g+lh,buckets.darkFrame);
        continue;
      }
      boxGeo(lx - 0.045, ly - 0.045, g + 0.08, lx + 0.045, ly + 0.045, g + 0.08 + lh, buckets.darkFrame);
      boxGeo(lx - 0.065, ly - 0.065, g + 0.08 + lh, lx + 0.065, ly + 0.065, g + 0.08 + lh + 0.14, buckets.lampGlow);
    }
    for (const t of nGarden.trees_scene || []) {
      trees.push({ species: t.species, x: t.position[0], y: t.position[1], s: t.scale || 1.0 });
    }
    // Opposite two-storey white/grey house with signature dark blue-grey vertical facade (N-01)
    const opp = nGarden.opposite_house;
    if (opp) {
      const [hx0, hy0, hx1, hy1] = opp.main_body_bounds_scene;
      const hh = opp.height_m || 7.2;
      boxGeo(hx0, hy0, g, hx1, hy1, g + 0.45, buckets.kerbStone);
      boxGeo(hx0, hy0, g + 0.45, hx1, hy1, g + 3.65, buckets.houseWhite);
      boxGeo(hx0 + 0.2, hy0 + 0.2, g + 3.65, hx1 - 0.2, hy1 - 0.2, g + hh, buckets.houseGrey);
      // Roof fascia slab
      boxGeo(hx0 - 0.35, hy0 - 0.35, g + hh, hx1 + 0.35, hy1 + 0.35, g + hh + 0.28, buckets.houseWhite);
      // Projecting horizontal balconies with glass rails & warm timber soffits
      for (const [bx0, by0, bx1, by1] of opp.balcony_bands_scene || []) {
        boxGeo(bx0, by0, g + 3.55, bx1, by1, g + 3.78, buckets.houseWhite);
        boxGeo(bx0 + 0.08, by0 + 0.08, g + 3.50, bx1 - 0.08, by1 - 0.08, g + 3.55, buckets.timberWarm);
        boxGeo(bx0 + 0.04, by0 + 0.05, g + 3.78, bx0 + 0.08, by1 - 0.05, g + 4.78, buckets.glass);
        boxGeo(bx0 + 0.02, by0 + 0.03, g + 4.78, bx0 + 0.10, by1 - 0.03, g + 4.83, buckets.darkFrame);
      }
      // Signature dark blue-grey vertical feature facade panel with vertical slot windows
      if (opp.dark_blue_grey_vertical_facade_bounds_scene) {
        const [fx0, fy0, fx1, fy1] = opp.dark_blue_grey_vertical_facade_bounds_scene;
        boxGeo(fx0, fy0, g + 0.35, fx1, fy1, g + hh + 0.55, buckets.houseBlueGrey);
        const midY = (fy0 + fy1) / 2;
        if (realistic) {
          // N-01 / R08: a small horizontal upper window, larger lower window.
          for(const [w,z,h] of [[1.45,1.05,1.25],[.90,6.15,.42]]) {
            boxGeo(fx0-.10,midY-w/2-.08,g+z-.08,fx0-.02,midY+w/2+.08,g+z+h+.08,buckets.houseWhite);
            boxGeo(fx0-.115,midY-w/2,g+z,fx0-.105,midY+w/2,g+z+h,buckets.glass);
            boxGeo(fx0-.12,midY-.024,g+z,fx0-.11,midY+.024,g+z+h,buckets.houseGrey);
          }
          for(let z=.65;z<hh;z+=.65)
            boxGeo(fx0-.003,fy0,g+z,fx0+.002,fy1,g+z+.009,buckets.darkFrame);
        } else {
        boxGeo(fx0 - 0.03, midY - 0.55, g + 1.1, fx0 + 0.05, midY - 0.18, g + hh - 0.4, buckets.glass);
        boxGeo(fx0 - 0.03, midY + 0.18, g + 1.1, fx0 + 0.05, midY + 0.55, g + hh - 0.4, buckets.glass);
        }
      }
      // Large framed windows on the road-facing facade (hx0)
      for (const f of [0, 1]) {
        const z0 = g + 0.45 + f * 3.2 + 0.55, z1 = z0 + 2.1;
        for (const wy of [hy0 + 2.2, hy1 - 2.4]) {
          boxGeo(hx0 - 0.03, wy - 0.9, z0, hx0 + 0.05, wy + 0.9, z1, buckets.glass);
          boxGeo(hx0 - 0.05, wy - 0.96, z0 - 0.05, hx0 + 0.06, wy + 0.96, z0, buckets.darkFrame);
          boxGeo(hx0 - 0.05, wy - 0.96, z1, hx0 + 0.06, wy + 0.96, z1 + 0.05, buckets.darkFrame);
        }
      }
    }
  }

  // 3. Eastern Basketball-Court Tall Pale Metal Mesh Enclosure, Posts, Raised Bed & Screening Planting (E-01, N-04, V01)
  const court = ctx.east_basketball_court;
  if (court) {
    const [bx0, by0, bx1, by1] = court.raised_bed_bounds_scene;
    boxGeo(bx0, by0, g, bx1, by1, g + 0.58, buckets.mauveWall);
    boxGeo(bx0 - 0.03, by0 - 0.03, g + 0.58, bx1 + 0.03, by1 + 0.03, g + 0.65, buckets.wallCoping);
    if(realistic) boxGeo(bx0+.09,by0+.09,g+.651,bx1-.09,by1-.09,g+.655,buckets.plantingSoil);
    addGroovedCornerPier(bx1 - 0.36, by1 - 0.36, bx1 + 0.06, by1 + 0.06, 1.32);
    // Mixed burgundy Acalypha & white-flowering green hedge along court boundary (V01, V03)
    let hIdx = 0;
    for (let x = bx0 + 0.6; x < bx1 - 0.6; x += 0.85) {
      const first=trees.length;
      addMixedHedgePoint(x, (by0 + by1) / 2, hIdx++);
      if(realistic) for(let i=first;i<trees.length;i++) {
        trees[i].z=g+.65;
        if(trees[i].species==='shrub_round') trees[i].stretch=[1.35,.82,1.05];
      }
    }
    const [cx0, cy0, cx1, cy1] = court.enclosure_bounds_scene;
    boxGeo(cx0, cy0, g - 0.02, cx1, cy1, g + 0.08, buckets.courtSurface);
    // Terracotta-red court key & crisp white court lines (V01)
    const midX = (cx0 + cx1) / 2, midY = (cy0 + cy1) / 2;
    boxGeo(midX - 2.4, cy1 - 5.2, g + 0.081, midX + 2.4, cy1 - 0.6, g + 0.088, buckets.courtRed);
    boxGeo(cx0 + 0.6, cy0 + 0.6, g + 0.089, cx1 - 0.6, cy0 + 0.68, g + 0.094, buckets.courtLine);
    boxGeo(cx0 + 0.6, cy1 - 0.68, g + 0.089, cx1 - 0.6, cy1 - 0.6, g + 0.094, buckets.courtLine);
    boxGeo(cx0 + 0.6, cy0 + 0.6, g + 0.089, cx0 + 0.68, cy1 - 0.6, g + 0.094, buckets.courtLine);
    boxGeo(cx1 - 0.68, cy0 + 0.6, g + 0.089, cx1 - 0.6, cy1 - 0.6, g + 0.094, buckets.courtLine);
    boxGeo(cx0 + 0.6, midY - 0.04, g + 0.089, cx1 - 0.6, midY + 0.04, g + 0.094, buckets.courtLine);
    const fh = court.fence_height_m || 5.4;
    // Repeated vertical tubular posts
    for (const [px, py] of court.posts_scene || []) {
      boxGeo(px - 0.055, py - 0.055, g + 0.08, px + 0.055, py + 0.055, g + fh + 0.12, buckets.paleMesh);
    }
    // Horizontal rails along West face (cy1 in scene coords) and North face (cx1 in scene coords)
    for (const rz of [g + 0.35, g + 2.75, g + fh]) {
      boxGeo(cx0, cy1 - 0.04, rz - 0.035, cx1, cy1 + 0.04, rz + 0.035, buckets.paleMesh);
      boxGeo(cx1 - 0.04, cy0, rz - 0.035, cx1 + 0.04, cy1, rz + 0.035, buckets.paleMesh);
    }
    // Tall pale metal mesh lattice along West court face (cy1) and North court return (cx1)
    if (realistic) {
      meshFaces.push({x:(cx0+cx1)/2,y:cy1,z:g+.35,w:cx1-cx0,h:fh-.35,turn:0},
        {x:cx1,y:(cy0+cy1)/2,z:g+.35,w:cy1-cy0,h:fh-.35,turn:Math.PI/2});
    } else {
    for (let x = cx0 + 0.25; x < cx1; x += 0.32) {
      boxGeo(x - 0.008, cy1 - 0.01, g + 0.35, x + 0.008, cy1 + 0.01, g + fh, buckets.paleMesh);
    }
    for (let y = cy0 + 0.25; y < cy1; y += 0.32) {
      boxGeo(cx1 - 0.01, y - 0.008, g + 0.35, cx1 + 0.01, y + 0.008, g + fh, buckets.paleMesh);
    }
    for (let z = g + 0.65; z < g + fh; z += 0.45) {
      boxGeo(cx0, cy1 - 0.01, z - 0.007, cx1, cy1 + 0.01, z + 0.007, buckets.paleMesh);
      boxGeo(cx1 - 0.01, cy0, z - 0.007, cx1 + 0.01, cy1, z + 0.007, buckets.paleMesh);
    }
    }
    // Basketball hoop support inside court with white backboard, red target square & orange rim (V01, E-01)
    const hoopX = (cx0 + cx1) / 2, hoopY = cy1 - 1.8;
    boxGeo(hoopX - 0.09, hoopY - 0.09, g + 0.08, hoopX + 0.09, hoopY + 0.09, g + 3.55, buckets.houseWhite);
    boxGeo(hoopX - 0.06, hoopY - 0.82, g + 3.25, hoopX + 0.06, hoopY, g + 3.42, buckets.houseWhite);
    boxGeo(hoopX - 0.92, hoopY - 0.88, g + 2.85, hoopX + 0.92, hoopY - 0.80, g + 3.95, buckets.houseWhite);
    boxGeo(hoopX - 0.32, hoopY - 0.89, g + 3.05, hoopX + 0.32, hoopY - 0.79, g + 3.48, buckets.courtRed);
    boxGeo(hoopX - 0.22, hoopY - 0.88, g + 3.12, hoopX + 0.22, hoopY - 0.78, g + 3.41, buckets.houseWhite);
    boxGeo(hoopX - 0.24, hoopY - 1.32, g + 3.02, hoopX + 0.24, hoopY - 0.88, g + 3.06, buckets.terracotta);
    // Round-hooded post-top park lamp beside the basketball court fence (V01)
    const ptX = cx1 - 1.4, ptY = cy1 + 0.55;
    boxGeo(ptX - 0.12, ptY - 0.12, g, ptX + 0.12, ptY + 0.12, g + 0.38, buckets.wallCoping);
    boxGeo(ptX - 0.045, ptY - 0.045, g + 0.38, ptX + 0.045, ptY + 0.045, g + 3.65, buckets.darkFrame);
    if (realistic) {
      turnedGeo([[0,0],[.10,0],[.22,.23],[0,.23]],ptX,ptY,g+3.65,buckets.lampGlow);
      turnedGeo([[0,.30],[.30,.24],[.30,.21],[0,.21]],ptX,ptY,g+3.65,buckets.darkFrame);
    } else {
      boxGeo(ptX - 0.16, ptY - 0.16, g + 3.65, ptX + 0.16, ptY + 0.16, g + 3.88, buckets.lampGlow);
      boxGeo(ptX - 0.28, ptY - 0.28, g + 3.88, ptX + 0.28, ptY + 0.28, g + 3.98, buckets.darkFrame);
    }
    // Substantial screening trees and palms
    for (const t of court.screening_trees_scene || []) {
      trees.push({ species: t.species, x: t.position[0], y: t.position[1], s: t.scale || 1.0 });
    }
    // Court-side light posts
    for (const lt of court.lights_scene || []) {
      const [lx, ly] = lt.position;
      const lh = lt.height_m || 4.2;
      boxGeo(lx - 0.05, ly - 0.05, g, lx + 0.05, ly + 0.05, g + lh, buckets.galvSteel);
      boxGeo(lx - 0.16, ly - 0.16, g + lh, lx + 0.16, ly + 0.16, g + lh + 0.12, buckets.lampGlow);
    }
  }

  // 4. Northwest Electrical Feeder Cabinets, Low Wall, Hedge & Trees (N-02)
  const nwCabs = ctx.northwest_feeder_cabinets;
  if (nwCabs) {
    const [px0, py0, px1, py1] = nwCabs.plinth_bounds_scene;
    boxGeo(px0, py0, g, px1, py1, g + 0.22, buckets.kerbStone);
    // Smaller East cabinet (left in N-02 view looking SW)
    const cSmall = nwCabs.smaller_east_cabinet;
    if (cSmall) {
      const [sx0, sy0, sx1, sy1] = cSmall.bounds_scene;
      const sh = cSmall.size_m[2];
      boxGeo(sx0, sy0, g + 0.22, sx1, sy1, g + 0.22 + sh, buckets.cabinetBody);
      boxGeo(sx0 - 0.02, sy0 - 0.02, g + 0.22 + sh, sx1 + 0.02, sy1 + 0.02, g + 0.28 + sh, buckets.cabinetTrim);
      // Door seam & handle on road-facing (+x) and oblique faces
      const midY = (sy0 + sy1) / 2;
      boxGeo(sx1 - 0.01, midY - 0.012, g + 0.30, sx1 + 0.015, midY + 0.012, g + 0.16 + sh, buckets.cabinetTrim);
      boxGeo(sx0 + 0.04, sy0 + 0.04, g + 0.22, sx1 - 0.04, sy1 - 0.04, g + 0.30, buckets.cabinetTrim);
    }
    // Taller West cabinet (right in N-02 view looking SW)
    const cTall = nwCabs.taller_west_cabinet;
    if (cTall) {
      const [tx0, ty0, tx1, ty1] = cTall.bounds_scene;
      const th = cTall.size_m[2];
      boxGeo(tx0, ty0, g + 0.22, tx1, ty1, g + 0.22 + th, buckets.cabinetBody);
      boxGeo(tx0 - 0.025, ty0 - 0.025, g + 0.22 + th, tx1 + 0.025, ty1 + 0.025, g + 0.29 + th, buckets.cabinetTrim);
      const midY = (ty0 + ty1) / 2;
      boxGeo(tx1 - 0.01, midY - 0.014, g + 0.32, tx1 + 0.018, midY + 0.014, g + 0.16 + th, buckets.cabinetTrim);
      // Louvered vent strips on cabinet doors
      for (const vz of [g + 0.65, g + 0.78, g + 1.35, g + 1.48]) {
        boxGeo(tx1 - 0.008, ty0 + 0.12, vz, tx1 + 0.015, ty1 - 0.12, vz + 0.04, buckets.cabinetTrim);
      }
      boxGeo(tx0 + 0.04, ty0 + 0.04, g + 0.22, tx1 - 0.04, ty1 - 0.04, g + 0.32, buckets.cabinetTrim);
    }
    // Low brown-grey wall & hedge around NW corner
    const [wx0, wy0, wx1, wy1] = nwCabs.low_wall_bounds_scene;
    boxGeo(wx0, wy0, g, wx1, wy1, g + 0.90, buckets.weatheredWall);
    const [hx0, hy0, hx1, hy1] = nwCabs.hedge_bounds_scene;
    for (let y = hy0 + 0.4; y < hy1 - 0.3; y += 0.65) {
      trees.push({ species: 'shrub_round', x: (hx0 + hx1) / 2, y, s: 0.65 });
    }
    for (const t of nwCabs.trees_scene || []) {
      trees.push({ species: t.species, x: t.position[0], y: t.position[1], s: t.scale || 0.85 });
    }
  }

  // 5. North & East Road Streetlight Poles & Horizontally Grooved NE Corner Pier (R09, R11, R13, R14, V02, V04, V05)
  const utils = ctx.north_frontage_utilities;
  if (utils) {
    const pole = utils.streetlight_pole;
    if (pole) {
      const [px, py] = pole.position_scene;
      const ph = pole.height_m || 6.2;
      addStreetLight(px, py, ph, 1.45, 0.0);
    }
    // Additional colony streetlights observed in R09/R13 and V04
    addStreetLight(xmax + 0.55, -0.45, 6.2, 0.95, -0.95);
    addStreetLight(xmax + 0.55, ymax + 7.5, 6.2, 1.45, 0.0);
    addStreetLight(-6.5, -0.45, 6.0, 0.0, -1.35);

    const pillar = utils.ne_reference_pillar;
    if (pillar) {
      const [px0, py0, px1, py1] = pillar.bounds_scene;
      const ph = pillar.height_m || 1.38;
      addGroovedCornerPier(px0, py0, px1, py1, ph);
    }
    // Roadside mixed burgundy/green shrub border along the North & East plot boundary walls (R10, R11, R12, R14, V03, V05)
    if (refined) {
      for (const [x0,y0,x1,y1] of [[xmax+.045,.60,xmax+.70,ymax-.40],[.45,-.68,xmax-3.40,-.045]]) {
        boxGeo(x0,y0,g+.03,x1,y1,g+.045,buckets.plantingSoil);
        const north=(x0>xmax);
        if(north) boxGeo(x1-.025,y0,g+.03,x1,y1,g+.058,buckets.wallCoping);
        else boxGeo(x0,y0,g+.03,x1,y0+.025,g+.058,buckets.wallCoping);
      }
    }
    let plotHedgeIdx = 0;
    for (let y = ymin + 0.8; y < ymax - 0.6; y += refined ? .58 : 1.05) {
      addMixedHedgePoint(xmax + 0.36, y, plotHedgeIdx++);
    }
    for (let x = xmin + 0.8; x < xmax - 3.6; x += refined ? .58 : 1.05) {
      addMixedHedgePoint(x, ymin - 0.36, plotHedgeIdx++);
    }
  }

  // Helper: build an articulated multi-storey colony residence with windows, chajjas, balconies, parapet & boundary wall
  const addArticulatedNeighbour = (bx0, by0, bx1, by1, storeys, bodyBucket, bandBucket, accentBucket) => {
    const hFloor = 3.15;
    const totalH = storeys * hFloor;
    // Plinth & main storeys
    boxGeo(bx0, by0, g, bx1, by1, g + 0.42, buckets.kerbStone);
    for (let s = 0; s < storeys; s++) {
      const z0 = g + 0.42 + s * hFloor, z1 = z0 + hFloor - 0.18;
      boxGeo(bx0, by0, z0, bx1, by1, z1, bodyBucket);
      boxGeo(bx0 - 0.16, by0 - 0.16, z1, bx1 + 0.16, by1 + 0.16, z1 + 0.18, bandBucket);
      // Framed windows & chajja hoods along North (+x), East (-y), and South (-x) faces
      const winZ0 = z0 + 0.82, winZ1 = z0 + 2.25;
      for (const wy of [by0 + 1.8, (by0 + by1) / 2, by1 - 1.8]) {
        if (wy > by0 + 1.0 && wy < by1 - 1.0) {
          boxGeo(bx1 - 0.03, wy - 0.72, winZ0, bx1 + 0.05, wy + 0.72, winZ1, buckets.glass);
          boxGeo(bx1 - 0.05, wy - 0.80, winZ0 - 0.06, bx1 + 0.07, wy + 0.80, winZ0, buckets.darkFrame);
          boxGeo(bx1 - 0.02, wy - 0.92, winZ1, bx1 + 0.38, wy + 0.92, winZ1 + 0.08, bandBucket);
          boxGeo(bx0 - 0.05, wy - 0.72, winZ0, bx0 + 0.03, wy + 0.72, winZ1, buckets.glass);
        }
      }
      for (const wx of [bx0 + 1.8, (bx0 + bx1) / 2, bx1 - 1.8]) {
        if (wx > bx0 + 1.0 && wx < bx1 - 1.0) {
          boxGeo(wx - 0.72, by0 - 0.05, winZ0, wx + 0.72, by0 + 0.03, winZ1, buckets.glass);
          boxGeo(wx - 0.90, by0 - 0.38, winZ1, wx + 0.90, by0 + 0.02, winZ1 + 0.08, bandBucket);
        }
      }
      // Projecting upper-floor balconies on East (-y) and North (+x) sides
      if (s > 0) {
        const balY0 = by0 - 1.15, balY1 = by0;
        boxGeo(bx0 + 1.2, balY0, z0 - 0.18, bx1 - 1.2, balY1, z0 + 0.04, bandBucket);
        boxGeo(bx0 + 1.3, balY0 + 0.08, z0 - 0.22, bx1 - 1.3, balY1 - 0.08, z0 - 0.18, buckets.timberWarm);
        boxGeo(bx0 + 1.24, balY0 + 0.04, z0 + 0.04, bx1 - 1.24, balY0 + 0.09, z0 + 1.02, buckets.glass);
        boxGeo(bx0 + 1.22, balY0 + 0.02, z0 + 1.02, bx1 - 1.22, balY0 + 0.11, z0 + 1.07, buckets.darkFrame);
      }
    }
    // Vertical architectural feature screen / stair tower accent
    boxGeo(bx1 - 2.4, by0 - 0.12, g + 0.42, bx1 - 0.6, by0 + 1.2, g + totalH + 1.15, accentBucket);
    // Roof parapet & pergola beams
    const topZ = g + 0.42 + totalH;
    boxGeo(bx0 - 0.12, by0 - 0.12, topZ, bx1 + 0.12, by0 + 0.12, topZ + 0.85, bandBucket);
    boxGeo(bx0 - 0.12, by1 - 0.12, topZ, bx1 + 0.12, by1 + 0.12, topZ + 0.85, bandBucket);
    boxGeo(bx0 - 0.12, by0 - 0.12, topZ, bx0 + 0.12, by1 + 0.12, topZ + 0.85, bandBucket);
    boxGeo(bx1 - 0.12, by0 - 0.12, topZ, bx1 + 0.12, by1 + 0.12, topZ + 0.85, bandBucket);
  };

  // 6. Articulated South, West & Surrounding Colony Houses (R09, R10, R12, R13, V04)
  const adj = ctx.adjoining_south_and_west;
  if (adj?.vacant) {
    // Owner-confirmed empty neighbouring lots; no speculative house masses.
    for (const key of ['south_vacant_bounds_scene','west_vacant_bounds_scene']) {
      const [x0,y0,x1,y1] = adj[key];
      boxGeo(x0,y0,g-.035,x1,y1,g+.006,buckets.colonyLawn);
      // Fine blades near the house; distant grass uses the same textured ground.
      const near = key.startsWith('south') ? [Math.max(x0,-3.5),y0,x1,Math.min(y1,ymax)] : [x0,y0,x1,Math.min(y1,ymax+3.5)];
      const [a,b,c,d]=near;
      lawnPockets.push({polygon:[[a,b],[c,b],[c,d],[a,d]],holes:[],z:g+.009,heightScale:.30});
    }
    group.userData.vacantAdjoiningLots = 2;
  } else if (adj) {
    // South Adjoining Neighbour: 3-storey (G+2) warm cream/beige residential building observed in R10 & R12
    if (adj.south_neighbour_bounds_scene) {
      const [sx0, sy0, sx1, sy1] = adj.south_neighbour_bounds_scene;
      addArticulatedNeighbour(sx0, sy0, sx1, sy1, 3, buckets.neighbourCream, buckets.neighbourBand, buckets.timberWarm);
      // Low mauve-taupe boundary wall & hedge along East road frontage for South neighbour
      boxGeo(sx0 - 1.2, ymin - 0.05, g, xmin, ymin + 0.18, g + 0.92, buckets.mauveWall);
      boxGeo(sx0 - 1.22, ymin - 0.08, g + 0.92, xmin + 0.02, ymin + 0.21, g + 0.99, buckets.wallCoping);
      for (let x = sx0; x < xmin - 0.5; x += 1.1) {
        addMixedHedgePoint(x, ymin - 0.35, Math.abs(Math.round(x)));
      }
    }
    // West Adjoining Neighbour: 2-storey (G+1) warm ivory/stone colony residence
    if (adj.west_neighbour_bounds_scene) {
      const [wx0, wy0, wx1, wy1] = adj.west_neighbour_bounds_scene;
      addArticulatedNeighbour(wx0, wy0, wx1, wy1, 2, buckets.houseWhite, buckets.neighbourBand, buckets.houseGrey);
      boxGeo(xmax - 0.18, ymax, g, xmax + 0.04, wy1 + 1.2, g + 0.92, buckets.mauveWall);
      boxGeo(xmax - 0.21, ymax - 0.02, g + 0.92, xmax + 0.07, wy1 + 1.22, g + 0.99, buckets.wallCoping);
      for (let y = ymax + 0.8; y < wy1; y += 1.1) {
        addMixedHedgePoint(xmax + 0.35, y, Math.round(y));
      }
    }
  }

  // Additional Colony Street Residences (R09, R13, V04) so every exterior/window sightline has authentic colony depth
  // Northwest across the 12 m North road (west of colony garden, seen in R09/R13/V04)
  addArticulatedNeighbour(25.2, 18.2, 34.0, 28.5, 2, buckets.houseWhite, buckets.houseGrey, buckets.terracotta);
  boxGeo(24.2, 17.2, g, 24.42, 29.5, g + 0.92, buckets.mauveWall);
  boxGeo(24.17, 17.17, g + 0.92, 24.45, 29.53, g + 0.99, buckets.wallCoping);
  addGroovedCornerPier(24.12, 17.05, 24.52, 17.45, 1.32);
  // Southwest colony house (diagonal behind South & West neighbours)
  if (!adj?.vacant) addArticulatedNeighbour(-12.5, 17.5, -2.2, 27.8, 2, buckets.neighbourCream, buckets.neighbourBand, buckets.houseBlueGrey);
  // Further South along the 9 m East road (west side & east side)
  if (!adj?.vacant) addArticulatedNeighbour(-25.5, 1.8, -15.2, 12.6, 2, buckets.houseWhite, buckets.neighbourBand, buckets.timberWarm);
  addArticulatedNeighbour(-14.5, -21.5, -3.5, -10.8, 2, buckets.neighbourCream, buckets.houseWhite, buckets.terracotta);
  // Northeast across the junction (north of basketball court, seen in R09/R13)
  addArticulatedNeighbour(25.4, -22.0, 34.8, -10.8, 3, buckets.houseWhite, buckets.neighbourBand, buckets.houseBlueGrey);
  boxGeo(24.2, -23.0, g, 24.42, -9.2, g + 0.92, buckets.mauveWall);
  boxGeo(24.17, -23.03, g + 0.92, 24.45, -9.17, g + 0.99, buckets.wallCoping);
  addGroovedCornerPier(24.12, -9.45, 24.52, -9.05, 1.35);
  // East background colony residences beyond the basketball court
  // Background setback is illustrative, not a measured neighbour position.
  addArticulatedNeighbour(1.5, realistic ? -57 : -38, 12.5, realistic ? -46.5 : -27.5, 2, buckets.neighbourCream, buckets.neighbourBand, buckets.timberWarm);

  // Street trees along colony avenues (outside the plot)
  trees.push(
    { species: 'neem', x: 24.8, y: 18.0, s: 0.95 },
    { species: 'tree_shade', x: 24.8, y: 25.5, s: 1.05 },
    { species: 'palm', x: 25.0, y: -10.2, s: 1.0 },
    { species: 'neem', x: -13.5, y: 1.2, s: 0.92 },
    { species: 'tree_shade', x: -6.5, y: -10.2, s: 0.95 },
    { species: 'mango', x: -2.0, y: 16.5, s: 0.90 },
  );

  // 7. Existing-Site Plot Representation (for 'Existing plot' vs 'Proposed Tirumala 4' Site Mode Toggle)
  // Reproduces the pre-construction dry red-brown soil, concrete footing blocks (R07), continuous mauve-taupe
  // boundary wall, horizontally grooved NE corner pier (R11, V05), mixed burgundy/green hedge (R10, R12, V03),
  // and pre-construction interior plot trees (R07, R10, R12, V06) without any tree trunks inside Proposed mode.
  boxGeo(xmin, ymin, g, xmax, ymax, g + 0.05, existingBuckets.redEarth);
  boxGeo(xmin + 1.2, ymin + 2.0, g + 0.051, xmax - 1.5, ymax - 2.5, g + 0.065, existingBuckets.colonyLawn);
  // Pre-construction concrete footing blocks scattered on the eastern side (observed in R07)
  for (const [fx, fy, fw, fd] of [
    [4.4, 2.2, 0.55, 0.42], [5.8, 3.1, 0.62, 0.48], [7.2, 2.5, 0.52, 0.44],
    [8.6, 4.2, 0.58, 0.46], [6.3, 5.8, 0.50, 0.40], [9.4, 2.8, 0.54, 0.45],
  ]) {
    boxGeo(fx, fy, g + 0.05, fx + fw, fy + fd, g + 0.24, existingBuckets.footingBlock);
  }
  // Continuous pre-construction North & East boundary wall in muted mauve-taupe with grey coping (R07, R10, R11, R12, V05)
  boxGeo(xmax - 0.22, ymin, g, xmax, ymax, g + 0.92, existingBuckets.mauveWall);
  boxGeo(xmax - 0.25, ymin - 0.02, g + 0.92, xmax + 0.03, ymax + 0.02, g + 0.99, existingBuckets.wallCoping);
  boxGeo(xmin, ymin, g, xmax, ymin + 0.22, g + 0.92, existingBuckets.mauveWall);
  boxGeo(xmin - 0.02, ymin - 0.02, g + 0.92, xmax + 0.02, ymin + 0.25, g + 0.99, existingBuckets.wallCoping);
  addGroovedCornerPier(xmax - 0.34, ymin - 0.10, xmax + 0.10, ymin + 0.34, 1.38, existingBuckets);
  let exHedgeIdx = 0;
  for (let y = ymin + 0.6; y < ymax - 0.4; y += 0.85) {
    addMixedHedgePoint(xmax - 0.45, y, exHedgeIdx++, existingBuckets, existingTrees);
  }
  for (let x = xmin + 0.6; x < xmax - 0.4; x += 0.85) {
    addMixedHedgePoint(x, ymin + 0.45, exHedgeIdx++, existingBuckets, existingTrees);
  }
  existingTrees.push(
    { species: 'palm', x: xmax - 1.4, y: ymin + 1.4, s: 0.98 },
    { species: 'tree_shade', x: xmax - 2.2, y: (ymin + ymax) / 2, s: 0.95 },
    { species: 'neem', x: xmax - 1.8, y: ymax - 2.5, s: 0.90 },
    { species: 'mango', x: (xmin + xmax) / 2, y: (ymin + ymax) / 2 + 1.2, s: 0.92 },
    { species: 'tree_shade', x: xmin + 2.8, y: ymin + 3.2, s: 0.88 },
    { species: 'neem', x: (xmin + xmax) / 2 + 1.4, y: ymin + 3.8, s: 0.85 },
  );

  // Distant horizon foliage ring
  const cx = (xmin + xmax) / 2, cy = (ymin + ymax) / 2;
  const horizonCount=realistic?112:64;
  for (let i = 0; i < horizonCount; i++) {
    const a = (i / horizonCount) * Math.PI * 2 + rnd() * 0.05, r = realistic?54+rnd()*25:68+rnd()*85;
    trees.push({ species: (realistic ? i % 7 === 0 : i % 3 === 0) ? 'palm' : realistic?['tree_shade','neem','mango'][i%3]:'tree_shade',
      x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r, s: 0.95 + rnd() * 0.55, far: true });
  }

  const mats = viewer.materials;
  const customMats = {
    concreteRoad: new THREE.MeshStandardMaterial({ color: '#c4c0b6', roughness: 0.88, metalness: 0.02 }),
    roadJoint: new THREE.MeshStandardMaterial({ color: '#7a7770', roughness: 0.92 }),
    drainSlab: new THREE.MeshStandardMaterial({ color: '#b6b1a5', roughness: 0.86 }),
    drainHole: new THREE.MeshStandardMaterial({ color: '#1f2120', roughness: 0.95 }),
    paverVerge: mats.get('paver') || new THREE.MeshStandardMaterial({ color: '#b5948a', roughness: 0.85 }),
    kerbStone: mats.get('stone') || new THREE.MeshStandardMaterial({ color: '#8f8b82', roughness: 0.84 }),
    colonyLawn: new THREE.MeshStandardMaterial({ color: '#5c7e42', roughness: 0.92 }),
    houseWhite: mats.get('wall') || new THREE.MeshStandardMaterial({ color: '#f1efea', roughness: 0.75 }),
    houseGrey: new THREE.MeshStandardMaterial({ color: '#d7d6d2', roughness: 0.78 }),
    houseBlueGrey: new THREE.MeshStandardMaterial({ color: '#314254', roughness: 0.62, metalness: 0.08 }),
    neighbourCream: new THREE.MeshStandardMaterial({ color: '#dfd2bc', roughness: 0.80 }),
    neighbourBand: new THREE.MeshStandardMaterial({ color: '#c4b49c', roughness: 0.78 }),
    glass: new THREE.MeshPhysicalMaterial({ color: '#7f939e', roughness: 0.05, metalness: 0.82, envMapIntensity: 2.0 }),
    darkFrame: mats.get('frame') || new THREE.MeshStandardMaterial({ color: '#282c30', roughness: 0.45, metalness: 0.4 }),
    timberWarm: mats.get('oak') || mats.get('timber') || new THREE.MeshStandardMaterial({ color: '#7d5434', roughness: 0.55 }),
    potStone: new THREE.MeshStandardMaterial({ color: '#dfd9cc', roughness: 0.72 }),
    terracotta: new THREE.MeshStandardMaterial({ color: '#b66649', roughness: 0.78 }),
    courtSurface: new THREE.MeshStandardMaterial({ color: '#4f7a58', roughness: 0.84 }),
    courtRed: new THREE.MeshStandardMaterial({ color: '#a84c3e', roughness: 0.84 }),
    courtLine: new THREE.MeshStandardMaterial({ color: '#f4f3ee', roughness: 0.72 }),
    paleMesh: new THREE.MeshStandardMaterial({ color: '#d6dbd6', roughness: 0.52, metalness: 0.35 }),
    cabinetBody: new THREE.MeshStandardMaterial({ color: '#dad6cb', roughness: 0.58, metalness: 0.18 }),
    cabinetTrim: new THREE.MeshStandardMaterial({ color: '#5a5d5e', roughness: 0.50, metalness: 0.45 }),
    weatheredWall: new THREE.MeshStandardMaterial({ color: '#8e7e85', roughness: 0.88 }),
    mauveWall: new THREE.MeshStandardMaterial({ color: '#8e7e85', roughness: 0.86 }),
    mauveGroove: new THREE.MeshStandardMaterial({ color: '#6b5c63', roughness: 0.90 }),
    wallCoping: new THREE.MeshStandardMaterial({ color: '#c8c4bc', roughness: 0.80 }),
    burgundyShrub: new THREE.MeshStandardMaterial({ color: '#782934', roughness: 0.88 }),
    whiteBlossom: new THREE.MeshStandardMaterial({ color: '#f7f5ee', roughness: 0.75 }),
    redEarth: new THREE.MeshStandardMaterial({ color: '#84563c', roughness: 0.94 }),
    footingBlock: new THREE.MeshStandardMaterial({ color: '#b8b3a8', roughness: 0.88 }),
    pillarCap: new THREE.MeshStandardMaterial({ color: '#c8c4bc', roughness: 0.78 }),
    galvSteel: new THREE.MeshStandardMaterial({ color: '#aeb5ba', roughness: 0.38, metalness: 0.65 }),
    lampGlow: mats.get('lamp') || new THREE.MeshStandardMaterial({ color: '#fff3d1', emissive: '#ffcf87', emissiveIntensity: 1.6, roughness: 0.2 }),
  };

  if (refined) {
    customMats.plantingSoil=mats.get('t4-mulch');
    const replacements={concreteRoad:'t4-colony-road',paverVerge:'t4-colony-paving',
      colonyLawn:'t4-colony-turf',mauveWall:'t4-colony-wall',weatheredWall:'t4-colony-wall',
      wallCoping:'t4-boundary-coping'};
    for (const [key,name] of Object.entries(replacements)) {
      const old=customMats[key];
      if (![...mats.cache.values()].includes(old)) old.dispose();
      customMats[key]=mats.get(name);
    }
  }

  if (realistic) {
    customMats.timberWarm=mats.get('t4-garden-timber');
    customMats.terracotta.dispose();
    customMats.terracotta=mats.get('t4-garden-urn');
    customMats.glass.color.set('#71817e');
    customMats.glass.metalness=.28;
    customMats.glass.roughness=.16;
    customMats.glass.envMapIntensity=1.1;
    customMats.courtSurface.color.set('#658181');
    customMats.lampGlow=mats.get('wall'); // Daytime park lenses must not glow like lamps.
  }

  const created = [];
  for (const f of meshFaces) {
    const geo=new THREE.PlaneGeometry(f.w,f.h);
    const uv=geo.attributes.uv;
    for(let i=0;i<uv.count;i++) uv.setXY(i,uv.getX(i)*f.w,uv.getY(i)*f.h);
    geo.rotateY(f.turn);
    geo.translate(f.x,f.z+f.h/2,-f.y);
    const mesh=new THREE.Mesh(geo,mats.get('t4-chainlink'));
    mesh.name='colony-fine-diamond-chainlink'; mesh.receiveShadow=true;
    group.add(mesh); created.push(mesh);
  }
  group.userData.realismRefinement = realistic ? {fineMeshFaces:meshFaces.length, referenceGarden:true} : null;
  group.userData.walkSurfaces = [];
  for (const [name, out] of Object.entries(buckets)) {
    if (!out.pos.length) continue;
    const mesh = new THREE.Mesh(geometry(out), customMats[name]);
    mesh.name = 'colony-' + name;
    // Match walking support to the visible road and verge at the exterior spawn.
    if (['concreteRoad', 'paverVerge', 'kerbStone', 'colonyLawn', 'courtSurface'].includes(name)) {
      group.userData.walkSurfaces.push(mesh.geometry);
    }
    mesh.castShadow = name !== 'glass' && name !== 'concreteRoad' && name !== 'colonyLawn';
    mesh.receiveShadow = true;
    group.add(mesh);
    created.push(mesh);
  }

  const existingPlotGroup = new THREE.Group();
  existingPlotGroup.name = 'existing-plot-context';
  existingPlotGroup.visible = false;
  for (const [name, out] of Object.entries(existingBuckets)) {
    if (!out.pos.length) continue;
    const mesh = new THREE.Mesh(geometry(out), customMats[name]);
    mesh.name = 'colony-' + name;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    existingPlotGroup.add(mesh);
    created.push(mesh);
  }
  group.add(existingPlotGroup);
  group.userData.existingPlotGroup = existingPlotGroup;

  const veg = viewer.vegetation;
  const instantiateTrees = (treeList, targetGroup, seedOffset) => {
    if (!veg || !veg.materials) return;
    const bySpecies = new Map();
    for (const [i,t] of treeList.entries()) {
      const key=refined ? `${t.species}|${i%3}|${JSON.stringify(t.opts||{})}` : t.species;
      if (!bySpecies.has(key)) bySpecies.set(key, []);
      bySpecies.get(key).push(t);
    }
    for (const [key, list] of bySpecies) {
      const species=list[0].species;
      const variant=refined ? Number(key.split('|')[1]) : 0;
      const spec = buildSpecies(species, seedOffset + species.length + variant*137, list[0].opts||{});
      for (const [part, geo] of Object.entries(spec.parts)) {
        if (!geo || (!refined && part === 'flowers')) continue;
        const mesh = new THREE.InstancedMesh(geo, veg.partMaterial(part, spec), list.length);
        const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0);
        list.forEach((t, i) => {
          q.setFromAxisAngle(up, (i * 1.618 + seedOffset) % (Math.PI * 2));
          const st=t.stretch||[1,1,1];
          m.compose(s2t(t.x, t.y, t.z ?? g), q, new THREE.Vector3(t.s*st[0], t.s*st[1], t.s*st[2]));
          mesh.setMatrixAt(i, m);
        });
        mesh.instanceMatrix.needsUpdate = true;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.computeBoundingSphere();
        targetGroup.add(mesh);
        created.push(mesh);
        veg.geometries.push(geo);
      }
    }
  };
  instantiateTrees(trees, group, 901);
  instantiateTrees(existingTrees, existingPlotGroup, 977);
  if (refined && veg) {
    const lawn=buildLawn(lawnPockets, 1.3, veg.uniforms, '#63854e');
    if(lawn) { group.add(lawn); created.push(lawn); }
    group.userData.exteriorRefinement = {solidRedHedgeBlocks:0, grassPockets:lawnPockets.length};
  }


  group.userData.dispose = () => {
    for (const m of created) {
      if (m.geometry) m.geometry.dispose();
      if (m.name==='lawn-grass') m.material.dispose();
    }
    for (const m of Object.values(customMats)) if (m && m.dispose && ![...mats.cache.values()].includes(m)) m.dispose();
  };
  return group;
}
