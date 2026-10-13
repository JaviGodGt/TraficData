# Traffic Ingestion Service (Grupo 2)

Microservicio de ingesta de **tráfico vehicular real** para el proyecto *Monitoreo Urbano e Inteligencia Ambiental* (Universidad San Pablo de Guatemala).

Dado un punto GPS real (`lat`/`lon`):

1. Consulta Mapbox Directions (`driving-traffic` + `driving`)
2. Calcula el Índice de Congestión ∈ [0, 1]
3. Arma el Data Contract estándar y lo envía (o imprime en `DRY_RUN`) al Data Warehouse del G4
4. Guarda métricas crudas en SQLite para Looker Studio

**Regla:** sin datos simulados en producción. Si Mapbox falla o la lectura es inválida, se descarta y se registra el error.

## Requisitos

- Python 3.11+
- Token de Mapbox con acceso a Directions API

## Instalación

```bash
cd traffic-service
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Editar .env con MAPBOX_ACCESS_TOKEN, STUDENT_ID y SECRET_KEY
```

**Importante:** copia `.env.example` → `.env` y pon el token ahí. `.env` está en `.gitignore` — **nunca** lo subas a GitHub. Si el token se filtró (chat, screenshot, commit), regenerarlo en Mapbox y reemplazarlo en `.env`.

CSV de puntos reales de ejemplo: `data/points.csv`.

```bash
# Smoke test local (DRY_RUN, Mapbox real)
python -m app.cli run --csv data/points.csv
```

## Variables de entorno

| Variable | Requerida | Default | Descripción |
| --- | --- | --- | --- |
| `MAPBOX_ACCESS_TOKEN` | sí | — | Token Mapbox |
| `STUDENT_ID` | sí | — | Identificador del estudiante/grupo |
| `SECRET_KEY` | sí | — | Clave compartida para `auth_hash` |
| `DW_ENDPOINT_URL` | no | — | URL REST del DW (G4) |
| `DW_AUTH_TOKEN` | no | — | Token Bearer opcional |
| `DRY_RUN` | no | `true` | Si `true` o no hay DW URL: no envía, imprime payload |
| `SEGMENT_LENGTH_M` | no | `400` | Longitud del tramo sintético (m) |
| `SEGMENT_BEARING_DEG` | no | `0` | Rumbo del segundo punto (°) |
| `DB_PATH` | no | `traffic.db` | SQLite local |
| `GROUP1_API_URL` | no | — | Reservado para fuente G1 (stub) |

Los secretos **nunca** se hardcodean ni se loguean.

### Nota Mapbox

`annotations` requiere `overview=full` (docs Directions v5). El perfil `driving-traffic` usa `overview=full` + `annotations=duration,distance,congestion_numeric`. El perfil `driving` usa `overview=false`.

## API FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- `GET /health` → `{"status":"ok"}`
- `POST /traffic/reading` body: `{"latitude": 14.6349, "longitude": -90.5069}`

Respuesta incluye `status` (`SENT` | `DRY_RUN` | `FAILED` | `INVALID`), `payload` (si aplica) y `error`.

## CLI

```bash
# Ingestar puntos reales desde CSV (columnas lat,lon o latitude,longitude)
python -m app.cli run --csv points.csv

# Bucle cada 5 minutos
python -m app.cli run --csv points.csv --loop --interval 300

# Exportar SQLite → CSV (fuente Looker Studio)
python -m app.cli export-csv --out readings.csv
```

## Script de cobertura (evidencia hora pico / valle)

```bash
python scripts/coverage_check.py --csv points.csv --log coverage_log.csv
```

Imprime una tabla por punto (`t_traffic`, `t_free`, distancia, índice, congestion promedio) y agrega cada corrida con timestamp a `coverage_log.csv`.

## Tests

Los mocks de Mapbox viven **solo** en `tests/` (vía `respx`).

```bash
pytest -q
```

## Data Contract (enviado al DW)

Campos: `reading_id`, `timestamp`, `latitude`, `longitude`, `student_id`, `auth_hash`, `domain_data` (`noise_db`, `traffic_congestion_index`, `air_quality_aqi`). Sin campos extra.

Índice: `(t_traffic - t_free) / t_traffic`, clamp [0, 1], 4 decimales.

## TODO(G2)

- Confirmar formato exacto de `auth_hash` con G4
- Confirmar endpoint y autenticación del DW
- Confirmar aceptación de `null` en `noise_db` / `air_quality_aqi`
- Implementar `Group1ApiSource` cuando exista el feed de coordenadas
