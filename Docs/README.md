# Documentation

| Folder | Read it when you need… |
|---|---|
| [`01_Design`](01_Design) | **What** the game is: concept, worlds, cat, rooms, kids, UI ([GDD](01_Design/Game_Design_Document.md)) |
| [`02_Specs`](02_Specs) | **How** each system works: exact values, assets, events |
| [`03_Requirements`](03_Requirements) | **What must be true** for the game to be done: functional and non-functional requirements with IDs |
| [`04_Production`](04_Production) | **When and who**: stages, issues per person, Git workflow |

## Specs
| Spec | Owner |
|---|---|
| [Conventions and shared contracts](02_Specs/Conventions.md) — folders, prefixes, scale, tags, interfaces, events | Everyone (changes announced) |
| [Cat character](02_Specs/Cat_Character.md) — movement, input, abilities, animation | Erick |
| [World switch](02_Specs/World_Switch.md) — Real ↔ Cut system | Erick |
| [NPC kids](02_Specs/NPC_Kids.md) — AI states, perception, placement | Andrew / Brianna |
| [Missions](02_Specs/Missions.md) — framework and every room mission | Andrew |
| [Level and environment](02_Specs/Level_and_Environment.md) — rooms, building rules, lighting, performance | Javier |
| [Art pipeline](02_Specs/Art_Pipeline.md) — budgets, workflow, animation and prop lists, VFX | Brianna / Javier |
| [UI and HUD](02_Specs/UI_HUD.md) | Leonardo |
| [Audio](02_Specs/Audio.md) | Leonardo |

## Requirements
- [Functional requirements](03_Requirements/Functional_Requirements.md) (`FR-*`)
- [Non-functional requirements](03_Requirements/Non_Functional_Requirements.md) (`NFR-*`)

## Production
- [Stages and schedule](04_Production/Stages_and_Schedule.md) — milestones and the issue table
- [Team and ownership](04_Production/Team_and_Ownership.md)
- [Git workflow](04_Production/Git_Workflow.md)

## Rules for docs
- English only.
- When a value changes in the game, update the spec in the same PR.
- Requirements keep their IDs forever; deleted ones are marked ~~struck through~~, never reused.
