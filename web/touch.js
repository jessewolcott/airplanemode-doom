"use strict";
// Touch controls for PrBoom+. They call the engine directly (am_key / am_mouse in
// engine/am_web.c) rather than faking keyboard events. Every ~100 ms the page asks the
// engine what's on screen (am_state) and swaps between play, menu and "tap to continue".
(() => {
  const $ = (s) => document.querySelector(s);
  const ui = $("#touch");
  const KEY = {
    up: 0xad, down: 0xaf, left: 0xac, right: 0xae, esc: 27, enter: 13, backspace: 127,
    map: 9, fire: 0x80 + 0x1d, use: 32, speed: 0x80 + 0x36,
    nextweapon: 0x80 + 0x6b, prevweapon: 0x80 + 0x6c,
    forward: 119 /* w */, back: 115 /* s */, strafeleft: 97 /* a */, straferight: 100 /* d */,
    y: 121, n: 110,
  };
  const engine = () => window.Module && Module._am_key ? Module : null;
  const held = new Map();   // key code -> count of fingers holding it

  function press(code) {
    const n = held.get(code) || 0;
    held.set(code, n + 1);
    if (!n && engine()) Module._am_key(1, code);
  }
  function release(code) {
    const n = held.get(code) || 0;
    if (n <= 1) { held.delete(code); if (engine()) Module._am_key(0, code); } else held.set(code, n - 1);
  }
  function releaseAll() {
    for (const code of held.keys()) if (engine()) Module._am_key(0, code);
    held.clear();
    stickKeys.clear();
    $("#stick").classList.remove("on");
    document.querySelectorAll(".btn.on").forEach((b) => b.classList.remove("on"));
    fingers.clear();
  }
  function tap(code) { press(code); setTimeout(() => release(code), 80); }

  // ---------------------------------------------------------- fingers
  // id -> { kind: "stick" | "look" | "button", ... }
  const fingers = new Map();
  const stick = $("#stick"), knob = stick.querySelector("i");
  const stickKeys = new Set();
  const RADIUS = 56;

  function setStickKeys(want) {
    for (const k of stickKeys) if (!want.has(k)) { release(k); stickKeys.delete(k); }
    for (const k of want) if (!stickKeys.has(k)) { press(k); stickKeys.add(k); }
  }

  function stickMove(f, x, y) {
    let dx = x - f.x0, dy = y - f.y0;
    const d = Math.hypot(dx, dy);
    if (d > RADIUS) {
      // drag the stick along so reversing direction is quick
      f.x0 = x - (dx / d) * RADIUS; f.y0 = y - (dy / d) * RADIUS;
      stick.style.left = f.x0 + "px"; stick.style.top = f.y0 + "px";
      dx = x - f.x0; dy = y - f.y0;
    }
    knob.style.transform = `translate(${dx}px, ${dy}px)`;
    const nx = dx / RADIUS, ny = dy / RADIUS, mag = Math.min(1, Math.hypot(nx, ny));
    const want = new Set();
    if (ny < -0.3) want.add(KEY.forward);
    if (ny > 0.3) want.add(KEY.back);
    if (nx < -0.38) want.add(KEY.strafeleft);
    if (nx > 0.38) want.add(KEY.straferight);
    // autorun is on: holding "speed" walks instead, for small pushes
    if (want.size && mag < 0.7) want.add(KEY.speed);
    setStickKeys(want);
  }

  let turnRest = 0;
  function look(f, x) {
    const dx = (x - f.lx) * settingsSens() + turnRest;
    f.lx = x;
    const whole = Math.trunc(dx);
    turnRest = dx - whole;
    if (whole && engine()) Module._am_mouse(whole, 0);
  }
  const settingsSens = () => {
    const el = document.querySelector("#sens");
    // PrBoom+ turns 1/65536 of a circle per mouse unit: at the default (8) a 300 px swipe
    // is about 160 degrees
    return (el ? +el.value : 8) * 12;
  };

  function onStart(e) {
    if (!ui.classList.contains("play") && !ui.classList.contains("menu")) {
      if (ui.classList.contains("skip")) tap(KEY.enter);
      e.preventDefault();
      return;
    }
    for (const t of e.changedTouches) {
      const target = document.elementFromPoint(t.clientX, t.clientY);
      const btn = target && target.closest(".btn");
      if (btn && btn.offsetParent !== null) {
        const code = KEY[btn.dataset.key];
        if (code === undefined) continue;
        press(code);
        btn.classList.add("on");
        if (btn.dataset.key === "fire" && navigator.vibrate) navigator.vibrate(8);
        fingers.set(t.identifier, { kind: "button", code, btn, lx: t.clientX, look: !!btn.dataset.look });
      } else if (target && target.closest("#move")) {
        fingers.set(t.identifier, { kind: "stick", x0: t.clientX, y0: t.clientY });
        stick.style.left = t.clientX + "px"; stick.style.top = t.clientY + "px";
        knob.style.transform = "";
        stick.classList.add("on");
      } else if (target && target.closest("#look")) {
        fingers.set(t.identifier, { kind: "look", lx: t.clientX });
      }
    }
    e.preventDefault();
  }

  function onMove(e) {
    for (const t of e.changedTouches) {
      const f = fingers.get(t.identifier);
      if (!f) continue;
      if (f.kind === "stick") stickMove(f, t.clientX, t.clientY);
      else if (f.kind === "look" || f.look) look(f, t.clientX);
    }
    e.preventDefault();
  }

  function onEnd(e) {
    for (const t of e.changedTouches) {
      const f = fingers.get(t.identifier);
      if (!f) continue;
      fingers.delete(t.identifier);
      if (f.kind === "button") { release(f.code); f.btn.classList.remove("on"); }
      if (f.kind === "stick") { setStickKeys(new Set()); stick.classList.remove("on"); }
    }
    e.preventDefault();
  }

  ui.addEventListener("touchstart", onStart, { passive: false });
  ui.addEventListener("touchmove", onMove, { passive: false });
  ui.addEventListener("touchend", onEnd, { passive: false });
  ui.addEventListener("touchcancel", onEnd, { passive: false });
  ui.addEventListener("contextmenu", (e) => e.preventDefault());

  // ---------------------------------------------------------- mode switching
  let mode = "";
  function poll() {
    if (!engine() || !Module._am_state) return;
    let s;
    try { s = Module._am_state(); } catch { return; }
    const next = s & 3 ? "menu" : s & 8 ? "play" : "skip";
    if (next !== mode) {
      releaseAll();
      ui.classList.remove("menu", "play", "skip");
      ui.classList.add(next);
      mode = next;
    }
    ui.classList.toggle("question", !!(s & 2));
  }

  function enableTouch() {
    ui.hidden = false;
    ui.classList.toggle("lefty", !!(document.querySelector("#lefty") || {}).checked);
  }

  window.addEventListener("doom-started", () => {
    const coarse = window.matchMedia && matchMedia("(pointer: coarse)").matches;
    if (coarse || navigator.maxTouchPoints > 0) enableTouch();
    // a touch on a laptop with a touchscreen turns the controls on too
    $("#game").addEventListener("touchstart", enableTouch, { once: true, passive: true });
    setInterval(poll, 100);
  });
  window.addEventListener("blur", releaseAll);
})();
