# Cyber-HUD

Catálogo de ejercicios con interfaz HUD: zonas musculares, búsqueda, modo Safe-Green (sin usar las piernas / bajo impacto) y ficha de detalle.

Un solo servidor: FastAPI sirve la API **y** el HTML.

## Arranque rápido

Necesitas el entorno del repo (`.venv` o [uv](https://docs.astral.sh/uv/)).

```powershell
cd C:\Users\emper\Documents\dev\human-body-hud\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

En PowerShell la ruta al Python es `..\.venv\Scripts\python.exe` (sin espacio después de `..`).

Cuando veas `Uvicorn running on http://127.0.0.1:8000`, abre:

- HUD: http://127.0.0.1:8000/
- Salud de la API: http://127.0.0.1:8000/api/health  
  Debe decir `"database_found": true`.

`--reload` recarga `main.py` al guardar. Los cambios de `frontend/` se ven con F5.

No uses Live Server ni `python -m http.server` como flujo principal. Si abres el HTML en el puerto 3000, el catálogo solo carga si FastAPI ya está en el **8000**.

Si el 8000 está ocupado (`WinError 10013`), cierra el `uvicorn` anterior (en esa terminal `Ctrl+C`) y vuelve a lanzar el comando. El flujo oficial es el puerto **8000**.

## Estructura

```
backend/   main.py + gym.db     API y base SQLite
frontend/  index.html, style.css, app.js
data/      ejercicios.json y scripts de carga
```

## Regenerar `gym.db`

La base que usa la app es **`backend/gym.db`**, no un archivo en la raíz.

Hay que ejecutar el script **desde `data/`**, porque las rutas del script son relativas:

```powershell
cd C:\Users\emper\Documents\dev\human-body-hud\data
..\.venv\Scripts\python.exe cargar_db.py
```

Eso lee `data/ejercicios.json` y **reemplaza** la tabla `ejercicios` en `backend/gym.db`. Luego recarga el HUD.

Pandas tiene que estar instalado en ese Python. Si falla el import:

```powershell
..\.venv\Scripts\python.exe -m pip install pandas
```

(o `uv run --with pandas cargar_db.py` desde `data/`).

### Opcional: Excel → JSON → SQLite

1. `procesar_excel.py` convierte `ejercicios_corregidos.xlsx` en `ejercicios.json` (hace falta `openpyxl`).
2. Vuelve a correr `cargar_db.py`.

## API

| Método | Ruta | Uso |
|---|---|---|
| GET | `/api/health` | ¿Está la DB? |
| GET | `/api/ejercicios` | Catálogo (`page`, `limit`, `search`, `muscle_id`, `no_legs`, `is_sitting`, `low_impact`) |
| POST | `/api/feedback` | Opiniones del diálogo (se guardan en `backend/feedback.json`, no en git) |

## Dependencias de la app

Están en `pyproject.toml`: FastAPI, Pydantic, Uvicorn. Los scripts de `data/` usan pandas aparte.
