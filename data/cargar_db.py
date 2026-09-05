import json
import sqlite3
import pandas as pd

# 1. Rutas de tus archivos
json_path = "ejercicios.json"
db_path = "../backend/gym.db"  # Apunta al archivo .db en la carpeta backend

# 2. Cargar el JSON
with open(json_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# 3. Convertir a DataFrame de Pandas
df = pd.DataFrame(data)

# 4. Conectar a SQLite y guardar la tabla
conn = sqlite3.connect(db_path)
df.to_sql("ejercicios", conn, if_exists="replace", index=False)
conn.close()

print(
    "¡Éxito! La tabla 'ejercicios' ha sido cargada en backend/gym.db con",
    len(df),
    "registros.",
)