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

# Section and subsection numbers such as 3.4.2 or 4.1 are cross-reference
# targets written out in prose, not measured quantities, so the precision rule
# does not apply to them. Stripped before the precision test runs.
SECTION_NUMBER = re.compile(r"\b\d+\.\d+(?:\.\d+)*\b(?=[\s,.)]|$)")

# Values that legitimately carry other precision. Keep this list short; every
# entry is a place where the three-decimal rule is deliberately not applied.
PRECISION_ALLOWLIST = {
    "1.12",  # LaTeX arraystretch argument
    "1.15",  # LaTeX arraystretch argument
    "0.98",  # includegraphics width fraction
}


def looks_like_section_number(text: str, match: re.Match) -> bool:
    """Return True when a decimal is part of a section number, not a measurement."""
    for candidate in SECTION_NUMBER.finditer(text):
        if candidate.start() <= match.start() and match.end() <= candidate.end():
            # A bare "4.1" is ambiguous, so require a section cue nearby.
            window = text[max(0, candidate.start() - 40) : candidate.start()]
            if re.search(r"(?i)\b(?:section|subsection|methods|figure|table)\b", window):
                return True
            # Three-part numbers such as 3.4.2 are never measurements here.
            if candidate.group(0).count(".") >= 2:
                return True
    return False


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
            if match.group(0) in PRECISION_ALLOWLIST:
                continue
            if looks_like_section_number(text, match):
                continue
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
