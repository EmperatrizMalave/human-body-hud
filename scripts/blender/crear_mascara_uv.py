# crear_mascara_uv.py
# Crea una máscara UV en escala de grises para ambos cuádriceps y un solo
# material que la usa como factor. No asigna el músculo cara por cara.
# No cambia pesos, huesos, IK ni la acción. No sobrescribe el origen.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\crear_mascara_uv.py"
#
# Para volver a cargar un PNG editado a mano, sin reconstruir el material:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_muscular_uv_test.blend" `
#     --python "scripts\blender\crear_mascara_uv.py" `
#     -- recargar

import array
import json
import math
import os
import sys

import bpy
from mathutils import Vector


TAMANO = 2048
GRIS = (0.718, 0.725, 0.745, 1.0)
TURQUESA = (19 / 255, 184 / 255, 166 / 255, 1.0)
HUESOS = ("upperleg01.L", "upperleg01.R", "lowerleg01.L", "lowerleg01.R")


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def ruta_png():
    return os.path.join(carpeta_proyecto(), "assets", "textures", "mascara_cuadriceps.png")


def ruta_blend():
    return os.path.join(carpeta_proyecto(), "assets", "models", "personaje_muscular_uv_test.blend")


def argumentos():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def suave(valor, inicio, fin):
    if fin <= inicio:
        return 1.0 if valor >= fin else 0.0
    if valor <= inicio:
        return 0.0
    if valor >= fin:
        return 1.0
    t = (valor - inicio) / (fin - inicio)
    return t * t * (3.0 - 2.0 * t)


def banda(valor, inicio, fin, borde):
    return suave(valor, inicio, inicio + borde) * (1.0 - suave(valor, fin - borde, fin))


def exigir_huesos(arm):
    faltan = [nombre for nombre in HUESOS if nombre not in arm.data.bones]
    if faltan:
        raise RuntimeError("Diagnóstico: faltan huesos y no se creó la máscara: " + ", ".join(faltan))


def local_de_hueso(arm, malla, nombre):
    hueso = arm.data.bones[nombre]
    return malla.matrix_world.inverted() @ (arm.matrix_world @ hueso.head_local)


def vertices_visibles(obj):
    grupo = obj.vertex_groups.get("body")
    if grupo is None:
        raise RuntimeError("Diagnóstico: no está el grupo visible 'body'. No se creó la máscara.")
    indice = grupo.index
    return {
        vertice.index
        for vertice in obj.data.vertices
        for asignacion in vertice.groups
        if asignacion.group == indice and asignacion.weight >= 0.5
    }


def regla_muslo(arm, malla, lado, anterior):
    cadera = local_de_hueso(arm, malla, f"upperleg01.{lado}")
    rodilla = local_de_hueso(arm, malla, f"lowerleg01.{lado}")
    eje = rodilla - cadera
    largo = eje.length
    if largo < 1e-4:
        raise RuntimeError(f"Diagnóstico: el fémur {lado} no tiene longitud.")
    eje = eje / largo
    frente = anterior - eje * anterior.dot(eje)
    if frente.length < 1e-5:
        raise RuntimeError(f"Diagnóstico: no se separa el frente del muslo {lado}.")
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
        raise RuntimeError("Diagnóstico: no se pudo medir la dirección de los pies.")
    return avance.normalized()


def peso_anatomico(punto, regla):
    delta = punto - regla["cadera"]
    recorrido = delta.dot(regla["eje"])
    radial = delta - regla["eje"] * recorrido
    t = recorrido / regla["largo"]
    if radial.length < 1e-5 or radial.length > 0.12 or t < 0.02 or t > 1.05:
        return 0.0
    adelante = radial.dot(regla["frente"])
    if adelante <= 0.0:
        return 0.0
    angulo = math.atan2(radial.dot(regla["lateral"]), adelante)
    recto = banda(t, 0.10, 0.90, 0.12) * banda(angulo, -0.62, 0.48, 0.28)
    lateral = banda(t, 0.12, 0.88, 0.12) * banda(angulo, 0.02, 1.18, 0.30)
    medial = banda(t, 0.52, 0.99, 0.14) * banda(angulo, -1.22, -0.04, 0.28)
    limite = abs(regla["cadera"].x) * 0.36
    ingle = suave(abs(punto.x), limite, limite + 0.035)
    return max(0.0, min(1.0, max(recto, lateral, medial) * ingle))


def suavizar_campo(malla, pesos, pasos=3):
    vecinos = [[] for _ in malla.vertices]
    for cara in malla.polygons:
        puntos = cara.vertices
        for i, origen in enumerate(puntos):
            destino = puntos[(i + 1) % len(puntos)]
            vecinos[origen].append(destino)
            vecinos[destino].append(origen)
    actual = list(pesos)
    for _ in range(pasos):
        nuevo = actual[:]
        for indice, adyacentes in enumerate(vecinos):
            if not adyacentes or actual[indice] <= 0.0 and all(actual[v] <= 0.0 for v in adyacentes):
                continue
            promedio = sum(actual[v] for v in adyacentes) / len(adyacentes)
            nuevo[indice] = actual[indice] * 0.62 + promedio * 0.38
        actual = nuevo
    return actual


def rasterizar(malla, uv, pesos, visibles):
    tamano = TAMANO
    buffer = array.array("f", [0.0]) * (tamano * tamano)
    pixeles = 0

    def area(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def triangulo(indices, bucles):
        nonlocal pixeles
        puntos = []
        for vertice, bucle in zip(indices, bucles):
            coord = uv.uv[bucle].vector
            puntos.append((coord.x * (tamano - 1), coord.y * (tamano - 1), pesos[vertice]))
        if max(p[0] for p in puntos) - min(p[0] for p in puntos) > tamano * 0.35:
            return
        if max(p[1] for p in puntos) - min(p[1] for p in puntos) > tamano * 0.35:
            return
        a, b, c = puntos
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
                if wa < -0.002 or wb < -0.002 or wc < -0.002:
                    continue
                valor = wa * a[2] + wb * b[2] + wc * c[2]
                if valor <= 0.004:
                    continue
                pos = y * tamano + x
                if valor > buffer[pos]:
                    buffer[pos] = valor
                    pixeles += 1

    for cara in malla.polygons:
        if not all(indice in visibles for indice in cara.vertices):
            continue
        if max(pesos[indice] for indice in cara.vertices) <= 0.004:
            continue
        verts = list(cara.vertices)
        loops = list(cara.loop_indices)
        if len(verts) == 3:
            triangulo(verts, loops)
        elif len(verts) >= 4:
            for i in range(1, len(verts) - 1):
                triangulo(
                    [verts[0], verts[i], verts[i + 1]],
                    [loops[0], loops[i], loops[i + 1]],
                )
    return buffer, pixeles


def desenfocar(buffer, radio=5):
    tamano = TAMANO
    xs = [i % tamano for i, valor in enumerate(buffer) if valor > 0.01]
    ys = [i // tamano for i, valor in enumerate(buffer) if valor > 0.01]
    if not xs:
        return
    minx = max(0, min(xs) - radio)
    maxx = min(tamano - 1, max(xs) + radio)
    miny = max(0, min(ys) - radio)
    maxy = min(tamano - 1, max(ys) + radio)
    origen = array.array("f", buffer)
    for y in range(miny, maxy + 1):
        fila = y * tamano
        for x in range(minx, maxx + 1):
            total = 0.0
            cuenta = 0
            for dx in range(-radio, radio + 1):
                xx = x + dx
                if 0 <= xx < tamano:
                    total += origen[fila + xx]
                    cuenta += 1
            buffer[fila + x] = total / cuenta
    origen = array.array("f", buffer)
    for x in range(minx, maxx + 1):
        for y in range(miny, maxy + 1):
            total = 0.0
            cuenta = 0
            for dy in range(-radio, radio + 1):
                yy = y + dy
                if 0 <= yy < tamano:
                    total += origen[yy * tamano + x]
                    cuenta += 1
            buffer[y * tamano + x] = total / cuenta


def guardar_png(buffer, ruta):
    import struct
    import zlib

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
            + bytes(
                max(0, min(255, int(buffer[base + x] * 255 + 0.5)))
                for x in range(ancho)
            )
        )
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(filas), 6))
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as archivo:
        archivo.write(png)


def escribir_imagen(buffer):
    imagen = bpy.data.images.get("MascaraCuadriceps")
    if imagen is not None and (imagen.size[0] != TAMANO or imagen.size[1] != TAMANO):
        bpy.data.images.remove(imagen)
        imagen = None
    if imagen is None:
        imagen = bpy.data.images.new("MascaraCuadriceps", TAMANO, TAMANO, alpha=True)
    maximo = max(buffer)
    if maximo <= 0.01:
        raise RuntimeError("Diagnóstico: la máscara quedó vacía. No se guardó el archivo.")
    guardar_png(buffer, ruta_png())
    imagen.filepath = ruta_png()
    imagen.source = "FILE"
    imagen.reload()
    imagen.colorspace_settings.name = "Non-Color"
    imagen.pack()
    print("MASCARA_MAX", round(maximo, 4))
    return imagen


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
    textura.name = "MascaraCuadriceps"
    textura.label = "MascaraCuadriceps"
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


def aplicar_material_unico(obj, material):
    while obj.data.materials:
        obj.data.materials.pop(index=0)
    obj.data.materials.append(material)
    indices = [0] * len(obj.data.polygons)
    obj.data.polygons.foreach_set("material_index", indices)


def costuras_del_muslo(obj, uv, reglas):
    malla = obj.data
    dentro = set()
    for vertice in malla.vertices:
        for regla in reglas:
            delta = vertice.co - regla["cadera"]
            recorrido = delta.dot(regla["eje"])
            radial = (delta - regla["eje"] * recorrido).length
            t = recorrido / regla["largo"]
            if 0.2 <= t <= 0.8 and radial < 0.1:
                dentro.add(vertice.index)
                break
    aristas = {}
    for cara in malla.polygons:
        puntos = cara.vertices
        bucles = cara.loop_indices
        for i in range(len(puntos)):
            a = puntos[i]
            b = puntos[(i + 1) % len(puntos)]
            if a not in dentro or b not in dentro:
                continue
            clave = tuple(sorted((a, b)))
            coord = tuple(
                sorted(
                    (
                        tuple(round(v, 4) for v in uv.uv[bucles[i]].vector),
                        tuple(round(v, 4) for v in uv.uv[bucles[(i + 1) % len(puntos)]].vector),
                    )
                )
            )
            aristas.setdefault(clave, set()).add(coord)
    return sum(1 for pares in aristas.values() if len(pares) > 1), len(dentro)


def error_de_simetria(malla, pesos):
    por_lado = {}
    for vertice in malla.vertices:
        if abs(vertice.co.x) < 0.05 or pesos[vertice.index] <= 0.02:
            continue
        clave = (round(abs(vertice.co.x), 3), round(vertice.co.y, 3), round(vertice.co.z, 3))
        por_lado.setdefault(clave, []).append(pesos[vertice.index])
    diferencias = [max(valores) - min(valores) for valores in por_lado.values() if len(valores) >= 2]
    if not diferencias:
        return None
    diferencias.sort()
    return round(diferencias[int((len(diferencias) - 1) * 0.95)], 4)


def crear():
    if os.path.abspath(bpy.data.filepath) == os.path.abspath(ruta_blend()):
        raise RuntimeError("Abre el modelo de origen, no el archivo UV de prueba.")
    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    cuerpo = bpy.data.objects.get("Human")
    if arm is None or cuerpo is None or cuerpo.type != "MESH":
        raise RuntimeError("Diagnóstico: no están Human y su armadura.")
    exigir_huesos(arm)
    if "toe1-1.L" not in arm.data.bones or "foot.L" not in arm.data.bones:
        raise RuntimeError("Diagnóstico: faltan los huesos del pie para orientar el frente.")
    uv = cuerpo.data.uv_layers.active
    if uv is None:
        raise RuntimeError("Diagnóstico: Human no tiene mapa UV. No se puede crear la máscara.")

    anterior = direccion_anterior(arm, cuerpo)
    reglas = [regla_muslo(arm, cuerpo, lado, anterior) for lado in ("L", "R")]
    visibles = vertices_visibles(cuerpo)
    pesos = [0.0] * len(cuerpo.data.vertices)
    for indice in visibles:
        punto = cuerpo.data.vertices[indice].co
        regla = min(reglas, key=lambda item: (punto - item["cadera"]).length)
        pesos[indice] = peso_anatomico(punto, regla)
    pesos = suavizar_campo(cuerpo.data, pesos, 4)
    if sum(1 for valor in pesos if valor > 0.2) < 80:
        raise RuntimeError("Diagnóstico: la máscara quedó casi vacía. No se guardó el archivo.")

    buffer, pixeles = rasterizar(cuerpo.data, uv, pesos, visibles)
    desenfocar(buffer, 7)
    imagen = escribir_imagen(buffer)
    material = construir_material(imagen)
    aplicar_material_unico(cuerpo, material)
    bpy.context.scene.frame_set(1)

    costuras, verts_muslo = costuras_del_muslo(cuerpo, uv, reglas)
    informe = {
        "archivo_origen": bpy.data.filepath,
        "archivo_salida": ruta_blend(),
        "textura": ruta_png(),
        "imagen": imagen.name,
        "material": material.name,
        "uv": uv.name,
        "accion_conservada": (
            arm.animation_data.action.name if arm.animation_data and arm.animation_data.action else None
        ),
        "pixeles_con_musculo": pixeles,
        "costuras_uv_en_el_muslo": costuras,
        "vertices_del_tubo": verts_muslo,
        "simetria_diferencia_p95": error_de_simetria(cuerpo.data, pesos),
        "pesos_de_deformacion_modificados": False,
        "delimitacion": "textura UV continua, no materiales por cara",
        "cabezas_aproximadas": ["recto femoral", "vasto lateral", "vasto medial"],
        "limitacion": (
            "La forma sale de un campo suave sobre el muslo. Los huesos solo orientan "
            "el eje. No marca inserciones reales ni separa las tres cabezas con colores distintos. "
            "El borde se corrige pintando MascaraCuadriceps, sin reconstruir el material."
        ),
    }
    destino_informe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uv_mask_report.json")
    with open(destino_informe, "w", encoding="utf-8") as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(ruta_blend()), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=ruta_blend(), copy=True)
    print("MASCARA_UV_OK", ruta_blend())
    print("COSTURAS_MUSLO", costuras, "SIMETRIA", informe["simetria_diferencia_p95"])


def recargar():
    if os.path.basename(bpy.data.filepath) != "personaje_muscular_uv_test.blend":
        raise RuntimeError("Abre personaje_muscular_uv_test.blend para recargar la máscara.")
    imagen = bpy.data.images.get("MascaraCuadriceps")
    material = bpy.data.materials.get("CuerpoMuscular")
    if imagen is None or material is None:
        raise RuntimeError("El material o la imagen no están. No se reconstruyó nada.")
    if not os.path.isfile(ruta_png()):
        raise RuntimeError("No existe assets/textures/mascara_cuadriceps.png.")
    imagen.filepath = ruta_png()
    imagen.source = "FILE"
    imagen.reload()
    imagen.colorspace_settings.name = "Non-Color"
    bpy.ops.wm.save_mainfile()
    print("MASCARA_RECARGADA", ruta_png())


def main():
    if "recargar" in argumentos():
        recargar()
    else:
        crear()


if __name__ == "__main__":
    main()
