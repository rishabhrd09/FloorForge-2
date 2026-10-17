// Smooth scrolling without a library: the page scrolls natively (scrollbars, keys, touch and assistive tech all
// work), and the walkthrough follows a critically damped copy of the position so the camera glides between steps.
export class SmoothScroll {
  constructor({ reduced = false } = {}) {
    this.reduced = reduced;
    this.value = this.target();
    this.velocity = 0;
  }

  target() {
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    return Math.min(1, Math.max(0, scrollY / max));
  }

  // Advance by dt seconds; returns the smoothed progress 0..1 and whether it is still moving.
  step(dt) {
    const goal = this.target();
    if (this.reduced) { const moved = Math.abs(goal - this.value) > 1e-6; this.value = goal; return { value: goal, moving: moved }; }
    const w = 7.5, x = this.value - goal;
    // Critically damped spring: no overshoot, no drift.
    const a = -w * w * x - 2 * w * this.velocity;
    this.velocity += a * dt;
    this.value += this.velocity * dt;
    if (Math.abs(this.value - goal) < 2e-6 && Math.abs(this.velocity) < 1e-5) { this.value = goal; this.velocity = 0; }
    return { value: this.value, moving: Math.abs(this.value - goal) > 1e-5 || Math.abs(this.velocity) > 1e-5 };
  }

  jump(progress, smooth = true) {
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    scrollTo({ top: progress * max, behavior: smooth && !this.reduced ? 'smooth' : 'auto' });
  }
}
