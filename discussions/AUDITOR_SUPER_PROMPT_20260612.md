# ZERO-TRUST AUDIT SUPER PROMPT — TUKU Pilot Results

**Date:** 2026-06-12
**Station:** TUKU (土庫)
**Repo root:** `/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2`
**Reference manual:** `discussions/AUDITOR_INVITATION_20260612.md` — consult only when a step references it explicitly. Contains sign conventions, column schemas, JSON structures, and file inventories. Do NOT read it as narrative; use it as a lookup table.

---

## ═══════════ PRECONDITIONS — Read Once ═══════════

```
$REPO = /mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2
$LAYERS = F1 T1 F2 T2 F3 F4
$CADENCES = none annual semiannual quarterly monthly actual
$SIGN_ERROR_THRESHOLD = 0.1  # mm — only flag |obs_inc| > 0.1
```

**Sign conventions (verify first — wrong sign invalidates everything):**
- MLCW compaction: negative = compaction. Check: `b_observed_mm` in reconstruction CSVs must be ≤ 0.
- GWL head: `dh_raw = H(t) − H(t_ref)`, negative = head fell. Never negate.
- InSAR/GPS displacement: negative = subsidence.
- Residual = pred − obs: positive = model underpredicts compaction (less negative than observation).
- V(t): ≤ 0 always, monotonically non-increasing.

**Execution rules (binding):**
1. Execute steps in order. Do not skip.
2. If a step fails, record the failure with exact output and continue to the next step.
3. If a required file is missing, record `FILE_NOT_FOUND: <path>` and skip the step.
4. Do not improvise. Do not add steps. Do not expand scope.
5. Do not trust any numeric claim in discussion documents. Verify against data files.
6. All Python commands use `python3 -c "..."` with inline code. No script files created.
7. Report format: `STEP X.Y: PASS | FAIL | SKIP — <evidence>`

**Reference document lookup syntax:** When a step says `REF§X.Y`, open `discussions/AUDITOR_INVITATION_20260612.md` and read only the referenced section.

---

## ═══════════ PHASE 0: Depth Verification ═══════════

### Step 0.1: Read the well manager's ring-to-layer classification
```bash
cat $REPO/data/mlcw/group_byLayer_orig/TUKU_classify_table.csv
```
**Expected:** 25 rows. Columns: `depth,layer`. F3 entries span 172.889 to 272.728 m.
**Assert:** F3 spans 172.9–272.7 m (NOT "238–275 m" as claimed in discussion documents).

### Step 0.2: Read the borehole material log
```bash
python3 -c "
import pandas as pd
df = pd.read_excel('$REPO/data/mlcw/borehole_materials/YL_WSYL23G1_TUKU_土庫.xlsx')
# Material at 176-179 m (well 09050331 screen zone)
screen = df[(df['TOP'] <= 179) & (df['BOTTOM'] >= 176)]
print(screen[['TOP','BOTTOM','SOIL_TYPE','SOIL_CATEGORY']].to_string())
# F3 zone materials (170-280 m)
f3 = df[(df['TOP'] >= 170) & (df['TOP'] <= 280)]
print('\nF3 zone category counts:')
print(f3['SOIL_CATEGORY'].value_counts().to_string())
"
```
**Expected:** Well screen at 176–179 m is in SOIL_CATEGORY 5 (Z=clay, M=mud). F3 zone is 71% category 5.

### Step 0.3: Read GWL well 09050331 metadata
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('$REPO/data/gwl/well_info/gwl_allwells_flat.csv')
well = df[df['wellcode'].astype(str) == '09050331']
print(f\"well_depth_m: {well['well_depth_m'].values[0]}\")
print(f\"screen: {well['screen_top_m'].values[0]} – {well['screen_bot_m'].values[0]} m\")
print(f\"elevation: {well['elev_leveling_m'].values[0]} m MSL\")
"
```
**Expected:** well_depth=185.0 m, screen=176.0–179.0 m.

### Step 0.4: Reconcile F3 depth vs well position
**Operation:** Well screen at 176–179 m. F3 spans 172.9–272.7 m per Step 0.1. Well total depth = 185 m.
**Assert:** Well IS within F3 (172.9–272.7 m), overlapping upper 3–6 m of layer. Well bottom at 185 m leaves lower F3 (185–272.7 m, ~88 m) unmonitored.
**Contradiction found:** Previous claim "79 m gap, 0 m overlap" in `discussions/F3_FORENSIC_VERDICT_20260612.md` is FALSE. Report this.

### Step 0.5: Check CLAUDE.md depth claims against classify_table
```bash
grep -n "238.*275\|240.*275\|79.*gap\|F3.*depth\|F3.*clay" $REPO/CLAUDE.md
```
**Operation:** For each match, cross-reference against Step 0.1–0.4 findings.
**Expected:** At least one depth claim in CLAUDE.md will not match the classify_table.

### Step 0.6: Check F3 forensic document depth claims
```bash
grep -n "238.*275\|240.*275\|79.*m gap\|0 m overlap\|no piezometer.*F3" $REPO/discussions/F3_FORENSIC_VERDICT_20260612.md
```
**Operation:** For each match, report whether the claim is TRUE, FALSE, or MISLEADING given Steps 0.1–0.4.

---

## ═══════════ PHASE 1: Sign Convention & Provenance Audit ═══════════

### Step 1.1: Verify MLCW sign convention (negative = compaction)
```bash
python3 -c "
import pandas as pd
for layer in ['F1','T1','F2','T2','F3','F4']:
    df = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_'+layer+'_reconstruction.csv')
    obs = df['b_observed_mm'].dropna()
    n_pos = (obs > 0).sum()
    print(f'{layer}: {len(obs)} observed epochs, {n_pos} positive values (should be 0)')
    if n_pos > 0:
        print(f'  VIOLATION examples: {obs[obs > 0].head(5).tolist()}')
"
```
**Expected:** All layers: n_pos = 0. Any positive value is a sign convention violation.

### Step 1.2: Verify GPS surface sign convention (negative = subsidence)
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_F1_reconstruction.csv')
gps = df['d_surface_mm'].dropna()
n_pos = (gps > 0).sum()
print(f'GPS surface: {len(gps)} epochs, min={gps.min():.2f}, max={gps.max():.2f}, {n_pos} positive')
print(f'Expected: overwhelmingly negative (subsidence), occasional positive (uplift) is acceptable')
"
```
**Expected:** GPS values predominantly negative. Occasional positive values are physically acceptable (seasonal uplift).

### Step 1.3: Verify GWL head is NOT negated
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('$REPO/tau_demo_TUKU/results/timeseries/TUKU_F1_cumulative_timeseries.csv')
head = df['H_zero_ref_m'].dropna()
print(f'Head range: [{head.min():.2f}, {head.max():.2f}] m')
print(f'Expected: within [-50, +50] m for CRAF. Values < -100 suggest negation error.')
if head.min() < -100:
    print('VIOLATION: head values < -100 m — possible negation error')
"
```
**Expected:** Head range within [−50, +50] m for CRAF context.

### Step 1.4: Cross-check provenance mask against original field data
```bash
python3 -c "
import pandas as pd
mask = pd.read_csv('$REPO/tau_demo_TUKU/results/mlcw_observed_epoch_mask.csv', parse_dates=['date'])
orig = pd.read_csv('$REPO/data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv', parse_dates=['datetime'])
orig_dates = set(orig['datetime'].dropna())
# For each layer column in mask, check: when mask=True, is the date in orig_dates?
for col in ['F1_observed','T1_observed','F2_observed','T2_observed','F3_observed','F4_observed']:
    true_dates = set(mask[mask[col] == True]['date'])
    false_positives = true_dates - orig_dates
    false_negatives = orig_dates - true_dates
    print(f'{col}: {len(true_dates)} marked observed, {len(false_positives)} false positives, {len(false_negatives)} false negatives')
"
```
**Expected:** false_positives ≤ 0 for all layers. false_negatives may be > 0 (some original dates not in mask due to date alignment).

### Step 1.5: Detect non-integer MLCW values in 2024+ data
```bash
python3 -c "
import pandas as pd
orig = pd.read_csv('$REPO/data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv', parse_dates=['datetime'])
post2024 = orig[orig['datetime'] >= '2024-01-01']
for col in ['F1','T1','F2','T2','F3','F4']:
    vals = post2024[col].dropna()
    if len(vals) == 0:
        print(f'{col}: no post-2024 data')
        continue
    n_int = (vals == vals.round()).sum()
    n_nonint = len(vals) - n_int
    print(f'{col}: {len(vals)} values, {n_int} integer, {n_nonint} non-integer ({n_nonint/max(len(vals),1):.0%})')
print('Genuine magnetic-ring readings are integer mm. 100% non-integer = computer-smoothed, not field-verifiable.')
"
```
**Expected:** Post-2024 data is predominantly non-integer — confirming the provenance warning.

---

## ═══════════ PHASE 2: Core Metric Verification ═══════════

### Step 2.1: Verify Σ a_k constraint
```bash
python3 -c "
import json
with open('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json') as f:
    d = json.load(f)
sum_a = sum(d['per_layer'][l]['a_k'] for l in ['F1','T1','F2','T2','F3','F4'])
print(f'Σ a_k = {sum_a:.4f}')
print(f'Claimed in file: {d.get(\"sum_a_k\", \"NOT FOUND\")}')
print(f'≤ 1.0: {sum_a <= 1.0}')
"
```
**Expected:** Σ a_k = 0.637, ≤ 1.0. If the file's `sum_a_k` field disagrees with computed sum, report discrepancy.

### Step 2.2: Verify reconstruction identity for F3 (d_k = 0, GWL term absent)
```bash
python3 -c "
import pandas as pd, numpy as np, json
with open('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json') as f:
    d = json.load(f)
for layer in ['F3','F4']:
    ld = d['per_layer'][layer]
    a_k, c_k = ld['a_k'], ld['c_k']
    df = pd.read_csv(f'$REPO/tau_demo_TUKU/results/reconstruction/TUKU_{layer}_reconstruction.csv')
    valid = df['d_surface_mm'].notna() & df['b_model_mm'].notna()
    predicted = a_k * df.loc[valid, 'd_surface_mm'] + c_k
    actual = df.loc[valid, 'b_model_mm']
    dev = (predicted - actual).abs()
    print(f'{layer}: max |a_k·d_GPS + c_k − b_model| = {dev.max():.6f} mm (should be ~0)')
"
```
**Expected:** Max deviation < 1e-6 mm for F3/F4 (pure carrier, no GWL term).

### Step 2.3: Verify reconstruction identity for F1/T1/F2/T2 (GWL term present)
```bash
python3 -c "
import pandas as pd, numpy as np, json
with open('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json') as f:
    d = json.load(f)
for layer in ['F1','T1','F2','T2']:
    ld = d['per_layer'][layer]
    a_k, c_k = ld['a_k'], ld['c_k']
    df = pd.read_csv(f'$REPO/tau_demo_TUKU/results/reconstruction/TUKU_{layer}_reconstruction.csv')
    valid = df['d_surface_mm'].notna() & df['b_model_mm'].notna()
    carrier_only = a_k * df.loc[valid, 'd_surface_mm'] + c_k
    actual = df.loc[valid, 'b_model_mm']
    gwl_component = actual - carrier_only
    print(f'{layer}: GWL component range = [{gwl_component.min():.2f}, {gwl_component.max():.2f}] mm')
    print(f'  GWL component std = {gwl_component.std():.2f} mm')
"
```
**Expected:** Non-zero GWL component for all four layers. F2 GWL component should be the largest (a_k=0.23, d_k=0.55).

### Step 2.4: Verify carrier tail evaluation skill claims
```bash
python3 -c "
import json
with open('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json') as f:
    d = json.load(f)
for layer in ['F1','T1','F2','T2','F3','F4']:
    tail = d['per_layer'][layer].get('tail_evaluation', {})
    skill = tail.get('skill', None)
    rmse = tail.get('rmse_mm', None)
    print(f'{layer}: tail_skill={skill}, tail_rmse={rmse} mm')
print()
print('DP2 claims skill > 0 for T1 (+0.41), F2 (+0.43), T2 (+0.30). F3/F4 skill < 0 expected.')
"
```
**Expected:** T1, F2, T2 tail_skill > 0; F3, F4 tail_skill < 0.

### Step 2.5: Verify F3 sign-error rate (our claim: 39.3%)
```bash
python3 -c "
import pandas as pd, numpy as np
df = pd.read_csv('$REPO/tau_demo_TUKU/results/auditor_diagnostics/sign_error_log.csv')
f3 = df[df['layer'] == 'F3']
n_sign = (f3['error_type'] == 'sign_reversal').sum()
n_total = len(f3)
print(f'F3 sign-reversal rate: {n_sign}/{n_total} = {n_sign/max(n_total,1):.1%}')
print(f'Our claim: 39.3%')
print(f'Match: {abs(n_sign/max(n_total,1) - 0.393) < 0.02}')
# Show worst 5 F3 sign reversals
f3_sr = f3[f3['error_type'] == 'sign_reversal'].nlargest(5, f3['residual_mm'].abs())
print('\nWorst 5 F3 sign reversals:')
for _, r in f3_sr.iterrows():
    print(f\"  {r['date']} | obs={r['obs_inc_mm']:+.3f} pred={r['pred_inc_mm']:+.3f} | res={r['residual_mm']:+.3f}\")
"
```
**Expected:** F3 sign-reversal rate ≈ 39.3% ± 2pp. Worst epochs cluster in June 2023.

### Step 2.6: Verify F2/F3 anti-phase rate (our claim: 23.5%)
```bash
python3 -c "
import pandas as pd, numpy as np
df = pd.read_csv('$REPO/tau_demo_TUKU/results/auditor_diagnostics/cross_layer_consistency.csv')
anti_rate = df['f2_f3_anti_phase'].mean()
print(f'F2/F3 anti-phase rate: {anti_rate:.1%}')
print(f'Our claim: 23.5%')
# Independent recomputation from reconstruction CSVs
f2 = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_F2_reconstruction.csv')
f3 = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_F3_reconstruction.csv')
f2_inc = f2['b_observed_mm'].diff()
f3_inc = f3['b_observed_mm'].diff()
valid = (f2_inc.abs() > 0.1) & (f3_inc.abs() > 0.1)
anti = (np.sign(f2_inc[valid]) != np.sign(f3_inc[valid])).mean()
print(f'Independent recomputation: {anti:.1%}')
"
```
**Expected:** Anti-phase rate ≈ 23.5% by both methods.

### Step 2.7: Verify storage parameter F2 S_skv claim (matches Hung et al. 2021)
```bash
python3 -c "
import json
with open('$REPO/tau_demo_TUKU/results/characterization/TUKU_storage_params.json') as f:
    d = json.load(f)
f2 = d['per_layer']['F2']
print(f'F2 S_skv: {f2[\"S_skv_m1\"]:.2e} m⁻¹')
print(f'Hung et al. (2021) middle fan S_skv: 1.33e-3 m⁻¹')
print(f'Ratio: {f2[\"S_skv_m1\"]/1.33e-3:.2f}')
print(f'Within 10%: {abs(f2[\"S_skv_m1\"]/1.33e-3 - 1.0) < 0.10}')
print()
for layer in ['F1','T1','F2','T2','F3','F4']:
    ld = d['per_layer'][layer]
    print(f'{layer}: S_ke={ld[\"S_ke_mm_per_m\"]:.3f}, S_kv={ld[\"S_kv_mm_per_m\"]:.3f}, r2={ld[\"r2_cum\"]:.3f}, tau={ld[\"tau_opt\"]}')
"
```
**Expected:** F2 S_skv = 1.34e-3 m⁻¹, within 10% of Hung et al. (2021). F3 and F4: S_ke = 0.0 (inelastic-only).

---

## ═══════════ PHASE 3: Guardrails Code Audit ═══════════

### Step 3.1: Find all callers of validate_layer_params — check if material is passed
```bash
grep -rn "validate_layer_params" $REPO/ --include="*.py" | grep -v "__pycache__" | grep -v ".pyc"
```
**Operation:** For each caller, check the function call for `material=` keyword argument.
**Expected:** At least one caller (likely `tau_demo_TUKU/15_storage_characterization.py`) calls without `material=`.

### Step 3.2: Verify what happens when material=None (checks skipped)
```bash
python3 -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from guardrails import validate_layer_params, TUKU_MATERIALS
# With material
r_with = validate_layer_params(S_ke=2.626, S_kv=4.315, layer='F1', station='TUKU', fan_zone='middle', material=TUKU_MATERIALS.get('F1'), n_total=100, n_inelastic=50, r2=0.691, tau=6)
print(f'With material: {len(r_with.errors)} errors, {len(r_with.warnings)} warnings')
for w in r_with.warnings[:3]:
    print(f'  WARN: {w[:100]}...')
# Without material
r_without = validate_layer_params(S_ke=2.626, S_kv=4.315, layer='F1', station='TUKU', fan_zone='middle', material=None, n_total=100, n_inelastic=50, r2=0.691, tau=6)
print(f'Without material: {len(r_without.errors)} errors, {len(r_without.warnings)} warnings')
for w in r_without.warnings[:3]:
    print(f'  WARN: {w[:100]}...')
print(f'Warnings lost: {len(r_with.warnings) - len(r_without.warnings)}')
"
```
**Expected:** r_with has more warnings than r_without (literature bounds, ratio gate warnings lost when material=None).

### Step 3.3: Reproduce ratio explosion for tiny S_ke
```bash
python3 -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from guardrails import validate_ratio_gate
# S_ke = 1e-10 mm/m, total_m = 100 m → S_ske_m1 = 1e-15
# S_kv = 1e-3 mm/m, aquitard_m = 50 m → S_skv_m1 = 2e-8
warnings = validate_ratio_gate(S_ske_m1=1e-15, S_skv_m1=2e-8, layer='TEST', station='TEST')
print(f'Warnings: {warnings}')
print(f'Expected: should say S_ske ≈ 0 or ratio undefined, NOT implausibly large inelastic')
# Check: does it say 'implausibly large'?
has_false_warning = any('implausibly large' in w for w in warnings)
print(f'Has false implausibly large warning: {has_false_warning}')
"
```
**Expected:** Should NOT warn about "implausibly large" inelastic storage. If it does, G3 is confirmed.

### Step 3.4: Test F4 clay-check bypass when S_ke = 0
```bash
python3 -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from guardrails import validate_clay_layer_behavior
warnings = validate_clay_layer_behavior(
    S_ke=0.0, S_kv=8.695, n_inelastic=224, n_total=772,
    layer='F4', is_clay_dominated=True, station='TUKU'
)
print(f'Warnings for F4 (S_ke=0, clay): {warnings}')
print(f'Expected: at minimum a note that 100% clay layer has zero elastic storage')
print(f'Warning emitted: {len(warnings) > 0}')
"
```
**Expected:** If warnings list is empty, G4 is confirmed (F4 clay check silently bypassed).

### Step 3.5: Verify proximal fan S_skv silently accepted
```bash
python3 -c "
import sys; sys.path.insert(0, '$REPO/scripts')
from guardrails import validate_literature_bounds
# Proximal fan has S_skv_m1=None — inelastic not expected
warnings = validate_literature_bounds(
    S_ske_m1=1e-4, S_skv_m1=5e-4,  # non-zero inelastic in proximal zone
    layer='F1', station='PROX_TEST', fan_zone='proximal'
)
print(f'Warnings for proximal fan with S_skv=5e-4: {warnings}')
print(f'Expected: should warn that inelastic storage unexpected in proximal fan')
print(f'Warning emitted: {len(warnings) > 0}')
"
```
**Expected:** If warnings list is empty, G5 is confirmed.

### Step 3.6: Verify V(t) NaN invisibility
```bash
python3 -c "
import sys, numpy as np; sys.path.insert(0, '$REPO/scripts')
from guardrails import validate_virgin_term
# V(t) with NaN block hiding an increase (violation)
V = np.array([0.0, -0.1, -0.2, np.nan, np.nan, -0.5, -0.4])  # -0.5 → -0.4 is an increase
try:
    validate_virgin_term(V, 'TEST', 'TEST')
    print('No violation raised — NaN block hid the increase (G7 confirmed)')
except Exception as e:
    print(f'Violation raised: {e}')
"
```
**Expected:** If no exception, G7 confirmed (NaN hides the violation).

---

## ═══════════ PHASE 4: Kalman Filter Feasibility ═══════════

**Context:** `discussions/KALMAN_DESIGN_BRAINSTORM_20260612.md` proposes a scalar Kalman tracker as an alternative to the M8 level-reset estimator. Verify the key claims.

### Step 4.1: Verify SVD rank-1 of carrier contribution matrix
```bash
python3 -c "
import pandas as pd, numpy as np
# Build carrier contribution matrix: 6 layers × N epochs
layers = ['F1','T1','F2','T2','F3','F4']
data = {}
for layer in layers:
    df = pd.read_csv(f'$REPO/tau_demo_TUKU/results/reconstruction/TUKU_{layer}_reconstruction.csv')
    data[layer] = df['d_surface_mm'].values
# Stack into matrix (epochs × layers) — use common non-NaN epochs
valid = np.ones(len(data['F1']), dtype=bool)
for layer in layers:
    valid = valid & ~np.isnan(data[layer])
M = np.column_stack([data[l][valid] for l in layers])
U, S, Vt = np.linalg.svd(M, full_matrices=False)
print(f'Singular values: {S}')
print(f'SV1 = {S[0]:.2e}')
print(f'SV2/SV1 = {S[1]/S[0]:.2e} (should be < 1e-15)')
print(f'SV3/SV1 = {S[2]/S[0]:.2e}')
print(f'Rank = 1: {S[1]/S[0] < 1e-10}')
"
```
**Expected:** SV2/SV1 < 1e-15, confirming rank-1 degeneracy.

### Step 4.2: Compute Kalman gain for annual visit cadence
```bash
python3 -c "
Q = 9.0   # mm² — process noise (3 mm)² per 5-day epoch
R = 4.0   # mm² — measurement noise (2 mm)²
n_gap = 73  # epochs between annual visits (~365/5)
P_prior = n_gap * Q  # covariance after 1 year without update
K = P_prior / (P_prior + R)
print(f'P_prior (after 1 year): {P_prior:.0f} mm²')
print(f'Kalman gain K: {K:.4f}')
print(f'K ≈ 1.0 (hard reset): {K > 0.99}')
print(f'Expected: K ≈ 0.994, so M8 level reset ≈ optimal Kalman for annual cadence')
"
```
**Expected:** K ≈ 0.994. Yes, M8 hard reset ≈ Kalman limit for annual cadence.

### Step 4.3: Compute Kalman gain for monthly visit cadence
```bash
python3 -c "
Q = 9.0; R = 4.0; n_gap = 6  # monthly ≈ 30 days
P_prior = n_gap * Q
K = P_prior / (P_prior + R)
print(f'P_prior (after 1 month): {P_prior:.0f} mm²')
print(f'Kalman gain K: {K:.4f}')
print(f'K < 0.99 (differs from hard reset): {K < 0.99}')
print(f'Expected: K ≈ 0.93 — Kalman update differs from hard reset at monthly cadence')
"
```
**Expected:** K ≈ 0.93. Kalman update materially differs from hard reset at monthly cadence.

### Step 4.4: Implement scalar Kalman tracker and compare to M8
```bash
python3 -c "
import pandas as pd, numpy as np, json

# Load frozen calibration
with open('$REPO/tau_demo_TUKU/results/seq/frozen_calibration.json') as f:
    cal = json.load(f)
a = cal.get('a_total', cal.get('sum_a_k', 0.559))
print(f'Total carrier coefficient a = {a:.4f}')

# Load GPS surface
gps_df = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_F1_reconstruction.csv', parse_dates=['date'])
gps = gps_df[['date','d_surface_mm']].dropna()
gps_inc = gps['d_surface_mm'].diff().values  # incremental GPS

# Load MLCW total column from reconstruction (sum over layers)
total_obs = pd.Series(0.0, index=gps_df['date'].values)
for layer in ['F1','T1','F2','T2','F3','F4']:
    df = pd.read_csv(f'$REPO/tau_demo_TUKU/results/reconstruction/TUKU_{layer}_reconstruction.csv', parse_dates=['date'])
    total_obs = total_obs.add(df.set_index('date')['b_observed_mm'].reindex(total_obs.index), fill_value=0)
total_obs = total_obs.values  # cumulative total column

# Scalar Kalman (simplified — predict only, no update since MLCW visits are sparse)
Q, R = 9.0, 4.0
P = np.full(len(gps), np.nan)
z = np.full(len(gps), np.nan)
z[0] = 0.0
P[0] = R

# Simple predict-only (no MLCW update — pure carrier drift)
n = len(gps)
for t in range(1, n):
    z[t] = z[t-1] + a * (gps_inc[t] if not np.isnan(gps_inc[t]) else 0)
    P[t] = P[t-1] + Q

# Compute 90% prediction interval width at last epoch
hw_90 = 1.645 * np.sqrt(P[-1])
print(f'Final z = {z[-1]:.1f} mm')
print(f'Final P = {P[-1]:.0f} mm²')
print(f'90% prediction interval half-width at last epoch: {hw_90:.1f} mm')
print(f'Compare: M8 conformal half-width at annual cadence typically 2-4 mm')
"
```
**Expected:** Kalman prediction interval grows with time since last visit. Conformal bands are static.

### Step 4.5: Verify per-layer decomposition formula
```bash
python3 -c "
import json
with open('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_carrier_reconstruction_summary.json') as f:
    d = json.load(f)
a_total = sum(d['per_layer'][l]['a_k'] for l in ['F1','T1','F2','T2','F3','F4'])
for layer in ['F1','T1','F2','T2','F3','F4']:
    a_k = d['per_layer'][layer]['a_k']
    fraction = a_k / a_total
    print(f'{layer}: a_k/a_total = {a_k:.4f}/{a_total:.4f} = {fraction:.3f} ({fraction*100:.1f}% of column)')
print(f'Sum of fractions: {sum(d[\"per_layer\"][l][\"a_k\"]/a_total for l in [\"F1\",\"T1\",\"F2\",\"T2\",\"F3\",\"F4\"]):.4f} (should = 1.0)')
"
```
**Expected:** Fractions sum to 1.0. F3 gets largest share (0.306/0.637 = 48.0%).

---

## ═══════════ PHASE 5: ARX / Prophet / MCR-AR Re-Evaluation ═══════════

### Step 5.1: Read and verify ARX obsolete results
```bash
python3 -c "
import pandas as pd
# Check if ARX results directory exists
import os
arx_dir = '$REPO/results/arx_OBSOLETE_temporal_methods'
if os.path.exists(arx_dir):
    files = os.listdir(arx_dir)
    print(f'ARX results directory exists: {len(files)} files')
    for f in files[:10]:
        print(f'  {f}')
else:
    print('ARX results directory NOT FOUND')
print()
# Read ARX discussion
arx_disc = '$REPO/notes/methods/discussion_20260517_arx_results.md'
if os.path.exists(arx_disc):
    with open(arx_disc) as f:
        content = f.read()
    # Extract key claims
    if '92.1%' in content:
        print('Claim found: median 92.1% RMSE reduction')
    if 'anchor-only' in content:
        idx = content.find('anchor-only')
        print(f'anchor-only mention: ...{content[max(0,idx-50):idx+100]}...')
    if 'phi_k' in content:
        idx = content.find('phi_k')
        print(f'phi_k mention: ...{content[max(0,idx-30):idx+80]}...')
else:
    print('ARX discussion NOT FOUND')
"
```
**Expected:** ARX results show 67-97% RMSE reduction at active stations (median 92.1%). phi_k ≈ 1.0 for all stations. Anchor-only ablation matched ARX.

### Step 5.2: Read and verify Prophet obsolete results
```bash
python3 -c "
import os
prophet_dir = '$REPO/results/prophet_OBSOLETE_ablation'
if os.path.exists(prophet_dir):
    files = os.listdir(prophet_dir)
    print(f'Prophet results exist: {len(files)} files')
    for f in files:
        print(f'  {f}')
print()
prophet_disc = '$REPO/notes/methods/discussion_20260517_prophet_tuku.md'
if os.path.exists(prophet_disc):
    with open(prophet_disc) as f:
        content = f.read()
    if 'deep' in content.lower():
        for line in content.split('\n'):
            if 'deep' in line.lower() and ('%' in line or 'improve' in line.lower()):
                print(f'Deep depth claim: {line.strip()[:120]}')
    if 'shallow' in content.lower():
        for line in content.split('\n'):
            if 'shallow' in line.lower() and ('%' in line or 'degrad' in line.lower()):
                print(f'Shallow depth claim: {line.strip()[:120]}')
else:
    print('Prophet discussion NOT FOUND')
"
```
**Expected:** Prophet improved deep depths (50-66%), degraded shallow depths (-62% to -218%). Generally inferior to ARX.

### Step 5.3: Re-implement ARX on current TUKU data
```bash
python3 -c "
import pandas as pd, numpy as np

# Load TUKU original field data (not reconstructed)
orig = pd.read_csv('$REPO/data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv', parse_dates=['datetime'])
# Sum all layers to get total column
orig['total'] = orig[['F1','T1','F2','T2','F3','F4']].sum(axis=1)
orig = orig.dropna(subset=['total'])

# Load GPS surface
gps = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_F1_reconstruction.csv', parse_dates=['date'])
gps_valid = gps.dropna(subset=['d_surface_mm'])

# ARX(1): Y_t = phi * Y_{t-1} + beta * X_t + eps
# Fit on first 80% of genuine visits
n_visits = len(orig)
n_train = int(0.8 * n_visits)
train = orig.iloc[:n_train]
test = orig.iloc[n_train:]

# Merge with GPS on nearest date
train_dates = train['datetime'].values
Y = train['total'].values
# Get GPS at those dates
gps_at_train = []
for d in train_dates:
    match = gps_valid.iloc[(gps_valid['date'] - pd.Timestamp(d)).abs().argsort()[:1]]
    gps_at_train.append(match['d_surface_mm'].values[0] if len(match) > 0 else np.nan)
X = np.array(gps_at_train)
valid = ~np.isnan(X) & ~np.isnan(Y[1:])

# Least squares: Y_t = phi * Y_{t-1} + beta * X_t
# Using valid indices
Y_curr = Y[1:][valid[1:]] if len(valid) > 1 else Y[1:]
Y_prev = Y[:-1][valid[:-1]] if len(valid) > 1 else Y[:-1]
X_curr = X[1:][valid[1:]] if len(valid) > 1 else X[1:]

if len(Y_curr) > 10:
    A = np.column_stack([Y_prev, X_curr, np.ones(len(Y_curr))])
    coeffs, _, _, _ = np.linalg.lstsq(A, Y_curr, rcond=None)
    phi, beta, intercept = coeffs
    print(f'ARX(1) fit: phi={phi:.4f}, beta={beta:.4f}, intercept={intercept:.2f}')
    print(f'phi ≈ 1.0: {abs(phi - 1.0) < 0.05}')
    
    # Walk-forward test
    last_y = Y[n_train-1]
    predictions = []
    for i in range(len(test)):
        d = test['datetime'].iloc[i]
        match = gps_valid.iloc[(gps_valid['date'] - pd.Timestamp(d)).abs().argsort()[:1]]
        x_t = match['d_surface_mm'].values[0] if len(match) > 0 else 0
        pred = phi * last_y + beta * x_t + intercept
        predictions.append(pred)
        # If this is a genuine visit, update last_y
        true_val = test['total'].iloc[i]
        if not pd.isna(true_val):
            last_y = true_val
    
    pred_arr = np.array(predictions)
    true_arr = test['total'].values
    valid_test = ~np.isnan(true_arr)
    if valid_test.sum() > 0:
        rmse = np.sqrt(np.mean((pred_arr[valid_test] - true_arr[valid_test])**2))
        # Baseline: just hold last value
        baseline_pred = np.full(len(test), Y[n_train-1])
        baseline_rmse = np.sqrt(np.mean((baseline_pred[valid_test] - true_arr[valid_test])**2))
        print(f'ARX walk-forward RMSE: {rmse:.2f} mm')
        print(f'Baseline (hold-last) RMSE: {baseline_rmse:.2f} mm')
        print(f'ARX improvement: {(1 - rmse/baseline_rmse)*100:.1f}%')
        print(f'Previous claim: anchor-only ablation matched ARX — verify: improvement < 5%?')
else:
    print('Insufficient data for ARX fit')
"
```
**Expected:** φ ≈ 1.0, ARX improvement over baseline minimal (< 5%). Confirms anchor-only ablation finding.

### Step 5.4: Re-implement Prophet on current TUKU F2 data
```bash
python3 -c "
import pandas as pd, numpy as np
# Try importing prophet
try:
    from prophet import Prophet
    print('Prophet available')
except ImportError:
    print('Prophet NOT installed — SKIP this step. Record SKIP with reason.')
    exit(0)

# Load F2 data
orig = pd.read_csv('$REPO/data/mlcw/group_byLayer_orig/TUKU_orig_grouped.csv', parse_dates=['datetime'])
f2 = orig[['datetime','F2']].dropna()
f2.columns = ['ds','y']
f2['ds'] = pd.to_datetime(f2['ds'])

# Fit on first 80%
n_train = int(0.8 * len(f2))
train = f2.iloc[:n_train]
test = f2.iloc[n_train:]

m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
m.fit(train)
future = m.make_future_dataframe(periods=len(test), freq=None)
# Use test dates
future = pd.DataFrame({'ds': test['ds']})
forecast = m.predict(future)

rmse = np.sqrt(np.mean((forecast['yhat'].values - test['y'].values)**2))
# Baseline: linear trend extrapolation
from sklearn.linear_model import LinearRegression
X_train = (train['ds'] - train['ds'].min()).dt.days.values.reshape(-1,1)
lr = LinearRegression().fit(X_train, train['y'])
X_test = (test['ds'] - train['ds'].min()).dt.days.values.reshape(-1,1)
baseline_pred = lr.predict(X_test)
baseline_rmse = np.sqrt(np.mean((baseline_pred - test['y'].values)**2))
print(f'Prophet RMSE: {rmse:.2f} mm')
print(f'Linear trend RMSE: {baseline_rmse:.2f} mm')
print(f'Prophet improvement over trend: {(1-rmse/baseline_rmse)*100:.1f}%')
"
```
**Expected:** If Prophet not installed, SKIP. If installed, Prophet likely does not substantially outperform linear trend for F2 (seasonal signal is weak).

### Step 5.5: Implement MCR-AR on F2 and F3 layers
```bash
python3 -c "
import pandas as pd, numpy as np
'''
Multivariate Curve Resolution with Alternating Regression (MCR-AR)
Applied to: F2 and F3 per-layer compaction timeseries

MCR-AR decomposes a data matrix D (epochs × 2 layers) into:
  D = C * S^T + E
where C (epochs × k) are concentration profiles and S (layers × k) are pure spectra.
Alternating regression:
  1. Initialize S (random or from PCA)
  2. Given S, solve C = D * S * (S^T * S)^(-1)  [with non-negativity]
  3. Given C, solve S^T = (C^T * C)^(-1) * C^T * D  [with non-negativity]
  4. Repeat until convergence

The hypothesis: MCR-AR can separate the F2 and F3 signals into components
that the carrier model conflates (since both are scalar multiples of the same GPS signal).
'''

# Load F2 and F3 reconstruction data
f2 = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_F2_reconstruction.csv', parse_dates=['date'])
f3 = pd.read_csv('$REPO/tau_demo_TUKU/results/reconstruction/TUKU_F3_reconstruction.csv', parse_dates=['date'])

# Use cumulative observed values
f2_obs = f2['b_observed_mm'].values
f3_obs = f3['b_observed_mm'].values

# Build data matrix D (valid epochs × 2 layers)
valid = ~np.isnan(f2_obs) & ~np.isnan(f3_obs)
D = np.column_stack([f2_obs[valid], f3_obs[valid]])
print(f'Data matrix D: {D.shape[0]} valid epochs × {D.shape[1]} layers')

# Center by subtracting column means
D_mean = D.mean(axis=0)
D_ctr = D - D_mean

# Initialize with 2 components from PCA
U, S, Vt = np.linalg.svd(D_ctr, full_matrices=False)
k = min(2, len(S))  # number of components
S_mat = Vt[:k].T.copy()  # (layers × k)
print(f'Singular values: {S[:k]}')
print(f'SV2/SV1 = {S[1]/S[0]:.4f} (> 0.1 → two meaningful components exist)')

# MCR-AR iterations
n_iter = 50
for it in range(n_iter):
    # Step 1: Given S, solve C with non-negativity (shifted to be ≥ 0)
    StS = S_mat.T @ S_mat
    if np.linalg.cond(StS) < 1e10:
        C_mat = D_ctr @ S_mat @ np.linalg.inv(StS)
    else:
        C_mat = D_ctr @ S_mat @ np.linalg.pinv(StS)
    
    # Non-negativity: shift each column to be ≥ 0
    for j in range(k):
        shift = C_mat[:, j].min()
        if shift < 0:
            C_mat[:, j] -= shift
    
    # Step 2: Given C, solve S with non-negativity
    CtC = C_mat.T @ C_mat
    if np.linalg.cond(CtC) < 1e10:
        S_new = np.linalg.inv(CtC) @ C_mat.T @ D_ctr
    else:
        S_new = np.linalg.pinv(CtC) @ C_mat.T @ D_ctr
    
    # Non-negativity
    for j in range(k):
        shift = S_new[:, j].min()
        if shift < 0:
            S_new[:, j] -= shift
    
    # Check convergence
    change = np.abs(S_new - S_mat).max()
    S_mat = S_new
    if change < 1e-8:
        print(f'Converged at iteration {it+1}')
        break

# Reconstruct
D_recon = C_mat @ S_mat.T + D_mean
residual = D - D_recon
r2_f2 = 1 - np.var(residual[:,0]) / np.var(D[:,0])
r2_f3 = 1 - np.var(residual[:,1]) / np.var(D[:,1])
print(f'MCR-AR R²: F2={r2_f2:.4f}, F3={r2_f3:.4f}')
print(f'Components: S matrix (layers × {k}) =')
print(S_mat)

# Compare: carrier model R²
f2_carrier = f2['b_model_mm'].values[valid]
f3_carrier = f3['b_model_mm'].values[valid]
r2_f2_carrier = 1 - np.var(f2_carrier - D[:,0]) / np.var(D[:,0])
r2_f3_carrier = 1 - np.var(f3_carrier - D[:,1]) / np.var(D[:,1])
print(f'Carrier model R²: F2={r2_f2_carrier:.4f}, F3={r2_f3_carrier:.4f}')
print(f'MCR-AR vs Carrier: F2 delta={r2_f2 - r2_f2_carrier:+.4f}, F3 delta={r2_f3 - r2_f3_carrier:+.4f}')
"
```
**Expected:** MCR-AR identifies two components in F2/F3 data (SV2 > 0). If both layers are scalar multiples of GPS (rank-1), MCR-AR will find only 1 meaningful component, confirming the degeneracy from a different mathematical angle.

---

## ═══════════ PHASE 6: Sequential Rehearsal Verification ═══════════

### Step 6.1: Verify semiannual seq RMSE against metrics.json
```bash
python3 -c "
import pandas as pd, numpy as np, json

with open('$REPO/tau_demo_TUKU/results/seq/semiannual/metrics.json') as f:
    metrics = json.load(f)

for layer in ['F1','T1','F2','T2','F3','F4']:
    claimed_rmse = metrics['layers'][layer]['RMSE_mm']
    
    # Recompute from data
    seq = pd.read_csv(f'$REPO/tau_demo_TUKU/results/seq/semiannual/TUKU_{layer}_seq_timeseries.csv', parse_dates=['date'])
    transp = pd.read_csv(f'$REPO/tau_demo_TUKU/results/seq/transparency/TUKU_{layer}_transparency_data.csv', parse_dates=['date'])
    
    merged = seq.merge(transp[['date','obs_verified_mm','is_reveal']], on='date', how='left')
    reveals = merged[merged['is_reveal'] == True].dropna(subset=['obs_verified_mm'])
    
    if len(reveals) > 0:
        recomputed_rmse = np.sqrt(np.mean((reveals['pred_mm'] - reveals['obs_verified_mm'])**2))
        match = abs(recomputed_rmse - claimed_rmse) < 0.01
        print(f'{layer}: claimed={claimed_rmse:.3f}, recomputed={recomputed_rmse:.3f}, match={match}')
    else:
        print(f'{layer}: no reveal data to verify')
"
```
**Expected:** All layers: claimed RMSE matches recomputed within 0.01 mm.

### Step 6.2: Verify coverage claims per cadence
```bash
python3 -c "
import pandas as pd, json

with open('$REPO/tau_demo_TUKU/results/auditor_diagnostics/auditor_summary.json') as f:
    summary = json.load(f)

print('Coverage scorecard (in_band fraction):')
print(f'{\"Layer\":<6}', end='')
cadences = list(summary['seq_coverage'].keys())
for c in cadences:
    print(f'{c:>12}', end='')
print()
for layer in ['F1','T1','F2','T2','F3','F4']:
    print(f'{layer:<6}', end='')
    for c in cadences:
        val = summary['seq_coverage'][c].get(layer, {}).get('in_band_fraction', None)
        if val is not None:
            print(f'{val:>11.1%}', end='')
        else:
            print(f'{\"N/A\":>12}', end='')
    print()
print()
print('Red Team claim: semiannual coverage FAIL (3/6 layers < 0.85)')
# Verify
semi = summary['seq_coverage'].get('semiannual', {})
n_pass = sum(1 for l in ['F1','T1','F2','T2','F3','F4'] if semi.get(l, {}).get('in_band_fraction', 0) >= 0.85)
print(f'Semiannual: {n_pass}/6 layers pass 0.85 threshold')
"
```
**Expected:** Semiannual: ≤ 4/6 layers pass (Red Team claim: 3/6). Monthly: 5/6 pass.

### Step 6.3: Verify honest skill table (anchor-once baseline)
```bash
python3 -c "
import json, os
honest_path = '$REPO/tau_demo_TUKU/results/seq/red_team_fixes/anchor_once/honest_skill_table.json'
if os.path.exists(honest_path):
    with open(honest_path) as f:
        skill = json.load(f)
    print('Honest skill (anchor-once baseline):')
    for layer in ['F1','T1','F2','T2','F3','F4']:
        val = skill.get(layer, None)
        if isinstance(val, dict):
            print(f'  {layer}: {json.dumps(val)[:200]}')
        else:
            print(f'  {layer}: {val}')
    print()
    print('Red Team claim: honest annual skill ≤ 0 for F2/T2, +0.19 for F3')
else:
    print(f'Honest skill table not found at {honest_path}')
    print('Check alternative paths:')
    import glob
    for f in glob.glob('$REPO/tau_demo_TUKU/results/seq/red_team_fixes/**/*skill*', recursive=True):
        print(f'  {f}')
"
```
**Expected:** F2/T2 honest skill ≤ 0, F3 skill ≈ +0.19. Confirms skill was inflated in original framing.

### Step 6.4: Verify leakage guard (TimeOracle)
```bash
grep -rn "TimeOracle\|leakage\|leak_guard" $REPO/tau_demo_TUKU/seq/ --include="*.py" | head -20
```
**Operation:** Verify TimeOracle class exists and is imported in walk-forward scripts.
**Expected:** TimeOracle implemented in `tau_demo_TUKU/seq/`. Leakage guard prevents training on future data.

---

## ═══════════ PHASE 7: Cross-Layer & Regime Diagnostics ═══════════

### Step 7.1: Verify F3 regime classification (our claim: 97% inelastic)
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('$REPO/tau_demo_TUKU/results/auditor_diagnostics/per_layer_regime_epochs.csv')
for layer in ['F1','T1','F2','T2','F3','F4']:
    ldf = df[df['layer'] == layer].dropna(subset=['regime'])
    elastic = (ldf['regime'] == 'elastic').sum()
    inelastic = (ldf['regime'] == 'inelastic').sum()
    print(f'{layer}: elastic={elastic}, inelastic={inelastic}, frac_inelastic={inelastic/max(len(ldf),1):.1%}')
"
```
**Expected:** F3 ≈ 97% inelastic. F2 ≈ 99% inelastic. F4 ≈ 29% inelastic.

### Step 7.2: Verify F3 head-compaction mismatch clusters in June
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('$REPO/tau_demo_TUKU/results/auditor_diagnostics/per_layer_regime_epochs.csv')
f3 = df[(df['layer'] == 'F3') & (~df['expected_sign_match'])]
f3['month'] = pd.to_datetime(f3['date']).dt.month
print('F3 head-compaction mismatches by month:')
print(f3['month'].value_counts().sort_index().to_string())
print(f'June dominance: {f3[\"month\"].value_counts().get(6, 0)} of {len(f3)} mismatches in June')
"
```
**Expected:** June dominates (rainy season recharge → head rises while F3 continues compacting).

### Step 7.3: Verify column closure error magnitude
```bash
python3 -c "
import pandas as pd, numpy as np
df = pd.read_csv('$REPO/tau_demo_TUKU/results/auditor_diagnostics/cross_layer_consistency.csv')
mismatch = df['column_mismatch_mm'].dropna()
print(f'Column closure error:')
print(f'  p50: {mismatch.abs().median():.2f} mm')
print(f'  p95: {mismatch.abs().quantile(0.95):.2f} mm')
print(f'  max: {mismatch.abs().max():.2f} mm')
print(f'  mean signed: {mismatch.mean():.2f} mm (positive = sum_pred > sum_obs)')
print(f'Our claim: p95 = 256 mm')
print(f'Within 20%: {abs(mismatch.abs().quantile(0.95) - 256) / 256 < 0.20}')
"
```
**Expected:** p95 column mismatch ≈ 200-300 mm. Carrier model does not enforce Σ a_k = 1.0.

---

## ═══════════ PHASE 8: Final Verdict Assembly ═══════════

### Step 8.1: Assemble pass/fail/skip summary for all 42 steps
**Operation:** Compile a table with columns: `Phase, Step, Status (PASS/FAIL/SKIP), Evidence (one-line)`
**Output format:**
```
| Phase | Step | Status | Evidence |
|-------|------|--------|----------|
| 0 | 0.1 | PASS | F3 = 172.9–272.7 m per classify_table |
| 0 | 0.4 | FAIL | Previous 79 m gap claim FALSE — well IS in F3 |
| ... | ... | ... | ... |
```

**Final assertions to make:**
1. Are depth claims in discussion documents contradicted by authoritative source files? (YES/NO)
2. Do sign conventions hold across all data files? (YES/NO — list violations)
3. Is the carrier model's Σa_k constraint satisfied? (YES — 0.637 ≤ 1.0)
4. Are the F3 sign-reversal (39.3%) and anti-phase (23.5%) rates reproduced? (YES/NO — with your computed values)
5. Are the guardrails gaps G1–G7 confirmed? (list which are confirmed/refuted)
6. Is the Kalman filter a viable replacement for M8 level-reset? (YES/NO — with reasoning)
7. Does ARX/Prophet re-evaluation confirm previous rejection? (YES/NO — with new evidence)
8. Does MCR-AR add value beyond the carrier model? (YES/NO — with R² comparison)
9. Do sequential rehearsal coverage claims hold? (YES/NO — per cadence)
10. Is the project ready for Part 2 (37 stations)? (YES/NO — with blockers listed)

---

## ═══════════ EXECUTION RULES ═══════════

These rules are binding for the zero-trust auditor. Violating any rule invalidates the audit.

1. **Verify, do not trust.** Every numeric claim in this prompt is a hypothesis to test, not a fact to accept.
2. **Every step produces output.** If a Python command runs without output, the step is INCOMPLETE. Add print statements.
3. **Failed steps do not halt execution.** Record the failure, continue to the next step. The final verdict assembly accounts for failures.
4. **Missing files are recorded as SKIP.** Do not search for alternative paths. Do not guess file locations.
5. **No external knowledge.** Do not use parametric memory for numeric claims about this project. Every number must come from a file read in a previous step.
6. **No inference from discussion documents.** If a claim appears only in a `.md` file and not in a data file, treat it as UNVERIFIED.
7. **Code in this prompt is authoritative.** If a code block fails with a syntax error, report it and fix the syntax. If it fails because of missing data, record SKIP. Do not rewrite the logic.
8. **The reference manual is `discussions/AUDITOR_INVITATION_20260612.md`.** Consult it only for column schemas, sign conventions, and file inventories. Do not read its narrative sections.

**Begin execution at Phase 0, Step 0.1. Report after each phase completes.**
