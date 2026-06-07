> ⛔ STATUS: PAUSED — waiting for user to fill missing GWL values (2026-06-02)
> Resume order: (1) user provides filled GWL files → (2) run gap audit → (3) TAU_MAX fix → (4) bounds fix → (5) re-run TUKU → (6) batch run
> ⚠ CRITICAL: Do NOT interpret α=0.0197 as "explained by the 40% below-300 m depth gap." These are independent facts. Run the MLCW/InSAR ratio check first (see memory file ihmf_audit_findings.md).

# What to Prepare for the Next Stage
*Written 2026-06-02. Plain language. No jargon.*

---

## Where we are right now

The model has been fixed and tested at one station (TUKU). The test results are good enough to move forward — the model fits the borehole compaction data to within 1.2 mm error. The next goal is to run the model at all 191 station-layer combinations across the fan.

Before that batch run can happen, two things need to be done in code (I handle them), and three things need your input. This document tells you exactly what to prepare.

---

## What I will do — no input needed from you

These are code changes. I will do them when you say go.

### Code fix 1 — Extend the lag search window
One underground layer (the shallow clay T1) has its response time stuck at the maximum allowed value of 365 days. This means the model found the wall of the search box instead of the true answer. I will extend the search box to 600 days and re-run TUKU to find T1's real response time.

**Time needed:** About 10 minutes.

### Code fix 2 — Add physical limits to the model parameters
Right now the model has no upper ceiling on how large the compaction coefficients can be. Across repeated tests, the F2 aquifer coefficient drifted from 0.197 up to 1.078 — a 5-fold swing — which means the model is memorizing each test window rather than learning a stable physical value. I will add physically-grounded upper limits from the published literature for this fan.

**Time needed:** About 20 minutes.

### Code fix 3 — Re-run TUKU and check stability
After both fixes, run TUKU again and confirm the walk-forward tests no longer produce all-negative fit quality scores.

---

## What I need from you — your three tasks

---

### Your Task 1 — Check whether three specific wells have complete water-level records (HIGHEST PRIORITY)

Three groundwater monitoring wells are each shared by 6 or 7 station-layer pairs in the model. If any of these wells has missing readings during 2015–2025, the model breaks for all those pairs at once.

The three wells are:

| Well code | Serves this many pairs |
|---|---|
| **10070141** | 7 pairs |
| **09050341** | 6 pairs |
| **09080251** | 6 pairs |

**What to check:** In your Water Resources Agency database or local raw data files, look up each of these three wells. Does each well have continuous water-level readings from January 2015 through December 2025? Or are there months or years where the gauge was broken, the well was dry, or the data was not recorded?

**What to give me:** A simple list — "well 10070141: complete" or "well 09080251: gap from April 2019 to August 2020." If you have the raw reading files (Excel, CSV, or text), you can drop them in the folder `data/gwl/raw_gwl_records/` and I will read them directly.

**Why it matters:** Fixing gaps in these three wells improves up to 19 model fits at once — the highest return on your time.

---

### Your Task 2 — Run one command and paste the result (5 minutes)

This command checks all 189 water-level files already in the project and tells us which ones have internal missing readings. You do not need to understand the output — just paste it back here.

Run this in PowerShell:

```powershell
$env:PYTHONPATH = ""
conda run -n fafalab python -c "
import pandas as pd
from pathlib import Path
d = Path(r'D:\1000_SCRIPTS\004_Project003\20260427_InSAR_MLCW_v2\data\gwl\mlcw_gwl_timeseries')
results = []
for f in sorted(d.glob('*.feather')):
    df = pd.read_feather(f)
    col = [c for c in df.columns if 'head' in c.lower() or 'gwl' in c.lower() or 'level' in c.lower()]
    if not col:
        col = df.select_dtypes('number').columns.tolist()
    if col:
        n_nan = df[col[0]].isna().sum()
        n_total = len(df)
        if n_nan > 0:
            results.append(f'{f.name}: {n_nan}/{n_total} missing ({100*n_nan/n_total:.1f}%)')
for r in results:
    print(r)
print(f'--- Total files with any gap: {len(results)} of 189 ---')
"
```

**What to give me:** The full printed output — every line.

**Why it matters:** This tells us exactly which water-level records need filling. Without it, we are guessing.

---

### Your Task 3 — Tell me about the water-level history before 2015 at TUKU (optional but useful)

The model uses the lowest water level ever recorded at each well as the threshold between recoverable and permanent compaction. For TUKU, the current records start in 2015 — but the worst droughts in this area happened in 2002–2003.

If the well at TUKU was already deeper than the 2015 starting level during that earlier drought, the model is underestimating how much permanent compaction has occurred.

**What to check:** Do you have any record of the water level in the F2 aquifer well at TUKU (well code 09050321) before 2015? Specifically: what was the lowest recorded level in metres above sea level, and approximately when did it occur?

**What to give me:** Just one number — the lowest water level in metres MSL, and the approximate year it happened. If you do not have this, say so and we proceed without it.

---

## Priority order for your time

| Priority | Task | Time required from you |
|---|---|---|
| 1 (do first) | Run the PowerShell command (Task 2) and paste output | 5 minutes |
| 2 | Check wells 10070141, 09050341, 09080251 for gaps (Task 1) | 30–60 minutes |
| 3 (if available) | Look up TUKU F2 minimum head before 2015 (Task 3) | 10 minutes |

---

## What happens after you give me this information

1. I write a gap-filling script targeted at the specific wells with missing readings.
2. I rebuild the water-level files with gaps filled.
3. I apply both code fixes (extended search window + parameter limits).
4. I run the full 191-pair batch.
5. We review the batch results together.

The batch run is the gateway to the paper's results section. Everything above clears the path to it.

---

## What is NOT needed from you

- You do not need to write any code.
- You do not need to understand the model internals.
- You do not need to process or clean the raw data yourself — just locate it and give me the files or numbers.
- You do not need to check all 189 water-level files — the PowerShell command does that automatically.
