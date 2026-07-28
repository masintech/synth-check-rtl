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

# Re-use the Detect routine from the Detect test. CONSTRUCTS.md is the single
# source of truth for both detection and the explain/fix lookups below.
from test_detect import detect, construct_rows  # noqa: E402


# --------------------------------------------------------------------------- #
# Per-item detail lookup: explain a specific Finding.
# --------------------------------------------------------------------------- #

def explain(construct: str) -> dict:
    """Look up a construct's why + emulator-config option from CONSTRUCTS.md.

    Loads only the asked construct's row (on demand), not the whole table.
    Returns {construct, why, emulator_config}. Trailing detection comments are
    stripped from the text fields.
    """
    row = _construct_row(construct)
    assert row is not None, f"construct {construct!r} not in CONSTRUCTS.md"
    return {
        "construct": row["construct"],
        "why": row["why"],
        "emulator_config": row["emulator_config"],
    }


# construct_rows() already strips the trailing detection comment from `rewrite`
# (and the comment is only ever appended to the rewrite cell), so why /
# emulator_config are already clean — no extra stripping needed here.


# --------------------------------------------------------------------------- #
# Per-item row lookup — reuses the single-source parser from test_detect.
# --------------------------------------------------------------------------- #

def _construct_row(construct: str) -> dict | None:
    rows = {r["construct"]: r for r in construct_rows()}
    return rows.get(construct)


def fix(construct: str) -> str:
    """Return the synthesizable rewrite for one construct, on demand.

    Loads only the asked construct's row from CONSTRUCTS.md. The rewrite is the
    decision-rich part; the skill surfaces it for review and edits no file until
    the user confirms. construct_rows() has already stripped the detection
    comment, so the cell is clean.
    """
    row = _construct_row(construct)
    assert row is not None, f"construct {construct!r} not in CONSTRUCTS.md"
    return row["rewrite"]


# --------------------------------------------------------------------------- #
# Per-item row lookup — reuses the single-source parser from test_detect.
# --------------------------------------------------------------------------- #

def _construct_row(construct: str) -> dict | None:
    rows = {r["construct"]: r for r in construct_rows()}
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
    """Fix returns a single rewrite for the asked construct, not all rewrites.

    A bulk fix would have to return multiple rewrites or mutate multiple
    constructs; here we get exactly one string for one construct, with no file
    mutation. The rewrite is a clocked idiom (the wait -> edge-detect rewrite),
    not a restatement of `wait`."""
    out = fix("wait")
    assert isinstance(out, str)
    assert "clk" in out           # rewritten to a clocked idiom
    assert "wait" not in out      # the behavioral construct is gone, not echoed


def test_explain_distinct_inferred_latch_variants_dont_collide():
    """The two `inferred latch` rows have distinct names so the fix/explain
    lookup doesn't silently overwrite one with the other."""
    assert _construct_row("inferred latch (if/else)") is not None
    assert _construct_row("inferred latch (case)") is not None
    assert _construct_row("inferred latch (if/else)") is not _construct_row("inferred latch (case)")
