"use strict";
// AirplaneMode Doom: picks a game, downloads its WADs, starts PrBoom+ (WebAssembly).
// Everything runs in this browser; the box only serves files. Saves and settings live in
// IndexedDB (Emscripten's IDBFS) under /home/web_user/.prboom-plus.

const $ = (s) => document.querySelector(s);
const HOME = "/home/web_user/.prboom-plus";

const GAMES = [
  { id: "layover", name: "Layover", badge: "New", iwad: "freedoom2.wad", files: ["layover.wad"],
    desc: "Six levels made for AirplaneMode: from the curbside, through security and the concourse, under the baggage hall, across the tarmac and up the control tower." },
  { id: "freedoom2", name: "Freedoom: Phase 2", iwad: "freedoom2.wad", files: [],
    desc: "32 levels in one long campaign. Free, community-made game data." },
  { id: "freedoom1", name: "Freedoom: Phase 1", iwad: "freedoom1.wad", files: [],
    desc: "Four episodes of nine levels each. Free, community-made game data." },
];

// ---------------------------------------------------------------- settings
const store = {
  get(k, d) { try { const v = localStorage.getItem("amdoom." + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem("amdoom." + k, JSON.stringify(v)); } catch { /* private mode */ } },
};
const settings = {
  sens: store.get("sens", 8),
  res: store.get("res", 400),
  lefty: store.get("lefty", false),
};
function bindSettings() {
  const sens = $("#sens"), res = $("#res"), lefty = $("#lefty");
  sens.value = settings.sens; res.value = String(settings.res); lefty.checked = settings.lefty;
  sens.oninput = () => { settings.sens = +sens.value; store.set("sens", settings.sens); };
  res.onchange = () => { settings.res = +res.value; store.set("res", settings.res); };
  lefty.onchange = () => { settings.lefty = lefty.checked; store.set("lefty", settings.lefty); };
}

// ---------------------------------------------------------------- launcher
function card({ title, badge, desc, extra, onPlay, saved }) {
  const el = document.createElement("div");
  el.className = "card";
  const h = document.createElement("h3");
  h.textContent = title;
  if (badge) { const b = document.createElement("span"); b.className = "badge"; b.textContent = badge; h.append(b); }
  const p = document.createElement("p");
  p.textContent = desc;
  const row = document.createElement("div");
  row.className = "row";
  if (extra) row.append(extra);
  const btn = document.createElement("button");
  btn.className = "play";
  btn.textContent = "Play";
  btn.onclick = onPlay;
  row.append(btn);
  el.append(h, p, row);
  if (saved) { const s = document.createElement("span"); s.className = "saved"; s.textContent = saved; el.append(s); }
  return el;
}

function renderBundled() {
  const box = $("#games");
  box.replaceChildren(...GAMES.map((g) => card({
    title: g.name, badge: g.badge, desc: g.desc,
    onPlay: () => launch({ id: g.id, title: g.name, iwad: { url: "wads/" + g.iwad, name: g.iwad },
      files: g.files.map((f) => ({ url: "wads/" + f, name: f })) }),
  })));
}

// ---------------------------------------------------------------- Drop
// WAD files in Drop show up as games. We read just the header and directory (two small
// range requests) to tell an IWAD from a mod and which kind of maps it has.
const dropFile = (id) => "../drop/api/files/" + encodeURIComponent(id);

async function dropItems() {
  try {
    const r = await fetch("../drop/api/items", { cache: "no-store" });
    if (!r.ok) return null;
    const data = await r.json();
    return (data.items || []).filter((i) => i.kind === "file" && /\.wad$/i.test(i.name || ""));
  } catch { return null; }
}

async function rangeBytes(url, start, end) {
  const r = await fetch(url, { headers: { Range: `bytes=${start}-${end}` } });
  if (!r.ok) throw new Error(r.status === 403 ? "Drop has downloads turned off for this file." : "HTTP " + r.status);
  const buf = new Uint8Array(await r.arrayBuffer());
  // a server that ignores Range sends the whole file: slice what we asked for
  return r.status === 206 ? buf : buf.slice(start, end + 1);
}

function parseWadDirectory(header, dir) {
  const dv = new DataView(header.buffer, header.byteOffset);
  const kind = String.fromCharCode(...header.slice(0, 4));
  const names = [];
  for (let i = 0; i + 16 <= dir.length; i += 16) {
    let n = "";
    for (let j = 8; j < 16 && dir[i + j]; j++) n += String.fromCharCode(dir[i + j]);
    names.push(n.toUpperCase());
  }
  const maps = names.filter((n) => /^(E\dM\d|MAP\d\d)$/.test(n));
  return { kind, count: dv.getInt32(4, true), maps,
    format: maps.some((n) => n.startsWith("MAP")) ? "doom2" : maps.length ? "doom" : "any" };
}

async function inspectWad(item) {
  const url = dropFile(item.id);
  const header = await rangeBytes(url, 0, 11);
  const kind = String.fromCharCode(...header.slice(0, 4));
  if (kind !== "IWAD" && kind !== "PWAD") throw new Error("not a WAD file");
  const dv = new DataView(header.buffer, header.byteOffset);
  const count = dv.getInt32(4, true), offset = dv.getInt32(8, true);
  if (count < 0 || count > 65536 || offset < 12) throw new Error("damaged WAD");
  const dir = count ? await rangeBytes(url, offset, offset + count * 16 - 1) : new Uint8Array();
  return { ...parseWadDirectory(header, dir), item, url };
}

async function renderDrop() {
  const items = await dropItems();
  if (items === null) return;            // no Drop on this box
  $("#drop-hint").hidden = false;
  if (!items.length) return;
  const wads = [];
  for (const it of items) {
    try { wads.push(await inspectWad(it)); } catch (e) { wads.push({ error: e.message, item: it }); }
  }
  const iwads = wads.filter((w) => w.kind === "IWAD");
  const cards = [];
  for (const w of wads) {
    const name = w.item.name;
    if (w.error) {
      cards.push(card({ title: name, desc: "Can't use this one: " + w.error, onPlay: () => alert(w.error) }));
      continue;
    }
    if (w.kind === "IWAD") {
      cards.push(card({ title: name.replace(/\.wad$/i, ""), desc: `A full game (${w.maps.length} levels), from Drop.`,
        onPlay: () => launch({ id: "drop-" + safeId(name), title: name, iwad: { url: w.url, name: name.toLowerCase() }, files: [] }) }));
      continue;
    }
    // A mod: pick the game it goes on top of. Your own IWADs from Drop come first.
    const sel = document.createElement("select");
    const bases = [];
    for (const i of iwads) if (w.format === "any" || i.format === w.format) bases.push({ label: i.item.name + " (Drop)", url: i.url, name: i.item.name.toLowerCase() });
    if (w.format !== "doom") bases.push({ label: "Freedoom: Phase 2", url: "wads/freedoom2.wad", name: "freedoom2.wad" });
    if (w.format !== "doom2") bases.push({ label: "Freedoom: Phase 1", url: "wads/freedoom1.wad", name: "freedoom1.wad" });
    bases.forEach((b, i) => { const o = document.createElement("option"); o.value = i; o.textContent = "on " + b.label; sel.append(o); });
    cards.push(card({ title: name.replace(/\.wad$/i, ""), extra: sel,
      desc: `A mod${w.maps.length ? ` with ${w.maps.length} level${w.maps.length > 1 ? "s" : ""}` : ""}, from Drop.`,
      onPlay: () => { const b = bases[+sel.value]; launch({ id: "drop-" + safeId(name), title: name, iwad: b,
        files: [{ url: w.url, name: safeId(name) + ".wad" }] }); } }));
  }
  $("#drop-games").replaceChildren(...cards);
  $("#drop-section").hidden = false;
  return wads;
}

const safeId = (s) => s.toLowerCase().replace(/\.wad$/, "").replace(/[^a-z0-9]+/g, "-").slice(0, 40) || "wad";

// "Play in Doom" from Drop opens #drop=<item id>
async function openFromHash(wads) {
  const m = /^#drop=(.+)$/.exec(location.hash);
  if (!m) return;
  const id = decodeURIComponent(m[1]);
  history.replaceState(null, "", location.pathname);
  const w = (wads || []).find((x) => x.item && x.item.id === id);
  if (!w || w.error) { showError(w ? w.error : "That file isn't in Drop any more."); return; }
  const btn = [...document.querySelectorAll("#drop-games .card")]
    .find((c) => c.querySelector("h3").textContent === w.item.name.replace(/\.wad$/i, ""));
  // starting needs a tap (audio and fullscreen want one), so point at the card
  if (btn) { btn.scrollIntoView({ block: "center" }); btn.style.outline = "2px solid var(--accent)"; }
}

// ---------------------------------------------------------------- downloading
let manifest = {};
async function loadManifest() {
  try { manifest = await (await fetch("wads/manifest.json")).json(); } catch { manifest = {}; }
}

async function download(files, onProgress) {
  const totals = files.map((f) => manifest[f.url] || 0);
  const done = files.map(() => 0);
  const report = () => onProgress(done.reduce((a, b) => a + b, 0), totals.reduce((a, b) => a + b, 0));
  return Promise.all(files.map(async (f, i) => {
    const r = await fetch(f.url);
    if (!r.ok) throw new Error(`${f.name}: ${r.status === 403 ? "Drop has downloads turned off for it" : "HTTP " + r.status}`);
    if (!totals[i]) totals[i] = +r.headers.get("Content-Length") || 0;
    const reader = r.body.getReader();
    const parts = [];
    for (;;) {
      const { done: end, value } = await reader.read();
      if (end) break;
      parts.push(value);
      done[i] += value.length;
      if (done[i] > totals[i]) totals[i] = done[i];
      report();
    }
    const out = new Uint8Array(done[i]);
    let pos = 0;
    for (const p of parts) { out.set(p, pos); pos += p.length; }
    return { ...f, data: out };
  }));
}

// ---------------------------------------------------------------- running
const log = [];
function note(t) { log.push(t); if (log.length > 200) log.shift(); console.log(t); }

function showError(text) {
  $("#launcher").hidden = true; $("#loading").hidden = true; $("#game").hidden = true;
  $("#error-text").textContent = text;
  $("#error-log").textContent = log.slice(-30).join("\n");
  $("#error").hidden = false;
}

function screenSize() {
  const h = settings.res;
  const aspect = Math.max(4 / 3, Math.min(21 / 9, window.innerWidth / window.innerHeight || 16 / 9));
  // phones held upright still get a widescreen picture: they'll turn sideways
  const a = window.innerWidth < window.innerHeight ? 16 / 9 : aspect;
  // Doom's pixels are taller than wide: PrBoom+ shows h rows as 1.2*h, so widen to match
  return { w: Math.round((h * 1.2 * a) / 2) * 2, h };
}

function goFullscreen() {
  const el = document.documentElement;
  try {
    const p = el.requestFullscreen ? el.requestFullscreen({ navigationUI: "hide" }) : null;
    if (p && p.then) p.then(() => screen.orientation && screen.orientation.lock && screen.orientation.lock("landscape").catch(() => {})).catch(() => {});
  } catch { /* iPhone Safari: no fullscreen API; add to home screen instead */ }
}

const DEFAULT_CFG = `# AirplaneMode defaults (written once; your changes in the game's options are kept)
snd_midiplayer "opl2"
autorun 1
usemouse 1
use_joystick 1
uncapped_framerate 1
render_vsync 0
render_wipescreen 1
usegamma 1
screenblocks 10
hud_displayed 0
key_nextweapon 0xeb
key_prevweapon 0xec
`;

async function launch(game) {
  goFullscreen();   // needs the tap, so before anything async
  $("#launcher").hidden = true;
  $("#loading").hidden = false;
  $("#loading-title").textContent = game.title;
  const files = [{ url: "wads/prboom-plus.wad", name: "prboom-plus.wad" }, game.iwad, ...game.files];
  let blobs;
  try {
    blobs = await download(files, (got, total) => {
      $("#loading-bar").style.width = total ? Math.min(100, (100 * got) / total) + "%" : "30%";
      $("#loading-text").textContent = `Downloading ${(got / 1048576).toFixed(1)}${total ? " of " + (total / 1048576).toFixed(1) : ""} MB`;
    });
  } catch (e) { showError(e.message); return; }
  $("#loading-text").textContent = "Starting the engine...";
  startEngine(game, blobs);
}

function startEngine(game, blobs) {
  const canvas = $("#canvas");
  const size = screenSize();
  window.Module = {
    canvas,
    print: note,
    printErr: note,
    locateFile: (p) => "engine/" + p,
    setStatus: () => {},
    onAbort: (what) => showError("The engine stopped: " + what),
    onExit: (code) => {
      saveNow().finally(() => {
        if (code) showError("The game quit with an error.");
        else location.href = location.pathname;   // back to the game list
      });
    },
    onRuntimeInitialized() {
      const FS = Module.FS;
      FS.mkdir("/wads");
      for (const b of blobs) FS.writeFile("/wads/" + b.name, b.data);
      blobs.length = 0;
      FS.mkdirTree(HOME);
      FS.mount(Module.IDBFS, {}, HOME);
      FS.syncfs(true, (err) => {
        if (err) note("saves: " + err);
        if (!FS.analyzePath(HOME + "/prboom-plus.cfg").exists) FS.writeFile(HOME + "/prboom-plus.cfg", DEFAULT_CFG);
        const saveDir = HOME + "/saves/" + game.id;
        FS.mkdirTree(saveDir);
        FS.chdir("/wads");
        const args = ["-iwad", game.iwad.name];
        for (const f of game.files) args.push("-file", f.name);
        args.push("-save", saveDir, "-width", String(size.w), "-height", String(size.h), "-nofullscreen");
        note("prboom-plus " + args.join(" "));
        $("#loading").hidden = true;
        $("#game").hidden = false;
        window.dispatchEvent(new CustomEvent("doom-started"));
        try { Module.callMain(args); } catch (e) { if (!(e && e.name === "ExitStatus")) showError(String(e)); }
        setInterval(saveNow, 5000);
      });
    },
  };
  const s = document.createElement("script");
  s.src = "engine/prboom-plus.js";
  s.onerror = () => showError("Couldn't load the engine.");
  document.body.append(s);
}

// write settings + saved games to IndexedDB
let saving = null;
function saveNow() {
  if (saving || !window.Module || !Module.FS) return saving || Promise.resolve();
  saving = new Promise((resolve) => Module.FS.syncfs(false, (err) => { if (err) note("save failed: " + err); resolve(); }))
    .finally(() => { saving = null; });
  return saving;
}
document.addEventListener("visibilitychange", () => {
  if (document.hidden && window.Module && Module._am_save_config) {
    try { Module._am_save_config(); } catch { /* engine not running */ }
    saveNow();
  }
});

// ---------------------------------------------------------------- home button
// The game in progress lives only in this tab's memory (saved games survive, the level you're
// in doesn't), so leaving mid-game asks first, then writes settings and saves before going.
// The button sits outside the canvas and #touch; its events stop here so the engine's
// document listeners don't take the tap as a key or a pointer-lock request.
function bindHome() {
  const a = $("#am-home-float");
  for (const ev of ["mousedown", "mouseup", "pointerdown", "pointerup", "touchstart", "touchend", "keydown", "keyup"]) {
    a.addEventListener(ev, (e) => e.stopPropagation());
  }
  a.addEventListener("click", (e) => {
    if ($("#game").hidden || !window.Module || !Module.FS) return;   // loading or error: just go
    e.preventDefault();
    if (document.pointerLockElement) document.exitPointerLock();
    if (!confirm("Leave the game? Anything since your last save is lost.")) return;
    try { if (Module._am_save_config) Module._am_save_config(); } catch { /* engine stopped */ }
    saveNow().finally(() => { location.href = a.href; });
  });
}

// ---------------------------------------------------------------- start
bindSettings();
bindHome();
renderBundled();
loadManifest();
renderDrop().then(openFromHash);
