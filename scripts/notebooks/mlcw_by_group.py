# ==============================================================================
# 1. LOAD MASTER MLCW STATION METADATA FROM HDF5
# ==============================================================================

# File path to the pre-processed, imputed Multilayer Compaction Well (MLCW) master dataset
h5_fpath = r"D:\1000_SCRIPTS\003_Project002\20251111_GTWR003\1_PrepareDatasets\MLCW_3\20251230_MLCW_CRFP_Imputed_v4.h5"

# Load the HDF5 data payload and metadata attributes using specialized groundwater tools
mlcw_data, mlcw_info = gwatertools.open_HDF5(h5_fpath)

# Extract valid station identifiers (keys containing dictionary structures) from the HDF5 file
available_stations = [
    ele for ele in mlcw_data.keys() if isinstance(mlcw_data[ele], dict)
]
# Preview the first 5 available groundwater monitoring stations (e.g., TUKU)
available_stations[:5]

# ==============================================================================
# 2. LOCATE RECONSTRUCTED TIMESERIES DATA (InSAR-MLCW COUPLING PROJECT)
# ==============================================================================

# Folder containing reconstructed MLCW time-series data files associated with InSAR processing
mlcw_reconst_fld = r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\reconstructed"

# Gather paths of all reconstructed station text files (.csv format) inside the target directory
mlcw_reconst_files = glob(os.path.join(mlcw_reconst_fld, "*csv"))
# Quick check on the first 3 file paths
mlcw_reconst_files[:3]

# ------------------------------------------------------------------------------
# PURPOSE: DEFINE OUTPUT DIRECTORY AND ENSURE STORAGE PATH EXISTS
# ------------------------------------------------------------------------------

# Define the destination folder for storing aggregated layer-by-layer compaction datasets
output_savefld = r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\mlcw\group_byLayer_reconstr"

# Create the target directory automatically if it does not already exist
if not os.path.exists(output_savefld):
    os.makedirs(output_savefld, exist_ok=True)

# ------------------------------------------------------------------------------
# PURPOSE: BATCH-PROCESS ALL AVAILABLE STATIONS ACROSS THE CHOUSHUI RIVER ALLUVIAL FAN
# ------------------------------------------------------------------------------

# Iterate systematically through every available monitoring station using a progress bar
for select_station in tqdm(available_stations):
    try:
        # Match and retrieve the reconstructed time-series CSV file path for the active station
        mlcw_reconst_fpath = [
            f for f in mlcw_reconst_files if select_station in f
        ][0]

        # Extract depth values and binary-encoded layer information from the station's HDF5 schema
        classify_byStation = mlcw_data[select_station]["classify"]
        depth_arr = np.round(classify_byStation["depth"], 3)

        # Decode binary/byte layer names into standard, readable UTF-8 strings
        layer_arr = [ele.decode("utf-8") for ele in classify_byStation["layer"]]

        # Construct a reference dataframe mapping sensor anchor depths to specific hydrogeological layers
        classify_df = pd.DataFrame(
            data={"depth": depth_arr, "layer": layer_arr}
        )
        classify_df = classify_df.astype("str")

        # Generate an ordered sequence of unique aquifer/aquitard layers monitored at this well site
        all_layers = classify_df["layer"].unique()

        # ------------------------------------------------------------------------------
        # PURPOSE: AGGREGATE SENSOR COMPACTION DATA BY HYDROGEOLOGICAL LAYERS
        # ------------------------------------------------------------------------------

        # Load the station's historical timeseries data, initializing the timestamp column as a DatetimeIndex
        mlcw_reconst_df = pd.read_csv(
            mlcw_reconst_fpath, index_col=[0], parse_dates=[0]
        )

        # Instantiate a tracking list for processed depths and a fresh container for aggregated layer values
        cache = []
        output_mlcw_byLayer = pd.DataFrame(data=None, index=None)

        # Loop through each classified layer to sum up individual multi-depth sensor readings
        for idx, select_layer in enumerate(all_layers[:]):

            # Final-Layer Safeguard: Assign any remaining unmapped depths to the bottom layer
            # to ensure strict continuity and zero tracking omissions.
            if idx == (len(all_layers) - 1):
                depth_to_extract = mlcw_reconst_df.columns.difference(cache)
                depth_byLayer_str = classify_df.query(
                    "depth in @depth_to_extract"
                )["depth"].tolist()

            # Standard Operation: Isolate sensor depths explicitly designated for the current active layer
            else:
                depth_byLayer_str = classify_df.query("layer==@select_layer")[
                    "depth"
                ].tolist()

            # Slice displacement columns and sum them horizontally to establish a cumulative layer-wide metric
            mlcw_byDepth = mlcw_reconst_df.loc[:, depth_byLayer_str]
            mlcw_byDepth_sum = mlcw_byDepth.sum(axis=1)
            mlcw_byDepth_sum.name = select_layer

            # Horizontally merge the current layer's time-series into the active processing DataFrame
            output_mlcw_byLayer = pd.concat(
                [output_mlcw_byLayer, mlcw_byDepth_sum], axis=1
            )

            # Log these processed sensor depths into the cache to mask them in the final iteration loop
            cache.extend(depth_byLayer_str)

        # ------------------------------------------------------------------------------
        # PURPOSE: FORMAT DATAFRAMES AND EXPORT PRODUCTION DATASETS TO DISK
        # ------------------------------------------------------------------------------

        # Flatten the DatetimeIndex back into a normal column and rename it formally to "datetime"
        output_mlcw_byLayer = output_mlcw_byLayer.reset_index()
        output_mlcw_byLayer = output_mlcw_byLayer.rename(
            {"index": "datetime"}, axis=1
        )

        # Save the processed layer-by-layer cumulative compaction time-series dataset to a CSV file
        output_mlcw_byLayer.to_csv(
            os.path.join(
                output_savefld, f"{select_station}_reconst_grouped.csv"
            ),
            index=False,
        )

        # Export the standalone hydrogeological stratigraphy/depth mapping table for future model reference
        classify_df.to_csv(
            os.path.join(
                output_savefld, f"{select_station}_classify_table.csv"
            ),
            index=False,
        )
    except Exception as e:
        print(select_station, e)
        pass