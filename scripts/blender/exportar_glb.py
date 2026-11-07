# exportar_glb.py
# Exporta squat_bodyweight a GLB. Hornea el IK en los huesos de deformación.
# No guarda el .blend.
#
# PowerShell, desde la raíz del proyecto:
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight_mujer.blend" `
#     --python "scripts\blender\exportar_glb.py" -- mujer
#
#   & "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
#     --background "assets\models\personaje_squat_bodyweight_hombre.blend" `
#     --python "scripts\blender\exportar_glb.py" -- hombre

import json
import os
import struct
import sys

import bpy


def carpeta_proyecto():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def pedido():
    if "--" not in sys.argv:
        return None, None
    resto = sys.argv[sys.argv.index("--") + 1:]
    if not resto or resto[0] not in ("mujer", "hombre"):
        raise RuntimeError("Después de -- indica mujer u hombre.")
    nombre = resto[1] if len(resto) > 1 else None
    if nombre and not nombre.endswith(".glb"):
        nombre = f"{nombre}.glb"
    return resto[0], nombre


def ruta_glb(sexo, nombre=None):
    carpeta = os.path.join(carpeta_proyecto(), "frontend", "modelos")
    if sexo:
        carpeta = os.path.join(carpeta, sexo)
    return os.path.join(carpeta, nombre or "squat_bodyweight.glb")


def hornear_formas(cuerpo):
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


def leer_glb(ruta):
    with open(ruta, "rb") as archivo:
        magia, _version, _longitud = struct.unpack("<4sII", archivo.read(12))
        if magia != b"glTF":
            raise RuntimeError("El archivo exportado no es un GLB.")
        tamano, tipo = struct.unpack("<I4s", archivo.read(8))
        if tipo != b"JSON":
            raise RuntimeError("El GLB no trae el bloque JSON.")
        return json.loads(archivo.read(tamano).rstrip(b"\x00"))


def resumen_glb(ruta):
    gltf = leer_glb(ruta)
    nodos = gltf.get("nodes", [])
    nombres = {indice: nodo.get("name", "") for indice, nodo in enumerate(nodos)}
    animaciones = []
    for anim in gltf.get("animations", []):
        objetivos = []
        for canal in anim.get("channels", []):
            nodo = nombres.get(canal.get("target", {}).get("node"), "")
            camino = canal.get("target", {}).get("path", "")
            objetivos.append(f"{nodo}:{camino}")
        animaciones.append(
            {
                "nombre": anim.get("name"),
                "canales": len(anim.get("channels", [])),
                "objetivos": sorted(set(objetivos))[:12],
            }
        )
    return {
        "nodos": len(nodos),
        "mallas": len(gltf.get("meshes", [])),
        "skins": len(gltf.get("skins", [])),
        "materiales": [mat.get("name") for mat in gltf.get("materials", [])],
        "animaciones": animaciones,
    }


def animacion_se_mueve(ruta):
    gltf = leer_glb(ruta)
    nombres = [nodo.get("name", "") for nodo in gltf.get("nodes", [])]
    anim = next(item for item in gltf["animations"] if item.get("name") == "squat_bodyweight")
    for canal in anim["channels"]:
        if nombres[canal["target"]["node"]] != "root" or canal["target"]["path"] != "translation":
            continue
        salida = gltf["accessors"][anim["samplers"][canal["sampler"]]["output"]]
        vista = gltf["bufferViews"][salida["bufferView"]]
        with open(ruta, "rb") as archivo:
            archivo.seek(0, os.SEEK_END)
            archivo.seek(12)
            tamano, _tipo = struct.unpack("<I4s", archivo.read(8))
            inicio_bin = 20 + tamano + 8
            archivo.seek(inicio_bin + vista["byteOffset"])
            crudo = archivo.read(vista["byteLength"])
        primero = struct.unpack_from("<3f", crudo, 0)
        medio = struct.unpack_from("<3f", crudo, (salida["count"] // 2) * 12)
        return abs(primero[1] - medio[1]) > 0.05
    return False


def aplanar_tinte(obj):
    if obj.type != "MESH" or not obj.material_slots:
        return
    mat = obj.material_slots[0].material
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        return
    bsdf = next((nodo for nodo in mat.node_tree.nodes if nodo.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    base = bsdf.inputs.get("Base Color")
    if base is None or not base.is_linked:
        return
    origen = base.links[0].from_node
    if origen.type != "MIX_RGB":
        return
    color = origen.inputs["Color1"].default_value[:]
    for enlace in list(base.links):
        mat.node_tree.links.remove(enlace)
    base.default_value = color


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Abre el .blend del maniquí antes de exportar.")
    if os.path.basename(bpy.data.filepath) == "squat_bodyweight.glb":
        raise RuntimeError("El archivo abierto no es el modelo de origen.")

    arm = next((obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None)
    cuerpo = bpy.data.objects.get("Human")
    if arm is None or cuerpo is None or cuerpo.type != "MESH":
        raise RuntimeError("Diagnóstico: no están Human y su armadura. No se exportó.")
    accion = arm.animation_data.action if arm.animation_data else None
    if accion is None or accion.name != "squat_bodyweight":
        raise RuntimeError("Diagnóstico: la acción activa no es squat_bodyweight. No se exportó.")

    deformacion = [hueso.name for hueso in arm.data.bones if hueso.use_deform]
    ik = []
    for pose in arm.pose.bones:
        for con in pose.constraints:
            if con.type != "IK":
                continue
            ik.append(
                {
                    "hueso": pose.name,
                    "objetivo": con.subtarget,
                    "eslabones": int(con.chain_count),
                    "influencia": round(float(con.influence), 3),
                }
            )
    if not deformacion or not ik:
        raise RuntimeError("Diagnóstico: no hay huesos de deformación o restricciones IK. No se exportó.")

    sexo, nombre_glb = pedido()
    formas = hornear_formas(cuerpo) if sexo == "hombre" else 0

    if not cuerpo.data.materials:
        gris = bpy.data.materials.new("CuerpoVisor")
        gris.diffuse_color = (0.86, 0.87, 0.89, 1.0)
        gris.use_nodes = True
        bsdf = next(nodo for nodo in gris.node_tree.nodes if nodo.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (0.86, 0.87, 0.89, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
        cuerpo.data.materials.append(gris)

    for obj in bpy.data.objects:
        obj.select_set(False)
    cuerpo.select_set(True)
    for extra in ("Top", "Shorts", "Pelo", "Coleta", "Zapatos"):
        prenda = bpy.data.objects.get(extra)
        if prenda is not None and prenda.type == "MESH":
            prenda.select_set(True)
    for hijo in arm.children:
        if hijo.type != "MESH" or hijo == cuerpo:
            continue
        if "low-poly" in hijo.name.lower():
            continue
        hijo.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    if nombre_glb and "colores" in nombre_glb:
        for obj in bpy.context.view_layer.objects.selected:
            aplanar_tinte(obj)

    destino = ruta_glb(sexo, nombre_glb)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=destino,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_animations=True,
        export_animation_mode="ACTIVE_ACTIONS",
        export_nla_strips_merged_animation_name="squat_bodyweight",
        export_bake_animation=True,
        export_def_bones=True,
        export_skins=True,
        export_materials="EXPORT",
        export_anim_slide_to_zero=False,
    )
    if bpy.data.is_dirty:
        # La exportación no debe escribir el .blend. Este proceso termina sin guardar.
        pass

    glb = resumen_glb(destino)
    if not glb["animaciones"]:
        raise RuntimeError("Diagnóstico: el GLB no trae animaciones.")
    if not any(item["nombre"] == "squat_bodyweight" for item in glb["animaciones"]):
        raise RuntimeError(
            "Diagnóstico: el GLB no incluye squat_bodyweight. Trae: "
            + ", ".join(item["nombre"] or "" for item in glb["animaciones"])
        )
    if glb["skins"] < 1:
        raise RuntimeError("Diagnóstico: el GLB no trae skinning.")
    if not animacion_se_mueve(destino):
        raise RuntimeError("Diagnóstico: la animación exportada no cambia de pose.")

    informe = {
        "sexo": sexo or "base",
        "formas_horneadas": formas,
        "archivo_origen": bpy.data.filepath,
        "glb": destino,
        "bytes": os.path.getsize(destino),
        "accion": accion.name,
        "fotogramas": [round(float(v), 2) for v in accion.frame_range],
        "huesos_deformacion": len(deformacion),
        "restricciones_ik": ik,
        "origen_no_guardado": True,
        "glb_contenido": glb,
        "nota": (
            "El IK no viaja al navegador. export_bake_animation graba el movimiento "
            "ya resuelto en los huesos de deformación."
        ),
    }
    nombre_informe = "glb_export_report.json" if not sexo else f"glb_export_report_{sexo}.json"
    ruta_informe = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre_informe)
    with open(ruta_informe, "w", encoding="utf-8") as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
    print("GLB_OK", destino, "BYTES", informe["bytes"])
    print("ANIM", glb["animaciones"][0]["nombre"], "CANALES", glb["animaciones"][0]["canales"])


if __name__ == "__main__":
    main()
