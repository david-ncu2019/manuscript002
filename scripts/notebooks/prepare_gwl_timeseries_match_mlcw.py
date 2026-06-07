import os

import pandas as pd

# =================================================================
# 1. SETUP MASTER PATHS, OUTPUT DIRECTORIES & CONSTANTS
# =================================================================

# Root workspace directory for data integration
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Destination folder where the synchronized, multi-layer timeline files will be saved
OUTPUT_DIR = os.path.join(PROJECT_DIR, r"data\gwl\mlcw_gwl_timeseries")

# Ensure the output subdirectory exists to prevent save errors later
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# Master timeline file containing the exact dates of the satellite overpasses (InSAR)
INSAR_TIMELINE_PATH = os.path.join(
    PROJECT_DIR, r"data\insar\timeseries\mlcw_interp_insar_IDW_extend.feather"
)

# Relational mapping file linking compaction well stations to nearby aquifer layers
LAYER_ASSIGNMENT_PATH = os.path.join(
    PROJECT_DIR, r"data\gwl\gwl_to_mlcw_layer_assignment.csv"
)

# =================================================================
# 2. EXTRACT INSAR TIMELINE CHECKLIST (TEMPORAL FILTER BASIS)
# =================================================================

# Load the satellite metadata to harvest target acquisition dates
insar_master_df = pd.read_feather(INSAR_TIMELINE_PATH)

# Reconstruct a complete date catalog: Add the designated initial baseline date
# ('D20150116') to the rest of the available 'D'-prefixed column headers
insar_date_columns = ["D20150116"] + [
    col for col in insar_master_df.columns if col.startswith("D")
]

# Strip the leading 'D' prefix and cast strings to real datetime objects.
# This array acts as a master temporal mask to sample the daily groundwater data.
insar_target_dates = pd.to_datetime([col[1:] for col in insar_date_columns])

# =================================================================
# 3. PARSE CROSS-REFERENCE MAP & CHOOSE TARGET STATION
# =================================================================

# Load the spreadsheet that cross-references compaction stations with aquifer layouts
layer_mapping_df = pd.read_csv(LAYER_ASSIGNMENT_PATH)

# Extract a unique catalog of all hydrogeological monitoring stations
available_stations = layer_mapping_df["station"].unique()

# Select the primary target station for processing (Index 0)
# selected_station = available_stations[0]  # Expected Output: 'ANHE'

for selected_station in available_stations:

    # Isolate the specific rows containing geological layer assignments for this station
    station_layer_subdf = layer_mapping_df.query("station == @selected_station")

    # =================================================================
    # 4. LOAD DAILY GROUNDWATER LEVEL (GWL) TIME SERIES
    # =================================================================

    # Identify all feather files for this station (may be >1 with screen-depth-first assignment)
    associated_feather_files = station_layer_subdf["feather_file"].unique()

    # Load all unique GWL feather files into a dict keyed by feather path
    gwl_dfs = {}
    for feather_relpath in associated_feather_files:
        if not feather_relpath or pd.isna(feather_relpath):
            continue
        gwl_file_path = os.path.join(
            PROJECT_DIR, str(feather_relpath).replace("/", "\\")
        )
        if os.path.exists(gwl_file_path):
            gdf = pd.read_feather(gwl_file_path)
            # Some feather files store dates as a DatetimeIndex (no 'datetime' column)
            if isinstance(gdf.index, pd.DatetimeIndex):
                gdf.index.name = "datetime"
            else:
                gdf["datetime"] = pd.to_datetime(gdf["datetime"])
                gdf = gdf.set_index("datetime")
            gwl_dfs[feather_relpath] = gdf

    if not gwl_dfs:
        print(f"  SKIP {selected_station}: no feather files could be loaded")
        continue

    # =================================================================
    # 5. VERTICAL PROFILE EXTRACTION & TIMELINE DOWN-SAMPLING
    # =================================================================

    # Storage list to collect the processed time series column of each aquifer layer
    layer_series_buffer = []

    # Identify all distinct underground layers monitored at this station (e.g., F1, F2, F3)
    available_layers = station_layer_subdf["layer"].unique()

    # Loop through each geological layer to isolate and align its hydrogeological behavior
    for current_layer in available_layers:

        # 1. Retrieve the assigned well code and its feather file for this layer
        layer_row = station_layer_subdf.query("layer == @current_layer").iloc[0]
        assigned_well_code = str(layer_row["assigned_wellcode"]).zfill(8)
        layer_feather = layer_row.get("feather_file", "")

        # 2. Select the correct GWL DataFrame for this layer
        layer_gwl_df = gwl_dfs.get(layer_feather)
        if layer_gwl_df is None:
            print(f"  SKIP {selected_station} {current_layer}: feather not loaded")
            continue

        # 3. Extract the specific water column tracking this well code
        if assigned_well_code not in layer_gwl_df.columns:
            print(f"  SKIP {selected_station} {current_layer}: "
                  f"wellcode {assigned_well_code} not in {layer_feather}")
            continue
        single_layer_ts = layer_gwl_df.loc[:, [assigned_well_code]]

        # 4. Derive the GWL station name from the feather file basename
        gwl_station_name = os.path.basename(str(layer_feather)).split("_")[0]

        # 5. Construct a standard compound identifier
        single_layer_ts.columns = [
            f"{selected_station}_{current_layer}_{gwl_station_name}_{assigned_well_code}"
        ]

        # 4. Down-sample the continuous daily records to match the specific overpass instances
        # of the InSAR radar. If a target date is missing in the source data, Pandas handles it with a NaN.
        aligned_layer_ts = single_layer_ts.reindex(insar_target_dates)

        # 5. Cache the synchronized column for the final stacking process
        layer_series_buffer.append(aligned_layer_ts)

    # =================================================================
    # 6. UNIFY AQUIFER HORIZONS & EXPORT STANDARDIZED FEATHER FILE
    # =================================================================

    # Bind the isolated layer columns side-by-side to construct a full vertical profile matrix
    station_gwl_profile_df = pd.concat(layer_series_buffer, axis=1)

    # Prepare the data matrix structure to meet strict Feather format requirements:
    # Move the Datetime index back to an explicit column and reset the index pointers.
    station_gwl_profile_df = station_gwl_profile_df.reset_index()
    station_gwl_profile_df = station_gwl_profile_df.rename(
        {"index": "datetime"}, axis=1
    )

    # Export the final consolidated table. The resulting dataset maps water levels directly
    # against InSAR observations for subsidence correlation analysis.
    output_file_name = f"{selected_station}_{gwl_station_name}.feather"
    station_gwl_profile_df.to_feather(
        os.path.join(OUTPUT_DIR, output_file_name)
    )