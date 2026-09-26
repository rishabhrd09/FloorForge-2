// Physical sky, sun, image-based lighting and lighting "grades" (day, golden hour, dusk, night, overcast).
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';

// Each daylight grade is authored against the analytic Preetham sky (whose radiance is pre-scaled by 0.04).
// Below the horizon the Preetham model breaks down, so blue hour and night use a measured-looking twilight
// gradient instead (deep blue zenith, warm afterglow toward the sun, pink anti-twilight band opposite).
// `punch` blends AgX's base look towards Blender's "Punchy" look; `probe` scales room light probes indoors.
export const GRADES = {
  day: {
    label: 'Daylight', elevation: null, turbidity: 2.4, rayleigh: 1.6, mie: .0032, mieG: .84, clouds: .32,
    sunColor: '#fff0d8', sun: 5.4, env: .12, exposure: .98, lamps: .06, fog: '#c3d3e4', fogDensity: .0016, indoor: 1.9,
    ground: '#6f7a5f', bloom: .2, bounce: .38, punch: .55, probe: 1.25,
  },
  golden: {
    label: 'Golden hour', elevation: 7.5, turbidity: 4.5, rayleigh: 2.2, mie: .005, mieG: .86, clouds: .28,
    sunColor: '#ffb574', sun: 3.2, env: .35, exposure: .95, lamps: .45, fog: '#dcc3a8', fogDensity: .0032, indoor: 1.6,
    ground: '#6d644d', bloom: .35, bounce: .32, bounceColor: '#e2b98e', punch: .4, probe: 1.2,
  },
  dusk: {
    label: 'Blue hour', elevation: -4, sunColor: '#8fa6d8', sun: .2, env: .95, exposure: 1.2, lamps: .75,
    fog: '#34405c', fogDensity: .004, indoor: .62, background: 1.0, ground: '#1d2229', bloom: .38, bounce: .06,
    bounceColor: '#8a7d6d', punch: .3, probe: .75,
    twilight: { zenith: '#0a1c4a', horizon: '#5a6f9c', glow: '#ff9148', glowStrength: .9, glowWidth: .075, belt: '#7d6c8e', ground: '#1c2027', level: 1 },
  },
  night: {
    label: 'Night', elevation: -18, sunColor: '#9fb4ff', sun: .05, env: .6, exposure: 1.6, lamps: .8,
    fog: '#0f141e', fogDensity: .005, indoor: .7, background: 1.0, ground: '#0b0d10', bloom: .48, moon: .15, bounce: .02,
    bounceColor: '#5a5046', punch: .25, probe: .75,
    twilight: { zenith: '#02050d', horizon: '#0d1320', glow: '#2a2118', glowStrength: .5, glowWidth: .08, belt: '#0d1320', ground: '#07080a', level: .55, halo: true },
  },
  overcast: {
    label: 'Overcast', elevation: null, turbidity: 9.5, rayleigh: .9, mie: .012, mieG: .6, clouds: .85,
    sunColor: '#eef0f2', sun: .7, env: .5, exposure: 1.0, lamps: .25, fog: '#b9c0c4', fogDensity: .0055, indoor: 1.8,
    ground: '#5b6250', bloom: .2, bounce: .55, punch: .2, probe: 1.25,
  },
};

const TWILIGHT_VERT = /* glsl */`
varying vec3 vWorld;
void main() {
  vec4 w = modelMatrix * vec4(position, 1.0);
  vWorld = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
  gl_Position.z = gl_Position.w;
}`;

const TWILIGHT_FRAG = /* glsl */`
uniform vec3 sunDir;
uniform vec3 zenith;
uniform vec3 horizon;
uniform vec3 glow;
uniform vec3 belt;
uniform vec3 ground;
uniform float glowWidth;
uniform float halo;
varying vec3 vWorld;
void main() {
  vec3 d = normalize(vWorld - cameraPosition);
  float h = d.y;
  float up = max(h, 0.0);
  vec2 sa = normalize(sunDir.xz + vec2(1e-5));
  vec2 da = normalize(d.xz + vec2(1e-5));
  float toward = dot(sa, da);
  // Sky dome: zenith to horizon, horizon band slightly thicker away from the sun.
  vec3 col = mix(zenith, horizon, pow(1.0 - up, 3.2));
  // Afterglow: warm, low and concentrated toward the sun's azimuth; broader and paler higher up.
  float az = pow(max(toward * .5 + .5, 0.0), 4.0);
  col += glow * az * exp(-up / glowWidth);
  col += glow * .18 * az * exp(-up / (glowWidth * 3.5));
  // Anti-twilight arch (Belt of Venus) opposite the sun, just above the horizon.
  float anti = pow(max(-toward * .5 + .5, 0.0), 3.0) * exp(-abs(up - .07) / .06);
  col += belt * anti * .6;
  // Settlement glow on every horizon at night.
  col += glow * halo * .35 * exp(-up / .05);
  if (h < 0.0) col = mix(horizon * .55, ground, smoothstep(0.0, .06, -h));
  gl_FragColor = vec4(col, 1.0);
}`;

function twilightSky() {
  const material = new THREE.ShaderMaterial({
    name: 'TwilightSky', side: THREE.BackSide, depthWrite: false,
    uniforms: {
      sunDir: { value: new THREE.Vector3(0, -.05, 1) }, zenith: { value: new THREE.Color() }, horizon: { value: new THREE.Color() },
      glow: { value: new THREE.Color() }, belt: { value: new THREE.Color() }, ground: { value: new THREE.Color() },
      glowWidth: { value: .1 }, halo: { value: 0 },
    },
    vertexShader: TWILIGHT_VERT, fragmentShader: TWILIGHT_FRAG,
  });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), material);
  mesh.scale.setScalar(900);
  return mesh;
}

export class Environment {
  constructor(renderer, scene, { quality = 'high' } = {}) {
    this.renderer = renderer;
    this.scene = scene;
    this.pmrem = new THREE.PMREMGenerator(renderer);
    this.sky = new Sky();
    this.sky.scale.setScalar(900);
    this.twilight = twilightSky();
    this.skyScene = new THREE.Scene();
    this.skyScene.add(this.sky);
    this.envGround = new THREE.Mesh(new THREE.CircleGeometry(800, 48), new THREE.MeshBasicMaterial({ color: '#555', side: THREE.DoubleSide }));
    this.envGround.rotation.x = -Math.PI / 2;
    this.envGround.position.y = -2;
    this.cubeSize = quality === 'performance' ? 256 : 512;
    this.cubeTarget = new THREE.WebGLCubeRenderTarget(this.cubeSize, { type: THREE.HalfFloatType, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter });
    this.cubeCamera = new THREE.CubeCamera(.5, 2000, this.cubeTarget);
    this.envTarget = null;
    this.sun = new THREE.DirectionalLight('#ffffff', 3);
    this.sun.castShadow = true;
    this.sun.shadow.bias = -0.00015;
    this.sun.shadow.normalBias = .025;
    this.sun.shadow.radius = 3;
    this.sunTarget = new THREE.Object3D();
    this.sun.target = this.sunTarget;
    scene.add(this.sun, this.sunTarget);
    this.moon = new THREE.DirectionalLight('#9fb4ff', 0);
    scene.add(this.moon);
    // Stand-in for one-bounce light from floors and paving onto ceilings, soffits and undersides.
    this.bounce = new THREE.HemisphereLight('#dfe6ee', '#d9c7aa', .3);
    scene.add(this.bounce);
    this.fog = new THREE.FogExp2('#c9d6e0', .003);
    scene.fog = this.fog;
    this.sunDir = new THREE.Vector3(0.4, .7, .5).normalize();
    this.solarDir = this.sunDir.clone();
    this.center = new THREE.Vector3();
    this.radius = 30;
    this.gradeName = 'day';
    this.grade = GRADES.day;
    this.setShadowQuality(quality);
  }

  setShadowQuality(quality) {
    const size = quality === 'ultra' ? 4096 : quality === 'high' ? 4096 : quality === 'balanced' ? 2048 : 1024;
    if (this.sun.shadow.mapSize.x !== size) {
      this.sun.shadow.mapSize.set(size, size);
      this.sun.shadow.map?.dispose();
      this.sun.shadow.map = null;
    }
  }

  // Solar vector is in the scene's Z-up plan frame; convert to Three's Y-up world.
  setSite(solarVectorLocal, center, radius) {
    const [x, y, z] = solarVectorLocal;
    this.solarDir.set(x, z, -y).normalize();
    this.center.copy(center);
    this.radius = radius;
    const cam = this.sun.shadow.camera;
    cam.left = -radius; cam.right = radius; cam.top = radius; cam.bottom = -radius;
    cam.near = 1; cam.far = radius * 4 + 80;
    cam.updateProjectionMatrix();
  }

  sunDirectionFor(grade) {
    if (grade.elevation === null || grade.elevation === undefined) {
      const d = this.solarDir.clone();
      if (d.y < .2) { d.y = .2; d.normalize(); }
      return d;
    }
    const az = Math.atan2(this.solarDir.x, this.solarDir.z);
    const el = THREE.MathUtils.degToRad(grade.elevation);
    return new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el)).normalize();
  }

  setGrade(name) {
    const grade = GRADES[name] || GRADES.day;
    this.gradeName = GRADES[name] ? name : 'day';
    this.grade = grade;
    const dir = this.sunDirectionFor(grade);
    this.sunDir.copy(dir);
    const u = this.sky.material.uniforms;
    if (grade.twilight) {
      const t = grade.twilight, tu = this.twilight.material.uniforms, k = t.level ?? 1;
      tu.sunDir.value.copy(dir);
      tu.zenith.value.set(t.zenith).multiplyScalar(k);
      tu.horizon.value.set(t.horizon).multiplyScalar(k);
      tu.glow.value.set(t.glow).multiplyScalar(k * (t.glowStrength ?? 1));
      tu.belt.value.set(t.belt).multiplyScalar(k);
      tu.ground.value.set(t.ground).multiplyScalar(k);
      tu.glowWidth.value = t.glowWidth ?? .1;
      tu.halo.value = t.halo ? 1 : 0;
      this.skyScene.remove(this.sky);
      this.skyScene.add(this.twilight);
    } else {
      u.turbidity.value = grade.turbidity;
      u.rayleigh.value = grade.rayleigh;
      u.mieCoefficient.value = grade.mie;
      u.mieDirectionalG.value = grade.mieG;
      u.sunPosition.value.copy(dir);
      if (u.cloudCoverage) { u.cloudCoverage.value = grade.clouds; u.cloudDensity.value = this.gradeName === 'overcast' ? .8 : .45; u.cloudScale.value = .00018; u.cloudElevation.value = .55; }
      this.skyScene.remove(this.twilight);
      this.skyScene.add(this.sky);
    }
    // Directional sun (or a faint twilight fill when the sun is below the horizon).
    const lightDir = dir.y > .05 ? dir : new THREE.Vector3(dir.x, .35, dir.z).normalize();
    this.sun.color.set(grade.sunColor);
    this.sun.intensity = grade.sun;
    this.sun.position.copy(this.center).addScaledVector(lightDir, this.radius * 2 + 40);
    this.sunTarget.position.copy(this.center);
    this.sun.castShadow = grade.sun > .3;
    this.moon.intensity = grade.moon || 0;
    this.bounce.intensity = grade.bounce ?? .3;
    this.bounce.groundColor.set(grade.bounceColor || '#d9c7aa');
    this.moon.position.set(this.center.x - 30, this.center.y + 60, this.center.z + 20);
    this.moon.target = this.sunTarget;
    this.fog.color.set(grade.fog);
    this.fog.density = grade.fogDensity;
    this.envGround.material.color.set(grade.ground).multiplyScalar(grade.sun > 1 ? .45 : .08);
    this.renderSky();
    return grade;
  }

  renderSky() {
    const r = this.renderer;
    const u = this.sky.material.uniforms;
    // Background: full sky with sun disc. Environment: sky without the disc plus a darker ground hemisphere.
    u.showSunDisc.value = 1;
    this.skyScene.remove(this.envGround);
    this.cubeCamera.update(r, this.skyScene);
    this.scene.background = this.cubeTarget.texture;
    u.showSunDisc.value = 0;
    this.skyScene.add(this.envGround);
    const next = this.pmrem.fromScene(this.skyScene, 0, .5, 2000);
    this.skyScene.remove(this.envGround);
    u.showSunDisc.value = 1;
    this.envTarget?.dispose();
    this.envTarget = next;
    this.scene.environment = next.texture;
    this.scene.environmentIntensity = this.grade.env;
    this.scene.backgroundIntensity = this.grade.background ?? 1;
    this.probe = null;
  }

  // Local light probe for a room: a cube capture of the surroundings of `position`, lit by the current sun,
  // sky (through the windows) and lamps, prefiltered exactly like the sky environment so materials can
  // switch between them without recompiling. Indoors this replaces open-sky lighting with the room's own
  // warm bounce light, and glossy floors reflect walls and windows instead of the sky.
  captureProbe(position) {
    const r = this.renderer, scene = this.scene;
    if (!this.probeTarget) {
      this.probeTarget = new THREE.WebGLCubeRenderTarget(256, { type: THREE.HalfFloatType, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter });
      this.probeCamera = new THREE.CubeCamera(.05, 600, this.probeTarget);
    }
    const saved = [scene.environment, scene.environmentIntensity, scene.background, scene.backgroundIntensity, r.shadowMap.autoUpdate, this.bounce.intensity];
    scene.environment = this.envTarget.texture;
    scene.environmentIntensity = this.grade.env;
    // The sky seen through windows, without the sun disc, at the radiance it lights the scene with.
    scene.background = this.envTarget.texture;
    scene.backgroundIntensity = this.grade.env;
    this.bounce.intensity = (this.grade.bounce ?? .3) * .6;
    r.shadowMap.autoUpdate = false;
    r.shadowMap.needsUpdate = true;
    this.probeCamera.position.copy(position);
    // Pass 1: the room lit by sun, lamps and a sky term reduced for the ceiling and walls that occlude it.
    scene.environmentIntensity = this.grade.env * .35;
    this.probeCamera.update(r, scene);
    const first = this.pmrem.fromCubemap(this.probeTarget.texture);
    // Pass 2: the room re-lit by its own first bounce (windows included), a one-probe radiosity step.
    scene.environment = first.texture;
    scene.environmentIntensity = 1;
    this.probeCamera.update(r, scene);
    first.dispose();
    [scene.environment, scene.environmentIntensity, scene.background, scene.backgroundIntensity, r.shadowMap.autoUpdate, this.bounce.intensity] = saved;
    const target = this.pmrem.fromCubemap(this.probeTarget.texture);
    target.stats = null;
    target.statsReady = this.probeStats().then((stats) => { target.stats = stats; return stats; });
    return target;
  }

  // Solid-angle-weighted mean radiance of the last probe capture: drives per-room auto exposure and white
  // balance, the way a camera meters a room. A 16x8 lat-long reduction of a coarse mip is read back
  // asynchronously, so entering a room never stalls the frame on a GPU readback.
  probeStats() {
    const r = this.renderer;
    if (this.statsSupported === undefined) this.statsSupported = r.extensions.has('EXT_color_buffer_float');
    if (!this.statsSupported) return Promise.resolve(null);
    if (!this.statsMaterial) {
      this.statsMaterial = new THREE.ShaderMaterial({
        uniforms: { cube: { value: null } }, depthTest: false, depthWrite: false,
        vertexShader: 'void main() { gl_Position = vec4(position.xy, 0.0, 1.0); }',
        fragmentShader: `uniform samplerCube cube;
void main() {
  vec2 uv = gl_FragCoord.xy / vec2(16.0, 8.0);
  float phi = uv.x * 6.2831853, th = uv.y * 3.1415927;
  vec3 d = vec3(sin(th) * cos(phi), cos(th), sin(th) * sin(phi));
  gl_FragColor = vec4(textureLod(cube, d, 4.0).rgb, 1.0);
}`,
      });
      this.statsScene = new THREE.Scene();
      this.statsScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.statsMaterial));
      this.statsCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    }
    const target = new THREE.WebGLRenderTarget(16, 8, { type: THREE.FloatType, depthBuffer: false, generateMipmaps: false });
    this.statsMaterial.uniforms.cube.value = this.probeTarget.texture;
    const previous = r.getRenderTarget();
    r.setRenderTarget(target);
    r.render(this.statsScene, this.statsCamera);
    r.setRenderTarget(previous);
    const b = new Float32Array(16 * 8 * 4);
    return r.readRenderTargetPixelsAsync(target, 0, 0, 16, 8, b).then(() => {
      target.dispose();
      let w = 0, R = 0, G = 0, B = 0;
      for (let y = 0; y < 8; y++) {
        const k = Math.sin((y + .5) / 8 * Math.PI);
        for (let x = 0; x < 16; x++) { const i = (y * 16 + x) * 4; R += b[i] * k; G += b[i + 1] * k; B += b[i + 2] * k; w += k; }
      }
      R /= w; G /= w; B /= w;
      const luminance = .2126 * R + .7152 * G + .0722 * B;
      return Number.isFinite(luminance) && luminance > 0 ? { r: R, g: G, b: B, luminance } : null;
    }).catch(() => { target.dispose(); this.statsSupported = false; return null; });
  }

  useProbe(target) {
    const texture = target ? target.texture : this.envTarget?.texture;
    if (!texture) return;
    if (this.scene.environment !== texture) this.scene.environment = texture;
    this.scene.environmentIntensity = target ? (this.grade.probe ?? 1) : this.grade.env;
    this.bounce.intensity = (this.grade.bounce ?? .3) * (target ? .3 : 1);
    this.probe = target || null;
  }

  dispose() {
    this.envTarget?.dispose();
    this.probeTarget?.dispose();
    this.statsMaterial?.dispose();
    this.twilight.geometry.dispose();
    this.twilight.material.dispose();
    this.cubeTarget.dispose();
    this.pmrem.dispose();
    this.sky.geometry.dispose();
    this.sky.material.dispose();
    this.envGround.geometry.dispose();
    this.envGround.material.dispose();
    this.sun.shadow.map?.dispose();
  }
}
