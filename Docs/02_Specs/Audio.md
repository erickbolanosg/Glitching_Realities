# Spec — Audio

**Owner:** Leonardo · **Requirements:** FR-AUD-*

## 1. Structure
- Sound classes: `SC_Master` → `SC_Music`, `SC_SFX`, `SC_UI`. Sound mix `SMix_Default`. Volumes driven by Options.
- Attenuation presets: `ATT_Small` (10 m), `ATT_Medium` (20 m).
- All sources must be free for commercial/jam use; record license in `Docs/05_Assets/Licenses.md` (create on first import).

## 2. Sound list
| Asset | Trigger | Owner of trigger |
|---|---|---|
| `SFX_Cat_Meow` (3 variants) | Meow action | Cat |
| `SFX_Cat_Scratch` | Scratch | Cat |
| `SFX_Cat_Swipe` | Push / Corrupt montage notify | Cat |
| `SFX_Cat_Footstep` | `AN_Footstep` | Cat ABP |
| `SFX_Cat_Pounce` | Pounce | Cat |
| `SFX_Teleport` | Teleport | Cat |
| `SFX_Corrupt` | Corrupt hit | Cat |
| `SFX_WorldSwitch` | World switch | World manager |
| `SFX_ObjectFall_Light/Heavy` | Prop hits floor | `BP_InteractableBase` |
| `SFX_Kid_Curious`, `SFX_Kid_Shout`, `SFX_Kid_Alert`, `SFX_Kid_Startled` | AI states | Kid |
| `SFX_KidConvert` | Conversion | Kid |
| `SFX_MissionComplete` | Mission complete | HUD |
| `SFX_UI_Hover/Click` | Menus | UI |
| `MUS_Real` (loop) | Real world | World manager |
| `MUS_Cut` (loop) | Cut world | World manager |
| `MUS_Menu` (loop) | Main menu | UI |

## 3. World music
`MUS_Real` and `MUS_Cut` play in sync; `OnWorldChanged` crossfades them in 0.3 s (same tempo/key recommended so the switch feels like a "version" change).
