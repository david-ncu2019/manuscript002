"""
Direct Ratio Analysis v2 — TUKU Station
f_k(i) = Y_s(i,k) / x_s(i)   (raw sign convention, no negation)

Loads data directly from source files without sign reversal:
  - InSAR: negative = subsidence  (cumulative mm, relative to feather start)
  - MLCW:  negative = subsidence  (baseline-subtracted at 2015-01-16)

Ratio f_k(i) is positive when both signals are negative (subsiding epoch),
which is the physically expected case.

Outputs are saved to direct_ratio_TUKU_v2/ and compared against v1
(direct_ratio_TUKU/) at the end.

Outputs
-------
direct_ratio_TUKU_v2/tuku_direct_ratio_stats_v2.csv   — median, IQR, 5–95 CI per depth
direct_ratio_TUKU_v2/tuku_direct_ratio_all_v2.npy     — full (n_valid, 60) ratio matrix
direct_ratio_TUKU_v2/tuku_direct_ratio_profile_v2.png — depth profile vs Stage 1 w_k
direct_ratio_TUKU_v2/tuku_direct_ratio_heatmap_v2.png — ratio heatmap over time × depth
direct_ratio_TUKU_v2/tuku_v1_vs_v2_comparison.png     — side-by-side v1 vs v2 profiles
"""

import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
MLCW_FILE   = BASE_DIR / 'MLCW_5m_regular' / 'TUKU_5m_grid.csv'
INSAR_FILE  = BASE_DIR / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
OUTPUT_DIR  = BASE_DIR / 'direct_ratio_TUKU_v2'
V1_STATS    = BASE_DIR / 'direct_ratio_TUKU' / 'tuku_direct_ratio_stats.csv'
W_HAT_CSV   = Path(r'D:\112_PROJECT_002\output\stage1_perstation_tuku_test\tuku_B_point_estimate.csv')

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STATION           = 'TUKU'
MLCW_REF_DATE     = datetime(2015, 1, 16)   # same baseline as the loader
DEPTH_GRID        = np.arange(0, 300, 5, dtype=float)   # [0, 5, ..., 295]
N_DEPTHS          = 60
ACTIVE_DEPTH_COLS = [f'depth_{int(d):03d}m' for d in DEPTH_GRID]

logger.info("=" * 70)
logger.info(f"DIRECT RATIO ANALYSIS v2  —  {STATION}  (raw sign, no negation)")
logger.info("=" * 70)

# ── 1. Load InSAR ─────────────────────────────────────────────────────────────
logger.info("\n[1/5] Loading InSAR feather...")
df_insar = pd.read_feather(INSAR_FILE)
tuku_row  = df_insar[df_insar['Ename'] == STATION]
if len(tuku_row) == 0:
    raise ValueError(f"{STATION} not found in feather")

d_cols      = sorted([c for c in df_insar.columns if c.startswith('D')])
insar_dates = np.array([datetime.strptime(c[1:], '%Y%m%d') for c in d_cols])
insar_vals  = tuku_row[d_cols].values.flatten() * 1000.0   # m → mm, raw sign

logger.info(f"  {len(insar_dates)} InSAR epochs  "
            f"({insar_dates[0].date()} to {insar_dates[-1].date()})")
logger.info(f"  InSAR range: [{insar_vals.min():.2f}, {insar_vals.max():.2f}] mm  "
            f"(negative = subsidence)")

# Build date → value lookup for InSAR (YYYYMMDD integer key)
insar_lookup = {
    d.year * 10000 + d.month * 100 + d.day: v
    for d, v in zip(insar_dates, insar_vals)
}

# ── 2. Load MLCW ──────────────────────────────────────────────────────────────
logger.info("\n[2/5] Loading MLCW CSV and subtracting 2015-01-16 baseline...")
df_mlcw     = pd.read_csv(MLCW_FILE, parse_dates=['datetime'])
mlcw_dates  = pd.to_datetime(df_mlcw['datetime'].values)
mlcw_yyyymmdd = np.array([
    d.year * 10000 + d.month * 100 + d.day for d in mlcw_dates
])
mlcw_date_idx = {v: i for i, v in enumerate(mlcw_yyyymmdd)}

# Baseline subtraction: subtract value at MLCW_REF_DATE
ref_key = MLCW_REF_DATE.year * 10000 + MLCW_REF_DATE.month * 100 + MLCW_REF_DATE.day
ref_row = mlcw_date_idx.get(ref_key)
if ref_row is None:
    logger.warning(f"  Reference date {MLCW_REF_DATE.date()} not found — using zeros")
    ref_vals = np.zeros(N_DEPTHS)
else:
    ref_vals = df_mlcw[ACTIVE_DEPTH_COLS].iloc[ref_row].values.astype(float)
    logger.info(f"  Reference epoch {MLCW_REF_DATE.date()} found at row {ref_row}")

logger.info(f"  MLCW spans: {mlcw_dates.min().date()} to {mlcw_dates.max().date()}")

# ── 3. Align and compute ratios ───────────────────────────────────────────────
logger.info("\n[3/5] Aligning InSAR and MLCW by date and computing ratios...")

matched_dates   = []
insar_matched   = []
mlcw_matched    = []

for d, v_insar in zip(insar_dates, insar_vals):
    key = d.year * 10000 + d.month * 100 + d.day
    m_idx = mlcw_date_idx.get(key)
    if m_idx is None:
        continue   # no MLCW match for this InSAR epoch
    mlcw_row = df_mlcw[ACTIVE_DEPTH_COLS].iloc[m_idx].values.astype(float) - ref_vals
    if np.any(np.isnan(mlcw_row)) or np.isnan(v_insar):
        continue   # skip NaN rows
    matched_dates.append(d)
    insar_matched.append(v_insar)
    mlcw_matched.append(mlcw_row)

X_valid     = np.array(insar_matched)              # (n_valid,)  negative = subsidence
Y_valid     = np.array(mlcw_matched)               # (n_valid, 60)
dates_valid = np.array(matched_dates)
n_valid     = len(X_valid)

logger.info(f"  Matched epochs: {n_valid}")
logger.info(f"  InSAR range:  [{X_valid.min():.2f}, {X_valid.max():.2f}] mm")
logger.info(f"  MLCW range:   [{Y_valid.min():.2f}, {Y_valid.max():.2f}] mm")

# ── 4. Ratio matrix ───────────────────────────────────────────────────────────
with np.errstate(divide='ignore', invalid='ignore'):
    R = Y_valid / X_valid[:, None]   # (n_valid, 60); both negative → ratio positive

n_inf = np.sum(~np.isfinite(R))
R = np.where(np.isfinite(R), R, np.nan)

logger.info(f"\n  Ratio matrix shape: {R.shape}")
logger.info(f"  Non-finite values:  {n_inf}")
logger.info(f"  Ratio range (finite): [{np.nanmin(R):.4f}, {np.nanmax(R):.4f}]")

# ── 5. Summary statistics per depth ──────────────────────────────────────────
logger.info("\n[4/5] Computing summary statistics...")

f_median = np.nanmedian(R,              axis=0)
f_q25    = np.nanpercentile(R,  25,    axis=0)
f_q75    = np.nanpercentile(R,  75,    axis=0)
f_p05    = np.nanpercentile(R,   5,    axis=0)
f_p95    = np.nanpercentile(R,  95,    axis=0)
n_finite = np.sum(np.isfinite(R),      axis=0)

logger.info(f"  Median f_k range: [{f_median.min():.5f}, {f_median.max():.5f}]")
logger.info(f"  Sum of medians:   {f_median.sum():.4f}  (compare: alpha_s ≈ 0.5580)")

# ── Save CSV ──────────────────────────────────────────────────────────────────
df_stats = pd.DataFrame({
    'depth_m':         DEPTH_GRID,
    'f_median':        f_median,
    'f_q25':           f_q25,
    'f_q75':           f_q75,
    'f_p05':           f_p05,
    'f_p95':           f_p95,
    'n_finite_epochs': n_finite,
})
csv_path = OUTPUT_DIR / 'tuku_direct_ratio_stats_v2.csv'
df_stats.to_csv(csv_path, index=False)
logger.info(f"  Saved: {csv_path}")

npy_path = OUTPUT_DIR / 'tuku_direct_ratio_all_v2.npy'
np.save(npy_path, R)
logger.info(f"  Saved: {npy_path}  shape={R.shape}")

# ── 6. Load Stage 1 w_k ───────────────────────────────────────────────────────
logger.info("\n[5/5] Generating figures...")

w_hat = None
if W_HAT_CSV.exists():
    df_w  = pd.read_csv(W_HAT_CSV)
    w_hat = df_w['B_point'].values
    logger.info(f"  Loaded Stage 1 w_k from {W_HAT_CSV.name}")

v1_stats = None
if V1_STATS.exists():
    v1_stats = pd.read_csv(V1_STATS)
    logger.info(f"  Loaded v1 stats from {V1_STATS.name}")

# ── Figure 1: Depth profile (v2) ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(6, 10))

ax.fill_betweenx(DEPTH_GRID, f_p05, f_p95,
                 color='steelblue', alpha=0.15, label='5–95th pct')
ax.fill_betweenx(DEPTH_GRID, f_q25, f_q75,
                 color='steelblue', alpha=0.35, label='IQR (Q25–Q75)')
ax.plot(f_median, DEPTH_GRID, color='steelblue', lw=2, label='Median $f_k$ (v2)')

if w_hat is not None:
    ax.plot(w_hat, DEPTH_GRID, color='darkorange', lw=1.5,
            linestyle='--', label='Stage 1 $\\hat{w}_k$')

ax.set_xlabel('Fraction of InSAR signal (dimensionless)', fontsize=11)
ax.set_ylabel('Depth (m)', fontsize=11)
ax.set_title(f'TUKU — Direct ratio $f_k$ (v2, raw sign)\n'
             f'n = {n_valid} valid epochs', fontsize=11)
ax.invert_yaxis()
ax.set_ylim(295, 0)
ax.legend(fontsize=9, loc='lower right')
ax.grid(True, alpha=0.3)
ax.axvline(0, color='k', lw=0.5, ls=':')
ax.text(0.98, 0.02,
        f'Median sum = {f_median.sum():.4f}\n$\\alpha_s$ = 0.5580',
        transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

fig.tight_layout()
profile_path = OUTPUT_DIR / 'tuku_direct_ratio_profile_v2.png'
fig.savefig(profile_path, dpi=150, bbox_inches='tight')
plt.close(fig)
logger.info(f"  Saved: {profile_path}")

# ── Figure 2: Heatmap (v2) ────────────────────────────────────────────────────
vmax = float(np.nanpercentile(np.abs(R), 98))
vmin = -vmax

fig, ax = plt.subplots(figsize=(14, 6))
depth_edges = np.append(DEPTH_GRID - 2.5, DEPTH_GRID[-1] + 2.5)
epoch_edges = np.arange(n_valid + 1)

pcm = ax.pcolormesh(depth_edges, epoch_edges, R,
                    cmap='RdBu_r', vmin=vmin, vmax=vmax, shading='flat')

year_ticks, year_labels, current_year = [], [], None
for idx, d in enumerate(dates_valid):
    yr = d.year
    if yr != current_year:
        year_ticks.append(idx)
        year_labels.append(str(yr))
        current_year = yr

ax.set_yticks(year_ticks)
ax.set_yticklabels(year_labels, fontsize=8)
ax.set_xlabel('Depth (m)', fontsize=11)
ax.set_ylabel('Epoch (year)', fontsize=11)
ax.set_title(f'TUKU — Ratio heatmap $f_k(i)$ (v2, raw sign)\n'
             f'Colour clipped to ±{vmax:.3f}  (98th pct of |R|)', fontsize=11)

cbar = fig.colorbar(pcm, ax=ax, shrink=0.85, pad=0.01)
cbar.set_label('$f_k(i)$', fontsize=9)

fig.tight_layout()
heatmap_path = OUTPUT_DIR / 'tuku_direct_ratio_heatmap_v2.png'
fig.savefig(heatmap_path, dpi=150, bbox_inches='tight')
plt.close(fig)
logger.info(f"  Saved: {heatmap_path}")

# ── Figure 3: v1 vs v2 side-by-side comparison ───────────────────────────────
if v1_stats is not None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 10), sharey=True)

    for ax, (label, median, q25, q75, p05, p95, color) in zip(axes, [
        ('v1 (negated)',  v1_stats['f_median'].values, v1_stats['f_q25'].values,
         v1_stats['f_q75'].values, v1_stats['f_p05'].values,
         v1_stats['f_p95'].values, 'steelblue'),
        ('v2 (raw sign)', f_median, f_q25, f_q75, f_p05, f_p95, 'seagreen'),
    ]):
        ax.fill_betweenx(DEPTH_GRID, p05, p95,
                         color=color, alpha=0.15, label='5–95th pct')
        ax.fill_betweenx(DEPTH_GRID, q25, q75,
                         color=color, alpha=0.35, label='IQR')
        ax.plot(median, DEPTH_GRID, color=color, lw=2, label=f'Median ({label})')
        if w_hat is not None:
            ax.plot(w_hat, DEPTH_GRID, color='darkorange', lw=1.5,
                    linestyle='--', label='Stage 1 $\\hat{w}_k$')
        ax.axvline(0, color='k', lw=0.5, ls=':')
        ax.set_xlabel('Fraction of InSAR signal', fontsize=10)
        ax.set_title(f'Direct ratio — {label}\nMedian sum = {median.sum():.4f}', fontsize=10)
        ax.legend(fontsize=8, loc='lower right')
        ax.grid(True, alpha=0.3)
        ax.invert_yaxis()
        ax.set_ylim(295, 0)

    axes[0].set_ylabel('Depth (m)', fontsize=11)
    fig.suptitle('TUKU — Direct ratio f_k: v1 (negated) vs v2 (raw sign)\n'
                 'Orange dashed = Stage 1 regularised $\\hat{w}_k$', fontsize=11)
    fig.tight_layout()
    comp_path = OUTPUT_DIR / 'tuku_v1_vs_v2_comparison.png'
    fig.savefig(comp_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"  Saved: {comp_path}")

# ── Console summary ───────────────────────────────────────────────────────────
print(f"\n{'=' * 70}")
print(f"  {STATION}  Direct ratio f_k (v2, raw sign)")
print(f"  n_valid = {n_valid}  |  non-finite ratios = {n_inf}")
print(f"  Median sum = {f_median.sum():.4f}   (alpha_s = 0.5580)")
print(f"{'=' * 70}")
print(f"  {'depth':>6}  {'median':>8}  {'q25':>8}  {'q75':>8}  {'p05':>8}  {'p95':>8}")
print(f"  {'-'*6}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}")
show = list(range(10)) + list(range(50, 60))
for i in show:
    if i == 10:
        print(f"  {'...':>6}")
    print(f"  {int(DEPTH_GRID[i]):>5}m  "
          f"{f_median[i]:>8.5f}  {f_q25[i]:>8.5f}  {f_q75[i]:>8.5f}  "
          f"{f_p05[i]:>8.5f}  {f_p95[i]:>8.5f}")
print(f"{'=' * 70}")

if w_hat is not None:
    from scipy.stats import pearsonr, spearmanr
    valid_both = np.isfinite(f_median) & np.isfinite(w_hat)
    rp, pp = pearsonr( f_median[valid_both], w_hat[valid_both])
    rs, ps = spearmanr(f_median[valid_both], w_hat[valid_both])
    print(f"\n  Correlation with Stage 1 w_k (v2 median vs w_hat):")
    print(f"    Pearson  r = {rp:.4f}  (p = {pp:.2e})")
    print(f"    Spearman r = {rs:.4f}  (p = {ps:.2e})")

if v1_stats is not None:
    v1_med = v1_stats['f_median'].values
    diff   = f_median - v1_med
    print(f"\n  v2 vs v1 median difference (v2 - v1) per depth:")
    print(f"    Max absolute diff: {np.max(np.abs(diff)):.6f}")
    print(f"    Mean diff:         {diff.mean():.6f}")
    print(f"    All identical?:    {np.allclose(f_median, v1_med, atol=1e-8)}")
    print()
