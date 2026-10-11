## cholesky

Cholesky decomposition, which decomposes a matrix to triangular matrices. Only applicable when the input matrix is positive-definite.
It takes the following as input,

- $A: N \times N$ positive-definite matrix

and gives the following as output:

- $L: N \times N$ lower triangular matrix such that $A = LL^T$

The C reference implementation uses CholeskyBanachiewicz algorithm. The algorithm computes the following, where the computation starts from the upper-left corner of $L$ and proceeds row by row.

$$
L(i,j) =
\begin{cases}
\sqrt{A(i, i) - \sum_{k=0}^{i-1} L(i, k)^2} & \text{for } i = j \\
\frac{1}{L(j, j)} \left( A(i, j) - \sum_{k=0}^{j-1} L(i, k)L(j, k) \right) & \text{for } i > j
\end{cases}
$$
Storage/ordering contract: use the original t_ap_fixed type and modes. Process rows i in increasing order. For each j<i in increasing order, subtract A[i][k]*A[j][k] from stored A[i][j], storing in t_ap_fixed after each k=0..j-1; then divide the stored value by A[j][j] and store it. For the diagonal subtract A[i][k]*A[i][k] from stored A[i][i], storing after each k=0..i-1; then assign hls::sqrt of that stored value. The fixed-point operand domains must make each required pivot positive and each division defined. The output obligation covers only the lower triangle; upper-triangle storage is not part of the result and is not graded.

Original numeric type: t_ap_fixed is exactly ap_fixed<32,16>, with the original SDK default AP_TRN quantization, AP_WRAP overflow and N=0 template settings. Retain that declared width, integer width and those conversion/storage points; the observable stored result is compared by its 32 raw bits.
