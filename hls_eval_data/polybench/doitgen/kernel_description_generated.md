Kernel Description:
The `kernel_doitgen` is a high-level synthesis kernel that implements a multiresolution adaptive numerical scientific simulation (MADNESS) algorithm. It takes three inputs, `A`, `C4`, and `sum`, and performs a matrix multiplication-like operation to produce an output `A_out`. The kernel is designed to operate on 3D arrays, where `A` is a 3D array of size `R x Q x S`, `C4` is a 2D array of size `S x S`, and `sum` is a 1D array of size `S`. The output `A_out` is a 3D array of size `R x Q x P`, where `P` is equal to `S`. The kernel performs the following computation: `A_out(r, q, p) = \sum_{s=0}^{S-1} A(r, q, s) x(p, s)`, where `x` is a 2D array of size `P x S` that is not explicitly provided as an input.

It takes the following as inputs,

- $A: R \times Q \times S$ array
- $x: P \times S$ array

and gives the following as output:

- $A_{out}: R \times Q \times P$ array

where $A_{out}(r, q, p) = \sum_{s=0}^{S-1} A(r, q, s) x(p, s)$

Note that the output $A_{out}$ is to be stored in place of the input array $A$ in the original code. Although it is not mentioned anywhere, the computation does not make sense if $P \neq S$.

---

Top-Level Function: `kernel_doitgen`

Complete Function Signature of the Top-Level Function:
`void kernel_doitgen(double A[10][8][12], double C4[12][12], double sum[12]);`

Inputs:
- `A`: a 3D array of size `R x Q x S`, where `R=10`, `Q=8`, and `S=12`, representing the input data.
- `C4`: a 2D array of size `S x S`, where `S=12`, representing the coefficient matrix.
- `sum`: a 1D array of size `S`, where `S=12`, used as a temporary storage for the sum of products.

Outputs:
- `A_out`: a 3D array of size `R x Q x P`, where `P=S=12`, representing the output data, stored in place of the input array `A`.

Important Data Structures and Data Types:
- `A`: a 3D array of size `R x Q x S`, where each element is a `double` precision floating-point number.
- `C4`: a 2D array of size `S x S`, where each element is a `double` precision floating-point number.
- `sum`: a 1D array of size `S`, where each element is a `double` precision floating-point number.

Sub-Components:
- None