# render_musculos.py
# Renderiza una vista frontal y otra lateral del maniquí ya pintado.
# No guarda el .blend.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_muscular_test.blend" `
#     --python "scripts\blender\render_musculos.py"

import math
import os

import bpy
from mathutils import Vector


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def apuntar(objeto, destino):
    direccion = Vector(destino) - objeto.location
    objeto.rotation_euler = direccion.to_track_quat("-Z", "Y").to_euler()


def caja_mundo(obj):
    puntos = [obj.matrix_world @ Vector(esquina) for esquina in obj.bound_box]
    minimo = Vector((min(p.x for p in puntos), min(p.y for p in puntos), min(p.z for p in puntos)))
    maximo = Vector((max(p.x for p in puntos), max(p.y for p in puntos), max(p.z for p in puntos)))
    return (minimo + maximo) / 2, maximo.z - minimo.z, maximo.x - minimo.x


def preparar_escena(scene, centro, alto, ancho):
    for obj in list(bpy.data.objects):
        if obj.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type in {"ARMATURE", "EMPTY"}:
            obj.hide_render = True

    mundo = scene.world or bpy.data.worlds.new("Mundo_Musculos")
    scene.world = mundo
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes.get("Background")
    fondo.inputs[0].default_value = (0.16, 0.17, 0.19, 1.0)
    fondo.inputs[1].default_value = 1.0
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError as error:
        raise RuntimeError("EEVEE no está disponible: " + str(error)) from error
    if hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.frame_set(1)

    datos = bpy.data.cameras.new("Cam_Revision")
    datos.lens = 50
    datos.sensor_fit = "VERTICAL"
    datos.sensor_height = 24
    camara = bpy.data.objects.new("Cam_Revision", datos)
    scene.collection.objects.link(camara)
    scene.camera = camara
    proporcion = scene.render.resolution_x / scene.render.resolution_y
    mitad = max(alto, ancho / proporcion) * 0.5 * 1.18
    fov = 2 * math.atan((datos.sensor_height / 2) / datos.lens)
    distancia = mitad / math.tan(fov / 2)

    def area(nombre, ubicacion, energia):
        luz_datos = bpy.data.lights.new(nombre, "AREA")
        luz_datos.energy = energia
        luz_datos.size = 2.6
        luz_datos.shape = "DISK"
        luz = bpy.data.objects.new(nombre, luz_datos)
        scene.collection.objects.link(luz)
        luz.location = ubicacion
        apuntar(luz, centro)

    area("Luz_Clave", centro + Vector((1.2, -1.8, alto * 0.75)), 14)
    area("Luz_Relleno", centro + Vector((-1.6, -0.8, alto * 0.3)), 6)
    area("Luz_Contra", centro + Vector((-0.3, 1.7, alto * 0.65)), 7)
    return camara, distancia


def main():
    if os.path.basename(bpy.data.filepath) != "personaje_muscular_test.blend":
        raise RuntimeError("Este render solo usa assets/models/personaje_muscular_test.blend.")
    cuerpo = next((obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name == "Human"), None)
    if cuerpo is None:
        raise RuntimeError("No está la malla Human.")
    scene = bpy.context.scene
    centro, alto, ancho = caja_mundo(cuerpo)
    camara, distancia = preparar_escena(scene, centro, alto, ancho)
    destino = os.path.join(carpeta_proyecto(), "assets", "previews")
    os.makedirs(destino, exist_ok=True)

    vistas = {
        "cuadriceps_frontal.png": Vector((0.0, -1.0, alto * 0.02)),
        "cuadriceps_lateral.png": Vector((1.0, -0.18, alto * 0.02)),
    }
    for nombre, direccion in vistas.items():
        camara.location = centro + direccion.normalized() * distancia
        apuntar(camara, centro + Vector((0.0, 0.0, alto * 0.01)))
        scene.render.filepath = os.path.join(destino, nombre)
        bpy.ops.render.render(write_still=True)
        print("RENDER_OK", scene.render.filepath)


if __name__ == "__main__":
    main()
