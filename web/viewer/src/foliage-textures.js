// Canvas-painted foliage atlases (alpha-tested leaf cards). Deterministic, no bitmaps shipped.
import * as THREE from 'three';
import { mulberry32 } from './util.js';

function canvas(size) {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(size, size);
  const c = document.createElement('canvas'); c.width = size; c.height = size; return c;
}

// Alpha-tested cards are filtered and mipmapped in straight colour, so the clear texels around a painted leaf
// must carry the leaf's own colour: a canvas stores them black, which darkens or lightens edges and tips once
// filtered. Push-pull fill (power-of-two size): average the solid texels down a pyramid, then give every clear
// texel the mean colour of the finest level that has any. Alpha is left as painted.
export function bleedColour(px, size) {
  const levels = [];
  let n = size, w = new Float32Array(n * n), c = new Float32Array(n * n * 3);
  for (let i = 0; i < n * n; i++) {
    if (px[i * 4 + 3] < 128) continue;
    w[i] = 1; c[i * 3] = px[i * 4]; c[i * 3 + 1] = px[i * 4 + 1]; c[i * 3 + 2] = px[i * 4 + 2];
  }
  levels.push({ n, w, c });
  while (n > 1) {
    const m = n >> 1, w2 = new Float32Array(m * m), c2 = new Float32Array(m * m * 3);
    for (let y = 0; y < m; y++) for (let x = 0; x < m; x++) {
      const o = y * m + x;
      for (const s of [2 * y * n + 2 * x, 2 * y * n + 2 * x + 1, (2 * y + 1) * n + 2 * x, (2 * y + 1) * n + 2 * x + 1]) {
        w2[o] += w[s]; c2[o * 3] += c[s * 3]; c2[o * 3 + 1] += c[s * 3 + 1]; c2[o * 3 + 2] += c[s * 3 + 2];
      }
    }
    levels.push({ n: m, w: w2, c: c2 });
    n = m; w = w2; c = c2;
  }
  for (let k = levels.length - 1; k >= 0; k--) {
    const { n, w, c } = levels[k], up = levels[k + 1];
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const o = y * n + x;
      if (w[o] > 0) { for (let j = 0; j < 3; j++) c[o * 3 + j] /= w[o]; continue; }
      if (!up) continue;
      const q = ((y >> 1) * up.n + (x >> 1)) * 3;
      c[o * 3] = up.c[q]; c[o * 3 + 1] = up.c[q + 1]; c[o * 3 + 2] = up.c[q + 2];
    }
  }
  const c0 = levels[0].c;
  for (let i = 0; i < size * size; i++) {
    if (px[i * 4 + 3] >= 128) continue;
    px[i * 4] = Math.round(c0[i * 3]); px[i * 4 + 1] = Math.round(c0[i * 3 + 1]); px[i * 4 + 2] = Math.round(c0[i * 3 + 2]);
  }
  return px;
}

function toTexture(cv, anisotropy, bleed = false) {
  let t;
  if (bleed) {
    // Straight-colour pixels with the leaf colour bled outwards; a canvas upload would drop it again.
    const image = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height);
    bleedColour(image.data, cv.width);
    t = new THREE.DataTexture(new Uint8Array(image.data.buffer), cv.width, cv.height, THREE.RGBAFormat);
    t.magFilter = THREE.LinearFilter;
  } else t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = anisotropy;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true;
  // Atlas convention: canvas row 0 is v = 0 and every cell is painted base-at-top, tip downward.
  t.flipY = false;
  t.needsUpdate = true;
  return t;
}

const hsl = (h, s, l, a = 1) => `hsla(${h},${s}%,${l}%,${a})`;

// A pointed-oval leaf path centred on the origin, tip at +y.
function leafPath(ctx, len, width, pointy = .55) {
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.bezierCurveTo(width * .9, len * .2, width * (1 - pointy * .3), len * .75, 0, len);
  ctx.bezierCurveTo(-width * (1 - pointy * .3), len * .75, -width * .9, len * .2, 0, 0);
  ctx.closePath();
}

function drawLeaf(ctx, rnd, { x, y, angle, len, width, hue, sat, light, vein = true, pointy = .55, gloss = .15 }) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  leafPath(ctx, len, width, pointy);
  const g = ctx.createLinearGradient(-width, 0, width, len * .2);
  g.addColorStop(0, hsl(hue, sat, light - 6));
  g.addColorStop(.5, hsl(hue + 2, sat + 4, light + 3));
  g.addColorStop(1, hsl(hue - 3, sat, light - 9));
  ctx.fillStyle = g;
  ctx.fill();
  // Soft specular sheen on one half.
  ctx.globalAlpha = gloss;
  ctx.fillStyle = hsl(hue + 10, 30, light + 30);
  ctx.beginPath();
  ctx.ellipse(width * .25, len * .45, width * .3, len * .3, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 1;
  if (vein) {
    ctx.strokeStyle = hsl(hue + 8, sat - 10, light + 14, .55);
    ctx.lineWidth = Math.max(1, width * .06);
    ctx.beginPath(); ctx.moveTo(0, len * .03); ctx.lineTo(0, len * .95); ctx.stroke();
    ctx.lineWidth = Math.max(.6, width * .025);
    for (let i = 1; i < 7; i++) {
      const t = i / 7, w = width * Math.sin(t * Math.PI) * .85;
      ctx.beginPath(); ctx.moveTo(0, len * t); ctx.quadraticCurveTo(w * .5, len * (t + .03), w, len * (t + .1)); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, len * t); ctx.quadraticCurveTo(-w * .5, len * (t + .03), -w, len * (t + .1)); ctx.stroke();
    }
  }
  ctx.restore();
}

// 2x2 atlas of small-leaf clusters (shrubs, hedges, tree canopies). Cell 3 = conifer sprig.
function clusterAtlas(size, palette) {
  const cv = canvas(size); const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, size, size);
  const cell = size / 2;
  const rnd = mulberry32(1234 + palette.seed);
  for (let c = 0; c < 4; c++) {
    const ox = (c % 2) * cell, oy = Math.floor(c / 2) * cell;
    ctx.save();
    ctx.beginPath(); ctx.rect(ox, oy, cell, cell); ctx.clip();
    ctx.translate(ox + cell / 2, oy + cell / 2);
    if (c === 3 && palette.conifer) {
      // Conifer sprig: dense feathery scale-leaves on branching twigs.
      for (let b = 0; b < 9; b++) {
        const a = -Math.PI / 2 + (b - 4) * .32 + (rnd() - .5) * .2;
        const L = cell * (.28 + rnd() * .16);
        for (let k = 0; k < 40; k++) {
          const t = k / 40, r = L * t;
          const px = Math.cos(a) * r, py = Math.sin(a) * r;
          const w = (1 - t) * cell * .05 + 2;
          ctx.fillStyle = hsl(palette.hue + rnd() * 10 - 5, palette.sat, palette.light - 8 + rnd() * 14);
          ctx.beginPath(); ctx.ellipse(px, py, w, w * 1.7, a, 0, Math.PI * 2); ctx.fill();
        }
      }
    } else {
      const n = palette.count || 70;
      for (let i = 0; i < n; i++) {
        const r = Math.sqrt(rnd()) * cell * .38;
        const th = rnd() * Math.PI * 2;
        const len = cell * (palette.leafLen || .16) * (.65 + rnd() * .6);
        drawLeaf(ctx, rnd, {
          x: Math.cos(th) * r, y: Math.sin(th) * r, angle: th - Math.PI / 2 + (rnd() - .5) * 1.4,
          len, width: len * (palette.widthRatio || .36), hue: palette.hue + (rnd() - .5) * 14, sat: palette.sat + (rnd() - .5) * 10,
          light: palette.light + (rnd() - .5) * 16 - (1 - r / (cell * .38)) * 8, vein: false, pointy: .7, gloss: .12,
        });
      }
    }
    ctx.restore();
  }
  return cv;
}

// Single-leaf atlas: 0 frangipani, 1 strap (cordyline), 2 paddle (strelitzia), 3 monstera.
function leafAtlas(size) {
  const cv = canvas(size); const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, size, size);
  const cell = size / 2;
  const rnd = mulberry32(99);
  const cells = [
    { hue: 108, sat: 46, light: 27, len: .93, width: .47, pointy: .35 },
    { hue: 338, sat: 48, light: 26, len: .95, width: .44, pointy: .8 },
    { hue: 112, sat: 40, light: 29, len: .95, width: .5, pointy: .2 },
    { hue: 128, sat: 50, light: 22, len: .86, width: .38, pointy: .1 },
  ];
  cells.forEach((p, c) => {
    const ox = (c % 2) * cell, oy = Math.floor(c / 2) * cell;
    ctx.save();
    ctx.beginPath(); ctx.rect(ox, oy, cell, cell); ctx.clip();
    ctx.translate(ox + cell / 2, oy + cell * .03);
    const len = cell * p.len, width = cell * p.width;
    if (c === 3) {
      // Monstera: heart-shaped, fenestrated.
      ctx.beginPath();
      ctx.moveTo(0, len * .05);
      ctx.bezierCurveTo(width * 1.3, -len * .02, width * 1.45, len * .7, 0, len);
      ctx.bezierCurveTo(-width * 1.45, len * .7, -width * 1.3, -len * .02, 0, len * .05);
      ctx.fillStyle = hsl(p.hue, p.sat, p.light); ctx.fill();
      ctx.globalCompositeOperation = 'destination-out';
      for (let i = 0; i < 6; i++) {
        const t = .22 + i * .12;
        for (const s of [-1, 1]) {
          ctx.beginPath(); ctx.ellipse(s * width * (.55 + .2 * Math.sin(t * 3)), len * t, width * .09, len * .035, s * .5, 0, Math.PI * 2); ctx.fill();
          if (i % 2) { ctx.beginPath(); ctx.moveTo(s * width * 1.5, len * (t + .02)); ctx.lineTo(s * width * .95, len * (t + .03)); ctx.lineWidth = 7; ctx.stroke(); }
        }
      }
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = hsl(p.hue + 10, 30, 42, .6); ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(0, len * .06); ctx.lineTo(0, len * .95); ctx.stroke();
    } else {
      drawLeaf(ctx, rnd, { x: 0, y: 0, angle: 0, len, width, hue: p.hue, sat: p.sat, light: p.light, pointy: p.pointy, gloss: .22 });
      if (c === 1) { // variegated strap edge (cordyline)
        ctx.strokeStyle = hsl(345, 60, 45, .8); ctx.lineWidth = 5; leafPath(ctx, len, width, p.pointy); ctx.stroke();
      }
      if (c === 2) { // parallel veins + a few natural splits in the paddle blade
        ctx.strokeStyle = hsl(100, 25, 42, .35); ctx.lineWidth = 2;
        for (let i = 1; i < 18; i++) { const t = i / 18; ctx.beginPath(); ctx.moveTo(0, len * t); ctx.lineTo(width * .95 * Math.sin(t * Math.PI), len * (t + .06)); ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, len * t); ctx.lineTo(-width * .95 * Math.sin(t * Math.PI), len * (t + .06)); ctx.stroke(); }
        ctx.globalCompositeOperation = 'destination-out'; ctx.lineWidth = 3;
        for (let i = 0; i < 3; i++) { const t = .3 + i * .2; ctx.beginPath(); ctx.moveTo(width * .15, len * t); ctx.lineTo(width, len * (t + .07)); ctx.stroke(); }
        ctx.globalCompositeOperation = 'source-over';
      }
    }
    ctx.restore();
  });
  return cv;
}

// Flower atlas: 0 frangipani, 1 hydrangea head, 2 ixora (red) cluster, 3 bougainvillea bracts.
function flowerAtlas(size) {
  const cv = canvas(size); const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, size, size);
  const cell = size / 2;
  const rnd = mulberry32(7);
  const petalFlower = (x, y, r, petals, fill, center, rot) => {
    for (let i = 0; i < petals; i++) {
      const a = rot + i * Math.PI * 2 / petals;
      ctx.save(); ctx.translate(x, y); ctx.rotate(a);
      ctx.beginPath(); ctx.ellipse(r * .55, 0, r * .55, r * .3, .35, 0, Math.PI * 2);
      ctx.fillStyle = fill; ctx.fill(); ctx.restore();
    }
    ctx.beginPath(); ctx.arc(x, y, r * .22, 0, Math.PI * 2); ctx.fillStyle = center; ctx.fill();
  };
  // Frangipani: a loose cluster of 5-petal flowers, white with yellow centres.
  ctx.save(); ctx.translate(cell / 2, cell / 2);
  for (let i = 0; i < 9; i++) { const a = rnd() * Math.PI * 2, r = rnd() * cell * .24; petalFlower(Math.cos(a) * r, Math.sin(a) * r, cell * .11, 5, hsl(45, 70, 95), hsl(46, 95, 58), rnd() * 6); }
  ctx.restore();
  // Hydrangea: dense dome of small 4-petal florets (cream-green / white).
  ctx.save(); ctx.translate(cell * 1.5, cell / 2);
  for (let i = 0; i < 230; i++) { const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * cell * .4; petalFlower(Math.cos(a) * r, Math.sin(a) * r, cell * .045, 4, hsl(70 + rnd() * 20, 35 + rnd() * 20, 78 + rnd() * 12), hsl(80, 40, 60), rnd() * 6); }
  ctx.restore();
  // Ixora: red umbels.
  ctx.save(); ctx.translate(cell / 2, cell * 1.5);
  for (let i = 0; i < 120; i++) { const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * cell * .34; petalFlower(Math.cos(a) * r, Math.sin(a) * r, cell * .05, 4, hsl(356 + rnd() * 10, 78, 46 + rnd() * 10), hsl(40, 80, 60), rnd() * 6); }
  ctx.restore();
  // Bougainvillea: magenta papery bracts.
  ctx.save(); ctx.translate(cell * 1.5, cell * 1.5);
  for (let i = 0; i < 90; i++) { const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * cell * .38; petalFlower(Math.cos(a) * r, Math.sin(a) * r, cell * .07, 3, hsl(318 + rnd() * 12, 70, 48 + rnd() * 12), hsl(60, 60, 85), rnd() * 6); }
  ctx.restore();
  return cv;
}

// Palm frond cards (2x2 atlas): rachis with drooping pinnate leaflets, base at the top of each cell.
function frondAtlas(size) {
  const cv = canvas(size); const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, size, size);
  const rnd = mulberry32(31);
  const cell = size / 2;
  for (let c = 0; c < 4; c++) {
    const ox = (c % 2) * cell, oy = Math.floor(c / 2) * cell;
    ctx.save(); ctx.beginPath(); ctx.rect(ox, oy, cell, cell); ctx.clip(); ctx.translate(ox + cell / 2, oy + 2);
    ctx.strokeStyle = hsl(60, 25, 40); ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, cell * .97); ctx.stroke();
    for (let i = 0; i < 40; i++) {
      const t = .04 + i / 42, y = cell * t, L = cell * .47 * Math.sin(Math.min(1, t * 1.2) * Math.PI) + 5;
      for (const sgn of [-1, 1]) {
        ctx.save(); ctx.translate(0, y); ctx.rotate(-sgn * (1.9 + rnd() * .25));
        drawLeaf(ctx, rnd, { x: 0, y: 0, angle: 0, len: L, width: 4 + rnd() * 2.5, hue: 88 + rnd() * 16, sat: 40, light: 27 + rnd() * 10, vein: false, pointy: .9, gloss: .1 });
        ctx.restore();
      }
    }
    ctx.restore();
  }
  return cv;
}

// ---------------- Indian garden atlases (4x4), painted on first use by the heritage species only ----------------
function cellAt(ctx, size, c, fn) {
  const cell = size / 4, ox = (c % 4) * cell, oy = Math.floor(c / 4) * cell;
  ctx.save(); ctx.beginPath(); ctx.rect(ox, oy, cell, cell); ctx.clip(); ctx.translate(ox, oy);
  fn(cell); ctx.restore();
}

function pinnate(ctx, rnd, x, y, angle, len, pairs, leaflet, colour) {
  // A compound leaf: a rachis with paired leaflets and a terminal one (neem, rose, marigold).
  ctx.save(); ctx.translate(x, y); ctx.rotate(angle);
  ctx.strokeStyle = hsl(colour.hue + 10, colour.sat - 15, colour.light + 6); ctx.lineWidth = Math.max(1.2, len * .012);
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(len * .04, len * .5, 0, len); ctx.stroke();
  for (let i = 0; i < pairs; i++) {
    const t = .12 + .82 * i / pairs;
    for (const s of [-1, 1]) {
      drawLeaf(ctx, rnd, { x: 0, y: len * t, angle: s * (1.15 - .25 * t) + (rnd() - .5) * .15, len: leaflet * (1 - .25 * t), width: leaflet * .3,
        hue: colour.hue + (rnd() - .5) * 10, sat: colour.sat, light: colour.light + (rnd() - .5) * 10, vein: false, pointy: .85, gloss: .18 });
    }
  }
  drawLeaf(ctx, rnd, { x: 0, y: len * .96, angle: 0, len: leaflet * .8, width: leaflet * .28, hue: colour.hue, sat: colour.sat, light: colour.light, vein: false, pointy: .85, gloss: .18 });
  ctx.restore();
}

function gardenLeafAtlas(size) {
  const cv = canvas(size); const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, size, size);
  const rnd = mulberry32(4242);
  const leafAt = (cell, o) => drawLeaf(ctx, rnd, { vein: true, pointy: .6, gloss: .2, ...o, x: o.x * cell, y: o.y * cell, len: o.len * cell, width: o.width * cell });
  // 0 neem: sprays of pinnate leaves with sickle-shaped leaflets.
  cellAt(ctx, size, 0, (cell) => {
    for (let i = 0; i < 9; i++) {
      const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * cell * .22;
      pinnate(ctx, rnd, cell / 2 + Math.cos(a) * r, cell / 2 + Math.sin(a) * r - cell * .18, a * .4 - .2 + (rnd() - .5) * 1.2, cell * (.34 + rnd() * .1), 8, cell * .07, { hue: 90 + rnd() * 10, sat: 50, light: 30 + rnd() * 10 });
    }
  });
  // 1 mango: long glossy lanceolate leaves, one coppery new flush.
  cellAt(ctx, size, 1, (cell) => {
    // Mango: whorls of long glossy leaves at the twig ends, many to a card.
    for (let w = 0; w < 7; w++) {
      const cx = .2 + rnd() * .6, cy = .15 + rnd() * .55;
      for (let i = 0; i < 9; i++) {
        const a = rnd() * Math.PI * 2;
        leafAt(cell, { x: cx, y: cy, angle: a, len: .2 + rnd() * .09, width: .035, hue: 108 + rnd() * 14, sat: 46, light: 17 + rnd() * 11, pointy: .9, vein: false, gloss: .08 });
      }
    }
  });
  // 2 ashoka: long, narrow, wavy leaves hanging from a twig.
  cellAt(ctx, size, 2, (cell) => {
    for (let i = 0; i < 9; i++) {
      ctx.save(); ctx.translate(cell * (.12 + i * .095), cell * .02); ctx.rotate((rnd() - .5) * .25);
      const len = cell * (.7 + rnd() * .25), w = cell * .055;
      ctx.beginPath(); ctx.moveTo(0, 0);
      for (let k = 0; k <= 12; k++) { const t = k / 12; ctx.lineTo(Math.sin(t * Math.PI) * w + Math.sin(t * 19) * w * .25, len * t); }
      for (let k = 12; k >= 0; k--) { const t = k / 12; ctx.lineTo(-Math.sin(t * Math.PI) * w + Math.sin(t * 19 + 1) * w * .25, len * t); }
      ctx.fillStyle = hsl(96 + rnd() * 14, 52, 27 + rnd() * 12); ctx.fill();
      ctx.strokeStyle = hsl(100, 30, 34, .5); ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, len * .95); ctx.stroke();
      ctx.restore();
    }
  });
  // 3 araucaria: a horizontal frond of overlapping scale-needles with side sprigs.
  cellAt(ctx, size, 3, (cell) => {
    const sprig = (x0, y0, x1, y1, w) => { for (let k = 0; k < 36; k++) { const t = k / 36, x = x0 + (x1 - x0) * t, y = y0 + (y1 - y0) * t, r = w * (1 - t * .6);
      ctx.fillStyle = hsl(125 + rnd() * 10, 38, 20 + rnd() * 12); ctx.beginPath(); ctx.ellipse(x, y, r, r * .55, Math.atan2(y1 - y0, x1 - x0), 0, Math.PI * 2); ctx.fill(); } };
    sprig(cell * .02, cell * .5, cell * .98, cell * .5, cell * .07);
    for (let i = 0; i < 6; i++) { const x = cell * (.12 + i * .14); sprig(x, cell * .5, x + cell * .12, cell * (.2 + rnd() * .08), cell * .04); sprig(x, cell * .5, x + cell * .12, cell * (.8 - rnd() * .08), cell * .04); }
  });
  // 4 areca: a feathery yellow-green frond.
  cellAt(ctx, size, 4, (cell) => pinnate(ctx, rnd, cell * .5, cell * .02, 0, cell * .95, 18, cell * .3, { hue: 74, sat: 55, light: 38 }));
  // 5, 6 croton: broad glossy leaves splashed with yellow veins (green) or flushed red and orange.
  for (const [c, hue, sat, light, vein] of [[5, 104, 55, 24, 52], [6, 12, 70, 33, 48]]) {
    cellAt(ctx, size, c, (cell) => {
      for (let i = 0; i < 3; i++) {
        const x = cell * (.25 + i * .25), a = (i - 1) * .3, len = cell * .9, w = cell * .19;
        drawLeaf(ctx, rnd, { x, y: cell * .03, angle: a, len, width: w, hue: hue + (rnd() - .5) * 12, sat, light, vein: false, pointy: .5, gloss: .3 });
        ctx.save(); ctx.translate(x, cell * .03); ctx.rotate(a);
        ctx.strokeStyle = hsl(vein, 85, 55, .9); ctx.lineWidth = cell * .02;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, len * .95); ctx.stroke();
        ctx.lineWidth = cell * .009;
        for (let k = 1; k < 7; k++) { const t = k / 7, ww = w * Math.sin(t * Math.PI) * .8; for (const sgn of [-1, 1]) { ctx.beginPath(); ctx.moveTo(0, len * t); ctx.lineTo(sgn * ww, len * (t + .08)); ctx.stroke(); } }
        for (let k = 0; k < 14; k++) { ctx.fillStyle = hsl(vein - 10 + rnd() * 20, 90, 50 + rnd() * 15, .85); ctx.beginPath(); ctx.arc((rnd() - .5) * w, len * (.1 + rnd() * .8), cell * (.008 + rnd() * .014), 0, Math.PI * 2); ctx.fill(); }
        ctx.restore();
      }
    });
  }
  // 7 poinsettia: scarlet bracts.
  cellAt(ctx, size, 7, (cell) => { for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; leafAt(cell, { x: .5 + Math.cos(a) * .06, y: .5 + Math.sin(a) * .06, angle: a - Math.PI / 2, len: .42, width: .12, hue: 356, sat: 82, light: 40 + rnd() * 8, pointy: .9 }); }
    ctx.fillStyle = hsl(52, 90, 55); for (let k = 0; k < 7; k++) { ctx.beginPath(); ctx.arc(cell * (.5 + (rnd() - .5) * .08), cell * (.5 + (rnd() - .5) * .08), cell * .015, 0, Math.PI * 2); ctx.fill(); } });
  // 8 tulsi: small ovate leaves, green flushed with purple.
  cellAt(ctx, size, 8, (cell) => { for (let i = 0; i < 46; i++) { const r = Math.sqrt(rnd()) * cell * .4, th = rnd() * Math.PI * 2; const purple = rnd() < .35;
    drawLeaf(ctx, rnd, { x: cell / 2 + Math.cos(th) * r, y: cell / 2 + Math.sin(th) * r, angle: th - Math.PI / 2, len: cell * .14, width: cell * .07, hue: purple ? 300 : 98, sat: purple ? 22 : 42, light: purple ? 24 : 28 + rnd() * 8, vein: false, pointy: .4, gloss: .15 }); } });
  // 9 rose: compound leaves, dark green with a reddish new-growth edge.
  cellAt(ctx, size, 9, (cell) => { for (let i = 0; i < 4; i++) pinnate(ctx, rnd, cell * (.2 + i * .2), cell * .05, -.5 + i * .33, cell * .6, 2, cell * .22, { hue: i === 3 ? 10 : 112, sat: i === 3 ? 40 : 42, light: i === 3 ? 28 : 22 }); });
  // 10 leafy greens: broad crinkled leaves with pale ribs.
  cellAt(ctx, size, 10, (cell) => { for (let i = 0; i < 3; i++) leafAt(cell, { x: .3 + i * .2, y: .03, angle: (i - 1) * .3, len: .9, width: .26, hue: 102, sat: 55, light: 30 + i * 3, pointy: .2 }); });
  // 11 tomato / brinjal foliage: lobed leaflets.
  cellAt(ctx, size, 11, (cell) => { for (let i = 0; i < 4; i++) pinnate(ctx, rnd, cell * (.2 + i * .2), cell * .05, -.45 + i * .3, cell * .7, 3, cell * .2, { hue: 96, sat: 40, light: 28 }); });
  // 12 strap leaf (amaryllis, spider lily).
  cellAt(ctx, size, 12, (cell) => leafAt(cell, { x: .5, y: 0, angle: 0, len: .99, width: .22, hue: 110, sat: 42, light: 30, pointy: .3, vein: false }));
  // 13 heart-shaped creeper leaves.
  cellAt(ctx, size, 13, (cell) => { for (let i = 0; i < 14; i++) { const x = cell * (.15 + rnd() * .7), y = cell * (.1 + rnd() * .6), len = cell * (.22 + rnd() * .1);
    ctx.save(); ctx.translate(x, y); ctx.rotate((rnd() - .5) * 1.2); ctx.beginPath(); ctx.moveTo(0, 0);
    ctx.bezierCurveTo(len * .7, -len * .25, len * .65, len * .6, 0, len); ctx.bezierCurveTo(-len * .65, len * .6, -len * .7, -len * .25, 0, 0);
    ctx.fillStyle = hsl(96 + rnd() * 14, 50, 25 + rnd() * 12); ctx.fill(); ctx.restore(); } });
  // 14 bougainvillea leaves: small soft ovals.
  cellAt(ctx, size, 14, (cell) => { for (let i = 0; i < 26; i++) { const r = Math.sqrt(rnd()) * cell * .38, th = rnd() * Math.PI * 2;
    drawLeaf(ctx, rnd, { x: cell / 2 + Math.cos(th) * r, y: cell / 2 + Math.sin(th) * r, angle: th - Math.PI / 2, len: cell * .2, width: cell * .11, hue: 104, sat: 46, light: 25 + rnd() * 8, vein: true, pointy: .45, gloss: .15 }); } });
  // 15 feathery marigold foliage.
  cellAt(ctx, size, 15, (cell) => { for (let i = 0; i < 6; i++) pinnate(ctx, rnd, cell * (.15 + i * .14), cell * .05, -.6 + i * .24, cell * .7, 11, cell * .07, { hue: 100, sat: 45, light: 27 }); });
  return cv;
}

function gardenFlowerAtlas(size) {
  const cv = canvas(size); const ctx = cv.getContext('2d');
  ctx.clearRect(0, 0, size, size);
  const rnd = mulberry32(5151);
  const petals = (x, y, r, n, fill, rot, w = .3, centre = null, cr = .2) => {
    for (let i = 0; i < n; i++) {
      const a = rot + i * Math.PI * 2 / n;
      ctx.save(); ctx.translate(x, y); ctx.rotate(a);
      ctx.beginPath(); ctx.ellipse(r * .55, 0, r * .55, r * w, 0, 0, Math.PI * 2); ctx.fillStyle = fill(i); ctx.fill(); ctx.restore();
    }
    if (centre) { ctx.beginPath(); ctx.arc(x, y, r * cr, 0, Math.PI * 2); ctx.fillStyle = centre; ctx.fill(); }
  };
  const pom = (cell, hue) => {
    // Marigold: a dense ball of ruffled petals, darker toward the heart.
    const cx = cell / 2, cy = cell / 2;
    for (let ring = 6; ring >= 0; ring--) {
      const R = cell * .44 * (ring + 1) / 7;
      const n = 10 + ring * 6;
      for (let i = 0; i < n; i++) {
        const a = i / n * Math.PI * 2 + rnd() * .3;
        ctx.save(); ctx.translate(cx + Math.cos(a) * R * .75, cy + Math.sin(a) * R * .75); ctx.rotate(a);
        ctx.beginPath(); ctx.ellipse(0, 0, cell * .05, cell * .035, 0, 0, Math.PI * 2);
        ctx.fillStyle = hsl(hue + (rnd() - .5) * 8, 95, 44 + ring * 2.5 + rnd() * 6); ctx.fill(); ctx.restore();
      }
    }
  };
  const rose = (cell, hue, sat, light) => {
    const cx = cell / 2, cy = cell / 2;
    for (let ring = 5; ring >= 0; ring--) {
      const R = cell * .44 * (ring + 1) / 6, n = 5 + ring;
      for (let i = 0; i < n; i++) {
        const a = i / n * Math.PI * 2 + ring * .7;
        ctx.save(); ctx.translate(cx + Math.cos(a) * R * .35, cy + Math.sin(a) * R * .35); ctx.rotate(a + Math.PI / 2);
        ctx.beginPath(); ctx.arc(0, 0, R * .55, Math.PI * .05, Math.PI * .95); ctx.closePath();
        ctx.fillStyle = hsl(hue, sat, light - (5 - ring) * 2.2 + rnd() * 4); ctx.fill();
        ctx.strokeStyle = hsl(hue, sat, light - 14, .6); ctx.lineWidth = 1.5; ctx.stroke(); ctx.restore();
      }
    }
  };
  cellAt(ctx, size, 0, (cell) => pom(cell, 30));
  cellAt(ctx, size, 1, (cell) => pom(cell, 46));
  cellAt(ctx, size, 2, (cell) => rose(cell, 352, 76, 42));
  cellAt(ctx, size, 3, (cell) => rose(cell, 340, 62, 70));
  cellAt(ctx, size, 4, (cell) => rose(cell, 45, 32, 90));
  cellAt(ctx, size, 5, (cell) => petals(cell / 2, cell / 2, cell * .44, 5, () => hsl(325, 62, 72), .3, .42, hsl(335, 70, 45), .18));
  cellAt(ctx, size, 6, (cell) => { for (let i = 0; i < 16; i++) { const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * cell * .3; petals(cell / 2 + Math.cos(a) * r, cell / 2 + Math.sin(a) * r, cell * .12, 5, () => hsl(358 + rnd() * 6, 82, 44 + rnd() * 8), rnd() * 6, .38, hsl(10, 60, 30), .15); } });
  cellAt(ctx, size, 7, (cell) => { petals(cell / 2, cell / 2, cell * .46, 26, () => hsl(22 + rnd() * 6, 92, 52 + rnd() * 6), 0, .12); petals(cell / 2, cell / 2, cell * .25, 18, () => hsl(30, 90, 45), .1, .12, hsl(20, 60, 18), .5); });
  cellAt(ctx, size, 8, (cell) => {
    petals(cell / 2, cell / 2, cell * .47, 6, () => hsl(358, 80, 42), 0, .3);
    for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3; ctx.strokeStyle = hsl(0, 30, 92, .8); ctx.lineWidth = cell * .025; ctx.beginPath(); ctx.moveTo(cell / 2, cell / 2); ctx.lineTo(cell / 2 + Math.cos(a) * cell * .3, cell / 2 + Math.sin(a) * cell * .3); ctx.stroke(); }
    ctx.beginPath(); ctx.arc(cell / 2, cell / 2, cell * .09, 0, Math.PI * 2); ctx.fillStyle = hsl(80, 40, 75); ctx.fill();
  });
  const bracts = (cell, hue, sat, light) => { for (let i = 0; i < 9; i++) { const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * cell * .26;
    petals(cell / 2 + Math.cos(a) * r, cell / 2 + Math.sin(a) * r, cell * .2, 3, () => hsl(hue + (rnd() - .5) * 10, sat, light + (rnd() - .5) * 10), rnd() * 6, .42, hsl(55, 50, 85), .12); } };
  cellAt(ctx, size, 9, (cell) => bracts(cell, 60, 18, 90));
  cellAt(ctx, size, 10, (cell) => bracts(cell, 318, 72, 50));
  cellAt(ctx, size, 11, (cell) => petals(cell / 2, cell / 2, cell * .44, 5, () => hsl(280, 52, 52), .2, .45, hsl(290, 40, 85), .14));
  cellAt(ctx, size, 12, (cell) => { for (let i = 0; i < 14; i++) { const a = rnd() * Math.PI * 2, r = Math.sqrt(rnd()) * cell * .34; petals(cell / 2 + Math.cos(a) * r, cell / 2 + Math.sin(a) * r, cell * .11, 6, () => hsl(50, 25, 96), rnd() * 6, .2, hsl(55, 60, 75), .15); } });
  cellAt(ctx, size, 13, (cell) => { for (let i = 0; i < 3; i++) { const x = cell * (.25 + i * .25), y = cell * (.35 + rnd() * .15);
    ctx.strokeStyle = hsl(80, 30, 30); ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, y); ctx.stroke();
    const g = ctx.createRadialGradient(x - cell * .03, y + cell * .12, cell * .02, x, y + cell * .16, cell * .16); g.addColorStop(0, hsl(62, 70, 62)); g.addColorStop(1, hsl(88, 55, 33));
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(x, y + cell * .17, cell * .085, cell * .15, (rnd() - .5) * .3, 0, Math.PI * 2); ctx.fill(); } });
  cellAt(ctx, size, 14, (cell) => { ctx.strokeStyle = hsl(290, 25, 30); ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cell / 2, 0); ctx.lineTo(cell / 2, cell); ctx.stroke();
    for (let i = 0; i < 9; i++) { const y = cell * (.08 + i * .1); petals(cell / 2, y, cell * (.16 - i * .008), 6, () => hsl(290 + rnd() * 10, 30, 40 + rnd() * 10), rnd(), .35); } });
  cellAt(ctx, size, 15, (cell) => petals(cell / 2, cell / 2, cell * .46, 18, () => hsl(50, 15, 97), 0, .14, hsl(46, 90, 52), .26));
  return cv;
}

export class FoliageTextures {
  constructor(renderer, quality = 'high') {
    const size = quality === 'performance' ? 512 : 1024;
    const an = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    this.size = size; this.an = an;
    this.cluster = toTexture(clusterAtlas(size, { hue: 104, sat: 38, light: 28, seed: 1, conifer: true, count: 80 }), an);
    this.clusterLight = toTexture(clusterAtlas(size, { hue: 86, sat: 42, light: 34, seed: 2, conifer: true, count: 70, leafLen: .19 }), an);
    this.leaves = toTexture(leafAtlas(size), an, true);
    this.flowers = toTexture(flowerAtlas(size), an);
    this.fronds = toTexture(frondAtlas(size), an);
  }
  // Indian garden atlases are painted only when a scene plants one of the heritage species.
  get gardenLeaves() { return this._gardenLeaves ||= toTexture(gardenLeafAtlas(this.size), this.an); }
  get gardenFlowers() { return this._gardenFlowers ||= toTexture(gardenFlowerAtlas(this.size), this.an); }
  dispose() { for (const t of [this.cluster, this.clusterLight, this.leaves, this.flowers, this.fronds, this._gardenLeaves, this._gardenFlowers]) t?.dispose(); }
}
