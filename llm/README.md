# Doom: how it's built (LLM / engineer reference)

Checked-in notes (`.dockerignore` lists `llm`, so none of this reaches the image). Written from the code as of release 0.1.0 (2026-11-22). If the code
and these notes disagree, the code wins; fix the notes.

## Overview

The Doom app is PrBoom+ 2.6.66 compiled to WebAssembly, served as static files by busybox
httpd. **The game runs in the visitor's browser**; the box only serves files (memory limit
32 MB). The page offers three bundled games (Layover, Freedoom: Phase 2, Freedoom: Phase 1)
plus any `.wad` files in Drop, downloads the WADs with a progress bar, writes them into
Emscripten's in-memory filesystem, and calls the engine's `main()`. Saves and the config file
live in IndexedDB (Emscripten IDBFS). Touch controls call small C functions added to the
engine (`am_key`, `am_mouse`, `am_state`) rather than faking DOM keyboard events.

**Layover** is a six-map airport episode generated entirely by Python in `wad/` (maps,
textures, flats, signs, title/intermission/menu pictures, UMAPINFO). Every build validates
each map statically and node-builds with zdbsp. It plays on top of `freedoom2.wad`.

## Files in this folder

| File | What it covers |
|---|---|
| [architecture.md](architecture.md) | Pieces, the Docker build stages, request flow, how it sits in the platform |
| [engine.md](engine.md) | `engine/`: the Emscripten build, `patch.py`'s patches, `am_web.c`, link flags, runtime behaviour |
| [page-and-touch.md](page-and-touch.md) | `web/`: launcher, downloads, Drop WADs, starting the engine, saves, touch controls, modes |
| [layover-tools.md](layover-tools.md) | `wad/`: `mapkit.py` (geometry -> lines, roles, textures, validation), `parts.py`, `art.py`, `screens.py`, `build.py` |
| [layover-maps.md](layover-maps.md) | The six maps: layout, key route, features, monsters, secrets |
| [testing-and-release.md](testing-and-release.md) | Tests, how things were verified, CI, releasing, platform wiring |
| [gotchas-and-extending.md](gotchas-and-extending.md) | Non-obvious behaviour and how to add maps, textures, controls, engine patches |

## Source map

| Path | Role |
|---|---|
| `Dockerfile` | 4 build stages (engine, freedoom, wad, site) + busybox runtime |
| `httpd.conf` | busybox MIME types (`.wasm`, `.wad`, ...) |
| `engine/build.sh` | Native rdatawad + emcmake/make of PrBoom+ |
| `engine/patch.py` | Asserted string patches to the PrBoom+ checkout |
| `engine/am_web.c` | Browser glue compiled into the engine |
| `web/index.html` | Launcher, loading screen, game canvas, touch overlay markup, error screen |
| `web/app.js` | Games, Drop WADs, downloads, engine start, IDBFS saves (~330 lines) |
| `web/touch.js` | Touch controls (~170 lines) |
| `web/style.css` | Launcher + overlay styles (tokens on `:root`, dark only) |
| `wad/mapkit.py` | Map kit (~670 lines) |
| `wad/parts.py` | Airport furniture helpers |
| `wad/art.py` | Procedural textures/flats (~520 lines) |
| `wad/screens.py` | TITLEPIC, INTERPIC, M_DOOM, AMLVnn level names |
| `wad/wadlib.py` | WAD I/O, picture/flat encoding, PNAMES/TEXTURE1 |
| `wad/things.py` | Thing type constants |
| `wad/maps/map01.py`..`map06.py` | The maps |
| `wad/build.py` | Builds `layover.wad` |
| `wad/test_wad.py` | Unit tests + every map validates |
| `tools/manifest.py` | Writes `wads/manifest.json` (sizes for the progress bar) in the image |
| `tools/test_web.py` | Static page checks |
| `docs/maps/*.png` | Top-down previews (copy from a `--preview` build after map changes) |

## Invariants that matter

1. **Relative URLs only** in `web/` (served at `/doom/` with the prefix stripped). Drop is
   `../drop/`, the platform API `../api/`. `tools/test_web.py` checks.
2. **Nothing from the internet at runtime.** Freedoom and the engine are baked into the image.
3. **Touch key codes = PrBoom+ default bindings** (`w s a d`, RCtrl fire, space use, RShift
   speed, wheel up/down for weapons). The default config the page writes must agree. Tested.
4. **Every Layover map validates** (no overlaps, things placed sanely, exit reachable with
   findable keys) or the build fails.
5. **Function-pointer signatures must match exactly** in wasm; see engine.md.
6. **Art must use colours the Doom palette has**; muted blues/teals become grey.
7. MAP06's exit depends on UMAPINFO `bossaction`: a Cyberdemon (medium/hard) or barons (easy)
   must exist on every skill.
