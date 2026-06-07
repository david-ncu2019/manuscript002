# ---------------------------------------------------------
# 1. Setup paths and input parameters
# ---------------------------------------------------------
MLCW_MODEL_FLD = "MLCW_modeled/"
GPS_MODEL_FLD = "GPS_modeled/"
SAVEFIG_FLD = "MLCW_GPS_figs/"
PAIRS_EXCEL = "MLCW_GPS_pairs.xlsx"

# ---------------------------------------------------------
# 2. Find corresponding GPS station
# ---------------------------------------------------------
# Read the pairs and get the corresponding GPS station name
station_pairs = pd.read_excel(PAIRS_EXCEL, index_col=[1])


available_stations = station_pairs.index.tolist()

# Select the MLCW station to analyze
# select_mlcw = "TUKU"
for select_mlcw in tqdm(available_stations):
    try:
        gps_byMLCW = station_pairs.loc[select_mlcw, "station_co"]
        # ---------------------------------------------------------
        # 3. Load Data
        # ---------------------------------------------------------
        # Find the first matching CSV for the MLCW station and read it
        mlcw_csv_path = glob(
            os.path.join(MLCW_MODEL_FLD, f"*{select_mlcw}*csv")
        )[0]
        mlcw_df = (
            pd.read_csv(mlcw_csv_path, index_col=[0], parse_dates=[0]) * 1000
        )

        # Find the first matching CSV for the GPS station and read it
        gps_csv_path = glob(os.path.join(GPS_MODEL_FLD, f"*{gps_byMLCW}*csv"))[
            0
        ]
        gps_df = (
            pd.read_csv(gps_csv_path, index_col=[0], parse_dates=[0]) * 1000
        )

        # ---------------------------------------------------------
        # 4. Align Data to Mutual Timeframe
        # ---------------------------------------------------------
        def get_aligned_df(df, mutual_time):
            """
            Filter dataframe by mutual dates and shift values so the
            first observation starts at 0 for a clean comparison baseline.
            """
            new_df = df.loc[mutual_time]
            new_df = new_df.subtract(new_df.iloc[0, :], axis=1)
            return new_df

        # Find intersection of dates between MLCW and GPS
        mutual_dates = mlcw_df.index.intersection(gps_df.index)

        # Align both dataframes to the mutual dates
        aligned_mlcw = get_aligned_df(df=mlcw_df, mutual_time=mutual_dates)
        aligned_gps = get_aligned_df(df=gps_df, mutual_time=mutual_dates)

        # Sum all components for MLCW to get total displacement
        aligned_mlcw_arr = aligned_mlcw.sum(axis=1)

        # Extract the 'modeled' column for GPS
        aligned_gps_arr = aligned_gps["modeled"]

        # ---------------------------------------------------------
        # 5. Visualize with appgeopy
        # ---------------------------------------------------------
        # Create 2 subplots: Top (larger) for displacement, Bottom (smaller) for the ratio
        fig, (ax1, ax2) = plt.subplots(
            nrows=2,
            ncols=1,
            figsize=(11.7, 8.27),  # A4 landscape from appgeopy's BASE_SIZE
            gridspec_kw={"height_ratios": [3, 1]},
            sharex=True,
        )

        # --- Top Plot: Displacement Comparison ---
        ax1.plot(
            aligned_mlcw_arr.index,
            aligned_mlcw_arr.values,
            label="MLCW",
            color="blue",
            linewidth=2,
        )
        ax1.plot(
            aligned_gps_arr.index,
            aligned_gps_arr.values,
            label="GPS",
            color="orange",
            linewidth=2,
        )

        # Use appgeopy's configure_axis for styling the top plot
        visualize.configure_axis(
            ax1,
            ylabel="Displacement (mm)",
            title=f"Deformation Comparison: MLCW ({select_mlcw}) vs GPS ({gps_byMLCW})",
        )
        visualize.configure_legend(ax1, frameon=True)

        # --- Bottom Plot: Ratio ---
        ratio_arr = aligned_mlcw_arr / aligned_gps_arr
        ax2.plot(
            ratio_arr.index,
            ratio_arr.values,
            label="MLCW / GPS Ratio",
            color="red",
            linestyle="--",
        )

        # Add a horizontal line at 1.0 to show perfect agreement
        ax2.axhline(1.0, color="black", linewidth=1, linestyle=":")
        ax2.set_ylim(bottom=-1.5, top=1.5)

        # Use appgeopy's configure_axis for styling the bottom plot
        visualize.configure_axis(ax2, xlabel="Date", ylabel="Ratio")
        visualize.configure_legend(ax2, frameon=True, loc="lower left")

        # Auto-format dates for better x-axis readability and tighten layout
        fig.autofmt_xdate(rotation=45, ha="center")
        fig.tight_layout()

        visualize.save_figure(
            fig=fig,
            savepath=os.path.join(SAVEFIG_FLD, f"{select_mlcw}_mlcw_gps.png"),
        )
        # Show the plot
        # plt.show()
        plt.close()

        # ---------------------------------------------------------
        # 6. Calculate Slopes and Save to JSON
        # ---------------------------------------------------------
        from appgeopy.analysis import get_linear_trend
        import json

        # get_linear_trend returns (trend_series, slope_per_point) in mm/point
        _, mlcw_slope_per_point = get_linear_trend(aligned_mlcw_arr)
        _, gps_slope_per_point = get_linear_trend(aligned_gps_arr)

        # Convert slope from mm/point to cm/year
        total_days = (mutual_dates[-1] - mutual_dates[0]).days
        total_years = total_days / 365.25
        num_intervals = len(mutual_dates) - 1
        
        if total_years > 0 and num_intervals > 0:
            mlcw_slope_cm_yr = mlcw_slope_per_point * num_intervals / total_years * 0.1
            gps_slope_cm_yr = gps_slope_per_point * num_intervals / total_years * 0.1
            
            slope_data = {
                select_mlcw: {
                    "MLCW_slope": mlcw_slope_cm_yr,
                    "GPS_slope": gps_slope_cm_yr,
                    "MLCW_GPS_ratio": mlcw_slope_cm_yr / gps_slope_cm_yr if gps_slope_cm_yr != 0 else None
                }
            }
            
            json_path = os.path.join(SAVEFIG_FLD, f"{select_mlcw}_slope_ratio.json")
            with open(json_path, "w") as f:
                json.dump(slope_data, f, indent=4)
                
    except Exception as e:
        print(select_mlcw, gps_byMLCW, e)
        print()
        pass