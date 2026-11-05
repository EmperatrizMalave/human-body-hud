# crear_mascara_uv_v2.py
# Tres formas de cuádriceps en una máscara UV de 2048.
# El borde es corto. Entre músculos queda una franja gris, no una línea negra.
# No cambia pesos, huesos, IK ni la acción. No sobrescribe el origen.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\crear_mascara_uv_v2.py"

import array
import json
import math
import os
import struct
import zlib

import bpy
from mathutils import Vector


TAMANO = 2048
AA_METROS = 0.0032
RADIO_ARCO = 0.08
GRIS = (0.718, 0.725, 0.745, 1.0)
TURQUESA = (19 / 255, 184 / 255, 166 / 255, 1.0)

# (t a lo largo del fémur, ángulo: + lateral, − medial) y radio transversal en metros.
# Son siluetas estilizadas. No son inserciones medidas sobre este cuerpo.
MUSCULOS = {
    "recto_femoral": {
        "linea": [(0.16, 0.0), (0.30, 0.02), (0.46, 0.01), (0.62, 0.0), (0.76, 0.0), (0.88, 0.0)],
        "radios": [0.009, 0.018, 0.026, 0.018, 0.012, 0.007],
    },
    "vasto_lateral": {
        "linea": [(0.14, 0.46), (0.28, 0.68), (0.46, 0.78), (0.64, 0.66), (0.80, 0.48), (0.90, 0.36)],
        "radios": [0.011, 0.020, 0.028, 0.022, 0.014, 0.009],
    },
    "vasto_medial": {
        "linea": [(0.60, -0.32), (0.72, -0.52), (0.82, -0.74), (0.90, -0.90), (0.96, -0.62)],
        "radios": [0.008, 0.015, 0.022, 0.026, 0.014],
    },
}


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def ruta_png():
    return os.path.join(carpeta_proyecto(), "assets", "textures", "mascara_cuadriceps_v2.png")


def ruta_blend():
    return os.path.join(carpeta_proyecto(), "assets", "models", "personaje_muscular_uv_v2.blend")


def suave(valor, inicio, fin):
    if valor <= inicio:
        return 0.0
    if valor >= fin:
        return 1.0
    t = (valor - inicio) / (fin - inicio)
    return t * t * (3.0 - 2.0 * t)


def holgura(t, angulo, largo, linea, radios):
    px = t * largo
    py = angulo * RADIO_ARCO
    mejor = -1.0
    for indice in range(len(linea) - 1):
        ax = linea[indice][0] * largo
        ay = linea[indice][1] * RADIO_ARCO
        bx = linea[indice + 1][0] * largo
        by = linea[indice + 1][1] * RADIO_ARCO
        abx = bx - ax
        aby = by - ay
        ab2 = abx * abx + aby * aby
        if ab2 < 1e-12:
            avance = 0.0
        else:
            avance = ((px - ax) * abx + (py - ay) * aby) / ab2
            avance = 0.0 if avance < 0.0 else (1.0 if avance > 1.0 else avance)
        dx = px - (ax + abx * avance)
        dy = py - (ay + aby * avance)
        distancia = math.sqrt(dx * dx + dy * dy)
        radio = radios[indice] * (1.0 - avance) + radios[indice + 1] * avance
        holg = radio - distancia
        if holg > mejor:
            mejor = holg
    return mejor


def peso_de_punto(t, angulo, largo):
    mejor = 0.0
    for musculo in MUSCULOS.values():
        holg = holgura(t, angulo, largo, musculo["linea"], musculo["radios"])
        mejor = max(mejor, suave(holg, 0.0, AA_METROS))
    return mejor


def local_de_hueso(arm, malla, nombre):
    hueso = arm.data.bones[nombre]
    return malla.matrix_world.inverted() @ (arm.matrix_world @ hueso.head_local)


def regla_muslo(arm, malla, lado, anterior):
    cadera = local_de_hueso(arm, malla, f"upperleg01.{lado}")
    rodilla = local_de_hueso(arm, malla, f"lowerleg01.{lado}")
    eje = rodilla - cadera
    largo = eje.length
    if largo < 1e-4:
        raise RuntimeError(f"Diagnóstico: el fémur {lado} no tiene longitud.")
    eje = eje / largo
    frente = anterior - eje * anterior.dot(eje)
    frente.normalize()
    afuera = Vector((1.0 if cadera.x >= 0.0 else -1.0, 0.0, 0.0))
    lateral = eje.cross(frente)
    if lateral.dot(afuera) < 0.0:
        lateral.negate()
    lateral.normalize()
    return {"lado": lado, "cadera": cadera, "largo": largo, "eje": eje, "frente": frente, "lateral": lateral}


def direccion_anterior(arm, malla):
    avance = Vector((0.0, 0.0, 0.0))
    for lado in ("L", "R"):
        avance += local_de_hueso(arm, malla, f"toe1-1.{lado}") - local_de_hueso(arm, malla, f"foot.{lado}")
    avance.z = 0.0
    if avance.length < 1e-6:
        raise RuntimeError("Diagnóstico: no se pudo orientar el frente del cuerpo.")
    return avance.normalized()


def coordenadas(punto, regla):
    delta = punto - regla["cadera"]
    recorrido = delta.dot(regla["eje"])
    radial = delta - regla["eje"] * recorrido
    if radial.length < 1e-5:
        return None
    adelante = radial.dot(regla["frente"])
    if adelante <= 0.002:
        return None
    t = recorrido / regla["largo"]
    if t < 0.08 or t > 1.02 or radial.length > 0.12:
        return None
    angulo = math.atan2(radial.dot(regla["lateral"]), adelante)
    return t, angulo


def campo(punto, reglas):
    regla = min(reglas, key=lambda item: (punto - item["cadera"]).length)
    coord = coordenadas(punto, regla)
    if coord is None:
        return 0.0
    return peso_de_punto(coord[0], coord[1], regla["largo"])


def vertices_visibles(obj):
    grupo = obj.vertex_groups.get("body")
    if grupo is None:
        raise RuntimeError("Diagnóstico: no está el grupo visible 'body'.")
    indice = grupo.index
    return {
        vertice.index
        for vertice in obj.data.vertices
        for asignacion in vertice.groups
        if asignacion.group == indice and asignacion.weight >= 0.5
    }


def rasterizar(malla, uv, visibles, reglas):
    tamano = TAMANO
    buffer = array.array("f", [0.0]) * (tamano * tamano)
    pixeles = 0

    def area(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def triangulo(indices, bucles):
        nonlocal pixeles
        muestras = []
        for vertice, bucle in zip(indices, bucles):
            coord = uv.uv[bucle].vector
            muestras.append((coord.x * (tamano - 1), coord.y * (tamano - 1), malla.vertices[vertice].co))
        if max(p[0] for p in muestras) - min(p[0] for p in muestras) > tamano * 0.35:
            return
        if max(p[1] for p in muestras) - min(p[1] for p in muestras) > tamano * 0.35:
            return
        a, b, c = muestras
        den = area(a, b, c)
        if abs(den) < 1e-6:
            return
        minx = max(0, int(min(a[0], b[0], c[0])))
        maxx = min(tamano - 1, int(max(a[0], b[0], c[0])) + 1)
        miny = max(0, int(min(a[1], b[1], c[1])))
        maxy = min(tamano - 1, int(max(a[1], b[1], c[1])) + 1)
        for y in range(miny, maxy + 1):
            for x in range(minx, maxx + 1):
                p = (x + 0.5, y + 0.5)
                wa = area(b, c, p) / den
                wb = area(c, a, p) / den
                wc = area(a, b, p) / den
                if wa < -0.001 or wb < -0.001 or wc < -0.001:
                    continue
                posicion = a[2] * wa + b[2] * wb + c[2] * wc
                valor = campo(posicion, reglas)
                if valor <= 0.02:
                    continue
                pos = y * tamano + x
                if valor > buffer[pos]:
                    buffer[pos] = valor
                    pixeles += 1

    for cara in malla.polygons:
        if not all(indice in visibles for indice in cara.vertices):
            continue
        if not any(coordenadas(malla.vertices[indice].co, min(reglas, key=lambda item: (malla.vertices[indice].co - item["cadera"]).length)) for indice in cara.vertices):
            continue
        verts = list(cara.vertices)
        loops = list(cara.loop_indices)
        if len(verts) < 3:
            continue
        for i in range(1, len(verts) - 1):
            triangulo([verts[0], verts[i], verts[i + 1]], [loops[0], loops[i], loops[i + 1]])
    return buffer, pixeles


def guardar_png(buffer, ruta):
    ancho = alto = TAMANO

    def chunk(etiqueta, datos):
        return (
            struct.pack(">I", len(datos))
            + etiqueta
            + datos
            + struct.pack(">I", zlib.crc32(etiqueta + datos) & 0xFFFFFFFF)
        )

    filas = []
    for y in range(alto - 1, -1, -1):
        base = y * ancho
        filas.append(
            b"\x00"
            + bytes(max(0, min(255, int(buffer[base + x] * 255 + 0.5))) for x in range(ancho))
        )
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(filas), 6))
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as archivo:
        archivo.write(png)


def construir_material(imagen):
    material = bpy.data.materials.get("CuerpoMuscular") or bpy.data.materials.new("CuerpoMuscular")
    material.use_nodes = True
    material.diffuse_color = GRIS
    nodos = material.node_tree.nodes
    enlaces = material.node_tree.links
    for nodo in list(nodos):
        nodos.remove(nodo)
    salida = nodos.new("ShaderNodeOutputMaterial")
    salida.location = (700, 0)
    bsdf = nodos.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (420, 0)
    bsdf.inputs["Roughness"].default_value = 0.48
    bsdf.inputs["Metallic"].default_value = 0.0
    mezcla = nodos.new("ShaderNodeMix")
    mezcla.data_type = "RGBA"
    mezcla.blend_type = "MIX"
    mezcla.name = "MezclaMuscular"
    mezcla.location = (140, 0)
    base = nodos.new("ShaderNodeRGB")
    base.name = "BODY_BASE"
    base.label = "BODY_BASE"
    base.location = (-160, -80)
    base.outputs[0].default_value = GRIS
    activo = nodos.new("ShaderNodeRGB")
    activo.name = "MUSCLE_ACTIVE"
    activo.label = "MUSCLE_ACTIVE"
    activo.location = (-160, 80)
    activo.outputs[0].default_value = TURQUESA
    textura = nodos.new("ShaderNodeTexImage")
    textura.name = "MascaraCuadricepsV2"
    textura.label = "MascaraCuadricepsV2"
    textura.location = (-520, -40)
    textura.image = imagen
    textura.interpolation = "Linear"
    mapa = nodos.new("ShaderNodeUVMap")
    mapa.uv_map = "UVMap"
    mapa.location = (-760, -40)
    separar = nodos.new("ShaderNodeSeparateColor")
    separar.location = (-220, -180)
    enlaces.new(mapa.outputs["UV"], textura.inputs["Vector"])
    enlaces.new(textura.outputs["Color"], separar.inputs["Color"])
    enlaces.new(separar.outputs["Red"], mezcla.inputs["Factor"])
    enlaces.new(base.outputs["Color"], mezcla.inputs["A"])
    enlaces.new(activo.outputs["Color"], mezcla.inputs["B"])
    enlaces.new(mezcla.outputs["Result"], bsdf.inputs["Base Color"])
    enlaces.new(bsdf.outputs["BSDF"], salida.inputs["Surface"])
    return material


def main():
    if os.path.abspath(bpy.data.filepath) == os.path.abspath(ruta_blend()):
        raise RuntimeError("Abre el modelo de origen, no el archivo v2.")
    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    cuerpo = bpy.data.objects.get("Human")
    if arm is None or cuerpo is None or cuerpo.type != "MESH":
        raise RuntimeError("Diagnóstico: no están Human y su armadura.")
    for nombre in ("upperleg01.L", "upperleg01.R", "lowerleg01.L", "lowerleg01.R", "foot.L", "toe1-1.L"):
        if nombre not in arm.data.bones:
            raise RuntimeError("Diagnóstico: falta el hueso " + nombre + ". No se creó la máscara.")
    uv = cuerpo.data.uv_layers.active
    if uv is None:
        raise RuntimeError("Diagnóstico: Human no tiene UVMap.")

    anterior = direccion_anterior(arm, cuerpo)
    reglas = [regla_muslo(arm, cuerpo, lado, anterior) for lado in ("L", "R")]
    buffer, pixeles = rasterizar(cuerpo.data, uv, vertices_visibles(cuerpo), reglas)
    maximo = max(buffer)
    if maximo < 0.8 or pixeles < 1000:
        raise RuntimeError(
            "Diagnóstico: la máscara no cubre las tres formas. No se guardó el archivo. "
            f"max={maximo:.3f} pixeles={pixeles}"
        )
    guardar_png(buffer, ruta_png())
    imagen = bpy.data.images.get("MascaraCuadricepsV2")
    if imagen is not None and tuple(imagen.size) != (TAMANO, TAMANO):
        bpy.data.images.remove(imagen)
        imagen = None
    if imagen is None:
        imagen = bpy.data.images.new("MascaraCuadricepsV2", TAMANO, TAMANO, alpha=True)
    imagen.filepath = ruta_png()
    imagen.source = "FILE"
    imagen.reload()
    imagen.colorspace_settings.name = "Non-Color"
    imagen.pack()

    material = construir_material(imagen)
    while cuerpo.data.materials:
        cuerpo.data.materials.pop(index=0)
    cuerpo.data.materials.append(material)
    cuerpo.data.polygons.foreach_set("material_index", [0] * len(cuerpo.data.polygons))
    bpy.context.scene.frame_set(1)

    informe = {
        "archivo_origen": bpy.data.filepath,
        "archivo_salida": ruta_blend(),
        "textura": ruta_png(),
        "imagen": imagen.name,
        "material": material.name,
        "resolucion": [TAMANO, TAMANO],
        "pixeles_con_musculo": pixeles,
        "antialiasing_mm": AA_METROS * 1000,
        "accion_conservada": (
            arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None
        ),
        "pesos_de_deformacion_modificados": False,
        "musculos": MUSCULOS,
        "separacion": "Franja del gris del cuerpo entre formas. No hay línea negra.",
        "limitacion": (
            "Las siluetas están medidas sobre el eje del fémur, no sobre inserciones reales. "
            "Sirven como plantilla. Se corrigen una sola vez pintando MascaraCuadricepsV2."
        ),
    }
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uv_mask_v2_report.json")
    with open(destino, "w", encoding="utf-8") as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(ruta_blend()), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=ruta_blend(), copy=True)
    print("MASCARA_V2_OK", ruta_blend(), "PIXELS", pixeles, "MAX", round(maximo, 3))


if __name__ == "__main__":
    main()
