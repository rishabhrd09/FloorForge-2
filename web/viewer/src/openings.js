// Runtime poses for authored openings. The canonical scene and export geometry stay immutable.
import * as THREE from 'three';
import { MeshBVH } from 'three-mesh-bvh';
import { buildBuckets } from './scene-builder.js';

const point = ([x, y, z]) => new THREE.Vector3(x, z, -y);
const up = new THREE.Vector3(0, 1, 0);
const angleDelta = (a, b) => Math.atan2(Math.sin(a - b), Math.cos(a - b));

// The optional building supplies the same hosts for older saved scenes and the bundled example.
export function describeOpenings(scene, building = scene.opening_model) {
  building ||= {walls: [], openings: []};
  const walls = new Map(building.walls.map(w => [w.id, w]));
  const result = (scene.gate_model || []).map(gate => ({
    ...gate, start: point(gate.start), axis: point(gate.axis),
    center: point(gate.start).addScaledVector(point(gate.axis), gate.width / 2).addScaledVector(up, gate.height / 2),
    parts: gate.parts.map(part => ({...part, ...(part.slide ? {slide: point(part.slide)} : {pivot: point(part.pivot)})})),
  }));
  for (const o of building.openings) {
    if (o.kind === 'cased' || o.fixed) continue;
    const wall = walls.get(o.wall_id);
    if (!wall) continue;
    const dx = wall.b[0] - wall.a[0], dy = wall.b[1] - wall.a[1], len = Math.hypot(dx, dy);
    const u = [dx / len, dy / len], n = [-u[1], u[0]], width = o.width / 1000;
    const start = [wall.a[0] / 1000 + u[0] * o.offset / 1000, wall.a[1] / 1000 + u[1] * o.offset / 1000];
    const at = (x, z) => [start[0] + u[0] * x, start[1] + u[1] * x, z];
    const base = o.floor * scene.floor_height, sill = o.sill / 1000, height = o.height / 1000;
    const owned = scene.nodes.filter(node => node.owner === o.id);
    const label = (scene.rooms || []).filter(r => o.connects?.includes(r.id)).map(r => r.name).join(' / ');
    const desc = { id: o.id, floor: o.floor, kind: o.kind, label: `${o.kind === 'window' ? 'Window' : o.kind === 'entry' ? 'Entrance door' : 'Door'}${label ? ' · ' + label : ''}`,
      center: point(at(width / 2, base + sill + Math.min(height / 2, 1.25))), start: point(at(0, base + sill)), axis: point([u[0], u[1], 0]), width, sill, height, base, parts: [] };
    const glass = owned.filter(node => node.role === 'glass');
    if (scene.door_motion?.[o.id]) {
      const motion = scene.door_motion[o.id];
      if (motion.layers) {
        for (const leaf of motion.layers) result.push({...desc, id: leaf.id,
          label: `${leaf.label} · ${label}`, initial: 0, clearWidth: leaf.clearWidth ?? motion.clearWidth,
          handle: point(leaf.handle), parts: [{ids: leaf.ids, ...(leaf.slide ? {slide: point(leaf.slide)} : {pivot: point(leaf.pivot), angle: leaf.angle})}]});
        continue;
      }
      desc.parts.push({...motion, pivot: point(motion.pivot)});
      desc.initial = 0;
    } else if (o.kind === 'glazed' && o.sliding && glass.length) {
      const panelCount = o.slidingPanels || 3;
      for (let pane=1;pane<panelCount;pane++) desc.parts.push({ids: owned.filter(n => n.slidingPanel === pane).map(n => n.id), slide: point([-u[0]*(width-.1)/panelCount*pane,-u[1]*(width-.1)/panelCount*pane,0])});
      desc.initial = 0; desc.clearWidth = (width-.1)*(panelCount-1)/panelCount-.04;
    } else if (o.kind === 'window' && glass.length) {
      if (glass.length > 1) {
        // The first sash slides onto its neighbour; other panes and the fixed frame stay put.
        desc.parts.push({ ids: [glass[0].id], slide: point([u[0] * width / glass.length, u[1] * width / glass.length, 0]) });
      } else {
        desc.parts.push({ ids: [glass[0].id], pivot: point(at(.045, base + sill)), angle: Math.PI / 2 });
      }
      desc.initial = 0;
    } else if (o.kind === 'glazed' && glass.length) {
      // The authored balcony leaf already rests half-open. Swing that leaf clear of the full aperture.
      const first = owned.findIndex(node => node.role === 'glass');
      desc.parts.push({ ids: owned.slice(first).filter(node => ['glass', 'joinery'].includes(node.role)).map(node => node.id),
        pivot: point(at(width - .04, base)), angle: Math.PI / 2 });
      desc.initial = 0; desc.partial = true;
    } else {
      const leaf = owned.find(node => node.role === 'door');
      if (!leaf) continue;
      const pivotDoor = Math.abs(leaf.scale[0] - .056) < .001;
      const hinge = pivotDoor ? .05 + (width - .1) * .17 : o.hinge === 'end' ? width - .055 : .055;
      const pivot = at(hinge, base), dot = (leaf.position[0] - pivot[0]) * n[0] + (leaf.position[1] - pivot[1]) * n[1];
      const direction = dot >= 0 ? n : n.map(v => -v);
      const closed = !pivotDoor && o.hinge === 'end' ? u.map(v => -v) : u;
      // Legacy handles either have no owner or own their generated object ID. They still
      // belong to the immediately preceding leaf and must move with it, including collision.
      const ids = []; let inLeaf = false;
      for (const node of scene.nodes) {
        if (node.owner === o.id && node.role === 'door') { ids.push(node.id); inLeaf = true; }
        else if (inLeaf && (!node.owner || node.owner === node.id) && node.role === 'door' && node.floor === o.floor) ids.push(node.id);
        else if (inLeaf) break;
      }
      desc.parts.push({ ids, pivot: point(pivot), angle: angleDelta(Math.atan2(closed[1], closed[0]), Math.atan2(direction[1], direction[0])), reverse: true });
      desc.initial = 1; // The design's original door pose is open.
    }
    if (desc.parts.length) result.push(desc);
  }
  return result;
}

export class OpeningController {
  constructor(viewer, descriptors) {
    this.viewer = viewer; this.items = []; this.target = null; this.message = ''; this.messageUntil = 0;
    const nodes = new Map(viewer.data.nodes.map(n => [n.id, n]));
    const chunks = []; let offset = 0;
    for (const d of descriptors) {
      const item = { ...d, value: d.initial, goal: d.initial, parts: [] };
      for (const motion of d.parts) {
        const group = new THREE.Group(); viewer.root.add(group);
        const part = { ...motion, group, chunks: [] };
        const buckets = buildBuckets({ ...viewer.data, nodes: motion.ids.map(id => nodes.get(id)).filter(Boolean) }, viewer.materials);
        for (const bucket of buckets) {
          const mesh = viewer.addBucket(bucket, group);
          if (!bucket.collide) continue;
          const source = mesh.geometry.attributes.position.array;
          const chunk = { source, offset, owner: item.id, matrix: group.matrixWorld };
          chunks.push(chunk); part.chunks.push(chunk); offset += source.length;
        }
        item.parts.push(part);
      }
      this.items.push(item);
    }
    if (offset) {
      this.geometry = new THREE.BufferGeometry();
      this.geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(offset), 3));
      this.chunks = chunks; this.syncGeometry();
      this.bvh = new MeshBVH(this.geometry, { maxLeafSize: 8 });
      viewer.walker.dynamicBVHs = [this.bvh];
    }
  }

  pose(item) {
    for (const part of item.parts) {
      const t = part.reverse ? 1 - item.value : item.value, m = part.group.matrix;
      m.identity();
      if (part.slide) m.makeTranslation(...part.slide.clone().multiplyScalar(t).toArray());
      else {
        m.makeTranslation(...part.pivot.toArray());
        m.multiply(new THREE.Matrix4().makeRotationAxis(up, part.angle * t));
        m.multiply(new THREE.Matrix4().makeTranslation(...part.pivot.clone().negate().toArray()));
      }
      part.group.matrixAutoUpdate = false; part.group.updateMatrixWorld(true);
    }
  }

  syncGeometry() {
    if (!this.geometry) return;
    const array = this.geometry.attributes.position.array, p = new THREE.Vector3();
    for (const c of this.chunks) for (let i = 0; i < c.source.length; i += 3) {
      p.fromArray(c.source, i).applyMatrix4(c.matrix).toArray(array, c.offset + i);
    }
    this.geometry.attributes.position.needsUpdate = true;
    this.bvh?.refit();
  }

  findTarget(eye, direction) {
    let best = null, score = Infinity;
    const walker = this.viewer.walker;
    for (const item of this.items) {
      if (Math.abs(walker.position.y - item.base) > .65) continue;
      // Aim at the opening, from either side. Clamp to the aperture so wide openings remain reachable.
      const delta = eye.clone().sub(item.start), along = Math.max(.08, Math.min(item.width - .08, delta.dot(item.axis)));
      const target = item.start.clone().addScaledVector(item.axis, along);
      target.y = Math.max(item.start.y + .12, Math.min(item.start.y + item.height - .12, eye.y));
      // Layered doors are selected at their actual handles, including after swinging
      // aside. This lets the visitor reach the screen and close either timber leaf.
      if (item.handle) target.copy(item.handle).applyMatrix4(item.parts[0].group.matrixWorld);
      const vector = target.clone().sub(eye), distance = vector.length();
      if (distance > 2.1 || distance < .05 || vector.normalize().dot(direction) < .6) continue;
      const ray = new THREE.Ray(eye, vector);
      // Static walls, furniture and frames occlude the interaction; the leaf itself must remain targetable.
      if (walker.bvh.raycastFirst(ray, THREE.DoubleSide, .04, distance - .12)) continue;
      const hit = this.bvh?.raycastFirst(ray, THREE.DoubleSide, .04, distance - .12);
      if (hit) {
        const vertex = this.geometry.index.getX(hit.faceIndex * 3) * 3;
        const owner = this.chunks.find(c => vertex >= c.offset && vertex < c.offset + c.source.length)?.owner;
        if (owner !== item.id) continue;
      }
      const value = distance + (1 - vector.dot(direction));
      if (value < score) { best = item; score = value; }
    }
    return best;
  }

  prompt() {
    if (performance.now() < this.messageUntil) return { text: this.message, disabled: true };
    if (!this.target) return null;
    const t = this.target;
    const action = t.partial ? (t.goal > .5 ? 'Return to half-open' : 'Open fully') : (t.goal > .5 ? 'Close' : 'Open');
    return { text: `${action} ${t.label.toLowerCase()}`, note: t.kind === 'window' && t.sill > .38 ? 'F or tap · raised sill; use a door for balcony access' : 'F or tap · accessible from either side' };
  }

  updateTarget() {
    const w = this.viewer.walker, eye = w.eyePosition(new THREE.Vector3());
    const direction = new THREE.Vector3(0, 0, -1).applyEuler(new THREE.Euler(w.pitch, w.yaw, 0, 'YXZ'));
    this.target = this.findTarget(eye, direction);
    this.viewer.hud?.setInteraction(this.prompt());
  }

  interact() {
    this.updateTarget();
    if (!this.target || performance.now() < this.messageUntil) return false;
    this.target.goal = this.target.goal > .5 ? 0 : 1;
    this.viewer.clearProbes?.();
    return true;
  }

  update(dt) {
    let changed = false;
    for (const item of this.items) {
      if (item.value === item.goal) continue;
      const before = item.value;
      // Small substeps prevent a swinging panel crossing the visitor between frames.
      const steps = Math.max(1, Math.ceil(dt / .015));
      for (let i = 0; i < steps; i++) {
        const old = item.value, sign = Math.sign(item.goal - old);
        item.value = old + sign * Math.min(Math.abs(item.goal - old), dt / steps * 1.7);
        this.pose(item); this.syncGeometry();
        if (this.bvh && this.viewer.walker.overlaps(this.bvh)) {
          item.value = old; item.goal = old; this.pose(item); this.syncGeometry();
          this.message = 'Step clear of the moving panel, then press F again'; this.messageUntil = performance.now() + 2200;
          break;
        }
      }
      changed ||= before !== item.value;
    }
    if (changed) { this.viewer.dirty = true; if (this.items.every(item => item.value === item.goal)) this.viewer.clearProbes?.(); }
    return changed;
  }

  dispose() { this.geometry?.dispose(); }
}
