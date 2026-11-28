## gesummv

Summed matrix-vector multiplications from updated BLAS. However, it is not part of the current BLAS distribution.
It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A, B$: $N \times N$ matrix
- $x$: vector of length $N$

and gives the following as outputs:

- $y$: vector of length $N$, where $y = \alpha Ax + \beta Bx$

### Fixed-point evaluation contract (2026-10-11)

The mathematical formula above is implemented with `t_ap_fixed =
ap_fixed<32,16>` using the default `AP_TRN` and `AP_WRAP` modes. Each assignment
or compound assignment below stores back into that type. AP expression widths,
parentheses and the listed accumulation order are part of the numerical contract;
do not replace them with a wider accumulator followed by one final conversion.
The testbench emits all 32 raw bits of each defined output in hexadecimal, and
comparison is exact. Workspace arrays are not additional scored outputs.

Here `N=90`. For ascending `i`, zero `tmp[i]` and `y[i]`. For ascending
`j=0..89`, store `tmp[i]=A[i][j]*x[j]+tmp[i]` and
`y[i]=B[i][j]*x[j]+y[i]`. Finally store
`y[i]=alpha*tmp[i]+beta*y[i]` as one expression. All of `y[90]` is scored;
`tmp` is workspace.
