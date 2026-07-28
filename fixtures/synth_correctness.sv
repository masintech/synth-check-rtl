// Fixture for synth-check-rtl — synthesis-correctness issues (warnings).
module synth_correctness (
    input  logic clk,
    input  logic a,
    input  logic sel,
    output logic q,
    output logic r
);
    // Inferred latch: missing else -> q holds value -> latch.
    always @(*) begin
        if (sel) q = a;
    end

    // Blocking assignment in a clocked block -> race / wrong order.
    always_ff @(posedge clk) begin
        r = a;                 // behavioral: blocking in clocked block
    end

endmodule
