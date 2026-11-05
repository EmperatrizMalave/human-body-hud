import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

# ==========================================
# 1. INICIALIZACIÓN DE LA APLICACIÓN FASTAPI
# ==========================================
app = FastAPI(
    title="Cyber-HUD Fitness API",
    description="API REST para el dashboard de entrenamiento Cyber-HUD",
    version="2.0.2",
)

# CORS: el HUD en :8000 es same-origin (no usa esto). :3000 es Live Server.
# credentials=False: la sesión v1 es localStorage, no cookie. * + credentials
# es inválido en el navegador y peligroso el día que haya login.
_ORIGENES_HUD = (
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_ORIGENES_HUD),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ==========================================
# 2. RESOLUCIÓN DE RUTA DE LA BASE DE DATOS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "gym.db"))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
FEEDBACK_PATH = os.path.abspath(os.path.join(BASE_DIR, "feedback.json"))
FEEDBACK_LOCK_PATH = FEEDBACK_PATH + ".lock"
_feedback_hilo = threading.Lock()


# ==========================================
# 3. FUNCIÓN DE CONEXIÓN A SQLITE
# ==========================================
@contextmanager
def get_db_connection():
    """Abre SQLite y la cierra siempre (éxito, HTTPException o error de SQL)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Nombres históricos: el JSON usa IS_SITTING; una carga vieja a SQLite
# dejó SENTADO_SITTING. Aceptamos ambos para no romper ningún dataset.
SITTING_COLUMNS = ("IS_SITTING", "SENTADO_SITTING")
NO_LEGS_COLUMNS = ("NO_LEGS",)
IMPACT_COLUMNS = ("LOW_IMPACT",)


def _columnas_tabla(conn):
    return {row[1] for row in conn.execute("PRAGMA table_info(ejercicios)")}


def _resolver_columna(columnas, candidatas):
    """Devuelve el primer nombre de columna que sí existe en gym.db."""
    for nombre in candidatas:
        if nombre in columnas:
            return nombre
    return None


def _es_verdadero_sql(columna):
    """pandas guardó booleanos como 0.0 / 1.0 (REAL). CAST los vuelve 0 / 1."""
    return f"CAST({columna} AS INTEGER) = 1"


def _identificador_sql(nombre):
    """Comillas para columnas como Unnamed: 0 (pandas)."""
    return '"' + str(nombre).replace('"', '""') + '"'


def _like_contiene(fragmento):
    """Texto del usuario como substring. % y _ dejan de ser comodines de LIKE."""
    literal = (
        str(fragmento)
        .replace("#", "##")
        .replace("%", "#%")
        .replace("_", "#_")
    )
    return f"%{literal}%"


def _sql_like(columnas):
    return "(" + " OR ".join(f"{col} LIKE ? ESCAPE '#'" for col in columnas) + ")"


def _columna_id(columnas):
    """El JSON de pandas guarda el índice como Unnamed: 0; un id propio gana."""
    return _resolver_columna(columnas, ("id", "Unnamed: 0"))


def _sql_orden_catalogo(col_id):
    """Orden estable para LIMIT/OFFSET. Sin esto, SQLite puede reordenar cada SELECT."""
    if col_id:
        ident = _identificador_sql(col_id)
        return f" ORDER BY CAST({ident} AS INTEGER) ASC, rowid ASC"
    return " ORDER BY rowid ASC"


def _entero_id(valor):
    if valor is None or valor is False:
        return None
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return numero


# Columnas del dump que el HUD no usa (placeholders, medidas vacías, género casi constante).
_CAMPOS_NO_PRODUCTO = (
    "IMAGE_URL",
    "HEIGHT_CM",
    "WAIST_CM",
    "NECK_CM",
    "HIP_CM",
    "GENDER_EN",
    "GENDER_ES",
)


def _bajo_impacto_producto(item):
    """NO_LEGS se revisó ficha a ficha. LOW_IMPACT del dump (535) no.
    En producto solo contamos estiramientos: el resto se vendía como articular
    y incluía plank jacks."""
    if not item.get("LOW_IMPACT"):
        return False
    return str(item.get("TYPE_EN") or "").strip().lower() == "stretching"


def _normalizar_ejercicio(row):
    """Expone flags de inclusión como booleanos reales para el frontend."""
    item = dict(row)
    for campo in _CAMPOS_NO_PRODUCTO:
        item.pop(campo, None)
    sentado = item.get("IS_SITTING", item.get("SENTADO_SITTING"))
    sin_piernas = item.get("NO_LEGS")
    item["IS_SITTING"] = bool(sentado)
    # Si el dataset aún no trae NO_LEGS, no inventamos inclusión.
    item["NO_LEGS"] = bool(sin_piernas) if sin_piernas is not None else False
    item["LOW_IMPACT"] = _bajo_impacto_producto(item)
    # DNI de ficha: no uses título+equipo (hay títulos repetidos).
    item["id"] = _entero_id(item.get("id", item.get("Unnamed: 0")))
    return item


# ==========================================
# 4. HEALTH CHECK (no usamos "/" para dejar el HUD ahí)
# ==========================================
@app.get("/api/health")
def health():
    return {
        "status": "online",
        "system": "Cyber-HUD Backend Engine",
        "database_path": DB_PATH,
        "database_found": os.path.exists(DB_PATH),
    }


# ==========================================
# 5. ENDPOINT PRINCIPAL: /api/ejercicios
# ==========================================
@app.get("/api/ejercicios")
def obtener_ejercicios(
    page: int = Query(1, ge=1, description="Número de página actual"),
    limit: int = Query(20, ge=1, le=100, description="Registros por página"),
    search: Optional[str] = Query(None, description="Término de búsqueda global"),
    muscle_id: Optional[str] = None,
    equipment: Optional[str] = None,
    level: Optional[str] = None,
    is_sitting: Optional[bool] = Query(
        None,
        description="Si es true, solo ejercicios en postura sentada (banco / máquina / silla)",
    ),
    no_legs: Optional[bool] = Query(
        None,
        description="Si es true, solo ejercicios cuyo motor no es el tren inferior (Safe-Green)",
    ),
    low_impact: Optional[bool] = Query(
        None,
        description="Si es true, solo ejercicios de bajo impacto articular (Safe-Green)",
    ),
):
    """Consulta la base de datos aplicando filtros de alta precisión y paginación exacta."""

    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Base de datos no encontrada")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        columnas = _columnas_tabla(conn)
        col_sitting = _resolver_columna(columnas, SITTING_COLUMNS)
        col_no_legs = _resolver_columna(columnas, NO_LEGS_COLUMNS)
        col_impact = _resolver_columna(columnas, IMPACT_COLUMNS)
        col_id = _columna_id(columnas)

        base_query = "FROM ejercicios WHERE 1=1"
        params = []

        # --- FILTRO GLOBAL DE BÚSQUEDA PRECISA ---
        if search:
            palabras = search.strip().split()
            for palabra in palabras:
                cols = ("TITLE_ES", "TITLE_EN", "BODYPART_ES")
                base_query += f" AND {_sql_like(cols)}"
                params.extend([_like_contiene(palabra)] * len(cols))

        # --- OTROS FILTROS ESPECÍFICOS ---
        if muscle_id:
            cols = ("MUSCLE_ID", "BODYPART_ES", "BODYPART_EN")
            base_query += f" AND {_sql_like(cols)}"
            params.extend([_like_contiene(muscle_id)] * len(cols))

        if equipment:
            cols = ("EQUIPMENT_ES", "EQUIPMENT_EN")
            base_query += f" AND {_sql_like(cols)}"
            params.extend([_like_contiene(equipment)] * len(cols))

        if level:
            cols = ("LEVEL_ES", "LEVEL_EN")
            base_query += f" AND {_sql_like(cols)}"
            params.extend([_like_contiene(level)] * len(cols))

        # Safe-Green: el checkbox marcado significa "solo estos", no "excluir".
        # Si no viene el parámetro, no filtramos (catálogo completo).
        if is_sitting:
            if not col_sitting:
                raise HTTPException(
                    status_code=500,
                    detail="No existe columna IS_SITTING ni SENTADO_SITTING",
                )
            base_query += f" AND {_es_verdadero_sql(col_sitting)}"

        if no_legs:
            if not col_no_legs:
                raise HTTPException(
                    status_code=500,
                    detail="No existe columna NO_LEGS",
                )
            base_query += f" AND {_es_verdadero_sql(col_no_legs)}"

        if low_impact:
            if not col_impact:
                raise HTTPException(
                    status_code=500,
                    detail="No existe columna LOW_IMPACT",
                )
            # Misma regla que _bajo_impacto_producto: no filtrar los 535 crudos.
            base_query += (
                f" AND {_es_verdadero_sql(col_impact)}"
                " AND lower(TYPE_EN) = 'stretching'"
            )

        # 1. Contar el total exacto de resultados
        cursor.execute(f"SELECT COUNT(*) as total {base_query}", tuple(params))
        total_registros = cursor.fetchone()["total"]

        # Calcular total de páginas
        total_paginas = (total_registros + limit - 1) // limit if total_registros > 0 else 1

        if page > total_paginas:
            page = total_paginas

        # 2. Calcular el desplazamiento (OFFSET)
        offset = (page - 1) * limit

        # 3. Mismo orden en cada request: OFFSET 40 = siempre las filas 41–60 de ese orden.
        query_final = f"SELECT * {base_query}{_sql_orden_catalogo(col_id)} LIMIT ? OFFSET ?"
        params_finales = params + [limit, offset]

        cursor.execute(query_final, tuple(params_finales))
        ejercicios = [_normalizar_ejercicio(row) for row in cursor.fetchall()]

    return {
        "total_registros": total_registros,
        "total_paginas": total_paginas,
        "pagina_actual": page,
        "por_pagina": limit,
        "data": ejercicios,
    }


@app.get("/api/ejercicios/{ejercicio_id}")
def obtener_ejercicio(ejercicio_id: int):
    """Una ficha por id estable (Unnamed: 0 en gym.db)."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Base de datos no encontrada")

    with get_db_connection() as conn:
        columnas = _columnas_tabla(conn)
        col_id = _columna_id(columnas)
        if not col_id:
            raise HTTPException(status_code=500, detail="No existe columna de id")
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM ejercicios WHERE CAST({_identificador_sql(col_id)} AS INTEGER) = ? LIMIT 1",
            (ejercicio_id,),
        )
        row = cursor.fetchone()
        ejercicio = _normalizar_ejercicio(row) if row is not None else None

    if ejercicio is None:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    return ejercicio


class FeedbackIn(BaseModel):
    nombre: str = Field(default="", max_length=80)
    mensaje: str = Field(..., min_length=10, max_length=2000)
    tipo: Literal["sugerencia", "error", "otro"] = "sugerencia"

    @field_validator("nombre", "mensaje")
    @classmethod
    def recortar(cls, valor: str) -> str:
        return valor.strip()


def _adquirir_candado_archivo(candado):
    if os.name == "nt":
        import msvcrt

        candado.seek(0, os.SEEK_END)
        if candado.tell() == 0:
            candado.write(b"0")
            candado.flush()
        candado.seek(0)
        msvcrt.locking(candado.fileno(), msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(candado.fileno(), fcntl.LOCK_EX)


def _soltar_candado_archivo(candado):
    if os.name == "nt":
        import msvcrt

        candado.seek(0)
        msvcrt.locking(candado.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(candado.fileno(), fcntl.LOCK_UN)


@contextmanager
def _bloqueo_feedback():
    """Un solo lector-escritor a la vez: hilos del proceso y otros procesos Uvicorn."""
    with open(FEEDBACK_LOCK_PATH, "a+b") as candado:
        _adquirir_candado_archivo(candado)
        try:
            with _feedback_hilo:
                yield
        finally:
            _soltar_candado_archivo(candado)


def _leer_historial_feedback():
    if not os.path.exists(FEEDBACK_PATH):
        return []
    with open(FEEDBACK_PATH, encoding="utf-8") as archivo:
        try:
            historial = json.load(archivo)
        except json.JSONDecodeError:
            return []
    return historial if isinstance(historial, list) else []


def _escribir_historial_feedback(historial):
    temporal = FEEDBACK_PATH + ".tmp"
    with open(temporal, "w", encoding="utf-8") as archivo:
        json.dump(historial, archivo, ensure_ascii=False, indent=2)
        archivo.flush()
        os.fsync(archivo.fileno())
    os.replace(temporal, FEEDBACK_PATH)


@app.post("/api/feedback")
def guardar_feedback(body: FeedbackIn):
    """Guarda opiniones en backend/feedback.json (archivo local, no base de datos)."""
    entrada = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "nombre": body.nombre or "anónimo",
        "tipo": body.tipo,
        "mensaje": body.mensaje,
    }
    with _bloqueo_feedback():
        historial = _leer_historial_feedback()
        historial.append(entrada)
        _escribir_historial_feedback(historial)
        total = len(historial)
    return {"ok": True, "total": total}


# El mount en "/" va AL FINAL: si va antes, tapa /api/*.
# html=True sirve index.html cuando entras a http://127.0.0.1:8000/
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")