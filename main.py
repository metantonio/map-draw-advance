import os
import sys
import math
import numpy as np
import pandas as pd
import folium
from folium import plugins
from folium.plugins import MeasureControl, MiniMap, HeatMap, Fullscreen, Draw
import itertools

from functions import excel_Localizacion, save_csv, excel_Linea, excel_Circulo, excel_PuntoDistAng
from eqa2utm import gms2utm, utm2gms
from distAndAngle import distanceAndAngle, distance2points, distanceAndAngleInterpolation, haversine_distance, rf_signal_decay, smooth_radiation_perimeter
from scaletemplate import leyenda

def formatoMouse(my_map):
    formatter = "function(num) {return L.Util.formatNum(num, 6) + ' º ';};"
    return plugins.MousePosition(
        position='topright',
        separator=' | ',
        empty_string='NaN',
        lng_first=True,
        num_digits=6,
        prefix='Coordenadas:',
        lat_formatter=formatter,
        lng_formatter=formatter,
    ).add_to(my_map)

def agregar_grilla(group, grid_step=1.0, bounds=None, coord_system='wgs84'):
    """
    Genera una grilla visible con líneas contrastadas y etiquetas de coordenadas en los bordes del plano (WGS-84 o UTM).
    """
    try:
        step = float(grid_step) if float(grid_step) > 0 else 1.0
    except (ValueError, TypeError):
        step = 1.0

    if bounds:
        min_lat = max(-89.9, bounds[0][0])
        max_lat = min(89.9, bounds[1][0])
        min_lon = max(-179.9, bounds[0][1])
        max_lon = min(179.9, bounds[1][1])
    else:
        min_lat, max_lat = -85.0, 85.0
        min_lon, max_lon = -180.0, 180.0

    system = str(coord_system).lower()

    if system == 'utm':
        # Grilla UTM
        lat_ctr = (min_lat + max_lat) / 2.0
        lon_ctr = (min_lon + max_lon) / 2.0
        n_ctr, e_ctr, huso = gms2utm(lat_ctr, lon_ctr)

        n_sw, e_sw, _ = gms2utm(min_lat, min_lon)
        n_ne, e_ne, _ = gms2utm(max_lat, max_lon)

        min_e, max_e = min(e_sw, e_ne), max(e_sw, e_ne)
        min_n, max_n = min(n_sw, n_ne), max(n_sw, n_ne)

        if step <= 0.001: step_m = 100
        elif step <= 0.005: step_m = 500
        elif step <= 0.01: step_m = 1000
        elif step <= 0.05: step_m = 5000
        elif step <= 0.1: step_m = 10000
        elif step <= 0.5: step_m = 50000
        elif step <= 1.0: step_m = 100000
        else: step_m = 500000

        start_e = math.floor(min_e / step_m) * step_m
        end_e = math.ceil(max_e / step_m) * step_m
        start_n = math.floor(min_n / step_m) * step_m
        end_n = math.ceil(max_n / step_m) * step_m

        e_steps = np.arange(start_e, end_e + step_m * 0.5, step_m)
        n_steps = np.arange(start_n, end_n + step_m * 0.5, step_m)

        max_l = 100
        if len(e_steps) > max_l: e_steps = e_steps[::int(len(e_steps)/max_l) + 1]
        if len(n_steps) > max_l: n_steps = n_steps[::int(len(n_steps)/max_l) + 1]

        # Líneas Verticales UTM (Este)
        for e_val in e_steps:
            lat1, lon1 = utm2gms(start_n, e_val, huso)
            lat2, lon2 = utm2gms(end_n, e_val, huso)

            folium.PolyLine(
                [[lat1, lon1], [lat2, lon2]],
                weight=1.5,
                color="#059669",
                opacity=0.6,
                dash_array="4, 4",
                tooltip=f"UTM Este: {e_val:,.0f} m (Huso {huso})"
            ).add_to(group)

            # Etiqueta en Borde Superior
            folium.Marker(
                [lat2, lon2],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-top">E: {e_val:,.0f} m</div>'
                )
            ).add_to(group)

            # Etiqueta en Borde Inferior
            folium.Marker(
                [lat1, lon1],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-bottom">E: {e_val:,.0f} m</div>'
                )
            ).add_to(group)

        # Líneas Horizontales UTM (Norte)
        for n_val in n_steps:
            lat1, lon1 = utm2gms(n_val, start_e, huso)
            lat2, lon2 = utm2gms(n_val, end_e, huso)

            folium.PolyLine(
                [[lat1, lon1], [lat2, lon2]],
                weight=1.5,
                color="#059669",
                opacity=0.6,
                dash_array="4, 4",
                tooltip=f"UTM Norte: {n_val:,.0f} m (Huso {huso})"
            ).add_to(group)

            # Etiqueta en Borde Izquierdo
            folium.Marker(
                [lat1, lon1],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-left">N: {n_val:,.0f} m</div>'
                )
            ).add_to(group)

            # Etiqueta en Borde Derecho
            folium.Marker(
                [lat2, lon2],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-right">N: {n_val:,.0f} m</div>'
                )
            ).add_to(group)

    else:
        # Grilla WGS-84
        start_lat = math.floor(min_lat / step) * step
        end_lat = math.ceil(max_lat / step) * step
        start_lon = math.floor(min_lon / step) * step
        end_lon = math.ceil(max_lon / step) * step

        lat_steps = np.arange(start_lat, end_lat + step * 0.5, step)
        lon_steps = np.arange(start_lon, end_lon + step * 0.5, step)

        max_lines = 100
        if len(lat_steps) > max_lines: lat_steps = lat_steps[::int(len(lat_steps)/max_lines) + 1]
        if len(lon_steps) > max_lines: lon_steps = lon_steps[::int(len(lon_steps)/max_lines) + 1]

        # Líneas de Latitud (Horizontales)
        for lat in lat_steps:
            lat_val = round(float(lat), 6)
            folium.PolyLine(
                [[lat_val, start_lon], [lat_val, end_lon]],
                weight=1.5,
                color="#2563eb",
                opacity=0.6,
                dash_array="4, 4",
                tooltip=f"Latitud: {lat_val:.4f}º"
            ).add_to(group)

            hemi_n = 'N' if lat_val >= 0 else 'S'
            lbl_lat = f"{abs(lat_val):.4f}º {hemi_n}"

            # Etiqueta Borde Izquierdo
            folium.Marker(
                [lat_val, start_lon],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-left">{lbl_lat}</div>'
                )
            ).add_to(group)

            # Etiqueta Borde Derecho
            folium.Marker(
                [lat_val, end_lon],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-right">{lbl_lat}</div>'
                )
            ).add_to(group)

        # Líneas de Longitud (Verticales)
        for lon in lon_steps:
            lon_val = round(float(lon), 6)
            folium.PolyLine(
                [[start_lat, lon_val], [end_lat, lon_val]],
                weight=1.5,
                color="#2563eb",
                opacity=0.6,
                dash_array="4, 4",
                tooltip=f"Longitud: {lon_val:.4f}º"
            ).add_to(group)

            hemi_e = 'E' if lon_val >= 0 else 'W'
            lbl_lon = f"{abs(lon_val):.4f}º {hemi_e}"

            # Etiqueta Borde Superior
            folium.Marker(
                [end_lat, lon_val],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-top">{lbl_lon}</div>'
                )
            ).add_to(group)

            # Etiqueta Borde Inferior
            folium.Marker(
                [start_lat, lon_val],
                icon=folium.DivIcon(
                    class_name="grid-edge-marker",
                    icon_size=None,
                    html=f'<div class="grid-edge-label grid-edge-bottom">{lbl_lon}</div>'
                )
            ).add_to(group)

def build_folium_map(data_localizacion, data_linea, data_circulo, data_radiacion, grid_step=1.0, coord_system='wgs84', show_perimeter_markers=False, cajetin_info=None, output_file='Mapa.html'):
    """
    Construye y guarda el mapa Folium con marcadores de perímetro opcionales, etiquetas visibles bajo marcadores y datos del Cajetín de Plano.
    """
    all_coords = []
    default_location = [10.4806, -66.9036]

    # Extraer arrays de datos
    norte_GMS = [row['norte'] for row in data_localizacion]
    este_GMS = [row['este'] for row in data_localizacion]
    coordenadas = [[row['norte'], row['este']] for row in data_localizacion]
    colorM = [row.get('color', 'blue') for row in data_localizacion]
    tipoIcon = [row.get('tipo', 'Default') for row in data_localizacion]
    direccion = [row.get('direccion', '') for row in data_localizacion]
    sobrenombre = [row.get('sobrenombre', f'Punto_{i+1}') for i, row in enumerate(data_localizacion)]

    norte_GMSL = [row['norte'] for row in data_linea]
    este_GMSL = [row['este'] for row in data_linea]
    coordenadasL = [[row['norte'], row['este']] for row in data_linea]

    norte_GMSC = [row['norte'] for row in data_circulo]
    este_GMSC = [row['este'] for row in data_circulo]
    coordenadasC = [[row['norte'], row['este']] for row in data_circulo]
    radio = [row.get('radio', 100.0) for row in data_circulo]

    norte_GMSP = [row['norte'] for row in data_radiacion]
    este_GMSP = [row['este'] for row in data_radiacion]
    anguloP = [row.get('angulo', 0.0) for row in data_radiacion]
    distanciaP = [row.get('distancia', 1.0) for row in data_radiacion]

    # Transformación a UTM
    df_loc, df_lin, df_cir, df_rad_g, df_rad_utm = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    puntos_cajetin = []
    if norte_GMS:
        n_utm, e_utm, h_utm = zip(*[gms2utm(n, e) for n, e in zip(norte_GMS, este_GMS)])
        df_loc = pd.DataFrame({'Norte': n_utm, 'Este': e_utm, 'Huso': h_utm})

        for i in range(len(norte_GMS)):
            if abs(norte_GMS[i]) > 0.0001 and abs(este_GMS[i]) > 0.0001:
                puntos_cajetin.append({
                    'nombre': sobrenombre[i] if i < len(sobrenombre) else f"Punto_{i+1}",
                    'wgs84': f"{norte_GMS[i]:.5f}º, {este_GMS[i]:.5f}º",
                    'utm': f"{n_utm[i]:.0f} N, {e_utm[i]:.0f} E ({h_utm[i]})"
                })

    if norte_GMSL:
        n_utm, e_utm, h_utm = zip(*[gms2utm(n, e) for n, e in zip(norte_GMSL, este_GMSL)])
        df_lin = pd.DataFrame({'Norte': n_utm, 'Este': e_utm, 'Huso': h_utm})

    if norte_GMSC:
        n_utm, e_utm, h_utm = zip(*[gms2utm(n, e) for n, e in zip(norte_GMSC, este_GMSC)])
        df_cir = pd.DataFrame({'Norte': n_utm, 'Este': e_utm, 'Huso': h_utm})

    norte_GMSP2, este_GMSP2, dataHeatMap = [], [], []
    if norte_GMSP:
        norte_GMSP2 = [0]*len(norte_GMSP)
        este_GMSP2 = [0]*len(este_GMSP)
        for i in range(len(norte_GMSP)):
            norte_GMSP2[i], este_GMSP2[i] = distanceAndAngle(norte_GMSP[i], este_GMSP[i], anguloP[i], distanciaP[i])
            
            # Centro transmisor a 100% (1.0)
            dataHeatMap.append([norte_GMSP[i], este_GMSP[i], 1.0])

            # Interpolación concéntrica de decaimiento RF
            auxlist = distanceAndAngleInterpolation(norte_GMSP[i], este_GMSP[i], anguloP[i], distanciaP[i])
            for pt in auxlist:
                dataHeatMap.append([pt[0], pt[1], pt[2]])

        df_rad_g = pd.DataFrame({'Norte Latitud(deg)': norte_GMSP2, 'Este Longitud(deg)': este_GMSP2, 'Angulo (deg)': anguloP, 'Distancia (km)': distanciaP})
        n_utm, e_utm, h_utm = zip(*[gms2utm(n, e) for n, e in zip(norte_GMSP2, este_GMSP2)])
        df_rad_utm = pd.DataFrame({'Norte': n_utm, 'Este': e_utm, 'Huso': h_utm, 'Angulo (deg)': anguloP, 'Distancia (km)': distanciaP})

    # Exportar Excel UTM
    try:
        with pd.ExcelWriter('resultsUTM.xlsx', mode='w', engine='openpyxl') as writer:
            if not df_loc.empty: df_loc.to_excel(writer, sheet_name="LOCALIZACION")
            if not df_lin.empty: df_lin.to_excel(writer, sheet_name="LINEA")
            if not df_cir.empty: df_cir.to_excel(writer, sheet_name="CIRCULO")
            if not df_rad_g.empty: df_rad_g.to_excel(writer, sheet_name="P_DIST_ANG_G")
            if not df_rad_utm.empty: df_rad_utm.to_excel(writer, sheet_name="P_DIST_ANG_UTM")
    except Exception as e:
        print(f"[!] No se pudo guardar resultsUTM.xlsx: {e}")

    # Filtrar coordenadas válidas
    valid_initial = [c for c in coordenadas if abs(c[0]) > 0.0001 and abs(c[1]) > 0.0001]
    if not valid_initial:
        valid_initial = [c for c in coordenadasL if abs(c[0]) > 0.0001 and abs(c[1]) > 0.0001]
    
    initial_center = valid_initial[0] if valid_initial else default_location

    # Inicializar Folium Map con tiles=None para evitar capas duplicadas
    myMap = folium.Map(location=initial_center, zoom_start=12, control_scale=True, tiles=None)

    # Añadir Capas Base Estándar
    folium.TileLayer('openstreetmap', name='OpenStreetMap (Estándar)').add_to(myMap)
    folium.TileLayer('cartodbpositron', name='CartoDB Positron (Modo Claro)').add_to(myMap)
    folium.TileLayer('cartodbdarkmatter', name='CartoDB Dark Matter (Modo Oscuro)').add_to(myMap)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Esri Satellite HD',
        overlay=False,
        control=True
    ).add_to(myMap)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Topo Map',
        name='Esri Topográfico',
        overlay=False,
        control=True
    ).add_to(myMap)

    folium.raster_layers.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Maps",
        name="Google Satellite",
        max_zoom=20,
        overlay=False,
        control=True,
    ).add_to(myMap)

    folium.raster_layers.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps",
        name="Google Maps (Calles)",
        max_zoom=20,
        overlay=False,
        control=True,
    ).add_to(myMap)

    # GRUPOS DE CAPAS DE ELEMENTOS
    fg_localizacion = folium.FeatureGroup(name="📍 Puntos de Localización")
    fg_lineas = folium.FeatureGroup(name="📏 Polilíneas")
    fg_circulos = folium.FeatureGroup(name="⭕ Círculos")
    fg_perimetro = folium.FeatureGroup(name="🚩 Perímetro RF (Curva Suave)", show=True)
    fg_perimetro_marcadores = folium.FeatureGroup(name="📌 Vértices Perímetro RF (Marcadores)", show=show_perimeter_markers)
    fg_heatmap = folium.FeatureGroup(name="🔥 Patrón de Radiación (Heatmap RF)")
    grid_sys_lbl = "UTM (m)" if coord_system.lower() == "utm" else "WGS-84 (º)"
    fg_grilla = folium.FeatureGroup(name=f"🌐 Grilla {grid_sys_lbl}", show=True)

    # 1. Puntos Localización (CON ETIQUETAS PERMANENTES VISIBLES DEBAJO DEL MARCADOR)
    if coordenadas:
        for i in range(len(coordenadas)):
            if abs(coordenadas[i][0]) > 0.0001 and abs(coordenadas[i][1]) > 0.0001:
                all_coords.append(coordenadas[i])
                icon_color = colorM[i] if i < len(colorM) and str(colorM[i]) != 'nan' and colorM[i] in ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'] else 'blue'
                tipo = tipoIcon[i] if i < len(tipoIcon) else 'Default'
                dir_icon = direccion[i] if i < len(direccion) else ''
                nombre = sobrenombre[i] if i < len(sobrenombre) else f"Punto_{i+1}"

                if tipo != "Default" and dir_icon and os.path.exists(dir_icon):
                    icon_obj = folium.features.CustomIcon(dir_icon, icon_size=(40, 40))
                else:
                    icon_obj = folium.Icon(color=icon_color, icon='info-sign')

                popup_html = f"""
                <div style="font-family: sans-serif; min-width: 180px;">
                    <h4 style="margin: 0 0 8px 0; color: #2c3e50;">📍 {nombre}</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <tr><td><b>Latitud:</b></td><td>{coordenadas[i][0]:.6f} º</td></tr>
                        <tr><td><b>Longitud:</b></td><td>{coordenadas[i][1]:.6f} º</td></tr>
                        <tr><td><b>Índice:</b></td><td>#{i+1}</td></tr>
                    </table>
                </div>
                """

                # Tooltip permanente posicionado debajo del marcador
                perm_tooltip = folium.Tooltip(
                    text=f"<b>{nombre}</b>",
                    permanent=True,
                    direction="bottom",
                    offset=[0, 10],
                    style="background-color: rgba(255, 255, 255, 0.92); border: 1px solid #1e293b; border-radius: 4px; color: #0f172a; font-weight: bold; font-size: 11px; padding: 2px 6px; box-shadow: 0 2px 6px rgba(0,0,0,0.25);"
                )

                folium.Marker(
                    coordenadas[i],
                    icon=icon_obj,
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=perm_tooltip
                ).add_to(fg_localizacion)

    # 2. Marcadores del perímetro de radiación (Capa Independiente Opcional)
    if norte_GMSP2:
        for i in range(len(norte_GMSP2)):
            coord = [norte_GMSP2[i], este_GMSP2[i]]
            if abs(coord[0]) > 0.0001 and abs(coord[1]) > 0.0001:
                all_coords.append(coord)
                folium.Marker(
                    coord,
                    icon=folium.Icon(color='red', icon='crosshairs', prefix='fa'),
                    popup=f"Vértice Radiación #{i+1}<br>N: {coord[0]:.6f}º<br>E: {coord[1]:.6f}º<br>Atenuación RF: 0%",
                    tooltip=f"Perímetro RF #{i+1}"
                ).add_to(fg_perimetro_marcadores)

    # 3. Polilíneas
    valid_L = [c for c in coordenadasL if abs(c[0]) > 0.0001 and abs(c[1]) > 0.0001]
    if valid_L:
        for c in valid_L: all_coords.append(c)
        dist_linea = []
        for i in range(len(valid_L) - 1):
            d_km = haversine_distance(valid_L[i], valid_L[i+1])
            dist_linea.append(round(d_km, 3))

        folium.PolyLine(
            valid_L,
            color="#e74c3c",
            weight=3.5,
            opacity=0.9,
            popup=f"<b>Polilínea Principal</b><br>Tramos (km): {dist_linea}<br>Total: {sum(dist_linea):.2f} km",
            tooltip="Línea trazada"
        ).add_to(fg_lineas)

    # 4. Perímetro de Radiación con CURVAS SUAVES
    if norte_GMSP:
        lat_c, lon_c = norte_GMSP[0], este_GMSP[0]
        if abs(lat_c) > 0.0001 and abs(lon_c) > 0.0001:
            smooth_coords = smooth_radiation_perimeter(lat_c, lon_c, anguloP, distanciaP)
            for sc in smooth_coords:
                all_coords.append(sc)

            folium.PolyLine(
                smooth_coords,
                color="#8e44ad",
                weight=3.5,
                opacity=0.95,
                smooth_factor=1.0,
                popup="<b>Perímetro de Radiación RF (Curva Suave)</b><br>Contorno de Cobertura Radioeléctrica",
                tooltip="Perímetro RF (Curva Suave)"
            ).add_to(fg_perimetro)

    # 5. Círculos
    if coordenadasC:
        for i in range(len(coordenadasC)):
            if abs(coordenadasC[i][0]) > 0.0001 and abs(coordenadasC[i][1]) > 0.0001:
                all_coords.append(coordenadasC[i])
                rad = radio[i] if i < len(radio) else 100
                folium.Circle(
                    coordenadasC[i],
                    radius=rad,
                    popup=f"<b>Círculo #{i+1}</b><br>Centro: {coordenadasC[i]}<br>Radio: {rad} m",
                    color='#3498db',
                    fill_color='#3498db',
                    fill=True,
                    fill_opacity=0.3
                ).add_to(fg_circulos)

    # 6. Heatmap de Señal de Radio Fluid & Continuous
    if dataHeatMap:
        HeatMap(
            dataHeatMap,
            name="Mapa de Calor RF",
            min_opacity=0.3,
            radius=30,
            blur=20,
            max_zoom=18,
            gradient={0.0: '#ffcdfd', 0.25: '#819fdd', 0.5: '#00af50', 0.75: '#ffff00', 1.0: '#ff0000'}
        ).add_to(fg_heatmap)

    leyenda(myMap, cajetin_info=cajetin_info, puntos_cajetin=puntos_cajetin)

    # Determinar Encuadre / Bounds SOLO con coordenadas geográficas válidas
    bounds = None
    valid_coords = [c for c in all_coords if abs(c[0]) > 0.0001 and abs(c[1]) > 0.0001]
    if valid_coords:
        lats = [c[0] for c in valid_coords]
        lons = [c[1] for c in valid_coords]
        south_west = [min(lats), min(lons)]
        north_east = [max(lats), max(lons)]
        if south_west == north_east:
            south_west = [south_west[0] - 0.01, south_west[1] - 0.01]
            north_east = [north_east[0] + 0.01, north_east[1] + 0.01]
        bounds = [south_west, north_east]
        myMap.fit_bounds(bounds)

    # Generar Grilla Dinámica con contraste mejorado y etiquetas de borde
    agregar_grilla(fg_grilla, grid_step=grid_step, bounds=bounds, coord_system=coord_system)

    # Añadir FeatureGroups al mapa
    fg_localizacion.add_to(myMap)
    fg_lineas.add_to(myMap)
    fg_circulos.add_to(myMap)
    fg_perimetro.add_to(myMap)
    fg_perimetro_marcadores.add_to(myMap)
    fg_heatmap.add_to(myMap)
    fg_grilla.add_to(myMap)

    # Controles Interactivos
    folium.LayerControl(collapsed=False).add_to(myMap)
    formatoMouse(myMap)
    myMap.add_child(MeasureControl(position='bottomleft'))
    myMap.add_child(MiniMap(toggle_display=True, position='bottomleft'))
    Draw(export=True, filename='mis_dibujos.geojson', position='topleft').add_to(myMap)

    # Inyectar Script para Forzar Invalidador de Tamaño de Mapa Leaflet y Grilla Dinámica Adaptativa al Zoom y PDF
    grid_js = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/proj4js/2.9.0/proj4.js"></script>
    <script>
    window.MAP_COORD_SYSTEM = "{coord_system}";

    function latLonToUtmJS(lat, lon) {{
        var clampedLon = Math.max(-179.99999, Math.min(179.99999, lon));
        var clampedLat = Math.max(-80.0, Math.min(84.0, lat));
        var zone = Math.floor((clampedLon + 180) / 6) + 1;
        zone = Math.max(1, Math.min(60, zone));
        var south = clampedLat < 0;
        try {{
            var projStr = "+proj=utm +zone=" + zone + (south ? " +south" : "") + " +datum=WGS84 +units=m +no_defs";
            var res = proj4("EPSG:4326", projStr, [clampedLon, clampedLat]);
            return {{ easting: res[0], northing: res[1], zone: zone + (south ? "S" : "N") }};
        }} catch(e) {{
            return {{ easting: 0, northing: 0, zone: zone }};
        }}
    }}

    function utmToLatLonJS(easting, northing, zoneStr) {{
        var zoneNum = parseInt(zoneStr);
        var south = (zoneStr + "").indexOf("S") !== -1;
        try {{
            var projStr = "+proj=utm +zone=" + zoneNum + (south ? " +south" : "") + " +datum=WGS84 +units=m +no_defs";
            var res = proj4(projStr, "EPSG:4326", [easting, northing]);
            return {{ lat: res[1], lon: res[0] }};
        }} catch(e) {{
            return {{ lat: 0, lon: 0 }};
        }}
    }}

    var dynamicGridLayerGroup = null;

    function fixLeafletMapSize() {{
        for (var key in window) {{
            try {{
                if (window[key] && window[key] instanceof L.Map) {{
                    window[key].invalidateSize();
                }}
            }} catch(e) {{}}
        }}
        updateGridEdgeBounds();
    }}

    function updateGridEdgeBounds() {{
        var mapObj = null;
        for (var key in window) {{
            try {{
                if (window[key] && window[key] instanceof L.Map) {{
                    mapObj = window[key];
                    break;
                }}
            }} catch(e) {{}}
        }}
        if (!mapObj) return;

        if (!dynamicGridLayerGroup) {{
            dynamicGridLayerGroup = L.layerGroup().addTo(mapObj);
        }} else {{
            dynamicGridLayerGroup.clearLayers();
        }}

        var bounds = mapObj.getBounds();
        var south = bounds.getSouth();
        var north = bounds.getNorth();
        var west = bounds.getWest();
        var east = bounds.getEast();
        var zoom = mapObj.getZoom();

        var sz = mapObj.getSize();
        var pad = 14;
        var topLat = mapObj.containerPointToLatLng([sz.x / 2, pad]).lat;
        var botLat = mapObj.containerPointToLatLng([sz.x / 2, sz.y - pad]).lat;
        var lftLon = mapObj.containerPointToLatLng([pad, sz.y / 2]).lng;
        var rgtLon = mapObj.containerPointToLatLng([sz.x - pad, sz.y / 2]).lng;

        var system = (window.MAP_COORD_SYSTEM || "wgs84").toLowerCase();

        if (system === "utm") {{
            var swUtm = latLonToUtmJS(south, west);
            var neUtm = latLonToUtmJS(north, east);
            var zoneStr = swUtm.zone;

            var eMin = Math.min(swUtm.easting, neUtm.easting);
            var eMax = Math.max(swUtm.easting, neUtm.easting);
            var nMin = Math.min(swUtm.northing, neUtm.northing);
            var nMax = Math.max(swUtm.northing, neUtm.northing);

            var stepM = 100000;
            if (zoom >= 17) stepM = 100;
            else if (zoom >= 15) stepM = 500;
            else if (zoom >= 13) stepM = 1000;
            else if (zoom >= 11) stepM = 5000;
            else if (zoom >= 9) stepM = 10000;
            else if (zoom >= 7) stepM = 50000;

            var startE = Math.floor(eMin / stepM) * stepM;
            var endE = Math.ceil(eMax / stepM) * stepM;
            var startN = Math.floor(nMin / stepM) * stepM;
            var endN = Math.ceil(nMax / stepM) * stepM;

            var maxLines = 30;
            var eCount = Math.floor((endE - startE) / stepM);
            if (eCount > maxLines) stepM *= Math.ceil(eCount / maxLines);

            // Líneas Verticales UTM (Este)
            for (var eVal = startE; eVal <= endE; eVal += stepM) {{
                var ptBot = utmToLatLonJS(eVal, nMin, zoneStr);
                var ptTop = utmToLatLonJS(eVal, nMax, zoneStr);

                L.polyline([[ptBot.lat, ptBot.lon], [ptTop.lat, ptTop.lon]], {{
                    color: "#059669", weight: 1.5, opacity: 0.6, dashArray: "4, 4"
                }}).addTo(dynamicGridLayerGroup);

                var eLbl = "E: " + Math.round(eVal).toLocaleString() + " m";

                // Borde Superior (Interno)
                L.marker([topLat, ptTop.lon], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-top">' + eLbl + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);

                // Borde Inferior (Interno)
                L.marker([botLat, ptBot.lon], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-bottom">' + eLbl + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);
            }}

            // Líneas Horizontales UTM (Norte)
            for (var nVal = startN; nVal <= endN; nVal += stepM) {{
                var ptLft = utmToLatLonJS(eMin, nVal, zoneStr);
                var ptRgt = utmToLatLonJS(eMax, nVal, zoneStr);

                L.polyline([[ptLft.lat, ptLft.lon], [ptRgt.lat, ptRgt.lon]], {{
                    color: "#059669", weight: 1.5, opacity: 0.6, dashArray: "4, 4"
                }}).addTo(dynamicGridLayerGroup);

                var nLbl = "N: " + Math.round(nVal).toLocaleString() + " m";

                // Borde Izquierdo (Interno)
                L.marker([ptLft.lat, lftLon], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-left">' + nLbl + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);

                // Borde Derecho (Interno)
                L.marker([ptRgt.lat, rgtLon], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-right">' + nLbl + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);
            }}

        }} else {{
            // Sistema WGS-84
            var stepDeg = 1.0;
            if (zoom >= 16) stepDeg = 0.001;
            else if (zoom >= 14) stepDeg = 0.005;
            else if (zoom >= 12) stepDeg = 0.01;
            else if (zoom >= 10) stepDeg = 0.05;
            else if (zoom >= 8) stepDeg = 0.1;
            else if (zoom >= 6) stepDeg = 0.5;

            var startLat = Math.floor(south / stepDeg) * stepDeg;
            var endLat = Math.ceil(north / stepDeg) * stepDeg;
            var startLon = Math.floor(west / stepDeg) * stepDeg;
            var endLon = Math.ceil(east / stepDeg) * stepDeg;

            var maxLines = 30;
            var latCount = Math.floor((endLat - startLat) / stepDeg);
            if (latCount > maxLines) stepDeg *= Math.ceil(latCount / maxLines);

            // Líneas de Latitud (Horizontales)
            for (var lat = startLat; lat <= endLat; lat += stepDeg) {{
                var latVal = parseFloat(lat.toFixed(6));
                L.polyline([[latVal, west], [latVal, east]], {{
                    color: "#2563eb", weight: 1.5, opacity: 0.6, dashArray: "4, 4"
                }}).addTo(dynamicGridLayerGroup);

                var hemiN = latVal >= 0 ? "N" : "S";
                var lblLat = Math.abs(latVal).toFixed(4) + "º " + hemiN;

                // Borde Izquierdo (Interno)
                L.marker([latVal, lftLon], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-left">' + lblLat + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);

                // Borde Derecho (Interno)
                L.marker([latVal, rgtLon], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-right">' + lblLat + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);
            }}

            // Líneas de Longitud (Verticales)
            for (var lon = startLon; lon <= endLon; lon += stepDeg) {{
                var lonVal = parseFloat(lon.toFixed(6));
                L.polyline([[south, lonVal], [north, lonVal]], {{
                    color: "#2563eb", weight: 1.5, opacity: 0.6, dashArray: "4, 4"
                }}).addTo(dynamicGridLayerGroup);

                var hemiE = lonVal >= 0 ? "E" : "W";
                var lblLon = Math.abs(lonVal).toFixed(4) + "º " + hemiE;

                // Borde Superior (Interno)
                L.marker([topLat, lonVal], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-top">' + lblLon + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);

                // Borde Inferior (Interno)
                L.marker([botLat, lonVal], {{
                    icon: L.divIcon({{
                        className: "grid-edge-marker",
                        iconSize: null,
                        html: '<div class="grid-edge-label grid-edge-bottom">' + lblLon + '</div>'
                    }})
                }}).addTo(dynamicGridLayerGroup);
            }}
        }}
    }}

    function initDynamicGridListener() {{
        for (var key in window) {{
            try {{
                if (window[key] && window[key] instanceof L.Map) {{
                    var map = window[key];
                    map.off('moveend zoomend resize', updateGridEdgeBounds);
                    map.on('moveend zoomend resize', updateGridEdgeBounds);
                    updateGridEdgeBounds();
                    break;
                }}
            }} catch(e) {{}}
        }}
    }}

    window.addEventListener('load', function() {{
        setTimeout(initDynamicGridListener, 100);
        setTimeout(initDynamicGridListener, 400);
        setTimeout(initDynamicGridListener, 1000);
    }});

    window.addEventListener('resize', fixLeafletMapSize);
    window.addEventListener('beforeprint', fixLeafletMapSize);
    </script>
    """
    myMap.get_root().html.add_child(folium.Element(grid_js))

    # Guardar mapa en ruta absoluta
    abs_output = os.path.abspath(output_file)
    myMap.save(abs_output)
    print(f" [OK] Mapa generado exitosamente en: {abs_output} (Grilla: {grid_step}º)")
    return abs_output

def menuPpal(user):
    data, norte_GMS, este_GMS, coordenadas, colorM, tipoIcon, direccion, sobrenombre = excel_Localizacion()
    dataL, norte_GMSL, este_GMSL, coordenadasL = excel_Linea()
    dataC, norte_GMSC, este_GMSC, coordenadasC, radio = excel_Circulo()
    dataP, norte_GMSP, este_GMSP, coordenadasP, anguloP, distanciaP, heatmapP = excel_PuntoDistAng()

    loc_list = [{'norte': norte_GMS[i], 'este': este_GMS[i], 'color': colorM[i], 'tipo': tipoIcon[i], 'direccion': direccion[i], 'sobrenombre': sobrenombre[i]} for i in range(len(norte_GMS))]
    lin_list = [{'norte': norte_GMSL[i], 'este': este_GMSL[i]} for i in range(len(norte_GMSL))]
    cir_list = [{'norte': norte_GMSC[i], 'este': este_GMSC[i], 'radio': radio[i]} for i in range(len(norte_GMSC))]
    rad_list = [{'norte': norte_GMSP[i], 'este': este_GMSP[i], 'angulo': anguloP[i], 'distancia': distanciaP[i]} for i in range(len(norte_GMSP))]

    grid_step = 1.0
    try:
        g_in = input(" Ingrese paso de la grilla en grados [ej: 0.01, 0.1, 1.0] (def 1.0): ").strip()
        if g_in: grid_step = float(g_in)
    except Exception:
        pass

    build_folium_map(loc_list, lin_list, cir_list, rad_list, grid_step=grid_step, output_file='Mapa.html')
    return folium.Map()

if __name__ == '__main__':
    menuPpal(4)
