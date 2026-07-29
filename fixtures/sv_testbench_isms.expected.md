# Expected Findings — fixtures/sv_testbench_isms.sv

| # | file:line                 | construct          | severity | category          |
|---|---------------------------|--------------------|----------|-------------------|
| 1 | sv_testbench_isms.sv:7    | `dynamic array`    | error    | SV testbench-isms |
| 2 | sv_testbench_isms.sv:8    | `associative array`| error    | SV testbench-isms |
| 3 | sv_testbench_isms.sv:9    | `queue`            | error    | SV testbench-isms |
| 4 | sv_testbench_isms.sv:11   | `class`            | error    | SV testbench-isms |

Summary: `4 findings: 4 errors, 0 warnings, 0 notes`

The synthesizable `always_ff` (lines 18–20), the static `reg_array`
(line 15), and the variable-indexed RAM read `reg_array[in[3:0]]` (line 18) —
ordinary array indexing, not an associative array — must NOT be flagged.
