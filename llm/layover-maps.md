# Layover maps

All on `freedoom2.wad` (MAPxx). Monster counts are easy/medium/hard as reported by the
build at 0.1.0. Every map has one secret (sector special 9) behind a wall-textured door with
the SECRET line flag. Previews: `docs/maps/mapNN.png`.

| Map | Title | Music | Par | Monsters | Keys |
|---|---|---|---|---|---|
| MAP01 | Curbside | D_RUNNIN | 90 | 13/20/23 | blue |
| MAP02 | Security | D_STALKS | 120 | 14/22/25 | yellow |
| MAP03 | Concourse B | D_COUNTD | 180 | 25/36/39 | blue, yellow |
| MAP04 | Baggage Underworld | D_BETWEE | 200 | 16/28/30 | red |
| MAP05 | The Tarmac | D_DOOM | 240 | 24/34/38 | yellow, blue |
| MAP06 | Control Tower | D_EVIL | 300 | 13/20/22 | red |

## MAP01 Curbside

Start on the road (sky) by a shuttle bus (96-high block with AMPLANE face), sidewalk, three
sliding glass doors into the check-in hall (desks, seats, queue ropes, pillars, signs,
departures board). Staff door (DOOR3) north to baggage make-up (belt flaps = window sectors
with scrolling belt flats, scrolling belts), then into the airline office: **blue keycard**
behind the desk. Blue door (AMDOORB) east -> security corridor with x-ray blocks -> exit room,
exit switch SW1GRAY1 on the east wall (special 11). Secret: duty-free stockroom west of the
hall (green armour, shell box). Shotgun in the hall.

## MAP02 Security

Queue hall with three rope lanes. The checkpoint's three shutters (AMBAGW) are **remote
doors** opened by the S1 switch (103) in the security office. Route: staff door east ->
corridor -> **lift** (62 below / 88 above) up to the office (floor 128), which looks over
airside through a window sector. Confiscated goods room beside it: **yellow keycard**.
Back down, through the shutters into airside (seats, duty-free kiosk, demons), crew door
(AMDOORY, yellow) north -> exit. Secret: smoking room west of airside (soulsphere). Chaingun.

## MAP03 Concourse B

Start on the terminal train platform. 3072-long concourse with four moving walkway strips
(253, ±4 units/tic, east lanes y 96-160, west lanes 224-288), signs across and along. Four
gates (carpet, seats, desk). Gate B2: door -> jet bridge -> plane cabin (seat rows, aisle):
**blue keycard** at the aisle end; crossing into the cabin (W1 special 2) opens the food-court
**kitchen doors** (remote, tag) releasing imps/demons behind you. Blue door at the concourse's
east end -> lounge; the **yellow keycard** on a dais whose edges (W1 2) open a closet of
spectres/demon. Gate B4: yellow door -> bridge -> cabin -> cockpit exit switch. Secret:
duty-free room south of the west concourse (blue armour, backpack). Chaingun at gate B6.

## MAP04 Baggage Underworld

Baggage claim with two octagonal carousels (ring carries you north, centre is a block).
Staff door north -> corridor (dark maintenance room west) -> conveyor tunnel east (253, +3)
whose entry line (73 WR) starts a slow **crusher** mid-tunnel (strobe light, AMHAZ walls,
explicit upper textures) -> drop 128 into the sorting hall (scrolling belt blocks, NUKAGE1
"fuel leak" damaging 5%, cacodemon). **Lift** north up to lost luggage: **red keycard** and
the super shotgun. Back down, teleporter pad (GATE1, 97) in the sorting hall -> baggage claim.
Red door (AMDOORR) east -> six 16-unit steps -> exit. Secret: west of baggage claim
(backpack, rockets). Rocket launcher in the sorting hall.

## MAP05 The Tarmac

Start in the gate building, glass door onto a 3584x2560 sky apron: taxiway lines (AMTARL
strips), runway (AMRUNW), two airliners (fuselage 112-high blocks, swept wings 24 high you
can stand on, engines on the wings), baggage carts, catering truck, barrels. **Yellow
keycard** on the upper wing of the plane on stand 2. Yellow door west -> fuel depot (tanks,
truck): switch (103) on its west wall opens the 512-wide **hangar door** (remote, AMHANGR) on
the apron's east side. Hangar: **blue keycard**, rocket launcher, knight/baron. Blue door
north -> tower base -> exit. Secret: crew rest room west of the gate building (soulsphere).

## MAP06 Control Tower

Lobby -> door -> 13 steps of 20 spiralling round a solid core in a 448-high shaft (top 260)
-> landing: **red keycard**, knights -> lift to 512 -> glass cab (AMTOWER walls, consoles,
plasma rifle, revenant on hard) -> red door -> roof deck (sky octagon, four pillars). The
radar mast in the centre is a **remote door with `parent=roof`** (tag 99) with a pillar inside
carrying the exit switch (SW1EXIT); UMAPINFO `bossaction = Cyberdemon, 2, 99` (medium/hard
place a Cyberdemon) and `bossaction = BaronOfHell, 2, 99` (easy places two barons) open it.
UMAPINFO then shows the ending `intertext` over AMTARM and the cast call (`endcast`).
Secret: radar workshop west of the lobby (megasphere, rocket launcher).

Verified in a desktop browser: every map loads; MAP06's mast opened after `tntem` killed
everything (automap showed the pillar's walls, 20/20 monsters).
