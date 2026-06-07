"""
TUKU per-layer timeseries figures.
One figure per layer (6 total): 4 subplots vertically, one per fold year.
Each subplot: mlcw_obs (black), tier1_pred (blue), tier2_pred (orange, if available),
              persistence (grey dashed), trend_extrap (green dashed).

Usage:
    python scripts/15_prediction/plot_tuku_timeseries.py
    python scripts/15_prediction/plot_tuku_timeseries.py --station TUKU --epoch-csv results/prediction_v1/TUKU_epoch_predictions.csv
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

A4_W, A4_H, DPI = 11.7, 8.3, 300
LAYERS_ORDER = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EPOCH_CSV = ROOT / 'results/prediction_v1/TUKU_epoch_predictions.csv'
DEFAULT_OUT_DIR   = ROOT / 'results/prediction_v1/figures'


def plot_layer(df_layer: pd.DataFrame, layer: str, out_dir: Path) -> None:
    folds = sorted(df_layer['fold_year'].unique())
    n_folds = len(folds)
    fig_h = max(A4_H, 2.5 * n_folds)
    fig, axes = plt.subplots(n_folds, 1, figsize=(A4_W, fig_h), dpi=DPI,
                             sharex=False, squeeze=False)

    for row_i, fold_yr in enumerate(folds):
        ax = axes[row_i, 0]
        sub = df_layer[df_layer['fold_year'] == fold_yr].sort_values('datetime')
        is_fold1 = bool(sub['is_fold1'].iloc[0]) if len(sub) > 0 else False
        tier2_ok = bool(sub['tier2_available'].iloc[0]) if len(sub) > 0 else False

        dates = sub['datetime'].values

        ax.plot(dates, sub['mlcw_obs'].values,    color='black',   lw=1.5, label='MLCW observed')
        ax.plot(dates, sub['tier1_pred'].values,  color='steelblue', lw=1.5, label='Tier 1 (fbar×InSAR)')
        if tier2_ok:
            ax.plot(dates, sub['tier2_pred'].values, color='darkorange', lw=1.5, label='Tier 2 (+seasonal)')
        ax.plot(dates, sub['persistence'].values, color='grey',    lw=1.0, ls='--', label='Persistence')
        ax.plot(dates, sub['trend_extrap'].values, color='green',  lw=1.0, ls='--', label='Trend extrap')

        fold1_tag = '  ← fold-1 / most critical' if is_fold1 else ''
        ax.set_title(f'Hold-out {fold_yr}{fold1_tag}', fontsize=9, loc='left')
        ax.set_ylabel('Cumul. compaction (mm)', fontsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right', fontsize=7)
        ax.tick_params(axis='y', labelsize=7)
        ax.grid(True, alpha=0.3)

        if row_i == 0:
            ax.legend(fontsize=7, loc='upper left', framealpha=0.7)

    station = df_layer['station'].iloc[0] if len(df_layer) > 0 else 'UNKNOWN'
    fig.suptitle(f'{station} — Layer {layer}: walk-forward predictions vs observed MLCW',
                 fontsize=11, fontweight='bold', y=1.002)
    fig.tight_layout()
    out_path = out_dir / f'{station}_{layer}_timeseries.png'
    fig.savefig(out_path, dpi=DPI, bbox_inches='tight', format='png')
    plt.close(fig)
    print(f'  Saved → {out_path.name}')


def main():
    p = argparse.ArgumentParser(description='Plot TUKU per-layer timeseries figures.')
    p.add_argument('--station',    default='TUKU')
    p.add_argument('--epoch-csv',  type=Path, default=DEFAULT_EPOCH_CSV)
    p.add_argument('--out-dir',    type=Path, default=DEFAULT_OUT_DIR)
    args = p.parse_args()

    if not args.epoch_csv.exists():
        print(f'ERROR: epoch CSV not found: {args.epoch_csv}')
        sys.exit(1)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.epoch_csv, parse_dates=['datetime'])
    df = df[df['station'] == args.station]
    if df.empty:
        print(f'ERROR: no rows for station {args.station} in {args.epoch_csv.name}')
        sys.exit(1)

    layers = [l for l in LAYERS_ORDER if l in df['layer'].unique()]
    print(f'\nPlotting {len(layers)} layers for {args.station}:')
    for layer in layers:
        plot_layer(df[df['layer'] == layer].copy(), layer, args.out_dir)

    print(f'\nDone — {len(layers)} figures saved to {args.out_dir}')


if __name__ == '__main__':
    main()
