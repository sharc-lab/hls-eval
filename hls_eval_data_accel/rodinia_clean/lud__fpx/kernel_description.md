## lud

In-place LU decomposition without pivoting (Doolittle's method) of an $N \times N$ matrix,
packed into a single buffer, as in the Rodinia `lud` benchmark.

It takes as input,

- `result`: $N \times N$ matrix $A$.

and overwrites it in place with:

- `result`: the same $N \times N$ buffer, where the entries on and above the diagonal
  ($i \le j$) hold $U(i,j)$ and the entries below the diagonal ($i > j$) hold $L(i,j)$ (with an
  implicit unit diagonal for $L$), such that $A = LU$.

$L$ and $U$ satisfy:

$$
U(i,j) = A(i,j) - \sum_{k=0}^{i-1} L(i,k) U(k,j), \qquad j \ge i
$$

$$
L(j,i) = \frac{1}{U(i,i)} \left( A(j,i) - \sum_{k=0}^{i-1} L(j,k) U(k,i) \right), \qquad j > i
$$
