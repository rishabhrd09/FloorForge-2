// The reveal mask: a plan-view texture over the site, one channel per storey (R ground and the garden, G first,
// B second/roof). Each room is a shape drawn with a soft disc that grows from the door the visitor came through, so
// its materials sweep across the room; the garden sweeps from the gate. Redrawn only when a sweep moves.
import * as THREE from 'three';

const VERT = 'varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }';
const FRAG = /* glsl */`
uniform vec2 uOrigin;
uniform float uRadius;
uniform float uSoft;
uniform vec4 uChannel;
varying vec2 vP;
void main() {
  float cover = 1. - smoothstep(uRadius - uSoft, uRadius, distance(vP, uOrigin));
  gl_FragColor = uChannel * cover;
}`;

const CHANNELS = [new THREE.Vector4(1, 0, 0, 0), new THREE.Vector4(0, 1, 0, 0), new THREE.Vector4(0, 0, 1, 0)];

export class RevealMask {
  constructor(renderer, data, { size = 1024, soft = .35 } = {}) {
    this.renderer = renderer;
    this.soft = soft;
    const [x0, y0, x1, y1] = data.maskBox;
    this.box = new THREE.Vector4(x0, y0, 1 / (x1 - x0), 1 / (y1 - y0));
    this.target = new THREE.WebGLRenderTarget(size, size, { type: THREE.UnsignedByteType, depthBuffer: false, generateMipmaps: false });
    this.target.texture.minFilter = THREE.LinearFilter; this.target.texture.magFilter = THREE.LinearFilter;
    this.camera = new THREE.OrthographicCamera(x0, x1, y1, y0, -10, 10);
    this.camera.position.z = 5;
    this.scene = new THREE.Scene();
    this.shapes = new Map();
    const add = (id, polygons, channels, reach) => {
      const group = [];
      for (const ch of channels) {
        const material = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG, depthTest: false, depthWrite: false,
          blending: THREE.CustomBlending, blendEquation: THREE.MaxEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor,
          uniforms: { uOrigin: { value: new THREE.Vector2() }, uRadius: { value: -1 }, uSoft: { value: soft }, uChannel: { value: CHANNELS[ch] } } });
        for (const poly of polygons) {
          const outer = new THREE.Shape(poly[0].map(([x, y]) => new THREE.Vector2(x, y)));
          for (const hole of poly.slice(1)) outer.holes.push(new THREE.Path(hole.map(([x, y]) => new THREE.Vector2(x, y))));
          const mesh = new THREE.Mesh(new THREE.ShapeGeometry(outer), material);
          this.scene.add(mesh);
        }
        group.push(material);
      }
      this.shapes.set(id, { materials: group, reach, progress: -1 });
    };
    for (const r of data.maskRooms) add(r.id, r.polygons, [Math.min(2, r.floor)], r.reach);
    // The garden, facades and roofs: one shape per storey, all sweeping together from the gate.
    const outside = [];
    for (const f of data.maskOutside.floors) {
      add('outside-' + f.floor, f.polygons, [Math.min(2, f.floor)], data.maskOutside.reach);
      outside.push(this.shapes.get('outside-' + f.floor));
    }
    this.shapes.set('outside', { group: outside, materials: outside.flatMap((s) => s.materials), reach: data.maskOutside.reach, progress: -1 });
    this.dirty = true;
    this.render();
  }

  // progress 0..1 of a room's sweep from `origin` (scene x, y); a negative progress hides the room again.
  set(id, progress, origin) {
    const s = this.shapes.get(id);
    if (!s) return;
    const p = Math.max(-1, Math.min(1, progress));
    if (Math.abs(p - s.progress) < 1e-4 && (!origin || (s.origin && s.origin[0] === origin[0] && s.origin[1] === origin[1]))) return;
    s.progress = p;
    if (origin) s.origin = origin;
    const radius = p <= 0 ? -1 : p >= 1 ? 1e4 : p * (s.reach + this.soft) ;
    for (const m of s.materials) {
      m.uniforms.uRadius.value = radius;
      if (s.origin) m.uniforms.uOrigin.value.set(s.origin[0], s.origin[1]);
    }
    this.dirty = true;
  }

  progress(id) { return this.shapes.get(id)?.progress ?? -1; }

  render() {
    if (!this.dirty) return;
    const r = this.renderer, prev = r.getRenderTarget(), clear = r.getClearColor(new THREE.Color()), alpha = r.getClearAlpha();
    const planes = r.clippingPlanes;
    r.clippingPlanes = [];
    r.setRenderTarget(this.target);
    r.setClearColor(0x000000, 0);
    r.clear(true, false, false);
    r.render(this.scene, this.camera);
    r.setRenderTarget(prev);
    r.setClearColor(clear, alpha);
    r.clippingPlanes = planes;
    this.dirty = false;
  }

  dispose() {
    this.target.dispose();
    this.scene.traverse((o) => { o.geometry?.dispose(); o.material?.dispose?.(); });
  }
}
