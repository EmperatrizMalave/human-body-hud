# vestir_mujer.py
# Cubre a la mujer con top, shorts, pelo y zapatos.
# El corte sigue planos del cuerpo, no el borde de los pesos, para que el
# dobladillo no quede en escalera. Las prendas usan los mismos huesos que
# la sentadilla. No guarda el archivo de origen.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight_mujer.blend" `
#     --python "scripts\blender\vestir_mujer.py"

import math
import os

import bmesh
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


TELA = (0.30, 0.36, 0.43)
VIVO = (0.10, 0.78, 0.82)
PELO = (0.52, 0.36, 0.20)
ZAPATO = (0.94, 0.95, 0.96)
SUELA = (0.62, 0.66, 0.70)
BRAZOS = (
    "upperarm01.L", "upperarm01.R", "upperarm02.L", "upperarm02.R",
    "lowerarm01.L", "lowerarm01.R", "lowerarm02.L", "lowerarm02.R",
)


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def exigir_hueso(arm, nombre):
    hueso = arm.data.bones.get(nombre)
    if hueso is None:
        raise RuntimeError(f"Diagnóstico: falta el hueso {nombre}. No se vistió a la mujer.")
    return hueso


def hueso_local(arm, cuerpo, nombre, cola=False):
    hueso = exigir_hueso(arm, nombre)
    punto = hueso.tail_local if cola else hueso.head_local
    return cuerpo.matrix_world.inverted() @ (arm.matrix_world @ punto)


def peso(obj, nombre, indice):
    grupo = obj.vertex_groups.get(nombre)
    if grupo is None:
        return 0.0
    try:
        return float(grupo.weight(indice))
    except RuntimeError:
        return 0.0


def peso_suma(obj, indice, nombres):
    return sum(peso(obj, nombre, indice) for nombre in nombres)


def material(nombre, color, rugosidad):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = next(nodo for nodo in mat.node_tree.nodes if nodo.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = rugosidad
    return mat


def hornear_forma(cuerpo):
    if not cuerpo.data.shape_keys:
        return 0
    cantidad = len(cuerpo.data.shape_keys.key_blocks) - 1
    bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.data.objects:
        obj.select_set(False)
    cuerpo.select_set(True)
    bpy.context.view_layer.objects.active = cuerpo
    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    return cantidad


def indices_cuerpo(cuerpo):
    if cuerpo.vertex_groups.get("body") is None:
        raise RuntimeError("Diagnóstico: la malla no tiene el grupo body. No se vistió.")
    visibles = {
        indice
        for indice in range(len(cuerpo.data.vertices))
        if peso(cuerpo, "body", indice) > 0.5
    }
    if len(visibles) < 1000:
        raise RuntimeError("Diagnóstico: el grupo body casi no tiene vértices. No se vistió.")
    return visibles


def malla_visible(cuerpo, visibles):
    bm = bmesh.new()
    mapa = {}
    for cara in cuerpo.data.polygons:
        if not all(indice in visibles for indice in cara.vertices):
            continue
        nuevos = []
        for indice in cara.vertices:
            vertice = mapa.get(indice)
            if vertice is None:
                vertice = bm.verts.new(cuerpo.data.vertices[indice].co)
                mapa[indice] = vertice
            nuevos.append(vertice)
        try:
            bm.faces.new(nuevos)
        except ValueError:
            continue
    bm.normal_update()
    return bm


def cortar_plano(bm, origen, normal, quedarse_negativo):
    if not bm.faces:
        return
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    # Positivo es el lado de la normal. clear_outer tira ese lado.
    bmesh.ops.bisect_plane(
        bm,
        geom=geom,
        dist=0.0001,
        plane_co=origen,
        plane_no=normal.normalized(),
        clear_inner=not quedarse_negativo,
        clear_outer=quedarse_negativo,
    )
    sueltos = [vertice for vertice in bm.verts if not vertice.link_faces]
    if sueltos:
        bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    bm.normal_update()


def cortar_altura(bm, z_min, z_max):
    if z_max is not None:
        cortar_plano(bm, Vector((0.0, 0.0, z_max)), Vector((0.0, 0.0, 1.0)), True)
    if z_min is not None:
        cortar_plano(bm, Vector((0.0, 0.0, z_min)), Vector((0.0, 0.0, 1.0)), False)


def borrar_brazos(bm, cuerpo):
    arbol = KDTree(len(cuerpo.data.vertices))
    for indice, vertice in enumerate(cuerpo.data.vertices):
        arbol.insert(vertice.co, indice)
    arbol.balance()
    borrar = []
    for vertice in bm.verts:
        _, indice, _distancia = arbol.find(vertice.co)
        if peso_suma(cuerpo, indice, BRAZOS) > 0.45:
            borrar.append(vertice)
    if borrar:
        bmesh.ops.delete(bm, geom=borrar, context="VERTS")
    bm.normal_update()


def orientar(bm, interior):
    bm.normal_update()
    muestra = list(bm.verts)[::max(1, len(bm.verts) // 40)]
    hacia_dentro = 0
    for vertice in muestra:
        destino = interior - vertice.co
        if destino.length < 1e-6:
            continue
        if vertice.normal.dot(destino.normalized()) > 0.05:
            hacia_dentro += 1
    if muestra and hacia_dentro > len(muestra) * 0.5:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.normal_update()


def empujar(bm, distancia, interior):
    for vertice in bm.verts:
        alejarse = vertice.co - interior
        if alejarse.length < 1e-5:
            continue
        vertice.co += alejarse.normalized() * distancia


def cubiertos(cuerpo, bm, margen):
    if not bm.verts:
        return []
    arbol = KDTree(len(bm.verts))
    for indice, vertice in enumerate(bm.verts):
        arbol.insert(vertice.co.copy(), indice)
    arbol.balance()
    return [
        indice
        for indice, vertice in enumerate(cuerpo.data.vertices)
        if arbol.find(vertice.co)[2] <= margen
    ]


def objeto_desde(nombre, bm, cuerpo):
    if not bm.faces:
        bm.free()
        raise RuntimeError(f"Diagnóstico: {nombre} no cubrió ninguna cara. No se vistió.")
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(nombre, malla)
    coleccion = cuerpo.users_collection[0] if cuerpo.users_collection else bpy.context.scene.collection
    coleccion.objects.link(obj)
    obj.parent = cuerpo.parent
    obj.matrix_world = cuerpo.matrix_world.copy()
    print("PRENDA", nombre, "VERTICES", len(malla.vertices), "CARAS", len(malla.polygons))
    return obj


def copiar_pesos(cuerpo, destino):
    arbol = KDTree(len(cuerpo.data.vertices))
    for indice, vertice in enumerate(cuerpo.data.vertices):
        arbol.insert(vertice.co, indice)
    arbol.balance()
    grupos = {}
    for nuevo, vertice in enumerate(destino.data.vertices):
        _, fuente, _ = arbol.find(vertice.co)
        for grupo in cuerpo.vertex_groups:
            try:
                valor = float(grupo.weight(fuente))
            except RuntimeError:
                continue
            if valor <= 0.0001:
                continue
            destino_grupo = grupos.get(grupo.name)
            if destino_grupo is None:
                destino_grupo = destino.vertex_groups.new(name=grupo.name)
                grupos[grupo.name] = destino_grupo
            destino_grupo.add([nuevo], valor, "REPLACE")


def aplicar(obj, nombre):
    bpy.ops.object.mode_set(mode="OBJECT")
    for otro in bpy.data.objects:
        otro.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=nombre)


def vestir(obj, cuerpo, colores, grosor):
    copiar_pesos(cuerpo, obj)
    for indice, (color, rugosidad) in enumerate(colores):
        obj.data.materials.append(material(f"{obj.name}_{indice}", color, rugosidad))
    referencia = next(mod for mod in cuerpo.modifiers if mod.type == "ARMATURE")
    suavizado = obj.modifiers.new("Suavizar", "SUBSURF")
    suavizado.levels = 2
    suavizado.render_levels = 2
    solido = obj.modifiers.new("Grosor", "SOLIDIFY")
    solido.thickness = grosor
    solido.offset = 1.0
    solido.use_rim = True
    solido.material_offset_rim = 1
    armadura = obj.modifiers.new("Armature", "ARMATURE")
    armadura.object = referencia.object
    armadura.use_vertex_groups = True
    armadura.use_bone_envelopes = False
    bpy.ops.object.mode_set(mode="OBJECT")
    for otro in bpy.data.objects:
        otro.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()


def unir(principal, piezas):
    bpy.ops.object.mode_set(mode="OBJECT")
    for otro in bpy.data.objects:
        otro.select_set(False)
    principal.select_set(True)
    bpy.context.view_layer.objects.active = principal
    for pieza in piezas:
        pieza.select_set(True)
    bpy.ops.object.join()
    return principal


def ajustar_a_cuerpo(obj, cuerpo, separacion):
    ajuste = obj.modifiers.new("Ajuste", "SHRINKWRAP")
    ajuste.target = cuerpo
    ajuste.wrap_method = "NEAREST_SURFACEPOINT"
    ajuste.offset = separacion
    aplicar(obj, "Ajuste")


def cinta(nombre, inicio, fin, cuerpo, ancho=0.034):
    bm = bmesh.new()
    direccion = fin - inicio
    lateral = direccion.cross(Vector((0.0, -1.0, 0.0)))
    if lateral.length < 1e-6:
        lateral = Vector((1.0, 0.0, 0.0))
    lateral.normalize()
    filas = []
    for paso in range(9):
        centro = inicio.lerp(fin, paso / 8)
        fila = []
        for corte in range(5):
            fila.append(bm.verts.new(centro + lateral * ((corte / 4) - 0.5) * ancho))
        filas.append(fila)
    for paso in range(8):
        for corte in range(4):
            bm.faces.new((
                filas[paso][corte],
                filas[paso][corte + 1],
                filas[paso + 1][corte + 1],
                filas[paso + 1][corte],
            ))
    bm.normal_update()
    obj = objeto_desde(nombre, bm, cuerpo)
    ajustar_a_cuerpo(obj, cuerpo, 0.008)
    return obj


def ocultar_interior(cuerpo, indices):
    if not indices:
        return 0
    grupo = cuerpo.vertex_groups.get("piel_oculta")
    if grupo is None:
        grupo = cuerpo.vertex_groups.new(name="piel_oculta")
    grupo.add(list(indices), 1.0, "REPLACE")
    mascara = cuerpo.modifiers.new("Ocultar ropa", "MASK")
    mascara.vertex_group = "piel_oculta"
    mascara.invert_vertex_group = True
    return len(indices)


def marcas(cuerpo, arm, visibles):
    cadera = hueso_local(arm, cuerpo, "upperleg01.L")
    rodilla = hueso_local(arm, cuerpo, "lowerleg01.L")
    cuello = hueso_local(arm, cuerpo, "neck01")
    hombro = hueso_local(arm, cuerpo, "upperarm01.L")
    tobillo = hueso_local(arm, cuerpo, "foot.L")
    cabeza = hueso_local(arm, cuerpo, "head")
    coronilla = hueso_local(arm, cuerpo, "head", cola=True)
    exigir_hueso(arm, "breast.L")
    alturas_pecho = [
        cuerpo.data.vertices[indice].co.z
        for indice in visibles
        if peso_suma(cuerpo, indice, ("breast.L", "breast.R")) > 0.15
    ]
    if not alturas_pecho:
        raise RuntimeError("Diagnóstico: no encontré el pecho. No se vistió.")
    banda = min(alturas_pecho) - 0.018
    cintura = min(cadera.z + 0.07, banda - 0.06)
    dobladillo = cadera.z - (cadera.z - rodilla.z) * 0.34
    print(
        "MARCAS",
        "BANDA", round(banda, 3),
        "CINTURA", round(cintura, 3),
        "DOBLADILLO", round(dobladillo, 3),
        "CUELLO", round(cuello.z, 3),
        "TOBILLO", round(tobillo.z, 3),
    )
    return {
        "banda": banda,
        "cintura": cintura,
        "dobladillo": dobladillo,
        "cuello": cuello,
        "hombro": hombro,
        "tobillo": tobillo.z,
        "cabeza": cabeza,
        "alto": max(coronilla.z - cabeza.z, 0.05),
        "cadera": cadera,
    }


def cortar_lados(bm, centro_x, ancho):
    cortar_plano(bm, Vector((centro_x + ancho, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)), True)
    cortar_plano(bm, Vector((centro_x - ancho, 0.0, 0.0)), Vector((-1.0, 0.0, 0.0)), True)


def crear_top(base, cuerpo, guia):
    bm = base.copy()
    cortar_altura(bm, guia["banda"], guia["cuello"].z - 0.02)
    centro = guia["cuello"].x
    ancho = abs(guia["hombro"].x - centro) * 0.9
    cortar_lados(bm, centro, max(ancho, 0.11))
    print("TOP_ANCHO", round(ancho, 3))
    pecho = cubiertos(cuerpo, bm, 0.004)
    empujar(bm, 0.009, Vector((guia["cuello"].x, guia["cuello"].y, (guia["banda"] + guia["cuello"].z) * 0.5)))
    top = objeto_desde("Top", bm, cuerpo)
    hombro = guia["hombro"]
    cuello = guia["cuello"]
    tirantes = []
    for signo, nombre in ((1.0, "Tirante.L"), (-1.0, "Tirante.R")):
        ancho = abs(hombro.x - cuello.x)
        inicio = Vector((cuello.x + signo * ancho * 0.55, cuello.y - 0.03, guia["banda"] + 0.09))
        fin = Vector((hombro.x if signo > 0 else cuello.x - (hombro.x - cuello.x), hombro.y - 0.01, hombro.z + 0.015))
        tirantes.append(cinta(nombre, inicio, fin, cuerpo))
    unir(top, tirantes)
    return top, pecho


def crear_shorts(base, cuerpo, guia):
    bm = base.copy()
    cortar_altura(bm, guia["dobladillo"], guia["cintura"])
    borrar_brazos(bm, cuerpo)
    cadera = guia["cadera"]
    lejos = []
    for vertice in bm.verts:
        plano = Vector((vertice.co.x, vertice.co.y, 0.0))
        ancla = Vector((cadera.x, cadera.y, 0.0))
        otra = Vector((-cadera.x + 2 * (guia["cuello"].x), cadera.y, 0.0))
        if min((plano - ancla).length, (plano - otra).length) > 0.2:
            lejos.append(vertice)
    if lejos:
        bmesh.ops.delete(bm, geom=lejos, context="VERTS")
    piel = cubiertos(cuerpo, bm, 0.004)
    empujar(bm, 0.009, Vector((guia["cuello"].x, guia["cadera"].y, (guia["cintura"] + guia["dobladillo"]) * 0.5)))
    return objeto_desde("Shorts", bm, cuerpo), piel


def crear_pelo(base, cuerpo, guia):
    bm = base.copy()
    cabeza = guia["cabeza"]
    alto = guia["alto"]
    borrar = []
    for vertice in bm.verts:
        rel = (vertice.co.z - cabeza.z) / alto
        frente = cabeza.y - vertice.co.y
        if frente > 0.015 and rel < 0.62:
            borrar.append(vertice)
        elif rel < 0.18:
            borrar.append(vertice)
    if borrar:
        bmesh.ops.delete(bm, geom=borrar, context="VERTS")
    piel = cubiertos(cuerpo, bm, 0.004)
    empujar(bm, 0.006, guia["cabeza"])
    return objeto_desde("Pelo", bm, cuerpo), piel


def crear_coleta(ancla, cuerpo):
    bm = bmesh.new()
    segmentos = 16
    lados = 10
    anillos = []
    for paso in range(segmentos + 1):
        avance = paso / segmentos
        centro = ancla + Vector((0.0, 0.008 + avance * 0.04, -0.01 - avance * 0.42))
        radio = 0.022 * (1.0 - avance * 0.7) + 0.006
        anillo = []
        for lado in range(lados):
            angulo = (lado / lados) * math.tau
            anillo.append(bm.verts.new(centro + Vector((
                math.cos(angulo) * radio,
                math.sin(angulo) * radio * 0.65,
                0.0,
            ))))
        anillos.append(anillo)
    for paso in range(segmentos):
        for lado in range(lados):
            siguiente = (lado + 1) % lados
            cara = bm.faces.new((
                anillos[paso][lado],
                anillos[paso][siguiente],
                anillos[paso + 1][siguiente],
                anillos[paso + 1][lado],
            ))
            cara.material_index = 1 if paso == 0 else 0
    punta = bm.verts.new(ancla + Vector((0.0, 0.05, -0.45)))
    for lado in range(lados):
        bm.faces.new((anillos[-1][lado], anillos[-1][(lado + 1) % lados], punta))
    bm.normal_update()
    obj = objeto_desde("Coleta", bm, cuerpo)
    grupo = obj.vertex_groups.new(name="head")
    grupo.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    obj.data.materials.append(material("Coleta_0", PELO, 0.42))
    obj.data.materials.append(material("Coleta_1", VIVO, 0.35))
    referencia = next(mod for mod in cuerpo.modifiers if mod.type == "ARMATURE")
    armadura = obj.modifiers.new("Armature", "ARMATURE")
    armadura.object = referencia.object
    armadura.use_vertex_groups = True
    armadura.use_bone_envelopes = False
    bpy.ops.object.mode_set(mode="OBJECT")
    for otro in bpy.data.objects:
        otro.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    return obj


def ancla_coleta(pelo):
    mejor = max(pelo.data.vertices, key=lambda vertice: (vertice.co.y, vertice.co.z))
    return mejor.co.copy()


def bloque_zapato(bm, vertices):
    minimo = Vector((
        min(vertice.co.x for vertice in vertices),
        min(vertice.co.y for vertice in vertices),
        min(vertice.co.z for vertice in vertices),
    ))
    maximo = Vector((
        max(vertice.co.x for vertice in vertices),
        max(vertice.co.y for vertice in vertices),
        max(vertice.co.z for vertice in vertices),
    ))
    centro = (minimo + maximo) / 2
    centro.y -= 0.012
    centro.z += 0.006
    escala = (maximo - minimo) / 2
    escala.x += 0.018
    escala.y += 0.03
    escala.z += 0.016
    caja = bmesh.new()
    bmesh.ops.create_cube(caja, size=1.0)
    bmesh.ops.subdivide_edges(caja, edges=list(caja.edges), cuts=3)
    for vertice in caja.verts:
        # El cubo de tamaño 1 va de -0.5 a 0.5. El 2 lo lleva al tamaño del pie.
        vertice.co = centro + Vector((
            vertice.co.x * escala.x * 2,
            vertice.co.y * escala.y * 2,
            vertice.co.z * escala.z * 2,
        ))
    return caja


def crear_zapatos(base, cuerpo, guia):
    bm = base.copy()
    cortar_altura(bm, None, guia["tobillo"] + 0.04)
    piel = cubiertos(cuerpo, bm, 0.008)
    centro_x = guia["cuello"].x
    print(
        "PIE_CORTE",
        "N", len(bm.verts),
        "Z", round(min(v.co.z for v in bm.verts), 3), round(max(v.co.z for v in bm.verts), 3),
        "Y", round(min(v.co.y for v in bm.verts), 3), round(max(v.co.y for v in bm.verts), 3),
    )
    izquierdo = [vertice for vertice in bm.verts if vertice.co.x >= centro_x]
    derecho = [vertice for vertice in bm.verts if vertice.co.x < centro_x]
    zapatos = bmesh.new()
    for grupo in (izquierdo, derecho):
        if len(grupo) < 20:
            continue
        caja = bloque_zapato(bm, grupo)
        vert_map = {}
        for vertice in caja.verts:
            vert_map[vertice] = zapatos.verts.new(vertice.co)
        zapatos.verts.ensure_lookup_table()
        for cara in caja.faces:
            zapatos.faces.new([vert_map[vertice] for vertice in cara.verts])
        caja.free()
    bm.free()
    if not zapatos.faces:
        zapatos.free()
        raise RuntimeError("Diagnóstico: no pude armar los zapatos.")
    zapatos.normal_update()
    obj = objeto_desde("Zapatos", zapatos, cuerpo)
    return obj, piel


def pintar_zapatos(obj):
    for cara in obj.data.polygons:
        cara.material_index = 2 if cara.normal.z < -0.25 else 0


def centro_z(obj):
    bpy.context.view_layer.update()
    evaluado = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    alturas = [(evaluado.matrix_world @ Vector(esquina)).z for esquina in evaluado.bound_box]
    return (min(alturas) + max(alturas)) * 0.5


def caida(obj, escena):
    escena.frame_set(1)
    arriba = centro_z(obj)
    escena.frame_set(24)
    abajo = centro_z(obj)
    escena.frame_set(1)
    return arriba - abajo


def apuntar(objeto, destino):
    direccion = Vector(destino) - objeto.location
    objeto.rotation_euler = direccion.to_track_quat("-Z", "Y").to_euler()


def renderizar(cuerpo, prendas):
    escena = bpy.context.scene
    escena.frame_set(1)
    for obj in list(bpy.data.objects):
        if obj.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type in {"ARMATURE", "EMPTY"}:
            obj.hide_render = True
    puntos = []
    for obj in [cuerpo, *prendas]:
        for esquina in obj.bound_box:
            puntos.append(obj.matrix_world @ Vector(esquina))
    minimo = Vector((min(p.x for p in puntos), min(p.y for p in puntos), min(p.z for p in puntos)))
    maximo = Vector((max(p.x for p in puntos), max(p.y for p in puntos), max(p.z for p in puntos)))
    centro = (minimo + maximo) / 2
    alto = maximo.z - minimo.z
    ancho = max(maximo.x - minimo.x, 0.2)

    mundo = escena.world or bpy.data.worlds.new("Mundo_Ropa")
    escena.world = mundo
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes.get("Background")
    fondo.inputs[0].default_value = (0.027, 0.043, 0.078, 1.0)
    fondo.inputs[1].default_value = 1.0
    escena.view_settings.view_transform = "AgX"
    try:
        escena.render.engine = "BLENDER_EEVEE"
    except TypeError as error:
        raise RuntimeError("EEVEE no está disponible: " + str(error)) from error
    if hasattr(escena.eevee, "taa_render_samples"):
        escena.eevee.taa_render_samples = 16
    escena.render.resolution_x = 720
    escena.render.resolution_y = 960
    escena.render.image_settings.file_format = "PNG"
    escena.render.image_settings.color_mode = "RGB"

    datos = bpy.data.cameras.new("Cam_Ropa")
    datos.lens = 50
    datos.sensor_fit = "VERTICAL"
    datos.sensor_height = 24
    camara = bpy.data.objects.new("Cam_Ropa", datos)
    escena.collection.objects.link(camara)
    escena.camera = camara
    proporcion = escena.render.resolution_x / escena.render.resolution_y
    mitad = max(alto, ancho / proporcion) * 0.5 * 1.12
    fov = 2 * math.atan((datos.sensor_height / 2) / datos.lens)
    distancia = mitad / math.tan(fov / 2)

    def area(nombre, ubicacion, energia):
        luz_datos = bpy.data.lights.new(nombre, "AREA")
        luz_datos.energy = energia
        luz_datos.size = 2.4
        luz = bpy.data.objects.new(nombre, luz_datos)
        escena.collection.objects.link(luz)
        luz.location = ubicacion
        apuntar(luz, centro)

    area("Luz_Clave", centro + Vector((1.1, -1.7, alto * 0.7)), 22)
    area("Luz_Relleno", centro + Vector((-1.5, -0.7, alto * 0.25)), 9)
    area("Luz_Contra", centro + Vector((-0.2, 1.6, alto * 0.6)), 8)

    destino = os.path.join(carpeta_proyecto(), "assets", "previews")
    os.makedirs(destino, exist_ok=True)
    vistas = {
        "mujer_ropa_frente.png": (Vector((0.0, -1.0, alto * 0.02)), 1),
        "mujer_ropa_lado.png": (Vector((1.0, -0.15, alto * 0.02)), 1),
        "mujer_ropa_sentadilla.png": (Vector((0.55, -0.85, alto * 0.04)), 24),
    }
    for nombre, (direccion, fotograma) in vistas.items():
        escena.frame_set(fotograma)
        camara.location = centro + direccion.normalized() * distancia
        apuntar(camara, centro)
        escena.render.filepath = os.path.join(destino, nombre)
        bpy.ops.render.render(write_still=True)
        print("RENDER_OK", escena.render.filepath)
    escena.frame_set(1)
    for obj in list(bpy.data.objects):
        if obj.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(obj, do_unlink=True)


def main():
    if os.path.basename(bpy.data.filepath) != "personaje_squat_bodyweight_mujer.blend":
        raise RuntimeError("Este script solo abre assets/models/personaje_squat_bodyweight_mujer.blend.")
    cuerpo = bpy.data.objects.get("Human")
    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    if cuerpo is None or cuerpo.type != "MESH" or arm is None:
        raise RuntimeError("Diagnóstico: no están Human y su armadura. No se vistió.")
    accion = arm.animation_data.action if arm.animation_data else None
    if accion is None or accion.name != "squat_bodyweight":
        raise RuntimeError("Diagnóstico: la acción activa no es squat_bodyweight. No se vistió.")
    origen = bpy.data.filepath
    escena = bpy.context.scene
    escena.frame_set(1)
    print("FORMAS_HORNEADAS", hornear_forma(cuerpo))
    visibles = indices_cuerpo(cuerpo)
    guia = marcas(cuerpo, arm, visibles)
    base = malla_visible(cuerpo, visibles)

    top, piel_top = crear_top(base, cuerpo, guia)
    shorts, piel_shorts = crear_shorts(base, cuerpo, guia)
    pelo, piel_pelo = crear_pelo(base, cuerpo, guia)
    coleta = crear_coleta(ancla_coleta(pelo), cuerpo)
    zapatos, piel_pies = crear_zapatos(base, cuerpo, guia)
    base.free()

    telas = ((TELA, 0.55), (VIVO, 0.35))
    vestir(top, cuerpo, telas, 0.0035)
    vestir(shorts, cuerpo, telas, 0.0035)
    vestir(pelo, cuerpo, ((PELO, 0.4), (VIVO, 0.35)), 0.002)
    for grupo in list(pelo.vertex_groups):
        pelo.vertex_groups.remove(grupo)
    craneo = pelo.vertex_groups.new(name="head")
    craneo.add(list(range(len(pelo.data.vertices))), 1.0, "REPLACE")
    vestir(zapatos, cuerpo, ((ZAPATO, 0.32), (VIVO, 0.28), (SUELA, 0.62)), 0.004)
    for grupo in list(zapatos.vertex_groups):
        zapatos.vertex_groups.remove(grupo)
    pie_izquierdo = zapatos.vertex_groups.new(name="foot.L")
    pie_derecho = zapatos.vertex_groups.new(name="foot.R")
    for indice, vertice in enumerate(zapatos.data.vertices):
        grupo = pie_izquierdo if vertice.co.x >= guia["cuello"].x else pie_derecho
        grupo.add([indice], 1.0, "REPLACE")
    zapatos.modifiers["Grosor"].material_offset_rim = 0
    pintar_zapatos(zapatos)
    print("PIEL_SIN_MASCARA", len(piel_top) + len(piel_shorts) + len(piel_pelo) + len(piel_pies))

    prendas = [top, shorts, pelo, coleta, zapatos]
    caidas = {obj.name: round(caida(obj, escena), 4) for obj in [cuerpo, *prendas]}
    print("CAIDAS", caidas)
    renderizar(cuerpo, prendas)
    destino = os.path.join(carpeta_proyecto(), "assets", "models", "personaje_squat_bodyweight_mujer_vestida.blend")
    bpy.ops.wm.save_as_mainfile(filepath=destino, copy=True)
    if bpy.data.filepath != origen:
        raise RuntimeError("El archivo de origen cambió de ruta. No debía guardarse encima.")
    if caidas["Top"] < 0.12 or caidas["Shorts"] < 0.12 or caidas["Pelo"] < 0.12 or caidas["Coleta"] < 0.12:
        raise RuntimeError("Diagnóstico: una prenda no acompaña el descenso de la sentadilla. " + str(caidas))
    if caidas["Zapatos"] > 0.05:
        raise RuntimeError("Diagnóstico: los zapatos se hunden con la cadera. " + str(caidas))
    print("ROPA_OK", destino)


if __name__ == "__main__":
    main()
