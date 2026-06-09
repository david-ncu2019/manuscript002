"""
guardrails.py — Automated Physical-Law Validation for IHM-F Pipeline

Usage:
    from guardrails import validate_layer_params, validate_virgin_term, GuardrailViolation

    validate_layer_params(S_ske_m1, S_skv_m1, layer, station, fan_zone="middle")
    validate_virgin_term(V_arr, layer)

All checks raise GuardrailViolation on failure — the caller decides whether to
halt, warn, or flag.  No silent pass-through of physically impossible values.

Physical sources:
  - Terzaghi (1925) effective stress: σ_vt = P + σ_ve
  - Riley (1969) stress-strain loop for preconsolidation head
  - Hung et al. (2021) WRR: Choushui River Alluvial Fan S_ske, S_skv per fan zone
  - MODFLOW 6 SUB/CSUB documentation (USGS)
  - CLAUDE.md physical-law halt table (project-specific)

Author: 2026-06-08 — built from 6 NotebookLM notebooks + 3 independent audits
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════════
# Literature Priors — Hung et al. (2021) WRR via Choushui_Sub notebook
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class FanZonePriors:
    """Skeletal specific storage priors per fan zone (Hung et al. 2021 WRR)."""
    S_ske_m1: float       # elastic skeletal specific storage [m⁻¹]
    S_skv_m1: float       # inelastic skeletal specific storage [m⁻¹]
    S_ske_tol: float      # acceptable deviation from prior (multiplicative)
    S_skv_tol: float

# Values from Choushui_Sub notebook query, 2026-06-08
# Tolerance = 1 order of magnitude (factor of 10) — per Gap 2 analysis
FAN_ZONE_PRIORS: dict[str, FanZonePriors] = {
    "proximal": FanZonePriors(
        S_ske_m1=1.18e-4, S_skv_m1=None,  # no inelastic in proximal fan
        S_ske_tol=10.0, S_skv_tol=10.0,
    ),
    "middle": FanZonePriors(
        S_ske_m1=1.15e-4, S_skv_m1=1.33e-3,
        S_ske_tol=10.0, S_skv_tol=10.0,
    ),
    "distal": FanZonePriors(
        S_ske_m1=1.16e-4, S_skv_m1=1.91e-3,
        S_ske_tol=10.0, S_skv_tol=10.0,
    ),
}

# For stations in transition zones, use closest match
FAN_ZONE_DEFAULT = "middle"

# ═══════════════════════════════════════════════════════════════════════════════
# Material Classification — borehole-based (Relearn_GeotechEngineer notebook)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class LayerMaterial:
    """Borehole-derived material properties for a layer at a specific station."""
    layer: str
    station: str
    total_m: float           # total borehole span [m]
    aquitard_m: float        # fine-grained material thickness [m]
    is_clay_dominated: bool   # > 50% fine-grained → clay physics applies
    fan_zone: str             # "proximal", "middle", "distal"

# TUKU borehole (YL_WSYL23G1_TUKU.xlsx, verified 2026-06-06)
# Source: tau_demo_TUKU/12_stress_strain_per_layer.py lines 97-124
TUKU_MATERIALS: dict[str, LayerMaterial] = {
    "F1": LayerMaterial("F1", "TUKU", 41.577, 16.577, False, "middle"),
    "T1": LayerMaterial("T1", "TUKU",  8.729,  7.423, True,  "middle"),
    "F2": LayerMaterial("F2", "TUKU", 106.284, 12.090, False, "middle"),
    "T2": LayerMaterial("T2", "TUKU", 16.299, 10.299, True,  "middle"),
    "F3": LayerMaterial("F3", "TUKU", 110.494, 76.994, True,  "middle"),
    "F4": LayerMaterial("F4", "TUKU", 16.617, 16.617, True,  "middle"),
}

# ═══════════════════════════════════════════════════════════════════════════════
# Exception class
# ═══════════════════════════════════════════════════════════════════════════════

class GuardrailViolation(Exception):
    """Raised when a physical-law check fails. Contains diagnostic message."""
    pass


class GuardrailWarning(UserWarning):
    """Non-fatal physical anomaly — flag but don't halt."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Check 1: Sign constraints (CLAUDE.md physical-law halt table)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_sign_constraints(
    S_ke: float,
    S_kv: float,
    layer: str,
    station: str = "UNKNOWN",
) -> None:
    """
    Halt if S_ke < 0 or S_kv < S_ke.

    CLAUDE.md: "S_ske >= 0, S_skv >= 0, beta >= 0. Negative solver output →
    reject the layer; do not accept."
    """
    if S_ke < 0:
        raise GuardrailViolation(
            f"{station}/{layer}: S_ke = {S_ke:.6f} is NEGATIVE — "
            f"elastic skeletal storage cannot be negative. Layer rejected."
        )
    if S_kv < 0:
        raise GuardrailViolation(
            f"{station}/{layer}: S_kv = {S_kv:.6f} is NEGATIVE — "
            f"inelastic skeletal storage cannot be negative. Layer rejected."
        )
    if S_kv < S_ke - 1e-15:  # ~1e-15 tolerance for floating-point
        raise GuardrailViolation(
            f"{station}/{layer}: S_kv ({S_kv:.6f}) < S_ke ({S_ke:.6f}) — "
            f"inelastic storage must be >= elastic storage. Layer rejected."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Check 2: Literature prior bounds (Gap 2 fix — Choushui_Sub notebook)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_literature_bounds(
    S_ske_m1: Optional[float],
    S_skv_m1: Optional[float],
    layer: str,
    station: str = "UNKNOWN",
    fan_zone: str = "middle",
    strict: bool = False,
) -> list[str]:
    """
    Flag if fitted specific storage deviates > 1 order of magnitude from
    Hung et al. (2021) WRR literature values for the station's fan zone.

    Parameters
    ----------
    strict : bool
        If True, raise GuardrailViolation. If False, return warning strings.

    Returns
    -------
    list[str] : warning messages (empty if all OK)
    """
    priors = FAN_ZONE_PRIORS.get(fan_zone, FAN_ZONE_PRIORS[FAN_ZONE_DEFAULT])
    warnings: list[str] = []

    if S_ske_m1 is not None and S_ske_m1 > 0:
        ratio_ske = S_ske_m1 / priors.S_ske_m1 if priors.S_ske_m1 > 0 else float("inf")
        if ratio_ske > priors.S_ske_tol or ratio_ske < (1.0 / priors.S_ske_tol):
            msg = (
                f"{station}/{layer}: S_ske = {S_ske_m1:.2e} m⁻¹ deviates "
                f"{ratio_ske:.1f}× from literature ({priors.S_ske_m1:.2e} m⁻¹, "
                f"{fan_zone} fan). Max allowed: {priors.S_ske_tol:.0f}×."
            )
            warnings.append(msg)
            if strict:
                raise GuardrailViolation(msg)

    if S_skv_m1 is not None and priors.S_skv_m1 is not None and S_skv_m1 > 0:
        ratio_skv = S_skv_m1 / priors.S_skv_m1
        if ratio_skv > priors.S_skv_tol or ratio_skv < (1.0 / priors.S_skv_tol):
            msg = (
                f"{station}/{layer}: S_skv = {S_skv_m1:.2e} m⁻¹ deviates "
                f"{ratio_skv:.1f}× from literature ({priors.S_skv_m1:.2e} m⁻¹, "
                f"{fan_zone} fan). Max allowed: {priors.S_skv_tol:.0f}×."
            )
            warnings.append(msg)
            if strict:
                raise GuardrailViolation(msg)

    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# Check 3: Specific storage ratio gate (relaxed from [8, 100])
# ═══════════════════════════════════════════════════════════════════════════════

def validate_ratio_gate(
    S_ske_m1: Optional[float],
    S_skv_m1: Optional[float],
    layer: str,
    station: str = "UNKNOWN",
    ratio_min: float = 3.0,
    ratio_max: float = 50.0,
) -> list[str]:
    """
    Flag if S_skv/S_ske ratio is outside [ratio_min, ratio_max].

    Relaxed from CLAUDE.md [8, 100] based on Gap 1 analysis: Hung et al. (2021)
    reports ~11.6× (middle fan), ~16× (distal fan). 5× and 50× are physically
    defensible upper/lower bounds for the Choushui system.
    """
    warnings: list[str] = []
    if S_ske_m1 is None or S_skv_m1 is None:
        return warnings
    if S_ske_m1 < 1e-15:
        return [f"{station}/{layer}: S_ske ≈ 0 — ratio undefined (inelastic-only)"]

    ratio = S_skv_m1 / S_ske_m1
    if ratio < ratio_min:
        msg = (
            f"{station}/{layer}: S_skv/S_ske = {ratio:.1f}× < {ratio_min:.0f}× — "
            f"inelastic storage too close to elastic. Possible collinearity "
            f"compression or elastic-dominated regime."
        )
        warnings.append(msg)
    if ratio > ratio_max:
        msg = (
            f"{station}/{layer}: S_skv/S_ske = {ratio:.1f}× > {ratio_max:.0f}× — "
            f"inelastic storage implausibly large. Check compressible thickness "
            f"and V(t) computation."
        )
        warnings.append(msg)
    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# Check 4: Virgin exceedance term monotonicity (Gap 4 fix)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_virgin_term(
    V_arr: np.ndarray,
    layer: str,
    station: str = "UNKNOWN",
) -> None:
    """
    V(t) = min(0, cummin(H(t)) - h_c) MUST be monotonically non-increasing.
    It represents permanent inelastic strain memory — it can never recover.

    MODFLOW CSUB documentation: preconsolidation stress can only increase.
    """
    if len(V_arr) < 2:
        return
    diffs = np.diff(V_arr)
    # V should be <= 0 always, and non-increasing (diffs <= 0)
    if np.any(V_arr > 1e-10):
        n_positive = int(np.sum(V_arr > 1e-10))
        raise GuardrailViolation(
            f"{station}/{layer}: V(t) has {n_positive} positive values — "
            f"virgin term must be <= 0 always. Check cummin implementation."
        )
    if np.any(diffs > 1e-10):
        n_increasing = int(np.sum(diffs > 1e-10))
        raise GuardrailViolation(
            f"{station}/{layer}: V(t) increases at {n_increasing} epochs — "
            f"virgin term must be monotonically non-increasing. "
            f"Check: cummin must be computed on LAGGED head H(t-τ), not raw head."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Check 5: Data sufficiency (CLAUDE.md insufficient-data rule)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_data_sufficiency(
    n_total: int,
    n_inelastic: int,
    layer: str,
    station: str = "UNKNOWN",
    min_total: int = 10,
    min_inelastic: int = 10,
) -> list[str]:
    """
    CLAUDE.md: "Fewer than 10 jointly valid points → result undefined."
    Gap 5: n_inelastic < 10 → S_kv unreliable (audit finding).
    """
    warnings: list[str] = []
    if n_total < min_total:
        msg = (
            f"{station}/{layer}: n_total = {n_total} < {min_total} — "
            f"Insufficient data. Result is undefined."
        )
        warnings.append(msg)
    if n_inelastic < min_inelastic:
        msg = (
            f"{station}/{layer}: n_inelastic = {n_inelastic} < {min_inelastic} — "
            f"S_kv unreliable. Too few inelastic epochs for parameter estimation."
        )
        warnings.append(msg)
    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# Check 6: GWL sign convention (CLAUDE.md)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_gwl_sign(
    head_m: np.ndarray,
    layer: str,
    station: str = "UNKNOWN",
) -> None:
    """
    dh_raw = H(t) - H(t_ref) — NEVER negate.
    CLAUDE.md: "dh_raw sign: never negate. Halt if code negates H(t)−H(t_ref)."

    This check verifies that head values are in physically plausible range
    for the Choushui system (roughly -50 to +50 m MSL, but this varies by
    location). The critical check is: are values being negated somewhere?
    """
    # Choushui alluvial fan: head ranges from ~-30 m (deep drawdown) to ~+50 m
    # Values outside [-100, 200] suggest unit error or unintended negation
    if np.any(head_m < -100) or np.any(head_m > 200):
        h_min, h_max = float(np.nanmin(head_m)), float(np.nanmax(head_m))
        raise GuardrailViolation(
            f"{station}/{layer}: head range [{h_min:.1f}, {h_max:.1f}] m MSL "
            f"outside plausible CRAF bounds [-100, 200]. "
            f"Check: is head being negated? Are units in metres MSL?"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Check 7: Preconsolidation head window (Bug F fix — permanent)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_hc_window(
    h_c: float,
    head_pre_ref: np.ndarray,
    layer: str,
    station: str = "UNKNOWN",
    ref_date: str = "2015-01-16",
) -> list[str]:
    """
    Bug F (fixed 2026-06-05): h_c must be computed from raw GWL rows dated
    BEFORE REF_DATE, before zero-referencing. Using post-REF_DATE data pushes
    h_c too low → up to 51% of epochs misclassified as elastic.
    """
    warnings: list[str] = []
    if len(head_pre_ref) < 10:
        warnings.append(
            f"{station}/{layer}: < 10 pre-REF_DATE ({ref_date}) GWL values — "
            f"h_c may be unreliable."
        )
    h_pre_min = float(np.nanmin(head_pre_ref)) if len(head_pre_ref) > 0 else float("nan")
    if not np.isnan(h_pre_min) and h_c > h_pre_min + 1e-6:
        raise GuardrailViolation(
            f"{station}/{layer}: h_c = {h_c:.3f} m > pre-REF_DATE min "
            f"({h_pre_min:.3f} m) — h_c must be the MINIMUM pre-REF_DATE head. "
            f"Bug F regression detected."
        )
    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# Check 8: Tau bounds (CLAUDE.md)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_tau_bounds(
    tau: int,
    tau_max: int = 120,
    layer: str = "",
    station: str = "UNKNOWN",
) -> list[str]:
    """τ must be non-negative integer, ≤ tau_max. τ at boundary → flag."""
    warnings: list[str] = []
    if tau < 0:
        raise GuardrailViolation(
            f"{station}/{layer}: τ = {tau} is NEGATIVE — lag cannot be negative."
        )
    if tau > tau_max:
        raise GuardrailViolation(
            f"{station}/{layer}: τ = {tau} > τ_max = {tau_max} — "
            f"search range exceeded."
        )
    if tau == tau_max:
        warnings.append(
            f"{station}/{layer}: τ = {tau_max} at boundary — "
            f"true lag may be longer. Consider extending τ_max."
        )
    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# Check 9: Clay-layer prediction sanity (Gap 3 fix)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_clay_layer_behavior(
    S_ke: float,
    S_kv: float,
    n_inelastic: int,
    n_total: int,
    layer: str,
    is_clay_dominated: bool,
    station: str = "UNKNOWN",
) -> list[str]:
    """
    Gap 3: Clay layers (aquitards) should be inelastic-dominated.
    Sand layers (aquifers) should be elastic-dominated.

    If a clay layer has S_ke ≈ S_kv, something is wrong (collinearity or
    misclassification). If a sand layer has S_kv >> S_ke, check borehole
    — it may actually be clay-dominated (F4 at TUKU).
    """
    warnings: list[str] = []
    if n_total < 10:
        return warnings

    frac_inelastic = n_inelastic / n_total

    if is_clay_dominated and frac_inelastic < 0.1:
        warnings.append(
            f"{station}/{layer}: CLAY layer with only {frac_inelastic:.0%} "
            f"inelastic epochs — unexpected. Check h_c value and GWL regime."
        )
    if is_clay_dominated and S_kv < 2.0 * S_ke and S_ke > 1e-10:
        warnings.append(
            f"{station}/{layer}: CLAY layer with S_kv/S_ke = {S_kv/S_ke:.1f}× < 2× — "
            f"clay should be inelastic-dominated. Collinearity suspected."
        )

    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# Check 10: R² sanity (CLAUDE.md)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_r2_sanity(
    r2: float,
    layer: str,
    station: str = "UNKNOWN",
) -> list[str]:
    """R² < 0 → model worse than mean. Flag, don't halt."""
    warnings: list[str] = []
    if np.isnan(r2):
        warnings.append(f"{station}/{layer}: R² = NaN — fit did not converge.")
    elif r2 < 0:
        warnings.append(
            f"{station}/{layer}: R² = {r2:.4f} < 0 — model is worse than "
            f"predicting the mean. Predictions are not useful."
        )
    return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# Master validation — run all checks for a single layer
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LayerValidationResult:
    """Aggregate of all guardrail checks for one layer."""
    layer: str
    station: str
    passed: bool
    errors: list[str]      # fatal — must halt
    warnings: list[str]    # non-fatal — flag but may proceed


def validate_layer_params(
    S_ke: float,
    S_kv: float,
    layer: str,
    station: str = "UNKNOWN",
    fan_zone: str = "middle",
    material: Optional[LayerMaterial] = None,
    n_total: int = 0,
    n_inelastic: int = 0,
    r2: float = float("nan"),
    tau: int = 0,
    strict_literature: bool = False,
) -> LayerValidationResult:
    """
    Run ALL guardrail checks for one layer's fitted parameters.

    Returns LayerValidationResult with aggregated errors and warnings.
    The caller decides whether to halt or continue based on .passed.
    """
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Sign constraints (fatal)
    try:
        validate_sign_constraints(S_ke, S_kv, layer, station)
    except GuardrailViolation as e:
        errors.append(str(e))

    # 2. Specific storage conversion + literature bounds
    if material is not None and material.total_m > 0:
        S_ske_m1 = S_ke / (material.total_m * 1000.0) if S_ke > 1e-15 else None
        # For inelastic, use compressible thickness (fine-grained only)
        if material.aquitard_m > 0 and S_kv > 1e-15:
            S_skv_m1 = S_kv / (material.aquitard_m * 1000.0)
        else:
            S_skv_m1 = None
    else:
        S_ske_m1 = None
        S_skv_m1 = None

    # 3. Literature bounds
    with np.errstate(invalid="ignore"):
        lit_warnings = validate_literature_bounds(
            S_ske_m1, S_skv_m1, layer, station, fan_zone, strict=strict_literature
        )
    warnings.extend(lit_warnings)

    # 4. Ratio gate
    ratio_warnings = validate_ratio_gate(S_ske_m1, S_skv_m1, layer, station)
    warnings.extend(ratio_warnings)

    # 5. Data sufficiency
    data_warnings = validate_data_sufficiency(n_total, n_inelastic, layer, station)
    warnings.extend(data_warnings)

    # 6. R² sanity
    r2_warnings = validate_r2_sanity(r2, layer, station)
    warnings.extend(r2_warnings)

    # 7. Tau bounds
    tau_warnings = validate_tau_bounds(tau, layer=layer, station=station)
    warnings.extend(tau_warnings)

    # 8. Clay-layer behavior
    if material is not None:
        clay_warnings = validate_clay_layer_behavior(
            S_ke, S_kv, n_inelastic, n_total, layer,
            material.is_clay_dominated, station,
        )
        warnings.extend(clay_warnings)

    passed = len(errors) == 0
    return LayerValidationResult(
        layer=layer, station=station,
        passed=passed, errors=errors, warnings=warnings,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Quick inline assertions (for use inside data-loading scripts)
# ═══════════════════════════════════════════════════════════════════════════════

def assert_ske_nonnegative(S_ke: float, layer: str = "") -> None:
    """Inline assertion: S_ke >= 0. Use inside fitting loops."""
    if S_ke < 0:
        raise GuardrailViolation(
            f"S_ke = {S_ke:.6f} is NEGATIVE{ ' for ' + layer if layer else ''}."
        )

def assert_skv_ge_ske(S_kv: float, S_ke: float, layer: str = "") -> None:
    """Inline assertion: S_kv >= S_ke."""
    if S_kv < S_ke - 1e-15:
        raise GuardrailViolation(
            f"S_kv ({S_kv:.6f}) < S_ke ({S_ke:.6f})"
            f"{ ' for ' + layer if layer else ''}."
        )

def assert_head_not_negated(head_m: np.ndarray, label: str = "") -> None:
    """Inline assertion: head values are not negated (should be m MSL)."""
    if np.any(head_m < -100):
        raise GuardrailViolation(
            f"Head values < -100 m MSL detected{ ' in ' + label if label else ''}. "
            f"Is head being negated?"
        )

def assert_virgin_monotonic(V_arr: np.ndarray, label: str = "") -> None:
    """Inline assertion: V(t) is monotonically non-increasing."""
    if len(V_arr) > 1 and np.any(np.diff(V_arr) > 1e-10):
        raise GuardrailViolation(
            f"V(t) is not monotonic{ ' in ' + label if label else ''}."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Print-friendly report
# ═══════════════════════════════════════════════════════════════════════════════

def print_validation_report(results: list[LayerValidationResult]) -> None:
    """Print a human-readable validation report for all layers at a station."""
    n_pass = sum(1 for r in results if r.passed)
    n_total = len(results)
    print(f"\n{'='*60}")
    print(f"GUARDRAIL VALIDATION — {results[0].station if results else 'UNKNOWN'}")
    print(f"  {n_pass}/{n_total} layers passed sign-constraint checks")
    print(f"{'='*60}")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"\n  [{status}] {r.layer}")
        for err in r.errors:
            print(f"    ERROR: {err}")
        for warn in r.warnings:
            print(f"    WARN:  {warn}")

    if n_pass == n_total:
        print(f"\n  All {n_total} layers passed physical-law checks.")
    else:
        print(f"\n  {n_total - n_pass} layer(s) FAILED — review errors above.")
    print(f"{'='*60}\n")
