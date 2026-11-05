import test from 'node:test';
import assert from 'node:assert/strict';
import {MaterialLibrary} from './materials.js';

test('exterior glass overrides do not change other glass materials', () => {
  const lib = new MaterialLibrary(null, {
    ordinary: {alpha:.2, color:'#d4e9ed'},
    exterior: {alpha:.4, color:'#aec8cc', glassOpacity:.4, glassReflectivity:.65, glassEnv:2},
  });
  const ordinary = lib.get('ordinary');
  const exterior = lib.get('exterior');
  assert.equal(ordinary.opacity, .2*.75);
  assert.ok(Math.abs(ordinary.reflectivity-.5)<1e-12);
  assert.equal(ordinary.envMapIntensity, 1.6);
  assert.equal(exterior.opacity, .4);
  assert.ok(exterior.reflectivity > ordinary.reflectivity);
  assert.equal(exterior.envMapIntensity, 2);
  assert.equal(exterior.transparent, true);
  assert.equal(exterior.depthWrite, false);
  assert.equal(lib.get('ordinary'), ordinary);
  lib.dispose();
});
