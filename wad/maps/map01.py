"""MAP01 Curbside: drop-off lane, check-in hall, the airline office (blue boarding pass),
then through the staff door to security."""
from mapkit import Map, rect, SKY, EASY, MEDIUM, HARD, ALL, AMBUSH, SECRET_LINE
from parts import sign, board, block, desk, seats, crates, lights, rope

INFO = {"par": 90, "music": "D_RUNNIN"}

# thing types
PLAYER, ZOMBIE, SHOTGUY, IMP, DEMON = 1, 3004, 9, 3001, 3002
SHOTGUN, CLIP, SHELLS, SHELLBOX, STIM, MEDKIT, HBONUS, ABONUS, GREEN, BLUECARD = \
    2001, 2007, 2008, 2049, 2011, 2012, 2014, 2015, 2018, 5
BARREL, LAMP = 2035, 2028
MED_UP, HARD_ONLY = MEDIUM | HARD, HARD


def build():
    m = Map("MAP01", "Curbside")

    # --- outside: the road and the sidewalk under the sky
    road = m.room(rect(0, 0, 1536, 320), floor=0, ceil=320, ftex="AMTARM", ctex=SKY,
                  light=208, wall="AMCONC", name="road")
    walk = m.room(rect(0, 320, 1536, 480), floor=8, ceil=320, ftex="AMCONCF", ctex=SKY,
                  light=208, wall="AMGLASS", face_lower="AMCONC", name="sidewalk")
    m.wall((0, 320), (0, 480), "AMCONC")
    m.wall((1536, 320), (1536, 480), "AMCONC")
    block(m, road, 256, 96, 768, 192, 96, "AMPLANE", top="AMWINGF")       # the airport shuttle
    crates(m, road, 1088, 176, 1152, 240, 48)                              # dropped luggage
    crates(m, road, 1152, 192, 1200, 240, 32)

    # --- three sliding glass doors in the facade
    for x in (320, 704, 1088):
        m.door(rect(x, 480, x + 128, 496), floor=8, tex="AMDOOR1")

    # --- check-in hall
    hall = m.room(rect(0, 496, 1536, 1088), floor=8, ceil=224, light=192, wall="AMWALL1", name="hall")
    m.wall((0, 496), (1536, 496), "AMGLASS")
    for x1 in (192, 576, 960):
        desk(m, hall, x1, 880, x1 + 256, 928)
        sign(m, hall, x1 + 128, 960, "AMSCHK")
    for x1 in (160, 1184):
        seats(m, hall, x1, 640, x1 + 192, 672)
        seats(m, hall, x1, 736, x1 + 192, 768)
    board(m, hall, 768, 640)
    sign(m, hall, 1440, 800, "AMSSEC", along="y")
    for x, y in ((512, 720), (1024, 720)):
        m.pillar(hall, rect(x - 32, y - 32, x + 32, y + 32))
    lights(m, hall, [(256, 560), (768, 560), (1280, 560), (384, 1024), (1152, 1024)])
    for x in (608, 640, 672):   # queue lanes in front of the middle desk
        rope(m, hall, x, 768, x + 8, 848)

    # --- staff door to baggage make-up, and the office with the boarding pass
    bag = m.room(rect(0, 1104, 1024, 1408), floor=8, ceil=160, ftex="AMCONCF", light=128,
                 wall="AMBAGW", name="baggage")
    m.door(rect(896, 1088, 960, 1104), floor=8, tex="DOOR3")
    for x in (288, 672):   # conveyor belts from the desks into the back room
        flap = m.sector(rect(x, 1088, x + 64, 1104), floor=40, ceil=72, ftex="AMBELT", ctex="AMSTEEL",
                        light=128, wall="AMBAGW", face_lower="AMBELTS", face_upper="AMBAGW", role="window")
        m.scroll(flap, 0, 1, special=251)
        belt = block(m, bag, x, 1104, x + 64, 1312, 32, "AMBELTS", top="AMBELT")
        m.scroll(belt, 0, 1)
    crates(m, bag, 96, 1248, 192, 1344)
    crates(m, bag, 480, 1280, 544, 1376, 48)

    office = m.room(rect(1040, 1104, 1536, 1408), floor=8, ceil=128, ftex="AMCARPT", light=160,
                    wall="AMWALL2", name="office")
    m.door(rect(1024, 1216, 1040, 1280), floor=8, tex="DOOR3")
    desk(m, office, 1216, 1312, 1408, 1360)
    lights(m, office, [(1152, 1200), (1408, 1200)])

    # --- security: the blue (boarding pass) door, x-ray corridor, then the exit room
    m.door(rect(1536, 736, 1552, 864), floor=8, tex="AMDOORB", key="blue")
    corr = m.room(rect(1552, 704, 2048, 896), floor=8, ceil=160, light=176, wall="AMWALL2", name="security")
    block(m, corr, 1664, 704 + 16, 1792, 768, 48, "AMXRAY")
    block(m, corr, 1856, 832, 1984, 896 - 16, 48, "AMXRAY")
    sign(m, corr, 1600, 800, "AMSSEC", along="y")
    end = m.room(rect(2048, 640, 2304, 960), floor=8, ceil=192, light=192, wall="AMWALL1", name="exit")
    m.line((2304, 768), (2304, 832), special=11, mid="SW1GRAY1", xoff=0)
    sign(m, end, 2240, 800, "AMSEXIT", along="y")

    # --- secret: duty-free stockroom behind the hall's west wall
    stash = m.room(rect(-272, 640, -16, 896), floor=8, ceil=128, ftex="AMCARP2", light=176,
                   wall="AMDUTY", special=9, name="secret")
    m.door(rect(-16, 704, 0, 832), floor=8, tex="AMPOSTR")
    m.line((0, 704), (0, 832), flags=SECRET_LINE)

    # --- things
    m.thing(192, 160, PLAYER, 90)
    m.things_at(ZOMBIE, [(832, 128), (896, 240)], 180)
    m.thing(200, 64, BARREL)
    m.thing(820, 64, BARREL)
    m.things_at(CLIP, [(480, 400), (1300, 400)])
    m.thing(1400, 120, STIM)
    # hall
    m.things_at(ZOMBIE, [(384, 1000), (1152, 1000), (768, 760)], 270)
    m.things_at(ZOMBIE, [(320, 1040), (1240, 1040)], 270, MED_UP)
    m.things_at(SHOTGUY, [(768, 1000)], 270, MED_UP)
    m.things_at(IMP, [(96, 1024), (1440, 1024)], 270, HARD_ONLY)
    m.thing(768, 800, SHOTGUN)
    m.things_at(HBONUS, [(560, 600), (624, 600), (912, 600), (976, 600)])
    m.things_at(ABONUS, [(1280, 700), (288, 700)])
    m.things_at(SHELLS, [(80, 560), (1456, 560)])
    # baggage
    m.things_at(IMP, [(416, 1200), (800, 1340)], 0)
    m.things_at(IMP, [(160, 1180)], 0, MED_UP)
    m.things_at(ZOMBIE, [(600, 1200), (850, 1250)], 0)
    m.thing(900, 1360, BARREL)
    m.thing(560, 1180, BARREL)
    m.things_at(SHELLS, [(64, 1150), (950, 1150)])
    m.thing(380, 1360, STIM)
    # office
    m.thing(1300, 1250, SHOTGUY, 180, ALL | AMBUSH)
    m.thing(1460, 1160, ZOMBIE, 180, MED_UP | AMBUSH)
    m.thing(1312, 1384, BLUECARD)
    m.thing(1100, 1380, MEDKIT)
    # security and exit
    m.things_at(ZOMBIE, [(1720, 850), (1920, 760)], 180)
    m.thing(1980, 760, IMP, 180, MED_UP)
    m.things_at(SHOTGUY, [(2176, 720), (2176, 880)], 180, MED_UP)
    m.thing(2120, 800, ZOMBIE, 180, EASY)
    m.thing(2240, 900, IMP, 180, HARD_ONLY)
    m.thing(1600, 740, SHELLS)
    # secret
    m.thing(-144, 768, GREEN)
    m.thing(-220, 700, SHELLBOX)
    return m
