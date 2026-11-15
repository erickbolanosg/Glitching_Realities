# Spec — Missions

**Owner:** Andrew · **Assets:** `BP_MissionBase`, `BP_Mission_<Room>`, `BP_GameState` · **Requirements:** FR-MIS-*

## 1. Framework
- **One mission = one Blueprint inside its room's Level Instance.** It only watches actors tagged `Mission.<Room>` in that room and never reads another mission.
- `BP_MissionBase` (Actor):
  - Properties: `MissionId` (Name), `DisplayName` (Text), `World` (`E_World` or Both), `Objectives` (array of `S_Objective { Description, Required, Current }`).
  - `ProgressObjective(Index, Amount)`, `IsComplete()`.
  - Broadcasts `OnObjectiveProgress` and, once, `OnMissionCompleted(MissionId)`.
- `BP_GameState` keeps `CompletedMissions`, `KidsConverted`, `KidsTotal` and exposes them to the HUD.
- Missions in the Cut world are inactive (no progress) while in the Real world, and vice versa.

## 2. Mission props
`BP_InteractableBase` children implement `BPI_Interactable` (see Conventions). Flags on each prop: `Pushable`, `Scratchable`, `Corruptible`, `BreaksOnCorrupt`, `LosesCollisionOnCorrupt`. Small props: `Simulate Physics`, convex collision, mass 0.5–5 kg.

A prop counts as **knocked over** when it rests ≥40 cm below its start height or its up vector tilts >60°.

## 3. Missions

| ID | Room | World | Objectives | Fail/pressure | Mechanics |
|---|---|---|---|---|---|
| `M_Classroom` | Classroom | Real | Knock 5 `Mission.Classroom` items off the teacher's desk; scratch the blackboard 3 times | Kid restores items when Annoyed | Push, Scratch, Jump |
| `M_Cafeteria` | Cafeteria | Real | Push the birthday cake off the table | 2 kids sit at the table; must be lured with Meow first | Meow, Push |
| `M_Gym` | Gym | Real | Scratch 3 mats while not being seen (a scratch seen by a kid does not count) | Patrolling kid; bleachers give cover (crouch) | Crouch, Scratch, Stealth |
| `M_Library` | Library | Real | Topple the first bookshelf; it falls domino-style (physics chain of 4 shelves) | Climb via 2 jumps; Pounce from the top gives the needed impulse | Jump, Pounce |
| `M_Lab` | Lab | Real | Corrupt the professor's computer | Reveals a story clue (monitor shows the professor's photo) | Corrupt, Story |
| `M_Auditorium` | Auditorium | Cut | Corrupt the film camera; knock down the spotlight | Reached via a Cut passage; teleport over the stage gap | Teleport, Corrupt |
| `M_ServerRoom` | Server Room | Cut | Delete 3 floating "files" (Corrupt) | Files are behind `Glitched` walls (phase) | Phase, Corrupt |
| `M_ProfessorOffice` | Professor's Office | Cut | Find and knock down the transformation formula | Hidden on a high shelf; story props | Explore, Push |
| — | Closed Wing (13+) | Cut | No mission: taped door + "Content removed to meet the rating" sign | — | — |

Each mission must be completable in 1–3 minutes by someone who knows the room.

## 4. Feedback
- On objective progress: small HUD toast "2/5 items knocked over".
- On completion: HUD banner, `SFX_MissionComplete`, a short glitch pulse (`MPC_World.SwitchPulse`).
