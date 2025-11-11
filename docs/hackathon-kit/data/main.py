import pandas as pd
import folium
from folium.plugins import TimestampedGeoJson
from pyproj import Transformer
import json
import branca # Necesario para las escalas de color
import numpy as np # Necesario para comprobar NaNs

# --- Constantes ---
FILE_APS = 'rookie_filtered_aps.json'
FILE_CLIENTS = 'rookie_filtered_clients.json'

# Archivos de salida
OUTPUT_MAP_HEALTH = 'mapa_health_dinamico.html'
OUTPUT_MAP_SIGNAL = 'mapa_signal_dinamico.html'
OUTPUT_MAP_CLIENTS = 'mapa_clientes_dinamico.html'

# --- Función de Escala (para el radio) ---
def linear_scale(value, in_min, in_max, out_min, out_max):
    """
    Mapea un valor de un rango a otro (interpolación lineal).
    Usado para calcular el radio del círculo.
    """
    if in_min == in_max:
        return (out_min + out_max) / 2
    clamped_value = max(in_min, min(value, in_max))
    in_range = in_max - in_min
    out_range = out_max - out_min
    scaled_value = (clamped_value - in_min) / in_range
    return out_min + (scaled_value * out_range)

# Definimos el conversor de coordenadas.
try:
    transformer = Transformer.from_crs("epsg:25831", "epsg:4326")
except ImportError:
    print("Error: La librería 'pyproj' no está instalada.")
    print("Por favor, instálala ejecutando: py -m pip install pyproj branca")
    exit()

# --- ¡MODIFICADO! Coordenadas de inicio ---
# Coordenadas de AP-VET71
start_x, start_y = 424638.107049, 4595093.80301
start_lat, start_lon = transformer.transform(start_x, start_y)
map_center_coords = [start_lat, start_lon]
# ------------------------------------

print("Script iniciado...")

# --- 1. Cargar y Procesar Datos de Clientes ---
print(f"Cargando y procesando clientes desde {FILE_CLIENTS}...")
try:
    df_clients = pd.read_json(FILE_CLIENTS)
    
    df_clients['health'] = pd.to_numeric(df_clients['health'], errors='coerce')
    df_clients['signal_db'] = pd.to_numeric(df_clients['signal_db'], errors='coerce')
    df_clients = df_clients.dropna(subset=['health', 'signal_db', 'associated_device_name', 'date', 'hour'])

    df_metrics = df_clients.groupby(['date', 'hour', 'associated_device_name']).agg(
        avg_health=('health', 'mean'),
        avg_signal_db=('signal_db', 'mean'),
        num_clients_metricos=('health', 'size')
    ).reset_index()

    df_metrics.rename(columns={'associated_device_name': 'name'}, inplace=True)
    print(f"Métricas de clientes calculadas (ej: {len(df_metrics)} registros de AP/hora).")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo {FILE_CLIENTS}")
    exit()
except Exception as e:
    print(f"Error procesando {FILE_CLIENTS}: {e}")
    exit()

# --- 2. Cargar y Procesar Ubicaciones de APs ---
print(f"Cargando y procesando APs desde {FILE_APS}...")
try:
    with open(FILE_APS, 'r', encoding='utf-8') as f:
        data_aps = json.load(f)
    df_aps = pd.DataFrame(data_aps)

    df_aps = df_aps.dropna(subset=['location'])
    df_ap_locations = df_aps.drop_duplicates(subset=['name'], keep='last').copy()

    def convert_coordinates(row):
        try:
            x = row['location']['x']
            y = row['location']['y']
            lat, lon = transformer.transform(x, y)
            return pd.Series([lat, lon, row['location'].get('building_name', 'N/A')])
        except Exception:
            return pd.Series([None, None, None])

    print("Convirtiendo coordenadas UTM a Lat/Lon (esto puede tardar un momento)...")
    df_ap_locations[['lat', 'lon', 'building_name']] = df_ap_locations.apply(convert_coordinates, axis=1)
    df_ap_locations = df_ap_locations.dropna(subset=['lat', 'lon'])
    df_ap_locations = df_ap_locations[['name', 'lat', 'lon', 'building_name']]
    print(f"Ubicaciones únicas de APs procesadas (total: {len(df_ap_locations)} APs).")
    
except FileNotFoundError:
    print(f"Error: No se encontró el archivo {FILE_APS}")
    exit()
except Exception as e:
    print(f"Error procesando {FILE_APS}: {e}")
    exit()

# --- 3. Unir Métricas y Ubicaciones ---
print("Uniendo métricas de clientes con ubicaciones de APs...")
df_master = pd.merge(df_metrics, df_ap_locations, on='name', how='inner')

if df_master.empty:
    print("Error: No se ha podido encontrar datos comunes entre clientes y APs.")
    exit()

# Creamos el timestamp string en el dataframe maestro
df_master['hour_str'] = df_master['hour'].astype(str).str.zfill(2)
df_master['timestamp_str'] = df_master['date'].dt.strftime('%Y-%m-%d') + 'T' + df_master['hour_str'] + ':00:00'


# --- 4. Preparar Datos para TimestampedGeoJson (¡MODIFICADO!) ---
print("Creando 'scaffolding' de tiempo/AP para evitar 'stacking'...")

# Obtenemos todos los APs únicos y todos los tiempos únicos
all_aps_data = df_ap_locations[['name', 'lat', 'lon', 'building_name']]
all_times = df_master['timestamp_str'].unique()
all_times.sort() # Nos aseguramos de que el tiempo esté ordenado

# 1. Crear el "andamio" (scaffolding) con todas las combinaciones posibles
df_scaffold_index = pd.MultiIndex.from_product([all_aps_data['name'].unique(), all_times], names=['name', 'timestamp_str'])
df_scaffold = pd.DataFrame(index=df_scaffold_index).reset_index()

# 2. Unir el andamio con los datos de AP (para tener lat/lon siempre)
df_master_full = pd.merge(df_scaffold, all_aps_data, on='name', how='left')

# 3. Unir con los datos de métricas (esto creará 'NaN' donde no haya datos)
df_master_full = pd.merge(
    df_master_full, 
    df_master, 
    on=['name', 'timestamp_str', 'lat', 'lon', 'building_name'], 
    how='left'
)

print(f"Formateando datos GeoJSON para los mapas dinámicos (Total features: {len(df_master_full)})...")

# --- Definir escalas de color y tamaño ---
cmap_bueno_es_verde = branca.colormap.LinearColormap(['red', 'yellow', 'green'], vmin=0, vmax=100)
max_clients_global = df_master['num_clients_metricos'].max()
if pd.isna(max_clients_global) or max_clients_global == 0: max_clients_global = 1 
cmap_mucho_es_rojo = branca.colormap.LinearColormap(['green', 'yellow', 'red'], vmin=0, vmax=max_clients_global)

# Estilo INVISIBLE para APs sin datos
style_invisible = {
    'color': '#000000', 'fillColor': '#000000',
    'opacity': 0.0, 'fillOpacity': 0.0, 'weight': 0, 'radius': 0
}

# --- Función para crear las "features" de GeoJSON (corregida) ---
def create_feature(row, timestamp, iconstyle, popup):
    """Crea una única feature de GeoJSON para un punto en el tiempo."""
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [row['lon'], row['lat']]
        },
        'properties': {
            'time': timestamp,
            'icon': 'circle',       
            'iconstyle': iconstyle,   
            'popup': popup
        }
    }

features_health = []
features_signal = []
features_clients = []

# Iteramos sobre el dataframe COMPLETO (df_master_full)
for _, row in df_master_full.iterrows():
    ts = row['timestamp_str']
    
    # Comprobamos si hay datos para esta hora/AP
    is_active = not pd.isna(row['avg_health'])
    
    if is_active:
        # --- Si está ACTIVO, creamos estilos VISIBLES ---
        popup_html = (f"<b>AP:</b> {row['name']}<br>"
                      f"<b>Edificio:</b> {row['building_name']}<br>"
                      f"<b>Hora:</b> {ts}<br>"
                      f"<b>Health:</b> {row['avg_health']:.1f}<br>"
                      f"<b>Señal:</b> {row['avg_signal_db']:.1f} dBm<br>"
                      f"<b>Clientes:</b> {row['num_clients_metricos']}")
        
        # 1. Estilo Health
        health_color = cmap_bueno_es_verde(row['avg_health'])
        style_health = {
            'color': health_color, 'fillColor': health_color,
            'opacity': 0.8, 'fillOpacity': 0.6, 'weight': 1, 'radius': 15
        }
        
        # 2. Estilo Signal
        signal_weight = (100 + row['avg_signal_db']) 
        signal_color = cmap_bueno_es_verde(signal_weight)
        style_signal = {
            'color': signal_color, 'fillColor': signal_color,
            'opacity': 0.8, 'fillOpacity': 0.6, 'weight': 1, 'radius': 15
        }

        # 3. Estilo Clientes
        client_radius = linear_scale(row['num_clients_metricos'], 0, max_clients_global, 5, 40)
        client_color = cmap_mucho_es_rojo(row['num_clients_metricos'])
        style_clients = {
            'color': client_color, 'fillOpacity': 0.0, 'opacity': 0.7,
            'weight': 3, 'radius': client_radius
        }
    
    else:
        # --- Si está INACTIVO, creamos estilos INVISIBLES ---
        popup_html = f"<b>AP:</b> {row['name']}<br><b>Hora:</b> {ts}<br>Sin datos"
        
        style_health = style_invisible
        style_signal = style_invisible
        style_clients = style_invisible
    
    # Añadimos la feature (visible o invisible)
    features_health.append(create_feature(row, ts, style_health, popup_html))
    features_signal.append(create_feature(row, ts, style_signal, popup_html))
    features_clients.append(create_feature(row, ts, style_clients, popup_html))

print(f"Datos GeoJSON preparados.")

# --- 5. Función para crear y guardar los mapas (¡MODIFICADA!) ---
def create_dynamic_bubble_map(features_list, ap_locations, output_filename, map_title):
    print(f"Creando mapa: {output_filename}...")
    
    # --- ¡CAMBIO! Centramos en las coordenadas dadas con zoom 16 ---
    m = folium.Map(location=map_center_coords, zoom_start=16)

    # Capa 1: Marcadores de APs
    fg_aps = folium.FeatureGroup(name='Mostrar Ubicación de APs')
    offset_lat = 0.00003
    offset_lon = 0.00004
    for _, ap in ap_locations.iterrows():
        bounds_rect = [
            [ap['lat'] - offset_lat, ap['lon'] - offset_lon],
            [ap['lat'] + offset_lat, ap['lon'] + offset_lon]
        ]
        folium.Rectangle(
            bounds=bounds_rect,
            color="#e63946", fill=True, fill_color="#e63946", fill_opacity=0.6,
            popup=f"<b>AP:</b> {ap['name']}<br><b>Edificio:</b> {ap['building_name']}"
        ).add_to(fg_aps)
    fg_aps.add_to(m)

    # Capa 2: Círculos Dinámicos
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': features_list},
        period='PT1H', 
        duration='PT1H', # <-- ¡ARREGLO PARA "STACKING"! (Cada círculo dura 1h)
        add_last_point=False, # <-- No dejar el último punto
        auto_play=False,
        loop=False,
        max_speed=100, # <-- ¡VELOCIDAD AUMENTADA!
        loop_button=True,
        date_options='YYYY-MM-DD HH:mm',
        time_slider_drag_update=True,
    ).add_to(m)

    # Título
    title_html = f'''
                 <div style="position: fixed; top: 10px; left: 50px; z-index:1000;
                             font-size: 24px; font-weight: bold; color: #1d3557;
                             background-color: rgba(255, 255, 255, 0.7);
                             padding: 5px 15px; border-radius: 5px;">
                   {map_title} (UAB)
                 </div>
                 '''
    m.get_root().html.add_child(folium.Element(title_html))

    folium.LayerControl().add_to(m)
    m.save(output_filename)
    print(f"¡Mapa guardado! -> {output_filename}")

# --- 6. Generar los TRES mapas ---
create_dynamic_bubble_map(
    features_health,
    df_ap_locations,
    OUTPUT_MAP_HEALTH,
    "Mapa Dinámico: Health (Color: 0=Rojo, 100=Verde)"
)

create_dynamic_bubble_map(
    features_signal,
    df_ap_locations,
    OUTPUT_MAP_SIGNAL,
    "Mapa Dinámico: Señal (Color: Malo=Rojo, Bueno=Verde)"
)

create_dynamic_bubble_map(
    features_clients,
    df_ap_locations,
    OUTPUT_MAP_CLIENTS,
    "Mapa Dinámico: Nº Clientes (Tamaño: Dinámico | Borde: Verde-Rojo)"
)

print("\n¡Proceso completado! Revisa los TRES archivos .html generados.")
