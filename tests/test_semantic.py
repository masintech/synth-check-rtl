"""
Acceptance test for the synth-check-rtl skill — semantic reasoning (ticket 08).

The semantic constructs (CDC, logic on reset, multi-edge sensitivity, etc.) are
NOT pattern-detectable: a `posedge clk or negedge rst` is a valid async reset,
while `posedge a or posedge b` is a dual-clock hazard. Distinguishing them needs
reasoning against SYNTH-RULES.md, so detection here is model-dependent and its
accuracy is probabilistic.

This test does NOT run the agent. It enforces the conditions that make honest
model-dependent verification possible:

  1. The semantic constructs are declared in CONSTRUCTS.md with a `semantic:TAG`
     (and no pattern), so they are excluded from the deterministic detector and
     handed to the reasoning pass — never silently pattern-matched.
  2. The valid-form guard is in place: the deterministic detector must NOT flag
     the valid async reset in the semantic fixture (it has no pattern for it, so
     a real async reset stays silent — the reasoning pass owns the judgment).
  3. A fixture + manifest of known semantic cases exists as the comparison point
     for the agent's reading (used by hand / a harness, not a tautological unit
     test that recomputes the answer).

We assert what CAN be asserted deterministically about a probabilistic system.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
from test_detect import (  # noqa: E402
    construct_rows, detect, detect_findings, _pattern_rows, parse_manifest, _key
)

SEMANTIC_TAGS = {
    "cdc", "logic-on-reset", "logic-on-clock", "multi-edge",
    "mixed-logic", "case-no-default", "multi-driver", "generate-misuse",
    "port-width", "blocking-in-clocked", "incomplete-if-else",
}


# --------------------------------------------------------------------------- #
# 1. Semantic constructs are declared with a semantic tag and no pattern.
# --------------------------------------------------------------------------- #

def test_semantic_constructs_carry_a_tag_and_no_pattern():
    """Every synthesis-correctness construct that needs judgment is marked
    `semantic:TAG` and excluded from the pattern detector — so it is handed to
    the reasoning pass, never silently pattern-matched."""
    semantic_rows = [r for r in construct_rows() if r["semantic"]]
    assert semantic_rows, "no semantic constructs declared in CONSTRUCTS.md"
    for r in semantic_rows:
        assert r["semantic"] in SEMANTIC_TAGS, f"unknown semantic tag: {r['semantic']}"
        assert r["pattern"] is None, f"semantic construct {r['construct']!r} also has a pattern — pick one"


def test_reasoning_constructs_are_not_pattern_detected():
    """A construct marked semantic is NOT in the deterministic registry — it is
    reserved for the reasoning pass."""
    registry_constructs = {r["construct"] for r in _pattern_rows()}
    semantic_constructs = {r["construct"] for r in construct_rows() if r["semantic"]}
    overlap = registry_constructs & semantic_constructs
    assert overlap == set(), f"semantic construct also pattern-detected: {overlap}"


# --------------------------------------------------------------------------- #
# 2. Valid-form guard: a real async reset is not pattern-flagged.
# --------------------------------------------------------------------------- #

def test_valid_async_reset_is_not_pattern_flagged(tmp_path):
    """The valid async reset in the semantic fixture must NOT be flagged by the
    deterministic detector. The reasoning pass owns the judgment that it is
    valid; pattern detection must stay silent on it."""
    fixture = FIXTURES / "semantic.sv"
    findings = detect_findings(fixture)
    # No pattern construct should fire on the valid async reset (line 17) or on
    # the reasoning-only lines — pattern detection returns nothing here.
    findings = detect_findings(fixture)
    flagged_lines = {f["line"] for f in findings}
    # The valid async reset is the `always_ff @(posedge clk or negedge rst_n)`
    # on line 20 (line 17 is a comment). It must never appear as a pattern
    # Finding — pattern detection has no `posedge` pattern, so the reasoning
    # pass owns the judgment that this form is valid.
    assert 20 not in flagged_lines, f"valid async reset pattern-flagged: {findings}"
    assert 18 not in flagged_lines, f"valid async reset body pattern-flagged: {findings}"


# --------------------------------------------------------------------------- #
# 3. The semantic fixture + manifest exist as the comparison point.
# --------------------------------------------------------------------------- #

def test_semantic_fixture_and_manifest_exist():
    assert (FIXTURES / "semantic.sv").exists()
    assert (FIXTURES / "semantic.expected.md").exists()
    manifest = parse_manifest(FIXTURES / "semantic.expected.md")
    # The manifest records the reasoning-only constructs, none of which are
    # pattern-detectable — proving they require the reasoning pass.
    semantic_names = {r["construct"] for r in construct_rows() if r["semantic"]}
    for row in manifest:
        assert row["construct"] in semantic_names, (
            f"manifest construct {row['construct']!r} is not a declared semantic construct"
        )


def test_semantic_manifest_covers_every_reasoning_construct():
    """The fixture carries one case per semantic construct declared in
    CONSTRUCTS.md — so every reasoning construct has a known-case fixture."""
    manifest = parse_manifest(FIXTURES / "semantic.expected.md")
    declared = {r["construct"] for r in construct_rows() if r["semantic"]}
    manifest_constructs = {row["construct"] for row in manifest}
    missing = declared - manifest_constructs
    assert not missing, f"semantic constructs with no fixture case: {missing}"
    # And every manifest construct is a declared semantic construct.
    extra = manifest_constructs - declared
    assert not extra, f"manifest constructs not declared semantic: {extra}"


# --------------------------------------------------------------------------- #
# Honesty: the SKILL.md admits detection is model-dependent.
# --------------------------------------------------------------------------- #

def test_skill_admits_model_dependent_detection():
    skill = (FIXTURES.parent / ".claude" / "skills" / "synth-check-rtl" / "SKILL.md").read_text()
    assert "probabilistic" in skill.lower() or "model-dependent" in skill.lower(), (
        "SKILL.md must admit the reasoning pass is model-dependent / probabilistic"
    )
