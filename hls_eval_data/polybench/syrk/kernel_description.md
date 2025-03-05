Kernel Description:
The `kernel_syrk` design is a high-level synthesis implementation of the symmetric rank-k update (SYRK) algorithm from the Basic Linear Algebra Subprograms (BLAS) library. The SYRK algorithm updates a symmetric matrix `C` with the product of a matrix `A` and its transpose, scaled by a factor `alpha`, and adds the result to `C` scaled by a factor `beta`. The output `C_out` is stored in place of the input matrix `C`. The matrix `C` is stored as a triangular matrix in BLAS, and the result is also triangular.

It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A$: $N \times M$ matrix
- $C$: $N \times N$ symmetric matrix

and gives the following as output:

- $C_{out}$: $N \times N$ matrix, where $C_{out} = \alpha A A^T + \beta C$

Note that the output $C_{out}$ is to be stored in place of the input array $C$. The matrix $C$ is stored as a triangular matrix in BLAS, and the result is also triangular. The configurations used are `TRANS = 'N'` and `UPLO = 'L'` meaning the $A$ matrix is not transposed, and $C$ matrix stores the symmetric matrix as lower triangular matrix.

---

Top-Level Function: `kernel_syrk`

Complete Function Signature of the Top-Level Function:
`void kernel_syrk(double alpha, double beta, double C[30][30], double A[30][20]);`

Inputs:
- `alpha`: a scalar value of type `double` that represents the scaling factor for the matrix product.
- `beta`: a scalar value of type `double` that represents the scaling factor for the input matrix `C`.
- `C`: a symmetric matrix of size `30x30` stored as a lower triangular matrix, with elements of type `double`.
- `A`: a matrix of size `30x20` with elements of type `double`.

Outputs:
- `C_out`: a symmetric matrix of size `30x30` stored as a lower triangular matrix, with elements of type `double`, which is the result of the SYRK operation.

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used to represent the elements of the matrices `C` and `A`.
- `C` and `A` matrices: stored as 2D arrays of `double` elements, with sizes `30x30` and `30x20`, respectively.

Sub-Components:
- None