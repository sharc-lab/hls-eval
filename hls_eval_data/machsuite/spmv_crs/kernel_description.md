## spmv_crs

An implementation of the Sparse Matrix-Vector Multiplication (SpMV) algorithm, a fundamental operation in linear algebra and machine learning. The design takes advantage of the Compressed Row Storage (CRS) format to efficiently store and process sparse matrices. The algorithm iterates over the rows of the matrix, computing the dot product of each row with a given input vector and storing the results in an output vector.

Top-Level Function: `spmv`

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
- `spmv_2`: a nested loop that iterates over the non-zero elements of each row, computing the dot product of the row with the input vector.