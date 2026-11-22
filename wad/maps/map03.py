"""MAP03 Concourse B: off the terminal train and down the concourse on the moving walkways.
The blue key is aboard the plane at gate B2 (and stepping aboard wakes the food court
kitchen). The lounge holds the yellow crew badge; gate B4's plane is the way out."""
from mapkit import Map, rect, EASY, MEDIUM, HARD, ALL, AMBUSH, SECRET_LINE
from parts import sign, board, block, seats, desk, crates, lights
from things import *  # noqa: F401,F403

INFO = {"par": 180, "music": "D_COUNTD"}
MH = MEDIUM | HARD
GATES = [128, 896, 1664, 2432]   # x of each gate's left wall


def cabin(m, x0, entry_tag=None):
    """Jet bridge north of a gate, into a plane cabin with rows of seats either side."""
    bridge = m.room(rect(x0 + 192, 848, x0 + 320, 1344), floor=0, ceil=112, ftex="AMSTEEL",
                    light=128, wall="AMBAGW", name="bridge")
    cab = m.room(rect(x0 - 64, 1344, x0 + 576, 1600), floor=16, ceil=112, ftex="AMCARPT",
                 light=112, wall="AMTILE", face_lower="AMTILE", name="cabin")
    for y in (1424, 1488, 1552):
        block(m, cab, x0 - 48, y, x0 + 224, y + 24, 32, "AMSEAT", top="AMCARPT")
        block(m, cab, x0 + 288, y, x0 + 560, y + 24, 32, "AMSEAT", top="AMCARPT")
    lights(m, cab, [(x0 + 256, 1392)], size=32)
    if entry_tag:
        m.line((x0 + 192, 1344), (x0 + 320, 1344), special=2, tag=entry_tag)   # W1: open those doors
    return bridge, cab


def build():
    m = Map("MAP03", "Concourse B")

    # --- terminal train platform (start) and the concourse
    plat = m.room(rect(-512, 0, 0, 384), floor=0, ceil=160, ftex="AMCONCF", light=160, wall="AMCONC",
                  name="platform")
    block(m, plat, -448, 16, -128, 80, 96, "AMPLANE", top="AMWINGF")   # the train
    conc = m.room(rect(0, 0, 3072, 384), floor=0, ceil=224, light=192, wall="AMWALL1",
                  face_upper="AMWALL2", name="concourse")
    sign(m, conc, 48, 192, "AMSTRN", along="y")
    for x1, x2 in ((256, 1408), (1664, 2816)):
        east = m.inset(conc, rect(x1, 96, x2, 160), ftex="AMWALK", light=208)
        west = m.inset(conc, rect(x1, 224, x2, 288), ftex="AMWALK", light=208)
        m.scroll(east, 4, 0)
        m.scroll(west, -4, 0)
    lights(m, conc, [(128, 192), (1536, 192), (2944, 192)])
    board(m, conc, 1536, 320)
    for x in (200, 1600):   # signs across the concourse, facing people walking east
        sign(m, conc, x, 192, "AMSGATE", along="y")

    # --- the four gates
    for i, x0 in enumerate(GATES):
        g = m.room(rect(x0, 384, x0 + 512, 832), floor=0, ceil=160, ftex="AMCARPT", light=176,
                   wall="AMWALL2", name=f"gate B{i * 2 + 2}")
        m.wall((x0, 832), (x0 + 512, 832), "AMGLASS")
        seats(m, g, x0 + 64, 576, x0 + 448, 608)
        seats(m, g, x0 + 64, 672, x0 + 448, 704)
        desk(m, g, x0 + 384, 752, x0 + 480, 800)
        sign(m, conc, x0 + 256, 368, "AMSGATE")

    # --- food court, and the kitchen behind it (opens when you board at B2)
    food = m.room(rect(1024, -640, 2048, 0), floor=0, ceil=192, light=176, wall="AMWALL2", name="food court")
    for x in (1152, 1408, 1664, 1920):
        for y in (-448, -256):
            block(m, food, x - 32, y - 32, x + 32, y + 32, 32, "AMDESK", top="AMCEIL")
    for x1, x2 in ((1088, 1312), (1504, 1568), (1760, 1984)):
        block(m, food, x1, -608, x2, -560, 40, "AMDESK")
    kitchen_tag = m.new_tag()
    m.room(rect(1280, -896, 1792, -656), floor=0, ceil=128, ftex="AMCONCF",
           light=144, wall="AMTILE", name="block")
    for x in (1344, 1600):
        m.door(rect(x, -656, x + 128, -640), floor=0, tex="AMWALL2", remote=True, tag=kitchen_tag)

    # --- gate B2: jet bridge and the plane with the blue key
    m.door(rect(GATES[1] + 192, 832, GATES[1] + 320, 848), floor=0, tex="AMDOOR1")
    cabin(m, GATES[1], entry_tag=kitchen_tag)

    # --- the lounge (blue door), yellow badge on the dais, and what it wakes
    m.door(rect(3072, 128, 3088, 256), floor=0, tex="AMDOORB", key="blue")
    sign(m, conc, 2992, 192, "AMSLNG", along="y")
    lounge = m.room(rect(3088, 0, 3600, 512), floor=0, ceil=144, ftex="AMCARP2", light=160,
                    wall="AMWALL1", name="lounge")
    seats(m, lounge, 3152, 64, 3344, 96)
    seats(m, lounge, 3152, 192, 3344, 224)
    desk(m, lounge, 3408, 48, 3536, 96)
    dais = m.inset(lounge, rect(3472, 320, 3568, 416), floor=16, ftex="AMSTEEL", face_lower="AMWALL2")
    trap_tag = m.new_tag()
    for a, b in zip(dais.outer, dais.outer[1:] + dais.outer[:1]):
        m.line(a, b, special=2, tag=trap_tag)
    m.room(rect(3200, 528, 3456, 704), floor=0, ceil=128, ftex="AMCONCF", light=96, wall="AMCONC", name="block")
    m.door(rect(3264, 512, 3392, 528), floor=0, tex="AMWALL1", remote=True, tag=trap_tag)

    # --- gate B4: the crew door, and the plane out (exit in the cockpit)
    m.door(rect(GATES[3] + 192, 832, GATES[3] + 320, 848), floor=0, tex="AMDOORY", key="yellow")
    _, cab4 = cabin(m, GATES[3])
    x0 = GATES[3]
    m.room(rect(x0 + 192, 1600, x0 + 320, 1728), floor=16, ceil=96, ftex="AMSTEEL", light=144,
           wall="AMWALL1", name="cockpit")
    m.line((x0 + 224, 1728), (x0 + 288, 1728), special=11, mid="SW1GRAY1", xoff=0)

    # --- secret: duty free stockroom behind the concourse's south wall
    m.room(rect(320, -288, 576, -16), floor=0, ceil=128, ftex="AMCARP2", light=144, wall="AMDUTY",
           special=9, name="secret")
    m.door(rect(384, -16, 512, 0), floor=0, tex="AMWALL1")
    m.line((384, 0), (512, 0), flags=SECRET_LINE)

    # --- things
    m.thing(-256, 192, PLAYER, 0)
    m.thing(-96, 320, SHOTGUN)
    m.things_at(SHELLS, [(-448, 320), (-320, 320)])
    m.thing(-64, 120, CLIP)
    # concourse
    m.things_at(ZOMBIE, [(700, 40), (1100, 340), (2200, 40)], 180)
    m.things_at(SHOTGUY, [(1500, 40), (2500, 340), (2900, 40)], 180)
    m.things_at(IMP, [(900, 200), (2300, 200)], 180, MH)
    m.thing(2700, 200, CHAINGUY, 180, HARD)
    m.things_at(HBONUS, [(x, 192) for x in range(400, 1300, 128)])
    m.things_at(ABONUS, [(x, 192) for x in range(1800, 2700, 128)])
    # gates
    m.things_at(IMP, [(256, 760), (500, 520)], 270)
    m.things_at(SHOTGUY, [(1000, 760), (1300, 520)], 270, MH)
    m.things_at(ZOMBIE, [(1100, 640)], 270)
    m.thing(1800, 760, IMP, 270)
    m.things_at(SHELLBOX, [(1700, 520)])
    m.thing(2100, 760, MEDKIT)
    m.thing(1920, 640, CHAINGUN, 0, ALL)
    m.things_at(SHOTGUY, [(2500, 760), (2850, 520)], 270)
    m.thing(2700, 640, CHAINGUY, 270, MH)
    # B2 bridge and cabin
    m.thing(1152, 1100, IMP, 270)
    m.things_at(IMP, [(1152, 1460), (1152, 1530)], 270, ALL | AMBUSH)
    m.thing(1152, 1584, BLUECARD)
    m.thing(900, 1380, SHOTGUY, 0, MH | AMBUSH)
    m.thing(1400, 1380, STIM)
    # food court and kitchen
    m.things_at(ZOMBIE, [(1280, -128), (1792, -128)], 90)
    m.things_at(IMP, [(1400, -760), (1660, -760)], 90, ALL | AMBUSH)
    m.things_at(DEMON, [(1440, -820), (1700, -820)], 90, MH | AMBUSH)
    m.thing(1540, -760, DEMON, 90, HARD | AMBUSH)
    m.things_at(SHELLS, [(1100, -360), (2000, -360)])
    m.thing(1540, -360, MEDKIT)
    # lounge and its trap
    m.things_at(IMP, [(3200, 400), (3500, 150)], 180)
    m.thing(3520, 368, YELLOWCARD)
    m.things_at(SPECTRE, [(3250, 600), (3410, 600)], 270, MH | AMBUSH)
    m.thing(3330, 640, DEMON, 270, ALL | AMBUSH)
    m.thing(3150, 450, MEDKIT)
    m.thing(3560, 470, SHELLBOX)
    # B4 cabin and cockpit
    m.things_at(IMP, [(2688, 1460), (2688, 1540)], 270)
    m.thing(2688, 1650, SHOTGUY, 270, MH)
    m.thing(2400, 1380, ZOMBIE, 0)
    m.thing(2950, 1380, IMP, 180, HARD)
    # secret
    m.thing(448, -160, BLUE_ARMOR)
    m.thing(380, -240, BACKPACK)
    return m
