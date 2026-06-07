#!/usr/bin/env python3
"""
Memory-safe Ascending/Descending to Horizontal/Vertical decomposition using spatial patching.

This script decomposes LOS timeseries from two tracks into horizontal and vertical
components using MintPy utilities. It processes data in small spatial patches (row-strips)
serially to keep peak RAM usage bounded to one patch at a time.

Why serial and not parallel:
  - HDF5 is not concurrent-write-safe, so multiprocessing cannot speed up I/O.
  - For large datasets (786 dates × 2674 × 2053), each patch is several GB. Sending
    patches to workers via IPC (pickling) multiplies RAM usage by 3-9×, causing OOM.
  - The inner date loop is pure numpy and fast; the bottleneck is always disk I/O.
  - This matches MintPy's own timeseries2velocity.py / dem_error.py approach.

Usage:
    python insar_asc_desc_decompose_optimized.py asc.h5 desc.h5 -g asc_geom.h5 desc_geom.h5 -o 6_decompose/
    python insar_asc_desc_decompose_optimized.py asc.h5 desc.h5 -o 6_decompose/ --max-memory 2.0
"""

import os
import sys
import argparse
import time
import math
import warnings
import numpy as np

from mintpy.objects import cluster, timeseries
from mintpy.utils import readfile, writefile, utils as ut
from mintpy.asc_desc2horz_vert import get_overlap_lalo, get_design_matrix4horz_vert


def _write_and_zero_ref(horz_file, vert_file, horz_patch, vert_patch,
                        box_overlap, num_dates, ref_y, ref_x):
    """Write one spatial patch to HDF5 and zero reference pixel if it falls within."""
    block_3d = [0, num_dates, box_overlap[1], box_overlap[3],
                box_overlap[0], box_overlap[2]]

    writefile.write_hdf5_block(horz_file, data=horz_patch, datasetName='timeseries',
                               block=block_3d, print_msg=False)
    writefile.write_hdf5_block(vert_file, data=vert_patch, datasetName='timeseries',
                               block=block_3d, print_msg=False)

    # Zero reference pixel if it falls within this patch's spatial range
    if ref_y >= 0 and ref_x >= 0:
        y0, y1 = box_overlap[1], box_overlap[3]
        x0, x1 = box_overlap[0], box_overlap[2]
        if y0 <= ref_y < y1 and x0 <= ref_x < x1:
            zero_block = [0, num_dates, ref_y, ref_y + 1, ref_x, ref_x + 1]
            zero_data = np.zeros((num_dates, 1, 1), dtype=np.float32)
            writefile.write_hdf5_block(horz_file, data=zero_data,
                                       datasetName='timeseries', block=zero_block, print_msg=False)
            writefile.write_hdf5_block(vert_file, data=zero_data,
                                       datasetName='timeseries', block=zero_block, print_msg=False)


def get_common_info(asc_file, desc_file):
    """Find common dates and spatial overlap between ascending and descending tracks."""
    print("Finding common dates and spatial overlap...")

    # Metadata
    atr_asc = readfile.read_attribute(asc_file)
    atr_desc = readfile.read_attribute(desc_file)

    # Dates
    dates_asc = timeseries(asc_file).get_date_list()
    dates_desc = timeseries(desc_file).get_date_list()
    common_dates = sorted(list(set(dates_asc) & set(dates_desc)))

    if not common_dates:
        raise ValueError("No common dates found between ascending and descending tracks!")

    # Spatial overlap
    S, N, W, E = get_overlap_lalo([atr_asc, atr_desc])
    lat_step = float(atr_asc['Y_STEP'])
    lon_step = float(atr_asc['X_STEP'])
    length = int(round((S - N) / lat_step))
    width = int(round((E - W) / lon_step))

    # Crop boxes
    coord_asc = ut.coordinate(atr_asc)
    coord_desc = ut.coordinate(atr_desc)
    y0_asc, x0_asc = coord_asc.lalo2yx(N, W)
    y0_desc, x0_desc = coord_desc.lalo2yx(N, W)

    box_asc = (x0_asc, y0_asc, x0_asc + width, y0_asc + length)
    box_desc = (x0_desc, y0_desc, x0_desc + width, y0_desc + length)

    return common_dates, (S, N, W, E), (length, width), (box_asc, box_desc), (atr_asc, atr_desc)


def setup_output_files(output_base, common_dates, length, width, meta):
    """Pre-allocate output horizontal and vertical timeseries files."""
    num_dates = len(common_dates)

    base_dir = os.path.dirname(output_base) or '.'
    base_name = os.path.basename(output_base)
    if not base_name:
        base_name = "decomposed"

    horz_file = os.path.join(base_dir, f"horz_{base_name}.h5")
    vert_file = os.path.join(base_dir, f"vert_{base_name}.h5")

    print(f"Setting up output files: {horz_file}, {vert_file}")

    # Prepare datasets
    date_digit = len(common_dates[0])
    ds_name_dict = {
        "date": [np.dtype(f'S{date_digit}'), (num_dates,), np.array(common_dates, np.bytes_)],
        "bperp": [np.float32, (num_dates,), np.zeros(num_dates, np.float32)],
        "timeseries": [np.float32, (num_dates, length, width), None]
    }

    # Metadata update
    out_meta = meta.copy()
    out_meta['FILE_TYPE'] = 'timeseries'
    out_meta['UNIT'] = 'm'
    out_meta['LENGTH'] = str(length)
    out_meta['WIDTH'] = str(width)
    out_meta['START_DATE'] = common_dates[0]
    out_meta['END_DATE'] = common_dates[-1]

    # Reference point
    if 'REF_LAT' in meta and 'REF_LON' in meta:
        ref_lat, ref_lon = float(meta['REF_LAT']), float(meta['REF_LON'])
        coord = ut.coordinate(out_meta)
        ref_y, ref_x = coord.lalo2yx(ref_lat, ref_lon)
        out_meta['REF_Y'] = str(int(ref_y))
        out_meta['REF_X'] = str(int(ref_x))

    for f in [horz_file, vert_file]:
        if os.path.exists(f):
            os.remove(f)
        writefile.layout_hdf5(f, ds_name_dict=ds_name_dict, metadata=out_meta)

    return horz_file, vert_file


def decompose_patch_wise(asc_file, desc_file, geom_files, output_base,
                         horz_az_angle=-90.0, max_memory=4.0):
    """
    Main decomposition controller: serial patch-by-patch processing.

    Splits the spatial domain into row-strips so that one patch (asc + desc input
    plus horz + vert output) fits within max_memory. Each patch is decomposed in a
    single batched matrix operation — no Python loops over dates or pixels.
    """
    start_time = time.time()

    # 1. Get overlap and common info
    common_dates, snwe, (length, width), (box_asc, box_desc), (atr_asc, atr_desc) = \
        get_common_info(asc_file, desc_file)
    num_dates = len(common_dates)

    # 2. Setup output (pre-allocate HDF5 before the patch loop)
    horz_file, vert_file = setup_output_files(output_base, common_dates, length, width, atr_asc)

    # 3. Memory-aware spatial partitioning
    # Peak per iteration: 4 float32 arrays (asc_in, desc_in, horz_out, vert_out)
    # each of shape (num_dates, patch_rows, width). max_memory is the cap for all 4.
    max_memory_bytes = max_memory * 1024**3
    num_box = math.ceil(
        (4 * num_dates * length * width * 4) / max_memory_bytes
    )
    num_box = max(1, num_box)

    box_list, num_box = cluster.split_box2sub_boxes(
        box=(0, 0, width, length),
        num_split=num_box,
        dimension='y',
        print_msg=True
    )

    # 4. Compute date indices in source files (common dates only)
    ts_asc = timeseries(asc_file)
    ts_desc = timeseries(desc_file)
    ts_asc.open(print_msg=False)
    ts_desc.open(print_msg=False)
    idx_asc = [ts_asc.dateList.index(d) for d in common_dates]
    idx_desc = [ts_desc.dateList.index(d) for d in common_dates]

    # 5. Resolve reference pixel in output-space coordinates
    ref_y, ref_x = -1, -1
    if 'REF_LAT' in atr_asc and 'REF_LON' in atr_asc:
        out_atr = readfile.read_attribute(horz_file)
        coord = ut.coordinate(out_atr)
        ref_y, ref_x = coord.lalo2yx(float(atr_asc['REF_LAT']), float(atr_asc['REF_LON']))

    # Pre-compute scalar geometry (scalar path, no geometry files)
    if not geom_files:
        los_inc_scalar = np.array([
            ut.incidence_angle(atr_asc, dimension=0, print_msg=False),
            ut.incidence_angle(atr_desc, dimension=0, print_msg=False),
        ], dtype=np.float32)
        los_az_scalar = np.array([
            ut.heading2azimuth_angle(float(atr_asc['HEADING'])),
            ut.heading2azimuth_angle(float(atr_desc['HEADING'])),
        ], dtype=np.float32)

    # 6. Patch loop — one patch in memory at a time, fully vectorized over all dates
    print(f'Decomposing {num_dates} dates in {num_box} spatial patches (vectorized)...')
    warnings.filterwarnings('ignore')

    for i, box_overlap in enumerate(box_list):
        if num_box > 1:
            print(f'  processing patch {i+1}/{num_box} (rows {box_overlap[1]}-{box_overlap[3]})')

        # Translate overlap-space box to file-specific pixel boxes
        bpa = (box_asc[0] + box_overlap[0], box_asc[1] + box_overlap[1],
               box_asc[0] + box_overlap[2], box_asc[1] + box_overlap[3])
        bpd = (box_desc[0] + box_overlap[0], box_desc[1] + box_overlap[1],
               box_desc[0] + box_overlap[2], box_desc[1] + box_overlap[3])

        # Read LOS data for this patch, common dates only
        asc_patch  = readfile.read(asc_file,  datasetName='timeseries', box=bpa, print_msg=False)[0][idx_asc]
        desc_patch = readfile.read(desc_file, datasetName='timeseries', box=bpd, print_msg=False)[0][idx_desc]

        patch_len = box_overlap[3] - box_overlap[1]
        patch_wid = box_overlap[2] - box_overlap[0]

        # Geometry for this patch
        if geom_files:
            los_inc = np.array([
                readfile.read(geom_files[0], datasetName='incidenceAngle', box=bpa, print_msg=False)[0],
                readfile.read(geom_files[1], datasetName='incidenceAngle', box=bpd, print_msg=False)[0],
            ], dtype=np.float32)
            los_az = np.array([
                readfile.read(geom_files[0], datasetName='azimuthAngle', box=bpa, print_msg=False)[0],
                readfile.read(geom_files[1], datasetName='azimuthAngle', box=bpd, print_msg=False)[0],
            ], dtype=np.float32)
        else:
            los_inc = los_inc_scalar
            los_az  = los_az_scalar

        # Stack into (2, T, L, W) — index 0 = asc, index 1 = desc (matches MintPy convention)
        dlos = np.stack([asc_patch, desc_patch], axis=0)

        # Zero reference pixel in input before decomposition (mirrors parallel script)
        if ref_y >= 0 and ref_x >= 0:
            local_ref_y = ref_y - box_overlap[1]
            local_ref_x = ref_x - box_overlap[0]
            if 0 <= local_ref_y < patch_len and 0 <= local_ref_x < patch_wid:
                dlos[:, :, local_ref_y, local_ref_x] = 0.0

        if los_inc.ndim == 1:
            # Scalar geometry: one G for the whole patch.
            # Matches MintPy 1D branch: pinv(G) @ dlos.reshape(2, -1)
            G = get_design_matrix4horz_vert(los_inc, los_az, horz_az_angle)
            Ginv = np.linalg.pinv(G).astype(np.float32)          # (2, 2)
            result = np.dot(Ginv, dlos.reshape(2, -1))            # (2, T*L*W)
            horz_patch = result[0].reshape(num_dates, patch_len, patch_wid).astype(np.float32)
            vert_patch  = result[1].reshape(num_dates, patch_len, patch_wid).astype(np.float32)

        else:
            # 2D geometry: replicate MintPy's windowed-median approach (step=20).
            # Precompute Ginv once per window, broadcast to all pixels in that window,
            # then apply to all T dates via a single batched matmul — no Python date loop.
            step = 20
            num_row = int(np.ceil(patch_len / step))
            num_col = int(np.ceil(patch_wid / step))
            Ginv = np.zeros((patch_len, patch_wid, 2, 2), dtype=np.float32)

            for ii in range(num_row):
                y0, y1 = step * ii, min(step * (ii + 1), patch_len)
                for jj in range(num_col):
                    x0, x1 = step * jj, min(step * (jj + 1), patch_wid)
                    med_inc = np.nanmedian(los_inc[:, y0:y1, x0:x1], axis=(1, 2))
                    med_az  = np.nanmedian(los_az[:,  y0:y1, x0:x1], axis=(1, 2))
                    if np.all(~np.isnan(med_inc)):
                        G = get_design_matrix4horz_vert(med_inc, med_az, horz_az_angle)
                        Ginv[y0:y1, x0:x1] = np.linalg.pinv(G)

            # (L, W, 2, 2) @ (L, W, 2, T) → (L, W, 2, T)
            dlos_t = dlos.transpose(2, 3, 0, 1)
            result  = np.matmul(Ginv, dlos_t)
            horz_patch = result[:, :, 0, :].transpose(2, 0, 1).astype(np.float32)
            vert_patch  = result[:, :, 1, :].transpose(2, 0, 1).astype(np.float32)

        del dlos

        # Write and free immediately
        _write_and_zero_ref(horz_file, vert_file, horz_patch, vert_patch,
                            box_overlap, num_dates, ref_y, ref_x)
        del asc_patch, desc_patch, horz_patch, vert_patch

    # 7. Timing report
    m, s = divmod(time.time() - start_time, 60)
    print("-" * 60)
    print(f"Decomposition successful!")
    print(f"Time used: {m:02.0f} mins {s:02.1f} secs.")
    print(f"Output: {horz_file}")
    print(f"        {vert_file}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Memory-safe Asc/Desc Decomposition using serial spatial patching.'
    )
    parser.add_argument('asc_file', help='Ascending timeseries HDF5 file.')
    parser.add_argument('desc_file', help='Descending timeseries HDF5 file.')
    parser.add_argument('-g', '--geometry', nargs=2, metavar=('ASC_GEOM', 'DESC_GEOM'),
                        help='Geometry files for ascending and descending tracks.')
    parser.add_argument('-o', '--output', required=True,
                        help='Output base name (horz_/vert_ will be prefixed).')
    parser.add_argument('--horz-az', type=float, default=-90.0,
                        help='Horizontal azimuth angle in degrees (default: -90.0).')
    parser.add_argument('--max-memory', type=float, default=4.0,
                        help='Max RAM for one patch (4 arrays) in GB (default: 4.0).')

    args = parser.parse_args()

    out_dir = os.path.dirname(args.output) or '.'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:
        decompose_patch_wise(
            args.asc_file,
            args.desc_file,
            args.geometry,
            args.output,
            horz_az_angle=args.horz_az,
            max_memory=args.max_memory,
        )
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
