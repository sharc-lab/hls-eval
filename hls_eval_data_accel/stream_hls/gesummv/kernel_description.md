## gesummv

Summed matrix-vector multiplication: two matrix-vector products with the same vector, each
scaled by a fixed constant and added. The scalars are fixed constants inside the kernel, not
arguments.

Top-Level Function: `forward`

Arguments, in order:

- `A`: `float[250][250]`, $N \times N$ matrix. Input.
- `B`: `float[250][250]`, $N \times N$ matrix. Input.
- `x`: `float[250]`, vector of length $N$. Input.
- `y`: `float[250]`, vector of length $N$. Output, where $y = \alpha Ax + \beta Bx$ with
  $\alpha = 1.5$ and $\beta = 1.2$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
