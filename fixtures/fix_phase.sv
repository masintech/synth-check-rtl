// Fix-phase fixture for synth-check-rtl — pairs behavioral constructs with
// their expected synthesizable rewrites. Each item below is requested ONE AT A
// TIME; the skill generates the rewrite only for the asked item.
//
// The rewrites live in fixtures/fix_phase.expected.md as the source of truth.

module fix_phase (
    input  logic clk,
    input  logic rst_n,
    input  logic a,
    output logic q
);
    // Item 1 — behavioral: #delay (remove; drive from clock edge).
    initial begin
        #10;
        q = 1'b1;
    end

    // Item 2 — behavioral: wait (replace with edge detection).
    always begin
        wait(a);
        q = 1'b1;
    end

endmodule
