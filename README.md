# UAB THE HACK!

Proyecto base para el hackathon de la UAB (2º curso). Objetivo: mostrar un asistente sencillo con frontend Bootstrap y backend FastAPI listo para conectarse a un LLM o a datos estructurados.

## Estructura del repositorio

```
.
├── backend/          # FastAPI + futuras integraciones de datos
├── frontend/         # HTML/JS/CSS para la demo
└── scripts/          # Lanzadores rápidos (bash y PowerShell)
```

## Requisitos previos

- Python 3.10 o superior con `pip`.
- PowerShell 7+ (Windows) o bash/zsh (macOS/Linux).
- Navegador moderno (Chrome, Edge o Firefox).

## Instalación

```bash
git clone https://github.com/itsCarlosDev/uab-the-hack.git
cd uab-the-hack
python -m venv .venv        # En Windows: py -3 -m venv .venv
source .venv/bin/activate   # En Windows: .\\.venv\\Scripts\\activate
pip install -r backend/requirements.txt
```

> `pandas`, `sqlmodel` y `python-dotenv` ya están listos para cuando integremos datos/secretos. De momento no requieren configuración extra.

## Ejecución para la demo

### Opción recomendada (scripts)

macOS/Linux:

```bash
./scripts/run_backend.sh
./scripts/run_frontend.sh
```

Windows (PowerShell):

```powershell
pwsh scripts/run_backend.ps1
pwsh scripts/run_frontend.ps1
```

### Opción manual

1. **Backend**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
2. **Frontend**
   ```bash
   cd frontend
   python -m http.server 8001
   ```
3. Abre [http://127.0.0.1:8001](http://127.0.0.1:8001) y lanza tu pregunta. El `fetch` apunta a `http://127.0.0.1:8000/api/chat`.

## Endpoints disponibles

| Método | Ruta        | Descripción                                |
|--------|-------------|--------------------------------------------|
| GET    | `/health`   | Status de la API para comprobaciones rápidas |
| POST   | `/api/chat` | Recibe `{ "message": str }` y devuelve eco |

> CORS está activado para orígenes locales (`localhost`, `127.0.0.1`, `file://`) así la página funciona aunque se abra directamente desde el disco.

## Checklist previa a la demo

1. Crear/activar el entorno virtual y ejecutar `pip install -r backend/requirements.txt`.
2. Lanzar backend y frontend con los scripts (o comandos manuales).
3. Verificar `http://127.0.0.1:8000/health`.
4. Probar al menos una pregunta desde la UI.
5. Preparar speech rápido: qué hace el backend ahora, qué datos/LLM se van a conectar después.

## Estructura de commits

- `feat`: añadir endpoint /api/chat en FastAPI
- `feat`: crear pantalla principal con Bootstrap
- `fix`: corregir llamada a la API del LLM
- `refactor`: separar rutas del backend en módulos
- `docs`: actualizar README con instrucciones de ejecución
- `chore`: añadir config básica de gitignore y estructura de proyecto

¡Listo para iterar y enseñar al jurado!
