# GanadoBravo IA — Full App v4.1 (Pro mode)

- **Análisis 2D:** igual que siempre (no cambia).
- **Pro mode (3D):** opcional. Acepta `mesh_file` (OBJ/PLY/GLB/USDZ) y `meta_json`. Ajusta la decisión con métricas geométricas.
- **Mobile starters incluidos:** iOS (ARKit SceneDepth) y Android (ARCore Depth) con manejo **No soportado**.

## Deploy rápido (Railway)
1. Variables:
   - `OPENAI_API_KEY` (**obligatoria**)
   - Opcional: `PRO_MODE_ENABLED=true` (si quieres mostrar el toggle siempre, aunque el frontend ya lo trae).
2. Ejecutable: `Procfile` → `web: uvicorn main:app --host=0.0.0.0 --port=${PORT:-8000}`
3. `runtime.txt`: `python-3.11.9`

## Endpoints
- `GET /` → UI (./static/index.html)
- `POST /api/evaluate` → campos `category`, `file` (imagen), opcionales `pro=1`, `mesh_file`, `meta_json`.

## meta_json ejemplo
```json
{"units":"m","scale":1.0,"source":"ios-arkit-depth","frames_kept":16,"angle_covered_deg":185}
```

## Mobile
- iOS: `mobile/ios/GanadoBravoScan` (SwiftUI + ARKit). Abre `Config.swift` y pon tu URL de backend.
- Android: `mobile/android/GanadoBravoScan`. Detecta ARCore/Depth; deja TODO para captura + PLY + upload.

## Notas
- Si el dispositivo **no soporta** LiDAR/Depth, las apps muestran **No soportado** y puedes seguir con 2D.
- El backend usa `gpt-4o-mini` vía Responses API o fallback a Chat Completions si no está disponible.
