"""Generate the polished, deliberately small RigNostic demo face."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

CONTROLS = (
    "eyeBlink_L",
    "eyeBlink_R",
    "jawOpen",
    "mouthSmile_L",
    "mouthSmile_R",
    "mouthFunnel",
    "browUp_L",
    "browUp_R",
)


def output_path() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if "--output" in args:
        return Path(args[args.index("--output") + 1]).resolve()
    return Path(__file__).resolve().parent / "rignostic_demo_face_v2.blend"


def material(name: str, color: tuple[float, float, float, float], metallic=0.0, roughness=0.5):
    value = bpy.data.materials.new(name)
    value.diffuse_color = color
    value.metallic = metallic
    value.roughness = roughness
    return value


def uv_sphere(name, location, scale, mat, segments=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def add_key(obj, name, transform):
    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis")
    key = obj.shape_key_add(name=name, from_mix=False)
    for index, point in enumerate(key.data):
        point.co = transform(index, point.co.copy())
    return key


def make_rig():
    armature = bpy.data.armatures.new("DemoFaceRigData")
    rig = bpy.data.objects.new("DemoFaceRig", armature)
    bpy.context.collection.objects.link(rig)
    rig.show_in_front = True
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = armature.edit_bones.new("face_root")
    root.head, root.tail = (0, 0.25, -1.55), (0, 0.25, 1.55)
    positions = {
        "eyeBlink_L": (-0.55, -1.25, 0.4), "eyeBlink_R": (0.55, -1.25, 0.4),
        "browUp_L": (-0.55, -1.25, 0.88), "browUp_R": (0.55, -1.25, 0.88),
        "mouthSmile_L": (-0.52, -1.25, -0.45), "mouthSmile_R": (0.52, -1.25, -0.45),
        "mouthFunnel": (0, -1.25, -0.42), "jawOpen": (0, -1.25, -0.95),
    }
    for name in CONTROLS:
        bone = armature.edit_bones.new(name)
        bone.head = positions[name]
        bone.tail = Vector(positions[name]) + Vector((0, 0, 0.18))
        bone.parent = root
    bpy.ops.object.mode_set(mode="POSE")
    for name in CONTROLS:
        bone = rig.pose.bones[name]
        bone["value"] = 0.0
        bone.id_properties_ui("value").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
    for name in ("browUp_L", "browUp_R"):
        limit = rig.pose.bones[name].constraints.new("LIMIT_LOCATION")
        limit.name = "Brow Range"
        limit.use_min_z = limit.use_max_z = True
        limit.min_z, limit.max_z = 0.0, 0.3
        limit.owner_space = "LOCAL"
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def connect_driver(obj, key_name, rig, control=None):
    curve = obj.data.shape_keys.driver_add(f'key_blocks["{key_name}"].value')
    driver = curve.driver
    driver.type = "SCRIPTED"
    driver.expression = "var"
    variable = driver.variables.new()
    variable.name = "var"
    variable.type = "SINGLE_PROP"
    variable.targets[0].id = rig
    variable.targets[0].data_path = f'pose.bones["{control or key_name}"]["value"]'


def add_studio(scene):
    camera_data = bpy.data.cameras.new("DemoCamera")
    camera = bpy.data.objects.new("DemoCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0, -6.2, 0.05)
    camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 58
    scene.camera = camera
    for name, location, energy, size, color in (
        ("Key", (-3.2, -4.0, 4.0), 850, 4.0, (0.72, 0.9, 1.0)),
        ("Fill", (3.5, -2.5, 1.0), 600, 3.0, (0.35, 0.7, 1.0)),
        ("Rim", (0.5, 2.2, 3.5), 1000, 2.5, (0.2, 0.85, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = location
        light.rotation_euler = (-Vector(location)).to_track_quat("-Z", "Y").to_euler()


def make_lips(mat):
    vertices = [
        (-0.58, -1.0, -0.32), (-0.28, -1.06, -0.25), (0, -1.08, -0.23),
        (0.28, -1.06, -0.25), (0.58, -1.0, -0.32), (0.28, -1.07, -0.42),
        (0, -1.09, -0.45), (-0.28, -1.07, -0.42),
    ]
    faces = [(0, 1, 7), (1, 2, 6, 7), (2, 3, 5, 6), (3, 4, 5)]
    mesh = bpy.data.meshes.new("LipsData")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new("Lips", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Soft lip edge", "SOLIDIFY")
    bevel.thickness = 0.035
    return obj


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    skin = material("Skin", (0.42, 0.15, 0.09, 1), roughness=0.72)
    skin_light = material("Ear", (0.5, 0.2, 0.13, 1), roughness=0.72)
    white = material("Eye white", (0.92, 0.96, 1.0, 1), roughness=0.25)
    iris = material("Iris", (0.03, 0.32, 0.42, 1), metallic=0.1, roughness=0.2)
    dark = material("Pupil", (0.006, 0.009, 0.012, 1), roughness=0.25)
    lip_mat = material("Lips", (0.45, 0.035, 0.06, 1), roughness=0.45)
    brow_mat = material("Brows", (0.035, 0.018, 0.012, 1), roughness=0.8)
    neck_mat = skin

    head = uv_sphere("DemoHead", (0, 0, 0), (1.15, 0.92, 1.48), skin)
    uv_sphere("Ear_L", (-1.12, 0, 0.05), (0.2, 0.13, 0.38), skin_light, 32, 20)
    uv_sphere("Ear_R", (1.12, 0, 0.05), (0.2, 0.13, 0.38), skin_light, 32, 20)
    uv_sphere("Neck", (0, 0.23, -1.55), (0.48, 0.42, 0.65), neck_mat, 40, 24)
    uv_sphere("Nose", (0, -0.91, 0.02), (0.18, 0.24, 0.32), skin_light, 32, 20)

    rig = make_rig()
    for side, x in (("L", -0.46), ("R", 0.46)):
        eye = uv_sphere(f"Eye_{side}", (x, -0.79, 0.37), (0.34, 0.17, 0.22), white, 40, 24)
        add_key(eye, f"eyeBlink_{side}", lambda _i, co: Vector((co.x, co.y, co.z * 0.08)))
        connect_driver(eye, f"eyeBlink_{side}", rig)
        uv_sphere(f"Iris_{side}", (x, -0.955, 0.37), (0.115, 0.035, 0.115), iris, 32, 20)
        uv_sphere(f"Pupil_{side}", (x, -0.988, 0.37), (0.048, 0.018, 0.048), dark, 24, 16)
        brow = uv_sphere(f"Brow_{side}", (x, -0.86, 0.78), (0.42, 0.045, 0.075), brow_mat, 32, 16)
        add_key(brow, f"browUp_{side}", lambda _i, co: co + Vector((0, 0, 0.23)))
        connect_driver(brow, f"browUp_{side}", rig)

    lips = make_lips(lip_mat)
    add_key(
        lips,
        "mouthSmile_L",
        lambda i, co: co + (Vector((-0.08, 0, 0.27)) if i in {0, 1, 7} else Vector()),
    )
    add_key(
        lips,
        "mouthSmile_R",
        lambda i, co: co + (Vector((0.08, 0, 0.27)) if i in {3, 4, 5} else Vector()),
    )
    add_key(lips, "mouthFunnel", lambda _i, co: Vector((co.x * 0.53, co.y - 0.16, co.z)))
    add_key(
        lips,
        "jawOpen",
        lambda i, co: co
        + (Vector((0, 0, -0.38)) if i in {5, 6, 7} else Vector((0, 0, -0.08))),
    )
    for name in ("mouthSmile_L", "mouthSmile_R", "mouthFunnel", "jawOpen"):
        connect_driver(lips, name, rig)

    # A subtle chin response makes jawOpen readable from both front and profile views.
    add_key(
        head,
        "jawOpen",
        lambda _i, co: co
        + (Vector((0, 0.05, -0.16)) if co.z < -0.48 and co.y < 0 else Vector()),
    )
    connect_driver(head, "jawOpen", rig)

    bpy.context.scene["rignostic_fixture"] = "demo_face_v2"
    bpy.context.scene["rignostic_controls"] = ",".join(CONTROLS)
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
    world = bpy.data.worlds.new("Black Ice World")
    world.color = (0.008, 0.012, 0.018)
    bpy.context.scene.world = world
    add_studio(bpy.context.scene)
    destination = output_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), check_existing=False)
    print(f"RIGNOSTIC_DEMO_SAVED={destination}")


if __name__ == "__main__":
    main()
