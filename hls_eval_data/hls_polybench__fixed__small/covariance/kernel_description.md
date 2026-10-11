## covariance

Computes the covariance, a measure from statistics that show how linearly related two variables are.
It takes the following as input,

- `data`: $N \times M$ matrix that represents $N$ data points, each with $M$ attributes,

and gives the following output:

- `cov`: $M \times M$ matrix where the $i,j$-th element is the covariance between $i$ and $j$. The matrix is symmetric.

Covariance is defined to be the mean of the product of deviations for $i$ and $j$:

$$
\text{cov}(i,j) = \frac{\sum_{k=0}^{N-1} ( \text{data}(k,i) - \text{mean}(i) )(\text{data}(k,j) - \text{mean}(j) )}{N - 1}
$$

where

$$
\text{mean}(x) = \frac{\sum_{k=0}^{N-1} \text{data}(k, x)}{N}
$$

Note that the above computes *sample covariance* where the denominator is $N - 1$.

### Fixed-point evaluation contract (2026-10-11)

The mathematical formula above is implemented with `t_ap_fixed =
ap_fixed<32,16>` using the default `AP_TRN` and `AP_WRAP` modes. Each assignment
or compound assignment below stores back into that type. AP expression widths,
parentheses and the listed accumulation order are part of the numerical contract;
do not replace them with a wider accumulator followed by one final conversion.
The testbench emits all 32 raw bits of each defined output in hexadecimal, and
comparison is exact. Workspace arrays are not additional scored outputs.

Here `N=100`, `M=80`, and the supplied `float_n` is the typed normalization
scalar (the benchmark supplies `N`). For each column, zero `mean[j]`, accumulate
`mean[j] += data[i][j]` for ascending `i`, then store `mean[j] /= float_n`.
Next store `data[i][j] -= mean[j]`. For ascending `i` and `j=i..79`, zero
`cov[i][j]`, accumulate `cov[i][j] += data[k][i]*data[k][j]` for ascending
`k=0..99`, divide by `(float_n-t_ap_fixed(1))`, and mirror to `cov[j][i]`.
Both divisors must be nonzero. All of `cov[80][80]` is scored; `mean` and the
centered `data` are workspace.
