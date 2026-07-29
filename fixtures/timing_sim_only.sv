// Fixture for synth-check-rtl — timing & sim-only behavioral constructs.
// Expected: every behavioral construct below is flagged as a Finding (error).
// The synthesizable baseline must NOT be flagged.
module timing_sim_only_fixture (
    input  logic clk,
    input  logic rst_n,
    output logic done
);
    // Synthesizable baseline (must NOT be flagged).
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) done <= 1'b0;
        else        done <= 1'b1;
    end

    realtime rt;                  // behavioral: real/time (realtime variant)
    logic dly_out;
    assign dly_out = #2 clk;      // behavioral: #delay on assign (one Finding, not two)

    // response time budget note — must NOT be flagged: "time" inside a comment.
    logic resp_time;              // must NOT be flagged: "time" inside an identifier

    initial begin
        #10;                          // behavioral: #delay
        $display("sim only");         // behavioral: $display
        wait(rst_n);                  // behavioral: wait
    end

    always begin
        forever begin                 // behavioral: forever
            clk_test = ~clk_test;
        end
    end

endmodule
