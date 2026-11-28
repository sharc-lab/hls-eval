## durbin

Durbin is an algorithm for solving Yule-Walker equations, which is a special case of Toeplitz systems.
It takes the following as input,

- $r$: vector of length $N$.

and gives the following as output:

- $y$: vector of length $N$

such that $Ty = -r$ where $T$ is a symmetric, unit-diagonal, Toeplitz matrix defined by the vector $[1,r_0, \ldots ,r_{N-1}]$.
The C reference implementation is a direct implementation of the algorithm described in a book by Golub and Van Loan. The book mentions that a vector can be removed to use less space, but the implementation retains this vector.

### Fixed-point evaluation contract (2026-10-11)

The mathematical formula above is implemented with `t_ap_fixed =
ap_fixed<32,16>` using the default `AP_TRN` and `AP_WRAP` modes. Each assignment
or compound assignment below stores back into that type. AP expression widths,
parentheses and the listed accumulation order are part of the numerical contract;
do not replace them with a wider accumulator followed by one final conversion.
The testbench emits all 32 raw bits of each defined output in hexadecimal, and
comparison is exact. Workspace arrays are not additional scored outputs.

Here `N=120`. All of `alpha`, `beta`, `sum` and `z` also use `t_ap_fixed`.
Store `y[0]=-r[0]`, `beta=t_ap_fixed(1)`, `alpha=-r[0]`. For ascending
`k=1..119`, store `beta=(1-alpha*alpha)*beta`, zero `sum`, then accumulate
`sum += r[k-i-1]*y[i]` for ascending `i=0..k-1`. Store
`alpha=-(r[k]+sum)/beta`. Compute all `z[i]=y[i]+alpha*y[k-i-1]` using the
previous `y`, copy them to `y[i]`, then store `y[k]=alpha`. The integer literal
`1` in the beta expression is retained. Legal inputs keep the stored divisor
`beta` nonzero. All of `y[120]` is scored; `z` is workspace.
