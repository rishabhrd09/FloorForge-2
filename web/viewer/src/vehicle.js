// Optional parked vehicle: independent geometry, collision and presentation state.
import { MeshBVH } from 'three-mesh-bvh';
import { buildBuckets } from './scene-builder.js';

export class ParkedVehicle {
  constructor(viewer, nodes) {
    this.viewer = viewer;
    this.key = `floorforge:parked-car:${viewer.data.planHash || 'preview'}`;
    this.visible = true;
    try { this.visible = localStorage.getItem(this.key) !== 'hidden'; } catch { /* file previews may deny storage */ }
    const buckets = buildBuckets({ ...viewer.data, nodes }, viewer.materials);
    this.meshes = buckets.map(b => { const m = viewer.addBucket(b); m.userData.vehicle = true; return m; });
    this.geometry = viewer.mergeForCollision(buckets.filter(b => b.collide).map(b => b.geometry));
    this.bvh = new MeshBVH(this.geometry, { maxLeafSize: 8 });
    this.apply();
  }
  apply() {
    this.meshes.forEach(m => { m.visible = this.visible; });
    this.viewer.walker.optionalBVHs = this.visible ? [this.bvh] : [];
    this.viewer.dirty = true;
  }
  setVisible(visible) {
    const v = this.viewer;
    visible = Boolean(visible);
    if (visible && !this.visible && v.mode === 'walk' && v.walker.overlaps(this.bvh)) {
      v.onStatus('Step out of the parking space before showing the car.');
      return false;
    }
    this.visible = visible;
    this.apply();
    try { localStorage.setItem(this.key, visible ? 'visible' : 'hidden'); } catch { /* session-only fallback */ }
    v.clearProbes();
    v.onCarChange?.(visible);
    v.onStatus(visible ? 'Škoda Kylaq parked in the right bay.' : 'Car hidden · parking space is clear.');
    return true;
  }
  dispose() { this.geometry.dispose(); }
}
