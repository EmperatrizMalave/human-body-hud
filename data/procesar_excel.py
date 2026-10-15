import json
import os
import pandas as pd


def convert_excel_to_json(excel_file_name, json_file_name):
  # Obtener la ruta del directorio donde se encuentra este mismo archivo script
  script_dir = os.path.dirname(os.path.abspath(__file__))

  # Construir las rutas absolutas a los archivos
  excel_path = os.path.join(script_dir, excel_file_name)
  json_path = os.path.join(script_dir, json_file_name)

  print(f"Leyendo archivo Excel desde: {excel_path}")

  # Cargar el Excel
  df = pd.read_excel(excel_path)

  # Convertir el tipo de datos a objeto y reemplazar NaN por None (que en JSON se traduce a null)
  df = df.astype(object).where(pd.notnull(df), None)

  # Convertir a lista de diccionarios
  records = df.to_dict(orient="records")

  # Guardar como JSON con codificación UTF-8
  with open(json_path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

  print(
      f"¡Éxito! Se procesaron {len(records)} registros limpios desde "
      f'"{excel_file_name}" a "{json_file_name}".'
  )


if __name__ == "__main__":
  # Usar ejercicios_corregidos.xlsx como archivo de origen
  convert_excel_to_json("ejercicios_corregidos.xlsx", "ejercicios.json")