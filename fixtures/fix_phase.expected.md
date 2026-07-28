# Fix-phase expected rewrites — fixtures/fix_phase.sv

The expected **synthesizable** rewrite for each behavioral construct, requested
one item at a time. These are the source of truth for ticket 03's fix phase: the
skill must produce exactly these rewrites (the decision-rich parts only).

## Item 1 — `#delay` (line 11)

Behavioral:
```systemverilog
initial begin
    #10;
    q = 1'b1;
end
```

Synthesizable rewrite (key signal: clocked reset logic):
```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else        q <= 1'b1;
end
```
Why: `#delay` and `initial` have no hardware; move init into a clocked reset
branch driven by the clock edge. (Drawn from the `#delay` and `initial` entries of
CONSTRUCTS.md.)

## Item 2 — `wait(a)` (line 17)

Behavioral:
```systemverilog
always begin
    wait(a);
    q = 1'b1;
end
```

Synthesizable rewrite (key signal: level sampled on the clock edge):
```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else        q <= a;   // level condition sampled on the clock edge
end
```
Why: `wait` is level-sensitive with no hardware; replace with edge detection on
the clock. (Drawn from the `wait` entry of CONSTRUCTS.md.)
