from __future__ import annotations
import io, math, numpy as np
from typing import Any, Dict
try:
    import trimesh
except Exception:
    trimesh = None

def _fit_plane_ransac(points: np.ndarray, max_iters: int = 800, thresh: float = 0.02):
    import random
    N = points.shape[0]
    if N < 50:
        n0 = np.array([0,1,0], float); d0 = 0.0
        return n0, d0, np.zeros(N, dtype=bool), float("nan")
    best_inliers = None; best_n=None; best_d=None
    rng = random.Random(42); idx = list(range(N))
    for _ in range(max_iters):
        i1,i2,i3 = rng.sample(idx,3)
        p1,p2,p3 = points[i1],points[i2],points[i3]
        v1,v2 = p2-p1, p3-p1
        n = np.cross(v1,v2); norm = np.linalg.norm(n)
        if norm < 1e-6: continue
        n = n/norm; d = -float(n @ p1)
        dist = np.abs(points @ n + d)
        inl = dist <= thresh
        if best_inliers is None or inl.sum() > best_inliers.sum():
            best_inliers, best_n, best_d = inl, n, d
    if best_inliers is None:
        n0 = np.array([0,1,0], float); d0 = 0.0
        return n0, d0, np.zeros(N, dtype=bool), float("nan")
    dist = np.abs(points @ best_n + best_d)
    rmse = float(np.sqrt(np.mean(dist[best_inliers]**2))) if best_inliers.any() else float("nan")
    return best_n, float(best_d), best_inliers, rmse

def _to_numpy_vertices(mesh) -> np.ndarray:
    if hasattr(mesh, 'vertices'):
        return np.asarray(mesh.vertices, dtype=float)
    return np.asarray(mesh.get('vertices', []), dtype=float)

def extract_lidar_metrics(file_bytes: bytes, filename: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    if trimesh is None:
        return {"error": "trimesh no disponible"}
    file_obj = io.BytesIO(file_bytes)
    ft = filename.split('.')[-1].lower()
    try:
        mesh = trimesh.load(file_obj, file_type=ft, force='mesh')
    except Exception:
        file_obj.seek(0); mesh = trimesh.load(file_obj, force='mesh')
    if not isinstance(mesh, trimesh.Trimesh):
        if hasattr(mesh, 'dump'):
            mesh = mesh.dump().sum()

    V = _to_numpy_vertices(mesh).astype(float)
    V = V[np.isfinite(V).all(axis=1)]
    if V.size == 0:
        return {"error": "Malla vacía o no soportada"}

    # Ground plane + crop
    n, d, inliers, rmse = _fit_plane_ransac(V, max_iters=800, thresh=0.02)
    dist_signed = V @ n + d
    keep = dist_signed >= -0.01
    V = V[keep]

    # PCA axes
    C = V.mean(0, keepdims=True)
    X = V - C
    U,S,Vt = np.linalg.svd(X, full_matrices=False)
    axes = Vt
    Xp = X @ axes.T
    L = float(Xp[:,0].ptp())
    W = float(Xp[:,1].ptp())
    H = float(Xp[:,2].ptp())

    # Heart girth approx by slab hull at 40% length
    x_min, x_max = float(Xp[:,0].min()), float(Xp[:,0].max())
    slab = (Xp[:,0] >= x_min + 0.37*(x_max-x_min)) & (Xp[:,0] <= x_min + 0.43*(x_max-x_min))
    yz = Xp[slab][:,1:3]
    heart_girth = float('nan')
    if yz.shape[0] >= 50:
        pts = yz[np.lexsort((yz[:,1], yz[:,0]))]
        def cross(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
        lower=[]; upper=[]
        for p in pts:
            while len(lower)>=2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
            lower.append(tuple(p))
        for p in reversed(pts):
            while len(upper)>=2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
            upper.append(tuple(p))
        hull = np.array(lower[:-1]+upper[:-1])
        per=0.0
        for i in range(len(hull)):
            a=hull[i]; b=hull[(i+1)%len(hull)]
            per += float(np.linalg.norm(np.array(b)-np.array(a)))
        heart_girth = float(per)

    # Volume/peso aprox
    try:
        est_vol = float(mesh.volume if mesh.is_volume else mesh.convex_hull.volume)
    except Exception:
        est_vol = float('nan')
    weight_est = (heart_girth**2 * L)/11877.0 if np.isfinite(heart_girth) and heart_girth>0 else float('nan')

    quality = {
        "coverage_pct": 80.0 if V.shape[0] > 5_000 else 50.0,
        "noise_level": 0.08 if V.shape[0] > 5_000 else 0.2,
        "ground_plane_fit_rmse": rmse,
        "scale_warning": not (0.9 <= H <= 1.9),
    }

    return {{
        "quality": quality,
        "withers_height_m": H, "body_length_m": L, "heart_girth_m": heart_girth,
        "chest_depth_m": float(np.ptp(yz[:,1])) if isinstance(yz, np.ndarray) and yz.size else float('nan'),
        "hip_width_m": W, "rump_angle_deg": float('nan'),
        "estimated_volume_m3": est_vol, "stance_asymmetry_idx": float('nan'),
        "weight_est_kg": weight_est,
    }}
