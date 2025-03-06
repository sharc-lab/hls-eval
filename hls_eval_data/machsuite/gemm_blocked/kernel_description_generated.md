Kernel Description:
The `bbgemm` kernel implements the General Matrix-Matrix Multiplication (GEMM) algorithm, optimized for cache performance using a blocked algorithm. The design takes advantage of spatial locality by dividing the input matrices into smaller blocks, reducing memory access patterns and improving data reuse. The kernel performs a matrix-matrix multiplication operation, computing the product of two input matrices `m1` and `m2` and storing the result in the output matrix `prod`. The blocked algorithm is based on the paper "The cache performance and optimizations of blocked algorithms" by M. D. Lam, E. E. Rothberg, and M. E. Wolf, presented at ASPLOS 1991. The algorithm can be represented by the following equation: 
\[ C = AB \]
where $C$ is the output matrix, $A$ and $B$ are the input matrices, and the multiplication is performed element-wise. The blocked algorithm can be further represented as:
\[ C_{ij} = \sum_{k=0}^{N-1} A_{ik}B_{kj} \]
where $N$ is the number of elements in the matrices, and $i$, $j$, and $k$ are the row, column, and block indices, respectively.

The kernel uses four nested loops to iterate over the blocks of the input matrices: `loopjj` and `loopkk` iterate over the blocks of the input matrices, while `loopi` and `loopk` perform the actual matrix-matrix multiplication operation. The innermost loop, `loopj`, accumulates the partial products of the matrix-matrix multiplication operation. The kernel uses a block size of 8, which is defined by the `block_size` constant. The input matrices are divided into blocks of size `block_size x block_size`, and the kernel performs the matrix-matrix multiplication operation on each block.

The kernel uses the following data structures and data types:
- `TYPE`: a double precision floating-point data type, used to represent the elements of the input and output matrices.
- `block_size`: an integer constant defining the size of the blocks used in the blocked algorithm.
- `row_size` and `col_size`: integer constants defining the size of the input matrices.
- `N`: an integer constant representing the total number of elements in the input matrices.

The kernel does not have any sub-components that are explicitly listed as separate C++ functions in the code.

---

Top-Level Function: `bbgemm`

Complete Function Signature of the Top-Level Function:
`void bbgemm(TYPE m1[N], TYPE m2[N], TYPE prod[N]);`

Inputs:
- `m1`: a 2D matrix of size `N x N` (where `N = row_size * col_size`) containing the first input matrix, stored in row-major order with each element of type `TYPE` (double precision floating-point).
- `m2`: a 2D matrix of size `N x N` containing the second input matrix, stored in row-major order with each element of type `TYPE` (double precision floating-point).

Outputs:
- `prod`: a 2D matrix of size `N x N` containing the product of the input matrices, stored in row-major order with each element of type `TYPE` (double precision floating-point).

Important Data Structures and Data Types:
- `TYPE`: a double precision floating-point data type, used to represent the elements of the input and output matrices.
- `block_size`: an integer constant defining the size of the blocks used in the blocked algorithm, set to 8.
- `row_size` and `col_size`: integer constants defining the size of the input matrices, set to 64.
- `N`: an integer constant representing the total number of elements in the input matrices, calculated as `row_size * col_size`.

Sub-Components:
- None