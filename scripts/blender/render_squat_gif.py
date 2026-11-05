# render_squat_gif.py
# Renderiza la acción squat_bodyweight ya guardada y deja los fotogramas PNG.
# No cambia la pose, no guarda el .blend y no toca el maniquí original.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\render_squat_gif.py"
#
# Una prueba de un solo fotograma:
#   ... --python "scripts\blender\render_squat_gif.py" -- prueba

import math
import os
import shutil
import subprocess
import sys

import bpy
from mathutils import Vector


NOMBRE_BLEND = "personaje_squat_bodyweight.blend"
NOMBRE_ACCION = "squat_bodyweight"
ANCHO = 540
ALTO = 720
MUESTRAS = 8
PASO = 2


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def argumentos():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def exigir_archivo():
    if not bpy.data.filepath:
        raise RuntimeError("Abre personaje_squat_bodyweight.blend antes de renderizar.")
    if os.path.basename(bpy.data.filepath) != NOMBRE_BLEND:
        raise RuntimeError(
            "Este render solo usa "
            + NOMBRE_BLEND
            + ". El archivo abierto es "
            + bpy.data.filepath
        )


def malla_del_cuerpo(arm):
    hijas = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.parent == arm]
    if hijas:
        return max(hijas, key=lambda obj: len(obj.data.vertices))
    mallas = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    if not mallas:
        raise RuntimeError("No hay malla para encuadrar.")
    return max(mallas, key=lambda obj: len(obj.data.vertices))


def apuntar(objeto, destino):
    direccion = Vector(destino) - objeto.location
    objeto.rotation_euler = direccion.to_track_quat("-Z", "Y").to_euler()


def caja_en_fotogramas(scene, malla, fotogramas):
    puntos = []
    for fotograma in fotogramas:
        scene.frame_set(fotograma)
        bpy.context.view_layer.update()
        for esquina in malla.bound_box:
            puntos.append(malla.matrix_world @ Vector(esquina))
    minimo = Vector(
        (
            min(punto.x for punto in puntos),
            min(punto.y for punto in puntos),
            min(punto.z for punto in puntos),
        )
    )
    maximo = Vector(
        (
            max(punto.x for punto in puntos),
            max(punto.y for punto in puntos),
            max(punto.z for punto in puntos),
        )
    )
    return minimo, maximo


def preparar_camara(scene, malla):
    datos = bpy.data.cameras.new("Cam_Ejercicio")
    datos.lens = 50
    datos.sensor_fit = "VERTICAL"
    datos.sensor_height = 24
    camara = bpy.data.objects.new("Cam_Ejercicio", datos)
    scene.collection.objects.link(camara)
    scene.camera = camara

    minimo, maximo = caja_en_fotogramas(scene, malla, (1, 24, 48))
    centro = (minimo + maximo) / 2
    alto = max(maximo.z - minimo.z, 0.2)
    ancho = max(maximo.x - minimo.x, 0.2)
    proporcion = scene.render.resolution_x / scene.render.resolution_y
    mitad = max(alto, ancho / proporcion) * 0.5 * 1.22
    fov = 2 * math.atan((datos.sensor_height / 2) / datos.lens)
    distancia = mitad / math.tan(fov / 2)
    # El maniquí mira hacia -Y. La cámara queda al frente y un poco de lado.
    camara.location = centro + Vector((distancia * 0.34, -distancia * 0.94, alto * 0.04))
    apuntar(camara, centro + Vector((0.0, 0.0, alto * 0.02)))
    return centro, alto


def preparar_luces(centro, alto):
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.hide_render = True

    def area(nombre, ubicacion, energia, tamano):
        datos = bpy.data.lights.new(nombre, "AREA")
        datos.energy = energia
        datos.size = tamano
        datos.shape = "DISK"
        luz = bpy.data.objects.new(nombre, datos)
        bpy.context.scene.collection.objects.link(luz)
        luz.location = ubicacion
        apuntar(luz, centro)
        return luz

    area("Luz_Clave", centro + Vector((1.1, -1.8, alto * 0.85)), 12, 2.4)
    area("Luz_Relleno", centro + Vector((-1.7, -1.1, alto * 0.35)), 5, 3.2)
    area("Luz_Contra", centro + Vector((-0.4, 1.6, alto * 0.7)), 6, 1.8)


def preparar_fondo(scene):
    mundo = scene.world or bpy.data.worlds.new("Mundo_Ejercicio")
    scene.world = mundo
    mundo.use_nodes = True
    fondo = mundo.node_tree.nodes.get("Background")
    if fondo is None:
        fondo = mundo.node_tree.nodes.new("ShaderNodeBackground")
    fondo.inputs[0].default_value = (0.16, 0.17, 0.19, 1.0)
    fondo.inputs[1].default_value = 1.0
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.film_transparent = False


def preparar_motor(scene, carpeta_frames):
    try:
        scene.render.engine = "BLENDER_EEVEE"
    except TypeError as error:
        raise RuntimeError("EEVEE no está disponible en este Blender: " + str(error)) from error
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "taa_render_samples"):
        scene.eevee.taa_render_samples = MUESTRAS
    scene.render.resolution_x = ANCHO
    scene.render.resolution_y = ALTO
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 48
    scene.frame_step = PASO
    scene.render.use_overwrite = True
    scene.render.image_settings.media_type = "IMAGE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = os.path.join(carpeta_frames, "frame_")


def empaquetar():
    uv = shutil.which("uv")
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "empaquetar_gif.py")
    if uv is None:
        print("GIF_PENDIENTE falta uv; ejecuta empaquetar_gif.py")
        return
    subprocess.run(
        [uv, "run", "--with", "pillow", "python", script],
        cwd=carpeta_proyecto(),
        check=True,
    )


def main():
    exigir_archivo()
    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    if arm is None or arm.animation_data is None or arm.animation_data.action is None:
        raise RuntimeError("La armadura no tiene la acción " + NOMBRE_ACCION)
    if arm.animation_data.action.name != NOMBRE_ACCION:
        raise RuntimeError(
            "La acción activa es "
            + arm.animation_data.action.name
            + ", se esperaba "
            + NOMBRE_ACCION
        )

    scene = bpy.context.scene
    carpeta_frames = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_frames_squat")
    if os.path.isdir(carpeta_frames):
        shutil.rmtree(carpeta_frames)
    os.makedirs(carpeta_frames)

    preparar_fondo(scene)
    preparar_motor(scene, carpeta_frames)
    malla = malla_del_cuerpo(arm)
    centro, alto = preparar_camara(scene, malla)
    preparar_luces(centro, alto)

    prueba = "prueba" in argumentos()
    if prueba:
        scene.frame_set(24)
        scene.render.filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "preview_gif_f24.png"
        )
        bpy.ops.render.render(write_still=True)
        print("PRUEBA_OK", scene.render.filepath)
        return

    bpy.ops.render.render(animation=True)
    print("FRAMES_OK", carpeta_frames)
    empaquetar()


if __name__ == "__main__":
    main()
