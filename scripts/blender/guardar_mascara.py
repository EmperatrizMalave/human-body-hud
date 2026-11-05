# guardar_mascara.py
# Guarda una selección manual de caras para reutilizarla.
# No cambia los pesos del esqueleto ni el archivo de origen.
#
# En Blender, con la malla Human en Modo Edición y las caras elegidas:
#   Scripting > Abrir > scripts/blender/guardar_mascara.py > Ejecutar script
#
# Para volver a pintar el archivo de prueba con esa selección:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight.blend" `
#     --python "scripts\blender\guardar_mascara.py" `
#     -- aplicar

import json
import os
import sys

import bpy


def carpeta_script():
    if "__file__" in globals():
        return os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(os.path.dirname(bpy.data.filepath), "..", "..", "scripts", "blender"))


def carpeta_proyecto():
    return os.path.abspath(os.path.join(carpeta_script(), "..", ".."))


def ruta_mascara():
    carpeta = os.path.join(carpeta_script(), "mascaras")
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, "cuadriceps.json")


def argumentos():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def malla_cuerpo():
    activa = bpy.context.view_layer.objects.active
    if activa is not None and activa.type == "MESH":
        return activa
    return next((obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name == "Human"), None)


def caras_seleccionadas(obj):
    if obj.mode != "EDIT":
        raise RuntimeError("Entra en Modo Edición, selecciona las caras del cuádriceps y ejecuta el script otra vez.")
    import bmesh

    malla = bmesh.from_edit_mesh(obj.data)
    indices = [cara.index for cara in malla.faces if cara.select]
    if len(indices) < 20:
        raise RuntimeError("La selección tiene menos de 20 caras. No se guardó la máscara.")
    return sorted(indices)


def guardar_seleccion():
    obj = malla_cuerpo()
    if obj is None:
        raise RuntimeError("Selecciona la malla Human antes de guardar la máscara.")
    indices = caras_seleccionadas(obj)
    datos = {
        "origen": "manual",
        "malla": obj.name,
        "grupo_muscular": "cuadriceps",
        "material": "MUSCLE_ACTIVE",
        "caras": indices,
        "nota": "Selección manual de caras. Sustituye la propuesta automática al aplicarla.",
    }
    destino = ruta_mascara()
    with open(destino, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
    print("MASCARA_GUARDADA", destino, "caras", len(indices))


def material(nombre, color):
    bloque = bpy.data.materials.get(nombre) or bpy.data.materials.new(nombre)
    bloque.diffuse_color = color
    bloque.use_nodes = True
    bsdf = next(nodo for nodo in bloque.node_tree.nodes if nodo.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.48
    bsdf.inputs["Metallic"].default_value = 0.0
    return bloque


def aplicar_mascara():
    destino = os.path.join(carpeta_proyecto(), "assets", "models", "personaje_muscular_test.blend")
    if os.path.abspath(bpy.data.filepath) == os.path.abspath(destino):
        raise RuntimeError("Abre el modelo de origen, no el archivo de prueba.")
    with open(ruta_mascara(), encoding="utf-8") as archivo:
        datos = json.load(archivo)
    obj = next((candidato for candidato in bpy.data.objects if candidato.name == datos["malla"]), None)
    if obj is None or obj.type != "MESH":
        raise RuntimeError("La máscara pertenece a una malla que no está en este archivo.")
    caras = datos["caras"]
    if any(indice < 0 or indice >= len(obj.data.polygons) for indice in caras):
        raise RuntimeError("La máscara no coincide con la cantidad de caras de esta malla.")

    malla = obj.data
    while malla.materials:
        malla.materials.pop(index=0)
    malla.materials.append(material("BODY_BASE", (0.718, 0.725, 0.745, 1.0)))
    malla.materials.append(material("MUSCLE_ACTIVE", (19 / 255, 184 / 255, 166 / 255, 1.0)))
    malla.materials.append(material("MUSCLE_SECONDARY", (46 / 255, 204 / 255, 113 / 255, 1.0)))
    indices = [0] * len(malla.polygons)
    vertices = set()
    for indice in caras:
        indices[indice] = 1
        vertices.update(malla.polygons[indice].vertices)
    malla.polygons.foreach_set("material_index", indices)
    malla.update()

    for lado in ("L", "R"):
        previo = obj.vertex_groups.get(f"mascara_cuadriceps.{lado}")
        if previo is not None:
            obj.vertex_groups.remove(previo)
    grupo = obj.vertex_groups.get("mascara_cuadriceps") or obj.vertex_groups.new(name="mascara_cuadriceps")
    grupo.add(sorted(vertices), 1.0, "REPLACE")

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=destino, copy=True)
    print("MASCARA_APLICADA", destino, "caras", len(caras))


def main():
    if "aplicar" in argumentos():
        aplicar_mascara()
    else:
        guardar_seleccion()


if __name__ == "__main__":
    main()
