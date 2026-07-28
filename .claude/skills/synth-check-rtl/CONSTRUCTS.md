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
| `#delay`    | error    | No timing; synthesis ignores or drops it.            | Some emulators accept `#delay` in a sim-only region if isolated and pruned. | `always_ff @(posedge clk or negedge rst_n) if (!rst_n) q<=0; else q<=1;` — drive from the clock edge, not a delay. <!-- name:#delay | pattern:#\d+ -->
| `$display` and other system tasks (`$monitor`, `$fwrite`, `$finish`, ...) | error | System task; no hardware. | Emulators often elide system tasks if the flow strips them. | Remove from RTL; emit state via a synthesizable debug port. <!-- name:$display | pattern:\$display\b -->
| `wait(sig)` | error    | Level-sensitive wait has no hardware.                | Few emulators support it; usually rejected.     | `always_ff @(posedge clk or negedge rst_n) if (!rst_n) q<=0; else q<=sig;` — sample the level on the clock edge. <!-- name:wait | pattern:\bwait\s*\( -->
| `forever`   | error    | Unbounded loop; no hardware termination.             | Unsupported in synthesis.                       | Drive from a clocked `always_ff` with an explicit enable/condition. <!-- name:forever | pattern:\bforever\b -->
| `initial`   | error    | Simulation-only initialization; no reset hardware.  | Emulators accept `initial` for FPGA-style init (some flows). | Move init into a clocked reset branch (`if (!rst_n)`). <!-- name:initial | pattern:\binitial\b -->
| `event`     | error    | Simulation event type; no hardware.                  | Unsupported.                                    | Replace with a wire/logic signal triggered on a clock edge. <!-- name:event | pattern:\bevent\b -->
| `force`/`release` | error | Procedural override; not hardware.             | Used in sim only; emulators reject in RTL.      | Remove; model the override as a mux/select driven by a control signal. <!-- name:force/release | pattern:\b(force|release)\b -->
| `fork`/`join` | error  | Concurrent processes; no hardware parallelism model. | Unsupported.                                  | Serialize into one clocked process, or model as parallel always_ff blocks. <!-- name:fork | pattern:\bfork\b -->
| `disable`   | error    | Procedural process kill; no hardware.               | Unsupported.                                    | Replace with a state-machine exit condition / enable deassert. <!-- name:disable | pattern:\bdisable\b -->
| `deassign`  | error    | Procedural override removal; not hardware.          | Unsupported.                                    | Remove; assign through a single driver with a mux. <!-- name:deassign | pattern:\bdeassign\b -->
| `real`/`time` type | error | Non-synthesizable types.                       | Unsupported.                                    | Use fixed-point integer arithmetic. <!-- name:real/time | pattern:(?<!parameter\s)\b(real|time)\b -->
| `$random`/`$urandom`/`$urandom_range` | error | System random functions; no hardware. | Unsupported. | Drive inputs from a synthesizable LFSR or a fixed/seeded vector. <!-- name:$random | pattern:\$(random|urandom|urandom_range)\b -->
| `#delay` on continuous `assign` (`assign a = #2 b;`) | error | Delay on a continuous assignment; no hardware. | Unsupported. | Remove the delay; insert a register (clocked `always_ff`) for the desired latency. <!-- name:#delay on assign | pattern:\bassign\b.*#\d+ -->

## 2. SV testbench-isms

| Construct            | Severity | Why                                          | Emulator-config option            | Synthesizable rewrite                                        |
|----------------------|----------|----------------------------------------------|------------------------------------|--------------------------------------------------------------|
| dynamic array `[]`   | error    | Heap-allocated; no hardware.                 | Unsupported in RTL.                | Use a fixed-size array with a bounded depth constant. <!-- name:dynamic array | pattern:\w+\s*\[\s*\] -->
| associative array    | error    | Hashed storage; no hardware.                 | Unsupported.                       | Use a fixed-size array indexed by an enumerated/bounded key. <!-- name:associative array | pattern:\b\w+\s*\[[a-zA-Z_]\w*\s*\] -->
| `class`              | error    | OOP; no hardware.                            | Unsupported.                       | Model as a module/struct of `logic` signals. <!-- name:class | pattern:\bclass\b -->
| `randomize`          | error    | Constraint solver; runtime only.             | Unsupported.                       | Drive inputs from a synthesizable LFSR or a fixed vector. <!-- name:randomize | pattern:\brandomize\b -->
| `new()`              | error    | Object allocation; no hardware.              | Unsupported.                       | Replace with static signal declarations. <!-- name:new() | pattern:\bnew\s*\( -->
| queue (`[$]`)        | error    | Unbounded FIFO; no fixed hardware.           | Unsupported.                       | Use a fixed-depth FIFO module. <!-- name:queue | pattern:\[\s*\$ -->
| `string`             | error    | Variable-length; no hardware.                | Unsupported.                       | Use a fixed-width byte array / fixed-length char storage. <!-- name:string | pattern:\bstring\s+ -->
| `chandle`            | error    | DPI/pointer; no hardware.                    | Unsupported.                       | Remove; replace with an integer ID. <!-- name:chandle | pattern:\bchandle\b -->

## 3. Synthesis-correctness

| Construct                              | Severity | Why                                                  | Emulator-config option | Synthesizable rewrite                                                |
|----------------------------------------|----------|------------------------------------------------------|------------------------|----------------------------------------------------------------------|
| inferred latch (incomplete `if/else`)  | warning  | Missing branch holds value -> latch.                  | Emulators latch-prone; some warn. | Add the `else` branch to assign every output. <!-- name:inferred latch | semantic:incomplete-if-else -->
| inferred latch (missing `case`/`default`) | warning | Uncovered case holds value -> latch.               | As above.              | Add `default` assigning every output. <!-- semantic:case-no-default -->
| multi-driver net                       | warning  | Two drivers on one net -> X / contention.            | Some flows flag it.   | Drive each net from exactly one `always` block. <!-- semantic:multi-driver -->
| blocking (`=`) in clocked block        | warning  | Blocking in sequential logic -> race / wrong order.  | As above.              | Use nonblocking (`<=`) in clocked `always_ff`. <!-- semantic:blocking-in-clocked -->
| logic on reset (non-constant RHS)     | warning  | Non-constant sampled on reset -> MUX/logic on reset net; glitch risk. | Some flows accept it. | Reset to a constant only; sample inputs in the combinational block (see SYNTH-RULES Rule 1). <!-- semantic:logic-on-reset -->
| logic on clock                         | warning  | Combinational logic on the clock net -> glitch risk.  | Some flows accept it.  | Clock the register on a clean clock edge; move logic to a separate combinational block. <!-- semantic:logic-on-clock -->
| clock-domain crossing (CDC)            | warning  | Signal from one async clock domain used in another without a synchroniser -> metastability. | Some flows flag CDC. | Insert a synchroniser (dual-flop) at the crossing (see SYNTH-RULES Rule 1). <!-- semantic:cdc -->
| mixed logic in sequential block        | warning  | Combinational cloud inside a sequential block -> breaks direct FF mapping. | Some flows accept it. | Move combinational logic to an `always @*` block; keep the sequential block a clean register (see SYNTH-RULES Rule 3). <!-- semantic:mixed-logic -->
| multi-edge sensitivity (`posedge a or posedge b`) | warning | Two edge sources -> ambiguous FF control; usually a dual-clock hazard. | Rarely supported. | One clock + one async reset only. If two clocks, that's a CDC — use a synchroniser (see SYNTH-RULES Rule 1). <!-- semantic:multi-edge -->

## 4. Structural / port

| Construct                          | Severity | Why                                              | Emulator-config option | Synthesizable rewrite                                         |
|------------------------------------|----------|--------------------------------------------------|------------------------|---------------------------------------------------------------|
| `generate` misuse                  | note     | Mis-scoped generate can break synthesis.          | Flow-dependent.        | Place `generate`/`endgenerate` correctly; use `genvar`. <!-- semantic:generate-misuse -->
| `real`/`time` parameter            | error    | Non-synthesizable param type.                    | Unsupported.           | Use integer parameters. <!-- name:real parameter | pattern:parameter\s+(real|time)\b -->
| port width mismatch                | warning  | Width mismatch truncates / zero-extends.          | Some flows warn.       | Match port widths exactly at instantiation. <!-- semantic:port-width -->

## Notes

- The allowlist (`docs/agents/emulation-allowlist.md`) is the only per-project
  override: a listed construct's Finding downgrades to `note`.
- This is the generic IEEE 1800 synthesizable subset. Vendor-specific accepted
  constructs go in the allowlist, not here.
- Synthesis-correctness rows (logic on reset/clock, CDC, mixed logic,
  multi-edge sensitivity) need semantic judgment — a `posedge clk or negedge
  rst` is a valid async reset, while `posedge a or posedge b` is a dual-clock
  hazard. Classify against [`SYNTH-RULES.md`](SYNTH-RULES.md), not by pattern.
