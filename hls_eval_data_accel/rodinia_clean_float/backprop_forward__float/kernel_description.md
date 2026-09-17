## backprop_forward

Computes the forward pass of one layer of a back-propagation neural network, as used in the
Rodinia `backprop` benchmark: a weighted sum of the input layer's activations followed by a
sigmoid (logistic) activation function.

It takes the following as input,

- `l1`: vector of length 65537, the activation of each of the 65536 input units, indexed
  $k = 1, \ldots, 65536$. Index 0 is a fixed bias unit and is always treated as having
  activation 1, regardless of the value passed in.
- `conn`: $65537 \times 17$ matrix (row-major, `conn[k*17+j]`) of connection weights from
  input unit $k$ (including the bias unit $k=0$) to output unit $j$.

and gives the following as output:

- `l2`: vector of length 17. `l2[j]` is the activation of output unit $j = 1, \ldots, 16$
  (index 0 is unused).

For every output unit $j = 1, \ldots, 16$ (with $l1(0) \equiv 1$):

$$
sum(j) = \sum_{k=0}^{65536} conn(k,j) \cdot l1(k)
\qquad\qquad
l2(j) = \frac{1}{1 + e^{-sum(j)}}
$$
