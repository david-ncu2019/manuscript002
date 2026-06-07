"""
extract_well_info_direct.py
===========================
Pure regex + PyPDF2 extraction of well information from Well_Info_2024.pdf.
No LLM API is used.

Output:
  - One markdown file per page → well_info_output/Well_Info_2024_page_NNN_table.md
  - One combined CSV          → well_info_combined.csv
"""

import re
import csv
import sys
import os

# Force stdout to UTF-8 so Chinese characters in warnings don't crash on cp1252 consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

try:
    import PyPDF2
except ImportError:
    print("ERROR: PyPDF2 not found. Install with: pip install PyPDF2")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PDF_PATH = Path(r"D:\VINHTRUONG\001_STUDY_AREA\GroundwaterObservation"
                r"\@DOWNLOAD_WRA_GWOB_YEARBOOK_PROJECT\Well_Info_2024.pdf")
OUT_DIR   = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2"
                 r"\gwl_inspection\well_info_output")
CSV_PATH  = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2"
                 r"\gwl_inspection\well_info_combined.csv")

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# 8-character computer ID (digits and letters)
COMP_ID_RE = re.compile(r'\b([0-9A-Za-z]{8})\b')

# Two floats that look like TWD97 coordinates
# X (easting)  ~ 150,000 – 230,000
# Y (northing) ~ 2,550,000 – 2,720,000
# They appear as e.g.  200779.080  2662059.143
COORD_RE = re.compile(
    r'(\d{6,7}\.\d+)\s+(\d{7,9}\.\d+)'  # two floats with at least 6/7 digits
)

# Elevation and casing depth: floats with exactly 4 decimal places
FLOAT4_RE = re.compile(r'\d+\.\d{4}')

# 3-digit screen type code (standalone, not part of a float)
SCREEN_CODE_RE = re.compile(r'(?<!\d)(\d{3})(?!\d)')

# Date period: YYYY/MM~ optionally followed by YYYY/MM
DATE_RE = re.compile(r'(\d{4}/\d{2}~(?:\d{4}/\d{2})?)')

# Bare depth pair: float~float  (screen interval)
DEPTH_PAIR_RE = re.compile(r'\d+(?:\.\d+)?~\d+(?:\.\d+)?')

# Lines that are purely depth pairs (continuation lines)
DEPTH_LINE_RE = re.compile(r'^\s*(\d+(?:\.\d+)?~\d+(?:\.\d+)?[\s]*)+\s*$')

# Header sentinel strings – lines containing any of these are header lines
HEADER_TOKENS = [
    '測區編號', 'TWD97TM2', '濾 水 管 位 置', '濾水管位置',
    '資  料  起  迄', '資料起迄', '(X座標)', '(Y座標)',
    '電 腦 編 號', '電腦編號', '井    名', '井管深度', '井  頂  高',
    '(M)', '現有自記', '一覽表', '測  區  名  稱',
]

CSV_COLUMNS = [
    'survey_area_code', 'survey_area_name', 'well_name', 'computer_id',
    'x_twd97', 'y_twd97', 'address', 'elev_m', 'casing_depth_m',
    'screen_raw', 'data_period', 'source_page',
]

MD_HEADERS = [
    '測區編號', '測區名稱', '井名', '電腦編號',
    'TWD97TM2 (X座標)', 'TWD97TM2 (Y座標)', '井址',
    '井頂高 (M)', '井管深度 (M)', '濾水管位置 (M)', '資料起迄',
]

# ---------------------------------------------------------------------------
# Helper: is this line a header line?
# ---------------------------------------------------------------------------
def is_header_line(line: str) -> bool:
    return any(tok in line for tok in HEADER_TOKENS)

# ---------------------------------------------------------------------------
# Helper: split Chinese area+well name prefix from computer_id position
# ---------------------------------------------------------------------------
def split_area_well(text_before_id: str):
    """
    text_before_id is the portion of the line before the 8-char computer ID.
    It may look like:
      '濁水溪沖積扇 東芳(1) '
      '濁水溪沖積扇 顏厝 '
    We heuristically split at the LAST run of Chinese characters / brackets
    that contains a non-space gap.  Area name is typically 5-6 Chinese chars;
    well name is shorter.  Strategy: the last space-delimited token is the
    well name; everything before it (stripped) is the area name.
    """
    text_before_id = text_before_id.strip()
    # Split on whitespace
    tokens = text_before_id.split()
    if not tokens:
        return '', ''
    if len(tokens) == 1:
        # Could be area name with well name glued on — try splitting at last
        # Chinese character run before a parenthesis or alphanumeric run
        # Simple fallback: whole thing is area name, well name empty
        return tokens[0], ''
    well_name = tokens[-1]
    area_name = ' '.join(tokens[:-1])
    return area_name, well_name

# ---------------------------------------------------------------------------
# Helper: parse a single well record from (primary_line, continuation_lines)
# ---------------------------------------------------------------------------
def parse_well_record(primary_line: str, continuation_lines: list, page_no: int):
    """
    Returns a dict with CSV_COLUMNS keys, or None if parsing fails.
    """
    # 1. Find the computer ID
    m_id = COMP_ID_RE.search(primary_line)
    if not m_id:
        return None
    comp_id = m_id.group(1)
    id_start = m_id.start()
    id_end   = m_id.end()

    # 2. Everything before comp_id → area + well name
    area_name, well_name = split_area_well(primary_line[:id_start])

    # 3. Everything after comp_id
    after_id = primary_line[id_end:]

    # 4. Extract the two coordinate floats
    # Also match the zero-coord case:  0.000  0.000
    COORD_ANY_RE = re.compile(r'(\d+\.\d+)\s+(\d+\.\d+)')
    m_coords = COORD_RE.search(after_id)
    if not m_coords:
        # Try to find two floats of the right magnitude separately (5+ digit easting/northing)
        floats_found = re.findall(r'\d{5,9}\.\d+', after_id)
        if len(floats_found) >= 2:
            c1, c2 = float(floats_found[0]), float(floats_found[1])
            # Build a fake match end position: find end of second float in after_id
            pos1 = after_id.find(floats_found[0])
            pos2 = after_id.find(floats_found[1], pos1 + len(floats_found[0]))
            coord_end = pos2 + len(floats_found[1])
        else:
            # Zero-coord case: look for any two floats like 0.000  0.000
            m_any = COORD_ANY_RE.search(after_id)
            if m_any:
                c1, c2 = float(m_any.group(1)), float(m_any.group(2))
                coord_end = m_any.end()
            else:
                print(f"  WARN page {page_no}: cannot parse coords in: {primary_line[:80]!r}")
                c1, c2 = 0.0, 0.0
                coord_end = 0
    else:
        c1, c2 = float(m_coords.group(1)), float(m_coords.group(2))
        coord_end = m_coords.end()

    # Determine X (easting ~150k-230k) vs Y (northing ~2.5M-2.7M)
    if c1 > 1_000_000:
        # c1 is northing, c2 is easting — swap
        x_twd97, y_twd97 = c2, c1
    else:
        x_twd97, y_twd97 = c1, c2

    # 5. Strip coord text from after_id to isolate the address+elev+casing+screen
    remainder = after_id[coord_end:]

    # 6. Extract elevation and casing depth (first two 4-decimal floats)
    floats4 = FLOAT4_RE.findall(remainder)
    if len(floats4) >= 2:
        elev_m        = float(floats4[0])
        casing_depth_m = float(floats4[1])
        # Remove them from remainder to isolate address
        r_stripped = remainder
        for f in floats4[:2]:
            r_stripped = r_stripped.replace(f, '', 1)
    elif len(floats4) == 1:
        elev_m         = float(floats4[0])
        casing_depth_m = 0.0
        r_stripped = remainder.replace(floats4[0], '', 1)
    else:
        elev_m = casing_depth_m = 0.0
        r_stripped = remainder

    # 7. Extract address: Chinese text before the elevation
    # Address ends where the first 4-decimal float begins
    m_first_float = FLOAT4_RE.search(remainder)
    if m_first_float:
        address_raw = remainder[:m_first_float.start()].strip()
    else:
        address_raw = remainder.strip()

    # Clean up address: remove stray whitespace, collapse multiple spaces
    address = re.sub(r'\s+', '', address_raw)  # Chinese addresses have no meaningful spaces

    # 8. Everything after the casing depth float → screen + date
    if len(floats4) >= 2:
        # Find position of second float in remainder
        pos1 = remainder.find(floats4[0])
        pos2 = remainder.find(floats4[1], pos1 + len(floats4[0]))
        after_casing = remainder[pos2 + len(floats4[1]):]
    else:
        after_casing = r_stripped

    after_casing = after_casing.strip()

    # 9. Extract screen code (3-digit)
    m_code = SCREEN_CODE_RE.search(after_casing)
    screen_code = m_code.group(1) if m_code else ''

    # 10. Extract date period
    m_date = DATE_RE.search(after_casing)
    data_period = m_date.group(1) if m_date else ''

    # 11. Extract depth pairs from the primary line (after the date)
    if m_date:
        after_date = after_casing[m_date.end():]
    else:
        after_date = after_casing[m_code.end():] if m_code else after_casing

    primary_depths = DEPTH_PAIR_RE.findall(after_date)

    # 12. Collect continuation depth pairs
    cont_depths = []
    for cl in continuation_lines:
        pairs = DEPTH_PAIR_RE.findall(cl)
        cont_depths.extend(pairs)

    all_depths = primary_depths + cont_depths

    # Zone code (040/050/060) → 測區編號; screen gets only depth pairs
    survey_area_code = screen_code if screen_code else '-'
    screen_raw = ' '.join(all_depths) if all_depths else '-'

    return {
        'survey_area_code': survey_area_code,
        'survey_area_name': area_name,
        'well_name':        well_name,
        'computer_id':      comp_id,
        'x_twd97':          f'{x_twd97:.3f}',
        'y_twd97':          f'{y_twd97:.3f}',
        'address':          address,
        'elev_m':           f'{elev_m:.4f}',
        'casing_depth_m':   f'{casing_depth_m:.4f}',
        'screen_raw':       screen_raw,
        'data_period':      data_period,
        'source_page':      str(page_no),
    }

# ---------------------------------------------------------------------------
# Helper: split a page's text into logical lines, strip headers, group wells
# ---------------------------------------------------------------------------
def process_page_text(raw_text: str, page_no: int):
    """
    Returns list of parsed well record dicts.
    """
    lines = raw_text.split('\n')

    # --- Step 1: skip header lines ---
    data_lines = []
    in_header = True
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if in_header:
            if is_header_line(stripped):
                continue
            else:
                in_header = False
        data_lines.append(stripped)

    if not data_lines:
        return []

    # --- Step 2: group lines into well records ---
    # A new record starts whenever an 8-char computer ID appears
    groups = []   # list of (primary_line, [continuation_lines])
    current_primary = None
    current_cont    = []

    for line in data_lines:
        if COMP_ID_RE.search(line):
            # Save previous group
            if current_primary is not None:
                groups.append((current_primary, current_cont))
            current_primary = line
            current_cont    = []
        else:
            # Is this a header line that slipped through? (e.g. partial header on page break)
            if is_header_line(line):
                continue
            # Is it a pure depth-pair continuation?
            if current_primary is not None and DEPTH_LINE_RE.match(line):
                current_cont.append(line)
            # Otherwise it might be an address fragment or something else — append to primary
            elif current_primary is not None:
                # Append to primary (handles address split across lines)
                current_primary += line

    if current_primary is not None:
        groups.append((current_primary, current_cont))

    # --- Step 3: parse each group ---
    records = []
    for primary, conts in groups:
        rec = parse_well_record(primary, conts, page_no)
        if rec is not None:
            records.append(rec)
        else:
            print(f"  WARN page {page_no}: failed to parse: {primary[:80]!r}")

    return records

# ---------------------------------------------------------------------------
# Format as markdown table
# ---------------------------------------------------------------------------
def records_to_markdown(records: list, page_no: int) -> str:
    lines = [f"# Table extracted from page {page_no} of Well_Info_2024.pdf", '']
    header_row = '| ' + ' | '.join(MD_HEADERS) + ' |'
    sep_row    = '| ' + ' | '.join(['---'] * len(MD_HEADERS)) + ' |'
    lines.append(header_row)
    lines.append(sep_row)
    for r in records:
        row_vals = [
            r['survey_area_code'],
            r['survey_area_name'],
            r['well_name'],
            r['computer_id'],
            r['x_twd97'],
            r['y_twd97'],
            r['address'],
            r['elev_m'],
            r['casing_depth_m'],
            r['screen_raw'],
            r['data_period'],
        ]
        lines.append('| ' + ' | '.join(row_vals) + ' |')
    lines.append('')
    return '\n'.join(lines)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"Opening PDF: {PDF_PATH}")
    with open(PDF_PATH, 'rb') as fh:
        reader = PyPDF2.PdfReader(fh)
        n_pages = len(reader.pages)
        print(f"Total pages: {n_pages}")

        all_records = []
        problem_pages = []

        for page_idx in range(n_pages):
            page_no = page_idx + 1
            page = reader.pages[page_idx]
            raw_text = page.extract_text() or ''

            records = process_page_text(raw_text, page_no)

            if not records:
                print(f"  INFO page {page_no}: no rows extracted")
                problem_pages.append(page_no)
            else:
                print(f"  page {page_no}: {len(records)} rows")

            # Write per-page markdown
            md_path = OUT_DIR / f"Well_Info_2024_page_{page_no:03d}_table.md"
            md_text = records_to_markdown(records, page_no)
            md_path.write_text(md_text, encoding='utf-8')

            all_records.extend(records)

        # Write combined CSV
        print(f"\nWriting combined CSV: {CSV_PATH}")
        with open(CSV_PATH, 'w', newline='', encoding='utf-8-sig') as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(all_records)

        print(f"\nTotal rows across all pages: {len(all_records)}")
        if problem_pages:
            print(f"Pages with no rows extracted: {problem_pages}")
        else:
            print("All pages yielded at least one row.")

if __name__ == '__main__':
    main()
