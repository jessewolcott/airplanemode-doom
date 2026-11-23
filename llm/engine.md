# Engine (`engine/`)

## build.sh (runs inside emsdk)

1. Copies `am_web.c` into `prboom2/src/`, runs `patch.py`.
2. **rdatawad natively**: PrBoom+ builds its own `prboom-plus.wad` with a helper program; when
   cross-compiling, CMake expects an "import file" pointing at a native build. We compile
   `prboom2/data/rd_*.c` with gcc against a three-line `config.h`, and write
   `/build/native/import.cmake` declaring an IMPORTED `rdatawad` target.
3. `embuilder build sdl2 zlib`, then `emcmake cmake` with SDL2/zlib paths pointed at the
   emsdk cache sysroot, and every optional library off: `BUILD_GL OFF`, no SDL_image,
   **no SDL_mixer** (music uses PrBoom+'s own OPL synth: `snd_midiplayer "opl2"`), no net,
   pcre, mad, fluidsynth, dumb, vorbis, portmidi, alsa. `SIMPLECHECKS`/`ZONEIDCHECK` off.
4. `make prboom-plus prboomwad`, copy `prboom-plus.{js,wasm}` and `prboom-plus.wad` to `$OUT`.

Link flags that matter:

| Flag | Why |
|---|---|
| `-sASYNCIFY` (+ 64 KB asyncify stack, 1 MB stack) | The Doom main loop never returns; asyncify lets `emscripten_sleep` / `am_wait_frame` yield to the browser |
| `-sALLOW_MEMORY_GROWTH -sINITIAL_MEMORY=64MB` | Freedoom WADs are ~29 MB each in MEMFS plus the zone heap |
| `-sINVOKE_RUN=0` | The page calls `callMain(args)` after writing the WADs |
| `-sEXIT_RUNTIME=1` | Quitting from the menu calls `Module.onExit` (page goes back to the game list) |
| `-sFORCE_FILESYSTEM -lidbfs.js`, export `FS, IDBFS, callMain` | MEMFS for WADs, IDBFS for saves |
| export `_am_key,_am_mouse,_am_state,_am_save_config` | Touch/page glue |
| `-sENVIRONMENT=web` | Smaller JS |

Output: ~2.2 MB wasm, ~170 KB JS, 358 KB prboom-plus.wad.

## patch.py

Normalises each touched file to LF (upstream mixes CRLF), applies asserted replacements
(exactly one match each, else exit 1):

- `src/CMakeLists.txt`: add `am_web.c` to the sources.
- `src/d_main.c`: declare `am_wait_frame()` and call it at the top of every `D_DoomLoop`
  iteration (yields until the next `requestAnimationFrame`, or 100 ms if the tab is hidden).
- `src/SDL/i_system.c`: `I_uSleep` -> `emscripten_sleep(us/1000)` (prototype declared by hand:
  `emscripten.h`'s `true/false` macros clash with `doomtype.h`'s enum).
- `fix_cheat_handlers()` on `m_cheat.c`: handlers are called through `void (*)()` with one
  argument, but ~30 are defined with none. Native code ignores it; **wasm traps with
  "function signature mismatch"** the moment you type a cheat. Regex turns
  `static void cheat_x()` (optionally followed by a `//` comment, e.g. `cheat_massacre`)
  into `(int unused_arg)` and direct calls `cheat_x()` into `cheat_x(0)`. Pointers and ints
  are both i32 in wasm32, so the `char *buf` and `int` handlers already match. Asserts 20+.

The build log's `-Wdeprecated-non-prototype` warnings were reviewed: the state action calls
(`st->action(mobj)`, `state->action(player, psp)`) and thinkers match their definitions;
only m_cheat.c needed fixing.

## am_web.c

| Function | Does |
|---|---|
| `am_key(down, key)` | Posts `ev_keydown`/`ev_keyup` with a Doom key code |
| `am_mouse(dx, dy)` | Posts `ev_mousemotion`. Turning: `cmd->angleturn -= mousex`, **65536 = a full turn**, sensitivity 10 = x1 |
| `am_state()` | bit0 menu open, bit1 yes/no message waiting (`messageToPrint && messageNeedsInput`), bit2 automap, bit3 in a level, bit4 not in a level (title, intermission, finale) |
| `am_save_config()` | `M_SaveDefaults()` (the page calls it when the tab is hidden; normally only on quit) |
| `am_wait_frame()` | `EM_ASYNC_JS`: await `requestAnimationFrame` (or 100 ms timeout when hidden) |

Include order: Doom headers first, then `emscripten.h`.

## Runtime behaviour worth knowing

- Resolution: the page passes `-width W -height H` with `H` = 300/400/600 ("Sharpness") and
  `W = H * 1.2 * aspect` because PrBoom+ shows the frame 1.2x taller (Doom's pixels). The
  canvas is CSS-stretched with `object-fit: contain; image-rendering: pixelated`.
- Config: `HOME=/home/web_user`, PrBoom+ uses `~/.prboom-plus/prboom-plus.cfg` because the
  directory exists (the page mkdirs it before mounting IDBFS).
- `prboom-plus.wad` is found because the cwd is `/wads`.
- Saves: `-save /home/web_user/.prboom-plus/saves/<game id>`; files `prboom-plus-savegame<N>.dsg`.
  The save menu pre-fills a name (`SetDefaultSaveName`), so OK saves without typing.
- Log lines like `Couldn't find preferred music player vorbis player` are normal (those
  players aren't compiled in); it then uses `opl2 synth player`.
- A console error "root document ... not valid for pointer lock" at start is SDL asking for
  pointer lock without a gesture; clicking the canvas works.
