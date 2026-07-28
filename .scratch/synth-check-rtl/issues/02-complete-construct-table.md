# 02 — Complete the construct table across all four categories

**What to build:** expand the construct reference (the single source of truth) from the tracer-bullet subset to the full set across all four categories — timing & sim-only, SV testbench-isms, synthesis-correctness, and structural/port. Each row co-locates the construct with its severity (`error`/`warning`/`note`), why it's non-synthesizable, the emulator-config/construct option that lets it run as-is, and the synthesizable rewrite. Fixtures grow to seed every category, with an expected-Findings manifest per fixture. The Detect path from 01 now surfaces all categories.

**Blocked by:** 01 — Detect behavioral codes, list lean Findings.

**Status:** ready-for-agent

- [ ] The construct reference covers all four categories (timing & sim-only, SV testbench-isms, synthesis-correctness, structural/port) with every row co-locating severity, why, emulator-config option, and synthesizable rewrite.
- [ ] Severity assignment is correct per category: `error` for won't-synthesize, `warning` for synthesizes-wrong, `note` for tool-dependent/structural.
- [ ] A fixture per category seeds its constructs, and each fixture's expected-Findings manifest (construct, line, severity, category) is reproduced by the skill.
- [ ] The construct reference remains the single source of truth — Detect loads entries on demand, not bulk.
