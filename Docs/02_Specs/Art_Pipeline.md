# Spec — Art Pipeline (models, rigs, animation)

**Owners:** Erick (cat), Brianna (kids, VFX), Javier (environment props), Andrew (Cut-world & mission props) · **Requirements:** NFR-ART-*

## 1. Formats and budgets
| Asset | Triangles | Textures | Format |
|---|---|---|---|
| Cat | 5,000–8,000 | 1024 px | FBX (mesh + skeleton), one FBX per animation |
| Kid | 4,000–6,000 | 1024 px | FBX |
| Prop | 300–2,000 | 512 px | FBX (GLB only if FBX fails) |

Tools: **Tripo AI** first, Meshy / Hyper3D as fallback.

## 2. Character workflow
1. Generate the model (text or image → 3D) in a neutral pose: quadruped standing for the cat, A-pose for kids.
2. Reduce to the budget (low-poly / remesh); textures to 1024 px.
3. Auto-rig: **Quadruped** for the cat, **Humanoid/Biped** for kids.
4. Animate on that same skeleton. All animations **in place** (no root motion), 30 fps.
5. Export one FBX with mesh + skeleton, then one FBX per animation. Names: `A_Cat_Walk`, `A_Kid_PointShout`…
6. Import into Unreal: mesh first (creates the skeleton), then each animation targeting that skeleton. Scale 1.0. Check the cat is ~45 cm long without tail.
7. **The cat skeleton is frozen once approved.** Do not re-rig after animations exist.

## 3. Cat
Approved look: stocky solid-black cat, no white markings. Reference: `SourceArt/Characters/Cat/Ref_Cat_Approved.png`.

Prompt: `low poly stylized chubby solid black cat, stocky round body, short thick legs, no white markings, standing on four legs, neutral pose, tail straight back, mouth closed, game asset, clean topology`

The Tripo auto-rig mis-placed the skeleton on this body. `SK_Cat.fbx` was cleaned and rigged in Blender (quadruped: `root`, `pelvis`, `spine_01`, `spine_02`, `chest`, `neck`, `head`, `jaw`, `tail_01`–`tail_04`, and `front_` / `hind_` `thigh` / `shin` / `paw` `_l` / `_r`). Do not re-rig it. The 16 clips in `SourceArt/Characters/Cat/Animations/` are in-place, 30 fps, on that skeleton. Triangle count is about 6,200.

| Animation | Loop | Length | Use |
|---|---|---|---|
| `A_Cat_Idle` | Yes | 3–4 s | Standing |
| `A_Cat_IdleSit` / `A_Cat_IdleLick` | No | 4–6 s | Idle variation after 8 s |
| `A_Cat_Walk` | Yes | 1 s | Walk |
| `A_Cat_Run` | Yes | 0.6 s | Sprint (trot) |
| `A_Cat_JumpStart` | No | 0.3 s | Take-off |
| `A_Cat_JumpLoop` | Yes | 0.5 s | Falling |
| `A_Cat_Land` | No | 0.3 s | Landing |
| `A_Cat_CrouchIdle` | Yes | 2 s | Crouched |
| `A_Cat_CrouchWalk` | Yes | 1.2 s | Stealth |
| `A_Cat_PawSwipe` | No | 0.5 s | Push, Corrupt |
| `A_Cat_Scratch` | No | 0.8 s | Scratch |
| `A_Cat_Pounce` | No | 0.8 s | Pounce, Teleport |
| `A_Cat_Meow` | No | 1 s | Meow (head up, mouth open) |
| `A_Cat_GlitchTwitch` | No | 0.8 s | Cut world twitch ("convulsing, twitching, jerky") |
| `A_Cat_Caught` | No | 1 s | Being caught |
| `A_Cat_ConvertCast` | No | 1.5 s | Convert (arched back, bristled tail) |

## 4. Props
| Room | Props |
|---|---|
| Classroom | student desk, chair, teacher desk, blackboard, globe, mug, vase |
| Cafeteria | long table, bench, tray, plate, birthday cake |
| Gym | mat, ball, bleachers, locker, bench |
| Library | bookshelf, 3 book variants, desk lamp |
| Lab | retro computer, flasks, test tubes, formula blackboard |
| Cut world | film camera, clapperboard, spotlight, server rack, floating "file", caution tape, "Content removed" sign |

Walls, floors and doors are **not** AI-generated: they come from the modular kit (see [`Level_and_Environment.md`](Level_and_Environment.md#2-building-rules)).

## 5. Kids
Prompt: `low poly stylized school student, kid, school uniform, A-pose, game asset, simple shapes` (variants: backpack, glasses, girl with braids).
Shortcut: IK Retarget Manny's Idle/Walk/Run/Jump. Generate only: `Sit_Idle`, `Reading`, `Eating`, `Play_Ball`, `Talk`, `Exercise`, `Startled`, `Point_Shout`, `Pick_Up`, `Grab_Cat`.
Kid → cat conversion uses VFX + model swap, no special animation.

## 6. VFX (Niagara, Brianna)
| System | Trigger |
|---|---|
| `NS_WorldSwitch` | World switch (screen-space + around the cat) |
| `NS_Teleport` | Start and end of teleport |
| `NS_Corrupt` | Corrupt hit on a prop |
| `NS_KidConvert` | Glitch + smoke on conversion |
| `NS_Scratch` | Scratch marks / paper bits |
| `NS_MeowRing` | Expanding ring showing meow radius |

Budget: ≤ 2,000 particles on screen, GPU sim off unless needed.
