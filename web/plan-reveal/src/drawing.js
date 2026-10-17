// Drawing buffers. The same model is rendered once more with a plain material into a normals + depth target, and the
// sheet's annotations (wall poché at the cut, door swings, tags, dimension chains, grid, levels) are laid onto that
// target as ink: they multiply its alpha, so 1 - alpha is how much ink a pixel carries. The composite turns this
// into the ink-on-paper drawing wherever the visitor has not arrived yet.
import * as THREE from 'three';

const s2t = (x, y, z) => new THREE.Vector3(x, z, -y); // scene (Z-up) -> three (Y-up)
export const DRAW_LAYER = 2;

export function gbufferMaterial(clipPlane) {
  return new THREE.ShaderMaterial({
    name: 'reveal-gbuffer',
    side: THREE.DoubleSide,
    clipping: true,
    clippingPlanes: [clipPlane],
    vertexShader: /* glsl */`
      #include <common>
      #include <clipping_planes_pars_vertex>
      varying vec3 vN;
      void main() {
        #include <begin_vertex>
        #include <project_vertex>
        #include <clipping_planes_vertex>
        vN = normalize(normalMatrix * normal);
      }`,
    fragmentShader: /* glsl */`
      #include <clipping_planes_pars_fragment>
      varying vec3 vN;
      void main() {
        #include <clipping_planes_fragment>
        vec3 n = normalize(vN) * (gl_FrontFacing ? 1. : -1.);
        gl_FragColor = vec4(n * .5 + .5, 1.);
      }`,
  });
}

// Ink multiplies the target's alpha and leaves its normals alone.
function inkBlend(m) {
  Object.assign(m, { transparent: true, depthWrite: false, blending: THREE.CustomBlending, blendEquation: THREE.AddEquation,
    blendSrc: THREE.ZeroFactor, blendDst: THREE.OneFactor, blendEquationAlpha: THREE.AddEquation,
    blendSrcAlpha: THREE.ZeroFactor, blendDstAlpha: THREE.OneMinusSrcAlphaFactor, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -8 });
  return m;
}

function fillMaterial(opacity) {
  return inkBlend(new THREE.ShaderMaterial({
    uniforms: { uInk: { value: 1 }, uOpacity: { value: opacity } },
    vertexShader: 'void main(){ gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
    fragmentShader: 'uniform float uInk; uniform float uOpacity; void main(){ gl_FragColor = vec4(0., 0., 0., uInk * uOpacity); }',
    side: THREE.DoubleSide,
  }));
}

// Lines with a constant on-screen width, trimmed at the near plane, anti-aliased, optionally dashed (in metres).
const LINE_VERT = /* glsl */`
attribute vec3 aA;
attribute vec3 aB;
attribute vec4 aStyle;     // width (px), ink, dash period (m), dash duty
uniform vec2 uViewport;
uniform float uPixel;
uniform float uNear;
varying float vSide;
varying float vHalf;
varying float vAlong;
varying vec4 vStyle;
void main() {
  vec4 pa = modelViewMatrix * vec4(aA, 1.), pb = modelViewMatrix * vec4(aB, 1.);
  if (pa.z > -uNear && pb.z > -uNear) { gl_Position = vec4(2., 2., 2., 1.); return; }
  float cross = (pa.z + uNear) / (pa.z - pb.z + 1e-9);
  float t0 = pa.z > -uNear ? cross : 0., t1 = pb.z > -uNear ? cross : 1.;
  vec4 va = mix(pa, pb, t0), vb = mix(pa, pb, t1);
  vec4 ca = projectionMatrix * va, cb = projectionMatrix * vb;
  vec2 sa = ca.xy / ca.w * .5 * uViewport, sb = cb.xy / cb.w * .5 * uViewport;
  vec2 dir = sb - sa; float sl = length(dir); dir = sl > 1e-5 ? dir / sl : vec2(1., 0.);
  vec2 nrm = vec2(-dir.y, dir.x);
  float hw = max(aStyle.x * uPixel, .6) * .5 + .75;
  vec4 c = mix(ca, cb, position.x);
  vec2 off = nrm * position.y * hw + dir * (position.x * 2. - 1.) * .75;
  c.xy += off / (.5 * uViewport) * c.w;
  gl_Position = c;
  float len = distance(aA, aB);
  vSide = position.y * hw; vHalf = hw - .75; vAlong = mix(t0, t1, position.x) * len; vStyle = aStyle;
}`;

const LINE_FRAG = /* glsl */`
uniform float uInk;
varying float vSide;
varying float vHalf;
varying float vAlong;
varying vec4 vStyle;
void main() {
  float cover = clamp(vHalf + .5 - abs(vSide), 0., 1.);
  if (vStyle.z > 0.) {
    float ph = fract(vAlong / vStyle.z), w = fwidth(vAlong / vStyle.z) + 1e-4;
    cover *= smoothstep(vStyle.w + w, vStyle.w - w, ph);
  }
  gl_FragColor = vec4(0., 0., 0., cover * vStyle.y * uInk);
}`;

const STYLE = {  // px width, ink, dash period, duty
  'ink-heavy': [2.1, .95], 'ink-medium': [1.35, .9], 'ink-fine': [.95, .82],
  'light-heavy': [1.5, .5], 'light-medium': [1.1, .45], 'light-fine': [.85, .4],
  'accent-heavy': [1.9, .8], 'accent-medium': [1.3, .7], 'accent-fine': [.95, .6],
  'glass-heavy': [1.4, .6], 'glass-medium': [1.1, .55], 'glass-fine': [.9, .5],
};

function lineMesh(segments, z) {
  const base = new THREE.InstancedBufferGeometry();
  base.setAttribute('position', new THREE.Float32BufferAttribute([0, -1, 0, 1, -1, 0, 1, 1, 0, 0, 1, 0], 3));
  base.setIndex([0, 1, 2, 0, 2, 3]);
  const n = segments.length, A = new Float32Array(n * 3), B = new Float32Array(n * 3), S = new Float32Array(n * 4);
  segments.forEach(([x0, y0, x1, y1, st], i) => {
    const a = s2t(x0, y0, z), b = s2t(x1, y1, z);
    A.set([a.x, a.y, a.z], i * 3); B.set([b.x, b.y, b.z], i * 3); S.set(st, i * 4);
  });
  base.setAttribute('aA', new THREE.InstancedBufferAttribute(A, 3));
  base.setAttribute('aB', new THREE.InstancedBufferAttribute(B, 3));
  base.setAttribute('aStyle', new THREE.InstancedBufferAttribute(S, 4));
  base.instanceCount = n;
  const material = inkBlend(new THREE.ShaderMaterial({
    uniforms: { uViewport: { value: new THREE.Vector2(1, 1) }, uPixel: { value: 1 }, uNear: { value: .05 }, uInk: { value: 1 } },
    vertexShader: LINE_VERT, fragmentShader: LINE_FRAG, side: THREE.DoubleSide,
  }));
  const mesh = new THREE.Mesh(base, material);
  mesh.frustumCulled = false;
  return mesh;
}

// Text: one atlas per sheet, a quad per label anchored like the CAD text (baseline point, start/middle/end, rotation).
function textLayer(texts, z, { font = '"Reveal Mono", "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace', pxPerM = 230, weight = 500 } = {}) {
  if (!texts.length) return null;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const pad = 6, W = 2048;
  const items = texts.map(([x, y, text, size, anchor, rot]) => {
    const px = Math.max(14, Math.round(size * pxPerM));
    ctx.font = `${weight} ${px}px ${font}`;
    const m = ctx.measureText(text);
    return { x, y, text, size, anchor, rot, px, w: Math.ceil(m.width) + pad * 2, h: Math.ceil(px * 1.32) + pad * 2 };
  });
  let cx = 0, cy = 0, row = 0;
  for (const it of items) {
    if (cx + it.w > W) { cx = 0; cy += row; row = 0; }
    it.u = cx; it.v = cy; cx += it.w; row = Math.max(row, it.h);
  }
  const H = Math.min(8192, THREE.MathUtils.ceilPowerOfTwo(Math.max(64, cy + row)));
  canvas.width = W; canvas.height = H;
  ctx.fillStyle = 'rgba(0,0,0,0)'; ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#fff'; ctx.textBaseline = 'alphabetic';
  for (const it of items) {
    ctx.font = `${weight} ${it.px}px ${font}`;
    ctx.fillText(it.text, it.u + pad, it.v + pad + it.px);
  }
  const pos = [], uv = [], idx = [];
  for (const it of items) {
    const wM = (it.w - pad * 2) / it.px * it.size, ascent = it.size * 1.0, descent = it.size * .32, padM = pad / it.px * it.size;
    const shift = it.anchor === 'middle' ? -wM / 2 : it.anchor === 'end' ? -wM : 0;
    const r = THREE.MathUtils.degToRad(it.rot || 0), ux = Math.cos(r), uy = Math.sin(r), vx = -uy, vy = ux;
    const corner = (a, b) => s2t(it.x + ux * a + vx * b, it.y + uy * a + vy * b, z);
    const x0 = shift - padM, x1 = shift + wM + padM, y0 = -descent - padM, y1 = ascent + padM;
    const k = pos.length / 3;
    for (const p of [corner(x0, y0), corner(x1, y0), corner(x1, y1), corner(x0, y1)]) pos.push(p.x, p.y, p.z);
    const u0 = it.u / W, u1 = (it.u + it.w) / W;
    const vb = 1 - (it.v + pad + it.px + descent / it.size * it.px + pad) / H, vt = 1 - (it.v + pad + it.px - ascent / it.size * it.px - pad) / H;
    uv.push(u0, vb, u1, vb, u1, vt, u0, vt);
    idx.push(k, k + 1, k + 2, k, k + 2, k + 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  const tex = new THREE.CanvasTexture(canvas);
  tex.anisotropy = 8; tex.generateMipmaps = true; tex.minFilter = THREE.LinearMipmapLinearFilter;
  const material = inkBlend(new THREE.ShaderMaterial({
    uniforms: { tText: { value: tex }, uInk: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
    fragmentShader: 'uniform sampler2D tText; uniform float uInk; varying vec2 vUv; void main(){ float a = texture2D(tText, vUv).a; gl_FragColor = vec4(0., 0., 0., a * .92 * uInk); }',
    side: THREE.DoubleSide,
  }));
  const mesh = new THREE.Mesh(g, material);
  mesh.frustumCulled = false;
  return mesh;
}

function polygonGeometry(polys, z) {
  const geoms = [];
  for (const pts of polys) {
    if (pts.length < 3) continue;
    const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)));
    const g = new THREE.ShapeGeometry(shape);
    g.rotateX(-Math.PI / 2);  // shape XY -> three XZ with z = -y
    g.translate(0, z, 0);
    geoms.push(g);
  }
  if (!geoms.length) return null;
  const merged = mergeGeometries(geoms);
  geoms.forEach((g) => g.dispose());
  return merged;
}

function mergeGeometries(list) {
  let n = 0, m = 0;
  for (const g of list) { n += g.attributes.position.count; m += g.index ? g.index.count : g.attributes.position.count; }
  const pos = new Float32Array(n * 3), idx = new Uint32Array(m);
  let o = 0, k = 0;
  for (const g of list) {
    pos.set(g.attributes.position.array, o * 3);
    const src = g.index ? g.index.array : [...Array(g.attributes.position.count).keys()];
    for (let i = 0; i < src.length; i++) idx[k + i] = src[i] + o;
    o += g.attributes.position.count; k += src.length;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  out.setIndex(new THREE.BufferAttribute(idx, 1));
  return out;
}

// Room names large on the floor, along the room's long side, for the walk: the drawing state of a room you have not
// entered yet carries its name and size like a stencil on the slab.
function floorLabels(rooms, level) {
  const texts = [];
  for (const r of rooms) {
    if (['stair', 'stair-landing', 'void', 'lift-shaft'].includes(r.kind) || r.area < 3) continue;
    const [w, d] = r.size, along = w >= d ? 0 : 90, long = Math.max(w, d);
    const name = r.name.split('·')[0].trim().toUpperCase();
    const size = Math.max(.16, Math.min(.42, long / Math.max(8, name.length * 1.15)));
    const [x, y] = r.label, rad = THREE.MathUtils.degToRad(along), vx = -Math.sin(rad), vy = Math.cos(rad);
    texts.push([x + vx * size * .25, y + vy * size * .25, name, size, 'middle', along]);
    texts.push([x - vx * size * .95, y - vy * size * .95, `${r.area.toFixed(0)} m²   ${r.size[0].toFixed(2)} × ${r.size[1].toFixed(2)}`, size * .42, 'middle', along]);
  }
  return textLayer(texts, level + .006, { pxPerM: 260, weight: 400 });
}

export class Drawing {
  constructor(data) {
    this.scene = new THREE.Scene();
    this.sheets = new Map();
    this.cutNodes = [];
    this.lineMeshes = [];
    for (const sheet of data.sheets) {
      const level = sheet.level, group = new THREE.Group();
      group.name = `sheet-${sheet.floor}`;
      // Poché caps ride on the cut plane; every other layer lies on the finished floor.
      const poche = polygonGeometry(sheet.poche, 0);
      let cap = null;
      if (poche) { cap = new THREE.Mesh(poche, fillMaterial(1)); cap.frustumCulled = false; group.add(cap); }
      const fills = polygonGeometry(sheet.fills.filter((f) => f.tone >= .5).map((f) => f.points), level + .01);
      if (fills) group.add(new THREE.Mesh(fills, fillMaterial(1)));
      const tints = polygonGeometry(sheet.fills.filter((f) => f.tone < .5).map((f) => f.points), level + .009);
      if (tints) group.add(new THREE.Mesh(tints, fillMaterial(.16)));
      const segments = [];
      for (const [style, flat] of Object.entries(sheet.lines)) {
        const key = style.replace('-dash', ''), [w, ink] = STYLE[key] || [1, .8], dash = style.endsWith('-dash');
        for (let i = 0; i < flat.length; i += 4) segments.push([flat[i], flat[i + 1], flat[i + 2], flat[i + 3], [w, ink, dash ? .2 : 0, .62]]);
      }
      if (segments.length) { const lines = lineMesh(segments, level + .012); group.add(lines); this.lineMeshes.push(lines); }
      const text = textLayer(sheet.texts, level + .013);
      if (text) group.add(text);
      const labels = floorLabels(data.rooms.filter((r) => r.floor === sheet.floor), level);
      if (labels) { labels.material.uniforms.uInk.value = 0; group.add(labels); }
      group.traverse((o) => o.layers.set(DRAW_LAYER));
      this.scene.add(group);
      this.sheets.set(sheet.floor, { group, cap, labels, level, text });
    }
  }

  // Only the storey being shown is annotated: the upper floor's tags, dimensions and north point never print over
  // the ground floor's plan.
  setFloor(floor) {
    if (floor === this.floor) return;
    this.floor = floor;
    for (const [f, s] of this.sheets) s.group.visible = f === floor;
  }

  // The cut height (three Y) the poché caps sit at; caps of floors cut above their own storey are hidden.
  setCut(y, floorH) {
    for (const [floor, s] of this.sheets) {
      if (!s.cap) continue;
      const top = s.level + floorH - .2;
      s.cap.visible = y > s.level + .3 && y < top;
      s.cap.position.y = y;
    }
  }

  // How much of each layer shows: the CAD sheet (tags, dims, grid) and the large floor names for the walk.
  setInk(sheetInk, labelInk) {
    for (const s of this.sheets.values()) {
      s.group.traverse((o) => { if (o.material?.uniforms?.uInk && o !== s.labels && o !== s.cap) o.material.uniforms.uInk.value = sheetInk; });
      if (s.labels) s.labels.material.uniforms.uInk.value = labelInk;
    }
  }

  setViewport(w, h, pixel, near) {
    for (const m of this.lineMeshes) {
      m.material.uniforms.uViewport.value.set(w, h);
      m.material.uniforms.uPixel.value = pixel;
      m.material.uniforms.uNear.value = near;
    }
  }
}
