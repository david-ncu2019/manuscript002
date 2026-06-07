import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import argparse
import pandas as pd
import numpy as np
import h5py
from multiprocessing import Pool
from pathlib import Path
from mintpy.utils import readfile

# Add Interpolation Engine to path
ENGINE_PATH = "/mnt/hgfs/1000_SCRIPTS/004_Project003/20260423_Interp_Engine"
if ENGINE_PATH not in sys.path:
    sys.path.append(ENGINE_PATH)

try:
    from src.engines.kriging import AnisotropicKriging
    from src.preprocessor import TrendProcessor
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Check if ENGINE_PATH is correct: {ENGINE_PATH}")

def parse_args():
    parser = argparse.ArgumentParser(description='Interpolate InSAR TS to GNSS stations.')
    parser.add_argument('--input', type=str, required=True, help='Path to input vert_regts_msk.h5')
    parser.add_argument('--stations', type=str, required=True, help='Path to station CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV')
    parser.add_argument('--trial', type=int, default=0, help='Number of time steps to process for trial (0 for all)')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    
    # Engine parameters
    parser.add_argument('--n-trials', type=int, default=100, help='Number of trials for Kriging parameter optimization')
    parser.add_argument('--n-splits', type=int, default=3, help='Number of splits for cross-validation')
    parser.add_argument('--max-anisotropy', type=float, default=10.0, help='Maximum allowed anisotropy ratio')
    parser.add_argument('--engine-workers', type=int, default=1, help='Number of parallel workers for parameter searching per date')
    parser.add_argument('--param-cache', type=str, default=None, help='Path to JSON file to load/save optimal Kriging parameters')
    
    # Preprocessing parameters
    parser.add_argument('--poly-order', type=int, default=1, help='Order of polynomial detrending')
    parser.add_argument('--max-points', type=int, default=5000, help='Maximum number of InSAR points to use for fitting')
    parser.add_argument('--buffer-radius', type=float, default=None, help='Buffer radius in meters to filter InSAR points around stations')
    
    return parser.parse_args()

def get_insar_coords(atr):
    """Generate X, Y UTM coordinate arrays for InSAR grid."""
    x0 = float(atr['X_FIRST'])
    y0 = float(atr['Y_FIRST'])
    dx = float(atr['X_STEP'])
    dy = float(atr['Y_STEP'])
    width = int(atr['WIDTH'])
    length = int(atr['LENGTH'])
    
    x = x0 + dx * np.arange(width)
    y = y0 + dy * np.arange(length)
    xv, yv = np.meshgrid(x, y)
    return xv, yv

def interpolate_worker(date_info):
    input_file, date_idx, date_str, insar_coords, station_coords, valid_spatial_indices, args_dict, cache_entry = date_info
    
    # Suppress numerical warnings during optimization to keep output clean
    import warnings
    warnings.filterwarnings('ignore', category=RuntimeWarning, message='overflow encountered in power')
    
    with h5py.File(input_file, 'r') as f:
        # Read only the slice for this date
        data = f['timeseries'][date_idx, :, :].flatten()
    
    if valid_spatial_indices is not None:
        data = data[valid_spatial_indices]
    
    # Mask invalid pixels (NaN or 0)
    mask = ~np.isnan(data) & (data != 0)
    if np.sum(mask) < 10:
        return np.zeros(len(station_coords)), None, None
    
    X_train = insar_coords[mask]
    y_train = data[mask]
    
    print(f"[{date_str}] After masking: X_train shape={X_train.shape}, y_train shape={y_train.shape}", flush=True)
    
    # Spatial thinning if too many points
    max_pts = args_dict['max_points']
    if len(y_train) > max_pts:
        np.random.seed(42 + date_idx) # Deterministic for this date
        idx = np.random.choice(len(y_train), max_pts, replace=False)
        X_train = X_train[idx]
        y_train = y_train[idx]
        print(f"[{date_str}] After max_points thinning: X_train shape={X_train.shape}, y_train shape={y_train.shape}", flush=True)
    
    from scipy.spatial.distance import pdist, squareform
    dist_mat = squareform(pdist(X_train))
    np.fill_diagonal(dist_mat, np.inf)
    min_dist = dist_mat.min()
    print(f"[{date_str}] Min distance between points: {min_dist:.1f}", flush=True)
    
    # Simple jitter to prevent exact 0 distances which crash Kriging/GP
    if min_dist < 1e-3:
        print(f"[{date_str}] Adding jitter to prevent zero-distances...", flush=True)
        np.random.seed(42 + date_idx)
        X_train += np.random.uniform(-1e-2, 1e-2, size=X_train.shape)
    
    # Detrend
    print(f"[{date_str}] Before TrendProcessor fitting...", flush=True)
    tp = TrendProcessor(order=args_dict['poly_order'])
    tp.fit(X_train[:, 0], X_train[:, 1], y_train)
    y_detrended = tp.detrend(X_train[:, 0], X_train[:, 1], y_train)
    print(f"[{date_str}] After TrendProcessor fitting.", flush=True)
    
    # Kriging
    ak = AnisotropicKriging(
        n_trials=args_dict['n_trials'], 
        n_splits=args_dict['n_splits'], 
        max_anisotropy=args_dict['max_anisotropy'],
        n_jobs=args_dict['engine_workers'],
        verbose=True
    )
    
    if cache_entry is not None:
        print(f"[{date_str}] CACHE HIT! Bypassing Optuna search...", flush=True)
        best_model_name = cache_entry['model_name']
        best_params = cache_entry['params']
        ak.fit_with_known_params(X_train, y_detrended, best_model_name, best_params)
    else:
        print(f"[{date_str}] Initializing AnisotropicKriging and fitting...", flush=True)
        ak.fit(X_train, y_detrended)
        best_model_name = ak.best_model_name_
        best_params = ak.best_params_
    
    # Predict
    y_pred_detrended = ak.predict(station_coords)
    
    # Retrend
    y_pred = tp.retrend(station_coords[:, 0], station_coords[:, 1], y_pred_detrended)
    
    print(f"  Finished date index {date_idx} ({date_str}).", flush=True)
    return y_pred, best_model_name, best_params

if __name__ == "__main__":
    args = parse_args()
    print(f"Input: {args.input}")
    print(f"Stations: {args.stations}")
    print(f"Output: {args.output}")

    atr = readfile.read_attribute(args.input)
    xv, yv = get_insar_coords(atr)
    insar_coords = np.column_stack((xv.flatten(), yv.flatten()))
    
    df_stations = pd.read_csv(args.stations)
    station_coords = df_stations[['X_UTM50N', 'Y_UTM50N']].values
    print(f"Loaded {len(df_stations)} stations.")
    
    valid_spatial_indices = None
    if args.buffer_radius is not None and args.buffer_radius > 0:
        from scipy.spatial import cKDTree
        print(f"Building KDTree for {len(insar_coords)} InSAR points...")
        tree = cKDTree(insar_coords)
        print(f"Querying KDTree with buffer radius {args.buffer_radius}m...")
        indices = tree.query_ball_point(station_coords, r=args.buffer_radius)
        non_empty_indices = [idx for idx in indices if len(idx) > 0]
        if non_empty_indices:
            valid_spatial_indices = np.unique(np.concatenate(non_empty_indices))
            insar_coords = insar_coords[valid_spatial_indices]
            print(f"Filtered to {len(insar_coords)} InSAR points within buffer.")
        else:
            print("Warning: No InSAR points found within the buffer radius for any station.")
            valid_spatial_indices = np.array([], dtype=int)
            insar_coords = insar_coords[valid_spatial_indices]
    
    with h5py.File(args.input, 'r') as f:
        dates = [d.decode('utf-8') for d in f['date'][:]]
    
    # Filter dates between 20150301 and 20251201
    target_dates = [d for d in dates if '20150301' <= d <= '20251201']
    if args.trial > 0:
        target_dates = target_dates[:args.trial]
    
    print(f"Processing {len(target_dates)} dates...")
    if len(target_dates) > 0:
        print(f"First few dates: {target_dates[:5]}")

    # Prepare cache
    import json
    kriging_cache = {}
    if args.param_cache and os.path.exists(args.param_cache):
        print(f"Loading parameter cache from {args.param_cache}...")
        try:
            with open(args.param_cache, 'r') as f:
                kriging_cache = json.load(f)
            print(f"Loaded {len(kriging_cache)} cached dates.")
        except Exception as e:
            print(f"Warning: Could not load cache file: {e}")

    # Prepare tasks for pool
    args_dict = vars(args)
    tasks = []
    for d in target_dates:
        idx = dates.index(d)
        cache_entry = kriging_cache.get(d)
        tasks.append((args.input, idx, d, insar_coords, station_coords, valid_spatial_indices, args_dict, cache_entry))
    
    import multiprocessing as mp
    print(f"Starting parallel processing with {args.workers} workers...")
    with mp.get_context('spawn').Pool(args.workers) as pool:
        results = pool.map(interpolate_worker, tasks)
    
    # Assembly
    print("Assembling results...")
    cache_updated = False
    for i, d in enumerate(target_dates):
        y_pred, best_model_name, best_params = results[i]
        df_stations[f"D{d}"] = y_pred
        
        # Update cache if this was a newly computed model
        if best_model_name is not None and best_params is not None:
            if d not in kriging_cache:
                kriging_cache[d] = {'model_name': best_model_name, 'params': best_params}
                cache_updated = True
    
    df_stations.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")

    if args.param_cache and cache_updated:
        print(f"Saving updated parameter cache to {args.param_cache}...")
        try:
            with open(args.param_cache, 'w') as f:
                json.dump(kriging_cache, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save cache file: {e}")

