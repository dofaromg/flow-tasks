from __future__ import annotations
import numpy as np

def time_derivative(field: np.ndarray, t: np.ndarray) -> np.ndarray:
    field = np.asarray(field, dtype=float); t = np.asarray(t, dtype=float)
    if field.shape[0] != t.size or t.size < 2 or not np.all(np.diff(t) > 0):
        raise ValueError("time axis must match field[0], contain >=2 points, and be strictly increasing")
    return np.gradient(field, t, axis=0, edge_order=1)

def div2d(ax: np.ndarray, ay: np.ndarray, dx: float, dy: float) -> np.ndarray:
    return np.gradient(ax, dx, axis=-1) + np.gradient(ay, dy, axis=-2)

def div3d(ax: np.ndarray, ay: np.ndarray, az: np.ndarray, dx: float, dy: float, dz: float) -> np.ndarray:
    return (np.gradient(ax, dx, axis=-1) + np.gradient(ay, dy, axis=-2) +
            np.gradient(az, dz, axis=-3))
