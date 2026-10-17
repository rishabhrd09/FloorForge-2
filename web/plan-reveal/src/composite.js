// The drawing composite. After the photographic grade, every pixel the visitor has not reached yet is redrawn as ink
// on paper from the drawing buffers (normals, depth and annotation ink of the same model, same camera); where the
// reveal mask says a room has been entered, the photograph shows through, with a warm line at the sweeping edge.
import { Effect } from 'postprocessing';
import { Uniform, Vector2, Vector3, Vector4, Matrix4 } from 'three';

const FRAG = /* glsl */`
uniform sampler2D tGbuf;
uniform sampler2D tDepth;
uniform sampler2D tMask;
uniform mat4 uProjInv;
uniform mat4 uCamWorld;
uniform float uNear;
uniform float uFar;
uniform vec4 uMaskBox;
uniform float uFloorH;
uniform vec3 uOutside;      // outdoor sweep beyond the mask: origin x, y and radius
uniform float uSky;         // the sky's own reveal
uniform float uAll;         // everything revealed (closing aerial)
uniform float uWipe;        // closing paper wipe position across the screen (0 none .. 1 all paper)
uniform float uLineWidth;
uniform vec2 uTexel;
uniform vec3 uPaper;
uniform vec3 uInk;
uniform vec3 uAccent;
uniform float uSheet;       // 1 on the flat sheet: no form shading, the paper reads as paper
uniform float uSoft;
uniform vec4 uFocus;        // house centre (three x, z) and radius: the site's far edges draw faintly
uniform float uPoche;       // the plan's cut walls inked over the colour plan
uniform vec2 uMaskTexel;
uniform float uClip;        // drawn lines stop at the sheet border (uFrame, in texture coordinates)
uniform vec4 uFrame;
uniform float uSiteFade;    // the closing plan: beyond the plot (uSite, scene x0 y0 x1 y1) returns to paper
uniform vec4 uSite;

float ffViewZ(float d) { return (uNear * uFar) / ((uFar - uNear) * d - uFar); }
float ffHash(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float ffNoise(vec2 x) { vec2 i = floor(x), f = fract(x); vec2 u = f * f * (3. - 2. * f);
  return mix(mix(ffHash(i), ffHash(i + vec2(1, 0)), u.x), mix(ffHash(i + vec2(0, 1)), ffHash(i + vec2(1, 1)), u.x), u.y); }

float ffChannel(vec2 m, float f) { vec4 s = texture2D(tMask, m); return f < .5 ? s.r : f < 1.5 ? s.g : s.b; }

float ffReveal(vec3 w) {
  vec2 p = vec2(w.x, -w.z);
  vec2 m = (p - uMaskBox.xy) * uMaskBox.zw;
  if (m.x < 0. || m.y < 0. || m.x > 1. || m.y > 1.)
    return max(uAll, 1. - smoothstep(uOutside.z - uSoft, uOutside.z, distance(p, uOutside.xy)));
  float f = floor((w.y + .08) / uFloorH);
  float r = ffChannel(m, f);
  // A sweep's front is soft over tens of centimetres; a shape's own edge is one texel, and the value there is only the
  // texture filter's blend. On such a still edge the reveal is snapped, so a cabinet back or a jamb that happens to
  // stand on a room's boundary does not glow as if a sweep were crossing it.
  if (r > .002 && r < .998) {
    float k = max(max(abs(ffChannel(m + vec2(uMaskTexel.x, 0.), f) - ffChannel(m - vec2(uMaskTexel.x, 0.), f)),
                      abs(ffChannel(m + vec2(0., uMaskTexel.y), f) - ffChannel(m - vec2(0., uMaskTexel.y), f))), 0.);
    if (k > .45) r = step(.5, r);
  }
  return max(r, uAll);
}

vec3 ffNormal(vec2 st) { return texture2D(tGbuf, st).rgb * 2. - 1.; }

void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec4 g = texture2D(tGbuf, uv);
  float d = texture2D(tDepth, uv).x;
  float ink = 1. - g.a;
  bool sky = d >= .999999;
  float rev;
  vec3 world = vec3(0.);
  if (sky) rev = max(uSky, uAll);
  else {
    vec4 v = uProjInv * vec4(uv * 2. - 1., d * 2. - 1., 1.);
    v /= v.w;
    world = (uCamWorld * v).xyz;
    rev = ffReveal(world);
  }
  // The accent band marks a sweep's front only, never the closing fades below.
  float sweep = rev, keep = 1.;
  if (uSiteFade > 0.) {
    vec2 sp = vec2(world.x, -world.z);
    float inside = sky ? 0. : smoothstep(0., .3, min(min(sp.x - uSite.x, uSite.z - sp.x), min(sp.y - uSite.y, uSite.w - sp.y)));
    keep = mix(1., inside, uSiteFade);
    rev *= keep;
  }
  if (uWipe > 0.) rev *= step(uWipe, uv.x);
  if (rev >= .999 && ink < .001) { outputColor = inputColor; return; }

  // Ink from the model itself: silhouettes (where inverse depth stops being planar) and creases (normal turns).
  vec2 dx = vec2(uTexel.x * uLineWidth, 0.), dy = vec2(0., uTexel.y * uLineWidth);
  float z0 = ffViewZ(d);
  float edge = 0.;
  if (!sky) {
    float iz = 1. / z0;
    float l = 1. / ffViewZ(texture2D(tDepth, uv - dx).x), r = 1. / ffViewZ(texture2D(tDepth, uv + dx).x);
    float b = 1. / ffViewZ(texture2D(tDepth, uv - dy).x), t = 1. / ffViewZ(texture2D(tDepth, uv + dy).x);
    float lap = max(abs(l + r - 2. * iz), abs(b + t - 2. * iz)) / max(abs(iz), 1e-6);
    edge = smoothstep(.0012, .006, lap);
    vec3 n = ffNormal(uv);
    float turn = max(max(1. - dot(n, ffNormal(uv + dx)), 1. - dot(n, ffNormal(uv - dx))),
                     max(1. - dot(n, ffNormal(uv + dy)), 1. - dot(n, ffNormal(uv - dy))));
    edge = max(edge, smoothstep(.12, .35, turn));
    // Distant geometry draws lighter, as a pen would; the plot's far edges fade out around the house.
    edge *= mix(1., .45, smoothstep(30., 140., -z0) * (1. - uSheet));
    edge *= 1. - .85 * smoothstep(uFocus.z, uFocus.z * 1.9, distance(world.xz, uFocus.xy));
  } else {
    float near = texture2D(tDepth, uv + dx).x + texture2D(tDepth, uv - dx).x + texture2D(tDepth, uv + dy).x + texture2D(tDepth, uv - dy).x;
    edge = near < 3.9999 ? .7 : 0.;
  }
  // Paper: a warm sheet with fibre and soft mottling; form shading only off the flat sheet.
  vec2 px = uv / uTexel;
  float fibre = ffNoise(px * .55) * .55 + ffNoise(px * .13 + 4.) * .45;
  float mottle = ffNoise(world.xz * .35 + 9.) * .5 + ffNoise(uv * 3.1) * .5;
  vec3 paper = uPaper * (.975 + .035 * fibre - .02 * mottle);
  vec3 n = ffNormal(uv);
  float key = clamp(dot(n, normalize(vec3(-.35, .55, .76))), 0., 1.);
  float shade = sky ? 1. : mix(.84 + .16 * key, 1., uSheet);
  vec3 drawn = paper * shade;
  if (uClip > 0.) {
    float beyond = 1. - step(uFrame.x, uv.x) * step(uv.x, uFrame.z) * step(uFrame.y, uv.y) * step(uv.y, uFrame.w);
    edge *= 1. - beyond * uClip; ink *= 1. - beyond * uClip;
  }
  drawn = mix(drawn, uInk, clamp(max(edge * .82, ink), 0., 1.));
  vec3 col = mix(drawn, inputColor.rgb, rev);
  // The sweeping edge between drawing and photograph.
  float band = smoothstep(.04, .5, sweep) * (1. - smoothstep(.5, .96, sweep)) * keep * step(uWipe, uv.x);
  col = mix(col, uAccent, band * .9 * (sky ? 0. : 1.));
  // On the closing colour plan the cut walls keep their poché, as on a rendered plan.
  col = mix(col, uInk * 1.35, ink * uPoche * rev);
  if (uWipe > 0.) col = mix(col, col * .82, smoothstep(.02, 0., abs(uv.x - uWipe)) * .6);
  outputColor = vec4(col, inputColor.a);
}`;

export class RevealEffect extends Effect {
  constructor() {
    super('RevealEffect', FRAG, {
      uniforms: new Map([
        ['tGbuf', new Uniform(null)], ['tDepth', new Uniform(null)], ['tMask', new Uniform(null)],
        ['uProjInv', new Uniform(new Matrix4())], ['uCamWorld', new Uniform(new Matrix4())], ['uNear', new Uniform(.05)], ['uFar', new Uniform(1500)],
        ['uMaskBox', new Uniform(new Vector4(0, 0, 1, 1))], ['uFloorH', new Uniform(3.15)], ['uOutside', new Uniform(new Vector3(0, 0, -1))],
        ['uSky', new Uniform(0)], ['uAll', new Uniform(0)], ['uWipe', new Uniform(0)], ['uLineWidth', new Uniform(1)],
        ['uTexel', new Uniform(new Vector2(1 / 1024, 1 / 1024))], ['uPaper', new Uniform(new Vector3(.94, .925, .89))],
        ['uInk', new Uniform(new Vector3(.11, .11, .1))], ['uAccent', new Uniform(new Vector3(.88, .38, .16))], ['uSheet', new Uniform(1)], ['uSoft', new Uniform(.35)], ['uFocus', new Uniform(new Vector4(0, 0, 1e4, 0))],
        ['uPoche', new Uniform(0)], ['uMaskTexel', new Uniform(new Vector2(1 / 1024, 1 / 1024))],
        ['uClip', new Uniform(0)], ['uFrame', new Uniform(new Vector4(0, 0, 1, 1))], ['uSiteFade', new Uniform(0)], ['uSite', new Uniform(new Vector4(-1e4, -1e4, 1e4, 1e4))],
      ]),
    });
  }

  set(name, value) { this.uniforms.get(name).value = value; }
  get(name) { return this.uniforms.get(name).value; }
}
