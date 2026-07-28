// Fixture for synth-check-rtl — SV testbench-isms in RTL (must be flagged).
module sv_testbench_isms (
    input  logic clk,
    input  logic [7:0] in,
    output logic [7:0] out
);
    int dyn_arr[];              // behavioral: dynamic array
    int assoc_arr[string];      // behavioral: associative array
    logic [7:0] queue [$];      // behavioral: queue

    class Cfg;                  // behavioral: class
        int v;
    endclass

    logic [7:0] reg_array [0:15];

    always_ff @(posedge clk) begin
        out <= in;
    end

endmodule
