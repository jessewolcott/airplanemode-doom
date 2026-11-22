# AirplaneMode Doom: PrBoom+ compiled to WebAssembly, Freedoom, and the Layover episode,
# served as static files. The game runs in the browser; the box only serves files.
#
# The engine and the WADs are platform-independent, so those stages run on the build
# machine ($BUILDPLATFORM) and only the tiny final stage is per-architecture.

ARG PRBOOM_TAG=v2.6.66
ARG PRBOOM_COMMIT=969515162c5aebea4ad7a125ee178dcad3d576ad
ARG FREEDOOM_VERSION=0.13.0
ARG FREEDOOM_SHA256=3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59

# ---- 1. PrBoom+ -> prboom-plus.{js,wasm} + prboom-plus.wad
FROM --platform=$BUILDPLATFORM emscripten/emsdk:6.0.13 AS engine
ARG PRBOOM_TAG
ARG PRBOOM_COMMIT
RUN git clone --depth 1 --branch "$PRBOOM_TAG" https://github.com/coelckers/prboom-plus /src/prboom-plus \
 && test "$(git -C /src/prboom-plus rev-parse HEAD)" = "$PRBOOM_COMMIT"
COPY engine/ /engine/
RUN sh /engine/build.sh

# ---- 2. Freedoom (BSD-licensed game data)
FROM --platform=$BUILDPLATFORM python:3.12-slim AS freedoom
ARG FREEDOOM_VERSION
ARG FREEDOOM_SHA256
ADD --checksum=sha256:${FREEDOOM_SHA256} \
    https://github.com/freedoom/freedoom/releases/download/v${FREEDOOM_VERSION}/freedoom-${FREEDOOM_VERSION}.zip /freedoom.zip
RUN python -m zipfile -e /freedoom.zip /tmp/fd && mkdir /out \
 && cp /tmp/fd/freedoom-*/freedoom1.wad /tmp/fd/freedoom-*/freedoom2.wad /tmp/fd/freedoom-*/COPYING.txt /out/ \
 && cp /tmp/fd/freedoom-*/CREDITS.txt /out/CREDITS-freedoom.txt

# ---- 3. The Layover episode, built from code (wad/), checked, with nodes from zdbsp
FROM --platform=$BUILDPLATFORM python:3.12-slim AS wad
RUN apt-get update && apt-get install -y --no-install-recommends zdbsp fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*
COPY wad/requirements.txt /wad/requirements.txt
RUN pip install --no-cache-dir -r /wad/requirements.txt
COPY wad/ /wad/
COPY --from=freedoom /out/freedoom2.wad /fd/freedoom2.wad
RUN python /wad/test_wad.py /fd/freedoom2.wad \
 && python /wad/build.py --iwad /fd/freedoom2.wad --out /out/layover.wad --preview /out/preview

# ---- 4. Static site
FROM --platform=$BUILDPLATFORM python:3.12-slim AS site
COPY web/ /www/
COPY --from=engine /out/prboom-plus.js /out/prboom-plus.wasm /www/engine/
COPY --from=engine /out/prboom-plus.wad /www/wads/
COPY --from=freedoom /out/ /www/wads/
COPY --from=wad /out/layover.wad /www/wads/
COPY tools/manifest.py /tmp/manifest.py
# sizes for the page's progress bar, then gzip copies (busybox httpd serves x.gz for x)
RUN python /tmp/manifest.py /www \
 && find /www -type f \( -name '*.wasm' -o -name '*.js' -o -name '*.wad' -o -name '*.html' -o -name '*.css' -o -name '*.json' \) \
      -exec gzip -k -9 {} \;

FROM busybox:1.37
COPY --from=site /www /www
COPY httpd.conf /etc/httpd.conf
USER 65534:65534
EXPOSE 8000
CMD ["httpd", "-f", "-v", "-p", "8000", "-h", "/www", "-c", "/etc/httpd.conf"]
