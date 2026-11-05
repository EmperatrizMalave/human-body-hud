import json
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "ejercicios.json"
DB_PATH = BASE_DIR.parent / "backend" / "gym.db"

# Flags de inclusión: INTEGER 0/1 (no REAL 0.0 de pandas).
COLUMNAS_FLAG = ("IS_SITTING", "LOW_IMPACT", "NO_LEGS")
COLUMNAS_REAL = ("RATING",)

# No van al producto: 2918 placeholders, medidas 100% nulas, género casi constante.
COLUMNAS_OMITIR = (
    "IMAGE_URL",
    "HEIGHT_CM",
    "WAIST_CM",
    "NECK_CM",
    "HIP_CM",
    "GENDER_EN",
    "GENDER_ES",
)

# Índices alineados con GET /api/ejercicios (igualdad). LIKE '%x%' no los usa.
INDICES = (
    "CREATE INDEX idx_ejercicios_muscle ON ejercicios (MUSCLE_ID)",
    "CREATE INDEX idx_ejercicios_no_legs ON ejercicios (NO_LEGS)",
    "CREATE INDEX idx_ejercicios_low_impact ON ejercicios (LOW_IMPACT)",
    "CREATE INDEX idx_ejercicios_sitting ON ejercicios (IS_SITTING)",
)


def _ident(nombre):
    return '"' + str(nombre).replace('"', '""') + '"'


def _tipo_sql(columna):
    if columna in COLUMNAS_FLAG:
        return "INTEGER NOT NULL DEFAULT 0"
    if columna in COLUMNAS_REAL:
        return "REAL"
    return "TEXT"


def _sql_create(columnas):
    piezas = ["id INTEGER PRIMARY KEY NOT NULL"]
    for col in columnas:
        if col == "id":
            continue
        piezas.append(f"{_ident(col)} {_tipo_sql(col)}")
    return "CREATE TABLE ejercicios (\n    " + ",\n    ".join(piezas) + "\n)"


def _preparar_dataframe(data):
    df = pd.DataFrame(data)
    if "id" in df.columns:
        pass
    elif "Unnamed: 0" in df.columns:
        df = df.rename(columns={"Unnamed: 0": "id"})
    else:
        df.insert(0, "id", range(len(df)))

    df["id"] = pd.to_numeric(df["id"], errors="raise").astype("int64")
    if df["id"].isna().any() or df["id"].duplicated().any():
        raise SystemExit("id nulo o duplicado: el JSON no sirve como catálogo.")

    for col in COLUMNAS_FLAG:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(bool).astype("int64")

    omitir = {c for c in COLUMNAS_OMITIR if c in df.columns}
    if omitir:
        df = df.drop(columns=list(omitir))

    # id primero: coincide con PRIMARY KEY y con item["id"] de la API.
    resto = [c for c in df.columns if c != "id"]
    return df[["id", *resto]]


def cargar():
    with JSON_PATH.open(encoding="utf-8") as archivo:
        data = json.load(archivo)
    df = _preparar_dataframe(data)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DROP TABLE IF EXISTS ejercicios")
        conn.execute(_sql_create(list(df.columns)))
        df.to_sql("ejercicios", conn, if_exists="append", index=False)
        for sql in INDICES:
            conn.execute(sql)
        conn.commit()
    finally:
        conn.close()

    print(
        f"Tabla ejercicios en {DB_PATH.name}: {len(df)} filas, "
        f"PRIMARY KEY id, {len(INDICES)} índices."
    )


if __name__ == "__main__":
    cargar()
