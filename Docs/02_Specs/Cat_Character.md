# Spec — The Glitched Cat (player character)

**Owner:** Erick · **Blueprints:** `BP_Cat` (Character), `BPC_CatAbilities` (Actor Component), `ABP_Cat` · **Requirements:** FR-CAT-*, FR-WLD-*

## 1. Character setup

| Property | Value |
|---|---|
| Parent class | `Character` (replaces `BP_ThirdPersonCharacter`) |
| Capsule | radius 18 cm, half-height 16 cm (fits 25 cm gaps when crouched) |
| Mesh | `SK_Cat` (quadruped), ~45 cm long; placeholder `SM_GlitchCat` scaled to match until delivered |
| Camera | Spring arm 220 cm, socket offset Z +40, lag enabled (speed 12), collision test on |
| Walk speed | 300 cm/s |
| Sprint speed | 550 cm/s (Real world only, hold Shift) |
| Crouch speed | 140 cm/s; crouched half-height 10 cm |
| Jump Z velocity | 520 cm/s (reaches 75 cm tables); air control 0.6 |
| Rotation | Orient rotation to movement; controller yaw not used |

## 2. Input (Enhanced Input)

Mapping context `IMC_Cat` (priority 0). All actions use `IA_<Name>`.

| Input action | Key | Trigger |
|---|---|---|
| `IA_Move` | WASD | Axis2D |
| `IA_Look` | Mouse XY | Axis2D |
| `IA_Jump` | Space | Pressed |
| `IA_Crouch` | Left Ctrl | Pressed (toggle) |
| `IA_Sprint` | Left Shift | Hold (Real) |
| `IA_Teleport` | Left Shift | Pressed (Cut) — same key, routed by current world |
| `IA_Push` | E | Pressed |
| `IA_Scratch` | Left mouse | Pressed |
| `IA_Pounce` | Right mouse | Pressed |
| `IA_Meow` | R | Pressed |
| `IA_Corrupt` | F | Hold 1.0 s |
| `IA_SwitchWorld` | Q | Pressed |
| `IA_Convert` | T | Hold 2.0 s |
| `IA_Pause` | Esc | Pressed |

Touch controls and the template's `IMC_Default`/`IMC_MouseLook` are removed from the cat.

## 3. Ability system (`BPC_CatAbilities`)

One component owns every action so cooldowns and rules live in one place.

- Data: `DT_CatAbilities` rows keyed by `E_CatAction` with `Cooldown`, `Range`, `HoldTime`, `AllowedWorlds`, `Montage`, `Sound`, `Icon`.
- `TryActivate(Action)`:
  1. Fail if on cooldown, if the current world is not in `AllowedWorlds`, or if another action is playing (except Meow).
  2. For hold actions, start a hold timer; releasing early cancels with no cooldown.
  3. Play montage, run the effect, start cooldown, broadcast `OnCooldownChanged` every 0.1 s until 0.
- Cooldowns keep running across world switches.
- `IsBusy` blocks movement input only during Pounce and Convert.

## 4. Actions

| Action | Range / area | Effect | Montage | Noise (loudness) |
|---|---|---|---|---|
| **Push** | Sphere trace 60 cm in front | Calls `OnPushed` with impulse 350 (×mass) forward+up 30°; physics props fall | `AM_Cat_PawSwipe` | 0.6 when the object hits the floor (`ObjectFall`) |
| **Scratch** | Sphere trace 50 cm | Calls `OnScratched`; scratchable props swap to damaged mesh/material | `AM_Cat_Scratch` | 0.3 (`Scratch`) |
| **Pounce** | Launch 300 cm forward, 150 up | Kid hit → `Startled` for 2 s (convertible window). Prop hit → `OnPushed` impulse ×2.5 | `AM_Cat_Pounce` | 0.5 |
| **Meow** | Noise radius 800 cm | `ReportNoiseEvent` tag `Meow`; kids in Routine walk to the noise location (lure) | `AM_Cat_Meow` | 1.0 (`Meow`) |
| **Corrupt** | Trace 150 cm, hold 1 s | Calls `OnCorrupted`: target gets `Glitched` tag, glitch material, and (if flagged) loses collision / breaks / swaps mesh | `AM_Cat_PawSwipe` + `NS_Corrupt` | 0.4 |
| **Switch world** | Global | `BP_WorldManager.RequestSwitch()` | — | 0 |
| **Glitch Teleport** | 600 cm forward | Cut only. Sweep capsule ignoring actors tagged `Glitched`; teleport to last free spot; `NS_Teleport` at start and end | — | 0.2 |
| **Phase (passive)** | — | Cut only. Capsule ignores collision of `Glitched` actors (custom object channel `Glitched`) | — | — |
| **Convert** | Kid within 150 cm, hold 2 s | Allowed only if the kid does **not** see the cat, or is `Startled`. If the kid gains sight during the hold → cancel, kid goes **Alert**. Success → `Kid.Convert()` | `AM_Cat_ConvertCast` | 0.3 |

Cooldowns: see [GDD §4](../01_Design/Game_Design_Document.md#4-the-cat). Exact values are data in `DT_CatAbilities` and may be tuned.

## 5. States and rules

| State | Rule |
|---|---|
| Crouched | Kids' sight range ×0.5 against the cat; cannot sprint; can pass 25 cm gaps |
| Sprinting | Real world only; footstep noise 0.3 every 0.4 s |
| In air | Push/Scratch/Corrupt/Convert disabled; Pounce disabled |
| Caught | Input disabled 1 s, `AM_Cat_Caught`, fade out, teleport to the room's `Respawn.<Room>` actor, fade in. Cooldowns are not reset. |
| Cut world | Mesh material = `MI_Cat_Cut`; play `AM_Cat_GlitchTwitch` every random 6–10 s (only when idle or walking) |

Room tracking: each `LI_<Room>` contains a trigger volume `BP_RoomVolume` (Room name). The cat stores `CurrentRoom` on overlap for respawn.

## 6. Animation (`ABP_Cat`)

- Locomotion state machine: `Idle` ↔ `Walk/Run` (blend space `BS_Cat_Locomotion` by speed 0–550) ↔ `Jump_Start` → `Jump_Loop` → `Land`; crouch layer `Crouch_Idle`/`Crouch_Walk`.
- Idle variation: after 8 s idle, play `Idle_Sit` or `Idle_Lick` (random).
- Action montages in slot `DefaultSlot` (full body). Notifies: `AN_ActionHit` (moment the effect is applied), `AN_Footstep`.

## 7. Materials

| Material | Use |
|---|---|
| `MI_Cat_Real` | Black with white stripes |
| `MI_Cat_Cut` | Child of `M_GlitchCat_Skinned`: the current cyan/magenta glitch **without** the leg/tail WPO (the skeleton animates them), keeps the slice jitter + scanlines |

Switching material is driven by `OnWorldChanged`.

## 8. Acceptance
See FR-CAT-01…FR-CAT-16 in [`Functional_Requirements.md`](../03_Requirements/Functional_Requirements.md).
