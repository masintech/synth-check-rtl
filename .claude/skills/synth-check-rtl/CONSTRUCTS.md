# CONSTRUCTS — the construct reference

The single source of truth for what `synth-check-rtl` flags. Each construct
co-locates its **severity**, **why** it's non-synthesizable, the
**emulator-config option** that lets it run as-is, and the **synthesizable
rewrite** — in one row, so changing a verdict or fix is a one-place edit.

Loaded on demand (per Finding), never bulk-loaded during Detect.

## Severity

- `error` — won't synthesize / won't elaborate on an emulator.
- `warning` — synthesizes but produces wrong or ambiguous hardware.
- `note` — tool-dependent / structural, or a construct listed in the project
  allowlist (`docs/agents/emulation-allowlist.md`).

## 1. Timing & sim-only

| Construct   | Severity | Why                                                  | Emulator-config option                          | Synthesizable rewrite                                                              |
|-------------|----------|------------------------------------------------------|-------------------------------------------------|------------------------------------------------------------------------------------|
| `#delay`    | error    | No timing; synthesis ignores or drops it.            | Some emulators accept `#delay` in a sim-only region if isolated and pruned. | `always_ff @(posedge clk or negedge rst_n) if (!rst_n) q<=0; else q<=1;` — drive from the clock edge, not a delay. |
| `$display`  | error    | System task; no hardware.                            | Emulators often elide `$display` if the synthesis flow strips system tasks. | Remove from RTL; emit state via a synthesizable debug port instead.          |
| `wait(sig)` | error    | Level-sensitive wait has no hardware.                | Few emulators support it; usually rejected.     | `always_ff @(posedge clk or negedge rst_n) if (!rst_n) q<=0; else q<=sig;` — sample the level on the clock edge. |
| `forever`   | error    | Unbounded loop; no hardware termination.             | Unsupported in synthesis.                       | Drive from a clocked `always_ff` with an explicit enable/condition.                |
| `initial`   | error    | Simulation-only initialization; no reset hardware.  | Emulators accept `initial` for FPGA-style init (some flows). | Move init into a clocked reset branch (`if (!rst_n)`).                          |
| `event`     | error    | Simulation event type; no hardware.                  | Unsupported.                                    | Replace with a wire/logic signal triggered on a clock edge.                        |
| `force`/`release` | error | Procedural override; not hardware.             | Used in sim only; emulators reject in RTL.      | Remove; model the override as a mux/select driven by a control signal.            |
| `fork`/`join` | error  | Concurrent processes; no hardware parallelism model. | Unsupported.                                  | Serialize into one clocked process, or model as parallel always_ff blocks.         |
| `disable`   | error    | Procedural process kill; no hardware.               | Unsupported.                                    | Replace with a state-machine exit condition / enable deassert.                     |
| `deassign`  | error    | Procedural override removal; not hardware.          | Unsupported.                                    | Remove; assign through a single driver with a mux.                                 |
| `real`/`time` type | error | Non-synthesizable types.                       | Unsupported.                                    | Use fixed-point integer arithmetic.                                                |

## 2. SV testbench-isms

| Construct            | Severity | Why                                          | Emulator-config option            | Synthesizable rewrite                                        |
|----------------------|----------|----------------------------------------------|------------------------------------|--------------------------------------------------------------|
| dynamic array `[]`   | error    | Heap-allocated; no hardware.                 | Unsupported in RTL.                | Use a fixed-size array with a bounded depth constant.        |
| associative array    | error    | Hashed storage; no hardware.                 | Unsupported.                       | Use a fixed-size array indexed by an enumerated/bounded key. |
| `class`              | error    | OOP; no hardware.                            | Unsupported.                       | Model as a module/struct of `logic` signals.                 |
| `randomize`          | error    | Constraint solver; runtime only.             | Unsupported.                       | Drive inputs from a synthesizable LFSR or a fixed vector.    |
| `new()`              | error    | Object allocation; no hardware.              | Unsupported.                       | Replace with static signal declarations.                      |
| queue (`[$]`)        | error    | Unbounded FIFO; no fixed hardware.           | Unsupported.                       | Use a fixed-depth FIFO module.                                |
| `string`             | error    | Variable-length; no hardware.                | Unsupported.                       | Use a fixed-width byte array / fixed-length char storage.     |
| `chandle`            | error    | DPI/pointer; no hardware.                    | Unsupported.                       | Remove; replace with an integer ID.                           |

## 3. Synthesis-correctness

| Construct                              | Severity | Why                                                  | Emulator-config option | Synthesizable rewrite                                                |
|----------------------------------------|----------|------------------------------------------------------|------------------------|----------------------------------------------------------------------|
| inferred latch (incomplete `if/else`)  | warning  | Missing branch holds value -> latch.                  | Emulators latch-prone; some warn. | Add the `else` branch to assign every output.                       |
| inferred latch (missing `case`/`default`) | warning | Uncovered case holds value -> latch.               | As above.              | Add `default` assigning every output.                                |
| multi-driver net                       | warning  | Two drivers on one net -> X / contention.            | Some flows flag it.   | Drive each net from exactly one `always` block.                      |
| blocking (`=`) in clocked block        | warning  | Blocking in sequential logic -> race / wrong order.  | As above.              | Use nonblocking (`<=`) in clocked `always_ff`.                       |

## 4. Structural / port

| Construct                          | Severity | Why                                              | Emulator-config option | Synthesizable rewrite                                         |
|------------------------------------|----------|--------------------------------------------------|------------------------|---------------------------------------------------------------|
| `generate` misuse                  | note     | Mis-scoped generate can break synthesis.          | Flow-dependent.        | Place `generate`/`endgenerate` correctly; use `genvar`.       |
| `real`/`time` parameter            | error    | Non-synthesizable param type.                    | Unsupported.           | Use integer parameters.                                       |
| port width mismatch                | warning  | Width mismatch truncates / zero-extends.          | Some flows warn.       | Match port widths exactly at instantiation.                   |

## Notes

- The allowlist (`docs/agents/emulation-allowlist.md`) is the only per-project
  override: a listed construct's Finding downgrades to `note`.
- This is the generic IEEE 1800 synthesizable subset. Vendor-specific accepted
  constructs go in the allowlist, not here.
