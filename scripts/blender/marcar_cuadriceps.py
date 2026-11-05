# marcar_cuadriceps.py
# Pinta una primera región de ambos cuádriceps sobre la piel.
# No modifica pesos de deformación, restricciones ni el archivo de origen.
#
# Los huesos solo sirven de regla para medir el muslo. El peso de
# upperleg01 no es el borde del cuádriceps.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\marcar_cuadriceps.py"

import json
import math
import os

import bpy
from mathutils import Vector


T_MIN = 0.14
T_MAX = 0.93
ANGULO_MAX = math.radians(80)
GRIS = (0.718, 0.725, 0.745, 1.0)
TURQUESA = (19 / 255, 184 / 255, 166 / 255, 1.0)
ESMERALDA = (46 / 255, 204 / 255, 113 / 255, 1.0)
HUESOS = ("upperleg01.L", "upperleg01.R", "lowerleg01.L", "lowerleg01.R", "foot.L", "foot.R", "toe1-1.L", "toe1-1.R")


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def exigir_origen():
    if not bpy.data.filepath:
        raise RuntimeError("Abre el .blend del maniquí antes de ejecutar el script.")
    salida = os.path.join(carpeta_proyecto(), "assets", "models", "personaje_muscular_test.blend")
    if os.path.abspath(bpy.data.filepath) == os.path.abspath(salida):
        raise RuntimeError("El archivo abierto ya es el resultado. Usa el modelo de origen.")
    return salida


def exigir_huesos(arm):
    faltan = [nombre for nombre in HUESOS if nombre not in arm.data.bones]
    if faltan:
        raise RuntimeError(
            "Diagnóstico: faltan huesos de referencia y no se pintó nada: " + ", ".join(faltan)
        )


def local_de_hueso(arm, malla, nombre):
    hueso = arm.data.bones[nombre]
    mundo = arm.matrix_world @ hueso.head_local
    return malla.matrix_world.inverted() @ mundo


def vertices_de_grupo(obj, nombre, minimo=0.5):
    grupo = obj.vertex_groups.get(nombre)
    if grupo is None:
        return set()
    indice = grupo.index
    return {
        vertice.index
        for vertice in obj.data.vertices
        for asignacion in vertice.groups
        if asignacion.group == indice and asignacion.weight >= minimo
    }


def vertices_visibles(obj):
    cuerpo = vertices_de_grupo(obj, "body", 0.5)
    if not cuerpo:
        raise RuntimeError("Diagnóstico: la malla no tiene el grupo visible 'body'. No se pintó nada.")
    mascara = next((mod for mod in obj.modifiers if mod.type == "MASK"), None)
    if mascara is None or not mascara.vertex_group:
        return cuerpo
    grupo = vertices_de_grupo(obj, mascara.vertex_group, 0.5)
    # El modificador Mask deja visible el grupo. Con invert, ese grupo se oculta.
    if mascara.invert_vertex_group:
        return cuerpo - grupo
    return cuerpo & grupo


def material(nombre, color):
    bloque = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    bloque.diffuse_color = color
    bloque.use_nodes = True
    bsdf = next(nodo for nodo in bloque.node_tree.nodes if nodo.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.48
    bsdf.inputs["Metallic"].default_value = 0.0
    return bloque


def preparar_materiales(obj):
    malla = obj.data
    while malla.materials:
        malla.materials.pop(index=0)
    malla.materials.append(material("BODY_BASE", GRIS))
    malla.materials.append(material("MUSCLE_ACTIVE", TURQUESA))
    malla.materials.append(material("MUSCLE_SECONDARY", ESMERALDA))


def dirección_anterior(arm, malla):
    avance = Vector((0.0, 0.0, 0.0))
    for lado in ("L", "R"):
        avance += local_de_hueso(arm, malla, f"toe1-1.{lado}") - local_de_hueso(arm, malla, f"foot.{lado}")
    avance.z = 0.0
    if avance.length < 1e-6:
        raise RuntimeError("Diagnóstico: no se pudo medir hacia dónde apuntan los pies. No se pintó nada.")
    return avance.normalized()


def regla_muslo(arm, malla, lado, anterior):
    cadera = local_de_hueso(arm, malla, f"upperleg01.{lado}")
    rodilla = local_de_hueso(arm, malla, f"lowerleg01.{lado}")
    eje = rodilla - cadera
    largo = eje.length
    if largo < 1e-4:
        raise RuntimeError(f"Diagnóstico: el fémur {lado} no tiene longitud. No se pintó nada.")
    eje = eje / largo
    frente = anterior - eje * anterior.dot(eje)
    if frente.length < 1e-5:
        raise RuntimeError(f"Diagnóstico: el frente del muslo {lado} no se puede separar del fémur.")
    frente.normalize()
    afuera = Vector((1.0 if cadera.x >= 0 else -1.0, 0.0, 0.0))
    lateral = eje.cross(frente)
    if lateral.dot(afuera) < 0:
        lateral.negate()
    lateral.normalize()
    return {"lado": lado, "cadera": cadera, "largo": largo, "eje": eje, "frente": frente, "lateral": lateral}


def medida(punto, regla):
    delta = punto - regla["cadera"]
    recorrido = delta.dot(regla["eje"])
    radial = delta - regla["eje"] * recorrido
    return recorrido / regla["largo"], radial


def limite_de_radio(vertices, indices, regla):
    radios = []
    for indice in indices:
        t, radial = medida(vertices[indice].co, regla)
        if 0.40 <= t <= 0.62 and radial.length > 1e-4 and radial.angle(regla["frente"]) <= math.radians(70):
            radios.append(radial.length)
    if len(radios) < 20:
        raise RuntimeError(
            f"Diagnóstico: el muslo {regla['lado']} no tiene bastante superficie frontal. No se pintó nada."
        )
    radios.sort()
    return radios[int((len(radios) - 1) * 0.95)] * 1.12


def fuera_de_la_ingle(punto, regla):
    # El pubis está en el centro. Los cuádriceps no se tocan entre las piernas.
    if punto.x * regla["cadera"].x <= 0.0:
        return False
    return abs(punto.x) >= abs(regla["cadera"].x) * 0.42


def vertice_en_cuadriceps(punto, regla, radio_max):
    t, radial = medida(punto, regla)
    if not fuera_de_la_ingle(punto, regla):
        return False
    if t < T_MIN or t > T_MAX or radial.length < 1e-4 or radial.length > radio_max:
        return False
    if radial.angle(regla["frente"]) > ANGULO_MAX:
        return False
    adelante = radial.dot(regla["frente"])
    lateral = radial.dot(regla["lateral"])
    # La ingle interna queda fuera. Cerca de la rodilla se admite el vasto medial.
    margen = 1.25 if t > 0.68 else 0.9
    if lateral < 0.0 and adelante < abs(lateral) * margen:
        return False
    return True


def construir_mascara(obj, arm):
    visibles = vertices_visibles(obj)
    anterior = dirección_anterior(arm, obj)
    reglas = [regla_muslo(arm, obj, lado, anterior) for lado in ("L", "R")]
    vertices = obj.data.vertices
    radios = {regla["lado"]: limite_de_radio(vertices, visibles, regla) for regla in reglas}
    por_lado = {"L": set(), "R": set()}
    for indice in visibles:
        punto = vertices[indice].co
        elegido = min(reglas, key=lambda regla: (punto - regla["cadera"]).length)
        if vertice_en_cuadriceps(punto, elegido, radios[elegido["lado"]]):
            por_lado[elegido["lado"]].add(indice)

    caras = {"L": [], "R": []}
    reglas_por_cara = {}
    for cara in obj.data.polygons:
        if not all(indice in visibles for indice in cara.vertices):
            continue
        centro = sum((vertices[indice].co for indice in cara.vertices), Vector()) / len(cara.vertices)
        elegido = min(reglas, key=lambda regla: (centro - regla["cadera"]).length)
        votos = sum(1 for indice in cara.vertices if indice in por_lado[elegido["lado"]])
        if votos >= max(2, len(cara.vertices) // 2) or vertice_en_cuadriceps(
            centro, elegido, radios[elegido["lado"]]
        ):
            caras[elegido["lado"]].append(cara.index)
            reglas_por_cara[cara.index] = elegido

    caras = cerrar_huecos(obj, caras, reglas_por_cara, radios)
    for lado in ("L", "R"):
        por_lado[lado] = {
            indice
            for cara in caras[lado]
            for indice in obj.data.polygons[cara].vertices
        }
    return por_lado, caras, radios, anterior


def cerrar_huecos(obj, caras, reglas_por_cara, radios):
    vecinos = {}
    for cara in obj.data.polygons:
        puntos = cara.vertices
        for indice in range(len(puntos)):
            arista = tuple(sorted((puntos[indice], puntos[(indice + 1) % len(puntos)])))
            vecinos.setdefault(arista, []).append(cara.index)
    adyacencia = {cara.index: set() for cara in obj.data.polygons}
    for pares in vecinos.values():
        if len(pares) == 2:
            adyacencia[pares[0]].add(pares[1])
            adyacencia[pares[1]].add(pares[0])

    incluidas = set(caras["L"]) | set(caras["R"])
    extra = []
    for indice in list(incluidas):
        for vecino in adyacencia[indice]:
            if vecino in incluidas:
                continue
            cara = obj.data.polygons[vecino]
            centro = sum((obj.data.vertices[v].co for v in cara.vertices), Vector()) / len(cara.vertices)
            regla = reglas_por_cara[indice]
            t, radial = medida(centro, regla)
            if not fuera_de_la_ingle(centro, regla):
                continue
            if radial.length < 1e-4 or radial.length > radios[regla["lado"]]:
                continue
            if T_MIN - 0.03 <= t <= T_MAX + 0.02 and radial.angle(regla["frente"]) <= ANGULO_MAX + math.radians(8):
                extra.append((vecino, regla))
    for indice, regla in extra:
        if indice not in incluidas:
            caras[regla["lado"]].append(indice)
            incluidas.add(indice)
            reglas_por_cara[indice] = regla

    for lado in ("L", "R"):
        conjunto = set(caras[lado])
        caras[lado] = [
            indice
            for indice in conjunto
            if any(vecino in conjunto for vecino in adyacencia[indice])
        ]
    return caras


def guardar_grupos(obj, por_lado):
    for lado, indices in por_lado.items():
        nombre = f"mascara_cuadriceps.{lado}"
        previo = obj.vertex_groups.get(nombre)
        if previo is not None:
            obj.vertex_groups.remove(previo)
        grupo = obj.vertex_groups.new(name=nombre)
        if indices:
            grupo.add(sorted(indices), 1.0, "REPLACE")


def asignar_materiales(obj, caras):
    preparar_materiales(obj)
    indices = [0] * len(obj.data.polygons)
    for lado in caras.values():
        for indice in lado:
            indices[indice] = 1
    obj.data.polygons.foreach_set("material_index", indices)
    obj.data.update()


def main():
    salida = exigir_origen()
    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    if arm is None:
        raise RuntimeError("Diagnóstico: no hay armadura. No se pintó nada.")
    exigir_huesos(arm)
    malla = next((obj for obj in bpy.data.objects if obj.type == "MESH" and obj.parent == arm), None)
    if malla is None:
        raise RuntimeError("Diagnóstico: la armadura no tiene una malla hija. No se pintó nada.")

    por_lado, caras, radios, anterior = construir_mascara(malla, arm)
    total = len(caras["L"]) + len(caras["R"])
    if len(caras["L"]) < 40 or len(caras["R"]) < 40:
        raise RuntimeError(
            "Diagnóstico: la región automática quedó demasiado pequeña "
            f"(L={len(caras['L'])}, R={len(caras['R'])}). No se guardó el archivo."
        )

    guardar_grupos(malla, por_lado)
    asignar_materiales(malla, caras)
    bpy.context.scene.frame_set(1)

    mascara = {
        "origen": "automatica",
        "malla": malla.name,
        "grupo_muscular": "cuadriceps",
        "material": "MUSCLE_ACTIVE",
        "caras": sorted(caras["L"] + caras["R"]),
        "lados": {lado: sorted(indices) for lado, indices in caras.items()},
        "nota": (
            "Propuesta geométrica del frente del muslo. No separa recto femoral "
            "ni vastos, e incluye parte del sartorio. Hay que revisarla."
        ),
    }
    carpeta_mascara = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mascaras")
    os.makedirs(carpeta_mascara, exist_ok=True)
    ruta_mascara = os.path.join(carpeta_mascara, "cuadriceps.json")
    with open(ruta_mascara, "w", encoding="utf-8") as archivo:
        json.dump(mascara, archivo, ensure_ascii=False, indent=2)

    informe = {
        "archivo_origen": bpy.data.filepath,
        "archivo_salida": salida,
        "armadura": arm.name,
        "malla": malla.name,
        "accion_conservada": (
            arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None
        ),
        "materiales": ["BODY_BASE", "MUSCLE_ACTIVE", "MUSCLE_SECONDARY"],
        "colores": {"BODY_BASE": "#B7B9BE", "MUSCLE_ACTIVE": "#13B8A6", "MUSCLE_SECONDARY": "#2ECC71"},
        "caras_total": len(malla.data.polygons),
        "caras_cuadriceps": {"L": len(caras["L"]), "R": len(caras["R"]), "total": total},
        "vertices_mascara": {"L": len(por_lado["L"]), "R": len(por_lado["R"])},
        "radio_max_m": {lado: round(valor, 5) for lado, valor in radios.items()},
        "frente_local": [round(valor, 5) for valor in anterior],
        "parametros": {
            "t_min": T_MIN,
            "t_max": T_MAX,
            "angulo_max_grados": round(math.degrees(ANGULO_MAX)),
        },
        "huesos_usados_como_regla": ["upperleg01.L", "upperleg01.R", "lowerleg01.L", "lowerleg01.R"],
        "pesos_de_deformacion_modificados": False,
        "mascara": ruta_mascara,
        "revision": (
            "La piel no tiene un borde de cuádriceps. Esta región es el frente del muslo "
            "entre la cadera y la rodilla. Conviene corregirla con guardar_mascara.py."
        ),
    }
    ruta_informe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuadriceps_report.json")
    with open(ruta_informe, "w", encoding="utf-8") as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)

    os.makedirs(os.path.dirname(salida), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=salida, copy=True)
    print("CUADRICEPS_OK", salida)
    print("CARAS", len(caras["L"]), len(caras["R"]))
    print("INFORME", ruta_informe)


if __name__ == "__main__":
    main()
