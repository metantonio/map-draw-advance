import os
import sys
import time
import traceback
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, send_file, make_response
import pandas as pd

from functions import find_excel_file
from main import build_folium_map

app = Flask(__name__, template_folder='templates', static_folder='static')

def create_excel_template(output_path='plantilla_data.xlsx'):
    """
    Crea una plantilla vacía de Excel estructurada con las 4 pestañas requeridas.
    """
    df_loc = pd.DataFrame({
        'ID': [1],
        'DESCRIPCION': ['Ejemplo Punto 1'],
        'TIPO_ESTACION': ['BASE'],
        'PROVINCIA': ['CARACAS'],
        'MUNICIPIO': ['LIBERTADOR'],
        'PARROQUIA': ['CATEDRAL'],
        'NORTE_LATITUD': [10.488767],
        'GRADOS_N': [10],
        'MINUTOS_N': [29],
        'SEGUNDOS_N': [19.56],
        'HEMISFERIO_N': ['N'],
        'ESTE_LONGITUD': [-66.889464],
        'COLOR': ['blue'],
        'TIPO_ICONO': ['Default'],
        'RUTA_ICONO': [''],
        'SOBRENOMBRE': ['Estación Base']
    })

    df_lin = pd.DataFrame({
        'ID': [1],
        'DESCRIPCION': ['Vértice 1'],
        'TIPO_ESTACION': ['LINEA'],
        'PROVINCIA': ['CARACAS'],
        'MUNICIPIO': ['LIBERTADOR'],
        'PARROQUIA': ['CATEDRAL'],
        'NORTE_LATITUD': [10.488767],
        'GRADOS_N': [10],
        'MINUTOS_N': [29],
        'SEGUNDOS_N': [19.56],
        'HEMISFERIO_N': ['N'],
        'ESTE_LONGITUD': [-66.889464]
    })

    df_cir = pd.DataFrame({
        'ID': [1],
        'DESCRIPCION': ['Centro Círculo 1'],
        'TIPO_ESTACION': ['CIRCULO'],
        'PROVINCIA': ['CARACAS'],
        'MUNICIPIO': ['LIBERTADOR'],
        'PARROQUIA': ['CATEDRAL'],
        'NORTE_LATITUD': [10.488767],
        'GRADOS_N': [10],
        'MINUTOS_N': [29],
        'SEGUNDOS_N': [19.56],
        'HEMISFERIO_N': ['N'],
        'ESTE_LONGITUD': [-66.889464],
        'RADIO_METROS': [500.0]
    })

    df_rad = pd.DataFrame({
        'ID': [1],
        'DESCRIPCION': ['Punto Radiación 1'],
        'TIPO_ESTACION': ['RADIACION'],
        'PROVINCIA': ['CARACAS'],
        'MUNICIPIO': ['LIBERTADOR'],
        'PARROQUIA': ['CATEDRAL'],
        'NORTE_LATITUD': [10.488767],
        'GRADOS_N': [10],
        'MINUTOS_N': [29],
        'SEGUNDOS_N': [19.56],
        'HEMISFERIO_N': ['N'],
        'ESTE_LONGITUD': [-66.889464],
        'ANGULO_GIRO': [0.0],
        'DISTANCIA_KM': [2.5]
    })

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_loc.to_excel(writer, sheet_name="LOCALIZACION", index=False)
        df_lin.to_excel(writer, sheet_name="LINEA", index=False)
        df_cir.to_excel(writer, sheet_name="CIRCULO", index=False)
        df_rad.to_excel(writer, sheet_name="P_ANG_DIST", index=False)

    return output_path

def get_col_val(df, row_idx, posibles_nombres, pos_default):
    """
    Busca el valor en una fila probando primero por nombres de columna o por índice posicional.
    """
    for nombre in posibles_nombres:
        for col in df.columns:
            if str(col).strip().upper() == str(nombre).strip().upper():
                val = df.iloc[row_idx][col]
                if pd.notna(val):
                    return val

    if df.shape[1] > pos_default:
        val = df.iloc[row_idx, pos_default]
        if pd.notna(val):
            return val
    return None

def parse_excel_to_json(filepath):
    """
    Lee un archivo Excel de forma 100% robusta tolerando pestañas vacías o columnas faltantes.
    """
    result = {
        'localizacion': [],
        'linea': [],
        'circulo': [],
        'radiacion': []
    }

    if not os.path.exists(filepath):
        return result

    try:
        xl = pd.ExcelFile(filepath)
        sheet_names = [s.strip().upper() for s in xl.sheet_names]
    except Exception as e:
        print(f"[!] Error abriendo estructura Excel {filepath}: {e}")
        return result

    # 1. LOCALIZACION
    loc_sheets = [s for s in xl.sheet_names if s.strip().upper() == 'LOCALIZACION']
    if loc_sheets:
        try:
            df_loc = pd.read_excel(filepath, sheet_name=loc_sheets[0])
            if not df_loc.empty:
                for i in range(len(df_loc)):
                    try:
                        n_val = get_col_val(df_loc, i, ['NORTE_LATITUD', 'LATITUD', 'NORTE', 'LAT'], 6)
                        e_val = get_col_val(df_loc, i, ['ESTE_LONGITUD', 'LONGITUD', 'ESTE', 'LON'], 11)
                        if n_val is not None and e_val is not None:
                            n, e = float(n_val), float(e_val)
                            if (abs(n) > 0.0001 or abs(e) > 0.0001):
                                color = str(get_col_val(df_loc, i, ['COLOR'], 12) or 'blue')
                                tipo = str(get_col_val(df_loc, i, ['TIPO_ICONO', 'TIPO'], 13) or 'Default')
                                dir_icon = str(get_col_val(df_loc, i, ['RUTA_ICONO', 'DIRECCION'], 14) or '')
                                sobrenom = str(get_col_val(df_loc, i, ['SOBRENOMBRE', 'ETIQUETA'], 15) or f"Punto_{i+1}")
                                result['localizacion'].append({
                                    'norte': n, 'este': e, 'color': color, 'tipo': tipo, 'direccion': dir_icon, 'sobrenombre': sobrenom
                                })
                    except Exception:
                        continue
        except Exception as e:
            print(f"[!] Aviso al procesar hoja LOCALIZACION: {e}")

    # 2. LINEA
    lin_sheets = [s for s in xl.sheet_names if s.strip().upper() == 'LINEA']
    if lin_sheets:
        try:
            df_lin = pd.read_excel(filepath, sheet_name=lin_sheets[0])
            if not df_lin.empty:
                for i in range(len(df_lin)):
                    try:
                        n_val = get_col_val(df_lin, i, ['NORTE_LATITUD', 'LATITUD', 'NORTE', 'LAT'], 6)
                        e_val = get_col_val(df_lin, i, ['ESTE_LONGITUD', 'LONGITUD', 'ESTE', 'LON'], 11)
                        if n_val is not None and e_val is not None:
                            n, e = float(n_val), float(e_val)
                            if (abs(n) > 0.0001 or abs(e) > 0.0001):
                                result['linea'].append({'norte': n, 'este': e})
                    except Exception:
                        continue
        except Exception as e:
            print(f"[!] Aviso al procesar hoja LINEA: {e}")

    # 3. CIRCULO
    cir_sheets = [s for s in xl.sheet_names if s.strip().upper() == 'CIRCULO']
    if cir_sheets:
        try:
            df_cir = pd.read_excel(filepath, sheet_name=cir_sheets[0])
            if not df_cir.empty:
                for i in range(len(df_cir)):
                    try:
                        n_val = get_col_val(df_cir, i, ['NORTE_LATITUD', 'LATITUD', 'NORTE', 'LAT'], 6)
                        e_val = get_col_val(df_cir, i, ['ESTE_LONGITUD', 'LONGITUD', 'ESTE', 'LON'], 11)
                        if n_val is not None and e_val is not None:
                            n, e = float(n_val), float(e_val)
                            if (abs(n) > 0.0001 or abs(e) > 0.0001):
                                rad = float(get_col_val(df_cir, i, ['RADIO_METROS', 'RADIO'], 12) or 100.0)
                                result['circulo'].append({'norte': n, 'este': e, 'radio': rad})
                    except Exception:
                        continue
        except Exception as e:
            print(f"[!] Aviso al procesar hoja CIRCULO: {e}")

    # 4. P_ANG_DIST (RADIACION)
    rad_sheets = [s for s in xl.sheet_names if s.strip().upper() in ['P_ANG_DIST', 'RADIACION']]
    if rad_sheets:
        try:
            df_rad = pd.read_excel(filepath, sheet_name=rad_sheets[0])
            if not df_rad.empty:
                for i in range(len(df_rad)):
                    try:
                        n_val = get_col_val(df_rad, i, ['NORTE_LATITUD', 'LATITUD', 'NORTE', 'LAT'], 6)
                        e_val = get_col_val(df_rad, i, ['ESTE_LONGITUD', 'LONGITUD', 'ESTE', 'LON'], 11)
                        if n_val is not None and e_val is not None:
                            n, e = float(n_val), float(e_val)
                            if (abs(n) > 0.0001 or abs(e) > 0.0001):
                                ang = float(get_col_val(df_rad, i, ['ANGULO_GIRO', 'ANGULO', 'ANG'], 12) or 0.0)
                                dist = float(get_col_val(df_rad, i, ['DISTANCIA_KM', 'DISTANCIA', 'DIST'], 13) or 1.0)
                                etiq_val = get_col_val(df_rad, i, ['ETIQUETA', 'PATRON', 'NOMBRE', 'ETIQUETA_PATRON'], 14)
                                col_val = get_col_val(df_rad, i, ['COLOR', 'COLOR_PATRON'], 15)
                                item_rad = {'norte': n, 'este': e, 'angulo': ang, 'distancia': dist}
                                if etiq_val is not None and str(etiq_val).strip() != '' and str(etiq_val).lower() != 'nan':
                                    item_rad['etiqueta'] = str(etiq_val).strip()
                                if col_val is not None and str(col_val).strip() != '' and str(col_val).lower() != 'nan':
                                    item_rad['color'] = str(col_val).strip()
                                result['radiacion'].append(item_rad)
                    except Exception:
                        continue
        except Exception as e:
            print(f"[!] Aviso al procesar hoja RADIACION: {e}")

    return result

@app.route('/')
def index():
    if not os.path.exists('Mapa.html'):
        excel_file = find_excel_file()
        if excel_file:
            data = parse_excel_to_json(excel_file)
            build_folium_map(data['localizacion'], data['linea'], data['circulo'], data['radiacion'], grid_step=1.0, show_perimeter_markers=False)
        else:
            build_folium_map([], [], [], [], grid_step=1.0, show_perimeter_markers=False)
    return render_template('index.html')

@app.route('/Mapa.html')
@app.route('/api/map')
def get_map():
    map_path = os.path.abspath('Mapa.html')
    if not os.path.exists(map_path):
        excel_file = find_excel_file()
        if excel_file:
            data = parse_excel_to_json(excel_file)
            build_folium_map(data['localizacion'], data['linea'], data['circulo'], data['radiacion'], grid_step=1.0, show_perimeter_markers=False)
        else:
            build_folium_map([], [], [], [], grid_step=1.0, show_perimeter_markers=False)
    
    response = make_response(send_file(map_path))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/load-data', methods=['GET'])
def api_load_data():
    excel_file = find_excel_file()
    if excel_file:
        data = parse_excel_to_json(excel_file)
        return jsonify({'status': 'ok', 'filename': excel_file, 'data': data})
    else:
        return jsonify({'status': 'empty', 'message': 'No se encontró archivo Excel predeterminado', 'data': {
            'localizacion': [], 'linea': [], 'circulo': [], 'radiacion': []
        }})

@app.route('/api/upload-excel', methods=['POST'])
def api_upload_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No se adjuntó archivo'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'Nombre de archivo vacío'}), 400

        filename = 'data.xlsx'
        file.save(filename)
        data = parse_excel_to_json(filename)
        
        grid_step = float(request.form.get('grid_step', 1.0))
        coord_system = str(request.form.get('coord_system', 'wgs84')).lower()
        show_markers = str(request.form.get('show_perimeter_markers', 'false')).lower() == 'true'
        build_folium_map(data['localizacion'], data['linea'], data['circulo'], data['radiacion'], grid_step=grid_step, coord_system=coord_system, show_perimeter_markers=show_markers)

        return jsonify({
            'status': 'ok',
            'message': 'Archivo subido y mapa actualizado correctamente',
            'data': data,
            'map_url': f'/Mapa.html?t={int(time.time())}'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/generate-map', methods=['POST'])
def api_generate_map():
    try:
        req = request.get_json(force=True) or {}
        localizacion = req.get('localizacion', [])
        linea = req.get('linea', [])
        circulo = req.get('circulo', [])
        radiacion = req.get('radiacion', [])
        grid_step = float(req.get('grid_step', 1.0))
        coord_system = str(req.get('coord_system', 'wgs84')).lower()
        show_markers = bool(req.get('show_perimeter_markers', False))
        cajetin_info = req.get('cajetin_info', None)

        out_file = build_folium_map(
            localizacion, linea, circulo, radiacion,
            grid_step=grid_step, coord_system=coord_system, show_perimeter_markers=show_markers,
            cajetin_info=cajetin_info, output_file='Mapa.html'
        )
        return jsonify({
            'status': 'ok',
            'message': 'Mapa generado exitosamente',
            'map_url': f'/Mapa.html?t={int(time.time())}'
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/download-utm', methods=['GET'])
def api_download_utm():
    if os.path.exists('resultsUTM.xlsx'):
        return send_file(os.path.abspath('resultsUTM.xlsx'), as_attachment=True)
    return jsonify({'status': 'error', 'message': 'El archivo resultsUTM.xlsx aún no se ha generado'}), 404

@app.route('/api/download-template', methods=['GET'])
def api_download_template():
    template_path = os.path.abspath('plantilla_data.xlsx')
    if not os.path.exists(template_path):
        create_excel_template(template_path)
    return send_file(template_path, as_attachment=True, download_name='plantilla_data.xlsx')

def open_browser():
    time.sleep(1.2)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    print("=======================================================")
    print(" 🚀 INICIANDO MAP DRAW ADVANCE WEB SERVER")
    print(" Servidor ejecutandose en: http://127.0.0.1:5000")
    print("=======================================================")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
