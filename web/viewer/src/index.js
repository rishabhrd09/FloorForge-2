/* FloorForge realistic walkthrough viewer.
   Offline Three.js renderer for the generated scene contract: physically based materials synthesised
   on the GPU, analytic sky + sun + image-based light, soft shadows, ambient occlusion, bloom, filmic grade,
   procedural planting and a first-person walk (WASD, mouse look, Shift run, Space jump, C crouch). */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer, RenderPass, EffectPass, BloomEffect, SMAAEffect, SMAAPreset, KernelSize } from 'postprocessing';
import { N8AOPostPass } from 'n8ao';
import { TextureSynth } from './textures.js';
import { MaterialLibrary } from './materials.js';
import { Environment, GRADES } from './environment.js';
import { buildBuckets, visibilityClass } from './scene-builder.js';
import { Walker } from './walker.js';
import { ParkedVehicle } from './vehicle.js';
import { OpeningController, describeOpenings } from './openings.js';
import { GradeEffect } from './grade.js';
import { Vegetation } from './vegetation.js';
import { Hud } from './hud.js';
import { buildContext } from './context.js';
import { exportPresentation } from './export.js';
import { frameBox } from './framing.js';
import { pointInPolygon, clamp } from './util.js';

const QUALITY = {
  ultra: { pixelRatio: 2, ao: true, aoHalf: false, aoMode: 'High', bloom: true, shadow: 'ultra', smaa: true, lights: 10, veg: 1.2, textures: 'high' },
  high: { pixelRatio: 1.5, ao: true, aoHalf: true, aoMode: 'Medium', bloom: true, shadow: 'high', smaa: true, lights: 8, veg: 1, textures: 'high' },
  balanced: { pixelRatio: 1, ao: true, aoHalf: true, aoMode: 'Low', bloom: true, shadow: 'balanced', smaa: true, lights: 6, veg: .6, textures: 'balanced' },
  performance: { pixelRatio: .75, ao: false, aoHalf: true, aoMode: 'Performance', bloom: false, shadow: 'performance', smaa: false, lights: 4, veg: .3, textures: 'performance' },
};
const ORDER = ['ultra', 'high', 'balanced', 'performance'];
const DIRECTED = new Set(['downlight', 'soffit', 'uplight']);
const WALK_KEYS = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'ShiftLeft', 'ShiftRight', 'KeyC', 'ControlLeft', 'KeyE', 'KeyQ', 'KeyF']);

const s2t = (p) => new THREE.Vector3(p[0], p[2], -p[1]); // scene (Z-up) point -> Three (Y-up)
// Share of the frame the home fills: the studio's hero view keeps a little street around it; Focus fills the view.
const HERO_FILL = .84, FOCUS_FILL = .94;

function detectQuality() {
  const coarse = matchMedia?.('(pointer: coarse)').matches;
  const small = Math.min(screen.width, screen.height) < 700;
  const mem = navigator.deviceMemory || 8;
  if (coarse || small || mem <= 3) return 'balanced';
  return 'high';
}

class FloorForgeViewer {
  constructor(canvas, { onStatus = () => {}, quality = 'auto', hudInset = 16 } = {}) {
    this.canvas = canvas;
    this.onStatus = onStatus;
    this.qualityName = quality === 'auto' ? detectQuality() : quality;
    this.autoQuality = quality === 'auto';
    this.q = QUALITY[this.qualityName];
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: 'high-performance', stencil: false, preserveDrawingBuffer: false });
    if (!renderer.capabilities.isWebGL2) throw Error('WebGL2 is unavailable. The drawing and project exports still work.');
    this.renderer = renderer;
    this.gl = renderer.getContext();
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.localClippingEnabled = true;
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(43, 1, .05, 1500);
    this.camera.rotation.order = 'YXZ';
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = .08;
    this.controls.maxPolarAngle = Math.PI * .495;
    this.controls.minDistance = 1.5;
    this.controls.maxDistance = 160;
    this.controls.addEventListener('change', () => { this.dirty = true; });
    this.controls.addEventListener('start', () => { this.tour = false; this.interacting = true; this.zoomAnim = null; this.fitHeld = null; });
    this.controls.addEventListener('end', () => { this.interacting = false; this.settle = performance.now(); });
    this.env = new Environment(renderer, this.scene, { quality: this.q.shadow });
    this.synth = new TextureSynth(renderer, { quality: this.q.textures });
    this.root = new THREE.Group();
    this.scene.add(this.root);
    this.meshes = [];
    this.lightPool = [];
    this.probes = new Map();
    this.mode = 'solid';
    this.floor = 0;
    this.gradeName = 'day';
    this.clay = false;
    this._tour = false;
    this.dirty = true;
    this.keys = new Set();
    this.input = { forward: 0, strafe: 0, run: false, jump: false, crouch: false };
    this.listeners = [];
    this.frames = 0;
    this.frameTimes = [];
    this.lastTick = performance.now();
    this.time = 0;
    this.disposed = false;
    this.buildComposer();
    this.bindInput();
    this.resizeObserver = new ResizeObserver(() => { this.resized = true; this.dirty = true; });
    this.resizeObserver.observe(canvas);
    this.hud = new Hud(canvas, { onLock: () => this.lock(), onJump: () => { this.input.jump = true; }, onInteract: () => this.interactOpening(), inset: hudInset });
    const loop = () => { if (this.disposed) return; this.raf = requestAnimationFrame(loop); this.tick(); };
    this.raf = requestAnimationFrame(loop);
  }

  // ---------- rendering pipeline ----------
  buildComposer() {
    this.composer?.dispose();
    const r = this.renderer;
    this.composer = new EffectComposer(r, { frameBufferType: THREE.HalfFloatType, multisampling: 0, stencilBuffer: false });
    this.renderPass = new RenderPass(this.scene, this.camera);
    this.composer.addPass(this.renderPass);
    this.aoPass = null;
    if (this.q.ao) {
      this.aoPass = new N8AOPostPass(this.scene, this.camera, 512, 512);
      this.aoPass.setQualityMode(this.q.aoMode);
      Object.assign(this.aoPass.configuration, { aoRadius: 1.1, distanceFalloff: .45, intensity: 2.6, halfRes: this.q.aoHalf, gammaCorrection: false, transparencyAware: false, color: new THREE.Color(0, 0, 0) });
      this.composer.addPass(this.aoPass);
    }
    this.gradeEffect = new GradeEffect();
    this.bloom = this.q.bloom ? new BloomEffect({ mipmapBlur: true, luminanceThreshold: .95, luminanceSmoothing: .25, intensity: .3, radius: .72 }) : null;
    const effects = this.bloom ? [this.bloom, this.gradeEffect] : [this.gradeEffect];
    this.composer.addPass(new EffectPass(this.camera, ...effects));
    if (this.q.smaa) this.composer.addPass(new EffectPass(this.camera, new SMAAEffect({ preset: SMAAPreset.HIGH })));
    this.resized = true;
  }

  setQuality(name) {
    if (!QUALITY[name] || name === this.qualityName) return;
    this.qualityName = name;
    this.q = QUALITY[name];
    this.env.setShadowQuality(this.q.shadow);
    this.buildComposer();
    this.applyGrade();
    this.vegetation?.setDensity(this.q.veg);
    this.rebuildLightPool();
    this.dirty = true;
    this.onStatus(`Rendering quality: ${name}`);
  }

  resize() {
    const c = this.canvas;
    const w = Math.max(1, c.clientWidth), h = Math.max(1, c.clientHeight);
    const ratio = Math.min(window.devicePixelRatio || 1, this.q.pixelRatio);
    this.renderer.setPixelRatio(ratio);
    this.renderer.setSize(w, h, false);
    this.composer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.resized = false;
    // A framing the visitor has not touched since it was set follows the canvas (large view, full screen, rotation).
    if (this.fitHeld && this.mode !== 'walk') this.fitHouse({ ...this.fitHeld, animate: false });
  }

  // ---------- scene ----------
  setScene(data, building = data.opening_model) {
    if (data.up !== 'Z' || data.units !== 'm') throw Error('Scene must use Z-up metres.');
    const started = performance.now();
    if (this.mode === 'walk') this.leaveWalk();
    this.highlightRoom(null);
    this.clearScene();
    this.data = data;
    this.H = data.floor_height;
    this.materials = new MaterialLibrary(this.synth, data.materials);
    const descriptors = describeOpenings(data, data.opening_model || building);
    const movingIds = new Set(descriptors.flatMap(d => d.parts.flatMap(p => p.ids)));
    const buckets = buildBuckets({ ...data, nodes: data.nodes.filter(n => !movingIds.has(n.id) && n.owner !== 'parked-car') }, this.materials);
    const collision = [];
    for (const b of buckets) {
      this.addBucket(b);
      if (b.collide) collision.push(b.geometry);
    }
    // Site bounds, sun and shadow frustum.
    const [x0, y0, z0, x1, y1, z1] = data.bounds;
    this.boundsScene = data.bounds;
    const center = s2t([(x0 + x1) / 2, (y0 + y1) / 2, 0]);
    const radius = Math.hypot(x1 - x0, y1 - y0) * .5 + 4;
    this.center = center; this.radius = radius;
    this.env.setSite(data.solar?.vector_local || [.4, -.5, .75], center, radius);
    this.addGround();
    // Procedural planting, lawns and indoor plants (seeded, deterministic).
    this.vegetation = new Vegetation(this, data, { density: this.q.veg });
    this.root.add(this.vegetation.group);
    // Viewer-only neighbourhood context (not part of the design or exports).
    this.context = buildContext(this, data);
    this.root.add(this.context);
    this.footprint = data.footprint;
    this.topZ = data.storeys * data.floor_height;
    // Walking physics on the actual geometry.
    const merged = this.mergeForCollision(collision);
    const pad = 7.5;
    this.walker = new Walker(merged, {
      min: new THREE.Vector3(x0 - pad, z0 - 2, -(y1 + pad)),
      max: new THREE.Vector3(x1 + pad, z1 + 10, -(y0 - pad)),
    });
    this.walker.respawn = () => this.spawn('arrival');
    this.openings = new OpeningController(this, descriptors);
    const carNodes = data.nodes.filter(n => n.owner === 'parked-car');
    this.vehicle = carNodes.length ? new ParkedVehicle(this, carNodes) : null;
    this.rooms = (data.rooms || []).map((r) => ({ ...r }));
    this.rebuildLightPool();
    this.setGrade(this.gradeName);
    this.floor = 0;
    this.mode = this.mode === 'walk' ? 'solid' : this.mode;
    this.reset();
    this.applyVisibility();
    this.onModeChange?.(this.mode);
    this.onFloorChange?.(this.floor);
    this.dirty = true;
    const ms = Math.round(performance.now() - started);
    this.onStatus(`${data.nodes.length.toLocaleString()} objects · ${this.meshes.length} merged surfaces · ${this.vegetation.count} plants · realistic render ready in ${ms} ms`);
  }

  addBucket(b, parent = this.root) {
    const clipped = b.cls === 'clip', mat = this.materials.get(b.material, clipped);
    const material = b.doubleSided && mat.side !== THREE.DoubleSide ? this.doubleSided(mat, b.material, clipped) : mat;
    const mesh = new THREE.Mesh(b.geometry, material);
    mesh.castShadow = !b.transparent && !this.data.materials[b.material]?.emission;
    mesh.receiveShadow = !b.transparent;
    mesh.userData = { bucket: b, baseMaterial: material };
    if (b.transparent) mesh.renderOrder = 2;
    parent.add(mesh); this.meshes.push(mesh);
    return mesh;
  }

  get hasCar() { return Boolean(this.vehicle); }
  get carVisible() { return Boolean(this.vehicle?.visible); }
  setCarVisible(visible) { return this.vehicle?.setVisible(visible) ?? false; }

  interactOpening() {
    if (this.mode !== 'walk') return false;
    const result = this.openings?.interact() || false;
    this.canvas.focus?.();
    return result;
  }

  highlightRoom(id) {
    if (this.roomHighlight) {
      this.root.remove(this.roomHighlight);
      this.roomHighlight.traverse((object) => { object.geometry?.dispose(); object.material?.dispose(); });
      this.roomHighlight = null;
    }
    this.selectedRoomId = null;
    const room = id && this.data?.rooms?.find((item) => item.id === id);
    if (!room) { this.dirty = true; return; }
    const shape = new THREE.Shape(room.polygon.map(([x, y]) => new THREE.Vector2(x, y)));
    const mesh = new THREE.Mesh(new THREE.ShapeGeometry(shape), new THREE.MeshBasicMaterial({
      color: '#55cc91', transparent: true, opacity: .48, side: THREE.DoubleSide, depthTest: false, depthWrite: false,
    }));
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.y = room.floor * this.H + .04;
    mesh.renderOrder = 100;
    this.roomHighlight = mesh;
    this.selectedRoomId = id;
    this.root.add(mesh);
    this.setFloor(room.floor);
    this.setMode('dollhouse');
    this.dirty = true;
  }

  doubleSided(mat, name, clipped) {
    const key = name + (clipped ? '|clip' : '') + '|ds';
    this._ds ||= new Map();
    if (!this._ds.has(key)) { const m = mat.clone(); m.side = THREE.DoubleSide; if (mat.onBeforeCompile) { m.onBeforeCompile = mat.onBeforeCompile; m.customProgramCacheKey = mat.customProgramCacheKey; } this._ds.set(key, m); }
    return this._ds.get(key);
  }

  mergeForCollision(geometries) {
    let count = 0;
    for (const g of geometries) count += g.attributes.position.count;
    const pos = new Float32Array(count * 3);
    let o = 0;
    for (const g of geometries) { pos.set(g.attributes.position.array, o); o += g.attributes.position.array.length; }
    const merged = new THREE.BufferGeometry();
    merged.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    return merged;
  }

  // Distant ground that fades into atmospheric haze so the site never floats in a void.
  addGround() {
    const [x0, y0, z0] = this.data.bounds;
    const synthGrass = this.synth.make('grass', { base: '#5f7a3c', alt: '#a39a5c' });
    const g = new THREE.CircleGeometry(900, 64);
    const uv = g.attributes.uv; const pos = g.attributes.position;
    for (let i = 0; i < uv.count; i++) uv.setXY(i, pos.getX(i) / 2.4, pos.getY(i) / 2.4);
    const m = new THREE.MeshStandardMaterial({ map: synthGrass.map, normalMap: synthGrass.normalMap, roughnessMap: synthGrass.roughnessMap, color: '#9aa27f' });
    m.name = 'ground';
    const ground = new THREE.Mesh(g, m);
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(this.center.x, z0 - .16, this.center.z);
    ground.receiveShadow = true;
    ground.userData.ground = true;
    this.root.add(ground);
    this.groundMesh = ground;
  }

  clearScene() {
    this.clearProbes();
    this.openings?.dispose(); this.openings = null;
    this.vehicle?.dispose(); this.vehicle = null;
    this.hud?.setInteraction(null);
    for (const m of this.meshes) m.geometry.dispose();
    this.meshes = [];
    this.vegetation?.dispose();
    this.vegetation = null;
    this.context?.userData.dispose?.();
    this.context = null;
    if (this.groundMesh) { this.groundMesh.geometry.dispose(); this.groundMesh.material.dispose(); this.groundMesh = null; }
    this.root.clear();
    this.walker?.dispose();
    this.walker = null;
    this.materials?.dispose();
    this._ds?.forEach((m) => m.dispose());
    this._ds = new Map();
    for (const l of this.lightPool) { this.scene.remove(l); if (l.target) this.scene.remove(l.target); }
    this.lightPool = [];
  }

  // ---------- lights ----------
  // Fixture lights are pooled: the nearest fittings to the visitor (or orbit target) are live. Recessed and
  // soffit downlights are downward spotlights, so they pool light on floors and walls and leave the ceiling
  // around them dark, as real downlights do; garden uplights point up; other fittings radiate all round.
  rebuildLightPool() {
    for (const l of this.lightPool) { this.scene.remove(l); if (l.target) this.scene.remove(l.target); }
    this.lightPool = [];
    if (!this.data) return;
    const lights = this.data.lights || [];
    const n = Math.min(this.q.lights, lights.length);
    const directed = lights.filter((l) => DIRECTED.has(l.kind)).length;
    const spots = Math.min(directed, Math.round(n * .6)), points = Math.min(n - spots, lights.length - directed);
    for (let i = 0; i < spots + points; i++) {
      const l = i < spots ? new THREE.SpotLight('#ffd7a8', 0, 9, 1.0, .75, 2) : new THREE.PointLight('#ffd7a8', 0, 9, 2);
      l.castShadow = false;
      this.scene.add(l);
      if (l.target) this.scene.add(l.target);
      this.lightPool.push(l);
    }
    this.spotCount = spots;
    this.lightKey = '';
  }

  // `origin` overrides the visitor's eye, e.g. to light a room probe capture from the room's own fittings.
  updateLights(force = false, origin = null) {
    const lights = this.data?.lights || [];
    if (!this.lightPool.length || !lights.length) return;
    const eye = origin || this.camera.position;
    const level = GRADES[this.gradeName].lamps;
    const walk = this.mode === 'walk';
    // Re-rank fittings only once the viewpoint has moved 25 cm (the ranking sorts every fitting and ray-casts).
    const at = walk ? eye : this.controls.target;
    if (!force && !origin && this._lightsAt && this._lightsAt.distanceToSquared(at) < .0625) return;
    if (!origin) (this._lightsAt ||= new THREE.Vector3()).copy(at);
    const scored = lights.map((l, i) => {
      const p = s2t(l.position);
      let d = p.distanceTo(walk ? eye : this.controls.target);
      if (walk && Math.abs(p.y - eye.y) > 2.6) d += 20; // prefer fittings on the visitor's own level
      return { i, p, d, l };
    }).sort((a, b) => a.d - b.d);
    if (walk && this.walker) {
      // Lights do not cast shadows, so a fitting behind a wall would leak through it: when walking, only
      // fittings with a line of sight to the visitor or to the middle of the current room stay candidates.
      const room = this.probeRoom || this.roomAt(eye);
      const middle = room ? this.probePosition(room) : null;
      for (const s of scored.slice(0, 24)) {
        if (!this.walker.sees(s.p, eye) && !(middle && this.walker.sees(s.p, middle))) s.d += 60;
      }
      scored.sort((a, b) => a.d - b.d);
    }
    // Outside, the up-lights nearest the camera (washing a boundary wall or a tree) keep a few spot slots; the
    // rest go to the fittings nearest the point being looked at, as before.
    let spots = [];
    if (!walk && this.spotCount > 3) {
      spots = scored.filter((s) => s.l.kind === 'uplight').map((s) => ({ ...s, e: s.p.distanceTo(eye) }))
        .filter((s) => s.e < 16).sort((a, b) => a.e - b.e).slice(0, Math.min(3, this.spotCount >> 1));
    }
    const taken = new Set(spots.map((s) => s.i));
    spots = spots.concat(scored.filter((s) => DIRECTED.has(s.l.kind) && !taken.has(s.i)).slice(0, this.spotCount - spots.length));
    const points = scored.filter((s) => !DIRECTED.has(s.l.kind)).slice(0, this.lightPool.length - this.spotCount);
    const key = spots.map((s) => s.i).join(',') + '/' + points.map((s) => s.i).join(',') + '|' + level + (origin ? '|probe' : '');
    if (!force && key === this.lightKey) return;
    this.lightKey = key;
    const assign = (s, light) => {
      light.position.copy(s.p);
      light.color.set(s.l.color || '#ffdfae');
      light.intensity = (s.l.power_w || 10) * .9 * level;
      light.distance = s.l.power_w > 20 ? 11 : 7;
      if (light.isSpotLight) {
        const up = s.l.kind === 'uplight';
        light.angle = up ? .55 : 1.0;
        light.target.position.set(s.p.x, s.p.y + (up ? 3 : -3), s.p.z);
        light.target.updateMatrixWorld();
      }
    };
    spots.forEach((s, k) => assign(s, this.lightPool[k]));
    for (let k = spots.length; k < this.spotCount; k++) this.lightPool[k].intensity = 0;
    points.forEach((s, k) => assign(s, this.lightPool[this.spotCount + k]));
    for (let k = this.spotCount + points.length; k < this.lightPool.length; k++) this.lightPool[k].intensity = 0;
  }

  // ---------- grades ----------
  setGrade(name) {
    this.gradeName = GRADES[name] ? name : ({ golden: 'golden', dusk: 'dusk' }[name] || 'day');
    this.clearProbes();
    this.metered = null;
    this.env.setGrade(this.gradeName);
    this.applyGrade();
    this.dirty = true;
  }

  // Camera-like adaptation: a visitor indoors sees a brighter, warmer-balanced exposure, as a phone camera would.
  isIndoors(p) {
    if (!this.footprint) return false;
    const x = p.x, y = -p.z, z = p.y;
    if (z > this.topZ) return z < this.topZ + 2.5 && this.rooms.some(r => r.floor === this.data.roof_level && r.kind === 'stair' && pointInPolygon(x, y, r.polygon));
    if (!pointInPolygon(x, y, this.footprint)) return false;
    const floor = clamp(Math.floor(z / this.H), 0, this.data.storeys - 1);
    for (const r of this.rooms) if (r.kind === 'terrace' && r.floor === floor && pointInPolygon(x, y, r.polygon)) return false;
    return true;
  }

  // Indoor metering target for a room, from its probe: exposure so the room's mean radiance (windows included)
  // sits at a bright interior key, and white-balance gains that neutralise most, not all, of its colour cast.
  meterRoom() {
    const g = GRADES[this.gradeName];
    const lit = this.gradeName === 'dusk' || this.gradeName === 'night';
    const stats = this.env.probe?.stats;
    if (!stats) return { exposure: g.exposure * (g.indoor ?? 1.5), balance: [1, 1, 1] };
    const key = lit ? .22 : .68;
    const exposure = clamp(Math.pow(key / stats.luminance, .85) * Math.pow(g.exposure, .15), g.exposure * .06, g.exposure * 4);
    const strength = lit ? .55 : .7, bias = lit ? .12 : .06;
    let gr = Math.pow(stats.g / stats.r, strength) * (1 + bias), gb = Math.pow(stats.g / stats.b, strength) * (1 - bias);
    gr = clamp(gr, .75, 1.4); gb = clamp(gb, .7, 1.4);
    const norm = .2126 * gr + .7152 + .0722 * gb;
    return { exposure, balance: [gr / norm, 1 / norm, gb / norm] };
  }

  baseWarmth() {
    return this.gradeName === 'golden' ? .45 : this.gradeName === 'dusk' ? .05 : this.gradeName === 'night' ? -.15 : .05;
  }

  adapt(dt) {
    const target = this.mode === 'walk' && this.isIndoors(this.camera.position) ? 1 : 0;
    const prev = this.indoor || 0;
    this.indoor = Math.abs(target - prev) < .002 ? target : prev + (target - prev) * (1 - Math.exp(-2.2 * dt));
    // Eye/camera adaptation between rooms.
    const meter = this.meterRoom();
    const fresh = !this.metered;
    const m = this.metered || (this.metered = { exposure: meter.exposure, balance: [...meter.balance] });
    const k = 1 - Math.exp(-2.5 * dt);
    const changed = fresh || Math.abs(meter.exposure - m.exposure) > 1e-3 || meter.balance.some((v, i) => Math.abs(v - m.balance[i]) > 1e-3);
    if (changed) {
      m.exposure += (meter.exposure - m.exposure) * k;
      m.balance = m.balance.map((v, i) => v + (meter.balance[i] - v) * k);
    }
    if (changed || Math.abs(this.indoor - prev) > 1e-4 || this._adaptDirty) { this._adaptDirty = false; this.applyGrade(); }
  }

  applyGrade() {
    const g = GRADES[this.gradeName];
    const inside = this.indoor || 0;
    const m = this.metered || this.meterRoom();
    const exposure = g.exposure + (m.exposure - g.exposure) * inside;
    this.gradeEffect.set('exposure', exposure);
    // Bloom only what the exposed image renders near white, whatever the metered exposure.
    if (this.bloom) this.bloom.luminanceMaterial.threshold = .95 / exposure;
    this.gradeEffect.set('warmth', this.baseWarmth());
    this.gradeEffect.uniforms.get('balance').value.set(...m.balance.map((v) => 1 + (v - 1) * inside));
    this.gradeEffect.set('contrast', this.gradeName === 'overcast' ? 1.0 : 1.03);
    this.gradeEffect.set('saturation', this.gradeName === 'overcast' ? .96 : 1.0);
    this.gradeEffect.set('punch', g.punch ?? .3);
    if (this.bloom) this.bloom.intensity = g.bloom;
    this.materials?.setLampLevel(g.lamps);
    this.updateLights(true);
  }

  // ---------- room light probes ----------
  // The room (scene rooms metadata) containing a Three-space point, on the storey the point stands on.
  // Storey a standing height (feet, Three Y) belongs to; half-way up the stair still counts as the lower floor.
  levelOf(y) { return clamp(Math.floor((y + .6) / this.H), 0, this.data.roof_level ?? this.data.storeys - 1); }

  roomAt(p) {
    if (!this.rooms?.length) return null;
    const sx = p.x, sy = -p.z;
    const floor = this.levelOf(p.y);
    for (const r of this.rooms) if (r.floor === floor && pointInPolygon(sx, sy, r.polygon) && !(r.holes || []).some(h => pointInPolygon(sx, sy, h))) return r;
    return null;
  }

  probePosition(room) {
    // Area centroid of the room polygon at standing eye height; fall back to the visitor if it lies outside.
    const poly = room.polygon;
    let a = 0, cx = 0, cy = 0;
    for (let i = 0; i < poly.length; i++) {
      const [x0, y0] = poly[i], [x1, y1] = poly[(i + 1) % poly.length];
      const k = x0 * y1 - x1 * y0;
      a += k; cx += (x0 + x1) * k; cy += (y0 + y1) * k;
    }
    let x = cx / (3 * a), y = cy / (3 * a);
    if (!Number.isFinite(x) || !pointInPolygon(x, y, poly)) { x = this.camera.position.x; y = -this.camera.position.z; }
    return new THREE.Vector3(x, room.floor * this.H + 1.45, -y);
  }

  // Indoors in walk mode, light each room with its own captured probe (cached per room and grade).
  updateProbe() {
    let target = null;
    if (this.mode === 'walk' && this.walker && (this.indoor || 0) >= .5 && !this.clay) {
      const room = this.roomAt(this.walker.position) || this.probeRoom;
      if (room && room.kind !== 'terrace') {
        this.probeRoom = room;
        const key = room.id + '|' + this.gradeName;
        target = this.probes.get(key);
        if (target) { this.probes.delete(key); this.probes.set(key, target); }
        else {
          // Glowing lamp shades are already represented by their point lights; keep them out of the capture
          // so a pendant hanging near the probe point cannot dominate the room's light.
          // Light the capture with the fittings around the room's middle, not wherever the visitor came from.
          const lamps = GRADES[this.gradeName].lamps, at = this.probePosition(room);
          this.materials.setLampLevel(lamps * .04, 0);
          this.updateLights(true, at);
          target = this.env.captureProbe(at);
          this.materials.setLampLevel(lamps);
          this.updateLights(true);
          this.probes.set(key, target);
          while (this.probes.size > 16) { const [k, t] = this.probes.entries().next().value; t.dispose(); this.probes.delete(k); }
        }
      }
    } else if ((this.indoor || 0) < .5) this.probeRoom = null;
    if (target !== this.env.probe) { this.env.useProbe(target); this.dirty = true; }
  }

  clearProbes() {
    this.env.useProbe(null);
    for (const t of this.probes.values()) t.dispose();
    this.probes.clear();
    this.probeRoom = null;
  }

  // ---------- visibility / cutaway ----------
  applyVisibility() {
    if (!this.data) return;
    const cut = this.mode === 'dollhouse' || this.mode === 'plan';
    const H = this.H;
    const f = this.floor;
    const overlooksBelow = this.mode === 'dollhouse' && (this.data.rooms || []).some(r => r.floor === f && r.kind === 'void');
    this.materials.clipPlane.constant = cut ? f * H + 1.22 : 1e6;
    for (const mesh of this.meshes) {
      const b = mesh.userData.bucket;
      let visible = true;
      if (cut) {
        if (b.floor > f) visible = false;
        else if (b.cls === 'overhead' || b.cls === 'opening') visible = false;
        else if (b.floor >= 0 && b.floor < f && !overlooksBelow && !(b.cls === 'clip' && b.roles.includes('wall')) && b.cls !== 'floor') visible = false;
      }
      if (cut && f === this.data.roof_level && b.floor === f - 1 && b.roles.includes('roof')) visible = true;
      mesh.visible = visible && (!mesh.userData.vehicle || this.carVisible);
    }
    this.vegetation?.setCutaway(cut, f, H);
    if (this.groundMesh) this.groundMesh.visible = true;
    this.dirty = true;
  }

  setClay(on = true) {
    this.clay = Boolean(on);
    this.clearProbes();
    for (const mesh of this.meshes) {
      const b = mesh.userData.bucket;
      mesh.material = this.clay ? (b.transparent ? mesh.userData.baseMaterial : b.cls === 'clip' ? this.materials.clayClip : this.materials.clay) : mesh.userData.baseMaterial;
    }
    if (this.vegetation) this.vegetation.group.visible = !this.clay;
    this.dirty = true;
    this.onStatus(this.clay ? 'Neutral clay · planting hidden' : 'Geometry screened · regulatory and structural approval remain open.');
  }

  // ---------- cameras ----------
  orbitTo(targetScene, theta, phi, distance) {
    // Placing the camera outright ends any glide still under way (its destination belongs to the previous view).
    this.zoomAnim = null;
    const t = s2t(targetScene);
    // Views are composed for landscape frames; step back on a portrait (phone) canvas so the house still fits.
    const aspect = this.canvas.clientWidth / Math.max(1, this.canvas.clientHeight);
    if (aspect > 0) distance *= clamp(1.35 / aspect, 1, 1.8);
    const eye = new THREE.Vector3(
      t.x + distance * Math.cos(phi) * Math.cos(theta),
      t.y + distance * Math.sin(phi),
      t.z - distance * Math.cos(phi) * Math.sin(theta),
    );
    this.controls.target.copy(t);
    this.camera.position.copy(eye);
    this.camera.up.set(0, 1, 0);
    this.controls.update();
    this.dirty = true;
  }

  reset() {
    if (!this.data) return;
    this.sideView = false;
    this.showContext(this.contextWanted());
    if (this.mode === 'walk') { this.spawn('arrival'); return; }
    const key = this.mode === 'dollhouse' || this.mode === 'plan' ? 'dollhouse' : 'hero';
    const c = this.data.cameras[key];
    const d = [c.position[0] - c.target[0], c.position[1] - c.target[1], c.position[2] - c.target[2]];
    const dist = Math.hypot(...d);
    // The hero is photographed from the sunlit side (see heroDirection); the plan looks straight down.
    let { theta, phi } = key === 'hero' ? this.heroDirection() : { theta: Math.atan2(d[1], d[0]), phi: Math.asin(d[2] / dist) };
    if (this.mode === 'plan') { phi = 1.52; theta = this.overheadTheta(); }
    // The dollhouse looks down a diagonal turned so the home's long side runs across the screen.
    else if (key === 'dollhouse') theta = this.acrossTheta(theta);
    this.camera.fov = this.mode === 'plan' ? 30 : c.fov || 43;
    this.camera.updateProjectionMatrix();
    this.controls.enabled = true;
    this.orbitTo(c.target, theta, phi, dist);
    // The stored camera sets the direction; the distance is fitted so the home itself, not the street, fills the view.
    this.fitHouse({ fill: this.focus ? FOCUS_FILL : key === 'hero' ? HERO_FILL : .9, animate: false });
  }

  setMode(mode) {
    if (!['solid', 'dollhouse', 'plan', 'walk', 'tour'].includes(mode)) return;
    const prev = this.mode;
    this._tour = mode === 'tour';
    this.mode = mode === 'tour' ? 'solid' : mode;
    if (prev === 'walk' && this.mode !== 'walk') this.leaveWalk();
    this.applyVisibility();
    if (this.mode === 'walk') { this.fitHeld = null; this.showContext(true); this.enterWalk(); }
    else {
      this.reset();
      this.onStatus({ solid: 'Exterior · physically based daylight', dollhouse: 'Dollhouse · roof lifted on the selected floor', plan: 'Plan · the selected floor from above' }[this.mode]);
    }
    this.applyGrade();
  }

  // The neighbourhood stands aside for the side elevations, whose cameras would otherwise look out from
  // inside the neighbours' houses, and in Focus, which shows the home alone.
  showContext(on) {
    if (this.context && this.context.visible !== on) { this.context.visible = on; this.dirty = true; }
  }

  contextWanted() { return this.mode === 'walk' || (!this.focus && !this.sideView); }

  // Focus: the home on its own (street and neighbours set aside), framed to fill the whole view from the current
  // direction; every view, mode and reset keeps that framing until Focus is switched off.
  setFocus(on = true) {
    if (!this.data) return;
    this.focus = Boolean(on);
    if (this.focus && this.mode === 'walk') { this.setMode('solid'); this.onModeChange?.('solid'); }
    this.showContext(this.contextWanted());
    if (this.focus && this.mode !== 'walk') { this._tour = false; this.controls.autoRotate = false; this.fitHouse({ fill: FOCUS_FILL }); }
    this.onStatus(this.focus ? 'Focus · the home alone, filling the view · drag to orbit, scroll or double-click to look closer' : 'Focus off · street and neighbours back in view');
  }

  get tour() { return this._tour; }
  set tour(on) { this._tour = Boolean(on); this.controls.autoRotate = this._tour; this.controls.autoRotateSpeed = .55; this.dirty = true; }

  setFloor(f) {
    if (!this.data) return;
    if (this.mode === 'walk') { this.onStatus('Use the staircase to change floor while walking.'); this.onFloorChange?.(this.floor); return; }
    this.floor = clamp(Number(f) || 0, 0, this.data.roof_level ?? this.data.storeys - 1);
    this.applyVisibility();
  }

  setView(name = 'hero') {
    if (!this.data) return;
    if (this.mode === 'walk') this.leaveWalk();
    this._tour = false; this.controls.autoRotate = false;
    this.mode = 'solid';
    this.applyVisibility();
    if (name === 'hero') { this.reset(); this.onStatus('Hero view · physically based daylight'); return; }
    this.sideView = name === 'left' || name === 'right';
    this.showContext(this.contextWanted());
    const fp = this.data.footprint, xs = fp.map((p) => p[0]), ys = fp.map((p) => p[1]);
    const W = Math.max(...xs) - Math.min(...xs), D = Math.max(...ys) - Math.min(...ys), H = this.H;
    // Aim at the middle of the elevation's height, so single-storey homes are framed as well as G+1.
    const top = H * this.data.storeys;
    const mid = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2, Math.min(top * .55 + .1, 4.2)];
    const side = W / 2 + Math.max(D * .8, (top + .9) * 1.8);
    const bal = this.balcony();
    const hero = this.heroDirection();
    // The elevations, the aerial and the top view are fitted to the home; the close-ups keep their set distance.
    const views = {
      front: { target: [mid[0], -.2, mid[2]], theta: -Math.PI / 2, phi: .2, distance: Math.max(W, D) * 1.05, fit: .88 },
      // Side elevations: far enough back to hold the whole flank and its full height in frame.
      left: { target: [mid[0], D * .42, top * .45], theta: Math.PI, phi: .15, distance: side, fit: .88 },
      right: { target: [mid[0], D * .42, top * .45], theta: 0, phi: .15, distance: side, fit: .88 },
      // High three-quarter view over the roof, its terraces and the garden.
      aerial: { target: [mid[0], mid[1], top * .4], theta: hero.theta, phi: .66, distance: 30, fit: .9 },
      // Straight down onto the roof, terraces and garden, the long side of the plot across the screen.
      // (a long lens, so the roof does not loom over the garden as it would through a wide one).
      top: { target: [mid[0], mid[1], top * .5], theta: this.overheadTheta(), phi: 1.52, distance: 30, fit: .95, site: true, fov: 24 },
      entrance: { target: [this.data.entry[0], -.65, 1.65], theta: -Math.PI / 2, phi: .12, distance: 7.2 },
      balcony: bal && { target: [bal.x, bal.y - .2, bal.z + 1.25], theta: -Math.PI / 2, phi: .3, distance: 6.8 },
    };
    const v = views[name] || views.front;
    this.camera.fov = v.fov || 43; this.camera.updateProjectionMatrix();
    this.orbitTo(v.target, v.theta, v.phi, v.distance);
    this.fitHeld = null;
    if (v.fit) this.fitHouse({ fill: this.focus ? FOCUS_FILL : v.fit, site: v.site, animate: false });
    this.onStatus(`${name === 'top' ? 'Top' : name[0].toUpperCase() + name.slice(1)} view · physically based daylight`);
  }

  // Direction of the hero photograph: the street-side three-quarter view, mirrored toward the sun.
  heroDirection() {
    const c = this.data.cameras.hero;
    const d = [c.position[0] - c.target[0], c.position[1] - c.target[1], c.position[2] - c.target[2]];
    const sun = this.data.solar?.vector_local;
    if (sun && Math.abs(sun[0]) > .2 && Math.sign(sun[0]) !== Math.sign(d[0])) d[0] = -d[0];
    return { theta: Math.atan2(d[1], d[0]), phi: Math.asin(d[2] / Math.hypot(...d)) };
  }

  // Azimuth for looking straight down: the plot's long side runs along the canvas's long side, with the street at
  // the bottom (or on the left when a deep plot is shown across a landscape screen), so the plan uses the width.
  overheadTheta() {
    const [x0, y0, , x1, y1] = this.data.bounds;
    const landscape = this.canvas.clientWidth >= this.canvas.clientHeight;
    return (y1 - y0 > x1 - x0) === landscape ? 0 : -Math.PI / 2;
  }

  // A three-quarter azimuth on the same side as `theta` (street side, left or right) that turns the plot's long
  // side 30 degrees off the screen's long side instead of 60, so the home spreads across the width.
  acrossTheta(theta) {
    const [x0, y0, , x1, y1] = this.data.bounds;
    const landscape = this.canvas.clientWidth >= this.canvas.clientHeight;
    const off = (y1 - y0 > x1 - x0) === landscape ? Math.PI / 3 : Math.PI / 6;
    return Math.cos(theta) >= 0 ? -Math.PI / 2 + off : -Math.PI / 2 - off;
  }

  // World box of the home as drawn: every storey on show with its porch, terraces and roof (not the garden, walls,
  // street or planting), or the whole plot with `site`. A dollhouse cut is framed at the height of its cut.
  houseBox({ site = false } = {}) {
    const box = new THREE.Box3(), b = new THREE.Box3();
    for (const m of this.meshes) {
      const k = m.userData.bucket;
      if (!m.visible || k.floor < 0) continue;
      if (!m.geometry.boundingBox) m.geometry.computeBoundingBox();
      box.union(b.copy(m.geometry.boundingBox));
    }
    if (box.isEmpty()) return null;
    if (site) { const [x0, y0, z0, x1, y1] = this.data.bounds; box.union(b.set(s2t([x0, y1, z0]), s2t([x1, y0, z0]))); }
    if (this.mode === 'dollhouse' || this.mode === 'plan') box.max.y = Math.min(box.max.y, this.floor * this.H + 1.3);
    return box;
  }

  // Frame the home: keep the camera's viewing direction and move the camera (along and across its line of sight)
  // to the closest spot from which the whole box fills `fill` of the frame, clear of the toolbars laid over the
  // canvas (`frameInsets`, CSS pixels). The exact solve lives in framing.js.
  fitHouse({ fill = .9, site = false, animate = true, hold = true } = {}) {
    if (!this.data || this.mode === 'walk') return false;
    const box = this.houseBox({ site });
    if (!box) return false;
    const cam = this.camera, w = Math.max(1, this.canvas.clientWidth), h = Math.max(1, this.canvas.clientHeight);
    if (Math.abs(cam.aspect - w / h) > 1e-3) { cam.aspect = w / h; cam.updateProjectionMatrix(); this.resized = true; }
    const from = this.zoomAnim ? { target: this.zoomAnim.toTarget, pos: this.zoomAnim.toPos } : { target: this.controls.target, pos: cam.position };
    const i = this.frameInsets || {}, px = (v, n) => 2 * clamp(v || 0, 0, n * .3) / n;
    const fit = frameBox(box.min.toArray(), box.max.toArray(), from.target.clone().sub(from.pos).toArray(), {
      fov: cam.fov, aspect: w / h, fill, up: cam.up.toArray(), minReach: this.controls.minDistance,
      window: [-1 + px(i.left, w), 1 - px(i.right, w), -1 + px(i.bottom, h), 1 - px(i.top, h)],
    });
    const pos = new THREE.Vector3(...fit.position), target = new THREE.Vector3(...fit.target);
    if (animate) {
      this.zoomAnim = { t0: performance.now(), fromTarget: this.controls.target.clone(), toTarget: target, fromPos: cam.position.clone(), toPos: pos };
    } else {
      this.zoomAnim = null;
      this.controls.target.copy(target);
      cam.position.copy(pos);
      cam.lookAt(target);
      this.controls.update();
    }
    this.fitHeld = hold ? { fill, site } : null;
    this.dirty = true;
    return true;
  }


  // The street-facing balcony (deck centre, front edge and deck level), or null on homes without one.
  balcony() {
    const slabs = (this.data?.nodes || []).filter((n) => n.role === 'balcony');
    if (!slabs.length) return null;
    const x = slabs.reduce((a, n) => a + n.position[0], 0) / slabs.length;
    const y = Math.min(...slabs.map((n) => n.position[1] - Math.abs(n.scale[1]) / 2));
    const z = Math.max(...slabs.map((n) => n.position[2] + Math.abs(n.scale[2]) / 2));
    return { x, y, z };
  }

  // ---------- walking ----------
  enterWalk() {
    this.controls.enabled = false;
    this.controls.autoRotate = false;
    this._tour = false;
    this.camera.fov = this.walkFov || 62;
    this.camera.updateProjectionMatrix();
    if (this.floor === this.data.roof_level) { this.floor = 0; this.onFloorChange?.(0); }
    this.spawn(this.floor > 0 ? 'floor' : 'arrival');
    this.hud.show(true);
    this.canvas.focus?.();
    this.onStatus('Walk · drag the view to look · cursor stays free · ↑/↓ forward/back · ←/→ turn · A/D sideways · Shift run · Space jump · C crouch · F open/close · Esc to pause');
  }

  leaveWalk() {
    this.indoor = 0; this._adaptDirty = true;
    this.env.useProbe(null);
    this.probeRoom = null;
    if (document.pointerLockElement === this.canvas) document.exitPointerLock?.();
    this.keys.clear();
    this.hud.show(false);
    this.controls.enabled = true;
  }

  spawn(which = 'arrival') {
    if (!this.walker) return;
    const w = this.data.walk || {};
    let spot = null;
    if (which === 'floor') spot = (w.floors || []).find((s) => s.floor === this.floor);
    if (!spot && which === 'arrival') spot = w.arrival;
    if (!spot) {
      const [x0, y0] = this.data.bounds;
      const ex = this.data.entry[0];
      spot = which === 'floor'
        ? { position: [this.data.cameras.interior.position[0], this.data.cameras.interior.position[1] + 1, this.floor * this.H], yaw_deg: 0 }
        : { position: [ex, y0 + 1.1, -.45], yaw_deg: 0 };
    }
    const p = s2t(spot.position);
    p.y += .5;
    const yaw = THREE.MathUtils.degToRad(spot.yaw_deg || 0);
    this.walker.teleport(p, yaw, 0);
    this.floor = this.levelOf(this.walker.position.y);
    this.dirty = true;
  }

  lock() {
    if (this.mode !== 'walk') return;
    // Walking keeps the system cursor free. Drag on the canvas to look around.
    if (document.pointerLockElement === this.canvas) document.exitPointerLock?.();
    this.canvas.focus?.();
    this.hud.setLocked(true);
  }

  bindInput() {
    const c = this.canvas;
    const on = (target, name, fn, opt) => { target.addEventListener(name, fn, opt); this.listeners.push(() => target.removeEventListener(name, fn, opt)); };
    let drag = null;
    on(c, 'pointerdown', (e) => {
      if (this.mode !== 'walk') return;
      c.focus?.();
      this.lock();
      drag = { x: e.clientX, y: e.clientY, id: e.pointerId, touch: e.pointerType !== 'mouse' };
      if (drag.touch) {
        const rect = c.getBoundingClientRect();
        if (e.clientX - rect.left < rect.width * .38 && e.clientY - rect.top > rect.height * .45) drag.stick = { x: e.clientX, y: e.clientY };
      }
      try { c.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    });
    on(c, 'pointermove', (e) => {
      if (this.mode !== 'walk' || !this.walker) return;
      if (document.pointerLockElement === c) {
        this.walker.yaw -= e.movementX * .0022;
        this.walker.pitch = clamp(this.walker.pitch - e.movementY * .0022, -1.45, 1.45);
        return;
      }
      if (!drag || drag.id !== e.pointerId) return;
      if (drag.stick) {
        const dx = (e.clientX - drag.stick.x) / 60, dy = (e.clientY - drag.stick.y) / 60;
        this.touchMove = { forward: clamp(-dy, -1, 1), strafe: clamp(dx, -1, 1) };
        return;
      }
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      drag.x = e.clientX; drag.y = e.clientY;
      this.walker.yaw -= dx * .0042;
      this.walker.pitch = clamp(this.walker.pitch - dy * .0036, -1.45, 1.45);
    });
    const end = (e) => { if (drag && drag.id === e.pointerId) { if (drag.stick) this.touchMove = null; drag = null; } };
    on(c, 'pointerup', end);
    on(c, 'pointercancel', end);
    on(c, 'dblclick', (e) => { if (this.zoomToPoint(e.clientX, e.clientY)) e.preventDefault(); });
    on(c, 'wheel', (e) => {
      this.zoomAnim = null;
      if (this.mode !== 'walk') return;
      e.preventDefault();
      this.walkFov = clamp((this.walkFov || 62) + e.deltaY * .02, 38, 85);
      this.camera.fov = this.walkFov; this.camera.updateProjectionMatrix();
    }, { passive: false });
    const editable = (t) => t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable);
    on(window, 'keydown', (e) => {
      if (this.mode !== 'walk' || editable(e.target)) return;
      const focused = document.activeElement === c || document.pointerLockElement === c;
      if (!focused) return;
      if (e.code === 'Escape') { this.keys.clear();this.touchMove=null;drag=null;c.blur();this.hud.setLocked(false);return; }
      if (WALK_KEYS.has(e.code)) { e.preventDefault(); this.keys.add(e.code); if (e.code === 'Space' && !e.repeat) this.input.jump = true; if (e.code === 'KeyF' && !e.repeat) this.interactOpening(); }
    });
    on(window, 'keyup', (e) => { this.keys.delete(e.code); });
    on(window, 'blur', () => this.keys.clear());
    on(c, 'blur', () => { this.keys.clear(); this.touchMove=null; drag=null; });
    on(document, 'pointerlockchange', () => { this.hud.setLocked(document.pointerLockElement === c); });
    on(document, 'visibilitychange', () => { this.lastTick = performance.now(); });
  }

  readInput() {
    const k = this.keys;
    const i = this.input;
    i.forward = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    i.strafe = (k.has('KeyD') ? 1 : 0) - (k.has('KeyA') ? 1 : 0);
    i.turn = (k.has('ArrowLeft') || k.has('KeyQ') ? 1 : 0) - (k.has('ArrowRight') || k.has('KeyE') ? 1 : 0);
    if (this.touchMove) { i.forward = this.touchMove.forward; i.strafe = this.touchMove.strafe; }
    i.run = k.has('ShiftLeft') || k.has('ShiftRight');
    i.crouch = k.has('KeyC') || k.has('ControlLeft');
    return i;
  }

  hudUpdate() {
    if (!this.walker || !this.hud.visible) return;
    const p = this.walker.position;
    const level = p.y;
    const floor = this.levelOf(level);
    const room = level < -.2 ? null : this.roomAt(p);
    let label = room ? room.name : null;
    if (!label) label = level > this.H * .5 ? 'Terrace' : this.isIndoors(p) ? 'Hall' : -p.z < this.data.bounds[1] ? 'Street' : 'Garden';
    this.hud.setLocation(label, floor === this.data.roof_level ? `Roof terrace · level ${floor}` : floor === 0 ? 'Ground floor' : floor === 1 ? 'First floor' : `Level ${floor}`);
  }

  // ---------- frame ----------
  tick() {
    const now = performance.now();
    const dt = Math.min(.05, Math.max(0, (now - this.lastTick) / 1000));
    this.lastTick = now;
    this.time += dt;
    if (!this.data || this.paused) return;
    if (this.resized) this.resize();
    this.openings?.update(dt);
    let render = this.dirty;
    if (this.mode === 'walk' && this.walker) {
      this.walker.update(dt, this.readInput());
      const eye = this.walker.eyePosition(new THREE.Vector3());
      this.camera.position.copy(eye);
      this.camera.rotation.set(this.walker.pitch, this.walker.yaw, this.walker.roll());
      const f = this.levelOf(this.walker.position.y);
      if (f !== this.floor) { this.floor = f; this.onFloorChange?.(f); }
      this.hudUpdate();
      this.openings?.updateTarget();
      this.adapt(dt);
      this.updateProbe();
      render = true;
    } else {
      if (this.zoomAnim) this.stepZoom(now);
      if (this.controls.enabled) this.controls.update(dt);
      if (this._tour || this.interacting || this.zoomAnim || performance.now() - (this.settle || 0) < 1200) render = true;
    }
    if (!render) return;
    this.vegetation?.update(this.time, this.camera);
    this.updateLights();
    const t0 = performance.now();
    this.composer.render(dt);
    this.frames++;
    this.dirty = false;
    this.trackPerformance(performance.now() - t0, dt);
  }

  trackPerformance(ms, dt) {
    if (!this.autoQuality) return;
    this.frameTimes.push(dt);
    if (this.frameTimes.length < 90) return;
    const avg = this.frameTimes.reduce((a, b) => a + b, 0) / this.frameTimes.length;
    this.frameTimes = [];
    if (avg > 1 / 24) {
      const next = ORDER[ORDER.indexOf(this.qualityName) + 1];
      if (next) this.setQuality(next);
      else this.autoQuality = false;
    } else if (this.frames > 400) this.autoQuality = false;
  }

  // ---------- capture ----------
  // ---------- zoom ----------
  // factor < 1 moves in, > 1 moves out: the orbit camera glides along its line of sight (optionally onto a
  // new focus point); in walk mode the lens narrows or widens instead.
  zoom(factor, focus = null) {
    if (!this.data) return;
    if (this.mode === 'walk') {
      this.walkFov = clamp((this.walkFov || 62) * factor, 30, 90);
      this.camera.fov = this.walkFov; this.camera.updateProjectionMatrix(); this.dirty = true;
      return;
    }
    this._tour = false; this.controls.autoRotate = false; this.fitHeld = null;
    // Repeated presses build on the glide already under way.
    const from = this.zoomAnim ? { target: this.zoomAnim.toTarget, pos: this.zoomAnim.toPos } : { target: this.controls.target, pos: this.camera.position };
    const target = focus ? focus.clone() : from.target.clone();
    const dir = from.pos.clone().sub(from.target);
    const distance = clamp(dir.length() * factor, this.controls.minDistance, this.controls.maxDistance);
    this.zoomAnim = { t0: performance.now(), fromTarget: this.controls.target.clone(), toTarget: target,
      fromPos: this.camera.position.clone(), toPos: target.clone().add(dir.normalize().multiplyScalar(distance)) };
    this.dirty = true;
  }

  stepZoom(now) {
    const a = this.zoomAnim, k = clamp((now - a.t0) / 420, 0, 1), e = 1 - Math.pow(1 - k, 3);
    this.controls.target.lerpVectors(a.fromTarget, a.toTarget, e);
    this.camera.position.lerpVectors(a.fromPos, a.toPos, e);
    if (k >= 1) { this.zoomAnim = null; this.settle = performance.now(); }
  }

  // Double-click (or double-tap) a spot on the house to glide in and orbit around it.
  zoomToPoint(clientX, clientY) {
    if (this.mode === 'walk' || !this.data) return false;
    const r = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((clientX - r.left) / r.width) * 2 - 1, -((clientY - r.top) / r.height) * 2 + 1);
    const ray = new THREE.Raycaster();
    ray.setFromCamera(ndc, this.camera);
    const hit = ray.intersectObjects(this.meshes.filter((m) => m.visible), false)[0];
    if (!hit) return false;
    this.zoom(.5, hit.point);
    return true;
  }

  // PNG of the current view. With a width larger than the canvas, the frame is re-rendered at that size (same
  // framing) for a large, print-ready still.
  async snapshot({ width = 0 } = {}) {
    if (this.resized) this.resize();
    const c = this.canvas, w0 = Math.max(1, c.clientWidth), h0 = Math.max(1, c.clientHeight);
    const max = Math.min(this.renderer.capabilities.maxTextureSize || 4096, 7680);
    const W = Math.min(Math.round(width), max), H = Math.round(W * h0 / w0);
    const large = W > c.width && H <= max;
    if (large) {
      this.renderer.setPixelRatio(1);
      this.renderer.setSize(W, H, false);
      this.composer.setSize(W, H, false);
    }
    this.vegetation?.update(this.time, this.camera);
    this.composer.render(0);
    const blob = await new Promise((resolve) => c.toBlob(resolve, 'image/png'));
    if (large) { this.resize(); this.dirty = true; }
    return blob;
  }

  async record(seconds = 12) {
    if (!this.canvas.captureStream || !window.MediaRecorder) throw Error('Video recording is unavailable in this browser.');
    const stream = this.canvas.captureStream(30);
    const type = MediaRecorder.isTypeSupported('video/webm;codecs=vp9') ? 'video/webm;codecs=vp9' : 'video/webm';
    const rec = new MediaRecorder(stream, { mimeType: type, videoBitsPerSecond: 12000000 });
    const chunks = [];
    const wasTour = this._tour;
    if (this.mode !== 'walk') this.tour = true;
    return new Promise((resolve, reject) => {
      rec.ondataavailable = (e) => chunks.push(e.data);
      rec.onerror = reject;
      rec.onstop = () => { this.tour = wasTour; stream.getTracks().forEach((t) => t.stop()); resolve(new Blob(chunks, { type: 'video/webm' })); };
      rec.start();
      setTimeout(() => rec.stop(), seconds * 1000);
    });
  }

  // Binary glTF of what the viewer draws (textures, planting, lawn, optional context) for offline renderers.
  exportPresentation(options) { return exportPresentation(this, options); }

  // Debug/automation hook used by the capture harness and tests.
  debugState() {
    const w = this.walker;
    return { mode: this.mode, floor: this.floor, quality: this.qualityName, grade: this.gradeName, frames: this.frames,
      walker: w ? { x: w.position.x, y: w.position.y, z: w.position.z, yaw: w.yaw, onGround: w.onGround, crouching: w.crouching } : null,
      camera: this.camera.position.toArray() };
  }

  destroy() {
    this.disposed = true;
    this.clearProbes();
    cancelAnimationFrame(this.raf);
    this.resizeObserver.disconnect();
    this.listeners.forEach((fn) => fn());
    this.clearScene();
    this.hud.dispose();
    this.controls.dispose();
    this.composer.dispose();
    this.env.dispose();
    this.synth.dispose();
    this.renderer.dispose();
  }
}

FloorForgeViewer.GRADES = GRADES;
window.FloorForgeViewer = FloorForgeViewer;
window.FloorForgeMath = { pointIn: (p, poly) => pointInPolygon(p[0], p[1], poly) };
export { FloorForgeViewer, visibilityClass };
