"""
prophet_tuku.py
Prophet-based per-depth compaction forecasting at TUKU station.
Adds InSAR as exogenous regressor (add_regressor).
Walk-forward validation: folds ending 2021-11, 2022-11, 2023-11, 2024-11 to hold-outs 2022, 2023, 2024, 2025.
"""

import logging
import warnings
import os

# Suppress noisy Prophet / Stan output before importing
logging.getLogger('prophet').setLevel(logging.ERROR)
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
MLCW_PATH   = Path('D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/MLCW_5m_regular/TUKU_5m_grid.csv')
INSAR_PATH  = Path('D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/InSAR_timeries/mlcw_interp_insar_IDW_extend.feather')
RATIO_PATH  = Path('D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/direct_ratio_MLCW_InSAR/TUKU/TUKU_direct_ratio_stats.csv')
ARX_PATH    = Path('D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/arx_method7/TUKU_arx_walkforward_rmse.csv')
OUT_DIR     = Path('D:/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2/prophet_tuku')
FIG_DIR     = OUT_DIR / 'figures'
OUT_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

# ── matplotlib defaults ────────────────────────────────────────────────────────
plt.rcParams.update({
    'figure.dpi': 150,
    'font.family': 'DejaVu Sans',
    'axes.grid': True,
    'grid.alpha': 0.3,
})

# ── constants ──────────────────────────────────────────────────────────────────
FOLD_ENDS  = ['2021-11-30', '2022-11-30', '2023-11-30', '2024-11-30']
FOLD_NAMES = ['2022',       '2023',       '2024',       '2025']

# Representative depths: every 5th index to depths 0,25,50,...,275 m
REP_DEPTH_IDX = list(range(0, 60, 5))          # 12 indices
REP_DEPTHS_M  = [i * 5 for i in REP_DEPTH_IDX] # [0,25,50,...,275]

# 4 specific depths for detailed figures (convert to nearest 5 m depth_XXXm col)
DETAIL_DEPTHS_M = [30, 100, 180, 250]

# ── 1. Load data ───────────────────────────────────────────────────────────────
print('Loading data ...')

mlcw_raw = pd.read_csv(MLCW_PATH, parse_dates=['datetime']).set_index('datetime').sort_index()

# depth columns: depth_000m … depth_295m (exclude depth_300m anchor)
depth_cols = [c for c in mlcw_raw.columns if c.startswith('depth_') and c != 'depth_300m']
depth_vals_m = [int(c.replace('depth_', '').replace('m', '')) for c in depth_cols]  # [0,5,10,...,295]
assert len(depth_cols) == 60, f"Expected 60 depth cols, got {len(depth_cols)}"

df_insar = pd.read_feather(INSAR_PATH)
epoch_cols = [c for c in df_insar.columns if str(c).startswith('D20')]
dates_insar = pd.to_datetime([c.lstrip('D') for c in epoch_cols], format='%Y%m%d')

row_tuku = df_insar[df_insar['Ename'] == 'TUKU'].iloc[0]
insar_raw = pd.Series(
    row_tuku[epoch_cols].values.astype(float) * 1000.0,  # m to mm
    index=dates_insar,
    name='insar_mm'
)

# Inner join on dates
common = insar_raw.index.intersection(mlcw_raw.index)
common = common.sort_values()
print(f"  Common epochs: {len(common)}  ({common[0].date()} to {common[-1].date()})")

x_all = insar_raw.loc[common].values          # shape (n,)
Y_all = mlcw_raw.loc[common, depth_cols].values  # shape (n, 60)

# Baseline alignment: both start at 0 on first common epoch (2015-01-21)
x_all = x_all - x_all[0]
Y_all = Y_all - Y_all[0, :]
common_dates = common  # DatetimeIndex length n

# ── 2. Load f_median (static baseline) ────────────────────────────────────────
ratio_df = pd.read_csv(RATIO_PATH)
# f_median indexed by depth_m
f_median_series = ratio_df.set_index('depth_m')['f_median']
# Build array matching depth_cols order
f_median_arr = np.array([f_median_series.loc[dm] for dm in depth_vals_m])  # shape (60,)

# ── 3. Prophet fit/predict ─────────────────────────────────────────────────────
from prophet import Prophet  # import after logging config

def fit_predict_prophet(y_train, x_train, dates_train, x_ho, dates_ho):
    """Fit Prophet with InSAR regressor on training data; return yhat on hold-out."""
    df_train = pd.DataFrame({
        'ds':    dates_train,
        'y':     y_train,
        'insar': x_train,
    })
    # Remove NaN rows
    df_train = df_train.dropna()

    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        uncertainty_samples=0,  # MAP / L-BFGS, fast
    )
    m.add_regressor('insar')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        m.fit(df_train)

    df_future = pd.DataFrame({'ds': dates_ho, 'insar': x_ho})
    forecast = m.predict(df_future)
    return forecast['yhat'].values

# ── 4. Determine depth indices to run ─────────────────────────────────────────
# Combine representative + detail depths, deduplicate
all_target_depths_m = sorted(set(REP_DEPTHS_M) | set(DETAIL_DEPTHS_M))
# Find index in depth_cols for each target depth
def depth_to_idx(dm):
    return depth_vals_m.index(dm)

all_target_idx = [depth_to_idx(dm) for dm in all_target_depths_m]

print(f"Running Prophet on {len(all_target_depths_m)} depths: {all_target_depths_m}")

# ── 5. Walk-forward validation loop ───────────────────────────────────────────
# Results storage: dict of {depth_m: {fold_name: {'prophet': rmse, 'base': rmse}}}
results = {}

# Store full hold-out predictions for time-series figures (detail depths only)
# {depth_m: {fold_name: (dates_ho, y_ho_obs, y_ho_prophet, y_ho_base)}}
ts_preds = {dm: {} for dm in DETAIL_DEPTHS_M}

n_total = len(all_target_depths_m) * len(FOLD_ENDS)
done = 0

for k_idx, dm in zip(all_target_idx, all_target_depths_m):
    results[dm] = {}
    y_col = Y_all[:, k_idx]  # shape (n,)

    for fold_end_str, fold_name in zip(FOLD_ENDS, FOLD_NAMES):
        fold_end = pd.Timestamp(fold_end_str)
        # Hold-out: strictly after fold_end
        # (fold_end itself is the last training date)
        mask_train = common_dates <= fold_end
        mask_ho    = common_dates > fold_end

        if mask_ho.sum() == 0:
            results[dm][fold_name] = {'prophet': np.nan, 'base': np.nan}
            done += 1
            continue

        dates_train = common_dates[mask_train]
        dates_ho    = common_dates[mask_ho]
        x_train = x_all[mask_train]
        x_ho    = x_all[mask_ho]
        y_train = y_col[mask_train]
        y_ho    = y_col[mask_ho]

        # Baseline prediction: static f_median * InSAR hold-out
        f_k = f_median_arr[k_idx]
        y_base_pred = f_k * x_ho

        # Prophet prediction
        try:
            y_prop_pred = fit_predict_prophet(y_train, x_train, dates_train, x_ho, dates_ho)
        except Exception as e:
            print(f"  WARNING Prophet failed depth={dm}m fold={fold_name}: {e}")
            y_prop_pred = np.full(len(y_ho), np.nan)

        rmse_prophet = float(np.sqrt(np.nanmean((y_ho - y_prop_pred)**2)))
        rmse_base    = float(np.sqrt(np.nanmean((y_ho - y_base_pred)**2)))

        results[dm][fold_name] = {'prophet': rmse_prophet, 'base': rmse_base}

        # Store time-series for figure 2
        if dm in DETAIL_DEPTHS_M:
            ts_preds[dm][fold_name] = (dates_ho, y_ho, y_prop_pred, y_base_pred)

        done += 1
        print(f"  [{done}/{n_total}] depth={dm:3d}m fold={fold_name}  "
              f"prophet={rmse_prophet:.3f}  base={rmse_base:.3f}")

# ── 6. Build walkforward CSV ───────────────────────────────────────────────────
records = []
for dm in sorted(results.keys()):
    row = {'depth_m': dm}
    for fn in FOLD_NAMES:
        row[f'rmse_prophet_{fn}'] = results[dm][fn]['prophet']
        row[f'rmse_base_{fn}']    = results[dm][fn]['base']
    records.append(row)

wf_df = pd.DataFrame(records)
wf_path = OUT_DIR / 'TUKU_prophet_walkforward_rmse.csv'
wf_df.to_csv(wf_path, index=False)
print(f"\nSaved: {wf_path}")

# ── 7. Build summary CSV ───────────────────────────────────────────────────────
summary_records = []
for dm in sorted(results.keys()):
    prophet_vals = [results[dm][fn]['prophet'] for fn in FOLD_NAMES if not np.isnan(results[dm][fn]['prophet'])]
    base_vals    = [results[dm][fn]['base']    for fn in FOLD_NAMES if not np.isnan(results[dm][fn]['base'])]
    if prophet_vals and base_vals:
        rmse_p_med = float(np.median(prophet_vals))
        rmse_b_med = float(np.median(base_vals))
        impr_pct   = 100.0 * (rmse_b_med - rmse_p_med) / rmse_b_med if rmse_b_med > 0 else np.nan
    else:
        rmse_p_med = rmse_b_med = impr_pct = np.nan
    summary_records.append({
        'depth_m': dm,
        'rmse_prophet_med_mm': rmse_p_med,
        'rmse_base_med_mm':    rmse_b_med,
        'impr_pct':            impr_pct,
    })

sum_df = pd.DataFrame(summary_records)
sum_path = OUT_DIR / 'TUKU_prophet_summary.csv'
sum_df.to_csv(sum_path, index=False)
print(f"Saved: {sum_path}")

# ── 8. Figure 1 — horizontal bar chart ────────────────────────────────────────
print('\nPlotting Fig 1 ...')
rep_depths_in_summary = [dm for dm in REP_DEPTHS_M if dm in set(all_target_depths_m)]
rep_rows = sum_df[sum_df['depth_m'].isin(rep_depths_in_summary)].sort_values('depth_m', ascending=False)

fig, ax = plt.subplots(figsize=(9, 7))
y_pos = np.arange(len(rep_rows))
bar_h = 0.35

bars_base    = ax.barh(y_pos + bar_h/2, rep_rows['rmse_base_med_mm'],    bar_h, label='Static baseline', color='#d62728', alpha=0.8)
bars_prophet = ax.barh(y_pos - bar_h/2, rep_rows['rmse_prophet_med_mm'], bar_h, label='Prophet + InSAR', color='#1f77b4', alpha=0.8)

ax.set_yticks(y_pos)
ax.set_yticklabels([f"{int(d)} m" for d in rep_rows['depth_m']])
ax.set_xlabel('Median walk-forward RMSE (mm)')
ax.set_title('TUKU — Prophet vs Static Baseline\nMedian RMSE across 4 walk-forward folds')
ax.legend()
fig.tight_layout()
fig.savefig(FIG_DIR / 'fig1_prophet_vs_baseline_bar.png')
plt.close(fig)
print('  Saved fig1')

# ── 9. Figure 2 — 4-panel time series ─────────────────────────────────────────
print('Plotting Fig 2 ...')
fig, axes = plt.subplots(4, 1, figsize=(13, 16), sharex=False)

hold_start = pd.Timestamp('2022-01-01')

for ax_i, dm in enumerate(DETAIL_DEPTHS_M):
    ax = axes[ax_i]
    k_idx2 = depth_to_idx(dm)
    y_full = Y_all[:, k_idx2]
    x_full = x_all  # not plotted, just for reference

    # Observed full series
    ax.plot(common_dates, y_full, 'k-', lw=0.8, label='Observed MLCW', zorder=3)

    # Shaded hold-out region
    ax.axvspan(hold_start, common_dates[-1], color='lightyellow', alpha=0.6, label='Hold-out (2022–2025)')

    # Collect all hold-out predictions across folds
    all_dates_ho = []
    all_y_ho_prophet = []
    all_y_ho_base = []
    for fn in FOLD_NAMES:
        if fn in ts_preds[dm]:
            dates_ho_f, y_ho_obs_f, y_ho_prop_f, y_ho_base_f = ts_preds[dm][fn]
            all_dates_ho.extend(dates_ho_f)
            all_y_ho_prophet.extend(y_ho_prop_f)
            all_y_ho_base.extend(y_ho_base_f)

    if all_dates_ho:
        # Sort by date
        sort_idx = np.argsort(all_dates_ho)
        dates_sorted   = np.array(all_dates_ho)[sort_idx]
        prophet_sorted = np.array(all_y_ho_prophet)[sort_idx]
        base_sorted    = np.array(all_y_ho_base)[sort_idx]
        ax.plot(dates_sorted, prophet_sorted, 'b-',  lw=1.2, label='Prophet prediction', zorder=4)
        ax.plot(dates_sorted, base_sorted,    'r--', lw=1.2, label='Static baseline pred.', zorder=4)

    # RMSE annotation from summary
    row_s = sum_df[sum_df['depth_m'] == dm]
    if not row_s.empty:
        rp = row_s['rmse_prophet_med_mm'].values[0]
        rb = row_s['rmse_base_med_mm'].values[0]
        impr = row_s['impr_pct'].values[0]
        title_str = f"Depth {dm} m  |  Prophet RMSE={rp:.3f} mm, Baseline={rb:.3f} mm, Impr={impr:.1f}%"
    else:
        title_str = f"Depth {dm} m"
    ax.set_title(title_str, fontsize=9)
    ax.set_ylabel('Cumulative compaction (mm)')
    if ax_i == 0:
        ax.legend(fontsize=7, ncol=2, loc='upper left')
    ax.axvline(hold_start, color='gray', lw=0.8, ls='--')

axes[-1].set_xlabel('Date')
fig.suptitle('TUKU — Prophet + InSAR regressor: Time-series at 4 depths', fontsize=11, y=1.01)
fig.tight_layout()
fig.savefig(FIG_DIR / 'fig2_prophet_ts_4depths.png', bbox_inches='tight')
plt.close(fig)
print('  Saved fig2')

# ── 10. Figure 3 — Prophet vs ARX improvement profile ─────────────────────────
print('Plotting Fig 3 ...')

if ARX_PATH.exists():
    arx_df = pd.read_csv(ARX_PATH)
    # Compute ARX median RMSE and improvement
    arx_records = []
    for _, arx_row in arx_df.iterrows():
        dm_arx = int(arx_row['depth_m'])
        arx_vals  = [arx_row[f'rmse_arx_{fn}']  for fn in FOLD_NAMES if f'rmse_arx_{fn}'  in arx_row.index]
        base_vals = [arx_row[f'rmse_base_{fn}'] for fn in FOLD_NAMES if f'rmse_base_{fn}' in arx_row.index]
        arx_vals  = [v for v in arx_vals  if not np.isnan(v)]
        base_vals = [v for v in base_vals if not np.isnan(v)]
        if arx_vals and base_vals:
            arx_med  = np.median(arx_vals)
            base_med = np.median(base_vals)
            impr_arx = 100.0 * (base_med - arx_med) / base_med if base_med > 0 else np.nan
        else:
            impr_arx = np.nan
        arx_records.append({'depth_m': dm_arx, 'impr_arx_pct': impr_arx})
    arx_sum = pd.DataFrame(arx_records)

    # Merge with prophet summary on depths present in both
    merge_df = pd.merge(
        sum_df[['depth_m', 'impr_pct']].rename(columns={'impr_pct': 'impr_prophet_pct'}),
        arx_sum,
        on='depth_m', how='inner'
    ).sort_values('depth_m')

    fig, ax = plt.subplots(figsize=(8, 9))
    ax.plot(merge_df['impr_prophet_pct'], merge_df['depth_m'],
            'b-o', ms=5, lw=1.4, label='Prophet + InSAR')
    ax.plot(merge_df['impr_arx_pct'],     merge_df['depth_m'],
            'g-s', ms=5, lw=1.4, label='ARX (method 7)')
    ax.axvline(0, color='k', lw=0.8, ls='--')
    ax.set_xlabel('Improvement over static baseline (%)')
    ax.set_ylabel('Depth (m)')
    ax.invert_yaxis()
    ax.set_title('TUKU — Prophet vs ARX\nWalk-forward RMSE improvement over static baseline')
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'fig3_prophet_vs_arx_improvement.png')
    plt.close(fig)
    print('  Saved fig3')
else:
    print('  ARX file not found — fig3 skipped')

# ── 11. Print summary table ────────────────────────────────────────────────────
print('\n=== Prophet summary (representative depths) ===')
print(sum_df[sum_df['depth_m'].isin(REP_DEPTHS_M)].to_string(index=False))

print('\nDone. All outputs in:', OUT_DIR)

