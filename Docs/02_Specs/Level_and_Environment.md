# Spec — Level and Environment

**Owner:** Javier · **Assets:** `Lvl_School`, `LI_<Room>`, modular kit · **Requirements:** FR-LVL-*, NFR-PERF-*

## 1. Structure
- Main level **`Lvl_School`** (World Partition off, One File Per Actor on).
- **One room = one Level Instance** in `/Game/Levels/Rooms`:

| Level instance | World | Notes |
|---|---|---|
| `LI_Hallway` | Both | Central hub + courtyard; doors to every room; cat start point |
| `LI_Classroom` | Real (+Cut extras) | |
| `LI_Cafeteria` | Real (+Cut extras) | |
| `LI_Gym` | Real (+Cut extras) | Bleachers with 25 cm crawl gap |
| `LI_Library` | Real (+Cut extras) | 4 bookshelves in a domino line |
| `LI_Lab` | Real (+Cut extras) | Professor's computer |
| `LI_Auditorium` | Cut | Film set; stage gap needs teleport |
| `LI_ServerRoom` | Cut | Glitched walls |
| `LI_ProfessorOffice` | Cut | Story props |
| `LI_ClosedWing` | Cut | 13+ gag only |

- Cut rooms are reached through passages tagged `World.Cut` (walls that disappear, holes, extra doors). In the Real world those openings are closed by actors tagged `World.Real`.
- Every room has: `BP_RoomVolume` (room name), one `Respawn.<Room>` point at the entrance, NavMesh bounds, kid spots (see [`NPC_Kids.md`](NPC_Kids.md#5-placement-contract-for-the-level)), mission actor (see [`Missions.md`](Missions.md)).

## 2. Building rules
1. **Blockout first** with gray cubes at final dimensions; props and lights only after the blockout is approved in the group playtest.
2. **Modular kit on a 4 m grid:** wall 400×300 cm, door 120×220 cm, window, floor 400×400 cm, half-wall. Built with Modeling Mode (`ModelingToolsEditorMode` is enabled). Snap 10 cm, rotation 90°.
3. **Scale** is fixed (see [`Conventions.md`](Conventions.md#4-scale-frozen-after-stage-2)): tables 75 cm, crawl gaps 25 cm, shelves ≤200 cm.
4. **One person per room at a time.** Announce before editing someone else's Level Instance.
5. Real-world contrast: every Real room gets at least one `World.Cut` addition (extra furniture, one kid, or a passage).

## 3. Props
- Generated with AI (Tripo; Meshy/Hyper3D fallback), 300–2,000 tris, 512 px textures, convex collision.
- Small props: `Simulate Physics`, mass 0.5–5 kg, derived from `BP_InteractableBase`.
- Prop list per room: see [`Art_Pipeline.md`](Art_Pipeline.md#4-props).

## Lighting and performance
Rendering profile is already set in `Config/DefaultEngine.ini`:

| Setting | Value | Why |
|---|---|---|
| Global illumination | None | Lumen is the heaviest feature |
| Reflections | Screen Space | Cheap |
| Shadows | Classic shadow maps (VSM off) | VSM needs a strong GPU |
| Mesh Distance Fields | Off | Only used by Lumen |
| Ray tracing / Nanite | Off | Low-poly assets don't need them |
| Anti-aliasing | TAA | Cheaper than TSR |
| Static lighting | Allowed | Lets us bake if needed |

Rules:
1. Directional light + Sky Light **Movable**; Sky Light "Real Time Capture" off, recapture after changes.
2. Interiors: few Point/Spot lights; **Cast Shadows off** except 1–2 per room.
3. Without GI interiors look flat: add 1–2 dim fill lights per room, or Contact Shadow Length 0.02 on the main light.
4. Optional final pass: lights to Static + *Build Lighting Only*.
5. Work in the editor at Scalability **Medium/Low**.

## 4. Post process
`PP_World` is shared and driven by `BP_WorldManager` (see [`World_Switch.md`](World_Switch.md#5-post-process)). Do not place other unbound post-process volumes.
