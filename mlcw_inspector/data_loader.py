"""
data_loader.py — Loads and caches all data files for the MLCW Inspector.

Config, assignment, and InSAR are loaded once at init.
Per-station data (MLCW reconst, rings, classify table, GWL feathers)
is loaded on demand and cached.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

# ── Resolve project root so this module works from any working directory ──
MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parent

# Try the project-level paths.py; fall back to relative resolution
try:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from paths import DATA_ROOT as _paths_data_root
    DATA_ROOT = _paths_data_root
except ImportError:
    DATA_ROOT = PROJECT_ROOT / "data"


class DataLoader:
    """Loads data files. Caches config + assignment + InSAR once;
    per-station data cached on first access."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or PROJECT_ROOT
        self.data_root = self.project_root / "data"

        # ── One-time loads ─────────────────────────────────────────────
        self.config = self._load_config()
        self.assignment = self._load_assignment_csv()
        self.insar_df = self._load_insar_csv()

        # Build station list from config entries
        entries = self.config.get("entries", [])
        if isinstance(entries, dict):
            entries = list(entries.values())
        self.stations = sorted(
            set(e["station"] for e in entries if e.get("station"))
        )

        # Per-station cache
        self._cache: dict[str, dict] = {}

    # ── Config ────────────────────────────────────────────────────────

    def _load_config(self) -> dict:
        path = self.data_root / "ihmf_config.json"
        with open(path) as f:
            return json.load(f)

    # ── Assignment CSV ────────────────────────────────────────────────

    def _load_assignment_csv(self) -> pd.DataFrame:
        """Load v3 assignment CSV. Try JSON sidecar first for type safety."""
        json_path = self.data_root / "gwl" / "gwl_to_mlcw_layer_assignment.json"
        if json_path.exists():
            with open(json_path) as f:
                records = json.load(f)
            return pd.DataFrame(records)
        # Fallback: CSV with zero-padding guard
        csv_path = self.data_root / "gwl" / "gwl_to_mlcw_layer_assignment_v3.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path, dtype={"assigned_wellcode": str, "station": str})
        else:
            csv_path = self.data_root / "gwl" / "gwl_to_mlcw_layer_assignment.csv"
            df = pd.read_csv(csv_path, dtype={"assigned_wellcode": str, "station": str})
        # Zero-pad wellcodes
        df["assigned_wellcode"] = df["assigned_wellcode"].apply(
            lambda x: str(x).zfill(8) if pd.notna(x) and x != "" else x
        )
        return df

    # ── InSAR ─────────────────────────────────────────────────────────

    def _load_insar_csv(self) -> pd.DataFrame:
        path = self.data_root / "insar" / "InSAR_measures_at_MLCW.csv"
        df = pd.read_csv(path, parse_dates=[0])
        df.columns = [c.strip() for c in df.columns]
        rename = {df.columns[0]: "datetime"}
        df = df.rename(columns=rename)
        df["datetime"] = pd.to_datetime(df["datetime"])
        # Columns are station names; values in metres → convert to mm
        for col in df.columns:
            if col != "datetime":
                df[col] = df[col] * 1000.0
        return df

    # ── Per-station data ──────────────────────────────────────────────

    def get_station_data(self, station: str) -> dict:
        """Return cached data dict for a station.

        Keys: reconst, ring, classify, gwl_feathers, has_reconst, has_rings.
        """
        if station in self._cache:
            return self._cache[station]

        data = {
            "reconst": self._load_mlcw_reconst(station),
            "ring": self._load_mlcw_rings(station),
            "classify": self._load_classify_table(station),
            "gwl_feathers": {},
            "has_reconst": False,
            "has_rings": False,
        }
        data["has_reconst"] = data["reconst"] is not None
        data["has_rings"] = data["ring"] is not None

        # Load GWL feathers (needs mapper for wellcode resolution)
        # We defer this to the orchestrator, which calls load_gwl_for_station
        self._cache[station] = data
        return data

    def load_gwl_for_station(self, station: str,
                             mapper) -> dict[str, pd.Series]:
        """Load GWL head series for each layer at a station.

        Uses the DataMapper to resolve (layer, wellcode, feather_path).
        Returns {layer_name: pd.Series(head_m values, index=datetime)}.
        """
        wells = mapper.get_wells_for_station(station)

        # Group by feather path (load each file once)
        feather_groups: dict[str, list[tuple]] = {}
        for layer, wellcode, feather_path in wells:
            key = str(feather_path)
            feather_groups.setdefault(key, []).append((layer, wellcode))

        result: dict[str, pd.Series] = {}
        for feather_rel, pairs in feather_groups.items():
            fpath = self.project_root / feather_rel
            if not fpath.exists():
                for layer, wc in pairs:
                    result[layer] = pd.Series(dtype=float)
                continue
            df = pd.read_feather(fpath)
            df["datetime"] = pd.to_datetime(df["datetime"])
            for layer, wellcode in pairs:
                if wellcode in df.columns:
                    series = df.set_index("datetime")[wellcode].dropna()
                    series.name = "head_m"
                    result[layer] = series
                else:
                    result[layer] = pd.Series(dtype=float)

        # Update cache
        if station in self._cache:
            self._cache[station]["gwl_feathers"] = result
        return result

    # ── Internal loaders ──────────────────────────────────────────────

    def _load_mlcw_reconst(self, station: str) -> pd.DataFrame | None:
        path = (self.data_root / "mlcw" / "group_byLayer_reconstr"
                / f"{station}_reconst_grouped.csv")
        if not path.exists():
            return None
        df = pd.read_csv(path, parse_dates=["datetime"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def _load_mlcw_rings(self, station: str) -> pd.DataFrame | None:
        path = (self.data_root / "mlcw" / "raw_timeseries"
                / f"{station}_ringbyring.csv")
        if not path.exists():
            return None
        df = pd.read_csv(path, parse_dates=["datetime"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df

    def _load_classify_table(self, station: str) -> pd.DataFrame | None:
        path = (self.data_root / "mlcw" / "group_byLayer_reconstr"
                / f"{station}_classify_table.csv")
        if not path.exists():
            return None
        return pd.read_csv(path)
