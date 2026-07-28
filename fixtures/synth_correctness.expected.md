# Expected Findings — fixtures/synth_correctness.sv

| # | file:line            | construct                          | severity | category              |
|---|----------------------|------------------------------------|----------|-----------------------|

Summary: `0 findings: 0 errors, 0 warnings, 0 notes`

Note: the inferred-latch case (the `always @(*)` block, line 10) and the
blocking-in-clocked-block case (line 16) are **semantic** constructs — they are
flagged by the reasoning pass against SYNTH-RULES.md, not by pattern. This
fixture's pattern-level manifest is therefore empty; see `fixtures/semantic.sv`
+ `semantic.expected.md` for the reasoning cases.

