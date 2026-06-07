"""
data_mapper.py — Resolves station+layer to wellcode+feather_path
using the GWL-to-MLCW layer assignment (v3).

Also maps ring depths to layer names via the classify table.
"""

import pandas as pd
from pathlib import Path


class DataMapper:
    """Station-to-layer-to-well mapping using the v3 assignment table."""

    def __init__(self, assignment_df: pd.DataFrame, project_root: Path):
        self.df = assignment_df.copy()
        self.project_root = project_root
        # Ensure wellcodes are 8-digit strings
        self.df["assigned_wellcode"] = self.df["assigned_wellcode"].apply(
            lambda x: str(x).zfill(8) if pd.notna(x) and x != "" else x
        )

    def get_wells_for_station(self, station: str) -> list[tuple[str, str, Path]]:
        """Return list of (layer, wellcode_8digit, feather_path) tuples.

        Example:
            [('F1', '10070111', Path('data/gwl/well_timeseries/ANHE_gwl_timeseries.feather')),
             ('F2', '10070121', Path('data/gwl/well_timeseries/ANHE_gwl_timeseries.feather')),
             ('F3', '09060121', Path('data/gwl/well_timeseries/BEIGANG_gwl_timeseries.feather')),
             ...]
        """
        subset = self.df[self.df["station"] == station]
        results = []
        for _, row in subset.iterrows():
            layer = row["layer"]
            wc = str(row["assigned_wellcode"]).zfill(8)
            fp = row.get("feather_file", "")
            if pd.isna(fp) or fp == "":
                continue
            fpath = self.project_root / fp
            results.append((layer, wc, fpath))
        return results

    def get_layers_for_station(self, station: str) -> list[str]:
        """Return layer names for a station, in depth order."""
        subset = self.df[self.df["station"] == station].copy()
        if subset.empty:
            return []
        # Sort by layer depth
        subset = subset.sort_values("layer_depth_min_m")
        return subset["layer"].tolist()

    def get_well_label(self, station: str, layer: str) -> str:
        """Return a human-readable label for a (station, layer) GWL well.

        Example: '10070111 (ANHE)' or '' if no well assigned.
        """
        subset = self.df[
            (self.df["station"] == station) & (self.df["layer"] == layer)
        ]
        if subset.empty:
            return ""
        row = subset.iloc[0]
        wc = str(row["assigned_wellcode"]).zfill(8)
        feather = row.get("feather_file", "")
        stem = Path(feather).stem.replace("_gwl_timeseries", "") if feather else "?"
        return f"{wc} ({stem})"

    @staticmethod
    def map_rings_to_layers(classify_df: pd.DataFrame) -> dict[str, str]:
        """From classify table (columns: depth, layer), return {depth_str: layer_name}.

        Example: {'2.093': 'F1', '105.911': 'F2', ...}
        """
        if classify_df is None:
            return {}
        result = {}
        for _, row in classify_df.iterrows():
            depth = row["depth"]
            layer = row["layer"]
            key = str(depth)
            result[key] = layer
        return result

    @staticmethod
    def get_layer_depth_ranges(classify_df: pd.DataFrame) -> dict[str, tuple[float, float]]:
        """Return {layer_name: (min_depth, max_depth)} for legend labels."""
        if classify_df is None:
            return {}
        ranges = {}
        for layer, grp in classify_df.groupby("layer"):
            ranges[layer] = (grp["depth"].min(), grp["depth"].max())
        return ranges
