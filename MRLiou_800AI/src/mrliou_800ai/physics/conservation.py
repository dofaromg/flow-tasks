from __future__ import annotations
import numpy as np
from .operators import time_derivative, div2d, div3d

def mass_terms(rho, u, v, t, dx, dy, w=None, dz=None) -> dict:
    rho, u, v = map(lambda x: np.asarray(x, dtype=float), (rho, u, v))
    if not (rho.shape == u.shape == v.shape): raise ValueError("rho/u/v shapes must match")
    drho_dt = time_derivative(rho, np.asarray(t, dtype=float))
    if rho.ndim == 3:
        divergence = div2d(rho*u, rho*v, float(dx), float(dy))
        spatial_axes = (1, 2)
    elif rho.ndim == 4:
        if w is None or dz is None: raise ValueError("3D fields require w and dz")
        w = np.asarray(w, dtype=float)
        if w.shape != rho.shape: raise ValueError("w shape must match rho")
        divergence = div3d(rho*u, rho*v, rho*w, float(dx), float(dy), float(dz))
        spatial_axes = (1, 2, 3)
    else:
        raise ValueError("rho must be (T,Y,X) or (T,Z,Y,X)")
    residual = drho_dt + divergence
    return {"drho_dt": drho_dt, "div_rho_v": divergence, "residual": residual,
            "residual_mean_series": residual.mean(axis=spatial_axes),
            "abs_mean": float(np.mean(np.abs(residual))), "abs_max": float(np.max(np.abs(residual)))}
