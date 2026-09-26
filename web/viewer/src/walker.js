// First-person walking on the real generated geometry: capsule collision against a BVH of
// walls/furniture, step-offset stair climbing, gravity, jumping and crouching.
import * as THREE from 'three';
import { MeshBVH } from 'three-mesh-bvh';
import { damp, clamp } from './util.js';

const _seg = new THREE.Line3();
const _box = new THREE.Box3();
const _tri = new THREE.Vector3();
const _cap = new THREE.Vector3();
const _dir = new THREE.Vector3();
const _ray = new THREE.Ray();
const _n = new THREE.Vector3();

export const WALK_SETTINGS = {
  radius: .27,
  height: 1.78,
  eye: 1.63,
  crouchHeight: 1.2,
  crouchEye: 1.08,
  stepUp: .38,
  snapDown: .42,
  walkSpeed: 2.3,
  runSpeed: 5.0,
  crouchSpeed: 1.2,
  accel: 14,
  airAccel: 3,
  gravity: 16.5,
  jump: 5.4,
};

export class Walker {
  constructor(geometry, bounds, settings = {}) {
    this.s = { ...WALK_SETTINGS, ...settings };
    this.geometry = geometry;
    this.bvh = new MeshBVH(geometry, { maxLeafSize: 8 });
    this.bounds = bounds; // {min: Vector3, max: Vector3} in Three space
    this.position = new THREE.Vector3();
    this.velocity = new THREE.Vector3();
    this.yaw = 0; this.pitch = 0;
    this.onGround = false;
    this.crouching = false;
    this.eyeY = 0;
    this.bobPhase = 0;
    this.bobAmount = 0;
    this.landDip = 0;
    this.airTime = 0;
    this.lastGroundY = 0;
    this.distance = 0;
  }

  teleport(pos, yaw = this.yaw, pitch = 0) {
    this.position.copy(pos);
    this.velocity.set(0, 0, 0);
    this.yaw = yaw; this.pitch = pitch;
    const g = this.groundHeight(this.position, 1.2);
    if (g !== null) this.position.y = g;
    this.onGround = g !== null;
    this.eyeY = this.position.y + this.s.eye;
    this.landDip = 0;
  }

  // Highest walkable (upward-facing) surface under the feet within [feet - drop, feet + stepUp].
  groundHeight(pos, drop) {
    const s = this.s;
    const top = pos.y + s.stepUp + .05;
    let best = null;
    const r = s.radius * .62;
    const offsets = [[0, 0], [r, 0], [-r, 0], [0, r], [0, -r]];
    for (const [ox, oz] of offsets) {
      _ray.origin.set(pos.x + ox, top, pos.z + oz);
      _ray.direction.set(0, -1, 0);
      const hits = this.bvh.raycast(_ray, THREE.DoubleSide, 0, s.stepUp + .05 + drop);
      let y = null, dist = Infinity;
      for (const hit of hits) {
        if (hit.face && hit.face.normal.y < .3) continue; // underside/back face or a wall side
        if (hit.distance < dist) { dist = hit.distance; y = hit.point.y; }
      }
      if (y !== null && (best === null || y > best)) best = y;
    }
    return best;
  }

  ceilingClear(pos, height) {
    _ray.origin.set(pos.x, pos.y + .3, pos.z);
    _ray.direction.set(0, 1, 0);
    const hit = this.bvh.raycastFirst(_ray, THREE.DoubleSide, 0, height);
    return hit ? hit.distance + .3 : Infinity;
  }

  // Pushes a capsule (raised by the step offset) out of walls and furniture; returns horizontal correction.
  collide(pos) {
    const s = this.s;
    const h = this.crouching ? s.crouchHeight : s.height;
    const r = s.radius;
    const bottom = pos.y + s.stepUp + r * .5;
    const topY = Math.max(bottom + .01, pos.y + h - r);
    _seg.start.set(pos.x, bottom, pos.z);
    _seg.end.set(pos.x, topY, pos.z);
    const sx = _seg.start.x, sz = _seg.start.z;
    for (let iter = 0; iter < 3; iter++) {
      _box.makeEmpty();
      _box.expandByPoint(_seg.start); _box.expandByPoint(_seg.end);
      _box.min.addScalar(-r); _box.max.addScalar(r);
      let moved = false;
      this.bvh.shapecast({
        intersectsBounds: (box) => box.intersectsBox(_box),
        intersectsTriangle: (tri) => {
          const d = tri.closestPointToSegment(_seg, _tri, _cap);
          if (d < r) {
            if (d < 1e-6) { tri.getNormal(_dir); if (_dir.dot(_n.set(_seg.start.x - _tri.x, 0, _seg.start.z - _tri.z)) < 0) _dir.negate(); }
            else _dir.subVectors(_cap, _tri).divideScalar(d);
            _dir.y = 0;
            const l = _dir.length();
            if (l < 1e-4) return false;
            _dir.divideScalar(l);
            const depth = r - d;
            _seg.start.addScaledVector(_dir, depth);
            _seg.end.addScaledVector(_dir, depth);
            moved = true;
          }
          return false;
        },
      });
      if (!moved) break;
    }
    return [_seg.start.x - sx, _seg.start.z - sz];
  }

  update(dt, input) {
    const s = this.s;
    // Crouch (cannot stand up under a low ceiling).
    const wantCrouch = !!input.crouch;
    if (!wantCrouch && this.crouching) { if (this.ceilingClear(this.position, s.height) > s.height - .05) this.crouching = false; }
    else this.crouching = wantCrouch;
    const speed = this.crouching ? s.crouchSpeed : input.run ? s.runSpeed : s.walkSpeed;
    const fx = Math.sin(this.yaw), fz = Math.cos(this.yaw);
    // Forward is -Z in Three when yaw = 0 → use (-sin, -cos).
    let mx = -fx * input.forward + fz * input.strafe;
    let mz = -fz * input.forward - fx * input.strafe;
    const ml = Math.hypot(mx, mz);
    if (ml > 1) { mx /= ml; mz /= ml; }
    const accel = this.onGround ? s.accel : s.airAccel;
    const k = 1 - Math.exp(-accel * dt);
    this.velocity.x += (mx * speed - this.velocity.x) * k;
    this.velocity.z += (mz * speed - this.velocity.z) * k;
    if (input.jump && this.onGround && !this.crouching) {
      this.velocity.y = s.jump;
      this.onGround = false;
      this.airTime = 0;
      input.jump = false;
    }
    // Sub-stepped integration keeps fast motion from tunnelling through thin walls.
    const travel = Math.hypot(this.velocity.x, this.velocity.z) * dt + Math.abs(this.velocity.y) * dt;
    const steps = clamp(Math.ceil(travel / (s.radius * .35)), 1, 12);
    const h = dt / steps;
    const wasOnGround = this.onGround;
    const startY = this.position.y;
    for (let i = 0; i < steps; i++) this.step(h);
    // Camera: smoothed eye height (stairs feel continuous), head bob, landing dip.
    const horiz = Math.hypot(this.velocity.x, this.velocity.z);
    if (this.onGround && horiz > .2) {
      this.bobPhase += horiz * dt * (Math.PI / .72);
      this.bobAmount = damp(this.bobAmount, Math.min(1, horiz / s.runSpeed * 1.6), 6, dt);
    } else this.bobAmount = damp(this.bobAmount, 0, 5, dt);
    if (!wasOnGround && this.onGround) {
      const fall = Math.max(0, this.lastAirVel || 0);
      this.landDip = Math.min(.12, fall * .018);
    }
    this.landDip = damp(this.landDip, 0, 7, dt);
    const eyeTarget = this.position.y + (this.crouching ? s.crouchEye : s.eye);
    const stepping = this.onGround && Math.abs(this.position.y - startY) > 1e-4;
    this.eyeY = this.onGround ? damp(this.eyeY, eyeTarget, stepping ? 14 : 30, dt) : eyeTarget;
    if (Math.abs(this.eyeY - eyeTarget) > .6) this.eyeY = eyeTarget;
    this.distance += horiz * dt;
  }

  step(dt) {
    const s = this.s;
    const p = this.position;
    p.x += this.velocity.x * dt;
    p.z += this.velocity.z * dt;
    if (!this.onGround) {
      this.velocity.y -= s.gravity * dt;
      p.y += this.velocity.y * dt;
      this.airTime += dt;
    }
    const [cx, cz] = this.collide(p);
    p.x += cx; p.z += cz;
    if (Math.abs(cx) + Math.abs(cz) > 1e-6) {
      // Remove velocity into the obstacle so we slide along walls.
      const l = Math.hypot(cx, cz);
      const nx = cx / l, nz = cz / l;
      const vn = this.velocity.x * nx + this.velocity.z * nz;
      if (vn < 0) { this.velocity.x -= vn * nx; this.velocity.z -= vn * nz; }
    }
    // Ceiling.
    if (this.velocity.y > 0) {
      const room = this.ceilingClear(p, (this.crouching ? s.crouchHeight : s.height) + .2);
      if (room < (this.crouching ? s.crouchHeight : s.height)) this.velocity.y = 0;
    }
    // Ground: step up onto treads/kerbs, stick to the floor when walking down stairs.
    const drop = this.onGround ? s.snapDown : Math.max(.02, -this.velocity.y * dt + .02);
    const g = this.groundHeight(p, drop);
    if (g !== null && this.velocity.y <= 0.01 && g >= p.y - drop) {
      if (!this.onGround) this.lastAirVel = -this.velocity.y;
      p.y = g;
      this.velocity.y = 0;
      this.onGround = true;
      this.lastGroundY = g;
    } else if (this.onGround && (g === null || g < p.y - drop)) {
      this.onGround = false;
      this.airTime = 0;
    }
    // Keep the visitor on the generated site.
    const b = this.bounds;
    p.x = clamp(p.x, b.min.x, b.max.x);
    p.z = clamp(p.z, b.min.z, b.max.z);
    if (p.y < b.min.y - 25) { this.respawn?.(); }
  }

  eyePosition(target) {
    const bob = this.bobAmount;
    const y = this.eyeY + Math.sin(this.bobPhase * 2) * .028 * bob - this.landDip;
    const side = Math.cos(this.bobPhase) * .018 * bob;
    target.set(this.position.x + Math.cos(this.yaw) * side, y, this.position.z - Math.sin(this.yaw) * side);
    return target;
  }

  roll() { return Math.cos(this.bobPhase) * .0045 * this.bobAmount; }

  dispose() { this.geometry.dispose(); }
}
