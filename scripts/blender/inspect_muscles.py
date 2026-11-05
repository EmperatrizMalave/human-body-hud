# inspect_muscles.py
# Lee mallas, materiales, grupos de vértices y huesos.
# No guarda el .blend ni cambia pesos, restricciones ni acciones.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\inspect_muscles.py"

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
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "muscles_inspection.json")


def redondear(vector, cifras=5):
    return [round(float(valor), cifras) for valor in vector]


def color_base(material):
    if material is None or not material.use_nodes or material.node_tree is None:
        return None
    for nodo in material.node_tree.nodes:
        if nodo.type == "BSDF_PRINCIPLED":
            valor = nodo.inputs["Base Color"].default_value
            return [round(float(canal), 4) for canal in valor]
    return None


def inspeccionar_malla(obj, nombres_hueso):
    grupos = []
    conteo = {grupo.index: 0 for grupo in obj.vertex_groups}
    for vertice in obj.data.vertices:
        for asignacion in vertice.groups:
            if asignacion.weight > 0.001 and asignacion.group in conteo:
                conteo[asignacion.group] += 1
    for grupo in obj.vertex_groups:
        grupos.append(
            {
                "nombre": grupo.name,
                "vertices_con_peso": conteo.get(grupo.index, 0),
                "coincide_con_hueso": grupo.name in nombres_hueso,
            }
        )
    locales = [vertice.co for vertice in obj.data.vertices]
    if locales:
        minimo = Vector(
            (
                min(punto.x for punto in locales),
                min(punto.y for punto in locales),
                min(punto.z for punto in locales),
            )
        )
        maximo = Vector(
            (
                max(punto.x for punto in locales),
                max(punto.y for punto in locales),
                max(punto.z for punto in locales),
            )
        )
    else:
        minimo = Vector()
        maximo = Vector()
    return {
        "nombre": obj.name,
        "vertices": len(obj.data.vertices),
        "caras": len(obj.data.polygons),
        "padre": obj.parent.name if obj.parent else None,
        "modificadores": [
            {"nombre": mod.name, "tipo": mod.type, "objetivo": getattr(getattr(mod, "object", None), "name", None)}
            for mod in obj.modifiers
        ],
        "materiales": [
            {"nombre": ranura.name if ranura else None, "color_base": color_base(ranura)}
            for ranura in obj.data.materials
        ],
        "grupos_vertices": grupos,
        "grupos_que_no_son_hueso": [grupo["nombre"] for grupo in grupos if not grupo["coincide_con_hueso"]],
        "caja_local": {"min": redondear(minimo), "max": redondear(maximo)},
    }


def hueso_reposo(arm, malla, nombre):
    hueso = arm.data.bones.get(nombre)
    if hueso is None:
        return None
    cabeza_mundo = arm.matrix_world @ hueso.head_local
    cola_mundo = arm.matrix_world @ hueso.tail_local
    inversa = malla.matrix_world.inverted()
    return {
        "nombre": nombre,
        "padre": hueso.parent.name if hueso.parent else None,
        "cabeza_mundo": redondear(cabeza_mundo),
        "cola_mundo": redondear(cola_mundo),
        "cabeza_malla_local": redondear(inversa @ cabeza_mundo),
        "cola_malla_local": redondear(inversa @ cola_mundo),
    }


def main():
    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    if arm is None:
        raise RuntimeError("No hay armadura en el archivo.")
    nombres_hueso = {hueso.name for hueso in arm.data.bones}
    mallas = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    cuerpo = next((obj for obj in mallas if obj.parent == arm), mallas[0] if mallas else None)
    if cuerpo is None:
        raise RuntimeError("No hay malla en el archivo.")

    referencias = [
        "root",
        "pelvis.L",
        "pelvis.R",
        "upperleg01.L",
        "upperleg01.R",
        "upperleg02.L",
        "upperleg02.R",
        "lowerleg01.L",
        "lowerleg01.R",
        "foot.L",
        "foot.R",
        "toe1-1.L",
        "toe1-1.R",
    ]
    resultado = {
        "archivo": bpy.data.filepath,
        "blender": bpy.app.version_string,
        "armadura": arm.name,
        "huesos": len(arm.data.bones),
        "nombres_hueso": sorted(nombres_hueso),
        "acciones": [
            {"nombre": accion.name, "fotogramas": [round(float(v), 2) for v in accion.frame_range]}
            for accion in bpy.data.actions
        ],
        "accion_activa": (
            arm.animation_data.action.name
            if arm.animation_data and arm.animation_data.action
            else None
        ),
        "mallas": [inspeccionar_malla(obj, nombres_hueso) for obj in mallas],
        "referencias_reposo": [
            dato
            for nombre in referencias
            if (dato := hueso_reposo(arm, cuerpo, nombre)) is not None
        ],
        "nota": (
            "Un grupo de vértices que coincide con un hueso es un peso de deformación. "
            "No es el límite anatómico de un músculo."
        ),
    }
    destino = ruta_salida()
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)
    print("MUSCULOS_OK", destino)
    ajenos = resultado["mallas"][0]["grupos_que_no_son_hueso"]
    print("GRUPOS_FUERA_DEL_ESQUELETO", len(ajenos))


if __name__ == "__main__":
    main()
