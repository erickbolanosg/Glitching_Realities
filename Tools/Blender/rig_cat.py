"""Rig the original Tripo cat and give it a walk cycle. The mesh shape is never edited.

Run (Blender 5.3):
  blender --background --factory-startup --python Tools/Blender/rig_cat.py -- "<source.fbx>" "<out dir>"

Output in <out dir>:
  SK_Cat.fbx    mesh + skeleton + the walk cycle (one take: A_Cat_Walk), ready for Unreal
  SK_Cat.blend  editable rig + animation (open it in Blender to tweak and re-export)

What happens to the mesh: it is only rotated to face +X, moved so its feet sit on the origin,
and uniformly scaled to BODY_LENGTH (nose to rump, tail excluded). No vertex is added, removed
or reshaped.

Skeleton (armature object is called "root", so Unreal's root bone is "root"):
  pelvis > spine_01 > spine_02 > spine_03 > neck > head
  pelvis > tail_01..tail_05
  pelvis > hind_thigh/shin/foot/toe_{l,r}
  spine_03 > front_scapula/upper/lower/paw_{l,r}
Left is +Y (cat faces +X).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = args[0], args[1]
BODY_LENGTH = 0.45          # m, nose to rump (GDD: ~45 cm without the tail)
FPS = 30
CYCLE = 16                  # frames per walk cycle (0.53 s)
STANCE = 0.5                # fraction of the cycle a paw is on the ground
SWING = math.radians(22)    # leg swing, forward/back from vertical
LIFT_BEND = math.radians(55)  # lower leg fold while the paw is in the air
# Lateral-sequence walk: left hind, left front, right hind, right front.
PHASE = {"hind_l": 0.0, "front_l": 0.25, "hind_r": 0.5, "front_r": 0.75}


def log(*a):
    print("RIG:", *a)


# ---------------------------------------------------------------- load + align
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
mesh = next(o for o in bpy.data.objects if o.type == "MESH")
mesh.name = "SK_Cat"
mesh.data.transform(mesh.matrix_world)
mesh.matrix_world = Matrix.Identity(4)
verts = [v.co.copy() for v in mesh.data.vertices]
n = len(verts)
cx = sum(v.x for v in verts) / n
cy = sum(v.y for v in verts) / n
sxx = sum((v.x - cx) ** 2 for v in verts) / n
syy = sum((v.y - cy) ** 2 for v in verts) / n
sxy = sum((v.x - cx) * (v.y - cy) for v in verts) / n
ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
axis = Vector((math.cos(ang), math.sin(ang), 0))
# The head end is the one with more vertices (eyes, ears, face detail); the tail end is sparse.
ahead = sum(1 for v in verts if (v - Vector((cx, cy, 0))).dot(axis) > 0)
if ahead < n / 2:
    axis = -axis
yaw = math.atan2(axis.y, axis.x)
mesh.data.transform(Matrix.Rotation(-yaw, 4, "Z") @ Matrix.Translation(Vector((-cx, -cy, 0))))
P = [v.co for v in mesh.data.vertices]


def xs_slice(a, b):
    return [p for p in P if a <= p.x < b]


xmin, xmax = min(p.x for p in P), max(p.x for p in P)
zmax = max(p.z for p in P)
# Rump = first slice from the back that reaches down towards the belly; the tail hangs high.
rump_x = xmin
step = (xmax - xmin) / 80
x = xmin
while x < xmax:
    sl = xs_slice(x, x + step)
    if sl and min(p.z for p in sl) < zmax * 0.45:
        rump_x = x
        break
    x += step
scale = BODY_LENGTH / (xmax - rump_x)
feet_z = min(p.z for p in P)
mesh.data.transform(Matrix.Scale(scale, 4) @ Matrix.Translation(Vector((0, 0, -feet_z))))
P = [v.co for v in mesh.data.vertices]
xmin, xmax = min(p.x for p in P), max(p.x for p in P)
rump_x = (rump_x) * scale
height = max(p.z for p in P)
log(f"scale {scale:.4f}  body {xmax - rump_x:.3f} m  total length {xmax - xmin:.3f} m  height {height:.3f} m")

# Paws: lowest vertices, split front/back and left/right.
low = [p for p in P if p.z < height * 0.05]
mid_x = (min(p.x for p in low) + max(p.x for p in low)) / 2
paw = {}
for name, fx, side in (("front_l", 1, 1), ("front_r", 1, -1), ("hind_l", -1, 1), ("hind_r", -1, -1)):
    pts = [p for p in low if (p.x - mid_x) * fx > 0 and p.y * side > 0]
    c = sum(pts, Vector()) / len(pts)
    paw[name] = Vector((c.x, c.y, 0.0))
center_x = (paw["front_l"].x + paw["hind_l"].x) / 2
# Put the origin under the middle of the four paws so the capsule is centered on the body.
mesh.data.transform(Matrix.Translation(Vector((-center_x, 0, 0))))
for k in paw:
    paw[k].x -= center_x
rump_x -= center_x
xmin -= center_x
xmax -= center_x
P = [v.co for v in mesh.data.vertices]


def body_profile(x0, half=0.04):
    """Lowest belly point (paws excluded) and highest back point around x0."""
    sl = [p for p in P if abs(p.x - x0) < half and p.z > 0.06]
    return min(p.z for p in sl), max(p.z for p in sl)


def spine_point(x0, frac=0.6):
    lo, hi = body_profile(x0)
    return Vector((x0, 0, lo + (hi - lo) * frac))


hind_x = (paw["hind_l"].x + paw["hind_r"].x) / 2
front_x = (paw["front_l"].x + paw["front_r"].x) / 2
belly_hind = body_profile(hind_x)[0]
belly_front = body_profile(front_x)[0]
log("paws", {k: tuple(round(c, 3) for c in v) for k, v in paw.items()}, "rump_x", round(rump_x, 3), "nose_x", round(xmax, 3))

# Tail: centroids of thin slices behind the rump.
tail_pts = [p for p in P if p.x < rump_x]
tail_chain = []
for i in range(6):
    t = i / 5
    x0 = rump_x + (xmin - rump_x) * t
    sl = [p for p in tail_pts if abs(p.x - x0) < 0.015] or [p for p in P if abs(p.x - x0) < 0.02]
    c = sum(sl, Vector()) / len(sl)
    tail_chain.append(Vector((x0 if i < 5 else xmin + 0.01, 0, c.z)))
tail_chain[0] = Vector((rump_x + 0.03, 0, tail_chain[0].z))

# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new("SKEL_Cat")
arm = bpy.data.objects.new("root", arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, connect=False):
    b = eb.new(name)
    b.head, b.tail = Vector(head), Vector(tail)
    if parent:
        b.parent = eb[parent]
        b.use_connect = connect
    b.align_roll(Vector((0, 0, 1)) if abs((b.tail - b.head).normalized().z) < 0.8 else Vector((1, 0, 0)))
    return b


# A straight spine from the hips to the shoulders (the low-poly back is too sparse to follow).
pelvis_p = spine_point(hind_x)
s3 = spine_point(front_x)
s1 = pelvis_p.lerp(s3, 0.33)
s2 = pelvis_p.lerp(s3, 0.66)
head_lo, head_hi = body_profile(xmax - 0.06, 0.03)
head_c = Vector((xmax - 0.06, 0, head_lo + (head_hi - head_lo) * 0.45))
neck_p = Vector((front_x + (xmax - front_x) * 0.35, 0, (s3.z + head_c.z) / 2))
bone("pelvis", pelvis_p, s1)
bone("spine_01", s1, s2, "pelvis", True)
bone("spine_02", s2, s3, "spine_01", True)
bone("spine_03", s3, neck_p, "spine_02", True)
bone("neck", neck_p, head_c, "spine_03", True)
bone("head", head_c, Vector((xmax, 0, head_c.z)), "neck", True)
bone("tail_01", tail_chain[0], tail_chain[1], "pelvis")
for i in range(2, 6):
    bone(f"tail_0{i}", tail_chain[i - 1], tail_chain[i], f"tail_0{i - 1}", True)

LEG = {}
for side, s in (("l", 1), ("r", -1)):
    hp, fp = paw[f"hind_{side}"], paw[f"front_{side}"]
    hy, fy = abs(hp.y), abs(fp.y)
    hip = Vector((hp.x + 0.02, s * hy * 0.8, belly_hind + 0.07))
    knee = Vector((hp.x + 0.035, s * hy, belly_hind * 0.75 + 0.02))
    hock = Vector((hp.x - 0.015, s * hy, 0.025))
    hball = Vector((hp.x + 0.005, s * hy, 0.008))
    htoe = Vector((hp.x + 0.03, s * hy, 0.004))
    bone(f"hind_thigh_{side}", hip, knee, "pelvis")
    bone(f"hind_shin_{side}", knee, hock, f"hind_thigh_{side}", True)
    bone(f"hind_foot_{side}", hock, hball, f"hind_shin_{side}", True)
    bone(f"hind_toe_{side}", hball, htoe, f"hind_foot_{side}", True)
    sc = Vector((fp.x - 0.03, s * fy * 0.45, s3.z - 0.02))
    shoulder = Vector((fp.x + 0.005, s * fy * 0.85, belly_front + 0.06))
    elbow = Vector((fp.x - 0.015, s * fy, belly_front * 0.7 + 0.015))
    wrist = Vector((fp.x + 0.005, s * fy, 0.022))
    ftoe = Vector((fp.x + 0.03, s * fy, 0.006))
    bone(f"front_scapula_{side}", sc, shoulder, "spine_03")
    bone(f"front_upper_{side}", shoulder, elbow, f"front_scapula_{side}", True)
    bone(f"front_lower_{side}", elbow, wrist, f"front_upper_{side}", True)
    bone(f"front_paw_{side}", wrist, ftoe, f"front_lower_{side}", True)
    LEG[f"hind_{side}"] = dict(chain=(f"hind_thigh_{side}", f"hind_shin_{side}"), end=hock.copy(), side=s,
                              pole=knee + Vector((0.15, 0, 0)), rest=hp.copy(), top=hip.z)
    LEG[f"front_{side}"] = dict(chain=(f"front_upper_{side}", f"front_lower_{side}"), end=wrist.copy(), side=s,
                               pole=elbow + Vector((-0.15, 0, 0)), rest=fp.copy(), top=shoulder.z)
bpy.ops.object.mode_set(mode="OBJECT")
DEFORM = [b.name for b in arm_data.bones]
log("bones", len(DEFORM), DEFORM)

# ---------------------------------------------------------------- skin weights
segs = {b.name: (arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in arm_data.bones}


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (a + ab * t - p).length


groups = {name: mesh.vertex_groups.new(name=name) for name in DEFORM}
for v in mesh.data.vertices:
    p = v.co
    cands = []
    for name, (a, b) in segs.items():
        if name.startswith(("hind_", "front_")) and "scapula" not in name:
            leg = LEG["hind_" + name[-1]] if name.startswith("hind") else LEG["front_" + name[-1]]
            if p.y * leg["side"] < 0.005 or p.z > leg["top"] + 0.01 or abs(p.x - leg["rest"].x) > 0.07:
                continue
        if name.startswith("tail") and p.x > rump_x + 0.04:
            continue
        if not name.startswith("tail") and p.x < rump_x - 0.03:
            continue
        if name in ("neck", "head") and p.x < front_x - 0.02:
            continue
        cands.append((seg_dist(p, a, b), name))
    cands.sort()
    best = cands[:3]
    ws = [(1.0 / (d + 0.004) ** 4, nm) for d, nm in best]
    total = sum(w for w, _ in ws)
    for w, nm in ws:
        if w / total > 0.02:
            groups[nm].add([v.index], w / total, "REPLACE")
mod = mesh.modifiers.new("Armature", "ARMATURE")
mod.object = arm
mesh.parent = arm

# ---------------------------------------------------------------- walk cycle (FK)
# Short, chubby legs look best swinging like pendulums: the upper bone swings forward/back, the
# lower bone folds to lift the paw during the swing, and the paw counter-rotates to stay flat.
# Leg bones point down with their local Z towards +X, so +rotation_euler.x swings forward.
scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start, scene.frame_end = 1, CYCLE + 1
CHAINS = {"hind_l": ("hind_thigh_l", "hind_shin_l", "hind_foot_l"),
          "hind_r": ("hind_thigh_r", "hind_shin_r", "hind_foot_r"),
          "front_l": ("front_upper_l", "front_lower_l", "front_paw_l"),
          "front_r": ("front_upper_r", "front_lower_r", "front_paw_r")}

arm.animation_data_create()
arm.animation_data.action = bpy.data.actions.new("A_Cat_Walk")
pb = arm.pose.bones
for b in pb:
    b.rotation_mode = "XYZ"
for f in range(1, CYCLE + 2):
    t = ((f - 1) % CYCLE) / CYCLE
    for leg, (upper, lower, foot) in CHAINS.items():
        u = (t + PHASE[leg]) % 1.0
        if u < STANCE:                                   # paw on the ground, leg sweeps back
            a = SWING * (1 - 2 * u / STANCE)
            bend = 0.0
        else:                                            # paw in the air, leg returns forward
            s = (u - STANCE) / (1 - STANCE)
            a = -SWING + 2 * SWING * (0.5 - 0.5 * math.cos(math.pi * s))
            bend = LIFT_BEND * math.sin(math.pi * s)
        pb[upper].rotation_euler = (a, 0, 0)
        pb[lower].rotation_euler = (-bend, 0, 0)
        pb[foot].rotation_euler = (-a * 0.8 + bend * 0.6, 0, 0)
        for name in (upper, lower, foot):
            pb[name].keyframe_insert("rotation_euler", frame=f)
    w = 2 * math.pi * t
    pb["pelvis"].location = (0, 0, 0.004 * math.cos(2 * w))      # bone-local Z is up: tiny bob
    pb["pelvis"].keyframe_insert("location", frame=f)
    pb["pelvis"].rotation_euler = (0, 0, math.radians(3) * math.sin(w))
    pb["spine_02"].rotation_euler = (0, 0, math.radians(-2.5) * math.sin(w))
    pb["neck"].rotation_euler = (math.radians(2) * math.sin(2 * w + 1.0), 0, math.radians(-2) * math.sin(w))
    pb["head"].rotation_euler = (math.radians(-2) * math.sin(2 * w + 1.0), 0, math.radians(2) * math.sin(w))
    for i in range(1, 6):
        pb[f"tail_0{i}"].rotation_euler = (math.radians(1.5 * i) * math.sin(2 * w - i * 0.5), 0,
                                          math.radians(4 + 2 * i) * math.sin(w - i * 0.6))
    for side, s in (("l", 1), ("r", -1)):
        u = (t + PHASE[f"front_{side}"]) % 1.0
        pb[f"front_scapula_{side}"].rotation_euler = (math.radians(6) * math.sin(2 * math.pi * u), 0, 0)
    for name in ("pelvis", "spine_02", "neck", "head", *[f"tail_0{i}" for i in range(1, 6)],
                 "front_scapula_l", "front_scapula_r"):
        pb[name].keyframe_insert("rotation_euler", frame=f)

arm.animation_data.action.name = "A_Cat_Walk"


def paw_x(leg, frame):
    scene.frame_set(frame)
    return (arm.matrix_world @ pb[CHAINS[leg][2]].tail).x


# Ground speed the walk implies at play rate 1: how far a planted paw moves back per second.
stance_frames = int(STANCE * CYCLE)
start = int(round((1 - PHASE["hind_l"]) % 1 * CYCLE)) + 1
travel = paw_x("hind_l", start) - paw_x("hind_l", start + stance_frames)
ANIM_SPEED_CM_S = travel / (stance_frames / FPS) * 100
log(f"walk: {CYCLE} frames @ {FPS} fps, paw travel {travel * 100:.1f} cm per step, "
    f"ground speed {ANIM_SPEED_CM_S:.1f} cm/s at play rate 1")

# ---------------------------------------------------------------- export
os.makedirs(OUT, exist_ok=True)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SK_Cat.blend"))
bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUT, "SK_Cat.fbx"),
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    add_leaf_bones=False,
    armature_nodetype="NULL",
    bake_anim=True,
    bake_anim_use_all_actions=False,
    bake_anim_use_nla_strips=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,
    apply_scale_options="FBX_SCALE_NONE",
    mesh_smooth_type="FACE",
    path_mode="COPY",
    embed_textures=True,
)
log("exported", os.path.join(OUT, "SK_Cat.fbx"))
