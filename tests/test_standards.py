"""
Standards-conformance test for synth-check-rtl against writing-great-skills (ticket 05).

Enforces the levers from the writing-great-skills glossary on the skill files,
as a structural guard:
- Progressive disclosure: the construct table is disclosed behind a context
  pointer, not inline in SKILL.md.
- Single source of truth: each construct's verdict/rewrite lives in one row in
  CONSTRUCTS.md (each construct name appears in at most one table row).
- Completion criteria: SKILL.md steps carry checkable, exhaustive criteria, not
  vague "be thorough" no-ops.
- No negation as steering: SKILL.md phrases behavior positively; prohibitions
  appear only as hard guardrails paired with the positive target.
- Leading words as tokens: behavioral / synthesizable / bring-up / Finding
  recur in SKILL.md.
- Co-location: each construct's severity, why, emulator-config, and rewrite
  sit in one row.
- No CONTEXT.md / ADR created for this feature.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "synth-check-rtl" / "SKILL.md"
CONSTRUCTS = REPO / ".claude" / "skills" / "synth-check-rtl" / "CONSTRUCTS.md"


def test_construct_table_is_progressively_disclosed():
    """The construct table is NOT inlined in SKILL.md — it sits behind a pointer."""
    skill = SKILL.read_text()
    # SKILL.md must point to CONSTRUCTS.md rather than embed construct rows.
    assert "CONSTRUCTS.md" in skill
    # No table rows carrying verdicts (error/warning + a rewrite) inline.
    inline_rows = [
        l for l in skill.splitlines()
        if l.strip().startswith("|") and re.search(r"\b(error|warning)\b", l)
    ]
    assert inline_rows == [], "SKILL.md inlines construct verdicts — disclose to CONSTRUCTS.md"


def test_each_construct_has_single_source_of_truth():
    """Each construct name appears in at most one CONSTRUCTS.md table row."""
    text = CONSTRUCTS.read_text()
    names: list[str] = []
    for line in text.splitlines():
        m = re.match(r"\|\s*`?([^|`]+?)`?\s*\|", line.strip())
        if not m:
            continue
        first = m.group(1).strip()
        if first.lower() in {"construct", "---"} or set(first) <= {"-"}:
            continue
        names.append(first)
    # Build the short-token key the detector joins on, then assert uniqueness.
    keys = [re.split(r"[/(]", n)[0].strip() for n in names]
    keys = [k for k in keys if k]
    dups = {k for k in keys if keys.count(k) > 1}
    assert not dups, f"construct(s) have more than one row in CONSTRUCTS.md: {dups}"


def test_steps_have_checkable_completion_criteria():
    """Each step's completion criterion is checkable, not a vague no-op."""
    skill = SKILL.read_text()
    criteria = re.findall(r"\*\*Completion criterion[^:]*:\*\*\s*(.+?)(?=\n\n|\n###|\Z)",
                          skill, re.DOTALL)
    assert criteria, "no completion criteria found in SKILL.md"
    vague = {"be thorough", "be careful", "be comprehensive", "do your best"}
    for c in criteria:
        low = c.lower()
        assert not any(v in low for v in vague), f"vague criterion: {c!r}"


def test_no_negation_as_steering():
    """SKILL.md avoids negation as steering; prohibitions pair with positives."""
    skill = SKILL.read_text()
    # Raw "do not X" used as steering would be a negation smell.
    bare_negations = re.findall(r"(?<!\w)(?:do not|don't)\s+\w+", skill, re.IGNORECASE)
    # A few hard guardrails are fine; flag only if negations dominate the body.
    assert len(bare_negations) <= 3, f"negation used as steering: {bare_negations}"


def test_leading_words_recur_as_tokens():
    """Leading words recur in SKILL.md."""
    skill = SKILL.read_text().lower()
    for word in ("behavioral", "synthesizable", "bring-up", "finding"):
        assert skill.count(word) >= 2, f"leading word {word!r} underused"


def test_constructs_co_locate_verdict_and_remedy():
    """Each CONSTRUCTS.md row co-locates severity, why, emulator-config, rewrite."""
    text = CONSTRUCTS.read_text()
    rows = [l for l in text.splitlines()
            if l.strip().startswith("|") and re.search(r"\b(error|warning|note)\b", l)
            and "severity" not in l.lower()]
    assert rows, "no construct rows found"
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        # construct | severity | why | emulator-config | rewrite -> 5 cells
        assert len(cells) >= 5, f"row missing a cell: {row!r}"
        assert all(cells[i] for i in (1, 2, 3, 4)), f"row has an empty cell: {row!r}"


def test_no_context_md_or_adr_created_for_feature():
    """The skill creates no CONTEXT.md / ADR for itself."""
    assert not (REPO / "CONTEXT.md").exists(), "skill should not create CONTEXT.md"
    adr_dir = REPO / "docs" / "adr"
    if adr_dir.exists():
        adrs = [p for p in adr_dir.iterdir() if p.suffix == ".md"]
        assert not adrs, f"skill created ADR(s): {adrs}"
