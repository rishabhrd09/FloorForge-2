// Procedural planting for the realistic viewer: instanced species variants, hedges, lawn grass and wind.
import * as THREE from 'three';
import { buildSpecies } from './plant-builders.js';
import { FoliageTextures } from './foliage-textures.js';
import { buildLawn } from './grass.js';
import { hashString, mulberry32 } from './util.js';

const VARIANTS = 3;

// Shared foliage shader patch: wind sway, no back-face normal flip (bent card normals), soft translucency.
export function patchFoliage(material, uniforms, { translucency = .45, instancedWind = true } = {}) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
attribute float aSway;
uniform float ffTime;
uniform float ffWind;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
{
  #ifdef USE_INSTANCING
    vec3 ffBase = (modelMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
  #else
    vec3 ffBase = (modelMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
  #endif
  float ph = ffTime * 1.15 + ffBase.x * .37 + ffBase.z * .29;
  float gust = .65 + .35 * sin(ffTime * .37 + ffBase.x * .05);
  float s = aSway * ffWind * gust;
  transformed.x += (sin(ph) * .045 + sin(ffTime * 5.3 + position.y * 4.1 + position.x * 3.7) * .012) * s;
  transformed.z += (cos(ph * .83) * .035 + cos(ffTime * 4.7 + position.z * 3.9) * .01) * s;
  transformed.y += sin(ffTime * 6.1 + position.x * 5.0 + position.z * 4.0) * .006 * s;
}`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
uniform vec3 ffSunDir;
uniform vec3 ffSunColor;`)
      .replace('#include <normal_fragment_begin>', THREE.ShaderChunk.normal_fragment_begin.replace('normal *= faceDirection;', ''))
      .replace('#include <opaque_fragment>', `{
  vec3 sunV = normalize((viewMatrix * vec4(ffSunDir, 0.0)).xyz);
  float back = pow(max(dot(normalize(-vViewPosition), sunV), 0.0), 3.0);
  outgoingLight += diffuseColor.rgb * ffSunColor * back * ${translucency.toFixed(3)};
}
#include <opaque_fragment>`);
  };
  material.customProgramCacheKey = () => 'ff-foliage-' + translucency;
}

export class Vegetation {
  constructor(viewer, data, { density = 1 } = {}) {
    this.viewer = viewer;
    this.group = new THREE.Group();
    this.group.name = 'vegetation';
    this.count = 0;
    this.meshes = [];
    this.geometries = [];
    this.uniforms = {
      ffTime: { value: 0 }, ffWind: { value: 1 },
      ffSunDir: { value: new THREE.Vector3(.4, .7, .5) }, ffSunColor: { value: new THREE.Color('#fff2d8') },
    };
    const list = data.vegetation || [];
    const lawns = data.lawns || [];
    const renderer = viewer.renderer;
    this.tex = new FoliageTextures(renderer, viewer.q.textures);
    this.materials = this.makeMaterials(viewer);
    this.instances = [];
    // Group plant instances by species (+ options) and variant.
    const groups = new Map();
    for (const item of list) {
      const species = item.species || 'shrub_round';
      if (species === 'hedge') { this.addHedge(item); continue; }
      const seed = (item.seed ?? hashString(item.id || species)) >>> 0;
      const variant = seed % VARIANTS;
      const optsKey = JSON.stringify(item.options || {});
      const key = species + '|' + variant + '|' + optsKey;
      if (!groups.has(key)) groups.set(key, { species, variant, opts: item.options || {}, items: [] });
      groups.get(key).items.push(item);
    }
    for (const g of groups.values()) this.addInstanced(g);
    // Lawn grass blades.
    if (lawns.length && density > 0) {
      const lawn = buildLawn(lawns, density, this.uniforms, data.materials?.grass?.color);
      if (lawn) { this.group.add(lawn); this.meshes.push(lawn); this.lawn = lawn; }
    }
  }

  makeMaterials(viewer) {
    const u = this.uniforms;
    const leaf = (map, opts = {}) => {
      const m = new THREE.MeshStandardMaterial({ map, alphaTest: .42, side: THREE.DoubleSide, roughness: opts.roughness ?? .62, metalness: 0, color: opts.color || '#ffffff', envMapIntensity: .7 });
      patchFoliage(m, u, { translucency: opts.translucency ?? .45 });
      return m;
    };
    const bark = viewer.synth.make('bark', { base: '#5e5a4f', alt: '#7d8470', params: [.8, 0, 0, 0] });
    const smoothBark = viewer.synth.make('bark', { base: '#6f7064', alt: '#7f8a72', params: [.12, 0, 0, 0], seed: 3 });
    const palmBark = viewer.synth.make('bark', { base: '#8f8676', alt: '#8c8a78', params: [.25, 14, 0, 0] });
    const greenStem = viewer.synth.make('bark', { base: '#5f7440', alt: '#6f8a48', params: [.05, 0, 0, 0] });
    const barkMat = (t) => { const m = new THREE.MeshStandardMaterial({ map: t.map, normalMap: t.normalMap, roughnessMap: t.roughnessMap }); patchFoliage(m, u, { translucency: 0 }); return m; };
    const mass = new THREE.MeshStandardMaterial({ color: '#233518', roughness: .95 });
    patchFoliage(mass, u, { translucency: .05 });
    const solid = new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: .7 });
    patchFoliage(solid, u, { translucency: .35 });
    const set = {
      cluster: leaf(this.tex.cluster, { color: '#e6f0dc' }),
      clusterLight: leaf(this.tex.clusterLight, { color: '#f4f7ea' }),
      leaves: leaf(this.tex.leaves, { roughness: .45, translucency: .5 }),
      fronds: leaf(this.tex.fronds, { translucency: .55 }),
      flowers: leaf(this.tex.flowers, { roughness: .7, translucency: .6 }),
      solid,
      bark: barkMat(bark), smoothBark: barkMat(smoothBark), palmBark: barkMat(palmBark), greenStem: barkMat(greenStem), mass,
    };
    // Names travel into the presentation export, where offline renderers recognise foliage and bark.
    for (const [key, m] of Object.entries(set)) m.name = (/bark|stem/i.test(key) ? 'plant-bark-' : 'plant-foliage-') + key;
    return set;
  }

  partMaterial(part, spec) {
    if (part === 'wood') return spec.bark === 'palm' ? this.materials.palmBark : spec.bark === 'smooth' ? this.materials.smoothBark : spec.woodColor ? this.materials.greenStem : this.materials.bark;
    if (part === 'mass') return this.materials.mass;
    if (part === 'flowers') return this.materials.flowers;
    return this.materials[spec.leafAtlas] || this.materials.cluster;
  }

  matrixFor(item) {
    const p = item.position || [0, 0, 0];
    const s = item.scale ?? 1;
    const rnd = mulberry32((item.seed ?? hashString(item.id || 'x')) ^ 0x9e3779b9);
    const sy = s * (.92 + rnd() * .16);
    const m = new THREE.Matrix4();
    m.compose(new THREE.Vector3(p[0], p[2], -p[1]), new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), item.rotation ?? rnd() * Math.PI * 2), new THREE.Vector3(s, sy, s));
    return m;
  }

  addInstanced(g) {
    const seed = hashString(g.species + ':' + g.variant + ':' + JSON.stringify(g.opts));
    const spec = buildSpecies(g.species, seed, g.opts);
    const matrices = g.items.map((it) => this.matrixFor(it));
    for (const [part, geo] of Object.entries(spec.parts)) {
      if (!geo) continue;
      this.geometries.push(geo);
      const mesh = new THREE.InstancedMesh(geo, this.partMaterial(part, spec), g.items.length);
      matrices.forEach((m, i) => mesh.setMatrixAt(i, m));
      mesh.instanceMatrix.needsUpdate = true;
      mesh.castShadow = part !== 'flowers';
      mesh.receiveShadow = true;
      mesh.computeBoundingSphere();
      mesh.userData.items = g.items;
      mesh.userData.matrices = matrices;
      this.group.add(mesh);
      this.meshes.push(mesh);
    }
    this.count += g.items.length;
  }

  addHedge(item) {
    const spec = buildSpecies('hedge', (item.seed ?? hashString(item.id || 'hedge')) >>> 0, { size: item.size || [2, .5, 1] });
    const m = this.matrixFor({ ...item, scale: 1, rotation: item.rotation ?? 0 });
    for (const [part, geo] of Object.entries(spec.parts)) {
      if (!geo) continue;
      this.geometries.push(geo);
      const mesh = new THREE.Mesh(geo, this.partMaterial(part, spec));
      mesh.applyMatrix4(m);
      mesh.castShadow = true; mesh.receiveShadow = true;
      mesh.userData.items = [item];
      this.group.add(mesh);
      this.meshes.push(mesh);
    }
    this.count += 1;
  }

  setDensity(d) { if (this.lawn) this.lawn.userData.setDensity?.(d); }

  // Dollhouse/plan: hide indoor plants above the viewed floor.
  setCutaway(cut, floor) {
    const zero = new THREE.Matrix4().makeScale(0, 0, 0);
    for (const mesh of this.meshes) {
      const items = mesh.userData.items;
      if (!items) continue;
      if (mesh.isInstancedMesh) {
        items.forEach((it, i) => mesh.setMatrixAt(i, cut && (it.floor ?? -1) > floor ? zero : mesh.userData.matrices[i]));
        mesh.instanceMatrix.needsUpdate = true;
      } else mesh.visible = !(cut && (items[0].floor ?? -1) > floor);
    }
  }

  update(time, camera) {
    this.uniforms.ffTime.value = time;
    const env = this.viewer.env;
    if (env) {
      this.uniforms.ffSunDir.value.copy(env.sunDir);
      this.uniforms.ffSunColor.value.copy(env.sun.color).multiplyScalar(Math.min(1.5, env.sun.intensity / 3));
    }
    if (this.lawn) this.lawn.userData.update?.(camera);
  }

  dispose() {
    for (const g of this.geometries) g.dispose();
    if (this.lawn) this.lawn.geometry.dispose();
    if (this.materials) for (const m of Object.values(this.materials)) m.dispose();
    this.tex?.dispose();
    this.group.clear();
  }
}
