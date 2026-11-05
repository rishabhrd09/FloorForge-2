import test from 'node:test';
import assert from 'node:assert/strict';
import { visibilityClass, buildBuckets } from './scene-builder.js';

test('decorative ceiling panels lift with the roof in plan and dollhouse views', () => {
  assert.equal(visibilityClass('ceiling-feature'), 'overhead');
  assert.equal(visibilityClass('furniture'), 'other');
  assert.equal(visibilityClass('floor'), 'floor');
});

test('wall-integrated open slabs retain their exact walkable tops without enabling open decor collisions', () => {
  const asset = { vertices: [[0,0,3.508],[1,0,3.508],[0,1,3.508]], faces: [[0,1,2]], closed: false };
  const node = (id, role, marked) => ({ id, role, asset: 'open', material: 'stone', floor: 1,
    position: [0,0,0], rotation: [0,0,0], scale: [1,1,1],
    ...(marked ? { collisionEnvelope: 'wall-integrated-slab' } : {}) });
  const data = { assets: { open: asset }, materials: { stone: {} }, nodes: [
    node('floor', 'floor', true), node('slab', 'slab', true),
    node('unmarked-floor', 'floor', false), node('curtain', 'curtain', true),
  ] };
  const buckets = buildBuckets(data, { tileSize: () => [1,1], descriptor: () => ({kind:'stone'}) });
  const colliders = buckets.filter(b => b.collide);
  assert.deepEqual(colliders.flatMap(b => b.roles).sort(), ['floor','slab']);
  for (const b of colliders) {
    const positions = b.geometry.attributes.position;
    for (let i=0; i<positions.count; i++) assert.ok(Math.abs(positions.getY(i)-3.508)<1e-6);
    assert.equal(b.doubleSided, true);
  }
  assert.equal(buckets.find(b => b.roles.includes('curtain')).collide, false);
  assert.equal(buckets.find(b => b.roles.includes('floor') && !b.collide).collide, false);
});
