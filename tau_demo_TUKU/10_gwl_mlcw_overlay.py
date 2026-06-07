"""
tau_demo_TUKU/10_gwl_mlcw_overlay.py
======================================
Regime diagnostic overlay for TUKU layers.

For each layer, produces a 3-panel figure:
  Panel 1 (top):    H(t) [m, zero-ref] with h_c dashed line; background shaded
                    by regime (elastic = light gray, inelastic = light red).
  Panel 2 (middle): V(t) = min(0, cummin(H) - h_c) [m] — virgin exceedance term.
                    Shows when and how fast the inelastic term grows.
  Panel 3 (bottom): Cumulative observed MLCW b(t) (solid) vs. predicted b_pred(t)
                    (dashed) using S_ke, S_kv from stress_strain_per_layer.json.

Also writes machine-readable diagnostics to:
  tau_demo_TUKU/results/regime_overlay_diagnostics.json

Physical questions this diagnostic answers:
  F1: Is h_c = -2.344 m too shallow? (93% virgin saturation → near-collinear regressors)
  F2: Does GWL shape match MLCW shape at tau=0? (no lag — coupling quality check)
  F3: Does H ever recover above h_c = -4.456 m? (S_ke=0: permanently inelastic?)
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from pathlib import Path

# ============================================================
# PATHS — no hardcoded absolute paths
# ============================================================
REPO = Path(__file__).parent.parent
TUKU_DIR = REPO / 'tau_demo_TUKU'
DATA_DIR = TUKU_DIR / 'data'
RESULTS_DIR = TUKU_DIR / 'results'
PLOT_DIR = TUKU_DIR / 'plots' / 'results' / 'regime_overlay'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PLOT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# CONSTANTS
# ============================================================
REF_DATE = pd.Timestamp('2015-01-16')
EPOCH_DAYS = 5  # 5-day cadence
COLLINEARITY_THRESHOLD = 0.80  # flag if n_inelastic_virgin / n_total > this

# ============================================================
# LAYER CONFIGURATION (from tau_results.csv — do not edit manually)
# Wellcodes are 8-digit strings — never cast to int.
# ============================================================
LAYERS = [
    {'layer': 'F1', 'wellcode': '09050111', 'gwl_file': 'HONGLUN_gwl_timeseries.feather',
     'h_c': -2.344, 'tau_epochs': 42},
    {'layer': 'T1', 'wellcode': '09050111', 'gwl_file': 'HONGLUN_gwl_timeseries.feather',
     'h_c': -2.344, 'tau_epochs': 72},
    {'layer': 'F2', 'wellcode': '09050321', 'gwl_file': 'TUKU_gwl_timeseries.feather',
     'h_c': -5.086, 'tau_epochs': 0},
    {'layer': 'T2', 'wellcode': '09170121', 'gwl_file': 'LUNZI_gwl_timeseries.feather',
     'h_c': -8.457, 'tau_epochs': 72},
    {'layer': 'F3', 'wellcode': '09050331', 'gwl_file': 'TUKU_gwl_timeseries.feather',
     'h_c': -4.456, 'tau_epochs': 0},
    {'layer': 'F4', 'wellcode': '09080251', 'gwl_file': 'LIUZHUANG_gwl_timeseries.feather',
     'h_c': -7.008, 'tau_epochs': 105},
]

# Regime colors
COLOR_ELASTIC   = '#f0f0f0'   # light gray background
COLOR_INELASTIC = '#ffd6d6'   # light red background
COLOR_OBS       = '#2c7bb6'   # blue for observed MLCW
COLOR_PRED      = '#d7191c'   # red for predicted
COLOR_V         = '#756bb1'   # purple for V(t)
COLOR_HEAD      = '#31a354'   # green for H(t)


# ============================================================
# DATA LOADING
# ============================================================

def load_cumulative_mlcw():
    """
    Load cumulative MLCW from TUKU_reconst_grouped_cleaned.csv.
    Zero-reference each column to REF_DATE value.
    Returns DataFrame indexed by datetime (5-day cadence).
    """
    fpath = DATA_DIR / 'TUKU_reconst_grouped_cleaned.csv'
    df = pd.read_csv(fpath, parse_dates=['datetime'])
    df = df.set_index('datetime')
    df.index = pd.to_datetime(df.index)
    ref_row = df.loc[REF_DATE]
    return df - ref_row  # [mm], 0 at REF_DATE, negative = compaction


def load_gwl_absolute(gwl_file, wellcode):
    """
    Load absolute GWL from feather, zero-reference to REF_DATE.
    Returns (daily Series zero-ref [m], ref_val [m MSL]).
    Wellcode kept as string.
    """
    fpath = DATA_DIR / gwl_file
    df = pd.read_feather(str(fpath))
    df = df.set_index('datetime')
    df.index = pd.to_datetime(df.index)

    wc = str(wellcode)
    if wc not in df.columns:
        raise KeyError(f"Wellcode {wc} not in {gwl_file}. Columns: {df.columns.tolist()}")

    series = df[wc]
    avail = series.dropna()
    pre_ref = avail.index[avail.index <= REF_DATE]
    if len(pre_ref) == 0:
        raise ValueError(f"No GWL data on or before REF_DATE for wellcode {wc}")
    ref_val = float(avail.loc[pre_ref[-1]])
    return series - ref_val, ref_val


def apply_tau_lag(series_daily, tau_epochs):
    if tau_epochs == 0:
        return series_daily
    return series_daily.shift(int(tau_epochs * EPOCH_DAYS), freq='D')


def align_gwl_to_mlcw(mlcw_df, gwl_series_daily, layer):
    """
    Align daily GWL to 5-day MLCW grid (merge_asof, tolerance 3 days).
    Returns DataFrame with columns [H, b], indexed by datetime, from REF_DATE onward.
    """
    mlcw_sub = mlcw_df[[layer]].copy()
    mlcw_sub.index = pd.to_datetime(mlcw_sub.index)
    mlcw_sub = mlcw_sub[mlcw_sub.index >= REF_DATE].rename(columns={layer: 'b'})

    gwl_df = (gwl_series_daily.dropna()
              .reset_index()
              .rename(columns={gwl_series_daily.name if gwl_series_daily.name else 0: 'H',
                               'index': 'datetime'}))
    # handle Series with no name
    if 'H' not in gwl_df.columns:
        gwl_df.columns = ['datetime', 'H']
    gwl_df = gwl_df[gwl_df['datetime'] >= REF_DATE].sort_values('datetime')

    mlcw_reset = mlcw_sub.reset_index().sort_values('datetime')

    merged = pd.merge_asof(
        mlcw_reset, gwl_df,
        on='datetime',
        tolerance=pd.Timedelta('3D'),
        direction='nearest'
    ).set_index('datetime')

    return merged.dropna(subset=['H', 'b'])


# ============================================================
# PHYSICS
# ============================================================

def compute_virgin_term(H_series, h_c):
    """V(t) = min(0, cummin(H(t)) - h_c). Zero during elastic recovery."""
    H = np.asarray(H_series, dtype=float)
    cummin_H = np.minimum.accumulate(H)
    return np.minimum(0.0, cummin_H - h_c)


def compute_b_pred(H_arr, V_arr, S_ke, delta):
    """b_pred(t) = S_ke * H(t) + delta * V(t), where delta = S_kv - S_ke."""
    return S_ke * np.asarray(H_arr) + delta * np.asarray(V_arr)


def compute_r2(obs, pred):
    obs = np.asarray(obs, dtype=float)
    pred = np.asarray(pred, dtype=float)
    mask = np.isfinite(obs) & np.isfinite(pred)
    if mask.sum() < 2:
        return float('nan')
    ss_res = np.sum((obs[mask] - pred[mask])**2)
    ss_tot = np.sum((obs[mask] - obs[mask].mean())**2)
    return float('nan') if ss_tot == 0 else 1.0 - ss_res / ss_tot


# ============================================================
# PLOTTING
# ============================================================

def shade_regimes(ax, dates, elastic_mask, inelastic_mask):
    """Draw background shading for elastic (gray) and inelastic (red) epochs."""
    dates_arr = np.array(dates, dtype='datetime64[D]')

    def shade_blocks(ax, mask, color):
        in_block = False
        start = None
        for i, m in enumerate(mask):
            if m and not in_block:
                start = dates_arr[i]
                in_block = True
            elif not m and in_block:
                ax.axvspan(start, dates_arr[i - 1], color=color, alpha=0.3, lw=0)
                in_block = False
        if in_block:
            ax.axvspan(start, dates_arr[-1], color=color, alpha=0.3, lw=0)

    shade_blocks(ax, elastic_mask, COLOR_ELASTIC)
    shade_blocks(ax, inelastic_mask, COLOR_INELASTIC)


def plot_layer_overlay(layer_name, df_aligned, h_c, tau_epochs,
                       S_ke, S_kv, delta, V_arr, b_pred, out_path, diag):
    """
    3-panel figure:
      Panel 1: H(t) timeseries with h_c line and regime shading
      Panel 2: V(t) timeseries (virgin exceedance term)
      Panel 3: Cumulative observed vs predicted MLCW
    """
    H_arr    = df_aligned['H'].values
    b_arr    = df_aligned['b'].values
    dates    = df_aligned.index
    n        = len(H_arr)

    elastic_mask   = H_arr > h_c
    inelastic_mask = H_arr <= h_c
    cummin_H       = np.minimum.accumulate(H_arr)
    virgin_mask    = cummin_H < h_c  # V(t) is active (inelastic-virgin)

    ratio_str = f'{S_kv/S_ke:.1f}×' if S_ke > 0 else 'undefined (S_ke=0)'
    r2 = compute_r2(b_arr, b_pred)

    fig, axes = plt.subplots(3, 1, figsize=(13, 12), sharex=True)
    fig.suptitle(
        f'TUKU — Layer {layer_name}  |  $h_c$ = {h_c:.3f} m  |  '
        f'$\\tau$ = {tau_epochs} epochs ({tau_epochs*EPOCH_DAYS} d)  |  '
        f'$S_{{kv}}/S_{{ke}}$ = {ratio_str}',
        fontsize=14, fontweight='bold'
    )

    # ------ Panel 1: H(t) ------
    ax1 = axes[0]
    shade_regimes(ax1, dates, elastic_mask, inelastic_mask)
    ax1.plot(dates, H_arr, color=COLOR_HEAD, lw=1.5, label='H(t) zero-ref head')
    ax1.axhline(h_c, color='black', linestyle='--', lw=1.5,
                label=f'$h_c$ = {h_c:.3f} m')
    ax1.set_ylabel('Head H(t) [m]', fontsize=14)
    ax1.set_title(
        f'Elastic epochs: {elastic_mask.sum()} ({100*elastic_mask.sum()/n:.0f}%)  |  '
        f'Inelastic (H-based): {inelastic_mask.sum()} ({100*inelastic_mask.sum()/n:.0f}%)  |  '
        f'Inelastic-virgin: {virgin_mask.sum()} ({100*virgin_mask.sum()/n:.0f}%)',
        fontsize=12
    )
    ax1.legend(fontsize=12, loc='lower left')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(labelsize=12)

    # Collinearity warning
    frac_virgin = virgin_mask.sum() / n
    if frac_virgin > COLLINEARITY_THRESHOLD:
        ax1.text(
            0.98, 0.95,
            f'⚠ V(t) active {100*frac_virgin:.0f}% of record\n'
            f'(>{100*COLLINEARITY_THRESHOLD:.0f}% → near-collinear regressors)',
            transform=ax1.transAxes, fontsize=11, color='darkred',
            ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff0f0', edgecolor='darkred')
        )

    # ------ Panel 2: V(t) ------
    ax2 = axes[1]
    shade_regimes(ax2, dates, elastic_mask, inelastic_mask)
    ax2.fill_between(dates, V_arr, 0, where=V_arr < 0,
                     color=COLOR_V, alpha=0.6, label='V(t) exceedance area')
    ax2.plot(dates, V_arr, color=COLOR_V, lw=1.5)
    ax2.axhline(0, color='gray', linestyle=':', lw=0.8)
    ax2.set_ylabel('V(t) [m]', fontsize=14)
    ax2.set_title(
        f'Virgin exceedance V(t) = min(0, cummin(H) − $h_c$)  |  '
        f'V_min = {V_arr.min():.3f} m',
        fontsize=12
    )
    ax2.legend(fontsize=12, loc='lower left')
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(labelsize=12)

    # ------ Panel 3: MLCW obs vs pred ------
    ax3 = axes[2]
    shade_regimes(ax3, dates, elastic_mask, inelastic_mask)
    ax3.plot(dates, b_arr,  color=COLOR_OBS,  lw=1.8, label='Observed cumulative MLCW')
    ax3.plot(dates, b_pred, color=COLOR_PRED, lw=1.8, linestyle='--',
             label=f'Predicted (S_ke={S_ke:.3f}, S_kv={S_kv:.3f} mm/m)')
    ax3.axhline(0, color='gray', linestyle=':', lw=0.8)
    ax3.set_xlabel('Date', fontsize=14)
    ax3.set_ylabel('Cumulative compaction [mm]', fontsize=14)
    ax3.set_title(
        f'Obs range [{b_arr.min():.1f}, {b_arr.max():.1f}] mm  |  '
        f'Pred range [{b_pred.min():.1f}, {b_pred.max():.1f}] mm  |  '
        f'R² = {r2:.3f}',
        fontsize=12
    )
    ax3.legend(fontsize=12, loc='lower left')
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(labelsize=12)

    # Legend patch for regime shading
    from matplotlib.patches import Patch
    patches = [
        Patch(facecolor=COLOR_ELASTIC, alpha=0.3, label='Elastic regime'),
        Patch(facecolor=COLOR_INELASTIC, alpha=0.3, label='Inelastic regime'),
    ]
    fig.legend(handles=patches, loc='lower center', ncol=2, fontsize=12,
               bbox_to_anchor=(0.5, -0.01))

    plt.tight_layout(rect=[0, 0.02, 1, 1])
    plt.savefig(str(out_path), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {out_path}")


# ============================================================
# DIAGNOSTICS
# ============================================================

def compute_layer_diagnostics(layer_name, H_arr, b_arr, b_pred, V_arr,
                               h_c, tau_epochs, S_ke, S_kv, delta):
    """Build the machine-readable diagnostic dict for one layer."""
    n = len(H_arr)
    elastic_mask   = H_arr > h_c
    inelastic_mask = H_arr <= h_c
    cummin_H       = np.minimum.accumulate(H_arr)
    virgin_mask    = cummin_H < h_c

    frac_virgin  = float(virgin_mask.sum() / n)
    frac_inelas  = float(inelastic_mask.sum() / n)
    below_hc     = H_arr[H_arr < h_c]
    H_mean_below = float(below_hc.mean()) if len(below_hc) > 0 else float('nan')

    collinearity_flag = frac_virgin > COLLINEARITY_THRESHOLD
    if collinearity_flag:
        col_note = (f"n_inelastic_virgin/n_total = {frac_virgin:.3f} > "
                    f"{COLLINEARITY_THRESHOLD} — V(t) near-collinear with H(t)")
    else:
        col_note = "OK"

    ratio = float(S_kv / S_ke) if S_ke > 0 else None
    r2    = compute_r2(b_arr, b_pred)

    return {
        'h_c_m':                  float(h_c),
        'tau_epochs':             int(tau_epochs),
        'n_total':                int(n),
        'n_elastic_Hbased':       int(elastic_mask.sum()),
        'n_inelastic_Hbased':     int(inelastic_mask.sum()),
        'n_inelastic_virgin':     int(virgin_mask.sum()),
        'frac_inelastic_Hbased':  round(frac_inelas, 4),
        'frac_inelastic_virgin':  round(frac_virgin, 4),
        'V_min_m':                round(float(V_arr.min()), 4),
        'H_min_m':                round(float(H_arr.min()), 4),
        'H_max_m':                round(float(H_arr.max()), 4),
        'H_mean_below_hc_m':      round(H_mean_below, 4) if np.isfinite(H_mean_below) else None,
        'S_ke_mmpm':              round(float(S_ke), 6),
        'S_kv_mmpm':              round(float(S_kv), 6),
        'delta_mmpm':             round(float(delta), 6),
        'ratio_Skv_Ske':          round(ratio, 4) if ratio is not None else None,
        'r2_cumulative':          round(r2, 4) if np.isfinite(r2) else None,
        'collinearity_flag':      collinearity_flag,
        'collinearity_note':      col_note,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 65)
    print("10_gwl_mlcw_overlay.py — TUKU regime diagnostic overlay")
    print("=" * 65)

    # Load fit results from Script 12
    fit_path = RESULTS_DIR / 'stress_strain_per_layer.json'
    if not fit_path.exists():
        raise FileNotFoundError(
            f"stress_strain_per_layer.json not found at {fit_path}\n"
            "Run 12_stress_strain_per_layer.py first."
        )
    with open(fit_path) as f:
        fit_list = json.load(f)
    fit_results = {r['layer']: r for r in fit_list}

    # Load cumulative MLCW
    print("\nLoading cumulative MLCW...")
    mlcw_df = load_cumulative_mlcw()
    print(f"  MLCW columns: {mlcw_df.columns.tolist()}")
    print(f"  Date range: {mlcw_df.index.min().date()} to {mlcw_df.index.max().date()}")

    all_diagnostics = {}

    for layer_cfg in LAYERS:
        layer = layer_cfg['layer']
        h_c        = float(layer_cfg['h_c'])
        tau_epochs = int(layer_cfg['tau_epochs'])
        gwl_file   = layer_cfg['gwl_file']
        wellcode   = str(layer_cfg['wellcode'])

        print(f"\n{'─'*60}")
        print(f"Processing {layer}  wellcode={wellcode}  tau={tau_epochs} ep  h_c={h_c:.3f} m")

        if layer not in fit_results:
            print(f"  SKIP: {layer} not in fit results.")
            continue

        fr = fit_results[layer]
        S_ke  = float(fr['S_ke_mmpm'])
        S_kv  = float(fr['S_kv_mmpm'])
        delta = float(fr['delta_mmpm'])

        # Load and zero-reference GWL
        gwl_zero, gwl_ref_val = load_gwl_absolute(gwl_file, wellcode)
        print(f"  GWL ref value at REF_DATE: {gwl_ref_val:.4f} m MSL")

        # Apply tau lag
        gwl_lagged = apply_tau_lag(gwl_zero, tau_epochs)

        # Align to MLCW grid
        if layer not in mlcw_df.columns:
            print(f"  SKIP: column '{layer}' not in MLCW DataFrame.")
            continue

        df_aligned = align_gwl_to_mlcw(mlcw_df, gwl_lagged, layer)
        n = len(df_aligned)
        if n < 10:
            print(f"  SKIP: only {n} joint points — insufficient data.")
            continue

        H_arr = df_aligned['H'].values
        b_arr = df_aligned['b'].values

        # Compute V(t) and b_pred
        V_arr  = compute_virgin_term(H_arr, h_c)
        b_pred = compute_b_pred(H_arr, V_arr, S_ke, delta)

        # Diagnostics
        diag = compute_layer_diagnostics(
            layer, H_arr, b_arr, b_pred, V_arr,
            h_c, tau_epochs, S_ke, S_kv, delta
        )
        all_diagnostics[layer] = diag

        # Print diagnostic summary
        print(f"  n_total={n}  n_elastic_H={diag['n_elastic_Hbased']}  "
              f"n_inelastic_H={diag['n_inelastic_Hbased']}  "
              f"n_inelastic_virgin={diag['n_inelastic_virgin']}")
        print(f"  frac_virgin={diag['frac_inelastic_virgin']:.3f}  "
              f"V_min={diag['V_min_m']:.4f} m  "
              f"H_min={diag['H_min_m']:.4f} m  H_mean_below_hc={diag['H_mean_below_hc_m']} m")
        print(f"  S_ke={S_ke:.4f}  S_kv={S_kv:.4f}  ratio={diag['ratio_Skv_Ske']}  R²={diag['r2_cumulative']}")
        if diag['collinearity_flag']:
            print(f"  ⚠ COLLINEARITY: {diag['collinearity_note']}")
        else:
            print(f"  Collinearity: OK")

        # Plot
        out_png = PLOT_DIR / f'{layer}_regime_overlay.png'
        plot_layer_overlay(
            layer_name=layer,
            df_aligned=df_aligned,
            h_c=h_c,
            tau_epochs=tau_epochs,
            S_ke=S_ke,
            S_kv=S_kv,
            delta=delta,
            V_arr=V_arr,
            b_pred=b_pred,
            out_path=out_png,
            diag=diag,
        )

    # Write machine-readable diagnostics
    out_json = RESULTS_DIR / 'regime_overlay_diagnostics.json'
    with open(out_json, 'w') as f:
        json.dump(all_diagnostics, f, indent=2)
    print(f"\nDiagnostics written: {out_json}")

    # ---- Summary table ----
    print("\n" + "=" * 90)
    print(f"{'Layer':<6} {'h_c':>7} {'tau':>5} {'n':>5} "
          f"{'n_el_H':>8} {'n_in_H':>8} {'n_virg':>8} "
          f"{'frac_v':>8} {'ratio':>8} {'R²':>7} {'collin':>8}")
    print("-" * 90)
    for layer, d in all_diagnostics.items():
        ratio_str  = f"{d['ratio_Skv_Ske']:.2f}×" if d['ratio_Skv_Ske'] is not None else 'undef'
        r2_str     = f"{d['r2_cumulative']:.3f}"   if d['r2_cumulative']  is not None else 'n/a'
        collin_str = '⚠ YES' if d['collinearity_flag'] else 'ok'
        print(f"{layer:<6} {d['h_c_m']:>7.3f} {d['tau_epochs']:>5} {d['n_total']:>5} "
              f"{d['n_elastic_Hbased']:>8} {d['n_inelastic_Hbased']:>8} {d['n_inelastic_virgin']:>8} "
              f"{d['frac_inelastic_virgin']:>8.3f} {ratio_str:>8} {r2_str:>7} {collin_str:>8}")

    print("\nPhysical interpretation flags:")
    for layer, d in all_diagnostics.items():
        if d['collinearity_flag']:
            print(f"  {layer}: h_c = {d['h_c_m']:.3f} m too shallow — "
                  f"V(t) active {100*d['frac_inelastic_virgin']:.0f}% of record. "
                  f"Well may not represent consolidating layer.")
        if d['S_ke_mmpm'] == 0.0:
            print(f"  {layer}: S_ke = 0 — permanently inelastic. "
                  f"H_min = {d['H_min_m']:.3f} m vs h_c = {d['h_c_m']:.3f} m. "
                  f"Elastic regime unidentifiable from 2015–2026 record.")
    print("\nDone.")


if __name__ == '__main__':
    main()
