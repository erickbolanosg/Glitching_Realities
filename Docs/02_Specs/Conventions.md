# Conventions and Shared Contracts

Everything that **connects modules** is defined here. If you need to change a name, tag, event or folder in this file, announce it in the team chat first and update this file in the same commit.

## 1. Language
All content is in **English**: docs, issues, PRs, commit messages, asset names, in-game text, code comments.

## 2. Folder layout (`/Game`)

| Folder | Content | Owner |
|---|---|---|
| `/Game/Characters/Cat` | Cat mesh, skeleton, anims, ABP, materials, `BP_Cat` | Erick |
| `/Game/Characters/Cat/Placeholder` | Current block cat (`SM_GlitchCat`, `M_GlitchCat`) | Erick |
| `/Game/Characters/Kids` | Kid meshes, retargeted anims, ABP, materials, `BP_Kid` | Brianna (visuals), Andrew (logic) |
| `/Game/AI` | StateTrees, perception configs, AI controllers, EQS | Andrew |
| `/Game/Gameplay/Abilities` | Cat ability component and ability data | Erick |
| `/Game/Gameplay/World` | `BP_WorldManager`, `MPC_World`, world post-process | Erick |
| `/Game/Gameplay/Missions` | `BP_MissionBase`, `BP_Mission_<Room>` | Andrew |
| `/Game/Gameplay/Interaction` | `BPI_Interactable`, `BP_InteractableBase` and children | Javier (props) / Erick (interface) |
| `/Game/Props/<Room>` | Room props (meshes, materials, textures) | Javier |
| `/Game/Props/Cut` | Cut-world-only props | Andrew (models) / Javier (placement) |
| `/Game/Levels` | `Lvl_School`, `Lvl_MainMenu` | Javier |
| `/Game/Levels/Rooms` | `LI_<Room>` level instances | Javier |
| `/Game/VFX` | Niagara systems and VFX materials | Brianna |
| `/Game/UI` | Widgets, icons, fonts | Leonardo |
| `/Game/Audio` | Sound waves, cues/MetaSounds, sound classes, mixes | Leonardo |
| `/Game/Input` | Input actions and mapping contexts | Erick |

## 3. Asset prefixes

| Prefix | Type | Prefix | Type |
|---|---|---|---|
| `SM_` | Static mesh | `BP_` | Blueprint |
| `SK_` | Skeletal mesh | `BPI_` | Blueprint interface |
| `SKEL_` | Skeleton | `ABP_` | Animation blueprint |
| `A_` | Animation sequence | `AM_` | Animation montage |
| `BS_` | Blend space | `ST_` | StateTree |
| `M_` | Material | `MI_` | Material instance |
| `MPC_` | Material parameter collection | `T_` | Texture |
| `NS_` | Niagara system | `WBP_` | Widget blueprint |
| `SFX_` / `MUS_` | Sound effect / music | `IA_` / `IMC_` | Input action / mapping context |
| `LI_` | Level instance | `Lvl_` | Level (map) |
| `E_` / `S_` | Enum / Struct | `DT_` | Data table |

Names use `PascalCase` after the prefix: `A_Cat_Walk`, `SM_Classroom_Desk`, `WBP_HUD`.

## 4. Scale (frozen after Stage 2)

| Thing | Size |
|---|---|
| Cat | ~45 cm long (without tail), ~33 cm tall, stocky. About 69 cm including the tail. |
| Kid | ~130–145 cm tall |
| Table / desk top | 75 cm (one jump) |
| Gap under furniture | 25 cm (crouch only) |
| Bookshelf | up to 200 cm (two jumps) |
| Wall module | 400 × 300 cm |
| Door | 120 × 220 cm |

## 5. Actor tags

| Tag | Meaning | Who reads it |
|---|---|---|
| `World.Real` | Exists only in the Real world | `BP_WorldManager` |
| `World.Cut` | Exists only in the Cut world | `BP_WorldManager` |
| *(no World tag)* | Exists in both worlds | — |
| `Glitched` | Cat can phase through it in the Cut world | Cat, `BP_WorldManager` |
| `Mission.<Room>` | Counts for that room's mission (e.g. `Mission.Classroom`) | `BP_Mission_<Room>` |
| `Respawn.<Room>` | On the room's respawn point actor | Game mode |

## 6. Interfaces and events

### `BPI_Interactable` (implemented by props)
| Function | Signature | Notes |
|---|---|---|
| `GetInteractionPrompt` | `() -> Text` | e.g. "Knock over" — shown by the HUD |
| `CanInteract` | `(Instigator: Pawn, Action: E_CatAction) -> bool` | |
| `OnPushed` | `(Instigator: Pawn, Impulse: Vector)` | E / Pounce |
| `OnScratched` | `(Instigator: Pawn)` | Left mouse |
| `OnCorrupted` | `(Instigator: Pawn)` | F; sets `Glitched` tag, may disable collision |

### `E_CatAction`
`Push, Scratch, Pounce, Meow, Corrupt, SwitchWorld, Teleport, Convert`

### Event dispatchers
| Dispatcher | Owner | Payload | Listeners |
|---|---|---|---|
| `OnCooldownChanged` | `BPC_CatAbilities` | `Action: E_CatAction, Remaining: float, Duration: float` | HUD |
| `OnWorldChanged` | `BP_WorldManager` | `NewWorld: E_World` | HUD, audio, kids, materials |
| `OnMissionCompleted` | `BP_MissionBase` | `MissionId: Name` | HUD, `BP_GameState` |
| `OnKidConverted` | `BP_Kid` | `Kid: BP_Kid` | HUD counter, `BP_GameState` |
| `OnCatCaught` | `BP_Kid` | `Room: Name` | Game mode (respawn), audio |
| `OnNoiseMade` | uses `ReportNoiseEvent` | `Loudness, Tag` (`Meow`, `ObjectFall`, `Scratch`) | AI hearing |

### `E_World`
`Real, Cut`

## 7. Git
See [`../04_Production/Git_Workflow.md`](../04_Production/Git_Workflow.md).
