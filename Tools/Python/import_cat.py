"""Imports the rigged cat (SourceArt/Characters/Cat/SK_Cat.fbx) into /Game/Characters/Cat.

Run headless (UE 5.8.4) with the editor closed:
  UnrealEditor-Cmd.exe Glitching_Realities.uproject -run=pythonscript -script=Tools/Python/import_cat.py

The FBX comes from Tools/Blender/rig_cat.py and holds the mesh, the skeleton and the walk cycle.
Result (no physics asset, nothing else):
  SK_Cat          skeletal mesh
  SKEL_Cat        skeleton
  T_Cat_BaseColor texture (SourceArt/Characters/Cat/Source/T_Cat_BaseColor.jpg)
  Animations/A_Cat_Walk
Next: Tools/Python/build_cat_materials.py (M_Cat_Toon, M_Cat_Hologram), then build_cat_character.py.
Importing over existing assets compounds the scale, so the folder must be empty: delete
Content/Characters/Cat with the editor closed before re-running.
"""
import os
import unreal

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
FBX = os.path.join(PROJECT, "SourceArt", "Characters", "Cat", "SK_Cat.fbx")
DEST = "/Game/Characters/Cat"
eal = unreal.EditorAssetLibrary
LOG_PATH = os.environ.get("CAT_LOG")
_log = open(LOG_PATH, "w", encoding="utf-8") if LOG_PATH else None


def log(*a):
    msg = " ".join(str(x) for x in a)
    unreal.log("IMPORT_CAT: " + msg)
    if _log:
        _log.write(msg + "\n")
        _log.flush()


if eal.list_assets(DEST, recursive=True, include_folder=False):
    raise RuntimeError(f"{DEST} is not empty. Delete it with the editor closed and re-run.")

p = unreal.InterchangeGenericAssetsPipeline()
p.set_editor_property("asset_type_sub_folders", False)
mesh_p = p.get_editor_property("mesh_pipeline")
mesh_p.set_editor_property("import_static_meshes", False)
mesh_p.set_editor_property("import_skeletal_meshes", True)
mesh_p.set_editor_property("create_physics_asset", False)
mesh_p.set_editor_property("import_morph_targets", False)
p.get_editor_property("animation_pipeline").set_editor_property("import_animations", True)
# Interchange turns the FBX material into an untextured "legacy Phong" instance, so materials are
# skipped here and M_Cat is built below from Tripo's original texture.
p.get_editor_property("material_pipeline").set_editor_property("import_materials", False)

params = unreal.ImportAssetParameters()
params.set_editor_property("is_automated", True)
params.set_editor_property("replace_existing", True)
params.set_editor_property("override_pipelines", [unreal.SoftObjectPath(p.get_path_name())])
manager = unreal.InterchangeManager.get_interchange_manager_scripted()
manager.import_asset(DEST, unreal.InterchangeManager.create_source_data(FBX), params)
eal.save_directory(DEST)

# Give every imported asset a clear name.
renames = {}
for path in eal.list_assets(DEST, recursive=True, include_folder=False):
    a = unreal.load_asset(path)
    if isinstance(a, unreal.SkeletalMesh):
        renames[path] = f"{DEST}/SK_Cat"
    elif isinstance(a, unreal.Skeleton):
        renames[path] = f"{DEST}/SKEL_Cat"
    elif isinstance(a, unreal.AnimSequence):
        renames[path] = f"{DEST}/Animations/A_Cat_Walk"
    else:  # embedded textures/materials are not wanted (see above)
        log("removing extra asset", path, type(a).__name__)
        eal.delete_asset(path)
# Skeleton first, then save every package that now points at it, then the rest.
for src, dst in sorted(renames.items(), key=lambda kv: not kv[1].endswith("SKEL_Cat")):
    if src.split(".")[0] != dst and not eal.rename_asset(src, dst):
        raise RuntimeError(f"rename failed {src} -> {dst}")
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
eal.save_directory(DEST, only_if_is_dirty=False)

# --- Tripo's original texture (used by both cat materials)
tools = unreal.AssetToolsHelpers.get_asset_tools()
task = unreal.AssetImportTask()
task.set_editor_property("filename", os.path.join(PROJECT, "SourceArt", "Characters", "Cat", "Source", "T_Cat_BaseColor.jpg"))
task.set_editor_property("destination_path", DEST)
task.set_editor_property("destination_name", "T_Cat_BaseColor")
task.set_editor_property("automated", True)
task.set_editor_property("save", True)
tools.import_asset_tasks([task])
texture = unreal.load_asset(f"{DEST}/T_Cat_BaseColor")
if not texture:
    raise RuntimeError("T_Cat_BaseColor was not imported")

skeleton = unreal.load_asset(f"{DEST}/SKEL_Cat")
mesh = unreal.load_asset(f"{DEST}/SK_Cat")
walk = unreal.load_asset(f"{DEST}/Animations/A_Cat_Walk")
# Verify the references that were saved. Materials come next, from build_cat_materials.py.
checks = {
    "SK_Cat -> SKEL_Cat": mesh.get_editor_property("skeleton") == skeleton,
    "A_Cat_Walk -> SKEL_Cat": walk.get_editor_property("skeleton") == skeleton,
}
if not all(checks.values()):
    raise RuntimeError(f"broken references: {checks}")
log("references verified:", ", ".join(checks))
log("assets:", sorted(x.split(".")[0] for x in eal.list_assets(DEST, recursive=True, include_folder=False)))
log("bounds extent (cm):", mesh.get_bounds().box_extent, "origin:", mesh.get_bounds().origin)
log("walk length (s):", round(walk.get_play_length(), 3), "skeleton:", walk.get_editor_property("skeleton").get_name())
log("DONE")
