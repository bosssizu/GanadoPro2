# GanadoBravo IA — Full App v4.1 (Pro)

- **2D**: IA para morfología (11 métricas), salud y raza + decisión por categoría (pesos/offsets; pasos 0.5).
- **Pro (3D)**: opcional, combina métricas LiDAR/Depth con la IA; si no hay escáner abre la cámara 2D.

## Deploy
- `OPENAI_API_KEY` obligatoria.
- `Procfile` listo: `web: uvicorn main:app --host=0.0.0.0 --port=${PORT:-8000}`
- Python 3.11.9; requirements pinneados (httpx/httpcore compatibles).

## Endpoints
- `GET /` → UI estática.
- `POST /api/evaluate` → `category`, `file` (imagen), opcionales `pro=1`, `mesh_file`, `meta_json`.

## Mobile
Incluye deep-link en la web para abrir apps iOS/Android si existen; si no, cae a 2D.
