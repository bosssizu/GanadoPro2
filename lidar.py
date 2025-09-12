
# lidar.py — métricas 3D deterministas para Pro mode
from __future__ import annotations
import io, math, numpy as np
from typing import Dict, Any, Tuple

try:
    import trimesh
except Exception:
    trimesh = None

def _to_numpy_vertices(mesh) -> np.ndarray:
    # Soporta Trimesh o dict-like
    if hasattr(mesh, 'vertices'):
        V = np.asarray(mesh.vertices, dtype=float)
    else:
        V = np.asarray(mesh.get('vertices', []), dtype=float)
    return V

def _principal_axes(V: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    Vc = V - V.mean(0, keepdims=True)
    # SVD para PCA
    U, S, Vt = np.linalg.svd(Vc, full_matrices=False)
    return Vt[0], Vt[1], Vt[2]

def _slice_section(V: np.ndarray, axis: np.ndarray, center: float, half_thickness: float=0.03):
    # Selecciona puntos con proyección cercana a 'center' sobre 'axis'
    proj = V @ axis
    mask = (proj >= center - half_thickness) & (proj <= center + half_thickness)
    return V[mask]

def _perimeter_convex_2d(pts2: np.ndarray) -> float:
    if pts2.shape[0] < 10:
        return float('nan')
    # Convex hull "a mano" (monotone chain)
    pts = pts2[np.lexsort((pts2[:,1], pts2[:,0]))]
    def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[]
    for p in pts:
        while len(lower)>=2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(tuple(p))
    upper=[]
    for p in reversed(pts):
        while len(upper)>=2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(tuple(p))
    hull = np.array(lower[:-1]+upper[:-1])
    per = 0.0
    for i in range(len(hull)):
        a = hull[i]; b = hull[(i+1)%len(hull)]
        per += math.hypot(b[0]-a[0], b[1]-a[1])
    return float(per)

def extract_lidar_metrics(file_bytes: bytes, filename: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    if trimesh is None:
        # Sin trimesh instalado, devolvemos métrica mínima para no romper
        return {
            "quality": {"coverage_pct": 0.0, "noise_level": 1.0, "notes": "trimesh no disponible"},
            "withers_height_m": float('nan'),
            "body_length_m": float('nan'),
            "heart_girth_m": float('nan'),
            "chest_depth_m": float('nan'),
            "hip_width_m": float('nan'),
            "rump_angle_deg": float('nan'),
            "estimated_volume_m3": float('nan'),
            "stance_asymmetry_idx": float('nan'),
            "weight_est_kg": float('nan'),
        }
    # Cargar con trimesh
    file_obj = io.BytesIO(file_bytes)
    try:
        mesh = trimesh.load(file_obj, file_type=filename.split('.')[-1].lower(), force='mesh')
    except Exception:
        # Intento genérico
        file_obj.seek(0)
        mesh = trimesh.load(file_obj, force='mesh')
    if not isinstance(mesh, trimesh.Trimesh):
        # Si vino escena, toma geometría combinada
        if hasattr(mesh, 'dump'):
            mesh = mesh.dump().sum()
        elif hasattr(mesh, 'geometry') and len(mesh.geometry):
            geo = list(mesh.geometry.values())[0]
            mesh = geo
    V = _to_numpy_vertices(mesh)
    if V.size == 0:
        raise ValueError("Malla vacía o formato no soportado")
    # Escala
    scale = float(meta.get("scale", 1.0))
    V = V * scale

    # PCA ejes
    ex, ey, ez = _principal_axes(V)
    # Proyección
    X = V @ np.vstack([ex, ey, ez]).T

    # Rangos como primeras aproximaciones L,W,H
    body_length = float(np.ptp(X[:,0]))
    width = float(np.ptp(X[:,1]))
    height = float(np.ptp(X[:,2]))

    # Sección torácica en ~40% del largo (aprox región corazón)
    x_min, x_max = float(X[:,0].min()), float(X[:,0].max())
    x_center = x_min + 0.40*(x_max - x_min)
    slab = (X[:,0] >= x_center-0.03) & (X[:,0] <= x_center+0.03)
    yz = X[slab][:,1:3]
    heart_girth = _perimeter_convex_2d(yz)

    # Profundidad de pecho: rango Z en sección torácica
    chest_depth = float(np.ptp(yz[:,1])) if yz.size else float('nan')

    # Ancho de grupa: usa percentil 80–90% del largo
    x_rump = x_min + 0.85*(x_max - x_min)
    slab_r = (X[:,0] >= x_rump-0.03) & (X[:,0] <= x_rump+0.03)
    rump_y = X[slab_r][:,1]
    hip_width = float(np.ptp(rump_y)) if rump_y.size else float('nan')

    # Volumen: usa volumen de malla si está cerrada; si no, convex hull
    try:
        if mesh.is_volume:
            est_vol = float(mesh.volume) * (scale**3)
        else:
            hull = mesh.convex_hull
            est_vol = float(hull.volume) * (scale**3)
    except Exception:
        est_vol = float('nan')

    # Peso por fórmula cinta (métrica aproximada): (girth^2 * length) / 11877 → kg
    # Nota: heart_girth aproximado por perímetro; transformar a "circunferencia" estimando círculo equivalente
    if math.isfinite(heart_girth) and heart_girth > 0:
        # perímetro ≈ circunferencia
        circ = heart_girth
        girth_diam = circ / math.pi
        # circunferencia a "girth lineal" suele medirse como circunferencia; usamos circ directamente
        weight_est = ( (circ**2) * body_length ) / 11877.0
    else:
        weight_est = float('nan')

    # Calidad simple (placeholder determinista)
    coverage_pct = 80.0 if V.shape[0] > 5000 else 50.0
    noise_level = 0.08 if coverage_pct >= 80 else 0.2

    # Índice de aplomos (muy básico): variación de anchura en zona distal (percentil 5–10% Z)
    z_min, z_max = float(X[:,2].min()), float(X[:,2].max())
    z_distal = z_min + 0.08*(z_max - z_min)
    feet = X[(X[:,2] <= z_distal)]
    stance_asym = float(np.std(feet[:,1]))/max(1e-6, abs(width)) if feet.size else float('nan')

    return {
        "quality": {"coverage_pct": coverage_pct, "noise_level": noise_level},
        "withers_height_m": height,
        "body_length_m": body_length,
        "heart_girth_m": heart_girth,
        "chest_depth_m": chest_depth,
        "hip_width_m": hip_width,
        "rump_angle_deg": float('nan'),  # derivable con planos sacro/ilion (pendiente)
        "estimated_volume_m3": est_vol,
        "stance_asymmetry_idx": stance_asym,
        "weight_est_kg": weight_est,
    }
