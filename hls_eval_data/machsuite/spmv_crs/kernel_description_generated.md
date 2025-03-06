Kernel Description:
The Sparse Matrix-Vector Multiplication (SpMV) kernel is a fundamental operation in linear algebra and machine learning. This design takes advantage of the Compressed Row Storage (CRS) format to efficiently store and process sparse matrices. The algorithm iterates over the rows of the matrix, computing the dot product of each row with a given input vector and storing the results in an output vector. The CRS format is used to store the sparse matrix, where the non-zero values are stored in the `val` array, the column indices of the non-zero values are stored in the `cols` array, and the row delimiters are stored in the `rowDelimiters` array. The input vector is stored in the `vec` array, and the output vector is stored in the `out` array. The kernel uses two nested loops to compute the dot product of each row with the input vector. The outer loop iterates over the rows of the matrix, and the inner loop iterates over the non-zero elements of each row. The dot product is computed using the formula: $y_i = \sum_{j=0}^{N-1} A_{ij} \cdot x_j$, where $y_i$ is the $i^{th}$ element of the output vector, $A_{ij}$ is the $(i,j)^{th}$ element of the sparse matrix, and $x_j$ is the $j^{th}$ element of the input vector.

---

Top-Level Function: `spmv`

Complete Function Signature of the Top-Level Function:
`void spmv(TYPE val[NNZ], int32_t cols[NNZ], int32_t rowDelimiters[N + 1], TYPE vec[N], TYPE out[N])`

Inputs:
- `val`: an array of `NNZ` elements of type `TYPE` (double precision floating point), representing the non-zero values of the sparse matrix.
- `cols`: an array of `NNZ` elements of type `int32_t`, representing the column indices of the non-zero values in the sparse matrix.
- `rowDelimiters`: an array of `N+1` elements of type `int32_t`, representing the row delimiters of the sparse matrix in CRS format.
- `vec`: an array of `N` elements of type `TYPE` (double precision floating point), representing the input vector.

Outputs:
- `out`: an array of `N` elements of type `TYPE` (double precision floating point), representing the output vector resulting from the SpMV operation.

Important Data Structures and Data Types:
- `TYPE`: a double precision floating point data type, used to represent the non-zero values of the sparse matrix and the input/output vectors.
- `int32_t`: a 32-bit signed integer data type, used to represent the column indices and row delimiters of the sparse matrix.

Sub-Components:
- `spmv_1`: a loop that iterates over the rows of the sparse matrix, computing the dot product of each row with the input vector.
  - Signature: `for (i = 0; i < N; i++)`
  - Details: This loop iterates over the rows of the sparse matrix, and for each row, it computes the dot product with the input vector using the inner loop `spmv_2`.
- `spmv_2`: a nested loop that iterates over the non-zero elements of each row, computing the dot product of the row with the input vector.
  - Signature: `for (j = tmp_begin; j < tmp_end; j++)`
  - Details: This loop iterates over the non-zero elements of each row, and for each non-zero element, it computes the product of the element with the corresponding element of the input vector and accumulates the result in the `sum` variable.