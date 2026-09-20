## bicg

Kernel of the BiConjugate Gradient method: one matrix-transpose-vector product and one
matrix-vector product. Unlike PolyBench's `bicg`, the two products read **two separate matrix
arguments** (with different contents), one per product.

Top-Level Function: `forward`

Arguments, in order:

- `A1`: `float[410][390]`, $N \times M$ matrix ($N=410$, $M=390$). Input, used for $s$.
- `A2`: `float[410][390]`, $N \times M$ matrix. Input, used for $q$.
- `r`: `float[410]`, vector of length $N$. Input.
- `p`: `float[390]`, vector of length $M$. Input.
- `s`: `float[390]`, vector of length $M$. Output, where $s = A_1^T r$.
- `q`: `float[410]`, vector of length $N$. Output, where $q = A_2 p$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
