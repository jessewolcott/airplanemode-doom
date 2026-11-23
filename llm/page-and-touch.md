# Page and touch controls (`web/`)

## index.html

Four top-level screens, toggled with `hidden`: `#launcher` (game cards, Drop section, help,
settings, footer with licences), `#loading` (title, bar, text), `#game` (`#canvas` + `#touch`
overlay + `#rotate` portrait hint), `#error` (message + last 30 log lines + "Back to games",
an inline `onclick` that reloads without the hash). Scripts: `app.js` then `touch.js`.

**Home button** (platform app contract item 10): `a.am-home` (house icon, `href="../"`) at the
right end of the launcher's `<header>` (it replaced the old "AirplaneMode" text link), and a
second one, `#am-home-float.am-home.float`, after `#error`: `position: fixed` top right (safe-area
insets), shown by CSS on every screen except the launcher (`#launcher:not([hidden]) ~ ...`).
While `#game` shows it is see-through (opacity 0.55, 18 px icon) but still 44 x 44 px. It sits
outside `#touch`, so touch.js never sees taps on it. Left-handed mode moves ☰ and Map left by
56 px to keep the top right corner free. `bindHome()` in app.js stops its mouse/pointer/touch/key
events from reaching the engine's document listeners (no stray key or pointer-lock request) and,
mid-game, asks `confirm` first (only saved games survive a reload), then `am_save_config()` +
`saveNow()` before leaving. With the mouse captured, Esc releases pointer lock and the button is
clickable; SDL eats Tab during play, so keyboard focus can't reach it then (untested on phones).

`#touch` contains three control groups; CSS shows one depending on the class set by
`touch.js`: `.play` (move zone, look zone, buttons ☰ Map ‹ › Use Fire), `.menu` (D-pad, OK,
Back, Close, plus Yes/No when `.question`), `.skip` ("Tap to continue", any tap = Enter).
`.lefty` mirrors the play controls. Buttons carry `data-key` names that must exist in
touch.js's `KEY` table (tested).

## app.js

- `GAMES`: layover (iwad freedoom2 + layover.wad), freedoom2, freedoom1.
- Settings in localStorage (`amdoom.sens|res|lefty`, try/catch): turn speed 1-20 (default
  8), sharpness 300/400/600 (default 400), left-handed.
- **Drop WADs** (`renderDrop`): `fetch("../drop/api/items")`; null -> no Drop (hint hidden).
  For each `kind == "file"` named `*.wad`: `inspectWad` does a `Range: bytes=0-11` request
  (kind, lump count, directory offset) and a second Range request for the directory, then
  `parseWadDirectory` lists map lumps (`ExMy` -> format `doom`, `MAPxx` -> `doom2`).
  Servers that ignore Range get sliced. 403 -> "Drop has downloads turned off" (shouldn't
  happen since Drop 0.2.1 serves WADs inline).
  - IWAD -> its own card (game id `drop-<name>`).
  - PWAD -> card with a `<select>` of bases: matching IWADs from Drop first, then Freedoom
    Phase 2 (doom2 format) / Phase 1 (doom format); unknown format -> all.
- `#drop=<id>` (from Drop's Play in Doom): after Drop WADs render, highlights and scrolls to
  that card. It doesn't auto-start: audio and fullscreen need a tap.
- `launch(game)`: `goFullscreen()` first (needs the click's activation; then tries
  `screen.orientation.lock("landscape")`), then `download()` all files in parallel with
  streamed progress (totals from `wads/manifest.json` because gzip makes Content-Length the
  compressed size), then `startEngine`.
- `startEngine`: sets `window.Module` (canvas, print/printErr -> `note()` log ring of 200,
  `locateFile` -> `engine/`, `onAbort` -> error screen, `onExit` -> save then reload or error),
  injects `engine/prboom-plus.js`. `onRuntimeInitialized` as in architecture.md. Args:
  `-iwad <name> [-file <pwad>...] -save <dir> -width W -height H -nofullscreen`. Dispatches
  `doom-started` for touch.js. `setInterval(saveNow, 5000)`.
- `DEFAULT_CFG` (written only if no cfg yet): `snd_midiplayer "opl2"`, `autorun 1`,
  `usemouse 1`, `use_joystick 1`, `uncapped_framerate 1`, `render_vsync 0`,
  `render_wipescreen 1`, `usegamma 1`, `screenblocks 10`, `hud_displayed 0`,
  `key_nextweapon 0xeb`, `key_prevweapon 0xec`.
- `saveNow()`: `FS.syncfs(false)`, one at a time. On `visibilitychange` hidden: `am_save_config()` + sync.

## touch.js

- `KEY`: up/down/left/right arrows `0xad 0xaf 0xac 0xae`, esc 27, enter 13, backspace 127,
  map 9, fire `0x80+0x1d` (RCtrl), use 32, speed `0x80+0x36` (RShift), next/prev weapon
  `0x80+0x6b/0x6c` (wheel), forward/back/strafe `w s a d`, y, n.
- `press/release` reference-count keys across fingers; `releaseAll` on mode change and window blur.
- **Move stick** (`#move`, left 42%): floating origin where the finger lands, radius 56 px;
  dragging past the radius drags the origin. Forward if `ny < -0.3`, back `> 0.3`, strafe
  `|nx| > 0.38`; deflection under 0.7 also holds Speed, which with autorun on means walk.
- **Look** (`#look`, right 58%, or a finger that started on Fire, `data-look`): horizontal
  movement x `sens * 12` -> `am_mouse(dx, 0)`, fractional remainder carried. At the default
  (8), 300 px ≈ 160°.
- Buttons: finger down on a `.btn` presses its key (`navigator.vibrate(8)` on Fire).
- `poll()` every 100 ms: `am_state()` -> mode `menu` if bits 0-1, `play` if bit 3, else
  `skip`; `question` class from bit 1.
- Shown when `(pointer: coarse)` or `maxTouchPoints > 0`, or on the first touch on `#game`.

## style.css

Dark tokens on `:root` (`--bg #120b0b`, `--accent #e0472b`, `--accent-2 #f2b134`; the home
button uses `--panel`/`--line`, `--accent-2` for hover and its focus ring). The game
uses safe-area insets. Portrait on touch devices: canvas at 56% height, top-aligned, with the
rotate hint below it.
