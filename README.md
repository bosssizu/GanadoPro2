# GanadoBravo Fullstack IA (v4.1, fixed)


GanadoBravo Fullstack IA (GPT-4o) v4.0
Morfología/Salud/Raza independientes de categoría (determinismo: temperature=0)
Decisión por categoría con pesos y offsets ajustados (levante +0.4, vaca flaca +0.8, engorde -0.3)
Regla de levante: si estructura fuerte (≥7.0) y BCS ≥6.0 → al menos "Considerar alto"
Cache por imagen + normalización a pasos de 0.5 para estabilidad


FastAPI + OpenAI Vision (GPT-4o mini) app to evaluate bovine images for **levante / engorde / vaca flaca**.
This version reconstructs and completes the truncated files from your upload, adds stricter JSON parsing,
deterministic prompts, caching, and a consistent decision fallback.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
uvicorn main:app --reload
# open http://localhost:8000/static/index.html
```

## API
POST `/api/evaluate`
- form-data: `category` in {levante, engorde, "vaca flaca"}, `file` (image)

## Notes
- Deterministic outputs: temperature=0
- Health & breed are computed once per image (cache) and reused across categories
- Weighted decision per category + offsets; fallback mapping if LLM JSON is incomplete
- Scores are normalized to steps of 0.5 for stability


## Pro mode (LiDAR)
- Actívalo con el toggle en el formulario o enviando `pro=1` + `mesh_file` al mismo endpoint `/api/evaluate`.
- El análisis 2D **no cambia** si no envías `pro` y `mesh_file`.
- Formatos soportados: OBJ, PLY, GLB/GLTF, USDZ (preferidos OBJ/PLY).
- Requiere dependencias: open3d, trimesh, numpy, scipy.
- El servidor extrae métricas 3D deterministas (largo, alto, girth, volumen, etc.) y ajusta la decisión sin romper el flujo actual.

> **Nota sobre “Escanear”**: los navegadores no exponen el sensor LiDAR. Para escanear en 3D necesitas una **app nativa iOS (ARKit)** o Android que genere un **OBJ/PLY/GLB/USDZ**. La web UI muestra “Escanear”, pero por ahora significa **subir el archivo del escaneo**.
