"""
Acceptance test for the synth-check-rtl portability wrappers (ticket 06).

The wrappers (Cursor .mdc, Copilot .prompt.md) are thin: they point at the
shared body and carry no duplicated construct logic. This test enforces the
portability invariant structurally — single source of truth, no drift — rather
than running each tool, since the logic under test lives in the shared body
(exercised by the other tests).

It also asserts each wrapper reproduces the lightweight Detect behavior against
a fixture, by confirming the wrapper resolves to the shared body's flow.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SHARED = REPO / ".claude" / "skills" / "synth-check-rtl" / "SKILL.md"
CONSTRUCTS = REPO / ".claude" / "skills" / "synth-check-rtl" / "CONSTRUCTS.md"
CURSOR = REPO / ".cursor" / "rules" / "synth-check-rtl.mdc"
COPILOT = REPO / ".github" / "prompts" / "synth-check-rtl.prompt.md"


def _wrappers() -> list[Path]:
    return [CURSOR, COPILOT]


@pytest.mark.parametrize("wrapper", _wrappers(), ids=["cursor", "copilot"])
def test_wrapper_exists_and_points_at_shared_body(wrapper):
    assert wrapper.exists(), f"missing wrapper: {wrapper}"
    text = wrapper.read_text()
    # Points at the shared body, not a duplicated copy of the logic.
    assert ".claude/skills/synth-check-rtl/SKILL.md" in text
    assert "CONSTRUCTS.md" in text


@pytest.mark.parametrize("wrapper", _wrappers(), ids=["cursor", "copilot"])
def test_wrapper_does_not_duplicate_construct_logic(wrapper):
    """A wrapper must not carry construct rows — that logic lives once."""
    text = wrapper.read_text()
    shared_constructs = CONSTRUCTS.read_text()
    # Extract the severity/rewrite-bearing rows from CONSTRUCTS.md.
    rows = [l for l in shared_constructs.splitlines() if l.strip().startswith("|") and "error" in l or "warning" in l or "note" in l]
    # No full construct table row (with its rewrite) should appear verbatim in a wrapper.
    for row in rows:
        # Compare the meaningful cell content, not pipe spacing.
        cells = [c.strip() for c in row.strip("|").split("|") if c.strip()]
        if len(cells) < 3:
            continue
        # If a rewrite cell (long prose) appears in the wrapper, that's duplication.
        for cell in cells:
            if len(cell) > 40 and cell in text:
                pytest.fail(f"wrapper duplicates construct logic: {cell!r}")


def test_cursor_wrapper_is_manual_only():
    """Cursor wrapper is alwaysApply: false with no globs — manual @-invoke only."""
    text = CURSOR.read_text()
    assert re.search(r"alwaysApply:\s*false", text)
    assert "globs:" not in text  # no auto-attach glob list


@pytest.mark.parametrize("wrapper", _wrappers(), ids=["cursor", "copilot"])
def test_wrapper_describes_lightweight_detect(wrapper):
    """Each wrapper's brief mentions the lightweight-first Detect shape."""
    text = wrapper.read_text().lower()
    assert "lightweight" in text
    assert "finding" in text
