"""MAP04 Baggage Underworld: from baggage claim down into the belts under the terminal.
Ride the conveyor past the crusher, drop into the sorting hall, take the lift up to lost
luggage for the red key, and teleport back up to the red door."""
from mapkit import Map, rect, EASY, MEDIUM, HARD, ALL, AMBUSH, SECRET_LINE
from parts import sign, block, seats, crates, lights, carousel
from things import *  # noqa: F401,F403

INFO = {"par": 200, "music": "D_BETWEE"}
MH = MEDIUM | HARD


def build():
    m = Map("MAP04", "Baggage Underworld")

    # --- baggage claim
    bc = m.room(rect(0, 0, 1536, 1024), floor=0, ceil=192, light=144, wall="AMWALL1", name="claim")
    m.wall((0, 0), (1536, 0), "AMGLASS")
    c1 = carousel(m, bc, 448, 512)
    c2 = carousel(m, bc, 1088, 512)
    sign(m, bc, 768, 960, "AMSBAG")
    sign(m, bc, 768, 64, "AMSEXIT")
    lights(m, bc, [(128, 128), (1408, 128), (128, 896), (1408, 896), (768, 512)])

    # --- staff corridor down into the underworld, and the dark maintenance room
    m.door(rect(704, 1024, 832, 1040), floor=0, tex="DOOR3")
    u1 = m.room(rect(640, 1040, 896, 1536), floor=0, ceil=128, ftex="AMCONCF", light=112,
                wall="AMBAGW", name="staff corridor")
    maint = m.room(rect(128, 1152, 640, 1408), floor=0, ceil=128, ftex="AMCONCF", light=80,
                   wall="AMCONC", name="maintenance")
    crates(m, maint, 192, 1216, 288, 1312)
    crates(m, maint, 416, 1312, 480, 1376, 48)

    # --- the conveyor tunnel (carries you east, into the crusher)
    t1 = m.room(rect(896, 1280, 1408, 1408), floor=0, ceil=112, ftex="AMBELT", light=96,
                wall="AMBAGW", name="tunnel")
    m.scroll(t1, 3, 0)
    crush = m.room(rect(1408, 1280, 1536, 1408), floor=0, ceil=112, ftex="AMBELT", ctex="AMSTEEL",
                   light=160, special=1, wall="AMHAZ", name="crusher")
    m.scroll(crush, 3, 0)
    t2 = m.room(rect(1536, 1280, 2048, 1408), floor=0, ceil=112, ftex="AMBELT", light=96,
                wall="AMBAGW", name="tunnel 2")
    m.scroll(t2, 3, 0)
    crush.tag = m.new_tag()
    m.line((896, 1280), (896, 1408), special=73, tag=crush.tag)   # WR: crusher starts
    for x in (1408, 1536):   # the crusher's ceiling comes down: texture the faces it shows
        m.line((x, 1280), (x, 1408), upper="AMHAZ", back={"upper": "AMHAZ"})

    # --- the sorting hall, 128 below (you drop in from the tunnel)
    s = m.room(rect(2048, 896, 2816, 1792), floor=-128, ceil=128, ftex="AMCONCF", light=128,
               wall="AMBAGW", name="sorting")
    for y in (1024, 1536):
        belt = block(m, s, 2176, y, 2688, y + 64, 32, "AMBELTS", top="AMBELT")
        m.scroll(belt, 2 if y == 1024 else -2, 0)
    m.inset(s, rect(2304, 1216, 2560, 1408), floor=-144, ftex="NUKAGE1", light=160, special=7,
            face_lower="AMHAZ", name="fuel leak")
    m.pillar(s, rect(2176, 1280, 2240, 1344))
    m.pillar(s, rect(2624, 1280, 2688, 1344))
    lights(m, s, [(2112, 960), (2752, 960), (2112, 1728)])

    # --- lift up to lost luggage (red key)
    m.lift(rect(2432, 1792, 2560, 1920), low=-128, high=0, ceil=128)
    vault = m.room(rect(2368, 1920, 2624, 2176), floor=0, ceil=128, ftex="AMCONCF", light=144,
                   wall="AMBAGW", name="lost luggage")
    crates(m, vault, 2384, 2096, 2464, 2160)
    crates(m, vault, 2528, 2096, 2608, 2160, 48)

    # --- the train back up: a teleporter in the sorting hall to baggage claim
    m.teleport(rect(2112, 1600, 2176, 1664), s, bc, (1400, 512), 180)

    # --- red door, stairs up and out
    m.door(rect(1536, 448, 1552, 576), floor=0, tex="AMDOORR", key="red")
    x = m.room(rect(1552, 384, 1856, 640), floor=0, ceil=128, light=160, wall="AMWALL2", name="exit hall")
    for i in range(6):
        m.room(rect(1856 + 64 * i, 384, 1920 + 64 * i, 640), floor=16 * (i + 1), ceil=224, light=176,
               wall="AMWALL2", face_lower="STEP1", ftex="AMTERRA", name="stairs")
    end = m.room(rect(2240, 384, 2496, 640), floor=96, ceil=224, light=192, wall="AMWALL1", name="exit")
    m.line((2496, 480), (2496, 544), special=11, mid="SW1GRAY1", xoff=0)
    sign(m, end, 2432, 512, "AMSEXIT", along="y")

    # --- secret: behind baggage claim's west wall
    m.room(rect(-272, 416, -16, 608), floor=0, ceil=128, ftex="AMCARP2", light=144, wall="AMDUTY",
           special=9, name="secret")
    m.door(rect(-16, 448, 0, 576), floor=0, tex="AMWALL1")
    m.line((0, 448), (0, 576), flags=SECRET_LINE)

    # --- things
    m.thing(768, 160, PLAYER, 90)
    m.things_at(ZOMBIE, [(200, 850), (1300, 850)], 270)
    m.things_at(SHOTGUY, [(768, 800), (128, 300)], 270)
    m.things_at(IMP, [(1400, 300), (768, 300)], 90, MH)
    m.thing(768, 512, CHAINGUY, 90, HARD)   # on the light, between the carousels
    m.things_at(SHELLS, [(64, 64), (1472, 64)])
    m.thing(768, 900, STIM)
    # underworld
    m.things_at(IMP, [(768, 1300), (768, 1480)], 270)
    m.things_at(SPECTRE, [(380, 1250), (560, 1350)], 0, MH)
    m.thing(320, 1360, DEMON, 0, ALL)
    m.thing(560, 1200, GREEN)
    m.thing(200, 1180, SHELLBOX)
    m.thing(1100, 1344, ZOMBIE, 180)
    m.thing(1800, 1344, IMP, 180, MH)
    # sorting hall
    m.things_at(IMP, [(2112, 1200), (2752, 1200), (2400, 1700)], 90)
    m.things_at(DEMON, [(2300, 1500), (2560, 1150)], 90)
    m.thing(2432, 960, CACO, 90, MH)
    m.thing(2700, 1700, KNIGHT, 180, HARD)
    m.thing(2120, 1450, SHOTGUY, 0, MH)
    m.thing(2432, 1450, LAUNCHER)
    m.things_at(ROCKET, [(2700, 1450), (2112, 1100)])
    m.thing(2750, 1080, MEDKIT)
    # lost luggage
    m.thing(2496, 2080, REDCARD)
    m.thing(2496, 2140, SSG, 0)
    m.things_at(IMP, [(2420, 2000), (2580, 2000)], 270, ALL | AMBUSH)
    m.thing(2496, 1990, SHOTGUY, 270, MH | AMBUSH)
    # exit
    m.things_at(SHOTGUY, [(1700, 600), (1700, 420)], 180, MH)
    m.thing(1780, 512, IMP, 180)
    m.things_at(IMP, [(2300, 420), (2300, 600)], 180, MH)
    m.thing(1600, 512, SHELLS)
    # secret
    m.thing(-144, 512, BACKPACK)
    m.things_at(ROCKET, [(-220, 450), (-220, 570)])
    m.thing(-80, 512, MEDKIT)
    return m
