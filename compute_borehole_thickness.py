"""
Compute borehole-based aquifer/aquitard material thicknesses for TUKU MLCW layers.

Material classification (from material_notes.txt):
  Category 1: G          -> Aquifer (gravel)
  Category 2: cS         -> Aquifer (coarse sand)
  Category 3: cSmS       -> Aquifer (coarse-medium sand)
  Category 4: fS, fSvfS  -> Transitional (fine sand) -- treated as Aquitard here per convention
  Category 5: M, Z       -> Aquitard (mud, silt)
  Category 6: ZC, C      -> Aquitard (clay)

Layer depth bounds from TUKU_classify_table.csv (ring depths define layer assignment):
  F1: 0 m (surface) to first T1 ring = 41.577 m  → use 0–41.577 m
  T1: 41.577 m to first F2 ring = 50.306 m        → use 41.577–50.306 m
  F2: 50.306 m to first T2 ring = 156.59 m        → use 50.306–156.59 m
  T2: 156.59 m to first F3 ring = 172.889 m       → use 156.59–172.889 m
  F3: 172.889 m to first F4 ring = 283.383 m      → use 172.889–283.383 m
  F4: 283.383 m to bottom = 300 m                  → use 283.383–300 m

For each layer, compute:
  - total_m: total depth span
  - aquifer_m: sum of Category 1+2+3 strata within that span
  - aquitard_m: sum of Category 4+5+6 strata within that span
"""

import pandas as pd
import numpy as np

# ── Borehole log (from Excel) ─────────────────────────────────────────────────
strata = [
    (0,     4.5,   3, 'cSmS'),
    (4.5,   5.5,   5, 'Z'),
    (5.5,   6.5,   3, 'cSmS'),
    (6.5,   10,    5, 'M'),
    (10,    23,    3, 'cSmS'),
    (23,    24.5,  5, 'M'),
    (24.5,  26,    3, 'cSmS'),
    (26,    30,    5, 'M'),
    (30,    35,    3, 'cSmS'),
    (35,    39,    5, 'M'),
    (39,    47,    5, 'Z'),
    (47,    49,    5, 'M'),
    (49,    65,    3, 'cSmS'),
    (65,    72,    1, 'G'),
    (72,    79,    3, 'cSmS'),
    (79,    82,    1, 'G'),
    (82,    83.5,  3, 'cSmS'),
    (83.5,  85,    5, 'Z'),
    (85,    86,    5, 'M'),
    (86,    90.5,  3, 'cSmS'),
    (90.5,  91.5,  5, 'M'),
    (91.5,  94,    1, 'G'),
    (94,    105,   3, 'cSmS'),
    (105,   106,   5, 'M'),
    (106,   115,   3, 'cSmS'),
    (115,   120.5, 5, 'M'),
    (120.5, 154.5, 3, 'cSmS'),
    (154.5, 160,   5, 'M'),
    (160,   162.5, 5, 'Z'),
    (162.5, 163.5, 3, 'cSmS'),
    (163.5, 166,   5, 'M'),
    (166,   171,   3, 'cSmS'),
    (171,   176,   5, 'M'),
    (176,   180,   5, 'Z'),
    (180,   184,   5, 'M'),
    (184,   188,   5, 'Z'),
    (188,   190,   5, 'M'),
    (190,   196,   5, 'Z'),
    (196,   218,   5, 'M'),
    (218,   226,   3, 'cSmS'),
    (226,   230.5, 5, 'M'),
    (230.5, 240,   3, 'cSmS'),
    (240,   243,   5, 'M'),
    (243,   245.5, 5, 'Z'),
    (245.5, 250,   5, 'M'),
    (250,   255,   3, 'cSmS'),
    (255,   260,   5, 'Z'),
    (260,   265,   3, 'cSmS'),
    (265,   266,   5, 'M'),
    (266,   270,   3, 'cSmS'),
    (270,   275,   5, 'M'),
    (275,   277,   3, 'cSmS'),
    (277,   281,   5, 'M'),
    (281,   286.5, 5, 'Z'),
    (286.5, 292.5, 5, 'M'),
    (292.5, 300,   5, 'Z'),
]

AQUIFER_CATS  = {1, 2, 3}   # G, cS, cSmS
AQUITARD_CATS = {4, 5, 6}   # fS, M/Z, C

# ── Layer depth bounds (from classify table) ──────────────────────────────────
LAYER_BOUNDS = {
    'F1': (0,       41.577),
    'T1': (41.577,  50.306),
    'F2': (50.306,  156.59),
    'T2': (156.59,  172.889),
    'F3': (172.889, 283.383),
    'F4': (283.383, 300.0),
}


def overlap(s_top, s_bot, l_top, l_bot):
    """Return the overlap length between stratum [s_top, s_bot] and layer [l_top, l_bot]."""
    return max(0.0, min(s_bot, l_bot) - max(s_top, l_top))


print(f"\n{'Layer':<6} {'Span_top':>10} {'Span_bot':>10} {'Total_m':>8} {'Aquifer_m':>10} {'Aquitard_m':>11}")
print("-" * 60)

results = {}
for layer, (l_top, l_bot) in LAYER_BOUNDS.items():
    total = l_bot - l_top
    aq_m  = 0.0
    at_m  = 0.0
    for s_top, s_bot, cat, soil in strata:
        ol = overlap(s_top, s_bot, l_top, l_bot)
        if ol <= 0:
            continue
        if cat in AQUIFER_CATS:
            aq_m += ol
        else:
            at_m += ol
    results[layer] = {'total_m': total, 'aquifer_m': aq_m, 'aquitard_m': at_m}
    print(f"{layer:<6} {l_top:>10.3f} {l_bot:>10.3f} {total:>8.3f} {aq_m:>10.3f} {at_m:>11.3f}")

print()
print("Detail per layer (strata contributing):")
for layer, (l_top, l_bot) in LAYER_BOUNDS.items():
    print(f"\n  {layer} ({l_top}–{l_bot} m):")
    for s_top, s_bot, cat, soil in strata:
        ol = overlap(s_top, s_bot, l_top, l_bot)
        if ol > 0:
            kind = 'AQ' if cat in AQUIFER_CATS else 'AT'
            print(f"    {kind}  {max(s_top,l_top):.1f}–{min(s_bot,l_bot):.1f} m  ({ol:.2f} m)  cat={cat} soil={soil}")
