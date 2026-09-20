## ResMLP

A small four-layer MLP classifier head with a residual connection around the second layer, for a
batch of 8 inputs of width 1024 producing 10 logits. Linear layers use PyTorch's layout,
$\text{Linear}(t) = t W^T + b$ with `W[out][in]`.

Top-Level Function: `forward`

Arguments, in order:

- `x`: `float[8][1024]`, input batch. Input.
- `b1`: `float[512]`, `W1`: `float[512][1024]`, layer 1 bias and weights. Inputs.
- `b2`: `float[512]`, `W2`: `float[512][512]`, layer 2 bias and weights. Inputs.
- `b3`: `float[256]`, `W3`: `float[256][512]`, layer 3 bias and weights. Inputs.
- `b4`: `float[10]`, `W4`: `float[10][256]`, layer 4 bias and weights. Inputs.
- `y`: `float[8][10]`, output logits. Output.

(The bias precedes its weight matrix in the argument list, e.g. `b1, W1, b2, W2, ...`.)

$$
\begin{aligned}
a_1 &= xW_1^T + b_1, & h_1 &= \max(0, a_1) \\
a_2 &= h_1 W_2^T + b_2 + a_1, & h_2 &= \max(0, a_2) \\
h_3 &= h_2 W_3^T + b_3 & &\text{(no activation)} \\
y &= h_3 W_4^T + b_4
\end{aligned}
$$

Note that the residual term added in layer 2 is the layer-1 **pre-activation** $a_1$, not
$h_1$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
