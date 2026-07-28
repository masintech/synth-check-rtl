// Fixture for synth-check-rtl — semantic (reasoning) constructs (ticket 08).
// These CANNOT be caught by pattern; the agent reasons against SYNTH-RULES.md.
// Expected Findings are in semantic.expected.md. Line numbers below are stable;
// edit both files together.

module semantic (
    input  logic clk,
    input  logic clkB,        // a second, independent clock for the CDC case
    input  logic rst_n,
    input  logic a,
    input  logic b,
    input  logic in,
    input  logic sel,
    output logic q,
    output logic r,
    output logic s,
    output logic cdc_out
);
    // VALID async reset — must NOT be flagged (SYNTH-RULES Rule 1).
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= 1'b0;
        else        q <= a;
    end

    // multi-edge sensitivity / dual-clock hazard — FLAG (semantic:multi-edge).
    // Two edge sources (posedge clk and posedge clkB) is not a real flop.
    always_ff @(posedge clk or posedge clkB) begin
        r <= b;
    end

    // logic on reset (non-constant RHS on reset) — FLAG (semantic:logic-on-reset).
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) cdc_out <= in;   // non-constant sampled on reset
    end

    // clock-domain crossing — FLAG (semantic:cdc).
    // a is sampled by clk in the first block, then used in the clkB domain.
    logic a_sync;
    always_ff @(posedge clk)  a_sync <= a;
    always_ff @(posedge clkB) cdc_out <= a_sync;   // CDC: clk -> clkB, no synchroniser

    // inferred latch (incomplete if/else) — FLAG (semantic:incomplete-if-else).
    // sel true assigns s; sel false holds s -> latch.
    always @* begin
        if (sel) s = a;
    end

    // logic on clock — FLAG (semantic:logic-on-clock).
    // A gated/derived clock (clk & a) drives the edge — combinational logic on the clock net.
    always_ff @(posedge (clk & a)) begin
        s <= b;
    end

    // mixed logic in a sequential block — FLAG (semantic:mixed-logic).
    // An adder/MUX inside the clocked block instead of in a combinational cloud.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) r <= 1'b0;
        else        r <= (sel) ? (a + b) : (a - b);   // combinational cloud in sequential block
    end

    // multi-driver net — FLAG (semantic:multi-driver).
    // s is driven from two always blocks (also the latch above) -> contention.
    always_ff @(posedge clk) s <= a;

    // blocking in clocked block — FLAG (semantic:blocking-in-clocked).
    always_ff @(posedge clk) begin
        r = a;   // blocking assignment in a clocked block
    end

    // inferred latch (missing case/default) — FLAG (semantic:case-no-default).
    // sel is not fully decoded -> holds value -> latch.
    always @* begin
        case (sel)
            1'b1: s = a;
        endcase
    end

    // generate misuse — FLAG (semantic:generate-misuse).
    // `for` inside `generate` without a `genvar` is a common mis-scoping error.
    for (i = 0; i < 4; i = i + 1) begin : gen_loop
        assign q[i] = a;
    end

    // port width mismatch — FLAG (semantic:port-width).
    // 8-bit `in` drives the 4-bit `q[i]` slice above without width match — a
    // structural port-width mismatch at the implicit connection.

endmodule
