# Testing and release

## Automated (CI runs both before building)

```sh
pip install -r wad/requirements.txt && python wad/test_wad.py [freedoom2.wad]
python tools/test_web.py
```

`wad/test_wad.py` (unittest): WAD round trip; picture encoding keeps transparency (decoded
back); PNAMES/TEXTURE1 round trip; door lines face rooms with special 1 and the door texture;
walls split at shared edges; reachable exit; key-locked exit fails without the key and passes
with it; stuck thing detected; overlapping rooms detected; a room drawn over another
detected; inset touching its parent's wall; scroller control vector and tag; **every map in
`build.MAPS` validates**. Without the IWAD argument the picture test uses a grey ramp palette.
The Docker `wad` stage runs it with freedoom2.wad.

`tools/test_web.py`: no root-relative `src`/`href`/`fetch`/`url()`; nothing loaded from
`http(s)://`; touch key codes match PrBoom+ defaults; every `data-key` exists in `KEY`;
default cfg has the weapon keys and opl2.

## Manual checks done for 0.1.0 (desktop Chromium via Playwright)

- Title screen, menus, new game, all six maps via `idclev`, doors, pickups, cheats (after the
  m_cheat.c fix), music player = opl2, UMAPINFO names on the automap ("L5: The Tarmac").
- Saves persist across a page reload (IDBFS).
- Touch: synthetic TouchEvents -> `w`, `am_mouse`, RCtrl, Esc; menu mode appears.
- Platform dev stack: `/doom/` through Caddy; a `.wad` uploaded to Drop gets
  `application/x-doom-wad` and **Play in Doom**; the launcher lists it as a 6-level mod on
  Freedoom 2 and it loads (`adding airportmod.wad`).
- MAP06 bossaction: mast opens after all monsters die.

Not done: real phones (Android Chrome, iPhone home-screen app), audio on mobile, frame rate
on mid-range phones, gamepads. The platform's `docs/testing.md` has the on-device item.

## Iterating

- Maps: `python wad/build.py --iwad <freedoom2.wad> --out raw.wad --preview build/preview --no-nodes`
  (seconds), look at `build/preview/mapNN.png`, then `docker build` to play it.
- Engine: `docker build` reruns the emsdk stage only when `engine/` changes (~3 min).
- Quick serve: `docker run -d -p 8770:8000 airplanemode-doom:dev`.
- Driving the game from the browser console: `Module._am_key(1, code)` / `(0, code)`,
  `Module._am_state()`, cheats by typing characters (`idclevNN`, `iddqd`, `idclip`, `tntem`).
  Typing `iddqd` twice turns god mode off again.

## Releasing

Ask Jesse first (tags publish images). Push `vX.Y.Z` -> CI publishes
`ghcr.io/jessewolcott/airplanemode-doom:X.Y.Z` (arm64+amd64). Then in `../airplanemode`:
bump the pin in `compose.yaml`; the platform CI checks the image has arm64. Released: 0.1.0
(2026-11-22). Drop 0.2.1 was released alongside for Play in Doom.
