# crear_avatar_holografico.py
#
# Crea una copia holográfica del avatar que esté seleccionado y visible.
# No borra geometría, no cambia proporciones y no sobrescribe el .blend de origen.
#
# Limitación anatómica:
# este maniquí no tiene segmentos de músculo. Sus vertex groups son huesos
# de Mixamo (mixamorig). Las líneas cian son una aproximación visual apoyada
# en esos huesos, no una reconstrucción anatómica automática.
#
# Cómo ejecutarlo:
# 1. Abre el .blend en Blender.
# 2. Selecciona el cuerpo y su armature.
# 3. Ve al espacio Scripting, abre este archivo y pulsa Run Script.
# 4. El resultado queda en avatar_holografico.blend, junto al archivo de origen.

import os
import math

import bpy
from mathutils import Vector


VERSION_MINIMA = (4, 2, 0)
RADIO_LINEA = 0.42  # unidades locales del maniquí; en el mundo son unos 4 mm
COLOR_PERLA = (0.953, 0.965, 0.976, 1.0)
COLOR_CIAN = (0.55, 0.90, 0.96, 1.0)
COLOR_HIELO = (0.78, 0.94, 0.98, 1.0)


def comprobar_version():
    if bpy.app.version < VERSION_MINIMA:
        raise RuntimeError(
            "Hace falta Blender {0}.{1} o posterior. Esta sesión es {2}.".format(
                VERSION_MINIMA[0], VERSION_MINIMA[1], bpy.app.version_string
            )
        )


def coleccion(nombre):
    existente = bpy.data.collections.get(nombre)
    if existente is not None:
        raise RuntimeError(
            "La colección '{0}' ya existe. Abre de nuevo el .blend original antes de repetir el script.".format(nombre)
        )
    col = bpy.data.collections.new(nombre)
    bpy.context.scene.collection.children.link(col)
    return col


def mover_a(obj, destino):
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    destino.objects.link(obj)


def hueso(arm, sufijo):
    for bone in arm.data.bones:
        if bone.name.split(":")[-1] == sufijo:
            return bone
    return None


def encontrar_avatar():
    """Usa el armature activo si tiene una malla visible. Si no, la malla visible más grande."""
    activo = bpy.context.view_layer.objects.active
    if activo is not None:
        if activo.type == "ARMATURE":
            for hijo in activo.children:
                if hijo.type == "MESH" and any(m.type == "ARMATURE" for m in hijo.modifiers):
                    if not hijo.hide_get():
                        return hijo, activo
        if activo.type == "MESH":
            for mod in activo.modifiers:
                if mod.type == "ARMATURE" and mod.object is not None and not activo.hide_get():
                    return activo, mod.object

    mejor = None
    for obj in bpy.context.view_layer.objects:
        if obj.type != "MESH" or obj.hide_get():
            continue
        for mod in obj.modifiers:
            if mod.type == "ARMATURE" and mod.object is not None:
                tam = len(obj.data.vertices)
                if mejor is None or tam > mejor[0]:
                    mejor = (tam, obj, mod.object)
    if mejor is None:
        raise RuntimeError(
            "No hay un avatar visible con armature. Selecciona el cuerpo y vuelve a ejecutar el script."
        )
    return mejor[1], mejor[2]


def duplicar(obj, destino, nombre):
    copia = obj.copy()
    if obj.data is not None:
        copia.data = obj.data.copy()
    copia.name = nombre
    destino.objects.link(copia)
    return copia


def preparar_copia(malla, arm, col_holograma):
    nuevo_arm = duplicar(arm, col_holograma, "Armature_Holograma")
    nueva_malla = duplicar(malla, col_holograma, "Avatar_Holograma")
    nueva_malla.parent = nuevo_arm
    nueva_malla.matrix_parent_inverse = malla.matrix_parent_inverse.copy()
    for mod in nueva_malla.modifiers:
        if mod.type == "ARMATURE":
            mod.object = nuevo_arm
    for obj in (nueva_malla, nuevo_arm):
        obj.hide_set(False)
        obj.hide_render = False
        obj.hide_viewport = False
    nuevo_arm.data.pose_position = "REST"
    return nueva_malla, nuevo_arm


def material_cuerpo():
    mat = bpy.data.materials.new("M_Avatar_Holograma")
    mat.use_nodes = True
    nodos = mat.node_tree
    nodos.nodes.clear()

    salida = nodos.nodes.new("ShaderNodeOutputMaterial")
    salida.location = (980, 0)

    bsdf = nodos.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (220, 240)
    bsdf.inputs["Base Color"].default_value = COLOR_PERLA
    bsdf.inputs["Metallic"].default_value = 0.16
    bsdf.inputs["Roughness"].default_value = 0.28
    bsdf.inputs["Alpha"].default_value = 0.92
    bsdf.inputs["Emission Color"].default_value = COLOR_PERLA
    bsdf.inputs["Emission Strength"].default_value = 0.35
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.06

    borde = nodos.nodes.new("ShaderNodeEmission")
    borde.location = (220, -80)
    borde.inputs["Color"].default_value = COLOR_HIELO
    borde.inputs["Strength"].default_value = 1.15

    peso = nodos.nodes.new("ShaderNodeLayerWeight")
    peso.location = (-260, -80)
    potencia = nodos.nodes.new("ShaderNodeMath")
    potencia.location = (-40, -40)
    potencia.operation = "POWER"
    potencia.inputs[1].default_value = 3.5
    nodos.links.new(peso.outputs["Facing"], potencia.inputs[0])
    invertir = nodos.nodes.new("ShaderNodeMath")
    invertir.location = (-40, -160)
    invertir.operation = "SUBTRACT"
    invertir.inputs[0].default_value = 1.0
    nodos.links.new(potencia.outputs["Value"], invertir.inputs[1])
    fuerza = nodos.nodes.new("ShaderNodeMath")
    fuerza.location = (160, -180)
    fuerza.operation = "MULTIPLY"
    fuerza.inputs[1].default_value = 0.5
    nodos.links.new(invertir.outputs["Value"], fuerza.inputs[0])

    malla = nodos.nodes.new("ShaderNodeWireframe")
    malla.location = (-260, -320)
    malla.use_pixel_size = True
    malla.inputs["Size"].default_value = 0.55
    opacidad = nodos.nodes.new("ShaderNodeMath")
    opacidad.location = (-40, -320)
    opacidad.operation = "MULTIPLY"
    opacidad.inputs[1].default_value = 0.16
    nodos.links.new(malla.outputs["Fac"], opacidad.inputs[0])
    em_malla = nodos.nodes.new("ShaderNodeEmission")
    em_malla.location = (220, -300)
    em_malla.inputs["Color"].default_value = COLOR_HIELO
    em_malla.inputs["Strength"].default_value = 0.8

    def mezclar(factor, shader_a, shader_b, x, y):
        mezcla = nodos.nodes.new("ShaderNodeMixShader")
        mezcla.location = (x, y)
        nodos.links.new(factor, mezcla.inputs["Factor"])
        nodos.links.new(shader_a, mezcla.inputs[1])
        nodos.links.new(shader_b, mezcla.inputs[2])
        return mezcla

    con_malla = mezclar(opacidad.outputs["Value"], bsdf.outputs["BSDF"], em_malla.outputs["Emission"], 560, 120)
    con_borde = mezclar(fuerza.outputs["Value"], con_malla.outputs["Shader"], borde.outputs["Emission"], 780, 40)
    nodos.links.new(con_borde.outputs["Shader"], salida.inputs["Surface"])

    mat.blend_method = "BLEND"
    mat.surface_render_method = "BLENDED"
    mat.use_transparent_shadow = False
    return mat


def material_lineas():
    mat = bpy.data.materials.new("M_Lineas_Anatomicas")
    mat.use_nodes = True
    nodos = mat.node_tree
    nodos.nodes.clear()
    salida = nodos.nodes.new("ShaderNodeOutputMaterial")
    salida.location = (420, 0)
    emision = nodos.nodes.new("ShaderNodeEmission")
    emision.location = (120, 0)
    emision.inputs["Color"].default_value = COLOR_CIAN
    emision.inputs["Strength"].default_value = 3.0
    nodos.links.new(emision.outputs["Emission"], salida.inputs["Surface"])
    return mat


def perpendicular(eje, preferida):
    eje_n = eje.normalized()
    lateral = preferida - eje_n * preferida.dot(eje_n)
    if lateral.length < 1e-5:
        apoyo = Vector((0.0, 1.0, 0.0)) if abs(eje_n.z) > 0.85 else Vector((0.0, 0.0, 1.0))
        lateral = eje_n.cross(apoyo)
    return lateral.normalized()


def radio_superficial(malla, centro, eje):
    eje_n = eje.normalized()
    distancias = []
    for vert in malla.data.vertices:
        delta = vert.co - centro
        if abs(delta.dot(eje_n)) > 3.5:
            continue
        radial = (delta - eje_n * delta.dot(eje_n)).length
        if 0.5 < radial < 18.0:
            distancias.append(radial)
    if not distancias:
        return 4.5
    distancias.sort()
    return distancias[int(len(distancias) * 0.8)]


def punto_en_piel(malla, origen, direccion):
    """Lanza un rayo desde el interior del cuerpo hasta la piel. Es una aproximación."""
    direccion = direccion.normalized()
    acierto, lugar, normal, _indice = malla.ray_cast(origen, direccion)
    if not acierto:
        return None
    if normal.dot(direccion) < 0.0:
        normal = -normal
    return lugar + normal.normalized() * 0.22


def puntos_en_hueso(malla, bone, sesgo, pasos=7, margen=0.18):
    a = bone.head_local.copy()
    b = bone.tail_local.copy()
    eje = b - a
    if eje.length < 1e-4:
        return []
    direccion = perpendicular(eje, sesgo)
    puntos = []
    for i in range(pasos):
        t = margen + (1.0 - 2.0 * margen) * (i / (pasos - 1))
        punto = punto_en_piel(malla, a + eje * t, direccion)
        if punto is not None:
            puntos.append(punto)
    return puntos


def puntos_arco(malla, centro, normal, pasos=7):
    normal = normal.normalized()
    apoyo = Vector((0.0, 0.0, 1.0)) if abs(normal.z) < 0.85 else Vector((0.0, 1.0, 0.0))
    lado = normal.cross(apoyo).normalized()
    arriba = normal.cross(lado).normalized()
    puntos = []
    for i in range(pasos):
        angulo = math.radians(-50 + 100 * i / (pasos - 1))
        direccion = lado * math.cos(angulo) + arriba * math.sin(angulo)
        punto = punto_en_piel(malla, centro, direccion)
        if punto is not None:
            puntos.append(punto)
    return puntos


def tubo(puntos, radio):
    lados = 3
    vertices = []
    caras = []
    anillos = []
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
        apoyo = Vector((0.0, 0.0, 1.0)) if abs(tangente.z) < 0.9 else Vector((0.0, 1.0, 0.0))
        lado = tangente.cross(apoyo).normalized()
        normal = tangente.cross(lado).normalized()
        base = len(vertices)
        anillos.append(base)
        for k in range(lados):
            angulo = 2.0 * math.pi * k / lados
            vertices.append(punto + (lado * math.cos(angulo) + normal * math.sin(angulo)) * radio)
        if len(anillos) > 1:
            previo = anillos[-2]
            for k in range(lados):
                a = previo + k
                b = previo + (k + 1) % lados
                c = base + (k + 1) % lados
                d = base + k
                caras.append((a, b, c, d))
    return vertices, caras, anillos


def agregar_grupo(obj, nombre, indices, grupos):
    # En Blender 4.x y 5.x los vertex groups viven en el objeto, no en la malla.
    if nombre not in grupos:
        grupos[nombre] = obj.vertex_groups.new(name=nombre)
    if indices:
        grupos[nombre].add(indices, 1.0, "REPLACE")


def construir_lineas(malla_ref, arm, coleccion_dest, material):
    """Aproximación visual. No lee músculos reales: el modelo no los tiene."""
    frente = Vector((0.0, 0.0, 1.0))
    atras = Vector((0.0, 0.0, -1.0))
    lateral = Vector((1.0, 0.0, 0.0))
    trazos = []

    def trazo(nombre_hueso, sesgo, pasos=7):
        bone = hueso(arm, nombre_hueso)
        if bone is None:
            print("Aviso: no está el hueso", nombre_hueso)
            return
        pts = puntos_en_hueso(malla_ref, bone, sesgo, pasos=pasos)
        if len(pts) >= 2:
            trazos.append((bone.name, pts))

    trazo("LeftArm", frente)
    trazo("RightArm", frente)
    trazo("LeftArm", atras)
    trazo("RightArm", atras)
    trazo("LeftForeArm", frente, 6)
    trazo("RightForeArm", frente, 6)
    trazo("LeftUpLeg", frente)
    trazo("RightUpLeg", frente)
    trazo("LeftUpLeg", atras)
    trazo("RightUpLeg", atras)
    trazo("LeftUpLeg", lateral)
    trazo("RightUpLeg", -lateral)
    trazo("LeftLeg", atras, 6)
    trazo("RightLeg", atras, 6)

    for sufijo, signo in (("LeftArm", 1.0), ("RightArm", -1.0)):
        bone = hueso(arm, sufijo)
        if bone is None:
            continue
        direccion = (bone.tail_local - bone.head_local)
        if direccion.length < 1e-4:
            continue
        arco = puntos_arco(malla_ref, bone.head_local, direccion)
        if len(arco) >= 2:
            trazos.append((bone.name, arco))

    for sufijo, semi in (("Spine", 5.5), ("Spine1", 6.5), ("Spine2", 9.0)):
        bone = hueso(arm, sufijo)
        if bone is None:
            continue
        centro = bone.head_local.copy()
        linea = []
        for x in (-semi, 0.0, semi):
            punto = punto_en_piel(malla_ref, centro + Vector((x, 0.0, 0.0)), frente)
            if punto is not None:
                linea.append(punto)
        if len(linea) >= 2:
            trazos.append((bone.name, linea))

    costilla = hueso(arm, "Spine1")
    for sufijo, signo in (("LeftUpLeg", 1.0), ("RightUpLeg", -1.0)):
        cadera = hueso(arm, sufijo)
        if cadera is None or costilla is None:
            continue
        linea = []
        for t in (0.25, 0.55, 0.85):
            centro = cadera.head_local.lerp(costilla.head_local, t)
            centro.x += signo * 5.0
            punto = punto_en_piel(malla_ref, centro, Vector((signo * 0.45, 0.0, 0.9)))
            if punto is not None:
                linea.append(punto)
        if len(linea) >= 2:
            trazos.append((cadera.name, linea))

    vertices = []
    caras = []
    pesos = []
    for nombre, puntos in trazos:
        base = len(vertices)
        nuevos, nuevas, _anillos = tubo(puntos, RADIO_LINEA)
        if not nuevas:
            continue
        vertices.extend(nuevos)
        caras.extend(tuple(i + base for i in cara) for cara in nuevas)
        pesos.append((nombre, list(range(base, base + len(nuevos)))))

    datos = bpy.data.meshes.new("Lineas_Anatomicas_Mesh")
    datos.from_pydata(vertices, [], caras)
    datos.update()
    obj = bpy.data.objects.new("Lineas_Anatomicas", datos)
    coleccion_dest.objects.link(obj)
    obj.data.materials.append(material)
    grupos = {}
    for nombre, indices in pesos:
        agregar_grupo(obj, nombre, indices, grupos)
    return obj


def enlazar_lineas(lineas, malla, arm):
    lineas.parent = arm
    lineas.matrix_parent_inverse = malla.matrix_parent_inverse.copy()
    lineas.location = malla.location
    lineas.rotation_euler = malla.rotation_euler.copy()
    lineas.scale = malla.scale
    mod = lineas.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    mod.use_vertex_groups = True


def crear_luces(destino):
    def area(nombre, ubicacion, energia, color, tamano):
        datos = bpy.data.lights.new(nombre, "AREA")
        datos.energy = energia
        datos.color = color
        datos.size = tamano
        datos.use_shadow = False
        obj = bpy.data.objects.new(nombre, datos)
        obj.location = ubicacion
        destino.objects.link(obj)
        return obj

    return [
        area("Luz_Clave_Holo", (1.1, -2.6, 2.0), 36.0, (1.0, 1.0, 1.0), 3.6),
        area("Luz_Relleno_Holo", (-1.8, -1.6, 1.3), 12.0, (0.82, 0.92, 1.0), 4.0),
        area("Luz_Borde_Holo", (-0.4, 2.1, 1.6), 14.0, (0.62, 0.88, 0.95), 2.4),
    ]


def ocultar_otras_luces(propias):
    nombres = {luz.name for luz in propias}
    for obj in bpy.data.objects:
        if obj.type == "LIGHT" and obj.name not in nombres:
            obj.hide_render = True


def crear_camara(destino, objetivos):
    datos = bpy.data.cameras.new("Cam_Avatar_Holo")
    datos.type = "ORTHO"
    datos.clip_start = 0.01
    datos.clip_end = 100.0
    cam = bpy.data.objects.new("Cam_Avatar_Holo", datos)
    destino.objects.link(cam)

    centro = Vector((0.0, 0.0, 0.9))
    cam.location = centro + Vector((1.9, -2.15, 0.35))
    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()

    deps = bpy.context.evaluated_depsgraph_get()
    puntos = []
    for obj in objetivos:
        evaluado = obj.evaluated_get(deps)
        for esquina in evaluado.bound_box:
            puntos.append(evaluado.matrix_world @ Vector(esquina))
    inversa = cam.matrix_world.inverted()
    locales = [inversa @ punto for punto in puntos]
    xs = [p.x for p in locales]
    ys = [p.y for p in locales]
    desplazamiento = cam.matrix_world.to_3x3() @ Vector((
        (min(xs) + max(xs)) * 0.5,
        (min(ys) + max(ys)) * 0.5,
        0.0,
    ))
    cam.location += desplazamiento
    bpy.context.view_layer.update()

    inversa = cam.matrix_world.inverted()
    locales = [inversa @ punto for punto in puntos]
    xs = [p.x for p in locales]
    ys = [p.y for p in locales]
    datos.ortho_scale = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.16
    return cam


def configurar_render(camara, carpeta):
    escena = bpy.context.scene
    escena.camera = camara
    escena.render.engine = "BLENDER_EEVEE"
    escena.render.resolution_x = 2048
    escena.render.resolution_y = 2048
    escena.render.resolution_percentage = 100
    escena.render.film_transparent = True
    escena.render.image_settings.media_type = "IMAGE"
    escena.render.image_settings.file_format = "PNG"
    escena.render.image_settings.color_mode = "RGBA"
    escena.render.filepath = os.path.join(carpeta, "avatar_holografico.png")
    escena.render.use_compositing = False
    if hasattr(escena.eevee, "taa_render_samples"):
        escena.eevee.taa_render_samples = 32


def guardar(destino):
    origen = os.path.abspath(bpy.data.filepath) if bpy.data.filepath else ""
    if origen and os.path.abspath(destino) == origen:
        raise RuntimeError("El destino coincide con el archivo abierto. No se sobrescribe.")
    bpy.ops.wm.save_as_mainfile(filepath=destino)
    return destino


def main():
    comprobar_version()
    if not bpy.data.filepath:
        raise RuntimeError("Guarda el .blend actual antes de ejecutar el script.")

    malla, arm = encontrar_avatar()
    print("Avatar:", malla.name, "armature:", arm.name, "vértices:", len(malla.data.vertices))
    print("El modelo no tiene grupos musculares. Las líneas se aproximan con los huesos.")

    col_original = coleccion("AVATAR_ORIGINAL")
    col_holograma = coleccion("HOLOGRAMA")
    col_detalles = coleccion("DETALLES_ANATOMICOS")
    col_luces = coleccion("LUCES")
    col_camara = coleccion("CAMARA")

    mover_a(malla, col_original)
    mover_a(arm, col_original)
    malla.hide_set(True)
    malla.hide_render = True
    arm.hide_set(True)
    arm.hide_render = True

    nueva_malla, nuevo_arm = preparar_copia(malla, arm, col_holograma)
    nueva_malla.data.materials.clear()
    nueva_malla.data.materials.append(material_cuerpo())

    lineas = construir_lineas(nueva_malla, nuevo_arm, col_detalles, material_lineas())
    enlazar_lineas(lineas, nueva_malla, nuevo_arm)

    luces = crear_luces(col_luces)
    ocultar_otras_luces(luces)
    bpy.context.view_layer.update()
    camara = crear_camara(col_camara, (nueva_malla, lineas))

    carpeta = os.path.dirname(bpy.data.filepath)
    configurar_render(camara, carpeta)
    bpy.ops.render.render(write_still=True)

    destino = os.path.join(carpeta, "avatar_holografico.blend")
    guardar(destino)
    print("Blend:", destino)
    print("PNG:", bpy.context.scene.render.filepath)
    print("Para revisarlo: pulsa Z y elige Material Preview o Rendered.")


if __name__ == "__main__":
    main()
