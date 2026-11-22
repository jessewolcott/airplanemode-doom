"""Tests for the WAD tools. Run: python test_wad.py [freedoom2.wad]

Without the IWAD argument, the palette-dependent tests use a grey ramp instead.
"""
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import wadlib  # noqa: E402
from mapkit import Map, rect, TWO_SIDED, IMPASSABLE  # noqa: E402

IWAD = sys.argv.pop(1) if len(sys.argv) > 1 and sys.argv[1].endswith(".wad") else None


def palette():
    if IWAD:
        return wadlib.Palette(wadlib.lump(wadlib.read_wad(IWAD)[1], "PLAYPAL"))
    return wadlib.Palette(bytes(v for i in range(256) for v in (i, i, i)))


def decode_picture(data):
    """Doom picture -> {(x, y): index} (for checking our encoder)."""
    w, h, _, _ = struct.unpack_from("<hhhh", data)
    offs = struct.unpack_from(f"<{w}i", data, 8)
    px = {}
    for x, o in enumerate(offs):
        while data[o] != 0xFF:
            top, n = data[o], data[o + 1]
            for i in range(n):
                px[(x, top + i)] = data[o + 3 + i]
            o += n + 4
    return w, h, px


def two_rooms_and_door(key=None, with_exit=True):
    m = Map("MAP01", "test")
    a = m.room(rect(0, 0, 256, 256), floor=0, ceil=128)
    b = m.room(rect(0, 272, 256, 528), floor=0, ceil=128)
    m.door(rect(96, 256, 160, 272), floor=0, key=key)
    if with_exit:
        m.line((256, 368), (256, 432), special=11, mid="SW1GRAY1")
    m.thing(128, 64, 1, 90)
    return m, a, b


class Wad(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.wad"
            wadlib.write_wad(p, [("A", b"hello"), ("B", b""), ("C", bytes(range(256)))])
            kind, lumps = wadlib.read_wad(p)
            self.assertEqual(kind, "PWAD")
            self.assertEqual([n for n, _ in lumps], ["A", "B", "C"])
            self.assertEqual(lumps[2][1], bytes(range(256)))

    def test_picture_transparency(self):
        from PIL import Image
        img = Image.new("RGBA", (4, 6), (0, 0, 0, 0))
        img.putpixel((1, 2), (255, 255, 255, 255))
        img.putpixel((1, 3), (255, 255, 255, 255))
        img.putpixel((3, 5), (0, 0, 0, 255))
        w, h, px = decode_picture(wadlib.to_picture(img, palette()))
        self.assertEqual((w, h), (4, 6))
        self.assertEqual(set(px), {(1, 2), (1, 3), (3, 5)})

    def test_texture_tables_roundtrip(self):
        tex = [("AMTEST", 128, 64, [(0, 0, 3)]), ("OTHER", 64, 128, [(0, 0, 1), (32, 0, 2)])]
        self.assertEqual(wadlib.parse_texture1(wadlib.build_texture1(tex)), tex)
        self.assertEqual(wadlib.parse_pnames(wadlib.build_pnames(["A", "BB"])), ["A", "BB"])


class Geometry(unittest.TestCase):
    def test_door_faces_rooms(self):
        m, a, b = two_rooms_and_door()
        m.build()
        door_lines = [l for l in m.lines if l.special == 1]
        self.assertEqual(len(door_lines), 2)
        for l in door_lines:
            self.assertEqual(l.back.role, "door")          # opened from the front: the room
            self.assertTrue(l.flags & TWO_SIDED)
            self.assertEqual(l.sides[0]["upper"], "AMDOOR1")

    def test_walls_split_at_shared_edges(self):
        m, a, b = two_rooms_and_door()
        m.build()
        top_of_a = [l for l in m.lines if l.v1[1] == 256 and l.v2[1] == 256]
        self.assertEqual(sorted(l.back is None for l in top_of_a), [False, True, True])
        self.assertTrue(all(l.flags & IMPASSABLE for l in top_of_a if l.back is None))

    def test_reachable_exit(self):
        m, *_ = two_rooms_and_door()
        self.assertEqual(m.validate()["errors"], [])

    def test_locked_exit_without_key_fails(self):
        m, *_ = two_rooms_and_door(key="blue")
        with self.assertRaisesRegex(ValueError, "exit can't be reached"):
            m.validate()

    def test_key_opens_the_way(self):
        m, *_ = two_rooms_and_door(key="blue")
        m.thing(200, 200, 5)
        self.assertIn("blue", m.validate()["keys"])

    def test_stuck_thing(self):
        m, *_ = two_rooms_and_door()
        m.thing(4, 100, 3001)
        with self.assertRaisesRegex(ValueError, "stuck"):
            m.validate()

    def test_overlap_detected(self):
        m = Map("MAP01")
        m.room(rect(0, 0, 256, 256))
        m.room(rect(128, 0, 384, 256))
        m.thing(64, 64, 1)
        with self.assertRaises(ValueError):
            m.build()
            m.validate()

    def test_sector_drawn_over_another(self):
        m = Map("MAP01")
        m.room(rect(0, 0, 512, 512))
        m.room(rect(128, 128, 256, 256))      # should have been an inset
        m.thing(64, 64, 1)
        with self.assertRaisesRegex(ValueError, "overlap"):
            m.validate()

    def test_inset_touching_parent_wall(self):
        m = Map("MAP01")
        a = m.room(rect(0, 0, 256, 256))
        m.inset(a, rect(0, 0, 64, 64), floor=32)   # in the corner
        m.build()
        self.assertFalse(any(l.front is l.back for l in m.lines))

    def test_scroller_control_direction(self):
        m, a, b = two_rooms_and_door()
        m.scroll(a, 0, 2)
        m.build()
        ctrl = [l for l in m.lines if l.special == 253]
        self.assertEqual(len(ctrl), 1)
        self.assertEqual((ctrl[0].v2[0] - ctrl[0].v1[0], ctrl[0].v2[1] - ctrl[0].v1[1]), (0, 64))
        self.assertEqual(ctrl[0].tag, a.tag)


class Maps(unittest.TestCase):
    def test_all_maps_validate(self):
        import build
        import importlib
        for name in build.MAPS:
            with self.subTest(name):
                m = importlib.import_module(f"maps.{name}").build()
                report = m.validate()
                self.assertGreater(report["monsters"]["hard"], report["monsters"]["easy"] - 1)
                self.assertEqual(sum(1 for t in m.things if t.type == 1), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
