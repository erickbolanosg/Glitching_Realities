"""Play-in-editor test for BP_Cat: toon look, walking, Q to the hologram look and back.

Q is pressed through the OS exactly like the keyboard, but only while the Unreal Editor window is
in front, so keys never reach another program. Windows does not always give the game viewport
keyboard focus in an automated run; when the key does not arrive, the log says so and the test
calls ToggleGlitchState (the same event Q fires). Walking is driven with AddMovementInput.
Run (UE 5.8.4, editor GUI; a path without spaces works best for -ExecCmds):
  UnrealEditor.exe Glitching_Realities.uproject -ExecCmds="py <abs path>/play_test_cat.py"
Results: Saved/Logs/CatTest.txt and Saved/Screenshots/WindowsEditor/CatTest_*.png
"""
import ctypes
import os
from ctypes import wintypes

import unreal

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
LOG = open(os.path.join(PROJECT, "Saved", "Logs", "CatTest.txt"), "w", encoding="utf-8")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
state = {"t": 0.0, "pie": None, "shots": 0}

# ---------------------------------------------------------------- OS keyboard
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32")
VK = {"Q": 0x51}


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class _U(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _U)]


def editor_in_front():
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(pid))
    return pid.value == kernel32.GetCurrentProcessId()


def key(name, up=False):
    if not editor_in_front():
        log(f"SKIPPED key {name} {'up' if up else 'down'}: Unreal is not the foreground window")
        return False
    inp = INPUT(type=1, u=_U(ki=KEYBDINPUT(wVk=VK[name], wScan=user32.MapVirtualKeyW(VK[name], 0),
                                           dwFlags=0x0002 if up else 0, time=0, dwExtraInfo=0)))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    return True


# ---------------------------------------------------------------- helpers
def log(*a):
    LOG.write(f"[{state['pie'] or 0:6.1f}] " + " ".join(str(x) for x in a) + "\n")
    LOG.flush()


def world_objects():
    world = ues.get_game_world()
    if not world:
        return None, None
    return unreal.GameplayStatics.get_player_pawn(world, 0), unreal.GameplayStatics.get_player_controller(world, 0)


def report(pawn, label):
    mesh = pawn.get_editor_property("mesh")
    anim = mesh.get_anim_instance()
    mat = mesh.get_material(0)
    log(label, "| bIsGlitched", pawn.get_editor_property("bIsGlitched"),
        "| bCanSwitch", pawn.get_editor_property("bCanSwitch"),
        "| material", mat.get_name() if mat else None,
        "| speed", round(pawn.get_velocity().length(), 1),
        "| WalkAlpha", round(anim.get_editor_property("WalkAlpha"), 2) if anim else None,
        "| WalkPhase", round(anim.get_editor_property("WalkPhase"), 2) if anim else None)


def press_q(pawn):
    """Real Q through the OS; if the game did not get it (keyboard focus), call the same event."""
    before = pawn.get_editor_property("bIsGlitched")
    can = pawn.get_editor_property("bCanSwitch")
    sent = key("Q") and key("Q", up=True)
    state["q_check"] = (before, can, sent)


def check_q(pawn):
    before, can, sent = state.pop("q_check")
    now = pawn.get_editor_property("bIsGlitched")
    if not can:
        log("Q during cooldown:", "ignored as expected" if now == before else "CHANGED (unexpected)")
    elif now != before:
        log("Q key switched the look (real key press)")
    else:
        log("Q key did not reach the game (keyboard focus); calling ToggleGlitchState directly")
        pawn.call_method("ToggleGlitchState")


def shot(name):
    state["shots"] += 1
    unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, f"CatTest_{state['shots']}_{name}.png")


PLAN = [
    (39.0, "report:spawned (toon)"), (40.0, "frame"), (41.0, "shot:toon_idle"),
    # Walk to the right of the screen (side view) by driving movement directly.
    (41.3, "direct_on"), (42.3, "report:toon walking"), (42.4, "shot:toon_walking"), (42.8, "direct_off"),
    (43.5, "q"), (44.2, "check_q"), (44.4, "report:after Q (hologram expected)"), (44.8, "shot:hologram_idle"),
    (45.0, "q"), (45.5, "check_q"),                                  # still inside the 3 s cooldown
    (45.8, "direct_on"), (46.8, "report:hologram walking"), (46.9, "shot:hologram_walking"), (47.3, "direct_off"),
    # Game time can lag behind real time while shaders compile: wait well past the 3 s cooldown.
    (53.0, "report:cooldown over? (bCanSwitch should be True)"),
    (53.5, "q"), (54.2, "check_q"), (54.5, "report:after Q (toon expected)"), (54.9, "shot:toon_again"),
    (56.5, "quit"),
]


def tick(dt):
    state["t"] += dt
    if state["pie"] is None:
        if state["t"] > 8.0:
            les.editor_request_begin_play()
            state["pie"] = 0.0
        return
    state["pie"] += dt
    pawn, pc = world_objects()
    if state.get("direct") and pawn and pc:
        yaw = pc.get_control_rotation().yaw + 90  # same direction D should walk
        pawn.add_movement_input(unreal.MathLibrary.get_forward_vector(unreal.Rotator(0, 0, yaw)), 1.0, True)
    while PLAN and state["pie"] >= PLAN[0][0]:
        _, action = PLAN.pop(0)
        try:
            if action == "frame" and pawn and pc:
                # Camera in front-left of the cat, looking a little down, to see the face.
                pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=pawn.get_actor_rotation().yaw + 150))
            elif action == "q" and pawn:
                press_q(pawn)
            elif action == "check_q" and pawn:
                check_q(pawn)
            elif action.startswith("shot:"):
                shot(action[5:])
            elif action.startswith("down:"):
                key(action[5:])
            elif action.startswith("up:"):
                key(action[3:], up=True)
            elif action in ("direct_on", "direct_off"):
                state["direct"] = action == "direct_on"
            elif action.startswith("report:") and pawn:
                report(pawn, action[7:])
            elif action == "quit":
                unreal.unregister_slate_post_tick_callback(state["handle"])
                les.editor_request_end_play()
                unreal.SystemLibrary.quit_editor()
        except Exception as e:
            log("ERROR in", action, repr(e))


state["handle"] = unreal.register_slate_post_tick_callback(tick)
