/* reel-edit-engine — deterministic, seek(t)-driven helpers for editing a talking-head clip into a
 * styled 1080x1920 reel. Everything is a pure function of t so render.mjs can jump to any frame.
 *
 * Page contract:
 *   window.FOOTAGE = { dir: "footage", fps: 30, count: 660, cut: "cutout" | null }
 *   window.seek = async t => { await R.footage(t); R.frame(t); ...scenes... }
 *   window.REEL_DURATION = <seconds>
 * Call helpers UNCONDITIONALLY every seek (not inside if-blocks): they register SFX cues
 * (pop, whoosh, type, click, ding) that render.mjs --cues exports for sfx.py.
 */
(function () {
  const R = (window.Reel = {});
  const clamp = (R.clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x)));
  const prog = (R.prog = (t, a, d) => clamp((t - a) / d));
  const lerp = (R.lerp = (a, b, p) => a + (b - a) * p);
  const E = (R.ease = {
    out3: p => 1 - Math.pow(1 - p, 3),
    out5: p => 1 - Math.pow(1 - p, 5),
    inOut: p => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    back: p => { const c = 1.6; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
    spring: p => (p >= 1 ? 1 : 1 - Math.exp(-6 * p) * Math.cos(9 * p)),
  });
  const $ = (R.$ = id => (typeof id === "string" ? document.getElementById(id) : id));

  // ---------- sound cues ----------
  const seen = new Set();
  R.cues = window.__cues = [];
  R.cue = (type, t, extra = {}) => {
    const k = type + ":" + (+t).toFixed(3);
    if (seen.has(k)) return;
    seen.add(k); R.cues.push({ type, t: +t, ...extra });
  };

  // ---------- footage ----------
  const pad = n => String(n).padStart(5, "0");
  const loaded = new Map();
  function load(src) {
    if (!loaded.has(src)) loaded.set(src, new Promise(res => { const im = new Image(); im.onload = () => res(im); im.onerror = () => res(null); im.src = src; }));
    return loaded.get(src);
  }
  /** show the footage frame for time t (and the cutout frame if the page has #cut). Await it. */
  R.footage = async (t, o = {}) => {
    const F = window.FOOTAGE; if (!F) return;
    const i = clamp(Math.round(t * F.fps), 0, F.count - 1);
    const fr = $("frame"), cut = $("cut");
    const jobs = [];
    if (fr) jobs.push(load(`${F.dir}/${pad(i)}.jpg`).then(im => { if (im) fr.src = im.src; }));
    if (cut && F.cut) jobs.push(load(`${F.cut}/${pad(i)}.png`).then(im => { if (im) cut.src = im.src; }));
    await Promise.all(jobs);
  };
  /** punch-in zoom on the footage: zooms = [[start, end, scale, originX%, originY%]] */
  R.zoom = (el, t, zooms, o = {}) => {
    el = $(el); let s = 1, ox = 50, oy = 40;
    for (const [a, b, z, x = 50, y = 40] of zooms) {
      const pin = E.out5(prog(t, a, o.d ?? 0.18)), pout = E.out3(prog(t, b, o.d ?? 0.18));
      if (t >= a) { s = lerp(1, z, pin) * (1 - pout) + pout * 1; ox = x; oy = y; if (pin > 0 && pin < 1 && o.sfx !== false) R.cue("click", a); }
    }
    const drift = 1 + (o.drift || 0) * prog(t, 0, o.driftOver ?? 30); // slow creep, e.g. drift:0.04
    el.style.transformOrigin = `${ox}% ${oy}%`;
    el.style.transform = `scale(${s * drift})`;
    return s;
  };
  /** keyframed box: keys = [{t, x, y, w, h, r?, o?}] (px / radius / opacity). Eases between keys. */
  R.rect = (el, t, keys, o = {}) => {
    // hold keys[j] until keys[j+1].t, then ease to it over keys[j+1].d seconds
    el = $(el); let j = 0;
    for (let i = 0; i < keys.length; i++) if (t >= keys[i].t) j = i;
    let k0 = keys[Math.max(0, j - 1)], k1 = keys[j], p = 1;
    if (j > 0) p = (o.ease || E.inOut)(prog(t, k1.t, Math.max(0.001, k1.d ?? 0.6)));
    else k0 = k1;
    const v = key => lerp(k0[key] ?? 0, k1[key] ?? k0[key] ?? 0, p);
    el.style.left = v("x") + "px"; el.style.top = v("y") + "px"; el.style.width = v("w") + "px"; el.style.height = v("h") + "px";
    el.style.borderRadius = v("r") + "px"; el.style.opacity = k0.o == null && k1.o == null ? 1 : lerp(k0.o ?? 1, k1.o ?? 1, p);
  };

  // ---------- element helpers ----------
  R.rise = (el, t, a, o = {}) => {
    el = $(el); const d = o.d ?? 0.5, dy = o.dy ?? 50, blur = o.blur ?? 0;
    const p = E.out3(prog(t, a, d)), pout = o.until != null ? E.out3(prog(t, o.until, 0.3)) : 0;
    el.style.opacity = p * (1 - pout);
    el.style.transform = `translateY(${(1 - p) * dy - pout * 30}px)` + (o.extra || "");
    el.style.filter = blur ? `blur(${((1 - p) + pout) * blur}px)` : "";
    return p;
  };
  R.pop = (el, t, a, o = {}) => {
    el = $(el); const d = o.d ?? 0.5, rot = o.rot ?? 0;
    if (o.sfx !== false) R.cue("pop", a);
    const p = prog(t, a, d), pout = o.until != null ? E.out3(prog(t, o.until, 0.25)) : 0;
    el.style.opacity = clamp(p * 3) * (1 - pout);
    el.style.transform = `scale(${lerp(o.from ?? 0.4, 1, E.spring(p)) * (1 - 0.1 * pout)}) rotate(${rot * E.out3(p)}deg)`;
    return p;
  };
  R.punch = (el, t, a, amt = 0.07, d = 0.35) => {
    el = $(el); const s = 1 + amt * Math.sin(Math.PI * prog(t, a, d));
    el.style.transform = (el.style.transform || "").replace(/ ?scale\([^)]*\) ?$/, "") + ` scale(${s})`;
  };
  /** kinetic text: split into words once; reveal with stagger or exact times[] */
  R.words = (el, t, a, o = {}) => {
    el = $(el);
    if (!el.dataset.split) {
      const out = [];
      el.childNodes.forEach(n => {
        if (n.nodeType === 3) n.textContent.split(/(\s+)/).forEach(w => out.push(/\S/.test(w) ? `<span class="w">${w}</span>` : w));
        else if (n.nodeName === "BR") out.push("<br>");
        else { n.classList.add("w"); out.push(n.outerHTML); }
      });
      el.innerHTML = out.join(""); el.dataset.split = 1;
    }
    const ws = el.querySelectorAll(".w"), st = o.stagger ?? 0.09, d = o.d ?? 0.45;
    const pout = o.until != null ? E.out3(prog(t, o.until, 0.3)) : 0;
    el.style.opacity = 1 - pout;
    ws.forEach((w, i) => {
      const at = o.times ? o.times[Math.min(i, o.times.length - 1)] : a + i * st;
      const p = prog(t, at, d), e = E.out3(p);
      w.style.display = "inline-block";
      w.style.opacity = clamp(p * 1.6);
      w.style.transform = `translateY(${(1 - e) * (o.dy ?? 60)}px) rotate(${(1 - e) * 3}deg)`;
      w.style.filter = `blur(${(1 - e) * 10}px)`;
    });
  };
  R.marker = (el, t, a, d = 0.45, color = "rgba(232,132,42,.35)") => {
    el = $(el); const p = E.inOut(prog(t, a, d));
    el.style.backgroundImage = `linear-gradient(transparent 55%, ${color} 55%, ${color} 92%, transparent 92%)`;
    el.style.backgroundRepeat = "no-repeat"; el.style.backgroundSize = `${p * 100}% 100%`;
  };
  R.type = (el, text, t, a, cps = 32) => {
    el = $(el); R.cue("type", a, { t2: a + text.length / cps });
    const n = clamp(Math.floor((t - a) * cps), 0, text.length);
    el.textContent = text.slice(0, n); return n >= text.length;
  };
  R.count = (el, t, a, d, to, o = {}) => {
    el = $(el); const fmt = o.fmt || (x => Math.round(x).toLocaleString("en-US"));
    if (o.ding) R.cue("ding", a + d);
    el.textContent = fmt((o.from ?? 0) + (to - (o.from ?? 0)) * E.out3(prog(t, a, d)));
  };
  R.draw = (el, t, a, d) => {
    el = $(el);
    if (!el.dataset.len) { el.dataset.len = el.getTotalLength(); el.style.strokeDasharray = el.dataset.len; }
    el.style.strokeDashoffset = el.dataset.len * (1 - E.inOut(prog(t, a, d)));
  };
  R.wipe = (el, t, a, d, dir = "right") => {
    el = $(el); const r = (1 - E.inOut(prog(t, a, d))) * 100;
    const m = { right: `0 ${r}% 0 0`, left: `0 0 0 ${r}%`, down: `0 0 ${r}% 0`, up: `${r}% 0 0 0` };
    el.style.clipPath = `inset(${m[dir]})`;
  };
  R.camera = (el, t, a, d, from, to) => {
    el = $(el); const p = E.inOut(prog(t, a, d));
    const x = lerp(from.x || 0, to.x || 0, p), y = lerp(from.y || 0, to.y || 0, p), s = lerp(from.s || 1, to.s || 1, p);
    el.style.transformOrigin = "0 0"; el.style.transform = `translate(${x}px, ${y}px) scale(${s})`;
  };
  /** dot-matrix "loading" reveal (Ajené-style): fills el with dots that light up randomly until a */
  R.dots = (el, t, a, d = 0.9, o = {}) => {
    el = $(el); const cols = o.cols ?? 24, rows = o.rows ?? 42;
    if (!el.dataset.built) {
      let h = ""; for (let i = 0; i < cols * rows; i++) { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; h += `<i style="--k:${(x - Math.floor(x)).toFixed(3)}"></i>`; }
      el.innerHTML = h; el.style.gridTemplateColumns = `repeat(${cols},1fr)`; el.dataset.built = 1;
    }
    const p = prog(t, a - d, d), fade = prog(t, a, 0.35);
    el.style.opacity = (1 - fade) * (o.max ?? 1);
    el.querySelectorAll("i").forEach(i => { const k = +i.style.getPropertyValue("--k"); i.style.opacity = k < p ? 0.9 : 0.12; });
  };

  // ---------- voice-synced timing ----------
  const nrm = s => s.toLowerCase().replace(/[^\w]/g, "");
  let TOK = null;
  const tokens = () => (TOK ||= (window.CAPTION_PAGES || []).flat());
  function find(phrase, nth = 0) {
    const q = nrm(phrase), T = tokens();
    for (let i = 0, hit = 0; i < T.length; i++) {
      let acc = "";
      for (let j = i; j < T.length && acc.length < q.length; j++) {
        acc += nrm(T[j].t);
        if (acc === q && hit++ === nth) return [T[i], T[j]];
      }
    }
    throw new Error(`Reel.at: phrase not found in captions: "${phrase}"`);
  }
  R.at = (phrase, nth = 0) => find(phrase, nth)[0].s;
  R.end = (phrase, nth = 0) => find(phrase, nth)[1].e;
  R.voiceEnd = () => { const T = tokens(); return T.length ? T[T.length - 1].e : 0; };

  // ---------- frame-level systems ----------
  let C = null;
  /** cfg: {scenes:[{id,s,e,enter}], captions:{top, style:'chest'|'headline'|'none', max}} */
  R.setup = cfg => {
    C = cfg;
    (cfg.scenes || []).forEach(sc => { if (sc.s > 0 && sc.whoosh !== false) R.cue("whoosh", sc.s); });
    const cap = $("cap"); if (cap && cfg.captions && cfg.captions.top != null) cap.style.top = cfg.captions.top + "px";
  };
  function scenes(t) {
    let cur = null;
    for (const sc of C.scenes || []) {
      const el = $(sc.id); if (!el) continue;
      const pin = sc.s === 0 ? 1 : E.out3(prog(t, sc.s - 0.06, sc.din ?? 0.42));
      const pout = prog(t, sc.e - 0.22, 0.28);
      const a = pin * (1 - pout);
      el.style.display = a <= 0.001 ? "none" : "block";
      if (a <= 0.001) continue;
      if (t >= sc.s && t < sc.e) cur = sc.id;
      let tf = "", blur = (1 - pin) * 8 + pout * 8;
      switch (sc.enter || "up") {
        case "zoom": tf = `scale(${lerp(1.12, 1, pin)})`; break;
        case "left": tf = `translateX(${(1 - pin) * 140}px)`; break;
        case "fade": blur = pout * 6; break;
        case "blur": tf = `translateY(${(1 - pin) * 30}px) scale(${lerp(0.96, 1, pin)})`; blur = (1 - pin) * 18 + pout * 14; break;
        case "none": blur = 0; break;
        default: tf = `translateY(${(1 - pin) * 90}px)`;
      }
      tf += ` translateY(${-50 * E.out3(pout)}px)`;
      el.style.opacity = a; el.style.transform = tf; el.style.filter = blur > 0.05 ? `blur(${blur}px)` : "";
    }
    return cur;
  }
  /** chest captions: the current page, active word popped; `window.CAPTION_PAGES` from captions.py */
  function captions(t) {
    const el = $("cap"), P = window.CAPTION_PAGES || [];
    if (!el) return;
    if (C.captions && C.captions.style === "none") { el.innerHTML = ""; return; }
    let page = null;
    for (let i = 0; i < P.length; i++) {
      const p = P[i], nx = P[i + 1];
      if (t >= p[0].s - 0.08 && t < Math.min(nx ? nx[0].s - 0.08 : 1e9, p[p.length - 1].e + 0.6)) { page = p; break; }
    }
    if (!page) { el.innerHTML = ""; return; }
    const hide = (C.captions && C.captions.hide || []).some(([a, b]) => t >= a && t < b);
    el.style.opacity = hide ? 0 : 1;
    el.innerHTML = page.map(w => {
      if (t >= w.s - 0.04 && t < w.e + 0.06) {
        const s = lerp(0.9, 1.06, E.spring(prog(t, w.s - 0.04, 0.25)));
        return `<span class="on" style="transform:scale(${s})">${w.t}</span>`;
      }
      return `<span style="opacity:${t >= w.e ? 1 : 0.45}">${w.t}</span>`;
    }).join(" ");
  }
  function grain(t) {
    const gr = $("grain"); if (gr) { const f = Math.floor(t * 30); gr.style.backgroundPosition = `${(f * 137) % 400}px ${(f * 263) % 400}px`; }
  }
  /** call right after R.footage in window.seek */
  R.frame = t => { grain(t); const cur = scenes(t); captions(t); return { scene: cur }; };
})();
