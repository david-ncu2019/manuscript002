"""Check the Results and Discussion section against the manuscript's style rules.

Written because an earlier shell check was unreliable. Filtering out any LINE
containing "tab:" or "subsec:" also filtered out real prose violations that
happened to share a line with a cross-reference, and reported a clean result
three times while two prose colons were present. This script strips the macro
arguments themselves rather than discarding whole lines.

Run with, from the worktree root:

    $env:PYTHONPATH=""; conda run -n fafalab2 python scripts/check_section4_style.py

Exits non-zero if any check fails, so it can gate a commit.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parent.parent
TARGET = WORKTREE / "sections" / "results_discussion_draft.tex"

# Macros whose arguments legitimately contain colons or internal-looking tokens.
MACRO_WITH_ARGUMENT = re.compile(
    r"\\(?:C?ref|label|citep|citet|cite|texttt|input)\{[^}]*\}"
)

BANNED_WORDS = re.compile(
    r"\b(?:nowcast\w*|harmoniz\w*|reconcil\w*|protocol\w*|yield\w*|secular\w*"
    r"|suppl(?:y|ied|ies|ying)|feature\s+matrix)\b",
    re.IGNORECASE,
)

FIRST_PERSON = re.compile(r"\b(?:we|our|ours|us|I)\b")

INTERNAL_LABELS = re.compile(r"\bP0\b|Level\s*1a|level1[abc]\b", re.IGNORECASE)

# A decimal that shows one, two, four or more places instead of exactly three.
WRONG_PRECISION = re.compile(r"\b\d+\.(?:\d{1,2}|\d{4,})\b")

# Values that legitimately carry other precision: design constants and ratios
# quoted from the methods section or from a cited source.
PRECISION_ALLOWLIST = {
    "1.4",   # approximate pooled range in the old 4.2 prose
    "1.5",
    "2.4",
    "2.7",
    "2.65",  # endpoint MAE quoted at source precision in the old 4.2 prose
    "4.75",
    "0.94",
    "1.06",
    "2.55",
    "4.76",
    "1.02",
    "1.33",
    "1.47",
    "2.46",
    "1.52",
    "2.74",
    "17.0",  # fit-once means quoted at source precision in the old 4.3 prose
    "8.3",
    "4.3",
    "53.5",
    "0.1",
    "1.12",  # LaTeX arraystretch values
    "1.15",
    "0.98",  # includegraphics width fraction
}


def prose_lines() -> list[tuple[int, str]]:
    """Return numbered lines with comments dropped and macro arguments stripped."""
    lines = []
    for number, raw in enumerate(TARGET.read_text(encoding="utf-8").splitlines(), 1):
        if raw.lstrip().startswith("%"):
            continue
        lines.append((number, MACRO_WITH_ARGUMENT.sub("", raw)))
    return lines


def report(name: str, hits: list[tuple[int, str]]) -> bool:
    """Print a pass or fail line for one check. Return True when it passed."""
    if not hits:
        print(f"  PASS  {name}")
        return True
    print(f"  FAIL  {name} ({len(hits)} hit(s))")
    for number, detail in hits[:8]:
        print(f"          line {number}: {detail}")
    return False


def main() -> None:
    lines = prose_lines()
    passed = []

    passed.append(
        report(
            "no prose colon outside macro arguments",
            [(n, text.strip()[:90]) for n, text in lines if ":" in text],
        )
    )
    passed.append(
        report(
            "no banned vocabulary",
            [
                (n, match.group(0))
                for n, text in lines
                if (match := BANNED_WORDS.search(text))
            ],
        )
    )
    passed.append(
        report(
            "no first-person pronoun",
            [
                (n, match.group(0))
                for n, text in lines
                if (match := FIRST_PERSON.search(text))
            ],
        )
    )
    passed.append(
        report(
            "no internal profile or level label",
            [
                (n, match.group(0))
                for n, text in lines
                if (match := INTERNAL_LABELS.search(text))
            ],
        )
    )

    precision_hits = []
    for number, text in lines:
        for match in WRONG_PRECISION.finditer(text):
            if match.group(0) not in PRECISION_ALLOWLIST:
                precision_hits.append((number, match.group(0)))
    passed.append(
        report("every decimal at three places or allowlisted", precision_hits)
    )

    print()
    if all(passed):
        print("All style checks passed.")
        sys.exit(0)
    print("Style checks FAILED.")
    sys.exit(1)


if __name__ == "__main__":
    main()
