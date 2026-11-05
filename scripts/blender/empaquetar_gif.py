# empaquetar_gif.py
# Junta los PNG de _frames_squat en assets/previews/squat_bodyweight.gif.
# Se ejecuta con Pillow, sin guardar nada dentro de Blender:
#   uv run --with pillow python scripts/blender/empaquetar_gif.py

import glob
import os
import shutil

from PIL import Image


def main():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    frames = sorted(glob.glob(os.path.join(carpeta, "_frames_squat", "frame_*.png")))
    if len(frames) < 2:
        raise RuntimeError("No hay suficientes fotogramas en scripts/blender/_frames_squat.")

    imagenes = [Image.open(ruta).convert("RGB") for ruta in frames]
    paleta = imagenes[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    cuadros = [imagen.quantize(palette=paleta, dither=Image.Dither.NONE) for imagen in imagenes]

    destino_dir = os.path.abspath(os.path.join(carpeta, "..", "..", "assets", "previews"))
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, "squat_bodyweight.gif")
    # El render avanza de 2 en 2 sobre 24 fps, así que cada cuadro dura 2/24 s.
    cuadros[0].save(
        destino,
        save_all=True,
        append_images=cuadros[1:],
        duration=83,
        loop=0,
        optimize=True,
        disposal=2,
    )
    for imagen in imagenes:
        imagen.close()
    shutil.rmtree(os.path.join(carpeta, "_frames_squat"))
    print("GIF_OK", destino, "cuadros", len(cuadros))


if __name__ == "__main__":
    main()
