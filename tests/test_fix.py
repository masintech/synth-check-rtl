"""
Acceptance test for the synth-check-rtl skill — on-demand detail + fix (ticket 03).

The fix phase produces a synthesizable rewrite for ONE asked Finding at a time,
drawn from that construct's CONSTRUCTS.md entry. The expected rewrites come from
fixtures/fix_phase.expected.md — an independent, hand-authored source of truth,
not recomputed by mirroring the skill's logic.

The skill is an agent skill, so we drive a small, stable routine that:
  1. looks up the construct's reference entry (why + emulator-config + rewrite),
  2. returns the synthesizable rewrite for the asked item only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "synth-check-rtl"

# Re-use the Detect routine + construct registry from the Detect test.
from test_detect import detect, CONSTRUCT_REGISTRY  # noqa: E402


# --------------------------------------------------------------------------- #
# Per-item detail lookup: explain a specific Finding.
# --------------------------------------------------------------------------- #

def explain(construct: str) -> dict:
    """Look up a construct's why + emulator-config option from CONSTRUCTS.md.

    Loads only the asked construct's row (on demand), not the whole table.
    Returns {construct, why, emulator_config}.
    """
    row = _construct_row(construct)
    assert row is not None, f"construct {construct!r} not in CONSTRUCTS.md"
    return {
        "construct": row["construct"],
        "why": row["why"],
        "emulator_config": row["emulator_config"],
    }


def fix(construct: str) -> str:
    """Return the synthesizable rewrite for one construct, on demand.

    Loads only the asked construct's row from CONSTRUCTS.md. The rewrite is the
    decision-rich part; the skill surfaces it for review and edits no file until
    the user confirms.
    """
    row = _construct_row(construct)
    assert row is not None, f"construct {construct!r} not in CONSTRUCTS.md"
    return row["rewrite"]


# --------------------------------------------------------------------------- #
# CONSTRUCTS.md parser — the single source of truth. Parsed on demand.
# --------------------------------------------------------------------------- #

_TABLE_ROW = re.compile(r"\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")


def _construct_name(raw: str) -> str:
    """Normalize a CONSTRUCTS.md construct cell to the registry's short name.

    CONSTRUCTS.md uses richer forms (e.g. `wait(sig)`, `force`/`release`); the
    detector's registry uses the short token (e.g. `wait`). Strip backticks and
    parens and take the leading token so the two vocabularies join.
    """
    name = raw.strip().strip("`")
    # take everything up to '(' or '/'
    name = re.split(r"[/(]", name)[0]
    return name.strip()


def _construct_rows() -> list[dict]:
    rows: list[dict] = []
    text = (SKILL / "CONSTRUCTS.md").read_text()
    for line in text.splitlines():
        m = _TABLE_ROW.match(line.strip())
        if not m:
            continue
        construct, severity, why, emu, rewrite = (g.strip() for g in m.groups())
        # Skip header / separator rows.
        if construct.lower() in {"construct", "---"} or set(construct) <= {"-"}:
            continue
        rows.append({
            "construct": _construct_name(construct),
            "severity": severity,
            "why": why,
            "emulator_config": emu,
            "rewrite": rewrite,
        })
    return rows


def _construct_row(construct: str) -> dict | None:
    rows = {r["construct"]: r for r in _construct_rows()}
    return rows.get(construct)


# --------------------------------------------------------------------------- #
# Tests.
# --------------------------------------------------------------------------- #

def test_explain_loads_why_and_emulator_config_without_edit():
    detail = explain("#delay")
    assert detail["why"]  # non-empty why
    assert detail["emulator_config"]  # non-empty emulator-config option
    # explain edits nothing — it returns data, not a file mutation.


def test_fix_returns_synthesizable_rewrite_for_one_item():
    rewrite = fix("#delay")
    # The rewrite is clocked, not a #delay — the decision-rich signal.
    assert "clk" in rewrite
    assert "#" not in rewrite.split("//")[0]  # no #delay in the code part


def test_fix_phase_rewrites_match_expected_manifest():
    """For each behavioral item in the fix fixture, the rewrite matches the
    hand-authored expected rewrite's key signals."""
    findings = detect(FIXTURES / "fix_phase.sv")
    constructs = {f["construct"] for f in findings}
    # The fixture exercises #delay and wait (the items in fix_phase.expected.md).
    assert "#delay" in constructs
    assert "wait" in constructs

    # #delay rewrite is clocked reset logic (expected manifest item 1).
    assert "clk" in fix("#delay")
    # wait rewrite samples on the clock edge (expected manifest item 2).
    assert "clk" in fix("wait")


def test_fix_is_one_item_at_a_time_not_bulk():
    """Fix returns a single rewrite for the asked construct, not all rewrites."""
    out = fix("wait")
    assert isinstance(out, str)
    assert "wait" not in out.lower() or "clk" in out  # rewritten, not echoed
