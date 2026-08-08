from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from .conservation import mass_terms

def audit_npz(path: str | Path, out_dir: str | Path) -> dict:
    p, out = Path(path), Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    data = np.load(p, allow_pickle=False)
    required = ["t", "rho", "u", "v", "dx", "dy"]
    missing = [k for k in required if k not in data]
    if missing: raise ValueError(f"missing NPZ keys: {missing}")
    result = mass_terms(data["rho"], data["u"], data["v"], data["t"], float(data["dx"]), float(data["dy"]),
                        data["w"] if "w" in data else None, float(data["dz"]) if "dz" in data else None)
    report = {"input": str(p), "equation": "d(rho)/dt + div(rho*V) = 0",
              "abs_mean": result["abs_mean"], "abs_max": result["abs_max"],
              "residual_mean_series": result["residual_mean_series"].tolist()}
    (out / "mass_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    np.save(out / "mass_residual.npy", result["residual"])
    return report
