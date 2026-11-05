# inspect_rig.py
# Exporta huesos, restricciones IK, controles y acciones reales de un .blend.
# No guarda el archivo ni modifica el esqueleto.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "C:\Users\emper\OneDrive\Documents\personaje_base_woman.blend.blend" `
#     --python "scripts\blender\inspect_rig.py" `
#     -- "scripts\blender\rig_inspection.json"

import json
import os
import sys

import bpy
from mathutils import Vector


def ruta_salida():
    if "--" in sys.argv:
        extras = sys.argv[sys.argv.index("--") + 1 :]
        for argumento in extras:
            if argumento.lower().endswith(".json"):
                return os.path.abspath(argumento)
    carpeta = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(carpeta, "rig_inspection.json")


def redondear(vector, cifras=5):
    return [round(float(valor), cifras) for valor in vector]


def matriz(objeto):
    return [redondear(fila) for fila in objeto.matrix_world]


def restriccion(con):
    datos = {
        "nombre": con.name,
        "tipo": con.type,
        "activo": bool(getattr(con, "enabled", True)),
        "influencia": round(float(getattr(con, "influence", 1.0)), 4),
    }
    objetivo = getattr(con, "target", None)
    if objetivo is not None:
        datos["objetivo"] = objetivo.name
    subobjetivo = getattr(con, "subtarget", None)
    if subobjetivo:
        datos["subobjetivo"] = subobjetivo
    if hasattr(con, "chain_count"):
        datos["eslabones"] = int(con.chain_count)
    if hasattr(con, "pole_target") and con.pole_target is not None:
        datos["polo"] = con.pole_target.name
        datos["polo_subobjetivo"] = con.pole_subtarget
    if hasattr(con, "use_location"):
        datos["usa_localizacion"] = bool(con.use_location)
    if hasattr(con, "use_rotation"):
        datos["usa_rotacion"] = bool(con.use_rotation)
    return datos


def inspeccionar():
    armaduras = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armaduras:
        raise RuntimeError("El archivo no contiene ninguna armadura.")

    resultado = {
        "archivo": bpy.data.filepath,
        "blender": bpy.app.version_string,
        "armaduras": [],
        "acciones": [],
        "objetos": [],
    }

    for accion in bpy.data.actions:
        resultado["acciones"].append(
            {
                "nombre": accion.name,
                "fotogramas": [round(float(v), 2) for v in accion.frame_range],
            }
        )

    for obj in bpy.data.objects:
        resultado["objetos"].append(
            {
                "nombre": obj.name,
                "tipo": obj.type,
                "padre": obj.parent.name if obj.parent else None,
                "localizacion": redondear(obj.location),
                "rotacion_grados": redondear([v * 57.2957795 for v in obj.rotation_euler]),
                "escala": redondear(obj.scale),
                "oculto_render": bool(obj.hide_render),
            }
        )

    for arm in armaduras:
        bpy.context.view_layer.objects.active = arm
        bpy.context.view_layer.update()
        huesos = []
        controles_ik = []
        for hueso in arm.data.bones:
            pose = arm.pose.bones.get(hueso.name)
            restricciones = []
            if pose is not None:
                restricciones = [restriccion(con) for con in pose.constraints]
                for con in pose.constraints:
                    if con.type == "IK":
                        controles_ik.append(
                            {
                                "hueso_con_ik": hueso.name,
                                "objetivo": con.target.name if con.target else None,
                                "control": con.subtarget,
                                "eslabones": int(con.chain_count),
                                "polo": con.pole_subtarget if getattr(con, "pole_target", None) else "",
                                "influencia": round(float(con.influence), 4),
                            }
                        )
            cabeza_mundo = arm.matrix_world @ hueso.head_local
            cola_mundo = arm.matrix_world @ hueso.tail_local
            huesos.append(
                {
                    "nombre": hueso.name,
                    "padre": hueso.parent.name if hueso.parent else None,
                    "deforma": bool(hueso.use_deform),
                    "conectado": bool(hueso.use_connect),
                    "cabeza_local": redondear(hueso.head_local),
                    "cola_local": redondear(hueso.tail_local),
                    "cabeza_mundo": redondear(cabeza_mundo),
                    "cola_mundo": redondear(cola_mundo),
                    "longitud": round(float(hueso.length), 5),
                    "restricciones": restricciones,
                }
            )
        resultado["armaduras"].append(
            {
                "nombre": arm.name,
                "huesos": len(huesos),
                "matriz_mundo": matriz(arm),
                "accion": (
                    arm.animation_data.action.name
                    if arm.animation_data and arm.animation_data.action
                    else None
                ),
                "controles_ik": controles_ik,
                "lista_huesos": huesos,
                "hijos": [
                    {"nombre": hijo.name, "tipo": hijo.type}
                    for hijo in arm.children
                ],
            }
        )
    return resultado


def main():
    destino = ruta_salida()
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    datos = inspeccionar()
    with open(destino, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    print("INSPECCION_OK", destino)
    for armadura in datos["armaduras"]:
        print("ARMADURA", armadura["nombre"], "huesos", armadura["huesos"])
        for control in armadura["controles_ik"]:
            print(
                "IK",
                control["hueso_con_ik"],
                "->",
                control["control"],
                "eslabones",
                control["eslabones"],
            )


if __name__ == "__main__":
    main()
