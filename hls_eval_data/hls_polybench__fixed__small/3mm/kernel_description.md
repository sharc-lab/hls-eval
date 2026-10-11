## 3mm

Linear algebra kernel that consists of three matrix multiplications.
It takes the following as inputs,

- $A: P \times Q$ matrix
- $B: Q \times R$ matrix
- $C: R \times S$ matrix
- $D: S \times T$ matrix

and gives the following as output:

- $G: P \times T$ matrix, where $G = (A.B).(C.D)$

### Fixed-point evaluation contract (2026-10-11)

The mathematical formula above is implemented with `t_ap_fixed =
ap_fixed<32,16>` using the default `AP_TRN` and `AP_WRAP` modes. Each assignment
or compound assignment below stores back into that type. AP expression widths,
parentheses and the listed accumulation order are part of the numerical contract;
do not replace them with a wider accumulator followed by one final conversion.
The testbench emits all 32 raw bits of each defined output in hexadecimal, and
comparison is exact. Workspace arrays are not additional scored outputs.

For ascending row and column indices, zero each `E[i][j]` and accumulate
`E[i][j] += A[i][k]*B[k][j]` for `k=0..59`. Then zero each `F[i][j]` and
accumulate `F[i][j] += C[i][k]*D[k][j]` for `k=0..79`. Finally zero each
`G[i][j]` and accumulate `G[i][j] += E[i][k]*F[k][j]` for `k=0..49`.
The scored output is all of `G[40][70]`; `E` and `F` are workspace.
