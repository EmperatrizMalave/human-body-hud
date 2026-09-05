import json
from pathlib import Path
import pandas as pd


def convert_excel_to_json(excel_path: str, json_path: str):
  # Cargar el archivo Excel
  df = pd.read_excel(excel_path)

  # 1. Eliminar columnas de índices sin nombre ("Unnamed: 0")
  df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

  # 2. Limpiar espacios en blanco en los nombres de las columnas
  df.columns = df.columns.str.strip()

  # 3. Limpiar celdas vacías o nulas
  df = df.fillna('')

  # 4. Rellenar campos vacíos en español/inglés con un valor por defecto si la celda quedó vacía en Excel
  if 'TITLE_ES' in df.columns:
    df['TITLE_ES'] = df.apply(
        lambda r: r['TITLE_ES'] if r['TITLE_ES'] != '' else r['TITLE_EN'],
        axis=1,
    )
  if 'DESC_EN' in df.columns:
    df['DESC_EN'] = df.apply(
        lambda r: r['DESC_EN']
        if r['DESC_EN'] != ''
        else (
            f"Exercise type {r.get('TYPE_EN', '')} targeting the"
            f" {r.get('BODYPART_EN', '')} area ({r.get('TITLE_EN', '')})."
        ),
        axis=1,
    )

  # 5. Formatear datos para serialización a JSON
  for col in df.columns:
    df[col] = df[col].apply(
        lambda x: (
            x.isoformat()
            if hasattr(x, 'isoformat')
            else (
                int(x)
                if isinstance(x, float) and x.is_integer()
                else (float(x) if isinstance(x, (int, float)) else str(x))
            )
        )
    )

  # Convertir a lista de diccionarios
  records = df.to_dict(orient='records')

  # Guardar como JSON con codificación UTF-8
  with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

  print(
      f'¡Éxito! Se procesaron {len(records)} registros limpios desde {excel_path}'
      f' a {json_path}'
  )


if __name__ == '__main__':
  convert_excel_to_json('data/ejercicios.xlsx', 'data/ejercicios.json')