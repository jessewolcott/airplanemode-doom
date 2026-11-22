"""Read and write Doom WAD files, and convert images to Doom's picture and flat formats."""
import struct
from pathlib import Path


def read_wad(path):
    """-> (kind, [(name, bytes), ...]) where kind is 'IWAD' or 'PWAD'."""
    data = Path(path).read_bytes()
    kind, count, offset = struct.unpack_from("<4sii", data, 0)
    lumps = []
    for i in range(count):
        pos, size, name = struct.unpack_from("<ii8s", data, offset + 16 * i)
        lumps.append((name.rstrip(b"\0").decode("ascii", "replace").upper(), data[pos:pos + size]))
    return kind.decode(), lumps


def write_wad(path, lumps, kind="PWAD"):
    body = bytearray()
    directory = bytearray()
    pos = 12
    for name, data in lumps:
        if len(name) > 8:
            raise ValueError(f"lump name too long: {name}")
        directory += struct.pack("<ii8s", pos, len(data), name.upper().encode("ascii"))
        body += data
        pos += len(data)
    out = struct.pack("<4sii", kind.encode(), len(lumps), 12 + len(body)) + bytes(body) + bytes(directory)
    Path(path).write_bytes(out)


def lump(lumps, name):
    """The last lump called name (later lumps override earlier ones, like the engine)."""
    for n, d in reversed(lumps):
        if n == name:
            return d
    raise KeyError(name)


# ---------------------------------------------------------------- palette
class Palette:
    """Nearest-colour lookup into PLAYPAL's first palette."""

    def __init__(self, playpal):
        self.rgb = [tuple(playpal[i * 3:i * 3 + 3]) for i in range(256)]
        self.cache = {}

    def index(self, r, g, b):
        key = (r, g, b)
        hit = self.cache.get(key)
        if hit is None:
            best, hit = 1 << 30, 0
            for i, (pr, pg, pb) in enumerate(self.rgb):
                # weighted distance: eyes care more about green
                d = 3 * (r - pr) ** 2 + 4 * (g - pg) ** 2 + 2 * (b - pb) ** 2
                if d < best:
                    best, hit = d, i
                    if d == 0:
                        break
            self.cache[key] = hit
        return hit


def to_picture(img, pal, left=None, top=None):
    """PIL RGBA image -> Doom picture lump (columns of posts). Alpha < 128 is transparent."""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    left = w // 2 if left is None else left
    top = h - 4 if top is None else top
    header = struct.pack("<hhhh", w, h, left, top)
    columns = []
    for x in range(w):
        col = bytearray()
        y = 0
        while y < h:
            if px[x, y][3] < 128:
                y += 1
                continue
            start = y
            run = []
            while y < h and px[x, y][3] >= 128 and len(run) < 128:
                r, g, b, _ = px[x, y]
                run.append(pal.index(r, g, b))
                y += 1
            # Posts start at row <= 254 (255 ends the column). Tall pictures would need
            # DeePsea-style relative offsets; ours are at most 128 high.
            col += bytes([start, len(run), run[0]]) + bytes(run) + bytes([run[-1]])
        col += b"\xff"
        columns.append(bytes(col))
    offsets = []
    pos = 8 + 4 * w
    for c in columns:
        offsets.append(pos)
        pos += len(c)
    return header + struct.pack(f"<{w}i", *offsets) + b"".join(columns)


def to_flat(img, pal):
    """64x64 PIL image -> 4096-byte flat."""
    img = img.convert("RGB").resize((64, 64))
    px = img.load()
    return bytes(pal.index(*px[x, y]) for y in range(64) for x in range(64))


def from_flat(data, pal):
    """Flat -> PIL RGB image (for previews)."""
    from PIL import Image
    img = Image.new("RGB", (64, 64))
    img.putdata([pal.rgb[b] for b in data[:4096]])
    return img


# ---------------------------------------------------------------- textures
def parse_pnames(data):
    n = struct.unpack_from("<i", data)[0]
    return [data[4 + 8 * i:12 + 8 * i].rstrip(b"\0").decode("ascii").upper() for i in range(n)]


def build_pnames(names):
    return struct.pack("<i", len(names)) + b"".join(n.encode("ascii").ljust(8, b"\0") for n in names)


def parse_texture1(data):
    """-> [(name, width, height, [(xoff, yoff, patch_index), ...]), ...]"""
    n = struct.unpack_from("<i", data)[0]
    offs = struct.unpack_from(f"<{n}i", data, 4)
    out = []
    for o in offs:
        name = data[o:o + 8].rstrip(b"\0").decode("ascii").upper()
        _, w, h, _, npatch = struct.unpack_from("<ihhih", data, o + 8)
        patches = [struct.unpack_from("<hhhhh", data, o + 22 + 10 * i)[:3] for i in range(npatch)]
        out.append((name, w, h, patches))
    return out


def build_texture1(textures):
    entries = []
    for name, w, h, patches in textures:
        e = name.encode("ascii").ljust(8, b"\0") + struct.pack("<ihhih", 0, w, h, 0, len(patches))
        for xo, yo, idx in patches:
            e += struct.pack("<hhhhh", xo, yo, idx, 1, 0)
        entries.append(e)
    head = 4 + 4 * len(entries)
    offs, pos = [], head
    for e in entries:
        offs.append(pos)
        pos += len(e)
    return struct.pack("<i", len(entries)) + struct.pack(f"<{len(offs)}i", *offs) + b"".join(entries)
