# Synthesizable RTL — Rules & Canonical Forms

Disclosed reference for `synth-check-rtl`. Consult this when **classifying a
synthesis-correctness Finding** (is this a valid async reset, or logic on reset?
is this a clock-domain crossing? a latch?) and when **producing a synthesizable
rewrite** in the Fix phase. The canonical example code lives here; `CONSTRUCTS.md`
carries only the verdict and a one-line rewrite per construct.

**Source:** Adi Teman · https://www.youtube.com/watch?v=BIqLk23hE90 · 2025-04-09

---

Three "unforgivable rules" for synthesizable Verilog/SystemVerilog RTL:
(1) no logic on reset or clock, (2) no latch inference, (3) strict separation
of sequential and combinational logic.

## Core concepts

- **RTL (Register Transfer Logic)** — a sequential design passing data between
  registers with combinational logic between them. Only a subset of the HDL is
  synthesizable.
- **Glitch** — a temporary spurious output pulse from unequal combinational path
  delays. **Glitches on clock or reset are catastrophic** — unwanted sampling or
  accidental resets.
- **State of a design** — the minimum set of variables (registers + primary
  inputs) needed to determine all values. All registers form the state; FSM
  states are a small subset.

## Rule 1 — No logic on reset or clock

Never place combinational logic on reset or clock signals.

Bad — logic on reset (`in` is non-constant):
```verilog
always @(posedge clk or negedge reset) begin
    if (!reset)
        in_sampled <= in;   // non-constant on reset!
    else
        in_sampled <= in_sampled;
end
```
Correct — reset only to a constant; sample the input in the combinational block:
```verilog
always @(posedge clk or negedge reset) begin
    if (!reset) begin
        state      <= INIT;
        in_sampled <= '0;   // constant 0
    end else begin
        state      <= next_state;
        in_sampled <= next_in;
    end
end
always @* begin
    next_in    = in_sampled;   // default
    next_state = state;
    if (state == INIT) begin
        next_in    = in;
        next_state = START;
    end
end
```

**No clock-domain crossings (CDC)** — never let a path cross from one
asynchronous clock domain to another without a synchroniser:
```verilog
// BAD: a driven by clk1, used combinationally, sampled by clk2
always @(posedge clk1) a <= next_a;
always @(posedge clk2) b <= next_b;
always @*        next_b = a;   // clock domain crossing
```

## Rule 2 — Do not infer latches

A latch is inferred when a combinational block does not assign an LHS signal for
all conditions. Causes: `if` without `else`; missing `case` items with no
`default`; `if/else` or `case` not assigning all LHS signals.

```verilog
always @* begin
    case (state)
        START:  next_state = RUN;
        FINISH: begin
            next_state = IDLE;
            finished   = 1;   // finished not assigned when state==START
        end
    endcase
end
```
Workaround — default assignments at the top of the `always @*`:
```verilog
always @* begin
    next_state = IDLE;
    finished   = 0;
    case (state)
        START:  next_state = RUN;
        FINISH: begin next_state = IDLE; finished = 1; end
    endcase
end
```
Use `always @*` (or `always_comb`) so the sensitivity list can't drift and cause
simulation/synthesis mismatches.

## Rule 3 — Separate sequential and combinational logic

- Sequential → `always @(posedge clk or negedge reset)` — maps to a flip-flop.
- Combinational → `always @*` or `assign`.
- Never mix combinational logic inside a sequential block (except simple enable
  flops, which are standard cells).

Bad (style) — adder and MUX inside a sequential block. Note this is not a
correctness bug: `count <= count + 1` synthesizes fine (the adder infers
directly on the flop's D-input) — a plain up/down counter written this way is
a normal, working design. Flag it as `note` (optional refactor), not `warning`;
the concern is readability and keeping the register boundary explicit as the
combinational logic grows, not broken hardware:
```verilog
always @(posedge clk or negedge reset) begin
    if (!reset) count <= 0;
    else begin
        if (state == COUNT_UP)   count <= count + 1;
        else if (state == COUNT_DOWN) count <= count - 1;
    end
end
```
Preferred — sequential registers; combinational computes next_count + enable:
```verilog
always @(posedge clk or negedge reset) begin
    if (!reset)         count <= 0;
    else if (count_enable) count <= next_count;
end
always @* begin
    next_count   = count;   // default
    count_enable = 0;
    case (state)
        COUNT_UP:   begin next_count = count + 1; count_enable = 1; end
        COUNT_DOWN: begin next_count = count - 1; count_enable = 1; end
    endcase
end
```

**Multi-driven nets** — a signal must be assigned in exactly one `always` block
or `assign`:
```verilog
// BAD: x driven from two always blocks
always @* x = a & b;
always @* x = c | d;
```

## Checklist

- [ ] Clock and reset never appear on the RHS of `always @*` or `assign`
- [ ] No clock-domain crossings
- [ ] Every `if` has an `else`; every `case` has a `default` or full coverage
- [ ] All LHS signals in combinational blocks are assigned for every condition
- [ ] Each signal is assigned in exactly one `always` block or `assign`
- [ ] All combinational sensitivity lists use `always @*` (or `always_comb`)
- [ ] Sequential blocks use `posedge clk or negedge reset` and no extra logic
- [ ] No combinational loops (check synthesis warnings)

## See Also

- Digital VLSI Design — FSM Coding
- Clock Domain Crossing Techniques
- Verilog vs SystemVerilog for Synthesis
