// Camera framing for a fixed viewing direction: the closest camera from which a box's eight corners fill a window of
// the frame. A corner at lateral offset d and depth z projects inside [lo, hi] (NDC) when lo·t·z <= d <= hi·t·z, so
// every frame edge bounds the camera by a plane; per screen axis the furthest-forward camera is the maximum of a
// concave piecewise-linear function of its lateral position. It is solved exactly (ternary search), and the axis
// with room to spare is then centred. Plain arrays and no dependencies, so it runs and is tested outside a browser.

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unit = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

/**
 * @param {number[]} min  box corner (world, lowest x, y, z)
 * @param {number[]} max  box corner (world, highest x, y, z)
 * @param {number[]} forward  viewing direction (world)
 * @param {object} options  fov (vertical, degrees), aspect (width / height), fill (share of the window the box
 *   spans on its limiting axis), window ([left, right, bottom, top] in NDC; [-1, 1, -1, 1] is the whole frame),
 *   up (world up), minReach (least distance from the camera to the target)
 * @returns {{position: number[], target: number[]}}  camera position and an orbit target on its line of sight
 */
export function frameBox(min, max, forward, { fov = 43, aspect = 1, fill = .9, window = [-1, 1, -1, 1], up = [0, 1, 0], minReach = 1.5 } = {}) {
  const F = unit(forward), R = unit(cross(F, up)), U = cross(R, F);
  const tv = Math.tan(fov * Math.PI / 360), th = tv * aspect;
  const shrink = (lo, hi) => { const c = (lo + hi) / 2, r = (hi - lo) / 2 * fill; return [Math.min(c - r, -.05), Math.max(c + r, .05)]; };
  const [xl, xh] = shrink(window[0], window[1]), [yl, yh] = shrink(window[2], window[3]);
  const pts = [];
  for (let i = 0; i < 8; i++) {
    const p = [i & 1 ? max[0] : min[0], i & 2 ? max[1] : min[1], i & 4 ? max[2] : min[2]];
    pts.push({ r: dot(p, R), u: dot(p, U), f: dot(p, F) });
  }
  // g(c): the furthest forward the camera may stand with lateral coordinate c on this axis.
  const axis = (key, lo, hi, t) => {
    const g = (c) => { let m = Infinity; for (const p of pts) { const d = p[key] - c; m = Math.min(m, p.f - Math.max(d / (hi * t), d / (lo * t))); } return m; };
    let a = Math.min(...pts.map((p) => p[key])), b = Math.max(...pts.map((p) => p[key]));
    const span = b - a + 1;
    for (let k = 0; k < 100; k++) { const m1 = a + (b - a) / 3, m2 = b - (b - a) / 3; if (g(m1) < g(m2)) a = m1; else b = m2; }
    return { best: (a + b) / 2, g, span };
  };
  const X = axis('r', xl, xh, th), Y = axis('u', yl, yh, tv);
  const depth = Math.min(X.g(X.best), Y.g(Y.best), Math.min(...pts.map((p) => p.f)) - .5);
  // The middle of the lateral range over which the fit still holds (a single point on the limiting axis).
  const centre = (A) => {
    if (A.g(A.best) <= depth + 1e-9) return A.best;
    const edge = (dir) => {
      let inside = A.best, step = A.span, out = A.best + dir * step;
      while (A.g(out) >= depth) { inside = out; step *= 2; out = A.best + dir * step; }
      for (let k = 0; k < 60; k++) { const m = (inside + out) / 2; if (A.g(m) >= depth) inside = m; else out = m; }
      return inside;
    };
    return (edge(-1) + edge(1)) / 2;
  };
  const cr = centre(X), cu = centre(Y);
  const position = [0, 1, 2].map((i) => R[i] * cr + U[i] * cu + F[i] * depth);
  const mid = [0, 1, 2].map((i) => (min[i] + max[i]) / 2);
  const reach = Math.max(minReach, dot(mid, F) - depth);
  return { position, target: position.map((x, i) => x + F[i] * reach) };
}

// NDC of a world point seen by a camera at `position` looking at `target` (the inverse check used by the tests).
export function project(point, position, target, { fov = 43, aspect = 1, up = [0, 1, 0] } = {}) {
  const F = unit([target[0] - position[0], target[1] - position[1], target[2] - position[2]]), R = unit(cross(F, up)), U = cross(R, F);
  const d = [point[0] - position[0], point[1] - position[1], point[2] - position[2]];
  const tv = Math.tan(fov * Math.PI / 360), z = dot(d, F);
  return [dot(d, R) / (z * tv * aspect), dot(d, U) / (z * tv), z];
}
