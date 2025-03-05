Kernel Description:
The `kernel_cholesky` design is a high-level synthesis implementation of the Cholesky decomposition algorithm, which decomposes a positive-definite matrix into a lower triangular matrix. The algorithm is based on the Cholesky-Banachiewicz algorithm, which computes the lower triangular matrix row by row, starting from the upper-left corner.

It takes the following as input,

- $A: N \times N$ positive-definite matrix

and gives the following as output:

- $L: N \times N$ lower triangular matrix such that $A = LL^T$

The C reference implementation uses Cholesky Banachiewicz algorithm. The algorithm computes the following, where the computation starts from the upper-left corner of $L$ and proceeds row by row.

$$
L(i,j) =
\begin{cases}
\sqrt{A(i, i) - \sum_{k=0}^{i-1} L(i, k)^2} & \text{for } i = j \\
\frac{1}{L(j, j)} \left( A(i, j) - \sum_{k=0}^{j-1} L(i, k)L(j, k) \right) & \text{for } i > j
\end{cases}
$$

---

Top-Level Function: `kernel_cholesky`

Complete Function Signature of the Top-Level Function:
`void kernel_cholesky(double A[40][40]);`

Inputs:
- `A`: a 40x40 positive-definite matrix, represented as a 2D array of double-precision floating-point numbers.

Outputs:
- `A`: the lower triangular matrix, represented as a 2D array of double-precision floating-point numbers, such that `A = LL^T`.

Important Data Structures and Data Types:
- `double[40][40]`: a 2D array of double-precision floating-point numbers, used to represent the input matrix `A` and the output lower triangular matrix `L`.

Sub-Components:
- None