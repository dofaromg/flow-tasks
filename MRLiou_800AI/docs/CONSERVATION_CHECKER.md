# CFD Conservation Checker

Input fields:

- `rho`: density, shape `(T,Y,X)` or `(T,Z,Y,X)`
- `u, v, [w]`: velocity components
- `t`: strictly increasing time vector
- `dx, dy, [dz]`: regular-grid spacing

Mass equation:

```text
d(rho)/dt + div(rho * V) = 0
```

The package computes the full residual field, global absolute mean/max, and a spatially averaged residual time series. Momentum and energy interfaces are documented in the roadmap and are the next first-class implementation milestone.
