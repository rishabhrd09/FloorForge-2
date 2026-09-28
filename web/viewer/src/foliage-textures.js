// Canvas-painted foliage atlases (alpha-tested leaf cards). Deterministic, no bitmaps shipped.
import * as THREE from 'three';
import { mulberry32 } from './util.js';

function canvas(size) {
  if (typeof OffscreenCanvas !== 'undefined') return new OffscreenCanvas(size, size);
  const c = document.createElement('canvas'); c.width = size; c.height = size; return c;
}

function toTexture(cv, anisotropy) {
  const t = new THREE.CanvasTexture(cv);
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

export class FoliageTextures {
  constructor(renderer, quality = 'high') {
    const size = quality === 'performance' ? 512 : 1024;
    const an = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    this.cluster = toTexture(clusterAtlas(size, { hue: 104, sat: 38, light: 28, seed: 1, conifer: true, count: 80 }), an);
    this.clusterLight = toTexture(clusterAtlas(size, { hue: 86, sat: 42, light: 34, seed: 2, conifer: true, count: 70, leafLen: .19 }), an);
    this.leaves = toTexture(leafAtlas(size), an);
    this.flowers = toTexture(flowerAtlas(size), an);
    this.fronds = toTexture(frondAtlas(size), an);
  }
  dispose() { for (const t of [this.cluster, this.clusterLight, this.leaves, this.flowers, this.fronds]) t.dispose(); }
}
