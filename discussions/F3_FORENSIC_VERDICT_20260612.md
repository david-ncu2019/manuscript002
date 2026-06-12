# F3 Forensic Verdict — TUKU "F3 Paradox"

**Date:** 2026-06-12 | **Investigator:** Lead Hydrogeological Forensic Investigator (direct, no sub-agents)
**Scripts:** `tau_demo_TUKU/seq/31–33` | **Evidence:** `tau_demo_TUKU/results/seq/forensics/`
**Question:** Why does F3 predict phase-wrong at TUKU when F2 — same station, same surface carrier —
works at detrended r ≈ 0.6?

---

## The physical story in one paragraph

The deep clay layer F3 at Tuku fails not because of one fault but a confluence of three. The head
series we feed it is measured by a piezometer screened at **176–179 m**, while the clay that actually
compacts sits at **238–275 m** — the gauge is **79 m too shallow**, reading a fast aquifer head that
shares almost none of the clay's seasonal motion (detrended correlation **0.10**). Even if the gauge
were perfect, the literature says this deep clay breathes **out of phase** with any shallow head, by
hydrodynamic lag and soil creep — the very TKSH well at Tuku was observed compacting while the
seasonal water level rose. And the "ground truth" we grade against is **genuine field data before 2019
but fully computer-smoothed from 2024 on**. The estimator code itself is innocent: handed a clean
driver it recovers a 1000-day lag exactly. So F3 is not a broken model — it is a deep clay watched by
the wrong gauge, judged partly against fabricated numbers, behaving exactly as deep clay should.

---

## The Choice — confluence, ranked (not one smoking gun)

| Rank | Hypothesis | Verdict | Deciding evidence |
|------|-----------|---------|-------------------|
| 1 | **H1 — depth-mismatched driver** | **SUPPORTED** | Assigned well `09050331` carries ~0 of F3's seasonal (detrended \|r\| = **0.10**; v4's 0.24 was a trend-only number, independently reproduced at 0.39 trend-inclusive). Screen 176–179 m vs clay 238–275 m → **79 m gap, 0 m overlap**. Assigned well ranks **237/242**. |
| 2 | **H3 — physical outlier (out-of-phase deep clay)** | **SUPPORTED** | Phase-0 literature: TKSH/Tuku clay observed out-of-phase with seasonal GWL 2004–2007; 90 %-compaction time 26–488 days at 220–300 m; soil creep + Noordbergum reversal; surface-only inversion rank-deficient. No piezometer is screened in the F3 clay, so the slow driving head is **unmeasured**. |
| 3 | **H2 — poisoned truth (temporal)** | **PARTIAL** | F3 "truth" non-integer fraction **15 % (pre-2019) → 42 % (2019–23) → 100 % (2024+)**. Aggregate roughness still matches genuine F2 (std of 2nd difference 4.19 vs 4.90; dense fill 0.39), so the early record is real; only the recent era is smoothed. |
| — | **Code at fault?** | **REJECTED** | Synthetic recovery: injected τ = 200 recovered **exactly** (S_ke 2.02 vs 2.0, S_kv 4.95 vs 5.0). Lag recovery survives only down to driver \|r\| ≈ 0.58; the real F3 well sits at 0.10–0.24. |

Scorecard: `plots/seq/forensics/f3_verdict_decision.png`. Matrix: `results/seq/forensics/f3_verdict_matrix.json`.

---

## Reputation result — the estimator is sound (Phase 1, script 31)

A controlled synthetic 6-layer world was built with F3 given a **τ = 200 epochs (1000 days)** lag and
a seasonal phase that **opposes F2** (zero-lag detrended r = −0.73). Fed a clean, independent driver,
the frozen-model solver recovered:

- **τ = 200** (injected 200; tolerance ±3) ✓
- **S_ke = 2.02** (truth 2.0, within 15 %) ✓ · **S_kv = 4.95** (truth 5.0) ✓

A driver-quality sweep then degraded the head and measured the lagged-peak correlation (the same
"xcorr_max" semantics as the production assignment). **Lag recovery survives only down to peak-\|r\|
≈ 0.58.** At the real F3 well's 0.24 the solver loses the lag entirely (recovers τ = 113, S_ke → 0.03).
**Conclusion: driver quality, not the code, governs whether the deep lag can be found.** This is the
hinge of the whole verdict — it converts "F3 is phase-wrong" from a modelling failure into an
input-quality failure.

Evidence: `synthetic_reputation.json`, `synthetic_driver_quality_sweep.csv`, `synthetic_recovery.png`.

---

## Physical Interpretation (geomechanical meaning)

**The driver gauges the wrong stress horizon.** The F3 layer at TUKU is 99.8 m thick (172.9–272.7 m),
of which **77 m is fine-grained aquitard** — the inelastic mass that produces the compaction. That mass
is concentrated in the deep half (238–275 m, CLAUDE.md borehole breakdown). The assigned head gauge
`09050331` is screened at 176–179 m, in the thin sandy top (4.6 % into the layer). Effective stress at
177 m and effective stress at 256 m are governed by different, depth-lagged pore-pressure fields in a
clay this thick: pore pressure at the clay's centre dissipates on the 26–488-day (literature) to ~815-day
(diagnosed) timescale, while the 177 m sand tracks the seasonal cycle almost instantly. So the gauge
reports a head that is both **weak in shared seasonal variance (0.10)** and **wrong in phase** for the
clay. By contrast the F2 gauge `09050321` sits mid-layer (44 % depth) and reaches r ≈ 0.33 / 0.61 —
which is why F2 "works."

**The clay's storage character is consistent with the literature.** The diagnosed F3 lag (≈815 days)
**exceeds** the literature 90 %-compaction upper bound for this depth (488 days) — a signature of
residual/secondary compression (soil creep), the visco-elasto-plastic behaviour that keeps clay
compacting at constant effective stress and desynchronises it from the seasonal head. The "phase-wrong"
F3 the Red Team flagged is therefore the **physically expected** response of a deep Holocene aquitard,
not an artefact.

**The recent truth cannot be trusted.** Magnetic-ring extensometers read to 1 mm (Phase 0), so genuine
values are integer millimetres. The 2024+ F3 rows are 100 % non-integer — they passed through numeric
processing and are not field-verifiable. Any 2024 confirmatory grade on F3 is provisional at best.

---

## Implication for the blocked project

This **confirms** the Red Team's "underdetermined at sparse cadence" verdict but **sharpens it into an
instrumentation conclusion**:

- The reason is not merely sparse visits. It is that **the physically correct driver — a piezometer
  screened in the F3 clay at 240–275 m — does not exist in the network at TUKU.** The slow head that
  drives the deep compaction is simply unmeasured.
- The deep clay is **intrinsically out of phase** with every shallow head that *does* exist, so no
  re-assignment among the available wells fixes F3 (the best local candidate reaches only 0.65, and
  only at an 810-day lag — itself a fingerprint of the extreme lag, and partly lag-shopping).

**Actionable next step (physical):** F3 sub-annual reconstruction at TUKU requires either (a) a deep
co-screened piezometer at 240–275 m, or (b) a modelled deep head (e.g. a 1-D consolidation/MODFLOW-CSUB
head at the clay centroid) as the driver — not another shallow well. With only shallow heads + surface
GPS, F3 sub-annual dynamics stay unrecoverable. What **remains valid and deployable** is unchanged from
the Red Team remediation: **secular trend apportionment (<1 % error) + datum maintenance via sparse
visits + partial F2 dynamics.** F3/F4 deep-clay dynamics are deferred to a deep-head track.

**Status:** This forensic result is advisory. It does not unblock Part 2/Part 3 — it tells us *why* F3
is blocked and *what data* would unblock it. Awaiting human direction on whether to pursue a modelled
deep head for F3 before any multi-station extension.

---

## Artifacts

- Phase 0: `results/seq/forensics/phase0_geomech_prior.{md,json}`
- Phase 1: `seq/31_synthetic_reputation_test.py`; `synthetic_reputation.{json,csv}`,
  `synthetic_driver_quality_sweep.csv`, `plots/.../synthetic_recovery.png`
- Phase 2: `seq/32_f3_input_forensics.py`; `driver_purity.{json,csv}`,
  `interpolation_signature.{json,csv}`, `geomech_consistency.{json,csv}`, `f3_forensics_summary.json`;
  `plots/.../{driver_purity_top,interpolation_signature,geomech_consistency}.png`
- Phase 3: `seq/33_f3_verdict_assembly.py`; `f3_verdict_matrix.{json,csv}`,
  `plots/.../f3_verdict_decision.png`
- Run logs (no-in-sample manifests): `results/seq/forensics/3?_*_run_log.txt`
