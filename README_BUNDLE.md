
# GanadoBravo — Full Bundle

Este paquete incluye:
- **GanadoBravo_WebAPI_v4.3.20** (FastAPI + front estático) — listo para Railway.
- **GanadoBravoScan_iOS_Starter_v0.1** (SwiftUI + ARKit) — app nativa para escaneo 3D (starter).

## Despliegue Web/API
1) Variables en Railway (ejemplo):
   - `OPENAI_API_KEY` = tu clave
   - `GB_PRO_MODE_ENABLED` = "1"
   - `GB_ALLOW_3D_UPLOADS` = "1" (opcional, si habilitas endpoint /api/scans/upload)
2) `Procfile` y `requirements.txt` ya incluidos.
3) Endpoint principal: `/evaluate` (POST) + front en `/`.
4) Pro mode: muestra cámara 2D y enlaces a app 3D (algunas restricciones de iOS aplican).

## iOS Scan Starter
- Proyecto starter Xcode (SwiftUI + ARKit SceneDepth). Captura 12–20s, keyframes, nube de puntos PLY, subida multipart.
- Edita `Sources/Config.swift` para apuntar `uploadURL` a tu dominio.
- Revisa `README.md` dentro de esa carpeta para pasos rápidos.

