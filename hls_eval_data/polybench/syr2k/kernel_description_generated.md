Kernel Description:
The `kernel_syr2k` design is a high-level synthesis implementation of the symmetric rank 2k update algorithm from the BLAS (Basic Linear Algebra Subprograms) library. It performs a symmetric rank 2k update on a matrix `C` using matrices `A` and `B` and scalars `alpha` and `beta`. The output `C_out` is stored in place of the input matrix `C`. The matrix `C` is stored as a triangular matrix in BLAS, and the result is also triangular.

It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A, B$: $N \times M$ matrices
- $C$: $N \times N$ symmetric matrix

and gives the following as output:

- $C_{out}$: $N \times N$ matrix, where $C_{out} = \alpha AB^T + \alpha BA^T + \beta C$

Note that the output $C_{out}$ is to be stored in place of the input array $C$. The matrix $C$ is stored as a triangular matrix in BLAS, and the result is also triangular. The configurations used are $TRANS = 'N'$ and $UPLO = 'L'$, meaning the $A$ matrix is not transposed, and the lower triangular part of the matrix $C$ is used.

---

Top-Level Function: `kernel_syr2k`

Complete Function Signature of the Top-Level Function:
`void kernel_syr2k(double alpha, double beta, double C[30][30], double A[30][20], double B[30][20]);`

Inputs:
- `alpha`: a scalar value of type `double` representing the scaling factor for the matrix product `AB^T` and `BA^T`.
- `beta`: a scalar value of type `double` representing the scaling factor for the matrix `C`.
- `C`: a symmetric matrix of size `30x30` stored as a triangular matrix in BLAS, with elements of type `double`.
- `A`: a matrix of size `30x20` with elements of type `double`.
- `B`: a matrix of size `30x20` with elements of type `double`.

Outputs:
- `C_out`: a symmetric matrix of size `30x30` stored in place of the input matrix `C`, with elements of type `double`.

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used to represent the elements of the matrices `A`, `B`, and `C`, as well as the scalars `alpha` and `beta`.

Sub-Components:
- None