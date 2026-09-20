## MultiHeadSelfAttention1

Multi-head self-attention (no mask, no residual, no layer norm) over a sequence of 64 tokens with
model width 128 and 8 heads of dimension 16. Linear layers use PyTorch's layout,
$\text{Linear}(t) = t W^T + b$ with `W[out][in]`.

Top-Level Function: `forward`

Arguments, in order:

- `x`: `float[1][64][128]`, input tokens (batch, token, feature). Input.
- `bq`: `float[128]`, `Wq`: `float[128][128]`, the query projection bias and weights. Inputs.
- `bk`: `float[128]`, `Wk`: `float[128][128]`, the key projection bias and weights. Inputs.
- `bv`: `float[128]`, `Wv`: `float[128][128]`, the value projection bias and weights. Inputs.
- `bo`: `float[128]`, `Wo`: `float[128][128]`, the output projection bias and weights. Inputs.
- `y`: `float[1][64][128]`, output tokens. Output.

(The bias precedes its weight matrix in the argument list, e.g. `bq, Wq, bk, Wk, ...`.)

Computation: $Q = xW_q^T + b_q$, $K = xW_k^T + b_k$, $V = xW_v^T + b_v$. Each of $Q, K, V$ is
split along the feature axis into 8 heads of 16 consecutive features (head $h$ takes features
$16h \ldots 16h+15$). Per head,

$$
\text{out}_h = \text{softmax}\!\Big(\frac{Q_h K_h^T}{4}\Big) V_h
$$

where the softmax is over the key (last) axis, $4 = \sqrt{16}$, and it is computed in the
numerically stable form (subtract the row maximum before exponentiating). The head outputs are
concatenated back to width 128, in head order, and projected: $y = \text{out}\, W_o^T + b_o$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
