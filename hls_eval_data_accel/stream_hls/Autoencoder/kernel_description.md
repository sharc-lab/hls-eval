## Autoencoder

A fully connected autoencoder for flattened $28 \times 28$ images (784 features), for a batch of
32: encoder $784 \to 256 \to 128 \to 64$ and decoder $64 \to 128 \to 256 \to 784$, with a
sigmoid on the reconstructed output. Linear layers use PyTorch's layout,
$\text{Linear}(t) = t W^T + b$ with `W[out][in]`.

Top-Level Function: `forward`

Arguments, in order:

- `x`: `float[32][784]`, input batch. Input.
- `b1`: `float[256]`, `W1`: `float[256][784]`. Inputs.
- `b2`: `float[128]`, `W2`: `float[128][256]`. Inputs.
- `b3`: `float[64]`, `W3`: `float[64][128]`. Inputs.
- `b4`: `float[128]`, `W4`: `float[128][64]`. Inputs.
- `b5`: `float[256]`, `W5`: `float[256][128]`. Inputs.
- `b6`: `float[784]`, `W6`: `float[784][256]`. Inputs.
- `y`: `float[32][784]`, reconstruction. Output.

(The bias precedes its weight matrix in the argument list, e.g. `b1, W1, b2, W2, ...`.)

$$
\begin{aligned}
h_1 &= \max(0,\; xW_1^T + b_1) \\
h_2 &= \max(0,\; h_1 W_2^T + b_2) \\
z &= h_2 W_3^T + b_3 & &\text{(64-wide bottleneck, no activation)} \\
h_4 &= \max(0,\; z W_4^T + b_4) \\
h_5 &= \max(0,\; h_4 W_5^T + b_5) \\
y &= \sigma(h_5 W_6^T + b_6), & \sigma(v) &= 1/(1+e^{-v})
\end{aligned}
$$

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
