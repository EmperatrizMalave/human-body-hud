# create_squat.py
# Crea la acción squat_bodyweight en una copia del maniquí MPFB.
# No modifica el esqueleto ni sobrescribe el .blend de origen.
#
# Los controles salen de scripts/blender/rig_inspection.json:
#   root
#   left_foot_ik, right_foot_ik
#   left_knee_ik, right_knee_ik
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "C:\Users\emper\OneDrive\Documents\personaje_base_woman.blend.blend" `
#     --python "scripts\blender\create_squat.py"

import json
import os

import bpy
from mathutils import Vector


ENTRADA_ESPERADA = r"C:\Users\emper\OneDrive\Documents\personaje_base_woman.blend.blend"
NOMBRE_ACCION = "squat_bodyweight"
DESCENSO_METROS = 0.22
RODILLA_ADELANTE_METROS = 0.10
RODILLA_ABAJO_METROS = 0.04

CONTROLES = (
    "root",
    "left_foot_ik",
    "right_foot_ik",
    "left_knee_ik",
    "right_knee_ik",
)


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def exigir_controles(arm):
    faltan = [nombre for nombre in CONTROLES if nombre not in arm.pose.bones]
    if faltan:
        raise RuntimeError(
            "El rig no tiene estos controles y no se creó la animación: " + ", ".join(faltan)
        )


def cabeza_mundo(arm, pose_bone):
    return arm.matrix_world @ pose_bone.head


def mover_cabeza(arm, nombre, destino):
    pose = arm.pose.bones[nombre]
    bpy.context.view_layer.update()
    actual = cabeza_mundo(arm, pose)
    mundo = arm.matrix_world @ pose.matrix
    mundo.translation += destino - actual
    pose.matrix = arm.matrix_world.inverted() @ mundo
    bpy.context.view_layer.update()


def insertar(pose, fotograma):
    pose.keyframe_insert(data_path="location", frame=fotograma)
    if pose.rotation_mode == "QUATERNION":
        pose.keyframe_insert(data_path="rotation_quaternion", frame=fotograma)
    else:
        pose.keyframe_insert(data_path="rotation_euler", frame=fotograma)


def pose_reposo(arm):
    for pose in arm.pose.bones:
        pose.location = (0.0, 0.0, 0.0)
        if pose.rotation_mode == "QUATERNION":
            pose.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        else:
            pose.rotation_euler = (0.0, 0.0, 0.0)
        pose.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()


def medir(arm):
    return {
        nombre: [round(v, 5) for v in cabeza_mundo(arm, arm.pose.bones[nombre])]
        for nombre in ("root", "left_foot_ik", "right_foot_ik", "foot.L", "foot.R", "left_knee_ik", "right_knee_ik")
    }


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Abre el .blend del personaje antes de ejecutar el script.")
    if os.path.abspath(bpy.data.filepath) == os.path.abspath(
        os.path.join(carpeta_proyecto(), "assets", "models", "personaje_squat_bodyweight.blend")
    ):
        raise RuntimeError("El archivo abierto ya es el resultado. Usa el modelo original.")

    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    if arm is None:
        raise RuntimeError("No hay armadura en el archivo.")
    exigir_controles(arm)

    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    pose_reposo(arm)
    reposo = medir(arm)

    datos = arm.animation_data_create()
    accion_previa = bpy.data.actions.get(NOMBRE_ACCION)
    if accion_previa is not None:
        bpy.data.actions.remove(accion_previa)
    accion = bpy.data.actions.new(NOMBRE_ACCION)
    datos.action = accion

    for fotograma in (1, 48):
        bpy.context.scene.frame_set(fotograma)
        pose_reposo(arm)
        for nombre in CONTROLES:
            insertar(arm.pose.bones[nombre], fotograma)

    bpy.context.scene.frame_set(24)
    pose_reposo(arm)
    raiz = Vector(reposo["root"])
    mover_cabeza(arm, "root", raiz + Vector((0.0, 0.0, -DESCENSO_METROS)))
    for lado in ("left", "right"):
        rodilla = Vector(reposo[f"{lado}_knee_ik"])
        mover_cabeza(
            arm,
            f"{lado}_knee_ik",
            rodilla + Vector((0.0, -RODILLA_ADELANTE_METROS, -RODILLA_ABAJO_METROS)),
        )
    for nombre in CONTROLES:
        insertar(arm.pose.bones[nombre], 24)

    bpy.context.view_layer.update()
    fondo = medir(arm)
    pies = {}
    for nombre in ("foot.L", "foot.R", "left_foot_ik", "right_foot_ik"):
        delta = Vector(fondo[nombre]) - Vector(reposo[nombre])
        pies[nombre] = {
            "reposo": reposo[nombre],
            "fotograma_24": fondo[nombre],
            "desplazamiento_m": [round(v, 5) for v in delta],
            "desplazamiento_total_m": round(delta.length, 5),
        }

    aviso = [
        nombre
        for nombre, info in pies.items()
        if info["desplazamiento_total_m"] > 0.02
    ]
    informe = {
        "archivo_origen": bpy.data.filepath,
        "armadura": arm.name,
        "accion": NOMBRE_ACCION,
        "fotogramas": {"inicio": 1, "fondo": 24, "regreso": 48},
        "descenso_pedido_m": DESCENSO_METROS,
        "root_reposo": reposo["root"],
        "root_fotograma_24": fondo["root"],
        "pies": pies,
        "pies_con_desplazamiento_mayor_a_2cm": aviso,
        "nota": (
            "Pose mecánica para revisión visual. No está validada como sentadilla anatómica. "
            "Los dedos del modelo apuntan hacia -Y; las rodillas se adelantan en esa dirección."
        ),
    }
    destino_informe = os.path.join(os.path.dirname(__file__), "squat_report.json")
    with open(destino_informe, "w", encoding="utf-8") as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)

    escena = bpy.context.scene
    escena.frame_start = 1
    escena.frame_end = 48
    escena.frame_set(24)

    salida = os.path.join(carpeta_proyecto(), "assets", "models", "personaje_squat_bodyweight.blend")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    if os.path.abspath(salida) == os.path.abspath(bpy.data.filepath):
        raise RuntimeError("La ruta de salida es el archivo original. No se guardó.")
    bpy.ops.wm.save_as_mainfile(filepath=salida)
    print("SQUAT_OK", salida)
    print("INFORME", destino_informe)
    if aviso:
        print("DIAGNOSTICO pies movidos:", ", ".join(aviso))
    else:
        print("DIAGNOSTICO pies dentro de 2 cm")


if __name__ == "__main__":
    main()
