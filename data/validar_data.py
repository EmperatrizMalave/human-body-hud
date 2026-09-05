import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "ejercicios.xlsx")

def auditar_dataset():
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ No se encontró el archivo: {EXCEL_PATH}")
        return

    df = pd.read_excel(EXCEL_PATH)

    print("==========================================")
    print("      REPORTE DE CALIDAD DE LA DATA       ")
    print("==========================================")
    print(f"📊 Total de filas (ejercicios): {len(df)}")
    print(f"📋 Columnas detectadas: {list(df.columns)}\n")

    # 1. Conteo de valores nulos (faltantes)
    print("1️⃣ VALORES FALTANTES POR COLUMNA:")
    nulos = df.isnull().sum()
    porcentaje_nulos = (df.isnull().sum() / len(df)) * 100
    
    df_nulos = pd.DataFrame({
        "Faltantes": nulos,
        "Porcentaje (%)": porcentaje_nulos.round(2)
    })
    print(df_nulos)
    print("-" * 40)

    # 2. Verificar duplicados por título
    duplicados = df.duplicated(subset=["Title"]).sum()
    print(f"\n2️⃣ EJERCICIOS DUPLICADOS: {duplicados}")

    # 3. Categorías disponibles para los filtros de la API
    print("\n3️⃣ CATEGORÍAS ENCONTRADAS PARA FILTROS:")
    if "BodyPart" in df.columns:
        print(f"  • Zonas corporales ({df['BodyPart'].nunique()}): {df['BodyPart'].dropna().unique().tolist()}")
    if "Level" in df.columns:
        print(f"  • Niveles ({df['Level'].nunique()}): {df['Level'].dropna().unique().tolist()}")
    if "Equipment" in df.columns:
        print(f"  • Equipamiento ({df['Equipment'].nunique()}): {df['Equipment'].dropna().unique().tolist()}")
    if "Type" in df.columns:
        print(f"  • Tipos ({df['Type'].nunique()}): {df['Type'].dropna().unique().tolist()}")
        
    print("\n==========================================")

if __name__ == "__main__":
    auditar_dataset()