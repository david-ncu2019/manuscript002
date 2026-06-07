"""
ARX Method 7 — Visualization Suite
Produces 5 figures saved to arx_method7/figures/
"""
import os, glob
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import TwoSlopeNorm
import pyarrow.feather as feather

# ── paths ──────────────────────────────────────────────────────────────────────
BASE    = r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2'
ARX_DIR = os.path.join(BASE, 'arx_method7')
FIG_DIR = os.path.join(ARX_DIR, 'figures')
os.makedirs(FIG_DIR, exist_ok=True)

MLCW_DIR   = os.path.join(BASE, 'MLCW_5m_regular')
INSAR_FILE = os.path.join(BASE, 'InSAR_timeries', 'mlcw_interp_insar_IDW_extend.feather')

# ── style ───────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.labelsize': 10, 'axes.titlesize': 11,
    'xtick.labelsize': 9,  'ytick.labelsize': 9,
    'figure.dpi': 150,
})
ACTIVE_COLOR   = '#1a6bb5'
BASELINE_COLOR = '#d94f3d'
PANEL_BG       = '#f7f7f7'

# ── load summary ────────────────────────────────────────────────────────────────
summary = pd.read_csv(os.path.join(ARX_DIR, 'arx_allstations_summary.csv'))
active  = summary[summary['arx_recommended']].copy().reset_index(drop=True)
active  = active.sort_values('impr_pct', ascending=True).reset_index(drop=True)

# ── load npz params ─────────────────────────────────────────────────────────────
npz      = np.load(os.path.join(ARX_DIR, 'arx_allstations_params.npz'), allow_pickle=True)
stations = [str(s) for s in npz['stations']]
phi_all  = npz['phi']   # (39, 60)
depths   = npz['depths']  # (60,)

# ══════════════════════════════════════════════════════════════════════════════
# Figure 1 — Station improvement bar chart (active 19 stations)
# ══════════════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(10, 5.5))
y = np.arange(len(active))
bar_arx  = ax.barh(y, active['rmse_arx_med_mm'],  color=ACTIVE_COLOR,   height=0.5, label='ARX (median RMSE)')
bar_base = ax.barh(y, active['rmse_base_med_mm'], color=BASELINE_COLOR, height=0.5,
                   alpha=0.35, label='Static baseline (median RMSE)')

# improvement % annotation
for i, row in active.iterrows():
    ax.text(row['rmse_base_med_mm'] + 0.15, i, f"{row['impr_pct']:.1f}%",
            va='center', ha='left', fontsize=8.5, color='#333333')

ax.set_yticks(y)
ax.set_yticklabels(active['station'], fontsize=9)
ax.set_xlabel('Median per-depth RMSE over 2022–2025 hold-out (mm)')
ax.set_title('ARX vs. Static Baseline — Walk-Forward RMSE\n19 Active MLCW Stations', pad=10)
ax.legend(loc='lower right', fontsize=9)
ax.set_xlim(0, active['rmse_base_med_mm'].max() * 1.18)
ax.axvline(0, color='k', lw=0.5)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig1_station_improvement.png'), bbox_inches='tight')
plt.close(fig)
print('Fig 1 saved.')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 2 — RMSE vs depth heatmap for all 19 active stations (ARX minus baseline)
# ══════════════════════════════════════════════════════════════════════════════
active_stations_sorted = summary[summary['arx_recommended']].sort_values('impr_pct', ascending=False)['station'].tolist()

rmse_arx_mat  = np.full((len(active_stations_sorted), 60), np.nan)
rmse_base_mat = np.full((len(active_stations_sorted), 60), np.nan)

for i, sta in enumerate(active_stations_sorted):
    path = os.path.join(ARX_DIR, f'{sta}_arx_walkforward_rmse.csv')
    if not os.path.exists(path):
        continue
    df = pd.read_csv(path)
    # mean across folds (2022–2025)
    arx_cols  = [c for c in df.columns if c.startswith('rmse_arx_')]
    base_cols = [c for c in df.columns if c.startswith('rmse_base_')]
    rmse_arx_mat[i]  = df[arx_cols].mean(axis=1).values
    rmse_base_mat[i] = df[base_cols].mean(axis=1).values

improvement_mat = 100 * (rmse_base_mat - rmse_arx_mat) / rmse_base_mat  # % improvement

fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)
dep_arr = np.linspace(0, 295, 60)

# --- left: ARX RMSE ---
im1 = axes[0].imshow(rmse_arx_mat, aspect='auto', origin='upper',
                     extent=[dep_arr[0], dep_arr[-1], len(active_stations_sorted)-0.5, -0.5],
                     cmap='YlOrRd', vmin=0, vmax=2.0)
axes[0].set_yticks(np.arange(len(active_stations_sorted)))
axes[0].set_yticklabels(active_stations_sorted, fontsize=8)
axes[0].set_xlabel('Depth (m)')
axes[0].set_title('ARX — Mean RMSE per Depth\n(mm, avg 2022–2025)')
plt.colorbar(im1, ax=axes[0], label='RMSE (mm)')

# --- right: improvement % ---
norm = TwoSlopeNorm(vmin=improvement_mat[~np.isnan(improvement_mat)].min(),
                    vcenter=0, vmax=improvement_mat[~np.isnan(improvement_mat)].max())
im2 = axes[1].imshow(improvement_mat, aspect='auto', origin='upper',
                     extent=[dep_arr[0], dep_arr[-1], len(active_stations_sorted)-0.5, -0.5],
                     cmap='RdYlGn', norm=norm)
axes[1].set_yticks(np.arange(len(active_stations_sorted)))
axes[1].set_yticklabels(active_stations_sorted, fontsize=8)
axes[1].set_xlabel('Depth (m)')
axes[1].set_title('RMSE Improvement over Baseline\n(%, avg 2022–2025)')
plt.colorbar(im2, ax=axes[1], label='Improvement (%)')

fig.suptitle('Walk-Forward Validation: ARX vs. Static Direct Ratio — Depth × Station', y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig2_depth_station_heatmap.png'), bbox_inches='tight')
plt.close(fig)
print('Fig 2 saved.')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 3 — phi_k profiles: all 39 stations
# ══════════════════════════════════════════════════════════════════════════════
active_mask   = np.array([s in summary[summary['arx_recommended']]['station'].values for s in stations])
shutdown_mask = ~active_mask

fig, ax = plt.subplots(figsize=(7, 8))
for i, sta in enumerate(stations):
    color = ACTIVE_COLOR if active_mask[i] else '#aaaaaa'
    lw    = 1.0 if active_mask[i] else 0.5
    alpha = 0.7 if active_mask[i] else 0.35
    ax.plot(phi_all[i], depths, color=color, lw=lw, alpha=alpha)

# legend proxies
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color=ACTIVE_COLOR, lw=1.5, label='Active stations (19)'),
    Line2D([0], [0], color='#aaaaaa',    lw=0.8, label='Shut-down stations (20)'),
    Line2D([0], [0], color='k', lw=1, ls='--', label='phi = 1.0 (unit root)'),
]
ax.axvline(1.0, color='k', ls='--', lw=1, alpha=0.6)
ax.set_xlabel('AR(1) coefficient $\\phi_k$')
ax.set_ylabel('Depth (m)')
ax.set_ylim(295, 0)
ax.set_xlim(0.92, 1.06)
ax.set_title('ARX Parameter $\\phi_k$ — All 39 Stations\n(near-unit-root: cumulative compaction is persistent)', pad=8)
ax.legend(handles=legend_elements, fontsize=9, loc='lower right')
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig3_phi_profiles.png'), bbox_inches='tight')
plt.close(fig)
print('Fig 3 saved.')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 4 — TUKU obs vs ARX predicted (time series, 4 depths, 2022–2025)
# Raw convention: negative = subsidence. No negation applied.
# ══════════════════════════════════════════════════════════════════════════════
import matplotlib.dates as mdates

STATION = 'TUKU'
HOLDOUT_DEPTHS = [30, 60, 120, 200]  # representative shallow / mid / deep

# Load MLCW — raw convention: negative = subsidence
mlcw_path = os.path.join(MLCW_DIR, f'{STATION}_5m_grid.csv')
mlcw_raw  = pd.read_csv(mlcw_path, parse_dates=['datetime']).set_index('datetime').sort_index()
mlcw      = mlcw_raw  # no negation: negative = subsidence

# Load InSAR — raw convention: negative = subsidence
insar_df   = feather.read_feather(INSAR_FILE)
sta_row    = insar_df[insar_df['Ename'] == STATION].iloc[0]
epoch_cols = [c for c in insar_df.columns if c.startswith('D2')]
epochs     = pd.to_datetime([c[1:] for c in epoch_cols], format='%Y%m%d')
insar_ts   = pd.Series(sta_row[epoch_cols].values.astype(float) * 1000.0, index=epochs).sort_index()
# m → mm; no negation: negative = subsidence

params     = pd.read_csv(os.path.join(ARX_DIR, f'{STATION}_arx_params.csv'))
ratio_df   = pd.read_csv(os.path.join(BASE, 'direct_ratio_MLCW_InSAR', STATION,
                                      f'{STATION}_direct_ratio_stats.csv'))

TRAIN_END  = pd.Timestamp('2021-11-30')
HOLD_START = pd.Timestamp('2022-01-01')

insar_common = insar_ts[insar_ts.index >= pd.Timestamp('2015-01-01')]

fig, axes = plt.subplots(len(HOLDOUT_DEPTHS), 1, figsize=(12, 10), sharex=True)
fig.suptitle(f'TUKU — ARX vs. Static Baseline vs. Observed MLCW\n'
             f'Hold-out: 2022–2025  |  Model trained on 2015–2021  |  Negative = subsidence', y=1.01)

for ax, depth in zip(axes, HOLDOUT_DEPTHS):
    col = f'depth_{depth:03d}m'
    if col not in mlcw.columns:
        ax.set_title(f'Depth {depth} m — not in MLCW')
        continue

    # align MLCW to InSAR epochs
    mlcw_interp = (mlcw[col]
                   .reindex(mlcw[col].index.union(insar_common.index))
                   .interpolate('time')[insar_common.index])

    all_epochs = insar_common.index
    all_x      = insar_common.values
    all_y_obs  = mlcw_interp.values
    # Baseline-align to first common epoch (matches arx_all_stations.py training)
    all_x     = all_x     - all_x[0]
    all_y_obs = all_y_obs - all_y_obs[0]
    hold_mask  = all_epochs >= HOLD_START
    hold_idx   = np.where(hold_mask)[0]
    anchor_idx = hold_idx[0] - 1

    # ARX params
    row = params[params['depth_m'] == depth]
    if len(row) == 0:
        ax.set_title(f'Depth {depth} m — no ARX params')
        continue
    phi   = row['phi_k'].values[0]
    beta  = row['beta_k'].values[0]
    gamma = row['gamma_k'].values[0]

    # f_median for static baseline
    f_med_row = ratio_df[ratio_df['depth_m'] == depth]
    f_med     = f_med_row['f_median'].values[0] if len(f_med_row) > 0 else np.nan

    # recursive ARX forward prediction (uses predicted state, not observed)
    y_hat_arx = np.full(len(hold_idx), np.nan)
    y_prev    = all_y_obs[anchor_idx]
    x_prev    = all_x[anchor_idx]
    for j, idx in enumerate(hold_idx):
        dx           = all_x[idx] - x_prev
        y_hat        = phi * y_prev + beta * all_x[idx] + gamma * dx
        y_hat_arx[j] = y_hat
        x_prev       = all_x[idx]
        y_prev       = y_hat

    y_hat_base = f_med * all_x[hold_mask]
    hold_dates  = all_epochs[hold_mask]
    y_obs_hold  = all_y_obs[hold_mask]

    rmse_arx  = np.sqrt(np.nanmean((y_obs_hold - y_hat_arx)**2))
    rmse_base = np.sqrt(np.nanmean((y_obs_hold - y_hat_base)**2))
    impr      = 100 * (rmse_base - rmse_arx) / rmse_base

    ax.plot(hold_dates, y_obs_hold, 'k-',  lw=1.6, label='Observed (MLCW)', zorder=3)
    ax.plot(hold_dates, y_hat_arx,  color=ACTIVE_COLOR,   lw=1.3, ls='-',  label='ARX prediction', zorder=2)
    ax.plot(hold_dates, y_hat_base, color=BASELINE_COLOR, lw=1.0, ls='--', label='Static baseline (f̄·x)', zorder=1)
    ax.axvspan(HOLD_START, hold_dates[-1], alpha=0.05, color='steelblue')
    ax.set_ylabel('Displacement (mm, negative = subsidence)', fontsize=9)
    ax.set_title(f'Depth {depth} m  |  RMSE: ARX = {rmse_arx:.2f} mm,  Baseline = {rmse_base:.2f} mm  →  {impr:.1f}% improvement',
                 fontsize=9)
    ax.set_facecolor(PANEL_BG)
    if depth == HOLDOUT_DEPTHS[0]:
        ax.legend(fontsize=8.5, loc='upper left')

axes[-1].set_xlabel('Date')
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig4_tuku_obs_vs_pred.png'), bbox_inches='tight')
plt.close(fig)
print('Fig 4 saved.')

# ══════════════════════════════════════════════════════════════════════════════
# Figure 5 — Per-fold RMSE breakdown: arx vs baseline for each hold-out year (TUKU)
# ══════════════════════════════════════════════════════════════════════════════
wf = pd.read_csv(os.path.join(ARX_DIR, f'{STATION}_arx_walkforward_rmse.csv'))
years = ['2022', '2023', '2024', '2025']

fig, axes = plt.subplots(1, 4, figsize=(14, 6), sharey=True)
fig.suptitle(f'TUKU — ARX vs. Baseline RMSE by Hold-Out Year and Depth', y=1.01)

for ax, yr in zip(axes, years):
    arx_col  = f'rmse_arx_{yr}'
    base_col = f'rmse_base_{yr}'
    ax.plot(wf[base_col], wf['depth_m'], color=BASELINE_COLOR, lw=1.5, ls='--', label='Baseline')
    ax.plot(wf[arx_col],  wf['depth_m'], color=ACTIVE_COLOR,   lw=1.5, label='ARX')
    ax.set_xlabel('RMSE (mm)')
    ax.set_title(f'Hold-out {yr}')
    ax.set_ylim(295, 0)
    ax.set_facecolor(PANEL_BG)
    if yr == years[0]:
        ax.set_ylabel('Depth (m)')
        ax.legend(fontsize=9)

fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig5_tuku_rmse_by_year.png'), bbox_inches='tight')
plt.close(fig)
print('Fig 5 saved.')

print(f'\nAll figures saved to: {FIG_DIR}')
