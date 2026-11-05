# crear_hombre.py
# Duplica la sentadilla y arma el hombre con el mismo Standard Rig.
# Copia squat_bodyweight; no la vuelve a posar.
# No guarda el .blend de origen.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\crear_hombre.py"

import importlib
import os

import bpy


CONTROLES = (
    "root",
    "left_foot_ik",
    "right_foot_ik",
    "left_knee_ik",
    "right_knee_ik",
)


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def cargar_mpfb():
    for nombre in ("mpfb", "bl_ext.blender_org.mpfb"):
        try:
            return importlib.import_module(nombre)
        except ModuleNotFoundError:
            continue
    raise RuntimeError("MPFB no está cargado. No se creó el hombre.")


def armadura():
    return next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)


def restricciones(arm):
    encontradas = []
    for pose in arm.pose.bones:
        for con in pose.constraints:
            if con.type == "IK":
                encontradas.append((pose.name, con.subtarget, int(con.chain_count)))
    return encontradas


def muestra_malla(cuerpo):
    deps = bpy.context.evaluated_depsgraph_get()
    evaluada = cuerpo.evaluated_get(deps)
    vertices = evaluada.data.vertices
    paso = max(1, len(vertices) // 40)
    return [vertices[i].co.copy() for i in range(0, len(vertices), paso)]


def guardar_copia(ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=ruta, copy=True)


def main():
    if os.path.basename(bpy.data.filepath) != "personaje_squat_bodyweight.blend":
        raise RuntimeError("Hay que abrir personaje_squat_bodyweight.blend. No se creó el hombre.")

    cuerpo = bpy.data.objects.get("Human")
    arm = armadura()
    if cuerpo is None or cuerpo.type != "MESH" or arm is None:
        raise RuntimeError("Diagnóstico: no están Human y su armadura. No se creó el hombre.")
    accion = arm.animation_data.action if arm.animation_data else None
    if accion is None or accion.name != "squat_bodyweight":
        raise RuntimeError("Diagnóstico: la acción activa no es squat_bodyweight. No se creó el hombre.")

    huesos = {hueso.name for hueso in arm.data.bones}
    ik = restricciones(arm)
    faltan = [nombre for nombre in CONTROLES if nombre not in arm.pose.bones]
    if faltan or not ik:
        raise RuntimeError("Diagnóstico: faltan controles IK. No se creó el hombre: " + ", ".join(faltan))

    mpfb = cargar_mpfb()
    propiedades = mpfb.entities.objectproperties.HumanObjectProperties
    objetivos = mpfb.services.TargetService
    humanos = mpfb.services.HumanService
    rigs = mpfb.services.RigService

    genero = float(propiedades.get_value("gender", entity_reference=cuerpo))
    tipo_rig = rigs.identify_rig(arm)
    print("GENERO_INICIAL", round(genero, 3), "RIG", tipo_rig, "VERTICES", len(cuerpo.data.vertices))
    if genero >= 0.99:
        raise RuntimeError(
            "Diagnóstico: el maniquí de origen ya está en masculino. No se creó otra copia."
        )

    antes = muestra_malla(cuerpo)
    modelos = os.path.join(carpeta_proyecto(), "assets", "models")
    guardar_copia(os.path.join(modelos, "personaje_squat_bodyweight_mujer.blend"))

    propiedades.set_value("gender", 1.0, entity_reference=cuerpo)
    objetivos.reapply_macro_details(cuerpo, remove_zero_weight_targets=True)
    humanos.refit(cuerpo)
    bpy.context.view_layer.update()

    arm = armadura()
    cuerpo = bpy.data.objects.get("Human")
    accion = arm.animation_data.action if arm and arm.animation_data else None
    genero_final = float(propiedades.get_value("gender", entity_reference=cuerpo))
    huesos_final = {hueso.name for hueso in arm.data.bones}
    ik_final = restricciones(arm)
    despues = muestra_malla(cuerpo)
    cambio = max((a - b).length for a, b in zip(antes, despues))

    if abs(genero_final - 1.0) > 0.001:
        raise RuntimeError(f"Diagnóstico: el género no quedó en masculino ({genero_final}). No se guardó el hombre.")
    if accion is None or accion.name != "squat_bodyweight":
        raise RuntimeError("Diagnóstico: se perdió squat_bodyweight al ajustar el hombre. No se guardó.")
    if huesos_final != huesos or ik_final != ik:
        raise RuntimeError("Diagnóstico: el esqueleto o las restricciones IK cambiaron. No se guardó el hombre.")
    if cambio < 0.01:
        raise RuntimeError("Diagnóstico: la malla no cambió al pasar a masculino. No se guardó el hombre.")
    if os.path.basename(bpy.data.filepath) != "personaje_squat_bodyweight.blend":
        raise RuntimeError("Diagnóstico: el archivo abierto dejó de ser el original. No se guardó el hombre.")

    destino = os.path.join(modelos, "personaje_squat_bodyweight_hombre.blend")
    guardar_copia(destino)
    print("HOMBRE_OK", destino, "CAMBIO_M", round(cambio, 4), "FOTOGRAMAS", list(accion.frame_range))


if __name__ == "__main__":
    main()
