"""
Generate gwl_to_mlcw_layer_assignment_v4.csv

Full OODA pass over all 195 v3 rows.
Each row follows a clear decision tree with exactly one output row per input row.
"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path(r"D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2")
V3_PATH  = BASE / "data/gwl/gwl_to_mlcw_layer_assignment_v3.csv"
WELL_INFO_PATH = BASE / "data/gwl/well_info/gwl_allwells_flat.csv"
FEATHER_DIR = BASE / "data/gwl/well_timeseries"
XCORR_DIR   = BASE / "results/ring_gwl_xcorr"
OUT_PATH    = BASE / "data/gwl/gwl_to_mlcw_layer_assignment_v4.csv"

# Dead wellcodes confirmed from OBSERVE phase (0 obs in 2023-2025)
DEAD_WELLS = {'09030211', '09030221', '09160111', '09190211', '09030121'}

# ── helpers ────────────────────────────────────────────────────────────────────

def is_t_layer(layer):
    return layer.startswith('T')

def depth_tol(layer):
    return 20.0 if is_t_layer(layer) else 15.0

def depth_ok_fn(screen_mid, layer_min, layer_max, tol):
    if pd.isna(screen_mid):
        return False
    return (screen_mid >= layer_min - tol) and (screen_mid <= layer_max + tol)

# Coverage cache
_cov_cache = {}
def get_coverage(gwl_station, wellcode):
    key = (gwl_station, str(wellcode).zfill(8))
    if key not in _cov_cache:
        fp = FEATHER_DIR / f"{gwl_station}_gwl_timeseries.feather"
        if not fp.exists():
            _cov_cache[key] = (0, 0)
        else:
            df = pd.read_feather(fp)
            if 'datetime' in df.columns:
                df = df.set_index('datetime')
            df.index = pd.to_datetime(df.index)
            wc = key[1]
            if wc not in df.columns:
                _cov_cache[key] = (0, 0)
            else:
                s = df[wc]
                n15 = int(s.loc['2015-01-01':'2022-12-31'].notna().sum())
                n23 = int(s.loc['2023-01-01':'2025-12-31'].notna().sum())
                _cov_cache[key] = (n15, n23)
    return _cov_cache[key]

# Xcorr cache
_xcorr_cache = {}
def load_xcorr(station):
    if station not in _xcorr_cache:
        p = XCORR_DIR / f"{station}_ring_gwl_xcorr.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            df['gwl_wellcode'] = df['gwl_wellcode'].astype(str).str.zfill(8)
            _xcorr_cache[station] = df
        else:
            _xcorr_cache[station] = None
    return _xcorr_cache[station]

# Well info cache
_wi = None
def get_well_info():
    global _wi
    if _wi is None:
        _wi = pd.read_csv(WELL_INFO_PATH, dtype={"wellcode": str})
        _wi['wellcode'] = _wi['wellcode'].astype(str).str.zfill(8)
    return _wi

def get_xcorr_for_well(xcorr_df, wellcode, layer_min, layer_max):
    """Return (xcorr_max, lag_days) at ring closest to layer midpoint."""
    wc = str(wellcode).zfill(8)
    ring_target = (layer_min + layer_max) / 2.0
    rows = xcorr_df[xcorr_df['gwl_wellcode'] == wc].copy()
    if rows.empty:
        return np.nan, np.nan
    rows['_rd'] = (rows['ring_depth_m'] - ring_target).abs()
    br = rows.sort_values('_rd').iloc[0]
    xm = br.get('xcorr_max', np.nan)
    ld = br.get('lag_days_at_max', np.nan)
    return (float(xm) if pd.notna(xm) else np.nan,
            float(ld) if pd.notna(ld) else np.nan)

def find_best_candidate(xcorr_df, layer_min, layer_max, layer_str, exclude_wcs=None):
    """
    Search xcorr for the best replacement candidate.
    Priority order (per spec):
      1. depth_ok AND dist<=10km AND cov ok => DIRECT_MATCH
      2. depth_ok AND dist>10km AND cov ok  => NEAREST_FALLBACK
      3. best_coverage AND dist<=10km       => NEAREST_FALLBACK
      4. best_coverage anywhere             => DATA_LIMITED
    Returns dict or None.
    """
    tol = depth_tol(layer_str)
    ring_target = (layer_min + layer_max) / 2.0

    df = xcorr_df.copy()
    # Exclude dead wells and any exclusions
    excl = set(DEAD_WELLS)
    if exclude_wcs:
        excl |= {str(w).zfill(8) for w in exclude_wcs}
    df = df[~df['gwl_wellcode'].isin(excl)]

    # Flag depth ok
    df['_dok'] = df.apply(
        lambda r: depth_ok_fn(r['screen_mid_m'], layer_min, layer_max, tol), axis=1)

    # Unique candidates sorted by depth_ok desc, dist asc
    deduped = df.drop_duplicates(subset=['gwl_station', 'gwl_wellcode'])
    deduped = deduped.sort_values(['_dok', 'dist_m'], ascending=[False, True])

    def xcorr_vals(wc_str):
        rows2 = xcorr_df[xcorr_df['gwl_wellcode'] == wc_str].copy()
        if rows2.empty:
            return np.nan, np.nan
        rows2['_rd'] = (rows2['ring_depth_m'] - ring_target).abs()
        br = rows2.sort_values('_rd').iloc[0]
        xm = br.get('xcorr_max', np.nan)
        ld = br.get('lag_days_at_max', np.nan)
        return (float(xm) if pd.notna(xm) else np.nan,
                float(ld) if pd.notna(ld) else np.nan)

    def make_result(cand_row, method, note):
        wc = str(cand_row['gwl_wellcode']).zfill(8)
        gs = cand_row['gwl_station']
        n15, n23 = get_coverage(gs, wc)
        xm, ld = xcorr_vals(wc)
        wi = get_well_info()
        wi_row = wi[wi['wellcode'] == wc]
        ss = wi_row['well_screen_str'].values[0] if len(wi_row) else ''
        wd = wi_row['well_depth_m'].values[0] if len(wi_row) else np.nan
        return {
            'gwl_station': gs,
            'assigned_wellcode': wc,
            'screen_top_m': cand_row['screen_top_m'],
            'screen_bot_m': cand_row['screen_bot_m'],
            'screen_mid_m': cand_row['screen_mid_m'],
            'screen_str': ss,
            'well_depth_m': wd,
            'dist_m': cand_row['dist_m'],
            'feather_file': f"data/gwl/well_timeseries/{gs}_gwl_timeseries.feather",
            'n_2015_2022': n15,
            'n_2023_2025': n23,
            'xcorr_max': xm,
            'xcorr_lag_days': ld,
            'assignment_method': method,
            'note': note,
        }

    # Sorted dedup: depth_ok desc, then dist asc, then n23 desc (for coverage tie-break)
    # We need n23 per candidate for sorting — compute lazily
    # Actually, sort by depth_ok desc, dist asc first; check n23 inside loop

    # Pass 1: depth_ok AND dist<=10km AND cov ok => DIRECT_MATCH  (best case)
    for _, cand in deduped[deduped['_dok'] & (deduped['dist_m'] <= 10000.0)].sort_values(
            'dist_m').iterrows():
        wc = str(cand['gwl_wellcode']).zfill(8)
        gs = cand['gwl_station']
        n15, n23 = get_coverage(gs, wc)
        if n15 >= 200 and n23 >= 100:
            return make_result(cand, 'DIRECT_MATCH',
                f"Screen mid {cand['screen_mid_m']}m in layer [{layer_min:.0f}-{layer_max:.0f}m] "
                f"±{tol:.0f}m tol (v4) dist={cand['dist_m']:.0f}m")

    # Pass 2: any well within dist<=10km with cov ok (NEAREST_FALLBACK — depth violation)
    # This fires BEFORE Pass 3 (distant depth-ok) because Rule 2 hard cap is ≤10km
    for _, cand in deduped.sort_values('dist_m').iterrows():
        if cand['dist_m'] > 10000.0:
            break
        wc = str(cand['gwl_wellcode']).zfill(8)
        gs = cand['gwl_station']
        n15, n23 = get_coverage(gs, wc)
        if n15 >= 200 and n23 >= 100:
            return make_result(cand, 'NEAREST_FALLBACK',
                f"No depth match within 10km; nearest well screen_mid={cand['screen_mid_m']}m "
                f"dist={cand['dist_m']:.0f}m (v4)")

    # Pass 3: depth_ok + dist>10km + cov ok (NEAREST_FALLBACK — distance violation)
    # Only reaches here if no well within 10km has adequate coverage
    for _, cand in deduped[deduped['_dok']].sort_values('dist_m').iterrows():
        wc = str(cand['gwl_wellcode']).zfill(8)
        gs = cand['gwl_station']
        n15, n23 = get_coverage(gs, wc)
        if n15 >= 200 and n23 >= 100:
            return make_result(cand, 'NEAREST_FALLBACK',
                f"Depth ok screen_mid={cand['screen_mid_m']}m but dist={cand['dist_m']:.0f}m>10km; "
                f"no live well within 10km (v4)")

    # Pass 4: best coverage anywhere, DATA_LIMITED
    for _, cand in deduped.sort_values('dist_m').iterrows():
        wc = str(cand['gwl_wellcode']).zfill(8)
        gs = cand['gwl_station']
        n15, n23 = get_coverage(gs, wc)
        if n15 >= 200 and n23 >= 100:
            return make_result(cand, 'DATA_LIMITED',
                f"No well within 10km passes depth+coverage; using dist={cand['dist_m']:.0f}m "
                f"screen_mid={cand['screen_mid_m']}m (v4)")

    return None


# ── Main loop ─────────────────────────────────────────────────────────────────

print("Loading v3...")
v3 = pd.read_csv(V3_PATH, dtype={"assigned_wellcode": str})
v3['assigned_wellcode'] = v3['assigned_wellcode'].astype(str).str.zfill(8)
print(f"v3 rows: {len(v3)}")

output_rows = []
change_log  = []  # (station, layer, what_changed)

for idx, row in v3.iterrows():
    station   = row['station']
    layer     = row['layer']
    layer_min = float(row['layer_depth_min_m'])
    layer_max = float(row['layer_depth_max_m'])
    curr_wc   = str(row['assigned_wellcode']).zfill(8)
    ff        = row['feather_file']
    gwl_st_v3 = ff.split('/')[-1].replace('_gwl_timeseries.feather', '')
    tol       = depth_tol(layer)

    xcorr_df  = load_xcorr(station)

    # Coverage for currently assigned well
    n15_curr, n23_curr = get_coverage(gwl_st_v3, curr_wc)
    is_dead = (n23_curr < 100)

    # XCorr for current well (needed even if we replace it — we use the new well's xcorr)
    curr_sm = float(row['screen_mid_m']) if pd.notna(row['screen_mid_m']) else np.nan
    curr_depth_ok_v4 = depth_ok_fn(curr_sm, layer_min, layer_max, tol)

    if is_dead:
        # ── CASE A: current well is offline — find replacement ──
        new = find_best_candidate(xcorr_df, layer_min, layer_max, layer) if xcorr_df is not None else None
        if new is None:
            # No replacement found — keep dead well with DATA_LIMITED
            xm, ld = (np.nan, np.nan)
            if xcorr_df is not None:
                xm, ld = get_xcorr_for_well(xcorr_df, curr_wc, layer_min, layer_max)
            out = {
                'station': station, 'layer': layer,
                'layer_depth_min_m': layer_min, 'layer_depth_max_m': layer_max,
                'assigned_wellcode': curr_wc,
                'screen_top_m': row['screen_top_m'],
                'screen_bot_m': row['screen_bot_m'],
                'screen_mid_m': row['screen_mid_m'],
                'screen_str': row['screen_str'],
                'well_depth_m': row['well_depth_m'],
                'assignment_method': 'DATA_LIMITED',
                'note': f"No live replacement; orig {curr_wc} offline (n23={n23_curr})",
                'feather_file': ff,
                'dist_to_gwl_m': row['dist_to_gwl_m'],
                'xcorr_max': xm,
                'xcorr_lag_days': ld,
                'coverage_2015_2022': n15_curr,
                'coverage_2023_2025': n23_curr,
            }
            change_log.append((station, layer, f"DEAD→DATA_LIMITED (no replacement)"))
        else:
            out = {
                'station': station, 'layer': layer,
                'layer_depth_min_m': layer_min, 'layer_depth_max_m': layer_max,
                'assigned_wellcode': new['assigned_wellcode'],
                'screen_top_m': new['screen_top_m'],
                'screen_bot_m': new['screen_bot_m'],
                'screen_mid_m': new['screen_mid_m'],
                'screen_str': new['screen_str'],
                'well_depth_m': new['well_depth_m'],
                'assignment_method': new['assignment_method'],
                'note': new['note'] + f" [replaced dead {curr_wc} (n23={n23_curr})]",
                'feather_file': new['feather_file'],
                'dist_to_gwl_m': new['dist_m'],
                'xcorr_max': new['xcorr_max'],
                'xcorr_lag_days': new['xcorr_lag_days'],
                'coverage_2015_2022': new['n_2015_2022'],
                'coverage_2023_2025': new['n_2023_2025'],
            }
            change_log.append((station, layer,
                f"DEAD→{new['assignment_method']} wc={new['assigned_wellcode']}"))

    else:
        # ── CASE B: current well is alive — recompute method and optionally upgrade ──

        xm_curr, ld_curr = (np.nan, np.nan)
        if xcorr_df is not None:
            xm_curr, ld_curr = get_xcorr_for_well(xcorr_df, curr_wc, layer_min, layer_max)

        v3_method = row['assignment_method']

        if curr_depth_ok_v4:
            # Current well passes v4 depth tolerance → DIRECT_MATCH (may upgrade from v3 NEAREST_FALLBACK)
            new_method = 'DIRECT_MATCH'
            new_note   = (f"Screen mid {curr_sm}m in layer [{layer_min:.0f}-{layer_max:.0f}m] "
                          f"±{tol:.0f}m tol (v4)")
            if v3_method == 'NEAREST_FALLBACK':
                change_log.append((station, layer, f"NEAREST_FALLBACK→DIRECT_MATCH (v4 tol)"))
        else:
            # Current well does NOT pass v4 depth tolerance.
            # Check if a DIRECT_MATCH now exists in xcorr within 10km that we missed.
            upgraded = None
            if xcorr_df is not None:
                df_c = xcorr_df.copy()
                df_c = df_c[~df_c['gwl_wellcode'].isin(DEAD_WELLS)]
                df_c['_dok'] = df_c.apply(
                    lambda r: depth_ok_fn(r['screen_mid_m'], layer_min, layer_max, tol), axis=1)
                depth_within = df_c[
                    df_c['_dok'] & (df_c['dist_m'] <= 10000.0)
                ].drop_duplicates(subset=['gwl_station','gwl_wellcode']).sort_values('dist_m')
                for _, dc in depth_within.iterrows():
                    dwc = str(dc['gwl_wellcode']).zfill(8)
                    dgs = dc['gwl_station']
                    dn15, dn23 = get_coverage(dgs, dwc)
                    if dn15 >= 200 and dn23 >= 100:
                        wi = get_well_info()
                        wi_r = wi[wi['wellcode'] == dwc]
                        ss2 = wi_r['well_screen_str'].values[0] if len(wi_r) else ''
                        wd2 = wi_r['well_depth_m'].values[0] if len(wi_r) else np.nan
                        ring_target2 = (layer_min + layer_max) / 2.0
                        xm2, ld2 = get_xcorr_for_well(xcorr_df, dwc, layer_min, layer_max)
                        upgraded = {
                            'assigned_wellcode': dwc,
                            'screen_top_m': dc['screen_top_m'],
                            'screen_bot_m': dc['screen_bot_m'],
                            'screen_mid_m': dc['screen_mid_m'],
                            'screen_str': ss2,
                            'well_depth_m': wd2,
                            'feather_file': f"data/gwl/well_timeseries/{dgs}_gwl_timeseries.feather",
                            'dist_to_gwl_m': dc['dist_m'],
                            'xcorr_max': xm2, 'xcorr_lag_days': ld2,
                            'coverage_2015_2022': dn15, 'coverage_2023_2025': dn23,
                            'note': (f"Upgraded {curr_wc}→{dwc}: screen_mid={dc['screen_mid_m']}m "
                                     f"in layer ±{tol:.0f}m tol (v4) dist={dc['dist_m']:.0f}m"),
                        }
                        change_log.append((station, layer,
                            f"UPGRADE {curr_wc}→{dwc} (NEAREST_FALLBACK→DIRECT_MATCH)"))
                        break

            if upgraded:
                out = {
                    'station': station, 'layer': layer,
                    'layer_depth_min_m': layer_min, 'layer_depth_max_m': layer_max,
                    'assignment_method': 'DIRECT_MATCH',
                    **upgraded,
                }
            else:
                # Keep current well as NEAREST_FALLBACK
                new_method = 'NEAREST_FALLBACK'
                new_note   = row['note']
                out = {
                    'station': station, 'layer': layer,
                    'layer_depth_min_m': layer_min, 'layer_depth_max_m': layer_max,
                    'assigned_wellcode': curr_wc,
                    'screen_top_m': row['screen_top_m'],
                    'screen_bot_m': row['screen_bot_m'],
                    'screen_mid_m': row['screen_mid_m'],
                    'screen_str': row['screen_str'],
                    'well_depth_m': row['well_depth_m'],
                    'assignment_method': new_method,
                    'note': new_note,
                    'feather_file': ff,
                    'dist_to_gwl_m': row['dist_to_gwl_m'],
                    'xcorr_max': xm_curr,
                    'xcorr_lag_days': ld_curr,
                    'coverage_2015_2022': n15_curr,
                    'coverage_2023_2025': n23_curr,
                }

        if not is_dead:
            if curr_depth_ok_v4:
                out = {
                    'station': station, 'layer': layer,
                    'layer_depth_min_m': layer_min, 'layer_depth_max_m': layer_max,
                    'assigned_wellcode': curr_wc,
                    'screen_top_m': row['screen_top_m'],
                    'screen_bot_m': row['screen_bot_m'],
                    'screen_mid_m': row['screen_mid_m'],
                    'screen_str': row['screen_str'],
                    'well_depth_m': row['well_depth_m'],
                    'assignment_method': new_method,
                    'note': new_note,
                    'feather_file': ff,
                    'dist_to_gwl_m': row['dist_to_gwl_m'],
                    'xcorr_max': xm_curr,
                    'xcorr_lag_days': ld_curr,
                    'coverage_2015_2022': n15_curr,
                    'coverage_2023_2025': n23_curr,
                }

    output_rows.append(out)

# ── Write output ──────────────────────────────────────────────────────────────

v4 = pd.DataFrame(output_rows)
COLS = [
    'station', 'layer', 'layer_depth_min_m', 'layer_depth_max_m',
    'assigned_wellcode', 'screen_top_m', 'screen_bot_m', 'screen_mid_m',
    'screen_str', 'well_depth_m', 'assignment_method', 'note',
    'feather_file', 'dist_to_gwl_m',
    'xcorr_max', 'xcorr_lag_days',
    'coverage_2015_2022', 'coverage_2023_2025',
]
v4 = v4[COLS]
print(f"\nv4 rows: {len(v4)}  (expected: {len(v3)})")

v4.to_csv(OUT_PATH, index=False)
print(f"Wrote: {OUT_PATH}")

# ── Change log ────────────────────────────────────────────────────────────────

print(f"\n=== CHANGES from v3 ===")
for s, l, what in change_log:
    print(f"  {s:15s} {l:3s} {what}")
print(f"\nTotal changes: {len(change_log)}")

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n=== METHOD COUNTS ===")
print(v4['assignment_method'].value_counts())

n_dead_replaced = sum(1 for _, _, w in change_log if 'DEAD' in w and 'DATA_LIMITED' not in w)
n_dead_datalim  = sum(1 for _, _, w in change_log if 'DEAD' in w and 'DATA_LIMITED' in w)
n_upgraded      = sum(1 for _, _, w in change_log if 'NEAREST_FALLBACK→DIRECT_MATCH' in w)
print(f"\n  Dead wells replaced (live assignment): {n_dead_replaced}")
print(f"  Dead wells → DATA_LIMITED:             {n_dead_datalim}")
print(f"  NEAREST_FALLBACK→DIRECT_MATCH (v4 tol): {n_upgraded}")

# ── Post-write assertions ─────────────────────────────────────────────────────

print("\n=== POST-WRITE ASSERTIONS ===")

bad_rowcount = len(v4) != len(v3)
print(f"{'FAIL' if bad_rowcount else 'PASS'}: Row count is {len(v4)} (expected {len(v3)})")

bad_dist = v4[(v4['dist_to_gwl_m'] > 10000.0) & (v4['assignment_method'] == 'DIRECT_MATCH')]
print(f"{'FAIL' if len(bad_dist) else 'PASS'}: "
      f"DIRECT_MATCH rows with dist>10km: {len(bad_dist)}")
if len(bad_dist):
    print(bad_dist[['station','layer','dist_to_gwl_m','assignment_method']].to_string())

bad_cov = v4[(v4['coverage_2023_2025'] < 100) & (v4['assignment_method'] != 'DATA_LIMITED')]
print(f"{'FAIL' if len(bad_cov) else 'PASS'}: "
      f"Non-DATA_LIMITED rows with n23<100: {len(bad_cov)}")
if len(bad_cov):
    print(bad_cov[['station','layer','assigned_wellcode','coverage_2023_2025','assignment_method']].to_string())

bad_wc = v4[v4['assigned_wellcode'].astype(str).str.len() != 8]
print(f"{'FAIL' if len(bad_wc) else 'PASS'}: Wellcodes not 8 digits: {len(bad_wc)}")

fangcao_remain = v4[v4['feather_file'].str.contains('FANGCAO', na=False)]
print(f"{'FAIL' if len(fangcao_remain) else 'PASS'}: FANGCAO feather references: {len(fangcao_remain)}")

dead_remain = v4[v4['assigned_wellcode'].isin(DEAD_WELLS) & (v4['assignment_method'] != 'DATA_LIMITED')]
print(f"{'FAIL' if len(dead_remain) else 'PASS'}: Dead wells without DATA_LIMITED: {len(dead_remain)}")
if len(dead_remain):
    print(dead_remain[['station','layer','assigned_wellcode','assignment_method']].to_string())

# Rule-1 compliance check: DIRECT_MATCH rows must have screen_mid within ±tol of layer range
print("\n=== Rule-1 compliance check ===")
rule1_fails = []
for _, r in v4[v4['assignment_method'] == 'DIRECT_MATCH'].iterrows():
    if pd.isna(r['screen_mid_m']):
        continue
    tol_r = 20.0 if r['layer'].startswith('T') else 15.0
    lmin_r = r['layer_depth_min_m']
    lmax_r = r['layer_depth_max_m']
    sm = float(r['screen_mid_m'])
    if not (sm >= lmin_r - tol_r and sm <= lmax_r + tol_r):
        rule1_fails.append(r)
        print(f"  FAIL Rule-1: {r['station']} {r['layer']} wc={r['assigned_wellcode']} "
              f"screen_mid={sm}m layer=[{lmin_r:.0f}-{lmax_r:.0f}]m tol={tol_r}m")
if not rule1_fails:
    print("PASS: All DIRECT_MATCH rows satisfy Rule-1 (screen_mid within ±tol of layer)")

# NEAREST_FALLBACK rows should be either >10km OR depth-out-of-tol (or both)
nf_check_fails = []
for _, r in v4[v4['assignment_method'] == 'NEAREST_FALLBACK'].iterrows():
    if pd.isna(r['screen_mid_m']):
        continue
    tol_r = 20.0 if r['layer'].startswith('T') else 15.0
    lmin_r = r['layer_depth_min_m']
    lmax_r = r['layer_depth_max_m']
    sm = float(r['screen_mid_m'])
    dist_r = float(r['dist_to_gwl_m'])
    depth_ok_r = (sm >= lmin_r - tol_r and sm <= lmax_r + tol_r)
    dist_ok_r  = (dist_r <= 10000.0)
    if depth_ok_r and dist_ok_r:
        # Would be a DIRECT_MATCH if Rule 3 passed — check coverage
        nf_check_fails.append(r)
        print(f"  SUSPECT NEAREST_FALLBACK: {r['station']} {r['layer']} wc={r['assigned_wellcode']} "
              f"screen_mid={sm}m depth_ok=True dist={dist_r:.0f}m <=10km "
              f"n23={r['coverage_2023_2025']} (should be DIRECT_MATCH or DATA_LIMITED)")
if not nf_check_fails:
    print("PASS: All NEAREST_FALLBACK rows have depth violation or dist>10km")

print("\nDone.")
