# Architecture

```
phone browser ──GET /doom/...──> Caddy (platform proxy) ──> doom:8000 (busybox httpd, static)
     │                                                        /www/index.html, app.js, touch.js, style.css
     │                                                        /www/engine/prboom-plus.{js,wasm}
     │                                                        /www/wads/{freedoom1,freedoom2,layover,prboom-plus}.wad
     │                                                        /www/wads/manifest.json (+ .gz copies of all of it)
     ├──GET /drop/api/items, /drop/api/files/<id> (Range)──> drop:8000      (user WADs)
     └──GET /api/apps (via Drop only; the Doom page doesn't need it)
```

There is no backend. Everything dynamic happens in the browser:
`app.js` downloads WADs -> loads `engine/prboom-plus.js` -> `onRuntimeInitialized` writes the
WADs to `/wads` in MEMFS, mounts IDBFS at `/home/web_user/.prboom-plus`, syncs it in, writes a
default `prboom-plus.cfg` if missing, `chdir("/wads")`, then `Module.callMain(args)`.

## Docker build (`Dockerfile`)

| Stage | Base | Platform | Does |
|---|---|---|---|
| `engine` | `emscripten/emsdk:6.0.13` | `$BUILDPLATFORM` | Clones PrBoom+ `v2.6.66`, checks commit `969515162c5a...`, runs `engine/build.sh` -> `/out/prboom-plus.{js,wasm,wad}` |
| `freedoom` | `python:3.12-slim` | `$BUILDPLATFORM` | `ADD --checksum` Freedoom 0.13.0 zip, unzips WADs + COPYING + CREDITS |
| `wad` | `python:3.12-slim` + apt `zdbsp fonts-dejavu-core` + Pillow | `$BUILDPLATFORM` | `test_wad.py`, then `build.py` -> `/out/layover.wad` (+ previews) |
| `site` | `python:3.12-slim` | `$BUILDPLATFORM` | Assembles `/www`, writes `manifest.json`, `gzip -k -9` copies of wasm/js/wad/html/css/json |
| final | `busybox:1.37` | target | `httpd -f -v -p 8000 -h /www -c /etc/httpd.conf`, user 65534 |

All heavy stages are architecture-independent output, so CI's arm64+amd64 build only runs
the final stage twice (~4.5 min total on GitHub runners). busybox httpd serves `x.gz` when
the client accepts gzip (freedoom2.wad 28.8 MB -> 10.9 MB) and sends ETag/Last-Modified, so
browsers revalidate rather than re-download.

## In the platform

- `compose.yaml`: service `doom`, image `ghcr.io/jessewolcott/airplanemode-doom:0.1.1`,
  `mem_limit: ${DOOM_MEM:-32m}`, no volume, no env. `compose.dev.yaml` builds `../airplanemode-doom`.
- `Caddyfile`: `redir /doom /doom/` + `handle_path /doom/* { reverse_proxy doom:8000 }`.
- `portal/apps.json`: entry `doom` (category Games, icon `/icons/doom.svg`) with
  `opens: {from: drop, types: [application/x-doom-wad], url: /doom/#drop={id}}`.
- `hardware/*.env`: `DOOM_MEM=32m`.
- Decision record: platform `docs/decisions/0015-doom.md`.
- Drop 0.2.1 maps `.wad` to `application/x-doom-wad` and treats it as an inline type.

## Standalone

`docker compose up -d --build` -> http://localhost:8771. Drop isn't reachable standalone
(`../drop/` 404s), so the Drop section just stays hidden.
