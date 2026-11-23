# Gotchas and extending

## Gotchas

- **Doom palette**: muted blues/teals quantise to grey. Test new art through PLAYPAL.
- **wasm function-pointer mismatches trap** at runtime, not compile time. Any new engine code
  calling through pointers must match signatures exactly.
- **`emscripten.h` after Doom headers** (true/false macros).
- **Line endings**: upstream PrBoom+ mixes CRLF (patch.py normalises). This repo is LF via
  `.gitattributes`; Python on Windows writes CRLF in text mode (`build.sh` once broke with
  `set: Illegal option -`), so write files with `newline="\n"`.
- **Turn units**: 65536 per full turn. The touch multiplier is `sens * 12`.
- **Aspect**: width must include the 1.2 factor or the picture is pillarboxed.
- **Overlapping sectors** aren't caught by edge checks alone; validate's point-in-sector check
  catches a room drawn on top of another. Always `inset`, `pillar` or `door(parent=)`.
- **Things on blocks**: a monster within its radius of a block taller than 24 is "stuck".
  Props near walls: keep 16+ units of clearance from walls you don't mean to touch.
- **Moving ceilings** (crushers) need explicit `upper` on adjacent lines, or you see holes when
  they move. Doors and lifts are handled automatically.
- **Octagons**: vertices at 22.5° + 45°k; corners cut in, so check thing positions against
  the diagonal edges (MAP06's roof had things outside until fixed).
- **Freedoom's names** follow Doom's (SW1GRAY1, DOORTRAK, GATE1, NUKAGE1, CRATE1, METAL...);
  `build.py` fails on unknown names. Flats are not textures (AMSTEEL is a flat, not a wall).
- **bossaction** fires only when the last monster of that type dies; no such monster = no exit.
- Drop items uploaded before Drop 0.2.1 have type `application/octet-stream`: no Play in Doom
  button, but the launcher still lists them (it matches on the `.wad` name).
- `#drop=<id>` only highlights the card; starting needs a tap.
- iPhone Safari: no Fullscreen API for pages; the manifest + apple meta tags make a
  home-screen web app instead (untested).

## Add a map

1. `wad/maps/map07.py` with `INFO` (par, music, optional `extra` UMAPINFO lines) and
   `build()` returning a `Map("MAP07", "Title")`.
2. Add it to `build.MAPS`. `next` links are generated in order; move the episode ending
   (`endcast`, `intertext`) from MAP06's `extra` to the new last map.
3. Build with `--preview`, fix validation errors, check the PNG, copy to `docs/maps/`.
4. The level-name patch `AMLVnn` is generated from the title.

## Add a texture or flat

Add a function to `art.py` and an entry in `TEXTURES` (wall, any width; keep heights ≤ 128
and widths 64/128/256 so it tiles) or `FLATS` (64x64). Names ≤ 8 characters, prefix `AM`.
See-through midtextures: return RGBA (alpha < 128 = transparent).

## Add a touch control

Button in `index.html` with `data-key="<name>"`, the code in touch.js's `KEY`, position in
`style.css` (and its `.lefty` mirror). If it needs a new binding, add it to `DEFAULT_CFG` and
note that existing players keep their old cfg. Update `tools/test_web.py`.

## Engine changes

Add an asserted replacement to `patch.py` (one match exactly); new exported C functions go
in `am_web.c` (`EMSCRIPTEN_KEEPALIVE`) and in `-sEXPORTED_FUNCTIONS` in `build.sh`. Bumping
PrBoom+ means updating `PRBOOM_TAG`/`PRBOOM_COMMIT` in the Dockerfile and re-checking every
patch. Multiplayer would need a WebSocket relay (PrBoom+ netplay is UDP).
