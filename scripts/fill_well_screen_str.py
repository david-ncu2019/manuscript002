#!/usr/bin/env python3
"""
Fill missing well_screen_str in gwl_allwells_flat.csv using screen depth data
from markdown table files in well_info_output/.
"""

import re
import sys
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT / "data" / "gwl" / "well_info" / "gwl_allwells_flat.csv"
MD_DIR = PROJECT / "data" / "gwl" / "well_info" / "well_info_output"

# ── Columns of interest ────────────────────────────────────────────────────
COL_WELLCODE = "電腦編號"
COL_SCREEN = "濾水管位置 (M)"


def parse_md_table(text: str) -> list[dict[str, str]]:
    """Parse a markdown table into a list of dicts (column_name -> cell_text).

    Handles:
      - Standard separator rows: | --- | --- | --- |
      - Compressed separators: |---|---|---|---|
      - Separators with dashes only: | - | - | - |
      - Leading/trailing pipes, whitespace inside cells.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 3:
        return []

    # ── Locate the separator row (the second row of a markdown table) ──
    # Heuristic: a row where every pipe-delimited segment consists only of
    # dashes, optional colons, and optional whitespace.
    sep_idx = None
    for i, ln in enumerate(lines):
        # A separator row must contain at least 2 pipes and all non-empty
        # segments stripped match ^:?-+:?$
        parts = [p.strip() for p in ln.split("|")]
        parts = [p for p in parts if p]  # ignore leading/trailing empty
        if len(parts) >= 2 and all(re.fullmatch(r":?-{3,}:?", p) for p in parts):
            sep_idx = i
            break

    if sep_idx is None or sep_idx >= len(lines) - 1:
        return []  # no data rows after separator

    # ── Header row is immediately before separator ──────────────────────
    header_line = lines[sep_idx - 1]
    headers = [h.strip() for h in header_line.split("|")]
    headers = [h for h in headers if h]  # drop empties from leading/trailing pipe

    # ── Data rows are everything after separator ────────────────────────
    rows = []
    for ln in lines[sep_idx + 1:]:
        # Stop if we hit the start of a new table (another separator) or
        # a non-table line that doesn't start with '|'.
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.split("|")]
        # First and last cells are empty due to leading/trailing pipe
        cells = cells[1:-1] if len(cells) > len(headers) else cells
        if len(cells) < len(headers):
            continue  # malformed row
        row = dict(zip(headers, cells[: len(headers)]))
        rows.append(row)

    return rows


def build_screen_mapping(md_dir: Path) -> tuple[dict[str, str], int, int]:
    """Scan all .md files under md_dir, parse tables, and return:
      - mapping: wellcode -> screen_str (excludes '-' values)
      - n_files: number of .md files parsed
      - n_wellcodes: number of unique wellcodes collected
    """
    mapping: dict[str, str] = {}
    files = sorted(md_dir.glob("*.md"))
    n_files = len(files)

    for fp in files:
        text = fp.read_text(encoding="utf-8")
        rows = parse_md_table(text)
        for row in rows:
            wc = row.get(COL_WELLCODE, "").strip()
            screen = row.get(COL_SCREEN, "").strip()
            if not wc:
                continue
            # Only add if screen is a non-trivial value (ignore '-' which
            # means "no data available in the PDF")
            if screen and screen != "-":
                mapping[wc] = screen
            elif screen == "-":
                # Explicitly mark as no-data, but we still might want to
                # record that we *saw* this wellcode so we don't leave it
                # as a "not found" but rather a "found but no screen data"
                if wc not in mapping:
                    mapping[wc] = ""  # empty string = found but no screen info

    return mapping, n_files, len(mapping)


def main():
    # ── Read CSV ────────────────────────────────────────────────────────
    df = pd.read_csv(CSV_PATH)
    missing_mask = df["well_screen_str"].isna() | (df["well_screen_str"] == "")
    n_missing_before = missing_mask.sum()
    n_total = len(df)

    print(f"CSV total rows: {n_total}")
    print(f"Rows with missing well_screen_str before: {n_missing_before}")

    # ── Build mapping from markdown files ───────────────────────────────
    mapping, n_files, n_wellcodes = build_screen_mapping(MD_DIR)
    print(f"\nMarkdown files parsed: {n_files}")
    print(f"Unique wellcodes in mapping: {n_wellcodes}")
    print(f"Sample entries from mapping:")
    for k in list(mapping.keys())[:8]:
        print(f"  {k} -> '{mapping[k]}'")

    # ── Fill missing values ─────────────────────────────────────────────
    updated_count = 0
    found_no_data_count = 0
    not_found_count = 0

    for idx in df[missing_mask].index:
        wc = str(df.at[idx, "wellcode"]).strip()
        if wc in mapping:
            val = mapping[wc]
            if val and val != "-":
                df.at[idx, "well_screen_str"] = val
                updated_count += 1
            else:
                # mapping says "-" (no screen info in PDF) or empty
                found_no_data_count += 1
        else:
            not_found_count += 1

    n_missing_after = df["well_screen_str"].isna().sum() + (df["well_screen_str"] == "").sum()

    # ── Write back ──────────────────────────────────────────────────────
    df.to_csv(CSV_PATH, index=False)
    print(f"\nRows updated with screen_str: {updated_count}")
    print(f"Rows found but marked no-data ('-'): {found_no_data_count}")
    print(f"Rows NOT found in any markdown: {not_found_count}")
    print(f"Rows still missing after fill: {n_missing_after}")

    # ── Show a few newly filled rows ────────────────────────────────────
    if updated_count > 0:
        print("\nSample newly filled rows:")
        filled = df[~df["well_screen_str"].isna() & (df["well_screen_str"] != "")]
        # Show rows that were previously missing
        for _, r in filled.tail(min(10, updated_count)).iterrows():
            print(f"  {r['station']:12s} {r['wellcode']:10s} -> '{r['well_screen_str']}'")


if __name__ == "__main__":
    main()
