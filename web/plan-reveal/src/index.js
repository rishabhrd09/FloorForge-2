/* FloorForge Plan Reveal: a scroll-driven walkthrough that opens on the house's own drawing.
   The data (the generated scene and the walk computed by floorforge/plan_reveal.py) is packaged beside this file as
   reveal-data.js, so the page works from disk with no network. */
import * as THREE from 'three';
import { RevealViewer } from './reveal-viewer.js';
import { Drawing } from './drawing.js';
import { RevealMask } from './mask.js';
import { Director } from './director.js';
import { Hud } from './hud.js';
import { SmoothScroll } from './scroll.js';

const $ = (id) => document.getElementById(id);
const PAPER = '#efebe2', INK = '#1e1e1b', ACCENT = '#d9622b';
const vec = (hex) => { const c = new THREE.Color(hex); return new THREE.Vector3(c.r, c.g, c.b); };
const progress = (p) => document.querySelector('#loader i')?.style.setProperty('--p', String(p));

async function boot() {
  const packaged = window.__PLAN_REVEAL__;
  if (!packaged) throw Error('reveal-data.js is missing.');
  const { scene, reveal: data } = packaged;
  delete window.__PLAN_REVEAL__;
  if (scene.planHash !== data.planHash) throw Error('The walkthrough does not match this house.');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  progress(.15);
  await Promise.race([document.fonts?.ready, new Promise((r) => setTimeout(r, 1500))]);
  await new Promise((r) => requestAnimationFrame(r));
  const canvas = $('stage');
  const viewer = new RevealViewer(canvas, { quality: 'auto', onStatus: () => {} });
  progress(.3);
  viewer.setScene(scene);
  viewer.setGrade(data.grade || 'golden');
  viewer.fitHeld = null; viewer.zoomAnim = null;
  progress(.7);
  const fx = viewer.reveal;
  fx.set('uPaper', vec(PAPER)); fx.set('uInk', vec(INK)); fx.set('uAccent', vec(ACCENT));
  fx.set('uFloorH', data.floorHeight);
  viewer.drawing = new Drawing(data);
  viewer.mask = new RevealMask(viewer.renderer, data);
  fx.set('tMask', viewer.mask.target.texture);
  fx.get('uMaskBox').copy(viewer.mask.box);
  fx.get('uMaskTexel').set(1 / viewer.mask.target.width, 1 / viewer.mask.target.height);
  const px = data.plot.map((q) => q[0]), py = data.plot.map((q) => q[1]);
  fx.get('uSite').set(Math.min(...px) - .6, Math.min(...py) - .6, Math.max(...px) + .6, Math.max(...py) + .6);
  const hud = new Hud(data, { onJump: (n) => jump(n) });
  const director = new Director({ viewer, mask: viewer.mask, drawing: viewer.drawing, data, scene, hud, reduced });
  const h = director.house;
  fx.get('uFocus').set((h.x0 + h.x1) / 2, -(h.y0 + h.y1) / 2, Math.hypot(h.x1 - h.x0, h.y1 - h.y0) * .75 + 3, 0);
  const spacer = $('scroll');
  const size = () => { spacer.style.height = `${(director.total + 1) * innerHeight}px`; };
  size();
  addEventListener('resize', size);
  const scroll = new SmoothScroll({ reduced });
  function jump(n) {
    if (n < 0) { scroll.jump(0); return; }
    const at = n === 0 ? director.startOf('dwell', 0) : director.startOf('dwell', n);
    scroll.jump((at + .35) / director.total);
  }
  let last = null;
  viewer.onFrame = (dt) => {
    const { value, moving } = scroll.step(dt);
    const p = value * director.total;
    const s = director.update(p);
    s.p = p;
    viewer.cut(s.cut);
    viewer.planLight(s.planLight || 0);
    viewer.sinkContext(s.context || 0);
    fx.set('uPoche', s.poche || 0);
    fx.set('uClip', s.clip || 0);
    fx.set('uSiteFade', s.site || 0);
    fx.get('uFrame').fromArray(hud.frameRect());
    viewer.drawing.setFloor(s.floor || 0);
    viewer.drawing.setCut(s.cut, data.floorHeight);
    viewer.drawing.setInk(s.sheetInk, s.labelInk);
    viewer.mode = s.indoor ? 'walk' : 'solid';
    hud.update(s, director);
    const changed = moving || !last || last.chapter !== s.chapter;
    last = s;
    return changed || viewer.mask.dirty;
  };
  window.__planReveal = { viewer, director, data, scroll, state: () => last, ready: false, frames: () => viewer.frames,
    goto: (p) => { scroll.value = p / director.total; scroll.velocity = 0; viewer.dirty = true; },
    // Automation: settle at progress p, render that one frame and hold it (for screenshots), or resume.
    still: (p) => {
      viewer.paused = false;
      scroll.value = p / director.total; scroll.velocity = 0;
      const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
      scrollTo(0, p / director.total * max);
      viewer.lastTick = performance.now() - 16;
      for (let i = 0; i < 3; i++) { viewer.dirty = true; viewer.tick(); viewer.lastTick = performance.now() - 300; }
      viewer.paused = true;
      return last && { chapter: last.chapter, stop: last.stop, cut: last.cut, fov: viewer.camera.fov };
    },
    resume: () => { viewer.paused = false; } };
  await new Promise((r) => setTimeout(r, 60));
  progress(1);
  const ready = () => { $('loader').classList.add('done'); window.__planReveal.ready = true; };
  let frames = 0;
  const wait = () => { if (viewer.frames > 2 || ++frames > 240) ready(); else requestAnimationFrame(wait); };
  requestAnimationFrame(wait);
}

boot().catch((e) => {
  console.error(e);
  $('loader')?.classList.add('done');
  $('fail')?.classList.add('on');
  window.__planReveal = { ready: false, error: String(e?.message || e) };
});
