"""Patch a PrBoom+ v2.6.66 checkout for the browser build.

Usage: python3 patch.py <prboom-plus checkout>

Plain string replacements, each asserted, so an upstream change fails loudly instead of
building something half-patched. Files are normalised to LF first (upstream mixes CRLF in).
"""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) / "prboom2" / "src"

EDITS = {
    "CMakeLists.txt": [
        # our glue (engine/am_web.c, copied in by build.sh)
        ("    am_map.c\n", "    am_map.c\n    am_web.c\n"),
    ],
    "d_main.c": [
        ("static void D_DoomLoop(void)\n{",
         "#ifdef __EMSCRIPTEN__\nvoid am_wait_frame(void);\n#endif\n\nstatic void D_DoomLoop(void)\n{"),
        # hand the browser a frame on every pass of the main loop
        ("  for (;;)\n    {\n      WasRenderedInTryRunTics = false;",
         "  for (;;)\n    {\n#ifdef __EMSCRIPTEN__\n      am_wait_frame();\n#endif\n"
         "      WasRenderedInTryRunTics = false;"),
    ],
    "SDL/i_system.c": [
        # sleeping must yield to the browser (ASYNCIFY), not block the page.
        # (emscripten.h's true/false macros clash with doomtype.h, so declare it by hand.)
        ("void I_uSleep(unsigned long usecs)\n{\n    SDL_Delay(usecs/1000);\n}",
         "#ifdef __EMSCRIPTEN__\nvoid emscripten_sleep(unsigned int ms);\n#endif\n"
         "void I_uSleep(unsigned long usecs)\n{\n#ifdef __EMSCRIPTEN__\n    emscripten_sleep(usecs/1000);\n"
         "#else\n    SDL_Delay(usecs/1000);\n#endif\n}"),
    ],
}


def fix_cheat_handlers():
    """m_cheat.c calls every handler through `void (*)()` with one argument, but many are
    defined with none. Native code shrugs; WebAssembly traps ("function signature mismatch")
    as soon as you type a cheat. Give those handlers an unused int (pointers and ints are
    both i32 in wasm32, so the others already match) and pass 0 where they're called."""
    import re
    path = ROOT / "m_cheat.c"
    text = path.read_bytes().decode("latin-1").replace("\r\n", "\n")
    # definitions: "static void cheat_x()" alone on its line (maybe with a // comment)
    defn = r"^static void (cheat_\w+)\(\)(\s*(//.*)?)$"
    noargs = set(m[0] for m in re.findall(defn, text, flags=re.M))
    if len(noargs) < 20:
        sys.exit(f"patch.py: m_cheat.c: expected 20+ no-argument cheat handlers, found {len(noargs)}")
    text = re.sub(defn, r"static void \1(int unused_arg)\2", text, flags=re.M)
    text = re.sub(r"^static void (cheat_\w+)\(\);", r"static void \1();", text, flags=re.M)
    calls = re.compile(r"(?<!static void )\b(" + "|".join(sorted(noargs)) + r")\(\)")
    text = calls.sub(r"\1(0)", text)
    path.write_bytes(text.encode("latin-1"))
    print(f"patched m_cheat.c ({len(noargs)} cheat handlers)")


def main():
    fix_cheat_handlers()
    for name, edits in EDITS.items():
        path = ROOT / name
        text = path.read_bytes().decode("latin-1").replace("\r\n", "\n")
        for old, new in edits:
            if text.count(old) != 1:
                sys.exit(f"patch.py: {name}: expected exactly one match for {old[:60]!r}")
            text = text.replace(old, new)
        path.write_bytes(text.encode("latin-1"))
        print(f"patched {name} ({len(edits)} edits)")


if __name__ == "__main__":
    main()
