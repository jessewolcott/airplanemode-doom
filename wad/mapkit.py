"""Build Doom (Boom-format) maps from polygons.

A map is a set of sectors. Each sector is a polygon (plus optional holes). Where two
sectors share an edge, a two-sided line is made between them; edges nobody shares become
walls. Doors, lifts, windows and teleport pads are sectors with a role, which sets their
line specials, textures and orientation. Then `validate()` checks the result statically
(things inside sectors, nothing stuck in walls, the exit reachable with the keys you can
find) and `preview()` draws a top-down PNG.

Coordinates are Doom map units (the player is 32 wide, 56 tall, steps up 24). y points up.
"""
from __future__ import annotations

import math
import struct
from collections import defaultdict, deque
from dataclasses import dataclass, field

SKY = "F_SKY1"

# linedef flags
IMPASSABLE, BLOCK_MONSTERS, TWO_SIDED, UPPER_UNPEGGED, LOWER_UNPEGGED = 1, 2, 4, 8, 16
SECRET_LINE, BLOCK_SOUND, NOT_ON_MAP, ALWAYS_ON_MAP = 32, 64, 128, 256

# thing flags (skills: 1 = easy (ITYTD, HNTR), 2 = medium (HMP), 4 = hard (UV, NM))
EASY, MEDIUM, HARD, AMBUSH = 1, 2, 4, 8
ALL = EASY | MEDIUM | HARD

KEY_DOOR = {None: 1, "blue": 26, "yellow": 27, "red": 28}  # DR (use) doors
KEY_THINGS = {"blue": (5, 40), "yellow": (6, 39), "red": (13, 38)}
EXIT_SPECIALS = {11, 52, 197}
SECRET_EXIT_SPECIALS = {51, 124, 198}
TELEPORT_SPECIALS = {39, 97, 125, 126}
LIFT_SPECIALS = {62, 88, 120, 121, 10, 21}

# radius, height of things we use (for the "stuck in a wall" check). Unknown: 16, 16.
THING_SIZE = {
    1: (16, 56), 2: (16, 56), 3: (16, 56), 4: (16, 56), 11: (16, 56), 14: (16, 56),
    3004: (20, 56), 9: (20, 56), 65: (20, 56), 3001: (20, 56), 3002: (30, 56), 58: (30, 56),
    3006: (16, 56), 3005: (31, 56), 3003: (24, 64), 69: (24, 64), 66: (20, 56), 67: (48, 64),
    68: (64, 64), 71: (31, 56), 64: (20, 56), 16: (40, 110), 7: (128, 100),
    2035: (10, 42), 48: (16, 16), 2028: (16, 16), 85: (16, 16), 86: (16, 16), 70: (16, 16),
}
MONSTERS = {3004, 9, 65, 3001, 3002, 58, 3006, 3005, 3003, 69, 66, 67, 68, 71, 64, 16, 7}


def rect(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def area2(poly):
    """Twice the signed area: positive = counter-clockwise (y up)."""
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))


def cw(poly):
    poly = [tuple(map(int, p)) for p in poly]
    return poly if area2(poly) < 0 else poly[::-1]


def ccw(poly):
    return cw(poly)[::-1]


def on_segment(p, a, b):
    """p strictly between a and b on the segment ab."""
    (px, py), (ax, ay), (bx, by) = p, a, b
    if (bx - ax) * (py - ay) - (by - ay) * (px - ax) != 0:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    return 0 < dot < (bx - ax) ** 2 + (by - ay) ** 2


def point_in_poly(p, poly):
    x, y = p
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / float(dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def segments_cross(a, b, c, d):
    """Proper crossing (interiors intersect at a single point)."""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (v > 0) - (v < 0)
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


@dataclass(eq=False)
class Sector:
    floor: int
    ceil: int
    ftex: str
    ctex: str
    light: int = 160
    special: int = 0
    tag: int = 0
    wall: str = "AMWALL1"        # its one-sided walls
    face_lower: str | None = None  # what neighbours see below: the edge of this raised floor
    face_upper: str | None = None  # what neighbours see above: the edge of this lowered ceiling
    role: str = "room"           # room | door | lift | window | pad | dummy
    key: str | None = None       # door: None, blue, yellow, red
    remote: bool = False         # door opened by a switch somewhere else (no DR special)
    low: int | None = None       # lift: bottom floor height
    name: str = ""
    dest: "Sector | None" = None  # teleport pad: where it sends you
    rings: list = field(default_factory=list)  # [outer (cw), holes (ccw)...]
    index: int = -1

    @property
    def outer(self):
        return self.rings[0]

    def contains(self, p):
        return point_in_poly(p, self.rings[0]) and not any(point_in_poly(p, h) for h in self.rings[1:])

    def floor_range(self):
        return (self.low, self.floor) if self.role == "lift" else (self.floor, self.floor)


@dataclass(eq=False)
class Line:
    v1: tuple
    v2: tuple
    front: Sector
    back: Sector | None = None
    flags: int = 0
    special: int = 0
    tag: int = 0
    # per side: upper, lower, mid, xoff, yoff
    sides: list = field(default_factory=lambda: [{}, {}])

    def flip(self):
        self.v1, self.v2 = self.v2, self.v1
        self.front, self.back = self.back, self.front
        self.sides.reverse()

    def length(self):
        return math.dist(self.v1, self.v2)


@dataclass
class Thing:
    x: int
    y: int
    type: int
    angle: int = 0
    flags: int = ALL


class Map:
    def __init__(self, lumpname, title=""):
        self.lumpname = lumpname
        self.title = title
        self.sectors: list[Sector] = []
        self.things: list[Thing] = []
        self.overrides = []   # (a, b, props)
        self.switches = []    # (a, b, special, target sector) -> remote doors etc.
        self.scrollers = []   # (target, dx, dy, special)
        self.boss_opens = []  # sectors a UMAPINFO bossaction opens (counted as openable)
        self.lines: list[Line] = []
        self._tag = 0
        self._dummy_x = None

    # ------------------------------------------------------------ building
    def new_tag(self):
        self._tag += 1
        return self._tag

    def sector(self, poly, holes=(), **props):
        s = Sector(**props)
        s.rings = [cw(poly)] + [ccw(h) for h in holes]
        self.sectors.append(s)
        return s

    def room(self, poly, floor=0, ceil=128, ftex="AMTERRA", ctex="AMCEIL", **props):
        return self.sector(poly, floor=floor, ceil=ceil, ftex=ftex, ctex=ctex, **props)

    def inset(self, parent, poly, **props):
        """A sector inside another one (a desk, platform, pillar, pool): a hole in the
        parent filled by the new sector. Missing props copy the parent's."""
        parent.rings.append(ccw(poly))
        base = dict(floor=parent.floor, ceil=parent.ceil, ftex=parent.ftex, ctex=parent.ctex,
                    light=parent.light, wall=parent.wall)
        base.update(props)
        return self.sector(poly, **base)

    def pillar(self, parent, poly):
        """A solid column: a hole in the parent with nothing in it."""
        parent.rings.append(ccw(poly))

    def door(self, poly, floor, tex="AMDOOR1", key=None, light=None, remote=False, tag=0, ceil=None,
             parent=None):
        """A door sector (closed: ceiling = floor). Put it between two rooms so it shares an
        edge with each, or inside one (parent=room). key: None, 'blue', 'yellow' or 'red'."""
        if parent is not None:
            parent.rings.append(ccw(poly))
        d = self.sector(poly, floor=floor, ceil=floor if ceil is None else ceil, ftex="AMTERRA",
                        ctex="AMCEIL", light=light or 144, role="door", key=key, remote=remote,
                        face_upper=tex, wall="DOORTRAK", tag=tag)
        return d

    def lift(self, poly, low, high, ceil, tex="AMLIFT", ftex="AMLIFTF", light=160):
        """A lift resting at the top (high); use it from below to ride it."""
        return self.sector(poly, floor=high, ceil=ceil, ftex=ftex, ctex="AMCEIL", light=light,
                           role="lift", low=low, face_lower=tex, wall=tex, tag=self.new_tag())

    def window(self, poly, sill, lintel, light=160, ftex="AMTERRA", ctex="AMCEIL", wall="AMWALL1"):
        """A window between two areas: you can see and shoot through, not walk."""
        return self.sector(poly, floor=sill, ceil=lintel, ftex=ftex, ctex=ctex, light=light,
                           role="window", face_lower=wall, face_upper=wall, wall=wall)

    def teleport(self, pad_poly, parent, dest_sector, dest_xy, dest_angle=0, ftex="GATE1"):
        """A teleport pad inside `parent` that sends you to dest_xy in dest_sector."""
        if not dest_sector.tag:
            dest_sector.tag = self.new_tag()
        pad = self.inset(parent, pad_poly, ftex=ftex, role="pad", light=max(parent.light, 192))
        pad.dest = dest_sector  # build() gives its edges special 97 tagged to dest
        self.thing(*dest_xy, 14, dest_angle)
        return pad

    def scroll(self, target, dx, dy, special=253):
        """Boom scroller on a sector (253 scroll floor + carry things, 250 ceiling,
        251 floor texture only). dx, dy: speed in map units per tic."""
        if not target.tag:
            target.tag = self.new_tag()
        self.scrollers.append((target, dx, dy, special))

    def line(self, a, b, **props):
        """Override properties of the line(s) on segment a-b: special, tag, flags (added),
        upper/lower/mid/xoff/yoff (front side), back={...} (back side), front=Sector."""
        self.overrides.append((tuple(a), tuple(b), props))

    def wall(self, a, b, tex, **props):
        """Retexture the one-sided walls on segment a-b (two-sided lines there are left alone)."""
        self.overrides.append((tuple(a), tuple(b), dict(mid=tex, only_walls=True, **props)))

    def switch(self, a, b, special, target, tex=None):
        """A switch on wall a-b that triggers `special` on the target sector (e.g. 103 S1
        open door, 23 S1 floor lower, 62 SR lift)."""
        targets = target if isinstance(target, (list, tuple)) else [target]
        tag = next((t.tag for t in targets if t.tag), 0) or self.new_tag()
        for t in targets:
            t.tag = tag
        props = dict(special=special, tag=tag)
        if tex:
            props["mid"] = tex
        self.overrides.append((tuple(a), tuple(b), props))
        for t in targets:
            self.switches.append((tuple(a), tuple(b), special, t))

    def thing(self, x, y, type, angle=0, flags=ALL):
        self.things.append(Thing(int(x), int(y), type, angle, flags))

    def things_at(self, type, points, angle=0, flags=ALL):
        for x, y in points:
            self.thing(x, y, type, angle, flags)

    # ------------------------------------------------------------ geometry -> lines
    def _dummy_sector(self, poly, **props):
        return self.sector(poly, floor=0, ceil=8, ftex="AMTERRA", ctex="AMCEIL", role="dummy", **props)

    def _make_scroll_controls(self):
        """Boom scrollers take speed and direction from a control line's vector (length/32
        units per tic). Each gets a tiny closed sector outside the map."""
        if not self.scrollers:
            return []
        xs = [p[0] for s in self.sectors for p in s.outer]
        ys = [p[1] for s in self.sectors for p in s.outer]
        x, y = max(xs) + 512, min(ys)
        controls = []
        for target, dx, dy, special in self.scrollers:
            vx, vy = round(dx * 32), round(dy * 32)
            n = math.hypot(vx, vy) or 1
            # right-hand normal makes [p0, p1, p2, p3] clockwise, so p0->p1 keeps its direction
            nx, ny = round(vy / n * 32), round(-vx / n * 32)
            p0 = (x, y)
            p1 = (x + vx, y + vy)
            poly = [p0, p1, (p1[0] + nx, p1[1] + ny), (p0[0] + nx, p0[1] + ny)]
            if area2(poly) >= 0:
                raise ValueError("scroller control polygon not clockwise")
            self._dummy_sector(poly)
            controls.append((p0, p1, special, target.tag))
            y += 128 + abs(vy) + abs(ny)
        return controls

    def build(self):
        controls = self._make_scroll_controls()
        for i, s in enumerate(self.sectors):
            s.index = i
        verts = {p for s in self.sectors for r in s.rings for p in r}
        # override/switch endpoints split the walls they sit on
        verts |= {p for a, b, _ in self.overrides for p in (a, b)}
        verts = sorted(verts)
        # directed edges, split wherever another vertex lies on them (T-junctions)
        claims = defaultdict(list)
        for s in self.sectors:
            for ring in s.rings:
                for a, b in zip(ring, ring[1:] + ring[:1]):
                    minx, maxx = sorted((a[0], b[0]))
                    miny, maxy = sorted((a[1], b[1]))
                    mids = [v for v in verts if minx <= v[0] <= maxx and miny <= v[1] <= maxy
                            and on_segment(v, a, b)]
                    mids.sort(key=lambda v: (v[0] - a[0]) ** 2 + (v[1] - a[1]) ** 2)
                    pts = [a] + mids + [b]
                    for p, q in zip(pts, pts[1:]):
                        claims[(p, q)].append(s)
        # A sector that has an edge both ways (an inset touching its parent's outer wall)
        # cancels it, leaving the edge to the inset and its other neighbour.
        edges = {}
        for (p, q), owners in claims.items():
            rest = [o for o in owners if o not in claims.get((q, p), ())]
            if len(rest) > 1:
                raise ValueError(f"{self.lumpname}: sectors overlap along {p}-{q}")
            if rest:
                edges[(p, q)] = rest[0]
        lines = []
        done = set()
        for (p, q), s in edges.items():
            if (p, q) in done:
                continue
            t = edges.get((q, p))
            done.add((p, q))
            if t is not None:
                done.add((q, p))
                if t is s:
                    continue  # an edge inside one sector (e.g. touching holes): no line
                lines.append(Line(p, q, s, t, TWO_SIDED))
            else:
                lines.append(Line(p, q, s, None, IMPASSABLE))
        self.lines = lines
        self._apply_roles()
        self._apply_textures()
        for p0, p1, special, tag in controls:
            self._override(p0, p1, dict(special=special, tag=tag))
        for a, b, props in self.overrides:
            self._override(a, b, props)
        return self

    def _lines_on(self, a, b):
        return [l for l in self.lines
                if (l.v1 == a or on_segment(l.v1, a, b) or l.v1 == b)
                and (l.v2 == a or on_segment(l.v2, a, b) or l.v2 == b)]

    def _override(self, a, b, props):
        found = self._lines_on(a, b)
        if not found:
            raise ValueError(f"{self.lumpname}: no line on {a}-{b}")
        props = dict(props)
        if props.pop("only_walls", False):
            found = [l for l in found if l.back is None]
        if props.pop("only_twosided", False):
            found = [l for l in found if l.back is not None]
            if not found:
                return
        want_front = props.pop("front", None)
        back = props.pop("back", None)
        for l in found:
            if want_front is not None and l.front is not want_front:
                if l.back is want_front:
                    l.flip()
                else:
                    raise ValueError(f"{self.lumpname}: {a}-{b} doesn't border that sector")
            for k, v in props.items():
                if k == "flags":
                    l.flags |= v
                elif k == "clearflags":
                    l.flags &= ~v
                elif k in ("special", "tag"):
                    setattr(l, k, v)
                else:
                    l.sides[0][k] = v
            if back:
                l.sides[1].update(back)

    def _apply_roles(self):
        for l in self.lines:
            if l.back is None:
                continue
            roles = (l.front.role, l.back.role)
            # door: front = the room you open it from, back = the door
            if "door" in roles:
                door = l.front if l.front.role == "door" else l.back
                other = l.back if door is l.front else l.front
                if other.role == "door":
                    continue
                if l.front is door:
                    l.flip()
                if not door.remote:
                    l.special = KEY_DOOR[door.key]
            elif "lift" in roles:
                lift = l.front if l.front.role == "lift" else l.back
                other = l.back if lift is l.front else l.front
                if other.floor < lift.floor and other.role != "lift":
                    if l.front is lift:
                        l.flip()
                    l.special, l.tag = 62, lift.tag  # SR: use the lift's side from below
                elif other.role != "lift":
                    l.special, l.tag = 88, lift.tag  # WR: step on it from the top to ride down
            elif "pad" in roles:
                pad = l.front if l.front.role == "pad" else l.back
                if l.front is pad:
                    l.flip()  # teleport lines only fire when crossed from the front
                l.special, l.tag = 97, pad.dest.tag
            if "window" in roles:
                l.flags |= IMPASSABLE | BLOCK_MONSTERS

    def _apply_textures(self):
        for l in self.lines:
            for side, (me, other) in enumerate(((l.front, l.back), (l.back, l.front))):
                if me is None:
                    continue
                d = l.sides[side]
                # world-aligned x offset so split walls tile continuously
                v1, v2 = (l.v1, l.v2) if side == 0 else (l.v2, l.v1)
                ln = math.dist(v1, v2) or 1
                d.setdefault("xoff", round((v1[0] * (v2[0] - v1[0]) + v1[1] * (v2[1] - v1[1])) / ln))
                if other is None:
                    d.setdefault("mid", me.wall)
                    if me.role == "door":
                        l.flags |= LOWER_UNPEGGED
                    continue
                if me.ceil > other.ceil or other.role == "door":
                    d.setdefault("upper", other.face_upper or me.wall)
                if me.floor < other.floor or "lift" in (me.role, other.role):
                    fallback = other.wall if me.role == "lift" else me.wall
                    d.setdefault("lower", other.face_lower or fallback)

    # ------------------------------------------------------------ output
    def lumps(self):
        """-> [(name, data)] map lumps without nodes (a node builder adds those)."""
        if not self.lines:
            self.build()
        vidx = {}
        verts = []
        for l in self.lines:
            for v in (l.v1, l.v2):
                if v not in vidx:
                    vidx[v] = len(verts)
                    verts.append(v)
        sides = []
        ldata = bytearray()
        for l in self.lines:
            sn = []
            for side, sec in ((0, l.front), (1, l.back)):
                if sec is None:
                    sn.append(0xFFFF)
                    continue
                d = l.sides[side]
                sn.append(len(sides))
                sides.append(struct.pack("<hh8s8s8sH", int(d.get("xoff", 0)) % 1024,
                                         int(d.get("yoff", 0)), _tex(d.get("upper")), _tex(d.get("lower")),
                                         _tex(d.get("mid")), sec.index))
            ldata += struct.pack("<HHHHHHH", vidx[l.v1], vidx[l.v2], l.flags, l.special, l.tag, sn[0], sn[1])
        sdata = b"".join(struct.pack("<hh8s8shhh", s.floor, s.ceil, _tex(s.ftex), _tex(s.ctex),
                                     s.light, s.special, s.tag) for s in self.sectors)
        tdata = b"".join(struct.pack("<hhhhh", t.x, t.y, t.angle, t.type, t.flags) for t in self.things)
        vdata = b"".join(struct.pack("<hh", x, y) for x, y in verts)
        return [(self.lumpname, b""), ("THINGS", tdata), ("LINEDEFS", bytes(ldata)),
                ("SIDEDEFS", b"".join(sides)), ("VERTEXES", vdata), ("SECTORS", sdata)]

    # ------------------------------------------------------------ checks
    def sector_at(self, p):
        hits = [s for s in self.sectors if s.role != "dummy" and s.contains(p)]
        return hits[0] if hits else None

    def validate(self):
        """Static checks. Returns a report dict; raises ValueError on hard errors."""
        if not self.lines:
            self.build()
        errors, warnings = [], []
        # crossing edges between different sectors' rings mean overlapping sectors
        segs = [(a, b, s) for s in self.sectors for r in s.rings for a, b in zip(r, r[1:] + r[:1])]
        for i, (a, b, s) in enumerate(segs):
            for c, d, t in segs[i + 1:]:
                if segments_cross(a, b, c, d):
                    errors.append(f"edges cross: {a}-{b} and {c}-{d}")
        # a sector drawn on top of another (forgot to make it an inset)
        for s in self.sectors:
            if s.role == "dummy":
                continue
            cx = sum(p[0] for p in s.outer) / len(s.outer)
            cy = sum(p[1] for p in s.outer) / len(s.outer)
            if not s.contains((cx, cy)):
                continue
            for o in self.sectors:
                if o is not s and o.role != "dummy" and o.contains((cx, cy)):
                    errors.append(f"sectors overlap: {s.name or s.index} and {o.name or o.index} at {(cx, cy)}")
        for x, y in (v for l in self.lines for v in (l.v1, l.v2)):
            if not (-32000 < x < 32000 and -32000 < y < 32000):
                errors.append(f"vertex out of range {(x, y)}")
        starts = [t for t in self.things if t.type == 1]
        if len(starts) != 1:
            errors.append(f"need exactly one player 1 start, found {len(starts)}")
        for t in self.things:
            s = self.sector_at((t.x, t.y))
            if s is None:
                errors.append(f"thing {t.type} at {(t.x, t.y)} is outside the map")
                continue
            r, h = THING_SIZE.get(t.type, (16, 16))
            if t.type in MONSTERS or t.type in (1, 2, 3, 4, 11):
                if s.ceil - s.floor < h and s.role != "door":
                    errors.append(f"thing {t.type} at {(t.x, t.y)} doesn't fit under the ceiling")
                def blocks(l):
                    if l.back is None or l.flags & IMPASSABLE:
                        return True
                    if "door" in (l.front.role, l.back.role):
                        return False
                    hi = max(l.front.floor, l.back.floor)
                    return hi > s.floor + 24 or min(l.front.ceil, l.back.ceil) - hi < h
                for l in self.lines:
                    if seg_dist((t.x, t.y), l.v1, l.v2) < r and blocks(l):
                        errors.append(f"thing {t.type} at {(t.x, t.y)} is stuck in the wall {l.v1}-{l.v2}")
                        break
        report = self._reachability(errors, warnings)
        report["errors"], report["warnings"] = errors, warnings
        if errors:
            raise ValueError(f"{self.lumpname}:\n  " + "\n  ".join(errors[:40]))
        return report

    def _reachability(self, errors, warnings):
        start = next((t for t in self.things if t.type == 1), None)
        if start is None:
            return {}
        s0 = self.sector_at((start.x, start.y))
        adj = defaultdict(list)  # sector -> [(neighbour, requirement or None)]

        def door_ceil(d):
            ns = [l.back if l.front is d else l.front for l in self.lines if d in (l.front, l.back) and l.back]
            return min((n.ceil for n in ns if n is not d), default=d.ceil) - 4

        def ceil_of(s):
            return door_ceil(s) if s.role == "door" else s.ceil

        for l in self.lines:
            if l.back is None or l.flags & IMPASSABLE:
                continue
            for a, b in ((l.front, l.back), (l.back, l.front)):
                (alo, ahi), (blo, bhi) = a.floor_range(), b.floor_range()
                if blo > ahi + 24:
                    continue
                if min(ceil_of(a), ceil_of(b)) - max(alo, blo) < 56:
                    continue
                req = None
                for s in (a, b):
                    if s.role == "door":
                        if s.remote and s in self.boss_opens:
                            req = None
                        elif s.remote:
                            req = ("switch", s.index)
                        elif s.key:
                            req = ("key", s.key)
                adj[a.index].append((b.index, req))
        for l in self.lines:
            if l.special in TELEPORT_SPECIALS:
                dest = next((s for s in self.sectors if s.tag == l.tag and s.role != "pad"), None)
                if dest:
                    adj[l.front.index].append((dest.index, None))
        keys_at = defaultdict(set)
        for t in self.things:
            for k, types in KEY_THINGS.items():
                if t.type in types:
                    s = self.sector_at((t.x, t.y))
                    if s:
                        keys_at[s.index].add(k)
        switch_front = defaultdict(list)  # target sector index -> sectors you press it from
        for a, b, special, target in self.switches:
            for l in self._lines_on(a, b):
                switch_front[target.index].append(l.front.index)

        reached, have = set(), set()
        changed = True
        while changed:
            changed = False
            q = deque([s0.index]) if s0.index not in reached else deque(reached)
            seen = set(reached) | {s0.index}
            while q:
                u = q.popleft()
                if u not in reached:
                    reached.add(u)
                    changed = True
                for k in keys_at.get(u, ()):
                    if k not in have:
                        have.add(k)
                        changed = True
                for v, req in adj.get(u, ()):
                    if v in seen:
                        continue
                    if req and req[0] == "key" and req[1] not in have:
                        continue
                    if req and req[0] == "switch" and not any(f in reached for f in switch_front.get(req[1], ())):
                        continue
                    seen.add(v)
                    q.append(v)
        exits = [l for l in self.lines if l.special in EXIT_SPECIALS]
        if not exits:
            errors.append("no exit line")
        elif not any(l.front.index in reached or (l.back and l.back.index in reached) for l in exits):
            errors.append("the exit can't be reached from the start")
        playable = [s for s in self.sectors if s.role not in ("dummy", "window")]
        unreached = [s for s in playable if s.index not in reached and s.role != "door" and s.name != "block"]
        for s in unreached:
            warnings.append(f"sector {s.index} {s.name or ''} at {s.outer[0]} can't be reached")
        secrets = [s for s in self.sectors if s.special == 9]
        for s in secrets:
            if s.index not in reached:
                warnings.append(f"secret sector {s.index} can't be reached")
        monsters = {k: sum(1 for t in self.things if t.type in MONSTERS and t.flags & bit)
                    for k, bit in (("easy", EASY), ("medium", MEDIUM), ("hard", HARD))}
        return {"keys": sorted(have), "monsters": monsters, "secrets": len(secrets),
                "sectors": len(playable), "lines": len(self.lines), "things": len(self.things)}

    # ------------------------------------------------------------ preview
    def preview(self, path, scale=None):
        from PIL import Image, ImageDraw
        pts = [p for s in self.sectors if s.role != "dummy" for p in s.outer]
        minx, maxx = min(p[0] for p in pts) - 64, max(p[0] for p in pts) + 64
        miny, maxy = min(p[1] for p in pts) - 64, max(p[1] for p in pts) + 64
        scale = scale or min(1.0, 1400 / max(maxx - minx, maxy - miny))
        W, H = int((maxx - minx) * scale), int((maxy - miny) * scale)
        img = Image.new("RGB", (W, H), (16, 16, 20))
        dr = ImageDraw.Draw(img)

        def xy(p):
            return ((p[0] - minx) * scale, (maxy - p[1]) * scale)

        fl = [s.floor for s in self.sectors if s.role != "dummy"]
        lo, hi = min(fl), max(fl)
        for s in self.sectors:
            if s.role == "dummy":
                continue
            k = (s.floor - lo) / ((hi - lo) or 1)
            col = (40 + int(60 * k), 50 + int(90 * k), 70 + int(40 * k))
            if s.ctex == SKY:
                col = (col[0], col[1] + 30, col[2] - 20)
            if s.role == "door":
                col = (120, 90, 40) if not s.key else {"blue": (40, 60, 200), "yellow": (190, 170, 30), "red": (190, 40, 40)}[s.key]
            if s.role == "lift":
                col = (90, 160, 90)
            if s.special == 9:
                col = (150, 60, 150)
            dr.polygon([xy(p) for p in s.outer], fill=col)
            for h in s.rings[1:]:
                dr.polygon([xy(p) for p in h], fill=(16, 16, 20))
        for l in self.lines:
            if l.front.role == "dummy":
                continue
            c = (230, 230, 230) if l.back is None else (110, 110, 120)
            if l.special:
                c = (255, 80, 80) if l.special in EXIT_SPECIALS else (255, 200, 0)
            dr.line([xy(l.v1), xy(l.v2)], fill=c, width=2 if l.back is None or l.special else 1)
        for t in self.things:
            x, y = xy((t.x, t.y))
            c = (0, 255, 0) if t.type == 1 else (255, 60, 60) if t.type in MONSTERS else \
                (80, 160, 255) if any(t.type in v for v in KEY_THINGS.values()) else (200, 200, 120)
            r = 5 if t.type == 1 or any(t.type in v for v in KEY_THINGS.values()) else 3
            dr.ellipse([x - r, y - r, x + r, y + r], fill=c)
        img.save(path)
        return path


def _tex(name):
    return (name or "-").upper().encode("ascii")[:8].ljust(8, b"\0")
