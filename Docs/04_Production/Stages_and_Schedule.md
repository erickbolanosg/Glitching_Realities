# Stages and Schedule

Deadline: **Sunday 2026-11-15, 12:00 (UTC-6)**. Work is split into five stages by discipline. Each stage is a GitHub **milestone** and every member has at least one issue per stage, so everyone always knows what to do next.

| Stage | Window (UTC-6) | Goal | Gate (must be true to close the stage) |
|---|---|---|---|
| **S1 · Modeling** | Sat 11:00 → Sat 17:00 | Produce every asset *outside* the engine: models, rigs, animations, props, UI art, audio | Cat approved and rigged; kids, props, icons and sounds exported |
| **S2 · Building** | Sat 17:00 → Sat 23:00 | Bring assets *into* Unreal and into the world | `BP_Cat` animated, kids animated, school blockout with all demo rooms, widgets laid out, kids/missions placed |
| **S3 · Programming** | Sat 23:00 → Sun 05:00 | Make everything *work* | All `Must` functional requirements implemented on feature branches |
| **S4 · Integration & QA** | Sun 05:00 → Sun 09:00 | Merge, playtest, fix, optimize, first build | Demo route playable on `develop`; packaged build launches |
| **S5 · Polish & Release** | Sun 09:00 → Sun 12:00 | Release and submit | `v1.0.0` on `main`, submitted by 11:30 |

## Rules
1. **Nobody waits.** If an input from another stage is late, use the placeholder (block cat, Manny, gray cubes, fake HUD values) and keep going. Programming work may *start* earlier with placeholders; the stage window is when it must be *finished*.
2. **Stage close = group sync.** At the end of each window everyone pushes, opens/merges PRs into `develop`, and the team plays 20 minutes together.
3. **Cut rule.** If a stage gate is more than 2 h late, apply the short plan: 3 Real rooms (Classroom, Cafeteria, Gym) + 2 Cut rooms (Auditorium, Server Room).
4. **Frozen after S2:** cat skeleton, global scale, world system contracts.
5. **Feature freeze:** Sun 09:00. Only bug fixes after that.

## Issues by stage and owner

| Stage | Erick | Andrew | Brianna | Javier | Leonardo |
|---|---|---|---|---|---|
| **S1 · Modeling** | #1 Cat model, rig, animations | #4 Cut-world & mission props | #2 Kid models & animations | #3 Modular kit & room props | #5 UI art & audio assets |
| **S2 · Building** | #6 Cat import, `ABP_Cat`, `BP_Cat` | #9 Place kids, spots, paths, missions | #7 Kids import, retarget, VFX | #8 `Lvl_School` blockout & rooms | #10 Widgets layout & audio import |
| **S3 · Programming** | #11 Cat abilities · #12 World switch | #13 Kid AI · #14 Missions | #16 Montages, notifies, VFX hookup | #15 Interactable props & Cut content | #17 UI & audio logic |
| **S4 · Integration & QA** | #18 Integration & demo route | #19 Balance & bug fixing | #20 Characters/VFX polish | #21 Lighting & performance | #22 First packaged build |
| **S5 · Polish & Release** | #23 Release candidate `v1.0.0` | #24 Final bug triage | #25 Screenshots & key art | #26 Scalability check | #27 Trailer, page, submission |

Milestones: <https://github.com/erickbolanosg/Glitching_Realities/milestones>

## Critical path
`#1 Cat model → #6 Cat import → #11 Abilities / #12 World switch → #18 Integration → #23 Release → #27 Submission`

Everything else can slip to placeholders without blocking the demo.

## Definition of Done (every issue)
- All steps and acceptance criteria ticked.
- Assets follow [Conventions](../02_Specs/Conventions.md) (folders, prefixes, tags).
- Work merged into `develop` through a PR that says `Closes #<n>`.
- Tested in `Lvl_School` (or the test map, before S2 is done) without new warnings in the Message Log.
