// Physically based materials for installed electrical parts. Engineering
// overlays (selection, traced routes) use separate unlit materials so they never
// look like part of the installation.
import * as THREE from '../../viewer/node_modules/three/build/three.module.js';

const cache = new Map();
const once = (key, make) => { if (!cache.has(key)) cache.set(key, make()); return cache.get(key); };

export const OVERLAY = { selected: '#f0a63a', trace: '#3ec7d8', traceDim: '#2a8e9b', energised: '#f6c25b' };

export function mat(name) {
  switch (name) {
    case 'plate': return once(name, () => new THREE.MeshPhysicalMaterial({ color: '#f4f3ee', roughness: .32, clearcoat: .55, clearcoatRoughness: .25, sheen: .1 }));
    case 'module': return once(name, () => new THREE.MeshPhysicalMaterial({ color: '#f7f6f2', roughness: .28, clearcoat: .65, clearcoatRoughness: .2 }));
    case 'moduleRear': return once(name, () => new THREE.MeshStandardMaterial({ color: '#e9e6dc', roughness: .62 }));
    case 'frame': return once(name, () => new THREE.MeshStandardMaterial({ color: '#b7bcc0', metalness: .85, roughness: .42 }));
    case 'galv': return once(name, () => new THREE.MeshStandardMaterial({ color: '#a9b0b4', metalness: .88, roughness: .5 }));
    case 'galvDark': return once(name, () => new THREE.MeshStandardMaterial({ color: '#7f878c', metalness: .82, roughness: .55 }));
    case 'screw': return once(name, () => new THREE.MeshStandardMaterial({ color: '#c8ccce', metalness: 1, roughness: .32 }));
    case 'brass': return once(name, () => new THREE.MeshStandardMaterial({ color: '#c6a35a', metalness: 1, roughness: .34 }));
    case 'copper': return once(name, () => new THREE.MeshStandardMaterial({ color: '#c47a4e', metalness: 1, roughness: .3 }));
    case 'tinned': return once(name, () => new THREE.MeshStandardMaterial({ color: '#c9c7bf', metalness: .95, roughness: .38 }));
    case 'conduit': return once(name, () => new THREE.MeshStandardMaterial({ color: '#e6e3d9', roughness: .58 }));
    case 'conduitCut': return once(name, () => new THREE.MeshStandardMaterial({ color: '#d9d4c6', roughness: .66, side: THREE.DoubleSide }));
    case 'chase': return once(name, () => new THREE.MeshStandardMaterial({ color: '#8f8a80', roughness: .95 }));
    case 'chaseEdge': return once(name, () => new THREE.MeshStandardMaterial({ color: '#b9b3a6', roughness: .9 }));
    case 'concrete': return once(name, () => new THREE.MeshStandardMaterial({ color: '#9b9a95', roughness: .96 }));
    case 'pvcBox': return once(name, () => new THREE.MeshStandardMaterial({ color: '#d7d4c9', roughness: .7 }));
    case 'enclosure': return once(name, () => new THREE.MeshStandardMaterial({ color: '#dcdad3', roughness: .48, metalness: .25 }));
    case 'enclosureInner': return once(name, () => new THREE.MeshStandardMaterial({ color: '#c9c7c0', roughness: .6, metalness: .2 }));
    case 'deadFront': return once(name, () => new THREE.MeshStandardMaterial({ color: '#e4e2db', roughness: .45, metalness: .2 }));
    case 'device': return once(name, () => new THREE.MeshPhysicalMaterial({ color: '#f1f0ea', roughness: .38, clearcoat: .3 }));
    case 'deviceGrey': return once(name, () => new THREE.MeshStandardMaterial({ color: '#5d6266', roughness: .5 }));
    case 'toggle': return once(name, () => new THREE.MeshStandardMaterial({ color: '#2f3336', roughness: .45 }));
    case 'toggleRed': return once(name, () => new THREE.MeshStandardMaterial({ color: '#b5332a', roughness: .45 }));
    case 'dinRail': return once(name, () => new THREE.MeshStandardMaterial({ color: '#c0c4c4', metalness: .9, roughness: .4 }));
    case 'meterBody': return once(name, () => new THREE.MeshPhysicalMaterial({ color: '#e8e8e2', roughness: .4, clearcoat: .3 }));
    case 'meterWindow': return once(name, () => new THREE.MeshPhysicalMaterial({ color: '#ffffff', roughness: .05, transmission: .85, thickness: .004, transparent: true, opacity: .35 }));
    case 'lcd': return once(name, () => new THREE.MeshStandardMaterial({ color: '#9fb39a', roughness: .3, emissive: '#1d2a1c', emissiveIntensity: .4 }));
    case 'seal': return once(name, () => new THREE.MeshStandardMaterial({ color: '#b2342a', roughness: .5 }));
    case 'fanBody': return once(name, () => new THREE.MeshPhysicalMaterial({ color: '#e9e7e0', roughness: .35, metalness: .25, clearcoat: .4 }));
    case 'fanBlade': return once(name, () => new THREE.MeshStandardMaterial({ color: '#dedbd2', roughness: .4, metalness: .35 }));
    case 'downrod': return once(name, () => new THREE.MeshStandardMaterial({ color: '#d9d7d0', roughness: .3, metalness: .6 }));
    case 'hook': return once(name, () => new THREE.MeshStandardMaterial({ color: '#6c6f70', metalness: .9, roughness: .45 }));
    case 'connector': return once(name, () => new THREE.MeshStandardMaterial({ color: '#f0eee6', roughness: .55 }));
    case 'rubber': return once(name, () => new THREE.MeshStandardMaterial({ color: '#2a2b2c', roughness: .8 }));
    case 'pit': return once(name, () => new THREE.MeshStandardMaterial({ color: '#8d8b84', roughness: .92 }));
    case 'pitCover': return once(name, () => new THREE.MeshStandardMaterial({ color: '#5b5e5f', metalness: .7, roughness: .55 }));
    case 'lensOn': return once(name, () => new THREE.MeshStandardMaterial({ color: '#fff4dc', emissive: '#ffd59a', emissiveIntensity: 2.4, roughness: .3 }));
    case 'lensOff': return once(name, () => new THREE.MeshStandardMaterial({ color: '#d9d8d2', roughness: .35, metalness: .05 }));
    case 'exhaust': return once(name, () => new THREE.MeshStandardMaterial({ color: '#efede6', roughness: .5 }));
    default: throw Error('Unknown material ' + name);
  }
}

// Insulation colours are passed in from the model (with their source), never assumed here.
export function insulation(hex) {
  return once('ins:' + hex, () => new THREE.MeshPhysicalMaterial({ color: hex, roughness: .42, clearcoat: .25, clearcoatRoughness: .4 }));
}

// Two-colour (green/yellow) protective-conductor insulation as a striped texture.
export function stripedInsulation(a, b) {
  return once(`stripe:${a}:${b}`, () => {
    const c = document.createElement('canvas'); c.width = 64; c.height = 64;
    const g = c.getContext('2d');
    g.fillStyle = a; g.fillRect(0, 0, 64, 64);
    g.fillStyle = b;
    for (let i = -64; i < 128; i += 22) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i + 11, 0); g.lineTo(i + 11 - 64, 64); g.lineTo(i - 64, 64); g.fill(); }
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(1, 40);
    return new THREE.MeshPhysicalMaterial({ map: tex, roughness: .42, clearcoat: .25 });
  });
}

export function overlayMaterial(kind, opacity = 1) {
  return once(`overlay:${kind}:${opacity}`, () => new THREE.MeshBasicMaterial({
    color: OVERLAY[kind] || kind, transparent: opacity < 1, opacity, depthWrite: false, toneMapped: false,
  }));
}

export function outlineMaterial(kind = 'selected') {
  return once('outline:' + kind, () => new THREE.MeshBasicMaterial({ color: OVERLAY[kind], side: THREE.BackSide, depthWrite: false, toneMapped: false }));
}

// Text/graphics printed on parts (module legends, legend strips, meter display).
export function printedTexture(width, height, draw, key) {
  return once('tex:' + key, () => {
    const c = document.createElement('canvas');
    c.width = width; c.height = height;
    draw(c.getContext('2d'), width, height);
    const tex = new THREE.CanvasTexture(c);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = 4;
    return tex;
  });
}

export function printedMaterial(key, width, height, draw, base = {}) {
  return once('pm:' + key, () => new THREE.MeshStandardMaterial({ map: printedTexture(width, height, draw, key), roughness: .45, ...base }));
}
