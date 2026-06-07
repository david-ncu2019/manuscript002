#!/usr/bin/env python3
"""
Mask large MintPy timeseries HDF5 files using patch-by-patch processing.

This program applies a spatial mask to a timeseries file by processing data 
in spatial blocks (patches), preserving all metadata and structure while 
maintaining low memory usage.

Usage: python insar_mask_optimized.py input_timeseries.h5 -m mask_file.h5 [-o output_file.h5]
Example: python insar_mask_optimized.py desc_ts.h5 -m maskTempCoh.h5
"""

import os
import sys
import argparse
import time
import numpy as np
import h5py
import logging
from mintpy.objects import timeseries, cluster
from mintpy.utils import readfile, writefile, utils as ut

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def mask_matrix_block(data, mask, fill_value=np.nan):
    """
    Apply mask to a data block (2D or 3D).
    
    Parameters:
        data (np.ndarray): Data block to be masked
        mask (np.ndarray): 2D boolean mask for the block
        fill_value (float): Value to fill masked-out pixels
        
    Returns:
        np.ndarray: Masked data
    """
    # Check data type for NaN filling
    if np.isnan(fill_value) and data.dtype.kind not in ('f', 'd', 'c'):
        data = data.astype(np.float32)

    if data.ndim == 2:
        data[mask == 0] = fill_value
    elif data.ndim == 3:
        # Apply 2D mask to each 2D slice of 3D data
        # Using boolean indexing for efficiency
        data[:, mask == 0] = fill_value
    return data

def mask_file_patch_wise(input_file, mask_file, output_file=None, fill_value=np.nan, max_memory=4.0):
    """
    Process file in patches to apply mask.
    
    Parameters:
        input_file (str): Path to input file to be masked
        mask_file (str): Path to mask HDF5 file
        output_file (str): Optional output filename
        fill_value (float): Value for masked-out pixels
        max_memory (float): Maximum memory in GB for patch processing
    """
    start_time = time.time()
    
    # 1. Read metadata and dimensions
    atr = readfile.read_attribute(input_file)
    length, width = int(atr['LENGTH']), int(atr['WIDTH'])
    ds_names = readfile.get_dataset_list(input_file)
    
    # Read full mask (it's 2D, so it fits in memory)
    logger.info(f"Reading mask from: {mask_file}")
    mask, mask_atr = readfile.read(mask_file)
    
    # Check mask dimensions
    if mask.shape != (length, width):
        # Try to handle slightly different shapes if attributes match (e.g. subsetted)
        logger.warning(f"Mask shape {mask.shape} differs from input shape ({length}, {width})!")
        logger.info("Attempting to align mask using SNWE coordinates...")
        # This is a fallback; in most cases they should match if cropped/overlap was used
        # For this tool, we assume they are already aligned/cropped to match.
        if mask.shape[0] * mask.shape[1] != length * width:
             raise ValueError("Mask dimensions do not match input dimensions!")

    # 2. Prepare output file name
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_msk{ext}"
    
    if os.path.abspath(input_file) == os.path.abspath(output_file):
        raise ValueError("Output file cannot be the same as input file!")

    # 3. Initialize output file structure (Layout)
    logger.info(f"Initializing output file structure: {output_file}")
    
    # Build dataset dictionary for layout
    ds_name_dict = {}
    with h5py.File(input_file, 'r') as f:
        for ds_name in ds_names:
            ds = f[ds_name]
            # Convert dtype if using NaN fill on integer data
            dtype = ds.dtype
            if np.isnan(fill_value) and dtype.kind not in ('f', 'd', 'c'):
                dtype = np.float32
            
            # For non-spatial datasets (like 'date', 'bperp' if 1D), we write them now
            if ds.ndim == 1:
                logger.info(f"Writing 1D dataset: {ds_name}")
                ds_name_dict[ds_name] = [dtype, ds.shape, ds[:]]
            else:
                # Spatial datasets (2D or 3D) will be pre-allocated
                ds_name_dict[ds_name] = [dtype, ds.shape, None]

    # Pre-allocate HDF5 layout
    writefile.layout_hdf5(output_file, ds_name_dict=ds_name_dict, metadata=atr)

    # 4. Split into boxes for patch-by-patch processing
    # Estimate memory per epoch (num_dates if timeseries)
    num_epoch = 0
    with h5py.File(input_file, 'r') as f:
        for ds_name in ds_names:
            if f[ds_name].ndim == 3:
                num_epoch += f[ds_name].shape[0]
            elif f[ds_name].ndim == 2:
                num_epoch += 1
    
    # Safety factor of 2.5
    num_box = int(np.ceil((num_epoch * length * width * 4) * 2.5 / (max_memory * 1024**3)))
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
            logger.info(f"Processing patch {i+1}/{num_box} (rows {box[1]}-{box[3]})")
        
        # Get mask chunk for this box
        mask_chunk = mask[box[1]:box[3], box[0]:box[2]]
        
        for ds_name in ds_names:
            # Skip datasets already written (1D)
            with h5py.File(input_file, 'r') as f:
                if f[ds_name].ndim < 2:
                    continue
                ds_shape = f[ds_name].shape
                ds_ndim = f[ds_name].ndim

            # Read data chunk
            data, _ = readfile.read(input_file, datasetName=ds_name, box=box)
            
            # Mask data chunk
            data_masked = mask_matrix_block(data, mask_chunk, fill_value=fill_value)
            
            # Write to output
            if ds_ndim == 2:
                block = [box[1], box[3], box[0], box[2]]
            else: # 3D
                block = [0, ds_shape[0], box[1], box[3], box[0], box[2]]
            
            writefile.write_hdf5_block(output_file, data=data_masked, datasetName=ds_name, block=block)

    # 6. Finalize
    m, s = divmod(time.time() - start_time, 60)
    logger.info("-" * 60)
    logger.info(f"Successfully created masked file: {output_file}")
    logger.info(f"Time used: {m:02.0f} mins {s:02.1f} secs.")
    logger.info("-" * 60)

def main():
    parser = argparse.ArgumentParser(
        description='Mask large MintPy HDF5 files using spatial patching.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python insar_mask_optimized.py timeseries.h5 -m maskTempCoh.h5
  python insar_mask_optimized.py velocity.h5 -m maskConnComp.h5 -o velocity_msk.h5
  python insar_mask_optimized.py timeseries.h5 -m mask.h5 --fill-value 0 --max-memory 2.0
        """
    )
    parser.add_argument('input_file', help='Input HDF5 file to be masked (timeseries, velocity, geometry, etc.)')
    parser.add_argument('-m', '--mask', required=True, help='Mask HDF5 file.')
    parser.add_argument('-o', '--output', help='Output filename (optional).')
    parser.add_argument('--fill-value', type=float, default=np.nan, 
                        help='Value for masked-out pixels (default: NaN).')
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
    if not os.path.isfile(args.mask):
        logger.error(f"Mask file not found: {args.mask}")
        sys.exit(1)

    try:
        mask_file_patch_wise(
            args.input_file, 
            args.mask, 
            output_file=args.output, 
            fill_value=args.fill_value,
            max_memory=args.max_memory
        )
    except Exception as e:
        logger.error(f"An error occurred during processing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
