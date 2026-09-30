import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { Walker, WALK_SETTINGS } from './walker.js';

function walker() {
  const ground = new THREE.PlaneGeometry(100, 100).rotateX(-Math.PI / 2);
  const w = new Walker(ground, { min: new THREE.Vector3(-50, -1, -50), max: new THREE.Vector3(50, 20, 50) });
  w.teleport(new THREE.Vector3(0, .1, 0), 0);
  return w;
}
function step(w, input, fps = 60, seconds = 1) {
  for (let i = 0; i < fps * seconds; i++) w.update(1 / fps, { forward: 0, strafe: 0, ...input });
}

test('turning in place rotates the view without translating sideways', () => {
  for (const turn of [-1, 1]) {
    const w = walker();
    step(w, { turn });
    assert.ok(Math.abs(w.yaw - turn * WALK_SETTINGS.turnSpeed) < 1e-10);
    assert.equal(w.position.x, 0);
    assert.equal(w.position.z, 0);
  }
});

test('keyboard turn speed is consistent at 30, 60 and 144 frames per second', () => {
  for (const fps of [30, 60, 144]) {
    const w = walker();
    step(w, { turn: -1 }, fps, 2);
    assert.ok(Math.abs(w.yaw + WALK_SETTINGS.turnSpeed * 2) < 1e-10);
  }
});

test('forward and backward follow the new facing direction after a right turn', () => {
  const w = walker();
  w.update(Math.PI / 2 / WALK_SETTINGS.turnSpeed, { turn: -1, forward: 0, strafe: 0 });
  step(w, { forward: 1 });
  assert.ok(w.position.x > 2 && Math.abs(w.position.z) < 1e-8);
  const before = w.position.x;
  step(w, { forward: -1 });
  assert.ok(w.position.x < before - 1.5 && Math.abs(w.position.z) < 1e-8);
});

test('moving and turning together steers, and releasing turn stops rotation', () => {
  const w = walker();
  step(w, { forward: 1, turn: -1 });
  assert.ok(w.position.x > .5 && w.position.z < -.5);
  const yaw = w.yaw;
  step(w, { forward: 1 });
  assert.equal(w.yaw, yaw);
});

test('sideways movement stays independent of facing direction', () => {
  const w = walker();
  step(w, { strafe: 1 });
  assert.ok(w.position.x > 2);
  assert.equal(w.position.z, 0);
  assert.equal(w.yaw, 0);
});
