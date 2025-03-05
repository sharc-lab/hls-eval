Kernel Description:
The kernel_gramschmidt design is an implementation of the Modified Gram-Schmidt algorithm for QR decomposition. It takes a matrix A as input and produces two matrices Q and R such that A = QR, where Q is an orthogonal matrix and R is an upper triangular matrix. The algorithm is described in a tech report by Walter Gander.

The design consists of three main stages: normalization, orthogonalization, and update. In the normalization stage, the norm of each column of A is computed and stored in the diagonal elements of R. In the orthogonalization stage, each column of A is divided by the corresponding norm to produce the columns of Q. In the update stage, the remaining columns of A are updated using the computed Q and R.

It takes the following as input,

- $A: M \times N$ rank $N$ matrix ($M \geq N$).

and gives the following as outputs:

- $Q: M \times N$ orthogonal matrix
- $R: N \times N$ upper triangular matrix

such that $A = QR$.

---

Top-Level Function: `kernel_gramschmidt`

Complete Function Signature of the Top-Level Function:
`void kernel_gramschmidt(double A[20][30], double R[30][30], double Q[20][30]);`

Inputs:
- `A`: a 20x30 matrix of doubles, representing the input matrix to be decomposed.

Outputs:
- `Q`: a 20x30 matrix of doubles, representing the orthogonal matrix.
- `R`: a 30x30 matrix of doubles, representing the upper triangular matrix.

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point number, used to represent the elements of the input and output matrices.

Sub-Components:
- None