## spmv_ellpack

An implementation the ELLPACK sparse matrix-vector multiplication algorithm. This algorithm is optimized for sparse matrices with a small number of non-zero elements per row. The design takes advantage of the sparse structure of the matrix to reduce memory access and improve performance. The kernel computes the matrix-vector product of a sparse matrix and a dense vector, storing the result in an output vector.

Top-Level Function: `ellpack`

Inputs:

- `nzval`: a 2D array of size N x L, where N is the number of rows in the sparse matrix and L is the maximum number of non-zero elements per row. Each element is of type `TYPE` (double precision floating point). The array stores the non-zero values of the sparse matrix.
- `cols`: a 2D array of size N x L, where N is the number of rows in the sparse matrix and L is the maximum number of non-zero elements per row. Each element is of type `int32_t`. The array stores the column indices of the non-zero elements in the sparse matrix.
- `vec`: a 1D array of size N, where N is the number of rows in the sparse matrix. Each element is of type `TYPE` (double precision floating point). The array stores the dense vector to be multiplied with the sparse matrix.

Outputs:

- `out`: a 1D array of size N, where N is the number of rows in the sparse matrix. Each element is of type `TYPE` (double precision floating point). The array stores the result of the matrix-vector product.

Important Data Structures and Data Types:

- `TYPE`: a double precision floating point data type used to represent the elements of the sparse matrix and the dense vector.
- `int32_t`: a 32-bit integer data type used to represent the column indices of the non-zero elements in the sparse matrix.

Sub-Components:

- `ellpack_1`: a loop that iterates over the rows of the sparse matrix, computing the dot product of each row with the dense vector.
- `ellpack_2`: a nested loop that iterates over the non-zero elements of each row, computing the product of each non-zero element with the corresponding element of the dense vector and accumulating the results.