import pandas as pd
import numpy as np

# Load all three data sources for TUKU
raw = pd.read_csv('data/mlcw/raw_timeseries/TUKU_ringbyring.csv', parse_dates=[0], index_col=0)
det = pd.read_csv('data/mlcw/modeled_nojump/detrended/TUKU_ringbyring.csv', parse_dates=[0], index_col=0)
grp = pd.read_csv('data/mlcw/group_byLayer_modeled/TUKU_modeled_grouped.csv', parse_dates=[0], index_col=0)

def linear_detrend(y):
    t = np.arange(len(y), dtype=float)
    mask = ~np.isnan(y)
    if mask.sum() < 3:
        return y.copy()
    A = np.column_stack([np.ones(len(y)), t])
    theta, _, _, _ = np.linalg.lstsq(A[mask], y[mask], rcond=None)
    return y - A @ theta

def lagged_ccf(a, b, max_lag, min_common=20):
    """Find lag tau that maximizes positive Pearson r between a and b.
    a is shifted relative to b: at lag tau, we correlate a[tau:] with b[:-tau] (a leads b)
    at negative tau, b leads a.
    Returns: (best_r, best_lag, n_common_pairs)
    """
    best_r = -1
    best_lag = 0
    best_n = 0
    for tau in range(-max_lag, max_lag + 1):
        if tau >= 0:
            a_shifted = a[tau:]
            b_shifted = b[:len(b)-tau]
        else:
            t = -tau
            a_shifted = a[:len(a)-t]
            b_shifted = b[t:]
        mask = ~np.isnan(a_shifted) & ~np.isnan(b_shifted)
        n = mask.sum()
        if n < min_common:
            continue
        r = np.corrcoef(a_shifted[mask], b_shifted[mask])[0, 1]
        if r > best_r:
            best_r = r
            best_lag = tau
            best_n = n
    return best_r, best_lag, best_n

# Test on detrended data (most interesting -- seasonal signal, no trend)
# Pick 3 representative ring pairs
ring_cols_det = sorted([float(c) for c in det.columns if c.replace('.','',1).replace('.','',1).isdigit()], reverse=False)
ring_cols_det_str = [str(c) for c in ring_cols_det]

# Detrend all
det_d = pd.DataFrame(index=det.index)
for col in ring_cols_det_str:
    det_d[col] = linear_detrend(det[col].values)

print("=== DETRENDED DATA (1572 rows, ~5-day) ===")
print(f"Time range: {det.index[0]} to {det.index[-1]}")
print(f"Sampling interval: ~{(det.index[1] - det.index[0]).days} days")
print(f"Max lag in days for lag=20: {20 * 5} days")
print(f"Max lag in days for lag=60: {60 * 5} days")

# Test: shallow ring (8.775) vs mid (50.306), mid vs deep (252.265)
pairs_to_test = [
    ('8.775', '50.306', 'shallow vs mid-aquifer'),
    ('50.306', '252.265', 'F2 vs deep F3'),
    ('8.775', '252.265', 'shallow vs deep'),
    ('117.442', '252.265', 'mid-F2 vs deep-F3'),
]

print("\n--- Lagged CCF (max_lag=30, ~150 days) ---")
for a_col, b_col, desc in pairs_to_test:
    a = det_d[a_col].values.astype(float)
    b = det_d[b_col].values.astype(float)
    best_r, best_lag, n = lagged_ccf(a, b, max_lag=30)
    print(f"  {desc}: best_r={best_r:.4f} at lag={best_lag} ({best_lag*5:+d} days), n={n}")

# Now test with max_lag=60 (~300 days)
print("\n--- Lagged CCF (max_lag=60, ~300 days) ---")
for a_col, b_col, desc in pairs_to_test:
    a = det_d[a_col].values.astype(float)
    b = det_d[b_col].values.astype(float)
    best_r, best_lag, n = lagged_ccf(a, b, max_lag=60)
    print(f"  {desc}: best_r={best_r:.4f} at lag={best_lag} ({best_lag*5:+d} days), n={n}")

# Test on RAW data (264 rows, ~monthly)
print("\n\n=== RAW DATA (264 rows, ~monthly) ===")
ring_cols_raw = sorted([float(c) for c in raw.columns if c.replace('.','',1).replace('.','',1).isdigit()], reverse=False)
ring_cols_raw_str = [str(c) for c in ring_cols_raw]
raw_d = pd.DataFrame(index=raw.index)
for col in ring_cols_raw_str:
    raw_d[col] = linear_detrend(raw[col].values)

print(f"Time range: {raw.index[0]} to {raw.index[-1]}")
print(f"Avg sampling interval: ~{(raw.index[-1] - raw.index[0]).days / len(raw):.0f} days")
print(f"Max lag in days for lag=12: ~{12 * 30} days")

pairs_raw = [
    ('8.775', '50.306', 'shallow vs mid-aquifer'),
    ('50.306', '252.265', 'F2 vs deep F3'),
]
print("\n--- Lagged CCF (max_lag=12, ~12 months) ---")
for a_col, b_col, desc in pairs_raw:
    a = raw_d[a_col].values.astype(float)
    b = raw_d[b_col].values.astype(float)
    best_r, best_lag, n = lagged_ccf(a, b, max_lag=12)
    print(f"  {desc}: best_r={best_r:.4f} at lag={best_lag} ({best_lag:+d} steps), n={n}")

# Test on GROUPED data (6 layers, monthly)
print("\n\n=== GROUPED DATA (6 layers, 264 rows) ===")
grp_d = pd.DataFrame(index=grp.index)
for col in grp.columns:
    grp_d[col] = linear_detrend(grp[col].values)

for a_col in grp.columns:
    for b_col in grp.columns:
        if a_col < b_col:
            a = grp_d[a_col].values.astype(float)
            b = grp_d[b_col].values.astype(float)
            best_r, best_lag, n = lagged_ccf(a, b, max_lag=12)
            print(f"  {a_col} vs {b_col}: best_r={best_r:.4f} at lag={best_lag} ({best_lag:+d} steps), n={n}")
