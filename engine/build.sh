#!/bin/sh
# Build PrBoom+ to WebAssembly. Runs inside the emscripten/emsdk image (see ../Dockerfile).
#   SRC  = PrBoom+ checkout (prboom2/ inside), patched with engine/patches/*.patch
#   OUT  = where prboom-plus.{js,wasm} and prboom-plus.wad go
set -eu
SRC=${SRC:-/src/prboom-plus}
OUT=${OUT:-/out}
HERE=$(cd "$(dirname "$0")" && pwd)
P=$SRC/prboom2
mkdir -p "$OUT" /build/native /build/wasm

# Our glue: JS-callable input functions and the browser main loop.
cp "$HERE/am_web.c" "$P/src/am_web.c"
python3 "$HERE/patch.py" "$SRC"

# 1. The data-WAD tool runs on the build machine, so compile it natively.
cat > /build/native/config.h <<'EOF'
#define PACKAGE_NAME "prboom-plus"
#define PACKAGE_VERSION "2.6.66"
#define HAVE_UNISTD_H 1
EOF
gcc -O2 -I/build/native -o /build/native/rdatawad "$P"/data/rd_*.c
cat > /build/native/import.cmake <<'EOF'
add_executable(rdatawad IMPORTED)
set_property(TARGET rdatawad PROPERTY IMPORTED_LOCATION /build/native/rdatawad)
EOF

# 2. SDL2 from emscripten's ports (built once into the emsdk cache).
embuilder build sdl2 zlib >/dev/null
SYSROOT=$(em-config CACHE)/sysroot
FLAGS="-O3 -sUSE_SDL=2 -sUSE_ZLIB=1"

cd /build/wasm
emcmake cmake "$P" -G "Unix Makefiles" \
  -DCMAKE_BUILD_TYPE=Release \
  -DIMPORT_EXECUTABLES=/build/native/import.cmake \
  -DCMAKE_C_FLAGS="$FLAGS" -DCMAKE_CXX_FLAGS="$FLAGS" \
  -DSDL2_INCLUDE_DIR="$SYSROOT/include/SDL2" \
  -DSDL2_LIBRARY="$SYSROOT/lib/wasm32-emscripten/libSDL2.a" \
  -DZLIB_INCLUDE_DIR="$SYSROOT/include" \
  -DZLIB_LIBRARY="$SYSROOT/lib/wasm32-emscripten/libz.a" \
  -DBUILD_GL=OFF -DWITH_IMAGE=OFF -DWITH_MIXER=OFF -DWITH_NET=OFF -DWITH_PCRE=OFF \
  -DWITH_MAD=OFF -DWITH_FLUIDSYNTH=OFF -DWITH_DUMB=OFF -DWITH_VORBISFILE=OFF \
  -DWITH_PORTMIDI=OFF -DWITH_ALSA=OFF -DSIMPLECHECKS=OFF -DZONEIDCHECK=OFF \
  -DCMAKE_EXE_LINKER_FLAGS="$FLAGS \
    -sASYNCIFY -sASYNCIFY_STACK_SIZE=65536 -sSTACK_SIZE=1048576 \
    -sALLOW_MEMORY_GROWTH=1 -sINITIAL_MEMORY=67108864 \
    -sINVOKE_RUN=0 -sEXIT_RUNTIME=1 -sFORCE_FILESYSTEM=1 -lidbfs.js \
    -sEXPORTED_RUNTIME_METHODS=callMain,FS,IDBFS \
    -sEXPORTED_FUNCTIONS=_main,_am_key,_am_mouse,_am_state,_am_save_config \
    -sENVIRONMENT=web"
make -j"$(nproc)" prboom-plus prboomwad
cp prboom-plus.wad "$OUT/"
cp src/prboom-plus.js src/prboom-plus.wasm "$OUT/" 2>/dev/null || cp prboom-plus.js prboom-plus.wasm "$OUT/"
ls -l "$OUT"
