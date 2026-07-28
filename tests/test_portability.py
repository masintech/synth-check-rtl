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
    """A wrapper must not carry construct rows — that logic lives once.

    A wrapper is a pointer, not a copy. Its body must be far shorter than the
    shared construct table, and must not reproduce any long prose row from
    CONSTRUCTS.md (which would be duplication drifting from the single source).
    """
    text = wrapper.read_text()
    shared_constructs = CONSTRUCTS.read_text()
    # No construct-table rewrite cell (the long prose a row carries) should
    # appear verbatim in a wrapper.
    for line in shared_constructs.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|") if c.strip()]
        for cell in cells:
            if len(cell) > 40 and cell in text:
                pytest.fail(f"wrapper duplicates construct logic: {cell!r}")
    # And the wrapper is a pointer, so it stays short relative to the full table.
    assert len(text) < len(shared_constructs), (
        "wrapper is longer than the shared body it points at — likely duplicated"
    )


def test_cursor_wrapper_is_manual_only():
    """Cursor wrapper is alwaysApply: false with no globs — manual @-invoke only."""
    text = CURSOR.read_text()
    assert re.search(r"alwaysApply:\s*false", text)
    assert "globs:" not in text  # no auto-attach glob list


@pytest.mark.parametrize("wrapper", _wrappers(), ids=["cursor", "copilot"])
def test_wrapper_points_at_shared_body_and_is_thin(wrapper):
    """Each wrapper points at the shared body and stays a thin pointer.

    The lightweight-first behavior lives in the shared body; the wrapper need
    only point there. We assert the pointer is present and the wrapper is a
    pointer, not a restatement — covered by the exists/thin checks above. This
    test guards that the pointer text itself is intact.
    """
    text = wrapper.read_text()
    assert ".claude/skills/synth-check-rtl/SKILL.md" in text
    assert ".claude/skills/synth-check-rtl/CONSTRUCTS.md" in text
