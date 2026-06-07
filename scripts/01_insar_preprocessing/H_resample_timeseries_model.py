#!/usr/bin/env python3
"""
Generate temporally-regularized timeseries based on a kinematic deformation model.
Projects a fitted model onto a fixed schedule (e.g., days 1, 6, 11, 16, 21, 26).
"""

import os
import sys
import argparse
import numpy as np
import h5py
from datetime import datetime, timedelta
from calendar import monthrange

# MintPy Imports
try:
    from mintpy.utils import readfile, writefile, ptime, time_func
    from mintpy.objects import timeseries, cluster
except ImportError:
    print("Error: MintPy not found in environment.")
    sys.exit(1)

def create_regular_dates(start_date, end_date, ref_date, days_of_month=[1, 6, 11, 16, 21, 26]):
# def create_regular_dates(start_date, end_date, ref_date, days_of_month=[1]):
    """Generate the target date list."""
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    
    dates = [ref_date]
    curr = datetime(start_dt.year, start_dt.month, 1)
    
    while curr <= end_dt:
        for day in days_of_month:
            # Handle months with fewer than 31 days (though not needed for 1-26)
            last_day = monthrange(curr.year, curr.month)[1]
            if day <= last_day:
                target_dt = datetime(curr.year, curr.month, day)
                if start_dt <= target_dt <= end_dt:
                    dates.append(target_dt.strftime('%Y%m%d'))
        
        # Advance to next month
        if curr.month == 12:
            curr = datetime(curr.year + 1, 1, 1)
        else:
            curr = datetime(curr.year, curr.month + 1, 1)
            
    return sorted(list(set(dates)))

def main():
    parser = argparse.ArgumentParser(description='Model-based Regular Resampling')
    parser.add_argument('input', help='Input timeseries.h5')
    parser.add_argument('-o', '--output', required=True, help='Output HDF5')
    parser.add_argument('--poly', type=int, default=1)
    parser.add_argument('--period', type=float, nargs='+', default=[1.0, 0.5])
    parser.add_argument('--polyline', nargs='+', default=[])
    parser.add_argument('--ex', nargs='+', default=[])
    parser.add_argument('--ref-yx', type=int, nargs=2, default=[1749, 1436])
    parser.add_argument('--max-memory', type=float, default=4.0)
    args = parser.parse_args()

    # 1. Setup Model
    model = {
        'polynomial': args.poly,
        'periodic': args.period,
        'stepDate': [],
        'polyline': args.polyline,
        'exp': {}, 'log': {}
    }
    
    # 2. Open Input
    atr = readfile.read_attribute(args.input)
    length, width = int(atr['LENGTH']), int(atr['WIDTH'])
    ts_obj = timeseries(args.input)
    ts_obj.open()
    orig_dates = ts_obj.get_date_list()
    seconds = float(atr.get('CENTER_LINE_UTC', 0))
    ref_date = atr.get('REF_DATE', orig_dates[0])

    # 3. Create Regular Dates
    new_dates = create_regular_dates(orig_dates[0], orig_dates[-1], ref_date)
    num_new = len(new_dates)
    print(f"Projecting model onto {num_new} regular dates...")

    # 4. Design Matrices
    # G for fitting (original dates)
    G_fit = time_func.get_design_matrix4time_func(orig_dates, model, ref_date, seconds)
    # G for projection (new dates)
    G_proj = time_func.get_design_matrix4time_func(new_dates, model, ref_date, seconds)
    
    # Exclude dates from fit if requested
    if args.ex:
        mask_ex = np.array([d not in args.ex for d in orig_dates])
        G_fit = G_fit[mask_ex, :]

    # 5. Prepare Output File
    atr_out = dict(atr)
    atr_out['FILE_TYPE'] = 'timeseries'
    atr_out['START_DATE'] = new_dates[0]
    atr_out['END_DATE'] = new_dates[-1]
    
    ds_name_dict = {
        'date': [f'S{len(new_dates[0])}', (num_new,), np.array(new_dates, dtype=f'S{len(new_dates[0])}')],
        'timeseries': [np.float32, (num_new, length, width), None]
    }
    writefile.layout_hdf5(args.output, metadata=atr_out, ds_name_dict=ds_name_dict)

    # 6. Block Processing
    num_param = G_fit.shape[1]
    box_list, num_box = cluster.split_box2sub_boxes(
        box=(0, 0, width, length),
        num_split=int(np.ceil((len(orig_dates) * length * width * 4 * 2) / (args.max_memory * 1024**3))),
        dimension='y'
    )

    with h5py.File(args.output, 'r+') as f_out:
        dset = f_out['timeseries']
        
        for i, box in enumerate(box_list):
            print(f"Processing Patch {i+1}/{num_box}...")
            data = readfile.read(args.input, box=box)[0]
            
            # Spatial Referencing
            ry, rx = args.ref_yx
            if box[1] <= ry < box[3] and box[0] <= rx < box[2]:
                ref_ts = data[:, ry-box[1], rx-box[0]]
                data -= ref_ts[:, None, None]
            
            # Temporal Referencing
            ridx = orig_dates.index(ref_date)
            data -= data[ridx, :, :][None, :, :]
            
            # Flatten
            m_orig, h, w = data.shape
            data_2d = data.reshape(m_orig, -1)
            
            # Apply Exclusions
            if args.ex:
                data_2d = data_2d[mask_ex, :]
            
            # Fit & Project Pixel-by-Pixel (Vectorized)
            # We solve Gm = d -> m = G+ d
            # Then d_new = G_proj * m
            valid = ~np.all(np.isnan(data_2d), axis=0) & ~np.all(data_2d == 0, axis=0)
            
            if np.any(valid):
                # Least Squares Fit
                m_params = np.linalg.lstsq(G_fit, data_2d[:, valid], rcond=None)[0]
                # Projection
                proj_data = np.dot(G_proj, m_params)
                
                # Reshape back to block
                out_block = np.full((num_new, h * w), np.nan, dtype=np.float32)
                out_block[:, valid] = proj_data
                dset[:, box[1]:box[3], box[0]:box[2]] = out_block.reshape(num_new, h, w)

    print(f"Success! Model-based regular timeseries saved to {args.output}")

if __name__ == '__main__':
    main()
