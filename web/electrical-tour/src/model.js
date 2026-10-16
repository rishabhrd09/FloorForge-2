// Indexes and coordinate frames for the electrical model (scene Z-up metres).
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';
import { s2t } from './geom.js';

export class Model {
  constructor(data) {
    this.data = data;
    this.byId = new Map();
    for (const key of ['enclosures', 'devices', 'terminals', 'switches', 'regulators', 'points', 'boxes', 'circuits', 'conduits', 'conductors', 'rooms']) {
      for (const item of data[key]) { item._type = key; this.byId.set(item.id, item); }
    }
    this.sources = new Map(data.sources.map((s) => [s.id, s]));
    this.facts = new Map(data.facts.map((f) => [f.id, f]));
    this.assumptions = new Map(data.assumptions.map((a) => [a.id, a]));
    this.termsByOwner = new Map();
    for (const t of data.terminals) {
      const owner = t.enclosureId || t.boxId;
      if (!this.termsByOwner.has(owner)) this.termsByOwner.set(owner, []);
      this.termsByOwner.get(owner).push(t);
    }
    this.conductorsByConduit = new Map();
    this.conductorsByOwner = new Map();
    for (const k of data.conductors) {
      for (const c of k.conduits) {
        if (!this.conductorsByConduit.has(c)) this.conductorsByConduit.set(c, []);
        this.conductorsByConduit.get(c).push(k);
      }
      for (const tid of [k.from, k.to]) {
        const t = this.byId.get(tid);
        const owner = t && (t.enclosureId || t.boxId);
        if (!owner) continue;
        if (!this.conductorsByOwner.has(owner)) this.conductorsByOwner.set(owner, new Set());
        this.conductorsByOwner.get(owner).add(k);
      }
    }
    this.devicesByEnclosure = new Map();
    for (const d of data.devices) {
      if (!d.enclosureId) continue;
      if (!this.devicesByEnclosure.has(d.enclosureId)) this.devicesByEnclosure.set(d.enclosureId, []);
      this.devicesByEnclosure.get(d.enclosureId).push(d);
    }
    this.pointsByCircuit = new Map();
    for (const p of data.points) {
      if (!this.pointsByCircuit.has(p.circuitId)) this.pointsByCircuit.set(p.circuitId, []);
      this.pointsByCircuit.get(p.circuitId).push(p);
    }
    this._frames = new Map();
  }

  get(id) { return this.byId.get(id); }
  circuit(id) { return this.byId.get(id); }
  room(id) { return this.data.rooms.find((r) => r.id === id); }
  roomName(id) { const r = this.room(id); return r ? r.name : (id === null ? 'Outside' : id); }
  source(id) { return this.sources.get(id); }

  // Frame of a wall-mounted enclosure or box: x right (facing the wall), y up, z out of the face.
  frame(owner) {
    if (this._frames.has(owner.id)) return this._frames.get(owner.id);
    const m = new THREE.Matrix4();
    if (owner.mount) {
      const n = owner.mount.normal;
      const z = new THREE.Vector3(n[0], 0, -n[1]);
      const y = new THREE.Vector3(0, 1, 0);
      const x = y.clone().cross(z).normalize();
      m.makeBasis(x, y, z).setPosition(s2t(owner.mount.face));
    } else if (owner.kind === 'earth-pit') {
      m.makeBasis(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, -1), new THREE.Vector3(0, 1, 0)).setPosition(s2t(owner.position));
    } else {
      // ceiling box: z points down out of the soffit into the room
      m.makeBasis(new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, -1, 0)).setPosition(s2t(owner.position));
    }
    this._frames.set(owner.id, m);
    return m;
  }

  local(owner, p) { return new THREE.Vector3(p[0], p[1], p[2]).applyMatrix4(this.frame(owner)); }

  terminalWorld(tid) {
    const t = this.byId.get(tid);
    if (!t) return null;
    const owner = this.byId.get(t.enclosureId || t.boxId);
    return this.local(owner, t.local);
  }

  ownerOf(tid) { const t = this.byId.get(tid); return t ? this.byId.get(t.enclosureId || t.boxId) : null; }

  conductorsOf(owner) { return [...(this.conductorsByOwner.get(owner) || [])]; }

  circuitOfObject(obj) {
    if (!obj) return null;
    if (obj.circuitId) return obj.circuitId;
    if (obj._type === 'conduits') return obj.circuitIds[0] || null;
    if (obj._type === 'enclosures') return obj.circuitIds?.[0] || null;
    if (obj._type === 'boxes' && obj.pointId) return this.get(obj.pointId)?.circuitId || null;
    if (obj._type === 'devices') return obj.circuitId || this.get(obj.pointId)?.circuitId || this.byId.get(obj.enclosureId)?.circuitIds?.[0] || null;
    return null;
  }

  colour(key) {
    const c = this.data.colours[key] || this.data.colours.LIVE;
    return c;
  }

  // Human description of a conductor's role.
  roleText(k) {
    const c = k.circuitId && this.circuit(k.circuitId);
    const phase = c ? c.phase : null;
    switch (k.role) {
      case 'L1': return 'Phase L1 (R)';
      case 'L2': return 'Phase L2 (Y)';
      case 'L3': return 'Phase L3 (B)';
      case 'L': return phase ? `Phase (live), ${phase} phase` : 'Phase (live)';
      case 'SW': return 'Switched live';
      case 'REG': return 'Regulated live (fan feed)';
      case 'N': return 'Neutral (return)';
      case 'PE': return 'Protective earth';
      default: return k.role;
    }
  }

  endName(tid) {
    if (tid === 'DISCOM network') return 'DISCOM network (beyond the property)';
    const t = this.byId.get(tid);
    const owner = this.ownerOf(tid);
    if (!t || !owner) return tid;
    const ownerName = owner.label || owner.kind;
    return `${t.label} · ${ownerName}`;
  }
}
