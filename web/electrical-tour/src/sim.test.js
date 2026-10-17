// Switching logic of the electrical edition, run against the published model:
// operating one control changes only its own points and conductors, protective
// devices isolate exactly what they feed, and earth never carries load current.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { Simulation } from './sim.js';

const model = JSON.parse(readFileSync(new URL('../../../examples/gallery/my-desired-home-electrical/electrical-model.json', import.meta.url), 'utf8'));
const byId = new Map([...model.devices, ...model.circuits, ...model.points, ...model.switches].map((x) => [x.id, x]));
const circuitOf = (pointId) => byId.get(pointId).circuitId;

function changed(before, after) {
  const points = Object.keys(after.points).filter((id) => after.points[id] !== before.points[id]);
  const conductors = Object.keys(after.conductors).filter((id) =>
    after.conductors[id].live !== before.conductors[id].live || after.conductors[id].current !== before.conductors[id].current);
  return { points, conductors };
}

test('the default state: every device closed, lights on, fans and outlets off', () => {
  const sim = new Simulation(model);
  const snap = sim.snapshot();
  assert.ok(Object.values(snap.circuits).every(Boolean));
  const lights = ['downlight', 'cove', 'mirror-light', 'undercabinet'];
  for (const p of model.points) assert.equal(snap.points[p.id], lights.includes(p.kind), `${p.id} ${p.kind}`);
  for (const k of model.conductors) {
    const st = snap.conductors[k.id];
    if (k.role === 'SW' || k.role === 'REG') assert.equal(st.live, k.controls.every((s) => sim.switchClosed(s)), k.id);
    if (k.role === 'L' && k.circuitId) assert.equal(st.live, true, k.id);
  }
});

test('with every switch off, circuits stay live but no load runs', () => {
  const sim = new Simulation(model);
  for (const s of model.switches) if (sim.switchClosed(s.id)) sim.toggleSwitch(s.id);
  const snap = sim.snapshot();
  assert.ok(Object.values(snap.circuits).every(Boolean));
  for (const p of model.points) assert.equal(snap.points[p.id], false, p.id);
  for (const k of model.conductors.filter((x) => x.role === 'SW' || x.role === 'REG')) assert.equal(snap.conductors[k.id].live, false, k.id);
});

test('a light switch changes only its own points and the conductors that feed them', () => {
  const sw = model.switches.find((s) => s.points.length > 1 && s.points.every((p) => byId.get(p).kind === 'downlight'));
  const sim = new Simulation(model);
  for (const s of model.switches) if (sim.switchClosed(s.id)) sim.toggleSwitch(s.id);
  const before = sim.snapshot();
  sim.toggleSwitch(sw.id);
  const after = sim.snapshot();
  const diff = changed(before, after);
  assert.deepEqual(diff.points.sort(), [...sw.points].sort());
  const circuit = circuitOf(sw.points[0]);
  assert.ok(diff.conductors.length > 0);
  for (const id of diff.conductors) {
    const k = model.conductors.find((c) => c.id === id);
    assert.ok(k.serves.some((p) => sw.points.includes(p)), `${id} does not serve the switched points`);
    assert.notEqual(k.role, 'PE');
    if (k.role === 'SW' || k.role === 'REG') assert.deepEqual(k.controls, [sw.id]);
    if (k.circuitId) assert.equal(k.circuitId, circuit);
  }
  // the phase conductors were already live: only their load current changes
  for (const id of diff.conductors) {
    const role = model.conductors.find((c) => c.id === id).role;
    if (role === 'L' || role === 'N') assert.equal(before.conductors[id].live, after.conductors[id].live);
  }
});

test('a fan runs only with its switch on and its regulator above zero', () => {
  const fan = model.points.find((p) => p.kind === 'fan');
  const sw = fan.controls[0];
  const reg = model.regulators.find((r) => r.id === fan.regulator);
  const feed = model.conductors.find((k) => k.role === 'REG' && k.serves.includes(fan.id));
  const series = model.conductors.find((k) => k.role === 'SW' && k.to === byId.get(reg.deviceId).terminals.in);
  const sim = new Simulation(model);
  assert.equal(sim.pointSupplied(fan.id), false);
  sim.toggleSwitch(sw);
  assert.equal(sim.pointSupplied(fan.id), true);
  assert.equal(sim.conductorStatus(feed.id).live, true);
  sim.setRegulator(reg.id, 0);
  assert.equal(sim.pointSupplied(fan.id), false);
  assert.equal(sim.conductorStatus(series.id).live, true, 'switch output still reaches the regulator');
  assert.equal(sim.conductorStatus(feed.id).live, false, 'regulator off: the fan lead is dead');
  sim.setRegulator(reg.id, 9);
  assert.equal(sim.state.regulators[reg.id], reg.steps);
});

test('an outgoing MCB isolates only its own circuit', () => {
  const circuit = model.circuits.find((c) => c.kind === 'lighting');
  const sim = new Simulation(model);
  for (const s of model.switches) if (!sim.switchClosed(s.id)) sim.toggleSwitch(s.id);
  const before = sim.snapshot();
  sim.toggleDevice(circuit.mcb);
  const after = sim.snapshot();
  for (const c of model.circuits) assert.equal(after.circuits[c.id], c.id !== circuit.id, c.id);
  const diff = changed(before, after);
  assert.ok(diff.points.length > 0);
  for (const id of diff.points) assert.equal(circuitOf(id), circuit.id);
  for (const k of model.conductors.filter((x) => x.circuitId === circuit.id && ['L', 'SW', 'REG'].includes(x.role))) {
    assert.equal(after.conductors[k.id].live, false, k.id);
  }
});

test('the first-floor isolator and the sub-main MCB cut only first-floor circuits', () => {
  const isolator = model.devices.find((d) => d.kind === 'isolator2p');
  const sub = model.circuits.find((c) => c.id === 'SUB');
  for (const device of [isolator.id, sub.mcb]) {
    const sim = new Simulation(model);
    sim.toggleDevice(device);
    for (const c of model.circuits) {
      const downstream = c.chain.includes(device);
      assert.equal(sim.circuitLive(c.id), !downstream, `${device} → ${c.id}`);
      if (c.id === 'SUB') assert.equal(downstream, device === sub.mcb);
      else assert.equal(downstream, c.floor === 1, c.id);
    }
  }
});

test('the main switch and the RCCB isolate the whole installation', () => {
  for (const kind of ['mcb4p', 'rccb4p']) {
    const sim = new Simulation(model);
    const device = model.devices.find((d) => d.kind === kind).id;
    sim.toggleDevice(device);
    assert.ok(model.circuits.every((c) => !sim.circuitLive(c.id)), kind);
    let dead = 0;
    for (const k of model.conductors.filter((x) => ['L', 'L1', 'L2', 'L3'].includes(x.role))) {
      const chain = k.chain || model.circuits.find((c) => c.id === k.circuitId)?.chain || [];
      const live = sim.conductorStatus(k.id).live;
      assert.equal(live, !chain.includes(device), `${kind}: ${k.id} ${k.kind}`);
      if (k.kind === 'service' || k.kind === 'meter-tail') assert.ok(live, `${k.id}: the supply side stays live`);
      dead += live ? 0 : 1;
    }
    assert.ok(dead > model.circuits.length, `${kind} leaves the outgoing phase conductors dead`);
  }
});

test('an earth-leakage fault trips the RCCB, which must be reset deliberately', () => {
  const sim = new Simulation(model);
  const rccb = model.devices.find((d) => d.kind === 'rccb4p');
  const out = sim.injectFault('G2', 'leakage');
  assert.equal(out.device, rccb.id);
  assert.ok(model.circuits.every((c) => !sim.circuitLive(c.id)));
  sim.toggleDevice(rccb.id);            // tripped → reset to OFF
  assert.equal(sim.closed(rccb.id), false);
  sim.toggleDevice(rccb.id);            // OFF → ON
  assert.ok(model.circuits.every((c) => sim.circuitLive(c.id)));
  assert.equal(sim.state.faults.G2, null);
});

test('an overload trips the circuit MCB, not the RCCB', () => {
  const sim = new Simulation(model);
  const circuit = model.circuits.find((c) => c.id === 'F1');
  const out = sim.injectFault('F1', 'overload');
  assert.equal(out.device, circuit.mcb);
  assert.equal(sim.circuitLive('F1'), false);
  assert.ok(model.circuits.filter((c) => c.id !== 'F1').every((c) => sim.circuitLive(c.id)));
});

test('protective conductors never carry load current, neutrals only with a load running', () => {
  const sim = new Simulation(model);
  for (const s of model.switches) if (!sim.switchClosed(s.id)) sim.toggleSwitch(s.id);
  const snap = sim.snapshot();
  for (const k of model.conductors) {
    const st = snap.conductors[k.id];
    if (k.role === 'PE') assert.deepEqual([st.live, st.current], [false, false], k.id);
    if (k.role === 'N') assert.equal(st.live, false, k.id);
    if (k.role === 'N' && k.serves.length) assert.equal(st.current, k.serves.some((p) => snap.points[p]), k.id);
  }
});
