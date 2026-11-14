"""Builds the two cat materials and makes the toon one SK_Cat's default.

Run headless (UE 5.8.4), editor closed, after Tools/Python/import_cat.py:
  UnrealEditor-Cmd.exe Glitching_Realities.uproject -run=pythonscript -script=Tools/Python/build_cat_materials.py
Re-running replaces both materials.

M_Cat_Toon      normal cat. Cel shading: two tones (lit / shadow) from the sun direction, a soft
                rim light and glowing eyes, on Tripo's texture. Unlit + exposure-compensated so
                it reads like Tripo's viewer regardless of the level's lighting.
M_Cat_Hologram  glitch cat (Tripo's "hologram" viewer style recreated): translucent teal, bright
                edges, a grid that sticks to the body, a light band sweeping up the cat, flicker
                and short sideways glitch jumps.
Every look value is a material parameter, so instances (MI_*) can tune them without scripts.
"""
import os
import unreal

DEST = "/Game/Characters/Cat"
eal = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
LOG_PATH = os.environ.get("CAT_LOG")
_log = open(LOG_PATH, "w", encoding="utf-8") if LOG_PATH else None


def log(*a):
    msg = " ".join(str(x) for x in a)
    unreal.log("CAT_MATERIALS: " + msg)
    if _log:
        _log.write(msg + "\n")
        _log.flush()


def fresh_material(name):
    path = f"{DEST}/{name}"
    if eal.does_asset_exist(path) and not eal.delete_asset(path):
        raise RuntimeError(f"cannot delete {path}; close the editor and delete it on disk")
    mat = tools.create_asset(name, DEST, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("used_with_skeletal_mesh", True)
    return mat


def expr(mat, cls_name, x, y, **props):
    cls = getattr(unreal, cls_name, None)
    if cls is None:
        return None
    node = mel.create_material_expression(mat, cls, x, y)
    for k, v in props.items():
        node.set_editor_property(k, v)
    return node


def scalar(mat, name, value, x, y, group):
    return expr(mat, "MaterialExpressionScalarParameter", x, y, parameter_name=name, default_value=value, group=group)


def vector(mat, name, rgb, x, y, group):
    return expr(mat, "MaterialExpressionVectorParameter", x, y, parameter_name=name,
                default_value=unreal.LinearColor(*rgb, 1.0), group=group)


def custom(mat, code, inputs, x, y):
    node = expr(mat, "MaterialExpressionCustom", x, y, code=code,
                output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    pins = []
    for n in inputs:
        ci = unreal.CustomInput()
        ci.import_text(f'(InputName="{n}")')
        pins.append(ci)
    node.set_editor_property("inputs", pins)
    return node


def wire(src, dst, pin, out=""):
    if not mel.connect_material_expressions(src, out, dst, pin):
        raise RuntimeError(f"could not connect {src.get_name()}.{out} -> {dst.get_name()}.{pin}")


def exposure_neutral(mat, color_node, x, y):
    """Cancel auto-exposure so the on-screen color matches the material value (like Tripo's viewer)."""
    inv = expr(mat, "MaterialExpressionEyeAdaptationInverse", x, y)
    if inv is None:
        log("EyeAdaptationInverse not available; using the color as is")
        return color_node, ""
    wire(color_node, inv, "LightValueInput")
    return inv, ""


texture = unreal.load_asset(f"{DEST}/T_Cat_BaseColor")
if not texture:
    raise RuntimeError("Run import_cat.py first (T_Cat_BaseColor missing)")

# ---------------------------------------------------------------- M_Cat_Toon
TOON_HLSL = r"""
float3 n = normalize(N);
float3 l = normalize(L);
float ndl = dot(n, l);
float lit = smoothstep(-Soft, Soft, ndl);                    // hard-ish terminator = cartoon look
float light = lerp(ShadowLevel, 1.0, lit);
float rim = pow(1.0 - saturate(dot(n, normalize(V))), RimPower) * RimStrength * (0.35 + 0.65 * lit);
float lum = dot(C, float3(0.333, 0.333, 0.333));
float eyes = smoothstep(0.55, 0.8, lum);                     // the eyes are the only bright texels
float3 col = C * Brightness * light + RimColor * rim + C * eyes * EyeGlow;
return col;
"""

toon = fresh_material("M_Cat_Toon")
toon.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
tex = expr(toon, "MaterialExpressionTextureSample", -1200, -200, texture=texture)
normal = expr(toon, "MaterialExpressionVertexNormalWS", -1200, 50)
camvec = expr(toon, "MaterialExpressionCameraVectorWS", -1200, 150)
sun = expr(toon, "MaterialExpressionAtmosphericLightVector", -1200, 250)
if sun is None:  # fallback: fixed key light from the front-left, above
    sun = expr(toon, "MaterialExpressionConstant3Vector", -1200, 250, constant=unreal.LinearColor(0.45, -0.35, 0.82, 1))
    log("AtmosphericLightVector not available; using a fixed light direction")
p = {
    "Brightness": scalar(toon, "Brightness", 1.6, -1200, 400, "Toon"),
    "ShadowLevel": scalar(toon, "ShadowLevel", 0.55, -1200, 480, "Toon"),
    "Soft": scalar(toon, "TerminatorSoftness", 0.08, -1200, 560, "Toon"),
    "RimPower": scalar(toon, "RimPower", 3.0, -1200, 640, "Toon"),
    "RimStrength": scalar(toon, "RimStrength", 0.06, -1200, 720, "Toon"),
    "RimColor": vector(toon, "RimColor", (0.55, 0.6, 0.7), -1200, 800, "Toon"),
    "EyeGlow": scalar(toon, "EyeGlow", 0.8, -1200, 960, "Toon"),
}
toon_node = custom(toon, TOON_HLSL, ["C", "N", "L", "V"] + list(p), -700, 0)
wire(tex, toon_node, "C", "RGB")
wire(normal, toon_node, "N")
wire(camvec, toon_node, "V")
wire(sun, toon_node, "L")
for name, node in p.items():
    wire(node, toon_node, name)
out, pin = exposure_neutral(toon, toon_node, -350, 0)
mel.connect_material_property(out, pin, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(toon)
eal.save_loaded_asset(toon)
log("M_Cat_Toon built")

# ---------------------------------------------------------------- M_Cat_Hologram
HOLO_HLSL = r"""
float3 n = normalize(N);
float fres = pow(1.0 - saturate(abs(dot(n, normalize(V)))), FresnelPower);
// Grid lines in the cat's own space (pre-skinning), so they move with the body.
float3 g = abs(frac(P / GridSize) - 0.5);
float d = 0.5 - max(g.x, max(g.y, g.z));
float grid = 1.0 - smoothstep(0.0, GridWidth, d);
// Light band sweeping from the paws to the ears, plus fine moving scanlines.
float h = saturate(P.z / CatHeight);
float band = 1.0 - smoothstep(0.0, BandWidth, abs(h - frac(T * BandSpeed)));
float lines = 0.5 + 0.5 * sin(P.z * 2.2 - T * 6.0);
// Flicker: a few frames per second dim at random.
float tick = floor(T * 18.0);
float rnd = frac(sin(tick * 91.3458) * 47453.5453);
float flick = rnd > 0.9 ? 0.35 : 1.0;
float detail = dot(C, float3(0.333, 0.333, 0.333));
float I = 0.35 + fres * 1.4 + grid * 0.35 + band * 2.2 + lines * 0.08 + detail * 0.9;
return Color * I * Glow * flick;
"""
# Opacity: see-through body, solid edges / grid / band, so the teal reads on light backgrounds too.
HOLO_OPACITY_HLSL = r"""
float3 n = normalize(N);
float fres = pow(1.0 - saturate(abs(dot(n, normalize(V)))), FresnelPower);
float3 g = abs(frac(P / GridSize) - 0.5);
float grid = 1.0 - smoothstep(0.0, GridWidth, 0.5 - max(g.x, max(g.y, g.z)));
float h = saturate(P.z / CatHeight);
float band = 1.0 - smoothstep(0.0, BandWidth, abs(h - frac(T * BandSpeed)));
float tick = floor(T * 18.0);
float flick = frac(sin(tick * 91.3458) * 47453.5453) > 0.9 ? 0.5 : 1.0;
return saturate((BaseOpacity + fres * 0.6 + grid * 0.25 + band * 0.5) * flick);
"""
JITTER_HLSL = r"""
// Short sideways jumps of horizontal slices (local Y), a few times per second.
float tick = floor(T * 14.0);
float slice = floor(P.z / 4.0);
float rnd = frac(sin(dot(float2(slice, tick), float2(12.9898, 78.233))) * 43758.5453);
float on = rnd > (1.0 - 0.06 * Amount) ? 1.0 : 0.0;
return float3(0.0, (frac(rnd * 37.0) - 0.5) * 6.0 * Amount * on, 0.0);
"""

holo = fresh_material("M_Cat_Hologram")
holo.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
holo.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
htex = expr(holo, "MaterialExpressionTextureSample", -1300, -250, texture=texture)
hpos = expr(holo, "MaterialExpressionPreSkinnedPosition", -1300, 0)
hnorm = expr(holo, "MaterialExpressionVertexNormalWS", -1300, 100)
hcam = expr(holo, "MaterialExpressionCameraVectorWS", -1300, 200)
htime = expr(holo, "MaterialExpressionTime", -1300, 300)
hp = {
    "Color": vector(holo, "HologramColor", (0.02, 0.85, 0.62), -1300, 400, "Hologram"),
    "Glow": scalar(holo, "Glow", 1.0, -1300, 560, "Hologram"),
    "FresnelPower": scalar(holo, "FresnelPower", 2.5, -1300, 640, "Hologram"),
    "GridSize": scalar(holo, "GridSize", 2.5, -1300, 720, "Hologram"),
    "GridWidth": scalar(holo, "GridWidth", 0.04, -1300, 800, "Hologram"),
    "CatHeight": scalar(holo, "CatHeight", 33.0, -1300, 880, "Hologram"),
    "BandWidth": scalar(holo, "BandWidth", 0.035, -1300, 960, "Hologram"),
    "BandSpeed": scalar(holo, "BandSpeed", 0.45, -1300, 1040, "Hologram"),
}
holo_node = custom(holo, HOLO_HLSL, ["C", "P", "N", "V", "T"] + list(hp), -700, 0)
wire(htex, holo_node, "C", "RGB")
# Pre-skinned position only exists in the vertex shader: pass it to the pixel shader.
hpos_ps = expr(holo, "MaterialExpressionVertexInterpolator", -1000, 0)
wire(hpos, hpos_ps, "VS")
wire(hpos_ps, holo_node, "P")
wire(hnorm, holo_node, "N")
wire(hcam, holo_node, "V")
wire(htime, holo_node, "T")
for name, node in hp.items():
    wire(node, holo_node, name)
hout, hpin = exposure_neutral(holo, holo_node, -350, 0)
mel.connect_material_property(hout, hpin, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
base_opacity = scalar(holo, "BaseOpacity", 0.3, -1300, 1120, "Hologram")
opacity = custom(holo, HOLO_OPACITY_HLSL, ["P", "N", "V", "T", "BaseOpacity", "FresnelPower", "GridSize",
                                           "GridWidth", "CatHeight", "BandWidth", "BandSpeed"], -700, 300)
opacity.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
wire(hpos_ps, opacity, "P")
wire(hnorm, opacity, "N")
wire(hcam, opacity, "V")
wire(htime, opacity, "T")
wire(base_opacity, opacity, "BaseOpacity")
for name in ("FresnelPower", "GridSize", "GridWidth", "CatHeight", "BandWidth", "BandSpeed"):
    wire(hp[name], opacity, name)
mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
amount = scalar(holo, "GlitchAmount", 1.0, -1300, 1200, "Hologram")
jitter = custom(holo, JITTER_HLSL, ["P", "T", "Amount"], -700, 500)
wire(hpos, jitter, "P")
wire(htime, jitter, "T")
wire(amount, jitter, "Amount")
to_world = expr(holo, "MaterialExpressionTransform", -400, 500,
                transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
wire(jitter, to_world, "")
mel.connect_material_property(to_world, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
mel.recompile_material(holo)
eal.save_loaded_asset(holo)
log("M_Cat_Hologram built")

# ---------------------------------------------------------------- default material of SK_Cat
mesh = unreal.load_asset(f"{DEST}/SK_Cat")
slots = [unreal.SkeletalMaterial(material_interface=toon, material_slot_name=s.get_editor_property("material_slot_name"))
         for s in mesh.get_editor_property("materials")]
mesh.modify()
mesh.set_editor_property("materials", slots)
if not eal.save_loaded_asset(mesh, only_if_is_dirty=False):
    raise RuntimeError("could not save SK_Cat")
if not all(s.get_editor_property("material_interface") == toon for s in mesh.get_editor_property("materials")):
    raise RuntimeError("SK_Cat does not use M_Cat_Toon")
log("SK_Cat default material -> M_Cat_Toon")
log("DONE")
