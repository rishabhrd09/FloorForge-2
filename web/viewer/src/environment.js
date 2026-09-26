// Physical sky, sun, image-based lighting and lighting "grades" (day, golden hour, dusk, night, overcast).
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';

// Each grade is authored against the analytic Preetham sky (whose radiance is pre-scaled by 0.04).
export const GRADES = {
  day: {
    label: 'Daylight', elevation: null, turbidity: 2.0, rayleigh: 2.7, mie: .0028, mieG: .8, clouds: .3,
    sunColor: '#fff4e6', sun: 4.0, env: .17, exposure: 1.0, lamps: .06, fog: '#bccfe3', fogDensity: .0022, indoor: 1.55,
    ground: '#6f7a5f', bloom: .22, bounce: .42,
  },
  golden: {
    label: 'Golden hour', elevation: 7.5, turbidity: 4.5, rayleigh: 2.2, mie: .005, mieG: .86, clouds: .28,
    sunColor: '#ffb574', sun: 3.2, env: .35, exposure: .95, lamps: .45, fog: '#dcc3a8', fogDensity: .0032, indoor: 1.4,
    ground: '#6d644d', bloom: .35, bounce: .32, bounceColor: '#e2b98e',
  },
  dusk: {
    label: 'Blue hour', elevation: -.6, turbidity: 3.2, rayleigh: 3.2, mie: .005, mieG: .8, clouds: .22,
    sunColor: '#ffa36b', sun: .18, env: 1.3, exposure: 1.5, lamps: .75, fog: '#46506a', fogDensity: .0045, indoor: 1.0, background: 1.6,
    ground: '#262b31', bloom: .55, bounce: .05, bounceColor: '#8a7d6d',
  },
  night: {
    label: 'Night', elevation: -1.6, turbidity: 2, rayleigh: 1.2, mie: .003, mieG: .7, clouds: .15,
    sunColor: '#9fb4ff', sun: .05, env: .9, exposure: 1.45, lamps: .8, fog: '#141a26', fogDensity: .005, indoor: 1.0, background: .45,
    ground: '#0b0d10', bloom: .7, moon: .28, bounce: .02, bounceColor: '#5a5046',
  },
  overcast: {
    label: 'Overcast', elevation: null, turbidity: 9.5, rayleigh: .9, mie: .012, mieG: .6, clouds: .85,
    sunColor: '#eef0f2', sun: .7, env: .5, exposure: 1.0, lamps: .25, fog: '#b9c0c4', fogDensity: .0055, indoor: 1.5,
    ground: '#5b6250', bloom: .2, bounce: .55,
  },
};

export class Environment {
  constructor(renderer, scene, { quality = 'high' } = {}) {
    this.renderer = renderer;
    this.scene = scene;
    this.pmrem = new THREE.PMREMGenerator(renderer);
    this.sky = new Sky();
    this.sky.scale.setScalar(900);
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
    u.turbidity.value = grade.turbidity;
    u.rayleigh.value = grade.rayleigh;
    u.mieCoefficient.value = grade.mie;
    u.mieDirectionalG.value = grade.mieG;
    u.sunPosition.value.copy(dir);
    if (u.cloudCoverage) { u.cloudCoverage.value = grade.clouds; u.cloudDensity.value = this.gradeName === 'overcast' ? .8 : .45; u.cloudScale.value = .00018; u.cloudElevation.value = .55; }
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
  }

  dispose() {
    this.envTarget?.dispose();
    this.cubeTarget.dispose();
    this.pmrem.dispose();
    this.sky.geometry.dispose();
    this.sky.material.dispose();
    this.envGround.geometry.dispose();
    this.envGround.material.dispose();
    this.sun.shadow.map?.dispose();
  }
}
