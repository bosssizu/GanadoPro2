# GanadoBravoScan (iOS, ARKit SceneDepth)
- Requiere iOS 15+ y dispositivo con **LiDAR** (iPhone/iPad Pro).
- Si el device no soporta SceneDepth se muestra **No soportado** y puedes seguir con el análisis 2D en web.
- Edita `Config.swift` para poner la URL de tu backend (`/api/evaluate`).

## Flujo
1. Toca Escanear (6–20 s, 120–270° alrededor).
2. Keyframing + desproyección a metros → nube (PLY) 80–150k pts.
3. Toma 1 foto RGB.
4. Subida a `/api/evaluate` con `pro=1`, `mesh_file`, `file` y `meta_json`.
