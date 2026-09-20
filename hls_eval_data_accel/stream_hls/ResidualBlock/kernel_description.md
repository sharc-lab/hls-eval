## ResidualBlock

A ResNet basic residual block: two $3 \times 3$ convolutions, each followed by inference-mode
batch normalization, with a ReLU after the first and an identity skip connection added before the
final ReLU. Batch size 1, 16 channels, $56 \times 56$ feature map.

Top-Level Function: `forward`

Arguments, in order:

- `x`: `float[1][16][56][56]`, input feature map (NCHW). Input.
- `w1`: `float[16][16][3][3]`, first convolution weights `[out_ch][in_ch][3][3]`. Input.
- `w2`: `float[16][16][3][3]`, second convolution weights `[out_ch][in_ch][3][3]`. Input.
- `y`: `float[1][16][56][56]`, output feature map. Output.

Computation, where $\text{conv}$ is a $3 \times 3$ convolution with zero padding of 1 and
stride 1 (cross-correlation, no kernel flip), and $\text{BN}(v) = v / \sqrt{1+\epsilon}$
with $\epsilon = 10^{-5}$ (batch normalization with running mean 0, running variance 1, and no
learned scale or shift):

$$
h = \max\!\big(0,\; \text{BN}(\text{conv}(x, w_1))\big), \qquad
y = \max\!\big(0,\; \text{BN}(\text{conv}(h, w_2)) + x\big)
$$

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
