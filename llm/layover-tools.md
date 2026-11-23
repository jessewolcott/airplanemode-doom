# Layover tools (`wad/`)

## mapkit.py: polygons -> a Doom map

Coordinates are map units, y up. Player: 32 wide, 56 tall, steps 24.

**Building API (`Map`)**

| Call | Makes |
|---|---|
| `room(poly, floor, ceil, ftex, ctex, light=, wall=, face_lower=, face_upper=, special=, name=)` | A sector |
| `inset(parent, poly, **props)` | A hole in `parent` filled by a new sector (missing props copied from parent). May touch the parent's outer wall |
| `pillar(parent, poly)` | A void hole (solid column) |
| `door(poly, floor, tex, key=None|blue|yellow|red, remote=False, tag=0, parent=None)` | Door sector, ceiling = floor. Between two rooms, or inside one with `parent=` |
| `lift(poly, low, high, ceil)` | Lift resting at `high`; gets a tag |
| `window(poly, sill, lintel)` | Impassable see/shoot-through sector |
| `teleport(pad_poly, parent, dest_sector, dest_xy, angle)` | Pad inset + teleport destination thing |
| `scroll(target, dx, dy, special=253)` | Boom scroller (253 floor+carry, 251 floor texture, 250 ceiling) |
| `line(a, b, special=, tag=, flags=, upper/lower/mid/xoff/yoff=, back={...}, front=Sector, only_twosided=)` | Overrides on the line(s) lying on segment a-b |
| `wall(a, b, tex)` | Retexture one-sided walls on a segment |
| `switch(a, b, special, target or [targets], tex=)` | Switch line tagged to sector(s); also recorded for reachability |
| `thing(x, y, type, angle, flags)`, `things_at(type, points, ...)` | Things (flags: EASY 1, MEDIUM 2, HARD 4, AMBUSH 8) |
| `boss_opens.append(sector)` | Remote door opened by UMAPINFO bossaction (counted as openable) |

**`build()`**

1. Scroller control sectors: each `scroll()` gets a tiny closed sector 512 units east of the
   map whose first edge has vector `(dx*32, dy*32)` (Boom takes speed and direction from it).
2. Collects every ring edge (outer rings clockwise, holes counter-clockwise), **splitting
   edges at any vertex lying on them** (T-junctions; override endpoints count as vertices,
   so `line()`/`switch()` can address part of a wall).
3. A sector that owns an edge in both directions cancels it (an inset touching its parent's
   wall). More than one owner left for a directed edge = overlap error.
4. Edge pairs (p,q)/(q,p) of different sectors -> two-sided line (front = first, flags
   TWO_SIDED); unpaired -> one-sided wall (IMPASSABLE).
5. `_apply_roles`: door lines flipped so **front = room, back = door**, special 1/26/27/28
   unless remote; lift lines: 62 (SR) from lower neighbours (front = lower side), 88 (WR)
   from upper ones; pad lines: 97 to `pad.dest.tag`, front outward; window lines
   IMPASSABLE|BLOCK_MONSTERS.
6. `_apply_textures`: per side, world-aligned `xoff` (dot(v1, dir)) so split walls tile;
   one-sided -> `me.wall` (door tracks get LOWER_UNPEGGED); upper if my ceiling is higher or
   the other side is a door -> `other.face_upper or me.wall`; lower if my floor is lower or
   a lift is involved -> `other.face_lower or (other.wall if I'm the lift else me.wall)`.
7. Scroller control lines, then all overrides.

**`validate()`** raises on: crossing edges; a sector whose vertex-average point lies inside
another sector (drawn on top instead of inset); vertices beyond ±32000; not exactly one
player start; things outside the map; monsters/players that don't fit under the ceiling or
sit within their radius of a blocking line (one-sided, impassable, or a step above 24, or a
gap below their height; door lines excluded); **exit unreachable**. Reachability: directed
sector graph (step up ≤ 24 using floor ranges, so lifts span low..high; headroom ≥ 56 using
door ceilings = lowest neighbour ceiling - 4), key doors need the key, remote doors need a
reachable switch front sector (or `boss_opens`), teleports add edges; iterate as keys are
picked up. Warnings: unreachable sectors (except `name="block"` props/closets and doors),
unreachable secrets. Report: keys, monsters per skill, counts.

**`preview(path)`**: top-down PNG, floor height shading, sky tint, doors coloured by key,
lifts green, secrets purple; walls white, specials yellow, exits red; things as dots.

## parts.py

`sign` (8-thick sector hung `drop=32` below the ceiling, `face_upper` = 128x32 sign texture;
`along="x"|"y"`), `board` (128x64 departures board, drop 64), `block` (raised inset, default
`name="block"`), `desk` (40 high, AMDESK), `seats` (32, AMSEAT), `crates` (CRATE1/CRATOP1),
`lights` (inset with AMLITE ceiling, +32 light), `rope` (thin strip; its two-sided edges get
the see-through AMROPE midtexture, impassable, lower-unpegged), `octagon`, `carousel` (belt
ring +24 that scrolls/carries, raised centre +64).

## art.py and screens.py

Pillow drawings, one function per lump; `TEXTURES` (single-patch wall textures, patch name =
texture name) and `FLATS` (64x64). Fonts: DejaVu Sans Bold / Mono Bold in the image (Arial /
Consolas fallback on Windows, so local renders differ slightly). **Colours**: the palette has
greys, browns, tans, greens, reds, oranges/yellows, pure blues `(0,0,x)` and the periwinkle
ramp `(v,v,255)`; nothing teal or muted blue. `NAVY = (0,0,155)` for liveries. `contact_sheet()`
renders everything (unquantised; quantise with the palette to see the real result).
screens.py: TITLEPIC and INTERPIC (320x200), M_DOOM (menu logo), `AMLVnn` level-name patches.

## build.py

Reads freedoom2.wad's PLAYPAL, PNAMES, TEXTURE1 and flat names. Encodes art (nearest
palette colour, weighted RGB), **appends** our patches to Freedoom's PNAMES/TEXTURE1 and
writes both whole (a PWAD's TEXTURE1 replaces the IWAD's). Flats go between FF_START/FF_END
(PrBoom+ merges PWAD flats). For each map module: `build()`, `validate()`, check every
texture/flat name exists, lumps, preview. UMAPINFO per map: levelname, label `L<n>`,
levelpic `AMLVnn`, skytexture `AMSKY1`, music, partime, next, plus `INFO["extra"]` lines.
Then `zdbsp -q -R -o out raw` (zero REJECT). `--no-nodes` skips zdbsp (for local checks).
