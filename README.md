# Analizador Geoespacial WiFi - UAB THE HACK! 2025

Este repositorio reune todo lo que usamos para el hackathon de la UAB: el dashboard web con IA, los datos anonimizados de la WiFi del campus y el kit oficial del reto. La idea es que cualquiera del equipo pueda clonar el repo y tenerlo listo para iterar, generar mapas y lanzar preguntas al chatbot AINA sin depender de carpetas sueltas.

## Que encontraras aqui

- **Apps**: backend en FastAPI (cliente de la IA de AINA + endpoints propios) y frontend ligero en HTML/JS/CSS con los mapas embebidos.
- **Datos**: historicos completos (~21 GB), snapshots ligeros y los JSON filtrados (`rookie_*`) para prototipar rapido.
- **Docs oficiales**: el kit de la UAB tal cual lo entregaron, en `docs/hackathon-kit`.
- **Toolkit geoespacial**: scripts y ejemplos para experimentar con los datos sin tocar la demo principal.

El script main.py lee los datos de los Puntos de Acceso (APs) y de los clientes conectados, los procesa y genera tres mapas dinámicos e interactivos en formato .html.

```
.
|- apps/
|  |- backend/             # FastAPI, cliente de la IA y orquestacion
|  |- frontend/            # Web estatica, mapas y llamadas al backend
|- data/
|  |- context/ai/          # Prompt base y archivos que se inyectan al LLM
|  |- processed/rookie/    # Datos agregados listos para mapas (rookie_*)
|  |- raw/
|     |- anonymized_data/  # Dump completo entregado por la UAB (APs + clientes)
|     |- snapshots/        # Muestras pequenas para pruebas rapidas
|- docs/hackathon-kit/     # Manuales, logos y materiales del reto
|- packages/geolocation/   # Utilidades y ejemplos de visualizacion
|- scripts/                # Lanzadores para bash y PowerShell
|- .venv/ (opcional)       # Entorno virtual local
```

## Como funciona el script principal (`main.py`)

1. **Carga de fuentes**  
   - `rookie_filtered_aps.json` (nombre y coordenadas UTM EPSG:25831 de cada AP).  
   - `rookie_filtered_clients.json` (timestamp, AP, salud, senal y metricas del cliente).
2. **Conversion geografica**: pasa de UTM a latitud/longitud (EPSG:4326) para poder usar mapas web.
3. **Agregacion temporal**: agrupa por AP, dia y hora; calcula `avg_health`, `avg_signal_db` y `num_clients_metricos`.
4. **Generacion de mapas**: con Folium + `TimestampedGeoJson`, usando `duration='PT1H'` para evitar stacking y centrando la escena en Veterinaria con animacion rapida (`max_speed=100`).
5. **Salida**: tres HTML interactivos listos para abrir o incrustar en el frontend.

## Mapas interactivos generados

| Archivo                       | Metrica principal                        | Visualizacion                                                     |
|------------------------------|------------------------------------------|-------------------------------------------------------------------|
| `mapa_health_dinamico.html`  | Salud media de conexion (0-100)          | Circulos de tamano fijo con gradiente de rojo (0) a verde (100).  |
| `mapa_signal_dinamico.html`  | Intensidad media de senal (-90 a -30 dBm)| Circulos fijos, color de rojo (debil) a verde (fuerte).           |
| `mapa_clientes_dinamico.html`| Numero total de clientes por AP          | Radio dinamico; borde verde->rojo segun carga; relleno transparente. |

Todos incluyen slider temporal y boton "Play" para recorrer las horas del dataset.

## Requisitos

- Python 3.10 o superior con `pip`.
- PowerShell 7+ (Windows) o bash/zsh (macOS/Linux).
- Navegador moderno.
- Variable `AINA_API_KEY` si quieres usar un token diferente al de pruebas.

Dependencias clave (ademas de las del `requirements.txt`):

```bash
pip install folium pandas pyproj branca
pip install numpy pytz python-dateutil tzdata requests
```

## Instalacion rapida

```bash
git clone <este_repo>
cd uab-the-hack
python -m venv .venv                # en Windows: py -3 -m venv .venv
source .venv/bin/activate           # en Windows: .\.venv\Scripts\activate
pip install -r apps/backend/requirements.txt
```

## Ejecucion

### Scripts listos

```bash
# bash / zsh
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

```powershell
# PowerShell 7+
pwsh scripts/run_backend.ps1
pwsh scripts/run_frontend.ps1
```

### Modo manual

```bash
# Backend
cd apps/backend
uvicorn main:app --reload

# Frontend (otra terminal)
cd apps/frontend
python -m http.server 8001
```

Abre `http://127.0.0.1:8001` y lanza tus preguntas; el frontend llama a `http://127.0.0.1:8000/api/chat`.

### Acceso rapido a la API (flujo anterior)

Si prefieres mantener el mismo flujo que usabas antes de reorganizar carpetas, sigue estos pasos desde la raiz del repo:

```bash
cd uab-the-hack/backend
source uab-the-hack/backend/.venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Con eso el backend queda escuchando en `http://127.0.0.1:8000` y puedes consumir la API de AINA igual que antes (no olvides exportar `AINA_API_KEY` en esa terminal).

## API del backend

| Metodo | Ruta        | Descripcion                                       |
|--------|-------------|---------------------------------------------------|
| GET    | `/health`   | Comprobacion rapida de que el backend sigue vivo  |
| POST   | `/api/chat` | Recibe `{ "message": "<texto>" }` y responde la IA |

La variable `FRONTEND_ORIGINS` permite ampliar la lista de origenes autorizados para CORS.

## Datos y ejemplos

- Historicos completos: `data/raw/anonymized_data/aps/*.json` y `clients/*.json`.
- Conjuntos ligeros para pruebas: `data/raw/snapshots/`.
- Agregados listos: `data/processed/rookie/*.json`.
- Ejemplos practicos: `packages/geolocation/examples/*.py` (ya apuntan a los datos raw).

## Uso del chatbot AINA

1. Ajusta el prompt y los anexos en `data/context/ai/el_teu_arxiu.txt` (mensajes cortos, sin ambiguedades).  
2. Si necesitas nuevos datos estadisticos, subelos en CSV/TXT a esa misma carpeta y referencia el archivo en el prompt.  
3. Instala cualquier libreria auxiliar (`requests`, etc.) dentro del entorno virtual antes de ejecutar el backend.  
4. Define `AINA_API_KEY` cuando quieras usar un token propio y reinicia el backend para que recoja la variable.  
5. Lanza preguntas desde el frontend; el backend compone el contexto y reenvia la consulta al endpoint de AINA.

## Problemas habituales

- **Mapa sin fondo**: Folium necesita internet para cargar los tiles de OpenStreetMap. Si ves un lienzo gris o blanco, revisa firewalls o la conexion.  
- **Datos pesados**: los ~21 GB del historico completo no son obligatorios; usa `snapshots/` para iterar rapido.  
- **CORS**: si sirves el frontend desde otro puerto u host, ampliala con `FRONTEND_ORIGINS`.  
- **Dependencias**: algunos notebooks usan `requests`, `geopy` u otras libs; instalalas en el `.venv` segun lo que necesites.

## Checklist antes de presentar

1. Activar el entorno virtual e instalar dependencias (`pip install -r apps/backend/requirements.txt`).  
2. Definir `AINA_API_KEY` (o usar el token por defecto).  
3. Lanzar backend y frontend (scripts o modo manual) y validar `/health`.  
4. Ejecutar `main.py` si necesitas regenerar los mapas o actualizar metricas.  
5. Abrir los tres HTML (`apps/frontend/maps/`) y tenerlos listos para ensenar.  
6. Revisar que el chatbot responda bien con las instrucciones actualizadas.

Listo: clonas, instalas, generas mapas y tienes material suficiente para impresionar al jurado.
