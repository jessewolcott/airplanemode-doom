"""MAP06 Control Tower: climb the stair shaft, take the red key from the landing, ride up
to the glass cab, and face what's waiting on the roof. The radar mast opens (and with it
the way out) once the big one is dead."""
from mapkit import Map, rect, SKY, EASY, MEDIUM, HARD, ALL, AMBUSH, SECRET_LINE
from parts import sign, block, desk, crates, lights, octagon
from things import *  # noqa: F401,F403

MAST_TAG = 99   # opened by UMAPINFO bossaction when the boss dies
INFO = {
    "par": 300, "music": "D_EVIL",
    "extra": [
        "bossaction = clear",
        f"bossaction = Cyberdemon, 2, {MAST_TAG}",   # medium and hard
        f"bossaction = BaronOfHell, 2, {MAST_TAG}",  # easy has two barons instead
        "endcast = true",
        'intertext = "The tower falls quiet.",',
        '  "On the radar, one blip is still moving:",',
        '  "a late flight, inbound, lights on.",',
        '  "",',
        '  "You find a seat by the window",',
        '  "and put your phone in airplane mode.",',
        '  "",',
        '  "Thanks for flying Layover."',
        'interbackdrop = "AMTARM"',
    ],
}
MH = MEDIUM | HARD


def build():
    m = Map("MAP06", "Control Tower")

    # --- lobby
    lobby = m.room(rect(640, -512, 1280, -16), floor=0, ceil=192, light=176, wall="AMWALL1", name="lobby")
    desk(m, lobby, 832, -320, 1088, -272)
    sign(m, lobby, 960, -64, "AMSTWR")
    lights(m, lobby, [(768, -400), (1152, -400)])
    m.door(rect(896, -16, 1024, 0), floor=0, tex="AMDOOR1")

    # --- the stair shaft: 13 steps around a solid core, 20 units each
    cells = [(896, 0, 1024, 192), (1024, 0, 1152, 192), (1152, 0, 1280, 192), (1280, 0, 1408, 192),
             (1408, 0, 1536, 192), (1344, 192, 1536, 320), (1344, 320, 1536, 448), (1344, 448, 1536, 640),
             (1216, 448, 1344, 640), (1088, 448, 1216, 640), (896, 448, 1088, 640), (896, 320, 1088, 448),
             (896, 192, 1088, 320)]
    steps = []
    for i, (x1, y1, x2, y2) in enumerate(cells):
        steps.append(m.room(rect(x1, y1, x2, y2), floor=20 * (i + 1), ceil=448, ftex="AMTERRA",
                            light=144 + (i % 2) * 16, wall="AMWALL2", face_lower="STEP1", name=f"step {i + 1}"))
    top = steps[-1].floor   # 260

    # --- landing (red key) and the lift up to the cab
    m.door(rect(880, 192, 896, 320), floor=top, tex="DOOR3")
    landing = m.room(rect(512, 128, 880, 384), floor=top, ceil=top + 128, light=176, wall="AMWALL1",
                     name="landing")
    crates(m, landing, 528, 144, 592, 208, 48)
    m.lift(rect(512, 384, 640, 512), low=top, high=512, ceil=640)
    m.room(rect(512, 512, 640, 576), floor=512, ceil=640, light=192, wall="AMWALL1", name="cab hall")

    # --- the cab: glass all round, consoles
    cab = m.room(octagon(576, 872, 320), floor=512, ceil=640, ftex="AMCARPT", light=208, wall="AMTOWER",
                 name="cab")
    for x1, y1, x2, y2 in ((352, 752, 416, 992), (736, 752, 800, 992), (480, 1040, 672, 1088)):
        block(m, cab, x1, y1, x2, y2, 40, "AMDESK")
    lights(m, cab, [(576, 872)], size=96)

    # --- the roof deck (red door): the boss, and the radar mast with the exit inside
    m.door(rect(512, 1168, 640, 1184), floor=512, tex="AMDOORR", key="red")
    roof = m.room(octagon(576, 1598, 448), floor=512, ceil=768, ftex="AMCONCF", ctex=SKY, light=224,
                  wall="AMCONC", name="roof")
    mast = m.door(rect(528, 1550, 624, 1646), floor=512, tex="METAL", remote=True, tag=MAST_TAG,
                  parent=roof)
    m.boss_opens.append(mast)
    m.pillar(mast, rect(560, 1582, 592, 1614))
    m.line((592, 1582), (560, 1582), special=11, mid="SW1EXIT", xoff=0)
    for cx, cy in ((320, 1400), (832, 1400), (320, 1800), (832, 1800)):
        m.pillar(roof, rect(cx - 32, cy - 32, cx + 32, cy + 32))

    # --- secret: the radar workshop off the lobby
    m.room(rect(368, -416, 624, -160), floor=0, ceil=128, ftex="AMCONCF", light=144, wall="AMBAGW",
           special=9, name="secret")
    m.door(rect(624, -352, 640, -224), floor=0, tex="AMWALL1")
    m.line((640, -352), (640, -224), flags=SECRET_LINE)

    # --- things
    m.thing(960, -440, PLAYER, 90)
    m.things_at(SHOTGUY, [(720, -100), (1200, -100)], 270)
    m.thing(960, -200, CHAINGUY, 270, MH)
    m.things_at(SHELLBOX, [(700, -460), (1220, -460)])
    m.thing(1220, -200, ROCKETBOX)
    # stairs
    m.things_at(IMP, [(1216, 96), (1440, 384), (1152, 544), (992, 256)], 180)
    m.things_at(IMP, [(1440, 560), (992, 384)], 180, MH)
    m.thing(1088, 96, DEMON, 0, MH)
    m.thing(1440, 96, MEDKIT)
    m.thing(992, 540, ROCKET)
    # landing
    m.thing(700, 300, REDCARD)
    m.things_at(KNIGHT, [(800, 200)], 180)
    m.thing(620, 330, KNIGHT, 180, HARD)
    m.thing(820, 340, MEDKIT)
    m.thing(560, 260, CELLPACK)
    # cab
    m.thing(576, 1000, PLASMA)
    m.things_at(CELL, [(450, 700), (700, 700)])
    m.things_at(CHAINGUY, [(500, 900), (650, 900)], 270, MH)
    m.thing(576, 700, REVENANT, 270, HARD)
    m.things_at(IMP, [(420, 1050), (730, 1050)], 270)
    m.thing(576, 800, MEDKIT)
    # roof
    m.thing(576, 1880, CYBER, 270, MH)
    m.things_at(BARON, [(420, 1880), (732, 1880)], 270, EASY)
    m.things_at(CACO, [(300, 1600), (850, 1600)], 270, MH)
    m.things_at(IMP, [(330, 1320), (822, 1320)], 270)
    m.things_at(ROCKETBOX, [(260, 1500), (890, 1500)])
    m.things_at(CELLPACK, [(260, 1700), (890, 1700)])
    m.thing(576, 1260, SOUL)
    m.thing(420, 1960, MEDKIT, 0)
    m.thing(732, 1960, MEDKIT, 0)
    # secret
    m.thing(496, -288, MEGA)
    m.thing(420, -380, LAUNCHER)
    return m
