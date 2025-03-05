Kernel Description:
The `kernel_trmm` design is a high-level synthesis implementation of a triangular matrix multiplication (TRMM) algorithm. It takes two input matrices, `A` and `B`, and a scalar `alpha`, and performs the matrix multiplication `B = alpha * A * B` in place, storing the result in `B`. The matrix `A` is a lower triangular matrix, and the multiplication is performed from the left. The design uses a nested loop structure to iterate over the elements of the matrices, with the innermost loop performing the dot product of the rows of `A` and columns of `B`.

It takes the following as inputs,

- $A$: $N \times N$ lower triangular matrix
- $B$: $N \times N$ matrix

and gives the following as output:

- $B_{out}$: $N \times N$ matrix, where $B_{out} = AB$

Note that the output $B_{out}$ is to be stored in place of the input array $B$. The configurations used are `SIDE = 'L'`, `UPLO = 'L'`, `TRANSA = 'T'`, and `DIAG = 'U'`, meaning the multiplication is from the left, the matrix is lower triangular, untransposed with unit diagonal.

---

Top-Level Function: `kernel_trmm`

Complete Function Signature of the Top-Level Function:
`void kernel_trmm(double alpha, double A[20][20], double B[20][30]);`

Inputs:
- `alpha`: a scalar value used to scale the result of the matrix multiplication
- `A`: a 20x20 lower triangular matrix
- `B`: a 20x30 matrix, which is also the output matrix

Outputs:
- `B`: a 20x30 matrix, which is the result of the matrix multiplication `B = alpha * A * B`

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used to represent the elements of the matrices
- `A` and `B` matrices: 2D arrays of `double` values, with sizes 20x20 and 20x30, respectively

Sub-Components:
- None