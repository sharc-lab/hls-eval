Kernel Description:
The `kernel_symm` design is a high-level synthesis implementation of the symmetric matrix multiplication algorithm from the Basic Linear Algebra Subprograms (BLAS) library. It takes five inputs: two scalar values `alpha` and `beta`, and three matrices `A`, `B`, and `C`. The output is a modified matrix `C` that stores the result of the symmetric matrix multiplication. The algorithm performs the operation `C = alpha * A * B + beta * B * C`, where `A` is a symmetric matrix stored as a lower triangular matrix.

It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A$: $M \times M$ symmetric matrix
- $B, C$: $M \times N$ matrices

and gives the following as output:

- $C_{\text{out}}$: $M \times N$ matrix, where $C_{\text{out}} = \alpha AB + \beta BC$

Note that the output $C_{\text{out}}$ is to be stored in place of the input array $C$. The matrix $A$ is stored as a triangular matrix in BLAS. The configuration used are `SIDE = 'L'` and `UPLO = 'L'`, meaning the multiplication is from the left, and the symmetric matrix is stored as a lower triangular matrix.

---

Top-Level Function: `kernel_symm`

Complete Function Signature of the Top-Level Function:
`void kernel_symm(double alpha, double beta, double C[20][30], double A[20][20], double B[20][30]);`

Inputs:
- `alpha`: a scalar value that represents the scaling factor for the matrix multiplication
- `beta`: a scalar value that represents the scaling factor for the matrix addition
- `C`: a `M x N` matrix that stores the output result
- `A`: a `M x M` symmetric matrix stored as a lower triangular matrix
- `B`: a `M x N` matrix that is used for the matrix multiplication

Outputs:
- `C`: a `M x N` matrix that stores the output result of the symmetric matrix multiplication

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used for the matrix elements
- `M x N` matrix: a 2D array of `double` values with `M` rows and `N` columns
- `M x M` symmetric matrix: a 2D array of `double` values with `M` rows and `M` columns, stored as a lower triangular matrix

Sub-Components:
- None