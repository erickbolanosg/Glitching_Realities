# Team and Ownership

Each person owns a module for the whole project. Owners decide inside their module; anything that touches [shared contracts](../02_Specs/Conventions.md) is agreed in the team chat first.

| Member | GitHub | Module | Owns |
|---|---|---|---|
| Erick Bolaños | [@erickbolanosg](https://github.com/erickbolanosg) | Cat & world (lead) | Cat model, `BP_Cat`, abilities, input, world switch, integration, releases |
| Andrew González | [@ander1231245125232](https://github.com/ander1231245125232) | Kids AI & missions | `ST_Kid`, AI perception, missions, game state, Cut/mission props, final bug triage |
| Brianna Matus | [@Patchesse](https://github.com/Patchesse) | Characters & VFX | Kid models/animation, retargeting, montages, Niagara VFX, media |
| Javier Salazar | [@Javtamata145](https://github.com/Javtamata145) | Level & environment | Modular kit, room props, `Lvl_School`, level instances, interactable props, lighting, performance |
| Leonardo Lomas | [@Leonardo-Lomas](https://github.com/Leonardo-Lomas) | UI, audio & delivery | Icons, widgets, HUD, options, audio, packaging, trailer, jam page |

## Who to ask
| Question about… | Ask |
|---|---|
| Tags, interfaces, events, input | Erick |
| Kid behavior, mission rules | Andrew |
| Rigs, animation, VFX | Brianna |
| Room layout, scale, lighting, props | Javier |
| HUD data, sounds, builds | Leonardo |

## Module boundaries
- `BP_Kid`: Brianna owns visuals (mesh, ABP, materials); Andrew owns logic (StateTree, perception, conversion). Agree before editing the same Blueprint — lock it with `git lfs lock`.
- `BP_InteractableBase`: Javier owns it; Erick owns the `BPI_Interactable` interface it implements.
- Cut-world props: Andrew models them (S1) and places mission ones (S2); Javier places the rest and gives them behavior (S3).
