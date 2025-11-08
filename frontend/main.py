import pandas as pd
import folium
from folium.plugins import HeatMapWithTime
from pyproj import Transformer
import json
from collections import defaultdict

# --- Constantes ---
# Archivos de entrada
FILE_APS = 'rookie_filtered_aps.json'
FILE_CLIENTS = 'rookie_filtered_clients.json'

# Archivos de salida
OUTPUT_MAP_HEALTH = 'mapa_health_dinamico.html'
OUTPUT_MAP_SIGNAL = 'mapa_signal_dinamico.html'
OUTPUT_MAP_CLIENTS = 'mapa_clientes_dinamico.html'

# --- ¡CAMBIOS SOLICITADOS! ---
# Aumentamos el radio de 40 a 70 para reducir la atenuación
MAP_RADIUS = 70
# --------------------------------

# Gradiente para "Bueno es Verde" (Health, Señal)
GRADIENT_GOOD_IS_GREEN = {0.2: 'red', 0.5: 'yellow', 1.0: 'green'}
# Gradiente para "Mucho es Rojo" (Nº Clientes)
GRADIENT_HIGH_IS_RED = {0.2: 'green', 0.5: 'yellow', 1.0: 'red'}


# Definimos el conversor de coordenadas.
try:
    transformer = Transformer.from_crs("epsg:25831", "epsg:4326")
except ImportError:
    print("Error: La librería 'pyproj' no está instalada.")
    print("Por favor, instálala ejecutando: py -m pip install pyproj")
    exit()

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
    
    # --- ¡CAMBIO SOLICITADO! Calcular límites para centrado automático ---
    min_lat = df_ap_locations['lat'].min()
    max_lat = df_ap_locations['lat'].max()
    min_lon = df_ap_locations['lon'].min()
    max_lon = df_ap_locations['lon'].max()
    map_bounds = [[min_lat, min_lon], [max_lat, max_lon]]
    # -----------------------------------------------------------------

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

# --- 4. Preparar Datos para los Mapas Dinámicos ---
print("Formateando datos para los mapas de calor dinámicos...")

df_master['hour_str'] = df_master['hour'].astype(str).str.zfill(2)
df_master['timestamp_str'] = df_master['date'].dt.strftime('%Y-%m-%d') + 'T' + df_master['hour_str'] + ':00:00'
df_master = df_master.sort_values(by='timestamp_str')

time_index = df_master['timestamp_str'].unique().tolist()

data_health_dict = defaultdict(list)
data_signal_dict = defaultdict(list)
data_clientes_dict = defaultdict(list)

for _, row in df_master.iterrows():
    time_step = row['timestamp_str']
    lat = row['lat']
    lon = row['lon']
    
    # 1. Datos de Health
    avg_health = row['avg_health']
    data_health_dict[time_step].append([lat, lon, avg_health])
    
    # 2. Datos de Signal (dBm)
    signal_weight = (100 + row['avg_signal_db'])
    signal_weight = max(0, signal_weight) 
    data_signal_dict[time_step].append([lat, lon, signal_weight])
    
    # 3. Datos de Conteo de Clientes
    client_count = row['num_clients_metricos']
    data_clientes_dict[time_step].append([lat, lon, client_count])

data_health = [data_health_dict[time_step] for time_step in time_index]
data_signal = [data_signal_dict[time_step] for time_step in time_index]
data_clientes = [data_clientes_dict[time_step] for time_step in time_index]

print(f"Datos preparados para {len(time_index)} pasos de tiempo.")


# --- 5. Función para crear y guardar los mapas ---
# --- ¡MODIFICADA! Acepta 'bounds' para el centrado automático ---
def create_dynamic_heatmap(map_data, time_index, ap_locations, output_filename, map_title, gradient_config, map_radius, bounds):
    print(f"Creando mapa: {output_filename}...")
    
    # --- ¡CAMBIO SOLICITADO! ---
    # Ya no centramos manualmente. Usamos fit_bounds()
    m = folium.Map()
    m.fit_bounds(bounds)
    # ---------------------------

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
            color="#e63946",
            fill=True,
            fill_color="#e63946",
            fill_opacity=0.6,
            popup=f"<b>AP:</b> {ap['name']}<br><b>Edificio:</b> {ap['building_name']}"
        ).add_to(fg_aps)
    
    fg_aps.add_to(m)

    hm = HeatMapWithTime(
        map_data,
        index=time_index,
        auto_play=True,
        max_opacity=0.7,
        radius=map_radius,       # <-- Radio modificado a 70
        gradient=gradient_config,
        name=map_title
    )
    hm.add_to(m)

    title_html = f'''
                 <div style="position: fixed; 
                             top: 10px; left: 50px; z-index:1000;
                             font-size: 24px; font-weight: bold; color: #1d3557;
                             background-color: rgba(255, 255, 255, 0.7);
                             padding: 5px 15px; border-radius: 5px;
                             ">
                   {map_title} (UAB)
                 </div>
                 '''
    m.get_root().html.add_child(folium.Element(title_html))

    folium.LayerControl().add_to(m)
    m.save(output_filename)
    print(f"¡Mapa guardado! -> {output_filename}")


# --- 6. Generar los TRES mapas ---
# --- ¡MODIFICADO! Pasamos 'map_bounds' a cada llamada ---
create_dynamic_heatmap(
    data_health, 
    time_index, 
    df_ap_locations, 
    OUTPUT_MAP_HEALTH, 
    "Mapa de Calor: Health (0=Rojo, 100=Verde)",
    GRADIENT_GOOD_IS_GREEN,
    MAP_RADIUS,
    map_bounds # <-- Pasamos los límites
)

create_dynamic_heatmap(
    data_signal, 
    time_index, 
    df_ap_locations, 
    OUTPUT_MAP_SIGNAL, 
    "Mapa de Calor: Señal dBm (Mala=Rojo, Buena=Verde)",
    GRADIENT_GOOD_IS_GREEN,
    MAP_RADIUS,
    map_bounds # <-- Pasamos los límites
)

create_dynamic_heatmap(
    data_clientes, 
    time_index, 
    df_ap_locations, 
    OUTPUT_MAP_CLIENTS, 
    "Mapa de Calor: Nº Clientes (Pocos=Verde, Muchos=Rojo)",
    GRADIENT_HIGH_IS_RED,
    MAP_RADIUS,
    map_bounds # <-- Pasamos los límites
)

print("\n¡Proceso completado! Revisa los TRES archivos .html generados.")
