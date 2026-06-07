"""
Visualise MLCW-aligned GWL timeseries from mlcw_gwl_timeseries feather files.

Produces one A4-portrait figure per station with stacked subplots (one per
hydrogeological layer), for quick visual inspection of the 37-station dataset.

Output: data/gwl/mlcw_gwl_timeseries/figs/  (*.png, 300 dpi)
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path
from collections import OrderedDict

# ── Constants ──────────────────────────────────────────────────────────
LAYER_CODES = ["F1", "T1", "F2", "T2", "F3", "F4"]
LINE_COLOR = "#1f77b4"
LINE_WIDTH = 1.2
CM = 1 / 2.54  # inches per cm (A4 = 21 × 29.7 cm)

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "gwl" / "mlcw_gwl_timeseries"
OUT_DIR = DATA_DIR / "figs"

# ── Matplotlib style ───────────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 13,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "figure.dpi": 100,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "lines.linewidth": LINE_WIDTH,
})


# ── Helpers ────────────────────────────────────────────────────────────
def extract_layer_code(col_name: str) -> str | None:
    """Extract layer code (F1/T1/F2/T2/F3/F4) from a column name.

    Column format: {STATION}_{LAYER}_{GWL_STATION}_{WELLCODE}
    """
    parts = col_name.split("_")
    if len(parts) >= 2 and parts[1] in LAYER_CODES:
        return parts[1]
    return None


def load_station_data(filepath: Path) -> dict:
    """Read a single feather file and return organised data."""
    df = pd.read_feather(filepath)
    station_name = filepath.stem.split("_")[0]  # e.g. TUKU from TUKU_TUKU

    # Identify layer columns and parse their codes
    layers = OrderedDict()
    wellcodes = {}
    for col in df.columns:
        if col == "datetime":
            continue
        code = extract_layer_code(col)
        if code is None:
            continue
        layers[code] = df[col]
        wellcodes[code] = col.split("_")[-1]  # 8-digit wellcode

    # Reorder to stratigraphic sequence (F1 -> F4)
    ordered = OrderedDict()
    for code in LAYER_CODES:
        if code in layers:
            ordered[code] = layers[code]

    # Count NaN rows (whole-row gaps)
    n_nan = df["datetime"].isna().sum()  # should be 0
    # Count rows where ALL layer columns are NaN
    layer_cols = list(ordered.values())
    if layer_cols:
        all_nan = pd.concat(layer_cols, axis=1).isna().all(axis=1).sum()
    else:
        all_nan = 0

    return {
        "station_name": station_name,
        "datetime": df["datetime"],
        "layers": ordered,
        "wellcodes": wellcodes,
        "has_nan_gaps": all_nan > 0,
        "n_nan_rows": all_nan,
    }


def plot_single_station(data: dict, output_path: Path) -> None:
    """Create A4 portrait figure with stacked subplots, one per layer."""
    layers = data["layers"]
    n_layers = len(layers)
    if n_layers == 0:
        print(f"  SKIP {data['station_name']}: no layer columns found")
        return

    fig, axes = plt.subplots(
        n_layers, 1, sharex=True,
        figsize=(21 * CM, 29.7 * CM),
    )
    if n_layers == 1:
        axes = [axes]  # make iterable

    for ax, (code, series) in zip(axes, layers.items()):
        wellcode = data["wellcodes"].get(code, "?")
        ax.plot(
            data["datetime"], series,
            color=LINE_COLOR, linewidth=LINE_WIDTH,
        )
        ax.set_title(f"{code}  (well {wellcode})", fontsize=12, pad=4)
        ax.set_ylabel("Head (m)")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.grid(True, linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)

    # X-axis date formatting on bottom subplot
    axes[-1].set_xlabel("Date")
    axes[-1].xaxis.set_major_locator(mdates.YearLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[-1].xaxis.set_minor_locator(mdates.MonthLocator())

    # Figure-level title
    suptitle = f"GWL Timeseries — {data['station_name']}"
    if data["has_nan_gaps"]:
        suptitle += f"  [{data['n_nan_rows']} epochs missing]"
    fig.suptitle(suptitle, fontsize=16, fontweight="bold", y=0.98)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"  {data['station_name']}: {n_layers} layers, "
          f"{'NaN' if data['has_nan_gaps'] else 'clean'}, "
          f"-> {output_path.name}")


# ── Main ───────────────────────────────────────────────────────────────
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(DATA_DIR.glob("*.feather"))
    print(f"Found {len(files)} feather files in {DATA_DIR}\n")

    ok = 0
    skip = 0
    for fp in files:
        try:
            data = load_station_data(fp)
            out_path = OUT_DIR / f"{data['station_name']}_gwl_timeseries.png"
            plot_single_station(data, out_path)
            ok += 1
        except Exception as exc:
            print(f"  FAIL {fp.stem}: {exc}")
            skip += 1

    print(f"\nDone: {ok} plotted, {skip} failed")
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
