## FeedForward

The position-wise feed-forward network of a Transformer block: a linear layer, a ReLU, and a
second linear layer, applied independently to each of 512 tokens with model width 128 and hidden
width 256. Linear layers use PyTorch's layout, $\text{Linear}(t) = t W^T + b$ with
`W[out][in]`.

Top-Level Function: `forward`

Arguments, in order:

- `x`: `float[1][512][128]`, input tokens (batch, token, feature). Input.
- `b1`: `float[256]`, first-layer bias. Input.
- `W1`: `float[256][128]`, first-layer weights. Input.
- `b2`: `float[128]`, second-layer bias. Input.
- `W2`: `float[128][256]`, second-layer weights. Input.
- `y`: `float[1][512][128]`, output tokens. Output.

$$
y = \max(0,\; x W_1^T + b_1)\, W_2^T + b_2
$$

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
