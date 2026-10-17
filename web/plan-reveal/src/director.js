// The choreography. Scroll position is the only clock: every frame the camera pose, the cut height, each room's
// reveal and the HUD are a pure function of it, so scrolling back un-builds the house exactly as it was built.
//   sheet    — the plan from 1 700 m up through a 2° lens: a flat drawing that is the real model cut at +1.2 m
//   lift     — the lens opens while the camera holds the framing (a dolly zoom) and the cut rises: the walls grow
//   descend  — down to the street, the garden sweeping in; then room by room along the real routes
//   rise / floor plan / drop — a change of floor lifts back into that floor's drawing and comes down into it
//   outro    — up again, the house cut back down to its plan, everything in colour, then paper rolls back over it
import * as THREE from 'three';

const DEG = Math.PI / 180;
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const smooth = (a, b, v) => { const t = clamp((v - a) / (b - a)); return t * t * (3 - 2 * t); };
const ease = (t) => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const easeIO = (t) => .5 - .5 * Math.cos(Math.PI * clamp(t));
const lerp = (a, b, t) => a + (b - a) * t;
const s2t = ([x, y, z]) => new THREE.Vector3(x, z, -y);

function invertEase(f, y) {
  let lo = 0, hi = 1;
  for (let i = 0; i < 30; i++) { const m = (lo + hi) / 2; if (f(m) < y) lo = m; else hi = m; }
  return (lo + hi) / 2;
}

export class Director {
  constructor({ viewer, mask, drawing, data, scene, hud, reduced = false }) {
    Object.assign(this, { viewer, mask, drawing, data, scene, hud, reduced });
    this.H = data.floorHeight;
    this.stops = data.tour.stops;
    this.legs = data.tour.legs.map((leg) => ({ ...leg, curve: this.curve(leg.points) }));
    const fp = data.footprint, xs = fp.map((p) => p[0]), ys = fp.map((p) => p[1]);
    this.house = { x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) };
    this.houseCenter = [(this.house.x0 + this.house.x1) / 2, (this.house.y0 + this.house.y1) / 2];
    this.top = data.storeys * this.H + 1.4;
    this.ground = scene.bounds[2];
    this.plan();
    this.schedule();
    this.scheduleDoors();
    this.state = { p: 0 };
    this.tmp = { pos: new THREE.Vector3(), look: new THREE.Vector3(), up: new THREE.Vector3(0, 1, 0) };
  }

  curve(points) {
    const pts = points.map(s2t);
    if (pts.length < 2) pts.push(pts[0].clone().add(new THREE.Vector3(.01, 0, 0)));
    const c = new THREE.CatmullRomCurve3(pts, false, 'centripetal', .5);
    c.arcLengthDivisions = Math.max(200, pts.length * 8);
    return c;
  }

  // Chapters in scroll screens (one screen = one viewport height of scrolling).
  plan() {
    const ch = [];
    const add = (kind, len, extra = {}) => ch.push({ kind, len, ...extra });
    add('sheet', 1.2);
    add('lift', 1.9);
    add('descend', 1.6);
    add('dwell', .8, { stop: 0 });
    for (const leg of this.legs) {
      if (leg.kind === 'lift') { add('rise', 1.1, { leg }); add('floorplan', .8, { leg }); add('drop', 1.1, { leg }); }
      add('walk', clamp(.55 + leg.length / 4.5, .7, 2.6), { leg });
      add('dwell', 1, { stop: leg.to });
    }
    add('outro', 1.8);
    add('colour', 1.2);
    add('wipe', 1.0);
    add('end', .7);
    let at = 0;
    for (const c of ch) { c.start = at; at += c.len; }
    this.chapters = ch;
    this.total = at;
  }

  // When each room starts to reveal: the moment the camera crosses into it on the first leg that does.
  schedule() {
    this.reveals = new Map();
    for (const c of this.chapters) {
      if (c.kind !== 'walk') continue;
      const L = Math.max(c.leg.length, .01);
      for (const e of c.leg.enters) {
        if (this.reveals.has(e.room)) continue;
        const t = invertEase(easeIO, clamp((e.s - .35) / L));
        this.reveals.set(e.room, { at: c.start + t * c.len, origin: e.origin, floor: c.leg.floor });
      }
    }
    // Rooms presented as stops but never crossed (an open terrace reached by a lift) start on arrival.
    for (const c of this.chapters) if (c.kind === 'dwell' && c.stop > 0) {
      const s = this.stops[c.stop];
      if (s.room && !this.reveals.has(s.room)) this.reveals.set(s.room, { at: c.start, origin: s.stand.slice(0, 2), floor: s.floor });
    }
    const descend = this.chapters.find((c) => c.kind === 'descend');
    this.outdoorAt = descend.start + descend.len * .25;
    this.outdoorLen = descend.len * .95;
  }

  chapterAt(p) {
    let c = this.chapters[0];
    for (const x of this.chapters) if (p >= x.start) c = x;
    return c;
  }

  // The stop the visitor is at or last passed, for the overlay's room ruler.
  stopAt(p) {
    let stop = 0;
    for (const c of this.chapters) if (c.kind === 'dwell' && c.start <= p) stop = c.stop;
    return stop;
  }

  startOf(kind, stop) { return this.chapters.find((c) => c.kind === kind && (stop === undefined || c.stop === stop))?.start ?? 0; }

  // ---------------------------------------------------------------- camera helpers
  aspect() { return this.viewer.camera.aspect || 1.6; }

  // The opening sheet. On a landscape screen the drawing sits right of the title, in the margin the header, the
  // lens readout and the title block leave free: beside the title block or above it, whichever draws it larger. On
  // a portrait screen it sits below the title. Returns the frame's visible height in metres, the camera target and
  // the drawing's centre.
  sheetFrame() {
    const b = this.data.sheets[0].bounds, a = this.aspect();
    const bw = b[2] - b[0], bh = b[3] - b[1], cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
    // Free boxes as screen fractions [left, top, right, bottom].
    const boxes = this.hud?.sheetBoxes?.() || (a >= 1.05 ? [[.45, .13, .965, .9]] : [[.05, .36, .95, .86]]);
    let best = null;
    for (const [l, t, r, btm] of boxes) {
      const Hv = Math.max(bh / (btm - t), bw / ((r - l) * a));
      if (!best || Hv < best.Hv) best = { Hv, x: l + r - 1, y: 1 - t - btm };
    }
    const { Hv, x, y } = best;
    return { Hv, target: [cx - x * Hv * a / 2, cy - y * Hv / 2], center: [cx, cy] };
  }

  placeTopDown(target2, height, fov, twist = 0) {
    const cam = this.viewer.camera;
    const t = s2t([target2[0], target2[1], height]);
    const d = this.frameDistance;
    cam.position.set(t.x, t.y + d, t.z);
    cam.up.set(Math.sin(twist), 0, -Math.cos(twist));
    cam.lookAt(t);
    cam.fov = fov;
  }

  lookFrom(pos, look, fov, up = new THREE.Vector3(0, 1, 0)) {
    const cam = this.viewer.camera;
    cam.position.copy(pos);
    cam.up.copy(up);
    cam.lookAt(look);
    cam.fov = fov;
  }

  setClip(near, far) {
    const cam = this.viewer.camera;
    cam.near = near; cam.far = far;
    cam.updateProjectionMatrix();
  }

  // ---------------------------------------------------------------- the frame
  update(p) {
    const v = this.viewer, cam = v.camera;
    p = clamp(p, 0, this.total - 1e-4);
    const c = this.chapterAt(p), t = clamp((p - c.start) / c.len);
    const out = { chapter: c.kind, stop: null, card: 0, cut: 1e5, sheetInk: 0, labelInk: 0, sky: 1, all: 0, wipe: 0, sheet: 0, indoor: false, floor: 0, planLight: 0, context: 0, poche: 0 };
    const sf = this.sheetFrame();
    const radius = Math.hypot(this.house.x1 - this.house.x0, this.house.y1 - this.house.y0);
    const liftEnd = this.liftEnd(sf);

    if (c.kind === 'sheet' || c.kind === 'lift') {
      const lt = c.kind === 'sheet' ? 0 : t;
      const e = smooth(.04, .86, lt);
      const fov = Math.exp(lerp(Math.log(2), Math.log(liftEnd.fov), e));
      const Hv = sf.Hv * lerp(c.kind === 'sheet' ? 1 - .03 * t : .97, liftEnd.Hv / sf.Hv, smooth(.3, 1, lt));
      const d = Hv / (2 * Math.tan(fov * DEG / 2));
      const target = new THREE.Vector3().lerpVectors(s2t([sf.target[0], sf.target[1], 0]), liftEnd.target, easeIO(smooth(.05, .95, lt)));
      const elev = lerp(89.95, liftEnd.elev, easeIO(smooth(.12, .95, lt))) * DEG;
      const az = liftEnd.az;
      const dir = new THREE.Vector3(Math.cos(elev) * Math.cos(az), Math.sin(elev), -Math.cos(elev) * Math.sin(az));
      const north = new THREE.Vector3(0, 0, -1), up = north.clone().lerp(new THREE.Vector3(0, 1, 0), smooth(.2, .9, lt)).normalize();
      this.lookFrom(target.clone().addScaledVector(dir, d), target, fov, up);
      this.setClip(Math.max(.05, d - radius * 2.5 - 40), d + radius * 3 + 80);
      out.cut = lerp(1.2, this.H - .18, smooth(.18, .95, lt));
      out.sheetInk = 1 - smooth(.22, .6, lt);
      out.labelInk = smooth(.7, 1, lt) * .85;
      out.sky = 0; out.sheet = 1 - smooth(.25, .8, lt);
    } else if (c.kind === 'descend') {
      const s0 = this.stops[0], e = easeIO(t);
      const P1 = liftEnd.pos, T1 = liftEnd.target, S = s2t(s0.stand), L = s2t(s0.look);
      const back = S.clone().sub(L).setY(0).normalize();
      const c1 = P1.clone().lerp(S, .25).setY(P1.y * .8);
      const c2 = S.clone().addScaledVector(back, 6).setY(S.y + 4);
      const pos = new THREE.CubicBezierCurve3(P1, c1, c2, S).getPoint(e);
      const look = T1.clone().lerp(L, smooth(.15, .85, t));
      this.lookFrom(pos, look, lerp(liftEnd.fov, s0.fov, e));
      this.setClip(lerp(Math.max(.05, liftEnd.dist - radius * 2.5 - 40), .05, smooth(0, .6, t)), lerp(liftEnd.dist + radius * 3 + 80, 1500, smooth(0, .4, t)));
      const build = smooth(.08, .62, t);
      out.cut = build < .999 ? lerp(this.H - .18, this.top + .6, build) : 1e5;
      out.labelInk = .85;
      out.sky = smooth(.45, .95, t);
    } else if (c.kind === 'dwell') {
      const s = this.stops[c.stop], S = s2t(s.stand), L = s2t(s.look);
      const fwd = L.clone().sub(S).setY(0).normalize();
      const side = new THREE.Vector3(-fwd.z, 0, fwd.x);
      const drift = this.reduced ? 0 : easeIO(t) - .5;
      const pos = S.clone().addScaledVector(fwd, .22 * (drift + .5)).addScaledVector(side, .05 * drift);
      const look = L.clone().addScaledVector(side, .35 * drift);
      // A room is held like an interior photograph: the camera settles a little lower and levels off, and a lens
      // shift instead of a tilt keeps the floor in frame, so the walls' verticals stay vertical.
      const hold = c.stop > 0 && !this.reduced ? smooth(0, .22, t) * (1 - smooth(.8, 1, t)) : c.stop > 0 ? 1 : 0;
      // Positive shifts show more floor; negative ones, for a stop looking up (a court's tree), more sky.
      const tilt = Math.atan2(pos.y - look.y, Math.hypot(look.x - pos.x, look.z - pos.z));
      out.shift = hold * clamp(Math.tan(tilt) / Math.tan(s.fov * DEG / 2), -.45, .4);
      pos.y -= .25 * hold;
      look.y = lerp(look.y, pos.y, hold);
      this.lookFrom(pos, look, s.fov);
      this.setClip(.05, 1500);
      out.stop = c.stop; out.card = smooth(.06, .28, t) * (1 - smooth(.86, 1, t));
      out.labelInk = .85; out.indoor = c.stop > 0; out.floor = s.floor;
    } else if (c.kind === 'walk') {
      this.walkPose(c.leg, t);
      out.labelInk = .85; out.indoor = true; out.floor = c.leg.floor;
      out.stop = null;
    } else if (c.kind === 'rise' || c.kind === 'floorplan' || c.kind === 'drop') {
      const r = this.liftPose(c, t);
      Object.assign(out, r);
      out.floor = c.leg.floor;
      // Seen from above, the floor's plan reads on its own: the neighbours sink away while the camera is up there.
      out.context = c.kind === 'rise' ? smooth(.15, .6, t) : c.kind === 'floorplan' ? 1 : 1 - smooth(.35, .85, t);
      out.site = c.kind === 'rise' ? smooth(.3, .8, t) : c.kind === 'floorplan' ? 1 : 1 - smooth(.25, .75, t);
    } else {
      Object.assign(out, this.outroPose(c, t, sf));
    }
    // Drawn lines stop at the sheet border while the page is a sheet: the opening, the lift, a floor's plan seen from
    // above and the closing plan.
    out.clip = c.kind === 'sheet' || c.kind === 'lift' ? 1 : c.kind === 'descend' ? 1 - smooth(0, .2, t)
      : c.kind === 'outro' ? smooth(.75, 1, t) : ['colour', 'wipe', 'end'].includes(c.kind) ? 1 : out.sheetInk > .5 ? 1 : 0;
    this.applyReveals(p, out);
    this.applyDoors(p);
    // The lens shift (a vertical view offset, in half-heights of the frame).
    if (Math.abs(out.shift || 0) > 1e-4) {
      cam.view = cam.view || { enabled: true, fullWidth: 1, fullHeight: 1, offsetX: 0, offsetY: 0, width: 1, height: 1 };
      cam.view.enabled = true; cam.view.offsetY = out.shift / 2;
    } else if (cam.view) cam.view.enabled = false;
    cam.updateProjectionMatrix();
    cam.updateMatrixWorld();
    return out;
  }

  // The pose the lift settles on: a high three-quarter view from the street side with the whole plot in frame. In
  // perspective the near corner of the front garden is what overflows first, so the distance and the aim are solved
  // by projecting the plot's corners and the house's roof corners into the view.
  liftEnd() {
    const a = this.aspect();
    if (this._liftEnd?.aspect === a) return this._liftEnd.pose;
    const fov = 40, tn = Math.tan(fov * DEG / 2), elev = 48;
    const entry = this.stops[0].stand;
    const toStreet = Math.atan2(entry[1] - this.houseCenter[1], entry[0] - this.houseCenter[0]);
    const az = toStreet + 24 * DEG * (entry[0] >= this.houseCenter[0] ? -1 : 1);
    const dir = new THREE.Vector3(Math.cos(elev * DEG) * Math.cos(az), Math.sin(elev * DEG), -Math.cos(elev * DEG) * Math.sin(az));
    const fwd = dir.clone().negate(), right = new THREE.Vector3().crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize();
    const up = new THREE.Vector3().crossVectors(right, fwd);
    const xs = this.data.plot.map((q) => q[0]), ys = this.data.plot.map((q) => q[1]);
    const pts = [];
    for (const x of [Math.min(...xs), Math.max(...xs)]) for (const y of [Math.min(...ys), Math.max(...ys)]) pts.push(s2t([x, y, this.ground]));
    for (const x of [this.house.x0, this.house.x1]) for (const y of [this.house.y0, this.house.y1]) pts.push(s2t([x, y, this.top]));
    // The frame the plot must sit in, in NDC: clear of the header above and the chapter marks below.
    const lim = { x: .8, top: .66, bottom: .78 };
    const extent = (target, d) => {
      const pos = target.clone().addScaledVector(dir, d), v = new THREE.Vector3();
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (const q of pts) {
        v.subVectors(q, pos);
        const z = v.dot(fwd), x = v.dot(right) / (z * tn * a), y = v.dot(up) / (z * tn);
        x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
      }
      return { x0, x1, y0, y1, fit: Math.max(-x0 / lim.x, x1 / lim.x, y1 / lim.top, -y0 / lim.bottom) };
    };
    let target = s2t([this.houseCenter[0], this.houseCenter[1], 1.2]), dist = 60;
    for (let pass = 0; pass < 3; pass++) {
      let lo = 4, hi = 600;
      for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (extent(target, m).fit > 1) lo = m; else hi = m; }
      dist = hi;
      const e = extent(target, dist), cy = (lim.top - lim.bottom) / 2;
      target = target.clone().addScaledVector(right, (e.x0 + e.x1) / 2 * dist * tn * a).addScaledVector(up, ((e.y0 + e.y1) / 2 - cy) * dist * tn);
    }
    const pose = { fov, Hv: 2 * dist * tn, dist, target, az, elev, pos: target.clone().addScaledVector(dir, dist) };
    this._liftEnd = { aspect: a, pose };
    return pose;
  }

  walkPose(leg, t) {
    const cv = leg.curve, L = Math.max(leg.length, .01), e = easeIO(t);
    const u = clamp(e);
    const pos = cv.getPointAt(u);
    const ahead = cv.getPointAt(clamp(u + 1.8 / L));
    const tangent = ahead.clone().sub(pos);
    if (tangent.lengthSq() < 1e-6) tangent.copy(cv.getTangentAt(clamp(u)));
    tangent.setY(0).normalize();
    const from = this.stops[leg.from], to = this.stops[leg.to];
    const walkLook = pos.clone().addScaledVector(tangent, 3).setY(pos.y - .12);
    const look = walkLook.clone()
      .lerp(s2t(to.look), smooth(.55, 1, t))
      .lerp(s2t(from.look), (1 - smooth(0, .22, t)) * (leg.kind === 'lift' ? 0 : 1));
    this.lookFrom(pos, look, lerp(leg.kind === 'lift' ? 62 : from.fov, to.fov, smooth(.4, 1, t)));
    this.setClip(.05, 1500);
  }

  // Doors and gates swing open a couple of metres before the camera reaches them, and close again when the visitor
  // scrolls back past that point: a door's state is a function of scroll position like everything else.
  scheduleDoors() {
    this.doors = [];
    const items = this.viewer.openings?.items || [];
    for (const c of this.chapters) {
      if (c.kind !== 'walk' || !c.leg.opens?.length) continue;
      const pts = c.leg.points.map(s2t), L = Math.max(c.leg.length, .01);
      for (const id of c.leg.opens) {
        for (const item of items) {
          if (item.id !== id && !item.id.startsWith(id + '-') || this.doors.some((d) => d.item === item)) continue;
          let best = 0, bestD = Infinity, run = 0;
          pts.forEach((q, i) => { if (i) run += q.distanceTo(pts[i - 1]); const d = q.distanceTo(item.center); if (d < bestD) { bestD = d; best = run; } });
          const t = invertEase(easeIO, clamp((best - 2.6) / L));
          this.doors.push({ item, at: c.start + t * c.len });
        }
      }
    }
  }

  applyDoors(p) {
    const ctl = this.viewer.openings;
    for (const d of this.doors || []) {
      // Open (1) from a few steps before the camera reaches it; before that, the door keeps the design's own pose.
      const v = Math.max(d.item.initial ?? 0, clamp((p - d.at) / .3));
      if (Math.abs(v - d.item.value) < 1e-4) continue;
      d.item.value = d.item.goal = v;
      ctl.pose(d.item);
      this.viewer.dirty = true;
    }
  }

  liftPose(c, t) {
    const leg = c.leg, H = this.H, from = this.stops[leg.from], to = leg.floor * H;
    const fromLevel = leg.fromFloor * H;
    const b = this.data.sheets.find((s) => s.floor === leg.floor)?.bounds || this.data.sheets[0].bounds;
    const center = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
    const a = this.aspect();
    const Hv = Math.max((b[3] - b[1]) / .82, (b[2] - b[0]) / (.9 * a));
    const fov = 34, high = Hv / (2 * Math.tan(fov * DEG / 2));
    const planTarget = s2t([center[0], center[1], to]);
    const out = { cut: 1e5, labelInk: .85, sheetInk: 0, sky: 1, indoor: false, sheet: 0 };
    if (c.kind === 'rise') {
      const S = s2t(from.stand), L = s2t(from.look), e = easeIO(t);
      const pos = S.clone().lerp(planTarget.clone().setY(to + high), e);
      pos.x = lerp(S.x, planTarget.x, smooth(.3, 1, t)); pos.z = lerp(S.z, planTarget.z, smooth(.3, 1, t));
      const down = smooth(0, .45, t);
      const look = L.clone().lerp(planTarget, down);
      const up = new THREE.Vector3(0, 1, 0).lerp(new THREE.Vector3(0, 0, -1), smooth(.25, .6, t)).normalize();
      this.lookFrom(pos, look, lerp(from.fov, fov, e), up);
      this.setClip(.05, 1500);
      out.cut = Math.min(Math.max(pos.y - .5, fromLevel + 2.55), to + 1.2 + (to > fromLevel ? 0 : 0));
      if (to < fromLevel) out.cut = Math.max(to + 1.2, Math.min(fromLevel + 2.55, pos.y - .5));
      out.labelInk = .85 * (1 - smooth(.2, .7, t));
      out.sheetInk = smooth(.55, 1, t);
    } else if (c.kind === 'floorplan') {
      this.lookFrom(planTarget.clone().setY(to + high * (1 - .03 * t)), planTarget, fov, new THREE.Vector3(0, 0, -1));
      this.setClip(.05, 1500);
      out.cut = to + 1.2; out.sheetInk = 1; out.labelInk = 0; out.sheet = .6;
    } else {
      const start = s2t(leg.points[0]), next = s2t(leg.points[Math.min(3, leg.points.length - 1)]), e = easeIO(t);
      const dir = next.clone().sub(start).setY(0).normalize();
      const pos = planTarget.clone().setY(to + high).lerp(start, e);
      const look = planTarget.clone().lerp(start.clone().addScaledVector(dir, 3).setY(start.y - .1), smooth(.45, 1, t));
      const up = new THREE.Vector3(0, 0, -1).lerp(new THREE.Vector3(0, 1, 0), smooth(.45, .9, t)).normalize();
      this.lookFrom(pos, look, lerp(fov, 62, smooth(.4, 1, t)), up);
      this.setClip(.05, 1500);
      out.cut = t < .995 ? to + 1.2 + (H - .8) * smooth(.5, .98, t) : 1e5;
      out.sheetInk = 1 - smooth(0, .4, t); out.labelInk = .85 * smooth(.5, 1, t);
    }
    return out;
  }

  // The closing plan is framed on the plot itself; the wipe and the end card return to the sheet's framing.
  plotFrame() {
    const xs = this.data.plot.map((q) => q[0]), ys = this.data.plot.map((q) => q[1]);
    const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
    return { Hv: Math.max(h / .8, w / (.86 * this.aspect())), target: s2t([(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2, 0]) };
  }

  outroPose(c, t, sf) {
    const out = { cut: 1e5, sheetInk: 0, labelInk: 0, sky: 1, all: 1, wipe: 0, sheet: 0, indoor: false, context: 1, poche: 1, site: 1 };
    const last = this.stops[this.stops.length - 1];
    const lastLevel = last.floor * this.H;
    const sheetTarget = s2t([sf.target[0], sf.target[1], 0]), plot = this.plotFrame();
    const radius = Math.hypot(this.house.x1 - this.house.x0, this.house.y1 - this.house.y0);
    if (c.kind === 'outro') {
      const S = s2t(last.stand), L = s2t(last.look), e = easeIO(t);
      const fov = Math.exp(lerp(Math.log(last.fov), Math.log(2), smooth(.15, 1, t)));
      const d = plot.Hv / (2 * Math.tan(fov * DEG / 2));
      const high = plot.target.clone().setY(d);
      const pos = S.clone().lerp(high, smooth(0, 1, e));
      const look = L.clone().lerp(plot.target, smooth(0, .5, t));
      const up = new THREE.Vector3(0, 1, 0).lerp(new THREE.Vector3(0, 0, -1), smooth(.1, .5, t)).normalize();
      this.lookFrom(pos, look, fov, up);
      this.setClip(Math.max(.05, pos.y - radius * 2.5 - 40 - this.top), pos.y + radius * 3 + 80);
      // The house is cut back down to its ground-floor plan as the camera climbs: the floors melt into the drawing.
      const climb = Math.max(pos.y - .5, lastLevel + 2.55);
      out.cut = Math.min(climb, lerp(this.top + 1.5, 1.2, smooth(.12, .62, t)));
      out.all = smooth(.05, .45, t);
      out.planLight = smooth(.3, .8, t);
      out.context = smooth(.25, .7, t);
      out.poche = smooth(.5, .85, t);
      // Beyond the plot the site folds back into paper: the plan arrives in colour on its sheet.
      out.site = smooth(.25, .75, t);
    } else {
      // The colour plan holds on the plot, then eases back to the sheet's framing for the paper to roll over it.
      const k = c.kind === 'colour' ? smooth(.55, 1, t) : 1;
      const Hv = lerp(plot.Hv, sf.Hv, k), at = plot.target.clone().lerp(sheetTarget, k);
      const d = Hv / (2 * Math.tan(1 * DEG));
      this.lookFrom(at.clone().setY(d), at, 2, new THREE.Vector3(0, 0, -1));
      this.setClip(Math.max(.05, d - radius * 2.5 - 40), d + radius * 3 + 80);
      out.cut = 1.2;
      out.planLight = 1;
      if (c.kind === 'colour') { out.all = 1; }
      // The paper rolls from where the drawing starts (the title side is paper already) to the far border.
      else if (c.kind === 'wipe') { out.wipe = lerp(.42, 1.02, easeIO(t)); out.all = 1; out.sheetInk = smooth(.3, .9, t); out.sheet = 1; }
      else { out.all = 1; out.wipe = 1.02; out.sheetInk = 1; out.sheet = 1; }
      out.sky = 0;
    }
    return out;
  }

  applyReveals(p, out) {
    const soft = .35, dur = .45;
    for (const [room, r] of this.reveals) {
      const k = (p - r.at) / dur;
      this.mask.set(room, k <= 0 ? -1 : k, r.origin);
    }
    const o = (p - this.outdoorAt) / this.outdoorLen;
    const site = this.data.maskOutside.reach;
    const origin = this.stops[0].stand;
    this.mask.set('outside', o <= 0 ? -1 : o, [origin[0], origin[1]]);
    const fx = this.viewer.reveal;
    fx.get('uOutside').set(origin[0], origin[1], o <= 0 ? -1 : clamp(o) * (site + soft) + (o >= 1 ? 1e4 : 0));
    fx.set('uSky', Math.max(out.sky * clamp(o * 1.4), out.all));
    fx.set('uAll', out.all);
    fx.set('uWipe', out.wipe);
    fx.set('uSheet', out.sheet);
    fx.set('uSoft', soft);
  }
}
