Kernel Description:
The `kernel_lu` design is a high-level synthesis implementation of the LU decomposition algorithm without pivoting. It takes a square matrix `A` as input and computes the lower triangular matrix `L` and upper triangular matrix `U` such that `A = LU`. The algorithm uses a nested loop structure to iterate over the elements of the input matrix, computing the elements of `L` and `U`.

It takes the following as input,

- $A: N \times N$ matrix

and gives the following as outputs:

- $L: N \times N$ lower triangular matrix
- $U: N \times N$ upper triangular matrix

such that $A = LU$.
L and U are computed as follows:

$$
U(i,j) = A(i,j) - \sum_{k=0}^{i-1} L(i,k)U(k,j)
$$

$$
L(i,j) = \frac{1}{U(j,j)} \left( A(i,j) - \sum_{k=0}^{j-1} L(i,k)U(k,j) \right)
$$

---

Top-Level Function: `kernel_lu`

Complete Function Signature of the Top-Level Function:
`void kernel_lu(double A[40][40]);`

Inputs:
- `A`: a square matrix of size 40x40, represented as a 2D array of `double` values.

Outputs:
- `L`: a lower triangular matrix of size 40x40, represented as a 2D array of `double` values.
- `U`: an upper triangular matrix of size 40x40, represented as a 2D array of `double` values.

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used to represent the elements of the input and output matrices.

Sub-Components:
- None