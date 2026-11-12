"""Visual smoke test: starts PIE, walks the cat around, takes screenshots, quits.

Run:  UnrealEditor.exe Glitching_Realities.uproject -ExecutePythonScript=Tools/Python/play_test.py
Screenshots land in Saved/Screenshots/.
"""
import math
import unreal

state = {"t": 0.0, "pie_t": None, "shots": 0, "handle": None}
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

# (seconds after PIE start, action)
PLAN = [
    (45.0, "front"),   # wait for shaders, then look at the cat's face
    (47.0, "shot"),
    (48.0, "side"),
    (50.5, "shot"),
    (51.3, "shot"),
    (53.0, "quit"),
]


def pawn_and_pc():
    world = ues.get_game_world()
    if not world:
        return None, None
    return unreal.GameplayStatics.get_player_pawn(world, 0), unreal.GameplayStatics.get_player_controller(world, 0)


def tick(dt):
    state["t"] += dt
    if state["pie_t"] is None:
        if state["t"] > 8.0:
            unreal.log("PLAYTEST: starting PIE")
            les.editor_request_begin_play()
            state["pie_t"] = 0.0
        return
    state["pie_t"] += dt
    pawn, pc = pawn_and_pc()
    mode = state.get("mode")
    if pawn and mode == "walk":
        yaw = math.radians(state["walk_yaw"])
        pawn.add_movement_input(unreal.Vector(math.cos(yaw), math.sin(yaw), 0), 1.0)

    while PLAN and state["pie_t"] >= PLAN[0][0]:
        _, action = PLAN.pop(0)
        unreal.log(f"PLAYTEST: {action} pawn={pawn}")
        if action == "front" and pawn and pc:
            yaw = pawn.get_actor_rotation().yaw
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw + 150))
        elif action == "side" and pawn and pc:
            cam_yaw = pc.get_control_rotation().yaw
            state["walk_yaw"] = cam_yaw + 90  # walk across the screen
            state["mode"] = "walk"
        elif action == "shot":
            state["shots"] += 1
            unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, f"GlitchCat_{state['shots']}.png")
        elif action == "quit":
            unreal.unregister_slate_post_tick_callback(state["handle"])
            les.editor_request_end_play()
            unreal.SystemLibrary.quit_editor()


state["handle"] = unreal.register_slate_post_tick_callback(tick)
