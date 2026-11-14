"""Builds the playable cat: ABP_Cat, BP_Cat (toon look + hologram glitch look) and the Q switch.

Run headless (UE 5.8.4), editor closed, after import_cat.py and build_cat_materials.py:
  UnrealEditor-Cmd.exe Glitching_Realities.uproject -run=pythonscript -culture=en
      -script=Tools/Python/build_cat_character.py
`-culture=en` matters: graph nodes are looked up by their English menu names.
If IA_SwitchWorld did not exist yet, the first run creates it and asks for a second run (new
input actions only appear in the Blueprint node menu after an editor restart).
Before re-running, delete Content/Characters/Cat/ABP_Cat and BP_Cat with the editor closed.

Creates / changes
- /Game/Characters/Cat/ABP_Cat        rest pose when still, walk cycle when moving. The walk is
                                      driven by distance travelled (no foot sliding at any speed).
- /Game/Input/Actions/IA_SwitchWorld  mapped to Q in IMC_Default
- /Game/Characters/Cat/BP_Cat         copy of BP_ThirdPersonCharacter (keeps move/look/jump) with
                                      SK_Cat + ABP_Cat. Q -> ToggleGlitchState swaps the mesh material
                                      between NormalMaterial (M_Cat_Toon) and GlitchMaterial
                                      (M_Cat_Hologram), 3 s cooldown.
- BP_ThirdPersonGameMode              default pawn = BP_Cat
"""
import os
import unreal

CAT = "/Game/Characters/Cat"
SKELETON = f"{CAT}/SKEL_Cat"
MESH = f"{CAT}/SK_Cat"
WALK = f"{CAT}/Animations/A_Cat_Walk"
ABP_PATH = f"{CAT}/ABP_Cat"
BP_PATH = f"{CAT}/BP_Cat"
TEMPLATE_BP = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
GAME_MODE = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode"
IA_PATH = "/Game/Input/Actions/IA_SwitchWorld"
IMC_PATH = "/Game/Input/IMC_Default"
SWITCH_KEY = "Q"

WALK_GROUND_SPEED = 30.6        # cm/s the walk covers at play rate 1 (printed by Tools/Blender/rig_cat.py)
CAPSULE_RADIUS = 16.0
CAPSULE_HALF_HEIGHT = 16.5      # cat is ~32.5 cm tall, ~45 cm long without the tail
NORMAL_MATERIAL = f"{CAT}/M_Cat_Toon"       # from Tools/Python/build_cat_materials.py
GLITCH_MATERIAL = f"{CAT}/M_Cat_Hologram"
WALK_SPEED = 100.0              # cm/s; the legs speed up to match (about 3.3x the authored pace)
JUMP_Z = 450.0
SWITCH_COOLDOWN = 3.0

BEL = unreal.BlueprintEditorLibrary
GE = unreal.BlueprintGraphEditor
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
LOG_PATH = os.environ.get("CAT_LOG")
_log = open(LOG_PATH, "w", encoding="utf-8") if LOG_PATH else None


def log(*a):
    msg = " ".join(str(x) for x in a)
    unreal.log("BUILD_CAT: " + msg)
    if _log:
        _log.write(msg + "\n")
        _log.flush()


# ---------------------------------------------------------------- graph helpers
def pins(node):
    return [str(p.get_pin_name()) for p in BEL.list_all_pins(node)]


def pin(node, name, direction):
    for p in BEL.list_all_pins(node):
        if str(p.get_pin_name()) == name and p.get_pin_direction() == direction:
            return p
    raise RuntimeError(f"pin '{name}' not found on {BEL.get_node_title(node)}; pins: {pins(node)}")


def out_pin(node, name):
    return pin(node, name, unreal.EdGraphPinDirection.EGPD_OUTPUT)


def in_pin(node, name):
    return pin(node, name, unreal.EdGraphPinDirection.EGPD_INPUT)


def link(a, b):
    if not a.try_create_connection(b):
        raise RuntimeError(f"cannot connect {a.get_pin_name()} -> {b.get_pin_name()} "
                           f"({BEL.get_node_title(a.get_owning_node())} -> {BEL.get_node_title(b.get_owning_node())})")


def place(node, x, y):
    BEL.set_node_pos(node, unreal.IntPoint(int(x), int(y)))
    return node


def by_name(ed, name, x, y):
    node = ed.create_node_from_name(name, unreal.Vector2D(x, y), [])
    if not node:
        raise RuntimeError(f"node '{name}' could not be created")
    return place(node, x, y)


def call(ed, function_path, x, y):
    node = ed.add_call_function_node(function_path)
    if not node:
        raise RuntimeError(f"function '{function_path}' not found")
    return place(node, x, y)


def get_var(ed, name, x, y):
    return place(ed.add_get_member_variable_node(name), x, y)


def set_var(ed, name, x, y):
    return place(ed.add_set_member_variable_node(name), x, y)


def var_type(*names):
    for n in names:
        t = BEL.get_basic_type_by_name(n)
        if t:
            return t
    raise RuntimeError(f"no basic type among {names}")


def save(asset):
    """Git LFS 'lockable' files are read-only until locked: lock them (git lfs lock) or make them writable."""
    if not eal.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {asset.get_path_name()} (read-only? run `git lfs lock` on it first)")


def must_not_exist(path):
    if eal.does_asset_exist(path):
        raise RuntimeError(f"{path} already exists. Close the editor, delete its .uasset and re-run.")


def compile_checked(bp, *editors):
    BEL.compile_blueprint(bp)
    problems = []
    for ed in editors:
        problems += [f"ERROR {BEL.get_node_title(n)}" for n in ed.list_nodes_with_errors()]
        problems += [f"warning {BEL.get_node_title(n)}" for n in ed.list_nodes_with_warnings()]
    log(bp.get_name(), "compiled;", problems or "no node errors/warnings")
    if any(p.startswith("ERROR") for p in problems):
        raise RuntimeError(f"{bp.get_name()} has node errors")


# ---------------------------------------------------------------- input
def build_input():
    created = False
    if eal.does_asset_exist(IA_PATH):
        ia = unreal.load_asset(IA_PATH)
    else:
        ia = tools.create_asset("IA_SwitchWorld", "/Game/Input/Actions", unreal.InputAction, None)
        created = True
    ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    save(ia)

    imc = unreal.load_asset(IMC_PATH)
    key = unreal.Key()
    key.set_editor_property("key_name", SWITCH_KEY)
    mappings = imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
    for m in mappings:
        if m.get_editor_property("action") == ia:
            imc.unmap_key(ia, m.get_editor_property("key"))
    imc.map_key(ia, key)
    bound = [str(m.get_editor_property("key").get_editor_property("key_name"))
             for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
             if m.get_editor_property("action") == ia]
    if bound != [SWITCH_KEY]:
        raise RuntimeError(f"IA_SwitchWorld is bound to {bound}, expected ['{SWITCH_KEY}']")
    save(imc)
    log("input: IA_SwitchWorld ->", bound)
    return ia, created


# ---------------------------------------------------------------- ABP_Cat
def build_abp():
    must_not_exist(ABP_PATH)
    walk = unreal.load_asset(WALK)
    walk_len = walk.get_play_length()
    f = unreal.AnimBlueprintFactory()
    f.set_editor_property("target_skeleton", unreal.load_asset(SKELETON))
    f.set_editor_property("parent_class", unreal.AnimInstance)
    f.set_editor_property("preview_skeletal_mesh", unreal.load_asset(MESH))
    abp = tools.create_asset("ABP_Cat", CAT, unreal.AnimBlueprint, f)

    real = var_type("real", "float", "double")
    eg = GE.get_graph_editor(BEL.find_event_graph(abp))
    for name in ("Speed", "WalkAlpha", "WalkPhase", "WalkTime"):
        eg.add_member_variable(name, real, "0.0")

    # Event graph:
    #   Speed     = ground speed of the owning pawn
    #   WalkAlpha = 0 when still, 1 above 15 cm/s
    #   WalkPhase = frac(WalkPhase + dt * Speed / (WALK_GROUND_SPEED * walk_len))   (distance driven)
    #   WalkTime  = WalkPhase * walk_len
    event = eg.find_event_node("BlueprintUpdateAnimation")
    owner = call(eg, "/Script/Engine.AnimInstance:TryGetPawnOwner", 0, 300)
    valid = call(eg, "/Script/Engine.KismetSystemLibrary:IsValid", 300, 300)
    branch = place(eg.add_branch_node(), 400, 0)
    velocity = call(eg, "/Script/Engine.Actor:GetVelocity", 300, 450)
    size_xy = call(eg, "/Script/Engine.KismetMathLibrary:VSizeXY", 550, 450)
    set_speed = set_var(eg, "Speed", 700, 0)
    alpha_map = call(eg, "/Script/Engine.KismetMathLibrary:MapRangeClamped", 900, 300)
    set_alpha = set_var(eg, "WalkAlpha", 1100, 0)
    mul_dt = call(eg, "/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble", 1100, 450)
    mul_k = call(eg, "/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble", 1300, 450)
    add_phase = call(eg, "/Script/Engine.KismetMathLibrary:Add_DoubleDouble", 1500, 450)
    frac = call(eg, "/Script/Engine.KismetMathLibrary:Fraction", 1700, 450)
    set_phase = set_var(eg, "WalkPhase", 1500, 0)
    mul_len = call(eg, "/Script/Engine.KismetMathLibrary:Multiply_DoubleDouble", 1800, 300)
    set_time = set_var(eg, "WalkTime", 1950, 0)
    log("event pins:", pins(event), "| Fraction:", pins(frac), "| Multiply:", pins(mul_dt))

    dt_pin = next(p for p in pins(event) if p.startswith("DeltaTime"))
    link(out_pin(event, "then"), in_pin(branch, "execute"))
    link(out_pin(owner, "ReturnValue"), in_pin(valid, "Object"))
    link(out_pin(valid, "ReturnValue"), in_pin(branch, "Condition"))
    link(out_pin(owner, "ReturnValue"), in_pin(velocity, "self"))
    link(out_pin(velocity, "ReturnValue"), in_pin(size_xy, "A"))
    link(out_pin(branch, "then"), in_pin(set_speed, "execute"))
    link(out_pin(size_xy, "ReturnValue"), in_pin(set_speed, "Speed"))
    link(out_pin(set_speed, "then"), in_pin(set_alpha, "execute"))
    link(out_pin(set_speed, "Output_Get"), in_pin(alpha_map, "Value"))
    for pn, v in (("InRangeA", "0.0"), ("InRangeB", "15.0"), ("OutRangeA", "0.0"), ("OutRangeB", "1.0")):
        in_pin(alpha_map, pn).set_pin_value(v)
    link(out_pin(alpha_map, "ReturnValue"), in_pin(set_alpha, "WalkAlpha"))
    link(out_pin(event, dt_pin), in_pin(mul_dt, "A"))
    link(out_pin(set_speed, "Output_Get"), in_pin(mul_dt, "B"))
    link(out_pin(mul_dt, "ReturnValue"), in_pin(mul_k, "A"))
    in_pin(mul_k, "B").set_pin_value(f"{1.0 / (WALK_GROUND_SPEED * walk_len):.6f}")
    link(out_pin(mul_k, "ReturnValue"), in_pin(add_phase, "A"))
    link(out_pin(get_var(eg, "WalkPhase", 1300, 600), "WalkPhase"), in_pin(add_phase, "B"))
    link(out_pin(add_phase, "ReturnValue"), in_pin(frac, "A"))
    link(out_pin(set_alpha, "then"), in_pin(set_phase, "execute"))
    link(out_pin(frac, "ReturnValue"), in_pin(set_phase, "WalkPhase"))
    link(out_pin(set_phase, "then"), in_pin(set_time, "execute"))
    link(out_pin(set_phase, "Output_Get"), in_pin(mul_len, "A"))
    in_pin(mul_len, "B").set_pin_value(f"{walk_len:.6f}")
    link(out_pin(mul_len, "ReturnValue"), in_pin(set_time, "WalkTime"))

    # Anim graph: rest pose <-> walk (evaluated at WalkTime), blended by WalkAlpha.
    ag = GE.get_graph_editor(BEL.find_graph(abp, "AnimGraph"))
    root = next(n for n in ag.list_all_nodes() if n.get_class().get_name() == "AnimGraphNode_Root")
    place(root, 900, 0)
    rest = by_name(ag, "Animation|Poses|LocalSpaceRefPose", 0, -150)
    walk_eval = by_name(ag, "Animation|Sequences|Evaluate'A_Cat_Walk'", 0, 100)
    blend = by_name(ag, "Animation|Blends|TwoWayBlend", 500, 0)
    log("pins RefPose:", pins(rest), "| Evaluator:", pins(walk_eval), "| Blend:", pins(blend))
    link(out_pin(get_var(ag, "WalkTime", -250, 200), "WalkTime"), in_pin(walk_eval, "ExplicitTime"))
    link(out_pin(rest, "Pose"), in_pin(blend, "A"))
    link(out_pin(walk_eval, "Pose"), in_pin(blend, "B"))
    link(out_pin(get_var(ag, "WalkAlpha", 300, 250), "WalkAlpha"), in_pin(blend, "Alpha"))
    link(out_pin(blend, "Pose"), in_pin(root, "Result"))

    compile_checked(abp, eg, ag)
    save(abp)
    return abp


# ---------------------------------------------------------------- BP_Cat
def subobject_templates(bp):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    return {str(lib.get_variable_name(lib.get_data(h))): lib.get_object(lib.get_data(h))
            for h in sds.k2_gather_subobject_data_for_blueprint(bp)}


def remove_component(bp, name):
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = list(sds.k2_gather_subobject_data_for_blueprint(bp))
    target = next((h for h in handles if str(lib.get_variable_name(lib.get_data(h))) == name), None)
    if target is None:
        return
    removed = sds.delete_subobject(handles[0], target, bp)
    if not removed:
        raise RuntimeError(f"could not remove component {name} from {bp.get_name()}")
    BEL.compile_blueprint(bp)
    log("removed component", name)


def build_bp(abp):
    must_not_exist(BP_PATH)
    bp = eal.duplicate_asset(TEMPLATE_BP, BP_PATH)
    BEL.compile_blueprint(bp)
    # Remove the old block cat first: deleting a component re-instances the class defaults,
    # which would discard the settings below.
    remove_component(bp, "GlitchCat")
    comps = subobject_templates(bp)

    cdo = unreal.get_default_object(bp.generated_class())
    cap = cdo.get_editor_property("capsule_component")
    cap.set_editor_property("capsule_radius", CAPSULE_RADIUS)
    cap.set_editor_property("capsule_half_height", CAPSULE_HALF_HEIGHT)
    mesh = cdo.get_editor_property("mesh")
    mesh.set_editor_property("skeletal_mesh_asset", unreal.load_asset(MESH))
    mesh.set_editor_property("override_materials", [])  # the template overrides with mannequin materials
    mesh.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_BLUEPRINT)
    mesh.set_editor_property("anim_class", abp.generated_class())
    mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -CAPSULE_HALF_HEIGHT))
    mesh.set_editor_property("relative_rotation", unreal.Rotator(0, 0, 0))  # SK_Cat faces +X
    mesh.set_editor_property("visible", True)
    move =cdo.get_editor_property("character_movement")
    move.set_editor_property("max_walk_speed", WALK_SPEED)
    move.set_editor_property("jump_z_velocity", JUMP_Z)
    boom = comps["CameraBoom"]
    boom.set_editor_property("target_arm_length", 200.0)
    boom.set_editor_property("socket_offset", unreal.Vector(0, 0, 30))

    boolean = var_type("bool", "boolean")
    real = var_type("real", "float", "double")
    eg = GE.get_graph_editor(BEL.find_event_graph(bp))
    eg.add_member_variable("bIsGlitched", boolean, "false")
    eg.add_member_variable("bCanSwitch", boolean, "true")
    eg.add_member_variable("SwitchCooldown", real, str(SWITCH_COOLDOWN))
    mat_type = BEL.get_object_reference_type(unreal.MaterialInterface)
    eg.add_member_variable("NormalMaterial", mat_type, f"{NORMAL_MATERIAL}.{NORMAL_MATERIAL.split('/')[-1]}")
    eg.add_member_variable("GlitchMaterial", mat_type, f"{GLITCH_MATERIAL}.{GLITCH_MATERIAL.split('/')[-1]}")
    for v in ("bIsGlitched", "bCanSwitch", "SwitchCooldown", "NormalMaterial", "GlitchMaterial"):
        BEL.set_blueprint_variable_category(bp, v, unreal.Text("Glitch State"))
    for v in ("SwitchCooldown", "NormalMaterial", "GlitchMaterial"):
        BEL.set_blueprint_variable_instance_editable(bp, v, True)
    BEL.compile_blueprint(bp)
    gen_cdo = unreal.get_default_object(bp.generated_class())
    for v, path in (("NormalMaterial", NORMAL_MATERIAL), ("GlitchMaterial", GLITCH_MATERIAL)):
        if gen_cdo.get_editor_property(v) is None:  # default text was not accepted: set it on the CDO
            gen_cdo.set_editor_property(v, unreal.load_asset(path))
        log(v, "=", gen_cdo.get_editor_property(v).get_name())

    # ToggleGlitchState: if bCanSwitch -> flip bIsGlitched, put GlitchMaterial / NormalMaterial on
    # the mesh, lock for SwitchCooldown.
    x, y = 0, 1800
    toggle = place(eg.add_custom_event_node("ToggleGlitchState"), x, y)
    BEL.compile_blueprint(bp)
    branch = place(eg.add_branch_node(), x + 300, y)
    not_g = call(eg, "/Script/Engine.KismetMathLibrary:Not_PreBool", x + 600, y + 220)
    set_g = set_var(eg, "bIsGlitched", x + 850, y)
    which = place(eg.add_branch_node(), x + 1150, y)
    set_glitch = call(eg, "/Script/Engine.PrimitiveComponent:SetMaterial", x + 1450, y - 150)
    set_normal = call(eg, "/Script/Engine.PrimitiveComponent:SetMaterial", x + 1450, y + 200)
    lock = set_var(eg, "bCanSwitch", x + 1850, y)
    delay = call(eg, "/Script/Engine.KismetSystemLibrary:Delay", x + 2100, y)
    unlock = set_var(eg, "bCanSwitch", x + 2400, y)
    link(out_pin(toggle, "then"), in_pin(branch, "execute"))
    link(out_pin(get_var(eg, "bCanSwitch", x + 100, y + 150), "bCanSwitch"), in_pin(branch, "Condition"))
    link(out_pin(branch, "then"), in_pin(set_g, "execute"))
    link(out_pin(get_var(eg, "bIsGlitched", x + 400, y + 220), "bIsGlitched"), in_pin(not_g, "A"))
    link(out_pin(not_g, "ReturnValue"), in_pin(set_g, "bIsGlitched"))
    link(out_pin(set_g, "then"), in_pin(which, "execute"))
    link(out_pin(set_g, "Output_Get"), in_pin(which, "Condition"))
    for node, var, exec_out, dy in ((set_glitch, "GlitchMaterial", "then", -50), (set_normal, "NormalMaterial", "else", 300)):
        link(out_pin(which, exec_out), in_pin(node, "execute"))
        link(out_pin(get_var(eg, "Mesh", x + 1250, y + dy), "Mesh"), in_pin(node, "self"))
        link(out_pin(get_var(eg, var, x + 1250, y + dy + 70), var), in_pin(node, "Material"))
        in_pin(node, "ElementIndex").set_pin_value("0")
        link(out_pin(node, "then"), in_pin(lock, "execute"))
    in_pin(lock, "bCanSwitch").set_pin_value("false")
    link(out_pin(lock, "then"), in_pin(delay, "execute"))
    link(out_pin(get_var(eg, "SwitchCooldown", x + 1850, y + 200), "SwitchCooldown"), in_pin(delay, "Duration"))
    link(out_pin(delay, "then"), in_pin(unlock, "execute"))
    in_pin(unlock, "bCanSwitch").set_pin_value("true")

    # Q (IA_SwitchWorld, Started) -> ToggleGlitchState
    q_event = by_name(eg, "Input|EnhancedActionEvents|IA_SwitchWorld", x - 450, y - 300)
    q_call = eg.add_call_function_node(f"{BP_PATH}.BP_Cat_C:ToggleGlitchState") or by_name(
        eg, next(n for n in eg.list_available_nodes([]) if n.endswith("ToggleGlitchState")), 0, 0)
    place(q_call, x - 100, y - 300)
    link(out_pin(q_event, "Started"), in_pin(q_call, "execute"))
    eg.add_comment_node(
        "Q -> ToggleGlitchState: NormalMaterial (toon) <-> GlitchMaterial (hologram) on the cat, 3 s cooldown. "
        "BP_WorldManager (issue #12) should call ToggleGlitchState instead of adding its own switch.",
        unreal.Vector2D(x - 500, y - 420), unreal.Vector2D(3000, 1000))

    compile_checked(bp, eg)
    save(bp)
    return bp


def set_default_pawn(bp):
    gm = unreal.load_asset(GAME_MODE)
    unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", bp.generated_class())
    BEL.compile_blueprint(gm)
    save(gm)
    log("game mode default pawn ->", bp.get_name())


ia, created = build_input()
if created:
    log("IA_SwitchWorld was just created: run this script once more (the node menu needs a restart).")
else:
    abp = build_abp()
    bp = build_bp(abp)
    set_default_pawn(bp)
    log("DONE")
