import math
import numpy as np

def haversine_distance(origin, destination):
    """
    Calcula la distancia haversine en kilómetros entre dos puntos (lat, lon).
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371.0088  # Radio medio terrestre WGS84 en km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c

def distanceAndAngle(latitude, longitude, angulo, distance):
    """
    Calcula el punto destino (lat, lon) desde un punto inicial, un azimut/ángulo (deg) y una distancia (km).
    """
    R = 6378.137  # Radio terrestre WGS-84 en km
    d = distance
    brng = math.radians(angulo)
    lat1 = math.radians(latitude)
    lon1 = math.radians(longitude)

    lat2 = math.asin(math.sin(lat1) * math.cos(d / R) +
                     math.cos(lat1) * math.sin(d / R) * math.cos(brng))

    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d / R) * math.cos(lat1),
                             math.cos(d / R) - math.sin(lat1) * math.sin(lat2))

    return math.degrees(lat2), math.degrees(lon2)

def distance2points(lat1, lon1, lat2, lon2):
    return haversine_distance((lat1, lon1), (lat2, lon2))

def rf_signal_decay(d_ratio):
    """
    Calcula la atenuación no lineal de la señal de radio en función de la distancia relativa.
    d_ratio = d / D_max (0 en el centro transmisor, 1 en el perímetro).
    Retorna intensidad de radiación entre 1.0 (100% en centro) y 0.001 (0% en perímetro).
    """
    if d_ratio <= 0:
        return 1.0
    elif d_ratio >= 1.0:
        return 0.001

    decay = math.pow(math.cos((math.pi / 2.0) * d_ratio), 1.8)
    return max(0.001, round(decay, 4))

def smooth_radiation_perimeter(latitude, longitude, angulos, distancias, sub_points=12):
    """
    Genera un perímetro de radiación con curvas suaves (spline polar cerrado)
    intercalando sub-puntos suaves entre cada par de azimuts consecutivos.
    """
    if not angulos or not distancias or len(angulos) < 2:
        coords = []
        for i in range(len(angulos)):
            lat, lon = distanceAndAngle(latitude, longitude, angulos[i], distancias[i])
            coords.append([lat, lon])
        return coords

    # Ordenar por ángulo
    pairs = sorted(zip(angulos, distancias), key=lambda x: x[0])
    angs = [p[0] for p in pairs]
    dists = [p[1] for p in pairs]

    # Cerrar el bucle polar añadiendo 360 grados al primer ángulo
    if angs[-1] < 360:
        angs.append(angs[0] + 360.0)
        dists.append(dists[0])

    smooth_coords = []

    # Interpolación catmull-rom / spline cúbica polar suave
    for i in range(len(angs) - 1):
        a1, a2 = angs[i], angs[i+1]
        d1, d2 = dists[i], dists[i+1]

        # Puntos de control vecinos para pendiente suave
        d0 = dists[i-1] if i > 0 else dists[-2]
        d3 = dists[i+2] if (i+2) < len(dists) else dists[1]

        for k in range(sub_points):
            t = k / float(sub_points)
            # Interpolación cúbica Hermite/Catmull-Rom para distancia radial
            t2 = t * t
            t3 = t2 * t
            
            # Funciones base de Hermite
            h00 = 2*t3 - 3*t2 + 1
            h10 = t3 - 2*t2 + t
            h01 = -2*t3 + 3*t2
            h11 = t3 - t2

            m0 = 0.5 * (d2 - d0)
            m1 = 0.5 * (d3 - d1)

            d_interp = h00 * d1 + h10 * m0 + h01 * d2 + h11 * m1
            d_interp = max(0.01, d_interp)

            a_interp = a1 + t * (a2 - a1)

            lat_interp, lon_interp = distanceAndAngle(latitude, longitude, a_interp, d_interp)
            smooth_coords.append([lat_interp, lon_interp])

    # Cerrar la polilínea repitiendo el primer punto
    if smooth_coords:
        smooth_coords.append(smooth_coords[0])

    return smooth_coords

def distanceAndAngleInterpolation(latitude, longitude, angulo, distance, heat_user=None):
    """
    Genera puntos interpolados desde el centro transmisor (100% de radiación) hasta el perímetro (0% de radiación),
    utilizando el modelo no lineal de atenuación de ondas de radio.
    """
    R = 6378.137  # Radio terrestre en km
    lista = []

    num_particiones = 20

    for i in range(num_particiones + 1):
        d_ratio = i / float(num_particiones)
        d_km = d_ratio * distance
        
        heat_val = rf_signal_decay(d_ratio)

        brng = math.radians(angulo)
        lat1 = math.radians(latitude)
        lon1 = math.radians(longitude)

        lat2 = math.asin(math.sin(lat1) * math.cos(d_km / R) +
                         math.cos(lat1) * math.sin(d_km / R) * math.cos(brng))

        lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d_km / R) * math.cos(lat1),
                                 math.cos(d_km / R) - math.sin(lat1) * math.sin(lat2))

        lista.append([math.degrees(lat2), math.degrees(lon2), heat_val, angulo, distance])

    return lista
