Kernel Description:
The `kernel_gesummv` design is a high-level synthesis implementation of the summed matrix-vector multiplication algorithm, which is an extension of the Basic Linear Algebra Subprograms (BLAS) library. This kernel takes in two matrices `A` and `B`, two scalars `alpha` and `beta`, and a vector `x` as inputs, and produces a vector `y` as output. The output vector `y` is computed as `y = alpha * Ax + beta * Bx`, where `Ax` and `Bx` are the matrix-vector products of `A` and `B` with `x`, respectively.

It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A, B$: $N \times N$ matrix
- $x$: vector of length $N$

and gives the following as outputs:

- $y$: vector of length $N$, where $y = \alpha Ax + \beta Bx$

---

Top-Level Function: `kernel_gesummv`

Complete Function Signature of the Top-Level Function:
`void kernel_gesummv(double alpha, double beta, double A[30][30], double B[30][30], double tmp[30], double x[30], double y[30]);`

Inputs:
- `alpha`: a scalar value of type `double` that represents the scaling factor for the matrix-vector product `Ax`.
- `beta`: a scalar value of type `double` that represents the scaling factor for the matrix-vector product `Bx`.
- `A`: a 2D matrix of size `30x30` with elements of type `double`, representing the first input matrix.
- `B`: a 2D matrix of size `30x30` with elements of type `double`, representing the second input matrix.
- `x`: a 1D vector of length `30` with elements of type `double`, representing the input vector.
- `tmp`: a 1D vector of length `30` with elements of type `double`, used as a temporary storage for intermediate results.

Outputs:
- `y`: a 1D vector of length `30` with elements of type `double`, representing the output vector computed as `y = alpha * Ax + beta * Bx`.

Important Data Structures and Data Types:
- `double[30][30]`: a 2D matrix data structure with elements of type `double`, used to represent the input matrices `A` and `B`.
- `double[30]`: a 1D vector data structure with elements of type `double`, used to represent the input vector `x`, temporary vector `tmp`, and output vector `y`.

Sub-Components:
- None