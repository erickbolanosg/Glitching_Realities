"""Clean the Tripo cat, fit a quadruped rig, and export the SourceArt set.

Run with Blender:
  blender --background --python Tools/Python/build_cat_assets.py
"""
import os
import math
import shutil

import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

SRC = r"C:\Users\Erick\Downloads\tripo_convert_2bc3b879-dd0f-4e13-8787-038a0c4b5c7c\tripo_convert_2bc3b879-dd0f-4e13-8787-038a0c4b5c7c.fbx"
REF = r"C:\Users\Erick\AppData\Local\Temp\glitchcat-refs\chubby1.png"
OUT = r"C:\Users\Erick\Projects\Glitching_Realities\SourceArt\Characters\Cat"
ANIM = os.path.join(OUT, "Animations")
PREVIEW = r"C:\Users\Erick\Projects\Glitching_Realities\Tools\Python\_cat_preview"
BODY_LENGTH = 0.45  # meters, without the tail. FBX_SCALE_ALL writes this as 45 cm.

os.makedirs(ANIM, exist_ok=True)
os.makedirs(PREVIEW, exist_ok=True)


def write_png(path, rgb):
    img = bpy.data.images.new(os.path.basename(path), 1024, 1024, alpha=False)
    color = (rgb[0], rgb[1], rgb[2], 1.0)
    img.pixels.foreach_set(color * (1024 * 1024))
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


def material(name, image):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    bsdf.inputs["Roughness"].default_value = 0.72
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def clean_mesh(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    parts.sort(key=lambda o: len(o.data.polygons), reverse=True)
    body = parts[0]
    eyes = []
    for part in parts[1:]:
        dims = part.dimensions
        thin = min(dims) < 0.015 and len(part.data.polygons) < 400
        if thin:
            print("removed stray island", len(part.data.polygons), tuple(round(v, 4) for v in dims))
            bpy.data.objects.remove(part, do_unlink=True)
        else:
            eyes.append(part)
            print("kept eye island", len(part.data.polygons))

    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    return body, eyes


def shave_back(body, tail_base):
    me = body.data
    xs = [v.co.x for v in me.vertices]
    x0, x1 = min(xs), max(xs)
    x_lo = tail_base + 0.03
    x_hi = x0 + (x1 - x0) * 0.72
    bins = 24
    span = max(1e-6, x_hi - x_lo)
    tops = []
    for i in range(bins):
        a = x_lo + span * i / bins
        b = a + span / bins
        slab = [v.co.z for v in me.vertices if a <= v.co.x < b and abs(v.co.y) < 0.08]
        if len(slab) < 6:
            tops.append(None)
            continue
        slab.sort()
        tops.append(slab[int(len(slab) * 0.75)])
    known = [t for t in tops if t is not None]
    if not known:
        return
    fallback = sum(known) / len(known)
    tops = [t if t is not None else fallback for t in tops]
    for _ in range(2):
        nxt = tops[:]
        for i in range(1, bins - 1):
            nxt[i] = (tops[i - 1] + tops[i] + tops[i + 1]) / 3.0
        tops = nxt
    moved = 0
    for v in me.vertices:
        if abs(v.co.y) > 0.07 or not (x_lo <= v.co.x <= x_hi):
            continue
        i = min(bins - 1, max(0, int((v.co.x - x_lo) / span * bins)))
        limit = tops[i] + 0.006
        if v.co.z > limit:
            v.co.z = limit
            moved += 1
    me.update()
    print("shaved back verts", moved)


def orient_forward(body, eyes):
    eye_pts = [Vector(v.co) for eye in eyes for v in eye.data.vertices]
    head = sum(eye_pts, Vector()) / len(eye_pts)
    tail = max(
        (Vector(v.co) for v in body.data.vertices),
        key=lambda co: (Vector((co.x, co.y, 0)) - Vector((head.x, head.y, 0))).length_squared,
    )
    direction = Vector((head.x - tail.x, head.y - tail.y, 0))
    angle = math.atan2(direction.y, direction.x)
    rot = Matrix.Rotation(-angle, 4, "Z")
    for obj in [body, *eyes]:
        for v in obj.data.vertices:
            v.co = rot @ v.co
        obj.data.update()
    print("yaw correction deg", round(math.degrees(angle), 2))


def scale_to_spec(body, eyes):
    verts = body.data.vertices
    xs = [v.co.x for v in verts]
    zs = [v.co.z for v in verts]
    x0, x1 = min(xs), max(xs)
    # Tail is the thin mass at the low-X end. Body starts where a cross-section gets wide.
    bins = 40
    width_at = []
    for i in range(bins):
        a = x0 + (x1 - x0) * i / bins
        b = a + (x1 - x0) / bins
        ys = [v.co.y for v in verts if a <= v.co.x < b]
        width_at.append(max(ys) - min(ys) if ys else 0)
    peak = max(width_at) or 1
    tail_base_i = 0
    for i, w in enumerate(width_at):
        if w > peak * 0.45:
            tail_base_i = i
            break
    tail_base_x = x0 + (x1 - x0) * tail_base_i / bins
    body_len = max(0.05, x1 - tail_base_x)
    factor = BODY_LENGTH / body_len
    print(f"body length {body_len:.3f} m -> scale {factor:.3f}, tail base x {tail_base_x:.3f}")
    for obj in [body, *eyes]:
        for v in obj.data.vertices:
            v.co *= factor
        obj.data.update()
    # Ground the paws and center the body on X/Y of the footprint.
    all_z = [v.co.z for obj in [body, *eyes] for v in obj.data.vertices]
    z_min = min(all_z)
    paw_z = z_min + 0.03 * factor
    paw_verts = [v.co for v in body.data.vertices if v.co.z < z_min + (max(all_z) - z_min) * 0.18]
    if not paw_verts:
        paw_verts = [v.co for v in body.data.vertices]
    cx = sum(v.x for v in paw_verts) / len(paw_verts)
    cy = sum(v.y for v in paw_verts) / len(paw_verts)
    for obj in [body, *eyes]:
        for v in obj.data.vertices:
            v.co.x -= cx
            v.co.y -= cy
            v.co.z -= z_min
        obj.data.update()
    zs = [v.co.z for v in body.data.vertices]
    xs = [v.co.x for v in body.data.vertices]
    print(f"scaled size x {max(xs)-min(xs):.3f} z {max(zs)-min(zs):.3f}")
    return tail_base_x * factor - cx


def kmeans(points, k, iters=12):
    centers = [points[int(i * (len(points) - 1) / max(1, k - 1))] for i in range(k)]
    groups = [[] for _ in range(k)]
    for _ in range(iters):
        groups = [[] for _ in range(k)]
        for p in points:
            j = min(range(k), key=lambda n: (p - centers[n]).length_squared)
            groups[j].append(p)
        for n in range(k):
            if groups[n]:
                centers[n] = sum(groups[n], Vector()) / len(groups[n])
    return centers, groups


def add_bone(arm, name, head, tail, parent, roll):
    bone = arm.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    if (tail - head).length < 0.004:
        bone.tail = head + Vector((0, 0, 0.01))
    bone.align_roll(roll)
    bone.use_deform = True
    if parent:
        bone.parent = parent
    return bone


def build_rig(body):
    vs = [Vector(v.co) for v in body.data.vertices]
    z_max = max(v.z for v in vs)
    z_min = min(v.z for v in vs)
    height = max(0.001, z_max - z_min)
    low = [v for v in vs if v.z <= z_min + height * 0.14]
    remaining = list(low)
    clusters = []
    while remaining and len(clusters) < 4:
        seed = min(remaining, key=lambda v: (v.z, -abs(v.y)))
        group = [v for v in remaining if (Vector(v) - Vector(seed)).length <= 0.055]
        if len(group) < 4:
            remaining = [v for v in remaining if v not in group]
            continue
        clusters.append(sum((Vector(v) for v in group), Vector()) / len(group))
        grouped = set(map(id, group))
        remaining = [v for v in remaining if id(v) not in grouped]
    clusters.sort(key=lambda c: c.x)
    if len(clusters) < 4:
        raise RuntimeError(f"expected 4 paws, found {len(clusters)}: {clusters}")
    hind = sorted(clusters[:2], key=lambda c: c.y)
    front = sorted(clusters[2:], key=lambda c: c.y)
    paws = {"hind_r": hind[0], "hind_l": hind[1], "front_r": front[0], "front_l": front[1]}
    print("paws", {k: tuple(round(v, 3) for v in c) for k, c in paws.items()})

    def slab(x, radius=0.03):
        return [v for v in vs if abs(v.x - x) < radius]

    def inside_point(x, y_target, z_bias):
        pts = slab(x, 0.035) or vs
        ys = sorted(v.y for v in pts)
        zs = sorted(v.z for v in pts)
        y = ys[len(ys) // 2]
        y = y * 0.25 + y_target * 0.15
        z = zs[int(len(zs) * z_bias)]
        return Vector((x, y, z))

    hip_x = (paws["hind_l"].x + paws["hind_r"].x) / 2
    chest_x = (paws["front_l"].x + paws["front_r"].x) / 2
    pelvis = inside_point(hip_x, 0, 0.72)
    chest = inside_point(chest_x, 0, 0.7)
    spine_a = pelvis.lerp(chest, 0.38)
    spine_b = pelvis.lerp(chest, 0.7)
    head_pts = [v for v in vs if v.x > chest_x + 0.04]
    if not head_pts:
        head_pts = vs
    head_center = sum(head_pts, Vector()) / len(head_pts)
    nose_x = max(v.x for v in vs)
    neck = inside_point((chest_x + head_center.x) * 0.5, 0, 0.62)
    head = Vector((head_center.x, 0, head_center.z))
    nose = Vector((nose_x * 0.92, 0, head.z * 0.92))
    jaw = Vector((nose.x * 0.98, 0, min(v.z for v in head_pts) + 0.01))

    tail_pts = [v for v in vs if v.x < hip_x - 0.01 and v.z > height * 0.35]
    tail_x1 = min(v.x for v in vs)
    tail_chain = []
    if tail_pts:
        for i in range(5):
            x = hip_x + (tail_x1 - hip_x) * (i / 4)
            col = [v for v in tail_pts if abs(v.x - x) < 0.03] or tail_pts
            c = sum(col, Vector()) / len(col)
            tail_chain.append(Vector((c.x, c.y * 0.2, c.z)))
    else:
        tail_chain = [pelvis + Vector((-(i * 0.04), 0, 0.02)) for i in range(5)]

    arm_data = bpy.data.armatures.new("SK_Cat")
    arm_obj = bpy.data.objects.new("SK_Cat", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    roll = Vector((0, 1, 0))
    root_head = Vector((0, 0, 0))
    root = add_bone(arm_data, "root", root_head, root_head + Vector((0, 0, 0.02)), None, roll)
    pelvis_b = add_bone(arm_data, "pelvis", pelvis, spine_a, root, roll)
    sp1 = add_bone(arm_data, "spine_01", spine_a, spine_b, pelvis_b, roll)
    sp2 = add_bone(arm_data, "spine_02", spine_b, chest, sp1, roll)
    chest_b = add_bone(arm_data, "chest", chest, neck, sp2, roll)
    neck_b = add_bone(arm_data, "neck", neck, head, chest_b, roll)
    head_b = add_bone(arm_data, "head", head, nose, neck_b, roll)
    add_bone(arm_data, "jaw", jaw, jaw + Vector((0.02, 0, 0)), head_b, roll)

    parent = pelvis_b
    for i in range(4):
        parent = add_bone(arm_data, f"tail_{i+1:02d}", tail_chain[i], tail_chain[i + 1], parent, roll)

    def leg(prefix, side, paw, hip_z_bias, knee_sign):
        hip = Vector((paw.x, paw.y * 0.55, pelvis.z * hip_z_bias))
        # Keep the hip inside the body, above the paw.
        hip.z = max(hip.z, paw.z + 0.08)
        knee = Vector((paw.x + 0.012 * knee_sign, paw.y * 0.85, (hip.z + paw.z) * 0.48))
        foot = Vector((paw.x, paw.y, max(0.005, paw.z)))
        thigh = add_bone(arm_data, f"{prefix}_thigh_{side}", hip, knee, pelvis_b if prefix == "hind" else chest_b, roll)
        shin = add_bone(arm_data, f"{prefix}_shin_{side}", knee, foot, thigh, roll)
        add_bone(arm_data, f"{prefix}_paw_{side}", foot, foot + Vector((0.02, 0, 0)), shin, roll)

    leg("hind", "l", paws["hind_l"], 0.95, 1)
    leg("hind", "r", paws["hind_r"], 0.95, 1)
    leg("front", "l", paws["front_l"], 0.85, -1)
    leg("front", "r", paws["front_r"], 0.85, -1)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def bind(meshes, arm):
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")


def key(pb, frame, rot, loc=None):
    pb.rotation_mode = "XYZ"
    pb.rotation_euler = Euler(tuple(math.radians(v) for v in rot))
    pb.keyframe_insert("rotation_euler", frame=frame)
    if loc is not None:
        pb.location = Vector(loc)
        pb.keyframe_insert("location", frame=frame)


def new_action(arm, name):
    if arm.animation_data is None:
        arm.animation_data_create()
    action = bpy.data.actions.new(name)
    arm.animation_data.action = action
    try:
        slot = arm.animation_data.action_slot
        if slot is None and action.slots:
            arm.animation_data.action_slot = action.slots[0]
    except Exception:
        pass
    return action


def pose_bones(arm):
    return {pb.name: pb for pb in arm.pose.bones}


def clear_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = Euler()
        pb.location = Vector()


def build_animations(arm):
    scene = bpy.context.scene
    scene.render.fps = 30
    P = lambda *a: pose_bones(arm)

    def legs_idle(frame, breath):
        pb = P()
        key(pb["spine_01"], frame, (breath, 0, 0))
        key(pb["spine_02"], frame, (breath * 0.6, 0, 0))
        key(pb["chest"], frame, (breath * 0.3, 0, 0))
        key(pb["tail_01"], frame, (0, 0, breath * 4))
        key(pb["tail_02"], frame, (0, 0, breath * 6))
        key(pb["tail_03"], frame, (0, 0, breath * 5))

    def loop_breath(name, seconds, amount):
        frames = int(seconds * 30)
        new_action(arm, name)
        clear_pose(arm)
        for i, f in enumerate((1, frames // 2, frames)):
            sign = (0, 1, 0)[i]
            legs_idle(f, amount * sign)
        return name

    loop_breath("A_Cat_Idle", 3.5, 3)

    # Sit: drop pelvis, fold hind legs, 5 s.
    new_action(arm, "A_Cat_IdleSit")
    clear_pose(arm)
    pb = P()
    for f in (1,):
        key(pb["pelvis"], f, (0, 0, 0), (0, 0, 0))
        for side in ("l", "r"):
            key(pb[f"hind_thigh_{side}"], f, (0, 0, 0))
            key(pb[f"hind_shin_{side}"], f, (0, 0, 0))
    for f in (70, 150):
        key(pb["pelvis"], f, (-12, 0, 0), (0, 0, -0.03))
        for side in ("l", "r"):
            key(pb[f"hind_thigh_{side}"], f, (-55, 0, 0))
            key(pb[f"hind_shin_{side}"], f, (70, 0, 0))
            key(pb[f"front_thigh_{side}"], f, (12, 0, 0))
        key(pb["tail_01"], f, (25, 0, 0))

    new_action(arm, "A_Cat_IdleLick")
    clear_pose(arm)
    pb = P()
    key(pb["pelvis"], 1, (0, 0, 0), (0, 0, 0))
    key(pb["head"], 1, (0, 0, 0))
    key(pb["jaw"], 1, (0, 0, 0))
    for f, head_x, jaw_x in ((40, 28, 12), (80, 18, 22), (110, 30, 8), (150, 20, 0)):
        key(pb["pelvis"], f, (-8, 0, 0), (0, 0, -0.02))
        key(pb["neck"], f, (10, 0, 8))
        key(pb["head"], f, (head_x, 8, 12))
        key(pb["jaw"], f, (jaw_x, 0, 0))
        key(pb["front_thigh_l"], f, (-20, 0, -15))

    def gait(name, seconds, lift, stride):
        frames = max(2, int(round(seconds * 30)))
        new_action(arm, name)
        clear_pose(arm)
        # Diagonal pairs. phase 0..1 across the cycle. Last frame matches first.
        pairs = (("front_l", "hind_r", 0.0), ("front_r", "hind_l", 0.5))
        for f in range(1, frames + 1):
            t = (f - 1) / frames
            for a, b, offset in pairs:
                phase = (t + offset) % 1.0
                swing = math.sin(phase * math.tau)
                lift_amt = max(0.0, swing) * lift
                for label, _sign in ((a, 1), (b, 1)):
                    prefix, side = label.split("_")
                    key(P()[f"{prefix}_thigh_{side}"], f, (stride * math.cos(phase * math.tau), 0, 0))
                    key(P()[f"{prefix}_shin_{side}"], f, (-lift_amt, 0, 0))
                    key(P()[f"{prefix}_paw_{side}"], f, (lift_amt * 0.4, 0, 0))
            key(P()["spine_01"], f, (2 * math.sin(t * math.tau), 0, 3 * math.sin(t * math.tau)))
            key(P()["tail_01"], f, (0, 0, 8 * math.sin(t * math.tau)))
            key(P()["tail_02"], f, (0, 0, 10 * math.sin(t * math.tau + 0.4)))
        # close the loop
        return name

    gait("A_Cat_Walk", 1.0, 28, 22)
    gait("A_Cat_Run", 0.6, 40, 32)
    gait("A_Cat_CrouchWalk", 1.2, 16, 14)

    # Crouch walk should stay low. Overlay pelvis drop on that action.
    arm.animation_data.action = bpy.data.actions["A_Cat_CrouchWalk"]
    frames = int(1.2 * 30)
    for f in range(1, frames + 1):
        key(P()["pelvis"], f, (8, 0, 0), (0, 0, -0.035))

    new_action(arm, "A_Cat_CrouchIdle")
    frames = 60
    for f in (1, 30, 60):
        breath = 2 if f == 30 else 0
        key(P()["pelvis"], f, (8 + breath, 0, 0), (0, 0, -0.035))
        for side in ("l", "r"):
            key(P()[f"front_thigh_{side}"], f, (18, 0, 0))
            key(P()[f"hind_thigh_{side}"], f, (-18, 0, 0))
            key(P()[f"front_shin_{side}"], f, (-20, 0, 0))
            key(P()[f"hind_shin_{side}"], f, (20, 0, 0))

    def oneshot(name, seconds, keys):
        new_action(arm, name)
        clear_pose(arm)
        end = int(seconds * 30)
        for frame, pose in keys:
            f = max(1, int(frame * end))
            for bone, rot in pose.items():
                loc = None
                if len(rot) == 2:
                    rot, loc = rot
                key(P()[bone], f, rot, loc)

    oneshot("A_Cat_JumpStart", 0.3, [
        (0.0, {"pelvis": ((8, 0, 0), (0, 0, -0.02)), "front_thigh_l": (20, 0, 0), "front_thigh_r": (20, 0, 0), "hind_thigh_l": (-25, 0, 0), "hind_thigh_r": (-25, 0, 0)}),
        (1.0, {"pelvis": ((-15, 0, 0), (0, 0, 0.04)), "front_thigh_l": (-30, 0, 0), "front_thigh_r": (-30, 0, 0), "hind_thigh_l": (20, 0, 0), "hind_thigh_r": (20, 0, 0)}),
    ])
    oneshot("A_Cat_JumpLoop", 0.5, [
        (0.0, {"pelvis": ((-10, 0, 0), (0, 0, 0.02)), "front_thigh_l": (-25, 0, 0), "front_thigh_r": (-25, 0, 0), "hind_thigh_l": (15, 0, 0), "hind_thigh_r": (15, 0, 0)}),
        (0.5, {"pelvis": ((-6, 0, 0), (0, 0, 0.02)), "spine_01": (6, 0, 0)}),
        (1.0, {"pelvis": ((-10, 0, 0), (0, 0, 0.02)), "front_thigh_l": (-25, 0, 0), "front_thigh_r": (-25, 0, 0), "hind_thigh_l": (15, 0, 0), "hind_thigh_r": (15, 0, 0)}),
    ])
    oneshot("A_Cat_Land", 0.3, [
        (0.0, {"pelvis": ((-8, 0, 0), (0, 0, 0.03))}),
        (0.45, {"pelvis": ((14, 0, 0), (0, 0, -0.03)), "front_shin_l": (-25, 0, 0), "front_shin_r": (-25, 0, 0)}),
        (1.0, {"pelvis": ((0, 0, 0), (0, 0, 0))}),
    ])
    oneshot("A_Cat_PawSwipe", 0.5, [
        (0.0, {"front_thigh_r": (0, 0, 0)}),
        (0.45, {"front_thigh_r": (-50, 0, -20), "front_shin_r": (-15, 0, 0), "spine_02": (0, 8, -8)}),
        (1.0, {"front_thigh_r": (0, 0, 0), "spine_02": (0, 0, 0)}),
    ])
    oneshot("A_Cat_Scratch", 0.8, [
        (0.0, {"front_thigh_l": (10, 0, 0), "front_thigh_r": (10, 0, 0)}),
        (0.25, {"front_thigh_l": (35, 0, 0), "front_shin_l": (-40, 0, 0), "front_thigh_r": (5, 0, 0)}),
        (0.5, {"front_thigh_r": (35, 0, 0), "front_shin_r": (-40, 0, 0), "front_thigh_l": (5, 0, 0)}),
        (0.75, {"front_thigh_l": (35, 0, 0), "front_shin_l": (-40, 0, 0)}),
        (1.0, {"front_thigh_l": (0, 0, 0), "front_thigh_r": (0, 0, 0)}),
    ])
    oneshot("A_Cat_Pounce", 0.8, [
        (0.0, {"pelvis": ((10, 0, 0), (0, 0, -0.02))}),
        (0.35, {"pelvis": ((-20, 0, 0), (0, 0, 0.02)), "front_thigh_l": (-45, 0, 0), "front_thigh_r": (-45, 0, 0), "hind_thigh_l": (25, 0, 0), "hind_thigh_r": (25, 0, 0)}),
        (1.0, {"pelvis": ((6, 0, 0), (0, 0, 0)), "front_thigh_l": (10, 0, 0), "front_thigh_r": (10, 0, 0)}),
    ])
    oneshot("A_Cat_Meow", 1.0, [
        (0.0, {"head": (0, 0, 0), "jaw": (0, 0, 0)}),
        (0.4, {"neck": (-12, 0, 0), "head": (-18, 0, 0), "jaw": (24, 0, 0)}),
        (0.7, {"jaw": (8, 0, 0), "head": (-10, 0, 0)}),
        (1.0, {"head": (0, 0, 0), "jaw": (0, 0, 0), "neck": (0, 0, 0)}),
    ])
    oneshot("A_Cat_GlitchTwitch", 0.8, [
        (0.0, {"spine_01": (0, 0, 0)}),
        (0.15, {"spine_01": (0, 0, 14), "head": (8, 0, -10), "tail_01": (0, 0, 20)}),
        (0.3, {"spine_01": (0, 0, -16), "spine_02": (10, 0, 0), "head": (-6, 0, 12)}),
        (0.5, {"spine_01": (12, 0, 8), "chest": (0, 0, -10), "tail_02": (0, 0, -18)}),
        (0.7, {"spine_02": (-8, 0, 14), "head": (10, 0, -8)}),
        (1.0, {"spine_01": (0, 0, 0), "spine_02": (0, 0, 0), "head": (0, 0, 0), "chest": (0, 0, 0)}),
    ])
    oneshot("A_Cat_Caught", 1.0, [
        (0.0, {"spine_01": (0, 0, 0)}),
        (0.35, {"spine_01": (18, 0, 0), "spine_02": (12, 0, 0), "head": (20, 0, 0), "pelvis": ((0, 0, 0), (0, 0, -0.015))}),
        (1.0, {"spine_01": (8, 0, 0), "head": (10, 0, 0)}),
    ])
    oneshot("A_Cat_ConvertCast", 1.5, [
        (0.0, {"spine_02": (0, 0, 0), "tail_01": (0, 0, 0)}),
        (0.45, {"spine_01": (-14, 0, 0), "spine_02": (-18, 0, 0), "tail_01": (-40, 0, 0), "tail_02": (-25, 0, 0), "head": (-8, 0, 0)}),
        (1.0, {"spine_01": (-8, 0, 0), "tail_01": (-20, 0, 0)}),
    ])


def export_fbx(path, arm, meshes, anim):
    bpy.ops.object.select_all(action="DESELECT")
    for m in meshes:
        m.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    if anim:
        arm.animation_data.action = bpy.data.actions[anim]
        scene_frame = 1
        bpy.context.scene.frame_set(scene_frame)
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False,
        bake_anim=bool(anim),
        bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0.0,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y",
        axis_up="Z",
        mesh_smooth_type="FACE",
        path_mode="COPY",
        embed_textures=True,
    )
    print("exported", path)


def replace_eyes(eyes):
    for eye in eyes:
        mod = eye.modifiers.new("Decimate", "DECIMATE")
        mod.ratio = 0.2
        bpy.context.view_layer.objects.active = eye
        bpy.ops.object.modifier_apply(modifier="Decimate")
        print("decimated eye faces", len(eye.data.polygons))
    return eyes


def render_views(arm, meshes, tag):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    world = bpy.data.worlds.new("PreviewWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.8, 0.8, 0.8, 1)
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    center = Vector((0.05, 0, 0.12))
    dist = 0.9
    arm.data.display_type = "OCTAHEDRAL"
    arm.hide_render = True
    scene.frame_set(1)
    if tag == "walk":
        arm.animation_data.action = bpy.data.actions["A_Cat_Walk"]
        scene.frame_set(8)
    if tag == "bend":
        new_action(arm, "BendTest")
        for name in ("front_thigh_l", "front_thigh_r", "hind_thigh_l", "hind_thigh_r"):
            key(pose_bones(arm)[name], 1, (35, 0, 0))
        scene.frame_set(1)
    shots = {
        "threequarter": center + Vector((dist, -dist, dist * 0.45)),
        "side": center + Vector((0, -dist * 1.15, 0.05)),
    }
    for shot, loc in shots.items():
        cam.location = loc
        cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(PREVIEW, f"{tag}_{shot}.png")
        bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=SRC)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # clean_mesh expects the joined? separate works on the active mesh. Join first if several.
    if len(meshes) > 1:
        bpy.ops.object.join()
    body, eyes = clean_mesh(bpy.context.view_layer.objects.active)
    orient_forward(body, eyes)
    tail_base = scale_to_spec(body, eyes)
    shave_back(body, tail_base)
    eyes = replace_eyes(eyes)

    body_img = write_png(os.path.join(OUT, "T_Cat_D.png"), (0.04, 0.04, 0.045))
    eye_img = write_png(os.path.join(OUT, "T_Cat_Eye.png"), (0.82, 0.84, 0.86))
    body.data.materials.clear()
    body.data.materials.append(material("M_Cat_Body", body_img))
    for eye in eyes:
        eye.data.materials.clear()
        eye.data.materials.append(material("M_Cat_Eye", eye_img))

    arm = build_rig(body)
    bind([body, *eyes], arm)
    tris = sum(len(p.vertices) - 2 for p in body.data.polygons for _ in [0] if len(p.vertices) >= 3)
    # polygon triangle count
    tri_count = 0
    for p in body.data.polygons:
        tri_count += max(1, len(p.vertices) - 2)
    for eye in eyes:
        for p in eye.data.polygons:
            tri_count += max(1, len(p.vertices) - 2)
    print("TRIANGLES", tri_count)
    build_animations(arm)
    render_views(arm, [body, *eyes], "rest")
    render_views(arm, [body, *eyes], "walk")
    render_views(arm, [body, *eyes], "bend")
    export_fbx(os.path.join(OUT, "SK_Cat.fbx"), arm, [body, *eyes], None)
    for action in list(bpy.data.actions):
        if action.name.startswith("A_Cat_"):
            export_fbx(os.path.join(ANIM, action.name + ".fbx"), arm, [body, *eyes], action.name)
    if os.path.isfile(REF):
        shutil.copyfile(REF, os.path.join(OUT, "Ref_Cat_Approved.png"))
    zs = [v.co.z for v in body.data.vertices]
    xs = [v.co.x for v in body.data.vertices]
    print(f"FINAL meters x {max(xs)-min(xs):.3f} height {max(zs):.3f} tris {tri_count}")


if __name__ == "__main__":
    main()
