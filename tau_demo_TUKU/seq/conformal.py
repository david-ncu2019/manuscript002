"""Split-conformal interval bank on absolute forward errors, bucketed by forecast horizon.
half_width(layer, horizon) = (1-alpha) empirical quantile of past |errors| in the bucket.
Finite-sample marginal coverage holds without distributional assumptions (Vovk et al.).
"""
from collections import defaultdict
import numpy as np

HORIZON_BUCKETS = [(1, 18), (19, 36), (37, 73), (74, 146), (147, 10**9)]  # five-day epochs
MIN_SAMPLES = 20

def bucket_of(horizon: int):
    for lo, hi in HORIZON_BUCKETS:
        if lo <= horizon <= hi:
            return (lo, hi)
    return HORIZON_BUCKETS[-1]

class ConformalBank:
    def __init__(self, alpha: float = 0.10):
        self.alpha = alpha
        self.errors = defaultdict(list)

    def add(self, layer: str, horizon: int, abs_err: float) -> None:
        if np.isfinite(abs_err):
            self.errors[(layer, bucket_of(int(horizon)))].append(float(abs_err))

    def half_width(self, layer: str, horizon: int) -> float:
        errs = self.errors[(layer, bucket_of(int(horizon)))]
        if len(errs) < MIN_SAMPLES:
            return float("nan")  # insufficient data - interval undefined, never guessed
        return float(np.quantile(errs, 1.0 - self.alpha))

    def census(self):
        return {f"{k[0]}|{k[1][0]}-{k[1][1]}": len(v) for k, v in self.errors.items()}
