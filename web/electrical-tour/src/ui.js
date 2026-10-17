// Sidebar and inspector rendering. Pure DOM from the model + simulation snapshot.
const $ = (id) => document.getElementById(id);
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const KIND_NAME = {
  conductors: 'Conductor', terminals: 'Terminal', devices: 'Device', enclosures: 'Enclosure', points: 'Point',
  conduits: 'Conduit', boxes: 'Box', circuits: 'Circuit', switches: 'Switch', regulators: 'Regulator',
};

export function phaseChip(p) { return p && 'RYB'.includes(p) ? `<span class="ph ${p}">${p}</span>` : '<span class="ph" style="background:#7d8a83">–</span>'; }

export function renderCircuits(model, ui) {
  const groups = [
    { title: 'Main DB · ground floor', list: model.data.circuits.filter((c) => c.floor === 0 && c.id !== 'SUB') },
    { title: 'Submain', list: model.data.circuits.filter((c) => c.id === 'SUB') },
    { title: 'First-floor sub-DB', list: model.data.circuits.filter((c) => c.floor === 1 && c.id !== 'SUB') },
  ];
  const snap = ui.snapshot;
  $('circuits').innerHTML = groups.map((g) => `<div class="kicker">${esc(g.title)}</div>` + g.list.map((c) => {
    const kind = { lighting: '💡', power: '🔌', geyser: '♨', submain: '⇪' }[c.kind] || '';
    return `<button class="cbtn" data-circuit="${esc(c.id)}" aria-pressed="${ui.circuitId === c.id}" title="${esc(c.label)}">
      <span class="id">${esc(c.id)}</span><span class="what">${kind} ${esc(c.short)}</span><span>${phaseChip(c.phase)} <i class="dot ${snap?.circuits?.[c.id] ? 'on' : ''}" title="${snap?.circuits?.[c.id] ? 'Supplied' : 'Not supplied'}"></i></span></button>`;
  }).join('')).join('');
}

function factRefs(model, ids) {
  return ids.filter(Boolean).map((id) => {
    const f = model.facts.get(id);
    if (f) {
      const s = model.source(f.source);
      return `<a class="ref" href="${esc(s?.url)}" target="_blank" rel="noopener" title="${esc(f.text)}">${esc(sourceShort(s))} ${esc(f.ref)}</a>`;
    }
    const a = model.assumptions.get(id);
    if (a) return `<span class="ref assume" title="${esc(a.text)}">Assumption: ${esc(a.title)}</span>`;
    return '';
  }).join('');
}

function sourceShort(s) {
  if (!s) return '';
  return ({ 'S-CPWD': 'CPWD 2023', 'S-WM': 'Wireman TT', 'S-E9': 'Easy9 BQT58820', 'S-E9DS': 'Easy9 datasheets', 'S-LG': 'Legrand India',
    'S-CEA': 'CEA 2023', 'S-CEAM': 'CEA meters', 'S-IS732': 'IS 732:2019', 'S-IS732-1989': 'IS 732:1989', 'S-IS1293': 'IS 1293',
    'S-IS9537': 'IS 9537-3', 'S-PC': 'Polycab', 'S-SUPPLY': 'Supply codes', 'S-BIS-TX': 'BIS/IS 12360', 'S-VID': 'Video' })[s.id] || s.id;
}

export function renderSources(model) {
  $('sources').innerHTML = model.data.sources.map((s) => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a> — ${esc(s.publisher)}${s.note ? `. <span style="color:#6b7c72">${esc(s.note)}</span>` : ''}</li>`).join('');
  $('assumptions').innerHTML = model.data.assumptions.map((a) => `<li><b>${esc(a.title)}.</b> ${esc(a.text)} <i>Confirm with: ${esc(a.confirm)}.</i></li>`).join('');
  $('not-modelled').innerHTML = model.data.notModelled.map((n) => `<li><b>${esc(n.title)}.</b> ${esc(n.why)}</li>`).join('');
  const notes = model.data.notes || [];
  $('placement-notes').innerHTML = notes.length ? notes.map((n) => `<li>${esc(n)}</li>`).join('')
    : '<li>Every proposed point found a clear position.</li>';
}

function stateText(model, sim, obj) {
  if (!obj) return '';
  if (obj._type === 'conductors') {
    const st = sim.conductorStatus(obj.id);
    if (obj.role === 'PE') return 'Protective earth — carries no normal load current';
    if (obj.role === 'N') return st.current ? 'Neutral — carrying return current' : 'Neutral — no load current at present';
    if (st.live) return st.current ? 'Live, carrying load current' : 'Live, no load operating';
    const upstream = (obj.chain || model.circuit(obj.circuitId)?.chain || []).map((id) => model.get(id)).find((d) => d && !sim.closed(d.id));
    if (upstream) return `Not live — ${upstream.label} is ${sim.state.tripped[upstream.id] ? 'tripped' : 'OFF'}`;
    if ((obj.controls || []).some((c) => !sim.switchControlClosed(c))) return 'Not live — its switch is OFF';
    if (obj.regulator && sim.regulatorStep(obj.regulator) === 0) return 'Not live — regulator at OFF';
    return 'Not live';
  }
  if (obj._type === 'points') return sim.pointSupplied(obj.id) ? 'Supplied — operating' : 'Not supplied / switched off';
  if (obj._type === 'circuits') return sim.circuitLive(obj.id) ? 'Supplied' : 'Not supplied';
  if (obj._type === 'devices' && obj.operable) return sim.state.tripped[obj.id] ? 'Tripped' : sim.closed(obj.id) ? 'Closed (ON)' : 'Open (OFF)';
  if (obj._type === 'devices' && ['switch', 'switch16', 'local-mcb'].includes(obj.kind)) return sim.switchClosed(obj.switchId) ? 'ON (closed)' : 'OFF (open)';
  if (obj._type === 'devices' && obj.kind === 'regulator') return `Step ${sim.regulatorStep(obj.regulatorId)} of 5`;
  return '';
}

// Rows for the in-scene label (short) and the inspector (fuller).
export function describe(model, sim, obj) {
  if (!obj) return null;
  const c = obj.circuitId ? model.circuit(obj.circuitId) : null;
  const circuitText = (cc) => cc ? `${cc.id} · ${cc.short}` : 'Service (before the main switch)';
  const rows = [], text = [], refs = [];
  let title = obj.label || obj.id, type = KIND_NAME[obj._type] || 'Item';
  switch (obj._type) {
    case 'conductors': {
      title = `${obj.circuitId || 'Service'} · ${model.roleText(obj)}`;
      rows.push(['Circuit', circuitText(c)], ['Role', model.roleText(obj)],
        ['Phase', c ? c.phase : ({ L1: 'R', L2: 'Y', L3: 'B', N: 'N' }[obj.role] || '—')], ['State', stateText(model, sim, obj)],
        ['From', model.endName(obj.from)], ['To', model.endName(obj.to)],
        ['Size', obj.size ? `${obj.size} mm² Cu (CPWD minimum)` : 'By designer'], ['Colour', model.colour(obj.colour).name]);
      const roleWhy = {
        L: 'Phase (live) conductor from the circuit MCB. Only live conductors pass through switches and MCBs (CPWD 3.11.5; CEA Reg. 17).',
        L1: 'One of the three service phases. It stays live up to the meter and the main switch even when the house is switched off.',
        L2: 'One of the three service phases. It stays live up to the meter and the main switch even when the house is switched off.',
        L3: 'One of the three service phases. It stays live up to the meter and the main switch even when the house is switched off.',
        SW: 'Switched live: the switch (or local MCB) output that energises only its own point when ON. CPWD switches are ON when the knob is down.',
        REG: 'Regulated live from the fan regulator, in series after the fan switch (IS 732:1989 C-8.1). Only the installation side is shown — not the fan’s internal motor wiring.',
        N: 'Neutral: the normal return path. It runs in the same conduit as its phase (CPWD 5.4.3(g)) and back to the neutral bar after the RCCB, so the RCCB can compare outgoing and returning current. It is never switched or fused (CEA Reg. 17).',
        PE: 'Protective earth: connects exposed metal parts and socket earth pins to the earthing system so a fault can be cleared. It never carries normal return current (CPWD 5.4.4; CEA Reg. 43).',
      };
      text.push(roleWhy[obj.role] || '');
      if (obj.conduits.length) text.push(`Runs through ${obj.conduits.length} concealed conduit${obj.conduits.length > 1 ? 's' : ''}: ${obj.conduits.join(', ')}.`);
      refs.push('F-COLOUR', obj.role === 'PE' ? 'F-PE-CONDUIT' : obj.role === 'N' ? 'F-BUNCH' : 'F-NEUTRAL', obj.size ? 'F-COND' : 'A-RATINGS');
      break;
    }
    case 'terminals': {
      const owner = model.ownerOf(obj.id);
      const lands = model.data.conductors.filter((k) => k.from === obj.id || k.to === obj.id);
      title = obj.label;
      rows.push(['In', owner?.label || owner?.id], ['Role', { P: 'Phase connector', N: 'Neutral connector', E: 'Earth', SW: 'Switched live', REG: 'Regulated live', L: 'Live', L1: 'Phase R', L2: 'Phase Y', L3: 'Phase B' }[obj.role] || obj.role],
        ['Wires', lands.map((k) => `${k.circuitId || 'svc'} ${k.role}`).join(', ') || '—']);
      const st = lands.length ? sim.conductorStatus(lands[0].id) : null;
      if (st) rows.push(['State', obj.role === 'E' ? 'Earth: no normal current' : st.live ? 'Live in the simulation' : obj.role === 'N' ? (st.current ? 'Neutral: return current' : 'Neutral') : 'Not live']);
      text.push(obj.role === 'P' || obj.role === 'N' || obj.role === 'E'
        ? 'The circuit lands on separate phase, neutral and earth connectors in the first box it reaches; point wiring starts from them (CPWD 3.5.6).'
        : 'Device terminal. Strip length about 10–12 mm; screw tightened to the maker’s torque (Easy9 1.5–2 N·m).');
      refs.push('F-TERM', 'F-E9');
      break;
    }
    case 'devices': {
      title = obj.label;
      const enc = model.get(obj.enclosureId);
      rows.push(['In', enc?.label || '—']);
      if (obj.circuitId) rows.push(['Circuit', circuitText(model.circuit(obj.circuitId))]);
      if (obj.phase) rows.push(['Phase', obj.phase]);
      if (obj.standard) rows.push(['Standard', obj.standard]);
      rows.push(['Rating', obj.rating?.sensitivity ? `${obj.rating.sensitivity}; current by designer` : 'By designer (not calculated)']);
      const st = stateText(model, sim, obj);
      if (st) rows.push(['State', st]);
      const why = {
        mcb: 'Single-pole MCB: opens the phase on overload or short circuit for its own circuit (CEA Reg. 37(4)). The neutral is not broken.',
        mcb4p: 'Incoming 4-pole MCB: isolates R, Y, B and N together and protects the installation (CEA Reg. 37(2)).',
        rccb4p: 'RCCB: compares the current in R, Y, B and N. Any leakage to earth above 30 mA makes it trip (CEA Reg. 44; CPWD G.3.1).',
        isolator2p: 'Linked isolator for the first-floor board: switches phase and neutral together.',
        switch: 'Single-pole modular switch in the live conductor, ON with the knob down (CPWD 3.14.1).',
        switch16: '16 A switch controlling its socket on the live side (CPWD 3.11.5, 3.11.7).',
        regulator: 'Two-module step regulator in series after the fan switch (CPWD 3.16.1(h)); its metal body is earthed (CPWD 3.16.3).',
        socket6: 'Shuttered 6 A 3-pin socket (IS 1293): live and neutral contacts below, earth contact above.',
        socket16: 'Shuttered 16 A 3-pin socket (IS 1293) on its own switch.',
        'local-mcb': 'Local 16 A MCB controlling the water-heater socket (CPWD 3.11.6(c)).',
        'neutral-bar': 'Neutral bar: each outgoing circuit has its own neutral terminal; all neutrals here return through the RCCB.',
        'earth-bar': 'Earth bar and main earthing terminal: protective conductors of every circuit and the two earthing conductors meet here.',
        busbar: 'Comb busbar: feeds the MCB inputs; each tooth is on one phase.',
        meter: 'DISCOM meter: owned and sealed by the licensee (CEA metering regulations).',
      };
      text.push(why[obj.kind] || '');
      refs.push(...({ mcb: ['F-CEA-MAIN', 'F-E9-DIM'], mcb4p: ['F-CEA-MAIN', 'F-MAINBOARD'], rccb4p: ['F-CEA-RCD', 'F-RCD'], switch: ['F-SWITCH-DOWN', 'F-NEUTRAL'],
        regulator: ['F-FAN', 'F-REG-EARTH'], socket6: ['F-IS1293', 'F-SOCKET-TYPE'], socket16: ['F-IS1293', 'F-SOCKET-CTRL'], 'local-mcb': ['F-GEYSER'],
        meter: ['F-CEA-METER'], 'neutral-bar': ['F-E9'], 'earth-bar': ['F-CEA-EARTH', 'F-PE-CONDUIT'] }[obj.kind] || []));
      break;
    }
    case 'enclosures': {
      title = obj.label;
      type = { switchboard: 'Room switchboard', 'socket-plate': 'Socket plate', 'geyser-mcb': 'Geyser control', 'geyser-outlet': 'Water-heater socket',
        'main-db': 'Main distribution board', 'sub-db': 'Sub-distribution board', 'loose-wire-box': 'Loose-wire box', meter: 'Service meter' }[obj.kind] || type;
      const m = obj.mount;
      rows.push(['Room', model.roomName(obj.roomId) + (obj.exterior ? ' (outside face)' : '')]);
      rows.push(['Mounted', obj.exterior ? 'Surface box on the external wall' : `Flush in ${(m.wallThickness * 1000).toFixed(0)} mm wall${m.finish > .02 ? ' (over tiles/panel)' : ''}`]);
      rows.push(['Box bottom', `${(m.face[2] - obj.floor * model.data.floorHeight - obj.size.h / 2).toFixed(2)} m above floor`]);
      rows.push(['Size', `${(obj.size.w * 1000).toFixed(0)} × ${(obj.size.h * 1000).toFixed(0)} mm${obj.plateModules ? ` · ${obj.plateModules}-module plate` : ''}`]);
      if (obj.circuitIds?.length) rows.push(['Circuits', obj.circuitIds.join(', ')]);
      const why = {
        switchboard: 'Lighting circuit board: the circuit lands on P/N/E connectors (CPWD 3.5.6), switches in the live feed ceiling lights and fans, and the regulator sits in series after the fan switch. Box bottom at 1.1 m (CPWD 3.15.1).',
        'socket-plate': 'Power circuit outlet with its own control switch (CPWD 3.11.7). Light and power wiring use separate conduits (CPWD 3.2.6).',
        'geyser-mcb': 'Water-heater control: a 16 A MCB in a modular box at 1.1 m (CPWD 3.11.6(c)), on an independent circuit (CPWD 3.10.3).',
        'geyser-outlet': 'Water-heater socket at least 2 m above floor near the assumed heater position (CPWD 3.11.6(c)); the heater itself is not modelled.',
        'main-db': 'Main board: incoming 4-pole MCB and 30 mA RCCB, then outgoing MCBs on a comb busbar (CPWD 3.20.9; CEA Regs. 37, 44). 1 m clear in front (CEA Reg. 39).',
        'sub-db': 'First-floor board fed by the submain: 2-pole isolator and single-pole MCBs.',
        'loose-wire-box': 'Outgoing phase/neutral/earth terminal blocks for every circuit (CPWD 3.18.2, Fig. 8).',
        meter: 'Sealed three-phase DISCOM meter, readable from outside the house; the cable from it is live whenever the DISCOM supply is on.',
      };
      text.push(why[obj.kind] || '');
      refs.push(...({ switchboard: ['F-BOX-H', 'F-TERM', 'F-BOX', 'F-LG-DIM'], 'socket-plate': ['F-SOCKET-H', 'F-SOCKET-CTRL', 'F-POWER-CCT'], 'geyser-mcb': ['F-GEYSER'],
        'geyser-outlet': ['F-GEYSER', 'A-GEYSER'], 'main-db': ['F-MAINBOARD', 'F-CEA-CLEAR', 'F-E9', 'F-E9-DIM', 'A-MAINDB'], 'sub-db': ['A-SUBDB', 'F-E9-DIM'],
        'loose-wire-box': ['F-DB-PREWIRED'], meter: ['F-CEA-METER', 'A-METER'] }[obj.kind] || []));
      break;
    }
    case 'points': {
      title = obj.label;
      const sw = obj.controls?.length ? model.get(obj.controls[0]) : null;
      rows.push(['Circuit', circuitText(c)], ['Controlled by', sw ? `${sw.label} switch` : 'Its own switch / MCB'], ['State', stateText(model, sim, obj)], ['Position', obj.provenance]);
      if (obj.kind === 'fan') rows.push(['Fan', `${obj.sweep} mm sweep, blades about 2.70 m above floor`]);
      const why = {
        fan: `Ceiling fan point: the regulated live, neutral and protective earth reach a connector in the fan box, which hangs from a 12 mm MS hook cast in the slab (CPWD 3.16.1, Fig. 4). ${obj.basis || ''}. The fan’s internal wiring is not shown.`,
        downlight: 'Ceiling light point from the architectural scene: switched live, neutral and protective earth reach a point box in the slab above the fitting.',
        cove: 'Cove LED strip in the false-ceiling band; its driver connection box is assumed in the slab above the cove pocket.',
        exhaust: 'Exhaust fan in an external-wall opening, fed by flexible cord from an exhaust-fan point beside it (CPWD 3.16.2).',
        socket6: '6 A switched socket on a power circuit (CPWD 3.5.4).', socket16: '16 A switched socket on a power circuit.',
        'geyser-outlet': 'Water-heater socket controlled by the 16 A MCB near the bathroom door.',
        'mirror-light': 'Mirror light from the architectural scene, on the bathroom switchboard.', undercabinet: 'Under-cabinet light from the architectural scene.',
      };
      text.push(why[obj.kind] || '');
      refs.push(...({ fan: ['F-FAN', 'F-FAN-H', 'F-FAN-TABLE', 'A-FAN'], exhaust: ['F-EXHAUST'], socket6: ['F-SOCKET-H', 'F-6A-POWER'], socket16: ['F-SOCKET-H', 'F-POWER-CCT'],
        'geyser-outlet': ['F-GEYSER', 'A-GEYSER'], downlight: ['F-LIGHT-CCT', 'A-POSITIONS'] }[obj.kind] || ['A-POSITIONS']));
      break;
    }
    case 'conduits': {
      title = `Conduit ${obj.id}`;
      type = { service: 'Service cable pipe', submain: 'Submain riser', earthing: 'Earthing conductor route', prewire: 'DB pre-wiring passage' }[obj.function] || 'Concealed conduit';
      const ks = model.conductorsByConduit.get(obj.id) || [];
      const by = {};
      for (const k of ks) (by[k.circuitId || 'service'] ||= []).push(k.role);
      rows.push(['Route', obj.label], ['Size', `${obj.diameter} mm ${obj.material || 'rigid PVC (IS 9537-3)'}`],
        ['Carries', Object.entries(by).map(([cid, roles]) => `${cid}: ${roles.join(' ')}`).join(' · ') || '—']);
      if (obj.fill) rows.push(['Fill', Object.entries(obj.fill).map(([s, n]) => `${n} × ${s} mm²`).join(', ') + ' (CPWD Table 4.1 limit respected)']);
      text.push('Concealed in a wall chase or embedded in the RCC slab (laid on the reinforcement before concreting). The cyan strip marks where it runs behind the finished surface; walk to a step of the route to see a cut-open section.');
      refs.push('F-CONDUIT', 'F-SLAB', 'F-CHASE', 'F-BUNCH', 'A-ROUTES');
      break;
    }
    case 'boxes': {
      title = obj.label;
      rows.push(['Room', model.roomName(obj.roomId)]);
      if (obj.kind === 'earth-pit') { rows.push(['Electrode', obj.electrode]); text.push('One of two earth electrodes (CEA Reg. 18 own electrode; Reg. 43 two distinct connections), at least 1.5 m from the building and 3 m apart (CPWD F.8.9).'); refs.push('F-CEA-EARTH', 'F-CEA-2EARTH', 'F-EARTH', 'A-EARTHING'); }
      else { text.push('Junction or outlet box flush with the slab soffit, at least 65 mm deep (CPWD 4.4.3(d)).'); refs.push('F-SLAB'); }
      break;
    }
    case 'circuits': {
      title = obj.label;
      rows.push(['Protective device', obj.mcb ? `${obj.id} MCB (single-pole)` : '—'], ['RCD', '4-pole 30 mA RCCB at the main DB'], ['Phase', obj.phase],
        ['Conductors', obj.conductorSize ? `${obj.conductorSize} mm² Cu (${obj.conductorBasis})` : obj.conductorBasis], ['Points', String(obj.points.length)], ['State', stateText(model, sim, obj)]);
      if (obj.designW) rows.push(['Design load', `${obj.designW} W on CPWD ratings (LED lights not added)`]);
      refs.push(obj.kind === 'lighting' ? 'F-LIGHT-CCT' : 'F-POWER-CCT', 'A-GROUPING', 'F-BALANCE');
      text.push('Grouping, phase and protective-device relationships are explicit: one MCB per circuit, all circuits behind the 30 mA RCCB, each circuit’s phase and neutral in the same conduits.');
      break;
    }
    default:
  }
  return { title, type, rows, text, refs };
}

export function renderInspector(model, sim, obj, actions = '') {
  const d = describe(model, sim, obj);
  if (!d) {
    $('insp-type').textContent = 'Nothing selected';
    $('insp-title').textContent = 'Click a board, wire, terminal or fitting';
    $('insp-facts').innerHTML = '';
    $('insp-text').innerHTML = '<p>In <b>Walk inside</b>, click a switchboard to open it. Each wire, terminal and device inside can be clicked; a label appears beside it.</p>';
    $('insp-refs').innerHTML = '';
    $('insp-actions').innerHTML = actions;
    return null;
  }
  $('insp-type').textContent = d.type;
  $('insp-title').textContent = d.title;
  $('insp-facts').innerHTML = d.rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('');
  $('insp-text').innerHTML = d.text.filter(Boolean).map((t) => `<p>${esc(t)}</p>`).join('');
  $('insp-refs').innerHTML = factRefs(model, [...new Set(d.refs)]);
  $('insp-actions').innerHTML = actions;
  return d;
}

export function renderControls(model, sim, ctx) {
  const { encId } = ctx;
  const enc = encId ? model.get(encId) : null;
  const row = (title, sub, btn) => `<div class="row"><span><strong>${esc(title)}</strong>${sub ? `<small>${esc(sub)}</small>` : ''}</span>${btn}</div>`;
  const tog = (attr, id, on, trip) => `<button class="tog${trip ? ' trip' : ''}" ${attr}="${esc(id)}" aria-pressed="${Boolean(on && !trip)}">${trip ? 'TRIPPED' : on ? 'ON' : 'OFF'}</button>`;
  if (enc && ['switchboard', 'socket-plate', 'geyser-mcb'].includes(enc.kind)) {
    $('ctrl-title').textContent = enc.label;
    $('ctrl-sub').textContent = `${enc.circuitIds.join(', ')} · ${model.circuit(enc.circuitIds[0])?.phase} phase · operate the switches; only their own points change.`;
    const html = [];
    for (const s of model.data.switches.filter((x) => x.enclosureId === enc.id)) {
      const pts = s.points.map((p) => model.get(p));
      html.push(row(`${s.label}${s.mcb ? '' : ' switch'}`, pts.map((p) => p.label.split(' · ').slice(1).join(' · ')).join(', '), tog('data-switch', s.id, sim.switchClosed(s.id))));
      const reg = model.data.regulators.find((r) => r.points.some((p) => s.points.includes(p)));
      if (reg) html.push(row('Regulator', `Step ${sim.regulatorStep(reg.id)} of ${reg.steps}`, `<span><button class="tog" data-reg="${esc(reg.id)}" data-step="-1" aria-pressed="true">−</button> <button class="tog" data-reg="${esc(reg.id)}" data-step="1" aria-pressed="true">+</button></span>`));
    }
    $('controls').innerHTML = html.join('') || '<p class="sub">No switches.</p>';
    return;
  }
  const isSub = enc?.kind === 'sub-db' || (enc?.kind === 'loose-wire-box' && enc.floor === 1);
  const db = model.get(isSub ? model.data.distribution.subDB : model.data.distribution.mainDB);
  $('ctrl-title').textContent = db.label;
  $('ctrl-sub').textContent = 'Operate the main switch, RCCB and MCBs in the simulation. Demonstrate faults on the selected circuit — software only.';
  const devs = model.devicesByEnclosure.get(db.id) || [];
  const html = [];
  for (const d of devs.filter((x) => x.operable && x.kind !== 'mcb')) html.push(row(d.label, d.residual ? 'Trips on earth leakage ≥ 30 mA' : 'Isolates the whole board', tog('data-device', d.id, sim.state.devices[d.id], sim.state.tripped[d.id])));
  for (const d of devs.filter((x) => x.kind === 'mcb')) {
    const c = model.circuit(d.circuitId);
    html.push(row(`${d.circuitId} MCB · ${d.phase}`, c?.short || '', tog('data-device', d.id, sim.state.devices[d.id], sim.state.tripped[d.id])));
  }
  const cid = ctx.circuitId;
  if (cid && cid !== 'SUB') {
    html.push(`<div class="row"><span><strong>Demonstrate a fault on ${esc(cid)}</strong><small>Shows which device would isolate it; no physics is modelled.</small></span><span>
      <button class="tog" data-fault="leakage" aria-pressed="false">Leakage</button> <button class="tog" data-fault="overload" aria-pressed="false">Overload</button></span></div>`);
  }
  $('controls').innerHTML = html.join('');
}

// Single-line diagram: supply -> meter -> main switch -> RCCB -> busbar phases -> MCBs; earthing.
export function renderSupply(model, sim, circuitId) {
  const d = model.data, sup = d.supply;
  const c = circuitId && model.circuit(circuitId);
  const snap = sim.snapshot();
  const main = d.devices.find((x) => x.kind === 'mcb4p'), rccb = d.devices.find((x) => x.kind === 'rccb4p');
  const iso = d.devices.find((x) => x.kind === 'isolator2p');
  const on = (id) => snap.devices[id]?.closed;
  const phaseX = { R: 168, Y: 210, B: 252 };
  const col = { R: 'var(--r)', Y: 'var(--y)', B: 'var(--b)' };
  const hl = (ph) => c && (c.phase === ph) ? 'stroke-width="5"' : 'stroke-width="2.5" opacity=".55"';
  const ff = c && (c.floor === 1 || c.id === 'SUB');
  const box = (x, y, w, h, t, sub, state) => `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="7" fill="${state === false ? '#f6e4dc' : '#fff'}" stroke="${state === false ? '#c0582f' : '#9db3a5'}"/>
    <text x="${x + w / 2}" y="${y + h / 2 - (sub ? 3 : -4)}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#24382e">${esc(t)}</text>${sub ? `<text x="${x + w / 2}" y="${y + h / 2 + 10}" text-anchor="middle" font-size="9" fill="#5b6c64">${esc(sub)}</text>` : ''}</g>`;
  const svg = `<svg viewBox="0 0 340 236" role="img" aria-label="Single-line diagram of the assumed supply">
    ${box(6, 8, 92, 34, '11 kV / 433 V', 'DISCOM transformer')}
    <path d="M98 25H118" stroke="#8a6d45" stroke-width="3"/>
    ${box(118, 8, 66, 34, 'Meter', 'sealed, DISCOM')}
    <path d="M184 25H204" stroke="#555" stroke-width="3"/>
    ${box(204, 8, 64, 34, 'Main MCB', '4-pole', on(main.id))}
    <path d="M268 25H282" stroke="#555" stroke-width="3"/>
    ${box(282, 8, 52, 34, 'RCCB', '30 mA', on(rccb.id) && !snap.devices[rccb.id]?.tripped)}
    <path d="M308 42V58H140" fill="none" stroke="#666" stroke-width="2"/>
    ${['R', 'Y', 'B'].map((ph) => `<path d="M${phaseX[ph]} 58V120" stroke="${col[ph]}" ${hl(ph)}/><text x="${phaseX[ph]}" y="132" text-anchor="middle" font-size="10" font-weight="800" fill="${col[ph]}">${ph}</text>`).join('')}
    <path d="M120 58V120" stroke="#1e1f21" stroke-width="2.5" opacity=".7"/><text x="120" y="132" text-anchor="middle" font-size="10" font-weight="800">N</text>
    <text x="8" y="80" font-size="9.5" fill="#4b5f54">Busbars after</text><text x="8" y="92" font-size="9.5" fill="#4b5f54">the RCCB</text>
    ${c ? `<rect x="${(phaseX[c.phase] || 210) - 30}" y="140" width="60" height="26" rx="6" fill="#ecfafc" stroke="var(--cyan-ink)"/><text x="${phaseX[c.phase] || 210}" y="157" text-anchor="middle" font-size="10.5" font-weight="800" fill="#0f6f7c">${esc(c.id)} MCB</text>
      <path d="M${phaseX[c.phase] || 210} 120V140" stroke="${col[c.phase] || '#888'}" stroke-width="4"/>` : ''}
    ${ff ? box(232, 176, 102, 30, '1st-floor sub-DB', 'isolator + MCBs', on(iso.id)) : ''}
    <g transform="translate(8 182)"><path d="M10 0V14M2 14H18M5 18H15M8 22H12" stroke="var(--pe)" stroke-width="2" fill="none"/><path d="M34 0V14M26 14H42M29 18H39M32 22H36" stroke="var(--pe)" stroke-width="2" fill="none"/>
      <path d="M10 0V-6H118" stroke="var(--pe)" stroke-width="2" stroke-dasharray="5 3" fill="none"/><path d="M34 0V-6" stroke="var(--pe)" stroke-width="2"/>
      <text x="0" y="40" font-size="9.5" fill="#3b6b44">2 electrodes → main earthing terminal → PE in every circuit</text></g>
  </svg>`;
  const pl = sup.phaseLoadW || {};
  $('supply-diagram').innerHTML = svg;
  $('supply-text').innerHTML = `<p><b>Assumed:</b> ${esc(sup.kind)}, ${esc(sup.nominal)}. Design load on CPWD ratings ≈ <b>${esc(sup.designLoadKW)} kW</b> (R ${((pl.R || 0) / 1000).toFixed(1)} · Y ${((pl.Y || 0) / 1000).toFixed(1)} · B ${((pl.B || 0) / 1000).toFixed(1)} kW), LED lighting not added. That exceeds the single-phase limit in most state supply codes, so three-phase is a reasonable assumption — <b>not a verified fact</b>; the DISCOM confirms the actual connection.</p>
    <p>Each final circuit uses <b>one phase and its own neutral</b>, both returning through the RCCB; the <b>protective earth</b> is a separate fault path from the electrodes and never carries normal current.</p>`;
}

export function renderSteps(steps, i) {
  $('steps-section').hidden = !steps;
  if (!steps) return;
  $('steps').innerHTML = steps.map((s, k) => `<li data-step="${k}" class="${k === i ? 'current' : ''}">${esc(s.title)}</li>`).join('');
}
