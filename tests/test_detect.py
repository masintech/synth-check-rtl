"""
Acceptance test for the synth-check-rtl skill — Detect (tickets 01, 02, 07).

This is the one pre-agreed test seam: run the skill on a fixture and assert it
reproduces that fixture's expected-Findings manifest.

The detection logic the skill describes is exercised through `detect` below.
To keep this test honest and avoid a tautology, the expected Findings come from
each fixture's manifest (an independent, hand-authored source of truth), NOT
recomputed by mirroring the detector's code.

Ticket 07: detection is driven by CONSTRUCTS.md (the single source of truth).
There is no separate hardcoded construct list — adding a construct with its
pattern to CONSTRUCTS.md extends detection. The allowlist is applied within
detection, and the Finding shape (file, line, construct, severity, category)
matches the manifests and SKILL.md.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "synth-check-rtl"

# --------------------------------------------------------------------------- #
# CONSTRUCTS.md parser — the single source of truth. Detection reads this.
# --------------------------------------------------------------------------- #

# A construct row optionally carries a detection spec in a trailing HTML
# comment on the row, of the form:  <!-- name:NAME | pattern:REGEX -->
# - `name`     — the canonical Finding construct name (the short, clean token
#                shown to the user; falls back to the stripped cell if absent).
# - `pattern`  — a regex; rows with a pattern are detected deterministically.
# Rows whose comment carries `semantic:TAG` instead are model-dependent (ticket
# 08) and are skipped by the deterministic detector.
_COMMENT = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)


def _parse_comment(comment: str | None) -> dict:
    """Extract name / pattern / semantic fields from a row's HTML comment.

    Fields are separated by ' | ', not bare '|' — regex patterns legitimately
    contain '|' (alternation), so splitting on every pipe would corrupt them.
    """
    out: dict = {"name": None, "pattern": None, "semantic": None}
    if not comment:
        return out
    for field in re.split(r"\s+\|\s+", comment):
        if field.startswith("name:"):
            out["name"] = field[len("name:"):].strip()
        elif field.startswith("pattern:"):
            out["pattern"] = field[len("pattern:"):].strip()
        elif field.startswith("semantic:"):
            out["semantic"] = field[len("semantic:"):].strip()
    return out


def _category_key(cat: str) -> str:
    """Normalize a category label so CONSTRUCTS.md headings and the manifests
    join on the same key (case + whitespace + slash vs hyphen)."""
    return re.sub(r"[\s/-]+", "", cat).lower()


def _cell_short_name(raw: str) -> str:
    """Fallback construct name from the cell: strip backticks, take the leading
    token up to '(' or '/'. Prefer the explicit `name:` field when present."""
    name = raw.strip().strip("`")
    name = re.split(r"[/(]", name)[0]
    return name.strip()


def construct_rows() -> list[dict]:
    """Parse CONSTRUCTS.md into one dict per construct row, on demand.

    Each dict: {construct, severity, category, why, emulator_config, rewrite,
    pattern, semantic}. `construct` is the canonical Finding name (from `name:`
    if given, else the stripped cell). `pattern` is None for semantic constructs.
    """
    text = (SKILL / "CONSTRUCTS.md").read_text()
    rows: list[dict] = []
    current_category = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            m = re.match(r"## \d+\.\s*(.*)", stripped)
            current_category = m.group(1).strip() if m else ""
            continue
        if not stripped.startswith("|") or set(stripped.replace("|", "")) <= {"-"}:
            continue
        # Split on the first 5 pipes only — the rewrite cell can legitimately
        # contain '|' (e.g. inside a code snippet), so don't over-split.
        cells = _split_row(stripped)
        if len(cells) < 5 or cells[0].lower() in {"construct"}:
            continue
        construct_cell, severity, why, emu, rewrite = cells[0], cells[1], cells[2], cells[3], cells[4]
        meta = _parse_comment(_COMMENT.search(line).group(1) if _COMMENT.search(line) else None)
        rows.append({
            "construct": meta["name"] or _cell_short_name(construct_cell),
            "severity": severity,
            "category": current_category,
            "why": why,
            "emulator_config": emu,
            "rewrite": _strip_trailing_comment(rewrite),
            "pattern": meta["pattern"],
            "semantic": meta["semantic"],
        })
    return rows


def _strip_trailing_comment(text: str) -> str:
    """Strip a trailing `<!-- ... -->` detection comment from a CONSTRUCTS.md
    cell, leaving the human-readable content. Single source for this strip —
    shared by construct_rows() and the fix/explain lookups in test_fix."""
    return re.sub(r"<!--.*?-->\s*$", "", text, flags=re.DOTALL).strip()


def _split_row(stripped: str) -> list[str]:
    """Split a markdown table row into its cells.

    The first 4 pipes delimit construct/severity/why/emu; everything after the
    5th pipe is the rewrite cell, which may itself contain pipes (code). We cut
    on the first 5 pipes and keep the remainder as the rewrite, intact.
    """
    body = stripped.strip().strip("|")
    idx = []
    i = 0
    while i < len(body):
        j = body.find("|", i)
        if j == -1:
            break
        idx.append(j)
        i = j + 1
    if len(idx) < 4:
        return [body]
    cuts = [body[:idx[0]]] + [body[idx[k] + 1: idx[k + 1]] for k in range(3)] + [body[idx[3] + 1:]]
    return [c.strip() for c in cuts]

def _pattern_rows() -> list[dict]:
    """Only the constructs that carry a deterministic pattern."""
    return [r for r in construct_rows() if r["pattern"]]


# The detectable registry, derived from CONSTRUCTS.md (single source of truth).
def _build_registry() -> dict[str, tuple[re.Pattern, str, str]]:
    return {
        r["construct"]: (re.compile(r["pattern"]), r["severity"], r["category"])
        for r in _pattern_rows()
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
    Detection patterns come from CONSTRUCTS.md (single source of truth). Lines
    are stripped of `//` comments and string literals' content before matching,
    so words in comments or strings don't trigger false Findings.
    """
    registry = _build_registry()
    text = path.read_text()
    findings: list[dict] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        probe = _strip_comments(line)
        for construct, (regex, severity, category) in registry.items():
            if regex.search(probe):
                findings.append({
                    "file": path.name,
                    "line": lineno,
                    "construct": construct,
                    "severity": severity,
                    "category": category,
                })
    return findings


def _strip_comments(line: str) -> str:
    """Remove a trailing `//` line comment and the contents of "..." string
    literals, so words inside them don't match detection patterns."""
    # Drop everything from an unquoted `//`.
    in_str = False
    out: list[str] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
        if not in_str and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        if in_str and ch != '"':
            out.append(" ")
        else:
            out.append(ch)
        i += 1
    return "".join(out)

# The shipped seed allowlist, auto-loaded by detect() when no allowlist is given.
_SEED_ALLOWLIST = Path(__file__).resolve().parent.parent / "docs" / "agents" / "emulation-allowlist.md"


def detect(path: Path, allowlist: set[str] | None = None) -> list[dict]:
    """Detect Findings over a file or directory, skipping testbench.

    The allowlist is applied within detection: a Finding against an allowlisted
    construct downgrades to 'note'. When `allowlist` is None (the default), the
    shipped seed at `docs/agents/emulation-allowlist.md` is auto-loaded — so an
    agent running the skill body with no arguments gets per-project tuning for
    free. Pass an explicit set (e.g. `set()`) to override and disable it.
    """
    if allowlist is None:
        allowlist = parse_allowlist(_SEED_ALLOWLIST)
    if path.is_dir():
        results: list[dict] = []
        for f in sorted(path.rglob("*")):
            if f.is_file() and is_rtl(f) and not is_testbench(f):
                results.extend(detect_findings(f))
    elif is_rtl(path) and not is_testbench(path):
        results = detect_findings(path)
    else:
        results = []
    return apply_allowlist(results, allowlist)


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


def test_detect_produces_count_summary():
    """Detect emits a one-line summary of error/warning/note counts."""
    actual = detect(FIXTURES / "timing_sim_only.sv")
    summary = count_summary(actual)
    assert summary == "7 findings: 7 errors, 0 warnings, 0 notes"


def test_detect_reproduces_synth_correctness_manifest():
    """The synth_correctness fixture's pattern-level manifest is empty — its
    inferred-latch and blocking-in-clocked cases are semantic (reasoning pass)."""
    manifest = parse_manifest(FIXTURES / "synth_correctness.expected.md")
    actual = detect(FIXTURES / "synth_correctness.sv")
    assert sorted(_key(f) for f in actual) == sorted(_key(f) for f in manifest)


def test_detect_reproduces_structural_port_manifest():
    manifest = parse_manifest(FIXTURES / "structural_port.expected.md")
    actual = detect(FIXTURES / "structural_port.sv")
    assert sorted(_key(f) for f in actual) == sorted(_key(f) for f in manifest)


# --------------------------------------------------------------------------- #
# Single-source-of-truth invariants (ticket 07).
# --------------------------------------------------------------------------- #

def test_detection_registry_derives_from_constructs_md():
    """The detectable registry is built FROM CONSTRUCTS.md, not a parallel list.

    Every construct whose row carries a pattern comment must appear in the
    registry; every registry entry must trace to a row. No separate hardcoded
    construct list exists.
    """
    registry = _build_registry()
    pattern_rows = _pattern_rows()
    assert set(registry.keys()) == {r["construct"] for r in pattern_rows}


def test_adding_a_construct_with_a_pattern_extends_detection(tmp_path):
    """A construct added to CONSTRUCTS.md with a pattern is detected without
    touching detection code — the single-source-of-truth invariant."""
    # Build a throwaway CONSTRUCTS.md with one extra construct + pattern.
    constructs = (SKILL / "CONSTRUCTS.md").read_text()
    injected = constructs + (
        "\n| `testonly_marker` | error | test | Unsupported. | x | <!-- pattern: testonly_marker_regex -->\n"
    )
    new_skill = tmp_path / "skill"
    new_skill.mkdir()
    (new_skill / "CONSTRUCTS.md").write_text(injected)
    # Point the module's SKILL path at the throwaway and re-derive the registry.
    import test_detect as td
    orig = td.SKILL
    td.SKILL = new_skill
    try:
        reg = td._build_registry()
        assert "testonly_marker" in reg
        # The original constructs are still present (no regression from the add).
        assert "#delay" in reg
    finally:
        td.SKILL = orig


def test_finding_shape_matches_manifest_and_skill():
    """The Finding shape is consistent across CONSTRUCTS.md, the manifests, and
    SKILL.md: {file, line, construct, severity, category} — and SKILL.md makes no
    stale `ref`-field claim."""
    findings = detect(FIXTURES / "timing_sim_only.sv")
    for f in findings:
        assert set(f.keys()) == {"file", "line", "construct", "severity", "category"}
    skill = (SKILL / "SKILL.md").read_text()
    assert "category" in skill
    # The stale claim "A Finding's `ref` names a construct" (the old Vocabularies
    # section) must be gone — it contradicted the {construct, ...} shape.
    assert "A Finding's `ref`" not in skill and "Finding's `ref`" not in skill, (
        "SKILL.md still claims a `ref` field — reconcile to {construct, ...}"
    )


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
    findings = detect(FIXTURES / "timing_sim_only.sv", allowlist={"#delay"})
    delays = [f for f in findings if f["construct"] == "#delay"]
    assert delays and all(f["severity"] == "note" for f in delays)


def test_without_allowlist_construct_is_at_base_severity():
    """With the allowlist explicitly disabled (empty set), the construct is at
    its base severity. (The default path auto-loads the shipped seed, which is
    also empty, so this checks the override path specifically.)"""
    findings = detect(FIXTURES / "timing_sim_only.sv", allowlist=set())
    delays = [f for f in findings if f["construct"] == "#delay"]
    assert delays and all(f["severity"] == "error" for f in delays)


def test_default_detect_auto_loads_shipped_seed_allowlist():
    """Calling detect() with no allowlist auto-loads the shipped seed — so an
    agent running the skill body with no args gets per-project tuning. With the
    empty shipped seed, severities are unchanged; if the seed listed `#delay`,
    those Findings would downgrade to note."""
    findings = detect(FIXTURES / "timing_sim_only.sv")  # default -> shipped seed
    delays = [f for f in findings if f["construct"] == "#delay"]
    assert delays and all(f["severity"] == "error" for f in delays)  # seed is empty
    # And the default path honors a populated seed the same as an explicit set:
    findings_with = detect(FIXTURES / "timing_sim_only.sv", allowlist={"#delay"})
    assert all(f["severity"] == "note" for f in findings_with if f["construct"] == "#delay")


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
    return (f["file"], f["line"], f["construct"], f["severity"], _category_key(f["category"]))


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
