# Expected Findings — fixtures/timing_sim_only.sv

The expected Findings when `/synth-check-rtl` scans `fixtures/timing_sim_only.sv`.
This is the acceptance manifest for the Detect tracer bullet: the skill must
reproduce exactly these Findings (construct, line, severity, category).

Every flagged construct is one Finding, so a line carrying two constructs
(e.g. `initial` and `#delay`) yields two Findings.

| # | file:line              | construct  | severity | category          |
|---|------------------------|------------|----------|-------------------|
| 1 | timing_sim_only.sv:15  | `initial`  | error    | timing & sim-only |
| 2 | timing_sim_only.sv:16  | `#delay`   | error    | timing & sim-only |
| 3 | timing_sim_only.sv:17  | `$display` | error    | timing & sim-only |
| 4 | timing_sim_only.sv:18  | `wait`     | error    | timing & sim-only |
| 5 | timing_sim_only.sv:22  | `forever`  | error    | timing & sim-only |

Summary: `5 findings: 5 errors, 0 warnings, 0 notes`

The synthesizable baseline (`always_ff` reset logic, lines 10–13) must NOT appear
in the findings.
