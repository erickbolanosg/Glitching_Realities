# Non-Functional Requirements

## Performance (NFR-PERF)
| ID | Requirement | How to verify |
|---|---|---|
| NFR-PERF-01 | ≥ 60 FPS at 1080p on **Medium** and ≥ 30 FPS on **Low** on a mid-range PC (GTX 1060 / RX 580 class, 16 GB RAM). | `stat fps` during the full demo route |
| NFR-PERF-02 | No Lumen, ray tracing, Nanite or Virtual Shadow Maps (lightweight profile in `Config/DefaultEngine.ini`). | Project Settings review |
| NFR-PERF-03 | ≤ 2 shadow-casting lights per room besides the sun. | Level review |
| NFR-PERF-04 | World switch causes no hitch > 50 ms. | `stat unit` while switching |
| NFR-PERF-05 | Level load (menu → game) ≤ 15 s from SSD. | Stopwatch |
| NFR-PERF-06 | Packaged build ≤ 2 GB. | File size |

## Art budgets (NFR-ART)
| ID | Requirement |
|---|---|
| NFR-ART-01 | Cat 5–8k tris, kids 4–6k tris, props 300–2,000 tris. |
| NFR-ART-02 | Textures: 1024 px characters, 512 px props. |
| NFR-ART-03 | Animations in place, 30 fps, on the approved skeleton. |
| NFR-ART-04 | Scale matches [Conventions §4](../02_Specs/Conventions.md#4-scale-frozen-after-stage-2). |

## Usability (NFR-USE)
| ID | Requirement |
|---|---|
| NFR-USE-01 | A new player sees every mechanic within 5 minutes. |
| NFR-USE-02 | Every key is shown on the HUD next to its ability icon. |
| NFR-USE-03 | Text ≥ 18 px at 1080p; Real/Cut states distinguishable without relying only on color (labels). |
| NFR-USE-04 | Mouse sensitivity adjustable; no motion-heavy effect is mandatory (glitch intensity ≤ 0.6 by default). |

## Reliability (NFR-REL)
| ID | Requirement |
|---|---|
| NFR-REL-01 | No crash or soft-lock during a 20-minute session. |
| NFR-REL-02 | The cat can never get permanently stuck (respawn after caught; world switch unstick; debug respawn key in Development). |
| NFR-REL-03 | Missing optional assets fall back to placeholders, never to errors. |

## Maintainability (NFR-MNT)
| ID | Requirement |
|---|---|
| NFR-MNT-01 | Assets follow folder and prefix conventions. |
| NFR-MNT-02 | Shared contracts (tags, interfaces, events) are only changed through [Conventions.md](../02_Specs/Conventions.md). |
| NFR-MNT-03 | Gameplay values (cooldowns, ranges, speeds) live in data tables or exposed variables, not hard-coded in graphs. |
| NFR-MNT-04 | Each room is an independent Level Instance; each mission only reads its own room. |

## Compliance and delivery (NFR-DEL)
| ID | Requirement |
|---|---|
| NFR-DEL-01 | Content suitable for a 13+ rating. |
| NFR-DEL-02 | All in-game text and documentation in English. |
| NFR-DEL-03 | Only assets we created or with licenses allowing jam use; licenses listed in credits. |
| NFR-DEL-04 | Windows 64-bit Shipping build, zipped, uploaded to the jam page before Sunday 2026-11-15 12:00 (UTC-6). |

## Collaboration (NFR-COL)
| ID | Requirement |
|---|---|
| NFR-COL-01 | Binary assets go through Git LFS; `.uasset`/`.umap` are lockable — lock before editing shared assets. |
| NFR-COL-02 | Work on feature branches off `develop`; `main` only receives releases. |
| NFR-COL-03 | One person per Level Instance at a time. |
