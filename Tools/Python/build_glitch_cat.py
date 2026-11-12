"""Builds the block-style glitched cat and puts it on BP_ThirdPersonCharacter.

Run headless:
  UnrealEditor-Cmd.exe Glitching_Realities.uproject -run=pythonscript -script=Tools/Python/build_glitch_cat.py
Re-running regenerates the mesh and materials (the Blueprint component is reused).
"""
import os
import unreal

FOLDER = "/Game/GlitchCat"
BP_PATH = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"
CAPSULE_RADIUS = 34.0
CAPSULE_HALF_HEIGHT = 44.0

LOG_PATH = os.environ.get("GLITCHCAT_LOG")
_log_file = open(LOG_PATH, "w", encoding="utf-8") if LOG_PATH else None


def log(*a):
    msg = " ".join(str(x) for x in a)
    unreal.log("GLITCHCAT: " + msg)
    if _log_file:
        _log_file.write(msg + "\n")
        _log_file.flush()


asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary


def fresh_asset(name, cls, factory):
    path = f"{FOLDER}/{name}"
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    return asset_tools.create_asset(name, FOLDER, cls, factory)


# ---------------------------------------------------------------- material
WPO_HLSL = r"""
// P: local vertex position (cm, X forward, Z up, origin at the feet)
// O: object world position -> legs cycle with distance travelled
float3 off = float3(0, 0, 0);

// --- gait: diagonal leg pairs swing together
float ph = sin(O.x * 0.045 * S) + sin(O.y * 0.051 * S + 1.7);
float pivotZ = 27.0;
if (P.z < pivotZ + 1.0 && abs(P.x) > 13.0 && abs(P.x) < 36.0)
{
    float legX = sign(P.x) * 24.0;
    float a = 0.32 * ph * sign(P.x) * sign(P.y);
    float dx = P.x - legX;
    float dz = P.z - pivotZ;
    float nx = dx * cos(a) - dz * sin(a);
    float nz = dx * sin(a) + dz * cos(a);
    off.x += nx - dx;
    off.z += nz - dz;
}

// --- tail sway + breathing + head bob
if (P.x < -33.0)
    off.y += sin(T * 3.0) * (-P.x - 33.0) * 0.35;
if (P.z > 26.0)
    off.z += sin(T * 2.2) * 0.7;
if (P.x > 31.0 && P.z > 48.0)
    off.z += sin(T * 2.2 + 0.8) * 1.2;

// --- glitch: horizontal slices that snap sideways
float tick = floor(T * 14.0);
float band = floor(P.z / 7.0);
float n = frac(sin(dot(float2(band, tick), float2(12.9898, 78.233))) * 43758.5453);
float big = frac(sin(tick * 91.345) * 47453.5453);
if (n > 1.0 - 0.08 * G)
    off.y += (frac(n * 37.0) - 0.5) * 14.0 * G;
if (big > 1.0 - 0.03 * G)
    off.x += (frac(big * 13.0) - 0.5) * 18.0 * G;
return off;
"""

EMISSIVE_HLSL = r"""
float tick = floor(T * 14.0);
float band = floor(P.z / 7.0);
float n = frac(sin(dot(float2(band, tick), float2(12.9898, 78.233))) * 43758.5453);
float scan = step(0.55, frac(P.z * 0.35 - T * 3.0));
float3 grad = lerp(A, B, frac(P.z * 0.02 + P.x * 0.01 + T * 0.4));
float3 body = grad * (0.15 + 0.5 * scan);
if (n > 1.0 - 0.08 * G)
    body += (frac(n * 7.0) > 0.5 ? A : B) * 6.0;
float blink = step(0.06, frac(T * 0.23));
float3 eye = E * 12.0 * blink;
return lerp(body, eye, M);
"""


def custom_node(mat, code, inputs, x, y):
    node = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, x, y)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    pins = []
    for n in inputs:
        ci = unreal.CustomInput()
        ci.import_text(f'(InputName="{n}")')
        pins.append(ci)
    node.set_editor_property("inputs", pins)
    return node


def scalar(mat, name, value, x, y):
    n = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
    n.set_editor_property("parameter_name", name)
    n.set_editor_property("default_value", value)
    return n


def vector(mat, name, rgb, x, y):
    n = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
    n.set_editor_property("parameter_name", name)
    n.set_editor_property("default_value", unreal.LinearColor(*rgb, 1.0))
    return n


def build_material():
    mat = fresh_asset("M_GlitchCat", unreal.Material, unreal.MaterialFactoryNew())

    local_pos = mel.create_material_expression(mat, unreal.MaterialExpressionLocalPosition, -1200, 0)
    time = mel.create_material_expression(mat, unreal.MaterialExpressionTime, -1200, 150)
    obj_pos = mel.create_material_expression(mat, unreal.MaterialExpressionObjectPositionWS, -1200, 300)
    glitch = scalar(mat, "GlitchAmount", 1.0, -1200, 450)
    gait = scalar(mat, "GaitSpeed", 1.0, -1200, 550)
    eye_mode = scalar(mat, "EyeMode", 0.0, -1200, 650)
    col_a = vector(mat, "GlitchColorA", (0.0, 1.0, 0.9), -1200, 750)
    col_b = vector(mat, "GlitchColorB", (1.0, 0.0, 0.8), -1200, 950)
    eye_col = vector(mat, "EyeColor", (0.3, 1.0, 0.1), -1200, 1150)
    base = vector(mat, "BaseColor", (0.02, 0.015, 0.04), -400, -300)
    rough = scalar(mat, "Roughness", 0.35, -400, -150)

    wpo = custom_node(mat, WPO_HLSL, ["P", "T", "O", "G", "S"], -700, 0)
    for src, pin in [(local_pos, "P"), (time, "T"), (obj_pos, "O"), (glitch, "G"), (gait, "S")]:
        mel.connect_material_expressions(src, "", wpo, pin)
    to_world = mel.create_material_expression(mat, unreal.MaterialExpressionTransform, -400, 0)
    to_world.set_editor_property("transform_source_type", unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL)
    to_world.set_editor_property("transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
    mel.connect_material_expressions(wpo, "", to_world, "")

    emi = custom_node(mat, EMISSIVE_HLSL, ["P", "T", "A", "B", "E", "M", "G"], -700, 500)
    for src, pin in [(local_pos, "P"), (time, "T"), (col_a, "A"), (col_b, "B"),
                     (eye_col, "E"), (eye_mode, "M"), (glitch, "G")]:
        mel.connect_material_expressions(src, "", emi, pin)

    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(emi, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.connect_material_property(to_world, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)

    def instance(name, eye):
        mi = fresh_asset(name, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, mat)
        mel.set_material_instance_scalar_parameter_value(mi, "EyeMode", eye)
        eal.save_loaded_asset(mi)
        return mi

    return instance("MI_GlitchCat_Body", 0.0), instance("MI_GlitchCat_Eyes", 1.0)


# ---------------------------------------------------------------- mesh
# (center x, y, z), (size x, y, z), material id   -- cm, X forward, Z up, feet at z=0
BODY, EYES = 0, 1
PARTS = [
    ((0, 0, 40), (70, 34, 30), BODY),            # torso
    ((46, 0, 62), (28, 30, 26), BODY),           # head
    ((62, 0, 57), (6, 14, 9), BODY),             # snout
    ((42, 10, 80), (8, 7, 10), BODY),            # ear L
    ((42, -10, 80), (8, 7, 10), BODY),           # ear R
    ((42, 10, 86.5), (4, 4, 3), BODY),           # ear tip L
    ((42, -10, 86.5), (4, 4, 3), BODY),          # ear tip R
    ((60.5, 7, 66), (2, 6, 5), EYES),            # eye L
    ((60.5, -7, 66), (2, 6, 5), EYES),           # eye R
    ((-40, 0, 51), (12, 7, 7), BODY),            # tail 1
    ((-47, 0, 58), (8, 7, 10), BODY),            # tail 2
    ((-51, 0, 68), (7, 7, 10), BODY),            # tail 3
    ((-53, 0, 78), (7, 7, 10), BODY),            # tail 4
]
for lx in (24, -24):                            # legs + paws
    for ly in (11, -11):
        PARTS.append(((lx, ly, 14), (10, 10, 28), BODY))
        PARTS.append(((lx + 1, ly, 2.5), (13, 12, 5), BODY))


def build_mesh(body_mi, eyes_mi):
    dm = unreal.DynamicMesh()
    for (c, s, mat_id) in PARTS:
        opts = unreal.GeometryScriptPrimitiveOptions()
        opts.set_editor_property("material_id", mat_id)
        xf = unreal.Transform(location=unreal.Vector(*c))
        steps = [max(1, int(v / 6)) for v in s]  # extra verts so WPO slices bend the blocks
        unreal.GeometryScript_Primitives.append_box(
            dm, opts, xf, s[0], s[1], s[2], steps[0], steps[1], steps[2],
            unreal.GeometryScriptPrimitiveOriginMode.CENTER)

    path = f"{FOLDER}/SM_GlitchCat"
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    opts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    opts.set_editor_property("enable_recompute_normals", False)
    opts.set_editor_property("enable_recompute_tangents", True)
    opts.set_editor_property("enable_collision", False)
    sm, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, path, opts)
    log("create static mesh:", outcome, "slots:", len(sm.get_editor_property("static_materials")))
    slots = []
    for mi, slot in [(body_mi, "Body"), (eyes_mi, "Eyes")]:
        s = unreal.StaticMaterial()
        s.set_editor_property("material_interface", mi)
        s.set_editor_property("material_slot_name", slot)
        slots.append(s)
    sm.set_editor_property("static_materials", slots)
    # WPO can push verts outside the bounds; pad them so the cat isn't culled
    sm.set_editor_property("positive_bounds_extension", unreal.Vector(30, 30, 20))
    sm.set_editor_property("negative_bounds_extension", unreal.Vector(30, 30, 20))
    eal.save_loaded_asset(sm)
    return sm


# ---------------------------------------------------------------- blueprint
def setup_blueprint(sm):
    bp = unreal.load_asset(BP_PATH)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    handles = {}
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        handles[str(lib.get_variable_name(lib.get_data(h)))] = h

    cat_handle = handles.get("GlitchCat")
    if cat_handle is None:
        params = unreal.AddNewSubobjectParams(
            parent_handle=handles["CapsuleComponent"],
            new_class=unreal.StaticMeshComponent,
            blueprint_context=bp)
        cat_handle, fail = sds.add_new_subobject(params)
        log("add_new_subobject fail reason:", fail)
        sds.rename_subobject(cat_handle, unreal.Text("GlitchCat"))
    cat = lib.get_object(lib.get_data(cat_handle))
    cat.set_editor_property("static_mesh", sm)
    cat.set_editor_property("relative_location", unreal.Vector(0, 0, -CAPSULE_HALF_HEIGHT))
    cat.set_collision_profile_name("NoCollision")
    cat.set_editor_property("cast_shadow", True)

    cdo = unreal.get_default_object(bp.generated_class())
    cap = cdo.get_editor_property("capsule_component")
    cap.set_editor_property("capsule_radius", CAPSULE_RADIUS)
    cap.set_editor_property("capsule_half_height", CAPSULE_HALF_HEIGHT)
    mesh = cdo.get_editor_property("mesh")
    mesh.set_editor_property("visible", False)
    mesh.set_editor_property("relative_location", unreal.Vector(0, 0, -CAPSULE_HALF_HEIGHT))

    boom = lib.get_object(lib.get_data(handles["CameraBoom"]))
    boom.set_editor_property("target_arm_length", 320.0)

    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    eal.save_loaded_asset(bp)
    log("blueprint saved")


body_mi, eyes_mi = build_material()
log("materials ok")
sm = build_mesh(body_mi, eyes_mi)
log("mesh ok", sm.get_name(), "tris:", sm.get_num_triangles(0))
setup_blueprint(sm)
log("DONE")
