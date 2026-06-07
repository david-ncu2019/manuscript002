#!/usr/bin/env python3
"""
IDW interpolation of HDF5 time-series to Shapefile points with multiprocessing support.
Incorporates KDTree pre-filtering for massive speedups.
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import argparse
import h5py
import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from sklearn.neighbors import KNeighborsRegressor, NearestNeighbors
from mintpy.utils import readfile

def parse_args():
    parser = argparse.ArgumentParser(description='Interpolate InSAR TS to Shapefile stations using IDW.')
    parser.add_argument('--input', type=str, required=True, help='Path to input InSAR HDF5 file (e.g., vert_regts_msk.h5)')
    parser.add_argument('--stations', type=str, required=True, help='Path to target Shapefile (.shp)')
    parser.add_argument('--output', type=str, required=True, help='Path to output file (.shp or .gpkg). GeoPackage (.gpkg) recommended for >255 dates.')
    parser.add_argument('--mask', type=str, default=None, help='Path to optional mask HDF5 file')
    
    parser.add_argument('--trial', type=int, default=0, help='Number of time steps to process for trial (0 for all)')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    
    # IDW parameters
    parser.add_argument('--neighbors', type=int, default=12, help='Number of neighbors for IDW')
    parser.add_argument('--buffer-radius', type=float, default=1000.0, help='KDTree pre-filtering buffer and max distance for IDW (meters)')
    
    return parser.parse_args()

def get_insar_coords(atr):
    """Generate X, Y geographic coordinate arrays for InSAR grid."""
    x0 = float(atr['X_FIRST'])
    y0 = float(atr['Y_FIRST'])
    dx = float(atr['X_STEP'])
    dy = float(atr['Y_STEP'])
    width = int(atr['WIDTH'])
    length = int(atr['LENGTH'])
    
    x = x0 + dx * np.arange(width) + dx / 2.0
    y = y0 + dy * np.arange(length) + dy / 2.0
    xv, yv = np.meshgrid(x, y)
    return xv, yv

def idw_worker(date_info):
    input_file, date_idx, date_str, insar_coords, target_coords, valid_spatial_indices, n_neighbors, max_distance, mask_data = date_info
    
    with h5py.File(input_file, 'r') as f:
        data = f['timeseries'][date_idx, :, :].flatten()
        
    if mask_data is not None:
        data = np.where(mask_data, data, np.nan)
        
    if valid_spatial_indices is not None:
        data = data[valid_spatial_indices]
        
    # Mask invalid pixels (NaN or 0)
    valid_mask = ~np.isnan(data) & (data != 0)
    
    if np.sum(valid_mask) < 1:
        return np.full(len(target_coords), np.nan)
        
    X_train = insar_coords[valid_mask]
    y_train = data[valid_mask]
    
    # IDW using KNeighborsRegressor
    try:
        knn = KNeighborsRegressor(
            n_neighbors=min(n_neighbors, len(y_train)),
            weights="distance",
            p=2,
            metric="minkowski"
        )
        knn.fit(X_train, y_train)
        
        predictions = knn.predict(target_coords)
        
        # Apply distance constraint
        if max_distance is not None:
            nn = NearestNeighbors(n_neighbors=1)
            nn.fit(X_train)
            distances, _ = nn.kneighbors(target_coords)
            predictions[distances.flatten() > max_distance] = np.nan
            
        print(f"  Finished date index {date_idx} ({date_str}).", flush=True)
        return predictions
        
    except Exception as e:
        print(f"Warning: IDW failed for date {date_str}: {e}", flush=True)
        return np.full(len(target_coords), np.nan)

def main():
    args = parse_args()
    print("="*50)
    print(f"Input: {args.input}")
    print(f"Stations: {args.stations}")
    print(f"Output: {args.output}")
    print("="*50)

    # 1. Read HDF5 Metadata
    print(f"Reading HDF5 metadata...")
    atr = readfile.read_attribute(args.input)
    h5_epsg = int(atr.get("EPSG", 0))
    if h5_epsg == 0:
        print("Warning: Could not read EPSG from HDF5 metadata. Assuming EPSG:32650.")
        h5_epsg = 32650
        
    xv, yv = get_insar_coords(atr)
    insar_coords = np.column_stack((xv.flatten(), yv.flatten()))

    # 2. Load Shapefile and Handle CRS
    print(f"Loading shapefile...")
    gdf = gpd.read_file(args.stations)
    print(f"Loaded {len(gdf)} target points.")
    
    if gdf.crs is None:
        print(f"Warning: Shapefile has no CRS. Assuming EPSG:{h5_epsg}")
        gdf.set_crs(epsg=h5_epsg, inplace=True)
    elif gdf.crs.to_epsg() != h5_epsg:
        print(f"Reprojecting Shapefile from EPSG:{gdf.crs.to_epsg()} to EPSG:{h5_epsg} to match InSAR data...")
        gdf = gdf.to_crs(epsg=h5_epsg)
        
    target_coords = np.column_stack([gdf.geometry.x.values, gdf.geometry.y.values])

    # 3. Load Mask (Optional)
    mask_data = None
    if args.mask and os.path.exists(args.mask):
        print(f"Loading mask from {args.mask}...")
        with h5py.File(args.mask, 'r') as f:
            mask_data = f['mask'][:].flatten()

    # 4. KDTree Pre-filtering
    valid_spatial_indices = None
    if args.buffer_radius is not None and args.buffer_radius > 0:
        print(f"Building KDTree for {len(insar_coords)} InSAR points...")
        tree = cKDTree(insar_coords)
        print(f"Querying KDTree with buffer radius {args.buffer_radius}m...")
        indices = tree.query_ball_point(target_coords, r=args.buffer_radius)
        non_empty_indices = [idx for idx in indices if len(idx) > 0]
        if non_empty_indices:
            valid_spatial_indices = np.unique(np.concatenate(non_empty_indices))
            insar_coords = insar_coords[valid_spatial_indices]
            if mask_data is not None:
                mask_data = mask_data[valid_spatial_indices]
            print(f"Filtered to {len(insar_coords)} valid InSAR points within buffer.")
        else:
            print("Warning: No InSAR points found within the buffer radius for any station.")
            valid_spatial_indices = np.array([], dtype=int)
            insar_coords = insar_coords[valid_spatial_indices]

    # 5. Extract Dates
    with h5py.File(args.input, 'r') as f:
        dates = [d.decode('utf-8') for d in f['date'][:]]
        
    # target_dates = [d for d in dates if '20150301' <= d <= '20251201']
    target_dates = [d for d in dates if '20150101' <= d <= '20251231']
    if args.trial > 0:
        target_dates = target_dates[:args.trial]
        
    print(f"Processing {len(target_dates)} dates...")
    if len(target_dates) > 0:
        print(f"First few dates: {target_dates[:5]}")

    # 6. Multiprocessing IDW
    tasks = []
    for d in target_dates:
        idx = dates.index(d)
        tasks.append((args.input, idx, d, insar_coords, target_coords, valid_spatial_indices, args.neighbors, args.buffer_radius, mask_data))
        
    import multiprocessing as mp
    print(f"Starting parallel processing with {args.workers} workers...")
    with mp.get_context('spawn').Pool(args.workers) as pool:
        results = pool.map(idw_worker, tasks)
        
    # 7. Assemble results (Avoiding DataFrame fragmentation)
    print("Assembling results...")
    new_cols = {f"D{d}": res for d, res in zip(target_dates, results)}
    new_df = pd.DataFrame(new_cols, index=gdf.index)
    gdf = pd.concat([gdf, new_df], axis=1)
        
    # 8. Save results with field limit check
    output_path = args.output
    n_fields = len(gdf.columns)
    
    if n_fields >= 255 and output_path.lower().endswith('.shp'):
        output_path = os.path.splitext(output_path)[0] + ".gpkg"
        print(f"\nWarning: Too many fields ({n_fields}) for Shapefile format (max 255).")
        print(f"Switching output to GeoPackage: {output_path}")
        
    print(f"Saving to {output_path}...")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    if output_path.lower().endswith('.gpkg'):
        gdf.to_file(output_path, driver='GPKG')
    else:
        gdf.to_file(output_path)
    
    print(f"✓ Results successfully saved to {output_path}")

if __name__ == "__main__":
    main()
