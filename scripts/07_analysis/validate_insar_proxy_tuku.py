"""
In-Sample Validation: Can InSAR Proxy Subsurface Compaction? (TUKU)

Answers two physical questions:
  Q1: How well does f̄_k × x(i) reproduce measured MLCW compaction at each depth?
  Q2: How large is the bias/RMSE, and does the P05–P95 band bracket the truth?

Method:
  Ŷ(i, k) = f̄_k × x(i)   — calibrated on the full record (in-sample)
  residual(i, k) = Y(i, k) − Ŷ(i, k)

Outputs → direct_ratio_MLCW_InSAR/TUKU/validation/
    TUKU_validation_rmse_profile.png
    TUKU_validation_residual_heatmap.png
    TUKU_validation_scatter_selected.png
    TUKU_validation_total_timeseries.png
    TUKU_validation_coverage.png
    TUKU_validation_stats.csv
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2')
MLCW_DIR    = BASE_DIR / 'MLCW_5m_regular'
INSAR_FILE  = BASE_DIR / 'InSAR_timeries' / 'mlcw_interp_insar_IDW_extend.feather'
RATIO_DIR   = BASE_DIR / 'direct_ratio_MLCW_InSAR' / 'TUKU'
OUT_DIR     = RATIO_DIR / 'validation'
OUT_DIR.mkdir(parents=True, exist_ok=True)

STATION       = 'TUKU'
MLCW_REF_DATE = datetime(2015, 1, 16)
DEPTH_GRID    = np.arange(0, 300, 5, dtype=float)   # [0, 5, …, 295]
N_DEPTHS      = 60
DEPTH_COLS    = [f'depth_{int(d):03d}m' for d in DEPTH_GRID]

# ── Load ratio stats (f̄_k, P05, P95) ─────────────────────────────────────────
stats_df = pd.read_csv(RATIO_DIR / f'{STATION}_direct_ratio_stats.csv')
f_median = stats_df['f_median'].values   # (60,)
f_p05    = stats_df['f_p05'].values
f_p95    = stats_df['f_p95'].values

# ── Load InSAR feather ─────────────────────────────────────────────────────────
print('Loading InSAR feather...')
df_insar    = pd.read_feather(INSAR_FILE)
d_cols      = sorted([c for c in df_insar.columns if c.startswith('D')])
insar_dates = [datetime.strptime(c[1:], '%Y%m%d') for c in d_cols]

tuku_row    = df_insar[df_insar['Ename'] == STATION].iloc[0]
insar_vals  = tuku_row[d_cols].values.astype(float) * 1000.0   # m → mm
insar_lookup = {
    d.year * 10000 + d.month * 100 + d.day: v
    for d, v in zip(insar_dates, insar_vals)
}

# ── Load MLCW ─────────────────────────────────────────────────────────────────
print('Loading MLCW...')
mlcw_file   = MLCW_DIR / f'{STATION}_5m_grid.csv'
df_mlcw     = pd.read_csv(mlcw_file, parse_dates=['datetime'])
mlcw_dates  = pd.to_datetime(df_mlcw['datetime'].values)
mlcw_yyyymmdd = np.array([
    d.year * 10000 + d.month * 100 + d.day for d in mlcw_dates
])
mlcw_date_idx = {v: i for i, v in enumerate(mlcw_yyyymmdd)}

ref_key = (MLCW_REF_DATE.year * 10000
           + MLCW_REF_DATE.month * 100
           + MLCW_REF_DATE.day)
ref_row  = mlcw_date_idx.get(ref_key)
ref_vals = (df_mlcw[DEPTH_COLS].iloc[ref_row].values.astype(float)
            if ref_row is not None else np.zeros(N_DEPTHS))

# ── Date alignment ─────────────────────────────────────────────────────────────
print('Aligning dates...')
matched_insar, matched_mlcw, matched_dates = [], [], []
for d in insar_dates:
    key     = d.year * 10000 + d.month * 100 + d.day
    v_insar = insar_lookup.get(key)
    m_idx   = mlcw_date_idx.get(key)
    if v_insar is None or m_idx is None:
        continue
    mlcw_row = df_mlcw[DEPTH_COLS].iloc[m_idx].values.astype(float) - ref_vals
    if np.isnan(v_insar) or np.any(np.isnan(mlcw_row)):
        continue
    matched_insar.append(v_insar)
    matched_mlcw.append(mlcw_row)
    matched_dates.append(d)

X_valid     = np.array(matched_insar)    # (n, )   InSAR mm
Y_valid     = np.array(matched_mlcw)    # (n, 60) MLCW mm
dates_valid = np.array(matched_dates)
n_valid     = len(X_valid)
print(f'  Matched {n_valid} epochs')

# ── Prediction and residuals ───────────────────────────────────────────────────
Y_hat = f_median[None, :] * X_valid[:, None]   # (n, 60)
resid = Y_valid - Y_hat                          # (n, 60)

# Per-depth statistics
rmse_per_depth = np.sqrt(np.mean(resid ** 2, axis=0))
bias_per_depth = np.mean(resid, axis=0)

ss_res = np.sum(resid ** 2, axis=0)
ss_tot = np.sum((Y_valid - Y_valid.mean(axis=0)) ** 2, axis=0)
r2_per_depth = np.where(ss_tot > 0, 1.0 - ss_res / ss_tot, np.nan)

# Band coverage — need to handle sign of X (band may flip if X < 0)
Y_band_lo = np.where(
    X_valid[:, None] >= 0,
    f_p05[None, :] * X_valid[:, None],
    f_p95[None, :] * X_valid[:, None],
)
Y_band_hi = np.where(
    X_valid[:, None] >= 0,
    f_p95[None, :] * X_valid[:, None],
    f_p05[None, :] * X_valid[:, None],
)
coverage = np.mean((Y_valid >= Y_band_lo) & (Y_valid <= Y_band_hi), axis=0)

# Total column compaction per epoch
Y_total     = Y_valid.sum(axis=1)
Y_hat_total = Y_hat.sum(axis=1)
band_lo_total = Y_band_lo.sum(axis=1)
band_hi_total = Y_band_hi.sum(axis=1)

# ── Save CSV ───────────────────────────────────────────────────────────────────
df_val = pd.DataFrame({
    'depth_m':          DEPTH_GRID,
    'rmse_mm':          rmse_per_depth,
    'bias_mm':          bias_per_depth,
    'r2':               r2_per_depth,
    'coverage_p05_p95': coverage,
    'n_epochs':         n_valid,
})
df_val.to_csv(OUT_DIR / f'{STATION}_validation_stats.csv', index=False)
print('Saved validation_stats.csv')


# ── Helper: year tick positions ────────────────────────────────────────────────
def year_ticks(dates):
    ticks, labels, cur = [], [], None
    for idx, d in enumerate(dates):
        yr = d.year
        if yr != cur:
            ticks.append(idx)
            labels.append(str(yr))
            cur = yr
    return ticks, labels


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 1: RMSE and R² depth profile
# ═══════════════════════════════════════════════════════════════════════════════
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 10), sharey=True)

ax1.plot(rmse_per_depth, DEPTH_GRID, color='steelblue', lw=2)
ax1.axvline(0, color='k', lw=0.6, ls=':')
ax1.set_xlabel('RMSE (mm)', fontsize=11)
ax1.set_ylabel('Depth (m)', fontsize=11)
ax1.set_title('In-sample RMSE\nHow closely does InSAR × f̄_k\ntrack actual MLCW compaction?',
              fontsize=10)
ax1.invert_yaxis()
ax1.set_ylim(295, 0)
ax1.grid(True, alpha=0.3)

ax2.plot(r2_per_depth, DEPTH_GRID, color='darkorange', lw=2)
ax2.axvline(1, color='k', lw=0.6, ls='--', alpha=0.4)
ax2.axvline(0, color='k', lw=0.6, ls=':')
ax2.set_xlabel('R²', fontsize=11)
ax2.set_title('In-sample R²\nFraction of MLCW variance\nexplained by InSAR proxy',
              fontsize=10)
ax2.grid(True, alpha=0.3)

fig.suptitle(f'{STATION} — In-sample validation  (n = {n_valid} epochs)',
             fontsize=12, fontweight='bold')
fig.tight_layout()
fig.savefig(OUT_DIR / f'{STATION}_validation_rmse_profile.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved validation_rmse_profile.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 2: Residual heatmap  Y − Ŷ
# ═══════════════════════════════════════════════════════════════════════════════
abs_resid = np.abs(resid[np.isfinite(resid)])
vmax = float(np.percentile(abs_resid, 98)) if len(abs_resid) > 0 else 1.0
vmin = -vmax

fig, ax = plt.subplots(figsize=(14, 6))
depth_edges = np.append(DEPTH_GRID - 2.5, DEPTH_GRID[-1] + 2.5)
epoch_edges = np.arange(n_valid + 1)

pcm = ax.pcolormesh(depth_edges, epoch_edges, resid,
                    cmap='RdBu_r', vmin=vmin, vmax=vmax, shading='flat')

yticks, ylabels = year_ticks(dates_valid)
ax.set_yticks(yticks)
ax.set_yticklabels(ylabels, fontsize=8)
ax.set_xlabel('Depth (m)', fontsize=11)
ax.set_ylabel('Epoch (year)', fontsize=11)
ax.set_title(f'{STATION} — Residual heatmap  Y − Ŷ\n'
             f'Where does InSAR × f̄_k over- or under-predict MLCW compaction?\n'
             f'Colour clipped to ±{vmax:.2f} mm  (98th pct of |residual|)',
             fontsize=10)

cbar = fig.colorbar(pcm, ax=ax, shrink=0.85, pad=0.01)
cbar.set_label('Residual (mm)', fontsize=9)

fig.tight_layout()
fig.savefig(OUT_DIR / f'{STATION}_validation_residual_heatmap.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved validation_residual_heatmap.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 3: Scatter at 4 selected depths
# ═══════════════════════════════════════════════════════════════════════════════
selected_depths = [50.0, 100.0, 150.0, 250.0]
selected_labels = ['50 m (F2 aquifer top)', '100 m (F2 bottom)',
                   '150 m (F3 top)', '250 m (F4)']

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes = axes.flatten()

for ax, depth, label in zip(axes, selected_depths, selected_labels):
    k = int(depth / 5)   # index into 60-depth array
    y_obs  = Y_valid[:, k]
    y_pred = Y_hat[:, k]

    r2_k   = r2_per_depth[k]
    rmse_k = rmse_per_depth[k]

    lim_vals = np.concatenate([y_obs, y_pred])
    lim = [np.nanmin(lim_vals), np.nanmax(lim_vals)]
    margin = (lim[1] - lim[0]) * 0.05
    lim = [lim[0] - margin, lim[1] + margin]

    ax.scatter(y_pred, y_obs, s=6, alpha=0.5, color='steelblue')
    ax.plot(lim, lim, 'k--', lw=1, label='1:1 line')
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel('Predicted Ŷ (mm)', fontsize=10)
    ax.set_ylabel('Observed Y (mm)', fontsize=10)
    ax.set_title(f'Depth {label}\nR² = {r2_k:.3f}   RMSE = {rmse_k:.2f} mm', fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal', adjustable='box')

fig.suptitle(f'{STATION} — Observed vs. predicted MLCW compaction at selected depths\n'
             f'Does InSAR × f̄_k recover the right magnitude?',
             fontsize=11, fontweight='bold')
fig.tight_layout()
fig.savefig(OUT_DIR / f'{STATION}_validation_scatter_selected.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved validation_scatter_selected.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 4: Total column compaction time series
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(14, 5))

date_nums = [d for d in dates_valid]

ax.fill_between(date_nums, band_lo_total, band_hi_total,
                color='steelblue', alpha=0.20, label='P05–P95 band (total)')
ax.plot(date_nums, Y_total,     color='k',          lw=1.5, label='Actual MLCW total (mm)')
ax.plot(date_nums, Y_hat_total, color='steelblue',  lw=1.5, linestyle='--',
        label='Predicted Ŷ_total = Σ f̄_k × x(i)')

ax.axhline(0, color='k', lw=0.5, ls=':')
ax.set_xlabel('Date', fontsize=11)
ax.set_ylabel('Total column compaction (mm)', fontsize=11)
ax.set_title(f'{STATION} — Actual vs. predicted total column compaction\n'
             f'How well does InSAR track the full-depth integrated subsidence signal?\n'
             f'Shaded band = propagated P05–P95 uncertainty',
             fontsize=10)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

fig.tight_layout()
fig.savefig(OUT_DIR / f'{STATION}_validation_total_timeseries.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved validation_total_timeseries.png')


# ═══════════════════════════════════════════════════════════════════════════════
# Figure 5: Band coverage per depth
# ═══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 9))

bar_width = 4.0
ax.barh(DEPTH_GRID, coverage, height=bar_width, color='steelblue', alpha=0.7)
ax.axvline(0.90, color='red', lw=1.5, ls='--', label='90% target (P05–P95)')
ax.axvline(1.00, color='k',   lw=0.6, ls=':', alpha=0.5)

ax.set_xlabel('Coverage fraction', fontsize=11)
ax.set_ylabel('Depth (m)', fontsize=11)
ax.set_title(f'{STATION} — P05–P95 band coverage per depth\n'
             f'Does the uncertainty band bracket the measured MLCW values?\n'
             f'Expected ~90% for a well-calibrated 5–95th percentile band',
             fontsize=10)
ax.set_xlim(0, 1.05)
ax.invert_yaxis()
ax.set_ylim(295, 0)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis='x')

mean_cov = float(np.mean(coverage))
ax.text(0.98, 0.02,
        f'Mean coverage = {mean_cov:.3f}',
        transform=ax.transAxes, fontsize=9, ha='right', va='bottom',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

fig.tight_layout()
fig.savefig(OUT_DIR / f'{STATION}_validation_coverage.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print('Saved validation_coverage.png')


# ── Terminal summary ───────────────────────────────────────────────────────────
print(f'\n{"=" * 65}')
print(f'  {STATION} IN-SAMPLE VALIDATION SUMMARY')
print(f'{"=" * 65}')
print(f'  Valid epochs:      {n_valid}')
print(f'  Mean RMSE:         {float(np.mean(rmse_per_depth)):.3f} mm')
print(f'  Mean |bias|:       {float(np.mean(np.abs(bias_per_depth))):.3f} mm')
print(f'  Mean R²:           {float(np.nanmean(r2_per_depth)):.3f}')
print(f'  Mean coverage:     {mean_cov:.3f}  (target 0.90)')
print(f'  Worst-RMSE depth:  {DEPTH_GRID[np.argmax(rmse_per_depth)]:.0f} m')
print(f'  Best-R²  depth:    {DEPTH_GRID[np.nanargmax(r2_per_depth)]:.0f} m')
print(f'  Output dir:        {OUT_DIR}')
print(f'{"=" * 65}')
