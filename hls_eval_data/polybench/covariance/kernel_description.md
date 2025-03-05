Kernel Description:
The `kernel_covariance` design computes the covariance, a measure from statistics that shows how linearly related two variables are. It takes a 2D matrix `data` as input, representing `N` data points, each with `M` attributes, and computes the covariance between each pair of attributes. The covariance is defined as the mean of the product of deviations for each pair of attributes.

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

---

Top-Level Function: `kernel_covariance`

Complete Function Signature of the Top-Level Function:
`void kernel_covariance(double float_n, double data[32][28], double cov[28][28], double mean[28]);`

Inputs:
- `float_n`: a double-precision floating-point number representing the number of data points `N`.
- `data`: a 2D matrix of size `32x28` representing `N` data points, each with `M` attributes.
- `cov`: a 2D matrix of size `28x28` to store the covariance between each pair of attributes.
- `mean`: a 1D array of size `28` to store the mean of each attribute.

Outputs:
- `cov`: a 2D matrix of size `28x28` where the `i,j`-th element is the covariance between the `i`-th and `j`-th attributes. The matrix is symmetric.

Important Data Structures and Data Types:
- `data`: a 2D matrix of size `32x28` representing `N` data points, each with `M` attributes, where each element is a double-precision floating-point number.
- `cov`: a 2D matrix of size `28x28` to store the covariance between each pair of attributes, where each element is a double-precision floating-point number.
- `mean`: a 1D array of size `28` to store the mean of each attribute, where each element is a double-precision floating-point number.

Sub-Components:
- None