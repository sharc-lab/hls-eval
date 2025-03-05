Kernel Description:
The `kernel_gemver` design is a high-level synthesis implementation of the GEMVER kernel, which performs multiple matrix-vector multiplications from the updated BLAS (Basic Linear Algebra Subprograms) standard. The kernel takes in several inputs, including scalars, matrices, and vectors, and produces two output vectors. The design consists of three main stages: matrix update, vector update, and final vector computation.

It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A$: $N \times N$ matrix
- $u1, v1, u2, v2, y, z$: vectors of length $N$

and gives the following as outputs:

- $A$: $N \times N$ matrix, where $A = A + u1 \cdot v1^T + u2 \cdot v2^T$
- $x$: vector of length $N$, where $x = \beta A^T y + z$
- $w$: vector of length $N$, where $w = \alpha A x$

---

Top-Level Function: `kernel_gemver`

Complete Function Signature of the Top-Level Function:
`void kernel_gemver(double alpha, double beta, double A[40][40], double u1[40], double v1[40], double u2[40], double v2[40], double w[40], double x[40], double y[40], double z[40]);`

Inputs:
- `alpha`: a scalar value used in the final vector computation
- `beta`: a scalar value used in the vector update stage
- `A`: a 40x40 matrix used in the matrix update and vector update stages
- `u1`, `v1`, `u2`, `v2`: four vectors of length 40 used in the matrix update stage
- `y`, `z`: two vectors of length 40 used in the vector update stage
- `w`, `x`: two output vectors of length 40

Outputs:
- `A`: the updated 40x40 matrix
- `x`: the output vector of length 40
- `w`: the output vector of length 40

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used for all inputs and outputs
- `A`: a 40x40 matrix represented as a 2D array of `double` values
- `u1`, `v1`, `u2`, `v2`, `y`, `z`, `w`, `x`: vectors of length 40 represented as 1D arrays of `double` values

Sub-Components:
- None