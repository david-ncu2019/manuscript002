"""
Batch run 2S-TOOL Python on all prepared input files.

Processes every 2STOOL_*.xlsx in data/gwl/2stool_inputs/ through the
2S-TOOL Python pipeline, writing per-file outputs to data/gwl/2stool_outputs/.

Usage:
    conda activate isce_ncu3
    python scripts/09_trackB/batch_run_2stool.py              # all files
    python scripts/09_trackB/batch_run_2stool.py --station TUKU  # one station
    python scripts/09_trackB/batch_run_2stool.py --dry-run       # list files only
"""

import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
INPUT_DIR = PROJECT_ROOT / "data" / "gwl" / "2stool_inputs"
OUTPUT_DIR = PROJECT_ROOT / "data" / "gwl" / "2stool_outputs"

# 2S-TOOL Python package location
TWOSTOOL_PYTHON = PROJECT_ROOT / "tools" / "2S-TOOL-Python"


def parse_filename(path: Path) -> dict | None:
    parts = path.stem.split("_", 2)
    if len(parts) == 3 and parts[0] == "2STOOL":
        return {"station": parts[1], "layer": parts[2]}
    return None


def _check_env() -> None:
    """Fail early with a clear message if scipy is not available."""
    try:
        import scipy  # noqa: F401
    except ImportError:
        sys.exit(
            "scipy not found. Activate the isce_ncu3 conda environment first:\n"
            "    conda activate isce_ncu3\n"
            "    python scripts/09_trackB/batch_run_2stool.py [args]\n"
            "Or use conda run:\n"
            "    conda run -n isce_ncu3 python scripts/09_trackB/batch_run_2stool.py [args]\n"
        )


def main():
    _check_env()
    parser = argparse.ArgumentParser(
        description="Batch-run 2S-TOOL Python on all prepared input files."
    )
    parser.add_argument("--stations", type=str, default=None,
                        help="Comma-separated station names (e.g. TUKU,ANHE).")
    parser.add_argument("--layer", type=str, default=None,
                        help="Process only this layer (e.g. F3).")
    parser.add_argument("--dry-run", action="store_true",
                        help="List files without processing.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Process at most N files (for testing).")
    args = parser.parse_args()

    station_filter = (
        {s.strip() for s in args.stations.split(",")} if args.stations else None
    )

    files = sorted(INPUT_DIR.glob("2STOOL_*.xlsx"))
    if not files:
        logger.error(f"No 2STOOL_*.xlsx files found in {INPUT_DIR}")
        sys.exit(1)

    # Filter by station / layer
    if station_filter or args.layer:
        filtered = []
        for fp in files:
            meta = parse_filename(fp)
            if meta is None:
                continue
            if station_filter and meta["station"] not in station_filter:
                continue
            if args.layer and meta["layer"] != args.layer:
                continue
            filtered.append(fp)
        files = filtered

    if args.limit:
        files = files[:args.limit]

    logger.info(f"Batch: {len(files)} files → {OUTPUT_DIR}")

    if args.dry_run:
        for fp in files:
            meta = parse_filename(fp)
            tag = f"{meta['station']} {meta['layer']}" if meta else fp.name
            logger.info(f"  {tag}")
        return

    # Import 2S-TOOL Python
    sys.path.insert(0, str(TWOSTOOL_PYTHON))
    import twostool_python.config as t2cfg
    from twostool_python.pipeline import run_pipeline

    # Set hc lookup paths (local-only, not for upstream)
    t2cfg.HC_WELL_TIMESERIES_DIR = str(PROJECT_ROOT / "data" / "gwl" / "well_timeseries")
    t2cfg.HC_ASSIGNMENT_CSV = str(PROJECT_ROOT / "data" / "gwl" / "gwl_to_mlcw_layer_assignment_v3.csv")
    t2cfg.HC_WELL_ELEVATIONS_CSV = str(PROJECT_ROOT / "data" / "gwl" / "well_info" / "gwl_allwells_flat.csv")

    ok = skv_only = errors = 0
    t0 = time.monotonic()

    for i, fp in enumerate(files):
        meta = parse_filename(fp)
        tag = f"{meta['station']} {meta['layer']}" if meta else fp.name
        try:
            result = run_pipeline(fp, OUTPUT_DIR)
            status = result["status"]
            if status == "ok":
                ok += 1
            elif status == "skv_only":
                skv_only += 1
            else:
                errors += 1
            summary = result.get("summary", {})
            skv_str = f"{summary.get('skv', 0):.4e}" if summary.get("skv") else "—"
            ske_str = f"{summary.get('ske_weighted', 0):.4e}" if summary.get("ske_weighted") else "—"
            logger.info(
                f"  [{i+1}/{len(files)}] {tag:20s}  {status:8s}  "
                f"s_kv={skv_str}  s_ke_w={ske_str}"
            )
        except Exception as exc:
            logger.error(f"  [{i+1}/{len(files)}] {tag:20s}  ERROR: {exc}")
            errors += 1

    elapsed = time.monotonic() - t0
    logger.info(
        f"\nDone in {elapsed:.0f}s: {ok} ok, {skv_only} skv-only, "
        f"{errors} errors  ({len(files)} total)"
    )

    if ok + skv_only > 0:
        logger.info(f"Outputs in: {OUTPUT_DIR}")
        logger.info("Run collect_2stool_results.py to aggregate.")


if __name__ == "__main__":
    main()
