# Scripts de Blender

El archivo `assets/models/personaje_rigged.blend` no está en el repositorio.
La inspección usó el maniquí MPFB ya guardado:

`C:\Users\emper\OneDrive\Documents\personaje_base_woman.blend.blend`

Ese archivo no se modifica. La sentadilla se guarda en
`assets/models/personaje_squat_bodyweight.blend`.

Desde PowerShell, en la raíz del proyecto:

```powershell
cd C:\Users\emper\Documents\dev\human-body-hud

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "C:\Users\emper\OneDrive\Documents\personaje_base_woman.blend.blend" `
  --python "scripts\blender\inspect_rig.py" `
  -- "scripts\blender\rig_inspection.json"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "C:\Users\emper\OneDrive\Documents\personaje_base_woman.blend.blend" `
  --python "scripts\blender\create_squat.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\render_squat_gif.py"
```

El último comando renderiza la acción `squat_bodyweight` y escribe
`assets\previews\squat_bodyweight.gif`. No vuelve a posar al maniquí
ni guarda el `.blend`. Usa la sentadilla que ya está en el archivo.

Para revisar la animación, abre `assets\models\personaje_squat_bodyweight.blend`,
selecciona `Human.rig` y reproduce del fotograma 1 al 48.
La acción se llama `squat_bodyweight`.

Para llevar esa sentadilla al navegador, sin guardar el `.blend`:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\exportar_glb.py"
```

El par queda en dos copias. La mujer es el archivo de origen sin cambios de
fenotipo. El hombre usa el mismo Standard Rig y la misma acción:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\crear_hombre.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight_mujer.blend" `
  --python "scripts\blender\vestir_mujer.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight_mujer_vestida.blend" `
  --python "scripts\blender\exportar_glb.py" -- mujer

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight_hombre.blend" `
  --python "scripts\blender\exportar_glb.py" -- hombre
```

Los GLB quedan en `frontend\modelos\mujer\` y `frontend\modelos\hombre\`.
El IK se hornea en los huesos de deformación, porque el navegador no
reproduce las restricciones. El `.blend` original no se guarda.

## Regiones musculares

`assets/models/personaje_muscular.blend` no está en el proyecto.
La prueba usa la copia MPFB que ya tiene la sentadilla:

`assets/models/personaje_squat_bodyweight.blend`

Ese archivo no se modifica. El resultado queda en
`assets/models/personaje_muscular_test.blend`.

```powershell
cd C:\Users\emper\Documents\dev\human-body-hud

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\inspect_muscles.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\marcar_cuadriceps.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_muscular_test.blend" `
  --python "scripts\blender\render_musculos.py"
```

La inspección escribe `scripts\blender\muscles_inspection.json`.
El pintado escribe `scripts\blender\cuadriceps_report.json`,
`scripts\blender\mascaras\cuadriceps.json` y el `.blend` de prueba.
Las imágenes quedan en `assets\previews\cuadriceps_frontal.png`
y `assets\previews\cuadriceps_lateral.png`.

Para corregir el borde una sola vez: abre el `.blend` de prueba, selecciona
`Human`, entra en Modo Edición, marca las caras del cuádriceps y ejecuta
`scripts\blender\guardar_mascara.py` desde el espacio de Scripting.
Eso guarda la selección. Para volver a pintar el archivo de prueba:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\guardar_mascara.py" `
  -- aplicar
```

## Máscara UV

Esa prueba por caras queda en `personaje_muscular_test.blend`. La versión
con textura, que es la que hay que revisar, se genera así:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\inspect_uv.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\crear_mascara_uv.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_muscular_uv_test.blend" `
  --python "scripts\blender\render_mascara_uv.py"
```

El material se llama `CuerpoMuscular`. Tiene dos nodos de color, `BODY_BASE`
y `MUSCLE_ACTIVE`, mezclados por la imagen `MascaraCuadriceps`. El archivo
nuevo es `assets\models\personaje_muscular_uv_test.blend`. La textura también
está en `assets\textures\mascara_cuadriceps.png`.

Para corregir el dibujo sin reconstruir el material:

1. Abre `personaje_muscular_uv_test.blend`.
2. Selecciona `Human` y entra en el modo Texture Paint, o abre la imagen
   `MascaraCuadriceps` en el Editor de imágenes.
3. Blanco añade cuádriceps, negro lo quita, el gris es el borde suave.
4. Guarda el `.blend`.

Si editas el PNG fuera de Blender, recarga solo la imagen:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_muscular_uv_test.blend" `
  --python "scripts\blender\crear_mascara_uv.py" `
  -- recargar
```

No vuelvas a ejecutar `crear_mascara_uv.py` sin la palabra `recargar`:
ese comando regenera la máscara y sustituye lo pintado a mano.

## Máscara UV v2

La versión con tres formas separadas sale de la misma sentadilla y se guarda
en `assets\models\personaje_muscular_uv_v2.blend`. No modifica los archivos
anteriores.

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_squat_bodyweight.blend" `
  --python "scripts\blender\crear_mascara_uv_v2.py"

& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background "assets\models\personaje_muscular_uv_v2.blend" `
  --python "scripts\blender\render_mascara_uv_v2.py"
```

La imagen se llama `MascaraCuadricepsV2` y también está en
`assets\textures\mascara_cuadriceps_v2.png`. El material sigue siendo
`CuerpoMuscular`: `BODY_BASE` y `MUSCLE_ACTIVE` mezclados por el canal rojo
de esa imagen.

Para corregir las formas una sola vez, sin reconstruir el material:

1. Abre `personaje_muscular_uv_v2.blend`.
2. Selecciona `Human` y entra en Texture Paint.
3. Pinta la imagen `MascaraCuadricepsV2`. Blanco añade músculo, negro lo quita.
4. Guarda el `.blend`.

No vuelvas a lanzar `crear_mascara_uv_v2.py` después de pintar: regenera la
plantilla y borra la corrección.
