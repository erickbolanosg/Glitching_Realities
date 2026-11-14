# Git Workflow

## 1. First-time setup
```bash
git lfs install
git clone https://github.com/erickbolanosg/Glitching_Realities.git
cd Glitching_Realities
git checkout develop
```
Open `Glitching_Realities.uproject` with **Unreal Engine 5.8.4**.

> **History was rewritten on 2026-11-14** (commit messages translated to English). If you cloned before that, run once:
> ```bash
> git fetch origin
> git checkout develop
> git reset --hard origin/develop
> ```
> Save any local work on another branch first.

## 2. Branches
| Branch | Purpose | Rules |
|---|---|---|
| `main` | Released builds only | Protected. Only `develop → main` release PRs (Erick). |
| `develop` | Integration branch | Protected: PR + 1 approval. Default branch. |
| `feature/<issue-key>` | One issue | Created from `develop`, e.g. `feature/cat-abilities`. Name given at the bottom of each issue. |
| `fix/<short-name>` | Bug fix | From `develop`. |

## 3. Daily loop
1. `git checkout develop && git pull`
2. `git checkout -b feature/<issue-key>` (or continue yours; `git merge develop` to update it).
3. Lock shared binary assets before editing: `git lfs lock Content/Path/Asset.uasset`. Unlock after merging: `git lfs unlock …`.
4. Commit small and often.
5. Push and open a PR to `develop` using the template. Ask one teammate to review.

## 4. Commit messages (English)
```
<area>: <imperative summary, max 72 chars>

<optional body: what and why>

Refs #<issue>
```
Areas: `cat`, `world`, `kids`, `ai`, `missions`, `level`, `props`, `vfx`, `ui`, `audio`, `build`, `docs`.
Example: `cat: add pounce ability with 4 s cooldown`.

## 5. Pull requests
- Title: same format as commits.
- Body: the PR template (`.github/pull_request_template.md`); include `Closes #<issue>`.
- Reviewer checks: runs in editor, follows conventions, no unrelated assets changed.
- Merge method: **squash** for features, **merge commit** for `develop → main` releases.

## 6. Unreal + Git tips
- Close the editor before `git pull` if it touches assets you have open.
- Never commit `Binaries/`, `Intermediate/`, `Saved/`, `DerivedDataCache/` (already ignored).
- After moving/renaming assets: *Fix Up Redirectors* in the folder before committing.
- Levels use One File Per Actor: two people can edit different rooms of `Lvl_School` safely; the same Level Instance cannot.
- Source files (FBX, WAV, PNG originals) go in `SourceArt/` at the repo root; imported assets in `Content/`.
