// Fixture for synth-check-rtl — structural / port issues.
module structural_port
#(
    parameter real GAIN = 1.0   // behavioral: real parameter
) (
    input  logic [7:0] in,
    output logic [3:0] out      // port-width mismatch at the instance below
);
    sub u_sub (
        .in  (in),              // 8-bit driving 4-bit -> width mismatch
        .out (out)
    );
endmodule

module sub (input logic [3:0] in, output logic [3:0] out);
    assign out = in;
endmodule
