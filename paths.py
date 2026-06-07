"""
paths.py — Cross-platform path resolver for the InSAR-MLCW project.

Detects the current OS and returns correct absolute paths for both:
  - Windows host:      D:\1000_SCRIPTS\... and D:\112_PROJECT_002
  - Ubuntu VM (HGFS):  /mnt/hgfs/1000_SCRIPTS/... and /mnt/hgfs/112_PROJECT_002

Usage in any script:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))  # if not already on path
    from paths import SCRIPTS_ROOT, DOCS_ROOT, DATA_ROOT

Migration helper for legacy scripts with hardcoded D:\ strings:
    from paths import resolve
    p = resolve(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\foo.csv")
"""

import sys
from pathlib import Path


# ── Root detection ────────────────────────────────────────────────────────────

def _detect_roots() -> tuple:
    """Return (SCRIPTS_ROOT, DOCS_ROOT) for the current OS/environment."""
    if sys.platform == "win32":
        return (
            Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2"),
            Path(r"D:\112_PROJECT_002"),
        )
    else:
        # Linux: VMware HGFS shared folder mount
        # D:\1000_SCRIPTS\... → /mnt/hgfs/1000_SCRIPTS/...
        # D:\112_PROJECT_002  → /mnt/hgfs/112_PROJECT_002
        return (
            Path("/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2"),
            Path("/mnt/hgfs/112_PROJECT_002"),
        )


SCRIPTS_ROOT, DOCS_ROOT = _detect_roots()

# ── Frequently used sub-paths (derived — never hardcode these elsewhere) ───────

DATA_ROOT          = SCRIPTS_ROOT / "data"
RESULTS_ROOT       = SCRIPTS_ROOT / "results"

MLCW_RECONST_DIR   = DATA_ROOT / "mlcw" / "group_byLayer_reconstr"
MLCW_MODELED_DIR   = DATA_ROOT / "mlcw" / "group_byLayer_modeled"
GWL_TIMESERIES_DIR = DATA_ROOT / "gwl" / "mlcw_gwl_timeseries"
GWL_WELL_INFO      = DATA_ROOT / "gwl" / "well_info" / "gwl_allwells_flat.csv"
GWL_ASSIGNMENT     = DATA_ROOT / "gwl" / "gwl_to_mlcw_layer_assignment_v4.csv"

INSAR_FEATHER      = DATA_ROOT / "insar" / "timeseries" / "mlcw_interp_insar_IDW_extend.feather"
IHMF_CONFIG        = DATA_ROOT / "ihmf_config.json"

IHMF_RESULTS_DIR   = RESULTS_ROOT / "ihmf"
DATA_ANALYSIS_DIR  = RESULTS_ROOT / "data_analysis"
DIRECT_RATIO_DIR   = RESULTS_ROOT / "direct_ratio"

# Docs-root sub-paths
DISCUSSIONS_DIR    = DOCS_ROOT / "discussions"
PROGRESS_MD        = DOCS_ROOT / "PROGRESS.md"


# ── Legacy migration helper ───────────────────────────────────────────────────

_WIN_SCRIPTS = r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2"
_WIN_DOCS    = r"D:\112_PROJECT_002"


def resolve(win_path: str) -> Path:
    """
    Convert a hardcoded Windows D:\... path string to the correct OS path.

    Examples
    --------
    resolve(r"D:\\1000_SCRIPTS\\004_Project003\\20260427_InSAR_MLCW_v2\\data\\foo.csv")
    # Windows → D:\1000_SCRIPTS\...\data\foo.csv
    # Linux   → /mnt/hgfs/1000_SCRIPTS/.../data/foo.csv

    resolve(r"D:\\112_PROJECT_002\\discussions\\note.md")
    # Windows → D:\112_PROJECT_002\discussions\note.md
    # Linux   → /mnt/hgfs/112_PROJECT_002/discussions/note.md
    """
    # Normalise separators
    p = win_path.replace("\\", "/")
    scripts_norm = _WIN_SCRIPTS.replace("\\", "/")
    docs_norm    = _WIN_DOCS.replace("\\", "/")

    if p.startswith(scripts_norm):
        rel = p[len(scripts_norm):].lstrip("/")
        return SCRIPTS_ROOT / rel
    elif p.startswith(docs_norm):
        rel = p[len(docs_norm):].lstrip("/")
        return DOCS_ROOT / rel
    else:
        # Unknown root — return as-is (best effort)
        return Path(win_path)


# ── Quick self-test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Platform    : {sys.platform}")
    print(f"SCRIPTS_ROOT: {SCRIPTS_ROOT}")
    print(f"DOCS_ROOT   : {DOCS_ROOT}")
    print(f"DATA_ROOT   : {DATA_ROOT}")
    print()
    # Test resolve()
    test = r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\ihmf_config.json"
    print(f"resolve test: {resolve(test)}")
    assert resolve(test) == IHMF_CONFIG, "resolve() mismatch!"
    print("All checks passed.")
