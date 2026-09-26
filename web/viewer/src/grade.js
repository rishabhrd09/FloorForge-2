// Final photographic grade: exposure, AgX tone mapping, gentle contrast/saturation, warmth and vignette.
import { Effect } from 'postprocessing';
import { Uniform } from 'three';

const FRAG = /* glsl */`
uniform float exposure;
uniform float contrast;
uniform float saturation;
uniform float warmth;
uniform float vignette;
uniform float lift;

const mat3 LIN_SRGB_TO_REC2020 = mat3(vec3(0.6274, 0.0691, 0.0164), vec3(0.3293, 0.9195, 0.0880), vec3(0.0433, 0.0113, 0.8956));
const mat3 REC2020_TO_LIN_SRGB = mat3(vec3(1.6605, -0.1246, -0.0182), vec3(-0.5876, 1.1329, -0.1006), vec3(-0.0728, -0.0083, 1.1187));
vec3 agxContrast(vec3 x){ vec3 x2 = x * x; vec3 x4 = x2 * x2;
  return 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232; }
vec3 agx(vec3 color){
  const mat3 inset = mat3(vec3(0.856627153315983, 0.137318972929847, 0.11189821299995), vec3(0.0951212405381588, 0.761241990602591, 0.0767994186031903), vec3(0.0482516061458583, 0.101439036467562, 0.811302368396859));
  const mat3 outset = mat3(vec3(1.1271005818144368, -0.1413297634984383, -0.14132976349843826), vec3(-0.11060664309660323, 1.157823702216272, -0.11060664309660294), vec3(-0.016493938717834573, -0.016493938717834257, 1.2519364065950405));
  const float minEv = -12.47393; const float maxEv = 4.026069;
  color = LIN_SRGB_TO_REC2020 * color;
  color = inset * color;
  color = max(color, 1e-10);
  color = log2(color);
  color = (color - minEv) / (maxEv - minEv);
  color = clamp(color, 0.0, 1.0);
  color = agxContrast(color);
  color = outset * color;
  color = pow(max(vec3(0.0), color), vec3(2.2));
  color = REC2020_TO_LIN_SRGB * color;
  return clamp(color, 0.0, 1.0);
}
void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor){
  vec3 c = inputColor.rgb * exposure;
  c *= vec3(1.0 + warmth * .06, 1.0, 1.0 - warmth * .07);
  c = agx(c);
  float l = dot(c, vec3(.2126, .7152, .0722));
  c = mix(vec3(l), c, saturation);
  // Contrast around mid-grey in a perceptual-ish space.
  vec3 g = pow(c, vec3(1.0 / 2.2));
  g = (g - .5) * contrast + .5 + lift;
  c = pow(clamp(g, 0.0, 1.0), vec3(2.2));
  vec2 d = uv - .5;
  float v = 1.0 - vignette * smoothstep(.25, .85, length(d * vec2(1.1, 1.0)));
  outputColor = vec4(c * v, inputColor.a);
}`;

export class GradeEffect extends Effect {
  constructor() {
    super('GradeEffect', FRAG, {
      uniforms: new Map([
        ['exposure', new Uniform(1)], ['contrast', new Uniform(1.06)], ['saturation', new Uniform(1.08)],
        ['warmth', new Uniform(0)], ['vignette', new Uniform(.22)], ['lift', new Uniform(0)],
      ]),
    });
  }
  set(name, value) { this.uniforms.get(name).value = value; }
}
