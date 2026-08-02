import os
import pandas as pd

def find_excel_file():
    """
    Busca automáticamente el archivo de datos Excel ('data.xlsx' o 'data.xls').
    """
    candidates = ['data.xlsx', 'data.xls']
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    # Si no se encuentra con nombre exacto, buscar cualquier excel que empiece por 'data'
    for f in os.listdir('.'):
        if f.lower().startswith('data') and f.lower().endswith(('.xlsx', '.xls')):
            return f
    return None

def excel_Localizacion():
    excel_path = find_excel_file()
    if not excel_path:
        print("⚠️ No se encontró el archivo de datos Excel (data.xlsx o data.xls).")
        return pd.DataFrame(), [], [], [], [], [], [], []

    try:
        df_excel = pd.read_excel(excel_path, sheet_name="LOCALIZACION")
    except Exception as e:
        print(f"⚠️ No se pudo leer la hoja 'LOCALIZACION' de {excel_path}: {e}")
        return pd.DataFrame(), [], [], [], [], [], [], []

    norte_GMS = []
    este_GMS = []
    color_GMS = []
    tipo_icon = []
    direccion = []
    sobrenombre = []
    feature = []

    # Determinar longitud segura
    rows_count = len(df_excel)
    if rows_count > 0 and pd.notna(df_excel.iloc[0, 0]) and isinstance(df_excel.iloc[0, 0], (int, float)):
        # Si la celda (0,0) especifica la cantidad de filas
        declared_len = int(df_excel.iloc[0, 0])
        dataset_len = min(declared_len, rows_count)
    else:
        dataset_len = rows_count

    for i in range(dataset_len):
        try:
            norte_val = df_excel.iloc[i, 6]
            este_val = df_excel.iloc[i, 11]

            if pd.isna(norte_val) or pd.isna(este_val):
                continue

            norte = float(norte_val)
            este = float(este_val)

            color = str(df_excel.iloc[i, 12]) if df_excel.shape[1] > 12 and pd.notna(df_excel.iloc[i, 12]) else 'blue'
            tipo = str(df_excel.iloc[i, 13]) if df_excel.shape[1] > 13 and pd.notna(df_excel.iloc[i, 13]) else 'Default'
            dir_icon = str(df_excel.iloc[i, 14]) if df_excel.shape[1] > 14 and pd.notna(df_excel.iloc[i, 14]) else ''
            sobrenom = str(df_excel.iloc[i, 15]) if df_excel.shape[1] > 15 and pd.notna(df_excel.iloc[i, 15]) else f"Punto_{i+1}"

            norte_GMS.append(norte)
            este_GMS.append(este)
            color_GMS.append(color)
            tipo_icon.append(tipo)
            direccion.append(dir_icon)
            sobrenombre.append(sobrenom)
            feature.append([norte, este])
        except Exception:
            continue

    data = pd.DataFrame(feature, columns=["Norte/Sur", "Este/Oeste"])
    print(f"\n Coordenadas de Localización ({len(feature)} puntos): \n", data)
    return data, norte_GMS, este_GMS, feature, color_GMS, tipo_icon, direccion, sobrenombre

def excel_Linea():
    excel_path = find_excel_file()
    if not excel_path:
        return pd.DataFrame(), [], [], []

    try:
        df_excel = pd.read_excel(excel_path, sheet_name="LINEA")
    except Exception as e:
        print(f"⚠️ No se pudo leer la hoja 'LINEA': {e}")
        return pd.DataFrame(), [], [], []

    norte_GMS = []
    este_GMS = []
    feature = []

    rows_count = len(df_excel)
    if rows_count > 0 and pd.notna(df_excel.iloc[0, 0]) and isinstance(df_excel.iloc[0, 0], (int, float)):
        dataset_len = min(int(df_excel.iloc[0, 0]), rows_count)
    else:
        dataset_len = rows_count

    for i in range(dataset_len):
        try:
            norte_val = df_excel.iloc[i, 6]
            este_val = df_excel.iloc[i, 11]

            if pd.isna(norte_val) or pd.isna(este_val):
                continue

            norte = float(norte_val)
            este = float(este_val)

            norte_GMS.append(norte)
            este_GMS.append(este)
            feature.append([norte, este])
        except Exception:
            continue

    data = pd.DataFrame(feature, columns=["Norte/Sur", "Este/Oeste"])
    print(f"\n Vértices Polilínea ({len(feature)} puntos): \n", data)
    return data, norte_GMS, este_GMS, feature

def excel_Circulo():
    excel_path = find_excel_file()
    if not excel_path:
        return pd.DataFrame(), [], [], [], []

    try:
        df_excel = pd.read_excel(excel_path, sheet_name="CIRCULO")
    except Exception as e:
        print(f"⚠️ No se pudo leer la hoja 'CIRCULO': {e}")
        return pd.DataFrame(), [], [], [], []

    norte_GMS = []
    este_GMS = []
    radio = []
    feature = []

    rows_count = len(df_excel)
    if rows_count > 0 and pd.notna(df_excel.iloc[0, 0]) and isinstance(df_excel.iloc[0, 0], (int, float)):
        dataset_len = min(int(df_excel.iloc[0, 0]), rows_count)
    else:
        dataset_len = rows_count

    for i in range(dataset_len):
        try:
            norte_val = df_excel.iloc[i, 6]
            este_val = df_excel.iloc[i, 11]

            if pd.isna(norte_val) or pd.isna(este_val):
                continue

            norte = float(norte_val)
            este = float(este_val)
            rad_val = float(df_excel.iloc[i, 12]) if df_excel.shape[1] > 12 and pd.notna(df_excel.iloc[i, 12]) else 100.0

            norte_GMS.append(norte)
            este_GMS.append(este)
            radio.append(rad_val)
            feature.append([norte, este])
        except Exception:
            continue

    data = pd.DataFrame(feature, columns=["Norte/Sur", "Este/Oeste"])
    print(f"\n Coordenadas Círculo ({len(feature)} elementos): \n", data)
    return data, norte_GMS, este_GMS, feature, radio

def excel_PuntoDistAng():
    excel_path = find_excel_file()
    if not excel_path:
        return pd.DataFrame(), [], [], [], [], [], []

    try:
        df_excel = pd.read_excel(excel_path, sheet_name="P_ANG_DIST")
    except Exception as e:
        print(f"⚠️ No se pudo leer la hoja 'P_ANG_DIST': {e}")
        return pd.DataFrame(), [], [], [], [], [], []

    norte_GMS = []
    este_GMS = []
    angulo = []
    distancia = []
    heatmap = []
    feature = []

    rows_count = len(df_excel)
    if rows_count > 0 and pd.notna(df_excel.iloc[0, 0]) and isinstance(df_excel.iloc[0, 0], (int, float)):
        dataset_len = min(int(df_excel.iloc[0, 0]), rows_count)
    else:
        dataset_len = rows_count

    for i in range(dataset_len):
        try:
            norte_val = df_excel.iloc[i, 6]
            este_val = df_excel.iloc[i, 11]

            if pd.isna(norte_val) or pd.isna(este_val):
                continue

            norte = float(norte_val)
            este = float(este_val)

            ang_val = float(df_excel.iloc[i, 12]) if df_excel.shape[1] > 12 and pd.notna(df_excel.iloc[i, 12]) else 0.0
            dist_val = float(df_excel.iloc[i, 13]) if df_excel.shape[1] > 13 and pd.notna(df_excel.iloc[i, 13]) else 1.0
            heat_val = float(df_excel.iloc[i, 14]) if df_excel.shape[1] > 14 and pd.notna(df_excel.iloc[i, 14]) else 50.0

            norte_GMS.append(norte)
            este_GMS.append(este)
            angulo.append(ang_val)
            distancia.append(dist_val)
            heatmap.append(heat_val)
            feature.append([norte, este])
        except Exception:
            continue

    data = pd.DataFrame(feature, columns=["Norte/Sur", "Este/Oeste"])
    print(f"\n Coordenadas Patrón Radiación ({len(feature)} puntos): \n", data)
    return data, norte_GMS, este_GMS, feature, angulo, distancia, heatmap

def save_csv(data, weights, bias, l_rate, epochs, epoch_loss, loss, average_loss):
    df = pd.DataFrame({'Weights': weights, 'Epoch': epochs})
    df["Average_loss"] = average_loss
    with pd.ExcelWriter('results.xlsx', mode='w') as writer:
        return df.to_excel(writer, sheet_name="results")
