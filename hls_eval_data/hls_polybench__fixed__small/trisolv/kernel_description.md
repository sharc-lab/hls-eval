## trisolv

Triangular matrix solver using forward substitution.
It takes the following as inputs,

- $L$: $N \times N$ lower triangular matrix
- $b$: vector of length $N$

and gives the following as output:

- $x$: vector of length $N$, where $Lx = b$

The forward substitution is as follows:

$$
x(i) = \frac{b(i) - \sum_{j=0}^{i-1} L(i, j) \cdot x(j)}{L(i, i)}
$$

### Fixed-point evaluation contract (2026-10-11)

The mathematical formula above is implemented with `t_ap_fixed =
ap_fixed<32,16>` using the default `AP_TRN` and `AP_WRAP` modes. Each assignment
or compound assignment below stores back into that type. AP expression widths,
parentheses and the listed accumulation order are part of the numerical contract;
do not replace them with a wider accumulator followed by one final conversion.
The testbench emits all 32 raw bits of each defined output in hexadecimal, and
comparison is exact. Workspace arrays are not additional scored outputs.

Here `N=120`. For ascending `i=0..119`, store `x[i]=b[i]`, then
`x[i] -= L[i][j]*x[j]` for ascending `j=0..i-1`, then
`x[i]=x[i]/L[i][i]`. Legal inputs have nonzero stored diagonal elements.
All of `x[120]` is scored.
