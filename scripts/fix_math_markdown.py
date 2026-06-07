#!/usr/bin/env python3
"""
fix_math_markdown.py — Convert plain-text math notation to LaTeX $...$ / $$...$$
in Markdown files.

Converts:
  - Unicode Greek letters (τ, α, β, Δ, etc.) → LaTeX commands (\\tau, \\alpha, ...)
  - Unicode operators (≥, ≤, ≈, ∈, ×, ·) → LaTeX commands (\\ge, \\le, ...)
  - Scientific E-notation in table rows → $x \\times 10^{y}$
  - Subscript variables (S_ske, h_c, f_bar_k, etc.) → $S_{ske}$, $h_c$, $\\bar{f}_k$
  - Display equations (lines with math) → wrapped in $$...$$
  - Inline math expressions → wrapped in $...$

Safety:
  - Code blocks (fenced ``` and inline `) are never touched.
  - Existing $...$ and $$...$$ blocks are preserved.
  - Subscript conversion uses a whitelist — column names, file paths, and
    station names with underscores are never converted.
  - --dry-run mode shows a unified diff without modifying files.
  - Idempotent: re-running on already-converted files changes nothing.

Usage:
  python scripts/fix_math_markdown.py --dry-run                     # preview all
  python scripts/fix_math_markdown.py --dry-run --priority 1        # preview batch
  python scripts/fix_math_markdown.py --in-place --priority 1       # apply batch
  python scripts/fix_math_markdown.py --dry-run --files a.md b.md   # target files

David Nguyen, InSAR-MLCW project, 2026-06-03.
"""

import argparse
import difflib
import re
import sys
import textwrap
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────────────────

SCRIPTS_REPO = Path("/mnt/hgfs/1000_SCRIPTS/004_Project003/20260427_InSAR_MLCW_v2")
DOCS_REPO   = Path("/mnt/hgfs/112_PROJECT_002")


# ── File registry by priority ──────────────────────────────────────────────────

PRIORITY_FILES = {
    1: [
        SCRIPTS_REPO / "CLAUDE.md",
        SCRIPTS_REPO / "PROGRESS.md",
        SCRIPTS_REPO / "AGENTS.md",
        SCRIPTS_REPO / "GEMINI.md",
        DOCS_REPO / "CLAUDE.md",
        DOCS_REPO / "PROGRESS.md",
        DOCS_REPO / "GEMINI.md",
    ],
    2: [
        SCRIPTS_REPO / "docs" / "tau_search_methodology.md",
        SCRIPTS_REPO / "docs" / "script_inventory.md",
        SCRIPTS_REPO / "docs" / "gwl_to_mlcw_layer_assign_guide.md",
        SCRIPTS_REPO / "docs" / "choushui_skeletal_storage_coeffs.md",
        SCRIPTS_REPO / "docs" / "choushui_background_search.md",
        SCRIPTS_REPO / "docs" / "2STOOL_BATCH_REPORT.md",
        SCRIPTS_REPO / "docs" / "s_ske_skv_tables.md",
        SCRIPTS_REPO / "docs" / "seasonal_harmonic_findings.md",
        DOCS_REPO / "docs" / "20260527_tasks.md",
        DOCS_REPO / "docs" / "file_reorganize.md",
    ],
    3: [
        DOCS_REPO / "discussions" / "discussion_memory.md",
        DOCS_REPO / "discussions" / "discussion_20260528_ihm_theory.md",
        DOCS_REPO / "discussions" / "2026-05-29-ihmf-universal-model-resolution.md",
        DOCS_REPO / "discussions" / "discussion_20260530_ml_brainstorm.md",
        DOCS_REPO / "discussions" / "discussion_20260530_seasonal_ske.md",
        DOCS_REPO / "discussions" / "discussion_20260530_ml_brainstorm_v2_teaching.md",
        DOCS_REPO / "discussions" / "discussion_20260519_v3.md",
        DOCS_REPO / "discussions" / "project_status_20260528.md",
        DOCS_REPO / "discussions" / "discussion_20260601_prediction_pipeline_design.md",
        DOCS_REPO / "discussions" / "discussion_20260601_prediction_pipeline_peer_review.md",
        DOCS_REPO / "discussions" / "discussion_20260601_review_response.md",
        DOCS_REPO / "discussions" / "discussion_20260601_review_response_evaluation.md",
        DOCS_REPO / "discussions" / "discussion_20260524.md",
        DOCS_REPO / "discussions" / "discussion_20260525_inspection.md",
        DOCS_REPO / "discussions" / "discussion_20260528.md",
        DOCS_REPO / "discussions" / "ms2_draft_20260527.md",
    ],
    4: [
        DOCS_REPO / "notes" / "methods" / "machine_learning_methods_review.md",
        DOCS_REPO / "notes" / "literature" / "discussion_literature_novelty_20260517.md",
        DOCS_REPO / "notes" / "presentation" / "MLCW_presentation_revision_summary_20260519.md",
        DOCS_REPO / "notes" / "arx" / "discussion_20260517_arx_results.md",
        DOCS_REPO / "notes" / "per_ring" / "per_ring_reconstruction_comparison_20260519.md",
        DOCS_REPO / "notes" / "cross_station" / "cross_station_summary_visualization_20260519.md",
        DOCS_REPO / "notes" / "prophet" / "discussion_20260517_prophet_tuku.md",
        DOCS_REPO / "notes" / "ablation" / "discussion_20260517_ablation.md",
        DOCS_REPO / "plans" / "2026-05-20-implementation-plan.md",
        DOCS_REPO / "plans" / "2026-05-28-methodology-plan.md",
        DOCS_REPO / "plans" / "2026-05-29-data-analysis-plan.md",
        DOCS_REPO / "plans" / "dataset_summary_corrections.md",
    ],
}


# ── Phase 1: Unicode Greek → LaTeX ─────────────────────────────────────────────

GREEK_MAP = {
    # Lowercase
    "α": r"\alpha",   "β": r"\beta",    "γ": r"\gamma",
    "δ": r"\delta",   "ε": r"\varepsilon", "ζ": r"\zeta",
    "η": r"\eta",     "θ": r"\theta",   "ι": r"\iota",
    "κ": r"\kappa",   "λ": r"\lambda",  "μ": r"\mu",
    "ν": r"\nu",      "ξ": r"\xi",      "π": r"\pi",
    "ρ": r"\rho",     "σ": r"\sigma",   "τ": r"\tau",
    "υ": r"\upsilon", "φ": r"\phi",     "χ": r"\chi",
    "ψ": r"\psi",     "ω": r"\omega",
    # Uppercase
    "Γ": r"\Gamma",   "Δ": r"\Delta",   "Θ": r"\Theta",
    "Λ": r"\Lambda",  "Ξ": r"\Xi",      "Π": r"\Pi",
    "Σ": r"\Sigma",   "Φ": r"\Phi",     "Ψ": r"\Psi",
    "Ω": r"\Omega",
    # Variants (common in this codebase)
    "ϕ": r"\phi",     "φ": r"\phi",
}


def _fix_latex_spacing(text: str) -> str:
    """Ensure space between LaTeX commands and adjacent letters (e.g., \\DeltaH → \\Delta H)."""
    # Match: backslash + word, followed immediately by a letter or digit
    text = re.sub(r"(\\(?:alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|"
                  r"kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|"
                  r"Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Phi|Psi|Omega|"
                  r"ge|le|approx|in|times|cdot|pm|ne|propto|infty|partial))"
                  r"([a-zA-Z0-9])",
                  r"\1 \2", text)
    return text


def convert_greek(text: str) -> str:
    """Replace Unicode Greek letters with LaTeX commands, ensuring spacing."""
    for char, latex in GREEK_MAP.items():
        text = text.replace(char, latex)
    text = _fix_latex_spacing(text)
    return text


# ── Phase 2: Unicode operators → LaTeX ─────────────────────────────────────────

OP_MAP = {
    "≥": r"\ge",
    "≤": r"\le",
    "≈": r"\approx",
    "∈": r"\in",
    "×": r"\times",
    "·": r"\cdot",
    "±": r"\pm",
    "≠": r"\ne",
    "∝": r"\propto",
    "∞": r"\infty",
    "∂": r"\partial",
    # Superscripts
    "²": "^2",
    "³": "^3",
    # Long arrows (only in math context — applied cautiously)
    # "→" is handled contextually
}


def convert_operators(text: str) -> str:
    """Replace Unicode math operators with LaTeX commands, ensuring spacing."""
    for char, latex in OP_MAP.items():
        text = text.replace(char, latex)
    text = _fix_latex_spacing(text)
    return text


# ── Phase 3: Scientific E-notation in table rows ────────────────────────────────

# Matches: 1.42E-05, 7.81E-35, 0.00E+00 (decimal . required to avoid matching
# station codes or non-math tokens)
E_NOTATION_RE = re.compile(r"\b(\d+\.\d+)[Ee]([+-]?\d+)\b")


def convert_scientific_notation(text: str) -> str:
    """Convert E-notation to LaTeX only inside Markdown table rows."""
    lines = text.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            # Inside a table row — convert E-notation cells
            def _replace_e(m: re.Match) -> str:
                mantissa = m.group(1)
                exponent = m.group(2)
                return f"${mantissa} \\times 10^{{{exponent}}}$"
            line = E_NOTATION_RE.sub(_replace_e, line)
        result.append(line)
    return "\n".join(result)


# ── Phase 4: Subscript variables (whitelist-based) ─────────────────────────────

# Whitelist of known math variable names that use underscores.
# These are the ONLY patterns that will be converted.
# Column names (screen_mid_m), file paths, station names (JINHU_XIN) are excluded.
SUBSCRIPT_WHITELIST = {
    # Storage coefficients
    "S_ske", "S_skv", "S_ke", "S_kv", "S_ske_bulk", "S_skv_bulk",
    # Subscripted S with index
    "S_j", "S_k",
    # Head / hydraulic
    "h_c", "h_crit", "H_raw",
    # Delta variables (before greek conversion: Unicode Δ)
    "ΔH_j", "ΔH_k", "Δb_j", "Δd_v", "ΔH", "Δb", "Δd",
    "Δx", "Δy", "Δσ", "Δp",
    # After greek conversion: LaTeX \Delta
    r"\Delta H_j", r"\Delta H_k", r"\Delta b_j", r"\Delta d_v",
    r"\Delta H", r"\Delta b", r"\Delta d",
    r"\Delta x", r"\Delta y",
    # Lag / tau
    r"\tau_opt", r"\tau_max", r"\tau_j", r"\tau_k", "τ_opt", "τ_max", "τ_j", "τ_k",
    # Compaction
    "D_k", "D_j",
    # Response
    "y_k", "y_j", "y_raw", "y_cut",
    # Predictor
    "x_k", "x_j", "x_InSAR",
    # Ratio
    "f_bar", "f_k", "f_bar_k",
    # Elastic/inelastic indicators
    "I_e", "I_i",
    # Model parameters
    r"\beta_k", "β_k",
    # Time references
    "t_ref", "t_max", "t_0",
    # Fitting metrics
    "dh_raw", "dh_lag",
}


# Subscript parts that are variable-name abbreviations (NOT English words).
# These should be rendered as plain math subscripts, not \text{}.
_MATH_SUB_ABBREV = {
    "ske", "skv", "ke", "kv", "j", "k", "c", "e", "i", "v", "x", "y",
    "0", "1", "2", "3", "4", "max", "min", "opt", "ref",
}


def convert_subscripts(text: str) -> str:
    """
    Convert whitelisted subscript variables to $...$ wrapped LaTeX.

    Strategy: scan for word_word patterns, check whitelist, convert.
    Also handles pre-converted Greek (e.g., \\Delta H_j after Phase 1).
    """
    # Build a regex that matches any whitelist entry as a complete token
    # Sort by length (longest first) to avoid partial matches
    sorted_terms = sorted(SUBSCRIPT_WHITELIST, key=len, reverse=True)
    escaped_terms = [re.escape(t) for t in sorted_terms]
    pattern = re.compile(r"\b(" + "|".join(escaped_terms) + r")\b")

    def _replace_subscript(m: re.Match) -> str:
        raw = m.group(1)
        # Convert underscore notation to LaTeX subscript
        parts = raw.split("_")
        base = parts[0]
        sub_parts = parts[1:]

        # Build LaTeX: base_{sub1,sub2,...}
        # Use \text{} only for English words (like "raw", "insar", "mlcw"),
        # not for variable-name abbreviations (ske, skv, ke, kv, opt, max)
        sub_latex_parts = []
        for sp in sub_parts:
            if sp in _MATH_SUB_ABBREV:
                sub_latex_parts.append(sp)
            elif sp.isalpha() and sp.islower() and len(sp) > 1:
                sub_latex_parts.append(r"\text{" + sp + "}")
            else:
                sub_latex_parts.append(sp)

        sub_joined = ",".join(sub_latex_parts) if len(sub_latex_parts) > 1 else sub_latex_parts[0]
        return f"${base}_{{{sub_joined}}}$"

    return pattern.sub(_replace_subscript, text)


# ── Phase 5: Math wrapping (display equations + inline math) ───────────────────

# Set of LaTeX command names that signal math context
_BARE_LATEX_CMDS = [
    "tau", "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon",
    "zeta", "eta", "theta", "kappa", "lambda", "mu", "nu", "xi", "pi",
    "rho", "sigma", "upsilon", "phi", "chi", "psi", "omega",
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega",
    "ge", "le", "approx", "in", "times", "cdot", "pm",
]


def _wrap_bare_latex_inline(text: str) -> str:
    """
    Wrap bare LaTeX commands (not already inside $...$) in inline math delimiters.
    Uses a simple approach: find each \\cmd and wrap it if not already in math mode.
    """
    # Strategy: process character by character tracking $ state.
    # Simpler: do a two-pass approach where we first protect $...$ regions,
    # then wrap bare commands, then restore.

    # Find all $...$ regions (already-math) and protect them
    protected_regions = []
    def _protect_existing(m: re.Match) -> str:
        pid = f"[[MATHREGION_{len(protected_regions)}]]"
        protected_regions.append(m.group(0))
        return pid

    temp = re.sub(r"\$[^$\n]+\$", _protect_existing, text)
    temp = re.sub(r"\$\$[\s\S]*?\$\$", _protect_existing, temp)

    # Now wrap each bare LaTeX command in $...$
    for cmd in _BARE_LATEX_CMDS:
        # Build regex pattern that matches literal \cmd (not preceded by $)
        # Use \\\\ to get literal backslash in the regex pattern
        pattern = r"(?<!\$)\\" + cmd
        replacement = "$\\" + cmd + "$"
        temp = re.sub(pattern, lambda m, r=replacement: r, temp)

    # Restore protected regions
    for i, region in enumerate(protected_regions):
        temp = temp.replace(f"[[MATHREGION_{i}]]", region)

    return temp

# Variables that signal math context when found with = or ≈
MATH_CONTEXT_SIGNALS = [
    r"\tau", r"\Delta", r"\alpha", r"\beta", r"\Sigma",
    r"\ge", r"\le", r"\approx", r"\in", r"\cdot", r"\times",
    "S_{ske}", "S_{skv}", "S_{ke}", "S_{kv}",
    "h_c", "f_k", "b_k",
]


def _is_display_equation(line: str) -> bool:
    """Check if a line is a display math equation (should use $$...$$)."""
    stripped = line.strip()
    # Skip empty lines, headings, table rows, list markers
    if not stripped:
        return False
    if stripped.startswith("#"):
        return False
    if stripped.startswith("|"):
        return False
    if re.match(r"^[-*>]\s", stripped):
        return False

    # Must contain an equation sign
    has_eq_sign = "=" in stripped or "\\approx" in stripped or "\\ge" in stripped or "\\le" in stripped
    if not has_eq_sign:
        return False

    # Count math signals vs total characters
    math_count = sum(stripped.count(s) for s in MATH_CONTEXT_SIGNALS)
    total = len(stripped.replace(" ", ""))
    if total == 0:
        return False

    # Line is display math if >15% of non-space chars are math signals
    return math_count > 0 and (math_count / total) > 0.15


def _merge_adjacent_math(text: str) -> str:
    """
    Surgically merge fragmented $...$ blocks without absorbing text.
    Only merges well-defined math patterns, never touches parenthetical text.

    Patterns merged:
      $\sigma$'(t)   → $\sigma'(t)$     (prime + function args)
      $D_{k}$(t)     → $D_k(t)$         (subscript + function args)
      $\Delta$ H     → $\Delta H$       (trailing single math variable)
      −$\rho$_w      → $-\rho_w$        (leading minus)
      $\Delta$$\sigma$ → $\Delta\sigma$  (adjacent blocks)
    """
    # Pass 1: Absorb prime (') after $...$
    # $\sigma$' → $\sigma'$
    text = re.sub(r"\$([^$]+)\$(')", r"$\1\2$", text)

    # Pass 2: Absorb function arguments (t), (x), (i), (k), (j) after $...$
    # $D_{k}$(t) → $D_k(t)$  BUT NOT $\sigma$(Pa) — only (single-letter)
    text = re.sub(r"\$([^$]+)\$\(([a-z0-9])\)", r"$\1(\2)$", text)

    # Pass 3: Merge adjacent $A$$B$ (no space) → $AB$
    for _ in range(3):
        new_text = re.sub(r"\$([^$]+)\$\$([^$]+)\$", r"$\1\2$", text)
        if new_text == text:
            break
        text = new_text

    # Pass 4: Absorb trailing single lowercase letter (math variable) after $...$ + space
    # $\Delta$ H → $\Delta H$  (only when H is followed by space/punctuation, not by a letter)
    text = re.sub(r"\$([^$]+)\$\s+([a-z])(?=\s|[\,\.\;\:\!\?\)\]\'\"]|$)", r"$\1 \2$", text)

    # Pass 5: Absorb leading minus sign before $...$
    # −$\rho$_w → $-\rho_w$
    text = re.sub(r"([−])\$([^$]+)\$", r"$\1\2$", text)

    # Pass 6: Clean up: merge $A$ $B$ (space-separated adjacent blocks)
    text = re.sub(r"\$([^$]+)\$\s+\$([^$]+)\$", r"$\1 \2$", text)

    # Pass 7: Absorb trailing bare subscript after $...$  (e.g., $\rho$_w → $\rho_w$)
    # Matches _singlechar or _{multi} after a closing $
    text = re.sub(r"\$([^$]+)\$(_[a-zA-Z0-9]+)", r"$\1\2$", text)
    text = re.sub(r"\$([^$]+)\$(_{[^}]+})", r"$\1\2$", text)

    # Pass 8: Clean empty double-dollar blocks
    text = re.sub(r"\$\$", "", text)

    return text


def wrap_math(text: str) -> str:
    """
    Wrap display equations in $$...$$ and inline math tokens in $...$.

    This handles the text AFTER Phases 1-4 have run, so Greek letters are
    already LaTeX commands and subscripts are already $...$ wrapped.
    """
    # Step A: Wrap bare LaTeX commands inline (two passes for idempotency)
    text = _wrap_bare_latex_inline(text)
    text = _wrap_bare_latex_inline(text)

    # Step A2: Surgical merge of fragmented math
    # Only merge well-defined patterns — never absorb text parentheticals
    text = _merge_adjacent_math(text)

    # Step B: Wrap display equations
    lines = text.split("\n")
    result = []
    for line in lines:
        # Skip already-wrapped display math
        if line.strip().startswith("$$") and line.strip().endswith("$$"):
            result.append(line)
            continue

        if _is_display_equation(line):
            stripped = line.strip()
            leading = line[:len(line) - len(line.lstrip())]
            # Remove trailing period from math block when it's clearly sentence-ending
            math_content = stripped
            trailing = ""
            if math_content.endswith(".") and math_content.count(".") == 1:
                math_content = math_content[:-1]
                trailing = "."

            result.append(f"{leading}$${math_content}$${trailing}")
        else:
            result.append(line)

    return "\n".join(result)


# ── Protection layer: code blocks & existing LaTeX ─────────────────────────────

def protect_code_blocks(text: str) -> tuple[str, dict[str, str]]:
    """
    Replace code blocks (fenced + inline) and existing LaTeX with placeholders.
    Returns (protected_text, placeholder_map).
    """
    placeholders = {}
    counter = [0]  # mutable counter

    def _next_id(kind: str) -> str:
        counter[0] += 1
        pid = f"[[PROTECTED_{kind}_{counter[0]}]]"
        return pid

    # 1. Fenced code blocks (``` ... ```)
    def _protect_fenced(m: re.Match) -> str:
        pid = _next_id("FENCE")
        placeholders[pid] = m.group(0)
        return pid

    text = re.sub(r"```[\s\S]*?```", _protect_fenced, text)

    # 2. Existing $$...$$ display math
    def _protect_display(m: re.Match) -> str:
        pid = _next_id("DISPLAY")
        placeholders[pid] = m.group(0)
        return pid

    text = re.sub(r"\$\$[\s\S]*?\$\$", _protect_display, text)

    # 3. Existing $...$ inline math (but NOT $ used as dollar sign)
    def _protect_inline(m: re.Match) -> str:
        pid = _next_id("INLINE")
        placeholders[pid] = m.group(0)
        return pid

    # Match $...$ where content looks like math (contains LaTeX commands or math chars)
    text = re.sub(r"(?<!\\)\$[^$\n]+?(?<!\\)\$", _protect_inline, text)

    # 4. Inline code (`...`)
    def _protect_inline_code(m: re.Match) -> str:
        pid = _next_id("CODE")
        placeholders[pid] = m.group(0)
        return pid

    text = re.sub(r"`[^`\n]+`", _protect_inline_code, text)

    return text, placeholders


def restore_code_blocks(text: str, placeholders: dict[str, str]) -> str:
    """Restore protected blocks from placeholders."""
    for pid, original in placeholders.items():
        text = text.replace(pid, original)
    return text


# ── Main processing pipeline ────────────────────────────────────────────────────

def process_text(text: str) -> str:
    """Apply all conversion phases to a markdown text block."""
    # Phase 1: Unicode Greek → LaTeX
    text = convert_greek(text)
    # Phase 2: Unicode operators → LaTeX
    text = convert_operators(text)
    # Phase 3: E-notation in tables
    text = convert_scientific_notation(text)
    # Phase 4: Subscript variables (whitelist)
    text = convert_subscripts(text)
    # Phase 5: Math wrapping
    text = wrap_math(text)
    return text


# Set of valid LaTeX commands used in this codebase
_VALID_LATEX_COMMANDS = {
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota",
    "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma", "tau", "upsilon",
    "phi", "chi", "psi", "omega",
    "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Phi", "Psi", "Omega",
    "ge", "le", "approx", "in", "times", "cdot", "pm", "ne", "propto", "infty", "partial",
    "text", "mathbf", "mathrm", "sum", "int", "frac", "sqrt", "left", "right",
    "bar", "hat", "tilde", "dot", "ddot", "text", "max", "min", "text", "opt",
    "begin", "end", "hline",
}


def final_sanity_checks(text: str) -> list[str]:
    """Run sanity checks on the processed text. Returns list of warnings."""
    warnings = []

    # Check for orphaned/unescaped $ signs
    dollar_count = text.count("$")
    if dollar_count % 2 != 0:
        warnings.append(f"Odd number of $ signs ({dollar_count}) — possible orphaned delimiter")

    # Check for stray placeholder patterns
    if "[[PROTECTED_" in text:
        count = text.count("[[PROTECTED_")
        warnings.append(f"{count} unresolved protection placeholders remain")

    # Check for unknown LaTeX commands (backslash followed by non-standard word)
    for m in re.finditer(r"\\([a-zA-Z]+)", text):
        cmd = m.group(1)
        if cmd not in _VALID_LATEX_COMMANDS and "PROTECTED" not in cmd:
            warnings.append(f"Unknown LaTeX command '\\{cmd}' — verify correctness")

    return warnings


def process_file(filepath: Path, dry_run: bool = False, backup_ext: str | None = None) -> bool:
    """
    Process a single markdown file.
    Returns True if changes were made, False otherwise.
    """
    if not filepath.exists():
        print(f"SKIP: {filepath} — file not found", file=sys.stderr)
        return False

    original = filepath.read_text(encoding="utf-8")

    # Step 1: Protect code blocks and existing LaTeX
    protected, placeholders = protect_code_blocks(original)

    # Step 2: Apply conversion phases
    converted = process_text(protected)

    # Step 3: Restore protected blocks
    result = restore_code_blocks(converted, placeholders)

    # Step 4: Sanity checks
    warnings = final_sanity_checks(result)
    if warnings:
        for w in warnings:
            print(f"WARNING [{filepath.name}]: {w}", file=sys.stderr)

    # Check if anything changed
    if result == original:
        print(f"UNCHANGED: {filepath}")
        return False

    if dry_run:
        # Print unified diff
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            result.splitlines(keepends=True),
            fromfile=str(filepath),
            tofile=str(filepath) + " (converted)",
        )
        sys.stdout.writelines(diff)
        print(f"\n--- DRY-RUN: {filepath} ({_count_changes(original, result)} changes) ---\n")
        return True

    # In-place mode
    if backup_ext:
        backup_path = filepath.with_suffix(filepath.suffix + backup_ext)
        filepath.rename(backup_path)
        print(f"BACKUP: {backup_path}")

    filepath.write_text(result, encoding="utf-8")
    print(f"CONVERTED: {filepath} ({_count_changes(original, result)} changes)")
    return True


def _count_changes(original: str, result: str) -> str:
    """Count rough number of changes between original and result."""
    orig_lines = original.splitlines()
    res_lines = result.splitlines()
    changed = sum(1 for o, r in zip(orig_lines, res_lines) if o != r)
    changed += abs(len(orig_lines) - len(res_lines))
    return f"~{changed} lines"


# ── CLI ─────────────────────────────────────────────────────────────────────────

def _resolve_files(priority: int | None, files: list[str] | None) -> list[Path]:
    """Resolve which files to process based on priority or explicit file list."""
    if files:
        return [Path(f).resolve() for f in files]
    if priority is not None:
        if priority not in PRIORITY_FILES:
            print(f"ERROR: Unknown priority {priority}. Valid: {list(PRIORITY_FILES.keys())}",
                  file=sys.stderr)
            sys.exit(1)
        existing = [f for f in PRIORITY_FILES[priority] if f.exists()]
        missing = [f for f in PRIORITY_FILES[priority] if not f.exists()]
        if missing:
            print(f"NOTE: {len(missing)} file(s) in priority {priority} not found (skipping):",
                  file=sys.stderr)
            for m in missing:
                print(f"  - {m}", file=sys.stderr)
        return existing
    # No priority, no files → process all priorities
    all_files = []
    for p in sorted(PRIORITY_FILES.keys()):
        all_files.extend(f for f in PRIORITY_FILES[p] if f.exists())
    return all_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert plain-text math to LaTeX $...$ / $$...$$ in Markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              %(prog)s --dry-run --priority 1       Preview Priority 1 changes
              %(prog)s --in-place --priority 1       Apply Priority 1 changes
              %(prog)s --dry-run --files a.md b.md   Preview specific files
              %(prog)s --in-place --backup .bak      Apply all with backup
        """),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="Preview changes as unified diff (no files modified)")
    mode.add_argument("--in-place", action="store_true",
                      help="Apply changes directly to files")

    parser.add_argument("--priority", type=int, choices=[1, 2, 3, 4],
                        help="Process a specific priority batch (1-4)")
    parser.add_argument("--files", nargs="+", metavar="FILE",
                        help="Process specific markdown files")
    parser.add_argument("--backup", type=str, default=None, metavar="EXT",
                        help="Backup extension for --in-place mode (e.g., '.bak')")

    args = parser.parse_args()

    files = _resolve_files(args.priority, args.files)

    if not files:
        print("No files to process. Use --priority or --files.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(files)} file(s)...")
    if args.dry_run:
        print("MODE: dry-run (no files will be modified)\n")

    changed_count = 0
    unchanged_count = 0

    for fp in files:
        changed = process_file(fp, dry_run=args.dry_run, backup_ext=args.backup)
        if changed:
            changed_count += 1
        else:
            unchanged_count += 1

    print(f"\nDone. {changed_count} file(s) changed, {unchanged_count} file(s) unchanged.")


if __name__ == "__main__":
    main()
