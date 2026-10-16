// A single, temporary inspection opening in the finished wall or ceiling.
//
// The house meshes are solid surfaces, so a flush box or an embedded conduit is
// hidden behind the plaster face. To inspect one, we clip the architectural
// materials inside one oriented box (three.js clipIntersection) and always pair
// that hole with modelled recess geometry (back box, chase channel) that fills
// it. Nothing beyond the opened recess becomes visible, so there is no see-through
// view into the neighbouring room. Only walk mode uses openings; every other view
// restores the original materials.
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';

export class Apertures {
  constructor(viewer) {
    this.viewer = viewer;
    this.saved = new Map();
    this.box = null;
  }

  // box: { centre: Vector3, axes: [Vector3 x, y, z] (unit, Three space), half: [hx, hy, hz] }
  open(box) {
    this.close();
    const planes = [];
    box.axes.forEach((axis, i) => {
      const a = axis.clone().normalize(), c = a.dot(box.centre), h = box.half[i];
      planes.push(new THREE.Plane(a.clone(), -c - h));
      planes.push(new THREE.Plane(a.clone().negate(), c - h));
    });
    const bounds = new THREE.Box3();
    for (const s of [-1, 1]) for (const t of [-1, 1]) for (const u of [-1, 1]) {
      bounds.expandByPoint(box.centre.clone()
        .addScaledVector(box.axes[0], s * box.half[0])
        .addScaledVector(box.axes[1], t * box.half[1])
        .addScaledVector(box.axes[2], u * box.half[2]));
    }
    bounds.expandByScalar(.01);
    const touched = new Set();
    for (const mesh of this.viewer.meshes) {
      if (!mesh.visible) continue;
      const g = mesh.geometry;
      if (!g.boundingBox) g.computeBoundingBox();
      if (!g.boundingBox.intersectsBox(bounds)) continue;
      const list = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      for (const m of list) touched.add(m);
    }
    for (const m of touched) {
      this.saved.set(m, { planes: m.clippingPlanes, intersection: m.clipIntersection, shadows: m.clipShadows });
      m.clippingPlanes = planes;
      m.clipIntersection = true;
      m.clipShadows = true;
      m.needsUpdate = true;
    }
    this.box = box;
    this.viewer.dirty = true;
    return touched.size;
  }

  close() {
    for (const [m, s] of this.saved) {
      m.clippingPlanes = s.planes;
      m.clipIntersection = s.intersection;
      m.clipShadows = s.shadows;
      m.needsUpdate = true;
    }
    const had = this.saved.size > 0;
    this.saved.clear();
    this.box = null;
    if (had) this.viewer.dirty = true;
  }

  get active() { return Boolean(this.box); }
}

// Oriented opening box for a wall-mounted enclosure: from slightly proud of the
// finished face back to the recess depth, inset so the box rim covers the cut.
export function enclosureOpening(group, width, height, depth, { inset = .0015, proud = .004 } = {}) {
  const m = group.matrixWorld;
  const x = new THREE.Vector3().setFromMatrixColumn(m, 0).normalize();
  const y = new THREE.Vector3().setFromMatrixColumn(m, 1).normalize();
  const z = new THREE.Vector3().setFromMatrixColumn(m, 2).normalize();
  const origin = new THREE.Vector3().setFromMatrixPosition(m);
  const centre = origin.clone().addScaledVector(z, (proud - depth) / 2);
  return { centre, axes: [x, y, z], half: [width / 2 - inset, height / 2 - inset, (depth + proud) / 2] };
}

// Opening along a straight chase segment (wall or ceiling). `normal` points out of the surface.
export function chaseOpening(a, b, normal, width, depth, { proud = .004 } = {}) {
  const dir = b.clone().sub(a);
  const length = dir.length();
  dir.normalize();
  const z = normal.clone().normalize();
  const y = z.clone().cross(dir).normalize();
  const x = dir;
  const centre = a.clone().add(b).multiplyScalar(.5).addScaledVector(z, (proud - depth) / 2);
  return { centre, axes: [x, y, z], half: [length / 2, width / 2, (depth + proud) / 2] };
}
