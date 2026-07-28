# 01 — Tracer bullet: Detect behavioral codes, list lean Findings

**What to build:** the end-to-end first slice. Invoke the skill with a path (defaulting to `rtl/` when no path is given and it exists). It scans `.v`/`.sv`/`.vhd` files, skips testbench code (`*_tb.sv`/`*_tb.v`, `bench/`, `tb/`) silently, and lists behavioral (non-synthesizable) constructs as lean **Findings** — `file:line | construct | severity | ref` — plus a one-line count summary (`N findings: X errors, Y warnings, Z notes`). Detect edits nothing and pre-computes no explanation or fix. This slice covers only the timing & sim-only category with a small handful of constructs (e.g. `#delay`, `forever`, `initial`, `$display`) — enough to prove the detect→list→report path is complete and verifiable, not a thorough table.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] Invoking the skill on a path scans `.v`/`.sv`/`.vhd` files; default is `rtl/` when no path given and that directory exists.
- [ ] Testbench files (`*_tb.sv`/`*_tb.v`, `bench/`, `tb/`) are skipped silently.
- [ ] Behavioral constructs are listed as lean Findings: `file:line | construct | severity | ref` plus a one-line count summary (`N findings: X errors, Y warnings, Z notes`).
- [ ] Detect edits no files and produces no per-item why or fix.
- [ ] A fixture `.sv` file seeds the timing & sim-only constructs, and an expected-Findings manifest asserts the skill reproduces it (construct, line, severity, category).
