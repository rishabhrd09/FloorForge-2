// Presentation export: the scene as the viewer draws it (GPU-synthesised PBR textures, grown planting, lawn
// grass, ground and, optionally, the neighbourhood context) as binary glTF for offline renderers such as
// Blender Cycles. Lights, sky, fog and post-processing are left out; an offline renderer rebuilds lighting
// from scene.json. Instanced planting is baked into ordinary meshes so any glTF importer reads it.
import * as THREE from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const KEEP = new Set(['position', 'normal', 'uv', 'color']);
const MAPS = ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'emissiveMap', 'aoMap', 'alphaMap'];

// glTF always multiplies base colour by COLOR_0, whereas three.js ignores vertex colours unless the material
// opts in: keep them only where the viewer actually shows them.
function cleanGeometry(geometry, keepColor) {
  const g = geometry.index ? geometry.toNonIndexed() : geometry.clone();
  for (const name of Object.keys(g.attributes)) if (!KEEP.has(name) || (name === 'color' && !keepColor)) g.deleteAttribute(name);
  g.morphAttributes = {};
  return g;
}

export async function exportPresentation(viewer, { context = true, grass = true, contextRadius = 60 } = {}) {
  const renderer = viewer.renderer;
  const textures = new Map();
  // Synthesised textures live in GPU render targets: copy them into canvases (the exporter encodes canvases;
  // rows stay in GL order with flipY off, so the exported UVs sample exactly what the viewer shows).
  const plain = (texture) => {
    if (!texture) return null;
    if (textures.has(texture)) return textures.get(texture);
    const rt = viewer.synth.owner(texture);
    let out = texture;
    if (rt) {
      const { width, height } = rt;
      const pixels = new Uint8ClampedArray(width * height * 4);
      renderer.readRenderTargetPixels(rt, 0, 0, width, height, pixels);
      const canvas = document.createElement('canvas');
      canvas.width = width; canvas.height = height;
      canvas.getContext('2d').putImageData(new ImageData(pixels, width, height), 0, 0);
      out = new THREE.CanvasTexture(canvas);
      out.flipY = false;
      out.colorSpace = texture.colorSpace;
      out.wrapS = out.wrapT = THREE.RepeatWrapping;
      // Colour maps travel as JPEG; normal and roughness data stay lossless.
      if (texture.colorSpace === THREE.SRGBColorSpace) out.userData.mimeType = 'image/jpeg';
    }
    textures.set(texture, out);
    return out;
  };
  const materials = new Map();
  const material = (m) => {
    if (Array.isArray(m)) return m.map(material);
    if (materials.has(m)) return materials.get(m);
    const c = m.clone();
    for (const key of MAPS) if (c[key]) c[key] = plain(c[key]);
    c.clippingPlanes = null;
    materials.set(m, c);
    return c;
  };
  const group = new THREE.Group();
  group.name = 'FloorForge presentation';
  group.userData = { planHash: viewer.data?.planHash, draftRevision: viewer.data?.draftRevision, openingPoses: viewer.openings?.items.map(item => ({ id: item.id, openness: item.value })), poseScope: 'Walkthrough presentation state; canonical design exports retain authored opening poses.' };
  const matrix = new THREE.Matrix4(), tint = new THREE.Color(), at = new THREE.Vector3();
  const centre = viewer.center || new THREE.Vector3();
  const add = (mesh, name, radius = Infinity) => {
    mesh.updateMatrixWorld(true);
    const keepColor = [].concat(mesh.material).some((m) => m.vertexColors);
    if (mesh.isInstancedMesh) {
      if (!mesh.count) return;
      const parts = [];
      for (let i = 0; i < mesh.count; i++) {
        mesh.getMatrixAt(i, matrix);
        matrix.premultiply(mesh.matrixWorld);
        // The distant horizon ring is backdrop for the live view only; offline renders keep nearby context.
        if (Math.hypot(at.setFromMatrixPosition(matrix).x - centre.x, at.z - centre.z) > radius) continue;
        const g = cleanGeometry(mesh.geometry, keepColor);
        g.applyMatrix4(matrix);
        if (mesh.instanceColor && g.attributes.color) {
          mesh.getColorAt(i, tint);
          const c = g.attributes.color;
          for (let k = 0; k < c.count; k++) c.setXYZ(k, c.getX(k) * tint.r, c.getY(k) * tint.g, c.getZ(k) * tint.b);
        }
        parts.push(g);
      }
      if (!parts.length) return;
      const merged = mergeGeometries(parts, false);
      parts.forEach((g) => g.dispose());
      if (!merged) return;
      const out = new THREE.Mesh(merged, material(mesh.material));
      out.name = name;
      group.add(out);
      return;
    }
    const g = cleanGeometry(mesh.geometry, keepColor);
    g.applyMatrix4(mesh.matrixWorld);
    const out = new THREE.Mesh(g, material(mesh.material));
    out.name = name;
    group.add(out);
  };
  viewer.meshes.forEach((mesh, i) => {
    if (mesh.userData.vehicle && !viewer.carVisible) return;
    const b = mesh.userData.bucket || {};
    add(mesh, `${b.material || 'surface'}-${b.floor ?? 'site'}-${i}`);
  });
  if (viewer.groundMesh) add(viewer.groundMesh, 'ground');
  viewer.vegetation?.group.traverse((o) => { if (o.isMesh && (grass || o !== viewer.vegetation.lawn)) add(o, o === viewer.vegetation.lawn ? 'lawn-grass' : 'planting'); });
  if (context && viewer.context) viewer.context.traverse((o) => { if (o.isMesh) add(o, 'context', contextRadius); });
  const exporter = new GLTFExporter();
  const glb = await exporter.parseAsync(group, { binary: true, onlyVisible: false, maxTextureSize: 2048 });
  group.traverse((o) => { if (o.isMesh) o.geometry.dispose(); });
  for (const t of textures.values()) if (t.isCanvasTexture) t.dispose();
  for (const m of materials.values()) [].concat(m).forEach((x) => x.dispose());
  return glb;
}
