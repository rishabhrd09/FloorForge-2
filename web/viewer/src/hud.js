// Minimal in-canvas walk overlay: click-to-walk prompt, key legend, crosshair, room/floor badge, touch controls.
const CSS = `
.ffhud{position:absolute;inset:0;pointer-events:none;font:500 12px/1.35 system-ui,-apple-system,Segoe UI,sans-serif;color:#fff;z-index:3}
.ffhud[hidden]{display:none}
.ffhud .ff-cross{position:absolute;left:50%;top:50%;width:6px;height:6px;margin:-3px 0 0 -3px;border-radius:50%;background:rgba(255,255,255,.85);box-shadow:0 0 0 1px rgba(0,0,0,.35)}
.ffhud .ff-where{position:absolute;left:16px;top:16px;padding:8px 12px;border-radius:8px;background:rgba(18,22,20,.46);backdrop-filter:blur(8px);letter-spacing:.02em}
.ffhud .ff-where b{display:block;font-size:14px;font-weight:650}
.ffhud .ff-where span{opacity:.8;font-size:11px;text-transform:uppercase;letter-spacing:.12em}
.ffhud .ff-start{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);pointer-events:auto;cursor:pointer;text-align:center;padding:18px 22px;border-radius:12px;background:rgba(18,22,20,.58);backdrop-filter:blur(10px);max-width:min(380px,86%)}
.ffhud .ff-start strong{display:block;font-size:16px;margin-bottom:10px}
.ffhud .ff-keys{display:grid;grid-template-columns:auto auto;gap:5px 14px;text-align:left;margin:0 auto;width:max-content}
.ffhud kbd{display:inline-block;min-width:18px;padding:2px 6px;border-radius:4px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.28);font:600 11px system-ui;text-align:center}
.ffhud.locked .ff-start{display:none}
.ffhud .ff-tip{position:absolute;right:16px;bottom:16px;padding:6px 10px;border-radius:6px;background:rgba(18,22,20,.4);font-size:11px;opacity:.85}
.ffhud .ff-touch{display:none}
@media (pointer:coarse){.ffhud .ff-touch{display:block}.ffhud .ff-start{top:32%}}
.ffhud .ff-stick{position:absolute;left:22px;bottom:22px;width:112px;height:112px;border-radius:50%;border:2px solid rgba(255,255,255,.45);background:rgba(255,255,255,.08)}
.ffhud .ff-jump{position:absolute;right:22px;bottom:30px;width:72px;height:72px;border-radius:50%;border:2px solid rgba(255,255,255,.55);background:rgba(255,255,255,.14);pointer-events:auto;color:#fff;font:600 12px system-ui}
`;

export class Hud {
  constructor(canvas, { onLock = () => {}, onJump = () => {}, inset = 16 } = {}) {
    this.canvas = canvas;
    const parent = canvas.parentElement;
    this.parent = parent;
    if (parent && getComputedStyle(parent).position === 'static') parent.style.position = 'relative';
    if (!document.getElementById('ffhud-style')) {
      const style = document.createElement('style');
      style.id = 'ffhud-style';
      style.textContent = CSS;
      document.head.appendChild(style);
    }
    const el = document.createElement('div');
    el.className = 'ffhud';
    el.hidden = true;
    el.innerHTML = `<div class="ff-cross"></div>
<div class="ff-where"><b>Arrival court</b><span>Ground floor</span></div>
<div class="ff-start" role="button" tabindex="0" aria-label="Start walking"><strong>Click to walk through your home</strong>
<div class="ff-keys"><span><kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd></span><span>move</span><span>Mouse</span><span>look around</span>
<span><kbd>Shift</kbd></span><span>run</span><span><kbd>Space</kbd></span><span>jump</span><span><kbd>C</kbd></span><span>crouch</span>
<span><kbd>Q</kbd> <kbd>E</kbd></span><span>turn</span><span>Scroll</span><span>lens width</span><span><kbd>Esc</kbd></span><span>release mouse</span></div></div>
<div class="ff-tip">Walk up the stairs to change floor</div>
<div class="ff-touch"><div class="ff-stick"></div><button class="ff-jump" type="button">Jump</button></div>`;
    parent?.appendChild(el);
    this.el = el;
    this.where = el.querySelector('.ff-where');
    this.where.style.top = inset + 'px';
    const start = el.querySelector('.ff-start');
    start.addEventListener('click', (e) => { e.preventDefault(); onLock(); canvas.focus?.(); });
    start.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onLock(); } });
    this.jumpButton = el.querySelector('.ff-jump');
    this.jumpButton.addEventListener('pointerdown', (e) => { e.preventDefault(); onJump(); });
    this.visible = false;
    this.last = '';
  }

  show(on) { this.visible = on; this.el.hidden = !on; if (!on) this.setLocked(false); }

  setLocked(on) { this.el.classList.toggle('locked', on); }

  setLocation(room, floor) {
    const text = room + '|' + floor;
    if (text === this.last) return;
    this.last = text;
    this.where.innerHTML = '';
    const b = document.createElement('b'); b.textContent = room;
    const s = document.createElement('span'); s.textContent = floor;
    this.where.append(b, s);
  }

  dispose() { this.el.remove(); }
}
