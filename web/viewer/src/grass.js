// Instanced lawn grass: curved tapered blades in clumps, scattered only inside generated lawn polygons.
import * as THREE from 'three';
import { mulberry32, pointInPolygon, polygonArea, polygonBounds } from './util.js';

function clumpGeometry(baseColor) {
  const rnd = mulberry32(4242);
  const pos = [], col = [], nor = [], sway = [], idx = [];
  const base = new THREE.Color(baseColor || '#5b7a36');
  const dark = base.clone().multiplyScalar(.45), tipCol = base.clone().lerp(new THREE.Color('#c9c77e'), .35);
  const blades = 10;
  for (let b = 0; b < blades; b++) {
    const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * .075;
    const ox = Math.cos(a) * r, oz = Math.sin(a) * r;
    const h = .07 + rnd() * .09;
    const w = .0045 + rnd() * .003;
    const lean = rnd() * Math.PI * 2, bend = .2 + rnd() * .55;
    const facing = rnd() * Math.PI;
    const sx = Math.cos(facing), sz = Math.sin(facing);
    const lx = Math.cos(lean), lz = Math.sin(lean);
    const rows = [0, .35, .7, 1];
    const start = pos.length / 3;
    const tint = .85 + rnd() * .3;
    rows.forEach((t, k) => {
      const y = h * t, off = bend * h * t * t;
      const cx = ox + lx * off, cz = oz + lz * off;
      const ww = w * (1 - Math.pow(t, 1.4));
      const c = dark.clone().lerp(base, Math.min(1, t * 1.6)).lerp(tipCol, Math.max(0, t - .55) * 1.4).multiplyScalar(tint);
      const n = [lx * .25, .95, lz * .25];
      if (k < rows.length - 1) {
        pos.push(cx - sx * ww, y, cz - sz * ww, cx + sx * ww, y, cz + sz * ww);
        col.push(c.r, c.g, c.b, c.r, c.g, c.b); nor.push(...n, ...n); sway.push(t * t, t * t);
      } else { pos.push(cx, y, cz); col.push(c.r, c.g, c.b); nor.push(...n); sway.push(1); }
    });
    // rows: 0:(s,s+1) 1:(s+2,s+3) 2:(s+4,s+5) tip: s+6
    for (let k = 0; k < 2; k++) { const a0 = start + k * 2; idx.push(a0, a0 + 1, a0 + 3, a0, a0 + 3, a0 + 2); }
    idx.push(start + 4, start + 5, start + 6);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setAttribute('aSway', new THREE.Float32BufferAttribute(sway, 1));
  g.setIndex(idx);
  return g;
}

export function buildLawn(lawns, density, uniforms, baseColor) {
  const perM2 = 70 * density;
  const rnd = mulberry32(90210);
  const points = [];
  for (const lawn of lawns) {
    const poly = lawn.polygon;
    if (!poly || poly.length < 3) continue;
    const holes = lawn.holes || [];
    const area = polygonArea(poly) - holes.reduce((s, h) => s + polygonArea(h), 0);
    const n = Math.min(60000, Math.round(area * perM2));
    const [x0, y0, x1, y1] = polygonBounds(poly);
    let tries = 0;
    for (let i = 0; i < n && tries < n * 4; tries++) {
      const x = x0 + rnd() * (x1 - x0), y = y0 + rnd() * (y1 - y0);
      if (!pointInPolygon(x, y, poly) || holes.some((h) => pointInPolygon(x, y, h))) continue;
      points.push([x, y, lawn.z ?? 0, Math.max(.2, Math.min(2, lawn.heightScale ?? 1))]);
      i++;
    }
  }
  if (!points.length) return null;
  const geo = clumpGeometry(baseColor);
  const material = new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: .82, metalness: 0 });
  material.name = 'plant-foliage-lawn';
  const local = { ffFadeNear: { value: 14 }, ffFadeFar: { value: 30 } };
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms, local);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
attribute float aSway;
uniform float ffTime; uniform float ffWind; uniform float ffFadeNear; uniform float ffFadeFar;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
{
  vec3 ffI = (modelMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
  float fade = 1.0 - smoothstep(ffFadeNear, ffFadeFar, distance(cameraPosition, ffI));
  float ph = ffTime * 1.6 + ffI.x * .8 + ffI.z * .6;
  float s = aSway * ffWind * (.7 + .3 * sin(ffTime * .4 + ffI.x * .1));
  transformed.x += (sin(ph) * .018 + sin(ffTime * 7.0 + ffI.z * 5.0) * .004) * s;
  transformed.z += cos(ph * .9) * .014 * s;
  transformed.y *= fade;
}`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <normal_fragment_begin>', THREE.ShaderChunk.normal_fragment_begin.replace('normal *= faceDirection;', ''));
  };
  material.customProgramCacheKey = () => 'ff-lawn';
  const mesh = new THREE.InstancedMesh(geo, material, points.length);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  const c = new THREE.Color();
  points.forEach(([x, y, z, heightScale], i) => {
    q.setFromAxisAngle(up, rnd() * Math.PI * 2);
    const k = .75 + rnd() * .6;
    s.set(k, k * (.8 + rnd() * .5) * heightScale, k);
    p.set(x, z, -y);
    m.compose(p, q, s);
    mesh.setMatrixAt(i, m);
    const v = .82 + rnd() * .3;
    c.setRGB(v * (.96 + rnd() * .1), v, v * (.9 + rnd() * .12));
    mesh.setColorAt(i, c);
  });
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  mesh.castShadow = false;
  mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  mesh.name = 'lawn-grass';
  mesh.userData.update = (camera) => {
    // Walk mode keeps blades out to ~30 m; distant orbit views rely on the lawn texture.
    const d = camera.position.y;
    local.ffFadeNear.value = d > 12 ? 6 : 14;
    local.ffFadeFar.value = d > 12 ? 14 : 30;
  };
  return mesh;
}
