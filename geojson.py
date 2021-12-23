import folium
import geopandas
import sys

def geojsonread(mapName):
    #mapName = folium.Map()
    counties_gdf = geopandas.read_file('./venezuela/curvas_nivel/Venezuela_Curvas_Nivel.shp')
    counties_gdf.head()
    print(counties_gdf.head())
    return folium.GeoJson(data=counties_gdf["geometry"], name='COTA_MTS', localize=True)).add_to(mapName)
    #map
map = folium.Map()
geojsonread(map)
map.save('MapaCurvas.html')
map

