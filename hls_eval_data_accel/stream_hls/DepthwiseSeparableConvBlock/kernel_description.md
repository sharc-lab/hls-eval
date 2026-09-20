## DepthwiseSeparableConvBlock

A depthwise-separable convolution block as used in MobileNet-style networks: a $3 \times 3$
depthwise convolution, a $1 \times 1$ pointwise convolution, inference-mode batch
normalization, and a ReLU. Batch size 1, 8 channels, $112 \times 112$ feature map.

Top-Level Function: `forward`

Arguments, in order:

- `x`: `float[1][8][112][112]`, input feature map (NCHW). Input.
- `w_pw`: `float[8][8][1][1]`, pointwise weights `[out_ch][in_ch][1][1]`. Input.
- `w_dw`: `float[8][3][3]`, depthwise weights `[ch][3][3]`. Input.
- `y`: `float[1][8][112][112]`, output feature map. Output.

Computation, with zero padding of 1 and stride 1 (cross-correlation, no kernel flip):

$$
d[c,h,w] = \sum_{i=0}^{2}\sum_{j=0}^{2} x_{pad}[c,h+i,w+j]\, w_{dw}[c,i,j], \qquad
p[o,h,w] = \sum_{c=0}^{7} w_{pw}[o,c,0,0]\, d[c,h,w]
$$

$$
y[o,h,w] = \max\!\Big(0,\; \frac{p[o,h,w]}{\sqrt{1+\epsilon}}\Big), \qquad \epsilon = 10^{-5}
$$

The batch normalization uses running mean 0, running variance 1, and no learned scale or shift,
so it reduces to the constant scale $1/\sqrt{1+\epsilon}$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
