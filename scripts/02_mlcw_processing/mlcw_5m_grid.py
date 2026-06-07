"""
MLCW Near-Surface Extrapolation & 5m Grid Regularization

Processes ringbyring.csv files to produce individual ring displacements on a uniform 5m depth grid.

Processing chain per station per epoch:
1. Exclude NaN/missing rings
2. Bottom-up cumulative sum → cumulative profile
3. Extrapolate to depth=0 via gradient from two shallowest rings (MLCW reference frame)
4. PCHIP interpolation → uniform 5m grid [0, 5, 10, ..., 300m]
5. Difference adjacent levels → d_individual(z_k, t)

Output: {STATION}_5m_grid.csv with columns [datetime, depth_000m, depth_005m, ..., depth_300m]
Units: mm (same sign convention as input: negative = subsidence)
"""

import pandas as pd
import numpy as np
from scipy.interpolate import PchipInterpolator
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Configuration
INPUT_DIR = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_reconstruction')
OUTPUT_DIR = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\MLCW_5m_regular')  # overwrite in place
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_DEPTHS = np.arange(0, 305, 5)  # [0, 5, 10, ..., 300]
PCHIP_TOLERANCE = 0.5  # mm, validation threshold per mlcw_info.md §5.6
N_RINGS_EXTRAPOLATION = 3  # number of shallowest rings used for surface extrapolation


def load_ringbyring(filepath):
    """Load ringbyring.csv, return (datetime, ring_depths, ring_values_matrix)."""
    df = pd.read_csv(filepath)

    # Extract datetime
    datetime_col = df.iloc[:, 0]

    # Extract ring depths (column names, excluding datetime col 0)
    ring_depth_strs = df.columns[1:]
    ring_depths = np.array([float(d) for d in ring_depth_strs])

    # Extract ring values (all rows, columns 1 onwards)
    ring_values = df.iloc[:, 1:].values.astype(float)

    return datetime_col, ring_depths, ring_values


def exclude_nan_rings(ring_depths, ring_values):
    """
    Exclude any ring column where ALL values are NaN.
    Return (filtered_depths, filtered_values).
    """
    valid_cols = []
    valid_depths = []

    for i, depth in enumerate(ring_depths):
        if not np.all(np.isnan(ring_values[:, i])):
            valid_cols.append(i)
            valid_depths.append(depth)

    if len(valid_cols) == 0:
        raise ValueError("All ring columns are entirely NaN.")

    filtered_values = ring_values[:, valid_cols]
    return np.array(valid_depths), filtered_values


def bottom_up_cumsum(ring_values):
    """
    Compute bottom-up cumulative sum per row.
    Input shape: (n_epochs, n_valid_rings)
    Output shape: (n_epochs, n_valid_rings)

    cumsum_row = np.cumsum(row[::-1])[::-1]
    """
    cumsum_values = np.zeros_like(ring_values)

    for i in range(ring_values.shape[0]):
        row = ring_values[i, :]
        # Reverse, cumsum, reverse back
        cumsum_values[i, :] = np.cumsum(row[::-1])[::-1]

    return cumsum_values


def extrapolate_to_surface(ring_depths, cumsum_values_row, n_rings=None):
    """
    Extrapolate cumulative profile to depth=0 via least-squares linear fit
    through N shallowest rings.

    Option C: Fit line through first n_rings, evaluate at depth=0.
    - n_rings=2: recovers single two-point gradient (original behavior)
    - n_rings=3+: fits line through multiple points, averaging out noise

    Returns: value at depth=0 (extrapolated).
    """
    if n_rings is None:
        n_rings = N_RINGS_EXTRAPOLATION

    if len(ring_depths) < n_rings:
        raise ValueError(f"Need at least {n_rings} valid rings for extrapolation.")

    depths = ring_depths[:n_rings]
    values = cumsum_values_row[:n_rings]

    # Least-squares linear fit: slope, intercept = np.polyfit(x, y, deg=1)
    slope, intercept = np.polyfit(depths, values, 1)

    return intercept


def pchip_interpolate_row(ring_depths, cumsum_values_row, d_at_zero, target_depths):
    """
    PCHIP interpolation of cumulative profile to uniform 5m grid.

    Knots: [0] + ring_depths + [300]
    Values: [d_at_zero] + cumsum_values_row + [0.0]

    The 300m anchor (value=0) is the physical boundary condition of the MLCW
    instrument: cumulative compaction is zero at the concrete base. Including
    it as an explicit PCHIP knot eliminates the previous linear gap-fill
    discontinuity at z_deepest and prevents near-identical values at
    depth_290m and depth_295m for stations whose deepest ring is just below
    295m (e.g., TUKU at 294.698m).

    Returns: interpolated values at target_depths, pchip object.
    """
    if ring_depths[-1] < 300.0:
        # Append 300m zero-anchor only when deepest ring is shallower than 300m.
        # This is the common case: PCHIP then handles the 290–300m zone smoothly
        # instead of the previous linear gap-fill that caused depth_290m ≈ depth_295m.
        knots = np.concatenate(([0.0], ring_depths, [300.0]))
        values = np.concatenate(([d_at_zero], cumsum_values_row, [0.0]))
    else:
        # Deepest ring is at or beyond 300m (e.g., BEICHEN, HONGLUN).
        # Do not append a duplicate 300m knot; PCHIP covers the full range already.
        knots = np.concatenate(([0.0], ring_depths))
        values = np.concatenate(([d_at_zero], cumsum_values_row))

    pchip = PchipInterpolator(knots, values)
    interpolated = pchip(target_depths)

    return interpolated, pchip


def validate_pchip(pchip, ring_depths, cumsum_values_row, tolerance=PCHIP_TOLERANCE):
    """
    Validate PCHIP fit: max residual at original ring depths should be ≤ tolerance.
    Returns: (is_valid, max_residual).
    """
    pchip_at_rings = pchip(ring_depths)
    residuals = np.abs(pchip_at_rings - cumsum_values_row)
    max_residual = np.max(residuals)
    is_valid = max_residual <= tolerance
    return is_valid, max_residual


def difference_to_individual(interpolated_values):
    """
    Convert cumulative profile to individual ring displacements by differencing.

    d_individual[k] = cumsum[k] - cumsum[k+1]  for k = 0..58
    d_individual[59] = cumsum[59]               for k = 59 (deepest level)

    Input: interpolated_values (60 points at [0, 5, 10, ..., 300m])
    Output: individual displacements (60 points)
    """
    individual = np.zeros_like(interpolated_values)

    # Difference for k = 0..58
    for k in range(59):
        individual[k] = interpolated_values[k] - interpolated_values[k + 1]

    # Deepest level: cumsum[59] is already the individual displacement of 300m ring
    individual[59] = interpolated_values[59]

    return individual


def process_station(filepath):
    """
    Process a single MLCW station ringbyring.csv file.
    Returns: DataFrame with columns [datetime, depth_000m, depth_005m, ..., depth_300m]
    """
    print(f"Processing: {filepath.name}")

    # Load data
    datetime_col, ring_depths, ring_values = load_ringbyring(filepath)

    # Exclude fully-NaN ring columns
    ring_depths, ring_values = exclude_nan_rings(ring_depths, ring_values)
    print(f"  Valid rings: {len(ring_depths)} at depths {ring_depths}")

    # Compute bottom-up cumulative sum
    cumsum_values = bottom_up_cumsum(ring_values)

    # Process each epoch
    n_epochs = ring_values.shape[0]
    output_data = {'datetime': datetime_col}

    validation_failures = []

    for i in range(n_epochs):
        cumsum_row = cumsum_values[i, :]

        # Check for NaN in this epoch
        if np.any(np.isnan(cumsum_row)):
            print(f"  Epoch {i} ({datetime_col.iloc[i]}): contains NaN, skipping")
            validation_failures.append(i)
            continue

        # Extrapolate to surface
        d_at_zero = extrapolate_to_surface(ring_depths, cumsum_row)

        # PCHIP interpolation
        interpolated, pchip = pchip_interpolate_row(
            ring_depths, cumsum_row, d_at_zero, TARGET_DEPTHS
        )

        # Validate PCHIP fit
        is_valid, max_residual = validate_pchip(pchip, ring_depths, cumsum_row)
        if not is_valid:
            print(f"  Epoch {i} ({datetime_col.iloc[i]}): PCHIP residual {max_residual:.3f}mm > {PCHIP_TOLERANCE}mm")

        # Convert to individual displacements
        individual = difference_to_individual(interpolated)

        # Store in output dictionary
        for j, depth in enumerate(TARGET_DEPTHS):
            col_name = f'depth_{int(depth):03d}m'
            if col_name not in output_data:
                output_data[col_name] = []
            output_data[col_name].append(individual[j])

    # Pad unfilled epochs with NaN
    for col_name in output_data:
        if col_name != 'datetime':
            if len(output_data[col_name]) < n_epochs:
                pad_length = n_epochs - len(output_data[col_name])
                output_data[col_name] = list(output_data[col_name]) + [np.nan] * pad_length

    # Create output DataFrame
    output_df = pd.DataFrame(output_data)

    # Report summary
    if validation_failures:
        print(f"  Skipped {len(validation_failures)} epochs due to NaN or validation failures")
    print(f"  Output shape: {output_df.shape}")

    return output_df


def main():
    """Main entry point."""
    # Find all ringbyring.csv files
    ringbyring_files = sorted(INPUT_DIR.glob('*_ringbyring_reconstructed.csv'))
    print(f"Found {len(ringbyring_files)} ringbyring.csv files\n")

    if len(ringbyring_files) == 0:
        print(f"ERROR: No ringbyring.csv files found in {INPUT_DIR}")
        return

    # Process each station
    for filepath in ringbyring_files:
        try:
            output_df = process_station(filepath)

            # Save output
            station_name = filepath.stem.replace('_ringbyring_reconstructed', '')
            output_file = OUTPUT_DIR / f'{station_name}_5m_grid.csv'
            output_df.to_csv(output_file, index=False)
            print(f"  Saved: {output_file.name}\n")

        except Exception as e:
            print(f"ERROR processing {filepath.name}: {e}\n")
            continue

    print(f"All stations processed. Output saved to: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
