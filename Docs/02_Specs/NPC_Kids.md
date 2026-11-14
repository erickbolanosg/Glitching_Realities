# Spec — NPC Kids

**Owners:** Andrew (AI, logic) · Brianna (models, animation, VFX) · **Assets:** `BP_Kid`, `BP_KidAIController`, `ST_Kid`, `ABP_Kid` · **Requirements:** FR-NPC-*

## 1. Population
| World | Count | Notes |
|---|---|---|
| Real | 5 | One per Real room (Classroom, Cafeteria, Gym, Library, Lab) |
| Cut | +3 to +5 (8–10 total) | Tagged `World.Cut`; same models, glitch material `MI_Kid_Cut`, different outfit color |

Looks: 3 base models × color variations = 5 looks. Variation is set by `KidLook` (data asset) on the placed instance.

## 2. Components
- `CharacterMovement`: walk 180 cm/s, run (chase) 380 cm/s. The cat sprint (550) can always escape a chase.
- `AIPerception` on the controller:
  - Sight: radius 900 cm, lose 1100 cm, peripheral half-angle 60°. Against a crouched cat the effective radius is ×0.5 (checked in the StateTree when sensing).
  - Hearing: radius 1200 cm; reacts to tags `Meow`, `ObjectFall`, `Scratch`.
- `StateTree` (`ST_Kid`) running on the controller (`StateTreeAIComponent`).

## 3. State machine
| # | State | Enter when | Behavior | Exit |
|---|---|---|---|---|
| 1 | **Routine** | Default; or 10 s without sensing the cat | Loop room activity at an `ActivitySpot` (Read, Eat, PlayBall, Talk, Exercise, Sit) or patrol 2–4 points | Senses cat → Curious; hears `ObjectFall`/`Scratch` or sees a moved mission prop → Annoyed; hears `Meow` → Lured |
| 1b | **Lured** | Hears `Meow` while in Routine | Walk to noise location, look around 3 s | Back to Routine (spot is now 3–6 s farther away, which is the gameplay opening) |
| 2 | **Curious** | Sees the cat, no mess | Turn head/body to the cat, follow ≤3 m for ≤5 s | Cat does a mess action in sight → Annoyed; lost sight 10 s → Routine |
| 3 | **Annoyed** | Sees/hears mess | `Point_Shout` montage, walk to the object, `Pick_Up`, put it back at its original transform (if `Mission` prop not yet completed) | Sees the cat do a 2nd mess within 15 s, or sees a Convert attempt → Alert; else → Routine |
| 4 | **Alert** | As above | Shout (`SFX_Kid_Alert`), alert kids within 1500 cm in the same room (they also go Alert), chase the cat. If within 90 cm → `Grab_Cat` → broadcast `OnCatCaught` | Lost the cat for 10 s → Routine |
| 5 | **Startled** | Hit by Pounce | Stunned 2 s, `Startled` montage. Convertible. | → Annoyed |
| 6 | **Converted** | `Convert()` succeeded | Stop AI, glitch + smoke VFX (`NS_KidConvert`), swap to a cat mesh (`SK_Cat` with `M_Cat_Hologram`), wander slowly; broadcast `OnKidConverted` | Final |

Kids never damage the cat. Being caught only respawns the cat.

## 4. Interfering with objectives
- Pick up and restore dropped mission props (Annoyed).
- Close doors tagged `Door.Closable` when Alert ends in that room.
- Stand in front of a target prop: one kid per room may use an `ActivitySpot` placed next to the mission target.

## 5. Placement contract (for the level)
Each room's `LI_<Room>` contains: `BP_ActivitySpot` actors (with `Activity` enum), optional `BP_PatrolPath` (points), kid spawn points with `KidLook`, and a NavMesh bounds volume covering the floor.

## 6. Animations
Retargeted from Manny via IK Retargeter: Idle, Walk, Run, Jump. New: `Sit_Idle`, `Reading`, `Eating`, `Play_Ball`, `Talk`, `Exercise`, `Startled`, `Point_Shout`, `Pick_Up`, `Grab_Cat`.

## 7. Debug
`ShowDebug AI` and a world-text label above each kid with its current state (Development builds only).
