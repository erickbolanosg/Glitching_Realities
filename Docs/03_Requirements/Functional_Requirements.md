# Functional Requirements

Each requirement is testable in a Development build. **Priority:** `Must` = needed for the 5-minute demo · `Should` = full game · `Could` = if time allows. Issues reference these IDs.

## Cat (FR-CAT)
| ID | Requirement | Priority | Spec |
|---|---|---|---|
| FR-CAT-01 | The player moves the cat with WASD and rotates the camera with the mouse; the cat faces its movement direction. | Must | [Cat §1–2](../02_Specs/Cat_Character.md) |
| FR-CAT-02 | Space makes the cat jump high enough to land on a 75 cm table. | Must | Cat §1 |
| FR-CAT-03 | Ctrl toggles crouch; crouched, the cat fits through 25 cm gaps and kids' sight range against it is halved. | Must | Cat §5 |
| FR-CAT-04 | Holding Shift in the Real world sprints at a speed higher than any kid's chase speed. | Must | Cat §1 |
| FR-CAT-05 | E pushes the interactable in front of the cat; physics props fall. Cooldown 0.5 s. | Must | Cat §4 |
| FR-CAT-06 | Left mouse scratches the interactable in front; scratchable props show damage. Cooldown 0.6 s. | Must | Cat §4 |
| FR-CAT-07 | Right mouse pounces forward; a kid hit is Startled for 2 s, a prop hit receives a strong impulse. Cooldown 4 s. | Must | Cat §4 |
| FR-CAT-08 | R meows; kids within 8 m in Routine walk to the cat's position. Cooldown 3 s. | Must | Cat §4, Kids §3 |
| FR-CAT-09 | Holding F for 1 s corrupts the targeted object (glitch look, may break or lose collision). Releasing early cancels without cooldown. Cooldown 8 s. | Must | Cat §4 |
| FR-CAT-10 | Holding T for 2 s next to an unaware or Startled kid converts it into a cat; if the kid sees the cat during the hold, the action is cancelled and the kid becomes Alert. Cooldown 15 s. | Must | Cat §4 |
| FR-CAT-11 | In the Cut world, pressing Shift teleports the cat ~6 m forward through `Glitched` actors, never into solid geometry. Cooldown 5 s. | Must | Cat §4 |
| FR-CAT-12 | In the Cut world, the cat passes through actors tagged `Glitched`. | Should | Cat §4 |
| FR-CAT-13 | When caught, the cat respawns at the current room's entrance within 2 s; no health or death exists. | Must | Cat §5 |
| FR-CAT-14 | Every action plays its animation (or placeholder) and sound. | Should | Cat §6, Audio |
| FR-CAT-15 | The cat uses the black/white material in the Real world and the glitch material + periodic twitch in the Cut world. | Should | Cat §7 |
| FR-CAT-16 | Actions are blocked while in the air (except movement) and while another action is playing (except Meow). | Should | Cat §3, §5 |

## World switch (FR-WLD)
| ID | Requirement | Priority | Spec |
|---|---|---|---|
| FR-WLD-01 | Q switches between Real and Cut worlds with a 0.3 s glitch transition. Cooldown 3 s. | Must | [World §3](../02_Specs/World_Switch.md) |
| FR-WLD-02 | Actors tagged `World.Cut` are hidden and non-colliding in the Real world; `World.Real` actors are hidden in the Cut world; untagged actors exist in both. | Must | World §2 |
| FR-WLD-03 | After a switch the cat is never stuck inside geometry. | Must | World §3 |
| FR-WLD-04 | The Cut world applies a purple/blue tint, chromatic aberration and soft scanlines; the Real world is slightly desaturated. | Should | World §5 |
| FR-WLD-05 | Cut-only kids, missions and abilities are inactive in the Real world. | Must | World §2, §6 |
| FR-WLD-06 | Music crossfades between `MUS_Real` and `MUS_Cut` on switch. | Could | Audio §3 |

## NPC kids (FR-NPC)
| ID | Requirement | Priority | Spec |
|---|---|---|---|
| FR-NPC-01 | 5 kids exist in the Real world and 8–10 in the Cut world. | Must (min 3 Real + 2 Cut) | [Kids §1](../02_Specs/NPC_Kids.md) |
| FR-NPC-02 | Kids perform a room routine until they sense the cat or a mess. | Must | Kids §3 |
| FR-NPC-03 | A kid that sees the cat becomes Curious and looks at/follows it without catching it. | Should | Kids §3 |
| FR-NPC-04 | A kid that sees or hears a mess becomes Annoyed, points/shouts and restores the object. | Must | Kids §3 |
| FR-NPC-05 | Repeated mess or a seen conversion makes the kid Alert: it alerts nearby kids, chases and can catch the cat. | Must | Kids §3 |
| FR-NPC-06 | Kids return to Routine after ~10 s without sensing the cat. | Must | Kids §3 |
| FR-NPC-07 | Kids hear Meow (8 m), falling objects and scratches. | Must | Kids §2 |
| FR-NPC-08 | A converted kid shows the conversion VFX, becomes a cat and increases the counter. | Must | Kids §3 |

## Missions (FR-MIS)
| ID | Requirement | Priority | Spec |
|---|---|---|---|
| FR-MIS-01 | Each room has at most one mission that only depends on objects of that room. | Must | [Missions §1](../02_Specs/Missions.md) |
| FR-MIS-02 | Missions can be completed in any order. | Must | Missions §1 |
| FR-MIS-03 | The demo set (Classroom, Cafeteria, Gym, Auditorium, Server Room) is implemented. | Must | Missions §3 |
| FR-MIS-04 | Library, Lab and Professor's Office missions are implemented. | Should | Missions §3 |
| FR-MIS-05 | Mission progress and completion are shown on the HUD. | Must | Missions §4 |
| FR-MIS-06 | The Closed Wing shows the 13+ "content removed" gag. | Could | Missions §3 |

## Level (FR-LVL)
| ID | Requirement | Priority | Spec |
|---|---|---|---|
| FR-LVL-01 | The school has a hub hallway connecting every Real room. | Must | [Level §1](../02_Specs/Level_and_Environment.md) |
| FR-LVL-02 | Cut rooms are only reachable in the Cut world. | Must | Level §1 |
| FR-LVL-03 | Every Real room has at least one Cut-world addition. | Should | Level §2 |
| FR-LVL-04 | Every room has a respawn point and NavMesh coverage. | Must | Level §1 |
| FR-LVL-05 | Environmental story props (blackboard notes, photos, lab) exist. | Should | GDD §2 |

## UI (FR-UI)
| ID | Requirement | Priority | Spec |
|---|---|---|---|
| FR-UI-01 | Main menu with Start, Options, Credits, Quit. | Must | [UI §2](../02_Specs/UI_HUD.md) |
| FR-UI-02 | Options for graphics quality, volume, mouse sensitivity and fullscreen, persisted between sessions. | Must | UI §3 |
| FR-UI-03 | HUD shows ability cooldowns, world indicator, kids counter and context prompt. | Must | UI §4 |
| FR-UI-04 | Esc pauses the game with Resume, Options, Quit to menu. | Must | UI §5 |
| FR-UI-05 | Credits list the team and third-party licenses. | Should | UI §7 |

## Audio (FR-AUD)
| ID | Requirement | Priority | Spec |
|---|---|---|---|
| FR-AUD-01 | Every cat action and kid reaction has a sound. | Should | [Audio §2](../02_Specs/Audio.md) |
| FR-AUD-02 | Music plays in menu and in game; volume follows Options. | Must | Audio §1 |
