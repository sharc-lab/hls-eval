Kernel Description:
The `kernel_correlation` design computes the correlation coefficients (Pearson's) between attributes of a dataset. It takes a 2D matrix `data` as input, where each row represents a data point and each column represents an attribute. The design first computes the mean and standard deviation of each attribute, then normalizes the data by subtracting the mean and dividing by the standard deviation. Finally, it computes the correlation coefficients between each pair of attributes using the normalized data.

It takes the following as input,

- `data`: $N \times M$ matrix that represents $N$ data points, each with $M$ attributes,

and gives the following as output:

- `corr`: $M \times M$ matrix where the $i,j$-th element is the correlation coefficient between $i$ and $j$. The matrix is symmetric.

Correlation is defined as the following,

$$
\text{corr}(i,j) = \frac{\text{cov}(i,j)}{\text{stddev}(i)\text{stddev}(j)}
$$

where

$$
\text{stddev}(x) = \sqrt{\frac{\sum_{k=0}^{N-1} (\text{data}(k, x) - \text{mean}(x))^2}{N}}
$$

`cov` and `mean` are defined in covariance (1).

(1): However, the denominator when computing covariance is $N$ for correlation.

---

Top-Level Function: `kernel_correlation`

Complete Function Signature of the Top-Level Function:
`void kernel_correlation(double float_n, double data[32][28], double corr[28][28], double mean[28], double stddev[28]);`

Inputs:
- `float_n`: a floating-point value representing the number of data points
- `data`: a 2D matrix of size 32x28, where each row represents a data point and each column represents an attribute
- `mean`: an array of size 28 to store the mean of each attribute
- `stddev`: an array of size 28 to store the standard deviation of each attribute

Outputs:
- `corr`: a 2D matrix of size 28x28, where each element represents the correlation coefficient between two attributes

Important Data Structures and Data Types:
- `data`: a 2D matrix of size 32x28, where each element is a `double` value
- `mean` and `stddev`: arrays of size 28, where each element is a `double` value
- `corr`: a 2D matrix of size 28x28, where each element is a `double` value

Sub-Components:
- None