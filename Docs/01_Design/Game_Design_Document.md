# Glitching Realities — Game Design Document

> Source of truth for *what* the game is. Implementation details live in [`../02_Specs`](../02_Specs), testable requirements in [`../03_Requirements`](../03_Requirements), and the schedule in [`../04_Production`](../04_Production).

| | |
|---|---|
| **Engine** | Unreal Engine 5.8 |
| **Platform** | Windows PC, keyboard + mouse |
| **Genre** | 3D sandbox / light stealth, third person |
| **Jam theme** | "Director's Cut" |
| **Rating target** | 13+ |
| **Deadline** | Sunday 2026-11-15, 12:00 (UTC-6) |

---

## 1. Concept

**Glitching Realities** is a 3D sandbox set in a school. You are an evil, glitched cat who can toggle between the "official" release of the game and its **Cut version**: everything the developers removed comes back. Every mechanic can be seen within 5 minutes; seeing everything takes about 2 hours.

**Theme fit ("Director's Cut"):** the cat bends reality and exposes the director's cut: more map, more kids, more missions. The game "admits" it had too much content and trimmed it. Running gag: some of it was cut "to meet the jam's 13+ rating".

### Pillars
1. **Freedom** — no mission depends on another. The player chooses where to go.
2. **Contrast** — switching worlds always reveals something new (rooms, objects, kids, paths).
3. **Cat chaos** — knocking things over, scratching, meowing and getting in the way *is* the gameplay.

---

## 2. Story and tone

The cat used to be a teacher/experimenter at the school who accidentally turned into a cat. Frustrated, it is now evil: its goal is to **turn the kids into cats**, and to annoy everyone for fun.

- **Tone:** mysterious and unsettling, with dry humor in the details.
- **Narration:** wordless, environmental storytelling only (blackboard notes, the professor's lab, photos, objects that exist only in the Cut world).
- **Ending:** open and non-linear. The underlying goal is converting kids; there is no mandatory final scene.
- **Conversion** is a direct cat action. Room missions are independent chaos objectives; converting kids can happen at any time.

---

## 3. The two worlds

The player switches world at any time with **Q** (3 s cooldown). Everything in the Real world also exists in the Cut world; the Cut world only **adds** what was deleted, and that added content looks glitched.

| Aspect | Real world | Cut world (Director's Cut) |
|---|---|---|
| Palette | Normal colors, slightly desaturated | Subtle purple/blue tint |
| Real objects | Normal | Still intact, with collision |
| Deleted objects | Do not exist | Flicker, broken textures, no/partial collision, sometimes overlapping real objects |
| Map | 5 rooms + hallway/courtyard hub | +3 rooms and extra passages |
| Kids | 5 | 8–10 (extras are "cut" kids with glitch material) |
| Cat | Black with white stripes | Cyan/magenta, twitches now and then |
| Extra abilities | — | Glitch Teleport, phase through glitched objects |
| Camera | Clean | Chromatic aberration and soft scanlines |

**13+ gag:** in the Cut world there is a taped-off door with a sign *"Content removed to meet the rating"*, or a pixelated room that cannot be opened.

System design: [`World_Switch.md`](../02_Specs/World_Switch.md).

---

## 4. The cat

All actions are available from the start so the whole kit is visible in 5 minutes. Full parameters: [`Cat_Character.md`](../02_Specs/Cat_Character.md).

| Action | Key | World | Cooldown |
|---|---|---|---|
| Move / camera | WASD / mouse | Both | — |
| Sprint | Shift (hold) | Real | — |
| Jump | Space | Both | — |
| Crouch | Ctrl | Both | — |
| Push / knock over | E | Both | 0.5 s |
| Scratch | Left mouse | Both | 0.6 s |
| Pounce | Right mouse | Both | 4 s |
| Meow | R | Both | 3 s |
| Corrupt | F (hold 1 s) | Both | 8 s |
| Switch world | Q | Both | 3 s |
| Glitch Teleport | Shift (press) | Cut only | 5 s |
| Phase through glitched objects | Passive | Cut only | — |
| Convert kid | T (hold 2 s) | Both | 15 s |

- **Caught:** the cat respawns at the room entrance. No health, no death.
- **Look:** one quadruped-rigged cat model. Real world = black with white stripes material; Cut world = the current cyan/magenta glitch material adapted to a skinned mesh, plus a twitch animation every 6–10 s.

---

## 5. Rooms and missions

A central hallway with a courtyard is the hub; every room can be entered in any order. Each mission takes 1–3 minutes with similar difficulty. Details: [`Missions.md`](../02_Specs/Missions.md).

| Room | World | Mission | Mechanics showcased |
|---|---|---|---|
| Classroom | Real | Ruin the class: knock 5 items off the teacher's desk and scratch the blackboard | Push, scratch, jump |
| Cafeteria | Real | Drop the birthday cake: meow to lure kids away, then push it off the table | Meow, push |
| Gym | Real | Tear 3 mats without being seen; hide under the bleachers | Crouch, scratch, stealth |
| Library | Real | Topple a bookshelf domino-style by climbing the shelves | Jump, pounce |
| Lab | Real | Corrupt the professor's computer; reveals who the cat is | Corrupt, story |
| Auditorium / film set | Cut | Ruin the "director's cut" shoot: corrupt the camera and drop the spotlight | Teleport, corrupt |
| Server Room | Cut | Delete 3 "files" by phasing through glitched walls | Phase, corrupt |
| Professor's Office | Cut | Find and knock down the transformation formula; more story | Exploration, push |
| Closed Wing (13+) | Cut | No mission — the "content removed" gag | — |

- **Short plan (if behind schedule):** 3 Real rooms (Classroom, Cafeteria, Gym) + 2 Cut rooms (Auditorium, Server Room) are enough for the 5-minute demo.
- **Contrast in Real rooms:** every Real room also changes in the Cut world (extra furniture, one more kid, a passage that only exists there).

---

## 6. NPCs: the kids

Kids live their routine and do not attack on sight; they react to **mess**. 5 in the Real world, 8–10 in the Cut world. Details: [`NPC_Kids.md`](../02_Specs/NPC_Kids.md).

States: **Routine → Curious → Annoyed → Alert → back to Routine** after ~10 s without seeing the cat. Kids pick up dropped objects, close doors, stand in front of targets and move things around. Implementation: StateTree (`GameplayStateTree` plugin already enabled) + AI Perception (sight + hearing).

---

## 7. UI and menus

- **Main menu:** title + Start, Options, Credits, Quit. Temporary background: slow camera over the level with the world glitch.
- **Options:** graphics quality (Low/Medium/High), volume, mouse sensitivity, fullscreen.
- **HUD:** ability icons with radial cooldowns (Cut-only abilities dimmed in the Real world), current world indicator, "Kids converted X/N" counter, contextual prompt ("E — Knock over").
- **Pause:** Resume, Options, Quit to menu.
- Template touch controls are removed.

Details: [`UI_HUD.md`](../02_Specs/UI_HUD.md), [`Audio.md`](../02_Specs/Audio.md).

---

## 8. Performance and lighting

The project ships with a **lightweight rendering profile** (no Lumen, ray tracing, Nanite or Virtual Shadow Maps) in `Config/DefaultEngine.ini`. See [`Level_and_Environment.md`](../02_Specs/Level_and_Environment.md#lighting-and-performance) and [`Non_Functional_Requirements.md`](../03_Requirements/Non_Functional_Requirements.md).

---

## 9. Decisions log

| Date | Decision |
|---|---|
| 2026-11-13 | Setting is a school. Two-world toggle on Q. |
| 2026-11-13 | Lightweight rendering profile (no Lumen/Nanite/VSM/RT). |
| 2026-11-14 | All project content (docs, in-game text, assets, issues) is in **English**. |
| 2026-11-14 | Shift: hold = Sprint in Real world; press = Glitch Teleport in Cut world (no sprint in Cut). |
| 2026-11-14 | Short plan uses Classroom, Cafeteria, Gym (the original "Dormitory" did not exist in the room list). |
| 2026-11-14 | Cat skeleton, global scale and world system are frozen after Stage 2 (Building). |
