# inspect_uv.py
# Describe los mapas UV de Human. No guarda el .blend.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\inspect_uv.py"

import json
import os

import bpy
from mathutils import Vector


def ruta_salida():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "uv_inspection.json")


def leer_uv(capa, indice):
    dato = capa.uv[indice]
    return dato.vector.copy() if hasattr(dato, "vector") else dato.uv.copy()


def main():
    arm = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
    cuerpo = next(obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name == "Human")
    malla = cuerpo.data
    capas = []
    for capa in malla.uv_layers:
        us = [leer_uv(capa, indice) for indice in range(len(capa.uv))]
        if not us:
            continue
        minimo = Vector((min(c.x for c in us), min(c.y for c in us)))
        maximo = Vector((max(c.x for c in us), max(c.y for c in us)))
        capas.append(
            {
                "nombre": capa.name,
                "activa": capa == malla.uv_layers.active,
                "bucles": len(us),
                "min": [round(minimo.x, 5), round(minimo.y, 5)],
                "max": [round(maximo.x, 5), round(maximo.y, 5)],
            }
        )

    def local(nombre):
        hueso = arm.data.bones[nombre]
        return cuerpo.matrix_world.inverted() @ (arm.matrix_world @ hueso.head_local)

    cadera_l = local("upperleg01.L")
    cadera_r = local("upperleg01.R")
    activa = malla.uv_layers.active
    muslos = {"L": [], "R": []}
    if activa is not None:
        for cara in malla.polygons:
            centro = sum((malla.vertices[i].co for i in cara.vertices), Vector()) / len(cara.vertices)
            if not (0.45 < centro.z < 0.82):
                continue
            lado = "L" if (centro - cadera_l).length < (centro - cadera_r).length else "R"
            if abs(centro.x) < 0.04:
                continue
            uvs = [leer_uv(activa, li) for li in cara.loop_indices]
            promedio = sum(uvs, Vector((0.0, 0.0))) / len(uvs)
            muslos[lado].append(promedio)

    def caja(puntos):
        if not puntos:
            return None
        return {
            "caras": len(puntos),
            "min": [round(min(p.x for p in puntos), 5), round(min(p.y for p in puntos), 5)],
            "max": [round(max(p.x for p in puntos), 5), round(max(p.y for p in puntos), 5)],
        }

    costuras = 0
    if activa is not None:
        aristas = {}
        for cara in malla.polygons:
            puntos = cara.vertices
            bucles = cara.loop_indices
            for i in range(len(puntos)):
                a = puntos[i]
                b = puntos[(i + 1) % len(puntos)]
                clave = tuple(sorted((a, b)))
                uv = tuple(
                    tuple(round(v, 5) for v in leer_uv(activa, bucles[n]))
                    for n in (i, (i + 1) % len(puntos))
                )
                aristas.setdefault(clave, []).append(uv)
        for pares in aristas.values():
            if len(pares) == 2 and pares[0] != pares[1] and pares[0] != tuple(reversed(pares[1])):
                costuras += 1

    resultado = {
        "archivo": bpy.data.filepath,
        "malla": cuerpo.name,
        "vertices": len(malla.vertices),
        "caras": len(malla.polygons),
        "capas_uv": capas,
        "muslo_uv": {"L": caja(muslos["L"]), "R": caja(muslos["R"])},
        "aristas_con_uv_distinto": costuras,
        "nota": "La caja del muslo solo localiza las islas. No es el borde del cuádriceps.",
    }
    destino = ruta_salida()
    with open(destino, "w", encoding="utf-8") as archivo:
        json.dump(resultado, archivo, ensure_ascii=False, indent=2)
    print("UV_OK", destino)
    print("CAPAS", len(capas), "COSTURAS", costuras)


if __name__ == "__main__":
    main()
