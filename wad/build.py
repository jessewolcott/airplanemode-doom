"""Build layover.wad: the Layover episode (6 airport maps) for Freedoom: Phase 2.

    python build.py --iwad freedoom2.wad --out layover.wad [--preview DIR] [--maps map01,map02]

Needs Pillow, and zdbsp (the node builder) on PATH unless --no-nodes.
Every map is checked before it's written (mapkit.Map.validate); a failing check stops
the build. The WAD carries only our own art and maps; textures from Freedoom are
referenced by name, so it must be played with freedoom2.wad (BSD-licensed) as the IWAD.
"""
import argparse
import importlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import art  # noqa: E402
import screens  # noqa: E402
import wadlib  # noqa: E402

MAPS = ["map01", "map02", "map03", "map04", "map05", "map06"]


def umapinfo(infos):
    out = []
    for i, (lump, info) in enumerate(infos):
        out.append(f"MAP {lump}\n{{")
        out.append(f'  levelname = "{info["title"]}"')
        out.append(f'  label = "L{i + 1}"')
        out.append(f'  levelpic = "AMLV{i + 1:02d}"')
        out.append('  skytexture = "AMSKY1"')
        if info.get("music"):
            out.append(f'  music = "{info["music"]}"')
        out.append(f'  partime = {info.get("par", 120)}')
        if i + 1 < len(infos):
            out.append(f'  next = "{infos[i + 1][0]}"')
        for line in info.get("extra", []):
            out.append("  " + line)
        out.append("}\n")
    return "\n".join(out).encode("ascii")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iwad", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview")
    ap.add_argument("--maps", default=",".join(MAPS))
    ap.add_argument("--no-nodes", action="store_true")
    args = ap.parse_args()

    _, base = wadlib.read_wad(args.iwad)
    pal = wadlib.Palette(wadlib.lump(base, "PLAYPAL"))
    pnames = wadlib.parse_pnames(wadlib.lump(base, "PNAMES"))
    textures = wadlib.parse_texture1(wadlib.lump(base, "TEXTURE1"))
    known = {t[0] for t in textures}

    patch_lumps = []
    for name, fn in art.TEXTURES.items():
        img = fn()
        patch_lumps.append((name, wadlib.to_picture(img, pal, 0, 0)))
        pnames.append(name)
        textures.append((name, img.size[0], img.size[1], [(0, 0, len(pnames) - 1)]))
        known.add(name)
    flat_lumps = [(name, wadlib.to_flat(fn(), pal)) for name, fn in art.FLATS.items()]
    base_flats = {n for n, d in base if len(d) == 4096}
    flats_known = base_flats | set(art.FLATS)

    preview = Path(args.preview) if args.preview else None
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        art.contact_sheet(preview / "art.png")

    map_lumps, infos, reports = [], [], {}
    for name in args.maps.split(","):
        mod = importlib.import_module(f"maps.{name}")
        m = mod.build()
        report = m.validate()
        # every texture and flat the map names must exist somewhere
        for l in m.lines:
            for side in l.sides:
                for k in ("upper", "lower", "mid"):
                    t = side.get(k)
                    if t and t != "-" and t.upper() not in known:
                        raise SystemExit(f"{m.lumpname}: unknown texture {t}")
        for s in m.sectors:
            for f in (s.ftex, s.ctex):
                if f.upper() not in flats_known:
                    raise SystemExit(f"{m.lumpname}: unknown flat {f}")
        map_lumps += m.lumps()
        infos.append((m.lumpname, dict(title=m.title, **getattr(mod, "INFO", {}))))
        reports[m.lumpname] = {k: v for k, v in report.items() if k != "errors"}
        print(f"{m.lumpname} {m.title}: {json.dumps(reports[m.lumpname]['monsters'])} monsters, "
              f"{report['sectors']} sectors, {report['lines']} lines, keys {report['keys']}")
        for w in report["warnings"]:
            print("   warning:", w)
        if preview:
            m.preview(preview / f"{name}.png")

    screen_lumps = [(n, wadlib.to_picture(img, pal, 0, 0)) for n, img in screens.pictures(infos)]
    lumps = [("UMAPINFO", umapinfo(infos))] + map_lumps
    lumps += [("PNAMES", wadlib.build_pnames(pnames)), ("TEXTURE1", wadlib.build_texture1(textures))]
    lumps += screen_lumps + patch_lumps
    lumps += [("FF_START", b"")] + flat_lumps + [("FF_END", b"")]

    out = Path(args.out)
    if args.no_nodes:
        wadlib.write_wad(out, lumps)
    else:
        zdbsp = shutil.which("zdbsp")
        if not zdbsp:
            raise SystemExit("zdbsp not found (apt install zdbsp), or pass --no-nodes")
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw.wad"
            wadlib.write_wad(raw, lumps)
            # -R: zero-filled REJECT (monsters always check sight) is fine for maps this size
            subprocess.run([zdbsp, "-q", "-R", "-o", str(out), str(raw)], check=True)
    if preview:
        (preview / "report.json").write_text(json.dumps(reports, indent=2))
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
