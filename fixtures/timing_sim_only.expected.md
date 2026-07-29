# Expected Findings — fixtures/timing_sim_only.sv

The expected Findings when `/synth-check-rtl` scans `fixtures/timing_sim_only.sv`.
This is the acceptance manifest for the Detect tracer bullet: the skill must
reproduce exactly these Findings (construct, line, severity, category).

Every flagged construct is one Finding, so a line carrying two constructs
(e.g. `initial` and `#delay`) yields two Findings.

| # | file:line              | construct           | severity | category          |
|---|------------------------|----------------------|----------|-------------------|
| 1 | timing_sim_only.sv:15  | `real/time`          | error    | timing & sim-only |
| 2 | timing_sim_only.sv:17  | `#delay on assign`   | error    | timing & sim-only |
| 3 | timing_sim_only.sv:22  | `initial`            | error    | timing & sim-only |
| 4 | timing_sim_only.sv:23  | `#delay`             | error    | timing & sim-only |
| 5 | timing_sim_only.sv:24  | `$display`           | error    | timing & sim-only |
| 6 | timing_sim_only.sv:25  | `wait`               | error    | timing & sim-only |
| 7 | timing_sim_only.sv:29  | `forever`            | error    | timing & sim-only |

Summary: `7 findings: 7 errors, 0 warnings, 0 notes`

Line 17 (`assign dly_out = #2 clk;`) carries exactly one Finding
(`#delay on assign`), not two — the generic `#delay` pattern excludes lines
already matched by the more specific continuous-assign case.

Lines 19–20 (`resp_time`, and the "response time" comment) must NOT be
flagged: `\btime\b` requires a word boundary, so it never matches inside the
identifier `resp_time`, and the `//` comment content is stripped before
pattern matching (see SKILL.md's Pattern-pass step).

The synthesizable baseline (`always_ff` reset logic, lines 10–13) must NOT appear
in the findings.
