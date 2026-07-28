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
    (re.compile(r"#\d+"),                             "#delay",                   "error",   "timing & sim-only"),
    (re.compile(r"\$display\b"),                      "$display",                 "error",   "timing & sim-only"),
    (re.compile(r"\bwait\s*\("),                      "wait",                     "error",   "timing & sim-only"),
    (re.compile(r"\bforever\b"),                       "forever",                  "error",   "timing & sim-only"),
    (re.compile(r"\binitial\b"),                       "initial",                  "error",   "timing & sim-only"),
    # SV testbench-isms
    (re.compile(r"\w+\s*\[\s*\]"),                     "dynamic array",            "error",   "SV testbench-isms"),
    (re.compile(r"\w+\s*\[[a-zA-Z_]\w*\]"),            "associative array",        "error",   "SV testbench-isms"),
    (re.compile(r"\[\s*\$"),                            "queue",                    "error",   "SV testbench-isms"),
    (re.compile(r"\bclass\b"),                          "class",                    "error",   "SV testbench-isms"),
    # synthesis-correctness
    (re.compile(r"always\s*@\s*\(\s*\*\s*\)"),          "inferred latch",           "warning", "synthesis-correctness"),
    # structural / port
    (re.compile(r"parameter\s+real\b"),                 "real parameter",           "error",   "structural/port"),
]

# Stable registry: construct name -> (severity, category), for the detectable
# subset. (CONSTRUCTS.md is the full source of truth; this maps the constructs
# the detector can currently flag by pattern.)
CONSTRUCT_REGISTRY: dict[str, tuple[str, str]] = {
    name: (severity, category) for _r, name, severity, category in _TRACER_CONSTRUCTS
}

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

    actual = detect(FIXTURES / "timing_sim_only.sv")
    # Order-independent comparison: same set of Findings.
    assert sorted(_key(f) for f in actual) == sorted(_key(f) for f in manifest)


def test_detect_reproduces_sv_testbench_isms_manifest():
    manifest = parse_manifest(FIXTURES / "sv_testbench_isms.expected.md")
    actual = detect(FIXTURES / "sv_testbench_isms.sv")
    assert sorted(_key(f) for f in actual) == sorted(_key(f) for f in manifest)


def test_detect_reproduces_synth_correctness_manifest():
    manifest = parse_manifest(FIXTURES / "synth_correctness.expected.md")
    actual = detect(FIXTURES / "synth_correctness.sv")
    assert sorted(_key(f) for f in actual) == sorted(_key(f) for f in manifest)


def test_detect_reproduces_structural_port_manifest():
    manifest = parse_manifest(FIXTURES / "structural_port.expected.md")
    actual = detect(FIXTURES / "structural_port.sv")
    assert sorted(_key(f) for f in actual) == sorted(_key(f) for f in manifest)


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


# --------------------------------------------------------------------------- #
# Allowlist tests (ticket 04).
# --------------------------------------------------------------------------- #

def test_allowlist_downgrades_to_note():
    """A construct in the allowlist is reported at note severity."""
    findings = detect(FIXTURES / "timing_sim_only.sv")
    with_allow = apply_allowlist(findings, allowlist={"#delay"})
    delays = [f for f in with_allow if f["construct"] == "#delay"]
    assert delays and all(f["severity"] == "note" for f in delays)


def test_without_allowlist_construct_is_at_base_severity():
    """Without the allowlist, the same construct is at its base severity."""
    findings = detect(FIXTURES / "timing_sim_only.sv")
    without = apply_allowlist(findings, allowlist=set())
    delays = [f for f in without if f["construct"] == "#delay"]
    assert delays and all(f["severity"] == "error" for f in delays)


def test_absent_allowlist_governs_generically():
    """An absent allowlist file yields an empty set (generic subset governs)."""
    al = parse_allowlist(FIXTURES / "does_not_exist.md")
    assert al == set()


def test_seed_allowlist_parses_to_empty():
    """The shipped seed allowlist has no accepted constructs."""
    repo_allowlist = FIXTURES.parent / "docs" / "agents" / "emulation-allowlist.md"
    assert parse_allowlist(repo_allowlist) == set()


def count_summary(findings: list[dict]) -> str:
    errs = sum(1 for f in findings if f["severity"] == "error")
    warns = sum(1 for f in findings if f["severity"] == "warning")
    notes = sum(1 for f in findings if f["severity"] == "note")
    return f"{len(findings)} findings: {errs} errors, {warns} warnings, {notes} notes"


def _key(f: dict):
    return (f["file"], f["line"], f["construct"], f["severity"], f["category"])


# --------------------------------------------------------------------------- #
# Allowlist — per-project downgrade to note.
# --------------------------------------------------------------------------- #

_ALLOWLIST_ENTRY = re.compile(r"^\s*-\s*`?([^`]+?)`?\s*$")


def parse_allowlist(path: Path) -> set[str]:
    """Parse the allowlist's accepted-construct list.

    Reads only the bulleted entries under 'Accepted constructs'. An absent file
    or an empty list yields an empty set — the generic subset then governs.
    """
    if not path.exists():
        return set()
    text = path.read_text()
    # Collect lines under the 'Accepted constructs' heading, before '## Notes'.
    lines = text.splitlines()
    accepted: list[str] = []
    in_section = False
    for line in lines:
        if line.strip().startswith("## Accepted"):
            in_section = True
            continue
        if line.strip().startswith("## "):  # next heading ends the section
            in_section = False
            continue
        if not in_section:
            continue
        m = _ALLOWLIST_ENTRY.match(line)
        if m and m.group(1).strip().lower() not in {"(none)"}:
            accepted.append(m.group(1).strip())
    return set(accepted)


def apply_allowlist(findings: list[dict], allowlist: set[str]) -> list[dict]:
    """Downgrade a Finding against an allowlisted construct to 'note'."""
    out: list[dict] = []
    for f in findings:
        if f["construct"] in allowlist:
            out.append({**f, "severity": "note"})
        else:
            out.append(f)
    return out
