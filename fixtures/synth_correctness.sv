// Fixture for synth-check-rtl — synthesis-correctness issues (warnings).
// The inferred-latch and blocking-in-clocked-block cases here are SEMANTIC:
// flagged by reasoning against SYNTH-RULES.md, not by pattern. The pattern-level
// expected-Findings manifest for this fixture is therefore empty.
module synth_correctness (
    input  logic clk,
    input  logic a,
    input  logic sel,
    output logic q,
    output logic r
);
    // Inferred latch: missing else -> q holds value -> latch (semantic).
    always @(*) begin
        if (sel) q = a;
    end

    // Blocking assignment in a clocked block -> race / wrong order (semantic).
    always_ff @(posedge clk) begin
        r = a;
    end

endmodule
