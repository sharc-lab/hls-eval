Kernel Description:
The `linear_input_stationary` kernel performs a linear transformation on the input data using a weight matrix and a bias vector. The kernel is designed to be efficient by utilizing parallel processing and pipelining. The input data is streamed in chunks of size `PARALLEL`, and the kernel processes these chunks to compute the output. The computation involves matrix-vector multiplication where the input vector is multiplied by the weight matrix and then the bias vector is added. If the `RELU` macro is defined, a ReLU activation function is applied to the output. The kernel uses HLS pragmas to optimize the hardware implementation, including array partitioning and loop unrolling.

The input data is streamed in chunks of size `PARALLEL` to allow parallel processing. The weight matrix is partitioned to enable efficient access during the matrix-vector multiplication. The bias vector and output vector are also partitioned to allow parallel updates. The kernel processes the input data in a pipelined fashion, with each iteration of the outer loop corresponding to a single output element. The inner loop performs the dot product of the input chunk with the corresponding rows of the weight matrix. The results are accumulated and added to the bias to produce the final output. If the `RELU` macro is set to 1, the output is passed through a ReLU activation function, setting any negative values to zero.

---

Top-Level Function: `linear_input_stationary`

Complete Function Signature of the Top-Level Function:
`void linear_input_stationary(hls::stream<array<FM_TYPE, PARALLEL>> &input, WT_TYPE weight[DIM_OUT][DIM_IN], WT_TYPE bias[DIM_OUT], FM_TYPE output[DIM_OUT]);`

Inputs:
- `input`: A stream of arrays of type `FM_TYPE` with size `PARALLEL`. This represents the input data that is streamed into the kernel in chunks of size `PARALLEL`.
- `weight`: A 2D array of type `WT_TYPE` with dimensions `DIM_OUT x DIM_IN`. This represents the weight matrix used in the linear transformation.
- `bias`: An array of type `WT_TYPE` with size `DIM_OUT`. This represents the bias vector added to the result of the matrix-vector multiplication.

Outputs:
- `output`: An array of type `FM_TYPE` with size `DIM_OUT`. This represents the output of the linear transformation after applying the bias and, if enabled, the ReLU activation function.

Important Data Structures and Data Types:
- `array<FM_TYPE, PARALLEL>`: A fixed-size array of type `FM_TYPE` with size `PARALLEL`. This is used to represent chunks of the input data that are streamed into the kernel.
- `FM_TYPE`: A floating-point type (typically `float`) used to represent the elements of the input data and the output.
- `WT_TYPE`: A floating-point type (typically `float`) used to represent the elements of the weight matrix and the bias vector.

Sub-Components:
- None