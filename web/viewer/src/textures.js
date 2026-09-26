// GPU procedural texture synthesis. Every surface pattern is authored here as a tileable
// GLSL function, rendered once into mip-mapped render targets (albedo / normal / roughness).
// No downloaded bitmaps, no network: identical output offline.
import * as THREE from 'three';

const VERT = /* glsl */`
varying vec2 vUv;
void main(){ vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

const COMMON = /* glsl */`
precision highp float;
varying vec2 vUv;
uniform vec3 uBase;      // linear base colour
uniform vec3 uAlt;       // linear secondary colour
uniform vec4 uP;         // kind parameters
uniform float uSeed;
uniform int uMode;       // 0 albedo, 1 normal, 2 roughness
uniform float uNormal;   // normal strength
uniform float uTexel;    // 1 / size

float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031 + uSeed * .0137); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec2 hash22(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973) + uSeed * .0171); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
float vnoise(vec2 x, vec2 per){
  vec2 i = floor(x), f = fract(x); vec2 u = f * f * (3. - 2. * f);
  float a = hash12(mod(i, per)), b = hash12(mod(i + vec2(1., 0.), per));
  float c = hash12(mod(i + vec2(0., 1.), per)), d = hash12(mod(i + vec2(1., 1.), per));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbm(vec2 p, vec2 per, int oct){
  float s = 0., a = .5, n = 0.;
  for (int i = 0; i < 8; i++) { if (i >= oct) break; s += a * vnoise(p, per); n += a; p *= 2.; per *= 2.; a *= .5; }
  return s / n;
}
// Free (non-periodic) noise for features evaluated in local cell space.
float fnoise(vec2 x){ vec2 i = floor(x), f = fract(x); vec2 u = f * f * (3. - 2. * f);
  return mix(mix(hash12(i), hash12(i + vec2(1, 0)), u.x), mix(hash12(i + vec2(0, 1)), hash12(i + vec2(1, 1)), u.x), u.y); }
float ffbm(vec2 p, int oct){ float s = 0., a = .5, n = 0.; for (int i = 0; i < 8; i++) { if (i >= oct) break; s += a * fnoise(p); n += a; p = p * 2.03 + 1.7; a *= .5; } return s / n; }
// Periodic Worley noise: F1, F2, id hash, id hash 2.
vec4 voronoi(vec2 x, vec2 per, float jitter){
  vec2 n = floor(x), f = fract(x); float F1 = 8., F2 = 8.; vec2 id = vec2(0.);
  for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
    vec2 g = vec2(float(i), float(j)); vec2 cell = mod(n + g, per);
    vec2 o = .5 + (hash22(cell) - .5) * jitter; vec2 r = g + o - f; float d = dot(r, r);
    if (d < F1) { F2 = F1; F1 = d; id = cell; } else if (d < F2) { F2 = d; }
  }
  return vec4(sqrt(F1), sqrt(F2), hash12(id + 3.1), hash12(id + 17.7));
}
float sdBox(vec2 p, vec2 b){ vec2 d = abs(p) - b; return length(max(d, 0.)) + min(max(d.x, d.y), 0.); }
float sdRoundBox(vec2 p, vec2 b, float r){ return sdBox(p, b - r) - r; }
vec3 srgb(vec3 c){ return pow(c, vec3(2.2)); }
float luma(vec3 c){ return dot(c, vec3(.2126, .7152, .0722)); }
// smoothstep that accepts reversed edges (GLSL leaves edge0 >= edge1 undefined).
float sstep(float a, float b, float x){ float t = clamp((x - a) / (b - a), 0., 1.); return t * t * (3. - 2. * t); }
`;

// Each kind implements: void surface(vec2 p, out vec3 c, out float h, out float r)
// p is in [0,1)^2 and must tile seamlessly. c is linear albedo. h is height (arbitrary units, ~0..1).
const KINDS = {
  render: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float lo = fbm(p * 3., vec2(3.), 4);
  float mid = fbm(p * 22., vec2(22.), 3);
  float hi = fbm(p * 96., vec2(96.), 3);
  float grain = vnoise(p * 384., vec2(384.));
  h = hi * .55 + grain * .35 + mid * .25;
  c = uBase * (.955 + .07 * (lo - .5) + .035 * (mid - .5) + .02 * (grain - .5));
  r = .82 + .1 * hi;
}`,
  concrete: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float lo = fbm(p * 4., vec2(4.), 5);
  float mid = fbm(p * 24., vec2(24.), 4);
  float pores = smoothstep(.80, .92, vnoise(p * 210., vec2(210.))) * smoothstep(.4, .7, vnoise(p * 57., vec2(57.)));
  float grain = vnoise(p * 420., vec2(420.));
  h = mid * .5 + grain * .25 - pores * .9;
  c = uBase * (.9 + .16 * (lo - .5) * 2. + .06 * (mid - .5)) * (1. - .35 * pores);
  r = .72 + .16 * lo + .1 * pores;
}`,
  stone: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float lo = fbm(p * 5., vec2(5.), 5);
  float mid = fbm(p * 30., vec2(30.), 4);
  float specks = smoothstep(.83, .95, vnoise(p * 160., vec2(160.)));
  float bed = sin((p.y + lo * .12) * 6.2831853 * 7.) * .5 + .5;
  h = mid * .6 + vnoise(p * 300., vec2(300.)) * .3;
  c = uBase * (.92 + .1 * (lo - .5) * 2. + .03 * bed + .04 * (mid - .5)) * (1. - .22 * specks);
  r = .55 + .12 * mid;
}`,
  marble: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float w = fbm(p * 3., vec2(3.), 6);
  float v = abs(sin((p.x * 2. + p.y + w * 3.2) * 6.2831853));
  float vein = pow(1. - v, 22.) + .45 * pow(1. - abs(sin((p.x * 5. - p.y * 3. + w * 5.) * 6.2831853)), 40.);
  float cloud = fbm(p * 9., vec2(9.), 4);
  c = mix(uBase * (.97 + .05 * (cloud - .5)), uAlt, clamp(vein * .75, 0., 1.));
  h = cloud * .2;
  r = .12 + .06 * cloud;
}`,
  tile: /* glsl */`
// uP.x tiles per texture, uP.y grout width (fraction of tile), uP.z veining, uP.w gloss 0..1
void surface(vec2 p, out vec3 c, out float h, out float r){
  float n = uP.x; vec2 g = p * n; vec2 id = mod(floor(g), vec2(n)); vec2 f = fract(g) - .5;
  float gw = uP.y;
  float d = sdRoundBox(f, vec2(.5 - gw * .5), gw * .6);
  float tileMask = sstep(0., -gw * .35, d);
  float t = hash12(id + 5.);
  float cloud = fbm(p * 6., vec2(6.), 5);
  float w = fbm(p * 2., vec2(2.), 5);
  float vein = pow(1. - abs(sin((p.x + p.y * .7 + w * 2.6) * 6.2831853 * 1.5)), 26.) * uP.z;
  vec3 face = uBase * (.955 + .06 * t + .05 * (cloud - .5));
  face = mix(face, uAlt * 1.1, clamp(vein, 0., .45));
  vec3 grout = uBase * .62 * vec3(.97, .96, .93);
  c = mix(grout, face, tileMask);
  h = tileMask * (.8 + .05 * vnoise(p * 180., vec2(180.))) ;
  float gloss = mix(.38, .09, uP.w);
  r = mix(.92, gloss + .05 * cloud, tileMask);
}`,
  terrazzo: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  vec4 v = voronoi(p * 38., vec2(38.), .95);
  vec4 v2 = voronoi(p * 90. + 3.1, vec2(90.), .9);
  float chip = step(v.x, .22 + .12 * v.z) * step(.45, v.w);
  float chip2 = step(v2.x, .18) * step(.6, v2.w);
  vec3 cc = mix(uAlt, uBase * .55, v.z);
  c = uBase * (.97 + .05 * fbm(p * 8., vec2(8.), 3));
  c = mix(c, cc, chip); c = mix(c, uAlt * 1.2, chip2 * .8);
  h = .5; r = .22 + .05 * v.z;
}`,
  wood: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float warp = fbm(p * vec2(2., 6.), vec2(2., 6.), 4);
  float rings = sin((p.y * 18. + warp * 3.5 + fbm(p * vec2(1., 3.), vec2(1., 3.), 3) * 2.) * 6.2831853) * .5 + .5;
  float streak = fbm(p * vec2(3., 120.), vec2(3., 120.), 4);
  float pores = smoothstep(.65, .9, vnoise(p * vec2(60., 480.), vec2(60., 480.)));
  float tone = .82 + .22 * rings * .6 + .16 * (streak - .5);
  c = uBase * tone * (1. - .18 * pores);
  c = mix(c, uBase * vec3(.78, .7, .62), .25 * smoothstep(.55, .95, rings));
  h = streak * .4 - pores * .3;
  r = .48 + .12 * streak + .08 * pores;
}`,
  woodfloor: /* glsl */`
// Planks run along u. uP.x rows per texture, uP.y bevel.
void surface(vec2 p, out vec3 c, out float h, out float r){
  float rows = uP.x; float row = mod(floor(p.y * rows), rows); float fy = fract(p.y * rows);
  float off = hash12(vec2(row, 3.));
  float uu = fract(p.x + off);
  float split = .32 + .36 * hash12(vec2(row, 7.));
  float idx = uu < split ? 0. : 1.;
  float start = idx == 0. ? 0. : split; float len = idx == 0. ? split : 1. - split;
  float fu = (uu - start) / len;
  vec2 pid = vec2(row, idx);
  float ph = hash12(pid + 11.), ph2 = hash12(pid + 23.);
  vec2 q = vec2(fu * len * 2.4, fy * .2) * vec2(1., 1.) + vec2(ph * 31., ph2 * 17.);
  float warp = ffbm(q * vec2(1.5, 14.), 3);
  float grain = sin((fy * 3. + warp * 2.2 + ffbm(q * vec2(.6, 6.), 2)) * 6.2831853 * (1.5 + ph * 2.)) * .5 + .5;
  float streak = ffbm(vec2(q.x * 2., fy * 40. + ph * 9.), 4);
  float pores = smoothstep(.62, .9, fnoise(vec2(q.x * 90., fy * 70. + ph * 50.)));
  float knot = smoothstep(.93, .99, fnoise(q * vec2(1.2, 6.)));
  vec3 plank = mix(uBase, uAlt, ph * .7) * (.86 + .12 * ph2);
  plank *= .86 + .16 * grain + .1 * (streak - .5);
  plank *= 1. - .2 * pores - .35 * knot;
  float bevel = uP.y;
  float ex = smoothstep(0., bevel, fy) * smoothstep(0., bevel, 1. - fy);
  float ez = smoothstep(0., bevel * .08, fu * len) * smoothstep(0., bevel * .08, (1. - fu) * len);
  float edge = ex * ez;
  c = mix(plank * .55, plank, edge);
  h = edge * .9 + streak * .08 - pores * .05;
  r = mix(.7, .34 + .1 * streak + .08 * pores, edge);
}`,
  deck: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float rows = uP.x; float row = mod(floor(p.y * rows), rows); float fy = fract(p.y * rows);
  float off = hash12(vec2(row, 5.)); float uu = fract(p.x + off);
  float ph = hash12(vec2(row, floor((p.x + off) * 1.)));
  float gap = smoothstep(0., .06, fy) * smoothstep(0., .06, 1. - fy);
  float end = smoothstep(0., .004, uu) * smoothstep(0., .004, 1. - uu);
  float grooves = sin(fy * 6.2831853 * 9.) * .5 + .5;
  float streak = fbm(vec2(p.x * 3., p.y * 90.), vec2(3., 90.), 4);
  vec3 board = mix(uBase, uAlt, ph * .6) * (.88 + .16 * (streak - .5) * 2.);
  float m = gap * end;
  c = mix(board * .25, board * (.94 + .06 * grooves), m);
  h = m * (.85 + .08 * grooves);
  r = mix(.9, .62 + .1 * streak, m);
}`,
  cobble: /* glsl */`
// Stamped / setted cobblestone in running bond. uP.x rows, uP.y stones per row, uP.z joint.
void surface(vec2 p, out vec3 c, out float h, out float r){
  float rows = uP.x, k = uP.y, joint = uP.z;
  float row = mod(floor(p.y * rows), rows); float fy = fract(p.y * rows);
  float x = fract(p.x + (mod(row, 2.) * .5 + hash12(vec2(row, 1.)) * .15) / k) * k;
  float j = floor(x);
  float jl = j + (hash12(vec2(row, mod(j, k))) - .5) * .3;
  float jr = j + 1. + (hash12(vec2(row, mod(j + 1., k))) - .5) * .3;
  float s = j;
  if (x < jl) { jr = jl; s = j - 1.; jl = s + (hash12(vec2(row, mod(s, k))) - .5) * .3; }
  else if (x >= jr) { jl = jr; s = j + 1.; jr = s + 1. + (hash12(vec2(row, mod(s + 1., k))) - .5) * .3; }
  float w = jr - jl;
  vec2 local = vec2((x - jl) / w - .5, fy - .5);
  vec2 sizeM = vec2(w / k, 1. / rows);            // stone size in texture units
  vec2 lp = local * sizeM;
  vec2 id = vec2(row, mod(s, k));
  float t = hash12(id + 9.), t2 = hash12(id + 21.), t3 = hash12(id + 40.);
  float d = sdRoundBox(lp + (hash22(id) - .5) * joint * .3, sizeM * .5 - joint * .5, min(sizeM.x, sizeM.y) * (.18 + .12 * t2));
  float stoneMask = sstep(joint * .15, -joint * .25, d);
  float dome = clamp(-d / (min(sizeM.x, sizeM.y) * .5), 0., 1.);
  float surf = fbm(p * 60., vec2(60.), 5);
  float chip = fbm(p * 150., vec2(150.), 3);
  vec3 stone = mix(uBase, uAlt, t * .8) * (.78 + .34 * t2);
  stone *= .88 + .2 * (surf - .5) * 2. + .06 * (chip - .5);
  stone = mix(stone, stone * vec3(.92, .9, .95), step(.8, t3) * .7);
  vec3 jointCol = uBase * .32 * vec3(1., .97, .92) * (.8 + .4 * vnoise(p * 90., vec2(90.)));
  c = mix(jointCol, stone, stoneMask);
  h = stoneMask * (.55 + .35 * sqrt(dome) + .18 * surf + .05 * chip);
  r = mix(.95, .5 + .22 * surf + .1 * t, stoneMask);
}`,
  paver: /* glsl */`
// Large concrete/stone slabs in stretcher bond. uP.x rows, uP.y slabs per row, uP.z joint.
void surface(vec2 p, out vec3 c, out float h, out float r){
  float rows = uP.x, k = uP.y, joint = uP.z;
  float row = mod(floor(p.y * rows), rows); float fy = fract(p.y * rows);
  float x = fract(p.x + mod(row, 2.) * .5 / k) * k; float s = mod(floor(x), k); float fx = fract(x);
  vec2 sizeM = vec2(1. / k, 1. / rows);
  vec2 lp = (vec2(fx, fy) - .5) * sizeM;
  float d = sdRoundBox(lp, sizeM * .5 - joint * .5, joint * .6);
  float m = sstep(joint * .1, -joint * .2, d);
  vec2 id = vec2(row, s); float t = hash12(id + 2.);
  float surf = fbm(p * 40., vec2(40.), 5); float grain = vnoise(p * 300., vec2(300.));
  vec3 slab = mix(uBase, uAlt, t * .5) * (.9 + .14 * (surf - .5) * 2. + .04 * (grain - .5));
  c = mix(uBase * .45, slab, m);
  h = m * (.8 + .1 * surf + .05 * grain);
  r = mix(.95, .7 + .15 * surf, m);
}`,
  pebbles: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float cells = uP.x;
  vec4 v = voronoi(p * cells, vec2(cells), .92);
  vec4 v2 = voronoi(p * cells * 2.3 + 7.3, vec2(cells * 2.3), .9);
  float s = v.x / (v.x + v.y); float s2 = v2.x / (v2.x + v2.y);
  float big = clamp(1. - pow(s * 2.25, 2.4), 0., 1.);
  float small = clamp(1. - pow(s2 * 2.15, 3.), 0., 1.) * .55;
  float dome = max(sqrt(big), small * .9);
  bool isBig = sqrt(big) >= small * .9;
  float t = isBig ? v.z : v2.z; float t2 = isBig ? v.w : v2.w;
  vec3 peb = uBase * (.86 + .2 * t);
  peb = mix(peb, uAlt * (.8 + .4 * t), step(.86, t2));
  peb *= .92 + .1 * vnoise(p * 400., vec2(400.));
  float shade = smoothstep(0., .35, dome);
  c = mix(uBase * .16, peb, shade) * (.75 + .25 * dome);
  h = dome;
  r = mix(.9, .42 + .2 * t, shade);
}`,
  gravel: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float cells = uP.x;
  vec4 v = voronoi(p * cells, vec2(cells), 1.);
  vec4 v2 = voronoi(p * cells * 1.9 + 3.7, vec2(cells * 1.9), 1.);
  float e = smoothstep(0., .18, v.y - v.x); float e2 = smoothstep(0., .2, v2.y - v2.x);
  float facet = 1. - v.x * .9; float facet2 = 1. - v2.x;
  float hA = e * facet, hB = e2 * facet2 * .8;
  float useA = step(hB, hA);
  float t = mix(v2.z, v.z, useA);
  h = max(hA, hB);
  vec3 g = mix(uBase, uAlt, t) * (.75 + .5 * vnoise(p * 500., vec2(500.)));
  c = mix(uBase * .25, g, smoothstep(0., .3, h));
  r = .82 + .1 * t;
}`,
  grass: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float patchy = fbm(p * 3., vec2(3.), 5);
  float clump = fbm(p * 18., vec2(18.), 4);
  float b1 = vnoise(p * vec2(640., 170.), vec2(640., 170.));
  float b2 = vnoise(p * vec2(170., 640.) + 13.1, vec2(170., 640.));
  float b3 = vnoise(p * 900., vec2(900.));
  float blades = max(b1, b2) * .7 + b3 * .3;
  vec3 dark = uBase * .55, light = uBase * 1.18, dry = uAlt;
  vec3 g = mix(dark, light, smoothstep(.3, .9, blades));
  g = mix(g, dry, smoothstep(.62, .85, patchy) * .35 + smoothstep(.75, .95, b3) * .15);
  g *= .9 + .2 * (clump - .5) * 2.;
  c = g;
  h = blades * .8 + clump * .2;
  r = .9 - .12 * blades;
}`,
  soil: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  vec4 v = voronoi(p * vec2(uP.x, uP.x * .55), vec2(uP.x, uP.x * .55), 1.);
  float chip = smoothstep(0., .25, v.y - v.x);
  float fine = vnoise(p * 380., vec2(380.));
  c = mix(uBase * .45, mix(uBase, uAlt, v.z) * (.8 + .4 * v.w), chip) * (.85 + .3 * fine);
  h = chip * (.6 + .4 * v.w) + fine * .2;
  r = .95;
}`,
  asphalt: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  vec4 v = voronoi(p * 160., vec2(160.), 1.);
  float agg = smoothstep(0., .2, v.y - v.x) * step(.55, v.z);
  float stain = fbm(p * 3., vec2(3.), 5);
  float fine = vnoise(p * 600., vec2(600.));
  c = uBase * (.8 + .35 * (stain - .5) * 2. + .15 * fine);
  c = mix(c, uAlt * (.8 + .4 * v.w), agg * .55);
  h = agg * .6 + fine * .3;
  r = .86 - .1 * stain + .05 * agg;
}`,
  encaustic: /* glsl */`
// Patterned cement tiles. uP.x tiles per texture.
void surface(vec2 p, out vec3 c, out float h, out float r){
  float n = uP.x; vec2 g = fract(p * n) - .5; vec2 id = floor(p * n);
  vec2 a = abs(g);
  float gw = .012;
  float grout = step(.5 - gw, max(a.x, a.y));
  // Quarter circles at corners form rings across tiles; a four-point star in the centre.
  float corner = length(a - .5);
  float ring = sstep(.02, .0, abs(corner - .30) - .035);
  float petal = sstep(.015, 0., abs(length(g) - .21) - .02);
  float diamond = sstep(.01, 0., (a.x + a.y) - .16);
  float crossM = step(max(a.x, a.y), .47) * sstep(.01, 0., min(a.x, a.y) - .018) * step(.24, max(a.x, a.y));
  float star = max(diamond, max(petal, crossM));
  float dark = clamp(max(ring, star), 0., 1.);
  float wear = fbm(p * 30., vec2(30.), 4);
  vec3 light = uBase * (.95 + .07 * (wear - .5));
  vec3 ink = uAlt * (.92 + .1 * wear);
  c = mix(light, ink, dark);
  c = mix(c, uBase * .7, grout);
  h = (1. - grout) * .9 + .04 * wear;
  r = mix(.9, .48 + .12 * wear, 1. - grout);
}`,
  fabric: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float n = uP.x;
  float wx = sin(p.x * 6.2831853 * n) , wy = sin(p.y * 6.2831853 * n);
  float over = step(0., sin(p.x * 3.14159265 * n) * sin(p.y * 3.14159265 * n));
  float weave = mix(wx * .5 + .5, wy * .5 + .5, over);
  float fuzz = fbm(p * 90., vec2(90.), 4);
  float slub = fbm(p * vec2(4., 60.), vec2(4., 60.), 3);
  c = uBase * (.9 + .09 * weave + .08 * (fuzz - .5) + .05 * (slub - .5));
  h = weave * .6 + fuzz * .3;
  r = .88 + .08 * fuzz;
}`,
  rug: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float pile = fbm(p * 160., vec2(160.), 3);
  float knots = vnoise(p * 520., vec2(520.));
  float band = smoothstep(.45, .5, abs(fract(p.y * 4. + fbm(p * 3., vec2(3.), 3) * .15) - .5)) * .5;
  c = mix(uBase, uAlt, band * .6) * (.86 + .18 * pile + .06 * knots);
  h = pile * .6 + knots * .4;
  r = .97;
}`,
  metal: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float peel = fbm(p * 70., vec2(70.), 4);
  c = uBase * (.97 + .05 * (peel - .5));
  h = peel * .4;
  r = clamp(uP.x + .08 * (peel - .5), .05, 1.);
}`,
  brushed: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  float s = vnoise(p * vec2(6., 900.), vec2(6., 900.)) * .6 + vnoise(p * vec2(12., 2200.), vec2(12., 2200.)) * .4;
  c = uBase * (.9 + .16 * s);
  h = s * .3;
  r = clamp(uP.x + .12 * (s - .5), .05, 1.);
}`,
  stoneclad: /* glsl */`
// Split-face ledgestone strips. uP.x rows per texture.
void surface(vec2 p, out vec3 c, out float h, out float r){
  float rows = uP.x; float row = mod(floor(p.y * rows), rows); float fy = fract(p.y * rows);
  float k = 3.;
  float x = fract(p.x + hash12(vec2(row, 2.))) * k; float j = mod(floor(x), k); float fx = fract(x);
  vec2 id = vec2(row, j); float t = hash12(id + 4.), t2 = hash12(id + 8.);
  float jointY = smoothstep(0., .08, fy) * smoothstep(0., .08, 1. - fy);
  float jointX = smoothstep(0., .015, fx) * smoothstep(0., .015, 1. - fx);
  float m = jointY * jointX;
  float rough = fbm(p * vec2(18., 40.), vec2(18., 40.), 5);
  float split = fbm(p * vec2(60., 120.), vec2(60., 120.), 3);
  vec3 st = mix(uBase, uAlt, t) * (.78 + .3 * rough + .1 * t2);
  c = mix(uBase * .25, st, m);
  h = m * (.45 + .35 * t2 + .35 * rough + .1 * split);
  r = mix(.95, .8 + .1 * rough, m);
}`,
  leather: /* glsl */`
void surface(vec2 p, out vec3 c, out float h, out float r){
  vec4 v = voronoi(p * 90., vec2(90.), 1.);
  float cr = smoothstep(0., .12, v.y - v.x);
  float lo = fbm(p * 5., vec2(5.), 4);
  c = uBase * (.85 + .15 * cr + .08 * (lo - .5));
  h = cr * .6;
  r = .45 + .15 * (1. - cr);
}`,
  bark: /* glsl */`
// u wraps around the stem, v runs along it. uP.x fissure depth, uP.y ring count (palms).
void surface(vec2 p, out vec3 c, out float h, out float r){
  float fis = fbm(p * vec2(8., 3.), vec2(8., 3.), 5);
  float cracks = smoothstep(.46, .72, fbm(p * vec2(22., 6.), vec2(22., 6.), 4));
  float rings = uP.y > 0. ? smoothstep(.82, 1., abs(sin(p.y * 3.14159265 * uP.y))) : 0.;
  float lich = smoothstep(.7, .9, fbm(p * 5. + 4., vec2(5.), 4));
  c = uBase * (.78 + .38 * fis) * (1. - .45 * cracks * uP.x) * (1. - .28 * rings);
  c = mix(c, uAlt, lich * .3);
  h = fis * .6 - cracks * uP.x * .9 - rings * .6;
  r = .88;
}`,
  art: /* glsl */`
// Abstract painted canvas for wall art (soft washes, a few confident strokes).
void surface(vec2 p, out vec3 c, out float h, out float r){
  float a = fbm(p * 2. + uSeed, vec2(2.), 5);
  float b = fbm(p * 3. + 9.1, vec2(3.), 5);
  vec3 wash = mix(uBase, uAlt, smoothstep(.35, .75, a));
  wash = mix(wash, vec3(.85, .82, .76), smoothstep(.55, .8, b) * .6);
  float stroke = sstep(.02, 0., abs(sin(p.x * 6.28 + a * 4.) * .3 + .5 - p.y) - .01) * .5;
  c = mix(wash, uAlt * .4, stroke);
  float canvas = vnoise(p * 700., vec2(700.));
  c *= .95 + .08 * canvas;
  h = canvas * .5 + a * .2;
  r = .85;
}`,
};

const FRAG_MAIN = /* glsl */`
void main(){
  vec2 p = vUv;
  vec3 c; float h; float r;
  if (uMode == 1) {
    float e = uTexel;
    vec3 c0; float r0; float hx0, hx1, hy0, hy1;
    surface(fract(p + vec2(-e, 0.)), c0, hx0, r0);
    surface(fract(p + vec2(e, 0.)), c0, hx1, r0);
    surface(fract(p + vec2(0., -e)), c0, hy0, r0);
    surface(fract(p + vec2(0., e)), c0, hy1, r0);
    vec3 n = normalize(vec3((hx0 - hx1) * uNormal, (hy0 - hy1) * uNormal, 1.));
    gl_FragColor = vec4(n * .5 + .5, 1.);
    return;
  }
  surface(p, c, h, r);
  if (uMode == 0) gl_FragColor = vec4(clamp(c, 0., 1.), 1.);
  else gl_FragColor = vec4(1., clamp(r, .02, 1.), 0., 1.);
}`;

export const TEXTURE_KINDS = Object.keys(KINDS);

// Default authoring parameters per kind: [size factor, texture world size (m), params, normal strength].
export const KIND_DEFAULTS = {
  render: { tile: [2.2, 2.2], p: [0, 0, 0, 0], normal: 1.2, hi: false },
  concrete: { tile: [2.0, 2.0], p: [0, 0, 0, 0], normal: 1.6, hi: false },
  stone: { tile: [1.6, 1.6], p: [0, 0, 0, 0], normal: 1.0, hi: false },
  marble: { tile: [1.4, 1.4], p: [0, 0, 0, 0], normal: .4, hi: true },
  tile: { tile: [1.2, 1.2], p: [2, .006, .35, .8], normal: 3.0, hi: true },
  terrazzo: { tile: [1.0, 1.0], p: [0, 0, 0, 0], normal: .3, hi: true },
  wood: { tile: [1.2, 1.2], p: [0, 0, 0, 0], normal: .8, hi: false },
  woodfloor: { tile: [2.4, 1.14], p: [6, .018, 0, 0], normal: 4.0, hi: true },
  deck: { tile: [2.0, 1.12], p: [8, 0, 0, 0], normal: 3.0, hi: true },
  cobble: { tile: [1.2, 1.2], p: [10, 8, .0075, 0], normal: 6.0, hi: true },
  paver: { tile: [2.4, 2.4], p: [4, 4, .0035, 0], normal: 3.0, hi: true },
  pebbles: { tile: [.9, .9], p: [22, 0, 0, 0], normal: 5.0, hi: true },
  gravel: { tile: [.8, .8], p: [48, 0, 0, 0], normal: 5.0, hi: true },
  grass: { tile: [2.4, 2.4], p: [0, 0, 0, 0], normal: 2.0, hi: true },
  soil: { tile: [1.2, 1.2], p: [34, 0, 0, 0], normal: 4.0, hi: false },
  asphalt: { tile: [3.0, 3.0], p: [0, 0, 0, 0], normal: 3.0, hi: true },
  encaustic: { tile: [.8, .8], p: [4, 0, 0, 0], normal: 1.2, hi: true },
  fabric: { tile: [.35, .35], p: [120, 0, 0, 0], normal: 1.4, hi: false },
  rug: { tile: [1.2, 1.2], p: [0, 0, 0, 0], normal: 2.0, hi: false },
  metal: { tile: [1.0, 1.0], p: [.42, 0, 0, 0], normal: .25, hi: false },
  brushed: { tile: [.6, .6], p: [.28, 0, 0, 0], normal: .3, hi: false },
  stoneclad: { tile: [1.2, 1.2], p: [9, 0, 0, 0], normal: 7.0, hi: true },
  leather: { tile: [.5, .5], p: [0, 0, 0, 0], normal: 1.2, hi: false },
  art: { tile: [1.0, 1.0], p: [0, 0, 0, 0], normal: .3, hi: false },
  bark: { tile: [.6, 1.2], p: [.8, 0, 0, 0], normal: 4.0, hi: false },
};

export class TextureSynth {
  constructor(renderer, { quality = 'high' } = {}) {
    this.renderer = renderer;
    this.quality = quality;
    this.targets = [];
    this.owners = new Map(); // texture -> render target, for CPU read-back (presentation export)
    this.cache = new Map();
    this.programs = new Map();
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
    this.quad = new THREE.Mesh(geo, null);
    this.quad.frustumCulled = false;
    this.scene = new THREE.Scene();
    this.scene.add(this.quad);
    this.anisotropy = Math.min(16, renderer.capabilities.getMaxAnisotropy());
  }

  material(kind) {
    if (!this.programs.has(kind)) {
      const src = KINDS[kind];
      if (!src) throw Error('Unknown texture kind ' + kind);
      this.programs.set(kind, new THREE.ShaderMaterial({
        vertexShader: VERT,
        fragmentShader: COMMON + src + FRAG_MAIN,
        uniforms: {
          uBase: { value: new THREE.Color() }, uAlt: { value: new THREE.Color() }, uP: { value: new THREE.Vector4() },
          uSeed: { value: 0 }, uMode: { value: 0 }, uNormal: { value: 1 }, uTexel: { value: 1 / 512 },
        },
        depthTest: false, depthWrite: false,
      }));
    }
    return this.programs.get(kind);
  }

  size(kind) {
    const hi = KIND_DEFAULTS[kind]?.hi;
    if (this.quality === 'performance') return hi ? 512 : 256;
    if (this.quality === 'balanced') return hi ? 1024 : 512;
    return hi ? 1024 : 512;
  }

  target(size, srgb) {
    const rt = new THREE.WebGLRenderTarget(size, size, {
      type: THREE.UnsignedByteType, format: THREE.RGBAFormat, depthBuffer: false, stencilBuffer: false,
      generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter,
      wrapS: THREE.RepeatWrapping, wrapT: THREE.RepeatWrapping, colorSpace: srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace,
      anisotropy: this.anisotropy,
    });
    this.targets.push(rt);
    this.owners.set(rt.texture, rt);
    return rt;
  }

  // The render target a synthesised texture lives in (null for other textures).
  owner(texture) { return this.owners.get(texture) || null; }

  // Returns {map, normalMap, roughnessMap}. Colours are sRGB hex strings.
  make(kind, { base = '#ffffff', alt = null, params = null, seed = 0, normal = null } = {}) {
    const def = KIND_DEFAULTS[kind];
    const key = JSON.stringify([kind, base, alt, params, seed, normal]);
    if (this.cache.has(key)) return this.cache.get(key);
    const mat = this.material(kind);
    const size = this.size(kind);
    const u = mat.uniforms;
    u.uBase.value.set(base);
    u.uAlt.value.set(alt || base);
    const p = params || def.p;
    u.uP.value.set(p[0] ?? 0, p[1] ?? 0, p[2] ?? 0, p[3] ?? 0);
    u.uSeed.value = seed;
    u.uNormal.value = (normal ?? def.normal) * 0.12 * (size / 512);
    u.uTexel.value = 1 / size;
    this.quad.material = mat;
    const r = this.renderer;
    const prevTarget = r.getRenderTarget();
    const prevAutoClear = r.autoClear;
    const prevXR = r.xr.enabled; r.xr.enabled = false;
    const out = {};
    for (const [mode, name, srgb] of [[0, 'map', true], [1, 'normalMap', false], [2, 'roughnessMap', false]]) {
      const rt = this.target(size, srgb);
      u.uMode.value = mode;
      r.setRenderTarget(rt);
      r.autoClear = true;
      r.render(this.scene, this.camera);
      out[name] = rt.texture;
    }
    r.setRenderTarget(prevTarget);
    r.autoClear = prevAutoClear;
    r.xr.enabled = prevXR;
    this.cache.set(key, out);
    return out;
  }

  dispose() {
    for (const rt of this.targets) rt.dispose();
    for (const m of this.programs.values()) m.dispose();
    this.quad.geometry.dispose();
    this.targets = []; this.owners.clear(); this.cache.clear(); this.programs.clear();
  }
}
