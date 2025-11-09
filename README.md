Analizador Geoespacial WiFi de la UAB (UAB THE HACK! 2025)

Este proyecto analiza los datos de la red WiFi del campus de la UAB, proporcionados para el hackathon UAB THE HACK! 2025.

El script main.py lee los datos de los Puntos de Acceso (APs) y de los clientes conectados, los procesa y genera tres mapas dinámicos e interactivos en formato .html.

¿Qué hace el script?

El script main.py realiza las siguientes operaciones:

Carga dos fuentes de datos:

rookie_filtered_aps.json: Contiene la información de los Puntos de Acceso (APs), incluyendo su nombre y sus coordenadas de ubicación (x, y).

rookie_filtered_clients.json: Un registro de conexiones de clientes, incluyendo la hora, el AP al que se conectó, la salud (health) de la conexión y la intensidad de la señal (signal_db).

Conversión de Coordenadas: Convierte las coordenadas x, y de los APs (que están en formato UTM EPSG:25831) a Latitud, Longitud (EPSG:4326), que es el formato que los mapas web entienden.

Procesado y Agregación: Agrupa los miles de registros de clientes por AP, Día y Hora. Para cada grupo, calcula:

La salud media (avg_health).

La señal media (avg_signal_db).

El número total de clientes (num_clients_metricos).

Generación de Mapas (Bubble Map): Utiliza la librería folium y el plugin TimestampedGeoJson para crear tres mapas dinámicos.

Evita el "Stacking": El script se ha diseñado específicamente para solucionar el problema de "apilamiento". Usando duration='PT1H', cada círculo de datos solo "vive" durante una hora en la animación, limpiando el mapa en cada paso de tiempo.

Centrado y Rápido: Los mapas se cargan centrados en un punto clave del campus (Veterinaria) y la animación está configurada a alta velocidad (max_speed=100).

Los 3 Mapas Generados

El script produce tres archivos .html interactivos. Todos incluyen un slider de tiempo y un botón de "Play".

1. mapa_health_dinamico.html

Qué muestra: La "Salud" media de la conexión en cada AP.

Visualización: Círculos de tamaño fijo.

Color: El color del círculo cambia dinámicamente (de Rojo [mala salud, 0] a Verde [buena salud, 100]).

2. mapa_signal_dinamico.html

Qué muestra: La "Señal" media (dBm) en cada AP.

Visualización: Círculos de tamaño fijo.

Color: El color del círculo cambia dinámicamente (de Rojo [mala señal, -90dBm] a Verde [buena señal, -30dBm]).

3. mapa_clientes_dinamico.html (El Mapa Principal)

Qué muestra: El número total de clientes conectados a cada AP.

Visualización: ¡Círculos de TAMAÑO DINÁMICO!

El Radio del círculo se hace más grande cuantos más clientes hay.

El Borde del círculo cambia de color (de Verde [pocos clientes] a Rojo [muchos clientes]).

El Relleno del círculo es transparente para poder ver el marcador del AP que hay debajo.

Instalación y Uso

Sigue estos pasos para ejecutar el proyecto.

1. Entorno y Librerías

Se asume que estás usando un entorno virtual de Python (ej: .venv).

Instala todas las librerías necesarias con pip (asegúrate de tener tu entorno virtual activado):

# Instala las librerías principales para mapas, datos y conversión
py -m pip install folium pandas pyproj branca

# Instala las dependencias que 'pandas' puede necesitar
py -m pip install numpy pytz python-dateutil tzdata


2. Estructura de Archivos

Asegúrate de tener tus archivos en la misma carpeta:

HACKATHON 2025/
│
├── .venv/                   (Tu entorno virtual)
├── main.py                  (Este script)
├── rookie_filtered_aps.json   (Datos de APs)
└── rookie_filtered_clients.json (Datos de Clientes)


3. Ejecución

Una vez instaladas las librerías, simplemente ejecuta el script main.py desde tu terminal:

py main.py


4. Resultados

El script tardará unos segundos en procesar todos los datos. Cuando termine, verás los siguientes mensajes y ya podrás abrir los archivos .html en tu navegador:

Script iniciado...
Cargando y procesando clientes...
[...]
Formateando datos GeoJSON...
Creando mapa: mapa_health_dinamico.html
¡Mapa guardado! -> mapa_health_dinamico.html
Creando mapa: mapa_signal_dinamico.html
¡Mapa guardado! -> mapa_signal_dinamico.html
Creando mapa: mapa_clientes_dinamico.html
¡Mapa guardado! -> mapa_clientes_dinamico.html

¡Proceso completado! Revisa los TRES archivos .html generados.


Nota Importante sobre la Red

La librería folium necesita conexión a internet para descargar el mapa de fondo (las calles, edificios, etc., de OpenStreetMap).

Si abres los archivos .html y ves los círculos y el slider, pero el fondo del mapa está gris o en blanco, significa que tu ordenador no puede conectarse a los servidores del mapa (posiblemente por un firewall de la red del hackathon o una conexión lenta).
