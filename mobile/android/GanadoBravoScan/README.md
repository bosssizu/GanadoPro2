# GanadoBravoScan (Android, ARCore Depth)
- Verifica soporte ARCore y Depth; si falta, muestra **No soportado** y puedes usar análisis 2D en web.
- Falta implementar el lazo de captura + PLY + upload (ver iOS como guía).

## Próximos pasos
1. Bucle con `session.update()` y `acquireDepthImage16Bits()`.
2. Desproyección a metros usando intrínsecos + pose.
3. Voxel/filtrado → PLY (80–150k pts) y POST multipart a `/api/evaluate`.
