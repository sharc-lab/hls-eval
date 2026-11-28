## mvt

Matrix vector multiplication composed with another matrix vector multiplication but with transposed matrix.
It takes the following as inputs,

- $A: N \times N$ matrix
- $y1, y2$: vectors of length $N$

and gives the following as outputs:

- $x1$: vector of length $N$, where $x1 = x1 + Ay1$
- $x2$: vector of length $N$, where $x2 = x2 + A^Ty2$

### Fixed-point evaluation contract (2026-10-11)

The mathematical formula above is implemented with `t_ap_fixed =
ap_fixed<32,16>` using the default `AP_TRN` and `AP_WRAP` modes. Each assignment
or compound assignment below stores back into that type. AP expression widths,
parentheses and the listed accumulation order are part of the numerical contract;
do not replace them with a wider accumulator followed by one final conversion.
The testbench emits all 32 raw bits of each defined output in hexadecimal, and
comparison is exact. Workspace arrays are not additional scored outputs.

Here `N=120`; `x1` and `x2` are input/output vectors with supplied initial
values. For ascending `i` then `j`, store
`x1[i]=x1[i]+A[i][j]*y_1[j]`. After this pass, for ascending `i` then `j`,
store `x2[i]=x2[i]+A[j][i]*y_2[j]`. Both complete vectors are scored.
