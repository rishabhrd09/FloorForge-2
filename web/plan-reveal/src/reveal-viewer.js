// The walkthrough viewer with a drawing state. It builds the house exactly as the realistic viewer does (same scene
// contract, materials, planting, light and grade) and adds: one cut plane shared by every material, the drawing
// buffers and the composite, a camera the page drives, and the room light probes and exposure of the walk.
import * as THREE from 'three';
import { EffectComposer, RenderPass, EffectPass, BloomEffect, SMAAEffect, SMAAPreset } from 'postprocessing';
import { N8AOPostPass } from 'n8ao';
import { FloorForgeViewer } from '../../viewer/src/index.js';
import { GradeEffect } from '../../viewer/src/grade.js';
import { GRADES } from '../../viewer/src/environment.js';
import { RevealEffect } from './composite.js';
import { DRAW_LAYER, gbufferMaterial } from './drawing.js';

const PLAN_SUN = new THREE.Vector3(-.45, 1.25, -.45).normalize();  // high, from the north-west of the sheet
const PLAN_SUN_COLOR = new THREE.Color('#fff1de');
const smoothstep = (t) => t * t * (3 - 2 * t);

export class RevealViewer extends FloorForgeViewer {
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
    this.reveal ||= new RevealEffect();
    const effects = this.bloom ? [this.bloom, this.gradeEffect, this.reveal] : [this.gradeEffect, this.reveal];
    this.composer.addPass(new EffectPass(this.camera, ...effects));
    if (this.q.smaa) this.composer.addPass(new EffectPass(this.camera, new SMAAEffect({ preset: SMAAPreset.HIGH })));
    this.resized = true;
  }

  // Interiors are metered a little darker and crisper than in the free walkthrough, with less bloom, so rooms keep
  // their depth beside the paper overlay instead of washing out.
  applyGrade() {
    super.applyGrade();
    const inside = this.indoor || 0, u = this.gradeEffect.uniforms;
    u.get('exposure').value *= 1 - .2 * inside;
    u.get('contrast').value += .07 * inside;
    if (this.bloom) this.bloom.intensity = (GRADES[this.gradeName].bloom ?? .3) * (1 - .45 * inside);
  }

  // The page has no orbit or walk input; the director places the camera.
  bindInput() { this.listeners ||= []; }

  setScene(data, building) {
    super.setScene(data, building);
    this.controls.enabled = false;
    this.hud.show(false);
    // One plane cuts everything that belongs to the site and the house (glass, roofs and shadows too). Planting is
    // not sliced: a plan shows a tree as its whole canopy, so plants stand whole up to the storey being cut and the
    // ones above it are set aside (see cut()).
    this.cutPlane = this.materials.clipPlane;
    const seen = new Set(), planting = new Set();
    this.vegetation?.group.traverse((o) => planting.add(o));
    this.root.traverse((o) => {
      if (!o.isMesh && !o.isInstancedMesh && !o.isLineSegments) return;
      if (o === this.groundMesh || planting.has(o)) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        if (!m || seen.has(m)) continue;
        seen.add(m);
        m.clippingPlanes = [this.cutPlane];
        m.clipShadows = true;
        m.needsUpdate = true;
      }
    });
    // The drawing pass sees the architecture (not planting, glass, the street context or the parked car).
    for (const mesh of this.meshes) if (!mesh.userData.bucket?.transparent && !mesh.userData.vehicle) mesh.layers.enable(DRAW_LAYER);
    this.groundMesh?.layers.enable(DRAW_LAYER);
    this.gbufMaterial = gbufferMaterial(this.cutPlane);
    this.drawCamera = new THREE.PerspectiveCamera();
    this.drawCamera.layers.set(DRAW_LAYER);
    this.walker?.teleport(new THREE.Vector3(this.center.x, -60, this.center.z), 0, 0);  // out of the way of moving doors
    this.cut(1e5);
  }

  // The closing colour plan is lit like an architectural plan render: the sun climbs to the north-west, so walls cast
  // short shadows down and to the right of the sheet, with more sky fill; the neighbours sink away so the plot reads
  // on its own.
  planLight(k) {
    if (Math.abs((this._plan ?? 0) - k) < 1e-3) return;
    this._plan = k;
    const g = GRADES[this.gradeName], env = this.env;
    const dir = env.sunDir.clone().lerp(PLAN_SUN, k).normalize();
    env.sun.position.copy(env.center).addScaledVector(dir, env.radius * 2 + 40);
    env.sun.color.set(g.sunColor).lerp(PLAN_SUN_COLOR, k);
    env.sun.intensity = g.sun * (1 - .3 * k);
    env.bounce.intensity = (g.bounce ?? .3) * (1 + 1.2 * k);
    this.gradeEffect.set('exposure', g.exposure * (1 + .12 * k));
    this.dirty = true;
  }

  // The neighbourhood sinks into the ground (k = 1) while the house is looked at as a plan from above.
  sinkContext(k) {
    if (!this.context || Math.abs((this._sunk ?? 0) - k) < 1e-3) return;
    this._sunk = k;
    this.context.position.y = -16 * smoothstep(k);
    this.context.visible = k < .999;
    this.dirty = true;
  }

  cut(y) {
    this.cutPlane.constant = y;
    this.cutY = y;
    const H = this.data?.floor_height || 3;
    const storey = y > 1e4 ? null : Math.max(0, Math.floor((y - .08) / H));
    if (storey !== this._plantStorey) {
      this._plantStorey = storey;
      this.vegetation?.setCutaway(storey !== null, storey ?? 0);
      this.dirty = true;
    }
  }

  resize() {
    super.resize();
    const w = this.renderer.domElement.width, h = this.renderer.domElement.height;
    if (!this.gbuf) {
      this.gbuf = new THREE.WebGLRenderTarget(w, h, { type: THREE.UnsignedByteType, depthTexture: new THREE.DepthTexture(w, h, THREE.FloatType), generateMipmaps: false });
      this.gbuf.texture.minFilter = this.gbuf.texture.magFilter = THREE.NearestFilter;
    } else this.gbuf.setSize(w, h);
    this.reveal.set('tGbuf', this.gbuf.texture);
    this.reveal.set('tDepth', this.gbuf.depthTexture);
    this.reveal.get('uTexel').set(1 / w, 1 / h);
    this.reveal.set('uLineWidth', Math.max(1, this.renderer.getPixelRatio() * .9));
    this.drawing?.setViewport(w, h, this.renderer.getPixelRatio(), this.camera.near);
  }

  renderDrawing() {
    const r = this.renderer, cam = this.drawCamera, main = this.camera;
    cam.position.copy(main.position); cam.quaternion.copy(main.quaternion);
    cam.fov = main.fov; cam.aspect = main.aspect; cam.near = main.near; cam.far = main.far; cam.zoom = main.zoom;
    cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const background = this.scene.background, fog = this.scene.fog;
    this.scene.background = null; this.scene.fog = null;
    this.scene.overrideMaterial = this.gbufMaterial;
    const clear = r.getClearColor(new THREE.Color()), alpha = r.getClearAlpha(), auto = r.autoClear;
    r.setRenderTarget(this.gbuf);
    r.setClearColor(new THREE.Color(.5, .5, 1), 1);
    r.clear(true, true, false);
    r.autoClear = false;
    r.render(this.scene, cam);
    this.scene.overrideMaterial = null;
    if (this.drawing) {
      this.drawing.setViewport(this.gbuf.width, this.gbuf.height, r.getPixelRatio(), cam.near);
      r.render(this.drawing.scene, cam);
    }
    r.autoClear = auto;
    r.setRenderTarget(null);
    r.setClearColor(clear, alpha);
    this.scene.background = background; this.scene.fog = fog;
    this.reveal.get('uProjInv').copy(cam.projectionMatrixInverse);
    this.reveal.get('uCamWorld').copy(cam.matrixWorld);
    this.reveal.set('uNear', cam.near); this.reveal.set('uFar', cam.far);
  }

  // Room probes and the eye's adaptation follow the camera (there is no walking body).
  updateProbe() {
    let target = null;
    if (this.mode === 'walk' && (this.indoor || 0) >= .5 && !this.clay) {
      const room = this.roomAt(this.camera.position) || this.probeRoom;
      if (room && room.kind !== 'terrace' && room.kind !== 'courtyard') {
        this.probeRoom = room;
        const key = room.id + '|' + this.gradeName;
        target = this.probes.get(key);
        if (!target) {
          const lamps = GRADES[this.gradeName].lamps, at = this.probePosition(room);
          const cut = this.cutPlane.constant;
          this.cutPlane.constant = 1e5;
          this.materials.setLampLevel(lamps * .04, 0);
          this.updateLights(true, at);
          target = this.env.captureProbe(at);
          this.materials.setLampLevel(lamps);
          this.updateLights(true);
          this.cutPlane.constant = cut;
          this.probes.set(key, target);
          while (this.probes.size > 16) { const [k, t] = this.probes.entries().next().value; t.dispose(); this.probes.delete(k); }
        }
      }
    } else if ((this.indoor || 0) < .5) this.probeRoom = null;
    if (target !== this.env.probe) this.env.useProbe(target);
  }

  tick() {
    const now = performance.now();
    const dt = Math.min(.05, Math.max(0, (now - this.lastTick) / 1000));
    this.lastTick = now;
    this.time += dt;
    if (!this.data || this.paused) return;
    if (this.resized) this.resize();
    const moving = this.onFrame ? this.onFrame(dt) : true;
    // Haze is for the street and the garden: from the long-lens heights it would fog the whole drawing away.
    if (this.scene.fog) {
      this.fogBase ??= this.scene.fog.density;
      const far = this.camera.position.distanceTo(this.center);
      this.scene.fog.density = this.fogBase * (1 - Math.min(1, Math.max(0, (far - 45) / 60)));
    }
    const doors = this.openings?.update(dt);
    if (this.mode === 'walk') { this.adapt(dt); this.updateProbe(); }
    if (!moving && !doors && !this.dirty && this.frames > 2 && (this.idleFrames = (this.idleFrames || 0) + 1) % 3) return;
    this.vegetation?.update(this.time, this.camera);
    this.updateLights();
    this.mask?.render();
    this.renderDrawing();
    this.composer.render(dt);
    this.frames++;
    this.dirty = false;
  }
}
