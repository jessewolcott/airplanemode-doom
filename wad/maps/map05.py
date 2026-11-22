"""MAP05 The Tarmac: out on the apron. The crew badge is up on a wing of the plane on
stand 2; it opens the fuel depot, whose switch raises the hangar door. The hangar has the
blue key for the control tower."""
from mapkit import Map, rect, SKY, EASY, MEDIUM, HARD, ALL, AMBUSH, SECRET_LINE
from parts import sign, block, crates, lights, octagon
from things import *  # noqa: F401,F403

INFO = {"par": 240, "music": "D_DOOM"}
MH = MEDIUM | HARD


def wing(cx, cy, side):
    """Swept wing on one side of a fuselage centred at (cx, cy) running along x."""
    s = 1 if side > 0 else -1
    return [(cx - 64, cy + 48 * s), (cx + 96, cy + 48 * s), (cx - 16, cy + 368 * s), (cx - 112, cy + 368 * s)]


def plane(m, apron, cx, cy):
    """An airliner: fuselage (too tall to climb), wings you can step onto, engines."""
    block(m, apron, cx - 320, cy - 48, cx + 320, cy + 48, 112, "AMPLANE", top="AMWINGF")
    wings = []
    for side in (1, -1):
        w = m.inset(apron, wing(cx, cy, side), floor=apron.floor + 24, ftex="AMWINGF", face_lower="METAL")
        y1, y2 = sorted((cy + 176 * side, cy + 240 * side))
        block(m, w, cx - 72, y1, cx + 8, y2, 40, "AMBAGW")
        wings.append(w)
    return wings


def build():
    m = Map("MAP05", "The Tarmac")

    # --- the gate building you come down into
    g = m.room(rect(1280, -256, 2304, -16), floor=0, ceil=160, light=176, wall="AMWALL1", name="gate")
    m.wall((1280, -16), (2304, -16), "AMGLASS")
    m.wall((1280, -256), (2304, -256), "AMGLASS")
    m.door(rect(1728, -16, 1856, 0), floor=0, tex="AMDOOR1")
    sign(m, g, 1792, -64, "AMSAPRN")
    lights(m, g, [(1472, -136), (2112, -136)])

    # --- the apron
    apron = m.room(rect(0, 0, 3584, 2560), floor=0, ceil=384, ftex="AMTARM", ctex=SKY, light=208,
                   wall="AMCONC", name="apron")
    for x in (384, 3136):
        m.inset(apron, rect(x, 256, x + 64, 2176), ftex="AMTARL")
    m.inset(apron, rect(128, 2240, 3456, 2432), ftex="AMRUNW")
    plane(m, apron, 1024, 1088)
    plane(m, apron, 2560, 1600)
    crates(m, apron, 1600, 384, 1664, 448, 48)        # baggage carts
    crates(m, apron, 1680, 384, 1744, 448, 48)
    crates(m, apron, 2944, 256, 3008, 320, 64)
    block(m, apron, 1920, 2000, 2112, 2096, 56, "AMBAGW")   # catering truck

    # --- fuel depot (yellow gate) and the switch for the hangar
    m.door(rect(-16, 1216, 0, 1344), floor=0, tex="AMDOORY", key="yellow")
    depot = m.room(rect(-768, 896, -16, 1664), floor=0, ceil=384, ftex="AMCONCF", ctex=SKY, light=192,
                   wall="AMCONC", name="fuel depot")
    for cy in (1088, 1472):
        m.inset(depot, octagon(-512, cy, 112), floor=160, ftex="AMSTEEL", face_lower="METAL", name="block")
    block(m, depot, -320, 1200, -128, 1296, 56, "AMBAGW")   # fuel truck

    # --- the hangar, east of the apron
    hangar = m.room(rect(3600, 640, 4368, 1408), floor=0, ceil=288, ftex="AMCONCF", light=160,
                    wall="AMBAGW", name="hangar")
    hdoor = m.door(rect(3584, 768, 3600, 1280), floor=0, tex="AMHANGR", remote=True)
    m.switch((-768, 1248), (-768, 1312), 103, hdoor, tex="SW1GRAY1")
    block(m, hangar, 3840, 960, 4224, 1024, 96, "AMPLANE", top="AMWINGF")
    lights(m, hangar, [(3744, 768), (4224, 768), (3744, 1280), (4224, 1280)])

    # --- the tower base (blue door) and the exit
    m.door(rect(448, 2560, 576, 2576), floor=0, tex="AMDOORB", key="blue")
    tower = m.room(rect(256, 2576, 768, 3088), floor=0, ceil=192, light=176, wall="AMWALL1", name="tower base")
    sign(m, tower, 512, 2900, "AMSTWR")
    m.pillar(tower, rect(448, 2768, 576, 2832))
    m.line((480, 3088), (544, 3088), special=11, mid="SW1GRAY1", xoff=0)

    # --- secret: crew rest room at the gate's west end
    m.room(rect(1008, -224, 1264, -32), floor=0, ceil=128, ftex="AMCARP2", light=144, wall="AMWALL2",
           special=9, name="secret")
    m.door(rect(1264, -192, 1280, -64), floor=0, tex="AMWALL1")
    m.line((1280, -192), (1280, -64), flags=SECRET_LINE)

    # --- things
    m.thing(1792, -160, PLAYER, 90)
    m.things_at(ZOMBIE, [(1400, -100), (2200, -100)], 90)
    m.thing(2200, -200, SHELLS)
    m.thing(1350, -200, STIM)
    # apron
    m.things_at(IMP, [(300, 600), (1600, 600), (2200, 400), (3300, 800), (1800, 1900), (600, 1800)], 270)
    m.things_at(IMP, [(1000, 1300), (1000, 876)], 270, MH)        # on P1's wings
    m.things_at(SHOTGUY, [(1200, 400), (2800, 500), (1500, 1500), (3000, 2000)], 270)
    m.thing(1900, 1100, CHAINGUY, 270, MH)
    m.thing(3300, 1500, CHAINGUY, 180, HARD)
    m.things_at(DEMON, [(700, 700), (1300, 1800)], 270)
    m.thing(2000, 700, DEMON, 270, MH)
    m.thing(1800, 1300, CACO, 270)
    m.thing(2900, 1100, CACO, 270, MH)
    m.thing(800, 2000, CACO, 270, HARD)
    m.thing(3300, 2300, KNIGHT, 270, MH)
    m.thing(2520, 1900, YELLOWCARD)                                 # up on P2's wing
    m.thing(2536, 1388, IMP, 90, ALL)
    m.things_at(BARREL, [(1580, 480), (1760, 480), (2950, 380), (1900, 1950), (2140, 1950)])
    m.things_at(MEDKIT, [(1800, 200), (3400, 200)])
    m.thing(100, 2400, SHELLBOX)
    m.thing(1024, 600, ROCKET)
    m.thing(2560, 1000, SHELLS)
    # depot
    m.things_at(IMP, [(-400, 1000), (-200, 1550)], 0)
    m.thing(-650, 1300, SHOTGUY, 0, MH)
    m.thing(-300, 1100, DEMON, 0)
    m.things_at(BARREL, [(-100, 1180), (-100, 1320), (-350, 1350)])
    m.thing(-700, 1600, MEDKIT)
    # hangar
    m.thing(3800, 800, KNIGHT, 180)
    m.thing(4000, 1200, BARON, 180, HARD)
    m.things_at(DEMON, [(3700, 1100), (4250, 1150)], 180, MH)
    m.things_at(IMP, [(3700, 700), (4300, 900)], 180)
    m.thing(4300, 700, BLUECARD)
    m.thing(3700, 1300, LAUNCHER)
    m.thing(4250, 1300, ROCKETBOX)
    m.thing(4000, 760, MEDKIT)
    # tower base
    m.things_at(IMP, [(320, 2700), (700, 2700)], 270)
    m.thing(512, 3000, SHOTGUY, 270, MH)
    m.thing(400, 2950, CHAINGUY, 270, HARD)
    # secret
    m.thing(1136, -128, SOUL)
    return m
