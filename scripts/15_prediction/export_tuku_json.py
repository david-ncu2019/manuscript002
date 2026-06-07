"""
Export comprehensive machine-readable evaluation JSON for TUKU.
Reads walkforward_rmse.csv — all RMSE/skill values are leakage-free per-fold estimates.

Usage:
    python scripts/15_prediction/export_tuku_json.py
    python scripts/15_prediction/export_tuku_json.py --station TUKU --csv results/prediction_v1/walkforward_rmse.csv
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV     = ROOT / 'results/prediction_v1/walkforward_rmse.csv'
DEFAULT_OUT_DIR = ROOT / 'results/prediction_v1'
LAYERS_ORDER    = ['F1', 'T1', 'F2', 'T2', 'F3', 'F4']

METRIC_COLS = [
    'RMSE_tier1', 'RMSE_tier2', 'RMSE_persistence', 'RMSE_trend_extrap',
    'skill_tier1_vs_persistence', 'skill_tier1_vs_trend',
    'skill_tier2_vs_persistence', 'skill_tier2_vs_trend',
    'fbar_per_fold', 'r1_per_fold', 'n_holdout_epochs',
]


def _safe(v):
    """Convert numpy scalar or nan to Python native for JSON."""
    if v is None:
        return None
    try:
        if np.isnan(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def fold_record(row: pd.Series) -> dict:
    rec = {'fold_year': int(row['fold_year']), 'is_fold1': bool(row['is_fold1']),
           'tier2_available': bool(row['tier2_available'])}
    for col in METRIC_COLS:
        rec[col] = _safe(row[col]) if col in row.index else None
    return rec


def layer_summary(layer_df: pd.DataFrame) -> dict:
    folds_sorted = layer_df.sort_values('fold_year')
    fold1_rows   = layer_df[layer_df['is_fold1'] == True]
    fold1        = fold_record(fold1_rows.iloc[0]) if len(fold1_rows) > 0 else None

    median_cols = ['RMSE_tier1', 'RMSE_tier2', 'RMSE_persistence', 'RMSE_trend_extrap',
                   'skill_tier1_vs_persistence', 'skill_tier1_vs_trend',
                   'skill_tier2_vs_persistence', 'skill_tier2_vs_trend']
    medians = {}
    for col in median_cols:
        vals = layer_df[col].dropna().values
        medians[col] = _safe(float(np.median(vals))) if len(vals) > 0 else None

    return {
        'fold1':               fold1,
        'folds':               [fold_record(r) for _, r in folds_sorted.iterrows()],
        'median_across_folds': medians,
    }


def main():
    p = argparse.ArgumentParser(description='Export TUKU evaluation JSON.')
    p.add_argument('--station', default='TUKU')
    p.add_argument('--csv',     type=Path, default=DEFAULT_CSV)
    p.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    args = p.parse_args()

    if not args.csv.exists():
        print(f'ERROR: walkforward CSV not found: {args.csv}')
        sys.exit(1)

    df = pd.read_csv(args.csv)
    df = df[df['station'] == args.station]
    if df.empty:
        print(f'ERROR: no rows for station {args.station}')
        sys.exit(1)

    # Summary counts
    n_total   = len(df)
    n_beat_ps = int((df['skill_tier1_vs_persistence'] > 0).sum())
    n_beat_tr = int((df['skill_tier1_vs_trend'] > 0).sum())

    # Tier 2 effect on F2 specifically (seasonal is active there)
    f2_df = df[df['layer'] == 'F2']
    tier2_hurts_f2 = bool((f2_df['RMSE_tier2'] > f2_df['RMSE_tier1']).all()) if len(f2_df) > 0 else None

    fold1_df = df[df['is_fold1'] == True]
    fold1_med_skill = _safe(float(fold1_df['skill_tier1_vs_trend'].median())) if len(fold1_df) > 0 else None

    layers_present = [l for l in LAYERS_ORDER if l in df['layer'].unique()]
    layers_dict = {}
    for layer in layers_present:
        layers_dict[layer] = layer_summary(df[df['layer'] == layer])

    out = {
        'metadata': {
            'station':     args.station,
            'calibration': 'leakage-free per-fold (train epochs: year < fold_year)',
            'source_csv':  args.csv.name,
            'generated':   str(date.today()),
            'note':        (
                'fbar_per_fold estimated from training window only. '
                'Full-record fbar in reconstruction_metrics.csv is DIAGNOSTIC ONLY '
                'and must not enter the prediction path.'
            ),
        },
        'summary': {
            'n_layer_fold_pairs':          n_total,
            'n_layers':                    len(layers_present),
            'n_fold_years':                len(df['fold_year'].unique()),
            'n_beating_persistence':       n_beat_ps,
            'n_beating_trend':             n_beat_tr,
            'pct_beating_persistence':     _safe(round(100 * n_beat_ps / n_total, 1)),
            'pct_beating_trend':           _safe(round(100 * n_beat_tr / n_total, 1)),
            'tier2_hurts_f2_all_folds':    tier2_hurts_f2,
            'fold1_median_skill_vs_trend': fold1_med_skill,
            'gate_assessment': (
                'TUKU does not clearly clear the interpolation gate: '
                'F2 seasonal (Tier 2) degrades all 4 folds; '
                'F3 RMSE is unstable across folds (range 4.7-23.4 mm); '
                'Tier 1 vs trend skill is mixed at F2 (median ~-0.1).'
            ),
        },
        'layers': layers_dict,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f'{args.station}_evaluation.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f'Saved → {out_path}')
    print(f'  Layers: {layers_present}')
    print(f'  Layer×fold pairs: {n_total}')
    print(f'  Beating persistence: {n_beat_ps}/{n_total} ({100*n_beat_ps//n_total}%)')
    print(f'  Beating trend extrap: {n_beat_tr}/{n_total} ({100*n_beat_tr//n_total}%)')
    print(f'  Tier 2 hurts F2 all folds: {tier2_hurts_f2}')
    print(f'  Fold-1 median skill vs trend: {fold1_med_skill}')


if __name__ == '__main__':
    main()
