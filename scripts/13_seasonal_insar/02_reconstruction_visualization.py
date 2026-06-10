"""
02_reconstruction_visualization.py
------------------------------------
Visualise how well InSAR alone can reconstruct per-layer MLCW compaction.

Two reconstruction tiers are shown:
  Tier 1 (TREND only):    f̄_k × InSAR_trend(t)
  Tier 2 (TREND+SEASONAL): f̄_k × InSAR_trend(t) + r1_k × A1_x × sin(ωt + φ1_x + Δφ1_k)

Where:
  f̄_k          = median(MLCW_k / InSAR) over all valid epochs (direct ratio, static scaling)
  InSAR_trend   = linear trend of InSAR (a + b·t_days)
  r1_k          = mean annual amplitude ratio from Step 3 phase stability summary
  A1_x, φ1_x   = InSAR annual harmonic amplitude and phase from Step 2
  Δφ1_k         = mean annual phase offset (MLCW leads InSAR by Δφ1_k days) from Step 3

Outputs per station (in figures/seasonal_insar_harmonic/{STATION}/):
  reconstruction_full_timeseries.png   — observed vs Tier1 vs Tier2, all layers, full 2015-2025
  reconstruction_seasonal_zoom.png     — detrended observed vs detrended Tier2 (seasonal only)
  reconstruction_metrics_summary.png   — RMSE bar chart comparing Tier1 vs Tier2

Also writes:
  results/seasonal_insar_harmonic/{STATION}/reconstruction_metrics.csv

Usage:
  PYTHONPATH="" conda run -n fafalab2 python scripts/13_seasonal_insar/02_reconstruction_visualization.py --station TUKU
  PYTHONPATH="" conda run -n fafalab2 python scripts/13_seasonal_insar/02_reconstruction_visualization.py --station XIUTAN
  PYTHONPATH="" conda run -n fafalab2 python scripts/13_seasonal_insar/02_reconstruction_visualization.py --station YUANCHANG
"""

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ANNUAL_T   = 365.25
LAYERS     = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']
ANALYSIS_START = '2015-01-01'
ANALYSIS_END   = '2025-12-31'

# ── Path helpers ──────────────────────────────────────────────────────────────
def find_project_root() -> Path:
    candidate = Path(__file__).resolve().parent
    for _ in range(4):
        candidate = candidate.parent
        if (candidate / 'data' / 'mlcw').exists():
            return candidate
    raise RuntimeError("Cannot locate project root.")


# ── Data loading ──────────────────────────────────────────────────────────────
def load_mlcw(station: str, root: Path) -> pd.DataFrame:
    path = root / 'data' / 'mlcw' / 'group_byLayer_reconstr' / f'{station}_reconst_grouped.csv'
    df = pd.read_csv(path, parse_dates=['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    mask = (df['datetime'] >= ANALYSIS_START) & (df['datetime'] <= ANALYSIS_END)
    return df[mask].reset_index(drop=True)


def load_insar(station: str, root: Path) -> pd.Series:
    path = root / 'data' / 'insar' / 'timeseries' / 'mlcw_interp_insar_IDW_extend.feather'
    df = pd.read_feather(path)
    row = df[df['Ename'] == station]
    if len(row) != 1:
        raise ValueError(f"Station '{station}' not found in feather.")
    epoch_cols, epoch_dates = [], []
    for c in df.columns:
        if isinstance(c, str) and c.startswith('D') and len(c) == 9:
            try:
                epoch_cols.append(c)
                epoch_dates.append(pd.to_datetime(c[1:], format='%Y%m%d'))
            except Exception:
                pass
    vals = row[epoch_cols].values.flatten().astype(float)
    if np.nanmedian(np.abs(vals[~np.isnan(vals)])) < 1.0:
        vals *= 1000.0
    s = pd.Series(vals, index=pd.DatetimeIndex(epoch_dates), name='insar_mm').sort_index()
    return s[(s.index >= ANALYSIS_START) & (s.index <= ANALYSIS_END)]


def t_days(dates, ref=None):
    if ref is None:
        ref = dates[0]
    return (pd.DatetimeIndex(dates) - ref).total_seconds().values / 86400.0


# ── Detrend ───────────────────────────────────────────────────────────────────
def linear_detrend(t, y):
    valid = ~np.isnan(y)
    A = np.column_stack([np.ones(valid.sum()), t[valid]])
    coef, *_ = np.linalg.lstsq(A, y[valid], rcond=None)
    trend = coef[0] + coef[1] * t
    return y - trend, trend, coef


# ── Direct ratio f̄_k (static scaling) ─────────────────────────────────────────
def compute_fbar_anchored(y_mlcw, y_insar):
    """
    OLS slope of ΔMLCW_k ~ ΔInSAR (both anchored to first common valid epoch).
    Anchoring removes the offset caused by different reference dates
    (MLCW cumulates from ~2003 installation; InSAR starts near 0 in Jan 2015).
    Returns (fbar, anchor_mlcw, anchor_insar) for reconstruction.
    """
    valid = ~np.isnan(y_mlcw) & ~np.isnan(y_insar)
    if valid.sum() < 20:
        return np.nan, np.nan, np.nan
    first = np.where(valid)[0][0]
    dy_mlcw  = y_mlcw  - y_mlcw[first]   # ΔMLCW from first common epoch
    dy_insar = y_insar - y_insar[first]   # ΔInSAR from first common epoch
    # OLS through origin: slope = Σ(dy_mlcw × dy_insar) / Σ(dy_insar²)
    v = valid.copy()
    v[first] = False  # exclude anchor epoch (both 0 there)
    denom = float(np.dot(dy_insar[v], dy_insar[v]))
    if denom < 1e-6:
        return np.nan, y_mlcw[first], y_insar[first]
    fbar = float(np.dot(dy_mlcw[v], dy_insar[v]) / denom)
    return fbar, float(y_mlcw[first]), float(y_insar[first])


# ── Harmonic reconstruction ───────────────────────────────────────────────────
def build_seasonal_reconstruction(t_common, A1_x, phi1_x_rad, Δφ1_rad, r1):
    """
    Seasonal prediction: r1 × A1_x × sin(ωt + φ1_x + Δφ1)
    = r1 × A1_x × sin(ωt + φ1_k)   where φ1_k = φ1_x + Δφ1
    """
    omega = 2 * np.pi / ANNUAL_T
    phi1_k_rad = phi1_x_rad + Δφ1_rad
    return r1 * A1_x * np.sin(omega * t_common + phi1_k_rad)


def save_fig(fig, path, dpi=300):
    fig.savefig(path, dpi=dpi, bbox_inches='tight', format='png')
    plt.close(fig)
    print(f"  Saved → {path.name}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RECONSTRUCTION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
def run(station: str):
    root = find_project_root()
    res_dir = root / 'results' / 'seasonal_insar_harmonic' / station
    fig_dir = root / 'figures'  / 'seasonal_insar_harmonic' / station
    fig_dir.mkdir(parents=True, exist_ok=True)

    # ── Load step outputs ──────────────────────────────────────────────────
    step2 = pd.read_csv(res_dir / 'step2_insar_harmonic_decomposition.csv').iloc[0]
    step3 = pd.read_csv(res_dir / 'step3_phase_stability_summary.csv')
    step3 = step3.set_index('layer')

    A1_x      = float(step2['A1_x_mm'])
    phi1_x_rad = float(step2['phi1_x_rad'])

    # ── Load raw data ──────────────────────────────────────────────────────
    mlcw_df  = load_mlcw(station, root)
    insar_s  = load_insar(station, root)
    avail    = [L for L in LAYERS if L in mlcw_df.columns]

    # Align InSAR to MLCW timeline
    insar_tmp = insar_s.reset_index()
    insar_tmp.columns = ['datetime', 'insar_mm']
    merged = pd.merge_asof(
        mlcw_df[['datetime']].sort_values('datetime'),
        insar_tmp.sort_values('datetime'),
        on='datetime', direction='nearest', tolerance=pd.Timedelta('10D')
    ).sort_values('datetime').reset_index(drop=True)

    dates   = pd.DatetimeIndex(merged['datetime'])
    t_ref   = dates[0]
    t_vec   = t_days(dates, t_ref)
    y_insar = merged['insar_mm'].values.astype(float)

    # Detrend InSAR
    y_insar_det, insar_trend, _ = linear_detrend(t_vec, y_insar)

    metrics_rows = []

    # ── Compute reconstructions per layer ─────────────────────────────────
    layer_data = {}
    for layer in avail:
        # MLCW on merged timeline
        mlcw_tmp = pd.merge_asof(
            merged[['datetime']],
            mlcw_df[['datetime', layer]].sort_values('datetime'),
            on='datetime', direction='nearest', tolerance=pd.Timedelta('10D')
        )
        y_obs = mlcw_tmp[layer].values.astype(float)

        # Tier 1: anchored trend reconstruction (static scaling)
        # Both signals are anchored to first common valid epoch to align baselines.
        # Tier1(t) = MLCW_k(t0) + f̄_k × [InSAR(t) − InSAR(t0)]
        fbar, anchor_mlcw, anchor_insar = compute_fbar_anchored(y_obs, y_insar)
        if not np.isnan(fbar):
            tier1 = anchor_mlcw + fbar * (y_insar - anchor_insar)
        else:
            tier1 = np.full_like(y_insar, np.nan)

        # Seasonal transfer parameters
        if layer in step3.index and step3.loc[layer, 'annual_PASS']:
            r1    = float(step3.loc[layer, 'mean_r1'])
            dphi1_days = float(step3.loc[layer, 'mean_dphi1_days'])
            dphi1_rad  = dphi1_days / ANNUAL_T * 2 * np.pi
            seasonal_pred = build_seasonal_reconstruction(t_vec, A1_x, phi1_x_rad, dphi1_rad, r1)
            # Tier2: anchored trend + per-layer seasonal
            # The seasonal term is already centred (mean ~0), so we add it to Tier1
            tier2 = tier1 + seasonal_pred
            has_seasonal = True
        else:
            tier2 = tier1.copy()
            has_seasonal = False
            seasonal_pred = np.zeros_like(y_obs)

        # Detrended MLCW (for seasonal-only plot)
        y_obs_det, _, _ = linear_detrend(t_vec, y_obs)

        layer_data[layer] = {
            'y_obs':       y_obs,
            'y_obs_det':   y_obs_det,
            'tier1':       tier1,
            'tier2':       tier2,
            'seasonal_pred': seasonal_pred,
            'fbar':        fbar,
            'has_seasonal': has_seasonal,
        }

        # Metrics (exclude NaN epochs)
        valid = ~np.isnan(y_obs) & ~np.isnan(tier1)
        if valid.sum() > 10:
            rmse_t1 = float(np.sqrt(np.nanmean((y_obs[valid] - tier1[valid])**2)))
            rmse_t2 = float(np.sqrt(np.nanmean((y_obs[valid] - tier2[valid])**2)))
            ss_tot  = float(np.nanvar(y_obs[valid]))
            r2_t1   = float(1 - np.nanmean((y_obs[valid]-tier1[valid])**2) / ss_tot)
            r2_t2   = float(1 - np.nanmean((y_obs[valid]-tier2[valid])**2) / ss_tot)
            # Seasonal-only metrics (on detrended signal)
            valid_d  = valid & ~np.isnan(y_obs_det)
            seas_pred = layer_data[layer]['seasonal_pred']
            rmse_seas = float(np.sqrt(np.nanmean((y_obs_det[valid_d] - seas_pred[valid_d])**2)))
            r2_seas   = float(1 - np.nanmean((y_obs_det[valid_d]-seas_pred[valid_d])**2)
                              / max(np.nanvar(y_obs_det[valid_d]), 1e-9))
        else:
            rmse_t1 = rmse_t2 = rmse_seas = r2_t1 = r2_t2 = r2_seas = np.nan

        # Runtime guard: if seasonal term degrades the fit, revert to Tier 1 only
        if has_seasonal and (np.isnan(r2_seas) or r2_seas <= 0.0):
            has_seasonal = False
            layer_data[layer]['has_seasonal'] = False

        metrics_rows.append({
            'station':     station,
            'layer':       layer,
            'fbar':        round(float(fbar), 5) if not np.isnan(fbar) else np.nan,
            'RMSE_tier1_mm':  round(rmse_t1, 3),
            'RMSE_tier2_mm':  round(rmse_t2, 3),
            'R2_tier1':    round(r2_t1, 4),
            'R2_tier2':    round(r2_t2, 4),
            'RMSE_seasonal_mm': round(rmse_seas, 3),
            'R2_seasonal': round(r2_seas, 4),
            'seasonal_applied': has_seasonal,
        })
        print(f"  {layer}: fbar={fbar:.4f}, RMSE_T1={rmse_t1:.2f}mm, RMSE_T2={rmse_t2:.2f}mm, "
              f"R2_T1={r2_t1:.3f}, R2_T2={r2_t2:.3f} | R2_seas={r2_seas:.3f}")

    # Save metrics
    df_met = pd.DataFrame(metrics_rows)
    df_met.to_csv(res_dir / 'reconstruction_metrics.csv', index=False)
    print(f"  Saved → reconstruction_metrics.csv")

    # ══════════════════════════════════════════════════════════════════════
    # FIGURE 1: Full timeseries — observed vs Tier1 vs Tier2
    # ══════════════════════════════════════════════════════════════════════
    n_layers = len(avail)
    # A4 landscape: 11.7" × 8.3"; use full width, height scales per layer
    fig, axes = plt.subplots(n_layers, 1, figsize=(11.7, max(8.3, 2.0 * n_layers)), sharex=True, dpi=300)
    if n_layers == 1:
        axes = [axes]

    colors = {'obs': '#2c3e50', 'tier1': '#e74c3c', 'tier2': '#2980b9'}

    for ax, layer in zip(axes, avail):
        ld = layer_data[layer]
        ax.plot(dates, ld['y_obs'],  color=colors['obs'],   lw=1.0, alpha=0.85, label='Observed MLCW')
        ax.plot(dates, ld['tier1'],  color=colors['tier1'], lw=1.2, alpha=0.80, ls='--',
                label=f'Tier1: f̄×InSAR  (R²={df_met.loc[df_met.layer==layer,"R2_tier1"].values[0]:.3f})')
        if ld['has_seasonal']:
            ax.plot(dates, ld['tier2'], color=colors['tier2'], lw=1.2, alpha=0.90,
                    label=f'Tier2: trend+seasonal  (R²={df_met.loc[df_met.layer==layer,"R2_tier2"].values[0]:.3f})')

        ax.set_ylabel(f'{layer}\n(mm)', fontsize=9)
        ax.legend(loc='upper left', fontsize=7, ncol=3)
        ax.grid(True, alpha=0.25, lw=0.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())

    fig.suptitle(f'{station} — Observed MLCW vs InSAR reconstruction (2015–2025)\n'
                 f'Tier1 = f̄_k×InSAR (static scaling) | Tier2 = Tier1 + seasonal phase transfer',
                 fontsize=11, y=1.01)
    fig.tight_layout()
    save_fig(fig, fig_dir / 'reconstruction_full_timeseries.png')

    # ══════════════════════════════════════════════════════════════════════
    # FIGURE 2: Seasonal component zoom (detrended)
    # ══════════════════════════════════════════════════════════════════════
    fig, axes = plt.subplots(n_layers, 1, figsize=(11.7, max(8.3, 1.8 * n_layers)), sharex=True, dpi=300)
    if n_layers == 1:
        axes = [axes]

    for ax, layer in zip(axes, avail):
        ld = layer_data[layer]
        r2_s = df_met.loc[df_met.layer==layer, 'R2_seasonal'].values[0]
        rmse_s = df_met.loc[df_met.layer==layer, 'RMSE_seasonal_mm'].values[0]

        ax.fill_between(dates, ld['y_obs_det'], alpha=0.25, color='steelblue', label='')
        ax.plot(dates, ld['y_obs_det'], color='steelblue', lw=1.0, alpha=0.9,
                label='Detrended MLCW (observed)')
        if ld['has_seasonal']:
            ax.plot(dates, ld['seasonal_pred'], color='darkorange', lw=1.5,
                    label=f'InSAR seasonal prediction  (R²={r2_s:.3f}, RMSE={rmse_s:.2f}mm)')
            ax.set_ylabel(f'{layer}\n(mm)', fontsize=9)
        else:
            ax.text(0.5, 0.5, 'Phase not stable — seasonal not applied',
                    transform=ax.transAxes, ha='center', va='center',
                    color='grey', fontsize=9)
            ax.set_ylabel(f'{layer}\n(mm)', fontsize=9)

        ax.axhline(0, color='grey', lw=0.6, ls=':')
        ax.legend(loc='upper left', fontsize=7, ncol=2)
        ax.grid(True, alpha=0.25, lw=0.5)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_major_locator(mdates.YearLocator())

    fig.suptitle(f'{station} — Detrended MLCW vs InSAR seasonal prediction\n'
                 f'Seasonal = r̄1_k × A1_InSAR × sin(ωt + φ1_InSAR + Δφ̄1_k)  '
                 f'[layers not passing phase gate shown as grey text]',
                 fontsize=11, y=1.01)
    fig.tight_layout()
    save_fig(fig, fig_dir / 'reconstruction_seasonal_zoom.png')

    # ══════════════════════════════════════════════════════════════════════
    # FIGURE 3: Metrics bar chart
    # ══════════════════════════════════════════════════════════════════════
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.7, 8.3), dpi=300)

    x   = np.arange(len(avail))
    w   = 0.30
    clr = {'t1': '#e74c3c', 't2': '#2980b9', 'seas': '#27ae60'}

    rmse_t1  = df_met['RMSE_tier1_mm'].values
    rmse_t2  = df_met['RMSE_tier2_mm'].values
    rmse_s   = df_met['RMSE_seasonal_mm'].values
    r2_t1    = df_met['R2_tier1'].values
    r2_t2    = df_met['R2_tier2'].values
    r2_s     = df_met['R2_seasonal'].values

    ax1.bar(x - w, rmse_t1, w, label='Tier1: f̄_k×InSAR (trend)', color=clr['t1'], alpha=0.85)
    ax1.bar(x,     rmse_t2, w, label='Tier2: +seasonal',           color=clr['t2'], alpha=0.85)
    ax1.bar(x + w, rmse_s,  w, label='Seasonal only',              color=clr['seas'], alpha=0.85)
    ax1.set_xticks(x); ax1.set_xticklabels(avail)
    ax1.set_ylabel('RMSE (mm)'); ax1.set_title('Reconstruction RMSE by layer')
    ax1.legend(fontsize=8); ax1.grid(True, axis='y', alpha=0.3)

    ax2.bar(x - w/2, r2_t1, w, label='Tier1: f̄_k×InSAR', color=clr['t1'], alpha=0.85)
    ax2.bar(x + w/2, r2_t2, w, label='Tier2: +seasonal',  color=clr['t2'], alpha=0.85)
    ax2.axhline(0, color='grey', lw=0.8, ls='--')
    ax2.set_xticks(x); ax2.set_xticklabels(avail)
    ax2.set_ylabel('R²'); ax2.set_title('Reconstruction R² by layer')
    ax2.legend(fontsize=8); ax2.grid(True, axis='y', alpha=0.3)

    # Annotate R² for seasonal on a secondary plot
    ax2b = ax2.twinx()
    ax2b.plot(x, r2_s, 's--', color=clr['seas'], ms=7, lw=1.2, label='R² seasonal only')
    ax2b.set_ylabel('R² (seasonal component)', color=clr['seas'], fontsize=8)
    ax2b.tick_params(axis='y', labelcolor=clr['seas'])
    ax2b.legend(loc='lower right', fontsize=8)

    fig.suptitle(f'{station} — Reconstruction quality metrics', fontsize=11)
    fig.tight_layout()
    save_fig(fig, fig_dir / 'reconstruction_metrics_summary.png')

    print(f"\n  All figures saved to figures/seasonal_insar_harmonic/{station}/")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--station', required=True,
                        help='Station name (any station from group_byLayer_reconstr/).')
    args = parser.parse_args()
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    print(f"\n{'='*60}")
    print(f"  Reconstruction Visualization — {args.station}")
    print(f"{'='*60}\n")
    run(args.station)
    print("\nDone.\n")
