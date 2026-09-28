// Maps FloorForge scene material descriptors to physically based Three.js materials.
import * as THREE from 'three';
import { KIND_DEFAULTS } from './textures.js';

// Legacy (floorforge.scene/0.3) texture names and material names mapped onto the newer surface kinds.
const LEGACY_TEXTURE = { plaster: 'render', stone: 'stone', concrete: 'concrete', wood: 'wood', tile: 'tile', paver: 'paver', grass: 'grass', asphalt: 'asphalt', fabric: 'fabric' };
const LEGACY_NAME = {
  woodfloor: { texture: 'woodfloor', alt: null }, floor: { texture: 'tile' }, wetfloor: { texture: 'tile', params: [4, .01, 0, .3] },
  roof: { texture: 'concrete' }, soil: { texture: 'soil', alt: '#3b2d20' }, rug: { texture: 'rug' }, frame: { texture: 'metal' },
  brass: { texture: 'brushed' }, linen: { texture: 'fabric' }, ceramic: {},
};

// Ground-type surfaces get world-space macro variation to hide texture repetition.
const MACRO = { grass: .16, cobble: .1, paver: .08, pebbles: .08, gravel: .1, soil: .12, asphalt: .12, render: .035, concrete: .07, deck: .05 };

const MACRO_GLSL = /* glsl */`
float ffHash(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float ffNoise(vec2 x){ vec2 i = floor(x), f = fract(x); vec2 u = f * f * (3. - 2. * f);
  return mix(mix(ffHash(i), ffHash(i + vec2(1, 0)), u.x), mix(ffHash(i + vec2(0, 1)), ffHash(i + vec2(1, 1)), u.x), u.y); }
float ffMacro(vec2 p){ return ffNoise(p * .11) * .55 + ffNoise(p * .37 + 7.) * .3 + ffNoise(p * 1.3 + 3.) * .15; }`;

function addMacro(material, amount, kind) {
  const stripes = kind === 'grass' ? 1 : 0;
  material.onBeforeCompile = (shader) => {
    shader.uniforms.ffMacroAmount = { value: amount };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vFFWorld;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvFFWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vFFWorld;\nuniform float ffMacroAmount;\n' + MACRO_GLSL)
      .replace('#include <map_fragment>', `#include <map_fragment>
  { float m = ffMacro(vFFWorld.xz); diffuseColor.rgb *= 1.0 + ffMacroAmount * (m - .5) * 2.0;
    ${stripes ? 'float s = step(.5, fract(vFFWorld.x / 1.35)); diffuseColor.rgb *= mix(.94, 1.05, s); diffuseColor.g *= 1.0 + .03 * (m - .5);' : ''} }`);
  };
  material.customProgramCacheKey = () => 'ffmacro-' + kind;
}

export class MaterialLibrary {
  constructor(synth, sceneMaterials) {
    this.synth = synth;
    this.defs = sceneMaterials;
    this.cache = new Map();
    this.emissive = [];
    this.clipPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 1e6);
    this.clay = new THREE.MeshStandardMaterial({ color: '#d8d4cb', roughness: .9, metalness: 0 });
    this.clayClip = this.clay.clone();
    this.clayClip.clippingPlanes = [this.clipPlane];
    this.clayClip.clipShadows = true;
  }

  descriptor(name) {
    const src = this.defs[name] || { color: '#cccccc', roughness: .8 };
    const d = { ...src };
    const legacy = LEGACY_NAME[name];
    if (!src.kind) {
      if (legacy && (legacy.texture || legacy.params)) Object.assign(d, { kind: legacy.texture, ...(legacy.params ? { params: legacy.params } : {}), ...(legacy.alt !== undefined && legacy.alt !== null ? { alt: legacy.alt } : {}) });
      else if (src.texture) d.kind = LEGACY_TEXTURE[src.texture] || src.texture;
    }
    return d;
  }

  // World-size of one texture repeat in metres, as [u, v].
  tileSize(name) {
    const d = this.descriptor(name);
    if (!d.kind || !KIND_DEFAULTS[d.kind]) return [1, 1];
    if (d.tile_m) return Array.isArray(d.tile_m) ? d.tile_m : [d.tile_m, d.tile_m];
    return KIND_DEFAULTS[d.kind].tile;
  }

  get(name, clipped = false) {
    const key = name + (clipped ? '|clip' : '');
    if (this.cache.has(key)) return this.cache.get(key);
    const m = this.build(name);
    if (clipped) { m.clippingPlanes = [this.clipPlane]; m.clipShadows = true; }
    this.cache.set(key, m);
    return m;
  }

  build(name) {
    const d = this.descriptor(name);
    const color = new THREE.Color(d.color || '#cccccc');
    const alpha = d.alpha ?? 1;
    // Glass: reflective, lightly tinted, double-sided; lets exterior light and views through.
    if (alpha < 1) {
      const m = new THREE.MeshPhysicalMaterial({
        color: color.clone().lerp(new THREE.Color('#ffffff'), .35), metalness: 0, roughness: d.roughness_override ?? .03,
        transparent: true, opacity: Math.max(.12, Math.min(.5, alpha * .75)), ior: 1.5, reflectivity: .5, specularIntensity: 1,
        envMapIntensity: 1.6, side: THREE.DoubleSide, depthWrite: false,
      });
      m.userData.glass = true;
      m.name = name;
      return m;
    }
    if (d.emission) {
      const m = new THREE.MeshStandardMaterial({ color: '#000000', emissive: color, emissiveIntensity: 1, roughness: .4 });
      m.userData.emissiveBase = d.emission * (d.lumen_scale ?? 6);
      this.emissive.push(m);
      m.name = name;
      return m;
    }
    const kind = d.kind && KIND_DEFAULTS[d.kind] ? d.kind : null;
    const useSheen = kind === 'fabric' || kind === 'rug' || d.sheen;
    const usePhysical = useSheen || d.clearcoat;
    const params = {
      color: '#ffffff', roughness: d.roughness_scale ?? 1, metalness: d.metallic ?? 0,
      envMapIntensity: d.env ?? 1,
    };
    const m = usePhysical ? new THREE.MeshPhysicalMaterial(params) : new THREE.MeshStandardMaterial(params);
    m.name = name;
    if (kind) {
      const tex = this.synth.make(kind, { base: d.color || '#cccccc', alt: d.alt || null, params: d.params || null, seed: d.seed || 0, normal: d.normal ?? null });
      m.map = tex.map;
      m.normalMap = tex.normalMap;
      m.roughnessMap = tex.roughnessMap;
      m.normalScale = new THREE.Vector2(1, 1);
      if (MACRO[kind]) addMacro(m, MACRO[kind], kind);
    } else {
      m.color.copy(color);
      m.roughness = d.roughness ?? .8;
    }
    if (useSheen && m.isMeshPhysicalMaterial) {
      m.sheen = d.sheen ?? .6;
      m.sheenRoughness = .75;
      m.sheenColor = color.clone().lerp(new THREE.Color('#ffffff'), .35);
    }
    if (d.clearcoat && m.isMeshPhysicalMaterial) {
      m.clearcoat = d.clearcoat;
      m.clearcoatRoughness = d.clearcoat_roughness ?? .08;
    }
    if (d.double_sided) m.side = THREE.DoubleSide;
    return m;
  }

  setLampLevel(level, floor = .08) {
    for (const m of this.emissive) m.emissiveIntensity = Math.max(floor, m.userData.emissiveBase * level);
  }

  dispose() {
    for (const m of this.cache.values()) m.dispose();
    this.clay.dispose(); this.clayClip.dispose();
    this.cache.clear();
  }
}
