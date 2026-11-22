"""Procedural airport textures and flats for Layover (all original, drawn in code).

Each function returns a PIL image. `TEXTURES` (walls, single patch each) and `FLATS` map
lump names to those functions. Colours get snapped to the Doom palette when the WAD is
built, so keep them simple and fairly saturated.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
MONO_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "C:/Windows/Fonts/consolab.ttf",
]


NAVY = (0, 0, 155)   # the Doom palette's blues are pure blue; muted blues turn grey


def font(size, mono=False):
    for p in (MONO_PATHS if mono else FONT_PATHS):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def noise(img, amount, seed):
    rnd = random.Random(seed)
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            d = rnd.randint(-amount, amount)
            px[x, y] = tuple(max(0, min(255, c + d)) for c in p[:3]) + tuple(p[3:])
    return img


def new(w, h, colour):
    return Image.new("RGB", (w, h), colour)


def centred(dr, box, text, fnt, fill):
    x1, y1, x2, y2 = box
    l, t, r, b = dr.textbbox((0, 0), text, font=fnt)
    dr.text(((x1 + x2 - (r - l)) / 2 - l, (y1 + y2 - (b - t)) / 2 - t), text, font=fnt, fill=fill)


# ------------------------------------------------------------------ walls
def wall_panels(seed=1, base=(178, 170, 156)):
    img = new(128, 128, base)
    dr = ImageDraw.Draw(img)
    for x in (0, 64):
        dr.line([(x, 0), (x, 127)], fill=(120, 114, 104))
        dr.line([(x + 1, 0), (x + 1, 127)], fill=(206, 198, 184))
    dr.line([(0, 0), (127, 0)], fill=(120, 114, 104))
    dr.rectangle([0, 116, 127, 127], fill=(96, 92, 86))  # skirting
    return noise(img, 6, seed)


def wall_stripe():
    img = wall_panels(2)
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 72, 127, 87], fill=NAVY)
    dr.rectangle([0, 90, 127, 93], fill=(220, 160, 30))
    return img


def wall_tile():
    img = new(64, 128, (210, 214, 214))
    dr = ImageDraw.Draw(img)
    for y in range(0, 128, 16):
        dr.line([(0, y), (63, y)], fill=(150, 156, 158))
    for x in range(0, 64, 16):
        dr.line([(x, 0), (x, 127)], fill=(150, 156, 158))
    return noise(img, 5, 3)


def sky_strip(img, top, bottom, seed):
    """Sky gradient with a few clouds, inside rows top..bottom."""
    dr = ImageDraw.Draw(img)
    w = img.size[0]
    for y in range(top, bottom):
        k = (y - top) / max(1, bottom - top)
        # Doom's palette has one sky ramp: periwinkle, from (83,83,255) to (231,231,255)
        v = int(83 + 140 * k)
        dr.line([(0, y), (w - 1, y)], fill=(v, v, 255))
    rnd = random.Random(seed)
    for _ in range(w // 24):
        cx, cy = rnd.randint(0, w), rnd.randint(top, top + (bottom - top) // 2)
        for _ in range(5):
            r = rnd.randint(4, 10)
            ox, oy = rnd.randint(-12, 12), rnd.randint(-3, 3)
            dr.ellipse([cx + ox - r * 2, cy + oy - r, cx + ox + r * 2, cy + oy + r], fill=(235, 240, 248))


def glass_wall():
    img = new(128, 128, (40, 50, 60))
    sky_strip(img, 0, 96, 7)
    dr = ImageDraw.Draw(img)
    # distant runway and a plane on approach
    dr.rectangle([0, 96, 127, 127], fill=(90, 96, 92))
    dr.line([(0, 100), (127, 100)], fill=(200, 200, 190))
    dr.polygon([(80, 40), (104, 37), (108, 39), (84, 42)], fill=(230, 230, 236))
    dr.polygon([(92, 39), (98, 33), (100, 39)], fill=(200, 200, 210))
    # mullions
    for x in (0, 63, 64, 127):
        dr.line([(x, 0), (x, 127)], fill=(60, 62, 66))
    for y in (0, 60, 61):
        dr.line([(0, y), (127, y)], fill=(60, 62, 66))
    dr.rectangle([0, 120, 127, 127], fill=(70, 70, 74))
    return img


def corrugated(base=(130, 134, 138)):
    img = new(128, 128, base)
    dr = ImageDraw.Draw(img)
    for x in range(0, 128, 8):
        dr.line([(x, 0), (x, 127)], fill=tuple(c - 40 for c in base))
        dr.line([(x + 3, 0), (x + 3, 127)], fill=tuple(min(255, c + 30) for c in base))
    return noise(img, 6, 4)


def concrete():
    img = new(128, 128, (118, 116, 110))
    noise(img, 14, 5)
    img = img.filter(ImageFilter.SMOOTH)
    dr = ImageDraw.Draw(img)
    dr.line([(0, 64), (127, 64)], fill=(90, 88, 84))
    for x in (0, 64):
        dr.line([(x, 0), (x, 127)], fill=(90, 88, 84))
    return img


def hazard():
    img = new(64, 32, (30, 30, 30))
    dr = ImageDraw.Draw(img)
    for x in range(-32, 64, 16):
        dr.polygon([(x, 32), (x + 8, 32), (x + 40, 0), (x + 32, 0)], fill=(230, 190, 20))
    return img


def glass_door():
    img = new(64, 128, (60, 64, 70))
    dr = ImageDraw.Draw(img)
    for x0 in (2, 33):
        dr.rectangle([x0, 4, x0 + 28, 123], fill=(0, 0, 107))
        dr.line([(x0 + 6, 10), (x0 + 16, 40)], fill=(143, 143, 255), width=2)
        dr.line([(x0 + 4, 50), (x0 + 12, 74)], fill=(83, 83, 255), width=1)
    dr.rectangle([0, 0, 63, 3], fill=(40, 40, 44))
    dr.line([(31, 0), (31, 127)], fill=(30, 30, 34), width=2)
    dr.rectangle([12, 60, 18, 70], fill=(200, 200, 200))
    dr.rectangle([45, 60, 51, 70], fill=(200, 200, 200))
    return img


def security_door(colour, label):
    img = new(64, 128, (120, 124, 128))
    dr = ImageDraw.Draw(img)
    dr.rectangle([2, 2, 61, 125], outline=(70, 72, 76), width=2)
    dr.rectangle([0, 50, 63, 70], fill=colour)
    centred(dr, (0, 50, 64, 70), label, font(11), (255, 255, 255))
    dr.rectangle([48, 78, 56, 92], fill=(40, 40, 40))   # card reader
    dr.rectangle([50, 80, 54, 83], fill=colour)
    return noise(img, 4, 8)


def lift_side():
    img = new(64, 128, (150, 154, 160))
    dr = ImageDraw.Draw(img)
    for y in range(0, 128, 32):
        dr.line([(0, y), (63, y)], fill=(100, 104, 110))
    for y in (12, 44, 76, 108):
        dr.polygon([(24, y + 10), (40, y + 10), (32, y)], fill=(230, 190, 20))
    return noise(img, 4, 9)


def desk_front():
    img = new(128, 64, (150, 110, 70))
    dr = ImageDraw.Draw(img)
    for y in range(0, 64, 4):
        dr.line([(0, y), (127, y)], fill=(140, 100, 62))
    dr.rectangle([0, 0, 127, 6], fill=(200, 200, 204))
    dr.rectangle([0, 18, 127, 30], fill=NAVY)
    centred(dr, (0, 18, 128, 30), "CONTRAIL", font(10), (255, 255, 255))
    return noise(img, 5, 10)


def seats():
    """Row of gate seats, 128x32 (the face of a 32-high seat block)."""
    img = new(128, 32, (70, 72, 76))
    dr = ImageDraw.Draw(img)
    for x in range(2, 128, 32):
        dr.rounded_rectangle([x, 0, x + 27, 22], radius=5, fill=(30, 40, 70))
        dr.rectangle([x + 2, 22, x + 25, 27], fill=(20, 26, 46))
    dr.rectangle([0, 28, 127, 31], fill=(50, 50, 54))
    return img


def queue_rope():
    """See-through queue barrier (posts and a belt), 64x40, for two-sided lines."""
    img = Image.new("RGBA", (64, 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for x in (0, 62):
        dr.rectangle([x, 4, x + 1, 39], fill=(190, 192, 196, 255))
    dr.rectangle([0, 6, 63, 9], fill=(30, 70, 200, 255))
    dr.rectangle([0, 36, 63, 39], fill=(0, 0, 0, 0))
    return img


def xray():
    img = new(128, 64, (200, 200, 196))
    dr = ImageDraw.Draw(img)
    dr.rectangle([24, 6, 104, 46], fill=(40, 40, 44))
    dr.rectangle([30, 12, 98, 40], fill=(90, 150, 200))
    for i in range(6):
        dr.rectangle([30 + i * 11, 12, 34 + i * 11, 40], fill=(70, 120, 170))
    dr.rectangle([0, 48, 127, 63], fill=(60, 60, 64))
    centred(dr, (0, 48, 128, 64), "X-RAY", font(10), (230, 190, 20))
    return img


def belt_side():
    img = new(64, 32, (160, 164, 170))
    dr = ImageDraw.Draw(img)
    for x in range(0, 64, 16):
        dr.line([(x, 0), (x, 31)], fill=(110, 114, 120))
    dr.rectangle([0, 0, 63, 4], fill=(40, 40, 40))
    return img


def sign(text, arrow=None, colour=(240, 200, 30), ink=(20, 20, 20)):
    """Hanging airport sign, 128x32 (hung from the ceiling as a sector's upper face)."""
    img = new(128, 32, colour)
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, 127, 31], outline=(40, 40, 40), width=2)
    x1, x2 = 4, 124
    if arrow:
        a = {"left": [(6, 16), (18, 6), (18, 26)], "right": [(122, 16), (110, 6), (110, 26)],
             "up": [(12, 5), (4, 20), (20, 20)], "down": [(12, 27), (4, 12), (20, 12)]}[arrow]
        dr.polygon(a, fill=ink)
        if arrow == "right":
            x2 = 108
        else:
            x1 = 22
    f = font(14)
    while dr.textbbox((0, 0), text, font=f)[2] > x2 - x1 and f.size > 8:
        f = font(f.size - 1)
    centred(dr, (x1, 2, x2, 30), text, f, ink)
    return img


def board():
    """Departures board, 128x64, hung like a sign."""
    img = new(128, 64, (12, 12, 16))
    dr = ImageDraw.Draw(img)
    f = font(8, mono=True)
    dr.rectangle([0, 0, 127, 9], fill=NAVY)
    dr.text((3, 0), "DEPARTURES", font=f, fill=(255, 255, 255))
    rows = [("CT101", "LISBON", "BOARD", (100, 230, 100)), ("CT208", "OSAKA", "DELAY", (240, 200, 30)),
            ("CT315", "NAIROBI", "CANCEL", (240, 60, 40)), ("CT422", "QUITO", "CANCEL", (240, 60, 40)),
            ("CT530", "OSLO", "CANCEL", (240, 60, 40))]
    for i, (fl, city, st, c) in enumerate(rows):
        y = 12 + i * 10
        dr.text((3, y), fl, font=f, fill=(240, 200, 30))
        dr.text((36, y), city, font=f, fill=(240, 200, 30))
        dr.text((92, y), st, font=f, fill=c)
    return img


def fuselage():
    img = new(256, 128, (232, 234, 238))
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 84, 255, 99], fill=NAVY)
    dr.rectangle([0, 100, 255, 103], fill=(220, 160, 30))
    for x in range(8, 256, 20):
        dr.rounded_rectangle([x, 46, x + 9, 60], radius=4, fill=(40, 50, 70))
    dr.rectangle([150, 30, 176, 82], outline=(150, 152, 160), width=2)  # cabin door
    centred(dr, (20, 8, 140, 36), "CONTRAIL", font(20), NAVY)
    dr.rectangle([0, 104, 255, 127], fill=(200, 202, 208))
    return noise(img, 3, 11)


def hangar_door():
    img = corrugated((150, 140, 110))
    big = Image.new("RGB", (256, 128))
    big.paste(img, (0, 0))
    big.paste(img, (128, 0))
    dr = ImageDraw.Draw(big)
    for x in (0, 64, 128, 192):
        dr.line([(x, 0), (x, 127)], fill=(70, 66, 52), width=2)
    centred(dr, (0, 8, 256, 30), "HANGAR 3", font(16), (40, 36, 28))
    return big


def tower_glass():
    img = new(128, 128, (31, 67, 23))
    dr = ImageDraw.Draw(img)
    for y in range(100):   # dark green glass, lighter towards the top
        dr.line([(0, y), (127, y)], fill=(55, 115, 43) if y < 30 else (31, 67, 23))
    for x in range(10, 128, 42):
        dr.line([(x, 90), (x + 24, 6)], fill=(75, 159, 63), width=3)
    for x in (0, 42, 85, 127):
        dr.line([(x, 0), (x, 127)], fill=(40, 44, 44), width=3)
    dr.rectangle([0, 100, 127, 127], fill=(70, 74, 76))
    return img


def poster():
    img = new(64, 128, (178, 170, 156))
    dr = ImageDraw.Draw(img)
    dr.rectangle([6, 10, 57, 100], fill=(240, 120, 40))
    dr.ellipse([18, 20, 46, 48], fill=(255, 220, 80))
    dr.polygon([(6, 100), (26, 60), (40, 80), (50, 66), (57, 100)], fill=(40, 90, 70))
    centred(dr, (6, 84, 58, 100), "HALCYON", font(9), (255, 255, 255))
    dr.rectangle([4, 8, 59, 102], outline=(60, 60, 60), width=2)
    return noise(img, 3, 13)


def duty_free():
    img = new(128, 128, (90, 60, 40))
    dr = ImageDraw.Draw(img)
    rnd = random.Random(14)
    for y in (28, 60, 92):
        dr.rectangle([0, y + 26, 127, y + 30], fill=(200, 200, 200))
        x = 4
        while x < 120:
            w = rnd.randint(6, 10)
            h = rnd.randint(14, 24)
            c = rnd.choice([(40, 120, 60), (160, 40, 40), (220, 180, 60), (60, 60, 160), (230, 230, 230)])
            dr.rectangle([x, y + 26 - h, x + w, y + 26], fill=c)
            dr.rectangle([x + w // 3, y + 20 - h, x + 2 * w // 3, y + 26 - h], fill=c)
            x += w + 3
    centred(dr, (0, 2, 128, 22), "DUTY FREE", font(14), (240, 200, 30))
    return img


def sky():
    img = new(256, 128, (0, 0, 0))
    sky_strip(img, 0, 128, 15)
    dr = ImageDraw.Draw(img)
    # far skyline along the bottom (the sky texture's lower edge sits at the horizon)
    rnd = random.Random(16)
    x = 0
    while x < 256:
        w, h = rnd.randint(8, 22), rnd.randint(6, 26)
        dr.rectangle([x, 127 - h, x + w, 127], fill=(70, 90, 120))
        x += w + rnd.randint(0, 6)
    dr.rectangle([180, 82, 186, 127], fill=(70, 90, 120))   # a control tower far away
    dr.rectangle([174, 76, 192, 84], fill=(70, 90, 120))
    return img


# ------------------------------------------------------------------ flats
def terrazzo():
    img = new(64, 64, (196, 192, 184))
    rnd = random.Random(20)
    dr = ImageDraw.Draw(img)
    for _ in range(140):
        x, y = rnd.randrange(64), rnd.randrange(64)
        dr.point((x, y), fill=rnd.choice([(120, 116, 110), (230, 228, 220), (150, 130, 110)]))
    dr.line([(0, 0), (63, 0)], fill=(160, 156, 150))
    dr.line([(0, 0), (0, 63)], fill=(160, 156, 150))
    return img


def carpet(base, dot):
    img = new(64, 64, base)
    dr = ImageDraw.Draw(img)
    for y in range(4, 64, 16):
        for x in range(4, 64, 16):
            dr.rectangle([x, y, x + 3, y + 3], fill=dot)
            dr.point((x + 9, y + 9), fill=dot)
    return noise(img, 6, 21)


def ceiling_tiles():
    img = new(64, 64, (210, 210, 206))
    dr = ImageDraw.Draw(img)
    dr.line([(0, 0), (63, 0)], fill=(150, 150, 146))
    dr.line([(0, 0), (0, 63)], fill=(150, 150, 146))
    dr.line([(0, 32), (63, 32)], fill=(150, 150, 146))
    dr.line([(32, 0), (32, 63)], fill=(150, 150, 146))
    return noise(img, 4, 22)


def light_panel():
    img = new(64, 64, (180, 180, 176))
    dr = ImageDraw.Draw(img)
    dr.rectangle([6, 6, 57, 57], fill=(255, 255, 240))
    return img


def belt():
    img = new(64, 64, (40, 40, 44))
    dr = ImageDraw.Draw(img)
    for y in range(0, 64, 8):
        dr.rectangle([0, y, 63, y + 2], fill=(70, 70, 76))
    return img


def walkway():
    img = new(64, 64, (120, 124, 130))
    dr = ImageDraw.Draw(img)
    for x in range(0, 64, 4):
        dr.line([(x, 0), (x, 63)], fill=(80, 84, 90))
    return img


def asphalt(line=None):
    img = new(64, 64, (70, 72, 74))
    noise(img, 10, 23)
    dr = ImageDraw.Draw(img)
    if line == "centre":
        dr.rectangle([28, 0, 35, 63], fill=(230, 190, 20))
    elif line == "runway":
        dr.rectangle([8, 0, 55, 31], fill=(230, 230, 226))
    return img


def diamond_plate():
    img = new(64, 64, (150, 154, 160))
    dr = ImageDraw.Draw(img)
    for y in range(0, 64, 8):
        for x in range((y // 8 % 2) * 4, 64, 8):
            dr.line([(x, y + 1), (x + 3, y + 4)], fill=(200, 204, 210))
    return img


def concrete_floor():
    img = new(64, 64, (128, 126, 120))
    return noise(img, 10, 24).filter(ImageFilter.SMOOTH)


def aircraft_skin():
    img = new(64, 64, (220, 222, 228))
    dr = ImageDraw.Draw(img)
    for x in range(0, 64, 16):
        dr.line([(x, 0), (x, 63)], fill=(190, 192, 198))
    return img


TEXTURES = {
    "AMWALL1": wall_panels,
    "AMWALL2": wall_stripe,
    "AMTILE": wall_tile,
    "AMGLASS": glass_wall,
    "AMBAGW": corrugated,
    "AMCONC": concrete,
    "AMHAZ": hazard,
    "AMDOOR1": glass_door,
    "AMDOORB": lambda: security_door((0, 0, 203), "STAFF"),
    "AMDOORY": lambda: security_door((220, 180, 20), "CREW"),
    "AMDOORR": lambda: security_door((200, 30, 30), "TOWER"),
    "AMLIFT": lift_side,
    "AMDESK": desk_front,
    "AMSEAT": seats,
    "AMROPE": queue_rope,
    "AMXRAY": xray,
    "AMBELTS": belt_side,
    "AMBOARD": board,
    "AMPLANE": fuselage,
    "AMHANGR": hangar_door,
    "AMTOWER": tower_glass,
    "AMPOSTR": poster,
    "AMDUTY": duty_free,
    "AMSKY1": sky,
    "AMSCHK": lambda: sign("CHECK-IN", "right"),
    "AMSSEC": lambda: sign("SECURITY", "left"),
    "AMSGATE": lambda: sign("GATES B1-B9", "right"),
    "AMSBAG": lambda: sign("BAGGAGE", "down"),
    "AMSEXIT": lambda: sign("EXIT", None, (40, 140, 60), (255, 255, 255)),
    "AMSDEP": lambda: sign("DEPARTURES", "up"),
    "AMSTRN": lambda: sign("TRAIN", "left"),
    "AMSLNG": lambda: sign("LOUNGE", "right"),
    "AMSTWR": lambda: sign("TOWER", "up", (40, 40, 44), (240, 200, 30)),
    "AMSAPRN": lambda: sign("APRON - CREW ONLY", None, (200, 30, 30), (255, 255, 255)),
}

FLATS = {
    "AMTERRA": terrazzo,
    "AMCARPT": lambda: carpet((40, 60, 120), (200, 170, 60)),
    "AMCARP2": lambda: carpet((110, 30, 40), (220, 200, 160)),
    "AMCEIL": ceiling_tiles,
    "AMLITE": light_panel,
    "AMBELT": belt,
    "AMWALK": walkway,
    "AMTARM": asphalt,
    "AMTARL": lambda: asphalt("centre"),
    "AMRUNW": lambda: asphalt("runway"),
    "AMSTEEL": diamond_plate,
    "AMLIFTF": diamond_plate,
    "AMCONCF": concrete_floor,
    "AMWINGF": aircraft_skin,
}


def contact_sheet(path):
    """All the art on one PNG, for checking by eye."""
    items = [(n, f()) for n, f in list(TEXTURES.items()) + list(FLATS.items())]
    cols, cell = 6, 140
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGB", (cols * 270, rows * (cell + 16)), (20, 20, 24))
    dr = ImageDraw.Draw(sheet)
    for i, (n, img) in enumerate(items):
        x, y = (i % cols) * 270, (i // cols) * (cell + 16)
        sheet.paste(img.convert("RGB"), (x + 4, y + 14))
        dr.text((x + 4, y), n, fill=(255, 255, 255))
    sheet.save(path)


if __name__ == "__main__":
    import sys
    contact_sheet(sys.argv[1] if len(sys.argv) > 1 else "art.png")
