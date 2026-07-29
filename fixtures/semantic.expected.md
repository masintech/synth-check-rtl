# Expected Findings — fixtures/semantic.sv (semantic / reasoning constructs)

These constructs are **not** pattern-detectable. The agent reasons against
`SYNTH-RULES.md` and flags the real instances; a valid async reset is left alone.
This manifest is the source of truth for ticket 08's reasoning pass. Accuracy is
**probabilistic** — these expected Findings are what a correct reading produces;
a weaker model may miss or misjudge. Verification treats this as a fixture of
known cases, not a tautological unit test that recomputes the answer.

| #  | file:line      | construct                          | severity | category              |
|----|----------------|------------------------------------|----------|-----------------------|
| 1  | semantic.sv:27 | `multi-edge sensitivity`           | warning  | synthesis-correctness |
| 2  | semantic.sv:32 | `logic on reset`                   | warning  | synthesis-correctness |
| 3  | semantic.sv:40 | `clock-domain crossing`            | warning  | synthesis-correctness |
| 4  | semantic.sv:44 | `inferred latch (if/else)`         | warning  | synthesis-correctness |
| 5  | semantic.sv:50 | `logic on clock`                   | warning  | synthesis-correctness |
| 6  | semantic.sv:56 | `mixed logic in sequential block`  | note     | synthesis-correctness |
| 7  | semantic.sv:63 | `multi-driver net`                | warning  | synthesis-correctness |
| 8  | semantic.sv:66 | `blocking in clocked block`        | warning  | synthesis-correctness |
| 9  | semantic.sv:72 | `inferred latch (case)`            | warning  | synthesis-correctness |
| 10 | semantic.sv:84 | `generate misuse`                   | note     | structural/port      |
| 11 | semantic.sv:95 | `port width mismatch`              | warning  | structural/port      |

NOT flagged (must stay silent):
- `semantic.sv:20` — `posedge clk or negedge rst_n` is a **valid async reset**
  (SYNTH-RULES Rule 1). A correct reasoning pass leaves it alone.

## Honesty note

These eleven cases cover every semantic construct declared in CONSTRUCTS.md.
Because detection is model-dependent, this manifest is exercised as a fixture
(the agent's reading is compared to it), not as a tautological unit test that
recomputes the answer.
