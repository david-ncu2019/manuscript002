#!/usr/bin/env python3
"""
Remove specific dates from MintPy timeseries HDF5 files using patch-by-patch processing.

This program efficiently removes specified dates from large timeseries files
by processing data in spatial blocks, preserving all metadata and structure.
It follows the MintPy patch-by-patch architecture for memory efficiency.

Usage: python insar_remove_dates_optimized.py input_timeseries.h5 YYYYMMDD [YYYYMMDD2 ...]
Example: python insar_remove_dates_optimized.py vertical_timeseries.h5 20250801 20250815
"""

import os
import sys
import argparse
import time
import numpy as np
import h5py
import logging
from mintpy.objects import timeseries, cluster
from mintpy.utils import readfile, writefile, ptime, utils as ut

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def get_dates_to_keep(input_file, dates_to_remove):
    """
    Identify which dates to keep and return mask and new date list.
    
    Parameters:
        input_file (str): Path to input HDF5 file
        dates_to_remove (list): List of YYYYMMDD strings to remove
        
    Returns:
        tuple: (keep_mask, new_date_list, valid_to_remove)
    """
    with h5py.File(input_file, 'r') as f:
        dates_raw = f['date'][:]
        date_list = [d.decode('utf-8') if hasattr(d, 'decode') else str(d) for d in dates_raw]
    
    # Validate dates to remove
    valid_to_remove = []
    for d in dates_to_remove:
        if d in date_list:
            valid_to_remove.append(d)
        else:
            logger.warning(f"Date {d} not found in file, skipping.")
            
    if not valid_to_remove:
        logger.error("No valid dates found to remove among the provided inputs.")
        sys.exit(1)
        
    keep_mask = np.array([d not in valid_to_remove for d in date_list], dtype=bool)
    new_date_list = [d for i, d in enumerate(date_list) if keep_mask[i]]
    
    if len(new_date_list) < 2:
        raise ValueError("Error: Removing these dates would leave fewer than 2 dates in the timeseries!")
        
    return keep_mask, new_date_list, valid_to_remove

def remove_dates_patch_wise(input_file, dates_to_remove, output_file=None, max_memory=4.0):
    """
    Process file in patches to remove dates.
    
    Parameters:
        input_file (str): Path to input timeseries file
        dates_to_remove (list): List of dates to remove
        output_file (str): Optional output filename
        max_memory (float): Maximum memory in GB for patch processing
    """
    start_time = time.time()
    
    # 1. Read basic info
    atr = readfile.read_attribute(input_file)
    length, width = int(atr['LENGTH']), int(atr['WIDTH'])
    
    keep_mask, new_date_list, removed_dates = get_dates_to_keep(input_file, dates_to_remove)
    num_date = len(keep_mask)
    num_keep = len(new_date_list)
    
    logger.info(f"Input file: {input_file}")
    logger.info(f"Original dates: {num_date}")
    logger.info(f"Dates to remove: {len(removed_dates)} ({removed_dates})")
    logger.info(f"Remaining dates: {num_keep}")
    
    # Check Reference Date
    ref_date = atr.get('REF_DATE')
    if ref_date in removed_dates:
        logger.warning("-" * 60)
        logger.warning(f"CRITICAL WARNING: You are removing the reference date ({ref_date})!")
        logger.warning("This will likely cause visualization issues (non-zero phase at reference).")
        logger.warning("Recommendation: Change reference date before removing this date if possible.")
        logger.warning("-" * 60)

    # 2. Prepare output file name
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_rem{len(removed_dates)}{ext}"
    
    if os.path.abspath(input_file) == os.path.abspath(output_file):
        raise ValueError("Output file cannot be the same as input file!")

    # 3. Initialize output file structure (Layout)
    logger.info(f"Initializing output file structure: {output_file}")
    
    # Define datasets for layout
    date_digit = len(new_date_list[0])
    ds_name_dict = {
        "date": [np.dtype(f'S{date_digit}'), (num_keep,), np.array(new_date_list, np.bytes_)],
        "timeseries": [np.float32, (num_keep, length, width), None]
    }
    
    # Handle bperp if present
    with h5py.File(input_file, 'r') as f:
        if 'bperp' in f:
            if f['bperp'].ndim == 1:
                logger.info("Found 1D bperp dataset, filtering and writing.")
                bperp_filtered = f['bperp'][:][keep_mask]
                ds_name_dict['bperp'] = [np.float32, (num_keep,), bperp_filtered]
            elif f['bperp'].ndim == 3:
                logger.info("Found 3D bperp dataset, will process patch-wise.")
                ds_name_dict['bperp'] = [np.float32, (num_keep, length, width), None]

    # Update metadata
    meta = dict(atr)
    meta['START_DATE'] = new_date_list[0]
    meta['END_DATE'] = new_date_list[-1]
    # Update DATE12 attribute (YYMMDD-YYMMDD)
    meta['DATE12'] = f"{new_date_list[0][2:]}-{new_date_list[-1][2:]}"
    
    # Pre-allocate HDF5 layout
    writefile.layout_hdf5(output_file, ds_name_dict=ds_name_dict, metadata=meta)

    # 4. Split into boxes for patch-by-patch processing
    # Memory estimation: (num_date_in + num_keep_out) * length * width * 4 bytes
    # Safety factor of 2.0 to account for overhead
    num_epoch = num_date + num_keep
    num_box = int(np.ceil((num_epoch * length * width * 4) * 2.0 / (max_memory * 1024**3)))
    box_list, num_box = cluster.split_box2sub_boxes(
        box=(0, 0, width, length),
        num_split=num_box,
        dimension='y',
        print_msg=True
    )

    # 5. Loop through patches
    logger.info(f"Processing data in {num_box} patches...")
    for i, box in enumerate(box_list):
        if num_box > 1:
            logger.info(f"Processing patch {i+1}/{num_box}: rows {box[1]}-{box[3]}, cols {box[0]}-{box[2]}")
        
        # Read timeseries block
        data, _ = readfile.read(input_file, datasetName='timeseries', box=box)
        
        # Filter dates (temporal mask)
        data_filtered = data[keep_mask, :, :]
        
        # Write filtered block to output
        # Block format for 3D: [z_start, z_end, y_start, y_end, x_start, x_end]
        block_3d = [0, num_keep, box[1], box[3], box[0], box[2]]
        writefile.write_hdf5_block(output_file, data=data_filtered, datasetName='timeseries', block=block_3d)
        
        # Handle 3D bperp if necessary
        with h5py.File(input_file, 'r') as f:
            if 'bperp' in f and f['bperp'].ndim == 3:
                bperp_data, _ = readfile.read(input_file, datasetName='bperp', box=box)
                bperp_filtered = bperp_data[keep_mask, :, :]
                writefile.write_hdf5_block(output_file, data=bperp_filtered, datasetName='bperp', block=block_3d)

    # 6. Finalize
    m, s = divmod(time.time() - start_time, 60)
    logger.info("-" * 60)
    logger.info(f"Successfully created: {output_file}")
    logger.info(f"Time used: {m:02.0f} mins {s:02.1f} secs.")
    logger.info("To verify, run: info.py " + output_file + " --compact")
    logger.info("-" * 60)

def main():
    parser = argparse.ArgumentParser(
        description='Remove specific dates from MintPy timeseries HDF5 files using spatial patching.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python insar_remove_dates_optimized.py timeseries.h5 20210301 20210315
  python insar_remove_dates_optimized.py timeseries.h5 20220726 -o timeseries_fixed.h5 --max-memory 2.0
        """
    )
    parser.add_argument('input_file', help='Input timeseries HDF5 file.')
    parser.add_argument('dates', nargs='+', help='Dates to remove in YYYYMMDD format.')
    parser.add_argument('-o', '--output', help='Output filename (optional).')
    parser.add_argument('--max-memory', type=float, default=4.0, 
                        help='Max memory in GB for patch processing (default: 4.0).')
    
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    
    # Basic file check
    if not os.path.isfile(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)

    # Validate dates format
    for d in args.dates:
        if len(d) != 8 or not d.isdigit():
            logger.error(f"Invalid date format '{d}'. Expected YYYYMMDD.")
            sys.exit(1)
            
    try:
        remove_dates_patch_wise(
            args.input_file, 
            args.dates, 
            output_file=args.output, 
            max_memory=args.max_memory
        )
    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
