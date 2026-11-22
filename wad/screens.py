"""Full-screen pictures for Layover: title screen, intermission backdrop, level names."""
import random

from PIL import Image, ImageDraw

from art import font, sky_strip, centred


def skyline(dr, w, h, seed, colour):
    rnd = random.Random(seed)
    x = 0
    while x < w:
        bw, bh = rnd.randint(10, 30), rnd.randint(10, 40)
        dr.rectangle([x, h - bh, x + bw, h], fill=colour)
        x += bw + rnd.randint(0, 8)


def titlepic():
    img = Image.new("RGB", (320, 200))
    sky_strip(img, 0, 150, 31)
    dr = ImageDraw.Draw(img)
    skyline(dr, 320, 150, 32, (60, 80, 110))
    # terminal and tower
    dr.rectangle([0, 130, 320, 200], fill=(46, 48, 52))
    dr.rectangle([20, 104, 300, 150], fill=(160, 164, 170))
    for x in range(26, 296, 14):
        dr.rectangle([x, 110, x + 10, 140], fill=(83, 83, 255))
    dr.rectangle([240, 40, 256, 104], fill=(150, 154, 160))
    dr.polygon([(228, 40), (268, 40), (262, 22), (234, 22)], fill=(55, 115, 43))
    dr.rectangle([226, 40, 270, 44], fill=(90, 94, 100))
    # a plane climbing away, trailing smoke
    dr.line([(20, 90), (120, 52)], fill=(200, 200, 200), width=3)
    dr.polygon([(118, 52), (150, 40), (154, 44), (122, 56)], fill=(236, 236, 240))
    dr.polygon([(132, 47), (140, 34), (144, 46)], fill=(210, 210, 220))
    # fire behind the terminal: something is wrong
    for x, h in ((70, 18), (120, 26), (180, 14), (210, 22)):
        dr.polygon([(x - 14, 104), (x, 104 - h), (x + 14, 104)], fill=(230, 90, 20))
        dr.polygon([(x - 7, 104), (x, 104 - h // 2), (x + 7, 104)], fill=(250, 200, 40))
    big = font(44)
    for dx, dy in ((2, 2), (0, 0)):
        centred(dr, (dx, 150 + dy, 320 + dx, 196 + dy), "LAYOVER",
                big, (30, 0, 0) if dx else (230, 50, 30))
    centred(dr, (0, 4, 320, 20), "AN AIRPLANEMODE EPISODE", font(10), (255, 255, 255))
    return img


def interpic():
    img = Image.new("RGB", (320, 200))
    sky_strip(img, 0, 200, 33)
    dr = ImageDraw.Draw(img)
    skyline(dr, 320, 200, 34, (50, 64, 90))
    dr.rectangle([0, 170, 320, 200], fill=(40, 42, 46))
    for x in range(0, 320, 40):
        dr.rectangle([x + 10, 184, x + 30, 188], fill=(220, 220, 210))
    return Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.35)


def level_name(text):
    """Level name for the intermission screen, red like the built-in ones."""
    f = font(18)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = probe.textbbox((0, 0), text.upper(), font=f)
    img = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    dr.text((2 - l, 2 - t), text.upper(), font=f, fill=(60, 0, 0, 255))
    dr.text((1 - l, 1 - t), text.upper(), font=f, fill=(220, 40, 30, 255))
    return img


def menu_logo():
    """M_DOOM: the logo above the main menu."""
    f = font(30)
    img = Image.new("RGBA", (180, 44), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    centred(dr, (2, 2, 180, 44), "LAYOVER", f, (60, 0, 0, 255))
    centred(dr, (0, 0, 178, 42), "LAYOVER", f, (230, 50, 30, 255))
    return img


def pictures(infos):
    """-> [(lump name, image)]"""
    out = [("TITLEPIC", titlepic()), ("INTERPIC", interpic()), ("M_DOOM", menu_logo())]
    for i, (_, info) in enumerate(infos):
        out.append((f"AMLV{i + 1:02d}", level_name(info["title"])))
    return out
