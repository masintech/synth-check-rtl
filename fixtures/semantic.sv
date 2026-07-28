// Fixture for synth-check-rtl — semantic (reasoning) constructs (ticket 08).
// These CANNOT be caught by pattern; the agent reasons against SYNTH-RULES.md.
// Expected Findings are in semantic.expected.md.

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

endmodule
