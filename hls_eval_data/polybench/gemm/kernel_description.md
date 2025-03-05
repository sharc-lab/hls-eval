Kernel Description:
The `kernel_gemm` design is a high-level synthesis implementation of the Generalized Matrix Multiply (GEMM) algorithm from the Basic Linear Algebra Subprograms (BLAS) library. It performs a matrix multiplication operation between two input matrices `A` and `B`, and accumulates the result in a third matrix `C`. The operation is defined as `C_out = alpha * A * B + beta * C`, where `alpha` and `beta` are scalar values.

It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A$: $P \times Q$ matrix
- $B$: $Q \times R$ matrix
- $C$: $P \times R$ matrix

and gives the following as output:

- $C_{out}$: $P \times R$ array, where $C_{out} = \alpha AB + \beta C$

Note that the output $C_{out}$ is to be stored in place of the input array $C$. The BLAS parameters used are `TRANSA = TRANSB = ‘N’`, meaning both $A$ and $B$ are not transposed.

---

Top-Level Function: `kernel_gemm`

Complete Function Signature of the Top-Level Function:
`void kernel_gemm(double alpha, double beta, double C[20][25], double A[20][30], double B[30][25]);`

Inputs:
- `alpha`: a scalar value of type `double` that represents the scaling factor for the matrix product `A * B`.
- `beta`: a scalar value of type `double` that represents the scaling factor for the matrix `C`.
- `C`: a 2D matrix of size `20 x 25` of type `double`, which is the output matrix that stores the result of the GEMM operation.
- `A`: a 2D matrix of size `20 x 30` of type `double`, which is the first input matrix.
- `B`: a 2D matrix of size `30 x 25` of type `double`, which is the second input matrix.

Outputs:
- `C_out`: a 2D matrix of size `20 x 25` of type `double`, which is the output matrix that stores the result of the GEMM operation. Note that the output `C_out` is stored in place of the input matrix `C`.

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used to represent the elements of the input and output matrices.
- `2D matrix`: a data structure used to represent the input and output matrices, where each element is a `double` value.

Sub-Components:
- None