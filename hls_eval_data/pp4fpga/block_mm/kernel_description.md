Kernel Description:
The `blockmatmul` kernel is designed to perform block matrix multiplication using a streaming interface. The kernel processes matrices in blocks to optimize memory usage and improve performance on hardware accelerators. The algorithm reads blocks of rows from matrix A and blocks of columns from matrix B, computes the partial product, and writes the result to a partial output matrix. The kernel uses a dataflow architecture to overlap data loading, computation, and output writing, which is enabled by the `#pragma HLS DATAFLOW` directive. The kernel is parameterized by the matrix size (`SIZE`) and block size (`BLOCK_SIZE`), which are set to 8 and 4, respectively. The kernel handles the loading of matrix A rows only when necessary, determined by the iteration counter `it`. This optimization reduces unnecessary data transfers and improves efficiency.

The kernel processes the matrices in a block-wise manner, where each block is of size `BLOCK_SIZE x BLOCK_SIZE`. The partial product is computed using a nested loop structure, where the outer loop iterates over the columns of matrix B, and the inner loops perform the element-wise multiplication and accumulation. The result is stored in a local array `AB`, which is then written to the output matrix `ABpartial`.

The kernel uses the `hls::stream` data structure to handle the input and output data streams, which allows for efficient data transfer between the kernel and the host. The `blockvec` structure is used to represent a block of elements from matrix A or B, and the `blockmat` structure is used to represent the partial output matrix.

---

Top-Level Function: `blockmatmul`

Complete Function Signature of the Top-Level Function:
`void blockmatmul(hls::stream<blockvec> &Arows, hls::stream<blockvec> &Bcols, blockmat &ABpartial, int it);`

Inputs:
- `Arows`: A stream of `blockvec` elements representing blocks of rows from matrix A. Each `blockvec` contains `BLOCK_SIZE` elements of type `DTYPE`.
- `Bcols`: A stream of `blockvec` elements representing blocks of columns from matrix B. Each `blockvec` contains `BLOCK_SIZE` elements of type `DTYPE`.
- `ABpartial`: A reference to a `blockmat` structure where the partial product of the block multiplication will be stored. The `blockmat` structure contains a `BLOCK_SIZE x BLOCK_SIZE` matrix of type `DTYPE`.
- `it`: An integer representing the current iteration count, used to determine when to load new rows from matrix A.

Outputs:
- `ABpartial`: The partial product of the block multiplication is stored in the `out` field of the `blockmat` structure. The `out` field is a `BLOCK_SIZE x BLOCK_SIZE` matrix of type `DTYPE`.

Important Data Structures and Data Types:
- `blockvec`: A structure representing a block of elements from matrix A or B. It contains an array `a` of size `BLOCK_SIZE` with elements of type `DTYPE`.
- `blockmat`: A structure representing the partial output matrix. It contains a 2D array `out` of size `BLOCK_SIZE x BLOCK_SIZE` with elements of type `DTYPE`.

Sub-Components:
- None