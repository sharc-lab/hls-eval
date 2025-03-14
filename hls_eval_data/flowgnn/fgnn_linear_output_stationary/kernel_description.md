Kernel Description:
The `linear_output_stationary` kernel performs a linear transformation on the input data using a weight matrix and a bias vector. The kernel is designed to be efficient by utilizing parallel processing and pipelining. The input data is stationary, meaning it is not moved during the computation, while the output is computed in parallel slices. The kernel supports an optional ReLU activation function, which is applied to the output if the `RELU` macro is set to 1. The input data is partitioned to allow parallel access, and the weight matrix is partitioned both cyclically and completely to optimize memory access patterns. The bias vector is also partitioned cyclically to match the parallel processing requirements.

The kernel processes the input data in chunks defined by the `PARALLEL` factor, which determines the number of output elements computed in parallel. For each chunk, the kernel computes the dot product of the input vector with the corresponding rows of the weight matrix, adds the bias, and applies the ReLU activation if enabled. The results are then written to an output stream in slices of size `PARALLEL`.

---

Top-Level Function: `linear_output_stationary`

Complete Function Signature of the Top-Level Function:
`void linear_output_stationary(FM_TYPE input[DIM_IN], WT_TYPE weight[DIM_OUT][DIM_IN], WT_TYPE bias[DIM_OUT], hls::stream<array<FM_TYPE, PARALLEL>> &output);`

Inputs:
- `input`: An array of `FM_TYPE` (float) with a size of `DIM_IN` (32). This array represents the input feature map to the linear layer.
- `weight`: A 2D array of `WT_TYPE` (float) with dimensions `DIM_OUT` (16) x `DIM_IN` (32). This array represents the weight matrix of the linear layer.
- `bias`: An array of `WT_TYPE` (float) with a size of `DIM_OUT` (16). This array represents the bias vector of the linear layer.

Outputs:
- `output`: A stream of `array<FM_TYPE, PARALLEL>` (array of float with size 4). This stream outputs the computed results in parallel slices of size `PARALLEL`.

Important Data Structures and Data Types:
- `array<FM_TYPE, PARALLEL>`: A fixed-size array of `FM_TYPE` (float) with a size of `PARALLEL` (4). This data structure is used to store and transmit parallel slices of the output.

Sub-Components:
- None