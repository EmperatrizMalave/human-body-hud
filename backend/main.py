import os
import sqlite3
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# 1. INICIALIZACIÓN DE LA APLICACIÓN FASTAPI
# ==========================================
app = FastAPI(
    title="Cyber-HUD Fitness API",
    description="API REST para el dashboard de entrenamiento Cyber-HUD",
    version="2.0.2",
)

# ==========================================
# 1.5. CONFIGURACIÓN DE SEGURIDAD (CORS)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. RESOLUCIÓN DE RUTA DE LA BASE DE DATOS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "gym.db"))


# ==========================================
# 3. FUNCIÓN DE CONEXIÓN A SQLITE
# ==========================================
def get_db_connection():
    """Conecta a la base de datos y configura el formato de respuesta por columnas."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Nombres históricos: el JSON usa IS_SITTING; una carga vieja a SQLite
# dejó SENTADO_SITTING. Aceptamos ambos para no romper ningún dataset.
SITTING_COLUMNS = ("IS_SITTING", "SENTADO_SITTING")
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


def _normalizar_ejercicio(row):
    """Expone IS_SITTING y LOW_IMPACT como booleanos reales para el frontend."""
    item = dict(row)
    sentado = item.get("IS_SITTING", item.get("SENTADO_SITTING"))
    impacto = item.get("LOW_IMPACT")
    item["IS_SITTING"] = bool(sentado)
    item["LOW_IMPACT"] = bool(impacto)
    return item


# ==========================================
# 4. ENDPOINT DE BIENVENIDA / HEALTH CHECK
# ==========================================
@app.get("/")
def home():
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
        description="Si es true, solo ejercicios en postura sentada (Safe-Green)",
    ),
    low_impact: Optional[bool] = Query(
        None,
        description="Si es true, solo ejercicios de bajo impacto articular (Safe-Green)",
    ),
):
    """Consulta la base de datos aplicando filtros de alta precisión y paginación exacta."""

    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Base de datos no encontrada")

    conn = get_db_connection()
    cursor = conn.cursor()
    columnas = _columnas_tabla(conn)
    col_sitting = _resolver_columna(columnas, SITTING_COLUMNS)
    col_impact = _resolver_columna(columnas, IMPACT_COLUMNS)

    base_query = "FROM ejercicios WHERE 1=1"
    params = []

    # --- FILTRO GLOBAL DE BÚSQUEDA PRECISA ---
    if search:
        palabras = search.strip().split()
        for palabra in palabras:
            base_query += " AND (TITLE_ES LIKE ? OR TITLE_EN LIKE ? OR BODYPART_ES LIKE ?)"
            p = f"%{palabra}%"
            params.extend([p, p, p])

    # --- OTROS FILTROS ESPECÍFICOS ---
    if muscle_id:
        base_query += " AND (MUSCLE_ID LIKE ? OR BODYPART_ES LIKE ? OR BODYPART_EN LIKE ?)"
        params.extend([f"%{muscle_id}%", f"%{muscle_id}%", f"%{muscle_id}%"])

    if equipment:
        base_query += " AND (EQUIPMENT_ES LIKE ? OR EQUIPMENT_EN LIKE ?)"
        params.extend([f"%{equipment}%", f"%{equipment}%"])

    if level:
        base_query += " AND (LEVEL_ES LIKE ? OR LEVEL_EN LIKE ?)"
        params.extend([f"%{level}%", f"%{level}%"])

    # Safe-Green: el checkbox marcado significa "solo estos", no "excluir".
    # Si no viene el parámetro, no filtramos (catálogo completo).
    if is_sitting:
        if not col_sitting:
            conn.close()
            raise HTTPException(
                status_code=500,
                detail="No existe columna IS_SITTING ni SENTADO_SITTING",
            )
        base_query += f" AND {_es_verdadero_sql(col_sitting)}"

    if low_impact:
        if not col_impact:
            conn.close()
            raise HTTPException(
                status_code=500,
                detail="No existe columna LOW_IMPACT",
            )
        base_query += f" AND {_es_verdadero_sql(col_impact)}"

    # 1. Contar el total exacto de resultados
    cursor.execute(f"SELECT COUNT(*) as total {base_query}", tuple(params))
    total_registros = cursor.fetchone()["total"]

    # Calcular total de páginas
    total_paginas = (total_registros + limit - 1) // limit if total_registros > 0 else 1
    
    if page > total_paginas:
        page = total_paginas

    # 2. Calcular el desplazamiento (OFFSET)
    offset = (page - 1) * limit

    # 3. Consulta final aplicando LIMIT y OFFSET
    query_final = f"SELECT * {base_query} LIMIT ? OFFSET ?"
    params_finales = params + [limit, offset]

    cursor.execute(query_final, tuple(params_finales))
    rows = cursor.fetchall()
    conn.close()

    ejercicios = [_normalizar_ejercicio(row) for row in rows]

    return {
        "total_registros": total_registros,
        "total_paginas": total_paginas,
        "pagina_actual": page,
        "por_pagina": limit,
        "data": ejercicios,
    }