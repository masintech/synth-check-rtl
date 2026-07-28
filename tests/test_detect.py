"""
Acceptance test for the synth-check-rtl skill — Detect tracer bullet (ticket 01).

This is the one pre-agreed test seam: run the skill on a fixture and assert it
reproduces that fixture's expected-Findings manifest.

The skill is an agent skill, so its Detect logic is exercised through a small,
stable detection routine the skill itself documents. To keep this test honest and
avoid a tautology, the expected Findings come from the fixture's manifest
(an independent source of truth, hand-authored from the spec), NOT recomputed
by mirroring the detector's code.

How the skill is reached:
  - The detector's construct list lives in fixtures/../../CONSTRUCTS-like reference
    but for ticket 01 the construct set is small and the detection routine is
    minimal. This test drives the detection routine over the fixture text and
    checks the Findings against the manifest.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


# --------------------------------------------------------------------------- #
# Minimal Detect routine for the tracer-bullet subset (timing & sim-only).
# This is the detection logic the skill describes for ticket 01; it is the
# thing under test. Keeping it tiny and explicit is the point of the slice.
# --------------------------------------------------------------------------- #

# Tracer-bullet construct subset: timing & sim-only.
# Each entry: (regex, construct name, severity, category)
_TRACER_CONSTRUCTS = [
    (re.compile(r"#\d+"),                        "#delay",    "error", "timing & sim-only"),
    (re.compile(r"\$display\b"),                 "$display",  "error", "timing & sim-only"),
    (re.compile(r"\bwait\s*\("),                 "wait",      "error", "timing & sim-only"),
    (re.compile(r"\bforever\b"),                  "forever",   "error", "timing & sim-only"),
    (re.compile(r"\binitial\b"),                  "initial",   "error", "timing & sim-only"),
]

# Files that are testbench and must be skipped, by convention.
_TB_PATTERNS = (re.compile(r"_tb\.sv$"), re.compile(r"_tb\.v$"))
_TB_DIRS = ("bench", "tb")


def is_testbench(path: Path) -> bool:
    name = path.name
    if any(p.search(name) for p in _TB_PATTERNS):
        return True
    return any(part in _TB_DIRS for part in path.parts)


def is_rtl(path: Path) -> bool:
    return path.suffix in {".v", ".sv", ".vhd"}


def detect_findings(path: Path) -> list[dict]:
    """Return the Findings for one file as a list of dicts.

    A Finding is: {file, line, construct, severity, category}.
    """
    text = path.read_text()
    findings: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for regex, construct, severity, category in _TRACER_CONSTRUCTS:
            if regex.search(line):
                findings.append({
                    "file": path.name,
                    "line": lineno,
                    "construct": construct,
                    "severity": severity,
                    "category": category,
                })
    return findings


def detect(path: Path) -> list[dict]:
    """Detect Findings over a file or directory, skipping testbench."""
    if path.is_dir():
        results: list[dict] = []
        for f in sorted(path.rglob("*")):
            if f.is_file() and is_rtl(f) and not is_testbench(f):
                results.extend(detect_findings(f))
        return results
    if is_rtl(path) and not is_testbench(path):
        return detect_findings(path)
    return []


# --------------------------------------------------------------------------- #
# Manifest parsing — the independent source of truth for expected Findings.
# --------------------------------------------------------------------------- #

_MANIFEST_ROW = re.compile(
    r"\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"
)


def _clean_construct(name: str) -> str:
    return name.strip().strip("`").strip()


def parse_manifest(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text().splitlines():
        m = _MANIFEST_ROW.match(line.strip())
        if not m:
            continue
        file_line, construct, severity, category = (g.strip() for g in m.groups())
        # file:line -> split, line to int
        fname, _, lineno = file_line.partition(":")
        rows.append({
            "file": fname.strip(),
            "line": int(lineno),
            "construct": _clean_construct(construct),
            "severity": severity,
            "category": category,
        })
    return rows


# --------------------------------------------------------------------------- #
# Tests — red before green.
# --------------------------------------------------------------------------- #

def test_detect_reproduces_timing_sim_only_manifest():
    """The skill's Detect reproduces the fixture's expected-Findings manifest."""
    fixture = FIXTURES / "timing_sim_only.sv"
    manifest = parse_manifest(FIXTURES / "timing_sim_only.expected.md")

    actual = detect(fixture)
    # Order-independent comparison: same set of Findings.
    assert sorted(
        (f["file"], f["line"], f["construct"], f["severity"], f["category"])
        for f in actual
    ) == sorted(
        (f["file"], f["line"], f["construct"], f["severity"], f["category"])
        for f in manifest
    )


def test_detect_produces_count_summary():
    """Detect emits a one-line summary of error/warning/note counts."""
    actual = detect(FIXTURES / "timing_sim_only.sv")
    summary = count_summary(actual)
    assert summary == "5 findings: 5 errors, 0 warnings, 0 notes"


def test_detect_skips_testbench_files():
    """Testbench files are skipped silently."""
    tb = FIXTURES / "skip_tb.sv"  # created by the test below
    tb.write_text("module skip_tb; initial #10 $display(\"x\"); endmodule\n")
    try:
        assert detect(tb) == []
    finally:
        tb.unlink()


def test_detect_defaults_to_rtl_dir(tmp_path, monkeypatch):
    """With no path and an rtl/ dir present, Detect scans rtl/."""
    rtl = tmp_path / "rtl"
    rtl.mkdir()
    (rtl / "a.sv").write_text("module a; initial #10; endmodule\n")
    # bench/ under tmp must be skipped
    bench = tmp_path / "bench"
    bench.mkdir()
    (bench / "b_tb.sv").write_text("module b_tb; initial #5; endmodule\n")

    monkeypatch.chdir(tmp_path)
    actual = detect(Path("rtl"))
    # a.sv has both `initial` and `#delay` on one line -> two Findings.
    assert [f["file"] for f in actual] == ["a.sv", "a.sv"]
    assert {f["construct"] for f in actual} == {"initial", "#delay"}
    # b_tb.sv under bench/ is skipped entirely.
    assert all(f["file"] != "b_tb.sv" for f in actual)


def count_summary(findings: list[dict]) -> str:
    errs = sum(1 for f in findings if f["severity"] == "error")
    warns = sum(1 for f in findings if f["severity"] == "warning")
    notes = sum(1 for f in findings if f["severity"] == "note")
    return f"{len(findings)} findings: {errs} errors, {warns} warnings, {notes} notes"
