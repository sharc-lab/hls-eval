Kernel Description:
The `linear` kernel performs a linear transformation on the input data, followed by an optional ReLU activation function. The transformation is defined by a weight matrix and a bias vector. The kernel is designed to process the input data in parallel to optimize performance. The input data is a vector of size `DIM_IN`, the weight matrix is of size `DIM_OUT x DIM_IN`, and the bias vector is of size `DIM_OUT`. The output is a vector of size `DIM_OUT`. The kernel uses array partitioning and pipelining to achieve high throughput. The `PARALLEL` parameter defines the degree of parallelism, allowing multiple output elements to be computed in parallel. The `RELU` macro determines whether the ReLU activation function is applied to the output.

The kernel processes the input data in chunks of size `PARALLEL`. For each chunk, it computes the corresponding output elements by performing matrix-vector multiplication and adding the bias. If the `RELU` macro is set to 1, it applies the ReLU function to each output element, setting negative values to zero. The use of `#pragma HLS ARRAY_PARTITION` directives optimizes memory access patterns, while `#pragma HLS PIPELINE` and `#pragma HLS UNROLL` directives enable efficient parallel execution.

---

Top-Level Function: `linear`

Complete Function Signature of the Top-Level Function:
`void linear(FM_TYPE input[DIM_IN], WT_TYPE weight[DIM_OUT][DIM_IN], WT_TYPE bias[DIM_OUT], FM_TYPE output[DIM_OUT]);`

Inputs:
- `input`: A vector of size `DIM_IN` (32) containing the input features. Each element is of type `FM_TYPE` (float).
- `weight`: A matrix of size `DIM_OUT x DIM_IN` (16 x 32) containing the weights for the linear transformation. Each element is of type `WT_TYPE` (float).
- `bias`: A vector of size `DIM_OUT` (16) containing the bias terms for the linear transformation. Each element is of type `WT_TYPE` (float).

Outputs:
- `output`: A vector of size `DIM_OUT` (16) containing the transformed output features. Each element is of type `FM_TYPE` (float).

Important Data Structures and Data Types:
- `FM_TYPE`: A floating-point data type (float) used for input and output features.
- `WT_TYPE`: A floating-point data type (float) used for weights and biases.

Sub-Components:
- None