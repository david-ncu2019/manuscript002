"""FrozenLayerModel — fixed two-regime structure (Assumption A2), per-layer.
b_k(t) = c + a*d(t) + S_ke*u(t-tau) + S_kv*V(t-tau) + beta(live bias)
Signs: b negative = compaction; u = H - H_ref (never negated); V = min(0, cummin(H) - h_c) <= 0.
Units: b, d in mm; u, V in m; S_ke, S_kv in mm/m; a dimensionless.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import lsq_linear

@dataclass
class FrozenLayerModel:
    layer: str
    a: float = 0.0
    c: float = 0.0
    S_ke: float = 0.0
    S_kv: float = 0.0
    tau: int = 0
    use_u: bool = True
    use_V: bool = True
    beta: float = 0.0          # the only live parameter after freezing
    h_c: float = float("nan")

    def design(self, d, u_lag, V_lag):
        cols = [np.ones_like(d), d]
        if self.use_u:
            cols.append(u_lag)
        if self.use_V:
            cols.append(V_lag)
        return np.column_stack(cols)

    def fit(self, d, u_lag, V_lag, b):
        m = np.isfinite(b) & np.isfinite(d)
        if self.use_u:
            m &= np.isfinite(u_lag)
        if self.use_V:
            m &= np.isfinite(V_lag)
        if m.sum() < 30:
            raise ValueError(f"{self.layer}: insufficient data - fit is undefined (n={m.sum()})")
        X, y = self.design(d, u_lag, V_lag)[m], b[m]
        lo = [-np.inf, 0.0] + ([0.0] if self.use_u else []) + ([0.0] if self.use_V else [])
        res = lsq_linear(X, y, bounds=(lo, [np.inf] * X.shape[1]))
        coef = list(res.x)
        self.c, self.a = coef[0], coef[1]
        i = 2
        if self.use_u:
            self.S_ke = coef[i]; i += 1
        if self.use_V:
            self.S_kv = coef[i]
        return self

    def predict(self, d, u_lag, V_lag):
        y = self.c + self.beta + self.a * d
        if self.use_u:
            y = y + self.S_ke * u_lag
        if self.use_V:
            y = y + self.S_kv * V_lag
        return y

    def assimilate(self, innovation_mm: float):
        """Visit update (Assumption A6): hard level reset."""
        self.beta += float(innovation_mm)
