// Installed (closed) appearance of every electrical fitting, at manufacturer scale.
// Local frames: x right (facing the wall), y up, z out of the finished face.
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';
import { mergeGeometries, roundedPlate, frameGeometry, s2t } from './geom.js';
import { mat, printedMaterial } from './materials.js';

const MW = .0225, MH = .045;          // Legrand module (F-LG-DIM)

function place(geo, x, y, z) { const g = geo.clone(); g.translate(x, y, z); return g; }

function pin(r, depth = .002) {
  const g = new THREE.CircleGeometry(r, 20);
  g.translate(0, 0, depth);
  return g;
}

// ---------------------------------------------------------------- modular plates
export function buildPlate(model, enc, pickables) {
  const group = new THREE.Group();
  group.name = enc.id;
  const frame = model.frame(enc);
  frame.decompose(group.position, group.quaternion, group.scale);
  const W = enc.size.w, H = enc.size.h, D = enc.size.plateDepth || .0065;
  const cols = enc.plateModules <= 8 ? enc.plateModules : 6;
  const rows = enc.plateModules <= 8 ? 1 : 2;
  const winW = cols * MW + .003, winH = rows * MH + (rows - 1) * .0 + .003;
  // everything in front of the wall rides on one assembly so the opened view can swing it out
  const assembly = new THREE.Group();
  assembly.name = 'assembly';
  group.add(assembly);
  // cover plate: polycarbonate frame around the module window
  const plate = new THREE.Mesh(frameGeometry(W, H, winW, winH, D, .002), mat('plate'));
  plate.userData = { kind: 'plate', ref: enc.id };
  assembly.add(plate);
  // a small bevel strip so the plate edge catches light
  const edge = new THREE.Mesh(roundedPlate(W, H, .0012, .006, .0006), mat('plate'));
  assembly.add(edge);
  // support frame behind the window
  const back = new THREE.Mesh(new THREE.PlaneGeometry(winW, winH), mat('frame'));
  back.position.z = .0005;
  assembly.add(back);
  const statics = [], darks = [];
  const parts = { group, assembly, plate, rockers: new Map(), knobs: new Map(), modules: [] };
  for (const m of enc.modules) {
    const span = m.span;
    const w = span * MW - .0008, h = MH - .0008;
    const cx = m.x, cy = m.y;
    const face = new THREE.BoxGeometry(w, h, .004);
    statics.push(place(face, cx, cy, D - .002));
    if (m.kind === 'switch' || m.kind === 'switch16') {
      const rocker = new THREE.Mesh(new THREE.BoxGeometry(.0148, .031, .0042), mat('module'));
      rocker.position.set(cx, cy, D + .0018);
      rocker.userData = { kind: 'switch', ref: m.switchId, enclosure: enc.id };
      const mark = new THREE.Mesh(new THREE.PlaneGeometry(.004, .0016), mat('toggleRed'));
      mark.position.set(0, -.0115, .0022);
      rocker.add(mark);
      assembly.add(rocker);
      parts.rockers.set(m.switchId, rocker);
      pickables.push(rocker);
    } else if (m.kind === 'socket6' || m.kind === 'socket16') {
      // IS 1293 Annex A: earth contact above two current-carrying contacts
      const big = m.kind === 'socket16';
      const spread = big ? .0254 : .0191, up = big ? .0259 : .0200, rp = big ? .0040 : .0030, re = big ? .0045 : .0037;
      const boss = new THREE.CylinderGeometry(.019, .019, .0015, 32);
      boss.rotateX(Math.PI / 2);
      statics.push(place(boss, cx, cy, D + .0006));
      darks.push(place(pin(rp), cx - spread / 2, cy - up / 3, D + .0002 + .0015));
      darks.push(place(pin(rp), cx + spread / 2, cy - up / 3, D + .0002 + .0015));
      darks.push(place(pin(re), cx, cy + up * 2 / 3, D + .0002 + .0015));
      const hit = new THREE.Mesh(new THREE.BoxGeometry(w, h, .006), mat('module'));
      hit.position.set(cx, cy, D);
      hit.visible = false;
      hit.userData = { kind: 'device', ref: m.deviceId, enclosure: enc.id, proxy: true };
      assembly.add(hit);
      pickables.push(hit);
    } else if (m.kind === 'regulator') {
      const knob = new THREE.Mesh(new THREE.CylinderGeometry(.0125, .0135, .011, 32), mat('module'));
      knob.rotation.x = Math.PI / 2;
      knob.position.set(cx, cy, D + .0055);
      knob.userData = { kind: 'regulator', ref: m.regulatorId, enclosure: enc.id };
      const pointer = new THREE.Mesh(new THREE.BoxGeometry(.0018, .0015, .007), mat('toggle'));
      pointer.position.set(0, .0056, -.0055);
      pointer.rotation.x = -Math.PI / 2;
      knob.add(pointer);
      assembly.add(knob);
      parts.knobs.set(m.regulatorId, knob);
      pickables.push(knob);
      for (let i = 0; i < 6; i++) {
        const a = Math.PI * (1.25 - i * .3);
        darks.push(place(pin(.0007), cx + Math.cos(a) * .0175, cy + Math.sin(a) * .0175, D + .0001));
      }
    } else if (m.kind === 'mcb') {
      const win = new THREE.BoxGeometry(.014, .03, .0015);
      darks.push(place(win, cx, cy, D + .0008));
      const toggle = new THREE.Mesh(new THREE.BoxGeometry(.008, .012, .006), mat('toggle'));
      toggle.position.set(cx, cy + .004, D + .003);
      toggle.userData = { kind: 'switch', ref: m.switchId, enclosure: enc.id, mcb: true };
      assembly.add(toggle);
      parts.rockers.set(m.switchId, toggle);
      pickables.push(toggle);
    }
    parts.modules.push(m);
  }
  if (statics.length) {
    const g = mergeGeometries(statics.map((x) => x.toNonIndexed ? x.toNonIndexed() : x));
    const faces = new THREE.Mesh(g, mat('module'));
    faces.userData = { kind: 'plate', ref: enc.id };
    assembly.add(faces);
    pickables.push(faces);
  }
  if (darks.length) {
    const g = mergeGeometries(darks.map((x) => x.toNonIndexed ? x.toNonIndexed() : x));
    assembly.add(new THREE.Mesh(g, mat('toggle')));
  }
  pickables.push(plate);
  assembly.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = true; } });
  return parts;
}

// Rockers: ON when the knob is down (CPWD 3.14.1(a)); modular MCB: toggle up = ON.
export function setRocker(obj, on, isMcb = false) {
  if (isMcb) { obj.position.y = obj.userData.baseY ??= obj.position.y; obj.position.y = obj.userData.baseY + (on ? .004 : -.004); return; }
  obj.rotation.x = on ? -.13 : .13;
}

// ---------------------------------------------------------------- distribution boards
export function buildDB(model, enc, pickables, { danger = true } = {}) {
  const group = new THREE.Group();
  group.name = enc.id;
  model.frame(enc).decompose(group.position, group.quaternion, group.scale);
  const W = enc.size.w, H = enc.size.h, D = enc.size.depth;
  // flush flange (plastering guide) + double door, slightly proud of the plaster
  const flange = new THREE.Mesh(frameGeometry(W + .024, H + .024, W - .02, H - .02, .006, .002), mat('enclosure'));
  flange.userData = { kind: 'enclosure', ref: enc.id };
  group.add(flange);
  pickables.push(flange);
  const doors = new THREE.Group();
  doors.name = 'doors';
  const leafW = (W - .022) / 2;
  const mkLeaf = (sign) => {
    const pivot = new THREE.Group();
    pivot.position.set(sign * (W - .022) / 2, 0, .006);
    const leaf = new THREE.Mesh(roundedPlate(leafW - .002, H - .022, .016, .003, .0015), mat('enclosure'));
    leaf.position.set(-sign * leafW / 2, 0, 0);
    leaf.userData = { kind: 'enclosure', ref: enc.id, door: true };
    pivot.add(leaf);
    pickables.push(leaf);
    if (sign < 0) {
      const handle = new THREE.Mesh(new THREE.BoxGeometry(.012, .05, .01), mat('deviceGrey'));
      handle.position.set(leafW - .016, 0, .019);
      leaf.add(handle);
    }
    doors.add(pivot);
    return pivot;
  };
  const left = mkLeaf(-1), right = mkLeaf(1);
  group.add(doors);
  if (danger && enc.kind !== 'loose-wire-box') {
    const plate = new THREE.Mesh(new THREE.PlaneGeometry(.075, .05), printedMaterial('danger-plate', 300, 200, (g, w, h) => {
      g.fillStyle = '#f4f1e8'; g.fillRect(0, 0, w, h);
      g.fillStyle = '#b4271f'; g.fillRect(0, 0, w, 54);
      g.fillStyle = '#fff'; g.font = 'bold 40px system-ui, sans-serif'; g.textAlign = 'center'; g.fillText('DANGER', w / 2, 42);
      g.fillStyle = '#1d1d1d'; g.font = 'bold 44px system-ui, sans-serif'; g.fillText('400 V', w / 2, 118);
      g.font = '24px system-ui, sans-serif'; g.fillText('CEA Reg. 20 notice', w / 2, 168);
    }));
    left.children[0].add(plate);
    plate.position.set(0, H / 2 - .07, .0165);
  }
  if (enc.kind === 'loose-wire-box') {
    // plain removable cover, no doors
    doors.visible = false;
    const cover = new THREE.Mesh(roundedPlate(W - .02, H - .02, .01, .003, .0012), mat('enclosure'));
    cover.position.z = .006;
    cover.userData = { kind: 'enclosure', ref: enc.id };
    group.add(cover);
    pickables.push(cover);
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) {
      const sc = new THREE.Mesh(new THREE.CylinderGeometry(.003, .003, .002, 12), mat('screw'));
      sc.rotation.x = Math.PI / 2;
      sc.position.set(sx * (W / 2 - .025), sy * (H / 2 - .022), .0165);
      group.add(sc);
    }
    return { group, doors: null, cover, left: null, right: null };
  }
  return { group, doors, left, right, cover: null };
}

// ---------------------------------------------------------------- meter box (exterior, sealed)
export function buildMeter(model, enc, pickables) {
  const group = new THREE.Group();
  group.name = enc.id;
  model.frame(enc).decompose(group.position, group.quaternion, group.scale);
  const W = enc.size.w, H = enc.size.h, D = enc.size.surface || .2;
  const body = new THREE.Mesh(roundedPlate(W, H, D, .012, .004), mat('meterBody'));
  body.userData = { kind: 'enclosure', ref: enc.id };
  group.add(body);
  pickables.push(body);
  // the meter visible through the cover window
  const meter = new THREE.Group();
  meter.position.set(0, .02, D - .03);
  const mb = new THREE.Mesh(roundedPlate(.191, .255, .02, .008, .003), mat('device'));
  mb.position.z = -.02;
  meter.add(mb);
  const lcd = new THREE.Mesh(new THREE.PlaneGeometry(.085, .028), printedMaterial('meter-lcd', 340, 112, (g, w, h) => {
    g.fillStyle = '#9db398'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#1e2a1d'; g.font = 'bold 56px ui-monospace, monospace'; g.textAlign = 'right'; g.fillText('00427.6', w - 52, 74);
    g.font = 'bold 26px system-ui'; g.fillText('kWh', w - 6, 74); g.font = '20px system-ui'; g.textAlign = 'left'; g.fillText('3Ø 4W', 8, 102);
  }));
  lcd.position.set(0, .06, .0015);
  meter.add(lcd);
  const led = new THREE.Mesh(new THREE.CircleGeometry(.0028, 16), new THREE.MeshStandardMaterial({ color: '#ff5b45', emissive: '#ff3b25', emissiveIntensity: 0 }));
  led.position.set(.06, .025, .0015);
  meter.add(led);
  const tcover = new THREE.Mesh(new THREE.BoxGeometry(.18, .055, .01), mat('device'));
  tcover.position.set(0, -.095, .004);
  meter.add(tcover);
  for (const sx of [-.07, .07]) {
    const seal = new THREE.Mesh(new THREE.SphereGeometry(.004, 12, 8), mat('seal'));
    seal.position.set(sx, -.122, .012);
    meter.add(seal);
  }
  group.add(meter);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(.2, .14), new THREE.MeshPhysicalMaterial({ color: '#dfe9ee', roughness: .05, transparent: true, opacity: .22, depthWrite: false }));
  glass.position.set(0, .07, D + .0005);
  group.add(glass);
  const label = new THREE.Mesh(new THREE.PlaneGeometry(.12, .03), printedMaterial('meter-label', 480, 120, (g, w, h) => {
    g.fillStyle = '#f7f6f0'; g.fillRect(0, 0, w, h);
    g.fillStyle = '#25302c'; g.font = 'bold 40px system-ui'; g.textAlign = 'center'; g.fillText('DISCOM METER', w / 2, 52);
    g.font = '30px system-ui'; g.fillText('Sealed · licensee only', w / 2, 100);
  }));
  label.position.set(0, -.13, D + .0006);
  group.add(label);
  return { group, led };
}

// ---------------------------------------------------------------- ceiling fan (hung from its slab box)
export function buildFan(model, point, box, pickables) {
  const group = new THREE.Group();
  group.name = point.id;
  const sweep = (point.sweep || 1200) / 1000;
  const soffit = box.position[2];
  const bladeZ = (point.floor * model.data.floorHeight) + 2.69;     // >= 300 mm below the soffit (IS 732:1989 C-8.1)
  group.position.copy(s2t([point.position[0], point.position[1], soffit]));
  const drop = soffit - bladeZ;                                       // ~0.29 m
  const canopy = new THREE.Mesh(new THREE.CylinderGeometry(.045, .062, .12, 32, 1, true), mat('fanBody'));
  canopy.position.y = -.06;
  canopy.userData = { kind: 'fan-canopy', ref: point.id };
  const capTop = new THREE.Mesh(new THREE.CircleGeometry(.062, 32), mat('fanBody'));
  capTop.rotation.x = Math.PI / 2; capTop.position.y = -.12;
  const canopyGroup = new THREE.Group();
  canopyGroup.add(canopy, capTop);
  group.add(canopyGroup);
  pickables.push(canopy);
  const rodLen = drop - .07;
  const rod = new THREE.Mesh(new THREE.CylinderGeometry(.0105, .0105, rodLen, 16), mat('downrod'));
  rod.position.y = -rodLen / 2 - .0;
  group.add(rod);
  const rotor = new THREE.Group();
  rotor.position.y = -drop;
  const motor = new THREE.Mesh(new THREE.CylinderGeometry(.105, .095, .085, 40), mat('fanBody'));
  motor.userData = { kind: 'point', ref: point.id };
  rotor.add(motor);
  const cap = new THREE.Mesh(new THREE.SphereGeometry(.095, 32, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), mat('fanBody'));
  cap.scale.y = .35; cap.position.y = -.042;
  rotor.add(cap);
  pickables.push(motor);
  const bladeLen = sweep / 2 - .1;
  for (let i = 0; i < 3; i++) {
    const arm = new THREE.Group();
    arm.rotation.y = i * Math.PI * 2 / 3;
    const shape = new THREE.Shape();
    shape.moveTo(0, -.03); shape.lineTo(bladeLen * .3, -.05); shape.quadraticCurveTo(bladeLen, -.06, bladeLen, 0);
    shape.quadraticCurveTo(bladeLen, .055, bladeLen * .3, .05); shape.lineTo(0, .03); shape.lineTo(0, -.03);
    const g = new THREE.ExtrudeGeometry(shape, { depth: .0025, bevelEnabled: false });
    g.rotateX(Math.PI / 2);
    const blade = new THREE.Mesh(g, mat('fanBlade'));
    blade.position.set(.1, 0, 0);
    blade.rotation.x = .08;
    blade.userData = { kind: 'point', ref: point.id };
    arm.add(blade);
    pickables.push(blade);
    rotor.add(arm);
  }
  group.add(rotor);
  // Only the sun casts shadows in this viewer, and it barely reaches a ceiling fan indoors:
  // keeping fans out of the shadow pass saves a draw call per fan part every frame.
  group.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = true; } });
  return { group, rotor, canopyGroup, drop };
}

// ---------------------------------------------------------------- wall exhaust fan + point box plate
export function buildExhaust(model, point, pickables) {
  const group = new THREE.Group();
  group.name = point.id;
  const wallBox = model.get(point.boxId);
  const n = wallBox.mount.normal;
  const pos = point.position;
  const z = new THREE.Vector3(n[0], 0, -n[1]);
  const y = new THREE.Vector3(0, 1, 0);
  const x = y.clone().cross(z).normalize();
  group.matrixAutoUpdate = true;
  const m = new THREE.Matrix4().makeBasis(x, y, z).setPosition(s2t([pos[0] + n[0] * .002, pos[1] + n[1] * .002, pos[2]]));
  m.decompose(group.position, group.quaternion, group.scale);
  const s = point.size || .3;
  const frame = new THREE.Mesh(frameGeometry(s, s, s - .05, s - .05, .025, .006), mat('exhaust'));
  frame.userData = { kind: 'point', ref: point.id };
  group.add(frame);
  pickables.push(frame);
  const grille = new THREE.Group();
  for (let i = 0; i < 9; i++) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(s - .06, .004, .004), mat('exhaust'));
    bar.position.set(0, -s / 2 + .04 + i * (s - .08) / 8, .02);
    grille.add(bar);
  }
  group.add(grille);
  const hub = new THREE.Group();
  hub.position.z = .006;
  for (let i = 0; i < 5; i++) {
    const blade = new THREE.Mesh(new THREE.BoxGeometry(.1, .035, .002), mat('fanBlade'));
    blade.position.x = .055;
    const arm = new THREE.Group(); arm.rotation.z = i * Math.PI * 2 / 5; arm.add(blade); hub.add(arm);
  }
  group.add(hub);
  const back = new THREE.Mesh(new THREE.CircleGeometry((s - .05) / 2, 32), mat('rubber'));
  back.position.z = .001;
  group.add(back);
  return { group, hub };
}

// Cord outlet plate on an exhaust/mirror/under-cabinet outlet box (2-module blank with grommet).
export function buildOutletPlate(model, box, pickables) {
  const group = new THREE.Group();
  model.frame(box).decompose(group.position, group.quaternion, group.scale);
  const assembly = new THREE.Group();
  group.add(assembly);
  const plate = new THREE.Mesh(roundedPlate(.086, .086, .0065, .006, .0012), mat('plate'));
  plate.userData = { kind: 'box', ref: box.id };
  assembly.add(plate);
  pickables.push(plate);
  const grommet = new THREE.Mesh(new THREE.TorusGeometry(.005, .0018, 8, 20), mat('rubber'));
  grommet.position.set(0, -.02, .0068);
  assembly.add(grommet);
  return { group, assembly };
}

// ---------------------------------------------------------------- earth pit cover (flush with paving)
export function buildPit(model, pit, pickables) {
  const group = new THREE.Group();
  group.position.copy(s2t(pit.position));
  const rim = new THREE.Mesh(frameGeometry(.36, .36, .3, .3, .02, .002), mat('pit'));
  rim.rotation.x = -Math.PI / 2;
  rim.position.y = -.014;
  const cover = new THREE.Mesh(new THREE.BoxGeometry(.296, .012, .296), printedMaterial('pit-cover', 256, 256, (g, w, h) => {
    g.fillStyle = '#4e5355'; g.fillRect(0, 0, w, h);
    g.strokeStyle = '#626869'; g.lineWidth = 6;
    for (let i = 20; i < w; i += 28) { g.beginPath(); g.moveTo(i, 10); g.lineTo(i, h - 10); g.stroke(); }
    g.fillStyle = '#d7d2c4'; g.font = 'bold 34px system-ui'; g.textAlign = 'center'; g.fillText('EARTH', w / 2, h / 2 + 12);
  }, { metalness: .6, roughness: .55 }));
  cover.position.y = -.0035;
  cover.userData = { kind: 'box', ref: pit.id };
  group.add(rim, cover);
  pickables.push(cover);
  return { group };
}

// ---------------------------------------------------------------- downlight state caps (one InstancedMesh)
export function buildLightCaps(model, viewerScene, points) {
  // A thin disc just below each architectural lamp lens shows the simulated state of that point.
  const downs = points.filter((p) => p.kind === 'downlight' && p.lens);
  const geo = new THREE.CylinderGeometry(1, 1, .0008, 28);
  const on = new THREE.InstancedMesh(geo, mat('lensOn'), downs.length);
  const off = new THREE.InstancedMesh(geo, mat('lensOff'), downs.length);
  const index = new Map();
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3();
  downs.forEach((p, i) => {
    const pos = s2t([p.lens.xy[0], p.lens.xy[1], p.lens.bottom - .0006]);
    const r = p.lens.r + .0012;
    m.compose(pos, q, sc.set(r, 1, r));
    on.setMatrixAt(i, m);
    off.setMatrixAt(i, m);
    index.set(p.id, i);
  });
  on.frustumCulled = off.frustumCulled = false;
  on.userData = { kind: 'light-caps' };
  return { on, off, index, downs };
}
