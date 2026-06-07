"""
InSAR-to-MLCW compaction prediction pipeline.
Walk-forward temporal validation + spatial kriging to 8,577 grid points.

Usage:
    # TUKU pilot, fold 1 only, no kriging:
    python scripts/15_prediction/main.py --stations TUKU --folds 2022 --krige none

    # Full run, all stations, all folds, ordinary kriging:
    python scripts/15_prediction/main.py --stations all --folds 2022 2023 2024 2025 --krige ordinary

    # IDW spatial baseline:
    python scripts/15_prediction/main.py --stations all --krige idw
"""
import argparse
import logging
import sys
from pathlib import Path


import importlib.util as _ilu

def _load_module(name, file_path):
    spec = _ilu.spec_from_file_location(name, file_path)
    mod  = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[name] = mod
    return mod

_PKG = Path(__file__).resolve().parent
P              = _load_module('pred_paths',        _PKG / 'paths.py')
io_loader      = _load_module('pred_io_loader',    _PKG / 'io_loader.py')
walkforward    = _load_module('pred_walkforward',  _PKG / 'walkforward.py')
spatial_kriging = _load_module('pred_spatial',     _PKG / 'spatial_kriging.py')
reporter       = _load_module('pred_reporter',     _PKG / 'reporter.py')


# ── Known station list ────────────────────────────────────────────────────────
ALL_STATIONS = [
    "ANHE", "ANNAN", "BEICHEN", "CANLIN", "DONGGUANG", "DONGSHI", "ERLUN",
    "FENGAN", "FENGRONG", "GUANGFU", "HAIFENG", "HONGLUN", "HUNAN", "HUWEI",
    "JIANYANG", "JIAXING", "JIUZHUANG", "KECUO", "LONGYAN", "NANGUANG",
    "NEILIAO", "QIAOYI", "TANQIFENXIAO", "TUKU", "XIGANG", "XINGHUA",
    "XINJIE", "XINPI", "XINSHENG", "XINXING", "XIUTAN", "XIZHOU", "YIWU",
    "YUANCHANG", "ZHENGMIN", "ZHENNAN", "ZHUTANG",
]


def parse_args():
    p = argparse.ArgumentParser(
        description='InSAR-to-MLCW compaction prediction with walk-forward validation '
                    'and spatial kriging.'
    )
    p.add_argument('--stations', nargs='+', default=['all'],
                   help="Station names or 'all' (default: all)")
    p.add_argument('--folds', nargs='+', type=int, default=[2022, 2023, 2024, 2025],
                   help='Hold-out years (default: 2022 2023 2024 2025)')
    p.add_argument('--krige', choices=['ordinary', 'idw', 'none'], default='ordinary',
                   help='Kriging method (default: ordinary)')
    p.add_argument('--output-dir', type=Path, default=P.OUTPUT_DIR,
                   help=f'Output root directory (default: {P.OUTPUT_DIR})')
    p.add_argument('--insar-file', type=Path, default=P.INSAR_STATIONS_FEATHER,
                   help='Override InSAR stations feather path')
    p.add_argument('--harmonic-dir', type=Path, default=P.HARMONIC_DIR,
                   help='Override seasonal harmonic results directory')
    p.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING'], default='INFO')
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level),
                        format='%(levelname)s %(message)s')
    log = logging.getLogger('prediction')

    stations = ALL_STATIONS if args.stations == ['all'] else args.stations
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Output directory: {output_dir}")
    log.info(f"Stations ({len(stations)}): {', '.join(stations)}")
    log.info(f"Fold years: {args.folds}")
    log.info(f"Kriging method: {args.krige}")

    # ── [1/6] Load data ───────────────────────────────────────────────────────
    print("\n[1/6] Loading data")
    insar_df = io_loader.load_insar_stations(args.insar_file)
    log.info(f"  InSAR stations: {insar_df.shape[0]} stations × {insar_df.shape[1]} cols")

    if args.krige != 'none':
        insar_grid_df = io_loader.load_insar_grid(P.INSAR_GRID_FEATHER)
        log.info(f"  InSAR grid: {insar_grid_df.shape[0]} points")
    else:
        insar_grid_df = None

    # ── [2/6] Walk-forward validation ─────────────────────────────────────────
    print("\n[2/6] Walk-forward validation")
    all_results = []
    skipped = []
    station_fbars = []   # for kriging: station, layer, fbar, coords

    for stn in stations:
        try:
            insar_series = io_loader.insar_series_for_station(insar_df, stn)
        except KeyError:
            skipped.append({'station': stn, 'reason': 'not in InSAR feather'})
            log.warning(f"  SKIP {stn}: not in InSAR feather")
            continue

        try:
            mlcw_df = io_loader.load_mlcw_grouped(stn, P.MLCW_GROUPED_DIR)
        except FileNotFoundError as e:
            skipped.append({'station': stn, 'reason': str(e)})
            log.warning(f"  SKIP {stn}: {e}")
            continue

        # Load harmonic files — degrade to Tier 1 only if missing
        metrics_df = None
        peryear_df = None
        insar_harmonic_ts = None
        try:
            metrics_df      = io_loader.load_reconstruction_metrics(stn, args.harmonic_dir)
            peryear_df      = io_loader.load_seasonal_stability(stn, args.harmonic_dir)
            insar_harmonic_ts = io_loader.load_insar_harmonic_ts(stn, args.harmonic_dir)
        except FileNotFoundError as e:
            log.debug(f"  {stn}: harmonic files missing — Tier 1 only ({e})")

        result_df, epoch_df = walkforward.run_walkforward(
            station=stn,
            insar_series=insar_series,
            mlcw_grouped=mlcw_df,
            metrics_df=metrics_df,
            peryear_df=peryear_df if peryear_df is not None else None,
            fold_years=args.folds,
            insar_harmonic_ts=insar_harmonic_ts,
        )

        if result_df.empty:
            skipped.append({'station': stn, 'reason': 'no valid walk-forward rows'})
            log.warning(f"  SKIP {stn}: no valid walk-forward rows")
            continue

        all_results.append(result_df)

        # Save per-epoch series for this station
        if not epoch_df.empty:
            ep_path = output_dir / f'{stn}_epoch_predictions.csv'
            epoch_df.to_csv(ep_path, index=False)
            log.debug(f"  {stn}: saved per-epoch series ({len(epoch_df)} rows) → {ep_path.name}")

        # Collect per-station fbar (from fold 1, training years ≤ 2021) for kriging
        fold1_rows = result_df[result_df['is_fold1'] == True]
        if not fold1_rows.empty and 'X_TWD97' in insar_df.columns:
            x_twd = float(insar_df.loc[stn, 'X_TWD97']) if stn in insar_df.index else float('nan')
            y_twd = float(insar_df.loc[stn, 'Y_TWD97']) if stn in insar_df.index else float('nan')
            for _, row in fold1_rows.iterrows():
                station_fbars.append({
                    'station': stn,
                    'layer':   row['layer'],
                    'fbar':    row['fbar_per_fold'],
                    'X_TWD97': x_twd,
                    'Y_TWD97': y_twd,
                })

        fold1_F2 = result_df[(result_df['layer'] == 'F2') & result_df['is_fold1']]
        if not fold1_F2.empty:
            r = fold1_F2.iloc[0]
            log.info(f"  {stn} F2 fold-2022: RMSE_T1={r['RMSE_tier1']:.3f}mm  "
                     f"skill_vs_trend={r['skill_tier1_vs_trend']:.3f}")

    if not all_results:
        print("ERROR: No valid results. Check station names and input files.")
        sys.exit(1)

    results_df = pd.concat(all_results, ignore_index=True)
    log.info(f"  Walk-forward complete: {len(results_df)} rows, {len(skipped)} skipped")

    # ── [3/6] Spatial kriging ─────────────────────────────────────────────────
    grid_fbar_df = None
    if args.krige != 'none' and station_fbars and insar_grid_df is not None:
        print(f"\n[3/6] Spatial kriging ({args.krige})")
        sf_df = pd.DataFrame(station_fbars)
        grid_coords = insar_grid_df[['X_TWD97', 'Y_TWD97']].copy()
        grid_fbar_df = spatial_kriging.krige_fbar_to_grid(sf_df, grid_coords, method=args.krige)
        log.info(f"  Kriging complete: {len(grid_fbar_df)} grid×layer rows")
    else:
        print("\n[3/6] Spatial kriging — skipped")

    # ── [4/6] Spatial LOO-CV ─────────────────────────────────────────────────
    loo_df = None
    if args.krige != 'none' and station_fbars:
        print(f"\n[4/6] Spatial LOO-CV")
        sf_df = pd.DataFrame(station_fbars)
        loo_df = spatial_kriging.run_spatial_loo_cv(sf_df, method=args.krige)
        log.info(f"  LOO-CV complete: {len(loo_df)} station×layer rows")
    else:
        print("\n[4/6] Spatial LOO-CV — skipped")

    # ── [5/6] Writing outputs ─────────────────────────────────────────────────
    print("\n[5/6] Writing outputs")
    reporter.write_walkforward_csv(results_df, output_dir)
    reporter.write_comparison_csv(results_df, output_dir)
    if skipped:
        reporter.write_stations_skipped_csv(skipped, output_dir)
    if loo_df is not None and not loo_df.empty:
        reporter.write_spatial_loo_csv(loo_df, output_dir)
    if grid_fbar_df is not None and not grid_fbar_df.empty:
        reporter.write_grid_fbar_csv(grid_fbar_df, output_dir)

    reporter.plot_walkforward_heatmap(results_df, output_dir)
    if grid_fbar_df is not None:
        for layer in ['F2', 'F3']:
            reporter.plot_spatial_fbar_maps(grid_fbar_df, layer, output_dir)
    if loo_df is not None and not loo_df.empty:
        reporter.plot_loo_cv_error_map(loo_df, output_dir)

    # ── [6/6] Done ────────────────────────────────────────────────────────────
    print(f"\n[6/6] Done — results in {output_dir}")
    fold1 = results_df[results_df['is_fold1']]
    if not fold1.empty:
        med_t1 = fold1['skill_tier1_vs_trend'].median()
        print(f"       Fold-1 median skill (Tier1 vs trend): {med_t1:+.3f}")
    return results_df


if __name__ == '__main__':
    import pandas as pd  # noqa: F811
    main()
