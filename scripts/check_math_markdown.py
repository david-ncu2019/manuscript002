#!/usr/bin/env python3
"""
check_math_markdown.py — Detect plain-text math symbols in Markdown files.

Scans .md files for bare Unicode Greek letters and math-context underscores
that should be wrapped in $...$ LaTeX delimiters.

Usage:
  python scripts/check_math_markdown.py                  # Check all tracked .md files
  python scripts/check_math_markdown.py --files a.md b.md # Check specific files
  python scripts/check_math_markdown.py --staged           # Check git-staged .md files

Exit code 0 = clean, 1 = violations found.

David Nguyen, InSAR-MLCW project, 2026-06-03.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


# Unicode Greek letters that should always be in $...$
BARE_GREEK = re.compile(r"[Α-ωϰ-Ͽ]")  # Greek and Coptic block

# Math operators that should be in $...$
BARE_OPERATORS = re.compile(r"[≥≤≈∈×·±≠∝∞∂]")

# Subscript patterns likely to be math (word_word where first part is short)
# These are suspicious when they appear outside code blocks and existing $...$
MATH_SUBSCRIPT_RE = re.compile(
    r"\b(S_ske|S_skv|S_ke|S_kv|h_c|dh_raw|dh_lag|"
    r"tau_opt|tau_max|tau_j|tau_k|"
    r"f_bar|f_bar_k|f_k|b_k|I_e|I_i|"
    r"t_ref|t_max|y_raw|y_cut|x_InSAR|"
    r"Delta_H_j|Delta_H_k|Delta_b_j|Delta_d_v)\b"
)


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks and inline code from text before checking."""
    # Fenced code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Inline code
    text = re.sub(r"`[^`\n]+`", "", text)
    # Existing LaTeX math
    text = re.sub(r"\$\$[\s\S]*?\$\$", "", text)
    text = re.sub(r"\$[^$\n]+\$", "", text)
    return text


def check_file(filepath: Path) -> list[str]:
    """Check a single file. Returns list of violation messages."""
    violations = []
    try:
        raw = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Cannot read {filepath}: {e}"]

    # Strip protected zones
    clean = _strip_code_blocks(raw)

    lines = clean.split("\n")
    for lineno, line in enumerate(lines, 1):
        # Check bare Greek
        greek_matches = BARE_GREEK.findall(line)
        for gm in greek_matches:
            violations.append(
                f"{filepath}:{lineno}: bare Unicode Greek '{gm}' — wrap in $...$"
            )

        # Check bare operators
        op_matches = BARE_OPERATORS.findall(line)
        for om in op_matches:
            violations.append(
                f"{filepath}:{lineno}: bare Unicode operator '{om}' — use LaTeX command in $...$"
            )

        # Check subscript patterns
        sub_matches = MATH_SUBSCRIPT_RE.findall(line)
        for sm in sub_matches:
            violations.append(
                f"{filepath}:{lineno}: bare math subscript '{sm}' — use $...$ with LaTeX"
            )

    return violations


def get_staged_md_files() -> list[Path]:
    """Get list of staged .md files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True, text=True, check=True,
        )
        return [Path(f) for f in result.stdout.strip().split("\n") if f.endswith(".md")]
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: Not a git repository or git not available.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect plain-text math symbols in Markdown files."
    )
    parser.add_argument("--files", nargs="+", metavar="FILE",
                        help="Check specific markdown files")
    parser.add_argument("--staged", action="store_true",
                        help="Check git-staged .md files (for pre-commit hook)")
    args = parser.parse_args()

    if args.staged:
        files = get_staged_md_files()
    elif args.files:
        files = [Path(f).resolve() for f in args.files]
    else:
        # Default: find all .md files in repo (excluding trash, .firecrawl, data/gps)
        repo_root = Path(__file__).resolve().parent.parent
        files = [
            p for p in repo_root.rglob("*.md")
            if "trash" not in str(p)
            and ".firecrawl" not in str(p)
            and "data/gps" not in str(p)
        ]

    if not files:
        print("No markdown files to check.")
        sys.exit(0)

    all_violations = []
    for fp in files:
        violations = check_file(fp)
        all_violations.extend(violations)

    if all_violations:
        print(f"Found {len(all_violations)} math notation violation(s):\n")
        for v in all_violations:
            print(f"  {v}")
        print(f"\nRun: python scripts/fix_math_markdown.py --files <file> --in-place")
        sys.exit(1)
    else:
        print(f"OK: {len(files)} file(s) checked, no plain-text math found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
