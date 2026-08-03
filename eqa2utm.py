import math
from pyproj import Transformer, CRS

def gms2utm(lat, lon):
    """
    Convierte latitud y longitud (grados decimales WGS84) a Coordenadas UTM.
    Retorna (norte, este, huso)
    """
    lon_clamped = max(-179.999999, min(179.999999, float(lon)))
    lat_clamped = max(-80.0, min(84.0, float(lat)))
    e2u_zone = max(1, min(60, int(divmod(lon_clamped, 6)[0]) + 31))
    south = lat_clamped < 0
    try:
        crs_utm = CRS.from_dict({'proj': 'utm', 'zone': e2u_zone, 'south': south, 'ellps': 'WGS84'})
        transformer = Transformer.from_crs("EPSG:4326", crs_utm, always_xy=True)
        utmx, utmy = transformer.transform(lon_clamped, lat_clamped)
        return utmy, utmx, e2u_zone
    except Exception as e:
        print(f"Error en transformación gms2utm para lat={lat}, lon={lon}: {e}")
        return 0.0, 0.0, e2u_zone

def utm2gms(norte, este, huso, south=False):
    """
    Convierte coordenadas UTM (norte, este, huso) a Latitud y Longitud.
    Retorna (latitud, longitud)
    """
    try:
        crs_utm = CRS.from_dict({'proj': 'utm', 'zone': huso, 'south': south, 'ellps': 'WGS84'})
        transformer = Transformer.from_crs(crs_utm, "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(este, norte)
        return lat, lon
    except Exception as e:
        print(f"Error en transformación utm2gms para norte={norte}, este={este}, huso={huso}: {e}")
        return 0.0, 0.0
