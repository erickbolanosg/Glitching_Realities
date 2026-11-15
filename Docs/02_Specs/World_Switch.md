# Spec — World Switch (Real ↔ Cut)

**Owner:** Erick · **Assets:** `BP_WorldManager`, `MPC_World`, `PP_World` · **Requirements:** FR-WLD-*

## 1. Overview
One `BP_WorldManager` per level holds the current world (`E_World`) and is the **only** system allowed to show/hide world content. Nobody builds their own toggle.

## 2. Content rules
| Actor tag | Real world | Cut world |
|---|---|---|
| none | visible + collision | visible + collision |
| `World.Real` | visible + collision | hidden, no collision, tick off |
| `World.Cut` | hidden, no collision, tick off | visible; collision per actor (glitched props usually none) |

Kids tagged `World.Cut` are deactivated (AI logic paused, hidden) in the Real world.

## 3. Switch sequence (`RequestSwitch`)
1. Reject if cooldown (3 s) is running.
2. Timeline 0.3 s: drive `MPC_World.SwitchPulse` 0 → 1 → 0 (screen glitch flash) and `MPC_World.WorldBlend` 0 ↔ 1.
3. At the midpoint (0.15 s): apply visibility/collision to all cached tagged actors, swap cat material, broadcast `OnWorldChanged(NewWorld)`.
4. Play `SFX_WorldSwitch`; start cooldown via `BPC_CatAbilities`.
5. If the cat ends up overlapping a now-solid actor, push it to the nearest free spot (capsule sweep up/out).

Tagged actors are cached once at `BeginPlay` (`GetAllActorsWithTag`) and refreshed when Level Instances finish loading.

## 4. `MPC_World` parameters
| Parameter | Range | Used by |
|---|---|---|
| `WorldBlend` | 0 Real – 1 Cut | Tint + glitch on every glitchable material |
| `SwitchPulse` | 0–1 | Transition flash/scanline burst |
| `GlitchIntensity` | 0–1 (default 0.6) | Global glitch amount for cut props |

Material function `MF_WorldGlitch` (inputs: base color, emissive) applies tint and glitch from `MPC_World`; every Cut-world material uses it.

## 5. Post process
Unbound post-process volume `PP_World` with two weighted blendables driven by `WorldBlend`:
- Real: saturation 0.85, no extra effects.
- Cut: purple/blue tint (scene color tint ~ #B9A8FF), chromatic aberration 0.4, scanline post material `M_PP_Scanlines` (weight 0.3).
No Lumen, bloom kept low (see NFRs).

## 6. Cut-world-only cat features
- Teleport and Phase enabled only while `CurrentWorld == Cut`.
- Sprint disabled in Cut.
- Twitch animation timer runs only in Cut.

## 7. Debug
Console command / key `F9` (Development builds only): toggle world without cooldown.
