"""
Entry point: PYTHONPATH="" conda run -n isce_ncu3 python -m mlcw_inspector

Opens the Panel/Bokeh dashboard in a browser tab with MLCW + GWL + InSAR
time series, a station dropdown, Layers/Rings mode toggle, and per-layer
visibility checkboxes.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from mlcw_inspector import DataLoader, DataMapper, MLCWInspector


def main():
    loader = DataLoader()
    mapper = DataMapper(loader.assignment, loader.project_root)
    app = MLCWInspector(loader, mapper)
    print(f"Loaded {len(loader.stations)} stations.")
    print("Opening dashboard in your browser …")
    app.show()


if __name__ == "__main__":
    main()
