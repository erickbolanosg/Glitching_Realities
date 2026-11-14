# Glitching Realities

A 3D sandbox where you play an evil, glitched cat in a school, switching between the "official" game and its **Director's Cut**, where all the removed content comes back.

Unreal Engine **5.8.4** · Windows · keyboard + mouse · Game jam build (deadline Sunday 2026-11-15, 12:00 UTC-6).

## Start here
1. **Docs:** [`Docs/README.md`](Docs/README.md) — design, specs, requirements, schedule.
2. **Your tasks:** [issues assigned to you](https://github.com/erickbolanosg/Glitching_Realities/issues/assigned/@me), grouped by [milestone](https://github.com/erickbolanosg/Glitching_Realities/milestones) (S1 Modeling → S5 Release).
3. **Git:** [`Docs/04_Production/Git_Workflow.md`](Docs/04_Production/Git_Workflow.md). Work on `develop` and feature branches, never directly on `main`.

## Engine version: Unreal Engine 5.8.4
The whole team must use **UE 5.8.4** (Epic Games Launcher build). Assets saved with a newer version do not open in an older one.

1. In the Epic Games Launcher → Unreal Engine → Library, check that 5.8 says **5.8.4**. Update it if not.
2. Open `Glitching_Realities.uproject`. If Windows asks which version to use, pick **5.8**.
3. Do not use "Switch Unreal Engine version" or source-built engines: they replace `EngineAssociation` in the `.uproject` with a local GUID and break the project for everyone. It must always be `"EngineAssociation": "5.8"`.

Check with Help → About Unreal Editor: it must say 5.8.4.

## Git LFS
Binary assets use Git LFS: run `git lfs install` before cloning. `.uasset`/`.umap` are lockable (`git lfs lock <file>`).

## Rendering profile
The project uses a lightweight profile (no Lumen, ray tracing, Nanite or Virtual Shadow Maps) so it runs on integrated graphics. Do not re-enable them without telling the team. Details: [Level and environment spec](Docs/02_Specs/Level_and_Environment.md#lighting-and-performance).

## Repository layout
| Path | Content |
|---|---|
| `Content/` | Unreal assets |
| `Config/` | Project settings |
| `Docs/` | Design, specs, requirements, production |
| `SourceArt/` | Source files (FBX, WAV, PNG) before import |
| `Tools/Python/` | Editor automation scripts (placeholder cat builder, play test) |
| `.github/` | Issue and PR templates |
