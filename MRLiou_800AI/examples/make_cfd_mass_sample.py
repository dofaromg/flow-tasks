from pathlib import Path
import numpy as np
T, Y, X = 6, 12, 16
t = np.linspace(0, 1, T)
rho = np.ones((T, Y, X)); u = np.zeros_like(rho); v = np.zeros_like(rho)
out = Path(__file__).with_name("cfd_mass_sample.npz")
np.savez(out, t=t, rho=rho, u=u, v=v, dx=0.1, dy=0.1)
print(out)
