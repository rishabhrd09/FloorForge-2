import test from 'node:test';
import assert from 'node:assert/strict';
import { toTexture } from './foliage-textures.js';

test('transparent atlas pixels take their own cell\'s leaf colour and keep their alpha', () => {
  // A 4 × 4 atlas of 2 × 2 cells as a canvas returns it: no colour left where a pixel is transparent.
  const size = 4, data = new Uint8ClampedArray(size * size * 4);
  const set = (x, y, rgba) => data.set(rgba, (y * size + x) * 4);
  set(0, 0, [40, 120, 30, 255]); set(1, 0, [60, 140, 50, 255]);   // a leaf in the top-left cell
  set(1, 1, [255, 255, 255, 20]);                                  // a faint antialiased pixel at its edge
  set(2, 2, [200, 60, 80, 255]);                                   // a petal in the bottom-right cell
  const cv = { width: size, height: size, getContext: () => ({ getImageData: () => ({ data }) }) };
  const t = toTexture(cv, 4, 2);
  const px = (x, y) => Array.from(t.image.data.slice((y * size + x) * 4, (y * size + x) * 4 + 4));
  assert.deepEqual(px(0, 0), [40, 120, 30, 255]);   // leaf pixels are left as painted
  assert.deepEqual(px(0, 1), [50, 130, 40, 0]);     // transparent: the cell's mean leaf colour, still transparent
  assert.deepEqual(px(1, 1), [50, 130, 40, 20]);    // the faint edge pixel takes the leaf colour, not white
  assert.deepEqual(px(3, 3), [200, 60, 80, 0]);     // the petal's cell keeps to its own colour
  assert.deepEqual(px(3, 0), [0, 0, 0, 0]);         // an empty cell is left alone
  assert.equal(t.flipY, false);
  assert.equal(t.generateMipmaps, true);
});
