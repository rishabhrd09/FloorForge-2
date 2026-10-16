// Educational supply-state model for the electrical edition. It answers only
// "is this part connected to the supply through closed devices?" and "would it
// carry the load current of a point that is switched on?". It does not compute
// voltages, currents, fault levels or trip times.

export function createState(model) {
  const state = { devices: {}, switches: {}, regulators: {}, faults: {}, tripped: {}, utility: true };
  for (const d of model.devices) if (d.operable) state.devices[d.id] = d.defaultOn !== false;
  for (const s of model.switches) state.switches[s.id] = Boolean(s.defaultOn);
  for (const r of model.regulators || []) state.regulators[r.id] = r.defaultStep ?? 3;
  return state;
}

export class Simulation {
  constructor(model, state = createState(model)) {
    this.model = model;
    this.state = state;
    this.devices = new Map(model.devices.map((d) => [d.id, d]));
    this.circuits = new Map(model.circuits.map((c) => [c.id, c]));
    this.points = new Map(model.points.map((p) => [p.id, p]));
    this.switches = new Map(model.switches.map((s) => [s.id, s]));
    this.regulators = new Map((model.regulators || []).map((r) => [r.id, r]));
    this.conductors = new Map(model.conductors.map((c) => [c.id, c]));
  }

  closed(deviceId) {
    const d = this.devices.get(deviceId);
    if (!d) return false;
    if (!d.operable) return true;
    return Boolean(this.state.devices[deviceId]) && !this.state.tripped[deviceId];
  }

  // Every protective or isolating device between the utility service and a circuit is closed.
  circuitLive(circuitId) {
    const c = this.circuits.get(circuitId);
    if (!c || !this.state.utility) return false;
    return c.chain.every((id) => this.closed(id));
  }

  switchClosed(switchId) { return Boolean(this.state.switches[switchId]); }

  regulatorStep(regId) { return this.state.regulators[regId] ?? 0; }

  // A point is supplied when its circuit is live and its own control (if any) is closed.
  pointSupplied(pointId) {
    const p = this.points.get(pointId);
    if (!p || !this.circuitLive(p.circuitId)) return false;
    for (const s of p.controls || []) if (!this.switchControlClosed(s)) return false;
    if (p.regulator && this.regulatorStep(p.regulator) <= 0) return false;
    return true;
  }

  // Two-way (staircase) controls are closed when both switches agree.
  switchControlClosed(control) {
    if (typeof control === 'string') return this.switchClosed(control);
    if (control.type === 'two-way') return this.switchClosed(control.a) === this.switchClosed(control.b);
    return false;
  }

  // Load operating: supplied, and an appliance outlet is treated as "in use" only when its own switch is on.
  pointOperating(pointId) { return this.pointSupplied(pointId); }

  conductorStatus(conductorId) {
    const k = this.conductors.get(conductorId);
    if (!k) return null;
    const serves = k.serves || [];
    const anyLoad = serves.some((p) => this.pointOperating(p));
    let live = false;
    switch (k.role) {
      case 'service':
        live = this.state.utility; break;
      case 'L': case 'L1': case 'L2': case 'L3':
        // service cable and meter tails have an empty chain: live whenever the utility supplies
        live = this.upstreamLive(k); break;
      case 'SW':
        live = this.upstreamLive(k) && (k.controls || []).every((s) => this.switchControlClosed(s)); break;
      case 'REG':
        live = this.upstreamLive(k) && (k.controls || []).every((s) => this.switchControlClosed(s)) && this.regulatorStep(k.regulator) > 0; break;
      case 'STRAP':
        live = this.upstreamLive(k); break;
      case 'N': case 'PE':
        live = false; break;
      default:
        live = false;
    }
    const current = k.role === 'PE' ? false : (k.role === 'N' ? anyLoad : live && anyLoad);
    return { live, current, role: k.role };
  }

  // Conductors upstream of the circuit's own device follow the devices listed on the conductor.
  upstreamLive(k) {
    if (!this.state.utility) return false;
    return (k.chain || this.circuits.get(k.circuitId)?.chain || []).every((id) => this.closed(id));
  }

  toggleDevice(id) {
    const d = this.devices.get(id);
    if (!d?.operable) return false;
    if (this.state.tripped[id]) { this.state.tripped[id] = false; this.state.devices[id] = false; return true; }
    this.state.devices[id] = !this.state.devices[id];
    if (this.state.devices[id]) for (const [c, f] of Object.entries(this.state.faults)) if (f && this.protects(id, c)) this.state.faults[c] = null;
    return true;
  }

  toggleSwitch(id) { if (!this.switches.has(id)) return false; this.state.switches[id] = !this.state.switches[id]; return true; }

  setRegulator(id, step) {
    const r = this.regulators.get(id);
    if (!r) return false;
    this.state.regulators[id] = Math.max(0, Math.min(r.steps, Math.round(step)));
    return true;
  }

  protects(deviceId, circuitId) { return this.circuits.get(circuitId)?.chain.includes(deviceId); }

  // Demonstration of which protective function would isolate a fault. No physics is modelled.
  injectFault(circuitId, kind) {
    const c = this.circuits.get(circuitId);
    if (!c || !this.circuitLive(circuitId)) return null;
    const chain = c.chain.map((id) => this.devices.get(id));
    let device = null;
    if (kind === 'leakage') device = [...chain].reverse().find((d) => d.residual);
    else if (kind === 'overload' || kind === 'short') device = [...chain].reverse().find((d) => d.overcurrent);
    if (!device) return { circuitId, kind, device: null };
    this.state.faults[circuitId] = kind;
    this.state.tripped[device.id] = true;
    return { circuitId, kind, device: device.id };
  }

  clearFault(circuitId) { this.state.faults[circuitId] = null; }

  // Everything a view needs for one frame of state, as plain data.
  snapshot() {
    const points = {}, conductors = {}, circuits = {}, devices = {};
    for (const id of this.circuits.keys()) circuits[id] = this.circuitLive(id);
    for (const id of this.points.keys()) points[id] = this.pointSupplied(id);
    for (const id of this.conductors.keys()) conductors[id] = this.conductorStatus(id);
    for (const [id, d] of this.devices) devices[id] = { closed: this.closed(id), tripped: Boolean(this.state.tripped[id]), operable: Boolean(d.operable) };
    return { points, conductors, circuits, devices };
  }
}
