# Expected Findings — fixtures/semantic.sv (semantic / reasoning constructs)

These constructs are **not** pattern-detectable. The agent reasons against
`SYNTH-RULES.md` and flags the real instances; a valid async reset is left alone.
This manifest is the source of truth for ticket 08's reasoning pass. Accuracy is
**probabilistic** — these expected Findings are what a correct reading produces;
a weaker model may miss or misjudge. Verification therefore treats this as a
fixture of known cases, not a guarantee.

| # | file:line      | construct            | severity | category              |
|---|----------------|----------------------|----------|-----------------------|
| 1 | semantic.sv:23 | `multi-edge sensitivity` | warning | synthesis-correctness |
| 2 | semantic.sv:30 | `logic on reset`     | warning  | synthesis-correctness |
| 3 | semantic.sv:36 | `clock-domain crossing` | warning | synthesis-correctness |

NOT flagged (must stay silent):
- `semantic.sv:17` — `posedge clk or negedge rst_n` is a **valid async reset**
  (SYNTH-RULES Rule 1). A correct reasoning pass leaves it alone.

## Honesty note

These three are the cases the reasoning pass must get right. Because detection is
model-dependent, this manifest is exercised as a fixture (the agent's reading is
compared to it), not as a tautological unit test that recomputes the answer.
