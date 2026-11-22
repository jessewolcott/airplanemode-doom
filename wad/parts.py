"""Airport furniture built from sectors, shared by the Layover maps."""
from mapkit import IMPASSABLE, LOWER_UNPEGGED, BLOCK_MONSTERS, rect


def sign(m, room, x, y, tex, along="x", drop=32, length=128):
    """A sign hung from the ceiling: a thin sector whose lowered ceiling shows `tex` on
    both faces. (x, y) is the centre; along: the direction the sign runs."""
    h = length // 2
    r = rect(x - h, y - 4, x + h, y + 4) if along == "x" else rect(x - 4, y - h, x + 4, y + h)
    return m.inset(room, r, ceil=room.ceil - drop, face_upper=tex, ctex="AMSTEEL")


def board(m, room, x, y, along="x"):
    """A departures board (hung, 128x64)."""
    return sign(m, room, x, y, "AMBOARD", along, drop=64)


def block(m, room, x1, y1, x2, y2, height, face, top="AMSTEEL", **props):
    """A raised block (desk, seats, crate, vehicle): an inset with a higher floor."""
    props.setdefault("name", "block")   # not meant to be walked on: no "unreachable" warning
    return m.inset(room, rect(x1, y1, x2, y2), floor=room.floor + height, ftex=top, face_lower=face, **props)


def desk(m, room, x1, y1, x2, y2):
    return block(m, room, x1, y1, x2, y2, 40, "AMDESK")


def seats(m, room, x1, y1, x2, y2):
    return block(m, room, x1, y1, x2, y2, 32, "AMSEAT", top="AMCARPT")


def crates(m, room, x1, y1, x2, y2, height=64):
    return block(m, room, x1, y1, x2, y2, height, "CRATE1", top="CRATOP1")


def lights(m, room, points, size=64, light=None):
    """Bright ceiling panels (inset sectors with the light flat)."""
    out = []
    for x, y in points:
        out.append(m.inset(room, rect(x - size // 2, y - size // 2, x + size // 2, y + size // 2),
                           ctex="AMLITE", light=light or min(255, room.light + 32)))
    return out


def rope(m, room, x1, y1, x2, y2):
    """Queue barrier: a thin strip whose edges carry a see-through rope texture and block
    walking (but not shots)."""
    s = m.inset(room, rect(x1, y1, x2, y2), name="block")
    pts = s.outer
    for a, b in zip(pts, pts[1:] + pts[:1]):
        m.line(a, b, mid="AMROPE", flags=IMPASSABLE | BLOCK_MONSTERS | LOWER_UNPEGGED,
               back={"mid": "AMROPE"}, only_twosided=True)
    return s


def grid(x1, y1, x2, y2, step):
    return [(x, y) for x in range(x1, x2 + 1, step) for y in range(y1, y2 + 1, step)]


def octagon(cx, cy, r):
    import math
    return [(cx + round(r * math.cos(math.radians(22.5 + 45 * k))),
             cy + round(r * math.sin(math.radians(22.5 + 45 * k)))) for k in range(8)]


def carousel(m, room, cx, cy, r_out=224, r_in=128):
    """Baggage carousel: a moving belt ring (it carries you) around a raised centre."""
    ring = m.inset(room, octagon(cx, cy, r_out), floor=room.floor + 24, ftex="AMBELT",
                   face_lower="AMBELTS", light=room.light + 16)
    m.inset(ring, octagon(cx, cy, r_in), floor=room.floor + 64, ftex="AMSTEEL",
            face_lower="AMBAGW", name="block")
    m.scroll(ring, 0, 2)
    return ring
