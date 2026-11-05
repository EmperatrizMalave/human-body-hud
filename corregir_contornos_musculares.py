# corregir_contornos_musculares.py
#
# Sustituye las líneas rectas del intento anterior por contornos curvos
# proyectados sobre la piel. No toca el rig, los pesos ni la malla original.
#
# Limitación: Ch36 / Avatar_Holograma es un cascarón continuo. No tiene
# cortes anatómicos. Estas curvas son una plantilla editable, no una
# medición de músculos reales. Se pueden mover en Edit Mode y volver a
# proyectar ejecutando este script.
#
# Grupos (el material se llama igual, para cambiar el color desde la web):
# pectoral_mayor, deltoides, biceps, triceps, recto_abdominal,
# oblicuos, dorsales, cuadriceps, isquiotibiales, gemelos.

import os
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


OFFSET = 0.62
GROSOR = 0.30
COLOR_LINEA = (0.50, 0.86, 0.94, 1.0)

GRUPOS = (
    "pectoral_mayor",
    "deltoides",
    "biceps",
    "triceps",
    "recto_abdominal",
    "oblicuos",
    "dorsales",
    "cuadriceps",
    "isquiotibiales",
    "gemelos",
)


def exigir_avatar():
    malla = bpy.data.objects.get("Avatar_Holograma")
    arm = bpy.data.objects.get("Armature_Holograma")
    if malla is None or arm is None:
        raise RuntimeError("Abre avatar_holografico.blend: faltan Avatar_Holograma o Armature_Holograma.")
    return malla, arm


def quitar_lineas_viejas():
    """Solo borra la malla decorativa del script anterior."""
    vieja = bpy.data.objects.get("Lineas_Anatomicas")
    if vieja is None:
        return
    datos = vieja.data
    bpy.data.objects.remove(vieja, do_unlink=True)
    if datos is not None and datos.users == 0:
        bpy.data.meshes.remove(datos)
    material = bpy.data.materials.get("M_Lineas_Anatomicas")
    if material is not None and material.users == 0:
        bpy.data.materials.remove(material)


def quitar_contornos_previos():
    for obj in list(bpy.data.objects):
        if obj.get("origen") == "contornos_musculares":
            datos = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if datos is not None and getattr(datos, "users", 1) == 0:
                if isinstance(datos, bpy.types.Mesh):
                    bpy.data.meshes.remove(datos)
                elif isinstance(datos, bpy.types.Curve):
                    bpy.data.curves.remove(datos)


def coleccion_grupo(nombre):
    padre = bpy.data.collections.get("DETALLES_ANATOMICOS")
    if padre is None:
        padre = bpy.data.collections.new("DETALLES_ANATOMICOS")
        bpy.context.scene.collection.children.link(padre)
    titulo = "Grupo_" + nombre
    for hijo in padre.children:
        if hijo.name == titulo:
            return hijo
    hijo = bpy.data.collections.new(titulo)
    padre.children.link(hijo)
    return hijo


def catmull(puntos, muestras):
    if len(puntos) < 2:
        return list(puntos)
    extendida = [puntos[0]] + list(puntos) + [puntos[-1]]
    salida = []
    tramos = len(puntos) - 1
    por_tramo = max(3, muestras // tramos)
    for i in range(tramos):
        p0, p1, p2, p3 = extendida[i], extendida[i + 1], extendida[i + 2], extendida[i + 3]
        pasos = por_tramo if i < tramos - 1 else por_tramo + 1
        for s in range(pasos):
            t = s / float(por_tramo)
            t2 = t * t
            t3 = t2 * t
            salida.append(0.5 * (
                (2.0 * p1)
                + (-p0 + p2) * t
                + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
            ))
    return salida


def proyectar(malla, guias, direccion, retroceso, muestras=16):
    """Curva suave, luego cada punto sale del interior hasta la piel."""
    direccion = direccion.normalized()
    puntos = []
    for guia in catmull(guias, muestras):
        acierto, lugar, normal, _indice = malla.ray_cast(guia - direccion * retroceso, direccion)
        if not acierto:
            continue
        if normal.dot(direccion) < 0.0:
            normal = -normal
        nuevo = lugar + normal.normalized() * OFFSET
        if puntos and (nuevo - puntos[-1]).length > 9.0:
            continue
        puntos.append(nuevo)
    return puntos


def tubo(puntos):
    lados = 4
    vertices = []
    caras = []
    for indice, punto in enumerate(puntos):
        if indice == 0:
            tangente = puntos[1] - punto
        elif indice == len(puntos) - 1:
            tangente = punto - puntos[indice - 1]
        else:
            tangente = puntos[indice + 1] - puntos[indice - 1]
        if tangente.length < 1e-6:
            continue
        tangente.normalize()
        apoyo = Vector((0.0, 1.0, 0.0)) if abs(tangente.y) < 0.92 else Vector((1.0, 0.0, 0.0))
        lado = tangente.cross(apoyo).normalized()
        normal = tangente.cross(lado).normalized()
        base = len(vertices)
        for k in range(lados):
            angulo = 2.0 * math.pi * k / lados
            vertices.append(punto + (lado * math.cos(angulo) + normal * math.sin(angulo)) * GROSOR)
        if indice:
            previo = base - lados
            for k in range(lados):
                a = previo + k
                b = previo + (k + 1) % lados
                c = base + (k + 1) % lados
                d = base + k
                caras.append((a, b, c, d))
    return vertices, caras


def material_grupo(grupo):
    nombre = "M_" + grupo
    mat = bpy.data.materials.get(nombre)
    if mat is None:
        mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nodos = mat.node_tree
    nodos.nodes.clear()
    salida = nodos.nodes.new("ShaderNodeOutputMaterial")
    salida.location = (360, 0)
    emision = nodos.nodes.new("ShaderNodeEmission")
    emision.location = (80, 0)
    emision.inputs["Color"].default_value = COLOR_LINEA
    emision.inputs["Strength"].default_value = 2.4
    nodos.links.new(emision.outputs["Emission"], salida.inputs["Surface"])
    mat["grupo_muscular"] = grupo
    return mat


def crear_curva(nombre, grupo, puntos, coleccion, arm, referencia):
    datos = bpy.data.curves.new(nombre, "CURVE")
    datos.dimensions = "3D"
    datos.resolution_u = 8
    datos.bevel_depth = 0.0
    spline = datos.splines.new("BEZIER")
    spline.bezier_points.add(len(puntos) - 1)
    for punto, destino in zip(spline.bezier_points, puntos):
        punto.co = destino
        punto.handle_left_type = "AUTO"
        punto.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(nombre, datos)
    coleccion.objects.link(obj)
    obj.parent = arm
    obj.matrix_parent_inverse = referencia.matrix_parent_inverse.copy()
    obj["origen"] = "contornos_musculares"
    obj["grupo_muscular"] = grupo
    obj["editable"] = 1
    obj.hide_render = True
    return obj


def crear_malla(nombre, grupo, puntos, coleccion, arm, referencia, material):
    vertices, caras = tubo(puntos)
    if len(caras) < 1:
        return None
    datos = bpy.data.meshes.new(nombre + "_Mesh")
    datos.from_pydata(vertices, [], caras)
    datos.update()
    obj = bpy.data.objects.new(nombre, datos)
    coleccion.objects.link(obj)
    obj.parent = arm
    obj.matrix_parent_inverse = referencia.matrix_parent_inverse.copy()
    obj.data.materials.append(material)
    obj["origen"] = "contornos_musculares"
    obj["grupo_muscular"] = grupo
    obj["lado_color"] = "material:" + material.name
    return obj


def seguir_cuerpo(obj, cuerpo):
    modificador = obj.modifiers.new("SeguirCuerpo", "SURFACE_DEFORM")
    modificador.target = cuerpo
    bpy.context.view_layer.update()
    try:
        with bpy.context.temp_override(object=obj, active_object=obj, selected_editable_objects=[obj]):
            bpy.ops.object.surfacedeform_bind(modifier=modificador.name)
        return modificador.is_bound if hasattr(modificador, "is_bound") else True
    except RuntimeError as exc:
        print("No se pudo pegar", obj.name, "a la piel:", exc)
        obj.modifiers.remove(modificador)
        return False


def espejo(punto, signo):
    return Vector((punto.x * signo, punto.y, punto.z))


def definir_contornos():
    """Puntos guía en el espacio local del maniquí. La curva se arquea y luego se proyecta."""
    frente = Vector((0.0, 0.0, 1.0))
    atras = Vector((0.0, 0.0, -1.0))
    contornos = []

    def ambos(grupo, guias, direccion, retroceso=5.0):
        for signo, lado in ((1.0, "L"), (-1.0, "R")):
            contornos.append({
                "grupo": grupo,
                "lado": lado,
                "guias": [espejo(p, signo) for p in guias],
                "direccion": Vector((direccion.x * signo, direccion.y, direccion.z)),
                "retroceso": retroceso,
            })

    ambos("pectoral_mayor", [
        Vector((1.6, 141.0, 7.0)),
        Vector((6.5, 135.0, 9.0)),
        Vector((12.5, 136.5, 7.5)),
        Vector((17.2, 141.8, 3.0)),
    ], frente, 6.0)
    ambos("pectoral_mayor", [
        Vector((2.0, 145.8, 5.5)),
        Vector((8.0, 146.6, 6.5)),
        Vector((15.0, 144.2, 3.5)),
    ], frente, 6.0)
    ambos("deltoides", [
        Vector((15.0, 144.2, 3.5)),
        Vector((17.5, 149.8, 1.5)),
        Vector((22.5, 147.5, -1.0)),
        Vector((19.5, 142.2, -5.2)),
    ], Vector((0.2, 0.6, 0.2)), 4.0)
    ambos("biceps", [
        Vector((23.0, 141.6, 2.2)),
        Vector((31.0, 139.2, 5.2)),
        Vector((39.0, 140.6, 3.6)),
        Vector((43.2, 141.3, 1.4)),
    ], frente, 3.5)
    ambos("triceps", [
        Vector((23.5, 142.4, -5.5)),
        Vector((32.0, 139.4, -7.6)),
        Vector((41.5, 141.0, -5.0)),
    ], atras, 3.5)
    ambos("oblicuos", [
        Vector((11.5, 133.0, 4.5)),
        Vector((15.0, 122.0, 6.5)),
        Vector((12.0, 110.0, 4.0)),
    ], Vector((0.7, 0.0, 0.7)), 5.0)
    ambos("dorsales", [
        Vector((6.5, 116.0, -5.5)),
        Vector((11.0, 128.0, -6.0)),
        Vector((15.5, 139.5, -3.0)),
    ], Vector((0.35, 0.0, -0.94)), 5.0)
    ambos("cuadriceps", [
        Vector((9.2, 90.0, 6.5)),
        Vector((11.5, 78.0, 8.5)),
        Vector((12.8, 66.0, 8.0)),
        Vector((13.2, 56.0, 5.5)),
    ], frente, 4.0)
    ambos("cuadriceps", [
        Vector((13.0, 88.0, 2.5)),
        Vector((16.2, 74.0, 3.5)),
        Vector((14.5, 58.0, 2.0)),
    ], Vector((0.85, 0.0, 0.45)), 4.0)
    ambos("isquiotibiales", [
        Vector((7.0, 90.0, -3.5)),
        Vector((8.5, 76.0, -6.5)),
        Vector((10.5, 62.0, -5.5)),
        Vector((11.5, 54.0, -3.5)),
    ], atras, 4.0)
    ambos("gemelos", [
        Vector((13.8, 47.5, -1.2)),
        Vector((15.8, 36.0, -4.8)),
        Vector((14.2, 24.0, -3.2)),
    ], atras, 3.5)
    ambos("gemelos", [
        Vector((10.2, 46.5, -2.0)),
        Vector((9.2, 34.0, -5.6)),
        Vector((11.2, 23.0, -3.0)),
    ], atras, 3.5)

    for y, panza in ((114.0, 1.3), (122.0, 1.6), (130.0, 1.4), (137.0, 0.8)):
        contornos.append({
            "grupo": "recto_abdominal",
            "lado": "C",
            "guias": [
                Vector((-6.5, y, 7.0)),
                Vector((0.0, y, 7.0 + panza)),
                Vector((6.5, y, 7.0)),
            ],
            "direccion": frente,
            "retroceso": 6.0,
        })
    contornos.append({
        "grupo": "recto_abdominal",
        "lado": "C",
        "guias": [
            Vector((0.0, 109.0, 7.5)),
            Vector((0.0, 124.0, 9.0)),
            Vector((0.0, 139.0, 7.0)),
        ],
        "direccion": frente,
        "retroceso": 6.0,
    })
    return contornos


def ajustar_material_cuerpo(malla):
    mat = malla.data.materials[0] if malla.data.materials else bpy.data.materials.new("M_Avatar_Holograma")
    if not malla.data.materials:
        malla.data.materials.append(mat)
    mat.use_nodes = True
    nodos = mat.node_tree
    nodos.nodes.clear()
    salida = nodos.nodes.new("ShaderNodeOutputMaterial")
    salida.location = (900, 40)
    bsdf = nodos.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 220)
    bsdf.inputs["Base Color"].default_value = (0.91, 0.93, 0.95, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.2
    bsdf.inputs["Roughness"].default_value = 0.34
    bsdf.inputs["Alpha"].default_value = 0.94
    bsdf.inputs["Emission Color"].default_value = (0.82, 0.91, 0.96, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.18
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.04
    borde = nodos.nodes.new("ShaderNodeEmission")
    borde.location = (200, -40)
    borde.inputs["Color"].default_value = (0.72, 0.90, 0.96, 1.0)
    borde.inputs["Strength"].default_value = 0.9
    peso = nodos.nodes.new("ShaderNodeLayerWeight")
    peso.location = (-280, -20)
    potencia = nodos.nodes.new("ShaderNodeMath")
    potencia.operation = "POWER"
    potencia.inputs[1].default_value = 4.0
    potencia.location = (-60, 20)
    nodos.links.new(peso.outputs["Facing"], potencia.inputs[0])
    invertir = nodos.nodes.new("ShaderNodeMath")
    invertir.operation = "SUBTRACT"
    invertir.inputs[0].default_value = 1.0
    invertir.location = (-60, -100)
    nodos.links.new(potencia.outputs["Value"], invertir.inputs[1])
    fuerza = nodos.nodes.new("ShaderNodeMath")
    fuerza.operation = "MULTIPLY"
    fuerza.inputs[1].default_value = 0.42
    fuerza.location = (140, -120)
    nodos.links.new(invertir.outputs["Value"], fuerza.inputs[0])
    malla_nodo = nodos.nodes.new("ShaderNodeWireframe")
    malla_nodo.use_pixel_size = True
    malla_nodo.inputs["Size"].default_value = 0.4
    malla_nodo.location = (-280, -260)
    opacidad = nodos.nodes.new("ShaderNodeMath")
    opacidad.operation = "MULTIPLY"
    opacidad.inputs[1].default_value = 0.1
    opacidad.location = (-60, -260)
    nodos.links.new(malla_nodo.outputs["Fac"], opacidad.inputs[0])
    em_malla = nodos.nodes.new("ShaderNodeEmission")
    em_malla.inputs["Color"].default_value = (0.78, 0.9, 0.94, 1.0)
    em_malla.inputs["Strength"].default_value = 0.45
    em_malla.location = (200, -260)

    def mezclar(factor, a, b, x, y):
        nodo = nodos.nodes.new("ShaderNodeMixShader")
        nodo.location = (x, y)
        nodos.links.new(factor, nodo.inputs["Factor"])
        nodos.links.new(a, nodo.inputs[1])
        nodos.links.new(b, nodo.inputs[2])
        return nodo

    con_malla = mezclar(opacidad.outputs["Value"], bsdf.outputs["BSDF"], em_malla.outputs["Emission"], 520, 140)
    con_borde = mezclar(fuerza.outputs["Value"], con_malla.outputs["Shader"], borde.outputs["Emission"], 740, 40)
    nodos.links.new(con_borde.outputs["Shader"], salida.inputs["Surface"])
    mat.blend_method = "BLEND"
    mat.surface_render_method = "BLENDED"
    mat.use_transparent_shadow = False


def ajustar_luces():
    valores = {
        "Luz_Clave_Holo": (26.0, (1.0, 1.0, 1.0)),
        "Luz_Relleno_Holo": (8.0, (0.84, 0.91, 0.98)),
        "Luz_Borde_Holo": (9.0, (0.62, 0.84, 0.92)),
    }
    for nombre, (energia, color) in valores.items():
        obj = bpy.data.objects.get(nombre)
        if obj is None or obj.type != "LIGHT":
            continue
        obj.data.energy = energia
        obj.data.color = color
        obj.data.use_shadow = False


def render_y_guardar():
    escena = bpy.context.scene
    camara = bpy.data.objects.get("Cam_Avatar_Holo")
    if camara is not None:
        escena.camera = camara
    carpeta = os.path.dirname(bpy.data.filepath)
    escena.render.engine = "BLENDER_EEVEE"
    escena.render.resolution_x = 2048
    escena.render.resolution_y = 2048
    escena.render.resolution_percentage = 100
    escena.render.film_transparent = True
    escena.render.image_settings.media_type = "IMAGE"
    escena.render.image_settings.file_format = "PNG"
    escena.render.image_settings.color_mode = "RGBA"
    escena.render.filepath = os.path.join(carpeta, "avatar_anatomico.png")
    escena.render.use_compositing = False
    if hasattr(escena.eevee, "taa_render_samples"):
        escena.eevee.taa_render_samples = 24
    bpy.ops.render.render(write_still=True)
    destino = os.path.join(carpeta, "avatar_holografico_anatomico.blend")
    if os.path.abspath(destino) == os.path.abspath(bpy.data.filepath):
        raise RuntimeError("El destino coincide con el archivo abierto.")
    bpy.ops.wm.save_as_mainfile(filepath=destino)
    print("PNG", escena.render.filepath)
    print("Blend", destino)


def curvas_editables():
    return [obj for obj in bpy.data.objects if obj.type == "CURVE" and obj.get("origen") == "contornos_musculares"]


def puntos_de_curva(obj):
    puntos = []
    for spline in obj.data.splines:
        if spline.type != "BEZIER":
            continue
        for punto in spline.bezier_points:
            puntos.append(Vector(punto.co))
    return puntos


def quitar_solo_mallas():
    for obj in list(bpy.data.objects):
        if obj.type == "MESH" and obj.get("origen") == "contornos_musculares":
            datos = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if datos is not None and datos.users == 0:
                bpy.data.meshes.remove(datos)


def construir_desde_curvas(malla, arm):
    creados = 0
    for curva in curvas_editables():
        puntos = puntos_de_curva(curva)
        if len(puntos) < 4:
            continue
        grupo = curva.get("grupo_muscular", "contorno")
        coleccion = coleccion_grupo(grupo)
        nombre = curva.name.replace("Curva_", "", 1)
        obj = crear_malla(nombre, grupo, puntos, coleccion, arm, malla, material_grupo(grupo))
        if obj is None:
            continue
        if not seguir_cuerpo(obj, malla):
            print("Pendiente de deformación:", obj.name)
        creados += 1
    return creados


def main():
    if bpy.app.version < (4, 2, 0):
        raise RuntimeError("Hace falta Blender 4.2 o posterior.")
    malla, arm = exigir_avatar()
    arm.data.pose_position = "REST"
    quitar_lineas_viejas()
    ajustar_material_cuerpo(malla)
    ajustar_luces()

    if curvas_editables():
        quitar_solo_mallas()
        creados = construir_desde_curvas(malla, arm)
        print("Mallas reconstruidas desde las curvas editadas:", creados)
    else:
        quitar_contornos_previos()
        creados = 0
        for item in definir_contornos():
            puntos = proyectar(malla, item["guias"], item["direccion"], item["retroceso"])
            if len(puntos) < 4:
                print("Aviso: pocos puntos en", item["grupo"], item["lado"])
                continue
            coleccion = coleccion_grupo(item["grupo"])
            nombre = "Anat_{0}_{1}".format(item["grupo"], item["lado"])
            crear_curva("Curva_" + nombre, item["grupo"], puntos, coleccion, arm, malla)
            obj = crear_malla(nombre, item["grupo"], puntos, coleccion, arm, malla, material_grupo(item["grupo"]))
            if obj is None:
                continue
            if not seguir_cuerpo(obj, malla):
                print("Pendiente de deformación:", obj.name)
            creados += 1
        print("Contornos creados:", creados)
    print("Materiales web:", ", ".join("M_" + g for g in GRUPOS))
    render_y_guardar()


if __name__ == "__main__":
    main()
