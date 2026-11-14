# Spec — UI, Menus and HUD

**Owner:** Leonardo · **Assets:** `WBP_MainMenu`, `WBP_Options`, `WBP_Credits`, `WBP_HUD`, `WBP_Pause`, `BP_UIManager` · **Requirements:** FR-UI-*

## 1. Flow
```
Lvl_MainMenu ──Start──▶ Lvl_School (HUD) ──Esc──▶ Pause ──Quit to menu──▶ Lvl_MainMenu
      │                                         └──Options──▶ Options (back returns to Pause)
      ├─Options─▶ Options
      ├─Credits─▶ Credits
      └─Quit───▶ exit game
```
Input mode: UI only in menus (cursor visible), Game only in play, Game+UI in pause. Pause sets game paused.

## 2. Main menu (`WBP_MainMenu`)
Title "GLITCHING REALITIES" with glitch text effect, buttons Start / Options / Credits / Quit. Background: slow camera dolly over `Lvl_School` with `WorldBlend` oscillating (temporary).

## 3. Options (`WBP_Options`)
| Setting | Control | Stored in |
|---|---|---|
| Graphics quality | Low / Medium / High (maps to Scalability 0/1/2) | `GameUserSettings` |
| Fullscreen | Toggle (Fullscreen ↔ Windowed) | `GameUserSettings` |
| Master volume | Slider 0–100 | `SG_Settings` (SaveGame) → `SC_Master` |
| Music / SFX volume | Sliders | `SG_Settings` → `SC_Music`, `SC_SFX` |
| Mouse sensitivity | Slider 0.2–3.0 (default 1.0) | `SG_Settings` → read by `BP_Cat` |
Apply on change; persist across launches.

## 4. HUD (`WBP_HUD`)
| Element | Data source |
|---|---|
| Ability bar: 9 icons (Push, Scratch, Pounce, Meow, Corrupt, Switch, Teleport, Convert, + Phase passive) with radial cooldown and key label | `BPC_CatAbilities.OnCooldownChanged` |
| Cut-only abilities dimmed in Real world | `BP_WorldManager.OnWorldChanged` |
| World indicator ("REAL" / "DIRECTOR'S CUT") | `OnWorldChanged` |
| Counter "Kids converted X/N" | `BP_GameState` (`OnKidConverted`) |
| Mission toast + completion banner | `OnObjectiveProgress`, `OnMissionCompleted` |
| Context prompt ("E — Knock over") | Cat's focused interactable `GetInteractionPrompt` |
| Hold progress ring (Corrupt, Convert) | `BPC_CatAbilities` hold timer |

Until real data exists, HUD uses fake values (placeholder rule).

## 5. Pause (`WBP_Pause`)
Resume, Options, Quit to menu.

## 6. Style
Font: one free pixel/mono font (OFL license) + one readable sans. Colors: Real = white/gray, Cut = cyan `#00FFE5` / magenta `#FF00CC`. Minimum text size 18 px at 1080p.

## 7. Credits
Team names and roles (see [`Team_and_Ownership.md`](../04_Production/Team_and_Ownership.md)) + third-party asset licenses.
