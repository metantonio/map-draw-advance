import os
import sys
import time
import webbrowser
import threading
from flask import Flask, render_template, request, jsonify, send_file, make_response
import pandas as pd

from functions import find_excel_file, excel_Localizacion, excel_Linea, excel_Circulo, excel_PuntoDistAng
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

def parse_excel_to_json(filepath):
    result = {
        'localizacion': [],
        'linea': [],
        'circulo': [],
        'radiacion': []
    }

    if not os.path.exists(filepath):
        return result

    # 1. LOCALIZACION
    try:
        df_loc = pd.read_excel(filepath, sheet_name="LOCALIZACION")
        for i in range(len(df_loc)):
            try:
                n = float(df_loc.iloc[i, 6])
                e = float(df_loc.iloc[i, 11])
                if pd.notna(n) and pd.notna(e) and (abs(n) > 0.0001 or abs(e) > 0.0001):
                    color = str(df_loc.iloc[i, 12]) if df_loc.shape[1] > 12 and pd.notna(df_loc.iloc[i, 12]) else 'blue'
                    tipo = str(df_loc.iloc[i, 13]) if df_loc.shape[1] > 13 and pd.notna(df_loc.iloc[i, 13]) else 'Default'
                    dir_icon = str(df_loc.iloc[i, 14]) if df_loc.shape[1] > 14 and pd.notna(df_loc.iloc[i, 14]) else ''
                    sobrenom = str(df_loc.iloc[i, 15]) if df_loc.shape[1] > 15 and pd.notna(df_loc.iloc[i, 15]) else f"Punto_{i+1}"
                    result['localizacion'].append({
                        'norte': n, 'este': e, 'color': color, 'tipo': tipo, 'direccion': dir_icon, 'sobrenombre': sobrenom
                    })
            except Exception:
                continue
    except Exception:
        pass

    # 2. LINEA
    try:
        df_lin = pd.read_excel(filepath, sheet_name="LINEA")
        for i in range(len(df_lin)):
            try:
                n = float(df_lin.iloc[i, 6])
                e = float(df_lin.iloc[i, 11])
                if pd.notna(n) and pd.notna(e) and (abs(n) > 0.0001 or abs(e) > 0.0001):
                    result['linea'].append({'norte': n, 'este': e})
            except Exception:
                continue
    except Exception:
        pass

    # 3. CIRCULO
    try:
        df_cir = pd.read_excel(filepath, sheet_name="CIRCULO")
        for i in range(len(df_cir)):
            try:
                n = float(df_cir.iloc[i, 6])
                e = float(df_cir.iloc[i, 11])
                if pd.notna(n) and pd.notna(e) and (abs(n) > 0.0001 or abs(e) > 0.0001):
                    rad = float(df_cir.iloc[i, 12]) if df_cir.shape[1] > 12 and pd.notna(df_cir.iloc[i, 12]) else 100.0
                    result['circulo'].append({'norte': n, 'este': e, 'radio': rad})
            except Exception:
                continue
    except Exception:
        pass

    # 4. P_ANG_DIST (RADIACION)
    try:
        df_rad = pd.read_excel(filepath, sheet_name="P_ANG_DIST")
        for i in range(len(df_rad)):
            try:
                n = float(df_rad.iloc[i, 6])
                e = float(df_rad.iloc[i, 11])
                if pd.notna(n) and pd.notna(e) and (abs(n) > 0.0001 or abs(e) > 0.0001):
                    ang = float(df_rad.iloc[i, 12]) if df_rad.shape[1] > 12 and pd.notna(df_rad.iloc[i, 12]) else 0.0
                    dist = float(df_rad.iloc[i, 13]) if df_rad.shape[1] > 13 and pd.notna(df_rad.iloc[i, 13]) else 1.0
                    result['radiacion'].append({'norte': n, 'este': e, 'angulo': ang, 'distancia': dist})
            except Exception:
                continue
    except Exception:
        pass

    return result

@app.route('/')
def index():
    if not os.path.exists('Mapa.html'):
        excel_file = find_excel_file()
        if excel_file:
            data = parse_excel_to_json(excel_file)
            build_folium_map(data['localizacion'], data['linea'], data['circulo'], data['radiacion'], grid_step=1.0)
        else:
            build_folium_map([], [], [], [], grid_step=1.0)
    return render_template('index.html')

@app.route('/Mapa.html')
@app.route('/api/map')
def get_map():
    map_path = os.path.abspath('Mapa.html')
    if not os.path.exists(map_path):
        excel_file = find_excel_file()
        if excel_file:
            data = parse_excel_to_json(excel_file)
            build_folium_map(data['localizacion'], data['linea'], data['circulo'], data['radiacion'], grid_step=1.0)
        else:
            build_folium_map([], [], [], [], grid_step=1.0)
    
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
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No se adjuntó archivo'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'Nombre de archivo vacío'}), 400

    filename = 'data.xlsx'
    file.save(filename)
    data = parse_excel_to_json(filename)
    
    build_folium_map(data['localizacion'], data['linea'], data['circulo'], data['radiacion'], grid_step=1.0)

    return jsonify({
        'status': 'ok',
        'message': 'Archivo subido y mapa actualizado correctamente',
        'data': data,
        'map_url': f'/Mapa.html?t={int(time.time())}'
    })

@app.route('/api/generate-map', methods=['POST'])
def api_generate_map():
    req = request.get_json(force=True)
    localizacion = req.get('localizacion', [])
    linea = req.get('linea', [])
    circulo = req.get('circulo', [])
    radiacion = req.get('radiacion', [])
    grid_step = float(req.get('grid_step', 1.0))

    out_file = build_folium_map(localizacion, linea, circulo, radiacion, grid_step=grid_step, output_file='Mapa.html')
    return jsonify({
        'status': 'ok',
        'message': 'Mapa generado exitosamente',
        'map_url': f'/Mapa.html?t={int(time.time())}'
    })

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
