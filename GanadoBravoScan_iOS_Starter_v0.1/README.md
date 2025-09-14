# GanadoBravo Scan — iOS Starter (v0.1)

SwiftUI + ARKit (SceneDepth/LiDAR) **starter** para capturar 12–20 s, seleccionar *keyframes*, fusionar a un **point cloud**,
exportar **PLY** y subirlo a tu backend (`/api/scans/upload`).

> Esqueleto listo para pegar en un proyecto Xcode (SwiftUI App). En 5–10 min lo corres.

## Requisitos
- Xcode 15+ / iOS 16+ (recomendado 17+), iPhone con **LiDAR** (Pro) para profundidad densa. También corre en iPhones sin LiDAR, pero desactiva SceneDepth (queda RGB-only).
- Activa: **Camera Usage**, **Motion** (opcional), **ARKit**. Opcional: **Associated Domains** si usarás Universal Links.

## Pasos rápidos (nuevo proyecto)
1. Xcode → iOS App (SwiftUI) → `GanadoBravoScan`.
2. Arrastra los archivos de `Sources/*.swift` y `Resources/*` al proyecto (Copy if needed).
3. En `Info.plist`, agrega:
   - `NSCameraUsageDescription` = "Necesitamos la cámara para escanear el animal."
   - (Opcional) `NSPhotoLibraryAddUsageDescription` si guardarás archivos.
   - `UIRequiredDeviceCapabilities`: agrega `arkit` (para forzar dispositivos compatibles).
4. En `Signing & Capabilities`:
   - (Opcional) **Associated Domains** → `applinks:scan.ganadobravo.app` (ajústalo a tu dominio).
5. Updatea `Config.swift` con tu endpoint y token.

## Flujo
- **Start Scan** → captura frames 12–20 s.
- Selección de **keyframes** (10–20) por *parallax* (ángulo) y calidad.
- **Fusión** simple a **point cloud** (unproject depth -> world) + limpieza básica (downsample por voxel + radius outlier removal).
- **PLY export** (ASCII) y **upload** con `sid` y `token` (multipart).
- Volver a tu web vía Universal Link (si lo habilitas) o mostrar el status.

## Endpoint esperado
```
POST /api/scans/upload
Content-Type: multipart/form-data
fields: sid=<string>, token=<string>, meta=<json>, file=@model.ply (o model.glb)
-> 200 { "ok": true, "sid": "<sid>" }
```
Puedes reusar tu backend actual; añade un handler para almacenar el scan.

## Notas y TODO
- El **TSDF**/meshing avanzado NO está incluido (esto es point cloud + limpieza). Suficiente para volumen aproximado y métricas iniciales.
- `Segmentation` va como *placeholder* (puedes integrar un CoreML para máscara de bovino antes de fusionar).
- En iPhone sin LiDAR, `sceneDepth` no está → puedes capturar RGB para fotogrametría posterior ó usar ARKit `depthData` si disponible.

## Estructura
- `GanadoBravoScanApp.swift` — App entry.
- `ContentView.swift` — UI principal (Start/Stop, progreso, export, upload).
- `DepthCaptureManager.swift` — ARSession + capturas + keyframes.
- `PointCloudFusion.swift` — Unprojection + voxel downsample + radius outlier removal.
- `PLYWriter.swift` — Serialización PLY.
- `Uploader.swift` — Multipart POST.
- `Config.swift` — Ajustes de API / Universal Link.
- `Models.swift` — Tipos auxiliares.
- `README.md` — Este archivo.

## Build
Compila y corre en iPhone (no en simulador). Si falla por permisos, revisa `Info.plist`.
