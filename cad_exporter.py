"""
cad_exporter.py - Módulo de Exportación a AutoCAD y Open CAD (DXF & COM)
Permite exportar capas geoespaciales (Puntos, Polilíneas, Círculos, Radiales)
a formato universal DXF compatible con AutoCAD, LibreCAD, QCAD, FreeCAD,
y enviar directamente a una instancia activa de AutoCAD en Windows vía COM.
"""

import os
import math
import ezdxf
from ezdxf import colors
from eqa2utm import gms2utm

# Mapeo de colores web a colores ACI (AutoCAD Color Index)
COLOR_MAP_ACI = {
    'red': 1,
    'yellow': 2,
    'green': 3,
    'cyan': 4,
    'blue': 5,
    'magenta': 6,
    'white': 7,
    'gray': 8,
    'grey': 8,
    'orange': 30,
    'purple': 210,
    'pink': 221,
    'black': 7
}

def get_aci_color(color_name):
    """Retorna el código de color ACI para AutoCAD / DXF."""
    if not color_name:
        return 7
    c = str(color_name).strip().lower()
    return COLOR_MAP_ACI.get(c, 7)

def export_to_dxf(localizacion, linea, circulo, radiacion, coord_system='utm', output_path='mapa_export.dxf'):
    """
    Genera un archivo DXF estándar estructurado con capas organizadas.
    Compatible con AutoCAD, LibreCAD, QCAD, BricsCAD, etc.
    
    :param localizacion: Lista de dicts {norte, este, color, tipo, sobrenombre}
    :param linea: Lista de dicts {norte, este}
    :param circulo: Lista de dicts {norte, este, radio}
    :param radiacion: Lista de dicts {norte, este, angulo, distancia, etiqueta, color}
    :param coord_system: 'utm' (en metros, recomendado para CAD) o 'wgs84' (grados)
    :param output_path: Ruta destino del archivo .dxf
    :return: output_path
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Definir capas estándar con colores distintivos
    layers = [
        ('LOCALIZACION', 4),       # Cian
        ('LOCALIZACION_TXT', 7),   # Blanco/Texto
        ('PERIMETRO_LINEAS', 3),   # Verde
        ('CIRCULOS', 6),           # Magenta
        ('RADIALES', 2),           # Amarillo
        ('RADIALES_PERIMETRO', 1), # Rojo
    ]
    for layer_name, color_aci in layers:
        if layer_name not in doc.layers:
            doc.layers.add(name=layer_name, color=color_aci)

    def to_coords(lat, lon):
        """Convierte coordenadas a (X, Y) para CAD según el sistema elegido."""
        if coord_system == 'utm':
            try:
                if abs(lat) > 90 or abs(lon) > 180:
                    return float(lon), float(lat)
                n, e, _ = gms2utm(lat, lon)
                return float(e), float(n)  # En CAD X=Este, Y=Norte
            except Exception:
                return float(lon), float(lat)
        return float(lon), float(lat)

    # 1. PUNTOS DE LOCALIZACIÓN
    for i, pt in enumerate(localizacion):
        try:
            lat = float(pt.get('norte', 0.0))
            lon = float(pt.get('este', 0.0))
            if abs(lat) < 0.0001 and abs(lon) < 0.0001:
                continue
            x, y = to_coords(lat, lon)
            label = str(pt.get('sobrenombre') or f"P{i+1}")
            pt_color = get_aci_color(pt.get('color'))

            # Insertar punto CAD
            msp.add_point((x, y, 0), dxfattribs={'layer': 'LOCALIZACION', 'color': pt_color})
            
            # Texto identificador con pequeño offset
            txt_height = 15.0 if coord_system == 'utm' else 0.0002
            msp.add_text(label, dxfattribs={
                'layer': 'LOCALIZACION_TXT',
                'height': txt_height,
                'color': pt_color
            }).set_placement((x + txt_height * 0.5, y + txt_height * 0.5, 0))
        except Exception as e:
            print(f"[DXF] Error exportando punto {pt}: {e}")

    # 2. POLILÍNEA / LÍNEA
    if len(linea) > 1:
        pts_linea = []
        for pt in linea:
            try:
                lat = float(pt.get('norte', 0.0))
                lon = float(pt.get('este', 0.0))
                if abs(lat) < 0.0001 and abs(lon) < 0.0001:
                    continue
                pts_linea.append(to_coords(lat, lon))
            except Exception:
                continue
        if len(pts_linea) >= 2:
            msp.add_lwpolyline(pts_linea, dxfattribs={'layer': 'PERIMETRO_LINEAS', 'color': 3})

    # 3. CÍRCULOS
    for i, c in enumerate(circulo):
        try:
            lat = float(c.get('norte', 0.0))
            lon = float(c.get('este', 0.0))
            radio_m = float(c.get('radio', 100.0))
            if abs(lat) < 0.0001 and abs(lon) < 0.0001:
                continue
            x, y = to_coords(lat, lon)
            # En WGS84 1 grado ~= 111,320 m
            radius_cad = radio_m if coord_system == 'utm' else (radio_m / 111320.0)
            msp.add_circle((x, y, 0), radius=radius_cad, dxfattribs={'layer': 'CIRCULOS', 'color': 6})
        except Exception as e:
            print(f"[DXF] Error exportando círculo {c}: {e}")

    # 4. RADIALES
    if radiacion:
        grouped = {}
        for r in radiacion:
            try:
                lat = float(r.get('norte', 0.0))
                lon = float(r.get('este', 0.0))
                ang = float(r.get('angulo', 0.0))
                dist_km = float(r.get('distancia', 1.0))
                color = r.get('color', 'red')
                key = (round(lat, 6), round(lon, 6))
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append((ang, dist_km, color))
            except Exception:
                continue

        for (c_lat, c_lon), rays in grouped.items():
            cx, cy = to_coords(c_lat, c_lon)
            rays.sort(key=lambda item: item[0])
            perimeter_pts = []

            for ang_deg, dist_km, col in rays:
                # En matemáticas de CAD: 0° azimut suele ser Norte (eje Y) o Este (eje X)
                # En geodesia/topografía: Azimut 0° es Norte, 90° es Este (sentido horario)
                ang_rad = math.radians(ang_deg)
                dist_m = dist_km * 1000.0

                if coord_system == 'utm':
                    # dx = d * sin(azimut), dy = d * cos(azimut)
                    dx = dist_m * math.sin(ang_rad)
                    dy = dist_m * math.cos(ang_rad)
                    end_x = cx + dx
                    end_y = cy + dy
                else:
                    # Aproximación en grados
                    d_deg = dist_km / 111.32
                    dx = d_deg * math.sin(ang_rad)
                    dy = d_deg * math.cos(ang_rad)
                    end_x = cx + dx
                    end_y = cy + dy

                perimeter_pts.append((end_x, end_y))
                rad_color = get_aci_color(col)
                # Dibujar rayo
                msp.add_line((cx, cy, 0), (end_x, end_y, 0), dxfattribs={'layer': 'RADIALES', 'color': rad_color})

            # Polígono perimetral que envuelve los radiales
            if len(perimeter_pts) >= 2:
                span = rays[-1][0] - rays[0][0]
                is_full = (span >= 330.0) or (len(rays) > 2 and (360.0 - span) <= (rays[1][0] - rays[0][0]) * 1.5)
                if is_full and len(perimeter_pts) >= 3:
                    closed_poly = perimeter_pts + [perimeter_pts[0]]
                else:
                    closed_poly = [(cx, cy)] + perimeter_pts + [(cx, cy)]
                msp.add_lwpolyline(closed_poly, dxfattribs={'layer': 'RADIALES_PERIMETRO', 'color': 1})

    doc.saveas(output_path)
    return output_path

def send_to_active_autocad(localizacion, linea, circulo, radiacion, coord_system='utm'):
    """
    Se conecta vía COM a una sesión de AutoCAD abierta en Windows
    y dibuja las entidades directamente en el ModelSpace activo.
    """
    try:
        import win32com.client
        import pythoncom
    except ImportError:
        return {'status': 'error', 'message': 'El módulo pywin32 no está disponible en este entorno.'}

    prog_ids = [
        "AutoCAD.Application",
        "AutoCAD.Application.25",
        "AutoCAD.Application.24.1",
        "AutoCAD.Application.24",
        "AutoCAD.Application.23.1",
        "AutoCAD.Application.23",
        "AutoCAD.Application.22",
        "AutoCAD.Application.21",
        "AutoCAD.Application.20.1",
        "AutoCAD.Application.20",
    ]

    app = None
    last_err = None
    for prog_id in prog_ids:
        try:
            app = win32com.client.GetActiveObject(prog_id)
            if app:
                break
        except Exception as e:
            last_err = e
            continue

    if not app:
        return {
            'status': 'error',
            'message': 'No se detectó ninguna instancia de AutoCAD en ejecución. Abre AutoCAD con un dibujo nuevo y vuelve a intentar.'
        }

    try:
        doc = app.ActiveDocument
        msp = doc.ModelSpace
    except Exception as e:
        return {'status': 'error', 'message': f'Error accediendo al espacio de dibujo activo de AutoCAD: {e}'}

    def _get_double_array(x, y, z=0.0):
        return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (float(x), float(y), float(z)))

    def to_coords(lat, lon):
        if coord_system == 'utm':
            try:
                if abs(lat) > 90 or abs(lon) > 180:
                    return float(lon), float(lat)
                n, e, _ = gms2utm(lat, lon)
                return float(e), float(n)
            except Exception:
                return float(lon), float(lat)
        return float(lon), float(lat)

    created_count = 0

    # 1. Puntos
    for pt in localizacion:
        try:
            lat = float(pt.get('norte', 0.0))
            lon = float(pt.get('este', 0.0))
            if abs(lat) < 0.0001 and abs(lon) < 0.0001: continue
            x, y = to_coords(lat, lon)
            msp.AddPoint(_get_double_array(x, y, 0.0))
            created_count += 1
        except Exception:
            continue

    # 2. Líneas
    if len(linea) > 1:
        for i in range(len(linea) - 1):
            try:
                p1, p2 = linea[i], linea[i+1]
                x1, y1 = to_coords(float(p1['norte']), float(p1['este']))
                x2, y2 = to_coords(float(p2['norte']), float(p2['este']))
                msp.AddLine(_get_double_array(x1, y1), _get_double_array(x2, y2))
                created_count += 1
            except Exception:
                continue

    # 3. Círculos
    for c in circulo:
        try:
            lat = float(c.get('norte', 0.0))
            lon = float(c.get('este', 0.0))
            radio_m = float(c.get('radio', 100.0))
            if abs(lat) < 0.0001 and abs(lon) < 0.0001: continue
            x, y = to_coords(lat, lon)
            rad = radio_m if coord_system == 'utm' else (radio_m / 111320.0)
            msp.AddCircle(_get_double_array(x, y), rad)
            created_count += 1
        except Exception:
            continue

    # 4. Radiales
    for r in radiacion:
        try:
            lat = float(r.get('norte', 0.0))
            lon = float(r.get('este', 0.0))
            ang = float(r.get('angulo', 0.0))
            dist_km = float(r.get('distancia', 1.0))
            cx, cy = to_coords(lat, lon)
            ang_rad = math.radians(ang)
            dist_m = dist_km * 1000.0
            dx = dist_m * math.sin(ang_rad) if coord_system == 'utm' else (dist_km / 111.32) * math.sin(ang_rad)
            dy = dist_m * math.cos(ang_rad) if coord_system == 'utm' else (dist_km / 111.32) * math.cos(ang_rad)
            msp.AddLine(_get_double_array(cx, cy), _get_double_array(cx + dx, cy + dy))
            created_count += 1
        except Exception:
            continue

    return {
        'status': 'ok',
        'message': f'¡Se han dibujado exitosamente {created_count} entidades en AutoCAD!',
        'count': created_count
    }
