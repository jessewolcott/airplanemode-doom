"""MAP02 Security: the checkpoint is in lockdown. Ride the staff lift up to the security
office, lift the shutters, grab the crew badge from the confiscated-goods room, and leave
airside through the crew door."""
from mapkit import Map, rect, EASY, MEDIUM, HARD, ALL, AMBUSH, SECRET_LINE
from parts import sign, board, block, seats, crates, lights, rope
from things import *  # noqa: F401,F403

INFO = {"par": 120, "music": "D_STALKS"}
MH = MEDIUM | HARD


def build():
    m = Map("MAP02", "Security")

    # --- queue hall, lanes marked out with ropes
    q = m.room(rect(0, 0, 1280, 640), floor=0, ceil=256, light=176, wall="AMWALL2", name="queue")
    rope(m, q, 0, 188, 1024, 196)
    rope(m, q, 256, 316, 1280, 324)
    rope(m, q, 0, 444, 1024, 452)
    lights(m, q, [(256, 96), (768, 96), (512, 256), (1024, 256), (256, 384), (768, 384), (640, 560)])
    sign(m, q, 1152, 96, "AMSSEC")
    # the checkpoint: three lanes, each an x-ray machine and a shutter (locked down)
    shutters = []
    for x in (288, 608, 928):
        block(m, q, x - 96, 504, x - 16, 632, 48, "AMXRAY")
        shutters.append(m.door(rect(x, 640, x + 64, 704), floor=0, tex="AMBAGW", remote=True))

    # --- staff corridor and the lift up to the office
    m.door(rect(1280, 256, 1296, 384), floor=0, tex="DOOR3")
    corr = m.room(rect(1296, 64, 1552, 576), floor=0, ceil=128, light=144, wall="AMTILE", name="staff")
    m.lift(rect(1296, 576, 1552, 704), low=0, high=128, ceil=256)
    office = m.room(rect(1296, 704, 1680, 1024), floor=128, ceil=256, ftex="AMCARPT", light=176,
                    wall="AMWALL1", name="office")
    block(m, office, 1424, 912, 1616, 960, 40, "AMDESK")
    lights(m, office, [(1424, 800), (1584, 800)])
    m.switch((1456, 1024), (1520, 1024), 103, shutters, tex="SW1GRAY1")   # S1: open the shutters
    # window from the office over airside
    m.window(rect(1280, 800, 1296, 960), sill=168, lintel=232, wall="AMWALL1")

    # --- confiscated goods (the crew badge)
    m.door(rect(1680, 832, 1696, 896), floor=128, tex="DOOR3")
    conf = m.room(rect(1696, 768, 1952, 960), floor=128, ceil=192, ftex="AMCONCF", light=128,
                  wall="AMBAGW", name="confiscated")
    crates(m, conf, 1760, 896, 1824, 944)
    crates(m, conf, 1872, 784, 1936, 848, 48)

    # --- airside hall
    a = m.room(rect(0, 704, 1280, 1280), floor=0, ceil=256, light=192, wall="AMWALL1", name="airside")
    for y in (848, 1008):
        seats(m, a, 160, y, 448, y + 32)
        seats(m, a, 832, y, 1120, y + 32)
    block(m, a, 512, 1088, 768, 1216, 64, "AMDUTY", top="AMCEIL")     # duty-free kiosk
    board(m, a, 640, 800)
    sign(m, a, 640, 1248, "AMSGATE")
    lights(m, a, [(256, 1180), (1024, 1180), (640, 1040)])
    m.pillar(a, rect(576, 896, 704, 960))

    # --- the crew door and the way out
    m.door(rect(576, 1280, 704, 1296), floor=0, tex="AMDOORY", key="yellow")
    out = m.room(rect(512, 1296, 768, 1600), floor=0, ceil=160, light=160, wall="AMWALL2", name="exit")
    m.line((608, 1600), (672, 1600), special=11, mid="SW1GRAY1", xoff=0)
    sign(m, out, 640, 1560, "AMSEXIT")

    # --- secret: smoking room behind the airside west wall
    m.room(rect(-272, 928, -16, 1120), floor=0, ceil=128, ftex="AMCARP2", light=112,
           wall="AMDUTY", special=9, name="secret")
    m.door(rect(-16, 960, 0, 1088), floor=0, tex="AMWALL1")
    m.line((0, 960), (0, 1088), flags=SECRET_LINE)

    # --- things
    m.thing(160, 80, PLAYER, 90)
    m.thing(320, 96, SHOTGUN, 0)
    m.things_at(ZOMBIE, [(640, 256), (900, 380), (200, 520)], 270)
    m.things_at(SHOTGUY, [(400, 380), (1100, 520)], 270, MH)
    m.thing(700, 560, IMP, 270, HARD)
    m.things_at(SHELLS, [(1200, 60), (60, 260)])
    m.thing(1220, 590, STIM)
    m.things_at(HBONUS, [(500, 30), (560, 30), (620, 30), (680, 30)])
    # staff corridor
    m.things_at(IMP, [(1424, 400)], 270)
    m.things_at(IMP, [(1360, 200)], 90, MH)
    m.thing(1500, 120, CLIP)
    # office
    m.things_at(SHOTGUY, [(1360, 960), (1640, 760)], 270, ALL | AMBUSH)
    m.thing(1500, 860, ZOMBIE, 270, MH)
    m.thing(1620, 1000, MEDKIT)
    m.thing(1350, 760, SHELLBOX)
    # confiscated
    m.thing(1900, 920, YELLOWCARD)
    m.things_at(IMP, [(1800, 800)], 180, ALL | AMBUSH)
    m.things_at(IMP, [(1900, 880)], 180, MH | AMBUSH)
    m.thing(1740, 800, ABONUS)
    # airside
    m.things_at(IMP, [(300, 950), (1000, 950), (300, 1200), (980, 1220)], 270)
    m.things_at(DEMON, [(640, 1040), (200, 1120)], 270, MH)
    m.thing(1100, 760, DEMON, 270, HARD)
    m.things_at(SHOTGUY, [(500, 780), (800, 780)], 270)
    m.thing(1200, 1100, CHAINGUY, 180, HARD)
    m.thing(640, 1040, CHAINGUN, 0, EASY)   # easy: the demon isn't there
    m.thing(1180, 760, CHAINGUN, 0, MH)
    m.things_at(CLIP, [(60, 760), (1220, 1250)])
    m.thing(60, 1240, MEDKIT)
    m.thing(1220, 740, GREEN)
    # exit
    m.things_at(IMP, [(560, 1500), (720, 1500)], 270, MH)
    m.thing(640, 1450, ZOMBIE, 270, EASY)
    # secret
    m.thing(-144, 1024, SOUL)
    m.thing(-220, 960, AMMOBOX)
    return m
