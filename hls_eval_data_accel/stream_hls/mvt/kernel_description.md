## mvt

Matrix-vector product and transposed matrix-vector product. Unlike PolyBench's `mvt`, the two
products read **two separate matrix arguments** (with different contents), and the result
vectors start from zero rather than being accumulated into an input.

Top-Level Function: `forward`

Arguments, in order:

- `A1`: `float[400][400]`, $N \times N$ matrix. Input, used for $x_1$.
- `A2`: `float[400][400]`, $N \times N$ matrix. Input, used for $x_2$.
- `y1`: `float[400]`, vector of length $N$. Input.
- `y2`: `float[400]`, vector of length $N$. Input.
- `x1`: `float[400]`, vector of length $N$. Output, where $x_1 = A_1 y_1$.
- `x2`: `float[400]`, vector of length $N$. Output, where $x_2 = A_2^T y_2$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
